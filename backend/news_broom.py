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
# Configure CORS to allow requests from anywhere
CORS(app, resources={r"/*": {
    "origins": "*",  # Allow all origins
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]
}})


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
        
        # Check if parquet files already exist in the output directory
        existing_parquet_files = list(output_dir.glob("*.parquet"))
        existing_json_files = list(output_dir.glob("*.json"))
        all_existing_files = existing_parquet_files + existing_json_files
        
        # If parquet or json files already exist, we can skip running graphrag index
        if all_existing_files:
            print(f"Found existing graph files in {output_folder}, skipping indexing step")
            print(f"Existing files: {all_existing_files}")
            data = get_graph(output_dir)
            return jsonify(data)
            
        # If no existing files, continue with the indexing process
        print(f"No existing graph files found in {output_folder}, proceeding with indexing")
        
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
    Query the knowledge graph using GraphRAG local query method.
    """
    try:
        # Import required modules
        import subprocess
        import os
        import yaml
        from pathlib import Path
        
        # Get query from request body
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "Missing 'query' in request body"}), 400
        if not data or 'topic' not in data:
            return jsonify({"error": "Missing 'topic' in request body"}), 400
            
        original_query = data['query']
        topic = data['topic']
        
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
        if process.returncode == 1:
            # Extract citations and their data
            citations = extract_citations_from_response(stdout, output_dir)
            
            # Get the full graph data
            full_graph = get_graph(output_dir)
            
            # Find nodes related to citations
            highlighted_nodes = []
            highlighted_links = []
            
            if full_graph and full_graph.get('nodes'):
                # Track nodes we want to highlight
                highlight_ids = set()
                
                # Look for nodes matching our citations
                for citation_type in ['reports', 'sources', 'entities']:
                    for citation in citations[citation_type]:
                        citation_id = citation['id']
                        
                        # Look for matching nodes
                        for node in full_graph['nodes']:
                            node_id = str(node.get('id', ''))
                            node_label = str(node.get('label', '')).lower()
                            
                            # Check for matches in id or label
                            if (f"{citation_type}_{citation_id}" == node_id.lower() or
                                f"{citation_type}({citation_id})" in node_label):
                                
                                # Copy node and mark as highlighted
                                highlighted_node = dict(node)
                                highlighted_node['highlighted'] = True
                                highlighted_node['citation_match'] = f"{citation_type}({citation_id})"
                                highlighted_nodes.append(highlighted_node)
                                highlight_ids.add(node_id)
                
                # Find links between highlighted nodes
                if full_graph.get('links'):
                    for link in full_graph['links']:
                        source = str(link.get('source', ''))
                        target = str(link.get('target', ''))
                        
                        if source in highlight_ids and target in highlight_ids:
                            highlighted_link = dict(link)
                            highlighted_link['highlighted'] = True
                            highlighted_links.append(highlighted_link)
            
            # Prepare visualization data
            visualization_data = {
                'full_graph': full_graph,
                'highlighted_subgraph': {
                    'nodes': highlighted_nodes,
                    'links': highlighted_links
                }
            }

            print("visualization_data", visualization_data)
            print("citations", citations)
            
            # Prepare response data
            response_data = {
                "status": "success",
                "message": "Knowledge graph queried successfully",
                "data": {
                    "query": original_query,
                    "formatted_query": formatted_query,
                    "topic": topic,
                    "result": stdout,
                    "citations": citations,
                    "visualization": visualization_data
                }
            }
            
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

@app.route("/api/query_global_knowledge_graph", methods=["GET", "POST"])
def query_global_knowledge_graph():
    """
    Query the knowledge graph using GraphRAG global query method.
    
    Expected JSON body:
    {
        "query": "The question to ask about the knowledge graph",
        "topic": "The original topic that was used to create the knowledge graph"
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
        
        # Get query from request body
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "Missing 'query' in request body"}), 400
        if not data or 'topic' not in data:
            return jsonify({"error": "Missing 'topic' in request body"}), 400
            
        query = data['query']
        topic = data['topic']
        
        # Use the same folder name creation logic
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
        output_dir = ragtest_dir / output_folder
        
        # Check if the output folder exists
        if not output_dir.exists():
            return jsonify({
                "status": "error",
                "message": f"Output folder {output_folder} does not exist. Please create the knowledge graph first."
            }), 404
            
        # Handle settings file
        default_settings = {
            "input": {"base_dir": "default_input"},
            "output": {"base_dir": "default_output"}
        }
        
        if not settings_file.exists():
            with open(settings_file, "w") as f:
                yaml.dump(default_settings, f, default_flow_style=False)
        
        # Read current settings
        with open(settings_file, "r") as f:
            settings = yaml.safe_load(f)
        
        # Store original settings
        original_settings = settings.copy()
        
        # Update settings for this query
        settings["input"]["base_dir"] = input_folder
        settings["output"]["base_dir"] = output_folder
        
        with open(settings_file, "w") as f:
            yaml.dump(settings, f, default_flow_style=False)
        
        # Prepare the graphrag query command using global method
        command = [
            "graphrag", "query",
            "--root", "./ragtest",
            "--method", "global",  # Using global search method
            "--query", query
        ]
        
        # Execute the command
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(graphrag_dir)
        )
        
        # Get the output and errors
        stdout, stderr = process.communicate()
        
        # Restore original settings
        with open(settings_file, "w") as f:
            yaml.dump(original_settings, f, default_flow_style=False)
        
        # Check if command was successful
        if process.returncode == 0:
            # Extract citations and their data
            citations = extract_citations_from_response(stdout, output_dir)
            
            # Get the full graph data
            full_graph = get_graph(output_dir)
            
            # Prepare response data
            response_data = {
                "status": "success",
                "message": "Knowledge graph queried successfully using global search",
                "data": {
                    "query": query,
                    "topic": topic,
                    "command": " ".join(command),
                    "result": stdout,
                    "citations": citations,
                    "graph": full_graph
                }
            }
            
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
    
    # Initialize citation containers
    citations = {
        'reports': [],
        'sources': [],
        'entities': [],
        'raw_matches': []
    }
    
    try:
        # Load parquet files if they exist
        data_files = {
            'reports': pd.read_parquet(output_dir / "community_reports.parquet") if (output_dir / "community_reports.parquet").exists() else None,
            'sources': pd.read_parquet(output_dir / "sources.parquet") if (output_dir / "sources.parquet").exists() else None,
            'entities': pd.read_parquet(output_dir / "entities.parquet") if (output_dir / "entities.parquet").exists() else None
        }
        
        # Extract citations using regex patterns
        patterns = {
            'reports': r'\[Data:\s*Reports\s*\((\d+)\)\]',
            'sources': r'\[Data:\s*Sources\s*\((\d+)\)\]',
            'entities': r'\[Data:\s*Entities\s*\((\d+)\)\]'
        }
        
        # Find all citations in the text
        for citation_type, pattern in patterns.items():
            matches = re.findall(pattern, stdout)
            df = data_files[citation_type]
            
            for item_id in matches:
                citation_info = {
                    'type': citation_type,
                    'id': item_id,
                }
                
                # Add to raw matches for reference
                citations['raw_matches'].append(f"{citation_type}({item_id})")
                
                # Look up the data if dataframe is available
                if df is not None:
                    try:
                        item_data = df[df['id'] == int(item_id)].to_dict('records')
                        if item_data:
                            citation_info['data'] = item_data[0]
                        else:
                            citation_info['error'] = f"No {citation_type} found with ID {item_id}"
                    except Exception as e:
                        citation_info['error'] = f"Error looking up {citation_type} {item_id}: {str(e)}"
                else:
                    citation_info['error'] = f"No {citation_type} data file available"
                
                citations[citation_type].append(citation_info)
        
        return citations
        
    except Exception as e:
        print(f"Error extracting citations: {str(e)}")
        return citations

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)