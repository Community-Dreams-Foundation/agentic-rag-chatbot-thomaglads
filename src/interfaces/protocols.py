"""
Abstract protocols for Codex components.

Using typing.Protocol (structural subtyping) means existing classes
automatically satisfy these interfaces without any changes — pure duck typing.
This enables dependency inversion: high-level modules depend on abstractions,
not concrete implementations.

Example: Swap ChromaDB for Pinecone by creating a new class that satisfies
RetrieverProtocol — zero changes to ComplianceAgent.
"""

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from src.memory.models import MemoryEntry, MemoryType


@runtime_checkable
class RetrieverProtocol(Protocol):
    """
    Contract for document retrieval systems.
    Satisfied by: ComplianceRetriever (LangChain), LlamaQueryEngine (LlamaIndex)
    """

    def retrieve_with_citations(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[dict] = None,
    ) -> Dict:
        """Retrieve documents and return with citation metadata."""
        ...


@runtime_checkable
class MemoryStoreProtocol(Protocol):
    """
    Contract for persistent memory systems.
    Satisfied by: MemoryManager (Markdown files)
    Future: Could be satisfied by SQLiteMemory, RedisMemory, etc.
    """

    def read_memories(
        self,
        memory_type: MemoryType,
        limit: Optional[int] = None,
    ) -> List[MemoryEntry]:
        """Read stored memories of a given type."""
        ...

    def write_memory(
        self,
        entry: MemoryEntry,
        memory_type: MemoryType,
    ) -> None:
        """Persist a new memory entry."""
        ...

    def get_relevant_context(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 5,
    ) -> str:
        """Retrieve contextually relevant memories as a formatted string."""
        ...


@runtime_checkable
class LLMProtocol(Protocol):
    """
    Contract for language model providers.
    Satisfied by: ChatNVIDIA (NVIDIA NIM), ChatOpenAI, ChatOllama, etc.
    """

    def invoke(self, messages: List[Any]) -> Any:
        """Invoke the LLM with a list of messages."""
        ...


@runtime_checkable
class WeatherProtocol(Protocol):
    """
    Contract for weather data providers.
    Satisfied by: OpenMeteoClient (free, no key)
    Future: Could be satisfied by WeatherAPIClient, NOAAClient, etc.
    """

    def get_weather_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
    ) -> Dict:
        """Fetch weather forecast for given coordinates."""
        ...
