import sys
sys.path.append("../DataPipeline")
from dotenv import load_dotenv
import os
load_dotenv("vars.env")
load_dotenv("../../vars.env")
from openai import OpenAI
openai_api = os.environ.get("OPENAI_API")
from retrieval import get_embedding, find_closest_article_using_simple_search, fetch_embeddings_from_mongo
all_doc_embeddings = fetch_embeddings_from_mongo()
import re
import requests
from bs4 import BeautifulSoup
from prompts import *


def fetch_article_contents(article_id):
    '''
    Returns article's author and contents of the article
    '''
    asset_url = "https://assets.msn.com/content/view/v2/Detail/en-us/" + article_id

    try:
        response = requests.get(asset_url)
        response.raise_for_status()
        data = response.json()
        html_content = data.get('body', 'No content found')

    except requests.RequestException as e:
        print(f"Error fetching article: {e}")
        return None
    
    soup = BeautifulSoup(html_content, 'lxml')
    paragraphs = [p.get_text(separator=' ', strip=True) for p in soup.find_all('p')]
    #print(author)
    return '\n\n'.join(paragraphs)



def fetch_and_summarize_articles(relevant_articles):
    content = [fetch_article_contents(article) for article in relevant_articles]
    combined_summaries = summarize_articles(content)
    return combined_summaries



def summarize_articles(text_from_articles):
    context_prompt = summarize_prompt
    query_prompts = text_from_articles
    return updated_query_chatgpt(context_prompt, query_prompts)



def generate_relevant_questions(article_context, user_prompt):
    context_prompt = relevant_question_prompt
    article_context = "Here is an article that you will use to aid your question making: " + article_context
    return updated_query_chatgpt([context_prompt, article_context], [user_prompt])



def generate_article(user_prompt, relevant_info, relevant_articles):
    #Relevant info is a list of strings where each string is an article body

    overall_context = generate_article_prompt

    relevant_context = "Here is some relevant information to write your articles. Use the information here to extract facts for your articles (each piece of information is separated by a semicolon): "
    for info in relevant_articles:
        relevant_context += info + ";"
    relevant_context = relevant_context[:-1]

    preds_context = "Here are some pre-generated predictions. As a creative writing exercise, riff off of these possibilities, imagining one or more as what concretely happens:\n"
    for pred in relevant_info:
        preds_context += pred

    user_query = 'Please write an article using the context to answer the following question: ' + user_prompt

    return updated_query_chatgpt([overall_context, preds_context, relevant_context], user_query)



def generate_predictions(relevant_articles, user_query = None):
    #Relevant info is a list of strings where each string is an article body
    overall_context = prediction_prompt
    relevant_context = "Here is some relevant information to formulate your predictions: ".replace("\n", "")
    for article in relevant_articles:
        relevant_context += article + ";"
    relevant_context = relevant_context[:-1]

    if user_query:
        query = 'Generate detailed predictions from the following query based on what you think might happen: ' + user_query
    else:
        query = 'Generate detailed predictions based on the context provided. Make sure the predictions span a lot of possibilities.'

    return updated_query_chatgpt([overall_context, relevant_context], query)



def updated_query_chatgpt(contexts, queries):
    # Query ChatGPT and return the response (this function needs to be defined)
    # Set your OpenAI API key
    openai_api = os.environ.get("OPENAI_API")

    client = OpenAI(
        #  This is the default and can be omitted
        api_key=openai_api,
    )

    if len(queries) > 1:
        contexts += ["Note: The input will be split by semicolons. Answer each prompt separately and return your answer also split by semicolons. For example, if I asked you to solve arithmetic problems and my input was '2+2;4+5', your answer should be '4;9'."]
    messages = []
    for context in contexts:
        messages.append({"role": "system", "content": context})
    final_query = ""
    for query in queries:
        final_query += query + ";"
    messages.append({"role": "user", "content": final_query[:-1]})
    response = client.chat.completions.create(
        messages=messages,
        model="gpt-4-1106-preview",
    )

    return response.choices[0].message.content.split(";")




