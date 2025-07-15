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
from utils.database_helper import db_helper
from datetime import datetime
from core.solar_math import safe_divide
from utils.consolidated_data_manager import ConsolidatedDataManager

def get_orientation_from_azimuth(azimuth):
    """Convert azimuth angle to cardinal orientation."""
    try:
        azimuth = float(azimuth)
        if 315 <= azimuth <= 360 or 0 <= azimuth < 45:
            return "North"
        elif 45 <= azimuth < 135:
            return "East"
        elif 135 <= azimuth < 225:
            return "South"
        elif 225 <= azimuth < 315:
            return "West"
        else:
            return "Unknown"
    except (ValueError, TypeError):
        return "Unknown"

# BIPV Glass Types with Commercial Presets
BIPV_GLASS_TYPES = {
    "Heliatek HeliaSol 436-2000": {
        "efficiency": 0.089,  # 8.9% efficiency
        "transparency": 0.0,   # 0% transparency (opaque)
        "cost_per_m2": 183,   # €183/m² calculated from €160 per 0.872 m²
        "power_density": 85,  # 85 W/m² as specified
        "description": "Ultra-light OPV film by Heliatek",
        "contact": "Treidlerstraße 3, 01139 Dresden • +49 351 2130 3430"
    },
    "SUNOVATION eFORM clear": {
        "efficiency": 0.11,   # 11% average (10-12% range)
        "transparency": 0.35,  # 35% average (10-65% selectable)
        "cost_per_m2": 400,   # €400/m² typical for eFORM
        "power_density": 110,  # W/m² calculated from efficiency
        "description": "Glass-glass Si BIPV with selectable transparency",
        "contact": "Glanzstoffstraße 21, 63820 Elsenfeld • +49 6022 26573-0"
    },
    "Solarnova SOL_GT Translucent": {
        "efficiency": 0.132,  # 13.2% module efficiency
        "transparency": 0.22,  # 22% average (11% and 33% variants)
        "cost_per_m2": 185,   # €185/m² average (120-250 range)
        "power_density": 132,  # W/m² calculated from efficiency
        "description": "Custom glass-glass Si with translucent options",
        "contact": "Am Marienhof 6, 22880 Wedel • +49 4103 91208-0"
    },
    "Solarwatt Panel Vision AM 4.5": {
        "efficiency": 0.219,  # 21.9% average (21.5-22.3% range)
        "transparency": 0.20,  # 20% via widened inter-cell gaps
        "cost_per_m2": 87,    # €87/m² calculated from €169 per 1.95 m²
        "power_density": 219,  # W/m² calculated from efficiency
        "description": "Glass-glass TOPCon with Style design",
        "contact": "Maria-Reiche-Str. 2a, 01109 Dresden • +49 351 8895-0"
    },
    "AVANCIS SKALA 105-110W": {
        "efficiency": 0.102,  # 10.2% average (10.0-10.4% range)
        "transparency": 0.0,   # 0% opaque with matt finishes
        "cost_per_m2": 244,   # €244/m² calculated from 6,294 Kč per 1.05 m²
        "power_density": 102,  # W/m² calculated from efficiency
        "description": "CIGS thin-film façade panel with color finishes",
        "contact": "Solarstraße 3, 04860 Torgau • +49 3421 7388-0"
    },
    "Custom": {
        "efficiency": 0.16,
        "transparency": 0.20,
        "cost_per_m2": 300,
        "power_density": 160,
        "description": "Custom BIPV glass specification",
        "contact": "User-defined parameters"
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
        st.info(f"🔍 Debug: Radiation data type: {type(radiation_data)}, columns: {list(radiation_data.columns) if hasattr(radiation_data, 'columns') else 'N/A'}")
        
        if isinstance(radiation_data, pd.DataFrame) and 'element_id' in radiation_data.columns:
            st.info(f"📊 Processing DataFrame with {len(radiation_data)} radiation records")
            for _, rad_row in radiation_data.iterrows():
                element_id = rad_row.get('element_id', '')
                # Try multiple field names for annual radiation (Step 5 uses 'annual_irradiation')
                annual_radiation = (
                    rad_row.get('annual_irradiation') or  # Step 5 default column name
                    rad_row.get('annual_radiation') or
                    rad_row.get('radiation') or
                    rad_row.get('annual_radiation_kwh_m2') or
                    rad_row.get('annual_energy_potential') or
                    None
                )
                if annual_radiation is not None and annual_radiation > 0:
                    radiation_lookup[element_id] = float(annual_radiation)
                    
            st.success(f"✅ Created radiation lookup for {len(radiation_lookup)} elements")
            # Show sample radiation values for debugging
            if len(radiation_lookup) > 0:
                sample_items = list(radiation_lookup.items())[:3]
                st.info(f"📈 Sample radiation values: {sample_items}")
                
        elif isinstance(radiation_data, dict) and 'element_radiation' in radiation_data:
            radiation_lookup = radiation_data['element_radiation']
        elif isinstance(radiation_data, dict):
            # Handle direct radiation data dict
            for element_id, rad_value in radiation_data.items():
                if isinstance(rad_value, (int, float)) and rad_value > 0:
                    radiation_lookup[element_id] = float(rad_value)
    else:
        st.error("❌ No radiation data available from Step 5 - authentic TMY calculations required")
    
    for idx, element in suitable_elements.iterrows():
        # Use actual Element ID from building elements - REQUIRE authentic BIM data
        element_id = element.get('Element ID') or element.get('element_id')
        if not element_id:
            st.error(f"❌ No Element ID found for building element at index {idx}. Authentic BIM data required.")
            continue  # Skip this element instead of using fallback values
        
        # Extract glass area from multiple possible column names - REQUIRE authentic BIM data
        glass_area_raw = (
            element.get('Glass Area (m²)') or
            element.get('glass_area') or
            element.get('Glass Area') or
            element.get('Area (m²)') or
            element.get('area') or
            element.get('Window Area') or
            element.get('window_area') or
            element.get('glass_area_m2')
        )
        
        # Convert to float and validate - NO fallback values allowed
        try:
            glass_area = float(glass_area_raw) if glass_area_raw is not None else None
            if glass_area is None or glass_area <= 0:
                st.error(f"❌ No valid glass area found for element {element_id}. Authentic BIM data required.")
                continue  # Skip this element instead of using fallback values
        except (ValueError, TypeError):
            st.error(f"❌ Invalid glass area data for element {element_id}. Authentic BIM data required.")
            continue  # Skip this element instead of using fallback values
        
        # Get orientation information from building elements - REQUIRE authentic BIM data
        azimuth = element.get('Azimuth') or element.get('azimuth')
        if azimuth is None:
            st.error(f"❌ No azimuth data found for element {element_id}. Authentic BIM data required.")
            continue  # Skip this element instead of using fallback values
            
        orientation = element.get('Orientation') or element.get('orientation') or get_orientation_from_azimuth(azimuth)
        
        # Get radiation data for this specific element - REQUIRE authentic TMY data
        annual_radiation = radiation_lookup.get(element_id)
        if annual_radiation is None or annual_radiation <= 0:
            # Try alternative element ID formats
            alt_element_id = str(element_id).replace('element_', '') if 'element_' in str(element_id) else f"element_{element_id}"
            annual_radiation = radiation_lookup.get(alt_element_id)
            
            if annual_radiation is None or annual_radiation <= 0:
                st.error(f"❌ No authentic TMY radiation data found for element {element_id}. Cannot proceed without real data.")
                continue  # Skip this element instead of using fallback values
        
        # Calculate BIPV specifications
        bipv_area = calculate_bipv_glass_coverage(glass_area)
        capacity_kw = bipv_area * panel_specs['power_density'] / 1000
        
        # More accurate energy calculation using radiation data
        # annual_radiation is in kWh/m²/year, efficiency and performance_ratio are decimals
        specific_yield_kwh_m2 = annual_radiation * panel_specs['efficiency'] * panel_specs['performance_ratio']
        annual_energy_kwh = bipv_area * specific_yield_kwh_m2
        
        # Sanity check for realistic values (typical BIPV: 50-200 kWh/m²/year)
        if specific_yield_kwh_m2 > 300:
            # Radiation values might be in W/m² instead of kWh/m²/year, convert
            specific_yield_kwh_m2 = (annual_radiation / 1000) * panel_specs['efficiency'] * panel_specs['performance_ratio']
            annual_energy_kwh = bipv_area * specific_yield_kwh_m2
        
        total_cost_eur = bipv_area * panel_specs['cost_per_m2']
        
        # Calculate actual power density (W/m²) for this system
        actual_power_density = panel_specs['power_density']  # W/m² from panel specs
        
        bipv_spec = {
            'element_id': element_id,
            'orientation': orientation,
            'azimuth': azimuth,
            'glass_area_m2': glass_area,
            'bipv_area_m2': bipv_area,
            'capacity_kw': capacity_kw,
            'annual_energy_kwh': annual_energy_kwh,
            'annual_radiation_kwh_m2': annual_radiation,
            'specific_yield_kwh_kw': annual_energy_kwh / capacity_kw if capacity_kw > 0 else None,
            'power_density_w_m2': actual_power_density,
            'total_cost_eur': total_cost_eur,
            'efficiency': panel_specs['efficiency'],
            'transparency': panel_specs['transparency']
        }
        
        bipv_specifications.append(bipv_spec)
    
    return pd.DataFrame(bipv_specifications)

def render_pv_specification():
    """Render the simplified PV panel specification and layout module."""
    
    # Enhanced production-grade interface option
    if st.checkbox("🚀 Use Production-Grade Interface", value=False, help="Switch to the new modular, high-performance interface"):
        try:
            from step6_pv_spec import render_pv_specification_enhanced
            # Get project_id from session or database
            project_id = st.session_state.get('project_id', 1)
            render_pv_specification_enhanced(project_id)
            return
        except ImportError:
            st.warning("Production-grade interface not available. Using legacy interface.")
        except Exception as e:
            st.error(f"Error loading production interface: {e}")
            st.info("Falling back to legacy interface.")
    
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
        all_elements = pd.DataFrame(building_elements)
    else:
        all_elements = building_elements
    
    # Filter for only suitable elements (South/East/West-facing)
    if 'pv_suitable' in all_elements.columns:
        suitable_elements = all_elements[all_elements['pv_suitable'] == True].copy()
    elif 'suitable' in all_elements.columns:
        suitable_elements = all_elements[all_elements['suitable'] == True].copy()
    else:
        # Fallback: filter by orientation if suitability flags not available
        suitable_orientations = ["South (135-225°)", "East (45-135°)", "West (225-315°)"]
        if 'orientation' in all_elements.columns:
            suitable_elements = all_elements[all_elements['orientation'].isin(suitable_orientations)].copy()
        else:
            st.warning("⚠️ Could not determine element suitability. Processing all elements.")
            suitable_elements = all_elements
    
    # Debug information with suitability confirmation
    total_elements = len(all_elements)
    suitable_count = len(suitable_elements)
    excluded_count = total_elements - suitable_count
    
    st.success(f"✅ Filtered for BIPV suitability: {suitable_count} suitable elements (excluded {excluded_count} non-suitable)")
    
    if excluded_count > 0:
        st.info(f"💡 Excluded elements are typically north-facing windows with poor solar performance")
    
    if suitable_count == 0:
        st.error("❌ No suitable elements found for BIPV installation. Check building orientation data.")
        return
    
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
    
    # Display selected panel information
    if selected_panel_type != "Custom":
        st.info(f"**{selected_panel_type}**: {base_specs['description']}")
        if 'contact' in base_specs:
            st.caption(f"📞 Contact: {base_specs['contact']}")
    
    # Simplified customization - only the most important parameters
    st.subheader("🔧 Customize Key Specifications")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        panel_efficiency = st.slider(
            "Efficiency (%)",
            min_value=2.0, max_value=25.0, 
            value=float(base_specs['efficiency']*100),
            step=0.5,
            key="panel_efficiency",
            help="BIPV glass efficiency: 8.9% (OPV), 10-13% (standard Si), 21-22% (high-performance TOPCon)"
        ) / 100
        
    with col2:
        transparency = st.slider(
            "Transparency (%)",
            min_value=0.0, max_value=65.0,
            value=float(base_specs['transparency']*100),
            step=5.0,
            key="transparency",
            help="Light transmission through BIPV glass (0% = opaque, 10-65% = semi-transparent)"
        ) / 100
        
    with col3:
        cost_per_m2 = st.number_input(
            "Cost (EUR/m²)",
            min_value=50.0, max_value=500.0,
            value=float(base_specs['cost_per_m2']),
            step=25.0,
            key="cost_per_m2",
            help="BIPV glass cost: €87 (Solarwatt), €183 (Heliatek), €400 (SUNOVATION)"
        )
    
    # Calculate derived specifications - BIPV glass power density
    # Use preset power density if available, otherwise calculate from efficiency
    if 'power_density' in base_specs and selected_panel_type != "Custom":
        power_density = float(base_specs['power_density'])  # Use preset value
    else:
        # Calculate from efficiency for custom panels
        power_density = panel_efficiency * 1000  # W/m² peak power (STC)
    
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
                    # Save using database helper
                    db_helper.save_step_data("pv_specifications", {
                        'panel_type': selected_panel['name'],
                        'efficiency': selected_panel['efficiency'],
                        'transparency': selected_panel.get('transparency', 0),
                        'cost_per_m2': selected_panel['cost_per_m2'],
                        'power_density': selected_panel['power_density'],
                        'installation_factor': selected_panel.get('installation_factor', 1.2),
                        'systems': systems
                    })
                    
                    # Legacy save method for compatibility
                    project_id = db_helper.get_project_id(project_name)
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
                
                # Store CSV data in session state for download functionality
                st.session_state['csv_download_data'] = {
                    'bipv_specifications': bipv_specifications,
                    'final_panel_specs': final_panel_specs
                }
                
                st.info("💡 **CSV download functionality is now available below the analysis.**")
                
            else:
                st.error("Could not calculate BIPV specifications. Please check your data.")
    
    # CSV Download functionality (always available when data exists)
    if 'csv_download_data' in st.session_state:
        st.markdown("---")
        st.subheader("📥 Download BIPV Specifications")
        
        # Get data from session state
        csv_data = st.session_state['csv_download_data']
        bipv_specifications = csv_data['bipv_specifications']
        final_panel_specs = csv_data['final_panel_specs']
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Prepare comprehensive CSV data
            download_df = bipv_specifications.copy()
            
            # Add calculated fields for export
            download_df['specific_yield_kwh_kw'] = download_df['annual_energy_kwh'] / download_df['capacity_kw']
            download_df['cost_per_kw_eur'] = download_df['total_cost_eur'] / download_df['capacity_kw']
            download_df['power_density_w_m2'] = (download_df['capacity_kw'] * 1000) / download_df['glass_area_m2']
            
            # Add panel specifications
            download_df['panel_efficiency_%'] = final_panel_specs['efficiency']
            download_df['panel_transparency_%'] = final_panel_specs['transparency']
            download_df['panel_cost_per_m2_eur'] = final_panel_specs['cost_per_m2']
            
            # Reorder columns for logical flow
            column_order = [
                'element_id', 'orientation', 'glass_area_m2', 'annual_radiation_kwh_m2',
                'capacity_kw', 'annual_energy_kwh', 'specific_yield_kwh_kw', 
                'power_density_w_m2', 'total_cost_eur', 'cost_per_kw_eur',
                'panel_efficiency_%', 'panel_transparency_%', 'panel_cost_per_m2_eur'
            ]
            
            # Include only available columns
            available_columns = [col for col in column_order if col in download_df.columns]
            csv_df = download_df[available_columns]
            
            # Create CSV string
            import io
            csv_buffer = io.StringIO()
            csv_df.to_csv(csv_buffer, index=False, float_format='%.2f')
            csv_string = csv_buffer.getvalue()
            
            # Generate filename with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"BIPV_Specifications_{timestamp}.csv"
            
            st.download_button(
                label="📊 Download Complete BIPV Specifications",
                data=csv_string,
                file_name=filename,
                mime="text/csv",
                help="Download comprehensive BIPV system specifications with all calculated parameters",
                key="download_complete_specs"
            )
        
        with col2:
            # Summary statistics for download
            summary_stats = {
                'Total_Elements': len(bipv_specifications),
                'Total_Capacity_kW': bipv_specifications['capacity_kw'].sum(),
                'Total_Glass_Area_m2': bipv_specifications['glass_area_m2'].sum(),
                'Total_Annual_Energy_kWh': bipv_specifications['annual_energy_kwh'].sum(),
                'Average_Specific_Yield_kWh_kW': (bipv_specifications['annual_energy_kwh'].sum() / bipv_specifications['capacity_kw'].sum()),
                'Total_Investment_EUR': bipv_specifications['total_cost_eur'].sum(),
                'Average_Power_Density_W_m2': (bipv_specifications['capacity_kw'].sum() * 1000 / bipv_specifications['glass_area_m2'].sum()),
                'Panel_Efficiency_%': final_panel_specs['efficiency'],
                'Panel_Transparency_%': final_panel_specs['transparency'],
                'Panel_Cost_per_m2_EUR': final_panel_specs['cost_per_m2']
            }
            
            # Create summary CSV
            summary_df = pd.DataFrame(list(summary_stats.items()), columns=['Parameter', 'Value'])
            
            summary_csv_buffer = io.StringIO()
            summary_df.to_csv(summary_csv_buffer, index=False, float_format='%.2f')
            summary_csv_string = summary_csv_buffer.getvalue()
            
            summary_filename = f"BIPV_Summary_{timestamp}.csv"
            
            st.download_button(
                label="📋 Download System Summary",
                data=summary_csv_string,
                file_name=summary_filename,
                mime="text/csv",
                help="Download project summary with key performance indicators and totals",
                key="download_system_summary"
            )
        
        st.info("💡 **CSV Contents:** Complete specifications include element details, performance metrics, costs, and panel specifications for further analysis or integration with other tools.")

    # Add step-specific download button
    st.markdown("---")
    st.markdown("### 📄 Step 6 Analysis Report")
    st.markdown("Download detailed PV specification and system design report:")
    
    from utils.individual_step_reports import create_step_download_button
    create_step_download_button(6, "PV Specification", "Download PV Specification Report")
    
    st.markdown("---")
    st.markdown("**Next Step:** Proceed to Step 7 (Yield vs Demand Analysis) to compare energy generation with building consumption.")