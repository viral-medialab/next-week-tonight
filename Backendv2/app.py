import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Backendv2')))


from flask import Flask, jsonify, request
from flask_cors import CORS
from query_utils import *
from article_utils import *
from database_utils import clear_cache, save_generated_article_to_DB

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
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


@app.route('/')
def home():
    return 'Next Week Tonight Backend'


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

    Outputs a new article in the format {'title': title, 'body': body, etc.} 
    '''
    data = request.get_json()
    article_url = data.get('articleUrl', None)
    article_id = data.get('article_id', None)
    polarity = data.get('polarity', 2)
    probability = data.get('probability', 0)
    if article_url:
        article_id = get_article_id(article_url)
    client, db, collection = connect_to_mongodb(collection_to_open = 'trendingTopics') # here, we will try to see if the article was hashed
    user_prompt = data.get('user_prompt')
    verbose = data.get('verbose', True)
    article = get_article_contents_from_id(article_id)
    print(article, user_prompt, verbose)
    out = {}

    #############################################################################
    # This is where the code is modified to fit the output to what              #
    # is currently expected in the frontend. I remake the dictionary such that  #
    # the entries are not (probability, polarity) but rather article_i so that  #
    # it is recognized by the frontend.                                         #
    #############################################################################
    for topic in collection.find(): 
        article = topic['articles'][0]
        if article['id'] == article_id:
            if user_prompt in article['questions']:
                before_out = article['questions'][user_prompt]
                after_out = {}
                for generated_article in before_out: # this loop converts 'prob;pol' to (prob, pol). we want to keep this
                    content = article['questions'][user_prompt][generated_article]
                    prob, pol = (int(val) for val in generated_article.split(";"))
                    after_out[(prob, pol)] = content
                    print(after_out)
                for i, generated_article in enumerate(before_out): # this loop converts (prob, pol) to article_i. we want to delete this
                    out[f'article_{i}'] = article['questions'][user_prompt][generated_article] 
                    out[f'article_{i}']['probability'] = prob
                    out[f'article_{i}']['polarity'] = pol
                break


    if out == {}:
        results = q2a_workflow(article, article_id, user_prompt, polarity, probability, verbose)
        result = results[-1]
        id, parent = save_generated_article_to_DB(title = result[0], body = result[1], parent = article_id, query = user_prompt)
        out[f'article_0'] = {"title": result[0], "body": result[1], "id": id, "parent": parent}
        print(out[f'article_0'])
    print(out)
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

    out = {}
    client, db, collection = connect_to_mongodb(collection_to_open = 'trendingTopics') # here, we will try to see if the article was hashed
    for topic in collection.find():
        article = topic['articles'][0]
        if article['id'] == article_id:
            for i, question in enumerate(article['questions']):
                out[f'prediction_{i}'] = question.replace("What happens if", "...")

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
    df = pd.read_csv(data, sep=';', skipinitialspace=True)
    print(df)

    column_names = ", ".join(df.columns)
    query = "draw a bar graph"

    prompt_content = f"""
            The dataset is ALREADY loaded into a DataFrame named 'df'. DO NOT load the data again.
            
            The DataFrame has the following columns: {column_names}
            
            Before plotting, ensure the data is ready:
            1. Check if columns that are supposed to be numeric are recognized as such. If not, attempt to convert them.
            2. Handle NaN values by filling with mean or median.
            
            Use package Pandas and Matplotlib ONLY.
            Provide SINGLE CODE BLOCK with a solution using Pandas and Matplotlib plots in a single figure to address the following query:
            
            {query}

            - USE SINGLE CODE BLOCK with a solution. 
            - Do NOT EXPLAIN the code 
            - DO NOT COMMENT the code. 
            - ALWAYS WRAP UP THE CODE IN A SINGLE CODE BLOCK.
            - The code block must start and end with ```
            
            - Example code format ```code```
        
            - Colors to use for background and axes of the figure : #F0F0F6
            - Try to use the following color palette for coloring the plots : #8f63ee #ced5ce #a27bf6 #3d3b41
            
            """

    # Define the messages for the OpenAI model
    messages = [
        {
            "role": "system",
            "content": "You are a helpful Data Visualization assistant who gives a single block without explaining or commenting the code to plot. IF ANYTHING NOT ABOUT THE DATA, JUST politely respond that you don't know.",
        },
        {"role": "user", "content": prompt_content},
    ]

    response = []
    result = ""
    for chunk in client.chat.completions.create(
            model="gpt-4-1106-preview", messages=messages, stream=True
    ):
        text = chunk.choices[0].delta.content
        if text:
            response.append(text)
            result = "".join(response).strip()
    print(result)
    return execute_openai_code(result, df)

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

    if code:
        try:
            exec(code)
            # Save the plot to a bytes buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            # Encode the image data as base64
            encoded_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
            # Return the base64 encoded image data
            return encoded_image

        except Exception as e:
            error_message = str(e)
            return f"📟 Apologies, failed to execute the code due to the error: {error_message}"
    else:
        return response_text

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
