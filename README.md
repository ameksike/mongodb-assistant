# 🤖 Conversational Assistance System

This project started as a PoC (Proof of Concept) of a virtual assistant to perform demonstrations for the project ['Mandate Ledger Service -  Universal Commerce Protocol (UCP) supported on MongoDB'](./doc/mls-project.md). A dynamic conversational assistance system built with **Python**, **FastAPI**, **LangChain**, **MongoDB**, and LLMs. The system analyzes conversation context and guides interactions based on configurable workflow definitions.

---

## ✨ Features

- 📋 Workflow-driven conversation guidance with configurable steps, goals, and policies
- 🔌 Pluggable workflow providers: **JSON files** (local) or **MongoDB** (remote)
- 🧠 Pluggable LLM providers: **local GGUF** (llama-cpp-python), **REMOTE** (LangChain + Gemini), or **VERTEXAI** (google-genai SDK direct, JSON-enforced)
- 🐳 Docker support: multi-stage build optimised for local LLM deployment
- 💉 Dependency Injection architecture for seamless provider switching
- ✅ Pydantic request/response validation
- 🏗️ Class-based OOP design throughout

## 🚀 Quick start (two separate flows)

### 1️⃣ Run the project

Use this when you want to **start the API** (local LLM example):

```bash
make preflight                        # pre-flight: verify Python, tools, files
make setup                            # same as make project:setup
make model:select modelName=phi-2
make dev
```

