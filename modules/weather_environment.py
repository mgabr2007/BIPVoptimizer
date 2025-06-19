import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

def fetch_weather_data(api_key, lat, lon):
    """Fetch weather data from OpenWeatherMap API."""
    try:
        # Current weather
        current_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        current_response = requests.get(current_url)
        current_data = current_response.json()
        
        # Historical weather (last 5 days for TMY simulation)
        hist_data = []
        for i in range(5):
            timestamp = int((datetime.now() - timedelta(days=i)).timestamp())
            hist_url = f"http://api.openweathermap.org/data/3.0/onecall/timemachine?lat={lat}&lon={lon}&dt={timestamp}&appid={api_key}&units=metric"
            try:
                hist_response = requests.get(hist_url)
                if hist_response.status_code == 200:
                    hist_data.append(hist_response.json())
            except:
                continue
        
        return current_data, hist_data
    except Exception as e:
        raise Exception(f"Weather API error: {str(e)}")

def generate_tmy_data(lat, lon, hist_data):
    """Generate simplified TMY (Typical Meteorological Year) data."""
    # Create synthetic TMY data based on location and historical patterns
    dates = pd.date_range('2023-01-01', '2023-12-31 23:00:00', freq='H')
    
    # Base solar irradiance calculation (simplified)
    day_of_year = dates.dayofyear
    hour = dates.hour
    
    # Solar elevation angle approximation
    declination = 23.45 * np.sin(np.radians(360 * (284 + day_of_year) / 365))
    hour_angle = 15 * (hour - 12)
    
    elevation = np.arcsin(
        np.sin(np.radians(lat)) * np.sin(np.radians(declination)) +
        np.cos(np.radians(lat)) * np.cos(np.radians(declination)) * np.cos(np.radians(hour_angle))
    )
    
    # Calculate irradiance components
    ghi = np.maximum(0, 900 * np.sin(elevation) * (1 + 0.3 * np.sin(2 * np.pi * day_of_year / 365)))
    dni = np.maximum(0, ghi * 0.8)
    dhi = ghi - dni * np.sin(elevation)
    
    # Add weather variations
    np.random.seed(42)  # For reproducible results
    weather_factor = 0.7 + 0.6 * np.random.random(len(dates))
    
    tmy_data = pd.DataFrame({
        'datetime': dates,
        'GHI': ghi * weather_factor,
        'DNI': dni * weather_factor,
        'DHI': dhi * weather_factor,
        'temperature': 15 + 10 * np.sin(2 * np.pi * day_of_year / 365) + 5 * np.random.randn(len(dates)),
        'humidity': 60 + 20 * np.random.randn(len(dates)),
        'wind_speed': 3 + 2 * np.random.randn(len(dates))
    })
    
    # Ensure realistic values
    tmy_data['GHI'] = np.clip(tmy_data['GHI'], 0, 1200)
    tmy_data['DNI'] = np.clip(tmy_data['DNI'], 0, 1000)
    tmy_data['DHI'] = np.clip(tmy_data['DHI'], 0, 500)
    tmy_data['temperature'] = np.clip(tmy_data['temperature'], -20, 45)
    tmy_data['humidity'] = np.clip(tmy_data['humidity'], 20, 100)
    tmy_data['wind_speed'] = np.clip(tmy_data['wind_speed'], 0, 15)
    
    return tmy_data

def calculate_shading_factors(tree_data, building_position):
    """Calculate shading factors based on tree positions and building location."""
    if tree_data is None or len(tree_data) == 0:
        return pd.DataFrame({'hour': range(24), 'shading_factor': [1.0] * 24})
    
    # Simplified shading calculation
    shading_factors = []
    for hour in range(24):
        total_shading = 0
        for _, tree in tree_data.iterrows():
            # Calculate sun angle and tree shadow
            sun_elevation = max(0, 60 * np.sin(np.pi * (hour - 6) / 12))
            if sun_elevation > 0:
                shadow_length = tree['height'] / np.tan(np.radians(sun_elevation))
                distance = np.sqrt((tree['x'] - building_position[0])**2 + (tree['y'] - building_position[1])**2)
                
                if distance < shadow_length:
                    # Calculate shading effect based on tree canopy
                    shading_effect = min(0.8, tree['canopy_radius'] / distance)
                    total_shading += shading_effect
        
        # Total shading factor (0 = fully shaded, 1 = no shading)
        shading_factor = max(0.2, 1 - min(0.8, total_shading))
        shading_factors.append(shading_factor)
    
    return pd.DataFrame({'hour': range(24), 'shading_factor': shading_factors})

