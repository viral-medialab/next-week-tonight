import numpy as np
import time
from prompts import *
from openai_utils import *
from database_utils import *
from article_utils import *

print("loading doc embeddings")
all_doc_embeddings = get_embeddings_from_mongo()
print("done loading embeddings")



def generate_relevant_questions(article_context, user_prompt):
    context_prompt = relevant_question_prompt
    article_context = "Here is an article that you will use to aid your question making: " + article_context
    return query_chatgpt([context_prompt, article_context], [user_prompt], model="gpt-3.5-turbo-0125")



def summarize_articles(text_from_articles):
    context_prompt = summarize_prompt
    query_prompts = text_from_articles
    return query_chatgpt([context_prompt], [query_prompts])




def generate_what_if_questions(text_from_articles, num_preds = 3):
    instruction_context_prompt = what_if_prompt
    query_prompt = f'Generate exactly {num_preds} what-if questions, separated by semi-colons, based on the following article:\n\n' + text_from_articles
    return query_chatgpt([instruction_context_prompt], [query_prompt])




def generate_article(user_prompt, scenario, relevant_articles, max_context_length = 10000):
    overall_context = generate_article_prompt

    relevant_context = "Here is some relevant information to write your articles. Use the information here to extract facts for your articles (each piece of information is separated by a semicolon): "
    for info in relevant_articles:
        relevant_context += info + "- NEXT ARTICLE -"
    relevant_context = relevant_context[:-16]

    user_query = 'Please write an article title followed by a roughly 500 word article, where the article title is separated from the article contents by a semi-colon (do not write "Title:" for the title or something similar). Answer the following question: ' + user_prompt + ', assuming that ' + scenario

    return query_chatgpt([overall_context, relevant_context], user_query[:max_context_length])





def generate_scenarios(relevant_articles, user_query = None, max_context_length = 10000):
    #Relevant info is a list of strings where each string is an article body
    overall_context = scenario_generation_prompt
    relevant_context = "Here is some relevant information to formulate your scenarios: ".replace("\n", "")
    for article in relevant_articles:
        relevant_context += article + "- NEXT ARTICLE -"
    relevant_context = relevant_context[:-1]

    if user_query:
        query = "Generate five scenarios, separated by semicolons. Do not list the scenarios one-by-one: " + user_query
    else:
        query = 'For now, there is no question. Generate the scenarios using only the relevant articles.'

    scenarios = query_chatgpt([overall_context, relevant_context], query[:max_context_length])
    if type(scenarios) == type("string"):
        raise Exception("Scenario Generation Failed")

    out = []
    for scenario in scenarios:
        scenario_title= query_chatgpt([], ["Make a title for this scenario: " + scenario], model="gpt-3.5-turbo-0125")
        out.append([scenario_title, scenario])

    return out




def q2a_workflow(article, user_prompt, num_articles = 1, verbose = True):
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
            Output: AI-generated scenarios
            
        5)  Input:  User input, AI-generated scenarios
            Output: AI-generated article 
    '''

    time1 = time.time()
    yield "Generating Questions"
    AI_generated_questions = generate_relevant_questions(article, user_prompt)
    time2 = time.time()
    yield f"Generating questions took {time2-time1} seconds"


    time1 = time.time()
    yield "Generating text embeddings for questions"
    embeddings = [get_embedding(user_prompt)] + [get_embedding(question) for question in AI_generated_questions[:3]]
    time2 = time.time()
    yield f"Fetching embeddings took {time2-time1} seconds"
    

    time1 = time.time()
    yield "Finding relevant articles based on questions"
    relevant_article_urls = [find_closest_article_using_simple_search(embedding, all_doc_embeddings) for embedding in embeddings]
    time2 = time.time()
    yield f"Finding relevant articles took {time2-time1} seconds"
    

    time1 = time.time()
    yield "Loading relevant article contents"
    relevant_articles = [get_article_contents_from_id(get_article_id(url)) for url in set(relevant_article_urls[:2])]
    time2 = time.time()
    yield f"Loading relevant article contents took {time2-time1} seconds"
    

    time1 = time.time()
    yield "Generating possible scenarios"
    scenarios = generate_scenarios(relevant_articles, user_query=user_prompt, max_context_length = 10000)
    time2 = time.time()
    yield f"Generating scenarios based on articles and query took {time2-time1} seconds"

    '''
    

    #########################################################################################################################################################
    # this can become asynchronous, will decrease speed BUT will increase API cost (have to refeed context every time =  a lot ofextra input tokens)
    time1 = time.time()
    print("Beginning to generate articles")
    out = []
    if verbose:
        print('generated scenarios: ', scenarios)
    for scenario in scenarios[1:4]:
        out.append(generate_article(user_prompt, scenario, relevant_articles, max_context_length = 10000))
    time2 = time.time()
    print(f"Generating output articles took {time2-time1} seconds")
    #########################################################################################################################################################
    
    '''
    out = scenarios

    if verbose:
        print("AI generated questions: ", AI_generated_questions, "\n\n\n\n")
        print("Relevant articles: ", relevant_articles, "\n\n\n\n")
        print("Created article:", out, "\n\n\n\n")
        print("Created scenarios:", scenarios, "\n\n\n\n")

    return [AI_generated_questions, relevant_articles, scenarios, out]




def q2a_workflow_wrapper(article, user_prompt, num_articles = 1, verbose = True):
    '''
    Placeholder function such that we receive all yields from q2a_workflow
    but we only return the desired output
    '''
    for out in q2a_workflow(article, user_prompt, num_articles, verbose):
        if type(out) == str:
            print(out)
        elif type(out) == list:
            for info in out:
                print(info)
            return out



def save_to_file(data, filename="out_article.txt"):
    with open(filename, 'w') as file:
        for entry in data:
            if isinstance(entry, list):
                for item in entry:
                    file.write(f"{item}\n")
            else:
                file.write(entry + "\n")
            file.write("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")