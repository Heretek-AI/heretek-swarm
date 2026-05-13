"""Tests for GoalProposer — prompt generation and LLM response parsing.

Verifies that:
- generate_proposal_prompt() returns a non-empty, structured prompt
- proposal_system_prompt() returns the Metis system prompt
- parse_llm_response() correctly parses valid JSON
- parse_llm_response() handles JSON wrapped in markdown code fences
- parse_llm_response() handles LLM commentary around JSON
- parse_llm_response() returns _parse_error for empty/blank responses
- parse_llm_response() returns _parse_error when no JSON object is found
- parse_llm_response() returns _parse_error for malformed JSON
- parse_llm_response() returns _parse_error for missing required keys
- parse_llm_response() returns _parse_error for invalid field types
"""

from __future__ import annotations

import pytest

from heretek_swarm.goals.models import Goal
from heretek_swarm.goals.proposer import GoalProposer

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def valid_llm_response() -> str:
    """A well-formed LLM response with exactly the required keys."""
    return """\
{"title": "Improve Cross-Agent Knowledge Sharing", "description": "Enable agents to share observations and learnings via a common knowledge base, reducing redundant computation and improving collective intelligence.", "success_criteria": ["All agents can publish to the knowledge base", "Queries return relevant results within 2 seconds", "Knowledge base has >80% accuracy after 100 queries"], "estimated_node_types": ["llm", "agent", "io"]}"""


@pytest.fixture
def fenced_llm_response() -> str:
    """LLM response wrapped in ```json ... ``` fences."""
    return """```json
{"title": "Add Real-Time Monitoring", "description": "Build a dashboard showing agent health and message latency in real time.", "success_criteria": ["Dashboard renders within 1s", "All agents report health every 5s"], "estimated_node_types": ["agent", "tool"]}  # noqa: E501
```"""


@pytest.fixture
def verbose_llm_response() -> str:
    """LLM response with commentary before and after the JSON."""
    return """Here is a strategic goal for the swarm:

{"title": "Decentralize Decision Making", "description": "Gradually distribute authority so that routine decisions no longer require Steward approval, increasing throughput and reducing bottleneck risk.", "success_criteria": ["50% of decisions are autonomous after 2 days", "No increase in error rate after delegation", "Steward approval queue drops below 10 items"], "estimated_node_types": ["decision", "agent", "parallel"]}  # noqa: E501

I hope this aligns with the swarm's current priorities!"""


# ---------------------------------------------------------------------------
# Prompt generation tests
# ---------------------------------------------------------------------------


class TestGoalProposerPrompt:
    """Tests for GoalProposer prompt generation."""

    def test_generate_proposal_prompt_returns_non_empty_string(self):
        """The proposal prompt is a non-empty string."""
        prompt = GoalProposer.generate_proposal_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_generate_proposal_prompt_contains_required_keys(self):
        """The prompt instructs the LLM to include all required fields."""
        prompt = GoalProposer.generate_proposal_prompt()
        assert "title" in prompt
        assert "description" in prompt
        assert "success_criteria" in prompt
        assert "estimated_node_types" in prompt

    def test_proposal_system_prompt_returns_string(self):
        """The system prompt is a non-empty string mentioning Metis."""
        sp = GoalProposer.proposal_system_prompt()
        assert isinstance(sp, str)
        assert len(sp) > 0
        assert "Metis" in sp


# ---------------------------------------------------------------------------
# Response parsing tests — happy path
# ---------------------------------------------------------------------------


class TestGoalProposerParseHappy:
    """Tests for parse_llm_response() with valid inputs."""

    def test_parse_valid_json(self, valid_llm_response):
        """Parses a clean JSON response into a goal-creation dict."""
        result = GoalProposer.parse_llm_response(valid_llm_response)
        assert "_parse_error" not in result
        assert result["title"] == "Improve Cross-Agent Knowledge Sharing"
        assert "knowledge base" in result["description"]
        assert len(result["success_criteria"]) == 3
        assert "llm" in result["estimated_node_types"]

    def test_parse_fenced_json(self, fenced_llm_response):
        """Extracts JSON from ```json ... ``` code fences."""
        result = GoalProposer.parse_llm_response(fenced_llm_response)
        assert "_parse_error" not in result
        assert result["title"] == "Add Real-Time Monitoring"
        assert len(result["estimated_node_types"]) == 2

    def test_parse_verbose_response(self, verbose_llm_response):
        """Extracts JSON even when surrounding commentary is present."""
        result = GoalProposer.parse_llm_response(verbose_llm_response)
        assert "_parse_error" not in result
        assert result["title"] == "Decentralize Decision Making"
        assert "Steward" in result["description"]

    def test_parsed_result_can_build_goal(self, valid_llm_response):
        """The output of parse_llm_response can be fed directly to Goal()."""
        result = GoalProposer.parse_llm_response(valid_llm_response)
        goal = Goal(
            id="goal-test-001",
            title=result["title"],
            description=result["description"],
            success_criteria=result["success_criteria"],
            estimated_node_types=result["estimated_node_types"],
            status="proposed",
        )
        assert goal.title == "Improve Cross-Agent Knowledge Sharing"
        assert goal.status == "proposed"


