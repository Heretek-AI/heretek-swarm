"""
Metrics collection for Heretek Swarm.

Agent Gamma - QA and Validation Lead
Provides Prometheus-compatible metrics for monitoring system health.
"""

from dataclasses import dataclass
from typing import Any

from opentelemetry import metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource


# ============== CONFIGURATION ==============

@dataclass
class MetricsConfig:
    """Configuration for metrics collection."""
    service_name: str = "heretek-swarm"
    prometheus_port: int = 9090
    enable_prometheus: bool = True


# ============== METER INITIALIZATION ==============

_meter: metrics.Meter | None = None


def init_metrics(config: MetricsConfig | None = None) -> metrics.Meter:
    """
    Initialize OpenTelemetry metrics.
    
    Args:
        config: Metrics configuration.
    
    Returns:
        Configured meter instance.
    """
    global _meter
    
    if _meter is not None:
        return _meter
    
    config = config or MetricsConfig()
    
    # Create resource
    resource = Resource.create({
        "service.name": config.service_name,
    })
    
    # Create readers
    readers = []
    
    if config.enable_prometheus:
        prometheus_reader = PrometheusMetricReader(port=config.prometheus_port)
        readers.append(prometheus_reader)
    
    # Create meter provider
    provider = MeterProvider(
        resource=resource,
        metric_readers=readers,
    )
    
    metrics.set_meter_provider(provider)
    
    _meter = metrics.get_meter(config.service_name)
    
    return _meter


def get_meter() -> metrics.Meter:
    """Get the configured meter, initializing if needed."""
    global _meter
    if _meter is None:
        _meter = init_metrics()
    return _meter


# ============== METRIC DEFINITIONS ==============

class SwarmMetrics:
    """
    Standard metrics for Heretek Swarm monitoring.
    
    Metrics follow Prometheus naming conventions:
    - snake_case names
    - _total suffix for counters
    - _seconds/_bytes suffix for units
    - Base unit in the name
    """
    
    _instance: "SwarmMetrics | None" = None
    
    def __init__(self) -> None:
        meter = get_meter()
        
        # ============== AGENT METRICS ==============
        
        self.agents_active = meter.create_gauge(
            name="heretek_agents_active",
            description="Number of currently active agents",
            unit="1",
        )
        
        self.agent_tasks_total = meter.create_counter(
            name="heretek_agent_tasks_total",
            description="Total number of tasks executed by agents",
            unit="1",
        )
        
        self.agent_task_duration = meter.create_histogram(
            name="heretek_agent_task_duration_seconds",
            description="Duration of agent task execution",
            unit="s",
        )
        
        self.agent_errors_total = meter.create_counter(
            name="heretek_agent_errors_total",
            description="Total number of agent errors",
            unit="1",
        )
        
        # ============== MESSAGE METRICS ==============
        
        self.messages_sent_total = meter.create_counter(
            name="heretek_messages_sent_total",
            description="Total number of A2A messages sent",
            unit="1",
        )
        
        self.messages_received_total = meter.create_counter(
            name="heretek_messages_received_total",
            description="Total number of A2A messages received",
            unit="1",
        )
        
        self.message_latency = meter.create_histogram(
            name="heretek_message_latency_seconds",
            description="A2A message delivery latency",
            unit="s",
        )
        
        self.messages_failed_total = meter.create_counter(
            name="heretek_messages_failed_total",
            description="Total number of failed message deliveries",
            unit="1",
        )
        
        # ============== CONSENSUS METRICS ==============
        
        self.consensus_rounds_total = meter.create_counter(
            name="heretek_consensus_rounds_total",
            description="Total number of consensus rounds",
            unit="1",
        )
        
        self.consensus_duration = meter.create_histogram(
            name="heretek_consensus_duration_seconds",
            description="Duration of consensus rounds",
            unit="s",
        )
        
        self.consensus_timeouts_total = meter.create_counter(
            name="heretek_consensus_timeouts_total",
            description="Total number of consensus timeouts",
            unit="1",
        )
        
        # ============== STATE METRICS ==============
        
        self.state_checkpoints_total = meter.create_counter(
            name="heretek_state_checkpoints_total",
            description="Total number of state checkpoints created",
            unit="1",
        )
        
        self.state_rollbacks_total = meter.create_counter(
            name="heretek_state_rollbacks_total",
            description="Total number of state rollbacks",
            unit="1",
        )
        
        self.state_rollback_duration = meter.create_histogram(
            name="heretek_state_rollback_duration_seconds",
            description="Duration of state rollbacks",
            unit="s",
        )
        
        # ============== LATENCY GATE METRICS ==============
        
        self.latency_baseline_exceeded_total = meter.create_counter(
            name="heretek_latency_baseline_exceeded_total",
            description="Total number of operations exceeding latency baseline",
            unit="1",
        )
        
    @classmethod
    def get_instance(cls) -> "SwarmMetrics":
        """Get singleton instance of metrics."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


# ============== CONVENIENCE FUNCTIONS ==============

def record_message_sent(message_type: str, sender_type: str) -> None:
    """Record a sent message."""
    metrics = SwarmMetrics.get_instance()
    metrics.messages_sent_total.add(1, {
        "message_type": message_type,
        "sender_type": sender_type,
    })


def record_message_latency(latency_ms: float, exceeded_baseline: bool) -> None:
    """Record message latency."""
    metrics = SwarmMetrics.get_instance()
    metrics.message_latency.record(latency_ms / 1000)  # Convert to seconds
    
    if exceeded_baseline:
        metrics.latency_baseline_exceeded_total.add(1)


def record_task_completion(agent_type: str, duration_seconds: float) -> None:
    """Record task completion."""
    metrics = SwarmMetrics.get_instance()
    metrics.agent_tasks_total.add(1, {"agent_type": agent_type})
    metrics.agent_task_duration.record(duration_seconds)


def record_consensus_round(outcome: str, duration_seconds: float) -> None:
    """Record consensus round completion."""
    metrics = SwarmMetrics.get_instance()
    metrics.consensus_rounds_total.add(1, {"outcome": outcome})
    metrics.consensus_duration.record(duration_seconds)


def record_state_rollback(success: bool, duration_seconds: float) -> None:
    """Record state rollback."""
    metrics = SwarmMetrics.get_instance()
    metrics.state_rollbacks_total.add(1, {"success": str(success).lower()})
    metrics.state_rollback_duration.record(duration_seconds)
