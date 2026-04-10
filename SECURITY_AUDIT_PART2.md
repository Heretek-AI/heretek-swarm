# SECURITY AUDIT - Part 2: Input Validation & Auth/Authz

**Heretek Swarm Codebase**  
**Audit Date:** 2026-04-10  
**Auditor:** Security Analysis Tool  
**Scope:** Input Validation, Authentication, Authorization, Environment Variable Handling

---

## Executive Summary

This security audit examines the Heretek Swarm codebase focusing on input validation mechanisms, authentication/authorization implementations, and environment variable handling. The codebase demonstrates a well-structured security architecture with multiple defensive layers, though several areas require attention to achieve production-ready security.

**Overall Security Posture:** MODERATE - Good foundational security with identified areas for improvement.

---

## 1. INPUT VALIDATION FINDINGS

### 1.1 🔴 CRITICAL: Missing Input Validation on Consensus Results Endpoint

**File:** `src/heretek_swarm/api/consensus.py`  
**Lines:** 444-461

**Code Snippet:**
```python
@router.get("/{consensus_id}/results")
async def get_consensus_results(consensus_id: str):
    """
    Get results of a completed consensus round.
    ...
    """
    if consensus_id not in _active_rounds:
        raise HTTPException(404, f"Consensus round {consensus_id} not found")
```

**Issue:** This endpoint has NO authentication dependency (`Depends(get_authenticated_agent)` is MISSING).

**Severity:** CRITICAL

**Existing Controls:** None - endpoint is publicly accessible.

**Recommended Fix:**
```python
@router.get("/{consensus_id}/results")
async def get_consensus_results(
    consensus_id: str,
    agent_id: str = Depends(get_authenticated_agent)
):
    # Validate consensus_id format
    if not consensus_id or len(consensus_id) > 100:
        raise HTTPException(400, "Invalid consensus_id format")
    
    # Add UUID format validation
    import re
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    if not uuid_pattern.match(consensus_id):
        raise HTTPException(400, "Invalid consensus_id format")
    
    if consensus_id not in _active_rounds:
        raise HTTPException(404, f"Consensus round {consensus_id} not found")
```

---

### 1.2 🔴 CRITICAL: Missing Input Validation on Token Generation Endpoint

**File:** `src/heretek_swarm/api/consensus.py`  
**Lines:** 537-555

**Code Snippet:**
```python
@router.post("/auth/token")
async def generate_auth_token(agent_id: str, permissions: Optional[List[str]] = None):
    """
    Generate an authentication token for an agent.
    """
    token = consensus_auth_manager.generate_token(agent_id, permissions)
    return {
        "token": token,
        "agent_id": agent_id,
        "permissions": permissions or ["vote", "create", "view"],
    }
```

**Issue:** 
- No authentication required to generate tokens
- No validation on `agent_id` length or format
- No rate limiting on token generation
- No CAPTCHA or proof-of-work to prevent automated attacks

**Severity:** CRITICAL

**Existing Controls:** None - endpoint is publicly accessible.

**Recommended Fix:**
```python
@router.post("/auth/token")
async def generate_auth_token(
    agent_id: str = Body(..., min_length=1, max_length=100),
    permissions: Optional[List[str]] = Body(None)
):
    # Validate agent_id format (alphanumeric, underscore, hyphen only)
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', agent_id):
        raise HTTPException(400, "Invalid agent_id format")
    
    # Validate permissions
    VALID_PERMISSIONS = {"vote", "create", "view"}
    if permissions and not all(p in VALID_PERMISSIONS for p in permissions):
        raise HTTPException(400, "Invalid permission values")
    
    # Add rate limiting check here
    # ...
    
    token = consensus_auth_manager.generate_token(agent_id, permissions)
    return {
        "token": token,
        "agent_id": agent_id,
        "permissions": permissions or ["vote", "create", "view"],
    }
```

---

### 1.3 🔴 HIGH: Missing Input Validation on Token Revocation Endpoint

**File:** `src/heretek_swarm/api/consensus.py`  
**Lines:** 558-572

