"""
Data validation and dependency checking for Step 7 Yield vs Demand Analysis
"""

import streamlit as st
from services.io import get_current_project_id
from database_manager import db_manager


def validate_step7_dependencies(project_id):
    """
    Validate all required data dependencies for Step 7 analysis.
    
    Returns:
        tuple: (is_valid, validation_results, project_data)
    """
    validation_results = {
        'project_id': False,
        'historical_data': False,
        'pv_specifications': False,
        'building_elements': False,
        'weather_data': False,
        'errors': [],
        'warnings': []
    }
    
    if not project_id:
        validation_results['errors'].append("No project ID found. Please complete Step 1 (Project Setup) first.")
        return False, validation_results, None
    
    validation_results['project_id'] = True
    
    try:
        # Fetch all project data in single database call
        project_data = db_manager.get_project_data(project_id)
        
        # Validate historical data (Step 2) - check both ai_models and energy_analysis tables
        historical_data = db_manager.get_historical_data(project_id)
        if historical_data and (historical_data.get('annual_consumption') or historical_data.get('data_analysis_complete')):
            validation_results['historical_data'] = True
        else:
            # Also check ai_models table directly
            try:
                conn = db_manager.get_connection()
                if conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT COUNT(*) FROM ai_models WHERE project_id = %s", (project_id,))
                        ai_model_count = cursor.fetchone()[0]
                        if ai_model_count > 0:
                            validation_results['historical_data'] = True
                        else:
                            validation_results['errors'].append("Historical energy data missing. Please complete Step 2 (Historical Data Analysis).")
                    conn.close()
                else:
                    validation_results['errors'].append("Historical energy data missing. Please complete Step 2 (Historical Data Analysis).")
            except Exception:
                validation_results['errors'].append("Historical energy data missing. Please complete Step 2 (Historical Data Analysis).")
        
        # Validate PV specifications (Step 6)
        pv_specs = db_manager.get_pv_specifications(project_id)
        if pv_specs is not None and len(pv_specs) > 0:
            validation_results['pv_specifications'] = True
        else:
            validation_results['errors'].append("PV system specifications missing. Please complete Step 6 (PV Specification).")
        
        # Validate building elements (Step 4)
        building_elements = db_manager.get_building_elements(project_id)
        if building_elements is not None and len(building_elements) > 0:
            validation_results['building_elements'] = True
        else:
            validation_results['warnings'].append("Building elements data missing. This may affect accuracy.")
        
        # Validate weather data (Step 3)
        if project_data and project_data.get('weather_analysis'):
            validation_results['weather_data'] = True
        else:
            validation_results['warnings'].append("TMY weather data missing from Step 3. Using simplified calculations.")
        
        # Overall validation
        required_deps = ['project_id', 'historical_data', 'pv_specifications']
        is_valid = all(validation_results[dep] for dep in required_deps)
        
        return is_valid, validation_results, project_data
        
    except Exception as e:
        validation_results['errors'].append(f"Database error: {str(e)}")
        return False, validation_results, None


def display_validation_results(validation_results):
    """Display validation results to user."""
    
    if validation_results['errors']:
        st.error("❌ **Missing Required Data:**")
        for error in validation_results['errors']:
            st.error(f"• {error}")
        return False
    
    if validation_results['warnings']:
        st.warning("⚠️ **Data Quality Warnings:**")
        for warning in validation_results['warnings']:
            st.warning(f"• {warning}")
    
    # Show successful validations
    success_count = sum(1 for key, value in validation_results.items() 
                       if key not in ['errors', 'warnings'] and value)
    
    st.success(f"✅ **Data Validation Complete:** {success_count}/4 dependencies satisfied")
    
    return True


def get_validated_project_data():
    """
    Get validated project data with comprehensive dependency checking.
    
    Returns:
        tuple: (project_id, project_data, validation_passed)
    """
    project_id = get_current_project_id()
    
    if not project_id:
        st.error("⚠️ No project ID found. Please complete Step 1 (Project Setup) first.")
        return None, None, False
    
    # Validate dependencies
    is_valid, validation_results, project_data = validate_step7_dependencies(project_id)
    
    # Display validation results
    validation_passed = display_validation_results(validation_results)
    
    if not validation_passed:
        return project_id, None, False
    
    return project_id, project_data, True