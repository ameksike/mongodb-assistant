from abc import ABC, abstractmethod


class LlmService(ABC):
    """Abstract interface for LLM interaction."""

    @abstractmethod
    def generateResponse(self, context: dict) -> tuple:
        """Return (stepId, answers) based on workflow context and conversation."""
        pass
