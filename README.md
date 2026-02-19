# Codex: Operational Risk & Compliance Agent

**AI-Powered Decision Support for Safety-Critical Operations**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

---

## Executive Summary

Codex is an agentic AI system that bridges the gap between static compliance documentation and real-time operational conditions. Built for construction, logistics, and field services, it automates safety decision-making by integrating document intelligence, persistent memory, and environmental data.

**Key Capabilities:**
- **Document Intelligence**: Retrieves specific safety rules with source citations from uploaded manuals
- **Persistent Memory**: Maintains institutional knowledge across sessions and personnel changes
- **Environmental Integration**: Validates operations against real-time weather conditions

---

## The Problem

Safety-critical industries face a critical disconnect:

1. **Static Documentation**: Hundreds of pages of safety protocols, equipment specifications, and site requirements
2. **Dynamic Environment**: Constantly changing weather, site conditions, and operational factors
3. **Knowledge Gaps**: Manual cross-referencing leads to delays, oversights, and safety violations

**Business Impact:**
- Delayed operations due to manual safety reviews
- Equipment damage from weather-related incidents
- Compliance violations and associated penalties
- Knowledge loss during personnel transitions

---

## The Solution

Codex creates an autonomous decision loop that connects documentation, memory, and real-time data:

### 1. Intelligent Document Retrieval (RAG)
Upload safety manuals and protocols. Query natural language questions. Receive specific rules with source citations.

**Example:**  
*Input:* "Can we operate cranes today?"  
*Output:* "Wind speed limit: 20 mph [Source: OSHA3146_Crane_Safety.pdf, Relevance: 0.92]"

### 2. Persistent Organizational Memory
Automatically captures and recalls high-signal operational knowledge:

- **USER_MEMORY.md**: User-specific context (roles, preferences, managed sites)
- **COMPANY_MEMORY.md**: Organizational learnings (site issues, recurring problems)

### 3. Environmental Validation
Integrates with Open-Meteo API to validate operations against current and forecasted conditions.

**Example:**  
System detects wind speeds of 25 mph → Cross-references with crane safety rules → Recommends operation suspension

---

## Demo Scenario

```
User Request: "Check Site Alpha for crane operations"

System Response:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Document Analysis
   Rule Found: "Crane operations prohibited when wind > 20 mph"
   Source: [1] OSHA3146_Crane_Safety.pdf (Relevance: 0.89)

🌤️ Environmental Check
   Current Wind: 25 mph (EXCEEDS LIMIT)
   Forecast: 10mm precipitation expected

🧠 Memory Context
   Note: Site Alpha has active roof leak (reported 2024-01-15)

⚠️  DECISION: OPERATION NOT RECOMMENDED
   
   Reasoning: Multiple safety threshold violations detected.
   • Wind speed (25 mph) exceeds 20 mph operational limit
   • Precipitation forecast indicates unsafe conditions
   • Site-specific hazards (roof leak) compound risk

💡 Recommended Actions:
   1. Postpone crane operations until winds decrease
   2. Schedule roof inspection post-weather event
   3. Resume operations when conditions meet all thresholds

💾 Knowledge Capture: Safety pause logged to organizational memory
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Participant Information

| Field | Details |
|-------|---------|
| **Name** | Thoma Glads Choppala |
| **Email** | this.thoma@gmail.com |
| **GitHub** | [@thomaglads](https://github.com/thomaglads) |

---

## Quick Start

### Prerequisites

- Python 3.9 or higher
- NVIDIA API key (obtain from [build.nvidia.com](https://build.nvidia.com/))

### Installation

```bash
# Clone repository
git clone https://github.com/Community-Dreams-Foundation/agentic-rag-chatbot-thomaglads
cd agentic-rag-chatbot-thomaglads

# Install dependencies
make install

