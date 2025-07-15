"""
Configuration constants and settings for PV specification module.
"""

import os
from typing import Dict, Any, List
from pathlib import Path
from pydantic import BaseSettings, Field


class DatabaseConfig(BaseSettings):
    """Database configuration settings."""
    
    host: str = Field(default="localhost", env="PGHOST")
    port: int = Field(default=5432, env="PGPORT")
    database: str = Field(default="postgres", env="PGDATABASE")
    username: str = Field(default="postgres", env="PGUSER")
    password: str = Field(default="", env="PGPASSWORD")
    
    # Connection pool settings
    min_connections: int = Field(default=1)
    max_connections: int = Field(default=10)
    connection_timeout: int = Field(default=30)
    
    # Performance settings
    batch_size: int = Field(default=1000)
    max_retries: int = Field(default=3)
    retry_delay: float = Field(default=1.0)
    
    @property
    def connection_url(self) -> str:
        """Get database connection URL."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def async_connection_url(self) -> str:
        """Get async database connection URL."""
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    class Config:
        env_prefix = "DB_"


class SpecificationConfig(BaseSettings):
    """PV specification calculation configuration."""
    
    # Coverage factors
    default_coverage_factor: float = Field(default=0.85, description="Default panel coverage")
    min_coverage_factor: float = Field(default=0.60, description="Minimum coverage")
    max_coverage_factor: float = Field(default=0.95, description="Maximum coverage")
    
    # Performance ratios
    default_performance_ratio: float = Field(default=0.85, description="Default system performance ratio")
    min_performance_ratio: float = Field(default=0.70, description="Minimum performance ratio")
    max_performance_ratio: float = Field(default=0.95, description="Maximum performance ratio")
    
    # System sizing limits
    min_system_size_kw: float = Field(default=0.1, description="Minimum system size in kW")
    max_system_size_kw: float = Field(default=1000.0, description="Maximum system size in kW")
    min_glass_area_m2: float = Field(default=0.5, description="Minimum glass area in m²")
    max_glass_area_m2: float = Field(default=100.0, description="Maximum glass area in m²")
    
    # Calculation settings
    enable_vectorized_calculations: bool = Field(default=True, description="Use vectorized pandas calculations")
    use_dask_for_large_datasets: bool = Field(default=True, description="Use Dask for >100k elements")
    large_dataset_threshold: int = Field(default=100000, description="Threshold for large dataset processing")
    
    # Filtering options
    filter_by_orientation: bool = Field(default=True, description="Filter unsuitable orientations")
    unsuitable_orientations: List[str] = Field(
        default_factory=lambda: ["North"], 
        description="Orientations to filter out"
    )
    min_annual_radiation: float = Field(default=300.0, description="Minimum annual radiation kWh/m²/year")
    
    class Config:
        env_prefix = "SPEC_"


class CatalogConfig(BaseSettings):
    """Panel catalog configuration."""
    
    enable_custom_panels: bool = Field(default=True, description="Allow custom panel specifications")
    enable_catalog_crud: bool = Field(default=True, description="Enable catalog CRUD operations")
    require_admin_for_crud: bool = Field(default=True, description="Require admin role for CRUD")
    
    # Auto-calculation settings
    auto_calculate_power_density: bool = Field(default=True, description="Auto-calculate missing power density")
    standard_irradiance: float = Field(default=1000.0, description="Standard test irradiance W/m²")
    
    # Cache settings
    enable_catalog_cache: bool = Field(default=True, description="Enable LRU caching for catalog")
    cache_ttl_seconds: int = Field(default=3600, description="Cache TTL in seconds")
    cache_max_size: int = Field(default=100, description="Maximum cache entries")
    
    class Config:
        env_prefix = "CATALOG_"


class UIConfig(BaseSettings):
    """UI configuration settings."""
    
    # Chart settings
    chart_height: int = Field(default=400, description="Default chart height")
    chart_theme: str = Field(default="plotly", description="Chart theme")
    
    # Export settings
    enable_excel_export: bool = Field(default=True, description="Enable Excel export")
    csv_encoding: str = Field(default="utf-8-sig", description="CSV encoding with BOM")
    
    # Session persistence
    persist_selections: bool = Field(default=True, description="Persist selections in session state")
    auto_save_interval: int = Field(default=300, description="Auto-save interval in seconds")
    
    class Config:
        env_prefix = "UI_"


class SecurityConfig(BaseSettings):
    """Security and access control settings."""
    
    enable_rbac: bool = Field(default=False, description="Enable role-based access control")
    require_project_ownership: bool = Field(default=True, description="Require project ownership")
    
    # API settings
    enable_api: bool = Field(default=True, description="Enable FastAPI endpoints")
    api_key_required: bool = Field(default=False, description="Require API key")
    rate_limit_per_minute: int = Field(default=60, description="API rate limit per minute")
    
    class Config:
        env_prefix = "SECURITY_"


class LoggingConfig(BaseSettings):
    """Logging configuration settings."""
    
    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="json" if os.getenv("ENV") == "prod" else "text", description="Log format")
    file_enabled: bool = Field(default=True, description="Enable file logging")
    console_enabled: bool = Field(default=True, description="Enable console logging")
    
    # Log file settings
    log_file: str = Field(default="logs/pv_specification.log", description="Log file path")
    max_file_size: str = Field(default="10 MB", description="Maximum log file size")
    backup_count: int = Field(default=5, description="Number of backup files")
    
    # Sentry settings
    sentry_dsn: str = Field(default="", env="SENTRY_DSN", description="Sentry DSN")
    sentry_environment: str = Field(default="development", env="SENTRY_ENV", description="Sentry environment")
    
    class Config:
        env_prefix = "LOG_"


# Table and column name constants
TABLE_NAMES = {
    "panel_catalog": "panel_catalog",
    "element_pv_specifications": "element_pv_specifications",
    "building_elements": "building_elements",
    "element_radiation": "element_radiation",
    "projects": "projects"
}

COLUMN_MAPPINGS = {
    "panel_catalog": {
        "id": "id",
        "name": "name",
        "manufacturer": "manufacturer",
        "panel_type": "panel_type",
        "efficiency": "efficiency",
        "transparency": "transparency",
        "power_density": "power_density",
        "cost_per_m2": "cost_per_m2",
        "glass_thickness": "glass_thickness",
        "u_value": "u_value",
        "glass_weight": "glass_weight",
        "performance_ratio": "performance_ratio",
        "is_active": "is_active"
    },
    "element_pv_specifications": {
        "id": "id",
        "project_id": "project_id",
        "element_id": "element_id",
        "panel_spec_id": "panel_spec_id",
        "glass_area": "glass_area",
        "panel_coverage": "panel_coverage",
        "effective_area": "effective_area",
        "system_power": "system_power",
        "annual_radiation": "annual_radiation",
        "annual_energy": "annual_energy",
        "specific_yield": "specific_yield",
        "total_cost": "total_cost",
        "cost_per_wp": "cost_per_wp",
        "orientation": "orientation"
    }
}

# SQL query templates
SQL_QUERIES = {
    "get_active_panels": """
        SELECT * FROM panel_catalog 
        WHERE is_active = true 
        ORDER BY manufacturer, name
    """,
    
    "get_panels_by_type": """
        SELECT * FROM panel_catalog 
        WHERE is_active = true AND panel_type = $1 
        ORDER BY efficiency DESC
    """,
    
    "insert_panel": """
        INSERT INTO panel_catalog 
        (name, manufacturer, panel_type, efficiency, transparency, power_density, 
         cost_per_m2, glass_thickness, u_value, glass_weight, performance_ratio, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        RETURNING id
    """,
    
    "update_panel": """
        UPDATE panel_catalog SET
            name = $2, manufacturer = $3, panel_type = $4, efficiency = $5,
            transparency = $6, power_density = $7, cost_per_m2 = $8,
            glass_thickness = $9, u_value = $10, glass_weight = $11,
            performance_ratio = $12, is_active = $13, updated_at = CURRENT_TIMESTAMP
        WHERE id = $1
    """,
    
    "upsert_element_specification": """
        INSERT INTO element_pv_specifications 
        (project_id, element_id, panel_spec_id, glass_area, panel_coverage,
         effective_area, system_power, annual_radiation, annual_energy,
         specific_yield, total_cost, cost_per_wp, orientation, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
        ON CONFLICT (project_id, element_id) 
        DO UPDATE SET
            panel_spec_id = EXCLUDED.panel_spec_id,
            glass_area = EXCLUDED.glass_area,
            panel_coverage = EXCLUDED.panel_coverage,
            effective_area = EXCLUDED.effective_area,
            system_power = EXCLUDED.system_power,
            annual_radiation = EXCLUDED.annual_radiation,
            annual_energy = EXCLUDED.annual_energy,
            specific_yield = EXCLUDED.specific_yield,
            total_cost = EXCLUDED.total_cost,
            cost_per_wp = EXCLUDED.cost_per_wp,
            orientation = EXCLUDED.orientation,
            created_at = EXCLUDED.created_at
    """,
    
    "get_project_specifications": """
        SELECT eps.*, pc.name as panel_name, pc.manufacturer
        FROM element_pv_specifications eps
        JOIN panel_catalog pc ON eps.panel_spec_id = pc.id
        WHERE eps.project_id = $1
        ORDER BY eps.element_id
    """,
    
    "get_specification_summary": """
        SELECT 
            COUNT(*) as total_elements,
            SUM(glass_area) as total_glass_area,
            SUM(effective_area) as total_effective_area,
            SUM(system_power) as total_system_power,
            SUM(annual_energy) as total_annual_energy,
            SUM(total_cost) as total_system_cost,
            AVG(specific_yield) as avg_specific_yield,
            AVG(cost_per_wp) as avg_cost_per_wp
        FROM element_pv_specifications 
        WHERE project_id = $1
    """,
    
    "clear_project_specifications": """
        DELETE FROM element_pv_specifications WHERE project_id = $1
    """,
    
    "get_building_elements_with_radiation": """
        SELECT be.element_id, be.orientation, be.azimuth, be.glass_area, be.pv_suitable,
               er.annual_radiation, er.shading_factor
        FROM building_elements be
        LEFT JOIN element_radiation er ON be.project_id = er.project_id AND be.element_id = er.element_id
        WHERE be.project_id = $1 AND be.pv_suitable = true
        ORDER BY be.element_id
    """
}

# Index creation statements
INDEX_STATEMENTS = [
    "CREATE INDEX IF NOT EXISTS idx_panel_catalog_type_active ON panel_catalog(panel_type, is_active)",
    "CREATE INDEX IF NOT EXISTS idx_panel_catalog_manufacturer ON panel_catalog(manufacturer)",
    "CREATE INDEX IF NOT EXISTS idx_element_pv_specs_project_id ON element_pv_specifications(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_element_pv_specs_element_id ON element_pv_specifications(element_id)",
    "CREATE INDEX IF NOT EXISTS idx_element_pv_specs_panel_id ON element_pv_specifications(panel_spec_id)",
    "CREATE INDEX IF NOT EXISTS idx_element_pv_specs_orientation ON element_pv_specifications(orientation)",
    "CREATE INDEX IF NOT EXISTS idx_element_pv_specs_project_element ON element_pv_specifications(project_id, element_id)"
]

# Validation constants
VALIDATION_RANGES = {
    "efficiency": (0.02, 0.25),  # 2% to 25%
    "transparency": (0.0, 0.65),  # 0% to 65%
    "power_density": (10, 250),  # 10 to 250 W/m²
    "cost_per_m2": (50, 1000),  # €50 to €1000 per m²
    "glass_thickness": (1.0, 15.0),  # 1mm to 15mm
    "u_value": (0.5, 6.0),  # 0.5 to 6.0 W/m²K
    "glass_weight": (5.0, 50.0),  # 5 to 50 kg/m²
    "performance_ratio": (0.60, 0.95),  # 60% to 95%
    "coverage_factor": (0.50, 0.98),  # 50% to 98%
    "glass_area": (0.1, 100.0),  # 0.1 to 100 m²
    "annual_radiation": (100, 3000)  # 100 to 3000 kWh/m²/year
}

# Unit conversion factors
UNIT_CONVERSIONS = {
    "cm2_to_m2": 0.0001,  # cm² to m²
    "kw_to_w": 1000,  # kW to W
    "percent_to_decimal": 0.01,  # % to decimal
    "kwh_to_wh": 1000  # kWh to Wh
}

# Default panel types filter
PANEL_TYPE_FILTERS = {
    "opaque": {
        "transparency_max": 0.05,
        "efficiency_min": 0.08,
        "applications": ["facades", "roofs", "canopies"]
    },
    "semi_transparent": {
        "transparency_min": 0.05,
        "transparency_max": 0.65,
        "efficiency_min": 0.06,
        "applications": ["windows", "skylights", "curtain_walls"]
    }
}

# Orientation suitability factors
ORIENTATION_FACTORS = {
    "South": 1.0,
    "Southeast": 0.95,
    "Southwest": 0.95,
    "East": 0.85,
    "West": 0.85,
    "Northeast": 0.70,
    "Northwest": 0.70,
    "North": 0.50,  # Can be filtered out
    "Unknown": 0.60
}

# Cost estimation parameters
COST_PARAMETERS = {
    "installation_factor": 1.2,  # 20% installation markup
    "inverter_cost_per_kw": 150.0,  # €150/kW for inverters
    "structural_cost_per_m2": 25.0,  # €25/m² for structural components
    "electrical_cost_per_system": 200.0,  # €200 per system for electrical
    "margin_factor": 1.15  # 15% profit margin
}

# API endpoint configuration
API_ENDPOINTS = {
    "base_path": "/api/v1",
    "specifications": "/pv-specs/{project_id}",
    "catalog": "/panel-catalog",
    "summary": "/pv-summary/{project_id}",
    "export": "/export/{project_id}/{format}"
}

# Error messages
ERROR_MESSAGES = {
    "no_elements": "No suitable building elements found for PV specification",
    "no_radiation": "No radiation analysis data available",
    "invalid_panel": "Invalid panel specification selected",
    "calculation_failed": "PV specification calculation failed",
    "database_error": "Database operation failed",
    "validation_failed": "Data validation failed",
    "insufficient_data": "Insufficient data for analysis",
    "export_failed": "Export operation failed"
}

# Load configuration instances
db_config = DatabaseConfig()
spec_config = SpecificationConfig()
catalog_config = CatalogConfig()
ui_config = UIConfig()
security_config = SecurityConfig()
logging_config = LoggingConfig()

# Export commonly used values
DEFAULT_COVERAGE_FACTOR = spec_config.default_coverage_factor
DEFAULT_PERFORMANCE_RATIO = spec_config.default_performance_ratio
MIN_SYSTEM_SIZE = spec_config.min_system_size_kw
MAX_SYSTEM_SIZE = spec_config.max_system_size_kw
ENABLE_VECTORIZED = spec_config.enable_vectorized_calculations
LARGE_DATASET_THRESHOLD = spec_config.large_dataset_threshold