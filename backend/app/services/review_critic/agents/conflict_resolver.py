"""Stage 4: Conflict Resolver.

Takes Critic judgments + classified comments, identifies clusters of
conflicting/overlapping comments, and produces final ResolvedDecision per comment.

Deterministic rules first; LLM only for genuine ambiguity.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path

from app.services.review_critic.io.state import save_stage, load_stage
from app.services.review_critic.io.verification_ledger import load_ledger
from app.services.review_critic.llm import call_claude, extract_json_array
from app.services.review_critic.qa.benja_predicate import benja_alignment
from app.services.review_critic.schemas import (
    ClassifiedComment,
    ConflictCluster,
    CriticJudgment,
    ResolvedDecision,
)

_log = logging.getLogger(__name__)


SYSTEM_PROMPT = """Eres un editor senior arbitrando conflictos entre revisores.

Te doy un grupo de comentarios que se solapan (misma seccion o anchor) y sus
critic judgments. Genera DECISIÓN FINAL para cada comentario en el cluster.

REGLAS DETERMINISTAS (aplica siempre):

1. Si hay verified factual correction (verification_refs incluye claim refuted):
   → Esa correccion gana sin importar otros revisores
   → factos > preferencias

2. Tension estilistica (CIF detallado vs Eduardo conciso):
   → Linea Benja: terse pero retiene sustancia tecnica
   → Si CIF agrega contenido factual: ACCEPT
   → Si CIF agrega texto sin nuevo contenido: ACCEPT_PARTIAL (resumido)

3. CIF "agregar contenido X" + Eduardo "menos prescriptivo":
   → NO siempre conflicto (DAC = factual no prescriptivo)
   → Si X es factual/tecnico → aceptar ambos (agregar X + suavizar prescripcion)
   → Si X es propuesta de politica → CIF cede a Eduardo

4. Estructura: si dos revisores proponen restructuras incompatibles
   → DEFER ambos, requires_director_approval=true, sugerir mejor opcion

5. Genuine ambiguity (sin regla clara):
   → ACCEPT_PARTIAL con propuesta tentativa + requires_director_approval=true

OUTPUT por comentario:

{
  "comment_id": "C-CIF1",
  "final_recommendation": "ACCEPT|ACCEPT_PARTIAL|REJECT|DEFER|NEEDS_DATA",
  "proposed_action": "apply_local_edit|...",
  "requires_director_approval": false,
  "cluster_id": "CL-1",
  "override_reason": "Critic dijo X pero conflict resolver dice Y porque..." (null si no override),
  "final_reasoning": "1-2 oraciones"
}

