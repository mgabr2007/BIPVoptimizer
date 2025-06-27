import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# BIPV Glass Technology Database
BIPV_GLASS_DATABASE = {
    "Semi-Transparent a-Si": {
        "efficiency": 0.06,
        "cost_per_m2": 280,
        "transparency": 0.25,
        "glass_thickness": 0.012,
        "power_per_m2": 60,
        "temperature_coefficient": -0.002,
        "warranty_years": 20,
        "description": "Amorphous silicon BIPV glass with 25% transparency"
    },
    "Semi-Transparent μc-Si": {
        "efficiency": 0.08,
        "cost_per_m2": 350,
        "transparency": 0.20,
        "glass_thickness": 0.015,
        "power_per_m2": 80,
        "temperature_coefficient": -0.0025,
        "warranty_years": 25,
        "description": "Microcrystalline silicon BIPV glass with 20% transparency"
    },
    "CdTe Transparent": {
        "efficiency": 0.10,
        "cost_per_m2": 320,
        "transparency": 0.30,
        "glass_thickness": 0.008,
        "power_per_m2": 100,
        "temperature_coefficient": -0.002,
        "warranty_years": 25,
        "description": "Cadmium telluride transparent BIPV glass"
    },
    "Organic PV Glass": {
        "efficiency": 0.04,
        "cost_per_m2": 200,
        "transparency": 0.40,
        "glass_thickness": 0.005,
        "power_per_m2": 40,
        "temperature_coefficient": -0.003,
        "warranty_years": 15,
        "description": "Flexible organic photovoltaic glass with high transparency"
    },
    "Perovskite Tandem": {
        "efficiency": 0.12,
        "cost_per_m2": 450,
        "transparency": 0.15,
        "glass_thickness": 0.010,
        "power_per_m2": 120,
        "temperature_coefficient": -0.0035,
        "warranty_years": 20,
        "description": "Advanced perovskite-silicon tandem BIPV glass technology"
    }
}

def calculate_bipv_glass_coverage(element_area, frame_factor=0.10):
    """Calculate BIPV glass coverage for window elements."""
    
    # Net glazed area after accounting for window frame
    glazed_area = element_area * (1 - frame_factor)
    frame_area = element_area * frame_factor
    
    # BIPV glass covers the entire glazed area (no separate panels)
    coverage_ratio = (1 - frame_factor)
    
    return {
        'total_area': element_area,
        'glazed_area': glazed_area,
        'frame_area': frame_area,
        'coverage_ratio': coverage_ratio,
        'bipv_glass_area': glazed_area
    }

