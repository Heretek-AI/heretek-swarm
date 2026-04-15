# Implementation Plan: INTG-04 — Chronos Time Perception

## Task Overview

**Owner**: Chronos
**Depends**: Phase 1 (Agent base class)
**Files**:
- `src/heretek_swarm/actors/chronos.py` (enhance - already exists)
- `src/heretek_swarm/coordination/time_dilation.py` (create)

**Verification**: Chronos manages long-running execution context; time perception metrics; adaptive timeout handling.

## Edge Cases

- Chronos itself overloaded — delegation to Coordinator; graceful degradation
- Time perception drift — reality anchoring against external clocks

---

## 1. Analysis of Existing Code

### 1.1 Chronos Agent (`src/heretek_swarm/actors/chronos.py`)

**Current Capabilities**:
- `ScheduledTask` and `Deadline` dataclasses
- `ScheduleStatus` enum (PENDING, ACTIVE, PAUSED, COMPLETED, CANCELLED, MISSED, FAILED)
- `RecurrenceType` enum (ONCE, HOURLY, DAILY, WEEKLY, MONTHLY, YEARLY, CRON, INTERVAL)
- `Priority` enum (LOW=1 to CRITICAL=5)
- Basic task scheduling via `_handle_schedule_task()`
- Deadline management via `_handle_set_deadline()` and `_check_deadlines()`
- Scheduler loop: `_run_scheduler()` checking every `check_interval` (default 1s)
- Task execution: `_execute_task()` notifies target agents
- Recurrence handling: `_schedule_next_run()`
- Message handlers: `schedule_task`, `cancel_task`, `pause_task`, `resume_task`, `get_task_status`, `set_deadline`, `check_deadline`, `get_timeline`, `get_schedule`, `register_reminder`

**Missing for INTG-04**:
- No long-running execution context tracking
- No time perception metrics (subjective vs objective time)
- No adaptive timeout handling based on workload
- No reality anchoring against external clocks
- No overload detection and delegation to Coordinator
- No time dilation handling for agent perception
- No execution context lifecycle beyond simple task completion

---

## 2. Implementation Architecture

### 2.1 Files to Create

```
src/heretek_swarm/coordination/
├── __init__.py                    # Package init (shared with INTG-01)
├── time_dilation.py              # NEW - Time perception and adaptive timeout
```

### 2.2 Files to Modify

```
src/heretek_swarm/actors/chronos.py  # ENHANCE - Integrate time_dilation
```

---

## 3. Detailed Implementation

### 3.1 `src/heretek_swarm/coordination/time_dilation.py` (NEW)

**Purpose**: Time perception management with adaptive timeouts, reality anchoring, and overload handling.

#### Data Structures

