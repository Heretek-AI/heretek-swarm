"""
Sentinel-Prime Agent - Security Commander & Threat Response.

Sentinel-Prime provides:
- Active threat detection and response
- Security incident management
- Intrusion detection and prevention
- Threat intelligence aggregation
- Security policy enforcement
- Incident response automation

Sentinel-Prime is the "security commander" of the Collective, responsible for
identifying, analyzing, and responding to security threats in real-time.
"""

import asyncio
import logging
import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from pydantic import BaseModel, Field, ValidationError
import structlog
from swarms import Agent

from heretek_swarm.actors.base import AgentActor, ActorMessage
from heretek_swarm.actors.validation import validate_message, MessageContent

logger = structlog.get_logger("SentinelPrimeAgent")


class ThreatLevel(str, Enum):
    """Threat severity classification."""
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(str, Enum):
    """Types of security threats."""
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_EXFILTRATION = "data_exfiltration"
    MALWARE = "malware"
    PHISHING = "phishing"
    DOS_ATTACK = "dos_attack"
    MAN_IN_THE_MIDDLE = "man_in_the_middle"
    SQL_INJECTION = "sql_injection"
    XSS_ATTACK = "xss_attack"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    CREDENTIAL_STUFFING = "credential_stuffing"
    BRUTE_FORCE = "brute_force"
    SUSPICIOUS_BEHAVIOR = "suspicious_behavior"
    POLICY_VIOLATION = "policy_violation"
    ZERO_DAY_EXPLOIT = "zero_day_exploit"


class IncidentStatus(str, Enum):
    """Security incident status."""
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    REMEDIATED = "remediated"
    CLOSED = "closed"
    ESCALATED = "escalated"


class ResponseAction(str, Enum):
    """Automated response actions."""
    ALERT = "alert"
    BLOCK = "block"
    ISOLATE = "isolate"
    TERMINATE = "terminate"
    QUARANTINE = "quarantine"
    RATE_LIMIT = "rate_limit"
    BLACKLIST = "blacklist"
    NOTIFY = "notify"
    LOG_ONLY = "log_only"


@dataclass
class ThreatIndicator:
    """Individual threat indicator."""
    indicator_id: str
    indicator_type: str  # IP, domain, hash, pattern, behavior
    value: str
    confidence: float  # 0.0 - 1.0
    first_seen: datetime
    last_seen: datetime
    source: str
    tags: List[str] = field(default_factory=list)


@dataclass
class SecurityIncident:
    """Security incident record."""
    incident_id: str
    threat_type: ThreatType
    threat_level: ThreatLevel
    status: IncidentStatus
    timestamp: datetime
    source_actor: Optional[str] = None
    target_actor: Optional[str] = None
    target_resource: Optional[str] = None
    indicators: List[ThreatIndicator] = field(default_factory=list)
    response_actions: List[ResponseAction] = field(default_factory=list)
    description: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    remediation_steps: List[str] = field(default_factory=list)
    closed_at: Optional[datetime] = None


@dataclass
class ThreatReport:
    """Aggregated threat intelligence report."""
    report_id: str
    timestamp: datetime
    time_range: str
    total_incidents: int
    incidents_by_level: Dict[str, int]
    incidents_by_type: Dict[str, int]
    active_threats: int
    contained_threats: int
    top_indicators: List[Dict[str, Any]]
    recommendations: List[str]


