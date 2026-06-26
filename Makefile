# Makefile for homelab-netstats dummy diagnostics app

.PHONY: dev build run stop clean

# Run the app locally on host using python venv
dev:
	@echo "Creating virtual environment..."
	python3 -m venv .venv
	@echo "Installing requirements..."
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt
	@echo "Starting Streamlit..."
	.venv/bin/streamlit run streamlit_app.py --server.port 8501

# Build docker image
build:
	docker build -t homelab-netstats:latest .

# Spin up composition locally in docker
run:
	docker compose up -d

# Stop local composition
stop:
	docker compose down

# Clean virtual environment files
clean:
	rm -rf .venv
