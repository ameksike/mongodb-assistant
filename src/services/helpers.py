import json
import logging

logger = logging.getLogger(__name__)


class ResponseParser:
    """Utility class for parsing LLM JSON responses."""

    @staticmethod
    def parseJson(content: str, maxAnswers: int) -> tuple:
        """Parse a JSON string from LLM output and return (stepId, answers)."""
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        try:
            data = json.loads(cleaned)
            stepId = data["stepId"]
            answers = data["answers"][:maxAnswers]
            return stepId, answers
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            raise ValueError(f"Invalid LLM response format: {e}")
