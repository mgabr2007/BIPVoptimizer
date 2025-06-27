"""
Project Setup page for BIPV Optimizer
Enhanced with weather station selection interface
"""
import streamlit as st
import os
import folium
from streamlit_folium import st_folium
import pandas as pd
from core.solar_math import get_location_solar_parameters, get_location_electricity_rates, determine_timezone_from_coordinates, get_currency_symbol
from services.io import get_weather_data_from_coordinates, save_project_data
from services.weather_stations import find_nearest_stations, get_station_summary, format_station_display


def render_project_setup():
    """Render the project setup module with configuration inputs."""
    st.header("Step 1: Project Setup & Configuration")
    st.markdown("Configure your BIPV optimization project parameters and location settings.")
    
    # Project basic information
    st.subheader("Project Information")
    
    col1, col2 = st.columns(2)
    with col1:
        project_name = st.text_input(
            "Project Name",
            value="BIPV Optimization Project",
            help="📝 Enter a descriptive name for your BIPV analysis project. This name will be used for database storage and report generation. Examples: 'University Main Building BIPV', 'Office Complex Solar Integration'",
            key="project_name_input"
        )
    
    with col2:
        # Auto-set currency to EUR (standardized)
        currency = "EUR"
        st.text_input(
            "Currency (Fixed)",
            value="EUR",
            disabled=True,
            help="💰 All financial calculations are standardized to EUR (Euros). Exchange rates from local currencies are automatically applied using current market rates. This ensures consistent economic analysis across different regions.",
            key="currency_display"
        )
    
    # Enhanced location selection with weather station integration
    st.subheader("📍 Enhanced Location Selection")
    st.markdown("Select your project location and choose the nearest weather station for accurate meteorological data.")
    
    # Initialize map with default coordinates (Berlin)
    if 'map_coordinates' not in st.session_state:
        st.session_state.map_coordinates = {'lat': 52.5200, 'lng': 13.4050}
    
    # Location selection method
    col1, col2 = st.columns([2, 1])
    
    with col1:
        location_method = st.radio(
            "Location Selection Method",
            ["Interactive Map", "Manual Coordinates"],
            help="Choose how to specify your project location",
            key="location_method"
        )
    
    with col2:
        search_radius = st.selectbox(
            "Weather Station Search Radius",
            [100, 200, 300, 500, 750, 1000],
            index=3,
            help="Maximum distance to search for weather stations (km)",
            key="search_radius"
        )
    
    # Location input based on selected method
    if location_method == "Manual Coordinates":
        coord_col1, coord_col2 = st.columns(2)
        with coord_col1:
            manual_lat = st.number_input(
                "Latitude",
                min_value=-90.0, max_value=90.0,
                value=st.session_state.map_coordinates['lat'],
                format="%.6f",
                help="Project latitude in decimal degrees",
                key="manual_lat"
            )
        with coord_col2:
            manual_lon = st.number_input(
                "Longitude",
                min_value=-180.0, max_value=180.0,
                value=st.session_state.map_coordinates['lng'],
                format="%.6f",
                help="Project longitude in decimal degrees",
                key="manual_lon"
            )
        
        # Update coordinates from manual input
        st.session_state.map_coordinates = {'lat': manual_lat, 'lng': manual_lon}
    
    # Find nearby weather stations
    nearby_stations = find_nearest_stations(
        st.session_state.map_coordinates['lat'], 
        st.session_state.map_coordinates['lng'], 
        max_distance_km=search_radius
    )
    
    # Create enhanced folium map with weather stations
    m = folium.Map(
        location=[st.session_state.map_coordinates['lat'], st.session_state.map_coordinates['lng']],
        zoom_start=8,
        tiles="OpenStreetMap"
    )
    
    # Add marker for current location
    folium.Marker(
        [st.session_state.map_coordinates['lat'], st.session_state.map_coordinates['lng']],
        popup="Selected Project Location",
        tooltip="Project Location",
        icon=folium.Icon(color="red", icon="building", prefix="fa")
    ).add_to(m)
    
    # Add weather station markers
    if not nearby_stations.empty:
        for idx, station in nearby_stations.iterrows():
            station_info = format_station_display(station)
            folium.Marker(
                location=[station['latitude'], station['longitude']],
                popup=f"""
                <b>{station['name']}</b><br>
                Country: {station['country']}<br>
                WMO ID: {station['wmo_id']}<br>
                Distance: {station['distance_km']:.1f} km<br>
                Elevation: {station['height']:.0f} m
                """,
                tooltip=station_info['full_info'],
                icon=folium.Icon(color="blue", icon="cloud", prefix="fa")
            ).add_to(m)
    
    # Display map and capture clicks
    map_data = None
    if location_method == "Interactive Map":
        map_data = st_folium(m, key="location_map", height=450, width=700)
        # Update coordinates when map is clicked
        if map_data and map_data['last_clicked'] is not None:
            st.session_state.map_coordinates = map_data['last_clicked']
            st.rerun()
    else:
        # Display map without interaction for manual coordinates
        st_folium(m, key="location_map_display", height=450, width=700)
    
    # Display selected coordinates
    selected_lat = st.session_state.map_coordinates['lat']
    selected_lon = st.session_state.map_coordinates['lng']
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Latitude", f"{selected_lat:.4f}°")
    with col2:
        st.metric("Longitude", f"{selected_lon:.4f}°")
    with col3:
        # Auto-determine timezone
        timezone = determine_timezone_from_coordinates(selected_lat, selected_lon)
        st.metric("Timezone", timezone)
    
    # Location name input
    location_name = st.text_input(
        "Location Name",
        value="Berlin, Germany",
        help="🏙️ Enter the city and country name for reference. This helps identify the project location in reports and provides context for solar irradiance and electricity rate calculations. Format: 'City, Country'",
        key="location_name_input"
    )
    
    # Weather data integration
    st.subheader("🌤️ Weather Data Integration")
    
    # Check for OpenWeather API key
    api_key = os.environ.get('OPENWEATHER_API_KEY')
    
    if api_key:
        if st.button("🔄 Fetch Current Weather Data", key="fetch_weather"):
            with st.spinner("Fetching weather data from OpenWeatherMap..."):
                weather_data = get_weather_data_from_coordinates(selected_lat, selected_lon, api_key)
                
                if weather_data and weather_data.get('api_success'):
                    st.success("✅ Weather data retrieved successfully!")
                    
                    # Display current weather
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Temperature", f"{weather_data['temperature']:.1f}°C")
                    with col2:
                        st.metric("Humidity", f"{weather_data['humidity']}%")
                    with col3:
                        st.metric("Wind Speed", f"{weather_data['wind_speed']} m/s")
                    with col4:
                        st.metric("Cloud Cover", f"{weather_data['clouds']}%")
                    
                    st.info(f"Conditions: {weather_data['description'].title()}")
                    
                    # Store weather data
                    st.session_state.project_data = st.session_state.get('project_data', {})
                    st.session_state.project_data['current_weather'] = weather_data
                    st.session_state.project_data['weather_complete'] = True
                    
                else:
                    st.error("❌ Failed to retrieve weather data. Please check your internet connection.")
    else:
        st.warning("⚠️ OpenWeather API key not found. Weather data integration will be limited.")
    
    # Project configuration summary
    st.subheader("📋 Project Configuration Summary")
    
    if st.button("💾 Save Project Configuration", key="save_project", type="primary"):
        # Prepare project data
        project_data = {
            'project_name': project_name,
            'location': location_name,
            'coordinates': {
                'lat': selected_lat,
                'lon': selected_lon
            },
            'timezone': timezone,
            'currency': currency,
            'setup_complete': True
        }
        
        # Get location-specific parameters
        location_params = get_location_solar_parameters(location_name)
        electricity_rates = get_location_electricity_rates(location_name, currency)
        
        # Add calculated parameters
        project_data['solar_parameters'] = location_params
        project_data['electricity_rates'] = electricity_rates
        
        # Store in session state
        st.session_state.project_data = project_data
        
        # Save to database
        project_id = save_project_data(project_data)
        if project_id:
            st.session_state.project_id = project_id
            st.success("✅ Project configuration saved successfully!")
            
            # Display configuration summary
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"""
                **Project Details:**
                - Name: {project_name}
                - Location: {location_name}
                - Coordinates: {selected_lat:.4f}°, {selected_lon:.4f}°
                - Timezone: {timezone}
                - Currency: {get_currency_symbol(currency)} ({currency})
                """)
            
            with col2:
                st.info(f"""
                **Solar Parameters:**
                - Annual GHI: {location_params['ghi']} kWh/m²
                - Clearness Index: {location_params['clearness']:.2f}
                - Temperature Coefficient: {location_params['temp_coeff']:.4f}/°C
                
                **Electricity Rates:**
                - Import Rate: {get_currency_symbol(currency)}{electricity_rates['import_rate']:.3f}/kWh
                - Export Rate: {get_currency_symbol(currency)}{electricity_rates['export_rate']:.3f}/kWh
                """)
            

        else:
            st.error("❌ Failed to save project data to database.")
    
    # Navigation hint
    if st.session_state.get('project_data', {}).get('setup_complete'):
        st.success("✅ Project setup complete! You can now proceed to Step 2: Historical Data Analysis.")