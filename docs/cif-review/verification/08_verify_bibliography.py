"""Bibliography verification: check URLs/DOIs exist for each entry.

Output: ledger entries for each bibliography reference.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import httpx

# Load bibliography
text = Path(
    "/srv/projects/cochid/cochid-scribe/docs/cif-review/informe-final-text.md"
).read_text()


def extract_entries(text: str) -> list[str]:
    match = re.search(r"#\s*Bibliografía", text)
    if not match:
        return []
    start = match.end()
    end_match = re.search(r"#\s*Anexos", text[start:])
    end = (start + end_match.start()) if end_match else len(text)
    biblio = text[start:end]
    return [e.strip() for e in re.split(r"\n\s*\n", biblio) if e.strip()]


URL_RE = re.compile(r"https?://[^\s)\]]+")
DOI_RE = re.compile(r"\b10\.\d{4,}/[^\s,;)\]]+")
YEAR_RE = re.compile(r"\((\d{4})(?:[\u2013\u2014-]\d{4})?\)")


def parse_entry(entry: str) -> dict:
    url_match = URL_RE.search(entry)
    doi_match = DOI_RE.search(entry)
    year_match = YEAR_RE.search(entry)

    # Author = up to first "."
    parts = entry.split(".", 1)
    author = parts[0].strip() if parts else ""
    title = ""
    if len(parts) > 1:
        # Title is between year and next period typically
        rest = parts[1].strip()
        # Skip year
        if year_match:
            year_end = entry.find(")") + 1
            title_start = entry[year_end:].lstrip(". ")
            title = title_start.split(".")[0].strip()
        else:
            title = rest.split(".")[0].strip()

    return {
        "raw": entry[:300],
        "author": author,
        "year": year_match.group(1) if year_match else None,
        "title": title[:200],
        "url": url_match.group() if url_match else None,
        "doi": doi_match.group() if doi_match else None,
    }


def check_url(url: str, timeout: float = 5.0) -> dict:
    """HEAD then fall back to GET. Returns status."""
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, verify=True) as client:
            try:
                r = client.head(url)
                if r.status_code == 405:  # Method not allowed
                    r = client.get(url)
                return {
                    "ok": r.status_code < 400,
                    "status_code": r.status_code,
                    "final_url": str(r.url),
                }
            except httpx.HTTPError as e:
                return {"ok": False, "error": str(e)[:80]}
    except Exception as e:
        return {"ok": False, "error": str(e)[:80]}


def main():
    entries = extract_entries(text)
    print(f"Total bibliography entries: {len(entries)}")

    parsed = [parse_entry(e) for e in entries]

    has_url = sum(1 for p in parsed if p["url"])
    has_doi = sum(1 for p in parsed if p["doi"])
    has_year = sum(1 for p in parsed if p["year"])

    print(f"  with URL: {has_url}")
    print(f"  with DOI: {has_doi}")
    print(f"  with year: {has_year}")

    # Verify URLs
    print(f"\nVerifying URLs...")
    results = []
    for i, p in enumerate(parsed):
        if not p["url"]:
            results.append({**p, "url_status": "no_url"})
            continue
        status = check_url(p["url"])
        results.append(
            {
                **p,
                "url_status": "ok" if status.get("ok") else "broken",
                "url_check": status,
            }
        )
        marker = "OK " if status.get("ok") else "ERR"
        print(
            f"  [{i+1:2d}/{len(parsed)}] {marker} {p['url'][:70]}"
        )

    # Save
    import json
    out = Path(
        "/srv/projects/cochid/cochid-scribe/docs/cif-review/critic-state/_bibliography_audit.json"
    )
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\nSaved: {out}")

    # Stats
    from collections import Counter

    statuses = Counter(r["url_status"] for r in results)
    print(f"\nURL statuses: {dict(statuses)}")
    broken = [r for r in results if r["url_status"] == "broken"]
    if broken:
        print(f"\n=== {len(broken)} BROKEN URLs ===")
        for r in broken[:20]:
            print(f"  {r['author'][:30]}: {r['url'][:70]}")


if __name__ == "__main__":
    main()
