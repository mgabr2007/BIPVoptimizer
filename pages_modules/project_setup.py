"""
Project Setup page for BIPV Optimizer - Clean Implementation
Database-driven approach with WMO weather station integration
"""
import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import os
from datetime import datetime
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
                'project_name': project_info.get('project_name') or 'BIPV Optimization Project',
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
        # Force complete coordinate update with proper structure
        st.session_state.map_coordinates = {
            'lat': existing_data['coordinates']['lat'],
            'lng': existing_data['coordinates']['lng']
        }
        st.session_state.location_name = existing_data['location_name']
        st.session_state.project_name = existing_data['project_name']
        
        # Clear any cached coordinate keys to force fresh updates
        if 'last_updated_coord' in st.session_state:
            del st.session_state.last_updated_coord
            
        if existing_data['weather_station']:
            st.session_state.selected_weather_station = existing_data['weather_station']
        st.success(f"✅ Loaded existing project data (ID: {existing_data['project_id']})")
    else:
        # Default values for new projects
        if 'map_coordinates' not in st.session_state:
            st.session_state.map_coordinates = {'lat': 52.5121, 'lng': 13.3270}
        if 'location_name' not in st.session_state:
            st.session_state.location_name = "Berlin, Germany"
        if 'project_name' not in st.session_state:
            st.session_state.project_name = "BIPV Optimization Project"


