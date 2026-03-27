import logging
import os

from langchain_google_genai import ChatGoogleGenerativeAI

from src.services.llmService import LlmService

logger = logging.getLogger(__name__)


class LlmRemoteService(LlmService):
    """REMOTE provider: Gemini via LangChain ``ChatGoogleGenerativeAI`` (Vertex or API key)."""

    defaultModel = "gemini-2.5-flash"

    def __init__(self):
        model = os.getenv("GOOGLE_MODEL_ID", self.defaultModel)
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

        if project:
            self.llm = ChatGoogleGenerativeAI(
                model=model,
                project=project,
                location=location,
            )
            logger.info(
                "LlmRemoteService initialized with ChatGoogleGenerativeAI "
                "(model=%s, project=%s, location=%s)",
                model,
                project,
                location,
            )
        else:
            self.llm = ChatGoogleGenerativeAI(model=model)
            logger.info(
                "LlmRemoteService initialized with ChatGoogleGenerativeAI "
                "(model=%s, developer API / env credentials)",
                model,
            )

    def _invokeLogMessage(self) -> str:
        return "Sending request to Google Generative AI (Gemini)"