```python
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
import uuid

class TimeDomain(Enum):
    """Time domains for perception management."""
    REAL = "real"           # Wall-clock time
    SUBJECTIVE = "subjective"  # Perceived time by agent
    DILATED = "dilated"     # Stretched time under load

class OverloadState(Enum):
    """States of Chronos overload handling."""
    NORMAL = "normal"
    LOADED = "loaded"
    OVERLOADED = "overloaded"
    DEGRADED = "degraded"

class AnchorSource(Enum):
    """Sources for time reality anchoring."""
    SYSTEM_CLOCK = "system_clock"
    NTP_SERVER = "ntp_server"
    EXTERNAL_API = "external_api"
    COORDINATOR = "coordinator"

@dataclass
class ExecutionContext:
    """Long-running execution context tracked by Chronos."""
    context_id: str
    agent_id: str
    task_id: str
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expected_duration: timedelta | None = None
    deadline: datetime | None = None
    subjective_start: datetime = field(default_factory=lambda: datetime.now(UTC))
    checkpoint_count: int = 0
    progress_percent: float = 0.0
    status: str = "running"  # running, paused, completed, failed, cancelled
    time_dilation_factor: float = 1.0  # How much time is dilated (1.0 = normal)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def wallclock_elapsed(self) -> timedelta:
        """Actual wall-clock time elapsed."""
        return datetime.now(UTC) - self.started_at
    
    @property
    def subjective_elapsed(self) -> timedelta:
        """Perceived time by the agent (may be dilated)."""
        return self.wallclock_elapsed * self.time_dilation_factor
    
    @property
    def time_remaining(self) -> timedelta | None:
        """Time remaining until deadline, None if no deadline."""
        if self.deadline is None:
            return None
        return self.deadline - datetime.now(UTC)
    
    @property
    def is_at_risk(self) -> bool:
        """Check if context is at risk of missing deadline."""
        if self.time_remaining is None:
            return False
        # At risk if less than 10% of time remaining and less than 50% progress
        return self.time_remaining.total_seconds() < (self.expected_duration.total_seconds() * 0.1) and self.progress_percent < 50.0

@dataclass
class TimePerceptionMetrics:
    """Metrics for time perception tracking."""
    total_contexts: int = 0
    active_contexts: int = 0
    completed_contexts: int = 0
    failed_contexts: int = 0
    avg_dilation_factor: float = 1.0
    max_dilation_factor: float = 1.0
    perception_drift_seconds: float = 0.0  # Difference between subjective and real
    deadline_misses: int = 0
    adaptive_timeouts_triggered: int = 0
    last_anchor_check: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "total_contexts": self.total_contexts,
            "active_contexts": self.active_contexts,
            "completed_contexts": self.completed_contexts,
            "failed_contexts": self.failed_contexts,
            "avg_dilation_factor": self.avg_dilation_factor,
            "max_dilation_factor": self.max_dilation_factor,
            "perception_drift_seconds": self.perception_drift_seconds,
            "deadline_misses": self.deadline_misses,
            "adaptive_timeouts_triggered": self.adaptive_timeouts_triggered,
            "last_anchor_check": self.last_anchor_check.isoformat(),
        }

@dataclass
class AdaptiveTimeout:
    """Configuration for adaptive timeout handling."""
    base_timeout: timedelta = field(default_factory=lambda: timedelta(seconds=30))
    max_timeout: timedelta = field(default_factory=lambda: timedelta(minutes=5))
    min_timeout: timedelta = field(default_factory=lambda: timedelta(seconds=5))
    scale_factor: float = 1.5  # How much to scale on retry
    workload_threshold: float = 0.7  # Load at which to start scaling
    decay_rate: float = 0.95  # Decay factor for timeout reduction
    
    def calculate_timeout(self, retry_count: int, current_load: float) -> timedelta:
        """Calculate adaptive timeout based on retries and load."""
        scale = min(self.scale_factor ** retry_count, 5.0)
        if current_load > self.workload_threshold:
            scale *= (1.0 + (current_load - self.workload_threshold))
        timeout_seconds = self.base_timeout.total_seconds() * scale
        timeout_seconds = max(
            self.min_timeout.total_seconds(),
            min(self.max_timeout.total_seconds(), timeout_seconds)
        )
        return timedelta(seconds=timeout_seconds)
```

#### Core Class: `TimePerceptionManager`

