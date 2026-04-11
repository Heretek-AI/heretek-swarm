"""
Explorer Agent - Intelligence Gathering & Opportunity Discovery.

The Explorer agent provides:
- Monitoring of upstream sources and external systems
- Intelligence gathering from external sources
- Opportunity identification and capability discovery
- Anomaly detection and threat reporting
- External integration research

Explorer is the "eyes and ears" of the Collective, constantly scanning
the environment for opportunities, threats, and new capabilities.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import structlog
from swarms import Agent

from heretek_swarm.actors.base import ActorMessage, AgentActor
from heretek_swarm.actors.validation import validate_message

# Session 44: Collective Learning Integration
from heretek_swarm.collective.learning import PatternExtractor, PatternType

# Session 44: Consensus Integration
from heretek_swarm.consensus.swarm_deliberation import Position, SwarmDeliberationEngine

# Session 44: Memory Optimization Integration
from heretek_swarm.memory.access_patterns import AccessPatternAnalyzer, AccessTier

# Session 44: Zero-Trust Validation
from heretek_swarm.security.zero_trust import ZeroTrustValidator

_logger = structlog.get_logger("ExplorerAgent")


class OpportunityType(str, Enum):
    """Types of opportunities Explorer can identify."""
    API_INTEGRATION = "api_integration"
    FRAMEWORK = "framework"
    PERFORMANCE_IMPROVEMENT = "performance_improvement"
    SECURITY_ENHANCEMENT = "security_enhancement"
    COST_REDUCTION = "cost_reduction"
    CAPABILITY_ADDITION = "capability_addition"


class ThreatLevel(str, Enum):
    """Threat severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(str, Enum):
    """Types of anomalies Explorer can detect."""
    PERFORMANCE = "performance"
    SECURITY = "security"
    BEHAVIORAL = "behavioral"
    INTEGRATION = "integration"
    DATA = "data"


@dataclass
class Opportunity:
    """Discovered opportunity record."""
    id: str
    type: OpportunityType
    title: str
    description: str
    source: str
    confidence: float  # 0-1 confidence score
    impact_score: float  # 0-1 impact potential
    effort_estimate: str  # low/medium/high
    discovered_at: datetime
    status: str = "new"  # new/under_review/approved/rejected
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Anomaly:
    """Detected anomaly record."""
    id: str
    type: AnomalyType
    description: str
    source: str
    severity: ThreatLevel
    detected_at: datetime
    affected_components: List[str]
    evidence: Dict[str, Any]
    status: str = "new"  # new/investigating/escalated/resolved
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntelligenceReport:
    """Consolidated intelligence report."""
    id: str
    generated_at: datetime
    opportunities: List[Opportunity]
    anomalies: List[Anomaly]
    summary: str
    recommendations: List[str]
    sources_monitored: List[str]
    time_range_hours: int


