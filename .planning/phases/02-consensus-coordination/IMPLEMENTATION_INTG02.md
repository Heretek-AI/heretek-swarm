# Implementation Plan: INTG-02 — Nexus Gateway External API Handling

## Task Overview

**Owner**: Nexus
**Depends**: Phase 1 (ZERO-01 operational)
**Verification**: Nexus handles all external API interactions; protocol translation operational; zero-trust coverage maintained.

## Edge Cases

- API rate limit violations — automatic backoff; logging
- API provider failure — fallback mechanisms; graceful degradation

---

## 1. Analysis of Existing Code

### 1.1 Nexus Agent (`src/heretek_swarm/actors/nexus.py`)

**Current Capabilities**:
- `ExternalConnection` dataclass with protocol, auth, rate_limit tracking
- `WebhookConfig` for webhook endpoint management
- `ApiResponse` standardized API response format
- ZERO-01 hostile input treatment with 6-layer sanitization
- Connection management: create, update, delete, status
- Webhook management: register, unregister, validate, status
- Basic protocol translation via `_translate_data()`
- Request execution via aiohttp with auth handling (bearer, basic, api_key)
- Rate limiting per connection via `rate_limit_remaining`
- Request logging for audit

**Missing for INTG-02**:
- No automatic backoff on rate limit violations (429 responses)
- No retry logic with exponential backoff
- No circuit breaker pattern for provider failure
- No fallback/secondary endpoint mechanisms
- No request queuing for deferred retry
- No dedicated external API client module in gateway/

---

## 2. Implementation Architecture

### 2.1 Files to Create

```
src/heretek_swarm/gateway/
├── external_api.py              # NEW - External API client with resilience
```

### 2.2 Files to Modify

```
src/heretek_swarm/actors/nexus.py  # ENHANCE - Integrate external_api.py
```

---

## 3. Detailed Implementation

### 3.1 `src/heretek_swarm/gateway/external_api.py` (NEW)

**Purpose**: Centralized external API client with automatic backoff, circuit breaker, fallback mechanisms, and graceful degradation.

#### Data Structures

```python
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
import asyncio
import random

class RetryStrategy(Enum):
    """Retry backoff strategies."""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIBONACCI = "fibonacci"

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovery possible

@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    initial_delay_ms: int = 100
    max_delay_ms: int = 30000
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter: bool = True  # Add randomness to prevent thundering herd
    
    @property
    def jitter_factor(self) -> float:
        """Jitter factor for randomization (0.0-1.0)."""
        return 0.1 if self.jitter else 0.0

@dataclass
class RateLimitConfig:
    """Configuration for rate limit handling."""
    requests_per_minute: int = 60
    burst_size: int | None = None  # None = no burst limit
    auto_backoff: bool = True
    backoff_multiplier: float = 2.0
    max_backoff_ms: int = 60000

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes in half-open to close
    timeout_seconds: float = 30.0  # Time before trying half-open
    excluded_status_codes: list[int] = field(
        default_factory=lambda: [400, 401, 403, 404]
    )

@dataclass
class FallbackConfig:
    """Configuration for fallback endpoints."""
    enabled: bool = False
    fallback_endpoints: list[str] = field(default_factory=list)
    health_check_interval_seconds: float = 30.0
    require_all_healthy: bool = False

@dataclass
class APIRequestMetrics:
    """Metrics for an API request."""
    request_id: str
    attempt: int = 0
    total_retries: int = 0
    latency_ms: int = 0
    status_code: int | None = None
    error: str | None = None
    rate_limited: bool = False
    circuit_open: bool = False
    fallback_used: bool = False
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "attempt": self.attempt,
            "total_retries": self.total_retries,
            "latency_ms": self.latency_ms,
            "status_code": self.status_code,
            "error": self.error,
            "rate_limited": self.rate_limited,
            "circuit_open": self.circuit_open,
            "fallback_used": self.fallback_used,
            "timestamp": self.timestamp.isoformat(),
        }
```

#### Core Class: `RateLimitHandler`

