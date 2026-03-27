import json
import logging
import os

from src.services.workflowService import WorkflowService

logger = logging.getLogger(__name__)


class WorkflowJsonService(WorkflowService):
    """LOCAL provider: loads workflow definitions from JSON files in cfg/workflows/."""

    def __init__(self):
        self.workflowDir = os.getenv("WORKFLOW_DIR", "cfg/workflows")
        logger.info(
            f"WorkflowJsonService initialized with directory: {self.workflowDir}"
        )

    def loadWorkflow(self, workflowId: str) -> dict:
        filePath = os.path.join(self.workflowDir, f"{workflowId}.json")
        logger.info(f"Loading workflow from: {filePath}")
        with open(filePath, encoding="utf-8") as f:
            return json.load(f)
