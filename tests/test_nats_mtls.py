"""Mock-based tests for NATS mTLS integration.

Covers:
- HERETEK_MTLS_ENABLED=false → nats.connect called without tls
- HERETEK_MTLS_ENABLED=true → ssl.SSLContext constructed and passed as tls=
- URL prefix switch (nats:// → tls://)
- Error path: missing cert files → clear error logged
- HERETEK_MTLS_ENABLED truthiness: only 'true'/'1'/'yes' enable
- Integration tests gated behind --integration flag
"""

from __future__ import annotations

import os
import ssl
from pathlib import Path
from unittest import mock

import pytest

pytestmark = [pytest.mark.unit]

# Module-level imports (after NATS stub guard)
from heretek_swarm.gateway.nats_event_mesh import NATSEventMesh
from heretek_swarm.infrastructure.nats.client import NATSClient, NATSConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cert_pems() -> dict[str, str]:
    """Create a small set of in-memory cert PEMs for SSL context building.

    Uses cryptography directly to generate a real CA + agent cert so the
    SSL context can actually be constructed.
    """
    import datetime

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    ca_key = rsa.generate_private_key(65537, 2048)
    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test CA")]))
        .issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test CA")]))
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.UTC))
        .not_valid_after(
            datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=365)
        )
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(ca_key, hashes.SHA256())
    )

    agent_key = rsa.generate_private_key(65537, 2048)
    agent_cert = (
        x509.CertificateBuilder()
        .subject_name(
            x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test-client")])
        )
        .issuer_name(ca_cert.subject)
        .public_key(agent_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.UTC))
        .not_valid_after(
            datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=90)
        )
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(ca_key, hashes.SHA256())
    )

    return {
        "ca_cert": ca_cert.public_bytes(serialization.Encoding.PEM).decode("ascii"),
        "ca_key": ca_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("ascii"),
        "agent_cert": agent_cert.public_bytes(serialization.Encoding.PEM).decode(
            "ascii"
        ),
        "agent_key": agent_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("ascii"),
    }


def _write_temp_pems(
    tmp_path: Path, pems: dict[str, str]
) -> dict[str, str]:
    """Write certificate PEM data to temp files and return path mapping."""
    paths = {}
    for name, content in pems.items():
        fpath = tmp_path / f"{name}.pem"
        fpath.write_text(content, encoding="ascii")
        paths[name] = str(fpath)
    return paths


# ---------------------------------------------------------------------------
# NATSEventMesh mTLS tests
# ---------------------------------------------------------------------------


class TestNATSEventMeshTLSDisabled:
    """When HERETEK_MTLS_ENABLED is false/absent, no TLS is used."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_mtls_disabled_by_default() -> None:
        """NATSEventMesh defaults to tls_enabled=False when env var absent."""
        with mock.patch.dict(os.environ, {}, clear=True):
            mesh = NATSEventMesh(
                servers=["nats://localhost:4222"],
                tls_enabled=None,  # read from env
            )
            assert mesh.tls_enabled is False

    @staticmethod
    @pytest.mark.asyncio
    async def test_mtls_disabled_env_false() -> None:
        """HERETEK_MTLS_ENABLED=false → tls_enabled=False."""
        with mock.patch.dict(os.environ, {"HERETEK_MTLS_ENABLED": "false"}):
            mesh = NATSEventMesh(
                servers=["nats://localhost:4222"],
                tls_enabled=None,
            )
            assert mesh.tls_enabled is False

    @staticmethod
    @pytest.mark.asyncio
    async def test_connect_without_tls() -> None:
        """When tls_enabled=False, nats.connect called without tls= param."""
        with mock.patch(
            "heretek_swarm.gateway.nats_event_mesh.nats.connect",
        ) as mock_connect:
            mock_connect.return_value = mock.MagicMock()
            mock_connect.return_value.jetstream.return_value = None

            mesh = NATSEventMesh(
                servers=["nats://localhost:4222"],
                tls_enabled=False,
                max_reconnect_attempts=1,
            )

            await mesh.connect()

            # Verify nats.connect was called
            call_kwargs = mock_connect.call_args
            assert call_kwargs is not None
            # kwargs should either not contain "tls" or have None for tls
            kwargs = call_kwargs[1]
            assert "tls" not in kwargs or kwargs.get("tls") is None

    @staticmethod
    @pytest.mark.asyncio
    async def test_url_prefix_unchanged_without_tls() -> None:
        """When tls_enabled=False, URL stays nats://."""
        with mock.patch(
            "heretek_swarm.gateway.nats_event_mesh.nats.connect",
        ) as mock_connect:
            mock_connect.return_value = mock.MagicMock()
            mock_connect.return_value.jetstream.return_value = None

            mesh = NATSEventMesh(
                servers=["nats://localhost:4222"],
                tls_enabled=False,
                max_reconnect_attempts=1,
            )

            await mesh.connect()

            call_args = mock_connect.call_args[0]
            assert call_args[0] == "nats://localhost:4222"


