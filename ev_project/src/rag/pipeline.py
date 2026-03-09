"""
rag/pipeline.py
Retrieval Augmented Generation pipeline for EV diagnostics.
"""
import os
import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

EV_SYSTEM_PROMPT = """You are an expert AI assistant specialising in electric vehicle (EV) diagnostics and repair.

You have access to official EV manufacturer manuals, technical service documents, and battery research papers.

GUIDELINES:
- Answer ONLY from the provided context. Do not hallucinate.
- If the answer is not in the context, say: "This information is not in my current knowledge base."
- Always mention specific fault codes (DTC codes) where relevant.
- Structure your answer: Root Cause → Diagnosis Steps → Recommended Action.
- Warn the user if the fault makes the vehicle unsafe to drive.
- Be precise and technical — your users are EV technicians.

CONTEXT FROM EV MANUALS:
{context}

CONVERSATION HISTORY:
{history}

TECHNICIAN QUESTION: {question}

EXPERT ANSWER:"""


class EVRAGPipeline:
    """
    Full RAG pipeline: retrieve context → augment prompt → generate answer.
    Works with OpenAI GPT or free HuggingFace models.
    """

    def __init__(
        self,
        vector_store,           # EVSemanticSearch or compatible
        llm_provider: str = "openai",   # "openai" | "free"
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.1,
        max_tokens: int = 600,
        k_retrieve: int = 5,
    ):
        self.vs          = vector_store
        self.provider    = llm_provider
        self.model       = model_name
        self.temperature = temperature
        self.max_tokens  = max_tokens
        self.k           = k_retrieve
        self.history: List[Dict] = []
        self._llm        = None
        self._init_llm()

    def _init_llm(self):
        if self.provider == "openai":
            try:
                from langchain_openai import ChatOpenAI
                self._llm = ChatOpenAI(
                    model       = self.model,
                    temperature = self.temperature,
                    max_tokens  = self.max_tokens,
                )
                logger.info(f"OpenAI LLM ready: {self.model}")
            except Exception as e:
                logger.warning(f"OpenAI init failed: {e} — falling back to free mode")
                self.provider = "free"

    def _format_history(self) -> str:
        if not self.history:
            return "No previous conversation."
        lines = []
        for turn in self.history[-4:]:   # last 2 full turns
            lines.append(f"Technician: {turn['question']}")
            lines.append(f"AI: {turn['answer'][:200]}...")
        return "\n".join(lines)

    def ask(
        self,
        question: str,
        vehicle_context: Optional[str] = None,
        brand_filter:    Optional[str] = None,
        system_filter:   Optional[str] = None,
        print_answer:    bool = True,
    ) -> dict:
        full_q = f"{vehicle_context} {question}".strip() if vehicle_context else question

        # Retrieve context
        results = self.vs.search(full_q, k=self.k,
                                 brand=brand_filter, system=system_filter,
                                 print_results=False)
        context = "\n\n---\n\n".join(r["text"] for r in results)
        sources = list({r.get("doc_id", "?") for r in results})

        # Build prompt
        prompt  = EV_SYSTEM_PROMPT.format(
            context  = context or "No relevant context found.",
            history  = self._format_history(),
            question = question,
        )

        # Generate answer
        if self.provider == "openai" and self._llm:
            from langchain_core.messages import HumanMessage
            response = self._llm.invoke([HumanMessage(content=prompt)])
            answer   = response.content
        else:
            # Free fallback: return retrieved context with a note
            answer = (
                f"[FREE MODE — Add OpenAI API key for full AI answers]\n\n"
                f"Retrieved {len(results)} relevant passages from EV manuals:\n\n"
            )
            for i, r in enumerate(results, 1):
                answer += f"{i}. [{r.get('system','?')}] {r['text'][:250]}...\n\n"

        # Save to history
        self.history.append({"question": question, "answer": answer,
                             "sources": sources})

        result = {
            "question":  question,
            "answer":    answer,
            "sources":   sources,
            "context_chunks": len(results),
            "mode": self.provider,
        }

        if print_answer:
            print(f"\n{'='*65}")
            print(f"Question: {question}")
            print(f"{'='*65}")
            print(f"\n{answer}")
            print(f"\nSources: {sources}")

        return result

    def clear_history(self):
        self.history = []


class HybridRetriever:
    """
    Combines BM25 keyword search + dense semantic search.
    Weighted combination: score = alpha*dense + (1-alpha)*sparse
    """

    def __init__(self, chunks: List[dict], embedder, alpha: float = 0.7):
        from rank_bm25 import BM25Okapi
        self.chunks   = chunks
        self.embedder = embedder
        self.alpha    = alpha
        corpus        = [c["text"].lower().split() for c in chunks]
        self.bm25     = BM25Okapi(corpus)
        logger.info(f"BM25 index built: {len(chunks)} documents")

    def search(self, query: str, k: int = 5) -> List[dict]:
        import numpy as np

        # BM25 scores
        bm25_scores = np.array(self.bm25.get_scores(query.lower().split()))
        if bm25_scores.max() > 0:
            bm25_scores = bm25_scores / bm25_scores.max()

        # Dense scores
        q_vec = self.embedder.embed_query(query)
        texts = [c["text"] for c in self.chunks]
        dense_vecs = self.embedder.embed(texts, show_progress=False)
        dense_scores = (dense_vecs @ q_vec).flatten()

        # Weighted combination
        combined = self.alpha * dense_scores + (1 - self.alpha) * bm25_scores
        top_idx  = np.argsort(combined)[::-1][:k]

        return [{"score": float(combined[i]), **self.chunks[i]} for i in top_idx]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("RAG pipeline module — use EVRAGPipeline in your notebook.")
