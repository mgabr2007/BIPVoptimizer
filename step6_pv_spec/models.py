"""
Pydantic models for BIPV panel specification and analysis.
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum
from datetime import datetime
from decimal import Decimal
import pandas as pd


class PanelType(str, Enum):
    """Enumeration for BIPV panel types."""
    OPAQUE = "opaque"
    SEMI_TRANSPARENT = "semi_transparent"


class OrientationType(str, Enum):
    """Building element orientation types."""
    NORTH = "North"
    NORTHEAST = "Northeast"
    EAST = "East"
    SOUTHEAST = "Southeast"
    SOUTH = "South"
    SOUTHWEST = "Southwest"
    WEST = "West"
    NORTHWEST = "Northwest"
    UNKNOWN = "Unknown"


class BuildingElement(BaseModel):
    """Building element data from Step 4 facade extraction."""
    model_config = ConfigDict(validate_assignment=True, extra="allow")
    
    element_id: str = Field(..., description="Unique element identifier")
    project_id: int = Field(..., description="Project identifier")
    orientation: OrientationType = Field(..., description="Element orientation")
    azimuth: float = Field(..., description="Azimuth angle in degrees")
    glass_area: float = Field(..., description="Glass area in square meters")
    building_level: Optional[str] = Field(None, description="Building level/floor")
    wall_element_id: Optional[str] = Field(None, description="Associated wall element ID")
    pv_suitable: bool = Field(default=True, description="PV suitability flag")
    
    @field_validator('glass_area')
    @classmethod
    def validate_glass_area(cls, v):
        """Validate glass area is positive."""
        if v <= 0:
            raise ValueError(f'Glass area must be positive, got {v}')
        return v
    
    @field_validator('azimuth')
    @classmethod
    def validate_azimuth(cls, v):
        """Validate azimuth is in valid range."""
        if not 0 <= v <= 360:
            raise ValueError(f'Azimuth must be between 0 and 360 degrees, got {v}')
        return v


class RadiationRecord(BaseModel):
    """Solar radiation data from Step 5 analysis."""
    model_config = ConfigDict(validate_assignment=True, extra="allow")
    
    element_id: str = Field(..., description="Unique element identifier")
    project_id: int = Field(..., description="Project identifier")
    annual_radiation: float = Field(..., description="Annual radiation in kWh/m²/year")
    monthly_radiation: Optional[Dict[str, float]] = Field(None, description="Monthly breakdown")
    shading_factor: float = Field(default=1.0, description="Applied shading factor")
    calculated_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator('annual_radiation')
    @classmethod
    def validate_radiation(cls, v):
        """Validate radiation values are reasonable."""
        if v < 0 or v > 3000:
            raise ValueError(f'Annual radiation {v} kWh/m²/year outside expected range (0-3000)')
        return v
    
    @field_validator('shading_factor')
    @classmethod
    def validate_shading_factor(cls, v):
        """Validate shading factor is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError(f'Shading factor must be between 0 and 1, got {v}')
        return v


class PanelSpecification(BaseModel):
    """BIPV panel specification from catalog."""
    id: Optional[int] = Field(None, description="Database ID")
    name: str = Field(..., description="Panel name/model")
    manufacturer: str = Field(..., description="Manufacturer name")
    panel_type: PanelType = Field(..., description="Panel type classification")
    efficiency: float = Field(..., description="Panel efficiency as decimal (0.08 = 8%)")
    transparency: float = Field(..., description="Glass transparency as decimal (0.35 = 35%)")
    power_density: float = Field(..., description="Power density in W/m²")
    cost_per_m2: float = Field(..., description="Cost per square meter in EUR")
    glass_thickness: float = Field(..., description="Glass thickness in mm")
    u_value: float = Field(..., description="Thermal transmittance in W/m²K")
    glass_weight: float = Field(..., description="Glass weight in kg/m²")
    performance_ratio: float = Field(default=0.85, description="System performance ratio")
    is_active: bool = Field(default=True, description="Active in catalog")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator('efficiency')
    @classmethod
    def validate_efficiency(cls, v):
        """Validate efficiency is reasonable."""
        if not 0.02 <= v <= 0.25:  # 2% to 25%
            raise ValueError(f'Efficiency {v} outside reasonable range (0.02-0.25)')
        return v
    
    @field_validator('transparency')
    @classmethod
    def validate_transparency(cls, v):
        """Validate transparency is between 0 and 1."""
        if not 0.0 <= v <= 0.65:  # 0% to 65%
            raise ValueError(f'Transparency {v} outside range (0.0-0.65)')
        return v
    
    @field_validator('cost_per_m2')
    @classmethod
    def validate_cost(cls, v):
        """Validate cost is reasonable."""
        if not 50.0 <= v <= 1000.0:
            raise ValueError(f'Cost per m² {v} outside reasonable range (50-1000 EUR)')
        return v
    
    @field_validator('power_density')
    @classmethod
    def validate_power_density(cls, v):
        """Validate power density is reasonable."""
        if not 10.0 <= v <= 250.0:
            raise ValueError(f'Power density {v} outside reasonable range (10-250 W/m²)')
        return v
    
    def efficiency_percent(self) -> float:
        """Get efficiency as percentage."""
        return self.efficiency * 100
    
    def transparency_percent(self) -> float:
        """Get transparency as percentage."""
        return self.transparency * 100


