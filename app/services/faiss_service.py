import faiss
import numpy as np

index = None

def create_faiss_index(vectors):
    global index
    dimension = vectors.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(vectors, dtype='float32'))

def query_faiss_index(query_vector, top_k=5):
    global index
    query_vector = np.array(query_vector, dtype='float32')
    distances, indices = index.search(query_vector, top_k)
    return indices[0]
