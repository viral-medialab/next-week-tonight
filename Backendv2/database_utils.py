from pymongo.mongo_client import MongoClient
from article_utils import *
from env import *
from openai_utils import get_embedding
from copy import deepcopy
from numpy import random
import numpy as np



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


client, db, collection = connect_to_mongodb()



def remove_duplicate_db_entries():
    client, db, collection = connect_to_mongodb()

    articles = set()
    for i, doc in enumerate(collection.find({})):
        if i % 10 == 0:
            print(f"Checked {i} docs so far")
        id = get_article_id(doc)
        title, author, content = get_article_contents_for_website(id)
        if hash(title + author) in articles:
            collection.delete_one( { 'url': doc['url'] } )
            print('Deleted duplicate of ID:', id)
        else:
            articles.add(hash(title + author))





def polish_trending_topic_entries():
    client, db, collection = connect_to_mongodb()
    collection = db["trendingTopics"]

    seen_articles = set()
    topic_embeddings = []
    topics = collection.find({})
    for topic in topics:
        topic_name = topic['topic']
        print(f"Checking if {topic_name} is similar to other topics")
        e = get_embedding(topic_name)
        for other_topic_name, other_e in topic_embeddings:
            s = similarity_score(e, other_e, verbose=False)
            if s > 0.9:
                collection.delete_one({'topic': topic_name})
                break
            else:
                topic_embeddings.append((topic_name, e))

        '''
        print(f"Removing unnecessary characters in topic names")
        new_entry = deepcopy(topic)
        new_entry['topic'] = topic['topic'].replace("\n", "")

        print(f"Deleting entries in {topic['topic']}")
        topic_articles = topic["articles"]
        new_topic_articles = []
        for article in topic_articles:
            id = get_article_id(article)
            title, author, content = get_article_contents_for_website(id)
            if hash(title + author) in seen_articles:
                print('Deleted duplicate of title:', title)
            else:
                print("Kept article in DB with title:", title)
                seen_articles.add(hash(title + author))
                new_topic_articles.append(article)
        new_entry['articles'] = new_topic_articles

        collection.replace_one(topic, new_entry)
        '''



def add_ids_to_entries():
    client, db, collection = connect_to_mongodb()
    for doc in collection.find({"id": {"$exists": False}}):
        new_doc = deepcopy(doc)
        id = get_article_id(new_doc)
        new_doc['id'] = id
        collection.replace_one(doc, new_doc)
        print(f'{doc["_id"]} -> {new_doc["_id"]} (UPDATE)')




def get_embeddings_from_mongo():
    client, db, collection = connect_to_mongodb()
    embeddings = []
    for doc in collection.find({ 'is_generated': { '$exists': False} }):
        if len(doc['semantic_embedding']) != 1536:
            raise Exception(f'Article at ID={doc["id"]} has incorret embedding vector')
        embeddings.append([doc['semantic_embedding'], doc['url']])
    return embeddings




def remove_topic(topic):
    client, db, collection = connect_to_mongodb()
    collection.delete_many( { 'topic': topic } )
    print('Removed all instances of topic:', topic)




def save_generated_article_to_DB(title, body, parent, query):
    client, db, collection = connect_to_mongodb()
    new_id = parent + str(random.randint(10**(len(parent)-1),10**(len(parent))))
    doc = {'title': title, 'body': body, 'parent': parent, 'id': new_id, 'query': query, 'is_generated': True}

    # we will make a two-way dependency in the DB
    # first, pull the article with the parent id and save the current article id as a child
    parent_doc = collection.find_one({'id': parent})
    new_doc = deepcopy(parent_doc)
    if 'children' in parent_doc:
        new_doc['children'].append(new_id)
    else:
        new_doc['children'] = [new_id]
    collection.replace_one(parent_doc, new_doc)

    # then, save the article itself in the database with the parent as its parent
    collection.insert_one(doc)
    return new_id, parent



def clear_cache(parent_id = None):
    client, db, collection = connect_to_mongodb()
    if parent_id:
        for doc in collection.find({"id" : {"$regex" : parent_id}}):
            if doc['id'] != parent_id:
                yield f"Now deleting document with id {doc['id']}"
                collection.delete_one(doc)
    else:
        collection.delete_many({'is_generated': True})
    return







def similarity_score(x, y, verbose = True):
    x = np.array(x)
    y = np.array(y)
    sim_score = x.T@y / (np.linalg.norm(x) * np.linalg.norm(y))
    if verbose:
        print(f"Similarity between the two embeddings is: {sim_score:.4f}")
    return sim_score




def find_closest_article_using_simple_search(question_embedding, article_embeddings):
    closest_dist = -1.1
    closest_url = False
    for other_embed in article_embeddings:
        if not closest_url or similarity_score(question_embedding, other_embed[0], verbose=False) > closest_dist:
            closest_dist = similarity_score(question_embedding, other_embed[0], verbose=False)
            closest_url = other_embed[1]

    return closest_url




def add_children_to_all_entries():
    client, db, collection = connect_to_mongodb()
    collection = db['trendingTopics']
    # we will make a two-way dependency in the DB
    # first, pull the article with the parent id and save the current article id as a child


    topics = collection.find({})
    for topic in topics:
        new_entry = deepcopy(topic)
        new_entry['articles'] = []
        for article in topic['articles']:
            if 'children' not in article:
                new_article = deepcopy(article)
                new_article['children'] = []
                new_entry['articles'].append(new_article)
                print(f"Adding children field to document with id {article['id']}")
        collection.replace_one(topic, new_entry)





if __name__ == '__main__':
    add_children_to_all_entries()