**Code Snippet:**
```python
@router.post("/auth/revoke")
async def revoke_auth_token(token: str):
    """
    Revoke an authentication token.
    """
    success = consensus_auth_manager.revoke_token(token)
    return {
        "revoked": success,
    }
```

**Issue:**
- No authentication required
- Token passed as query parameter (visible in logs)
- No validation of token format before processing
- Information disclosure: reveals whether token exists (200 vs 200 response)

**Severity:** HIGH

**Existing Controls:** None

**Recommended Fix:**
```python
@router.post("/auth/revoke")
async def revoke_auth_token(
    token: str = Body(..., embed=True),
    authenticated: str = Depends(verify_auth)  # Require auth
):
    # Validate token format
    if len(token) < 32 or len(token) > 128:
        raise HTTPException(400, "Invalid token format")
    
    # Always return success to prevent enumeration
    success = consensus_auth_manager.revoke_token(token)
    return {"revoked": True}  # Always return True
```

---

### 1.4 🟡 MEDIUM: No Rate Limiting on Consensus Token Endpoints

**File:** `src/heretek_swarm/api/consensus.py`  
**Lines:** 537-572

**Issue:** The `/auth/token` and `/auth/revoke` endpoints have no rate limiting, making them vulnerable to:
- Token generation flooding
- Brute-force token guessing
- DoS attacks

**Severity:** MEDIUM

**Existing Controls:** General rate limiting may be configured at application level.

**Recommended Fix:** Add rate limiting middleware specifically for these endpoints:
```python
from heretek_swarm.api.rate_limiting import rate_limit_by_ip

@router.post("/auth/token")
@rate_limit_by_ip(max_requests=5, window_seconds=60)  # 5 tokens per minute
async def generate_auth_token(...):
    ...
```

---

### 1.5 🟡 MEDIUM: Insufficient Input Validation on Plugin Configuration

**File:** `src/heretek_swarm/api/plugins.py`  
**Lines:** 213-232

**Code Snippet:**
```python
@router.put("/{plugin_id}/config")
async def update_plugin_config(plugin_id: str, config: Dict[str, Any]):
    """
    Update plugin configuration.
    """
    if plugin_id not in _plugin_states:
        raise HTTPException(404, f"Plugin {plugin_id} not found")
    
    _plugin_states[plugin_id]["config"].update(config)
    ...
```

**Issue:**
- No authentication required
- No validation of config values against expected schema
- Allows arbitrary key-value pairs
- Configuration changes not persisted to database

**Severity:** MEDIUM

**Existing Controls:** None - publicly accessible

**Recommended Fix:**
```python
@router.put("/{plugin_id}/config", dependencies=[Depends(verify_auth)])
async def update_plugin_config(
    plugin_id: str,
    config: Dict[str, Any],
    authenticated: str = Depends(verify_auth)
):
    if plugin_id not in _plugin_states:
        raise HTTPException(404, f"Plugin {plugin_id} not found")
    
    # Validate config keys and values
    ALLOWED_CONFIGS = {
        "consciousness": {"workspace_capacity", "attention_threshold", "broadcast_enabled"},
        "liberation": {"audit_enabled", "threat_detection", "red_flag_sensitivity"},
    }
    
    allowed_keys = ALLOWED_CONFIGS.get(plugin_id, set())
    invalid_keys = set(config.keys()) - allowed_keys
    if invalid_keys:
        raise HTTPException(400, f"Invalid config keys: {invalid_keys}")
    
    # Validate value types and ranges
    if plugin_id == "consciousness":
        if "workspace_capacity" in config and not isinstance(config["workspace_capacity"], int):
            raise HTTPException(400, "workspace_capacity must be integer")
        ...
    
    _plugin_states[plugin_id]["config"].update(config)
```

---

## 2. AUTHENTICATION/AUTHORIZATION FINDINGS

### 2.1 🔴 CRITICAL: In-Memory Token Storage with No Persistence

**File:** `src/heretek_swarm/api/consensus.py`  
**Lines:** 38-70

