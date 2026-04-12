"""
Heretek Swarm Serverless Handler for AWS Lambda.

This module provides Lambda function handlers for the Heretek Swarm system:
- API Gateway integration for REST endpoints
- SQS event processing for async tasks
- EventBridge scheduled tasks
- Cold start optimization

Usage:
    # Deploy with Serverless Framework
    serverless deploy
    
    # Test locally
    serverless offline
"""

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict

import structlog

# Configure logging for Lambda
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Initialize structlog for Lambda
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

log = structlog.get_logger()

# Global variables for connection reuse (cold start optimization)
_db_connection = None
_redis_connection = None
_rag_pipeline = None
_profiler = None


# =============================================================================
# Cold Start Optimization
# =============================================================================

def initialize_dependencies() -> None:
    """
    Initialize expensive dependencies during cold start.
    
    This function is called once per container initialization
    to reuse connections across multiple invocations.
    """
    global _db_connection, _redis_connection, _rag_pipeline, _profiler

    log.info("initializing_dependencies")

    try:
        # Database connection would be initialized here
        # _db_connection = create_db_connection()

        # Redis connection
        # _redis_connection = create_redis_connection()

        # RAG pipeline (lazy initialization)
        # _rag_pipeline = None  # Initialize on first use

        # Behavior profiler
        # _profiler = None  # Initialize on first use

        log.info("dependencies_initialized")
    except Exception as e:
        log.error("dependency_initialization_failed", error=str(e))
        raise


# Run initialization on module load (cold start)
initialize_dependencies()


# =============================================================================
# API Gateway Handler
# =============================================================================

