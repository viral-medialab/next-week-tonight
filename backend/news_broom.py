"""
news_broom.py
Flask API - imports helpers from graph_utils.py
"""
from pathlib import Path
import traceback, sys
import json

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
CORS(app)


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
        settings_file = graphrag_dir / "ragtest" / "settings.yaml"
        
        # Check if the input folder exists
        input_dir = graphrag_dir / "ragtest" / input_folder
        output_dir = graphrag_dir / "ragtest" / output_folder
        if not input_dir.exists():
            return jsonify({
                "status": "error",
                "message": f"Input folder {input_folder} does not exist. Please gather news sources first."
            }), 404
        
        # Create backup of original settings file
        backup_file = settings_file.with_suffix(".yaml.bak")
        shutil.copy2(settings_file, backup_file)
        
        # Read the current settings.yaml
        with open(settings_file, "r") as f:
            settings = yaml.safe_load(f)
        
        # Update only the input path to use topic-specific folder
        # Keep output in the default location
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
        
        # Restore original settings file
        shutil.copy2(backup_file, settings_file)
        os.remove(backup_file)
        
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
        "num_sources": 5  // Optional: Number of sources to return (default: 3)
    }
    
    Returns:
        JSON with status, message, and query results
    """
    try:
        # Get query from request body
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "Missing 'query' in request body"}), 400
            
        query = data['query']
        num_sources = data.get('num_sources', 3)  # Default to 3 sources if not specified
        
        # Import subprocess to run shell commands
        import subprocess
        import os
        from pathlib import Path
        import re
        
        # Define the root directory for graphrag
        root_dir = Path("backend/graphrag/ragtest")
        
        # Ensure the root directory exists
        if not root_dir.exists():
            return jsonify({
                "status": "error",
                "message": f"Root directory {root_dir} does not exist"
            }), 404
        
        # Prepare the graphrag query command
        command = [
            "graphrag", "query",
            "--root", "./ragtest",
            "--method", "global",
            "--top-k", str(num_sources),  # Add parameter for number of sources
            "--query", query
        ]
        
        # Execute the command
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(Path("backend/graphrag"))  # Change working directory to be relative to graphrag folder
        )
        
        # Get the output and errors
        stdout, stderr = process.communicate()
        
        # Check if command was successful
        if process.returncode == 0:
            # Try to determine how many sources were actually found
            # This is a simple heuristic and may need adjustment based on actual output format
            found_sources = 0
            
            # Count sources by looking for "Source:" or similar patterns in the output
            source_matches = re.findall(r'Source\s*\d*:', stdout, re.IGNORECASE) or \
                             re.findall(r'Reference\s*\d*:', stdout, re.IGNORECASE)
            
            if source_matches:
                found_sources = len(source_matches)
            
            # Prepare response data
            response_data = {
                "status": "success",
                "message": "Knowledge graph queried successfully",
                "data": {
                    "query": query,
                    "requested_sources": num_sources,
                    "found_sources": found_sources,
                    "command": " ".join(command),
                    "result": stdout,
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


# ------------------------------------------------------------------------------

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == "__main__":  # pragma: no cover
    app.run(debug=True)