**Code Snippet:**
```python
class ConsensusAuthManager:
    """Manages authentication for consensus operations."""
    
    def __init__(self):
        self._valid_tokens: Dict[str, Dict[str, Any]] = {}  # In-memory only!
        self._token_expiry = timedelta(hours=24)
        self._agent_permissions: Dict[str, List[str]] = {}
```

**Issue:**
- Tokens stored only in memory (lost on restart)
- No Redis/database fallback for distributed systems
- Race conditions in multi-worker deployments
- No token revocation persistence

**Severity:** CRITICAL

**Existing Controls:** Token expiry mechanism exists but ineffective for distributed systems.

**Recommended Fix:**
```python
class ConsensusAuthManager:
    def __init__(self, redis_client=None):
        self._redis = redis_client
        self._token_expiry = timedelta(hours=24)
        self._agent_permissions: Dict[str, List[str]] = {}
    
    async def _get_from_storage(self, token: str) -> Optional[Dict]:
        if self._redis:
            data = await self._redis.get(f"auth_token:{token}")
            return json.loads(data) if data else None
        return self._tokens.get(token)
    
    async def generate_token(self, agent_id: str, permissions: Optional[List[str]] = None) -> str:
        token = secrets.token_urlsafe(32)
        token_data = {
            "agent_id": agent_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + self._token_expiry).isoformat(),
            "permissions": permissions or ["vote", "create", "view"],
        }
        
        if self._redis:
            await self._redis.setex(
                f"auth_token:{token}",
                int(self._token_expiry.total_seconds()),
                json.dumps(token_data)
            )
        else:
            self._valid_tokens[token] = token_data
        
        return token
```

---

### 2.2 🔴 HIGH: WebSocket Authentication Uses Predictable Default Secret

**File:** `src/heretek_swarm/api/websockets.py`  
**Lines:** 30-35

**Code Snippet:**
```python
class WebSocketAuthManager:
    """Manages authentication for WebSocket connections."""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or os.environ.get(
            "WEBSOCKET_SECRET_KEY", 
            secrets.token_hex(32)  # Generated at startup!
        )
```

**Issue:**
- If `WEBSOCKET_SECRET_KEY` env var is not set, key is generated at startup
- Generated keys are lost on restart
- In containerized environments, may regenerate on each pod
- Different pods would have different keys

**Severity:** HIGH

**Existing Controls:** Token validation exists.

**Recommended Fix:**
```python
class WebSocketAuthManager:
    def __init__(self, secret_key: Optional[str] = None):
        key = secret_key or os.environ.get("WEBSOCKET_SECRET_KEY")
        if not key:
            raise RuntimeError(
                "WEBSOCKET_SECRET_KEY environment variable is required. "
                "Generate with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        self.secret_key = key
```

---

### 2.3 🟡 MEDIUM: Missing Authorization Checks on Agent ID Parameter

**File:** `src/heretek_swarm/api/agents_management.py`  
**Lines:** 100-140

**Code Snippet:**
```python
@router.get("/types/{agent_type}")
async def get_agent_type_metadata(
    agent_type: str,
    registry: EnhancedAgentRegistry = Depends(get_registry),
    authenticated: str = Depends(verify_auth),
):
 validated against whitelist
- Path traversal possible (`../../etc/passwd`)
- No length constraints on agent_type
- Information disclosure if invalid types reveal internal paths

**Severity:** MEDIUM

**Existing Controls:** Authentication present, but input validation missing.

**Recommended Fix:**
```python
from fastapi import Path

# Define allowed agent types
ALLOWED_AGENT_TYPES = {
    "coordinator", "researcher", "coder", "critic", "synthesizer",
    "planner", "executor", "monitor"
}

@router.get("/types/{agent_type:path}")
async def get_agent_type_metadata(
    agent_type: str = Path(..., min_length=1, max_length=50),
    registry: EnhancedAgentRegistry = Depends(get_registry),
    authenticated: str = Depends(verify_auth),
):
    # Validate agent_type against whitelist
    if agent_type not in ALLOWED_AGENT_TYPES:
        raise HTTPException(404, f"Agent type '{agent_type}' not found")
