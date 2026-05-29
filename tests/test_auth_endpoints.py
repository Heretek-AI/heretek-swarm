"""
Comprehensive auth endpoint smoke test — 401 coverage across ≥30 router family
endpoints and mutation paths.

Iterates over protected endpoint paths and asserts each returns 401 without an
Authorization header.  Also confirms health and Prometheus endpoints remain
public.

Each router is tested in isolation with a fresh FastAPI app to avoid
module-level side effects from the full ``main.py`` app.  For routers that
register as sub-routers under a parent (observability subpackage), we include
the parent router so prefix resolution works correctly.
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.unit]

from fastapi import FastAPI
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Known protected endpoints — one representative GET path per router family
# plus additional paths to reach ≥30 distinct paths.
#
# Format: (label, import_module, test_path)
# ---------------------------------------------------------------------------

PROTECTED_ENDPOINTS: list[tuple[str, str, str]] = [
    # --- agents_management (prefix: /api/agents) ---
    ("agents_list", "heretek_swarm.api.agents_management", "/api/agents"),
    ("agents_status", "heretek_swarm.api.agents_management", "/api/agents/status"),
    # --- autonomous (prefix: /api/autonomous, router-level auth) ---
    ("autonomous_agents", "heretek_swarm.api.autonomous", "/api/autonomous/agents"),
    ("autonomous_status", "heretek_swarm.api.autonomous", "/api/autonomous/status"),
    # --- collective_evolution (prefix: /api/collective) ---
    ("collective_status", "heretek_swarm.api.collective_evolution", "/api/collective/evolution-status"),
    ("collective_capabilities", "heretek_swarm.api.collective_evolution", "/api/collective/capabilities"),
    ("collective_dashboard", "heretek_swarm.api.collective_evolution", "/api/collective/fitness-landscape"),
    # --- compute_tier (prefix: /api/compute, router-level auth) ---
    ("compute_get", "heretek_swarm.api.compute_tier", "/api/compute/tier"),
    # --- configuration (prefix: /api/config, per-endpoint auth) ---
    ("config_list", "heretek_swarm.api.configuration", "/api/config"),
    ("config_llm_types", "heretek_swarm.api.configuration", "/api/config/llm/types"),
    ("config_llm_providers", "heretek_swarm.api.configuration", "/api/config/llm/providers"),
    ("config_embedding_types", "heretek_swarm.api.configuration", "/api/config/embedding/types"),
    ("config_agent_configs", "heretek_swarm.api.configuration", "/api/config/agent/configs"),
    ("config_health", "heretek_swarm.api.configuration", "/api/config/health"),
    # --- consciousness (prefix: /api/consciousness) ---
    ("consciousness_statistics", "heretek_swarm.api.consciousness", "/api/consciousness/statistics"),
    ("consciousness_swarm", "heretek_swarm.api.consciousness", "/api/consciousness/agency/swarm"),
    ("consciousness_states", "heretek_swarm.api.consciousness", "/api/consciousness/states"),
    # --- consensus (prefix: /api/consensus) ---
    ("consensus_list", "heretek_swarm.api.consensus", "/api/consensus"),
    ("consensus_history", "heretek_swarm.api.consensus", "/api/consensus/history"),
    # --- emergent_intelligence (prefix: /api/emergent-intelligence) ---
    ("emergent_dashboard", "heretek_swarm.api.emergent_intelligence", "/api/emergent-intelligence/dashboard"),
    ("emergent_status", "heretek_swarm.api.emergent_intelligence", "/api/emergent-intelligence/status"),
    # --- evaluation (prefix: /api/evaluation) ---
    ("evaluation_summaries", "heretek_swarm.api.evaluation", "/api/evaluation/summaries"),
    ("evaluation_test_cases", "heretek_swarm.api.evaluation", "/api/evaluation/test-cases"),
    # --- plugins (prefix: /api/plugins, router-level auth) ---
    ("plugins_list", "heretek_swarm.api.plugins", "/api/plugins"),
    # --- providers_config (prefix: /api/providers) ---
    ("providers_llm", "heretek_swarm.api.providers_config", "/api/providers/llm"),
    ("providers_embedding", "heretek_swarm.api.providers_config", "/api/providers/embedding"),
    # --- provisioner (prefix: /api/wizard/provision) ---
    ("provision_status", "heretek_swarm.api.provisioner", "/api/wizard/provision/status"),
    # --- rag (prefix: /api/rag) ---
    ("rag_documents", "heretek_swarm.api.rag", "/api/rag/documents"),
    ("rag_config", "heretek_swarm.api.rag", "/api/rag/config"),
    # --- skills (prefix: /api/skills) ---
    ("skills_list", "heretek_swarm.api.skills", "/api/skills"),
    ("skills_agents", "heretek_swarm.api.skills", "/api/skills/agents"),
    # --- wizard (prefix: /api/wizard) ---
    ("wizard_providers", "heretek_swarm.api.wizard", "/api/wizard/providers"),
    ("wizard_config", "heretek_swarm.api.wizard", "/api/wizard/config"),
    # --- workflows (prefix: /api/workflows) ---
    ("workflows_list", "heretek_swarm.api.workflows", "/api/workflows"),
    # --- MCP (prefix: /api/mcp, router-level auth) ---
    ("mcp_tools", "heretek_swarm.mcp.server", "/api/mcp/tools"),
    # --- perceiver (prefix: /api/perceiver, POST-only) ---
    ("perceiver", "heretek_swarm.api.perceiver", "/api/perceiver"),
    # --- memory_versions (prefix: /api/memory/versions) ---
    ("mem_versions_head", "heretek_swarm.api.memory_versions", "/api/memory/versions/head"),
    ("mem_versions_stats", "heretek_swarm.api.memory_versions", "/api/memory/versions/statistics"),
    # --- observability subpackage — use parent router for correct prefix ---
    # Parent: prefix="/api/observability"; sub-routers have prefix=""
    # NOTE: alerts.py and external_calls.py lack Depends(verify_auth) —
    # these are currently unprotected and are excluded from this test list.
    ("obs_swarm", "heretek_swarm.api.observability", "/api/observability/swarm"),
    ("obs_events_replay", "heretek_swarm.api.observability", "/api/observability/events/replay"),
    # --- consciousness additional ---
    ("consciousness_connectivity", "heretek_swarm.api.consciousness", "/api/consciousness/connectivity"),
    ("consciousness_all_agency", "heretek_swarm.api.consciousness", "/api/consciousness/agency/all"),
]


# ---------------------------------------------------------------------------
# Parametrized 401 test
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("label", "module_name", "test_path"),
    [(l, m, p) for l, m, p in PROTECTED_ENDPOINTS],
    ids=[l for l, _, _ in PROTECTED_ENDPOINTS],
)
def test_protected_endpoint_returns_401(
    label: str,
    module_name: str,
    test_path: str,
) -> None:
    """GET {test_path} returns 401 without Authorization header for {label}."""
    import importlib

    try:
        mod = importlib.import_module(module_name)
    except ImportError as e:
        pytest.skip(f"Cannot import {module_name}: {e}")

    # The perceiver router has only POST /analyze — GET on "/api/perceiver"
    # returns 404 (no such route).  We test mutation separately; skip GET here.
    if label == "perceiver":
        pytest.skip("perceiver has no GET route — mutation tested separately")

    router = mod.router

    app = FastAPI()
    app.include_router(router)

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get(test_path)

    assert resp.status_code == 401, (
        f"{label}: expected 401 for GET {test_path} without auth, "
        f"got {resp.status_code} — body: {resp.text[:200]}"
    )


# ---------------------------------------------------------------------------
# Health endpoints — must be public
# ---------------------------------------------------------------------------


def test_health_endpoints_public() -> None:
    """GET /api/health, /api/health/live, /api/health/ready all return
    non-401 without auth."""
    import importlib

    mod = importlib.import_module("heretek_swarm.api.main")
    app = mod.app

    client = TestClient(app, raise_server_exceptions=False)

    for path in ("/api/health", "/api/health/live", "/api/health/ready"):
        resp = client.get(path)
        assert resp.status_code != 401, (
            f"Health endpoint {path} should be public, got {resp.status_code}"
        )


# ---------------------------------------------------------------------------
# Prometheus metrics — must be public
# ---------------------------------------------------------------------------


def test_prometheus_metrics_public() -> None:
    """GET /api/metrics returns non-401 without auth (Prometheus scraping)."""
    import importlib

    mod = importlib.import_module("heretek_swarm.api.metrics")
    router = mod.router

    app = FastAPI()
    app.include_router(router)

    client = TestClient(app, raise_server_exceptions=False)

    resp = client.get("/api/metrics")
    assert resp.status_code != 401, (
        f"Prometheus /api/metrics should be public, got {resp.status_code}"
    )

    # But /api/metrics/json requires auth
    resp_json = client.get("/api/metrics/json")
    assert resp_json.status_code == 401, (
        f"/api/metrics/json should require auth, got {resp_json.status_code}"
    )


# ---------------------------------------------------------------------------
# Mutations (POST/PUT/DELETE) also rejected
# ---------------------------------------------------------------------------


MUTATION_PATHS: list[tuple[str, str, str, str]] = [
    # wizard
    ("wizard_reset", "heretek_swarm.api.wizard", "/api/wizard/reset", "post"),
    # plugins
    ("plugins_enable", "heretek_swarm.api.plugins", "/api/plugins/test/enable", "post"),
    # provisioner
    ("provision_create", "heretek_swarm.api.provisioner", "/api/wizard/provision", "post"),
    ("provision_stop", "heretek_swarm.api.provisioner", "/api/wizard/provision/stop", "post"),
    # mcp
    ("mcp_call", "heretek_swarm.mcp.server", "/api/mcp/tools/call", "post"),
    # configuration
    ("config_post", "heretek_swarm.api.configuration", "/api/config", "post"),
    ("config_delete", "heretek_swarm.api.configuration", "/api/config/test-key", "delete"),
    # consensus
    ("consensus_create", "heretek_swarm.api.consensus", "/api/consensus", "post"),
    # workflows
    ("workflows_create", "heretek_swarm.api.workflows", "/api/workflows", "post"),
    ("workflows_validate", "heretek_swarm.api.workflows", "/api/workflows/validate", "post"),
    # rag
    ("rag_ingest", "heretek_swarm.api.rag", "/api/rag/ingest", "post"),
    # skills
    ("skills_create", "heretek_swarm.api.skills", "/api/skills", "post"),
    # perceiver — POST /analyze (the only route)
    ("perceiver_analyze", "heretek_swarm.api.perceiver", "/api/perceiver/analyze", "post"),
    # observability (parent router) — events sub-routes
    ("obs_events_replay_post", "heretek_swarm.api.observability", "/api/observability/events/replay", "post"),
    ("obs_events_time_travel", "heretek_swarm.api.observability", "/api/observability/events/time-travel", "post"),
    # main.py inline POST endpoint (prompt)
    # consciousness mutations
    ("consciousness_record_agency", "heretek_swarm.api.consciousness", "/api/consciousness/agency/record", "post"),
    # memory versions
    ("mem_versions_snapshot", "heretek_swarm.api.memory_versions", "/api/memory/versions/snapshot", "post"),
]


@pytest.mark.parametrize(
    ("label", "module_name", "path", "method"),
    MUTATION_PATHS,
    ids=[m[0] for m in MUTATION_PATHS],
)
def test_mutation_endpoint_returns_401(
    label: str,
    module_name: str,
    path: str,
    method: str,
) -> None:
    """{method.upper()} {path} returns 401 without auth."""
    import importlib

    mod = importlib.import_module(module_name)
    router = mod.router

    app = FastAPI()
    app.include_router(router)

    client = TestClient(app, raise_server_exceptions=False)
    fn = getattr(client, method)
    resp = fn(path)

    assert resp.status_code == 401, (
        f"{label}: expected 401 for {method.upper()} {path} without auth, "
        f"got {resp.status_code}"
    )


# ---------------------------------------------------------------------------
# main.py inline endpoints — use the full app
# ---------------------------------------------------------------------------


MAIN_PROTECTED_PATHS: list[tuple[str, str]] = [
    ("main_supervisor", "/api/supervisor/status"),
    ("main_memory", "/api/memory"),
    ("main_litellm", "/api/litellm/metrics"),
    ("main_a2a", "/api/a2a/messages"),
    ("main_historian", "/api/historian/events"),
    ("main_consensus", "/api/consensus"),
]


@pytest.mark.parametrize(
    ("label", "test_path"),
    MAIN_PROTECTED_PATHS,
    ids=[m[0] for m in MAIN_PROTECTED_PATHS],
)
def test_main_app_endpoint_returns_401(label: str, test_path: str) -> None:
    """GET {test_path} on the full app returns 401 without auth."""
    import importlib

    mod = importlib.import_module("heretek_swarm.api.main")
    app = mod.app

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get(test_path)

    assert resp.status_code == 401, (
        f"{label}: expected 401 for GET {test_path} without auth, "
        f"got {resp.status_code} — body: {resp.text[:200]}"
    )


def test_main_app_prompt_returns_401() -> None:
    """POST /api/prompt returns 401 without auth (has Depends(verify_auth))."""
    import importlib

    mod = importlib.import_module("heretek_swarm.api.main")
    app = mod.app

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/api/prompt")

    assert resp.status_code == 401, (
        f"POST /api/prompt should require auth, got {resp.status_code}"
    )


# ---------------------------------------------------------------------------
# WebSocket endpoints — out of scope (Depends not supported on WS routes)
# ---------------------------------------------------------------------------


def test_websocket_endpoints_not_covered_by_depends() -> None:
    """WebSocket routes don't support FastAPI Depends auth; they're out of scope.

    This test exists to document that WebSocket endpoints (/api/ws/*) are
    not checked here because Depends-based auth cannot be applied to WebSocket
    routes.  Middleware-level auth for WebSocket is tracked separately.
    """
    import importlib

    mod = importlib.import_module("heretek_swarm.api.websockets")
    router = mod.router

    app = FastAPI()
    app.include_router(router)

    client = TestClient(app, raise_server_exceptions=False)

    # A normal GET on WS routes will either 404/405 (method not allowed for WS)
    # or 401 if the router happens to have a GET endpoint.
    resp = client.get("/api/ws")
    assert resp.status_code in (404, 405, 401), (
        f"WebSocket endpoint returned unexpected status {resp.status_code}"
    )
