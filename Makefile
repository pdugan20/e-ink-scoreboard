.PHONY: help install install-hooks lint format check test test-python test-js test-fast test-coverage clean

# Detect if we should use venv or global commands
PYTHON := $(shell command -v python3 2> /dev/null || echo python)
PYTEST := $(shell command -v venv/bin/pytest 2> /dev/null || command -v pytest 2> /dev/null || echo python -m pytest)
PIP := $(shell command -v venv/bin/pip 2> /dev/null || command -v pip 2> /dev/null || echo pip)

help:
	@echo "Available commands:"
	@echo "  make install        - Install all dependencies (Python + Node)"
	@echo "  make install-hooks  - Install pre-commit hooks"
	@echo "  make lint           - Run all linters"
	@echo "  make format         - Format all code"
	@echo "  make check          - Run all checks (lint + format check)"
	@echo "  make test           - Run all tests (Python + JavaScript)"
	@echo "  make test-python    - Run Python tests only"
	@echo "  make test-js        - Run JavaScript tests only"
	@echo "  make test-fast      - Run fast tests only (skip slow/e2e)"
	@echo "  make test-coverage  - Run tests with coverage report"
	@echo "  make clean          - Remove cache files"

install:
	@echo "Installing Python dependencies..."
	$(PIP) install -r requirements-dev.txt
	$(PIP) install -r requirements-test.txt
	@echo "Installing Node dependencies..."
	npm install
	@echo "Done! Run 'make install-hooks' to set up git hooks."

install-hooks:
	@echo "Installing pre-commit hooks..."
	pre-commit install
	@echo "Hooks installed! They will run automatically on commit."

lint:
	@echo "Running linters (via pre-commit)..."
	pre-commit run --all-files

format:
	@echo "Auto-formatting all code (via pre-commit)..."
	pre-commit run --all-files

check:
	@echo "Running all checks..."
	@echo "\n=== Running pre-commit hooks on all files ==="
	pre-commit run --all-files
	@echo "\nAll checks passed!"

test:
	@echo "Running all tests..."
	@echo "\n=== Python tests ==="
	$(PYTEST)
	@echo "\n=== JavaScript tests ==="
	npm run test
	@echo "\nAll tests passed!"

test-python:
	@echo "Running Python tests..."
	$(PYTEST)

test-js:
	@echo "Running JavaScript tests..."
	npm run test

test-fast:
	@echo "Running fast tests only..."
	$(PYTEST) -m "not slow and not e2e"
	npm run test

test-coverage:
	@echo "Running tests with coverage..."
	@echo "\n=== Python coverage ==="
	$(PYTEST) --cov --cov-report=html --cov-report=term
	@echo "\n=== JavaScript coverage ==="
	npm run test:coverage
	@echo "\nCoverage reports generated:"
	@echo "  Python: htmlcov/index.html"
	@echo "  JavaScript: coverage/index.html"

clean:
	@echo "Cleaning cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Clean complete!"