def render_project_info_section():
    """Render project information section"""
    st.subheader("1️⃣ Project Information")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        project_name = st.text_input(
            "Project Name",
            value=st.session_state.get('project_name', 'BIPV Optimization Project'),
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
    
    # Display map with location-based key to update when coordinates change
    st.info("📍 Click on the map to select your project location")
    
    # Always get fresh coordinates from session state
    current_coords = st.session_state.map_coordinates
    
    # Create unique map key using coordinates with high precision to force recreation
    import time
    if 'map_timestamp' not in st.session_state:
        st.session_state.map_timestamp = int(time.time())
    
    # Use high precision coordinates in key to ensure map recreation on any change
    location_key = f"map_{st.session_state.map_timestamp}_{current_coords['lat']:.6f}_{current_coords['lng']:.6f}"
    
    # Create folium map with current coordinates
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
    
    # Render map component
    map_data = st_folium(
        m, 
        key=location_key, 
        height=400, 
        width=700,
        returned_objects=["last_clicked"]
    )
    
    # Process map clicks with immediate coordinate update
    if map_data and map_data.get('last_clicked'):
        new_coords = map_data['last_clicked']
        
        # Check if coordinates changed significantly
        lat_diff = abs(new_coords['lat'] - current_coords['lat'])
        lng_diff = abs(new_coords['lng'] - current_coords['lng'])
        
        if lat_diff > 0.001 or lng_diff > 0.001:  # Significant movement detected
            # Check if we haven't already processed this exact coordinate
            coord_key = f"{new_coords['lat']:.6f},{new_coords['lng']:.6f}"
            if st.session_state.get('last_updated_coord') != coord_key:
                # Update coordinates immediately with high precision
                st.session_state.map_coordinates = {
                    'lat': new_coords['lat'], 
                    'lng': new_coords['lng']
                }
                
                # Get location name and update session state
                new_location_name = get_location_name(new_coords['lat'], new_coords['lng'])
                st.session_state.location_name = new_location_name
                st.session_state.last_updated_coord = coord_key
                
                # Clear weather station selection when location changes
                if 'selected_weather_station' in st.session_state:
                    del st.session_state.selected_weather_station
                
                # Update database in background (non-blocking)
                from services.io import get_current_project_id
                project_id = get_current_project_id()
                if project_id:
                    try:
                        from database_manager import BIPVDatabaseManager
                        db_manager = BIPVDatabaseManager()
                        conn = db_manager.get_connection()
                        if conn:
                            with conn.cursor() as cursor:
                                cursor.execute(
                                    "UPDATE projects SET location = %s, latitude = %s, longitude = %s WHERE id = %s",
                                    (new_location_name, new_coords['lat'], new_coords['lng'], project_id)
                                )
                            conn.commit()
                            conn.close()
                    except Exception:
                        pass  # Silent fail to avoid UI disruption
                
                # Force complete map recreation with millisecond timestamp
                import time
                st.session_state.map_timestamp = int(time.time() * 1000000)  # Microsecond precision
                
                # Success message with updated coordinates
                st.success(f"📍 Location updated to: {new_coords['lat']:.4f}°, {new_coords['lng']:.4f}°")
                st.rerun()
            else:
                st.info("📍 Location already updated")
        else:
            if lat_diff > 0.0001 or lng_diff > 0.0001:  # Any click detected
                st.info(f"📍 Click too close to current location (moved {max(lat_diff, lng_diff):.4f}°)")
    
    # Display current coordinates (always fresh from session state)
    # Force fresh read of coordinates to ensure synchronization
    display_coords = st.session_state.map_coordinates
    display_location = st.session_state.location_name
    
    # Location info panel with live coordinates
    st.info(f"📍 **Selected Location:** {display_location}")
    
    # Coordinate display with high precision
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Latitude:** {display_coords['lat']:.4f}°")
    with col2:
        st.write(f"**Longitude:** {display_coords['lng']:.4f}°")


def render_weather_api_selection():
    """Render weather API selection section"""
    st.subheader("3️⃣ Weather API Selection")
    
    # Always get fresh coordinates from session state
    current_coords = st.session_state.map_coordinates
    
    # Import weather API manager
    try:
        from services.weather_api_manager import weather_api_manager
        
        # Get API coverage information
        coverage_info = weather_api_manager.get_api_coverage_info(current_coords['lat'], current_coords['lng'])
        
        # Display coverage analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📍 Location Coverage Analysis**")
            st.info(f"**Coordinates:** {coverage_info['location']}")
            
            rec_api = coverage_info['recommended_api']
            rec_details = coverage_info['recommendation']
            
            if rec_api == 'tu_berlin':
                st.success("🎓 **Recommended:** TU Berlin Climate Portal")
                st.write(f"**Coverage:** {rec_details['coverage_area']}")
                st.write(f"**Quality:** {rec_details['coverage_level'].title()}")
            else:
                st.info("🌍 **Recommended:** OpenWeatherMap")
                st.write(f"**Coverage:** {rec_details['coverage_area']}")
        
        with col2:
            st.write("**⚙️ API Selection**")
            
            api_options = {
                'wmo_stations': "🏢 WMO Weather Stations (Nearest)",
                'tu_berlin': "🎓 TU Berlin Climate Portal",
                'openweathermap': "🌍 OpenWeatherMap Global"
            }
            
            selected_api = st.selectbox(
                "Choose Weather Data Source:",
                options=list(api_options.keys()),
                format_func=lambda x: api_options[x],
                index=0,
                key="weather_api_choice"
            )
            
            # Store API selection
            st.session_state.selected_weather_api = selected_api
        
        # API comparison
        with st.expander("📊 Weather Service Comparison", expanded=False):
            comp_col1, comp_col2 = st.columns(2)
            
            with comp_col1:
                st.write("**🎓 TU Berlin Climate Portal**")
                tu_info = coverage_info['coverage_details']['tu_berlin']
                st.write(f"**Available:** {'✅ Yes' if tu_info['available'] else '❌ Outside coverage'}")
                st.write(f"**Quality:** {tu_info['quality']}")
                st.write(f"**Coverage:** {tu_info['coverage']}")
                
                st.write("**Advantages:**")
                for adv in tu_info['advantages']:
                    st.write(f"• {adv}")
            
            with comp_col2:
                st.write("**🌍 OpenWeatherMap Global**")
                ow_info = coverage_info['coverage_details']['openweathermap']
                st.write(f"**Available:** ✅ Yes")
                st.write(f"**Quality:** {ow_info['quality']}")
                st.write(f"**Coverage:** {ow_info['coverage']}")
                
                st.write("**Advantages:**")
                for adv in ow_info['advantages']:
                    st.write(f"• {adv}")
    
    except ImportError:
        st.info("Using WMO weather stations for reliable global coverage.")
        selected_api = 'wmo_stations'
        st.session_state.selected_weather_api = selected_api


def render_weather_station_selection():
    """Render WMO weather station selection"""
    st.subheader("4️⃣ Weather Station Selection")
    
    # Always get fresh coordinates from session state
    current_coords = st.session_state.map_coordinates
    
    # Show current location for weather station search
    st.info(f"🌍 **Searching near:** {st.session_state.location_name}")
    st.write(f"**Coordinates:** {current_coords['lat']:.4f}°, {current_coords['lng']:.4f}°")
    
    # Show selected API
    selected_api = st.session_state.get('selected_weather_api', 'wmo_stations')
    if selected_api != 'wmo_stations':
        st.info(f"🌤️ **Active Weather API:** {selected_api.replace('_', ' ').title()}")
    
    # Search radius selection
    search_radius = st.selectbox(
        "Search Radius for Weather Stations",
        [50, 100, 200, 500, 1000],
        index=1,  # Default to 100km
        help="Maximum distance to search for weather stations (km)",
        key="search_radius"
    )
    
    # Check if coordinates have changed and auto-refresh stations
    coord_key = f"{current_coords['lat']:.4f},{current_coords['lng']:.4f}"
    force_search = (st.session_state.get('last_station_search_coord') != coord_key or 
                   st.session_state.get('force_station_refresh', False))
    
    # Manual refresh button or auto-search on coordinate change
    manual_search = st.button("🔄 Refresh Weather Stations", key="refresh_stations")
    
    if manual_search or force_search:
        with st.spinner("Searching for weather stations..."):
            try:
                selected_api = st.session_state.get('selected_weather_api', 'wmo_stations')
                
                if selected_api in ['tu_berlin', 'openweathermap'] and selected_api != 'wmo_stations':
                    # Load stations from selected weather API
                    try:
                        from services.weather_api_manager import weather_api_manager
                        import asyncio
                        
                        # Determine which API to use
                        if selected_api == 'auto':
                            coverage_info = weather_api_manager.get_api_coverage_info(current_coords['lat'], current_coords['lng'])
                            api_to_use = coverage_info['recommended_api']
                        else:
                            api_to_use = selected_api
                        
                        # Fetch station data from API
                        if api_to_use == 'tu_berlin':
                            station_data = asyncio.run(weather_api_manager.fetch_tu_berlin_weather_data(current_coords['lat'], current_coords['lng']))
                        else:
                            station_data = asyncio.run(weather_api_manager.fetch_openweathermap_data(current_coords['lat'], current_coords['lng']))
                        
                        if 'error' not in station_data:
                            # Convert API station data to standard format
                            api_stations = []
                            
                            if api_to_use == 'tu_berlin':
                                # Handle TU Berlin API format
                                if 'all_nearby_stations' in station_data:
                                    for station_info in station_data['all_nearby_stations']:
                                        station = station_info.get('station_info', {})
                                        site_info = station.get('site', {})
                                        
                                        # Extract coordinates from TU Berlin format
                                        coord_str = station.get('coordinates', '')
                                        station_lat, station_lon = current_coords['lat'], current_coords['lng']
                                        
                                        if coord_str and 'POINT(' in coord_str:
                                            try:
                                                # Parse "POINT(lon lat)" format
                                                coords_part = coord_str.replace('POINT(', '').replace(')', '')
                                                lon_str, lat_str = coords_part.split()
                                                station_lat, station_lon = float(lat_str), float(lon_str)
                                            except:
                                                pass
                                        
                                        api_station = {
                                            'name': site_info.get('name', 'TU Berlin Station'),
                                            'wmo_id': f"TUB_{site_info.get('id', 'unknown')}",
                                            'latitude': station_lat,
                                            'longitude': station_lon,
                                            'height': site_info.get('elevation', 0),
                                            'distance_km': station_info.get('distance_km', 0),
                                            'country': 'Germany'
                                        }
                                        api_stations.append(api_station)
                                elif 'station_info' in station_data:
                                    # Single station format
                                    station = station_data['station_info']
                                    site_info = station.get('site', {})
                                    
                                    api_station = {
                                        'name': site_info.get('name', 'TU Berlin Station'),
                                        'wmo_id': f"TUB_{site_info.get('id', 'unknown')}",
                                        'latitude': current_coords['lat'],  # Use target coordinates as fallback
                                        'longitude': current_coords['lng'],
                                        'height': site_info.get('elevation', 0),
                                        'distance_km': station_data.get('distance_km', 0),
                                        'country': 'Germany'
                                    }
                                    api_stations.append(api_station)
                            else:
                                # Handle OpenWeatherMap API format
                                if 'stations' in station_data:
                                    for station in station_data['stations']:
                                        api_station = {
                                            'name': station.get('name', 'Unknown'),
                                            'wmo_id': station.get('id', 'API'),
                                            'latitude': station.get('lat', current_coords['lat']),
                                            'longitude': station.get('lon', current_coords['lng']),
                                            'height': station.get('elevation', 0),
                                            'distance_km': station.get('distance', 0),
                                            'country': station.get('country', 'Unknown')
                                        }
                                        api_stations.append(api_station)
                            
                            if api_stations:
                                st.session_state.available_stations = api_stations
                                st.success(f"Found {len(api_stations)} stations from {api_to_use.replace('_', ' ').title()}")
                            else:
                                st.warning(f"No stations available from {api_to_use.replace('_', ' ').title()}")
                        else:
                            st.warning(f"API error: {station_data.get('error', 'Unknown error')}")
                            # Fallback to WMO stations
                            st.info("Falling back to WMO weather stations...")
                            raise Exception("API unavailable")
                            
                    except Exception as api_error:
                        # Fallback to WMO stations
                        st.warning(f"Weather API unavailable: {str(api_error)}. Using WMO stations.")
                        stations_df = find_nearest_stations(
                            current_coords['lat'], 
                            current_coords['lng'], 
                            max_distance_km=search_radius
                        )
                        
                        if not stations_df.empty:
                            stations_list = stations_df.to_dict('records')
                            st.session_state.available_stations = stations_list
                            st.session_state.last_station_search_coord = coord_key
                            
                            # Auto-select nearest station for automatic searches or small radius
                            if (force_search and not manual_search) or (search_radius <= 100 and len(stations_list) > 0):
                                nearest_station = stations_list[0]  # First station is nearest
                                st.session_state.selected_weather_station = nearest_station
                                if force_search:
                                    st.success(f"🔄 Location updated - Auto-selected nearest station: {nearest_station['name']} ({nearest_station['distance_km']:.1f} km)")
                                else:
                                    st.success(f"✅ Auto-selected nearest station: {nearest_station['name']} ({nearest_station['distance_km']:.1f} km)")
                            else:
                                st.success(f"Found {len(stations_list)} WMO weather stations within {search_radius} km")
                        else:
                            st.warning(f"No WMO stations found within {search_radius} km.")
                else:
                    # Use WMO stations directly
                    stations_df = find_nearest_stations(
                        current_coords['lat'], 
                        current_coords['lng'], 
                        max_distance_km=search_radius
                    )
                    
                    if not stations_df.empty:
                        stations_list = stations_df.to_dict('records')
                        st.session_state.available_stations = stations_list
                        st.session_state.last_station_search_coord = coord_key
                        
                        # Auto-select nearest station for automatic searches or small radius
                        force_refresh = st.session_state.get('force_station_refresh', False)
                        if (force_search and not manual_search) or (search_radius <= 100 and len(stations_list) > 0) or force_refresh:
                            nearest_station = stations_list[0]  # First station is nearest
                            st.session_state.selected_weather_station = nearest_station
                            if force_refresh:
                                st.success(f"🌍 Updated weather station for new location: {nearest_station['name']} ({nearest_station['distance_km']:.1f} km)")
                                # Clear force refresh flag
                                st.session_state.force_station_refresh = False
                            elif force_search:
                                st.success(f"🔄 Location updated - Auto-selected nearest station: {nearest_station['name']} ({nearest_station['distance_km']:.1f} km)")
                            else:
                                st.success(f"✅ Auto-selected nearest station: {nearest_station['name']} ({nearest_station['distance_km']:.1f} km)")
                        else:
                            st.success(f"Found {len(stations_list)} WMO weather stations within {search_radius} km")
                    else:
                        st.warning(f"No WMO stations found within {search_radius} km. Try increasing the search radius.")
                        
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


def render_electricity_rate_integration():
    """Render electricity rate integration based on location"""
    st.subheader("5️⃣ Data Integration & Configuration")
    
    # Get fresh location information from session state
    coords = st.session_state.map_coordinates
    location_name = st.session_state.location_name
    
    # Show current location for electricity rate search
    st.info(f"🌍 **Rate Integration for:** {location_name}")
    st.write(f"**Coordinates:** {coords['lat']:.4f}°, {coords['lng']:.4f}°")
    
    # Get country code from reverse geocoding with enhanced detection
    try:
        from services.weather_api_manager import get_geocoding_data
        geocoding_data = get_geocoding_data(coords['lat'], coords['lng'])
        country_code = geocoding_data.get('country_code', None)
        
        # If reverse geocoding fails, use coordinate-based detection
        if not country_code:
            raise Exception("No country code from geocoding")
            
    except:
        # Enhanced country detection from coordinates and location name
        lat, lng = coords['lat'], coords['lng']
        location_lower = location_name.lower()
        
        # Coordinate-based country detection for major regions
        if 24 <= lat <= 42 and 25 <= lng <= 35:  # Egypt/Middle East region
            if any(x in location_lower for x in ['egypt', 'cairo', 'suez', 'alexandria']):
                country_code = 'EG'
            elif any(x in location_lower for x in ['saudi', 'riyadh', 'jeddah']):
                country_code = 'SA'
            else:
                country_code = 'EG'  # Default for this region
        elif 6 <= lat <= 37 and 68 <= lng <= 97:  # India region
            country_code = 'IN'
        elif 49 <= lat <= 55 and 14 <= lng <= 24:  # Poland/Czech region
            if any(x in location_lower for x in ['poland', 'polska', 'warsaw', 'krakow', 'poznan']):
                country_code = 'PL'
            elif any(x in location_lower for x in ['czech', 'praha', 'prague', 'brno']):
                country_code = 'CZ'
            else:
                country_code = 'PL'
        elif 47 <= lat <= 55 and 5 <= lng <= 15:  # Central Europe
            if any(x in location_lower for x in ['germany', 'deutschland', 'berlin', 'munich', 'hamburg']):
                country_code = 'DE'
            elif any(x in location_lower for x in ['france', 'paris', 'lyon', 'marseille']):
                country_code = 'FR'
            else:
                country_code = 'DE'
        elif 36 <= lat <= 47 and 6 <= lng <= 18:  # Southern Europe
            if any(x in location_lower for x in ['italy', 'italia', 'rome', 'milan', 'naples']):
                country_code = 'IT'
            elif any(x in location_lower for x in ['spain', 'españa', 'madrid', 'barcelona', 'seville']):
                country_code = 'ES'
            else:
                country_code = 'IT'
        elif 50 <= lat <= 60 and 3 <= lng <= 7:  # UK/Netherlands
            if any(x in location_lower for x in ['united kingdom', 'uk', 'london', 'manchester', 'birmingham']):
                country_code = 'UK'
            elif any(x in location_lower for x in ['netherlands', 'holland', 'amsterdam', 'rotterdam']):
                country_code = 'NL'
            else:
                country_code = 'UK'
        else:
            # Fallback to location name detection
            if any(x in location_lower for x in ['germany', 'deutschland']):
                country_code = 'DE'
            elif any(x in location_lower for x in ['egypt', 'cairo', 'suez']):
                country_code = 'EG'
            elif any(x in location_lower for x in ['india', 'delhi', 'mumbai']):
                country_code = 'IN'
            else:
                country_code = 'XX'  # Unknown country
    
    # Show detected country
    st.write(f"**🏴 Detected Country:** {country_code}")
    
    # Check if location has changed and auto-refresh rates
    coord_key = f"{coords['lat']:.4f},{coords['lng']:.4f}"
    location_changed = st.session_state.get('last_rate_search_coord') != coord_key
    force_rates_refresh = st.session_state.get('force_rates_refresh', False)
    
    st.write("**🔌 Live Electricity Rate Integration**")
    
    # Auto-fetch or manual refresh
    if location_changed or force_rates_refresh:
        if force_rates_refresh:
            st.info("🌍 Country changed - Click to fetch rates for new location")
        else:
            st.info("🔄 Location changed - Click to fetch rates for new location")
    
    # Fetch live electricity rates
    if st.button("🔄 Fetch Live Electricity Rates", key="fetch_rates") or location_changed or force_rates_refresh:
        with st.spinner("Fetching live electricity rates..."):
            try:
                from services.api_integrations import get_live_electricity_rates
                rates_result = get_live_electricity_rates(country_code, location_name)
                
                if rates_result.get('success'):
                    st.session_state.electricity_rates = {
                        'import_rate': rates_result['import_rate'],
                        'export_rate': rates_result['export_rate'],
                        'source': rates_result['source'],
                        'timestamp': rates_result['timestamp'],
                        'country_code': country_code,
                        'location': location_name
                    }
                    st.session_state.last_rate_search_coord = coord_key
                    
                    # Clear force refresh flag
                    if force_rates_refresh:
                        st.session_state.force_rates_refresh = False
                        st.success(f"🌍 Updated rates for new country - Retrieved from: {rates_result['source']}")
                    elif location_changed:
                        st.success(f"🔄 Location updated - Retrieved rates from: {rates_result['source']}")
                    else:
                        st.success(f"✅ Retrieved rates from: {rates_result['source']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Import Rate", f"{rates_result['import_rate']:.3f} €/kWh")
                    with col2:
                        st.metric("Export Rate", f"{rates_result['export_rate']:.3f} €/kWh")
                        
                else:
                    st.warning(f"⚠️ Live rates not available for {country_code}")
                    st.write("Available manual input below")
                    
            except Exception as e:
                st.error(f"Error fetching live rates: {str(e)}")
    
    # Manual rate input as fallback
    if 'electricity_rates' not in st.session_state:
        st.write("**⚙️ Manual Rate Configuration**")
        
        # Enhanced regional guidance with more countries
        rate_guidance = {
            'DE': {'import': 0.315, 'export': 0.082, 'note': 'German average residential rate'},
            'FR': {'import': 0.276, 'export': 0.060, 'note': 'French residential rate (EDF base)'},
            'IT': {'import': 0.284, 'export': 0.070, 'note': 'Italian residential rate'},
            'ES': {'import': 0.264, 'export': 0.055, 'note': 'Spanish residential rate'},
            'NL': {'import': 0.298, 'export': 0.075, 'note': 'Netherlands residential rate'},
            'UK': {'import': 0.285, 'export': 0.050, 'note': 'UK average residential rate'},
            'PL': {'import': 0.252, 'export': 0.045, 'note': 'Polish residential rate'},
            'CZ': {'import': 0.268, 'export': 0.055, 'note': 'Czech Republic residential rate'},
            'IN': {'import': 0.068, 'export': 0.025, 'note': 'Indian average residential rate'},
            'EG': {'import': 0.045, 'export': 0.020, 'note': 'Egyptian residential rate (subsidized)'},
            'SA': {'import': 0.048, 'export': 0.015, 'note': 'Saudi Arabian residential rate'},
            'XX': {'import': 0.200, 'export': 0.050, 'note': 'Global average estimate'},
        }
        
        guidance = rate_guidance.get(country_code, rate_guidance['DE'])
        st.info(f"💡 **Regional Guidance ({country_code}):** {guidance['note']}")
        
        # Adjust input ranges based on country
        if country_code in ['EG', 'SA', 'IN']:  # Countries with subsidized/low rates
            min_import, max_import = 0.020, 0.300
            min_export, max_export = 0.005, 0.100
        else:  # European and other countries
            min_import, max_import = 0.100, 0.500
            min_export, max_export = 0.010, 0.200
        
        col1, col2 = st.columns(2)
        with col1:
            import_rate = st.number_input(
                "Import Rate (€/kWh)",
                min_import, max_import, guidance['import'], 0.001,
                help="Your electricity purchase rate",
                key="manual_import_rate"
            )
        with col2:
            export_rate = st.number_input(
                "Export Rate (€/kWh)", 
                min_export, max_export, guidance['export'], 0.001,
                help="Feed-in tariff for excess solar energy",
                key="manual_export_rate"
            )
        
        if st.button("💾 Save Manual Rates", key="save_manual_rates"):
            st.session_state.electricity_rates = {
                'import_rate': import_rate,
                'export_rate': export_rate,
                'source': f'Manual Input - {guidance["note"]}',
                'timestamp': datetime.now().isoformat(),
                'country_code': country_code,
                'location': location_name
            }
            st.session_state.last_rate_search_coord = coord_key
            st.success("✅ Manual electricity rates saved")
    
    # Display saved rates
    if 'electricity_rates' in st.session_state:
        rates = st.session_state.electricity_rates
        st.write("**✅ Configured Electricity Rates**")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Import", f"{rates['import_rate']:.3f} €/kWh")
        with col2:
            st.metric("Export", f"{rates['export_rate']:.3f} €/kWh")
        with col3:
            st.write(f"**Source:** {rates['source']}")


def save_project_configuration(project_name):
    """Save project configuration to database"""
    try:
        # Get current coordinates and weather station
        coords = st.session_state.map_coordinates
        location_name = st.session_state.location_name
        
        # Get existing project_id if available (to prevent duplication)
        current_project_id = get_current_project_id()
        
        # Prepare project data
        project_data = {
            'project_name': project_name,
            'location': location_name,
            'coordinates': {
                'lat': coords['lat'],
                'lon': coords['lng']
            },
            'latitude': coords['lat'],
            'longitude': coords['lng'],
            'currency': 'EUR'
        }
        
        # Include project_id if we have one (for updates, not new projects)
        if current_project_id:
            project_data['project_id'] = current_project_id
        
        # Add weather API selection
        if 'selected_weather_api' in st.session_state:
            project_data['weather_api_choice'] = st.session_state.selected_weather_api
        
        # Add electricity rates if configured
        if 'electricity_rates' in st.session_state:
            project_data['electricity_rates'] = st.session_state.electricity_rates
        
        # Add weather station data if selected
        if 'selected_weather_station' in st.session_state:
            station = st.session_state.selected_weather_station
            project_data['selected_weather_station'] = station
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
    render_weather_api_selection()
    render_weather_station_selection()
    render_electricity_rate_integration()
    
    # Configuration summary and save
    st.subheader("6️⃣ Configuration Summary")
    
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
        
        # Show weather API selection
        weather_api = st.session_state.get('selected_weather_api', 'Not selected')
        if weather_api != 'Not selected':
            st.write(f"• Weather API: {weather_api.replace('_', ' ').title()}")
    
    with col2:
        if 'selected_weather_station' in st.session_state:
            station = st.session_state.selected_weather_station
            st.write("**Weather Station:**")
            st.write(f"• Name: {station['name']}")
            st.write(f"• WMO ID: {station['wmo_id']}")
            st.write(f"• Distance: {station['distance_km']:.1f} km")
        else:
            st.warning("⚠️ No weather station selected")
        
        # Show electricity rates if configured
        if 'electricity_rates' in st.session_state:
            rates = st.session_state.electricity_rates
            st.write("**Electricity Rates:**")
            st.write(f"• Import: {rates['import_rate']:.3f} €/kWh")
            st.write(f"• Export: {rates['export_rate']:.3f} €/kWh")
            st.write(f"• Source: {rates['source'][:30]}...")
        else:
            st.warning("⚠️ No electricity rates configured")
    
    # Save configuration button
    if st.button("💾 Save Project Configuration", type="primary", key="save_config"):
        missing_requirements = []
        if 'selected_weather_station' not in st.session_state:
            missing_requirements.append("Weather station")
        if 'electricity_rates' not in st.session_state:
            missing_requirements.append("Electricity rates")
            
        if missing_requirements:
            st.error(f"❌ Please configure: {', '.join(missing_requirements)}")
        else:
            save_project_configuration(project_name)
    
    # Navigation - Single Continue Button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📊 Continue to Step 2: Historical Data →", type="primary", key="nav_step2"):
            st.query_params['step'] = 'historical_data'
            st.rerun()