import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def coerceLlmContentToStr(content: Any) -> str:
    """Turn chat-model output content into a single string (LC 1.x / Gemini may use list parts)."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if text is not None:
                    parts.append(str(text))
                else:
                    parts.append(str(item))
            else:
                parts.append(str(item))
        return "".join(parts)
    return str(content)


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
