"""Memory data models."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """Types of memory entries."""
    USER = "user"
    COMPANY = "company"


class MemoryEntry(BaseModel):
    """A single memory entry."""
    
    timestamp: datetime = Field(default_factory=datetime.now)
    content: str = Field(..., description="The memory content")
    category: str = Field(..., description="Category of memory (e.g., 'preference', 'fact', 'issue')")
    source: str = Field(..., description="Source of the memory (e.g., 'conversation', 'document')")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score")
    
    def to_markdown(self) -> str:
        """Convert to markdown format."""
        return f"- [{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {self.content}"


class MemoryDecision(BaseModel):
    """Decision on whether to write to memory."""
    
    should_write: bool = Field(..., description="Whether to write this memory")
    memory_type: MemoryType = Field(..., description="Type of memory (user or company)")
    content: str = Field(..., description="Cleaned memory content to write")
    category: str = Field(..., description="Memory category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in this memory")
    reasoning: str = Field(..., description="Why this memory should or shouldn't be written")