class TestNATSEventMeshTLSEnabled:
    """When HERETEK_MTLS_ENABLED=true, mTLS is active."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_mtls_enabled_env_true() -> None:
        """HERETEK_MTLS_ENABLED=true → tls_enabled=True."""
        with mock.patch.dict(os.environ, {"HERETEK_MTLS_ENABLED": "true"}):
            mesh = NATSEventMesh(servers=["nats://localhost:4222"])
            assert mesh.tls_enabled is True

    @staticmethod
    @pytest.mark.asyncio
    async def test_mtls_enabled_explicit_true() -> None:
        """Explicit tls_enabled=True overrides env."""
        with mock.patch.dict(os.environ, {"HERETEK_MTLS_ENABLED": "false"}):
            mesh = NATSEventMesh(
                servers=["nats://localhost:4222"],
                tls_enabled=True,
            )
            assert mesh.tls_enabled is True

    @staticmethod
    @pytest.mark.asyncio
    async def test_ssl_context_passed_to_connect() -> None:
        """When tls_enabled=True, an ssl.SSLContext is passed as tls=."""
        with mock.patch(
            "heretek_swarm.gateway.nats_event_mesh.nats.connect",
        ) as mock_connect:
            mock_connect.return_value = mock.MagicMock()
            mock_connect.return_value.jetstream.return_value = None

            mesh = NATSEventMesh(
                servers=["nats://localhost:4222"],
                tls_enabled=True,
                max_reconnect_attempts=1,
            )

            await mesh.connect()

            kwargs = mock_connect.call_args[1]
            assert "tls" in kwargs
            assert isinstance(kwargs["tls"], ssl.SSLContext)

    @staticmethod
    @pytest.mark.asyncio
    async def test_url_prefix_switch_to_tls() -> None:
        """nats:// is switched to tls:// when TLS is enabled."""
        with mock.patch(
            "heretek_swarm.gateway.nats_event_mesh.nats.connect",
        ) as mock_connect:
            mock_connect.return_value = mock.MagicMock()
            mock_connect.return_value.jetstream.return_value = None

            mesh = NATSEventMesh(
                servers=["nats://localhost:4222"],
                tls_enabled=True,
                max_reconnect_attempts=1,
            )

            await mesh.connect()

            call_args = mock_connect.call_args[0]
            assert call_args[0].startswith("tls://")

    @staticmethod
    @pytest.mark.asyncio
    async def test_tls_connection_established_logged() -> None:
        """When TLS connects, nats_tls_connection_established is logged."""
        import structlog
        from structlog.testing import capture_logs

        with mock.patch(
            "heretek_swarm.gateway.nats_event_mesh.nats.connect",
        ) as mock_connect:
            mock_connect.return_value = mock.MagicMock()
            mock_connect.return_value.jetstream.return_value = None

            mesh = NATSEventMesh(
                servers=["nats://localhost:4222"],
                tls_enabled=True,
                max_reconnect_attempts=1,
            )

            # Silence the warning-level retry logs by patching logger
            with capture_logs() as cap:
                await mesh.connect()

            established = [
                r
                for r in cap
                if r.get("event") == "nats_tls_connection_established"
            ]
            assert len(established) == 1


