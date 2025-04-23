"""
news_broom.py
Flask API - imports helpers from graph_utils.py
"""
from pathlib import Path
import traceback, sys
import json
import os

from flask import Flask, jsonify, request
from flask_cors import CORS

# Project helpers
from graph_utils import get_graph, GRAPH_OUTPUT_DIR

# (Your existing project imports remain – shortened here)
from predictions.query_utils import *            # noqa: F401,F403
from api.article_utils import *                  # noqa: F401,F403
from database.database_utils import clear_cache, save_generated_article_to_DB  # noqa: F401
import openai
from test.env import OPENAI_API_KEY
import re

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ────────────────────────────────────────────────────────────────────────────────
#  Flask app
# ────────────────────────────────────────────────────────────────────────────────
app = Flask(__name__)
# Use the simplest CORS configuration
CORS(app, resources={r"/*": {"origins": "*"}})


@app.route("/")
def home():
    return "News Broom backend is running successfully"


# ╭──────────────────────────────────────────────────────────────────────────────╮
# │ Knowledge‑graph endpoint                                                    │
# ╰──────────────────────────────────────────────────────────────────────────────╯
@app.route("/api/get_topic_overview", methods=["GET", "POST"])
def get_topic_overview():
    """
    Get the overview of the topic from perplexity response file
    
    Expected JSON body:
    {
        "query": "topic to search for"
    }
    
    Returns:
        JSON with status, message, topic overview content, and file path
    """
    try:
        # Get query from request body
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "Missing 'query' in request body"}), 400
            
        query = data['query']
        
        # Create folder name from query (must match the logic in gather_news_sources)
        folder_name = "_".join(query.split()[:4])  # First 4 words
        folder_name = "".join(c for c in folder_name if c.isalnum() or c == '_')  # Remove special chars
        folder_name = f"{folder_name}_input"
        
        # Create full folder path
        folder = Path("backend/graphrag/ragtest") / folder_name
        
        # Check if folder exists
        if not folder.exists():
            return jsonify({
                "status": "error",
                "message": f"No data found for topic '{query}'. Please run gather_news_sources first."
            }), 404
        
        # Construct the path to the perplexity response file
        safe_query = "".join(x for x in query if x.isalnum() or x.isspace()).rstrip()
        safe_query = safe_query.replace(" ", "_")[:50]  # Limit length
        response_filename = f"{safe_query}_perplexity_response.txt"
        response_file_path = folder / response_filename
        
        # Check if perplexity response file exists
        if not response_file_path.exists():
            return jsonify({
                "status": "error",
                "message": f"Perplexity response file not found for topic '{query}'. Please run gather_news_sources first."
            }), 404
            
        # Read the perplexity response file
        with open(response_file_path, 'r', encoding='utf-8') as file:
            overview_content = file.read()
            
        return jsonify({
            "status": "success",
            "message": "Topic overview retrieved successfully",
            "data": {
                "query": query,
                "overview": overview_content,
                "file_path": str(response_file_path)
            }
        })
        
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        return jsonify({
            "status": "error",
            "message": f"Error retrieving topic overview: {str(e)}"
        }), 500

