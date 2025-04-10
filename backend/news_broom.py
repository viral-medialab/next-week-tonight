"""
news_broom.py
Flask API - imports helpers from graph_utils.py
"""
from pathlib import Path
import traceback, sys

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
@app.route("/api/graph", methods=["GET"])
def api_graph():
    """
    Return the current knowledge graph.

    Query params
    -----------
    path  : str (optional)  - custom graph output directory
    fresh : bool (optional) - 'true' to bypass cache
    """
    out_path = request.args.get("path")
    fresh = request.args.get("fresh", "false").lower() == "true"
    out_dir = Path(out_path) if out_path else GRAPH_OUTPUT_DIR

    try:
        data = get_graph(out_dir, force_reload=fresh)
        return jsonify(data)
    except Exception as exc:  # pragma: no cover
        traceback.print_exc(file=sys.stderr)
        return jsonify({"error": str(exc)}), 500

@app.route("/api/gather_news_sources", methods=["POST"])
def gather_news_sources():
    """
    Gather news sources from user topic input
    """
    return jsonify({"status": "success", "message": "News sources gathered successfully"})
    # try:
    #     data = request.json
    #     topic = data.get("topic")
    #     if not topic:
    #         return jsonify({"error": "Topic is required"}), 400
        
@app.route("/api/create_knowledge_graph", methods=["POST"])
def create_knowledge_graph():
    """
    Create a knowledge graph from user topic input
    """
    return jsonify({"status": "success", "message": "Knowledge graph created successfully"})

@app.route("/api/generate_scenarios", methods=["GET", "POST"])
def generate_scenarios():
    """
    Generate scenarios from user topic input
    """
    return jsonify({"status": "success", "message": "Scenarios generated successfully"})

@app.route("/api/query_knowledge_graph", methods=["GET", "POST"])
def query_knowledge_graph():
    """
    Query the knowledge graph from user topic input
    """
    return jsonify({"status": "success", "message": "Knowledge graph queried successfully"})

# ------------------------------------------------------------------------------

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == "__main__":  # pragma: no cover
    app.run(debug=True)
