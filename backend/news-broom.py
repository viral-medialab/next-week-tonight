import sys
import os
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))


from flask import Flask, jsonify, request
from flask_cors import CORS
from predictions.query_utils import *
from api.article_utils import *
from database.database_utils import clear_cache, save_generated_article_to_DB

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import openai
from test.env import *

client = openai.OpenAI(
    api_key=OPENAI_API_KEY,
)

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)


'''
This script serves as the API by which the front-end and back-end interact.
The current API functions are:

handle_q2a_workflow()
handle_generate_what_if_questions()
handle_gather_article_info()
'''


@app.route('/')
def home():
    return 'News Broom backend is running successfully'

@app.route('/api/construct_knowledge_graph', methods=['GET', 'POST'])
def construct_knowledge_graph():
    return jsonify({'message': 'Knowledge graph construction started'})

@app.route('/api/construct_initial_graph', methods=['GET', 'POST'])
def handle_construct_initial_graph():
    '''
    Constructs the initial graph based on the user provided topic and data
    
    Inputs:
        topic (str) : The topic specified by the user
        Optional: date_range (str) : The date range specified by the user
        Optional: file (.csv) : The file containing the data
    Outputs:
        Containing summaries of the scenarios
    '''
    data = request.get_json()
    topic = data.get('topic', '')
    date_range = data.get('date_range', '')
    file = data.get('file', '')
    
    # Step 1: Get the news articles based on the topic and date range
    
    
    return jsonify()

if __name__ == '__main__':
    app.run(debug=True)
