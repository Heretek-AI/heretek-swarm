"""
Authentication Layer for Heretek Swarm Gateway

Bearer token authentication for all gateway endpoints.
Security First: Auth enabled by default, no hardcoded credentials.

Reference: Prime Directive Security First principle
"""

import os
import secrets
from typing import Optional

import structlog
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_logger = structlog.get_logger(__name__)

# Security configuration
_security = HTTPBearer(auto_error=False)


def generate_api_key() -> str:
    """
    Generate secure API key.
    
    Returns:
        Secure random API key with heretek prefix
    """
    return f"htsk_{secrets.token_urlsafe(32)}"


def get_api_key_from_env() -> str:
    """
    Get API key from environment, generate if missing.
    
    Returns:
        API key string
        
    Raises:
        RuntimeError: If in production without API key
    """
    _key = os.getenv("HERETEK_API_KEY")

    if not key:
        # Check if production
        _environment = os.getenv("ENVIRONMENT", "development")

        if environment == "production":
            logger.error("api_key_missing_production")
            raise RuntimeError(
                "HERETEK_API_KEY required in production. "
                "Generate with: export HERETEK_API_KEY=$(openssl rand -hex 32)"
            )

        # Development: generate and warn
        _key = generate_api_key()
        logger.warning(
            "api_key_generated_development",
            _message = "Set HERETEK_API_KEY environment variable",
            _key_prefix = key[:10] + "..."
        )

    return key


async def verify_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> str:
    """
    Verify Bearer token authentication.
    
    Args:
        credentials: HTTP Authorization credentials
        
    Returns:
        "authenticated" if valid
        
    Raises:
        HTTPException: If auth fails
    """
    # Get expected key
    _expected_key = get_api_key_from_env()

    # Check credentials
    if credentials is None:
        logger.warning("auth_missing_credentials")
        raise HTTPException(
            _status_code = status.HTTP_401_UNAUTHORIZED,
            _detail = "Missing authentication credentials",
            _headers = {"WWW-Authenticate": "Bearer"},
        )

    # Validate token
    if credentials.credentials != expected_key:
        logger.warning(
            "auth_invalid_token",
            _provided_prefix = credentials.credentials[:10] + "..."
        )
        raise HTTPException(
            _status_code = status.HTTP_401_UNAUTHORIZED,
            _detail = "Invalid API key",
            _headers = {"WWW-Authenticate": "Bearer"},
        )

    logger.debug("auth_success")
    return "authenticated"


async def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[str]:
    """
    Optional authentication - returns None if no credentials.
    
    Use for endpoints that work with or without auth.
    
    Args:
        credentials: HTTP Authorization credentials
        
    Returns:
        "authenticated" if valid, None otherwise
    """
    if credentials is None:
        return None

    _expected_key = get_api_key_from_env()

    if credentials.credentials == expected_key:
        return "authenticated"

    return None


def get_api_key_header() -> dict:
    """Get API key for outbound requests."""
    _key = get_api_key_from_env()
    return {"Authorization": f"Bearer {key}"}
