"""
Heretek Swarm CLI

Command-line interface for Heretek Swarm deployment and management.
"""

from __future__ import annotations

import asyncio
import os
import signal
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Any

import click
import difflib
import httpx
import structlog

from heretek_swarm.cli.config_loader import load_infrastructure_config
from heretek_swarm.cli.config_wizard import (
    AVAILABLE_PROVIDERS,
    list_configured_providers,
    add_provider,
    remove_provider,
    run_wizard,
    set_default_provider,
    validate_provider,
    prompt_for_provider,
)
from heretek_swarm.config.models import HealthStatus, InfrastructureService

logger = structlog.get_logger("cli")

# Default API base URL for CLI commands
DEFAULT_API_BASE = "http://localhost:8000"

# Global shutdown flag for signal handlers
_shutdown_event: asyncio.Event | None = None
_swarm_instance: "AutonomousSwarm | None" = None


# =============================================================================
# Infrastructure Configuration Helpers
# =============================================================================

def _load_infrastructure_config_and_echo() -> dict[str, Any] | None:
    """
    Load infrastructure configuration from database.

    Returns:
        The load result dict if config was loaded, None if DATABASE_URL wasn't set.
    """
    try:
        return load_infrastructure_config()
    except RuntimeError as e:
        click.echo(f"\n  ⚠ {e}")
        return None


def _print_infrastructure_config(result: dict[str, Any] | None) -> None:
    """
    Print loaded infrastructure configuration values.

    Args:
        result: LoadResult dict with 'postgres', 'redis', 'qdrant', 'nats' keys.
    """
    if result is None:
        return

    # Check if any config was set from DB (vs. pre-existing env vars)
    any_set = any(entry.get("set", False) for entry in result.values())

    if not any_set:
        # All values were pre-existing in environment
        click.echo("  Infrastructure: loaded from environment variables")
        return

    # Print each service that was set from DB
    for service_name, entry in result.items():
        url = entry.get("url") if entry else None
        if url:
            click.echo(f"  {service_name.capitalize()}: {url}")


# =============================================================================
# Health Check Functions
# =============================================================================

async def _check_service_health(
    service: InfrastructureService,
    host: str,
    port: int,
    timeout: float = 5.0,
) -> dict[str, Any]:
    """
    Perform health check for a single service.

    Args:
        service: The infrastructure service type
        host: Service host
        port: Service port
        timeout: Health check timeout

    Returns:
        Health check result dict
    """
    start = time.perf_counter()

    try:
        if service == InfrastructureService.POSTGRES:
            return await _check_postgres(host, port, timeout, start)
        elif service == InfrastructureService.REDIS:
            return await _check_redis(host, port, timeout, start)
        elif service == InfrastructureService.QDRANT:
            return await _check_qdrant(host, port, timeout, start)
        elif service == InfrastructureService.NATS:
            return await _check_nats(host, port, timeout, start)
        elif service == InfrastructureService.MEM0:
            return await _check_mem0(host, port, timeout, start)
        else:
            return _make_result(service, HealthStatus.UNKNOWN, start, f"Unknown service: {service}")
    except Exception as e:
        logger.warning("health_check_error", service=service.value, error=str(e))
        return _make_result(service, HealthStatus.UNHEALTHY, start, str(e))


def _make_result(
    service: InfrastructureService,
    status: HealthStatus,
    start: float,
    error: str | None = None,
) -> dict[str, Any]:
    """Create a health check result dict."""
    latency_ms = (time.perf_counter() - start) * 1000
    return {
        "service": service.value,
        "status": status.value,
        "latency_ms": round(latency_ms, 2),
        "error": error,
    }


async def _check_postgres(host: str, port: int, timeout: float, start: float) -> dict[str, Any]:
    """Check PostgreSQL health via TCP socket."""
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
        writer.close()
        await writer.wait_closed()
        return _make_result(InfrastructureService.POSTGRES, HealthStatus.HEALTHY, start)
    except asyncio.TimeoutError:
        return _make_result(InfrastructureService.POSTGRES, HealthStatus.UNHEALTHY, start, "Connection timed out")
    except Exception as e:
        return _make_result(InfrastructureService.POSTGRES, HealthStatus.UNHEALTHY, start, str(e))


async def _check_redis(host: str, port: int, timeout: float, start: float) -> dict[str, Any]:
    """Check Redis health via PING."""
    import redis.asyncio as redis
    import time

    try:
        client = redis.Redis(host=host, port=port, socket_timeout=timeout)
        await client.ping()
        await client.aclose()
        return _make_result(InfrastructureService.REDIS, HealthStatus.HEALTHY, start)
    except Exception as e:
        return _make_result(InfrastructureService.REDIS, HealthStatus.UNHEALTHY, start, str(e))


async def _check_qdrant(host: str, port: int, timeout: float, start: float) -> dict[str, Any]:
    """Check Qdrant health via /healthz endpoint."""
    import httpx
    import time

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://{host}:{port}/healthz", timeout=timeout)
            if response.status_code == 200:
                return _make_result(InfrastructureService.QDRANT, HealthStatus.HEALTHY, start)
            return _make_result(InfrastructureService.QDRANT, HealthStatus.UNHEALTHY, start, f"HTTP {response.status_code}")
    except httpx.TimeoutException:
        return _make_result(InfrastructureService.QDRANT, HealthStatus.UNHEALTHY, start, "Request timed out")
    except Exception as e:
        return _make_result(InfrastructureService.QDRANT, HealthStatus.UNHEALTHY, start, str(e))


async def _check_nats(host: str, port: int, timeout: float, start: float) -> dict[str, Any]:
    """Check NATS health via CONNECT/PING exchange."""
    import time

    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)

        # Send CONNECT
        writer.write(b'CONNECT {"verbose":false,"ping":true}\r\n')
        await writer.drain()

        # Read INFO
        info_response = await asyncio.wait_for(reader.readline(), timeout=timeout)
        if not (info_response and b"INFO" in info_response):
            writer.close()
            await writer.wait_closed()
            return _make_result(InfrastructureService.NATS, HealthStatus.UNHEALTHY, start, "No INFO response")

        # Send PING
        writer.write(b"PING\r\n")
        await writer.drain()

        # Read PONG
        pong_response = await asyncio.wait_for(reader.readline(), timeout=timeout)
        writer.close()
        await writer.wait_closed()

        if pong_response and b"PONG" in pong_response:
            return _make_result(InfrastructureService.NATS, HealthStatus.HEALTHY, start)
        return _make_result(InfrastructureService.NATS, HealthStatus.UNHEALTHY, start, "No PONG response")
    except asyncio.TimeoutError:
        return _make_result(InfrastructureService.NATS, HealthStatus.UNHEALTHY, start, "Connection timed out")
    except Exception as e:
        return _make_result(InfrastructureService.NATS, HealthStatus.UNHEALTHY, start, str(e))


