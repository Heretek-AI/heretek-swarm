"""
API Wiring Smoke Tests

Mechanical import and route-count checks for each of the 5 API routers
plus the WebSocket ConnectionManager. Verify each router can be imported
without error, has the expected prefix, and has a non-trivial number of
routes (stubs would have 0-1 routes).

Implements T01: Create API wiring smoke tests — Milestone M020, Slice S02.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest


# Project layout:
#   /home/john/Projects/heretek-swarm/                   ← project root (parents[2])
#     heretek-swarm/
#       heretek_swarm/
#         api/
#           consciousness.py
#           skills.py
#           ...
#         __init__.py
#   tests/
#     audit/
#       test_api_wiring.py
SRC_ROOT = Path(__file__).resolve().parents[2]  # → /home/john/Projects/heretek-swarm
# Source root includes the heretek_swarm package dir itself, so rel_path
# values should NOT include the heretek_swarm/ prefix.
HERETEK_SRC = SRC_ROOT / "heretek-swarm" / "heretek_swarm"  # → .../heretek-swarm/heretek_swarm


# Ensure the source root is on sys.path so heretek_swarm imports resolve
if str(SRC_ROOT / "heretek-swarm") not in sys.path:
    sys.path.insert(0, str(SRC_ROOT / "heretek-swarm"))


class TestRouterImports:
    """Verify each router module can be imported without error."""

    @pytest.mark.parametrize(
        "module_path,expected_prefix",
        [
            ("heretek_swarm.api.consciousness", "/api/consciousness"),
            ("heretek_swarm.api.skills", "/api/skills"),
            ("heretek_swarm.api.workflows", "/api/workflows"),
            ("heretek_swarm.api.memory_versions", "/api/memory/versions"),
            ("heretek_swarm.api.rag", "/api/rag"),
        ],
    )
    def test_api_router_imports(self, module_path: str, expected_prefix: str) -> None:
        """Each API router module imports without error and has the expected prefix."""
        mod = __import__(module_path, fromlist=["router"])
        router = mod.router

        assert hasattr(router, "prefix"), f"{module_path}.router missing 'prefix' attribute"
        assert router.prefix == expected_prefix, (
            f"{module_path}.router.prefix is {router.prefix!r}, expected {expected_prefix!r}"
        )

    def test_websocket_connection_manager_import(self) -> None:
        """WebSocket ConnectionManager class can be imported."""
        from heretek_swarm.api.websockets import ConnectionManager

        assert callable(ConnectionManager)

        # Instantiate to verify __init__ signature (no required args)
        manager = ConnectionManager()
        # Verify it holds the expected collections
        assert hasattr(manager, "execution_watchers")
        assert hasattr(manager, "a2a_listeners")
        assert hasattr(manager, "dashboard_listeners")


class TestRouteCounts:
    """Count routes per router and verify non-trivial implementations."""

    @pytest.mark.parametrize(
        "module_path,min_route_count",
        [
            ("heretek_swarm.api.consciousness", 5),
            ("heretek_swarm.api.skills", 5),
            ("heretek_swarm.api.workflows", 5),
            ("heretek_swarm.api.memory_versions", 5),
            ("heretek_swarm.api.rag", 5),
        ],
    )
    def test_api_router_has_routes(
        self, module_path: str, min_route_count: int
    ) -> None:
        """Each API router exposes a non-trivial number of routes."""
        mod = __import__(module_path, fromlist=["router"])
        router = mod.router

        routes = getattr(router, "routes", [])
        assert len(routes) >= min_route_count, (
            f"{module_path} has only {len(routes)} routes — "
            f"expected >= {min_route_count}. Stub routers typically have 0-1 routes."
        )

    def test_websocket_routes_present(self) -> None:
        """WebSocket module defines WebSocket route handlers."""
        from heretek_swarm.api import websockets

        # The module contains explicit websocket endpoint decorators at module level.
        # We check the file exists and has multiple @router.websocket decorators.
        ws_file = HERETEK_SRC / "api" / "websockets.py"
        assert ws_file.exists(), f"WebSocket source file not found: {ws_file}"

        content = ws_file.read_text(encoding="utf-8")
        # Count @router.websocket decorator usages as a proxy for route count
        decorator_count = content.count("@router.websocket")
        assert decorator_count >= 3, (
            f"websockets.py has only {decorator_count} @router.websocket decorators — "
            f"expected >= 3. A stub would have 0-1."
        )


class TestSourceFileExistence:
    """Verify all referenced source files exist on disk."""

    # rel_path is relative to HERETEK_SRC (i.e. relative to heretek_swarm/ itself)
    @pytest.mark.parametrize(
        "rel_path",
        [
            "api/consciousness.py",
            "api/skills.py",
            "api/workflows.py",
            "api/memory_versions.py",
            "api/rag.py",
            "api/websockets.py",
        ],
    )
    def test_source_file_exists(self, rel_path: str) -> None:
        """Each API source file exists at the expected location."""
        path = HERETEK_SRC / rel_path
        assert path.exists(), f"Source file missing: {path}"


class TestRouterHasRealDependencies:
    """Verify routers import from real implementation modules, not stubs."""

    @pytest.mark.parametrize(
        "module_path",
        [
            "heretek_swarm.api.consciousness",
            "heretek_swarm.api.skills",
            "heretek_swarm.api.workflows",
            "heretek_swarm.api.memory_versions",
            "heretek_swarm.api.rag",
        ],
    )
    def test_router_imports_real_modules(self, module_path: str) -> None:
        """Each router imports from non-api implementation modules."""
        import importlib

        importlib.import_module(module_path)

        # Parse the module's source file to find top-level imports
        imported_names: set[str] = set()
        # module_path is "heretek_swarm.api.X" — strip the leading "heretek_swarm."
        # prefix to get the relative path inside the package
        parts = module_path.split(".")  # e.g. ['heretek_swarm', 'api', 'consciousness']
        rel_parts = parts[1:]  # e.g. ['api', 'consciousness']
        module_py = HERETEK_SRC.joinpath(*rel_parts).with_suffix(".py")
        if module_py.exists():
            tree = ast.parse(module_py.read_text(encoding="utf-8"), filename=str(module_py))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_names.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imported_names.add(node.module.split(".")[0])

        # Each router should import from at least one non-api, non-stdlib module
        # (e.g. heretek_swarm.consciousness, heretek_swarm.workflow, etc.)
        skip = {"fastapi", "starlette", "typing", "datetime", "json", "asyncio", "structlog", "pathlib", "uuid"}
        meaningful_imports = {n for n in imported_names if n not in skip and not n.startswith("_")}

        assert len(meaningful_imports) >= 1, (
            f"{module_path} appears to only import stdlib/FastAPI — "
            f"expected at least 1 heretek_swarm implementation import. "
            f"Imports found: {sorted(imported_names)}"
        )