```python
class RateLimitHandler:
    """
    Handles rate limiting with automatic backoff.
    
    Responsibilities:
    1. Track request rates per endpoint/connection
    2. Detect rate limit violations (429 responses)
    3. Calculate backoff delay automatically
    4. Queue requests when rate limited
    5. Log all rate limit events
    
    Key Methods:
    - check_rate_limit() - Returns True if request allowed
    - record_response() - Process response, update limits
    - get_backoff_delay() - Calculate backoff for retry
    - wait_if_needed() - Async wait if rate limited
    """

    def __init__(self, config: RateLimitConfig | None = None):
        self._config = config or RateLimitConfig()
        
        # Rate tracking: endpoint -> list of request timestamps
        self._request_times: dict[str, list[datetime]] = {}
        
        # Rate limit state per endpoint
        self._rate_limited_until: dict[str, datetime | None] = {}
        
        # Backoff state per endpoint
        self._current_backoff_ms: dict[str, float] = {}
        
        # Metrics
        self._total_rate_limits: int = 0
        self._total_requests: int = 0
        
    def check_rate_limit(self, endpoint: str) -> bool:
        """
        Check if request to endpoint is allowed.
        
        Returns:
            True if allowed, False if should wait
        """
        
    def record_response(self, endpoint: str, status_code: int, 
                       retry_after: int | None = None) -> None:
        """
        Record response from API endpoint.
        
        Updates rate tracking and backoff state based on response.
        
        Args:
            endpoint: The API endpoint
            status_code: HTTP status code
            retry_after: Retry-After header value (seconds)
        """
        
    def get_backoff_delay(self, endpoint: str) -> float:
        """
        Get backoff delay for retry.
        
        Returns:
            Delay in seconds
        """
        
    async def wait_if_needed(self, endpoint: str) -> None:
        """
        Wait if endpoint is rate limited.
        
        Async wait implementation for use in request loop.
        """
        
    def get_metrics(self) -> dict[str, Any]:
        """Get rate limiting metrics."""
```

#### Core Class: `CircuitBreaker`

```python
class CircuitBreaker:
    """
    Circuit breaker pattern implementation for API resilience.
    
    Responsibilities:
    1. Track failures per endpoint
    2. Open circuit after threshold failures
    3. Allow testing after timeout (half-open)
    4. Close circuit after successes
    5. Reject requests immediately when open
    
    State Machine:
    
    CLOSED → (failures >= threshold) → OPEN
    OPEN → (timeout elapsed) → HALF_OPEN
    HALF_OPEN → (successes >= threshold) → CLOSED
    HALF_OPEN → (failure) → OPEN
    
    Key Methods:
    - can_execute() - Returns True if request allowed
    - record_success() - Record successful request
    - record_failure() - Record failed request
    - get_state() - Get current circuit state
    """

    def __init__(self, config: CircuitBreakerConfig | None = None):
        self._config = config or CircuitBreakerConfig()
        
        # State per endpoint
        self._states: dict[str, CircuitState] = {}
        self._failure_counts: dict[str, int] = {}
        self._success_counts: dict[str, int] = {}
        self._last_failure_time: dict[str, datetime | None] = {}
        self._opened_at: dict[str, datetime | None] = {}
        
    def can_execute(self, endpoint: str) -> tuple[bool, CircuitState]:
        """
        Check if request can execute.
        
        Returns:
            (can_execute, current_state)
        """
        
    def record_success(self, endpoint: str) -> None:
        """
        Record successful request.
        
        In HALF_OPEN: increments success count, closes if threshold reached
        In CLOSED: resets failure count
        """
        
    def record_failure(self, endpoint: str, 
                      status_code: int | None = None) -> None:
        """
        Record failed request.
        
        In CLOSED: increments failure count, opens if threshold reached
        In HALF_OPEN: immediately opens circuit
        In OPEN: no change (already open)
        
        Args:
            endpoint: The API endpoint
            status_code: HTTP status code (for excluded codes)
        """
        
    def get_state(self, endpoint: str) -> CircuitState:
        """Get circuit state for endpoint."""
        
    def get_metrics(self, endpoint: str) -> dict[str, Any]:
        """Get circuit breaker metrics for endpoint."""
```

#### Core Class: `FallbackManager`

```python
class FallbackManager:
    """
    Manages fallback endpoints for API resilience.
    
    Responsibilities:
    1. Track primary and fallback endpoints
    2. Monitor health of fallback endpoints
    3. Select best available endpoint
    4. Rotate through fallbacks on failure
    5. Mark endpoints as unhealthy after failures
    
    Key Methods:
    - get_available_endpoint() - Get best available endpoint
    - record_failure() - Mark endpoint as failing
    - record_success() - Mark endpoint as healthy
    - get_health_status() - Get health of all endpoints
    """

    def __init__(self, config: FallbackConfig | None = None):
        self._config = config or FallbackConfig()
        
        # All endpoints with health status
        self._endpoints: dict[str, dict[str, Any]] = {}
        
        # Current primary index for rotation
        self._current_primary_index: int = 0
        
    def add_endpoint(self, url: str, is_primary: bool = True,
                     metadata: dict[str, Any] | None = None) -> None:
        """
        Add an endpoint to the pool.
        
        Args:
            url: The endpoint URL
            is_primary: True if this is a primary (preferred) endpoint
            metadata: Optional metadata (name, region, etc.)
        """
        
    def get_available_endpoint(self) -> str | None:
        """
        Get best available endpoint.
        
        Priority:
        1. Primary if healthy
        2. Fallbacks in order if primary unhealthy
        3. Any healthy endpoint
        
        Returns:
            Endpoint URL or None if all unavailable
        """
        
    def record_failure(self, endpoint: str) -> None:
        """
        Record failure for endpoint.
        
        Marks endpoint as unhealthy, may trigger fallback selection.
        """
        
    def record_success(self, endpoint: str) -> None:
        """
        Record success for endpoint.
        
        Marks endpoint as healthy.
        """
        
    def get_health_status(self) -> dict[str, Any]:
        """Get health status of all endpoints."""
        
    def reset(self) -> None:
        """Reset all endpoints to healthy state."""
```

#### Core Class: `ResilientAPIClient`

```python
class ResilientAPIClient:
    """
    External API client with automatic retry, rate limiting, circuit breaker,
    and fallback support.
    
    Responsibilities:
    1. Execute HTTP requests with automatic retry
    2. Handle rate limits with backoff
    3. Circuit breaker for failing providers
    4. Fallback to secondary endpoints
    5. Zero-trust validation of requests/responses
    6. Comprehensive metrics and logging
    
    Key Methods:
    - request() - Execute HTTP request with full resilience
    - get() - GET request shorthand
    - post() - POST request shorthand
    - put() - PUT request shorthand
    - delete() - DELETE request shorthand
    
    Example:
    ```python
    client = ResilientAPIClient(
        retry_config=RetryConfig(max_retries=3),
        rate_limit_config=RateLimitConfig(requests_per_minute=60),
        circuit_breaker_config=CircuitBreakerConfig(failure_threshold=5),
        fallback_config=FallbackConfig(
            enabled=True,
            fallback_endpoints=["https://backup-api.example.com"]
        )
    )
    
    response = await client.request(
        "GET",
        "https://api.example.com/data",
        headers={"Authorization": "Bearer token"}
    )
    ```
    """

    def __init__(
        self,
        session: aiohttp.ClientSession | None = None,
        retry_config: RetryConfig | None = None,
        rate_limit_config: RateLimitConfig | None = None,
        circuit_breaker_config: CircuitBreakerConfig | None = None,
        fallback_config: FallbackConfig | None = None,
        timeout_seconds: float = 30.0,
        zero_trust_enabled: bool = True,
    ):
        self._session = session
        self._retry_config = retry_config or RetryConfig()
        self._rate_limiter = RateLimitHandler(rate_limit_config)
        self._circuit_breaker = CircuitBreaker(circuit_breaker_config)
        self._fallback_manager = FallbackManager(fallback_config)
        self._timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self._zero_trust_enabled = zero_trust_enabled
        
        # Metrics aggregation
        self._total_requests: int = 0
        self._total_errors: int = 0
        self._total_rate_limits: int = 0
        self._total_circuit_breaks: int = 0
        self._total_fallbacks: int = 0
        
    async def request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        json: Any = None,
        data: Any = None,
        retry_count: int = 0,
        request_id: str | None = None,
    ) -> ApiResponse:
        """
        Execute HTTP request with full resilience.
        
        Flow:
        1. Check circuit breaker
        2. Check rate limit
        3. Execute request
        4. Handle rate limit (429): backoff and retry
        5. Handle server error (5xx): retry with backoff
        6. Handle client error (4xx): don't retry
        7. Handle network error: retry
        8. Record metrics
        
        Args:
            method: HTTP method
            url: Request URL
            headers: Optional headers
            params: Optional query params
            json: JSON body
            data: Form data
            retry_count: Current retry attempt
            request_id: Optional request ID for tracing
            
        Returns:
            ApiResponse with success status and data
        """
        
    async def _execute_with_retry(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None,
        params: dict[str, str] | None,
        json: Any,
        data: Any,
        retry_count: int,
        request_id: str,
    ) -> ApiResponse:
        """
        Internal retry loop with exponential backoff.
        """
        
    def _should_retry(self, status_code: int, retry_count: int) -> bool:
        """
        Determine if request should be retried.
        
        Retry on:
        - Rate limit (429)
        - Server errors (500-599)
        - Network errors
        
        Don't retry on:
        - Client errors (400-499 except 429)
        - Max retries exceeded
        """
        
    def _calculate_backoff(self, retry_count: int, 
                          retry_after_ms: int | None = None) -> float:
        """
        Calculate backoff delay with jitter.
        
        Args:
            retry_count: Current retry attempt (0-indexed)
            retry_after_ms: Server-provided retry-after in milliseconds
            
        Returns:
            Delay in seconds
        """
        
    async def _handle_rate_limit(
        self,
        url: str,
        status_code: int,
        headers: dict[str, str],
        retry_count: int,
    ) -> tuple[bool, float]:
        """
        Handle rate limit response.
        
        Returns:
            (should_retry, backoff_seconds)
        """
        
    def _update_circuit_breaker(self, url: str, status_code: int,
                               is_error: bool) -> None:
        """Update circuit breaker state based on response."""
        
    def _update_fallback(self, url: str, is_error: bool) -> None:
        """Update fallback manager based on response."""
        
    async def get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> ApiResponse:
        """Execute GET request."""
        
    async def post(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        json: Any = None,
        data: Any = None,
    ) -> ApiResponse:
        """Execute POST request."""
        
    async def put(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        json: Any = None,
        data: Any = None,
    ) -> ApiResponse:
        """Execute PUT request."""
        
    async def delete(
        self,
        url: str,
        headers: dict[str, str] | None = None,
    ) -> ApiResponse:
        """Execute DELETE request."""
        
    def get_metrics(self) -> dict[str, Any]:
        """Get aggregated client metrics."""
```

