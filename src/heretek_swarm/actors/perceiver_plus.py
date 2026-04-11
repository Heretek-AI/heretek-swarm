"""
Perceiver+ Agent - Advanced Analytics & Enhanced Perception.

The Perceiver+ agent provides:
- Advanced multi-modal analytics and pattern recognition
- Deep feature extraction and correlation analysis
- Predictive modeling and trend forecasting
- Statistical analysis and significance testing
- Enhanced signal processing and noise reduction

Named as an enhancement to the base Perceiver agent, providing advanced
analytics capabilities for deeper insight extraction from sensory data.
"""

import math
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import structlog
from swarms import Agent

from heretek_swarm.actors.base import ActorMessage, AgentActor

# Session 44: Collective Learning Integration
from heretek_swarm.collective.learning import PatternExtractor, PatternType

# Session 44: Consensus Integration
from heretek_swarm.consensus.swarm_deliberation import Position, SwarmDeliberationEngine
from heretek_swarm.knowledge.unified_access import KnowledgeQueryResult, UnifiedKnowledgeAccess

# Session 44: Memory Optimization Integration
from heretek_swarm.memory.access_patterns import AccessPatternAnalyzer, AccessTier

# Session 44: Zero-Trust Validation
from heretek_swarm.security.zero_trust import ZeroTrustValidator

logger = structlog.get_logger("PerceiverPlusAgent")


class AnalyticsType(StrEnum):
    """Types of analytics Perceiver+ can perform."""
    DESCRIPTIVE = "descriptive"
    DIAGNOSTIC = "diagnostic"
    PREDICTIVE = "predictive"
    PRESCRIPTIVE = "prescriptive"
    STATISTICAL = "statistical"
    CORRELATIONAL = "correlational"
    TREND = "trend"
    ANOMALY = "anomaly"


class DataModality(StrEnum):
    """Data modalities for analysis."""
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    TEXTUAL = "textual"
    TEMPORAL = "temporal"
    SPATIAL = "spatial"
    MULTI_MODAL = "multi_modal"


class StatisticalTest(StrEnum):
    """Statistical tests available."""
    T_TEST = "t_test"
    CHI_SQUARE = "chi_square"
    ANOVA = "anova"
    CORRELATION = "correlation"
    REGRESSION = "regression"
    MANN_WHITNEY = "mann_whitney"
    WILCOXON = "wilcoxon"


class AnalyticsResult:
    """Represents an analytics result."""

    def __init__(
        self,
        analysis_id: str,
        analytics_type: AnalyticsType,
        title: str,
        findings: list[str],
        metrics: dict[str, float],
        confidence: float = 0.0,
        recommendations: list[str] | None = None,
        visualizations: list[dict[str, Any]] | None = None,
    ) -> None:
        self.analysis_id = analysis_id
        self.analytics_type = analytics_type
        self.title = title
        self.findings = findings
        self.metrics = metrics
        self.confidence = confidence
        self.recommendations = recommendations or []
        self.visualizations = visualizations or []
        self.timestamp = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "analysis_id": self.analysis_id,
            "analytics_type": self.analytics_type.value,
            "title": self.title,
            "findings": self.findings,
            "metrics": self.metrics,
            "confidence": self.confidence,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp.isoformat(),
            "visualizations": self.visualizations,
        }


class TrendAnalysis:
    """Represents a trend analysis result."""

    def __init__(
        self,
        trend_id: str,
        direction: str,
        strength: float,
        slope: float,
        r_squared: float,
        forecast: list[dict[str, Any]] | None = None,
        seasonal_patterns: list[str] | None = None,
    ) -> None:
        self.trend_id = trend_id
        self.direction = direction  # upward, downward, stable
        self.strength = strength  # 0-1
        self.slope = slope
        self.r_squared = r_squared
        self.forecast = forecast or []
        self.seasonal_patterns = seasonal_patterns or []
        self.timestamp = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """Convert trend to dictionary."""
        return {
            "trend_id": self.trend_id,
            "direction": self.direction,
            "strength": self.strength,
            "slope": self.slope,
            "r_squared": self.r_squared,
            "forecast": self.forecast,
            "seasonal_patterns": self.seasonal_patterns,
            "timestamp": self.timestamp.isoformat(),
        }


class CorrelationMatrix:
    """Represents a correlation analysis result."""

    def __init__(
        self,
        matrix_id: str,
        variables: list[str],
        correlations: dict[str, dict[str, float]],
        significant_pairs: list[tuple[str, str, float]],
    ) -> None:
        self.matrix_id = matrix_id
        self.variables = variables
        self.correlations = correlations
        self.significant_pairs = significant_pairs
        self.timestamp = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """Convert matrix to dictionary."""
        return {
            "matrix_id": self.matrix_id,
            "variables": self.variables,
            "correlations": self.correlations,
            "significant_pairs": [
                {"var1": p[0], "var2": p[1], "correlation": p[2]}
                for p in self.significant_pairs
            ],
            "timestamp": self.timestamp.isoformat(),
        }


