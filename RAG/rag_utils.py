import os
import json
import numpy as np
from google import genai

# Load Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# -----------------------------
# Helper: Load vector store
# -----------------------------
def load_store(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)


# -----------------------------
# Helper: Save vector store
# -----------------------------
def save_store(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


# -----------------------------
# Embed text using Gemini
# -----------------------------
def embed_text(text: str):
    """
    Uses Gemini embeddings.
    Returns list[float].
    """

    result = client.models.embed_content(
        model="text-embedding-004",
        contents=text,
    )

    # Gemini wraps embeddings inside .output_embedding
    return result.output_embedding


# -----------------------------
# Add text to class vector store
# -----------------------------
def add_to_vector_store(class_id: str, text: str):
    """
    Creates or appends to the vector store for a class.
    """

    store_path = os.path.join("upload", class_id, "vs.json")
    os.makedirs(os.path.join("upload", class_id), exist_ok=True)

    store = load_store(store_path)

    embedding = embed_text(text)

    store.append({
        "text": text,
        "embedding": embedding,
    })

    save_store(store_path, store)


# -----------------------------
# Build store from scratch (optional)
# -----------------------------
def build_vector_store(class_id: str, text: str):
    """
    Clears and rebuilds the entire store for a class.
    """

    store_path = os.path.join("upload", class_id, "vs.json")
    os.makedirs(os.path.join("upload", class_id), exist_ok=True)

    embedding = embed_text(text)

    store = [
        {
            "text": text,
            "embedding": embedding,
        }
    ]

    save_store(store_path, store)


# -----------------------------
# Search RAG store using cosine similarity
# -----------------------------
def search_vector_store(class_id: str, query: str):
    """
    Returns the most relevant text chunk for the given query.
    """

    store_path = os.path.join("upload", class_id, "vs.json")
    store = load_store(store_path)

    if not store:
        return None

    query_embedding = embed_text(query)
    query_vec = np.array(query_embedding)

    best_score = -999
    best_text = None

    for item in store:
        vec = np.array(item["embedding"])

        # cosine similarity
        score = np.dot(query_vec, vec) / (
            np.linalg.norm(query_vec) * np.linalg.norm(vec)
        )

        if score > best_score:
            best_score = score
            best_text = item["text"]

    return best_text
