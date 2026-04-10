"""
Alerting System for Heretek Swarm

Provides structured alerting with PagerDuty and OpsGenie integration.

Alert Severity Levels:
- CRITICAL: Immediate attention required (system down)
- HIGH: Serious issue requiring attention
- MEDIUM: Moderate issue, should be addressed
- LOW: Minor issue, can be addressed later

Alert Sources:
- Agent health check failures
- Consensus failures
- API error rate thresholds
- Memory/database connection issues
- Phi score anomalies
- Free energy spikes

Author: Heretek Swarm Collective
Date: 2026-04-10
"""

import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog

_logger = structlog.get_logger("alerting")

# Alert severity levels
class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AlertStatus(str, Enum):
    FIRING = "firing"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"


@dataclass
class Alert:
    """Represents an alert in the system."""
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    severity: AlertSeverity = AlertSeverity.MEDIUM
    title: str = ""
    description: str = ""
    source: str = ""  # Component that triggered the alert
    status: AlertStatus = AlertStatus.FIRING
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: Optional[str] = None
    acknowledged_at: Optional[str] = None
    acknowledged_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "source": self.source,
            "status": self.status.value,
            "timestamp": self.timestamp,
            "resolved_at": self.resolved_at,
            "acknowledged_at": self.acknowledged_at,
            "acknowledged_by": self.acknowledged_by,
            "metadata": self.metadata,
            "tags": self.tags,
        }


class AlertManager:
    """
    Central alert management with PagerDuty/OpsGenie integration.
    """

    def __init__(self):
        self._alerts: Dict[str, Alert] = {}
        self._alert_history: List[Alert] = []
        self._pagerduty_enabled = bool(os.getenv("PAGERDUTY_API_KEY"))
        self._opsgenie_enabled = bool(os.getenv("OPSGENIE_API_KEY"))
        self._integration = os.getenv("ALERT_INTEGRATION", "none")  # pagerduty, opsgenie, both, none

    async def send_alert(self, alert: Alert) -> bool:
        """Send an alert through configured integration."""
        logger.info(
            "alert_triggered",
            alert_id=alert.alert_id,
            severity=alert.severity.value,
            title=alert.title,
            source=alert.source,
        )

        # Store alert
        self._alerts[alert.alert_id] = alert

        # Send to integrations
        _success = True
        if self._integration in ("pagerduty", "both") and self._pagerduty_enabled:
            _success = success and await self._send_pagerduty(alert)
        if self._integration in ("opsgenie", "both") and self._opsgenie_enabled:
            _success = success and await self._send_opsgenie(alert)

        return success

    async def _send_pagerduty(self, alert: Alert) -> bool:
        """Send alert to PagerDuty Events API v2."""
        try:
            import aiohttp
            
            _pd_urgency = "high" if alert.severity in (AlertSeverity.CRITICAL, AlertSeverity.HIGH) else "low"
            
            _payload = {
                "routing_key": os.getenv("PAGERDUTY_API_KEY"),
                "event_action": "trigger",
                "payload": {
                    "summary": alert.title,
                    "source": f"heretek-swarm:{alert.source}",
                    "severity": pd_urgency,
                    "custom_details": {
                        "description": alert.description,
                        "alert_id": alert.alert_id,
                        "metadata": alert.metadata,
                    }
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://events.pagerduty.com/v2/enqueue",
                    _json = payload,
                    _headers = {"Content-Type": "application/json"},
                ) as resp:
                    if resp.status == 202:
                        logger.info("pagerduty_alert_sent", alert_id=alert.alert_id)
                        return True
                    else:
                        logger.error("pagerduty_alert_failed", status=resp.status)
                        return False
        except Exception as e:
            logger.error("pagerduty_alert_error", error=str(e))
            return False

    async def _send_opsgenie(self, alert: Alert) -> bool:
        """Send alert to OpsGenie Alerts API."""
        try:
            import aiohttp
            
            _opsgenie_priority = "P1" if alert.severity == AlertSeverity.CRITICAL else \
                              "P2" if alert.severity == AlertSeverity.HIGH else \
                              "P3" if alert.severity == AlertSeverity.MEDIUM else "P4"
            
            _payload = {
                "message": alert.title,
                "description": alert.description,
                "priority": opsgenie_priority,
                "tags": alert.tags,
                "extra_properties": {
                    "alert_id": alert.alert_id,
                    "source": alert.source,
                    **alert.metadata,
                }
            }

            _headers = {
                "Content-Type": "application/json",
                "Authorization": f"GenieKey {os.getenv('OPSGENIE_API_KEY')}",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.opsgenie.com/v2/alerts",
                    _json = payload,
                    _headers = headers,
                ) as resp:
                    if resp.status == 202:
                        logger.info("opsgenie_alert_sent", alert_id=alert.alert_id)
                        return True
                    else:
                        logger.error("opsgenie_alert_failed", status=resp.status)
                        return False
        except Exception as e:
            logger.error("opsgenie_alert_error", error=str(e))
            return False

    async def resolve_alert(self, alert_id: str, resolved_by: str) -> bool:
        """Resolve an alert."""
        if alert_id not in self._alerts:
            return False

        _alert = self._alerts[alert_id]
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now(timezone.utc).isoformat()
        
        # Move to history
        self._alert_history.append(alert)
        del self._alerts[alert_id]

        logger.info("alert_resolved", alert_id=alert_id, resolved_by=resolved_by)
        return True

    def get_active_alerts(self) -> List[Alert]:
        """Get all active (firing) alerts."""
        return list(self._alerts.values())

    def get_alert_history(self, limit: int) -> List[Alert]:
        """Get alert history."""
        return self._alert_history[-limit:]

    async def check_and_alert(self, check_type: str, value: float, threshold: float, severity: AlertSeverity, title: str, description: str, source: str) -> Optional[Alert]:
        """Check a value against threshold and alert if exceeded."""
        if check_type == "above" and value > threshold:
            pass  # Alert
        elif check_type == "below" and value < threshold:
            pass  # Alert
        elif check_type == "equals" and abs(value - threshold) < 0.001:
            pass  # Alert
        else:
            return None  # No alert needed

        _alert = Alert(
            _severity = severity,
            _title = title,
            _description = description,
            _source = source,
            _metadata = {"value": value, "threshold": threshold, "check_type": check_type},
        )
        await self.send_alert(alert)
        return alert


# Global alert manager instance
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get the global alert manager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager
