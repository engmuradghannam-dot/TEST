"""RAG Memory backed by ChromaDB.

Stores per-company document chunks with embeddings and retrieves
relevant context for AI operations. Falls back to an in-process
store when chromadb is not installed (dev environments).
"""
import hashlib
import logging

logger = logging.getLogger(__name__)

try:
    import chromadb
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False


class RAGMemory:
    def __init__(self, persist_dir: str = "/var/lib/nexus/chroma"):
        if HAS_CHROMA:
            self._client = chromadb.PersistentClient(path=persist_dir)
        else:
            logger.warning("chromadb not installed - using in-memory fallback store")
            self._fallback: dict[str, list[dict]] = {}

    def _collection_name(self, company_id: int) -> str:
        return f"company_{company_id}_memory"

    def add(self, company_id: int, text: str, metadata: dict | None = None) -> str:
        doc_id = hashlib.sha256(f"{company_id}:{text}".encode()).hexdigest()[:24]
        metadata = {**(metadata or {}), "company_id": str(company_id)}
        if HAS_CHROMA:
            col = self._client.get_or_create_collection(self._collection_name(company_id))
            col.upsert(ids=[doc_id], documents=[text], metadatas=[metadata])
        else:
            self._fallback.setdefault(self._collection_name(company_id), []).append(
                {"id": doc_id, "text": text, "meta": metadata}
            )
        return doc_id

    def query(self, company_id: int, query_text: str, n_results: int = 5) -> list[dict]:
        if HAS_CHROMA:
            col = self._client.get_or_create_collection(self._collection_name(company_id))
            res = col.query(query_texts=[query_text], n_results=n_results)
            out = []
            for i, doc in enumerate(res.get("documents", [[]])[0]):
                out.append({
                    "text": doc,
                    "metadata": res["metadatas"][0][i] if res.get("metadatas") else {},
                    "distance": res["distances"][0][i] if res.get("distances") else None,
                })
            return out
        # naive keyword fallback
        docs = self._fallback.get(self._collection_name(company_id), [])
        terms = set(query_text.lower().split())
        scored = sorted(
            docs,
            key=lambda d: -len(terms & set(d["text"].lower().split())),
        )
        return [{"text": d["text"], "metadata": d["meta"], "distance": None}
                for d in scored[:n_results]]

    def delete_company(self, company_id: int):
        if HAS_CHROMA:
            try:
                self._client.delete_collection(self._collection_name(company_id))
            except Exception:
                pass
        else:
            self._fallback.pop(self._collection_name(company_id), None)
