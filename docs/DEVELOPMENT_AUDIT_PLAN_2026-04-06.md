# Development & Audit Plan - 2026-04-06

## Executive Summary

This plan outlines a 14-day development and audit cycle for the Heretek Swarm project, targeting production readiness for The Collective - an autonomous multi-agent AI cluster. Current system health is estimated at **90-96% completion** with all major components implemented.

**Primary Objectives:**
1. Validate production Kubernetes deployment
2. Complete security audit of platform connectors
3. Expand test coverage from ~60% to >80%
4. Enhance visual workflow builder UX
5. Tune monitoring for production
6. Establish baseline performance metrics
7. Complete documentation updates

**Risk Level:** Medium - Core functionality is stable; gaps are in validation and hardening.

---

## Phase 1: Production Validation (Days 1-2)

### 1.1 Kubernetes Deployment Validation

**Files to Audit:**
- [`k8s/namespace.yaml`](k8s/namespace.yaml)
- [`k8s/api-deployment.yaml`](k8s/api-deployment.yaml)
- [`k8s/dashboard-deployment.yaml`](k8s/dashboard-deployment.yaml)
- [`k8s/autonomous-deployment.yaml`](k8s/autonomous-deployment.yaml)
- [`k8s/postgres-deployment.yaml`](k8s/postgres-deployment.yaml)
- [`k8s/redis-deployment.yaml`](k8s/redis-deployment.yaml)
- [`k8s/qdrant-deployment.yaml`](k8s/qdrant-deployment.yaml)
- [`k8s/configmaps.yaml`](k8s/configmaps.yaml)
- [`k8s/secrets.yaml`](k8s/secrets.yaml)
- [`k8s/ingress.yaml`](k8s/ingress.yaml)
- [`k8s/hpa.yaml`](k8s/hpa.yaml)
- [`scripts/deploy-k8s.sh`](scripts/deploy-k8s.sh)

**Tasks:**
- [ ] Verify all deployment specs have proper resource limits (CPU/memory)
- [ ] Validate liveness and readiness probes are configured
- [ ] Check HPA thresholds are appropriate for production load
- [ ] Verify secrets are properly referenced (not hardcoded)
- [ ] Test deployment script in staging environment
- [ ] Validate ingress TLS configuration
- [ ] Verify service mesh compatibility (if using Istio/Linkerd)

**Success Criteria:**
- All pods start successfully with `kubectl rollout status`
- Health endpoints return 200 OK for all services
- HPA scales correctly under load test
- No secrets exposed in pod specs or logs
- Deployment completes in <10 minutes

**Audit Procedure:**
```bash
# Validate namespace
kubectl get namespace heretek-swarm

# Check all deployments
kubectl get deployments -n heretek-swarm

# Verify pod status
kubectl get pods -n heretek-swarm -o wide

# Check resource limits
kubectl describe deployment heretek-swarm-api -n heretek-swarm | grep -A 10 "Limits:"

# Test health endpoints
kubectl port-forward -n heretek-swarm svc/heretek-swarm-api 8000:8000
curl http://localhost:8000/api/health/live
```

### 1.2 Autonomous Runtime Validation

**Files to Audit:**
- [`src/heretek_swarm/runtime/autonomous_runtime.py`](src/heretek_swarm/runtime/autonomous_runtime.py)
- [`src/heretek_swarm/runtime/autonomous_runtime_config.py`](src/heretek_swarm/runtime/autonomous_runtime_config.py)
- [`src/heretek_swarm/runtime/agent_runtime.py`](src/heretek_swarm/runtime/agent_runtime.py)

**Tasks:**
- [ ] Verify 24/7 scheduler is functioning
- [ ] Test self-healing mechanisms
- [ ] Validate health monitoring alerts
- [ ] Test automatic recovery from failures
- [ ] Verify state persistence across restarts

**Success Criteria:**
- Autonomous runtime operates for 24 hours without manual intervention
- Failed agents are automatically restarted within 60 seconds
- State is preserved across agent restarts
- Health alerts are triggered for anomalies

---

## Phase 2: Security Hardening (Days 3-4)

### 2.1 Platform Connector Security Audit