async def _check_mem0(host: str, port: int, timeout: float, start: float) -> dict[str, Any]:
    """Check Mem0 health via /health endpoint."""
    import httpx
    import time

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://{host}:{port}/health", timeout=timeout)
            if response.status_code == 200:
                return _make_result(InfrastructureService.MEM0, HealthStatus.HEALTHY, start)
            return _make_result(InfrastructureService.MEM0, HealthStatus.UNHEALTHY, start, f"HTTP {response.status_code}")
    except httpx.TimeoutException:
        return _make_result(InfrastructureService.MEM0, HealthStatus.UNHEALTHY, start, "Request timed out")
    except Exception as e:
        return _make_result(InfrastructureService.MEM0, HealthStatus.UNHEALTHY, start, str(e))


# =============================================================================
# Docker/Podman Detection
# =============================================================================

def check_container_runtime() -> tuple[str | None, str]:
    """
    Detect available container runtime (Docker or Podman).

    Returns:
        Tuple of (runtime_name, version_string) or (None, error_message)
    """
    for runtime in ["docker", "podman"]:
        try:
            result = subprocess.run(
                [runtime, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info("container_runtime_detected", runtime=runtime, version=version)
                return runtime, version
        except (subprocess.SubprocessError, FileNotFoundError):
            continue

    logger.warning("no_container_runtime_detected")
    return None, "Neither Docker nor Podman found"


def check_compose_plugin(runtime: str) -> bool:
    """
    Check if compose plugin is available for the container runtime.

    Args:
        runtime: Container runtime (docker or podman)

    Returns:
        True if compose plugin is available
    """
    try:
        result = subprocess.run(
            [runtime, "compose", "version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except subprocess.SubprocessError:
        return False


# =============================================================================
# CLI Commands
# =============================================================================

from importlib.metadata import version as _get_version, PackageNotFoundError

try:
    __version__ = _get_version("heretek-swarm")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"


class GroupedGroup(click.Group):
    """Custom Click group that organizes commands into labeled sections."""

    #: Mapping of group label → list of command names in display order.
    COMMAND_GROUPS: dict[str, list[str]] = {
        "Core Operations": ["run", "serve", "deploy", "wizard", "consensus"],
        "Configuration": ["config", "init"],
        "Monitoring": ["status", "stop"],
    }

    def format_commands(
        self, ctx: click.Context, formatter: click.HelpFormatter
    ) -> None:
        """Write command groups with separator lines to *formatter*."""
        # Collect all registered commands (excluding hidden)
        commands = {
            name: self.commands[name]
            for name in sorted(self.commands)
            if not self.commands[name].hidden
        }

        if not commands:
            return

        # Track which commands have been placed in a group
        placed: set[str] = set()

        for group_label, cmd_names in self.COMMAND_GROUPS.items():
            rows: list[tuple[str, str]] = []
            for cmd_name in cmd_names:
                if cmd_name in commands:
                    cmd = commands[cmd_name]
                    help_text = cmd.get_short_help_str(limit=50)
                    rows.append((cmd_name, help_text))
                    placed.add(cmd_name)

            if rows:
                # Section header
                with formatter.section(group_label):
                    formatter.write_dl(rows)

        # Any commands not in a group go into "Other"
        remaining = {
            name: cmd
            for name, cmd in commands.items()
            if name not in placed
        }
        if remaining:
            rows = [
                (name, cmd.get_short_help_str(limit=50))
                for name, cmd in sorted(remaining.items())
            ]
            with formatter.section("Other"):
                formatter.write_dl(rows)

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        """Look up a command by name, suggesting the closest match on miss."""
        cmd = super().get_command(ctx, cmd_name)
        if cmd is not None:
            return cmd

        # Suggest the closest valid command name
        matches = difflib.get_close_matches(
            cmd_name, self.list_commands(ctx), n=1, cutoff=0.6
        )
        if matches:
            raise click.UsageError(
                f"No such command '{cmd_name}'. Did you mean '{matches[0]}'?",
                ctx=ctx,
            )
        raise click.UsageError(f"No such command '{cmd_name}'.", ctx=ctx)


@click.group(
    cls=GroupedGroup,
    invoke_without_command=True,
    help=(
        "Heretek Swarm — autonomous multi-agent system with 23 specialized agents.\n"
        "Run locally or deploy via Docker."
    ),
    epilog=(
        "\b\n"
        "Examples:\n"
        "  pip install heretek-swarm\n"
        "  heretek-swarm run\n"
        "  heretek-swarm run --no-infra --prompt \"Analyze threat model\"\n"
        "  heretek-swarm serve --host 127.0.0.1 --port 9000\n"
        "  heretek-swarm config wizard"
    ),
)
@click.version_option(version=__version__, prog_name="heretek-swarm")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Heretek Swarm - Autonomous multi-agent system with 23 specialized agents."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command(
    epilog=(
        "\b\n"
        "Examples:\n"
        "  heretek-swarm deploy\n"
        "  heretek-swarm deploy --production --scale 3\n"
        "  heretek-swarm deploy --nats-url nats://cluster:4222"
    ),
)
@click.option("--production", is_flag=True, help="Deploy to production mode")
@click.option("--scale", default=1, type=int, help="Number of agent instances (default: 1)")
@click.option("--nats-url", default="nats://localhost:4222", help="NATS server URL")
@click.option("--api-base", default=DEFAULT_API_BASE, help="API base URL")
@click.option("--check-runtime/--no-check-runtime", default=True, help="Check container runtime availability")
def deploy(production: bool, scale: int, nats_url: str, api_base: str, check_runtime: bool) -> None:
    """
    Deploy Heretek Swarm agents.

    Reads wizard configuration from the API, checks Docker/Podman availability,
    and prints deployment instructions.
    """
    logger.info(
        "deploy_command",
        production=production,
        scale=scale,
        nats_url=nats_url,
        api_base=api_base,
    )

    click.echo("Heretek Swarm Deployment")
    click.echo("=" * 40)

    # Step 1: Read wizard config from API
    click.echo("\n[1/3] Reading wizard configuration...")
    wizard_config = _fetch_wizard_config(api_base)

    if wizard_config.get("wizard_completed"):
        click.echo("  ✓ Wizard configuration found")
        infrastructure = wizard_config.get("infrastructure", [])
        if infrastructure:
            click.echo(f"  ✓ {len(infrastructure)} infrastructure service(s) configured")
        providers = wizard_config.get("database_configured", {}).get("providers", [])
        if providers:
            click.echo(f"  ✓ {len(providers)} LLM provider(s) configured")
    else:
        click.echo("  ⚠ No wizard configuration found. Run 'heretek-swarm wizard' first.")

    # Step 2: Check container runtime
    click.echo("\n[2/3] Checking container runtime...")
    runtime, version = check_container_runtime()

    if runtime:
        click.echo(f"  ✓ {runtime.capitalize()} found: {version}")

        # Check compose plugin
        if check_compose_plugin(runtime):
            click.echo(f"  ✓ {runtime.capitalize()} Compose plugin available")
        else:
            click.echo(f"  ⚠ {runtime.capitalize()} Compose plugin not found")
            click.echo("    Install with: " + runtime + " compose install")
    else:
        click.echo(f"  ✗ {version}")
        click.echo("\n    Container runtime required for deployment.")
        click.echo("    Install Docker: https://docs.docker.com/get-docker/")
        click.echo("    Or Podman: https://podman.io/getting-started/installation")

    # Step 3: Print deployment instructions
    click.echo("\n[3/3] Deployment instructions:")
    click.echo("-" * 40)

    if runtime:
        compose_file = Path("docker-compose.yml")
        if compose_file.exists():
            click.echo("\nTo start the deployment:")
            click.echo(f"  {runtime} compose up -d")
            if production:
                click.echo(f"  {runtime} compose up -d --scale agent={scale}")
        else:
            click.echo("\nNo docker-compose.yml found in current directory.")
            click.echo("Create one or use heretek-swarm generate-compose.")
    else:
        click.echo("\n  Cannot proceed without container runtime.")
        click.echo("  Please install Docker or Podman first.")

    click.echo("\n" + "=" * 40)
    click.echo("Deployment ready. Run 'heretek-swarm status' to verify.")


# =============================================================================
# Run Command - Autonomous Swarm
# =============================================================================

def _print_startup_banner(swarm: "AutonomousSwarm") -> None:
    """Print a formatted startup status table showing component health."""
    status = swarm.get_startup_status()
    click.echo("")
    click.echo("  " + "-" * 50)
    click.echo(f"  {'Component':<20} {'Status':<12}")
    click.echo("  " + "-" * 50)
    for name, s in status.items():
        click.echo(f"  {name:<20}: {s}")
    click.echo("  " + "-" * 50)
    any_fail = any(s.startswith("✗") for s in status.values())
    if any_fail:
        click.echo("  ⚠ Some components unavailable — swarm running with degraded capabilities")
    click.echo("")


def _display_deliberation_results(results: dict[str, dict]) -> None:
    """Print formatted deliberation results per agent.

    Args:
        results: The dict returned by ``AutonomousSwarm.run_deliberation()``,
            mapping agent IDs to result dicts containing ``analyses``,
            ``challenges``, or ``error`` keys.
    """
    for agent_id in ["alpha", "beta", "charlie"]:
        agent_result = results.get(agent_id, {})
        click.echo("")
        click.echo(f"  {agent_id.upper()} response:")
        if "error" in agent_result:
            click.echo(f"    [Error: {agent_result['error']}]")
            continue
        analyses = agent_result.get("analyses", agent_result.get("challenges", []))
        if not analyses:
            click.echo("    [No analysis produced]")
            continue
        for entry in analyses:
            decision = entry.get("analysis", entry.get("decision", ""))
            if isinstance(decision, dict):
                decision = decision.get("decision", str(decision))
            click.echo(f"    {decision}")
    click.echo("")
    click.echo("  Deliberation complete.")


def _display_routed_result(result: dict) -> None:
    """Print a compact summary of a routed task result.

    Args:
        result: The dict returned by ``AutonomousSwarm.run_routed_task()``,
            containing at minimum ``status`` and optionally ``target_agent``,
            ``task_type``, ``message_id``, and ``error`` keys.
    """
    status = result.get("status", "unknown")
    target = result.get("target_agent", "?")
    task_type = result.get("task_type", "?")
    message_id = result.get("message_id", "?")

    if status == "dispatched":
        status_icon = "✓"
    elif status == "failed":
        status_icon = "✗"
    else:
        status_icon = "?"

    click.echo("")
    click.echo(f"  {status_icon} Routed to agent: {target}")
    click.echo(f"    Task type:       {task_type}")
    click.echo(f"    Status:          {status}")
    click.echo(f"    Message ID:      {message_id}")

    error = result.get("error")
    if error:
        click.echo(f"    Error:           {error}")

    click.echo("")
    click.echo("  Route complete.")


def _display_consensus_results(results: dict[str, Any]) -> None:
    """Print formatted consensus results.

    Args:
        results: The dict returned by ``AutonomousSwarm.run_consensus()``,
            containing ``decision``, ``confidence``, ``votes``, ``red_flags``,
            ``reasoning``, and ``consensus_id`` keys.
    """
    decision = results.get("decision", "unknown")
    confidence = results.get("confidence", 0.0)
    votes = results.get("votes", [])
    red_flags = results.get("red_flags", [])
    reasoning = results.get("reasoning", "")
    consensus_id = results.get("consensus_id", "unknown")
    round_history = results.get("round_history", [])
    total_rounds = results.get("total_rounds", 1)

    click.echo("")
    click.echo(f"  Consensus ID: {consensus_id}")
    click.echo("  " + "-" * 50)

    # Show round progress if multi-round
    if total_rounds > 1 or round_history:
        click.echo(f"  Rounds: {total_rounds}")
        click.echo("")

    # Selected agents
    agent_ids = [v.get("agent_id", "?") for v in votes]
    click.echo(f"  Agents ({len(agent_ids)}): {', '.join(agent_ids)}")
    click.echo("")

    # Individual votes
    click.echo("  Votes:")
    for v in votes:
        agent_id = v.get("agent_id", "?")
        v_decision = v.get("decision", "?")
        v_confidence = v.get("confidence", 0.0)
        reasoning_text = v.get("metadata", {}).get("reasoning", "")
        line = f"    {agent_id:<20} → {v_decision:<20} (conf: {v_confidence:.2f})"
        click.echo(line)
        if reasoning_text:
            click.echo(f"      Reasoning: {reasoning_text}")

    click.echo("")
    click.echo("  " + "-" * 50)

    # Winning decision
    click.echo(f"  ✓ Decision:  {decision}")
    click.echo(f"  ✓ Confidence: {confidence:.2f}")

    # Vote breakdown
    breakdown: dict[str, int] = {}
    for v in votes:
        d = v.get("decision", "unknown")
        breakdown[d] = breakdown.get(d, 0) + 1
    breakdown_str = ", ".join(f"{d}: {c}" for d, c in sorted(breakdown.items()))
    click.echo(f"  Vote breakdown: {breakdown_str}")

    # Red flags
    if red_flags:
        click.echo("")
        click.echo("  ⚠ Red Flags:")
        for flag in red_flags:
            click.echo(f"    - {flag}")

    # Reasoning summary
    if reasoning:
        click.echo("")
        click.echo("  Reasoning:")
        # Wrap long reasoning text
        for line in reasoning.split("; "):
            click.echo(f"    {line}")

    # Round history (multi-round deliberation)
    if round_history:
        click.echo("")
        click.echo("  Round History:")
        click.echo("  " + "-" * 50)
        for rh in round_history:
            r_num = rh.get("round_number", "?")
            r_score = rh.get("consensus_score", 0.0)
            r_decision = rh.get("decision", "none")
            r_votes = rh.get("vote_count", 0)
            click.echo(
                f"    Round {r_num}: decision={r_decision}, "
                f"score={r_score:.2f}, votes={r_votes}"
            )

    click.echo("")


async def _start_autonomous_swarm(
    no_infra: bool = False,
    prompt: str | None = None,
    target_agent: str | None = None,
    force_consensus: bool = False,
) -> None:
    """Start the AutonomousSwarm with signal handlers for graceful shutdown."""
    from heretek_swarm.logging.config import setup_logging
    from heretek_swarm.runtime.main_loop import AutonomousSwarm

    # Set up structured logging
    setup_logging(json_output=False, include_caller_info=False)

    # Get configuration from environment
    nats_servers_str = os.getenv("HERETEK_NATS_URL", "nats://localhost:4222")
    nats_servers = [s.strip() for s in nats_servers_str.split(",")]

    config = {
        "nats_servers": nats_servers,
        "health_check_interval": 30,
        "loop_interval": 1,
        "consciousness_interval": 5,
        "memory_maintenance_interval": 300,
        "scaling_interval": 60,
        "ephemeral": {"ttl_seconds": 3600},
        "persistent": {
            "connection_string": os.getenv(
                "DATABASE_URL",
                "postgresql://heretek:password@localhost/heretek_swarm"
            ),
        },
        "rag": {
            "embedding_provider": os.getenv("RAG_EMBEDDING_PROVIDER", "openai"),
            "embedding_model": os.getenv("RAG_EMBEDDING_MODEL", "text-embedding-3-small"),
            "llm_provider": os.getenv("RAG_LLM_PROVIDER", "openai"),
            "llm_model": os.getenv("RAG_LLM_MODEL", "gpt-4o-mini"),
            "collection_name": os.getenv("RAG_COLLECTION", "heretek_documents"),
        },
        "consensus": {
            "ahead_by_k": 2,
            "min_votes": 3,
            "red_flag_threshold": 0.3,
        },
    }

    if no_infra:
        click.echo("  --no-infra: skipping external infrastructure connections")
        click.echo("  Components requiring Postgres, Redis, Qdrant, or NATS will be unavailable")
        # Clear connection strings so no component tries external connections
        config["persistent"]["connection_string"] = ""

    swarm = AutonomousSwarm(config, no_infra=no_infra)
    global _swarm_instance
    _swarm_instance = swarm

    # Initialize and run
    await swarm.initialize()

    # Print startup diagnostics banner
    _print_startup_banner(swarm)

    if prompt:
        from heretek_swarm.consensus.complexity import ComplexityHeuristic

        click.echo("")
        if target_agent:
            click.echo(f"  Routing prompt to agent '{target_agent}': {prompt}")
            click.echo("  " + "-" * 50)
            try:
                result = await swarm.run_routed_task(
                    target_agent,
                    "on_demand_analysis",
                    {"prompt": prompt},
                )
            except Exception as e:
                click.echo(f"\n  ✗ Route failed: {e}")
                return
            _display_routed_result(result)
        else:
            # Auto-route: use ComplexityHeuristic to decide consensus vs triad
            heuristic = ComplexityHeuristic()
            complexity = heuristic.assess(prompt)

            logger.info(
                "auto_routing_decision",
                complexity_score=complexity.score,
                routing_decision=complexity.routing_mode,
                is_complex=complexity.is_complex,
                matched_keywords=complexity.matched_keywords,
                force_consensus=force_consensus,
            )

            if force_consensus or complexity.is_complex:
                mode_label = "forced consensus" if force_consensus else "auto-consensus"
                click.echo(f"  Routing: {mode_label} (complexity={complexity.score:.2f})")
                click.echo(f"  Consensus prompt: {prompt}")
                click.echo("  " + "-" * 50)
                try:
                    results = await swarm.run_consensus(prompt)
                except Exception as e:
                    click.echo(f"\n  ✗ Consensus failed: {e}")
                    return
                _display_consensus_results(results)
            else:
                click.echo(f"  Routing: triad deliberation (complexity={complexity.score:.2f})")
                click.echo(f"  Deliberating prompt: {prompt}")
                click.echo("  " + "-" * 50)
                try:
                    results = await swarm.run_deliberation(prompt)
                except Exception as e:
                    click.echo(f"\n  ✗ Deliberation failed: {e}")
                    return
                _display_deliberation_results(results)
        return  # Don't call swarm.run()

    await swarm.run()


def _handle_signal(signum: int, frame) -> None:
    """Handle SIGINT/SIGTERM for graceful shutdown."""
    sig_name = signal.Signals(signum).name
    logger.warning("shutdown_signal_received", signal=sig_name)

    if _shutdown_event:
        logger.info("initiating_graceful_shutdown", signal=sig_name)
        _shutdown_event.set()
    else:
        logger.info("immediate_exit", signal=sig_name)
        sys.exit(0)


@cli.command(
    epilog=(
        "\b\n"
        "Examples:\n"
        "  heretek-swarm run\n"
        "  heretek-swarm run --detach\n"
        "  heretek-swarm run --no-infra\n"
        "  heretek-swarm run --no-infra --prompt \"Analyze the strategic implications of X\"\n"
        "  heretek-swarm run --prompt \"analyze tradeoffs of Redis\" --consensus\n"
        "  HERETEK_NATS_URL=nats://cluster1:4222,nats://cluster2:4222 heretek-swarm run"
    ),
)
@click.option(
    "--detach",
    is_flag=True,
    help="Run in background (daemon mode)",
)
@click.option(
    "--nats-url",
    envvar="HERETEK_NATS_URL",
    default="nats://localhost:4222",
    help="NATS server URL(s), comma-separated for multiple servers",
)
@click.option(
    "--no-infra",
    is_flag=True,
    help="Skip external infrastructure connections (Postgres, Redis, Qdrant, NATS); use in-memory state only",
)
@click.option(
    "--prompt",
    type=str,
    default=None,
    help="Single prompt to deliberate through the triad, then exit",
)
@click.option(
    "--target-agent",
    type=str,
    default=None,
    help="Route prompt to a specific agent (default: triad deliberation)",
)
@click.option(
    "--consensus",
    "force_consensus",
    is_flag=True,
    default=False,
    help="Force MAKER consensus routing (bypasses complexity heuristic)",
)
def run(detach: bool, nats_url: str, no_infra: bool, prompt: str | None = None, target_agent: str | None = None, force_consensus: bool = False) -> None:
    """
    Start the Heretek Swarm autonomous runtime.

    Initializes and starts the AutonomousSwarm with 23 agents across 6 tiers.
    Supports graceful shutdown via SIGINT (Ctrl+C) and SIGTERM signals.

    Configuration is read from environment variables:
    - HERETEK_NATS_URL: NATS server URLs (default: nats://localhost:4222)
    - DATABASE_URL: PostgreSQL connection string
    - RAG_* environment variables for RAG configuration

    Use --no-infra to run without Docker/Postgres/Redis — the swarm uses
    in-memory state and logs graceful fallback warnings.
    """
    import os

    logger.info("run_command", detach=detach, nats_url=nats_url, no_infra=no_infra)

    click.echo("Heretek Swarm Autonomous Runtime")
    click.echo("=" * 40)

    if no_infra:
        click.echo("\n  --no-infra mode: external infrastructure connections will be skipped")
    else:
        # Load infrastructure configuration from database (if DATABASE_URL is set)
        infra_config = _load_infrastructure_config_and_echo()

    if detach:
        click.echo("\nStarting in detached mode...")
        # Use the daemon module — handles fork, PID file, Unix socket, signal handling.
        from heretek_swarm.runtime.daemon import daemonize
        from heretek_swarm.runtime.main_loop import AutonomousSwarm

        from heretek_swarm.logging.config import setup_logging
        setup_logging(json_output=False, include_caller_info=False)

        nats_servers = [s.strip() for s in nats_url.split(",")]

        config = {
            "nats_servers": nats_servers,
            "health_check_interval": 30,
            "loop_interval": 1,
            "consciousness_interval": 5,
            "memory_maintenance_interval": 300,
            "scaling_interval": 60,
            "ephemeral": {"ttl_seconds": 3600},
            "persistent": {
                "connection_string": os.getenv(
                    "DATABASE_URL",
                    "postgresql://heretek:password@localhost/heretek_swarm"
                ),
            },
            "rag": {
                "embedding_provider": os.getenv("RAG_EMBEDDING_PROVIDER", "openai"),
                "embedding_model": os.getenv("RAG_EMBEDDING_MODEL", "text-embedding-3-small"),
                "llm_provider": os.getenv("RAG_LLM_PROVIDER", "openai"),
                "llm_model": os.getenv("RAG_LLM_MODEL", "gpt-4o-mini"),
                "collection_name": os.getenv("RAG_COLLECTION", "heretek_documents"),
            },
            "consensus": {
                "ahead_by_k": 2,
                "min_votes": 3,
                "red_flag_threshold": 0.3,
            },
        }

        if no_infra:
            config["persistent"]["connection_string"] = ""

        swarm = AutonomousSwarm(config, no_infra=no_infra)
        daemonize(swarm)
        # daemonize() exits the parent after printing the PID — control never reaches here.
        return

    click.echo("\nInitializing autonomous swarm...")
    click.echo(f"  NATS: {nats_url}")

    if not no_infra:
        # Print loaded infrastructure configuration
        _print_infrastructure_config(infra_config)

    if prompt:
        # Prompt mode: no signal handlers needed, exit after deliberation
        try:
            asyncio.run(_start_autonomous_swarm(no_infra=no_infra, prompt=prompt, target_agent=target_agent, force_consensus=force_consensus))
        except Exception as e:
            logger.error("prompt_mode_failure", error=str(e))
            click.echo(f"\n✗ Failed to start: {e}")
            sys.exit(1)
        return

    # Set up signal handlers for long-running mode
    shutdown_event = asyncio.Event()
    global _shutdown_event
    _shutdown_event = shutdown_event

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    try:
        # Run the async main in long-running mode
        asyncio.run(_start_autonomous_swarm(no_infra=no_infra))
    except KeyboardInterrupt:
        logger.info("shutdown_keyboard_interrupt")
        click.echo("\nShutdown complete.")
    except Exception as e:
        logger.error("startup_failure", error=str(e))
        click.echo(f"\n✗ Failed to start: {e}")
        sys.exit(1)


@cli.command(
    epilog=(
        "\b\n"
        "Examples:\n"
        "  heretek-swarm consensus \"should we add rate limiting?\"\n"
        "  heretek-swarm consensus \"should we refactor the auth module?\" --timeout 180\n"
        "  heretek-swarm consensus \"what database should we use?\" --participants 5\n"
        "  heretek-swarm consensus \"analyze the tradeoffs of caching\" --rounds 3"
    ),
)
@click.argument("question")
@click.option(
    "--timeout",
    default=120,
    type=float,
    help="Consensus timeout in seconds (default: 120)",
)
@click.option(
    "--participants",
    default=None,
    type=int,
    help="Override number of participants (default: 5-7 from domain selection)",
)
@click.option(
    "--rounds",
    "max_rounds",
    default=1,
    type=int,
    help="Number of deliberation rounds with argument exchange (default: 1)",
)
def consensus(question: str, timeout: float, participants: int | None, max_rounds: int = 1) -> None:
    """
    Run MAKER consensus on a question.

    Selects domain-relevant agents via topic matching, each agent votes with
    a decision and confidence through LLM, MAKER ahead-by-k voting terminates
    when a clear winner emerges, and the result is displayed with winning
    decision, confidence score, vote breakdown, and red flags.
    """
    logger.info("consensus_command", question=question[:200], timeout=timeout, participants=participants, max_rounds=max_rounds)

    click.echo("Heretek Swarm Consensus")
    click.echo("=" * 40)
    click.echo(f"\n  Question: {question}")
    click.echo(f"  Timeout:  {timeout}s")
    if participants is not None:
        click.echo(f"  Participants: {participants} (override)")
    if max_rounds > 1:
        click.echo(f"  Rounds:   {max_rounds} (with argument exchange)")

    click.echo("\nInitializing swarm...")

    try:
        results = asyncio.run(_run_consensus(question, timeout, max_rounds=max_rounds))
        _display_consensus_results(results)
    except Exception as e:
        logger.error("consensus_failure", error=str(e))
        click.echo(f"\n✗ Consensus failed: {e}")
        sys.exit(1)


async def _run_consensus(question: str, timeout: float, max_rounds: int = 1) -> dict[str, Any]:
    """Async helper for the consensus CLI command."""
    from heretek_swarm.logging.config import setup_logging
    from heretek_swarm.runtime.main_loop import AutonomousSwarm

    setup_logging(json_output=False, include_caller_info=False)

    nats_servers_str = os.getenv("HERETEK_NATS_URL", "nats://localhost:4222")
    nats_servers = [s.strip() for s in nats_servers_str.split(",")]

    config = {
        "nats_servers": nats_servers,
        "health_check_interval": 30,
        "loop_interval": 1,
        "consciousness_interval": 5,
        "memory_maintenance_interval": 300,
        "scaling_interval": 60,
        "ephemeral": {"ttl_seconds": 3600},
        "persistent": {
            "connection_string": os.getenv(
                "DATABASE_URL",
                "postgresql://heretek:password@localhost/heretek_swarm"
            ),
        },
        "rag": {
            "embedding_provider": os.getenv("RAG_EMBEDDING_PROVIDER", "openai"),
            "embedding_model": os.getenv("RAG_EMBEDDING_MODEL", "text-embedding-3-small"),
            "llm_provider": os.getenv("RAG_LLM_PROVIDER", "openai"),
            "llm_model": os.getenv("RAG_LLM_MODEL", "gpt-4o-mini"),
            "collection_name": os.getenv("RAG_COLLECTION", "heretek_documents"),
        },
        "consensus": {
            "ahead_by_k": 2,
            "min_votes": 3,
            "red_flag_threshold": 0.3,
        },
    }

    # Always use --no-infra for consensus (short-lived, no need for external services)
    no_infra = True
    click.echo("  --no-infra: consensus runs without external infrastructure")

    swarm = AutonomousSwarm(config, no_infra=no_infra)

    await swarm.initialize()
    _print_startup_banner(swarm)

    click.echo("\nRunning consensus...")
    click.echo("  " + "-" * 50)

    results = await swarm.run_consensus(question, timeout=timeout, max_rounds=max_rounds)
    return results


@cli.command(
    epilog=(
        "\b\n"
        "Examples:\n"
        "  heretek-swarm serve\n"
        "  heretek-swarm serve --host 127.0.0.1 --port 9000\n"
        "  heretek-swarm serve --workers 4"
    ),
)
@click.option(
    "--host",
    default="0.0.0.0",
    help="Host to bind to (default: 0.0.0.0)",
)
@click.option(
    "--port",
    default=8000,
    type=int,
    help="Port to bind to (default: 8000)",
)
@click.option(
    "--workers",
    default=1,
    type=int,
    help="Number of worker processes (default: 1)",
)
def serve(host: str, port: int, workers: int) -> None:
    """
    Start the Heretek Swarm API server.

    Starts uvicorn with the FastAPI application on the specified host and port.
    Uses structured logging via uvicorn's built-in configuration.
    """
    import os

    logger.info("serve_command", host=host, port=port, workers=workers)

    click.echo("Heretek Swarm API Server")
    click.echo("=" * 40)

    # Load infrastructure configuration from database (if DATABASE_URL is set)
    infra_config = _load_infrastructure_config_and_echo()

    # Check if uvicorn is available
    try:
        import uvicorn
    except ImportError:
        click.echo("\n✗ uvicorn not installed. Install with: pip install uvicorn")
        sys.exit(1)

    click.echo(f"\nStarting API server on {host}:{port}...")
    click.echo("  Press Ctrl+C to stop")

    # Print loaded infrastructure configuration
    _print_infrastructure_config(infra_config)

    # Build uvicorn command
    app_module = "heretek_swarm.api.main:app"

    # Configure logging for uvicorn
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["default"]["fmt"] = (
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    log_config["formatters"]["access"]["fmt"] = (
        '%(asctime)s | %(client_addr)s | "%(request_line)s" %(status_code)s'
    )

    uvicorn.run(
        app_module,
        host=host,
        port=port,
        workers=workers,
        log_config=log_config,
    )


@cli.command()
def wizard() -> None:
    """
    Open the Heretek Swarm wizard in your browser.

    Opens http://localhost:3000 in the default browser. If no browser is available,
    prints the URL instead.
    """
    logger.info("wizard_command")

    url = "http://localhost:3000"

    try:
        webbrowser.open(url)
        click.echo(f"Opening {url} in browser...")
    except Exception:
        click.echo(f"No browser available. Navigate to: {url}")
        sys.exit(0)


@cli.command()
def init() -> None:
    """
    Initialize Heretek Swarm configuration.

    Creates ~/.heretek-swarm/.env from .env.example if it doesn't already exist.
    """
    logger.info("init_command")

    config_dir = Path.home() / ".heretek-swarm"
    config_file = config_dir / ".env"

    # Create config directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)

    # Check if already initialized
    if config_file.exists():
        click.echo(f"Already initialized: {config_file}")
        sys.exit(0)

    # Resolve .env.example - try CWD first, then package directory
    example_paths = [
        Path(".env.example"),
        Path(__file__).parent.parent.parent / ".env.example",
    ]

    example_path: Path | None = None
    for p in example_paths:
        if p.exists():
            example_path = p
            break

    if example_path is None:
        click.echo("Error: .env.example not found")
        click.echo("  Searched in current directory and package directory")
        sys.exit(1)

    # Copy .env.example to ~/.heretek-swarm/.env
    shutil.copy2(example_path, config_file)

    click.echo(f"Initialized: {config_file}")


@cli.command()
@click.option("--api-base", default=DEFAULT_API_BASE, help="API base URL")
@click.option("--timeout", default=30, type=int, help="Health check timeout in seconds")
@click.option("--json", "output_json", is_flag=True, help="Output results as JSON")
def status(api_base: str, timeout: int, output_json: bool) -> None:
    """
    Check Heretek Swarm status.

    If the background daemon is running, queries it via the Unix socket
    for agent status.  Otherwise falls back to fetching infrastructure
    configuration from the HTTP API and performing health checks.
    """
    import json as json_mod

    logger.info("status_command", api_base=api_base, timeout=timeout)

    # --- Try daemon socket first --------------------------------------------
    from heretek_swarm.runtime.daemon import DEFAULT_PID_FILE, DEFAULT_SOCKET_PATH, read_pid_file

    pid = read_pid_file(DEFAULT_PID_FILE)
    if pid is not None:
        agent_data = _query_daemon_socket()
        if agent_data is not None:
            _display_daemon_status(agent_data, pid, output_json)
            return

    # ── Fallback: API-based health check ────────────────────────────────────
    import time

    if not output_json:
        click.echo("Heretek Swarm Status")
        click.echo("=" * 40)

    start_time = time.perf_counter()

    # Fetch infrastructure config from API
    if not output_json:
        click.echo(f"\nFetching infrastructure configuration from {api_base}...")

    try:
        response = httpx.get(
            f"{api_base}/api/wizard/infrastructure",
            timeout=5.0,
        )
        response.raise_for_status()
        data = response.json()
    except httpx.ConnectError:
        if output_json:
            click.echo(json_mod.dumps({"error": f"Cannot connect to API server at {api_base}"}))
            sys.exit(2)
        # Check if there's genuinely nothing available
        click.echo("  ✗ Cannot connect to API server")
        click.echo("  No running daemon or API server found")
        sys.exit(1)
    except httpx.HTTPError as e:
        if output_json:
            click.echo(json_mod.dumps({"error": f"API error: {e}"}))
            sys.exit(2)
        click.echo(f"  ✗ API error: {e}")
        sys.exit(1)

    configs = data.get("infrastructure", [])
    if not configs:
        if output_json:
            import json
            result = {
                "services": [],
                "summary": {"total": 0, "healthy": 0, "unhealthy": 0, "unknown": 0, "duration_ms": round((time.perf_counter() - start_time) * 1000, 1)},
                "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat().replace("+00:00", "Z"),
            }
            click.echo(json.dumps(result))
            sys.exit(0)
        click.echo("  ⚠ No infrastructure services configured")
        click.echo("\nRun 'heretek-swarm deploy' or use the wizard to configure services.")
        sys.exit(0)

    if not output_json:
        click.echo(f"  Found {len(configs)} configured service(s)")

    # Perform health checks
    if not output_json:
        click.echo("\nPerforming health checks...")
    results: list[dict[str, Any]] = []

    async def run_health_checks() -> list[dict[str, Any]]:
        checks = []
        for config in configs:
            service_str = config.get("service")
            try:
                service = InfrastructureService(service_str)
            except ValueError:
                click.echo(f"  ⚠ Unknown service: {service_str}")
                continue

            checks.append(
                _check_service_health(
                    service=service,
                    host=config.get("host", "localhost"),
                    port=config.get("port", 0),
                    timeout=float(timeout),
                )
            )

        return await asyncio.gather(*checks)

    results = asyncio.run(run_health_checks())

    healthy_count = 0
    unhealthy_count = 0
    unknown_count = 0
    for r in results:
        s = r.get("status", "unknown")
        if s == "healthy":
            healthy_count += 1
        elif s == "unhealthy":
            unhealthy_count += 1
        else:
            unknown_count += 1

    if output_json:
        import json
        total_time_ms = (time.perf_counter() - start_time) * 1000
        result = {
            "services": [
                {
                    "service": r.get("service", "unknown"),
                    "status": r.get("status", "unknown"),
                    "latency_ms": round(r.get("latency_ms", 0), 1),
                    "error": r.get("error"),
                }
                for r in results
            ],
            "summary": {
                "total": len(results),
                "healthy": healthy_count,
                "unhealthy": unhealthy_count,
                "unknown": unknown_count,
                "duration_ms": round(total_time_ms, 1),
            },
            "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        click.echo(json.dumps(result))
        sys.exit(1 if unhealthy_count > 0 else 0)

    # Display results (human-readable table)
    click.echo("\n" + "-" * 60)
    click.echo(f"{'Service':<12} {'Status':<12} {'Latency':<12} Details")
    click.echo("-" * 60)

    for result in results:
        service = result.get("service", "unknown")
        status_val = result.get("status", "unknown")
        latency = result.get("latency_ms", 0)
        error = result.get("error")

        # Status icon and color
        if status_val == "healthy":
            icon = "✓"
        elif status_val == "unhealthy":
            icon = "✗"
        else:
            icon = "?"

        # Format latency
        if latency < 1000:
            latency_str = f"{latency:.1f}ms"
        else:
            latency_str = f"{latency/1000:.2f}s"

        # Display row
        status_display = f"{icon} {status_val.upper()}"
        click.echo(f"{service:<12} {status_display:<12} {latency_str:<12} {error or ''}")

        # Structured log for each health check
        logger.info(
            "health_check_result",
            service=service,
            status=status_val,
            latency_ms=latency,
            error=error,
        )

    click.echo("-" * 60)

    # Summary
    total_time = time.perf_counter() - start_time
    click.echo(f"\nSummary: {healthy_count} healthy, {unhealthy_count} unhealthy, {unknown_count} unknown")
    click.echo(f"Total time: {total_time:.2f}s")

    # Exit code based on health
    if unhealthy_count > 0:
        click.echo("\n⚠ Some services are unhealthy. Run 'heretek-swarm deploy' for setup instructions.")
        sys.exit(1)
    elif unknown_count > 0:
        click.echo("\n⚠ Some services have unknown status.")
        sys.exit(1)
    else:
        click.echo("\n✓ All services healthy")


@cli.command()
def stop() -> None:
    """
    Stop a running Heretek Swarm background daemon.

    Sends SIGTERM to the daemon process and cleans up the socket file.
    Exits with code 1 if no daemon PID file is found.
    """
    from heretek_swarm.runtime.daemon import (
        DEFAULT_PID_FILE,
        DEFAULT_SOCKET_PATH,
        cleanup_daemon,
        read_pid_file,
        send_stop,
    )

    logger.info("stop_command")

    pid = read_pid_file(DEFAULT_PID_FILE)
    if pid is None:
        click.echo("No running daemon found")
        sys.exit(1)

    sent = send_stop(pid)
    if sent:
        click.echo(f"Shutdown signal sent to PID {pid}")
    else:
        click.echo(f"Failed to send stop signal to PID {pid} (process already gone?)")

    # Clean up stale files regardless — if the daemon is gone, these are leftovers.
    cleanup_daemon(DEFAULT_PID_FILE, DEFAULT_SOCKET_PATH)


# =============================================================================
# Daemon socket helpers
# =============================================================================


def _query_daemon_socket() -> dict | None:
    """Connect to the daemon's Unix socket and send a status query.

    Returns the parsed JSON response dict, or ``None`` if the socket is
    unreachable or the exchange fails.
    """
    from heretek_swarm.runtime.daemon import DEFAULT_SOCKET_PATH

    import json

    socket_path = DEFAULT_SOCKET_PATH
    if not socket_path.exists():
        return None

    try:
        import socket as sock_mod

        s = sock_mod.socket(sock_mod.AF_UNIX, sock_mod.SOCK_STREAM)
        s.settimeout(5.0)
        s.connect(str(socket_path))
        s.sendall(json.dumps({"type": "status"}).encode("utf-8") + b"\n")

        # Read response
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
            if b"\n" in data:
                break
        s.close()

        return json.loads(data.decode("utf-8").strip())
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("daemon_socket_query_failed", error=str(exc))
        return None


def _display_daemon_status(agent_data: dict, pid: int, output_json: bool) -> None:
    """Print agent status from the daemon to stdout.

    Args:
        agent_data: Response dict containing an ``"agents"`` list.
        pid: The daemon PID (printed in the header).
        output_json: If ``True``, output JSON only.
    """
    import json

    agents = agent_data.get("agents", [])

    if output_json:
        click.echo(json.dumps({
            "daemon_pid": pid,
            "agents": agents,
            "agent_count": len(agents),
        }))
        return

    click.echo("Heretek Swarm Status (daemon)")
    click.echo("=" * 40)
    click.echo(f"  Daemon PID: {pid}")
    click.echo("")

    if not agents:
        click.echo("  No agent data available from daemon.")
        return

    # Column widths
    id_w = max(len(a.get("agent_id", "")) for a in agents) + 2  # padding
    id_w = max(id_w, 12)
    state_w = 12
    mb_w = 8
    msg_w = 10
    err_w = 6

    header = (
        f"  {'Agent ID':<{id_w}} {'State':<{state_w}} "
        f"{'Mailbox':<{mb_w}} {'Messages':<{msg_w}} {'Errors':<{err_w}} Last Activity"
    )
    click.echo(header)
    click.echo("  " + "-" * len(header))

    for a in agents:
        aid = a.get("agent_id", "?")
        state = a.get("state", "?")
        mb = a.get("mailbox_size", 0)
        msgs = a.get("message_count", 0)
        errs = a.get("error_count", 0)
        last_act = a.get("last_activity", "")
        click.echo(
            f"  {aid:<{id_w}} {state:<{state_w}} "
            f"{mb:<{mb_w}} {msgs:<{msg_w}} {errs:<{err_w}} {last_act}"
        )

    click.echo("")
    click.echo(f"  ✓ {len(agents)} agent(s) running")


def _fetch_wizard_config(api_base: str) -> dict[str, Any]:
    """
    Fetch wizard configuration from the API.

    Args:
        api_base: Base URL of the API

    Returns:
        Wizard configuration dict
    """
    try:
        response = httpx.get(
            f"{api_base}/api/wizard/config",
            timeout=5.0,
        )
        response.raise_for_status()
        return response.json()
    except httpx.ConnectError:
        logger.warning("api_unavailable", api_base=api_base)
        return {}
    except httpx.HTTPError as e:
        logger.warning("api_error", error=str(e))
        return {}


# =============================================================================
# Config Command Group
# =============================================================================


@cli.group()
def config() -> None:
    """
    Manage LLM provider configuration.

    Configure providers (OpenAI, Ollama, Anthropic, etc.) interactively
    via the wizard, or manage them directly with subcommands.
    Providers are persisted to ``~/.heretek-swarm/config.json`` and loaded
    on the next swarm startup.
    """


@config.command("wizard")
def config_wizard() -> None:
    """
    Interactive configuration wizard for adding LLM providers.

    Prompts you through selecting a provider, entering API keys and
    endpoints, validating the connection, and saving to config.
    No .env editing required.
    """
    logger.info("config_wizard_command")
    run_wizard()


@config.command("list")
def config_list() -> None:
    """
    List all configured LLM providers.

    Shows provider name, type, default model, status, and whether
    each is the default provider.
    """
    logger.info("config_list_command")
    providers = list_configured_providers()

    if not providers:
        click.echo("No LLM providers configured.")
        click.echo("Run 'heretek-swarm config wizard' to add one.")
        return

    click.echo("")
    click.echo(f"Configured LLM Providers ({len(providers)})")
    click.echo("=" * 60)

    for p in providers:
        name = p.get("name", p.get("type", "?"))
        pid = p.get("id", "?")
        model = p.get("defaultModel", "(none)")
        ptype = p.get("type", "?")
        enabled = p.get("isEnabled", True)
        is_default = p.get("isDefault", False)
        base_url = p.get("baseUrl", "?")

        status_icon = "[+]" if enabled else "[-]"
        default_tag = click.style(" [default]", bold=True) if is_default else ""

        click.echo(f"\n  {name}{default_tag}")
        click.echo(f"    ID:      {pid[:8]}...{pid[-4:]}")
        click.echo(f"    Type:    {ptype}")
        click.echo(f"    Model:   {model}")
        click.echo(f"    URL:     {base_url}")
        click.echo(f"    Status:  {status_icon} {'Enabled' if enabled else 'Disabled'}")

    click.echo("")


@config.command("remove")
@click.argument("provider_id")
def config_remove(provider_id: str) -> None:
    """
    Remove a configured LLM provider by its ID (full or partial).

    PROVIDER_ID is the provider's UUID (you can provide the first
    8+ characters for partial matching).
    """
    logger.info("config_remove_command", provider_id=provider_id)
    providers = list_configured_providers()

    # Try exact match first, then partial
    match = None
    for p in providers:
        pid = p.get("id", "")
        if pid == provider_id:
            match = p
            break
    if match is None:
        for p in providers:
            pid = p.get("id", "")
            if pid.startswith(provider_id):
                match = p
                break

    if match is None:
        click.echo(f"Provider with ID '{provider_id}' not found.")
        click.echo("Run 'heretek-swarm config list' to see configured providers.")
        return

    name = match.get("name", match.get("type", "?"))
    confirm = click.prompt(
        f"Remove provider '{name}' ({match['id'][:8]}...)?",
        type=bool,
        default=False,
        show_default=True,
    )

    if not confirm:
        click.echo("Cancelled.")
        return

    removed = remove_provider(match["id"])
    if removed:
        click.echo(f"✓ Removed provider: {name}")
    else:
        click.echo("Failed to remove provider.")


@config.command("set-default")
@click.argument("provider_id")
def config_set_default(provider_id: str) -> None:
    """
    Set a provider as the default for routing.

    PROVIDER_ID is the provider's UUID (first 8+ chars for partial match).
    """
    logger.info("config_set_default_command", provider_id=provider_id)
    providers = list_configured_providers()

    match = None
    for p in providers:
        pid = p.get("id", "")
        if pid == provider_id:
            match = p
            break
    if match is None:
        for p in providers:
            pid = p.get("id", "")
            if pid.startswith(provider_id):
                match = p
                break

    if match is None:
        click.echo(f"Provider with ID '{provider_id}' not found.")
        click.echo("Run 'heretek-swarm config list' to see configured providers.")
        return

    success = set_default_provider(match["id"])
    if success:
        name = match.get("name", match.get("type", "?"))
        click.echo(f"✓ {name} set as default provider.")
    else:
        click.echo("Failed to set default provider.")


@config.command("validate")
@click.argument("provider_id", required=False, default=None)
def config_validate(provider_id: str | None) -> None:
    """
    Validate connectivity for configured providers.

    If PROVIDER_ID is given (first 8+ chars), validates only that
    provider. Otherwise validates all configured providers.
    """
    logger.info("config_validate_command", provider_id=provider_id)
    providers = list_configured_providers()

    if not providers:
        click.echo("No providers configured. Run 'heretek-swarm config wizard' first.")
        return

    targets: list[dict[str, Any]] = []
    if provider_id:
        for p in providers:
            pid = p.get("id", "")
            if pid == provider_id:
                targets.append(p)
                break
        if not targets:
            for p in providers:
                pid = p.get("id", "")
                if pid.startswith(provider_id):
                    targets.append(p)
                    break
        if not targets:
            click.echo(f"Provider with ID '{provider_id}' not found.")
            return
    else:
        targets = providers

    click.echo("")
    click.echo("Provider Validation")
    click.echo("=" * 50)

    all_passed = True
    for p in targets:
        name = p.get("name", p.get("type", "?"))
        pid = p.get("id", "")[:8]
        ptype = p.get("type", "")
        base_url = p.get("baseUrl", "")
        api_key = p.get("apiKey")
        default_model = p.get("defaultModel", "")

        # Resolve provider_id for validator dispatch
        provider_lookup_id = None
        for pid_candidate, info in AVAILABLE_PROVIDERS.items():
            if info["type"] == ptype:
                provider_lookup_id = pid_candidate
                break

        click.echo(f"\n  {name} ({pid}...)")
        click.echo(f"    URL:   {base_url}")
        click.echo(f"    Model: {default_model}")

        if provider_lookup_id is None:
            click.echo(click.style("    ✗ Unknown provider type, skipping validation", fg="yellow"))
            all_passed = False
            continue

        result = validate_provider(provider_lookup_id, api_key, base_url, default_model)
        if result.get("valid"):
            msg = result.get("message", "Valid")
            click.echo(click.style(f"    [+] {msg}", fg="green"))
        else:
            err = result.get("error", "Unknown error")
            click.echo(click.style(f"    [-] {err}", fg="red"))
            all_passed = False

    click.echo("")
    if all_passed:
        click.echo(click.style(" [+] All validations passed", fg="green"))
    else:
        click.echo(click.style(" [-] Some validations failed", fg="red"))

    click.echo("")


def main() -> None:
    """Entry point for the CLI."""
    cli(prog_name="heretek-swarm")


# Register the goal command group
from heretek_swarm.cli.goal_commands import goal
cli.add_command(goal)

main = cli


if __name__ == "__main__":
    main()
