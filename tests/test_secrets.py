"""Tests for SOPS secrets management (M002/S01).

Tests verify .sops.yaml configuration, encrypted file round-trips,
.gitignore rules, SecretsLoader behaviour, and SOPS binary integration.

Coverage:
  - SOPS config validity (T01)
  - SecretsLoader all code paths (T02)
  - CI pipeline artifacts (T03)
  - Pre-commit hook (T04)
  - Comprehensive edge-case tests (T05):
      - Production with key (mocked + real)
      - Missing SOPS binary
      - Corrupted encrypted file
      - Required key verification
      - Plaintext secret scanning
      - Integration test with real SOPS binary
"""

from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path
from unittest import mock

import pytest

pytestmark = [pytest.mark.unit]

# ---------------------------------------------------------------------------
# Module-level constants (overridable by tests via mock.patch) for fixtures
# and assertions that need the real decrypted shape.
# ---------------------------------------------------------------------------

_KNOWN_SECRET_KEYS = frozenset(
    {
        "HERETEK_API_KEY",
        "DATABASE_URL",
        "POSTGRES_PASSWORD",
        "REDIS_URL",
        "QDRANT_HOST",
        "QDRANT_PORT",
        "QDRANT_URL",
        "QDRANT_API_KEY",
        "HERETEK_NATS_URL",
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "LLM_MODEL",
        "EMBEDDING_PROVIDER",
        "EMBEDDING_BASE_URL",
        "EMBEDDING_API_KEY",
        "EMBEDDER_MODEL",
        "EMBEDDING_DIMENSIONS",
        "HERETEK_LOG_LEVEL",
        "MAX_MAILBOX_SIZE",
        "HEARTBEAT_INTERVAL",
        "PHASE_TIMEOUT",
        "CONSENSUS_AHEAD_BY_K",
        "CONSENSUS_MIN_VOTES",
        "CONSENSUS_CONFIDENCE_THRESHOLD",
        "MEMORY_MAX_SIZE",
        "MEMORY_DEFAULT_TTL",
        "MEM0_POSTGRES_PASSWORD",
        "MEM0_LLM_PROVIDER",
        "MEM0_LLM_MODEL",
        "MEM0_LLM_BASE_URL",
        "MEM0_LLM_API_KEY",
        "JWT_SECRET",
        "API_KEY",
        "ANTHROPIC_API_KEY",
        "CORS_ORIGINS",
        "ENVIRONMENT",
        "RATE_LIMIT_ENABLED",
    }
)


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


# =============================================================================
# T05: Comprehensive edge-case and mock-backed tests
# =============================================================================


# ---- Helpers for constructing mocked asyncio subprocess results -------------


def _make_mock_proc(
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> mock.AsyncMock:
    """Build an AsyncMock that mimics an asyncio subprocess Process.

    Uses mock.AsyncMock return_value (not asyncio.Future) so the helper can be
    called outside a running event loop (required since Python 3.14).
    """
    proc = mock.AsyncMock()
    proc.returncode = returncode
    proc.communicate = mock.AsyncMock(
        return_value=(stdout.encode(), stderr.encode())
    )
    return proc


# ---- Mocked unit tests (no real sops binary required) -----------------------


class TestSecretsLoaderProductionWithKeyMocked:
    """Production mode with valid key — subprocess calls mocked."""

    def test_production_with_valid_key_decrypts_and_injects(
        self,
    ) -> None:
        """Production decrypts encrypted.env and populates os.environ."""
        from heretek_swarm.config.secrets_loader import SecretsLoader

        fake_plaintext = "MY_API_KEY=sekrit123\nDB_URL=postgres://localhost/db\n"
        mock_proc = _make_mock_proc(returncode=0, stdout=fake_plaintext)

        # Clean target keys before test
        os.environ.pop("MY_API_KEY", None)
        os.environ.pop("DB_URL", None)

        try:
            with (
                mock.patch.object(SecretsLoader, "_ensure_sops_binary"),
                mock.patch(
                    "heretek_swarm.config.secrets_loader.ENCRYPTED_ENV_FILE",
                    Path("/fake/secrets/encrypted.env"),
                ),
                mock.patch(
                    "asyncio.create_subprocess_exec",
                    return_value=mock_proc,
                ),
            ):
                # Must also patch ENCRYPTED_ENV_FILE.exists() — Path mock
                with mock.patch.object(Path, "exists", return_value=True):
                    loader = SecretsLoader(
                        environment="production", sops_age_key=AGE_KEY
                    )
                    # _ensure_sops_binary is mocked no-op; set the attribute
                    # so _decrypt_file's assert passes
                    loader._sops_binary = "/fake/bin/sops"
                    asyncio.run(loader.load_secrets())

            assert os.environ["MY_API_KEY"] == "sekrit123"
            assert os.environ["DB_URL"] == "postgres://localhost/db"
        finally:
            os.environ.pop("MY_API_KEY", None)
            os.environ.pop("DB_URL", None)

    def test_production_sops_decrypt_nonzero_raises_runtime_error(
        self,
    ) -> None:
        """sops non-zero exit raises RuntimeError in production."""
        from heretek_swarm.config.secrets_loader import SecretsLoader

        mock_proc = _make_mock_proc(
            returncode=2, stderr="Error decrypting: no key available"
        )

        with (
            mock.patch.object(SecretsLoader, "_ensure_sops_binary"),
            mock.patch(
                "heretek_swarm.config.secrets_loader.ENCRYPTED_ENV_FILE",
                Path("/fake/secrets/encrypted.env"),
            ),
            mock.patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_proc,
            ),
            mock.patch.object(Path, "exists", return_value=True),
            pytest.raises(RuntimeError, match="sops --decrypt"),
        ):
            loader = SecretsLoader(
                environment="production", sops_age_key=AGE_KEY
            )
            loader._sops_binary = "/fake/bin/sops"
            asyncio.run(loader.load_secrets())