**Files to Audit:**
- [`src/heretek_swarm/integrations/discord_bot.py`](src/heretek_swarm/integrations/discord_bot.py)
- [`src/heretek_swarm/integrations/telegram_bot.py`](src/heretek_swarm/integrations/telegram_bot.py)
- [`src/heretek_swarm/integrations/slack_bot.py`](src/heretek_swarm/integrations/slack_bot.py)
- [`src/heretek_swarm/integrations/praison_handoffs.py`](src/heretek_swarm/integrations/praison_handoffs.py)

**Zero-Trust Audit Procedures:**
- [ ] Audit all external API calls for input sanitization
- [ ] Verify bot tokens are never logged
- [ ] Check rate limiting is applied to all endpoints
- [ ] Validate message content filtering
- [ ] Test for command injection vulnerabilities
- [ ] Verify OAuth flows are secure (if applicable)
- [ ] Audit webhook endpoints for authentication

**Success Criteria:**
- No secrets appear in logs (verified via log scanning)
- All external inputs are sanitized before processing
- Rate limiting prevents abuse (>100 req/min blocked)
- No command injection vulnerabilities found

**Audit Procedure:**
```bash
# Scan for hardcoded secrets
grep -r "xoxb-\|sk-\|ghp_\|AKIA" src/heretek_swarm/integrations/

# Check for logging of sensitive data
grep -r "message.content\|token\|secret\|password" src/heretek_swarm/integrations/ | grep -v "REDACTED"

# Run Bandit security scanner
bandit -r src/heretek_swarm/integrations/ -f json -o security-report.json

# Review report
cat security-report.json | jq '.results[] | select(.issue_severity == "HIGH")'
```

### 2.2 Guardrails System Validation

**Files to Audit:**
- [`src/heretek_swarm/security/guardrails.py`](src/heretek_swarm/security/guardrails.py)
- [`src/heretek_swarm/gateway/auth.py`](src/heretek_swarm/gateway/auth.py)
- [`src/heretek_swarm/api/rate_limiting.py`](src/heretek_swarm/api/rate_limiting.py)

**Tasks:**
- [ ] Test all blocked patterns from [`DEFAULT_BLOCKED_PATTERNS`](src/heretek_swarm/security/guardrails.py:466)
- [ ] Verify SQL injection patterns are blocked
- [ ] Test XSS pattern detection
- [ ] Validate path traversal blocking
- [ ] Test personal information redaction
- [ ] Verify code execution blocking
- [ ] Test rate limiting under load

**Success Criteria:**
- All malicious inputs are blocked with appropriate action
- Personal information is redacted from outputs
- Rate limiting triggers at configured thresholds
- No false positives on legitimate inputs

---

## Phase 3: Test Coverage Expansion (Days 5-7)

### 3.1 Test Coverage Analysis

**Current Test Files:**
- [`tests/test_agents.py`](tests/test_agents.py)
- [`tests/test_consciousness_api.py`](tests/test_consciousness_api.py)
- [`tests/test_gateway.py`](tests/test_gateway.py)
- [`tests/test_integrations.py`](tests/test_integrations.py)
- [`tests/test_rag_pipeline.py`](tests/test_rag_pipeline.py)
- [`tests/test_tools.py`](tests/test_tools.py)
- [`tests/evaluation/test_evaluator.py`](tests/evaluation/test_evaluator.py)
- [`tests/integration/test_a2a_messaging.py`](tests/integration/test_a2a_messaging.py)
- [`tests/integration/test_state_rollback.py`](tests/integration/test_state_rollback.py)
- [`tests/load/test_concurrent_agents.py`](tests/load/test_concurrent_agents.py)
- [`tests/memory/test_dual_tier.py`](tests/memory/test_dual_tier.py)
- [`tests/plugins/test_consciousness_enhanced.py`](tests/plugins/test_consciousness_enhanced.py)
- [`tests/security/test_security.py`](tests/security/test_security.py)
- [`tests/state/test_state_management.py`](tests/state/test_state_management.py)
- [`tests/tools/test_registry.py`](tests/tools/test_registry.py)
- [`tests/unit/test_actor_factory.py`](tests/unit/test_actor_factory.py)

**Coverage Analysis Command:**
```bash
pytest tests/ --cov=src --cov-report=html --cov-report=term
```

**Target Coverage:** >80% (currently ~60%)

