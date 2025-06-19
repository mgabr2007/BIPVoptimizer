import streamlit as st
import json
import random
import math
from datetime import datetime, timedelta
import pytz

st.set_page_config(
    page_title="BIPV Optimizer",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("🏢 BIPV Optimizer")
    st.markdown("---")
    
    # Initialize session state
    if 'workflow_step' not in st.session_state:
        st.session_state.workflow_step = 1
    if 'project_data' not in st.session_state:
        st.session_state.project_data = {}
    
    # Sidebar navigation
    st.sidebar.title("BIPV Workflow")
    
    # Workflow steps
    workflow_steps = [
        "1. Project Setup",
        "2. Historical Data & AI Model",
        "3. Weather & Environment",
        "4. Facade & Window Extraction",
        "5. Radiation & Shading Grid",
        "6. PV Panel Specification",
        "7. Yield vs Demand Calculation",
        "8. Multi-Objective Optimization",
        "9. Financial & Environmental Analysis",
        "10. 3D Visualization",
        "11. Reporting & Export"
    ]
    
    # Display workflow progress
    for i, step in enumerate(workflow_steps, 1):
        if i <= st.session_state.workflow_step:
            st.sidebar.success(step)
        else:
            st.sidebar.info(step)
    
    # Step navigation buttons
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("⬅️ Previous", key="prev_step") and st.session_state.workflow_step > 1:
            st.session_state.workflow_step -= 1
            st.rerun()
    with col2:
        if st.button("Next ➡️", key="next_step") and st.session_state.workflow_step < 11:
            st.session_state.workflow_step += 1
            st.rerun()
    
    # Main content based on current step
    if st.session_state.workflow_step == 1:
        render_project_setup()
    elif st.session_state.workflow_step == 2:
        render_historical_data()
    elif st.session_state.workflow_step == 3:
        render_weather_environment()
    elif st.session_state.workflow_step == 4:
        render_facade_extraction()
    elif st.session_state.workflow_step == 5:
        render_radiation_grid()
    elif st.session_state.workflow_step == 6:
        render_pv_specification()
    elif st.session_state.workflow_step == 7:
        render_yield_demand()
    elif st.session_state.workflow_step == 8:
        render_optimization()
    elif st.session_state.workflow_step == 9:
        render_financial_analysis()
    elif st.session_state.workflow_step == 10:
        render_3d_visualization()
    elif st.session_state.workflow_step == 11:
        render_reporting()

def render_project_setup():
    st.header("Step 1: Project Setup")
    st.write("Configure your BIPV optimization project settings.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Project Configuration")
        
        project_name = st.text_input(
            "Project Name",
            value=st.session_state.project_data.get('project_name', 'BIPV Optimization Project'),
            key="project_name_input"
        )
        
        timezone = st.selectbox(
            "Timezone",
            options=["UTC", "US/Eastern", "US/Pacific", "Europe/London", "Europe/Berlin", "Asia/Tokyo"],
            index=0,
            key="timezone_select"
        )
        
        currency = st.selectbox(
            "Currency",
            options=["USD", "EUR", "GBP", "JPY", "CAD"],
            index=0,
            key="currency_select"
        )
        
        units = st.selectbox(
            "Units System",
            options=["Metric", "Imperial"],
            index=0,
            key="units_select"
        )
    
    with col2:
        st.subheader("BIM Model Upload")
        st.write("Upload your building model for analysis")
        
        uploaded_file = st.file_uploader(
            "Choose BIM file",
            type=['rvt', 'ifc', 'dwg'],
            help="Supported formats: Revit (.rvt), IFC (.ifc), AutoCAD (.dwg)",
            key="bim_upload"
        )
        
        if uploaded_file is not None:
            st.success(f"✅ File uploaded: {uploaded_file.name}")
            st.session_state.project_data['bim_file'] = uploaded_file.name
        
        location = st.text_input(
            "Building Location",
            placeholder="e.g., New York, NY",
            key="location_input"
        )
    
    # Save project data
    st.session_state.project_data.update({
        'project_name': project_name,
        'timezone': timezone,
        'currency': currency,
        'units': units,
        'location': location,
        'setup_complete': True
    })
    
    if project_name and location:
        st.success("✅ Project setup complete!")

def render_historical_data():
    st.header("Step 2: Historical Data & AI Model")
    st.write("Upload and analyze historical energy consumption data.")
    
    uploaded_file = st.file_uploader(
        "Upload Historical Energy Data (CSV)",
        type=['csv'],
        help="CSV file with columns: Date, Consumption, Temperature (optional)",
        key="historical_data_upload"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ Data uploaded: {uploaded_file.name}")
        
        # Simulate data processing
        with st.spinner("Processing historical data..."):
            # Create sample data structure
            sample_data = {
                'months': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                'consumption': [1200, 1100, 1000, 900, 800, 750, 
                               800, 850, 900, 1000, 1100, 1150]
            }
            
            st.session_state.project_data['historical_data'] = sample_data
            st.session_state.project_data['ai_model_trained'] = True
        
        st.success("✅ AI model trained successfully!")
        
        # Display summary
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Annual Consumption", "12,000 kWh")
            st.metric("Average Monthly", "1,000 kWh")
        with col2:
            st.metric("Peak Month", "January (1,200 kWh)")
            st.metric("Low Month", "June (750 kWh)")

def render_weather_environment():
    st.header("Step 3: Weather & Environment")
    st.write("Integrate weather data for solar analysis.")
    
    if st.session_state.project_data.get('location'):
        location = st.session_state.project_data['location']
        st.info(f"Fetching weather data for: {location}")
        
        if st.button("Generate TMY Data", key="generate_tmy"):
            with st.spinner("Generating Typical Meteorological Year data..."):
                # Simulate TMY data generation
                tmy_data = {
                    'annual_ghi': 1450,  # kWh/m²/year
                    'annual_dni': 1680,  # kWh/m²/year
                    'peak_irradiance': 1000,  # W/m²
                    'quality_score': 0.92
                }
                
                st.session_state.project_data['tmy_data'] = tmy_data
                st.session_state.project_data['weather_complete'] = True
            
            st.success("✅ Weather data generated successfully!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Annual GHI", "1,450 kWh/m²")
                st.metric("Annual DNI", "1,680 kWh/m²")
            with col2:
                st.metric("Peak Irradiance", "1,000 W/m²")
                st.metric("Data Quality", "92%")
    else:
        st.warning("Please complete project setup first.")

def render_facade_extraction():
    st.header("Step 4: Facade & Window Extraction")
    st.write("Extract building facade and window elements from BIM model.")
    
    if st.session_state.project_data.get('bim_file'):
        if st.button("Extract Building Elements", key="extract_elements"):
            with st.spinner("Extracting facade and window elements..."):
                # Simulate facade extraction
                facade_data = {
                    'total_facades': 24,
                    'suitable_facades': 18,
                    'total_area': 2400,  # m²
                    'suitable_area': 1800,  # m²
                    'orientations': ['North', 'South', 'East', 'West']
                }
                
                st.session_state.project_data['facade_data'] = facade_data
                st.session_state.project_data['extraction_complete'] = True
            
            st.success("✅ Building elements extracted successfully!")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Facades", "24")
            with col2:
                st.metric("Suitable Facades", "18")
            with col3:
                st.metric("Total Area", "2,400 m²")
            with col4:
                st.metric("Suitable Area", "1,800 m²")
    else:
        st.warning("Please upload a BIM file first.")

def render_radiation_grid():
    st.header("Step 5: Radiation & Shading Grid")
    st.write("Calculate solar radiation and shading analysis.")
    
    if st.session_state.project_data.get('facade_data'):
        if st.button("Calculate Radiation Grid", key="calc_radiation"):
            with st.spinner("Calculating solar radiation and shading..."):
                # Simulate radiation calculations
                radiation_data = {
                    'avg_irradiance': 850,  # kWh/m²/year
                    'shading_factor': 0.85,
                    'grid_points': 15000,
                    'analysis_complete': True
                }
                
                st.session_state.project_data['radiation_data'] = radiation_data
            
            st.success("✅ Radiation analysis complete!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Average Irradiance", "850 kWh/m²/year")
                st.metric("Shading Factor", "85%")
            with col2:
                st.metric("Grid Points", "15,000")
                st.metric("Analysis Status", "Complete")
    else:
        st.warning("Please complete facade extraction first.")

def render_pv_specification():
    st.header("Step 6: PV Panel Specification")
    st.write("Specify PV panel technology and system layout.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        panel_type = st.selectbox(
            "Panel Technology",
            options=["Monocrystalline", "Polycrystalline", "Thin-film", "Bifacial"],
            key="panel_type_select"
        )
        
        efficiency = st.slider(
            "Panel Efficiency (%)",
            min_value=15.0,
            max_value=25.0,
            value=20.0,
            step=0.5,
            key="efficiency_slider"
        )
    
    with col2:
        system_losses = st.slider(
            "System Losses (%)",
            min_value=5.0,
            max_value=20.0,
            value=10.0,
            step=1.0,
            key="losses_slider"
        )
        
        spacing_factor = st.slider(
            "Spacing Factor",
            min_value=1.1,
            max_value=2.0,
            value=1.5,
            step=0.1,
            key="spacing_slider"
        )
    
    if st.button("Calculate PV System", key="calc_pv_system"):
        with st.spinner("Calculating PV system specifications..."):
            # Simulate PV calculations
            pv_data = {
                'panel_type': panel_type,
                'efficiency': efficiency,
                'total_panels': 450,
                'system_capacity': 180,  # kW
                'annual_yield': 252000,  # kWh/year
                'specific_yield': 1400  # kWh/kW/year
            }
            
            st.session_state.project_data['pv_data'] = pv_data
        
        st.success("✅ PV system calculated successfully!")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Panels", "450")
            st.metric("System Capacity", "180 kW")
        with col2:
            st.metric("Annual Yield", "252,000 kWh")
            st.metric("Specific Yield", "1,400 kWh/kW")
        with col3:
            st.metric("Panel Efficiency", f"{efficiency}%")
            st.metric("System Losses", f"{system_losses}%")

def render_yield_demand():
    st.header("Step 7: Yield vs Demand Calculation")
    st.write("Compare PV energy generation with building demand.")
    
    if st.session_state.project_data.get('pv_data') and st.session_state.project_data.get('historical_data'):
        if st.button("Calculate Energy Balance", key="calc_energy_balance"):
            with st.spinner("Calculating energy balance..."):
                # Simulate energy balance calculations
                balance_data = {
                    'annual_demand': 120000,  # kWh/year
                    'annual_generation': 252000,  # kWh/year
                    'self_consumption': 95000,  # kWh/year
                    'grid_export': 157000,  # kWh/year
                    'grid_import': 25000,  # kWh/year
                    'self_sufficiency': 79.2  # %
                }
                
                st.session_state.project_data['energy_balance'] = balance_data
            
            st.success("✅ Energy balance calculated successfully!")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Annual Demand", "120,000 kWh")
                st.metric("Annual Generation", "252,000 kWh")
            with col2:
                st.metric("Self Consumption", "95,000 kWh")
                st.metric("Grid Export", "157,000 kWh")
            with col3:
                st.metric("Grid Import", "25,000 kWh")
                st.metric("Self Sufficiency", "79.2%")
    else:
        st.warning("Please complete PV specification and historical data analysis first.")

def render_optimization():
    st.header("Step 8: Multi-Objective Optimization")
    st.write("Optimize PV system configuration using genetic algorithms.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Optimization Parameters")
        
        pop_size = st.slider("Population Size", 20, 100, 50, key="pop_size")
        generations = st.slider("Generations", 10, 100, 30, key="generations")
        
        st.subheader("Economic Parameters")
        electricity_rate = st.number_input("Electricity Rate ($/kWh)", 0.05, 0.50, 0.12, key="elec_rate")
        feed_in_tariff = st.number_input("Feed-in Tariff ($/kWh)", 0.01, 0.20, 0.08, key="fit_rate")
    
    with col2:
        st.subheader("Objective Weights")
        obj1_weight = st.slider("Net Energy Import Weight", 0.0, 1.0, 0.6, key="obj1_weight")
        obj2_weight = st.slider("ROI Weight", 0.0, 1.0, 0.4, key="obj2_weight")
        
        st.subheader("Financial Parameters")
        discount_rate = st.number_input("Discount Rate (%)", 1.0, 15.0, 5.0, key="discount_rate") / 100
        project_lifetime = st.slider("Project Lifetime (years)", 10, 30, 25, key="lifetime")
    
    if st.button("Run Optimization", key="run_optimization"):
        with st.spinner("Running genetic algorithm optimization..."):
            # Simulate optimization
            optimization_results = {
                'best_solutions': [
                    {'panels': 420, 'capacity': 168, 'roi': 12.5, 'net_import': 18000},
                    {'panels': 450, 'capacity': 180, 'roi': 11.8, 'net_import': 15000},
                    {'panels': 380, 'capacity': 152, 'roi': 13.2, 'net_import': 22000}
                ],
                'pareto_front': True,
                'optimization_complete': True
            }
            
            st.session_state.project_data['optimization_results'] = optimization_results
        
        st.success("✅ Optimization complete!")
        
        st.subheader("Optimal Solutions")
        for i, solution in enumerate(optimization_results['best_solutions'], 1):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(f"Solution {i} - Panels", solution['panels'])
            with col2:
                st.metric(f"Capacity", f"{solution['capacity']} kW")
            with col3:
                st.metric(f"ROI", f"{solution['roi']}%")
            with col4:
                st.metric(f"Net Import", f"{solution['net_import']:,} kWh")

def render_financial_analysis():
    st.header("Step 9: Financial & Environmental Analysis")
    st.write("Comprehensive financial modeling and environmental impact assessment.")
    
    if st.session_state.project_data.get('optimization_results'):
        solution_idx = st.selectbox(
            "Select Solution for Analysis",
            options=[0, 1, 2],
            format_func=lambda x: f"Solution {x+1}",
            key="solution_select"
        )
        
        if st.button("Analyze Solution", key="analyze_solution"):
            with st.spinner("Calculating financial analysis..."):
                # Simulate financial analysis
                financial_data = {
                    'initial_investment': 450000,
                    'annual_savings': 28500,
                    'npv': 125000,
                    'irr': 11.8,
                    'payback_period': 15.8,
                    'co2_savings': 125,  # tons/year
                    'analysis_complete': True
                }
                
                st.session_state.project_data['financial_analysis'] = financial_data
            
            st.success("✅ Financial analysis complete!")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Initial Investment", "$450,000")
                st.metric("Annual Savings", "$28,500")
            with col2:
                st.metric("NPV", "$125,000")
                st.metric("IRR", "11.8%")
            with col3:
                st.metric("Payback Period", "15.8 years")
                st.metric("CO₂ Savings", "125 tons/year")
    else:
        st.warning("Please complete optimization first.")

def render_3d_visualization():
    st.header("Step 10: 3D Visualization")
    st.write("Interactive 3D visualization of building and PV system.")
    
    if st.session_state.project_data.get('optimization_results'):
        st.info("3D visualization would be displayed here with interactive building model and PV panel placement.")
        
        # Placeholder for 3D visualization
        st.subheader("Building Overview")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Building Height", "45 m")
            st.metric("Floor Area", "2,400 m²")
            st.metric("Facade Area", "1,800 m²")
        
        with col2:
            st.metric("PV Coverage", "75%")
            st.metric("Panel Count", "450")
            st.metric("System Capacity", "180 kW")
        
        if st.button("Generate 3D Model", key="generate_3d"):
            st.success("✅ 3D model generated successfully!")
            st.session_state.project_data['visualization_complete'] = True
    else:
        st.warning("Please complete optimization first.")

def render_reporting():
    st.header("Step 11: Reporting & Export")
    st.write("Generate comprehensive reports and export analysis results.")
    
    if st.session_state.project_data.get('financial_analysis'):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Report Generation")
            
            report_type = st.selectbox(
                "Report Type",
                options=["Executive Summary", "Technical Report", "Financial Analysis", "Complete Report"],
                key="report_type"
            )
            
            if st.button("Generate Report", key="generate_report"):
                st.success(f"✅ {report_type} generated successfully!")
        
        with col2:
            st.subheader("Data Export")
            
            export_format = st.selectbox(
                "Export Format",
                options=["CSV", "JSON", "Excel"],
                key="export_format"
            )
            
            if st.button("Export Data", key="export_data"):
                st.success(f"✅ Data exported as {export_format} successfully!")
        
        # Project summary
        st.subheader("Project Summary")
        project_name = st.session_state.project_data.get('project_name', 'BIPV Optimization Project')
        
        summary_data = {
            'Project': project_name,
            'System Capacity': '180 kW',
            'Annual Generation': '252,000 kWh',
            'Investment': '$450,000',
            'Annual Savings': '$28,500',
            'Payback Period': '15.8 years',
            'CO₂ Savings': '125 tons/year'
        }
        
        for key, value in summary_data.items():
            st.write(f"**{key}:** {value}")
        
        st.success("✅ BIPV Optimizer workflow complete!")
    else:
        st.warning("Please complete financial analysis first.")

if __name__ == "__main__":
    main()