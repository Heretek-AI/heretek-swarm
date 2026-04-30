"""
CLI Package

Command-line interface utilities for Heretek Swarm.
"""

from heretek_swarm.cli.config_loader import load_infrastructure_config

# Re-export the CLI group and commands from the cli module.
# Note: cli.py and cli/ share a name — Python prioritizes packages over modules
# with the same name. We import the module explicitly by file path to avoid
# the naming conflict.
import importlib.util
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "heretek_swarm._cli_module",
    Path(__file__).parent.parent / "cli.py"
)
_cli_module = importlib.util.module_from_spec(_spec)
sys.modules["heretek_swarm._cli_module"] = _cli_module
_spec.loader.exec_module(_cli_module)

from heretek_swarm._cli_module import (
    cli,
    run,
    serve,
    status,
    stop,
    _check_service_health,
    _display_daemon_status,
    _display_deliberation_results,
    _handle_signal,
    _print_infrastructure_config,
    _print_startup_banner,
    _query_daemon_socket,
    _shutdown_event,
    _start_autonomous_swarm,
    check_compose_plugin,
    check_container_runtime,
    init,
    wizard,
)

__all__ = [
    "load_infrastructure_config",
    "cli",
    "run",
    "serve",
    "status",
    "stop",
    "_check_service_health",
    "_display_daemon_status",
    "_display_deliberation_results",
    "_handle_signal",
    "_print_infrastructure_config",
    "_print_startup_banner",
    "_query_daemon_socket",
    "_shutdown_event",
    "_start_autonomous_swarm",
    "check_compose_plugin",
    "check_container_runtime",
    "init",
    "wizard",
]
