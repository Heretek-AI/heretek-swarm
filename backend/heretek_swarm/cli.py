"""
Re-export stub — all CLI symbols now live in the ``cli/`` subpackage.

Import ``heretek_swarm.cli`` (the package) directly; this module is retained
only for backward-compatible filesystem visibility.
"""

from heretek_swarm.cli import (  # noqa: F401
    cli,
    config,
    config_wizard,
    consensus,
    deploy,
    init,
    main,
    run,
    serve,
    status,
    stop,
    wizard,
)
