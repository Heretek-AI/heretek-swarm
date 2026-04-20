"""Tests for the Severity enum and helper functions."""

from heretek_swarm.audit.severity import Severity, is_critical, is_info, is_warning


class TestSeverityEnum:
    def test_has_critical_member(self) -> None:
        assert hasattr(Severity, "CRITICAL")

    def test_has_warning_member(self) -> None:
        assert hasattr(Severity, "WARNING")

    def test_has_info_member(self) -> None:
        assert hasattr(Severity, "INFO")

    def test_critical_is_not_equal_to_warning(self) -> None:
        assert Severity.CRITICAL != Severity.WARNING

    def test_all_three_members_are_distinct(self) -> None:
        """All three severity levels are distinct enum members."""
        assert len({Severity.CRITICAL, Severity.WARNING, Severity.INFO}) == 3


class TestSeverityHelpers:
    def test_is_critical_with_enum(self) -> None:
        assert is_critical(Severity.CRITICAL) is True
        assert is_critical(Severity.WARNING) is False
        assert is_critical(Severity.INFO) is False

    def test_is_critical_with_string(self) -> None:
        assert is_critical("CRITICAL") is True
        assert is_critical("critical") is True
        assert is_critical("WARNING") is False

    def test_is_warning_with_enum(self) -> None:
        assert is_warning(Severity.WARNING) is True
        assert is_warning(Severity.CRITICAL) is False
        assert is_warning(Severity.INFO) is False

    def test_is_warning_with_string(self) -> None:
        assert is_warning("WARNING") is True
        assert is_warning("warning") is True
        assert is_warning("INFO") is False

    def test_is_info_with_enum(self) -> None:
        assert is_info(Severity.INFO) is True
        assert is_info(Severity.CRITICAL) is False
        assert is_info(Severity.WARNING) is False

    def test_is_info_with_string(self) -> None:
        assert is_info("INFO") is True
        assert is_info("info") is True
        assert is_info("CRITICAL") is False
