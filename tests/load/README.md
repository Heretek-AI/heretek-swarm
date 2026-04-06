# Heretek Swarm Load Testing Framework

Performance benchmarking and load testing for the Heretek Swarm multi-agent AI system.

## Overview

This framework provides comprehensive load testing capabilities using two industry-standard tools:

- **Locust** - Python-based distributed load testing
- **k6** - Modern JavaScript load testing with Grafana integration

## Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| p95 Latency | < 100ms | < 200ms |
| p99 Latency | < 500ms | < 1000ms |
| Success Rate | > 99% | > 95% |
| Concurrent Users | 100+ | 50+ |

## Quick Start

### Prerequisites

```bash
# Install Locust
pip install locust

# Install k6 (macOS)
brew install k6

# Install k6 (Linux)
curl https://github.com/grafana/k6/releases/download/v1.0.0/k6-v1.0.0-linux-amd64.tar.gz | sudo tar -xz --strip-components 1 -C /usr/local/bin
```

### Running Tests

#### Locust Tests

```bash
# Web UI (interactive)
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Headless mode (CI/CD)
locust -f tests/load/locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 60s

# With custom shape (spike test)
locust -f tests/load/locustfile.py --host=http://localhost:8000 --headless --shape-class SpikeLoadShape
```

#### k6 Tests

```bash
# Basic test
k6 run tests/load/k6/load_test.js

# With custom VUs and duration
k6 run --vus 100 --duration 60s tests/load/k6/load_test.js

# With thresholds
k6 run --thresholds "http_req_duration<p(95)=100" tests/load/k6/load_test.js

# Output to InfluxDB (for Grafana)
k6 run --out influxdb=http://localhost:8086/k6 tests/load/k6/load_test.js
```

## Test Scenarios

### 1. Spike Load Test

**Purpose:** Test system behavior under sudden traffic surge

| Phase | Duration | Users | Description |
|-------|----------|-------|-------------|
| Baseline | 60s | 10 | Normal operation |
| Spike | 60s | 10 → 100 | Sudden increase |
| Hold | 60s | 100 | Peak load |
| Recovery | 60s | 100 → 10 | Return to normal |

**Expected Results:**
- System handles spike without crashing
- Latency increases but stays within acceptable bounds
- System recovers quickly after spike ends

### 2. Endurance Test

**Purpose:** Detect memory leaks and resource exhaustion

| Phase | Duration | Users | Description |
|-------|----------|-------|-------------|
| Ramp Up | 5m | 0 → 50 | Gradual increase |
| Hold | 60m | 50 | Sustained load |
| Ramp Down | 5m | 50 → 0 | Graceful shutdown |

**Expected Results:**
- Stable latency throughout test
- No memory growth over time
- No resource exhaustion

### 3. Breaking Point Test

**Purpose:** Find system limits and failure modes

| Phase | Duration | Users | Description |
|-------|----------|-------|-------------|
| Stage 1 | 2m | 10 → 50 | Light load |
| Stage 2 | 2m | 50 → 100 | Moderate load |
| Stage 3 | 2m | 100 → 200 | Heavy load |
| Stage 4 | 2m | 200 → 500 | Very heavy load |
| Stage 5 | 2m | 500 → 1000 | Extreme load |

**Expected Results:**
- Identify maximum sustainable load
- Document failure mode (graceful degradation vs crash)
- Establish scaling thresholds

### 4. Recovery Test

**Purpose:** Verify system recovery after overload

| Phase | Duration | Users | Description |
|-------|----------|-------|-------------|
| Normal | 1m | 20 | Baseline |
| Overload | 2m | 500 | System stress |
| Recovery | 1m | 500 → 20 | Load reduction |
| Verify | 2m | 20 | Confirm recovery |

**Expected Results:**
- System recovers automatically
- No manual intervention required
- Performance returns to baseline

## Endpoint Coverage

