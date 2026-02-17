"""Main Compliance Agent - Operational Risk & Compliance Agent."""

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from ..rag import ComplianceRetriever, DocumentIngestion, DocumentStore
from ..memory import MemoryManager, MemoryType
from ..weather import OpenMeteoClient, WeatherSandbox


@dataclass
class SafetyDecision:
    """Result of a safety compliance check."""
    
    query: str
    site_location: Optional[str]
    operation_type: str
    
    # RAG Results
    relevant_rules: List[Dict] = field(default_factory=list)
    rules_context: str = ""
    
    # Weather Results
    weather_compliance: Optional[Dict] = None
    current_conditions: Optional[Dict] = None
    
    # Memory Context
    user_memory_context: str = ""
    company_memory_context: str = ""
    
    # Decision
    can_proceed: bool = False
    reasoning: str = ""
    recommendations: List[str] = field(default_factory=list)
    citations: List[Dict] = field(default_factory=list)
    
    # Meta
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    new_memories: List[Dict] = field(default_factory=list)


class ComplianceAgent:
    """
    Operational Risk & Compliance Agent.
    
    Combines:
    - RAG: Retrieves safety rules from documents
    - Memory: Recalls site-specific and user-specific information
    - Weather: Checks real-time weather conditions
    
    To make informed safety decisions.
    """
    
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        model: str = "gpt-4o-mini",
    ):
        self.model = model
        self.llm = ChatOpenAI(model=model, temperature=0)
        
        # Initialize components
        self.document_store = DocumentStore(persist_directory=persist_directory)
        self.ingestion = DocumentIngestion()
        self.retriever = ComplianceRetriever(self.document_store, model=model)
        self.memory_manager = MemoryManager()
        self.weather_client = OpenMeteoClient()
        self.weather_sandbox = WeatherSandbox()
    
    def ingest_documents(
        self,
        file_paths: List[str],
        document_type: str = "safety_manual",
    ) -> int:
        """
        Ingest documents into the RAG system.
        
        Args:
            file_paths: List of file paths to ingest
            document_type: Type of documents
            
        Returns:
            Number of chunks ingested
        """
        total_chunks = 0
        
        for file_path in file_paths:
            chunks = self.ingestion.ingest_document(
                file_path=file_path,
                document_type=document_type,
            )
            self.document_store.add_documents(chunks)
            total_chunks += len(chunks)
        
        return total_chunks
    
    def check_site_safety(
        self,
        site_location: str,
        operation_type: str = "outdoor work",
        check_weather: bool = True,
    ) -> SafetyDecision:
        """
        Check if operations are safe at a given site.
        
        This is the main workflow:
        1. Retrieve relevant safety rules from documents (RAG)
        2. Check memory for site-specific issues
        3. Check real-time weather conditions
        4. Combine all information to make a decision
        
        Args:
            site_location: Site name or location (e.g., "Site Alpha, Boston")
            operation_type: Type of operation (e.g., "crane operation")
            check_weather: Whether to check weather conditions
            
        Returns:
            SafetyDecision with complete analysis
        """
        decision = SafetyDecision(
            query=f"Check safety for {operation_type} at {site_location}",
            site_location=site_location,
            operation_type=operation_type,
        )
        
        # Step 1: Retrieve safety rules (RAG)
        print(f"🔍 Searching safety manual for {operation_type} rules...")
        rag_results = self.retriever.find_safety_rules(
            operation=operation_type,
            site_location=site_location,
        )
        decision.relevant_rules = rag_results["documents"]
        decision.rules_context = rag_results["context"]
        decision.citations = rag_results["citations"]
        
        # Step 2: Check memory
        print(f"🧠 Checking memory for {site_location}...")
        decision.user_memory_context = self.memory_manager.get_relevant_context(
            query=f"user {site_location} {operation_type}",
            memory_type=MemoryType.USER,
            max_entries=3,
        )
        decision.company_memory_context = self.memory_manager.get_relevant_context(
            query=f"{site_location} issues problems safety",
            memory_type=MemoryType.COMPANY,
            max_entries=5,
        )
        
        # Step 3: Check weather (if enabled and location can be geocoded)
        weather_compliance = None
        if check_weather:
            print(f"🌤️ Checking weather for {site_location}...")
            location_data = self.weather_client.geocode_location(site_location)
            
            if location_data:
                # Extract thresholds from rules if possible
                wind_threshold = self._extract_wind_threshold(decision.rules_context) or 20.0
                rain_threshold = self._extract_rain_threshold(decision.rules_context) or 5.0
                
                weather_compliance = self.weather_sandbox.check_safety_compliance(
                    latitude=location_data["latitude"],
                    longitude=location_data["longitude"],
                    wind_threshold=wind_threshold,
                    rain_threshold=rain_threshold,
                )
                decision.weather_compliance = weather_compliance
                
                # Get current conditions for display
                decision.current_conditions = self.weather_client.get_current_weather(
                    latitude=location_data["latitude"],
                    longitude=location_data["longitude"],
                )
        
        # Step 4: Make decision using LLM
        print("🤔 Analyzing compliance...")
        decision = self._make_safety_decision(decision)
        
        # Step 5: Update memory with this interaction
        print("💾 Updating memory...")
        self._update_memory(decision)
        
        return decision
    
    def _extract_wind_threshold(self, rules_context: str) -> Optional[float]:
        """Extract wind speed threshold from rules text."""
        # Look for patterns like "wind speed exceed 20 mph" or "wind > 30 km/h"
        patterns = [
            r'wind\s+(?:speed\s+)?(?:exceed|greater than|>|above)\s+(\d+(?:\.\d+)?)\s*(?:mph|km/h|kmh)',
            r'wind\s+(?:speed\s+)?(?:limit|threshold|maximum)\s+(?:of\s+)?(\d+(?:\.\d+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, rules_context.lower())
            if match:
                speed = float(match.group(1))
                # Convert mph to km/h if needed
                if 'mph' in rules_context.lower():
                    speed = speed * 1.60934
                return speed
        
        return None
    
    def _extract_rain_threshold(self, rules_context: str) -> Optional[float]:
        """Extract rainfall threshold from rules text."""
        patterns = [
            r'rain(?:fall)?\s+(?:exceed|greater than|>|above)\s+(\d+(?:\.\d+)?)\s*mm',
            r'precipitation\s+(?:exceed|greater than|>|above)\s+(\d+(?:\.\d+)?)\s*mm',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, rules_context.lower())
            if match:
                return float(match.group(1))
        
        return None
    
    def _make_safety_decision(self, decision: SafetyDecision) -> SafetyDecision:
        """Use LLM to make final safety decision."""
        system_prompt = """You are an Operational Risk & Compliance Agent.
Your job is to analyze safety rules, weather conditions, and site memory to make safety recommendations.

Analyze the provided information and determine:
1. Can the operation proceed safely?
2. What are the specific risks?
3. What recommendations should be made?

Respond in JSON format:
{
    "can_proceed": true/false,
    "reasoning": "Detailed explanation of the decision",
    "recommendations": ["Specific action items"],
    "risk_level": "LOW/MEDIUM/HIGH/CRITICAL"
}"""

        # Build context
        context_parts = []
        
        if decision.rules_context:
            context_parts.append("SAFETY RULES FROM DOCUMENTS:\n" + decision.rules_context)
        
        if decision.user_memory_context:
            context_parts.append("\nUSER MEMORY:\n" + decision.user_memory_context)
        
        if decision.company_memory_context:
            context_parts.append("\nCOMPANY MEMORY:\n" + decision.company_memory_context)
        
        if decision.weather_compliance:
            weather = decision.weather_compliance
            context_parts.append(f"\nWEATHER COMPLIANCE CHECK:\n")
            context_parts.append(f"Status: {weather['compliance_status']}")
            context_parts.append(f"Recommendation: {weather['recommendation']}")
            if weather['violations']:
                context_parts.append("Violations:")
                for v in weather['violations']:
                    context_parts.append(f"  - {v['date']}: {', '.join(v['issues'])}")
        
        context = "\n".join(context_parts)
        
        user_message = f"""Operation: {decision.operation_type}
Site: {decision.site_location}

{context}

Based on the above information, can this operation proceed safely?"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]
        
        try:
            response = self.llm.invoke(messages)
            
            # Parse JSON response
            result = json.loads(response.content)
            
            decision.can_proceed = result.get("can_proceed", False)
            decision.reasoning = result.get("reasoning", "")
            decision.recommendations = result.get("recommendations", [])
            
        except json.JSONDecodeError:
            # Fallback decision
            if decision.weather_compliance and decision.weather_compliance["compliance_status"] == "VIOLATION":
                decision.can_proceed = False
                decision.reasoning = "Weather conditions violate safety thresholds."
                decision.recommendations = ["Postpone outdoor work due to weather conditions."]
            else:
                decision.can_proceed = True
                decision.reasoning = "No clear violations detected."
        
        return decision
    
    def _update_memory(self, decision: SafetyDecision) -> None:
        """Update memory based on the decision."""
        # Add company memory for safety violations
        if decision.weather_compliance and decision.weather_compliance["violations"]:
            memory_text = f"Safety pause at {decision.site_location} due to weather violations"
            
            from ..memory.models import MemoryEntry
            entry = MemoryEntry(
                content=memory_text,
                category="safety",
                source="compliance_check",
            )
            
            self.memory_manager.write_memory(entry, MemoryType.COMPANY)
            
            decision.new_memories.append({
                "type": "company",
                "content": memory_text,
            })
        
        # Add user memory for site location
        if decision.site_location:
            memory_text = f"Manages operations at {decision.site_location}"
            
            from ..memory.models import MemoryEntry
            entry = MemoryEntry(
                content=memory_text,
                category="location",
                source="compliance_check",
            )
            
            self.memory_manager.write_memory(entry, MemoryType.USER)
            
            decision.new_memories.append({
                "type": "user",
                "content": memory_text,
            })
    
    def ask_question(
        self,
        question: str,
        site_location: Optional[str] = None,
    ) -> Dict:
        """
        Ask a general question about compliance/safety.
        
        Args:
            question: The question to ask
            site_location: Optional site context
            
        Returns:
            Dict with answer and citations
        """
        # Retrieve relevant documents
        rag_results = self.retriever.retrieve_with_citations(
            query=question,
            k=5,
        )
        
        # Get memory context
        memory_context = ""
        if site_location:
            memory_context = self.memory_manager.get_relevant_context(
                query=f"{site_location} {question}",
                max_entries=3,
            )
        
        # Build prompt
        system_prompt = """You are a compliance assistant. Answer the user's question based on the provided documentation.
Always cite your sources using the citation numbers provided in the context.

If the information isn't in the context, say so clearly."""

        context = rag_results["context"]
        if memory_context:
            context = f"MEMORY CONTEXT:\n{memory_context}\n\nDOCUMENTS:\n{context}"
        
        user_message = f"""Context:
{context}

Question: {question}

Provide a clear answer with citations."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]
        
        response = self.llm.invoke(messages)
        
        return {
            "answer": response.content,
            "citations": rag_results["citations"],
            "context_used": bool(rag_results["documents"]),
        }
    
    def get_stats(self) -> Dict:
        """Get system statistics."""
        return {
            "documents": self.document_store.get_collection_stats(),
        }