@app.route("/api/gather_news_sources", methods=["POST"])
def gather_news_sources():
    """
    Gather news sources from user topic input using Perplexity API
    
    Expected JSON body:
    {
        "query": "topic to search for"
    }
    
    Returns:
        JSON with status, message, and extracted sources info
    """
    try:
        # Get query from request body
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "Missing 'query' in request body"}), 400
            
        query = data['query']
        
        # Create folder name from query
        # Take first few words, replace spaces with underscores, remove special chars
        folder_name = "_".join(query.split()[:4])  # First 4 words
        folder_name = "".join(c for c in folder_name if c.isalnum() or c == '_')  # Remove special chars
        folder_name = f"{folder_name}_input"
        
        # Create full folder path
        folder = Path("backend/graphrag/ragtest") / folder_name

        # Check if folder already exists and contains data
        if folder.exists():
            # Count number of text files (excluding perplexity response)
            saved_sources = []
            successful_extractions = 0
            
            for file in folder.glob("*.txt"):
                if not file.name.endswith("_perplexity_response.txt"):
                    successful_extractions += 1
                    with open(file, 'r', encoding='utf-8') as f:
                        first_line = f.readline().strip()
                        url = first_line.replace("Source: ", "") if first_line.startswith("Source: ") else "Unknown"
                        
                    saved_sources.append({
                        "url": url,
                        "filepath": str(file),
                        "successful": True,
                        "extraction_method": "Previously Extracted"
                    })

            if successful_extractions > 0:
                return jsonify({
                    "status": "success", 
                    "message": f"Found existing data with {successful_extractions} sources.",
                    "data": {
                        "query": query,
                        "folder": str(folder),
                        "num_sources": successful_extractions,
                        "successful_extractions": successful_extractions,
                        "sources": saved_sources,
                        "perplexity_response_saved": True,
                        "perplexity_response_file": str(folder / f"{''.join(x for x in query if x.isalnum() or x.isspace()).rstrip().replace(' ', '_')[:50]}_perplexity_response.txt")
                    }
                })
        
        # Ensure folder exists for new extraction
        folder.mkdir(parents=True, exist_ok=True)
        
        # Import the functions we need from extract_data_perplexity
        from database.extract_data_perplexity import (
            get_perplexity_sources, 
            save_text_to_file,
            extract_text_from_url
        )
        import pandas as pd
        
        # Get sources from Perplexity
        sources, perplexity_response = get_perplexity_sources(query)
        
        if not sources and not perplexity_response:
            return jsonify({
                "status": "error",
                "message": "No sources found from Perplexity API"
            }), 404
            
        # Save the Perplexity response
        response_file = None
        if perplexity_response:
            response_file = save_text_to_file(
                perplexity_response, 
                query, 
                "", 
                folder=str(folder), 
                is_perplexity_response=True
            )
        
        # For keeping track of extraction results
        saved_sources = []
        successful_extractions = 0
        
        if sources:
            # Create a DataFrame to pass to extract_text_from_url
            sources_df = pd.DataFrame({'url': sources})
            
            # Extract text using the functions from extract_raw_text.py
            article_texts = extract_text_from_url(sources_df)
            
            # Save each extracted text to a file
            for i, (source, text) in enumerate(zip(sources, article_texts)):
                extraction_info = {
                    "url": source,
                    "successful": False,
                    "extraction_method": "Unknown"
                }
                
                # Check if extraction was successful
                if isinstance(text, tuple):  # If text is a tuple (score, content) from perplexity_text_extractor
                    score, content = text
                    if score.isnumeric() and int(score) >= 2:
                        text_to_save = content
                        extraction_method = f"Perplexity (score: {score})"
                        successful = True
                    else:
                        # Text was not good enough, but was already handled by extract_text_from_url
                        text_to_save = content
                        extraction_method = f"Perplexity with low score ({score}), fallback to BeautifulSoup"
                        successful = True
                elif text != "Extraction Failed":
                    text_to_save = text
                    extraction_method = "BeautifulSoup"
                    successful = True
                else:
                    text_to_save = "Could not extract text from this source."
                    extraction_method = "Failed"
                    successful = False
                
                # Save the text (even if failed, to keep record)
                try:
                    filepath = save_text_to_file(text_to_save, query, source, folder=str(folder))
                    
                    extraction_info.update({
                        "filepath": filepath,
                        "successful": successful,
                        "extraction_method": extraction_method
                    })
                    
                    if successful:
                        successful_extractions += 1
                except Exception as e:
                    print(f"Error saving source {source}: {str(e)}")
                    extraction_info["error"] = str(e)
                
                saved_sources.append(extraction_info)
                
        return jsonify({
            "status": "success",
            "message": f"News sources gathered successfully. Extracted {successful_extractions} out of {len(sources)} sources.",
            "data": {
                "query": query,
                "folder": str(folder),
                "num_sources": len(sources),
                "successful_extractions": successful_extractions,
                "sources": saved_sources,
                "perplexity_response_saved": bool(response_file),
                "perplexity_response_file": response_file
            }
        })
        
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        return jsonify({
            "status": "error",
            "message": f"Error gathering news sources: {str(e)}"
        }), 500

