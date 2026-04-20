"""Tests for stub pattern detection."""

import re

from heretek_swarm.audit.stub_patterns import (
    scan_directory,
    scan_file,
)


class TestRegexPatterns:
    """Test that individual regex patterns match correctly."""

    def test_pass_only_matches_pass(self) -> None:
        """The pass-only regex matches bare 'pass' but not 'pass_function()'."""
        compiled = re.compile(r"^\s*pass\s*(?:#.*)?$")
        assert compiled.search("    pass") is not None
        assert compiled.search("    pass  # comment") is not None
        assert compiled.search("pass_function()") is None

    def test_return_empty_dict_matches(self) -> None:
        compiled = re.compile(r"^\s*return\s+{}\s*(?:#.*)?$")
        assert compiled.search("    return {}") is not None
        assert compiled.search("return {}  # empty") is not None
        assert compiled.search("return {1: 2}") is None

    def test_return_none_matches(self) -> None:
        compiled = re.compile(r"^\s*return\s+None\s*(?:#.*)?$")
        assert compiled.search("    return None") is not None
        # The optional comment group makes this match (trailing comment is allowed)
        assert compiled.search("return None  # no value") is not None
        assert compiled.search("return none") is None  # case-sensitive

    def test_raise_not_implemented_matches(self) -> None:
        compiled = re.compile(r"^\s*raise\s+NotImplementedError\b")
        assert compiled.search("    raise NotImplementedError") is not None
        # \b is a word boundary: between 'Error' and '(' the boundary holds
        assert compiled.search("raise NotImplementedError()") is not None
        assert compiled.search("raise NotImplemented") is None  # not the full name

    def test_set_interval_matches(self) -> None:
        compiled = re.compile(r"\bsetInterval\s*\(")
        assert compiled.search("setInterval(callback, 1000)") is not None
        assert compiled.search("window.setInterval(0)") is not None

    def test_generate_random_matches(self) -> None:
        compiled = re.compile(r"\bgenerateRandom\b")
        assert compiled.search("function generateRandom() {}") is not None

    def test_math_random_matches(self) -> None:
        compiled = re.compile(r"\bMath\.random\b")
        assert compiled.search("Math.random()") is not None


class TestScanFile:
    """Test the scan_file function."""

    def test_detects_pass_only(self, sample_python_file: str) -> None:
        findings = scan_file(sample_python_file)
        names = [f.pattern_name for f in findings]
        assert "PassOnlyStatement" in names

    def test_detects_return_empty_dict(self, sample_python_file: str) -> None:
        findings = scan_file(sample_python_file)
        names = [f.pattern_name for f in findings]
        assert "ReturnEmptyDict" in names

    def test_detects_return_none(self, sample_python_file: str) -> None:
        findings = scan_file(sample_python_file)
        names = [f.pattern_name for f in findings]
        assert "ReturnNone" in names

    def test_detects_raise_not_implemented(self, sample_python_file: str) -> None:
        findings = scan_file(sample_python_file)
        names = [f.pattern_name for f in findings]
        assert "RaiseNotImplementedError" in names

    def test_create_sample_functions_are_flagged(self, sample_python_file: str) -> None:
        """Functions named create_sample_* ARE flagged as SampleDataGenerator.

        The exclusion rule only applies to filenames (paths containing _sample/
        _test/_demo), not function names within Python source.
        """
        findings = scan_file(sample_python_file)
        names = [f.pattern_name for f in findings]
        assert "SampleDataGenerator" in names

    def test_scan_typescript_file(self, sample_typescript_file: str) -> None:
        findings = scan_file(sample_typescript_file)
        names = [f.pattern_name for f in findings]
        assert "SetIntervalJavaScript" in names
        assert "GenerateRandomFunction" in names
        assert "MathRandomJavaScript" in names

    def test_nonexistent_file_returns_empty(self, tmp_path: str) -> None:
        findings = scan_file(tmp_path / "does_not_exist.py")
        assert findings == []

    def test_filter_by_pattern_name(self, sample_python_file: str) -> None:
        findings = scan_file(sample_python_file, patterns=["PassOnlyStatement"])
        names = [f.pattern_name for f in findings]
        assert names == ["PassOnlyStatement"]


class TestScanDirectory:
    """Test the scan_directory aggregation."""

    def test_aggregates_multiple_files(self, tmp_path: str) -> None:
        """Scanning a directory returns findings from all matching files."""
        # Create two Python files with stub patterns
        p1 = tmp_path / "file1.py"
        p1.write_text("def f():\n    pass\n", encoding="utf-8")

        p2 = tmp_path / "file2.py"
        p2.write_text("def g():\n    return {}\n", encoding="utf-8")

        findings = scan_directory(tmp_path, extensions={".py"})
        names = [f.pattern_name for f in findings]
        assert "PassOnlyStatement" in names
        assert "ReturnEmptyDict" in names

    def test_respects_extension_filter(self, tmp_path: str) -> None:
        """Files with non-matching extensions are skipped."""
        p1 = tmp_path / "file1.py"
        p1.write_text("def f():\n    pass\n", encoding="utf-8")

        p2 = tmp_path / "file2.txt"
        p2.write_text("def f():\n    pass\n", encoding="utf-8")

        findings = scan_directory(tmp_path, extensions={".py"})
        assert all(f.file.endswith(".py") for f in findings)

    def test_excludes_dirs(self, tmp_path: str) -> None:
        """Files inside excluded directories are skipped."""
        sub = tmp_path / "tests"
        sub.mkdir()
        p = sub / "stub.py"
        p.write_text("def f():\n    pass\n", encoding="utf-8")

        findings = scan_directory(tmp_path, extensions={".py"})
        assert not any("tests/stub.py" in f.file for f in findings)

    def test_excludes_name_parts(self, tmp_path: str) -> None:
        """Files with _sample/_test/_demo as standalone name components are skipped.

        Note: `_sample_helper.py` (leading underscore) IS excluded because it
        contains `_sample` as a prefix token. Plain `sample_helper.py` is NOT
        excluded because `_sample` is not a standalone token in that name.
        """
        # This one IS excluded (has _sample as a prefix)
        p_excluded = tmp_path / "_sample_helper.py"
        p_excluded.write_text("def f():\n    pass\n", encoding="utf-8")

        # This one is NOT excluded (sample is embedded, no leading underscore)
        p_included = tmp_path / "sample_helper.py"
        p_included.write_text("def f():\n    return {}\n", encoding="utf-8")

        findings = scan_directory(tmp_path, extensions={".py"})
        excluded_found = [f for f in findings if "_sample_helper.py" in f.file]
        included_found = [f for f in findings if "sample_helper.py" in f.file]

        assert len(excluded_found) == 0, "_sample_helper.py should be excluded"
        assert len(included_found) == 1, "sample_helper.py should be included"
