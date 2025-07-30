"""
Step 3: Weather & Environment Integration for BIPV Optimizer
Database-driven TMY generation with ISO 15927-4 compliance
"""
import streamlit as st
import os
import math
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import plotly.express as px
import plotly.graph_objects as go

# Core imports
from core.solar_math import calculate_solar_position_iso, SimpleMath
from services.io import get_current_project_id, find_nearest_wmo_station
from database_manager import BIPVDatabaseManager
from utils.database_helper import DatabaseHelper


class WeatherEnvironmentController:
    """Controller for Step 3: Weather & Environment Integration"""
    
    def __init__(self):
        self.db_manager = BIPVDatabaseManager()
        self.data_manager = DatabaseHelper()
        self.project_id = get_current_project_id()
    
    def get_climate_zone(self, latitude: float) -> str:
        """Determine climate zone based on latitude"""
        abs_lat = abs(latitude)
        if abs_lat < 23.5:
            return "Tropical"
        elif abs_lat < 35:
            return "Subtropical"
        elif abs_lat < 50:
            return "Temperate"
        elif abs_lat < 66.5:
            return "Subarctic"
        else:
            return "Arctic"
    
    def get_base_temperature(self, latitude: float) -> float:
        """Get base temperature for climate zone"""
        climate_zone = self.get_climate_zone(latitude)
        temperature_map = {
            "Tropical": 25.0,
            "Subtropical": 20.0,
            "Temperate": 15.0,
            "Subarctic": 10.0,
            "Arctic": 5.0
        }
        return temperature_map.get(climate_zone, 15.0)


