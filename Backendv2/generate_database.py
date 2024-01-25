import requests
import sys
from pretrained_models import SentimentModel
from openai_utils import *
from database_utils import *
from article_utils import *
from env import *

sentiment_model = SentimentModel()



def populate_database_by_recent_news(num_articles_to_store = 100, num_topics = 10):
    url = "https://api.bing.microsoft.com/v7.0/news"  # Changed to general news endpoint
    headers = {'Ocp-Apim-Subscription-Key': BING_API_KEY}
    query_params = {"count": 10, "q": "Breaking Global US News", "mkt": "en-US"}
    response = requests.get(url, headers=headers, params = query_params)
    response.raise_for_status()
    results = response.json()['value']

    context = "Return a comprensive list of unique topics covered by these news headlines and descriptions. These topics will be used by a news API to get even more articles on the particular topic. Please provide specific topics. It is essential the topics do not overlap with each other and are unique, that is, do not be repetitive. Format the response as an array of topics. For example, [\"Pakistani's defeat in war against Iraq\", \"New York Marathon\", \"US Senate elections\"]. Use enough descriptive words (up to 7 words) to make the topic specific enough and captilize the first letter. Do not miscategorize topics, for example: if the topic is \"Convicted Felon arrested for illegal weapons in Washington\", do not miscategorize it as \"Washington Senator convicted for illegal weapons\". Remain true to the topic at hand. Do not use commas in the topics to avoid ambiguity with the array commas. Do not return anything else except the array."
    query =  "News headlines and descriptions (separated by semicolons): "
    for article in results:
        query = query + article['name'] + article['description'] + '; '
    topics = query_chatgpt(context, query[:-2])[1:-1].replace(' "','').replace('"','').split(",")

    for topic in topics:
        print("NOW EXAMINING HEADLINES IN ", topic.upper())
        populate_database_by_topic(topic, num_articles_to_store // num_topics)





def populate_database_by_topic(topic, num_articles_to_store):
    client, db, collection = connect_to_mongodb()

    num_articles_stored = 0
    offset = 0
    while num_articles_stored < num_articles_to_store:
        articles = find_articles_by_topic(topic, offset)
        articles = filter_msn_articles(articles)
        for article in articles:
            try:
                cur_article_id = get_article_id(article)
                cur_article_url = article['url']
                if collection.count_documents({'id': cur_article_id}) == 0 and collection.count_documents({'url': cur_article_url}) == 0:
                    metadata = gather_article_metadata(article, topic, sentiment_model)
                    result = collection.insert_one(metadata)
                    num_articles_stored += 1
                    print(f"Document added. The document ID is: {result.inserted_id}")
            
            except Exception as e:
                print(f"An error occurred: {e}")
                continue

        offset += 100




def find_articles_by_topic(topic, offset = 0):
    #api_endpoint = "https://api.bing.microsoft.com/"
    api_endpoint = "https://api.bing.microsoft.com/v7.0/news/search"

    query_params = {
        "q": topic + ' site:msn.com',
        "count": 100, 
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
        raise Exception("Usage: \npython generate_dataset.py <amount_of_articles> <topic> , or\n python generate_dataset.py <amount_of_articles> <num_topics>")
        
    try:
        amount_of_articles = int(args[1])
        num_topics = int(args[2])
        print(f"Now adding {amount_of_articles} articles on {num_topics} trending topics into the database.")
        populate_database_by_recent_news(amount_of_articles, num_topics)
    except:
        amount_of_articles = int(args[1])
        topic = args[2]
        print(f"Now adding {amount_of_articles} articles on {topic} into the database.")
        populate_database_by_topic(topic, amount_of_articles)




if __name__=='__main__':
    main(sys.argv)