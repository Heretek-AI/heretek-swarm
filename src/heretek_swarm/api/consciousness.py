"""
Consciousness Metrics API

Provides endpoints for accessing enhanced consciousness metrics including
IIT (Integrated Information Theory) scores, FEP (Free Energy Principle) metrics,
and agent connectivity analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from ..gateway.auth import verify_auth
from ..plugins.consciousness_enhanced import (
    EnhancedConsciousnessPlugin,
    ConsciousnessState,
)
from ..plugins.manager import plugin_manager

router = APIRouter(prefix="/api/consciousness", tags=["consciousness"])


def get_consciousness_plugin() -> Optional[EnhancedConsciousnessPlugin]:
    """Get the consciousness plugin instance."""
    plugin = plugin_manager.get_plugin("consciousness_enhanced")
    if plugin is None:
        raise HTTPException(status_code=503, detail="Consciousness plugin not available")
    return plugin


@router.get("/statistics")
async def get_consciousness_statistics(
    authenticated: str = Depends(verify_auth),
) -> Dict[str, Any]:
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **stats,
    }


@router.get("/agents/{agent_id}")
async def get_agent_consciousness(
    agent_id: str,
    authenticated: str = Depends(verify_auth),
) -> Dict[str, Any]:
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **metrics,
    }


@router.get("/agents/{agent_id}/iit")
async def get_agent_iit_metrics(
    agent_id: str,
    authenticated: str = Depends(verify_auth),
) -> Dict[str, Any]:
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phi_score": phi,
        "connectivity": connectivity,
        "average_phi": iit_calculator.get_average_phi(),
    }


@router.get("/agents/{agent_id}/fep")
async def get_agent_fep_metrics(
    agent_id: str,
    window: int = Query(50, ge=1, le=500, description="Window size for averaging"),
    authenticated: str = Depends(verify_auth),
) -> Dict[str, Any]:
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "average_free_energy": avg_free_energy,
        "window_size": window,
    }


@router.get("/connectivity")
async def get_connectivity_matrix(
    authenticated: str = Depends(verify_auth),
) -> Dict[str, Any]:
    """
    Get the agent connectivity matrix.

    Returns a matrix showing interaction frequencies and causal power
    between all agents in the swarm.
    """
    plugin = get_consciousness_plugin()
    iit_calculator = plugin._iit_calculator
    connectivity = iit_calculator._build_connectivity_matrix()

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "connectivity": connectivity,
        "agent_count": len(connectivity),
    }


@router.get("/states")
async def get_consciousness_states(
    authenticated: str = Depends(verify_auth),
) -> Dict[str, Any]:
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "states": {agent_id: state.value for agent_id, state in states.items()},
        "counts": state_counts,
        "total_agents": len(states),
    }


@router.get("/history")
async def get_consciousness_history(
    agent_id: Optional[str] = Query(None, description="Filter by specific agent"),
    hours: int = Query(24, ge=1, le=168, description="Hours of history to retrieve"),
    authenticated: str = Depends(verify_auth),
) -> Dict[str, Any]:
    """
    Get historical consciousness metrics.

    Returns time-series data for tracking consciousness evolution.
    """
    plugin = get_consciousness_plugin()
    iit_calculator = plugin._iit_calculator

    # Get interaction history
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    history = []

    for interaction in iit_calculator._interactions:
        interaction_time = datetime.fromisoformat(interaction["timestamp"])
        if interaction_time >= cutoff_time:
            if agent_id is None or interaction["from_agent"] == agent_id or interaction["to_agent"] == agent_id:
                history.append(interaction)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_id": agent_id,
        "hours": hours,
        "history": history,
        "count": len(history),
    }


@router.post("/record-interaction")
async def record_interaction(
    interaction: Dict[str, Any],
    authenticated: str = Depends(verify_auth),
) -> Dict[str, Any]:
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/record-prediction")
async def record_prediction(
    prediction: Dict[str, Any],
    authenticated: str = Depends(verify_auth),
) -> Dict[str, Any]:
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/record-outcome")
async def record_outcome(
    outcome: Dict[str, Any],
    authenticated: str = Depends(verify_auth),
) -> Dict[str, Any]:
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/metrics/{agent_id}")
async def calculate_consciousness_metrics(
    agent_id: str,
    authenticated: str = Depends(verify_auth),
) -> Dict[str, Any]:
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **metrics,
    }


@router.get("/visualization/network")
async def get_network_visualization(
    authenticated: str = Depends(verify_auth),
) -> Dict[str, Any]:
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "nodes": nodes,
        "links": links,
    }


@router.get("/visualization/timeseries")
async def get_timeseries_data(
    agent_id: str,
    metric: str = Query("phi", description="Metric to retrieve: phi, free_energy, surprise"),
    hours: int = Query(24, ge=1, le=168, description="Hours of data"),
    authenticated: str = Depends(verify_auth),
) -> Dict[str, Any]:
    """
    Get time-series data for a specific metric.

    Returns data points suitable for line charts.
    """
    plugin = get_consciousness_plugin()
    iit_calculator = plugin._iit_calculator

    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
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