@app.route("/api/create_knowledge_graph", methods=["GET", "POST"])
def create_knowledge_graph():
    """
    Create a knowledge graph by indexing data from a topic-specific input folder
    and saving results to the default output folder.
    
    Expected JSON body:
    {
        "query": "topic to search for"
    }
    
    Returns:
        JSON with status, message, and knowledge graph info
    """
    try:
        # Import required modules
        import subprocess
        import os
        import yaml
        from pathlib import Path
        import shutil
        
        # Get query from request body
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "Missing 'query' in request body"}), 400
            
        query = data['query']
        print(f"Creating knowledge graph for query: {query}")
        
        # Use the EXACT SAME folder name creation logic as gather_news_sources
        folder_name = "_".join(query.split()[:4])  # First 4 words
        folder_name = "".join(c for c in folder_name if c.isalnum() or c == '_')  # Remove special chars
        input_folder = f"{folder_name}_input"
        output_folder = f"{folder_name}_output"
        
        # Define paths
        graphrag_dir = Path("backend/graphrag")
        ragtest_dir = graphrag_dir / "ragtest"
        
        # Make sure the ragtest directory exists
        ragtest_dir.mkdir(parents=True, exist_ok=True)
        
        settings_file = ragtest_dir / "settings.yaml"
        
        # Check if the input folder exists
        input_dir = ragtest_dir / input_folder
        output_dir = ragtest_dir / output_folder
        if not input_dir.exists():
            return jsonify({
                "status": "error",
                "message": f"Input folder {input_folder} does not exist. Please gather news sources first."
            }), 404
        
        # Make sure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Default settings if file doesn't exist
        default_settings = {
            "input": {"base_dir": "default_input"},
            "output": {"base_dir": "default_output"}
        }
        
        # Check if settings.yaml exists, create if not
        if not settings_file.exists():
            with open(settings_file, "w") as f:
                yaml.dump(default_settings, f, default_flow_style=False)
            print(f"Created new settings file at {settings_file}")
        
        # Read the current settings from file
        with open(settings_file, "r") as f:
            settings = yaml.safe_load(f)
        
        # Store original settings to restore later
        original_settings = settings.copy()
        
        # Update settings to use topic-specific folders
        settings["input"]["base_dir"] = input_folder
        settings["output"]["base_dir"] = output_folder
        print(f"Using input folder: {input_folder}")
        print(f"Using output folder: {output_folder}")
        
        # Write the updated settings back to the file
        with open(settings_file, "w") as f:
            yaml.dump(settings, f, default_flow_style=False)
        
        # Prepare the graphrag index command
        command = [
            "graphrag", "index",
            "--root", "./ragtest"
        ]
        
        # Execute the command
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(graphrag_dir)  # Change working directory
        )
        print("GraphRAG command executed")
        
        # Get the output and errors
        stdout, stderr = process.communicate()
        
        # Restore original settings
        with open(settings_file, "w") as f:
            yaml.dump(original_settings, f, default_flow_style=False)
        
        # Check if command was successful
        if process.returncode == 0:
            root_dir = graphrag_dir / "ragtest"
            output_dir = root_dir / output_folder
            
            # Look for output files in the output directory
            output_files = list(output_dir.glob("*.parquet")) if output_dir.exists() else []
            print(f"Output parquet files: {output_files}")
            output_json_files = list(output_dir.glob("*.json")) if output_dir.exists() else []
            print(f"Output json files: {output_json_files}")
            
            # Combine all found files
            all_output_files = output_files + output_json_files
            print(f"All output files: {all_output_files}")
            
            print("Knowledge graph indexed successfully with output files: ", all_output_files)
           
        else:
            return jsonify({
                "status": "error",
                "message": f"Error creating knowledge graph: {stderr}",
                "command": " ".join(command)
            }), 500
        
        data = get_graph(output_dir)
        return jsonify(data)
            
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        return jsonify({
            "status": "error",
            "message": f"Error creating knowledge graph: {str(e)}"
        }), 500


