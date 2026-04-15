"""
Test suite for Perceiver+ Agent - Advanced Analytics & Enhanced Perception.

This module provides comprehensive tests for the Perceiver+ agent including:
- Initialization with all required dependencies
- Advanced signal extraction
- Meta-perception capabilities
- Analytics and statistical analysis
- Trend detection and forecasting
- Correlation computation
- Error handling and edge cases
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from heretek_swarm.actors.base import ActorMessage
from heretek_swarm.actors.perceiver_plus import (
    AnalyticsResult,
    AnalyticsType,
    CorrelationMatrix,
    DataModality,
    PerceiverPlusAgent,
    StatisticalTest,
    TrendAnalysis,
)


@pytest.fixture
def mock_pattern_extractor() -> MagicMock:
    extractor = MagicMock()
    extractor.analyze_message = AsyncMock(return_value=None)
    extractor.extract_patterns = AsyncMock(return_value=[])
    return extractor


@pytest.fixture
def mock_deliberation_engine() -> MagicMock:
    engine = MagicMock()
    engine.start_deliberation = MagicMock(return_value="delib-123")
    engine.submit_position = MagicMock(return_value=True)
    return engine


@pytest.fixture
def mock_access_analyzer() -> MagicMock:
    analyzer = MagicMock()
    analyzer.record_access = MagicMock(return_value=None)
    return analyzer


@pytest.fixture
def mock_zero_trust_validator() -> MagicMock:
    validator = MagicMock()
    validator.validate_input = MagicMock(return_value=True)
    validator.validate_output = MagicMock(return_value=True)
    return validator


@pytest.fixture
def perceiver_plus_agent(
    mock_pattern_extractor: MagicMock,
    mock_deliberation_engine: MagicMock,
    mock_access_analyzer: MagicMock,
    mock_zero_trust_validator: MagicMock,
) -> PerceiverPlusAgent:
    agent = PerceiverPlusAgent(
        agent_id="test-perceiver-plus",
        name="TestPerceiverPlus",
        max_analyses=100,
        confidence_threshold=0.7,
        significance_level=0.05,
    )
    agent.pattern_extractor = mock_pattern_extractor
    agent.deliberation_engine = mock_deliberation_engine
    agent.access_analyzer = mock_access_analyzer
    agent.zero_trust_validator = mock_zero_trust_validator
    return agent


class TestPerceiverPlusInitialization:
    def test_init_default(self) -> None:
        agent = PerceiverPlusAgent()
        assert agent.agent_id == "perceiver-plus"
        assert agent.max_analyses == 100
        assert agent.confidence_threshold == 0.7
        assert agent.significance_level == 0.05

    def test_init_custom_params(self) -> None:
        agent = PerceiverPlusAgent(
            agent_id="custom-perceiver",
            max_analyses=200,
            confidence_threshold=0.8,
        )
        assert agent.agent_id == "custom-perceiver"
        assert agent.max_analyses == 200

    def test_init_with_mocked_deps(
        self,
        perceiver_plus_agent: PerceiverPlusAgent,
        mock_pattern_extractor: MagicMock,
    ) -> None:
        assert perceiver_plus_agent.pattern_extractor is mock_pattern_extractor
        assert perceiver_plus_agent.analysis_results == {}


class TestDescriptiveAnalysis:
    def test_descriptive_analysis_numeric(self) -> None:
        agent = PerceiverPlusAgent()
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = agent._descriptive_analysis(data, "test-1")
        assert result.analytics_type == AnalyticsType.DESCRIPTIVE
        assert "mean" in result.metrics
        assert result.metrics["mean"] == 3.0

    def test_descriptive_analysis_stats(self) -> None:
        agent = PerceiverPlusAgent()
        data = [10, 20, 30, 40, 50]
        result = agent._descriptive_analysis(data, "test-2")
        assert result.confidence >= 0.9
        assert result.metrics["min"] == 10
        assert result.metrics["max"] == 50

    def test_descriptive_analysis_empty(self) -> None:
        agent = PerceiverPlusAgent()
        result = agent._descriptive_analysis([], "test-empty")
        assert result.confidence == 0.0


class TestStatisticalAnalysis:
    def test_statistical_analysis_numeric(self) -> None:
        agent = PerceiverPlusAgent()
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = agent._statistical_analysis(data, "stat-1")
        assert result.analytics_type == AnalyticsType.STATISTICAL
        assert "sample_size" in result.metrics
        assert result.metrics["sample_size"] == 5

    def test_statistical_analysis_confidence_interval(self) -> None:
        agent = PerceiverPlusAgent()
        data = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 6.0, 6.0, 8.0, 10.0]
        result = agent._statistical_analysis(data, "stat-2")
        assert "ci_95_lower" in result.metrics
        assert "ci_95_upper" in result.metrics
        assert result.metrics["ci_95_lower"] < result.metrics["ci_95_upper"]

    def test_statistical_analysis_insufficient_data(self) -> None:
        agent = PerceiverPlusAgent()
        result = agent._statistical_analysis([1.0], "stat-small")
        assert result.confidence == 0.0


class TestCorrelationalAnalysis:
    def test_correlation_calculation(self) -> None:
        agent = PerceiverPlusAgent()
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]
        corr = agent._calculate_correlation(x, y)
        assert abs(corr - 1.0) < 0.01

    def test_correlation_positive(self) -> None:
        agent = PerceiverPlusAgent()
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        corr = agent._calculate_correlation(x, y)
        assert corr > 0.9

    def test_correlation_negative(self) -> None:
        agent = PerceiverPlusAgent()
        x = [1, 2, 3, 4, 5]
        y = [10, 8, 6, 4, 2]
        corr = agent._calculate_correlation(x, y)
        assert corr < -0.9

    def test_correlation_insufficient_data(self) -> None:
        agent = PerceiverPlusAgent()
        corr = agent._calculate_correlation([1.0], [2.0])
        assert corr == 0.0


class TestTrendAnalysis:
    def test_trend_analysis_upward(self) -> None:
        agent = PerceiverPlusAgent()
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = agent._trend_analysis(data, "trend-1")
        assert result.analytics_type == AnalyticsType.TREND
        assert result.metrics["slope"] > 0

    def test_trend_analysis_downward(self) -> None:
        agent = PerceiverPlusAgent()
        data = [5.0, 4.0, 3.0, 2.0, 1.0]
        result = agent._trend_analysis(data, "trend-2")
        assert result.metrics["slope"] < 0

    def test_trend_analysis_r_squared(self) -> None:
        agent = PerceiverPlusAgent()
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = agent._trend_analysis(data, "trend-3")
        assert "r_squared" in result.metrics
        assert result.metrics["r_squared"] >= 0


class TestAnomalyDetection:
    def test_anomaly_detection_with_anomalies(self) -> None:
        agent = PerceiverPlusAgent()
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 100.0]
        result = agent._anomaly_analysis(data, "anomaly-1")
        assert result.analytics_type == AnalyticsType.ANOMALY
        assert result.metrics["anomalies_count"] >= 1

    def test_anomaly_detection_no_anomalies(self) -> None:
        agent = PerceiverPlusAgent()
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = agent._anomaly_analysis(data, "anomaly-2")
        assert result.metrics["anomalies_count"] == 0

    def test_anomaly_detection_insufficient_data(self) -> None:
        agent = PerceiverPlusAgent()
        result = agent._anomaly_analysis([1.0, 2.0], "anomaly-small")
        assert result.confidence == 0.0


class TestSignalProcessing:
    def test_process_signal_moving_average(self) -> None:
        agent = PerceiverPlusAgent()
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = agent._process_signal(data, "moving_average", 2)
        assert len(result) <= len(data)

    def test_process_signal_empty(self) -> None:
        agent = PerceiverPlusAgent()
        result = agent._process_signal([], "moving_average", 2)
        assert len(result) == 0


class TestFeatureExtraction:
    @pytest.mark.asyncio
    async def test_extract_features_from_data_numeric(self) -> None:
        agent = PerceiverPlusAgent()
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        features = await agent._extract_features_from_data(data)
        assert "count" in features
        assert features["count"] == 5
        assert "mean" in features


class TestForecasting:
    @pytest.mark.asyncio
    async def test_forecast_values_linear(self) -> None:
        agent = PerceiverPlusAgent()
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        forecast = await agent._forecast_values(data, 3)
        assert len(forecast) == 3
        for f in forecast:
            assert "period" in f
            assert "predicted_value" in f

    @pytest.mark.asyncio
    async def test_forecast_insufficient_data(self) -> None:
        agent = PerceiverPlusAgent()
        forecast = await agent._forecast_values([1.0], 5)
        assert len(forecast) == 1
        assert "error" in forecast[0]


class TestMessageHandling:
    @pytest.mark.asyncio
    async def test_handle_analyze_data_success(
        self,
        perceiver_plus_agent: PerceiverPlusAgent,
    ) -> None:
        message = ActorMessage(
            sender="test",
            message_type="analyze_data",
            content={
                "data": [1.0, 2.0, 3.0, 4.0, 5.0],
                "analysis_id": "analysis-1",
                "analytics_types": ["descriptive"],
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(UTC).isoformat(),
        )
        perceiver_plus_agent.send = AsyncMock(return_value="msg-123")
        await perceiver_plus_agent._handle_analyze_data(message)
        assert perceiver_plus_agent.send.called

    @pytest.mark.asyncio
    async def test_handle_detect_trends(
        self,
        perceiver_plus_agent: PerceiverPlusAgent,
    ) -> None:
        message = ActorMessage(
            sender="test",
            message_type="detect_trends",
            content={
                "data": [1.0, 2.0, 3.0, 4.0, 5.0],
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(UTC).isoformat(),
        )
        perceiver_plus_agent.send = AsyncMock(return_value="msg-123")
        await perceiver_plus_agent._handle_detect_trends(message)
        assert perceiver_plus_agent.send.called

    @pytest.mark.asyncio
    async def test_handle_compute_correlations(
        self,
        perceiver_plus_agent: PerceiverPlusAgent,
    ) -> None:
        message = ActorMessage(
            sender="test",
            message_type="compute_correlations",
            content={
                "data": {"x": [1.0, 2.0, 3.0], "y": [2.0, 4.0, 6.0]},
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(UTC).isoformat(),
        )
        perceiver_plus_agent.send = AsyncMock(return_value="msg-123")
        await perceiver_plus_agent._handle_compute_correlations(message)
        assert perceiver_plus_agent.send.called

    @pytest.mark.asyncio
    async def test_handle_extract_features(
        self,
        perceiver_plus_agent: PerceiverPlusAgent,
    ) -> None:
        message = ActorMessage(
            sender="test",
            message_type="extract_features",
            content={
                "data": [1.0, 2.0, 3.0],
                "feature_id": "feat-1",
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(UTC).isoformat(),
        )
        perceiver_plus_agent.send = AsyncMock(return_value="msg-123")
        await perceiver_plus_agent._handle_extract_features(message)
        assert perceiver_plus_agent.send.called

    @pytest.mark.asyncio
    async def test_handle_forecast_values(
        self,
        perceiver_plus_agent: PerceiverPlusAgent,
    ) -> None:
        message = ActorMessage(
            sender="test",
            message_type="forecast_values",
            content={
                "data": [1.0, 2.0, 3.0, 4.0, 5.0],
                "periods": 3,
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(UTC).isoformat(),
        )
        perceiver_plus_agent.send = AsyncMock(return_value="msg-123")
        await perceiver_plus_agent._handle_forecast_values(message)
        assert perceiver_plus_agent.send.called

    @pytest.mark.asyncio
    async def test_handle_get_analytics_summary(
        self,
        perceiver_plus_agent: PerceiverPlusAgent,
    ) -> None:
        message = ActorMessage(
            sender="test",
            message_type="get_analytics_summary",
            content={"reply_to": "reply-topic"},
            timestamp=datetime.now(UTC).isoformat(),
        )
        perceiver_plus_agent.send = AsyncMock(return_value="msg-123")
        await perceiver_plus_agent._handle_get_analytics_summary(message)
        assert perceiver_plus_agent.send.called

    @pytest.mark.asyncio
    async def test_handle_signal_processing(
        self,
        perceiver_plus_agent: PerceiverPlusAgent,
    ) -> None:
        message = ActorMessage(
            sender="test",
            message_type="signal_processing",
            content={
                "data": [1.0, 2.0, 3.0, 4.0, 5.0],
                "method": "moving_average",
                "window": 2,
                "reply_to": "reply-topic",
            },
            timestamp=datetime.now(UTC).isoformat(),
        )
        perceiver_plus_agent.send = AsyncMock(return_value="msg-123")
        await perceiver_plus_agent._handle_signal_processing(message)
        assert perceiver_plus_agent.send.called


class TestInputValidation:
    def test_validate_data_input_valid(self) -> None:
        agent = PerceiverPlusAgent()
        is_valid, error = agent._validate_data_input({"data": [1, 2, 3]})
        assert is_valid

    def test_validate_data_input_missing(self) -> None:
        agent = PerceiverPlusAgent()
        is_valid, error = agent._validate_data_input({})
        assert not is_valid

    def test_validate_data_input_invalid_type(self) -> None:
        agent = PerceiverPlusAgent()
        is_valid, error = agent._validate_data_input({"data": "not a list"})
        assert not is_valid

    def test_validate_data_input_too_large(self) -> None:
        agent = PerceiverPlusAgent()
        is_valid, error = agent._validate_data_input({"data": list(range(100001))})
        assert not is_valid


class TestProcessMessage:
    @pytest.mark.asyncio
    async def test_process_unknown_type(self, perceiver_plus_agent: PerceiverPlusAgent) -> None:
        message = ActorMessage(
            sender="test",
            message_type="unknown_type",
            content={},
            timestamp=datetime.now(UTC).isoformat(),
        )
        await perceiver_plus_agent.process_message(message)

    @pytest.mark.asyncio
    async def test_process_handler_error(
        self,
        perceiver_plus_agent: PerceiverPlusAgent,
    ) -> None:
        async def failing_handler(msg: ActorMessage) -> None:
            raise ValueError("Test error")

        perceiver_plus_agent.register_handler("failing", failing_handler)
        message = ActorMessage(
            sender="test",
            message_type="failing",
            content={"reply_to": "reply"},
            timestamp=datetime.now(UTC).isoformat(),
        )
        perceiver_plus_agent.send = AsyncMock(return_value="msg-123")
        await perceiver_plus_agent.process_message(message)
        assert perceiver_plus_agent.error_count >= 1


class TestInitialization:
    @pytest.mark.asyncio
    async def test_initialize_registers_handlers(
        self,
        perceiver_plus_agent: PerceiverPlusAgent,
    ) -> None:
        await perceiver_plus_agent.initialize()
        assert "analyze_data" in perceiver_plus_agent._message_handlers
        assert "detect_trends" in perceiver_plus_agent._message_handlers
        assert "extract_features" in perceiver_plus_agent._message_handlers


class TestAnalyticsResult:
    def test_analytics_result_to_dict(self) -> None:
        result = AnalyticsResult(
            analysis_id="test-1",
            analytics_type=AnalyticsType.DESCRIPTIVE,
            title="Test Analysis",
            findings=["Finding 1", "Finding 2"],
            metrics={"mean": 5.0, "count": 10},
            confidence=0.95,
        )
        d = result.to_dict()
        assert d["analysis_id"] == "test-1"
        assert d["analytics_type"] == "descriptive"
        assert d["confidence"] == 0.95


class TestTrendAnalysisClass:
    def test_trend_analysis_to_dict(self) -> None:
        trend = TrendAnalysis(
            trend_id="trend-1",
            direction="upward",
            strength=0.8,
            slope=0.5,
            r_squared=0.95,
        )
        d = trend.to_dict()
        assert d["trend_id"] == "trend-1"
        assert d["direction"] == "upward"
        assert d["slope"] == 0.5


class TestCorrelationMatrixClass:
    def test_correlation_matrix_to_dict(self) -> None:
        matrix = CorrelationMatrix(
            matrix_id="corr-1",
            variables=["x", "y"],
            correlations={"x": {"y": 0.95}, "y": {"x": 0.95}},
            significant_pairs=[("x", "y", 0.95)],
        )
        d = matrix.to_dict()
        assert d["matrix_id"] == "corr-1"
        assert len(d["significant_pairs"]) == 1


from heretek_swarm.actors.base import ActorMessage
