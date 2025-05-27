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
            "ENTITY"
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

    # Check for community_reports.parquet
    reports_path = out_dir / "community_reports.parquet"
    if reports_path.exists():
        reports_tbl = pq.read_table(reports_path)
        reports_data = reports_tbl.to_pylist()
        print(f"Found {len(reports_data)} reports in community_reports.parquet")
        
        # Map report IDs to their content
        for report in reports_data:
            report_id = report.get('human_readable_id')
            if report_id is not None:
                report_human_id = report_id
                # Extract entities mentioned in this report
                if 'entity_ids' in report:
                    entity_ids = report.get('entity_ids', [])
                    # Add these to the processed_communities map
                    processed_communities[report_human_id] = [
                        id_to_label.get(node_id) for node_id in entity_ids 
                        if id_to_label.get(node_id) is not None
                    ]

    return (processed_communities, human_id_to_label, link_id_to_nodes)

def extract_citations_from_response(stdout, output_dir):
    """
    Helper function to extract and lookup citations from GraphRAG response.
    Recursively processes citations in report content with improved pattern matching.
    """
    import pandas as pd
    import re
    import pyarrow.parquet as pq
    
    # Initialize citation containers
    citations = {
        'reports': [],
        'relationships': [],
        'entities': [],
        'raw_matches': [],
        'highlightNodes': [],
        'highlightEdges': []
    }
    
    try:
        # Original citation patterns - keep these
        citation_pattern = r'\[Data:\s*((?:Reports|Entities|Relationships)\s*\(\d+\)(?:,\s*(?:Reports|Entities|Relationships)\s*\(\d+\))*)\]'
        loose_citation_pattern = r'(Reports|Entities|Relationships)\s*\((\d+)\)'
        
        # NEW pattern for comma-separated IDs in citations
        complex_citation_pattern = r'\[Data:\s*((?:Reports|Entities|Relationships)\s*\([\d,\s+more]+\)(?:,\s*(?:Reports|Entities|Relationships)\s*\([\d,\s+more]+\))*)\]'
        complex_entry_pattern = r'(Reports|Entities|Relationships)\s*\(([\d,\s+more]+)\)'
        
        # Extract citation blocks from main text using original patterns
        main_matches = re.findall(citation_pattern, stdout)
        process_citation_matches(main_matches, citations, loose_citation_pattern)
        
        # Also scan for standalone citations not in [Data:] blocks (original approach)
        standalone_matches = re.findall(loose_citation_pattern, stdout)
        for citation_type, citation_id in standalone_matches:
            add_citation(citations, citation_type, citation_id)
        
        # NEW: Also extract complex citation blocks with comma-separated IDs
        complex_matches = re.findall(complex_citation_pattern, stdout)
        for match in complex_matches:
            # Extract each citation type (Reports/Entities/Relationships) with their IDs
            citation_entries = re.findall(complex_entry_pattern, match)
            
            for entry_type, entry_ids in citation_entries:
                # Clean and extract individual IDs
                # Remove '+more' and any other non-numeric content
                clean_ids = re.sub(r'[+more\s]', '', entry_ids)
                
                # Split by comma to get individual IDs
                id_list = [id.strip() for id in clean_ids.split(',') if id.strip()]
                
                # Add each ID as a citation
                for id_str in id_list:
                    if id_str.isdigit():
                        add_citation(citations, entry_type, id_str)
        
        # Now get report content to look for nested citations
        reports_path = output_dir / "community_reports.parquet"
        if reports_path.exists():
            # Get the IDs of cited reports
            cited_report_ids = [str(report['id']) for report in citations['reports']]
            
            if cited_report_ids:
                # Load report data
                reports_tbl = pq.read_table(reports_path)
                reports_data = reports_tbl.to_pylist()
                
                # For each cited report, extract additional citations from its content
                for report in reports_data:
                    report_id = str(report.get('id', '')) or str(report.get('human_readable_id', ''))
                    
                    if report_id in cited_report_ids:
                        # Check various possible content fields
                        for content_field in ['full_content', 'text', 'content', 'summary']:
                            if content_field in report and report[content_field]:
                                # Extract citations from report content - use original patterns
                                report_matches = re.findall(citation_pattern, report[content_field])
                                process_citation_matches(report_matches, citations, loose_citation_pattern)
                                
                                # Also look for standalone citations (original approach)
                                standalone_matches = re.findall(loose_citation_pattern, report[content_field])
                                for citation_type, citation_id in standalone_matches:
                                    add_citation(citations, citation_type, citation_id)
                                
                                # NEW: Look for complex citations within reports
                                complex_report_matches = re.findall(complex_citation_pattern, report[content_field])
                                for rmatch in complex_report_matches:
                                    # Extract each citation type with their IDs
                                    citation_entries = re.findall(complex_entry_pattern, rmatch)
                                    
                                    for entry_type, entry_ids in citation_entries:
                                        # Clean and extract individual IDs
                                        clean_ids = re.sub(r'[+more\s]', '', entry_ids)
                                        
                                        # Split by comma to get individual IDs
                                        id_list = [id.strip() for id in clean_ids.split(',') if id.strip()]
                                        
                                        # Add each ID as a citation
                                        for id_str in id_list:
                                            if id_str.isdigit():
                                                add_citation(citations, entry_type, id_str)
        
        # Get the mapping data for nodes and relationships
        report_id_to_node_ids, node_human_id_to_label, edge_human_id_to_nodes = get_report_nodes(output_dir)
        
        # Process all collected citations to add highlight nodes and edges
        highlightNodeSet = set()
        
        # Process each citation type
        for citation_type, citation_list in [
            ('reports', citations['reports']), 
            ('entities', citations['entities']), 
            ('relationships', citations['relationships'])
        ]:
            for citation_info in citation_list:
                item_id = citation_info['id']
                
                if citation_type == 'reports':
                    # Add nodes from the report
                    report_child_nodes = report_id_to_node_ids.get(item_id, [])
                    for node_human_id in report_child_nodes:
                        if node_human_id not in citations['highlightNodes']:
                            citations['highlightNodes'].append(node_human_id)
                            highlightNodeSet.add(node_human_id)
                            
                elif citation_type == 'entities':
                    # Add entity nodes
                    if item_id in node_human_id_to_label:
                        node_label = node_human_id_to_label[item_id]
                        if node_label not in citations['highlightNodes']:
                            citations['highlightNodes'].append(node_label)
                            highlightNodeSet.add(node_label)
                            
                elif citation_type == 'relationships':
                    # Add relationship edges
                    edge_source_target = edge_human_id_to_nodes.get(item_id)
                    if edge_source_target:
                        # Check if this edge is already in highlightEdges
                        edge_already_exists = False
                        for existing_edge in citations['highlightEdges']:
                            if (existing_edge.get('source') == edge_source_target.get('source') and 
                                existing_edge.get('target') == edge_source_target.get('target')):
                                edge_already_exists = True
                                break
                                
                        if not edge_already_exists:
                            citations['highlightEdges'].append(edge_source_target)
                            
                            # Also add the source and target nodes to highlightNodes
                            source_label = edge_source_target.get('source')
                            target_label = edge_source_target.get('target')
                            
                            if source_label and source_label not in citations['highlightNodes']:
                                citations['highlightNodes'].append(source_label)
                                highlightNodeSet.add(source_label)
                                
                            if target_label and target_label not in citations['highlightNodes']:
                                citations['highlightNodes'].append(target_label)
                                highlightNodeSet.add(target_label)
        
        # Highlight edges between highlighted nodes (transitive closure)
        for edge in edge_human_id_to_nodes.values():
            source, target = edge.get('source'), edge.get('target')
            if source in highlightNodeSet and target in highlightNodeSet:
                # Check if this edge is already in highlightEdges
                edge_already_exists = False
                for existing_edge in citations['highlightEdges']:
                    if (existing_edge.get('source') == source and 
                        existing_edge.get('target') == target):
                        edge_already_exists = True
                        break
                        
                if not edge_already_exists:
                    citations['highlightEdges'].append(edge)
        
        return citations
        
    except Exception as e:
        print(f"Error extracting citations: {str(e)}")
        return citations

