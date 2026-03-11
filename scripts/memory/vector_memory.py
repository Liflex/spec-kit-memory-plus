#!/usr/bin/env python3
"""
Vector Memory CLI — standalone tool for Claude Code agent.

Usage:
    python vector_memory.py store --content "..." --type lesson --project my-project
    python vector_memory.py search --query "..." --limit 5 --project my-project
    python vector_memory.py status
    python vector_memory.py reindex --project my-project

Requires: Ollama running with mxbai-embed-large model.
Storage: ~/.claude/memory/vector/embeddings.json
"""

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

try:
    import requests
except ImportError:
    print("ERROR: requests library required. Install: pip install requests")
    sys.exit(1)


OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "mxbai-embed-large"
EMBEDDING_DIM = 1024

CLAUDE_HOME = Path.home() / ".claude"
VECTOR_DIR = CLAUDE_HOME / "memory" / "vector"
EMBEDDINGS_FILE = VECTOR_DIR / "embeddings.json"


def ollama_embed(text: str) -> Optional[List[float]]:
    """Generate embedding via Ollama API."""
    try:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/embed",
            json={"model": OLLAMA_MODEL, "input": text.strip()},
            timeout=30
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        if "embeddings" in data and data["embeddings"]:
            return data["embeddings"][0]
        if "embedding" in data:
            return data["embedding"]
        return None
    except Exception as e:
        print(f"Ollama error: {e}", file=sys.stderr)
        return None


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def load_store() -> List[Dict[str, Any]]:
    """Load embeddings store from disk."""
    if not EMBEDDINGS_FILE.exists():
        return []
    try:
        return json.loads(EMBEDDINGS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def save_store(entries: List[Dict[str, Any]]) -> None:
    """Save embeddings store to disk."""
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    EMBEDDINGS_FILE.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def cmd_store(args):
    """Store content with embedding."""
    content = args.content
    if not content or not content.strip():
        print("ERROR: empty content", file=sys.stderr)
        sys.exit(1)

    embedding = ollama_embed(content)
    if embedding is None:
        print("ERROR: failed to generate embedding (is Ollama running?)", file=sys.stderr)
        sys.exit(1)

    entries = load_store()

    entry = {
        "content": content.strip(),
        "type": args.type or "semantic",
        "project": args.project or "",
        "tags": args.tags.split(",") if args.tags else [],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "embedding": embedding
    }

    entries.append(entry)
    save_store(entries)

    print(f"OK: stored ({len(entries)} total entries)")


def cmd_search(args):
    """Search by semantic similarity."""
    query = args.query
    if not query or not query.strip():
        print("ERROR: empty query", file=sys.stderr)
        sys.exit(1)

    query_embedding = ollama_embed(query)
    if query_embedding is None:
        print("ERROR: failed to generate query embedding", file=sys.stderr)
        sys.exit(1)

    entries = load_store()
    if not entries:
        print("No entries in vector memory.")
        return

    # Filter by project if specified
    if args.project:
        entries = [e for e in entries if e.get("project", "") == args.project or not e.get("project")]

    # Calculate similarities
    scored = []
    for entry in entries:
        emb = entry.get("embedding")
        if not emb:
            continue
        score = cosine_similarity(query_embedding, emb)
        if score >= (args.min_score or 0.3):
            scored.append({
                "content": entry["content"],
                "type": entry.get("type", ""),
                "project": entry.get("project", ""),
                "tags": entry.get("tags", []),
                "timestamp": entry.get("timestamp", ""),
                "score": round(score, 4)
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    scored = scored[:args.limit]

    if not scored:
        print("No relevant results found.")
        return

    # Output as JSON for easy parsing by Claude
    print(json.dumps(scored, ensure_ascii=False, indent=2))


def cmd_reindex(args):
    """Re-index file memory (lessons.md, patterns.md, architecture.md) into vector store."""
    project = args.project or ""

    # Find memory files in project
    memory_dirs = []
    if project:
        # Project-level memory
        project_memory = Path.cwd() / ".claude" / "memory"
        if project_memory.exists():
            memory_dirs.append(project_memory)

    # Global memory
    global_memory = CLAUDE_HOME / "memory" / "projects"
    if global_memory.exists():
        for d in global_memory.iterdir():
            if d.is_dir() and d.name != ".global":
                memory_dirs.append(d)

    if not memory_dirs:
        print("No memory directories found.")
        return

    total_sections = 0
    entries = load_store()

    # Remove old indexed entries (avoid duplicates)
    entries = [e for e in entries if "auto-indexed" not in e.get("tags", [])]

    for memory_dir in memory_dirs:
        for md_file in memory_dir.glob("*.md"):
            if md_file.name.startswith("MEMORY"):
                continue  # Skip Claude Code's own MEMORY.md

            sections = extract_sections(md_file)
            dir_project = memory_dir.name if memory_dir.parent.name == "projects" else project

            for title, content in sections:
                if len(content.strip()) < 20:
                    continue

                full_text = f"{title}\n\n{content}"
                embedding = ollama_embed(full_text)
                if embedding is None:
                    print(f"  WARN: failed to embed section '{title}'", file=sys.stderr)
                    continue

                entries.append({
                    "content": full_text,
                    "type": file_to_type(md_file.name),
                    "project": dir_project,
                    "tags": ["auto-indexed", md_file.stem],
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "embedding": embedding
                })
                total_sections += 1
                # Small delay to not overwhelm Ollama
                time.sleep(0.05)

    save_store(entries)
    print(f"OK: indexed {total_sections} sections ({len(entries)} total entries)")


def extract_sections(file_path: Path) -> List[tuple]:
    """Extract ## sections from markdown file."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError:
        return []

    sections = []
    current_title = None
    current_lines = []

    for line in content.split("\n"):
        if line.startswith("## "):
            if current_title:
                sections.append((current_title, "\n".join(current_lines).strip()))
            current_title = line[3:].strip()
            current_lines = []
        elif current_title is not None:
            current_lines.append(line)

    if current_title:
        sections.append((current_title, "\n".join(current_lines).strip()))

    return sections


def file_to_type(filename: str) -> str:
    """Map filename to memory type."""
    mapping = {
        "lessons.md": "episodic",
        "patterns.md": "procedural",
        "architecture.md": "semantic",
    }
    return mapping.get(filename, "semantic")


def cmd_status(args):
    """Check vector memory status."""
    status = {"ollama": False, "model": False, "entries": 0, "store_path": str(EMBEDDINGS_FILE)}

    # Check Ollama
    try:
        resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if resp.status_code == 200:
            status["ollama"] = True
            models = resp.json().get("models", [])
            status["model"] = any(m.get("name", "").startswith(OLLAMA_MODEL) for m in models)
            status["models"] = [m["name"] for m in models]
    except Exception:
        pass

    # Check store
    entries = load_store()
    status["entries"] = len(entries)

    if entries:
        types = {}
        projects = set()
        for e in entries:
            t = e.get("type", "unknown")
            types[t] = types.get(t, 0) + 1
            if e.get("project"):
                projects.add(e["project"])
        status["types"] = types
        status["projects"] = list(projects)

    print(json.dumps(status, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Vector Memory CLI for Claude Code")
    sub = parser.add_subparsers(dest="command", required=True)

    # store
    p_store = sub.add_parser("store", help="Store content with embedding")
    p_store.add_argument("--content", "-c", required=True, help="Content to store")
    p_store.add_argument("--type", "-t", default="semantic", choices=["semantic", "episodic", "procedural"])
    p_store.add_argument("--project", "-p", default="", help="Project identifier")
    p_store.add_argument("--tags", default="", help="Comma-separated tags")
    p_store.set_defaults(func=cmd_store)

    # search
    p_search = sub.add_parser("search", help="Semantic search")
    p_search.add_argument("--query", "-q", required=True, help="Search query")
    p_search.add_argument("--limit", "-l", type=int, default=5, help="Max results")
    p_search.add_argument("--project", "-p", default="", help="Filter by project")
    p_search.add_argument("--min-score", type=float, default=0.3, help="Minimum similarity score")
    p_search.set_defaults(func=cmd_search)

    # reindex
    p_reindex = sub.add_parser("reindex", help="Re-index file memory into vector store")
    p_reindex.add_argument("--project", "-p", default="", help="Project identifier")
    p_reindex.set_defaults(func=cmd_reindex)

    # status
    p_status = sub.add_parser("status", help="Check vector memory status")
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
