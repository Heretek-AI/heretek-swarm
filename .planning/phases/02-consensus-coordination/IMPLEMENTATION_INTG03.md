# Implementation Plan: INTG-03 — Catalyst Paradigm Shift Detection

## Task Overview

**Owner**: Catalyst
**Depends**: Task 11 (INTG-01), Task 12 (INTG-02)
**Verification**: Catalyst detects paradigm shifts; change impact assessment; Core Triad notification.

## Edge Cases

- False positive paradigm shift — Beta validates; deliberation resolves
- Rapid successive shifts — rate limiting; cumulative impact assessment

---

## 1. Analysis of Existing Code

### 1.1 Catalyst Agent (`src/heretek_swarm/actors/catalyst.py`)

**Current Capabilities**:
- `ChangeRequest` and `ChangeNotification` dataclasses
- `ChangeStatus` enum (PROPOSED, ANALYZING, APPROVED, SCHEDULED, IN_PROGRESS, TESTING, COMPLETED, ROLLED_BACK, FAILED)
- `ChangeType` enum (CONFIGURATION, DEPLOYMENT, MIGRATION, UPGRADE, PATCH, HOTFIX, ROLLBACK)
- `ImpactLevel` enum (LOW, MEDIUM, HIGH, CRITICAL)
- Change management handlers: `propose_change`, `analyze_change`, `approve_change`, `schedule_change`, `execute_change`
- Rollback handlers: `request_rollback`, `execute_rollback`
- Notification system: `notify_stakeholders`, `_notify_stakeholders`
- Risk scoring: `_calculate_risk_score()`, `_generate_recommendations()`
- History tracking: `_record_change_event()`

**Integration Components (from Session 44)**:
- `PatternExtractor` - for pattern analysis
- `SwarmDeliberationEngine` - for deliberation on false positives
- `AccessPatternAnalyzer` - for access pattern analysis
- `ZeroTrustValidator` - for validation

**Missing for INTG-03**:
- No paradigm shift detection - Catalyst only handles ChangeRequests, not systemic change
- No rate limiting for rapid successive changes
- No cumulative impact assessment for multiple changes
- No Beta validation integration for false positive detection
- No Core Triad notification mechanism for paradigm-level events
- No change velocity tracking

---

## 2. Implementation Architecture

### 2.1 Files to Create

```
src/heretek_swarm/coordination/
├── __init__.py                    # Update - add exports
├── paradigm_detection.py          # NEW - Paradigm shift detection module
```

### 2.2 Files to Modify

```
src/heretek_swarm/actors/catalyst.py  # ENHANCE - Add paradigm detection handlers
```

---

## 3. Detailed Implementation

### 3.1 `src/heretek_swarm/coordination/paradigm_detection.py` (NEW)

**Purpose**: Detect paradigm shifts in the swarm's operational context. A paradigm shift is a significant change in how the collective operates, not just individual changes but a pattern that suggests fundamental change in approach, technology, or behavior.

#### Data Structures

