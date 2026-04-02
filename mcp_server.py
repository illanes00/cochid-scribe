"""Scribe MCP Server — Exposes Scribe's document, claims, comments, bibliography
and review APIs as MCP tools for Claude Code CLI integration.

Run: python mcp_server.py (stdio transport)
Register in .mcp.json to use from Claude Code.
"""

import json
import sys
from typing import Any

import httpx

SCRIBE_API = "http://127.0.0.1:8132"


def _api(method: str, path: str, body: dict | None = None) -> Any:
    """Call Scribe API and return parsed JSON."""
    url = f"{SCRIBE_API}{path}"
    try:
        if method == "GET":
            r = httpx.get(url, timeout=30)
        else:
            r = httpx.post(url, json=body or {}, timeout=120)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return {"error": detail}
    except Exception as e:
        return {"error": str(e)}


# ── Tool definitions ─────────────────────────────────────────────

TOOLS = [
    {
        "name": "scribe_list_documents",
        "description": "List all documents in Scribe with their slugs, types, and titles.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "scribe_get_document",
        "description": "Get a document's full content (markdown), metadata, and Google sync status.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "slug": {"type": "string", "description": "Document slug (e.g. 'cif-medicamentos')"}
            },
            "required": ["slug"],
        },
    },
    {
        "name": "scribe_list_comments",
        "description": "List all comments for a document, including CIF/director feedback and Google Docs comments.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "slug": {"type": "string", "description": "Document slug"}
            },
            "required": ["slug"],
        },
    },
    {
        "name": "scribe_list_claims",
        "description": "List all verified claims/facts for a document with their types and evidence.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "slug": {"type": "string", "description": "Document slug"}
            },
            "required": ["slug"],
        },
    },
    {
        "name": "scribe_extract_claims",
        "description": "Use AI to extract verifiable claims from a document and store them.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "slug": {"type": "string", "description": "Document slug"}
            },
            "required": ["slug"],
        },
    },
    {
        "name": "scribe_review_status",
        "description": "Get review status: how many comments are pending, resolved, and if Google is linked.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "slug": {"type": "string", "description": "Document slug"}
            },
            "required": ["slug"],
        },
    },
    {
        "name": "scribe_review_analyze",
        "description": "AI analyzes all pending comments and generates suggested responses with evidence.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "slug": {"type": "string", "description": "Document slug"}
            },
            "required": ["slug"],
        },
    },
    {
        "name": "scribe_import_feedback",
        "description": "Import structured feedback (from email, meetings, etc.) as comments on a document.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "slug": {"type": "string", "description": "Document slug"},
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "author": {"type": "string"},
                            "content": {"type": "string"},
                            "quote": {"type": "string"},
                            "feedback_type": {"type": "string", "enum": ["general", "structural", "factual", "editorial", "methodological"]},
                        },
                        "required": ["author", "content"],
                    },
                },
                "source": {"type": "string", "default": "email"},
            },
            "required": ["slug", "items"],
        },
    },
    {
        "name": "scribe_search_bibliography",
        "description": "Search bibliography entries by keyword.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"],
        },
    },
    {
        "name": "scribe_list_bibliography",
        "description": "List all bibliography entries.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "scribe_add_bibliography",
        "description": "Add a bibliography entry.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "bib_key": {"type": "string", "description": "Citation key (e.g. 'oecd_2025')"},
                "title": {"type": "string"},
                "author": {"type": "string"},
                "year": {"type": "string"},
                "journal": {"type": "string"},
                "doi": {"type": "string"},
                "url": {"type": "string"},
            },
            "required": ["bib_key", "title"],
        },
    },
    {
        "name": "scribe_get_knowledge_graph",
        "description": "Get the knowledge graph showing connections between documents, notes, claims, and bibliography.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "scribe_create_note",
        "description": "Create a knowledge base note (idea, summary, concept) linked to documents.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string", "description": "Markdown content"},
                "note_type": {"type": "string", "enum": ["idea", "summary", "quote", "concept"]},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title", "content"],
        },
    },
    {
        "name": "scribe_list_notes",
        "description": "List all knowledge base notes.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "scribe_sync_google_comments",
        "description": "Sync comments from Google Docs into Scribe (requires Google OAuth).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "slug": {"type": "string", "description": "Document slug"}
            },
            "required": ["slug"],
        },
    },
    {
        "name": "scribe_track_changes",
        "description": "List track changes for a document with their status (pending/accepted/rejected).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "slug": {"type": "string", "description": "Document slug"}
            },
            "required": ["slug"],
        },
    },
]