### 3.2 Missing Test Files to Create

**Priority Tests:**

1. **Collective Intelligence Tests**
   - [ ] Create [`tests/test_collective_society.py`](tests/test_collective_society.py)
     - Test [`AgentSociety`](src/heretek_swarm/collective/society.py:272) hierarchy
     - Test [`CollectiveMemory`](src/heretek_swarm/collective/society.py:177) operations
     - Test emergent behavior detection
     - Test contribution caching

2. **Consciousness Plugin Tests**
   - [ ] Create [`tests/plugins/test_consciousness_gwt.py`](tests/plugins/test_consciousness_gwt.py)
     - Test Global Workspace Theory calculation
     - Test IIT Phi calculation
     - Test AST calculation
     - Test FEP calculation

3. **Workflow Engine Tests**
   - [ ] Create [`tests/test_workflow_engine.py`](tests/test_workflow_engine.py)
     - Test workflow parsing
     - Test node execution
     - Test error handling and rollback
     - Test topological sort

4. **Consensus Tests**
   - [ ] Create [`tests/consensus/test_maker.py`](tests/consensus/test_maker.py)
     - Test MAKER consensus algorithm
     - Test reputation-weighted voting
     - Test red-flagging on anomalies

5. **Observability Tests**
   - [ ] Create [`tests/observability/test_metrics.py`](tests/observability/test_metrics.py)
     - Test Prometheus metrics export
     - Test metric collection accuracy
     - Test tracing integration

**Success Criteria:**
- Overall coverage >80%
- All critical paths have unit tests
- Integration tests cover A2A messaging
- Load tests validate 1000+ concurrent agents

---

## Phase 4: UI/UX Enhancement (Days 8-10)

### 4.1 Visual Workflow Builder Enhancement

**Files to Enhance:**
- [`dashboard/frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx`](dashboard/frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx)
- [`dashboard/frontend/src/components/WorkflowBuilder/types.ts`](dashboard/frontend/src/components/WorkflowBuilder/types.ts)
- [`dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx`](dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx)

**Current Node Types (from [`nodePalette`](dashboard/frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx:68)):**
- Agents: Steward, Alpha
- Tools: Code Execution, Web Browser
- Memory: Ephemeral, Persistent, mem0
- Decision: Conditional Branch
- Connector: Agent to Agent
- LLM: OpenAI GPT-4

**Enhancement Tasks:**
- [ ] Add more agent types (Beta, Charlie, Coder, Sentinel, Historian)
- [ ] Add more tool types (File I/O, Database Query, API Call)
- [ ] Add loop/iteration nodes
- [ ] Add parallel execution nodes
- [ ] Add sub-workflow nodes
- [ ] Improve node configuration UI (forms vs JSON)
- [ ] Add workflow templates
- [ ] Add workflow versioning UI
- [ ] Add real-time execution visualization
- [ ] Add node search/filter in palette

**Success Criteria:**
- All 17+ character types available as nodes
- Configuration is form-based, not JSON editing
- Workflow templates are available for common patterns
- Execution shows real-time node status (running/success/failed)

### 4.2 Consciousness Dashboard Enhancement

**Files to Enhance:**
- [`dashboard/frontend/src/components/Consciousness/ConsciousnessDashboard.tsx`](dashboard/frontend/src/components/Consciousness/ConsciousnessDashboard.tsx)
- [`dashboard/frontend/src/components/Consciousness/types.ts`](dashboard/frontend/src/components/Consciousness/types.ts)

**Tasks:**
- [ ] Add real-time GWT visualization
- [ ] Add IIT Phi metric display
- [ ] Add AST attention heatmap
- [ ] Add FEP free energy graph
- [ ] Add combined consciousness score over time
- [ ] Add agent-by-agent consciousness breakdown

**Success Criteria:**
- All four consciousness theories are visualized
- Metrics update in real-time (WebSocket)
- Historical trends are visible

---

## Phase 5: Performance & Documentation (Days 11-14)

### 5.1 Monitoring Production Tuning

**Files to Audit:**
- [`k8s/prometheus-config.yaml`](k8s/prometheus-config.yaml)
- [`k8s/prometheus-deployment.yaml`](k8s/prometheus-deployment.yaml)
- [`k8s/grafana-deployment.yaml`](k8s/grafana-deployment.yaml)
- [`src/observability/metrics.py`](src/observability/metrics.py)
- [`src/observability/tracing.py`](src/observability/tracing.py)

