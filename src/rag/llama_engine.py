"""LlamaIndex-based query engine for conversational document Q&A.

Uses the same ChromaDB collection as LangChain, providing a dual-framework
RAG approach: LangChain for structured safety checks, LlamaIndex for chat.
"""

import os
from typing import Optional

from dotenv import load_dotenv
import chromadb
from ..utils import LLMFactory, logger

# Environment variables should be loaded by the entry point


class LlamaQueryEngine:
    """
    Conversational query engine using LlamaIndex over the shared ChromaDB collection.

    This engine is used for the Chat tab, providing synthesized, conversational
    answers from ingested compliance documents.
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "compliance_docs",
    ):
        self.persist_directory = persist_directory or os.getenv(
            "CHROMA_PERSIST_DIR", "./chroma_db"
        )
        self.collection_name = collection_name
        self._index = None
        self._query_engine = None
        self._initialized = False

    def initialize(self, force: bool = False):
        """Initialize or re-initialize the query engine from the vector store."""
        if self._initialized and not force:
            return

        try:
            from llama_index.core import VectorStoreIndex, Settings
            from llama_index.vector_stores.chroma import ChromaVectorStore
            from llama_index.core import StorageContext

            # Configure LlamaIndex via Factory
            Settings.llm = LLMFactory.create_llm(model=os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct"))
            Settings.embed_model = LLMFactory.create_embeddings()

            # Connect to the same ChromaDB collection as LangChain
            chroma_client = chromadb.PersistentClient(path=self.persist_directory)
            chroma_collection = chroma_client.get_or_create_collection(self.collection_name)

            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)

            # Build index from existing vector store (no re-embedding needed)
            self._index = VectorStoreIndex.from_vector_store(
                vector_store,
                storage_context=storage_context,
            )

            self._query_engine = self._index.as_query_engine(
                similarity_top_k=5,
                response_mode="compact",
            )
            self._initialized = True

        except Exception as e:
            # We don't want to crash the whole app just because LlamaIndex fails
            # ComplianceAgent will handle the fallback
            logger.error(f"LlamaIndex Initialization failed: {e}")
            self._initialized = False

    def refresh(self):
        """Force re-initialization to recognize newly ingested documents."""
        logger.info("Refreshing index for new documents...")
        self.initialize(force=True)

    def query(self, question: str) -> dict:
        """
        Query the document store conversationally.

        Returns:
            dict with 'answer' (str) and 'sources' (list of source node info)
        """
        if not self._initialized:
            self.initialize()

        if self._query_engine is None:
            return {
                "answer": "Query engine not available. Please ingest documents first.",
                "sources": [],
            }

        try:
            response = self._query_engine.query(question)
            sources = []
            if hasattr(response, "source_nodes"):
                for node in response.source_nodes:
                    sources.append({
                        "filename": node.metadata.get("filename", "Unknown"),
                        "score": round(node.score, 3) if node.score else None,
                        "text_preview": node.text[:150] if node.text else "",
                    })

            return {
                "answer": str(response),
                "sources": sources,
            }
        except Exception as e:
            return {
                "answer": f"Query failed: {str(e)}",
                "sources": [],
            }

    def is_ready(self) -> bool:
        """Check if the engine can be initialized (API key present)."""
        return bool(os.getenv("NVIDIA_API_KEY"))
