"""
Unit tests for radiation analysis models.
"""

import pytest
from datetime import datetime
from step5_radiation.models import (
    ElementRadiationResult, AnalysisProgress, PrecisionPreset,
    PrecisionLevel, TMYData, ValidationResult, get_precision_preset
)


class TestElementRadiationResult:
    """Test cases for ElementRadiationResult model."""
    
    def test_valid_element_result(self):
        """Test creating valid element radiation result."""
        result = ElementRadiationResult(
            element_id="W001",
            project_id=1,
            orientation="South",
            azimuth=180.0,
            glass_area=2.5,
            annual_radiation=1200.0
        )
        
        assert result.element_id == "W001"
        assert result.project_id == 1
        assert result.orientation == "South"
        assert result.annual_radiation == 1200.0
        assert result.shading_factor == 1.0  # Default value
    
    def test_invalid_radiation_value(self):
        """Test validation of radiation values."""
        with pytest.raises(ValueError, match="outside expected range"):
            ElementRadiationResult(
                element_id="W001",
                project_id=1,
                orientation="South",
                azimuth=180.0,
                glass_area=2.5,
                annual_radiation=5000.0  # Too high
            )
    
    def test_monthly_radiation_optional(self):
        """Test optional monthly radiation data."""
        monthly_data = {
            "January": 80.0,
            "February": 95.0,
            "March": 120.0
        }
        
        result = ElementRadiationResult(
            element_id="W001",
            project_id=1,
            orientation="South",
            azimuth=180.0,
            glass_area=2.5,
            annual_radiation=1200.0,
            monthly_radiation=monthly_data
        )
        
        assert result.monthly_radiation == monthly_data


class TestAnalysisProgress:
    """Test cases for AnalysisProgress model."""
    
    def test_progress_calculation(self):
        """Test progress percentage calculation."""
        progress = AnalysisProgress(
            project_id=1,
            total_elements=100,
            completed_elements=25
        )
        
        assert progress.progress_percentage == 25.0
    
    def test_zero_elements_progress(self):
        """Test progress with zero elements."""
        progress = AnalysisProgress(
            project_id=1,
            total_elements=0,
            completed_elements=0
        )
        
        assert progress.progress_percentage == 0.0
    
    def test_elapsed_time(self):
        """Test elapsed time calculation."""
        progress = AnalysisProgress(
            project_id=1,
            total_elements=100,
            completed_elements=25
        )
        
        # Should be very small elapsed time
        assert progress.elapsed_time >= 0.0
        assert progress.elapsed_time < 1.0  # Less than 1 second for immediate test


class TestPrecisionPreset:
    """Test cases for PrecisionPreset model."""
    
    def test_precision_preset_creation(self):
        """Test creating precision preset."""
        preset = PrecisionPreset(
            level=PrecisionLevel.DAILY_PEAK,
            calc_count=365,
            label="Daily Peak",
            description="Daily peak analysis",
            time_samples=[12],
            day_samples=list(range(1, 366)),
            scaling_factor=8.5
        )
        
        assert preset.level == PrecisionLevel.DAILY_PEAK
        assert preset.calc_count == 365
        assert preset.scaling_factor == 8.5
    
    def test_get_precision_preset(self):
        """Test getting predefined precision presets."""
        preset = get_precision_preset(PrecisionLevel.HOURLY)
        
        assert preset.level == PrecisionLevel.HOURLY
        assert preset.calc_count == 4015  # As defined in models
        assert len(preset.time_samples) > 1  # Multiple hours
        assert len(preset.day_samples) == 365  # All days


class TestTMYData:
    """Test cases for TMY data validation."""
    
    def test_valid_tmy_data(self):
        """Test creating valid TMY data."""
        weather_data = {
            'temperature': [20.0] * 8760,
            'humidity': [60.0] * 8760,
            'pressure': [101325.0] * 8760
        }
        
        solar_data = {
            'GHI': [500.0] * 8760,
            'DNI': [700.0] * 8760,
            'DHI': [200.0] * 8760
        }
        
        tmy = TMYData(
            project_id=1,
            data_source="Test TMY",
            location={"lat": 52.5, "lon": 13.4},
            weather_data=weather_data,
            solar_data=solar_data
        )
        
        assert tmy.project_id == 1
        assert len(tmy.weather_data['temperature']) == 8760
        assert len(tmy.solar_data['GHI']) == 8760
    
    def test_invalid_solar_data_length(self):
        """Test validation of solar data length."""
        weather_data = {
            'temperature': [20.0] * 8760,
            'humidity': [60.0] * 8760,
            'pressure': [101325.0] * 8760
        }
        
        # Incomplete solar data
        solar_data = {
            'GHI': [500.0] * 100,  # Too short
            'DNI': [700.0] * 8760,
            'DHI': [200.0] * 8760
        }
        
        with pytest.raises(ValueError, match="incomplete"):
            TMYData(
                project_id=1,
                data_source="Test TMY",
                location={"lat": 52.5, "lon": 13.4},
                weather_data=weather_data,
                solar_data=solar_data
            )
    
    def test_missing_required_columns(self):
        """Test validation of required columns."""
        weather_data = {
            'temperature': [20.0] * 8760,
            # Missing humidity and pressure
        }
        
        solar_data = {
            'GHI': [500.0] * 8760,
            'DNI': [700.0] * 8760,
            'DHI': [200.0] * 8760
        }
        
        with pytest.raises(ValueError, match="Required weather column"):
            TMYData(
                project_id=1,
                data_source="Test TMY",
                location={"lat": 52.5, "lon": 13.4},
                weather_data=weather_data,
                solar_data=solar_data
            )


class TestValidationResult:
    """Test cases for ValidationResult model."""
    
    def test_valid_result(self):
        """Test creating valid validation result."""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=["Minor issue"],
            data_summary={"count": 100}
        )
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert result.data_summary["count"] == 100
    
    def test_invalid_result(self):
        """Test creating invalid validation result."""
        result = ValidationResult(
            is_valid=False,
            errors=["Critical error", "Another error"],
            warnings=[],
            data_summary={}
        )
        
        assert result.is_valid is False
        assert len(result.errors) == 2
        assert len(result.warnings) == 0


@pytest.fixture
def sample_element_result():
    """Sample element radiation result for testing."""
    return ElementRadiationResult(
        element_id="W001",
        project_id=1,
        orientation="South",
        azimuth=180.0,
        glass_area=2.5,
        annual_radiation=1200.0,
        shading_factor=0.95
    )


@pytest.fixture
def sample_progress():
    """Sample analysis progress for testing."""
    return AnalysisProgress(
        project_id=1,
        total_elements=100,
        completed_elements=50,
        current_element_id="W025",
        current_orientation="East",
        current_area=3.0
    )


def test_model_serialization(sample_element_result):
    """Test model serialization to dict."""
    data = sample_element_result.dict()
    
    assert data["element_id"] == "W001"
    assert data["annual_radiation"] == 1200.0
    assert "calculated_at" in data


def test_model_json_serialization(sample_element_result):
    """Test model JSON serialization."""
    json_str = sample_element_result.json()
    
    assert "W001" in json_str
    assert "1200.0" in json_str