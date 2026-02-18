# Architecture Overview - Codex Compliance Agent

## System Architecture

Codex is an **Operational Risk & Compliance Agent** that bridges the gap between static compliance documents and real-time operational conditions. The system combines three core capabilities:

1. **RAG (Retrieval-Augmented Generation)** - Grounded document search with citations
2. **Durable Memory** - Persistent user and organizational knowledge
3. **Weather Intelligence** - Real-time environmental data integration

## High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface                           │
│  (CLI: src/ui/cli.py | Web: src/ui/app.py)                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              ComplianceAgent (Orchestrator)                 │
│  src/agent/compliance_agent.py                              │
│  - Coordinates RAG, Memory, and Weather modules             │
│  - Makes final safety decisions                             │
│  - Updates memory based on interactions                     │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│  RAG System  │  │    Memory    │  │  Weather System  │
│              │  │   Manager    │  │                  │
├──────────────┤  ├──────────────┤  ├──────────────────┤
│• Document    │  │• Evaluate    │  │• Open-Meteo API  │
│  Ingestion   │  │  memories    │  │  Client          │
│• Chunking    │  │• Write to    │  │• Safe Sandbox    │
│• Vector Store│  │  USER_MEMORY │  │  Execution       │
│  (ChromaDB)  │  │  & COMPANY_  │  │• Compliance      │
│• Retrieval   │  │  MEMORY      │  │  Checking        │
│  w/Citations │  │• Read context │  │                  │
└──────────────┘  └──────────────┘  └──────────────────┘
```

## Core Components

### 1. RAG System (`src/rag/`)

**Purpose**: Enable file-grounded Q&A with citations

**Components**:
- `DocumentIngestion`: Parses PDFs and text files, chunks content with metadata
- `DocumentStore`: ChromaDB vector store with OpenAI embeddings
- `ComplianceRetriever`: Retrieves relevant rules and formats with citation numbers

**Key Design Decisions**:
- Uses `RecursiveCharacterTextSplitter` for semantic chunking
- Stores chunk index and total chunks for precise citations
- ChromaDB persists locally for fast retrieval
- Embeddings: OpenAI `text-embedding-3-small` for quality/cost balance

**Citation Format**:
```
[Source 1] From safety_manual.pdf:
<retrieved text content>
```

### 2. Memory System (`src/memory/`)

**Purpose**: Maintain persistent, selective knowledge across sessions

**Components**:
- `MemoryManager`: Evaluates and writes memories using LLM
- `MemoryEntry`: Pydantic model for memory entries
- `MemoryDecision`: Structured decision on whether to write

**Storage**:
- `USER_MEMORY.md`: User-specific facts (role, sites managed, preferences)
- `COMPANY_MEMORY.md`: Organization-wide learnings (site issues, patterns)

**Key Design Decisions**:
- Selective storage: Only high-signal, reusable information
- Confidence threshold: 0.7+ required to write
- Duplicate detection: Prevents redundant entries
- Structured decision making via LLM JSON output

**Memory Evaluation Criteria**:
```json
{
  "should_write": true,
  "content": "User manages Site Alpha in Boston",
  "category": "location",
  "confidence": 0.95,
  "reasoning": "High-signal fact about user's role"
}
```

### 3. Weather System (`src/weather/`)

**Purpose**: Integrate real-time weather data for safety decisions

**Components**:
- `OpenMeteoClient`: API client for weather forecasts (no API key required)
- `WeatherSandbox`: Safe execution environment for weather analysis

**Features**:
- Geocoding: Convert location names to coordinates
- Safety metrics: Wind speed, precipitation, temperature extremes
- Compliance checking: Compare weather to safety thresholds
- Safe execution: AST-based code validation prevents malicious code

**Safety Thresholds** (extracted from documents):
- Wind speed: Default 20 mph (configurable per operation)
- Rain: Default 5mm (configurable)
- Weather codes: Automatic detection of thunderstorms, snow

### 4. Agent Orchestrator (`src/agent/`)

**Purpose**: Combine all systems into coherent safety decisions

**Workflow**:
1. **Retrieve Rules**: Search safety manual for relevant protocols
2. **Check Memory**: Recall site-specific and user-specific context
3. **Fetch Weather**: Get current and forecast conditions
4. **Extract Thresholds**: Parse wind/rain limits from retrieved rules
5. **Make Decision**: LLM analyzes all data and provides recommendation
6. **Update Memory**: Log safety decisions and site issues

**Output Format**:
```python
SafetyDecision(
    can_proceed=True/False,
    reasoning="Detailed explanation...",
    recommendations=["Action items..."],
    citations=[{source, filename, relevance_score}],
    weather_compliance={status, violations, ...},
    new_memories=[...]
)
```

## Data Flow

### Example: "Check Site Alpha for today"

```
User Input
    │
    ▼
