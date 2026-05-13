"""
CLI Package

Command-line interface utilities for Heretek Swarm.
"""

# Re-export the CLI group and commands from the cli module.
# Note: cli.py and cli/ share a name — Python prioritizes packages over modules
# with the same name. We import the module explicitly by file path to avoid
# the naming conflict.
import importlib.util
import sys
from pathlib import Path

from heretek_swarm.cli.config_loader import load_infrastructure_config

_spec = importlib.util.spec_from_file_location(
    "heretek_swarm._cli_module", Path(__file__).parent.parent / "cli.py"
)
_cli_module = importlib.util.module_from_spec(_spec)
sys.modules["heretek_swarm._cli_module"] = _cli_module
_spec.loader.exec_module(_cli_module)

from heretek_swarm._cli_module import (
    _check_service_health,
    _display_consensus_results,
    _display_daemon_status,
    _display_deliberation_results,
    _display_routed_result,
    _handle_signal,
    _print_infrastructure_config,
    _print_startup_banner,
    _query_daemon_socket,
    _run_consensus,
    _shutdown_event,
    _start_autonomous_swarm,
    check_compose_plugin,
    check_container_runtime,
    cli,
    config,
    config_list,
    config_remove,
    config_set_default,
    config_validate,
    config_wizard,
    consensus,
    init,
    run,
    serve,
    status,
    stop,
    wizard,
)
from heretek_swarm.cli.config_wizard import (
    AVAILABLE_PROVIDERS,
    add_provider,
    list_configured_providers,
    prompt_for_provider,
    remove_provider,
    run_wizard,
    set_default_provider,
    validate_provider,
)

__all__ = [
    "AVAILABLE_PROVIDERS",
    "_check_service_health",
    "_display_consensus_results",
    "_display_daemon_status",
    "_display_deliberation_results",
    "_display_routed_result",
    "_handle_signal",
    "_print_infrastructure_config",
    "_print_startup_banner",
    "_query_daemon_socket",
    "_shutdown_event",
    "_start_autonomous_swarm",
    "add_provider",
    "check_compose_plugin",
    "check_container_runtime",
    "cli",
    "config",
    "config_list",
    "config_remove",
    "config_set_default",
    "config_validate",
    "config_wizard",
    "consensus",
    "init",
    "list_configured_providers",
    "load_infrastructure_config",
    "prompt_for_provider",
    "remove_provider",
    "run",
    "run_wizard",
    "serve",
    "set_default_provider",
    "status",
    "stop",
    "validate_provider",
    "wizard",
]