Responde SOLO JSON array."""


def cluster_comments(
    classified: list[ClassifiedComment],
    judgments: list[CriticJudgment],
) -> list[ConflictCluster]:
    """Group comments into clusters by section overlap and explicit conflicts."""
    by_id = {c.id: c for c in classified}
    judgment_by_id = {j.comment_id: j for j in judgments}

    # Build adjacency: comment → set of comment_ids it touches
    adj: dict[str, set[str]] = defaultdict(set)

    # Edge type 1: explicit conflicts_with from Critic
    for j in judgments:
        for other in j.conflicts_with:
            if other in by_id:
                adj[j.comment_id].add(other)
                adj[other].add(j.comment_id)
        for other in j.supports:
            if other in by_id:
                adj[j.comment_id].add(other)
                adj[other].add(j.comment_id)

    # Edge type 2: same section_hint
    by_section: dict[str, list[str]] = defaultdict(list)
    for c in classified:
        if c.section_hint:
            by_section[c.section_hint].append(c.id)
        for sec in c.touches_sections:
            if sec:
                by_section[sec].append(c.id)

    for sec, ids in by_section.items():
        if len(ids) > 1:
            for i in ids:
                for j in ids:
                    if i != j:
                        adj[i].add(j)

    # Find connected components
    visited: set[str] = set()
    clusters: list[ConflictCluster] = []
    cluster_idx = 0

    for start_id in by_id:
        if start_id in visited:
            continue
        component = []
        stack = [start_id]
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            component.append(node)
            for neighbor in adj[node]:
                if neighbor not in visited:
                    stack.append(neighbor)

        if len(component) > 1:
            cluster_idx += 1
            section = None
            for cid in component:
                c = by_id.get(cid)
                if c and c.section_hint:
                    section = c.section_hint
                    break
            clusters.append(
                ConflictCluster(
                    cluster_id=f"CL-{cluster_idx}",
                    comment_ids=sorted(component),
                    cluster_type="section" if section else "explicit_conflict",
                    section=section,
                )
            )

    return clusters


def resolve_singletons(
    classified: list[ClassifiedComment],
    judgments: list[CriticJudgment],
    cluster_ids: set[str],
) -> list[ResolvedDecision]:
    """Comments NOT in any cluster get auto-promoted from Critic judgment."""
    j_by_id = {j.comment_id: j for j in judgments}
    results = []
    for c in classified:
        if c.id in cluster_ids:
            continue
        j = j_by_id.get(c.id)
        if j is None:
            continue

        # Promote DEFER to ACCEPT_PARTIAL with director_approval
        # if proposed_action implies an edit
        final_rec = j.recommendation
        requires_approval = j.requires_director_approval
        if final_rec == "DEFER" and j.proposed_action != "none_reply_only":
            final_rec = "ACCEPT_PARTIAL"
            requires_approval = True

        results.append(
            ResolvedDecision(
                comment_id=c.id,
                final_recommendation=final_rec,
                proposed_action=j.proposed_action,
                requires_director_approval=requires_approval,
                cluster_id=None,
                override_reason=None,
                final_reasoning=j.reasoning,
            )
        )
    return results


def resolve_cluster_llm(
    cluster: ConflictCluster,
    classified: list[ClassifiedComment],
    judgments: list[CriticJudgment],
    ledger_summary: str,
) -> list[ResolvedDecision]:
    """LLM-based resolution for a single cluster."""
    c_by_id = {c.id: c for c in classified}
    j_by_id = {j.comment_id: j for j in judgments}

    items_for_llm = []
    for cid in cluster.comment_ids:
        c = c_by_id.get(cid)
        j = j_by_id.get(cid)
        if not c or not j:
            continue
        items_for_llm.append(
            {
                "id": cid,
                "author": c.author,
                "comment_text": c.comment_text[:500],
                "type": c.type,
                "verifiability": c.verifiability,
                "raw_claims": c.raw_claims,
                "critic_recommendation": j.recommendation,
                "critic_reasoning": j.reasoning,
                "improvement_score": j.improvement_score,
                "preference_score": j.preference_score,
                "benja_alignment": j.benja_alignment,
                "correctness_score": j.correctness_score,
                "verification_refs": j.verification_refs,
                "proposed_action": j.proposed_action,
            }
        )

    user_content = (
        f"CLUSTER: {cluster.cluster_id} (seccion: {cluster.section or 'N/A'})\n"
        f"COMENTARIOS EN EL CLUSTER ({len(items_for_llm)}):\n\n"
        f"{json.dumps(items_for_llm, ensure_ascii=False, indent=1)}\n\n"
        f"---\nFACTS RELEVANTES:\n{ledger_summary}\n\n"
        f"---\nResuelve el cluster. JSON array con un objeto por comentario."
    )

    try:
        response = call_claude(user_content, SYSTEM_PROMPT, model="sonnet", timeout=180)
        raw = extract_json_array(response)
        results = []
        for item in raw:
            cid = item.get("comment_id")
            j = j_by_id.get(cid)
            override = None
            if j and item.get("final_recommendation") != j.recommendation:
                override = item.get("override_reason", "Cluster resolution")
            results.append(
                ResolvedDecision(
                    comment_id=cid,
                    final_recommendation=item.get("final_recommendation", "DEFER"),
                    proposed_action=item.get(
                        "proposed_action", "none_reply_only"
                    ),
                    requires_director_approval=bool(
                        item.get("requires_director_approval", False)
                    ),
                    cluster_id=cluster.cluster_id,
                    override_reason=override,
                    final_reasoning=item.get("final_reasoning", ""),
                )
            )
        return results
    except Exception as e:
        _log.warning("Cluster %s resolution failed: %s — defaulting", cluster.cluster_id, e)
        # Fallback: keep Critic judgments as-is
        return [
            ResolvedDecision(
                comment_id=cid,
                final_recommendation=j_by_id[cid].recommendation,
                proposed_action=j_by_id[cid].proposed_action,
                requires_director_approval=j_by_id[cid].requires_director_approval,
                cluster_id=cluster.cluster_id,
                override_reason=None,
                final_reasoning=j_by_id[cid].reasoning,
            )
            for cid in cluster.comment_ids
            if cid in j_by_id
        ]


def run() -> Path:
    """Run conflict resolution and save outputs."""
    classified = load_stage("10_classified.json", ClassifiedComment)
    judgments = load_stage("30_critic_judgments.json", CriticJudgment)

    clusters = cluster_comments(classified, judgments)
    print(f"Conflict Resolver: {len(clusters)} clusters detected")

    # Save clusters
    save_stage("40_conflict_clusters.json", clusters)

    cluster_ids = {cid for cl in clusters for cid in cl.comment_ids}

    # Build short ledger summary
    ledger = load_ledger()
    ledger_summary = "\n".join(
        f"  [{f.status}] {f.claim_id}: {f.claim_text[:80]}" for f in ledger.facts
    )

    # Singletons (auto-promote DEFER)
    singletons = resolve_singletons(classified, judgments, cluster_ids)
    print(f"  Singletons resolved: {len(singletons)}")

    # Clusters via LLM
    cluster_resolutions: list[ResolvedDecision] = []
    for cl in clusters:
        print(f"  Resolving {cl.cluster_id} ({len(cl.comment_ids)} comments)")
        cluster_resolutions.extend(
            resolve_cluster_llm(cl, classified, judgments, ledger_summary)
        )

    all_resolutions = singletons + cluster_resolutions

    # Stats
    from collections import Counter

    rec_counts = Counter(r.final_recommendation for r in all_resolutions)
    print(f"\n=== Final decisions: {len(all_resolutions)} ===")
    print(f"Recommendations: {dict(rec_counts)}")

    path = save_stage("41_resolved_decisions.json", all_resolutions)
    print(f"\nSaved → {path}")
    return path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run()