┌────────────────────────────┐
│ 1. RAG: Find safety rules  │
│    for "Site Alpha"        │
│    → Retrieves wind limits │
│    → Cites source doc      │
└────────────────────────────┘
    │
    ▼
┌────────────────────────────┐
│ 2. Memory: Check if Site   │
│    Alpha has known issues  │
│    → "Roof leak reported"  │
└────────────────────────────┘
    │
    ▼
┌────────────────────────────┐
│ 3. Weather: Get Boston     │
│    forecast                │
│    → Wind: 25 mph (high)   │
│    → Rain: 8mm (wet)       │
└────────────────────────────┘
    │
    ▼
┌────────────────────────────┐
│ 4. Decision: Compare       │
│    rules vs reality        │
│    → Wind exceeds limit    │
│    → Rain exceeds limit    │
│    → RECOMMEND STOP        │
└────────────────────────────┘
    │
    ▼
┌────────────────────────────┐
│ 5. Memory: Log safety      │
│    pause                   │
│    → COMPANY_MEMORY.md     │
└────────────────────────────┘
    │
    ▼
Response to User
```

## Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Language** | Python 3.9+ | Ecosystem, readability |
| **LLM** | OpenAI GPT-4o-mini | Quality/cost balance |
| **Embeddings** | OpenAI text-embedding-3-small | Quality, speed |
| **Vector DB** | ChromaDB | Local, no external deps |
| **RAG Framework** | LangChain | Modular, well-documented |
| **UI** | Streamlit | Rapid prototyping |
| **CLI** | Click | Clean command interface |
| **Validation** | Pydantic | Type safety |
| **Weather API** | Open-Meteo | Free, no key needed |

## Security Considerations

### 1. Prompt Injection Protection
- RAG context is clearly delimited from user input
- System prompts are fixed templates
- No dynamic prompt construction from user data

### 2. Sandbox Safety
- Weather analysis uses AST validation
- Disallowed operations: imports, file I/O, network calls
- Restricted built-ins only

### 3. Memory Safety
- No storage of secrets or PII
- Content filtering via LLM evaluation
- Confidence threshold prevents low-quality writes

### 4. API Security
- API keys via environment variables only
- No key logging or storage in memory files
- Local-only vector store (no cloud exposure)

## Scalability & Performance

**Current Design**:
- Single-user (per instance)
- Local ChromaDB (disk-based)
- In-memory LLM calls
- Suitable for hackathon/demo scale

**Future Improvements**:
- PostgreSQL + pgvector for multi-user
- Redis for caching
- Async API calls
- Distributed vector search

## Testing Strategy

**Unit Tests**:
- Document ingestion edge cases
- Memory evaluation logic
- Weather API response parsing

**Integration Tests**:
- Full safety check workflow
- End-to-end document Q&A
- Memory read/write cycles

**Sanity Check** (`make sanity`):
- Validates all components load
- Tests document ingestion
- Verifies memory writes
- Generates `artifacts/sanity_output.json`

## Deployment

**Local Development**:
```bash
pip install -e ".[dev]"
cp .env.example .env
# Edit .env with OPENAI_API_KEY
make ui  # Run web interface
```

**Production Considerations**:
- Environment variable management
- Persistent volume for ChromaDB
- Health check endpoint
- Monitoring and logging

## Trade-offs Made

1. **OpenAI vs Local Models**: Chose OpenAI for quality; local models would reduce latency/cost but increase complexity

2. **ChromaDB vs Pinecone**: ChromaDB is local and free; Pinecone would offer better scale but adds dependency

3. **Streamlit vs React**: Streamlit for speed of development; React would offer better UX but requires frontend expertise

4. **File-based vs Database Memory**: Markdown files are human-readable and hackathon-friendly; SQLite would be more robust for production

5. **Single vs Multi-tenant**: Single-tenant for simplicity; multi-tenant would require user auth and data isolation

## Future Enhancements

- **Multi-modal**: Support for image-based safety inspections
- **Real-time Alerts**: Webhook integration for weather alerts
- **Mobile App**: Field access for site managers
- **Historical Analysis**: Trend analysis of safety decisions
- **Integration**: Connect to project management tools (Procore, etc.)

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Author**: Codex Team
