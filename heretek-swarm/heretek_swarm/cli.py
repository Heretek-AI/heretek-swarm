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
import httpx
import structlog

from heretek_swarm.cli.config_loader import load_infrastructure_config
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

@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """Heretek Swarm - Next-generation multi-agent system."""


@cli.command()
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


async def _start_autonomous_swarm(no_infra: bool = False) -> None:
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


@cli.command()
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
def run(detach: bool, nats_url: str, no_infra: bool) -> None:
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

    Examples:
        heretek-swarm run
        heretek-swarm run --detach
        heretek-swarm run --no-infra
        HERETEK_NATS_URL=nats://cluster1:4222,nats://cluster2:4222 heretek-swarm run
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
        # Fork process for daemon mode
        pid = os.fork()
        if pid > 0:
            click.echo(f"  ✓ Process started in background (PID: {pid})")
            click.echo("  Use 'kill {pid}' to stop, or check logs for status.")
            sys.exit(0)

    # Set up signal handlers
    shutdown_event = asyncio.Event()
    global _shutdown_event
    _shutdown_event = shutdown_event

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    click.echo("\nInitializing autonomous swarm...")
    click.echo(f"  NATS: {nats_url}")

    if not no_infra:
        # Print loaded infrastructure configuration
        _print_infrastructure_config(infra_config)

    try:
        # Run the async main
        asyncio.run(_start_autonomous_swarm(no_infra=no_infra))
    except KeyboardInterrupt:
        logger.info("shutdown_keyboard_interrupt")
        click.echo("\nShutdown complete.")
    except Exception as e:
        logger.error("startup_failure", error=str(e))
        click.echo(f"\n✗ Failed to start: {e}")
        sys.exit(1)


@cli.command()
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

    Examples:
        heretek-swarm serve
        heretek-swarm serve --host 127.0.0.1 --port 9000
        heretek-swarm serve --workers 4
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

    Fetches infrastructure configuration from the API and performs
    health checks on all configured services.
    """
    import time

    logger.info("status_command", api_base=api_base, timeout=timeout)

    if output_json:
        # JSON-only output: suppress all human-readable text
        pass
    else:
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
            import json
            click.echo(json.dumps({"error": f"Cannot connect to API server at {api_base}"}))
            sys.exit(2)
        click.echo("  ✗ Cannot connect to API server")
        click.echo(f"    Is the server running at {api_base}?")
        click.echo("    Start with: heretek-swarm serve")
        sys.exit(1)
    except httpx.HTTPError as e:
        if output_json:
            import json
            click.echo(json.dumps({"error": f"API error: {e}"}))
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


def main() -> None:
    """Entry point for the CLI."""
    cli(prog_name="heretek-swarm")


main = cli


if __name__ == "__main__":
    main()
