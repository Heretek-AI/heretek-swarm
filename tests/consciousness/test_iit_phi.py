"""
IIT Phi Calculation Tests.

Test suite for the Integrated Information Theory (IIT) Phi calculation module.
Tests cover:
- Unit tests for each calculation method
- Integration tests with consciousness metrics plugin
- Validation against known Phi values from IIT literature
- Zero-trust input validation

Author: Heretek Swarm Collective
Date: 2026-04-07
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any, List

from heretek_swarm.consciousness.iit_phi import (
    PhiCalculator,
    PhiResult,
    CauseEffectStructure,
    SystemPartition,
)
from heretek_swarm.plugins.consciousness_metrics import (
    ConsciousnessMetricsCalculator,
    CausalAnalysis,
)


class TestPhiCalculatorInitialization:
    """Test PhiCalculator initialization and configuration."""
    
    def test_init_default(self):
        """Test default initialization."""
        calculator = PhiCalculator()
        assert calculator._calculation_count == 0
        assert len(calculator._cache) == 0
        assert calculator._last_calculation_time is None
    
    def test_init_strict_validation(self):
        """Test initialization with strict validation."""
        calculator = PhiCalculator(strict_validation=True)
        assert calculator._validator.strict_mode is True
    
    def test_init_non_strict_validation(self):
        """Test initialization with non-strict validation."""
        calculator = PhiCalculator(strict_validation=False)
        assert calculator._validator.strict_mode is False
    
    def test_get_statistics_empty(self):
        """Test statistics when no calculations performed."""
        calculator = PhiCalculator()
        stats = calculator.get_statistics()
        assert stats["calculation_count"] == 0
        assert stats["cache_size"] == 0
        assert stats["last_calculation_time"] is None


class TestCalculatePhi:
    """Test main Phi calculation method."""
    
    def test_calculate_phi_empty_system(self):
        """Test Phi calculation for empty system."""
        calculator = PhiCalculator()
        result = calculator.calculate_phi({
            "system_id": "empty_system",
            "elements": [],
            "connectivity": {},
            "current_state": {},
        })
        assert isinstance(result, PhiResult)
        assert result.phi == 0.0
        assert result.phi_max == 0.0
    
    def test_calculate_phi_single_element(self):
        """Test Phi calculation for single element system."""
        calculator = PhiCalculator()
        result = calculator.calculate_phi({
            "system_id": "single_element",
            "elements": ["A"],
            "connectivity": {"A": {}},
            "current_state": {"A": 1.0},
        })
        assert isinstance(result, PhiResult)
        assert result.phi >= 0.0
        assert result.phi <= 1.0
    
    def test_calculate_phi_two_elements(self):
        """Test Phi calculation for two element system."""
        calculator = PhiCalculator()
        result = calculator.calculate_phi({
            "system_id": "two_elements",
            "elements": ["A", "B"],
            "connectivity": {
                "A": {"B": 0.8},
                "B": {"A": 0.7},
            },
            "current_state": {"A": 1.0, "B": 0.5},
        })
        assert isinstance(result, PhiResult)
        assert result.phi >= 0.0
        assert result.phi <= 1.0
        assert result.mip is not None
    
    def test_calculate_phi_fully_connected(self):
        """Test Phi calculation for fully connected system."""
        calculator = PhiCalculator()
        # 3-element fully connected system
        result = calculator.calculate_phi({
            "system_id": "fully_connected",
            "elements": ["A", "B", "C"],
            "connectivity": {
                "A": {"B": 0.9, "C": 0.8},
                "B": {"A": 0.9, "C": 0.8},
                "C": {"A": 0.8, "B": 0.9},
            },
            "current_state": {"A": 1.0, "B": 1.0, "C": 1.0},
        })
        assert isinstance(result, PhiResult)
        assert result.phi >= 0.0
        assert result.phi <= 1.0
        assert result.integration_level in [
            "minimal", "low", "moderate", "high", "very_high"
        ]
    
    def test_calculate_phi_disconnected(self):
        """Test Phi calculation for disconnected system."""
        calculator = PhiCalculator()
        result = calculator.calculate_phi({
            "system_id": "disconnected",
            "elements": ["A", "B", "C"],
            "connectivity": {
                "A": {},
                "B": {},
                "C": {},
            },
            "current_state": {"A": 1.0, "B": 0.0, "C": 0.5},
        })
        assert isinstance(result, PhiResult)
        # Disconnected system should have minimal phi
        assert result.phi <= 0.3
        assert result.integration_level == "minimal"
    
    def test_calculate_phi_auto_system_id(self):
        """Test that system_id is auto-generated if not provided."""
        calculator = PhiCalculator()
        result = calculator.calculate_phi({
            "elements": ["A", "B"],
            "connectivity": {
                "A": {"B": 0.5},
                "B": {"A": 0.5},
            },
            "current_state": {"A": 1.0, "B": 0.0},
        })
        assert result.system_id is not None
        assert len(result.system_id) > 0
    
    def test_calculate_phi_caching(self):
        """Test that results are cached."""
        calculator = PhiCalculator()
        system_id = "cache_test"
        
        result1 = calculator.calculate_phi({
            "system_id": system_id,
            "elements": ["A", "B"],
            "connectivity": {
                "A": {"B": 0.5},
                "B": {"A": 0.5},
            },
            "current_state": {"A": 1.0, "B": 0.0},
        })
        
        cached_result = calculator.get_cached_result(system_id)
        assert cached_result is not None
        assert cached_result.phi == result1.phi
    
    def test_calculate_phi_clear_cache(self):
        """Test cache clearing."""
        calculator = PhiCalculator()
        
        calculator.calculate_phi({
            "system_id": "cache_test",
            "elements": ["A"],
            "connectivity": {},
            "current_state": {"A": 1.0},
        })
        
        assert len(calculator._cache) > 0
        calculator.clear_cache()
        assert len(calculator._cache) == 0


class TestCalculateMIP:
    """Test Minimum Information Partition calculation."""
    
    def test_find_mip_single_element(self):
        """Test MIP for single element system."""
        calculator = PhiCalculator()
        mip = calculator.find_mip({
            "elements": ["A"],
            "connectivity": {},
            "current_state": {"A": 1.0},
        })
        assert isinstance(mip, SystemPartition)
        assert len(mip.parts) == 1
        assert mip.is_mip is True
    
    def test_find_mip_two_elements(self):
        """Test MIP for two element system."""
        calculator = PhiCalculator()
        mip = calculator.find_mip({
            "elements": ["A", "B"],
            "connectivity": {
                "A": {"B": 0.8},
                "B": {"A": 0.7},
            },
            "current_state": {"A": 1.0, "B": 0.5},
        })
        assert isinstance(mip, SystemPartition)
        assert mip.is_mip is True
        assert mip.information_loss >= 0.0
        assert mip.information_loss <= 1.0
    
    def test_find_mip_asymmetric(self):
        """Test MIP for asymmetric connectivity."""
        calculator = PhiCalculator()
        mip = calculator.find_mip({
            "elements": ["A", "B", "C"],
            "connectivity": {
                "A": {"B": 0.9, "C": 0.1},
                "B": {"A": 0.9, "C": 0.1},
                "C": {"A": 0.1, "B": 0.1},
            },
            "current_state": {"A": 1.0, "B": 1.0, "C": 0.0},
        })
        assert isinstance(mip, SystemPartition)
        assert mip.is_mip is True
        # C should be separated from A-B cluster
        assert len(mip.parts) == 2
    
    def test_calculate_mip_public_method(self):
        """Test public calculate_mip method."""
        calculator = PhiCalculator()
        mip = calculator.calculate_mip({
            "elements": ["A", "B"],
            "connectivity": {
                "A": {"B": 0.5},
                "B": {"A": 0.5},
            },
            "current_state": {"A": 1.0, "B": 0.0},
        })
        assert isinstance(mip, SystemPartition)
        assert mip.is_mip is True


class TestCauseEffectInformation:
    """Test cause and effect information calculations."""
    
    def test_calculate_cause_info_empty(self):
        """Test cause info with empty state."""
        calculator = PhiCalculator()
        cause_info = calculator.calculate_cause_info(
            state={"repertoire": {}, "element": "A"},
            element="A",
        )
        assert cause_info == 0.0
    
    def test_calculate_cause_info_uniform(self):
        """Test cause info with uniform distribution."""
        calculator = PhiCalculator()
        # Uniform distribution = maximum entropy = minimum information
        cause_info = calculator.calculate_cause_info(
            state={
                "repertoire": {"A": 0.5, "B": 0.5},
                "element": "A",
            },
            element="A",
        )
        assert cause_info >= 0.0
        assert cause_info <= 1.0
    
    def test_calculate_cause_info_peaked(self):
        """Test cause info with peaked distribution."""
        calculator = PhiCalculator()
        # Peaked distribution = low entropy = high information
        cause_info = calculator.calculate_cause_info(
            state={
                "repertoire": {"A": 0.99, "B": 0.01},
                "element": "A",
            },
            element="A",
        )
        assert cause_info > 0.5  # Should be high information
    
    def test_calculate_effect_info_empty(self):
        """Test effect info with empty state."""
        calculator = PhiCalculator()
        effect_info = calculator.calculate_effect_info(
            state={"repertoire": {}, "element": "A"},
            element="A",
        )
        assert effect_info == 0.0
    
    def test_calculate_effect_info_uniform(self):
        """Test effect info with uniform distribution."""
        calculator = PhiCalculator()
        effect_info = calculator.calculate_effect_info(
            state={
                "repertoire": {"A": 0.5, "B": 0.5},
                "element": "A",
            },
            element="A",
        )
        assert effect_info >= 0.0
        assert effect_info <= 1.0
    
    def test_cause_effect_phi_total(self):
        """Test that phi_total is minimum of cause and effect."""
        calculator = PhiCalculator()
        ces = calculator._calculate_element_cause_effect(
            element="A",
            elements=["A", "B"],
            connectivity={
                "A": {"B": 0.8},
                "B": {"A": 0.7},
            },
            current_state={"A": 1.0, "B": 0.5},
        )
        assert ces.phi_total == min(ces.phi_cause, ces.phi_effect)


class TestInputValidation:
    """Test zero-trust input validation."""
    
    def test_validate_non_dict_input(self):
        """Test validation rejects non-dict input."""
        calculator = PhiCalculator()
        with pytest.raises(ValueError):
            calculator.calculate_phi("not a dict")  # type: ignore
    
    def test_validate_invalid_elements(self):
        """Test validation rejects invalid elements list."""
        calculator = PhiCalculator()
        with pytest.raises(ValueError):
            calculator.calculate_phi({
                "elements": "not a list",  # type: ignore
                "connectivity": {},
                "current_state": {},
            })
    
    def test_validate_invalid_connectivity(self):
        """Test validation rejects invalid connectivity."""
        calculator = PhiCalculator()
        with pytest.raises(ValueError):
            calculator.calculate_phi({
                "elements": ["A", "B"],
                "connectivity": "not a dict",  # type: ignore
                "current_state": {},
            })
    
    def test_validate_connection_weight_range(self):
        """Test validation warns about weights outside [0,1]."""
        calculator = PhiCalculator()
        result = calculator.calculate_phi({
            "elements": ["A", "B"],
            "connectivity": {
                "A": {"B": 1.5},  # Weight > 1
                "B": {"A": -0.5},  # Weight < 0
            },
            "current_state": {"A": 1.0, "B": 0.0},
        })
        # Should still calculate but with warnings
        assert isinstance(result, PhiResult)
    
    def test_validate_numeric_weights(self):
        """Test validation rejects non-numeric weights."""
        calculator = PhiCalculator()
        with pytest.raises(ValueError):
            calculator.calculate_phi({
                "elements": ["A", "B"],
                "connectivity": {
                    "A": {"B": "not a number"},  # type: ignore
                },
                "current_state": {},
            })


class TestIntegrationLevels:
    """Test integration and differentiation level determination."""
    
    def test_integration_level_minimal(self):
        """Test minimal integration level."""
        calculator = PhiCalculator()
        level = calculator._determine_integration_level(
            connectivity={"A": {}, "B": {}},
            elements=["A", "B"],
        )
        assert level == "minimal"
    
    def test_integration_level_very_high(self):
        """Test very high integration level."""
        calculator = PhiCalculator()
        level = calculator._determine_integration_level(
            connectivity={
                "A": {"B": 0.95, "C": 0.95},
                "B": {"A": 0.95, "C": 0.95},
                "C": {"A": 0.95, "B": 0.95},
            },
            elements=["A", "B", "C"],
        )
        assert level in ["high", "very_high"]
    
    def test_differentiation_level_minimal(self):
        """Test minimal differentiation level."""
        calculator = PhiCalculator()
        level = calculator._determine_differentiation_level(
            current_state={"A": 1.0, "B": 1.0, "C": 1.0},
            elements=["A", "B", "C"],
        )
        assert level == "minimal"  # All same state
    
    def test_differentiation_level_high(self):
        """Test high differentiation level."""
        calculator = PhiCalculator()
        level = calculator._determine_differentiation_level(
            current_state={"A": 0.0, "B": 0.5, "C": 1.0},
            elements=["A", "B", "C"],
        )
        assert level in ["moderate", "high", "very_high"]


class TestPhiResultNormalization:
    """Test Phi value normalization."""
    
    def test_normalize_phi_single_element(self):
        """Test normalization for single element."""
        calculator = PhiCalculator()
        normalized = calculator._normalize_phi(0.5, 1)
        assert normalized >= 0.0
        assert normalized <= 1.0
    
    def test_normalize_phi_large_system(self):
        """Test normalization for large system."""
        calculator = PhiCalculator()
        # Large raw phi should be normalized down
        normalized = calculator._normalize_phi(10.0, 100)
        assert normalized >= 0.0
        assert normalized <= 1.0
    
    def test_normalize_phi_bounds(self):
        """Test that normalization respects bounds."""
        calculator = PhiCalculator()
        assert calculator._normalize_phi(-1.0, 5) >= 0.0
        assert calculator._normalize_phi(100.0, 5) <= 1.0


class TestConsciousnessMetricsIntegration:
    """Test integration with consciousness_metrics plugin."""
    
    def test_calculator_uses_phi_calculator(self):
        """Test that ConsciousnessMetricsCalculator uses PhiCalculator."""
        metrics_calc = ConsciousnessMetricsCalculator()
        # Internal phi_calculator should exist
        assert hasattr(metrics_calc, "_phi_calculator")
        assert isinstance(metrics_calc._phi_calculator, PhiCalculator)
    
    def test_calculate_phi_integration(self):
        """Test Phi calculation through metrics calculator."""
        metrics_calc = ConsciousnessMetricsCalculator()
        
        connectivity = [
            [0.0, 0.8, 0.6],
            [0.7, 0.0, 0.9],
            [0.6, 0.7, 0.0],
        ]
        
        result = metrics_calc.calculate_phi(connectivity)
        assert isinstance(result, CausalAnalysis)
        assert result.integrated_info >= 0.0
        assert result.integrated_info <= 1.0
    
    def test_calculate_phi_with_state_vector(self):
        """Test Phi calculation with state vector."""
        metrics_calc = ConsciousnessMetricsCalculator()
        
        connectivity = [
            [0.0, 0.8],
            [0.7, 0.0],
        ]
        state_vector = [1.0, 0.5]
        
        result = metrics_calc.calculate_phi(connectivity, state_vector)
        assert isinstance(result, CausalAnalysis)


class TestKnownPhiValues:
    """Test against known Phi values from IIT literature."""
    
    def test_phi_major_complex_should_be_positive(self):
        """Test that a complex system has positive Phi."""
        calculator = PhiCalculator()
        result = calculator.calculate_phi({
            "system_id": "major_complex",
            "elements": ["A", "B", "C", "D"],
            "connectivity": {
                "A": {"B": 0.8, "C": 0.6},
                "B": {"A": 0.8, "D": 0.7},
                "C": {"A": 0.6, "D": 0.8},
                "D": {"B": 0.7, "C": 0.8},
            },
            "current_state": {"A": 1.0, "B": 0.8, "C": 0.6, "D": 0.9},
        })
        # Complex integrated system should have Phi > 0
        assert result.phi > 0.0
    
    def test_phi_disconnected_should_be_near_zero(self):
        """Test that disconnected system has near-zero Phi."""
        calculator = PhiCalculator()
        result = calculator.calculate_phi({
            "system_id": "disconnected",
            "elements": ["A", "B", "C"],
            "connectivity": {},
            "current_state": {"A": 1.0, "B": 0.0, "C": 0.5},
        })
        # Disconnected system should have minimal Phi
        assert result.phi < 0.2
    
    def test_phi_feedforward_chain(self):
        """Test Phi for feedforward chain (should be low)."""
        calculator = PhiCalculator()
        # Feedforward chain: A -> B -> C (no feedback)
        result = calculator.calculate_phi({
            "system_id": "feedforward",
            "elements": ["A", "B", "C"],
            "connectivity": {
                "A": {"B": 1.0},
                "B": {"C": 1.0},
                "C": {},
            },
            "current_state": {"A": 1.0, "B": 1.0, "C": 1.0},
        })
        # Feedforward systems have low integration
        assert result.phi < 0.5


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_self_connections_ignored(self):
        """Test that self-connections are handled."""
        calculator = PhiCalculator()
        result = calculator.calculate_phi({
            "system_id": "self_conn",
            "elements": ["A", "B"],
            "connectivity": {
                "A": {"A": 1.0, "B": 0.5},  # Self-connection
                "B": {"B": 1.0, "A": 0.5},
            },
            "current_state": {"A": 1.0, "B": 0.0},
        })
        assert isinstance(result, PhiResult)
    
    def test_sparse_connectivity(self):
        """Test sparse connectivity."""
        calculator = PhiCalculator()
        result = calculator.calculate_phi({
            "system_id": "sparse",
            "elements": ["A", "B", "C", "D", "E"],
            "connectivity": {
                "A": {"B": 0.9},
                "B": {"A": 0.9},
                "C": {"D": 0.9},
                "D": {"C": 0.9},
                "E": {},
            },
            "current_state": {"A": 1.0, "B": 0.0, "C": 1.0, "D": 0.0, "E": 0.5},
        })
        assert isinstance(result, PhiResult)
        # Should have multiple partitions
        assert result.mip is not None
    
    def test_zero_weights(self):
        """Test all-zero connectivity."""
        calculator = PhiCalculator()
        result = calculator.calculate_phi({
            "system_id": "zero_weights",
            "elements": ["A", "B", "C"],
            "connectivity": {
                "A": {"B": 0.0, "C": 0.0},
                "B": {"A": 0.0, "C": 0.0},
                "C": {"A": 0.0, "B": 0.0},
            },
            "current_state": {"A": 1.0, "B": 0.0, "C": 0.5},
        })
        assert result.phi == 0.0 or result.phi < 0.1


class TestAuditLogging:
    """Test audit logging for Phi calculations."""
    
    def test_statistics_tracking(self):
        """Test that calculation statistics are tracked."""
        calculator = PhiCalculator()
        
        # Initial stats
        stats = calculator.get_statistics()
        assert stats["calculation_count"] == 0
        
        # After calculation
        calculator.calculate_phi({
            "system_id": "stats_test",
            "elements": ["A", "B"],
            "connectivity": {
                "A": {"B": 0.5},
                "B": {"A": 0.5},
            },
            "current_state": {"A": 1.0, "B": 0.0},
        })
        
        stats = calculator.get_statistics()
        assert stats["calculation_count"] == 1
        assert stats["cache_size"] == 1
        assert stats["last_calculation_time"] is not None
    
    def test_cache_tracking(self):
        """Test that cache is properly tracked."""
        calculator = PhiCalculator()
        
        # Multiple calculations
        calculator.calculate_phi({
            "system_id": "cache_1",
            "elements": ["A"],
            "connectivity": {},
            "current_state": {"A": 1.0},
        })
        calculator.calculate_phi({
            "system_id": "cache_2",
            "elements": ["B"],
            "connectivity": {},
            "current_state": {"B": 1.0},
        })
        
        stats = calculator.get_statistics()
        assert stats["cache_size"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src/heretek_swarm/consciousness/iit_phi", "--cov-report=term-missing"])
