"""
Metrics collection for Heretek Swarm.

Agent Gamma - QA and Validation Lead
Provides Prometheus-compatible metrics for monitoring system health.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

try:
    from opentelemetry import metrics as otel_metrics
    from opentelemetry.exporter.prometheus import PrometheusMetricReader
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.resources import Resource
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    otel_metrics = None
    PrometheusMetricReader = None
    MeterProvider = None
    Resource = None

# ============== CONFIGURATION ==============


@dataclass
class MetricsConfig:
    """Configuration for metrics collection."""
    service_name: str = "heretek-swarm"
    prometheus_port: int = 9090
    enable_prometheus: bool = True
    enable_realtime: bool = True
    realtime_interval_seconds: int = 5


# ============== METER INITIALIZATION ==============

_meter: Any | None = None


def init_metrics(config: MetricsConfig | None = None) -> Any:
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
    
    if not OTEL_AVAILABLE:
        # Return mock meter when opentelemetry is not available
        return MockMeter()
    
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
    
    otel_metrics.set_meter_provider(provider)
    
    _meter = otel_metrics.get_meter(config.service_name)
    
    return _meter


def get_meter() -> Any:
    """Get the configured meter, initializing if needed."""
    global _meter
    if _meter is None:
        _meter = init_metrics()
    return _meter


class MockMeter:
    """Mock meter for testing when opentelemetry is not available."""
    
    def create_gauge(self, name: str, description: str = "", unit: str = "") -> "MockInstrument":
        return MockInstrument(name, "gauge")
    
    def create_counter(self, name: str, description: str = "", unit: str = "") -> "MockInstrument":
        return MockInstrument(name, "counter")
    
    def create_histogram(self, name: str, description: str = "", unit: str = "") -> "MockInstrument":
        return MockInstrument(name, "histogram")


class MockInstrument:
    """Mock instrument for testing."""
    
    def __init__(self, name: str, instrument_type: str):
        self.name = name
        self.instrument_type = instrument_type
        self.values: List[float] = []
    
    def set(self, value: float, attributes: Dict[str, Any] = None) -> None:
        self.values.append(value)
    
    def add(self, value: float, attributes: Dict[str, Any] = None) -> None:
        self.values.append(value)
    
    def record(self, value: float, attributes: Dict[str, Any] = None) -> None:
        self.values.append(value)


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


# ============== SWARM METRICS COLLECTOR ==============


@dataclass
class AgentMetrics:
    """Per-agent performance metrics."""
    agent_id: str
    agent_type: str
    tasks_completed: int = 0
    tasks_failed: int = 0
    avg_task_duration_seconds: float = 0.0
    messages_sent: int = 0
    messages_received: int = 0
    error_count: int = 0
    success_rate: float = 0.0
    health_score: float = 0.0
    last_activity: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "avg_task_duration_seconds": self.avg_task_duration_seconds,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "error_count": self.error_count,
            "success_rate": self.success_rate,
            "health_score": self.health_score,
            "last_activity": self.last_activity,
            "metadata": self.metadata,
        }


@dataclass
class SwarmMetricsData:
    """Aggregate swarm health metrics."""
    total_agents: int = 0
    active_agents: int = 0
    idle_agents: int = 0
    total_tasks_completed: int = 0
    total_tasks_failed: int = 0
    avg_task_duration_seconds: float = 0.0
    total_messages_sent: int = 0
    total_messages_received: int = 0
    avg_message_latency_seconds: float = 0.0
    consensus_rounds: int = 0
    consensus_success_rate: float = 0.0
    overall_health_score: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_agents": self.total_agents,
            "active_agents": self.active_agents,
            "idle_agents": self.idle_agents,
            "total_tasks_completed": self.total_tasks_completed,
            "total_tasks_failed": self.total_tasks_failed,
            "avg_task_duration_seconds": self.avg_task_duration_seconds,
            "total_messages_sent": self.total_messages_sent,
            "total_messages_received": self.total_messages_received,
            "avg_message_latency_seconds": self.avg_message_latency_seconds,
            "consensus_rounds": self.consensus_rounds,
            "consensus_success_rate": self.consensus_success_rate,
            "overall_health_score": self.overall_health_score,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class ConsciousnessMetricsData:
    """IIT Phi and FEP metrics from consciousness modules."""
    system_id: str = "swarm"
    phi_score: float = 0.0
    phi_max: float = 0.0
    phi_min: float = 0.0
    phi_avg: float = 0.0
    integration_level: str = "unknown"
    differentiation_level: str = "unknown"
    free_energy: float = 0.0
    free_energy_avg: float = 0.0
    surprise_avg: float = 0.0
    prediction_accuracy: float = 0.0
    belief_precision: float = 0.0
    agent_phi_scores: Dict[str, float] = field(default_factory=dict)
    agent_fep_scores: Dict[str, float] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "system_id": self.system_id,
            "phi_score": self.phi_score,
            "phi_max": self.phi_max,
            "phi_min": self.phi_min,
            "phi_avg": self.phi_avg,
            "integration_level": self.integration_level,
            "differentiation_level": self.differentiation_level,
            "free_energy": self.free_energy,
            "free_energy_avg": self.free_energy_avg,
            "surprise_avg": self.surprise_avg,
            "prediction_accuracy": self.prediction_accuracy,
            "belief_precision": self.belief_precision,
            "agent_phi_scores": self.agent_phi_scores,
            "agent_fep_scores": self.agent_fep_scores,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


class SwarmMetricsCollector:
    """
    Comprehensive metrics collector for agent swarm health monitoring.
    
    Collects per-agent metrics, aggregate swarm metrics, and consciousness
    metrics (IIT Phi and FEP) from GAP-001/GAP-002 implementations.
    
    Example:
        ```python
        collector = SwarmMetricsCollector()
        
        # Collect agent metrics
        agent_metrics = collector.collect_agent_metrics("alpha")
        
        # Collect swarm metrics
        swarm_metrics = collector.collect_swarm_metrics()
        
        # Collect consciousness metrics
        consciousness_metrics = collector.collect_consciousness_metrics()
        
        # Calculate overall health score
        health_score = collector.calculate_health_score()
        ```
    """
    
    def __init__(
        self,
        phi_calculator: Optional[Any] = None,
        fep_calculator: Optional[Any] = None,
    ):
        """
        Initialize the metrics collector.
        
        Args:
            phi_calculator: Optional IIT Phi calculator instance
            fep_calculator: Optional FEP calculator instance
        """
        self._metrics = SwarmMetrics.get_instance()
        self._phi_calculator = phi_calculator
        self._fep_calculator = fep_calculator
        
        # Agent metrics storage
        self._agent_metrics: Dict[str, AgentMetrics] = {}
        self._agent_states: Dict[str, str] = {}  # active, idle, offline
        
        # Swarm metrics storage
        self._swarm_metrics_history: List[SwarmMetricsData] = []
        self._consciousness_metrics_history: List[ConsciousnessMetricsData] = []
        
        # Callbacks for external data sources
        self._agent_state_callbacks: List[Callable[[], Dict[str, str]]] = []
        self._consciousness_callbacks: List[Callable[[], Dict[str, Any]]] = []
        
        self._last_collection_time: Optional[datetime] = None
    
    def register_agent_state_callback(self, callback: Callable[[], Dict[str, str]]) -> None:
        """Register a callback to fetch agent states."""
        self._agent_state_callbacks.append(callback)
    
    def register_consciousness_callback(self, callback: Callable[[], Dict[str, Any]]) -> None:
        """Register a callback to fetch consciousness metrics."""
        self._consciousness_callbacks.append(callback)
    
    def update_agent_state(self, agent_id: str, state: str) -> None:
        """Update an agent's state (active, idle, offline)."""
        self._agent_states[agent_id] = state
        if agent_id not in self._agent_metrics:
            self._agent_metrics[agent_id] = AgentMetrics(agent_id=agent_id, agent_type="unknown")
        self._agent_metrics[agent_id].last_activity = datetime.now(timezone.utc).isoformat()
    
    def record_agent_task(
        self,
        agent_id: str,
        duration_seconds: float,
        success: bool,
        agent_type: str = "unknown",
    ) -> None:
        """Record an agent task completion."""
        if agent_id not in self._agent_metrics:
            self._agent_metrics[agent_id] = AgentMetrics(agent_id=agent_id, agent_type=agent_type)
        
        metrics = self._agent_metrics[agent_id]
        metrics.agent_type = agent_type
        metrics.last_activity = datetime.now(timezone.utc).isoformat()
        
        if success:
            metrics.tasks_completed += 1
        else:
            metrics.tasks_failed += 1
            metrics.error_count += 1
        
        # Update average duration
        total_tasks = metrics.tasks_completed + metrics.tasks_failed
        metrics.avg_task_duration_seconds = (
            (metrics.avg_task_duration_seconds * (total_tasks - 1) + duration_seconds)
            / total_tasks
        )
        
        # Update success rate
        metrics.success_rate = metrics.tasks_completed / max(1, total_tasks)
        
        # Update health score (weighted combination)
        metrics.health_score = self._calculate_agent_health(metrics)
        
        # Record in Prometheus metrics
        if success:
            self._metrics.agent_tasks_total.add(1, {"agent_type": agent_type})
        self._metrics.agent_task_duration.record(duration_seconds)
    
    def record_agent_message(
        self,
        agent_id: str,
        sent: bool,
        latency_seconds: float = 0.0,
    ) -> None:
        """Record an agent message sent or received."""
        if agent_id not in self._agent_metrics:
            self._agent_metrics[agent_id] = AgentMetrics(agent_id=agent_id, agent_type="unknown")
        
        metrics = self._agent_metrics[agent_id]
        metrics.last_activity = datetime.now(timezone.utc).isoformat()
        
        if sent:
            metrics.messages_sent += 1
        else:
            metrics.messages_received += 1
        
        # Record in Prometheus metrics
        if sent:
            self._metrics.messages_sent_total.add(1, {"agent_id": agent_id})
        else:
            self._metrics.messages_received_total.add(1, {"agent_id": agent_id})
        
        if latency_seconds > 0:
            self._metrics.message_latency.record(latency_seconds)
    
    def record_agent_error(self, agent_id: str, error_type: str = "unknown") -> None:
        """Record an agent error."""
        if agent_id not in self._agent_metrics:
            self._agent_metrics[agent_id] = AgentMetrics(agent_id=agent_id, agent_type="unknown")
        
        self._agent_metrics[agent_id].error_count += 1
        self._agent_metrics[agent_id].last_activity = datetime.now(timezone.utc).isoformat()
        self._metrics.agent_errors_total.add(1, {"agent_id": agent_id, "error_type": error_type})
    
    def collect_agent_metrics(self, agent_id: str) -> AgentMetrics:
        """
        Collect per-agent performance metrics.
        
        Args:
            agent_id: ID of the agent to collect metrics for
            
        Returns:
            AgentMetrics with current metrics for the agent
        """
        if agent_id in self._agent_metrics:
            metrics = self._agent_metrics[agent_id]
            # Update state from callbacks
            for callback in self._agent_state_callbacks:
                try:
                    states = callback()
                    if agent_id in states:
                        self._agent_states[agent_id] = states[agent_id]
                except Exception:
                    pass
            metrics.health_score = self._calculate_agent_health(metrics)
            return metrics
        
        return AgentMetrics(agent_id=agent_id, agent_type="unknown")
    
    def collect_swarm_metrics(self) -> SwarmMetricsData:
        """
        Collect aggregate swarm health metrics.
        
        Returns:
            SwarmMetricsData with aggregate metrics
        """
        # Update agent states from callbacks
        for callback in self._agent_state_callbacks:
            try:
                self._agent_states.update(callback())
            except Exception:
                pass
        
        total_agents = len(self._agent_metrics)
        active_agents = sum(1 for s in self._agent_states.values() if s == "active")
        idle_agents = sum(1 for s in self._agent_states.values() if s == "idle")
        
        total_tasks_completed = sum(m.tasks_completed for m in self._agent_metrics.values())
        total_tasks_failed = sum(m.tasks_failed for m in self._agent_metrics.values())
        total_messages_sent = sum(m.messages_sent for m in self._agent_metrics.values())
        total_messages_received = sum(m.messages_received for m in self._agent_metrics.values())
        
        # Calculate averages
        avg_task_duration = (
            sum(m.avg_task_duration_seconds for m in self._agent_metrics.values())
            / max(1, len(self._agent_metrics))
        )
        
        # Calculate swarm health score
        overall_health = self.calculate_health_score()
        
        data = SwarmMetricsData(
            total_agents=total_agents,
            active_agents=active_agents,
            idle_agents=idle_agents,
            total_tasks_completed=total_tasks_completed,
            total_tasks_failed=total_tasks_failed,
            avg_task_duration_seconds=avg_task_duration,
            total_messages_sent=total_messages_sent,
            total_messages_received=total_messages_received,
            overall_health_score=overall_health,
        )
        
        self._swarm_metrics_history.append(data)
        self._last_collection_time = datetime.now(timezone.utc)
        
        return data
    
    def collect_consciousness_metrics(self) -> ConsciousnessMetricsData:
        """
        Collect IIT Phi and FEP metrics from consciousness modules.
        
        Returns:
            ConsciousnessMetricsData with consciousness metrics
        """
        agent_phi_scores: Dict[str, float] = {}
        agent_fep_scores: Dict[str, float] = {}
        
        # Collect from callbacks
        for callback in self._consciousness_callbacks:
            try:
                result = callback()
                if "phi_scores" in result:
                    agent_phi_scores.update(result["phi_scores"])
                if "fep_scores" in result:
                    agent_fep_scores.update(result["fep_scores"])
            except Exception:
                pass
        
        # Calculate aggregate phi metrics
        phi_values = list(agent_phi_scores.values())
        phi_avg = sum(phi_values) / max(1, len(phi_values)) if phi_values else 0.0
        phi_max = max(phi_values) if phi_values else 0.0
        phi_min = min(phi_values) if phi_values else 0.0
        
        # Calculate aggregate FEP metrics
        fep_values = list(agent_fep_scores.values())
        fep_avg = sum(fep_values) / max(1, len(fep_values)) if fep_values else 0.0
        
        # Determine integration/differentiation levels
        integration_level = self._determine_integration_level(agent_phi_scores)
        differentiation_level = self._determine_differentiation_level(agent_phi_scores)
        
        data = ConsciousnessMetricsData(
            phi_score=phi_avg,
            phi_max=phi_max,
            phi_min=phi_min,
            phi_avg=phi_avg,
            integration_level=integration_level,
            differentiation_level=differentiation_level,
            free_energy=fep_avg,
            free_energy_avg=fep_avg,
            agent_phi_scores=agent_phi_scores,
            agent_fep_scores=agent_fep_scores,
        )
        
        self._consciousness_metrics_history.append(data)
        return data
    
    def calculate_health_score(self) -> float:
        """
        Calculate overall swarm health score (0-100).
        
        Health score is a weighted combination of:
        - Agent success rates (40%)
        - Agent availability (30%)
        - Message delivery success (20%)
        - Consciousness metrics (10%)
        
        Returns:
            Health score from 0.0 to 100.0
        """
        if not self._agent_metrics:
            return 0.0
        
        # Agent success rate component (40%)
        avg_success_rate = sum(m.success_rate for m in self._agent_metrics.values()) / len(self._agent_metrics)
        success_component = avg_success_rate * 40
        
        # Agent availability component (30%)
        total_agents = len(self._agent_states)
        active_idle_agents = sum(1 for s in self._agent_states.values() if s in ("active", "idle"))
        availability = active_idle_agents / max(1, total_agents)
        availability_component = availability * 30
        
        # Message delivery component (20%)
        total_sent = sum(m.messages_sent for m in self._agent_metrics.values())
        total_received = sum(m.messages_received for m in self._agent_metrics.values())
        message_success = min(1.0, total_received / max(1, total_sent))
        message_component = message_success * 20
        
        # Consciousness metrics component (10%)
        consciousness_score = 0.0
        for callback in self._consciousness_callbacks:
            try:
                result = callback()
                if "phi_avg" in result:
                    consciousness_score = result["phi_avg"] * 10
                    break
            except Exception:
                pass
        
        return min(100.0, max(0.0, success_component + availability_component + message_component + consciousness_score))
    
    def get_agent_metrics_history(self, limit: int = 100) -> List[SwarmMetricsData]:
        """Get recent swarm metrics history."""
        return self._swarm_metrics_history[-limit:]
    
    def get_consciousness_metrics_history(self, limit: int = 100) -> List[ConsciousnessMetricsData]:
        """Get recent consciousness metrics history."""
        return self._consciousness_metrics_history[-limit:]
    
    def get_all_agent_metrics(self) -> Dict[str, AgentMetrics]:
        """Get metrics for all agents."""
        return dict(self._agent_metrics)
    
    def get_agent_states(self) -> Dict[str, str]:
        """Get current states of all agents."""
        return dict(self._agent_states)
    
    def get_last_collection_time(self) -> Optional[datetime]:
        """Get the timestamp of the last metrics collection."""
        return self._last_collection_time
    
    def _calculate_agent_health(self, metrics: AgentMetrics) -> float:
        """Calculate health score for a single agent (0-100)."""
        # Success rate component (50%)
        success_component = metrics.success_rate * 50
        
        # Error rate component (30%) - inverse of error rate
        total_tasks = metrics.tasks_completed + metrics.tasks_failed
        error_rate = metrics.error_count / max(1, total_tasks)
        error_component = (1 - error_rate) * 30
        
        # Activity component (20%)
        activity_component = 20 if metrics.last_activity else 0
        
        return min(100.0, max(0.0, success_component + error_component + activity_component))
    
    def _determine_integration_level(self, phi_scores: Dict[str, float]) -> str:
        """Determine qualitative integration level from phi scores."""
        if not phi_scores:
            return "unknown"
        avg_phi = sum(phi_scores.values()) / len(phi_scores)
        if avg_phi >= 0.9:
            return "very_high"
        elif avg_phi >= 0.7:
            return "high"
        elif avg_phi >= 0.5:
            return "moderate"
        elif avg_phi >= 0.3:
            return "low"
        else:
            return "minimal"
    
    def _determine_differentiation_level(self, phi_scores: Dict[str, float]) -> str:
        """Determine differentiation level from phi score variance."""
        if not phi_scores or len(phi_scores) < 2:
            return "unknown"
        values = list(phi_scores.values())
        avg = sum(values) / len(values)
        variance = sum((v - avg) ** 2 for v in values) / len(values)
        if variance >= 0.3:
            return "very_high"
        elif variance >= 0.2:
            return "high"
        elif variance >= 0.1:
            return "moderate"
        elif variance >= 0.05:
            return "low"
        else:
            return "minimal"


