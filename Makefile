# ============================================================================
# Conversational Assistance System - Project Commands
# ============================================================================
# Usage: make <command>
# Run `make help` to see all available commands.
# ============================================================================

.DEFAULT_GOAL := help
BASE_PYTHON := python
VENV_DIR := venv
ifeq ($(OS),Windows_NT)
VENV_BIN := $(VENV_DIR)/Scripts
VENV_PYTHON := $(VENV_BIN)/python.exe
VENV_PIP := $(VENV_BIN)/pip.exe
VENV_UVICORN := $(VENV_BIN)/uvicorn.exe
VENV_PYTEST := $(VENV_BIN)/pytest.exe
else
VENV_BIN := $(VENV_DIR)/bin
VENV_PYTHON := $(VENV_BIN)/python
VENV_PIP := $(VENV_BIN)/pip
VENV_UVICORN := $(VENV_BIN)/uvicorn
VENV_PYTEST := $(VENV_BIN)/pytest
endif
PYTHON := $(VENV_PYTHON)
PIP := $(VENV_PIP)
UVICORN := $(VENV_UVICORN)
PYTEST := $(VENV_PYTEST)
APP_MODULE := src.main:app
ENV_FILE := cfg/.env
ENV_EXAMPLE := cfg/.env.example

# ---- Setup -----------------------------------------------------------------

.PHONY: install
install: venv ## Install all project dependencies in virtual environment
	$(PIP) install -r requirements.txt

.PHONY: install-dev
install-dev: venv ## Install dependencies + dev tools (linting, formatting)
	$(PIP) install -r requirements.txt
	$(PIP) install ruff black

.PHONY: setup
setup: install env ## Full project setup (install deps + create .env)
	@echo "Setup complete. Edit cfg/.env with your settings."

.PHONY: env
env: ## Create cfg/.env from example if it does not exist
	@$(BASE_PYTHON) -c "from pathlib import Path; import shutil; env=Path(r'$(ENV_FILE)'); ex=Path(r'$(ENV_EXAMPLE)'); exists=env.exists(); (print(f'{env} already exists, skipping.') if exists else (shutil.copyfile(ex, env), print(f'Created {env} from {ex}')))"

.PHONY: venv
venv: ## Create a Python virtual environment
	$(BASE_PYTHON) -m venv $(VENV_DIR)
	@echo "Virtual environment ready in $(VENV_DIR)"

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
	$(BASE_PYTHON) scripts/downloadModel.py

.PHONY: model-list
model-list: ## List available models in the catalog
	$(BASE_PYTHON) scripts/downloadModel.py --list

.PHONY: model-select
model-select: ## Download a specific model (usage: make model-select MODEL=mistral-7b-instruct)
ifndef MODEL
	$(error Usage: make model-select MODEL=<model-name>. Run 'make model-list' to see available models.)
endif
	$(BASE_PYTHON) scripts/downloadModel.py --model "$(MODEL)"

.PHONY: model-custom
model-custom: ## Download a custom model (usage: make model-custom REPO=user/repo FILE=model.gguf)
ifndef REPO
	$(error Usage: make model-custom REPO=TheBloke/Model-GGUF FILE=model.Q4_K_M.gguf)
endif
ifndef FILE
	$(error Usage: make model-custom REPO=TheBloke/Model-GGUF FILE=model.Q4_K_M.gguf)
endif
	$(BASE_PYTHON) scripts/downloadModel.py --repo "$(REPO)" --file "$(FILE)"

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
