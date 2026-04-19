"""
Alerts API Endpoints

Provides HTTP endpoints for alert management:
- GET /api/alerts - List active alerts
- POST /api/alerts - Create a new alert
- PUT /api/alerts/{id}/resolve - Resolve an alert
- POST /api/alerts/test - Test alert configuration
- GET /api/alerts/history - Get alert history
"""

from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from heretek_swarm.gateway.auth import verify_auth
from heretek_swarm.observability.alerting import (
    Alert,
    AlertSeverity,
    get_alert_manager,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


class CreateAlertRequest(BaseModel):
    severity: str = "medium"
    title: str
    description: str
    source: str
    tags: list[str] = []


@router.get("")
async def get_active_alerts(auth: dict = Depends(verify_auth)) -> dict:
    """Get all active (firing) alerts."""
    manager = get_alert_manager()
    alerts = manager.get_active_alerts()
    return {
        "success": True,
        "count": len(alerts),
        "alerts": [a.to_dict() for a in alerts],
    }


@router.get("/history")
async def get_alert_history(
    auth: dict = Depends(verify_auth),
    limit: int = Query(100, ge=1, le=1000),
) -> dict:
    """Get resolved alert history."""
    manager = get_alert_manager()
    history = manager.get_alert_history(limit)
    return {
        "success": True,
        "count": len(history),
        "alerts": [a.to_dict() for a in history],
    }


@router.post("")
async def create_alert(
    request: CreateAlertRequest,
    auth: dict = Depends(verify_auth),
) -> dict:
    """Create a new alert."""
    manager = get_alert_manager()

    try:
        severity = AlertSeverity(request.severity.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid severity: {request.severity}")

    alert = Alert(
        severity=severity,
        title=request.title,
        description=request.description,
        source=request.source,
        tags=request.tags,
    )

    success = await manager.send_alert(alert)

    return {
        "success": success,
        "alert": alert.to_dict(),
    }


@router.put("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    auth: dict = Depends(verify_auth),
) -> dict:
    """Resolve an alert."""
    manager = get_alert_manager()
    success = await manager.resolve_alert(alert_id, resolved_by=auth.get("agent_id", "api"))

    if not success:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    return {
        "success": True,
        "alert_id": alert_id,
        "resolved_at": datetime.now(UTC).isoformat(),
    }


@router.post("/test")
async def test_alert_configuration(auth: dict = Depends(verify_auth)) -> dict:
    """Test alert configuration by sending a test alert."""
    manager = get_alert_manager()

    test_alert = Alert(
        severity=AlertSeverity.LOW,
        title="Heretek Swarm Test Alert",
        description="This is a test alert to verify alerting configuration.",
        source="api.test",
        tags=["test"],
    )

    success = await manager.send_alert(test_alert)

    # Resolve immediately
    await manager.resolve_alert(test_alert.alert_id, resolved_by="api.test")

    return {
        "success": success,
        "message": "Test alert sent and resolved",
        "alert_id": test_alert.alert_id,
    }