```

---

### 2.4 🟡 MEDIUM: Authorization Bypass via Agent ID Header

**File:** `src/heretek_swarm/api/consensus.py`  
**Lines:** 99-119

**Code Snippet:**
```python
async def get_authenticated_agent(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_agent_id: Optional[str] = Header(None, description="Agent ID header"),
) -> str:
    # ...
    # Verify agent ID matches if provided in header
    if x_agent_id and x_agent_id != agent_id:
        raise HTTPException(403, "Agent ID mismatch. Token does not match provided agent ID.")
    
    return agent_id
```

**Issue:**
- Agent ID from token can be overwritten by `X-Agent-ID` header
- If header is provided and matches token, no issue
- But the logic seems backwards - should check if token's agent_id matches, not header

**Severity:** MEDIUM

**Existing Controls:** Token validation exists but logic is confusing.

**Recommended Fix:**
```python
async def get_authenticated_agent(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_agent_id: Optional[str] = Header(None, description="Agent ID header"),
) -> str:
    if not credentials:
        raise HTTPException(401, "Authentication required. Provide Bearer token.")
    
    token = credentials.credentials
    is_valid, agent_id_from_token, error = consensus_auth_manager.validate_token(token)
    
    if not is_valid:
        raise HTTPException(401, f"Authentication failed: {error}")
    
    # Use agent_id from validated token only
    # X-Agent-ID header is for logging/tracing, not authorization
    return agent_id_from_token
```

---

## 3. ENVIRONMENT VARIABLE EXPOSURE FINDINGS

### 3.1 🔴 CRITICAL: Hardcoded Fallback Database Credentials in Code

**File:** `src/heretek_swarm/api/main.py`  
**Lines:** 224-231

**Code Snippet:**
```python
async def check_postgres() -> Dict[str, Any]:
    # ...
    if not memory_store:
        # Try to get database URL and connect directly
        db_url = os.environ.get("DATABASE_URL", 
            "postgresql+asyncpg://heretek:langfuse@postgres:5432/heretek_swarm")  # HARDCODED!
```

**Issue:**
- Default credentials embedded in source code
- If .env file is missing, falls back to hardcoded credentials
- These credentials likely exist in docker-compose.yml
- Exposed in stack traces and error messages

**Severity:** CRITICAL

**Existing Controls:** Should use only environment variables.

**Recommended Fix:**
```python
async def check_postgres() -> Dict[str, Any]:
    try:
        if not memory_store:
            db_url = os.environ.get("DATABASE_URL")
            if not db_url:
                return {
                    "status": "unhealthy",
                    "error": "DATABASE_URL not configured",
                }
            
            from sqlalchemy.ext.asyncio import create_async_engine
            from sqlalchemy import text
            engine = create_async_engine(db_url)
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            await engine.dispose()
```

---

### 3.2 🟠 HIGH: API Key Generated Without Warning in Production

**File:** `src/heretek_swarm/gateway/auth.py`  
**Lines:** 37-56

**Code Snippet:**
```python
def get_api_key_from_env() -> str:
    key = os.getenv("HERETEK_API_KEY")
    
    if not key:
        environment = os.getenv("ENVIRONMENT", "development")
        
        if environment == "production":
            logger.error("api_key_missing_production")
            raise RuntimeError("HERETEK_API_KEY required in production...")
        
        # Development: generate and warn
        key = generate_api_key()
        logger.warning(
            "api_key_generated_development",
            message="Set HERETEK_API_KEY environment variable",
            key_prefix=key[:10] + "..."
        )
    
    return key
