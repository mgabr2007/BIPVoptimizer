"""
Data Extractor for Comprehensive BIPV Reports
Handles reliable data recovery from database and session state
"""
import streamlit as st
from database_manager import BIPVDatabaseManager

def extract_comprehensive_project_data(project_name):
    """Extract comprehensive project data from all available sources"""
    
    # Initialize database manager
    db_manager = BIPVDatabaseManager()
    
    # Get data from database
    db_data = db_manager.get_project_report_data(project_name)
    
    # Get data from session state
    session_data = st.session_state.get('project_data', {})
    
    # Merge data with priority: database first, then session state
    project_data = {}
    
    if db_data:
        project_data.update(db_data)
    if session_data:
        # Only add session data that's not already in database
        for key, value in session_data.items():
            if key not in project_data or not project_data[key]:
                project_data[key] = value
    
    return project_data

def get_step1_data(project_data):
    """Extract Step 1: Project Setup data"""
    return {
        'project_name': project_data.get('project_name', 'BIPV Project'),
        'location_name': project_data.get('location_name', project_data.get('location', 'Not specified')),
        'latitude': float(project_data.get('latitude', 0)),
        'longitude': float(project_data.get('longitude', 0)),
        'timezone': project_data.get('timezone', 'UTC'),
        'weather_station': project_data.get('weather_station', 'Not selected'),
        'station_distance': float(project_data.get('station_distance', 0)),
        'wmo_id': project_data.get('wmo_id', 'Not available'),
        'import_rate': float(project_data.get('import_rate', project_data.get('electricity_rate', 0.30))),
        'export_rate': float(project_data.get('export_rate', project_data.get('feed_in_rate', 0.08)))
    }

def get_step2_data(project_data):
    """Extract Step 2: Historical Data & AI Model data"""
    historical_data = project_data.get('historical_data', {})
    if isinstance(historical_data, str):
        historical_data = {}
    
    return {
        'r2_score': float(project_data.get('r2_score', project_data.get('model_r2_score', 0))),
        'rmse': float(project_data.get('rmse', project_data.get('model_rmse', 0))),
        'building_area': float(project_data.get('building_floor_area', project_data.get('building_area', 5000))),
        'energy_intensity': float(project_data.get('energy_intensity', 0)),
        'peak_load_factor': float(project_data.get('peak_load_factor', 0)),
        'forecast_years': 25
    }

def get_step3_data(project_data):
    """Extract Step 3: Weather & Environment data"""
    weather_data = project_data.get('weather_analysis', {})
    if isinstance(weather_data, str):
        weather_data = {}
    
    return {
        'annual_ghi': float(project_data.get('annual_ghi', 1200)),
        'annual_dni': float(project_data.get('annual_dni', 1500)),
        'annual_dhi': float(project_data.get('annual_dhi', 600)),
        'vegetation_factor': float(project_data.get('vegetation_shading_factor', 0.95)),
        'building_factor': float(project_data.get('building_shading_factor', 0.90)),
        'tmy_hours': 8760
    }

def get_step4_data(project_data):
    """Extract Step 4: Building Elements data"""
    building_elements = project_data.get('building_elements', [])
    
    if not building_elements:
        return {
            'total_elements': 0,
            'total_area': 0,
            'orientation_counts': {},
            'level_counts': {}
        }
    
    total_area = sum([float(elem.get('glass_area', 0)) for elem in building_elements])
    
    # Count orientations
    orientation_counts = {}
    level_counts = {}
    
    for elem in building_elements:
        orientation = elem.get('orientation', 'Unknown')
        level = elem.get('building_level', elem.get('level', 'Unknown'))
        
        orientation_counts[orientation] = orientation_counts.get(orientation, 0) + 1
        level_counts[level] = level_counts.get(level, 0) + 1
    
    return {
        'total_elements': len(building_elements),
        'total_area': total_area,
        'orientation_counts': orientation_counts,
        'level_counts': level_counts,
        'avg_area': total_area / len(building_elements) if building_elements else 0
    }

