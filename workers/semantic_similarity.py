from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

_model = SentenceTransformer("all-MiniLM-L6-v2")


def calculate_semantic_similarity(reference: str, candidate: str) -> float:
    """
    Returns semantic similarity score between 0.0 and 1.0
    """

    if not reference or not candidate:
        return 0.0

    embeddings = _model.encode([reference, candidate], convert_to_numpy=True)

    similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

    return round(float(similarity), 4)
