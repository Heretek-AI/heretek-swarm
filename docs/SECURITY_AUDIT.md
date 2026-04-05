# SECURITY AUDIT CHECKLIST
## Heretek Swarm Security Review

**Date:** 2026-04-07
**Status:** In Progress
**Priority:** P0

---

## 🔒 AUTHENTICATION & AUTHORIZATION

### ✅ Implemented

- [x] Bearer token authentication on gateway
- [x] API key from environment variable (HERETEK_API_KEY)
- [x] 401 responses for missing/invalid credentials
- [x] Development key generation with warnings

### ⚠️ Needs Review

- [ ] Rate limiting on all endpoints
- [ ] API key rotation mechanism
- [ ] OAuth integration for external providers
- [ ] Role-based access control (RBAC)

### 🔧 Required Actions

```python
# Add rate limiting (src/heretek_swarm/api/main.py)
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/health")
@limiter.limit("100/minute")
async def health_check(request):
    ...
```

---

## 🛡️ INPUT VALIDATION

### ✅ Implemented

- [x] Pydantic models for configuration
- [x] Type hints throughout codebase
- [x] JSON schema validation via FastAPI

### ⚠️ Needs Review

- [ ] SQL injection prevention (using asyncpg - parameterized queries)
- [ ] XSS prevention (frontend escaping)
- [ ] Path traversal prevention in file tools
- [ ] Command injection in run_command tool

### 🔧 Required Actions

```python
# Fix run_command security (src/heretek_swarm/runtime/tools.py)
ALLOWED_COMMANDS = {"ls", "cat", "pwd", "echo"}  # Whitelist

async def run_command(command: str, timeout: int = 30) -> Dict:
    # Validate command
    base_cmd = command.split()[0]
    if base_cmd not in ALLOWED_COMMANDS:
        return {"success": False, "error": "Command not allowed"}
    
    # ... rest of implementation
```

---

## 🔐 SECRETS MANAGEMENT

### ✅ Implemented

- [x] No hardcoded credentials in code
- [x] Environment variables for all secrets
- [x] API key generation for development

### ⚠️ Needs Review

- [ ] Secrets should be in Docker secrets or Vault
- [ ] .env file in .gitignore
- [ ] No secrets in logs
- [ ] Key rotation policy

### 🔧 Required Actions

```bash
# Add to .gitignore
echo ".env" >> .gitignore
echo "*.key" >> .gitignore
echo "data/*.db" >> .gitignore

# Create .env.example
cat > .env.example <<EOF
HERETEK_API_KEY=htsk_your_key_here
OPENAI_API_KEY=sk-your_key_here
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
REDIS_URL=redis://localhost:6379
QDRANT_HOST=localhost
QDRANT_PORT=6333
EOF
```

---

## 📊 LOGGING & AUDIT

### ✅ Implemented

- [x] Structured logging with structlog
- [x] Authentication failure logging
- [x] Connection/disconnection logging

### ⚠️ Needs Review

- [ ] Audit log for all agent actions
- [ ] Log rotation
- [ ] No sensitive data in logs
- [ ] Centralized log aggregation

### 🔧 Required Actions

```python
# Add audit logging middleware
import logging
from datetime import datetime

class AuditLogger:
    def __init__(self, log_file: str = "audit.log"):
        self.logger = logging.getLogger("audit")
        handler = logging.FileHandler(log_file)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(message)s")
        )
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log(self, event: str, **kwargs):
        self.logger.info(f"{event} | {kwargs}")

# Usage
audit = AuditLogger()
audit.log("agent_action", agent_id="steward", action="think")
```

---

## 🌐 NETWORK SECURITY

### ✅ Implemented

- [x] CORS configured (currently allow all for dev)
- [x] WebSocket authentication
- [x] Health check endpoints

### ⚠️ Needs Review

- [ ] Restrict CORS to specific origins in production
- [ ] HTTPS/TLS for all connections
- [ ] Network segmentation
- [ ] DDoS protection

### 🔧 Required Actions

```python
# Restrict CORS in production (src/heretek_swarm/api/main.py)
import os

environment = os.getenv("ENVIRONMENT", "development")

if environment == "production":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://your-domain.com",
            "https://app.your-domain.com"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

---

## 🗄️ DATABASE SECURITY

### ✅ Implemented

- [x] pgvector for vector operations
- [x] Parameterized queries via SQLAlchemy
- [x] Separate database user (heretek)

### ⚠️ Needs Review

- [ ] Database encryption at rest
- [ ] SSL/TLS for database connections
- [ ] Regular backups
- [ ] Connection pooling limits

### 🔧 Required Actions

```python
# Enable SSL for PostgreSQL (in DATABASE_URL)
# postgresql+asyncpg://user:pass@host:5432/db?sslmode=require

# Add connection limits to docker-compose.yml
# postgres:
#   environment:
#     - POSTGRES_MAX_CONNECTIONS=100
```

---

## 🧪 SECURITY TESTING

### Required Tests

```python
# tests/test_security.py

class TestSecurity:
    
    def test_auth_required_on_endpoints(self):
        """All endpoints require authentication."""
        response = client.get("/api/agents")
        assert response.status_code == 401
    
    def test_invalid_token_rejected(self):
        """Invalid tokens are rejected."""
        response = client.get(
            "/api/agents",
            headers={"Authorization": "Bearer invalid"}
        )
        assert response.status_code == 401
    
    def test_sql_injection_prevented(self):
        """SQL injection attempts fail."""
        response = client.post(
            "/api/memory/search",
            json={"query": "'; DROP TABLE users; --"}
        )
        assert response.status_code != 500
    
    def test_command_injection_prevented(self):
        """Command injection blocked."""
        from heretek_swarm.runtime.tools import run_command
        result = await run_command("rm -rf /")
        assert result["success"] is False
```

---

## ✅ SECURITY CHECKLIST SUMMARY

| Category | Status | Priority |
|----------|--------|----------|
| Authentication | ✅ Implemented | P0 |
| Input Validation | ⚠️ Needs Work | P0 |
| Secrets Management | ⚠️ Needs Work | P0 |
| Logging & Audit | ⚠️ Needs Work | P1 |
| Network Security | ⚠️ Needs Work | P1 |
| Database Security | ✅ Basic | P1 |
| Security Testing | ❌ Not Started | P1 |

---

## 🚀 IMMEDIATE ACTIONS

1. **Add rate limiting** - Prevent DoS
2. **Fix command injection** - Whitelist allowed commands
3. **Restrict CORS** - Production origins only
4. **Add security tests** - Automated validation
5. **Enable HTTPS** - TLS for all connections

---

**Next Review:** After Phase 4 completion
**Auditor:** Security Team
