"""CLI for running audit scans and generating reports."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

# Ensure heretek_swarm is importable from the repo root.
# The audit package lives at heretek-swarm/heretek_swarm/audit/.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_HERETEK_PACKAGE = _REPO_ROOT / "heretek-swarm"
if str(_HERETEK_PACKAGE) not in sys.path:
    sys.path.insert(0, str(_HERETEK_PACKAGE))

from heretek_swarm.audit import (
    AuditFinding,
    generate_report,
    scan_directory,
)


@click.command()
@click.option(
    "--directory", "-d",
    default="heretek-swarm/heretek_swarm",
    help="Root directory to scan (default: heretek-swarm/heretek_swarm)",
)
@click.option(
    "--output", "-o",
    default=None,
    help="Output file path. If not provided, prints to stdout.",
)
@click.option(
    "--severity", "-s",
    type=click.Choice(["CRITICAL", "WARNING", "INFO", "all"], case_sensitive=False),
    default="all",
    help="Filter findings by severity level.",
)
@click.option(
    "--format", "-f",
    type=click.Choice(["markdown", "json"], case_sensitive=False),
    default="markdown",
    help="Output format.",
)
@click.option(
    "--patterns",
    default=None,
    help="Comma-separated list of pattern names to run (default: all).",
)
def cli(
    directory: str,
    output: str | None,
    severity: str,
    format: str,
    patterns: str | None,
) -> None:
    """Run the stub detection audit and generate a report.

    Examples:

        python audit/cli.py --directory heretek-swarm/heretek_swarm --output audit-report.md

        python -m heretek_swarm.audit.cli -d heretek-swarm/heretek_swarm -o report.md

        python -m heretek_swarm.audit.cli --severity CRITICAL -f json
    """
    scan_root = Path(directory).resolve()
    if not scan_root.is_dir():
        click.echo(f"Error: directory not found: {scan_root}", err=True)
        sys.exit(1)

    pattern_list = [p.strip() for p in patterns.split(",")] if patterns else None
    extensions = {".py", ".js", ".ts", ".jsx", ".tsx"}

    click.echo(f"Scanning {scan_root} ...")
    findings: list[AuditFinding] = []
    findings.extend(scan_directory(scan_root, patterns=pattern_list, extensions=extensions))
    click.echo(f"Found {len(findings)} finding(s).")

    if severity.lower() != "all":
        findings = [f for f in findings if f.severity.upper() == severity.upper()]
        click.echo(f"Filtered to {len(findings)} {severity.upper()} finding(s).")

    if format.lower() == "json":
        body = json.dumps(
            [
                {
                    "file": f.file,
                    "line": f.line,
                    "pattern_name": f.pattern_name,
                    "severity": f.severity,
                    "description": f.description,
                }
                for f in findings
            ],
            indent=2,
        )
    else:
        body = generate_report(findings, title="Stub Detection Audit Report")

    if output:
        Path(output).write_text(body, encoding="utf-8")
        click.echo(f"Report written to: {output}")
    else:
        click.echo(body)


if __name__ == "__main__":
    cli()