```python
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
import uuid

class ShiftType(Enum):
    """Types of paradigm shifts."""
    TECHNOLOGICAL = "technological"  # New tech stack, framework changes
    BEHAVIORAL = "behavioral"        # Agent interaction patterns change
    ARCHITECTURAL = "architectural"  # System structure changes
    PROTOCOL = "protocol"           # Communication/interface changes
    OPERATIONAL = "operational"     # Process/methodology changes

class ShiftMagnitude(Enum):
    """Magnitude of detected shift."""
    MINOR = "minor"      # Localized, recoverable
    MODERATE = "moderate"  # Affects multiple components
    MAJOR = "major"      # System-wide impact
    CRITICAL = "critical"  # Fundamental change requiring response

class ShiftConfidence(Enum):
    """Confidence level of shift detection."""
    SPECULATIVE = "speculative"  # < 50% confidence
    POSSIBLE = "possible"       # 50-70% confidence
    LIKELY = "likely"            # 70-85% confidence
    PROBABLE = "probable"        # 85-95% confidence
    CONFIRMED = "confirmed"       # > 95% confidence

class ShiftStatus(Enum):
    """Status of a detected paradigm shift."""
    DETECTED = "detected"
    VALIDATING = "validating"     # Beta validation in progress
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    MITIGATED = "mitigated"
    ESCALATED = "escalated"

@dataclass
class ShiftIndicator:
    """A single indicator contributing to shift detection."""
    indicator_id: str
    shift_type: ShiftType
    description: str
    first_detected: datetime = field(default_factory=lambda: datetime.now(UTC))
    occurrences: int = 0
    agents_involved: set[str] = field(default_factory=set)
    affected_components: list[str] = field(default_factory=list)
    confidence_boost: float = 0.0  # How much this indicator adds to confidence
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "indicator_id": self.indicator_id,
            "shift_type": self.shift_type.value,
            "description": self.description,
            "first_detected": self.first_detected.isoformat(),
            "occurrences": self.occurrences,
            "agents_involved": list(self.agents_involved),
            "affected_components": self.affected_components,
            "confidence_boost": self.confidence_boost,
        }

@dataclass
class ParadigmShift:
    """A detected paradigm shift."""
    shift_id: str
    shift_type: ShiftType
    magnitude: ShiftMagnitude
    confidence: ShiftConfidence
    status: ShiftStatus = ShiftStatus.DETECTED
    
    # Detection metadata
    indicators: list[ShiftIndicator] = field(default_factory=list)
    first_detected: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))
    detection_count: int = 0
    
    # Impact assessment
    affected_components: list[str] = field(default_factory=list)
    impacted_agents: list[str] = field(default_factory=list)
    impact_score: float = 0.0
    
    # Cumulative assessment (for rapid successive shifts)
    related_shifts: list[str] = field(default_factory=list)  # IDs of related shifts
    cumulative_impact: float = 0.0
    
    # Resolution
    validation_beta: str | None = None
    deliberation_id: str | None = None
    core_triad_notified: bool = False
    resolution_notes: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "shift_id": self.shift_id,
            "shift_type": self.shift_type.value,
            "magnitude": self.magnitude.value,
            "confidence": self.confidence.value,
            "status": self.status.value,
            "indicators": [i.to_dict() for i in self.indicators],
            "first_detected": self.first_detected.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "detection_count": self.detection_count,
            "affected_components": self.affected_components,
            "impacted_agents": self.impacted_agents,
            "impact_score": self.impact_score,
            "related_shifts": self.related_shifts,
            "cumulative_impact": self.cumulative_impact,
            "validation_beta": self.validation_beta,
            "deliberation_id": self.deliberation_id,
            "core_triad_notified": self.core_triad_notified,
            "resolution_notes": self.resolution_notes,
        }
```

#### Core Class: `ParadigmDetector`

```python
class ParadigmDetector:
    """
    Detects paradigm shifts in swarm behavior and operations.
    
    A paradigm shift is NOT:
    - A single change request
    - An isolated anomaly
    - Normal operational variance
    
    A paradigm shift IS:
    - A pattern of changes suggesting fundamental change
    - Multiple indicators converging on same conclusion
    - Velocity/scale beyond normal thresholds
    
    Responsibilities:
    1. Track change velocity and patterns
    2. Detect convergence of indicators
    3. Assess shift magnitude and confidence
    4. Trigger Beta validation for false positives
    5. Rate limit rapid successive shifts
    6. Calculate cumulative impact
    7. Notify Core Triad for high-magnitude shifts
    
    Key Methods:
    - analyze_change_velocity() - detect rapid successive changes
    - detect_shift_indicators() - identify paradigm shift signals
    - assess_shift_confidence() - calculate detection confidence
    - trigger_validation() - send to Beta for false positive check
    - notify_core_triad() - alert governance for major shifts
    - get_cumulative_impact() - aggregate impact of related shifts
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        pattern_extractor: PatternExtractor | None = None,
        deliberation_engine: SwarmDeliberationEngine | None = None,
        beta_agent_id: str = "beta",
        steward_agent_id: str = "steward",
        # Rate limiting
        min_shift_interval: timedelta = field(default_factory=lambda: timedelta(minutes=5)),
        max_shifts_per_hour: int = 10,
        # Detection thresholds
        indicator_threshold: int = 3,  # Min indicators for shift
        velocity_threshold: float = 2.0,  # Changes per minute
        confidence_threshold: float = 0.70,  # Min confidence to confirm
    ):
        self._config = config or {}
        
        # Detection state
        self._shifts: dict[str, ParadigmShift] = {}
        self._indicators: dict[str, list[ShiftIndicator]] = defaultdict(list)
        self._shift_history: list[ParadigmShift] = []
        
        # Rate limiting
        self._min_shift_interval = min_shift_interval
        self._max_shifts_per_hour = max_shifts_per_hour
        self._recent_shift_times: list[datetime] = []
        
        # Thresholds
        self._indicator_threshold = indicator_threshold
        self._velocity_threshold = velocity_threshold
        self._confidence_threshold = confidence_threshold
        
        # Dependencies
        self._pattern_extractor = pattern_extractor
        self._deliberation_engine = deliberation_engine
        
        # Agent IDs for notification
        self._beta_agent_id = beta_agent_id
        self._steward_agent_id = steward_agent_id
        
        # Change tracking for velocity
        self._change_timestamps: list[datetime] = []
        self._change_types: list[str] = []
        
        # Callbacks
        self._on_shift_detected: callable | None = None
        self._on_shift_confirmed: callable | None = None
        self._on_false_positive: callable | None = None
```

