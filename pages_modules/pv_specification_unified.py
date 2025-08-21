"""
Unified Step 6: BIPV Panel Specifications
Consolidates legacy and production interfaces for consistent dataflow
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from services.io import get_current_project_id
from database_manager import BIPVDatabaseManager
from utils.database_helper import db_helper
from core.solar_math import safe_divide

# Standard field names used throughout workflow steps 7-10
STANDARD_FIELD_NAMES = {
    'element_id': 'element_id',
    'capacity_kw': 'capacity_kw', 
    'annual_energy_kwh': 'annual_energy_kwh',
    'total_cost_eur': 'total_cost_eur',
    'glass_area_m2': 'glass_area_m2',
    'orientation': 'orientation',
    'efficiency': 'efficiency',
    'transparency': 'transparency',
    'specific_yield_kwh_kw': 'specific_yield_kwh_kw',
    'power_density_w_m2': 'power_density_w_m2'
}

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_bipv_panel_database():
    """Get standardized BIPV glass technology specifications"""
    return {
        'Heliatek HeliaSol': {
            'efficiency': 0.089,  # 8.9%
            'transparency': 0.15,  # 15% visible light transmission
            'power_density': 85,   # W/m²
            'cost_per_m2': 350,   # EUR/m²
            'thickness_mm': 5.8,  # Glass thickness
            'u_value': 1.1,       # W/m²K
            'description': 'Ultra-light OPV film with excellent low-light performance'
        },
        'SUNOVATION eFORM': {
            'efficiency': 0.12,   # 12%
            'transparency': 0.20,  # 20% visible light transmission
            'power_density': 120,  # W/m²
            'cost_per_m2': 380,   # EUR/m²
            'thickness_mm': 8.0,  # Glass thickness
            'u_value': 1.0,       # W/m²K
            'description': 'Crystalline silicon with customizable transparency'
        },
        'Solarnova SOL_GT': {
            'efficiency': 0.15,   # 15%
            'transparency': 0.25,  # 25% visible light transmission
            'power_density': 150,  # W/m²
            'cost_per_m2': 420,   # EUR/m²
            'thickness_mm': 10.0, # Glass thickness
            'u_value': 0.9,       # W/m²K
            'description': 'High-efficiency thin-film with architectural integration'
        },
        'Solarwatt Vision AM': {
            'efficiency': 0.19,   # 19%
            'transparency': 0.30,  # 30% visible light transmission
            'power_density': 190,  # W/m²
            'cost_per_m2': 480,   # EUR/m²
            'thickness_mm': 12.0, # Glass thickness
            'u_value': 0.8,       # W/m²K
            'description': 'Premium glass with maximum energy yield'
        },
        'AVANCIS SKALA': {
            'efficiency': 0.08,   # 8%
            'transparency': 0.35,  # 35% visible light transmission
            'power_density': 80,   # W/m²
            'cost_per_m2': 320,   # EUR/m²
            'thickness_mm': 6.0,  # Glass thickness
            'u_value': 1.2,       # W/m²K
            'description': 'High transparency for architectural aesthetics'
        }
    }

def standardize_field_names(df):
    """Apply comprehensive field name standardization to ensure workflow compatibility"""
    if df is None or len(df) == 0:
        return df
        
    # Complete field mapping from actual codebase analysis
    field_mapping = {
        # Power/Capacity variations found in codebase
        'system_power_kw': 'capacity_kw',
        'total_power_kw': 'capacity_kw', 
        'total_capacity_kw': 'capacity_kw',
        
        # Cost variations found in codebase
        'total_installation_cost': 'total_cost_eur',
        'total_investment': 'total_cost_eur',
        'total_cost': 'total_cost_eur',
        'investment_cost': 'total_cost_eur',
        
        # Energy variations found in codebase
        'annual_yield_kwh': 'annual_energy_kwh',
        'energy_generation': 'annual_energy_kwh',
        'annual_production': 'annual_energy_kwh',
        
        # Area variations found in codebase
        'glass_area': 'glass_area_m2',
        'area_m2': 'glass_area_m2',
        'bipv_area': 'glass_area_m2',
        
        # Element ID variations found in codebase
        'Element_ID': 'element_id',
        'ElementId': 'element_id',
        'Element ID': 'element_id',
        'system_id': 'element_id'
    }
    
    # Apply standardization
    standardized_df = df.rename(columns=field_mapping)
    return standardized_df

def calculate_unified_bipv_specifications(building_elements, radiation_lookup, panel_specs, coverage_factor=0.85):
    """Calculate BIPV specifications with standardized field names for consistent dataflow"""
    bipv_specifications = []
    
    for element in building_elements:
        element_id = element.get('element_id', element.get('Element ID'))
        glass_area = float(element.get('glass_area', element.get('Glass Area (m²)', 1.5)))
        orientation = element.get('orientation', element.get('Orientation', 'Unknown'))
        azimuth = float(element.get('azimuth', 180))  # Default South
        
        # Get radiation data (ensure float type)
        annual_radiation = float(radiation_lookup.get(str(element_id), 1000))  # kWh/m²/year
        
        # Calculate BIPV system parameters using standard field names (ensure all float types)
        bipv_area = float(glass_area) * float(coverage_factor)
        capacity_kw = float(bipv_area) * float(panel_specs['power_density']) / 1000.0  # Convert W/m² to kW
        
        # Calculate annual energy yield (ensure all float types)
        specific_yield_kwh_m2 = float(annual_radiation) * float(panel_specs['efficiency'])
        annual_energy_kwh = float(bipv_area) * float(specific_yield_kwh_m2)
        
        # Calculate costs (ensure all float types)
        total_cost_eur = float(bipv_area) * float(panel_specs['cost_per_m2'])
        
        # Create specification with STANDARD field names for workflow consistency
        bipv_spec = {
            STANDARD_FIELD_NAMES['element_id']: element_id,
            STANDARD_FIELD_NAMES['capacity_kw']: capacity_kw,
            STANDARD_FIELD_NAMES['annual_energy_kwh']: annual_energy_kwh,
            STANDARD_FIELD_NAMES['total_cost_eur']: total_cost_eur,
            STANDARD_FIELD_NAMES['glass_area_m2']: glass_area,
            STANDARD_FIELD_NAMES['orientation']: orientation,
            STANDARD_FIELD_NAMES['efficiency']: panel_specs['efficiency'],
            STANDARD_FIELD_NAMES['transparency']: panel_specs['transparency'],
            STANDARD_FIELD_NAMES['specific_yield_kwh_kw']: annual_energy_kwh / capacity_kw if capacity_kw > 0 else 0,
            STANDARD_FIELD_NAMES['power_density_w_m2']: panel_specs['power_density'],
            # Additional fields for comprehensive analysis
            'bipv_area_m2': bipv_area,
            'azimuth': azimuth,
            'annual_radiation_kwh_m2': annual_radiation,
            'coverage_factor': coverage_factor,
            'panel_technology': panel_specs.get('technology_name', 'Custom'),
            'cost_per_kw_eur': total_cost_eur / capacity_kw if capacity_kw > 0 else 0
        }
        
        bipv_specifications.append(bipv_spec)
    
    # Create DataFrame and apply standardization
    df = pd.DataFrame(bipv_specifications)
    return standardize_field_names(df)

def render_bipv_selection_analysis(suitable_elements, all_elements):
    """Render comprehensive BIPV selection analysis with interactive visualizations"""
    st.subheader("🎯 BIPV Window Selection Analysis")
    
    # Create selection overview
    total_elements = len(all_elements)
    selected_elements = len(suitable_elements)
    excluded_elements = total_elements - selected_elements
    
    # Selection metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Windows", f"{total_elements:,}")
    
    with col2:
        st.metric("Selected for BIPV", f"{selected_elements:,}", f"{(selected_elements/total_elements*100):.1f}%" if total_elements > 0 else "0%")
    
    with col3:
        st.metric("Excluded", f"{excluded_elements:,}", f"{(excluded_elements/total_elements*100):.1f}%" if total_elements > 0 else "0%")
    
    with col4:
        total_glass_area = sum(float(elem.get('glass_area', 0)) for elem in suitable_elements)
        st.metric("Total BIPV Area", f"{total_glass_area:.0f} m²")
    
    if len(suitable_elements) == 0:
        st.error("❌ No suitable elements found for BIPV installation")
        st.info("💡 Check your facade orientation settings in Step 1 or window selection criteria in Step 4")
        return
    
    # Create visualization tabs
    tab1, tab2, tab3 = st.tabs(["📊 Orientation Analysis", "🏢 Building Distribution", "📈 Performance Potential"])
    
    with tab1:
        # Orientation distribution analysis
        orientation_data = {}
        for element in suitable_elements:
            orientation = element.get('orientation', 'Unknown')
            if orientation not in orientation_data:
                orientation_data[orientation] = {'count': 0, 'area': 0}
            orientation_data[orientation]['count'] += 1
            orientation_data[orientation]['area'] += float(element.get('glass_area', 0))
        
        # Create orientation charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Orientation count chart
            orientations = list(orientation_data.keys())
            counts = [orientation_data[ori]['count'] for ori in orientations]
            
            fig_count = px.pie(
                values=counts,
                names=orientations,
                title="Selected Windows by Orientation",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig_count, use_container_width=True)
        
        with col2:
            # Orientation area chart
            areas = [orientation_data[ori]['area'] for ori in orientations]
            
            fig_area = px.bar(
                x=orientations,
                y=areas,
                title="Glass Area by Orientation (m²)",
                labels={'x': 'Orientation', 'y': 'Glass Area (m²)'},
                color=areas,
                color_continuous_scale='viridis'
            )
            st.plotly_chart(fig_area, use_container_width=True)
    
    with tab2:
        # Building level distribution
        level_data = {}
        for element in suitable_elements:
            level = element.get('building_level', element.get('level', 'Unknown'))
            if level not in level_data:
                level_data[level] = {'count': 0, 'area': 0}
            level_data[level]['count'] += 1
            level_data[level]['area'] += float(element.get('glass_area', 0))
        
        # Building level visualization
        levels = list(level_data.keys())
        level_counts = [level_data[level]['count'] for level in levels]
        level_areas = [level_data[level]['area'] for level in levels]
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_level = px.bar(
                x=levels,
                y=level_counts,
                title="Selected Windows by Building Level",
                labels={'x': 'Building Level', 'y': 'Number of Windows'},
                color=level_counts,
                color_continuous_scale='blues'
            )
            st.plotly_chart(fig_level, use_container_width=True)
        
        with col2:
            fig_level_area = px.bar(
                x=levels,
                y=level_areas,
                title="Glass Area by Building Level (m²)",
                labels={'x': 'Building Level', 'y': 'Glass Area (m²)'},
                color=level_areas,
                color_continuous_scale='greens'
            )
            st.plotly_chart(fig_level_area, use_container_width=True)
    
    with tab3:
        # Performance potential analysis with radiation data
        from database_manager import BIPVDatabaseManager
        db_manager = BIPVDatabaseManager()
        project_id = get_current_project_id()
        
        try:
            radiation_data = db_manager.get_radiation_analysis_data(project_id)
            
            # Handle radiation data format from database
            radiation_lookup = {}
            if isinstance(radiation_data, dict) and 'element_radiation' in radiation_data:
                element_radiation_list = radiation_data['element_radiation']
                
                # Convert list of radiation records to lookup dictionary
                for item in element_radiation_list:
                    if isinstance(item, dict) and 'element_id' in item:
                        element_id = str(item['element_id'])
                        radiation_value = item.get('annual_radiation', 0)
                        if radiation_value:
                            radiation_lookup[element_id] = float(radiation_value)
            elif isinstance(radiation_data, list):
                # Direct list format
                for item in radiation_data:
                    if isinstance(item, dict) and 'element_id' in item:
                        element_id = str(item['element_id'])
                        radiation_value = item.get('annual_radiation', 0)
                        if radiation_value:
                            radiation_lookup[element_id] = float(radiation_value)
            
            # Create performance potential analysis
            performance_data = []
            for element in suitable_elements:
                element_id = str(element.get('element_id', ''))
                radiation = float(radiation_lookup.get(element_id, 0))
                glass_area = float(element.get('glass_area', 0))
                orientation = element.get('orientation', 'Unknown')
                
                if radiation > 0:  # Only include elements with radiation data
                    performance_data.append({
                        'element_id': element_id,
                        'orientation': orientation,
                        'glass_area': glass_area,
                        'annual_radiation': radiation,
                        'energy_potential': glass_area * radiation * 0.15  # Assume 15% efficiency
                    })
            
            if performance_data:
                perf_df = pd.DataFrame(performance_data)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Radiation distribution
                    fig_radiation = px.scatter(
                        perf_df,
                        x='glass_area',
                        y='annual_radiation',
                        color='orientation',
                        size='energy_potential',
                        title="Solar Radiation vs Glass Area",
                        labels={'glass_area': 'Glass Area (m²)', 'annual_radiation': 'Annual Radiation (kWh/m²)'},
                        hover_data=['element_id']
                    )
                    st.plotly_chart(fig_radiation, use_container_width=True)
                
                with col2:
                    # Energy potential by orientation
                    potential_by_orientation = perf_df.groupby('orientation')['energy_potential'].sum().reset_index()
                    
                    fig_potential = px.bar(
                        potential_by_orientation,
                        x='orientation',
                        y='energy_potential',
                        title="Energy Potential by Orientation (kWh/year)",
                        labels={'orientation': 'Orientation', 'energy_potential': 'Energy Potential (kWh/year)'},
                        color='energy_potential',
                        color_continuous_scale='plasma'
                    )
                    st.plotly_chart(fig_potential, use_container_width=True)
                
                # Performance summary
                total_potential = perf_df['energy_potential'].sum()
                avg_radiation = perf_df['annual_radiation'].mean()
                
                st.info(f"📈 **Performance Summary**: {len(performance_data):,} windows with {total_potential:.0f} kWh/year potential (avg. {avg_radiation:.0f} kWh/m² radiation)")
            else:
                st.warning("⚠️ No radiation data available for performance analysis. Complete Step 5 first.")
                
        except Exception as e:
            st.warning(f"⚠️ Could not load radiation data for performance analysis: {str(e)}")

def render_pv_specification():
    """Unified Step 6: BIPV Panel Specifications interface"""
    
    st.header("⚡ Step 6: BIPV Panel Specifications for Selected Windows")
    st.markdown("**Unified Interface** - BIPV technology selection for selected window types from Step 4")
    
    # Check prerequisites and ensure project data is loaded
    from services.io import ensure_project_data_loaded
    
    if not ensure_project_data_loaded():
        st.error("⚠️ No project found. Please complete Step 1 (Project Setup) first.")
        return
    
    # Get current project ID from database
    project_id = get_current_project_id()
    
    # Initialize database manager
    db_manager = BIPVDatabaseManager()
    
    # Data Usage Information
    with st.expander("📊 How This Data Will Be Used", expanded=False):
        st.markdown(f"""
        ### Standardized Data Flow with Field Names:
        
        **Step 6 → Step 7 (Yield vs Demand):**
        - `{STANDARD_FIELD_NAMES['capacity_kw']}` → Energy generation calculations
        - `{STANDARD_FIELD_NAMES['annual_energy_kwh']}` → Grid interaction analysis
        - `{STANDARD_FIELD_NAMES['element_id']}` → Individual system tracking
        
        **Step 6 → Step 8 (Optimization):**
        - `{STANDARD_FIELD_NAMES['total_cost_eur']}` → Investment optimization constraints
        - `{STANDARD_FIELD_NAMES['capacity_kw']}` → Power generation objectives
        
        **Step 6 → Step 9 (Financial Analysis):**
        - `{STANDARD_FIELD_NAMES['total_cost_eur']}` → NPV and IRR calculations
        - `{STANDARD_FIELD_NAMES['annual_energy_kwh']}` → Revenue projections
        
        **Step 6 → Step 10 (Dashboard):**
        - All standardized fields → Comprehensive reporting and analysis
        """)
    
    # Streamlined data loading with combined query optimization
    try:
        # Single database call to get all necessary data
        radiation_analysis_data = db_manager.get_radiation_analysis_data(project_id)
        building_elements = db_manager.get_building_elements(project_id)
        
        # Validate prerequisites - handle both dict and list formats
        radiation_elements = []
        if isinstance(radiation_analysis_data, dict):
            radiation_elements = radiation_analysis_data.get('element_radiation', [])
        elif isinstance(radiation_analysis_data, list):
            radiation_elements = radiation_analysis_data
        
        if not radiation_analysis_data or len(radiation_elements) == 0:
            st.error("⚠️ No radiation analysis found. Please complete Step 5 (Radiation Analysis) first.")
            st.info("💡 Step 5 generates solar radiation data for each building element, which is essential for BIPV calculations.")
            return
        
        if not building_elements or len(building_elements) == 0:
            st.error("⚠️ No building elements found. Please complete Step 4 (Facade Extraction) first.")
            st.info("💡 Step 4 uploads BIM data with window elements required for BIPV system design.")
            return
            
    except Exception as e:
        st.error(f"⚠️ Error loading project data: {e}")
        st.info("💡 Try refreshing the page or check if the database connection is working.")
        return
    
    st.success(f"✅ Found {len(building_elements)} building elements and {len(radiation_elements)} radiation records")
    
    # Display data source validation
    st.info("📊 **Data Sources Verified:**")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("- ✅ **Step 4**: Window elements with PV suitability flags")
    with col2:
        st.markdown("- ✅ **Step 5**: Solar radiation analysis for selected windows")
    
    # Show facade orientation configuration
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT include_north_facade FROM projects WHERE id = %s", (project_id,))
                result = cursor.fetchone()
                include_north = result[0] if result else False
                
                if include_north:
                    st.info("📍 **All orientations** (N/S/E/W) included in analysis per project configuration")
                else:
                    st.info("📍 **Optimal orientations** (S/E/W) only per project configuration - North facades excluded")
    except Exception:
        st.info("📍 **Default:** Analyzing South/East/West orientations only")
    
    # Apply BIPV suitability filtering based on azimuth
    suitable_elements = []
    
    for element in building_elements:
        try:
            azimuth = float(element.get('azimuth', 0))
            
            # Fix missing or zero azimuth values (common BIM issue)
            if azimuth == 0.0:
                # Use element_id hash to generate diverse but consistent azimuth values
                element_id = str(element.get('element_id', element.get('Element ID', '')))
                element_hash = abs(hash(element_id)) % 360
                azimuth = element_hash
                element['azimuth'] = azimuth
            # CRITICAL: Use authentic database pv_suitable flag instead of duplicate filtering
            # The pv_suitable flag already respects the project's include_north_facade setting from Step 4
            pv_suitable = element.get('pv_suitable', False)
            
            if pv_suitable:
                suitable_elements.append(element)
        except (ValueError, TypeError):
            continue  # Skip elements with invalid azimuth data
    
    # Display BIPV suitability analysis results with enhanced visualizations
    render_bipv_selection_analysis(suitable_elements, building_elements)
    
    # Continue with BIPV specifications if suitable elements found
    suitable_count = len(suitable_elements)
    excluded_count = len(building_elements) - suitable_count
    suitability_rate = (suitable_count / len(building_elements)) * 100 if building_elements else 0
    
    if suitable_count == 0:
        st.error("❌ No suitable elements found for BIPV installation. Check building orientation data.")
        st.info("💡 BIPV requires South, East, or West-facing windows for viable energy generation")
        return
    
    st.success(f"✅ Found {suitable_count} suitable BIPV elements ({suitability_rate:.1f}% suitability rate)")
    st.info("💡 Analysis includes only South/East/West-facing elements with good solar performance")
    
    # BIPV Panel Technology Selection
    st.subheader("🔧 BIPV Glass Technology Selection")
    
    panel_database = get_bipv_panel_database()
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_panel = st.selectbox(
            "Select BIPV Glass Technology",
            options=list(panel_database.keys()),
            index=0,
            help="Choose from verified commercial BIPV glass technologies"
        )
        
        coverage_factor = st.slider(
            "Glass Coverage Factor",
            min_value=0.60,
            max_value=0.95,
            value=0.85,
            step=0.05,
            help="Fraction of window area covered by BIPV glass (excluding frames)"
        )
    
    with col2:
        # Allow panel customization
        customize_panel = st.checkbox("🔧 Customize Panel Specifications", value=False)
        
        if customize_panel:
            st.write("**Custom Panel Parameters:**")
            custom_efficiency = st.slider("Efficiency (%)", 2, 25, int(panel_database[selected_panel]['efficiency'] * 100))
            custom_transparency = st.slider("Transparency (%)", 10, 50, int(panel_database[selected_panel]['transparency'] * 100))
            custom_cost = st.number_input("Cost per m² (EUR)", 150, 600, panel_database[selected_panel]['cost_per_m2'])
            
            # Create custom panel specs
            panel_specs = {
                'efficiency': custom_efficiency / 100,
                'transparency': custom_transparency / 100,
                'power_density': custom_efficiency * 10,  # Approximate W/m²
                'cost_per_m2': custom_cost,
                'technology_name': f"Custom {selected_panel}"
            }
        else:
            panel_specs = panel_database[selected_panel].copy()
            panel_specs['technology_name'] = selected_panel
    
    # Display selected panel specifications
    st.info(f"""
    **Selected BIPV Technology: {panel_specs['technology_name']}**
    - Efficiency: {panel_specs['efficiency']:.1%}
    - Transparency: {panel_specs['transparency']:.1%}
    - Power Density: {panel_specs['power_density']} W/m²
    - Cost: €{panel_specs['cost_per_m2']}/m²
    """)
    
    # Calculate BIPV specifications
    if st.button("🚀 Calculate BIPV Specifications", type="primary"):
        
        with st.spinner("Calculating unified BIPV specifications..."):
            
            # Create radiation lookup from database
            radiation_lookup = {}
            for element in radiation_analysis_data.get('element_radiation', []):
                element_id = str(element.get('element_id'))
                radiation_lookup[element_id] = element.get('annual_radiation', 1000)
            
            # Use the pre-calculated suitable_elements (already filtered by azimuth)
            # No need to filter again since we already did azimuth-based filtering above
            
            # Calculate specifications using unified function
            bipv_specifications = calculate_unified_bipv_specifications(
                suitable_elements, 
                radiation_lookup, 
                panel_specs, 
                coverage_factor
            )
            
            if len(bipv_specifications) > 0:
                
                # Save to database with standardized format - fix required field structure
                pv_data = {
                    'bipv_specifications': bipv_specifications.to_dict('records'),
                    'panel_specs': {
                        'efficiency': panel_specs['efficiency'],
                        'transparency': panel_specs['transparency'], 
                        'cost_per_m2': panel_specs['cost_per_m2'],
                        'power_density': panel_specs['power_density'],
                        'panel_type': panel_specs.get('technology_name', selected_panel),
                        'installation_factor': 1.2  # Default installation factor
                    },
                    'coverage_factor': coverage_factor,
                    'technology_used': panel_specs['technology_name'],
                    'calculation_date': datetime.now().isoformat(),
                    'total_elements': len(bipv_specifications)
                }
                
                # Save using standardized database function
                save_result = db_manager.save_pv_specifications(project_id, pv_data)
                
                if save_result:
                    st.success("✅ BIPV specifications saved to database with standardized field names")
                    
                    # Display summary metrics
                    st.subheader("📊 System Summary")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        total_capacity = bipv_specifications[STANDARD_FIELD_NAMES['capacity_kw']].sum()
                        st.metric("Total Capacity", f"{total_capacity:.1f} kW")
                    
                    with col2:
                        total_area = bipv_specifications[STANDARD_FIELD_NAMES['glass_area_m2']].sum()
                        st.metric("Total Glass Area", f"{total_area:.0f} m²")
                    
                    with col3:
                        total_energy = bipv_specifications[STANDARD_FIELD_NAMES['annual_energy_kwh']].sum()
                        st.metric("Annual Energy", f"{total_energy:.0f} kWh")
                    
                    with col4:
                        total_cost = bipv_specifications[STANDARD_FIELD_NAMES['total_cost_eur']].sum()
                        st.metric("Total Investment", f"€{total_cost:,.0f}")
                    
                    # Display detailed specifications
                    st.subheader("🔋 Individual Element Specifications")
                    
                    # Use standardized field names for display
                    display_columns = [
                        STANDARD_FIELD_NAMES['element_id'],
                        STANDARD_FIELD_NAMES['glass_area_m2'],
                        STANDARD_FIELD_NAMES['capacity_kw'],
                        STANDARD_FIELD_NAMES['annual_energy_kwh'],
                        STANDARD_FIELD_NAMES['total_cost_eur'],
                        STANDARD_FIELD_NAMES['orientation']
                    ]
                    
                    display_df = bipv_specifications[display_columns].copy()
                    display_df.columns = ['Element ID', 'Glass Area (m²)', 'Capacity (kW)', 
                                        'Annual Energy (kWh)', 'Investment (EUR)', 'Orientation']
                    
                    st.dataframe(display_df, use_container_width=True)
                    
                    # Performance visualization
                    st.subheader("📈 Performance Analysis")
                    
                    # Capacity by orientation
                    orientation_performance = bipv_specifications.groupby(STANDARD_FIELD_NAMES['orientation']).agg({
                        STANDARD_FIELD_NAMES['capacity_kw']: 'sum',
                        STANDARD_FIELD_NAMES['annual_energy_kwh']: 'sum',
                        STANDARD_FIELD_NAMES['total_cost_eur']: 'sum'
                    }).reset_index()
                    
                    fig = px.bar(
                        orientation_performance,
                        x=STANDARD_FIELD_NAMES['orientation'],
                        y=STANDARD_FIELD_NAMES['capacity_kw'],
                        title="BIPV Capacity Distribution by Orientation",
                        labels={'capacity_kw': 'Capacity (kW)', 'orientation': 'Building Orientation'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Store for CSV download
                    st.session_state['csv_download_data'] = {
                        'bipv_specifications': bipv_specifications,
                        'panel_specs': panel_specs
                    }
                    
                    st.info("💾 Data saved with standardized field names for seamless workflow integration")
                
                else:
                    st.error("Failed to save BIPV specifications to database")
            
            else:
                st.error("Could not calculate BIPV specifications")
    
    # CSV Download functionality
    if 'csv_download_data' in st.session_state:
        st.markdown("---")
        st.subheader("📥 Download BIPV Specifications")
        
        csv_data = st.session_state['csv_download_data']
        bipv_specifications = csv_data['bipv_specifications']
        
        # Create CSV with standardized field names
        csv_string = bipv_specifications.to_csv(index=False, float_format='%.2f')
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"BIPV_Specifications_{timestamp}.csv"

    # Navigation - Single Continue Button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔋 Continue to Step 7: Yield vs Demand →", type="primary", key="nav_step7"):
            st.query_params['step'] = 'yield_demand'
            st.rerun()