def calculate_bipv_system_specifications(element_data, glass_specs, coverage_data):
    """Calculate complete BIPV system specifications for each element."""
    
    specifications = []
    
    for i, (_, element) in enumerate(element_data.iterrows()):
        coverage = coverage_data[i]
        
        if coverage['bipv_glass_area'] > 0:
            # Basic calculations for BIPV glass
            glass_area = coverage['bipv_glass_area']
            total_power = glass_area * glass_specs['power_per_m2'] / 1000  # Convert to kW
            total_cost = glass_area * glass_specs['cost_per_m2']
            
            # Performance calculations for BIPV glass
            annual_radiation = element.get('annual_radiation', 1200)  # kWh/m²/year
            performance_ratio = 0.85  # BIPV glass performance ratio
            annual_energy = glass_area * glass_specs['efficiency'] * annual_radiation * performance_ratio
            
            # Specific yield (kWh/kWp)
            specific_yield = annual_energy / total_power if total_power > 0 else 0
            
            # Installation costs
            installation_cost = total_cost * 1.5  # Including inverter, wiring, etc.
            
            specification = {
                'element_id': element.get('Element ID', f'Element_{i+1}'),
                'orientation': element.get('orientation', 'Unknown'),
                'glass_area': glass_area,
                'frame_area': coverage['frame_area'],
                'total_area': coverage['total_area'],
                'system_power_kw': total_power,
                'annual_energy_kwh': annual_energy,
                'specific_yield': specific_yield,
                'glass_cost': total_cost,
                'installation_cost': installation_cost,
                'total_cost': total_cost + installation_cost,
                'cost_per_kwh': (total_cost + installation_cost) / annual_energy if annual_energy > 0 else 0,
                'transparency': glass_specs['transparency'],
                'efficiency': glass_specs['efficiency'],
                'annual_radiation': annual_radiation
            }
            
            specifications.append(specification)
    
    return pd.DataFrame(specifications)
            
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
        selected_glass_type = st.selectbox(
            "Select BIPV Glass Technology",
            list(BIPV_GLASS_DATABASE.keys()),
            help="Choose semi-transparent photovoltaic glass to replace existing window glass"
        )
        
        glass_specs = BIPV_GLASS_DATABASE[selected_glass_type]
        
        # Display BIPV glass specifications
        st.markdown("**Selected BIPV Glass Specifications:**")
        spec_data = {
            "Specification": ["Efficiency", "Power per m²", "Cost per m²", "Transparency", "Glass Thickness", "Warranty"],
            "Value": [
                f"{glass_specs['efficiency']*100:.1f}%",
                f"{glass_specs['power_per_m2']} W/m²",
                f"€{glass_specs['cost_per_m2']:.0f}/m²",
                f"{glass_specs['transparency']*100:.0f}%",
                f"{glass_specs['glass_thickness']*1000:.0f} mm",
                f"{glass_specs['warranty_years']} years"
            ]
        }
        st.table(spec_data)
        
        st.info("💡 BIPV glass replaces existing window glass with semi-transparent photovoltaic material")
    
    with col2:
        # Custom glass specifications
        st.markdown("**Custom BIPV Glass Settings:**")
        
        custom_efficiency = st.number_input(
            "Glass Efficiency (%)",
            value=glass_specs['efficiency'] * 100,
            min_value=2.0,
            max_value=15.0,
            step=0.1,
            help="BIPV glass efficiency under standard test conditions"
        ) / 100
        
        custom_cost = st.number_input(
            "Cost per m² (€)",
            value=glass_specs['cost_per_m2'],
            min_value=150.0,
            max_value=600.0,
            step=10.0,
            help="Cost per watt-peak installed"
        )
        
        custom_transparency = st.slider(
            "Glass Transparency (%)",
            min_value=10,
            max_value=50,
            value=int(glass_specs['transparency'] * 100),
            step=5,
            help="Visible light transmission through BIPV glass"
        ) / 100
        
        # Override glass specs with custom values
        glass_specs['efficiency'] = custom_efficiency
        glass_specs['cost_per_m2'] = custom_cost  
        glass_specs['transparency'] = custom_transparency
    
    # BIPV Glass Installation Configuration
    st.subheader("BIPV Glass Installation Configuration")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        frame_factor = st.slider(
            "Window Frame Factor",
            min_value=0.05,
            max_value=0.25,
            value=0.10,
            step=0.01,
            help="Percentage of window area occupied by frame (non-glazed area)"
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
                    # Calculate BIPV glass coverage (no separate panels)
                    coverage = calculate_bipv_glass_coverage(
                        element['area'],
                        frame_factor
                    )
                    layout_results.append(coverage)
                
                # Calculate BIPV system specifications
                system_specs = calculate_bipv_system_specifications(radiation_df, glass_specs, layout_results)
                
                # Filter by minimum glass area requirement (0.5 m² minimum)
                system_specs = system_specs[system_specs['glass_area'] >= 0.5]
                
                # Apply installation cost factor
                system_specs['total_installation_cost'] = system_specs['installation_cost'] * installation_factor
                system_specs['total_cost_per_kwh'] = system_specs['total_installation_cost'] / system_specs['annual_energy_kwh']
                
                # Store results
                st.session_state.project_data['pv_specifications'] = system_specs.to_dict()
                st.session_state.project_data['selected_glass_type'] = selected_glass_type
                st.session_state.project_data['glass_specs'] = glass_specs
                
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
