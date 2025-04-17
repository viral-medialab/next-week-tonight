"""
graph_utils.py - Simplified version
Helper functions for graph processing and retrieval
"""
from pathlib import Path
import pyarrow.parquet as pq

# Default output directory
GRAPH_OUTPUT_DIR = Path("backend/graphrag/ragtest/output")

def get_graph(output_dir=None, force_reload=False):
    """
    Directly read parquet files and convert to graph data format.
    
    Parameters
    ----------
    output_dir : Path or str, optional
        Directory where parquet files are stored, defaults to GRAPH_OUTPUT_DIR
    force_reload : bool, optional
        Unused in this simplified version, kept for API compatibility
        
    Returns
    -------
    dict
        Graph data with nodes and links ready for frontend visualization
    """
    # Use the provided directory or default
    out_dir = Path(output_dir) if output_dir else GRAPH_OUTPUT_DIR
    
    # Fixed filenames - GraphRAG always produces these files
    nodes_path = out_dir / "entities.parquet"
    edges_path = out_dir / "relationships.parquet"
    
    # Verify files exist
    if not nodes_path.exists() or not edges_path.exists():
        raise FileNotFoundError(f"Could not find required parquet files in {out_dir}")
    
    print(f"Loading graph from {nodes_path} and {edges_path}")
    
    # Read the parquet files
    nodes_tbl = pq.read_table(nodes_path)
    edges_tbl = pq.read_table(edges_path)
    
    # Build nodes list
    nodes = []
    label_to_id = {}  # For quick lookups when building links
    
    for row in nodes_tbl.to_pylist():
        # Extract the label from various possible fields
        label = (
            row.get("name") or 
            row.get("label") or 
            row.get("title") or 
            row.get("id") or 
            row.get("entity_id")
        )
        
        if not label:
            continue  # Skip malformed rows
            
        node_id = str(label)  # Use label as ID for link resolution
        
        # Determine node group/category
        group = (
            row.get("community_id") or 
            row.get("type") or 
            row.get("category") or 
            "entity"
        )
        
        # Collect other properties
        props = {k: v for k, v in row.items() if k not in {
            "id", "entity_id", "name", "label", "title", 
            "community_id", "type", "category"
        }}
        
        # Add node to list
        nodes.append({
            "id": node_id, 
            "label": node_id, 
            "group": group, 
            "properties": props
        })
        
        # Store for quick lookup
        label_to_id[node_id] = node_id
    
    # Build links list
    links = []
    
    for row in edges_tbl.to_pylist():
        # Extract source and target from various possible fields
        source_lbl = (
            row.get("source") or 
            row.get("from") or 
            row.get("from_id") or 
            row.get("subject_id") or 
            row.get("entity_a_id")
        )
        
        target_lbl = (
            row.get("target") or 
            row.get("to") or 
            row.get("to_id") or 
            row.get("object_id") or 
            row.get("entity_b_id")
        )
        
        if not source_lbl or not target_lbl:
            continue  # Skip if missing source or target
            
        # Look up IDs from our nodes
        source = label_to_id.get(str(source_lbl))
        target = label_to_id.get(str(target_lbl))
        
        if not source or not target:
            continue  # Skip dangling edges
            
        # Get relationship type/label
        label = (
            row.get("relationType") or 
            row.get("predicate") or 
            row.get("label") or 
            "related"
        )
        
        # Collect other properties
        props = {k: v for k, v in row.items() if k not in {
            "source", "from", "from_id", "subject_id", "entity_a_id",
            "target", "to", "to_id", "object_id", "entity_b_id",
            "relationType", "predicate", "label"
        }}
        
        # Add link to list
        links.append({
            "source": source, 
            "target": target, 
            "label": label, 
            "properties": props
        })
    
    # Return the complete graph data
    return {"nodes": nodes, "links": links}