class SentinelPrimeAgent(AgentActor):
    """
    Sentinel-Prime Agent - Security Commander for the Heretek Swarm Collective.
    
    Sentinel-Prime provides active threat detection, incident response, and
    security intelligence for the Collective.
    """
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        name: str = "Sentinel-Prime",
        description: str = "Security Commander - Threat Response",
        config: Optional[Dict[str, Any]] = None,
        db_pool: Optional[Any] = None,
        redis_client: Optional[Any] = None,
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            config=config,
            db_pool=db_pool,
            redis_client=redis_client,
        )
        
        # Security configuration
        self._auto_response_enabled = config.get("auto_response_enabled", True) if config else True
        self._alert_threshold = config.get("alert_threshold", ThreatLevel.MEDIUM.value) if config else ThreatLevel.MEDIUM.value
        self._max_incidents = config.get("max_incidents", 5000) if config else 5000
        self._correlation_window = config.get("correlation_window", 300) if config else 300  # seconds
        
        # Security state
        self._incidents: Dict[str, SecurityIncident] = {}
        self._incident_history: List[str] = []  # LRU keys
        self._threat_indicators: Dict[str, ThreatIndicator] = {}
        self._indicator_cache: Dict[str, ThreatIndicator] = {}  # LRU cache
        self._max_indicator_cache = 10000
        
        # Rate limiting state
        self._rate_limits: Dict[str, Dict[str, Any]] = {}
        self._blocked_sources: Set[str] = set()
        self._isolated_actors: Set[str] = set()
        
        # Statistics
        self._stats = {
            "total_incidents": 0,
            "incidents_by_level": defaultdict(int),
            "incidents_by_type": defaultdict(int),
            "auto_responses_triggered": 0,
            "manual_responses_triggered": 0,
            "threats_contained": 0,
            "threats_mitigated": 0,
        }
        
        # Threat patterns
        self._attack_patterns = [
            (r"(?i)union\s+select", ThreatType.SQL_INJECTION),
            (r"(?i)or\s+1\s*=\s*1", ThreatType.SQL_INJECTION),
            (r"(?i)drop\s+table", ThreatType.SQL_INJECTION),
            (r"(?i)<script[^>]*>", ThreatType.XSS_ATTACK),
            (r"(?i)javascript:", ThreatType.XSS_ATTACK),
            (r"(?i)on\w+\s*=", ThreatType.XSS_ATTACK),
            (r"(?i)passwd|password|secret|api_key|token", ThreatType.DATA_EXFILTRATION),
            (r"(?i)/etc/passwd|/etc/shadow", ThreatType.UNAUTHORIZED_ACCESS),
            (r"(?i)\.\./", ThreatType.UNAUTHORIZED_ACCESS),
            (r"(?i)cmd\.exe|powershell|/bin/sh|/bin/bash", ThreatType.PRIVILEGE_ESCALATION),
        ]
        
        self._compiled_patterns = [
            (re.compile(pattern), threat_type)
            for pattern, threat_type in self._attack_patterns
        ]
        
        logger.info(
            "Sentinel-Prime Agent initialized",
            agent_id=self.agent_id,
            auto_response=self._auto_response_enabled,
            alert_threshold=self._alert_threshold,
        )
    
    async def process_message(self, message: ActorMessage) -> None:
        """Process incoming message with security validation."""
        try:
            handler = self._message_handlers.get(message.message_type)
            if handler:
                await handler(message)
            else:
                logger.warning(
                    "Unknown message type",
                    message_type=message.message_type,
                    sender=message.sender_id,
                )
        except Exception as e:
            logger.error(
                "Error processing message",
                message_type=message.message_type,
                error=str(e),
                exc_info=True,
            )
    
    def _register_handlers(self) -> None:
        """Register message handlers."""
        self._message_handlers = {
            "report_threat": self._handle_report_threat,
            "analyze_threat": self._handle_analyze_threat,
            "get_incident_details": self._handle_get_incident_details,
            "get_active_incidents": self._handle_get_active_incidents,
            "respond_to_incident": self._handle_respond_to_incident,
            "add_threat_indicator": self._handle_add_threat_indicator,
            "check_indicator": self._handle_check_indicator,
            "get_threat_report": self._handle_get_threat_report,
            "block_source": self._handle_block_source,
            "isolate_actor": self._handle_isolate_actor,
            "get_statistics": self._handle_get_statistics,
            "update_config": self._handle_update_config,
        }
    
    async def _handle_report_threat(self, message: ActorMessage) -> None:
        """
        Report a potential security threat.
        
        Content: {
            "threat_type": str,
            "threat_level": str (optional),
            "source": str (optional),
            "target": str (optional),
            "description": str,
            "evidence": Dict (optional),
            "indicators": List[Dict] (optional)
        }
        """
        try:
            content = message.content
            threat_type_str = content.get("threat_type")
            threat_level_str = content.get("threat_level", ThreatLevel.MEDIUM.value)
            source = content.get("source")
            target = content.get("target")
            description = content.get("description", "")
            evidence = content.get("evidence", {})
            indicators = content.get("indicators", [])
            
            # Validate
            validated = validate_message({
                "sender_id": message.sender_id,
                "message_type": "report_threat",
                "content": content,
                "timestamp": message.timestamp,
            })
            
            # Convert enums
            try:
                threat_type = ThreatType(threat_type_str)
            except ValueError:
                threat_type = ThreatType.SUSPICIOUS_BEHAVIOR
            
            try:
                threat_level = ThreatLevel(threat_level_str)
            except ValueError:
                threat_level = ThreatLevel.MEDIUM
            
            # Create incident
            incident_id = self._create_incident_id()
            incident = SecurityIncident(
                incident_id=incident_id,
                threat_type=threat_type,
                threat_level=threat_level,
                status=IncidentStatus.DETECTED,
                timestamp=datetime.now(timezone.utc),
                source_actor=source,
                target_actor=target,
                description=description,
                evidence=evidence,
            )
            
            # Add indicators
            for ind_data in indicators:
                indicator = self._create_indicator(ind_data)
                if indicator:
                    incident.indicators.append(indicator)
                    self._threat_indicators[indicator.indicator_id] = indicator
            
            # Store incident
            self._incidents[incident_id] = incident
            self._incident_history.append(incident_id)
            
            # Update statistics
            self._stats["total_incidents"] += 1
            self._stats["incidents_by_level"][threat_level.value] += 1
            self._stats["incidents_by_type"][threat_type.value] += 1
            
            # Auto-respond if enabled and threat level is high enough
            response_actions = []
            if self._auto_response_enabled:
                response_actions = await self._auto_respond(incident)
                incident.response_actions = response_actions
            
            # LRU cleanup
            if len(self._incident_history) > self._max_incidents:
                oldest = self._incident_history.pop(0)
                self._incidents.pop(oldest, None)
            
            logger.warning(
                "Security threat reported",
                incident_id=incident_id,
                threat_type=threat_type.value,
                threat_level=threat_level.value,
                source=source,
                target=target,
                auto_response=len(response_actions) > 0,
            )
            
            response_content = {
                "incident_id": incident_id,
                "status": incident.status.value,
                "threat_level": threat_level.value,
                "auto_response_triggered": len(response_actions) > 0,
                "response_actions": [a.value for a in response_actions],
                "recommendations": self._generate_recommendations(incident),
            }
            
            await self._send_response(message, response_content)
            
        except ValidationError as ve:
            logger.warning("Validation error", error=str(ve))
            await self._send_error(message, "Invalid threat report", str(ve))
        except Exception as e:
            logger.error("Error reporting threat", error=str(e), exc_info=True)
            await self._send_error(message, "Threat report failed", str(e))
    
    async def _handle_analyze_threat(self, message: ActorMessage) -> None:
        """
        Analyze a reported threat for correlation and severity.
        
        Content: {
            "incident_id": str,
            "correlate": bool (optional),
            "deep_analysis": bool (optional)
        }
        """
        try:
            content = message.content
            incident_id = content.get("incident_id")
            correlate = content.get("correlate", True)
            deep_analysis = content.get("deep_analysis", False)
            
            if not incident_id:
                await self._send_error(message, "Missing incident_id")
                return
            
            incident = self._incidents.get(incident_id)
            if not incident:
                await self._send_error(message, "Incident not found", incident_id)
                return
            
            # Perform analysis
            analysis_result = {
                "incident_id": incident_id,
                "severity_score": self._calculate_severity_score(incident),
                "correlated_incidents": [],
                "attack_chain": [],
                "ioc_matches": [],
                "mitre_techniques": [],
            }
            
            # Correlation analysis
            if correlate:
                correlated = self._find_correlated_incidents(incident)
                analysis_result["correlated_incidents"] = [
                    {"incident_id": c.incident_id, "correlation_score": 0.8}
                    for c in correlated[:5]
                ]
            
            # Deep analysis
            if deep_analysis:
                analysis_result["attack_chain"] = self._reconstruct_attack_chain(incident)
                analysis_result["ioc_matches"] = self._match_iocs(incident)
                analysis_result["mitre_techniques"] = self._map_mitre_techniques(incident)
            
            response_content = {
                "incident_id": incident_id,
                "analysis": analysis_result,
                "updated_threat_level": incident.threat_level.value,
            }
            
            await self._send_response(message, response_content)
            
        except Exception as e:
            logger.error("Error analyzing threat", error=str(e), exc_info=True)
            await self._send_error(message, "Threat analysis failed", str(e))
    
    async def _handle_get_incident_details(self, message: ActorMessage) -> None:
        """
        Get detailed information about a specific incident.
        
        Content: {
            "incident_id": str
        }
        """
        try:
            content = message.content
            incident_id = content.get("incident_id")
            
            if not incident_id:
                await self._send_error(message, "Missing incident_id")
                return
            
            incident = self._incidents.get(incident_id)
            if not incident:
                await self._send_error(message, "Incident not found", incident_id)
                return
            
            response_content = {
                "incident_id": incident.incident_id,
                "threat_type": incident.threat_type.value,
                "threat_level": incident.threat_level.value,
                "status": incident.status.value,
                "timestamp": incident.timestamp.isoformat(),
                "source_actor": incident.source_actor,
                "target_actor": incident.target_actor,
                "target_resource": incident.target_resource,
                "description": incident.description,
                "indicators": [
                    {
                        "indicator_id": i.indicator_id,
                        "type": i.indicator_type,
                        "value": i.value,
                        "confidence": i.confidence,
                    }
                    for i in incident.indicators
                ],
                "response_actions": [a.value for a in incident.response_actions],
                "remediation_steps": incident.remediation_steps,
                "evidence": incident.evidence,
            }
            
            await self._send_response(message, response_content)
            
        except Exception as e:
            logger.error("Error getting incident details", error=str(e), exc_info=True)
            await self._send_error(message, "Failed to get incident details", str(e))
    
    async def _handle_get_active_incidents(self, message: ActorMessage) -> None:
        """
        Get all active (non-closed) incidents.
        
        Content: {
            "threat_level_filter": str (optional),
            "limit": int (optional)
        }
        """
        try:
            content = message.content
            threat_level_filter = content.get("threat_level_filter")
            limit = content.get("limit", 100)
            
            active_incidents = [
                inc for inc in self._incidents.values()
                if inc.status not in [IncidentStatus.CLOSED, IncidentStatus.REMEDIATED]
            ]
            
            # Filter by threat level
            if threat_level_filter:
                try:
                    min_level = ThreatLevel(threat_level_filter)
                    level_order = {
                        ThreatLevel.INFORMATIONAL: 0,
                        ThreatLevel.LOW: 1,
                        ThreatLevel.MEDIUM: 2,
                        ThreatLevel.HIGH: 3,
                        ThreatLevel.CRITICAL: 4,
                    }
                    min_order = level_order.get(min_level, 0)
                    active_incidents = [
                        inc for inc in active_incidents
                        if level_order.get(inc.threat_level, 0) >= min_order
                    ]
                except ValueError:
                    pass
            
            # Sort by threat level (highest first)
            level_order = {
                ThreatLevel.CRITICAL: 4,
                ThreatLevel.HIGH: 3,
                ThreatLevel.MEDIUM: 2,
                ThreatLevel.LOW: 1,
                ThreatLevel.INFORMATIONAL: 0,
            }
            active_incidents.sort(
                key=lambda x: level_order.get(x.threat_level, 0),
                reverse=True,
            )
            
            # Apply limit
            active_incidents = active_incidents[:limit]
            
            response_content = {
                "active_incidents_count": len(active_incidents),
                "incidents": [
                    {
                        "incident_id": inc.incident_id,
                        "threat_type": inc.threat_type.value,
                        "threat_level": inc.threat_level.value,
                        "status": inc.status.value,
                        "timestamp": inc.timestamp.isoformat(),
                        "source_actor": inc.source_actor,
                        "target_actor": inc.target_actor,
                    }
                    for inc in active_incidents
                ],
            }
            
            await self._send_response(message, response_content)
            
        except Exception as e:
            logger.error("Error getting active incidents", error=str(e), exc_info=True)
            await self._send_error(message, "Failed to get active incidents", str(e))
    
    async def _handle_respond_to_incident(self, message: ActorMessage) -> None:
        """
        Execute response actions for an incident.
        
        Content: {
            "incident_id": str,
            "actions": List[str],
            "manual": bool (optional)
        }
        """
        try:
            content = message.content
            incident_id = content.get("incident_id")
            actions = content.get("actions", [])
            manual = content.get("manual", False)
            
            if not incident_id:
                await self._send_error(message, "Missing incident_id")
                return
            
            incident = self._incidents.get(incident_id)
            if not incident:
                await self._send_error(message, "Incident not found", incident_id)
                return
            
            executed_actions = []
            
            for action_str in actions:
                try:
                    action = ResponseAction(action_str)
                    result = await self._execute_response_action(incident, action)
                    if result:
                        executed_actions.append(action)
                        incident.response_actions.append(action)
                except ValueError:
                    logger.warning("Unknown response action", action=action_str)
            
            # Update incident status
            if executed_actions:
                if ResponseAction.CONTAINED in executed_actions or ResponseAction.ISOLATE in executed_actions:
                    incident.status = IncidentStatus.CONTAINED
                elif ResponseAction.REMEDIATED in executed_actions:
                    incident.status = IncidentStatus.REMEDIATED
            
            # Update statistics
            if manual:
                self._stats["manual_responses_triggered"] += len(executed_actions)
            else:
                self._stats["auto_responses_triggered"] += len(executed_actions)
            
            response_content = {
                "incident_id": incident_id,
                "executed_actions": [a.value for a in executed_actions],
                "new_status": incident.status.value,
                "success": len(executed_actions) > 0,
            }
            
            await self._send_response(message, response_content)
            
        except Exception as e:
            logger.error("Error responding to incident", error=str(e), exc_info=True)
            await self._send_error(message, "Response execution failed", str(e))
    
    async def _handle_add_threat_indicator(self, message: ActorMessage) -> None:
        """
        Add a threat indicator to the intelligence database.
        
        Content: {
            "indicator_type": str,
            "value": str,
            "confidence": float (optional),
            "source": str (optional),
            "tags": List[str] (optional)
        }
        """
        try:
            content = message.content
            indicator_data = {
                "indicator_type": content.get("indicator_type", "unknown"),
                "value": content.get("value", ""),
                "confidence": content.get("confidence", 0.5),
                "source": content.get("source", "manual"),
                "tags": content.get("tags", []),
            }
            
            indicator = self._create_indicator(indicator_data)
            if not indicator:
                await self._send_error(message, "Invalid indicator data")
                return
            
            self._threat_indicators[indicator.indicator_id] = indicator
            
            # Update cache
            self._indicator_cache[indicator.value] = indicator
            if len(self._indicator_cache) > self._max_indicator_cache:
                # Remove oldest
                oldest_key = next(iter(self._indicator_cache))
                self._indicator_cache.pop(oldest_key)
            
            response_content = {
                "indicator_id": indicator.indicator_id,
                "type": indicator.indicator_type,
                "value": indicator.value,
                "confidence": indicator.confidence,
                "success": True,
            }
            
            await self._send_response(message, response_content)
            
        except Exception as e:
            logger.error("Error adding threat indicator", error=str(e), exc_info=True)
            await self._send_error(message, "Failed to add indicator", str(e))
    
    async def _handle_check_indicator(self, message: ActorMessage) -> None:
        """
        Check if a value matches any known threat indicator.
        
        Content: {
            "value": str,
            "indicator_type": str (optional)
        }
        """
        try:
            content = message.content
            value = content.get("value", "")
            indicator_type = content.get("indicator_type")
            
            # Check cache first
            cached = self._indicator_cache.get(value)
            if cached:
                response_content = {
                    "value": value,
                    "match_found": True,
                    "indicator": {
                        "indicator_id": cached.indicator_id,
                        "type": cached.indicator_type,
                        "confidence": cached.confidence,
                        "tags": cached.tags,
                    },
                    "source": "cache",
                }
                await self._send_response(message, response_content)
                return
            
            # Check all indicators
            for indicator in self._threat_indicators.values():
                if indicator.value == value:
                    if indicator_type and indicator.indicator_type != indicator_type:
                        continue
                    
                    response_content = {
                        "value": value,
                        "match_found": True,
                        "indicator": {
                            "indicator_id": indicator.indicator_id,
                            "type": indicator.indicator_type,
                            "confidence": indicator.confidence,
                            "tags": indicator.tags,
                        },
                        "source": "database",
                    }
                    await self._send_response(message, response_content)
                    return
            
            response_content = {
                "value": value,
                "match_found": False,
                "source": "not_found",
            }
            await self._send_response(message, response_content)
            
        except Exception as e:
            logger.error("Error checking indicator", error=str(e), exc_info=True)
            await self._send_error(message, "Indicator check failed", str(e))
    
    async def _handle_get_threat_report(self, message: ActorMessage) -> None:
        """
        Generate comprehensive threat intelligence report.
        
        Content: {
            "time_range": str (optional),
            "include_indicators": bool (optional),
            "include_recommendations": bool (optional)
        }
        """
        try:
            content = message.content
            time_range = content.get("time_range", "24h")
            include_indicators = content.get("include_indicators", False)
            include_recommendations = content.get("include_recommendations", True)
            
            # Calculate statistics
            incidents_by_level = dict(self._stats["incidents_by_level"])
            incidents_by_type = dict(self._stats["incidents_by_type"])
            
            active_threats = sum(
                1 for inc in self._incidents.values()
                if inc.status in [IncidentStatus.DETECTED, IncidentStatus.INVESTIGATING]
            )
            contained_threats = sum(
                1 for inc in self._incidents.values()
                if inc.status in [IncidentStatus.CONTAINED, IncidentStatus.REMEDIATED]
            )
            
            # Get top indicators
            top_indicators = []
            if include_indicators:
                sorted_indicators = sorted(
                    self._threat_indicators.values(),
                    key=lambda x: x.confidence,
                    reverse=True,
                )[:20]
                top_indicators = [
                    {
                        "indicator_id": i.indicator_id,
                        "type": i.indicator_type,
                        "value": i.value,
                        "confidence": i.confidence,
                        "tags": i.tags,
                    }
                    for i in sorted_indicators
                ]
            
            # Generate recommendations
            recommendations = []
            if include_recommendations:
                recommendations = self._generate_strategic_recommendations()
            
            report = {
                "report_id": f"threat_report_{datetime.now(timezone.utc).timestamp()}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "time_range": time_range,
                "total_incidents": self._stats["total_incidents"],
                "incidents_by_level": incidents_by_level,
                "incidents_by_type": incidents_by_type,
                "active_threats": active_threats,
                "contained_threats": contained_threats,
                "top_indicators": top_indicators,
                "recommendations": recommendations,
                "auto_response_stats": {
                    "auto_responses": self._stats["auto_responses_triggered"],
                    "manual_responses": self._stats["manual_responses_triggered"],
                },
            }
            
            await self._send_response(message, {"report": report})
            
        except Exception as e:
            logger.error("Error generating threat report", error=str(e), exc_info=True)
            await self._send_error(message, "Threat report generation failed", str(e))
    
    async def _handle_block_source(self, message: ActorMessage) -> None:
        """
        Block a source from communicating with the Collective.
        
        Content: {
            "source": str,
            "duration": int (optional, seconds),
            "reason": str (optional)
        }
        """
        try:
            content = message.content
            source = content.get("source")
            duration = content.get("duration")
            reason = content.get("reason", "manual_block")
            
            if not source:
                await self._send_error(message, "Missing source")
                return
            
            self._blocked_sources.add(source)
            
            # Schedule unblock if duration specified
            if duration:
                asyncio.create_task(self._schedule_unblock(source, duration))
            
            logger.warning(
                "Source blocked",
                source=source,
                duration=duration,
                reason=reason,
            )
            
            response_content = {
                "source": source,
                "blocked": True,
                "duration": duration,
                "reason": reason,
            }
            
            await self._send_response(message, response_content)
            
        except Exception as e:
            logger.error("Error blocking source", error=str(e), exc_info=True)
            await self._send_error(message, "Block operation failed", str(e))
    
    async def _handle_isolate_actor(self, message: ActorMessage) -> None:
        """
        Isolate an actor from the Collective.
        
        Content: {
            "actor_id": str,
            "duration": int (optional, seconds),
            "reason": str (optional)
        }
        """
        try:
            content = message.content
            actor_id = content.get("actor_id")
            duration = content.get("duration")
            reason = content.get("reason", "security_isolation")
            
            if not actor_id:
                await self._send_error(message, "Missing actor_id")
                return
            
            self._isolated_actors.add(actor_id)
            
            # Schedule un-isolate if duration specified
            if duration:
                asyncio.create_task(self._schedule_unisolate(actor_id, duration))
            
            logger.warning(
                "Actor isolated",
                actor_id=actor_id,
                duration=duration,
                reason=reason,
            )
            
            response_content = {
                "actor_id": actor_id,
                "isolated": True,
                "duration": duration,
                "reason": reason,
            }
            
            await self._send_response(message, response_content)
            
        except Exception as e:
            logger.error("Error isolating actor", error=str(e), exc_info=True)
            await self._send_error(message, "Isolation operation failed", str(e))
    
    async def _handle_get_statistics(self, message: ActorMessage) -> None:
        """Get current security statistics."""
        try:
            response_content = {
                "statistics": {
                    "total_incidents": self._stats["total_incidents"],
                    "incidents_by_level": dict(self._stats["incidents_by_level"]),
                    "incidents_by_type": dict(self._stats["incidents_by_type"]),
                    "auto_responses": self._stats["auto_responses_triggered"],
                    "manual_responses": self._stats["manual_responses_triggered"],
                    "threats_contained": self._stats["threats_contained"],
                    "threats_mitigated": self._stats["threats_mitigated"],
                },
                "active_state": {
                    "active_incidents": len([
                        i for i in self._incidents.values()
                        if i.status not in [IncidentStatus.CLOSED, IncidentStatus.REMEDIATED]
                    ]),
                    "blocked_sources": len(self._blocked_sources),
                    "isolated_actors": len(self._isolated_actors),
                    "tracked_indicators": len(self._threat_indicators),
                },
            }
            
            await self._send_response(message, response_content)
            
        except Exception as e:
            logger.error("Error getting statistics", error=str(e), exc_info=True)
            await self._send_error(message, "Statistics retrieval failed", str(e))
    
    async def _handle_update_config(self, message: ActorMessage) -> None:
        """Update security configuration."""
        try:
            content = message.content
            
            if "auto_response_enabled" in content:
                self._auto_response_enabled = content["auto_response_enabled"]
            
            if "alert_threshold" in content:
                try:
                    self._alert_threshold = ThreatLevel(content["alert_threshold"]).value
                except ValueError:
                    pass
            
            if "max_incidents" in content:
                self._max_incidents = content["max_incidents"]
            
            response_content = {
                "updated": True,
                "current_config": {
                    "auto_response_enabled": self._auto_response_enabled,
                    "alert_threshold": self._alert_threshold,
                    "max_incidents": self._max_incidents,
                },
            }
            
            await self._send_response(message, response_content)
            
        except Exception as e:
            logger.error("Error updating config", error=str(e), exc_info=True)
            await self._send_error(message, "Config update failed", str(e))
    
    def _create_incident_id(self) -> str:
        """Generate unique incident ID."""
        timestamp = datetime.now(timezone.utc).timestamp()
        random_suffix = hashlib.sha256(str(timestamp).encode()).hexdigest()[:8]
        return f"INC_{int(timestamp)}_{random_suffix}"
    
    def _create_indicator(self, data: Dict[str, Any]) -> Optional[ThreatIndicator]:
        """Create a threat indicator from data."""
        try:
            indicator_id = f"IND_{hashlib.sha256(data.get('value', '').encode()).hexdigest()[:12]}"
            now = datetime.now(timezone.utc)
            
            return ThreatIndicator(
                indicator_id=indicator_id,
                indicator_type=data.get("indicator_type", "unknown"),
                value=data.get("value", ""),
                confidence=float(data.get("confidence", 0.5)),
                first_seen=now,
                last_seen=now,
                source=data.get("source", "unknown"),
                tags=data.get("tags", []),
            )
        except Exception as e:
            logger.error("Error creating indicator", error=str(e))
            return None
    
    async def _auto_respond(self, incident: SecurityIncident) -> List[ResponseAction]:
        """Execute automatic response to an incident."""
        actions = []
        
        # Determine response based on threat level
        if incident.threat_level == ThreatLevel.CRITICAL:
            # Critical: Immediate isolation and blocking
            actions.append(ResponseAction.ALERT)
            actions.append(ResponseAction.ISOLATE)
            actions.append(ResponseAction.BLOCK)
            actions.append(ResponseAction.QUARANTINE)
            
            if incident.source_actor:
                self._isolated_actors.add(incident.source_actor)
            if incident.target_resource:
                actions.append(ResponseAction.TERMINATE)
        
        elif incident.threat_level == ThreatLevel.HIGH:
            # High: Alert and rate limit
            actions.append(ResponseAction.ALERT)
            actions.append(ResponseAction.RATE_LIMIT)
            
            if incident.source_actor:
                self._rate_limits[incident.source_actor] = {
                    "max_requests": 10,
                    "window_seconds": 60,
                    "started_at": datetime.now(timezone.utc),
                }
        
        elif incident.threat_level == ThreatLevel.MEDIUM:
            # Medium: Alert and log
            actions.append(ResponseAction.ALERT)
            actions.append(ResponseAction.LOG_ONLY)
        
        else:
            # Low/Informational: Log only
            actions.append(ResponseAction.LOG_ONLY)
        
        # Update statistics
        self._stats["auto_responses_triggered"] += len(actions)
        
        return actions
    
    async def _execute_response_action(
        self,
        incident: SecurityIncident,
        action: ResponseAction,
    ) -> bool:
        """Execute a specific response action."""
        try:
            if action == ResponseAction.ALERT:
                logger.warning(
                    "Security alert triggered",
                    incident_id=incident.incident_id,
                    threat_type=incident.threat_type.value,
                )
                return True
            
            elif action == ResponseAction.BLOCK:
                if incident.source_actor:
                    self._blocked_sources.add(incident.source_actor)
                return True
            
            elif action == ResponseAction.ISOLATE:
                if incident.source_actor:
                    self._isolated_actors.add(incident.source_actor)
                return True
            
            elif action == ResponseAction.QUARANTINE:
                if incident.target_resource:
                    # Mark resource as quarantined
                    incident.evidence["quarantined"] = True
                return True
            
            elif action == ResponseAction.TERMINATE:
                # Terminate affected processes/connections
                incident.evidence["terminated"] = True
                return True
            
            elif action == ResponseAction.RATE_LIMIT:
                if incident.source_actor:
                    self._rate_limits[incident.source_actor] = {
                        "max_requests": 10,
                        "window_seconds": 60,
                    }
                return True
            
            elif action == ResponseAction.BLACKLIST:
                for indicator in incident.indicators:
                    self._blocked_sources.add(indicator.value)
                return True
            
            elif action == ResponseAction.NOTIFY:
                # Send notifications to administrators
                logger.info(
                    "Security notification sent",
                    incident_id=incident.incident_id,
                )
                return True
            
            elif action == ResponseAction.LOG_ONLY:
                logger.info(
                    "Security event logged",
                    incident_id=incident.incident_id,
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error("Error executing response action", action=action.value, error=str(e))
            return False
    
    def _calculate_severity_score(self, incident: SecurityIncident) -> float:
        """Calculate numerical severity score for an incident."""
        base_scores = {
            ThreatLevel.CRITICAL: 10.0,
            ThreatLevel.HIGH: 7.5,
            ThreatLevel.MEDIUM: 5.0,
            ThreatLevel.LOW: 2.5,
            ThreatLevel.INFORMATIONAL: 1.0,
        }
        
        score = base_scores.get(incident.threat_level, 5.0)
        
        # Adjust based on indicators
        score += len(incident.indicators) * 0.5
        
        # Adjust based on target
        if incident.target_actor:
            score += 1.0
        
        return min(score, 10.0)
    
    def _find_correlated_incidents(
        self,
        incident: SecurityIncident,
        max_results: int = 10,
    ) -> List[SecurityIncident]:
        """Find incidents correlated with the given incident."""
        correlated = []
        
        for other in self._incidents.values():
            if other.incident_id == incident.incident_id:
                continue
            
            correlation_score = 0.0
            
            # Same source actor
            if incident.source_actor and incident.source_actor == other.source_actor:
                correlation_score += 0.4
            
            # Same target
            if incident.target_actor and incident.target_actor == other.target_actor:
                correlation_score += 0.3
            
            # Same threat type
            if incident.threat_type == other.threat_type:
                correlation_score += 0.2
            
            # Shared indicators
            shared_indicators = set(
                i.value for i in incident.indicators
            ) & set(i.value for i in other.indicators)
            correlation_score += len(shared_indicators) * 0.1
            
            if correlation_score > 0.3:
                correlated.append(other)
        
        correlated.sort(key=lambda x: self._calculate_severity_score(x), reverse=True)
        return correlated[:max_results]
    
    def _reconstruct_attack_chain(self, incident: SecurityIncident) -> List[Dict[str, Any]]:
        """Reconstruct the attack chain leading to this incident."""
        chain = []
        correlated = self._find_correlated_incidents(incident, max_results=20)
        
        # Sort by timestamp
        correlated.sort(key=lambda x: x.timestamp)
        
        for related in correlated:
            chain.append({
                "incident_id": related.incident_id,
                "timestamp": related.timestamp.isoformat(),
                "threat_type": related.threat_type.value,
                "severity": self._calculate_severity_score(related),
            })
        
        return chain
    
    def _match_iocs(self, incident: SecurityIncident) -> List[Dict[str, Any]]:
        """Match indicators of compromise against known threat intelligence."""
        matches = []
        
        for indicator in incident.indicators:
            if indicator.value in self._indicator_cache:
                cached = self._indicator_cache[indicator.value]
                matches.append({
                    "indicator": indicator.value,
                    "matched_threat": cached.indicator_id,
                    "confidence": cached.confidence,
                    "tags": cached.tags,
                })
        
        return matches
    
    def _map_mitre_techniques(self, incident: SecurityIncident) -> List[str]:
        """Map incident to MITRE ATT&CK techniques."""
        technique_mapping = {
            ThreatType.SQL_INJECTION: ["T1190", "T1059"],
            ThreatType.XSS_ATTACK: ["T1189", "T1059"],
            ThreatType.UNAUTHORIZED_ACCESS: ["T1078", "T1133"],
            ThreatType.PRIVILEGE_ESCALATION: ["T1068", "T1134"],
            ThreatType.DATA_EXFILTRATION: ["T1041", "T1048"],
            ThreatType.MALWARE: ["T1204", "T1059"],
            ThreatType.PHISHING: ["T1566", "T1204"],
        }
        
        return technique_mapping.get(incident.threat_type, [])
    
    def _generate_recommendations(self, incident: SecurityIncident) -> List[str]:
        """Generate remediation recommendations for an incident."""
        recommendations = []
        
        if incident.threat_level in [ThreatLevel.CRITICAL, ThreatLevel.HIGH]:
            recommendations.append("Immediately isolate affected systems")
            recommendations.append("Conduct forensic analysis")
            recommendations.append("Review access logs for compromise indicators")
        
        if incident.threat_type == ThreatType.SQL_INJECTION:
            recommendations.append("Review and parameterize all database queries")
            recommendations.append("Implement input validation")
        
        if incident.threat_type == ThreatType.XSS_ATTACK:
            recommendations.append("Implement Content Security Policy (CSP)")
            recommendations.append("Sanitize all user inputs")
        
        if incident.threat_type == ThreatType.UNAUTHORIZED_ACCESS:
            recommendations.append("Reset compromised credentials")
            recommendations.append("Review and restrict access permissions")
        
        return recommendations
    
    def _generate_strategic_recommendations(self) -> List[str]:
        """Generate strategic security recommendations based on overall threat landscape."""
        recommendations = []
        
        # Check incident trends
        critical_count = self._stats["incidents_by_level"].get("critical", 0)
        if critical_count > 5:
            recommendations.append(
                f"High critical incident count ({critical_count}) - consider security architecture review"
            )
        
        # Check for specific threat patterns
        sql_injection_count = self._stats["incidents_by_type"].get("sql_injection", 0)
        if sql_injection_count > 10:
            recommendations.append(
                f" Elevated SQL injection attempts ({sql_injection_count}) - implement WAF rules"
            )
        
        # Auto-response effectiveness
        if self._stats["auto_responses_triggered"] > 100:
            recommendations.append(
                "High auto-response rate - review detection thresholds for false positives"
            )
        
        if not recommendations:
            recommendations.append("Security posture stable - continue monitoring")
        
        return recommendations
    
    async def _schedule_unblock(self, source: str, duration: int) -> None:
        """Schedule automatic unblocking of a source."""
        await asyncio.sleep(duration)
        self._blocked_sources.discard(source)
        logger.info("Source automatically unblocked", source=source)
    
    async def _schedule_unisolate(self, actor_id: str, duration: int) -> None:
        """Schedule automatic un-isolation of an actor."""
        await asyncio.sleep(duration)
        self._isolated_actors.discard(actor_id)
        logger.info("Actor automatically un-isolated", actor_id=actor_id)
