# Sample Documents

This folder contains sample documents for testing the RAG system.

## Contents

- `sample_safety_manual.txt` - Example construction safety manual with weather-related rules
- `site_protocols.txt` - Site-specific protocols and procedures

## Usage

Documents in this folder can be ingested using:

```bash
# CLI
python -m src.ui.cli ingest sample_docs/*.txt

# Or let the sanity check handle it automatically
make sanity
```

## Creating Your Own Documents

You can add your own:
- Safety manuals (PDF or TXT)
- Protocol documents
- Contract clauses
- Any compliance documentation

Supported formats:
- PDF (.pdf)
- Text (.txt)
- Markdown (.md)
