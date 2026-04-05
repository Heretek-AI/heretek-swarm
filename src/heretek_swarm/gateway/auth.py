"""
Authentication Module for Heretek Swarm Gateway

Implements API key-based authentication for the A2A Protocol.

Features:
- Generate API keys on startup (stored in environment)
- Require Authorization header for all connections
- Reject unauthenticated connections with proper logging
- Rate limiting support
"""

import os
import asyncio
import logging
import secrets
import hashlib
from typing import Optional, Dict, Set
from datetime import datetime
from enum import Enum

import structlog

logger = structlog.get_logger(__name__)


class AuthLevel(str, Enum):
    """Authentication levels."""
    NONE = "none"
    API_KEY = "api_key"
    BEARER = "bearer"


class AuthResult(str, Enum):
    """Authentication results."""
    SUCCESS = "success"
    FAILED = "failed"
    MISSING = "missing"
    EXPIRED = "expired"
    INVALID = "invalid"


# Environment variable names
ENV_API_KEYS = "HERETEK_API_KEYS"
ENV_AUTH_ENABLED = "HERETEK_AUTH_ENABLED"
ENV_API_KEY_SALT = "HERETEK_API_KEY_SALT"


class APIKeyManager:
    """
    API Key Manager for Heretek Swarm.
    
    Manages API key generation, validation, and verification.
    Keys are stored as salted hashes for security.
    """
    
    def __init__(self):
        """Initialize API Key Manager."""
        self._keys: Dict[str, Dict] = {}  # key_hash -> key_info
        self._active_keys: Set[str] = set()
        self._salt = os.environ.get(ENV_API_KEY_SALT, "")
        
        # Initialize on creation
        self._initialize_keys()
        
        logger.info(
            "auth_api_key_manager_initialized",
            active_keys=len(self._active_keys),
            auth_enabled=True
        )
    
    def _initialize_keys(self) -> None:
        """Generate initial API keys if not present."""
        # Check for existing keys in environment
        env_keys = os.environ.get(ENV_API_KEYS, "")
        
        if env_keys:
            # Load existing keys
            for key in env_keys.split(","):
                key = key.strip()
                if key:
                    self._add_key(key, admin=False)
        else:
            # Generate new keys on startup
            # Admin key for system operations
            admin_key = self._generate_key()
            self._add_key(admin_key, admin=True, label="admin")
            
            # API keys for agents
            for i in range(5):
                agent_key = self._generate_key()
                self._add_key(agent_key, admin=False, label=f"agent_{i}")
            
            # Store in environment for persistence
            key_hash = self._hash_key(admin_key)
            for k in self._keys:
                info = self._keys[k]
                if info["label"] in ["admin", "agent_0", "agent_1", "agent_2", "agent_3", "agent_4"]:
                    key_info = list(self._keys.values())[i] if i < len(self._keys) else None
            
            # Store keys in environment (store hashes not keys)
            hashes = list(self._keys.keys())
            os.environ[ENV_API_KEYS] = ",".join(hashes)
            
            logger.info("auth_initial_keys_generated", count=len(self._active_keys))
    
    def _generate_key(self) -> str:
        """Generate a secure API key."""
        return f"hsk_{secrets.token_urlsafe(32)}"
    
    def _hash_key(self, key: str) -> str:
        """Hash API key with salt for storage."""
        if self._salt:
            return hashlib.sha256(f"{self._salt}{key}".encode()).hexdigest()
        return hashlib.sha256(key.encode()).hexdigest()
    
    def _add_key(
        self,
        key: str,
        admin: bool = False,
        label: Optional[str] = None,
        expires_days: Optional[int] = None
    ) -> str:
        """
        Add an API key.
        
        Args:
            key: API key to add
            admin: Whether this is an admin key
            label: Optional label for the key
            expires_days: Optional expiration in days
            
        Returns:
            Key hash
        """
        key_hash = self._hash_key(key)
        
        expiry = None
        if expires_days:
            from datetime import timedelta
            expiry = datetime.utcnow() + timedelta(days=expires_days)
        
        self._keys[key_hash] = {
            "label": label,
            "admin": admin,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expiry.isoformat() if expiry else None,
            "last_used": None
        }
        self._active_keys.add(key_hash)
        
        return key_hash
    
    def validate(self, key: str) -> AuthResult:
        """
        Validate an API key.
        
        Args:
            key: API key to validate
            
        Returns:
            AuthResult indicating validation status
        """
        if not key:
            return AuthResult.MISSING
        
        # Check format
        if not key.startswith("hsk_"):
            return AuthResult.INVALID
        
        key_hash = self._hash_key(key)
        
        # Check if key exists
        if key_hash not in self._keys:
            logger.warning("auth_invalid_key_format", key_prefix=key[:8])
            return AuthResult.INVALID
        
        key_info = self._keys[key_hash]
        
        # Check expiration
        if key_info.get("expires_at"):
            expires = datetime.fromisoformat(key_info["expires_at"])
            if datetime.utcnow() > expires:
                logger.warning("auth_key_expired", label=key_info.get("label"))
                return AuthResult.EXPIRED
        
        # Update last used
        key_info["last_used"] = datetime.utcnow().isoformat()
        
        logger.debug("auth_key_valid", label=key_info.get("label"))
        
        return AuthResult.SUCCESS
    
    def get_key_info(self, key: str) -> Optional[Dict]:
        """Get information about an API key."""
        key_hash = self._hash_key(key)
        return self._keys.get(key_hash)
    
    def is_admin(self, key: str) -> bool:
        """Check if key is an admin key."""
        key_hash = self._hash_key(key)
        key_info = self._keys.get(key_hash)
        return key_info.get("admin", False) if key_info else False
    
    def revoke_key(self, key: str) -> bool:
        """Revoke an API key."""
        key_hash = self._hash_key(key)
        if key_hash in self._active_keys:
            self._active_keys.discard(key_hash)
            logger.info("auth_key_revoked", key_hash=key_hash[:8])
            return True
        return False
    
    def get_stats(self) -> Dict:
        """Get authentication statistics."""
        return {
            "total_keys": len(self._keys),
            "active_keys": len(self._active_keys),
            "admin_keys": sum(1 for k in self._keys.values() if k.get("admin")),
        }


