"""Tests for GoalToWorkflowTranslator.

Verifies that:
- Successful LLM response parses into nodes and edges
- Bad JSON triggers the fallback mechanism
- Missing keys in JSON triggers the fallback mechanism
- Exceptions in Metis agent trigger the fallback mechanism
"""

import json
from unittest.mock import AsyncMock

import pytest

from heretek_swarm.goals.models import Goal
from heretek_swarm.goals.translator import GoalToWorkflowTranslator


@pytest.fixture
def mock_metis() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def sample_goal() -> Goal:
    return Goal(
        id="goal-001",
        title="Test Goal",
        description="A goal to test.",
        success_criteria=["Test passing"],
        status="accepted",
    )


@pytest.mark.asyncio
async def test_successful_translation(mock_metis, sample_goal):
    translator = GoalToWorkflowTranslator(mock_metis)

    mock_workflow = {
        "nodes": [{"id": "node_1", "type": "agent_task", "config": {"agent": "coder"}}],
        "edges": [],
    }

    # Mock successful LLM response returning JSON string
    mock_metis.run_with_llm.return_value = json.dumps(mock_workflow)

    workflow = await translator.translate_goal(sample_goal)

    assert "nodes" in workflow
    assert "edges" in workflow
    assert len(workflow["nodes"]) == 1
    assert workflow["nodes"][0]["id"] == "node_1"


@pytest.mark.asyncio
async def test_translation_fallback_on_bad_json(mock_metis, sample_goal):
    translator = GoalToWorkflowTranslator(mock_metis)

    # Mock LLM returning invalid JSON
    mock_metis.run_with_llm.return_value = "This is not JSON at all."

    workflow = await translator.translate_goal(sample_goal)

    assert "nodes" in workflow
    assert "edges" in workflow
    assert len(workflow["nodes"]) == 1
    assert workflow["nodes"][0]["id"] == "fallback_execution_node"


@pytest.mark.asyncio
async def test_translation_fallback_on_missing_keys(mock_metis, sample_goal):
    translator = GoalToWorkflowTranslator(mock_metis)

    # Mock LLM returning JSON missing "nodes" and "edges"
    mock_metis.run_with_llm.return_value = '{"some_other_key": "value"}'

    workflow = await translator.translate_goal(sample_goal)

    assert len(workflow["nodes"]) == 1
    assert workflow["nodes"][0]["id"] == "fallback_execution_node"


@pytest.mark.asyncio
async def test_translation_fallback_on_exception(mock_metis, sample_goal):
    translator = GoalToWorkflowTranslator(mock_metis)

    # Mock LLM raising exception
    mock_metis.run_with_llm.side_effect = Exception("API Error")

    workflow = await translator.translate_goal(sample_goal)

    assert len(workflow["nodes"]) == 1
    assert workflow["nodes"][0]["id"] == "fallback_execution_node"
