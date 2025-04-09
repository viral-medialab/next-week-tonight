"""
graph_utils.py
Helpers for turning GraphRAG parquet / LanceDB output into the
{ nodes:[…], links:[…] } structure expected by react‑force‑graph.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List

import pyarrow.parquet as pq

# LanceDB enrichment is optional
try:
    import lance
except ImportError:  # pragma: no cover
    lance = None  # type: ignore

# ────────────────────────────────────────────────────────────────────────────────
#  Configuration
# ────────────────────────────────────────────────────────────────────────────────
GRAPH_OUTPUT_DIR = (
    Path(__file__).resolve().parent / "graphrag" / "ragtest" / "output"
)
DEFAULT_NODES_FILE = "nodes.parquet"
DEFAULT_EDGES_FILE = "edges.parquet"

# ────────────────────────────────────────────────────────────────────────────────
#  File‑location helpers
# ────────────────────────────────────────────────────────────────────────────────
def _first_file_with_keyword(directory: Path, keywords: tuple[str, ...]) -> Path | None:
    """Return the first *.parquet file whose name contains ANY keyword (case‑insensitive)."""
    for f in directory.iterdir():
        if f.is_file() and f.suffix == ".parquet":
            low = f.name.lower()
            if any(k in low for k in keywords):
                return f
    return None


def _locate_parquet_files(out_dir: Path) -> tuple[Path, Path]:
    """
    Find the parquet files that contain nodes and edges.

    Tries, in order:
      1. nodes.parquet / edges.parquet
      2. entities.parquet / relationships.parquet      (GraphRAG default)
      3. any *nodes|entities*  +  any *edges|relationships* file
    """
    # 1. explicit
    p_nodes, p_edges = out_dir / DEFAULT_NODES_FILE, out_dir / DEFAULT_EDGES_FILE
    if p_nodes.exists() and p_edges.exists():
        return p_nodes, p_edges

    # 2. GraphRAG default
    p_nodes, p_edges = out_dir / "entities.parquet", out_dir / "relationships.parquet"
    if p_nodes.exists() and p_edges.exists():
        return p_nodes, p_edges

    # 3. fuzzy
    nodes = _first_file_with_keyword(out_dir, ("nodes", "entities"))
    edges = _first_file_with_keyword(out_dir, ("edges", "relationships"))
    if nodes and edges:
        return nodes, edges

    raise FileNotFoundError(f"Could not find a nodes‑and‑edges parquet pair in {out_dir}")


# ────────────────────────────────────────────────────────────────────────────────
#  Loader
# ────────────────────────────────────────────────────────────────────────────────
def _load_graph_from_parquet(out_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Read parquet (and optional LanceDB) → force‑graph JSON."""
    nodes_path, edges_path = _locate_parquet_files(out_dir)

    nodes_tbl = pq.read_table(nodes_path)
    edges_tbl = pq.read_table(edges_path)

    # Build nodes (ID = human‑readable label to match link strings)
    nodes: list[dict[str, Any]] = []
    label_to_id: dict[str, str] = {}  # map for quick look‑ups
    for row in nodes_tbl.to_pylist():
        label = (
            row.get("name")
            or row.get("label")
            or row.get("title")
            or row.get("id")
            or row.get("entity_id")
        )
        if not label:
            continue  # skip malformed row
        node_id = str(label)  # use label as id so links resolve
        group = (
            row.get("community_id")
            or row.get("type")
            or row.get("category")
            or "entity"
        )
        props = {
            k: v
            for k, v in row.items()
            if k
            not in {
                "id",
                "entity_id",
                "name",
                "label",
                "title",
                "community_id",
                "type",
                "category",
            }
        }
        # keep original UUID if present
        if row.get("id") and str(row["id"]) != node_id:
            props["original_id"] = str(row["id"])
        nodes.append({"id": node_id, "label": node_id, "group": group, "properties": props})
        label_to_id[node_id] = node_id

    # Build links
    links: list[dict[str, Any]] = []
    for row in edges_tbl.to_pylist():
        source_lbl = (
            row.get("source")
            or row.get("from")
            or row.get("from_id")
            or row.get("subject_id")
            or row.get("entity_a_id")
        )
        target_lbl = (
            row.get("target")
            or row.get("to")
            or row.get("to_id")
            or row.get("object_id")
            or row.get("entity_b_id")
        )
        if not source_lbl or not target_lbl:
            continue
        source = label_to_id.get(str(source_lbl))
        target = label_to_id.get(str(target_lbl))
        if not source or not target:
            # skip dangling edge
            continue
        label = (
            row.get("relationType")
            or row.get("predicate")
            or row.get("label")
            or "related"
        )
        props = {
            k: v
            for k, v in row.items()
            if k
            not in {
                "source",
                "from",
                "from_id",
                "subject_id",
                "entity_a_id",
                "target",
                "to",
                "to_id",
                "object_id",
                "entity_b_id",
                "relationType",
                "predicate",
                "label",
            }
        }
        links.append({"source": source, "target": target, "label": label, "properties": props})

    # Optional community enrichment (keeps 'group' field consistent)
    comm_path = out_dir / "default-community-full_content.lance"
    if lance and comm_path.exists():
        ds = lance.dataset(str(comm_path))
        comm_map = {
            str(r.get("entity_id") or r.get("id") or r.get("label")): r.get("community_id")
            for r in ds.to_arrow().to_pylist()
        }
        for n in nodes:
            if n["id"] in comm_map:
                n["group"] = comm_map[n["id"]]

    return {"nodes": nodes, "links": links}


# ────────────────────────────────────────────────────────────────────────────────
#  Tiny cache (invalidate on mtime change)
# ────────────────────────────────────────────────────────────────────────────────
_graph_cache: dict[str, Any] = {"payload": None, "mtime": 0.0}


def _graph_mtime(out_dir: Path) -> float:
    try:
        nodes, edges = _locate_parquet_files(out_dir)
    except FileNotFoundError:
        return 0.0
    return max(nodes.stat().st_mtime, edges.stat().st_mtime)


def get_graph(out_dir: Path | None = None, *, force_reload: bool = False):
    """
    Return the latest graph (cached unless parquet files changed).

    Parameters
    ----------
    out_dir : Path | None
        Directory containing GraphRAG output; defaults to `GRAPH_OUTPUT_DIR`.
    force_reload : bool
        If True, bypass cache.
    """
    global _graph_cache
    out_dir = Path(out_dir) if out_dir else GRAPH_OUTPUT_DIR

    latest_mtime = _graph_mtime(out_dir)
    if (
        not force_reload
        and _graph_cache["payload"] is not None
        and latest_mtime <= _graph_cache["mtime"]
    ):
        return _graph_cache["payload"]

    payload = _load_graph_from_parquet(out_dir)
    _graph_cache = {"payload": payload, "mtime": latest_mtime}
    return payload
