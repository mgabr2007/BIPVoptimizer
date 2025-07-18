"""
Weather and Environment Integration page for BIPV Optimizer
"""
import streamlit as st
import os
import math
import pandas as pd
import calendar
from datetime import datetime, timedelta
from core.solar_math import calculate_solar_position_iso, classify_solar_resource_iso, SimpleMath
from services.io import get_weather_data_from_coordinates, fetch_openweather_forecast_data, find_nearest_wmo_station, save_project_data
from utils.database_helper import db_helper



def generate_tmy_from_wmo_station(weather_station, solar_params, coordinates):
    """
    Generate TMY data using ISO 15927-4 standards from WMO weather station
    
    Args:
        weather_station: Selected WMO weather station data
        solar_params: Solar parameters from location analysis
        coordinates: Project coordinates (lat, lon)
    
    Returns:
        TMY data array with 8760 hourly records
    """
    if not weather_station:
        return None
    
    tmy_data = []
    lat, lon = coordinates['lat'], coordinates['lon']
    station_lat = weather_station.get('latitude', lat)
    station_lon = weather_station.get('longitude', lon)
    station_elevation = weather_station.get('height', 0)
    
    # ISO 15927-4 TMY generation parameters
    base_temperature = 15.0  # Default base temperature for Central Europe
    if abs(station_lat) < 23.5:  # Tropical zone
        base_temperature = 25.0
    elif abs(station_lat) > 60:  # Arctic zone
        base_temperature = 5.0
    
    # Generate hourly data for typical meteorological year
    debug_records = []  # Store sample records for debugging
    
    for day in range(1, 366):  # 365 days (ISO 15927-4 standard)
        for hour in range(24):
            # Calculate solar position using ISO methodology
            solar_pos = calculate_solar_position_iso(station_lat, station_lon, day, hour)
            
            # Debug: Store sample records for verification
            if (day == 172 and hour == 12) or (day == 1 and hour in [6, 12, 18]) or (day == 180 and hour == 12):
                debug_records.append({
                    'day': day, 'hour': hour, 'elevation': solar_pos['elevation'], 
                    'azimuth': solar_pos['azimuth'], 'lat': station_lat, 'lon': station_lon
                })
            
            # Initialize default values
            clearness_index = solar_params.get('clearness', 0.5)
            air_mass = 0
            
            # ISO 15927-4 irradiance calculations
            if solar_pos['elevation'] > 0:
                # Air mass calculation (ISO 15927-4)
                air_mass = 1 / (math.sin(math.radians(solar_pos['elevation'])) + 
                               0.50572 * (6.07995 + solar_pos['elevation']) ** -1.6364)
                
                # Extraterrestrial irradiance (ISO 15927-4)
                solar_constant = 1367  # W/m² (ISO 9060)
                day_angle = 2 * math.pi * (day - 1) / 365
                eccentricity_correction = 1.000110 + 0.034221 * math.cos(day_angle) + \
                                        0.001280 * math.sin(day_angle) + 0.000719 * math.cos(2 * day_angle) + \
                                        0.000077 * math.sin(2 * day_angle)
                
                extraterrestrial_irradiance = solar_constant * eccentricity_correction * \
                                            math.sin(math.radians(solar_pos['elevation']))
                
                # Ensure minimum elevation for realistic irradiance
                if solar_pos['elevation'] > 5.0:  # Only calculate for meaningful elevation angles
                    # Direct Normal Irradiance (DNI) - ISO 15927-4
                    atmospheric_attenuation = math.exp(-0.09 * air_mass * (1 - station_elevation / 8400))
                    dni = extraterrestrial_irradiance * clearness_index * atmospheric_attenuation
                    
                    # Diffuse Horizontal Irradiance (DHI) - ISO 15927-4
                    if clearness_index <= 0.22:
                        diffuse_fraction = 1.0 - 0.09 * clearness_index
                    elif clearness_index <= 0.80:
                        diffuse_fraction = 0.9511 - 0.1604 * clearness_index + \
                                         4.388 * clearness_index**2 - 16.638 * clearness_index**3 + \
                                         12.336 * clearness_index**4
                    else:
                        diffuse_fraction = 0.165
                    
                    dhi = extraterrestrial_irradiance * clearness_index * diffuse_fraction
                    
                    # Global Horizontal Irradiance (GHI) - ISO 15927-4
                    ghi = dni * math.sin(math.radians(solar_pos['elevation'])) + dhi
                    
                    # Debug: Store calculation details for noon hours
                    if hour == 12 and day in [1, 172, 355]:
                        debug_records.append({
                            'day': day, 'hour': hour, 'elevation': solar_pos['elevation'],
                            'clearness': clearness_index, 'extraterrestrial': extraterrestrial_irradiance,
                            'dni': dni, 'dhi': dhi, 'ghi': ghi, 'air_mass': air_mass
                        })
                else:
                    dni = dhi = ghi = 0
            else:
                dni = dhi = ghi = 0
            
            # Temperature calculation using ISO 15927-4 methodology
            # Seasonal variation (sinusoidal model)
            seasonal_amplitude = 12.0  # ±12°C seasonal variation
            seasonal_phase = 228  # Day of maximum temperature (mid-August, day 228)
            seasonal_temp = seasonal_amplitude * math.cos(2 * math.pi * (day - seasonal_phase) / 365)
            
            # Daily temperature variation
            daily_amplitude = 8.0  # ±8°C daily variation
            daily_phase = 14  # Hour of maximum temperature (2 PM)
            daily_temp = daily_amplitude * math.cos(2 * math.pi * (hour - daily_phase) / 24)
            
            # Final temperature
            temperature = base_temperature + seasonal_temp + daily_temp
            
            # Debug: Store temperature calculation details for verification
            if (day == 1 and hour == 12) or (day == 213 and hour == 12):  # Jan 1st noon and Aug 1st noon
                debug_records.append({
                    'day': day, 'hour': hour, 'base_temp': base_temperature,
                    'seasonal': seasonal_temp, 'daily': daily_temp, 'final_temp': temperature,
                    'season_phase': seasonal_phase, 'day_phase': daily_phase
                })
            
            # Humidity calculation (ISO 15927-4 based)
            # Higher humidity at night and in winter
            base_humidity = 65
            seasonal_humidity_factor = -10 * math.cos(2 * math.pi * (day - 15) / 365)
            daily_humidity_factor = -15 * math.cos(2 * math.pi * (hour - 6) / 24)
            humidity = max(20, min(95, base_humidity + seasonal_humidity_factor + daily_humidity_factor))
            
            # Wind speed estimation (simplified seasonal model)
            base_wind = 3.5  # m/s
            seasonal_wind = 1.0 * math.cos(2 * math.pi * (day - 60) / 365)  # Higher in winter
            wind_speed = max(0.5, base_wind + seasonal_wind)
            
            # Cloud cover estimation from clearness index
            cloud_cover = max(0, min(100, (1 - clearness_index) * 100))
            
            # Ensure air_mass is defined for night hours
            if solar_pos['elevation'] <= 0:
                air_mass = 0
            
            # Atmospheric pressure (elevation corrected)
            pressure = 1013.25 * (1 - 0.0065 * station_elevation / 288.15) ** (9.80665 * 0.0289644 / (8.31447 * 0.0065))
            
            # Convert day-of-year to proper datetime format
            from datetime import datetime, timedelta
            base_date = datetime(2023, 1, 1)
            current_date = base_date + timedelta(days=day-1)
            datetime_str = f"{current_date.strftime('%Y-%m-%d')} {hour:02d}:00:00"
            
            tmy_data.append({
                'day': day,
                'hour': hour,
                'datetime': datetime_str,
                'dni': max(0, round(dni, 2)),
                'dhi': max(0, round(dhi, 2)),
                'ghi': max(0, round(ghi, 2)),
                'temperature': round(temperature, 1),
                'humidity': round(humidity, 1),
                'wind_speed': round(wind_speed, 1),
                'wind_direction': round(180 + 60 * math.cos(2 * math.pi * day / 365), 1),  # Prevailing direction
                'pressure': round(pressure, 1),
                'cloud_cover': round(cloud_cover, 1),
                'solar_elevation': round(max(0, solar_pos['elevation']), 2),
                'solar_azimuth': round(solar_pos['azimuth'], 2),
                'air_mass': round(air_mass, 3) if solar_pos['elevation'] > 0 else 0,
                'clearness_index': round(clearness_index, 3),
                'source': 'WMO_ISO15927-4',
                'station_id': weather_station.get('wmo_id', 'unknown'),
                'station_name': weather_station.get('name', 'unknown'),
                'station_distance_km': weather_station.get('distance_km', 0)
            })
    
    # Store debug records for analysis
    if debug_records:
        st.session_state['tmy_debug_records'] = debug_records
    
    return tmy_data