def process_citation_matches(matches, citations, entry_pattern):
    """Helper function to process regex matches and add them to citations dict"""
    import re
    
    for match in matches:
        entries = re.findall(entry_pattern, match)
        for dtype, did in entries:
            key = dtype.lower()  # convert to 'reports', 'entities', 'relationships'
            
            # Check if this citation already exists
            citation_exists = False
            for existing_citation in citations[key]:
                if existing_citation['id'] == int(did):
                    citation_exists = True
                    break
                    
            if not citation_exists:
                citations[key].append({
                    'type': key,
                    'id': int(did)
                })
                
                # Add to raw matches
                raw_match = f"{key}({did})"
                if raw_match not in citations['raw_matches']:
                    citations['raw_matches'].append(raw_match)

def add_citation(citations, citation_type, citation_id):
    """Helper function to add a citation of a specific type and ID to the citations dict"""
    key = citation_type.lower()  # convert to 'reports', 'entities', 'relationships'
    
    # Check if this citation already exists
    citation_exists = False
    for existing_citation in citations[key]:
        if existing_citation['id'] == int(citation_id):
            citation_exists = True
            break
            
    if not citation_exists:
        citations[key].append({
            'type': key,
            'id': int(citation_id)
        })
        
        # Add to raw matches
        raw_match = f"{key}({citation_id})"
        if raw_match not in citations['raw_matches']:
            citations['raw_matches'].append(raw_match)

