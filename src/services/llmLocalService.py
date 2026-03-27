import os
import json
import logging
from src.services.helpers import coerceLlmContentToStr
from src.services.llmService import LlmService

logger = logging.getLogger(__name__)


class LlmLocalService(LlmService):
    """LOCAL provider: GGUF model loaded via llama-cpp-python + LangChain."""

    def __init__(self):
        from langchain_community.llms import LlamaCpp
        modelPath = os.getenv(
            "LOCAL_MODEL_PATH",
            "models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
        )
        self.llm = LlamaCpp(
            model_path=modelPath,
            n_ctx=int(os.getenv("LOCAL_MODEL_N_CTX", "4096")),
            n_threads=int(os.getenv("LOCAL_MODEL_N_THREADS", "4")),
            temperature=float(os.getenv("LOCAL_MODEL_TEMPERATURE", "0.7")),
            verbose=False,
        )
        logger.info(f"LlmLocalService initialized with model: {modelPath}")

    def generateResponse(self, context: dict) -> tuple:
        prompt = self._buildPrompt(context)
        logger.info("Sending request to local LLM")
        response = self.llm.invoke(prompt)
        raw = response.content if hasattr(response, "content") else response
        return self._parseResponse(coerceLlmContentToStr(raw), context)

    def _buildPrompt(self, context: dict) -> str:
        workflow = context["workflow"]
        conversation = context["conversation"]
        maxAnswers = context["maxAnswers"]

        stepsText = "\n".join(
            f"  - {s['id']}: {s['description']}" for s in workflow["steps"]
        )
        goalsText = "\n".join(f"  - {g}" for g in workflow["goals"])
        policyText = "\n".join(f"  - {p}" for p in workflow["policy"])
        conversationText = "\n".join(
            f"  {m['role']}: {m['message']}" for m in conversation
        )

        return (
            f"[INST] You are a conversational assistant analyzing a workflow.\n\n"
            f"Workflow: {workflow['description']}\n\n"
            f"Goals:\n{goalsText}\n\n"
            f"Policies:\n{policyText}\n\n"
            f"Steps:\n{stepsText}\n\n"
            f"Conversation so far:\n{conversationText}\n\n"
            f"Based on the conversation, determine:\n"
            f"1. The current active step ID from the workflow steps.\n"
            f"2. Generate exactly {maxAnswers} suggested user responses that align "
            f"with the workflow goals and policies.\n\n"
            f"Respond ONLY with valid JSON in this format:\n"
            f'{{"stepId": "<step_id>", "answers": ["<answer1>", "<answer2>"]}} [/INST]'
        )

    def _parseResponse(self, content: str, context: dict) -> tuple:
        try:
            cleaned = content.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
                cleaned = cleaned.rsplit("```", 1)[0]
            data = json.loads(cleaned)
            stepId = data["stepId"]
            answers = data["answers"][:context["maxAnswers"]]
            return stepId, answers
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            raise ValueError(f"Invalid LLM response format: {e}")
