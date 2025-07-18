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
        
        # Get radiation data
        annual_radiation = radiation_lookup.get(str(element_id), 1000)  # kWh/m²/year
        
        # Calculate BIPV system parameters using standard field names
        bipv_area = glass_area * coverage_factor
        capacity_kw = bipv_area * panel_specs['power_density'] / 1000  # Convert W/m² to kW
        
        # Calculate annual energy yield
        specific_yield_kwh_m2 = annual_radiation * panel_specs['efficiency']
        annual_energy_kwh = bipv_area * specific_yield_kwh_m2
        
        # Calculate costs
        total_cost_eur = bipv_area * panel_specs['cost_per_m2']
        
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

def render_pv_specification():
    """Unified Step 6: BIPV Panel Specifications interface"""
    
    st.header("⚡ Step 6: BIPV Panel Specifications")
    st.markdown("**Unified Interface** - Consistent dataflow for all workflow steps")
    
    # Get current project ID from database
    project_id = get_current_project_id()
    if not project_id:
        st.error("⚠️ No project ID found. Please complete Step 1 first.")
        return
    
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
    
    # Check prerequisites from database
    project_data = db_manager.get_project_by_id(project_id) or {}
    
    # Check for radiation analysis data
    radiation_analysis_data = db_manager.get_radiation_analysis_data(project_id)
    if not radiation_analysis_data or len(radiation_analysis_data.get('element_radiation', [])) == 0:
        st.error("⚠️ Radiation analysis required. Complete Step 5 first.")
        return
    
    # Check for building elements from database
    try:
        building_elements = db_manager.get_building_elements(project_id)
        if not building_elements or len(building_elements) == 0:
            st.error("⚠️ Building elements required. Complete Step 4 first.")
            return
    except Exception as e:
        st.error(f"⚠️ Error loading building elements: {e}")
        return
    
    st.success(f"✅ Found {len(building_elements)} building elements and {len(radiation_analysis_data.get('element_radiation', []))} radiation records")
    
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
            
            # Filter for suitable elements only (exclude North-facing)
            suitable_elements = [
                elem for elem in building_elements 
                if elem.get('pv_suitable', True) and 
                elem.get('orientation', '').lower() not in ['north', 'n']
            ]
            
            if len(suitable_elements) == 0:
                st.error("No suitable building elements found for BIPV installation")
                return
            
            # Calculate specifications using unified function
            bipv_specifications = calculate_unified_bipv_specifications(
                suitable_elements, 
                radiation_lookup, 
                panel_specs, 
                coverage_factor
            )
            
            if len(bipv_specifications) > 0:
                
                # Save to database with standardized format
                pv_data = {
                    'bipv_specifications': bipv_specifications.to_dict('records'),
                    'panel_specifications': panel_specs,
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
        
        st.download_button(
            label="📊 Download Standardized BIPV Specifications",
            data=csv_string,
            file_name=filename,
            mime="text/csv",
            help="Download BIPV specifications with standardized field names for workflow consistency"
        )