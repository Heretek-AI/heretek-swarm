"""Backward-compat shim for moved security/ package.

Phase 2 Task 3 moved security/ from backend/heretek_swarm/security/
to packages/core/src/heretek_swarm_core/security/. Importing this
package as ``heretek_swarm.security`` still works — it re-exports
the canonical symbols from the new location.

We bypass ``heretek_swarm_core.__init__.py`` because loading it
triggers a circular import through ``actors.supervisor`` →
``mixins`` → ``collective`` → ``consciousness.fep_active_inference``
→ back here. Stubs are pre-registered in ``sys.modules`` at module
import time so dotted-name lookups resolve without running the real
parent init.
"""

from __future__ import annotations

# Pre-register stubs BEFORE relative imports can fire — the
# shim is loaded during ``heretek_swarm`` package init, when
# ``heretek_swarm_core.__init__`` would cycle through
# ``actors.supervisor``.
import importlib.util as _importlib_util
import sys as _sys
from pathlib import Path as _Path
from types import ModuleType as _ModuleType
from typing import Any as _Any

_CORE_SECURITY_ROOT = _Path("/home/john/Projects/heretek-swarm/packages/core/src/heretek_swarm_core/security")
_CORE_ROOT = _CORE_SECURITY_ROOT.parent

# CRITICAL: point this shim's __path__ at the new location so
# ``from heretek_swarm.security.immune import …`` resolves the
# submodule via the standard loader.
__path__ = [str(_CORE_SECURITY_ROOT)]  # type: ignore[misc]

if "heretek_swarm_core" not in _sys.modules:
    _stub = _ModuleType("heretek_swarm_core")
    _stub.__path__ = [str(_CORE_ROOT)]
    _sys.modules["heretek_swarm_core"] = _stub
if "heretek_swarm_core.security" not in _sys.modules:
    _stub = _ModuleType("heretek_swarm_core.security")
    _stub.__path__ = [str(_CORE_SECURITY_ROOT)]
    _sys.modules["heretek_swarm_core.security"] = _stub


def _load(module_name: str, file_name: str = "__init__.py") -> _Any:
    fqn = f"heretek_swarm_core.security.{module_name}"
    file_path = _CORE_SECURITY_ROOT / module_name / file_name
    if not file_path.exists():
        file_path = _CORE_SECURITY_ROOT / f"{module_name}.py"
    spec = _importlib_util.spec_from_file_location(fqn, str(file_path))
    module = _importlib_util.module_from_spec(spec)
    if file_path.name == "__init__.py":
        module.__path__ = [str(file_path.parent)]
    _sys.modules[fqn] = module
    spec.loader.exec_module(module)
    return module


_LAZY_NAMES = {
    "adversarial": "adversarial.py",
    "anomaly_detection": "anomaly_detection.py",
    "baseline_update": "baseline_update.py",
    "behavioral_baseline": "behavioral_baseline.py",
    "ddos_protection": "ddos_protection.py",
    "guardrails": "guardrails.py",
    "immune": "immune.py",
    "immune_engine": "immune_engine.py",
    "immune_types": "immune_types.py",
    "rate_limiter": "rate_limiter.py",
    "safe01_anomaly_response": "safe01_anomaly_response.py",
    "sandbox": "sandbox.py",
    "threat_detection": "threat_detection.py",
    "validators": "validators.py",
    "zero_trust": "zero_trust/__init__.py",
}


def __getattr__(name: str) -> _Any:
    if name in _LAZY_NAMES:
        target = _LAZY_NAMES[name]
        if "/" in target:
            pkg, fname = target.split("/")
            return _load(pkg, fname)
        return _load(name, target)
    raise AttributeError(f"module 'heretek_swarm.security' has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(_LAZY_NAMES)