**Tasks:**
- [ ] Tune Prometheus scrape interval (currently 15s)
- [ ] Add custom alerts for business metrics
- [ ] Create Grafana dashboards for:
  - Agent performance metrics
  - Consensus round times
  - Message latency distribution
  - Consciousness score trends
  - Collective intelligence metrics
- [ ] Configure alerting thresholds
- [ ] Set up alert routing (Slack/PagerDuty)

**Success Criteria:**
- Prometheus scrapes complete in <5s
- All critical metrics have alerts
- Grafana dashboards load in <3s
- Alerts are routed to appropriate channels

### 5.2 Performance Benchmarking

**Files to Create:**
- [`docs/PERFORMANCE_BASELINE.md`](docs/PERFORMANCE_BASELINE.md)
- [`scripts/benchmark_concurrent.py`](scripts/benchmark_concurrent.py)

**Benchmarks to Establish:**
- [ ] Message latency baseline (target: <100ms p95)
- [ ] Consensus round time (target: <5s)
- [ ] Agent spawn time (target: <1s)
- [ ] Workflow execution throughput
- [ ] Memory usage per agent
- [ ] Database query latency
- [ ] API response time (target: <200ms p95)

**Success Criteria:**
- All benchmarks documented in PERFORMANCE_BASELINE.md
- Baselines are reproducible via benchmark scripts
- Performance regression tests in CI pipeline

### 5.3 Documentation Updates

**Files to Create/Update:**
- [ ] Create [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md)
- [ ] Create [`docs/DEPLOYMENT_GUIDE.md`](docs/DEPLOYMENT_GUIDE.md)
- [ ] Create [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md)
- [ ] Create [`docs/WORKFLOW_BUILDER_GUIDE.md`](docs/WORKFLOW_BUILDER_GUIDE.md)
- [ ] Update [`README.md`](README.md) with latest features
- [ ] Create [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md)

**Success Criteria:**
- API reference covers all endpoints
- Deployment guide includes k8s and docker-compose
- Troubleshooting guide covers top 10 issues
- Workflow guide includes screenshots

---

## Zero-Trust Audit Procedures

### General Principles

1. **Never trust, always verify** - All inputs, outputs, and dependencies are treated as potentially hostile
2. **Defense in depth** - Multiple layers of validation
3. **Least privilege** - Minimal permissions for all components
4. **Comprehensive logging** - All actions are auditable

### Code Validation Checklist

For each component, verify:

**Input Validation:**
- [ ] All external inputs are sanitized
- [ ] Length limits are enforced
- [ ] Type validation is performed
- [ ] Pattern matching blocks malicious content

**Output Validation:**
- [ ] Personal information is redacted
- [ ] Code execution is blocked
- [ ] Output length is limited
- [ ] Content filtering is applied

**Error Handling:**
- [ ] No stack traces in user-facing errors
- [ ] Errors are logged with context
- [ ] Graceful degradation on failures
- [ ] Circuit breakers prevent cascade failures

**Security:**
- [ ] No hardcoded secrets
- [ ] Tokens are rotated
- [ ] Auth is required for sensitive operations
- [ ] Rate limiting prevents abuse

### Component-Specific Audits

**API Endpoints:**
```bash
# Test all health endpoints
curl http://localhost:8000/api/health/live
curl http://localhost:8000/api/health/gateway
curl http://localhost:8000/api/health/redis
curl http://localhost:8000/api/health/postgres
curl http://localhost:8000/api/health/qdrant

# Test authentication
curl -H "Authorization: Bearer invalid-token" http://localhost:8000/api/agents
# Should return 401

# Test rate limiting
for i in {1..100}; do curl http://localhost:8000/api/agents; done
# Should return 429 after threshold
```

**Platform Connectors:**
```bash
# Verify no secrets in logs
kubectl logs -n heretek-swarm -l app=heretek-swarm-api | grep -i "token\|secret\|key\|password"
# Should return no results

# Test message sanitization
# Send message with malicious content via Discord/Telegram
# Verify it's blocked or sanitized
```