#### Retry Logic Details

```python
def _calculate_backoff(self, retry_count: int, 
                      retry_after_ms: int | None = None) -> float:
    """
    Calculate backoff delay with exponential/fibonacci strategy.
    
    Formula (exponential):
        delay = min(initial_delay * (multiplier ^ retry_count), max_delay)
    
    Formula (fibonacci):
        delay = fibonacci(retry_count + 2) * initial_delay
    
    With jitter:
        delay = delay * (1 + random.uniform(-jitter_factor, jitter_factor))
    
    If retry_after from server:
        delay = max(delay, retry_after_ms / 1000)
    """
    
def _should_retry(self, status_code: int, retry_count: int) -> bool:
    """
    Decision matrix for retry:
    
    | Status | Retry? | Reason |
    |--------|--------|--------|
    | 429    | Yes    | Rate limited |
    | 500    | Yes    | Server error |
    | 502    | Yes    | Bad gateway |
    | 503    | Yes    | Service unavailable |
    | 504    | Yes    | Gateway timeout |
    | 400    | No     | Bad request (fix first) |
    | 401    | No     | Unauthorized (auth issue) |
    | 403    | No     | Forbidden (auth issue) |
    | 404    | No     | Not found |
    | >= 500 | Yes    | Server error |
    | Network| Yes    | Connection issue |
    """
```

#### Rate Limit Detection

```python
def _detect_rate_limit(self, status_code: int, 
                      headers: dict[str, str]) -> tuple[bool, int | None]:
    """
    Detect rate limiting from response.
    
    Rate limiting can be detected via:
    1. Status code 429
    2. Retry-After header
    3. X-RateLimit-* headers (if provider supplies)
    
    Returns:
        (is_rate_limited, retry_after_seconds)
    """
    if status_code == 429:
        retry_after = headers.get("Retry-After")
        if retry_after:
            try:
                return True, int(retry_after)
            except ValueError:
                pass
        return True, self._rate_limiter._config.max_backoff_ms // 1000
    
    # Check for provider-specific rate limit headers
    # GitHub: X-RateLimit-Remaining, X-RateLimit-Reset
    # Slack: Retry-After
    # etc.
    
    return False, None
```

---

## 4. Nexus Agent Enhancements

### 4.1 New Imports

```python
from heretek_swarm.gateway.external_api import (
    ResilientAPIClient,
    RateLimitHandler,
    CircuitBreaker,
    FallbackManager,
    RetryConfig,
    RateLimitConfig,
    CircuitBreakerConfig,
    FallbackConfig,
    RetryStrategy,
    CircuitState,
)
```

### 4.2 New Attributes

```python
# External API client with resilience
self._api_client: ResilientAPIClient | None = None

# Per-connection resilience config (can be overridden per connection)
self._retry_config: RetryConfig = RetryConfig(
    max_retries=3,
    initial_delay_ms=100,
    max_delay_ms=30000,
)
self._rate_limit_config: RateLimitConfig = RateLimitConfig(
    requests_per_minute=60,
    auto_backoff=True,
)
self._circuit_breaker_config: CircuitBreakerConfig = CircuitBreakerConfig(
    failure_threshold=5,
    timeout_seconds=30.0,
)
self._fallback_config: FallbackConfig = FallbackConfig(
    enabled=False,  # Enable per-connection as needed
)

# Request metrics
self._api_metrics: list[APIRequestMetrics] = []
self._max_metrics_entries: int = 1000
```

### 4.3 Initialize API Client

