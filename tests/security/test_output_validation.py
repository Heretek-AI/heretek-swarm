"""
Tests for Layer 3 Output Validation - PII Redaction

Tests the fix for the security output bypass bug where sanitized_output
was computed but not returned/passed through.
"""


import pytest

from src.heretek_swarm.security.zero_trust import (
    OutputValidationConfig,
    OutputValidator,
    ZeroTrustValidator,
)


class TestOutputValidatorSanitize:
    """Test the OutputValidator.sanitize() method."""

    def test_sanitize_email(self):
        """Test email redaction."""
        validator = OutputValidator()
        input_text = "Contact me at test@example.com for details"
        expected = "Contact me at [EMAIL_REDACTED] for details"

        result = validator.sanitize(input_text)
        assert result == expected

    def test_sanitize_phone(self):
        """Test phone number redaction."""
        validator = OutputValidator()
        input_text = "Call me at 555-123-4567 or 555.987.6543"
        result = validator.sanitize(input_text)

        assert "[PHONE_REDACTED]" in result
        assert "555-123-4567" not in result
        assert "555.987.6543" not in result

    def test_sanitize_ssn(self):
        """Test SSN redaction."""
        validator = OutputValidator()
        input_text = "SSN: 123-45-6789"
        expected = "SSN: [SSN_REDACTED]"

        result = validator.sanitize(input_text)
        assert result == expected

    def test_sanitize_credit_card(self):
        """Test credit card number redaction."""
        validator = OutputValidator()
        input_text = "Card: 1234-5678-9012-3456"
        expected = "Card: [CC_REDACTED]"

        result = validator.sanitize(input_text)
        assert result == expected

    def test_sanitize_ip_address(self):
        """Test IP address redaction."""
        validator = OutputValidator()
        input_text = "Server IP: 192.168.1.100"
        expected = "Server IP: [IP_REDACTED]"

        result = validator.sanitize(input_text)
        assert result == expected

    def test_sanitize_api_key(self):
        """Test API key redaction."""
        validator = OutputValidator()
        input_text = 'api_key = "sk-1234567890abcdefghij"'
        result = validator.sanitize(input_text)

        assert "[API_KEY_REDACTED]" in result
        assert "sk-1234567890abcdefghij" not in result

    def test_sanitize_private_key(self):
        """Test private key redaction."""
        validator = OutputValidator()
        input_text = "-----BEGIN RSA PRIVATE KEY-----\nMIIE..."
        result = validator.sanitize(input_text)

        assert "[PRIVATE_KEY_REDACTED]" in result

    def test_sanitize_aws_key(self):
        """Test AWS key redaction."""
        validator = OutputValidator()
        input_text = "AWS Key: AKIAIOSFODNN7EXAMPLE"
        expected = "AWS Key: [AWS_KEY_REDACTED]"

        result = validator.sanitize(input_text)
        assert result == expected

    def test_sanitize_jwt(self):
        """Test JWT token redaction."""
        validator = OutputValidator()
        # Valid JWT format: header.payload.signature
        input_text = "Token: eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.abc123"
        result = validator.sanitize(input_text)

        # JWT should be redacted (may be caught by API_KEY or JWT pattern)
        # The key test is that the original JWT is not in the output
        assert "eyJhbGciOiJIUzI1NiJ9" not in result
        # Should have some redaction marker
        assert "REDACTED" in result

    def test_sanitize_multiple_pii(self):
        """Test multiple PII types in same text."""
        validator = OutputValidator()
        input_text = "Email: test@example.com, Phone: 555-123-4567"
        result = validator.sanitize(input_text)

        assert "[EMAIL_REDACTED]" in result
        assert "[PHONE_REDACTED]" in result
        assert "test@example.com" not in result
        assert "555-123-4567" not in result

    def test_sanitize_no_pii(self):
        """Test text without PII passes through unchanged."""
        validator = OutputValidator()
        input_text = "Hello, this is a normal message without PII."
        result = validator.sanitize(input_text)

        assert result == input_text


class TestOutputValidatorValidate:
    """Test the OutputValidator.validate() method returns sanitized_output."""

    def test_validate_returns_sanitized_output(self):
        """Test that validate() includes sanitized_output in details."""
        config = OutputValidationConfig(redact_pii=True)
        validator = OutputValidator(config)

        input_text = "Contact: test@example.com, Phone: 555-123-4567"
        result = validator.validate(input_text)

        # Verify PII was detected
        assert result.details.get("pii_detected")
        assert len(result.details.get("pii_detected", [])) >= 2

        # Verify sanitized output is in details
        assert "sanitized_output" in result.details
        sanitized = result.details["sanitized_output"]

        # Verify sanitized output doesn't contain PII
        assert "test@example.com" not in sanitized
        assert "555-123-4567" not in sanitized
        assert "[EMAIL_REDACTED]" in sanitized
        assert "[PHONE_REDACTED]" in sanitized

    def test_validate_sanitized_flag(self):
        """Test that sanitized flag is set correctly."""
        config = OutputValidationConfig(redact_pii=True)
        validator = OutputValidator(config)

        # With PII
        result_with_pii = validator.validate("Email: test@example.com")
        assert result_with_pii.details.get("sanitized") is True

        # Without PII
        result_without_pii = validator.validate("Hello world")
        assert result_without_pii.details.get("sanitized") is False

    def test_validate_no_redaction_when_disabled(self):
        """Test that PII is not redacted when redact_pii=False."""
        config = OutputValidationConfig(redact_pii=False, enable_pii_detection=True)
        validator = OutputValidator(config)

        input_text = "Email: test@example.com"
        result = validator.validate(input_text)

        # Should detect PII but not redact
        assert result.passed is False  # Should fail because redact_pii=False
        assert result.details.get("pii_detected")

        # Sanitized output should be same as input (no redaction)
        sanitized = result.details.get("sanitized_output", input_text)
        assert "test@example.com" in sanitized


