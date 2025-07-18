"""
Yield vs Demand Analysis page for BIPV Optimizer - Refactored Modular Architecture
"""

import streamlit as st
from datetime import datetime as dt
from database_manager import db_manager

# Import modular components
from .step7_yield_demand import (
    get_validated_project_data,
    calculate_monthly_demand,
    calculate_pv_yields,
    calculate_energy_balance,
    save_analysis_results,
    render_step7_header,
    render_data_usage_info,
    render_analysis_configuration,
    render_environmental_factors,
    render_analysis_results,
    render_data_export,
    render_step_report_download
)


def render_yield_demand():
    """
    Render the yield vs demand analysis module - Refactored with modular architecture.
    
    This function orchestrates the entire Step 7 workflow using modular components:
    - Data validation and dependency checking
    - Analysis configuration
    - Energy calculations with caching
    - Results visualization
    - Data export functionality
    """
    
    # 1. Render header and introduction
    render_step7_header()
    
    # 2. Validate dependencies and get project data
    project_id, project_data, validation_passed = get_validated_project_data()
    
    if not validation_passed:
        return
    
    # 3. Render data usage information
    render_data_usage_info()
    
    # 4. Get analysis configuration from user
    config = render_analysis_configuration()
    
    # 5. Display environmental factors from Step 3
    environmental_factors = render_environmental_factors(project_data)
    
    # 6. Analysis execution
    st.subheader("🔄 Energy Balance Analysis")
    
    if st.button("🚀 Run Yield vs Demand Analysis", type="primary"):
        with st.spinner("Calculating energy balance..."):
            try:
                # Get historical data for demand calculations
                historical_data = db_manager.get_historical_data(project_id)
                
                # Get PV specifications from Step 6
                pv_specs = db_manager.get_pv_specifications(project_id)
                
                # Get TMY data from Step 3
                tmy_data = project_data.get('weather_analysis', {}).get('tmy_data', [])
                
                # Get electricity rates from Step 1
                electricity_rates = project_data.get('electricity_rates', {
                    'import_rate': config['electricity_price'],
                    'export_rate': config['feed_in_tariff']
                })
                
                # Calculate monthly demand
                st.info("📊 Calculating monthly energy demand...")
                demand_data = calculate_monthly_demand(project_id, historical_data)
                
                if not demand_data['is_valid']:
                    st.error(f"❌ Demand calculation failed: {demand_data.get('error', 'Unknown error')}")
                    return
                
                # Calculate PV yields
                st.info("☀️ Calculating PV energy yields...")
                yield_data = calculate_pv_yields(project_id, pv_specs, tmy_data, environmental_factors)
                
                if not yield_data['is_valid']:
                    st.error(f"❌ Yield calculation failed: {yield_data.get('error', 'Unknown error')}")
                    return
                
                # Calculate energy balance
                st.info("⚖️ Calculating energy balance...")
                balance_data = calculate_energy_balance(demand_data, yield_data, electricity_rates)
                
                if not balance_data['is_valid']:
                    st.error(f"❌ Energy balance calculation failed: {balance_data.get('error', 'Unknown error')}")
                    return
                
                # Save results to database
                st.info("💾 Saving analysis results...")
                if save_analysis_results(project_id, balance_data, config):
                    st.success("✅ Analysis completed successfully!")
                    
                    # Store results for display
                    st.session_state['step7_analysis_data'] = balance_data
                    st.session_state['step7_config'] = config
                    st.session_state['step7_yield_data'] = yield_data
                else:
                    st.error("❌ Failed to save analysis results")
                    return
                
            except Exception as e:
                st.error(f"❌ Analysis failed: {str(e)}")
                return
    
    # 7. Display results if available
    if 'step7_analysis_data' in st.session_state:
        analysis_data = st.session_state['step7_analysis_data']
        config = st.session_state.get('step7_config', {})
        
        render_analysis_results(analysis_data)
        render_data_export(analysis_data, config)
    
    # 8. Individual step report download
    render_step_report_download()