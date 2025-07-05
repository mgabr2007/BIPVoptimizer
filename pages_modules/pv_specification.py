"""
PV Panel Specification & Layout page for BIPV Optimizer
Simplified interface focusing on essential BIPV parameters
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from database_manager import db_manager
from datetime import datetime
from core.solar_math import safe_divide
from utils.consolidated_data_manager import ConsolidatedDataManager

# Simplified BIPV Glass Types
BIPV_GLASS_TYPES = {
    "Standard": {
        "efficiency": 0.16,
        "transparency": 0.20,
        "cost_per_m2": 300
    },
    "High-Efficiency": {
        "efficiency": 0.19,
        "transparency": 0.15,
        "cost_per_m2": 400
    },
    "Aesthetic": {
        "efficiency": 0.14,
        "transparency": 0.25,
        "cost_per_m2": 350
    }
}

def calculate_bipv_glass_coverage(element_area, coverage_factor=0.90):
    """Calculate BIPV glass coverage for window elements."""
    bipv_glass_area = element_area * coverage_factor
    return bipv_glass_area

def calculate_bipv_system_specifications(suitable_elements, panel_specs, coverage_data, radiation_data=None):
    """Calculate complete BIPV system specifications for each element."""
    bipv_specifications = []
    
    # Try to get radiation data for more accurate calculations
    radiation_lookup = {}
    if radiation_data is not None:
        if isinstance(radiation_data, pd.DataFrame) and 'element_id' in radiation_data.columns:
            for _, rad_row in radiation_data.iterrows():
                element_id = rad_row.get('element_id', '')
                annual_radiation = rad_row.get('annual_radiation', 1500)  # kWh/m²/year
                radiation_lookup[element_id] = annual_radiation
        elif isinstance(radiation_data, dict) and 'element_radiation' in radiation_data:
            radiation_lookup = radiation_data['element_radiation']
    
    for idx, element in suitable_elements.iterrows():
        # Use actual Element ID from building elements
        element_id = element.get('Element ID', element.get('element_id', f"element_{idx}"))
        glass_area = float(element.get('Glass Area (m²)', element.get('glass_area', 1.5)))
        
        # Get radiation data for this specific element
        annual_radiation = radiation_lookup.get(element_id, 1500)  # Default fallback
        
        # Calculate BIPV specifications
        bipv_area = calculate_bipv_glass_coverage(glass_area)
        capacity_kw = bipv_area * panel_specs['power_density'] / 1000
        
        # More accurate energy calculation using radiation data
        specific_yield = annual_radiation * panel_specs['efficiency'] * panel_specs['performance_ratio']
        annual_energy_kwh = bipv_area * specific_yield
        
        total_cost_eur = bipv_area * panel_specs['cost_per_m2']
        
        bipv_spec = {
            'element_id': element_id,
            'glass_area_m2': glass_area,
            'bipv_area_m2': bipv_area,
            'capacity_kw': capacity_kw,
            'annual_energy_kwh': annual_energy_kwh,
            'annual_radiation_kwh_m2': annual_radiation,
            'specific_yield_kwh_kw': safe_divide(annual_energy_kwh, capacity_kw, 0) if capacity_kw > 0 else 0,
            'total_cost_eur': total_cost_eur,
            'efficiency': panel_specs['efficiency'],
            'transparency': panel_specs['transparency']
        }
        
        bipv_specifications.append(bipv_spec)
    
    return pd.DataFrame(bipv_specifications)

def render_pv_specification():
    """Render the simplified PV panel specification and layout module."""
    
    # Add OptiSunny character header image
    st.image("attached_assets/step06_1751436847830.png", width=400)
    
    st.header("⚡ Step 6: BIPV Panel Specifications")
    
    # Data Usage Information
    with st.expander("📊 How This Data Will Be Used", expanded=False):
        st.markdown("""
        ### Data Flow Through BIPV Analysis Workflow:
        
        **Step 6 → Step 7 (Yield vs Demand):**
        - **System capacity (kW)** → Energy generation calculations and monthly yield profiles
        - **Annual energy yield** → Grid interaction analysis and self-consumption calculations
        - **Element-specific specifications** → Individual system performance tracking and optimization
        
        **Step 6 → Step 8 (Optimization):**
        - **Cost per system** → Genetic algorithm objective function for budget constraints
        - **Performance ratios** → Multi-objective optimization between cost and energy yield
        - **Technology specifications** → System selection constraints and feasibility analysis
        
        **Step 6 → Step 9 (Financial Analysis):**
        - **Total installation costs** → NPV and IRR calculations for investment analysis
        - **BIPV glass specifications** → Lifecycle cost modeling and maintenance projections
        - **Capacity factors** → Revenue generation and payback period calculations
        
        **Step 6 → Step 10 (Reporting):**
        - **Technical specifications** → System documentation and compliance validation
        - **BIPV technology details** → Architectural integration assessment and performance benchmarking
        - **Cost breakdown analysis** → Economic feasibility reporting and investment recommendations
        """)
    
    # Check for radiation data from Step 5 (multiple possible locations)
    project_data = st.session_state.get('project_data', {})
    radiation_data = project_data.get('radiation_data')
    radiation_completed = st.session_state.get('radiation_completed', False)
    
    if radiation_data is None and not radiation_completed:
        st.warning("⚠️ Radiation analysis data required. Please complete Step 5 (Solar Radiation & Shading Analysis) first.")
        st.info("PV specification requires solar radiation data to calculate energy yield accurately.")
        return
    
    # Confirm radiation data is available
    if radiation_data is not None or radiation_completed:
        if isinstance(radiation_data, pd.DataFrame):
            elements_count = len(radiation_data)
        elif isinstance(radiation_data, dict) and 'element_radiation' in radiation_data:
            elements_count = len(radiation_data['element_radiation'])
        else:
            elements_count = "available"
        st.success(f"✅ Radiation analysis data found ({elements_count} elements analyzed)")
    
    # Check for building elements data from Step 4
    building_elements = st.session_state.get('building_elements')
    if building_elements is None or len(building_elements) == 0:
        st.warning("⚠️ Building elements data required. Please complete Step 4 (Facade & Window Extraction) first.")
        st.info("BIPV specifications require building geometry data for accurate system sizing.")
        return
    
    # Convert to DataFrame if needed
    if isinstance(building_elements, list):
        suitable_elements = pd.DataFrame(building_elements)
    else:
        suitable_elements = building_elements
    
    # Debug information
    st.success(f"Designing BIPV systems for {len(suitable_elements)} building elements")
    
    # Show sample Element IDs for verification
    if len(suitable_elements) > 0:
        sample_ids = suitable_elements['Element ID'].head(3).tolist() if 'Element ID' in suitable_elements.columns else ["No Element ID column"]
        st.info(f"Sample Element IDs from building data: {sample_ids}")
        
        # Show available columns for debugging
        st.write(f"Debug - Available columns in building elements: {list(suitable_elements.columns)}")
        
        # Check radiation data availability
        if radiation_data is not None:
            if isinstance(radiation_data, pd.DataFrame):
                st.info(f"Radiation data available for {len(radiation_data)} elements")
                if 'element_id' in radiation_data.columns:
                    sample_rad_ids = radiation_data['element_id'].head(3).tolist()
                    st.info(f"Sample Element IDs from radiation data: {sample_rad_ids}")
            elif isinstance(radiation_data, dict):
                element_count = len(radiation_data.get('element_radiation', {}))
                st.info(f"Radiation data available for {element_count} elements")
    
    # Panel selection section
    st.subheader("🔧 BIPV Panel Selection & Customization")
    
    st.markdown("**Select BIPV glass type and customize the key specifications:**")
    
    # Simplified panel selection
    panel_types = list(BIPV_GLASS_TYPES.keys())
    selected_panel_type = st.selectbox(
        "BIPV Glass Type", 
        panel_types,
        key="bipv_glass_type",
        help="Choose BIPV glass technology as starting point for customization"
    )
    
    # Get base specifications
    base_specs = BIPV_GLASS_TYPES[selected_panel_type]
    
    # Simplified customization - only the most important parameters
    st.subheader("🔧 Customize Key Specifications")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        panel_efficiency = st.slider(
            "Efficiency (%)",
            min_value=10.0, max_value=22.0, 
            value=float(base_specs['efficiency']*100),
            step=0.5,
            key="panel_efficiency",
            help="PV conversion efficiency"
        ) / 100
        
    with col2:
        transparency = st.slider(
            "Transparency (%)",
            min_value=10.0, max_value=40.0,
            value=float(base_specs['transparency']*100),
            step=5.0,
            key="transparency",
            help="Light transmission through BIPV glass"
        ) / 100
        
    with col3:
        cost_per_m2 = st.number_input(
            "Cost (EUR/m²)",
            min_value=100.0, max_value=1000.0,
            value=float(base_specs['cost_per_m2']),
            step=25.0,
            key="cost_per_m2",
            help="BIPV glass cost per square meter (flexible range for various technologies)"
        )
    
    # Calculate derived specifications
    power_density = panel_efficiency * 1000  # W/m²
    temperature_coefficient = -0.004  # Standard value
    
    # Create final panel specifications
    final_panel_specs = {
        'type': selected_panel_type,
        'efficiency': panel_efficiency,
        'power_density': power_density,
        'transparency': transparency,
        'cost_per_m2': cost_per_m2,
        'temperature_coefficient': temperature_coefficient,
        'performance_ratio': 0.80,  # Standard value
        'degradation_rate': 0.005,  # Standard value
        'glass_properties': {
            'thickness': 0.008,  # 8mm standard
            'power_density': power_density,
            'u_value': 1.2,
            'weight': 24.0
        },
        'warranty_years': 25
    }
    
    # Display current specifications summary
    st.subheader("📊 Current Specifications Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Efficiency", f"{panel_efficiency*100:.1f}%")
    with col2:
        st.metric("Power Density", f"{power_density:.0f} W/m²")
    with col3:
        st.metric("Transparency", f"{transparency*100:.0f}%")
    with col4:
        st.metric("Cost", f"{cost_per_m2:.0f} EUR/m²")
    
    # Calculate system specifications using building elements and radiation data
    if st.button("⚡ Calculate BIPV Systems", type="primary", key="calculate_bipv_systems"):
        
        with st.spinner("Calculating BIPV system specifications for all building elements..."):
            # Calculate BIPV specifications using the simplified panel data and radiation data
            coverage_data = {}  # Simplified coverage calculation
            bipv_specifications = calculate_bipv_system_specifications(
                suitable_elements, 
                final_panel_specs, 
                coverage_data,
                radiation_data  # Pass radiation data for accurate calculations
            )
            
            if bipv_specifications is not None and len(bipv_specifications) > 0:
                st.session_state['pv_specifications'] = bipv_specifications.to_dict('records')
                
                # Save to consolidated data manager
                consolidated_manager = ConsolidatedDataManager()
                step6_data = {
                    'pv_specifications': {'individual_systems': bipv_specifications.to_dict('records')},
                    'bipv_specifications': final_panel_specs,
                    'individual_systems': bipv_specifications.to_dict('records'),
                    'specifications_complete': True
                }
                consolidated_manager.save_step6_data(step6_data)
                
                # Save to database
                project_name = st.session_state.get('project_name', 'Unnamed Project')
                try:
                    project_id = db_manager.save_project({'project_name': project_name})
                    if project_id:
                        db_manager.save_pv_specifications(int(project_id), {
                            'panel_specs': final_panel_specs,
                            'bipv_specifications': bipv_specifications.to_dict('records'),
                            'summary_stats': {
                                'total_elements': len(bipv_specifications),
                                'total_capacity': bipv_specifications['capacity_kw'].sum(),
                                'total_area': bipv_specifications['glass_area_m2'].sum(),
                                'avg_efficiency': final_panel_specs['efficiency']
                            }
                        })
                except Exception as e:
                    st.warning(f"Could not save to database: {e}")
                
                # Display results
                st.success(f"✅ Successfully calculated BIPV specifications for {len(bipv_specifications)} building elements")
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    total_capacity = bipv_specifications['capacity_kw'].sum()
                    st.metric("Total Capacity", f"{total_capacity:.1f} kW")
                with col2:
                    total_area = bipv_specifications['glass_area_m2'].sum()
                    st.metric("Total BIPV Area", f"{total_area:.0f} m²")
                with col3:
                    avg_specific_power = total_capacity * 1000 / total_area if total_area > 0 else 0
                    st.metric("Avg Power Density", f"{avg_specific_power:.0f} W/m²")
                with col4:
                    total_cost = (bipv_specifications['total_cost_eur'].sum() if 'total_cost_eur' in bipv_specifications.columns else 0)
                    st.metric("Total Cost", f"{total_cost:,.0f} EUR")
                
                # Display detailed specifications table
                st.subheader("Individual Element Specifications")
                display_df = bipv_specifications[['element_id', 'glass_area_m2', 'capacity_kw', 'annual_energy_kwh', 'annual_radiation_kwh_m2', 'total_cost_eur']].copy()
                display_df.columns = ['Element ID', 'Area (m²)', 'Capacity (kW)', 'Annual Energy (kWh)', 'Radiation (kWh/m²)', 'Cost (EUR)']
                st.dataframe(display_df, use_container_width=True)
                
                # Show top performing systems for verification
                st.subheader("🔋 Top Performing BIPV Systems (by Capacity)")
                top_systems = bipv_specifications.nlargest(10, 'capacity_kw')[['element_id', 'glass_area_m2', 'capacity_kw', 'annual_energy_kwh', 'annual_radiation_kwh_m2']]
                top_systems.columns = ['Element ID', 'Glass Area (m²)', 'Capacity (kW)', 'Annual Energy (kWh)', 'Solar Radiation (kWh/m²)']
                st.dataframe(top_systems, use_container_width=True)
                
            else:
                st.error("Could not calculate BIPV specifications. Please check your data.")
    
    # Add step-specific download button
    st.markdown("---")
    st.markdown("### 📄 Step 6 Analysis Report")
    st.markdown("Download detailed PV specification and system design report:")
    
    from utils.individual_step_reports import create_step_download_button
    create_step_download_button(6, "PV Specification", "Download PV Specification Report")
    
    st.markdown("---")
    st.markdown("**Next Step:** Proceed to Step 7 (Yield vs Demand Analysis) to compare energy generation with building consumption.")