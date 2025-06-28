"""
PV Panel Specification & Layout page for BIPV Optimizer
Enhanced with comprehensive BIPV panel selection interface
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from database_manager import db_manager
from datetime import datetime
from core.solar_math import safe_divide

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
    """Calculate BIPV glass coverage for window elements.
    BIPV glass replaces entire window surface with semi-transparent PV glass."""
    
    # BIPV glass covers the entire window area (minus frame)
    bipv_glass_area = element_area * coverage_factor
    coverage_ratio = coverage_factor
    
    return {
        'bipv_glass_area': bipv_glass_area,
        'coverage_ratio': coverage_ratio,
        'frame_factor': 1.0 - coverage_factor
    }

def calculate_bipv_system_specifications(element_data, glass_specs, radiation_data):
    """Calculate complete BIPV system specifications for each element using comprehensive panel specs."""
    
    specifications = []
    
    # Handle both DataFrame and list inputs
    if hasattr(element_data, 'iterrows'):
        elements_iter = element_data.iterrows()
    else:
        elements_iter = enumerate(element_data)
    
    for _, element in elements_iter:
        element_id = element.get('Element ID', element.get('element_id', ''))
        element_area = float(element.get('Glass Area (m²)', element.get('area', 1.5)))
        
        # Get radiation data for this element
        if hasattr(radiation_data, 'iterrows'):
            element_radiation = radiation_data[radiation_data['element_id'] == element_id]
            if len(element_radiation) > 0:
                annual_irradiation = float(element_radiation.iloc[0]['annual_irradiation'])
            else:
                annual_irradiation = 1000  # kWh/m²/year - default for Central Europe
        else:
            annual_irradiation = 1000  # Default fallback
        
        # Calculate BIPV glass coverage (replaces entire window surface)
        coverage = calculate_bipv_glass_coverage(element_area, coverage_factor=0.90)
        
        if coverage['bipv_glass_area'] > 0 and annual_irradiation > 0:
            # System power calculation using BIPV glass area and power density
            system_power_wp = coverage['bipv_glass_area'] * glass_specs['glass_properties']['power_density']
            system_power_kw = system_power_wp / 1000
            
            # Annual energy production using comprehensive performance ratio
            annual_energy_kwh = system_power_kw * annual_irradiation * glass_specs['performance_ratio']
            
            # Cost calculations using comprehensive economic specs
            panel_cost = system_power_wp * glass_specs['cost_per_wp']
            installation_cost = panel_cost * glass_specs['installation_factor']
            inverter_cost = system_power_kw * glass_specs['inverter_cost_per_kw']
            bos_cost = system_power_kw * glass_specs['other_bos_cost']
            total_cost = panel_cost + installation_cost + inverter_cost + bos_cost
            
            # Specific yield calculation
            specific_yield = safe_divide(annual_energy_kwh, system_power_kw, 0)
            
            specification = {
                'element_id': element_id,
                'element_area': element_area,
                'bipv_glass_area': coverage['bipv_glass_area'],
                'coverage_ratio': coverage['coverage_ratio'],
                'frame_factor': coverage['frame_factor'],
                'system_power_wp': system_power_wp,
                'system_power_kw': system_power_kw,
                'annual_energy_kwh': annual_energy_kwh,
                'specific_yield': specific_yield,
                'panel_cost': panel_cost,
                'installation_cost': installation_cost,
                'inverter_cost': inverter_cost,
                'bos_cost': bos_cost,
                'total_installation_cost': total_cost,
                'cost_per_kwh': safe_divide(total_cost, annual_energy_kwh, 0),
                'annual_irradiation': annual_irradiation,
                'orientation': element.get('orientation', element.get('Orientation', 'Unknown')),
                'transparency': glass_specs['transparency'],
                'efficiency': glass_specs['efficiency'],
                'temperature_coefficient': glass_specs['temperature_coefficient'],
                'warranty_years': glass_specs['warranty_years'],
                'degradation_rate': glass_specs['degradation_rate']
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
    st.subheader("🔧 BIPV Panel Selection & Customization")
    
    # Create two columns for panel selection
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
            min_value=200.0, max_value=600.0,
            value=float(base_specs['cost_per_m2']),
            step=25.0,
            key="cost_per_m2",
            help="BIPV glass cost per square meter"
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
    
    # Calculate system specifications using building elements and radiation data
    if st.button("⚡ Calculate BIPV Systems", type="primary", key="calculate_bipv_systems"):
        
        with st.spinner("Calculating BIPV system specifications for all building elements..."):
            # Calculate BIPV specifications using the simplified panel data
            bipv_specifications = calculate_bipv_system_specifications(
                suitable_elements, 
                final_panel_specs, 
                coverage_data
            )
            
            if bipv_specifications is not None and len(bipv_specifications) > 0:
                st.session_state['pv_specifications'] = bipv_specifications.to_dict('records')
                
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
                display_df = bipv_specifications[['element_id', 'glass_area_m2', 'capacity_kw', 'annual_energy_kwh', 'total_cost_eur']].copy()
                display_df.columns = ['Element ID', 'Area (m²)', 'Capacity (kW)', 'Annual Energy (kWh)', 'Cost (EUR)']
                st.dataframe(display_df, use_container_width=True)
                
            else:
                st.error("Could not calculate BIPV specifications. Please check your data.")
    
    st.markdown("---")
    st.markdown("**Next Step:** Proceed to Step 7 (Yield vs Demand Analysis) to compare energy generation with building consumption.")
            
            installation_factor = st.number_input(
                "Installation Cost Factor",
                min_value=0.3, max_value=1.0,
                value=0.5,
                step=0.05,
                key="install_factor",
                help="Installation cost as fraction of panel cost (typical: 0.5 for BIPV)"
            )
        
        with col2:
            inverter_cost_per_kw = st.number_input(
                "Inverter Cost (€/kW)",
                min_value=100, max_value=300,
                value=150,
                step=10,
                key="inverter_cost",
                help="Cost of inverters per kilowatt of installed capacity"
            )
            
            other_bos_cost = st.number_input(
                "Other BOS Cost (€/kW)",
                min_value=50, max_value=200,
                value=100,
                step=10,
                key="bos_cost",
                help="Balance of system costs: wiring, monitoring, permits"
            )
        
        with col3:
            warranty_years = st.number_input(
                "Warranty Period (years)",
                min_value=10, max_value=30,
                value=int(base_specs['warranty_years']),
                step=1,
                key="warranty_years",
                help="Manufacturer warranty period for power output"
            )
            
            degradation_rate = st.number_input(
                "Annual Degradation (%)",
                min_value=0.3, max_value=1.0,
                value=0.5,
                step=0.05,
                key="degradation_rate",
                help="Annual power output degradation rate"
            ) / 100
    
    with st.expander("🔧 Performance Specifications", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            performance_ratio = st.number_input(
                "Performance Ratio",
                min_value=0.70, max_value=0.95,
                value=0.85,
                step=0.01,
                key="performance_ratio",
                help="Overall system efficiency including inverter and wiring losses"
            )
            
            noct = st.number_input(
                "NOCT (°C)",
                min_value=40, max_value=50,
                value=45,
                step=1,
                key="noct",
                help="Nominal Operating Cell Temperature"
            )
        
        with col2:
            irradiance_threshold = st.number_input(
                "Min. Irradiance (W/m²)",
                min_value=50, max_value=200,
                value=100,
                step=10,
                key="irr_threshold",
                help="Minimum irradiance for power generation"
            )
            
            max_system_voltage = st.number_input(
                "Max System Voltage (V)",
                min_value=600, max_value=1500,
                value=1000,
                step=50,
                key="max_voltage",
                help="Maximum DC system voltage"
            )
        
        with col3:
            wind_load_resistance = st.number_input(
                "Wind Load (Pa)",
                min_value=1000, max_value=5000,
                value=2400,
                step=100,
                key="wind_load",
                help="Maximum wind load resistance"
            )
            
            hail_resistance = st.number_input(
                "Hail Resistance (mm)",
                min_value=20, max_value=35,
                value=25,
                step=1,
                key="hail_resistance",
                help="Hail ball diameter resistance"
            )
    
    # Compile final specifications
    final_panel_specs = {
        'panel_type': selected_panel_type,
        'efficiency': panel_efficiency,
        'power_density': power_density,
        'temperature_coefficient': temperature_coefficient,
        'voltage_at_pmax': voltage_at_pmax,
        'current_at_pmax': current_at_pmax,
        'fill_factor': fill_factor,
        'glass_properties': {
            'thickness': glass_thickness,
            'power_density': power_density,
            'u_value': u_value
        },
        'weight': glass_weight,
        'transparency': transparency,
        'solar_heat_gain': solar_heat_gain,
        'cost_per_wp': cost_per_wp,
        'cost_per_m2': cost_per_m2,
        'installation_factor': installation_factor,
        'inverter_cost_per_kw': inverter_cost_per_kw,
        'other_bos_cost': other_bos_cost,
        'warranty_years': warranty_years,
        'degradation_rate': degradation_rate,
        'performance_ratio': performance_ratio,
        'noct': noct,
        'irradiance_threshold': irradiance_threshold,
        'max_system_voltage': max_system_voltage,
        'wind_load_resistance': wind_load_resistance,
        'hail_resistance': hail_resistance
    }
    
    # Display customized specifications summary
    st.subheader("📊 Your Customized BIPV Specifications")
    st.markdown("**These are your final specifications that will be used for all calculations:**")
    
    # Show comparison between base and customized specs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Electrical Performance:**")
        efficiency_changed = final_panel_specs['efficiency'] != base_specs['efficiency']
        power_changed = final_panel_specs['power_density'] != base_specs['glass_properties']['power_density']
        temp_changed = final_panel_specs['temperature_coefficient'] != base_specs['temperature_coefficient']
        perf_changed = final_panel_specs['performance_ratio'] != 0.85  # Default performance ratio
        
        st.write(f"• Efficiency: {final_panel_specs['efficiency']*100:.1f}% {'🔧' if efficiency_changed else ''}")
        st.write(f"• Power Density: {final_panel_specs['power_density']} W/m² {'🔧' if power_changed else ''}")
        st.write(f"• Temperature Coeff: {final_panel_specs['temperature_coefficient']*100:.2f}%/°C {'🔧' if temp_changed else ''}")
        st.write(f"• Performance Ratio: {final_panel_specs['performance_ratio']*100:.0f}% {'🔧' if perf_changed else ''}")
    
    with col2:
        st.markdown("**BIPV Glass Properties:**")
        thickness_changed = final_panel_specs['glass_properties']['thickness'] != base_specs.get('dimensions', {}).get('thickness', 0.008)
        power_density_changed = final_panel_specs['glass_properties']['power_density'] != base_specs['efficiency']*1000
        transparency_changed = final_panel_specs['transparency'] != base_specs['transparency']
        
        st.write(f"• Glass Thickness: {final_panel_specs['glass_properties']['thickness']*1000:.1f} mm {'🔧' if thickness_changed else ''}")
        st.write(f"• Power Density: {final_panel_specs['glass_properties']['power_density']:.0f} W/m² {'🔧' if power_density_changed else ''}")
        st.write(f"• Transparency: {final_panel_specs['transparency']*100:.0f}% {'🔧' if transparency_changed else ''}")
        st.write(f"• Glass Weight: {final_panel_specs['weight']:.1f} kg/m²")
        st.write(f"• U-Value: {final_panel_specs['glass_properties']['u_value']:.1f} W/m²K")
    
    with col3:
        st.markdown("**Economic Parameters:**")
        cost_changed = final_panel_specs['cost_per_wp'] != base_specs['cost_per_wp']
        
        st.write(f"• Panel Cost: {final_panel_specs['cost_per_wp']:.2f} €/Wp {'🔧' if cost_changed else ''}")
        st.write(f"• Inverter Cost: {final_panel_specs['inverter_cost_per_kw']} €/kW")
        st.write(f"• Installation Factor: {final_panel_specs['installation_factor']*100:.0f}%")
        st.write(f"• Warranty: {final_panel_specs['warranty_years']} years")
    
    # Show modifications indicator
    modifications_made = any([
        final_panel_specs['efficiency'] != base_specs['efficiency'],
        final_panel_specs['power_density'] != base_specs['glass_properties']['power_density'],
        final_panel_specs['cost_per_wp'] != base_specs['cost_per_wp'],
        final_panel_specs['transparency'] != base_specs['transparency'],
        final_panel_specs['glass_properties']['thickness'] != base_specs['glass_properties']['thickness'],
        final_panel_specs['glass_properties']['power_density'] != base_specs['efficiency']*1000
    ])
    
    if modifications_made:
        st.success("🔧 Custom modifications detected - your personalized specifications will be used for calculations!")
    else:
        st.info(f"Using standard {selected_panel_type} specifications - modify any parameter above to customize")
    
    # Calculate system specifications using the comprehensive panel specifications
    button_text = "⚡ Calculate BIPV Systems with Custom Specifications" if modifications_made else "⚡ Calculate BIPV Systems with Standard Specifications"
    if st.button(button_text, type="primary", key="calculate_bipv_systems"):
        
        with st.spinner("Calculating BIPV system specifications for all building elements..."):
            # Calculate BIPV specifications using the comprehensive panel data
            bipv_specifications = calculate_bipv_system_specifications(
                suitable_elements, 
                final_panel_specs, 
                radiation_data
            )
            
            if len(bipv_specifications) > 0:
                st.session_state.pv_specifications = bipv_specifications
                st.session_state.pv_specs_completed = True
                st.session_state.customized_panel_specs = final_panel_specs
                st.session_state.modifications_made = modifications_made
                
                # Also store in project_data for cross-step access
                if 'project_data' not in st.session_state:
                    st.session_state.project_data = {}
                st.session_state.project_data['pv_specifications'] = bipv_specifications
                
                # Save customized specifications to database
                try:
                    # Get project ID from multiple possible sources
                    project_data = st.session_state.get('project_data', {})
                    project_id = project_data.get('project_id')
                    
                    # Fallback to project name if ID not available
                    if not project_id:
                        project_name = st.session_state.get('project_name')
                        if project_name:
                            # Save basic project first to get ID
                            project_id = db_manager.save_project({
                                'project_name': project_name,
                                'latitude': st.session_state.get('map_coordinates', {}).get('lat', 52.5200),
                                'longitude': st.session_state.get('map_coordinates', {}).get('lng', 13.4050),
                                'timezone': st.session_state.get('timezone', 'Europe/Berlin'),
                                'currency': 'EUR'
                            })
                            st.session_state.project_data['project_id'] = project_id
                    
                    if project_id:
                        # Convert DataFrame to dict if needed
                        if hasattr(bipv_specifications, 'to_dict'):
                            system_specs = bipv_specifications.to_dict('records')
                        else:
                            system_specs = bipv_specifications
                            
                        db_manager.save_pv_specifications(int(project_id), {
                            'base_panel_type': selected_panel_type,
                            'customized_panel_specs': final_panel_specs,
                            'modifications_made': modifications_made,
                            'system_specifications': system_specs,
                            'calculation_timestamp': datetime.now().isoformat()
                        })
                        if modifications_made:
                            st.info("Custom panel specifications saved to database")
                    else:
                        st.info("PV specifications calculated successfully (database saving skipped)")
                except Exception as e:
                    st.info(f"PV specifications calculated successfully (database error: {str(e)})")
                
                st.success(f"✅ Successfully calculated specifications for {len(bipv_specifications)} BIPV systems")
            else:
                st.error("❌ No viable BIPV systems found. Check building element data and radiation analysis.")
    
    # Display results if calculations have been performed
    pv_specifications = st.session_state.get('pv_specifications')
    if pv_specifications is not None and len(pv_specifications) > 0:
        
        st.subheader("📋 BIPV System Specifications Results")
        
        # Show what specifications were used
        if 'customized_panel_specs' in st.session_state:
            specs_used = st.session_state.get('customized_panel_specs', final_panel_specs)
            modifications_used = st.session_state.get('modifications_made', False)
            
            if modifications_used:
                st.success("Results calculated using your custom panel modifications")
            else:
                st.info(f"Results calculated using standard {selected_panel_type} specifications")
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_capacity = pv_specifications['system_power_kw'].sum()
        total_annual_energy = pv_specifications['annual_energy_kwh'].sum()
        
        # Use correct column name for total cost
        if 'total_cost' in pv_specifications.columns:
            total_investment = pv_specifications['total_cost'].sum()
        elif 'total_installation_cost' in pv_specifications.columns:
            total_investment = pv_specifications['total_installation_cost'].sum()
        else:
            total_investment = 0
            
        avg_specific_yield = pv_specifications['specific_yield'].mean()
        
        with col1:
            st.metric("Total Capacity", f"{total_capacity:.1f} kW")
        with col2:
            st.metric("Annual Energy", f"{total_annual_energy:,.0f} kWh")
        with col3:
            st.metric("Total Investment", f"€{total_investment:,.0f}")
        with col4:
            st.metric("Avg. Specific Yield", f"{avg_specific_yield:.0f} kWh/kW")
        
        # Detailed specifications table
        with st.expander("📊 Individual System Specifications", expanded=False):
            # Check available columns and select appropriate ones
            available_columns = list(pv_specifications.columns)
            display_columns = []
            
            # Build display columns based on what's available
            if 'element_id' in available_columns:
                display_columns.append('element_id')
            if 'orientation' in available_columns:
                display_columns.append('orientation')
            if 'glass_area' in available_columns:
                display_columns.append('glass_area')
            elif 'element_area' in available_columns:
                display_columns.append('element_area')
            if 'system_power_kw' in available_columns:
                display_columns.append('system_power_kw')
            if 'annual_energy_kwh' in available_columns:
                display_columns.append('annual_energy_kwh')
            if 'specific_yield' in available_columns:
                display_columns.append('specific_yield')
            if 'total_cost' in available_columns:
                display_columns.append('total_cost')
            elif 'total_installation_cost' in available_columns:
                display_columns.append('total_installation_cost')
            if 'cost_per_kwh' in available_columns:
                display_columns.append('cost_per_kwh')
            if 'transparency' in available_columns:
                display_columns.append('transparency')
            
            display_df = pv_specifications[display_columns].copy()
            
            # Format columns for better display (only format columns that exist)
            if 'system_power_kw' in display_df.columns:
                display_df['system_power_kw'] = display_df['system_power_kw'].round(3)
            if 'annual_energy_kwh' in display_df.columns:
                display_df['annual_energy_kwh'] = display_df['annual_energy_kwh'].round(0)
            if 'specific_yield' in display_df.columns:
                display_df['specific_yield'] = display_df['specific_yield'].round(0)
            if 'total_cost' in display_df.columns:
                display_df['total_cost'] = display_df['total_cost'].round(0)
            elif 'total_installation_cost' in display_df.columns:
                display_df['total_installation_cost'] = display_df['total_installation_cost'].round(0)
            if 'cost_per_kwh' in display_df.columns:
                display_df['cost_per_kwh'] = display_df['cost_per_kwh'].round(3)
            if 'transparency' in display_df.columns:
                display_df['transparency'] = (display_df['transparency'] * 100).round(0)
            
            st.dataframe(display_df, use_container_width=True, height=400)
        
        # Visualization charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Power distribution by orientation
            power_by_orientation = pv_specifications.groupby('orientation')['system_power_kw'].sum().reset_index()
            fig_power = px.bar(
                power_by_orientation, 
                x='orientation', 
                y='system_power_kw',
                title="Total Power Distribution by Orientation",
                labels={'system_power_kw': 'Total Power (kW)', 'orientation': 'Orientation'}
            )
            fig_power.update_layout(height=400)
            st.plotly_chart(fig_power, use_container_width=True)
        
        with col2:
            # Energy yield vs investment scatter
            fig_scatter = px.scatter(
                pv_specifications,
                x='total_installation_cost',
                y='annual_energy_kwh',
                color='orientation',
                size='system_power_kw',
                title="Energy Yield vs Investment Cost",
                labels={
                    'total_installation_cost': 'Total Investment (€)',
                    'annual_energy_kwh': 'Annual Energy (kWh)'
                }
            )
            fig_scatter.update_layout(height=400)
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        st.success("✅ Step 6 completed successfully. Ready to proceed to Step 7: Yield vs Demand Analysis.")