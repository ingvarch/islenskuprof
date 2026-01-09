.PHONY: test lint format check clean

# Run all tests
test:
	python -m unittest discover tests/ -v

# Run linter
lint:
	ruff check .

# Format code
format:
	ruff format .

# Run all checks (lint + format check + tests)
check: lint
	ruff format --check .
	python -m unittest discover tests/ -v

# Fix lint issues and format
fix:
	ruff check --fix .
	ruff format .

# Clean cache files
clean:
	ruff clean
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
