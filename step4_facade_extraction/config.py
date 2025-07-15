"""
Configuration management for facade extraction module.
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class OrientationConfig(BaseModel):
    """Configuration for orientation thresholds."""
    north_range: List[float] = Field(default=[315, 45], description="North orientation range in degrees")
    south_range: List[float] = Field(default=[135, 225], description="South orientation range in degrees")
    east_range: List[float] = Field(default=[45, 135], description="East orientation range in degrees")
    west_range: List[float] = Field(default=[225, 315], description="West orientation range in degrees")


class SuitabilityRules(BaseModel):
    """Configuration for PV suitability rules."""
    min_glass_area: float = Field(default=0.5, description="Minimum glass area in m²")
    max_glass_area: float = Field(default=100.0, description="Maximum glass area in m²")
    suitable_orientations: List[str] = Field(
        default=["South", "East", "West", "Southeast", "Southwest"],
        description="Orientations suitable for PV"
    )
    excluded_families: List[str] = Field(
        default=["Roof", "Floor", "Ceiling"],
        description="Window families to exclude"
    )
    min_building_level: Optional[str] = Field(default=None, description="Minimum building level")


class DatabaseConfig(BaseModel):
    """Configuration for database operations."""
    batch_size: int = Field(default=1000, description="Batch size for bulk operations")
    connection_timeout: int = Field(default=30, description="Connection timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    tables: Dict[str, str] = Field(
        default={
            "building_elements": "building_elements",
            "building_walls": "building_walls",
            "projects": "projects"
        },
        description="Database table names"
    )


class ProcessingConfig(BaseModel):
    """Configuration for data processing."""
    chunk_size: int = Field(default=500, description="CSV processing chunk size")
    max_file_size_mb: int = Field(default=50, description="Maximum file size in MB")
    allowed_extensions: List[str] = Field(default=[".csv"], description="Allowed file extensions")
    encoding_fallbacks: List[str] = Field(
        default=["utf-8", "latin-1", "iso-8859-1", "cp1252"],
        description="Encoding fallback sequence"
    )


class UIConfig(BaseModel):
    """Configuration for user interface."""
    progress_update_interval: int = Field(default=100, description="Progress update interval")
    max_preview_rows: int = Field(default=10, description="Maximum rows in data preview")
    enable_debug_mode: bool = Field(default=False, description="Enable debug information")
    chart_height: int = Field(default=400, description="Chart height in pixels")


class SecurityConfig(BaseModel):
    """Configuration for security settings."""
    enable_malware_scan: bool = Field(default=False, description="Enable malware scanning")
    max_upload_size_mb: int = Field(default=50, description="Maximum upload size in MB")
    allowed_mime_types: List[str] = Field(
        default=["text/csv", "application/csv"],
        description="Allowed MIME types"
    )


class FacadeExtractionConfig(BaseModel):
    """Main configuration class for facade extraction."""
    orientation: OrientationConfig = Field(default_factory=OrientationConfig)
    suitability: SuitabilityRules = Field(default_factory=SuitabilityRules)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    @classmethod
    def load_from_file(cls, config_path: Path) -> "FacadeExtractionConfig":
        """Load configuration from YAML or JSON file."""
        if not config_path.exists():
            return cls()  # Return default config if file doesn't exist
        
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
                data = yaml.safe_load(f)
            elif config_path.suffix.lower() == '.json':
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported config file format: {config_path.suffix}")
        
        return cls(**data)

    def save_to_file(self, config_path: Path) -> None:
        """Save configuration to YAML or JSON file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
                yaml.dump(self.dict(), f, default_flow_style=False, sort_keys=False)
            elif config_path.suffix.lower() == '.json':
                json.dump(self.dict(), f, indent=2)
            else:
                raise ValueError(f"Unsupported config file format: {config_path.suffix}")


# Default configuration instance
DEFAULT_CONFIG = FacadeExtractionConfig()

# Configuration file path
CONFIG_PATH = Path(__file__).parent / "config.yaml"


def get_config() -> FacadeExtractionConfig:
    """Get the current configuration."""
    if CONFIG_PATH.exists():
        return FacadeExtractionConfig.load_from_file(CONFIG_PATH)
    return DEFAULT_CONFIG


def save_config(config: FacadeExtractionConfig) -> None:
    """Save configuration to file."""
    config.save_to_file(CONFIG_PATH)


def reset_config() -> FacadeExtractionConfig:
    """Reset to default configuration."""
    config = FacadeExtractionConfig()
    save_config(config)
    return config