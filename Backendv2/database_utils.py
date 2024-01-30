from pymongo.mongo_client import MongoClient
from article_utils import *
from env import *
from copy import deepcopy
from numpy import random



def connect_to_mongodb():
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




def save_generated_article_to_DB(title, body, parent):
    client, db, collection = connect_to_mongodb()
    new_id = str(random.randint(10**(len(parent)-1),10**(len(parent))))
    doc = {'title': title, 'body': body, 'parent': parent, 'id': new_id, 'is_generated': True}

    # we will make a two-way dependency in the DB
    # first, pull the article with the parent id and save the current article id as a child
    parent_doc = collection.find({'id': parent})
    new_doc = deepcopy(parent_doc)
    if 'children' in parent_doc:
        new_doc['children'].append(new_id)
    else:
        new_doc['children'] = [new_id]
    collection.update_one(parent_doc, new_doc)

    # then, save the article itself in the database with the parent as its parent
    collection.insert_one(doc)
