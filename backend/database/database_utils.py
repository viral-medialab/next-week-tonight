from pymongo.mongo_client import MongoClient
from backend.api import *
from backend.test.env import *
from backend.llm.openai_utils import get_embedding
from copy import deepcopy
from numpy import random
import numpy as np


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




def save_generated_article_to_DB(title, body, parent, query, probability, impact):
    client, db, collection = connect_to_mongodb()
    #id_length = 8 
    parent_id = get_article_id(parent)
    new_id = parent_id + str(random.randint(10**(len(parent_id)-1),10**(len(parent_id))))
    doc = {'title': title, 'body': body, 'parent': parent, 'id': new_id, 'query': query, 'is_generated': True, 'probability':probability, 'impact':impact}

    # we will make a two-way dependency in the DB
    # first, pull the article with the parent id and save the current article id as a child
    parent_doc = collection.find_one({'url': parent})
    new_doc = deepcopy(parent_doc)
    if 'children' in parent_doc:
        new_doc['children'].append(new_id)
    else:
        new_doc['children'] = [new_id]
    collection.replace_one(parent_doc, new_doc)

    # then, save the article itself in the database with the parent as its parent
    collection.insert_one(doc)
    return new_id, parent

def save_generated_article_to_trending_topic_DB(all_generated_articles, article_url, user_prompt):
    client, db, collection = connect_to_mongodb(collection_to_open='trendingTopics')
    article_id = get_article_id(article_url)
    
    topic = collection.find_one({"articles.0.id": article_id})
    
    if topic:
        # Prepare the new questions data
        new_questions = {}
        for key, article in all_generated_articles.items():
            # prob = article['probability']
            # pol = article['polarity']
            new_questions[key] = {
                "title": article['title'],
                "body": article['body'],
                "id": article['id'],
                "parent": article['parent'],
                "probability": article["probability"], 
                "impact": article['impact']
            }

        # Update or add the user_prompt and generated articles
        update_query = {
            "$set": {
                f"articles.0.questions.{user_prompt}": new_questions
            }
        }

        # Update the document in the database
        result = collection.update_one({"_id": topic["_id"]}, update_query)
        
        if result.modified_count > 0:
            print(f"Updated first article in topic with new generated content for prompt: {user_prompt}")
        else:
            print(f"No changes were made to the document")
    else:
        print(f"Article with ID {article_id} not found as the first article in any topic")

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

def clear_all_expired_articles():
    client, db, collection = connect_to_mongodb() # article database
    for doc in collection.find({ 'url': { '$exists': True} }):
        contents = get_article_contents_from_id(doc['id'])
        if contents:
            print(f"Success with doc['id'] = {doc['id']}")
        else:
            print(f"Deleting doc with doc['id'] = {doc['id']}")
            collection.delete_one(doc)

def clear_trending_topics():
    client, db, collection = connect_to_mongodb(collection_to_open = 'trendingTopics') # article database
    for doc in collection.find({ 'articles': { '$exists': True} }):
        print(f"Deleting doc with doc['topic'] = {doc['topic']}")
        collection.delete_one(doc)


def update_articles_with_id():
    client, db, collection = connect_to_mongodb()  # This will use the default collection
    
    # Find all documents that don't have an 'id' field
    query = {'id': {'$exists': False}, 'url': {'$exists': True}}
    
    for doc in collection.find(query):
        if 'url' in doc:
            # Generate id from the URL
            article_id = get_article_id(doc['url'])
            
            # Update the document with the new id
            collection.update_one(
                {'_id': doc['_id']},
                {'$set': {'id': article_id}}
            )
            print(f"Updated article with URL {doc['url']} to have id {article_id}")

    print("Finished updating articles with ids")


def populate_trending_topics():
    client, db, collection = connect_to_mongodb()
    
    # Use aggregation to find all unique topics in the articles collection
    pipeline = [
        {"$group": {"_id": "$topic"}}
    ]
    unique_topics = collection.aggregate(pipeline)
    
    trending_topics_collection = db['trendingTopics']
    
    for topic in unique_topics:
        topic_name = topic['_id']
        print(f"Processing topic: {topic_name}")
        
        # Find all articles related to this topic
        articles = list(collection.find({"topic": topic_name}))
        
        if articles:
            # Check if the topic already exists in trendingTopics
            existing_entry = trending_topics_collection.find_one({"topic": topic_name})
            
            if existing_entry:
                # Merge new articles with existing ones
                existing_article_ids = {article['id'] for article in existing_entry['articles']}
                new_articles = [article for article in articles if article['id'] not in existing_article_ids]
                
                if new_articles:
                    # Update the existing entry with new articles
                    trending_topics_collection.update_one(
                        {"topic": topic_name},
                        {"$push": {"articles": {"$each": new_articles}}}
                    )
                    print(f"Updated topic '{topic_name}' with {len(new_articles)} new articles.")
                else:
                    print(f"No new articles to add for topic: {topic_name}")
            else:
                # Insert the new topic with its articles
                trending_topic_entry = {
                    "topic": topic_name,
                    "articles": articles
                }
                trending_topics_collection.insert_one(trending_topic_entry)
                print(f"Inserted topic '{topic_name}' with {len(articles)} articles into trendingTopics.")
        else:
            print(f"No articles found for topic: {topic_name}")

    print("Finished populating trending topics.")

# Example usage
if __name__ == '__main__':
    populate_trending_topics()