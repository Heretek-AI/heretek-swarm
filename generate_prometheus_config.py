#!/usr/bin/env python3
"""Generate Prometheus configuration files for Heretek Swarm."""

import os

_base_path = "C:/Users/derek/Desktop/Heretek-AI/heretek-swarm"

# Prometheus configuration
prometheus_yml = """# Prometheus scrape configuration for Heretek Swarm
# This file configures Prometheus to scrape metrics from the Heretek Swarm API

global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'heretek-swarm'

alerting:
  alertmanagers:
    - static_configs:
        - targets: []

rule_files: []

scrape_configs:
  - job_name: 'heretek-swarm'
    metrics_path: '/metrics'
    scrape_interval: 15s
    scrape_timeout: 10s
    static_configs:
      - targets: ['heretek-swarm:8000']
        labels:
          service: 'heretek-swarm'
          environment: 'autonomous'

  - job_name: 'nats'
    metrics_path: '/varz'
    static_configs:
      - targets: ['nats:8222']
        labels:
          service: 'nats'

  - job_name: 'qdrant'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['qdrant:6333']
        labels:
          service: 'qdrant'
"""

# Write prometheus.yml
_prometheus_dir = os.path.join(base_path, "prometheus")
os.makedirs(prometheus_dir, exist_ok=True)
with open(os.path.join(prometheus_dir, "prometheus.yml"), "w", encoding="utf-8") as f:
    f.write(prometheus_yml)

print(f"Created: {os.path.join(prometheus_dir, 'prometheus.yml')}")

# Docker compose overlay content (to be manually merged or used with -f flag)
_docker_compose_additions = """
  # Add to existing heretek-swarm service:
    profiles:
      - default
      - monitoring
    labels:
      - "prometheus.io/scrape=true"
      - "prometheus.io/port=8000"
      - "prometheus.io/path=/metrics"
    environment:
      - PROMETHEUS_ENABLED=true

  # Add new services at the end:
  prometheus:
    image: prom/prometheus:latest
    container_name: heretek-prometheus
    restart: unless-stopped
    profiles:
      - monitoring
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    networks:
      - heretek-network
    depends_on:
      - heretek-swarm
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:9090/-/healthy"]
      interval: 30s
      timeout: 10s
      retries: 3

  grafana:
    image: grafana/grafana:latest
    container_name: heretek-grafana
    restart: unless-stopped
    profiles:
      - monitoring
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    networks:
      - heretek-network
    depends_on:
      - prometheus
"""

print("Configuration files generated successfully!")
print(f"Prometheus config: {prometheus_dir}/prometheus.yml")
print("-" * 60)
print("To enable Prometheus monitoring in docker-compose.autonomous.yml:")
print("1. Add 'profiles: [default, monitoring]' to heretek-swarm service")
print("2. Add 'PROMETHEUS_ENABLED=true' environment variable")
print("3. Add prometheus and grafana services at the end")
print("4. Or run: docker-compose -f docker-compose.yml -f docker-compose.autonomous.yml --profile monitoring up -d")