```python
async def initialize(self) -> None:
    """Initialize the Nexus agent."""
    await super().initialize()
    
    # HTTP session
    self._session = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=self._config.get("timeout", 30)),
    )
    
    # Create resilient API client
    self._api_client = ResilientAPIClient(
        session=self._session,
        retry_config=self._retry_config,
        rate_limit_config=self._rate_limit_config,
        circuit_breaker_config=self._circuit_breaker_config,
        fallback_config=self._fallback_config,
        timeout_seconds=self._config.get("timeout", 30),
        zero_trust_enabled=True,
    )
    
    logger.info("nexus_http_session_initialized")
    logger.info(
        "nexus_resilience_configured",
        retry=self._retry_config.max_retries,
        rate_limit=self._rate_limit_config.requests_per_minute,
        circuit_breaker_threshold=self._circuit_breaker_config.failure_threshold,
    )
```

### 4.4 Enhanced `_handle_execute_request`

```python
async def _handle_execute_request(self, message: ActorMessage) -> None:
    """
    Execute an HTTP request through a connection WITH RESILIENCE.
    
    Content:
    - connection_id: str
    - method: str (GET|POST|PUT|DELETE|PATCH)
    - path: str
    - body: Optional[Any]
    - headers: Optional[Dict]
    - params: Optional[Dict]
    - use_fallback: Optional[bool] - Enable fallback endpoints
    - max_retries: Optional[int] - Override retry count
    """
    try:
        content = await self._validate_message(message)
        connection_id = content.get("connection_id")

        if not connection_id or connection_id not in self._connections:
            await self._send_error(
                message.sender_id,
                f"Connection {connection_id} not found",
                message.message_type,
            )
            return

        connection = self._connections[connection_id]

        # Check connection-level rate limit
        if connection.rate_limit and connection.rate_limit_remaining <= 0:
            connection.status = ConnectionStatus.RATE_LIMITED
            await self._send_error(
                message.sender_id,
                "Connection rate limit exceeded",
                message.message_type,
            )
            return

        if not self._session:
            await self._send_error(
                message.sender_id,
                "HTTP session not initialized",
                message.message_type,
            )
            return

        # Build URL
        url = f"{connection.base_url}{content.get('path', '')}"

        # Prepare headers
        headers = {**connection.headers, **(content.get("headers", {}))}

        # Add auth if configured
        headers = self._add_auth_headers(connection, headers)

        # Get retry config override if provided
        max_retries = content.get("max_retries", self._retry_config.max_retries)
        retry_config = RetryConfig(
            max_retries=max_retries,
            initial_delay_ms=self._retry_config.initial_delay_ms,
            max_delay_ms=self._retry_config.max_delay_ms,
        )

        # Configure fallback if requested
        use_fallback = content.get("use_fallback", False)
        if use_fallback and connection.metadata.get("fallback_endpoints"):
            fallback_config = FallbackConfig(
                enabled=True,
                fallback_endpoints=connection.metadata.get("fallback_endpoints", []),
            )
        else:
            fallback_config = self._fallback_config

        # Execute request with resilience
        method = content.get("method", "GET").upper()
        request_id = str(uuid.uuid4())
        
        start_time = datetime.now(UTC)
        
        response = await self._api_client.request(
            method=method,
            url=url,
            headers=headers,
            params=content.get("params"),
            json=content.get("body"),
            retry_count=0,
            request_id=request_id,
        )
        
        latency = (datetime.now(UTC) - start_time).total_seconds() * 1000

        # Update connection stats
        connection.last_request = datetime.now(UTC)
        connection.total_requests += 1
        connection.rate_limit_remaining = max(0, connection.rate_limit_remaining - 1)
        
        if not response.success:
            connection.failed_requests += 1
            connection.status = ConnectionStatus.ERROR

        # Log request
        self._log_request(connection_id, method, url, response.status_code, latency)
        
        # Record API metrics
        self._record_api_metrics(
            request_id=request_id,
            connection_id=connection_id,
            method=method,
            latency_ms=int(latency),
            success=response.success,
            status_code=response.status_code,
            error=response.error,
        )

        await self.send(
            message.sender_id,
            ActorMessage(
                message_type="request_completed",
                content={
                    "response": response.to_dict(),
                    "metrics": {
                        "total_retries": 0,  # From response
                        "rate_limited": False,  # From response
                    }
                },
                sender_id=self.agent_id,
            ),
        )

    except Exception as e:
        logger.error("execute_request_failed", error=str(e))
        if connection_id in self._connections:
            self._connections[connection_id].failed_requests += 1
            self._connections[connection_id].status = ConnectionStatus.ERROR
        await self._send_error(
            message.sender_id,
            f"Request failed: {e!s}",
            message.message_type,
        )
```

