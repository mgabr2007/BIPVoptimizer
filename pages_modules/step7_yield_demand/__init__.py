"""
Step 7 Yield vs Demand Analysis - Modular Architecture

This package contains the refactored Step 7 components:
- data_validation.py: Dependency checking and validation
- calculation_engine.py: Core energy calculations with caching
- ui_components.py: Streamlit UI rendering components
"""

from .data_validation import get_validated_project_data, validate_step7_dependencies
from .calculation_engine import calculate_monthly_demand, calculate_pv_yields, calculate_energy_balance, save_analysis_results
from .ui_components import (
    render_step7_header,
    render_data_usage_info,
    render_analysis_configuration,
    render_environmental_factors,
    render_analysis_results,
    render_data_export,
    render_step_report_download
)

__all__ = [
    'get_validated_project_data',
    'validate_step7_dependencies',
    'calculate_monthly_demand',
    'calculate_pv_yields',
    'calculate_energy_balance',
    'save_analysis_results',
    'render_step7_header',
    'render_data_usage_info',
    'render_analysis_configuration',
    'render_environmental_factors',
    'render_analysis_results',
    'render_data_export',
    'render_step_report_download'
]