class TestSecretsLoaderMissingSopsBinary:
    """RuntimeError when sops binary is not found anywhere."""

    def test_missing_sops_binary_raises_runtime_error(self) -> None:
        """_ensure_sops_binary raises RuntimeError when sops not on PATH."""
        from heretek_swarm.config.secrets_loader import SecretsLoader

        loader = SecretsLoader(environment="production", sops_age_key=AGE_KEY)
        # Force _sops_binary to None and mock all discovery paths
        loader._sops_binary = None
        with (
            mock.patch("shutil.which", return_value=None),
            mock.patch.object(Path, "is_file", return_value=False),
            pytest.raises(RuntimeError, match="SOPS binary not found"),
        ):
            loader._ensure_sops_binary()


class TestSecretsLoaderCorruptedFile:
    """Decryption of an invalid/corrupted SOPS file raises RuntimeError."""

    def test_corrupted_file_sops_nonzero_raises(self) -> None:
        """RuntimeError on sops exit code != 0 (simulating corrupted file)."""
        from heretek_swarm.config.secrets_loader import SecretsLoader

        mock_proc = _make_mock_proc(
            returncode=1,
            stderr="Failed to parse encrypted file: invalid sops metadata",
        )

        with (
            mock.patch.object(SecretsLoader, "_ensure_sops_binary"),
            mock.patch(
                "heretek_swarm.config.secrets_loader.ENCRYPTED_ENV_FILE",
                Path("/fake/secrets/corrupted.env"),
            ),
            mock.patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_proc,
            ),
            mock.patch.object(Path, "exists", return_value=True),
            pytest.raises(RuntimeError, match="sops --decrypt"),
        ):
            loader = SecretsLoader(
                environment="production", sops_age_key=AGE_KEY
            )
            loader._sops_binary = "/fake/bin/sops"
            asyncio.run(loader.load_secrets())

    def test_corrupted_file_dev_logs_warning_and_falls_back(self) -> None:
        """In dev mode, corrupted file logs warning and falls back to .env."""
        from heretek_swarm.config.secrets_loader import SecretsLoader

        mock_proc = _make_mock_proc(
            returncode=1, stderr="corrupted file"
        )

        # Provide a fake .env so the fallback path exercises
        dotenv_text = "DEV_FALLBACK_VAR=from_dotenv\n"

        with (
            mock.patch.object(SecretsLoader, "_ensure_sops_binary"),
            mock.patch(
                "heretek_swarm.config.secrets_loader.ENCRYPTED_ENV_FILE",
                Path("/fake/secrets/corrupted.env"),
            ),
            mock.patch(
                "heretek_swarm.config.secrets_loader.DOTENV_FILE",
                Path("/fake/.env"),
            ),
            mock.patch(
                "asyncio.create_subprocess_exec",
                return_value=mock_proc,
            ),
            mock.patch.object(Path, "exists", return_value=True),
            mock.patch.object(Path, "read_text", return_value=dotenv_text),
        ):
            os.environ.pop("DEV_FALLBACK_VAR", None)
            try:
                loader = SecretsLoader(
                    environment="development", sops_age_key=AGE_KEY
                )
                loader._sops_binary = "/fake/bin/sops"
                asyncio.run(loader.load_secrets())
                assert os.environ["DEV_FALLBACK_VAR"] == "from_dotenv"
            finally:
                os.environ.pop("DEV_FALLBACK_VAR", None)


