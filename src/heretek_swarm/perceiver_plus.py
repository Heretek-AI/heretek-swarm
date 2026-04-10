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
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum

import structlog
from swarms import Agent

from heretek_swarm.actors.base import AgentActor, ActorMessage
from heretek_swarm.knowledge.unified_access import UnifiedKnowledgeAccess, KnowledgeQueryResult

# Session 44: Collective Learning Integration
from heretek_swarm.collective.learning import PatternExtractor, PatternType

# Session 44: Consensus Integration
from heretek_swarm.consensus.swarm_deliberation import SwarmDeliberationEngine, Position

# Session 44: Memory Optimization Integration
from heretek_swarm.memory.access_patterns import AccessPatternAnalyzer, AccessTier

# Session 44: Zero-Trust Validation
from heretek_swarm.security.zero_trust import ZeroTrustValidator


_logger = structlog.get_logger("PerceiverPlusAgent")


class AnalyticsType(str, Enum):
    """Types of analytics Perceiver+ can perform."""
    DESCRIPTIVE = "descriptive"
    DIAGNOSTIC = "diagnostic"
    PREDICTIVE = "predictive"
    PRESCRIPTIVE = "prescriptive"
    STATISTICAL = "statistical"
    CORRELATIONAL = "correlational"
    TREND = "trend"
    ANOMALY = "anomaly"


class DataModality(str, Enum):
    """Data modalities for analysis."""
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    TEXTUAL = "textual"
    TEMPORAL = "temporal"
    SPATIAL = "spatial"
    MULTI_MODAL = "multi_modal"


