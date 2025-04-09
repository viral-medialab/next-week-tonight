"""
news_broom.py
Flask API – imports helpers from graph_utils.py
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
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)


@app.route("/")
def home():
    return "News Broom backend is running successfully"


# ╭──────────────────────────────────────────────────────────────────────────────╮
# │ Knowledge‑graph endpoint                                                    │
# ╰──────────────────────────────────────────────────────────────────────────────╯
@app.route("/api/graph", methods=["GET"])
def api_graph():
    """
    Return the current knowledge graph.

    Query params
    -----------
    path  : str (optional)  – custom graph output directory
    fresh : bool (optional) – 'true' to bypass cache
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


# (Other API routes unchanged – truncated for brevity)
# ------------------------------------------------------------------------------

if __name__ == "__main__":  # pragma: no cover
    app.run(debug=True)
