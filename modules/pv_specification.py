import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# PV Panel Database
PV_PANEL_DATABASE = {
    "Standard Monocrystalline": {
        "efficiency": 0.20,
        "cost_per_wp": 0.45,
        "dimensions": {"width": 1.65, "height": 1.00, "thickness": 0.035},
        "power_rating": 330,
        "temperature_coefficient": -0.004,
        "warranty_years": 25,
        "description": "Standard monocrystalline silicon panels"
    },
    "High-Efficiency Monocrystalline": {
        "efficiency": 0.22,
        "cost_per_wp": 0.65,
        "dimensions": {"width": 1.65, "height": 1.00, "thickness": 0.035},
        "power_rating": 365,
        "temperature_coefficient": -0.0035,
        "warranty_years": 25,
        "description": "High-efficiency monocrystalline panels with PERC technology"
    },
    "Polycrystalline": {
        "efficiency": 0.17,
        "cost_per_wp": 0.35,
        "dimensions": {"width": 1.65, "height": 1.00, "thickness": 0.035},
        "power_rating": 280,
        "temperature_coefficient": -0.0045,
        "warranty_years": 20,
        "description": "Cost-effective polycrystalline silicon panels"
    },
    "Thin-Film (CdTe)": {
        "efficiency": 0.18,
        "cost_per_wp": 0.40,
        "dimensions": {"width": 1.20, "height": 0.60, "thickness": 0.006},
        "power_rating": 130,
        "temperature_coefficient": -0.0025,
        "warranty_years": 25,
        "description": "Lightweight thin-film panels for building integration"
    },
    "Bifacial Monocrystalline": {
        "efficiency": 0.21,
        "cost_per_wp": 0.55,
        "dimensions": {"width": 1.65, "height": 1.00, "thickness": 0.035},
        "power_rating": 350,
        "temperature_coefficient": -0.0037,
        "warranty_years": 30,
        "description": "Bifacial panels capturing light from both sides"
    },
    "Building-Integrated (BIPV)": {
        "efficiency": 0.16,
        "cost_per_wp": 0.85,
        "dimensions": {"width": 1.00, "height": 1.50, "thickness": 0.008},
        "power_rating": 240,
        "temperature_coefficient": -0.004,
        "warranty_years": 25,
        "description": "Specialized panels designed for building integration"
    }
}

