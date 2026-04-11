"""API Endpoints for Session 46."""

from datetime import datetime, timezone
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query

from heretek_swarm.collective import (
    CollectiveIntelligenceMetrics,
    EmergenceLevel,
    EmergentPatternClass,
    MetricsExporter,
)
from heretek_swarm.gateway.auth import verify_auth

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1/emergent-intelligence", tags=["emergent-intelligence"])

_metrics_instance: Optional[CollectiveIntelligenceMetrics] = None
_exporter_instance: Optional[MetricsExporter] = None


def get_metrics_instance() -> CollectiveIntelligenceMetrics:
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = CollectiveIntelligenceMetrics()
    return _metrics_instance


def get_exporter_instance() -> MetricsExporter:
    global _exporter_instance
    if _exporter_instance is None:
        _exporter_instance = MetricsExporter(get_metrics_instance())
    return _exporter_instance


@router.get("/dashboard")
async def get_dashboard_data(auth: dict = Depends(verify_auth)):
    try:
        metrics = get_metrics_instance()
        dashboard = metrics.get_dashboard_data()
        return {"success": True, "data": dashboard.to_dict(), "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        logger.error("dashboard_data_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


@router.get("/siq")
async def get_siq(
    auth: dict = Depends(verify_auth),
    include_history: bool = Query(False),
    history_limit: int = Query(20, ge=1, le=100),
):
    try:
        metrics = get_metrics_instance()
        siq = await metrics.calculate_siq()
        result = siq.to_dict()
        if include_history:
            limit = int(history_limit)
            result["history"] = [s.to_dict() for s in metrics._siq_history[-limit:]]
        return {"success": True, "data": result, "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        logger.error("siq_calculation_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


@router.get("/efficiency")
async def get_collective_efficiency(
    auth: dict = Depends(verify_auth),
    include_history: bool = Query(False),
    history_limit: int = Query(20, ge=1, le=100),
):
    try:
        metrics = get_metrics_instance()
        efficiency = await metrics.calculate_collective_efficiency()
        result = efficiency.to_dict()
        if include_history:
            limit = int(history_limit)
            result["history"] = [e.to_dict() for e in metrics._efficiency_history[-limit:]]
        return {"success": True, "data": result, "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        logger.error("efficiency_calculation_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


@router.get("/knowledge-transfer")
async def get_knowledge_transfer_metrics(
    auth: dict = Depends(verify_auth),
    include_history: bool = Query(False),
    history_limit: int = Query(20, ge=1, le=100),
):
    try:
        metrics = get_metrics_instance()
        transfer = await metrics.calculate_knowledge_transfer()
        result = transfer.to_dict()
        if include_history:
            limit = int(history_limit)
            result["history"] = [t.to_dict() for t in metrics._transfer_history[-limit:]]
        return {"success": True, "data": result, "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        logger.error("knowledge_transfer_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


@router.get("/emergence-coefficient")
async def get_emergence_coefficient(
    auth: dict = Depends(verify_auth),
    include_history: bool = Query(False),
    history_limit: int = Query(20, ge=1, le=100),
):
    try:
        metrics = get_metrics_instance()
        coefficient = await metrics.calculate_emergence_coefficient()
        result = coefficient.to_dict()
        if include_history:
            limit = int(history_limit)
            result["history"] = [e.to_dict() for e in metrics._emergence_history[-limit:]]
        return {"success": True, "data": result, "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        logger.error("emergence_coefficient_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


@router.get("/emergent-patterns")
async def get_emergent_patterns(
    auth: dict = Depends(verify_auth),
    pattern_class: Optional[EmergentPatternClass] = None,
    min_level: Optional[EmergenceLevel] = None,
    limit: int = Query(100, ge=1, le=500),
):
    try:
        metrics = get_metrics_instance()
        detector = metrics.emergence_detector
        patterns = detector.get_emergent_patterns(pattern_class=pattern_class, min_emergence_level=min_level, limit=limit)
        return {"success": True, "data": {"patterns": [p.to_dict() for p in patterns], "total_count": len(patterns), "statistics": detector.get_emergence_statistics()}, "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        logger.error("emergent_patterns_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


@router.get("/learning-rates")
async def get_learning_rates(
    auth: dict = Depends(verify_auth),
    agent_id: Optional[str] = None,
):
    try:
        metrics = get_metrics_instance()
        controller = metrics.learning_controller
        if agent_id:
            state = controller.get_agent_state(agent_id)
            convergence = controller.get_convergence_metrics(agent_id)
            data = {"agent_id": agent_id, "state": state.to_dict(), "convergence": convergence.to_dict()}
        else:
            states = controller.get_all_agent_states()
            data = {"agents": {aid: s.to_dict() for aid, s in states.items()}, "swarm_statistics": controller.get_swarm_statistics()}
        return {"success": True, "data": data, "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        logger.error("learning_rates_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


@router.get("/agent-adaptation")
async def get_agent_adaptation(
    auth: dict = Depends(verify_auth),
    agent_id: Optional[str] = None,
):
    try:
        metrics = get_metrics_instance()
        adaptor = metrics.agent_adaptor
        if agent_id:
            state = adaptor.get_adaptation_state(agent_id)
            history = adaptor.get_adaptation_history(agent_id, limit=20)
            audit = adaptor.get_audit_log(agent_id, limit=20)
            data = {"agent_id": agent_id, "state": state.to_dict(), "recent_adaptations": [h.to_dict() for h in history], "recent_audit": [a.to_dict() for a in audit]}
        else:
            data = {"swarm_statistics": adaptor.get_swarm_adaptation_stats(), "total_agents": len(adaptor._agent_states)}
        return {"success": True, "data": data, "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        logger.error("agent_adaptation_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


@router.get("/metrics-definitions")
async def get_metric_definitions(auth: dict = Depends(verify_auth)):
    try:
        metrics = get_metrics_instance()
        definitions = metrics.get_all_metric_definitions()
        return {"success": True, "data": {"definitions": [d.to_dict() for d in definitions], "total_count": len(definitions)}, "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        logger.error("metric_definitions_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


@router.get("/metrics/{metric_id}/timeseries")
async def get_metric_timeseries(
    metric_id: str,
    auth: dict = Depends(verify_auth),
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
):
    try:
        metrics = get_metrics_instance()
        from datetime import datetime as dt
        start = dt.fromisoformat(start_time) if start_time else None
        end = dt.fromisoformat(end_time) if end_time else None
        series = metrics.get_metric_time_series(metric_id, start_time=start, end_time=end)
        return {"success": True, "data": series.to_dict(), "timestamp": datetime.now(timezone.utc).isoformat()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid format: {str(e)}")
    except Exception as e:
        logger.error("metric_timeseries_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


@router.get("/export/summary")
async def export_summary(auth: dict = Depends(verify_auth)):
    try:
        exporter = get_exporter_instance()
        summary = exporter.export_summary()
        return {"success": True, "data": summary, "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        logger.error("export_summary_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


@router.get("/status")
async def get_emergent_intelligence_status(auth: dict = Depends(verify_auth)):
    try:
        metrics = get_metrics_instance()
        status = {
            "metrics": metrics.get_status(),
            "learning_controller": metrics.learning_controller.get_status(),
            "agent_adaptor": metrics.agent_adaptor.get_status(),
            "emergence_detector": metrics.emergence_detector.get_status(),
            "pattern_library": metrics.pattern_library.get_library_status() if metrics.pattern_library else None,
        }
        return {"success": True, "data": status, "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        logger.error("status_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")