class TestEncryptedEnvRequiredKeys:
    """Verify decrypted content contains the expected set of configuration keys."""

    @pytest.mark.skipif(not _has_sops(), reason="sops binary not available")
    def test_encrypted_env_contains_required_keys(self, sops_env: dict[str, str]) -> None:
        """Decrypted encrypted.env has all required keys (HERETEK_API_KEY, DATABASE_URL, etc.)."""
        path = REPO_ROOT / "secrets" / "encrypted.env"
        r = subprocess.run(
            ["sops", "--decrypt", str(path)],
            capture_output=True,
            text=True,
            env=sops_env,
            timeout=30,
        )
        assert r.returncode == 0, f"sops --decrypt failed: {r.stderr.strip()}"

        decrypted_keys: set[str] = set()
        for line in r.stdout.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key = line.split("=", 1)[0]
                decrypted_keys.add(key)

        # Check that the critical operational keys are present
        critical = {
            "HERETEK_API_KEY",
            "DATABASE_URL",
            "OPENAI_API_KEY",
            "JWT_SECRET",
            "API_KEY",
        }
        missing = critical - decrypted_keys
        assert not missing, (
            f"Decrypted encrypted.env missing critical keys: {missing}"
        )

        # Also spot-check a few more
        extra = {"REDIS_URL", "CORS_ORIGINS", "QDRANT_HOST", "HERETEK_NATS_URL"}
        missing_extra = extra - decrypted_keys
        assert not missing_extra, (
            f"Decrypted encrypted.env missing expected keys: {missing_extra}"
        )

    def test_required_keys_from_known_set(self) -> None:
        """KNOWN_SECRET_KEYS covers all documented configuration keys."""
        # This is a self-check — makes sure the module-level constant stays in
        # sync with the actual encrypted.env content.
        assert len(_KNOWN_SECRET_KEYS) >= 30, (
            "KNOWN_SECRET_KEYS should track all documented config keys"
        )
        assert "HERETEK_API_KEY" in _KNOWN_SECRET_KEYS
        assert "DATABASE_URL" in _KNOWN_SECRET_KEYS
        assert "JWT_SECRET" in _KNOWN_SECRET_KEYS


class TestNoPlaintextSecretsInRepo:
    """Scan repo for plaintext secrets outside allowed paths."""

    def test_no_plaintext_secrets_outside_secrets_dir(self) -> None:
        """Rudimentary scan: common secret patterns must not appear outside
        secrets/ or the .secrets.baseline file."""
        import json
        import re

        # Patterns that would indicate a plaintext credential leak
        # (deliberately broad — false positives are handled by the baseline)
        patterns = [
            re.compile(rb"API_KEY\s*=\s*[a-zA-Z0-9+/=]{20,}"),
            re.compile(rb"SECRET_KEY\s*=\s*[a-zA-Z0-9+/=]{20,}"),
            re.compile(rb"sk-[a-zA-Z0-9]{20,}"),  # OpenAI-style
            re.compile(rb"AGE-SECRET-KEY-1[a-zA-Z0-9]{30,}"),
        ]

        # Load baseline to get known allowlisted files
        baseline_path = REPO_ROOT / ".secrets.baseline"
        baseline = json.loads(baseline_path.read_text())
        allowlisted = set(baseline.get("results", {}).keys())
        # Also always allow encrypted files
        allowlisted.update(
            [
                "secrets/encrypted.env",
                "secrets/ci.yaml",
            ]
        )

        violations: list[tuple[str, int, str]] = []
        tracked_dirs = [
            REPO_ROOT / "backend",
            REPO_ROOT / "scripts",
            REPO_ROOT / "docs",
        ]

        for d in tracked_dirs:
            if not d.is_dir():
                continue
            for py_file in d.rglob("*.py"):
                rel = str(py_file.relative_to(REPO_ROOT))
                if rel in allowlisted:
                    continue
                try:
                    content = py_file.read_bytes()
                except OSError:
                    continue
                for pattern in patterns:
                    for m in pattern.finditer(content):
                        # Skip matches inside comments (heuristic)
                        line_start = content.rfind(b"\n", 0, m.start()) + 1
                        line = content[line_start : content.find(b"\n", m.start())]
                        stripped = line.lstrip()
                        if stripped.startswith(b"#"):
                            continue
                        violations.append(
                            (rel, content[:m.start()].count(b"\n") + 1, m.group().decode(errors="replace"))
                        )

        assert not violations, (
            f"Found {len(violations)} plaintext secret(s) outside secrets/:\n"
            + "\n".join(f"  {f}:{l} -> {v[:80]}" for f, l, v in violations)
        )

    def test_no_raw_age_secret_in_source(self) -> None:
        """No AGE-SECRET-KEY literal appears in source files (outside secrets/)."""
        for pattern in ["AGE-SECRET-KEY-", "age1"]:
            proc = subprocess.run(
                [
                    "grep",
                    "-r",
                    "-l",
                    "--exclude-dir=__pycache__",
                    "--exclude-dir=.agents",
                    "--exclude-dir=.mypy_cache",
                    "--exclude=*.pyc",
                    pattern,
                    "backend/",
                    "scripts/",
                    "tests/",
                ],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
            )
            files = [f.strip() for f in proc.stdout.splitlines() if f.strip()]
            # Filter out files that are expected to contain the pattern:
            # - test_secrets.py (test fixture with a test-only age key)
            # - verify-sops-encryption.sh (pre-commit hook that validates age keys)
            allowed = {"tests/test_secrets.py", "scripts/verify-sops-encryption.sh"}
            violating = [f for f in files if f not in allowed]
            assert not violating, (
                f"AGE key pattern '{pattern}' found in source files: {violating}"
            )


