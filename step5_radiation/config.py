"""
Configuration constants and settings for radiation analysis module.
"""

import os
from typing import Dict, Any
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


class AnalysisConfig(BaseSettings):
    """Radiation analysis configuration settings."""
    
    # Default precision settings
    default_precision: str = Field(default="daily_peak")
    enable_parallel_processing: bool = Field(default=True)
    max_workers: int = Field(default=4)
    chunk_size: int = Field(default=50)
    
    # Timeout settings
    element_timeout: int = Field(default=30)  # seconds per element
    total_timeout: int = Field(default=3600)  # total analysis timeout
    
    # Solar calculation settings
    solar_elevation_threshold: float = Field(default=5.0)  # degrees
    atmospheric_pressure: float = Field(default=101325.0)  # Pa
    
    # Environmental shading defaults
    default_tree_shading: float = Field(default=0.85)
    default_building_shading: float = Field(default=0.90)
    
    # Memory management
    max_memory_mb: int = Field(default=1024)
    cleanup_interval: int = Field(default=100)  # elements
    
    class Config:
        env_prefix = "ANALYSIS_"


class LoggingConfig(BaseSettings):
    """Logging configuration settings."""
    
    level: str = Field(default="INFO")
    format: str = Field(default="json" if os.getenv("ENV") == "prod" else "text")
    file_enabled: bool = Field(default=True)
    console_enabled: bool = Field(default=True)
    
    # Log file settings
    log_file: str = Field(default="logs/radiation_analysis.log")
    max_file_size: str = Field(default="10 MB")
    backup_count: int = Field(default=5)
    
    # Sentry settings
    sentry_dsn: str = Field(default="", env="SENTRY_DSN")
    sentry_environment: str = Field(default="development", env="SENTRY_ENV")
    
    class Config:
        env_prefix = "LOG_"


class SecurityConfig(BaseSettings):
    """Security and access control settings."""
    
    enable_rbac: bool = Field(default=False)
    require_project_ownership: bool = Field(default=True)
    
    # File validation (for future uploads)
    max_file_size_mb: int = Field(default=100)
    allowed_mime_types: list = Field(default_factory=lambda: ["text/csv", "application/json"])
    
    # Rate limiting
    max_requests_per_minute: int = Field(default=60)
    max_concurrent_analyses: int = Field(default=3)
    
    class Config:
        env_prefix = "SECURITY_"


class UIConfig(BaseSettings):
    """UI configuration settings."""
    
    # Progress update intervals
    progress_update_interval: int = Field(default=5)  # elements
    log_display_lines: int = Field(default=200)
    
    # Chart settings
    chart_height: int = Field(default=400)
    chart_theme: str = Field(default="plotly")
    
    # Dashboard settings
    enable_dashboard: bool = Field(default=True)
    dashboard_cache_ttl: int = Field(default=300)  # seconds
    
    class Config:
        env_prefix = "UI_"


# Table and column name constants
TABLE_NAMES = {
    "building_elements": "building_elements",
    "building_walls": "building_walls",
    "element_radiation": "element_radiation",
    "radiation_analysis": "radiation_analysis",
    "projects": "projects",
    "weather_data": "weather_data"
}

COLUMN_MAPPINGS = {
    "element_radiation": {
        "id": "id",
        "project_id": "project_id",
        "element_id": "element_id",
        "orientation": "orientation",
        "azimuth": "azimuth",
        "glass_area": "glass_area",
        "annual_radiation": "annual_radiation",
        "monthly_radiation": "monthly_radiation",
        "shading_factor": "shading_factor",
        "created_at": "created_at"
    }
}

# SQL query templates
SQL_QUERIES = {
    "get_project_elements": """
        SELECT element_id, orientation, azimuth, glass_area, wall_element_id
        FROM building_elements 
        WHERE project_id = $1 AND pv_suitable = true
        ORDER BY element_id
    """,
    
    "get_wall_data": """
        SELECT element_id, orientation, azimuth, area, level
        FROM building_walls 
        WHERE project_id = $1
        ORDER BY element_id
    """,
    
    "upsert_radiation_result": """
        INSERT INTO element_radiation 
        (project_id, element_id, orientation, azimuth, glass_area, 
         annual_radiation, monthly_radiation, shading_factor, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (project_id, element_id) 
        DO UPDATE SET
            orientation = EXCLUDED.orientation,
            azimuth = EXCLUDED.azimuth,
            glass_area = EXCLUDED.glass_area,
            annual_radiation = EXCLUDED.annual_radiation,
            monthly_radiation = EXCLUDED.monthly_radiation,
            shading_factor = EXCLUDED.shading_factor,
            created_at = EXCLUDED.created_at
    """,
    
    "get_radiation_summary": """
        SELECT 
            COUNT(*) as total_elements,
            AVG(annual_radiation) as avg_radiation,
            SUM(glass_area) as total_area,
            orientation,
            COUNT(*) as orientation_count
        FROM element_radiation 
        WHERE project_id = $1
        GROUP BY orientation
    """,
    
    "clear_radiation_data": """
        DELETE FROM element_radiation WHERE project_id = $1
    """
}

# Index creation statements
INDEX_STATEMENTS = [
    "CREATE INDEX IF NOT EXISTS idx_element_radiation_project_id ON element_radiation(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_element_radiation_element_id ON element_radiation(element_id)",
    "CREATE INDEX IF NOT EXISTS idx_element_radiation_orientation ON element_radiation(orientation)",
    "CREATE INDEX IF NOT EXISTS idx_building_elements_project_pv ON building_elements(project_id, pv_suitable)",
    "CREATE INDEX IF NOT EXISTS idx_building_walls_project_id ON building_walls(project_id)"
]

# Validation thresholds
VALIDATION_THRESHOLDS = {
    "min_elements": 1,
    "max_elements": 10000,
    "min_glass_area": 0.1,  # m²
    "max_glass_area": 100.0,  # m²
    "min_radiation": 0.0,  # kWh/m²/year
    "max_radiation": 3000.0,  # kWh/m²/year
    "min_azimuth": 0.0,  # degrees
    "max_azimuth": 360.0,  # degrees
}

# Default environmental factors
DEFAULT_ENVIRONMENTAL_FACTORS = {
    "trees": 0.85,  # 15% reduction
    "buildings": 0.90,  # 10% reduction
    "atmospheric": 0.95,  # 5% reduction
    "ground_reflection": 0.20  # 20% ground reflectance
}

# Error messages
ERROR_MESSAGES = {
    "no_elements": "No suitable building elements found for radiation analysis",
    "no_tmy_data": "No TMY weather data available for analysis",
    "invalid_precision": "Invalid precision level specified",
    "database_error": "Database operation failed",
    "analysis_timeout": "Analysis exceeded maximum time limit",
    "insufficient_memory": "Insufficient memory for analysis",
    "invalid_configuration": "Invalid analysis configuration"
}

# Load configuration instances
db_config = DatabaseConfig()
analysis_config = AnalysisConfig()
logging_config = LoggingConfig()
security_config = SecurityConfig()
ui_config = UIConfig()

# Export commonly used values
PRECISION_LEVELS = ["hourly", "daily_peak", "monthly_average", "yearly_average"]
DEFAULT_PRECISION = analysis_config.default_precision
MAX_WORKERS = analysis_config.max_workers
CHUNK_SIZE = analysis_config.chunk_size