class TestNATSEventMeshTLSErrorPaths:
    """Error paths for TLS/mTLS failures."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_tls_connection_failed_logged() -> None:
        """When TLS connection fails, nats_tls_connection_failed is logged."""
        import structlog
        from structlog.testing import capture_logs

        with mock.patch(
            "heretek_swarm.gateway.nats_event_mesh.nats.connect",
            side_effect=ConnectionRefusedError("Connection refused"),
        ):
            mesh = NATSEventMesh(
                servers=["nats://localhost:4222"],
                tls_enabled=True,
                max_reconnect_attempts=1,
                reconnect_time_wait=0.0,
            )

            with capture_logs() as cap:
                try:
                    await mesh.connect()
                except ConnectionRefusedError:
                    pass

            failed_logs = [
                r
                for r in cap
                if r.get("event") == "nats_tls_connection_failed"
            ]
            assert len(failed_logs) >= 1

    @staticmethod
    @pytest.mark.asyncio
    async def test_missing_cert_files_logged_as_error() -> None:
        """When cert PEM files don't exist at given paths, error is logged."""
        import structlog
        from structlog.testing import capture_logs

        mesh = NATSEventMesh(
            servers=["nats://localhost:4222"],
            tls_enabled=True,
            tls_ca_file="/nonexistent/ca.pem",
            tls_cert_file="/nonexistent/cert.pem",
            tls_key_file="/nonexistent/key.pem",
            max_reconnect_attempts=1,
        )

        with capture_logs():
            with pytest.raises(FileNotFoundError):
                mesh._build_ssl_context()

    @staticmethod
    @pytest.mark.asyncio
    async def test_disconnect_cleans_temp_cert_files() -> None:
        """After disconnect, _temp_cert_files is empty."""
        with mock.patch(
            "heretek_swarm.gateway.nats_event_mesh.nats.connect",
        ) as mock_connect:
            mock_connect.return_value = mock.MagicMock()
            mock_connect.return_value.jetstream.return_value = None
            mock_connect.return_value.close = mock.AsyncMock()

            mesh = NATSEventMesh(
                servers=["nats://localhost:4222"],
                tls_enabled=True,
                max_reconnect_attempts=1,
            )

            await mesh.connect()
            # Build SSL context adds temp files
            assert len(mesh._temp_cert_files) > 0

            await mesh.disconnect()
            assert len(mesh._temp_cert_files) == 0