class ElementPVSpecification(BaseModel):
    """PV specification for individual building element."""
    id: Optional[int] = Field(None, description="Database ID")
    project_id: int = Field(..., description="Project identifier")
    element_id: str = Field(..., description="Building element ID")
    panel_spec_id: int = Field(..., description="Selected panel specification ID")
    glass_area: float = Field(..., description="Available glass area in m²")
    panel_coverage: float = Field(..., description="Panel coverage factor (0-1)")
    effective_area: float = Field(..., description="Effective panel area in m²")
    system_power: float = Field(..., description="System power in kW")
    annual_radiation: float = Field(..., description="Annual radiation kWh/m²/year")
    annual_energy: float = Field(..., description="Annual energy generation kWh/year")
    specific_yield: float = Field(..., description="Specific yield kWh/kW/year")
    total_cost: float = Field(..., description="Total system cost in EUR")
    cost_per_wp: float = Field(..., description="Cost per Wp in EUR")
    orientation: str = Field(..., description="Element orientation")
    created_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator('panel_coverage')
    @classmethod
    def validate_coverage(cls, v):
        """Validate coverage factor."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f'Panel coverage {v} must be between 0 and 1')
        return v
    
    @field_validator('effective_area', 'system_power', 'annual_energy')
    @classmethod
    def validate_positive_values(cls, v):
        """Validate values are positive."""
        if v < 0:
            raise ValueError(f'Value {v} must be non-negative')
        return v
    
    def power_per_m2(self) -> float:
        """Calculate power per square meter."""
        return (self.system_power * 1000) / self.glass_area if self.glass_area > 0 else 0


class ProjectPVSummary(BaseModel):
    """Summary of PV specifications for entire project."""
    project_id: int
    total_elements: int = Field(..., description="Total number of elements")
    suitable_elements: int = Field(..., description="PV-suitable elements")
    specified_elements: int = Field(..., description="Elements with PV specs")
    total_glass_area: float = Field(..., description="Total glass area in m²")
    total_effective_area: float = Field(..., description="Total effective panel area")
    total_system_power: float = Field(..., description="Total system power in kW")
    total_annual_energy: float = Field(..., description="Total annual energy in kWh")
    total_system_cost: float = Field(..., description="Total system cost in EUR")
    avg_specific_yield: float = Field(..., description="Average specific yield")
    avg_cost_per_wp: float = Field(..., description="Average cost per Wp")
    orientation_breakdown: Dict[str, int] = Field(..., description="Count by orientation")
    power_breakdown: Dict[str, float] = Field(..., description="Power by orientation")
    cost_breakdown: Dict[str, float] = Field(..., description="Cost by orientation")
    panel_type_distribution: Dict[str, int] = Field(..., description="Panel type usage")
    analysis_settings: Dict[str, Any] = Field(..., description="Analysis configuration")
    completed_at: datetime = Field(default_factory=datetime.now)


class SpecificationConfiguration(BaseModel):
    """Configuration for PV specification analysis."""
    default_coverage_factor: float = Field(default=0.85, description="Default panel coverage")
    min_coverage_factor: float = Field(default=0.60, description="Minimum coverage")
    max_coverage_factor: float = Field(default=0.95, description="Maximum coverage")
    default_performance_ratio: float = Field(default=0.85, description="Default performance ratio")
    min_system_size_kw: float = Field(default=0.1, description="Minimum system size")
    max_system_size_kw: float = Field(default=1000.0, description="Maximum system size")
    enable_custom_panels: bool = Field(default=True, description="Allow custom panel specs")
    filter_by_orientation: bool = Field(default=True, description="Filter unsuitable orientations")
    
    @field_validator('default_coverage_factor', 'min_coverage_factor', 'max_coverage_factor')
    @classmethod
    def validate_coverage_factors(cls, v):
        """Validate coverage factors are between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f'Coverage factor {v} must be between 0 and 1')
        return v