#### Change Velocity Analysis

```python
    async def analyze_change_velocity(self) -> dict[str, Any]:
        """
        Analyze change velocity to detect rapid successive shifts.
        
        Velocity metrics:
        - Changes per minute/hour
        - Types of changes clustered
        - Components affected in short window
        
        Returns:
            {
                "velocity": float,  # Changes per minute
                "is_rapid": bool,
                "cluster_type": str | None,
                "recommendation": str,
            }
        """
        now = datetime.now(UTC)
        
        # Clean old timestamps (older than 1 hour)
        self._change_timestamps = [
            ts for ts in self._change_timestamps
            if now - ts < timedelta(hours=1)
        ]
        
        if len(self._change_timestamps) < 2:
            return {
                "velocity": 0.0,
                "is_rapid": False,
                "cluster_type": None,
                "recommendation": "normal",
            }
        
        # Calculate velocity
        time_span = (now - self._change_timestamps[0]).total_seconds() / 60
        velocity = len(self._change_timestamps) / max(time_span, 1.0)
        
        # Check for clustering
        cluster_type = self._detect_change_cluster()
        
        # Determine if rapid
        is_rapid = velocity >= self._velocity_threshold
        
        return {
            "velocity": velocity,
            "is_rapid": is_rapid,
            "cluster_type": cluster_type,
            "recommendation": "rate_limit" if is_rapid else "normal",
        }
    
    async def record_change(self, change: ChangeRequest) -> None:
        """Record a change for velocity tracking."""
        self._change_timestamps.append(datetime.now(UTC))
        self._change_types.append(change.change_type.value)
        
        # Also check for paradigm shift indicators
        await self._check_shift_indicators(change)
```

#### Shift Indicator Detection

```python
    async def _check_shift_indicators(self, change: ChangeRequest) -> None:
        """
        Check if a change contributes to paradigm shift indicators.
        
        Indicators are grouped by shift_type:
        - TECHNOLOGICAL: Multiple deployment/upgrade changes to same component
        - BEHAVIORAL: Changes in how agents interact
        - ARCHITECTURAL: Structural changes to system
        - PROTOCOL: Interface/API changes
        - OPERATIONAL: Process methodology changes
        """
        # Analyze change for indicators
        indicators = self._extract_indicators_from_change(change)
        
        for indicator in indicators:
            self._indicators[indicator.shift_type.value].append(indicator)
            
            # Check if we have enough for a shift
            if len(self._indicators[indicator.shift_type.value]) >= self._indicator_threshold:
                await self._evaluate_shift(indicator.shift_type)
    
    async def _extract_indicators_from_change(
        self, change: ChangeRequest
    ) -> list[ShiftIndicator]:
        """Extract paradigm shift indicators from a change request."""
        indicators = []
        
        # Map change types to shift types
        type_mapping = {
            ChangeType.DEPLOYMENT: ShiftType.TECHNOLOGICAL,
            ChangeType.UPGRADE: ShiftType.TECHNOLOGICAL,
            ChangeType.MIGRATION: ShiftType.ARCHITECTURAL,
            ChangeType.CONFIGURATION: ShiftType.OPERATIONAL,
            ChangeType.PATCH: ShiftType.TECHNOLOGICAL,
        }
        
        shift_type = type_mapping.get(change.change_type)
        if not shift_type:
            return indicators
        
        # Create indicator
        indicator = ShiftIndicator(
            indicator_id=f"ind_{uuid.uuid4().hex[:12]}",
            shift_type=shift_type,
            description=f"Change pattern: {change.change_type.value} on {change.affected_components}",
            occurrences=1,
            agents_involved={change.requested_by},
            affected_components=change.affected_components,
            confidence_boost=self._calculate_indicator_boost(change),
        )
        
        indicators.append(indicator)
        
        # Check for behavioral indicators (multiple agents making similar changes)
        if len(self._get_agents_for_component(change.affected_components)) >= 3:
            behavioral = ShiftIndicator(
                indicator_id=f"ind_{uuid.uuid4().hex[:12]}",
                shift_type=ShiftType.BEHAVIORAL,
                description=f"Multi-agent coordination on {change.affected_components}",
                occurrences=1,
                agents_involved=self._get_agents_for_component(change.affected_components),
                affected_components=change.affected_components,
                confidence_boost=0.15,
            )
            indicators.append(behavioral)
        
        return indicators
```