```python
class TimePerceptionManager:
    """
    Time perception management with adaptive timeouts and reality anchoring.
    
    Responsibilities:
    1. Track long-running execution contexts
    2. Calculate time perception metrics (subjective vs objective time)
    3. Detect and handle time perception drift
    4. Provide adaptive timeout handling based on workload
    5. Anchor reality against external clocks (system, NTP, coordinator)
    6. Detect Chronos overload and delegate to Coordinator
    
    Key Methods:
    - create_context(), update_context(), checkpoint_context()
    - get_perception_metrics() - time perception statistics
    - anchor_time() - reality anchoring against external sources
    - calculate_adaptive_timeout() - workload-aware timeout scaling
    - detect_drift() - perception drift detection
    - get_overload_state() - current overload classification
    - delegate_to_coordinator() - overload fallback
    """

    def __init__(
        self,
        max_contexts: int = 1000,
        drift_threshold_seconds: float = 5.0,
        anchor_interval: timedelta = timedelta(minutes=5),
    ):
        # Execution contexts
        self._contexts: dict[str, ExecutionContext] = {}
        self._max_contexts = max_contexts
        
        # Time anchoring
        self._anchor_source: AnchorSource = AnchorSource.SYSTEM_CLOCK
        self._last_anchor_time: datetime = field(default_factory=lambda: datetime.now(UTC))
        self._anchor_interval = anchor_interval
        self._drift_threshold_seconds = drift_threshold_seconds
        self._perception_drift: float = 0.0
        
        # Adaptive timeout configuration
        self._adaptive_timeout = AdaptiveTimeout()
        
        # Metrics
        self._metrics = TimePerceptionMetrics()
        
        # Overload detection
        self._overload_threshold: float = 0.8  # 80% capacity
        self._current_load: float = 0.0
        
        # Delegation
        self._coordinator_proxy: Any = None
        
        # Callbacks
        self._on_overload: callable | None = None
        self._on_deadline_miss: callable | None = None
        self._on_drift_detected: callable | None = None

    # === Context Management ===
    
    def create_context(
        self,
        agent_id: str,
        task_id: str,
        expected_duration: timedelta | None = None,
        deadline: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionContext:
        """
        Create a new execution context for long-running operations.
        
        Returns:
            ExecutionContext with unique context_id
        """
        
    def get_context(self, context_id: str) -> ExecutionContext | None:
        """Get execution context by ID."""
        
    def update_context(
        self,
        context_id: str,
        progress_percent: float | None = None,
        status: str | None = None,
        time_dilation_factor: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Update execution context state.
        
        Returns:
            True if updated, False if not found
        """
        
    def checkpoint_context(self, context_id: str) -> dict[str, Any] | None:
        """
        Create a checkpoint of context state for recovery.
        
        Returns:
            Checkpoint data or None if context not found
        """
        
    def complete_context(self, context_id: str) -> bool:
        """
        Mark context as completed and record metrics.
        
        Returns:
            True if completed, False if not found
        """
        
    def fail_context(self, context_id: str, reason: str) -> bool:
        """
        Mark context as failed.
        
        Returns:
            True if failed, False if not found
        """

    # === Time Perception Metrics ===
    
    def get_perception_metrics(self) -> TimePerceptionMetrics:
        """
        Calculate and return time perception metrics.
        
        Returns:
            TimePerceptionMetrics with current statistics
        """
        
    def calculate_wallclock_elapsed(self, context_id: str) -> timedelta | None:
        """
        Calculate wall-clock time for a context.
        
        Returns:
            Elapsed time or None if context not found
        """
        
    def calculate_subjective_elapsed(self, context_id: str) -> timedelta | None:
        """
        Calculate perceived time for a context (may include dilation).
        
        Returns:
            Subjective elapsed time or None if context not found
        """
        
    def get_time_remaining(self, context_id: str) -> timedelta | None:
        """
        Get time remaining until deadline.
        
        Returns:
            Time remaining or None if no deadline/context not found
        """

    # === Reality Anchoring ===
    
    async def anchor_time(self, source: AnchorSource = AnchorSource.SYSTEM_CLOCK) -> dict[str, Any]:
        """
        Anchor time perception to an external source.
        
        Sources:
        - SYSTEM_CLOCK: Use system datetime (default)
        - NTP_SERVER: Use NTP server (if available)
        - EXTERNAL_API: Use external time API
        - COORDINATOR: Use Coordinator's trusted clock
        
        Returns:
            {
                "anchored": bool,
                "source": str,
                "anchor_time": datetime,
                "drift_detected": bool,
                "drift_seconds": float,
            }
        """
        
    async def check_and_anchor(self) -> dict[str, Any]:
        """
        Periodic anchoring check - called by scheduler.
        
        Returns:
            Anchoring result if check performed
        """
        
    def detect_drift(self, context_id: str) -> dict[str, Any] | None:
        """
        Detect time perception drift for a context.
        
        Returns:
            Drift info if detected, None otherwise
        """
        
    def get_drift_stats(self) -> dict[str, Any]:
        """
        Get overall drift statistics.
        
        Returns:
            {
                "total_drift_seconds": float,
                "max_drift_seconds": float,
                "anchor_count": int,
                "last_drift_detected": datetime | None,
            }
        """

    # === Adaptive Timeout Handling ===
    
    def calculate_adaptive_timeout(
        self,
        operation: str,
        retry_count: int = 0,
        context_id: str | None = None,
    ) -> timedelta:
        """
        Calculate adaptive timeout based on workload and context.
        
        Returns:
            Calculated timeout duration
        """
        
    def register_timeout_event(
        self,
        operation: str,
        timeout_used: timedelta,
        succeeded: bool,
    ) -> None:
        """
        Register timeout event for adaptive learning.
        
        Records actual timeout used vs calculated to improve future estimates.
        """
        
    def get_timeout_recommendation(self, operation: str) -> dict[str, Any]:
        """
        Get timeout recommendation for an operation type.
        
        Returns:
            {
                "recommended_timeout": timedelta,
                "operation": str,
                "recent_avg": timedelta,
                "pattern": str,  # "stable", "increasing", "decreasing"
            }
        """

    # === Overload Detection & Delegation ===
    
    def update_load(self, current_load: float) -> None:
        """
        Update current system load for overload detection.
        
        Called by Chronos scheduler based on active contexts.
        """
        
    def get_overload_state(self) -> OverloadState:
        """
        Determine current overload state.
        
        Returns:
            OverloadState enum value
        """
        
    async def delegate_to_coordinator(
        self,
        context_id: str,
        reason: str,
        fallback_action: str = "reschedule",
    ) -> dict[str, Any]:
        """
        Delegate context handling to Coordinator when Chronos is overloaded.
        
        Returns:
            {
                "delegated": bool,
                "coordinator_id": str | None,
                "context_transferred": bool,
                "fallback_action": str,
            }
        """
        
    def should_delegate(self, context_id: str | None = None) -> tuple[bool, str]:
        """
        Determine if delegation is needed.
        
        Returns:
            (should_delegate, reason)
        """

    # === Metrics & Health ===
    
    def get_metrics(self) -> TimePerceptionMetrics:
        """Get current time perception metrics."""
        
    async def emit_health_report(self) -> dict[str, Any]:
        """
        Emit health report for HealthReportingMixin.
        
        Returns:
            Health status dictionary
        """
```

