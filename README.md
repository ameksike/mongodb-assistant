# 🤖 Conversational Assistance System

A dynamic conversational assistance system built with **Python**, **FastAPI**, **LangChain**, and LLMs. The system analyzes conversation context and guides interactions based on configurable workflow definitions.

---

## ✨ Features

- 📋 Workflow-driven conversation guidance with configurable steps, goals, and policies
- 🔌 Pluggable workflow providers: **JSON files** (local) or **MongoDB** (remote)
- 🧠 Pluggable LLM providers: **Vertex AI Gemini 2.5 Flash** (remote) or **local GGUF model** via llama-cpp-python
- 💉 Dependency Injection architecture for seamless provider switching
- ✅ Pydantic request/response validation
- 🏗️ Class-based OOP design throughout

## 🚀 Get Started (Simple)

Use `make` to prepare everything and start the service:

```bash
make setup
make model-select MODEL=phi-2
make dev
```

Health check: [http://localhost:8000/health](http://localhost:8000/health)

For the full manual setup (without `make`) and a detailed comparison of both paths, see [doc/setup.md](doc/setup.md).

## 📦 Available Commands

Run `make help` to see all commands:

| Command | Description |
|---|---|
| `make setup` | Full project setup (install deps + create .env) |
| `make install` | Install all project dependencies |
| `make dev` | Start server in development mode (auto-reload) |
| `make start` | Start server in production mode |
| `make test` | Run all tests |
| `make check` | Run linter + tests |
| `make model-download` | Download the default local LLM model |
| `make model-list` | Catalog + download status; files already in `models/` |
| `make model-select MODEL=name` | Download a specific model from the catalog |
| `make model-custom REPO=x FILE=y` | Download any GGUF model from Hugging Face |
| `make lint` | Run linter (ruff) |
| `make format` | Format code (black) |
| `make clean` | Remove cache files and build artifacts |
| `make info` | Show current project configuration |
| `make health` | Check if the server is running |
| `make help` | Show all available commands |

## 🧠 Model Management

Models are managed through `cfg/models.json` (catalog) and downloaded via `bin/download.py`.

```bash
# Catalog, on-disk status, and files in models/
make model-list

# Download the default model (Mistral 7B Instruct Q4_K_M)
make model-download

# Download a specific catalog model
make model-select MODEL=phi-2

# Download any GGUF from Hugging Face
make model-custom REPO=TheBloke/Mistral-7B-Instruct-v0.2-GGUF FILE=mistral-7b-instruct-v0.2.Q5_K_M.gguf
```

The download script automatically updates `cfg/.env` with the new model path.

## 🔗 API

### `POST /api/process`

Send a workflow ID and conversation history to get the current step and suggested responses.

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
| `LLM_PROVIDER` | `LOCAL` | LLM provider: `LOCAL` or `REMOTE` |
| `LOCAL_MODEL_PATH` | `models/mistral-7b-instruct-v0.2.Q4_K_M.gguf` | Path to local GGUF model |
| `GCP_PROJECT_ID` | - | Google Cloud project (for REMOTE LLM) |
| `MDB_URI` | - | MongoDB connection URI (for MDB workflows) |

## 📁 Project Structure

```
cfg/
  workflows/           JSON workflow definitions
  models.json          Model download catalog
  .env                 Environment configuration
doc/                   Detailed documentation
iac/                   Infrastructure files (Docker/K8s)
models/                Local LLM model files (.gguf)
scripts/               Automation scripts
src/controllers/       FastAPI REST API layer
src/services/          Business logic (abstract + concrete)
src/utils/             Utility classes
tests/                 Unit and integration tests
```

## 📚 Documentation

See [doc/README.md](doc/README.md) for detailed architecture and provider documentation. For **local LLM process layout** (in-process `llama-cpp-python` vs external servers like Ollama), see [doc/llm.md](doc/llm.md).

### Related standards (agentic commerce and agents)

These open protocols sit alongside conversational and commerce-oriented agent systems; they are useful background when extending this assistant toward interoperable agents or checkout flows.

| Topic | Description | Documentation |
|--------|--------------|---------------|
| **UCP** | Universal Commerce Protocol — common language for platforms, agents, and merchants for agentic commerce | [ucp.dev](https://ucp.dev/) · [Specification overview](https://ucp.dev/latest/specification/overview/) · [Google Merchant / UCP](https://developers.google.com/merchant/ucp) · [GitHub: Universal-Commerce-Protocol/ucp](https://github.com/Universal-Commerce-Protocol/ucp) |
| **AP2** | Agent Payments Protocol — secure, verifiable payments initiated by agents (often used with A2A / MCP) | [ap2-protocol.org](https://ap2-protocol.org/) · [Google Cloud: Announcing AP2](https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol) · [GitHub: google-agentic-commerce/AP2](https://github.com/google-agentic-commerce/AP2) |
| **A2A** | Agent2Agent — discovery, tasks, and messaging between agents without sharing internal state | [A2A specification](https://google.github.io/A2A/specification/) · [a2a-protocol.org](https://a2a-protocol.org/) · [GitHub: google/A2A](https://github.com/google/A2A) |

### LLM stack used in this project

| Component | Documentation |
|-----------|----------------|
| **LangChain** | [Python docs](https://python.langchain.com/docs/) |
| **Vertex AI + Gemini** (remote) | [Vertex AI generative AI](https://cloud.google.com/vertex-ai/generative-ai/docs/overview) · [LangChain Google integrations](https://python.langchain.com/docs/integrations/providers/google/) · [`langchain-google-vertexai` reference](https://reference.langchain.com/python/langchain_google_vertexai/) |
| **Local GGUF** (llama-cpp) | [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) · [LangChain LlamaCpp](https://python.langchain.com/docs/integrations/llms/llamacpp/) |

## 🧪 Testing

```bash
make test         # Run all tests
make test-cov     # Run tests with coverage
make check        # Lint + tests
```

## 📄 License

See [LICENSE](LICENSE).
