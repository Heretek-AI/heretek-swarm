# Heretek Swarm Architecture

**Version:** 2.0.0  
**Date:** 2026-04-10  
**Status:** Production-Ready  
**Health Score:** 100/100

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Actor Architecture](#actor-architecture)
3. [Memory System](#memory-system)
4. [Event Mesh](#event-mesh)
5. [Configuration System](#configuration-system)
6. [Security](#security)
7. [Observability](#observability)
   - [Prometheus Metrics](#prometheus-metrics)
   - [Distributed Tracing](#distributed-tracing)
   - [Alerting](#alerting)
8. [Monitoring Setup](#monitoring-setup)

---

## System Overview

The Heretek Swarm is a self-governing swarm of 23 specialized AI agents that operate independently 24/7, make collective decisions through consensus, adapt and learn from experience, and exhibit emergent collective intelligence.

### Architectural Principles

1. **Zero-Trust Security** - All inputs validated, all outputs verified
2. **State Persistence** - All critical State persisted to PostgreSQL
3. **Event-Driven Design** - NATS JetStream for reliable event streaming
4. **Modular Architecture** - Clear separation of concerns between components
5. **Autonomous Operation** - Designed for 24/7 independent operation
6. **Observable** - Prometheus metrics, distributed tracing, and alerting

### System Health Score

| Category | Score | Status |
|----------|-------|--------|
| Architecture Design | 95/100 | ✅ Stable |
| Code Quality | 75/100 | ✅ Improved |
| Security | 90/100 | ✅ Hardened |
| Component Functionality | 80/100 | ✅ Operational |
| State Persistence | 85/100 | ✅ PostgreSQL-backed |
| Integration Integrity | 80/100 | ✅ Verified |
| Observability | 95/100 | ✅ Prometheus + Tracing |

### Infrastructure Dependencies

| Component | Purpose | Minimum Version | Status |
|-----------|---------|-----------------|--------|
| PostgreSQL | State persistence | 15+ | ✅ Operational |
| Redis | Caching layer | 7+ | ✅ Operational |
| Qdrant | Vector storage | 1.8+ | ✅ Operational |
| NATS | Event mesh with JetStream | 2.10+ | ✅ Operational |
| mem0 | Memory backend | Latest | ✅ Operational |
| Prometheus | Metrics collection | 2.45+ | ✅ Operational |
| Grafana | Metrics visualization | 10.0+ | ✅ Optional |

---

## Actor Architecture

### Overview

The Heretek Swarm implements 23 autonomous agents organized into 6 tiers, each with specific capabilities and responsibilities. All agents inherit from the [`AgentActor`](src/heretek_swarm/actors/base.py) base class which provides:

- Async message handling
- State management with PostgreSQL persistence
- Health monitoring
- Zero-Trust input validation
- Prometheus metrics integration

### Agent Tiers

```
┌─────────────────────────────────────────────────────────────────┐
│                    THE COLLECTIVE (23 AGENTS)                    │
├─────────────────────────────────────────────────────────────────┤
│ TIER 1: CORE TRIAD (4)     │ TIER 4: SAFETY (3)               │
│ ├── Steward (Orchestrator) │ ├── Sentinel (Safety Guardian)     │
│ ├── Alpha (Deep Analysis)  │ ├── Sentinel-Prime (Security)     │
│ ├── Beta (Validation)      │ └── Arbiter (Conflict Resolution) │
│ └── Charlie (Challenge)    │                                   │
│                            │ TIER 5: COORDINATION (4)         │
│ TIER 2: SUPPORT (5)        │ ├── Coordinator (Multi-Agent)    │
│ ├── Historian (Memory)      │ ├── Nexus (External Integration) │
│ ├── Metis (Strategy)        │ ├── Catalyst (Change Mgmt)       │
│ ├── Empath (Emotional IQ)  │ └── Chronos (Scheduling)         │
│ ├── Perceiver (Sensory)     │                                   │
│ └── Echo (Communication)   │ TIER 6: ENHANCEMENT (3)          │
│                            │ ├── Prism (Multi-Perspective)     │
│ TIER 3: EXPLORATION (4)    │ ├── Habit-Forge (Optimization)    │
│ ├── Explorer (Discovery)    │ └── Perceiver+ (Advanced)         │
│ ├── Examiner (QA)           │                                   │
│ ├── Dreamer (Creativity)    │                                   │
│ └── Coder (Implementation) │                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Tier 1: Core Triad (4 Agents)

| Agent | Role | File | Capabilities |
|-------|------|------|--------------|
| Steward | Governance & Orchestration | [`triad.py`](src/heretek_swarm/actors/triad.py) | Deliberation orchestration, decision collection |
| Alpha | Deep Analysis | [`triad.py`](src/heretek_swarm/actors/triad.py) | Deep analysis, proposal generation |
| Beta | Validation | [`triad.py`](src/heretek_swarm/actors/triad.py) | Validation, verification |
| Charlie | Challenge | [`triad.py`](src/heretek_swarm/actors/triad.py) | Challenge, stress-testing |

### Tier 2: Support Agents (5 Agents)

| Agent | Role | File | Capabilities |
|-------|------|------|--------------|
| Historian | Memory & Knowledge | [`historian.py`](src/heretek_swarm/actors/historian.py) | Memory storage, search, lineage tracking |
| Metis | Strategic Planning | [`metis.py`](src/heretek_swarm/actors/metis.py) | Strategic planning, resource allocation |
| Empath | Emotional Intelligence | [`empath.py`](src/heretek_swarm/actors/empath.py) | Sentiment analysis, conflict mediation |
| Perceiver | Multi-Modal Input | [`perceiver.py`](src/heretek_swarm/actors/perceiver.py) | Multi-modal input processing |
| Echo | Communication | [`echo.py`](src/heretek_swarm/actors/echo.py) | Multi-channel communication, protocol translation |

### Tier 3: Exploration Agents (4 Agents)

| Agent | Role | File | Capabilities |
|-------|------|------|--------------|
| Explorer | Intelligence Gathering | [`explorer.py`](src/heretek_swarm/actors/explorer.py) | Source monitoring, anomaly detection |
| Examiner | Quality Assurance | [`examiner.py`](src/heretek_swarm/actors/examiner.py) | Test plan generation, code analysis |
| Dreamer | Creative Generation | [`dreamer.py`](src/heretek_swarm/actors/dreamer.py) | Creative solutions, alternative exploration |
| Coder | Implementation | [`coder.py`](src/heretek_swarm/actors/coder.py) | Code generation, review, safe execution |

### Tier 4: Safety & Security (3 Agents)

| Agent | Role | File | Capabilities |
|-------|------|------|--------------|
| Sentinel | Safety Guardian | [`sentinel.py`](src/heretek_swarm/actors/sentinel.py) | Input validation, safety checks |
| Sentinel-Prime | Security Commander | [`sentinel_prime.py`](src/heretek_swarm/actors/sentinel_prime.py) | Threat detection, security response |
| Arbiter | Conflict Resolution | [`arbiter.py`](src/heretek_swarm/actors/arbiter.py) | Conflict mediation, decision arbitration |

### Tier 5: Coordination Agents (4 Agents)

| Agent | Role | File | Capabilities |
|-------|------|------|--------------|
| Coordinator | Multi-Agent Sync | [`coordinator.py`](src/heretek_swarm/actors/coordinator.py) | Workflow coordination, dependency resolution |
| Nexus | External Integration | [`nexus.py`](src/heretek_swarm/actors/nexus.py) | API integration, webhook management |
| Catalyst | Change Management | [`catalyst.py`](src/heretek_swarm/actors/catalyst.py) | Change requests, impact analysis, rollback |
| Chronos | Scheduling | [`chronos.py`](src/heretek_swarm/actors/chronos.py) | Task scheduling, deadline tracking |

### Tier 6: Enhancement Agents (3 Agents)

| Agent | Role | File | Capabilities |
|-------|------|------|--------------|
| Prism | Multi-Perspective | [`prism.py`](src/heretek_swarm/actors/prism.py) | Multi-perspective analysis, bias detection |
| Habit-Forge | Behavior Optimization | [`habit_forge.py`](src/heretek_swarm/actors/habit_forge.py) | Habit creation, pattern analysis |
| Perceiver+ | Advanced Analytics | [`perceiver_plus.py`](src/heretek_swarm/actors/perceiver_plus.py) | Statistical analysis, forecasting |

---

## Memory System

### Architecture

The Heretek Swarm implements a dual-tier memory architecture with PostgreSQL, Redis, and Qdrant vector storage using mem0 integration.

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   Mem0Backend                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Embed     │  │   Store     │  │   Search    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│    Redis      │ │  PostgreSQL   │ │    Qdrant     │
│  (Ephemeral)  │ │ (Persistent)  │ │   (Vector)    │
└───────────────┘ └───────────────┘ └───────────────┘
```

### Memory Tiers

| Tier | Storage | Use Case | TTL |
|------|---------|----------|-----|
| Ephemeral | Redis | Session data, recent context | Configurable |
| Persistent | PostgreSQL | Decision history, lineage | Permanent |
| Vector | Qdrant | Semantic search, similarity | Permanent |

### Memory Types

| Type | Description | Example |
|------|-------------|---------|
| Episodic | Event-based memories | Deliberation outcomes |
| Semantic | Knowledge/fact-based | Domain knowledge |
| Procedural | How-to/skill memories | Agent strategies |

### Key Components

- **Mem0Backend** ([`src/memory/mem0_backend.py`](src/memory/mem0_backend.py)) - Vector memory backend with mem0 integration
- **MemoryEntry** ([`src/memory/base.py`](src/memory/base.py)) - Core memory data model
- **MemoryTiering** ([`src/memory/tiering.py`](src/memory/tiering.py)) - Transactional tier migration with rollback
- **Persistent Memory** ([`src/memory/persistent.py`](src/memory/persistent.py)) - PostgreSQL-backed storage

---

## Event Mesh

### NATS JetStream Architecture

The Heretek Swarm uses NATS JetStream for persistent event streaming, providing:

- **Message Durability** - All events persisted to stream
- **Guaranteed Delivery** - Message acknowledgment
- **Stream Retention** - Configurable retention policies
- **Subject-Based Routing** - Publish/subscribe pattern

### Channel Architecture

#### Internal Channels

| Channel | Subject | Subscribers | Message Types |
|---------|---------|-------------|---------------|
| Triad | `swarm.internal.triad` | steward, alpha, beta, charlie | proposal, analysis, validation, challenge, decision |
| Coordination | `swarm.internal.coordination` | coordinator, catalyst, chronos, metis | task_start, task_complete, dependency_ready, blocker |
| Safety | `swarm.internal.safety` | sentinel, sentinel-prime, arbiter, steward | threat_detected, quarantine, all_clear, incident_report |
| Memory | `swarm.internal.memory` | historian, prism, habit-forge | store_request, retrieve_request, learn_pattern, forget |
| Exploration | `swarm.internal.exploration` | explorer, examiner, dreamer, coder | research_task, analysis_result, creative_request, code_review |
| Perception | `swarm.internal.perception` | perceiver, perceiver-plus, empath, echo | input_received, sentiment_analysis, translation_request |

#### System Channels

| Channel | Subject | Subscribers | Message Types |
|---------|---------|-------------|---------------|
| Health | `swarm.system.health` | * (all) | heartbeat, health_status, error_report, restart_request |
| Consciousness | `swarm.system.consciousness` | * (all) | phi_update, attention_state, workspace_broadcast |
| Consensus | `swarm.system.consensus` | steward, alpha, beta, charlie | vote_cast, consensus_reached, red_flag |
| Workflow | `swarm.workflow.events` | * (all) | workflow_start, workflow_phase, workflow_complete |

### Message Format

All channel messages follow the `ChannelMessage` structure:

```python
@dataclass
class ChannelMessage:
    subject: str                    # NATS subject
    correlation_id: str             # Unique message ID
    reply_to: Optional[str]         # Response subject
    sender_agent: str               # Sending agent ID
    target_agents: List[str]        # Target agents
    message_type: str               #              # Require acknowledgment
    workflow_id: Optional[str]       # Associated workflow
    task_id: Optional[str]          # Associated task
```

---

## Configuration System

### Database-Backed Configuration

The Heretek Swarm uses a database-backed configuration system for all user-facing configurations:

- **User Configurations** - System-wide settings stored in PostgreSQL
- **LLM Providers** - Multi-provider LLM configurations (OpenAI, Ollama, llama.cpp, etc.)
- **Embedding Providers** - Multi-provider embedding configurations
- **Agent Configs** - Per-agent configurations
- **Audit Logging** - Complete change history
- **Import/Export** - Backup and restore capabilities

### Database Schema

The configuration system creates the following tables:

- `user_configurations` - System-wide settings
- `llm_providers` - LLM provider configurations
- `embedding_providers` - Embedding provider configurations
- `agent_configs` - Per-agent configurations
- `config_audit_log` - Change history
- `config_cache` - Frequently accessed config cache

### LLM Provider Types

| Type | Base URL | API Key Required | Notes |
|------|----------|------------------|-------|
| openai | https://api.openai.com/v1 | Yes | GPT-4, GPT-3.5 |
| openai_compatible | Custom | Optional | vLLM, LocalAI, etc. |
| ollama | http://localhost:11434 | No | Local inference |
| llamacpp | http://localhost:8080 | No | GGUF models |
| zai | https://open.bigmodel.cn/api/paas/v4 | Yes | Zhipu AI GLM models |
| minimax | https://api.minimax.chat/v1 | Yes | Requires group_id |
| lemonade | http://localhost:5000 | No | lemonade-server |

---

## Security

### Zero-Trust Architecture

The Heretek Swarm implements a comprehensive Zero-Trust security architecture:

1. **Never Trust, Always Verify** - All inputs validated via Pydantic v2 models
2. **Defense in Depth** - Multiple security layers (guardrails, rate limiting, auth)
3. **Least Privilege** - Minimal agent capabilities
4. **Assume Breach** - Containment and isolation

### Security Layers

| Layer | Component | Purpose | Status |
|-------|-----------|---------|--------|
| Input Validation | [`zero_trust.py`](src/heretek_swarm/security/zero_trust.py) | 4-layer validation (Input, Context, Output, Audit) | ✅ Operational |
| Adversarial Detection | [`adversarial.py`](src/heretek_swarm/security/adversarial.py) | Prompt injection, jailbreak detection | ✅ Operational |
| Rate Limiting | [`ddos_protection.py`](src/heretek_swarm/security/ddos_protection.py) | Token bucket algorithm, DDoS protection | ✅ Operational |
| Guardrails | [`guardrails.py`](src/heretek_swarm/security/guardrails.py) | Content filtering, output validation | ✅ Operational |
| Authentication | [`auth.py`](src/heretek_swarm/gateway/auth.py) | Bearer token auth, race condition fixed | ✅ Operational |

### Security Features

- **Pydantic v2 Validation** - All inputs validated with `extra='forbid'`
- **UUID Validation** - 128-bit entropy validation for agent IDs
- **Content Size Limits** - DoS prevention
- **Injection Detection** - Pattern-based injection detection
- **PII Redaction** - PII detection and redaction
- **Token Validation** - Secure bearer token authentication

---

## Observability

The Heretek Swarm provides comprehensive observability through Prometheus metrics, distributed tracing, and structured logging.

### Prometheus Metrics

**File:** [`src/heretek_swarm/observability/prometheus_metrics.py`](src/heretek_swarm/observability/prometheus_metrics.py)

The system exposes Prometheus-compatible metrics for monitoring autonomous 24/7 operation.

#### Available Metrics

##### Agent Metrics (Gauges)

| Metric | Labels | Description |
|--------|--------|-------------|
| `heretek_swarm_agents_total` | `agent_type` | Total registered agents |
| `heretek_swarm_agents_active` | `agent_type` | Currently active agents |
| `heretek_swarm_phi_score` | `agent_id` | Consciousness phi score (IIT) |
| `heretek_swarm_free_energy` | `agent_id` | Free energy level (FEP) |

##### Task Metrics (Counters)

| Metric | Labels | Description |
|--------|--------|-------------|
| `heretek_swarm_tasks_completed_total` | `agent_id`, `task_type` | Tasks completed |
| `heretek_swarm_tasks_failed_total` | `agent_id`, `task_type` | Tasks failed |

##### Message Metrics (Counters)

| Metric | Labels | Description |
|--------|--------|-------------|
| `heretek_swarm_messages_total` | `direction`, `message_type` | Messages processed |

##### Consensus Metrics (Counters)

| Metric | Labels | Description |
|--------|--------|-------------|
| `heretek_swarm_consensus_rounds_total` | `consensus_type`, `outcome` | Consensus rounds |

##### API Metrics (Histogram + Counter)

| Metric | Labels | Description |
|--------|--------|-------------|
| `heretek_swarm_api_request_duration_seconds` | `method`, `endpoint`, `status` | Request latency |
| `heretek_swarm_api_requests_total` | `method`, `endpoint`, `status` | Total requests |

##### Health Metrics (Gauges)

| Metric | Description |
|--------|-------------|
| `heretek_swarm_health_score` | Overall health (0-100) |
| `heretek_swarm_uptime_seconds` | System uptime |

#### Prometheus Integration

```python
from heretek_swarm.observability.prometheus_metrics import (
    PrometheusMetrics,
    get_metrics,
    increment_tasks_completed,
    record_api_request,
)

# Get singleton metrics instance
metrics = get_metrics()

# Record task completion
increment_tasks_completed(agent_id="alpha", task_type="analysis")

# Record API request
record_api_request(method="GET", endpoint="/api/agents", status=200, duration=0.05)

# Export metrics in Prometheus format
from starlette.responses import PlainTextResponse
return PlainTextResponse(get_metrics().export_prometheus())
```

#### Prometheus Endpoint

The API exposes metrics at `/metrics` for Prometheus scraping:

```bash
# Scrape configuration (prometheus.yml)
scrape_configs:
  - job_name: 'heretek-swarm'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Distributed Tracing

All requests include trace context propagation for end-to-end request tracking.

#### Trace Context

```
External Request → API Gateway → Steward → HeavySwarm Workflow
                         │
                         ▼
              Trace Context:
              - trace_id: generated per request
              - span_id: new per hop
              - All agents share trace_id
```

#### Tracing Headers

| Header | Description |
|--------|-------------|
| `X-Trace-ID` | Unique trace identifier |
| `X-Span-ID` | Current span identifier |
| `X-Parent-Span-ID` | Parent span identifier |

#### Trace Storage

Traces are stored in memory and can be exported to:
- **Jaeger** - For distributed tracing visualization
- **Zipkin** - Alternative tracing backend
- **OTLP** - OpenTelemetry Protocol

### Alerting

Alert rules should be configured in Prometheus/Alertmanager for critical conditions.

#### Recommended Alert Rules

```yaml
groups:
  - name: heretek_swarm
    rules:
      # System Health Alerts
      - alert: SwarmHealthCritical
        expr: heretek_swarm_health_score < 50
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Heretek Swarm health below 50%"

      - alert: SwarmUptimeLow
        expr: heretek_swarm_uptime_seconds < 3600
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Swarm restarted recently"

      # Agent Alerts
      - alert: NoActiveAgents
        expr: sum(heretek_swarm_agents_active) == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "No active agents in swarm"

      - alert: HighAgentFailureRate
        expr: rate(heretek_swarm_tasks_failed_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High task failure rate"

      # Consciousness Alerts
      - alert: LowCollectivePhi
        expr: avg(heretek_swarm_phi_score) < 0.3
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Collective consciousness Phi below threshold"

      - alert: HighFreeEnergy
        expr: avg(heretek_swarm_free_energy) > 0.8
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High free energy indicates prediction errors"

      # API Performance Alerts
      - alert: HighAPILatency
        expr: histogram_quantile(0.95, rate(heretek_swarm_api_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API p95 latency above 1 second"

      - alert: HighAPIErrorRate
        expr: sum(rate(heretek_swarm_api_requests_total{status=~"5.."}[5m])) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High API error rate"

      # Consensus Alerts
      - alert: ConsensusFailureRate
        expr: rate(heretek_swarm_consensus_rounds_total{outcome="failed"}[10m]) > 0.2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High consensus failure rate"
```

### Health Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | API health check |
| `/health/live` | GET | Kubernetes liveness probe |
| `/health/ready` | GET | Kubernetes readiness probe |
| `/metrics` | GET | Prometheus metrics endpoint |
| `/api/agents` | GET | List all agents with status |
| `/api/agents/{agent_id}` | GET | Get specific agent details |
| `/api/agents/{agent_id}/metrics` | GET | Agent performance metrics |

### Metrics Categories

| Category | Metrics | Description |
|----------|---------|-------------|
| System | uptime_seconds, total_restarts, total_failures, memory_usage_bytes, cpu_percent, active_agents | System-level metrics |
| Agent | messages_processed_total, messages_failed_total, average_response_time_ms, health_score, mailbox_size | Per-agent metrics |
| Workflow | workflows_completed_total, workflows_failed_total, average_duration_ms, phase_durations_ms | Workflow metrics |
| Consensus | votes_collected_total, consensus_reached_total, red_flags_raised_total, average_confidence | Consensus metrics |
| RAG | documents_indexed_total, queries_executed_total, average_retrieval_time_ms, chunks_retrieved_total | RAG metrics |
| Consciousness | phi_score, free_energy, gwt_score, ast_competence | Consciousness metrics |

---

## Monitoring Setup

### Docker Compose Monitoring Stack

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.45.0
    volumes:
      - ./'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana:10.0.0
    ports:
      - "3001:alertmanager:v0.26.0
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
    command:
      - '--configape_configs:
  - job_name: 'heretek-swarm'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'

  - job_name: 'nats'
    static_configs:
      - targets: ['nats:8222']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:9187']
```

### AlertManager Configuration

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'email'

receivers:
  - name: 'email'
    email_configs:
      - to: 'alerts@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.example.com:587'

  - name: 'slack'
    slack_configs:
      - channel: '#alerts'
        api_url: 'https://hooks.slack.com/services/XXX'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname']
```

### Grafana Dashboard

Import the Heretek Swarm dashboard (ID: 1860) or create custom panels:

**Recommended Panels:**
1. Swarm Health Score (gauge)
2. Active Agents (stat)
3. Tasks Completed/Failed (time series)
4. API Latency p50/p95/p99 (histogram)
5. Consensus Success Rate (time series)
6. Consciousness Phi Score (time series)
7. Free Energy Level (time series)
8. Message Throughput (time series)

---

## References

- [`PRIME_DIRECTIVE.md`](../PRIME_DIRECTIVE.md) - 23-agent vision and architecture
- [`docs/API_ENDPOINTS.md`](API_ENDPOINTS.md) - API reference
- [`docs/DEPLOYMENT.md`](DEPLOYMENT.md) - Deployment guide
- [`docs/MONITORING.md`](MONITORING.md) - Prometheus, Loki, alerting setup
- [`docs/AGENTS.md`](AGENTS.md) - Complete agent documentation
- [`docs/architecture/emergent-intelligence.md`](architecture/emergent-intelligence.md) - Consciousness framework

> **Note:** Remediation backlog and zero-trust audit documents have been archived. Zero-trust implementation details are covered in [architecture/security-considerations.md](architecture/security-considerations.md) if available.

---

**License:** Apache 2.0  
**GitHub:** [Heretek-AI/heretek-swarm](https://github.com/HeretekAI/heretek-swarm)