#### Shift Evaluation and Confidence Assessment

```python
    async def _evaluate_shift(self, shift_type: ShiftType) -> ParadigmShift | None:
        """
        Evaluate if indicators constitute a paradigm shift.
        
        Confidence calculation factors:
        - Number of indicators (more = higher)
        - Indicator occurrences (recurring = higher)
        - Agents involved (more diverse = higher)
        - Time span (shorter = more significant)
        - Magnitude of changes (higher impact = higher)
        """
        indicators = self._indicators.get(shift_type.value, [])
        if len(indicators) < self._indicator_threshold:
            return None
        
        # Calculate confidence
        confidence = self._calculate_shift_confidence(indicators)
        
        # Determine magnitude based on impact
        magnitude = self._calculate_shift_magnitude(indicators)
        
        # Create shift record
        shift = ParadigmShift(
            shift_id=f"shift_{uuid.uuid4().hex[:12]}",
            shift_type=shift_type,
            magnitude=magnitude,
            confidence=confidence,
            indicators=indicators,
            affected_components=self._get_affected_components(indicators),
            impacted_agents=list(self._get_impacted_agents(indicators)),
            impact_score=self._calculate_impact_score(indicators),
        )
        
        self._shifts[shift.shift_id] = shift
        
        # Check rate limiting
        if await self._is_rate_limited(shift):
            logger.info(
                "paradigm_shift_rate_limited",
                shift_id=shift.shift_id,
                shift_type=shift_type.value,
            )
            return shift
        
        # High magnitude shifts notify Core Triad immediately
        if shift.magnitude in (ShiftMagnitude.MAJOR, ShiftMagnitude.CRITICAL):
            await self._notify_core_triad(shift)
        
        return shift
    
    def _calculate_shift_confidence(self, indicators: list[ShiftIndicator]) -> ShiftConfidence:
        """Calculate confidence level from indicators."""
        if not indicators:
            return ShiftConfidence.SPECULATIVE
        
        # Sum confidence boosts
        total_boost = sum(i.confidence_boost for i in indicators)
        
        # Factor in recurrence
        total_occurrences = sum(i.occurrences for i in indicators)
        recurrence_factor = min(total_occurrences / 10, 0.2)
        
        # Factor in diversity (more agents = higher confidence)
        all_agents = set()
        for i in indicators:
            all_agents.update(i.agents_involved)
        diversity_factor = min(len(all_agents) / 10, 0.15)
        
        confidence_score = min(1.0, total_boost + recurrence_factor + diversity_factor)
        
        # Map to confidence enum
        if confidence_score < 0.50:
            return ShiftConfidence.SPECULATIVE
        elif confidence_score < 0.70:
            return ShiftConfidence.POSSIBLE
        elif confidence_score < 0.85:
            return ShiftConfidence.LIKELY
        elif confidence_score < 0.95:
            return ShiftConfidence.PROBABLE
        else:
            return ShiftConfidence.CONFIRMED
```

#### False Positive Validation (Beta Integration)