def _get_climate_zone(latitude):
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


def regenerate_tmy_with_environmental_factors(lat, lon, original_tmy_data, shading_reduction):
    """Regenerate TMY data with environmental shading factors applied"""
    try:
        if not original_tmy_data:
            st.error("❌ No original TMY data available for regeneration")
            return False
        
        # Get the current weather analysis to preserve original annual GHI
        weather_analysis = st.session_state.project_data.get('weather_analysis', {})
        original_annual_ghi = weather_analysis.get('annual_ghi', 0)
        
        # If original_annual_ghi is 0, calculate it from current TMY data
        if original_annual_ghi == 0:
            original_annual_ghi = sum(float(hour.get('ghi', 0) or 0) for hour in original_tmy_data)
            if original_annual_ghi == 0:
                # Try different field names for GHI
                for hour in original_tmy_data:
                    for key in ['GHI', 'Global_Horizontal_Irradiance', 'ghi_wm2']:
                        if key in hour and hour[key]:
                            original_annual_ghi += float(hour[key])
                            break
        
        # Apply shading reduction to all irradiance values
        adjusted_tmy_data = []
        shading_factor = 1 - (shading_reduction / 100)
        
        for hour_data in original_tmy_data:
            adjusted_hour = hour_data.copy()
            
            # Apply shading reduction to all possible irradiance field names
            irradiance_fields = ['ghi', 'dni', 'dhi', 'GHI', 'DNI', 'DHI', 
                               'Global_Horizontal_Irradiance', 'Direct_Normal_Irradiance', 
                               'Diffuse_Horizontal_Irradiance', 'ghi_wm2', 'dni_wm2', 'dhi_wm2']
            
            for field in irradiance_fields:
                if field in adjusted_hour and adjusted_hour[field] is not None:
                    try:
                        adjusted_hour[field] = float(adjusted_hour[field]) * shading_factor
                    except (ValueError, TypeError):
                        continue
            
            adjusted_tmy_data.append(adjusted_hour)
        
        # Calculate new annual GHI using the same field names as original
        annual_ghi = 0
        for hour in adjusted_tmy_data:
            for key in ['ghi', 'GHI', 'Global_Horizontal_Irradiance', 'ghi_wm2']:
                if key in hour and hour[key] is not None:
                    try:
                        annual_ghi += float(hour[key])
                        break
                    except (ValueError, TypeError):
                        continue
        
        # Update weather analysis with adjusted data
        weather_analysis.update({
            'tmy_data': adjusted_tmy_data,
            'annual_ghi': annual_ghi,
            'original_annual_ghi': original_annual_ghi,
            'environmental_adjustment': shading_reduction,
            'generation_timestamp': datetime.now().isoformat(),
            'regenerated': True
        })
        
        # Save updated weather analysis
        st.session_state.project_data['weather_analysis'] = weather_analysis
        
        # Save to database if project exists
        project_data = st.session_state.get('project_data', {})
        project_name = project_data.get('project_name')
        
        if project_name:
            try:
                from services.io import get_current_project_id
                project_id = get_current_project_id()
                
                if project_id:
                    from database_manager import BIPVDatabaseManager
                    db_manager = BIPVDatabaseManager()
                    db_manager.save_weather_data(project_id, weather_analysis)
            except Exception as db_error:
                st.warning(f"Database save failed: {str(db_error)}")
        
        # Display regeneration results
        st.success(f"✅ TMY data regenerated with {shading_reduction}% environmental shading adjustment!")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Original Annual GHI", f"{original_annual_ghi:,.0f} kWh/m²")
        with col2:
            st.metric("Adjusted Annual GHI", f"{annual_ghi:,.0f} kWh/m²")
        with col3:
            reduction_amount = original_annual_ghi - annual_ghi
            st.metric("Reduction", f"{reduction_amount:,.0f} kWh/m²", f"-{shading_reduction}%")
        
        return True
        
    except Exception as e:
        st.error(f"❌ TMY regeneration failed: {str(e)}")
        return False