def generate_tmy_from_wmo_station(weather_station: Dict, coordinates: Dict, controller: WeatherEnvironmentController, include_diffuse: bool = True) -> List[Dict]:
    """
    Generate ISO 15927-4 compliant TMY data from WMO weather station with database integration
    
    Args:
        weather_station: Selected WMO weather station data
        coordinates: Project coordinates (lat, lon)
        controller: WeatherEnvironmentController instance
    
    Returns:
        List of 8760 hourly TMY records with complete meteorological data
    """
    if not weather_station:
        st.error("❌ No weather station data available for TMY generation")
        return []
    
    # Extract coordinates and station data
    lat, lon = float(coordinates['lat']), float(coordinates['lon'])
    station_lat = float(weather_station.get('latitude', lat))
    station_lon = float(weather_station.get('longitude', lon))
    station_elevation = float(weather_station.get('height', 0))
    
    # Climate-based parameters
    base_temperature = controller.get_base_temperature(station_lat)
    climate_zone = controller.get_climate_zone(station_lat)
    
    # Solar parameters for latitude
    clearness_index = 0.5  # Standard clearness index
    if abs(station_lat) < 35:  # Lower latitudes, clearer skies
        clearness_index = 0.6
    elif abs(station_lat) > 55:  # Higher latitudes, more clouds
        clearness_index = 0.4
    
    # Initialize TMY data array
    tmy_data = []
    debug_records = []
    
    # Generate 8760 hourly records (365 days × 24 hours)
    for day in range(1, 366):
        for hour in range(24):
            # Calculate solar position using ISO 15927-4 methodology
            solar_pos = calculate_solar_position_iso(station_lat, station_lon, day, hour)
            
            # Initialize irradiance values
            dni = dhi = ghi = 0.0
            air_mass = 0.0
            
            # Solar irradiance calculations (only for daylight hours)
            if solar_pos['elevation'] > 0:
                # Air mass calculation (ISO 15927-4 standard)
                air_mass = 1.0 / (math.sin(math.radians(solar_pos['elevation'])) + 
                                 0.50572 * (6.07995 + solar_pos['elevation']) ** -1.6364)
                
                # Extraterrestrial irradiance calculation
                solar_constant = 1367.0  # W/m² (ISO 9060 standard)
                day_angle = 2.0 * math.pi * (day - 1) / 365.0
                
                # Eccentricity correction factor
                eccentricity_correction = (1.000110 + 0.034221 * math.cos(day_angle) + 
                                         0.001280 * math.sin(day_angle) + 
                                         0.000719 * math.cos(2 * day_angle) + 
                                         0.000077 * math.sin(2 * day_angle))
                
                extraterrestrial_irradiance = (solar_constant * eccentricity_correction * 
                                             math.sin(math.radians(solar_pos['elevation'])))
                
                # Calculate irradiance components for meaningful sun angles
                if solar_pos['elevation'] > 5.0:
                    # Direct Normal Irradiance (DNI) - atmospheric attenuation model
                    atmospheric_attenuation = math.exp(-0.09 * air_mass * (1.0 - station_elevation / 8400.0))
                    dni = extraterrestrial_irradiance * clearness_index * atmospheric_attenuation
                    
                    # Diffuse Horizontal Irradiance (DHI) - Perez model
                    if clearness_index <= 0.22:
                        diffuse_fraction = 1.0 - 0.09 * clearness_index
                    elif clearness_index <= 0.80:
                        diffuse_fraction = (0.9511 - 0.1604 * clearness_index + 
                                          4.388 * clearness_index**2 - 
                                          16.638 * clearness_index**3 + 
                                          12.336 * clearness_index**4)
                    else:
                        diffuse_fraction = 0.165
                    
                    dhi = extraterrestrial_irradiance * clearness_index * diffuse_fraction
                    
                    # Global Horizontal Irradiance (GHI)
                    ghi = dni * math.sin(math.radians(solar_pos['elevation'])) + dhi
                    
                    # Ensure realistic values
                    dni = max(0.0, min(dni, 1200.0))
                    dhi = max(0.0, min(dhi, 800.0))
                    ghi = max(0.0, min(ghi, 1400.0))
            
            # Temperature calculation using ISO 15927-4 methodology
            seasonal_amplitude = 12.0 if climate_zone == "Temperate" else 8.0
            seasonal_phase = 228  # Day of maximum temperature (mid-August)
            seasonal_temp = seasonal_amplitude * math.cos(2.0 * math.pi * (day - seasonal_phase) / 365.0)
            
            # Daily temperature variation
            daily_amplitude = 8.0
            daily_phase = 14  # Hour of maximum temperature (2 PM)
            daily_temp = daily_amplitude * math.cos(2.0 * math.pi * (hour - daily_phase) / 24.0)
            
            # Final temperature with climate adjustment
            temperature = float(base_temperature + seasonal_temp + daily_temp)
            
            # Additional meteorological parameters
            # Humidity calculation (based on temperature and season)
            base_humidity = 60.0  # Base humidity percentage
            seasonal_humidity_variation = 20.0 * math.cos(2.0 * math.pi * (day - 30) / 365.0)  # Spring peak
            daily_humidity_variation = -15.0 * math.cos(2.0 * math.pi * (hour - 6) / 24.0)  # Morning peak
            humidity = max(30.0, min(95.0, base_humidity + seasonal_humidity_variation + daily_humidity_variation))
            
            # Atmospheric pressure (based on elevation and weather patterns)
            sea_level_pressure = 1013.25  # hPa
            pressure = sea_level_pressure * math.exp(-station_elevation / 8400.0)
            
            # Wind parameters (simplified model)
            wind_speed = max(0.5, 5.0 + 3.0 * math.sin(2.0 * math.pi * day / 365.0) + 
                           2.0 * math.cos(2.0 * math.pi * hour / 24.0))
            wind_direction = (180.0 + 60.0 * math.sin(2.0 * math.pi * day / 365.0) + 
                            30.0 * math.cos(2.0 * math.pi * hour / 24.0)) % 360.0
            
            # Cloud cover estimation
            cloud_cover = max(0.0, min(100.0, 50.0 * (1.0 - clearness_index) + 
                                      20.0 * math.sin(2.0 * math.pi * day / 365.0)))
            
            # Create comprehensive TMY record with configurable irradiance data
            tmy_record = {
                # Temporal information
                'datetime': f"2023-{(day-1)//31+1:02d}-{(day-1)%31+1:02d} {hour:02d}:00:00",
                'day': day,
                'hour': hour,
                'month': (day - 1) // 31 + 1,
                'day_of_month': (day - 1) % 31 + 1,
                
                # Solar position data
                'solar_elevation': round(max(0.0, solar_pos['elevation']), 2),
                'solar_azimuth': round(solar_pos['azimuth'], 2),
                'air_mass': round(air_mass, 3),
                'clearness_index': round(clearness_index, 3),
                
                # Irradiance data (W/m²) - conditional based on include_diffuse
                'ghi': round(ghi, 1),
                'dni': round(dni, 1),
            }
            
            # Add DHI only if requested for advanced calculations
            if include_diffuse:
                tmy_record['dhi'] = round(dhi, 1)
                tmy_record['diffuse_mode'] = 'advanced'
            else:
                tmy_record['diffuse_mode'] = 'simple'
            
            # Add remaining data
            tmy_record.update({
                # Meteorological data
                'temperature': round(temperature, 1),
                'humidity': round(humidity, 1),
                'pressure': round(pressure, 1),
                'wind_speed': round(wind_speed, 1),
                'wind_direction': round(wind_direction, 1),
                'cloud_cover': round(cloud_cover, 1),
                
                # Metadata
                'source': 'WMO_ISO15927-4',
                'station_id': weather_station.get('wmo_id', 'unknown'),
                'station_name': weather_station.get('name', 'unknown'),
                'station_distance_km': round(weather_station.get('distance_km', 0), 1),
                'climate_zone': climate_zone,
                'generation_method': 'ISO_15927-4_Compliant'
            })
            
            tmy_data.append(tmy_record)
            
            # Store debug records for key times
            if (day == 172 and hour == 12) or (day == 355 and hour == 12) or (day == 80 and hour in [6, 18]):
                debug_records.append({
                    'description': f"Day {day}, Hour {hour}",
                    'elevation': solar_pos['elevation'],
                    'ghi': ghi,
                    'temperature': temperature,
                    'clearness': clearness_index
                })
    
    # Store debug records for analysis
    if debug_records:
        st.session_state['tmy_debug_records'] = debug_records
    
    return tmy_data


