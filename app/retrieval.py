"""Hybrid evidence search with deterministic lexical reranking and optional embeddings."""
import math, re, os
from collections import Counter
from .data import DOCUMENTS, LOTS

def tokens(s): return re.findall(r"[a-z0-9]+", s.lower())

def search(query, lot=None, k=5):
    if os.getenv("RECALLTRACE_VECTOR_BACKEND")=="qdrant":
        from .vector_store import search as vector_search
        return vector_search(query,lot,k)
    docs=[]
    ids=LOTS[lot]["evidence"] if lot in LOTS else list(DOCUMENTS)
    for key in ids:
        item=DOCUMENTS[key]
        text=f"{item['title']} {item['text']}"
        docs.append({"id":key,"title":item['title'],"text":item['text'],"search_text":text})
    if not docs:return []
    query_terms=Counter(tokens(query)); corpus=[Counter(tokens(d['search_text'])) for d in docs]
    df=Counter(t for row in corpus for t in row)
    for d,row in zip(docs,corpus):
        d['lexical_score']=sum((1+math.log1p(row.get(t,0)))*math.log(1+(len(docs)+1)/(df[t]+1))*n for t,n in query_terms.items() if t in row)
        d['score']=d['lexical_score']
    if os.getenv('RECALLTRACE_EMBEDDINGS','').lower()=='local':
        try:
            from sentence_transformers import SentenceTransformer
            import numpy as np
            model=SentenceTransformer(os.getenv('RECALLTRACE_EMBEDDING_MODEL','sentence-transformers/all-MiniLM-L6-v2'))
            vectors=model.encode([query]+[d['search_text'] for d in docs],normalize_embeddings=True)
            for i,d in enumerate(docs):d['score']=0.65*float(np.dot(vectors[0],vectors[i+1]))+0.35*d['lexical_score']/(1+d['lexical_score'])
        except (ImportError,OSError,ValueError):pass
    ranked=sorted(docs,key=lambda d:(-d['score'],d['id']))[:k]
    return [{key:d[key] for key in ('id','title','text','score')} for d in ranked]