def calculate_panel_layout(element_area, element_width, element_height, panel_width, panel_height, spacing_factor=0.05):
    """Calculate optimal panel layout for given element dimensions."""
    
    # Account for spacing between panels
    effective_panel_width = panel_width * (1 + spacing_factor)
    effective_panel_height = panel_height * (1 + spacing_factor)
    
    # Calculate how many panels fit in each dimension
    panels_horizontal = int(element_width // effective_panel_width)
    panels_vertical = int(element_height // effective_panel_height)
    
    # Total panels and coverage
    total_panels = panels_horizontal * panels_vertical
    panel_area = panel_width * panel_height
    total_panel_area = total_panels * panel_area
    coverage_ratio = total_panel_area / element_area if element_area > 0 else 0
    
    return {
        'panels_horizontal': panels_horizontal,
        'panels_vertical': panels_vertical,
        'total_panels': total_panels,
        'total_panel_area': total_panel_area,
        'coverage_ratio': coverage_ratio,
        'unused_area': element_area - total_panel_area
    }

def calculate_system_specifications(element_data, panel_specs, layout_data):
    """Calculate complete system specifications for each element."""
    
    specifications = []
    
    for i, (_, element) in enumerate(element_data.iterrows()):
        layout = layout_data[i]
        
        if layout['total_panels'] > 0:
            # Basic calculations
            total_power = layout['total_panels'] * panel_specs['power_rating']
            total_cost = total_power * panel_specs['cost_per_wp']
            
            # Performance calculations
            annual_irradiation = element.get('corrected_annual_irradiation', element.get('annual_irradiation', 1500))
            annual_energy = (total_power / 1000) * annual_irradiation * panel_specs['efficiency'] / 0.20  # Normalize efficiency
            
            spec = {
                'element_id': element['element_id'],
                'element_type': element.get('element_type', 'Unknown'),
                'element_area': element['area'],
                'orientation': element['orientation'],
                'panels_count': layout['total_panels'],
                'panel_area': layout['total_panel_area'],
                'coverage_ratio': layout['coverage_ratio'],
                'system_power_kw': total_power / 1000,
                'annual_energy_kwh': annual_energy,
                'specific_yield': annual_energy / (total_power / 1000) if total_power > 0 else 0,
                'installation_cost': total_cost,
                'cost_per_kwh': total_cost / annual_energy if annual_energy > 0 else float('inf'),
                'panels_horizontal': layout['panels_horizontal'],
                'panels_vertical': layout['panels_vertical']
            }
            
            specifications.append(spec)
    
    return pd.DataFrame(specifications)

def render_pv_specification():
    """Render the PV panel specification and layout module."""
    
    st.header("6. PV Panel Specification")
    st.markdown("Configure PV panel specifications and calculate optimal layouts for each surface.")
    
    # Check prerequisites
    if 'radiation_grid' not in st.session_state.project_data:
        st.warning("⚠️ Please complete radiation analysis in Step 5 before proceeding.")
        return
    
    # Load radiation data
    radiation_df = pd.DataFrame(st.session_state.project_data['radiation_grid'])
    
    st.subheader("Panel Selection and Configuration")
    
    # Panel type selection
    col1, col2 = st.columns(2)
    
    with col1:
        selected_panel_type = st.selectbox(
            "Select PV Panel Type",
            list(PV_PANEL_DATABASE.keys()),
            help="Choose the type of PV panel for your installation"
        )
        
        panel_specs = PV_PANEL_DATABASE[selected_panel_type]
        
        # Display panel specifications
        st.markdown("**Selected Panel Specifications:**")
        spec_data = {
            "Specification": ["Efficiency", "Power Rating", "Cost per Wp", "Width", "Height", "Thickness", "Warranty"],
            "Value": [
                f"{panel_specs['efficiency']*100:.1f}%",
                f"{panel_specs['power_rating']} W",
                f"${panel_specs['cost_per_wp']:.2f}/Wp",
                f"{panel_specs['dimensions']['width']:.2f} m",
                f"{panel_specs['dimensions']['height']:.2f} m",
                f"{panel_specs['dimensions']['thickness']*1000:.0f} mm",
                f"{panel_specs['warranty_years']} years"
            ]
        }
        st.table(spec_data)
    
    with col2:
        # Custom panel specifications
        st.markdown("**Custom Panel Settings:**")
        
        custom_efficiency = st.number_input(
            "Panel Efficiency (%)",
            value=panel_specs['efficiency'] * 100,
            min_value=10.0,
            max_value=30.0,
            step=0.1,
            help="Panel efficiency under standard test conditions"
        ) / 100
        
        custom_cost = st.number_input(
            "Cost per Wp ($)",
            value=panel_specs['cost_per_wp'],
            min_value=0.20,
            max_value=2.00,
            step=0.05,
            help="Cost per watt-peak installed"
        )
        
        custom_power = st.number_input(
            "Panel Power Rating (W)",
            value=panel_specs['power_rating'],
            min_value=50,
            max_value=500,
            step=5,
            help="Nominal power rating of each panel"
        )
        
        # Override panel specs with custom values
        panel_specs['efficiency'] = custom_efficiency
        panel_specs['cost_per_wp'] = custom_cost
        panel_specs['power_rating'] = custom_power
    
    # Installation configuration
    st.subheader("Installation Configuration")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        spacing_factor = st.slider(
            "Panel Spacing Factor",
            min_value=0.0,
            max_value=0.20,
            value=0.05,
            step=0.01,
            help="Additional spacing between panels (as fraction of panel size)"
        )
    
    with col2:
        min_panels = st.number_input(
            "Minimum Panels per Element",
            value=1,
            min_value=1,
            max_value=10,
            help="Minimum number of panels required to install on an element"
        )
    
    with col3:
        installation_factor = st.slider(
            "Installation Cost Factor",
            min_value=1.0,
            max_value=3.0,
            value=1.5,
            step=0.1,
            help="Multiplier for total installation cost (includes labor, mounting, etc.)"
        )
    
    # Calculate layouts and specifications
    if st.button("Calculate Panel Layouts"):
        with st.spinner("Calculating optimal panel layouts for all elements..."):
            try:
                # Calculate layouts for each element
                layout_results = []
                
                for _, element in radiation_df.iterrows():
                    # Estimate element dimensions (simplified)
                    aspect_ratio = element.get('aspect_ratio', 1.5)
                    element_width = np.sqrt(element['area'] * aspect_ratio)
                    element_height = element['area'] / element_width
                    
                    layout = calculate_panel_layout(
                        element['area'],
                        element_width,
                        element_height,
                        panel_specs['dimensions']['width'],
                        panel_specs['dimensions']['height'],
                        spacing_factor
                    )
                    
                    layout_results.append(layout)
                
                # Calculate system specifications
                system_specs = calculate_system_specifications(radiation_df, panel_specs, layout_results)
                
                # Filter by minimum panels requirement
                system_specs = system_specs[system_specs['panels_count'] >= min_panels]
                
                # Apply installation cost factor
                system_specs['total_installation_cost'] = system_specs['installation_cost'] * installation_factor
                system_specs['total_cost_per_kwh'] = system_specs['total_installation_cost'] / system_specs['annual_energy_kwh']
                
                # Store results
                st.session_state.project_data['pv_specifications'] = system_specs.to_dict()
                st.session_state.project_data['selected_panel_type'] = selected_panel_type
                st.session_state.project_data['panel_specs'] = panel_specs
                
                st.success(f"✅ Layout calculated for {len(system_specs)} viable elements!")
                
                # Display summary
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Elements", len(system_specs))
                with col2:
                    st.metric("Total Panels", system_specs['panels_count'].sum())
                with col3:
                    st.metric("Total System Power", f"{system_specs['system_power_kw'].sum():.1f} kW")
                with col4:
                    st.metric("Total Annual Energy", f"{system_specs['annual_energy_kwh'].sum():.0f} kWh")
                
            except Exception as e:
                st.error(f"❌ Error calculating layouts: {str(e)}")
                return
    
    # Display specifications if available
    if 'pv_specifications' in st.session_state.project_data:
        specs_df = pd.DataFrame(st.session_state.project_data['pv_specifications'])
        
        st.subheader("System Specifications Summary")
        
        # Overall system metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total System Size", f"{specs_df['system_power_kw'].sum():.1f} kW")
        with col2:
            st.metric("Annual Energy Production", f"{specs_df['annual_energy_kwh'].sum():.0f} kWh")
        with col3:
            st.metric("Average Specific Yield", f"{specs_df['specific_yield'].mean():.0f} kWh/kW")
        with col4:
            st.metric("Total Installation Cost", f"${specs_df['total_installation_cost'].sum():,.0f}")
        
        # Performance analysis
        col1, col2 = st.columns(2)
        
        with col1:
            # System size distribution
            fig_power = px.bar(specs_df.nlargest(15, 'system_power_kw'),
                              x='element_id',
                              y='system_power_kw',
                              color='orientation',
                              title='Top 15 Elements by System Power',
                              labels={'system_power_kw': 'System Power (kW)'})
            st.plotly_chart(fig_power, use_container_width=True)
        
        with col2:
            # Energy production distribution
            fig_energy = px.bar(specs_df.nlargest(15, 'annual_energy_kwh'),
                               x='element_id',
                               y='annual_energy_kwh',
                               color='orientation',
                               title='Top 15 Elements by Annual Energy',
                               labels={'annual_energy_kwh': 'Annual Energy (kWh)'})
            st.plotly_chart(fig_energy, use_container_width=True)
        
        # Cost analysis
        st.subheader("Cost Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Cost per orientation
            cost_by_orientation = specs_df.groupby('orientation').agg({
                'total_installation_cost': 'sum',
                'annual_energy_kwh': 'sum'
            }).reset_index()
            cost_by_orientation['cost_per_kwh'] = cost_by_orientation['total_installation_cost'] / cost_by_orientation['annual_energy_kwh']
            
            fig_cost_orient = px.bar(cost_by_orientation,
                                    x='orientation',
                                    y='cost_per_kwh',
                                    title='Cost per kWh by Orientation',
                                    labels={'cost_per_kwh': 'Cost per kWh ($/kWh)'})
            st.plotly_chart(fig_cost_orient, use_container_width=True)
        
        with col2:
            # Coverage ratio analysis
            fig_coverage = px.scatter(specs_df,
                                     x='coverage_ratio',
                                     y='specific_yield',
                                     color='orientation',
                                     size='system_power_kw',
                                     title='Coverage Ratio vs Specific Yield',
                                     labels={'coverage_ratio': 'Panel Coverage Ratio',
                                            'specific_yield': 'Specific Yield (kWh/kW)'})
            st.plotly_chart(fig_coverage, use_container_width=True)
        
        # Detailed specifications table
        st.subheader("Detailed Specifications Table")
        
        # Select columns for display
        display_columns = ['element_id', 'orientation', 'panels_count', 'system_power_kw',
                          'annual_energy_kwh', 'specific_yield', 'coverage_ratio', 'total_installation_cost']
        
        display_df = specs_df[display_columns].round(2)
        display_df = display_df.sort_values('system_power_kw', ascending=False)
        
        # Format currency columns
        display_df['total_installation_cost'] = display_df['total_installation_cost'].apply(lambda x: f"${x:,.0f}")
        
        st.dataframe(display_df, use_container_width=True)
        
        # Layout visualization for top elements
        st.subheader("Panel Layout Examples")
        
        top_elements = specs_df.nlargest(6, 'system_power_kw')
        
        layout_data = []
        for _, element in top_elements.iterrows():
            layout_data.append({
                'Element ID': element['element_id'],
                'Orientation': element['orientation'],
                'Panels (H×V)': f"{element['panels_horizontal']}×{element['panels_vertical']}",
                'Total Panels': element['panels_count'],
                'Coverage': f"{element['coverage_ratio']*100:.1f}%",
                'Power': f"{element['system_power_kw']:.1f} kW"
            })
        
        st.table(layout_data)
        
        # Export specifications
        st.subheader("Export Specifications")
        
        if st.button("Export PV Specifications"):
            csv_data = specs_df.to_csv(index=False)
            st.download_button(
                label="Download PV Specifications CSV",
                data=csv_data,
                file_name="pv_system_specifications.csv",
                mime="text/csv"
            )
        
        st.success("✅ PV panel specifications completed! Ready for yield analysis.")
        
    else:
        st.info("👆 Please calculate panel layouts to proceed with system specifications.")
        
        # Show panel comparison
        with st.expander("🔧 Panel Type Comparison"):
            comparison_data = []
            for panel_type, specs in PV_PANEL_DATABASE.items():
                comparison_data.append({
                    'Panel Type': panel_type,
                    'Efficiency': f"{specs['efficiency']*100:.1f}%",
                    'Power': f"{specs['power_rating']} W",
                    'Cost': f"${specs['cost_per_wp']:.2f}/Wp",
                    'Size': f"{specs['dimensions']['width']:.2f}×{specs['dimensions']['height']:.2f} m",
                    'Best For': specs['description']
                })
            
            st.table(comparison_data)
