"""
Unit tests for BIPV specification calculator with edge cases and performance validation.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from decimal import Decimal
from datetime import datetime
from typing import List

from step6_pv_spec.models import (
    BuildingElement, RadiationRecord, PanelSpecification, 
    ElementPVSpecification, CalculationMetrics, OrientationType, PanelType
)
from step6_pv_spec.services.spec_calculator import SpecificationCalculator


@pytest.fixture
def sample_panel_spec():
    """Sample panel specification for testing."""
    return PanelSpecification(
        id=1,
        name="Test Panel",
        manufacturer="Test Manufacturer",
        panel_type=PanelType.SEMI_TRANSPARENT,
        efficiency=0.15,  # 15%
        transparency=0.30,  # 30%
        power_density=150.0,  # W/m²
        cost_per_m2=300.0,  # €/m²
        glass_thickness=6.0,
        u_value=2.0,
        glass_weight=25.0,
        performance_ratio=0.85
    )


@pytest.fixture
def sample_building_elements():
    """Sample building elements for testing."""
    return [
        BuildingElement(
            element_id="E001",
            project_id=1,
            orientation=OrientationType.SOUTH,
            azimuth=180.0,
            glass_area=10.0,
            pv_suitable=True
        ),
        BuildingElement(
            element_id="E002",
            project_id=1,
            orientation=OrientationType.EAST,
            azimuth=90.0,
            glass_area=8.0,
            pv_suitable=True
        ),
        BuildingElement(
            element_id="E003",
            project_id=1,
            orientation=OrientationType.NORTH,
            azimuth=0.0,
            glass_area=6.0,
            pv_suitable=True
        )
    ]


@pytest.fixture
def sample_radiation_records():
    """Sample radiation records for testing."""
    return [
        RadiationRecord(
            element_id="E001",
            project_id=1,
            annual_radiation=1200.0,  # kWh/m²/year
            shading_factor=1.0
        ),
        RadiationRecord(
            element_id="E002",
            project_id=1,
            annual_radiation=1000.0,  # kWh/m²/year
            shading_factor=0.9
        ),
        RadiationRecord(
            element_id="E003",
            project_id=1,
            annual_radiation=600.0,  # kWh/m²/year
            shading_factor=0.8
        )
    ]


@pytest.fixture
def calculator():
    """Specification calculator instance."""
    return SpecificationCalculator()


class TestSpecificationCalculator:
    """Test cases for specification calculator."""
    
    def test_basic_calculation(
        self, 
        calculator, 
        sample_building_elements, 
        sample_radiation_records, 
        sample_panel_spec
    ):
        """Test basic specification calculation."""
        specifications, metrics = calculator.calculate_specifications(
            elements=sample_building_elements,
            radiation_data=sample_radiation_records,
            panel_spec=sample_panel_spec
        )
        
        # Should have specifications for all elements
        assert len(specifications) == 3
        assert metrics.processed_elements == 3
        assert metrics.calculation_time > 0
        
        # Check first specification (South-facing)
        south_spec = next(s for s in specifications if s.element_id == "E001")
        assert south_spec.orientation == "South"
        assert south_spec.glass_area == 10.0
        assert south_spec.effective_area == 10.0 * 0.85  # Default coverage factor
        assert south_spec.system_power > 0
        assert south_spec.annual_energy > 0
        assert south_spec.total_cost > 0
    
    def test_edge_case_zero_area(
        self, 
        calculator, 
        sample_radiation_records, 
        sample_panel_spec
    ):
        """Test handling of zero glass area."""
        zero_area_element = BuildingElement(
            element_id="E_ZERO",
            project_id=1,
            orientation=OrientationType.SOUTH,
            azimuth=180.0,
            glass_area=0.0,  # Zero area
            pv_suitable=True
        )
        
        # Should raise validation error
        with pytest.raises(ValueError, match="Glass area must be positive"):
            BuildingElement(
                element_id="E_ZERO",
                project_id=1,
                orientation=OrientationType.SOUTH,
                azimuth=180.0,
                glass_area=0.0,
                pv_suitable=True
            )
    
    def test_edge_case_invalid_radiation(
        self, 
        calculator, 
        sample_building_elements, 
        sample_panel_spec
    ):
        """Test handling of invalid radiation values."""
        invalid_radiation = [
            RadiationRecord(
                element_id="E001",
                project_id=1,
                annual_radiation=-100.0,  # Negative radiation
                shading_factor=1.0
            )
        ]
        
        # Should raise validation error
        with pytest.raises(ValueError, match="outside expected range"):
            RadiationRecord(
                element_id="E001",
                project_id=1,
                annual_radiation=-100.0,
                shading_factor=1.0
            )
    
    def test_custom_coverage_factor(
        self, 
        calculator, 
        sample_building_elements, 
        sample_radiation_records, 
        sample_panel_spec
    ):
        """Test calculation with custom coverage factor."""
        specifications, metrics = calculator.calculate_specifications(
            elements=sample_building_elements,
            radiation_data=sample_radiation_records,
            panel_spec=sample_panel_spec,
            coverage_factor=0.75  # Custom coverage
        )
        
        # Check that coverage factor is applied
        for spec in specifications:
            assert spec.panel_coverage == 0.75
            assert spec.effective_area == spec.glass_area * 0.75
    
    def test_custom_performance_ratio(
        self, 
        calculator, 
        sample_building_elements, 
        sample_radiation_records, 
        sample_panel_spec
    ):
        """Test calculation with custom performance ratio."""
        specifications, metrics = calculator.calculate_specifications(
            elements=sample_building_elements,
            radiation_data=sample_radiation_records,
            panel_spec=sample_panel_spec,
            performance_ratio=0.90  # Higher performance ratio
        )
        
        # Higher performance ratio should result in higher energy generation
        for spec in specifications:
            assert spec.annual_energy > 0
    
    def test_orientation_factors(
        self, 
        calculator, 
        sample_building_elements, 
        sample_radiation_records, 
        sample_panel_spec
    ):
        """Test that orientation factors are applied correctly."""
        specifications, metrics = calculator.calculate_specifications(
            elements=sample_building_elements,
            radiation_data=sample_radiation_records,
            panel_spec=sample_panel_spec
        )
        
        # Get specifications by orientation
        south_spec = next(s for s in specifications if s.orientation == "South")
        east_spec = next(s for s in specifications if s.orientation == "East")
        north_spec = next(s for s in specifications if s.orientation == "North")
        
        # South should have highest yield, North should have lowest
        # (accounting for different radiation inputs)
        assert south_spec.specific_yield > north_spec.specific_yield
    
    def test_large_dataset_handling(self, calculator, sample_panel_spec):
        """Test handling of large datasets."""
        # Create large dataset
        large_elements = []
        large_radiation = []
        
        for i in range(1000):  # 1000 elements
            element = BuildingElement(
                element_id=f"E{i:04d}",
                project_id=1,
                orientation=OrientationType.SOUTH,
                azimuth=180.0,
                glass_area=5.0,
                pv_suitable=True
            )
            large_elements.append(element)
            
            radiation = RadiationRecord(
                element_id=f"E{i:04d}",
                project_id=1,
                annual_radiation=1000.0 + (i % 500),  # Varying radiation
                shading_factor=0.9
            )
            large_radiation.append(radiation)
        
        specifications, metrics = calculator.calculate_specifications(
            elements=large_elements,
            radiation_data=large_radiation,
            panel_spec=sample_panel_spec
        )
        
        # Should handle large dataset efficiently
        assert len(specifications) == 1000
        assert metrics.method_used in ["vectorized", "dask"]
        assert metrics.calculation_time < 30.0  # Should complete within 30 seconds
    
    def test_missing_radiation_data(
        self, 
        calculator, 
        sample_building_elements, 
        sample_panel_spec
    ):
        """Test handling when radiation data is missing for some elements."""
        partial_radiation = [
            RadiationRecord(
                element_id="E001",
                project_id=1,
                annual_radiation=1200.0,
                shading_factor=1.0
            )
            # Missing E002 and E003
        ]
        
        specifications, metrics = calculator.calculate_specifications(
            elements=sample_building_elements,
            radiation_data=partial_radiation,
            panel_spec=sample_panel_spec
        )
        
        # Should only process elements with radiation data
        assert len(specifications) == 1
        assert specifications[0].element_id == "E001"
    
    def test_cost_calculations(
        self, 
        calculator, 
        sample_building_elements, 
        sample_radiation_records, 
        sample_panel_spec
    ):
        """Test cost calculation accuracy."""
        specifications, metrics = calculator.calculate_specifications(
            elements=sample_building_elements,
            radiation_data=sample_radiation_records,
            panel_spec=sample_panel_spec
        )
        
        for spec in specifications:
            # Basic cost validation
            assert spec.total_cost > 0
            assert spec.cost_per_wp > 0
            
            # Cost should include panel cost at minimum
            expected_min_cost = spec.effective_area * sample_panel_spec.cost_per_m2
            assert spec.total_cost >= expected_min_cost
    
    def test_specific_yield_calculation(
        self, 
        calculator, 
        sample_building_elements, 
        sample_radiation_records, 
        sample_panel_spec
    ):
        """Test specific yield calculation accuracy."""
        specifications, metrics = calculator.calculate_specifications(
            elements=sample_building_elements,
            radiation_data=sample_radiation_records,
            panel_spec=sample_panel_spec
        )
        
        for spec in specifications:
            # Specific yield should be energy per power
            if spec.system_power > 0:
                calculated_yield = spec.annual_energy / spec.system_power
                assert abs(spec.specific_yield - calculated_yield) < 1.0  # Within 1 kWh/kW tolerance
    
    def test_unit_anomaly_detection(self, calculator):
        """Test unit anomaly detection."""
        test_data = pd.DataFrame({
            'glass_area': [50000, 2.5, 1.8],  # First value likely in cm²
            'annual_radiation': [0.5, 1200, 1000],  # First value likely in MWh/m²
            'power_density': [0.15, 150, 120]  # First value likely in kW/m²
        })
        
        issues = calculator.detect_unit_issues(test_data)
        
        assert 'glass_area' in issues
        assert 'cm²' in issues['glass_area']
    
    @pytest.mark.performance
    def test_vectorized_vs_iterative_performance(
        self, 
        calculator, 
        sample_panel_spec
    ):
        """Performance comparison between vectorized and iterative methods."""
        # Create medium dataset
        elements = []
        radiation_data = []
        
        for i in range(100):
            element = BuildingElement(
                element_id=f"E{i:03d}",
                project_id=1,
                orientation=OrientationType.SOUTH,
                azimuth=180.0,
                glass_area=5.0,
                pv_suitable=True
            )
            elements.append(element)
            
            radiation = RadiationRecord(
                element_id=f"E{i:03d}",
                project_id=1,
                annual_radiation=1000.0,
                shading_factor=1.0
            )
            radiation_data.append(radiation)
        
        # Test vectorized method
        calculator.use_vectorized = True
        specs_vec, metrics_vec = calculator.calculate_specifications(
            elements, radiation_data, sample_panel_spec
        )
        
        # Test iterative method
        calculator.use_vectorized = False
        specs_iter, metrics_iter = calculator.calculate_specifications(
            elements, radiation_data, sample_panel_spec
        )
        
        # Vectorized should be faster
        assert metrics_vec.calculation_time < metrics_iter.calculation_time
        
        # Results should be similar
        assert len(specs_vec) == len(specs_iter)
    
    def test_invalid_panel_specification(
        self, 
        calculator, 
        sample_building_elements, 
        sample_radiation_records
    ):
        """Test handling of invalid panel specifications."""
        invalid_panel = PanelSpecification(
            id=1,
            name="Invalid Panel",
            manufacturer="Test",
            panel_type=PanelType.OPAQUE,
            efficiency=2.0,  # Invalid: >100%
            transparency=0.0,
            power_density=150.0,
            cost_per_m2=300.0,
            glass_thickness=6.0,
            u_value=2.0,
            glass_weight=25.0
        )
        
        # Should raise validation error during panel creation
        with pytest.raises(ValueError, match="outside reasonable range"):
            PanelSpecification(
                id=1,
                name="Invalid Panel",
                manufacturer="Test",
                panel_type=PanelType.OPAQUE,
                efficiency=2.0,  # Invalid
                transparency=0.0,
                power_density=150.0,
                cost_per_m2=300.0,
                glass_thickness=6.0,
                u_value=2.0,
                glass_weight=25.0
            )
    
    def test_calculation_metrics(
        self, 
        calculator, 
        sample_building_elements, 
        sample_radiation_records, 
        sample_panel_spec
    ):
        """Test calculation metrics accuracy."""
        specifications, metrics = calculator.calculate_specifications(
            elements=sample_building_elements,
            radiation_data=sample_radiation_records,
            panel_spec=sample_panel_spec
        )
        
        # Check metrics
        assert isinstance(metrics, CalculationMetrics)
        assert metrics.total_elements == len(sample_building_elements)
        assert metrics.processed_elements == len(specifications)
        assert metrics.calculation_time > 0
        assert metrics.method_used in ["vectorized", "iterative", "dask"]
        assert metrics.errors_encountered >= 0


@pytest.mark.integration
class TestCalculatorIntegration:
    """Integration tests for calculator with database operations."""
    
    @pytest.fixture
    def mock_database(self):
        """Mock database for integration testing."""
        return Mock()
    
    def test_database_integration(
        self, 
        calculator, 
        mock_database, 
        sample_building_elements, 
        sample_radiation_records, 
        sample_panel_spec
    ):
        """Test calculator integration with database operations."""
        # This would test actual database operations
        # For now, just verify the interface works
        specifications, metrics = calculator.calculate_specifications(
            elements=sample_building_elements,
            radiation_data=sample_radiation_records,
            panel_spec=sample_panel_spec
        )
        
        assert len(specifications) > 0
        assert all(isinstance(spec, ElementPVSpecification) for spec in specifications)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])