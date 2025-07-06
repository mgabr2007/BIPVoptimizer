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
from services.electricity_rates import get_real_time_electricity_rates, display_rate_source_info, enhance_project_setup_with_live_rates
from services.api_integrations import implement_live_rate_fetching, get_live_electricity_rates



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

        return f"Location at {lat:.4f}°, {lon:.4f}°"


def render_project_setup():
    """Render the project setup module with configuration inputs."""
    
    # Add OptiSunny character header image
    st.image("attached_assets/step01_1751436847828.png", width=400)
    
    st.header("Step 1: Project Setup & Configuration")
    st.markdown("Configure your BIPV optimization project with location selection and data integration.")
    
    # STEP 1.1: Basic Project Information
    st.subheader("1️⃣ Project Information")
    
    col1, col2 = st.columns(2)
    with col1:
        project_name = st.text_input(
            "Project Name",
            value="BIPV Optimization Project",
            help="Enter a descriptive name for your BIPV analysis project",
            key="project_name_input"
        )
    
    with col2:
        # Auto-set currency to EUR (standardized)
        currency = "EUR"
        st.text_input(
            "Currency (Fixed)",
            value="EUR",
            disabled=True,
            help="All financial calculations use EUR with automatic exchange rate conversion",
            key="currency_display"
        )
    
    # STEP 1.2: Location Selection
    st.subheader("2️⃣ Location Selection")
    
    # Initialize map with default coordinates (Berlin)
    if 'map_coordinates' not in st.session_state:
        st.session_state.map_coordinates = {'lat': 52.5200, 'lng': 13.4050}
    
    # Location method selection
    location_method = st.radio(
        "Choose Location Selection Method",
        ["Interactive Map", "Manual Coordinates"],
        help="Select how to specify your project location",
        key="location_method",
        horizontal=True
    )
    
    # Configuration settings in balanced layout
    search_radius = st.selectbox(
        "Weather Station Search Radius (km)",
        [100, 200, 300, 500, 750, 1000],
        index=3,
        help="Maximum distance to search for meteorological stations",
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
        prefer_canvas=True,
        zoom_control=True,
        dragging=True,
        scrollWheelZoom=True
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
    
    # Custom CSS to reduce map spacing
    st.markdown("""
    <style>
    .stApp > div[data-testid="stVerticalBlock"] > div.element-container:has(iframe[title="streamlit_folium.st_folium"]) {
        margin-bottom: -1rem !important;
        padding-bottom: 0 !important;
    }
    iframe[title="streamlit_folium.st_folium"] {
        margin-bottom: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Display stable map with minimal refresh during panning
    map_data = None
    if location_method == "Interactive Map":
        # Initialize last click tracker to prevent map refreshing
        if 'last_map_click_lat' not in st.session_state:
            st.session_state.last_map_click_lat = None
        if 'last_map_click_lng' not in st.session_state:
            st.session_state.last_map_click_lng = None
            
        # Use stable map rendering with reduced sensitivity
        with st.container():
            map_data = st_folium(
                m, 
                key="location_map", 
                height=450, 
                width=700,
                returned_objects=["last_clicked"],  # Only track clicks, not zoom/pan
                feature_group_to_add=None,
                debug=False
            )
        
        # Only process actual clicks, not pan/zoom interactions
        if (map_data and 
            map_data.get('last_clicked') is not None):
            
            new_coords = map_data['last_clicked']
            
            # Check if this is a new actual click (not just pan/zoom)
            if (st.session_state.last_map_click_lat != new_coords['lat'] or 
                st.session_state.last_map_click_lng != new_coords['lng']):
                
                current_lat = st.session_state.map_coordinates['lat']
                current_lon = st.session_state.map_coordinates['lng']
                
                # Only process if coordinates changed significantly (actual click, not drift)
                lat_diff = abs(new_coords['lat'] - current_lat)
                lon_diff = abs(new_coords['lng'] - current_lon)
                
                if lat_diff > 0.01 or lon_diff > 0.01:  # Even higher threshold to prevent pan interference
                    # Add a small delay to debounce rapid clicks
                    import time
                    current_time = time.time()
                    last_update_time = st.session_state.get('last_map_update_time', 0)
                    
                    # Only update if enough time has passed (debounce)
                    if current_time - last_update_time > 1.0:  # 1 second debounce
                        # Update coordinates and location name
                        st.session_state.map_coordinates = new_coords
                        st.session_state.location_name = get_location_from_coordinates(
                            new_coords['lat'], new_coords['lng']
                        )
                        
                        # Remember this click to avoid reprocessing
                        st.session_state.last_map_click_lat = new_coords['lat']
                        st.session_state.last_map_click_lng = new_coords['lng']
                        st.session_state.last_map_update_time = current_time
                        
                        # Trigger rerun only for significant location changes
                        st.rerun()
    else:
        # Static map display for manual coordinates
        with st.container():
            st_folium(
                m, 
                key="location_map_display", 
                height=450, 
                width=700,
                returned_objects=[],  # No interaction needed
                debug=False
            )
    
    # STEP 1.3: Weather Station Selection
    st.subheader("3️⃣ Weather Station Selection")
    
    selected_lat = st.session_state.map_coordinates['lat']
    selected_lon = st.session_state.map_coordinates['lng']
    
    # Get current location name and weather info
    current_location = st.session_state.get('location_name', 'Loading location...')
    timezone = determine_timezone_from_coordinates(selected_lat, selected_lon)
    stations_summary = get_station_summary(nearby_stations)
    
    # Show current coordinates for reference
    st.info(f"Selected coordinates: {selected_lat:.4f}°, {selected_lon:.4f}° ({current_location})")
    
    # Streamlined weather station selection
    if not nearby_stations.empty:
        st.subheader("🌡️ Weather Station Selection")
        
        # Station selection dropdown
        station_options = []
        station_details = {}
        
        for idx, station in nearby_stations.head(10).iterrows():  # Show top 10 closest
            display_name = f"{station['name']} ({station['country']}) - {station['distance_km']:.1f} km"
            station_options.append(display_name)
            # Convert to dict but ensure distance_km maintains precision
            station_dict = station.to_dict()
            station_dict['distance_km'] = float(station['distance_km'])  # Ensure proper float precision
            station_details[display_name] = station_dict
        
        selected_station_name = st.selectbox(
            "Choose Weather Station",
            station_options,
            help="Select the weather station that best represents your project's climate conditions",
            key="weather_station_selector"
        )
        
        if selected_station_name:
            selected_station_data = station_details[selected_station_name]
            
            # Compact station details in a single info box
            st.info(f"""
            **Selected Station:** {selected_station_data['name']} (WMO ID: {selected_station_data['wmo_id']})  
            **Location:** {selected_station_data['country']} • {selected_station_data['latitude']:.4f}°, {selected_station_data['longitude']:.4f}° • {selected_station_data['height']:.0f}m elevation  
            **Distance:** {selected_station_data['distance_km']:.1f} km from project location
            """)
            
            # Save selected station to session state
            st.session_state.selected_weather_station = selected_station_data
    
    else:
        st.error(f"No weather stations found within {search_radius} km. Try increasing the search radius.")
        st.session_state.selected_weather_station = None
    

    
    # Weather data integration
    st.subheader("🌤️ Weather Data Integration")
    
    st.info("""
    **How Your Location Data Will Be Used:**
    
    📍 **Selected Coordinates & WMO Station** → Step 3 TMY Generation
    - Your precise coordinates and selected weather station will be used in Step 3 to generate authentic Typical Meteorological Year (TMY) data
    - TMY includes 8,760 hourly data points of solar irradiance (GHI, DNI, DHI), temperature, humidity, and wind
    - Generated using ISO 15927-4 standards with astronomical algorithms for accurate solar positioning
    - WMO station provides authentic meteorological reference data for your climate zone
    
    💰 **Electricity Rates** → Financial Analysis (Steps 7-9)
    - Import/export rates will be used for economic calculations including ROI, payback period, and cash flow analysis
    """)
    
    # STEP 1.4: Data Integration & Configuration
    st.subheader("4️⃣ Data Integration & Configuration")
    
    # Location name input
    default_location = st.session_state.get('location_name', "Berlin, Germany")
    location_name = st.text_input(
        "Project Location Name",
        value=default_location,
        help="Location name auto-detected from map selection. You can modify if needed.",
        key="location_name_input"
    )
    
    # Electricity Rate Integration
    st.markdown("**🔌 Electricity Rate Integration**")
    enable_live_rates = enhance_project_setup_with_live_rates()
    
    # Current Weather Data
    st.markdown("**🌤️ Current Weather Data**")
    api_key = os.environ.get('OPENWEATHER_API_KEY')
    
    if api_key:
        if st.button("Fetch Current Weather", key="fetch_weather"):
            with st.spinner("Fetching weather data..."):
                weather_data = get_weather_data_from_coordinates(selected_lat, selected_lon, api_key)
                
                if weather_data and weather_data.get('api_success'):
                    st.success("Weather data retrieved!")
                    st.info(f"{weather_data['temperature']:.1f}°C • {weather_data['description'].title()}")
                    
                    # Store weather data
                    st.session_state.project_data = st.session_state.get('project_data', {})
                    st.session_state.project_data['current_weather'] = weather_data
                    st.session_state.project_data['weather_complete'] = True
                else:
                    st.error("Failed to retrieve weather data")
    else:
        st.caption("OpenWeather API key not configured")
    
    # Data Usage Information
    with st.expander("📊 How This Data Will Be Used", expanded=False):
        st.markdown("""
        ### Data Flow Through BIPV Analysis Workflow:
        
        **Step 1 → Step 3 (Weather Integration):**
        - **Location coordinates** → Solar position calculations and TMY generation using ISO 15927-4 standards
        - **Selected weather station** → Authentic meteorological data from WMO CLIMAT database
        - **Timezone** → Proper time zone conversion for solar calculations
        
        **Step 1 → Step 5 (Radiation Analysis):**
        - **Geographic location** → Climate zone classification for solar parameters
        - **Elevation data** → Atmospheric corrections for radiation modeling
        
        **Step 1 → Step 7 (Yield vs Demand):**
        - **Electricity rates** → Financial calculations and grid interaction analysis
        - **Import/export rates** → Feed-in tariff and cost savings calculations
        
        **Step 1 → Step 9 (Financial Analysis):**
        - **Currency settings** → All financial metrics and NPV calculations
        - **Location-based parameters** → Regional electricity pricing and market conditions
        
        **Step 1 → Step 10 (Reporting):**
        - **Project metadata** → Report headers and location-specific context
        - **Configuration summary** → Technical specifications and analysis parameters
        """)
    
    # STEP 1.5: Configuration Review & Save
    st.subheader("5️⃣ Configuration Review & Save")
    
    # Show current configuration before saving
    with st.expander("📋 Review Current Configuration", expanded=False):
        st.markdown(f"""
        **Project Details:**
        - Name: {project_name}
        - Location: {location_name}
        - Coordinates: {selected_lat:.4f}°, {selected_lon:.4f}°
        - Timezone: {timezone}
        """)
        
        if stations_summary['total_stations'] > 0:
            st.markdown(f"""
            **Weather Data Sources:**
            - Weather stations found: {stations_summary['total_stations']}
            - Closest station: {stations_summary['closest_distance']:.1f} km
            - Search radius: {search_radius} km
            """)
        else:
            st.warning(f"No weather stations found within {search_radius} km")
    
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
        
        # Use real-time rates if available from live integration
        live_rates = st.session_state.get('live_electricity_rates')
        if live_rates and live_rates.get('success') and live_rates.get('import_rate'):
            electricity_rates = {
                'import_rate': live_rates['import_rate'],
                'export_rate': live_rates.get('export_rate', 0.070),
                'source': f"live_api_{live_rates['source']}",
                'live_rates_enabled': True,
                'data_quality': live_rates.get('data_quality', 'official_source')
            }
        else:
            electricity_rates = get_location_electricity_rates(location_name, currency)
            electricity_rates['source'] = 'database_estimates'
            electricity_rates['live_rates_enabled'] = False
        
        # Add calculated parameters
        project_data['solar_parameters'] = location_params
        project_data['electricity_rates'] = electricity_rates
        
        # Store in session state
        st.session_state.project_data = project_data
        
        # Save to database
        project_id = save_project_data(project_data)
        if project_id:
            st.session_state.project_id = project_id
            
            # Consolidated project summary
            
            with st.container():
                st.markdown("### 📋 Complete Project Configuration")
                
                # Create a comprehensive summary in organized sections
                st.markdown(f"""
                **🏢 Project Information**
                - **Name:** {project_name}
                - **Location:** {location_name}
                - **Coordinates:** {selected_lat:.4f}°, {selected_lon:.4f}°
                - **Timezone:** {timezone} • **Currency:** EUR
                
                **💰 Financial Parameters**
                - **Import Rate:** €{electricity_rates['import_rate']:.3f}/kWh
                - **Export Rate:** €{electricity_rates['export_rate']:.3f}/kWh
                - **Rate Source:** {electricity_rates.get('source', 'database_estimates').replace('_', ' ').title()}
                """)
                
                if selected_station:
                    st.markdown(f"""
                    **🌡️ Selected Weather Station**
                    - **Station:** {selected_station['name']}
                    - **Country:** {selected_station['country']}
                    - **WMO ID:** {selected_station['wmo_id']}
                    - **Distance:** {selected_station['distance_km']:.1f} km
                    - **Elevation:** {selected_station['height']:.0f} m
                    """)
                else:
                    st.warning(f"""
                    **🌡️ Weather Station**
                    - No station selected
                    - Found: {stations_summary['total_stations']} stations
                    - Radius: {search_radius} km
                    """)
                
                # Data usage explanation
                st.info("""
                **📊 How This Data Will Be Used:**
                - **Location coordinates** → TMY generation in Step 3 using ISO 15927-4 standards
                - **Weather station** → Authentic meteorological data for solar calculations
                - **Electricity rates** → Financial analysis including ROI, payback period, and cash flow
                """)
            

        else:
            st.error("❌ Failed to save project data to database.")
    

    
    # Navigation hint and step report download
    if st.session_state.get('project_data', {}).get('setup_complete'):
        st.success("✅ Project setup complete! You can now proceed to Step 2: Historical Data Analysis.")
        
        # Add step-specific download button
        st.markdown("---")
        st.markdown("### 📄 Step 1 Analysis Report")
        st.markdown("Download a detailed report of your project setup and configuration:")
        
        from utils.individual_step_reports import create_step_download_button
        create_step_download_button(1, "Project Setup", "Download Project Setup Report")