# Prometheus Metrics Documentation

## Overview

Heretek Swarm includes Prometheus metrics support for autonomous 24/7 operation monitoring. This enables integration with Prometheus-based monitoring systems, alerting, and visualization tools like Grafana.

## Architecture

```
┌─────────────────┐      /metrics       ┌─────────────┐
│  Heretek Swarm  │ ──────────────────► │ Prometheus  │
│  (FastAPI App)   │   scrape (15s)    │   Server    │
└─────────────────┘                     └──────┬──────┘
                                              │
                                              ▼
                                       ┌─────────────┐
                                       │   Grafana   │
                                       │  Dashboard  │
                                       └─────────────┘
```

## Available Metrics

### Agent Metrics (Gauges)

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `heretek_swarm_agents_total` | Gauge | Total registered agents | `agent_type` |
| `heretek_swarm_agents_active` | Gauge | Currently active agents | `agent_type` |
| `heretek_swarm_phi_score` | Gauge | Consciousness phi score (IIT) | `agent_id` |
| `heretek_swarm_free_energy` | Gauge | Free energy level (FEP) | `agent_id` |

### Task Metrics (Counters)

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `heretek_swarm_tasks_completed_total` | Counter | Tasks completed | `agent_id`, `task_type` |
| `heretek_swarm_tasks_failed_total` | Counter | Tasks failed | `agent_id`, `task_type` |

### Message Metrics (Counters)

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `heretek_swarm_messages_total` | Counter | Messages processed | `direction`, `message_type` |

### Consensus Metrics (Counters)

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `heretek_swarm_consensus_rounds_total` | Counter | Consensus rounds | `consensus_type`, `outcome` |

### API Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `heretek_swarm_api_request_duration_seconds` | Histogram | Request latency | `method`, `endpoint`, `status` |
| `heretek_swarm_api_requests_total` | Counter | Total requests | `method`, `endpoint`, `status` |

### Health Metrics (Gauges)

| Metric | Type | Description |
|--------|------|-------------|
| `heretek_swarm_health_score` | Gauge | Overall swarm health (0-100) |
| `heretek_swarm_uptime_seconds` | Gauge | Swarm uptime in seconds |

## Endpoints

### GET /metrics

Prometheus text format metrics endpoint. This is the primary endpoint for Prometheus scraping.

**Response:** `text/plain` (Prometheus exposition format)

```bash
curl http://localhost:8000/metrics
```

Example output:
```promql
# HELP heretek_swarm_agents_total Total number of registered agents
# TYPE heretek_swarm_agents_total gauge
heretek_swarm_agents_total{agent_type="executor"} 5

# HELP heretek_swarm_tasks_completed_total Total tasks completed
# TYPE heretek_swarm_tasks_completed_total counter
heretek_swarm_tasks_completed_total{agent_id="agent_1",task_type="analysis"} 42

# HELP heretek_swarm_api_request_duration_seconds API request latency
# TYPE heretek_swarm_api_request_duration_seconds histogram
heretek_swarm_api_request_duration_seconds_bucket{method="GET",endpoint="/api/agents",status="200",le="0.1"} 42
```

### GET /metrics/json

JSON format metrics for debugging and monitoring dashboards.

```bash
curl http://localhost:8000/metrics/json
```

## Quick Start

### 1. Run with Docker Compose

```bash
# Start Heretek Swarm with Prometheus monitoring
docker-compose -f docker-compose.yml -f docker-compose.autonomous.yml --profile monitoring up -d

# Access Grafana dashboard
open http://localhost:3001
# Default credentials: admin / admin
```

### 2. Manual Prometheus Setup

1. Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'heretek-swarm'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

2. Start Prometheus:

```bash
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

3. Verify metrics:

```bash
curl http://localhost:9090/api/v1/query?query=heretek_swarm_agents_total
```

## Integration with Existing Code

### Recording Metrics

```python
from heretek_swarm.observability.prometheus_metrics import (
    increment_tasks_completed,
    increment_tasks_failed,
    record_api_request,
    set_phi_score,
    set_free_energy,
)

