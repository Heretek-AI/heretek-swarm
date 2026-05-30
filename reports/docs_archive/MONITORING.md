# Monitoring Guide

**Version:** 2.0.0  
**Date:** 2026-04-10  
**Status:** Production-Ready

Comprehensive guide for setting up Prometheus, Grafana, Loki, and alerting for Heretek Swarm.

---

## Table of Contents

1. [Overview](#overview)
2. [Prometheus Setup](#prometheus-setup)
3. [Grafana Setup](#grafana-setup)
4. [AlertManager Setup](#alertmanager-setup)
5. [Log Aggregation (Loki)](#log-aggregation-loki)
6. [Docker Compose Stack](#docker-compose-stack)
7. [Kubernetes Deployment](#kubernetes-deployment)
8. [Alert Rules](#alert-rules)
9. [Dashboard Panels](#dashboard-panels)

---

## Overview

The Heretek Swarm exposes comprehensive metrics via Prometheus. The monitoring stack consists of:

| Component | Purpose | Default Port |
|-----------|---------|--------------|
| Prometheus | Metrics collection and storage | 9090 |
| Grafana | Metrics visualization and dashboards | 3001 |
| AlertManager | Alert routing and notification | 9093 |
| Loki | Log aggregation | 3100 |

### Metrics Endpoint

The API exposes metrics at `/metrics`:

```
curl http://localhost:8000/metrics
```

---

## Prometheus Setup

### Installation

```bash
# Download Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xzf prometheus-2.45.0.linux-amd64.tar.gz
cd prometheus-2.45.0.linux-amd64
```

### Configuration

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

rule_files:
  - "alert_rules.yml"

scrape_configs:
  # Heretek Swarm API
  - job_name: 'heretek-swarm'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  # NATS monitoring
  - job_name: 'nats'
    static_configs:
      - targets: ['nats:8222']
    metrics_path: '/metrics'

  # PostgreSQL exporter
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # Redis exporter
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Running Prometheus

```bash
./prometheus --config.file=prometheus.yml --storage.tsdb.path=data/
```

---

## Grafana Setup

### Installation

```bash
# Download Grafana
wget https://dl.grafana.com/oss/release/grafana-10.0.0.linux-amd64.tar.gz
tar xzf grafana-10.0.0.linux-amd64.tar.gz
cd grafana-10.0.0
```

### Running Grafana

```bash
./bin/grafana-server
```

### Data Source Configuration

1. Navigate to http://localhost:3001 (admin/admin)
2. Go to **Configuration** → **Data Sources**
3. Add **Prometheus**:
   - URL: `http://prometheus:9090`
4. Add **Loki**:
   - URL: `http://loki:3100`

### Provisioning (Recommended)

Create `grafana/provisioning/datasources/datasources.yml`:

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
```

---

## AlertManager Setup

### Configuration

Create `alertmanager.yml`:

```yaml
global:
  resolve_timeout: 5m
  smtp_smarthost: 'smtp.example.com:587'
  smtp_from: 'alertmanager@example.com'
  smtp_auth_username: 'alertmanager'
  smtp_auth_password: 'password'

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'email'
  routes:
    - match:
        severity: critical
      receiver: 'email'
      continue: true
    - match:
        severity: warning
      receiver: 'slack'

receivers:
  - name: 'email'
    email_configs:
      - to: 'alerts@example.com'
        send_resolved: true

  - name: 'slack'
    slack_configs:
      - channel: '#alerts'
        api_url: 'https://hooks.slack.com/services/XXX/YYY/ZZZ'
        send_resolved: true

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_SERVICE_KEY'
        severity: critical
        send_resolved: true

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname']
```

### Running AlertManager

```bash
./alertmanager --config.file=alertmanager.yml
```

---

## Log Aggregation (Loki)

### Promtail Configuration

Create `promtail.yml`:

```yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: heretek-swarm
    static_configs:
      - targets:
          - localhost
        labels:
          job: heretek-swarm
          __path__: /var/log/heretek-swarm/*.log

  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    relabel_configs:
      - source_labels: [__meta_docker_container_name]
        regex: 'heretek-.*'
        target_label: container
```

### Loki Configuration

Create `loki.yml`:

```yaml
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

common:
  path_prefix: /loki
  storage_dir: /data
  replication_factor: 1
  ring:
    instance_addr: 127.0.0.1
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2023-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /data/index
    cache_location: /data/index_cache
    shared_store: filesystem
  filesystem:
    directory: /data/chunks

limits_config:
  reject_old_samples: true
  reject_old_samples_max_age: 168h
```

---

## Docker Compose Stack

### Complete Monitoring Stack

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.45.0
    volumes:
      - ./prometheus '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
    ports:
      - "9090:9090"
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:10.0.0
    volumes:
      - ./grafana/provisioning:/etc/g_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "3001:3000"
    networks:
      - monitoring
    depends_on:
      - prometheus

  alert    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    ports:
      - "9093:9093"
    networks:
      - monitoring

  lok    command: -config.file=/etc/loki/loki.yml
    ports:
      - "3100:3100"
    networks:
      - monitoring

  promtail:
    image: grafana/promtail:2.8.0
    volumes:
      - ./promtail.yml:/etc/promtail/promtail.yml
      - /var/log:/var/log
    command: -config.file=/etc/promtail/promtail.yml
    networks# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# View logs
docker-compose -f docker-compose.monitoring.yml logs -f

# Stop monitoring stack
docker-compose -f docker-compose.monitoring.yml down
```

---

## Kubernetes Deployment

### Prometheus Operator

```yaml
# prometheus-operator.yaml
apiVersion: monitoring.coreos.com/v1
Name: prometheus
  serviceMonitorSelector:
    matchLabels:
      app: heretek-swarm
  ruleSelector:
    matchLabels:
      app: heretek-swarm
  alerting:
    alertmanagers:
      - namespaceetek-swarm
  labels:
    app: heretek-swarm
spec:
  selector:
    matchLabels:
      app: heretek-swarm
  endpoints:
    - port: metrics
      path: /metrics
      interval: 10s
```

---

## Alert Rules

### Critical Alerts

```yaml
# alert_rules.yml
groups:
  - name: heretek_swarm_critical
    rules:
      - alert: SwarmHealthCritical
        expr: heretek_swarm_health_score < 50
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Heretek Swarm health below 50%"
          description: "Current health: {{ $value }}"

      - alert: NoActiveAgents
        expr: sum(heretek_swarm_agents_active) == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "No active agents in swarm"

      - alert: SwarmDown
        expr: up{job="heretek-swarm"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Heretek Swarm API is down"

      - alert: HighAPIErrorRate
        expr: |
          sum(rate(heretek_swarm_api_requests_total{status=~"5.."}[5m]))
          / sum(rate(heretek_swarm_api_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "API error rate above 5%"
```

### Warning Alerts

```yaml
  - name: heretek_swarm_warning
    rules:
      - alert: LowCollectivePhi
        expr: avg(heretek_swarm_phi_score) < 0.3
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Collective consciousness Phi below threshold"
          description: "Average Phi: {{ $value }}"

      - alert: HighFreeEnergy
        expr: avg(heretek_swarm_free_energy) > 0.8
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High free energy indicates prediction errors"

      - alert: HighAgentFailureRate
        expr: |
          rate(heretek_swarm_tasks_failed_total[5m])
          / rate(heretek_swarm_tasks_completed_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Task failure rate above 10%"

      - alert: HighAPILatency
        expr: |
          histogram_quantile(0.95,
            rate(heretek_swarm_api_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API p95 latency above 1 second"

      - alert: ConsensusFailureRate
        expr: |
          rate(heretek_swarm_consensus_rounds_total{outcome="failed"}[10m])
          / rate(heretek_swarm_consensus_rounds_total[10m]) > 0.2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Consensus failure rate above 20%"

      - alert: SwarmUptimeLow
        expr: heretek_swarm_uptime_seconds < 3600
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Swarm restarted recently"
```

---

## Dashboard Panels

### Swarm Overview Dashboard

**Panel 1: Swarm Health Score**
```promql
heretek_swarm_health_score
```
- Type: Gauge
- Thresholds: 50 (red), 75 (yellow), 90 (green)

**Panel 2: Active Agents**
```promql
sum(heretek_swarm_agents_active) by (agent_type)
```
- Type: Stat
- Visualization: Time series

**Panel 3: Tasks Completed/Failed**
```promql
rate(heretek_swarm_tasks_completed_total[5m])
rate(heretek_swarm_tasks_failed_total[5m])
```
- Type: Time series (stacked)
- Colors: Success (green), Failed (red)

**Panel 4: API Latency**
```promql
histogram_quantile(0.50, rate(heretek_swarm_api_request_duration_seconds_bucket[5m]))
histogram_quantile(0.95, rate(heretek_swarm_api_request_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(heretek_swarm_api_request_duration_seconds_bucket[5m]))
```
- Type: Time series
- Legend: p50, p95, p99

### Consciousness Dashboard

**Panel 1: Collective Phi Score**
```promql
avg(heretek_swarm_phi_score) by (agent_id)
```
- Type: Time series
- Thresholds: 0.3 (red), 0.5 (yellow), 0.7 (green)

**Panel 2: Free Energy Level**
```promql
avg(heretek_swarm_free_energy) by (agent_id)
```
- Type: Time series
- Thresholds: 0.8 (red), 0.5 (yellow), 0.3 (green)

**Panel 3: Consensus Success Rate**
```promql
sum(rate(heretek_swarm_consensus_rounds_total{outcome="success"}[5m]))
/
sum(rate(heretek_swarm_consensus_rounds_total[5m]))
```
- Type: Time series
- Unit: Percent (0-100)

### Agent Performance Dashboard

**Panel 1: Messages Processed**
```promql
rate(heretek_swarm_messages_total{direction="incoming"}[5m])
```
- Type: Time series
- Group by: agent_id

**Panel 2: Task Breakdown by Agent**
```promql
sum(rate(heretek_swarm_tasks_completed_total[5m])) by (agent_id, task_type)
```
- Type: Time series (stacked)

---

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [Emergent Intelligence](../architecture/emergent-intelligence.md) - Consciousness framework
- [Prometheus Getting Started](https://prometheus.io/docs/prometheus/latest/getting_started/)
- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)
- [AlertManager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)

---

**License:** Apache 2.0
