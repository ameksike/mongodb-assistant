import logging
import os

from src.services.llmService import LlmService
from src.services.workflowService import WorkflowService

logger = logging.getLogger(__name__)


class ServiceFactory:
    """Resolves concrete service implementations based on environment configuration."""

    @staticmethod
    def getWorkflowService() -> WorkflowService:
        provider = os.getenv("WORKFLOW_PROVIDER", "JSON")
        logger.info(f"Resolving WorkflowService for provider: {provider}")
        if provider == "MDB":
            from src.services.workflowMdbService import WorkflowMdbService

            return WorkflowMdbService()
        from src.services.workflowJsonService import WorkflowJsonService

        return WorkflowJsonService()

    @staticmethod
    def getLlmService() -> LlmService:
        provider = os.getenv("LLM_PROVIDER", "LOCAL")
        logger.info(f"Resolving LlmService for provider: {provider}")
        if provider == "REMOTE":
            from src.services.llmRemoteService import LlmRemoteService

            return LlmRemoteService()
        from src.services.llmLocalService import LlmLocalService

        return LlmLocalService()