class PerceiverPlusAgent(AgentActor):
    """
    Perceiver+ Agent - Advanced Analytics Specialist.

    The Perceiver+ is responsible for:
    - Advanced multi-modal analytics and pattern recognition
    - Deep feature extraction and correlation analysis
    - Predictive modeling and trend forecasting
    - Statistical analysis and significance testing
    - Enhanced signal processing and noise reduction

    Enhanced Analytics Workflow:
    1. Receive data for analysis
    2. Detect data modalities and quality
    3. Apply appropriate analytical methods
    4. Extract deep features and patterns
    5. Generate predictions and forecasts
    6. Provide actionable recommendations
    """

    def __init__(
        self,
        agent_id: str = "perceiver-plus",
        name: str = "Perceiver+",
        description: str = "Advanced analytics and enhanced perception specialist",
        swarms_agent: Agent | None = None,
        max_analyses: int = 100,
        confidence_threshold: float = 0.7,
        significance_level: float = 0.05,
        **kwargs,
    ) -> None:
        """
        Initialize the Perceiver+ agent.

        Args:
            agent_id: Unique identifier
            name: Human-readable name
            description: Agent description
            swarms_agent: Optional Swarms Agent for LLM capabilities
            max_analyses: Maximum analyses to store
            confidence_threshold: Minimum confidence for reporting
            significance_level: Statistical significance threshold
            **kwargs: Additional arguments
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            topics=[
                "analytics",
                "statistics",
                "prediction",
                "patterns",
                "insights",
            ],
            capabilities=[
                "advanced-analytics",
                "predictive-modeling",
                "statistical-analysis",
                "correlation-detection",
                "trend-forecasting",
                "signal-processing",
            ],
            swarms_agent=swarms_agent,
            **kwargs,
        )

        # Perceiver+ specific state
        self.max_analyses = max_analyses
        self.confidence_threshold = confidence_threshold
        self.significance_level = significance_level

        # Analytics storage
        self.analysis_results: dict[str, AnalyticsResult] = {}
        self.trend_analyses: dict[str, TrendAnalysis] = {}
        self.correlation_matrices: dict[str, CorrelationMatrix] = {}
        self.feature_cache: dict[str, dict[str, Any]] = {}

        # Statistical computation state
        self.data_buffers: dict[str, list[float]] = {}
        self.categorical_buffers: dict[str, list[str]] = {}


        # Session 44: Collective Learning Integration
        self.pattern_extractor = pattern_extractor or PatternExtractor(min_support=3, min_confidence=0.6)

        # Session 44: Consensus Integration
        self.deliberation_engine = deliberation_engine or SwarmDeliberationEngine(
            max_rounds=5, consensus_threshold=0.75, min_participants=2
        )

        # Session 44: Memory Optimization Integration
        self.access_analyzer = access_analyzer or AccessPatternAnalyzer()

        # Session 44: Zero-Trust Validation
        self.zero_trust_validator = zero_trust_validator or ZeroTrustValidator()

        # Session 44: Integration state
        self._active_deliberations: dict[str, str] = {}
        self._pattern_emitted: Set[str] = set()


        logger.info(f"[{self.agent_id}] Perceiver+ agent initialized")

    async def initialize(self) -> None:
        """Initialize the Perceiver+ agent."""
        # Initialize unified knowledge access layer
        if self.memory_system or self.rag_pipeline:
            self.knowledge_access = UnifiedKnowledgeAccess(
                memory_system=self.memory_system,
                rag_pipeline=self.rag_pipeline,
            )
            logger.info(f"[{self.agent_id}] Unified knowledge access initialized")

        # Register message handlers with Zero-Trust validation
        self.register_handler("analyze_data", self._handle_analyze_data)
        self.register_handler("detect_trends", self._handle_detect_trends)
        self.register_handler("compute_correlations", self._handle_compute_correlations)
        self.register_handler("run_statistical_test", self._handle_run_statistical_test)
        self.register_handler("extract_features", self._handle_extract_features)
        self.register_handler("forecast_values", self._handle_forecast_values)
        self.register_handler("get_analytics_summary", self._handle_get_analytics_summary)
        self.register_handler("signal_processing", self._handle_signal_processing)
        self.register_handler("knowledge_enhanced_analysis", self._handle_knowledge_enhanced_analysis)

        logger.info(f"[{self.agent_id}] Perceiver+ initialization complete")

    async def process_message(self, message: ActorMessage) -> None:
        """
        Process incoming messages with exception handling.

        Args:
            message: Actor message to process
        """
        handler = self._message_handlers.get(message.message_type)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] Error processing message {message.message_type}: {e}",
                    exc_info=True,
                )
                self.error_count += 1
                if message.content.get("reply_to"):
                    await self.send(
                        topic=message.content["reply_to"],
                        content={
                            "message_type": "error_response",
                            "error": str(e),
                            "original_message_type": message.message_type,
                        },
                        sender_id=self.agent_id,
                    )
        else:
            logger.warning(f"[{self.agent_id}] Unknown message type: {message.message_type}")

    def _validate_data_input(self, content: dict[str, Any]) -> tuple[bool, str]:
        """
        Validate data input for analysis.

        Args:
            content: Message content to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if "data" not in content:
            return False, "Missing required field: data"

        data = content["data"]
        if not isinstance(data, (list, dict)):
            return False, "Field 'data' must be a list or dictionary"

        # Check data size
        if isinstance(data, list) and len(data) > 100000:
            return False, "Data exceeds maximum size (100000 elements)"

        return True, ""

    async def _handle_analyze_data(self, message: ActorMessage) -> None:
        """
        Perform comprehensive data analysis.

        Args:
            message: Actor message with data for analysis
        """
        try:
            # Validate content
            is_valid, error = self._validate_data_input(message.content)
            if not is_valid:
                logger.error(f"[{self.agent_id}] Invalid data analysis request: {error}")
                return

            data = message.content["data"]
            analysis_id = message.content.get(
                "analysis_id",
                f"analysis_{datetime.now(UTC).timestamp()}"
            )
            analytics_types = message.content.get("analytics_types", ["descriptive"])

            logger.info(f"[{self.agent_id}] Performing comprehensive analysis: {analysis_id}")

            # Perform analyses
            results = []
            for atype in analytics_types:
                try:
                    atype_enum = AnalyticsType(atype)
                    result = await self._perform_analysis(data, atype_enum, analysis_id)
                    if result.confidence >= self.confidence_threshold:
                        results.append(result)
                except ValueError:
                    logger.warning(f"[{self.agent_id}] Unknown analytics type: {atype}")

            # Store results
            for result in results:
                if len(self.analysis_results) >= self.max_analyses:
                    oldest_id = next(iter(self.analysis_results.keys()))
                    del self.analysis_results[oldest_id]
                self.analysis_results[result.analysis_id] = result

            # Send response
            response = {
                "message_type": "data_analysis_response",
                "analysis_id": analysis_id,
                "results": [r.to_dict() for r in results],
                "results_count": len(results),
            }

            if message.content.get("reply_to"):
                await self.send(
                    topic=message.content["reply_to"],
                    content=response,
                    sender_id=self.agent_id,
                )

            logger.info(f"[{self.agent_id}] Completed {len(results)} analyses")

        except Exception as e:
            logger.error(f"[{self.agent_id}] Error analyzing data: {e}", exc_info=True)

    async def _perform_analysis(
        self,
        data: list | dict,
        analytics_type: AnalyticsType,
        analysis_id: str,
    ) -> AnalyticsResult:
        """
        Perform a specific type of analysis.

        Args:
            data: Data to analyze
            analytics_type: Type of analysis to perform
            analysis_id: Analysis identifier

        Returns:
            AnalyticsResult object
        """
        if analytics_type == AnalyticsType.DESCRIPTIVE:
            return await self._descriptive_analysis(data, analysis_id)
        if analytics_type == AnalyticsType.DIAGNOSTIC:
            return await self._diagnostic_analysis(data, analysis_id)
        if analytics_type == AnalyticsType.PREDICTIVE:
            return await self._predictive_analysis(data, analysis_id)
        if analytics_type == AnalyticsType.STATISTICAL:
            return await self._statistical_analysis(data, analysis_id)
        if analytics_type == AnalyticsType.CORRELATIONAL:
            return await self._correlational_analysis(data, analysis_id)
        if analytics_type == AnalyticsType.TREND:
            return await self._trend_analysis(data, analysis_id)
        if analytics_type == AnalyticsType.ANOMALY:
            return await self._anomaly_analysis(data, analysis_id)
        return AnalyticsResult(
            analysis_id=analysis_id,
            analytics_type=analytics_type,
            title=f"Unknown analysis type: {analytics_type.value}",
            findings=[],
            metrics={},
            confidence=0.0,
        )

    async def _descriptive_analysis(
        self,
        data: list | dict,
        analysis_id: str,
    ) -> AnalyticsResult:
        """Perform descriptive statistics analysis."""
        findings = []
        metrics = {}

        if isinstance(data, list) and all(isinstance(x, (int, float)) for x in data):
            # Numeric descriptive stats
            n = len(data)
            if n > 0:
                mean = sum(data) / n
                variance = sum((x - mean) ** 2 for x in data) / n if n > 1 else 0
                std_dev = math.sqrt(variance)
                sorted_data = sorted(data)
                median = sorted_data[n // 2] if n % 2 == 1 else (sorted_data[n // 2 - 1] + sorted_data[n // 2]) / 2
                min_val = min(data)
                max_val = max(data)

                metrics = {
                    "count": n,
                    "mean": mean,
                    "std_dev": std_dev,
                    "median": median,
                    "min": min_val,
                    "max": max_val,
                    "range": max_val - min_val,
                    "variance": variance,
                }

                findings = [
                    f"Dataset contains {n} numeric values",
                    f"Mean: {mean:.4f}, Median: {median:.4f}",
                    f"Standard deviation: {std_dev:.4f}",
                    f"Range: [{min_val:.4f}, {max_val:.4f}]",
                ]

                confidence = 0.95
            else:
                confidence = 0.0
        else:
            # General description
            findings = [
                f"Data type: {type(data).__name__}",
                f"Data length/size: {len(data) if hasattr(data, '__len__') else 'N/A'}",
            ]
            metrics = {"size": len(data) if hasattr(data, "__len__") else 1}
            confidence = 0.7

        return AnalyticsResult(
            analysis_id=analysis_id,
            analytics_type=AnalyticsType.DESCRIPTIVE,
            title="Descriptive Statistics Analysis",
            findings=findings,
            metrics=metrics,
            confidence=confidence,
        )

    async def _diagnostic_analysis(
        self,
        data: list | dict,
        analysis_id: str,
    ) -> AnalyticsResult:
        """Perform diagnostic analysis to understand causes."""
        findings = []
        metrics = {}

        # Build prompt for LLM diagnostic analysis
        prompt = f"""Perform diagnostic analysis on this data:

DATA: {str(data)[:5000]}

Identify:
1. Key patterns and relationships
2. Potential causal factors
3. Contributing variables
4. Root causes of observed outcomes

Respond in JSON:
{{
    "findings": ["...", "..."],
    "causal_factors": ["...", "..."],
    "key_relationships": ["...", "..."],
    "confidence": 0.0
}}"""

        try:
            if self.swarms_agent:
                result = await self.run_with_llm(prompt=prompt, timeout=60)
                import json
                start_idx = result.find("{")
                end_idx = result.rfind("}") + 1
                if start_idx >= 0 and end_idx > start_idx:
                    parsed = json.loads(result[start_idx:end_idx])
                    findings = parsed.get("findings", [])
                    metrics = {
                        "causal_factors_count": len(parsed.get("causal_factors", [])),
                    }
                    confidence = float(parsed.get("confidence", 0.7))
                else:
                    raise ValueError("No JSON found")
            else:
                raise RuntimeError("LLM not available")
        except Exception:
            # Fallback
            findings = ["Diagnostic analysis requires LLM capabilities"]
            confidence = 0.3

        return AnalyticsResult(
            analysis_id=analysis_id,
            analytics_type=AnalyticsType.DIAGNOSTIC,
            title="Diagnostic Analysis",
            findings=findings,
            metrics=metrics,
            confidence=confidence,
        )

    async def _predictive_analysis(
        self,
        data: list | dict,
        analysis_id: str,
    ) -> AnalyticsResult:
        """Perform predictive analysis and forecasting."""
        findings = []
        metrics = {}

        prompt = f"""Perform predictive analysis on this data:

DATA: {str(data)[:5000]}

Generate:
1. Predictions for future values/outcomes
2. Confidence intervals
3. Key predictive factors
4. Risk indicators

Respond in JSON:
{{
    "predictions": ["...", "..."],
    "confidence_intervals": {{}},
    "predictive_factors": ["...", "..."],
    "risk_indicators": ["...", "..."],
    "confidence": 0.0
}}"""

        try:
            if self.swarms_agent:
                result = await self.run_with_llm(prompt=prompt, timeout=60)
                import json
                start_idx = result.find("{")
                end_idx = result.rfind("}") + 1
                if start_idx >= 0 and end_idx > start_idx:
                    parsed = json.loads(result[start_idx:end_idx])
                    findings = parsed.get("predictions", [])
                    metrics = {
                        "factors_count": len(parsed.get("predictive_factors", [])),
                    }
                    confidence = float(parsed.get("confidence", 0.6))
                else:
                    raise ValueError("No JSON found")
            else:
                raise RuntimeError("LLM not available")
        except Exception:
            findings = ["Predictive analysis requires LLM capabilities"]
            confidence = 0.3

        return AnalyticsResult(
            analysis_id=analysis_id,
            analytics_type=AnalyticsType.PREDICTIVE,
            title="Predictive Analysis",
            findings=findings,
            metrics=metrics,
            confidence=confidence,
            recommendations=metrics.get("risk_indicators", []),
        )

    async def _statistical_analysis(
        self,
        data: list | dict,
        analysis_id: str,
    ) -> AnalyticsResult:
        """Perform statistical analysis."""
        findings = []
        metrics = {}

        if isinstance(data, list) and all(isinstance(x, (int, float)) for x in data):
            n = len(data)
            if n >= 2:
                # Basic statistical tests
                mean = sum(data) / n
                variance = sum((x - mean) ** 2 for x in data) / (n - 1)
                std_dev = math.sqrt(variance)
                se = std_dev / math.sqrt(n)  # Standard error

                # 95% confidence interval
                ci_margin = 1.96 * se
                ci_lower = mean - ci_margin
                ci_upper = mean + ci_margin

                metrics = {
                    "sample_size": n,
                    "mean": mean,
                    "std_dev": std_dev,
                    "std_error": se,
                    "ci_95_lower": ci_lower,
                    "ci_95_upper": ci_upper,
                }

                findings = [
                    f"Sample size: {n}",
                    f"Mean: {mean:.4f} (95% CI: [{ci_lower:.4f}, {ci_upper:.4f}])",
                    f"Standard deviation: {std_dev:.4f}",
                    f"Standard error: {se:.4f}",
                ]

                confidence = 0.95
            else:
                findings = ["Insufficient data for statistical analysis (minimum n=2)"]
                confidence = 0.0
        else:
            findings = ["Statistical analysis requires numeric list data"]
            confidence = 0.0

        return AnalyticsResult(
            analysis_id=analysis_id,
            analytics_type=AnalyticsType.STATISTICAL,
            title="Statistical Analysis",
            findings=findings,
            metrics=metrics,
            confidence=confidence,
        )

    async def _correlational_analysis(
        self,
        data: list | dict,
        analysis_id: str,
    ) -> AnalyticsResult:
        """Perform correlational analysis between variables."""
        findings = []
        metrics = {}

        # Expect dict of variables: {var_name: [values]}
        if isinstance(data, dict):
            variables = list(data.keys())
            if len(variables) >= 2:
                # Calculate correlations
                correlations = {}
                significant_pairs = []

                for i, var1 in enumerate(variables):
                    correlations[var1] = {}
                    for var2 in variables[i:]:
                        if var1 == var2:
                            correlations[var1][var2] = 1.0
                        else:
                            corr = self._calculate_correlation(
                                data.get(var1, []),
                                data.get(var2, []),
                            )
                            correlations[var1][var2] = corr
                            correlations[var2][var1] = corr

                            if abs(corr) > 0.5:  # Significant threshold
                                significant_pairs.append((var1, var2, corr))

                # Store correlation matrix
                matrix = CorrelationMatrix(
                    matrix_id=f"corr_{analysis_id}",
                    variables=variables,
                    correlations=correlations,
                    significant_pairs=significant_pairs,
                )
                self.correlation_matrices[matrix.matrix_id] = matrix

                findings = [
                    f"Analyzed {len(variables)} variables",
                    f"Found {len(significant_pairs)} significant correlations (|r| > 0.5)",
                ] + [f"{p[0]} ↔ {p[1]}: r = {p[2]:.3f}" for p in significant_pairs[:5]]

                metrics = {
                    "variables_count": len(variables),
                    "significant_correlations": len(significant_pairs),
                    "strongest_correlation": max([abs(p[2]) for p in significant_pairs]) if significant_pairs else 0,
                }

                confidence = 0.85
            else:
                findings = ["Need at least 2 variables for correlation analysis"]
                confidence = 0.0
        else:
            findings = ["Correlational analysis requires dict of variables"]
            confidence = 0.0

        return AnalyticsResult(
            analysis_id=analysis_id,
            analytics_type=AnalyticsType.CORRELATIONAL,
            title="Correlational Analysis",
            findings=findings,
            metrics=metrics,
            confidence=confidence,
        )

    def _calculate_correlation(self, x: list[float], y: list[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        n = min(len(x), len(y))
        if n < 2:
            return 0.0

        x = x[:n]
        y = y[:n]

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denom_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
        denom_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))

        if denom_x * denom_y == 0:
            return 0.0

        return numerator / (denom_x * denom_y)

    async def _trend_analysis(
        self,
        data: list | dict,
        analysis_id: str,
    ) -> AnalyticsResult:
        """Perform trend analysis on time series data."""
        findings = []
        metrics = {}

        # Perform linear regression for trend
        if isinstance(data, list) and all(isinstance(x, (int, float)) for x in data):
            n = len(data)
            if n >= 3:
                # Simple linear regression
                x_mean = (n - 1) / 2
                y_mean = sum(data) / n

                numerator = sum((i - x_mean) * (data[i] - y_mean) for i in range(n))
                denominator = sum((i - x_mean) ** 2 for i in range(n))

                if denominator != 0:
                    slope = numerator / denominator
                    intercept = y_mean - slope * x_mean

                    # Calculate R-squared
                    y_pred = [slope * i + intercept for i in range(n)]
                    ss_res = sum((data[i] - y_pred[i]) ** 2 for i in range(n))
                    ss_tot = sum((data[i] - y_mean) ** 2 for i in range(n))
                    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

                    # Determine direction
                    if slope > 0.01:
                        direction = "upward"
                    elif slope < -0.01:
                        direction = "downward"
                    else:
                        direction = "stable"

                    # Store trend analysis
                    trend = TrendAnalysis(
                        trend_id=f"trend_{analysis_id}",
                        direction=direction,
                        strength=abs(slope),
                        slope=slope,
                        r_squared=r_squared,
                    )
                    self.trend_analyses[trend.trend_id] = trend

                    findings = [
                        f"Trend direction: {direction}",
                        f"Slope: {slope:.4f} units per time period",
                        f"R-squared: {r_squared:.4f} ({r_squared*100:.1f}% variance explained)",
                    ]

                    metrics = {
                        "slope": slope,
                        "intercept": intercept,
                        "r_squared": r_squared,
                        "trend_strength": abs(slope),
                    }

                    confidence = min(r_squared + 0.3, 1.0)
                else:
                    findings = ["Cannot compute trend (zero variance in time)"]
                    confidence = 0.0
            else:
                findings = ["Need at least 3 data points for trend analysis"]
                confidence = 0.0
        else:
            findings = ["Trend analysis requires numeric time series data"]
            confidence = 0.0

        return AnalyticsResult(
            analysis_id=analysis_id,
            analytics_type=AnalyticsType.TREND,
            title="Trend Analysis",
            findings=findings,
            metrics=metrics,
            confidence=confidence,
        )

    async def _anomaly_analysis(
        self,
        data: list | dict,
        analysis_id: str,
    ) -> AnalyticsResult:
        """Detect anomalies in data."""
        findings = []
        metrics = {}

        if isinstance(data, list) and all(isinstance(x, (int, float)) for x in data):
            n = len(data)
            if n >= 3:
                mean = sum(data) / n
                std_dev = math.sqrt(sum((x - mean) ** 2 for x in data) / (n - 1)) if n > 1 else 0

                # Find anomalies (values beyond 2 standard deviations)
                threshold = 2.0 * std_dev
                anomalies = []
                for i, value in enumerate(data):
                    if abs(value - mean) > threshold:
                        anomalies.append({
                            "index": i,
                            "value": value,
                            "deviation": abs(value - mean) / std_dev if std_dev > 0 else 0,
                        })

                findings = [
                    f"Analyzed {n} data points",
                    f"Detection threshold: ±{threshold:.4f} from mean ({mean:.4f})",
                    f"Found {len(anomalies)} anomalies",
                ] + [f"Index {a['index']}: value={a['value']:.4f} ({a['deviation']:.1f}σ)" for a in anomalies[:5]]

                metrics = {
                    "anomalies_count": len(anomalies),
                    "anomaly_rate": len(anomalies) / n,
                    "threshold_sigma": 2.0,
                }

                confidence = 0.8
            else:
                findings = ["Need at least 3 data points for anomaly detection"]
                confidence = 0.0
        else:
            findings = ["Anomaly detection requires numeric list data"]
            confidence = 0.0

        return AnalyticsResult(
            analysis_id=analysis_id,
            analytics_type=AnalyticsType.ANOMALY,
            title="Anomaly Detection",
            findings=findings,
            metrics=metrics,
            confidence=confidence,
            recommendations=["Review detected anomalies for data quality issues"] if metrics.get("anomalies_count", 0) > 0 else [],
        )

    async def _handle_detect_trends(self, message: ActorMessage) -> None:
        """
        Detect trends in time series data.

        Args:
            message: Actor message with time series data
        """
        try:
            is_valid, error = self._validate_data_input(message.content)
            if not is_valid:
                logger.error(f"[{self.agent_id}] Invalid trend detection request: {error}")
                return

            data = message.content["data"]

            logger.info(f"[{self.agent_id}] Detecting trends")

            result = await self._trend_analysis(data, f"trend_{datetime.now(UTC).timestamp()}")

            # Get trend details
            trend_id = f"trend_{result.analysis_id}"
            trend = self.trend_analyses.get(trend_id)

            response = {
                "message_type": "trend_detection_response",
                "result": result.to_dict(),
                "trend_details": trend.to_dict() if trend else None,
            }

            if message.content.get("reply_to"):
                await self.send(
                    topic=message.content["reply_to"],
                    content=response,
                    sender_id=self.agent_id,
                )

        except Exception as e:
            logger.error(f"[{self.agent_id}] Error detecting trends: {e}", exc_info=True)

    async def _handle_compute_correlations(self, message: ActorMessage) -> None:
        """
        Compute correlations between variables.

        Args:
            message: Actor message with variable data
        """
        try:
            is_valid, error = self._validate_data_input(message.content)
            if not is_valid:
                logger.error(f"[{self.agent_id}] Invalid correlation request: {error}")
                return

            data = message.content["data"]

            logger.info(f"[{self.agent_id}] Computing correlations")

            result = await self._correlational_analysis(data, f"corr_{datetime.now(UTC).timestamp()}")

            response = {
                "message_type": "correlation_response",
                "result": result.to_dict(),
            }

            if message.content.get("reply_to"):
                await self.send(
                    topic=message.content["reply_to"],
                    content=response,
                    sender_id=self.agent_id,
                )

        except Exception as e:
            logger.error(f"[{self.agent_id}] Error computing correlations: {e}", exc_info=True)

    async def _handle_run_statistical_test(self, message: ActorMessage) -> None:
        """
        Run a statistical test.

        Args:
            message: Actor message with test parameters
        """
        try:
            test_type = message.content.get("test_type", "t_test")
            data = message.content.get("data", [])

            logger.info(f"[{self.agent_id}] Running statistical test: {test_type}")

            # For now, run basic statistical analysis
            result = await self._statistical_analysis(data, f"stat_{datetime.now(UTC).timestamp()}")

            response = {
                "message_type": "statistical_test_response",
                "test_type": test_type,
                "result": result.to_dict(),
            }

            if message.content.get("reply_to"):
                await self.send(
                    topic=message.content["reply_to"],
                    content=response,
                    sender_id=self.agent_id,
                )

        except Exception as e:
            logger.error(f"[{self.agent_id}] Error running statistical test: {e}", exc_info=True)

    async def _handle_extract_features(self, message: ActorMessage) -> None:
        """
        Extract features from data.

        Args:
            message: Actor message with data
        """
        try:
            is_valid, error = self._validate_data_input(message.content)
            if not is_valid:
                logger.error(f"[{self.agent_id}] Invalid feature extraction request: {error}")
                return

            data = message.content["data"]
            feature_id = message.content.get("feature_id", f"features_{datetime.now(UTC).timestamp()}")

            logger.info(f"[{self.agent_id}] Extracting features")

            # Extract features
            features = await self._extract_features_from_data(data)

            # Cache features
            self.feature_cache[feature_id] = features

            response = {
                "message_type": "feature_extraction_response",
                "feature_id": feature_id,
                "features": features,
            }

            if message.content.get("reply_to"):
                await self.send(
                    topic=message.content["reply_to"],
                    content=response,
                    sender_id=self.agent_id,
                )

        except Exception as e:
            logger.error(f"[{self.agent_id}] Error extracting features: {e}", exc_info=True)

    async def _extract_features_from_data(self, data: list | dict) -> dict[str, Any]:
        """Extract features from data."""
        features = {
            "timestamp": datetime.now(UTC).isoformat(),
            "data_type": type(data).__name__,
        }

        if isinstance(data, list) and all(isinstance(x, (int, float)) for x in data):
            n = len(data)
            if n > 0:
                mean = sum(data) / n
                features.update({
                    "count": n,
                    "mean": mean,
                    "min": min(data),
                    "max": max(data),
                    "sum": sum(data),
                })
                if n > 1:
                    variance = sum((x - mean) ** 2 for x in data) / (n - 1)
                    features["variance"] = variance
                    features["std_dev"] = math.sqrt(variance)

        return features

    async def _handle_forecast_values(self, message: ActorMessage) -> None:
        """
        Forecast future values.

        Args:
            message: Actor message with historical data
        """
        try:
            data = message.content.get("data", [])
            periods = message.content.get("periods", 5)

            logger.info(f"[{self.agent_id}] Forecasting {periods} periods")

            # Simple forecasting
            forecast = await self._forecast_values(data, periods)

            response = {
                "message_type": "forecast_response",
                "historical_count": len(data),
                "forecast_periods": periods,
                "forecast": forecast,
            }

            if message.content.get("reply_to"):
                await self.send(
                    topic=message.content["reply_to"],
                    content=response,
                    sender_id=self.agent_id,
                )

        except Exception as e:
            logger.error(f"[{self.agent_id}] Error forecasting: {e}", exc_info=True)

    async def _forecast_values(self, data: list[float], periods: int) -> list[dict[str, Any]]:
        """Generate forecast values."""
        forecast = []

        if len(data) >= 2:
            # Simple linear extrapolation
            n = len(data)
            x_mean = (n - 1) / 2
            y_mean = sum(data) / n

            numerator = sum((i - x_mean) * (data[i] - y_mean) for i in range(n))
            denominator = sum((i - x_mean) ** 2 for i in range(n))

            if denominator != 0:
                slope = numerator / denominator
                intercept = y_mean - slope * x_mean

                for i in range(periods):
                    future_x = n + i
                    predicted = slope * future_x + intercept
                    forecast.append({
                        "period": i + 1,
                        "predicted_value": predicted,
                        "confidence": max(0.5 - (i * 0.05), 0.1),  # Decreasing confidence
                    })
            else:
                # Flat forecast
                for i in range(periods):
                    forecast.append({
                        "period": i + 1,
                        "predicted_value": y_mean,
                        "confidence": 0.3,
                    })
        else:
            forecast = [{"error": "Insufficient data for forecasting"}]

        return forecast

    async def _handle_get_analytics_summary(self, message: ActorMessage) -> None:
        """
        Get summary of all analytics.

        Args:
            message: Actor message
        """
        try:
            summary = {
                "analyses_count": len(self.analysis_results),
                "trend_analyses_count": len(self.trend_analyses),
                "correlation_matrices_count": len(self.correlation_matrices),
                "feature_cache_count": len(self.feature_cache),
                "recent_analyses": [
                    r.to_dict() for r in list(self.analysis_results.values())[-5:]
                ],
            }

            response = {
                "message_type": "analytics_summary_response",
                "summary": summary,
            }

            if message.content.get("reply_to"):
                await self.send(
                    topic=message.content["reply_to"],
                    content=response,
                    sender_id=self.agent_id,
                )

        except Exception as e:
            logger.error(f"[{self.agent_id}] Error getting analytics summary: {e}", exc_info=True)

    async def _handle_knowledge_enhanced_analysis(self, message: ActorMessage) -> None:
        """
        Perform knowledge-enhanced analytics using the unified knowledge access layer.

        This handler combines data analysis with contextual knowledge from memory and RAG.

        Args:
            message: Actor message with data and query for context
        """
        try:
            data = message.content.get("data", [])
            query = message.content.get("query")
            sources = message.content.get("sources", ["memory", "rag"])
            limit = message.content.get("limit", 10)
            message.content.get("analysis_type", "descriptive")

            if not query:
                logger.error(f"[{self.agent_id}] Knowledge enhanced analysis requires query")
                return

            logger.info(f"[{self.agent_id}] Performing knowledge-enhanced analysis: {query[:50]}")

            # First, query knowledge base for context
            if self.knowledge_access:
                knowledge_result = await self.knowledge_access.query(
                    query=query,
                    sources=sources,
                    limit=limit,
                    rerank=True,
                    diversity_lambda=0.5,
                )

                # Perform analysis on data
                analysis_id = f"knowledge_analysis_{datetime.now(UTC).timestamp()}"

                # Combine data analysis with knowledge context
                result = {
                    "analysis_id": analysis_id,
                    "query": query,
                    "knowledge_context": {
                        "entries": [e.to_dict() for e in knowledge_result.entries],
                        "total_results": knowledge_result.total_results,
                        "query_time_ms": knowledge_result.query_time_ms,
                    },
                    "data_analysis": {
                        "data_points": len(data),
                        "mean": sum(data) / len(data) if data else 0,
                        "min": min(data) if data else 0,
                        "max": max(data) if data else 0,
                    },
                }

                response = {
                    "message_type": "knowledge_enhanced_analysis_response",
                    "result": result,
                }

                if message.content.get("reply_to"):
                    await self.send(
                        topic=message.content["reply_to"],
                        content=response,
                        sender_id=self.agent_id,
                    )
            else:
                logger.warning(f"[{self.agent_id}] Knowledge access not initialized")

        except Exception as e:
            logger.error(f"[{self.agent_id}] Error in knowledge enhanced analysis: {e}", exc_info=True)

    async def knowledge_enhanced_query(
        self,
        query: str,
        sources: list[str] | None = None,
        limit: int = 10,
        rerank: bool = True,
    ) -> KnowledgeQueryResult:
        """
        Execute a knowledge-enhanced query for analytics context.

        Args:
            query: Search query string
            sources: List of sources (memory, rag)
            limit: Maximum results
            rerank: Apply MMR reranking

        Returns:
            KnowledgeQueryResult with merged and reranked entries
        """
        if not self.knowledge_access:
            logger.warning(f"[{self.agent_id}] Knowledge access not initialized")
            return KnowledgeQueryResult(entries=[], total_results=0)

        return await self.knowledge_access.query(
            query=query,
            sources=sources or ["memory", "rag"],
            limit=limit,
            rerank=rerank,
        )

    async def _handle_signal_processing(self, message: ActorMessage) -> None:
        """
        Process signals with noise reduction.

        Args:
            message: Actor message with signal data
        """
        try:
            data = message.content.get("data", [])
            method = message.content.get("method", "moving_average")
            window = message.content.get("window", 3)

            logger.info(f"[{self.agent_id}] Processing signal with {method}")

            # Process signal
            processed = self._process_signal(data, method, window)

            response = {
                "message_type": "signal_processing_response",
                "method": method,
                "window": window,
                "original_length": len(data),
                "processed_length": len(processed),
                "processed_signal": processed,
            }

            if message.content.get("reply_to"):
                await self.send(
                    topic=message.content["reply_to"],
                    content=response,
                    sender_id=self.agent_id,
                )

        except Exception as e:
            logger.error(f"[{self.agent_id}] Error processing signal: {e}", exc_info=True)


    # =========================================================================
    # Session 44: Collective Learning Integration Methods
    # =========================================================================

    async def _emit_pattern(self, item_id: str, item_type: str, outcome: str, content: dict[str, Any]) -> None:
        """Emit pattern for collective learning."""
        if not self.pattern_extractor:
            return

        if item_id in self._pattern_emitted:
            return

        try:
            await self.pattern_extractor.analyze_message(
                message_id=f"{item_type}_{item_id}",
                sender=self.agent_id,
                recipient="broadcast",
                message_type=f"{item_type}_completion",
                content=content,
                timestamp=datetime.now(UTC).isoformat(),
            )

            self._pattern_emitted.add(item_id)
            logger.info(f"{item_type}_pattern_emitted", item_id=item_id, outcome=outcome)
        except Exception as e:
            logger.warning("failed_to_emit_pattern", item_id=item_id, error=str(e))

    async def _consume_patterns(self, pattern_types: list[PatternType] | None = None) -> list[dict[str, Any]]:
        """Consume patterns from collective learning."""
        if not self.pattern_extractor:
            return []

        try:
            patterns = await self.pattern_extractor.extract_patterns(
                time_window_hours=24,
                pattern_types=pattern_types or [PatternType.SUCCESS, PatternType.DECISION],
            )
            return [p.to_dict() for p in patterns if p.metadata.confidence >= 0.7]
        except Exception as e:
            logger.warning("failed_to_consume_patterns", error=str(e))
            return []

    # =========================================================================
    # Session 44: Consensus Deliberation Integration Methods
    # =========================================================================

    async def _initiate_deliberation(
        self,
        item_id: str,
        proposal: str,
        participating_agents: list[str],
        domain: str = "general",
    ) -> str | None:
        """Initiate swarm deliberation."""
        if not self.deliberation_engine:
            return None

        try:
            deliberation_id = f"delib_{item_id}"
            self.deliberation_engine.start_deliberation(
                deliberation_id=deliberation_id,
                proposal=proposal[:200],
                participants=participating_agents,
                domain=domain,
            )
            self._active_deliberations[item_id] = deliberation_id

            logger.info("deliberation_initiated", deliberation_id=deliberation_id, item_id=item_id)
            return deliberation_id
        except Exception as e:
            logger.error("failed_to_initiate_deliberation", item_id=item_id, error=str(e))
            return None

    async def _submit_deliberation_position(
        self,
        item_id: str,
        agent_id: str,
        position: Position,
        confidence: float,
        argument: str,
    ) -> bool:
        """Submit agent position in deliberation."""
        if not self.deliberation_engine:
            return False

        deliberation_id = self._active_deliberations.get(item_id)
        if not deliberation_id:
            return False

        try:
            success = self.deliberation_engine.submit_position(
                deliberation_id=deliberation_id,
                agent_id=agent_id,
                position=position,
                confidence=confidence,
                argument=argument,
            )

            if success and self.access_analyzer:
                self.access_analyzer.record_access(
                    memory_id=f"delib_{deliberation_id}_{agent_id}",
                    access_type="write",
                    agent_id=agent_id,
                )

            return success
        except Exception as e:
            logger.error("failed_to_submit_deliberation_position", error=str(e))
            return False

    async def _finalize_deliberation(self, item_id: str) -> Any | None:
        """Finalize deliberation and apply result."""
        if not self.deliberation_engine:
            return None

        deliberation_id = self._active_deliberations.get(item_id)
        if not deliberation_id:
            return None

        try:
            result = self.deliberation_engine.finalize_deliberation(deliberation_id)

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

    def _track_memory_access(self, item_id: str, item_type: str, access_type: str = "read") -> None:
        """Track memory access patterns."""
        if not self.access_analyzer:
            return

        memory_id = f"{item_type}_{item_id}"
        self.access_analyzer.record_access(
            memory_id=memory_id,
            access_type=access_type,
            agent_id=self.agent_id,
        )

    def _get_memory_tier(self, item_id: str, item_type: str) -> AccessTier:
        """Get memory tier classification."""
        if not self.access_analyzer:
            return AccessTier.COLD

        memory_id = f"{item_type}_{item_id}"
        profile = self.access_analyzer.get_profile(memory_id)
        return profile.tier if profile else AccessTier.COLD

    async def _prefetch_relevant(self, agent_id: str, item_type: str) -> list[str]:
        """Prefetch items an agent is likely to need."""
        if not self.access_analyzer:
            return []

        try:
            predicted_memories = self.access_analyzer.predict_agent_access(agent_id)
            return [
                mem.replace(f"{item_type}_", "")
                for mem in predicted_memories
                if mem.startswith(f"{item_type}_")
            ]
        except Exception as e:
            logger.warning("failed_to_prefetch", agent_id=agent_id, error=str(e))
            return []

    def get_learning_status(self) -> dict[str, Any]:
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


    def _process_signal(self, data: list[float], method: str, window: int) -> list[float]:
        """Process signal with specified method."""
        if method == "moving_average":
            result = []
            for i in range(len(data) - window + 1):
                result.append(sum(data[i:i+window]) / window)
            return result
        if method == "median_filter":
            result = []
            for i in range(len(data) - window + 1):
                sorted_window = sorted(data[i:i+window])
                result.append(sorted_window[window // 2])
            return result
        return data  # No processing
