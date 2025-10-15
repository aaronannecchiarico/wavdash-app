.PHONY: help format format-check lint test test-unit test-feature clean install

# Default target
help:
	@echo "Available commands:"
	@echo "  make format        - Format code with Black and isort"
	@echo "  make format-check  - Check code formatting without changes"
	@echo "  make lint          - Run flake8 linter"
	@echo "  make test          - Run all tests"
	@echo "  make test-unit     - Run unit tests only"
	@echo "  make test-feature  - Run feature tests only"
	@echo "  make clean         - Remove Python cache files"
	@echo "  make install       - Install dependencies"
	@echo "  make ci-check      - Run all CI/CD checks locally"

# Format code (makes changes)
format:
	@echo "Formatting code with Black..."
	@black .
	@echo "Sorting imports with isort..."
	@isort .
	@echo "✅ Code formatted!"

# Check formatting (no changes)
format-check:
	@echo "Checking Black formatting..."
	@black --check --diff .
	@echo "Checking isort..."
	@isort --check-only --diff .
	@echo "✅ Format check complete!"

# Run linter
lint:
	@echo "Running flake8..."
	@flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	@flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	@echo "✅ Linting complete!"

# Run all tests
test:
	@echo "Running all tests..."
	@pytest tests/ -v --tb=short

# Run unit tests
test-unit:
	@echo "Running unit tests..."
	@pytest tests/unit/ -v --tb=short

# Run feature tests
test-feature:
	@echo "Running feature tests..."
	@pytest tests/feature/ -v --tb=short

# Clean Python cache files
clean:
	@echo "Cleaning Python cache files..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cache cleaned!"

# Install dependencies
install:
	@echo "Installing dependencies..."
	@pip install -r requirements.txt
	@pip install black isort flake8 pytest pytest-asyncio pytest-mock pytest-cov
	@echo "✅ Dependencies installed!"

# Run all CI/CD checks locally
ci-check: format-check lint test-unit
	@echo "✅ All CI/CD checks passed!"
