"""
Consolidated Data Manager for BIPV Optimizer
Centralized storage and retrieval of all workflow analysis results
"""

import streamlit as st
from datetime import datetime
import json

class ConsolidatedDataManager:
    """Manages consolidated analysis data across all workflow steps"""
    
    def __init__(self):
        # Initialize consolidated data structure if not exists
        if 'consolidated_analysis_data' not in st.session_state:
            st.session_state.consolidated_analysis_data = {
                'project_info': {},
                'step1_project_setup': {},
                'step2_historical_data': {},
                'step3_weather_environment': {},
                'step4_facade_extraction': {},
                'step5_radiation_analysis': {},
                'step6_pv_specification': {},
                'step7_yield_demand': {},
                'step8_optimization': {},
                'step9_financial_analysis': {},
                'last_updated': None
            }
    
    def save_step1_data(self, project_data):
        """Save Step 1: Project Setup data"""
        consolidated = st.session_state.consolidated_analysis_data
        consolidated['step1_project_setup'] = {
            'project_name': project_data.get('project_name'),
            'location': project_data.get('location'),
            'coordinates': project_data.get('coordinates', {}),
            'timezone': project_data.get('timezone'),
            'currency': project_data.get('currency'),
            'weather_station': project_data.get('selected_weather_station', {}),
            'electricity_rates': project_data.get('electricity_rates', {}),
            'solar_parameters': project_data.get('solar_parameters', {}),
            'setup_complete': project_data.get('setup_complete', False),
        }
        consolidated['project_info'] = {
            'name': project_data.get('project_name'),
            'location': project_data.get('location'),
            'coordinates': project_data.get('coordinates', {})
        }
        consolidated['last_updated'] = datetime.now().isoformat()
        # Silenced console output to prevent duplicate logging
        # print(f"ConsolidatedDataManager: Saved Step 1 data")
    
    def save_step2_data(self, historical_data):
        """Save Step 2: Historical Data & AI Model"""
        consolidated = st.session_state.consolidated_analysis_data
        consolidated['step2_historical_data'] = {
            'historical_data': historical_data.get('historical_data', {}),
            'demand_forecast': historical_data.get('demand_forecast', {}),
            'model_r2_score': historical_data.get('model_r2_score', 0),
            'model_performance_status': historical_data.get('model_performance_status', 'Unknown'),
            'building_area': historical_data.get('building_area', 5000),
            'annual_consumption': self._calculate_annual_consumption(historical_data),
            'energy_intensity': self._calculate_energy_intensity(historical_data),
            'data_analysis_complete': historical_data.get('data_analysis_complete', False)
        }
        consolidated['last_updated'] = datetime.now().isoformat()
        # Silenced console output to prevent duplicate logging
        # print(f"ConsolidatedDataManager: Saved Step 2 data")
    
    def save_step3_data(self, weather_data):
        """Save Step 3: Weather & Environment"""
        consolidated = st.session_state.consolidated_analysis_data
        consolidated['step3_weather_environment'] = {
            'weather_analysis': weather_data.get('weather_analysis', {}),
            'tmy_data': weather_data.get('tmy_data', []),
            'environmental_factors': weather_data.get('environmental_factors', {}),
            'solar_irradiance_annual': self._extract_solar_irradiance(weather_data),
            'weather_complete': weather_data.get('weather_complete', False)
        }
        consolidated['last_updated'] = datetime.now().isoformat()
        # Silenced console output to prevent duplicate logging
        # print(f"ConsolidatedDataManager: Saved Step 3 data")
    
    def save_step4_data(self, facade_data):
        """Save Step 4: Facade & Window Extraction"""
        consolidated = st.session_state.consolidated_analysis_data
        
        # Extract building elements from various possible locations
        building_elements = (facade_data.get('building_elements', []) or 
                           facade_data.get('facade_data', {}).get('building_elements', []) or
                           facade_data.get('elements', []) or
                           [])
        
        consolidated['step4_facade_extraction'] = {
            'building_elements': building_elements,
            'total_elements': len(building_elements),
            'total_glass_area': self._calculate_total_glass_area(building_elements),
            'orientation_distribution': self._analyze_orientations(building_elements),
            'level_distribution': self._analyze_levels(building_elements),
            'extraction_complete': facade_data.get('extraction_complete', False)
        }
        consolidated['last_updated'] = datetime.now().isoformat()
        # Silenced console output to prevent duplicate logging
        # print(f"ConsolidatedDataManager: Saved Step 4 data - {len(building_elements)} elements")
    
    def save_step5_data(self, radiation_data):
        """Save Step 5: Radiation & Shading Analysis"""
        consolidated = st.session_state.consolidated_analysis_data
        consolidated['step5_radiation_analysis'] = {
            'radiation_data': radiation_data.get('radiation_data', {}),
            'element_radiation': radiation_data.get('element_radiation', []),
            'analysis_parameters': radiation_data.get('analysis_parameters', {}),
            'shading_factors': radiation_data.get('shading_factors', {}),
            'radiation_complete': radiation_data.get('radiation_complete', False)
        }
        consolidated['last_updated'] = datetime.now().isoformat()
        # Silenced console output to prevent duplicate logging
        # print(f"ConsolidatedDataManager: Saved Step 5 data")
    
    def save_step6_data(self, pv_specs):
        """Save Step 6: PV Specification"""
        consolidated = st.session_state.consolidated_analysis_data
        
        # Extract individual systems from various possible locations
        individual_systems = (pv_specs.get('individual_systems', []) or 
                            pv_specs.get('systems', []) or
                            pv_specs.get('pv_specifications', {}).get('individual_systems', []) or
                            [])
        
        consolidated['step6_pv_specification'] = {
            'pv_specifications': pv_specs.get('pv_specifications', {}),
            'individual_systems': individual_systems,
            'bipv_specifications': pv_specs.get('bipv_specifications', {}),
            'total_capacity': self._calculate_total_capacity(individual_systems),
            'total_cost': self._calculate_total_cost(individual_systems),
            'specifications_complete': pv_specs.get('specifications_complete', False)
        }
        consolidated['last_updated'] = datetime.now().isoformat()
        # Silenced console output to prevent duplicate logging
        # print(f"ConsolidatedDataManager: Saved Step 6 data - {len(individual_systems)} systems")
    
    def save_step7_data(self, yield_demand_data):
        """Save Step 7: Yield vs Demand Analysis"""
        consolidated = st.session_state.consolidated_analysis_data
        consolidated['step7_yield_demand'] = {
            'yield_demand_analysis': yield_demand_data.get('yield_demand_analysis', {}),
            'energy_balance': yield_demand_data.get('energy_balance', {}),
            'monthly_analysis': yield_demand_data.get('monthly_analysis', []),
            'annual_metrics': yield_demand_data.get('annual_metrics', {}),
            'yield_complete': yield_demand_data.get('yield_complete', False)
        }
        consolidated['last_updated'] = datetime.now().isoformat()
        # Silenced console output to prevent duplicate logging
        # print(f"ConsolidatedDataManager: Saved Step 7 data")
    
    def save_step8_data(self, optimization_data):
        """Save Step 8: Optimization Results"""
        consolidated = st.session_state.consolidated_analysis_data
        
        # Extract solutions from various possible locations
        solutions = (optimization_data.get('solutions', []) or 
                    optimization_data.get('pareto_solutions', []) or
                    optimization_data.get('optimization_results', {}).get('solutions', []) or
                    [])
        
        consolidated['step8_optimization'] = {
            'optimization_results': optimization_data.get('optimization_results', {}),
            'solutions': solutions,
            'selected_solution': optimization_data.get('selected_optimization_solution', {}),
            'pareto_solutions': solutions,
            'algorithm_parameters': optimization_data.get('algorithm_parameters', {}),
            'optimization_complete': optimization_data.get('optimization_complete', False)
        }
        consolidated['last_updated'] = datetime.now().isoformat()
        # Silenced console output to prevent duplicate logging
        # print(f"ConsolidatedDataManager: Saved Step 8 data - {len(solutions)} solutions")
    
    def save_step9_data(self, financial_data):
        """Save Step 9: Financial Analysis"""
        consolidated = st.session_state.consolidated_analysis_data
        consolidated['step9_financial_analysis'] = {
            'financial_analysis': financial_data.get('financial_analysis', {}),
            'cash_flow_analysis': financial_data.get('cash_flow_analysis', {}),
            'environmental_impact': financial_data.get('environmental_impact', {}),
            'economic_metrics': financial_data.get('economic_metrics', {}),
            'financial_complete': financial_data.get('financial_complete', False)
        }
        consolidated['last_updated'] = datetime.now().isoformat()
        # Silenced console output to prevent duplicate logging
        # print(f"ConsolidatedDataManager: Saved Step 9 data")
    
    def get_consolidated_data(self):
        """Get all consolidated analysis data"""
        return st.session_state.consolidated_analysis_data
    
    def get_step_data(self, step_number):
        """Get data for a specific step"""
        step_key = f'step{step_number}_' + {
            1: 'project_setup',
            2: 'historical_data', 
            3: 'weather_environment',
            4: 'facade_extraction',
            5: 'radiation_analysis',
            6: 'pv_specification',
            7: 'yield_demand',
            8: 'optimization',
            9: 'financial_analysis'
        }.get(step_number, '')
        
        return st.session_state.consolidated_analysis_data.get(step_key, {})
    
    def _calculate_annual_consumption(self, historical_data):
        """Calculate annual consumption from historical data"""
        try:
            demand_forecast = historical_data.get('demand_forecast', {})
            if 'monthly_forecast' in demand_forecast:
                monthly_data = demand_forecast['monthly_forecast']
                if isinstance(monthly_data, list) and len(monthly_data) >= 12:
                    return sum(monthly_data[:12])  # First year
            
            # Fallback to historical data
            hist_data = historical_data.get('historical_data', {})
            if 'consumption_data' in hist_data:
                consumption = hist_data['consumption_data']
                if isinstance(consumption, list):
                    return sum(consumption)
            
            return 0
        except:
            return 0
    
    def _calculate_energy_intensity(self, historical_data):
        """Calculate energy intensity (kWh/m²/year)"""
        try:
            annual_consumption = self._calculate_annual_consumption(historical_data)
            building_area = historical_data.get('building_area', 5000)
            return annual_consumption / building_area if building_area > 0 else 0
        except:
            return 0
    
    def _extract_solar_irradiance(self, weather_data):
        """Extract solar irradiance data"""
        try:
            weather_analysis = weather_data.get('weather_analysis', {})
            return {
                'annual_ghi': weather_analysis.get('annual_ghi', 1200),
                'annual_dni': weather_analysis.get('annual_dni', 1500),
                'annual_dhi': weather_analysis.get('annual_dhi', 600)
            }
        except:
            return {'annual_ghi': 1200, 'annual_dni': 1500, 'annual_dhi': 600}
    
    def _calculate_total_glass_area(self, building_elements):
        """Calculate total glass area from building elements"""
        try:
            total_area = 0
            for element in building_elements:
                if isinstance(element, dict):
                    glass_area = (element.get('glass_area') or 
                                element.get('Glass_Area') or 
                                element.get('window_area') or 0)
                    total_area += float(glass_area) if glass_area else 0
            return total_area
        except:
            return 0
    
    def _analyze_orientations(self, building_elements):
        """Analyze orientation distribution"""
        try:
            orientations = {}
            for element in building_elements:
                if isinstance(element, dict):
                    orientation = (element.get('orientation') or 
                                 element.get('Orientation') or 
                                 'Unknown')
                    orientations[orientation] = orientations.get(orientation, 0) + 1
            return orientations
        except:
            return {}
    
    def _analyze_levels(self, building_elements):
        """Analyze building level distribution"""
        try:
            levels = {}
            for element in building_elements:
                if isinstance(element, dict):
                    level = (element.get('building_level') or 
                           element.get('Level') or 
                           element.get('level') or 
                           'Unknown')
                    levels[level] = levels.get(level, 0) + 1
            return levels
        except:
            return {}
    
    def _calculate_total_capacity(self, individual_systems):
        """Calculate total system capacity"""
        try:
            total_capacity = 0
            for system in individual_systems:
                if isinstance(system, dict):
                    capacity = (system.get('capacity_kw') or 
                              system.get('capacity') or 0)
                    total_capacity += float(capacity) if capacity else 0
            return total_capacity
        except:
            return 0
    
    def _calculate_total_cost(self, individual_systems):
        """Calculate total system cost"""
        try:
            total_cost = 0
            for system in individual_systems:
                if isinstance(system, dict):
                    cost = (system.get('total_cost_eur') or 
                          system.get('total_cost') or 0)
                    total_cost += float(cost) if cost else 0
            return total_cost
        except:
            return 0
    
    def print_summary(self):
        """Print summary of consolidated data (silenced to prevent duplicate logging)"""
        # Silenced console output to prevent duplicate logging
        # consolidated = st.session_state.consolidated_analysis_data
        # print("\n=== Consolidated Data Summary ===")
        # for step_key, step_data in consolidated.items():
        #     if step_key.startswith('step') and isinstance(step_data, dict):
        #         print(f"{step_key}: {len(step_data)} fields")
        #         if 'building_elements' in step_data:
        #             print(f"  - Building elements: {len(step_data['building_elements'])}")
        #         if 'individual_systems' in step_data:
        #             print(f"  - Individual systems: {len(step_data['individual_systems'])}")
        #         if 'solutions' in step_data:
        #             print(f"  - Solutions: {len(step_data['solutions'])}")
        pass