# Configure environment
cp .env.example .env
# Edit .env and add: NVIDIA_API_KEY=your_key_here
```

### Running the Application

**Web Interface (Recommended):**
```bash
make ui
# Access at: http://localhost:8501
```

**Command Line Interface:**
```bash
# Ingest documents
python -m src.ui.cli ingest sample_docs/*.txt

# Run safety check
python -m src.ui.cli check --site "Boston" --operation "crane operation"

# Interactive mode
python -m src.ui.cli demo
```

---

## Video Walkthrough

**[▶️ Watch Demo on YouTube](https://youtu.be/qFhx0KbB_9Q)** *(Demo walkthrough)*

*Demonstrates:*
- End-to-end safety compliance workflow
- Document upload and RAG with citations
- Memory system (USER_MEMORY.md, COMPANY_MEMORY.md)
- Weather integration and decision logic
- Architecture and design decisions

---

## System Architecture

### Data Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Document   │────▶│     RAG      │────▶│  Retrieved   │
│    Store     │     │   Pipeline   │     │    Rules     │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
┌──────────────┐     ┌──────────────┐            │
│   Weather    │────▶│   Agent      │◄───────────┘
│     API      │     │ Orchestrator │
└──────────────┘     └──────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │  Safety  │  │ Memory   │  │  User    │
        │ Decision │  │ Updates  │  │ Response │
        └──────────┘  └──────────┘  └──────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Language** | Python 3.9+ | Core runtime |
| **LLM** | Kimi K2.5 (NVIDIA NIM) | Natural language processing |
| **Embeddings** | NVIDIA llama-3.2-nv-embedqa-1b-v2 | Document vectorization |
| **Vector Store** | ChromaDB | Document retrieval |
| **RAG Framework** | LangChain + LlamaIndex | Retrieval augmentation |
| **UI** | Streamlit | Web interface |
| **Weather Data** | Open-Meteo API | Environmental conditions |

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design documentation.

---

## Features

### Feature A: RAG with Citations ✅

- [x] PDF and text document ingestion
- [x] Semantic chunking with metadata preservation
- [x] Vector storage and similarity search
- [x] Source citations with relevance scores
- [x] Grounded responses from uploaded content

### Feature B: Persistent Memory ✅

- [x] User-specific memory (USER_MEMORY.md)
- [x] Organizational memory (COMPANY_MEMORY.md)
- [x] LLM-based selective storage (confidence ≥0.7)
- [x] Duplicate detection and prevention
- [x] Memory-aware response generation

### Feature C: Environmental Validation ✅

- [x] Open-Meteo API integration (no API key)
- [x] Location geocoding
- [x] Automated threshold extraction
- [x] Safe execution sandbox (AST validation)
- [x] Multi-day forecast analysis

---

## Project Structure

```
codex/
├── src/
│   ├── agent/
│   │   └── compliance_agent.py      # Main orchestration
│   ├── rag/
│   │   ├── ingestion.py             # Document processing
│   │   ├── document_store.py        # ChromaDB wrapper
│   │   └── retriever.py             # RAG with citations
│   ├── memory/
│   │   ├── models.py                # Memory data structures
│   │   └── manager.py               # Memory operations
│   ├── weather/
│   │   ├── client.py                # Open-Meteo client
│   │   └── sandbox.py               # Safe analysis
│   └── ui/
│       ├── cli.py                   # Command-line interface
│       └── app.py                   # Streamlit web app
├── sample_docs/                     # Test documents
├── scripts/
│   └── sanity_check.py              # Validation script
├── artifacts/                       # Generated outputs
├── USER_MEMORY.md                   # Runtime user memory
├── COMPANY_MEMORY.md                # Runtime company memory
├── ARCHITECTURE.md                  # Technical documentation
├── EVAL_QUESTIONS.md                # Test scenarios
├── Makefile                         # Build automation
└── pyproject.toml                   # Dependencies
```

---

## Evaluation

### Automated Testing

```bash
# Run sanity check (required for judging)
make sanity
# Generates: artifacts/sanity_output.json

# Full test suite
make test

# Code quality
make format
make lint
```

### Manual Validation

```bash
# 1. Ingest sample documents
python -m src.ui.cli ingest sample_docs/*.txt

# 2. Execute safety check
python -m src.ui.cli check --site "Boston" --operation "crane"

# 3. Verify memory persistence
ls -la USER_MEMORY.md COMPANY_MEMORY.md

# 4. Check validation output
ls -la artifacts/sanity_output.json
```

See [EVAL_QUESTIONS.md](EVAL_QUESTIONS.md) for comprehensive test scenarios.

---

## Design Decisions

### 1. Cloud LLM vs. Local Models
**Decision:** NVIDIA-hosted Kimi K2.5  
**Rationale:** Optimal quality-speed-cost balance  
**Trade-off:** Requires API key vs. local deployment complexity

### 2. Local vs. Cloud Vector Store
**Decision:** ChromaDB (local)  
**Rationale:** Zero external dependencies, fast retrieval  
**Trade-off:** Single-node vs. distributed scalability

### 3. File vs. Database Memory
**Decision:** Markdown files  
**Rationale:** Human-readable, version-control friendly  
**Trade-off:** Simplicity vs. relational query capabilities

### 4. Streamlit vs. Custom Frontend
**Decision:** Streamlit  
**Rationale:** Rapid development, minimal boilerplate  
**Trade-off:** Development speed vs. customization depth

---

## Roadmap

- [ ] Multi-user authentication and access control
- [ ] Real-time weather alerts via webhook integration
- [ ] Mobile application for field operations
- [ ] Project management tool integrations (Procore, Autodesk)
- [ ] Historical trend analysis and reporting
- [ ] Computer vision for site inspections
- [ ] Voice interface for hands-free operation

---

## Security

- **Prompt Injection Protection**: RAG context isolated from user input
- **Sandbox Isolation**: AST-based code validation for safe execution
- **Data Protection**: No storage of secrets or PII; confidence-based filtering
- **API Security**: Environment-only key management; no sensitive data logging

---

## Acknowledgments

Developed for the **Agentic RAG Chatbot Hackathon** (Community Dreams Foundation)

**Technologies:**
- NVIDIA AI for LLM and embedding services
- Open-Meteo for weather data
- LangChain and LlamaIndex for RAG infrastructure
- ChromaDB for vector storage

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

**Developed by Thoma Glads Choppala**  
*Operational Risk & Compliance Agent*
