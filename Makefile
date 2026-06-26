# Makefile for homelab-netstats diagnostics app

.DEFAULT_GOAL := help

.PHONY: help env dev docker-build docker-run docker-stop clean

# Help Menu (Default)
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Local Python Development Targets:"
	@echo "  env          - Set up the Python virtual environment (.venv) and install dependencies"
	@echo "  dev          - Run the Streamlit app locally (runs 'make env' if .venv is missing)"
	@echo ""
	@echo "Docker Targets:"
	@echo "  docker-build - Build the homelab-netstats:latest Docker image"
	@echo "  docker-run   - Start the app in docker-compose mode (exposed at http://localhost:8501)"
	@echo "  docker-stop  - Stop the running docker-compose container stack"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean        - Remove Python virtual environment and temporary files"

# --- LOCAL PYTHON DEVELOPMENT ---

# Set up local virtual environment and dependencies
env:
	@echo "Creating virtual environment..."
	python3 -m venv .venv
	@echo "Installing requirements..."
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

# Run the app locally on host
dev:
	@if [ ! -d ".venv" ]; then \
		echo "Virtual environment not found. Running 'make env' first..."; \
		$(MAKE) env; \
	fi
	@echo "Starting Streamlit locally..."
	.venv/bin/streamlit run streamlit_app.py --server.port 8501

# --- DOCKER TARGETS ---

# Build docker image
docker-build:
	docker build -t homelab-netstats:latest .

# Spin up composition locally in docker
docker-run:
	docker compose up -d

# Stop local composition
docker-stop:
	docker compose down

# --- CLEANUP ---

# Clean virtual environment files
clean:
	rm -rf .venv
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true