#### Time Dilation Implementation

```python
class TimeDilationCalculator:
    """
    Calculates time dilation factors based on system load and context.
    
    Time dilation allows Chronos to stretch perceived time for agents
    when under heavy load, preventing premature deadline misses.
    """
    
    def __init__(
        self,
        base_dilation: float = 1.0,
        max_dilation: float = 3.0,
        load_threshold: float = 0.6,
    ):
        self._base_dilation = base_dilation
        self._max_dilation = max_dilation
        self._load_threshold = load_threshold
        
    def calculate_dilation(self, current_load: float, context_priority: int = 2) -> float:
        """
        Calculate time dilation factor.
        
        Formula:
        - Below load_threshold: dilation = 1.0 (no dilation)
        - Above load_threshold: dilation = 1.0 + (load - threshold) * scale_factor
        
        Priority affects scale:
        - CRITICAL (5): Lower dilation (keep them running fast)
        - LOW (1): Higher dilation (they can wait)
        
        Returns:
            Dilation factor (1.0 to max_dilation)
        """
        
    def adjust_deadline(
        self,
        original_deadline: datetime,
        current_load: float,
        progress_percent: float,
    ) -> datetime:
        """
        Adjust deadline based on load and progress.
        
        When system is overloaded, extended deadlines for
        lower-priority tasks to prevent cascade failures.
        
        Returns:
            Adjusted deadline (may be further in future)
        """
```

#### Overload Detection & Delegation

```python
class OverloadDetector:
    """
    Detects when Chronos is becoming overloaded.
    
    Uses multiple signals:
    - Active context count vs max_contexts
    - System load average
    - Average context age
    - Deadline miss rate
    """
    
    def __init__(
        self,
        context_weight: float = 0.4,
        load_weight: float = 0.3,
        age_weight: float = 0.2,
        miss_rate_weight: float = 0.1,
    ):
        self._weights = {
            "context": context_weight,
            "load": load_weight,
            "age": age_weight,
            "miss_rate": miss_rate_weight,
        }
        
    def calculate_overload_score(self) -> float:
        """
        Calculate overall overload score (0.0 to 1.0).
        
        0.0 = No load
        0.5 = Moderate load
        1.0 = Critical overload
        
        Returns:
            Overload score
        """
        
    def should_delegate(self, score: float, threshold: float = 0.8) -> bool:
        """
        Determine if delegation is warranted.
        
        Returns:
            True if score exceeds threshold
        """
```