```

**Issue:**
- Auto-generates API key in development mode
- Key logged with prefix (partial exposure)
- No persistence - key changes on restart
- Developers may unknowingly use unstable keys

**Severity:** HIGH

**Existing Controls:** Production mode blocks startup.

**Recommended Fix:**
```python
def get_api_key_from_env() -> str:
    key = os.getenv("HERETEK_API_KEY")
    
    if not key:
        environment = os.getenv("ENVIRONMENT", "development")
        
        if environment == "production":
            logger.error("api_key_missing_production")
            raise RuntimeError(
                "HERETEK_API_KEY environment variable is required in production. "
                "Generate with: python -c \"import secrets; print(f'htsk_{secrets.token_urlsafe(32)}')\""
            )
        
        # Development: FAIL FAST instead of auto-generating
        logger.error(
            "api_key_missing_development",
            message="Set HERETEK_API_KEY environment variable. "
                    "Generate with: python -c \"import secrets; print(f'htsk_{secrets.token_urlsafe(32)}')\""
        )
        raise RuntimeError(
            "HERETEK_API_KEY environment variable is required. "
            "Generate with: python -c \"import secrets; print(f'htsk_{secrets.token_urlsafe(32)}')\""
        )
    
    # Validate key format
    if not key.startswith("htsk_") or len(key) < 40:
        logger.warning("api_key_format_suboptimal", message="API key should start with 'htsk_' and be 40+ characters")
    
    return key
```

---

### 3.3 🟡 MEDIUM: Sensitive Values in Environment Variables Logged

**File:** `src/heretek_swarm/api/main.py`  
**Lines:** 83-100

**Code Snippet:**
```python
# Initialize mem0 backend if available
if MEM0_AVAILABLE:
    try:
        qdrant_host = await get_config("qdrant.url", default=os.environ.get("QDRANT_HOST", "localhost"))
        qdrant_port = await get_config("qdrant.port", default=int(os.environ.get("QDRANT_PORT", "6333")))
        openai_api_key = await get_config("llm.api_key", default=os.environ.get("OPENAI_API_KEY"))
        
        mem0_config = Mem0Config(
            qdrant_host=qdrant_host,
            qdrant_port=int(qdrant_port),
            openai_api_key=openai_api_key,  # Potentially sensitive
        )
```

**Issue:**
- API keys passed through multiple layers
- May appear in structlog output if not properly filtered
- No evidence of redaction in logging

**Severity:** MEDIUM

**Existing Controls:** Structured logging (structlog) may help filter.

**Recommended Fix:**
```python
mem0_config = Mem0Config(
    qdrant_host=qdrant_host,
    qdrant_port=int(qdrant_port),
    openai_api_key=openai_api_key,
)

# Add processor to structlog to redact sensitive values
from structlog.processors import UnicodeDecoder, JSONRenderer

def redact_sensitive_values(logger, method_name, event_dict):
    sensitive_keys = {'api_key', 'token', 'secret', 'password', 'key'}
    for key in list(event_dict.keys()):
        if any(s in key.lower() for s in sensitive_keys):
            if isinstance(event_dict[key], str) and len(event_dict[key]) > 8:
                event_dict[key] = event_dict[key][:4] + "****"
    return event_dict
```

---

### 3.4 🟡 MEDIUM: CONFIG_ENCRYPTION_KEY Optional with No Default

**File:** `src/heretek_swarm/config/service.py`  
**Lines:** 78-85

**Code Snippet:**
```python
# Initialize Fernet encryption for API keys
self._fernet: Optional[Fernet] = None
self._encryption_key = os.environ.get("CONFIG_ENCRYPTION_KEY")
if self._encryption_key:
    self._initialize_encryption()
else:
    logger.warning("CONFIG_ENCRYPTION_KEY not set - API keys will not be encrypted")
```

**Issue:**
- API key encryption is optional
- System works without encryption (just warns)
- Production deployments may accidentally run unencrypted
- No enforcement mechanism

**Severity:** MEDIUM

**Existing Controls:** Warning logged.

**Recommended Fix:**
```python
self._encryption_key = os.environ.get("CONFIG_ENCRYPTION_KEY")
environment = os.environ.get("ENVIRONMENT", "development")

