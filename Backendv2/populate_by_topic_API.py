import sys
import os
import requests
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import argparse
from dotenv import load_dotenv
from article_utils import *
from openai_utils import *
from pretrained_models import SentimentModel

sentiment_model = SentimentModel()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Backendv2')))

load_dotenv(os.path.join(os.path.dirname(__file__), 'vars.env'))
BING_API_KEY= "9285350d8f594e289835615f984deced"
MONGODB_URI_KEY= "mongodb+srv://viralgrads3:viralgrads3@sandbox.h8gtitv.mongodb.net" 


def connect_to_mongodb(collection_to_open = 'articles'):
    client = MongoClient(MONGODB_URI_KEY)
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
    
    db = client["news"]
    collection = db[collection_to_open]

    return client, db, collection

def fetch_articles_from_api(topic, start_date, end_date, api_key):
    url = "https://api.bing.microsoft.com/v7.0/news"
    headers = {'Ocp-Apim-Subscription-Key': BING_API_KEY}
    params = {
        'q': topic,
        'count': 100,
        'offset': 0,
        'mkt': 'en-US',
        'since': start_date,
        'sortBy': 'Date'
    }
    response = requests.get(url, headers=headers, params=params)
    print(f"Response status code: {response.status_code}")
    if response.status_code == 200:
        return response.json().get('value', [])
    else:
        print(f"Failed to fetch articles: {response.status_code}")
        print(f"Response content: {response.content}")
        return []


def update_articles(topic, months, api_key):
    client, db, collection = connect_to_mongodb()

    end_date = datetime.now().isoformat()
    start_date = (datetime.now() - timedelta(days=30*months)).isoformat()

    articles = fetch_articles_from_api(topic, start_date, end_date, api_key)
    
    # Save articles to MongoDB
    for article in articles:
        metadata = gather_article_metadata(article, topic, sentiment_model)
        # article['_id'] = str(ObjectId())
        # article['topic'] = topic
        result = collection.insert_one(metadata)
        print(f"Inserted article with ID: {result.inserted_id}")
        print(article)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fetch and update articles in the database based on topic and date range.')
    parser.add_argument('topic', type=str, help='The topic to filter articles by.')
    parser.add_argument('months', type=int, help='The number of months to look back for articles.')

    args = parser.parse_args()

    NEWS_API="199546a71aec433c9fd5df30fb4ca1cd"

    update_articles(args.topic, args.months, NEWS_API)
