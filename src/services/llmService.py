import logging
from abc import ABC, abstractmethod

from src.services.helpers import (
    WorkflowPromptParts,
    coerceLlmContentToStr,
    parse_workflow_llm_response,
)

logger = logging.getLogger(__name__)


class LlmService(ABC):
    """LLM workflow assistant: shared prompt, parsing, and invoke orchestration.

    Subclasses set ``self.llm`` (LangChain runnable with ``.invoke``) and implement
    :meth:`_invoke_log_message`. Override :meth:`_wrap_prompt` for instruction
    formats (e.g. Mistral ``[INST]`` … ``[/INST]``).
    """

    def generateResponse(self, context: dict) -> tuple:
        """Return ``(stepId, answers, error)``; see subclass docstrings."""
        early = self._validate_context(context)
        if early is not None:
            return early

        max_answers = context.get("maxAnswers", 2)
        prompt = self._buildPrompt(context)
        logger.info(self._invoke_log_message())
        response = self.llm.invoke(prompt)
        raw = response.content if hasattr(response, "content") else response
        text = coerceLlmContentToStr(raw)
        return self._parseModelOutput(text, max_answers)

    @staticmethod
    def _validate_context(context: dict) -> tuple[str, list[str], str] | None:
        workflow = context.get("workflow")
        conversation = context.get("conversation")
        max_answers = context.get("maxAnswers", 2)
        if not isinstance(workflow, dict):
            return "", [], "Invalid assistant context: workflow is missing."
        if not isinstance(conversation, list):
            return "", [], "Invalid assistant context: conversation is missing."
        if not isinstance(max_answers, int) or max_answers < 1:
            return (
                "",
                [],
                "Invalid assistant context: maxAnswers must be a positive integer.",
            )
        return None

    def _buildPrompt(self, context: dict) -> str:
        core = self._build_prompt_core(context)
        return self._wrap_prompt(core)

    def _wrap_prompt(self, core: str) -> str:
        return core

    def _build_prompt_core(self, context: dict) -> str:
        workflow = context["workflow"]
        conversation = context["conversation"]
        max_answers = context.get("maxAnswers", 2)
        if not isinstance(max_answers, int) or max_answers < 1:
            max_answers = 2

        steps_text = "\n".join(WorkflowPromptParts.bullet_lines(workflow, "steps"))
        goals_text = "\n".join(WorkflowPromptParts.bullet_lines(workflow, "goals"))
        policy_text = "\n".join(WorkflowPromptParts.bullet_lines(workflow, "policies"))
        conversation_text = "\n".join(
            WorkflowPromptParts.conversation_lines(conversation)
        )
        description = WorkflowPromptParts.description(workflow)

        return (
            f"You are a conversational assistant analyzing a workflow.\n\n"
            f"Workflow: {description}\n\n"
            f"Goals:\n{goals_text}\n\n"
            f"Policies:\n{policy_text}\n\n"
            f"Steps:\n{steps_text}\n\n"
            f"Conversation so far:\n{conversation_text}\n\n"
            f"Based on the conversation, determine:\n"
            f"1. The current active step ID from the workflow steps.\n"
            f"2. Generate exactly {max_answers} suggested user responses that align "
            f"with the workflow goals and policies.\n\n"
            f"You MUST output exactly one JSON object. Do not add markdown, comments, "
            f"or any text before or after the JSON.\n\n"
            f'On success, use this shape. The "answers" array MUST contain exactly '
            f"{max_answers} strings:\n"
            f'{{"stepId": "<step_id>", "answers": ["<answer1>", ...]}}\n\n'
            f"If you cannot comply (ambiguous conversation, missing information, policy "
            f"conflict, or any uncertainty), do NOT invent a stepId or filler answers. "
            f"Use ONLY this shape so the client can show your message to the user:\n"
            f'{{"error": "<short clear message in the same language as the conversation>"}}\n'
            f'In the error form, omit "stepId" and "answers", or set them to null.\n\n'
            f"Never return an empty response. Escape double quotes inside strings."
        )

    @staticmethod
    def _parseModelOutput(
        text: str, max_answers: int
    ) -> tuple[str, list[str], str | None]:
        return parse_workflow_llm_response(text, max_answers)

    @abstractmethod
    def _invoke_log_message(self) -> str:
        """Log line when sending a prompt to the provider-specific model."""