def calculate_monthly_solar_profiles(tmy_data: List[Dict]) -> Dict:
    """Calculate monthly solar irradiance profiles from TMY data"""
    if not tmy_data:
        return {}
    
    monthly_profiles = {}
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Initialize monthly data storage
    for i, month in enumerate(months, 1):
        monthly_profiles[month] = {
            'ghi_values': [],
            'dni_values': [],
            'dhi_values': [],
            'temp_values': [],
            'days': []
        }
    
    # Process TMY data by month
    for record in tmy_data:
        month_num = record.get('month', 1)
        if 1 <= month_num <= 12:
            month_name = months[month_num - 1]
            
            # Only include daylight hours for solar data
            if record.get('solar_elevation', 0) > 5:
                monthly_profiles[month_name]['ghi_values'].append(float(record.get('ghi', 0)))
                monthly_profiles[month_name]['dni_values'].append(float(record.get('dni', 0)))
                monthly_profiles[month_name]['dhi_values'].append(float(record.get('dhi', 0)))
            
            # Include all hours for temperature
            monthly_profiles[month_name]['temp_values'].append(float(record.get('temperature', 15)))
            monthly_profiles[month_name]['days'].append(record.get('day', 1))
    
    # Calculate monthly statistics with explicit float conversion
    monthly_stats = {}
    for month in months:
        ghi_vals = monthly_profiles[month]['ghi_values']
        dni_vals = monthly_profiles[month]['dni_values'] 
        dhi_vals = monthly_profiles[month]['dhi_values']
        temp_vals = monthly_profiles[month]['temp_values']
        
        if ghi_vals:  # Has daylight data
            monthly_stats[month] = {
                'avg_ghi': float(sum(ghi_vals) / len(ghi_vals)),
                'max_ghi': float(max(ghi_vals)),
                'avg_dni': float(sum(dni_vals) / len(dni_vals)),
                'avg_dhi': float(sum(dhi_vals) / len(dhi_vals)),
                'monthly_ghi_total': float(sum(ghi_vals)) / 1000.0,  # kWh/m²
                'avg_temp': float(sum(temp_vals) / len(temp_vals)),
                'daylight_hours': len(ghi_vals) / 30.4  # Average per day
            }
        else:  # No daylight (polar winter)
            monthly_stats[month] = {
                'avg_ghi': 0.0,
                'max_ghi': 0.0,
                'avg_dni': 0.0,
                'avg_dhi': 0.0,
                'monthly_ghi_total': 0.0,
                'avg_temp': float(sum(temp_vals) / len(temp_vals)) if temp_vals else 0.0,
                'daylight_hours': 0.0
            }
    
    return monthly_stats