Then open [http://localhost:3333/health](http://localhost:3333/health) or [http://localhost:3333/docs](http://localhost:3333/docs).

The API port defaults to **3333** in the `Makefile` (`APP_PORT`) to avoid Windows reserved ranges (port 8000 often triggers `WinError 10013`). Override: `make run:dev APP_PORT=8080`.

For full manual setup (without `make`), see [doc/setup.md](doc/setup.md).

### 2️⃣ Run the tests

Use this when you only want to **verify the codebase** (no server required for unit tests):

```bash
make setup        # once: creates venv, installs deps (same as make project:setup)
make test         # same as make test:run
```

Optional:

```bash
make test-cov     # same as make test:cov — coverage report
make check        # ruff lint + format check + tests (quality:check)
```

Without `make` (from the project root, with the virtualenv active):

```bash
pytest tests/ -v
python -m ruff check src tests
python -m ruff format --check src tests
```

Details: [doc/code-quality.md](doc/code-quality.md).

Run `make help` for grouped targets (`project:setup`, `model:list`, `run:dev`, `test:run`, …).

### 💠 CMD and Make

Use the **project root** (folder that contains the `Makefile`) as the current directory. Install **GNU Make** so `make` is on your `PATH` (for example: [Chocolatey](https://chocolatey.org/) `choco install make`, a Git for Windows environment that includes `make`, or MSYS2/MinGW).

Example from **Command Prompt**:

```bat
cd /d C:\path\to\mongodb-assistant
make setup
make model:select modelName=phi-2
make run:dev
```

**Rules that avoid surprises:**

| Topic | Detail |
|--------|--------|
| Target syntax | Type the colon as shown: `model:download`, `run:dev`, `test:run` (no backslash before `:` on the command line). |
| Variables | GNU Make variables are **camelCase** and attached with **no spaces**: `modelName=phi-2`, `huggingfaceRepo=TheBloke/Model-GGUF`, `fileName=model.Q4_K_M.gguf`, optional `forceDownload=1`. |
| Several variables | Put them on one line after the target: `make model:custom huggingfaceRepo=user/repo fileName=file.gguf` |
| `make` not installed | Use [Option B in doc/setup.md](doc/setup.md) (Python and `python bin\download.py` / `venv\Scripts\python.exe -m uvicorn ...`). |

`bin\download.py` is the same entry point the Makefile uses; it delegates to `src/services/modelDownloadService.py`. Full step-by-step for CMD and PowerShell is in [doc/setup.md](doc/setup.md).

---

## 📦 Available Commands

Main targets use **`namespace:action`** (GNU Make escapes these as `model\:download` in the Makefile; you type **`make model:download`**).

| Command | Alias | Description |
|---|---|---|
| `make project:check` | `make preflight` | Pre-flight: verify Python version, tools, files, models |
| `make project:setup` | `make setup` | Full setup: venv, deps, `cfg/.env` |
| `make project:env` | | Create `cfg/.env` from example only |
| `make project:info` | | Print env, models on disk, Python version |
| `make project:clean` | `make clean` | Remove `__pycache__`, `.pytest_cache`, `*.pyc` |
| `make deps:install` | `make install` | Install dependencies into `venv/` |
| `make run:dev` | `make dev` | API dev server (reload); default port **3333** (`APP_PORT`) |
| `make run:start` | `make start` | API production mode; same port variable |
| `make run:health` | `make health` | `GET /health` (needs `curl`) |
| `make model:download` | | Download default catalog model (skips if file exists) |
| `make model:list` | | Catalog + on-disk status |
| `make model:select modelName=phi-2` | | Download one catalog model |
| `make model:custom huggingfaceRepo=... fileName=...` | | Custom Hugging Face GGUF |
| `make model:remove modelName=phi-2` | | Remove catalog model file from `models/` |
| `make model:remove fileName=foo.gguf` | | Remove a file by basename |
| `make model:clean` | `make clean-models` | Delete all `.gguf` / `.bin` under `models/` |
| `make workflow:import` | | Import `cfg/workflows/*.json` into MongoDB |
| `make workflow:importDryRun` | | Show which workflows would be imported (no DB write) |
| `make workflow:list` | | `GET /api/workflows` on the running server |
| `make test:run` | `make test` | Pytest |
| `make test:cov` | `make test-cov` | Pytest + coverage |
| `make quality:lint` | `make lint` | Ruff static analysis (`ruff check`) |
| `make quality:format` | `make format` | Ruff formatter (`ruff format`) |
| `make quality:formatCheck` | | Fail if sources are not formatted |
| `make quality:check` | `make check` | Lint + format check + tests |
| `make help` | | Short list of groups and examples |

Optional: `make model:select modelName=phi-2 forceDownload=1` to force re-download.

### Workflow import (MongoDB)

When `WORKFLOW_PROVIDER=MDB`, import local JSON files into MongoDB:

```bash
make workflow:importDryRun   # preview
make workflow:import         # upsert into MongoDB (re-runnable)
make workflow:list           # verify via GET /api/workflows (server must be running)
```

The import script (`bin/import_workflows.py`) reads `MDB_URI`, `MDB_DATABASE_NAME`, and `MDB_COLLECTION_NAME` from `cfg/.env` and upserts each file by `workflowId`.

## 🧠 Model Management

Models are managed through `cfg/models.json` (catalog) and `bin/download.py`.

```bash
make model:list
make model:download
make model:select modelName=phi-2
make model:custom huggingfaceRepo=TheBloke/Mistral-7B-Instruct-v0.2-GGUF fileName=mistral-7b-instruct-v0.2.Q5_K_M.gguf
make model:remove modelName=phi-2
make model:clean
python bin/download.py --force --model phi-2   # re-download from CLI
```

If the file is already in `models/`, download **skips** the network (set `forceDownload=1` on `model:select` or `--force` on the script). The script updates `cfg/.env` `LLM_LOCAL_MODEL_PATH` when a download completes or when a skip still selects that catalog file.

## 🔗 API

### `GET /api/workflows`

List all available workflows (lightweight summaries based on `WORKFLOW_PROVIDER`).

**Response:**
```json
[
  { "workflowId": "straightforward", "description": "This workflow defines a guided purchase interaction..." },
  { "workflowId": "happy_path", "description": "..." }
]
```

### `POST /api/process`

Send a workflow ID and conversation history to get the current step and suggested user responses.

**Request:**
```json
{
  "workflowId": "happy_path",
  "conversation": [
    { "role": "user", "message": "I'd like to start shopping." },
    { "role": "agent", "message": "Great! What items are you looking for?", "step": "introduction" }
  ],
  "maxAnswers": 2
}
```

**Response:**
```json
{
  "workflowId": "happy_path",
  "stepId": "intentIdentification",
  "answers": [
    "I'm looking for gaming headphones with noise cancellation.",
    "I need a French press coffee maker that's refundable."
  ]
}
```

### `GET /health`

Health check endpoint.

## ⚙️ Configuration

All settings are loaded from `cfg/.env`:

| Variable | Default | Description |
|---|---|---|
| `WORKFLOW_PROVIDER` | `JSON` | Workflow source: `JSON` or `MDB` |
| `WORKFLOW_DIR` | `cfg/workflows` | Directory for JSON workflow files |
| `LLM_PROVIDER` | `LOCAL` | LLM provider: `LOCAL`, `REMOTE`, or `VERTEXAI` |
| `LLM_LOCAL_MODEL_PATH` | `models/mistral-7b-instruct-v0.2.Q4_K_M.gguf` | Path to local GGUF model |
| `GOOGLE_CLOUD_PROJECT` | - | Google Cloud project for REMOTE LLM (Vertex); omit to use API key |
| `GOOGLE_CLOUD_LOCATION` | `us-central1` | Region for Vertex |
| `GOOGLE_MODEL_ID` | `gemini-2.5-flash` | Gemini model id for REMOTE |
| `MDB_URI` | - | MongoDB connection URI (for MDB workflows) |
| `MDB_DATABASE_NAME` | - | MongoDB database name |
| `MDB_COLLECTION_NAME` | - | MongoDB collection name |
| `LLM_PROMPT_FORMAT` | `text` | Prompt packaging: `text` or `json` |
| `GOOGLE_API_KEY` | - | API key for REMOTE / VERTEXAI (mutually exclusive with Vertex AI ADC) |

## 🐳 Docker

Build and run with a local LLM model (no `make` required):

```bash
docker compose up --build
```

The Dockerfile uses a multi-stage build: C++ compilation of `llama-cpp-python` in the builder stage, slim runtime image with only the virtualenv. The GGUF model is mounted as a volume, never baked into the image.

```bash
# Or with plain docker:
docker build -t mongodb-assistant .
docker run -p 3333:3333 \
  -v ./models:/app/models:ro \
  -v ./cfg/.env:/app/cfg/.env:ro \
  mongodb-assistant
```

Override the model at runtime: `-e LLM_LOCAL_MODEL_PATH=models/phi-2.Q4_K_M.gguf`

For AVX2 SIMD optimisation on modern CPUs: `docker build --build-arg CMAKE_ARGS="-DGGML_AVX2=ON" -t mongodb-assistant .`

## 📁 Project Structure

```
cfg/
  workflows/           JSON workflow definitions
  models.json          Model download catalog
  .env                 Environment configuration
doc/                   Detailed documentation
iac/                   Infrastructure files (Docker/K8s)
models/                Local LLM model files (.gguf)
bin/                   CLI scripts (check.py, download.py, import_workflows.py)
Dockerfile             Multi-stage build (LOCAL LLM optimised)
docker-compose.yml     One-command container deployment
src/controllers/       FastAPI REST API layer
src/models/            Pydantic API schemas
src/services/          Business logic (abstract + concrete)
src/utils/             Utility classes
tests/                 Unit and integration tests
```

## 📚 Documentation

See [doc/README.md](doc/README.md) for detailed architecture and provider documentation. For **local LLM process layout** (in-process `llama-cpp-python` vs external servers like Ollama), see [doc/llm.md](doc/llm.md). For **macOS-specific issues** (`llama-cpp-python` build, SSL certificates, `python3` detection), see [doc/troubleshooting-macos.md](doc/troubleshooting-macos.md).

### Related standards (agentic commerce and agents)

These open protocols sit alongside conversational and commerce-oriented agent systems; they are useful background when extending this assistant toward interoperable agents or checkout flows.

| Topic | Description | Documentation |
|--------|--------------|---------------|
| **UCP** | Universal Commerce Protocol — common language for platforms, agents, and merchants for agentic commerce | [ucp.dev](https://ucp.dev/) · [Specification overview](https://ucp.dev/latest/specification/overview/) · [Google Merchant / UCP](https://developers.google.com/merchant/ucp) · [GitHub: Universal-Commerce-Protocol/ucp](https://github.com/Universal-Commerce-Protocol/ucp) |
| **AP2** | Agent Payments Protocol — secure, verifiable payments initiated by agents (often used with A2A / MCP) | [ap2-protocol.org](https://ap2-protocol.org/) · [Google Cloud: Announcing AP2](https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol) · [GitHub: google-agentic-commerce/AP2](https://github.com/google-agentic-commerce/AP2) |
| **A2A** | Agent2Agent — discovery, tasks, and messaging between agents without sharing internal state | [A2A specification](https://google.github.io/A2A/specification/) · [a2a-protocol.org](https://a2a-protocol.org/) · [GitHub: google/A2A](https://github.com/google/A2A) |
| **x402** | HTTP-native payment standard — servers respond with `402 Payment Required` and clients pay instantly with stablecoins; zero accounts, zero friction, designed for agentic payments at scale | [x402.org](https://www.x402.org/) · [Whitepaper](https://www.x402.org/whitepaper) |

### LLM stack used in this project

| Component | Documentation |
|-----------|----------------|
| **LangChain** | [Python docs](https://python.langchain.com/docs/) |
| **Gemini** (REMOTE) | [Vertex AI generative AI](https://cloud.google.com/vertex-ai/generative-ai/docs/overview) · [LangChain `ChatGoogleGenerativeAI`](https://reference.langchain.com/python/integrations/langchain_google_genai/ChatGoogleGenerativeAI/) |
| **Gemini** (VERTEXAI) | [google-genai SDK](https://googleapis.github.io/python-genai/) · Direct `genai.Client` with `response_mime_type="application/json"` |
| **Local GGUF** (llama-cpp) | [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) · [LangChain LlamaCpp](https://python.langchain.com/docs/integrations/llms/llamacpp/) |

## 📄 License

See [LICENSE](LICENSE).
