import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from src.controllers.workflowController import controller, router as workflowRouter
from src.services.serviceFactory import ServiceFactory

load_dotenv(dotenv_path="cfg/.env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def _logStartupConfig():
    """Eagerly initialise services and log a non-sensitive configuration summary."""
    workflowProvider = os.getenv("WORKFLOW_PROVIDER", "JSON")
    llmProvider = os.getenv("LLM_PROVIDER", "LOCAL")

    lines = ["", "========== Startup Configuration =========="]

    lines.append(f"  Workflow provider : {workflowProvider}")
    if workflowProvider.upper() == "MDB":
        lines.append(
            f"  Database          : {os.getenv('MDB_DATABASE_NAME', 'n/a')}"
        )
        lines.append(
            f"  Collection        : {os.getenv('MDB_COLLECTION_NAME', 'n/a')}"
        )
    else:
        lines.append(
            f"  Workflow directory: {os.getenv('WORKFLOW_DIR', 'cfg/workflows')}"
        )

    lines.append(f"  LLM provider      : {llmProvider}")

    llmInfo: dict = {}
    try:
        llmService = ServiceFactory.getLlmService()
        llmInfo = llmService.startupInfo()
        controller.llmService = llmService
    except Exception as exc:
        logger.warning("Could not initialise LLM service at startup: %s", exc)

    try:
        wfService = ServiceFactory.getWorkflowService()
        controller.workflowService = wfService
    except Exception as exc:
        logger.warning("Could not initialise workflow service at startup: %s", exc)

    promptFormat = llmInfo.get(
        "promptFormat", os.getenv("LLM_PROMPT_FORMAT", "text")
    )
    lines.append(f"  Prompt format     : {promptFormat}")

    if llmProvider.upper() == "LOCAL":
        _appendLocalInfo(lines, llmInfo)
    else:
        _appendRemoteInfo(lines, llmInfo)

    lines.append("============================================")
    logger.info("\n".join(lines))

    _logContextWindowAdvisory(llmProvider, llmInfo)


def _appendLocalInfo(lines: list[str], llmInfo: dict):
    modelPath = llmInfo.get(
        "modelPath", os.getenv("LLM_LOCAL_MODEL_PATH", "n/a")
    )
    lines.append(f"  Model             : {modelPath}")

    nCtx = llmInfo.get("nCtx")
    nCtxTrain = llmInfo.get("nCtxTrain")
    if nCtx and nCtxTrain:
        lines.append(
            f"  Context window    : {nCtx} tokens (training: {nCtxTrain})"
        )
    elif nCtx:
        lines.append(f"  Context window    : {nCtx} tokens")
    else:
        envCtx = os.getenv("LLM_LOCAL_MODEL_N_CTX")
        if envCtx:
            lines.append(f"  Context window    : {envCtx} tokens")

    nThreads = llmInfo.get(
        "nThreads", os.getenv("LLM_LOCAL_MODEL_N_THREADS", "n/a")
    )
    temperature = llmInfo.get(
        "temperature", os.getenv("LLM_LOCAL_MODEL_TEMPERATURE", "n/a")
    )
    lines.append(f"  Threads           : {nThreads}")
    lines.append(f"  Temperature       : {temperature}")


def _appendRemoteInfo(lines: list[str], llmInfo: dict):
    modelId = llmInfo.get("modelId", os.getenv("GOOGLE_MODEL_ID", "n/a"))
    lines.append(f"  Model             : {modelId}")
    project = llmInfo.get("project", os.getenv("GOOGLE_CLOUD_PROJECT"))
    if project:
        lines.append(f"  GCP project       : {project}")
    location = llmInfo.get(
        "location", os.getenv("GOOGLE_CLOUD_LOCATION", "n/a")
    )
    lines.append(f"  GCP location      : {location}")


def _logContextWindowAdvisory(llmProvider: str, llmInfo: dict):
    if llmProvider.upper() != "LOCAL":
        return
    nCtx = llmInfo.get("nCtx")
    nCtxTrain = llmInfo.get("nCtxTrain")
    if not nCtx or not nCtxTrain:
        return
    if nCtx > nCtxTrain:
        logger.warning(
            "Context window n_ctx (%d) exceeds model training context (%d). "
            "Prompts near the limit may produce degraded output.",
            nCtx,
            nCtxTrain,
        )
    else:
        logger.info(
            "Context window n_ctx (%d) within model training context (%d).",
            nCtx,
            nCtxTrain,
        )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _logStartupConfig()
    yield


app = FastAPI(
    title="Conversational Assistance System",
    description="Dynamic conversational interactions guided by workflow definitions.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(workflowRouter)


@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    return {"status": "ok"}
