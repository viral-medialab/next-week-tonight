from pymongo.mongo_client import MongoClient
from article_utils import *
from env import *
from copy import deepcopy



def connect_to_mongodb(return_db_collection = False):
    client = MongoClient(MONGODB_URI_KEY)
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
    
    db = client["news"]
    collection = db["articles"]

    return client, db, collection




def remove_duplicate_db_entries():
    client, db, collection = connect_to_mongodb()

    ids = set()
    for doc in collection.find({}):
        id = get_article_id(doc)
        if id in ids:
            collection.delete_one( { 'url': doc['url'] } )
            print('Deleted duplicate of ID:', id)
        else:
            ids.add(id)




def add_ids_to_entries():
    client, db, collection = connect_to_mongodb()
    for doc in collection.find({}):
        if 'id' not in doc:
            new_doc = deepcopy(doc)
            id = get_article_id(new_doc)
            new_doc['id'] = id
            collection.update_one(doc, new_doc)
            print(f'{doc} -> {new_doc} (UPDATE)')




def get_embeddings_from_mongo():
    client, db, collection = connect_to_mongodb()
    embeddings = []
    urls = set()
    for doc in collection.find({}):
        # Assuming each document has an 'embedding' field
        if len(doc['semantic_embedding']) != 1536:
            raise Exception(f'Article at ID={doc["id"]} has incorret embedding vector')
        if doc['url'] not in urls:
            urls.add(doc['url'])
            embeddings.append([doc['semantic_embedding'], doc['url']])
    return embeddings




def remove_topic(topic):
    client, db, collection = connect_to_mongodb()
    collection.delete_many( { 'topic': topic } )
    print('Removed all instances of topic:', topic)