"""
Project Setup page for BIPV Optimizer - Clean Implementation
Database-driven approach with WMO weather station integration
"""
import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import os
from services.io import get_current_project_id
from utils.database_helper import db_helper
from services.weather_stations import find_nearest_stations


def get_location_name(lat, lon):
    """Get location name from coordinates using OpenWeatherMap API"""
    api_key = os.environ.get('OPENWEATHER_API_KEY')
    if not api_key:
        return f"Location at {lat:.4f}°, {lon:.4f}°"
    
    try:
        url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={api_key}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                result = data[0]
                city = result.get('name', '')
                country = result.get('country', '')
                if city and country:
                    return f"{city}, {country}"
        
        return f"Location at {lat:.4f}°, {lon:.4f}°"
    except Exception as e:
        return f"Location at {lat:.4f}°, {lon:.4f}°"


def load_existing_project_data():
    """Load existing project data from database if available"""
    project_id = get_current_project_id()
    if not project_id:
        return None
    
    try:
        project_info = db_helper.db_manager.get_project_info(project_id)
        if project_info:
            return {
                'project_id': project_id,
                'coordinates': {
                    'lat': float(project_info.get('latitude') or 52.5121),
                    'lng': float(project_info.get('longitude') or 13.3270)
                },
                'location_name': project_info.get('location') or 'Berlin, Germany',
                'weather_station': {
                    'name': project_info.get('weather_station_name'),
                    'wmo_id': project_info.get('weather_station_id'),
                    'distance_km': float(project_info.get('weather_station_distance') or 0),
                    'latitude': float(project_info.get('weather_station_latitude') or 52.5121),
                    'longitude': float(project_info.get('weather_station_longitude') or 13.3270),
                    'height': float(project_info.get('weather_station_elevation') or 0)
                } if project_info.get('weather_station_name') else None
            }
    except Exception as e:
        st.warning(f"Could not load existing project data: {str(e)}")
    
    return None


def initialize_session_state():
    """Initialize session state with default or existing values"""
    existing_data = load_existing_project_data()
    
    if existing_data:
        st.session_state.map_coordinates = existing_data['coordinates']
        st.session_state.location_name = existing_data['location_name']
        if existing_data['weather_station']:
            st.session_state.selected_weather_station = existing_data['weather_station']
        st.success(f"✅ Loaded existing project data (ID: {existing_data['project_id']})")
    else:
        # Default values for new projects
        if 'map_coordinates' not in st.session_state:
            st.session_state.map_coordinates = {'lat': 52.5121, 'lng': 13.3270}
        if 'location_name' not in st.session_state:
            st.session_state.location_name = "Berlin, Germany"


def render_project_info_section():
    """Render project information section"""
    st.subheader("1️⃣ Project Information")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        project_name = st.text_input(
            "Project Name",
            value="BIPV Optimization Project",
            help="Enter a descriptive name for your BIPV analysis project",
            key="project_name_input"
        )
    
    with col2:
        st.text_input(
            "Currency (Fixed)",
            value="EUR",
            disabled=True,
            help="All financial calculations use EUR with automatic exchange rate conversion",
            key="currency_display"
        )
    
    return project_name


def render_location_selection():
    """Render location selection with interactive map"""
    st.subheader("2️⃣ Location Selection")
    
    current_coords = st.session_state.map_coordinates
    
    # Create folium map
    m = folium.Map(
        location=[current_coords['lat'], current_coords['lng']],
        zoom_start=10,
        tiles="OpenStreetMap"
    )
    
    # Add marker for current location
    folium.Marker(
        [current_coords['lat'], current_coords['lng']],
        popup=st.session_state.location_name,
        tooltip="Project Location",
        icon=folium.Icon(color='red', icon='home')
    ).add_to(m)
    
    # Display map
    st.info("📍 Click on the map to select your project location")
    map_data = st_folium(m, key="location_map", height=400, width=700)
    
    # Process map clicks
    if map_data and map_data.get('last_clicked'):
        new_coords = map_data['last_clicked']
        
        # Check if coordinates changed significantly
        lat_diff = abs(new_coords['lat'] - current_coords['lat'])
        lng_diff = abs(new_coords['lng'] - current_coords['lng'])
        
        if lat_diff > 0.001 or lng_diff > 0.001:
            st.session_state.map_coordinates = new_coords
            st.session_state.location_name = get_location_name(new_coords['lat'], new_coords['lng'])
            
            # Clear weather station selection when location changes
            if 'selected_weather_station' in st.session_state:
                del st.session_state.selected_weather_station
            
            st.rerun()
    
    # Display current coordinates
    st.info(f"📍 **Selected Location:** {st.session_state.location_name}")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Latitude:** {current_coords['lat']:.4f}°")
    with col2:
        st.write(f"**Longitude:** {current_coords['lng']:.4f}°")


