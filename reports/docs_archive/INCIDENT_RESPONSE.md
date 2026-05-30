# Incident Response Runbook

## Severity Levels

| Level | Description | Response Time | Escalation |
|-------|-------------|---------------|------------|
| SEV1 | System down, all agents offline | 15 minutes | Engineering Lead + On-call |
| SEV2 | Partial outage, degraded service | 30 minutes | On-call engineer |
| SEV3 | Minor issue, non-critical | 2 hours | Next business day |

## Incident Response Procedure

### 1. Detect
- Monitor Prometheus alerts in Grafana
- Check dashboard health indicators
- Review NATS message queue depth
- Monitor error rates in API logs

### 2. Triage
```bash
# Check overall system health
curl http://localhost:8000/api/health

# Check individual services
docker compose ps

# Check recent logs
docker compose logs --tail=100 api
docker compose logs --tail=100 nats
```

### 3. Contain
- If single agent: restart that agent via API
- If service down: `docker compose restart <service>`
- If database issue: check disk space, connection pool
- If memory leak: restart API server

### 4. Resolve
- Apply fix based on root cause
- Verify with health checks
- Monitor for 15 minutes post-fix

### 5. Post-Mortem
- Document timeline in incident report
- Identify root cause
- Create action items to prevent recurrence
- Update this runbook if needed

## Common Recovery Commands

```bash
# Full restart (preserves data)
docker compose down && docker compose up -d

# Restart specific service
docker compose restart api

# Check resource usage
docker stats --no-stream

# View NATS message stats
nats server report connections --server localhost:4222

# Database connection check
docker compose exec postgres pg_isready -U heretek

# Redis health
docker compose exec redis redis-cli PING

# Qdrant health
curl http://localhost:6333/health
```

## Escalation Contacts

| Role | Contact |
|------|---------|
| Engineering Lead | engineering@heretek.ai |
| Security Team | security@heretek.ai |
| DevOps On-call | devops@heretek.ai |

## Recovery Time Objectives (RTO)

| Service | RTO |
|---------|-----|
| API Server | 5 minutes |
| NATS | 2 minutes |
| PostgreSQL | 10 minutes |
| Redis | 2 minutes |
| Qdrant | 5 minutes |
| Dashboard | 5 minutes |