# Record task completion
increment_tasks_completed(agent_id="agent_1", task_type="analysis")

# Record task failure
increment_tasks_failed(agent_id="agent_1", task_type="analysis")

# Record consciousness metrics
set_phi_score("agent_1", 0.85)
set_free_energy("agent_1", 0.12)

# API requests are automatically recorded via middleware
```

### Direct Metrics Instance

```python
from heretek_swarm.observability.prometheus_metrics import get_metrics

metrics = get_metrics()

# Record various metrics
metrics.record_agent_registration("agent_1", "executor")
metrics.record_agent_active("agent_1", "executor")
metrics.record_task_completed("agent_1", "executor", "analysis")
metrics.record_message_sent("a2a")
metrics.record_consensus_round("deliberation", "success")

# Export for Prometheus
output = metrics.export_prometheus()
```

## Alerting Examples

Add these to your Prometheus alerting rules:

```yaml
groups:
  - name: heretek-swarm
    rules:
      # Alert if no agents are active
      - alert: NoActiveAgents
        expr: heretek_swarm_agents_active == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "No active agents in Heretek Swarm"

      # Alert if health score is low
      - alert: LowHealthScore
        expr: heretek_swarm_health_score < 50
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Heretek Swarm health score is low"

      # Alert on high task failure rate
      - alert: HighTaskFailureRate
        expr: rate(heretek_swarm_tasks_failed_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High task failure rate detected"

      # Alert on low consciousness
      - alert: LowConsciousness
        expr: heretek_swarm_phi_score < 0.3
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Consciousness phi score is below threshold"
```

## Grafana Dashboard

Example Grafana queries for Heretek Swarm:

### Swarm Overview
```promql
# Total agents
sum(heretek_swarm_agents_total)

# Active agents percentage
sum(heretek_swarm_agents_active) / sum(heretek_swarm_agents_total) * 100
```

### Task Performance
```promql
# Tasks completed rate
rate(heretek_swarm_tasks_completed_total[5m])

# Task failure rate
rate(heretek_swarm_tasks_failed_total[5m])
```

### API Performance
```promql
# Request rate
sum(rate(heretek_swarm_api_requests_total[5m]))

# P95 latency
histogram_quantile(0.95, rate(heretek_swarm_api_request_duration_seconds_bucket[5m]))
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROMETHEUS_ENABLED` | Enable Prometheus metrics | `true` |
| `PROMETHEUS_PORT` | Metrics port | `8000` |

### Docker Labels

Heretek Swarm includes Docker labels for automatic service discovery:

```yaml
labels:
  - "prometheus.io/scrape=true"
  - "prometheus.io/port=8000"
  - "prometheus.io/path=/metrics"
```

## Troubleshooting

### Metrics not appearing

1. Check if the metrics endpoint is accessible:
   ```bash
   curl http://localhost:8000/metrics
   ```

2. Verify Prometheus is configured correctly:
   ```bash
   # Check Prometheus targets
   curl http://localhost:9090/api/v1/targets
   ```

3. Check for errors in the Heretek Swarm logs:
   ```bash
   docker logs heretek-swarm-autonomous | grep -i prometheus
   ```

### High cardinality metrics

If you see high cardinality issues, the metrics automatically normalize endpoints:
- UUIDs are replaced with `{id}`
- Numeric IDs are replaced with `{id}`

For more control, use the `_normalize_endpoint` method in `PrometheusMetrics`.

## Files

- **Metrics Module:** `backend/heretek_swarm/observability/prometheus_metrics.py`
- **API Endpoint:** `backend/heretek_swarm/api/metrics.py`
- **Configuration:** `prometheus/prometheus.yml`
- **Middleware:** Automatically records all API requests

## See Also

- [Prometheus Exposition Format](https://prometheus.io/docs/instrumenting/exposition_formats/)
- [Prometheus Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboarding](https://grafana.com/docs/grafana/latest/dashboards/)
