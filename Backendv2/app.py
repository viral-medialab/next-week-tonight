from flask import Flask, jsonify, request
from flask_cors import CORS
from query_utils import q2a_workflow, generate_what_if_questions  # Import the functions
from article_utils import get_article_contents_from_id, get_article_id

app = Flask(__name__)
CORS(app)
'''
This script serves as the API by which the front-end and back-end interact.
The current ports are:

call_q2a_workflow()
handle_generate_what_if_questions()

'''



@app.route('/api/call_q2a_workflow', methods=['GET', 'POST'])
def call_q2a_workflow():
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
    article_id = data.get('article_id')
    user_prompt = data.get('user_prompt')
    num_articles = int(data.get('num_articles', '6'))
    verbose = data.get('verbose', False)
    article = get_article_contents_from_id(article_id)

    print(article, user_prompt, num_articles, verbose)
    result = q2a_workflow(article, user_prompt, num_articles, verbose)
    print({"title": result[-1][0], "body": result[-1][1]})
    return jsonify({"title": result[-1][0], "body": result[-1][1]})




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
    article_url = data.get('articleUrl')  
    article_id = get_article_id(article_url)
    amount_of_predictions = int(data.get('amount_of_predictions', '3'))
    article = get_article_contents_from_id(article_id)

    result = generate_what_if_questions(article, amount_of_predictions)
    out = {}
    for i, pred in enumerate(result):
        out[f'prediction_{i}'] = pred
    return jsonify(out)




@app.route('/api/gather_article_info')
def handle_gather_article_info():
    '''
    Fetches relevant information about an article that is not stored
    in the metadata. This includes author, title, and contents.

    Inputs:

        articleUrl (str)        :   The url of the article that is currently being viewed

    Outputs information in the format {'author': author, 'title': title, 'contents': article_contents}
    '''
    data = request.get_json()  
    article_url = data.get('articleUrl')  
    article_id = get_article_id(article_url)
    title, author, article_contents = get_article_contents_from_id(article_id, return_author=True, return_title=True)
    out = {'author': author, 'title': title, 'contents': article_contents}
    return jsonify(out)




@app.route('/api/test', methods=['GET', 'POST'])
def handle_test():
    print("handling test")
    data = request.json #request.get_json()
    print("retrieved data")
    article_id = data.get('article_id')
    print(f"got article id: {article_id}")
    return {"id": article_id}




if __name__ == '__main__':
    app.run(debug=True)