def enhance_citations_with_details(citations, output_dir):
    """
    Enhances citation information with detailed node and relationship data from the graph.
    Ensures that each citation appears only once in the result.
    
    Args:
        citations (dict): Citations extracted from the GraphRAG response
        output_dir (Path): Directory containing the parquet files
        
    Returns:
        dict: Enhanced citations with detailed information (deduplicated)
    """
    import pyarrow.parquet as pq
    
    enhanced = {
        'reports': [],
        'entities': [],
        'relationships': [],
        'highlightedNodes': [],
        'highlightedEdges': []
    }
    
    # Track processed items to avoid duplication
    processed_reports = set()
    processed_entities = set()
    processed_relationships = set()
    processed_nodes = set()
    processed_edges = set()
    
    # Load the full graph data for node and link details
    full_graph = get_graph(output_dir)
    
    # Load community reports directly from parquet
    reports_path = output_dir / "community_reports.parquet"
    if reports_path.exists():
        reports_tbl = pq.read_table(reports_path)
        reports_data = reports_tbl.to_pylist()
        print(f"Loaded {len(reports_data)} reports from {reports_path}")
    else:
        reports_data = []
        print(f"No community reports found at {reports_path}")
    
    # Create lookups for nodes and links
    nodes_by_label = {}
    for node in full_graph.get('nodes', []):
        label = node.get('label')
        if label:
            nodes_by_label[str(label).upper()] = node
    
    # Process highlighted nodes
    highlight_nodes = citations.get('highlightNodes', [])
    for node_label in highlight_nodes:
        # Skip if we've already processed this node
        if node_label in processed_nodes:
            continue
        
        # Look for node by label (case-insensitive)
        upper_label = str(node_label).upper()
        node_details = nodes_by_label.get(upper_label)
        
        if node_details:
            enhanced['highlightedNodes'].append({
                'label': node_label,
                'details': node_details
            })
            processed_nodes.add(node_label)
        else:
            # If not found in nodes_by_label, search through all nodes
            for node in full_graph.get('nodes', []):
                if str(node.get('label', '')).upper() == upper_label:
                    enhanced['highlightedNodes'].append({
                        'label': node_label,
                        'details': node
                    })
                    processed_nodes.add(node_label)
                    break
    
    # Process highlighted edges
    highlight_edges = citations.get('highlightEdges', [])
    for edge in highlight_edges:
        source_label = edge.get('source', '')
        target_label = edge.get('target', '')
        
        # Create a unique edge identifier
        edge_id = f"{source_label}→{target_label}"
        
        # Skip if we've already processed this edge
        if edge_id in processed_edges:
            continue
        
        # Find matching edge in the graph
        for link in full_graph.get('links', []):
            link_source = link.get('source')
            link_target = link.get('target')
            
            source_match = False
            target_match = False
            
            # Check source match
            if isinstance(link_source, dict) and str(link_source.get('label', '')).upper() == source_label.upper():
                source_match = True
            elif str(link_source).upper() == source_label.upper():
                source_match = True
                
            # Check target match
            if isinstance(link_target, dict) and str(link_target.get('label', '')).upper() == target_label.upper():
                target_match = True
            elif str(link_target).upper() == target_label.upper():
                target_match = True
                
            if source_match and target_match:
                enhanced['highlightedEdges'].append({
                    'source': source_label,
                    'target': target_label,
                    'details': link
                })
                processed_edges.add(edge_id)
                break
    
    # Process entity citations
    for entity_citation in citations.get('entities', []):
        entity_id = entity_citation.get('id')
        
        # Skip if we've already processed this entity
        if entity_id in processed_entities:
            continue
            
        if entity_id is not None:
            for node in full_graph.get('nodes', []):
                if (str(node.get('id')) == str(entity_id) or 
                    str(node.get('human_readable_id')) == str(entity_id)):
                    enhanced['entities'].append({
                        'id': entity_id,
                        'type': 'entity',
                        'details': node
                    })
                    processed_entities.add(entity_id)
                    break
    
    # Process relationship citations
    for rel_citation in citations.get('relationships', []):
        rel_id = rel_citation.get('id')
        
        # Skip if we've already processed this relationship
        if rel_id in processed_relationships:
            continue
            
        if rel_id is not None:
            for link in full_graph.get('links', []):
                if (str(link.get('id')) == str(rel_id) or
                    str(link.get('properties', {}).get('id', '')) == str(rel_id)):
                    enhanced['relationships'].append({
                        'id': rel_id,
                        'type': 'relationship',
                        'details': link
                    })
                    processed_relationships.add(rel_id)
                    break
    
    # Process report citations - directly access community_reports.parquet
    for report_citation in citations.get('reports', []):
        report_id = report_citation.get('id')
        
        # Skip if we've already processed this report
        if report_id in processed_reports:
            continue
            
        if report_id is not None:  # Handle ID 0 correctly
            # Look for the report in the reports data
            for report in reports_data:
                # Try matching on various possible ID fields
                if (str(report.get('id', '')) == str(report_id) or 
                    str(report.get('human_readable_id', '')) == str(report_id) or
                    str(report.get('report_id', '')) == str(report_id)):
                    
                    # Create enhanced report with all available data
                    enhanced_report = {
                        'id': report_id,
                        'type': 'report',
                        'title': report.get('title', f"Report {report_id}"),
                        'text': report.get('text', report.get('content', report.get('summary', ''))),
                        'details': report,
                        # Include all properties
                        'properties': {k: v for k, v in report.items() 
                                    if k not in ['id', 'human_readable_id', 'report_id', 'title', 
                                                'text', 'content', 'summary']}
                    }
                    
                    # Also gather nodes referenced in this report
                    if 'entity_ids' in report:
                        report_nodes = []
                        for node_id in report.get('entity_ids', []):
                            for node in full_graph.get('nodes', []):
                                if str(node.get('id')) == str(node_id):
                                    report_nodes.append(node)
                                    break
                        enhanced_report['nodes'] = report_nodes
                    
                    enhanced['reports'].append(enhanced_report)
                    processed_reports.add(report_id)
                    break
    
    # If reports are still empty, try looking in communities data
    if not enhanced['reports'] and citations.get('reports'):
        for report_citation in citations.get('reports', []):
            report_id = report_citation.get('id')
            
            # Skip if we've already processed this report
            if report_id in processed_reports:
                continue
                
            if report_id is not None and full_graph.get('communities'):
                for community in full_graph.get('communities', []):
                    if str(community.get('id')) == str(report_id):
                        # Get nodes for this community
                        community_nodes = []
                        for node_id in community.get('nodes', []):
                            for node in full_graph.get('nodes', []):
                                if str(node.get('id')) == str(node_id):
                                    community_nodes.append(node)
                                    break
                        
                        enhanced['reports'].append({
                            'id': report_id,
                            'type': 'community',
                            'title': community.get('label', f"Community {report_id}"),
                            'details': community,
                            'nodes': community_nodes
                        })
                        processed_reports.add(report_id)
                        break
    
    # Print debugging info
    print(f"Enhanced citations: {len(enhanced['reports'])} reports, {len(enhanced['highlightedNodes'])} highlighted nodes, {len(enhanced['highlightedEdges'])} highlighted edges")
    
    return enhanced