#### Example Usage

```python
# Initialize time perception manager
tpm = TimePerceptionManager(
    max_contexts=1000,
    drift_threshold_seconds=5.0,
)

# Create execution context for long-running task
context = tpm.create_context(
    agent_id="coder_abc123",
    task_id="task_build_001",
    expected_duration=timedelta(minutes=30),
    deadline=datetime.now(UTC) + timedelta(minutes=45),
)

# Update progress periodically
tpm.update_context(
    context.context_id,
    progress_percent=50.0,
)

# Check if at risk
if context.is_at_risk:
    print("Context at risk of deadline miss")
    
# Get perception metrics
metrics = tpm.get_perception_metrics()
print(f"Active contexts: {metrics.active_contexts}")
print(f"Avg dilation: {metrics.avg_dilation_factor}")

# Handle overload
if tpm.should_delegate()[0]:
    await tpm.delegate_to_coordinator(context.context_id, "Chronos overloaded")

# Anchor time periodically
anchor_result = await tpm.anchor_time(AnchorSource.COORDINATOR)
if anchor_result["drift_detected"]:
    print(f"Drift detected: {anchor_result['drift_seconds']} seconds")
```

---

## 4. Integration with Chronos Agent

### 4.1 New Imports

```python
from heretek_swarm.coordination.time_dilation import (
    TimePerceptionManager,
    ExecutionContext,
    TimePerceptionMetrics,
    AdaptiveTimeout,
    TimeDomain,
    OverloadState,
    AnchorSource,
    TimeDilationCalculator,
    OverloadDetector,
)
```

### 4.2 New Attributes

```python
# Time perception manager
self._time_manager: TimePerceptionManager | None = None

# Dilation calculator
self._dilation_calculator: TimeDilationCalculator | None = None

# Overload detector
self._overload_detector: OverloadDetector | None = None

# Execution contexts
self._execution_contexts: dict[str, ExecutionContext] = {}

# Configuration
self._enable_time_dilation: bool = self._config.get("enable_time_dilation", True)
self._anchor_interval_seconds: float = self._config.get("anchor_interval", 300)  # 5 min
self._overload_threshold: float = self._config.get("overload_threshold", 0.8)
self._max_contexts: int = self._config.get("max_contexts", 500)
```

### 4.3 New Message Handlers

```python
# In _register_handlers()
"create_execution_context": self._handle_create_context,
"update_execution_context": self._handle_update_context,
"checkpoint_context": self._handle_checkpoint_context,
"get_context_status": self._handle_get_context_status,
"get_time_perception_metrics": self._handle_get_metrics,
"anchor_time": self._handle_anchor_time,
"get_adaptive_timeout": self._handle_get_adaptive_timeout,
"delegate_to_coordinator": self._handle_delegate,
```

### 4.4 New Methods