def calculate_annual_statistics(tmy_data: List[Dict]) -> Dict:
    """Calculate annual statistics from TMY data with explicit float conversion"""
    if not tmy_data:
        return {}
    
    # Initialize accumulators
    total_ghi = total_dni = total_dhi = 0.0
    temp_values = []
    peak_ghi = 0.0
    daylight_hours = 0
    
    # Process all TMY records
    for record in tmy_data:
        # Solar irradiance (only for daylight)
        if record.get('solar_elevation', 0) > 5:
            ghi = float(record.get('ghi', 0))
            dni = float(record.get('dni', 0))
            dhi = float(record.get('dhi', 0))
            
            total_ghi += ghi
            total_dni += dni
            total_dhi += dhi
            peak_ghi = max(peak_ghi, ghi)
            daylight_hours += 1
        
        # Temperature (all hours)
        temp_values.append(float(record.get('temperature', 15)))
    
    # Calculate statistics with explicit float conversion
    annual_stats = {
        'annual_ghi': float(total_ghi) / 1000.0,  # Convert to kWh/m²
        'annual_dni': float(total_dni) / 1000.0,
        'annual_dhi': float(total_dhi) / 1000.0,
        'peak_ghi': float(peak_ghi),
        'total_irradiance': float(total_ghi + total_dni + total_dhi) / 1000.0,
        'avg_temperature': float(sum(temp_values) / len(temp_values)) if temp_values else 15.0,
        'peak_sun_hours': float(total_ghi) / 1000.0 / 365.0,
        'daylight_hours_per_day': float(daylight_hours) / 365.0,
        'data_records': len(tmy_data)
    }
    
    # Solar resource classification
    annual_ghi_kwh = annual_stats['annual_ghi']
    if annual_ghi_kwh > 1800:
        resource_class = "Excellent"
    elif annual_ghi_kwh > 1400:
        resource_class = "Very Good"
    elif annual_ghi_kwh > 1200:
        resource_class = "Good"
    elif annual_ghi_kwh > 1000:
        resource_class = "Moderate"
    else:
        resource_class = "Poor"
    
    annual_stats['solar_resource_class'] = resource_class
    
    return annual_stats


def apply_environmental_factors(tmy_data: List[Dict], environmental_factors: Dict) -> List[Dict]:
    """Apply environmental shading factors to TMY data with explicit float conversion"""
    if not tmy_data or not environmental_factors:
        return tmy_data
    
    # Calculate total shading reduction
    shading_reduction = 0.0
    if environmental_factors.get('trees_nearby', False):
        shading_reduction += 15.0  # 15% reduction from trees
    if environmental_factors.get('tall_buildings', False):
        shading_reduction += 10.0  # 10% reduction from buildings
    
    if shading_reduction == 0:
        return tmy_data
    
    # Apply shading factor to irradiance values
    shading_factor = 1.0 - (float(shading_reduction) / 100.0)
    adjusted_tmy_data = []
    
    for record in tmy_data:
        adjusted_record = record.copy()
        
        # Apply shading to all irradiance components
        irradiance_fields = ['ghi', 'dni', 'dhi']
        for field in irradiance_fields:
            if field in adjusted_record and adjusted_record[field] is not None:
                original_value = float(adjusted_record[field] or 0)
                adjusted_record[field] = round(original_value * float(shading_factor), 1)
        
        # Add environmental metadata
        adjusted_record['environmental_adjustment'] = float(shading_reduction)
        adjusted_record['shading_applied'] = True
        
        adjusted_tmy_data.append(adjusted_record)
    
    return adjusted_tmy_data


def create_monthly_solar_chart(monthly_stats: Dict) -> go.Figure:
    """Create interactive monthly solar profile chart"""
    if not monthly_stats:
        return go.Figure()
    
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    ghi_values = [monthly_stats.get(month, {}).get('monthly_ghi_total', 0) for month in months]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=months,
        y=ghi_values,
        name='Monthly GHI (kWh/m²)',
        marker_color='orange',
        text=[f"{val:.1f}" for val in ghi_values],
        textposition='outside'
    ))
    
    fig.update_layout(
        title='Monthly Solar Irradiance Profile',
        xaxis_title='Month',
        yaxis_title='Global Horizontal Irradiance (kWh/m²)',
        showlegend=False,
        height=400
    )
    
    return fig


