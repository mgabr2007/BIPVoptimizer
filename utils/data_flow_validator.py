"""
Data Flow Validation System for BIPV Optimizer
Validates data consistency between workflow steps and provides repair mechanisms
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime

def validate_step_dependencies() -> Dict[str, Any]:
    """Comprehensive validation of dependencies between workflow steps"""
    
    validation_report = {
        'passed': [],
        'warnings': [],
        'errors': [],
        'critical_errors': [],
        'summary': {}
    }
    
    project_data = st.session_state.get('project_data', {})
    
    # Step 1 → Step 2 Dependencies
    if project_data.get('setup_complete'):
        if not project_data.get('building_area'):
            validation_report['errors'].append("Step 1→2: Building area missing - required for energy intensity calculations")
        else:
            validation_report['passed'].append("Step 1→2: Building area available")
    
    # Step 2 → Step 7 Dependencies  
    if st.session_state.get('historical_completed', False):
        historical_data = project_data.get('historical_data', {})
        if not historical_data:
            validation_report['critical_errors'].append("Step 2→7: Historical data completely missing")
        elif not historical_data.get('consumption_data'):
            validation_report['errors'].append("Step 2→7: Consumption data missing from historical analysis")
        else:
            validation_report['passed'].append("Step 2→7: Historical data available")
            
        # Check AI model data
        ai_model = project_data.get('ai_model_data', {})
        if not ai_model.get('r2_score'):
            validation_report['warnings'].append("Step 2→7: AI model R² score missing")
    
    # Step 3 → Step 5 Dependencies
    if st.session_state.get('weather_completed', False):
        weather_data = project_data.get('weather_analysis', {})
        if not weather_data:
            validation_report['critical_errors'].append("Step 3→5: Weather analysis data missing")
        elif not weather_data.get('tmy_data'):
            validation_report['errors'].append("Step 3→5: TMY data missing for radiation calculations")
        else:
            validation_report['passed'].append("Step 3→5: Weather data available")
    
    # Step 4 → Step 5 Dependencies
    if st.session_state.get('facade_completed', False):
        building_elements = project_data.get('building_elements', [])
        if not building_elements:
            validation_report['critical_errors'].append("Step 4→5: Building elements completely missing")
        else:
            validation_report['passed'].append(f"Step 4→5: {len(building_elements)} building elements available")
            
            # Validate element structure
            missing_fields = []
            if building_elements:
                sample_element = building_elements[0]
                required_fields = ['element_id', 'orientation', 'glass_area']
                for field in required_fields:
                    if field not in sample_element:
                        missing_fields.append(field)
            
            if missing_fields:
                validation_report['errors'].append(f"Step 4→5: Missing element fields: {missing_fields}")
    
    # Step 5 → Step 6 Dependencies
    if st.session_state.get('radiation_completed', False):
        radiation_data = project_data.get('radiation_data', {})
        if not radiation_data:
            validation_report['critical_errors'].append("Step 5→6: Radiation analysis data missing")
        else:
            element_count = len(radiation_data) if isinstance(radiation_data, dict) else 0
            validation_report['passed'].append(f"Step 5→6: Radiation data for {element_count} elements")
    
    # Step 6 → Step 7/8 Dependencies
    if st.session_state.get('pv_specs_completed', False):
        pv_specs = project_data.get('pv_specifications', {})
        if not pv_specs:
            validation_report['critical_errors'].append("Step 6→7/8: PV specifications missing")
        else:
            validation_report['passed'].append("Step 6→7/8: PV specifications available")
    
    # Element ID Consistency Check
    building_elements = project_data.get('building_elements', [])
    radiation_data = project_data.get('radiation_data', {})
    
    if building_elements and radiation_data:
        element_ids_building = set()
        for elem in building_elements:
            elem_id = elem.get('element_id') or elem.get('Element ID') or elem.get('ElementId')
            if elem_id:
                element_ids_building.add(str(elem_id))
        
        element_ids_radiation = set(str(k) for k in radiation_data.keys())
        
        missing_in_radiation = element_ids_building - element_ids_radiation
        extra_in_radiation = element_ids_radiation - element_ids_building
        
        if missing_in_radiation:
            validation_report['warnings'].append(f"Element ID mismatch: {len(missing_in_radiation)} elements missing radiation data")
        
        if extra_in_radiation:
            validation_report['warnings'].append(f"Element ID mismatch: {len(extra_in_radiation)} extra radiation entries")
        
        if not missing_in_radiation and not extra_in_radiation:
            validation_report['passed'].append("Element ID consistency: Perfect match between building elements and radiation data")
    
    # Calculate summary
    validation_report['summary'] = {
        'total_checks': len(validation_report['passed']) + len(validation_report['warnings']) + len(validation_report['errors']) + len(validation_report['critical_errors']),
        'passed_checks': len(validation_report['passed']),
        'warning_count': len(validation_report['warnings']),
        'error_count': len(validation_report['errors']),
        'critical_count': len(validation_report['critical_errors']),
        'overall_status': 'CRITICAL' if validation_report['critical_errors'] else 
                         'ERROR' if validation_report['errors'] else 
                         'WARNING' if validation_report['warnings'] else 'PASSED'
    }
    
    return validation_report


def repair_data_flow_issues() -> List[str]:
    """Attempt to repair common data flow issues automatically"""
    
    repairs_made = []
    project_data = st.session_state.get('project_data', {})
    
    # Repair 1: Fix missing historical data reference
    if st.session_state.get('historical_completed') and not project_data.get('historical_data'):
        # Look for data in alternative locations
        for alt_key in ['historical_analysis', 'ai_model_results', 'consumption_analysis']:
            alt_data = project_data.get(alt_key)
            if alt_data:
                project_data['historical_data'] = alt_data
                repairs_made.append(f"Restored historical data from {alt_key}")
                break
    
    # Repair 2: Fix missing element ID standardization
    building_elements = project_data.get('building_elements', [])
    if building_elements:
        standardized_count = 0
        for i, element in enumerate(building_elements):
            # Standardize element ID field name
            elem_id = element.get('Element ID') or element.get('ElementId') or element.get('element_id')
            if elem_id and 'element_id' not in element:
                element['element_id'] = str(elem_id)
                standardized_count += 1
            
            # Standardize orientation field
            orientation = element.get('Orientation') or element.get('orientation') or element.get('Cardinal Orientation')
            if orientation and 'orientation' not in element:
                element['orientation'] = str(orientation)
            
            # Standardize glass area field
            glass_area = element.get('Glass Area') or element.get('glass_area') or element.get('Glass Area (m²)')
            if glass_area and 'glass_area' not in element:
                try:
                    element['glass_area'] = float(glass_area)
                except (ValueError, TypeError):
                    element['glass_area'] = 1.5  # Default fallback
        
        if standardized_count > 0:
            repairs_made.append(f"Standardized element ID format for {standardized_count} elements")
    
    # Repair 3: Fix missing radiation data structure
    if st.session_state.get('radiation_completed') and not project_data.get('radiation_data'):
        # Look for radiation data in session state
        alt_radiation = st.session_state.get('radiation_analysis_results')
        if alt_radiation:
            project_data['radiation_data'] = alt_radiation
            repairs_made.append("Restored radiation data from session state")
    
    # Repair 4: Fix missing completion flags consistency
    completion_mapping = {
        'setup_complete': 'setup_completed',
        'data_analysis_complete': 'historical_completed', 
        'weather_analysis_complete': 'weather_completed',
        'extraction_complete': 'facade_completed',
        'radiation_analysis_complete': 'radiation_completed'
    }
    
    for project_flag, session_flag in completion_mapping.items():
        if project_data.get(project_flag) and not st.session_state.get(session_flag):
            st.session_state[session_flag] = True
            repairs_made.append(f"Synchronized {session_flag} completion flag")
    
    # Update project data in session state
    st.session_state['project_data'] = project_data
    
    return repairs_made


def display_data_flow_status():
    """Display comprehensive data flow status in Streamlit interface"""
    
    validation_report = validate_step_dependencies()
    
    # Header
    status_icon = {
        'PASSED': '✅',
        'WARNING': '⚠️', 
        'ERROR': '❌',
        'CRITICAL': '🔴'
    }
    
    overall_status = validation_report['summary']['overall_status']
    st.subheader(f"{status_icon[overall_status]} Data Flow Status: {overall_status}")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Passed", validation_report['summary']['passed_checks'])
    with col2:
        st.metric("Warnings", validation_report['summary']['warning_count'])
    with col3:
        st.metric("Errors", validation_report['summary']['error_count'])
    with col4:
        st.metric("Critical", validation_report['summary']['critical_count'])
    
    # Detailed results
    if validation_report['passed']:
        with st.expander(f"✅ Passed Checks ({len(validation_report['passed'])})", expanded=False):
            for item in validation_report['passed']:
                st.success(item)
    
    if validation_report['warnings']:
        with st.expander(f"⚠️ Warnings ({len(validation_report['warnings'])})", expanded=True):
            for item in validation_report['warnings']:
                st.warning(item)
    
    if validation_report['errors']:
        with st.expander(f"❌ Errors ({len(validation_report['errors'])})", expanded=True):
            for item in validation_report['errors']:
                st.error(item)
    
    if validation_report['critical_errors']:
        with st.expander(f"🔴 Critical Errors ({len(validation_report['critical_errors'])})", expanded=True):
            for item in validation_report['critical_errors']:
                st.error(item)
    
    # Repair button
    if validation_report['warnings'] or validation_report['errors']:
        if st.button("🔧 Attempt Automatic Repairs", type="primary"):
            repairs = repair_data_flow_issues()
            if repairs:
                st.success("✅ Repairs completed:")
                for repair in repairs:
                    st.info(f"• {repair}")
                st.rerun()
            else:
                st.info("No automatic repairs available for current issues")
    
    return validation_report


def get_element_id_mapping() -> Dict[str, str]:
    """Get mapping of element IDs between different data structures"""
    
    project_data = st.session_state.get('project_data', {})
    building_elements = project_data.get('building_elements', [])
    radiation_data = project_data.get('radiation_data', {})
    
    mapping = {}
    
    # Map building element IDs to radiation data keys
    for element in building_elements:
        elem_id = element.get('element_id') or element.get('Element ID') or element.get('ElementId')
        if elem_id:
            elem_id_str = str(elem_id)
            if elem_id_str in radiation_data:
                mapping[elem_id_str] = elem_id_str
            else:
                # Look for variations
                for rad_key in radiation_data.keys():
                    if str(rad_key) == elem_id_str:
                        mapping[elem_id_str] = str(rad_key)
                        break
    
    return mapping