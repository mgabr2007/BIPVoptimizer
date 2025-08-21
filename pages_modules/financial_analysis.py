"""
Financial & Environmental Analysis page for BIPV Optimizer
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from database_manager import db_manager
from utils.database_helper import db_helper
from core.solar_math import safe_divide
from core.carbon_factors import get_grid_carbon_factor, display_carbon_factor_info
# Removed ConsolidatedDataManager - using database-only approach
# Removed session state dependency - using database-only approach

def calculate_npv(cash_flows, discount_rate):
    """Calculate Net Present Value of cash flows."""
    npv = 0
    for i, cash_flow in enumerate(cash_flows):
        npv += cash_flow / ((1 + discount_rate) ** i)
    return npv

def calculate_irr(cash_flows, max_iterations=1000, tolerance=1e-6):
    """Calculate Internal Rate of Return using Newton-Raphson method."""
    if len(cash_flows) < 2:
        return None
    
    # Initial guess
    rate = 0.1
    
    for _ in range(max_iterations):
        # Calculate NPV and its derivative
        npv = sum(cf / ((1 + rate) ** i) for i, cf in enumerate(cash_flows))
        npv_derivative = sum(-i * cf / ((1 + rate) ** (i + 1)) for i, cf in enumerate(cash_flows))
        
        if abs(npv) < tolerance:
            return rate
        
        if abs(npv_derivative) < tolerance:
            break
        
        # Newton-Raphson iteration
        rate = rate - npv / npv_derivative
        
        # Ensure rate stays reasonable
        if rate < -0.99 or rate > 10:
            return None
    
    return rate if abs(npv) < tolerance else None

def calculate_payback_period(cash_flows):
    """Calculate simple payback period."""
    if len(cash_flows) < 2:
        return None
    
    cumulative = 0
    for i, cash_flow in enumerate(cash_flows):
        cumulative += cash_flow
        if cumulative >= 0:
            if i == 0:
                return 0
            else:
                # Interpolate between years with zero check
                denominator = cash_flows[i-1] - cash_flow
                if abs(denominator) < 1e-10:  # Near zero check
                    return i - 1
                return i - 1 + (cash_flows[i-1] / denominator)
    
    return None  # Never pays back

def calculate_co2_savings(annual_energy_kwh, grid_co2_factor, system_lifetime):
    """Calculate CO2 emissions savings."""
    # CO2 savings per year (kg)
    annual_co2_savings = annual_energy_kwh * grid_co2_factor
    
    # Lifetime CO2 savings (tons)
    lifetime_co2_savings = (annual_co2_savings * system_lifetime) / 1000
    
    return annual_co2_savings, lifetime_co2_savings

def create_cash_flow_analysis(solution_data, financial_params, system_lifetime):
    """Create detailed cash flow analysis for a solution."""
    
    # Handle different key names for cost
    initial_cost = solution_data.get('total_investment', solution_data.get('total_cost', 0))
    annual_energy = solution_data.get('annual_energy_kwh', solution_data.get('annual_energy', 0))
    
    # Financial parameters
    discount_rate = financial_params['discount_rate']
    electricity_price = financial_params['electricity_price']
    price_escalation = financial_params.get('price_escalation', 0.02)
    maintenance_cost_rate = financial_params.get('maintenance_cost_rate', 0.01)
    inverter_replacement_year = financial_params.get('inverter_replacement_year', 12)
    inverter_replacement_cost = financial_params.get('inverter_replacement_cost_ratio', 0.15)
    
    # Incentives
    tax_credit = financial_params.get('tax_credit', 0.0)
    rebate_amount = financial_params.get('rebate_amount', 0.0)
    
    cash_flows = []
    annual_details = []
    
    for year in range(system_lifetime + 1):
        if year == 0:
            # Initial investment with incentives
            net_investment = initial_cost - rebate_amount - (initial_cost * tax_credit)
            cash_flow = -net_investment
        else:
            # Annual benefits
            escalated_price = electricity_price * ((1 + price_escalation) ** (year - 1))
            annual_savings = annual_energy * escalated_price
            
            # Annual costs
            maintenance_cost = initial_cost * maintenance_cost_rate
            
            # Inverter replacement
            inverter_cost = 0
            if year == inverter_replacement_year:
                inverter_cost = initial_cost * inverter_replacement_cost
            
            cash_flow = annual_savings - maintenance_cost - inverter_cost
        
        cash_flows.append(cash_flow)
        
        annual_details.append({
            'year': year,
            'cash_flow': cash_flow,
            'cumulative_cash_flow': sum(cash_flows),
            'annual_savings': annual_savings if year > 0 else 0,
            'maintenance_cost': maintenance_cost if year > 0 else 0,
            'inverter_cost': inverter_cost if year > 0 else 0
        })
    
    return cash_flows, annual_details

def render_financial_analysis():
    """Render the financial and environmental analysis module."""
    
    # Add OptiSunny character header image
    st.image("attached_assets/step09_1751436847831.png", width=400)
    
    st.header("💰 Step 9: Financial & Environmental Impact Analysis for Selected Windows")
    
    # Check prerequisites and ensure project data is loaded
    from services.io import get_current_project_id, ensure_project_data_loaded
    
    if not ensure_project_data_loaded():
        st.error("⚠️ No project found. Please complete Step 1 (Project Setup) first.")
        return
    
    project_id = get_current_project_id()
    
    # AI Model Performance Impact Notice
    # Get project data from database only
    project_data = db_manager.get_project_by_id(project_id) or {}
    if project_data.get('model_r2_score') is not None:
        r2_score = project_data['model_r2_score']
        status = project_data.get('model_performance_status', 'Unknown')
        
        if r2_score >= 0.85:
            color = "green"
            icon = "🟢"
        elif r2_score >= 0.70:
            color = "orange"
            icon = "🟡"
        else:
            color = "red"
            icon = "🔴"
        
        st.info(f"{icon} Financial analysis uses AI demand predictions (R² score: **{r2_score:.3f}** - {status} performance)")
        
        # Removed persistent warning message
    
    # Check dependencies - check database for optimization results
    optimization_data = db_manager.get_optimization_results(project_id)
    if not optimization_data:
        st.error("⚠️ Optimization results required. Please complete Step 8 (Multi-Objective Optimization) first.")
        return
    
    # Extract solutions from optimization data
    solutions = optimization_data.get('solutions')
    

    
    if solutions is None or (hasattr(solutions, 'empty') and solutions.empty) or (hasattr(solutions, '__len__') and len(solutions) == 0):
        st.error("⚠️ No optimization solutions available.")
        return
        
    # Load project data for other settings
    project_data = db_manager.get_project_by_id(project_id) or {}
    
    # Check if solution is selected - for now use the best solution (highest ROI)
    if hasattr(solutions, 'iloc') and len(solutions) > 0:
        # Use the best solution (first one, sorted by ROI in Step 8)
        selected_solution = solutions.iloc[0]
        st.success(f"✅ Using best optimization solution: {selected_solution['solution_id']}")
    else:
        st.error("⚠️ No optimization solutions available.")
        return
    
    st.success(f"✅ Analyzing financial performance of {selected_solution['solution_id']} for selected window types")
    st.info("💡 Financial analysis based on selected window types from Step 4 for accurate ROI calculations")
    
    # Get electricity rates for display (define at top level) - ensure it's a dict
    electricity_rates_raw = project_data.get('electricity_rates', {})
    
    if isinstance(electricity_rates_raw, str):
        try:
            import json
            electricity_rates = json.loads(electricity_rates_raw)
        except:
            electricity_rates = {'import_rate': 0.25, 'source': 'fallback'}
    else:
        electricity_rates = electricity_rates_raw or {'import_rate': 0.25, 'source': 'fallback'}
    
    # If no rates found in current project, check session state as backup
    if not electricity_rates or electricity_rates.get('import_rate') in [0.25, None]:
        if 'electricity_rates' in st.session_state:
            session_rates = st.session_state['electricity_rates']
            st.warning(f"⚠️ Using rates from session state: {session_rates.get('import_rate', 'N/A')} €/kWh")
            electricity_rates = session_rates
    
    # Add manual override option if rates don't match expected values
    st.subheader("⚙️ Electricity Rate Override")
    
    current_rate = electricity_rates.get('import_rate', 0.25)
    
    # Allow manual override
    override_rate = st.number_input(
        "Override Electricity Rate (€/kWh)",
        min_value=0.01,
        max_value=1.00,
        value=current_rate,
        step=0.001,
        format="%.3f",
        help="If the auto-loaded rate is incorrect, you can override it here. This will be used for all financial calculations.",
        key="override_electricity_rate"
    )
    
    # Update electricity_rates if overridden
    if override_rate != current_rate:
        electricity_rates = {
            'import_rate': override_rate,
            'source': f'Manual Override (was {current_rate:.3f})',
            'timestamp': 'now'
        }
        st.success(f"✅ Using override rate: {override_rate:.3f} €/kWh")
    
    # Show automatically loaded data
    st.subheader("📊 Auto-Loaded Project Data")
    
    auto_col1, auto_col2 = st.columns(2)
    
    with auto_col1:
        rate_value = electricity_rates.get('import_rate', 0.25)
        rate_source = electricity_rates.get('source', 'manual')
        location = project_data.get('location_name', project_data.get('location', 'Not set'))
        
        st.info(f"**💰 Electricity Rate:** {rate_value:.3f} €/kWh\n"
                f"**📍 Location:** {location}\n"
                f"**⚡ Rate Source:** {rate_source}")
    
    with auto_col2:
        # Use the selected_solution from optimization results (already a pandas Series)
        if selected_solution is not None:
            # Convert Series to dict for consistent access
            solution_dict = selected_solution.to_dict() if hasattr(selected_solution, 'to_dict') else selected_solution
            
            total_cost = float(solution_dict.get('total_cost', 0))
            capacity = float(solution_dict.get('capacity', 0))
            roi = float(solution_dict.get('roi', 0))
            
            st.info(f"**💼 System Cost:** €{total_cost:,.0f}\n"
                    f"**⚡ Capacity:** {capacity:.1f} kW\n"
                    f"**📈 ROI:** {roi:.1f}%\n"
                    f"**🎯 Solution:** {solution_dict.get('solution_id', 'Selected')}")
    
    # Financial configuration
    st.subheader("🔧 Financial Analysis Configuration")
    st.markdown("**Adjust the parameters below based on your specific project requirements:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**System Parameters**")
        system_lifetime = st.number_input(
            "System Lifetime (years)",
            15, 30, 25, 1,
            key="system_lifetime_fin"
        )
        
        discount_rate = st.slider(
            "Discount Rate (%)",
            1.0, 8.0, 4.0, 0.5,
            help="Cost of capital for NPV calculations",
            key="discount_rate_fin"
        )
        
        # Get electricity price from Step 1 project setup (database only) - already loaded above
        default_price = electricity_rates.get('import_rate', 0.25)
        
        electricity_price = st.number_input(
            "Financial Analysis Electricity Price (€/kWh)",
            0.01, 1.00, default_price, 0.001,
            format="%.3f",
            help=f"💡 Rate from database: {default_price:.3f} €/kWh. Adjust if needed for financial calculations.",
            key="electricity_price_fin"
        )
        
        # Show data source
        rate_source = electricity_rates.get('source', 'manual_input')
        if isinstance(rate_source, str) and rate_source.startswith('live_api'):
            st.info(f"📡 Using live rate from {rate_source.replace('live_api_', '').upper()} API")
        else:
            st.info(f"📊 Using rate from Step 1 configuration")
    
    with col2:
        st.markdown("**Economic Assumptions**")
        price_escalation = st.slider(
            "Annual Price Escalation (%)",
            0.0, 5.0, 2.0, 0.5,
            help="Expected annual increase in electricity prices",
            key="price_escalation_fin"
        )
        
        maintenance_cost_rate = st.slider(
            "Annual Maintenance Cost (%)",
            0.5, 3.0, 1.0, 0.1,
            help="Maintenance cost as % of initial investment",
            key="maintenance_cost_fin"
        )
        
        system_degradation = st.slider(
            "Annual Performance Degradation (%)",
            0.3, 0.8, 0.5, 0.1,
            help="Annual decrease in system performance",
            key="degradation_fin"
        )
    
    # Incentives and costs
    with st.expander("💸 Incentives & Additional Costs", expanded=False):
        inc_col1, inc_col2 = st.columns(2)
        
        with inc_col1:
            tax_credit = st.slider(
                "Tax Credit (%)",
                0.0, 50.0, 0.0, 5.0,
                help="Tax credit as % of system cost",
                key="tax_credit_fin"
            )
            
            rebate_amount = st.number_input(
                "Direct Rebate (€)",
                0, 50000, 0, 500,
                help="Direct cash rebate from government/utility",
                key="rebate_amount_fin"
            )
        
        with inc_col2:
            inverter_replacement_year = st.number_input(
                "Inverter Replacement Year",
                8, 20, 12, 1,
                help="Year when inverter replacement is needed",
                key="inverter_replacement_year_fin"
            )
            
            inverter_replacement_cost_ratio = st.slider(
                "Inverter Replacement Cost (%)",
                10.0, 25.0, 15.0, 1.0,
                help="Replacement cost as % of initial investment",
                key="inverter_replacement_cost_fin"
            )
    
    # Environmental parameters
    st.subheader("🌱 Environmental Impact Parameters")
    
    env_col1, env_col2 = st.columns(2)
    
    with env_col1:
        # Get location-based CO₂ factor using comprehensive database
        location_name = project_data.get('location_name', '')
        coordinates = project_data.get('coordinates', {})
        
        # Get carbon factor data with sources
        carbon_data = get_grid_carbon_factor(location_name, coordinates)
        default_co2 = carbon_data['factor']
        
        st.markdown("**Grid CO₂ Emissions Factor**")
        grid_co2_factor = st.number_input(
            "Grid CO₂ Factor (kg CO₂/kWh)",
            0.020, 0.900, default_co2, 0.001,
            help="CO₂ emissions per kWh of grid electricity. Used to calculate environmental impact of BIPV generation.",
            key="grid_co2_fin"
        )
        
        # Add refresh button for live data
        col_info, col_refresh = st.columns([3, 1])
        with col_info:
            # Display source information
            display_carbon_factor_info(carbon_data)
        with col_refresh:
            if st.button("🔄 Refresh", help="Update carbon factor with latest live data", key="refresh_carbon"):
                # Force refresh by clearing cache and reloading
                st.cache_data.clear()
                st.rerun()
    
    with env_col2:
        carbon_price = st.number_input(
            "Carbon Price (€/ton CO₂)",
            20, 100, 50, 5,
            help="💰 Current or projected carbon pricing for emissions trading. EU ETS: 50-100 €/ton CO₂, Social Cost of Carbon: 51 €/ton, Voluntary markets: 20-40 €/ton. This monetizes the environmental benefit of CO₂ savings from BIPV generation.",
            key="carbon_price_fin"
        )
    
    # How This Data Will Be Used section
    with st.expander("📋 How This Data Will Be Used", expanded=False):
        st.markdown("""
        **Financial Analysis Workflow:**
        
        **📊 Auto-Loaded Data:**
        - **Electricity Rates**: From Step 1 location configuration (live API or manual input)
        - **System Cost**: From Step 8 selected optimization solution
        - **Annual Energy**: From Step 7 yield vs demand analysis
        - **Location**: For CO₂ factor determination and regional parameters
        
        **💰 Financial Calculations:**
        - **NPV**: Net Present Value using discounted cash flows over system lifetime
        - **IRR**: Internal Rate of Return using Newton-Raphson method
        - **Payback Period**: Simple payback based on annual savings
        - **Cash Flow**: Year-by-year financial projections with maintenance and replacement costs
        
        **🌱 Environmental Impact:**
        - **CO₂ Factor Sources**: Official national grid data (TSOs, regulators), IEA estimates, or IPCC regional averages
        - **Fallback Methodology**: Coordinates-based regional estimates when country-specific data unavailable
        - **CO₂ Savings**: Annual emissions avoided (kWh × location-specific CO₂ factor)
        - **Carbon Value**: Monetary value of emissions reduction using market carbon pricing
        - **Lifetime Impact**: 25-year environmental benefit calculation with data source transparency
        
        **📈 Output for Next Steps:**
        - **Step 10**: Financial results integrated into comprehensive project reports
        - **Step 11**: AI consultation uses financial metrics for optimization recommendations
        - **Database**: All calculations saved for project persistence and comparison
        """)
    
    # Analysis execution
    if st.button("🚀 Run Financial & Environmental Analysis", key="run_financial_analysis"):
        with st.spinner("Calculating financial performance and environmental impact..."):
            try:
                # Setup financial parameters
                financial_params = {
                    'discount_rate': discount_rate / 100,
                    'electricity_price': electricity_price,
                    'price_escalation': price_escalation / 100,
                    'maintenance_cost_rate': maintenance_cost_rate / 100,
                    'inverter_replacement_year': inverter_replacement_year,
                    'inverter_replacement_cost_ratio': inverter_replacement_cost_ratio / 100,
                    'tax_credit': tax_credit / 100,
                    'rebate_amount': rebate_amount,
                    'system_degradation': system_degradation / 100
                }
                
                # Create cash flow analysis - convert Series to dict
                solution_dict = selected_solution.to_dict() if hasattr(selected_solution, 'to_dict') else selected_solution
                cash_flows, annual_details = create_cash_flow_analysis(
                    solution_dict, financial_params, system_lifetime
                )
                
                # Calculate financial metrics
                npv = calculate_npv(cash_flows, financial_params['discount_rate'])
                irr = calculate_irr(cash_flows)
                payback_period = calculate_payback_period(cash_flows)
                
                # Calculate environmental impact - get annual energy from multiple possible sources
                annual_energy_kwh = (
                    solution_dict.get('annual_energy_kwh') or 
                    solution_dict.get('annual_energy') or 
                    solution_dict.get('capacity', 0) * 1200  # Fallback: capacity * average solar hours
                )
                
                # Ensure we have valid energy data
                if annual_energy_kwh == 0:
                    st.error("⚠️ No annual energy data found in solution. Please complete Step 7 (Yield vs Demand Analysis) first.")
                    return
                
                annual_co2_savings, lifetime_co2_savings = calculate_co2_savings(
                    annual_energy_kwh, grid_co2_factor, system_lifetime
                )
                
                # Calculate carbon value
                carbon_value = lifetime_co2_savings * carbon_price
                
                # Sensitivity analysis
                # Get system cost from solution data
                system_cost = solution_dict.get('total_cost', solution_dict.get('total_investment', 0))
                
                sensitivity_ranges = {
                    'electricity_price': np.linspace(electricity_price * 0.8, electricity_price * 1.2, 5),
                    'discount_rate': np.linspace(max(0.01, (discount_rate/100) * 0.5), (discount_rate/100) * 1.5, 5),
                    'system_cost': np.linspace(system_cost * 0.8, system_cost * 1.2, 5)
                }
                
                sensitivity_results = {}
                for param, values in sensitivity_ranges.items():
                    npv_values = []
                    for value in values:
                        temp_params = financial_params.copy()
                        temp_solution = solution_dict.copy()
                        
                        if param == 'electricity_price':
                            temp_params['electricity_price'] = value
                        elif param == 'discount_rate':
                            temp_params['discount_rate'] = value
                        elif param == 'system_cost':
                            temp_solution['total_cost'] = value
                            temp_solution['total_investment'] = value  # Support both keys
                        
                        temp_cash_flows, _ = create_cash_flow_analysis(temp_solution, temp_params, system_lifetime)
                        temp_npv = calculate_npv(temp_cash_flows, temp_params['discount_rate'])
                        npv_values.append(temp_npv)
                    
                    sensitivity_results[param] = {'values': values.tolist(), 'npv': npv_values}
                
                # Save results
                total_investment = solution_dict.get('total_cost', solution_dict.get('total_investment', 0))
                annual_savings = solution_dict.get('annual_savings', annual_energy_kwh * electricity_price)
                
                financial_analysis_results = {
                    'financial_metrics': {
                        'npv': npv,
                        'irr': irr * 100 if irr else None,
                        'payback_period': payback_period,
                        'total_investment': total_investment,
                        'annual_savings': annual_savings,
                        'lifetime_savings': sum(cash_flows[1:])  # Exclude initial investment
                    },
                    'environmental_impact': {
                        'annual_co2_savings': annual_co2_savings,
                        'lifetime_co2_savings': lifetime_co2_savings,
                        'carbon_value': carbon_value,
                        'grid_co2_factor': grid_co2_factor
                    },
                    'cash_flow_analysis': annual_details,
                    'sensitivity_analysis': sensitivity_results,
                    'analysis_parameters': financial_params
                }
                
                # Save financial analysis to database only
                db_manager.save_financial_analysis(project_id, financial_analysis_results)
                
                # Database save completed above
                step9_data = {
                    'financial_analysis': financial_analysis_results,
                    'cash_flow_analysis': annual_details,
                    'environmental_impact': {
                        'annual_co2_savings': annual_co2_savings,
                        'lifetime_co2_savings': lifetime_co2_savings,
                        'carbon_value': carbon_value,
                        'grid_co2_factor': grid_co2_factor
                    },
                    'economic_metrics': {
                        'npv': npv,
                        'irr': irr * 100 if irr else None,
                        'payback_period': payback_period,
                        'total_investment': total_investment,
                        'annual_savings': annual_savings,
                        'lifetime_savings': sum(cash_flows[1:])  # Exclude initial investment
                    },
                    'financial_complete': True
                }
                # Data saved to database above - no consolidated manager needed
                
                # Save to database
                if project_id:
                    try:
                        # Prepare database-compatible financial data structure
                        db_financial_data = {
                            'initial_investment': total_investment,
                            'annual_savings': annual_savings,
                            'annual_generation': annual_energy_kwh,
                            'annual_export_revenue': 0,  # Calculate based on feed-in tariff if available
                            'annual_om_cost': total_investment * financial_params['maintenance_cost_rate'],
                            'net_annual_benefit': annual_savings,
                            'npv': npv,
                            'irr': irr,
                            'payback_period': payback_period,
                            'lcoe': safe_divide(total_investment, annual_energy_kwh * system_lifetime, 0),
                            'analysis_complete': True,
                            # Environmental impact data for database
                            'co2_savings_annual': annual_co2_savings,
                            'co2_savings_lifetime': lifetime_co2_savings,
                            'carbon_value': carbon_value,
                            'trees_equivalent': int(lifetime_co2_savings / 22),  # Approximate trees equivalent
                            'cars_equivalent': int(lifetime_co2_savings / 4.6)   # Approximate cars equivalent
                        }
                        
                        # Save using database helper
                        db_helper.save_step_data("financial_analysis", db_financial_data)
                        
                        # Legacy save method for compatibility
                        db_manager.save_financial_analysis(
                            project_id,
                            db_financial_data
                        )
                    except Exception as db_error:
                        st.warning(f"Database save failed: {str(db_error)}")
                else:
                    st.warning("Project ID not found - results saved to session only")
                
                st.success("✅ Financial and environmental analysis completed successfully!")
                
                # Store calculated data in session state for immediate tab display
                st.session_state['current_financial_analysis'] = financial_analysis_results
                st.session_state['current_solution_dict'] = solution_dict
                
            except Exception as e:
                st.error(f"Error during financial analysis: {str(e)}")
                return
    
    # Display results if available - use current analysis if just calculated, otherwise from database
    financial_data = st.session_state.get('current_financial_analysis') or db_manager.get_financial_analysis(project_id)
    current_solution = st.session_state.get('current_solution_dict') or (selected_solution.to_dict() if hasattr(selected_solution, 'to_dict') else selected_solution)
    
    if financial_data:
        
        if financial_data:
            st.subheader("📊 Financial Performance Results")
            
            # Key financial metrics
            metrics = financial_data.get('financial_metrics', {})
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                npv = metrics.get('npv', 0)
                st.metric("Net Present Value", f"€{npv:,.0f}", 
                         delta="Positive" if npv > 0 else "Negative")
            
            with col2:
                irr = metrics.get('irr')
                irr_display = f"{irr:.1f}%" if irr else "N/A"
                st.metric("Internal Rate of Return", irr_display)
            
            with col3:
                payback = metrics.get('payback_period')
                payback_display = f"{payback:.1f} years" if payback else "N/A"
                st.metric("Payback Period", payback_display)
            
            with col4:
                lifetime_savings = metrics.get('lifetime_savings', 0)
                st.metric("Lifetime Savings", f"€{lifetime_savings:,.0f}")
            
            # Environmental impact
            st.subheader("🌱 Environmental Impact")
            
            env_data = financial_data.get('environmental_impact', {})
            
            env_col1, env_col2, env_col3 = st.columns(3)
            
            with env_col1:
                annual_co2 = env_data.get('annual_co2_savings', 0)
                st.metric("Annual CO₂ Savings", f"{annual_co2:,.0f} kg")
            
            with env_col2:
                lifetime_co2 = env_data.get('lifetime_co2_savings', 0)
                st.metric("Lifetime CO₂ Savings", f"{lifetime_co2:,.1f} tons")
            
            with env_col3:
                carbon_value = env_data.get('carbon_value', 0)
                st.metric("Carbon Value", f"€{carbon_value:,.0f}")
            
            # Use current solution data if available, otherwise calculate missing fields
            if current_solution and 'annual_energy_kwh' in current_solution:
                solution_dict = current_solution
                st.info("✅ Using calculated solution data from financial analysis")
            else:
                solution_dict = selected_solution.to_dict() if hasattr(selected_solution, 'to_dict') else selected_solution
                
                # Ensure we have annual energy data
                if 'annual_energy_kwh' not in solution_dict and 'annual_energy' not in solution_dict:
                    # Get from database based on capacity
                    capacity = solution_dict.get('capacity', 0)
                    estimated_annual_energy = capacity * 1200  # Conservative estimate: 1200 kWh/kW/year
                    solution_dict['annual_energy_kwh'] = estimated_annual_energy
                    st.info(f"📊 Estimated annual energy: {estimated_annual_energy:,.0f} kWh (capacity × 1200 kWh/kW/year)")
                
                # Ensure we have annual savings
                if 'annual_savings' not in solution_dict:
                    annual_energy = solution_dict.get('annual_energy_kwh', solution_dict.get('annual_energy', 0))
                    estimated_savings = annual_energy * electricity_price
                    solution_dict['annual_savings'] = estimated_savings
                    st.info(f"💰 Estimated annual savings: €{estimated_savings:,.0f} (energy × electricity price)")
            
            # Detailed analysis tabs
            st.subheader("📈 Detailed Financial Analysis")
            
            tab1, tab2, tab3, tab4 = st.tabs(["Cash Flow", "Sensitivity Analysis", "Investment Summary", "Comparative Metrics"])
            
            with tab1:
                # Cash flow visualization
                cash_flow_data = financial_data.get('cash_flow_analysis', [])
                
                if cash_flow_data:
                    cash_flow_df = pd.DataFrame(cash_flow_data)
                    
                    fig_cashflow = go.Figure()
                    
                    fig_cashflow.add_trace(go.Bar(
                        x=cash_flow_df['year'],
                        y=cash_flow_df['cash_flow'],
                        name='Annual Cash Flow',
                        marker_color=['red' if x < 0 else 'green' for x in cash_flow_df['cash_flow']]
                    ))
                    
                    fig_cashflow.add_trace(go.Scatter(
                        x=cash_flow_df['year'],
                        y=cash_flow_df['cumulative_cash_flow'],
                        mode='lines+markers',
                        name='Cumulative Cash Flow',
                        yaxis='y2',
                        line=dict(color='blue')
                    ))
                    
                    fig_cashflow.update_layout(
                        title="Cash Flow Analysis Over System Lifetime",
                        xaxis_title="Year",
                        yaxis_title="Annual Cash Flow (€)",
                        yaxis2=dict(title="Cumulative Cash Flow (€)", overlaying='y', side='right'),
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig_cashflow, use_container_width=True)
                    
                    # Cash flow table
                    st.markdown("**Annual Cash Flow Details:**")
                    st.dataframe(
                        cash_flow_df.round(0),
                        use_container_width=True,
                        column_config={
                            'year': 'Year',
                            'cash_flow': st.column_config.NumberColumn('Cash Flow (€)', format="€%.0f"),
                            'cumulative_cash_flow': st.column_config.NumberColumn('Cumulative (€)', format="€%.0f"),
                            'annual_savings': st.column_config.NumberColumn('Savings (€)', format="€%.0f"),
                            'maintenance_cost': st.column_config.NumberColumn('Maintenance (€)', format="€%.0f"),
                            'inverter_cost': st.column_config.NumberColumn('Inverter (€)', format="€%.0f")
                        }
                    )
                else:
                    st.info("Cash flow data not available. Please run financial analysis first.")
            
            with tab2:
                # Sensitivity analysis
                sensitivity_data = financial_data.get('sensitivity_analysis', {})
                
                if sensitivity_data:
                    st.markdown("**NPV Sensitivity to Key Parameters:**")
                    
                    for param, data in sensitivity_data.items():
                        param_names = {
                            'electricity_price': 'Electricity Price (€/kWh)',
                            'discount_rate': 'Discount Rate (%)',
                            'system_cost': 'System Cost (€)'
                        }
                        
                        fig_sens = px.line(
                            x=data['values'],
                            y=data['npv'],
                            title=f"NPV Sensitivity to {param_names.get(param, param)}",
                            labels={'x': param_names.get(param, param), 'y': 'NPV (€)'}
                        )
                        fig_sens.update_layout(width=700, height=400)  # Fixed width to prevent expansion
                        st.plotly_chart(fig_sens, use_container_width=False)
                else:
                    st.info("Sensitivity analysis data not available. Please run financial analysis first.")
            
            with tab3:
                # Investment summary - use calculated solution_dict
                st.markdown("**Investment Summary:**")
                
                summary_data = {
                    'Metric': [
                        'Initial Investment',
                        'Annual Energy Production',
                        'First Year Savings',
                        'Net Present Value',
                        'Return on Investment',
                        'Energy Cost per kWh',
                        'CO₂ Savings Value'
                    ],
                    'Value': [
                        f"€{solution_dict.get('total_cost', 0):,.0f}",
                        f"{solution_dict.get('annual_energy_kwh', solution_dict.get('annual_energy', 0)):,.0f} kWh",
                        f"€{solution_dict.get('annual_savings', 0):,.0f}",
                        f"€{metrics.get('npv', 0):,.0f}",
                        f"{safe_divide(metrics.get('npv', 0), solution_dict.get('total_cost', 1), 0) * 100:.1f}%",
                        f"€{safe_divide(solution_dict.get('total_cost', 0), solution_dict.get('annual_energy_kwh', solution_dict.get('annual_energy', 1)) * system_lifetime, 0):.3f}",
                        f"€{env_data.get('carbon_value', 0):,.0f}"
                    ]
                }
                
                st.dataframe(
                    pd.DataFrame(summary_data),
                    use_container_width=True,
                    hide_index=True
                )
            
            with tab4:
                # Comparative metrics - use calculated solution_dict
                st.markdown("**Financial Performance Indicators:**")
                
                # Calculate additional metrics
                total_investment = solution_dict.get('total_cost', 0)
                annual_production = solution_dict.get('annual_energy_kwh', solution_dict.get('annual_energy', 0))
                
                cost_per_kwh_installed = safe_divide(total_investment, annual_production * system_lifetime, 0)
                capacity_factor = safe_divide(annual_production, solution_dict.get('capacity', 1) * 8760, 0)
                
                comparison_metrics = {
                    'Cost per kWh (Lifetime)': f"€{cost_per_kwh_installed:.3f}",
                    'Cost per kW Installed': f"€{safe_divide(total_investment, solution_dict.get('capacity', 1), 0):,.0f}",
                    'Capacity Factor': f"{capacity_factor * 100:.1f}%",
                    'Annual Yield per €1000': f"{safe_divide(annual_production, total_investment / 1000, 0):.0f} kWh",
                    'ROI (Simple)': f"{safe_divide(solution_dict.get('annual_savings', 0) * system_lifetime, total_investment, 0) * 100:.1f}%",
                    'Energy Independence': f"{min(100, safe_divide(annual_production * 100, 10000, 0)):.1f}%"  # Assume 10,000 kWh annual demand
                }
                
                metrics_df = pd.DataFrame(list(comparison_metrics.items()), columns=['Metric', 'Value'])
                st.dataframe(metrics_df, use_container_width=True, hide_index=True)
            
            # Export financial results
            st.subheader("💾 Export Financial Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 Download Financial Report (CSV)", key="download_financial"):
                    # Combine all financial data
                    export_data = {
                        'Financial Metrics': pd.DataFrame([metrics]),
                        'Environmental Impact': pd.DataFrame([env_data]),
                        'Cash Flow Analysis': pd.DataFrame(cash_flow_data) if cash_flow_data else pd.DataFrame()
                    }
                    
                    # Create combined CSV
                    csv_buffer = []
                    for sheet_name, df in export_data.items():
                        csv_buffer.append(f"\n{sheet_name}")
                        csv_buffer.append(df.to_csv(index=False))
                    
                    combined_csv = '\n'.join(csv_buffer)
            
            with col2:
                st.info("Financial analysis complete - ready for final reporting")
                

                
                # Navigation - Single Continue Button
                st.markdown("---")
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("📄 Continue to Step 10: Comprehensive Dashboard →", type="primary", key="nav_step10"):
                        st.query_params['step'] = 'reporting'
                        st.rerun()
        
        else:
            st.warning("No financial analysis results available. Please run the analysis.")