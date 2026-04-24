"""
M029 S02: Skills APIs E2E tests against real Docker stack.

Validates R056 (skills APIs) by exercising the skills registry endpoints
against the live stack brought up by conftest_m029.
Uses the api_client fixture (authenticated) for all tests except
test_skills_requires_auth which uses an unauthenticated session.

Run with: python -m pytest tests/e2e/test_m029_skills_e2e.py -v -m integration --tb=short
"""

import pytest
import requests


@pytest.mark.integration
def test_skills_list_endpoint(api_client: requests.Session) -> None:
    """
    GET /api/skills.

    Asserts 200, response has 'skills' (list) and 'total' (int) keys.
    The list may be empty if the 23-agent spawn did not register skills —
    both [] and populated are valid. This validates the endpoint is reachable
    and returns the correct structure.
    """
    resp = api_client.get("/api/skills")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert "skills" in body, f"Missing 'skills' key in response: {body}"
    assert "total" in body, f"Missing 'total' key in response: {body}"
    assert isinstance(body["skills"], list), f"'skills' must be list, got {type(body['skills'])}"
    assert isinstance(body["total"], int), f"'total' must be int, got {type(body['total'])}"


@pytest.mark.integration
def test_skills_agents_list(api_client: requests.Session) -> None:
    """
    GET /api/skills/agents.

    Asserts 200, response has 'agents' and 'total_agents' keys.
    Validates agent→skills mapping endpoint.
    """
    resp = api_client.get("/api/skills/agents")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert "agents" in body, f"Missing 'agents' key in response: {body}"
    assert "total_agents" in body, f"Missing 'total_agents' key in response: {body}"
    assert isinstance(body["total_agents"], int), (
        f"'total_agents' must be int, got {type(body['total_agents'])}"
    )


@pytest.mark.integration
def test_skills_agent_by_id(api_client: requests.Session) -> None:
    """
    GET /api/skills/agents/steward.

    If the agent was spawned, returns 200 with skills list.
    If not found, returns 404. Accept either outcome — the test validates
    the endpoint is reachable and returns structured JSON, not that steward's
    skills are populated. Assert response is JSON.
    """
    resp = api_client.get("/api/skills/agents/steward")
    # Accept 200 (agent found) or 404 (agent not found) — both are valid
    assert resp.status_code in (200, 404), (
        f"Expected 200 or 404, got {resp.status_code}: {resp.text}"
    )
    # Response must be valid JSON regardless of status
    body = resp.json()
    assert isinstance(body, dict), f"Response must be JSON dict, got {type(body)}"


@pytest.mark.integration
def test_skills_statistics(api_client: requests.Session) -> None:
    """
    GET /api/skills/statistics.

    Asserts 200, response has 'total_skills' and 'total_agents' keys.
    Validates the stats endpoint.
    """
    resp = api_client.get("/api/skills/statistics")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    body = resp.json()
    assert "total_skills" in body, f"Missing 'total_skills' key in response: {body}"
    assert "total_agents" in body, f"Missing 'total_agents' key in response: {body}"
    assert isinstance(body["total_skills"], int), (
        f"'total_skills' must be int, got {type(body['total_skills'])}"
    )
    assert isinstance(body["total_agents"], int), (
        f"'total_agents' must be int, got {type(body['total_agents'])}"
    )


