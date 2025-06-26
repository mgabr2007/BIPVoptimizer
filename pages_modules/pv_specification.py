"""
PV Panel Specification & Layout page for BIPV Optimizer
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from database_manager import db_manager
from datetime import datetime
from core.solar_math import safe_divide

# BIPV Panel Database
BIPV_PANEL_DATABASE = {
    "Standard BIPV Glass": {
        "efficiency": 0.16,
        "cost_per_wp": 0.85,
        "dimensions": {"width": 1.00, "height": 1.50, "thickness": 0.008},
        "power_rating": 240,
        "temperature_coefficient": -0.004,
        "warranty_years": 25,
        "transparency": 0.20,
        "description": "Standard semi-transparent BIPV glass panels for window integration"
    },
    "High-Efficiency BIPV": {
        "efficiency": 0.19,
        "cost_per_wp": 1.15,
        "dimensions": {"width": 1.00, "height": 1.50, "thickness": 0.008},
        "power_rating": 285,
        "temperature_coefficient": -0.0035,
        "warranty_years": 25,
        "transparency": 0.15,
        "description": "High-efficiency BIPV panels with advanced cell technology"
    },
    "Colored BIPV Glass": {
        "efficiency": 0.14,
        "cost_per_wp": 0.95,
        "dimensions": {"width": 1.00, "height": 1.50, "thickness": 0.008},
        "power_rating": 210,
        "temperature_coefficient": -0.0045,
        "warranty_years": 25,
        "transparency": 0.25,
        "description": "Aesthetically designed colored BIPV panels for architectural integration"
    },
    "Thin-Film BIPV": {
        "efficiency": 0.12,
        "cost_per_wp": 0.75,
        "dimensions": {"width": 1.20, "height": 1.60, "thickness": 0.006},
        "power_rating": 230,
        "temperature_coefficient": -0.0025,
        "warranty_years": 20,
        "transparency": 0.30,
        "description": "Flexible thin-film BIPV panels for curved surfaces"
    },
    "Premium BIPV Glass": {
        "efficiency": 0.21,
        "cost_per_wp": 1.35,
        "dimensions": {"width": 1.00, "height": 1.50, "thickness": 0.010},
        "power_rating": 315,
        "temperature_coefficient": -0.003,
        "warranty_years": 30,
        "transparency": 0.10,
        "description": "Premium BIPV panels with maximum efficiency and minimal transparency"
    }
}

def calculate_panel_layout(element_area, element_width, element_height, panel_width, panel_height, spacing_factor=0.02):
    """Calculate optimal panel layout for given element dimensions."""
    
    # For BIPV, spacing is minimal as panels replace glass
    effective_panel_width = panel_width * (1 + spacing_factor)
    effective_panel_height = panel_height * (1 + spacing_factor)
    
    # Calculate panels that fit
    panels_horizontal = max(1, int(element_width // effective_panel_width))
    panels_vertical = max(1, int(element_height // effective_panel_height))
    
    # For BIPV windows, typically use single large panels
    if element_area < 3.0:  # Small windows
        panels_horizontal = 1
        panels_vertical = 1
    
    total_panels = panels_horizontal * panels_vertical
    panel_area = panel_width * panel_height
    total_panel_area = total_panels * panel_area
    coverage_ratio = min(1.0, total_panel_area / element_area) if element_area > 0 else 0
    
    return {
        'panels_horizontal': panels_horizontal,
        'panels_vertical': panels_vertical,
        'total_panels': total_panels,
        'total_panel_area': total_panel_area,
        'coverage_ratio': coverage_ratio,
        'unused_area': max(0, element_area - total_panel_area)
    }

def calculate_system_specifications(element_data, panel_specs, radiation_data):
    """Calculate complete system specifications for each element."""
    
    specifications = []
    
    for _, element in element_data.iterrows():
        element_id = element.get('Element ID', element.get('element_id', ''))
        element_area = float(element.get('Glass Area (m²)', element.get('area', 1.5)))
        
        # Get radiation data for this element
        element_radiation = radiation_data[radiation_data['element_id'] == element_id]
        annual_irradiation = element_radiation.iloc[0]['annual_irradiation'] if len(element_radiation) > 0 else 1000
        
        # Calculate layout
        layout = calculate_panel_layout(
            element_area,
            element.get('Width (m)', 1.0),
            element.get('Height (m)', 1.5),
            panel_specs['dimensions']['width'],
            panel_specs['dimensions']['height']
        )
        
        if layout['total_panels'] > 0:
            # System power calculation
            system_power_wp = layout['total_panels'] * panel_specs['power_rating']
            system_power_kw = system_power_wp / 1000
            
            # Annual energy production
            # Energy = System Power (kW) × Annual Irradiation (kWh/m²) × Panel Efficiency × Performance Ratio
            performance_ratio = 0.85  # Account for inverter losses, soiling, etc.
            annual_energy_kwh = (system_power_kw * annual_irradiation * 
                               panel_specs['efficiency'] * performance_ratio / 1000)
            
            # Cost calculations
            panel_cost = system_power_wp * panel_specs['cost_per_wp']
            installation_cost = panel_cost * 0.5  # Installation cost ~50% of panel cost for BIPV
            inverter_cost = system_power_kw * 150  # €150/kW for inverters
            total_cost = panel_cost + installation_cost + inverter_cost
            
            # Specific yield (kWh/kWp)
            specific_yield = safe_divide(annual_energy_kwh * 1000, system_power_wp, 0)
            
            specification = {
                'element_id': element_id,
                'element_area': element_area,
                'panels_horizontal': layout['panels_horizontal'],
                'panels_vertical': layout['panels_vertical'],
                'total_panels': layout['total_panels'],
                'coverage_ratio': layout['coverage_ratio'],
                'system_power_wp': system_power_wp,
                'system_power_kw': system_power_kw,
                'annual_energy_kwh': annual_energy_kwh,
                'specific_yield': specific_yield,
                'panel_cost': panel_cost,
                'installation_cost': installation_cost,
                'inverter_cost': inverter_cost,
                'total_installation_cost': total_cost,
                'cost_per_kwh': safe_divide(total_cost, annual_energy_kwh, 0),
                'annual_irradiation': annual_irradiation,
                'orientation': element.get('Orientation', 'Unknown'),
                'transparency': panel_specs.get('transparency', 0.2)
            }
            
            specifications.append(specification)
    
    return pd.DataFrame(specifications)

def render_pv_specification():
    """Render the PV panel specification and layout module."""
    
    st.header("⚡ Step 6: BIPV Panel Specification & System Design")
    
    # Check dependencies
    building_elements = st.session_state.get('building_elements')
    if building_elements is None or len(building_elements) == 0:
        st.error("⚠️ Building elements data required. Please complete Step 4 (Facade & Window Extraction) first.")
        return
    
    project_data = st.session_state.get('project_data', {})
    radiation_data = project_data.get('radiation_data')
    
    if radiation_data is None or len(radiation_data) == 0:
        st.error("⚠️ Radiation analysis required. Please complete Step 5 (Solar Radiation Analysis) first.")
        return
    
    # Use building_elements as primary source
    suitable_elements = building_elements
    
    st.success(f"Designing BIPV systems for {len(suitable_elements)} building elements")
    
    # Panel selection section
    st.subheader("🔧 BIPV Panel Selection")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_panel_type = st.selectbox(
            "Select BIPV Panel Type",
            list(BIPV_PANEL_DATABASE.keys()),
            index=0,
            help="Choose BIPV panel technology based on your requirements. Standard BIPV Glass (16% efficiency, moderate cost), High-Efficiency Cells (20% efficiency, premium cost), or Transparent Thin-Film (12% efficiency, high transparency). Consider efficiency vs transparency trade-offs for your application.",
            key="selected_panel_type"
        )
        
        panel_specs = BIPV_PANEL_DATABASE[selected_panel_type]
        
        st.info(f"**{selected_panel_type}**: {panel_specs['description']}")
    
    with col2:
        st.metric("Panel Efficiency", f"{panel_specs['efficiency']*100:.1f}%")
        st.metric("Power Rating", f"{panel_specs['power_rating']} Wp")
        st.metric("Transparency", f"{panel_specs['transparency']*100:.0f}%")
    
    # Panel specifications display
    with st.expander("📋 Technical Specifications", expanded=False):
        spec_col1, spec_col2, spec_col3 = st.columns(3)
        
        with spec_col1:
            st.write("**Physical Properties**")
            st.write(f"• Width: {panel_specs['dimensions']['width']:.2f} m")
            st.write(f"• Height: {panel_specs['dimensions']['height']:.2f} m")
            st.write(f"• Thickness: {panel_specs['dimensions']['thickness']*1000:.0f} mm")
            
        with spec_col2:
            st.write("**Performance**")
            st.write(f"• Efficiency: {panel_specs['efficiency']*100:.1f}%")
            st.write(f"• Power Rating: {panel_specs['power_rating']} Wp")
            st.write(f"• Temp. Coefficient: {panel_specs['temperature_coefficient']*100:.2f}%/°C")
            
        with spec_col3:
            st.write("**Economic**")
            st.write(f"• Cost: €{panel_specs['cost_per_wp']:.2f}/Wp")
            st.write(f"• Warranty: {panel_specs['warranty_years']} years")
            st.write(f"• Transparency: {panel_specs['transparency']*100:.0f}%")
    
    # Advanced configuration
    with st.expander("⚙️ Advanced Configuration", expanded=False):
        config_col1, config_col2 = st.columns(2)
        
        with config_col1:
            performance_ratio = st.slider(
                "System Performance Ratio",
                0.70, 0.95, 0.85, 0.01,
                help="⚡ System Performance Ratio accounts for real-world losses: inverter efficiency (95-98%), DC/AC wiring losses (2-3%), soiling/dust (2-5%), module mismatch (1-3%), and temperature effects. Typical BIPV systems: 0.80-0.90. Higher values indicate better system design and maintenance.",
                key="performance_ratio_pv"
            )
            
            installation_cost_factor = st.slider(
                "Installation Cost Factor",
                0.3, 0.8, 0.5, 0.05,
                help="🔨 Installation cost as fraction of panel cost. Includes labor, mounting systems, electrical work, permits, and commissioning. Simple installations: 0.3-0.4, Standard BIPV: 0.4-0.6, Complex façade integration: 0.6-0.8. Higher values reflect complex glazing system integration.",
                key="installation_cost_factor_pv"
            )
        
        with config_col2:
            inverter_cost_per_kw = st.number_input(
                "Inverter Cost (€/kW)",
                100, 300, 150, 10,
                help="Cost of power electronics per kW",
                key="inverter_cost_per_kw_pv"
            )
            
            min_system_size = st.number_input(
                "Minimum System Size (kW)",
                0.05, 5.0, 0.1, 0.05,
                help="Minimum viable system size for BIPV installation",
                key="min_system_size_pv"
            )
    
    # System design calculation
    if st.button("🚀 Calculate BIPV System Specifications", key="calculate_pv_specs"):
        with st.spinner("Calculating optimal BIPV system designs..."):
            try:
                # Update panel specs with user configurations
                panel_specs_updated = panel_specs.copy()
                
                # Calculate system specifications
                pv_specifications = calculate_system_specifications(
                    suitable_elements, panel_specs_updated, radiation_data
                )
                
                # Filter by minimum system size (more flexible for BIPV)
                viable_systems = pv_specifications[
                    pv_specifications['system_power_kw'] >= min_system_size
                ]
                
                if len(viable_systems) == 0:
                    # Show all systems with warning about small sizes
                    st.warning(f"No systems meet minimum size of {min_system_size:.2f} kW. Showing all calculated systems:")
                    st.info("Consider reducing minimum system size for small BIPV installations.")
                    viable_systems = pv_specifications
                
                pv_specifications = viable_systems
                
                # Save to session state and database
                st.session_state.project_data['pv_specifications'] = pv_specifications
                st.session_state.project_data['selected_panel_specs'] = panel_specs_updated
                st.session_state.pv_specs_completed = True
                
                # Save to database if project_id exists
                if 'project_id' in st.session_state and st.session_state.project_id:
                    try:
                        db_manager.save_pv_specifications(
                            st.session_state.project_id,
                            {
                                'panel_type': selected_panel_type,
                                'panel_specifications': panel_specs_updated,
                                'system_specifications': pv_specifications.to_dict('records'),
                                'configuration': {
                                    'performance_ratio': performance_ratio,
                                    'installation_cost_factor': installation_cost_factor,
                                    'inverter_cost_per_kw': inverter_cost_per_kw,
                                    'min_system_size': min_system_size
                                }
                            }
                        )
                    except Exception as db_error:
                        st.warning(f"Could not save to database: {str(db_error)}")
                else:
                    st.info("PV specifications saved to session only (no project ID available)")
                
                st.success("✅ BIPV system specifications calculated successfully!")
                
            except Exception as e:
                st.error(f"Error calculating system specifications: {str(e)}")
                return
    
    # Display results if available
    if st.session_state.get('pv_specs_completed', False):
        pv_specs = st.session_state.project_data.get('pv_specifications')
        
        if pv_specs is not None and len(pv_specs) > 0:
            st.subheader("📊 BIPV System Design Results")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_power = pv_specs['system_power_kw'].sum()
                st.metric("Total System Power", f"{total_power:.1f} kW")
            
            with col2:
                total_energy = pv_specs['annual_energy_kwh'].sum()
                st.metric("Total Annual Energy", f"{total_energy:.0f} kWh")
            
            with col3:
                total_cost = pv_specs['total_installation_cost'].sum()
                st.metric("Total Investment", f"€{total_cost:,.0f}")
            
            with col4:
                avg_specific_yield = pv_specs['specific_yield'].mean()
                st.metric("Avg Specific Yield", f"{avg_specific_yield:.0f} kWh/kWp")
            
            # Detailed system specifications
            st.subheader("📋 Individual System Specifications")
            
            # Prepare display dataframe
            display_df = pv_specs.copy()
            display_columns = [
                'element_id', 'orientation', 'system_power_kw', 'annual_energy_kwh',
                'specific_yield', 'total_installation_cost', 'cost_per_kwh', 'coverage_ratio'
            ]
            
            st.dataframe(
                display_df[display_columns].round(2),
                use_container_width=True,
                column_config={
                    'element_id': 'Element ID',
                    'orientation': 'Orientation',
                    'system_power_kw': st.column_config.NumberColumn('Power (kW)', format="%.2f"),
                    'annual_energy_kwh': st.column_config.NumberColumn('Annual Energy (kWh)', format="%.0f"),
                    'specific_yield': st.column_config.NumberColumn('Specific Yield (kWh/kWp)', format="%.0f"),
                    'total_installation_cost': st.column_config.NumberColumn('Investment (€)', format="€%.0f"),
                    'cost_per_kwh': st.column_config.NumberColumn('Cost per kWh (€)', format="€%.3f"),
                    'coverage_ratio': st.column_config.NumberColumn('Coverage Ratio', format="%.2f")
                }
            )
            
            # Analysis and visualizations
            st.subheader("📈 System Performance Analysis")
            
            tab1, tab2, tab3, tab4 = st.tabs(["Power Distribution", "Economic Analysis", "Performance Metrics", "Technology Assessment"])
            
            with tab1:
                # Power by orientation
                orientation_power = pv_specs.groupby('orientation')['system_power_kw'].sum().reset_index()
                
                fig_power = px.bar(
                    orientation_power,
                    x='orientation',
                    y='system_power_kw',
                    title="Total Installed Power by Orientation",
                    labels={'system_power_kw': 'Installed Power (kW)', 'orientation': 'Orientation'}
                )
                st.plotly_chart(fig_power, use_container_width=True)
                
                # Power vs Area scatter
                fig_scatter = px.scatter(
                    pv_specs,
                    x='element_area',
                    y='system_power_kw',
                    color='orientation',
                    title="System Power vs Element Area",
                    labels={'element_area': 'Element Area (m²)', 'system_power_kw': 'System Power (kW)'}
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
            
            with tab2:
                # Cost analysis
                fig_cost_dist = px.histogram(
                    pv_specs,
                    x='cost_per_kwh',
                    title="Distribution of Cost per kWh",
                    labels={'cost_per_kwh': 'Cost per kWh (€)', 'count': 'Number of Systems'}
                )
                st.plotly_chart(fig_cost_dist, use_container_width=True)
                
                # Investment vs annual energy
                fig_invest = px.scatter(
                    pv_specs,
                    x='total_installation_cost',
                    y='annual_energy_kwh',
                    color='orientation',
                    title="Investment vs Annual Energy Production",
                    labels={'total_installation_cost': 'Investment (€)', 'annual_energy_kwh': 'Annual Energy (kWh)'}
                )
                st.plotly_chart(fig_invest, use_container_width=True)
            
            with tab3:
                # Specific yield distribution
                fig_yield = px.box(
                    pv_specs,
                    x='orientation',
                    y='specific_yield',
                    title="Specific Yield Distribution by Orientation",
                    labels={'specific_yield': 'Specific Yield (kWh/kWp)', 'orientation': 'Orientation'}
                )
                st.plotly_chart(fig_yield, use_container_width=True)
                
                # Coverage ratio analysis
                fig_coverage = px.histogram(
                    pv_specs,
                    x='coverage_ratio',
                    title="BIPV Coverage Ratio Distribution",
                    labels={'coverage_ratio': 'Coverage Ratio', 'count': 'Number of Elements'}
                )
                st.plotly_chart(fig_coverage, use_container_width=True)
            
            with tab4:
                # Technology assessment summary
                st.write("**Selected BIPV Technology Assessment**")
                
                assessment_col1, assessment_col2 = st.columns(2)
                
                with assessment_col1:
                    st.write("**Advantages:**")
                    if panel_specs['transparency'] > 0.25:
                        st.write("• High transparency for natural lighting")
                    if panel_specs['efficiency'] > 0.18:
                        st.write("• High energy conversion efficiency")
                    if panel_specs['warranty_years'] >= 25:
                        st.write("• Long-term warranty coverage")
                    st.write("• Building-integrated design")
                    st.write("• Dual functionality (glazing + energy)")
                
                with assessment_col2:
                    st.write("**Considerations:**")
                    if panel_specs['cost_per_wp'] > 1.0:
                        st.write("• Premium technology cost")
                    if panel_specs['transparency'] < 0.15:
                        st.write("• Limited natural light transmission")
                    st.write("• Specialized installation required")
                    st.write("• Grid connection and inverters needed")
                
                # Performance summary
                avg_efficiency = pv_specs['annual_energy_kwh'].sum() / pv_specs['element_area'].sum()
                st.metric("Overall System Efficiency", f"{avg_efficiency:.0f} kWh/m²/year")
            
            # Export options
            st.subheader("💾 Export System Specifications")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 Download Specifications (CSV)", key="download_pv_specs_csv"):
                    csv_data = pv_specs.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv_data,
                        file_name=f"bipv_specifications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            
            with col2:
                st.info("System specifications ready for yield analysis")
        
        else:
            st.warning("No system specifications available. Please run the calculation.")