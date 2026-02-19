"""Interface protocols for Codex - enables dependency inversion and swappable components."""

from .protocols import LLMProtocol, MemoryStoreProtocol, RetrieverProtocol, WeatherProtocol

__all__ = [
    "RetrieverProtocol",
    "MemoryStoreProtocol",
    "LLMProtocol",
    "WeatherProtocol",
]
