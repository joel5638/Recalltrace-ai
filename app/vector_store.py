"""Persistent Qdrant evidence collection, optional cross-encoder reranking."""
import os
from .data import DOCUMENTS, LOTS

def client():
    from qdrant_client import QdrantClient
    url=os.getenv("QDRANT_URL")
    return QdrantClient(url=url, api_key=os.getenv("QDRANT_API_KEY")) if url else QdrantClient(path=os.getenv("QDRANT_PATH",".qdrant"))

def model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(os.getenv("RECALLTRACE_EMBEDDING_MODEL","sentence-transformers/all-MiniLM-L6-v2"))

def index_documents():
    from qdrant_client.models import Distance, VectorParams, PointStruct
    import uuid
    m=model(); c=client(); collection="recalltrace_evidence"
    texts=[v["title"]+" "+v["text"] for v in DOCUMENTS.values()]
    embeddings=m.encode(texts,normalize_embeddings=True).tolist()
    if not c.collection_exists(collection):c.create_collection(collection,vectors_config=VectorParams(size=len(embeddings[0]),distance=Distance.COSINE))
    points=[PointStruct(id=str(uuid.uuid5(uuid.NAMESPACE_DNS,key)),vector=embeddings[i],payload={"id":key,**doc}) for i,(key,doc) in enumerate(DOCUMENTS.items())]
    c.upsert(collection,points=points,wait=True)
    return len(points)

def search(query,lot=None,k=5):
    c=client(); m=model(); ids=set(LOTS[lot]["evidence"]) if lot in LOTS else None
    hits=c.query_points(collection_name="recalltrace_evidence",query=m.encode(query,normalize_embeddings=True).tolist(),limit=25).points
    results=[{"id":h.payload["id"],"title":h.payload["title"],"text":h.payload["text"],"score":h.score} for h in hits if ids is None or h.payload["id"] in ids]
    if os.getenv("RECALLTRACE_RERANKER") and results:
        from sentence_transformers import CrossEncoder
        ranker=CrossEncoder(os.getenv("RECALLTRACE_RERANKER"))
        scores=ranker.predict([(query,x["title"]+" "+x["text"]) for x in results])
        for item,score in zip(results,scores):item["rerank_score"]=float(score)
        results.sort(key=lambda x:-x["rerank_score"])
    return results[:k]
