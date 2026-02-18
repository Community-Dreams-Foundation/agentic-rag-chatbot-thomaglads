# Codex - Operational Risk & Compliance Agent

[![Review Assignment Due Date](https://camo.githubusercontent.com/fddb80fc6041abdf59514ea69b4629955c7f39ce549e081d6c3059f1f4a33af9/68747470733a2f2f636c617373726f6f6d2e6769746875622e636f6d2f6173736574732f646561646c696e652d726561646d652d627574746f6e2d323230343161666430333430636539363564343761653665663163656665656532386337633439336136333436633466313564363637616239373664353936632e737667)](https://classroom.github.com/a/P5MLsfQv)

> **Winner's Focus**: This isn't just a chatbot—it's an **Operational Risk & Compliance Agent** that bridges the gap between static safety manuals and real-time operational conditions.

## The Problem: The "Disconnected Operations" Gap

In industries like **Logistics, Construction, and Field Services**, managers face a critical disconnect:

1. **Static Compliance**: Hundreds of pages of safety manuals, site protocols, and contract PDFs ("Do not operate Crane X if wind speeds exceed 20mph")
2. **Real-Time Environment**: Constantly changing weather, site conditions, and operational factors

**The Human Failure**: Managers must manually:
- Remember rules from PDFs
- Check weather apps
- Make gut-based decisions
- Write notes so they don't forget

**The Cost**: One missed step = expensive delays, equipment damage, or safety violations.

## The Solution: Codex

Codex creates a single "Agentic" loop that connects these dots automatically:

### Feature A: Bridging the "Knowledge Gap" (RAG)
- **Problem**: Documents too long to read daily
- **Solution**: Upload safety manual → Ask "Can we work today?" → Bot retrieves specific thresholds with page citations

### Feature B: Bridging the "Memory Gap" (Durable Memory)
- **Problem**: Operational knowledge lost when managers change
- **Solution**: 
  - `USER_MEMORY.md`: Remembers you manage "Site Alpha" in Boston
  - `COMPANY_MEMORY.md`: Remembers "Site Alpha has a roof leak"—warns future managers automatically

### Feature C: Bridging the "Reality Gap" (Open-Meteo Integration)
- **Problem**: Knowing the rule is useless without knowing current weather
- **Solution**: Bot sees safety rule → Calls Weather API → Runs calculation → Determines if reality violates the rule

## Demo Scenario

```
User: "Check Site Alpha for today"

Bot: 
🔍 Searching Safety Manual... Found rule: 'No outdoor work if rain > 5mm'
   [Source 1] safety_manual.pdf - Relevance: 0.89

🌤️ Checking Boston weather... 
   Forecast: 10mm rain expected today
   Wind: 25 mph (exceeds 20 mph limit)

🧠 Checking memory... Found: "Site Alpha has roof leak issue"

✅ DECISION: STOP outdoor work
   Reasoning: Weather conditions violate multiple safety thresholds.
   Rainfall (10mm) exceeds 5mm limit. Wind (25 mph) exceeds 20 mph limit.
   
💡 Recommendations:
   • Postpone crane operations until tomorrow
   • Inspect roof leak area after rain stops
   • Resume work when winds drop below 20 mph

💾 Memory: Logged safety pause in COMPANY_MEMORY.md for Site Alpha
```

## Participant Info (Required)

- **Full Name**: [Your Name]
- **Email**: [Your Email]
- **GitHub Username**: [Your GitHub Username]

## Quick Start

### Prerequisites

- Python 3.9+
- NVIDIA API key (get from https://build.nvidia.com/)
  - Kimi K2.5 model access
  - Embeddings model access (llama-3.2-nv-embedqa-1b-v2)

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd codex

# Install dependencies
make install

# Or manually:
pip install -e ".[dev]"

# Set up environment
cp .env.example .env
# Edit .env and add your NVIDIA_API_KEY from https://build.nvidia.com/
```

### Running the Application

**Option 1: Web Interface (Recommended)**
```bash
make ui
# Or: streamlit run src/ui/app.py
# Opens at http://localhost:8501
```

**Option 2: Command Line**
```bash
# Ingest documents
python -m src.ui.cli ingest sample_docs/*.txt

# Check site safety
python -m src.ui.cli check --site "Boston" --operation "crane operation"

# Ask questions
python -m src.ui.cli ask "What are the wind speed limits?"

# Run demo scenarios
python -m src.ui.cli demo
```

## Video Walkthrough

**[PASTE YOUR VIDEO LINK HERE]**

> Record a 5-10 minute walkthrough demonstrating:
> - End-to-end safety check workflow
> - Document upload and RAG with citations
> - Memory system (USER_MEMORY.md and COMPANY_MEMORY.md updates)
> - Weather integration and safety decision logic
> - Your key design choices and tradeoffs

## Architecture Overview

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system design.

### High-Level Flow

```
User Query → RAG (Rules) + Memory (Context) + Weather (Reality)
                    ↓
            Agent Orchestrator
                    ↓
        Safety Decision + Memory Updates
```

### Tech Stack

| Component | Technology |
|-----------|-----------|
| **Language** | Python 3.9+ |
| **LLM** | Kimi K2.5 (via NVIDIA NIM) |
| **Embeddings** | NVIDIA llama-3.2-nv-embedqa-1b-v2 |
| **Vector DB** | ChromaDB (local) |
| **RAG Framework** | LangChain + LlamaIndex |
| **UI** | Streamlit + Streamlit-ShadCN-UI |
| **Weather API** | Open-Meteo (free, no key) |
| **AI Platform** | NVIDIA AI Endpoints |

## Features Implemented

### ✅ Feature A: RAG with Citations

- [x] PDF and text document ingestion
- [x] Semantic chunking with metadata
- [x] Vector storage with ChromaDB
- [x] Similarity search with relevance scores
- [x] Citation format: `[Source N] filename (relevance: X.XX)`
- [x] Contextual responses grounded in documents

### ✅ Feature B: Durable Memory

- [x] `USER_MEMORY.md` - User-specific facts
- [x] `COMPANY_MEMORY.md` - Organization-wide learnings
- [x] LLM-based evaluation (selective, high-signal only)
- [x] Duplicate detection
- [x] Confidence threshold (0.7+)
- [x] Memory-aware responses

### ✅ Feature C: Weather + Safe Compute (Optional)

- [x] Open-Meteo API integration (no API key required)
- [x] Location geocoding
- [x] Safety threshold extraction from documents
- [x] Automated weather compliance checking
- [x] Safe sandbox execution (AST validation)
- [x] Multi-day forecast analysis

## Project Structure

```
codex/
├── src/
│   ├── agent/
│   │   └── compliance_agent.py      # Main orchestrator
│   ├── rag/
│   │   ├── ingestion.py             # Document parsing
│   │   ├── document_store.py        # ChromaDB wrapper
│   │   └── retriever.py             # RAG with citations
│   ├── memory/
│   │   ├── models.py                # Memory data models
│   │   └── manager.py               # Memory I/O
│   ├── weather/
│   │   ├── client.py                # Open-Meteo API
│   │   └── sandbox.py               # Safe analysis
│   └── ui/
│       ├── cli.py                   # Command line
│       └── app.py                   # Streamlit web
├── sample_docs/                     # Test documents
│   ├── sample_safety_manual.txt
│   └── site_protocols.txt
├── scripts/
│   └── sanity_check.py              # Judge validation
├── artifacts/                       # Generated output
├── USER_MEMORY.md                   # User memory (created at runtime)
├── COMPANY_MEMORY.md                # Company memory (created at runtime)
├── ARCHITECTURE.md                  # Detailed design
├── EVAL_QUESTIONS.md                # Test scenarios
├── Makefile                         # Commands
├── pyproject.toml                   # Dependencies
└── README.md                        # This file
```

## Usage Examples

### Example 1: Site Safety Check

```python
from src.agent import ComplianceAgent

agent = ComplianceAgent()

# Ingest documents
agent.ingest_documents(["safety_manual.pdf"])

# Check safety
decision = agent.check_site_safety(
    site_location="Boston",
    operation_type="crane operation"
)

print(f"Can proceed: {decision.can_proceed}")
print(f"Reasoning: {decision.reasoning}")
```

### Example 2: Ask with Citations

```python
result = agent.ask_question("What are the wind speed limits?")

print(result['answer'])
print("\nSources:")
for citation in result['citations']:
    print(f"  [{citation['number']}] {citation['filename']}")
```

### Example 3: Memory-Aware Query

```bash
# User tells bot their role
$ python -m src.ui.cli ask "I manage Site Alpha in Boston"

# Later, new query uses that memory
$ python -m src.ui.cli check --site "Site Alpha"
# Bot already knows location is Boston
```

## Evaluation

### Run Tests

```bash
# Run sanity check (generates artifacts/sanity_output.json)
make sanity

# Run full test suite
make test

# Format and lint
make format
make lint
```

### Manual Testing

See [EVAL_QUESTIONS.md](EVAL_QUESTIONS.md) for comprehensive test scenarios.

Quick validation:

```bash
# 1. Ingest documents
python -m src.ui.cli ingest sample_docs/*.txt

# 2. Check safety (requires OPENAI_API_KEY)
python -m src.ui.cli check --site "Boston" --operation "crane"

# 3. Verify memory files
ls -la USER_MEMORY.md COMPANY_MEMORY.md

# 4. Check artifacts
ls -la artifacts/sanity_output.json
```

## Design Tradeoffs

### 1. OpenAI vs Local Models
**Decision**: Use OpenAI for quality and speed  
**Tradeoff**: Requires API key and incurs cost, but delivers reliable results  
**Alternative**: Local models (Llama, etc.) would be free but slower and less accurate

### 2. ChromaDB vs Pinecone
**Decision**: Local ChromaDB  
**Tradeoff**: No external dependencies, but limited scalability  
**Alternative**: Pinecone/Weaviate would offer better scale but adds complexity

### 3. File-based vs Database Memory
**Decision**: Markdown files for memory  
**Tradeoff**: Human-readable and hackathon-friendly, but less robust than SQL  
**Alternative**: SQLite/PostgreSQL would enable complex queries

### 4. Streamlit vs React
**Decision**: Streamlit for UI  
**Tradeoff**: Fast to build, but limited customization  
**Alternative**: React would offer better UX but requires frontend expertise

## Future Enhancements

- [ ] Multi-user support with authentication
- [ ] Real-time weather alerts via webhooks
- [ ] Mobile app for field access
- [ ] Integration with project management tools (Procore, Autodesk)
- [ ] Historical trend analysis
- [ ] Image-based safety inspections
- [ ] Voice interface for hands-free operation

## Security Considerations

- **Prompt Injection**: RAG context clearly delimited from user input
- **Sandbox Safety**: AST validation prevents malicious code execution
- **Memory Safety**: No storage of secrets/PII; confidence threshold filtering
- **API Security**: Keys via environment only; no logging of sensitive data

## Acknowledgments

Built for the **Agentic RAG Chatbot Hackathon** by Community Dreams Foundation.

Special thanks to:
- OpenAI for GPT-4o-mini API
- Open-Meteo for free weather data
- LangChain for the RAG framework
- ChromaDB for vector storage

## License

MIT License - See LICENSE file for details

---

**Built with ❤️ for safer construction sites**
