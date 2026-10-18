import re
from functools import lru_cache

import numpy as np

_KEYWORD_INDEX = "keyword-fallback"


@lru_cache(maxsize=1)
def get_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("all-MiniLM-L6-v2")


def _tokens(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def embed_and_store(texts):
    """Embed texts and store them in a FAISS index.

    If the embedding model / FAISS is unavailable (e.g. offline first run),
    falls back to simple keyword matching so the app still works.
    Returns (index, texts).
    """
    texts = [t for t in texts if t and t.strip()]
    if not texts:
        print("[WARN] No news documents found - retrieval disabled.")
        return None, []

    try:
        import faiss

        vectors = np.asarray(get_model().encode(texts), dtype="float32")
        index = faiss.IndexFlatL2(vectors.shape[1])
        index.add(vectors)
        print(f"Number of embedded documents: {len(texts)}")
        return index, texts
    except Exception as e:
        print(f"[WARN] Embedding model unavailable ({e}); using keyword search fallback.")
        return _KEYWORD_INDEX, texts


def retrieve_top_k(query, index, texts, k=3):
    """Retrieve the top k most similar documents."""
    if not texts or index is None:
        return []
    k = min(k, len(texts))

    if index == _KEYWORD_INDEX:
        q = _tokens(query)
        scored = sorted(range(len(texts)), key=lambda i: -len(q & _tokens(texts[i])))
        return [texts[i] for i in scored[:k]]

    q_vec = np.asarray(get_model().encode([query]), dtype="float32")
    _, I = index.search(q_vec, k)
    return [texts[i] for i in I[0] if 0 <= i < len(texts)]