### 4.5 New Message Handlers

```python
# In _register_handlers()
"get_api_metrics": self._handle_get_api_metrics,
"configure_retry": self._handle_configure_retry,
"configure_rate_limit": self._handle_configure_rate_limit,
"configure_circuit_breaker": self._handle_configure_circuit_breaker,
"add_fallback_endpoint": self._handle_add_fallback_endpoint,
"get_resilience_status": self._handle_get_resilience_status,
"reset_circuit_breaker": self._handle_reset_circuit_breaker,
```

### 4.6 New Handler Methods

```python
async def _handle_get_api_metrics(self, message: ActorMessage) -> None:
    """
    Get API request metrics.
    
    Content: {
        "limit": Optional[int]  # Max entries to return
    }
    
    Returns: {
        "metrics": list[APIRequestMetrics],
        "summary": {
            "total_requests": int,
            "total_errors": int,
            "total_rate_limits": int,
            "total_circuit_breaks": int,
            "total_fallbacks": int,
        }
    }
    """

async def _handle_configure_retry(self, message: ActorMessage) -> None:
    """
    Configure retry behavior.
    
    Content: {
        "max_retries": int,
        "initial_delay_ms": int,
        "max_delay_ms": int,
        "strategy": str (exponential|linear|fibonacci),
        "jitter": bool,
    }
    """

async def _handle_configure_rate_limit(self, message: ActorMessage) -> None:
    """
    Configure rate limit handling.
    
    Content: {
        "requests_per_minute": int,
        "burst_size": Optional[int],
        "auto_backoff": bool,
        "backoff_multiplier": float,
        "max_backoff_ms": int,
    }
    """

async def _handle_configure_circuit_breaker(self, message: ActorMessage) -> None:
    """
    Configure circuit breaker.
    
    Content: {
        "failure_threshold": int,
        "success_threshold": int,
        "timeout_seconds": float,
        "excluded_status_codes": list[int],
    }
    """

async def _handle_add_fallback_endpoint(self, message: ActorMessage) -> None:
    """
    Add fallback endpoint for a connection.
    
    Content: {
        "connection_id": str,
        "fallback_url": str,
        "metadata": Optional[dict],
    }
    """

async def _handle_get_resilience_status(self, message: ActorMessage) -> None:
    """
    Get resilience component status.
    
    Returns: {
        "circuit_breakers": dict[str, CircuitState],
        "rate_limiter_metrics": dict,
        "fallback_health": dict,
    }
    """

async def _handle_reset_circuit_breaker(self, message: ActorMessage) -> None:
    """
    Reset circuit breaker for an endpoint.
    
    Content: {
        "endpoint": Optional[str]  # None = reset all
    }
    """
```

### 4.7 Helper Methods

```python
def _add_auth_headers(self, connection: ExternalConnection, 
                     headers: dict[str, str]) -> dict[str, str]:
    """Add authentication headers based on connection auth config."""
    if connection.auth_type == "bearer" and connection.auth_config.get("token"):
        headers["Authorization"] = f"Bearer {connection.auth_config['token']}"
    elif connection.auth_type == "basic":
        import base64
        creds = f"{connection.auth_config.get('username', '')}:{connection.auth_config.get('password', '')}"
        headers["Authorization"] = f"Basic {base64.b64encode(creds.encode()).decode()}"
    elif connection.auth_type == "api_key":
        headers[connection.auth_config.get("header", "X-API-Key")] = (
            connection.auth_config.get("key", "")
        )
    return headers

def _record_api_metrics(
    self,
    request_id: str,
    connection_id: str,
    method: str,
    latency_ms: int,
    success: bool,
    status_code: int,
    error: str | None,
) -> None:
    """Record API request metrics."""
    metric = APIRequestMetrics(
        request_id=request_id,
        latency_ms=latency_ms,
        status_code=status_code,
        error=error,
    )
    self._api_metrics.append(metric)
    
    # Trim if needed
    if len(self._api_metrics) > self._max_metrics_entries:
        self._api_metrics = self._api_metrics[-self._max_metrics_entries:]
```

---

## 5. Edge Case Handling

### 5.1 API Rate Limit Violations

**Detection Flow**:
```
HTTP Response (429)
    ↓
RateLimitHandler.record_response()
    ↓
Extract Retry-After header (if present)
    ↓
Update rate limit state
    ↓
Calculate backoff delay
    ↓
If auto_backoff enabled:
    - Wait for backoff duration
    - Increment retry counter
    - Retry request
    ↓
Log rate limit event
    ↓
Update connection status to RATE_LIMITED
```