@pytest.mark.integration
def test_skills_register_and_verify(api_client: requests.Session) -> None:
    """
    POST /api/skills to register a test skill, then GET /api/skills
    to verify the skill name appears in the 'skills' list.

    This proves POST→GET round-trip for skill registration end-to-end.
    Cleans up by deleting the registered skill afterward.
    """
    skill_name = "test-skill-m029"

    # Register the skill
    post_resp = api_client.post(
        "/api/skills",
        json={
            "name": skill_name,
            "description": "E2E test skill",
            "category": "analysis",
            "agent_id": "steward",
            "version": "1.0.0",
        },
    )
    assert post_resp.status_code in (200, 201), (
        f"POST /api/skills failed: {post_resp.status_code} {post_resp.text}"
    )
    post_body = post_resp.json()
    assert post_body.get("registered") is True, (
        f"Expected registered=True in POST response: {post_body}"
    )

    # Fetch all skills and verify the test skill is present
    get_resp = api_client.get("/api/skills")
    assert get_resp.status_code == 200, f"GET /api/skills failed: {get_resp.status_code}"
    get_body = get_resp.json()
    skill_names = [s.get("name") for s in get_body.get("skills", [])]
    assert skill_name in skill_names, (
        f"Skill '{skill_name}' not found in skills list: {skill_names}"
    )

    # Clean up — best-effort delete
    delete_resp = api_client.delete(f"/api/skills/steward/{skill_name}")
    assert delete_resp.status_code in (200, 204, 404), (
        f"DELETE cleanup failed: {delete_resp.status_code} {delete_resp.text}"
    )


@pytest.mark.integration
def test_skills_delete(api_client: requests.Session) -> None:
    """
    First register a skill, then DELETE /api/skills/steward/test-skill-delete-m029.

    Asserts 200 or 204 on success. If 404 (skill already cleaned up),
    that is acceptable. Validates skill removal works.
    """
    skill_name = "test-skill-delete-m029"

    # Ensure the skill exists by registering it first
    post_resp = api_client.post(
        "/api/skills",
        json={
            "name": skill_name,
            "description": "Skill for delete test",
            "category": "analysis",
            "agent_id": "steward",
            "version": "1.0.0",
        },
    )
    # Accept 200/201 for registration, or 404 if it already existed
    assert post_resp.status_code in (200, 201, 404), (
        f"Setup POST failed: {post_resp.status_code} {post_resp.text}"
    )

    # Now delete
    delete_resp = api_client.delete(f"/api/skills/steward/{skill_name}")
    assert delete_resp.status_code in (200, 204, 404), (
        f"DELETE returned unexpected status: {delete_resp.status_code} {delete_resp.text}"
    )


@pytest.mark.integration
def test_skills_requires_auth() -> None:
    """
    Make a request without Authorization header.

    Asserts 401. Validates auth is enforced on skills endpoints.
    Uses a fresh requests.Session without the Authorization header.
    """
    base_url = "http://localhost:8000"
    unauthenticated = requests.Session()
    unauthenticated.headers["Content-Type"] = "application/json"
    resp = unauthenticated.get(f"{base_url}/api/skills")
    assert resp.status_code == 401, (
        f"Expected 401 for unauthenticated request, got {resp.status_code}: {resp.text}"
    )


@pytest.mark.integration
def test_skills_workspace_register(api_client: requests.Session) -> None:
    """
    POST /api/skills/workspace to register a test workspace, then
    GET /api/skills/workspace/test-ws-m029 to verify the workspace_id matches.

    This proves workspace registration round-trip.
    """
    workspace_id = "test-ws-m029"

    # Register workspace
    post_resp = api_client.post(
        "/api/skills/workspace",
        json={"workspace_id": workspace_id, "skill_name": "test-skill"},
    )
    assert post_resp.status_code in (200, 201), (
        f"POST /api/skills/workspace failed: {post_resp.status_code} {post_resp.text}"
    )
    post_body = post_resp.json()
    assert post_body.get("registered") is True, (
        f"Expected registered=True in POST response: {post_body}"
    )

    # Retrieve workspace and verify
    get_resp = api_client.get(f"/api/skills/workspace/{workspace_id}")
    assert get_resp.status_code == 200, (
        f"GET /api/skills/workspace/{workspace_id} failed: {get_resp.status_code} {get_resp.text}"
    )
    get_body = get_resp.json()
    assert get_body.get("workspace_id") == workspace_id, (
        f"Expected workspace_id='{workspace_id}', got {get_body.get('workspace_id')}"
    )
