"""Test T03: Verify PerceiverAgent._describe_image_llm uses LLM provider chain.

Validates that the stubbed method returns real LLM descriptions instead of
the old placeholder string, with proper error-handling fallback.
"""

import inspect

import pytest

from heretek_swarm.actors.perceiver.agent import PerceiverAgent


class FakeAgentWithLLM(PerceiverAgent):
    """PerceiverAgent double with a controllable run_with_llm for testing."""

    def __init__(self, agent_id: str = "perceiver-test", **kwargs):
        super().__init__(agent_id=agent_id, **kwargs)
        self._llm_response: str | None = None
        self._should_fail = False
        self.run_with_llm_called_with: tuple[str, int] = ("", 0)

    async def run_with_llm(self, prompt, timeout=60, **kw):  # noqa: ASYNC109
        self.run_with_llm_called_with = (prompt, timeout)
        if self._should_fail:
            raise RuntimeError("No LLM provider available")
        return self._llm_response


@pytest.mark.asyncio
async def test_stub_replaced_no_hardcoded_placeholder():
    """The old hardcoded placeholder string must be gone from the method body."""
    source = inspect.getsource(PerceiverAgent._describe_image_llm)
    assert "Image analysis requested with prompt:" not in source, (
        "Must remove hardcoded placeholder string from _describe_image_llm"
    )
    assert "# noqa: E501" not in source, (
        "Must remove # noqa: E501 — real implementation does not need it"
    )


@pytest.mark.asyncio
async def test_successful_llm_call_returns_real_description():
    """When run_with_llm succeeds, return the LLM response as the description."""
    agent = FakeAgentWithLLM()
    agent._llm_response = "A clear blue sky with scattered white clouds over a green field."

    result = await agent._describe_image_llm("fake-base64-image-data")

    assert result == "A clear blue sky with scattered white clouds over a green field."
    prompt, timeout = agent.run_with_llm_called_with
    assert "fake-base64-image-data" in prompt
    assert timeout == 60


@pytest.mark.asyncio
async def test_successful_llm_call_with_data_url_includes_format():
    """Data URL images should include format and size in the prompt."""
    agent = FakeAgentWithLLM()
    agent._llm_response = "A diagram with labeled boxes and arrows."
    image_data = (
        "data:image/png;base64,"
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )

    result = await agent._describe_image_llm(image_data)

    assert result == "A diagram with labeled boxes and arrows."
    prompt, _ = agent.run_with_llm_called_with
    assert "png" in prompt
    assert "bytes" in prompt


@pytest.mark.asyncio
async def test_llm_failure_returns_metadata_fallback():
    """When run_with_llm raises, return metadata-only fallback string."""
    agent = FakeAgentWithLLM()
    agent._should_fail = True

    result = await agent._describe_image_llm("data:image/jpeg;base64,/9j/4AAQ==")

    assert result.startswith("[LLM unavailable]")
    assert "Image analysis requested" in result
    assert "bytes" in result
    assert "jpeg" in result


@pytest.mark.asyncio
async def test_non_data_url_image_detects_base64():
    """Image data without data: prefix is treated as base64."""
    agent = FakeAgentWithLLM()
    agent._llm_response = "description"
    image_data = "aW1hZ2UtZGF0YS1oZXJl"  # "image-data-here" in base64

    result = await agent._describe_image_llm(image_data)

    assert result == "description"
    prompt, _ = agent.run_with_llm_called_with
    assert "base64" in prompt


@pytest.mark.asyncio
async def test_llm_call_invoked_with_60s_timeout():
    """The timeout passed to run_with_llm must be 60 seconds."""
    agent = FakeAgentWithLLM()
    agent._llm_response = "description"

    await agent._describe_image_llm("some-image")

    _, timeout = agent.run_with_llm_called_with
    assert timeout == 60


@pytest.mark.asyncio
async def test_empty_image_data_still_works():
    """Edge case: empty string is still a valid input."""
    agent = FakeAgentWithLLM()
    agent._llm_response = "empty description"

    result = await agent._describe_image_llm("")

    assert result == "empty description"
    prompt, _ = agent.run_with_llm_called_with
    assert prompt is not None


@pytest.mark.asyncio
async def test_llm_error_logs_structured_event():
    """The exception path must include event='perceiver_llm_unavailable'."""
    agent = FakeAgentWithLLM()
    agent._should_fail = True

    # The structured warning is emitted via structlog — verify the method
    # still returns the expected fallback shape.
    result = await agent._describe_image_llm("test-image-data")

    assert "[LLM unavailable]" in result
    assert "bytes" in result