```python
    async def trigger_validation(self, shift: ParadigmShift) -> str:
        """
        Trigger Beta validation for a detected shift.
        
        This handles false positives - shifts that appear significant
        but are actually normal operational variance.
        
        Returns:
            validation_id for tracking
        """
        shift.status = ShiftStatus.VALIDATING
        shift.validation_beta = self._beta_agent_id
        
        validation_id = f"val_{uuid.uuid4().hex[:12]}"
        
        logger.info(
            "paradigm_shift_validation_triggered",
            shift_id=shift.shift_id,
            validation_id=validation_id,
            confidence=shift.confidence.value,
        )
        
        # In production, this would send a message to Beta agent
        # For now, return validation_id
        return validation_id
    
    async def handle_validation_result(
        self,
        shift_id: str,
        is_false_positive: bool,
        validation_details: dict[str, Any] | None = None,
    ) -> None:
        """
        Handle result from Beta validation.
        
        Args:
            shift_id: The shift being validated
            is_false_positive: True if Beta determined this is not a real shift
            validation_details: Additional context from Beta
        """
        shift = self._shifts.get(shift_id)
        if not shift:
            return
        
        if is_false_positive:
            shift.status = ShiftStatus.FALSE_POSITIVE
            shift.resolution_notes = f"Beta validation: {validation_details.get('reason', 'False positive')}"
            logger.info(
                "paradigm_shift_false_positive",
                shift_id=shift_id,
                details=validation_details,
            )
            
            if self._on_false_positive:
                self._on_false_positive(shift)
        else:
            # Real shift - proceed with confidence
            shift.status = ShiftStatus.CONFIRMED
            await self._confirm_shift(shift)
```

#### Deliberation Resolution

```python
    async def trigger_deliberation(self, shift: ParadigmShift) -> str:
        """
        Trigger deliberation for ambiguous shifts.
        
        Used when:
        - Confidence is POSSIBLE or LIKELY (not high enough to confirm)
        - Beta validation inconclusive
        - Multiple shift types competing
        
        Returns:
            deliberation_id for tracking
        """
        shift.status = ShiftStatus.ESCALATED
        shift.deliberation_id = f"delib_{uuid.uuid4().hex[:12]}"
        
        logger.info(
            "paradigm_shift_deliberation_triggered",
            shift_id=shift.shift_id,
            deliberation_id=shift.deliberation_id,
            confidence=shift.confidence.value,
        )
        
        # In production, this would invoke SwarmDeliberationEngine
        # Return deliberation_id for tracking
        return shift.deliberation_id
```

#### Rate Limiting

```python
    async def _is_rate_limited(self, shift: ParadigmShift) -> bool:
        """
        Check if a shift should be rate-limited.
        
        Rate limiting prevents cascade false positives during
        rapid successive changes.
        """
        now = datetime.now(UTC)
        
        # Check minimum interval
        if self._recent_shift_times:
            last_shift = self._recent_shift_times[-1]
            if now - last_shift < self._min_shift_interval:
                logger.info(
                    "paradigm_shift_rate_limited_interval",
                    shift_id=shift.shift_id,
                    last_shift_age=(now - last_shift).total_seconds(),
                )
                return True
        
        # Check max shifts per hour
        self._recent_shift_times = [
            ts for ts in self._recent_shift_times
            if now - ts < timedelta(hours=1)
        ]
        
        if len(self._recent_shift_times) >= self._max_shifts_per_hour:
            logger.info(
                "paradigm_shift_rate_limited_max",
                shift_id=shift.shift_id,
                shifts_in_window=len(self._recent_shift_times),
            )
            return True
        
        self._recent_shift_times.append(now)
        return False
```

#### Cumulative Impact Assessment

```python
    async def get_cumulative_impact(self, shift_id: str) -> dict[str, Any]:
        """
        Calculate cumulative impact of related shifts.
        
        For rapid successive shifts, individual assessments
        may understate total impact.
        """
        shift = self._shifts.get(shift_id)
        if not shift:
            return {"cumulative_impact": 0.0, "related_shifts": []}
        
        # Find related shifts (same type, within time window)
        related = []
        now = datetime.now(UTC)
        
        for other_id, other in self._shifts.items():
            if other_id == shift_id:
                continue
            
            # Same type
            if other.shift_type != shift.shift_type:
                continue
            
            # Within 1 hour
            if (now - other.first_detected) > timedelta(hours=1):
                continue
            
            related.append(other_id)
        
        # Calculate cumulative impact
        total_impact = shift.impact_score
        for related_id in related:
            related_shift = self._shifts[related_id]
            total_impact += related_shift.impact_score * 0.5  # 50% weight for related
        
        # Cap at 1.0
        cumulative = min(1.0, total_impact)
        
        # Update shift
        shift.cumulative_impact = cumulative
        shift.related_shifts = related
        
        return {
            "cumulative_impact": cumulative,
            "related_shifts": related,
            "is_significant": cumulative > 0.7,
        }
```

