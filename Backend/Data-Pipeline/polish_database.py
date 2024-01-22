from pymongo import MongoClient
from article_preprocess import fetch_article_id
from dotenv import load_dotenv
import os

load_dotenv("../vars.env")

def remove_duplicate_db_entries():
    uri = os.environ.get("MONGODB_URI")
    client = MongoClient(uri)
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
    db = client["news"]
    collection = db["articles"]

    ids = set()
    for doc in collection.find({}):
        id = fetch_article_id(doc)
        if id in ids:
            collection.delete_one( { 'url': doc['url'] } )
            print('Deleted duplicate of ID:', id)
            print(doc['url'])
        else:
            ids.add(id)



if __name__=='__main__':
    remove_duplicate_db_entries()