@app.route("/api/query_knowledge_graph", methods=["GET", "POST"])
def query_knowledge_graph():
    """
    Query the knowledge graph using GraphRAG global query method.
    
    Expected JSON body:
    {
        "query": "The question to ask about the knowledge graph",
        "topic": "The original topic that was used to create the knowledge graph",
        "num_sources": 5  // Optional: Number of sources to return (default: 3)
    }
    
    Returns:
        JSON with status, message, and query results
    """
    try:
        # Import required modules
        import subprocess
        import os
        import yaml
        from pathlib import Path
        import re
        
        # Get query from request body
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "Missing 'query' in request body"}), 400
        if not data or 'topic' not in data:
            return jsonify({"error": "Missing 'topic' in request body"}), 400
            
        original_query = data['query']
        topic = data['topic']
        num_sources = data.get('num_sources', 3)  # Default to 3 sources if not specified
        
        # Format the query to ask for scenarios from most likely to least likely
        # Check if query already ends with a question mark
        if original_query.endswith('?'):
            original_query = original_query[:-1]  # Remove the question mark
            
        # Format the query to ask for three scenarios
        formatted_query = f"Give me 3 scenarios from most likely to least likely about what would happen if {original_query}. Make each scenario different from the others. For each scenario, explain the reasoning and cite relevant sources."
        
        # Use the EXACT SAME folder name creation logic as create_knowledge_graph
        folder_name = "_".join(topic.split()[:4])  # First 4 words
        folder_name = "".join(c for c in folder_name if c.isalnum() or c == '_')  # Remove special chars
        input_folder = f"{folder_name}_input"
        output_folder = f"{folder_name}_output"
        
        # Define paths
        graphrag_dir = Path("backend/graphrag")
        ragtest_dir = graphrag_dir / "ragtest"
        
        # Make sure the ragtest directory exists
        ragtest_dir.mkdir(parents=True, exist_ok=True)
        
        settings_file = ragtest_dir / "settings.yaml"
        
        # Check if the output folder exists
        output_dir = ragtest_dir / output_folder
        if not output_dir.exists():
            return jsonify({
                "status": "error",
                "message": f"Output folder {output_folder} does not exist. Please create the knowledge graph first."
            }), 404
        
        # Default settings if file doesn't exist
        default_settings = {
            "input": {"base_dir": "default_input"},
            "output": {"base_dir": "default_output"}
        }
        
        # Check if settings.yaml exists, create if not
        if not settings_file.exists():
            with open(settings_file, "w") as f:
                yaml.dump(default_settings, f, default_flow_style=False)
            print(f"Created new settings file at {settings_file}")
        
        # Read the current settings from file
        with open(settings_file, "r") as f:
            settings = yaml.safe_load(f)
        
        # Store original settings to restore later
        original_settings = settings.copy()
        
        # Update settings to use topic-specific folders
        settings["input"]["base_dir"] = input_folder
        settings["output"]["base_dir"] = output_folder
        
        # Write the updated settings back to the file
        with open(settings_file, "w") as f:
            yaml.dump(settings, f, default_flow_style=False)
        
        # Prepare the graphrag query command with the formatted query
        command = [
            "graphrag", "query",
            "--root", "./ragtest",
            "--method", "local",
            "--query", formatted_query
        ]
        
        # Execute the command
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(graphrag_dir)  # Change working directory to be relative to graphrag folder
        )
        
        # Get the output and errors
        stdout, stderr = process.communicate()
        
        # Restore original settings
        with open(settings_file, "w") as f:
            yaml.dump(original_settings, f, default_flow_style=False)
        
        # Check if command was successful
        if process.returncode == 0:
            # Try to determine how many sources were actually found
            found_sources = 0
            
            # Improved pattern matching for various citation formats
            data_citations = []
            
            # Match [Data: Reports (X)] format
            report_matches = re.findall(r'\[Data:\s*Reports\s*\((\d+)\)\]', stdout)
            for report_num in report_matches:
                data_citations.append({"type": "report", "id": report_num})
            
            # Match [Data: Sources (Y)] format
            source_matches = re.findall(r'\[Data:\s*Sources\s*\((\d+)\)\]', stdout)
            for source_num in source_matches:
                data_citations.append({"type": "source", "id": source_num})
            
            # Match [Data: Reports (X); Sources (Y)] format
            combined_matches = re.findall(r'\[Data:\s*Reports\s*\((\d+)\);\s*Sources\s*\((\d+)\)\]', stdout)
            for report_num, source_num in combined_matches:
                data_citations.append({"type": "report", "id": report_num})
                data_citations.append({"type": "source", "id": source_num})
            
            # Count unique citations
            found_sources = len(data_citations)
            print(f"Found {found_sources} data citations: {data_citations}")
            
            # Add header to the response
            response_text = "## Three Scenarios: From Most Likely to Least Likely\n\n" + stdout
            
            # Get the full graph data
            full_graph = get_graph(output_dir)
            print(f"Full graph loaded with {len(full_graph.get('nodes', []))} nodes and {len(full_graph.get('links', []))} links")
            
            # Log some sample nodes to understand the structure
            if full_graph.get('nodes', []):
                print("Sample nodes:")
                for i, node in enumerate(full_graph.get('nodes', [])[:5]):  # First 5 nodes
                    print(f"Node {i}: ID={node.get('id')}, Label={node.get('label')}")
                    if node.get('properties'):
                        print(f"  Properties: {list(node.get('properties', {}).keys())}")
            
            # Set a maximum number of highlighted nodes to prevent overwhelming the graph
            MAX_HIGHLIGHTED_NODES = 5

            # More targeted approach to find relevant nodes
            highlighted_node_ids = set()
            relevant_nodes = []

            # Only do direct matching - no fallbacks to keep highlights conservative
            for citation in data_citations:
                citation_id = citation["id"]
                citation_type = citation["type"]
                
                # Find nodes directly matching this citation - with scoring
                matches = []
                
                for node in full_graph.get('nodes', []):
                    node_id = str(node.get('id', ''))
                    node_label = str(node.get('label', '')).lower()
                    node_props = node.get('properties', {})
                    
                    # Convert props to string for searching
                    prop_str = str(node_props).lower()
                    
                    # Score the match (higher is better)
                    score = 0
                    
                    # Exact ID matches are strongest
                    if f"{citation_type}_{citation_id}" == node_id.lower():
                        score = 100
                    elif f"{citation_id}" == node_id:
                        score = 90
                    # Label matches
                    elif f"{citation_type} {citation_id}" == node_label:
                        score = 80
                    elif f"{citation_type}({citation_id})" in node_label:
                        score = 70
                    # Partial matches in properties
                    elif citation_id in prop_str and citation_type in prop_str:
                        score = 50
                    elif citation_id in prop_str:
                        score = 30
                    else:
                        continue  # No match at all
                    
                    matches.append((node, score))
                
                # Sort by score and take the best match for this citation
                if matches:
                    matches.sort(key=lambda x: x[1], reverse=True)
                    best_match = matches[0][0]
                    node_id = str(best_match.get('id', ''))
                    
                    if node_id not in highlighted_node_ids and len(highlighted_node_ids) < MAX_HIGHLIGHTED_NODES:
                        highlighted_node_ids.add(node_id)
                        node_copy = dict(best_match)
                        node_copy['highlighted'] = True
                        node_copy['citation_match'] = f"{citation_type}({citation_id})"
                        relevant_nodes.append(node_copy)
                        print(f"Best match for {citation_type}({citation_id}): {node_id}")

            # Get only direct links between highlighted nodes
            relevant_links = []
            for link in full_graph.get('links', []):
                source = str(link.get('source', ''))
                target = str(link.get('target', ''))
                
                if source in highlighted_node_ids and target in highlighted_node_ids:
                    link_copy = dict(link)
                    link_copy['highlighted'] = True
                    relevant_links.append(link_copy)

            # Create the highlighted graph subset (much smaller now)
            highlighted_graph = {
                'nodes': relevant_nodes,
                'links': relevant_links,
                'citations': data_citations
            }

            print(f"Conservative highlighted graph has {len(relevant_nodes)} nodes and {len(relevant_links)} links")
            
            # Prepare response data
            response_data = {
                "status": "success",
                "message": "Knowledge graph queried successfully",
                "data": {
                    "query": original_query,
                    "formatted_query": formatted_query,
                    "topic": topic,
                    "requested_sources": num_sources,
                    "found_sources": found_sources,
                    "command": " ".join(command),
                    "result": response_text,
                    "highlighted_graph": highlighted_graph  # Add the highlighted graph data
                }
            }
            
            # Add warning if fewer sources than requested were found
            if found_sources < num_sources:
                response_data["data"]["warning"] = f"Only {found_sources} sources could be retrieved. Try adjusting the user query or asking a follow up to retrieve more sources."
            
            return jsonify(response_data)
        else:
            return jsonify({
                "status": "error",
                "message": f"Error querying knowledge graph: {stderr}",
                "command": " ".join(command)
            }), 500
            
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        return jsonify({
            "status": "error",
            "message": f"Error querying knowledge graph: {str(e)}"
        }), 500

