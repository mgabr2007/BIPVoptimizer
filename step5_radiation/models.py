"""
Pydantic models for radiation analysis results and configuration.
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator, ConfigDict
from enum import Enum
from datetime import datetime
import pandas as pd


class PrecisionLevel(str, Enum):
    """Enumeration for radiation analysis precision levels."""
    HOURLY = "hourly"
    DAILY_PEAK = "daily_peak"
    MONTHLY_AVERAGE = "monthly_average"
    YEARLY_AVERAGE = "yearly_average"


class PrecisionPreset(BaseModel):
    """Configuration for radiation analysis precision."""
    level: PrecisionLevel
    calc_count: int = Field(..., description="Number of calculations per element")
    label: str = Field(..., description="Human-readable label")
    description: str = Field(..., description="Detailed description")
    time_samples: List[int] = Field(..., description="Hour samples for analysis")
    day_samples: List[int] = Field(..., description="Day samples for analysis")
    scaling_factor: float = Field(default=1.0, description="Factor to scale to annual values")
    
    model_config = ConfigDict(use_enum_values=True)


class ElementRadiationResult(BaseModel):
    """Radiation analysis result for a single building element."""
    element_id: str = Field(..., description="Unique element identifier")
    project_id: int = Field(..., description="Project identifier")
    orientation: str = Field(..., description="Element orientation")
    azimuth: float = Field(..., description="Azimuth angle in degrees")
    glass_area: float = Field(..., description="Glass area in square meters")
    annual_radiation: float = Field(..., description="Annual radiation in kWh/m²/year")
    peak_radiation: Optional[float] = Field(None, description="Peak radiation value")
    monthly_radiation: Optional[Dict[str, float]] = Field(None, description="Monthly radiation breakdown")
    shading_factor: float = Field(default=1.0, description="Applied shading factor")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    calculated_at: datetime = Field(default_factory=datetime.now)
    
    @validator('annual_radiation')
    def validate_radiation(cls, v):
        """Validate radiation values are reasonable."""
        if v < 0 or v > 3000:  # Reasonable range for annual radiation
            raise ValueError(f'Annual radiation {v} kWh/m²/year is outside expected range (0-3000)')
        return v


class ProjectRadiationSummary(BaseModel):
    """Summary of radiation analysis for entire project."""
    project_id: int
    total_elements: int = Field(..., description="Total number of elements analyzed")
    suitable_elements: int = Field(..., description="Number of PV-suitable elements")
    total_glass_area: float = Field(..., description="Total glass area in m²")
    avg_annual_radiation: float = Field(..., description="Average annual radiation")
    orientation_breakdown: Dict[str, int] = Field(..., description="Count by orientation")
    energy_breakdown: Dict[str, float] = Field(..., description="Energy potential by orientation")
    processing_stats: Dict[str, Any] = Field(..., description="Processing statistics")
    analysis_settings: Dict[str, Any] = Field(..., description="Analysis configuration used")
    completed_at: datetime = Field(default_factory=datetime.now)


class AnalysisProgress(BaseModel):
    """Real-time analysis progress tracking."""
    project_id: int
    total_elements: int
    completed_elements: int = 0
    current_element_id: Optional[str] = None
    current_orientation: Optional[str] = None
    current_area: Optional[float] = None
    estimated_completion: Optional[datetime] = None
    start_time: datetime = Field(default_factory=datetime.now)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_elements == 0:
            return 0.0
        return (self.completed_elements / self.total_elements) * 100
    
    @property
    def elapsed_time(self) -> float:
        """Calculate elapsed time in seconds."""
        return (datetime.now() - self.start_time).total_seconds()


class TMYData(BaseModel):
    """Typical Meteorological Year data structure."""
    project_id: int
    data_source: str = Field(..., description="Source of TMY data")
    location: Dict[str, Any] = Field(..., description="Location information")
    weather_data: Dict[str, List[float]] = Field(..., description="Hourly weather data")
    solar_data: Dict[str, List[float]] = Field(..., description="Solar irradiance data")
    quality_flags: Dict[str, Any] = Field(default_factory=dict, description="Data quality indicators")
    generated_at: datetime = Field(default_factory=datetime.now)
    
    @validator('weather_data')
    def validate_weather_data(cls, v):
        """Validate weather data completeness."""
        required_columns = ['temperature', 'humidity', 'pressure']
        for col in required_columns:
            if col not in v:
                raise ValueError(f'Required weather column {col} missing')
        return v
    
    @validator('solar_data')
    def validate_solar_data(cls, v):
        """Validate solar data completeness."""
        required_columns = ['GHI', 'DNI', 'DHI']
        for col in required_columns:
            if col not in v or len(v[col]) != 8760:  # Full year
                raise ValueError(f'Solar column {col} missing or incomplete (need 8760 hours)')
        return v


class WallShadingData(BaseModel):
    """Wall geometry data for self-shading calculations."""
    wall_id: str
    project_id: int
    wall_type: str
    orientation: str
    azimuth: float
    height: float
    length: float
    area: float
    level: str
    adjacent_windows: List[str] = Field(default_factory=list, description="Connected window element IDs")
    
    @validator('height')
    def validate_height(cls, v):
        """Validate wall height is reasonable."""
        if v <= 0 or v > 100:  # Reasonable building height
            raise ValueError(f'Wall height {v}m is unreasonable')
        return v


class AnalysisConfiguration(BaseModel):
    """Complete configuration for radiation analysis."""
    precision_preset: PrecisionPreset
    enable_self_shading: bool = True
    enable_environmental_shading: bool = True
    environmental_factors: Dict[str, float] = Field(
        default_factory=lambda: {"trees": 0.85, "buildings": 0.90}
    )
    parallel_processing: bool = True
    max_workers: int = Field(default=4, ge=1, le=16)
    chunk_size: int = Field(default=50, ge=1, le=500)
    timeout_seconds: int = Field(default=300, ge=30, le=3600)
    
    @validator('environmental_factors')
    def validate_factors(cls, v):
        """Validate environmental factors are between 0 and 1."""
        for factor_name, factor_value in v.items():
            if not 0 <= factor_value <= 1:
                raise ValueError(f'Environmental factor {factor_name} must be between 0 and 1')
        return v


class ValidationResult(BaseModel):
    """Result of data validation checks."""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    data_summary: Dict[str, Any] = Field(default_factory=dict)
    checked_at: datetime = Field(default_factory=datetime.now)


class DatabaseMetrics(BaseModel):
    """Database operation metrics and statistics."""
    operation: str
    table_name: str
    rows_affected: int
    execution_time: float
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# Precision preset configurations
PRECISION_PRESETS = {
    PrecisionLevel.HOURLY: PrecisionPreset(
        level=PrecisionLevel.HOURLY,
        calc_count=4015,
        label="Hourly Analysis",
        description="Complete hourly analysis for all daylight hours (365 days × 11 hours avg)",
        time_samples=list(range(6, 19)),  # 6 AM to 6 PM
        day_samples=list(range(1, 366)),  # All days
        scaling_factor=1.0
    ),
    PrecisionLevel.DAILY_PEAK: PrecisionPreset(
        level=PrecisionLevel.DAILY_PEAK,
        calc_count=365,
        label="Daily Peak Analysis",
        description="Daily peak solar analysis (noon for each day of year)",
        time_samples=[12],  # Noon only
        day_samples=list(range(1, 366)),  # All days
        scaling_factor=8.5  # Scale noon to daily average
    ),
    PrecisionLevel.MONTHLY_AVERAGE: PrecisionPreset(
        level=PrecisionLevel.MONTHLY_AVERAGE,
        calc_count=12,
        label="Monthly Average",
        description="Representative day analysis for each month",
        time_samples=[12],  # Noon only
        day_samples=[15, 46, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349],  # Mid-month days
        scaling_factor=8.5 * 30.4  # Scale to monthly average
    ),
    PrecisionLevel.YEARLY_AVERAGE: PrecisionPreset(
        level=PrecisionLevel.YEARLY_AVERAGE,
        calc_count=4,
        label="Yearly Average",
        description="Seasonal analysis (4 representative days)",
        time_samples=[12],  # Noon only
        day_samples=[80, 172, 266, 355],  # Spring, Summer, Fall, Winter equinox/solstice
        scaling_factor=8.5 * 91.25  # Scale to seasonal average
    )
}


def get_precision_preset(level: PrecisionLevel) -> PrecisionPreset:
    """Get precision preset configuration by level."""
    return PRECISION_PRESETS[level]


def detect_tmy_format(data: pd.DataFrame) -> Dict[str, str]:
    """Detect TMY data format and column mappings."""
    column_mappings = {}
    
    # Common column name variations
    ghi_variants = ['GHI', 'ghi', 'GHI_Wm2', 'global_horizontal_irradiance', 'global_irradiance']
    dni_variants = ['DNI', 'dni', 'DNI_Wm2', 'direct_normal_irradiance', 'direct_irradiance']
    dhi_variants = ['DHI', 'dhi', 'DHI_Wm2', 'diffuse_horizontal_irradiance', 'diffuse_irradiance']
    temp_variants = ['temperature', 'temp', 'dry_bulb_temperature', 'air_temperature']
    
    for col in data.columns:
        col_lower = col.lower()
        if any(variant.lower() in col_lower for variant in ghi_variants):
            column_mappings['GHI'] = col
        elif any(variant.lower() in col_lower for variant in dni_variants):
            column_mappings['DNI'] = col
        elif any(variant.lower() in col_lower for variant in dhi_variants):
            column_mappings['DHI'] = col
        elif any(variant.lower() in col_lower for variant in temp_variants):
            column_mappings['temperature'] = col
    
    return column_mappings


def validate_units(data: pd.DataFrame, column_mappings: Dict[str, str]) -> Dict[str, str]:
    """Detect and validate units in TMY data."""
    unit_suggestions = {}
    
    for standard_name, actual_col in column_mappings.items():
        if actual_col not in data.columns:
            continue
            
        values = data[actual_col].dropna()
        if len(values) == 0:
            continue
        
        max_val = values.max()
        
        if standard_name in ['GHI', 'DNI', 'DHI']:
            if max_val > 2000:  # Likely W/m²
                unit_suggestions[actual_col] = "Values appear to be in W/m², consider converting to kWh/m²"
            elif max_val < 10:  # Likely kW/m²
                unit_suggestions[actual_col] = "Values appear to be in kW/m², multiply by 1000 for W/m²"
        elif standard_name == 'temperature':
            if max_val > 100:  # Likely Kelvin
                unit_suggestions[actual_col] = "Temperature values appear to be in Kelvin, convert to Celsius"
    
    return unit_suggestions