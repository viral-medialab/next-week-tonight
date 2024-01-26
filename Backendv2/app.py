from flask import Flask, jsonify, request
from query_utils import q2a_workflow, generate_what_if_questions  # Import the functions
from article_utils import get_article_contents_from_id

app = Flask(__name__)
'''
This script serves as the API by which the front-end and back-end interact.
The current ports are:

call_q2a_workflow()
handle_generate_what_if_questions()

'''




@app.route('/api/q2a_workflow', methods=['GET', 'POST'])
def call_q2a_workflow():
    '''
    Generates an article based on a 'what if...' question

    Inputs:

        article_id (str)    :   The id of the article that is currently being viewed
        user_prompt (str)   :   The "what happens if..." question that is selected
        num_articles (int)  :   [OPTIONAL, default = 6] The number of relevant articles 
                                we will use as context for the LLM generating the article
        verbose (bool)      :   [OPTIONAL, default = False] Prints debug statements 
                                into the terminal

    Outputs a new article in the format {'title': title, 'body': body}
    '''
    data = request.get_json()  
    article_id = data.get('article_id')  
    user_prompt = data.get('user_prompt')
    num_articles = data.get('num_articles', 6)
    verbose = data.get('verbose', False)
    article = get_article_contents_from_id(article_id)

    result = q2a_workflow(article, user_prompt, num_articles, verbose)
    return jsonify({"title": result[-1][0], "body": result[-1][1]})




@app.route('/api/generate_what_if_questions', methods=['GET', 'POST'])
def handle_generate_what_if_questions():
    '''
    Generates the completions for questions of the form 'what happens if...' 
    For example, from an article about the 2024 elections, one response
    could be '... Joe Biden gets re-elected?'

    Inputs:

        article_id (str)        :   The id of the article that is currently being viewed
        num_predictions (int)   :   [OPTIONAL, default = 3] The number of 'what if...'
                                    predictions to make.

    Outputs predictions in the format {'prediction_1': prediction, 'prediction_2': prediction, etc.}
    '''
    data = request.get_json()  
    article_id = data.get('article_id')  
    amount_of_predictions = data.get('amount_of_predictions', 3)
    article = get_article_contents_from_id(article_id)

    result = generate_what_if_questions(article, amount_of_predictions)
    out = {}
    for i, pred in enumerate(result):
        out[f'prediction_{i}'] = pred
    return jsonify(out)




if __name__ == '__main__':
    app.run(debug=True)
