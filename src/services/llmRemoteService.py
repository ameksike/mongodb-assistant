import os
import json
import logging
from src.services.llmService import LlmService

logger = logging.getLogger(__name__)


class LlmRemoteService(LlmService):
    """REMOTE provider: Vertex AI Gemini 2.5 Flash via LangChain."""

    def __init__(self):
        from langchain_google_vertexai import ChatVertexAI
        self.llm = ChatVertexAI(
            model_name="gemini-2.5-flash",
            project=os.getenv("GCP_PROJECT_ID"),
            location=os.getenv("GCP_LOCATION", "us-central1"),
        )
        logger.info("LlmRemoteService initialized with Vertex AI Gemini 2.5 Flash")

    def generateResponse(self, context: dict) -> tuple:
        prompt = self._buildPrompt(context)
        logger.info("Sending request to Vertex AI Gemini 2.5 Flash")
        response = self.llm.invoke(prompt)
        return self._parseResponse(response.content, context)

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
            f"You are a conversational assistant analyzing a workflow.\n\n"
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
            f'{{"stepId": "<step_id>", "answers": ["<answer1>", "<answer2>"]}}'
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
