"""
Energy calculation engine for Step 7 Yield vs Demand Analysis
"""

import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime as dt
from database_manager import db_manager


def safe_float(value, default=0.0):
    """Safely convert value to float."""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def calculate_monthly_demand(project_id, historical_data):
    """
    Calculate monthly energy demand from historical data and forecasts.
    
    Returns:
        dict: Monthly demand data with baseline consumption
    """
    try:
        # Extract consumption data
        consumption_data = historical_data.get('consumption_data', {})
        forecast_data = historical_data.get('forecast_data', [])
        
        # Get average monthly consumption
        avg_consumption = safe_float(consumption_data.get('avg_monthly_consumption', 0))
        annual_consumption = safe_float(consumption_data.get('annual_consumption', 0))
        consumption_pattern = consumption_data.get('consumption_pattern', [])
        
        if avg_consumption <= 0 and annual_consumption > 0:
            avg_consumption = annual_consumption / 12
        
        if avg_consumption > 0:
            # Use actual monthly consumption pattern if available
            if consumption_pattern and len(consumption_pattern) >= 12:
                monthly_demand = consumption_pattern[:12]
            elif forecast_data and len(forecast_data) >= 12:
                monthly_demand = forecast_data[:12]
            else:
                # Apply realistic seasonal factors for educational buildings
                seasonal_factors = [1.1, 1.0, 0.9, 0.8, 0.7, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]
                monthly_demand = [float(avg_consumption) * factor for factor in seasonal_factors]
            
            return {
                'avg_consumption': avg_consumption,
                'total_consumption': sum(monthly_demand),
                'monthly_demand': monthly_demand,
                'is_valid': True
            }
        else:
            return {
                'avg_consumption': 0,
                'total_consumption': 0,
                'monthly_demand': [0] * 12,
                'is_valid': False,
                'error': "No valid consumption data available"
            }
            
    except Exception as e:
        return {
            'avg_consumption': 0,
            'total_consumption': 0,
            'monthly_demand': [0] * 12,
            'is_valid': False,
            'error': f"Calculation error: {str(e)}"
        }


def calculate_pv_yields(project_id, pv_specs, tmy_data, environmental_factors=None):
    """
    Calculate PV energy yields using authentic TMY data and environmental factors.
    
    Returns:
        dict: Yield profiles and summary data
    """
    try:
        if pv_specs is None or len(pv_specs) == 0:
            return {'yield_profiles': [], 'total_annual_yield': 0, 'is_valid': False}
        
        yield_profiles = []
        total_annual_yield = 0
        
        # Get environmental shading factor
        shading_reduction = 0
        if environmental_factors:
            shading_reduction = environmental_factors.get('shading_reduction', 0)
        shading_factor = 1 - (shading_reduction / 100)
        
        # Calculate annual TMY radiation if available
        tmy_annual_ghi = 0
        if tmy_data and len(tmy_data) > 0:
            tmy_annual_ghi = sum(
                record.get('ghi', record.get('GHI_Wm2', record.get('GHI', 0))) 
                for record in tmy_data
            ) / 1000  # Convert to kWh/m²/year
        
        # Process each PV system
        for idx, (_, system) in enumerate(pv_specs.iterrows()):
            capacity_kw = safe_float(system.get('capacity_kw', 0))
            glass_area = safe_float(system.get('glass_area_m2', system.get('bipv_area_m2', 1.5)))
            efficiency = safe_float(system.get('efficiency', 0.08))
            
            # Calculate realistic annual energy
            performance_ratio = 0.85  # Typical for BIPV systems
            
            if tmy_annual_ghi > 100:  # Valid TMY data
                annual_radiation = tmy_annual_ghi
            else:
                annual_radiation = 1200  # Fallback for Central Europe
            
            # Energy = Area × Efficiency × Solar Radiation × Performance Ratio × Environmental Shading
            annual_energy = glass_area * efficiency * annual_radiation * performance_ratio * shading_factor
            
            # Calculate capacity if missing
            if capacity_kw <= 0:
                capacity_kw = glass_area * efficiency
            
            # Calculate specific yield
            specific_yield = annual_energy / capacity_kw if capacity_kw > 0 else 0
            
            # Calculate monthly distribution (simplified seasonal pattern)
            monthly_distribution = [0.03, 0.05, 0.08, 0.11, 0.14, 0.15, 0.14, 0.12, 0.09, 0.06, 0.03, 0.02]
            monthly_yields = [annual_energy * factor for factor in monthly_distribution]
            
            system_data = {
                'element_id': system.get('element_id', f'System_{idx+1}'),
                'capacity_kw': capacity_kw,
                'annual_yield': annual_energy,
                'specific_yield': specific_yield,
                'monthly_yields': monthly_yields,
                'environmental_shading_reduction': shading_reduction,
                'shading_factor': shading_factor,
                'glass_area': glass_area,
                'efficiency': efficiency
            }
            
            yield_profiles.append(system_data)
            total_annual_yield += annual_energy
        
        return {
            'yield_profiles': yield_profiles,
            'total_annual_yield': total_annual_yield,
            'total_capacity_kw': sum(profile['capacity_kw'] for profile in yield_profiles),
            'average_specific_yield': np.mean([p['specific_yield'] for p in yield_profiles]) if yield_profiles else 0,
            'is_valid': True
        }
        
    except Exception as e:
        return {
            'yield_profiles': [],
            'total_annual_yield': 0,
            'is_valid': False,
            'error': f"Yield calculation error: {str(e)}"
        }


