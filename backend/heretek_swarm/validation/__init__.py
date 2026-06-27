"""Backward-compatibility shim for ``heretek_swarm.validation``.

The canonical implementation lives in ``heretek_swarm_core.validation``.
This package re-exports the public surface and forwards submodule
imports (``import heretek_swarm.validation.agent_messages``) to the
canonical home during the migration. Remove once all callers are
updated.

The ``__path__`` shim makes submodule resolution find files under
``heretek_swarm_core.validation``. The ``__getattr__`` shim makes
attribute access on the package itself (``from heretek_swarm.validation
import LLMOutputValidator``) work after either the canonical package
has been loaded or someone calls ``from heretek_swarm.validation``
at runtime — by which point both packages are fully initialized.
"""

from __future__ import annotations

from pathlib import Path as _Path

# Forward submodule resolution to the canonical package directory.
_canonical_pkg = (
    _Path(__file__).resolve().parent.parent.parent.parent
    / "packages"
    / "core"
    / "src"
    / "heretek_swarm_core"
    / "validation"
)
if _canonical_pkg.is_dir():
    __path__ = [str(_canonical_pkg)] + list(__path__)


def __getattr__(name: str):
    # Lazy proxy to heretek_swarm_core.validation so legacy
    # `from heretek_swarm.validation import X` keeps working
    # without triggering heretek_swarm_core's init at package
    # load time (which would create a circular import).
    import heretek_swarm_core.validation as _core

    return getattr(_core, name)


def __dir__() -> list[str]:
    import heretek_swarm_core.validation as _core

    return sorted(set(globals()) | set(dir(_core)))
