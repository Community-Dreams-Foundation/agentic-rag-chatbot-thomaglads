"""Memory manager for persistent user and company memory."""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from .models import MemoryDecision, MemoryEntry, MemoryType


class MemoryManager:
    """
    Manages durable memory for users and companies.
    Writes selective, high-signal information to markdown files.
    """
    
    def __init__(
        self,
        user_memory_file: str = "USER_MEMORY.md",
        company_memory_file: str = "COMPANY_MEMORY.md",
        model: str = "gpt-4o-mini",
    ):
        self.user_memory_file = Path(user_memory_file)
        self.company_memory_file = Path(company_memory_file)
        self.llm = ChatOpenAI(model=model, temperature=0)
        
        # Ensure memory files exist
        self._ensure_memory_files_exist()
    
    def _ensure_memory_files_exist(self) -> None:
        """Create memory files if they don't exist."""
        for file_path in [self.user_memory_file, self.company_memory_file]:
            if not file_path.exists():
                file_path.write_text(f"# Memory Log\n\nGenerated: {datetime.now().isoformat()}\n\n")
    
    def _parse_existing_memories(self, file_path: Path) -> List[str]:
        """Parse existing memories to avoid duplicates."""
        if not file_path.exists():
            return []
        
        content = file_path.read_text()
        # Extract memory entries (lines starting with "-")
        memories = []
        for line in content.split('\n'):
            if line.strip().startswith('- ['):
                # Extract just the content part
                match = re.search(r'\] (.+)$', line.strip())
                if match:
                    memories.append(match.group(1).lower())
        return memories
    
    def evaluate_memory(
        self,
        conversation_context: str,
        memory_type: MemoryType,
    ) -> MemoryDecision:
        """
        Evaluate if information should be written to memory.
        
        Uses LLM to decide if information is:
        - High-signal and reusable
        - Selective (not a transcript dump)
        - Worth remembering long-term
        """
        system_prompt = """You are a memory management system for an Operational Risk & Compliance Agent.
        
Your job is to evaluate conversation context and decide if any information should be written to durable memory.

Rules for USER_MEMORY.md (user-specific facts):
- Store user preferences, role, responsibilities
- Store site locations they manage
- Store recurring tasks or workflows
- Store personal safety concerns or restrictions

Rules for COMPANY_MEMORY.md (org-wide learnings):
- Store site-specific issues (e.g., "Site Alpha has a roof leak")
- Store recurring operational problems
- Store cross-team learnings
- Store compliance patterns

CRITICAL RULES:
1. Be SELECTIVE - only high-signal, reusable information
2. NO transcript dumping - extract only key facts
3. Check for duplicates - don't repeat existing memories
4. Confidence must be > 0.7 to write
5. Never store sensitive personal data (SSN, passwords, etc.)
6. Never store secrets or API keys

Respond in JSON format:
{
    "should_write": true/false,
    "content": "Clean, concise memory statement",
    "category": "preference|fact|issue|workflow|location|safety",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of decision"
}"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Memory type: {memory_type.value}\n\nConversation context:\n{conversation_context}")
        ]
        
        response = self.llm.invoke(messages)
        
        # Parse JSON response
        try:
            import json
            result = json.loads(response.content)
            return MemoryDecision(
                should_write=result.get("should_write", False),
                memory_type=memory_type,
                content=result.get("content", ""),
                category=result.get("category", "fact"),
                confidence=result.get("confidence", 0.0),
                reasoning=result.get("reasoning", ""),
            )
        except json.JSONDecodeError:
            # Fallback: assume no memory to write
            return MemoryDecision(
                should_write=False,
                memory_type=memory_type,
                content="",
                category="",
                confidence=0.0,
                reasoning="Failed to parse response",
            )
    
    def write_memory(
        self,
        entry: MemoryEntry,
        memory_type: MemoryType,
    ) -> bool:
        """
        Write a memory entry to the appropriate file.
        
        Returns:
            True if written successfully, False if duplicate or error
        """
        file_path = (
            self.user_memory_file if memory_type == MemoryType.USER
            else self.company_memory_file
        )
        
        # Check for duplicates
        existing = self._parse_existing_memories(file_path)
        if entry.content.lower() in existing:
            return False
        
        # Append to file
        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(entry.to_markdown() + '\n')
            return True
        except Exception as e:
            print(f"Error writing memory: {e}")
            return False
    
    def add_memory_from_conversation(
        self,
        conversation: str,
        memory_type: MemoryType = MemoryType.USER,
    ) -> Optional[MemoryEntry]:
        """
        Evaluate and potentially add memory from conversation.
        
        Returns:
            MemoryEntry if written, None otherwise
        """
        decision = self.evaluate_memory(conversation, memory_type)
        
        if not decision.should_write or decision.confidence < 0.7:
            return None
        
        entry = MemoryEntry(
            content=decision.content,
            category=decision.category,
            source="conversation",
            confidence=decision.confidence,
        )
        
        success = self.write_memory(entry, memory_type)
        return entry if success else None
    
    def read_memories(
        self,
        memory_type: Optional[MemoryType] = None,
        category: Optional[str] = None,
    ) -> List[MemoryEntry]:
        """Read memories from file(s)."""
        entries = []
        
        files_to_read = []
        if memory_type is None or memory_type == MemoryType.USER:
            files_to_read.append((self.user_memory_file, MemoryType.USER))
        if memory_type is None or memory_type == MemoryType.COMPANY:
            files_to_read.append((self.company_memory_file, MemoryType.COMPANY))
        
        for file_path, mem_type in files_to_read:
            if not file_path.exists():
                continue
            
            content = file_path.read_text()
            for line in content.split('\n'):
                if line.strip().startswith('- ['):
                    # Parse line
                    match = re.search(r'\[([^\]]+)\] (.+)$', line.strip())
                    if match:
                        timestamp_str = match.group(1)
                        content_text = match.group(2)
                        
                        try:
                            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M')
                        except ValueError:
                            timestamp = datetime.now()
                        
                        entry = MemoryEntry(
                            timestamp=timestamp,
                            content=content_text,
                            category="stored",
                            source="file",
                        )
                        
                        # Filter by category if specified
                        if category is None or entry.category == category:
                            entries.append(entry)
        
        return entries
    
    def get_relevant_context(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        max_entries: int = 5,
    ) -> str:
        """Get relevant memory context for a query."""
        entries = self.read_memories(memory_type=memory_type)
        
        if not entries:
            return ""
        
        # Simple relevance scoring based on keyword matching
        query_words = set(query.lower().split())
        scored_entries = []
        
        for entry in entries:
            entry_words = set(entry.content.lower().split())
            score = len(query_words & entry_words)
            scored_entries.append((score, entry))
        
        # Sort by relevance and take top entries
        scored_entries.sort(key=lambda x: x[0], reverse=True)
        top_entries = scored_entries[:max_entries]
        
        if not top_entries or top_entries[0][0] == 0:
            return ""
        
        context_parts = []
        for score, entry in top_entries:
            if score > 0:
                context_parts.append(f"- {entry.content}")
        
        return "\n".join(context_parts)
