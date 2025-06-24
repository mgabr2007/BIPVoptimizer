"""
Radiation & Shading Grid Analysis page for BIPV Optimizer
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from database_manager import db_manager
from core.solar_math import safe_divide

def calculate_solar_position_simple(latitude, longitude, day_of_year, hour):
    """Calculate solar position using simplified formulas."""
    import math
    
    # Declination angle
    declination = 23.45 * math.sin(math.radians(360 * (284 + day_of_year) / 365))
    
    # Hour angle
    hour_angle = 15 * (hour - 12)
    
    # Solar elevation angle
    elevation = math.asin(
        math.sin(math.radians(declination)) * math.sin(math.radians(latitude)) +
        math.cos(math.radians(declination)) * math.cos(math.radians(latitude)) * 
        math.cos(math.radians(hour_angle))
    )
    
    # Solar azimuth angle
    azimuth = math.atan2(
        math.sin(math.radians(hour_angle)),
        math.cos(math.radians(hour_angle)) * math.sin(math.radians(latitude)) -
        math.tan(math.radians(declination)) * math.cos(math.radians(latitude))
    )
    
    return {
        'elevation': math.degrees(elevation),
        'azimuth': math.degrees(azimuth) + 180,  # Convert to 0-360 range
        'zenith': 90 - math.degrees(elevation)
    }

def calculate_irradiance_on_surface(ghi, dni, dhi, solar_position, surface_tilt, surface_azimuth):
    """Calculate irradiance on tilted surface using simplified model."""
    import math
    
    zenith = math.radians(solar_position['zenith'])
    sun_azimuth = math.radians(solar_position['azimuth'])
    surface_tilt_rad = math.radians(surface_tilt)
    surface_azimuth_rad = math.radians(surface_azimuth)
    
    # Calculate angle of incidence
    cos_incidence = (
        math.sin(zenith) * math.sin(surface_tilt_rad) * 
        math.cos(sun_azimuth - surface_azimuth_rad) +
        math.cos(zenith) * math.cos(surface_tilt_rad)
    )
    
    # Ensure cos_incidence is not negative
    cos_incidence = max(0, cos_incidence)
    
    # Simple POA calculation
    direct_on_surface = dni * cos_incidence
    diffuse_on_surface = dhi * (1 + math.cos(surface_tilt_rad)) / 2
    reflected_on_surface = ghi * 0.2 * (1 - math.cos(surface_tilt_rad)) / 2  # 0.2 = ground albedo
    
    poa_global = direct_on_surface + diffuse_on_surface + reflected_on_surface
    
    return max(0, poa_global)

def generate_radiation_grid(suitable_elements, tmy_data, latitude, longitude, shading_factors=None):
    """Generate radiation grid for all suitable elements."""
    
    if tmy_data is None or len(tmy_data) == 0:
        st.warning("No TMY data available for radiation calculations")
        return pd.DataFrame()
    
    # Convert TMY data to DataFrame if it's not already
    if isinstance(tmy_data, list):
        tmy_df = pd.DataFrame(tmy_data)
    else:
        tmy_df = tmy_data.copy()
    
    # Ensure datetime column exists
    if 'datetime' not in tmy_df.columns:
        # Create datetime from month, day, hour if available
        if all(col in tmy_df.columns for col in ['month', 'day', 'hour']):
            tmy_df['datetime'] = pd.to_datetime(
                tmy_df[['month', 'day', 'hour']].assign(year=2023)
            )
        else:
            # Create hourly data for a full year
            base_date = datetime(2023, 1, 1)
            tmy_df['datetime'] = pd.date_range(base_date, periods=len(tmy_df), freq='H')
    
    tmy_df['datetime'] = pd.to_datetime(tmy_df['datetime'])
    tmy_df['day_of_year'] = tmy_df['datetime'].dt.dayofyear
    tmy_df['hour'] = tmy_df['datetime'].dt.hour
    
    radiation_grid = []
    
    for _, element in suitable_elements.iterrows():
        # Get element properties with defaults
        element_id = element.get('Element ID', element.get('id', f"element_{len(radiation_grid)}"))
        element_area = float(element.get('Glass Area (m²)', element.get('area', 1.5)))
        orientation = element.get('Orientation', element.get('orientation', 'South'))
        azimuth = float(element.get('Azimuth (degrees)', element.get('azimuth', 180)))
        
        # Calculate tilt based on building type (assume vertical windows for BIPV)
        tilt = 90.0  # Vertical facade
        
        # Calculate irradiance for each hour
        hourly_irradiance = []
        
        for _, hour_data in tmy_df.iterrows():
            solar_pos = calculate_solar_position_simple(
                latitude, longitude, 
                hour_data['day_of_year'], 
                hour_data['hour']
            )
            
            # Get irradiance components (with defaults)
            ghi = hour_data.get('GHI', hour_data.get('ghi', 0))
            dni = hour_data.get('DNI', hour_data.get('dni', 0))
            dhi = hour_data.get('DHI', hour_data.get('dhi', ghi * 0.1))  # Estimate DHI if missing
            
            surface_irradiance = calculate_irradiance_on_surface(
                ghi, dni, dhi, solar_pos, tilt, azimuth
            )
            
            # Apply shading if available
            if shading_factors:
                shading_factor = shading_factors.get(str(hour_data['hour']), {}).get('shading_factor', 1.0)
                surface_irradiance *= shading_factor
            
            hourly_irradiance.append(surface_irradiance)
        
        # Convert to numpy array for calculations
        irradiance_array = np.array(hourly_irradiance)
        
        # Calculate monthly irradiation
        tmy_df['irradiance'] = irradiance_array
        monthly_irradiation = tmy_df.groupby(tmy_df['datetime'].dt.month)['irradiance'].sum() / 1000  # Convert W to kW
        
        # Calculate statistics
        annual_irradiation = irradiance_array.sum() / 1000  # kWh/m²/year
        peak_irradiance = irradiance_array.max()  # W/m²
        avg_irradiance = irradiance_array.mean()  # W/m²
        
        element_radiation = {
            'element_id': element_id,
            'element_type': 'Window',
            'orientation': orientation,
            'area': element_area,
            'tilt': tilt,
            'azimuth': azimuth,
            'annual_irradiation': annual_irradiation,
            'peak_irradiance': peak_irradiance,
            'avg_irradiance': avg_irradiance,
            'capacity_factor': safe_divide(avg_irradiance, 1000, 0),  # Simplified capacity factor
            'monthly_irradiation': monthly_irradiation.to_dict()
        }
        
        radiation_grid.append(element_radiation)
    
    return pd.DataFrame(radiation_grid)

def apply_orientation_corrections(radiation_df):
    """Apply orientation and tilt corrections to radiation calculations."""
    
    # Orientation factor corrections (relative to south-facing)
    orientation_corrections = {
        'South': 1.0,
        'Southwest': 0.95,
        'Southeast': 0.95,
        'West': 0.85,
        'East': 0.85,
        'Northwest': 0.70,
        'Northeast': 0.70,
        'North': 0.50
    }
    
    # Apply corrections
    radiation_df = radiation_df.copy()
    radiation_df['orientation_correction'] = radiation_df['orientation'].map(
        lambda x: orientation_corrections.get(x, 0.8)
    )
    
    # Apply correction to annual irradiation
    radiation_df['corrected_annual_irradiation'] = (
        radiation_df['annual_irradiation'] * radiation_df['orientation_correction']
    )
    
    return radiation_df

def render_radiation_grid():
    """Render the radiation and shading grid analysis module."""
    
    st.header("☀️ Step 5: Solar Radiation & Shading Analysis")
    
    # Check dependencies
    if not st.session_state.get('building_elements_completed', False):
        st.error("⚠️ Building elements data required. Please complete Step 4 (Facade & Window Extraction) first.")
        return
    
    if not st.session_state.get('weather_completed', False):
        st.error("⚠️ Weather data required. Please complete Step 3 (Weather & Environment Integration) first.")
        return
    
    # Load required data
    project_data = st.session_state.get('project_data', {})
    suitable_elements = project_data.get('suitable_elements')
    tmy_data = project_data.get('tmy_data')
    coordinates = project_data.get('coordinates', {})
    
    if suitable_elements is None or len(suitable_elements) == 0:
        st.error("No suitable building elements found. Please check Step 4 data.")
        return
    
    latitude = coordinates.get('lat', 52.52)
    longitude = coordinates.get('lng', 13.405)
    
    st.success(f"Analyzing {len(suitable_elements)} building elements for solar radiation potential")
    
    # Configuration section
    with st.expander("🔧 Analysis Configuration", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            include_shading = st.checkbox("Include Shading Analysis", value=False, key="include_shading_rad")
            apply_corrections = st.checkbox("Apply Orientation Corrections", value=True, key="apply_corrections_rad")
        
        with col2:
            analysis_precision = st.selectbox(
                "Analysis Precision",
                ["Standard", "High", "Maximum"],
                index=0,
                key="analysis_precision_rad"
            )
    
    # Shading factors input
    shading_factors = None
    if include_shading:
        st.subheader("⛅ Shading Configuration")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            morning_shading = st.slider("Morning Shading (6-12h)", 0.0, 1.0, 0.9, 0.1, key="morning_shading_rad")
        with col2:
            midday_shading = st.slider("Midday Shading (12-18h)", 0.0, 1.0, 1.0, 0.1, key="midday_shading_rad")
        with col3:
            evening_shading = st.slider("Evening Shading (18-20h)", 0.0, 1.0, 0.8, 0.1, key="evening_shading_rad")
        
        # Create hourly shading factors
        shading_factors = {}
        for hour in range(24):
            if 6 <= hour < 12:
                shading_factors[str(hour)] = {'shading_factor': morning_shading}
            elif 12 <= hour < 18:
                shading_factors[str(hour)] = {'shading_factor': midday_shading}
            elif 18 <= hour < 20:
                shading_factors[str(hour)] = {'shading_factor': evening_shading}
            else:
                shading_factors[str(hour)] = {'shading_factor': 0.1}  # Night
    
    # Analysis execution
    if st.button("🚀 Run Radiation Analysis", key="run_radiation_analysis"):
        with st.spinner("Calculating solar radiation on building surfaces..."):
            try:
                # Generate radiation grid
                radiation_data = generate_radiation_grid(
                    suitable_elements, tmy_data, latitude, longitude, shading_factors
                )
                
                if len(radiation_data) == 0:
                    st.error("Failed to generate radiation data")
                    return
                
                # Apply orientation corrections if requested
                if apply_corrections:
                    radiation_data = apply_orientation_corrections(radiation_data)
                
                # Save to session state and database
                st.session_state.project_data['radiation_data'] = radiation_data
                st.session_state.radiation_completed = True
                
                # Save to database
                db_manager.save_radiation_analysis(
                    st.session_state.project_data['project_id'],
                    {
                        'radiation_grid': radiation_data.to_dict('records'),
                        'analysis_config': {
                            'include_shading': include_shading,
                            'apply_corrections': apply_corrections,
                            'precision': analysis_precision,
                            'shading_factors': shading_factors
                        },
                        'location': {'latitude': latitude, 'longitude': longitude}
                    }
                )
                
                st.success("✅ Radiation analysis completed successfully!")
                
            except Exception as e:
                st.error(f"Error during radiation analysis: {str(e)}")
                return
    
    # Display results if available
    if st.session_state.get('radiation_completed', False):
        radiation_data = st.session_state.project_data.get('radiation_data')
        
        if radiation_data is not None and len(radiation_data) > 0:
            st.subheader("📊 Radiation Analysis Results")
            
            # Summary statistics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_annual = radiation_data['annual_irradiation'].mean()
                st.metric("Average Annual Irradiation", f"{avg_annual:.0f} kWh/m²")
            
            with col2:
                max_annual = radiation_data['annual_irradiation'].max()
                st.metric("Maximum Annual Irradiation", f"{max_annual:.0f} kWh/m²")
            
            with col3:
                avg_peak = radiation_data['peak_irradiance'].mean()
                st.metric("Average Peak Irradiance", f"{avg_peak:.0f} W/m²")
            
            with col4:
                total_area = radiation_data['area'].sum()
                st.metric("Total Analyzed Area", f"{total_area:.1f} m²")
            
            # Detailed results table
            st.subheader("📋 Element-by-Element Analysis")
            
            # Prepare display dataframe
            display_df = radiation_data.copy()
            display_columns = ['element_id', 'orientation', 'area', 'annual_irradiation', 'peak_irradiance', 'avg_irradiance']
            
            if apply_corrections and 'corrected_annual_irradiation' in display_df.columns:
                display_columns.append('corrected_annual_irradiation')
            
            st.dataframe(
                display_df[display_columns].round(2),
                use_container_width=True,
                column_config={
                    'element_id': 'Element ID',
                    'orientation': 'Orientation',
                    'area': st.column_config.NumberColumn('Area (m²)', format="%.2f"),
                    'annual_irradiation': st.column_config.NumberColumn('Annual Irradiation (kWh/m²)', format="%.0f"),
                    'peak_irradiance': st.column_config.NumberColumn('Peak Irradiance (W/m²)', format="%.0f"),
                    'avg_irradiance': st.column_config.NumberColumn('Avg Irradiance (W/m²)', format="%.0f"),
                    'corrected_annual_irradiation': st.column_config.NumberColumn('Corrected Annual (kWh/m²)', format="%.0f")
                }
            )
            
            # Visualization section
            st.subheader("📈 Radiation Distribution Analysis")
            
            tab1, tab2, tab3 = st.tabs(["Annual Irradiation", "Orientation Analysis", "Monthly Patterns"])
            
            with tab1:
                # Annual irradiation histogram
                fig_hist = px.histogram(
                    radiation_data, 
                    x='annual_irradiation',
                    title="Distribution of Annual Irradiation",
                    labels={'annual_irradiation': 'Annual Irradiation (kWh/m²)', 'count': 'Number of Elements'}
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            
            with tab2:
                # Radiation by orientation
                orientation_stats = radiation_data.groupby('orientation')['annual_irradiation'].agg(['mean', 'count']).reset_index()
                
                fig_orient = px.bar(
                    orientation_stats,
                    x='orientation',
                    y='mean',
                    title="Average Annual Irradiation by Orientation",
                    labels={'mean': 'Avg Annual Irradiation (kWh/m²)', 'orientation': 'Orientation'}
                )
                st.plotly_chart(fig_orient, use_container_width=True)
            
            with tab3:
                # Monthly patterns (if monthly data available)
                if 'monthly_irradiation' in radiation_data.columns:
                    # Extract monthly data for visualization
                    monthly_data = []
                    for _, row in radiation_data.iterrows():
                        if isinstance(row['monthly_irradiation'], dict):
                            for month, irrad in row['monthly_irradiation'].items():
                                monthly_data.append({
                                    'element_id': row['element_id'],
                                    'month': int(month),
                                    'irradiation': irrad,
                                    'orientation': row['orientation']
                                })
                    
                    if monthly_data:
                        monthly_df = pd.DataFrame(monthly_data)
                        monthly_avg = monthly_df.groupby('month')['irradiation'].mean().reset_index()
                        
                        fig_monthly = px.line(
                            monthly_avg,
                            x='month',
                            y='irradiation',
                            title="Average Monthly Irradiation Pattern",
                            labels={'irradiation': 'Monthly Irradiation (kWh/m²)', 'month': 'Month'}
                        )
                        st.plotly_chart(fig_monthly, use_container_width=True)
                    else:
                        st.info("Monthly pattern data not available")
                else:
                    st.info("Monthly pattern data not available")
            
            # Export options
            st.subheader("💾 Export Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 Download Radiation Data (CSV)", key="download_radiation_csv"):
                    csv_data = radiation_data.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv_data,
                        file_name=f"radiation_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            
            with col2:
                st.info("Radiation analysis ready for next step (PV Specification)")
        
        else:
            st.warning("No radiation data available. Please run the analysis.")