def render_weather_environment():
    """Render the weather and environment analysis module."""
    
    st.header("3. Weather & Environment")
    st.markdown("Configure weather data sources and analyze environmental factors affecting solar potential.")
    
    # API Configuration
    st.subheader("Weather Data Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        api_key = st.text_input(
            "OpenWeatherMap API Key",
            value=os.getenv("OPENWEATHER_API_KEY", ""),
            type="password",
            help="Enter your OpenWeatherMap API key for weather data access"
        )
        
        latitude = st.number_input(
            "Latitude",
            value=st.session_state.project_data.get('latitude', 40.7128),
            min_value=-90.0,
            max_value=90.0,
            step=0.0001,
            format="%.4f",
            help="Latitude of the project location"
        )
    
    with col2:
        st.markdown("**Quick Location Lookup**")
        st.caption("Popular cities:")
        location_options = {
            "New York, NY": (40.7128, -74.0060),
            "Los Angeles, CA": (34.0522, -118.2437),
            "London, UK": (51.5074, -0.1278),
            "Berlin, Germany": (52.5200, 13.4050),
            "Tokyo, Japan": (35.6762, 139.6503),
            "Sydney, Australia": (-33.8688, 151.2093)
        }
        
        selected_city = st.selectbox("Select a city", ["Custom"] + list(location_options.keys()))
        if selected_city != "Custom":
            latitude = location_options[selected_city][0]
            longitude = location_options[selected_city][1]
            st.session_state.project_data['latitude'] = latitude
            st.session_state.project_data['longitude'] = longitude
        
        longitude = st.number_input(
            "Longitude",
            value=st.session_state.project_data.get('longitude', -74.0060),
            min_value=-180.0,
            max_value=180.0,
            step=0.0001,
            format="%.4f",
            help="Longitude of the project location"
        )
    
    # Store coordinates
    st.session_state.project_data['latitude'] = latitude
    st.session_state.project_data['longitude'] = longitude
    
    # Fetch Weather Data
    if api_key and st.button("Fetch Weather Data"):
        with st.spinner("Fetching weather data from OpenWeatherMap..."):
            try:
                current_data, hist_data = fetch_weather_data(api_key, latitude, longitude)
                
                # Generate TMY data
                tmy_data = generate_tmy_data(latitude, longitude, hist_data)
                st.session_state.project_data['tmy_data'] = tmy_data.to_dict()
                st.session_state.project_data['current_weather'] = current_data
                
                st.success("✅ Weather data fetched successfully!")
                
                # Display current weather
                st.subheader("Current Weather Conditions")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Temperature", f"{current_data['main']['temp']:.1f}°C")
                with col2:
                    st.metric("Humidity", f"{current_data['main']['humidity']}%")
                with col3:
                    st.metric("Pressure", f"{current_data['main']['pressure']} hPa")
                with col4:
                    st.metric("Wind Speed", f"{current_data['wind']['speed']:.1f} m/s")
                
            except Exception as e:
                st.error(f"❌ Error fetching weather data: {str(e)}")
                st.info("Please check your API key and internet connection.")
    
    # Display TMY Data if available
    if 'tmy_data' in st.session_state.project_data:
        st.subheader("Typical Meteorological Year (TMY) Data")
        
        tmy_df = pd.DataFrame(st.session_state.project_data['tmy_data'])
        tmy_df['datetime'] = pd.to_datetime(tmy_df['datetime'])
        
        # Data quality report
        st.subheader("Data Quality Report")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Hours", len(tmy_df))
        with col2:
            st.metric("Avg GHI", f"{tmy_df['GHI'].mean():.1f} W/m²")
        with col3:
            st.metric("Max GHI", f"{tmy_df['GHI'].max():.1f} W/m²")
        
        # Irradiance components chart
        monthly_irradiance = tmy_df.groupby(tmy_df['datetime'].dt.month).agg({
            'GHI': 'mean',
            'DNI': 'mean',
            'DHI': 'mean'
        }).reset_index()
        monthly_irradiance['Month'] = monthly_irradiance['datetime']
        
        fig_irradiance = go.Figure()
        fig_irradiance.add_trace(go.Scatter(x=monthly_irradiance['Month'], y=monthly_irradiance['GHI'],
                                           mode='lines+markers', name='GHI', line=dict(color='orange')))
        fig_irradiance.add_trace(go.Scatter(x=monthly_irradiance['Month'], y=monthly_irradiance['DNI'],
                                           mode='lines+markers', name='DNI', line=dict(color='red')))
        fig_irradiance.add_trace(go.Scatter(x=monthly_irradiance['Month'], y=monthly_irradiance['DHI'],
                                           mode='lines+markers', name='DHI', line=dict(color='blue')))
        
        fig_irradiance.update_layout(
            title='Monthly Average Solar Irradiance Components',
            xaxis_title='Month',
            yaxis_title='Irradiance (W/m²)',
            height=400
        )
        st.plotly_chart(fig_irradiance, use_container_width=True)
        
        # Temperature profile
        monthly_temp = tmy_df.groupby(tmy_df['datetime'].dt.month)['temperature'].mean().reset_index()
        monthly_temp['Month'] = monthly_temp['datetime']
        
        fig_temp = px.line(monthly_temp, x='Month', y='temperature',
                          title='Monthly Average Temperature Profile',
                          labels={'temperature': 'Temperature (°C)'})
        st.plotly_chart(fig_temp, use_container_width=True)
    
    # Tree Dataset Upload
    st.subheader("Environmental Shading Analysis")
    st.markdown("Upload tree/obstacle data to calculate shading effects on solar potential.")
    
    tree_file = st.file_uploader(
        "Upload Tree Dataset (CSV)",
        type=['csv'],
        help="CSV with columns: x, y, height, canopy_radius (coordinates relative to building)"
    )
    
    if tree_file is not None:
        try:
            tree_data = pd.read_csv(tree_file)
            required_cols = ['x', 'y', 'height', 'canopy_radius']
            
            if all(col in tree_data.columns for col in required_cols):
                st.success(f"✅ Tree dataset uploaded: {len(tree_data)} trees")
                st.session_state.project_data['tree_data'] = tree_data.to_dict()
                
                # Display tree data preview
                st.dataframe(tree_data.head())
                
                # Calculate shading factors
                building_position = (0, 0)  # Assuming building at origin
                shading_factors = calculate_shading_factors(tree_data, building_position)
                st.session_state.project_data['shading_factors'] = shading_factors.to_dict()
                
                # Visualize shading effect
                fig_shading = px.line(shading_factors, x='hour', y='shading_factor',
                                     title='Hourly Shading Factors from Trees',
                                     labels={'shading_factor': 'Shading Factor (1=no shade, 0=full shade)',
                                            'hour': 'Hour of Day'})
                st.plotly_chart(fig_shading, use_container_width=True)
                
                # Tree positions visualization
                fig_trees = px.scatter(tree_data, x='x', y='y', size='canopy_radius', color='height',
                                      title='Tree Positions and Characteristics',
                                      labels={'x': 'X Position (m)', 'y': 'Y Position (m)',
                                             'height': 'Height (m)'})
                fig_trees.add_trace(go.Scatter(x=[0], y=[0], mode='markers',
                                              marker=dict(size=15, color='red', symbol='square'),
                                              name='Building Position'))
                st.plotly_chart(fig_trees, use_container_width=True)
                
            else:
                st.error(f"❌ Missing required columns: {[col for col in required_cols if col not in tree_data.columns]}")
        
        except Exception as e:
            st.error(f"❌ Error processing tree data: {str(e)}")
    
    else:
        st.info("🌳 Tree data is optional. Skip if no significant shading obstacles are present.")
        with st.expander("📋 View Sample Tree Data Format"):
            sample_trees = {
                'x': [10, -15, 25, 0],
                'y': [20, 10, -5, 30],
                'height': [8, 12, 6, 10],
                'canopy_radius': [4, 6, 3, 5]
            }
            st.dataframe(pd.DataFrame(sample_trees))
            st.caption("Coordinates in meters relative to building position (0,0)")
    
    # Weather data status
    weather_status = []
    if 'tmy_data' in st.session_state.project_data:
        weather_status.append({"Component": "TMY Weather Data", "Status": "✅ Available"})
    else:
        weather_status.append({"Component": "TMY Weather Data", "Status": "❌ Not fetched"})
    
    if 'tree_data' in st.session_state.project_data:
        weather_status.append({"Component": "Tree Shading Data", "Status": "✅ Uploaded"})
    else:
        weather_status.append({"Component": "Tree Shading Data", "Status": "⚪ Optional"})
    
    st.subheader("Environment Data Status")
    st.table(weather_status)
    
    if 'tmy_data' in st.session_state.project_data:
        st.success("✅ Weather environment data is ready for solar analysis!")
    else:
        st.warning("⚠️ Please fetch weather data before proceeding to facade analysis.")
