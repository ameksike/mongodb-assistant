import logging
import os

from src.services.llmService import LlmService

logger = logging.getLogger(__name__)


class LlmLocalService(LlmService):
    """LOCAL provider: GGUF model loaded via llama-cpp-python + LangChain."""

    def __init__(self):
        from langchain_community.llms import LlamaCpp

        modelPath = os.getenv(
            "LOCAL_MODEL_PATH", "models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
        )
        self.llm = LlamaCpp(
            model_path=modelPath,
            n_ctx=int(os.getenv("LOCAL_MODEL_N_CTX", "4096")),
            n_threads=int(os.getenv("LOCAL_MODEL_N_THREADS", "4")),
            temperature=float(os.getenv("LOCAL_MODEL_TEMPERATURE", "0.7")),
            verbose=False,
        )
        logger.info(f"LlmLocalService initialized with model: {modelPath}")

    def _invoke_log_message(self) -> str:
        return "Sending request to local LLM"

    def _wrap_prompt(self, core: str) -> str:
        return f"[INST]{core}[/INST]"