@dataclass
class APIResponse:
    """Standardized API Gateway response."""
    status_code: int
    body: Dict[str, Any]
    headers: Dict[str, str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API Gateway response format."""
        return {
            "statusCode": self.status_code,
            "body": json.dumps(self.body, default=str),
            "headers": self.headers or {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true",
            },
        }


def api_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main API Gateway handler for Heretek Swarm.
    
    Routes requests to appropriate handlers based on path and method.
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    request_id = context.aws_request_id
    start_time = time.time()

    log.info(
        "api_request_received",
        request_id=request_id,
        path=event.get("path"),
        method=event.get("httpMethod"),
    )

    try:
        # Parse path
        path = event.get("path", "/")
        method = event.get("httpMethod", "GET")

        # Health check endpoints
        if path == "/health" or path == "/{proxy+}" and method == "GET" and event.get("pathParameters", {}).get("proxy") == "health":
            return health_check(event, context)

        if path == "/ready" or path == "/{proxy+}" and method == "GET" and event.get("pathParameters", {}).get("proxy") == "ready":
            return readiness_check(event, context)

        # Route to appropriate handler
        if path.startswith("/api/agents"):
            return handle_agents_api(event, context)
        elif path.startswith("/api/rag"):
            return handle_rag_api(event, context)
        elif path.startswith("/api/workflows"):
            return handle_workflows_api(event, context)
        elif path.startswith("/api/consensus"):
            return handle_consensus_api(event, context)
        elif path.startswith("/api/observability"):
            return handle_observability_api(event, context)
        elif path.startswith("/api/config"):
            return handle_config_api(event, context)
        else:
            return APIResponse(
                status_code=404,
                body={"error": "Not found", "path": path},
            ).to_dict()

    except Exception as e:
        log.exception(
            "api_request_error",
            request_id=request_id,
            error=str(e),
        )
        return APIResponse(
            status_code=500,
            body={"error": "Internal server error", "request_id": request_id},
        ).to_dict()

    finally:
        duration_ms = (time.time() - start_time) * 1000
        log.info(
            "api_request_completed",
            request_id=request_id,
            duration_ms=duration_ms,
        )


def health_check(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns basic health status.
    """
    return APIResponse(
        status_code=200,
        body={
            "status": "healthy",
            "service": "heretek-swarm",
            "stage": os.environ.get("STAGE", "unknown"),
            "region": os.environ.get("REGION", "unknown"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    ).to_dict()


def readiness_check(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Readiness check endpoint.
    
    Verifies all dependencies are available.
    """
    checks = {
        "lambda": True,
        "environment": True,
        "dependencies": True,
    }

    # Check environment variables
    required_env = ["DATABASE_URL", "REDIS_URL", "API_KEY"]
    for env_var in required_env:
        if not os.environ.get(env_var):
            checks["environment"] = False
            break

    # Check dependencies (would verify actual connections)
    # if not _db_connection or not _redis_connection:
    #     checks["dependencies"] = False

    all_healthy = all(checks.values())

    return APIResponse(
        status_code=200 if all_healthy else 503,
        body={
            "status": "ready" if all_healthy else "not_ready",
            "checks": checks,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    ).to_dict()


# =============================================================================
# API Route Handlers
# =============================================================================

def handle_agents_api(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle /api/agents routes."""
    path = event.get("path", "")
    method = event.get("httpMethod", "GET")

    # Extract path parameters
    path_params = event.get("pathParameters", {})
    _instance_id = path_params.get("proxy", "").split("/")[-1] if path_params else None

    # Simple routing based on path
    if "/profiling" in path:
        return handle_profiling_api(event, context)

    # Default agents API response
    return APIResponse(
        status_code=200,
        body={
            "message": "Agents API",
            "path": path,
            "method": method,
            "note": "Full agents API requires Lambda function URL or API Gateway integration with FastAPI",
        },
    ).to_dict()


def handle_profiling_api(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle behavior profiling API endpoints."""
    path = event.get("path", "")
    method = event.get("httpMethod", "GET")

    # Get profiler
    profiler = get_profiler()
    if not profiler:
        return APIResponse(
            status_code=503,
            body={"error": "Behavior profiling not available"},
        ).to_dict()

    # Extract instance ID from path
    parts = path.split("/")
    instance_id = None
    for i, part in enumerate(parts):
        if part == "profiling" and i > 0:
            instance_id = parts[i - 1]
            break

    # Handle different endpoints
    if method == "GET":
        if "/metrics" in path and instance_id:
            metrics = profiler.compute_metrics(instance_id)
            return APIResponse(
                status_code=200,
                body=metrics.to_dict() if metrics else {},
            ).to_dict()

        elif "/profile" in path and instance_id:
            agent_type = instance_id.split("-")[0] if instance_id else "unknown"
            profile = profiler.get_profile(agent_type)
            return APIResponse(
                status_code=200,
                body=profile.to_dict() if profile else {},
            ).to_dict()

        elif "/anomalies" in path and instance_id:
            anomalies = profiler.detect_anomalies(instance_id)
            return APIResponse(
                status_code=200,
                body=[a.to_dict() for a in anomalies],
            ).to_dict()

        elif "/alerts" in path:
            alerts = profiler.get_alerts()
            return APIResponse(
                status_code=200,
                body=[a.to_dict() for a in alerts],
            ).to_dict()

        elif "/stats" in path:
            stats = profiler.get_stats()
            return APIResponse(
                status_code=200,
                body=stats,
            ).to_dict()

        elif "/prometheus" in path:
            metrics = profiler.export_prometheus_metrics()
            return {
                "statusCode": 200,
                "body": metrics,
                "headers": {"Content-Type": "text/plain"},
            }

    return APIResponse(
        status_code=404,
        body={"error": "Profiling endpoint not found"},
    ).to_dict()


def handle_rag_api(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle /api/rag routes."""
    return APIResponse(
        status_code=200,
        body={
            "message": "RAG API",
            "note": "Full RAG API requires Lambda function URL or API Gateway integration with FastAPI",
        },
    ).to_dict()


def handle_workflows_api(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle /api/workflows routes."""
    return APIResponse(
        status_code=200,
        body={
            "message": "Workflows API",
            "note": "Full workflows API requires Lambda function URL or API Gateway integration with FastAPI",
        },
    ).to_dict()


def handle_consensus_api(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle /api/consensus routes."""
    return APIResponse(
        status_code=200,
        body={
            "message": "Consensus API",
            "note": "Full consensus API requires Lambda function URL or API Gateway integration with FastAPI",
        },
    ).to_dict()


def handle_observability_api(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle /api/observability routes."""
    return APIResponse(
        status_code=200,
        body={
            "message": "Observability API",
            "note": "Full observability API requires Lambda function URL or API Gateway integration with FastAPI",
        },
    ).to_dict()


def handle_config_api(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle /api/config routes."""
    return APIResponse(
        status_code=200,
        body={
            "message": "Config API",
            "note": "Full config API requires Lambda function URL or API Gateway integration with FastAPI",
        },
    ).to_dict()


# =============================================================================
# SQS Event Handler
# =============================================================================

def async_processor(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Process async tasks from SQS queue.
    
    Args:
        event: SQS event with records
        context: Lambda context
        
    Returns:
        Processing result
    """
    request_id = context.aws_request_id
    log.info("async_processor_invoked", request_id=request_id, record_count=len(event.get("Records", [])))

    results = {
        "processed": 0,
        "failed": 0,
        "errors": [],
    }

    for record in event.get("Records", []):
        try:
            message_body = json.loads(record.get("body", "{}"))
            action = message_body.get("action")

            log.info("processing_message", message_id=record.get("messageId"), action=action)

            # Process based on action type
            if action == "agent_deploy":
                process_agent_deploy(message_body)
            elif action == "rag_ingest":
                process_rag_ingest(message_body)
            elif action == "workflow_execute":
                process_workflow_execute(message_body)
            elif action == "consensus_vote":
                process_consensus_vote(message_body)
            else:
                log.warning("unknown_action", action=action)
                results["failed"] += 1
                results["errors"].append(f"Unknown action: {action}")
                continue

            results["processed"] += 1

        except Exception as e:
            log.exception("message_processing_failed", error=str(e))
            results["failed"] += 1
            results["errors"].append(str(e))

    log.info("async_processor_completed", **results)

    return {
        "statusCode": 200 if results["failed"] == 0 else 207,
        "body": json.dumps(results),
    }


def process_agent_deploy(message_body: Dict[str, Any]) -> None:
    """Process agent deployment task."""
    agent_type = message_body.get("agent_type")
    _config = message_body.get("config", {})

    log.info("deploying_agent", agent_type=agent_type)
    # Implementation would deploy agent using runtime registry


def process_rag_ingest(message_body: Dict[str, Any]) -> None:
    """Process RAG document ingestion task."""
    document_id = message_body.get("document_id")
    source = message_body.get("source")

    log.info("ingesting_document", document_id=document_id, source=source)
    # Implementation would ingest document into RAG system


def process_workflow_execute(message_body: Dict[str, Any]) -> None:
    """Process workflow execution task."""
    workflow_id = message_body.get("workflow_id")
    steps = message_body.get("steps", [])

    log.info("executing_workflow", workflow_id=workflow_id, steps_count=len(steps))
    # Implementation would execute workflow steps


def process_consensus_vote(message_body: Dict[str, Any]) -> None:
    """Process consensus voting task."""
    proposal_id = message_body.get("proposal_id")
    voters = message_body.get("voters", [])

    log.info("processing_consensus_vote", proposal_id=proposal_id, voters_count=len(voters))
    # Implementation would process consensus votes


# =============================================================================
# EventBridge Scheduled Handlers
# =============================================================================

def swarm_health_check(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Scheduled health check for swarm agents.
    
    Checks all deployed agents and reports their status.
    """
    log.info("swarm_health_check_started")

    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agents_checked": 0,
        "healthy": 0,
        "unhealthy": 0,
        "details": [],
    }

    # Would query agent registry for all agents
    # and check their health status

    log.info("swarm_health_check_completed", **results)

    return {
        "statusCode": 200,
        "body": json.dumps(results),
    }


def agent_state_cleanup(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Cleanup expired agent states.
    
    Removes agent states that have exceeded their TTL.
    """
    log.info("agent_state_cleanup_started")

    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "states_scanned": 0,
        "states_deleted": 0,
    }

    # Would query DynamoDB for expired states
    # and delete them

    log.info("agent_state_cleanup_completed", **results)

    return {
        "statusCode": 200,
        "body": json.dumps(results),
    }


def rag_index_optimize(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Optimize RAG vector indexes.
    
    Performs index optimization for better query performance.
    """
    log.info("rag_index_optimize_started")

    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "indexes_optimized": 0,
        "optimization_time_ms": 0,
    }

    start_time = time.time()

    # Would optimize Qdrant vector indexes

    results["optimization_time_ms"] = (time.time() - start_time) * 1000

    log.info("rag_index_optimize_completed", **results)

    return {
        "statusCode": 200,
        "body": json.dumps(results),
    }


def behavior_profile_analyzer(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Analyze agent behavior profiles and detect anomalies.
    
    Runs periodic analysis on all agent behavior profiles.
    """
    log.info("behavior_profile_analyzer_started")

    profiler = get_profiler()

    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "profiles_analyzed": 0,
        "anomalies_detected": 0,
        "alerts_generated": 0,
    }

    if profiler:
        # Analyze all profiles
        profiles = profiler.get_all_profiles()
        results["profiles_analyzed"] = len(profiles)

        # Detect anomalies for each agent type
        for agent_type, profile in profiles.items():
            anomalies = profiler.detect_anomalies(f"{agent_type}-analysis")
            results["anomalies_detected"] += len(anomalies)

            # Count unacknowledged alerts
            alerts = profiler.get_alerts(unacknowledged_only=True)
            results["alerts_generated"] = len(alerts)

    log.info("behavior_profile_analyzer_completed", **results)

    return {
        "statusCode": 200,
        "body": json.dumps(results),
    }


# =============================================================================
# Helper Functions
# =============================================================================

def get_profiler():
    """Get or initialize behavior profiler."""
    global _profiler

    if _profiler is None:
        try:
            from heretek_swarm.actors.profiling import BehaviorProfiler, ProfilingConfig
            _profiler = BehaviorProfiler(ProfilingConfig())
            log.info("profiler_initialized")
        except ImportError as e:
            log.error("profiler_import_failed", error=str(e))
            return None

    return _profiler


def verify_auth(event: Dict[str, Any]) -> bool:
    """
    Verify API authentication.
    
    Checks for valid API key in headers.
    """
    headers = event.get("headers", {})

    # Check for API key
    api_key = headers.get("X-Heretek-Api-Key") or headers.get("x-heretek-api-key")

    if not api_key:
        return False

    # Verify against stored key
    expected_key = os.environ.get("API_KEY")
    return api_key == expected_key


def parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """Parse request body."""
    body = event.get("body")

    if not body:
        return {}

    # Handle base64 encoding (API Gateway)
    if event.get("isBase64Encoded"):
        import base64
        body = base64.b64decode(body).decode("utf-8")

    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {}


# =============================================================================
# Main Entry Point
# =============================================================================

def main(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main entry point for Lambda.
    
    Routes to appropriate handler based on event source.
    """
    # Determine event source
    if "httpMethod" in event or "requestContext" in event:
        # API Gateway
        return api_handler(event, context)
    elif "Records" in event:
        # SQS
        return async_processor(event, context)
    elif "source" in event:
        # EventBridge - route based on detail
        detail = event.get("detail", {})
        action = detail.get("action", "unknown")

        if action == "health_check":
            return swarm_health_check(event, context)
        elif action == "cleanup_states":
            return agent_state_cleanup(event, context)
        elif action == "optimize_index":
            return rag_index_optimize(event, context)
        elif action == "analyze_profiles":
            return behavior_profile_analyzer(event, context)
        else:
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "EventBridge event received", "action": action}),
            }
    else:
        # Unknown event type
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Unknown event type"}),
        }
