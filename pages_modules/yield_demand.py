"""
Yield vs Demand Analysis page for BIPV Optimizer - Simplified to fix refresh loop
"""

import streamlit as st
from datetime import datetime as dt
from database_manager import db_manager
from services.io import get_current_project_id


def render_yield_demand():
    """Simplified Step 7 to eliminate refresh loop issues."""
    
    st.header("⚖️ Energy Yield vs Demand Analysis for Selected Windows")
    
    st.markdown("""
    ### What This Step Does
    
    This analysis compares the energy your BIPV systems will generate from selected window types with your building's actual energy needs. 
    We calculate how much of your electricity demand can be met by solar energy from the chosen windows and identify potential cost savings.
    
    **Key Outputs:**
    - Monthly energy balance (generation from selected windows vs consumption)
    - Self-consumption percentage from selected BIPV windows
    - Grid electricity savings from selected window installations
    - Feed-in revenue from excess energy from selected windows
    """)
    
    # Check prerequisites and ensure project data is loaded
    from services.io import ensure_project_data_loaded
    
    if not ensure_project_data_loaded():
        st.error("⚠️ No project found. Please complete Step 1 (Project Setup) first.")
        return
    
    # Get project ID
    project_id = get_current_project_id()
    
    # Simple dependency validation
    st.subheader("📋 Dependency Check")
    
    try:
        # Check historical data
        historical_data = db_manager.get_historical_data(project_id)
        has_historical = historical_data and historical_data.get('consumption_data')
        
        # Check PV specifications
        pv_specs = db_manager.get_pv_specifications(project_id)
        has_pv_specs = pv_specs is not None and len(pv_specs) > 0
        
        # Display validation results
        col1, col2 = st.columns(2)
        
        with col1:
            if has_historical:
                st.success("✅ Historical energy data available (Step 2)")
            else:
                st.error("❌ Historical energy data missing (Step 2)")
        
        with col2:
            if has_pv_specs:
                st.success("✅ PV specifications for selected windows available (Step 6)")
            else:
                st.error("❌ PV specifications for selected windows missing (Step 6)")
        
        if not has_historical or not has_pv_specs:
            st.warning("Please complete the required steps before proceeding with yield analysis.")
            return
        
        # Analysis configuration
        st.subheader("⚙️ Analysis Configuration")
        
        col3, col4 = st.columns(2)
        
        with col3:
            analysis_start = st.date_input(
                "Analysis Start Date",
                value=dt(2024, 1, 1),
                help="When your BIPV system operation begins"
            )
        
        with col4:
            # Try to get electricity rate from Step 1 project data
            default_rate = 0.25
            rate_source = "Default"
            
            try:
                # Use already imported functions from module level
                project_id = get_current_project_id()
                if project_id:
                    project_data = db_manager.get_project_by_id(project_id)
                    
                    if project_data and project_data.get('electricity_rates'):
                        import json
                        # Parse JSON string to dict if needed
                        rates_data = project_data['electricity_rates']
                        if isinstance(rates_data, str):
                            rates = json.loads(rates_data)
                        else:
                            rates = rates_data
                            
                        if isinstance(rates, dict) and 'import_rate' in rates:
                            default_rate = float(rates['import_rate'])
                            rate_source = f"Step 1 ({rates.get('source', 'Unknown')})"
                            st.info(f"✅ Using electricity rate from Step 1: {default_rate:.3f} €/kWh")
                        else:
                            st.warning("⚠️ Electricity rates from Step 1 are not in expected format")
                    else:
                        st.warning("⚠️ No electricity rates found from Step 1 - please configure rates in Step 1")
                else:
                    st.warning("⚠️ No project ID found - using default rate")
                    
            except Exception as e:
                st.warning(f"⚠️ Error retrieving electricity rates from Step 1: {str(e)}")
            
            electricity_price = st.number_input(
                "Electricity Price (€/kWh)",
                0.01, 0.50, default_rate, 0.01,
                help=f"Electricity rate (Source: {rate_source})"
            )
        
        # Comprehensive analysis button
        if st.button("🚀 Run Analysis", type="primary"):
            with st.spinner("Running yield vs demand analysis..."):
                try:
                    # Get PV specifications from database
                    pv_specs = db_manager.get_pv_specifications(project_id)
                    historical_data = db_manager.get_historical_data(project_id)
                    
                    # Load data from database (silent processing)
                    
                    if not pv_specs or not historical_data:
                        st.error("Missing required data for analysis")
                        st.write(f"PV specs: {pv_specs}")
                        st.write(f"Historical data: {historical_data}")
                        return
                    
                    # Handle different data formats from database
                    import json
                    bipv_specs = []
                    
                    # Try different ways to parse PV specifications
                    if isinstance(pv_specs, list) and len(pv_specs) > 0:
                        # Format: [{'specification_data': '...'}, ...]
                        spec_data = pv_specs[0].get('specification_data', {})
                        if isinstance(spec_data, str):
                            spec_data = json.loads(spec_data)
                        bipv_specs = spec_data.get('bipv_specifications', [])
                    elif isinstance(pv_specs, dict):
                        # Format: {'bipv_specifications': [...]}
                        bipv_specs = pv_specs.get('bipv_specifications', [])
                    
                    if not bipv_specs:
                        st.error("No BIPV specifications found in database")
                        st.write(f"Available data: {pv_specs}")
                        return
                    
                    # Calculate totals using actual field names with safe conversion
                    total_capacity_kw = 0
                    total_annual_yield = 0 
                    total_cost_eur = 0
                    
                    for spec in bipv_specs:
                        try:
                            total_capacity_kw += float(spec.get('capacity_kw', 0))
                            total_annual_yield += float(spec.get('annual_energy_kwh', 0))
                            total_cost_eur += float(spec.get('total_cost_eur', 0))
                        except (ValueError, TypeError) as e:
                            st.warning(f"Error parsing spec data: {e}")
                            continue
                    
                    # Get annual demand from historical data with safe conversion
                    annual_demand = 0
                    try:
                        if isinstance(historical_data, dict):
                            # Try multiple possible field names for annual consumption
                            possible_fields = ['annual_consumption', 'total_annual_consumption', 'base_consumption']
                            for field in possible_fields:
                                if field in historical_data and historical_data[field]:
                                    annual_demand = float(historical_data[field])
                                    break
                            
                            # If still no annual demand, try to calculate from consumption data
                            if annual_demand == 0 and 'consumption_data' in historical_data:
                                consumption_data = historical_data['consumption_data']
                                if isinstance(consumption_data, list) and len(consumption_data) > 0:
                                    annual_demand = sum(float(x) for x in consumption_data if x is not None)
                                    # Annual demand calculated from consumption data
                                elif isinstance(consumption_data, dict):
                                    annual_demand = sum(float(v) for v in consumption_data.values() if v is not None)
                                    # Annual demand calculated from consumption dict
                                    
                            if annual_demand == 0:
                                st.error("No annual consumption data found in historical data")
                                st.write(f"Available fields: {list(historical_data.keys())}")
                                return
                        else:
                            st.error(f"Historical data format unexpected: {type(historical_data)}")
                            return
                    except (ValueError, TypeError) as e:
                        st.error(f"Error parsing annual demand: {e}")
                        return
                    
                    # Validate calculations before proceeding (silent processing)
                    
                    # Calculate key metrics with validation
                    if annual_demand > 0:
                        coverage_ratio = (total_annual_yield / annual_demand * 100)
                    else:
                        coverage_ratio = 0
                        st.warning("Annual demand is zero - cannot calculate coverage ratio")
                    
                    if total_capacity_kw > 0:
                        specific_yield = (total_annual_yield / total_capacity_kw)
                    else:
                        specific_yield = 0
                        st.warning("Total capacity is zero - cannot calculate specific yield")
                    
                    # Calculate savings
                    annual_savings = total_annual_yield * electricity_price
                    
                    # Validate all calculations are reasonable
                    if total_capacity_kw == 0 or total_annual_yield == 0 or total_cost_eur == 0:
                        st.error("Some calculated values are zero - check BIPV specifications data")
                        return
                    
                    st.success("✅ Analysis completed successfully!")
                    
                    # Display real results
                    st.subheader("📊 Analysis Results")
                    
                    col5, col6, col7 = st.columns(3)
                    
                    with col5:
                        st.metric(
                            "Annual Generation", 
                            f"{total_annual_yield:,.0f} kWh",
                            f"vs {annual_demand:,.0f} kWh demand"
                        )
                    
                    with col6:
                        st.metric(
                            "Energy Coverage", 
                            f"{coverage_ratio:.1f}%",
                            "of building demand"
                        )
                    
                    with col7:
                        st.metric(
                            "Annual Savings", 
                            f"€{annual_savings:,.0f}",
                            f"€{annual_savings/12:,.0f}/month"
                        )
                    
                    # Additional metrics
                    st.subheader("📈 System Performance Metrics")
                    
                    col8, col9, col10 = st.columns(3)
                    
                    with col8:
                        st.metric("Total Capacity", f"{total_capacity_kw:.2f} kW")
                    
                    with col9:
                        st.metric("Specific Yield", f"{specific_yield:.0f} kWh/kW")
                    
                    with col10:
                        st.metric("Total Investment", f"€{total_cost_eur:,.0f}")
                    
                    # Save results to database
                    yield_data = {
                        'total_annual_yield': total_annual_yield,
                        'annual_demand': annual_demand,
                        'coverage_ratio': coverage_ratio,
                        'total_capacity_kw': total_capacity_kw,
                        'total_cost_eur': total_cost_eur,
                        'annual_savings': annual_savings,
                        'specific_yield': specific_yield
                    }
                    
                    db_manager.save_yield_demand_data(project_id, yield_data)
                    
                except Exception as e:
                    st.error(f"Analysis failed: {str(e)}")
                    st.write("**Debug Info:**")
                    st.write(f"Project ID: {project_id}")
                    st.write(f"PV Specs Available: {bool(pv_specs)}")
                    st.write(f"Historical Data Available: {bool(historical_data)}")
                    st.write(f"Exception type: {type(e)}")
                    
                    # Additional debug info
                    if pv_specs:
                        st.write(f"PV Specs data: {pv_specs}")
                    if historical_data:
                        st.write(f"Historical data: {historical_data}")
                        
                    import traceback
                    st.text_area("Full Error Traceback", traceback.format_exc(), height=200)
        
        # Individual step report download
        st.markdown("---")
        st.markdown("### 📄 Step 7 Analysis Report")
        st.markdown("Download detailed yield vs demand analysis report:")
        
        try:
            from utils.individual_step_reports import create_step_download_button
            create_step_download_button(7, "Yield vs Demand", "Download Yield Analysis Report")
        except:
            st.info("Report download functionality temporarily unavailable.")
        
        # Navigation - Single Continue Button
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🎯 Continue to Step 8: Optimization →", type="primary", key="nav_step8"):
                st.query_params['step'] = 'optimization'
                st.rerun()
        
    except Exception as e:
        st.error(f"Error accessing project data: {str(e)}")
        st.info("Please try refreshing the page or selecting a different project.")