"""Document ingestion and processing for RAG."""

import os
import uuid
from pathlib import Path
from typing import List, Optional

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pypdf import PdfReader


class DocumentIngestion:
    """Handles document ingestion, parsing, and chunking."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )
    
    def parse_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    
    def parse_text_file(self, file_path: str) -> str:
        """Extract text from text file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def ingest_document(
        self,
        file_path: str,
        document_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> List[Document]:
        """
        Ingest a document and return chunked Documents with metadata.
        
        Args:
            file_path: Path to the document
            document_type: Type of document (e.g., 'safety_manual', 'contract')
            metadata: Additional metadata to attach
            
        Returns:
            List of Document chunks
        """
        file_path = Path(file_path)
        
        # Parse document based on type
        if file_path.suffix.lower() == '.pdf':
            text = self.parse_pdf(str(file_path))
        else:
            text = self.parse_text_file(str(file_path))
        
        # Create base metadata
        base_metadata = {
            "source": str(file_path),
            "filename": file_path.name,
            "document_type": document_type or "unknown",
            "document_id": str(uuid.uuid4()),
        }
        
        if metadata:
            base_metadata.update(metadata)
        
        # Split into chunks
        chunks = self.text_splitter.create_documents(
            texts=[text],
            metadatas=[base_metadata]
        )
        
        # Add chunk indices for citations
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i
            chunk.metadata["total_chunks"] = len(chunks)
        
        return chunks
    
    def ingest_directory(
        self,
        directory: str,
        document_type: Optional[str] = None,
        pattern: str = "*",
    ) -> List[Document]:
        """
        Ingest all matching files from a directory.
        
        Args:
            directory: Directory path
            document_type: Type of documents
            pattern: File pattern to match (e.g., '*.pdf')
            
        Returns:
            List of all Document chunks
        """
        directory = Path(directory)
        all_chunks = []
        
        for file_path in directory.glob(pattern):
            if file_path.is_file():
                try:
                    chunks = self.ingest_document(
                        str(file_path),
                        document_type=document_type,
                    )
                    all_chunks.extend(chunks)
                except Exception as e:
                    print(f"Error ingesting {file_path}: {e}")
        
        return all_chunks