```python
async def _handle_create_context(self, message: ActorMessage) -> None:
    """
    Create a long-running execution context.
    
    Content: {
        "agent_id": str,
        "task_id": str,
        "expected_duration": str | None (ISO8601 timedelta),
        "deadline": str | None (ISO8601 datetime),
        "priority": int | None (1-5),
        "metadata": dict | None,
    }
    
    Returns: {
        "context": ExecutionContext.to_dict(),
        "context_id": str,
    }
    """

async def _handle_update_context(self, message: ActorMessage) -> None:
    """
    Update execution context progress.
    
    Content: {
        "context_id": str,
        "progress_percent": float,
        "status": str | None,
        "time_dilation_factor": float | None,
        "metadata": dict | None,
    }
    """

async def _handle_checkpoint_context(self, message: ActorMessage) -> None:
    """
    Create a checkpoint for context recovery.
    
    Content: {"context_id": str}
    
    Returns: Checkpoint data for persistence
    """

async def _handle_get_context_status(self, message: ActorMessage) -> None:
    """
    Get status of an execution context.
    
    Content: {"context_id": str}
    
    Returns: {
        "context": ExecutionContext.to_dict(),
        "wallclock_elapsed": str,
        "subjective_elapsed": str,
        "time_remaining": str | None,
        "is_at_risk": bool,
    }
    """

async def _handle_get_metrics(self, message: ActorMessage) -> None:
    """
    Get time perception metrics.
    
    Returns: TimePerceptionMetrics.to_dict()
    """

async def _handle_anchor_time(self, message: ActorMessage) -> None:
    """
    Anchor time perception to external source.
    
    Content: {"source": str}  # system_clock, ntp_server, coordinator
    
    Returns: Anchoring result
    """

async def _handle_get_adaptive_timeout(self, message: ActorMessage) -> None:
    """
    Get adaptive timeout for an operation.
    
    Content: {
        "operation": str,
        "retry_count": int,
        "context_id": str | None,
    }
    
    Returns: {
        "timeout_seconds": float,
        "timeout_recommended": str,
    }
    """

async def _handle_delegate(self, message: ActorMessage) -> None:
    """
    Delegate context to Coordinator when overloaded.
    
    Content: {
        "context_id": str,
        "reason": str,
        "fallback_action": str | None,
    }
    """
```

### 4.5 Scheduler Integration

```python
async def _run_scheduler(self) -> None:
    """Enhanced scheduler with time perception management."""
    while self._scheduler_running:
        try:
            now = datetime.now(UTC)
            
            # Existing: Check for due tasks
            # ...
            
            # NEW: Periodic anchoring check
            if self._time_manager and self._enable_time_dilation:
                await self._time_manager.check_and_anchor()
                
            # NEW: Check context deadlines and update metrics
            await self._check_context_deadlines()
            
            # NEW: Update overload state
            self._update_overload_state()
            
            # NEW: Check if delegation needed
            if self._should_delegate():
                await self._handle_overload_delegation()
            
        except Exception as e:
            logger.error("scheduler_error", error=str(e))
        
        await asyncio.sleep(self._check_interval)

async def _check_context_deadlines(self) -> None:
    """Check execution context deadlines and send warnings."""
    for context in self._execution_contexts.values():
        if context.status != "running":
            continue
            
        if context.is_at_risk:
            await self._send_context_warning(context)
            
        if context.time_remaining and context.time_remaining.total_seconds() <= 0:
            await self._handle_context_deadline_miss(context)

def _update_overload_state(self) -> None:
    """Update overload detection based on current load."""
    active_count = sum(1 for c in self._execution_contexts.values() if c.status == "running")
    load = active_count / self._max_contexts if self._max_contexts > 0 else 0
    
    if self._time_manager:
        self._time_manager.update_load(load)

async def _handle_overload_delegation(self) -> None:
    """Delegate low-priority contexts to Coordinator."""
    # Find contexts that could be delegated
    delegatable = [
        c for c in self._execution_contexts.values()
        if c.status == "running" 
        and c.metadata.get("priority", 2) <= 2  # LOW or NORMAL
    ]
    
    if delegatable:
        context = delegatable[0]  # Delegate one at a time
        await self._time_manager.delegate_to_coordinator(
            context.context_id,
            "Chronos overloaded",
        )

async def _send_context_warning(self, context: ExecutionContext) -> None:
    """Send warning about at-risk context."""
    await self.send(
        context.agent_id,
        ActorMessage(
            message_type="context_at_risk",
            content={
                "context_id": context.context_id,
                "task_id": context.task_id,
                "time_remaining": str(context.time_remaining),
                "progress_percent": context.progress_percent,
                "deadline": context.deadline.isoformat() if context.deadline else None,
            },
            sender_id=self.agent_id,
        ),
    )
```

---

## 5. Edge Case Handling

### 5.1 Chronos Overloaded — Delegation to Coordinator

**Detection Flow**:
```
Chronos Load Increases
    ↓
OverloadDetector calculates score
    ↓
Score > threshold (0.8)?
    ↓ (yes)
Check delegatable contexts
    ↓
Priority <= 2? (LOW/NORMAL)
    ↓ (yes)
Call TimePerceptionManager.delegate_to_coordinator()
    ↓
Send message to Coordinator with context details
    ↓
Coordinator acknowledges transfer
    ↓
Remove from Chronos, context now managed by Coordinator
```