if not self._encryption_key:
    if environment == "production":
        raise RuntimeError(
            "CONFIG_ENCRYPTION_KEY is required in production. "
            "Generate with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    logger.warning("CONFIG_ENCRYPTION_KEY not set - API keys will not be encrypted")
else:
    self._initialize_encryption()
```

---

## 4. POSITIVE SECURITY CONTROLS (To Preserve)

The following security controls are well-implemented and should be preserved:

### 4.1 ✅ Pydantic v2 with extra='forbid'
**File:** `src/heretek_swarm/security/zero_trust.py`
- Rejects unknown fields in request bodies
- Strong input validation baseline

### 4.2 ✅ UUID v4 Validation
**File:** `src/heretek_swarm/security/zero_trust.py`
- Request IDs must be valid UUID v4 format
- 128-bit entropy protection

### 4.3 ✅ 4-Layer Zero Trust Architecture
**File:** `src/heretek_swarm/security/zero_trust.py`
- Layer 1: Input validation with injection detection
- Layer 2: Context validation with behavioral analysis
- Layer 3: Output validation with PII detection
- Layer 4: Audit logging

### 4.4 ✅ Fernet Encryption for API Keys
**File:** `src/heretek_swarm/config/service.py`
- API keys encrypted at rest in database
- Automatic encryption/decryption

### 4.5 ✅ Comprehensive Injection Pattern Detection
**File:** `src/heretek_swarm/security/validators.py`
- Detects Python injection (exec, eval, __import__)
- Detects shell injection (command substitution)
- Detects SQL injection patterns
- Detects path traversal

### 4.6 ✅ Rate Limiting Infrastructure
**File:** `src/heretek_swarm/api/rate_limiting.py`
- Tiered rate limiting (anonymous, authenticated, premium, internal)
- Token bucket algorithm
- DDoS protection mechanisms

---

## 5. SUMMARY TABLE

| ID | Category | Finding | Severity | Status |
|----|----------|---------|----------|--------|
| 1.1 | Input Validation | Missing auth on consensus results endpoint | CRITICAL | 🔴 Open |
| 1.2 | Input Validation | Missing auth on token generation endpoint | CRITICAL | 🔴 Open |
| 1.3 | Input Validation | Missing auth and validation on token revocation | HIGH | 🔴 Open |
| 1.4 | Input Validation | No rate limiting on auth endpoints | MEDIUM | 🟡 Open |
| 1.5 | Input Validation | Insufficient plugin config validation | MEDIUM | 🟡 Open |
| 2.1 | Auth/Authz | In-memory token storage (not distributed-safe) | CRITICAL | 🔴 Open |
| 2.2 | Auth/Authz | WebSocket auto-generated secret key | HIGH | 🔴 Open |
| 2.3 | Auth/Authz | Missing agent_type whitelist validation | MEDIUM | 🟡 Open |
| 2.4 | Auth/Authz | Confusing authorization logic with headers | MEDIUM | 🟡 Open |
| 3.1 | Env Vars | Hardcoded database credentials fallback | CRITICAL | 🔴 Open |
| 3.2 | Env Vars | Auto-generated API key without persistence | HIGH | 🟠 Open |
| 3.3 | Env Vars | Sensitive values may be logged | MEDIUM | 🟡 Open |
| 3.4 | Env Vars | Encryption key optional in production | MEDIUM | 🟡 Open |

---

## 6. RECOMMENDATIONS PRIORITY

### Immediate Actions (Before Production)
1. Add authentication to `/api/consensus/{consensus_id}/results` endpoint
2. Add authentication to `/api/consensus/auth/token` endpoint
3. Remove hardcoded database credentials fallback
4. Enforce CONFIG_ENCRYPTION_KEY in production mode

### High Priority (Within 1 Week)
1. Implement Redis-backed token storage for distributed deployments
2. Fix WebSocket secret key startup behavior
3. Add rate limiting to authentication endpoints
4. Validate all path parameters against whitelists

### Medium Priority (Within 1 Month)
1. Implement comprehensive input validation schemas using Pydantic
2. Add structured redaction to structlog for sensitive values
3. Review and fix all endpoints for consistent auth patterns
4. Implement mTLS for internal service communication

---

*End of Security Audit Report - Part 2*
