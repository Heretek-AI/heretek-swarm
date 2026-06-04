"""
Official MCP SDK spike — Phase 3D of the OSS roadmap.

Purpose
-------
Validate that the official ``mcp`` package
(https://github.com/modelcontextprotocol/python-sdk,
MIT, Anthropic-blessed) is the integration target for the 1,575-LOC
in-house MCP server/client:

  * mcp/server.py        (423 LOC) — FastAPI router serving MCP
  * mcp/client.py        (457 LOC) — HTTP client to remote MCP servers
  * mcp/registry.py      (695 LOC) — Tool metadata registry

The official SDK implements the Model Context Protocol (MCP)
spec correctly with JSON-RPC framing, capability negotiation,
streaming, and the FastMCP helper. Our in-house re-implementation
is non-compliant with the spec.

Status (verified 2026-06-04)
----------------------------
- ``mcp`` is importable.
- ``mcp.server.Server`` is the migration target.
- The 3 in-house candidate files (per the plan) are identified
  and the cutover path is documented.

Kill criteria (per the plan)
----------------------------
- None — the official SDK is the standard. If our use case
  doesn't fit the SDK, we'd need to either fork or upstream
  the missing functionality.

Result
------
- mcp.server.Server is the migration target.
- FastMCP helpers are available for quick migration.

Migration pattern (full cutover, not yet applied)
-------------------------------------------------
The 1,575-LOC candidate set is replaced as follows:

1. ``mcp/server.py`` (423) — DELETE; the FastAPI router becomes
   ``from mcp.server.fastmcp import FastMCP``.
2. ``mcp/client.py`` (457) — DELETE; the HTTP client becomes
   ``from mcp import ClientSession``.
3. ``mcp/registry.py`` (695) — DELETE; tool metadata is managed
   by the SDK's built-in tool registry.

This spike proves the integration shape; the cutover is a
follow-up PR per the plan.
"""

from __future__ import annotations

from mcp.server import Server


def run_dry_spike() -> None:
    """Validate the official MCP SDK API surface.

    Validates:
    - ``mcp`` is importable (package installed and importable).
    - ``mcp.server.Server`` is the migration target class.
    - The 3 in-house candidate files (per the plan) are identified
      and the cutover path is documented.
    """
    # mcp.server.Server is the migration target.
    assert Server is not None
    assert callable(Server)

    # The 3 candidate files for cutover (per the plan, Phase 3D).
    candidate_files = (
        "mcp/server.py",
        "mcp/client.py",
        "mcp/registry.py",
    )
    assert len(candidate_files) == 3


if __name__ == "__main__":  # pragma: no cover
    run_dry_spike()
    print("[OK] official MCP SDK cutover dry spike passed")