**Delegation Message Format**:
```python
{
    "message_type": "context_delegated",
    "content": {
        "context_id": "ctx_abc123",
        "agent_id": "coder_xyz",
        "task_id": "task_001",
        "original_deadline": "2026-04-14T15:30:00Z",
        "progress_percent": 45.0,
        "reason": "Chronos overloaded",
        "checkpoint_data": {...},
        "requires_coordinator_management": True,
    }
}
```

**Graceful Degradation**:
1. First: Pause low-priority contexts (not cancel)
2. Then: Dilate time for medium-priority contexts
3. Finally: Delegate to Coordinator if still overloaded

### 5.2 Time Perception Drift — Reality Anchoring

**Drift Detection Flow**:
```
Periodic Anchor Check (every 5 minutes)
    ↓
Compare Chronos internal time with anchor source
    ↓
Calculate drift: |anchor_time - internal_time|
    ↓
Drift > threshold (5 seconds)?
    ↓ (yes)
Log drift event
    ↓
Update perception_drift metric
    ↓
If drift > 30 seconds: Alert, attempt re-anchoring
    ↓
Adjust time_dilation_factor for active contexts
```

**Anchor Sources Priority**:
1. **COORDINATOR** (highest trust) - If Coordinator available and trusted
2. **NTP_SERVER** - If NTP service available
3. **EXTERNAL_API** - If external time API configured
4. **SYSTEM_CLOCK** (fallback) - Local system clock

**Drift Adjustment**:
```python
# When drift detected, adjust active context time dilation
def adjust_for_drift(self, drift_seconds: float) -> None:
    for context in self._execution_contexts.values():
        if context.status == "running":
            # Increase dilation to "catch up" perceived time
            # If we're behind, stretch time to match anchor
            if drift_seconds > 0:
                context.time_dilation_factor *= (1.0 + (drift_seconds / 100))
            else:
                # We're ahead, reduce dilation
                context.time_dilation_factor *= (1.0 - abs(drift_seconds) / 100)
```

---

## 6. Verification Criteria

| Criterion | Measurement | Pass Threshold |
|-----------|-------------|----------------|
| Execution context tracking | Contexts created and tracked | Contexts stored with wallclock/subjective time |
| Time perception metrics | Metrics calculated | Metrics include dilation, drift, active counts |
| Adaptive timeout handling | Timeout calculation | Timeouts scale with load and retry count |
| Time dilation | Dilation factor calculated | Factors range 1.0 to max_dilation based on load |
| Reality anchoring | Anchor checks performed | Anchoring occurs at configured interval |
| Drift detection | Drift events logged | Drift > threshold triggers adjustment |
| Overload detection | Overload state tracked | States: normal, loaded, overloaded, degraded |
| Delegation to Coordinator | Delegation messages sent | Overload triggers delegation |
| Graceful degradation | Context handling under load | No context loss during degradation |
| Health reporting | Health metrics emitted | Report includes perception metrics |

---

## 7. Implementation Order

### Phase 1: Core Data Structures (Day 1)

1. Create `src/heretek_swarm/coordination/__init__.py`
   - Package initialization
   - Exports for public API

2. Create `src/heretek_swarm/coordination/time_dilation.py`
   - `ExecutionContext`, `TimePerceptionMetrics`, `AdaptiveTimeout` dataclasses
   - `TimeDomain`, `OverloadState`, `AnchorSource` enums
   - `TimePerceptionManager` class with context management
   - Basic create/get/update context methods

### Phase 2: Time Perception (Day 2-3)

3. Implement time perception metrics in `TimePerceptionManager`
   - `get_perception_metrics()`
   - `calculate_wallclock_elapsed()`, `calculate_subjective_elapsed()`
   - `get_time_remaining()`

4. Implement `TimeDilationCalculator`
   - `calculate_dilation()` based on load and priority
   - `adjust_deadline()` for overloaded scenarios

### Phase 3: Reality Anchoring (Day 3-4)

