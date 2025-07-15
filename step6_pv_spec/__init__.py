"""
Step 6 PV Specification - Production-grade BIPV panel specification module.
"""

from .models import (
    PanelSpecification, ElementPVSpecification, BuildingElement,
    RadiationRecord, ProjectPVSummary, SpecificationConfiguration,
    ValidationResult, CalculationMetrics, PanelType, OrientationType,
    DEFAULT_PANEL_SPECIFICATIONS, validate_element_radiation_data, detect_unit_anomalies
)

from .config import (
    db_config, spec_config, catalog_config, ui_config, security_config, logging_config,
    TABLE_NAMES, COLUMN_MAPPINGS, SQL_QUERIES, INDEX_STATEMENTS,
    VALIDATION_RANGES, UNIT_CONVERSIONS, PANEL_TYPE_FILTERS,
    ORIENTATION_FACTORS, COST_PARAMETERS, API_ENDPOINTS, ERROR_MESSAGES
)

from .db.queries import (
    panel_catalog_queries, specification_queries, project_data_queries,
    execute_with_fallback, DatabaseConnectionManager, create_temp_tables, ensure_indexes
)

from .services.spec_calculator import (
    spec_calculator, SpecificationCalculator
)

from .services.panel_catalog import (
    panel_catalog_manager, PanelCatalogManager, get_default_panels,
    ensure_catalog_initialized, get_panel_by_name, get_recommended_panels_for_application
)

from .ui import PVSpecificationUI, render_pv_specification

__version__ = "1.0.0"
__author__ = "BIPV Optimizer Team"

# Main PV specification function
def render_pv_specification_enhanced(project_id: int) -> None:
    """
    Enhanced function to render the production-grade PV specification interface.
    
    Args:
        project_id: Current project ID for specification analysis
    """
    import streamlit as st
    from .ui import PVSpecificationUI
    from .db.queries import ensure_indexes
    from .services.panel_catalog import ensure_catalog_initialized
    import asyncio
    
    # Ensure database setup
    try:
        ensure_indexes()
        asyncio.run(ensure_catalog_initialized())
    except Exception as e:
        st.warning(f"Database initialization warning: {e}")
    
    # Initialize UI controller
    ui_controller = PVSpecificationUI()
    
    # Render main interface
    ui_controller.render_main_interface(project_id)


# Backward compatibility with existing pv_specification.py
from pages_modules.pv_specification import render_pv_specification as legacy_render

__all__ = [
    # Models
    'PanelSpecification', 'ElementPVSpecification', 'BuildingElement',
    'RadiationRecord', 'ProjectPVSummary', 'SpecificationConfiguration',
    'ValidationResult', 'CalculationMetrics', 'PanelType', 'OrientationType',
    'DEFAULT_PANEL_SPECIFICATIONS', 'validate_element_radiation_data', 'detect_unit_anomalies',
    
    # Configuration
    'db_config', 'spec_config', 'catalog_config', 'ui_config', 'security_config', 'logging_config',
    'TABLE_NAMES', 'COLUMN_MAPPINGS', 'SQL_QUERIES', 'INDEX_STATEMENTS',
    'VALIDATION_RANGES', 'UNIT_CONVERSIONS', 'PANEL_TYPE_FILTERS',
    'ORIENTATION_FACTORS', 'COST_PARAMETERS', 'API_ENDPOINTS', 'ERROR_MESSAGES',
    
    # Database
    'panel_catalog_queries', 'specification_queries', 'project_data_queries',
    'execute_with_fallback', 'DatabaseConnectionManager', 'create_temp_tables', 'ensure_indexes',
    
    # Services
    'spec_calculator', 'SpecificationCalculator',
    'panel_catalog_manager', 'PanelCatalogManager', 'get_default_panels',
    'ensure_catalog_initialized', 'get_panel_by_name', 'get_recommended_panels_for_application',
    
    # UI
    'PVSpecificationUI', 'render_pv_specification', 'render_pv_specification_enhanced'
]