| Endpoint | Category | Test Weight | Target p95 |
|----------|----------|-------------|------------|
| `/api/health` | Health | 30% | < 50ms |
| `/api/agents` | Agent Ops | 20% | < 100ms |
| `/api/agents/{id}/status` | Agent Ops | 20% | < 100ms |
| `/api/memory/search` | Memory | 15% | < 150ms |
| `/api/memory/store` | Memory | 10% | < 200ms |
| `/api/consensus/initiate` | Consensus | 5% | < 300ms |

## Monitoring Integration

### Prometheus Metrics

The load tests integrate with Prometheus for real-time monitoring:

```yaml
# prometheus-config.yaml
scrape_configs:
  - job_name: 'k6'
    static_configs:
      - targets: ['localhost:6565']
    
  - job_name: 'heretek-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboard

Import the provided dashboard for visualization:

```bash
# Import dashboard
curl -X POST -H "Content-Type: application/json" \
  -d @tests/load/grafana/dashboard.json \
  http://localhost:3000/api/dashboards/db
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/load-test.yml
name: Load Testing

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install Locust
        run: pip install locust
      
      - name: Start API
        run: |
          docker-compose up -d api
          sleep 30
      
      - name: Run Load Test
        run: |
          locust -f tests/load/locustfile.py \
            --host=http://localhost:8000 \
            --headless \
            -u 50 \
            -r 10 \
            -t 60s \
            --fail-on-threshold
```

## Results Analysis

### Locust Output

```
Name                                                        # reqs    # fails    Avg     Min     Max     Median     p95     p99
--------------------------------------------------------------------------------------------------------------------------------
Health Check                                                  1000      0 (0%)     25      10      80      22       45      68
List Agents                                                    500      0 (0%)     45      20     120      40       78     105
Agent Status                                                   500      0 (0%)     38      15      95      35       65      88
Search Memory                                                  300      0 (0%)     65      30     180      58      110     155
Store Memory                                                   200      0 (0%)     85      40     250      75      145     198
```

### k6 Output

```
     ✓ api_success_rate          : 100.00% ✓ 2500      ✗ 0
     ✓ http_req_duration         : avg=45ms min=10ms med=40ms max=250ms p(95)=78ms p(99)=105ms
     ✓ health_check_latency_ms   : avg=25ms min=10ms med=22ms max=80ms  p(95)=45ms p(99)=68ms

     checks.....................: 100.00% ✓ 2500      ✗ 0
     data_received..............: 1.5 MB
     data_sent..................: 500 KB
     http_reqs..................: 2500
     iteration_duration.........: avg=1.5s  min=1s    med=1.4s  max=3s    p(95)=2.2s  p(99)=2.8s
     iterations.................: 500
     vus........................: 50
     vus_max....................: 100
```

## Troubleshooting

### High Latency

1. Check database connection pool size
2. Verify NATS event mesh capacity
3. Review LLM API rate limits
4. Check Redis memory usage

### High Failure Rate

1. Verify authentication tokens
2. Check API endpoint availability
3. Review rate limiting configuration
4. Inspect error logs

### Resource Exhaustion

1. Monitor memory usage during tests
2. Check file descriptor limits
3. Review connection pool settings
4. Verify horizontal scaling configuration

## Best Practices

1. **Run tests in isolated environment** - Don't run load tests against production
2. **Start with baseline tests** - Establish normal performance before stress testing
3. **Monitor during tests** - Watch system metrics in real-time
4. **Document results** - Keep historical performance data
5. **Test regularly** - Run load tests as part of CI/CD pipeline
6. **Set realistic targets** - Base targets on actual user behavior

## References

- [Locust Documentation](https://docs.locust.io/)
- [k6 Documentation](https://k6.io/docs/)
- [Grafana k6 Integration](https://k6.io/docs/results-visualization/)
- [Performance Testing Best Practices](https://martinfowler.com/articles/performance-testing.html)
