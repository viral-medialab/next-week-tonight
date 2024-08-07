import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Backendv2')))

from pymongo import MongoClient
from datetime import datetime, timedelta
import argparse

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

def find_articles(topic, months):
    client, db, collection = connect_to_mongodb()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30*months)
    
    # Query articles based on topic and date range
    articles = collection.find({
        'topic': topic,
        'date_published': {
            '$gte': start_date,
            '$lte': end_date
        }
    })
    
    # Print each article and count the total number of articles
    article_count = 0
    for article in articles:
        print(f"Article ID: {article['_id']}")
        print(f"URL: {article.get('url', 'No url')}")
        print(f"Author: {article.get('author', 'No author')}")
        print(f"Date Published: {article.get('date_published', 'No date')}")
        print("-" * 80)
        article_count += 1
    
    print(f"Total number of articles found: {article_count}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Print articles from the database based on topic and date range.')
    parser.add_argument('topic', type=str, help='The topic to filter articles by.')
    parser.add_argument('months', type=int, help='The number of months to look back for articles.')

    args = parser.parse_args()
    find_articles(args.topic, args.months)