class ValidationResult(BaseModel):
    """Result of data validation."""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    element_count: int = 0
    radiation_count: int = 0
    validation_summary: Dict[str, Any] = Field(default_factory=dict)
    validated_at: datetime = Field(default_factory=datetime.now)


class CalculationMetrics(BaseModel):
    """Metrics for specification calculations."""
    total_elements: int
    processed_elements: int
    calculation_time: float
    memory_usage_mb: Optional[float] = None
    errors_encountered: int = 0
    warnings_generated: int = 0
    method_used: str = Field(default="vectorized")
    performance_notes: List[str] = Field(default_factory=list)


def validate_element_radiation_data(elements_df: pd.DataFrame, radiation_df: pd.DataFrame) -> ValidationResult:
    """Validate building elements and radiation data consistency."""
    errors = []
    warnings = []
    
    # Check if element IDs match
    element_ids = set(elements_df['element_id']) if 'element_id' in elements_df.columns else set()
    radiation_ids = set(radiation_df['element_id']) if 'element_id' in radiation_df.columns else set()
    
    missing_radiation = element_ids - radiation_ids
    if missing_radiation:
        warnings.append(f"Missing radiation data for {len(missing_radiation)} elements")
    
    missing_elements = radiation_ids - element_ids
    if missing_elements:
        warnings.append(f"Radiation data for {len(missing_elements)} elements without building data")
    
    # Check data types and ranges
    if 'glass_area' in elements_df.columns:
        invalid_areas = elements_df[elements_df['glass_area'] <= 0]
        if len(invalid_areas) > 0:
            errors.append(f"Found {len(invalid_areas)} elements with invalid glass areas")
    
    if 'annual_radiation' in radiation_df.columns:
        invalid_radiation = radiation_df[(radiation_df['annual_radiation'] < 0) | (radiation_df['annual_radiation'] > 3000)]
        if len(invalid_radiation) > 0:
            errors.append(f"Found {len(invalid_radiation)} elements with invalid radiation values")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        element_count=len(elements_df),
        radiation_count=len(radiation_df),
        validation_summary={
            'common_elements': len(element_ids & radiation_ids),
            'missing_radiation': len(missing_radiation),
            'missing_elements': len(missing_elements)
        }
    )


def detect_unit_anomalies(data: Dict[str, Any]) -> Dict[str, str]:
    """Detect unit anomalies in data and suggest conversions."""
    issues = {}
    
    # Check glass area (likely in cm² if very large)
    if 'glass_area' in data:
        areas = data['glass_area'] if isinstance(data['glass_area'], list) else [data['glass_area']]
        max_area = max(areas) if areas else 0
        if max_area > 1000:  # Likely cm²
            issues['glass_area'] = "Values appear to be in cm² - convert to m² by dividing by 10,000"
    
    # Check radiation (likely in MWh/m² if very small)
    if 'annual_radiation' in data:
        radiation = data['annual_radiation'] if isinstance(data['annual_radiation'], list) else [data['annual_radiation']]
        min_radiation = min(radiation) if radiation else 0
        if min_radiation < 10:  # Likely MWh/m²
            issues['annual_radiation'] = "Values appear to be in MWh/m² - convert to kWh/m² by multiplying by 1,000"
    
    # Check power density (likely in kW/m² if very small)
    if 'power_density' in data:
        power = data['power_density'] if isinstance(data['power_density'], list) else [data['power_density']]
        min_power = min(power) if power else 0
        if min_power < 1:  # Likely kW/m²
            issues['power_density'] = "Values appear to be in kW/m² - convert to W/m² by multiplying by 1,000"
    
    return issues