@app.route("/api/updating_knowledge_graph", methods=["GET", "POST"])
def updating_knowledge_graph():
    """
    Update the knowledge graph with new data and return the query response over the updated graph
    """
    return jsonify({"status": "success", "message": "Knowledge graph updated successfully"})

@app.route("/api/generate_report", methods=["GET", "POST"])
def generate_report():
    """
    Generate scenarios from user topic input
    """
    return jsonify({"status": "success", "message": "Scenarios generated successfully"})

@app.route("/api/save_report", methods=["GET", "POST"])
def save_report():
    """
    Save the report from user topic input
    """
    return jsonify({"status": "success", "message": "Report saved successfully"})

@app.route("/api/get_report", methods=["GET", "POST"])
def get_report():
    """
    Get the report from user topic input
    """
    return jsonify({"status": "success", "message": "Report retrieved successfully"})

@app.route("/api/explore_graph_data", methods=["POST"])
def explore_graph_data():
    """
    Explore the structure of graph data to help understand how citations map to nodes.
    
    Expected JSON body:
    {
        "topic": "The original topic that was used to create the knowledge graph",
        "citation_type": "report",  // Optional: "report" or "source"
        "citation_id": "0"  // Optional: The specific ID number to look for
    }
    
    Returns:
        JSON with insights about the data structure
    """
    try:
        import pandas as pd
        from pathlib import Path
        
        # Get topic from request body
        data = request.get_json()
        if not data or 'topic' not in data:
            return jsonify({"error": "Missing 'topic' in request body"}), 400
            
        topic = data['topic']
        citation_type = data.get('citation_type')
        citation_id = data.get('citation_id')
        
        # Get folder path using the same logic
        folder_name = "_".join(topic.split()[:4])
        folder_name = "".join(c for c in folder_name if c.isalnum() or c == '_')
        output_folder = f"{folder_name}_output"
        
        graphrag_dir = Path("backend/graphrag")
        output_dir = graphrag_dir / "ragtest" / output_folder
        
        if not output_dir.exists():
            return jsonify({
                "status": "error",
                "message": f"Output folder {output_folder} does not exist."
            }), 404
        
        # Look for parquet files
        parquet_files = list(output_dir.glob("*.parquet"))
        
        if not parquet_files:
            return jsonify({
                "status": "error",
                "message": "No parquet files found in the output directory."
            }), 404
        
        # Get full graph structure
        full_graph = get_graph(output_dir)
        
        # Analyze parquet files
        parquet_insights = []
        
        for pf in parquet_files:
            try:
                df = pd.read_parquet(pf)
                
                # Get column names
                columns = df.columns.tolist()
                
                # Look for specific citation if requested
                matching_rows = []
                if citation_type and citation_id:
                    # Search each column for the citation
                    for col in columns:
                        if df[col].dtype == 'object':  # String-like columns
                            matches = df[df[col].astype(str).str.contains(f"{citation_type}.*{citation_id}", regex=True, na=False)]
                            if not matches.empty:
                                for _, row in matches.iterrows():
                                    matching_rows.append(row.to_dict())
                
                parquet_insights.append({
                    "filename": pf.name,
                    "row_count": len(df),
                    "columns": columns,
                    "sample_row": df.iloc[0].to_dict() if not df.empty else {},
                    "matching_rows": matching_rows[:5]  # Limit to 5 matches
                })
            except Exception as e:
                parquet_insights.append({
                    "filename": pf.name,
                    "error": str(e)
                })
        
        # Basic graph structure analysis
        graph_structure = {
            "node_count": len(full_graph.get('nodes', [])),
            "link_count": len(full_graph.get('links', [])),
            "node_properties": set(),
            "node_types": {},
            "sample_nodes": []
        }
        
        # Analyze nodes
        for i, node in enumerate(full_graph.get('nodes', [])[:10]):  # First 10 nodes
            props = node.get('properties', {})
            for prop in props:
                graph_structure["node_properties"].add(prop)
            
            group = node.get('group')
            if group:
                graph_structure["node_types"][group] = graph_structure["node_types"].get(group, 0) + 1
            
            # Add sample nodes
            graph_structure["sample_nodes"].append({
                "id": node.get('id'),
                "label": node.get('label'),
                "group": group,
                "key_properties": {k: props.get(k) for k in list(props.keys())[:5]}  # First 5 properties
            })
        
        return jsonify({
            "status": "success",
            "message": "Graph data structure analyzed",
            "data": {
                "topic": topic,
                "citation_search": {
                    "type": citation_type,
                    "id": citation_id
                },
                "parquet_files": parquet_insights,
                "graph_structure": graph_structure
            }
        })
        
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        return jsonify({
            "status": "error",
            "message": f"Error exploring graph data: {str(e)}"
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)