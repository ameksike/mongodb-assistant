# Conversational Assistance System

A dynamic conversational assistance system built with **Python**, **FastAPI**, **LangChain**, and LLMs. The system analyzes conversation context and guides interactions based on configurable workflow definitions.

---

## Features

- Workflow-driven conversation guidance with configurable steps, goals, and policies
- Pluggable workflow providers: **JSON files** (local) or **MongoDB** (remote)
- Pluggable LLM providers: **Vertex AI Gemini 2.5 Flash** (remote) or **local GGUF model** via llama-cpp-python
- Dependency Injection architecture for seamless provider switching
- Pydantic request/response validation
- Class-based OOP design throughout

## Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd mongodb-assistant
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp cfg/.env.example cfg/.env
# Edit cfg/.env with your settings

# Run the server
uvicorn src.main:app --reload
```

## API

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

## Configuration

All settings are loaded from `cfg/.env`:

| Variable | Default | Description |
|---|---|---|
| `WORKFLOW_PROVIDER` | `JSON` | Workflow source: `JSON` or `MDB` |
| `WORKFLOW_DIR` | `cfg/workflows` | Directory for JSON workflow files |
| `LLM_PROVIDER` | `LOCAL` | LLM provider: `LOCAL` or `REMOTE` |
| `LOCAL_MODEL_PATH` | `models/mistral-7b-instruct-v0.2.Q4_K_M.gguf` | Path to local GGUF model |
| `GCP_PROJECT_ID` | - | Google Cloud project (for REMOTE LLM) |
| `MDB_URI` | - | MongoDB connection URI (for MDB workflows) |

## Project Structure

```
cfg/workflows/       # JSON workflow definitions
doc/                 # Detailed documentation
iac/                 # Infrastructure files (Docker/K8s)
models/              # Local LLM model files (.gguf)
src/controllers/     # FastAPI REST API layer
src/services/        # Business logic (abstract + concrete)
src/utils/           # Utility classes
tests/               # Unit and integration tests
```

## Documentation

See [doc/README.md](doc/README.md) for detailed architecture and provider documentation.

## Testing

```bash
pytest tests/ -v
```

## License

See [LICENSE](LICENSE).
