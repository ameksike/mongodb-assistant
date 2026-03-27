# Documentation

Detailed documentation for the Conversational Assistance System.

---

## 🚀 Get Started (Simple)

1) Prepare the project:

```bash
make setup
```

2) Download one model and run the server:

```bash
make model:select modelName=phi-2
make dev
```

(`make run:dev` is the same as `make dev`. On **Windows CMD**, run these from the repo root with GNU Make on your `PATH`; see [setup.md](setup.md) for `cmd.exe` examples.)

3) Verify the API:
- `http://localhost:3333/health`
- `http://localhost:3333/docs`

Need manual setup without `make`? See [setup.md](setup.md).

---

## Guides

| Document | Description |
|----------|-------------|
| [setup.md](setup.md) | Complete setup guide: simple path with `make` and full manual path without `make` |
| [llm.md](llm.md) | Local LLM deployment: **in-process** (`llama-cpp-python`) vs **external servers** (e.g. Ollama); how this relates to LangChain |
| [manual-postman-curl.md](manual-postman-curl.md) | Manual tests: **curl** and Postman for `/health` and `/api/process`, with JSON examples under [requests/](requests/) |

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

### Google Generative AI / Vertex (REMOTE)

- **Class**: `LlmRemoteService`
- **Model**: `ChatGoogleGenerativeAI` from `langchain-google-genai` (default model `gemini-2.5-flash`, overridable with `GEMINI_MODEL`)
- **Config**: `LLM_PROVIDER=REMOTE`. With `GCP_PROJECT_ID` or `GOOGLE_CLOUD_PROJECT`: Vertex + `GCP_LOCATION` / `GOOGLE_CLOUD_LOCATION`. Without project: developer API using `GOOGLE_API_KEY` or `GEMINI_API_KEY` (see LangChain docs).
- **Auth**: ADC for Vertex; API key env vars for developer API

### Local Model (LOCAL)

- **Class**: `LlmLocalService`
- **Model**: `mistral-7b-instruct-v0.2.Q4_K_M.gguf` (quantized GGUF)
- **Runtime**: `llama-cpp-python` + LangChain `LlamaCpp`
- **Config**: `LLM_PROVIDER=LOCAL`, `LOCAL_MODEL_PATH`, `LOCAL_MODEL_N_CTX`, `LOCAL_MODEL_N_THREADS`, `LOCAL_MODEL_TEMPERATURE`
- **Storage**: Place the `.gguf` file in the `models/` directory

### Downloading Models

Models are managed through `cfg/models.json` (catalog), **`bin/download.py`** (CLI), and **`ModelDownloadService`** in `src/services/modelDownloadService.py`.

**Automated download with Make (bash or CMD):**
```bash
make model:download
make model:list
make model:select modelName=phi-2
make model:remove modelName=phi-2
make model:clean
```

Optional: `make model:select modelName=phi-2 forceDownload=1` to re-download. See [setup.md](setup.md) for **Windows CMD** one-liners and quoting tips.

**Manual download:**
1. Download from Hugging Face (e.g. `https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF`)
2. Choose the `Q4_K_M` quantization for best balance of quality and performance.
3. Place the file in `models/` directory.
4. Update `LOCAL_MODEL_PATH` in `cfg/.env`.

**Custom model from any Hugging Face repo:**
```bash
make model:custom huggingfaceRepo=TheBloke/Model-GGUF fileName=model.Q4_K_M.gguf
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
