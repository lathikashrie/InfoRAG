from sentence_transformers import SentenceTransformer
import numpy as np
import pickle

MODEL_NAME = "multi-qa-MiniLM-L6-cos-v1"
model = SentenceTransformer(MODEL_NAME)


def build_index(chunks):
    print(f"Encoding {len(chunks)} chunks...")
    embeddings = model.encode(chunks, show_progress_bar=True, batch_size=64)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    embeddings = embeddings / norms
    print(f"Index built: {len(chunks)} chunks")
    return embeddings, chunks


def search(query, embeddings, chunks, top_k=6):
    query = query.lower().strip()
    q_emb = model.encode([query])[0]
    q_emb = q_emb / (np.linalg.norm(q_emb) + 1e-10)

    scores = np.dot(embeddings, q_emb)

    boosted = []
    for i, chunk in enumerate(chunks):
        score = scores[i]
        if any(word in chunk.lower() for word in query.split()):
            score += 0.15
        boosted.append(score)

    top_indices = np.argsort(boosted)[-top_k:][::-1]
    return [chunks[i] for i in top_indices]


def save_index(index, chunks, path="index.pkl"):
    with open(path, "wb") as f:
        pickle.dump((index, chunks), f)
    print(f"Index saved: {path}")


def load_index(path="index.pkl"):
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception:
        return None, []