#### Core Triad Notification

```python
    async def _notify_core_triad(self, shift: ParadigmShift) -> None:
        """
        Notify Core Triad (Steward) of high-magnitude shift.
        
        Format:
        - message_type: "paradigm_shift_alert"
        - content: {
            "shift_id": str,
            "shift_type": str,
            "magnitude": str,
            "confidence": str,
            "impact_score": float,
            "affected_components": list[str],
            "indicator_count": int,
            "requires_intervention": bool,
        }
        """
        shift.core_triad_notified = True
        
        logger.info(
            "core_triad_notified_paradigm_shift",
            shift_id=shift.shift_id,
            shift_type=shift.shift_type.value,
            magnitude=shift.magnitude.value,
        )
        
        # In production, this would send via NATS to Steward
        # Message format:
        # {
        #     "message_type": "paradigm_shift_alert",
        #     "content": {
        #         "shift_id": shift.shift_id,
        #         "shift_type": shift.shift_type.value,
        #         "magnitude": shift.magnitude.value,
        #         "confidence": shift.confidence.value,
        #         "impact_score": shift.impact_score,
        #         "affected_components": shift.affected_components,
        #         "indicator_count": len(shift.indicators),
        #         "requires_intervention": shift.magnitude in (MAJOR, CRITICAL),
        #     }
        # }
```

---

### 3.2 Catalyst Enhancements (`src/heretek_swarm/actors/catalyst.py`)

#### New Imports

```python
from heretek_swarm.coordination.paradigm_detection import (
    ParadigmDetector,
    ParadigmShift,
    ShiftType,
    ShiftMagnitude,
    ShiftConfidence,
    ShiftStatus,
    ShiftIndicator,
)
```

#### New Attributes

```python
# Paradigm detection
self._paradigm_detector: ParadigmDetector | None = None
self._paradigm_shifts: dict[str, ParadigmShift] = {}

# Rate limiting for rapid successive changes
self._shift_rate_limiter: dict[str, datetime] = {}  # shift_type -> last detection
self._min_shift_interval_seconds: int = self._config.get("min_shift_interval", 300)

# Change velocity tracking
self._change_velocity_window: timedelta = timedelta(minutes=10)
self._change_timestamps: list[datetime] = []
```

#### New Message Handlers

```python
# In _register_handlers()
"detect_paradigm_shift": self._handle_detect_paradigm_shift,
"get_paradigm_shift_status": self._handle_get_paradigm_shift_status,
"validate_paradigm_shift": self._handle_validate_paradigm_shift,
"get_shift_velocity": self._handle_get_shift_velocity,
"get_cumulative_impact": self._handle_get_cumulative_impact,
```

#### New Methods

```python
async def _handle_detect_paradigm_shift(self, message: ActorMessage) -> None:
    """
    Detect paradigm shift from change patterns.
    
    Content: {
        "change_id": str,  # Optional - analyze specific change
        "shift_type": str,  # Optional - filter by type
        "force_analysis": bool,  # Force analysis even if rate limited
    }
    
    Returns: {
        "shift_detected": bool,
        "shift": ParadigmShift | None,
        "rate_limited": bool,
    }
    """

async def _handle_get_paradigm_shift_status(self, message: ActorMessage) -> None:
    """
    Get status of paradigm shifts.
    
    Content: {
        "shift_id": str | None,  # Specific shift or None for all
    }
    
    Returns: {
        "shifts": list[ParadigmShift],
        "count": int,
    }
    """

async def _handle_validate_paradigm_shift(self, message: ActorMessage) -> None:
    """
    Handle Beta validation result for false positive check.
    
    Content: {
        "shift_id": str,
        "is_false_positive": bool,
        "validation_details": dict | None,
    }
    """

async def _handle_get_shift_velocity(self, message: ActorMessage) -> None:
    """
    Get current change velocity metrics.
    
    Returns: {
        "velocity": float,  # Changes per minute
        "is_rapid": bool,
        "cluster_type": str | None,
    }
    """

async def _handle_get_cumulative_impact(self, message: ActorMessage) -> None:
    """
    Get cumulative impact for a shift.
    
    Content: {
        "shift_id": str,
    }
    
    Returns: {
        "cumulative_impact": float,
        "related_shifts": list[str],
        "is_significant": bool,
    }
    """
```