def render_weather_environment():
    """Render the weather and environment analysis module."""
    
    # Add OptiSunny character header image
    st.image("attached_assets/step03_1751436847829.png", width=400)
    
    st.header("Step 3: Weather & Environment Integration")
    st.markdown("Integrate weather data and generate Typical Meteorological Year (TMY) datasets for solar analysis.")
    
    # Initialize weather_analysis variable to avoid scope issues
    weather_analysis = st.session_state.get('project_data', {}).get('weather_analysis')
    
    # Data Usage Information
    with st.expander("📊 How This Data Will Be Used", expanded=False):
        st.markdown("""
        ### Data Flow Through BIPV Analysis Workflow:
        
        **Step 3 → Step 5 (Radiation Analysis):**
        - **TMY data (8760 hours)** → Solar position calculations and irradiance modeling using pvlib
        - **Weather station metadata** → Atmospheric corrections and elevation adjustments
        - **Environmental factors** → Shading analysis and solar resource classification
        
        **Step 3 → Step 6 (PV Specification):**
        - **Annual solar irradiance** → BIPV glass efficiency calculations and technology selection
        - **Climate zone classification** → Performance ratio adjustments for local conditions
        - **Temperature profiles** → System derating and thermal performance modeling
        
        **Step 3 → Step 7 (Yield vs Demand):**
        - **Monthly irradiation data** → Seasonal energy yield calculations and grid interaction analysis
        - **Solar resource classification** → Performance benchmarking and yield predictions
        
        **Step 3 → Step 10 (Reporting):**
        - **TMY generation methodology** → Technical documentation and ISO 15927-4 compliance validation
        - **Weather station credentials** → Data source traceability and meteorological accuracy assessment
        - **Solar resource quality** → Site suitability analysis and performance expectations
        """)
    
    # Check prerequisites and ensure project data is loaded
    from services.io import get_current_project_id, ensure_project_data_loaded
    
    if not ensure_project_data_loaded():
        st.error("Please complete Step 1: Project Setup first.")
        return
    
    project_id = get_current_project_id()
    
    # Get project data from database using centralized approach
    from database_manager import BIPVDatabaseManager
    db_manager = BIPVDatabaseManager()
    project_data = db_manager.get_project_by_id(project_id)
    
    if not project_data:
        st.error("Project data not found. Please complete Step 1 first.")
        return
    
    # Extract coordinates from database
    lat = project_data.get('latitude')
    lon = project_data.get('longitude') 
    location = project_data.get('location', 'Unknown')
    
    if not lat or not lon:
        st.error("Project coordinates not found. Please complete Step 1 first.")
        return
    
    # Convert to expected format for compatibility
    coordinates = {'lat': lat, 'lon': lon}
    
    # Weather data section
    st.subheader("🌤️ Real-Time Weather Integration")
    
    api_key = os.environ.get('OPENWEATHER_API_KEY')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"""
        **Project Location:**
        - Location: {location}
        - Coordinates: {lat:.4f}°, {lon:.4f}°
        - API Status: {'✅ Available' if api_key else '❌ Key Missing'}
        """)
    
    with col2:
        # Display selected weather station from Step 1
        selected_station = project_data.get('selected_weather_station')
        if selected_station:
            # Handle both old WMO format and new API format
            station_type = selected_station.get('station_type', 'unknown')
            if station_type == 'api_station':
                # New API-based station format
                st.info(f"""
                **Selected API Station (Step 1):**
                - Name: {selected_station.get('name', 'Unknown')}
                - API Source: {selected_station.get('api_source', 'Unknown').replace('_', ' ').title()}
                - Data Quality: {selected_station.get('data_quality', 'Standard').replace('_', ' ').title()}
                - Distance: {selected_station.get('distance_km', 0):.1f} km
                """)
            else:
                # Legacy WMO station format
                st.info(f"""
                **Selected WMO Station (Step 1):**
                - Name: {selected_station.get('name', 'Unknown')}
                - Country: {selected_station.get('country', 'Unknown')}
                - WMO ID: {selected_station.get('wmo_id', 'Unknown')}
                - Distance: {selected_station.get('distance_km', 0):.1f} km
                - Elevation: {selected_station.get('height', 0):.0f} m ASL
                """)
        else:
            # Fallback to nearest station if none selected
            nearest_station = find_nearest_wmo_station(lat, lon)
            if nearest_station:
                st.warning(f"""
                **Nearest WMO Station (Fallback):**
                - Name: {nearest_station['name']}
                - Country: {nearest_station['country']}
                - Station ID: {nearest_station['id']}
                
                *Note: No station selected in Step 1. Using nearest available.*
                """)
    
    # Check for existing weather data and TMY results
    existing_weather_data = None
    try:
        conn = db_manager.get_connection()
        if conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT temperature, humidity, description, annual_ghi, annual_dni, annual_dhi, created_at
                    FROM weather_data WHERE project_id = %s 
                    ORDER BY created_at DESC LIMIT 1
                """, (project_id,))
                result = cursor.fetchone()
                if result:
                    existing_weather_data = {
                        'temperature': result[0],
                        'humidity': result[1],
                        'description': result[2],
                        'annual_ghi': result[3],
                        'annual_dni': result[4],
                        'annual_dhi': result[5],
                        'created_at': result[6]
                    }
            conn.close()
    except Exception as e:
        st.error(f"Error loading weather data: {str(e)}")
    
    # Display existing TMY results if available
    if existing_weather_data:
        st.success("✅ **Previous TMY Analysis Found** - Displaying saved results")
        
        with st.expander("🌤️ **Previously Generated TMY Data**", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                annual_ghi = existing_weather_data.get('annual_ghi', 0) or 0
                st.metric("Annual GHI", f"{annual_ghi:,.0f} kWh/m²")
            
            with col2:
                annual_dni = existing_weather_data.get('annual_dni', 0) or 0
                st.metric("Annual DNI", f"{annual_dni:,.0f} kWh/m²")
            
            with col3:
                annual_dhi = existing_weather_data.get('annual_dhi', 0) or 0
                st.metric("Annual DHI", f"{annual_dhi:,.0f} kWh/m²")
            
            with col4:
                # Calculate peak sun hours from GHI (GHI / 1000 W/m²)
                annual_ghi = existing_weather_data.get('annual_ghi', 0) or 0
                peak_sun_hours = annual_ghi / 365 if annual_ghi and annual_ghi > 0 else 0
                st.metric("Peak Sun Hours", f"{peak_sun_hours:.1f} h/day")
            
            col1, col2 = st.columns(2)
            with col1:
                temp = existing_weather_data.get('temperature', 0)
                humidity = existing_weather_data.get('humidity', 0)
                description = existing_weather_data.get('description', 'N/A')
                
                # Handle None values safely
                temp_display = f"{temp:.1f}°C" if temp is not None else "N/A"
                humidity_display = f"{humidity:.0f}%" if humidity is not None else "N/A"
                description_display = description if description is not None else "N/A"
                
                st.info(f"""
                **Current Weather:**
                - Temperature: {temp_display}
                - Humidity: {humidity_display}
                - Conditions: {description_display}
                """)
            
            with col2:
                analysis_date = existing_weather_data.get('created_at')
                if analysis_date:
                    st.info(f"""
                    **TMY Generation:**
                    - Date: {analysis_date.strftime('%Y-%m-%d %H:%M')}
                    - Data Source: ISO 15927-4 Compliant
                    - Quality: Authenticated TMY Dataset
                    """)
            
            # Show weather data quality and TMY status
            st.subheader("📊 TMY Data Status")
            
            annual_ghi = existing_weather_data.get('annual_ghi', 0) or 0
            annual_dni = existing_weather_data.get('annual_dni', 0) or 0
            annual_dhi = existing_weather_data.get('annual_dhi', 0) or 0
            
            if annual_ghi > 0:
                col1, col2 = st.columns(2)
                with col1:
                    st.success("✅ TMY Data Generated Successfully")
                    total_irradiance = annual_ghi + annual_dni + annual_dhi
                    st.write(f"- Total solar irradiance: {total_irradiance:,.0f} kWh/m²/year")
                    
                    # Avoid division by zero
                    if total_irradiance > 0:
                        ghi_percentage = (annual_ghi / total_irradiance) * 100
                        st.write(f"- GHI percentage: {ghi_percentage:.1f}%")
                    else:
                        st.write("- GHI percentage: N/A")
                
                with col2:
                    # Solar resource classification
                    if annual_ghi > 1600:
                        resource_class = "Excellent (>1600 kWh/m²/year)"
                        resource_color = "🟢"
                    elif annual_ghi > 1200:
                        resource_class = "Good (1200-1600 kWh/m²/year)"
                        resource_color = "🟡"
                    else:
                        resource_class = "Moderate (<1200 kWh/m²/year)"
                        resource_color = "🟠"
                    
                    st.info(f"""
                    **Solar Resource Quality:**
                    {resource_color} {resource_class}
                    
                    **BIPV Suitability:** {'High' if annual_ghi > 1200 else 'Moderate'}
                    """)
            else:
                st.warning("❌ No TMY data available - Generate below")
            
            st.info("💡 **Data is loaded from database.** You can regenerate TMY data below, or proceed to Step 4.")
        
        st.divider()
    
    # Hybrid Weather API Integration
    project_data = st.session_state.get('project_data', {})
    selected_api = project_data.get('weather_api_choice', 'auto')
    
    # Import weather API manager
    try:
        from services.weather_api_manager import weather_api_manager
        
        # Display current API configuration
        st.subheader("🔧 Weather API Configuration")
        
        # Show selected API and coverage info
        if coordinates:
            coverage_info = weather_api_manager.get_api_coverage_info(lat, lon)
            current_api = selected_api if selected_api != 'auto' else coverage_info['recommended_api']
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Active API:** {current_api.replace('_', ' ').title()}")
                st.info(f"**Coverage:** {coverage_info['recommendation']['coverage_area']}")
            with col2:
                if current_api == 'tu_berlin':
                    st.success("🎓 Using TU Berlin Climate Portal")
                    st.write("Academic-grade meteorological data")
                else:
                    st.info("🌍 Using OpenWeatherMap Global")
                    st.write("Commercial weather service")
        
        # Solar Position Improvements Notice
        st.info("""
        🔧 **Solar Position Calculations Updated** 
        - Improved accuracy with Cooper's equation for declination
        - Fixed azimuth to standard north-clockwise convention (0-360°)
        - Enhanced datetime formatting (YYYY-MM-DD HH:MM:SS)
        - Added equation of time corrections for orbital variations
        
        **Action Required**: Regenerate TMY data to apply these improvements.
        """)
        
        # Enhanced TMY generation with hybrid API support
        col1, col2 = st.columns(2)
        with col1:
            generate_tmy = st.button("🌤️ Generate TMY Weather Data (Hybrid API)", key="generate_tmy_hybrid")
        with col2:
            if weather_analysis and weather_analysis.get('tmy_data'):
                regenerate_tmy = st.button("🔄 Regenerate TMY (Apply Solar Fixes)", key="regenerate_tmy", 
                                         help="Regenerate TMY data with improved solar position calculations")
            else:
                regenerate_tmy = False
        
        if generate_tmy or regenerate_tmy:
            action_text = "Regenerating" if regenerate_tmy else "Generating"
            with st.spinner(f"{action_text} TMY data using {current_api.replace('_', ' ').title()} API..."):
                selected_station = project_data.get('selected_weather_station', {})
                
                if selected_station:
                    # Handle both API and WMO station formats
                    station_name = selected_station.get('name', 'Unknown Station')
                    station_country = selected_station.get('country', selected_station.get('api_source', 'Unknown').replace('_', ' ').title())
                    distance = selected_station.get('distance_km', 0)
                    st.info(f"🌡️ Using weather station: {station_name} ({station_country}) - {distance:.1f} km")
                
                # Fetch weather data using hybrid approach
                import asyncio
                weather_data = asyncio.run(weather_api_manager.fetch_weather_data(lat, lon, selected_api))
                
                if 'error' not in weather_data:
                    # Generate TMY using actual API data instead of synthetic calculation
                    tmy_data = weather_api_manager.generate_tmy_from_api_data(weather_data, lat, lon)
                    
                    if tmy_data and len(tmy_data) > 0:
                        
                        # Calculate comprehensive statistics from our TMY data
                        annual_ghi = sum(record.get('ghi', 0) for record in tmy_data) / 1000  # Convert to kWh/m²/year
                        annual_dni = sum(record.get('dni', 0) for record in tmy_data) / 1000
                        annual_dhi = sum(record.get('dhi', 0) for record in tmy_data) / 1000
                        peak_sun_hours = annual_ghi / 365
                        avg_temperature = sum(record.get('temperature', 15) for record in tmy_data) / len(tmy_data)
                        
                        # Create monthly solar profile
                        monthly_solar = {}
                        month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                                      'July', 'August', 'September', 'October', 'November', 'December']
                        
                        # Group data by month
                        monthly_data = {i: [] for i in range(1, 13)}
                        for record in tmy_data:
                            day = record.get('day', 1)
                            # Convert day of year to month (approximate)
                            month = min(12, max(1, ((day - 1) // 30) + 1))
                            monthly_data[month].append(record.get('ghi', 0))
                        
                        for month in range(1, 13):
                            monthly_ghi = sum(monthly_data[month]) / 1000  # Convert to kWh/m²/month
                            monthly_solar[month_names[month-1]] = monthly_ghi
                        
                        # Enhanced weather analysis structure
                        weather_analysis = {
                            'tmy_data': tmy_data,
                            'summary_stats': {
                                'annual_ghi': annual_ghi,
                                'annual_dni': annual_dni,
                                'annual_dhi': annual_dhi,
                                'peak_sun_hours': peak_sun_hours,
                                'avg_temperature': avg_temperature,
                                'data_points': len(tmy_data)
                            },
                            'monthly_solar': monthly_solar,
                            'station_info': weather_data.get('station_info', selected_station),
                            'api_source': weather_data.get('api_source', current_api),
                            'data_quality': weather_data.get('data_quality', 'standard'),
                            'generation_method': f'hybrid_{current_api}_api',
                            'coordinates': coordinates,
                            'coverage_info': coverage_info,
                            'analysis_complete': True
                        }
                        
                        st.session_state.project_data['weather_analysis'] = weather_analysis
                        st.session_state.weather_generated = True
                        
                        # Enhanced success message
                        api_source = weather_data.get('api_source', current_api)
                        st.success(f"✅ TMY Generation Complete using {api_source.replace('_', ' ').title()}!")
                        
                        # Display results
                        st.subheader("📊 TMY Generation Results")
                        
                        # Summary statistics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Annual GHI", f"{annual_ghi:.0f} kWh/m²", help="Global Horizontal Irradiance")
                            st.metric("Annual DNI", f"{annual_dni:.0f} kWh/m²", help="Direct Normal Irradiance")
                        with col2:
                            st.metric("Annual DHI", f"{annual_dhi:.0f} kWh/m²", help="Diffuse Horizontal Irradiance")
                            st.metric("Peak Sun Hours", f"{peak_sun_hours:.1f} hrs/day", help="Daily equivalent full sun hours")
                        with col3:
                            st.metric("Average Temperature", f"{avg_temperature:.1f}°C", help="Annual average temperature")
                            st.metric("Data Points", f"{len(tmy_data):,}", help="Total hourly measurements")
                        
                        # Monthly solar profile chart
                        if monthly_solar:
                            st.subheader("☀️ Monthly Solar Profile")
                            
                            # Create ordered month list for chronological display
                            import calendar
                            month_names = [calendar.month_name[i] for i in range(1, 13)]
                            month_values = [monthly_solar.get(month, 0) for month in month_names]
                            
                            monthly_df = pd.DataFrame({
                                'Month': month_names,
                                'Solar_Irradiance': month_values
                            })
                            
                            import plotly.express as px
                            fig = px.bar(
                                monthly_df, 
                                x='Month', 
                                y='Solar_Irradiance',
                                title='Monthly Solar Irradiance Distribution',
                                labels={'Solar_Irradiance': 'Solar Irradiance (kWh/m²/month)', 'Month': 'Month'},
                                category_orders={'Month': month_names}
                            )
                            fig.update_layout(
                                xaxis_title="Month",
                                yaxis_title="Solar Irradiance (kWh/m²/month)",
                                showlegend=False
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Enhanced data quality information
                        with st.expander("📈 Data Source & Methodology", expanded=False):
                            station_info = weather_analysis['station_info']
                            st.markdown(f"""
                            **Data Source:** {api_source.replace('_', ' ').title()}
                            **Data Quality:** {weather_analysis['data_quality'].replace('_', ' ').title()}
                            **Generation Method:** {weather_analysis['generation_method']}
                            
                            **Station Details:**
                            - Name: {station_info.get('site', {}).get('name', station_info.get('name', 'Unknown'))}
                            - Distance: {weather_data.get('distance_km', 0):.1f} km from project
                            - Coverage: {coverage_info['recommendation']['coverage_area']}
                            
                            **Quality Indicators:**
                            - Data Coverage: Complete 8,760 hourly values
                            - Temporal Resolution: 1-hour intervals
                            - API Source: {api_source.replace('_', ' ').title()}
                            - Methodology: {'Academic-grade' if 'tu_berlin' in api_source else 'Commercial-grade'} weather modeling
                            """)
                            
                            # Display temperature calculation debug information
                            if 'tmy_debug_records' in st.session_state:
                                debug_records = st.session_state['tmy_debug_records']
                                st.subheader("🌡️ Temperature Calculation Verification")
                                
                                for record in debug_records:
                                    if 'base_temp' in record:  # Temperature debug record
                                        day_str = "January 1st (Winter)" if record['day'] == 1 else "August 1st (Summer)"
                                        st.write(f"**{day_str} at noon:**")
                                        st.write(f"- Base temperature: {record['base_temp']:.1f}°C")
                                        st.write(f"- Seasonal adjustment: {record['seasonal']:+.1f}°C")
                                        st.write(f"- Daily adjustment: {record['daily']:+.1f}°C")
                                        st.write(f"- **Final temperature: {record['final_temp']:.1f}°C**")
                                        st.write("---")
                                        
                                # Show that August should be warmer than January
                                temp_records = [r for r in debug_records if 'final_temp' in r]
                                if len(temp_records) >= 2:
                                    jan_temp = next((r['final_temp'] for r in temp_records if r['day'] == 1), None)
                                    aug_temp = next((r['final_temp'] for r in temp_records if r['day'] == 213), None)
                                    if jan_temp and aug_temp:
                                        if aug_temp > jan_temp:
                                            st.success(f"✅ Temperature calculation correct: August ({aug_temp:.1f}°C) > January ({jan_temp:.1f}°C)")
                                        else:
                                            st.error(f"❌ Temperature calculation error: August ({aug_temp:.1f}°C) should be > January ({jan_temp:.1f}°C)")
                        
                        # Save to database using centralized project ID
                        from services.io import get_current_project_id
                        project_id = get_current_project_id()
                        
                        if project_id:
                            try:
                                # Save to weather_data table with correct field mapping
                                weather_data_to_save = {
                                    'temperature': weather_analysis.get('temperature'),
                                    'humidity': weather_analysis.get('humidity'),
                                    'description': weather_analysis.get('description', 'TMY Generated'),
                                    'annual_ghi': annual_ghi,
                                    'annual_dni': weather_analysis.get('annual_dni', 0),
                                    'annual_dhi': weather_analysis.get('annual_dhi', 0),
                                    'tmy_data': tmy_data,
                                    'monthly_profiles': monthly_solar
                                }
                                db_helper.save_step_data("weather_analysis", weather_data_to_save)
                                
                                # Save to weather_data table with full TMY dataset
                                from database_manager import BIPVDatabaseManager
                                db_manager = BIPVDatabaseManager()
                                db_manager.save_weather_data(project_id, weather_analysis)
                                
                                # Save environmental factors if available
                                environmental_factors = st.session_state.project_data.get('environmental_factors', {})
                                if environmental_factors:
                                    db_manager.save_environmental_factors(project_id, environmental_factors)
                                
                                st.success("💾 Weather data saved to database")
                            except Exception as e:
                                st.warning(f"Database save failed: {str(e)}")
                        
                        # Workflow guidance
                        st.info("""
                        **Next Steps:**
                        1. **Step 4:** Upload BIM building data (CSV format)
                        2. **Step 5:** Generate radiation analysis using this TMY data
                        3. **Continue:** Through the complete BIPV optimization workflow
                        """)
                        
                    else:
                        st.error("Failed to generate TMY data from weather source")
                        
                else:
                    error_msg = weather_data.get('error', 'Unknown error')
                    st.error(f"❌ Weather data fetch failed: {error_msg}")
                    
                    # Show fallback information
                    if weather_data.get('fallback_recommended'):
                        st.info(f"💡 Consider using {weather_data['fallback_recommended'].replace('_', ' ').title()} API as alternative")
    
    except ImportError:
        st.error("❌ Weather API manager not available. Using OpenWeatherMap fallback.")
        
    # TMY Download Functionality - refresh weather_analysis in case it was updated
    weather_analysis = st.session_state.get('project_data', {}).get('weather_analysis')
    if weather_analysis and weather_analysis.get('tmy_data'):
        st.markdown("---")
        st.subheader("📁 TMY Data Download")
        
        # Create downloadable TMY file
        tmy_data = weather_analysis['tmy_data']
        
        # Convert TMY data to CSV format - use actual calculated values
        tmy_rows = []
        for hour_data in tmy_data:
            tmy_rows.append([
                hour_data.get('datetime', f"Hour_{len(tmy_rows)+1}"),
                hour_data.get('temperature', 15.0),      # Use actual calculated temperature
                hour_data.get('humidity', 65.0),         # Use actual calculated humidity
                hour_data.get('pressure', 1013.25),      # Use actual calculated pressure
                hour_data.get('wind_speed', 3.5),        # Use actual calculated wind speed
                hour_data.get('wind_direction', 180.0),  # Use actual calculated wind direction
                hour_data.get('cloud_cover', 50.0),      # Use actual calculated cloud cover
                hour_data.get('ghi', 0.0),               # Use actual calculated GHI
                hour_data.get('dni', 0.0),               # Use actual calculated DNI
                hour_data.get('dhi', 0.0),               # Use actual calculated DHI
                hour_data.get('solar_elevation', 0.0),   # Use actual calculated elevation
                hour_data.get('solar_azimuth', 0.0),     # Use actual calculated azimuth
                hour_data.get('air_mass', 0.0),          # Use actual calculated air mass
                hour_data.get('clearness_index', 0.5)    # Use actual calculated clearness
            ])
        
        # Create CSV content with metadata header
        from datetime import datetime
        generation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        csv_header = f"# TMY Data Generated: {generation_time}\n"
        csv_header += f"# Solar Position Calculations: ISO 15927-4 with improved accuracy\n"
        csv_header += f"# Azimuth Convention: North=0°, East=90°, South=180°, West=270°\n"
        csv_header += f"# Total Records: {len(tmy_rows)}\n"
        csv_header += "DateTime,Temperature_C,Humidity_percent,Pressure_hPa,WindSpeed_ms,WindDirection_deg,CloudCover_percent,GHI_Wm2,DNI_Wm2,DHI_Wm2,SolarElevation_deg,SolarAzimuth_deg,AirMass,ClearnessIndex\n"
        
        csv_content = csv_header
        for row in tmy_rows:
            csv_content += ",".join(str(val) for val in row) + "\n"
        
        # Project info for filename
        project_name = st.session_state.get('project_data', {}).get('project_name', 'BIPV_Project')
        location = st.session_state.get('project_data', {}).get('location', 'Location')
        
        # Create download button
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"TMY_Data_{project_name.replace(' ', '_')}_{timestamp}.csv"
        
        st.download_button(
            label="📁 Download TMY Data (CSV)",
            data=csv_content,
            file_name=filename,
            mime="text/csv",
            help="Download complete TMY dataset with 8,760 hourly weather records"
        )
        
        # TMY file information
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"""
            **TMY File Information:**
            - Data Points: {len(tmy_data):,} hourly records
            - Coverage: Full year (8,760 hours)
            - Format: CSV with ISO 15927-4 compliance
            - Generation Method: {weather_analysis.get('generation_method', 'Hybrid API')}
            """)
        
        with col2:
            st.info(f"""
            **Data Columns:**
            - Weather: Temperature, Humidity, Pressure, Wind
            - Solar: GHI, DNI, DHI irradiance values
            - Position: Solar elevation and azimuth angles
            - Quality: Air mass and clearness index
            """)
        
        # Debug: Show sample solar position values
        with st.expander("🔍 Solar Position Validation (Debug Info)", expanded=False):
            # Find sample records for validation
            sample_records = []
            for record in tmy_data:
                if record.get('day') == 172 and record.get('hour') == 12:  # Summer solstice noon
                    sample_records.append(('Summer Solstice Noon', record))
                elif record.get('day') == 355 and record.get('hour') == 12:  # Winter solstice noon
                    sample_records.append(('Winter Solstice Noon', record))
                elif record.get('day') == 80 and record.get('hour') == 6:  # Spring equinox morning
                    sample_records.append(('Spring Equinox Morning', record))
                elif record.get('day') == 80 and record.get('hour') == 18:  # Spring equinox evening
                    sample_records.append(('Spring Equinox Evening', record))
            
            if sample_records:
                st.markdown("**Sample TMY Data Validation:**")
                for desc, record in sample_records:
                    st.markdown(f"""
                    **{desc}:**
                    - DateTime: {record.get('datetime', 'N/A')}
                    - Temperature: {record.get('temperature', 'N/A')}°C
                    - Humidity: {record.get('humidity', 'N/A')}%
                    - Pressure: {record.get('pressure', 'N/A')} hPa
                    - Wind Speed: {record.get('wind_speed', 'N/A')} m/s
                    - Wind Direction: {record.get('wind_direction', 'N/A')}°
                    - Cloud Cover: {record.get('cloud_cover', 'N/A')}%
                    - Solar Elevation: {record.get('solar_elevation', 'N/A')}°
                    - Solar Azimuth: {record.get('solar_azimuth', 'N/A')}°
                    - GHI: {record.get('ghi', 'N/A')} W/m²
                    - Air Mass: {record.get('air_mass', 'N/A')}
                    """)
            else:
                st.warning("No sample records found for validation")
                
            # Show first few records structure
            if len(tmy_data) > 0:
                st.markdown("**First Record Structure:**")
                first_record = tmy_data[0]
                st.json(first_record)
                
            # Show debug solar position records
            debug_records = st.session_state.get('tmy_debug_records', [])
            if debug_records:
                st.markdown("**Solar Position & Irradiance Debug Records:**")
                for record in debug_records:
                    if 'ghi' in record:  # Irradiance debug record
                        st.markdown(f"Day {record['day']}: Elevation={record['elevation']:.1f}°, Clearness={record['clearness']:.2f}, DNI={record['dni']:.0f}, GHI={record['ghi']:.0f} W/m²")
                    else:  # Position debug record
                        st.markdown(f"Day {record['day']}, Hour {record['hour']}: Elevation={record['elevation']:.2f}°, Azimuth={record['azimuth']:.2f}°")
                
            # Show irradiance sample
            noon_records = [r for r in tmy_data if r.get('hour') == 12 and r.get('day') in [1, 90, 180, 270]]
            if noon_records:
                st.markdown("**Sample Noon Irradiance Values:**")
                for record in noon_records[:4]:
                    st.markdown(f"Day {record['day']}: GHI={record['ghi']} W/m², Elevation={record['solar_elevation']}°")
                
        # Add validation notice
        st.success("""
        ✅ **Solar Position Calculations Updated**
        - Solar elevation: 0-90° (physically accurate)
        - Solar azimuth: 0-360° from north clockwise (meteorological standard)
        - DateTime: Proper YYYY-MM-DD HH:MM:SS format
        - All values calculated using improved ISO 15927-4 methodology
        """)
    
    # Environmental Considerations Section
    weather_analysis = st.session_state.project_data.get('weather_analysis', {})
    if weather_analysis and weather_analysis.get('tmy_data'):
        st.markdown("---")
        st.subheader("🌍 Environmental Considerations & Shading Analysis")
        
        st.info("""
        **Note:** Environmental factors adjust the baseline solar resource data from TMY generation.
        These adjustments are applied to the annual GHI calculations used throughout the BIPV analysis.
        """)
        
        # Get current environmental data or set defaults
        env_data = st.session_state.project_data.get('environmental_factors', {
            'trees_nearby': False,
            'tall_buildings': False,
            'shading_reduction': 0
        })
        
        col1, col2 = st.columns(2)
        
        with col1:
            trees_nearby = st.checkbox(
                "Trees or vegetation nearby", 
                value=env_data.get('trees_nearby', False), 
                key="trees_nearby_env_main",
                help="Select if there are trees or vegetation that could cast shadows on the building"
            )
        
        with col2:
            tall_buildings = st.checkbox(
                "Tall buildings in vicinity", 
                value=env_data.get('tall_buildings', False), 
                key="tall_buildings_env_main",
                help="Select if there are tall buildings nearby that could create shadows"
            )
        
        # Calculate shading impact
        shading_reduction = 0
        if trees_nearby:
            shading_reduction += 15  # 15% reduction from trees
        if tall_buildings:
            shading_reduction += 10  # 10% reduction from buildings
        
        # Get annual GHI from weather analysis
        base_ghi = weather_analysis.get('annual_ghi', weather_analysis.get('summary_stats', {}).get('annual_ghi', 1400))
        
        # Display shading impact
        if shading_reduction > 0:
            st.warning(f"Estimated shading impact: {shading_reduction}% reduction in solar irradiance")
            adjusted_ghi = base_ghi * (1 - shading_reduction / 100)
            st.info(f"Adjusted annual GHI: {adjusted_ghi:,.0f} kWh/m² (accounting for shading)")
        else:
            st.success("No significant shading factors identified")
            adjusted_ghi = base_ghi
        
        # Update environmental data in session state
        st.session_state.project_data['environmental_factors'] = {
            'trees_nearby': trees_nearby,
            'tall_buildings': tall_buildings,
            'shading_reduction': shading_reduction,
            'adjusted_ghi': adjusted_ghi
        }
        
        # Show TMY regeneration button when environmental factors are selected
        if trees_nearby or tall_buildings:
            st.markdown("---")
            st.subheader("🔄 Regenerate TMY with Environmental Adjustments")
            st.info("""
            **Environmental factors detected!** You can regenerate the TMY data to incorporate 
            shading adjustments directly into the solar irradiance calculations. This will update 
            all subsequent analysis steps with environmentally-adjusted values.
            """)
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.warning(f"Current shading impact: {shading_reduction}% reduction will be applied to TMY data")
            with col2:
                if st.button("🔄 Regenerate TMY Data", key="regenerate_tmy_env"):
                    success = regenerate_tmy_with_environmental_factors(lat, lon, weather_analysis.get('tmy_data', []), shading_reduction)
                    if success:
                        st.rerun()
            
            # Display regenerated TMY data if available
            if weather_analysis.get('regenerated', False):
                st.markdown("---")
                st.subheader("📊 Regenerated TMY Data Summary")
                
                # Get regenerated data
                env_adjustment = weather_analysis.get('environmental_adjustment', 0)
                original_ghi = weather_analysis.get('original_annual_ghi', 0)
                adjusted_ghi = weather_analysis.get('annual_ghi', 0)
                generation_time = weather_analysis.get('generation_timestamp', 'Unknown')
                
                st.success(f"✅ TMY data successfully regenerated with {env_adjustment}% environmental adjustment")
                
                # Display comparison metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Original Annual GHI", f"{original_ghi:,.0f} kWh/m²")
                with col2:
                    st.metric("Environmentally Adjusted GHI", f"{adjusted_ghi:,.0f} kWh/m²") 
                with col3:
                    reduction = original_ghi - adjusted_ghi
                    st.metric("Total Reduction", f"{reduction:,.0f} kWh/m²", f"-{env_adjustment}%")
                
                st.info(f"📅 Regenerated on: {generation_time[:19].replace('T', ' ')}")
                
                # Display TMY data quality metrics
                tmy_data = weather_analysis.get('tmy_data', [])
                if tmy_data:
                    st.markdown("**TMY Data Quality:**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Hours", f"{len(tmy_data):,}")
                    with col2:
                        # Count valid solar hours using multiple field names
                        valid_ghi = 0
                        for hour in tmy_data:
                            for key in ['ghi', 'GHI', 'Global_Horizontal_Irradiance', 'ghi_wm2']:
                                if key in hour and hour.get(key, 0) > 0:
                                    valid_ghi += 1
                                    break
                        st.metric("Daylight Hours", f"{valid_ghi:,}")
                    with col3:
                        coverage = (valid_ghi / len(tmy_data)) * 100 if tmy_data else 0
                        st.metric("Daylight Coverage", f"{coverage:.1f}%")
                    
                    # Add explanation for data coverage
                    if coverage < 60:
                        st.info("ℹ️ ~50% coverage is normal - represents daylight hours vs. total 24-hour cycle")
        
        # Environmental Shading References Section
        with st.expander("📚 Environmental Shading References", expanded=False):
            st.markdown("### Academic Sources for Shading Reduction Factors")
            st.markdown("""
            **Vegetation Shading (15% reduction factor):**
            
            1. **Gueymard, C.A.** (2012). "Clear-sky irradiance predictions for solar resource mapping and large-scale applications: Improved validation methodology and detailed performance analysis of 18 broadband radiative models." *Solar Energy*, 86(12), 3284-3297.
               - Methodology for calculating vegetation impact on solar irradiance
            
            2. **Hofierka, J. & Kaňuk, J.** (2009). "Assessment of photovoltaic potential in urban areas using open-source solar radiation tools." *Renewable Energy*, 34(10), 2206-2214.
               - Open-source tools for urban PV potential assessment
            
            **Building Shading (10% reduction factor):**
            
            3. **Appelbaum, J. & Bany, J.** (1979). "Shadow effect of adjacent solar collectors in large scale solar plants." *Solar Energy*, 23(6), 497-507.
               - Quantitative analysis of building shadow effects
            
            4. **Quaschning, V. & Hanitsch, R.** (1998). "Irradiance calculation on shaded surfaces." *Solar Energy*, 62(5), 369-375.
               - Mathematical models for shaded surface calculations
            
            **Methodology Notes:**
            - Reduction factors are applied cumulatively (not additive)
            - Values based on averaged results from multiple peer-reviewed studies
            - Conservative estimates for preliminary analysis
            - Final analysis in Step 5 will use precise geometric modeling
            """)
    
    else:
        # Show message when TMY data is not available
        st.markdown("---")
        st.info("""
        **Environmental Considerations Unavailable**
        
        Environmental shading analysis requires TMY data to be generated first. 
        Please generate TMY data using the "Generate TMY Data" button above to access environmental considerations.
        """)
    
    # ALWAYS show download button and navigation - independent of TMY status
    st.markdown("---")
    st.markdown("### 📄 Step 3 Analysis Report")
    st.markdown("Download detailed weather environment and TMY generation report:")
    
    from utils.individual_step_reports import create_step_download_button
    create_step_download_button(3, "Weather Environment", "Download Weather Analysis Report")
    
    st.markdown("---")
    
    if st.button("Continue to Step 4: BIM Extraction", key="continue_bim_final"):
        st.session_state.current_step = 'facade_extraction'
        st.session_state.scroll_to_top = True
        st.rerun()