**Backoff Calculation**:
```python
# Exponential backoff with jitter
base_delay = initial_delay_ms * (backoff_multiplier ^ retry_count)
jitter = random.uniform(-jitter_factor, jitter_factor) * base_delay
delay = min(base_delay + jitter, max_delay_ms)

# If Retry-After header present, use max of calculated and specified
if retry_after_ms:
    delay = max(delay, retry_after_ms)
```

**Logging**:
```python
logger.warning(
    "api_rate_limited",
    endpoint=url,
    retry_after=retry_after,
    backoff_ms=backoff,
    retry_count=retry_count,
    connection_id=connection_id,
)
```

### 5.2 API Provider Failure (Circuit Breaker)

**Detection Flow**:
```
HTTP Response (5xx or network error)
    ↓
CircuitBreaker.record_failure()
    ↓
Increment failure count
    ↓
Check threshold exceeded?
    ↓ (yes)
Set state = OPEN
    ↓
Reject subsequent requests immediately
    ↓
Wait timeout_seconds
    ↓
Set state = HALF_OPEN (allow test request)
    ↓
Success in HALF_OPEN?
    ↓ (yes, success_threshold times)
Set state = CLOSED
    ↓ (no, failure)
Set state = OPEN (back to step 6)
```

**Half-Open Testing**:
```python
# When circuit is HALF_OPEN, allow one request through
# If it succeeds: record success, close circuit if threshold reached
# If it fails: immediately open circuit again
```

**Excluded Status Codes**:
```python
# 400, 401, 403, 404 are NOT circuit breaker failures
# These are client issues that won't be fixed by retry
# They don't count toward failure threshold
```

### 5.3 Fallback Mechanisms

**Fallback Selection**:
```
Primary Endpoint: https://api.primary.com
    ↓ (failure)
Fallback 1: https://api.backup1.com
    ↓ (failure)
Fallback 2: https://api.backup2.com
    ↓ (all failed)
Return error (with all failure info)
```

**Health Monitoring**:
```python
# FallbackManager periodically checks health of endpoints
# Endpoints marked unhealthy after consecutive failures
# Endpoints marked healthy after successful requests
# Primary is preferred if healthy, even if fallbacks exist
```

### 5.4 Graceful Degradation

**Combined Resilience**:
```
Request
    ↓
Check Circuit Breaker (OPEN? → reject immediately)
    ↓ (closed/half-open)
Check Rate Limit (limited? → wait with backoff)
    ↓
Execute Request
    ↓
Success? → Record success, return response
    ↓ (failure)
Check if retryable (5xx, network? → retry with backoff)
    ↓
Check if fallback available → try fallback
    ↓
All retries exhausted → return error with context
```

---

## 6. Integration Points

### 6.1 With NATS Event Mesh (Phase 1)

- Nexus publishes resilience events for monitoring
- Circuit breaker state changes broadcast to Sentinel
- Rate limit events logged for pattern analysis

### 6.2 With ZERO-01 (Zero-Trust)

- All requests pass through `_sanitize_input()` before execution
- All responses validated before processing
- Request/response logging for audit trail

### 6.3 With Sentinel/Sentinel-Prime

- Circuit breaker OPEN events sent to Sentinel for threat analysis
- Rate limit patterns analyzed for DoS detection
- Fallback activation logged for anomaly detection

### 6.4 With HealthReportingMixin

- Resilience metrics included in health reports:
  - Circuit breaker states per endpoint
  - Rate limiter metrics
  - Fallback health status
  - Retry counts and latencies

---

## 7. Verification Criteria

| Criterion | Measurement | Pass Threshold |
|-----------|-------------|----------------|
| Automatic retry | Retry attempts on 429/5xx | 100% of retryable failures retried |
| Backoff calculation | Delay increases correctly | Exponential/linear as configured |
| Rate limit detection | 429 responses detected | 100% detected and handled |
| Circuit breaker | Circuit opens after threshold | Opens at configured failure count |
| Circuit recovery | Half-open testing works | Recovery after timeout |
| Fallback activation | Fallbacks used on primary failure | Fallbacks tried in order |
| Graceful degradation | Error returned after all retries | Error with full context |
| Zero-trust maintained | All inputs sanitized | ZERO-01 validation passes |
| Metrics recorded | All events logged | Metrics available via handler |

---

## 8. Implementation Order

### Phase 1: Core Data Structures (Day 1)

1. Create `src/heretek_swarm/gateway/external_api.py`
   - `RetryConfig`, `RateLimitConfig`, `CircuitBreakerConfig`, `FallbackConfig` dataclasses
   - `APIRequestMetrics` dataclass
   - `RetryStrategy` and `CircuitState` enums

### Phase 2: Rate Limit Handler (Day 1-2)

