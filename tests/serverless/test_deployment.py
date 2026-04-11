"""
Deployment Tests for Serverless Configuration.

Tests for:
- Serverless configuration validation
- Lambda handler functionality
- Cold start optimization
- IAM permissions
- Resource creation

Note: These tests validate the serverless configuration and handlers.
Full deployment testing requires AWS credentials and should be run
in a staging environment.
"""

import json
import os

# Test imports from handler module
import sys
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, 'serverless')


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def lambda_context():
    """Create mock Lambda context."""
    _context = Mock()
    context.aws_request_id = "test-request-id-123"
    context.function_name = "test-function"
    context.memory_limit_in_mb = 128
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test"
    context.log_stream_name = "test-log-stream"
    return context


@pytest.fixture
def api_gateway_event():
    """Create mock API Gateway event."""
    return {
        "httpMethod": "GET",
        "path": "/health",
        "headers": {
            "Content-Type": "application/json",
            "X-Heretek-Api-Key": "test-api-key",
        },
        "body": None,
        "isBase64Encoded": False,
        "pathParameters": None,
        "queryStringParameters": None,
        "requestContext": {
            "accountId": "123456789012",
            "apiId": "test-api",
            "protocol": "HTTP/1.1",
            "httpMethod": "GET",
            "path": "/health",
            "stage": "dev",
            "requestId": "test-request-id",
            "requestTime": "07/Apr/2026:18:00:00 +0000",
            "requestTimeEpoch": 1712512800000,
            "identity": {},
            "resourceId": "test-resource",
            "resourcePath": "/{proxy+}",
            "domainName": "test.execute-api.us-east-1.amazonaws.com",
        },
    }


@pytest.fixture
def sqs_event():
    """Create mock SQS event."""
    return {
        "Records": [
            {
                "messageId": "msg-1",
                "receiptHandle": "receipt-handle-1",
                "body": json.dumps({
                    "action": "agent_deploy",
                    "agent_type": "alpha",
                    "config": {"key": "value"},
                }),
                "attributes": {
                    "ApproximateReceiveCount": "1",
                    "SentTimestamp": "1712512800000",
                    "SenderId": "123456789012",
                },
                "messageAttributes": {},
                "md5OfBody": "md5-hash",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:test-queue",
                "awsRegion": "us-east-1",
            },
        ],
    }


@pytest.fixture
def eventbridge_event():
    """Create mock EventBridge event."""
    return {
        "version": "0",
        "id": "event-id-123",
        "detail-type": "Scheduled Task",
        "source": "aws.events",
        "account": "123456789012",
        "time": "2026-04-07T18:00:00Z",
        "region": "us-east-1",
        "resources": ["arn:aws:events:us-east-1:123456789012:rule/test-rule"],
        "detail": {
            "action": "health_check",
        },
    }


@pytest.fixture
def mock_env_vars():
    """Mock environment variables."""
    _env_vars = {
        "STAGE": "dev",
        "REGION": "us-east-1",
        "SERVICE_NAME": "heretek-swarm",
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
        "REDIS_URL": "redis://localhost:6379",
        "QDRANT_HOST": "localhost",
        "QDRANT_PORT": "6333",
        "NATS_SERVERS": "nats://localhost:4222",
        "API_KEY": "test-api-key",
        "SECRET_KEY": "test-secret-key",
        "OPENAI_API_KEY": "sk-test-key",
        "LOG_LEVEL": "INFO",
        "ENABLE_TRACING": "true",
        "ENABLE_METRICS": "true",
        "RAG_ENABLED": "true",
    }

    with patch.dict(os.environ, env_vars):
        yield


# =============================================================================
# Serverless Configuration Tests
# =============================================================================

