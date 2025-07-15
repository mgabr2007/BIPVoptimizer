"""
Session State Standardization for BIPV Optimizer
Ensures consistent data flow across all workflow steps
"""

import streamlit as st
from typing import Dict, Any, Optional, List
from datetime import datetime

class BIPVSessionStateManager:
    """Centralized session state management for consistent data flow"""
    
    # Standard session state variable names
    STANDARD_VARIABLES = {
        # Core project data
        'project_data': {},
        'project_id': None,
        'project_name': None,
        
        # Step completion flags
        'setup_completed': False,
        'historical_completed': False,
        'weather_completed': False, 
        'facade_completed': False,
        'radiation_completed': False,
        'pv_specs_completed': False,
        'yield_demand_completed': False,
        'optimization_completed': False,
        'financial_completed': False,
        'reporting_completed': False,
        
        # Current workflow state
        'current_step': 'welcome',
        'last_modified': None,
        
        # Data validation flags
        'data_validated': False,
        'element_ids_consistent': True,
        'calculation_errors': []
    }
    
    # Standard project_data structure
    STANDARD_PROJECT_DATA = {
        # Step 1: Project Setup
        'project_name': None,
        'location': None,
        'lat': None,
        'lng': None,
        'timezone': None,
        'currency': 'EUR',
        'building_area': None,
        'selected_weather_station': None,
        'weather_api_choice': None,
        'electricity_rates': {},
        'setup_complete': False,
        
        # Step 2: Historical Data
        'historical_data': {},
        'ai_model_data': {},
        'model_r2_score': None,
        'model_performance_status': None,
        'demand_forecast': {},
        'seasonal_variation': None,
        'ui_metrics': {},
        
        # Step 3: Weather Environment
        'weather_analysis': {},
        'tmy_data': {},
        'environmental_factors': {},
        'api_source': None,
        
        # Step 4: Facade Extraction
        'building_elements': [],
        'facade_data': {},
        'element_count': 0,
        'extraction_complete': False,
        
        # Step 5: Radiation Analysis
        'radiation_data': {},
        'shading_factors': {},
        'analysis_method': 'advanced',
        'calculation_precision': 'standard',
        
        # Step 6: PV Specifications
        'pv_specifications': {},
        'panel_selection': {},
        'system_capacity_total': 0,
        'bipv_technology': {},
        
        # Step 7: Yield vs Demand
        'yield_demand_analysis': {},
        'energy_balance': {},
        'grid_interaction': {},
        
        # Step 8: Optimization
        'optimization_results': {},
        'selected_optimization_solution': {},
        'genetic_algorithm_params': {},
        
        # Step 9: Financial Analysis
        'financial_analysis': {},
        'investment_metrics': {},
        'payback_analysis': {},
        
        # Step 10: Reporting
        'report_generated': False,
        'export_data': {}
    }
    
    @classmethod
    def initialize_session_state(cls):
        """Initialize all standard session state variables"""
        for key, default_value in cls.STANDARD_VARIABLES.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
        
        # Initialize project_data with standard structure
        if 'project_data' not in st.session_state or not st.session_state['project_data']:
            st.session_state['project_data'] = cls.STANDARD_PROJECT_DATA.copy()
        else:
            # Ensure all standard keys exist
            for key, default_value in cls.STANDARD_PROJECT_DATA.items():
                if key not in st.session_state['project_data']:
                    st.session_state['project_data'][key] = default_value
    
    @classmethod
    def validate_data_consistency(cls) -> Dict[str, List[str]]:
        """Validate data consistency across workflow steps"""
        issues = {
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        project_data = st.session_state.get('project_data', {})
        
        # Check Step 1 → Step 2 dependency
        if project_data.get('setup_complete') and not project_data.get('building_area'):
            issues['errors'].append("Step 1: Building area required for Step 2 energy intensity calculations")
        
        # Check Step 2 → Step 7 dependency
        if st.session_state.get('historical_completed') and not project_data.get('historical_data'):
            issues['errors'].append("Step 2: Historical data missing for Step 7 yield vs demand analysis")
        
        # Check Step 4 → Step 5 dependency
        if st.session_state.get('facade_completed') and not project_data.get('building_elements'):
            issues['errors'].append("Step 4: Building elements missing for Step 5 radiation analysis")
        
        # Check Step 5 → Step 6 dependency
        if st.session_state.get('radiation_completed') and not project_data.get('radiation_data'):
            issues['errors'].append("Step 5: Radiation data missing for Step 6 PV specifications")
        
        # Check element ID consistency
        building_elements = project_data.get('building_elements', [])
        radiation_data = project_data.get('radiation_data', {})
        
        if building_elements and radiation_data:
            element_ids_building = set()
            if isinstance(building_elements, list):
                element_ids_building = {elem.get('Element ID', elem.get('element_id', '')) for elem in building_elements}
            
            element_ids_radiation = set()
            if isinstance(radiation_data, dict):
                element_ids_radiation = set(radiation_data.keys())
            elif hasattr(radiation_data, 'keys'):
                element_ids_radiation = set(radiation_data.keys())
            
            missing_radiation = element_ids_building - element_ids_radiation
            if missing_radiation:
                issues['warnings'].append(f"Element IDs missing radiation data: {len(missing_radiation)} elements")
        
        return issues
    
    @classmethod
    def standardize_element_ids(cls):
        """Ensure consistent element ID format across all steps"""
        project_data = st.session_state.get('project_data', {})
        
        # Standardize building elements
        building_elements = project_data.get('building_elements', [])
        if building_elements:
            standardized_elements = []
            for element in building_elements:
                # Ensure consistent field names
                standardized_element = {}
                
                # Element ID (most critical for consistency)
                element_id = (element.get('Element ID') or 
                             element.get('element_id') or 
                             element.get('ElementId') or 
                             element.get('ID'))
                if element_id:
                    standardized_element['element_id'] = str(element_id)
                
                # Orientation
                orientation = (element.get('Orientation') or 
                              element.get('orientation') or 
                              element.get('Cardinal Orientation'))
                if orientation:
                    standardized_element['orientation'] = str(orientation)
                
                # Glass area
                glass_area = (element.get('Glass Area') or 
                             element.get('glass_area') or 
                             element.get('Area'))
                if glass_area:
                    try:
                        standardized_element['glass_area'] = float(glass_area)
                    except (ValueError, TypeError):
                        standardized_element['glass_area'] = 1.5  # Default fallback
                
                # Building level
                level = (element.get('Level') or 
                        element.get('level') or 
                        element.get('Building Level'))
                if level:
                    standardized_element['level'] = str(level)
                
                # Wall element ID
                wall_id = (element.get('HostWallId') or 
                          element.get('wall_element_id') or 
                          element.get('Wall ID'))
                if wall_id:
                    standardized_element['wall_element_id'] = str(wall_id)
                
                # Only add if has essential data
                if 'element_id' in standardized_element:
                    standardized_elements.append(standardized_element)
            
            project_data['building_elements'] = standardized_elements
        
        # Standardize radiation data keys
        radiation_data = project_data.get('radiation_data', {})
        if radiation_data and isinstance(radiation_data, dict):
            standardized_radiation = {}
            for key, value in radiation_data.items():
                # Ensure radiation data uses same element IDs as building elements
                standardized_key = str(key)
                standardized_radiation[standardized_key] = value
            
            project_data['radiation_data'] = standardized_radiation
        
        # Update session state
        st.session_state['project_data'] = project_data
    
    @classmethod
    def get_element_ids(cls) -> List[str]:
        """Get list of all element IDs in consistent format"""
        project_data = st.session_state.get('project_data', {})
        building_elements = project_data.get('building_elements', [])
        
        element_ids = []
        for element in building_elements:
            element_id = element.get('element_id')
            if element_id:
                element_ids.append(str(element_id))
        
        return element_ids
    
    @classmethod
    def update_step_completion(cls, step_name: str, completed: bool = True):
        """Update step completion status with validation"""
        completion_flag = f"{step_name}_completed"
        if completion_flag in cls.STANDARD_VARIABLES:
            st.session_state[completion_flag] = completed
            st.session_state['last_modified'] = datetime.now().isoformat()
            
            # Update project_data completion flags too
            project_data = st.session_state.get('project_data', {})
            project_data[f"{step_name}_complete"] = completed
            st.session_state['project_data'] = project_data
    
    @classmethod
    def get_data_flow_status(cls) -> Dict[str, Any]:
        """Get complete data flow status across workflow"""
        project_data = st.session_state.get('project_data', {})
        
        return {
            'step_1_ready': bool(project_data.get('setup_complete')),
            'step_2_ready': bool(project_data.get('historical_data')),
            'step_3_ready': bool(project_data.get('weather_analysis')),
            'step_4_ready': bool(project_data.get('building_elements')),
            'step_5_ready': bool(project_data.get('radiation_data')),
            'step_6_ready': bool(project_data.get('pv_specifications')),
            'step_7_ready': bool(project_data.get('yield_demand_analysis')),
            'step_8_ready': bool(project_data.get('optimization_results')),
            'step_9_ready': bool(project_data.get('financial_analysis')),
            'step_10_ready': bool(project_data.get('report_generated')),
            
            'element_count': len(project_data.get('building_elements', [])),
            'element_ids_available': len(cls.get_element_ids()),
            'data_consistency_issues': cls.validate_data_consistency()
        }
    
    @classmethod 
    def repair_broken_dependencies(cls):
        """Attempt to repair common data flow issues"""
        project_data = st.session_state.get('project_data', {})
        repairs_made = []
        
        # Repair missing historical data reference
        if st.session_state.get('historical_completed') and not project_data.get('historical_data'):
            # Look for data in alternative locations
            alt_data = (st.session_state.get('historical_data') or 
                       project_data.get('ai_model_data'))
            if alt_data:
                project_data['historical_data'] = alt_data
                repairs_made.append("Restored historical data from alternative location")
        
        # Repair missing radiation data structure
        if st.session_state.get('radiation_completed') and not project_data.get('radiation_data'):
            # Look for radiation results in session state
            alt_radiation = st.session_state.get('radiation_data')
            if alt_radiation:
                project_data['radiation_data'] = alt_radiation
                repairs_made.append("Restored radiation data from session state")
        
        # Repair element ID inconsistencies
        cls.standardize_element_ids()
        repairs_made.append("Standardized element ID format")
        
        # Update session state
        st.session_state['project_data'] = project_data
        
        return repairs_made


def initialize_standardized_session():
    """Initialize session state with standardized structure"""
    BIPVSessionStateManager.initialize_session_state()
    BIPVSessionStateManager.standardize_element_ids()


def validate_step_dependencies(current_step: str) -> Dict[str, Any]:
    """Validate dependencies for current step"""
    return BIPVSessionStateManager.validate_data_consistency()


def repair_data_flow():
    """Repair common data flow issues"""
    return BIPVSessionStateManager.repair_broken_dependencies()


def get_standardized_element_ids() -> List[str]:
    """Get standardized list of element IDs"""
    return BIPVSessionStateManager.get_element_ids()