5. Implement reality anchoring in `TimePerceptionManager`
   - `anchor_time()` with multiple source support
   - `check_and_anchor()` periodic check
   - `detect_drift()` and `get_drift_stats()`

### Phase 4: Overload Handling (Day 4-5)

6. Implement `OverloadDetector`
   - `calculate_overload_score()`
   - `should_delegate()`

7. Implement delegation in `TimePerceptionManager`
   - `delegate_to_coordinator()`
   - `should_delegate()`

8. Enhance Chronos agent with time perception handlers

### Phase 5: Integration & Testing (Day 6-7)

9. Integrate time perception into Chronos scheduler
   - Context deadline checking
   - Overload state updates
   - Delegation handling

10. Create tests:
    - `tests/coordination/test_time_dilation.py` (~150 lines)
    - `tests/coordination/test_chronos_time.py` (~100 lines)

11. Verify all criteria pass

---

## 8. File Summary

| File | Action | Lines Added |
|------|--------|-------------|
| `src/heretek_swarm/coordination/__init__.py` | CREATE | ~30 |
| `src/heretek_swarm/coordination/time_dilation.py` | CREATE | ~550 |
| `src/heretek_swarm/actors/chronos.py` | ENHANCE | ~250 |

**Total New Code**: ~580 lines
**Total Test Code**: ~250 lines

---

## 9. Dependencies

```
Phase 1 (Agent base class) ──────────────────────────────► INTG-04
                                                              │
Phase 2: INTG-01 (TaskSynchronizer) ─────────────────────────┤
                                                              │
Phase 2: SAFE-02 (HealthReportingMixin) ─────────────────────┤
                                                              │
Phase 2: CONS-02 (Consensus Tribunal) ────────────────────────┘
```

**Phase 1 dependencies**:
- Agent base class for actor functionality
- HealthReportingMixin for health reports
- ValidationMixin for message validation

**Task dependencies**:
- INTG-04 is independent from INTG-01, 02, 03 (can be implemented in parallel)
- All Phase 2 integration tasks depend on Phase 1 base

---

## 10. Open Questions (for resolution during implementation)

1. **Dilation factor calculation**: The formula `1.0 + (load - threshold) * scale_factor` — what scale factor value is appropriate? Start with 2.0?

2. **Anchor source priority**: Should Coordinator always be preferred if available, or should it depend on trust level?

3. **Delegation scope**: Should delegation transfer the entire context or just deadline management? Transferring full context is cleaner but more complex.

4. **Context vs existing tasks**: Should ExecutionContext replace ScheduledTask for long-running operations, or are they separate concepts?

5. **Time domain perception**: Should agents be able to query their "subjective" time, or is this only used internally by Chronos?

6. **Drift threshold values**: 5 seconds drift threshold — appropriate for the swarm's tolerance? Could be too sensitive or too lenient.

---

## 11. Monitoring and Alerting

### Health Metrics to Track

```python
{
    "time_perception": {
        "active_contexts": 15,
        "total_contexts": 150,
        "avg_dilation_factor": 1.35,
        "max_dilation_factor": 2.1,
        "perception_drift_seconds": 2.5,
    },
    "overload": {
        "state": "normal",  # normal, loaded, overloaded, degraded
        "current_load": 0.45,
        "overload_score": 0.3,
        "contexts_delegated": 2,
    },
    "deadlines": {
        "at_risk_contexts": 1,
        "deadline_misses": 0,
        "adaptive_timeouts_triggered": 5,
    },
    "anchoring": {
        "last_anchor": "2026-04-14T10:25:00Z",
        "anchor_source": "coordinator",
        "drift_detected_count": 0,
    }
}
```

### Alerting Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| active_contexts / max_contexts | > 70% | > 90% |
| overload_state | overloaded | degraded |
| perception_drift_seconds | > 10 | > 30 |
| deadline_misses | > 0 in 5min | > 0 ongoing |
| at_risk_contexts | > 2 | > 5 |

---

## 12. Future Enhancements (Out of Scope for INTG-04)

- NTP server integration for precise time anchoring
- ML-based deadline prediction based on historical context data
- Cross-agent time perception synchronization
- Predictive overload detection based on task patterns
- Hierarchical time domains (agent-local vs swarm-global time)