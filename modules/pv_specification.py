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

def render_pv_specification():
    """Render the BIPV glass specification and system design module."""
    
    st.header("🏢 Step 6: BIPV Glass Specification & System Design")
    st.markdown("Configure semi-transparent photovoltaic glass to replace existing window glass in your building.")
    
    # AI Model Performance Impact Notice
    project_data = st.session_state.get('project_data', {})
    if project_data.get('model_r2_score') is not None:
        r2_score = project_data['model_r2_score']
        status = project_data.get('model_performance_status', 'Unknown')
        
        if r2_score >= 0.85:
            icon = "🟢"
        elif r2_score >= 0.70:
            icon = "🟡"
        else:
            icon = "🔴"
        
        st.info(f"{icon} System design uses building data processed in previous steps (Model R² score: **{r2_score:.3f}** - {status} performance)")
    
    # Check prerequisites
    if not st.session_state.get('radiation_completed', False):
        st.error("⚠️ Radiation analysis required. Please complete Step 5 (Radiation & Shading Grid) first.")
        return
    
    # Load building elements data
    if 'radiation_grid' not in st.session_state.project_data:
        st.error("⚠️ No radiation analysis data available.")
        return
    
    radiation_df = pd.DataFrame(st.session_state.project_data['radiation_grid'])
    
    st.subheader("BIPV Glass Technology Selection")
    
    # BIPV glass type selection
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
            help="Cost per square meter of BIPV glass"
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
        installation_factor = st.slider(
            "Installation Cost Factor",
            min_value=1.0,
            max_value=2.5,
            value=1.5,
            step=0.1,
            help="Multiplier for installation costs (includes inverter, wiring, labor)"
        )
    
    with col3:
        min_glass_area = st.number_input(
            "Minimum Glass Area (m²)",
            min_value=0.1,
            max_value=5.0,
            value=0.5,
            step=0.1,
            help="Minimum glazed area required for BIPV installation"
        )
    
    # Calculate BIPV systems button
    if st.button("🔧 Calculate BIPV Glass Systems", key="calculate_bipv_glass"):
        with st.spinner("Calculating BIPV glass specifications..."):
            try:
                # Calculate BIPV glass coverage for each element
                coverage_results = []
                
                for _, element in radiation_df.iterrows():
                    # Calculate BIPV glass coverage (no separate panels)
                    coverage = calculate_bipv_glass_coverage(
                        element['area'],
                        frame_factor
                    )
                    coverage_results.append(coverage)
                
                # Calculate BIPV system specifications
                system_specs = calculate_bipv_system_specifications(radiation_df, glass_specs, coverage_results)
                
                # Filter by minimum glass area requirement
                system_specs = system_specs[system_specs['glass_area'] >= min_glass_area]
                
                # Apply installation cost factor
                system_specs['total_installation_cost'] = system_specs['installation_cost'] * installation_factor
                system_specs['total_cost_per_kwh'] = system_specs['total_installation_cost'] / system_specs['annual_energy_kwh']
                
                # Store results
                st.session_state.project_data['pv_specifications'] = system_specs.to_dict()
                st.session_state.project_data['selected_glass_type'] = selected_glass_type
                st.session_state.project_data['glass_specs'] = glass_specs
                
                st.success(f"✅ BIPV glass specifications calculated for {len(system_specs)} viable windows!")
                
                # Display summary
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Windows", len(system_specs))
                with col2:
                    st.metric("Total Glass Area", f"{system_specs['glass_area'].sum():.1f} m²")
                with col3:
                    st.metric("Total System Power", f"{system_specs['system_power_kw'].sum():.1f} kW")
                with col4:
                    st.metric("Total Annual Energy", f"{system_specs['annual_energy_kwh'].sum():.0f} kWh")
                
                # Results visualization
                st.subheader("BIPV Glass System Results")
                
                # Individual System Specifications
                with st.expander("📋 Individual BIPV Glass Specifications", expanded=False):
                    display_df = system_specs.copy()
                    display_df['glass_area'] = display_df['glass_area'].round(2)
                    display_df['system_power_kw'] = display_df['system_power_kw'].round(2)
                    display_df['annual_energy_kwh'] = display_df['annual_energy_kwh'].round(0)
                    display_df['transparency'] = (display_df['transparency'] * 100).round(0).astype(str) + '%'
                    display_df['efficiency'] = (display_df['efficiency'] * 100).round(1).astype(str) + '%'
                    
                    st.dataframe(
                        display_df[['element_id', 'orientation', 'glass_area', 'system_power_kw', 
                                   'annual_energy_kwh', 'transparency', 'efficiency', 'total_cost']],
                        use_container_width=True
                    )
                
                # Performance analysis
                fig_power = px.bar(
                    system_specs.head(20), 
                    x='element_id', 
                    y='system_power_kw',
                    color='orientation',
                    title="BIPV Glass Power by Window Element"
                )
                fig_power.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_power, use_container_width=True)
                
                # Mark step as completed
                st.session_state['pv_specs_completed'] = True
                
                # Save to database
                try:
                    from database_manager import BIPVDatabaseManager
                    db_manager = BIPVDatabaseManager()
                    
                    project_name = st.session_state.project_data.get('project_name', 'Unnamed Project')
                    db_manager.save_pv_specifications(project_name, {
                        'glass_type': selected_glass_type,
                        'glass_specs': glass_specs,
                        'system_specifications': system_specs.to_dict(),
                        'installation_parameters': {
                            'frame_factor': frame_factor,
                            'installation_factor': installation_factor,
                            'min_glass_area': min_glass_area
                        }
                    })
                    st.success("💾 BIPV specifications saved to database")
                except Exception as e:
                    st.warning(f"Database save failed: {str(e)}")
                
            except Exception as e:
                st.error(f"❌ Error calculating BIPV specifications: {str(e)}")
                st.write("Please check your data and try again.")
    
    # Show existing results if available
    elif 'pv_specifications' in st.session_state.project_data:
        st.subheader("Current BIPV Glass Specifications")
        
        system_specs = pd.DataFrame(st.session_state.project_data['pv_specifications'])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Windows", len(system_specs))
        with col2:
            st.metric("Total Glass Area", f"{system_specs['glass_area'].sum():.1f} m²")
        with col3:
            st.metric("Total System Power", f"{system_specs['system_power_kw'].sum():.1f} kW")
        with col4:
            st.metric("Total Annual Energy", f"{system_specs['annual_energy_kwh'].sum():.0f} kWh")
        
        st.info("BIPV glass specifications already calculated. Use the button above to recalculate with different parameters.")