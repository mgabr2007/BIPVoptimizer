"""
Yield vs Demand Analysis page for BIPV Optimizer - Simplified to fix refresh loop
"""

import streamlit as st
from datetime import datetime as dt
from database_manager import db_manager
from services.io import get_current_project_id


def render_yield_demand():
    """Simplified Step 7 to eliminate refresh loop issues."""
    
    st.header("⚖️ Energy Yield vs Demand Analysis")
    
    st.markdown("""
    ### What This Step Does
    
    This analysis compares the energy your BIPV systems will generate with your building's actual energy needs. 
    We calculate how much of your electricity demand can be met by solar energy and identify potential cost savings.
    
    **Key Outputs:**
    - Monthly energy balance (generation vs consumption)
    - Self-consumption percentage
    - Grid electricity savings
    - Feed-in revenue from excess energy
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
                st.success("✅ PV specifications available (Step 6)")
            else:
                st.error("❌ PV specifications missing (Step 6)")
        
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
            electricity_price = st.number_input(
                "Electricity Price (€/kWh)",
                0.10, 0.50, 0.25, 0.01,
                help="Your current electricity rate"
            )
        
        # Comprehensive analysis button
        if st.button("🚀 Run Analysis", type="primary"):
            with st.spinner("Running yield vs demand analysis..."):
                try:
                    # Get PV specifications from database
                    pv_specs = db_manager.get_pv_specifications(project_id)
                    historical_data = db_manager.get_historical_data(project_id)
                    
                    st.write(f"Debug - PV specs: {pv_specs}")
                    st.write(f"Debug - Historical data: {historical_data}")
                    
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
                            annual_demand = float(historical_data.get('annual_consumption', 0))
                            if annual_demand == 0:
                                # Try alternative field names
                                annual_demand = float(historical_data.get('total_annual_consumption', 0))
                        else:
                            st.error(f"Historical data format unexpected: {type(historical_data)}")
                            return
                    except (ValueError, TypeError) as e:
                        st.error(f"Error parsing annual demand: {e}")
                        return
                    
                    # Calculate key metrics
                    coverage_ratio = (total_annual_yield / annual_demand * 100) if annual_demand > 0 else 0
                    specific_yield = (total_annual_yield / total_capacity_kw) if total_capacity_kw > 0 else 0
                    
                    # Calculate savings
                    annual_savings = total_annual_yield * electricity_price
                    
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
        
    except Exception as e:
        st.error(f"Error accessing project data: {str(e)}")
        st.info("Please try refreshing the page or selecting a different project.")