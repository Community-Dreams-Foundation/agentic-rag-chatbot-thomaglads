"""Retriever with citation support for compliance documents."""

import os
from typing import Dict, List, Optional

from langchain_core.documents import Document
from .document_store import DocumentStore
from ..utils import LLMFactory


class ComplianceRetriever:
    """Retriever that finds relevant compliance rules with citations."""
    
    def __init__(
        self,
        document_store: DocumentStore,
        model: str = "meta/llama-3.1-70b-instruct",
    ):
        self.document_store = document_store
        
        # Initialize LLM via Factory
        self.llm = LLMFactory.create_llm(
            model=model,
            temperature=0,
        )
    
    def retrieve_with_citations(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[dict] = None,
    ) -> Dict:
        """
        Retrieve relevant documents and format with citations.
        
        Returns:
            Dict with 'documents', 'context', and 'citations'
        """
        # Retrieve documents
        results = self.document_store.similarity_search_with_score(
            query=query,
            k=k,
            filter_dict=filter_dict,
        )
        
        if not results:
            return {
                "documents": [],
                "context": "No relevant documents found.",
                "citations": [],
            }
        
        # Format documents with citation numbers
        documents = []
        context_parts = []
        citations = []
        
        for i, (doc, score) in enumerate(results, 1):
            documents.append(doc)
            
            # Create citation reference
            source = doc.metadata.get("source", "Unknown")
            filename = doc.metadata.get("filename", "Unknown")
            chunk_idx = doc.metadata.get("chunk_index", 0)
            total_chunks = doc.metadata.get("total_chunks", 1)
            
            citation = {
                "number": i,
                "source": source,
                "filename": filename,
                "chunk_index": chunk_idx,
                "total_chunks": total_chunks,
                "relevance_score": round(float(score), 4),
                "text_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
            }
            citations.append(citation)
            
            # Add to context with citation marker
            context_parts.append(f"[Source {i}] From {filename}:\n{doc.page_content}\n")
        
        context = "\n".join(context_parts)
        
        return {
            "documents": documents,
            "context": context,
            "citations": citations,
        }
    
    def find_safety_rules(
        self,
        operation: str,
        site_location: Optional[str] = None,
    ) -> Dict:
        """
        Specialized retrieval for safety rules.
        
        Args:
            operation: Type of operation (e.g., 'crane operation', 'roof work')
            site_location: Optional site location for context
            
        Returns:
            Retrieved safety rules with citations
        """
        # Construct targeted query
        query_parts = [f"safety rules for {operation}"]
        query_parts.append("wind speed rain weather conditions threshold limit")
        query_parts.append("prohibited restricted requirements safety protocol")
        
        if site_location:
            query_parts.append(f"site location {site_location}")
        
        query = " ".join(query_parts)
        
        return self.retrieve_with_citations(
            query=query,
            k=8,  # Get more results for comprehensive safety check
        )
