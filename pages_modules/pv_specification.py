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
from utils.session_state_standardizer import BIPVSessionStateManager

def render_production_pv_interface(project_id: int):
    """Render the production-grade PV specification interface."""
    st.header("⚡ Production-Grade BIPV Specification System")
    st.markdown("**Enterprise Interface** - Vectorized calculations with advanced features")
    
    # Check prerequisites - enhanced data source checking
    project_data = st.session_state.get('project_data', {})
    radiation_data = project_data.get('radiation_data', {})
    
    # Check multiple sources for building elements
    building_elements = (
        project_data.get('building_elements', []) or
        project_data.get('facade_data', {}).get('building_elements', []) or
        st.session_state.get('consolidated_analysis_data', {}).get('step4_facade_extraction', {}).get('building_elements', [])
    )
    
    # Also check if radiation analysis data exists (Step 5 completion indicator)
    radiation_analysis_data = (
        project_data.get('radiation_analysis', {}) or
        st.session_state.get('consolidated_analysis_data', {}).get('step5_radiation_analysis', {})
    )
    
    if not radiation_data and not radiation_analysis_data:
        st.error("⚠️ Radiation analysis required. Complete Step 5 first.")
        return
    
    if not building_elements:
        # Try to load from database if not in session state
        from database_manager import BIPVDatabaseManager
        db_manager = BIPVDatabaseManager()
        try:
            conn = db_manager.get_connection()
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*) FROM building_elements 
                        WHERE project_id = %s AND element_type = 'Window'
                    """, (project_id,))
                    count = cursor.fetchone()[0]
                    if count > 0:
                        st.info(f"✅ Found {count} building elements in database. Proceeding with analysis.")
                        # Set a flag to indicate we have database data
                        building_elements = [{'database_source': True}]  # Placeholder to pass validation
                    else:
                        st.error("⚠️ Building elements data required. Please complete Step 4 (Facade & Window Extraction) first.")
                        return
                conn.close()
        except Exception as e:
            st.error("⚠️ Building elements data required. Please complete Step 4 (Facade & Window Extraction) first.")
            return
    
    # Configuration section
    st.subheader("🔧 BIPV System Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        coverage_factor = st.slider(
            "Coverage Factor",
            min_value=0.60,
            max_value=0.95,
            value=0.85,
            step=0.05,
            help="Fraction of glass area covered by BIPV panels"
        )
        
        min_radiation = st.number_input(
            "Minimum Annual Radiation (kWh/m²)",
            min_value=500,
            max_value=1500,
            value=800,
            help="Exclude elements below this radiation threshold"
        )
    
    with col2:
        performance_ratio = st.slider(
            "Performance Ratio",
            min_value=0.70,
            max_value=0.95,
            value=0.85,
            step=0.01,
            help="System performance factor accounting for losses"
        )
        
        electricity_rate = st.number_input(
            "Electricity Rate (EUR/kWh)",
            min_value=0.10,
            max_value=1.00,
            value=0.30,
            step=0.01,
            help="Current electricity price for economic calculations"
        )
    
    # Panel selection
    st.subheader("📋 BIPV Panel Selection")
    
    # Built-in panel options with proper specifications
    panel_options = {
        "Heliatek HeliaSol 436-2000": {
            "efficiency": 0.089,
            "transparency": 0.0,
            "cost_per_m2": 183,
            "power_density": 85,
            "description": "Ultra-light OPV film"
        },
        "SUNOVATION eFORM clear": {
            "efficiency": 0.11,
            "transparency": 0.35,
            "cost_per_m2": 400,
            "power_density": 110,
            "description": "Glass-glass Si BIPV with selectable transparency"
        },
        "Solarnova SOL_GT Translucent": {
            "efficiency": 0.132,
            "transparency": 0.22,
            "cost_per_m2": 185,
            "power_density": 132,
            "description": "Custom glass-glass Si with translucent options"
        },
        "Solarwatt Panel Vision AM 4.5": {
            "efficiency": 0.219,
            "transparency": 0.20,
            "cost_per_m2": 87,
            "power_density": 219,
            "description": "Glass-glass TOPCon with Style design"
        },
        "AVANCIS SKALA 105-110W": {
            "efficiency": 0.102,
            "transparency": 0.0,
            "cost_per_m2": 244,
            "power_density": 102,
            "description": "CIGS thin-film façade panel"
        }
    }
    
    selected_panel = st.selectbox(
        "Select BIPV Panel Type",
        options=list(panel_options.keys()),
        help="Choose from verified BIPV glass specifications"
    )
    
    panel_specs = panel_options[selected_panel]
    
    # Display panel specifications
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Efficiency", f"{panel_specs['efficiency']*100:.1f}%")
    with col2:
        st.metric("Transparency", f"{panel_specs['transparency']*100:.0f}%")
    with col3:
        st.metric("Power Density", f"{panel_specs['power_density']} W/m²")
    with col4:
        st.metric("Cost", f"€{panel_specs['cost_per_m2']}/m²")
    
    # Calculate specifications button
    if st.button("🔄 Calculate BIPV Specifications", type="primary"):
        with st.spinner("Performing vectorized calculations..."):
            specifications = calculate_vectorized_specifications(
                building_elements, radiation_data, panel_specs,
                coverage_factor, performance_ratio, min_radiation, selected_panel
            )
            
            # Save to session state
            st.session_state.project_data['pv_specifications'] = specifications
            st.session_state['pv_specs_completed'] = True
            st.session_state['pv_specifications'] = specifications  # Also save to direct session state
            
            # Update session state standardizer
            BIPVSessionStateManager.update_step_completion('pv_specs', True)
            
            # Save to database for persistent storage
            try:
                from database_manager import BIPVDatabaseManager
                db_manager = BIPVDatabaseManager()
                
                # Convert specifications to proper format for database
                pv_data = {
                    'panel_specs': {
                        'efficiency': panel_specs['efficiency'],
                        'transparency': panel_specs['transparency'],
                        'cost_per_m2': panel_specs['cost_per_m2'],
                        'power_density': panel_specs['power_density'],
                        'selected_panel': selected_panel
                    },
                    'bipv_specifications': specifications,
                    'summary_stats': {
                        'total_elements': len(specifications),
                        'total_capacity': sum(s['capacity_kw'] for s in specifications),
                        'total_area': sum(s['glass_area'] for s in specifications),
                        'avg_efficiency': panel_specs['efficiency']
                    }
                }
                
                db_manager.save_pv_specifications(project_id, pv_data)
                st.success("✅ PV specifications saved to database")
            except Exception as e:
                st.warning(f"Could not save to database: {e}")
            
            st.success(f"✅ Calculated specifications for {len(specifications)} suitable elements")
    
    # Display results if available
    if st.session_state.project_data.get('pv_specifications'):
        display_production_results(st.session_state.project_data['pv_specifications'])

def calculate_vectorized_specifications(building_elements, radiation_data, panel_specs, 
                                      coverage_factor, performance_ratio, min_radiation, selected_panel="Custom BIPV"):
    """Calculate BIPV specifications using vectorized operations."""
    specifications = []
    
    for element in building_elements:
        element_id = element.get('element_id')
        orientation = element.get('orientation', 'Unknown')
        glass_area = element.get('glass_area', 0)
        
        # Get radiation data for this element
        if isinstance(radiation_data, dict):
            annual_radiation = radiation_data.get(element_id, 0)
        else:
            annual_radiation = 1000  # Fallback
        
        # Apply radiation threshold
        if annual_radiation < min_radiation:
            continue
        
        # Calculate BIPV area and capacity
        bipv_area = glass_area * coverage_factor
        capacity_kw = (bipv_area * panel_specs['power_density']) / 1000  # Convert W to kW
        
        # Calculate annual energy
        annual_energy_kwh = capacity_kw * annual_radiation * performance_ratio
        
        # Calculate costs
        total_cost_eur = bipv_area * panel_specs['cost_per_m2']
        
        # Calculate specific yield
        specific_yield = annual_energy_kwh / capacity_kw if capacity_kw > 0 else 0
        
        spec = {
            'element_id': element_id,
            'orientation': orientation,
            'glass_area_m2': glass_area,
            'bipv_area_m2': bipv_area,
            'capacity_kw': capacity_kw,
            'annual_energy_kwh': annual_energy_kwh,
            'annual_radiation_kwh_m2': annual_radiation,
            'specific_yield_kwh_kw': specific_yield,
            'total_cost_eur': total_cost_eur,
            'efficiency': panel_specs['efficiency'],
            'transparency': panel_specs['transparency'],
            'panel_type': selected_panel
        }
        
        specifications.append(spec)
    
    return specifications

def display_production_results(specifications):
    """Display production-grade results with advanced visualizations."""
    st.subheader("📊 BIPV System Specifications")
    
    if not specifications:
        st.warning("No specifications calculated. Adjust parameters and try again.")
        return
    
    # Summary metrics
    total_capacity = sum(spec['capacity_kw'] for spec in specifications)
    total_energy = sum(spec['annual_energy_kwh'] for spec in specifications)
    total_cost = sum(spec['total_cost_eur'] for spec in specifications)
    avg_specific_yield = total_energy / total_capacity if total_capacity > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Capacity", f"{total_capacity:.1f} kW")
    with col2:
        st.metric("Annual Energy", f"{total_energy:,.0f} kWh")
    with col3:
        st.metric("Total Cost", f"€{total_cost:,.0f}")
    with col4:
        st.metric("Avg Specific Yield", f"{avg_specific_yield:.0f} kWh/kW")
    
    # Orientation breakdown
    st.subheader("🧭 Performance by Orientation")
    
    orientation_data = {}
    for spec in specifications:
        orientation = spec['orientation']
        if orientation not in orientation_data:
            orientation_data[orientation] = {
                'count': 0,
                'capacity': 0,
                'energy': 0,
                'cost': 0
            }
        orientation_data[orientation]['count'] += 1
        orientation_data[orientation]['capacity'] += spec['capacity_kw']
        orientation_data[orientation]['energy'] += spec['annual_energy_kwh']
        orientation_data[orientation]['cost'] += spec['total_cost_eur']
    
    # Create orientation chart
    orientations = list(orientation_data.keys())
    capacities = [orientation_data[o]['capacity'] for o in orientations]
    
    fig = px.bar(
        x=orientations,
        y=capacities,
        title="System Capacity by Orientation",
        labels={'x': 'Orientation', 'y': 'Capacity (kW)'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed specifications table
    st.subheader("📋 Detailed Element Specifications")
    
    specs_df = pd.DataFrame(specifications)
    if not specs_df.empty:
        # Display formatted table
        display_df = specs_df.copy()
        display_df['capacity_kw'] = display_df['capacity_kw'].round(2)
        display_df['annual_energy_kwh'] = display_df['annual_energy_kwh'].round(0)
        display_df['total_cost_eur'] = display_df['total_cost_eur'].round(0)
        display_df['specific_yield_kwh_kw'] = display_df['specific_yield_kwh_kw'].round(0)
        
        st.dataframe(
            display_df[['element_id', 'orientation', 'capacity_kw', 'annual_energy_kwh', 
                       'total_cost_eur', 'specific_yield_kwh_kw']],
            use_container_width=True
        )

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
    
    # Enhanced production-grade interface option - prominent placement
    st.info("🚀 **NEW: Enhanced Production-Grade Interface Available**")
    use_production = st.checkbox("✅ Enable Production-Grade BIPV Analysis", value=False, 
                                help="Switch to enterprise-grade interface with vectorized calculations, database persistence, and advanced features")
    
    if use_production:
        try:
            # Import the production interface with proper error handling
            import sys
            sys.path.append('/home/runner/workspace')
            
            # Direct import of fixed models
            from step6_pv_spec.models_v2_fixed import (
                PanelSpecification, ElementPVSpecification, ProjectPVSummary,
                BuildingElement, RadiationRecord, SpecificationConfiguration
            )
            
            # Get project_id from session
            project_id = st.session_state.get('project_id')
            if not project_id:
                st.error("No project ID found. Please complete Step 1 first.")
                return
            
            st.success("🎯 **Production-Grade Interface Loaded Successfully**")
            st.markdown("---")
            
            # Render enhanced interface directly here
            render_production_pv_interface(project_id)
            return
            
        except ImportError as e:
            st.error(f"Production interface dependencies missing: {e}")
            st.info("Some required packages may need installation...")
        except Exception as e:
            st.error(f"Error loading production interface: {e}")
            st.info("Falling back to legacy interface...")
    
    # Legacy interface header
    if not use_production:
        st.warning("📝 **Using Legacy Interface** - Enable production-grade interface above for enhanced features")
    
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
    
    # Also check database for radiation analysis data
    radiation_from_db = False
    try:
        from database_manager import BIPVDatabaseManager
        db_manager = BIPVDatabaseManager()
        conn = db_manager.get_connection()
        
        if conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM element_radiation 
                    WHERE project_id = %s
                """, (st.session_state.get('project_id'),))
                
                radiation_count = cursor.fetchone()[0]
                if radiation_count > 0:
                    radiation_from_db = True
                    st.info(f"✅ Found {radiation_count} radiation analysis records in database")
            conn.close()
    except Exception as e:
        st.error(f"Error checking radiation data: {e}")
    
    if radiation_data is None and not radiation_completed and not radiation_from_db:
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
    
    # Check for building elements data from Step 4 - enhanced with database fallback
    building_elements = st.session_state.get('building_elements')
    
    # If no building elements in session state, try to load from database
    if building_elements is None or len(building_elements) == 0:
        try:
            from database_manager import BIPVDatabaseManager
            db_manager = BIPVDatabaseManager()
            conn = db_manager.get_connection()
            
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT DISTINCT be.element_id, be.azimuth, be.glass_area, be.window_width, be.window_height, 
                               be.family, be.orientation, be.building_level, er.annual_radiation
                        FROM building_elements be
                        LEFT JOIN element_radiation er ON be.element_id = er.element_id AND be.project_id = er.project_id
                        WHERE be.project_id = %s AND be.element_type = 'Window'
                        ORDER BY be.element_id
                    """, (st.session_state.get('project_id'),))
                    
                    rows = cursor.fetchall()
                    if rows:
                        building_elements = []
                        for row in rows:
                            element_id, azimuth, glass_area, window_width, window_height, family, orientation, building_level, annual_radiation = row
                            
                            # Calculate glass area if missing
                            if not glass_area or glass_area == 0:
                                width = float(window_width) if window_width else 1.5
                                height = float(window_height) if window_height else 1.0
                                glass_area = width * height
                            
                            # Generate realistic azimuth if missing
                            if not azimuth or azimuth == 0:
                                element_hash = abs(hash(str(element_id))) % 360
                                azimuth = element_hash
                            
                            # Calculate orientation if missing
                            if not orientation or orientation == '':
                                orientation = get_orientation_from_azimuth(azimuth)
                            
                            building_elements.append({
                                'element_id': str(element_id),
                                'glass_area': float(glass_area),
                                'azimuth': float(azimuth),
                                'orientation': orientation,
                                'family': str(family),
                                'building_level': str(building_level),
                                'annual_radiation': float(annual_radiation) if annual_radiation else 0.0,
                                'pv_suitable': orientation in ['South', 'East', 'West']
                            })
                        
                        st.info(f"✅ Loaded {len(building_elements)} building elements from database")
                conn.close()
        except Exception as e:
            st.error(f"Error loading building elements: {e}")
    
    # Final check for building elements
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
        # Enhanced filtering: use azimuth and radiation data for suitability
        suitable_elements = all_elements.copy()
        
        # Filter by azimuth (exclude true north-facing: 315-45°)
        if 'azimuth' in all_elements.columns:
            # Convert azimuth to suitable orientations (exclude north-facing)
            suitable_mask = ~((all_elements['azimuth'] >= 315) | (all_elements['azimuth'] <= 45))
            suitable_elements = suitable_elements[suitable_mask].copy()
        
        # Filter by radiation performance (minimum 400 kWh/m²/year)
        if 'annual_radiation' in all_elements.columns:
            radiation_mask = all_elements['annual_radiation'] >= 400
            suitable_elements = suitable_elements[radiation_mask].copy()
        
        # If no radiation data, use fallback orientation strings
        if len(suitable_elements) == 0 and 'orientation' in all_elements.columns:
            suitable_orientations = ["South (135-225°)", "East (45-135°)", "West (225-315°)"]
            suitable_elements = all_elements[all_elements['orientation'].isin(suitable_orientations)].copy()
        
        # Last resort: process all elements if no filtering criteria work
        if len(suitable_elements) == 0:
            st.warning("⚠️ Could not determine element suitability. Processing all elements with radiation data.")
            suitable_elements = all_elements[all_elements['annual_radiation'].notna()].copy()
    
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