import faiss 
import numpy as np

# Example dataset: 10000 vectors of dimension 512
d = 50  # Dimension
n_data = 10  # Number of data points
np.random.seed(1234)  # For reproducibility
db_vectors = np.random.random((n_data, d)).astype('float32')
# Example query vector
query_vector = np.random.random((1, d)).astype('float32')

print(np.linalg.norm(query_vector))
# Normalize the vectors (in-place normalization)
faiss.normalize_L2(db_vectors)
faiss.normalize_L2(query_vector)

d = db_vectors.shape[1]  # Dimension of the vectors

# Create the index
index = faiss.IndexFlatIP(d)

# Add vectors to the index
index.add(db_vectors)

# Perform the search
k = 4  # Number of nearest neighbors to retrieve
D, I = index.search(query_vector, k)  # D is the distance (dot product here), I is the indices of neighbors


'''
# For large-scale search with dot product
quantizer = faiss.IndexFlatIP(d)  # the quantizer
index = faiss.IndexIVFFlat(quantizer, d, number_of_clusters, faiss.METRIC_INNER_PRODUCT)
index.train(db_vectors)  # Only required if the index is not already trained
index.add(db_vectors)

# Now you can search with the index
D, I = index.search(query_vectors, k)
'''