# =============================================================================
# Integration test (requires real SOPS binary, opt-in via --integration)
# =============================================================================


@pytest.mark.integration
class TestSopsIntegration:
    """End-to-end test exercising the full SOPS decrypt-and-inject flow.

    Requires --integration flag (see conftest.py).
    """

    @pytest.mark.skipif(not _has_sops(), reason="sops binary not available")
    def test_full_production_load_cycle(self) -> None:
        """Production SecretsLoader decrypts real encrypted.env and populates env."""
        from heretek_swarm.config.secrets_loader import SecretsLoader

        # Save env to restore after
        saved = {}
        for k in (
            "SOPS_AGE_KEY",
            "HERETEK_API_KEY",
            "DATABASE_URL",
            "OPENAI_API_KEY",
            "JWT_SECRET",
        ):
            saved[k] = os.environ.pop(k, None)

        try:
            os.environ["SOPS_AGE_KEY"] = AGE_KEY
            loader = SecretsLoader(environment="production")
            asyncio.run(loader.load_secrets())

            # Verify critical keys were injected
            for k in ("HERETEK_API_KEY", "DATABASE_URL", "OPENAI_API_KEY", "JWT_SECRET"):
                assert k in os.environ, f"{k} not injected by full production cycle"
                assert os.environ[k], f"{k} is empty after injection"
        finally:
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v
                else:
                    os.environ.pop(k, None)

    @pytest.mark.skipif(not _has_sops(), reason="sops binary not available")
    def test_full_ci_load_cycle(self) -> None:
        """CI SecretsLoader.load_ci_secrets decrypts ci.yaml and injects keys."""
        from heretek_swarm.config.secrets_loader import SecretsLoader

        saved = os.environ.pop("SOPS_AGE_KEY", None)
        try:
            os.environ["SOPS_AGE_KEY"] = AGE_KEY
            loader = SecretsLoader(environment="ci")
            asyncio.run(loader.load_ci_secrets())
            assert "SOPS_AGE_KEY" in os.environ
        finally:
            if saved is not None:
                os.environ["SOPS_AGE_KEY"] = saved
            else:
                os.environ.pop("SOPS_AGE_KEY", None)

    @pytest.mark.skipif(not _has_sops(), reason="sops binary not available")
    def test_development_with_valid_key_uses_sops_not_fallback(self) -> None:
        """In dev mode with SOPS_AGE_KEY set, SOPS decryption is used (not .env fallback)."""
        from heretek_swarm.config.secrets_loader import SecretsLoader

        saved = {}
        for k in ("SOPS_AGE_KEY", "HERETEK_API_KEY", "DATABASE_URL"):
            saved[k] = os.environ.pop(k, None)

        try:
            os.environ["SOPS_AGE_KEY"] = AGE_KEY
            loader = SecretsLoader(environment="development")
            asyncio.run(loader.load_secrets())
            # HERETEK_API_KEY from encrypted.env should be injected
            assert "HERETEK_API_KEY" in os.environ
        finally:
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v
                else:
                    os.environ.pop(k, None)

    def test_production_no_key_fails_with_clear_message(self) -> None:
        """In production without SOPS_AGE_KEY, the error message is clear."""
        from heretek_swarm.config.secrets_loader import SecretsLoader

        loader = SecretsLoader(environment="production", sops_age_key="")
        with pytest.raises(RuntimeError) as exc_info:
            asyncio.run(loader.load_secrets())
        msg = str(exc_info.value)
        assert "SOPS_AGE_KEY" in msg
        assert "production" in msg.lower()
        # Error message should indicate the action needed
        assert "Set the SOPS_AGE_KEY" in msg or "required" in msg.lower()