def fetch_article_id(article_url):        
    pattern = re.compile(r'/ar-([A-Za-z0-9]+)')

    match = pattern.search(article_url)
    if match:
        article_id = match.group(1)
        return article_id
    else:
        raise Exception("No article ID found")




def q2a_workflow(article, user_prompt, num_articles, verbose = True):
    '''
    Takes an article and corresponding user query, and works it into an article that answers the user's prompt.

    The workflow is as follows:

        1)  Input:  User prompt, article
            Output: Questions that help answer user prompt

        2)  Input:  User prompt, Questions that help answer user prompt
            Output: Embeddings of these questions and user input

        3)  Input:  Embedding of user prompt and AI-generated questions
            Output: Set of articles that provide good context

        4)  Input:  User input, set of articles that provide good context
            Output: AI-generated predictions
            
        5)  Input:  User input, AI-generated predictions
            Output: AI-generated article 
    '''
    print("1")
    AI_generated_questions = generate_relevant_questions(article, user_prompt)
    print("2")
    embeddings = [get_embedding(user_prompt)] + [get_embedding(question) for question in AI_generated_questions]
    print("3")
    relevant_article_urls = [find_closest_article_using_simple_search(embedding, all_doc_embeddings) for embedding in embeddings]
    print("4")
    relevant_articles = [fetch_article_contents(fetch_article_id(url)) for url in set(relevant_article_urls[:2*num_articles])]
    print("5")
    preds = generate_predictions(relevant_articles, user_query=user_prompt)
    print(preds)
    print("6")
    out = generate_article(user_prompt, [], relevant_articles)
    if verbose:
        print("AI generated questions: ", AI_generated_questions)
        print("Relevant articles: ", relevant_articles)
        print("\n\n\n\n\n\n")
        print("Created article:", out)
        print("\n\n\n\n\n\n")
        print("Created predictions:", preds)
    return AI_generated_questions, relevant_articles, preds, out




'''
def q2p_workflow(article, num_articles, verbose = True):
    #
    Takes an article and corresponding user query, and works it into an article that answers the user's prompt.

    The workflow is as follows:

        1)  Input:  User prompt, article
            Output: Questions that help answer user prompt

        2)  Input:  User prompt, Questions that help answer user prompt
            Output: Embeddings of these questions and user input

        3)  Input:  Embedding of user prompt and AI-generated questions
            Output: Set of articles that provide good context

        4)  Input:  User input, set of articles that provide good context
            Output: AI-generated predictions
            
        5)  Input:  User input, AI-generated predictions
            Output: AI-generated article 
    #

    AI_generated_questions = generate_relevant_questions(article, "What is the context of this article and how does it tie into current events?")[:num_articles]
    embeddings = [get_embedding(question) for question in AI_generated_questions]
    relevant_article_urls = [find_closest_article_using_simple_search(embedding, all_doc_embeddings) for embedding in embeddings]
    relevant_articles = [fetch_article_contents(fetch_article_id(url)) for url in set(relevant_article_urls[:num_articles])]
    preds = generate_predictions(relevant_articles)
    if verbose:
        print("AI generated questions: ", AI_generated_questions)
        print("Relevant articles: ", relevant_articles)
        print("\n\n\n\n\n\n")
        print("Created predictions:", preds)
    return AI_generated_questions, relevant_articles, preds
'''




def save_to_file(data, filename="out_article.txt"):
    with open(filename, 'w') as file:
        for entry in data:
            if isinstance(entry, list):
                for item in entry:
                    file.write(f"{item}\n")
            else:
                file.write(entry + "\n")
            file.write("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")




if __name__ == '__main__':
    query = "What if the Houthis in Yemen retaliate against the American for their strikes?"
    article = sample_article
    AI_generated_questions, relevant_articles, preds, out = q2a_workflow(article, query, 3)
    save_to_file([query, article, AI_generated_questions, relevant_articles, preds, out], 'out_preds.txt')
                                                                  

    