class ExplorerAgent(AgentActor):
    """
    Explorer Agent - Intelligence Gathering Specialist.

    The Explorer is responsible for:
    - Continuously monitoring upstream sources and external APIs
    - Identifying new capabilities, frameworks, and integrations
    - Detecting anomalies in external systems and internal metrics
    - Gathering intelligence to support collective decisions
    - Reporting opportunities and threats to the swarm

    Intelligence Gathering Workflow:
    1. Monitor configured sources (APIs, feeds, repositories)
    2. Parse and analyze incoming data
    3. Identify patterns, opportunities, and anomalies
    4. Score and prioritize findings
    5. Generate intelligence reports
    6. Notify relevant agents of significant findings
    """

    def __init__(self, _agent_id: str, _name: str, _description: str, _swarms_agent: Optional[Agent], _monitoring_interval_seconds: int, _max_opportunities: int, _max_anomalies: int, _confidence_threshold: float, **kwargs) -> None:
        """
        Initialize the Explorer agent.

        Args:
            agent_id: Unique identifier
            name: Human-readable name
            description: Agent description
            swarms_agent: Optional Swarms Agent for LLM capabilities
            monitoring_interval_seconds: Interval between monitoring cycles
            max_opportunities: Maximum tracked opportunities (LRU eviction)
            max_anomalies: Maximum tracked anomalies (LRU eviction)
            confidence_threshold: Minimum confidence for reporting findings
            **kwargs: Additional arguments
        """
        super().__init__(
            agent_id=agent_id,
            _name = name,
            description=description,
            _topics = [
                "exploration",
                "intelligence",
                "opportunities",
                "discovery",
                "monitoring",
            ],
            _capabilities = [
                "source-monitoring",
                "opportunity-identification",
                "anomaly-detection",
                "intelligence-gathering",
                "capability-discovery",
            ],
            _swarms_agent = swarms_agent,
            **kwargs,
        )

        # Explorer-specific configuration
        self.monitoring_interval_seconds = monitoring_interval_seconds
        self.max_opportunities = max_opportunities
        self.max_anomalies = max_anomalies
        self.confidence_threshold = confidence_threshold

        # Explorer state
        self._opportunities: Dict[str, Opportunity] = {}
        self._anomalies: Dict[str, Anomaly] = {}
        self._monitored_sources: Set[str] = set()
        self._monitoring_active: bool = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._intelligence_history: List[IntelligenceReport] = []
        self._max_intelligence_history: int = 20

        # Source-specific state
        self._source_configs: Dict[str, Dict[str, Any]] = {}
        self._last_source_check: Dict[str, datetime] = {}
        self._source_error_counts: Dict[str, int] = {}
        self._max_source_errors: int = 3

        # Session 44: Integration components
        self.pattern_extractor: PatternExtractor | None = None
        self.deliberation_engine: SwarmDeliberationEngine | None = None
        self.access_analyzer: AccessPatternAnalyzer | None = None
        self.zero_trust_validator: ZeroTrustValidator | None = None

        # Initialize with defaults if not provided
        if not self.pattern_extractor:
            self.pattern_extractor = PatternExtractor(min_support=3, min_confidence=0.6)
        if not self.deliberation_engine:
            self.deliberation_engine = SwarmDeliberationEngine(
                _max_rounds = 5, consensus_threshold=0.75, min_participants=2
            )
        if not self.access_analyzer:
            self.access_analyzer = AccessPatternAnalyzer()
        if not self.zero_trust_validator:
            self.zero_trust_validator = ZeroTrustValidator()

        # Session 44: Integration state
        self._active_deliberations: Dict[str, str] = {}
        self._pattern_emitted: Set[str] = set()


        logger.info(
            "Explorer agent initialized",
            agent_id=agent_id,
            _monitoring_interval = monitoring_interval_seconds,
            confidence_threshold=confidence_threshold,
        )

    async def on_start(self) -> None:
        """Start the Explorer agent and begin monitoring."""
        await super().on_start()
        self._monitoring_active = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Explorer agent started, monitoring active")

    async def on_stop(self) -> None:
        """Stop the Explorer agent and halt monitoring."""
        self._monitoring_active = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
        await super().on_stop()
        logger.info("Explorer agent stopped")

    async def _monitoring_loop(self) -> None:
        """
        Continuous monitoring loop.

        Runs at configured intervals to check all monitored sources
        for opportunities and anomalies.
        """
        while self._monitoring_active:
            try:
                await self._check_all_sources()
                await self._analyze_findings()
                await asyncio.sleep(self.monitoring_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Monitoring loop error", error=str(e))
                await asyncio.sleep(self.monitoring_interval_seconds)

    async def _check_all_sources(self) -> None:
        """Check all configured monitoring sources."""
        for source_id, config in self._source_configs.items():
            try:
                await self._check_source(source_id, config)
                self._last_source_check[source_id] = datetime.now(timezone.utc)
                self._source_error_counts[source_id] = 0
            except Exception as e:
                self._source_error_counts[source_id] = self._source_error_counts.get(source_id, 0) + 1
                logger.error(
                    "Source check failed",
                    _source_id = source_id,
                    error=str(e),
                    _error_count = self._source_error_counts[source_id],
                )

    async def _check_source(self, _source_id: str, _config: Dict[str, Any]) -> None:
        """
        Check a single monitoring source.

        Args:
            source_id: Source identifier
            config: Source configuration (type, url, headers, etc.)
        """
        _source_type = config.get("type", "generic")
        logger.debug("Checking source", source_id=source_id, type=source_type)

        # Placeholder for actual source checking logic
        # This would integrate with HTTP clients, RSS parsers, API clients, etc.
        # For now, we'll log the check and rely on explicit intelligence requests

    async def _analyze_findings(self) -> None:
        """Analyze collected findings for patterns and correlations."""
        # Placeholder for pattern analysis
        # Would look for correlations between opportunities and anomalies
        pass

    def _add_opportunity(self, _opportunity: Opportunity) -> None:
        """
        Add opportunity with LRU eviction.

        Args:
            opportunity: Opportunity record to add
        """
        if len(self._opportunities) >= self.max_opportunities:
            # Evict oldest/lowest priority opportunity
            _oldest_id = min(
                self._opportunities.keys(),
                _key = lambda x: (
                    self._opportunities[x].impact_score,
                    self._opportunities[x].discovered_at,
                ),
            )
            del self._opportunities[oldest_id]
            logger.debug("Evicted oldest opportunity", evicted_id=oldest_id)

        self._opportunities[opportunity.id] = opportunity
        logger.info(
            "Opportunity added",
            _opportunity_id = opportunity.id,
            type=opportunity.type.value,
            confidence=opportunity.confidence,
            impact=opportunity.impact_score,
        )

    def _add_anomaly(self, _anomaly: Anomaly) -> None:
        """
        Add anomaly with LRU eviction.

        Args:
            anomaly: Anomaly record to add
        """
        if len(self._anomalies) >= self.max_anomalies:
            # Evict oldest/lowest severity anomaly
            _severity_order = {
                ThreatLevel.LOW: 0,
                ThreatLevel.MEDIUM: 1,
                ThreatLevel.HIGH: 2,
                ThreatLevel.CRITICAL: 3,
            }
            _oldest_id = min(
                self._anomalies.keys(),
                _key = lambda x: (
                    severity_order.get(self._anomalies[x].severity, 0),
                    self._anomalies[x].detected_at,
                ),
            )
            del self._anomalies[oldest_id]
            logger.debug("Evicted oldest anomaly", evicted_id=oldest_id)

        self._anomalies[anomaly.id] = anomaly
        logger.info(
            "Anomaly added",
            _anomaly_id = anomaly.id,
            type=anomaly.type.value,
            severity=anomaly.severity.value,
        )

    # -------------------------------------------------------------------------
    # Message Handlers
    # -------------------------------------------------------------------------

    async def _handle_start_monitoring(self, _message: ActorMessage) -> None:
        """
        Start monitoring a source.

        Content schema:
        {
            "source_id": str,
            "source_type": str,
            "config": dict,
        }
        """
        try:
            _validated = validate_message(message.content, "start_monitoring")
            _content = validated.content

            _source_id = content.get("source_id")
            _source_type = content.get("source_type", "generic")
            _config = content.get("config", {})

            if not source_id:
                logger.warning("Start monitoring missing source_id")
                return

            config["type"] = source_type
            self._source_configs[source_id] = config
            self._monitored_sources.add(source_id)
            self._last_source_check[source_id] = datetime.now(timezone.utc)

            logger.info(
                "Started monitoring source",
                _source_id = source_id,
                _source_type = source_type,
            )

            await self._send_status_update(
                status="monitoring_started",
                _source_id = source_id,
                _source_type = source_type,
            )

        except Exception as e:
            logger.error("Failed to start monitoring", error=str(e))
            await self._send_error_response(message.sender_id, f"Failed to start monitoring: {e}")

    async def _handle_stop_monitoring(self, _message: ActorMessage) -> None:
        """
        Stop monitoring a source.

        Content schema:
        {
            "source_id": str,
        }
        """
        try:
            _validated = validate_message(message.content, "stop_monitoring")
            _content = validated.content

            _source_id = content.get("source_id")

            if not source_id:
                logger.warning("Stop monitoring missing source_id")
                return

            if source_id in self._source_configs:
                del self._source_configs[source_id]
                self._monitored_sources.discard(source_id)
                logger.info("Stopped monitoring source", source_id=source_id)

            await self._send_status_update(
                status="monitoring_stopped",
                _source_id = source_id,
            )

        except Exception as e:
            logger.error("Failed to stop monitoring", error=str(e))
            await self._send_error_response(message.sender_id, f"Failed to stop monitoring: {e}")

    async def _handle_get_opportunities(self, _message: ActorMessage) -> None:
        """
        Get discovered opportunities.

        Content schema:
        {
            "limit": int (optional, default 10),
            "min_confidence": float (optional),
            "type": str (optional, filter by type),
            "status": str (optional, filter by status),
        }
        """
        try:
            _validated = validate_message(message.content, "get_opportunities")
            _content = validated.content

            _limit = content.get("limit", 10)
            _min_confidence = content.get("min_confidence", self.confidence_threshold)
            _opp_type = content.get("type")
            status = content.get("status")

            # Filter opportunities
            _filtered = [
                opp for opp in self._opportunities.values()
                if opp.confidence >= min_confidence
                and (not opp_type or opp.type.value == opp_type)
                and (not status or opp.status == status)
            ]

            # Sort by impact score and confidence
            filtered.sort(key=lambda x: (x.impact_score, x.confidence), reverse=True)
            _filtered = filtered[:limit]

            # Convert to serializable format
            _result = [
                {
                    "id": opp.id,
                    "type": opp.type.value,
                    "title": opp.title,
                    "description": opp.description,
                    "source": opp.source,
                    "confidence": opp.confidence,
                    "impact_score": opp.impact_score,
                    "effort_estimate": opp.effort_estimate,
                    "discovered_at": opp.discovered_at.isoformat(),
                    "status": opp.status,
                }
                for opp in filtered
            ]

            await self._send_response(
                message.sender_id,
                {
                    "opportunities": result,
                    "total_available": len(self._opportunities),
                    "total_filtered": len(filtered),
                },
            )

        except Exception as e:
            logger.error("Failed to get opportunities", error=str(e))
            await self._send_error_response(message.sender_id, f"Failed to get opportunities: {e}")

    async def _handle_get_anomalies(self, _message: ActorMessage) -> None:
        """
        Get detected anomalies.

        Content schema:
        {
            "limit": int (optional, default 10),
            "min_severity": str (optional),
            "type": str (optional, filter by type),
            "status": str (optional, filter by status),
        }
        """
        try:
            _validated = validate_message(message.content, "get_anomalies")
            _content = validated.content

            _limit = content.get("limit", 10)
            _min_severity = content.get("min_severity", ThreatLevel.LOW.value)
            _anomaly_type = content.get("type")
            status = content.get("status")

            _severity_order = {
                ThreatLevel.LOW.value: 0,
                ThreatLevel.MEDIUM.value: 1,
                ThreatLevel.HIGH.value: 2,
                ThreatLevel.CRITICAL.value: 3,
            }
            _min_severity_value = severity_order.get(min_severity, 0)

            # Filter anomalies
            _filtered = [
                anom for anom in self._anomalies.values()
                if severity_order.get(anom.severity.value, 0) >= min_severity_value
                and (not anomaly_type or anom.type.value == anomaly_type)
                and (not status or anom.status == status)
            ]

            # Sort by severity and recency
            filtered.sort(
                _key = lambda x: (severity_order.get(x.severity.value, 0), x.detected_at),
                _reverse = True,
            )
            _filtered = filtered[:limit]

            # Convert to serializable format
            _result = [
                {
                    "id": anom.id,
                    "type": anom.type.value,
                    "description": anom.description,
                    "source": anom.source,
                    "severity": anom.severity.value,
                    "detected_at": anom.detected_at.isoformat(),
                    "affected_components": anom.affected_components,
                    "status": anom.status,
                }
                for anom in filtered
            ]

            await self._send_response(
                message.sender_id,
                {
                    "anomalies": result,
                    "total_available": len(self._anomalies),
                    "total_filtered": len(filtered),
                },
            )

        except Exception as e:
            logger.error("Failed to get anomalies", error=str(e))
            await self._send_error_response(message.sender_id, f"Failed to get anomalies: {e}")

    async def _handle_generate_report(self, _message: ActorMessage) -> None:
        """
        Generate intelligence report.

        Content schema:
        {
            "time_range_hours": int (optional, default 24),
            "include_opportunities": bool (optional, default True),
            "include_anomalies": bool (optional, default True),
        }
        """
        try:
            _validated = validate_message(message.content, "generate_report")
            _content = validated.content

            time_range_hours = content.get("time_range_hours", 24)
            _include_opportunities = content.get("include_opportunities", True)
            _include_anomalies = content.get("include_anomalies", True)

            _cutoff = datetime.now(timezone.utc)

            # Filter by time range
            opportunities = [
                opp for opp in self._opportunities.values()
                if include_opportunities and opp.discovered_at >= cutoff
            ]
            anomalies = [
                anom for anom in self._anomalies.values()
                if include_anomalies and anom.detected_at >= cutoff
            ]

            # Generate summary using LLM if available
            summary = await self._generate_summary(opportunities, anomalies, time_range_hours)
            recommendations = await self._generate_recommendations(opportunities, anomalies)

            _report = IntelligenceReport(
                id=f"intel-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
                generated_at=datetime.now(timezone.utc),
                opportunities=opportunities,
                anomalies=anomalies,
                summary=summary,
                recommendations=recommendations,
                sources_monitored=list(self._monitored_sources),
                time_range_hours=time_range_hours,
            )

            # Store in history
            self._intelligence_history.append(report)
            if len(self._intelligence_history) > self._max_intelligence_history:
                self._intelligence_history = self._intelligence_history[-self._max_intelligence_history:]

            # Convert to serializable format
            _report_data = {
                "id": report.id,
                "generated_at": report.generated_at.isoformat(),
                "summary": report.summary,
                "recommendations": report.recommendations,
                "opportunities_count": len(report.opportunities),
                "anomalies_count": len(report.anomalies),
                "sources_monitored": report.sources_monitored,
                "time_range_hours": report.time_range_hours,
            }

            await self._send_response(message.sender_id, report_data)

        except Exception as e:
            logger.error("Failed to generate report", error=str(e))
            await self._send_error_response(message.sender_id, f"Failed to generate report: {e}")

    async def _handle_report_opportunity(self, _message: ActorMessage) -> None:
        """
        Report a new opportunity from external source.

        Content schema:
        {
            "type": str,
            "title": str,
            "description": str,
            "source": str,
            "confidence": float,
            "impact_score": float,
            "effort_estimate": str,
            "metadata": dict (optional),
        }
        """
        try:
            _validated = validate_message(message.content, "report_opportunity")
            _content = validated.content

            import uuid

            _opportunity = Opportunity(
                id=f"opp-{uuid.uuid4().hex[:8]}",
                type=OpportunityType(content.get("type", "capability_addition")),
                title=content.get("title", "Untitled Opportunity"),
                description=content.get("description", ""),
                source=content.get("source", "external"),
                confidence=float(content.get("confidence", 0.5)),
                impact_score=float(content.get("impact_score", 0.5)),
                _effort_estimate = content.get("effort_estimate", "medium"),
                _discovered_at = datetime.now(timezone.utc),
                metadata=content.get("metadata", {}),
            )

            self._add_opportunity(opportunity)

            await self._send_status_update(
                _status = "opportunity_recorded",
                _opportunity_id = opportunity.id,
                title=opportunity.title,
            )

        except Exception as e:
            logger.error("Failed to report opportunity", error=str(e))
            await self._send_error_response(message.sender_id, f"Failed to report opportunity: {e}")

    async def _handle_report_anomaly(self, _message: ActorMessage) -> None:
        """
        Report a detected anomaly.

        Content schema:
        {
            "type": str,
            "description": str,
            "source": str,
            "severity": str,
            "affected_components": list,
            "evidence": dict,
            "metadata": dict (optional),
        }
        """
        try:
            _validated = validate_message(message.content, "report_anomaly")
            _content = validated.content

            import uuid

            _anomaly = Anomaly(
                id=f"anom-{uuid.uuid4().hex[:8]}",
                type=AnomalyType(content.get("type", "behavioral")),
                description=content.get("description", ""),
                source=content.get("source", "internal"),
                severity=ThreatLevel(content.get("severity", ThreatLevel.LOW.value)),
                _detected_at = datetime.now(timezone.utc),
                _affected_components = content.get("affected_components", []),
                _evidence = content.get("evidence", {}),
                metadata=content.get("metadata", {}),
            )

            self._add_anomaly(anomaly)

            # Escalate high/critical anomalies immediately
            if anomaly.severity in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                logger.warning(
                    "High severity anomaly detected - escalating",
                    _anomaly_id = anomaly.id,
                    severity=anomaly.severity.value,
                    description=anomaly.description,
                )
                # Could notify Sentinel or Supervisor here

            await self._send_status_update(
                _status = "anomaly_recorded",
                _anomaly_id = anomaly.id,
                severity=anomaly.severity.value,
            )

        except Exception as e:
            logger.error("Failed to report anomaly", error=str(e))
            await self._send_error_response(message.sender_id, f"Failed to report anomaly: {e}")

    async def _handle_get_monitoring_status(self, _message: ActorMessage) -> None:
        """
        Get monitoring status overview.

        Content schema: {}
        """
        try:
            now = datetime.now(timezone.utc)

            _sources_status = []
            for source_id in self._monitored_sources:
                _last_check = self._last_source_check.get(source_id)
                _error_count = self._source_error_counts.get(source_id, 0)

                sources_status.append({
                    "source_id": source_id,
                    "type": self._source_configs.get(source_id, {}).get("type", "unknown"),
                    "last_check": last_check.isoformat() if last_check else None,
                    "error_count": error_count,
                    "status": "healthy" if error_count < self._max_source_errors else "error",
                })

            _status_data = {
                "monitoring_active": self._monitoring_active,
                "sources_count": len(self._monitored_sources),
                "opportunities_tracked": len(self._opportunities),
                "anomalies_tracked": len(self._anomalies),
                "reports_generated": len(self._intelligence_history),
                "sources": sources_status,
            }

            await self._send_response(message.sender_id, status_data)

        except Exception as e:
            logger.error("Failed to get monitoring status", error=str(e))
            await self._send_error_response(message.sender_id, f"Failed to get status: {e}")

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    async def _generate_summary(self, _opportunities: List[Opportunity], _anomalies: List[Anomaly], _time_range_hours: int) -> str:
        """Generate intelligence summary using LLM."""
        try:
            _prompt = self._build_summary_prompt(opportunities, anomalies, time_range_hours)
            _summary = await self.run_with_llm(prompt, timeout=60)
            return summary or f"Intelligence report for the past {time_range_hours} hours: {len(opportunities)} opportunities and {len(anomalies)} anomalies identified."
        except Exception as e:
            logger.error("Failed to generate LLM summary", error=str(e))
            return f"Intelligence report: {len(opportunities)} opportunities, {len(anomalies)} anomalies (summary generation failed)"

    async def _generate_recommendations(self, _opportunities: List[Opportunity], _anomalies: List[Anomaly]) -> List[str]:
        """Generate recommendations based on findings."""
        _recommendations = []

        # High-impact opportunities
        _high_impact = [o for o in opportunities if o.impact_score > 0.7]
        if high_impact:
            recommendations.append(
                f"Prioritize investigation of {len(high_impact)} high-impact opportunities"
            )

        # High-severity anomalies
        _critical = [a for a in anomalies if a.severity in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]]
        if critical:
            recommendations.append(
                f"Immediately address {len(critical)} critical/high-severity anomalies"
            )

        # Pattern-based recommendations
        if len(opportunities) > 10:
            recommendations.append("Consider expanding monitoring scope - high opportunity rate")

        if len(anomalies) > 20:
            recommendations.append("Review system health - elevated anomaly count detected")

        return recommendations or ["Continue standard monitoring operations"]

    def _build_summary_prompt(self, _opportunities: List[Opportunity], _anomalies: List[Anomaly], _time_range_hours: int) -> str:
        """Build LLM prompt for summary generation."""
        _opp_summary = "\n".join(
            f"- [{opp.type.value}] {opp.title} (confidence: {opp.confidence:.2f}, impact: {opp.impact_score:.2f})"
            for opp in opportunities[:10]
        )
        _anom_summary = "\n".join(
            f"- [{anom.severity.value}] {anom.description[:50]}... (source: {anom.source})"
            for anom in anomalies[:10]
        )

        return f"""Generate a concise intelligence summary for the past {time_range_hours} hours.

OPPORTUNITIES IDENTIFIED ({len(opportunities)} total, showing top 10):
{opp_summary or "None"}

ANOMALIES DETECTED ({len(anomalies)} total, showing top 10):
{anom_summary or "None"}

Provide a 2-3 sentence executive summary highlighting the most significant findings and recommended focus areas."""

    async def _send_status_update(self, _status: str, **kwargs) -> None:
        """Send status update to relevant agents."""
        await self._send_response("broadcast", {"status": status, **kwargs})


    # =========================================================================
    # Session 44: Collective Learning Integration Methods
    # =========================================================================

    async def _emit_pattern(self, _item_id: str, _item_type: str, _outcome: str, _content: Dict[str, Any]) -> None:
        """Emit pattern for collective learning."""
        if not self.pattern_extractor:
            return

        if item_id in self._pattern_emitted:
            return

        try:
            await self.pattern_extractor.analyze_message(
                _message_id = f"{item_type}_{item_id}",
                _sender = self.agent_id,
                _recipient = "broadcast",
                _message_type = f"{item_type}_completion",
                _content = content,
                _timestamp = datetime.now(timezone.utc).isoformat(),
            )

            self._pattern_emitted.add(item_id)
            logger.info(f"{item_type}_pattern_emitted", item_id=item_id, outcome=outcome)
        except Exception as e:
            logger.warning("failed_to_emit_pattern", item_id=item_id, error=str(e))

    async def _consume_patterns(self, _pattern_types: Optional[List[PatternType]]) -> List[Dict[str, Any]]:
        """Consume patterns from collective learning."""
        if not self.pattern_extractor:
            return []

        try:
            _patterns = await self.pattern_extractor.extract_patterns(
                _time_window_hours = 24,
                _pattern_types = pattern_types or [PatternType.SUCCESS, PatternType.DECISION],
            )
            return [p.to_dict() for p in patterns if p.metadata.confidence >= 0.7]
        except Exception as e:
            logger.warning("failed_to_consume_patterns", error=str(e))
            return []

    # =========================================================================
    # Session 44: Consensus Deliberation Integration Methods
    # =========================================================================

    async def _initiate_deliberation(self, _item_id: str, _proposal: str, _participating_agents: List[str], _domain: str) -> Optional[str]:
        """Initiate swarm deliberation."""
        if not self.deliberation_engine:
            return None

        try:
            _deliberation_id = f"delib_{item_id}"
            self.deliberation_engine.start_deliberation(
                _deliberation_id = deliberation_id,
                _proposal = proposal[:200],
                _participants = participating_agents,
                _domain = domain,
            )
            self._active_deliberations[item_id] = deliberation_id

            logger.info("deliberation_initiated", deliberation_id=deliberation_id, item_id=item_id)
            return deliberation_id
        except Exception as e:
            logger.error("failed_to_initiate_deliberation", item_id=item_id, error=str(e))
            return None

    async def _submit_deliberation_position(self, _item_id: str, _agent_id: str, _position: Position, _confidence: float, _argument: str) -> bool:
        """Submit agent position in deliberation."""
        if not self.deliberation_engine:
            return False

        _deliberation_id = self._active_deliberations.get(item_id)
        if not deliberation_id:
            return False

        try:
            _success = self.deliberation_engine.submit_position(
                _deliberation_id = deliberation_id,
                agent_id=agent_id,
                _position = position,
                _confidence = confidence,
                _argument = argument,
            )

            if success and self.access_analyzer:
                self.access_analyzer.record_access(
                    _memory_id = f"delib_{deliberation_id}_{agent_id}",
                    _access_type = "write",
                    agent_id=agent_id,
                )

            return success
        except Exception as e:
            logger.error("failed_to_submit_deliberation_position", error=str(e))
            return False

    async def _finalize_deliberation(self, _item_id: str) -> Optional[Any]:
        """Finalize deliberation and apply result."""
        if not self.deliberation_engine:
            return None

        _deliberation_id = self._active_deliberations.get(item_id)
        if not deliberation_id:
            return None

        try:
            _result = self.deliberation_engine.finalize_deliberation(deliberation_id)

            if result:
                self.deliberation_engine.cleanup_deliberation(deliberation_id)
                del self._active_deliberations[item_id]
                logger.info("deliberation_finalized", deliberation_id=deliberation_id)

            return result
        except Exception as e:
            logger.error("failed_to_finalize_deliberation", error=str(e))
            return None

    # =========================================================================
    # Session 44: Memory Optimization Integration Methods
    # =========================================================================

    def _track_memory_access(self, _item_id: str, _item_type: str, _access_type: str) -> None:
        """Track memory access patterns."""
        if not self.access_analyzer:
            return

        _memory_id = f"{item_type}_{item_id}"
        self.access_analyzer.record_access(
            _memory_id = memory_id,
            _access_type = access_type,
            agent_id=self.agent_id,
        )

    def _get_memory_tier(self, _item_id: str, _item_type: str) -> AccessTier:
        """Get memory tier classification."""
        if not self.access_analyzer:
            return AccessTier.COLD

        _memory_id = f"{item_type}_{item_id}"
        _profile = self.access_analyzer.get_profile(memory_id)
        return profile.tier if profile else AccessTier.COLD

    async def _prefetch_relevant(self, _agent_id: str, _item_type: str) -> List[str]:
        """Prefetch items an agent is likely to need."""
        if not self.access_analyzer:
            return []

        try:
            _predicted_memories = self.access_analyzer.predict_agent_access(agent_id)
            return [
                mem.replace(f"{item_type}_", "")
                for mem in predicted_memories
                if mem.startswith(f"{item_type}_")
            ]
        except Exception as e:
            logger.warning("failed_to_prefetch", agent_id=agent_id, error=str(e))
            return []

    def get_learning_status(self) -> Dict[str, Any]:
        """Get collective learning and memory optimization status."""
        return {
            "agent_id": self.agent_id,
            "collective_learning": {
                "patterns_extracted": len(self.pattern_extractor._validated_patterns) if self.pattern_extractor else 0,
                "message_cache_size": len(self.pattern_extractor._message_cache) if self.pattern_extractor else 0,
            },
            "consensus": {
                "active_deliberations": len(self._active_deliberations),
                "deliberation_engine_stats": self.deliberation_engine.get_statistics() if self.deliberation_engine else {},
            },
            "memory_optimization": {
                "access_statistics": self.access_analyzer.get_statistics().to_dict() if self.access_analyzer else {},
            },
        }


    async def _send_error_response(self, _recipient: str, _error: str) -> None:
        """Send error response."""
        await self._send_response(recipient, {"error": error})

    async def _send_response(self, _recipient: str, _data: Dict[str, Any]) -> None:
        """Send response message."""
        if recipient == "broadcast":
            # Broadcast to subscribed agents
            pass
        else:
            await self.put_message(
                _recipient = recipient,
                _message_type = "intelligence_response",
                _content = data,
            )
