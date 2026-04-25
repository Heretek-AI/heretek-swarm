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

_spec = importlib.util.spec_from_file_location(
    "heretek_swarm._cli_module",
    "heretek_swarm/cli.py"
)
_cli_module = importlib.util.module_from_spec(_spec)
sys.modules["heretek_swarm._cli_module"] = _cli_module
_spec.loader.exec_module(_cli_module)

from heretek_swarm._cli_module import (
    cli,
    run,
    serve,
    _check_service_health,
    _start_autonomous_swarm,
    _shutdown_event,
    _handle_signal,
    check_container_runtime,
    check_compose_plugin,
)

__all__ = [
    "load_infrastructure_config",
    "cli",
    "run",
    "serve",
    "_check_service_health",
    "_start_autonomous_swarm",
    "_shutdown_event",
    "_handle_signal",
    "check_container_runtime",
    "check_compose_plugin",
]