2. Implement `RateLimitHandler` class
   - `check_rate_limit()`, `record_response()`, `get_backoff_delay()`
   - Rate limit tracking per endpoint
   - Automatic backoff calculation

### Phase 3: Circuit Breaker (Day 2)

3. Implement `CircuitBreaker` class
   - State machine: CLOSED → OPEN → HALF_OPEN → CLOSED
   - `can_execute()`, `record_success()`, `record_failure()`
   - Configurable thresholds and timeouts

### Phase 4: Fallback Manager (Day 2-3)

4. Implement `FallbackManager` class
   - Endpoint health tracking
   - `get_available_endpoint()` with priority selection
   - `record_failure()`, `record_success()`

### Phase 5: Resilient API Client (Day 3-4)

5. Implement `ResilientAPIClient` class
   - Full retry loop with backoff
   - Integration of rate limiter, circuit breaker, fallback
   - `request()`, `get()`, `post()`, `put()`, `delete()` methods
   - Comprehensive metrics

### Phase 6: Nexus Integration (Day 5-6)

6. Enhance `src/heretek_swarm/actors/nexus.py`
   - Import external_api components
   - Initialize ResilientAPIClient
   - Enhance `_handle_execute_request` with resilience
   - Add new message handlers for metrics and configuration

### Phase 7: Testing & Verification (Day 7)

7. Create tests:
   - `tests/gateway/test_external_api.py` (~200 lines)
   - `tests/gateway/test_rate_limit_handler.py` (~100 lines)
   - `tests/gateway/test_circuit_breaker.py` (~100 lines)

8. Verify:
   - Rate limit detection and backoff works
   - Circuit breaker opens/closes correctly
   - Fallbacks activate on primary failure
   - Zero-trust validation maintained

---

## 9. File Summary

| File | Action | Lines Added |
|------|--------|-------------|
| `src/heretek_swarm/gateway/external_api.py` | CREATE | ~650 |
| `src/heretek_swarm/actors/nexus.py` | ENHANCE | ~200 |
| `tests/gateway/test_external_api.py` | CREATE | ~200 |
| `tests/gateway/test_rate_limit_handler.py` | CREATE | ~100 |
| `tests/gateway/test_circuit_breaker.py` | CREATE | ~100 |

**Total New Code**: ~850 lines
**Total Test Code**: ~400 lines

---

## 10. Dependencies

```
Phase 1 (ZERO-01) ────────────────────────────────────┐
                                                       │
Phase 1 (NATS Event Mesh) ─────────────────────────────┼──► INTG-02
                                                       │
Phase 1 (HealthReportingMixin) ────────────────────────┘
```

**Phase 1 dependencies**:
- ZERO-01 hostile input treatment (reused, not replicated)
- NATS for event publishing
- HealthReportingMixin for health reports
- ValidationMixin for message validation

---

## 11. Open Questions (for resolution during implementation)

1. **Default retry count**: 3 retries — appropriate for most APIs? Should this be configurable per connection?

2. **Circuit breaker scope**: Per-endpoint vs per-connection. Currently per-endpoint allows finer-grained failure isolation.

3. **Fallback health checks**: Should we actively probe fallback endpoints or just use them on primary failure?

4. **Rate limit header parsing**: Different providers use different headers (Retry-After, X-RateLimit-*, etc.). Should we support provider-specific parsing?

5. **Metrics retention**: 1000 entries in memory — should we persist to PostgreSQL for analysis?

6. **Connection timeout vs request timeout**: Currently combined. Should we separate for better control?

---

## 12. Monitoring and Alerting

### Health Metrics to Track

```python
{
    "api_requests_total": 1000,
    "api_errors_total": 15,
    "api_rate_limits_total": 5,
    "api_circuit_breaks_total": 2,
    "api_fallbacks_total": 3,
    "api_avg_latency_ms": 150,
    "circuit_breaker_states": {
        "https://api.example.com": "closed",
        "https://api.backup.com": "half_open",
    },
    "rate_limiter_status": {
        "requests_per_minute": 60,
        "current_rate": 45,
    },
}
```

### Alerting Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| circuit_breaker_opens | > 2 in 5min | > 5 in 5min |
| rate_limits_total | > 10 in 5min | > 20 in 5min |
| fallback_activations | > 5 in 5min | > 10 in 5min |
| avg_latency_ms | > 500ms | > 1000ms |
| error_rate | > 5% | > 10% |

---

## 13. Future Enhancements (Out of Scope for INTG-02)

- Request batching for rate limit optimization
- Response caching for idempotent GETs
- WebSocket support with automatic reconnection
- gRPC protocol translation
- Distributed rate limiting across agents
- ML-based anomaly detection for API failures
