"""Vector document store using ChromaDB."""

import os
from typing import List, Optional

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings


class DocumentStore:
    """Vector store for compliance documents using ChromaDB."""
    
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "compliance_docs",
    ):
        self.persist_directory = persist_directory or os.getenv(
            "CHROMA_PERSIST_DIR", "./chroma_db"
        )
        self.collection_name = collection_name
        
        # Initialize embeddings with NVIDIA NIM
        self.embeddings = NVIDIAEmbeddings(
            model=os.getenv("EMBEDDING_MODEL", "nvidia/llama-3.2-nv-embedqa-1b-v2"),
            truncate="NONE",
            base_url=os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"),
        )
        
        # Initialize vector store
        self.vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory,
        )
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the vector store."""
        if not documents:
            return
        
        # Add to vector store
        self.vector_store.add_documents(documents)
    
    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[dict] = None,
    ) -> List[Document]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            k: Number of results
            filter_dict: Optional metadata filter
            
        Returns:
            List of matching documents
        """
        results = self.vector_store.similarity_search(
            query=query,
            k=k,
            filter=filter_dict,
        )
        return results
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[dict] = None,
    ) -> List[tuple]:
        """
        Search for similar documents with relevance scores.
        
        Returns:
            List of (document, score) tuples
        """
        results = self.vector_store.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter_dict,
        )
        return results
    
    def delete_collection(self) -> None:
        """Delete the entire collection."""
        self.vector_store.delete_collection()
    
    def get_collection_stats(self) -> dict:
        """Get statistics about the collection."""
        collection = self.vector_store._collection
        count = collection.count()
        return {
            "collection_name": self.collection_name,
            "document_count": count,
            "persist_directory": self.persist_directory,
        }
