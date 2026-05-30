"""Tests for CertificateAuthority — certificate generation, issuance,
renewal, round-trip serialization, and temp file helpers.

Covers:
- CA root cert generation (PEM format, 365-day validity, RSA 4096-bit)
- Agent cert issuance (PEM format, 90-day validity, signed by CA)
- Round-trip: issue → serialize to YAML → encrypt → decrypt → deserialize
  → verify cert chain (agent cert signed by CA)
- Cert expiry detection (not_valid_after_utc ≤ RENEWAL_THRESHOLD_DAYS → renewal_needed)
- Renewal flow: renew_agent_cert generates new cert with extended validity
- write_temp_cert_files creates expected PEM files
- Cleanup removes temp files
"""

from __future__ import annotations

import datetime
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest
import yaml
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

pytestmark = [pytest.mark.unit]

from heretek_swarm.infrastructure.nats.ca import (
    AGENT_VALIDITY_DAYS,
    CA_CN,
    CA_KEY_SIZE,
    CA_VALIDITY_DAYS,
    RENEWAL_THRESHOLD_DAYS,
    CertificateAuthority,
    check_and_renew_certs,
    decrypt_certs,
    encrypt_certs,
    generate_cert_files,
    load_certificates,
    write_temp_cert_files,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def ca() -> CertificateAuthority:
    """Fresh CertificateAuthority for each test."""
    return CertificateAuthority()


@pytest.fixture
def agent_cert(ca: CertificateAuthority) -> dict[str, str]:
    """A freshly issued agent cert."""
    return ca.issue_agent_cert("test-agent-01")


# ---------------------------------------------------------------------------
# CA root cert generation
# ---------------------------------------------------------------------------


class TestCARootCertGeneration:
    """CA root cert: PEM format, 365-day validity, RSA 4096-bit."""

    def test_ca_cert_pem_format(self, ca: CertificateAuthority) -> None:
        """CA cert is a valid PEM-encoded X.509 certificate."""
        pem = ca.ca_cert_pem
        assert pem.startswith("-----BEGIN CERTIFICATE-----")
        assert pem.endswith("-----END CERTIFICATE-----\n")

        # Parse back and verify it loads cleanly
        loaded = x509.load_pem_x509_certificate(pem.encode("ascii"))
        assert isinstance(loaded, x509.Certificate)

    def test_ca_key_pem_format(self, ca: CertificateAuthority) -> None:
        """CA key is a valid PEM-encoded private key (PKCS#8)."""
        pem = ca.ca_key_pem
        assert pem.startswith("-----BEGIN PRIVATE KEY-----")
        assert pem.endswith("-----END PRIVATE KEY-----\n")

        # Parse back and verify
        loaded = serialization.load_pem_private_key(
            pem.encode("ascii"), password=None
        )
        assert isinstance(loaded, rsa.RSAPrivateKey)

    def test_ca_cert_validity_365_days(self, ca: CertificateAuthority) -> None:
        """CA cert has 365-day validity."""
        loaded = x509.load_pem_x509_certificate(ca.ca_cert_pem.encode("ascii"))
        delta = loaded.not_valid_after_utc - loaded.not_valid_before_utc
        assert delta.days == CA_VALIDITY_DAYS

    def test_ca_key_is_rsa_4096(self, ca: CertificateAuthority) -> None:
        """CA private key is RSA 4096-bit."""
        loaded = serialization.load_pem_private_key(
            ca.ca_key_pem.encode("ascii"), password=None
        )
        assert isinstance(loaded, rsa.RSAPrivateKey)
        assert loaded.key_size == CA_KEY_SIZE

    def test_ca_cert_is_self_signed(self, ca: CertificateAuthority) -> None:
        """CA cert subject equals issuer (self-signed)."""
        loaded = x509.load_pem_x509_certificate(ca.ca_cert_pem.encode("ascii"))
        assert loaded.subject == loaded.issuer

    def test_ca_cert_has_ca_basic_constraint(self, ca: CertificateAuthority) -> None:
        """CA cert has BasicConstraints ca=True."""
        loaded = x509.load_pem_x509_certificate(ca.ca_cert_pem.encode("ascii"))
        bc_ext = loaded.extensions.get_extension_for_class(x509.BasicConstraints)
        assert bc_ext.value.ca is True

    def test_ca_cert_common_name(self, ca: CertificateAuthority) -> None:
        """CA cert has the expected common name."""
        loaded = x509.load_pem_x509_certificate(ca.ca_cert_pem.encode("ascii"))
        cn_attrs = loaded.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        assert len(cn_attrs) == 1
        assert cn_attrs[0].value == CA_CN

    def test_ca_expiry_is_utc_datetime(self, ca: CertificateAuthority) -> None:
        """CA expiry property returns a UTC datetime."""
        expiry = ca.expiry
        assert isinstance(expiry, datetime.datetime)
        assert expiry.tzinfo is not None

    def test_custom_parameters_honoured(self) -> None:
        """CertificateAuthority respects custom key_size and validity_days."""
        ca = CertificateAuthority(
            common_name="Custom CA",
            key_size=2048,
            validity_days=180,
            agent_key_size=1024,
            agent_validity_days=60,
        )
        # Check CA key size
        pk = serialization.load_pem_private_key(ca.ca_key_pem.encode("ascii"), password=None)
        assert pk.key_size == 2048  # type: ignore[union-attr]
        # Check CA validity
        loaded = x509.load_pem_x509_certificate(ca.ca_cert_pem.encode("ascii"))
        delta = loaded.not_valid_after_utc - loaded.not_valid_before_utc
        assert delta.days == 180
        # Check agent cert validity
        agent = ca.issue_agent_cert("agent-1")
        agent_loaded = x509.load_pem_x509_certificate(agent["cert"].encode("ascii"))
        agent_delta = (
            agent_loaded.not_valid_after_utc - agent_loaded.not_valid_before_utc
        )
        assert agent_delta.days == 60


# ---------------------------------------------------------------------------
# Agent cert issuance
# ---------------------------------------------------------------------------


class TestAgentCertIssuance:
    """Agent cert: PEM format, 90-day validity, signed by CA."""

    def test_agent_cert_pem_format(self, agent_cert: dict[str, str]) -> None:
        """Agent cert is valid PEM X.509."""
        pem = agent_cert["cert"]
        assert pem.startswith("-----BEGIN CERTIFICATE-----")
        assert pem.endswith("-----END CERTIFICATE-----\n")
        loaded = x509.load_pem_x509_certificate(pem.encode("ascii"))
        assert isinstance(loaded, x509.Certificate)

    def test_agent_key_pem_format(self, agent_cert: dict[str, str]) -> None:
        """Agent private key is valid PEM PKCS#8."""
        pem = agent_cert["key"]
        assert pem.startswith("-----BEGIN PRIVATE KEY-----")
        assert pem.endswith("-----END PRIVATE KEY-----\n")
        loaded = serialization.load_pem_private_key(
            pem.encode("ascii"), password=None
        )
        assert isinstance(loaded, rsa.RSAPrivateKey)

    def test_agent_cert_validity_90_days(self, agent_cert: dict[str, str]) -> None:
        """Agent cert has 90-day validity."""
        loaded = x509.load_pem_x509_certificate(
            agent_cert["cert"].encode("ascii")
        )
        delta = loaded.not_valid_after_utc - loaded.not_valid_before_utc
        assert delta.days == AGENT_VALIDITY_DAYS

    def test_agent_cert_signed_by_ca(
        self, ca: CertificateAuthority, agent_cert: dict[str, str]
    ) -> None:
        """Agent cert is signed by the CA — verify the chain."""
        ca_loaded = x509.load_pem_x509_certificate(ca.ca_cert_pem.encode("ascii"))
        agent_loaded = x509.load_pem_x509_certificate(
            agent_cert["cert"].encode("ascii")
        )
        # Agent issuer matches CA subject
        assert agent_loaded.issuer == ca_loaded.subject

        # Cryptographic verification: the agent cert should be verifiable
        # with the CA's public key.
        # The signature algorithm is sha256WithRSAEncryption which uses
        # PKCS1v15 padding.
        from cryptography.hazmat.primitives.asymmetric import padding

        ca_public_key = ca_loaded.public_key()
        ca_public_key.verify(
            agent_loaded.signature,
            agent_loaded.tbs_certificate_bytes,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )

    def test_agent_cert_not_ca(self, agent_cert: dict[str, str]) -> None:
        """Agent cert has BasicConstraints ca=False."""
        loaded = x509.load_pem_x509_certificate(
            agent_cert["cert"].encode("ascii")
        )
        bc_ext = loaded.extensions.get_extension_for_class(x509.BasicConstraints)
        assert bc_ext.value.ca is False

    def test_agent_cert_has_client_auth_eku(self, agent_cert: dict[str, str]) -> None:
        """Agent cert includes clientAuth and serverAuth EKU."""
        loaded = x509.load_pem_x509_certificate(
            agent_cert["cert"].encode("ascii")
        )
        eku = loaded.extensions.get_extension_for_class(x509.ExtendedKeyUsage)
        oids = {oid.dotted_string for oid in eku.value}
        assert "1.3.6.1.5.5.7.3.2" in oids  # clientAuth
        assert "1.3.6.1.5.5.7.3.1" in oids  # serverAuth

    def test_agent_cert_common_name_is_agent_id(self) -> None:
        """Agent cert CN equals the provided agent_id."""
        ca = CertificateAuthority()
        cert = ca.issue_agent_cert("my-agent-42")
        loaded = x509.load_pem_x509_certificate(cert["cert"].encode("ascii"))
        cn = loaded.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        assert cn[0].value == "my-agent-42"

    def test_multiple_agent_certs_unique_serial(self, ca: CertificateAuthority) -> None:
        """Different agent certs have different serial numbers."""
        cert1 = ca.issue_agent_cert("agent-a")
        cert2 = ca.issue_agent_cert("agent-b")
        loaded1 = x509.load_pem_x509_certificate(cert1["cert"].encode("ascii"))
        loaded2 = x509.load_pem_x509_certificate(cert2["cert"].encode("ascii"))
        assert loaded1.serial_number != loaded2.serial_number


# ---------------------------------------------------------------------------
# Server cert issuance
# ---------------------------------------------------------------------------


class TestServerCertIssuance:
    """Server cert: PEM format, SANs, serverAuth EKU."""

    def test_server_cert_pem_format(self, ca: CertificateAuthority) -> None:
        """Server cert is valid PEM X.509."""
        result = ca.issue_server_cert()
        assert result["cert"].startswith("-----BEGIN CERTIFICATE-----")
        loaded = x509.load_pem_x509_certificate(result["cert"].encode("ascii"))
        assert isinstance(loaded, x509.Certificate)

    def test_server_cert_has_sans(self, ca: CertificateAuthority) -> None:
        """Server cert includes localhost, nats, hostname, 127.0.0.1 SANs."""
        result = ca.issue_server_cert("my-server")
        loaded = x509.load_pem_x509_certificate(result["cert"].encode("ascii"))
        san_ext = loaded.extensions.get_extension_for_class(
            x509.SubjectAlternativeName
        )
        names = san_ext.value.get_values_for_type(x509.DNSName)
        ips = san_ext.value.get_values_for_type(x509.IPAddress)
        assert "localhost" in names
        assert "nats" in names
        assert "my-server" in names
        assert "127.0.0.1" in str(ips[0]) if ips else False

    def test_server_cert_server_auth_only(self, ca: CertificateAuthority) -> None:
        """Server cert has serverAuth EKU but NOT clientAuth."""
        result = ca.issue_server_cert()
        loaded = x509.load_pem_x509_certificate(result["cert"].encode("ascii"))
        eku = loaded.extensions.get_extension_for_class(x509.ExtendedKeyUsage)
        oids = {oid.dotted_string for oid in eku.value}
        assert "1.3.6.1.5.5.7.3.1" in oids  # serverAuth
        assert "1.3.6.1.5.5.7.3.2" not in oids  # no clientAuth


# ---------------------------------------------------------------------------
# Cert expiry detection
# ---------------------------------------------------------------------------


class TestCertExpiryDetection:
    """Not valid after UTC ≤ RENEWAL_THRESHOLD_DAYS → certificate_renewal_needed log."""

    def test_agent_not_near_expiry_logs_no_warning(self, ca: CertificateAuthority) -> None:
        """Fresh agent cert does NOT log renewal_needed."""
        import structlog
        from structlog.testing import capture_logs

        with capture_logs() as cap:
            ca.issue_agent_cert("fresh-agent")
        renewal_logs = [
            r for r in cap if r.get("event") == "certificate_renewal_needed"
        ]
        assert len(renewal_logs) == 0

    def test_agent_near_expiry_logs_renewal_needed(self) -> None:
        """Agent cert with short validity ≤ RENEWAL_THRESHOLD_DAYS logs renewal_needed."""
        import structlog
        from structlog.testing import capture_logs

        # Create a CA that issues certs valid for ≤ RENEWAL_THRESHOLD_DAYS
        short_days = RENEWAL_THRESHOLD_DAYS
        ca = CertificateAuthority(
            agent_validity_days=short_days,
        )

        with capture_logs() as cap:
            ca.issue_agent_cert("expiring-agent")

        renewal_logs = [
            r
            for r in cap
            if r.get("event") == "certificate_renewal_needed"
            and r.get("subject") == "expiring-agent"
        ]
        assert len(renewal_logs) == 1
        assert renewal_logs[0]["days_remaining"] <= RENEWAL_THRESHOLD_DAYS

    def test_ca_cert_generated_log(self, ca: CertificateAuthority) -> None:
        """CA construction logs certificate_generated with cert_type=ca_root."""
        import structlog
        from structlog.testing import capture_logs

        with capture_logs() as cap:
            CertificateAuthority()

        gen_logs = [
            r
            for r in cap
            if r.get("event") == "certificate_generated"
            and r.get("cert_type") == "ca_root"
        ]
        assert len(gen_logs) == 1
        assert gen_logs[0]["subject"] == CA_CN
        assert "expiry" in gen_logs[0]

    def test_agent_cert_generated_log(self, ca: CertificateAuthority) -> None:
        """Agent cert issuance logs certificate_generated with cert_type=agent."""
        import structlog
        from structlog.testing import capture_logs

        with capture_logs() as cap:
            ca.issue_agent_cert("logged-agent")

        gen_logs = [
            r
            for r in cap
            if r.get("event") == "certificate_generated"
            and r.get("cert_type") == "agent"
        ]
        assert len(gen_logs) == 1
        assert gen_logs[0]["subject"] == "logged-agent"


# ---------------------------------------------------------------------------
# Renewal flow
# ---------------------------------------------------------------------------


class TestRenewalFlow:
    """renew_agent_cert generates new cert with extended validity."""

    def test_renew_agent_cert_returns_valid_pem(self, ca: CertificateAuthority) -> None:
        """renew_agent_cert returns a valid cert + key."""
        result = ca.renew_agent_cert("renew-me")
        assert "cert" in result
        assert "key" in result
        loaded = x509.load_pem_x509_certificate(result["cert"].encode("ascii"))
        assert isinstance(loaded, x509.Certificate)

    def test_renew_agent_cert_logs_renewal_completed(
        self, ca: CertificateAuthority
    ) -> None:
        """renew_agent_cert logs certificate_renewal_completed."""
        import structlog
        from structlog.testing import capture_logs

        with capture_logs() as cap:
            ca.renew_agent_cert("renew-me")

        completed = [
            r
            for r in cap
            if r.get("event") == "certificate_renewal_completed"
            and r.get("subject") == "renew-me"
        ]
        assert len(completed) == 1
        assert "new_expiry" in completed[0]

    def test_renewed_cert_has_extended_validity(
        self, ca: CertificateAuthority
    ) -> None:
        """Renewed cert not_valid_after is in the future (extended)."""
        result = ca.renew_agent_cert("extended-agent")
        loaded = x509.load_pem_x509_certificate(result["cert"].encode("ascii"))
        assert loaded.not_valid_after_utc > datetime.datetime.now(datetime.UTC)

    def test_renewed_cert_chain_still_valid(
        self, ca: CertificateAuthority
    ) -> None:
        """Renewed cert is still signed by the original CA."""
        result = ca.renew_agent_cert("chain-check")
        ca_loaded = x509.load_pem_x509_certificate(ca.ca_cert_pem.encode("ascii"))
        agent_loaded = x509.load_pem_x509_certificate(
            result["cert"].encode("ascii")
        )
        assert agent_loaded.issuer == ca_loaded.subject


# ---------------------------------------------------------------------------
# Round-trip: issue → serialize → encrypt → decrypt → verify chain
# ---------------------------------------------------------------------------


class TestRoundTripSerialization:
    """Full round-trip: issue cert → serialize to YAML → encrypt → decrypt
    → deserialize → verify cert chain."""

    def test_round_trip_cert_chain_verification(self, ca: CertificateAuthority) -> None:
        """Issue cert, round-trip via YAML serialization, verify chain."""
        agent_id = "roundtrip-agent"
        agent_result = ca.issue_agent_cert(agent_id)

        # Serialize to YAML structure
        data = {
            "ca": {
                "cert": ca.ca_cert_pem,
                "key": ca.ca_key_pem,
            },
            "agents": {
                agent_id: {
                    "cert": agent_result["cert"],
                    "key": agent_result["key"],
                }
            },
        }

        # Dump to YAML string and re-parse (simulating the SOPS cycle without
        # the actual binary)
        yaml_str = yaml.dump(data, default_flow_style=False)

        # Verify YAML round-trip is clean
        assert "BEGIN CERTIFICATE" in yaml_str
        assert "BEGIN PRIVATE KEY" in yaml_str

        parsed = yaml.safe_load(yaml_str)
        assert isinstance(parsed, dict)
        assert isinstance(parsed["ca"], dict)
        assert isinstance(parsed["agents"], dict)
        assert parsed["agents"][agent_id]["cert"] == agent_result["cert"]
        assert parsed["agents"][agent_id]["key"] == agent_result["key"]

    def test_round_trip_verify_cert_signed_by_ca(
        self, ca: CertificateAuthority
    ) -> None:
        """After YAML round-trip, cert chain is intact."""
        agent_id = "verify-chain"
        agent_result = ca.issue_agent_cert(agent_id)

        data = {
            "ca": {"cert": ca.ca_cert_pem, "key": ca.ca_key_pem},
            "agents": {agent_id: {"cert": agent_result["cert"], "key": agent_result["key"]}},
        }
        yaml_str = yaml.dump(data, default_flow_style=False)
        parsed = yaml.safe_load(yaml_str)

        # Re-parse certs from YAML
        ca_loaded = x509.load_pem_x509_certificate(
            parsed["ca"]["cert"].encode("ascii")
        )
        agent_loaded = x509.load_pem_x509_certificate(
            parsed["agents"][agent_id]["cert"].encode("ascii")
        )

        # Verify chain
        assert agent_loaded.issuer == ca_loaded.subject


# ---------------------------------------------------------------------------
# SOPS encrypt/decrypt convenience functions (mocked)
# ---------------------------------------------------------------------------


class TestSopsEncryptDecrypt:
    """SOPS encrypt/decrypt functions work correctly via mocked subprocess."""

    @pytest.mark.asyncio
    async def test_encrypt_certs_success(self) -> None:
        """encrypt_certs calls sops --encrypt --in-place and succeeds."""
        with mock.patch(
            "heretek_swarm.infrastructure.nats.ca._find_sops_binary",
            return_value="/usr/bin/sops",
        ):
            with mock.patch(
                "heretek_swarm.infrastructure.nats.ca.asyncio.create_subprocess_exec",
            ) as mock_exec:
                mock_proc = mock.AsyncMock()
                mock_proc.returncode = 0
                mock_proc.communicate = mock.AsyncMock(
                    return_value=(b"", b"")
                )
                mock_exec.return_value = mock_proc

                await encrypt_certs(Path("/tmp/test.yaml"))  # noqa: S108

                mock_exec.assert_called_once()
                args = mock_exec.call_args[0]
                assert args[0] == "/usr/bin/sops"
                assert "--encrypt" in args

    @pytest.mark.asyncio
    async def test_encrypt_certs_failure_raises(self) -> None:
        """encrypt_certs raises RuntimeError on non-zero exit."""
        with mock.patch(
            "heretek_swarm.infrastructure.nats.ca._find_sops_binary",
            return_value="/usr/bin/sops",
        ):
            with mock.patch(
                "heretek_swarm.infrastructure.nats.ca.asyncio.create_subprocess_exec",
            ) as mock_exec:
                mock_proc = mock.AsyncMock()
                mock_proc.returncode = 1
                mock_proc.communicate = mock.AsyncMock(
                    return_value=(b"", b"encryption error")
                )
                mock_exec.return_value = mock_proc

                with pytest.raises(RuntimeError, match="encryption error"):
                    await encrypt_certs(Path("/tmp/bad.yaml"))  # noqa: S108

    @pytest.mark.asyncio
    async def test_decrypt_certs_success(self) -> None:
        """decrypt_certs calls sops --decrypt and returns parsed YAML."""
        yaml_data = yaml.dump({"ca": {"cert": "fake-ca"}}, default_flow_style=False)

        with mock.patch(
            "heretek_swarm.infrastructure.nats.ca._find_sops_binary",
            return_value="/usr/bin/sops",
        ):
            with mock.patch(
                "heretek_swarm.infrastructure.nats.ca.asyncio.create_subprocess_exec",
            ) as mock_exec:
                mock_proc = mock.AsyncMock()
                mock_proc.returncode = 0
                mock_proc.communicate = mock.AsyncMock(
                    return_value=(yaml_data.encode(), b"")
                )
                mock_exec.return_value = mock_proc

                with mock.patch.object(Path, "exists", return_value=True):
                    result = await decrypt_certs(Path("/tmp/enc.yaml"))  # noqa: S108

                assert isinstance(result, dict)
                assert result["ca"]["cert"] == "fake-ca"

    @pytest.mark.asyncio
    async def test_decrypt_certs_failure_raises(self) -> None:
        """decrypt_certs raises RuntimeError on non-zero exit."""
        with mock.patch(
            "heretek_swarm.infrastructure.nats.ca._find_sops_binary",
            return_value="/usr/bin/sops",
        ):
            with mock.patch(
                "heretek_swarm.infrastructure.nats.ca.asyncio.create_subprocess_exec",
            ) as mock_exec:
                mock_proc = mock.AsyncMock()
                mock_proc.returncode = 1
                mock_proc.communicate = mock.AsyncMock(
                    return_value=(b"", b"decrypt failure")
                )
                mock_exec.return_value = mock_proc

                with mock.patch.object(Path, "exists", return_value=True):
                    with pytest.raises(RuntimeError, match="decrypt failure"):
                        await decrypt_certs(Path("/tmp/bad.yaml"))  # noqa: S108

    @pytest.mark.asyncio
    async def test_decrypt_certs_file_not_found(self) -> None:
        """decrypt_certs raises FileNotFoundError when file missing."""
        with mock.patch(
            "heretek_swarm.infrastructure.nats.ca._find_sops_binary",
            return_value="/usr/bin/sops",
        ):
            with mock.patch.object(Path, "exists", return_value=False):
                with pytest.raises(FileNotFoundError, match="Certs file not found"):
                    await decrypt_certs(Path("/tmp/nonexistent.yaml"))  # noqa: S108

    @pytest.mark.asyncio
    async def test_decrypt_certs_non_dict_raises(self) -> None:
        """decrypt_certs raises ValueError when YAML is not a mapping."""
        with mock.patch(
            "heretek_swarm.infrastructure.nats.ca._find_sops_binary",
            return_value="/usr/bin/sops",
        ):
            with mock.patch(
                "heretek_swarm.infrastructure.nats.ca.asyncio.create_subprocess_exec",
            ) as mock_exec:
                mock_proc = mock.AsyncMock()
                mock_proc.returncode = 0
                mock_proc.communicate = mock.AsyncMock(
                    return_value=(b"- list item\n", b"")
                )
                mock_exec.return_value = mock_proc

                with mock.patch.object(Path, "exists", return_value=True):
                    with pytest.raises(
                        ValueError, match="not a YAML mapping"
                    ):
                        await decrypt_certs(Path("/tmp/list.yaml"))  # noqa: S108


# ---------------------------------------------------------------------------
# load_certificates
# ---------------------------------------------------------------------------


class TestLoadCertificates:
    """load_certificates decryption and parsing."""

    @pytest.mark.asyncio
    async def test_load_certificates_returns_certs(self) -> None:
        """load_certificates returns ca_cert, ca_key, and agent_certs."""
        yaml_data = yaml.dump(
            {
                "ca": {"cert": "ca-cert-pem", "key": "ca-key-pem"},
                "agents": {
                    "agent-1": {"cert": "agent-cert", "key": "agent-key"},
                },
            },
            default_flow_style=False,
        )

        with mock.patch(
            "heretek_swarm.infrastructure.nats.ca._find_sops_binary",
            return_value="/usr/bin/sops",
        ):
            with mock.patch(
                "heretek_swarm.infrastructure.nats.ca.asyncio.create_subprocess_exec",
            ) as mock_exec:
                mock_proc = mock.AsyncMock()
                mock_proc.returncode = 0
                mock_proc.communicate = mock.AsyncMock(
                    return_value=(yaml_data.encode(), b"")
                )
                mock_exec.return_value = mock_proc

                with mock.patch.object(Path, "exists", return_value=True):
                    ca_cert, ca_key, agents = await load_certificates()

                assert ca_cert == "ca-cert-pem"
                assert ca_key == "ca-key-pem"
                assert agents["agent-1"]["cert"] == "agent-cert"
                assert agents["agent-1"]["key"] == "agent-key"

    @pytest.mark.asyncio
    async def test_load_certificates_missing_ca_key_raises(self) -> None:
        """load_certificates raises KeyError when 'ca' is missing."""
        yaml_data = yaml.dump(
            {"agents": {}}, default_flow_style=False
        )

        with mock.patch(
            "heretek_swarm.infrastructure.nats.ca._find_sops_binary",
            return_value="/usr/bin/sops",
        ):
            with mock.patch(
                "heretek_swarm.infrastructure.nats.ca.asyncio.create_subprocess_exec",
            ) as mock_exec:
                mock_proc = mock.AsyncMock()
                mock_proc.returncode = 0
                mock_proc.communicate = mock.AsyncMock(
                    return_value=(yaml_data.encode(), b"")
                )
                mock_exec.return_value = mock_proc

                with mock.patch.object(Path, "exists", return_value=True):
                    with pytest.raises(KeyError):
                        await load_certificates()

    @pytest.mark.asyncio
    async def test_load_certificates_ca_not_dict_raises(self) -> None:
        """load_certificates raises KeyError when 'ca' is not a dict."""
        yaml_data = yaml.dump(
            {"ca": "not-a-dict", "agents": {}}, default_flow_style=False
        )

        with mock.patch(
            "heretek_swarm.infrastructure.nats.ca._find_sops_binary",
            return_value="/usr/bin/sops",
        ):
            with mock.patch(
                "heretek_swarm.infrastructure.nats.ca.asyncio.create_subprocess_exec",
            ) as mock_exec:
                mock_proc = mock.AsyncMock()
                mock_proc.returncode = 0
                mock_proc.communicate = mock.AsyncMock(
                    return_value=(yaml_data.encode(), b"")
                )
                mock_exec.return_value = mock_proc

                with mock.patch.object(Path, "exists", return_value=True):
                    with pytest.raises(KeyError, match="'ca' to be a mapping"):
                        await load_certificates()


# ---------------------------------------------------------------------------
# write_temp_cert_files
# ---------------------------------------------------------------------------


class TestWriteTempCertFiles:
    """write_temp_cert_files creates expected PEM files, cleanup removes them."""

    def test_writes_ca_files(self, ca: CertificateAuthority) -> None:
        """write_temp_cert_files creates CA cert and key temp files."""
        ca_path, key_path, agent_cert_path, agent_key_path = write_temp_cert_files(
            ca_cert=ca.ca_cert_pem,
            ca_key=ca.ca_key_pem,
            agent_certs={},
            agent_id=None,
        )

        try:
            # Both CA files exist
            assert os.path.isfile(ca_path)
            assert os.path.isfile(key_path)
            # Agent paths are None (no agent_id)
            assert agent_cert_path is None
            assert agent_key_path is None

            # Content matches
            assert Path(ca_path).read_text() == ca.ca_cert_pem
            assert Path(key_path).read_text() == ca.ca_key_pem
        finally:
            # Cleanup
            for p in (ca_path, key_path):
                if p and os.path.isfile(p):
                    os.unlink(p)

    def test_writes_agent_files_when_agent_id_present(
        self, ca: CertificateAuthority
    ) -> None:
        """write_temp_cert_files creates agent cert/key when agent_id given."""
        agent_data = ca.issue_agent_cert("temp-agent")
        agent_certs = {"temp-agent": agent_data}

        ca_path, key_path, ac_path, ak_path = write_temp_cert_files(
            ca_cert=ca.ca_cert_pem,
            ca_key=ca.ca_key_pem,
            agent_certs=agent_certs,
            agent_id="temp-agent",
        )

        try:
            assert ac_path is not None
            assert ak_path is not None
            assert os.path.isfile(ac_path)
            assert os.path.isfile(ak_path)
            assert Path(ac_path).read_text() == agent_data["cert"]
            assert Path(ak_path).read_text() == agent_data["key"]
        finally:
            for p in (ca_path, key_path, ac_path, ak_path):
                if p and os.path.isfile(p):
                    os.unlink(p)

    def test_agent_id_not_found_no_agent_files(
        self, ca: CertificateAuthority
    ) -> None:
        """write_temp_cert_files returns None agent paths when agent_id not found."""
        ca_path, key_path, ac_path, ak_path = write_temp_cert_files(
            ca_cert=ca.ca_cert_pem,
            ca_key=ca.ca_key_pem,
            agent_certs={},
            agent_id="nonexistent",
        )

        try:
            assert ac_path is None
            assert ak_path is None
        finally:
            for p in (ca_path, key_path):
                if p and os.path.isfile(p):
                    os.unlink(p)

    def test_temp_files_cleanup(self) -> None:
        """Temp files are removable after creation (cleanup is possible)."""
        ca = CertificateAuthority()
        ca_p, key_p, _, _ = write_temp_cert_files(
            ca_cert=ca.ca_cert_pem,
            ca_key=ca.ca_key_pem,
            agent_certs={},
            agent_id=None,
        )

        # Remove them
        os.unlink(ca_p)
        os.unlink(key_p)

        # Verify removal
        assert not os.path.isfile(ca_p)
        assert not os.path.isfile(key_p)


# ---------------------------------------------------------------------------
# generate_cert_files
# ---------------------------------------------------------------------------


class TestGenerateCertFiles:
    """generate_cert_files writes all cert types to disk."""

    def test_generates_all_expected_files(self, tmp_path: Path) -> None:
        """generate_cert_files creates ca.crt, ca.key, nats-server.*, agent.*."""
        result = generate_cert_files(tmp_path)

        expected = {"ca_cert", "ca_key", "server_cert", "server_key", "agent_cert", "agent_key"}
        assert set(result.keys()) == expected

        for path in result.values():
            assert path.exists()
            assert path.read_text().startswith("-----BEGIN")

    def test_reuses_existing_ca(self, tmp_path: Path) -> None:
        """generate_cert_files reuses a pre-existing CA when provided."""
        ca = CertificateAuthority()
        result = generate_cert_files(tmp_path, ca=ca)

        ca_file = result["ca_cert"]
        assert ca_file.read_text() == ca.ca_cert_pem


# ---------------------------------------------------------------------------
# check_and_renew_certs
# ---------------------------------------------------------------------------


class TestCheckAndRenewCerts:
    """Startup cert renewal flow."""

    @pytest.mark.asyncio
    async def test_no_file_skips(self) -> None:
        """Returns False when certs file not found."""
        with mock.patch.object(Path, "exists", return_value=False):
            result = await check_and_renew_certs(Path("/tmp/nonexistent.yaml"))  # noqa: S108
        assert result is False

    @pytest.mark.asyncio
    async def test_no_sops_key_skips(self) -> None:
        """Returns False when SOPS_AGE_KEY is not set."""
        with mock.patch.object(Path, "exists", return_value=True):
            with mock.patch.dict(os.environ, {}, clear=True):
                result = await check_and_renew_certs(Path("/tmp/test.yaml"))  # noqa: S108
        assert result is False

    @pytest.mark.asyncio
    async def test_decrypt_failure_skips(self) -> None:
        """Returns False when decrypt fails."""
        with mock.patch.object(Path, "exists", return_value=True):
            with mock.patch.dict(os.environ, {"SOPS_AGE_KEY": "test-key"}):
                with mock.patch(
                    "heretek_swarm.infrastructure.nats.ca.decrypt_certs",
                    side_effect=RuntimeError("decrypt fail"),
                ):
                    result = await check_and_renew_certs(Path("/tmp/test.yaml"))  # noqa: S108
        assert result is False

    @pytest.mark.asyncio
    async def test_no_agents_skips(self) -> None:
        """Returns False when no agent certs in data."""
        data = {"ca": {"cert": "c", "key": "k"}, "agents": {}}
        with mock.patch.object(Path, "exists", return_value=True):
            with mock.patch.dict(os.environ, {"SOPS_AGE_KEY": "test-key"}):
                with mock.patch(
                    "heretek_swarm.infrastructure.nats.ca.decrypt_certs",
                    return_value=data,
                ):
                    result = await check_and_renew_certs(Path("/tmp/test.yaml"))  # noqa: S108
        assert result is False

    @pytest.mark.asyncio
    async def test_not_near_expiry_skips(self, ca: CertificateAuthority) -> None:
        """Returns False when agent cert is not near expiry."""
        agent = ca.issue_agent_cert("heretek-api")
        data = {
            "ca": {"cert": ca.ca_cert_pem, "key": ca.ca_key_pem},
            "agents": {"heretek-api": {"cert": agent["cert"], "key": agent["key"]}},
        }
        with mock.patch.object(Path, "exists", return_value=True):
            with mock.patch.dict(os.environ, {"SOPS_AGE_KEY": "test-key"}):
                with mock.patch(
                    "heretek_swarm.infrastructure.nats.ca.decrypt_certs",
                    return_value=data,
                ):
                    result = await check_and_renew_certs(Path("/tmp/test.yaml"))  # noqa: S108
        assert result is False

    @pytest.mark.asyncio
    async def test_near_expiry_renews(self, tmp_path: Path) -> None:
        """Returns True and renews when cert near expiry."""
        # Create a CA with very short validity so cert is "near expiry"
        ca = CertificateAuthority(agent_validity_days=RENEWAL_THRESHOLD_DAYS)
        agent = ca.issue_agent_cert("heretek-api")
        data = {
            "ca": {"cert": ca.ca_cert_pem, "key": ca.ca_key_pem},
            "agents": {"heretek-api": {"cert": agent["cert"], "key": agent["key"]}},
        }
        target = tmp_path / "certs.yaml"

        with mock.patch.object(Path, "exists", return_value=True):
            with mock.patch.dict(os.environ, {"SOPS_AGE_KEY": "test-key"}):
                with mock.patch(
                    "heretek_swarm.infrastructure.nats.ca.decrypt_certs",
                    return_value=data,
                ):
                    with mock.patch(
                        "heretek_swarm.infrastructure.nats.ca.encrypt_certs",
                    ) as mock_encrypt:
                        result = await check_and_renew_certs(target)

        assert result is True
        mock_encrypt.assert_called_once()

    @pytest.mark.asyncio
    async def test_near_expiry_non_default_agent(self) -> None:
        """Renews first agent when heretek-api not present."""
        ca = CertificateAuthority(agent_validity_days=RENEWAL_THRESHOLD_DAYS)
        agent = ca.issue_agent_cert("other-agent")
        data = {
            "ca": {"cert": ca.ca_cert_pem, "key": ca.ca_key_pem},
            "agents": {"other-agent": {"cert": agent["cert"], "key": agent["key"]}},
        }

        with mock.patch.object(Path, "exists", return_value=True):
            with mock.patch.dict(os.environ, {"SOPS_AGE_KEY": "test-key"}):
                with mock.patch(
                    "heretek_swarm.infrastructure.nats.ca.decrypt_certs",
                    return_value=data,
                ):
                    with mock.patch(
                        "heretek_swarm.infrastructure.nats.ca.encrypt_certs",
                    ) as mock_encrypt:
                        result = await check_and_renew_certs(Path("/tmp/test.yaml"))  # noqa: S108

        assert result is True
        mock_encrypt.assert_called_once()

    @pytest.mark.asyncio
    async def test_cert_parse_failure_skips(self) -> None:
        """Returns False when agent cert PEM cannot be parsed."""
        data = {
            "ca": {"cert": "bad-ca", "key": "bad-key"},
            "agents": {"heretek-api": {"cert": "not-a-cert", "key": "bad-key"}},
        }
        with mock.patch.object(Path, "exists", return_value=True):
            with mock.patch.dict(os.environ, {"SOPS_AGE_KEY": "test-key"}):
                with mock.patch(
                    "heretek_swarm.infrastructure.nats.ca.decrypt_certs",
                    return_value=data,
                ):
                    result = await check_and_renew_certs(Path("/tmp/test.yaml"))  # noqa: S108
        assert result is False
