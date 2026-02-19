"""LLM Factory - Centralized LLM and Embedding initialization.

This module provides factory functions for creating LLM and embedding instances,
reducing code duplication and making it easier to switch models.
"""

import os
from typing import Optional

from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings

# Load environment variables
load_dotenv()


class LLMFactory:
    """Factory for creating LLM and Embedding instances."""
    
    @staticmethod
    def create_llm(
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> ChatNVIDIA:
        """Create a ChatNVIDIA LLM instance.
        
        Args:
            model: Model name (defaults to NVIDIA_MODEL env var)
            temperature: Temperature (defaults to LLM_TEMPERATURE env var)
            max_tokens: Max tokens (defaults to LLM_MAX_TOKENS env var)
            
        Returns:
            ChatNVIDIA instance
        """
        return ChatNVIDIA(
            model=model or os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct"),
            temperature=temperature or float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=max_tokens or int(os.getenv("LLM_MAX_TOKENS", "16384")),
            base_url=os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"),
        )
    
    @staticmethod
    def create_embeddings(
        model: Optional[str] = None,
    ) -> NVIDIAEmbeddings:
        """Create a NVIDIAEmbeddings instance.
        
        Args:
            model: Model name (defaults to EMBEDDING_MODEL env var)
            
        Returns:
            NVIDIAEmbeddings instance
        """
        embedding_api_key = os.getenv("EMBEDDING_API_KEY") or os.getenv("NVIDIA_API_KEY")
        
        return NVIDIAEmbeddings(
            model=model or os.getenv("EMBEDDING_MODEL", "nvidia/llama-3.2-nv-embedqa-1b-v2"),
            nvidia_api_key=embedding_api_key,
            base_url="https://integrate.api.nvidia.com/v1",
            truncate="END",
        )
    
    @staticmethod
    def get_api_key() -> str:
        """Get the NVIDIA API key from environment.
        
        Returns:
            API key string
            
        Raises:
            ValueError: If API key is not set
        """
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            raise ValueError("NVIDIA_API_KEY not found in environment")
        return api_key
