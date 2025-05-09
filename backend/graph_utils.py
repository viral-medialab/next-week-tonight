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
    communities_path = out_dir / "communities.parquet"
    
    # Verify files exist
    if not nodes_path.exists() or not edges_path.exists() or not communities_path.exists():
        raise FileNotFoundError(f"Could not find required parquet files in {out_dir}")
    
    print(f"Loading graph from {nodes_path} and {edges_path}")
    
    # Read the parquet files
    nodes_tbl = pq.read_table(nodes_path)
    edges_tbl = pq.read_table(edges_path)
    communities_tbl = pq.read_table(communities_path)

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
    # Convert the table to a list of dictionaries
    communities = communities_tbl.to_pylist()

    # Process each community
    processed_communities = []
    for community in communities:
        # Extract the required information
        processed_community = {
            'id': community.get('human_readable_id'),
            'label': community.get('title'),
            'nodes': community.get('entity_ids',[]),
            # 'edges': community.get('relationship_ids',[]) I'm not sure if this is needed
        }
        processed_communities.append(processed_community)
    # Return the complete graph data
    return {"nodes": nodes, "links": links, "reports":processed_communities}

def get_report_nodes(output_dir=None, force_reload=False):
    # Use the provided directory or default
    out_dir = Path(output_dir) if output_dir else GRAPH_OUTPUT_DIR
    
    # Fixed filenames - GraphRAG always produces these files
    nodes_path = out_dir / "entities.parquet"
    edges_path = out_dir / "relationships.parquet"
    communities_path = out_dir / "communities.parquet"
    
    # Verify files exist
    if not nodes_path.exists() or not edges_path.exists() or not communities_path.exists():
        raise FileNotFoundError(f"Could not find required parquet files in {out_dir}")
    
    # Read the parquet files
    nodes_tbl = pq.read_table(nodes_path)
    edges_tbl = pq.read_table(edges_path)
    communities_tbl = pq.read_table(communities_path)

    #Variable that stores node raw_id to label
    id_to_label = {}

    #Variable that stores node human_id to label for lookup in citations
    human_id_to_label = {}

    #Store node id_to human_readable in dictionary
    for row in nodes_tbl.to_pylist():         
        node_id = row.get('id')
        node_title = row.get('title')
        node_human_id = row.get('human_readable_id')
        id_to_label[node_id] = node_title
        human_id_to_label[node_human_id] = node_title

    #Link_id to source-target
    link_id_to_nodes = {}

    #Store link_id to {source: source_node_label, target: target_node_label}
    edges = edges_tbl.to_pylist()
    for edge in edges:
        edge_human_id = edge.get('human_readable_id')
        source, target = edge.get('source'), edge.get('target')
        link_id_to_nodes[edge_human_id] = {'source':source, 'target':target}

    # Convert the table to a list of dictionaries
    communities = communities_tbl.to_pylist()

    # Process each community
    processed_communities = {}
    for community in communities:
        # Extract the required information
        report_node_ids = community.get('entity_ids')
        entities = [id_to_label.get(node_id) for node_id in report_node_ids if id_to_label.get(node_id) is not None]

        #Get the human id from raw_id
        report_human_id = community.get('human_readable_id')

        #Set the output
        processed_communities[report_human_id] = entities

    return (processed_communities, human_id_to_label, link_id_to_nodes)

def extract_citations_from_response(stdout, output_dir):
    """
    Helper function to extract and lookup citations from GraphRAG response.
    
    Args:
        stdout (str): The response text from GraphRAG
        output_dir (Path): Directory containing the parquet files
        
    Returns:
        dict: Dictionary containing parsed citations and their data
    """
    import pandas as pd
    import re
    import pyarrow.parquet as pq
    
    # Initialize citation containers
    citations = {
        'reports': [],
        'relationships': [],
        'entities': [],
        'raw_matches': []
    }
    try:
        # Load parquet files if they exist
        # data_files = {
        #     'reports': pq.read_table(output_dir / "community_reports.parquet").to_pylist() if (output_dir / "community_reports.parquet").exists() else None,
        #     'relationships': pq.read_table(output_dir / "relationships.parquet").to_pylist() if (output_dir / "relationships.parquet").exists() else None,
        #     'entities': pq.read_table(output_dir / "entities.parquet").to_pylist() if (output_dir / "entities.parquet").exists() else None
        # }
        
        # Extract citations using regex patterns
        # Regex to capture individual data items inside [Data: ...]
    
        citation_pattern = r'\[Data:\s*((?:Reports|Entities|Relationships)\s*\(\d+\)(?:,\s*(?:Reports|Entities|Relationships)\s*\(\d+\))*)\]'

        # Regex to extract each (type, id) pair
        entry_pattern = r'(Reports|Entities|Relationships)\s*\((\d+)\)'

        # Initialize result
        citation_dict = {'reports': [], 'entities': [], 'relationships': []}

        # Extract citation blocks
        matches = re.findall(citation_pattern, stdout)

        for match in matches:
            entries = re.findall(entry_pattern, match)
            for dtype, did in entries:
                key = dtype.lower()  # convert to 'reports', 'entities', 'relationships'
                citation_dict[key].append(int(did)) 

        #Get a dictionary mapping report_human_id : [list of node human ids], node_human_id : node_label, edge_human_id: {'source':node_label,'target':node_label}
        report_id_to_node_ids, node_human_id_to_label, edge_human_id_to_nodes = get_report_nodes(output_dir)
        citations['highlightNodes'] = []
        citations['highlightEdges'] = []
        highlightNodeSet = set()
        # Find all citations in the text
        for citation_type, matches in citation_dict.items():
            if not matches:
                continue

            for item_id in matches:
                item_id = int(item_id)
                citation_info = {
                    'type': citation_type,
                    'id': item_id,
                }
                #Extract child nodes from reports
                if citation_type == 'reports':
                    #Get the human_ids of the report's sources and add them to the highlight list
                    report_child_nodes = report_id_to_node_ids.get(item_id,[])

                    #Extract and add the nodes in the report
                    for node_human_id in report_child_nodes:
                        if node_human_id not in citations['highlightNodes']:
                            citations['highlightNodes'].append(node_human_id)
                            highlightNodeSet.add(node_human_id)

                #Extract nodes
                elif citation_type == 'entities':
                    citations['highlightNodes'].append(node_human_id_to_label[item_id])
                    highlightNodeSet.add(node_human_id_to_label[item_id])

                #Add edges to be highlighted
                elif citation_type == 'relationships':

                    #{'source':node_label,'target':node_label}
                    edge_source_target = edge_human_id_to_nodes.get(item_id)
                    citations['highlightEdges'].append(edge_source_target)
                    
                # Add to raw matches for reference
                citations['raw_matches'].append(f"{citation_type}({item_id})")
                citations[citation_type].append(citation_info)

        #Highlight all edges that have source and target in highlightNodes
        for edge in edge_human_id_to_nodes.values():
            source, target = edge['source'], edge['target']
            if source in highlightNodeSet and target in highlightNodeSet:
                citations['highlightEdges'].append(edge)

        return citations
        
    except Exception as e:
        print(f"Error extracting citations: {str(e)}")
        return citations