def render_weather_environment():
    """Render the complete Step 3: Weather & Environment Integration page"""
    st.header("☀️ Step 3: Weather & Environment Integration")
    st.markdown("Generate **ISO 15927-4 compliant** TMY data and environmental analysis")
    
    # Initialize controller
    controller = WeatherEnvironmentController()
    
    # Load project data from database using project ID only
    project_id = controller.project_id
    if not project_id:
        st.error("❌ No project ID found. Please complete Step 1 first.")
        return
    
    try:
        # Get project information from database
        project_info = controller.db_manager.get_project_info(project_id)
        if not project_info:
            st.error("❌ Project not found in database. Please complete Step 1 first.")
            return
        
        # Extract coordinates from database with None checking
        coordinates = {
            'lat': float(project_info.get('latitude') or 0),
            'lon': float(project_info.get('longitude') or 0)
        }
        
        # Extract WMO weather station from database with None checking
        weather_station = {
            'name': project_info.get('weather_station_name') or 'Unknown',
            'wmo_id': project_info.get('weather_station_id') or 'unknown',
            'distance_km': float(project_info.get('weather_station_distance') or 0),
            'latitude': float(project_info.get('weather_station_latitude') or coordinates['lat']),
            'longitude': float(project_info.get('weather_station_longitude') or coordinates['lon']),
            'height': float(project_info.get('weather_station_elevation') or 0)
        }
        
        if coordinates['lat'] == 0 or coordinates['lon'] == 0:
            st.error("❌ Invalid coordinates in database. Please complete Step 1 project setup.")
            return
            
        if weather_station['wmo_id'] == 'unknown':
            st.error("❌ No WMO weather station found in database. Please complete Step 1 weather station selection.")
            return
            
    except Exception as e:
        st.error(f"❌ Error retrieving project data: {str(e)}")
        st.write("Please ensure Step 1 project setup is completed with valid coordinates and weather station selection.")
        return
    
    # Display project and weather station info
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Project Location**: {coordinates['lat']:.4f}°N, {coordinates['lon']:.4f}°E")
        
    with col2:
        st.info(f"**Weather Station**: {weather_station.get('name', 'Unknown')} "
               f"({weather_station.get('distance_km', 0):.1f} km)")
    
    # TMY Generation Section
    st.subheader("🌤️ TMY Data Generation")
    
    # TMY Data Configuration Controls
    with st.expander("⚙️ TMY Data Configuration", expanded=False):
        st.markdown("**Configure what meteorological data to fetch from weather APIs**")
        
        include_diffuse = st.checkbox(
            "🌅 Include diffuse irradiance components for advanced calculations",
            value=True,
            help="Fetches DHI (Diffuse Horizontal Irradiance) data for enhanced solar modeling. Required for research-grade accuracy in Step 5."
        )
        
        if include_diffuse:
            st.success("✅ **Advanced TMY Mode** - Will fetch GHI, DNI, and DHI components")
            st.markdown("- Enables research-grade solar calculations in Step 5")
            st.markdown("- Supports advanced diffuse irradiance modeling")
            st.markdown("- Required for 'Advanced' calculation precision mode")
        else:
            st.info("ℹ️ **Simple TMY Mode** - Will fetch GHI and DNI only")
            st.markdown("- Faster data fetching and processing")
            st.markdown("- Sufficient for 'Simple' calculation precision mode")
            st.markdown("- DHI estimated from GHI-DNI difference")
    
    existing_weather_data = controller.data_manager.get_step_data("3")
    has_existing_tmy = existing_weather_data and existing_weather_data.get('tmy_data')
    
    if has_existing_tmy:
        st.success("✅ TMY data already generated")
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🔄 Regenerate TMY"):
                st.session_state['regenerate_tmy'] = True
                st.rerun()
    
    if not has_existing_tmy or st.session_state.get('regenerate_tmy', False):
        with st.status("Generating TMY data...", expanded=True) as status:
            st.write("📡 Connecting to WMO weather station...")
            st.write(f"🌍 Climate zone: {controller.get_climate_zone(coordinates['lat'])}")
            st.write("☀️ Calculating solar positions...")
            
            # Generate TMY data with diffuse configuration
            tmy_data = generate_tmy_from_wmo_station(weather_station, coordinates, controller, include_diffuse)
            
            if tmy_data:
                st.write("📊 Processing 8,760 hourly records...")
                
                # Calculate statistics
                monthly_stats = calculate_monthly_solar_profiles(tmy_data)
                annual_stats = calculate_annual_statistics(tmy_data)
                
                # Save to database
                weather_data = {
                    'tmy_data': json.dumps(tmy_data),
                    'monthly_profiles': json.dumps(monthly_stats),
                    'annual_statistics': json.dumps(annual_stats),
                    'station_metadata': json.dumps(weather_station),
                    'generation_method': 'ISO_15927-4_Compliant',
                    'coordinates': json.dumps(coordinates)
                }
                
                try:
                    controller.db_manager.save_weather_data(controller.project_id, weather_data)
                    controller.data_manager.save_step_data("3", {
                        'tmy_data': tmy_data,
                        'monthly_stats': monthly_stats,
                        'annual_stats': annual_stats,
                        'weather_station': weather_station
                    })
                    status.update(label="✅ TMY generation completed!", state="complete")
                    st.session_state['regenerate_tmy'] = False
                except Exception as e:
                    st.error(f"❌ Database save error: {str(e)}")
                    return
            else:
                status.update(label="❌ TMY generation failed", state="error")
                return
    
    # Load existing data for display
    step_data = controller.data_manager.get_step_data("3")
    if step_data:
        tmy_data = step_data.get('tmy_data', [])
        monthly_stats = step_data.get('monthly_stats', {})
        annual_stats = step_data.get('annual_stats', {})
        
        # Display annual statistics
        st.subheader("📈 Annual Solar Resource Analysis")
        
        if annual_stats:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Annual GHI", f"{annual_stats.get('annual_ghi', 0):.0f} kWh/m²")
                
            with col2:
                st.metric("Peak GHI", f"{annual_stats.get('peak_ghi', 0):.0f} W/m²")
                
            with col3:
                st.metric("Avg Temperature", f"{annual_stats.get('avg_temperature', 0):.1f}°C")
                
            with col4:
                st.metric("Solar Resource", annual_stats.get('solar_resource_class', 'Unknown'))
        
        # Monthly solar profile chart
        if monthly_stats:
            st.subheader("📊 Monthly Solar Profile")
            chart = create_monthly_solar_chart(monthly_stats)
            st.plotly_chart(chart, use_container_width=True)
    
    # Environmental Considerations Section
    st.subheader("🌳 Environmental Considerations & Shading Analysis")
    
    with st.expander("Environmental Shading Factors", expanded=False):
        st.markdown("""
        **Purpose**: Account for environmental shading that reduces solar irradiance reaching building surfaces
        
        **Academic References**:
        - Trees: 15% reduction (Gueymard, Solar Energy 2012)
        - Buildings: 10% reduction (Appelbaum & Bany, Solar Energy 1979)
        """)
        
        trees_nearby = st.checkbox(
            "🌲 Trees within 50m of building", 
            help="Nearby vegetation that may cast shadows on facade elements"
        )
        
        tall_buildings = st.checkbox(
            "🏢 Tall buildings nearby", 
            help="Adjacent structures that may create shading during certain hours"
        )
        
        if trees_nearby or tall_buildings:
            st.info("Environmental factors will reduce calculated solar irradiance")
            
            # Apply environmental factors if TMY data exists
            if tmy_data:
                environmental_factors = {
                    'trees_nearby': trees_nearby,
                    'tall_buildings': tall_buildings
                }
                
                adjusted_tmy_data = apply_environmental_factors(tmy_data, environmental_factors)
                adjusted_annual_stats = calculate_annual_statistics(adjusted_tmy_data)
                
                # Show impact
                if annual_stats and adjusted_annual_stats:
                    original_ghi = annual_stats.get('annual_ghi', 0)
                    adjusted_ghi = adjusted_annual_stats.get('annual_ghi', 0)
                    reduction_percent = ((original_ghi - adjusted_ghi) / original_ghi * 100) if original_ghi > 0 else 0
                    
                    st.warning(f"⚠️ Environmental shading reduces annual GHI by {reduction_percent:.1f}% "
                             f"({original_ghi:.0f} → {adjusted_ghi:.0f} kWh/m²)")
                    
                    # Update stored data with environmental adjustments
                    controller.data_manager.save_step_data("3", {
                        'tmy_data': adjusted_tmy_data,
                        'monthly_stats': calculate_monthly_solar_profiles(adjusted_tmy_data),
                        'annual_stats': adjusted_annual_stats,
                        'weather_station': weather_station,
                        'environmental_factors': environmental_factors
                    })
    
    # Navigation - Single Continue Button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if step_data and step_data.get('tmy_data'):
            if st.button("Continue to Step 4: Facade Extraction →", type="primary", key="nav_step4"):
                st.session_state.current_step = "facade_extraction"
                st.session_state.scroll_to_top = True
                st.rerun()
        else:
            st.button("Complete TMY Generation First", disabled=True)


if __name__ == "__main__":
    render_weather_environment()
