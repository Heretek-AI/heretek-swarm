"""Verify that no production .py file contains a silent ``except ... : pass``.

Uses the ``ast`` module to parse every production file under
``heretek_swarm/`` and assert that no ``except`` handler body consists
solely of a ``pass`` statement (or a docstring / expression-statement
pass equivalent).

This is a durable regression gate for Slice S02 ("Error Handling
Hardening"), which replaced 28 formerly-silent exception handlers with
structured ``logger.debug()``, ``logger.warning()``, or
``logger.exception()`` calls.
"""

from __future__ import annotations

import ast
import pathlib


_HERE = pathlib.Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent
_BACKEND = _PROJECT_ROOT / "backend"
_HERETEK_SWARM = _BACKEND / "heretek_swarm"


def _is_silent_pass_handler(node: ast.ExceptHandler) -> bool:
    """Return True when the handler body is a silent no-op (just ``pass``,
    or a single docstring / expr that evaluates to nothing followed by
    nothing else).

    Examples of matched patterns
    ----------------------------
    .. code-block:: python

        except ValueError:
            pass

        except KeyError:
            "fall through"  # expression-stmt with a doc-like string

    False negatives are fine for safety; false positives would be bad
    (we don't want to flag genuinely non-silent handlers), so we only
    match the most trivial ``pass`` body.
    """
    body = node.body
    if not body:
        return True
    if len(body) == 1 and isinstance(body[0], ast.Pass):
        return True
    # Single expression statement whose value is a string constant
    # (common pattern for "intentional no-op" documentation).
    if (
        len(body) == 1
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        return True
    return False


class SilentPassVisitor(ast.NodeVisitor):
    """Walk an AST and collect every silent ``except`` handler."""

    def __init__(self) -> None:
        self.violations: list[tuple[int, str]] = []

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if _is_silent_pass_handler(node):
            self.violations.append((node.lineno, ast.unparse(node).strip()))
        self.generic_visit(node)


def discover_production_files() -> list[pathlib.Path]:
    """Return every ``.py`` file under ``heretek_swarm/``."""
    if not _HERETEK_SWARM.is_dir():
        raise FileNotFoundError(
            f"Production source directory not found: {_HERETEK_SWARM}"
        )
    return sorted(p for p in _HERETEK_SWARM.rglob("*.py") if p.is_file())


def test_no_silent_passes() -> None:
    """Assert zero ``except ... : pass`` handlers in production code."""
    violations: list[str] = []
    for filepath in discover_production_files():
        source = filepath.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(filepath))
        except SyntaxError as exc:
            # A broken file is an automatic failure — it should be fixed.
            violations.append(
                f"{filepath.relative_to(_PROJECT_ROOT)}: SyntaxError — {exc}"
            )
            continue
        visitor = SilentPassVisitor()
        visitor.visit(tree)
        for lineno, snippet in visitor.violations:
            violations.append(
                f"{filepath.relative_to(_PROJECT_ROOT)}:{lineno}: {snippet}"
            )

    assert violations == [], (
        f"Found {len(violations)} silent except-pass handler(s) in production code:\n"
        + "\n".join(violations)
    )