def calculate_energy_balance(demand_data, yield_data, electricity_rates):
    """
    Calculate comprehensive energy balance including financial metrics.
    
    Returns:
        dict: Complete energy balance analysis
    """
    try:
        if not demand_data['is_valid'] or not yield_data['is_valid']:
            return {'is_valid': False, 'error': "Invalid input data"}
        
        monthly_demand = demand_data['monthly_demand']
        yield_profiles = yield_data['yield_profiles']
        
        # Calculate monthly totals
        monthly_yield_totals = [0] * 12
        for profile in yield_profiles:
            monthly_yields = profile['monthly_yields']
            for month in range(12):
                monthly_yield_totals[month] += monthly_yields[month]
        
        # Calculate energy balance for each month
        energy_balance = []
        total_annual_savings = 0
        total_feed_in = 0
        
        import_rate = electricity_rates.get('import_rate', 0.25)
        export_rate = electricity_rates.get('export_rate', 0.08)
        
        for month in range(12):
            demand = monthly_demand[month]
            generation = monthly_yield_totals[month]
            
            # Calculate net energy flows
            net_import = max(0, demand - generation)
            surplus_export = max(0, generation - demand)
            self_consumption = min(demand, generation)
            
            # Calculate financial impacts
            electricity_cost_savings = self_consumption * import_rate
            feed_in_revenue = surplus_export * export_rate
            monthly_savings = electricity_cost_savings + feed_in_revenue
            
            month_data = {
                'month': month + 1,
                'demand_kwh': demand,
                'generation_kwh': generation,
                'net_import_kwh': net_import,
                'surplus_export_kwh': surplus_export,
                'self_consumption_kwh': self_consumption,
                'self_consumption_ratio': self_consumption / demand if demand > 0 else 0,
                'electricity_cost_savings': electricity_cost_savings,
                'feed_in_revenue': feed_in_revenue,
                'total_monthly_savings': monthly_savings
            }
            
            energy_balance.append(month_data)
            total_annual_savings += monthly_savings
            total_feed_in += feed_in_revenue
        
        # Calculate annual summary metrics
        annual_demand = sum(monthly_demand)
        annual_generation = sum(monthly_yield_totals)
        coverage_ratio = (annual_generation / annual_demand * 100) if annual_demand > 0 else 0
        
        return {
            'energy_balance': energy_balance,
            'annual_demand': annual_demand,
            'annual_generation': annual_generation,
            'coverage_ratio': coverage_ratio,
            'total_annual_savings': total_annual_savings,
            'total_feed_in_revenue': total_feed_in,
            'average_monthly_savings': total_annual_savings / 12,
            'is_valid': True
        }
        
    except Exception as e:
        return {
            'is_valid': False,
            'error': f"Energy balance calculation error: {str(e)}"
        }


def save_analysis_results(project_id, analysis_data, config):
    """Save analysis results to database."""
    try:
        # Prepare data for database storage
        analysis_record = {
            'project_id': project_id,
            'analysis_date': dt.now(),
            'energy_balance': analysis_data,
            'configuration': config,
            'total_annual_yield': analysis_data.get('annual_generation', 0),
            'total_annual_demand': analysis_data.get('annual_demand', 0),
            'coverage_ratio': analysis_data.get('coverage_ratio', 0),
            'annual_savings': analysis_data.get('total_annual_savings', 0)
        }
        
        # Save to database
        db_manager.save_energy_analysis(project_id, analysis_record)
        
        # Save to consolidated data manager for workflow integration
        from utils.database_helper import db_helper
        db_helper.save_step_data(project_id, 7, {
            'energy_balance': analysis_data,
            'analysis_config': config,
            'calculation_timestamp': dt.now().isoformat()
        })
        
        return True
        
    except Exception as e:
        st.error(f"Failed to save analysis results: {str(e)}")
        return False