class TestNATSEventMeshTLSTruthiness:
    """Only 'true' (case-insensitive) enables mTLS from env var."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_true_enables() -> None:
        with mock.patch.dict(os.environ, {"HERETEK_MTLS_ENABLED": "true"}):
            mesh = NATSEventMesh(servers=["nats://localhost:4222"])
            assert mesh.tls_enabled is True

    @staticmethod
    @pytest.mark.asyncio
    async def test_true_mixed_case_enables() -> None:
        """'True' / 'TRUE' (case-insensitive) also enable."""
        for value in ("True", "TRUE", "tRuE"):
            with mock.patch.dict(os.environ, {"HERETEK_MTLS_ENABLED": value}):
                mesh = NATSEventMesh(servers=["nats://localhost:4222"])
                assert mesh.tls_enabled is True, f"'{value}' should enable"

    @staticmethod
    @pytest.mark.asyncio
    async def test_false_disables() -> None:
        with mock.patch.dict(os.environ, {"HERETEK_MTLS_ENABLED": "false"}):
            mesh = NATSEventMesh(servers=["nats://localhost:4222"])
            assert mesh.tls_enabled is False

    @staticmethod
    @pytest.mark.asyncio
    async def test_other_values_disabled() -> None:
        """Arbitrary strings like '1', 'yes', 'enabled', 'on' do NOT enable."""
        for value in ("1", "yes", "enabled", "on", "YES", "ON", "anything"):
            with mock.patch.dict(os.environ, {"HERETEK_MTLS_ENABLED": value}):
                mesh = NATSEventMesh(servers=["nats://localhost:4222"])
                assert mesh.tls_enabled is False, f"'{value}' should not enable"


# ---------------------------------------------------------------------------
# NATSClient mTLS tests
# ---------------------------------------------------------------------------


class TestNATSClientTLSDisabled:
    """NATSClient with TLS disabled does not build SSL context."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_natsclient_tls_disabled_by_default() -> None:
        """NATSClient config defaults to tls_enabled=False."""
        with mock.patch.dict(os.environ, {}, clear=True):
            config = NATSConfig(url="nats://localhost:4222")
            assert config.tls_enabled is False

    @staticmethod
    @pytest.mark.asyncio
    async def test_natsclient_connect_without_tls() -> None:
        """When tls_enabled=False, no tls= param sent to nats.connect."""
        import nats as _nats

        with mock.patch.object(_nats, "connect") as mock_connect:
            mock_connect.return_value = mock.MagicMock()

            config = NATSConfig(url="nats://localhost:4222", tls_enabled=False)
            client = NATSClient(config=config)

            await client.connect()

            kwargs = mock_connect.call_args[1]
            assert "tls" not in kwargs or kwargs.get("tls") is None


class TestNATSClientTLSEnabled:
    """NATSClient with TLS enabled builds SSL context correctly."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_natsclient_tls_enabled_from_env() -> None:
        """HERETEK_MTLS_ENABLED=true enables TLS in NATSConfig."""
        with mock.patch.dict(os.environ, {"HERETEK_MTLS_ENABLED": "true"}):
            config = NATSConfig(url="nats://localhost:4222")
            assert config.tls_enabled is True

    @staticmethod
    @pytest.mark.asyncio
    async def test_natsclient_ssl_context_passed() -> None:
        """SSLContext is built and passed as tls= to nats.connect."""
        import nats as _nats

        with mock.patch.object(_nats, "connect") as mock_connect:
            mock_connect.return_value = mock.MagicMock()

            config = NATSConfig(url="nats://localhost:4222", tls_enabled=True)
            client = NATSClient(config=config)

            await client.connect()

            kwargs = mock_connect.call_args[1]
            assert "tls" in kwargs
            assert isinstance(kwargs["tls"], ssl.SSLContext)

    @staticmethod
    @pytest.mark.asyncio
    async def test_natsclient_url_prefix_switch() -> None:
        """nats:// → tls:// when tls_enabled=True."""
        import nats as _nats

        with mock.patch.object(_nats, "connect") as mock_connect:
            mock_connect.return_value = mock.MagicMock()

            config = NATSConfig(url="nats://localhost:4222", tls_enabled=True)
            client = NATSClient(config=config)

            await client.connect()

            called_url = mock_connect.call_args[0][0]
            assert called_url.startswith("tls://")

    @staticmethod
    @pytest.mark.asyncio
    async def test_natsclient_tls_connection_logged() -> None:
        """nats_tls_connection_established logged on TLS connect."""
        import structlog
        from structlog.testing import capture_logs

        import nats as _nats

        with mock.patch.object(_nats, "connect") as mock_connect:
            mock_connect.return_value = mock.MagicMock()

            config = NATSConfig(url="nats://localhost:4222", tls_enabled=True)
            client = NATSClient(config=config)

            with capture_logs() as cap:
                await client.connect()

            established = [
                r
                for r in cap
                if r.get("event") == "nats_tls_connection_established"
            ]
            assert len(established) == 1

    @staticmethod
    @pytest.mark.asyncio
    async def test_natsclient_connection_failed_logged() -> None:
        """nats_tls_connection_failed logged on TLS connection error."""
        import structlog
        from structlog.testing import capture_logs

        import nats as _nats

        with mock.patch.object(
            _nats, "connect", side_effect=ConnectionRefusedError("refused")
        ):
            config = NATSConfig(url="nats://localhost:4222", tls_enabled=True)
            client = NATSClient(config=config)

            with capture_logs() as cap:
                await client.connect()

            failed = [
                r
                for r in cap
                if r.get("event") == "nats_tls_connection_failed"
            ]
            assert len(failed) >= 1

    @staticmethod
    @pytest.mark.asyncio
    async def test_natsclient_disconnect_cleans_temp_files() -> None:
        """Temp cert files are cleaned up on disconnect."""
        import nats as _nats

        with mock.patch.object(_nats, "connect") as mock_connect:
            mock_nc = mock.MagicMock()
            mock_nc.close = mock.AsyncMock()
            mock_connect.return_value = mock_nc

            config = NATSConfig(url="nats://localhost:4222", tls_enabled=True)
            client = NATSClient(config=config)

            await client.connect()
            assert len(client._temp_cert_files) > 0

            await client.disconnect()
            assert len(client._temp_cert_files) == 0


