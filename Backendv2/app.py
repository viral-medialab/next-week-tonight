from flask import Flask, jsonify, request
from flask_cors import CORS
from query_utils import *
from article_utils import *
from database_utils import clear_cache, save_generated_article_to_DB

import streamlit as st
import pandas as pd
import io
import openai
from env import *

client = openai.OpenAI(
    api_key=OPENAI_API_KEY,
)

app = Flask(__name__)
CORS(app)
'''
This script serves as the API by which the front-end and back-end interact.
The current API functions are:

handle_q2a_workflow()
handle_generate_what_if_questions()
handle_gather_article_info()
'''



@app.route('/api/call_q2a_workflow', methods=['GET', 'POST'])
def handle_q2a_workflow():
    '''
    Generates an article based on a 'what if...' question

    Inputs:

        article_id (str)    :   The id of the article that is currently being viewed
        user_prompt (str)   :   The "what happens if..." question that is selected
        num_articles (str)  :   [OPTIONAL, default = 6] The number of relevant articles 
                                we will use as context for the LLM generating the article
        verbose (bool)      :   [OPTIONAL, default = False] Prints debug statements 
                                into the terminal

    Outputs a new article in the format {'title': title, 'body': body}
    '''
    data = request.get_json()
    article_url = data.get('articleUrl', None)
    article_id = data.get('article_id', None)
    if article_url:
        article_id = get_article_id(article_url)
    user_prompt = data.get('user_prompt')
    num_articles = int(data.get('num_articles', '1'))
    verbose = data.get('verbose', False)
    article = get_article_contents_from_id(article_id)

    print(article, user_prompt, num_articles, verbose)
    results = q2a_workflow_wrapper(article, user_prompt, num_articles, verbose)
    out = {}
    for i, result in enumerate(results[-1]):
        id, parent = save_generated_article_to_DB(title = result[0], body = result[1], parent = article_id, query = user_prompt)
        out[f'article_{i}'] = {"title": result[0], "body": result[1], "id": id, "parent": parent, "sources": {"test title 1": "test url 1", "test title 2": "test url 2"}}
        print(out[f'article_{i}'])
    return jsonify(out)




@app.route('/api/generate_what_if_questions', methods=['GET', 'POST'])
def handle_generate_what_if_questions():
    '''
    Generates the completions for questions of the form 'what happens if...' 
    For example, from an article about the 2024 elections, one response
    could be '... Joe Biden gets re-elected?'

    Inputs:

        articleUrl (str)        :   The url of the article that is currently being viewed
        num_predictions (str)   :   [OPTIONAL, default = 3] The number of 'what if...'
                                    predictions to make.

    Outputs predictions in the format {'prediction_1': prediction, 'prediction_2': prediction, etc.}
    '''
    data = request.get_json()
    article_url = data.get('articleUrl', None)
    article_id = data.get('article_id', None)
    if article_url:
        article_id = get_article_id(article_url)
    amount_of_predictions = int(data.get('amount_of_predictions', '3'))
    article = get_article_contents_from_id(article_id)

    result = generate_what_if_questions(article, amount_of_predictions)
    out = {}
    for i, pred in enumerate(result):
        out[f'prediction_{i}'] = pred
    return jsonify(out)




@app.route('/api/gather_article_info', methods=['GET', 'POST'])
def handle_gather_article_info():
    '''
    Fetches relevant information about an article that is not stored
    in the metadata. This includes author, title, and contents.

    Inputs:

        articleUrl (str)        :   The url of the article that is currently being viewed
        article_id (str)        :   An alternative to URL (only one of URL and ID is needed)s


    Outputs information in the format {'author': author, 'title': title, 'contents': article_contents
    
    UPDATE: Now returns a children field for the children of the current article
    '''
    data = request.get_json()
    print(data)
    article_url = data.get('articleUrl', None)
    article_id = data.get('article_id', None)
    if article_url:
        article_id = get_article_id(article_url)
    client, db, collection = connect_to_mongodb()
    article = collection.find_one({'id': article_id})
    children = article['children'] if 'children' in article else []
    if article.get('is_generated', False):
        title = article['title']
        author = 'AI Generated'
        article_contents = article['body']
    else:
        title, author, article_contents = get_article_contents_for_website(article_id)
    out = {'author': author, 'title': title, 'contents': article_contents, 'children': children}
    return jsonify(out)





@app.route('/api/test', methods=['GET', 'POST'])
def handle_test():
    print("handling test")
    data = request.json #request.get_json()
    print("retrieved data")
    article_id = data.get('article_id')
    print(f"got article id: {article_id}")
    return jsonify({"id": article_id})





@app.route('/api/handle_clear_cache', methods=['GET','POST'])
def handle_clear_cache():
    '''
    Clears all AI generated articles that are children of the currently viewed article

    Inputs:

        article_id (str)        :   The id of the article whose children we are deleting
        

    To add: option for recursively deleting children of children
    '''
    data = request.get_json()
    article_id = data['article_id']
    for statement in clear_cache(article_id):
        print(statement)
    return jsonify({'message': 'Cache cleared successfully'})


'''
DATA VISUALIZATION
'''

@app.route('/api/generate_visualization', methods=['GET','POST'])
def generate_visualization():
    '''
    Returns visualization of data
    Inputs: data: csv file
    '''
    print(request.data)
    data = io.StringIO(request.data.decode('utf-8'))
    df = pd.read_csv(data)
    print(df)

    # Define the messages for the OpenAI model
    messages = [
        {
            "role": "system",
            "content": "You are a helpful Data Visualization assistant who gives a single block without explaining or commenting the code to plot. IF ANYTHING NOT ABOUT THE DATA, JUST politely respond that you don't know.",
        },
        {"role": "user", "content": "generate a visualization for this data"},
    ]

    # Call OpenAI and display the response
    response = client.chat.completions.create(
        messages=messages,
        model="gpt-4-1106-preview",
    )
    execute_openai_code(response, df)

def execute_openai_code(response_text: str, df: pd.DataFrame):
    """
    Execute the code provided by OpenAI in the app.

    Parameters:
    - response_text: The response text from OpenAI
    - df: DataFrame containing the data
    - query: The user's query
    """

    # Extract code from the response text
    code = extract_code_from_markdown(response_text)

    # If there's code in the response, try to execute it
    if code:
        try:
            exec(code)
            st.pyplot()
        except Exception as e:
            error_message = str(e)
            st.error(
                f"📟 Apologies, failed to execute the code due to the error: {error_message}"
            )
    else:
        st.write(response_text)

def extract_code_from_markdown(md_text):
    """
    Extract Python code from markdown text.

    Parameters:
    - md_text: Markdown text containing the code

    Returns:
    - The extracted Python code
    """
    # Extract code between the delimiters
    code_blocks = re.findall(r"```(python)?(.*?)```", md_text, re.DOTALL)

    # Strip leading and trailing whitespace and join the code blocks
    code = "\n".join([block[1].strip() for block in code_blocks])

    return code

    



'''
@app.route('/api/test', methods=['GET', 'POST'])
def handle_test():
    print("handling test")
    data = request.json #request.get_json()
    print("retrieved data")
    article_id = data.get('article_id')
    print(f"got article id: {article_id}")
    return {"id": article_id}

'''


if __name__ == '__main__':
    app.run(debug=True)
