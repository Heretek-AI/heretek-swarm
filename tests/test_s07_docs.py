"""
S07 T02 — Documentation Refresh Verification Tests

Verifies that documentation accurately reflects post-M001 reality:
- 6 containers, 7 logical services including embedded mem0
- No stale "6 services" references without the embedded-mem0 qualifier
- mem0 status reflects "Embedded" (not "✅ Operational")
- No stale src/memory/mem0_backend.py paths
- DEPLOYMENT.md mentions mem0
- README.md updated to 2026-06-10
"""

import re
from pathlib import Path

REPO = Path(__file__).parent.parent


def read_doc(filename: str) -> str:
    return (REPO / filename).read_text()


# ── README.md ─────────────────────────────────────────────────────────────

def test_readme_no_bare_6_services():
    """README should not contain bare '6 services' without the 7-logical qualifier."""
    text = read_doc("README.md")
    # Allow the phrase only when accompanied by "7 logical" nearby
    # Find all lines with "6 services" and verify the context mentions 7 logical
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if "6 services" in line or "6 services" in line.lower():
            # Check this line + neighbors for "7 logical" or "7 logical services"
            context = "\n".join(lines[max(0, i - 1):i + 2])
            assert "7 logical" in context or "7 logical services" in context, (
                f"Line {i+1} has '6 services' without '7 logical' qualifier:\n{line}"
            )


def test_readme_has_7_logical_services():
    """README should mention '7 logical services' or equivalent."""
    text = read_doc("README.md")
    assert "7 logical" in text.lower() or "7 logical services" in text, (
        "README.md does not mention '7 logical services'"
    )


def test_readme_has_embedded_mem0():
    """README should mention mem0 as embedded in the services list."""
    text = read_doc("README.md")
    assert "mem0" in text.lower(), "README.md lacks mem0 reference"
    # Must reference the embedded nature or the persistent.py file
    assert "embedded" in text.lower() or "persistent.py" in text, (
        "README.md should mention mem0 as embedded or reference persistent.py"
    )


def test_readme_date_updated():
    """README Last Updated should be 2026-06-10."""
    text = read_doc("README.md")
    assert "2026-06-10" in text, "README.md Last Updated not set to 2026-06-10"


def test_readme_infrastructure_table_has_mem0():
    """Infrastructure table should include mem0 row."""
    text = read_doc("README.md")
    assert "**mem0**" in text, "README.md infrastructure table missing mem0 row"


# ── ARCHITECTURE.md ───────────────────────────────────────────────────────

def test_architecture_mem0_not_operational():
    """ARCHITECTURE.md should not claim mem0 is '✅ Operational' as a separate service."""
    text = read_doc("docs/ARCHITECTURE.md")
    # Check the infrastructure table row for mem0
    for line in text.splitlines():
        if "mem0" in line and "Operational" in line:
            # If mem0 has a status, it should be "Embedded" not "✅ Operational"
            assert "Embedded" in line, (
                f"ARCHITECTURE.md mem0 row should say Embedded, got:\n{line}"
            )


def test_architecture_mem0_embedded():
    """ARCHITECTURE.md should reflect mem0 as embedded in API container."""
    text = read_doc("docs/ARCHITECTURE.md")
    assert "Embedded in API container" in text or "embedded" in text.lower(), (
        "ARCHITECTURE.md should state mem0 is embedded"
    )


def test_architecture_date_updated():
    """ARCHITECTURE.md should have updated date to 2026-06-10."""
    text = read_doc("docs/ARCHITECTURE.md")
    assert "2026-06-10" in text, "ARCHITECTURE.md date not updated to 2026-06-10"


# ── MEMORY_SYSTEM.md ──────────────────────────────────────────────────────

def test_memory_system_no_stale_path():
    """MEMORY_SYSTEM.md must not reference stale src/memory/mem0_backend.py path."""
    text = read_doc("docs/MEMORY_SYSTEM.md")
    assert "src/memory/mem0_backend.py" not in text, (
        "MEMORY_SYSTEM.md still references stale src/memory/mem0_backend.py"
    )


def test_memory_system_has_correct_path():
    """MEMORY_SYSTEM.md should reference backend/heretek_swarm/memory/persistent.py."""
    text = read_doc("docs/MEMORY_SYSTEM.md")
    assert "backend/heretek_swarm/memory/persistent.py" in text, (
        "MEMORY_SYSTEM.md missing updated persistent.py path"
    )


def test_memory_system_date_updated():
    """MEMORY_SYSTEM.md should have updated date."""
    text = read_doc("docs/MEMORY_SYSTEM.md")
    assert "2026-06-10" in text, "MEMORY_SYSTEM.md date not updated to 2026-06-10"


# ── DEPLOYMENT.md ─────────────────────────────────────────────────────────

def test_deployment_mentions_mem0():
    """DEPLOYMENT.md should mention mem0."""
    text = read_doc("docs/DEPLOYMENT.md")
    assert "mem0" in text.lower(), "DEPLOYMENT.md does not mention mem0"


def test_deployment_has_7_logical():
    """DEPLOYMENT.md should mention 7 logical services."""
    text = read_doc("docs/DEPLOYMENT.md")
    assert "7 logical" in text, "DEPLOYMENT.md missing '7 logical' reference"


def test_deployment_date_updated():
    """DEPLOYMENT.md date should be updated."""
    text = read_doc("docs/DEPLOYMENT.md")
    assert "2026-06-10" in text, "DEPLOYMENT.md date not updated to 2026-06-10"


# ── Cross-check: no stale "6 services" anywhere ───────────────────────────

def test_no_stale_6_services_across_docs():
    """No doc should have '6 services' without '7 logical' nearby."""
    doc_files = [
        "README.md",
        "docs/ARCHITECTURE.md",
        "docs/MEMORY_SYSTEM.md",
        "docs/DEPLOYMENT.md",
    ]
    for doc_path in doc_files:
        text = read_doc(doc_path)
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if "6 services" in line or "6 services" in line.lower():
                context = "\n".join(lines[max(0, i - 1):i + 2])
                acceptable = "7 logical" in context or "7 logical services" in context
                assert acceptable, (
                    f"{doc_path} line {i+1}: '6 services' without '7 logical' qualifier:\n{line}"
                )


def test_no_src_memory_path_anywhere():
    """No documentation should reference stale src/memory/ paths."""
    doc_files = [
        "README.md",
        "docs/ARCHITECTURE.md",
        "docs/MEMORY_SYSTEM.md",
        "docs/DEPLOYMENT.md",
        "docs/architecture/memory-system.md",
    ]
    for doc_path in doc_files:
        text = read_doc(doc_path)
        assert "src/memory/" not in text, (
            f"{doc_path} contains stale src/memory/ path"
        )
