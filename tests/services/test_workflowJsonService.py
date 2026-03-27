import os
import json
import tempfile
import pytest
from src.services.workflowJsonService import WorkflowJsonService


class TestWorkflowJsonService:
    """Tests for WorkflowJsonService (LOCAL provider)."""

    def setup_method(self):
        self.tempDir = tempfile.mkdtemp()
        self.sampleWorkflow = {
            "description": "Test workflow.",
            "goals": ["Goal 1"],
            "policy": ["Policy 1"],
            "steps": [
                {"id": "step1", "description": "First step."},
                {"id": "step2", "description": "Second step."},
            ],
        }
        filePath = os.path.join(self.tempDir, "test_workflow.json")
        with open(filePath, "w", encoding="utf-8") as f:
            json.dump(self.sampleWorkflow, f)
        os.environ["WORKFLOW_DIR"] = self.tempDir

    def teardown_method(self):
        os.environ.pop("WORKFLOW_DIR", None)

    def test_loadWorkflowSuccess(self):
        service = WorkflowJsonService()
        result = service.loadWorkflow("test_workflow")
        assert result == self.sampleWorkflow

    def test_loadWorkflowNotFound(self):
        service = WorkflowJsonService()
        with pytest.raises(FileNotFoundError):
            service.loadWorkflow("nonexistent")

    def test_loadWorkflowHasCorrectStructure(self):
        service = WorkflowJsonService()
        result = service.loadWorkflow("test_workflow")
        assert "description" in result
        assert "goals" in result
        assert "policy" in result
        assert "steps" in result
        assert len(result["steps"]) == 2
        assert result["steps"][0]["id"] == "step1"
