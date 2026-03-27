import logging
import os

from langchain_google_genai import ChatGoogleGenerativeAI

from src.services.llmService import LlmService

logger = logging.getLogger(__name__)


class LlmRemoteService(LlmService):
    """REMOTE provider: Gemini via LangChain ``ChatGoogleGenerativeAI`` (Vertex or API key)."""

    defaultModel = "gemini-2.5-flash"

    def __init__(self):
        self.modelId = os.getenv("GOOGLE_MODEL_ID", self.defaultModel)
        self.project = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

        if self.project:
            self.llm = ChatGoogleGenerativeAI(
                model=self.modelId,
                project=self.project,
                location=self.location,
            )
            logger.info(
                "LlmRemoteService initialized with ChatGoogleGenerativeAI "
                "(model=%s, project=%s, location=%s)",
                self.modelId,
                self.project,
                self.location,
            )
        else:
            self.llm = ChatGoogleGenerativeAI(model=self.modelId)
            logger.info(
                "LlmRemoteService initialized with ChatGoogleGenerativeAI "
                "(model=%s, developer API / env credentials)",
                self.modelId,
            )

    def startupInfo(self) -> dict:
        info = super().startupInfo()
        info["provider"] = "REMOTE"
        info["modelId"] = self.modelId
        info["location"] = self.location
        if self.project:
            info["project"] = self.project
        return info

    def _invokeLogMessage(self) -> str:
        return "Sending request to Google Generative AI (Gemini)"
