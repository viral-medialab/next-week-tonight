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
    article_context = "Make up to 7 questions. Here is the article that you will use to aid your question making: " + article_context
    return query_chatgpt([context_prompt, article_context], [user_prompt], model="gpt-3.5-turbo-0125")



def summarize_articles(text_from_articles):
    context_prompt = summarize_prompt
    query_prompts = text_from_articles
    return query_chatgpt([context_prompt], [query_prompts])




def generate_what_if_questions(text_from_articles, num_preds = 3):
    instruction_context_prompt = what_if_prompt
    query_prompt = f'Generate exactly {num_preds} what-if questions, separated by semi-colons, based on the following article:\n\n' + text_from_articles
    return query_chatgpt([instruction_context_prompt], [query_prompt])





def generate_scenario(relevant_articles, xscale, yscale, extreme_scenarios, user_query, max_context_length = 10000):
    #Relevant info is a list of strings where each string is an article body
    relevant_context = "Here is some relevant information that will aid in your answers: ".replace("\n", "")
    for article in relevant_articles:
        if type(article) == str:
            relevant_context += article + "   --- NEXT ARTICLE ---   "
    relevant_context = relevant_context[:-1]

    extremes_context = f'Here are some examples of extremes for the query:\n\n IMPACT EXTREMES-{extreme_scenarios["yscale_extremes"]}\nPROBABILITY EXTREMES-{extreme_scenarios["xscale_extremes"]}'

    query = single_scenario_using_pol_prob_prompt + "\n\n Here is the query: " + user_query + "\n" + extremes_context + f"\nThe impact is {yscale} and the probability is {xscale}"

    scenario = query_chatgpt([relevant_context], [query[:max_context_length]])
    
    actual_scenario = ""
    if type(scenario) == list:
        for part in scenario:
            actual_scenario += part + ";"
        scenario = actual_scenario[:-1]

    scenario_title= query_chatgpt([], ["Make a title for this scenario (write the title, but do not specify that it is the title by saying 'title:' or 'scenario header:' anything similar, and do not put quotes around it): " + scenario], model="gpt-3.5-turbo-0125")
    out = [scenario_title, scenario]

    return out




