"""
Negative-path auth bypass tests for all 8 router families.

FINDING-050 requires one endpoint per router family verified to return
HTTP 401 when no auth is provided. Uses FastAPI TestClient without
dependency_overrides for verify_auth — the actual auth layer is tested.

Each router family enforces auth at the router level via
``dependencies=[Depends(verify_auth)]``, so unauthenticated requests
are rejected before endpoint logic runs.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Router family tuples: (label, import_module, router_prefix, test_path)
# ---------------------------------------------------------------------------

ROUTER_FAMILIES: list[tuple[str, str, str, str]] = [
    ("wizard", "heretek_swarm.api.wizard", "/api/wizard", "/api/wizard/providers"),
    (
        "providers_config",
        "heretek_swarm.api.providers_config",
        "/api/providers",
        "/api/providers/llm",
    ),
    ("plugins", "heretek_swarm.api.plugins", "/api/plugins", "/api/plugins"),
    (
        "collective_evolution",
        "heretek_swarm.api.collective_evolution",
        "/api/collective",
        "/api/collective/evolution-status",
    ),
    (
        "autonomous",
        "heretek_swarm.api.autonomous",
        "/api/autonomous",
        "/api/autonomous/agents",
    ),
    (
        "provisioner",
        "heretek_swarm.api.provisioner",
        "/api/wizard/provision",
        "/api/wizard/provision/status",
    ),
    ("metrics", "heretek_swarm.api.metrics", "/api/metrics", "/api/metrics"),
    ("mcp", "heretek_swarm.mcp.server", "/api/mcp", "/api/mcp/tools"),
]


# ---------------------------------------------------------------------------
# Tests — one per router family
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("label", "module_name", "_prefix", "test_path"),
    ROUTER_FAMILIES,
    ids=[label for label, _, _, _ in ROUTER_FAMILIES],
)
def test_auth_bypass_returns_401(
    label: str,
    module_name: str,
    _prefix: str,
    test_path: str,
) -> None:
    """Verify GET {test_path} returns 401 without auth for {label} router."""
    import importlib

    mod = importlib.import_module(module_name)
    router = mod.router

    app = FastAPI()
    app.include_router(router)

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get(test_path)

    assert resp.status_code == 401, (
        f"{label}: expected 401 for GET {test_path} without auth, "
        f"got {resp.status_code}"
    )


# ---------------------------------------------------------------------------
# Additional negative-path: verify POST/PUT/DELETE also reject
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("label", "module_name", "path", "method"),
    [
        # wizard
        ("wizard_reset", "heretek_swarm.api.wizard", "/api/wizard/reset", "post"),
        # plugins
        ("plugins_enable", "heretek_swarm.api.plugins", "/api/plugins/test/enable", "post"),
        # provisioner
        ("provisioner_create", "heretek_swarm.api.provisioner", "/api/wizard/provision", "post"),
        # mcp
        ("mcp_call", "heretek_swarm.mcp.server", "/api/mcp/tools/call", "post"),
    ],
)
def test_auth_bypass_mutation_returns_401(
    label: str,
    module_name: str,
    path: str,
    method: str,
) -> None:
    """Verify {method.upper()} {path} returns 401 without auth for {label}."""
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
