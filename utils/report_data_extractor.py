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

def safe_float(value, default=0.0):
    """Safely convert value to float, returning default if None or invalid"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def get_step1_data(project_data):
    """Extract Step 1: Project Setup data"""
    return {
        'project_name': project_data.get('project_name', 'BIPV Project'),
        'location_name': project_data.get('location_name', project_data.get('location', 'Not specified')),
        'latitude': safe_float(project_data.get('latitude'), 0),
        'longitude': safe_float(project_data.get('longitude'), 0),
        'timezone': project_data.get('timezone', 'UTC'),
        'weather_station': project_data.get('weather_station', 'Not selected'),
        'station_distance': safe_float(project_data.get('station_distance'), 0),
        'wmo_id': project_data.get('wmo_id', 'Not available'),
        'import_rate': safe_float(project_data.get('import_rate', project_data.get('electricity_rate', 0.30)), 0.30),
        'export_rate': safe_float(project_data.get('export_rate', project_data.get('feed_in_rate', 0.08)), 0.08)
    }

def get_step2_data(project_data):
    """Extract Step 2: Historical Data & AI Model data"""
    historical_data = project_data.get('historical_data', {})
    if isinstance(historical_data, str):
        historical_data = {}
    
    return {
        'r2_score': safe_float(project_data.get('r2_score', project_data.get('model_r2_score', 0)), 0),
        'rmse': safe_float(project_data.get('rmse', project_data.get('model_rmse', 0)), 0),
        'building_area': safe_float(project_data.get('building_floor_area', project_data.get('building_area', 5000)), 5000),
        'energy_intensity': safe_float(project_data.get('energy_intensity', 0), 0),
        'peak_load_factor': safe_float(project_data.get('peak_load_factor', 0), 0),
        'forecast_years': 25
    }

def get_step3_data(project_data):
    """Extract Step 3: Weather & Environment data"""
    weather_data = project_data.get('weather_analysis', {})
    if isinstance(weather_data, str):
        weather_data = {}
    
    return {
        'annual_ghi': safe_float(project_data.get('annual_ghi', 1200), 1200),
        'annual_dni': safe_float(project_data.get('annual_dni', 1500), 1500),
        'annual_dhi': safe_float(project_data.get('annual_dhi', 600), 600),
        'vegetation_factor': safe_float(project_data.get('vegetation_shading_factor', 0.95), 0.95),
        'building_factor': safe_float(project_data.get('building_shading_factor', 0.90), 0.90),
        'tmy_hours': 8760
    }

def get_step4_data(project_data):
    """Extract Step 4: Building Elements data"""
    building_elements = project_data.get('building_elements', [])
    
    # Handle DataFrame case
    if hasattr(building_elements, 'to_dict'):
        building_elements = building_elements.to_dict('records')
    
    if not building_elements or len(building_elements) == 0:
        return {
            'total_elements': 0,
            'total_area': 0,
            'orientation_counts': {},
            'level_counts': {},
            'avg_area': 0
        }
    
    total_area = sum([safe_float(elem.get('glass_area', 0), 0) for elem in building_elements])
    
    # Count orientations with debug info
    orientation_counts = {}
    level_counts = {}
    
    # Debug: print first few elements to see data structure
    print(f"DEBUG: Building elements sample (first 3): {building_elements[:3] if building_elements else 'None'}")
    
    for elem in building_elements:
        # Try multiple possible orientation field names
        orientation = (
            elem.get('orientation') or 
            elem.get('Orientation') or 
            elem.get('orientation_desc') or
            elem.get('Orientation Desc') or
            'Unknown'
        )
        
        # Clean up orientation values - map numeric orientations to cardinal directions
        if isinstance(orientation, (int, float)):
            if 315 <= orientation or orientation < 45:
                orientation = 'North'
            elif 45 <= orientation < 135:
                orientation = 'East'
            elif 135 <= orientation < 225:
                orientation = 'South'
            elif 225 <= orientation < 315:
                orientation = 'West'
        elif isinstance(orientation, str):
            # Handle descriptive orientations like "East (45-135°)"
            orientation_lower = orientation.lower()
            if 'north' in orientation_lower:
                orientation = 'North'
            elif 'east' in orientation_lower:
                orientation = 'East'
            elif 'south' in orientation_lower:
                orientation = 'South'
            elif 'west' in orientation_lower:
                orientation = 'West'
        
        level = elem.get('building_level', elem.get('level', elem.get('Level', 'Unknown')))
        
        orientation_counts[orientation] = orientation_counts.get(orientation, 0) + 1
        level_counts[level] = level_counts.get(level, 0) + 1
    
    print(f"DEBUG: Final orientation counts: {orientation_counts}")
    
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
    
    # Handle DataFrame case
    if hasattr(building_elements, 'to_dict'):
        building_elements = building_elements.to_dict('records')
    
    if not building_elements or len(building_elements) == 0:
        return {
            'avg_radiation': 0,
            'max_radiation': 0,
            'min_radiation': 0,
            'orientation_radiation': {}
        }
    
    radiations = [safe_float(elem.get('annual_radiation', 0), 0) for elem in building_elements if elem.get('annual_radiation')]
    
    if not radiations:
        return {
            'avg_radiation': 0,
            'max_radiation': 0,
            'min_radiation': 0,
            'orientation_radiation': {}
        }
    
    # Calculate radiation by orientation with same mapping logic
    orientation_radiation = {}
    for elem in building_elements:
        # Use same orientation mapping logic as Step 4
        orientation = (
            elem.get('orientation') or 
            elem.get('Orientation') or 
            elem.get('orientation_desc') or
            elem.get('Orientation Desc') or
            'Unknown'
        )
        
        # Clean up orientation values
        if isinstance(orientation, (int, float)):
            if 315 <= orientation or orientation < 45:
                orientation = 'North'
            elif 45 <= orientation < 135:
                orientation = 'East'
            elif 135 <= orientation < 225:
                orientation = 'South'
            elif 225 <= orientation < 315:
                orientation = 'West'
        elif isinstance(orientation, str):
            orientation_lower = orientation.lower()
            if 'north' in orientation_lower:
                orientation = 'North'
            elif 'east' in orientation_lower:
                orientation = 'East'
            elif 'south' in orientation_lower:
                orientation = 'South'
            elif 'west' in orientation_lower:
                orientation = 'West'
        
        radiation = safe_float(elem.get('annual_radiation', 0), 0)
        
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
    
    # Handle DataFrame case for individual systems
    if hasattr(individual_systems, 'to_dict'):
        individual_systems = individual_systems.to_dict('records')
    
    total_capacity = sum([safe_float(system.get('capacity_kw', 0), 0) for system in individual_systems])
    total_cost = sum([safe_float(system.get('total_cost_eur', 0), 0) for system in individual_systems])
    total_area = sum([safe_float(system.get('glass_area', 0), 0) for system in individual_systems])
    
    bipv_specs = pv_specs.get('bipv_specifications', {})
    
    return {
        'total_capacity': total_capacity,
        'total_cost': total_cost,
        'total_area': total_area,
        'system_count': len(individual_systems),
        'efficiency': safe_float(bipv_specs.get('efficiency', 0.08), 0.08) * 100,
        'transparency': safe_float(bipv_specs.get('transparency', 0.3), 0.3) * 100,
        'cost_per_m2': safe_float(bipv_specs.get('cost_per_m2', 300), 300),
        'cost_per_kw': total_cost / total_capacity if total_capacity > 0 else 0
    }

def get_step7_data(project_data):
    """Extract Step 7: Yield vs Demand data"""
    yield_demand = project_data.get('yield_demand_analysis', {})
    monthly_balance = yield_demand.get('monthly_energy_balance', [])
    
    # Handle DataFrame case for monthly balance
    if hasattr(monthly_balance, 'to_dict'):
        monthly_balance = monthly_balance.to_dict('records')
    
    if not monthly_balance or len(monthly_balance) == 0:
        return {
            'annual_demand': 0,
            'annual_generation': 0,
            'annual_savings': 0,
            'annual_revenue': 0,
            'self_consumption_rate': 0,
            'monthly_data': []
        }
    
    annual_demand = sum([safe_float(month.get('demand_kwh', 0), 0) for month in monthly_balance])
    annual_generation = sum([safe_float(month.get('generation_kwh', 0), 0) for month in monthly_balance])
    annual_savings = sum([safe_float(month.get('cost_savings_eur', 0), 0) for month in monthly_balance])
    annual_revenue = sum([safe_float(month.get('feed_in_revenue_eur', 0), 0) for month in monthly_balance])
    
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
    
    # Handle DataFrame case for solutions
    if hasattr(solutions, 'to_dict'):
        solutions = solutions.to_dict('records')
    
    if not solutions or len(solutions) == 0:
        return {
            'solution_count': 0,
            'best_cost': 0,
            'best_yield': 0,
            'best_roi': 0,
            'weights': {}
        }
    
    costs = [safe_float(sol.get('cost', sol.get('total_cost', 0)), 0) for sol in solutions]
    yields = [safe_float(sol.get('yield', sol.get('annual_yield', 0)), 0) for sol in solutions]
    rois = [safe_float(sol.get('roi', 0), 0) for sol in solutions]
    
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
    
    # Debug: Show available financial data structure
    print(f"DEBUG - Available financial keys: {list(financial.keys()) if financial else 'None'}")
    
    # Try multiple data source locations for financial metrics
    financial_metrics = financial.get('financial_metrics', {})
    environmental_impact = financial.get('environmental_impact', {})
    
    # Primary data sources (direct field names as saved by financial analysis)
    npv = (
        safe_float(financial.get('npv'), None) or
        safe_float(financial_metrics.get('npv'), None) or
        safe_float(project_data.get('npv'), 0)
    )
    
    irr = (
        safe_float(financial.get('irr'), None) or
        safe_float(financial_metrics.get('irr'), None) or
        safe_float(project_data.get('irr'), 0)
    )
    
    payback = (
        safe_float(financial.get('payback_period'), None) or
        safe_float(financial_metrics.get('payback_period'), None) or
        safe_float(project_data.get('payback_period'), 0)
    )
    
    annual_savings = (
        safe_float(financial.get('annual_savings'), None) or
        safe_float(financial_metrics.get('annual_savings'), None) or
        safe_float(project_data.get('annual_savings'), 0)
    )
    
    # Investment cost from multiple field names
    investment_cost = (
        safe_float(financial.get('initial_investment'), None) or
        safe_float(financial.get('total_investment'), None) or
        safe_float(financial_metrics.get('total_investment'), None) or
        safe_float(project_data.get('initial_investment'), 0)
    )
    
    # Environmental data from direct field names  
    annual_co2 = (
        safe_float(financial.get('co2_savings_annual'), None) or
        safe_float(environmental_impact.get('annual_co2_savings'), None) or
        safe_float(project_data.get('co2_savings_annual'), 0)
    )
    
    lifetime_co2 = (
        safe_float(financial.get('co2_savings_lifetime'), None) or
        safe_float(environmental_impact.get('lifetime_co2_savings'), None) or
        safe_float(project_data.get('co2_savings_lifetime'), 0)
    )
    
    # System capacity
    system_capacity = (
        safe_float(financial.get('system_capacity'), None) or
        safe_float(project_data.get('system_capacity'), 0)
    )
    
    print(f"DEBUG Step 9 - NPV: {npv}, IRR: {irr}, Payback: {payback}")
    print(f"DEBUG Step 9 - Annual Savings: {annual_savings}, Investment: {investment_cost}")
    print(f"DEBUG Step 9 - CO2 Annual: {annual_co2}, CO2 Lifetime: {lifetime_co2}")
    
    return {
        'npv': npv if npv is not None else 0,
        'irr': irr if irr is not None else 0,
        'payback_period': payback if payback is not None else 0,
        'annual_savings': annual_savings if annual_savings is not None else 0,
        'investment_cost': investment_cost if investment_cost is not None else 0,
        'annual_co2_savings': annual_co2 if annual_co2 is not None else 0,
        'lifetime_co2_savings': lifetime_co2 if lifetime_co2 is not None else 0,
        'system_capacity': system_capacity if system_capacity is not None else 0
    }
        'installation_cost': safe_float(financial.get('installation_cost', 0), 0),
        'annual_co2_savings': safe_float(financial.get('annual_co2_savings', 0), 0),
        'lifetime_co2_savings': safe_float(financial.get('lifetime_co2_savings', 0), 0)
    }