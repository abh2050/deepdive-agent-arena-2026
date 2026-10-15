"""Chroma evidence index using deterministic local lexical vectors.
No external embedding API or model is called: all LLM/AI calls remain Mesh-only.
This is a lightweight scaffold retrieval baseline, NOT a semantic embedding model.
"""
import hashlib
import re
from pathlib import Path

DIMENSIONS = 384

def lexical_vector(text: str) -> list[float]:
    values = [0.0] * DIMENSIONS
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        digest = hashlib.sha256(token.encode()).digest()
        slot = int.from_bytes(digest[:4], "big") % DIMENSIONS
        values[slot] += 1.0
    length = sum(x*x for x in values) ** 0.5
    return [x / length for x in values] if length else values

class ChromaEvidenceIndex:
    def __init__(self, path: str = "./data/chroma"):
        import chromadb
        Path(path).mkdir(parents=True, exist_ok=True)
        self.collection = chromadb.PersistentClient(path=path).get_or_create_collection(
            name="deepdive_evidence", metadata={"hnsw:space": "cosine"})

    def add(self, run_id: str, evidence):
        if not evidence:
            return
        self.collection.upsert(
            ids=[f"{run_id}:{item.evidence_id}" for item in evidence],
            documents=[item.excerpt for item in evidence],
            embeddings=[lexical_vector(item.excerpt) for item in evidence],
            metadatas=[{"run_id":run_id,"evidence_id":item.evidence_id,
                        "url":item.url,"subquestion":item.subquestion,
                        "quality":float(item.quality)} for item in evidence],
        )

    def search(self, run_id: str, query: str, limit: int = 5):
        return self.collection.query(query_embeddings=[lexical_vector(query)],
                                     n_results=limit, where={"run_id":run_id})
