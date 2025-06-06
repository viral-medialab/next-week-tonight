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
from graph_utils import get_graph, extract_citations_from_response, GRAPH_OUTPUT_DIR, enhance_citations_with_details

# (Your existing project imports remain – shortened here)
#from predictions.query_utils import *          
#from api.article_utils import *                
#from database.database_utils import clear_cache, save_generated_article_to_DB  # noqa: F401
import openai
from test.env import OPENAI_API_KEY
from database.extract_data_perplexity import (
    get_perplexity_sources, 
    save_text_to_file,
    extract_text_from_url
)
import pandas as pd
from database.firecrawl_scrape import firecrawl_extract_only
import subprocess
import os
import yaml
from pathlib import Path
        
#import re

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ────────────────────────────────────────────────────────────────────────────────
#  Flask app
# ────────────────────────────────────────────────────────────────────────────────
app = Flask(__name__)

# More explicit CORS configuration
CORS(app, 
     origins=["*"],  
     methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     supports_credentials=True,
     max_age=3600)

# Also add CORS headers manually to all responses for extra assurance
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

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
        
        # Get sources from Perplexity
        sources, perplexity_response = get_perplexity_sources(query)
        
        if not sources and not perplexity_response:
            return jsonify({
                "status": "error",
                "message": "No sources found from Perplexity API"
            }), 404
        elif not sources and perplexity_response:
            print("Warning: Perplexity response received but no sources were extracted. This likely indicates an issue with source parsing.")
            return jsonify({
                "status": "error", 
                "message": "Sources could not be extracted from Perplexity response"
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
        
        # Process each source from Perplexity API response
        if sources: 
            for source in sources:
                extraction_info = {
                    "url": source,
                    "successful": False,
                    "extraction_method": "Unknown"
                }
                
                # Get the extraction result - returns a dictionary with 'text', 'news_title', etc.
                extraction_result = firecrawl_extract_only(source)
                
                if extraction_result:
                    # Extraction succeeded
                    extraction_method = extraction_result.get('extraction_method', 'Unknown method')
                    successful = True
                    
                    # Save the extraction result
                    try:
                        filepath = save_text_to_file(
                            extraction_result, 
                            query, 
                            source, 
                            folder=str(folder)
                        )
                        
                        extraction_info.update({
                            "filepath": filepath,
                            "successful": successful,
                            "extraction_method": extraction_method
                        })
                        
                        successful_extractions += 1
                        
                    except Exception as e:
                        print(f"Error saving source {source}: {str(e)}")
                        extraction_info["error"] = str(e)
                else:
                    # If firecrawl_extract_only failed, try the perplexity fallback
                    print(f"All extraction methods failed for {source}, trying Perplexity extraction as fallback")
                    
                    # Create a DataFrame with just this source for extract_text_from_url
                    source_df = pd.DataFrame({'url': [source]})
                    
                    # Use Perplexity extraction as fallback
                    text = extract_text_from_url(source_df)[0]
                    
                    # Check if Perplexity extraction was successful
                    if isinstance(text, tuple):  # If text is a tuple (score, content) from perplexity_text_extractor
                        score, content = text
                        if score.isnumeric() and int(score) >= 2:
                            text_to_save = content
                            extraction_method = f"Perplexity (score: {score})"
                            successful = True
                        else:
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
                    
                    # Only save here if we didn't already save with firecrawl_extract_only
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
                "successful_extractions": successful_extractions, #TODO: remove filepath from here
                "sources": saved_sources,
                "perplexity_response_saved": bool(response_file),
                "perplexity_response_file": response_file #TODO: remove filepath from here
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
            #print(f"Existing files: {all_existing_files}")
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
            "--root", "./ragtest",
            "--logger", "none"
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
            print(f"No. of Output parquet files: {len(output_files)}")
            output_json_files = list(output_dir.glob("*.json")) if output_dir.exists() else []
            print(f"No of. Output json files: {len(output_json_files)}")
            
            # Combine all found files
            all_output_files = output_files + output_json_files
            print(f"All output files: {len(all_output_files)}")
            
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
        if process.returncode == 0:
            # Extract citations and their data
            citations = extract_citations_from_response(stdout, output_dir)
            
            # Get the full graph data
            full_graph = get_graph(output_dir)
            
            # # Find nodes related to citations
            # highlighted_nodes = []
            # highlighted_links = []
            
            # if full_graph and full_graph.get('nodes'):
            #     # Track nodes we want to highlight
            #     highlight_ids = set()
                
            #     # Look for nodes matching our citations
            #     for citation_type in ['reports', 'sources', 'entities']:
            #         for citation in citations[citation_type]:
            #             citation_id = citation['id']
                        
            #             # Look for matching nodes
            #             for node in full_graph['nodes']:
            #                 node_id = str(node.get('id', ''))
            #                 node_label = str(node.get('label', '')).lower()
                            
            #                 # Check for matches in id or label
            #                 if (f"{citation_type}_{citation_id}" == node_id.lower() or
            #                     f"{citation_type}({citation_id})" in node_label):
                                
            #                     # Copy node and mark as highlighted
            #                     highlighted_node = dict(node)
            #                     highlighted_node['highlighted'] = True
            #                     highlighted_node['citation_match'] = f"{citation_type}({citation_id})"
            #                     highlighted_nodes.append(highlighted_node)
            #                     highlight_ids.add(node_id)
                
            #     # Find links between highlighted nodes
            #     if full_graph.get('links'):
            #         for link in full_graph['links']:
            #             source = str(link.get('source', ''))
            #             target = str(link.get('target', ''))
                        
            #             if source in highlight_ids and target in highlight_ids:
            #                 highlighted_link = dict(link)
            #                 highlighted_link['highlighted'] = True
            #                 highlighted_links.append(highlighted_link)
            
            # # Prepare visualization data
            # visualization_data = {
            #     'full_graph': full_graph,
            #     'highlighted_subgraph': {
            #         'nodes': highlighted_nodes,
            #         'links': highlighted_links
            #     }
            # }

            # print("visualization_data", visualization_data)
            # print("citations", citations)
            
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
                    "full_graph": full_graph,
                    #"visualization": visualization_data
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
        JSON with status, message, and query results with detailed citation information
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
            "--query", f"Give me 3 scenarios from most likely to least likely about what would happen if {query}. Make each scenario different from the others. For each scenario, explain the reasoning and cite relevant reports, entities and relationships from the graph."
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
            print("citations", citations)
            
            # Get the full graph data
            full_graph = get_graph(output_dir)
            
            # Enhance citations with detailed node/relationship information
            enhanced_citations = enhance_citations_with_details(citations, output_dir)
            #("enhanced_citations", enhanced_citations)
            
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
                    "enhanced_citations": enhanced_citations,
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


def save_text_to_file(text, query, url, folder="graphrag/ragtest/input", is_perplexity_response=False):
    """Save extracted text to a file."""
    # Create folder if it doesn't exist
    os.makedirs(folder, exist_ok=True)
    
    # Create a safe filename from the query and URL
    safe_query = "".join(x for x in query if x.isalnum() or x.isspace()).rstrip()
    safe_query = safe_query.replace(" ", "_")[:50]  # Limit length
    
    # Get a unique identifier from the URL or use "response" for the main perplexity response
    if is_perplexity_response:
        filename = f"{safe_query}_perplexity_response.txt"
    else:
        url_id = str(abs(hash(url)) % 10000)
        filename = f"{safe_query}_{url_id}.txt"
    
    filepath = os.path.join(folder, filename)
    
    # Debug what we're about to save
    print(f"\n--- DEBUGGING TEXT SAVING ---")
    print(f"File path: {filepath}")
    print(f"URL: {url}")
    print(f"Text type: {type(text)}")
    
    if isinstance(text, dict):
        print(f"Dictionary keys: {text.keys()}")
        if 'text' in text:
            text_sample = text['text'][:150] + "..." if len(text['text']) > 150 else text['text']
            print(f"Text content length: {len(text['text'])} chars")
            print(f"Text sample: {text_sample}")
    else:
        text_sample = text[:150] + "..." if len(text) > 150 else text
        print(f"Text content length: {len(text)} chars")
        print(f"Text sample: {text_sample}")
    
    # Save text to file
    try:
        with open(filepath, "w", encoding="utf-8") as file:
            # Add title and source information
            if not is_perplexity_response:
                if isinstance(text, dict) and 'news_title' in text and 'text' in text:
                    # Handle case where text is actually a dictionary with content
                    file.write(f"Title: {text['news_title']}\n")
                    file.write(f"Source: {url}\n\n")
                    file.write(text['text'])
                    
                    # Debug what we actually wrote
                    print(f"Wrote dictionary with title and text (news_title + text)")
                else:
        
                    file.write(text)
                    
                    # Debug what we actually wrote
                    print(f"Wrote plain text (text only)")
            else:
                # Just write the perplexity response directly
                file.write(text)
                print(f"Wrote perplexity response")
                
        # Verify file was written correctly
        file_size = os.path.getsize(filepath)
        file_content = None
        with open(filepath, "r", encoding="utf-8") as f:
            file_content = f.read(500)  # Read first 500 chars to check
        
        print(f"File saved: {filepath} ({file_size} bytes)")
        print(f"File content starts with: {file_content[:150]}...")
        
        # If file size is suspiciously small, log a warning
        if file_size < 500 and not is_perplexity_response:
            print(f"WARNING: File {filepath} is very small ({file_size} bytes). Content may be truncated.")
            
    except Exception as e:
        print(f"Error saving to file {filepath}: {str(e)}")
        
    return filepath

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)