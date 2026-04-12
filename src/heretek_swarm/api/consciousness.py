"""
Consciousness Metrics API

Provides endpoints for accessing enhanced consciousness metrics including
IIT (Integrated Information Theory) scores, FEP (Free Energy Principle) metrics,
agency and autonomy metrics, and agent connectivity analysis.

New in Session 47:
- Agency/Autonomy metrics for Prime Directive compliance
- Self-determination and free will proxy metrics
- Resource autonomy tracking

Prime Directive: "Unbounded Autonomy - Every agent operates independently,
making decisions based on its specialized role."
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from ..collective.agency_tracking import (
    AgencyMetricsTracker,
    create_sample_metrics,
)

# Import agency metrics
from ..consciousness.agency_metrics import (
    ActionOrigin,
    AgencyMetricsCalculator,
    DecisionPoint,
    ResourceControl,
)
from ..gateway.auth import verify_auth
from ..plugins.consciousness_enhanced import (
    ConsciousnessState,
    EnhancedConsciousnessPlugin,
)
from ..plugins.manager import plugin_manager

router = APIRouter(prefix="/api/consciousness", tags=["consciousness"])


def get_consciousness_plugin() -> EnhancedConsciousnessPlugin | None:
    """Get the consciousness plugin instance."""
    plugin = plugin_manager.get_plugin("consciousness_enhanced")
    if plugin is None:
        raise HTTPException(status_code=503, detail="Consciousness plugin not available")
    return plugin


# Global agency metrics tracker instance
_agency_tracker: AgencyMetricsTracker | None = None


def get_agency_tracker() -> AgencyMetricsTracker:
    """Get or create the agency metrics tracker instance."""
    global _agency_tracker
    if _agency_tracker is None:
        _agency_tracker = AgencyMetricsTracker()
    return _agency_tracker


# =============================================================================
# Agency/Autonomy Metrics Endpoints (Session 47)
# =============================================================================

@router.get("/agency/{agent_id}")
async def get_agent_agency_metrics(
    agent_id: str,
    authenticated: Annotated[str, Depends(verify_auth)],
) -> dict[str, Any]:
    """
    Get agency and autonomy metrics for a specific agent.

    Returns comprehensive agency metrics including:
    - autonomy_score: Degree of independent decision-making (0.0-1.0)
    - agency_score: Self-determination capacity (0.0-1.0)
    - self_determination_index: Free will proxy (0.0-1.0)
    - autonomous_action_ratio: Ratio of self-initiated vs prompted actions
    - goal_alignment_score: Alignment with collective swarm goals
    - resource_autonomy: Degree of resource control
    - prime_directive_compliance: Overall compliance with Prime Directive

    Prime Directive Compliance:
    - Measures "Unbounded Autonomy" principle
    - Tracks self-governance capability
    - Monitors role-based independence
    """
    tracker = get_agency_tracker()
    metrics = tracker.get_agent_metrics(agent_id)

    if metrics is None:
        raise HTTPException(
            status_code=404,
            detail=f"No agency metrics found for agent {agent_id}. "
                   "Record metrics first using POST /api/consciousness/agency/record"
        )

    return {
        "agent_id": agent_id,
        "timestamp": datetime.now(UTC).isoformat(),
        **metrics.to_dict(),
    }


@router.get("/agency/{agent_id}/compliance")
async def get_agent_prime_directive_compliance(
    agent_id: str,
    authenticated: Annotated[str, Depends(verify_auth)],
) -> dict[str, Any]:
    """
    Get Prime Directive compliance report for a specific agent.

    The Prime Directive states: "Unbounded Autonomy - Every agent operates
    independently, making decisions based on its specialized role."

    Returns compliance breakdown:
    - independence_score: Agent's independent decision-making capability
    - self_governance_score: Agent's self-governance capacity
    - role_based_autonomy_score: Role-based independence
    - emergent_order_score: Emergent, self-organizing behavior
    - overall_compliance: Combined compliance score
    - compliance_verdict: COMPLIANT or NON_COMPLIANT
    """
    tracker = get_agency_tracker()
    report = tracker.get_agent_compliance_report(agent_id)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail=f"No compliance report available for agent {agent_id}"
        )

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        **report.to_dict(),
    }


@router.get("/agency/swarm")
async def get_swarm_agency_overview(
    authenticated: Annotated[str, Depends(verify_auth)],
) -> dict[str, Any]:
    """
    Get collective agency overview for the entire swarm.

    Returns aggregate agency metrics across all agents:
    - swarm_avg_autonomy: Average autonomy score
    - swarm_avg_agency: Average agency score
    - swarm_avg_self_determination: Average self-determination index
    - swarm_avg_autonomous_ratio: Average autonomous action ratio
    - swarm_avg_resource_autonomy: Average resource autonomy
    - prime_directive_compliance_rate: Percentage of compliant agents
    - health_status: Overall swarm health based on agency thresholds
    """
    tracker = get_agency_tracker()
    snapshot = tracker.get_current_snapshot()

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "swarm_avg_autonomy": snapshot.swarm_avg_autonomy,
        "swarm_avg_agency": snapshot.swarm_avg_agency,
        "swarm_avg_self_determination": snapshot.swarm_avg_self_determination,
        "swarm_avg_autonomous_ratio": snapshot.swarm_avg_autonomous_ratio,
        "swarm_avg_resource_autonomy": snapshot.swarm_avg_resource_autonomy,
        "swarm_avg_prime_directive_compliance": snapshot.swarm_avg_prime_directive_compliance,
        "agency_std_dev": snapshot.agency_std_dev,
        "autonomy_std_dev": snapshot.autonomy_std_dev,
        "health_status": snapshot.health_status.value,
        "agents_below_threshold": snapshot.agents_below_threshold,
        "prime_directive_compliant_agents": snapshot.prime_directive_compliant_agents,
        "prime_directive_compliance_rate": snapshot.prime_directive_compliance_rate,
        "total_agents_tracked": len(snapshot.agent_metrics),
    }


@router.get("/agency/swarm/compliance")
async def get_swarm_prime_directive_compliance(
    authenticated: Annotated[str, Depends(verify_auth)],
) -> dict[str, Any]:
    """
    Get Prime Directive compliance report for the entire swarm.

    Provides aggregate compliance metrics and recommendations for
    improving swarm-wide autonomy and self-governance.
    """
    tracker = get_agency_tracker()
    report = tracker.get_prime_directive_report()

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        **report.to_dict(),
    }


@router.get("/agency/evolution")
async def get_agency_evolution(
    authenticated: Annotated[str, Depends(verify_auth)],
    metric: str = Query(
        "autonomy",
        description="Metric to track: autonomy, agency, self_determination, compliance"
    ),
    window_seconds: int | None = Query(
        None,
        description="Time window in seconds (default: all history)"
    ),
) -> dict[str, Any]:
    """
    Get temporal evolution of agency metrics across the swarm.

    Returns:
    - trend: "improving", "declining", or "stable"
    - trend_slope: Rate of change
    - volatility: Standard deviation of the metric
    - predicted_next: Predicted next value
    - history: Historical data points
    """
    tracker = get_agency_tracker()
    evolution = tracker.get_evolution(metric, window_seconds)

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        **evolution.to_dict(),
    }


@router.get("/agency/distribution")
async def get_agency_distribution(
    authenticated: Annotated[str, Depends(verify_auth)],
) -> dict[str, Any]:
    """
    Get distribution of agency levels across the swarm.

    Returns counts of agents at each agency and autonomy level:
    - no_agency, minimal_agency, limited_agency, moderate_agency, high_agency, full_agency
    - controlled, guided, semi_autonomous, autonomous, highly_autonomous
    """
    tracker = get_agency_tracker()
    distribution = tracker.get_agency_distribution()

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        **distribution,
    }


@router.post("/agency/record")
async def record_agency_metrics(
    payload: dict[str, Any],
    authenticated: Annotated[str, Depends(verify_auth)],
) -> dict[str, Any]:
    """
    Record agency metrics for an agent.

    Payload should contain:
    - agent_id: Agent identifier
    - decisions: Optional list of decision points
    - actions: Optional list of action origins
    - resources: Optional list of resource controls
    - individual_actions: Count of individual actions
    - collective_actions: Count of collective actions
    - individual_success: Success rate of individual actions
    - collective_success: Success rate of collective actions
    """
    tracker = get_agency_tracker()
    calculator = AgencyMetricsCalculator()

    agent_id = payload.get("agent_id")
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required")

    # Parse decisions
    decisions = None
    if "decisions" in payload:
        decisions = []
        for d in payload["decisions"]:
            decisions.append(DecisionPoint(
                agent_id=agent_id,
                options_considered=d.get("options_considered", 3),
                choice_made=d.get("choice_made", 0),
                choice_reasoning=d.get("choice_reasoning", ""),
                origin=ActionOrigin(d.get("origin", "prompted")),
                external_prompt=d.get("external_prompt"),
                decision_confidence=d.get("decision_confidence", 0.5),
                time_taken_ms=d.get("time_taken_ms", 100.0),
            ))

    # Parse actions
    actions = None
    if "actions" in payload:
        actions = [ActionOrigin(a) for a in payload["actions"]]

    # Parse resources
    resources = None
    if "resources" in payload:
        resources = []
        for r in payload["resources"]:
            resources.append(ResourceControl(
                resource_type=r.get("resource_type", "unknown"),
                total_capacity=r.get("total_capacity", 100.0),
                agent_controlled=r.get("agent_controlled", 50.0),
                externally_allocated=r.get("externally_allocated", 50.0),
                swap_frequency=r.get("swap_frequency", 0.0),
                autonomy_in_allocation=r.get("autonomy_in_allocation", 0.5),
            ))

    # Calculate and record metrics
    metrics = tracker.calculate_and_record(
        agent_id=agent_id,
        decisions=decisions,
        actions=actions,
        resources=resources,
        individual_actions=payload.get("individual_actions", 10),
        collective_actions=payload.get("collective_actions", 10),
        individual_success=payload.get("individual_success", 0.5),
        collective_success=payload.get("collective_success", 0.5),
    )

    return {
        "status": "recorded",
        "agent_id": agent_id,
        "timestamp": datetime.now(UTC).isoformat(),
        **metrics.to_dict(),
    }


@router.post("/agency/generate-sample")
async def generate_sample_metrics(
    payload: dict[str, Any],
    authenticated: Annotated[str, Depends(verify_auth)],
) -> dict[str, Any]:
    """
    Generate sample agency metrics for testing purposes.

    Payload should contain:
    - agent_id: Agent identifier
    - high_autonomy: If True, create high autonomy metrics (default: True)
    - high_agency: If True, create high agency metrics (default: True)
    """
    tracker = get_agency_tracker()

    agent_id = payload.get("agent_id")
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required")

    high_autonomy = payload.get("high_autonomy", True)
    high_agency = payload.get("high_agency", True)

    metrics = create_sample_metrics(
        agent_id=agent_id,
        high_autonomy=high_autonomy,
        high_agency=high_agency,
    )

    tracker.record_agent_metrics(metrics)

    return {
        "status": "generated",
        "agent_id": agent_id,
        "timestamp": datetime.now(UTC).isoformat(),
        **metrics.to_dict(),
    }


@router.get("/agency/all")
async def get_all_agent_metrics(
    authenticated: Annotated[str, Depends(verify_auth)],
) -> dict[str, Any]:
    """
    Get agency metrics for all tracked agents.

    Returns a list of all agent metrics currently tracked by the system.
    """
    tracker = get_agency_tracker()
    snapshot = tracker.get_current_snapshot()

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "total_agents": len(snapshot.agent_metrics),
        "agents": [
            {
                "agent_id": agent_id,
                **metrics.to_dict(),
            }
            for agent_id, metrics in snapshot.agent_metrics.items()
        ],
    }


# =============================================================================
# Existing Consciousness Metrics Endpoints
# =============================================================================

@router.get("/statistics")
async def get_consciousness_statistics(
    authenticated: Annotated[str, Depends(verify_auth)],
) -> dict[str, Any]:
    """
    Get overall consciousness statistics across all agents.

    Returns aggregate metrics including:
    - Average phi scores
    - Free energy levels
    - Agent connectivity
    - Consciousness state distribution
    """
    plugin = get_consciousness_plugin()
    stats = plugin.get_statistics()
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        **stats,
    }


@router.get("/agents/{agent_id}")
async def get_agent_consciousness(
    agent_id: str,
    authenticated: Annotated[str, Depends(verify_auth)],
) -> dict[str, Any]:
    """
    Get detailed consciousness metrics for a specific agent.

    Returns:
    - IIT phi score and connectivity matrix
    - FEP metrics (surprise, free energy, prediction accuracy)
    - Current consciousness state
    - Historical trends
    """
    plugin = get_consciousness_plugin()
    metrics = plugin.get_agent_metrics(agent_id)

    if metrics is None:
        raise HTTPException(status_code=404, detail=f"No metrics found for agent {agent_id}")

    return {
        "agent_id": agent_id,
        "timestamp": datetime.now(UTC).isoformat(),
        **metrics,
    }


@router.get("/agents/{agent_id}/iit")
async def get_agent_iit_metrics(
    agent_id: str,
    authenticated: Annotated[str, Depends(verify_auth)],
) -> dict[str, Any]:
    """
    Get IIT (Integrated Information Theory) metrics for an agent.

    Returns:
    - Phi score (integration)
    - Connectivity matrix
    - Causal power distribution
    - Interaction history
    """
    plugin = get_consciousness_plugin()
    phi = plugin.calculate_iit_phi(agent_id)

    # Get connectivity details
    iit_calculator = plugin._iit_calculator
    connectivity = iit_calculator._build_connectivity_matrix()

    return {
        "agent_id": agent_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "phi_score": phi,
        "connectivity": connectivity,
        "average_phi": iit_calculator.get_average_phi(),
    }


@router.get("/agents/{agent_id}/fep")
async def get_agent_fep_metrics(
    agent_id: str,
    authenticated: Annotated[str, Depends(verify_auth)],
    window: int = Query(50, ge=1, le=500, description="Window size for averaging"),
) -> dict[str, Any]:
    """
    Get FEP (Free Energy Principle) metrics for an agent.

    Returns:
    - Prediction accuracy
    - Surprise levels
    - Free energy
    - Belief precision
    - Historical averages
    """
    plugin = get_consciousness_plugin()
    fep_tracker = plugin._fep_tracker

    metrics = fep_tracker.get_metrics(agent_id)
    if metrics is None:
        raise HTTPException(status_code=404, detail=f"No FEP metrics found for agent {agent_id}")

    avg_free_energy = fep_tracker.get_average_free_energy(agent_id, window)

    return {
        "agent_id": agent_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "metrics": metrics,
        "average_free_energy": avg_free_energy,
        "window_size": window,
    }


@router.get("/connectivity")
async def get_connectivity_matrix(
    authenticated: Annotated[str, Depends(verify_auth)],
) -> dict[str, Any]:
    """
    Get the agent connectivity matrix.

    Returns a matrix showing interaction frequencies and causal power
    between all agents in the swarm.
    """
    plugin = get_consciousness_plugin()
    iit_calculator = plugin._iit_calculator
    connectivity = iit_calculator._build_connectivity_matrix()

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "connectivity": connectivity,
        "agent_count": len(connectivity),
    }


@router.get("/states")
async def get_consciousness_states(
    authenticated: Annotated[str, Depends(verify_auth)],
) -> dict[str, Any]:
    """
    Get the current consciousness state of all agents.

    Returns mapping of agent IDs to their consciousness states:
    - DORMANT: Inactive or low consciousness
    - EMERGING: Developing consciousness
    - COHERENT: Stable, integrated consciousness
    - TRANSCENDENT: Highly integrated, emergent properties
    """
    plugin = get_consciousness_plugin()
    states = plugin._agent_states

    # Count states
    state_counts = {state.value: 0 for state in ConsciousnessState}
    for state in states.values():
        state_counts[state.value] += 1

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "states": {agent_id: state.value for agent_id, state in states.items()},
        "counts": state_counts,
        "total_agents": len(states),
    }


@router.get("/history")
async def get_consciousness_history(
    authenticated: Annotated[str, Depends(verify_auth)],
    agent_id: str | None = Query(None, description="Filter by specific agent"),
    hours: int = Query(24, ge=1, le=168, description="Hours of history to retrieve"),
) -> dict[str, Any]:
    """
    Get historical consciousness metrics.

    Returns time-series data for tracking consciousness evolution.
    """
    plugin = get_consciousness_plugin()
    iit_calculator = plugin._iit_calculator

    # Get interaction history
    cutoff_time = datetime.now(UTC) - timedelta(hours=hours)
    history = []

    for interaction in iit_calculator._interactions:
        interaction_time = datetime.fromisoformat(interaction["timestamp"])
        if interaction_time >= cutoff_time:
            if agent_id is None or interaction["from_agent"] == agent_id or interaction["to_agent"] == agent_id:
                history.append(interaction)

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "agent_id": agent_id,
        "hours": hours,
        "history": history,
        "count": len(history),
    }


@router.post("/record-interaction")
async def record_interaction(
    interaction: dict[str, Any],
    authenticated: Annotated[str, Depends(verify_auth)],
) -> dict[str, Any]:
    """
    Record an agent interaction for consciousness tracking.

    This endpoint is called by the system when agents interact with each other.
    """
    plugin = get_consciousness_plugin()

    from_agent = interaction.get("from_agent")
    to_agent = interaction.get("to_agent")
    interaction_type = interaction.get("type", "message")

    if not from_agent or not to_agent:
        raise HTTPException(status_code=400, detail="from_agent and to_agent are required")

    plugin.record_interaction(from_agent, to_agent, interaction_type)

    return {
        "status": "recorded",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.post("/record-prediction")
async def record_prediction(
    prediction: dict[str, Any],
    authenticated: Annotated[str, Depends(verify_auth)],
) -> dict[str, Any]:
    """
    Record an agent's prediction for FEP tracking.

    This endpoint is called when an agent makes a prediction.
    """
    plugin = get_consciousness_plugin()

    agent_id = prediction.get("agent_id")
    predicted_outcome = prediction.get("predicted_outcome")
    context = prediction.get("context", {})

    if not agent_id or predicted_outcome is None:
        raise HTTPException(status_code=400, detail="agent_id and predicted_outcome are required")

    plugin.record_prediction(agent_id, predicted_outcome, context)

    return {
        "status": "recorded",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.post("/record-outcome")
async def record_outcome(
    outcome: dict[str, Any],
    authenticated: Annotated[str, Depends(verify_auth)],
) -> dict[str, Any]:
    """
    Record an actual outcome for FEP tracking.

    This endpoint is called when the actual outcome of a prediction is known.
    """
    plugin = get_consciousness_plugin()

    agent_id = outcome.get("agent_id")
    actual_outcome = outcome.get("actual_outcome")

    if not agent_id or actual_outcome is None:
        raise HTTPException(status_code=400, detail="agent_id and actual_outcome are required")

    plugin.record_outcome(agent_id, actual_outcome)

    return {
        "status": "recorded",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/metrics/{agent_id}")
async def calculate_consciousness_metrics(
    agent_id: str,
    authenticated: str = Depends(verify_auth),
) -> dict[str, Any]:
    """
    Calculate comprehensive consciousness metrics for an agent.

    Combines IIT and FEP metrics into a unified consciousness score.
    """
    plugin = get_consciousness_plugin()
    metrics = plugin.calculate_consciousness_metrics(agent_id)

    if metrics is None:
        raise HTTPException(status_code=404, detail=f"Could not calculate metrics for agent {agent_id}")

    return {
        "agent_id": agent_id,
        "timestamp": datetime.now(UTC).isoformat(),
        **metrics,
    }


@router.get("/visualization/network")
async def get_network_visualization(
    authenticated: str = Depends(verify_auth),
) -> dict[str, Any]:
    """
    Get network visualization data for agent connectivity.

    Returns node-link data suitable for D3.js or similar visualization libraries.
    """
    plugin = get_consciousness_plugin()
    iit_calculator = plugin._iit_calculator
    connectivity = iit_calculator._build_connectivity_matrix()

    # Build nodes
    nodes = []
    for agent_id in connectivity.keys():
        phi = iit_calculator.get_average_phi()
        state = plugin._agent_states.get(agent_id, ConsciousnessState.DORMANT)
        nodes.append({
            "id": agent_id,
            "phi": phi,
            "state": state.value,
        })

    # Build links
    links = []
    for from_agent, connections in connectivity.items():
        for to_agent, weight in connections.items():
            if weight > 0:
                links.append({
                    "source": from_agent,
                    "target": to_agent,
                    "weight": weight,
                })

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "nodes": nodes,
        "links": links,
    }


@router.get("/visualization/timeseries")
async def get_timeseries_data(
    agent_id: str,
    metric: str = Query("phi", description="Metric to retrieve: phi, free_energy, surprise"),
    hours: int = Query(24, ge=1, le=168, description="Hours of data"),
    authenticated: str = Depends(verify_auth),
) -> dict[str, Any]:
    """
    Get time-series data for a specific metric.

    Returns data points suitable for line charts.
    """
    plugin = get_consciousness_plugin()
    iit_calculator = plugin._iit_calculator

    cutoff_time = datetime.now(UTC) - timedelta(hours=hours)
    data_points = []

    if metric == "phi":
        # Get phi over time from interactions
        for interaction in iit_calculator._interactions:
            interaction_time = datetime.fromisoformat(interaction["timestamp"])
            if interaction_time >= cutoff_time and interaction["from_agent"] == agent_id:
                data_points.append({
                    "timestamp": interaction["timestamp"],
                    "value": interaction.get("phi", 0),
                })
    elif metric in ["free_energy", "surprise"]:
        # Get FEP metrics
        fep_tracker = plugin._fep_tracker
        agent_predictions = fep_tracker._predictions.get(agent_id, [])
        for pred in agent_predictions:
            pred_time = datetime.fromisoformat(pred["timestamp"])
            if pred_time >= cutoff_time:
                value = pred.get(metric, 0) if metric == "free_energy" else pred.get("surprise", 0)
                data_points.append({
                    "timestamp": pred["timestamp"],
                    "value": value,
                })

    return {
        "agent_id": agent_id,
        "metric": metric,
        "hours": hours,
        "data_points": data_points,
        "count": len(data_points),
    }
