import chromadb
from sentence_transformers import SentenceTransformer

_model = None
_client = chromadb.PersistentClient(path="chroma_db")

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def get_collection():
    return _client.get_or_create_collection(name="notes")

def add_chunks(chunks, source):
    collection = get_collection()
    collection.delete(where={"source": source})
    embeddings = get_model().encode(chunks).tolist()
    ids = [f"{source}_{i}" for i in range(len(chunks))]
    metadatas = [{"source": source, "chunk_index": i} for i in range(len(chunks))]
    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return len(chunks)

def search(query, k=3):
    collection = get_collection()
    total = collection.count()
    if total == 0:
        return []
    q_emb = get_model().encode([query]).tolist()
    res = collection.query(query_embeddings=q_emb, n_results=min(k, total))
    results = []
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        results.append({
            "text": doc,
            "source": meta["source"],
            "chunk_index": meta["chunk_index"],
            "distance": dist,
        })
    return results

def list_sources():
    data = get_collection().get(include=["metadatas"])
    counts = {}
    for m in data["metadatas"]:
        counts[m["source"]] = counts.get(m["source"], 0) + 1
    return counts

def delete_source(source):
    get_collection().delete(where={"source": source})

def clear_all():
    try:
        _client.delete_collection("notes")
    except Exception:
        pass

def get_source_chunks(source):
    data = get_collection().get(
        where={"source": source}, include=["documents", "metadatas"]
    )
    pairs = sorted(
        zip(data["metadatas"], data["documents"]),
        key=lambda p: p[0]["chunk_index"],
    )
    return [doc for _, doc in pairs]