#### Integration with Change Handlers

```python
async def _handle_propose_change(self, message: ActorMessage) -> None:
    """Existing handler - add paradigm detection."""
    # ... existing code ...
    
    # NEW: Record for velocity tracking and shift detection
    if self._paradigm_detector:
        await self._paradigm_detector.record_change(change)
        
        # Check for rapid successive changes
        velocity = await self._paradigm_detector.analyze_change_velocity()
        if velocity["is_rapid"]:
            # Trigger cumulative impact assessment
            logger.warning(
                "rapid_change_velocity_detected",
                change_id=change_id,
                velocity=velocity["velocity"],
            )
```

---

## 4. Integration Points

### 4.1 With Change Management (Catalyst Core)

- Change proposals feed into paradigm detection
- High-impact changes trigger shift analysis
- Change velocity tracked across all types

### 4.2 With Beta Agent (False Positive Validation)

- Detected shifts sent to Beta for validation
- Beta response updates shift status
- Delibration resolution for ambiguous cases

### 4.3 With Core Triad (Steward)

- Major/Critical shifts notify Steward immediately
- Shift alerts include magnitude, confidence, impact
- Requires intervention flag for governance awareness

### 4.4 With PatternExtractor (Session 44 Integration)

- Uses PatternExtractor for pattern analysis
- Integrates with SwarmDeliberationEngine for deliberation
- AccessPatternAnalyzer for access pattern analysis

---

## 5. Edge Case Handling

### 5.1 False Positive Paradigm Shift

**Detection Flow**:
```
Change recorded
    ↓
Analyze change velocity
    ↓
Indicators exceed threshold
    ↓
Shift detected (status: DETECTED)
    ↓
Trigger Beta validation
    ↓
Beta validates (true/false)
    ↓ (false positive)
Status = FALSE_POSITIVE
    ↓
Resolution notes recorded
    ↓
Shift archived in history
```

**Beta Validation Request**:
```python
{
    "message_type": "paradigm_shift_validation_request",
    "content": {
        "shift_id": "shift_abc123",
        "shift_type": "technological",
        "indicators": [...],
        "affected_components": ["component-1", "component-2"],
        "confidence": "likely",
        "requested_validation": "is_this_a_true_paradigm_shift",
    }
}
```

**Beta Validation Response**:
```python
{
    "message_type": "paradigm_shift_validation_response",
    "content": {
        "shift_id": "shift_abc123",
        "is_false_positive": False,  # or True
        "reason": "Confirmed: 5+ agents deploying same pattern",
        "confidence_in_assessment": 0.95,
    }
}
```

### 5.2 Rapid Successive Shifts

**Rate Limiting Flow**:
```
Shift detected
    ↓
Check min interval (default: 5 min)
    ↓ (too soon)
Rate limited
    ↓
Log rate limit event
    ↓
Return shift with rate_limited=True

OR

Check max shifts per hour (default: 10)
    ↓ (exceeded)
Rate limited
    ↓
Cumulative impact assessment
    ↓
If cumulative > threshold, notify Core Triad anyway
```

**Cumulative Impact Assessment**:
```python
# Related shifts (same type, within 1 hour) have cumulative effect
cumulative_impact = (
    current_shift.impact_score +
    sum(related.impact_score * 0.5 for related in related_shifts)
)
```

**Notification Threshold**:
- Individual shift magnitude >= MAJOR → notify immediately
- Cumulative impact >= 0.7 → notify even if individual < MAJOR

---

## 6. Verification Criteria

| Criterion | Measurement | Pass Threshold |
|-----------|-------------|----------------|
| Paradigm shift detection | Shifts detected from change patterns | Indicators → Shift conversion works |
| Change velocity analysis | Velocity calculation | Detects rapid successive changes |
| False positive validation | Beta validation flow | False positives confirmed by Beta |
| Rate limiting | Rapid successive detection | Rate limited shifts logged |
| Cumulative impact | Impact aggregation | Related shifts cumulative > individual |
| Core Triad notification | Steward notified | Major/Critical shifts alert Steward |
| Magnitude assessment | MAJOR/CRITICAL detection | Magnitude correlates with impact |
| Confidence scoring | SPECULATIVE → CONFIRMED | Confidence increases with indicators |

