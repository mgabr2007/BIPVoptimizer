"""
Project Setup page for BIPV Optimizer
"""
import streamlit as st
import os
import folium
from streamlit_folium import st_folium
from core.solar_math import get_location_solar_parameters, get_location_electricity_rates, determine_timezone_from_coordinates, get_currency_symbol
from services.io import get_weather_data_from_coordinates, save_project_data


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
    
    # Interactive map for location selection
    st.subheader("📍 Location Selection")
    st.markdown("Click on the map to select your project location for accurate solar and weather analysis.")
    
    # Initialize map with default coordinates (Berlin)
    if 'map_coordinates' not in st.session_state:
        st.session_state.map_coordinates = {'lat': 52.5200, 'lng': 13.4050}
    
    # Create folium map
    m = folium.Map(
        location=[st.session_state.map_coordinates['lat'], st.session_state.map_coordinates['lng']],
        zoom_start=10,
        tiles="OpenStreetMap"
    )
    
    # Add marker for current location
    folium.Marker(
        [st.session_state.map_coordinates['lat'], st.session_state.map_coordinates['lng']],
        popup="Selected Location",
        tooltip="Project Location",
        icon=folium.Icon(color="red", icon="building", prefix="fa")
    ).add_to(m)
    
    # Display map and capture clicks
    map_data = st_folium(m, key="location_map", height=400, width=700)
    
    # Update coordinates when map is clicked
    if map_data['last_clicked'] is not None:
        st.session_state.map_coordinates = map_data['last_clicked']
        st.rerun()
    
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