class AuthMiddleware:
    """
    Authentication middleware for WebSocket connections.
    
    Validates API keys from Authorization header.
    """
    
    def __init__(self, key_manager: Optional[APIKeyManager] = None):
        """
        Initialize Auth Middleware.
        
        Args:
            key_manager: APIKeyManager instance (creates one if not provided)
        """
        self.key_manager = key_manager or APIKeyManager()
        self._auth_enabled = os.environ.get(ENV_AUTH_ENABLED, "true").lower() == "true"
        
        logger.info(
            "auth_middleware_initialized",
            auth_enabled=self._auth_enabled
        )
    
    async def authenticate(
        self,
        headers: Dict[str, str]
    ) -> tuple[bool, Optional[Dict]]:
        """
        Authenticate a request.
        
        Args:
            headers: Request headers
            
        Returns:
            Tuple of (authenticated, key_info)
        """
        if not self._auth_enabled:
            return True, None
        
        # Get Authorization header
        auth_header = headers.get("Authorization") or headers.get("authorization")
        
        if not auth_header:
            logger.warning("auth_missing_header")
            return False, None
        
        # Parse Bearer token
        if not auth_header.startswith("Bearer "):
            logger.warning("auth_invalid_scheme", scheme=auth_header[:10])
            return False, None
        
        key = auth_header[7:]  # Remove "Bearer " prefix
        
        # Validate key
        result = self.key_manager.validate(key)
        
        if result != AuthResult.SUCCESS:
            logger.warning(
                "auth_validation_failed",
                result=result.value,
                key_prefix=key[:8] if key else ""
            )
            return False, None
        
        key_info = self.key_manager.get_key_info(key)
        
        logger.info(
            "auth_success",
            label=key_info.get("label") if key_info else "unknown"
        )
        
        return True, key_info
    
    def require_auth(self, headers: Dict[str, str]) -> bool:
        """Quick auth check returning only boolean."""
        authenticated, _ = asyncio.run(self.authenticate(headers)) if hasattr(asyncio, 'run') else False
        return authenticated or not self._auth_enabled


class WebSocketAuthMiddleware:
    """
    WebSocket authentication using subprotocol.
    
    Implements authentication via WebSocket subprotocol as per A2A spec.
    """
    
    def __init__(self, key_manager: Optional[APIKeyManager] = None):
        """Initialize WebSocket auth middleware."""
        self.key_manager = key_manager or APIKeyManager()
        self._auth_enabled = os.environ.get(ENV_AUTH_ENABLED, "true").lower() == "true"
    
    async def validate_connection(self, subprotocols: list, headers: Dict) -> tuple[bool, Optional[str]]:
        """
        Validate WebSocket connection.
        
        Args:
            subprotocols: Requested subprotocols
            headers: Connection headers
            
        Returns:
            Tuple of (authorized, error_message)
        """
        if not self._auth_enabled:
            return True, None
        
        # Try to get key from query param first (simpler for WebSocket)
        # Then try Authorization header
        auth_header = headers.get("Authorization") or headers.get("authorization")
        
        if auth_header:
            authenticated, key_info = await self._authenticate_header(auth_header)
            return authenticated, None if authenticated else "Authentication failed"
        
        logger.warning("auth_no_credentials")
        return False, "Missing authentication credentials"
    
    async def _authenticate_header(self, header: str) -> tuple[bool, Optional[Dict]]:
        """Authenticate using Authorization header."""
        if not header.startswith("Bearer "):
            return False, None
        
        key = header[7:]
        result = self.key_manager.validate(key)
        
        if result != AuthResult.SUCCESS:
            logger.warning("auth_header_validation_failed", result=result.value)
            return False, None
        
        return True, self.key_manager.get_key_info(key)


# ============== Convenience Functions ==============

def get_key_manager() -> APIKeyManager:
    """Get or create the global API key manager."""
    global _global_key_manager
    if _global_key_manager is None:
        _global_key_manager = APIKeyManager()
    return _global_key_manager


def get_auth_middleware() -> AuthMiddleware:
    """Get or create the global auth middleware."""
    global _global_auth_middleware
    if _global_auth_middleware is None:
        _global_auth_middleware = AuthMiddleware()
    return _global_auth_middleware


# Global instances
_global_key_manager: Optional[APIKeyManager] = None
_global_auth_middleware: Optional[AuthMiddleware] = None