---

## 7. Implementation Order

### Phase 1: Paradigm Detection Module (Day 1-3)

1. Create `src/heretek_swarm/coordination/__init__.py` update
2. Create `src/heretek_swarm/coordination/paradigm_detection.py`
   - Data classes: ShiftType, ShiftMagnitude, ShiftConfidence, ShiftStatus, ShiftIndicator, ParadigmShift
   - ParadigmDetector class with core detection logic
   - Change velocity analysis
   - Indicator extraction
   - Confidence calculation

### Phase 2: Rate Limiting and Cumulative Assessment (Day 2-3)

3. Add rate limiting to ParadigmDetector
4. Add cumulative impact assessment
5. Add helper methods for tracking

### Phase 3: Catalyst Integration (Day 4-5)

6. Enhance `src/heretek_swarm/actors/catalyst.py`
   - Add imports for paradigm_detection
   - Add _paradigm_detector attribute
   - Add new message handlers
   - Integrate with existing _handle_propose_change
   - Add notification methods

### Phase 4: Testing & Verification (Day 6-7)

7. Create tests:
   - `tests/coordination/test_paradigm_detection.py` (~200 lines)

8. Verify:
   - Shift detection works from change patterns
   - False positives validated by Beta
   - Rate limiting activates for rapid shifts
   - Core Triad notification for major shifts

---

## 8. File Summary

| File | Action | Lines Added |
|------|--------|-------------|
| `src/heretek_swarm/coordination/paradigm_detection.py` | CREATE | ~600 |
| `src/heretek_swarm/coordination/__init__.py` | UPDATE | ~20 |
| `src/heretek_swarm/actors/catalyst.py` | ENHANCE | ~200 |
| `tests/coordination/test_paradigm_detection.py` | CREATE | ~200 |

**Total New Code**: ~820 lines
**Total Test Code**: ~200 lines

---

## 9. Dependencies

```
INTG-01 (Task Synchronization) ─────────────────────┐
                                                       │
INTG-02 (Nexus External API) ─────────────────────────┤──► INTG-03 (This Task)
                                                       │
Phase 1 (PatternExtractor, DeliberationEngine) ──────┘
```

**Phase 1 dependencies**:
- PatternExtractor for pattern analysis
- SwarmDeliberationEngine for deliberation
- Agent base class for messaging

**Task dependencies**:
- INTG-01 must complete before INTG-03 can be fully tested
- INTG-02 provides external API context for shift detection

---

## 10. Open Questions (for resolution during implementation)

1. **Indicator threshold**: 3 indicators default — appropriate for detection sensitivity?

2. **Velocity threshold**: 2.0 changes/minute — should this be configurable per shift_type?

3. **Cumulative impact weighting**: 50% weight for related shifts — should this vary by magnitude?

4. **Core Triad notification format**: What specific fields does Steward need for governance action?

5. **Shift history retention**: How long to keep archived shifts for pattern analysis?

6. **Integration with existing ChangeRequest**: Should paradigm shifts create their own ChangeRequests or be separate?

---

## 11. Monitoring and Alerting

### Health Metrics to Track

```python
{
    "paradigm_shifts_detected": 5,
    "shifts_pending_validation": 1,
    "false_positives_rate": 0.15,  # 15% false positive rate
    "avg_detection_confidence": 0.72,
    "rate_limited_shifts": 2,
    "core_triad_notifications": 3,
    "active_shifts": {
        "technological": 2,
        "behavioral": 1,
        "architectural": 0,
        "protocol": 0,
        "operational": 1,
    },
    "cumulative_impact_events": 1,
}
```

### Alerting Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| false_positives_rate | > 20% | > 30% |
| shifts_pending_validation | > 5 | > 10 |
| rate_limited_shifts | > 5/hr | > 10/hr |
| core_triad_notifications | > 2/hr | > 5/hr |
| active_shifts | > 10 total | > 20 total |

---

## 12. Future Enhancements (Out of Scope for INTG-03)

- ML-based shift prediction (predict before indicators appear)
- Cross-component shift correlation analysis
- Shift pattern memory (learn from past false positives)
- Automated mitigation strategies for confirmed shifts
- Shift simulation (what-if analysis for potential shifts)