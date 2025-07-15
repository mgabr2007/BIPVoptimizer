"""
Pydantic V2 compatible models for BIPV panel specification and analysis.
Fixed for production use with proper Pydantic V2 syntax.
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


class PanelSpecification(BaseModel):
    """BIPV panel specification model."""
    model_config = ConfigDict(validate_assignment=True, extra="allow")
    
    panel_id: str = Field(..., description="Unique panel identifier")
    manufacturer: str = Field(..., description="Panel manufacturer")
    model_name: str = Field(..., description="Panel model name")
    panel_type: PanelType = Field(..., description="Panel type classification")
    
    # Technical specifications
    efficiency: float = Field(..., ge=0.01, le=0.30, description="Panel efficiency (0.01-0.30)")
    transparency: float = Field(..., ge=0.0, le=1.0, description="Transparency factor (0.0-1.0)")
    power_density: float = Field(..., ge=10.0, le=300.0, description="Power density in W/m²")
    
    # Physical properties
    glass_thickness_mm: float = Field(default=5.0, ge=3.0, le=20.0, description="Glass thickness in mm")
    u_value: float = Field(default=1.5, ge=0.5, le=3.0, description="U-value in W/m²K")
    weight_kg_m2: float = Field(default=25.0, ge=10.0, le=50.0, description="Weight in kg/m²")
    
    # Economic data
    cost_per_m2: float = Field(..., ge=50.0, le=1000.0, description="Cost per m² in EUR")
    warranty_years: int = Field(default=25, ge=10, le=30, description="Warranty period in years")
    
    # Performance factors
    performance_ratio: float = Field(default=0.85, ge=0.7, le=0.95, description="System performance ratio")
    degradation_rate: float = Field(default=0.005, ge=0.003, le=0.01, description="Annual degradation rate")
    
    @field_validator('efficiency')
    @classmethod
    def validate_efficiency(cls, v):
        """Validate efficiency is realistic for BIPV."""
        if v < 0.02 or v > 0.25:
            raise ValueError(f'BIPV efficiency {v*100:.1f}% outside typical range (2-25%)')
        return v


class ElementPVSpecification(BaseModel):
    """PV specification for individual building element."""
    model_config = ConfigDict(validate_assignment=True, extra="allow")
    
    element_id: str = Field(..., description="Building element ID")
    project_id: int = Field(..., description="Project identifier")
    panel_id: str = Field(..., description="Selected panel ID")
    
    # Element data
    glass_area_m2: float = Field(..., description="Total glass area in m²")
    bipv_area_m2: float = Field(..., description="BIPV coverage area in m²")
    coverage_factor: float = Field(..., ge=0.5, le=1.0, description="Coverage factor")
    
    # Performance calculations
    capacity_kw: float = Field(..., description="System capacity in kW")
    annual_energy_kwh: float = Field(..., description="Annual energy production in kWh")
    specific_yield_kwh_kw: float = Field(..., description="Specific yield in kWh/kW")
    
    # Financial data
    total_cost_eur: float = Field(..., description="Total system cost in EUR")
    cost_per_kw: float = Field(..., description="Cost per kW in EUR/kW")
    
    # Technical details
    orientation: OrientationType = Field(..., description="Element orientation")
    annual_radiation_kwh_m2: float = Field(..., description="Annual radiation in kWh/m²")
    
    calculated_at: datetime = Field(default_factory=datetime.now)


class ProjectPVSummary(BaseModel):
    """Project-level PV system summary."""
    model_config = ConfigDict(validate_assignment=True, extra="allow")
    
    project_id: int = Field(..., description="Project identifier")
    total_elements: int = Field(..., description="Total building elements")
    suitable_elements: int = Field(..., description="PV suitable elements")
    
    # System totals
    total_capacity_kw: float = Field(..., description="Total system capacity in kW")
    total_annual_energy_kwh: float = Field(..., description="Total annual energy in kWh")
    total_cost_eur: float = Field(..., description="Total system cost in EUR")
    
    # Averages
    average_specific_yield: float = Field(..., description="Average specific yield kWh/kW")
    average_cost_per_kw: float = Field(..., description="Average cost per kW")
    
    # Coverage statistics
    total_glass_area_m2: float = Field(..., description="Total glass area in m²")
    total_bipv_area_m2: float = Field(..., description="Total BIPV area in m²")
    overall_coverage_factor: float = Field(..., description="Overall coverage factor")
    
    # Panel distribution
    panel_count_by_type: Dict[str, int] = Field(default_factory=dict, description="Panel count by type")
    capacity_by_orientation: Dict[str, float] = Field(default_factory=dict, description="Capacity by orientation")
    
    generated_at: datetime = Field(default_factory=datetime.now)


class SpecificationConfiguration(BaseModel):
    """Configuration for PV specification calculations."""
    model_config = ConfigDict(validate_assignment=True, extra="allow")
    
    # Global settings
    default_coverage_factor: float = Field(default=0.85, ge=0.6, le=0.95)
    default_performance_ratio: float = Field(default=0.85, ge=0.7, le=0.95)
    minimum_system_capacity: float = Field(default=0.5, ge=0.1, le=2.0, description="Minimum system kW")
    
    # Orientation preferences  
    orientation_weights: Dict[str, float] = Field(default_factory=lambda: {
        'South': 1.0,
        'Southeast': 0.95,
        'Southwest': 0.95,
        'East': 0.85,
        'West': 0.85,
        'North': 0.3
    })
    
    # Economic settings
    electricity_rate_eur_kwh: float = Field(default=0.30, ge=0.10, le=1.00)
    feed_in_tariff_eur_kwh: float = Field(default=0.08, ge=0.00, le=0.50)
    discount_rate: float = Field(default=0.05, ge=0.01, le=0.15)
    
    # Quality thresholds
    min_annual_radiation: float = Field(default=800, ge=500, le=1500, description="Minimum kWh/m²/year")
    max_cost_per_kw: float = Field(default=5000, ge=2000, le=10000, description="Maximum EUR/kW")