class TestServerlessConfiguration:
    """Tests for serverless.yml configuration."""

    def test_serverless_file_exists(self):
        """Test that serverless.yml exists."""
        import os
        assert os.path.exists("serverless/serverless.yml")

    def test_serverless_yaml_valid(self):
        """Test that serverless.yml is valid YAML."""
        import yaml

        with open("serverless/serverless.yml", "r") as f:
            _config = yaml.safe_load(f)

        assert config is not None
        assert "service" in config
        assert "provider" in config
        assert "functions" in config
        assert "resources" in config

    def test_service_name(self):
        """Test service name configuration."""
        import yaml

        with open("serverless/serverless.yml", "r") as f:
            _config = yaml.safe_load(f)

        assert config["service"] == "heretek-swarm"

    def test_runtime_configuration(self):
        """Test runtime configuration."""
        import yaml

        with open("serverless/serverless.yml", "r") as f:
            _config = yaml.safe_load(f)

        _provider = config["provider"]
        assert provider["runtime"] == "python3.11"
        assert provider["memorySize"] >= 256
        assert provider["timeout"] <= 900  # Max 15 minutes

    def test_functions_defined(self):
        """Test that required functions are defined."""
        import yaml

        with open("serverless/serverless.yml", "r") as f:
            _config = yaml.safe_load(f)

        _functions = config["functions"]

        _required_functions = [
            "api",
            "async_processor",
            "swarm_health_check",
            "agent_state_cleanup",
            "behavior_profile_analyzer",
        ]

        for func_name in required_functions:
            assert func_name in functions, f"Function {func_name} not defined"

    def test_dynamodb_tables_defined(self):
        """Test that DynamoDB tables are defined."""
        import yaml

        with open("serverless/serverless.yml", "r") as f:
            _config = yaml.safe_load(f)

        _resources = config["resources"]["Resources"]

        _required_tables = [
            "AgentStateTable",
            "WorkflowStateTable",
            "KnowledgeTable",
            "AgentProfilesTable",
        ]

        for table_name in required_tables:
            assert table_name in resources, f"Table {table_name} not defined"

    def test_iam_permissions(self):
        """Test IAM permissions configuration."""
        import yaml

        with open("serverless/serverless.yml", "r") as f:
            _config = yaml.safe_load(f)

        _iam_statements = config["provider"]["iam"]["role"]["statements"]

        # Check for required permissions
        _actions_covered = set()
        for statement in iam_statements:
            actions_covered.update(statement.get("Action", []))

        _required_actions = [
            "dynamodb:GetItem",
            "dynamodb:PutItem",
            "logs:CreateLogGroup",
            "logs:CreateLogStream",
            "logs:PutLogEvents",
        ]

        for action in required_actions:
            assert action in actions_covered, f"Permission {action} not granted"


# =============================================================================
# Lambda Handler Tests
# =============================================================================

