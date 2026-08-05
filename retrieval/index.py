import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

documents = []
embeddings = []
index = None


def build_index(texts):
    global documents
    global embeddings
    global index

    documents = texts
    embeddings = model.encode(texts)

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings).astype("float32"))


def retrieve(query, top_k=3):
    global index
    global documents

    if index is None:
        raise ValueError("Index has not been built. Call build_index() first.")

    query_embedding = model.encode([query])

    _distances, ids = index.search(np.array(query_embedding).astype("float32"), top_k)

    results = []

    for i in ids[0]:
        if i != -1:
            results.append(documents[i])

    return results
