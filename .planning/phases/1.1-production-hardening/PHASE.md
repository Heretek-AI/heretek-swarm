# Phase 1.1: Production Hardening & Phase 2 Completion

**Milestone:** v1.1 — Production Hardening & Phase 2 Completion  
**Phase:** 1.1  
**Status:** Planned  
**Created:** 2026-04-15

---

## Phase Goal

Complete Phase 2 remaining items (Steward failover, max_rounds enforcement, quorum logic), production infrastructure hardening, and technical debt resolution. Achieve production-ready deployment with all Phase 1 and Phase 2 gate criteria met.

## Scope

### Phase 2 Remaining (3 items)
- **GOV-01-F**: Steward failover with Charlie tiebreaker logic
- **GOV-05-M**: max_rounds enforcement in deliberation
- **GOV-05-Q**: Quorum logic in Steward triad coordination

### Production Hardening (5 items)
- **DEPLOY-01**: NATS service in docker-compose
- **DEPLOY-02**: LiteLLM config.yaml created or references removed
- **DEPLOY-03**: Database pooling configuration
- **DEPLOY-04**: API key storage hardening
- **OPS-01**: Monitoring and alerting gaps addressed

### Technical Debt (4 items)
- **TD-01**: Pattern extraction enhancement in collective/
- **TD-02**: Consciousness metrics stubs → real implementation
- **TD-03**: Zero-trust exception list finalized
- **TD-04**: Behavioral baseline initialization strategy defined

## Open Questions (from v1.0)

1. NATS auth method — service accounts vs. shared token vs. mTLS?
2. Heartbeat interval — configurable per agent class or global? (default 10s vs 5s)
3. Convoy effect threshold — max_rounds default 3, correct for v1.1?
4. Steward failover identity — Charlie's authority scope during Steward failure?
5. Behavioral baseline initialization — zero state or bootstrap from static rules?
6. Zero-trust exception list — any internal topics exempt from sanitization?

## Success Criteria

| Criterion | Measurement |
|-----------|-------------|
| Steward failover time | < 30 seconds detection + transition |
| Deliberation completes | Within max_rounds (default 3) |
| NATS mesh uptime | ≥ 99.9% under load |
| Database connection efficiency | Pool utilization < 80% |
| Zero-trust exception list | 100% coverage, documented |
| All P0 items resolved | GOV-01-F, GOV-05-M, DEPLOY-01, DEPLOY-02 |
