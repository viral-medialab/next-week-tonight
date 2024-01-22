from article_preprocess import gather_article_metadata, fetch_article_id
import requests
import json
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv("../vars.env")

def populate_database_by_recent_news(num_articles_to_store = 100, num_topics = 10):
    url = "https://api.bing.microsoft.com/v7.0/news"  # Changed to general news endpoint
    api_key = os.environ.get("BING_API")  # Replace with your Bing News Search API key
    headers = {'Ocp-Apim-Subscription-Key': api_key}
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
    client = connect_to_mongodb()

    # Select database and collection
    db = client["news"]
    collection = db["articles"]
    num_articles_stored = 0
    offset = 10000
    while num_articles_stored < num_articles_to_store:
        articles = find_articles_by_topic(topic, offset)
        articles = filter_msn_articles(articles)
        for article in articles:
            try:
                cur_article_id = fetch_article_id(article)
                cur_article_url = article['url']
                if collection.count_documents({'id': cur_article_id}) == 0 and collection.count_documents({'url': cur_article_url}) == 0:
                    metadata = gather_article_metadata(article, topic)
                    result = collection.insert_one(metadata)
                    num_articles_stored += 1
                    print(f"Document added. The document ID is: {result.inserted_id}")
            
            except Exception as e:
                print(f"An error occurred: {e}")
                continue

        offset += 10000
        


    
def connect_to_mongodb():
    mongo_uri = os.environ.get("MONGODB_URI")
    client = MongoClient(mongo_uri)
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
    
    return client



def find_articles_by_topic(topic, offset = 0):
    # Bing News Search API endpoint and key
    #api_endpoint = "https://api.bing.microsoft.com/"
    api_endpoint = "https://api.bing.microsoft.com/v7.0/news/search"
    api_key = os.environ.get("BING_API")  # Replace with your Bing News Search API key

    # Bing News Search API Call
    query_params = {
        "q": topic + ' site:msn.com',  # Your search query
        "count": 100,  # Number of results to return (1 for the top article)
        "mkt": "en-US",  # Market; adjust as needed
        "offset": offset,
    }
    headers = {
        "Ocp-Apim-Subscription-Key": api_key
    }

    try:
        response = requests.get(api_endpoint, headers=headers, params=query_params)
        response.raise_for_status()
        results = response.json()
    except Exception as e:
        print(f"Error: {e}")

    articles = results['value']

    return articles



def filter_msn_articles(articles):
    return [article for article in articles if 'msn.com' in article['url']]




def query_chatgpt(context, query):
    # Query ChatGPT and return the response (this function needs to be defined)
    # Set your OpenAI API key
    openai_api = os.environ.get("OPENAI_API")

    client = OpenAI(
        #  This is the default and can be omitted
        api_key=openai_api,
    )


    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": context,
            },
            {
                "role": "user",
                "content": query
            }
        ],
        model="gpt-4",
    )

    return response.choices[0].message.content




if __name__ == '__main__':
    populate_database_by_recent_news(num_articles_to_store = 120, num_topics = 12)