class TestZeroTrustValidatorValidateResponse:
    """Test ZeroTrustValidator.validate_response() exposes sanitized_output."""

    @pytest.mark.asyncio
    async def test_validate_response_exposes_sanitized_output(self):
        """Test that validate_response() exposes sanitized_output in result."""
        validator = ZeroTrustValidator()

        output_with_pii = "User email: test@example.com, phone: 555-123-4567"

        result = await validator.validate_response(
            output=output_with_pii,
            agent_id="test-agent",
            request_id="test-request-id",
        )

        # Verify the ZeroTrustResult has sanitized_output field
        assert hasattr(result, "sanitized_output")

        # Verify sanitized output is populated
        assert result.sanitized_output is not None
        sanitized = result.sanitized_output

        # Verify PII is redacted in sanitized output
        assert "test@example.com" not in sanitized
        assert "555-123-4567" not in sanitized
        assert "[EMAIL_REDACTED]" in sanitized
        assert "[PHONE_REDACTED]" in sanitized

    @pytest.mark.asyncio
    async def test_validate_response_no_pii(self):
        """Test validate_response() with no PII."""
        validator = ZeroTrustValidator()

        output_without_pii = "Hello, this is a normal response."

        result = await validator.validate_response(
            output=output_without_pii,
            agent_id="test-agent",
        )

        # Should pass validation
        assert result.passed is True

        # sanitized_output should be same as input when no PII
        assert result.sanitized_output == output_without_pii

    @pytest.mark.asyncio
    async def test_validate_response_with_sensitive_data(self):
        """Test validate_response() with sensitive data like API keys."""
        validator = ZeroTrustValidator()

        output_with_sensitive = 'The API key is: api_key = "sk-1234567890abcdefghij"'

        result = await validator.validate_response(
            output=output_with_sensitive,
            agent_id="test-agent",
        )

        # Verify sanitized output is populated
        assert result.sanitized_output is not None
        sanitized = result.sanitized_output

        # Verify sensitive data is redacted
        assert "sk-1234567890abcdefghij" not in sanitized
        assert "[API_KEY_REDACTED]" in sanitized


class TestPIIRegression:
    """Regression tests for the output bypass bug fix."""

    @pytest.mark.asyncio
    async def test_pii_redaction_end_to_end(self):
        """
        End-to-end test verifying PII redaction works correctly.
        
        This is a regression test for the bypass bug where sanitized_output
        was computed but the original data was passed through.
        """
        validator = ZeroTrustValidator()

        # Test case with multiple PII types
        test_cases = [
            ("Email only", "Contact: user@domain.com", "[EMAIL_REDACTED]"),
            ("Phone only", "Call 555-867-5309", "[PHONE_REDACTED]"),
            ("SSN only", "SSN 987-65-4321", "[SSN_REDACTED]"),
            ("IP only", "IP 10.0.0.1", "[IP_REDACTED]"),
            (
                "Multiple PII",
                "Email: a@b.com Phone: 111-222-3333",
                ["[EMAIL_REDACTED]", "[PHONE_REDACTED]"],
            ),
        ]

        for name, input_text, expected_marker in test_cases:
            result = await validator.validate_response(
                output=input_text,
                agent_id="test-agent",
            )

            # Verify sanitized_output is populated
            assert result.sanitized_output is not None, f"{name}: sanitized_output is None"

            # Verify expected redaction markers are present
            if isinstance(expected_marker, list):
                for marker in expected_marker:
                    assert marker in result.sanitized_output, f"{name}: missing {marker}"
            else:
                assert expected_marker in result.sanitized_output, f"{name}: missing {expected_marker}"

            # Verify original PII is NOT in sanitized output
            # (this is the key regression check for the bypass bug)
            if "@" in input_text and "." in input_text:
                # Likely an email, verify it's redacted
                parts = input_text.split()
                for part in parts:
                    if "@" in part and not part.startswith("["):
                        assert part not in result.sanitized_output, \
                            f"{name}: PII '{part}' not redacted - bypass bug!"
