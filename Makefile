# Set up uv with proper path
UV = PYTHONPATH=src uv run

.PHONY: dev test lint clean install

# Development server with hot reload
dev:
	$(UV) uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload

# Install dependencies
install:
	uv sync

# Run tests
test:
	$(UV) pytest server/test.py -v

# Lint and format code
lint:
	$(UV) black server/
	$(UV) flake8 server/

# Clean Python cache
clean:
	find . -type d -name "__pycache__" -delete
	find . -name "*.pyc" -delete