# ── Tool handlers ────────────────────────────────────────────────


def handle_tool(name: str, args: dict) -> Any:
    slug = args.get("slug", "")

    if name == "scribe_list_documents":
        data = _api("GET", "/api/v1/documents")
        docs = data.get("documents", [])
        return [
            {
                "slug": d["slug"],
                "title": d["title"],
                "doc_type": d["doc_type"],
                "status": d.get("status"),
                "source_provider": d.get("source_provider"),
                "claim_count": d.get("claim_count", 0),
                "updated_at": d.get("updated_at"),
            }
            for d in docs
        ]

    elif name == "scribe_get_document":
        doc = _api("GET", f"/api/v1/documents/{slug}")
        return {
            "slug": doc.get("slug"),
            "title": doc.get("title"),
            "doc_type": doc.get("doc_type"),
            "markdown": doc.get("markdown", "")[:50000],
            "status": doc.get("status"),
            "source_provider": doc.get("source_provider"),
            "source_id": doc.get("source_id"),
            "claim_count": doc.get("claim_count", 0),
            "verified_count": doc.get("verified_count", 0),
        }

    elif name == "scribe_list_comments":
        return _api("GET", f"/api/v1/comments/document/{slug}")

    elif name == "scribe_list_claims":
        return _api("GET", f"/api/v1/claims/document/{slug}")

    elif name == "scribe_extract_claims":
        return _api("POST", f"/api/v1/llm/extract-claims-document/{slug}")

    elif name == "scribe_review_status":
        return _api("GET", f"/api/v1/review/{slug}/status")

    elif name == "scribe_review_analyze":
        return _api("POST", f"/api/v1/review/{slug}/analyze")

    elif name == "scribe_import_feedback":
        return _api("POST", f"/api/v1/comments/document/{slug}/import-feedback", {
            "items": args.get("items", []),
            "source": args.get("source", "email"),
        })

    elif name == "scribe_search_bibliography":
        return _api("POST", "/api/v1/bibliography/search", {"query": args["query"]})

    elif name == "scribe_list_bibliography":
        return _api("GET", "/api/v1/bibliography")

    elif name == "scribe_add_bibliography":
        body = {k: v for k, v in args.items() if v}
        return _api("POST", "/api/v1/bibliography", body)

    elif name == "scribe_get_knowledge_graph":
        return _api("GET", "/api/v1/graph")

    elif name == "scribe_create_note":
        return _api("POST", "/api/v1/notes", {
            "title": args["title"],
            "content": args["content"],
            "note_type": args.get("note_type", "concept"),
            "tags": args.get("tags", []),
        })

    elif name == "scribe_list_notes":
        return _api("GET", "/api/v1/notes")

    elif name == "scribe_sync_google_comments":
        return _api("POST", f"/api/v1/comments/document/{slug}/sync")

    elif name == "scribe_track_changes":
        return _api("GET", f"/api/v1/documents/{slug}/track-changes")

    return {"error": f"Unknown tool: {name}"}


# ── MCP stdio transport ──────────────────────────────────────────


def send(msg: dict):
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = msg.get("method", "")
        msg_id = msg.get("id")

        if method == "initialize":
            send({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "scribe", "version": "1.0.0"},
                },
            })

        elif method == "notifications/initialized":
            pass  # No response needed

        elif method == "tools/list":
            send({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": TOOLS},
            })

        elif method == "tools/call":
            params = msg.get("params", {})
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            try:
                result = handle_tool(tool_name, tool_args)
                text = json.dumps(result, ensure_ascii=False, default=str)
            except Exception as e:
                text = json.dumps({"error": str(e)})

            send({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": text}],
                    "isError": "error" in (text if isinstance(text, str) else ""),
                },
            })

        elif msg_id is not None:
            send({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {},
            })


if __name__ == "__main__":
    main()
