#!/usr/bin/env python3
"""
Automated triage classifier for CRITICAL audit findings.

Parses audit-report.md CRITICAL section, cross-references each finding with
AST analysis, and classifies into four buckets:
  1. WONTFIX  — intentional graceful degradation
  2. FIX      — dead code to remove
  3. REVIEW   — ambiguous, needs human judgment
  4. STUB     — pass-only stub to implement

Reduces 381 manual decisions to ~30 ambiguous REVIEW items.

Outputs: triage_data.json
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import NamedTuple


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent
AUDIT_REPORT = ROOT / "audit-report.md"
TRIAGE_JSON = ROOT / "triage_data.json"

# Source root is the nested heretek-swarm/ directory
SRC_ROOT = ROOT / "heretek-swarm" / "heretek_swarm"


# ---------------------------------------------------------------------------
# Four-bucket taxonomy
# ---------------------------------------------------------------------------
BUCKET_WONTFIX = "WONTFIX"       # intentional graceful degradation
BUCKET_FIX = "FIX"               # dead code to remove
BUCKET_REVIEW = "REVIEW"         # ambiguous, needs human judgment
BUCKET_STUB = "STUB"             # pass-only stub to implement

BUCKET_DESCRIPTIONS = {
    BUCKET_WONTFIX: "Intentional graceful degradation — function legitimately returns None/empty dict.",
    BUCKET_FIX: "Dead code — duplicate class definition, safe to remove.",
    BUCKET_REVIEW: "Ambiguous — needs human review to determine intent.",
    BUCKET_STUB: "Pass-only stub — function body contains only `pass`; needs real implementation.",
}


# ---------------------------------------------------------------------------
# Finding record
# ---------------------------------------------------------------------------
class Finding(NamedTuple):
    file: str
    line: int
    pattern: str
    description: str
    bucket: str
    action: str
    rationale: str


# ---------------------------------------------------------------------------
# Section 1: Parse audit-report.md CRITICAL section
# ---------------------------------------------------------------------------
CRITICAL_SECTION_RE = re.compile(
    r"^## CRITICAL\s*\n\s*\n?Found (\d+) critical issue\(s\)\.\s*\n(.*?)"
    r"(?=^## |\Z)",
    re.MULTILINE | re.DOTALL,
)

FINDING_RE = re.compile(
    r"`([^:`]+):(\d+)`\s*— \*\*(ReturnNone|PassOnlyStatement|ReturnEmptyDict|"
    r"DuplicateClassDefinition|RaiseNotImplementedError)\*\*\s*[:-]\s*(.+)",
    re.MULTILINE,
)


def parse_audit_report(path: Path) -> list[dict]:
    """Extract all CRITICAL findings from audit-report.md."""
    content = path.read_text(encoding="utf-8")
    idx = content.find("## CRITICAL")
    if idx < 0:
        raise ValueError("Could not find ## CRITICAL section in audit-report.md")

    # Find the end of the CRITICAL section (next ## heading or end of file)
    end_idx = len(content)
    for marker in ("\n## WARNING", "\n## Summary", "\n## Triage Notes"):
        m = content.find(marker, idx)
        if m > 0:
            end_idx = min(end_idx, m)

    body = content[idx:end_idx]

    m_total = re.search(r"Found (\d+) critical issue\(s\)", body)
    total = int(m_total.group(1)) if m_total else 0

    findings = []
    for m in FINDING_RE.finditer(body):
        findings.append({
            "file": m.group(1),
            "line": int(m.group(2)),
            "pattern": m.group(3),
            "description": m.group(4).strip(),
        })

    if len(findings) != total:
        print(
            f"WARNING: parsed {len(findings)} findings but report says {total}. "
            "Continuing with parsed count.",
            file=sys.stderr,
        )

    return findings


# ---------------------------------------------------------------------------
# Section 2: AST analysis helpers
# ---------------------------------------------------------------------------

def _get_source_lines(source: str) -> list[str]:
    """Return 1-indexed list of source lines (empty string for missing lines)."""
    lines = [""] + source.splitlines()  # dummy at index 0 so index 1 == first line
    return lines


def _get_function_for_line(
    tree: ast.AST,
    line_no: int,
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    """Find the function whose body contains the given line number."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                fn_start = node.lineno
                fn_end = node.end_lineno or fn_start + 1
                if fn_start <= line_no <= fn_end:
                    return node
    return None