**Memory System:**
```bash
# Test memory isolation
# Agent A stores data, Agent B should not access without permission

# Test memory cleanup
# Verify ephemeral memory is cleared after session
```

---

## GitHub Research Targets

### Priority 1: Multi-Agent Systems

| Repository | Stars | Focus Area | Research Goal |
|------------|-------|------------|---------------|
| `elizaOS/eliza` | 18k+ | Agent runtime | Port lifecycle patterns |
| `CAMEL-AI/CAMEL` | 5k+ | Agent society | Study role-based coordination |
| `MetaGPT/MetaGPT` | 10k+ | Team orchestration | Study software development workflows |
| `langchain-ai/langchain` | 80k+ | Agent chains | Study chain patterns |
| `microsoft/autogen` | 30k+ | Multi-agent | Study conversation patterns |

### Priority 2: Visual Workflow Builders

| Repository | Stars | Focus Area | Research Goal |
|------------|-------|------------|---------------|
| `FlowiseAI/Flowise` | 51k+ | Visual builder | Study ReactFlow integration |
| `langflow-ai/langflow` | 20k+ | Visual builder | Study node architecture |
| `wbkd/react-flow` | 24k+ | Canvas library | Study custom node types |
| `n8n-io/n8n` | 35k+ | Workflow automation | Study execution engine |

### Priority 3: Observability

| Repository | Stars | Focus Area | Research Goal |
|------------|-------|------------|---------------|
| `prometheus/prometheus` | - | Metrics | Study alerting rules |
| `grafana/grafana` | - | Dashboards | Study panel configurations |
| `open-telemetry/opentelemetry` | - | Tracing | Study span context |

### Research Questions

1. **Agent Runtime:** How does elizaOS handle agent lifecycle events?
2. **Memory:** What patterns does CAMEL use for shared memory?
3. **Consensus:** How does MetaGPT achieve team consensus?
4. **Visual Builder:** How does Flowise handle workflow execution?
5. **Observability:** What metrics are most useful for agent monitoring?

---

## Version Control Protocol

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting only (no code change)
- `refactor`: Code refactor (no feature change)
- `test`: Adding tests
- `chore`: Build/config changes
- `security`: Security-related changes
- `perf`: Performance improvements

**Examples:**
```
feat(collective): add emergent behavior detection to AgentSociety
fix(guardrails): correct regex pattern for SQL injection detection
docs(k8s): add production deployment checklist to README
test(workflow): add unit tests for topological sort
refactor(memory): simplify DualTierMemory interface
security(auth): add rate limiting to authentication endpoint
perf(api): cache supervisor status responses for 5s
```

### Commit Frequency Guidelines

- **Small, atomic commits** - Each commit should represent a single logical change
- **Commit early, commit often** - At least once per focused work session
- **Never commit broken code** - All tests must pass before committing
- **Maximum 500 lines per commit** - Large changes should be split

### Branch Strategy

```
main (production-ready)
  └── develop (integration branch)
        ├── feature/* (new features)
        ├── fix/* (bug fixes)
        ├── audit/* (security audits)
        └── docs/* (documentation)
```

### Pull Request Guidelines

**PR Template:**
```markdown
## Description
[Brief description of changes]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Security enhancement
- [ ] Performance improvement

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added where necessary
- [ ] Documentation updated
- [ ] No new security vulnerabilities introduced
```

**Review Requirements:**
- At least 1 approval required
- All CI checks must pass
- No security vulnerabilities introduced
- Test coverage maintained or improved

---

## Risk Mitigation

### Identified Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Production deployment failure | Medium | High | Staging validation, rollback plan |
| Security vulnerability discovered | Medium | High | Zero-trust audit, Bandit scans |
| Test coverage target not met | Low | Medium | Prioritize critical paths |
| Performance regression | Medium | Medium | Baseline benchmarks, CI checks |
| Documentation incomplete | Low | Low | Assign dedicated time in Phase 5 |

### Contingency Plans

**If Production Deployment Fails:**
1. Rollback to previous stable version
2. Analyze deployment logs
3. Fix identified issues
4. Re-deploy to staging
5. Re-attempt production after staging validation

**If Security Vulnerability Found:**
1. Document vulnerability details
2. Assess scope and impact
3. Create fix with security review
4. Deploy hotfix immediately
5. Conduct post-mortem

