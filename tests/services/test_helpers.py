import pytest
from src.services.helpers import (
    ResponseParser,
    coerceLlmContentToStr,
    workflow_policy_items,
)


class TestResponseParser:
    """Tests for ResponseParser utility."""

    def test_parseJsonValid(self):
        content = '{"stepId": "step1", "answers": ["Answer 1", "Answer 2"]}'
        stepId, answers = ResponseParser.parseJson(content, 2)
        assert stepId == "step1"
        assert answers == ["Answer 1", "Answer 2"]

    def test_parseJsonWithCodeBlock(self):
        content = '```json\n{"stepId": "step1", "answers": ["Answer 1"]}\n```'
        stepId, answers = ResponseParser.parseJson(content, 2)
        assert stepId == "step1"
        assert answers == ["Answer 1"]

    def test_parseJsonTruncatesAnswers(self):
        content = '{"stepId": "step1", "answers": ["A1", "A2", "A3"]}'
        stepId, answers = ResponseParser.parseJson(content, 2)
        assert len(answers) == 2

    def test_parseJsonInvalidJson(self):
        with pytest.raises(ValueError):
            ResponseParser.parseJson("not json", 2)

    def test_parseJsonMissingKey(self):
        with pytest.raises(ValueError):
            ResponseParser.parseJson('{"wrong": "format"}', 2)


class TestWorkflowPolicyItems:
    def test_prefers_policies_key(self):
        assert workflow_policy_items({"policies": ["a"], "policy": ["b"]}) == ["a"]

    def test_falls_back_to_policy(self):
        assert workflow_policy_items({"policy": ["x"]}) == ["x"]

    def test_empty_when_missing(self):
        assert workflow_policy_items({}) == []


class TestCoerceLlmContentToStr:
    def test_strUnchanged(self):
        assert coerceLlmContentToStr("hello") == "hello"

    def test_noneBecomesEmpty(self):
        assert coerceLlmContentToStr(None) == ""

    def test_listOfTextDicts(self):
        parts = [{"type": "text", "text": '{"stepId": "a", "answers": []}'}]
        assert "stepId" in coerceLlmContentToStr(parts)