def render_weather_station_selection():
    """Render WMO weather station selection"""
    st.subheader("3️⃣ Weather Station Selection")
    
    current_coords = st.session_state.map_coordinates
    
    # Search radius selection
    search_radius = st.selectbox(
        "Search Radius for Weather Stations",
        [100, 200, 500, 1000],
        index=1,
        help="Maximum distance to search for WMO weather stations (km)",
        key="search_radius"
    )
    
    # Find weather stations button
    if st.button("🔍 Find Nearest Weather Stations", key="find_stations"):
        with st.spinner("Searching for WMO weather stations..."):
            try:
                stations_df = find_nearest_stations(
                    current_coords['lat'], 
                    current_coords['lng'], 
                    max_distance_km=search_radius
                )
                
                if not stations_df.empty:
                    # Convert DataFrame to list of dictionaries
                    stations_list = stations_df.to_dict('records')
                    st.session_state.available_stations = stations_list
                    st.success(f"Found {len(stations_list)} weather stations within {search_radius} km")
                else:
                    st.warning(f"No weather stations found within {search_radius} km. Try increasing the search radius.")
            except Exception as e:
                st.error(f"Error finding weather stations: {str(e)}")
    
    # Display available stations for selection
    if 'available_stations' in st.session_state and st.session_state.available_stations:
        st.markdown("**Available Weather Stations:**")
        
        station_options = {}
        for station in st.session_state.available_stations:
            display_name = f"{station['name']} (WMO: {station['wmo_id']}) - {station['distance_km']:.1f} km"
            station_options[display_name] = station
        
        selected_station_name = st.selectbox(
            "Select Weather Station",
            options=list(station_options.keys()),
            key="station_selector"
        )
        
        if selected_station_name:
            selected_station = station_options[selected_station_name]
            st.session_state.selected_weather_station = selected_station
            
            # Display station details
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Station Name:** {selected_station['name']}")
                st.write(f"**WMO ID:** {selected_station['wmo_id']}")
                st.write(f"**Distance:** {selected_station['distance_km']:.1f} km")
            with col2:
                st.write(f"**Coordinates:** {selected_station['latitude']:.4f}°, {selected_station['longitude']:.4f}°")
                st.write(f"**Elevation:** {selected_station['height']:.0f} m")
                st.write(f"**Country:** {selected_station.get('country', 'Unknown')}")
    
    # Show currently selected station
    if 'selected_weather_station' in st.session_state:
        station = st.session_state.selected_weather_station
        st.success(f"✅ Selected: {station['name']} (WMO: {station['wmo_id']})")


def save_project_configuration(project_name):
    """Save project configuration to database"""
    try:
        # Get current coordinates and weather station
        coords = st.session_state.map_coordinates
        location_name = st.session_state.location_name
        
        # Prepare project data
        project_data = {
            'project_name': project_name,
            'location': location_name,
            'latitude': coords['lat'],
            'longitude': coords['lng'],
            'currency': 'EUR'
        }
        
        # Add weather station data if selected
        if 'selected_weather_station' in st.session_state:
            station = st.session_state.selected_weather_station
            project_data.update({
                'weather_station_name': station['name'],
                'weather_station_id': station['wmo_id'],
                'weather_station_distance': station['distance_km'],
                'weather_station_latitude': station['latitude'],
                'weather_station_longitude': station['longitude'],
                'weather_station_elevation': station['height']
            })
        
        # Save to database
        project_id = db_helper.save_project_data(project_data)
        
        if project_id:
            st.session_state.project_id = project_id
            st.session_state.project_data = project_data
            st.success(f"✅ Project configuration saved successfully (ID: {project_id})")
            return True
        else:
            st.error("❌ Failed to save project configuration to database")
            return False
            
    except Exception as e:
        st.error(f"❌ Error saving project configuration: {str(e)}")
        return False


def render_project_setup():
    """Main function to render the complete project setup page"""
    st.title("🏢 Project Setup")
    st.markdown("Configure your BIPV optimization project with precise location and weather data.")
    
    # Initialize session state
    initialize_session_state()
    
    # Render sections
    project_name = render_project_info_section()
    render_location_selection()
    render_weather_station_selection()
    
    # Configuration summary and save
    st.subheader("4️⃣ Configuration Summary")
    
    # Display current configuration
    coords = st.session_state.map_coordinates
    location = st.session_state.location_name
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Project Configuration:**")
        st.write(f"• Name: {project_name}")
        st.write(f"• Location: {location}")
        st.write(f"• Coordinates: {coords['lat']:.4f}°, {coords['lng']:.4f}°")
        st.write(f"• Currency: EUR")
    
    with col2:
        if 'selected_weather_station' in st.session_state:
            station = st.session_state.selected_weather_station
            st.write("**Weather Station:**")
            st.write(f"• Name: {station['name']}")
            st.write(f"• WMO ID: {station['wmo_id']}")
            st.write(f"• Distance: {station['distance_km']:.1f} km")
        else:
            st.warning("⚠️ No weather station selected")
    
    # Save configuration button
    if st.button("💾 Save Project Configuration", type="primary", key="save_config"):
        if 'selected_weather_station' not in st.session_state:
            st.error("❌ Please select a weather station before saving")
        else:
            if save_project_configuration(project_name):
                st.balloons()
    
    # Navigation
    from components.navigation import render_bottom_navigation
    render_bottom_navigation(current_step=1, total_steps=11)