# Documentation

Detailed documentation for the Conversational Assistance System.

---

## Guides

| Document | Description |
|----------|-------------|
| [localLlmRuntime.md](localLlmRuntime.md) | Local LLM deployment: **in-process** (`llama-cpp-python`) vs **external servers** (e.g. Ollama); how this relates to LangChain |

---

## Architecture Overview

The system follows a layered architecture with Dependency Injection (DI):

```
Controllers (HTTP) -> Services (Business Logic) -> Providers (Data/LLM)
```

All components are class-based (OOP). Abstract interfaces define contracts; concrete implementations are resolved at runtime by `ServiceFactory`.

## Workflow Providers

### JSON Provider (LOCAL)

- **Class**: `WorkflowJsonService`
- **Source**: JSON files in `cfg/workflows/`
- **Config**: `WORKFLOW_PROVIDER=JSON`, `WORKFLOW_DIR=cfg/workflows`
- **Usage**: Default provider. Each workflow is a `.json` file named by its `workflowId`.

### MongoDB Provider (REMOTE)

- **Class**: `WorkflowMdbService`
- **Source**: MongoDB collection
- **Config**: `WORKFLOW_PROVIDER=MDB`, `MDB_URI`, `MDB_DATABASE_NAME`, `MDB_COLLECTION_NAME`
- **Usage**: Documents must have a `workflowId` field matching the requested ID.

## LLM Providers

### Vertex AI (REMOTE)

- **Class**: `LlmRemoteService`
- **Model**: Gemini 2.5 Flash via `langchain-google-vertexai`
- **Config**: `LLM_PROVIDER=REMOTE`, `GCP_PROJECT_ID`, `GCP_LOCATION`
- **Auth**: Google Cloud Application Default Credentials (ADC)

### Local Model (LOCAL)

- **Class**: `LlmLocalService`
- **Model**: `mistral-7b-instruct-v0.2.Q4_K_M.gguf` (quantized GGUF)
- **Runtime**: `llama-cpp-python` + LangChain `LlamaCpp`
- **Config**: `LLM_PROVIDER=LOCAL`, `LOCAL_MODEL_PATH`, `LOCAL_MODEL_N_CTX`, `LOCAL_MODEL_N_THREADS`, `LOCAL_MODEL_TEMPERATURE`
- **Storage**: Place the `.gguf` file in the `models/` directory

### Downloading Models

Models are managed through `cfg/models.json` (catalog) and `scripts/downloadModel.py`.

**Automated download (recommended):**
```bash
make model-download                # download default model
make model-list                    # list available models
make model-select MODEL=phi-2     # download a specific model
```

**Manual download:**
1. Download from Hugging Face (e.g. `https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF`)
2. Choose the `Q4_K_M` quantization for best balance of quality and performance.
3. Place the file in `models/` directory.
4. Update `LOCAL_MODEL_PATH` in `cfg/.env`.

**Custom model from any Hugging Face repo:**
```bash
make model-custom REPO=TheBloke/Model-GGUF FILE=model.Q4_K_M.gguf
```

The download script automatically updates `cfg/.env` with the correct model path.

## Workflow JSON Schema

Each workflow file must follow this structure:

```json
{
  "description": "string",
  "goals": ["string"],
  "policy": ["string"],
  "steps": [
    { "id": "string", "description": "string" }
  ]
}
```

## Design Patterns Used

| Pattern | Where | Purpose |
|---|---|---|
| **Abstract Factory** | `ServiceFactory` | Resolves concrete providers from env config |
| **Strategy** | `WorkflowService` / `LlmService` | Same interface, different implementations |
| **Singleton** | LLM model loading | Load expensive model once at init |
| **Composition** | `WorkflowController` | Injects services via constructor |
