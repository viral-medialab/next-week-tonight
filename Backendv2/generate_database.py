import requests
import sys
from pretrained_models import SentimentModel
from openai_utils import *
from database_utils import *
from article_utils import *
from env import *
from prompts import *

sentiment_model = SentimentModel()



def populate_database_by_recent_news(num_articles_to_store = 2, num_topics = 20, simple_return = False, offset=0):
    url = "https://api.bing.microsoft.com/v7.0/news"  # Changed to general news endpoint
    headers = {'Ocp-Apim-Subscription-Key': BING_API_KEY}
    query_params = {"count": num_topics*2, 
                    "q": "Breaking Global US News",
                    "mkt": "en-US", 
                    "offset": 0}
    response = requests.get(url, headers=headers, params = query_params)
    response.raise_for_status()
    results = response.json()['value']

    context = trending_topics_prompt
    query =  "News headlines and descriptions (separated by semicolons): "
    for article in results:
        query = query + article['name'] + article['description'] + '; '
    topics = query_chatgpt([context], [query[:-2]])[1:-1].replace(' "','').replace('"','').split(",")

    if simple_return:
        return topics

    successful_topics = 0
    for topic in topics:
        if successful_topics < num_topics:
            print("NOW EXAMINING HEADLINES IN ", topic.upper())
            if populate_database_by_topic(topic, num_articles_to_store // num_topics, trending_topic=True):
                successful_topics += 1




def populate_database_by_topic(topic, num_articles_to_store, trending_topic=False, max_attempts = 30):
    client, db, collection = connect_to_mongodb()

    num_articles_stored = 0
    offset = 0
    if trending_topic:
        entry = {'topic': topic, 'articles': []}
    attempts = 0
    while num_articles_stored < num_articles_to_store and attempts < max_attempts:
        articles = find_articles_by_topic(topic, offset, count=min(5*num_articles_to_store,100))
        articles = filter_msn_articles(articles)
        for article in articles:
            try:
                cur_article_id = get_article_id(article)
                cur_article_url = article['url']
                if collection.count_documents({'id': cur_article_id}) == 0 and collection.count_documents({'url': cur_article_url}) == 0:
                    metadata = gather_article_metadata(article, topic, sentiment_model)
                    result = collection.insert_one(metadata)
                    if trending_topic:
                        entry['articles'].append(metadata)
                    num_articles_stored += 1
                    print(f"Document added. The document ID is: {result.inserted_id}")
            
            except Exception as e:
                print(f"An error occurred: {e}")
                continue

        offset += min(5*num_articles_to_store,100)
        attempts += 1

    if trending_topic:
        article_count = len(entry['articles'])
        if article_count >= 6:
            result = db['trendingTopics'].insert_one(entry)
            article_count = len(entry['articles'])
            print(f"Trending topic with {article_count} articles added to DB, the document id is {result.inserted_id}")
            return True
        else:
            return False




def find_articles_by_topic(topic, offset = 0, count=100):
    #api_endpoint = "https://api.bing.microsoft.com/"
    api_endpoint = "https://api.bing.microsoft.com/v7.0/news/search"

    query_params = {
        "q": topic + ' site:msn.com',
        "count": count, 
        "mkt": "en-US", 
        "offset": offset,
    }
    headers = {
        "Ocp-Apim-Subscription-Key": BING_API_KEY
    }

    try:
        response = requests.get(api_endpoint, headers=headers, params=query_params)
        response.raise_for_status()
        results = response.json()
    except Exception as e:
        print(f"Error: {e}")

    articles = results['value']

    print(f"Found {len(articles)} articles on {topic} with offset {offset}")

    return articles




def main(args):
    '''
    Adds articles to the database depending on user specification

    >> python generate_dataset.py 100 "Israel Gaza War"
    Now adding 100 articles on Israel Gaza war into the database

    >> python generate_dataset.py 100 10
    Now adding 100 articles on 10 trending topics into the database
    '''
    if len(args) != 3:
        print("Usage: \npython generate_dataset.py <amount_of_articles> <topic> , or\n python generate_dataset.py <amount_of_articles> <num_topics>")
        sys.exit(1)

    if args[2].isdigit():
        amount_of_articles = int(args[1])
        num_topics = int(args[2])
        print(f"Now adding {amount_of_articles} articles on {num_topics} trending topics into the database.")
        populate_database_by_recent_news(amount_of_articles, num_topics)
    else:
        amount_of_articles = int(args[1])
        topic = args[2]
        print(f"Now adding {amount_of_articles} articles on {topic} into the database.")
        populate_database_by_topic(topic, amount_of_articles, True)




if __name__=='__main__':
    #main(sys.argv)
    topics = ["U.S. Sends Ukraine Weapons Seized From Iran",
              "Marjorie Taylor Greene Keeps Up Pressure on Speaker Johnson",
              "Parents of Michigan School Shooter Sentenced For Manslaughter",
              "Arizona Supreme Court Issues Near-Total Ban On Abortions",
              "Trump Hush Money Trial To Move Ahead Despite Bid To Delay",
              "Russia Foreign Minister Visits Beijing"]
    for topic in topics:
        pass#populate_database_by_topic(topic, 5, trending_topic=True, max_attempts = 30)