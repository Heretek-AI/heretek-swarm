"""Tests for audit report generation."""

from heretek_swarm.audit import AuditFinding, generate_report, group_by_severity


class TestAuditFinding:
    """Test the AuditFinding dataclass."""

    def test_fields(self) -> None:
        f = AuditFinding(
            file="src/foo.py",
            line=10,
            pattern_name="PassOnlyStatement",
            severity="CRITICAL",
            description="Function body contains only `pass`.",
        )
        assert f.file == "src/foo.py"
        assert f.line == 10
        assert f.pattern_name == "PassOnlyStatement"
        assert f.severity == "CRITICAL"
        assert f.description == "Function body contains only `pass`."

    def test_severity_normalized_to_uppercase(self) -> None:
        f = AuditFinding(
            file="src/foo.py",
            line=1,
            pattern_name="X",
            severity="critical",
            description="",
        )
        assert f.severity == "CRITICAL"


class TestGroupBySeverity:
    """Test the group_by_severity helper."""

    def test_groups_critical(self) -> None:
        f1 = AuditFinding("a.py", 1, "P1", "CRITICAL", "d1")
        f2 = AuditFinding("b.py", 2, "P2", "CRITICAL", "d2")
        groups = group_by_severity([f1, f2])
        assert groups["CRITICAL"] == [f1, f2]
        assert groups["WARNING"] == []
        assert groups["INFO"] == []

    def test_groups_all_severities(self) -> None:
        f1 = AuditFinding("a.py", 1, "P1", "CRITICAL", "d1")
        f2 = AuditFinding("b.py", 2, "P2", "WARNING", "d2")
        f3 = AuditFinding("c.py", 3, "P3", "INFO", "d3")
        groups = group_by_severity([f1, f2, f3])
        assert len(groups["CRITICAL"]) == 1
        assert len(groups["WARNING"]) == 1
        assert len(groups["INFO"]) == 1

    def test_empty_list(self) -> None:
        groups = group_by_severity([])
        assert groups["CRITICAL"] == []
        assert groups["WARNING"] == []
        assert groups["INFO"] == []


class TestGenerateReport:
    """Test markdown report generation."""

    def test_empty_findings(self) -> None:
        report = generate_report([])
        assert "No findings" in report

    def test_includes_critical_section(self) -> None:
        findings = [
            AuditFinding("a.py", 1, "PassOnlyStatement", "CRITICAL",
                        "Function body only has pass."),
        ]
        report = generate_report(findings)
        assert "## CRITICAL" in report
        assert "PassOnlyStatement" in report
        assert "a.py:1" in report

    def test_includes_warning_section(self) -> None:
        findings = [
            AuditFinding("b.py", 5, "GenerateRandomFunction", "WARNING", "Sample function."),
        ]
        report = generate_report(findings)
        assert "## WARNING" in report
        assert "GenerateRandomFunction" in report

    def test_includes_info_section(self) -> None:
        findings = [
            AuditFinding("c.py", 9, "DuplicateClassDefinition", "INFO", "Class defined twice."),
        ]
        report = generate_report(findings)
        assert "## INFO" in report
        assert "DuplicateClassDefinition" in report

    def test_summary_table(self) -> None:
        findings = [
            AuditFinding("a.py", 1, "P1", "CRITICAL", "d1"),
            AuditFinding("a.py", 2, "P2", "CRITICAL", "d2"),
            AuditFinding("b.py", 3, "P3", "WARNING", "d3"),
        ]
        report = generate_report(findings)
        assert "| CRITICAL | 2 |" in report
        assert "| WARNING | 1 |" in report
        assert "| INFO | 0 |" in report

    def test_custom_title(self) -> None:
        report = generate_report([], title="Custom Report Title")
        assert "# Custom Report Title" in report

    def test_report_format(self) -> None:
        """Report must be valid markdown with correct structure."""
        findings = [
            AuditFinding("a.py", 1, "P1", "CRITICAL", "d1"),
        ]
        report = generate_report(findings, title="Test Report")
        # Must have all expected sections
        assert "# Test Report" in report
        assert "**Total findings:** 1" in report
        assert "## CRITICAL" in report
        assert "## WARNING" in report
        assert "## INFO" in report
        assert "## Summary" in report