**If Test Coverage Stalls:**
1. Identify uncovered critical paths
2. Prioritize by risk level
3. Create targeted tests for high-risk areas
4. Accept lower coverage for low-risk code
5. Create TODO for remaining gaps

**If Performance Regression:**
1. Identify regression source via profiling
2. Compare against baseline metrics
3. Optimize or revert problematic code
4. Update baseline if improvement is permanent
5. Add performance test to prevent regression

---

## Appendix: File Reference Index

### Kubernetes Files
- [`k8s/namespace.yaml`](k8s/namespace.yaml)
- [`k8s/api-deployment.yaml`](k8s/api-deployment.yaml)
- [`k8s/dashboard-deployment.yaml`](k8s/dashboard-deployment.yaml)
- [`k8s/autonomous-deployment.yaml`](k8s/autonomous-deployment.yaml)
- [`k8s/postgres-deployment.yaml`](k8s/postgres-deployment.yaml)
- [`k8s/redis-deployment.yaml`](k8s/redis-deployment.yaml)
- [`k8s/qdrant-deployment.yaml`](k8s/qdrant-deployment.yaml)
- [`k8s/prometheus-deployment.yaml`](k8s/prometheus-deployment.yaml)
- [`k8s/grafana-deployment.yaml`](k8s/grafana-deployment.yaml)
- [`k8s/configmaps.yaml`](k8s/configmaps.yaml)
- [`k8s/secrets.yaml`](k8s/secrets.yaml)
- [`k8s/ingress.yaml`](k8s/ingress.yaml)
- [`k8s/hpa.yaml`](k8s/hpa.yaml)
- [`k8s/prometheus-config.yaml`](k8s/prometheus-config.yaml)

### Source Files
- [`src/heretek_swarm/collective/society.py`](src/heretek_swarm/collective/society.py)
- [`src/heretek_swarm/security/guardrails.py`](src/heretek_swarm/security/guardrails.py)
- [`src/heretek_swarm/integrations/discord_bot.py`](src/heretek_swarm/integrations/discord_bot.py)
- [`src/heretek_swarm/integrations/telegram_bot.py`](src/heretek_swarm/integrations/telegram_bot.py)
- [`src/heretek_swarm/integrations/slack_bot.py`](src/heretek_swarm/integrations/slack_bot.py)
- [`src/heretek_swarm/runtime/autonomous_runtime.py`](src/heretek_swarm/runtime/autonomous_runtime.py)
- [`src/observability/metrics.py`](src/observability/metrics.py)
- [`src/observability/tracing.py`](src/observability/tracing.py)

### Frontend Files
- [`dashboard/frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx`](dashboard/frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx)
- [`dashboard/frontend/src/components/Consciousness/ConsciousnessDashboard.tsx`](dashboard/frontend/src/components/Consciousness/ConsciousnessDashboard.tsx)
- [`dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx`](dashboard/frontend/src/components/Canvas/EnhancedCanvas.tsx)

### Test Files
- [`tests/conftest.py`](tests/conftest.py)
- [`tests/test_agents.py`](tests/test_agents.py)
- [`tests/security/test_security.py`](tests/security/test_security.py)
- [`tests/integration/test_a2a_messaging.py`](tests/integration/test_a2a_messaging.py)

### CI/CD Files
- [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml)
- [`.github/workflows/ci.yml`](.github/workflows/ci.yml)
- [`.pre-commit-config.yaml`](.pre-commit-config.yaml)

### Documentation Files
- [`docs/PRIME_DIRECTIVE_ANALYSIS.md`](docs/PRIME_DIRECTIVE_ANALYSIS.md)
- [`docs/EXECUTION_SUMMARY_2026-04-05.md`](docs/EXECUTION_SUMMARY_2026-04-05.md)
- [`docs/GITHUB_RESEARCH_2026-04-05.md`](docs/GITHUB_RESEARCH_2026-04-05.md)
- [`k8s/README.md`](k8s/README.md)

---

**Document Version:** 1.0.0  
**Created:** 2026-04-06  
**Status:** Ready for Execution  
**Next Review:** After Phase 3 completion

🦞 *The thought that never ends.*
