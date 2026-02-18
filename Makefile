.PHONY: install run ui sanity clean test format lint help

# Default target
help:
	@echo "Codex - Operational Risk & Compliance Agent"
	@echo ""
	@echo "Available commands:"
	@echo "  make install     Install dependencies"
	@echo "  make run         Run the CLI application"
	@echo "  make ui          Run the Streamlit web interface"
	@echo "  make sanity      Run sanity check (generates artifacts/sanity_output.json)"
	@echo "  make test        Run tests"
	@echo "  make format      Format code with black and isort"
	@echo "  make lint        Run linting checks"
	@echo "  make clean       Clean generated files"

# Installation
install:
	pip install -e .
	pip install -e ".[dev]"
	@echo "Installation complete! Copy .env.example to .env and add your API keys."

# Run CLI
run:
	python -m src.ui.cli

# Run Streamlit UI
ui:
	streamlit run src/ui/app.py

# Sanity check for judges
sanity:
	python scripts/sanity_check.py

# Testing
test:
	pytest tests/ -v

# Code formatting
format:
	black src/ tests/ scripts/
	isort src/ tests/ scripts/

# Linting
lint:
	flake8 src/ tests/ scripts/
	mypy src/

# Clean generated files
clean:
	rm -rf __pycache__ src/__pycache__ src/*/__pycache__
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .mypy_cache/
	rm -rf chroma_db/ .chroma/
	rm -rf uploads/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
