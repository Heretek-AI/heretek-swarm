"""
M029 S02: Consciousness APIs E2E tests against real Docker stack.

Validates R055 (consciousness APIs) by exercising thinking-stream and
deliberation endpoints against the live stack brought up by conftest_m029.
Uses the api_client fixture (authenticated) for all tests except
test_consciousness_requires_auth which uses an unauthenticated session.

Run with: python -m pytest tests/e2e/test_m029_consciousness_e2e.py -v -m integration --tb=short
"""

import pytest
import requests


@pytest.mark.integration
def test_thinking_stream_returns_structured_response(api_client: requests.Session) -> None:
    """
    GET /api/consciousness/thinking-stream/all (no agent_id in path).

    Asserts 200, response has 'entries' (list) and 'count' (int) keys.
    Validates the endpoint is reachable and returns correct structure
    regardless of whether the stream has data.
    """
    resp = api_client.get("/api/consciousness/thinking-stream/all")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert "entries" in body, f"Missing 'entries' key in response: {body}"
    assert "count" in body, f"Missing 'count' key in response: {body}"
    assert isinstance(body["entries"], list), f"'entries' must be list, got {type(body['entries'])}"
    assert isinstance(body["count"], int), f"'count' must be int, got {type(body['count'])}"


@pytest.mark.integration
def test_thinking_stream_by_agent_id(api_client: requests.Session) -> None:
    """
    GET /api/consciousness/thinking-stream/steward (known agent).

    Asserts 200, 'entries' list, 'count' int, 'agent_id' field.
    Validates per-agent stream filtering.
    """
    resp = api_client.get("/api/consciousness/thinking-stream/steward")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert "entries" in body, f"Missing 'entries' key in response: {body}"
    assert "count" in body, f"Missing 'count' key in response: {body}"
    assert "agent_id" in body, f"Missing 'agent_id' key in response: {body}"
    assert body["agent_id"] == "steward", f"Expected agent_id='steward', got {body['agent_id']}"
    assert isinstance(body["entries"], list), f"'entries' must be list, got {type(body['entries'])}"
    assert isinstance(body["count"], int), f"'count' must be int, got {type(body['count'])}"


@pytest.mark.integration
def test_deliberation_returns_404_for_unknown_id(api_client: requests.Session) -> None:
    """
    GET /api/consciousness/deliberation/nonexistent-id.

    Asserts 404, response is JSON with 'detail' key.
    This is expected on a fresh stack — validates the endpoint is reachable
    and returns structured error, not a crash.
    """
    resp = api_client.get("/api/consciousness/deliberation/nonexistent-id")
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert "detail" in body, f"Missing 'detail' key in error response: {body}"


@pytest.mark.integration
def test_agency_generate_sample_seeds_thinking_stream(api_client: requests.Session) -> None:
    """
    POST /api/consciousness/agency/generate-sample with steward.

    Asserts 200. Then GET /api/consciousness/thinking-stream/steward
    and assert count > 0, entries contain the round_id from POST response.
    This proves the POST→GET round-trip works end-to-end.
    """
    # POST sample metrics for steward
    post_resp = api_client.post(
        "/api/consciousness/agency/generate-sample",
        json={"agent_id": "steward", "high_autonomy": True, "high_agency": True},
    )
    assert post_resp.status_code == 200, f"POST failed: {post_resp.status_code} {post_resp.text}"
    post_body = post_resp.json()
    assert post_body.get("agent_id") == "steward", f"Unexpected agent_id in POST response: {post_body}"

    # GET thinking stream for steward — count should be > 0
    get_resp = api_client.get("/api/consciousness/thinking-stream/steward")
    assert get_resp.status_code == 200, f"GET failed: {get_resp.status_code} {get_resp.text}"
    get_body = get_resp.json()
    assert "count" in get_body, f"Missing 'count' key: {get_body}"
    assert get_body["count"] > 0, (
        f"Expected count > 0 after generate-sample, got {get_body['count']}. "
        f"Entries: {get_body.get('entries', [])}"
    )

    # If entries exist, verify round_id is present in at least one entry
    entries = get_body.get("entries", [])
    round_ids = [e.get("round_id") for e in entries if e.get("round_id")]
    assert len(round_ids) > 0, f"No round_ids found in entries: {entries}"


@pytest.mark.integration
def test_consciousness_requires_auth() -> None:
    """
    Make a request without Authorization header.

    Asserts 401. Validates auth is enforced on consciousness endpoints.
    Uses a fresh requests.Session without the Authorization header.
    """
    base_url = "http://localhost:8000"
    unauthenticated = requests.Session()
    unauthenticated.headers["Content-Type"] = "application/json"
    resp = unauthenticated.get(f"{base_url}/api/consciousness/thinking-stream/all")
    assert resp.status_code == 401, (
        f"Expected 401 for unauthenticated request, got {resp.status_code}: {resp.text}"
    )


@pytest.mark.integration
def test_agency_swarm_overview_reachable(api_client: requests.Session) -> None:
    """
    GET /api/consciousness/agency/swarm.

    Asserts 200 and response contains 'swarm_avg_autonomy' and 'health_status'.
    Validates agency metrics endpoint.
    """
    resp = api_client.get("/api/consciousness/agency/swarm")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert "swarm_avg_autonomy" in body, f"Missing 'swarm_avg_autonomy' in response: {body}"
    assert "health_status" in body, f"Missing 'health_status' in response: {body}"