class StatisticalTest(str, Enum):
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
    
    def __init__(self, _analysis_id: str, _analytics_type: AnalyticsType, _title: str, _findings: List[str], _metrics: Dict[str, float], _confidence: float, _recommendations: Optional[List[str]], _visualizations: Optional[List[Dict[str, Any]]]) -> None:
        self.analysis_id = analysis_id
        self.analytics_type = analytics_type
        self.title = title
        self.findings = findings
        self.metrics = metrics
        self.confidence = confidence
        self.recommendations = recommendations or []
        self.visualizations = visualizations or []
        self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
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
    
    def __init__(self, _trend_id: str, _direction: str, _strength: float, _slope: float, _r_squared: float, _forecast: Optional[List[Dict[str, Any]]], _seasonal_patterns: Optional[List[str]]) -> None:
        self.trend_id = trend_id
        self.direction = direction  # upward, downward, stable
        self.strength = strength  # 0-1
        self.slope = slope
        self.r_squared = r_squared
        self.forecast = forecast or []
        self.seasonal_patterns = seasonal_patterns or []
        self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
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
    
    def __init__(self, _matrix_id: str, _variables: List[str], _correlations: Dict[str, Dict[str, float]], _significant_pairs: List[Tuple[str, str, float]]) -> None:
        self.matrix_id = matrix_id
        self.variables = variables
        self.correlations = correlations
        self.significant_pairs = significant_pairs
        self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
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
    
    def __init__(self, _agent_id: str, _name: str, _description: str, _swarms_agent: Optional[Agent], _max_analyses: int, _confidence_threshold: float, _significance_level: float, **kwargs) -> None:
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
            _name = name,
            _description = description,
            _topics = [
                "analytics",
                "statistics",
                "prediction",
                "patterns",
                "insights",
            ],
            _capabilities = [
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
        self.analysis_results: Dict[str, AnalyticsResult] = {}
        self.trend_analyses: Dict[str, TrendAnalysis] = {}
        self.correlation_matrices: Dict[str, CorrelationMatrix] = {}
        self.feature_cache: Dict[str, Dict[str, Any]] = {}
        
        # Statistical computation state
        self.data_buffers: Dict[str, List[float]] = {}
        self.categorical_buffers: Dict[str, List[str]] = {}
        
        
        # Session 44: Collective Learning Integration
        self.pattern_extractor = pattern_extractor or PatternExtractor(min_support=3, min_confidence=0.6)
        
        # Session 44: Consensus Integration
        self.deliberation_engine = deliberation_engine or SwarmDeliberationEngine(
            _max_rounds = 5, consensus_threshold=0.75, min_participants=2
        )
        
        # Session 44: Memory Optimization Integration
        self.access_analyzer = access_analyzer or AccessPatternAnalyzer()
        
        # Session 44: Zero-Trust Validation
        self.zero_trust_validator = zero_trust_validator or ZeroTrustValidator()
        
        # Session 44: Integration state
        self._active_deliberations: Dict[str, str] = {}
        self._pattern_emitted: Set[str] = set()


        logger.info(f"[{self.agent_id}] Perceiver+ agent initialized")
    
    async def initialize(self) -> None:
        """Initialize the Perceiver+ agent."""
        # Initialize unified knowledge access layer
        if self.memory_system or self.rag_pipeline:
            self.knowledge_access = UnifiedKnowledgeAccess(
                _memory_system = self.memory_system,
                _rag_pipeline = self.rag_pipeline,
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
    
    async def process_message(self, _message: ActorMessage) -> None:
        """
        Process incoming messages with exception handling.
        
        Args:
            message: Actor message to process
        """
        _handler = self._message_handlers.get(message.message_type)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] Error processing message {message.message_type}: {e}",
                    _exc_info = True,
                )
                self.error_count += 1
                if message.content.get("reply_to"):
                    await self.send(
                        _topic = message.content["reply_to"],
                        content={
                            "message_type": "error_response",
                            "error": str(e),
                            "original_message_type": message.message_type,
                        },
                        _sender_id = self.agent_id,
                    )
        else:
            logger.warning(f"[{self.agent_id}] Unknown message type: {message.message_type}")
    
    def _validate_data_input(self, _content: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate data input for analysis.
        
        Args:
            content: Message content to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if "data" not in content:
            return False, "Missing required field: data"
        
        _data = content["data"]
        if not isinstance(data, (list, dict)):
            return False, "Field 'data' must be a list or dictionary"
        
        # Check data size
        if isinstance(data, list) and len(data) > 100000:
            return False, "Data exceeds maximum size (100000 elements)"
        
        return True, ""
    
    async def _handle_analyze_data(self, _message: ActorMessage) -> None:
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
            
            _data = message.content["data"]
            analysis_id = message.content.get(
                "analysis_id", 
                f"analysis_{datetime.now(timezone.utc).timestamp()}"
            )
            _analytics_types = message.content.get("analytics_types", ["descriptive"])
            
            logger.info(f"[{self.agent_id}] Performing comprehensive analysis: {analysis_id}")
            
            # Perform analyses
            _results = []
            for atype in analytics_types:
                try:
                    _atype_enum = AnalyticsType(atype)
                    _result = await self._perform_analysis(data, atype_enum, analysis_id)
                    if result.confidence >= self.confidence_threshold:
                        results.append(result)
                except ValueError:
                    logger.warning(f"[{self.agent_id}] Unknown analytics type: {atype}")
            
            # Store results
            for result in results:
                if len(self.analysis_results) >= self.max_analyses:
                    _oldest_id = list(self.analysis_results.keys())[0]
                    del self.analysis_results[oldest_id]
                self.analysis_results[result.analysis_id] = result
            
            # Send response
            _response = {
                "message_type": "data_analysis_response",
                "analysis_id": analysis_id,
                "results": [r.to_dict() for r in results],
                "results_count": len(results),
            }
            
            if message.content.get("reply_to"):
                await self.send(
                    _topic = message.content["reply_to"],
                    _content = response,
                    _sender_id = self.agent_id,
                )
            
            logger.info(f"[{self.agent_id}] Completed {len(results)} analyses")
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error analyzing data: {e}", exc_info=True)
    
    async def _perform_analysis(self, _data: Union[List, Dict], _analytics_type: AnalyticsType, _analysis_id: str) -> AnalyticsResult:
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
        elif analytics_type == AnalyticsType.DIAGNOSTIC:
            return await self._diagnostic_analysis(data, analysis_id)
        elif analytics_type == AnalyticsType.PREDICTIVE:
            return await self._predictive_analysis(data, analysis_id)
        elif analytics_type == AnalyticsType.STATISTICAL:
            return await self._statistical_analysis(data, analysis_id)
        elif analytics_type == AnalyticsType.CORRELATIONAL:
            return await self._correlational_analysis(data, analysis_id)
        elif analytics_type == AnalyticsType.TREND:
            return await self._trend_analysis(data, analysis_id)
        elif analytics_type == AnalyticsType.ANOMALY:
            return await self._anomaly_analysis(data, analysis_id)
        else:
            return AnalyticsResult(
                analysis_id=analysis_id,
                _analytics_type = analytics_type,
                _title = f"Unknown analysis type: {analytics_type.value}",
                _findings = [],
                _metrics = {},
                confidence=0.0,
            )
    
    async def _descriptive_analysis(self, _data: Union[List, Dict], _analysis_id: str) -> AnalyticsResult:
        """Perform descriptive statistics analysis."""
        _findings = []
        _metrics = {}
        
        if isinstance(data, list) and all(isinstance(x, (int, float)) for x in data):
            # Numeric descriptive stats
            n = len(data)
            if n > 0:
                _mean = sum(data) / n
                _variance = sum((x - mean) ** 2 for x in data) / n if n > 1 else 0
                _std_dev = math.sqrt(variance)
                _sorted_data = sorted(data)
                _median = sorted_data[n // 2] if n % 2 == 1 else (sorted_data[n // 2 - 1] + sorted_data[n // 2]) / 2
                _min_val = min(data)
                _max_val = max(data)
                
                _metrics = {
                    "count": n,
                    "mean": mean,
                    "std_dev": std_dev,
                    "median": median,
                    "min": min_val,
                    "max": max_val,
                    "range": max_val - min_val,
                    "variance": variance,
                }
                
                _findings = [
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
            _findings = [
                f"Data type: {type(data).__name__}",
                f"Data length/size: {len(data) if hasattr(data, '__len__') else 'N/A'}",
            ]
            _metrics = {"size": len(data) if hasattr(data, '__len__') else 1}
            confidence = 0.7
        
        return AnalyticsResult(
            analysis_id=analysis_id,
            _analytics_type = AnalyticsType.DESCRIPTIVE,
            _title = "Descriptive Statistics Analysis",
            _findings = findings,
            _metrics = metrics,
            confidence=confidence,
        )
    
    async def _diagnostic_analysis(self, _data: Union[List, Dict], _analysis_id: str) -> AnalyticsResult:
        """Perform diagnostic analysis to understand causes."""
        _findings = []
        _metrics = {}
        
        # Build prompt for LLM diagnostic analysis
        _prompt = f"""Perform diagnostic analysis on this data:

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
        
        # Fallback values
        _findings = ["Diagnostic analysis requires LLM capabilities"]
        confidence = 0.3
        metrics = {}

        if self.swarms_agent:
            try:
                _result = await self.run_with_llm(prompt=prompt, timeout=60)
                import json
                _start_idx = result.find("{")
                _end_idx = result.rfind("}") + 1
                if start_idx >= 0 and end_idx > start_idx:
                    _parsed = json.loads(result[start_idx:end_idx])
                    _findings = parsed.get("findings", [])
                    _metrics = {
                        "causal_factors_count": len(parsed.get("causal_factors", [])),
                    }
                    confidence = float(parsed.get("confidence", 0.7))
            except Exception:
                pass  # Use fallback values set above
        
        return AnalyticsResult(
            analysis_id=analysis_id,
            _analytics_type = AnalyticsType.DIAGNOSTIC,
            _title = "Diagnostic Analysis",
            _findings = findings,
            _metrics = metrics,
            confidence=confidence,
        )
    
    async def _predictive_analysis(self, _data: Union[List, Dict], _analysis_id: str) -> AnalyticsResult:
        """Perform predictive analysis and forecasting."""
        _findings = []
        _metrics = {}
        
        _prompt = f"""Perform predictive analysis on this data:

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
        
        # Fallback values
        _findings = ["Predictive analysis requires LLM capabilities"]
        confidence = 0.3
        metrics = {}

        if self.swarms_agent:
            try:
                _result = await self.run_with_llm(prompt=prompt, timeout=60)
                import json
                _start_idx = result.find("{")
                _end_idx = result.rfind("}") + 1
                if start_idx >= 0 and end_idx > start_idx:
                    _parsed = json.loads(result[start_idx:end_idx])
                    _findings = parsed.get("predictions", [])
                    _metrics = {
                        "factors_count": len(parsed.get("predictive_factors", [])),
                    }
                    confidence = float(parsed.get("confidence", 0.6))
            except Exception:
                pass  # Use fallback values set above
        
        return AnalyticsResult(
            analysis_id=analysis_id,
            _analytics_type = AnalyticsType.PREDICTIVE,
            _title = "Predictive Analysis",
            _findings = findings,
            _metrics = metrics,
            confidence=confidence,
            _recommendations = metrics.get("risk_indicators", []),
        )
    
    async def _statistical_analysis(self, _data: Union[List, Dict], _analysis_id: str) -> AnalyticsResult:
        """Perform statistical analysis."""
        _findings = []
        _metrics = {}
        
        if isinstance(data, list) and all(isinstance(x, (int, float)) for x in data):
            n = len(data)
            if n >= 2:
                # Basic statistical tests
                _mean = sum(data) / n
                _variance = sum((x - mean) ** 2 for x in data) / (n - 1)
                _std_dev = math.sqrt(variance)
                se = std_dev / math.sqrt(n)  # Standard error
                
                # 95% confidence interval
                _ci_margin = 1.96 * se
                _ci_lower = mean - ci_margin
                _ci_upper = mean + ci_margin
                
                _metrics = {
                    "sample_size": n,
                    "mean": mean,
                    "std_dev": std_dev,
                    "std_error": se,
                    "ci_95_lower": ci_lower,
                    "ci_95_upper": ci_upper,
                }
                
                _findings = [
                    f"Sample size: {n}",
                    f"Mean: {mean:.4f} (95% CI: [{ci_lower:.4f}, {ci_upper:.4f}])",
                    f"Standard deviation: {std_dev:.4f}",
                    f"Standard error: {se:.4f}",
                ]
                
                confidence = 0.95
            else:
                _findings = ["Insufficient data for statistical analysis (minimum n=2)"]
                confidence = 0.0
        else:
            _findings = ["Statistical analysis requires numeric list data"]
            confidence = 0.0
        
        return AnalyticsResult(
            analysis_id=analysis_id,
            _analytics_type = AnalyticsType.STATISTICAL,
            _title = "Statistical Analysis",
            _findings = findings,
            _metrics = metrics,
            confidence=confidence,
        )
    
    async def _correlational_analysis(self, _data: Union[List, Dict], _analysis_id: str) -> AnalyticsResult:
        """Perform correlational analysis between variables."""
        _findings = []
        _metrics = {}
        
        # Expect dict of variables: {var_name: [values]}
        if isinstance(data, dict):
            _variables = list(data.keys())
            if len(variables) >= 2:
                # Calculate correlations
                _correlations = {}
                _significant_pairs = []
                
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
                    _variables = variables,
                    _correlations = correlations,
                    _significant_pairs = significant_pairs,
                )
                self.correlation_matrices[matrix.matrix_id] = matrix
                
                _findings = [
                    f"Analyzed {len(variables)} variables",
                    f"Found {len(significant_pairs)} significant correlations (|r| > 0.5)",
                ] + [f"{p[0]} ↔ {p[1]}: r = {p[2]:.3f}" for p in significant_pairs[:5]]
                
                _metrics = {
                    "variables_count": len(variables),
                    "significant_correlations": len(significant_pairs),
                    "strongest_correlation": max([abs(p[2]) for p in significant_pairs]) if significant_pairs else 0,
                }
                
                confidence = 0.85
            else:
                _findings = ["Need at least 2 variables for correlation analysis"]
                confidence = 0.0
        else:
            _findings = ["Correlational analysis requires dict of variables"]
            confidence = 0.0
        
        return AnalyticsResult(
            analysis_id=analysis_id,
            _analytics_type = AnalyticsType.CORRELATIONAL,
            _title = "Correlational Analysis",
            _findings = findings,
            _metrics = metrics,
            confidence=confidence,
        )
    
    def _calculate_correlation(self, _x: List[float], _y: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        n = min(len(x), len(y))
        if n < 2:
            return 0.0
        
        _x = x[:n]
        _y = y[:n]
        
        _mean_x = sum(x) / n
        _mean_y = sum(y) / n
        
        _numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        _denom_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
        _denom_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))
        
        if denom_x * denom_y == 0:
            return 0.0
        
        return numerator / (denom_x * denom_y)
    
    async def _trend_analysis(self, _data: Union[List, Dict], _analysis_id: str) -> AnalyticsResult:
        """Perform trend analysis on time series data."""
        _findings = []
        _metrics = {}
        
        # Perform linear regression for trend
        if isinstance(data, list) and all(isinstance(x, (int, float)) for x in data):
            n = len(data)
            if n >= 3:
                # Simple linear regression
                _x_mean = (n - 1) / 2
                _y_mean = sum(data) / n
                
                _numerator = sum((i - x_mean) * (data[i] - y_mean) for i in range(n))
                _denominator = sum((i - x_mean) ** 2 for i in range(n))
                
                if denominator != 0:
                    _slope = numerator / denominator
                    _intercept = y_mean - slope * x_mean
                    
                    # Calculate R-squared
                    _y_pred = [slope * i + intercept for i in range(n)]
                    _ss_res = sum((data[i] - y_pred[i]) ** 2 for i in range(n))
                    _ss_tot = sum((data[i] - y_mean) ** 2 for i in range(n))
                    _r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
                    
                    # Determine direction
                    if slope > 0.01:
                        _direction = "upward"
                    elif slope < -0.01:
                        _direction = "downward"
                    else:
                        _direction = "stable"
                    
                    # Store trend analysis
                    trend = TrendAnalysis(
                        trend_id=f"trend_{analysis_id}",
                        _direction = direction,
                        _strength = abs(slope),
                        _slope = slope,
                        _r_squared = r_squared,
                    )
                    self.trend_analyses[trend.trend_id] = trend
                    
                    _findings = [
                        f"Trend direction: {direction}",
                        f"Slope: {slope:.4f} units per time period",
                        f"R-squared: {r_squared:.4f} ({r_squared*100:.1f}% variance explained)",
                    ]
                    
                    _metrics = {
                        "slope": slope,
                        "intercept": intercept,
                        "r_squared": r_squared,
                        "trend_strength": abs(slope),
                    }
                    
                    confidence = min(r_squared + 0.3, 1.0)
                else:
                    _findings = ["Cannot compute trend (zero variance in time)"]
                    confidence = 0.0
            else:
                _findings = ["Need at least 3 data points for trend analysis"]
                confidence = 0.0
        else:
            _findings = ["Trend analysis requires numeric time series data"]
            confidence = 0.0
        
        return AnalyticsResult(
            analysis_id=analysis_id,
            _analytics_type = AnalyticsType.TREND,
            _title = "Trend Analysis",
            _findings = findings,
            _metrics = metrics,
            confidence=confidence,
        )
    
    async def _anomaly_analysis(self, _data: Union[List, Dict], _analysis_id: str) -> AnalyticsResult:
        """Detect anomalies in data."""
        _findings = []
        _metrics = {}
        
        if isinstance(data, list) and all(isinstance(x, (int, float)) for x in data):
            n = len(data)
            if n >= 3:
                _mean = sum(data) / n
                _std_dev = math.sqrt(sum((x - mean) ** 2 for x in data) / (n - 1)) if n > 1 else 0
                
                # Find anomalies (values beyond 2 standard deviations)
                _threshold = 2.0 * std_dev
                _anomalies = []
                for i, value in enumerate(data):
                    if abs(value - mean) > threshold:
                        anomalies.append({
                            "index": i,
                            "value": value,
                            "deviation": abs(value - mean) / std_dev if std_dev > 0 else 0,
                        })
                
                _findings = [
                    f"Analyzed {n} data points",
                    f"Detection threshold: ±{threshold:.4f} from mean ({mean:.4f})",
                    f"Found {len(anomalies)} anomalies",
                ] + [f"Index {a['index']}: value={a['value']:.4f} ({a['deviation']:.1f}σ)" for a in anomalies[:5]]
                
                _metrics = {
                    "anomalies_count": len(anomalies),
                    "anomaly_rate": len(anomalies) / n,
                    "threshold_sigma": 2.0,
                }
                
                confidence = 0.8
            else:
                _findings = ["Need at least 3 data points for anomaly detection"]
                confidence = 0.0
        else:
            _findings = ["Anomaly detection requires numeric list data"]
            confidence = 0.0
        
        return AnalyticsResult(
            analysis_id=analysis_id,
            _analytics_type = AnalyticsType.ANOMALY,
            _title = "Anomaly Detection",
            _findings = findings,
            _metrics = metrics,
            confidence=confidence,
            _recommendations = ["Review detected anomalies for data quality issues"] if metrics.get("anomalies_count", 0) > 0 else [],
        )
    
    async def _handle_detect_trends(self, _message: ActorMessage) -> None:
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
            
            _data = message.content["data"]
            
            logger.info(f"[{self.agent_id}] Detecting trends")
            
            _result = await self._trend_analysis(data, f"trend_{datetime.now(timezone.utc).timestamp()}")
            
            # Get trend details
            _trend_id = f"trend_{result.analysis_id}"
            trend = self.trend_analyses.get(trend_id)
            
            _response = {
                "message_type": "trend_detection_response",
                "result": result.to_dict(),
                "trend_details": trend.to_dict() if trend else None,
            }
            
            if message.content.get("reply_to"):
                await self.send(
                    _topic = message.content["reply_to"],
                    _content = response,
                    _sender_id = self.agent_id,
                )
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error detecting trends: {e}", exc_info=True)
    
    async def _handle_compute_correlations(self, _message: ActorMessage) -> None:
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
            
            _data = message.content["data"]
            
            logger.info(f"[{self.agent_id}] Computing correlations")
            
            _result = await self._correlational_analysis(data, f"corr_{datetime.now(timezone.utc).timestamp()}")
            
            _response = {
                "message_type": "correlation_response",
                "result": result.to_dict(),
            }
            
            if message.content.get("reply_to"):
                await self.send(
                    _topic = message.content["reply_to"],
                    _content = response,
                    _sender_id = self.agent_id,
                )
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error computing correlations: {e}", exc_info=True)
    
    async def _handle_run_statistical_test(self, _message: ActorMessage) -> None:
        """
        Run a statistical test.
        
        Args:
            message: Actor message with test parameters
        """
        try:
            _test_type = message.content.get("test_type", "t_test")
            _data = message.content.get("data", [])
            
            logger.info(f"[{self.agent_id}] Running statistical test: {test_type}")
            
            # For now, run basic statistical analysis
            _result = await self._statistical_analysis(data, f"stat_{datetime.now(timezone.utc).timestamp()}")
            
            _response = {
                "message_type": "statistical_test_response",
                "test_type": test_type,
                "result": result.to_dict(),
            }
            
            if message.content.get("reply_to"):
                await self.send(
                    _topic = message.content["reply_to"],
                    _content = response,
                    _sender_id = self.agent_id,
                )
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error running statistical test: {e}", exc_info=True)
    
    async def _handle_extract_features(self, _message: ActorMessage) -> None:
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
            
            _data = message.content["data"]
            _feature_id = message.content.get("feature_id", f"features_{datetime.now(timezone.utc).timestamp()}")
            
            logger.info(f"[{self.agent_id}] Extracting features")
            
            # Extract features
            _features = await self._extract_features_from_data(data)
            
            # Cache features
            self.feature_cache[feature_id] = features
            
            _response = {
                "message_type": "feature_extraction_response",
                "feature_id": feature_id,
                "features": features,
            }
            
            if message.content.get("reply_to"):
                await self.send(
                    _topic = message.content["reply_to"],
                    _content = response,
                    _sender_id = self.agent_id,
                )
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error extracting features: {e}", exc_info=True)
    
    async def _extract_features_from_data(self, _data: Union[List, Dict]) -> Dict[str, Any]:
        """Extract features from data."""
        _features = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data_type": type(data).__name__,
        }
        
        if isinstance(data, list) and all(isinstance(x, (int, float)) for x in data):
            n = len(data)
            if n > 0:
                _mean = sum(data) / n
                features.update({
                    "count": n,
                    "mean": mean,
                    "min": min(data),
                    "max": max(data),
                    "sum": sum(data),
                })
                if n > 1:
                    _variance = sum((x - mean) ** 2 for x in data) / (n - 1)
                    features["variance"] = variance
                    features["std_dev"] = math.sqrt(variance)
        
        return features
    
    async def _handle_forecast_values(self, _message: ActorMessage) -> None:
        """
        Forecast future values.
        
        Args:
            message: Actor message with historical data
        """
        try:
            _data = message.content.get("data", [])
            _periods = message.content.get("periods", 5)
            
            logger.info(f"[{self.agent_id}] Forecasting {periods} periods")
            
            # Simple forecasting
            _forecast = await self._forecast_values(data, periods)
            
            _response = {
                "message_type": "forecast_response",
                "historical_count": len(data),
                "forecast_periods": periods,
                "forecast": forecast,
            }
            
            if message.content.get("reply_to"):
                await self.send(
                    _topic = message.content["reply_to"],
                    _content = response,
                    _sender_id = self.agent_id,
                )
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error forecasting: {e}", exc_info=True)
    
    async def _forecast_values(self, _data: List[float], _periods: int) -> List[Dict[str, Any]]:
        """Generate forecast values."""
        _forecast = []
        
        if len(data) >= 2:
            # Simple linear extrapolation
            n = len(data)
            _x_mean = (n - 1) / 2
            _y_mean = sum(data) / n
            
            _numerator = sum((i - x_mean) * (data[i] - y_mean) for i in range(n))
            _denominator = sum((i - x_mean) ** 2 for i in range(n))
            
            if denominator != 0:
                _slope = numerator / denominator
                _intercept = y_mean - slope * x_mean
                
                for i in range(periods):
                    _future_x = n + i
                    _predicted = slope * future_x + intercept
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
            _forecast = [{"error": "Insufficient data for forecasting"}]
        
        return forecast
    
    async def _handle_get_analytics_summary(self, _message: ActorMessage) -> None:
        """
        Get summary of all analytics.
        
        Args:
            message: Actor message
        """
        try:
            _summary = {
                "analyses_count": len(self.analysis_results),
                "trend_analyses_count": len(self.trend_analyses),
                "correlation_matrices_count": len(self.correlation_matrices),
                "feature_cache_count": len(self.feature_cache),
                "recent_analyses": [
                    r.to_dict() for r in list(self.analysis_results.values())[-5:]
                ],
            }
            
            _response = {
                "message_type": "analytics_summary_response",
                "summary": summary,
            }
            
            if message.content.get("reply_to"):
                await self.send(
                    _topic = message.content["reply_to"],
                    _content = response,
                    _sender_id = self.agent_id,
                )
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error getting analytics summary: {e}", exc_info=True)
    
    async def _handle_knowledge_enhanced_analysis(self, _message: ActorMessage) -> None:
        """
        Perform knowledge-enhanced analytics using the unified knowledge access layer.
        
        This handler combines data analysis with contextual knowledge from memory and RAG.
        
        Args:
            message: Actor message with data and query for context
        """
        try:
            _data = message.content.get("data", [])
            query = message.content.get("query")
            _sources = message.content.get("sources", ["memory", "rag"])
            _limit = message.content.get("limit", 10)
            _analysis_type = message.content.get("analysis_type", "descriptive")
            
            if not query:
                logger.error(f"[{self.agent_id}] Knowledge enhanced analysis requires query")
                return
            
            logger.info(f"[{self.agent_id}] Performing knowledge-enhanced analysis: {query[:50]}")
            
            # First, query knowledge base for context
            if self.knowledge_access:
                _knowledge_result = await self.knowledge_access.query(
                    _query = query,
                    _sources = sources,
                    _limit = limit,
                    _rerank = True,
                    _diversity_lambda = 0.5,
                )
                
                # Perform analysis on data
                _analysis_id = f"knowledge_analysis_{datetime.now(timezone.utc).timestamp()}"
                
                # Combine data analysis with knowledge context
                _result = {
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
                
                _response = {
                    "message_type": "knowledge_enhanced_analysis_response",
                    "result": result,
                }
                
                if message.content.get("reply_to"):
                    await self.send(
                        _topic = message.content["reply_to"],
                        _content = response,
                        _sender_id = self.agent_id,
                    )
            else:
                logger.warning(f"[{self.agent_id}] Knowledge access not initialized")
                
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error in knowledge enhanced analysis: {e}", exc_info=True)
    
    async def knowledge_enhanced_query(self, _query: str, _sources: Optional[List[str]], _limit: int, _rerank: bool) -> KnowledgeQueryResult:
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
            _query = query,
            _sources = sources or ["memory", "rag"],
            _limit = limit,
            _rerank = rerank,
        )
    
    async def _handle_signal_processing(self, _message: ActorMessage) -> None:
        """
        Process signals with noise reduction.
        
        Args:
            message: Actor message with signal data
        """
        try:
            _data = message.content.get("data", [])
            _method = message.content.get("method", "moving_average")
            _window = message.content.get("window", 3)
            
            logger.info(f"[{self.agent_id}] Processing signal with {method}")
            
            # Process signal
            _processed = self._process_signal(data, method, window)
            
            _response = {
                "message_type": "signal_processing_response",
                "method": method,
                "window": window,
                "original_length": len(data),
                "processed_length": len(processed),
                "processed_signal": processed,
            }
            
            if message.content.get("reply_to"):
                await self.send(
                    _topic = message.content["reply_to"],
                    _content = response,
                    _sender_id = self.agent_id,
                )
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error processing signal: {e}", exc_info=True)
    

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


    def _process_signal(self, _data: List[float], _method: str, _window: int) -> List[float]:
        """Process signal with specified method."""
        if method == "moving_average":
            _result = []
            for i in range(len(data) - window + 1):
                result.append(sum(data[i:i+window]) / window)
            return result
        elif method == "median_filter":
            _result = []
            for i in range(len(data) - window + 1):
                _sorted_window = sorted(data[i:i+window])
                result.append(sorted_window[window // 2])
            return result
        else:
            return data  # No processing