# ---------------------------------------------------------------------------
# Response parsing tests — error paths
# ---------------------------------------------------------------------------


class TestGoalProposerParseErrors:
    """Tests for parse_llm_response() error handling."""

    def test_empty_response_returns_parse_error(self):
        """An empty string returns _parse_error=True."""
        result = GoalProposer.parse_llm_response("")
        assert result.get("_parse_error") is True
        assert "Empty LLM response" in result["error"]

    def test_whitespace_only_returns_parse_error(self):
        """A whitespace-only string returns _parse_error=True."""
        result = GoalProposer.parse_llm_response("   \n  \t  ")
        assert result.get("_parse_error") is True
        assert "Empty LLM response" in result["error"]

    def test_no_json_found_returns_parse_error(self):
        """A response with no JSON object returns _parse_error."""
        result = GoalProposer.parse_llm_response("Just some prose, no JSON here!")
        assert result.get("_parse_error") is True
        assert "No JSON object found" in result["error"]

    def test_malformed_json_returns_parse_error(self):
        """A malformed JSON string with balanced braces but invalid syntax returns _parse_error."""
        result = GoalProposer.parse_llm_response(
            '{"title": "Broken", "description": "Has a trailing comma", "success_criteria": [],}'
        )
        assert result.get("_parse_error") is True
        assert "JSON decode failed" in result["error"]

    def test_missing_title_returns_parse_error(self):
        """Missing 'title' key triggers a validation error."""
        result = GoalProposer.parse_llm_response(
            '{"description": "No title here", "success_criteria": [], "estimated_node_types": []}'
        )
        assert result.get("_parse_error") is True
        assert "title" in result["error"]

    def test_missing_description_returns_parse_error(self):
        """Missing 'description' key triggers a validation error."""
        result = GoalProposer.parse_llm_response(
            '{"title": "No desc", "success_criteria": [], "estimated_node_types": []}'
        )
        assert result.get("_parse_error") is True
        assert "description" in result["error"]

    def test_empty_title_returns_parse_error(self):
        """An empty or whitespace-only title triggers a validation error."""
        result = GoalProposer.parse_llm_response(
            '{"title": "   ", "description": "Valid desc", "success_criteria": ["a"], "estimated_node_types": ["b"]}'
        )
        assert result.get("_parse_error") is True

    def test_success_criteria_not_list_returns_parse_error(self):
        """success_criteria must be a list, not a string."""
        result = GoalProposer.parse_llm_response(
            '{"title": "X", "description": "Y", "success_criteria": "not a list", "estimated_node_types": []}'
        )
        assert result.get("_parse_error") is True
        assert "success_criteria" in result["error"]

    def test_non_string_criteria_items(self):
        """All items in success_criteria must be strings."""
        result = GoalProposer.parse_llm_response(
            '{"title": "X", "description": "Y", "success_criteria": [1, 2, 3], "estimated_node_types": []}'
        )
        assert result.get("_parse_error") is True

    def test_estimated_node_types_not_list(self):
        """estimated_node_types must be a list."""
        result = GoalProposer.parse_llm_response(
            '{"title": "X", "description": "Y", "success_criteria": [], "estimated_node_types": "llm"}'
        )
        assert result.get("_parse_error") is True
        assert "estimated_node_types" in result["error"]

    def test_partial_returned_on_validation_error(self):
        """When validation fails, _partial key contains what we parsed."""
        result = GoalProposer.parse_llm_response(
            '{"title": "Valid Title", "description": "Valid Desc", "success_criteria": [], "estimated_node_types": "bad"}'
        )
        assert result.get("_parse_error") is True
        assert "_partial" in result
        assert result["_partial"]["title"] == "Valid Title"