def _is_inside_except(tree: ast.AST, line_no: int) -> bool:
    """Return True if the given line is inside an except handler block."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            handler_start = node.lineno
            handler_end = getattr(node, "end_lineno", handler_start + 1)
            if handler_start <= line_no <= handler_end:
                return True
    return False


def _get_return_type_annotation(
    tree: ast.AST,
    func: ast.FunctionDef | ast.AsyncFunctionDef,
) -> str | None:
    """Return the return type annotation string, e.g. 'None' or 'Optional[X]'."""
    if func.returns is None:
        return None
    # ast.unparse available in Python 3.9+; use repr as fallback
    try:
        return ast.unparse(func.returns)
    except Exception:
        return repr(func.returns)


def _scan_file_ast(path: Path, target_line: int) -> dict:
    """Run AST analysis on a Python file and return context for the target line."""
    try:
        source = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return {"error": "read_failed"}

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return {"error": "parse_failed"}

    func = _get_function_for_line(tree, target_line)
    if func is None:
        return {"error": "no_function_found"}

    return_type = _get_return_type_annotation(tree, func)
    in_except = _is_inside_except(tree, target_line)

    return {
        "function_name": func.name,
        "function_lineno": func.lineno,
        "function_end_lineno": getattr(func, "end_lineno", None),
        "return_type": return_type,
        "in_except_block": in_except,
        "source_lines": _get_source_lines(source),
    }


# ---------------------------------------------------------------------------
# Section 3: Classification rules
# ---------------------------------------------------------------------------

def classify_return_none(
    finding: dict,
    ast_context: dict,
) -> tuple[str, str, str]:
    """Classify a ReturnNone finding using return type annotation."""
    rt = ast_context.get("return_type", "") or ""
    func_name = ast_context.get("function_name", "")

    # Detect Optional or union-style None (Python 3.10+ emits "X | None")
    has_none = bool(re.search(r"\bOptional\b|\| None\b", rt))

    if not rt:
        bucket = BUCKET_REVIEW
        action = "REVIEW"
        rationale = (
            f"Function `{func_name}` returns None with no type annotation. "
            "Cannot determine intent from AST alone — needs human review."
        )
    elif rt in ("None", "Literal[None]"):
        bucket = BUCKET_REVIEW
        action = "REVIEW"
        rationale = (
            f"Function `{func_name}` has `-> {rt}` return type but still flagged. "
            "Likely graceful degradation for exhausted/error cases, but line was flagged "
            "so manual confirmation recommended."
        )
    elif has_none:
        bucket = BUCKET_WONTFIX
        action = "WONTFIX"
        rationale = (
            f"Function `{func_name}` has `-> {rt}` signature (None in union). "
            "Returning None is the documented API contract — graceful degradation, not a stub."
        )
    elif rt == "Any":
        bucket = BUCKET_REVIEW
        action = "REVIEW"
        rationale = (
            f"Function `{func_name}` has `-> Any` return type annotation. "
            "Cannot determine if None is intentional without full context."
        )
    else:
        bucket = BUCKET_STUB
        action = "STUB"
        rationale = (
            f"Function `{func_name}` has non-optional return type `{rt}` but "
            "unconditionally returns None. This is a stub — the return type "
            "promises data that is never provided."
        )

    return bucket, action, rationale


def classify_pass_only(
    finding: dict,
    ast_context: dict,
) -> tuple[str, str, str]:
    """Classify a PassOnlyStatement finding using except-block detection."""
    func_name = ast_context.get("function_name", "")
    in_except = ast_context.get("in_except_block", False)

    if in_except:
        bucket = BUCKET_WONTFIX
        action = "WONTFIX"
        rationale = (
            f"Function `{func_name}` `pass` at line {finding['line']} is inside "
            "an `except` block. This is intentional exception swallowing — "
            "a common and legitimate pattern."
        )
    else:
        bucket = BUCKET_STUB
        action = "STUB"
        rationale = (
            f"Function `{func_name}` body contains only `pass`. "
            "No real logic implemented — this is a stub requiring implementation."
        )

    return bucket, action, rationale


def classify_return_empty_dict(
    finding: dict,
    ast_context: dict,
) -> tuple[str, str, str]:
    """Classify a ReturnEmptyDict finding."""
    func_name = ast_context.get("function_name", "")
    rt = (ast_context.get("return_type", "") or "")

    has_none = bool(re.search(r"\bOptional\b|\| None\b", rt))

    if not rt:
        bucket = BUCKET_REVIEW
        action = "REVIEW"
        rationale = (
            f"Function `{func_name}` returns `{{}}` with no return type annotation. "
            "Cannot determine if empty dict is intentional or stub."
        )
    elif rt in ("None", "Literal[None]"):
        bucket = BUCKET_STUB
        action = "STUB"
        rationale = (
            f"Function `{func_name}` has `-> {rt}` return type but returns empty dict. "
            "Stub with mismatched return type annotation."
        )
    elif has_none:
        bucket = BUCKET_WONTFIX
        action = "WONTFIX"
        rationale = (
            f"Function `{func_name}` has `-> {rt}` signature returning empty dict. "
            "Intentional when no items match query/filters — graceful degradation."
        )
    else:
        bucket = BUCKET_REVIEW
        action = "REVIEW"
        rationale = (
            f"Function `{func_name}` returns `{{}}` with `-> {rt}`. "
            "May be intentional empty result or stub — needs human review."
        )

    return bucket, action, rationale


def classify_raise_not_implemented(
    finding: dict,
    ast_context: dict,
) -> tuple[str, str, str]:
    """Classify a RaiseNotImplementedError finding."""
    func_name = ast_context.get("function_name", "")

    bucket = BUCKET_REVIEW
    action = "REVIEW"
    rationale = (
        f"Function `{func_name}` raises NotImplementedError. "
        "May be abstract method (convert to @abstractmethod) or pending work. "
        "Needs human review to determine if subclasses already implement it."
    )

    return bucket, action, rationale


def classify_duplicate_class(
    finding: dict,
) -> tuple[str, str, str]:
    """Classify a DuplicateClassDefinition finding — always FIX."""
    class_name = ""
    m = re.search(r"Class `([^`]+)`", finding["description"])
    if m:
        class_name = m.group(1)

    bucket = BUCKET_FIX
    action = "FIX"
    rationale = (
        f"Class `{class_name}` is defined multiple times in "
        f"{finding['file']}:{finding['line']}. The first definition is dead code — "
        "the second definition shadows it. Remove the earlier duplicate."
    )

    return bucket, action, rationale


def classify_finding(finding: dict) -> Finding:
    """Apply classification rules to a single finding."""
    pattern = finding["pattern"]
    file_rel = finding["file"]
    line_no = finding["line"]

    # Resolve file path: audit-report.md uses `heretek_swarm/` prefix
    if file_rel.startswith("heretek_swarm/"):
        file_rel = file_rel[len("heretek_swarm/") :]
        src_file = SRC_ROOT / file_rel
    else:
        src_file = SRC_ROOT / file_rel

    ast_context = {}
    if file_rel.endswith(".py") and src_file.exists():
        ast_context = _scan_file_ast(src_file, line_no)
    elif file_rel.endswith(".py"):
        ast_context = {"error": "file_not_found"}

    # Route to pattern-specific classifier
    if pattern == "ReturnNone":
        bucket, action, rationale = classify_return_none(finding, ast_context)
    elif pattern == "PassOnlyStatement":
        bucket, action, rationale = classify_pass_only(finding, ast_context)
    elif pattern == "ReturnEmptyDict":
        bucket, action, rationale = classify_return_empty_dict(finding, ast_context)
    elif pattern == "RaiseNotImplementedError":
        bucket, action, rationale = classify_raise_not_implemented(finding, ast_context)
    elif pattern == "DuplicateClassDefinition":
        bucket, action, rationale = classify_duplicate_class(finding)
    else:
        bucket = BUCKET_REVIEW
        action = "REVIEW"
        rationale = f"Unknown pattern `{pattern}` — needs human review."

    return Finding(
        file=finding["file"],
        line=finding["line"],
        pattern=pattern,
        description=finding["description"],
        bucket=bucket,
        action=action,
        rationale=rationale,
    )


# ---------------------------------------------------------------------------
# Section 4: Main driver
# ---------------------------------------------------------------------------

def build_triage_report(findings: list[dict]) -> list[dict]:
    """Classify all findings and return as dicts for JSON serialization."""
    results = []
    for finding in findings:
        f = classify_finding(finding)
        results.append({
            "file": f.file,
            "line": f.line,
            "pattern": f.pattern,
            "description": f.description,
            "bucket": f.bucket,
            "action": f.action,
            "rationale": f.rationale,
        })
    return results


def bucket_summary(results: list[dict]) -> dict:
    """Build bucket counts from triage results."""
    counts: dict[str, int] = {}
    for r in results:
        counts[r["bucket"]] = counts.get(r["bucket"], 0) + 1
    return counts


def main() -> None:
    print("Parsing audit-report.md CRITICAL section...")
    findings = parse_audit_report(AUDIT_REPORT)
    print(f"  Found {len(findings)} CRITICAL findings")

    print("Running automated AST classification...")
    results = build_triage_report(findings)

    print("Writing triage_data.json...")
    with open(TRIAGE_JSON, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, ensure_ascii=False)

    summary = bucket_summary(results)
    print("\nBucket summary:")
    for bucket, count in sorted(summary.items()):
        print(f"  {bucket}: {count}")

    print(f"\nOutput: {TRIAGE_JSON}")
    print(f"Total findings: {len(results)}")

    # Verify all 381 findings classified
    if len(results) == 381:
        print("\n✅ All 381 findings classified.")
    else:
        print(
            f"\n⚠ Expected 381 findings but got {len(results)}. "
            "Check audit-report.md section format.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
