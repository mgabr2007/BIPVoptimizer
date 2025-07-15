"""
Step 5 Radiation Analysis - Production-grade radiation modeling module.
"""

from .models import (
    ElementRadiationResult, AnalysisProgress, PrecisionPreset, PrecisionLevel,
    TMYData, WallShadingData, AnalysisConfiguration, ValidationResult,
    ProjectRadiationSummary, DatabaseMetrics, PRECISION_PRESETS, get_precision_preset
)

from .config import (
    db_config, analysis_config, logging_config, security_config, ui_config,
    TABLE_NAMES, SQL_QUERIES, VALIDATION_THRESHOLDS, DEFAULT_ENVIRONMENTAL_FACTORS
)

from .db.queries import (
    radiation_queries, aggregation_queries, index_manager,
    execute_with_fallback, DatabaseConnectionManager, RadiationDataQueries
)

from .services.analysis_runner import (
    analysis_orchestrator, RadiationAnalysisOrchestrator, ProgressCallback
)

from .ui import RadiationAnalysisUI, LogViewer, render_radiation_grid

__version__ = "1.0.0"
__author__ = "BIPV Optimizer Team"

# Main radiation analysis function
def render_radiation_grid_enhanced(project_id: int) -> None:
    """
    Enhanced function to render the production-grade radiation analysis interface.
    
    Args:
        project_id: Current project ID for analysis
    """
    import streamlit as st
    from .ui import RadiationAnalysisUI, LogViewer
    from .db.queries import index_manager
    
    # Ensure database indexes exist
    try:
        index_manager.ensure_indexes()
    except Exception as e:
        st.warning(f"Database optimization warning: {e}")
    
    # Initialize UI controller
    ui_controller = RadiationAnalysisUI()
    
    # Render main interface
    ui_controller.render_main_interface(project_id)
    
    # Log viewer for debugging
    log_viewer = LogViewer()
    log_viewer.render_log_panel()


# Backward compatibility with existing radiation_grid.py
from pages_modules.radiation_grid import render_radiation_grid as legacy_render

__all__ = [
    # Models
    'ElementRadiationResult', 'AnalysisProgress', 'PrecisionPreset', 'PrecisionLevel',
    'TMYData', 'WallShadingData', 'AnalysisConfiguration', 'ValidationResult',
    'ProjectRadiationSummary', 'DatabaseMetrics', 'PRECISION_PRESETS', 'get_precision_preset',
    
    # Configuration
    'db_config', 'analysis_config', 'logging_config', 'security_config', 'ui_config',
    'TABLE_NAMES', 'SQL_QUERIES', 'VALIDATION_THRESHOLDS', 'DEFAULT_ENVIRONMENTAL_FACTORS',
    
    # Database
    'radiation_queries', 'aggregation_queries', 'index_manager',
    'execute_with_fallback', 'DatabaseConnectionManager', 'RadiationDataQueries',
    
    # Services
    'analysis_orchestrator', 'RadiationAnalysisOrchestrator', 'ProgressCallback',
    
    # UI
    'RadiationAnalysisUI', 'LogViewer', 'render_radiation_grid',
    'render_radiation_grid_enhanced'
]