class TestLambdaHandlers:
    """Tests for Lambda handler functions."""

    @pytest.mark.asyncio
    async def test_health_check(self, _lambda_context, _mock_env_vars):
        """Test health check endpoint."""
        from serverless.handler import health_check

        _event = {"path": "/health"}
        _response = health_check(event, lambda_context)

        assert response["statusCode"] == 200
        _body = json.loads(response["body"])
        assert body["status"] == "healthy"
        assert "timestamp" in body

    @pytest.mark.asyncio
    async def test_readiness_check(self, _lambda_context, _mock_env_vars):
        """Test readiness check endpoint."""
        from serverless.handler import readiness_check

        _event = {"path": "/ready"}
        _response = readiness_check(event, lambda_context)

        assert response["statusCode"] in [200, 503]
        _body = json.loads(response["body"])
        assert "status" in body
        assert "checks" in body

    @pytest.mark.asyncio
    async def test_api_handler_health(self, _lambda_context, _mock_env_vars):
        """Test API handler with health check."""
        from serverless.handler import api_handler

        _event = {
            "httpMethod": "GET",
            "path": "/health",
            "headers": {},
        }

        _response = api_handler(event, lambda_context)

        assert response["statusCode"] == 200
        _body = json.loads(response["body"])
        assert body["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_api_handler_not_found(self, _lambda_context, _mock_env_vars):
        """Test API handler with unknown path."""
        from serverless.handler import api_handler

        _event = {
            "httpMethod": "GET",
            "path": "/unknown/path",
            "headers": {},
        }

        _response = api_handler(event, lambda_context)

        assert response["statusCode"] == 404
        _body = json.loads(response["body"])
        assert "error" in body

    @pytest.mark.asyncio
    async def test_async_processor(self, _lambda_context, _sqs_event, _mock_env_vars):
        """Test async processor handler."""
        from serverless.handler import async_processor

        _response = async_processor(sqs_event, lambda_context)

        assert response["statusCode"] in [200, 207]
        _body = json.loads(response["body"])
        assert "processed" in body
        assert "failed" in body

    @pytest.mark.asyncio
    async def test_swarm_health_check(self, _lambda_context, _eventbridge_event, _mock_env_vars):
        """Test scheduled swarm health check."""
        from serverless.handler import swarm_health_check

        _response = swarm_health_check(eventbridge_event, lambda_context)

        assert response["statusCode"] == 200
        _body = json.loads(response["body"])
        assert "timestamp" in body
        assert "agents_checked" in body

    @pytest.mark.asyncio
    async def test_agent_state_cleanup(self, _lambda_context, _eventbridge_event, _mock_env_vars):
        """Test agent state cleanup handler."""
        from serverless.handler import agent_state_cleanup

        _event = eventbridge_event.copy()
        event["detail"] = {"action": "cleanup_states"}

        _response = agent_state_cleanup(event, lambda_context)

        assert response["statusCode"] == 200
        _body = json.loads(response["body"])
        assert "timestamp" in body
        assert "states_scanned" in body

    @pytest.mark.asyncio
    async def test_behavior_profile_analyzer(self, _lambda_context, _eventbridge_event, _mock_env_vars):
        """Test behavior profile analyzer handler."""
        from serverless.handler import behavior_profile_analyzer

        _event = eventbridge_event.copy()
        event["detail"] = {"action": "analyze_profiles"}

        _response = behavior_profile_analyzer(event, lambda_context)

        assert response["statusCode"] == 200
        _body = json.loads(response["body"])
        assert "timestamp" in body
        assert "profiles_analyzed" in body


# =============================================================================
# Cold Start Optimization Tests
# =============================================================================

class TestColdStartOptimization:
    """Tests for cold start optimization."""

    def test_dependency_initialization(self, _mock_env_vars):
        """Test dependency initialization."""
        from serverless.handler import initialize_dependencies

        # Should not raise exception
        initialize_dependencies()

    def test_global_variables(self, _mock_env_vars):
        """Test global variable initialization."""
        from serverless.handler import (
            _db_connection,
            _redis_connection,
        )

        # Global variables should be initialized
        # (may be None if not configured)
        assert _db_connection is None or hasattr(_db_connection, 'execute')
        assert _redis_connection is None or hasattr(_redis_connection, 'get')


# =============================================================================
# Authentication Tests
# =============================================================================

class TestAuthentication:
    """Tests for authentication."""

    def test_verify_auth_valid(self, _mock_env_vars):
        """Test verifying valid API key."""
        from serverless.handler import verify_auth

        _event = {
            "headers": {
                "X-Heretek-Api-Key": "test-api-key",
            },
        }

        _result = verify_auth(event)
        assert result is True

    def test_verify_auth_missing(self, _mock_env_vars):
        """Test verifying missing API key."""
        from serverless.handler import verify_auth

        _event = {
            "headers": {},
        }

        _result = verify_auth(event)
        assert result is False

    def test_verify_auth_invalid(self, _mock_env_vars):
        """Test verifying invalid API key."""
        from serverless.handler import verify_auth

        _event = {
            "headers": {
                "X-Heretek-Api-Key": "wrong-key",
            },
        }

        _result = verify_auth(event)
        assert result is False


# =============================================================================
# Request Parsing Tests
# =============================================================================

class TestRequestParsing:
    """Tests for request parsing."""

    def test_parse_body_json(self):
        """Test parsing JSON body."""
        from serverless.handler import parse_body

        _event = {
            "body": json.dumps({"key": "value"}),
            "isBase64Encoded": False,
        }

        _body = parse_body(event)
        assert body == {"key": "value"}

    def test_parse_body_empty(self):
        """Test parsing empty body."""
        from serverless.handler import parse_body

        _event = {
            "body": None,
        }

        _body = parse_body(event)
        assert body == {}

    def test_parse_body_base64(self):
        """Test parsing base64 encoded body."""
        import base64

        from serverless.handler import parse_body

        _original_body = json.dumps({"key": "value"})
        _encoded_body = base64.b64encode(original_body.encode()).decode()

        _event = {
            "body": encoded_body,
            "isBase64Encoded": True,
        }

        _body = parse_body(event)
        assert body == {"key": "value"}

    def test_parse_body_invalid_json(self):
        """Test parsing invalid JSON body."""
        from serverless.handler import parse_body

        _event = {
            "body": "not valid json",
            "isBase64Encoded": False,
        }

        _body = parse_body(event)
        assert body == {}


# =============================================================================
# API Response Tests
# =============================================================================

class TestAPIResponse:
    """Tests for API response formatting."""

    def test_api_response_default_headers(self):
        """Test API response with default headers."""
        from serverless.handler import APIResponse

        _response = APIResponse(
            _status_code = 200,
            _body = {"message": "success"},
        )

        _result = response.to_dict()

        assert result["statusCode"] == 200
        assert "Content-Type" in result["headers"]
        assert "Access-Control-Allow-Origin" in result["headers"]

    def test_api_response_custom_headers(self):
        """Test API response with custom headers."""
        from serverless.handler import APIResponse

        _response = APIResponse(
            _status_code = 200,
            _body = {"message": "success"},
            _headers = {"X-Custom-Header": "custom-value"},
        )

        _result = response.to_dict()

        assert result["headers"]["X-Custom-Header"] == "custom-value"

    def test_api_response_json_serialization(self):
        """Test API response JSON serialization."""
        from datetime import datetime

        from serverless.handler import APIResponse

        _response = APIResponse(
            _status_code = 200,
            _body = {
                "message": "success",
                "timestamp": datetime.now(),
            },
        )

        _result = response.to_dict()

        # Should not raise exception
        json.loads(result["body"])


# =============================================================================
# Resource Tests
# =============================================================================

class TestResourceCreation:
    """Tests for AWS resource creation."""

    def test_dynamodb_table_properties(self):
        """Test DynamoDB table properties."""
        import yaml

        with open("serverless/serverless.yml", "r") as f:
            _config = yaml.safe_load(f)

        _tables = config["resources"]["Resources"]

        _agent_table = tables["AgentStateTable"]
        assert agent_table["Type"] == "AWS::DynamoDB::Table"
        assert "KeySchema" in agent_table["Properties"]
        assert "AttributeDefinitions" in agent_table["Properties"]

    def test_sqs_queue_properties(self):
        """Test SQS queue properties."""
        import yaml

        with open("serverless/serverless.yml", "r") as f:
            _config = yaml.safe_load(f)

        _queues = config["resources"]["Resources"]

        _async_queue = queues["AsyncProcessingQueue"]
        assert async_queue["Type"] == "AWS::SQS::Queue"
        assert "VisibilityTimeout" in async_queue["Properties"]

    def test_s3_bucket_properties(self):
        """Test S3 bucket properties."""
        import yaml

        with open("serverless/serverless.yml", "r") as f:
            _config = yaml.safe_load(f)

        _buckets = config["resources"]["Resources"]

        _docs_bucket = buckets["DocumentsBucket"]
        assert docs_bucket["Type"] == "AWS::S3::Bucket"
        assert "BucketEncryption" in docs_bucket["Properties"]
        assert "VersioningConfiguration" in docs_bucket["Properties"]

    def test_eventbridge_bus_properties(self):
        """Test EventBridge bus properties."""
        import yaml

        with open("serverless/serverless.yml", "r") as f:
            _config = yaml.safe_load(f)

        _buses = config["resources"]["Resources"]

        _events_bus = buses["SwarmEventsBus"]
        assert events_bus["Type"] == "AWS::Events::EventBus"


# =============================================================================
# Outputs Tests
# =============================================================================

class TestOutputs:
    """Tests for CloudFormation outputs."""

    def test_outputs_defined(self):
        """Test that outputs are defined."""
        import yaml

        with open("serverless/serverless.yml", "r") as f:
            _config = yaml.safe_load(f)

        _outputs = config["outputs"]

        _required_outputs = [
            "ApiGatewayApiUrl",
            "AgentStateTableName",
            "WorkflowStateTableName",
            "KnowledgeTableName",
            "EventsBusName",
            "AsyncQueueUrl",
            "DocumentsBucketName",
        ]

        for output_name in required_outputs:
            assert output_name in outputs, f"Output {output_name} not defined"


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for serverless deployment."""

    def test_full_api_request_flow(self, _lambda_context, _mock_env_vars):
        """Test full API request flow."""
        from serverless.handler import api_handler

        # Health check request
        _health_event = {
            "httpMethod": "GET",
            "path": "/health",
            "headers": {},
        }

        _health_response = api_handler(health_event, lambda_context)

        assert health_response["statusCode"] == 200

        # Ready check request
        _ready_event = {
            "httpMethod": "GET",
            "path": "/ready",
            "headers": {},
        }

        _ready_response = api_handler(ready_event, lambda_context)

        assert ready_response["statusCode"] in [200, 503]

    def test_error_handling(self, _lambda_context, _mock_env_vars):
        """Test error handling in handlers."""
        from serverless.handler import api_handler

        # Request that should cause 404
        _error_event = {
            "httpMethod": "GET",
            "path": "/nonexistent",
            "headers": {},
        }

        _response = api_handler(error_event, lambda_context)

        assert response["statusCode"] == 404
        _body = json.loads(response["body"])
        assert "error" in body
