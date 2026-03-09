"""
embeddings/vector_store.py
Generate embeddings and manage FAISS + ChromaDB vector stores.
"""
import os
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# EMBEDDER
# ─────────────────────────────────────────────────────────────────────────────
class EVEmbedder:
    """
    Generates embeddings using sentence-transformers.
    Default: all-MiniLM-L6-v2 (384-dim, free, fast, no API key needed)
    """

    RECOMMENDED_MODELS = {
        "fast":    "all-MiniLM-L6-v2",        # 384-dim — best for Colab free tier
        "quality": "all-mpnet-base-v2",         # 768-dim — better quality
        "multilingual": "paraphrase-multilingual-MiniLM-L12-v2",  # 50 languages
    }

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading embedding model: {model_name}")
        self.model      = SentenceTransformer(model_name)
        self.model_name = model_name
        self.dim        = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model ready — dimension: {self.dim}")

    def embed(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = True,
    ) -> np.ndarray:
        embeddings = self.model.encode(
            texts,
            batch_size           = batch_size,
            show_progress_bar    = show_progress,
            normalize_embeddings = True,
            convert_to_numpy     = True,
        )
        return embeddings.astype(np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        return self.model.encode(
            query,
            normalize_embeddings = True,
            convert_to_numpy     = True,
        ).astype(np.float32)


# ─────────────────────────────────────────────────────────────────────────────
# FAISS STORE
# ─────────────────────────────────────────────────────────────────────────────
class FAISSStore:
    """Lightweight FAISS vector store with metadata storage."""

    def __init__(self, dim: int):
        import faiss
        self.index  = faiss.IndexFlatIP(dim)   # Inner product = cosine for L2-normalised vecs
        self.dim    = dim
        self.chunks : List[dict] = []

    def add(self, embeddings: np.ndarray, chunks: List[dict]):
        self.index.add(embeddings)
        self.chunks.extend(chunks)
        logger.info(f"FAISS: {self.index.ntotal} vectors indexed")

    def search(self, query_vec: np.ndarray, k: int = 5) -> List[dict]:
        q = query_vec.reshape(1, -1)
        scores, idxs = self.index.search(q, k)
        results = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx >= 0:
                results.append({
                    **self.chunks[idx],
                    "score": float(score),
                })
        return results

    def save(self, path: str):
        import faiss
        index_path = f"{path}.index"
        meta_path  = f"{path}_meta.json"
        faiss.write_index(self.index, index_path)
        with open(meta_path, "w") as f:
            json.dump(self.chunks, f)
        logger.info(f"FAISS saved: {index_path}")

    @classmethod
    def load(cls, path: str, dim: int) -> "FAISSStore":
        import faiss
        store        = cls(dim)
        store.index  = faiss.read_index(f"{path}.index")
        with open(f"{path}_meta.json") as f:
            store.chunks = json.load(f)
        logger.info(f"FAISS loaded: {store.index.ntotal} vectors")
        return store


# ─────────────────────────────────────────────────────────────────────────────
# CHROMADB STORE
# ─────────────────────────────────────────────────────────────────────────────
class ChromaStore:
    """
    Persistent ChromaDB vector store.
    Persists to Google Drive when path is set to Drive folder.
    """

    def __init__(self, persist_dir: str, collection_name: str = "ev_manuals"):
        import chromadb
        os.makedirs(persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.col    = self.client.get_or_create_collection(
            name     = collection_name,
            metadata = {"hnsw:space": "cosine"},
        )
        logger.info(f"ChromaDB ready — {self.col.count()} existing docs")

    def add(self, embeddings: np.ndarray, chunks: List[dict],
            batch_size: int = 100):
        if self.col.count() > 0:
            logger.info("ChromaDB already populated — skipping add")
            return

        total = len(chunks)
        for i in range(0, total, batch_size):
            batch_c = chunks[i:i + batch_size]
            batch_e = embeddings[i:i + batch_size]
            self.col.add(
                embeddings = batch_e.tolist(),
                documents  = [c["text"] for c in batch_c],
                metadatas  = [{
                    "doc_id":   c.get("doc_id",   "?"),
                    "brand":    c.get("brand",    "general"),
                    "system":   c.get("system",   "general"),
                    "doc_type": c.get("doc_type", "general"),
                    "year":     str(c.get("year") or ""),
                } for c in batch_c],
                ids = [c["chunk_id"] for c in batch_c],
            )
            logger.info(f"  Added batch {i // batch_size + 1} "
                        f"({self.col.count()}/{total})")
        logger.info(f"ChromaDB populated: {self.col.count()} docs")

    def search(
        self,
        query_vec: np.ndarray,
        k: int = 5,
        brand_filter: Optional[str] = None,
        system_filter: Optional[str] = None,
    ) -> List[dict]:
        where = {}
        if brand_filter:
            where["brand"]  = brand_filter
        if system_filter:
            where["system"] = system_filter

        results = self.col.query(
            query_embeddings = [query_vec.tolist()],
            n_results        = k,
            where            = where if where else None,
        )

        output = []
        for doc, dist, meta, rid in zip(
            results["documents"][0],
            results["distances"][0],
            results["metadatas"][0],
            results["ids"][0],
        ):
            output.append({
                "chunk_id": rid,
                "text":     doc,
                "score":    round(1 - dist, 4),
                **meta,
            })
        return output

    def count(self) -> int:
        return self.col.count()


# ─────────────────────────────────────────────────────────────────────────────
# SEMANTIC SEARCH (combines embedder + ChromaDB)
# ─────────────────────────────────────────────────────────────────────────────
class EVSemanticSearch:
    """High-level semantic search over EV manuals."""

    def __init__(self, embedder: EVEmbedder, chroma: ChromaStore):
        self.embedder = embedder
        self.chroma   = chroma

    def search(
        self,
        query: str,
        k: int = 5,
        brand:  Optional[str] = None,
        system: Optional[str] = None,
        print_results: bool = True,
    ) -> List[dict]:
        q_vec   = self.embedder.embed_query(query)
        results = self.chroma.search(q_vec, k, brand, system)

        if print_results:
            print(f"\n🔍 Query: '{query}'")
            if brand:  print(f"   Filter: brand={brand}")
            if system: print(f"   Filter: system={system}")
            print("-" * 65)
            for r in results:
                print(f"  [{r['score']:.3f}] [{r.get('system','?')}]  "
                      f"{r['text'][:90]}...")

        return results

    def build_context(self, query: str, k: int = 5) -> str:
        results = self.search(query, k, print_results=False)
        return "\n\n---\n\n".join(r["text"] for r in results)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Vector store module — import and use EVSemanticSearch in your pipeline.")
