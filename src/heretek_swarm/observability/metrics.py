"""
Metrics collection and monitoring for Heretek Swarm.

Provides real-time metrics collection, consciousness metrics, and agent performance tracking.

Features:
- Per-agent performance metrics
- Aggregate swarm health metrics
- Consciousness metrics (Phi, FEP)
- Cycle detection metrics from workflow engine
- Phi training metrics from training environment
- Real-time metrics collection
- Prometheus format export
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# Import cycle detector and phi training for metrics integration
try:
    from ..workflow.engine import get_cycle_detector_metrics, export_cycle_detector_prometheus
    from ..consciousness.phi_training import PhiTrainingEnvironment
    CYCLE_DETECTOR_AVAILABLE = True
except ImportError:
    CYCLE_DETECTOR_AVAILABLE = False
    PhiTrainingEnvironment = None


@dataclass
class AgentMetrics:
    """Metrics for an individual agent."""
    agent_id: str
    tasks_completed: int = 0
    tasks_failed: int = 0
    avg_task_duration_ms: float = 0.0
    messages_sent: int = 0
    messages_received: int = 0
    error_count: int = 0
    health_score: float = 100.0
    last_activity: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "avg_task_duration_ms": self.avg_task_duration_ms,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "error_count": self.error_count,
            "health_score": self.health_score,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
        }


@dataclass
class SwarmMetricsData:
    """Aggregate metrics for the entire swarm."""
    total_agents: int = 0
    active_agents: int = 0
    idle_agents: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_messages: int = 0
    avg_message_latency_ms: float = 0.0
    health_score: float = 100.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_agents": self.total_agents,
            "active_agents": self.active_agents,
            "idle_agents": self.idle_agents,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "total_messages": self.total_messages,
            "avg_message_latency_ms": self.avg_message_latency_ms,
            "health_score": self.health_score,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ConsciousnessMetricsData:
    """Consciousness metrics (IIT Phi and FEP)."""
    phi_avg: float = 0.0
    phi_max: float = 0.0
    phi_min: float = 0.0
    integration_level: float = 0.0
    differentiation_level: float = 0.0
    free_energy_avg: float = 0.0
    free_energy_variance: float = 0.0
    agent_phi_scores: Dict[str, float] = field(default_factory=dict)
    agent_fep_scores: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "phi_avg": self.phi_avg,
            "phi_max": self.phi_max,
            "phi_min": self.phi_min,
            "integration_level": self.integration_level,
            "differentiation_level": self.differentiation_level,
            "free_energy_avg": self.free_energy_avg,
            "free_energy_variance": self.free_energy_variance,
            "agent_phi_scores": self.agent_phi_scores,
            "agent_fep_scores": self.agent_fep_scores,
            "timestamp": self.timestamp.isoformat(),
        }


class SwarmMetricsCollector:
    """
    Collects and aggregates metrics from all agents in the swarm.
    
    Features:
    - Per-agent performance metrics
    - Aggregate swarm health metrics
    - Consciousness metrics (Phi, FEP)
    - Real-time metrics collection
    """
    
    def __init__(self):
        self._agent_metrics: Dict[str, AgentMetrics] = {}
        self._message_latencies: List[float] = []
        self._task_durations: List[float] = []
        self._start_time = datetime.now(timezone.utc)
    
    def record_agent_activity(
        self,
        agent_id: str,
        task_completed: bool = False,
        task_failed: bool = False,
        task_duration_ms: float = 0.0,
        message_sent: bool = False,
        message_received: bool = False,
        error: bool = False,
    ) -> None:
        """Record activity for an agent."""
        if agent_id not in self._agent_metrics:
            self._agent_metrics[agent_id] = AgentMetrics(agent_id=agent_id)
        
        metrics = self._agent_metrics[agent_id]
        metrics.last_activity = datetime.now(timezone.utc)
        
        if task_completed:
            metrics.tasks_completed += 1
            if task_duration_ms > 0:
                self._task_durations.append(task_duration_ms)
                metrics.avg_task_duration_ms = sum(self._task_durations) / len(self._task_durations)
        
        if task_failed:
            metrics.tasks_failed += 1
        
        if message_sent:
            metrics.messages_sent += 1
        
        if message_received:
            metrics.messages_received += 1
        
        if error:
            metrics.error_count += 1
        
        # Update health score
        self._update_health_score(metrics)
    
    def _update_health_score(self, metrics: AgentMetrics) -> None:
        """Calculate agent health score based on various factors."""
        # Base score
        score = 100.0
        
        # Penalize errors
        score -= min(metrics.error_count * 5, 30)
        
        # Penalize failures
        total_tasks = metrics.tasks_completed + metrics.tasks_failed
        if total_tasks > 0:
            failure_rate = metrics.tasks_failed / total_tasks
            score -= failure_rate * 20
        
        # Penalize inactivity (if no activity in last 5 minutes)
        if metrics.last_activity:
            inactive_seconds = (datetime.now(timezone.utc) - metrics.last_activity).total_seconds()
            if inactive_seconds > 300:
                score -= min((inactive_seconds - 300) / 60, 20)
        
        metrics.health_score = max(0, min(100, score))
    
    def record_message_latency(self, latency_ms: float) -> None:
        """Record message latency."""
        self._message_latencies.append(latency_ms)
        # Keep only last 1000 measurements
        if len(self._message_latencies) > 1000:
            self._message_latencies = self._message_latencies[-1000:]
    
    def collect_swarm_metrics(self) -> SwarmMetricsData:
        """Collect aggregate swarm metrics."""
        total_agents = len(self._agent_metrics)
        active_agents = sum(
            1 for m in self._agent_metrics.values()
            if m.last_activity and (datetime.now(timezone.utc) - m.last_activity).total_seconds() < 60
        )
        idle_agents = total_agents - active_agents
        
        total_tasks = sum(m.tasks_completed + m.tasks_failed for m in self._agent_metrics.values())
        completed_tasks = sum(m.tasks_completed for m in self._agent_metrics.values())
        failed_tasks = sum(m.tasks_failed for m in self._agent_metrics.values())
        total_messages = sum(m.messages_sent + m.messages_received for m in self._agent_metrics.values())
        
        avg_latency = sum(self._message_latencies) / len(self._message_latencies) if self._message_latencies else 0
        
        # Calculate overall health score
        if self._agent_metrics:
            health_score = sum(m.health_score for m in self._agent_metrics.values()) / len(self._agent_metrics)
        else:
            health_score = 100.0
        
        return SwarmMetricsData(
            total_agents=total_agents,
            active_agents=active_agents,
            idle_agents=idle_agents,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            total_messages=total_messages,
            avg_message_latency_ms=avg_latency,
            health_score=health_score,
        )
    
    def collect_agent_metrics(self, agent_id: str) -> AgentMetrics:
        """Get metrics for a specific agent."""
        return self._agent_metrics.get(agent_id, AgentMetrics(agent_id=agent_id))
    
    def get_all_agent_metrics(self) -> Dict[str, AgentMetrics]:
        """Get metrics for all agents."""
        return self._agent_metrics.copy()
    
    def get_agent_states(self) -> Dict[str, str]:
        """Get current states of all agents."""
        states = {}
        now = datetime.now(timezone.utc)
        for agent_id, metrics in self._agent_metrics.items():
            if metrics.last_activity:
                inactive_seconds = (now - metrics.last_activity).total_seconds()
                if inactive_seconds < 60:
                    states[agent_id] = "active"
                elif inactive_seconds < 300:
                    states[agent_id] = "idle"
                else:
                    states[agent_id] = "inactive"
            else:
                states[agent_id] = "unknown"
        return states
    
    def calculate_health_score(self) -> float:
        """Calculate overall swarm health score."""
        if not self._agent_metrics:
            return 100.0
        
        avg_health = sum(m.health_score for m in self._agent_metrics.values()) / len(self._agent_metrics)
        
        # Factor in error rates
        total_tasks = sum(m.tasks_completed + m.tasks_failed for m in self._agent_metrics.values())
        total_failures = sum(m.tasks_failed for m in self._agent_metrics.values())
        failure_penalty = (total_failures / total_tasks * 10) if total_tasks > 0 else 0
        
        return max(0, min(100, avg_health - failure_penalty))
    
    def collect_consciousness_metrics(self) -> ConsciousnessMetricsData:
        """
        Collect consciousness metrics.
        
        Note: This is a placeholder implementation. In production,
        this would integrate with the IIT Phi and FEP calculators.
        """
        agent_phi_scores = {}
        agent_fep_scores = {}
        
        for agent_id, metrics in self._agent_metrics.items():
            # Simplified phi calculation based on activity
            activity_score = min(1.0, (metrics.messages_sent + metrics.messages_received) / 100)
            health_factor = metrics.health_score / 100
            agent_phi_scores[agent_id] = activity_score * health_factor
            
            # Simplified FEP calculation
            error_factor = 1 / (1 + metrics.error_count)
            agent_fep_scores[agent_id] = error_factor * health_factor
        
        phi_values = list(agent_phi_scores.values()) if agent_phi_scores else [0]
        
        return ConsciousnessMetricsData(
            phi_avg=sum(phi_values) / len(phi_values) if phi_values else 0,
            phi_max=max(phi_values) if phi_values else 0,
            phi_min=min(phi_values) if phi_values else 0,
            integration_level=0.5,  # Placeholder
            differentiation_level=0.5,  # Placeholder
            free_energy_avg=sum(agent_fep_scores.values()) / len(agent_fep_scores) if agent_fep_scores else 0,
            free_energy_variance=0.1,  # Placeholder
            agent_phi_scores=agent_phi_scores,
            agent_fep_scores=agent_fep_scores,
        )


class RealTimeMetricsStream:
    """
    Real-time metrics streaming for observability.
    
    Provides:
    - Periodic metrics snapshots
    - WebSocket streaming support
    - Prometheus format export
    """
    
    def __init__(self, collector: SwarmMetricsCollector):
        self._collector = collector
        self._snapshot_interval = 5  # seconds
        self._last_snapshot: Optional[SwarmMetricsData] = None
    
    def get_metrics_snapshot(self) -> SwarmMetricsData:
        """Get current metrics snapshot."""
        self._last_snapshot = self._collector.collect_swarm_metrics()
        return self._last_snapshot
    
    def export_prometheus_format(self) -> str:
        """
        Export metrics in Prometheus text format.
        
        Includes:
        - Standard swarm metrics
        - Consciousness metrics (Phi, FEP)
        - Cycle detection metrics (if available)
        - Phi training metrics (if available)
        """
        metrics = self._collector.collect_swarm_metrics()
        consciousness = self._collector.collect_consciousness_metrics()
        
        lines = [
            "# HELP heretek_swarm_total_agents Total number of agents",
            "# TYPE heretek_swarm_total_agents gauge",
            f"heretek_swarm_total_agents {metrics.total_agents}",
            "",
            "# HELP heretek_swarm_active_agents Number of active agents",
            "# TYPE heretek_swarm_active_agents gauge",
            f"heretek_swarm_active_agents {metrics.active_agents}",
            "",
            "# HELP heretek_swarm_health_score Overall swarm health score",
            "# TYPE heretek_swarm_health_score gauge",
            f"heretek_swarm_health_score {metrics.health_score}",
            "",
            "# HELP heretek_swarm_total_tasks Total tasks processed",
            "# TYPE heretek_swarm_total_tasks counter",
            f"heretek_swarm_total_tasks {metrics.total_tasks}",
            "",
            "# HELP heretek_swarm_consciousness_phi_avg Average consciousness phi score",
            "# TYPE heretek_swarm_consciousness_phi_avg gauge",
            f"heretek_swarm_consciousness_phi_avg {consciousness.phi_avg}",
            "",
            "# HELP heretek_swarm_consciousness_phi_max Maximum consciousness phi score",
            "# TYPE heretek_swarm_consciousness_phi_max gauge",
            f"heretek_swarm_consciousness_phi_max {consciousness.phi_max}",
            "",
            "# HELP heretek_swarm_consciousness_fep_avg Average free energy score",
            "# TYPE heretek_swarm_consciousness_fep_avg gauge",
            f"heretek_swarm_consciousness_fep_avg {consciousness.free_energy_avg}",
            "",
        ]
        
        # Add cycle detection metrics if available
        if CYCLE_DETECTOR_AVAILABLE:
            try:
                cycle_metrics = get_cycle_detector_metrics()
                if cycle_metrics:
                    lines.extend([
                        "# HELP heretek_workflow_cycles_total Total number of workflow cycles detected",
                        "# TYPE heretek_workflow_cycles_total counter",
                        f"heretek_workflow_cycles_total {cycle_metrics.get('total_cycles_detected', 0)}",
                        "",
                        "# HELP heretek_workflow_cycles_broken_total Total number of workflow cycles broken",
                        "# TYPE heretek_workflow_cycles_broken_total counter",
                        f"heretek_workflow_cycles_broken_total {cycle_metrics.get('total_cycles_broken', 0)}",
                        "",
                        "# HELP heretek_workflow_avg_iterations_before_cycle Average iterations before cycle detection",
                        "# TYPE heretek_workflow_avg_iterations_before_cycle gauge",
                        f"heretek_workflow_avg_iterations_before_cycle {cycle_metrics.get('avg_iterations_before_cycle', 0)}",
                        "",
                    ])
                    
                    # Add per-strategy metrics
                    for strategy, count in cycle_metrics.get("cycles_by_strategy", {}).items():
                        lines.extend([
                            "# HELP heretek_workflow_cycles_by_strategy Cycles broken by strategy",
                            "# TYPE heretek_workflow_cycles_by_strategy gauge",
                            f'heretek_workflow_cycles_by_strategy{{strategy="{strategy}"}} {count}',
                            "",
                        ])
            except Exception as e:
                lines.append(f"# Cycle detection metrics unavailable: {e}")
                lines.append("")
        
        # Add Phi training metrics if available
        if CYCLE_DETECTOR_AVAILABLE and PhiTrainingEnvironment:
            try:
                # Note: In production, you would get a reference to the actual training environment
                # This is a placeholder showing the metric format
                lines.extend([
                    "# HELP heretek_phi_training_episodes_total Total Phi training episodes",
                    "# TYPE heretek_phi_training_episodes_total counter",
                    "heretek_phi_training_episodes_total 0",
                    "",
                    "# HELP heretek_phi_training_success_total Successful Phi training episodes",
                    "# TYPE heretek_phi_training_success_total counter",
                    "heretek_phi_training_success_total 0",
                    "",
                    "# HELP heretek_phi_training_avg_improvement Average Phi improvement per episode",
                    "# TYPE heretek_phi_training_avg_improvement gauge",
                    "heretek_phi_training_avg_improvement 0",
                    "",
                    "# HELP heretek_phi_training_best_phi Best Phi achieved in training",
                    "# TYPE heretek_phi_training_best_phi gauge",
                    "heretek_phi_training_best_phi 0",
                    "",
                ])
            except Exception as e:
                lines.append(f"# Phi training metrics unavailable: {e}")
                lines.append("")
        
        # Add per-agent phi scores
        for agent_id, phi_score in consciousness.agent_phi_scores.items():
            lines.extend([
                "# HELP heretek_agent_phi Agent Phi score",
                "# TYPE heretek_agent_phi gauge",
                f'heretek_agent_phi{{agent_id="{agent_id}"}} {phi_score}',
                "",
            ])
        
        return "\n".join(lines)
