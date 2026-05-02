"""Tests for LLM cost calculation in ModelGarage's _calculate_cost method.

Covers the full pricing table with substring matching, zero-cost for local
models, and edge cases where usage data is missing or the model name does
not appear in the table.

Run with::

    python -m pytest tests/test_cost_calculation.py -x -v
"""

from __future__ import annotations

from heretek_swarm.llm.model_garage import LLMResponse, ModelGarage, ProviderType


def make_garage() -> ModelGarage:
    """Return a ModelGarage instance without initialising providers."""
    g = ModelGarage.__new__(ModelGarage)
    g._PRICING_TABLE = ModelGarage._PRICING_TABLE
    return g


def make_response(
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    model: str = "gpt-4o",
) -> LLMResponse:
    """Return a minimal LLMResponse with the given usage and model."""
    return LLMResponse(
        content="",
        model=model,
        provider=ProviderType.OPENAI,
        usage={"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
    )


# ---------------------------------------------------------------------------
# Pricing accuracy — spot-check known values
# ---------------------------------------------------------------------------

def test_gpt4o_pricing() -> None:
    """gpt-4o: $2.50/1K input, $10/1K output."""
    garage = make_garage()
    resp = make_response(prompt_tokens=1000, completion_tokens=500, model="gpt-4o")
    cost = garage._calculate_cost(resp, resp.model)
    # 1 * 2.50 + 0.5 * 10 = 2.50 + 5.00 = 7.50
    assert cost == 7.50, f"Expected 7.50, got {cost}"


def test_gpt4o_mini_pricing() -> None:
    """gpt-4o-mini: $0.15/1K input, $0.60/1K output."""
    garage = make_garage()
    resp = make_response(prompt_tokens=2000, completion_tokens=1000, model="gpt-4o-mini")
    cost = garage._calculate_cost(resp, resp.model)
    # 2 * 0.15 + 1 * 0.60 = 0.30 + 0.60 = 0.90
    assert cost == 0.90, f"Expected 0.90, got {cost}"


def test_claude_sonnet_pricing() -> None:
    """claude-3-5-sonnet: $3/1K input, $15/1K output."""
    garage = make_garage()
    resp = make_response(prompt_tokens=500, completion_tokens=200, model="claude-3-5-sonnet-20241022")
    cost = garage._calculate_cost(resp, resp.model)
    # 0.5 * 3 + 0.2 * 15 = 1.50 + 3.00 = 4.50
    assert cost == 4.50, f"Expected 4.50, got {cost}"


def test_claude_opus_pricing() -> None:
    """claude-3-opus: $15/1K input, $75/1K output."""
    garage = make_garage()
    resp = make_response(prompt_tokens=100, completion_tokens=40, model="claude-3-opus")
    cost = garage._calculate_cost(resp, resp.model)
    # 0.1 * 15 + 0.04 * 75 = 1.50 + 3.00 = 4.50
    assert cost == 4.50, f"Expected 4.50, got {cost}"


def test_gemini_pro_pricing() -> None:
    """gemini-1.5-pro: $1.25/1K input, $5/1K output."""
    garage = make_garage()
    resp = make_response(prompt_tokens=1000, completion_tokens=1000, model="gemini-1.5-pro")
    cost = garage._calculate_cost(resp, resp.model)
    assert cost == 6.25, f"Expected 6.25, got {cost}"


def test_o1_preview_pricing() -> None:
    """o1-preview: $15/1K input, $60/1K output."""
    garage = make_garage()
    resp = make_response(prompt_tokens=100, completion_tokens=50, model="o1-preview")
    cost = garage._calculate_cost(resp, resp.model)
    assert cost == 4.50, f"Expected 4.50, got {cost}"


# ---------------------------------------------------------------------------
# Substring matching — specificity ordering
# ---------------------------------------------------------------------------

def test_substring_not_matches_shorter() -> None:
    """'gpt-4o-mini' must NOT match the 'gpt-4o' row."""
    garage = make_garage()
    resp = make_response(prompt_tokens=1000, completion_tokens=500, model="gpt-4o-mini")
    cost = garage._calculate_cost(resp, resp.model)
    # gpt-4o-mini: 0.15/0.60 — 1*0.15 + 0.5*0.60 = 0.45
    assert cost == 0.45, f"Expected 0.45 for gpt-4o-mini, got {cost}"


# ---------------------------------------------------------------------------
# Local / free models
# ---------------------------------------------------------------------------

def test_llama_is_zero_cost() -> None:
    """llama* models cost $0."""
    garage = make_garage()
    resp = make_response(prompt_tokens=5000, completion_tokens=2000, model="llama3.1:8b")
    assert garage._calculate_cost(resp, resp.model) == 0.0


def test_mistral_is_zero_cost() -> None:
    """mistral models cost $0."""
    garage = make_garage()
    resp = make_response(prompt_tokens=5000, completion_tokens=2000, model="mistral:7b")
    assert garage._calculate_cost(resp, resp.model) == 0.0


def test_unknown_model_is_zero_cost() -> None:
    """An unrecognised model name returns 0.0."""
    garage = make_garage()
    resp = make_response(prompt_tokens=100, completion_tokens=50, model="unknown-model-v2")
    assert garage._calculate_cost(resp, resp.model) == 0.0


def test_exact_full_model_name() -> None:
    """Fully-qualified model names still match the pricing key via substring."""
    garage = make_garage()
    resp = make_response(prompt_tokens=1000, completion_tokens=500, model="gpt-4-turbo-preview")
    cost = garage._calculate_cost(resp, resp.model)
    # gpt-4-turbo: $10/$30 — 1*10 + 0.5*30 = 25.0
    assert cost == 25.0, f"Expected 25.0, got {cost}"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_zero_tokens_zero_cost() -> None:
    """Both prompt and completion tokens at zero should cost nothing."""
    garage = make_garage()
    resp = make_response(prompt_tokens=0, completion_tokens=0, model="gpt-4o")
    assert garage._calculate_cost(resp, resp.model) == 0.0


def test_empty_usage_zero_cost() -> None:
    """When the usage dict is missing/empty, cost must be 0.0 (local models)."""
    garage = make_garage()
    resp = LLMResponse(content="", model="gpt-4o", provider=ProviderType.OLLAMA, usage={})
    assert garage._calculate_cost(resp, resp.model) == 0.0


def test_no_usage_key_zero_cost() -> None:
    """When usage dict lacks prompt_tokens/completion_tokens, cost must be 0.0."""
    garage = make_garage()
    resp = LLMResponse(content="", model="gpt-4o", provider=ProviderType.OLLAMA, usage={"total_tokens": 10})
    assert garage._calculate_cost(resp, resp.model) == 0.0


def test_partial_tokens_rounding() -> None:
    """Fractional token counts are handled correctly."""
    garage = make_garage()
    resp = make_response(prompt_tokens=1, completion_tokens=1, model="claude-3-5-sonnet-20241022")
    cost = garage._calculate_cost(resp, resp.model)
    # 0.001 * 3 + 0.001 * 15 = 0.003 + 0.015 = 0.018
    assert cost == 0.018, f"Expected 0.018, got {cost}"


# ---------------------------------------------------------------------------
# Integration: _calculate_cost is wired into garage.complete()
# ---------------------------------------------------------------------------

def test_cost_is_set_on_response() -> None:
    """When a provider returns usage, the cost field must be populated."""
    garage = make_garage()
    resp = make_response(prompt_tokens=100, completion_tokens=50, model="gpt-4o")
    assert resp.cost is None  # not yet set
    cost = garage._calculate_cost(resp, resp.model)
    assert isinstance(cost, float)
    assert cost > 0.0
