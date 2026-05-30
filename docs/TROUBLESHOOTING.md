# Troubleshooting Guide

## Common Issues

### Docker Compose Fails to Start

**Symptom:** `docker compose up` exits with errors.

**Solutions:**
1. Check `.env` exists: `cp .env.example .env`
2. Verify `OPENAI_API_KEY` is set in `.env`
3. Check port conflicts: `netstat -ano | findstr 8000` (Windows) or `lsof -i :8000` (Linux)
4. Ensure Docker has enough resources (4GB+ RAM recommended)
5. Run `docker compose down -v` to clean volumes, then retry

### NATS Connection Refused

**Symptom:** Agents fail to connect to NATS.

**Solutions:**
1. Verify NATS container is running: `docker compose ps nats`
2. Check NATS logs: `docker compose logs nats`
3. Verify mTLS certificates exist in `certs/`
4. Regenerate certs: `heretek-swarm certs generate`

### PostgreSQL Connection Errors

**Symptom:** `could not connect to server` or `Connection refused`.

**Solutions:**
1. Check PostgreSQL is running: `docker compose ps postgres`
2. Verify credentials in `.env` match `POSTGRES_USER`/`POSTGRES_PASSWORD`
3. Check disk space: PostgreSQL needs at least 1GB free
4. Reset database: `docker compose down -v postgres && docker compose up -d postgres`

### Agent Not Responding

**Symptom:** Agent shows as `offline` or `degraded` in dashboard.

**Solutions:**
1. Check agent logs: `docker compose logs api | grep <agent_name>`
2. Verify agent is registered: `curl http://localhost:8000/api/agents`
3. Check NATS subject subscriptions: `nats sub --server localhost:4222 "agent.>"`
4. Restart the API server: `docker compose restart api`

### Memory / Qdrant Issues

**Symptom:** Vector search returns empty results.

**Solutions:**
1. Verify Qdrant is running: `docker compose ps qdrant`
2. Check Qdrant health: `curl http://localhost:6333/health`
3. Reindex memories: `heretek-swarm memory reindex`

### Dashboard Shows "Loading" Forever

**Symptom:** Dashboard stuck on loading spinner.

**Solutions:**
1. Check API is reachable: `curl http://localhost:8000/api/health`
2. Check browser console for CORS errors
3. Verify `VITE_API_HOST` is set correctly in dashboard environment
4. Clear browser cache and localStorage

### Test Failures

**Symptom:** `pytest tests/` fails.

**Solutions:**
1. Ensure dev dependencies installed: `pip install -e "backend/[dev]"`
2. Run specific test: `pytest tests/test_auth_endpoints.py -v`
3. Check for missing environment variables
4. Run with verbose output: `pytest tests/ -v --tb=long`

## Getting Help

- Check existing issues: https://github.com/Heretek-AI/heretek-swarm/issues
- Open a new issue with logs attached
- Include your OS, Python version, and Docker version
