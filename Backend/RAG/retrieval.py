from pymongo.mongo_client import MongoClient
#from sklearn.neighbors import KDTree
import numpy as np
from dotenv import load_dotenv
import os
from openai import OpenAI
# import faiss
import numpy as np
load_dotenv("../../vars.env")
load_dotenv("vars.env")
openai_api = os.environ.get("OPENAI_API")



def fetch_embeddings_from_mongo():
    uri = os.environ.get("MONGODB_URI")
    print(uri)
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




def find_closest_article_using_simple_search(embedding, article_embeddings):
    closest_dist = -1.1
    closest_url = False
    for other_embed in article_embeddings:
        if not closest_url or similarity_score(embedding, other_embed[0], verbose=False) > closest_dist:
            closest_dist = similarity_score(embedding, other_embed[0], verbose=False)
            closest_url = other_embed[1]

    return closest_url



def find_closest_article_using_FAISS(embedding, article_embeddings, num_articles):
    # Example dataset: 10000 vectors of dimension 512
    d = len(embedding) # Dimension
    db_vectors = [np.array(article_embedding[0]).astype('float32') for article_embedding in article_embeddings]
    query_vector = np.array(embedding).astype('float32')

    # Create the index
    index = faiss.IndexFlatIP(d)

    # Add vectors to the index
    index.add(db_vectors)

    # Perform the search
    k = num_articles  # Number of nearest neighbors to retrieve
    D, I = index.search(query_vector, k)  # D is the distance (dot product here), I is the indices of neighbors
    return D, I



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



if __name__ == '__main__':
    embeddings = fetch_embeddings_from_mongo()
    query = "Will Gaza surrender to Israel soon"
    query_embedding = get_embedding(query)

    u = find_closest_article_using_simple_search(query_embedding, embeddings)
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


def build_kd_tree(embeddings):
    return KDTree(embeddings, leaf_size=40, metric='')

# Fetch embeddings
embeddings = fetch_embeddings_from_mongo()

# Build KD Tree
tree = build_kd_tree(embeddings)

# Example usage: finding the nearest neighbor of a sample query embedding
query_embedding = np.array([1/np.sqrt(1536),] * 1536)  # replace with the query embedding
dist, ind = tree.query([query_embedding], k=1)
print(f"Closest article index: {ind[0][0]}, Distance: {dist[0][0]}")


'''
