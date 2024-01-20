from pymongo import MongoClient
from sklearn.neighbors import KDTree
import numpy as np
from dotenv import load_dotenv
import os

load_dotenv("../vars.env")

def fetch_embeddings_from_mongo():
    uri = os.environ.get("MONGODB_URI")
    client = MongoClient(uri)
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
    db = client["news"]
    collection = db["articles"]

    embeddings = []
    urls = set()
    for doc in collection.find({}):
        # Assuming each document has an 'embedding' field
        if len(doc['semantic_embedding']) != 1536:
            print(doc['url'])
        if doc['url'] not in urls:
            urls.add(doc['url'])
            embeddings.append([doc['semantic_embedding'], doc['url']])
    return embeddings



def build_kd_tree(embeddings):
    return KDTree(embeddings, leaf_size=40, metric='')



def find_closest_article(embedding, article_embeddings):
    closest_dist = -1.1
    closest_url = False
    for other_embed in article_embeddings:
        if not closest_url or similarity_score(embedding, other_embed[0], verbose=False) > closest_dist:
            closest_dist = similarity_score(embedding, other_embed[0], verbose=False)
            closest_url = other_embed[1]

    return closest_url


from openai import OpenAI
openai_api = os.environ.get("OPENAI_API")

def get_embedding(text, engine = 'text-embedding-ada-002'):
    """
    Get the embedding for the given text using OpenAI's Embedding API.

    :param text: The text to embed.
    :param engine: The embedding engine to use.
    :return: Embedding vector.
    """
    client = OpenAI(
        #  This is the default and can be omitted
        api_key=openai_api,
    )

    text = text.replace("\n", " ")
    return client.embeddings.create(input = [text], model=engine).data[0].embedding


def similarity_score(x, y, verbose = True):
    x = np.array(x)
    y = np.array(y)
    sim_score = x.T@y / (np.linalg.norm(x) * np.linalg.norm(y))
    if verbose:
        print(f"Similarity between the two embeddings is: {sim_score:.4f}")
    return sim_score


embeddings = fetch_embeddings_from_mongo()
query = "Will Gaza surrender to Israel soon"
query_embedding = get_embedding(query)

u = find_closest_article(query_embedding, embeddings)
print(u)


# comparing articles to each other
'''
embeddings = fetch_embeddings_from_mongo()
print(len(embeddings))
i = 250
print(embeddings[i][1])
query_embedding = embeddings[i][0]
embeddings = embeddings[0:i] + embeddings[i+1:]

u = find_closest_article(query_embedding, embeddings)
print(u)

'''


# KD Tree optimization for later
'''print(KDTree.valid_metrics)

# Fetch embeddings
embeddings = fetch_embeddings_from_mongo()

# Build KD Tree
tree = build_kd_tree(embeddings)

# Example usage: finding the nearest neighbor of a sample query embedding
query_embedding = np.array([1/np.sqrt(1536),] * 1536)  # replace with the query embedding
dist, ind = tree.query([query_embedding], k=1)
print(f"Closest article index: {ind[0][0]}, Distance: {dist[0][0]}")


'''
