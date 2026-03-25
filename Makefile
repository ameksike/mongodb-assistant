# ============================================================================
# Conversational Assistance System - Project Commands
# ============================================================================
# Usage: make <command>
# Run `make help` to see all available commands.
# ============================================================================

.DEFAULT_GOAL := help
PYTHON := python
PIP := pip
UVICORN := uvicorn
PYTEST := pytest
APP_MODULE := src.main:app
ENV_FILE := cfg/.env
ENV_EXAMPLE := cfg/.env.example

# ---- Setup -----------------------------------------------------------------

.PHONY: install
install: ## Install all project dependencies
	$(PIP) install -r requirements.txt

.PHONY: install-dev
install-dev: ## Install dependencies + dev tools (linting, formatting)
	$(PIP) install -r requirements.txt
	$(PIP) install ruff black

.PHONY: setup
setup: install env ## Full project setup (install deps + create .env)
	@echo "Setup complete. Edit cfg/.env with your settings."

.PHONY: env
env: ## Create cfg/.env from example if it does not exist
	@if [ ! -f $(ENV_FILE) ]; then \
		cp $(ENV_EXAMPLE) $(ENV_FILE); \
		echo "Created $(ENV_FILE) from $(ENV_EXAMPLE)"; \
	else \
		echo "$(ENV_FILE) already exists, skipping."; \
	fi

.PHONY: venv
venv: ## Create a Python virtual environment
	$(PYTHON) -m venv venv
	@echo "Activate with: source venv/bin/activate"

# ---- Run -------------------------------------------------------------------

.PHONY: dev
dev: ## Start the server in development mode (auto-reload)
	$(UVICORN) $(APP_MODULE) --reload --host 0.0.0.0 --port 8000

.PHONY: start
start: ## Start the server in production mode
	$(UVICORN) $(APP_MODULE) --host 0.0.0.0 --port 8000

.PHONY: health
health: ## Check if the server is running
	@curl -s http://localhost:8000/health | $(PYTHON) -m json.tool 2>/dev/null || echo "Server is not running."

# ---- Models ----------------------------------------------------------------

.PHONY: model-download
model-download: ## Download the default local LLM model
	$(PYTHON) scripts/downloadModel.py

.PHONY: model-list
model-list: ## List available models in the catalog
	$(PYTHON) scripts/downloadModel.py --list

.PHONY: model-select
model-select: ## Download a specific model (usage: make model-select MODEL=mistral-7b-instruct)
	@if [ -z "$(MODEL)" ]; then \
		echo "Usage: make model-select MODEL=<model-name>"; \
		echo "Run 'make model-list' to see available models."; \
	else \
		$(PYTHON) scripts/downloadModel.py --model $(MODEL); \
	fi

.PHONY: model-custom
model-custom: ## Download a custom model (usage: make model-custom REPO=user/repo FILE=model.gguf)
	@if [ -z "$(REPO)" ] || [ -z "$(FILE)" ]; then \
		echo "Usage: make model-custom REPO=TheBloke/Model-GGUF FILE=model.Q4_K_M.gguf"; \
	else \
		$(PYTHON) scripts/downloadModel.py --repo $(REPO) --file $(FILE); \
	fi

# ---- Test ------------------------------------------------------------------

.PHONY: test
test: ## Run all tests
	$(PYTEST) tests/ -v

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	$(PYTEST) tests/ -v --cov=src --cov-report=term-missing

.PHONY: test-watch
test-watch: ## Run tests in watch mode (requires pytest-watch)
	ptw tests/ -- -v

# ---- Code Quality ----------------------------------------------------------

.PHONY: lint
lint: ## Run linter (ruff)
	ruff check src/ tests/

.PHONY: format
format: ## Format code (black)
	black src/ tests/

.PHONY: check
check: lint test ## Run linter + tests

# ---- Clean -----------------------------------------------------------------

.PHONY: clean
clean: ## Remove Python cache files and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Cleaned."

.PHONY: clean-models
clean-models: ## Remove all downloaded model files
	rm -f models/*.gguf models/*.bin
	@echo "Model files removed."

# ---- Info ------------------------------------------------------------------

.PHONY: info
info: ## Show current project configuration
	@echo "=== Environment ==="
	@if [ -f $(ENV_FILE) ]; then \
		grep -v "^#" $(ENV_FILE) | grep -v "^$$"; \
	else \
		echo "No $(ENV_FILE) found. Run 'make env' to create it."; \
	fi
	@echo ""
	@echo "=== Models ==="
	@ls -lh models/*.gguf 2>/dev/null || echo "No models downloaded. Run 'make model-download'."
	@echo ""
	@echo "=== Python ==="
	@$(PYTHON) --version

# ---- Help ------------------------------------------------------------------

.PHONY: help
help: ## Show this help message
	@echo ""
	@echo "Usage: make <command>"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