# ============== REAL-TIME METRICS STREAM ==============


@dataclass
class MetricsSnapshot:
    """Point-in-time metrics snapshot."""
    swarm_metrics: SwarmMetricsData
    consciousness_metrics: ConsciousnessMetricsData
    agent_metrics: Dict[str, AgentMetrics]
    health_score: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "swarm_metrics": self.swarm_metrics.to_dict(),
            "consciousness_metrics": self.consciousness_metrics.to_dict(),
            "agent_metrics": {k: v.to_dict() for k, v in self.agent_metrics.items()},
            "health_score": self.health_score,
            "timestamp": self.timestamp,
        }


class RealTimeMetricsStream:
    """
    Real-time metrics streaming for live swarm monitoring.
    
    Provides async iterator interface for streaming metrics at
    configurable intervals, with support for Prometheus export format.
    
    Example:
        ```python
        stream = RealTimeMetricsStream(collector)
        
        # Stream metrics
        async for metrics in stream.stream_metrics(interval_seconds=5):
            print(f"Health: {metrics['health_score']}")
        
        # Get snapshot
        snapshot = stream.get_metrics_snapshot()
        
        # Export Prometheus format
        prometheus_data = stream.export_prometheus_format()
        ```
    """
    
    def __init__(self, collector: SwarmMetricsCollector):
        """
        Initialize the real-time metrics stream.
        
        Args:
            collector: SwarmMetricsCollector instance to stream from
        """
        self._collector = collector
        self._running = False
        self._snapshot: Optional[MetricsSnapshot] = None
        self._prometheus_cache: str = ""
        self._last_prometheus_update: Optional[datetime] = None
    
    async def stream_metrics(self, interval_seconds: int = 5) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream metrics at regular intervals.
        
        Args:
            interval_seconds: Time between metric collections
            
        Yields:
            Dictionary with current metrics snapshot
        """
        self._running = True
        
        try:
            while self._running:
                # Collect fresh metrics
                swarm = self._collector.collect_swarm_metrics()
                consciousness = self._collector.collect_consciousness_metrics()
                agents = self._collector.get_all_agent_metrics()
                health = self._collector.calculate_health_score()
                
                # Create snapshot
                self._snapshot = MetricsSnapshot(
                    swarm_metrics=swarm,
                    consciousness_metrics=consciousness,
                    agent_metrics=agents,
                    health_score=health,
                )
                
                # Update Prometheus cache
                self._update_prometheus_cache()
                
                yield self._snapshot.to_dict()
                
                await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            self._running = False
            raise
    
    def stop_streaming(self) -> None:
        """Stop the metrics streaming."""
        self._running = False
    
    def get_metrics_snapshot(self) -> MetricsSnapshot:
        """
        Get point-in-time metrics snapshot.
        
        Returns:
            MetricsSnapshot with current metrics
        """
        if self._snapshot is None:
            # Collect initial metrics
            swarm = self._collector.collect_swarm_metrics()
            consciousness = self._collector.collect_consciousness_metrics()
            agents = self._collector.get_all_agent_metrics()
            health = self._collector.calculate_health_score()
            
            self._snapshot = MetricsSnapshot(
                swarm_metrics=swarm,
                consciousness_metrics=consciousness,
                agent_metrics=agents,
                health_score=health,
            )
        
        return self._snapshot
    
    def export_prometheus_format(self) -> str:
        """
        Export metrics in Prometheus text format.
        
        Returns:
            Prometheus-formatted metrics string
        """
        if self._snapshot is None:
            self.get_metrics_snapshot()
        
        # Check if cache is stale (older than 5 seconds)
        now = datetime.now(timezone.utc)
        if (
            self._last_prometheus_update is None
            or (now - self._last_prometheus_update).total_seconds() > 5
        ):
            self._update_prometheus_cache()
        
        return self._prometheus_cache
    
    def _update_prometheus_cache(self) -> None:
        """Update the Prometheus format cache."""
        if self._snapshot is None:
            return
        
        lines = []
        timestamp_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        
        # Swarm metrics
        lines.append("# HELP heretek_swarm_health_score Overall swarm health score")
        lines.append("# TYPE heretek_swarm_health_score gauge")
        lines.append(f"heretek_swarm_health_score {self._snapshot.health_score}")
        
        lines.append("# HELP heretek_agents_total Total number of agents")
        lines.append("# TYPE heretek_agents_total gauge")
        lines.append(f"heretek_agents_total {self._snapshot.swarm_metrics.total_agents}")
        
        lines.append("# HELP heretek_agents_active Number of active agents")
        lines.append("# TYPE heretek_agents_active gauge")
        lines.append(f"heretek_agents_active {self._snapshot.swarm_metrics.active_agents}")
        
        lines.append("# HELP heretek_agents_idle Number of idle agents")
        lines.append("# TYPE heretek_agents_idle gauge")
        lines.append(f"heretek_agents_idle {self._snapshot.swarm_metrics.idle_agents}")
        
        lines.append("# HELP heretek_tasks_completed_total Total tasks completed")
        lines.append("# TYPE heretek_tasks_completed_total counter")
        lines.append(f"heretek_tasks_completed_total {self._snapshot.swarm_metrics.total_tasks_completed}")
        
        lines.append("# HELP heretek_tasks_failed_total Total tasks failed")
        lines.append("# TYPE heretek_tasks_failed_total counter")
        lines.append(f"heretek_tasks_failed_total {self._snapshot.swarm_metrics.total_tasks_failed}")
        
        lines.append("# HELP heretek_messages_sent_total Total messages sent")
        lines.append("# TYPE heretek_messages_sent_total counter")
        lines.append(f"heretek_messages_sent_total {self._snapshot.swarm_metrics.total_messages_sent}")
        
        lines.append("# HELP heretek_messages_received_total Total messages received")
        lines.append("# TYPE heretek_messages_received_total counter")
        lines.append(f"heretek_messages_received_total {self._snapshot.swarm_metrics.total_messages_received}")
        
        # Consciousness metrics
        lines.append("# HELP heretek_phi_score_avg Average Phi score (IIT)")
        lines.append("# TYPE heretek_phi_score_avg gauge")
        lines.append(f"heretek_phi_score_avg {self._snapshot.consciousness_metrics.phi_avg}")
        
        lines.append("# HELP heretek_phi_score_max Maximum Phi score")
        lines.append("# TYPE heretek_phi_score_max gauge")
        lines.append(f"heretek_phi_score_max {self._snapshot.consciousness_metrics.phi_max}")
        
        lines.append("# HELP heretek_free_energy_avg Average Free Energy (FEP)")
        lines.append("# TYPE heretek_free_energy_avg gauge")
        lines.append(f"heretek_free_energy_avg {self._snapshot.consciousness_metrics.free_energy_avg}")
        
        # Per-agent metrics
        for agent_id, metrics in self._snapshot.agent_metrics.items():
            safe_id = agent_id.replace("-", "_").replace(".", "_")
            
            lines.append(f"# HELP heretek_agent_health_score Health score for agent {agent_id}")
            lines.append("# TYPE heretek_agent_health_score gauge")
            lines.append(f"heretek_agent_health_score{{agent_id=\"{safe_id}\"}} {metrics.health_score}")
            
            lines.append(f"# HELP heretek_agent_tasks_completed Tasks completed by agent {agent_id}")
            lines.append("# TYPE heretek_agent_tasks_completed counter")
            lines.append(f"heretek_agent_tasks_completed{{agent_id=\"{safe_id}\"}} {metrics.tasks_completed}")
            
            lines.append(f"# HELP heretek_agent_tasks_failed Tasks failed by agent {agent_id}")
            lines.append("# TYPE heretek_agent_tasks_failed counter")
            lines.append(f"heretek_agent_tasks_failed{{agent_id=\"{safe_id}\"}} {metrics.tasks_failed}")
        
        # Agent Phi scores
        for agent_id, phi in self._snapshot.consciousness_metrics.agent_phi_scores.items():
            safe_id = agent_id.replace("-", "_").replace(".", "_")
            lines.append("# HELP heretek_agent_phi_score Phi score for agent")
            lines.append("# TYPE heretek_agent_phi_score gauge")
            lines.append(f"heretek_agent_phi_score{{agent_id=\"{safe_id}\"}} {phi}")
        
        self._prometheus_cache = "\n".join(lines)
        self._last_prometheus_update = datetime.now(timezone.utc)


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
