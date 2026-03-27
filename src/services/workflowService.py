from abc import ABC, abstractmethod


class WorkflowService(ABC):
    """Abstract interface for workflow loading."""

    @abstractmethod
    def loadWorkflow(self, workflowId: str) -> dict:
        """Load and return a workflow definition by its ID."""
        pass
