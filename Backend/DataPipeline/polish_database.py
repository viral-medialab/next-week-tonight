from pymongo import MongoClient
from article_preprocess import fetch_article_id
from dotenv import load_dotenv
import os
from copy import deepcopy
load_dotenv("../../vars.env")


def load_mongodb():
    uri = os.environ.get("MONGODB_URI")
    client = MongoClient(uri)
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
    db = client["news"]
    collection = db["articles"]

    return client, db, collection




def remove_duplicate_db_entries():
    client, db, collection = load_mongodb()

    ids = set()
    for doc in collection.find({}):
        id = fetch_article_id(doc)
        if id in ids:
            collection.delete_one( { 'url': doc['url'] } )
            print('Deleted duplicate of ID:', id)
            print(doc['url'])
        else:
            ids.add(id)



def add_ids_to_entries():
    client, db, collection = load_mongodb()
    for doc in collection.find({}):
        if 'id' not in doc:
            new_doc = deepcopy(doc)
            id = fetch_article_id(new_doc)
            new_doc['id'] = id
            collection.update_one(doc, new_doc)
            print(f'{doc} -> {new_doc} (UPDATE)')
    


if __name__=='__main__':
    add_ids_to_entries()