def get_step5_data(project_data):
    """Extract Step 5: Radiation Analysis data"""
    building_elements = project_data.get('building_elements', [])
    
    if not building_elements:
        return {
            'avg_radiation': 0,
            'max_radiation': 0,
            'min_radiation': 0,
            'orientation_radiation': {}
        }
    
    radiations = [float(elem.get('annual_radiation', 0)) for elem in building_elements if elem.get('annual_radiation')]
    
    if not radiations:
        return {
            'avg_radiation': 0,
            'max_radiation': 0,
            'min_radiation': 0,
            'orientation_radiation': {}
        }
    
    # Calculate radiation by orientation
    orientation_radiation = {}
    for elem in building_elements:
        orientation = elem.get('orientation', 'Unknown')
        radiation = float(elem.get('annual_radiation', 0))
        
        if orientation not in orientation_radiation:
            orientation_radiation[orientation] = []
        orientation_radiation[orientation].append(radiation)
    
    # Calculate averages
    for orientation in orientation_radiation:
        values = orientation_radiation[orientation]
        orientation_radiation[orientation] = {
            'avg': sum(values) / len(values),
            'count': len(values)
        }
    
    return {
        'avg_radiation': sum(radiations) / len(radiations),
        'max_radiation': max(radiations),
        'min_radiation': min(radiations),
        'orientation_radiation': orientation_radiation,
        'total_elements': len(building_elements)
    }

def get_step6_data(project_data):
    """Extract Step 6: PV Specifications data"""
    pv_specs = project_data.get('pv_specifications', {})
    individual_systems = pv_specs.get('individual_systems', [])
    
    total_capacity = sum([float(system.get('capacity_kw', 0)) for system in individual_systems])
    total_cost = sum([float(system.get('total_cost_eur', 0)) for system in individual_systems])
    total_area = sum([float(system.get('glass_area', 0)) for system in individual_systems])
    
    bipv_specs = pv_specs.get('bipv_specifications', {})
    
    return {
        'total_capacity': total_capacity,
        'total_cost': total_cost,
        'total_area': total_area,
        'system_count': len(individual_systems),
        'efficiency': float(bipv_specs.get('efficiency', 0.08)) * 100,
        'transparency': float(bipv_specs.get('transparency', 0.3)) * 100,
        'cost_per_m2': float(bipv_specs.get('cost_per_m2', 300)),
        'cost_per_kw': total_cost / total_capacity if total_capacity > 0 else 0
    }

def get_step7_data(project_data):
    """Extract Step 7: Yield vs Demand data"""
    yield_demand = project_data.get('yield_demand_analysis', {})
    monthly_balance = yield_demand.get('monthly_energy_balance', [])
    
    if not monthly_balance:
        return {
            'annual_demand': 0,
            'annual_generation': 0,
            'annual_savings': 0,
            'annual_revenue': 0,
            'self_consumption_rate': 0,
            'monthly_data': []
        }
    
    annual_demand = sum([float(month.get('demand_kwh', 0)) for month in monthly_balance])
    annual_generation = sum([float(month.get('generation_kwh', 0)) for month in monthly_balance])
    annual_savings = sum([float(month.get('cost_savings_eur', 0)) for month in monthly_balance])
    annual_revenue = sum([float(month.get('feed_in_revenue_eur', 0)) for month in monthly_balance])
    
    return {
        'annual_demand': annual_demand,
        'annual_generation': annual_generation,
        'annual_savings': annual_savings,
        'annual_revenue': annual_revenue,
        'self_consumption_rate': (annual_generation / annual_demand * 100) if annual_demand > 0 else 0,
        'monthly_data': monthly_balance
    }

def get_step8_data(project_data):
    """Extract Step 8: Optimization data"""
    optimization = project_data.get('optimization_results', {})
    solutions = optimization.get('pareto_solutions', optimization.get('solutions', []))
    
    if not solutions:
        return {
            'solution_count': 0,
            'best_cost': 0,
            'best_yield': 0,
            'best_roi': 0,
            'weights': {}
        }
    
    costs = [float(sol.get('cost', sol.get('total_cost', 0))) for sol in solutions]
    yields = [float(sol.get('yield', sol.get('annual_yield', 0))) for sol in solutions]
    rois = [float(sol.get('roi', 0)) for sol in solutions]
    
    return {
        'solution_count': len(solutions),
        'best_cost': min(costs) if costs else 0,
        'best_yield': max(yields) if yields else 0,
        'best_roi': max(rois) if rois else 0,
        'weights': optimization.get('objective_weights', {})
    }

def get_step9_data(project_data):
    """Extract Step 9: Financial Analysis data"""
    financial = project_data.get('financial_analysis', {})
    
    return {
        'npv': float(financial.get('npv', 0)),
        'irr': float(financial.get('irr', 0)),
        'payback_period': float(financial.get('payback_period', 0)),
        'annual_savings': float(financial.get('annual_savings', 0)),
        'system_capacity': float(financial.get('system_capacity', 0)),
        'installation_cost': float(financial.get('installation_cost', 0)),
        'annual_co2_savings': float(financial.get('annual_co2_savings', 0)),
        'lifetime_co2_savings': float(financial.get('lifetime_co2_savings', 0))
    }