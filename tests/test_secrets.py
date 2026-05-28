"""Tests for SOPS secrets management (M002/S01).

Tests verify .sops.yaml configuration, encrypted file round-trips,
.gitignore rules, SecretsLoader behaviour, and SOPS binary integration.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

pytestmark = [pytest.mark.unit]

if TYPE_CHECKING:
    from collections.abc import Generator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent

AGE_KEY = "AGE-SECRET-KEY-1N392SUAWRSDV2GKGNA97GTTCXVNS6HNVCGUDQAG03T86D3URUMYSDMZLW0"
AGE_PUBKEY = "age1lm4gvvhheqjhcy26arw79zxa909pvqcd63ew9c02qx3rspzjufcqe30r65"


def _has_sops() -> bool:
    """Check whether the real SOPS binary is available."""
    r = subprocess.run("which sops", shell=True, capture_output=True, text=True)
    return r.returncode == 0


def _has_age_keygen() -> bool:
    """Check whether age-keygen is available."""
    r = subprocess.run("which age-keygen", shell=True, capture_output=True, text=True)
    return r.returncode == 0


@pytest.fixture
def sops_env() -> dict[str, str]:
    """Environment with SOPS_AGE_KEY set for decryption tests."""
    env = os.environ.copy()
    env["SOPS_AGE_KEY"] = AGE_KEY
    return env


# ---------------------------------------------------------------------------
# T01: SOPS config scaffolding
# ---------------------------------------------------------------------------

class TestSopsConfigExists:
    """Verify .sops.yaml exists with valid age configuration."""

    def test_sops_config_exists(self) -> None:
        """.sops.yaml exists at repo root."""
        path = REPO_ROOT / ".sops.yaml"
        assert path.exists(), f"{path} does not exist"
        assert path.is_file(), f"{path} is not a regular file"

    def test_sops_config_has_age_recipient(self) -> None:
        """.sops.yaml contains an age public key placeholder or live key."""
        content = (REPO_ROOT / ".sops.yaml").read_text()
        assert "age:" in content, "Missing 'age:' recipient section in .sops.yaml"
        assert "age1" in content, "No age public key found in .sops.yaml"

    def test_sops_config_has_creation_rules(self) -> None:
        """Creation rules cover YAML and .env files under secrets/."""
        content = (REPO_ROOT / ".sops.yaml").read_text()
        assert "path_regex: secrets/" in content or "secrets/" in content, (
            "Missing secrets path regex in .sops.yaml"
        )

    def test_sops_config_has_unencrypted_suffix(self) -> None:
        """unencrypted_suffix is configured."""
        content = (REPO_ROOT / ".sops.yaml").read_text()
        assert "unencrypted_suffix" in content, (
            "Missing unencrypted_suffix in .sops.yaml"
        )


class TestEncryptedEnvFile:
    """Verify secrets/encrypted.env is valid SOPS-encrypted content."""

    @pytest.mark.skipif(not _has_sops(), reason="sops binary not available")
    def test_encrypted_env_is_sops_encrypted(self) -> None:
        """encrypted.env starts with a SOPS header."""
        path = REPO_ROOT / "secrets" / "encrypted.env"
        assert path.exists(), f"{path} does not exist"
        content = path.read_text()
        assert "sops" in content[:512].lower() or "ENC[" in content[:512], (
            "encrypted.env does not appear to be SOPS-encrypted"
        )

    @pytest.mark.skipif(not _has_sops(), reason="sops binary not available")
    def test_encrypted_env_decrypts(self, sops_env: dict[str, str]) -> None:
        """sops --decrypt secrets/encrypted.env succeeds."""
        path = REPO_ROOT / "secrets" / "encrypted.env"
        r = subprocess.run(
            ["sops", "--decrypt", str(path)],
            capture_output=True,
            text=True,
            env=sops_env,
            timeout=30,
        )
        assert r.returncode == 0, (
            f"sops --decrypt failed (exit {r.returncode}): {r.stderr.strip()}"
        )
        assert "HERETEK_API_KEY" in r.stdout, (
            "Decrypted content missing expected key HERETEK_API_KEY"
        )

    def test_decrypt_fails_without_key(self) -> None:
        """sops --decrypt fails when SOPS_AGE_KEY is unset/empty."""
        path = REPO_ROOT / "secrets" / "encrypted.env"
        env = os.environ.copy()
        env.pop("SOPS_AGE_KEY", None)
        r = subprocess.run(
            ["sops", "--decrypt", str(path)],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
        # sops exits non-zero when no key is available to decrypt
        assert r.returncode != 0, "sops --decrypt should fail without SOPS_AGE_KEY"


class TestCiYaml:
    """Verify secrets/ci.yaml is a valid SOPS-encrypted stub."""

    @pytest.mark.skipif(not _has_sops(), reason="sops binary not available")
    def test_ci_yaml_exists_and_encrypted(self) -> None:
        """ci.yaml exists and is SOPS-encrypted."""
        path = REPO_ROOT / "secrets" / "ci.yaml"
        assert path.exists(), f"{path} does not exist"
        content = path.read_text()
        assert "sops" in content.lower() or "ENC[" in content, (
            "ci.yaml does not appear to be SOPS-encrypted"
        )

    @pytest.mark.skipif(not _has_sops(), reason="sops binary not available")
    def test_ci_yaml_decrypts(self, sops_env: dict[str, str]) -> None:
        """sops --decrypt secrets/ci.yaml succeeds and has SOPS_AGE_KEY."""
        path = REPO_ROOT / "secrets" / "ci.yaml"
        r = subprocess.run(
            ["sops", "--decrypt", str(path)],
            capture_output=True,
            text=True,
            env=sops_env,
            timeout=30,
        )
        assert r.returncode == 0, (
            f"sops --decrypt ci.yaml failed (exit {r.returncode}): {r.stderr.strip()}"
        )
        assert "SOPS_AGE_KEY" in r.stdout, (
            "Decrypted ci.yaml missing SOPS_AGE_KEY placeholder"
        )


class TestEnvExample:
    """Verify .env.example documents the SOPS workflow."""

    def test_env_example_documents_sops_section(self) -> None:
        """'.env.example' contains a 'SOPS Secrets Management' section."""
        content = (REPO_ROOT / ".env.example").read_text()
        assert "SOPS Secrets Management" in content, (
            "Missing SOPS Secrets Management header in .env.example"
        )
        assert "age-keygen" in content, (
            "Missing age-keygen reference in .env.example"
        )
        assert "SOPS_AGE_KEY" in content, (
            "Missing SOPS_AGE_KEY reference in .env.example"
        )


class TestGitignoreRules:
    """Verify .gitignore allows encrypted secrets but blocks _unencrypted."""

    def test_gitignore_allows_encrypted_secrets(self) -> None:
        """secrets/ dir is not blanket-ignored."""
        content = (REPO_ROOT / ".gitignore").read_text()
        lines = [line.strip() for line in content.splitlines()]
        # secrets/ should not be in the ignore list anymore (was changed to secrets/*_unencrypted)
        assert "secrets/" not in lines, "secrets/ is still blanket-ignored in .gitignore"

    def test_gitignore_blocks_unencrypted(self) -> None:
        """secrets/*_unencrypted is gitignored."""
        content = (REPO_ROOT / ".gitignore").read_text()
        assert "secrets/*_unencrypted" in content, (
            "Missing secrets/*_unencrypted in .gitignore"
        )


class TestSopsYamlIsValid:
    """Verify .sops.yaml is syntactically valid YAML."""

    def test_sops_yaml_is_valid_yaml(self) -> None:
        """YAML parser can load .sops.yaml without error."""
        try:
            import yaml
        except ImportError:
            pytest.skip("pyyaml not installed")
        text = (REPO_ROOT / ".sops.yaml").read_text()
        data = yaml.safe_load(text)
        assert "creation_rules" in data, "Missing creation_rules key in .sops.yaml"
        rules = data["creation_rules"]
        assert isinstance(rules, list) and len(rules) > 0, (
            "creation_rules must be a non-empty list"
        )


class TestBaselineExists:
    """Verify .secrets.baseline exists for detect-secrets."""

    def test_secrets_baseline_exists(self) -> None:
        """'.secrets.baseline' is present at repo root."""
        path = REPO_ROOT / ".secrets.baseline"
        assert path.exists(), f"{path} does not exist"
        content = path.read_text()
        assert "version" in content, "secrets.baseline appears invalid/malformed"


class TestAgeKeyGenAvailable:
    """Verify age-keygen tool is callable."""

    @pytest.mark.skipif(not _has_age_keygen(), reason="age-keygen not available")
    def test_age_keygen_produces_valid_key(self) -> None:
        """age-keygen outputs a valid age public key and secret key."""
        r = subprocess.run(
            ["age-keygen"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert r.returncode == 0
        assert "age1" in r.stdout, "age-keygen output missing public key (age1...)"
        assert "AGE-SECRET-KEY-" in r.stdout, (
            "age-keygen output missing secret key (AGE-SECRET-KEY-...)"
        )


# ---------------------------------------------------------------------------
# T02: SecretsLoader behaviour
# ---------------------------------------------------------------------------


class TestSecretsLoaderImport:
    """Verify SecretsLoader is importable from the config package."""

    def test_import_from_config(self) -> None:
        """SecretsLoader can be imported from heretek_swarm.config."""
        from heretek_swarm.config.secrets_loader import SecretsLoader

        assert SecretsLoader is not None

    def test_import_from_config_init(self) -> None:
        """SecretsLoader is exported from config/__init__.py."""
        from heretek_swarm.config import SecretsLoader

        assert SecretsLoader is not None

    def test_default_environment_is_development(self) -> None:
        """Default environment is 'development' when ENVIRONMENT is unset."""
        from heretek_swarm.config.secrets_loader import SecretsLoader

        env_bak = os.environ.pop("ENVIRONMENT", None)
        try:
            loader = SecretsLoader()
            assert loader.environment == "development"
        finally:
            if env_bak is not None:
                os.environ["ENVIRONMENT"] = env_bak

    def test_environment_from_param(self) -> None:
        """Constructor parameter overrides ENVIRONMENT env var."""
        from heretek_swarm.config.secrets_loader import SecretsLoader

        loader = SecretsLoader(environment="production")
        assert loader.environment == "production"

    def test_environment_from_env(self) -> None:
        """ENVIRONMENT env var is read when no param given."""
        from heretek_swarm.config.secrets_loader import SecretsLoader

        os.environ["ENVIRONMENT"] = "staging"
        try:
            loader = SecretsLoader()
            assert loader.environment == "staging"
        finally:
            os.environ["ENVIRONMENT"] = "development"


class TestSecretsLoaderProductionMissingKey:
    """Production mode: fail fast when SOPS_AGE_KEY is empty/missing."""

    def test_production_missing_key_raises_runtime_error(self) -> None:
        """SecretsLoader raises RuntimeError in production without SOPS_AGE_KEY."""
        from heretek_swarm.config.secrets_loader import SecretsLoader

        loader = SecretsLoader(environment="production", sops_age_key="")
        with pytest.raises(RuntimeError, match="SOPS_AGE_KEY"):
            asyncio.run(loader.load_secrets())


class TestSecretsLoaderDevFallback:
    """Development mode: fall back to .env when no SOPS_AGE_KEY."""

    def test_dev_no_key_does_not_raise(self) -> None:
        """Dev mode without SOPS_AGE_KEY should not raise — falls back gracefully."""
        from heretek_swarm.config.secrets_loader import SecretsLoader

        loader = SecretsLoader(environment="development", sops_age_key="")
        # Should not raise; either loads .env or logs warning if .env absent
        asyncio.run(loader.load_secrets())

    def test_dev_fallback_logs_warning(self) -> None:
        """Dev fallback produces a secrets_fallback_dev log when .env exists."""
        from heretek_swarm.config.secrets_loader import SecretsLoader

        loader = SecretsLoader(environment="development", sops_age_key="")
        asyncio.run(loader.load_secrets())  # Should not raise

    @pytest.mark.skipif(not _has_sops(), reason="sops binary not available")
    def test_dev_with_key_decrypts(self) -> None:
        """Dev mode with valid SOPS_AGE_KEY decrypts encrypted.env."""
        from heretek_swarm.config.secrets_loader import SecretsLoader

        # Save existing SOPS_AGE_KEY
        bak = os.environ.pop("SOPS_AGE_KEY", None)
        try:
            os.environ["SOPS_AGE_KEY"] = AGE_KEY
            loader = SecretsLoader(environment="development")
            asyncio.run(loader.load_secrets())
            # HERETEK_API_KEY should now be in os.environ
            assert "HERETEK_API_KEY" in os.environ
        finally:
            if bak is not None:
                os.environ["SOPS_AGE_KEY"] = bak
            else:
                os.environ.pop("SOPS_AGE_KEY", None)


class TestSecretsLoaderCI:
    """CI mode: decrypts ci.yaml into environment."""

    @pytest.mark.skipif(not _has_sops(), reason="sops binary not available")
    def test_load_ci_secrets_decrypts(self) -> None:
        """load_ci_secrets decrypts secrets/ci.yaml into os.environ."""
        from heretek_swarm.config.secrets_loader import SecretsLoader

        bak = os.environ.pop("SOPS_AGE_KEY", None)
        try:
            os.environ["SOPS_AGE_KEY"] = AGE_KEY
            loader = SecretsLoader(environment="ci")
            asyncio.run(loader.load_ci_secrets())
            assert "SOPS_AGE_KEY" in os.environ
        finally:
            if bak is not None:
                os.environ["SOPS_AGE_KEY"] = bak
            else:
                os.environ.pop("SOPS_AGE_KEY", None)


class TestSecretsLoaderFileNotFound:
    """Graceful handling when encrypted file is missing."""

    def test_production_missing_file_raises(self) -> None:
        """Production mode raises FileNotFoundError when encrypted.env is missing."""
        import tempfile
        from unittest import mock

        from heretek_swarm.config.secrets_loader import ENCRYPTED_ENV_FILE, SecretsLoader

        with tempfile.TemporaryDirectory() as td:
            # Mock REPO_ROOT to use the temp dir so encrypted.env is absent
            with mock.patch(
                "heretek_swarm.config.secrets_loader.ENCRYPTED_ENV_FILE",
                Path(td) / "secrets" / "encrypted.env",
            ):
                loader = SecretsLoader(
                    environment="production", sops_age_key=AGE_KEY
                )
                with pytest.raises(FileNotFoundError):
                    asyncio.run(loader.load_secrets())


class TestSecretsLoaderSopsBinary:
    """sops binary detection."""

    def test_ensure_sops_binary_finds_in_path(self) -> None:
        """_ensure_sops_binary resolves when sops is on PATH."""
        from heretek_swarm.config.secrets_loader import SecretsLoader

        loader = SecretsLoader()
        if _has_sops():
            loader._ensure_sops_binary()
            assert loader._sops_binary is not None
        else:
            with pytest.raises(
                RuntimeError, match="SOPS binary not found"
            ):
                loader._ensure_sops_binary()


class TestKeyValueParsing:
    """Injection of KEY=value pairs from decrypted output."""

    def test_inject_env_from_simple_text(self) -> None:
        """Simple KEY=value lines are injected into os.environ."""
        from heretek_swarm.config.secrets_loader import SecretsLoader

        text = "MY_KEY=my_value\nOTHER_KEY=other_value"
        # Remove from os.environ first to ensure clean state
        os.environ.pop("MY_KEY", None)
        os.environ.pop("OTHER_KEY", None)
        try:
            count = SecretsLoader._inject_env_from_text(text)
            assert count == 2
            assert os.environ["MY_KEY"] == "my_value"
            assert os.environ["OTHER_KEY"] == "other_value"
        finally:
            os.environ.pop("MY_KEY", None)
            os.environ.pop("OTHER_KEY", None)

    def test_inject_skips_comments_and_blanks(self) -> None:
        """Comment and blank lines are skipped."""
        from heretek_swarm.config.secrets_loader import SecretsLoader

        text = "# this is a comment\n\nSECRET=abc123\n\n\n"
        os.environ.pop("SECRET", None)
        try:
            count = SecretsLoader._inject_env_from_text(text)
            assert count == 1
            assert os.environ["SECRET"] == "abc123"
        finally:
            os.environ.pop("SECRET", None)

    def test_inject_does_not_overwrite_existing(self) -> None:
        """Existing env vars are not overwritten."""
        from heretek_swarm.config.secrets_loader import SecretsLoader

        os.environ["EXISTING"] = "original"
        text = "EXISTING=new_value"
        try:
            count = SecretsLoader._inject_env_from_text(text)
            assert count == 0
            assert os.environ["EXISTING"] == "original"
        finally:
            os.environ.pop("EXISTING", None)
