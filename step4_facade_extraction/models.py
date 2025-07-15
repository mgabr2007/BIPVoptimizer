"""
Data models for facade extraction using Pydantic for validation and type safety.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
import pandas as pd
from datetime import datetime


class OrientationType(str, Enum):
    """Enumeration for building element orientations."""
    NORTH = "North"
    SOUTH = "South"
    EAST = "East"
    WEST = "West"
    NORTHEAST = "Northeast"
    NORTHWEST = "Northwest"
    SOUTHEAST = "Southeast"
    SOUTHWEST = "Southwest"
    UNKNOWN = "Unknown"


class WindowRecord(BaseModel):
    """Model for window/glazing building elements."""
    element_id: str = Field(..., description="Unique element identifier from BIM")
    family: str = Field(..., description="Window family/type name")
    element_type: str = Field(default="Window", description="Element type classification")
    glass_area: float = Field(..., ge=0, description="Glass area in square meters")
    window_width: Optional[float] = Field(None, ge=0, description="Window width in meters")
    window_height: Optional[float] = Field(None, ge=0, description="Window height in meters")
    building_level: Optional[str] = Field(None, description="Building level/floor")
    wall_element_id: Optional[str] = Field(None, description="Host wall element ID")
    azimuth: float = Field(..., ge=0, lt=360, description="Azimuth angle in degrees (0-360)")
    orientation: OrientationType = Field(..., description="Cardinal orientation")
    pv_suitable: bool = Field(default=False, description="Suitable for PV installation")
    project_id: int = Field(..., description="Associated project ID")
    created_at: Optional[datetime] = Field(default_factory=datetime.now)

    @validator('azimuth')
    def validate_azimuth(cls, v):
        """Ensure azimuth is within valid range."""
        if not 0 <= v < 360:
            raise ValueError('Azimuth must be between 0 and 360 degrees')
        return v

    @validator('glass_area')
    def validate_glass_area(cls, v):
        """Validate glass area is reasonable."""
        if v > 100:  # Unreasonably large window
            raise ValueError('Glass area seems too large (>100 m²)')
        return v

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True


class WallRecord(BaseModel):
    """Model for wall building elements."""
    element_id: str = Field(..., description="Unique wall element identifier")
    wall_type: str = Field(..., description="Wall type/family name")
    building_level: Optional[str] = Field(None, description="Building level/floor")
    length: float = Field(..., gt=0, description="Wall length in meters")
    area: float = Field(..., gt=0, description="Wall area in square meters")
    azimuth: float = Field(..., ge=0, lt=360, description="Wall azimuth in degrees")
    orientation: OrientationType = Field(..., description="Wall orientation")
    height: Optional[float] = Field(None, gt=0, description="Calculated wall height")
    project_id: int = Field(..., description="Associated project ID")
    created_at: Optional[datetime] = Field(default_factory=datetime.now)

    @validator('height', pre=True, always=True)
    def calculate_height(cls, v, values):
        """Calculate height from area and length if not provided."""
        if v is None and 'area' in values and 'length' in values:
            if values['length'] > 0:
                return values['area'] / values['length']
        return v

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True


class ProcessingResult(BaseModel):
    """Model for processing results."""
    success: bool
    total_elements: int = 0
    processed_elements: int = 0
    suitable_elements: int = 0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    processing_time: Optional[float] = None
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True


class UploadMetadata(BaseModel):
    """Model for upload metadata."""
    filename: str
    file_size: int
    upload_timestamp: datetime = Field(default_factory=datetime.now)
    project_id: int
    element_count: int = 0
    file_hash: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True


class ValidationError(BaseModel):
    """Model for validation errors."""
    row_number: int
    column: str
    error_message: str
    suggested_fix: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True