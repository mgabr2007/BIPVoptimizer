"""
Project Setup page for BIPV Optimizer
Enhanced with weather station selection interface
"""
import streamlit as st
import os
import folium
from streamlit_folium import st_folium
import pandas as pd
import requests
from core.solar_math import get_location_solar_parameters, get_location_electricity_rates, determine_timezone_from_coordinates, get_currency_symbol
from services.io import get_weather_data_from_coordinates, save_project_data
from services.weather_stations import find_nearest_stations, get_station_summary, format_station_display


def get_location_from_coordinates(lat, lon):
    """Get specific location name with district/neighborhood details from coordinates"""
    api_key = os.environ.get('OPENWEATHER_API_KEY')
    if not api_key:
        return f"Location at {lat:.4f}°, {lon:.4f}°"
    
    try:
        # Use OpenWeatherMap reverse geocoding with limit=10 for detailed hierarchy
        url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=10&appid={api_key}"
        response = requests.get(url, timeout=10)
        
        # Also try a direct geocoding approach for more specific results
        if response.status_code == 200:
            data = response.json()
            if data:
                # Try to get more specific location by searching nearby area
                first_result = data[0]
                city_name = first_result.get('name', '')
                
                # Make another call to get more specific results around this area
                search_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=5&appid={api_key}"
                search_response = requests.get(search_url, timeout=5)
                
                if search_response.status_code == 200:
                    search_data = search_response.json()
                    # Combine results for better coverage
                    data.extend(search_data)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                # Debug output if enabled
                if st.session_state.get('debug_geocoding_checkbox', False):
                    st.write(f"Debug: Found {len(data)} location results")
                    for i, loc in enumerate(data[:3]):
                        st.json(loc)
                
                # Extract comprehensive location hierarchy from API results
                location_components = {
                    'neighborhood': [],
                    'district': [],
                    'city': [],
                    'state': data[0].get('state', ''),
                    'country': data[0].get('country', '')
                }
                
                # Process all location results to build hierarchy
                for location_data in data:
                    name = location_data.get('name', '').strip()
                    local_names = location_data.get('local_names', {})
                    
                    # Categorize location names by specificity
                    if name and len(name) > 2:
                        # Check if it's a neighborhood, district, or city
                        if any(keyword in name.lower() for keyword in ['straße', 'platz', 'weg', 'berg', 'hof', 'kiez']):
                            if name not in location_components['neighborhood']:
                                location_components['neighborhood'].append(name)
                        elif len(name) < 15 and name != location_components['country'] and name != location_components['state']:
                            if name not in location_components['district']:
                                location_components['district'].append(name)
                        else:
                            if name not in location_components['city']:
                                location_components['city'].append(name)
                    
                    # Also check local names
                    for lang_code in ['en', 'de']:
                        local_name = local_names.get(lang_code, '').strip() if local_names else ''
                        if local_name and len(local_name) > 2 and local_name != name:
                            if len(local_name) < 15 and local_name not in location_components['district']:
                                location_components['district'].append(local_name)
                
                # Extract more specific location information from multiple API results
                location_hierarchy = []
                all_names = set()
                
                # Collect all unique location names from different API results
                for result in data[:5]:  # Check first 5 results for variety
                    name = result.get('name', '')
                    if name and name not in all_names and len(name) > 2:
                        all_names.add(name)
                        # Prioritize shorter, more specific names
                        if len(name) < 20:
                            location_hierarchy.append(name)
                
                # Use the most specific available information
                if len(location_hierarchy) >= 2:
                    # Filter to avoid repetition but keep specificity
                    unique_hierarchy = []
                    for loc in location_hierarchy[:3]:
                        if not any(existing in loc for existing in unique_hierarchy):
                            unique_hierarchy.append(loc)
                    
                    # Add country for international context
                    country = data[0].get('country', '')
                    if country and country not in unique_hierarchy:
                        unique_hierarchy.append(country)
                    
                    return ', '.join(unique_hierarchy[:3])  # Max 3 components
                
                # Enhanced fallback - use all available location data
                first_result = data[0]
                
                # Try to extract detailed information from the first result
                detailed_parts = []
                
                # Check for detailed address components in the first result
                if hasattr(first_result, 'get'):
                    # Look for local names or display name with more details
                    local_names = first_result.get('local_names', {})
                    if local_names:
                        for lang in ['en', 'de']:
                            if lang in local_names and local_names[lang] != first_result.get('name', ''):
                                detailed_parts.append(local_names[lang])
                    
                    # Add the primary name if not already included
                    primary_name = first_result.get('name', '')
                    if primary_name and primary_name not in detailed_parts:
                        detailed_parts.append(primary_name)
                    
                    # Add state if different from existing parts
                    state = first_result.get('state', '')
                    if state and state not in detailed_parts:
                        detailed_parts.append(state)
                    
                    # Add country code for international context
                    country = first_result.get('country', '')
                    if country:
                        detailed_parts.append(country)
                
                # Return enhanced location string
                if len(detailed_parts) >= 2:
                    return ', '.join(detailed_parts[:3])  # Limit to 3 components
                
                # Final fallback to basic format
                city = first_result.get('name', '') if data else ''
                country = first_result.get('country', '') if data else ''
                if city and country:
                    return f"{city}, {country}"
        
        return f"Location at {lat:.4f}°, {lon:.4f}°"
    
    except Exception as e:
        if st.session_state.get('debug_geocoding', False):
            st.error(f"Geocoding error: {e}")
        return f"Location at {lat:.4f}°, {lon:.4f}°"


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
        
        # Debug option for location detection
        debug_geocoding = st.checkbox(
            "Debug Location Detection",
            help="Show detailed geocoding API responses for troubleshooting",
            key="debug_geocoding_checkbox"
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
        
        # Update coordinates and location name from manual input
        if manual_lat != st.session_state.map_coordinates['lat'] or manual_lon != st.session_state.map_coordinates['lng']:
            st.session_state.map_coordinates = {'lat': manual_lat, 'lng': manual_lon}
            # Update location name based on new coordinates
            st.session_state.location_name = get_location_from_coordinates(manual_lat, manual_lon)
    
    # Find nearby weather stations
    nearby_stations = find_nearest_stations(
        st.session_state.map_coordinates['lat'], 
        st.session_state.map_coordinates['lng'], 
        max_distance_km=search_radius
    )
    
    # Create stable folium map with weather stations (prevent continuous refreshing)
    current_zoom = st.session_state.get('map_zoom', 13)
    m = folium.Map(
        location=[st.session_state.map_coordinates['lat'], st.session_state.map_coordinates['lng']],
        zoom_start=current_zoom,
        tiles="OpenStreetMap",
        prefer_canvas=True
    )
    
    # Add marker for current location with neighborhood-specific name
    current_location_name = st.session_state.get('location_name', 'Selected Location')
    folium.Marker(
        [st.session_state.map_coordinates['lat'], st.session_state.map_coordinates['lng']],
        popup=f"<b>{current_location_name}</b><br>Lat: {st.session_state.map_coordinates['lat']:.4f}°<br>Lon: {st.session_state.map_coordinates['lng']:.4f}°",
        tooltip=f"Project Location: {current_location_name}",
        icon=folium.Icon(color="red", icon="building", prefix="fa")
    ).add_to(m)
    
    # Add weather station markers
    if not nearby_stations.empty:
        for idx, station in nearby_stations.iterrows():
            station_info = format_station_display(station)
            # Convert pandas Series values to float for folium
            lat_val = float(station['latitude'])
            lon_val = float(station['longitude'])
            
            folium.Marker(
                [lat_val, lon_val],
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
    
    # Display stable map with optimized state management
    map_data = None
    if location_method == "Interactive Map":
        # Use stable map rendering with minimal updates
        map_data = st_folium(
            m, 
            key="location_map", 
            height=450, 
            width=700,
            returned_objects=["last_clicked", "zoom"],  # Only track essential data
            feature_group_to_add=None,  # Reduce complexity
            debug=False  # Disable debug mode for stability
        )
        
        # Update zoom level only when significantly changed
        if map_data and map_data.get('zoom') and abs(map_data['zoom'] - st.session_state.get('map_zoom', 13)) > 0.5:
            st.session_state.map_zoom = map_data['zoom']
        
        # Process map clicks with improved stability
        if (map_data and 
            map_data.get('last_clicked') is not None and 
            not st.session_state.get('processing_click', False)):
            
            new_coords = map_data['last_clicked']
            current_lat = st.session_state.map_coordinates['lat']
            current_lon = st.session_state.map_coordinates['lng']
            
            # Only process significant coordinate changes
            lat_diff = abs(new_coords['lat'] - current_lat)
            lon_diff = abs(new_coords['lng'] - current_lon)
            
            if lat_diff > 0.001 or lon_diff > 0.001:  # Increased threshold for stability
                # Prevent multiple simultaneous updates
                st.session_state.processing_click = True
                
                # Update coordinates
                st.session_state.map_coordinates = new_coords
                st.session_state.location_name = get_location_from_coordinates(
                    new_coords['lat'], new_coords['lng']
                )
                
                # Reset processing flag
                st.session_state.processing_click = False
    else:
        # Static map display for manual coordinates
        st_folium(
            m, 
            key="location_map_display", 
            height=450, 
            width=700,
            returned_objects=[],  # No interaction needed
            debug=False
        )
    
    # Display selected coordinates and weather station summary
    selected_lat = st.session_state.map_coordinates['lat']
    selected_lon = st.session_state.map_coordinates['lng']
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Latitude", f"{selected_lat:.4f}°")
    with col2:
        st.metric("Longitude", f"{selected_lon:.4f}°")
    with col3:
        # Auto-determine timezone
        timezone = determine_timezone_from_coordinates(selected_lat, selected_lon)
        st.metric("Timezone", timezone)
    with col4:
        stations_summary = get_station_summary(nearby_stations)
        st.metric("Nearby Stations", stations_summary['total_stations'])
    
    # Weather station selection interface
    if not nearby_stations.empty:
        st.subheader("🌡️ Weather Station Selection")
        st.markdown("Select the most appropriate weather station for your project's meteorological data:")
        
        # Station summary
        stations_summary = get_station_summary(nearby_stations)
        if stations_summary['total_stations'] > 0:
            countries_text = ", ".join(stations_summary['countries'][:3])
            if len(stations_summary['countries']) > 3:
                countries_text += f" and {len(stations_summary['countries'])-3} more"
            
            st.info(f"Found {stations_summary['total_stations']} stations within {search_radius} km. "
                   f"Countries: {countries_text}. "
                   f"Closest station: {stations_summary['closest_distance']:.1f} km away.")
        
        # Station selection
        station_options = []
        station_details = {}
        
        for idx, station in nearby_stations.head(10).iterrows():  # Show top 10 closest
            station_info = format_station_display(station)
            display_name = f"{station['name']} ({station['country']}) - {station['distance_km']:.1f} km"
            station_options.append(display_name)
            station_details[display_name] = station.to_dict()
        
        selected_station_name = st.selectbox(
            "Choose Weather Station",
            station_options,
            help="Select the weather station that best represents your project's climate conditions",
            key="weather_station_selector"
        )
        
        if selected_station_name:
            selected_station_data = station_details[selected_station_name]
            
            # Display selected station details
            with st.expander("📋 Selected Station Details", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**Station Information:**")
                    st.write(f"• Name: {selected_station_data['name']}")
                    st.write(f"• WMO ID: {selected_station_data['wmo_id']}")
                    st.write(f"• Country: {selected_station_data['country']}")
                
                with col2:
                    st.write("**Location Details:**")
                    st.write(f"• Latitude: {selected_station_data['latitude']:.4f}°")
                    st.write(f"• Longitude: {selected_station_data['longitude']:.4f}°")
                    st.write(f"• Elevation: {selected_station_data['height']:.0f} m")
                
                with col3:
                    st.write("**Distance Analysis:**")
                    st.write(f"• Distance: {selected_station_data['distance_km']:.1f} km")
                    st.write(f"• Search Radius: {search_radius} km")
                    coverage_pct = (selected_station_data['distance_km'] / search_radius) * 100
                    st.write(f"• Coverage: {coverage_pct:.1f}% of search area")
            
            # Save selected station to session state
            st.session_state.selected_weather_station = selected_station_data
    
    else:
        st.warning(f"No weather stations found within {search_radius} km of the selected location. "
                  f"Consider increasing the search radius or using manual weather data entry.")
        st.session_state.selected_weather_station = None
    
    # Location name input (auto-updated from map selection)
    default_location = st.session_state.get('location_name', "Berlin, Germany")
    

    
    location_name = st.text_input(
        "Location Name",
        value=default_location,
        help="🏙️ Location name auto-detected from map selection with neighborhood-level precision. You can modify if needed. This helps identify the project location in reports and provides context for solar irradiance and electricity rate calculations. Format: 'Neighborhood, District, City, Country'",
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
        # Prepare enhanced project data with weather station information
        project_data = {
            'project_name': project_name,
            'location': location_name,
            'coordinates': {
                'lat': selected_lat,
                'lon': selected_lon
            },
            'timezone': timezone,
            'currency': currency,
            'setup_complete': True,
            'location_method': location_method,
            'search_radius': search_radius
        }
        
        # Add selected weather station data if available
        selected_station = st.session_state.get('selected_weather_station')
        if selected_station:
            project_data['selected_weather_station'] = selected_station
            project_data['weather_station'] = {
                'wmo_id': selected_station['wmo_id'],
                'name': selected_station['name'],
                'country': selected_station['country'],
                'coordinates': {
                    'lat': selected_station['latitude'],
                    'lon': selected_station['longitude']
                },
                'elevation': selected_station['height'],
                'distance_km': selected_station['distance_km']
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
            
            # Display enhanced configuration summary
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.info(f"""
                **Project Details:**
                - Name: {project_name}
                - Location: {location_name}
                - Coordinates: {selected_lat:.4f}°, {selected_lon:.4f}°
                - Timezone: {timezone}
                - Currency: {get_currency_symbol(currency)} ({currency})
                - Selection Method: {location_method}
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
            
            with col3:
                if selected_station:
                    st.info(f"""
                    **Weather Station:**
                    - Name: {selected_station['name']}
                    - Country: {selected_station['country']}
                    - WMO ID: {selected_station['wmo_id']}
                    - Distance: {selected_station['distance_km']:.1f} km
                    - Elevation: {selected_station['height']:.0f} m
                    - Search Radius: {search_radius} km
                    """)
                else:
                    st.warning(f"""
                    **Weather Station:**
                    - No station selected
                    - Search radius: {search_radius} km
                    - Stations found: {stations_summary['total_stations']}
                    
                    Consider increasing search radius or using manual weather data.
                    """)
            

        else:
            st.error("❌ Failed to save project data to database.")
    
    # Navigation hint
    if st.session_state.get('project_data', {}).get('setup_complete'):
        st.success("✅ Project setup complete! You can now proceed to Step 2: Historical Data Analysis.")