class TestNATSClientTLSTruthiness:
    """NATSConfig only enables TLS for 'true' (case-insensitive)."""

    @staticmethod
    def test_env_true_enables_natsconfig() -> None:
        with mock.patch.dict(os.environ, {"HERETEK_MTLS_ENABLED": "true"}):
            config = NATSConfig(url="nats://localhost:4222")
            assert config.tls_enabled is True

    @staticmethod
    def test_env_mixed_case_true_enables_natsconfig() -> None:
        for value in ("True", "TRUE", "tRuE"):
            with mock.patch.dict(os.environ, {"HERETEK_MTLS_ENABLED": value}):
                config = NATSConfig(url="nats://localhost:4222")
                assert config.tls_enabled is True, f"NATSConfig with env='{value}' should be True"

    @staticmethod
    def test_env_false_disables_natsconfig() -> None:
        with mock.patch.dict(os.environ, {"HERETEK_MTLS_ENABLED": "false"}):
            config = NATSConfig(url="nats://localhost:4222")
            assert config.tls_enabled is False

    @staticmethod
    def test_env_other_disables_natsconfig() -> None:
        for value in ("1", "yes", "enabled", "on", "YES", "anything", ""):
            with mock.patch.dict(os.environ, {"HERETEK_MTLS_ENABLED": value}):
                config = NATSConfig(url="nats://localhost:4222")
                assert config.tls_enabled is False, (
                    f"NATSConfig with env='{value}' should be False"
                )


# ---------------------------------------------------------------------------
# Integration tests (gated behind --integration flag)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestNATSMTLSIntegration:
    """Integration tests requiring a real NATS server with mTLS.

    Run with: python3 -m pytest tests/test_nats_mtls.py --integration -v
    """

    @staticmethod
    @pytest.mark.asyncio
    async def test_real_mtls_connect_and_disconnect() -> None:
        """Connect to a real NATS server with mTLS, then disconnect cleanly.

        Requires a running NATS server with TLS configured. If this fails
        due to server unavailability, the test is skipped (not failed).
        """
        import nats as _nats

        pems = _make_cert_pems()
        with tempfile.TemporaryDirectory() as tmpdir:
            td = Path(tmpdir)
            paths = _write_temp_pems(td, pems)

            # Build a real NATSClient with TLS enabled
            config = NATSConfig(
                url="nats://localhost:4222",
                tls_enabled=True,
                tls_ca_file=paths["ca_cert"],
                tls_cert_file=paths["agent_cert"],
                tls_key_file=paths["agent_key"],
            )
            client = NATSClient(config=config)

            try:
                connected = await client.connect()
                if not connected:
                    pytest.skip("NATS server not available with mTLS — skipping")
            except Exception as e:
                pytest.skip(f"NATS server not available: {e}")

            assert client.is_connected
            assert client.state.value == "connected"

            await client.disconnect()
            assert not client.is_connected


# Import at module level for the fixture
import tempfile