def q2a_workflow(article, article_url, user_prompt, xscale, yscale, verbose = True):
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
    # #article_id = get_article_id_from_url(article_url)
    # time1 = time.time()
    # AI_generated_questions = generate_relevant_questions(article, user_prompt)
    # time2 = time.time()
    # if verbose: print(f"Generating questions took {time2-time1} seconds")

    # Generate AI-suggestions if not already generated
    time1 = time.time()
    client, db, collection = connect_to_mongodb(collection_to_open='trendingTopics')
    topic_doc = collection.find_one({'articles.url': article_url})
    
    if topic_doc and topic_doc['articles']:
        for article_doc in topic_doc['articles']:
            if article_doc['url'] == article_url:
                AI_generated_questions = list(article_doc.get('questions', {}).keys())
                break
    else:
        AI_generated_questions = []

    if not AI_generated_questions:
        AI_generated_questions = generate_relevant_questions(article, user_prompt)
    
    time2 = time.time()
    if verbose: print(f"Generating questions took {time2-time1} seconds")

    time1 = time.time()
    embeddings = [get_embedding(user_prompt)] + [get_embedding(question) for question in AI_generated_questions[:3]]
    time2 = time.time()
    if verbose: print(f"Fetching embeddings took {time2-time1} seconds")
    

    time1 = time.time()
    relevant_article_urls = [find_closest_article_using_simple_search(embedding, all_doc_embeddings) for embedding in embeddings]
    time2 = time.time()
    if verbose: print(f"Finding relevant articles took {time2-time1} seconds")
    

    time1 = time.time()
    relevant_article_urls = list(set(relevant_article_urls))
    context_window = 2500
    relevant_articles = []
    for url in relevant_article_urls:
        article_contents = get_article_contents_from_id(get_article_id(url))
        if article_contents:
            relevant_articles.append(article_contents[:(context_window//len(relevant_article_urls))])
        else:
            pass
    if not relevant_articles:
        relevant_articles = ["No relevant articles"]
    time2 = time.time()
    if verbose: print(f"Loading relevant article contents took {time2-time1} seconds")
    

    time1 = time.time()
    extreme_scenarios = retrieve_extreme_scenarios(user_prompt, article_url, xscale, yscale)
    time2 = time.time()
    if verbose: print(f"Generating extreme scenarios took {time2-time1} seconds")

    time1 = time.time()
    scenario_title, scenario = generate_scenario(relevant_articles, xscale, yscale, extreme_scenarios, user_query=user_prompt, max_context_length = 10000) #pass in polarity, probability, extreme statements 
    time2 = time.time()
    if verbose: print(f"Generating scenario based on articles and query took {time2-time1} seconds")

    scenario += "\n\n\nSources: "
    for i, article_url in enumerate(relevant_article_urls):
        scenario += f"\n({i}) " + article_url
    
    out = [scenario_title, scenario]

    if verbose:
        print("AI generated questions: ", AI_generated_questions, "\n\n\n\n")
        print("Relevant articles: ", relevant_articles, "\n\n\n\n")
        print("Created article:", out, "\n\n\n\n")
        print("Created scenario:", scenario, "\n\n\n\n")


    return [AI_generated_questions, relevant_articles, scenario, out]


def retrieve_extreme_scenarios(user_prompt, article_url, xscale, yscale, override=False):
    client, db, articles_collection = connect_to_mongodb()
    trending_topics_collection = db['trendingTopics']
    
    article_id = get_article_id(article_url)
    print("article url: ", article_url)
    
    # Find the article in the articles collection
    doc = articles_collection.find_one({'id': article_id})
    if not doc:
        print(f"Article with ID {article_id} not found in articles collection")
        return None

    if 'prompts' not in doc:
        doc['prompts'] = {}
    
    if user_prompt in doc['prompts'] and not override:
        return doc['prompts'][user_prompt]
    else:
        xscale_results = query_chatgpt([], [extreme_scenario_context + f"\n{user_prompt} // Probability "])
        yscale_results = query_chatgpt([], [extreme_scenario_context + f"\n{user_prompt} // Impact "])
        out = {"xscale_extremes": xscale_results, "yscale_extremes": yscale_results}
        doc['prompts'][user_prompt] = out
        
        # Update the article in the articles collection
        articles_collection.replace_one({'id': article_id}, doc)
        
        # Update the article in the trendingTopics collection
        trending_topic = trending_topics_collection.find_one({'articles.id': article_id})
        if trending_topic:
            for article in trending_topic['articles']:
                if article['id'] == article_id:
                    article['prompts'] = doc['prompts']
                    break
            trending_topics_collection.replace_one({'_id': trending_topic['_id']}, trending_topic)
            print(f"Updated article in trendingTopics collection")
        else:
            print(f"Article with ID {article_id} not found in trendingTopics collection")
        
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





if __name__ == '__main__':
    user_prompt = 'What if Iran declares war on Israel?'
    article_id = 'AA1n5srJ'
    article_url = 'https://www.msn.com/en-us/news/world/iran-is-ready-to-attack-israel-if-needed-says-iranian-general/ar-AA1n5srJ'
    print(retrieve_extreme_scenarios(user_prompt, article_id, override=False))
    print(generate_scenario([get_article_contents_from_id(article_id)], 7, 1, retrieve_extreme_scenarios(user_prompt, article_url), user_prompt, max_context_length = 10000))
    print(generate_scenario([get_article_contents_from_id(article_id)], 4, 4, retrieve_extreme_scenarios(user_prompt, article_url), user_prompt, max_context_length = 10000))
    print(generate_scenario([get_article_contents_from_id(article_id)], 1, 7, retrieve_extreme_scenarios(user_prompt, article_url), user_prompt, max_context_length = 10000))