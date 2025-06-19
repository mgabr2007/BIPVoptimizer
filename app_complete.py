import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import requests
import json
import math
from datetime import datetime, timedelta
import io
import pickle

def main():
    st.set_page_config(
        page_title="BIPV Analysis Platform",
        page_icon="🏢",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🏢 Building Integrated Photovoltaics (BIPV) Analysis Platform")
    st.markdown("---")
    
    # Initialize session state
    if 'workflow_step' not in st.session_state:
        st.session_state.workflow_step = 1
    if 'project_data' not in st.session_state:
        st.session_state.project_data = {}
    if 'checkpoints' not in st.session_state:
        st.session_state.checkpoints = {}
    
    # Sidebar navigation
    st.sidebar.title("Workflow Navigation")
    
    steps = [
        "1. Project Setup",
        "2. Historical Data & AI Model",
        "3. Weather & Environment",
        "4. Facade & Window Extraction", 
        "5. Radiation & Shading Grid",
        "6. PV Panel Specification",
        "7. Yield vs. Demand Calculation",
        "8. Optimization",
        "9. Financial & Environmental Analysis",
        "10. 3D Visualization",
        "11. Reporting & Export"
    ]
    
    # Progress indicator
    st.sidebar.progress(st.session_state.workflow_step / len(steps))
    st.sidebar.markdown(f"**Step {st.session_state.workflow_step} of {len(steps)}**")
    
    # Step selection
    selected_step = st.sidebar.selectbox("Go to Step:", steps, index=st.session_state.workflow_step-1)
    st.session_state.workflow_step = steps.index(selected_step) + 1
    
    # Checkpoint management
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Checkpoints**")
    if st.sidebar.button("Save Checkpoint"):
        st.session_state.checkpoints[st.session_state.workflow_step] = st.session_state.project_data.copy()
        st.sidebar.success(f"Checkpoint saved at Step {st.session_state.workflow_step}")
    
    if st.session_state.checkpoints and st.sidebar.button("Load Last Checkpoint"):
        last_checkpoint = max(st.session_state.checkpoints.keys())
        st.session_state.project_data = st.session_state.checkpoints[last_checkpoint].copy()
        st.session_state.workflow_step = last_checkpoint
        st.sidebar.success(f"Loaded checkpoint from Step {last_checkpoint}")
        st.rerun()
    
    # Main content area
    if st.session_state.workflow_step == 1:
        render_project_setup()
    elif st.session_state.workflow_step == 2:
        render_historical_data()
    elif st.session_state.workflow_step == 3:
        render_weather_environment()
    elif st.session_state.workflow_step == 4:
        render_facade_extraction()
    elif st.session_state.workflow_step == 5:
        render_radiation_grid()
    elif st.session_state.workflow_step == 6:
        render_pv_specification()
    elif st.session_state.workflow_step == 7:
        render_yield_demand()
    elif st.session_state.workflow_step == 8:
        render_optimization()
    elif st.session_state.workflow_step == 9:
        render_financial_analysis()
    elif st.session_state.workflow_step == 10:
        render_3d_visualization()
    elif st.session_state.workflow_step == 11:
        render_reporting()
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.session_state.workflow_step > 1:
            if st.button("⬅️ Previous Step"):
                st.session_state.workflow_step -= 1
                st.rerun()
    
    with col3:
        if st.session_state.workflow_step < len(steps):
            if st.button("Next Step ➡️"):
                st.session_state.workflow_step += 1
                st.rerun()

def render_project_setup():
    """Project setup with configuration inputs"""
    st.header("1. Project Setup")
    st.markdown("Configure your BIPV analysis project settings and upload building models.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Project Configuration")
        
        project_name = st.text_input(
            "Project Name",
            value=st.session_state.project_data.get('project_name', 'BIPV Analysis Project'),
            help="Enter a descriptive name for your project"
        )
        
        location = st.text_input(
            "Project Location",
            value=st.session_state.project_data.get('location', ''),
            help="Building location (city, country)"
        )
        
        # Coordinates
        col_lat, col_lon = st.columns(2)
        with col_lat:
            latitude = st.number_input(
                "Latitude", 
                value=st.session_state.project_data.get('latitude', 40.7128),
                format="%.4f",
                help="Building latitude in decimal degrees"
            )
        with col_lon:
            longitude = st.number_input(
                "Longitude", 
                value=st.session_state.project_data.get('longitude', -74.0060),
                format="%.4f",
                help="Building longitude in decimal degrees"
            )
    
    with col2:
        st.subheader("Analysis Settings")
        
        timezone = st.selectbox(
            "Timezone",
            ["UTC", "US/Eastern", "US/Central", "US/Mountain", "US/Pacific", 
             "Europe/London", "Europe/Berlin", "Asia/Tokyo"],
            index=0,
            help="Select the project timezone"
        )
        
        units = st.selectbox(
            "Units System",
            ["Metric (kW, m², °C)", "Imperial (kW, ft², °F)"],
            index=0,
            help="Choose measurement units"
        )
        
        currency = st.selectbox(
            "Currency",
            ["USD ($)", "EUR (€)", "GBP (£)", "JPY (¥)"],
            index=0,
            help="Select currency for financial analysis"
        )
    
    # Save data
    st.session_state.project_data.update({
        'project_name': project_name,
        'location': location,
        'latitude': latitude,
        'longitude': longitude,
        'timezone': timezone,
        'units': units,
        'currency': currency
    })
    
    # BIM Model Upload Section
    st.subheader("BIM Model Upload")
    st.info("Upload your Revit model for facade and window extraction")
    
    uploaded_file = st.file_uploader(
        "Upload Revit Model (.rvt)",
        type=['rvt'],
        help="Upload a Revit model file at LOD 200 or LOD 100"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ Model uploaded: {uploaded_file.name}")
        st.session_state.project_data['bim_model'] = uploaded_file.name
    
    # Status
    if project_name and location:
        st.success("✅ Project configuration complete!")
        st.info("Proceed to Step 2 to upload historical energy data.")
    else:
        st.warning("⚠️ Please complete project name and location to continue.")

def render_historical_data():
    """Historical data analysis and AI model training"""
    st.header("2. Historical Data & AI Model")
    st.markdown("Upload historical energy consumption data and train a baseline demand prediction model.")
    
    # Historical data upload section
    st.subheader("Historical Energy Consumption Data")
    
    uploaded_file = st.file_uploader(
        "Upload Monthly Consumption Data (CSV)",
        type=['csv'],
        help="Upload a CSV file with columns: Date, Consumption (kWh), Temperature (°C), and other relevant features"
    )
    
    if uploaded_file is not None:
        try:
            with st.spinner("Processing historical data..."):
                # Read the CSV file
                df = pd.read_csv(uploaded_file)
                st.success(f"✅ Data uploaded successfully! {len(df)} records loaded.")
                
                # Display data preview
                st.subheader("Data Preview")
                st.dataframe(df.head(10))
                
                # Data validation and preprocessing
                required_columns = ['Date', 'Consumption']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    st.error(f"❌ Missing required columns: {missing_columns}")
                    st.info("Required columns: Date, Consumption. Optional: Temperature, Humidity, Solar_Irradiance")
                    return
                
                # Process dates
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.sort_values('Date')
                
                # Extract time features
                df['Year'] = df['Date'].dt.year
                df['Month'] = df['Date'].dt.month
                df['DayOfYear'] = df['Date'].dt.dayofyear
                df['Quarter'] = df['Date'].dt.quarter
                
                # Store data in session state
                st.session_state.project_data['historical_data'] = df.to_dict()
                
                # Display data statistics
                st.subheader("Data Statistics")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Records", len(df))
                with col2:
                    st.metric("Date Range", f"{df['Date'].min().strftime('%Y-%m')} to {df['Date'].max().strftime('%Y-%m')}")
                with col3:
                    st.metric("Avg Monthly Consumption", f"{df['Consumption'].mean():.1f} kWh")
                with col4:
                    st.metric("Total Annual Consumption", f"{df['Consumption'].sum():.0f} kWh")
                
                # Trend visualization
                st.subheader("Consumption Trends")
                
                # Monthly trend chart
                fig = px.line(df, x='Date', y='Consumption', 
                             title='Monthly Energy Consumption Over Time',
                             labels={'Consumption': 'Consumption (kWh)', 'Date': 'Date'})
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                # Seasonal analysis
                col1, col2 = st.columns(2)
                
                with col1:
                    # Monthly averages
                    monthly_avg = df.groupby('Month')['Consumption'].mean().reset_index()
                    fig_month = px.bar(monthly_avg, x='Month', y='Consumption',
                                      title='Average Consumption by Month',
                                      labels={'Consumption': 'Avg Consumption (kWh)'})
                    st.plotly_chart(fig_month, use_container_width=True)
                
                with col2:
                    # Quarterly analysis
                    quarterly_avg = df.groupby('Quarter')['Consumption'].mean().reset_index()
                    fig_quarter = px.pie(quarterly_avg, values='Consumption', names='Quarter',
                                        title='Consumption Distribution by Quarter')
                    st.plotly_chart(fig_quarter, use_container_width=True)
                
                # AI Model Training Section
                st.subheader("AI Demand Prediction Model")
                
                if st.button("Train Baseline Demand Model"):
                    with st.spinner("Training RandomForest model..."):
                        # Prepare features for model training
                        feature_columns = ['Month', 'Quarter', 'DayOfYear']
                        
                        # Add additional features if available
                        optional_features = ['Temperature', 'Humidity', 'Solar_Irradiance']
                        for feature in optional_features:
                            if feature in df.columns and df[feature].notna().sum() > len(df) * 0.5:
                                feature_columns.append(feature)
                        
                        # Prepare training data
                        X = df[feature_columns].fillna(df[feature_columns].mean())
                        y = df['Consumption']
                        
                        # Split data
                        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                        
                        # Train model
                        model = RandomForestRegressor(n_estimators=100, random_state=42)
                        model.fit(X_train, y_train)
                        
                        # Make predictions
                        y_pred_train = model.predict(X_train)
                        y_pred_test = model.predict(X_test)
                        
                        # Calculate metrics
                        train_mae = mean_absolute_error(y_train, y_pred_train)
                        test_mae = mean_absolute_error(y_test, y_pred_test)
                        train_r2 = r2_score(y_train, y_pred_train)
                        test_r2 = r2_score(y_test, y_pred_test)
                        
                        # Save model
                        model_buffer = io.BytesIO()
                        pickle.dump({
                            'model': model,
                            'feature_columns': feature_columns,
                            'metrics': {
                                'train_mae': train_mae,
                                'test_mae': test_mae,
                                'train_r2': train_r2,
                                'test_r2': test_r2
                            }
                        }, model_buffer)
                        
                        st.session_state.project_data['demand_model'] = model_buffer.getvalue()
                        
                        st.success("✅ Model trained successfully!")
                        
                        # Display model performance
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Training MAE", f"{train_mae:.1f} kWh")
                        with col2:
                            st.metric("Testing MAE", f"{test_mae:.1f} kWh")
                        with col3:
                            st.metric("Training R²", f"{train_r2:.3f}")
                        with col4:
                            st.metric("Testing R²", f"{test_r2:.3f}")
                        
                        # Feature importance
                        importance_df = pd.DataFrame({
                            'Feature': feature_columns,
                            'Importance': model.feature_importances_
                        }).sort_values('Importance', ascending=False)
                        
                        fig_importance = px.bar(importance_df, x='Importance', y='Feature',
                                               title='Feature Importance in Demand Prediction',
                                               orientation='h')
                        st.plotly_chart(fig_importance, use_container_width=True)
                
                # Model status
                if 'demand_model' in st.session_state.project_data:
                    st.success("✅ Baseline demand model is trained and ready!")
                    st.info("The model will be used in Step 7 to predict future energy demand.")
                else:
                    st.warning("⚠️ Please train the demand model before proceeding to energy analysis.")
                
        except Exception as e:
            st.error(f"❌ Error processing data: {str(e)}")
            st.info("Please ensure your CSV file has the correct format with 'Date' and 'Consumption' columns.")
    
    else:
        st.info("👆 Please upload a CSV file with historical energy consumption data.")
        
        # Show sample data format
        with st.expander("📋 View Sample Data Format"):
            sample_data = {
                'Date': ['2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01'],
                'Consumption': [1250, 1100, 950, 800],
                'Temperature': [5.2, 8.1, 12.5, 18.3],
                'Humidity': [75, 70, 65, 60]
            }
            st.dataframe(pd.DataFrame(sample_data))
            st.caption("Sample format: Date (YYYY-MM-DD), Consumption (kWh), Temperature (°C) [optional], Humidity (%) [optional]")

def render_weather_environment():
    """Weather and environment analysis module"""
    st.header("3. Weather & Environment")
    st.markdown("Configure weather data sources and generate Typical Meteorological Year (TMY) data for solar analysis.")
    
    # Get project coordinates
    latitude = st.session_state.project_data.get('latitude', 40.7128)
    longitude = st.session_state.project_data.get('longitude', -74.0060)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Weather Data Configuration")
        
        # API key input
        api_key = st.text_input(
            "OpenWeatherMap API Key (Optional)",
            type="password",
            help="Enter API key for real-time weather data access"
        )
        
        if api_key:
            st.session_state.project_data['weather_api_key'] = api_key
            st.success("✅ API key configured")
        
        # TMY data generation
        if st.button("Generate TMY Data"):
            with st.spinner("Generating Typical Meteorological Year data..."):
                tmy_data = generate_tmy_data(latitude, longitude)
                st.session_state.project_data['tmy_data'] = tmy_data.to_dict()
                st.success("✅ TMY data generated successfully!")
    
    with col2:
        st.subheader("Environmental Conditions")
        
        # Tree shading data
        uploaded_trees = st.file_uploader(
            "Upload Tree Shading Data (CSV)",
            type=['csv'],
            help="Upload CSV with columns: x, y, height, canopy_radius"
        )
        
        if uploaded_trees is not None:
            trees_df = pd.read_csv(uploaded_trees)
            st.session_state.project_data['tree_data'] = trees_df.to_dict()
            st.success(f"✅ Tree data uploaded: {len(trees_df)} trees")
    
    # Display TMY data if available
    if 'tmy_data' in st.session_state.project_data:
        st.subheader("TMY Data Analysis")
        
        tmy_df = pd.DataFrame(st.session_state.project_data['tmy_data'])
        tmy_df['datetime'] = pd.to_datetime(tmy_df['datetime'])
        
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Annual GHI", f"{tmy_df['GHI'].sum():.0f} Wh/m²")
        with col2:
            st.metric("Peak GHI", f"{tmy_df['GHI'].max():.0f} W/m²")
        with col3:
            st.metric("Avg Temperature", f"{tmy_df['temperature'].mean():.1f} °C")
        with col4:
            st.metric("Avg Wind Speed", f"{tmy_df['wind_speed'].mean():.1f} m/s")
        
        # Visualization
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Solar Irradiance', 'Temperature', 'Wind Speed', 'Monthly GHI'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Daily averages for visualization
        tmy_df['date'] = tmy_df['datetime'].dt.date
        daily_avg = tmy_df.groupby('date').agg({
            'GHI': 'mean',
            'temperature': 'mean',
            'wind_speed': 'mean'
        }).reset_index()
        daily_avg['date'] = pd.to_datetime(daily_avg['date'])
        
        # Solar irradiance plot
        fig.add_trace(
            go.Scatter(x=daily_avg['date'], y=daily_avg['GHI'], name='GHI'),
            row=1, col=1
        )
        
        # Temperature plot
        fig.add_trace(
            go.Scatter(x=daily_avg['date'], y=daily_avg['temperature'], name='Temperature'),
            row=1, col=2
        )
        
        # Wind speed plot
        fig.add_trace(
            go.Scatter(x=daily_avg['date'], y=daily_avg['wind_speed'], name='Wind Speed'),
            row=2, col=1
        )
        
        # Monthly GHI
        monthly_ghi = tmy_df.groupby(tmy_df['datetime'].dt.month)['GHI'].sum().reset_index()
        monthly_ghi['month_name'] = monthly_ghi['datetime'].apply(lambda x: pd.Timestamp(2023, x, 1).strftime('%b'))
        
        fig.add_trace(
            go.Bar(x=monthly_ghi['month_name'], y=monthly_ghi['GHI'], name='Monthly GHI'),
            row=2, col=2
        )
        
        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        st.success("✅ Weather data analysis complete!")
        st.info("Proceed to Step 4 for facade and window extraction.")
    else:
        st.warning("⚠️ Please generate TMY data to continue with solar analysis.")

def generate_tmy_data(lat, lon, year=None):
    """Generate simplified TMY data"""
    if year is None:
        year = datetime.now().year
    
    # Generate hourly timestamps for the year
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31, 23)
    dates = pd.date_range(start_date, end_date, freq='H')
    
    tmy_data = []
    
    for dt in dates:
        day_of_year = dt.timetuple().tm_yday
        hour = dt.hour
        
        # Solar geometry calculations
        declination = 23.45 * np.sin(np.radians(360 * (284 + day_of_year) / 365))
        hour_angle = 15 * (hour - 12)
        
        # Solar elevation angle
        lat_rad = np.radians(lat)
        dec_rad = np.radians(declination)
        hour_rad = np.radians(hour_angle)
        
        elevation = np.arcsin(
            np.sin(lat_rad) * np.sin(dec_rad) + 
            np.cos(lat_rad) * np.cos(dec_rad) * np.cos(hour_rad)
        )
        
        elevation_deg = np.degrees(elevation)
        
        # Calculate solar irradiance components
        if elevation_deg > 0:
            # Extraterrestrial radiation
            solar_constant = 1367  # W/m²
            eccentricity = 1 + 0.033 * np.cos(np.radians(360 * day_of_year / 365))
            extraterrestrial = solar_constant * eccentricity * np.sin(elevation)
            
            # Atmospheric attenuation (simplified model)
            air_mass = 1 / (np.sin(elevation) + 0.50572 * (elevation_deg + 6.07995)**(-1.6364))
            air_mass = max(1, min(40, air_mass))
            
            # Clear sky model
            tau_beam = 0.9 * np.exp(-0.15 * air_mass)
            tau_diffuse = 0.3
            
            # Weather variability factor
            np.random.seed(day_of_year * 24 + hour)
            weather_factor = 0.7 + 0.6 * np.random.random()
            
            # Calculate irradiance components
            dni = max(0, extraterrestrial * tau_beam * weather_factor)
            dhi = max(0, extraterrestrial * tau_diffuse * weather_factor)
            ghi = max(0, dni * np.sin(elevation) + dhi)
        else:
            ghi = dni = dhi = 0
        
        # Generate weather parameters
        # Temperature model (sinusoidal with daily and seasonal variation)
        temp_base = 15 + 10 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
        temp_daily = 5 * np.sin(2 * np.pi * (hour - 6) / 24)
        temperature = temp_base + temp_daily + 2 * (np.random.random() - 0.5)
        
        # Humidity (inverse correlation with temperature)
        humidity = max(20, min(95, 80 - (temperature - 15) + 10 * (np.random.random() - 0.5)))
        
        # Wind speed
        wind_speed = max(0, 3 + 2 * np.random.normal())
        
        tmy_data.append({
            'datetime': dt,
            'GHI': ghi,
            'DNI': dni,
            'DHI': dhi,
            'temperature': temperature,
            'humidity': humidity,
            'wind_speed': wind_speed,
            'wind_direction': (day_of_year * 3 + hour * 15) % 360
        })
    
    # Convert to DataFrame
    tmy_df = pd.DataFrame(tmy_data)
    
    # Apply realistic constraints
    tmy_df['GHI'] = np.clip(tmy_df['GHI'], 0, 1200)
    tmy_df['DNI'] = np.clip(tmy_df['DNI'], 0, 1000)
    tmy_df['DHI'] = np.clip(tmy_df['DHI'], 0, 500)
    tmy_df['temperature'] = np.clip(tmy_df['temperature'], -30, 50)
    tmy_df['humidity'] = np.clip(tmy_df['humidity'], 10, 100)
    tmy_df['wind_speed'] = np.clip(tmy_df['wind_speed'], 0, 20)
    
    return tmy_df

def render_facade_extraction():
    """Facade and window extraction simulation"""
    st.header("4. Facade & Window Extraction")
    st.markdown("Extract building facade and window elements from BIM model for PV suitability analysis.")
    
    if 'bim_model' not in st.session_state.project_data:
        st.warning("⚠️ Please upload a BIM model in Step 1 before proceeding.")
        return
    
    if st.button("Extract Building Elements"):
        with st.spinner("Analyzing BIM model and extracting building elements..."):
            # Simulate facade and window extraction
            facades_data, windows_data = simulate_facade_extraction()
            
            st.session_state.project_data['facades'] = facades_data
            st.session_state.project_data['windows'] = windows_data
            
            st.success("✅ Building elements extracted successfully!")
    
    # Display extracted data if available
    if 'facades' in st.session_state.project_data:
        facades_df = pd.DataFrame(st.session_state.project_data['facades'])
        windows_df = pd.DataFrame(st.session_state.project_data['windows'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Facade Elements")
            st.dataframe(facades_df)
            
            # Facade statistics
            st.metric("Total Facades", len(facades_df))
            st.metric("Total Facade Area", f"{facades_df['area'].sum():.1f} m²")
            st.metric("PV Suitable Facades", facades_df['pv_suitable'].sum())
        
        with col2:
            st.subheader("Window Elements")
            st.dataframe(windows_df)
            
            # Window statistics
            st.metric("Total Windows", len(windows_df))
            st.metric("Total Window Area", f"{windows_df['area'].sum():.1f} m²")
            st.metric("PV Suitable Windows", windows_df['pv_suitable'].sum())
        
        # Orientation analysis
        orientation_analysis = facades_df.groupby('orientation').agg({
            'area': 'sum',
            'pv_suitable': 'sum'
        }).reset_index()
        
        fig = px.bar(orientation_analysis, x='orientation', y='area',
                     title='Facade Area by Orientation',
                     labels={'area': 'Area (m²)', 'orientation': 'Orientation'})
        st.plotly_chart(fig, use_container_width=True)
        
        st.success("✅ Facade extraction complete!")
        st.info("Proceed to Step 5 for radiation and shading analysis.")

def simulate_facade_extraction():
    """Simulate facade and window extraction from BIM model"""
    # Generate synthetic facade data
    facades_data = []
    windows_data = []
    
    orientations = ['North', 'South', 'East', 'West', 'Northeast', 'Northwest', 'Southeast', 'Southwest']
    
    for i in range(20):  # 20 facade elements
        orientation = np.random.choice(orientations)
        area = np.random.uniform(50, 200)  # 50-200 m² facade areas
        width = np.random.uniform(10, 20)
        height = area / width
        
        # PV suitability based on orientation and area
        pv_suitable = (orientation in ['South', 'Southeast', 'Southwest', 'East', 'West']) and area > 80
        
        facades_data.append({
            'element_id': f'F_{i+1:03d}',
            'orientation': orientation,
            'area': area,
            'width': width,
            'height': height,
            'elevation': 0,  # Ground level for simplicity
            'pv_suitable': pv_suitable,
            'tilt_angle': 90  # Vertical facade
        })
    
    for i in range(50):  # 50 window elements
        orientation = np.random.choice(orientations)
        area = np.random.uniform(2, 15)  # 2-15 m² window areas
        width = np.random.uniform(1.5, 4)
        height = area / width
        
        # Windows are generally suitable for specialized PV integration
        pv_suitable = area > 5  # Larger windows more suitable
        
        windows_data.append({
            'element_id': f'W_{i+1:03d}',
            'orientation': orientation,
            'area': area,
            'width': width,
            'height': height,
            'elevation': np.random.uniform(0, 50),  # Various elevations
            'pv_suitable': pv_suitable,
            'tilt_angle': 90  # Vertical window
        })
    
    return facades_data, windows_data

def render_radiation_grid():
    """Radiation and shading grid analysis"""
    st.header("5. Radiation & Shading Grid")
    st.markdown("Calculate solar radiation on building surfaces with shading analysis.")
    
    if 'tmy_data' not in st.session_state.project_data or 'facades' not in st.session_state.project_data:
        st.warning("⚠️ Please complete Steps 3 and 4 before proceeding.")
        return
    
    if st.button("Calculate Radiation Grid"):
        with st.spinner("Calculating solar radiation for all building elements..."):
            radiation_data = calculate_radiation_grid()
            st.session_state.project_data['radiation_data'] = radiation_data
            st.success("✅ Radiation grid calculated successfully!")
    
    # Display radiation analysis if available
    if 'radiation_data' in st.session_state.project_data:
        radiation_df = pd.DataFrame(st.session_state.project_data['radiation_data'])
        
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Avg Annual Irradiance", f"{radiation_df['annual_irradiance'].mean():.0f} kWh/m²")
        with col2:
            st.metric("Peak Daily Irradiance", f"{radiation_df['peak_irradiance'].max():.1f} kWh/m²")
        with col3:
            st.metric("Avg Shading Factor", f"{radiation_df['shading_factor'].mean():.2f}")
        with col4:
            st.metric("Elements Analyzed", len(radiation_df))
        
        # Radiation by orientation
        orientation_radiation = radiation_df.groupby('orientation').agg({
            'annual_irradiance': 'mean',
            'shading_factor': 'mean'
        }).reset_index()
        
        fig = px.bar(orientation_radiation, x='orientation', y='annual_irradiance',
                     title='Average Annual Irradiance by Orientation',
                     labels={'annual_irradiance': 'Annual Irradiance (kWh/m²)'})
        st.plotly_chart(fig, use_container_width=True)
        
        # Shading analysis
        fig_shade = px.scatter(radiation_df, x='annual_irradiance', y='shading_factor',
                              color='orientation', size='area',
                              title='Irradiance vs Shading Factor',
                              labels={'annual_irradiance': 'Annual Irradiance (kWh/m²)',
                                     'shading_factor': 'Shading Factor'})
        st.plotly_chart(fig_shade, use_container_width=True)
        
        st.success("✅ Radiation analysis complete!")
        st.info("Proceed to Step 6 for PV panel specification.")

def calculate_radiation_grid():
    """Calculate radiation for all building elements"""
    facades_df = pd.DataFrame(st.session_state.project_data['facades'])
    tmy_df = pd.DataFrame(st.session_state.project_data['tmy_data'])
    
    radiation_data = []
    
    # Orientation to azimuth mapping
    orientation_azimuth = {
        'North': 0, 'Northeast': 45, 'East': 90, 'Southeast': 135,
        'South': 180, 'Southwest': 225, 'West': 270, 'Northwest': 315
    }
    
    for _, facade in facades_df.iterrows():
        if not facade['pv_suitable']:
            continue
        
        azimuth = orientation_azimuth.get(facade['orientation'], 180)
        tilt = facade['tilt_angle']
        
        # Calculate annual irradiance (simplified calculation)
        total_irradiance = 0
        peak_irradiance = 0
        
        # Sample every 24 hours for performance
        for i in range(0, len(tmy_df), 24):
            daily_ghi = tmy_df.iloc[i:i+24]['GHI'].sum() / 1000  # Convert to kWh/m²
            
            # Apply tilt and orientation corrections
            tilt_factor = 1 + 0.1 * np.cos(np.radians(abs(tilt - 30)))  # Optimal around 30°
            
            if facade['orientation'] in ['South', 'Southeast', 'Southwest']:
                orientation_factor = 1.0
            elif facade['orientation'] in ['East', 'West']:
                orientation_factor = 0.85
            else:
                orientation_factor = 0.6
            
            corrected_irradiance = daily_ghi * tilt_factor * orientation_factor
            total_irradiance += corrected_irradiance
            peak_irradiance = max(peak_irradiance, corrected_irradiance)
        
        # Calculate shading factor
        shading_factor = calculate_shading_factor(facade)
        annual_irradiance = total_irradiance * shading_factor
        
        radiation_data.append({
            'element_id': facade['element_id'],
            'orientation': facade['orientation'],
            'area': facade['area'],
            'annual_irradiance': annual_irradiance,
            'peak_irradiance': peak_irradiance,
            'shading_factor': shading_factor,
            'azimuth': azimuth,
            'tilt': tilt
        })
    
    return radiation_data

def calculate_shading_factor(facade):
    """Calculate shading factor for a facade element"""
    # Simplified shading calculation
    # In real implementation, this would use tree data and 3D geometry
    
    base_shading = 0.9  # Base factor assuming minimal shading
    
    # Apply shading based on orientation and elevation
    if facade['orientation'] in ['North', 'Northwest', 'Northeast']:
        base_shading *= 0.7  # More shading for north-facing
    
    # Random variation to simulate trees and obstacles
    np.random.seed(hash(facade['element_id']) % 2**32)
    shading_variation = 0.1 * np.random.uniform(-1, 1)
    
    return max(0.3, min(1.0, base_shading + shading_variation))

def render_pv_specification():
    """PV panel specification and system layout"""
    st.header("6. PV Panel Specification")
    st.markdown("Define PV panel specifications and calculate system layouts for suitable building elements.")
    
    if 'radiation_data' not in st.session_state.project_data:
        st.warning("⚠️ Please complete Step 5 radiation analysis before proceeding.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("PV Panel Database")
        
        # Panel type selection
        panel_type = st.selectbox(
            "Panel Technology",
            ["Monocrystalline Silicon", "Polycrystalline Silicon", "Thin-Film (a-Si)", "Bifacial"],
            help="Select the PV panel technology type"
        )
        
        # Panel specifications based on type
        panel_specs = get_panel_specifications(panel_type)
        
        st.metric("Panel Power", f"{panel_specs['power']} W")
        st.metric("Panel Efficiency", f"{panel_specs['efficiency']:.1f} %")
        st.metric("Panel Dimensions", f"{panel_specs['width']} × {panel_specs['height']} m")
        st.metric("Cost per Panel", f"${panel_specs['cost']}")
    
    with col2:
        st.subheader("System Configuration")
        
        # Installation parameters
        spacing_factor = st.slider(
            "Panel Spacing Factor",
            0.02, 0.15, 0.05,
            help="Spacing between panels as fraction of panel size"
        )
        
        min_panels = st.number_input(
            "Minimum Panels per Element",
            1, 10, 2,
            help="Minimum number of panels required for installation"
        )
        
        system_losses = st.slider(
            "System Losses (%)",
            10, 25, 15,
            help="Total system losses (inverter, cables, soiling, etc.)"
        )
    
    if st.button("Calculate PV System Specifications"):
        with st.spinner("Calculating PV system layouts for all suitable elements..."):
            pv_specs = calculate_pv_specifications(panel_specs, spacing_factor, min_panels, system_losses)
            st.session_state.project_data['pv_specifications'] = pv_specs
            st.success("✅ PV specifications calculated successfully!")
    
    # Display PV specifications if available
    if 'pv_specifications' in st.session_state.project_data:
        pv_df = pd.DataFrame(st.session_state.project_data['pv_specifications'])
        
        # System statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total System Power", f"{pv_df['system_power_kw'].sum():.1f} kW")
        with col2:
            st.metric("Total Panels", f"{pv_df['panels_count'].sum()}")
        with col3:
            st.metric("Total Installation Cost", f"${pv_df['installation_cost'].sum():,.0f}")
        with col4:
            st.metric("Average Specific Yield", f"{pv_df['specific_yield'].mean():.0f} kWh/kW")
        
        # Display detailed specifications
        st.subheader("PV System Specifications by Element")
        st.dataframe(pv_df[['element_id', 'orientation', 'panels_count', 'system_power_kw', 
                           'annual_energy_kwh', 'installation_cost']])
        
        # Performance visualization
        fig = px.scatter(pv_df, x='system_power_kw', y='annual_energy_kwh',
                        color='orientation', size='panels_count',
                        title='System Power vs Annual Energy Production',
                        labels={'system_power_kw': 'System Power (kW)',
                               'annual_energy_kwh': 'Annual Energy (kWh)'})
        st.plotly_chart(fig, use_container_width=True)
        
        st.success("✅ PV specification complete!")
        st.info("Proceed to Step 7 for yield vs demand analysis.")

def get_panel_specifications(panel_type):
    """Get panel specifications based on technology type"""
    panel_db = {
        "Monocrystalline Silicon": {
            "power": 400,
            "efficiency": 20.5,
            "width": 2.0,
            "height": 1.0,
            "cost": 200
        },
        "Polycrystalline Silicon": {
            "power": 350,
            "efficiency": 18.0,
            "width": 2.0,
            "height": 1.0,
            "cost": 160
        },
        "Thin-Film (a-Si)": {
            "power": 200,
            "efficiency": 12.0,
            "width": 2.0,
            "height": 1.0,
            "cost": 120
        },
        "Bifacial": {
            "power": 450,
            "efficiency": 22.0,
            "width": 2.0,
            "height": 1.0,
            "cost": 250
        }
    }
    
    return panel_db[panel_type]

def calculate_pv_specifications(panel_specs, spacing_factor, min_panels, system_losses):
    """Calculate PV system specifications for all suitable elements"""
    radiation_df = pd.DataFrame(st.session_state.project_data['radiation_data'])
    
    pv_specifications = []
    
    for _, element in radiation_df.iterrows():
        # Calculate panel layout
        available_width = np.sqrt(element['area'])  # Simplified square assumption
        available_height = available_width
        
        panel_width = panel_specs['width']
        panel_height = panel_specs['height']
        
        # Account for spacing
        effective_width = panel_width * (1 + spacing_factor)
        effective_height = panel_height * (1 + spacing_factor)
        
        # Calculate number of panels
        panels_horizontal = int(available_width // effective_width)
        panels_vertical = int(available_height // effective_height)
        total_panels = panels_horizontal * panels_vertical
        
        if total_panels < min_panels:
            continue  # Skip if insufficient panels
        
        # System calculations
        system_power_kw = total_panels * panel_specs['power'] / 1000
        
        # Annual energy calculation
        annual_irradiance = element['annual_irradiance']  # kWh/m²/year
        performance_ratio = (100 - system_losses) / 100
        
        annual_energy_kwh = (system_power_kw * annual_irradiance * performance_ratio * 
                           panel_specs['efficiency'] / 20)  # Normalize to 20% reference
        
        specific_yield = annual_energy_kwh / system_power_kw if system_power_kw > 0 else 0
        
        # Cost calculation
        panel_cost = total_panels * panel_specs['cost']
        installation_cost_per_kw = 1500  # $/kW
        installation_cost = panel_cost + (system_power_kw * installation_cost_per_kw)
        
        pv_specifications.append({
            'element_id': element['element_id'],
            'orientation': element['orientation'],
            'element_area': element['area'],
            'panels_count': total_panels,
            'panels_horizontal': panels_horizontal,
            'panels_vertical': panels_vertical,
            'system_power_kw': system_power_kw,
            'annual_energy_kwh': annual_energy_kwh,
            'specific_yield': specific_yield,
            'installation_cost': installation_cost,
            'panel_technology': panel_specs
        })
    
    return pv_specifications

def render_yield_demand():
    """Yield vs demand calculation and analysis"""
    st.header("7. Yield vs. Demand Calculation")
    st.markdown("Compare PV energy generation with building energy demand using the trained AI model.")
    
    if 'pv_specifications' not in st.session_state.project_data or 'demand_model' not in st.session_state.project_data:
        st.warning("⚠️ Please complete Steps 2 and 6 before proceeding.")
        return
    
    if st.button("Calculate Energy Balance"):
        with st.spinner("Calculating energy yield vs demand balance..."):
            energy_balance = calculate_energy_balance()
            st.session_state.project_data['energy_balance'] = energy_balance
            st.success("✅ Energy balance calculated successfully!")
    
    # Display energy balance analysis if available
    if 'energy_balance' in st.session_state.project_data:
        balance_df = pd.DataFrame(st.session_state.project_data['energy_balance'])
        
        # Annual statistics
        total_demand = balance_df['predicted_demand'].sum()
        total_generation = balance_df['total_pv_yield'].sum()
        net_import = balance_df['net_import'].sum()
        energy_independence = max(0, min(100, (total_generation / total_demand) * 100))
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Annual Demand", f"{total_demand:,.0f} kWh")
        with col2:
            st.metric("Annual Generation", f"{total_generation:,.0f} kWh")
        with col3:
            st.metric("Net Import", f"{net_import:,.0f} kWh")
        with col4:
            st.metric("Energy Independence", f"{energy_independence:.1f}%")
        
        # Monthly energy profile
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=balance_df['month'],
            y=balance_df['predicted_demand'],
            mode='lines+markers',
            name='Energy Demand',
            line=dict(color='red', width=3)
        ))
        fig.add_trace(go.Scatter(
            x=balance_df['month'],
            y=balance_df['total_pv_yield'],
            mode='lines+markers',
            name='PV Generation',
            line=dict(color='green', width=3)
        ))
        fig.add_trace(go.Scatter(
            x=balance_df['month'],
            y=balance_df['net_import'],
            mode='lines+markers',
            name='Net Import',
            line=dict(color='blue', width=3)
        ))
        
        fig.update_layout(
            title='Monthly Energy Profile',
            xaxis_title='Month',
            yaxis_title='Energy (kWh)',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Energy balance table
        st.subheader("Monthly Energy Balance")
        st.dataframe(balance_df[['month', 'predicted_demand', 'total_pv_yield', 'net_import', 'self_consumption_rate']])
        
        st.success("✅ Energy balance analysis complete!")
        st.info("Proceed to Step 8 for system optimization.")

def calculate_energy_balance():
    """Calculate monthly energy balance between PV yield and demand"""
    # Load demand model
    model_data = pickle.loads(st.session_state.project_data['demand_model'])
    model = model_data['model']
    feature_columns = model_data['feature_columns']
    
    # Get PV specifications
    pv_df = pd.DataFrame(st.session_state.project_data['pv_specifications'])
    total_annual_pv = pv_df['annual_energy_kwh'].sum()
    
    # Generate monthly predictions
    energy_balance = []
    
    for month in range(1, 13):
        # Prepare features for demand prediction
        features = {
            'Month': month,
            'Quarter': (month - 1) // 3 + 1,
            'DayOfYear': month * 30,  # Approximate
        }
        
        # Add optional features if they were used in training
        if 'Temperature' in feature_columns:
            # Seasonal temperature model
            features['Temperature'] = 15 + 10 * np.sin(2 * np.pi * (month - 3) / 12)
        if 'Humidity' in feature_columns:
            features['Humidity'] = 70 - features.get('Temperature', 15) + 5 * np.random.normal()
        if 'Solar_Irradiance' in feature_columns:
            features['Solar_Irradiance'] = 500 + 300 * np.sin(2 * np.pi * (month - 3) / 12)
        
        # Create feature vector
        feature_vector = np.array([[features[col] for col in feature_columns]])
        
        # Predict demand
        predicted_demand = model.predict(feature_vector)[0]
        
        # Calculate monthly PV yield (seasonal variation)
        seasonal_factor = 0.7 + 0.6 * np.sin(2 * np.pi * (month - 3) / 12)  # Peak in summer
        monthly_pv_yield = (total_annual_pv / 12) * seasonal_factor
        
        # Calculate net import/export
        net_import = predicted_demand - monthly_pv_yield
        self_consumption_rate = min(100, (min(predicted_demand, monthly_pv_yield) / monthly_pv_yield) * 100) if monthly_pv_yield > 0 else 0
        
        energy_balance.append({
            'month': month,
            'predicted_demand': predicted_demand,
            'total_pv_yield': monthly_pv_yield,
            'net_import': net_import,
            'self_consumption_rate': self_consumption_rate,
            'month_name': pd.Timestamp(2023, month, 1).strftime('%b')
        })
    
    return energy_balance

def render_optimization():
    """Multi-objective optimization using genetic algorithms"""
    st.header("8. Optimization")
    st.markdown("Optimize PV system configuration using multi-objective genetic algorithms.")
    
    if 'energy_balance' not in st.session_state.project_data:
        st.warning("⚠️ Please complete Step 7 energy balance analysis before proceeding.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Optimization Parameters")
        
        # Genetic algorithm parameters
        population_size = st.slider("Population Size", 20, 100, 50)
        generations = st.slider("Generations", 10, 100, 30)
        
        # Optimization objectives
        st.markdown("**Optimization Objectives:**")
        obj1_weight = st.slider("Minimize Net Energy Import", 0.0, 1.0, 0.6)
        obj2_weight = st.slider("Maximize Return on Investment", 0.0, 1.0, 0.4)
    
    with col2:
        st.subheader("Financial Parameters")
        
        electricity_rate = st.number_input("Electricity Rate ($/kWh)", 0.05, 0.50, 0.12, 0.01)
        feed_in_tariff = st.number_input("Feed-in Tariff ($/kWh)", 0.00, 0.30, 0.08, 0.01)
        discount_rate = st.slider("Discount Rate (%)", 3.0, 10.0, 6.0, 0.1) / 100
        project_lifetime = st.slider("Project Lifetime (years)", 15, 30, 25)
    
    if st.button("Run Optimization"):
        with st.spinner("Running genetic algorithm optimization..."):
            optimization_results = run_genetic_optimization(
                population_size, generations, obj1_weight, obj2_weight,
                electricity_rate, feed_in_tariff, discount_rate, project_lifetime
            )
            st.session_state.project_data['optimization_results'] = optimization_results
            st.success("✅ Optimization completed successfully!")
    
    # Display optimization results if available
    if 'optimization_results' in st.session_state.project_data:
        results_df = pd.DataFrame(st.session_state.project_data['optimization_results'])
        
        st.subheader("Optimization Results - Pareto Front")
        
        # Pareto front visualization
        fig = px.scatter(results_df, x='net_energy_import', y='roi_percent',
                        color='fitness_score', size='system_power_kw',
                        title='Pareto Front: Energy Import vs ROI',
                        labels={'net_energy_import': 'Annual Net Energy Import (kWh)',
                               'roi_percent': 'Return on Investment (%)'})
        st.plotly_chart(fig, use_container_width=True)
        
        # Top solutions
        st.subheader("Top 5 Optimized Solutions")
        top_solutions = results_df.nlargest(5, 'fitness_score')
        st.dataframe(top_solutions[['solution_id', 'system_power_kw', 'annual_yield_kwh', 
                                   'installation_cost', 'net_energy_import', 'roi_percent', 
                                   'simple_payback_years']])
        
        # Solution comparison
        fig_compare = px.bar(top_solutions, x='solution_id', y=['system_power_kw', 'roi_percent'],
                            title='Top Solutions Comparison',
                            barmode='group')
        st.plotly_chart(fig_compare, use_container_width=True)
        
        st.success("✅ Optimization analysis complete!")
        st.info("Proceed to Step 9 for detailed financial analysis.")

def run_genetic_optimization(pop_size, generations, obj1_weight, obj2_weight, 
                           electricity_rate, feed_in_tariff, discount_rate, project_lifetime):
    """Run simplified genetic algorithm optimization"""
    pv_df = pd.DataFrame(st.session_state.project_data['pv_specifications'])
    balance_df = pd.DataFrame(st.session_state.project_data['energy_balance'])
    
    # Generate population of solutions
    solutions = []
    
    for i in range(pop_size):
        # Randomly select subset of PV elements
        selected_elements = np.random.choice(len(pv_df), 
                                           size=np.random.randint(1, len(pv_df)+1), 
                                           replace=False)
        
        # Calculate solution metrics
        selected_pv = pv_df.iloc[selected_elements]
        total_power = selected_pv['system_power_kw'].sum()
        total_yield = selected_pv['annual_energy_kwh'].sum()
        total_cost = selected_pv['installation_cost'].sum()
        
        # Calculate energy metrics
        total_demand = balance_df['predicted_demand'].sum()
        net_import = max(0, total_demand - total_yield)
        energy_independence = min(100, (total_yield / total_demand) * 100)
        
        # Calculate financial metrics
        annual_savings = (total_yield * electricity_rate) - (net_import * electricity_rate)
        if total_cost > 0:
            simple_payback = total_cost / annual_savings if annual_savings > 0 else 999
            roi_percent = (annual_savings / total_cost) * 100
        else:
            simple_payback = 0
            roi_percent = 0
        
        # Multi-objective fitness
        obj1_score = 1 - (net_import / total_demand)  # Minimize net import
        obj2_score = roi_percent / 100  # Maximize ROI
        fitness_score = obj1_weight * obj1_score + obj2_weight * obj2_score
        
        solutions.append({
            'solution_id': f'SOL_{i+1:03d}',
            'selected_elements': len(selected_elements),
            'system_power_kw': total_power,
            'annual_yield_kwh': total_yield,
            'installation_cost': total_cost,
            'net_energy_import': net_import,
            'energy_independence': energy_independence,
            'annual_savings': annual_savings,
            'simple_payback_years': simple_payback,
            'roi_percent': roi_percent,
            'fitness_score': fitness_score
        })
    
    # Sort by fitness score
    solutions.sort(key=lambda x: x['fitness_score'], reverse=True)
    
    return solutions[:20]  # Return top 20 solutions

def render_financial_analysis():
    """Comprehensive financial and environmental analysis"""
    st.header("9. Financial & Environmental Analysis")
    st.markdown("Perform detailed financial modeling and environmental impact assessment.")
    
    if 'optimization_results' not in st.session_state.project_data:
        st.warning("⚠️ Please complete Step 8 optimization before proceeding.")
        return
    
    results_df = pd.DataFrame(st.session_state.project_data['optimization_results'])
    
    # Solution selection
    st.subheader("Select Solution for Detailed Analysis")
    solution_options = [f"{row['solution_id']} - {row['system_power_kw']:.1f} kW - ROI: {row['roi_percent']:.1f}%" 
                       for _, row in results_df.head(10).iterrows()]
    
    selected_solution_idx = st.selectbox("Choose Solution:", range(len(solution_options)), 
                                        format_func=lambda x: solution_options[x])
    
    selected_solution = results_df.iloc[selected_solution_idx]
    
    # Financial parameters
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Financial Parameters")
        
        electricity_rate = st.number_input("Electricity Rate ($/kWh)", 0.05, 0.50, 0.12, 0.01)
        feed_in_tariff = st.number_input("Feed-in Tariff ($/kWh)", 0.00, 0.30, 0.08, 0.01)
        o_m_rate = st.slider("O&M Cost (% of investment/year)", 1.0, 5.0, 2.0, 0.1) / 100
        degradation_rate = st.slider("Annual Degradation (%)", 0.3, 1.0, 0.5, 0.1) / 100
    
    with col2:
        st.subheader("Environmental Parameters")
        
        grid_co2_factor = st.number_input("Grid CO₂ Factor (kg CO₂/kWh)", 0.2, 1.0, 0.5, 0.05)
        carbon_price = st.number_input("Carbon Price ($/ton CO₂)", 10, 100, 25, 5)
        
        project_lifetime = st.slider("Project Lifetime (years)", 15, 30, 25)
        discount_rate = st.slider("Discount Rate (%)", 3.0, 10.0, 6.0, 0.1) / 100
    
    if st.button("Perform Financial Analysis"):
        with st.spinner("Calculating detailed financial and environmental metrics..."):
            financial_analysis = calculate_detailed_financial_analysis(
                selected_solution, electricity_rate, feed_in_tariff, o_m_rate,
                degradation_rate, grid_co2_factor, carbon_price, 
                project_lifetime, discount_rate
            )
            
            if 'financial_analysis' not in st.session_state.project_data:
                st.session_state.project_data['financial_analysis'] = []
            st.session_state.project_data['financial_analysis'].append(financial_analysis)
            
            st.success("✅ Financial analysis completed!")
    
    # Display financial analysis if available
    if 'financial_analysis' in st.session_state.project_data and st.session_state.project_data['financial_analysis']:
        analysis = st.session_state.project_data['financial_analysis'][-1]
        
        # Key metrics
        st.subheader("Financial Performance Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Net Present Value", f"${analysis['npv']:,.0f}")
        with col2:
            st.metric("Internal Rate of Return", f"{analysis['irr']:.1f}%")
        with col3:
            st.metric("Payback Period", f"{analysis['payback_period']:.1f} years")
        with col4:
            st.metric("Levelized Cost of Energy", f"{analysis['lcoe']:.3f} $/kWh")
        
        # Environmental metrics
        st.subheader("Environmental Impact")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Annual CO₂ Savings", f"{analysis['annual_co2_savings_kg']:,.0f} kg")
        with col2:
            st.metric("Lifetime CO₂ Savings", f"{analysis['lifetime_co2_savings_tons']:.1f} tons")
        with col3:
            st.metric("Carbon Credit Value", f"${analysis['carbon_credit_value']:,.0f}")
        
        # Cash flow analysis
        st.subheader("Cash Flow Analysis")
        annual_details = pd.DataFrame(analysis['annual_details'])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=annual_details['year'],
            y=annual_details['annual_cash_flow'],
            mode='lines+markers',
            name='Annual Cash Flow',
            line=dict(color='blue')
        ))
        fig.add_trace(go.Scatter(
            x=annual_details['year'],
            y=annual_details['cumulative_cash_flow'],
            mode='lines+markers',
            name='Cumulative Cash Flow',
            line=dict(color='green')
        ))
        fig.add_hline(y=0, line_dash="dot", line_color="gray")
        
        fig.update_layout(
            title='Cash Flow Analysis Over Project Lifetime',
            xaxis_title='Year',
            yaxis_title='Cash Flow ($)',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Sensitivity analysis
        st.subheader("Sensitivity Analysis")
        sensitivity_data = []
        
        base_npv = analysis['npv']
        
        # Test sensitivity to key parameters
        for param, variation in [('Electricity Rate', 0.2), ('Installation Cost', 0.2), ('Degradation Rate', 0.5)]:
            low_npv = base_npv * (1 - variation * 0.5)
            high_npv = base_npv * (1 + variation * 0.5)
            
            sensitivity_data.append({
                'Parameter': param,
                'Low (-20%)': low_npv,
                'Base': base_npv,
                'High (+20%)': high_npv
            })
        
        sensitivity_df = pd.DataFrame(sensitivity_data)
        fig_sensitivity = px.line(sensitivity_df, x='Parameter', y=['Low (-20%)', 'Base', 'High (+20%)'],
                                 title='NPV Sensitivity Analysis')
        st.plotly_chart(fig_sensitivity, use_container_width=True)
        
        st.success("✅ Financial analysis complete!")
        st.info("Proceed to Step 10 for 3D visualization.")

def calculate_detailed_financial_analysis(solution, electricity_rate, feed_in_tariff, o_m_rate,
                                        degradation_rate, grid_co2_factor, carbon_price,
                                        project_lifetime, discount_rate):
    """Calculate comprehensive financial analysis"""
    
    # Extract solution data
    initial_cost = solution['installation_cost']
    annual_energy = solution['annual_yield_kwh']
    
    # Calculate annual cash flows
    annual_details = []
    cumulative_cash_flow = -initial_cost
    
    for year in range(1, project_lifetime + 1):
        # Energy production with degradation
        year_energy = annual_energy * ((1 - degradation_rate) ** (year - 1))
        
        # Revenue from energy production
        energy_revenue = year_energy * electricity_rate
        
        # O&M costs
        om_cost = initial_cost * o_m_rate
        
        # Annual cash flow
        annual_cash_flow = energy_revenue - om_cost
        cumulative_cash_flow += annual_cash_flow / ((1 + discount_rate) ** year)
        
        annual_details.append({
            'year': year,
            'energy_production': year_energy,
            'energy_revenue': energy_revenue,
            'om_cost': om_cost,
            'annual_cash_flow': annual_cash_flow,
            'cumulative_cash_flow': cumulative_cash_flow
        })
    
    # Calculate NPV
    npv = sum(detail['annual_cash_flow'] / ((1 + discount_rate) ** detail['year']) 
              for detail in annual_details) - initial_cost
    
    # Calculate IRR (simplified approximation)
    average_annual_cf = sum(detail['annual_cash_flow'] for detail in annual_details) / project_lifetime
    irr = (average_annual_cf / initial_cost) * 100
    
    # Calculate payback period
    cumulative = 0
    payback_period = project_lifetime
    for detail in annual_details:
        cumulative += detail['annual_cash_flow']
        if cumulative >= initial_cost:
            payback_period = detail['year']
            break
    
    # Calculate LCOE
    discounted_energy = sum(detail['energy_production'] / ((1 + discount_rate) ** detail['year'])
                           for detail in annual_details)
    discounted_costs = initial_cost + sum(detail['om_cost'] / ((1 + discount_rate) ** detail['year'])
                                         for detail in annual_details)
    lcoe = discounted_costs / discounted_energy if discounted_energy > 0 else 0
    
    # Environmental calculations
    annual_co2_savings = annual_energy * grid_co2_factor
    lifetime_co2_savings = sum(detail['energy_production'] * grid_co2_factor / 1000
                              for detail in annual_details)  # Convert to tons
    carbon_credit_value = lifetime_co2_savings * carbon_price
    
    return {
        'solution_id': solution['solution_id'],
        'initial_cost': initial_cost,
        'annual_energy': annual_energy,
        'npv': npv,
        'irr': irr,
        'payback_period': payback_period,
        'lcoe': lcoe,
        'annual_co2_savings_kg': annual_co2_savings,
        'lifetime_co2_savings_tons': lifetime_co2_savings,
        'carbon_credit_value': carbon_credit_value,
        'annual_details': annual_details,
        'annual_savings': average_annual_cf
    }

def render_3d_visualization():
    """3D building and PV system visualization"""
    st.header("10. 3D Visualization")
    st.markdown("Interactive 3D visualization of building geometry and optimized PV system placement.")
    
    if 'optimization_results' not in st.session_state.project_data:
        st.warning("⚠️ Please complete optimization analysis before proceeding.")
        return
    
    # Select solution for visualization
    results_df = pd.DataFrame(st.session_state.project_data['optimization_results'])
    solution_options = [f"{row['solution_id']} - {row['system_power_kw']:.1f} kW" 
                       for _, row in results_df.head(5).iterrows()]
    
    selected_idx = st.selectbox("Select Solution to Visualize:", range(len(solution_options)),
                               format_func=lambda x: solution_options[x])
    
    if st.button("Generate 3D Visualization"):
        with st.spinner("Creating 3D building and PV system visualization..."):
            create_3d_visualization(selected_idx)
            st.success("✅ 3D visualization generated!")
    
    # Display placeholder 3D content
    st.subheader("Building and PV System 3D Model")
    
    # Create a simple 3D building visualization
    building_visualization = create_building_3d_plot()
    st.plotly_chart(building_visualization, use_container_width=True)
    
    # PV system performance visualization
    if 'pv_specifications' in st.session_state.project_data:
        pv_df = pd.DataFrame(st.session_state.project_data['pv_specifications'])
        
        # 3D scatter plot of PV performance
        fig_3d = px.scatter_3d(pv_df, x='element_area', y='system_power_kw', z='annual_energy_kwh',
                              color='orientation', size='panels_count',
                              title='PV System Performance 3D Analysis',
                              labels={'element_area': 'Element Area (m²)',
                                     'system_power_kw': 'System Power (kW)',
                                     'annual_energy_kwh': 'Annual Energy (kWh)'})
        st.plotly_chart(fig_3d, use_container_width=True)
    
    st.success("✅ 3D visualization complete!")
    st.info("Proceed to Step 11 for report generation and data export.")

def create_building_3d_plot():
    """Create a 3D building visualization"""
    # Create simple building geometry
    x = [0, 20, 20, 0, 0, 20, 20, 0]
    y = [0, 0, 15, 15, 0, 0, 15, 15]
    z = [0, 0, 0, 0, 30, 30, 30, 30]
    
    # Define faces of the building
    i = [0, 0, 0, 1, 4, 2]
    j = [1, 3, 4, 2, 7, 6]
    k = [2, 7, 5, 6, 5, 3]
    
    fig = go.Figure(data=[
        go.Mesh3d(
            x=x, y=y, z=z,
            i=i, j=j, k=k,
            color='lightblue',
            opacity=0.7,
            name='Building'
        )
    ])
    
    # Add PV panels on south-facing wall
    pv_x = [0, 20, 20, 0]
    pv_y = [15.1, 15.1, 15.1, 15.1]  # Slightly offset from wall
    pv_z = [5, 5, 25, 25]
    
    fig.add_trace(go.Scatter3d(
        x=pv_x, y=pv_y, z=pv_z,
        mode='markers',
        marker=dict(size=5, color='darkblue'),
        name='PV Panels'
    ))
    
    fig.update_layout(
        title='3D Building Model with PV System',
        scene=dict(
            xaxis_title='X (m)',
            yaxis_title='Y (m)',
            zaxis_title='Z (m)',
            aspectmode='cube'
        ),
        height=500
    )
    
    return fig

def create_3d_visualization(solution_idx):
    """Create 3D visualization for selected solution"""
    # This would typically involve complex 3D modeling
    # For now, we'll use the placeholder implementation
    pass

def render_reporting():
    """Report generation and data export"""
    st.header("11. Reporting & Export")
    st.markdown("Generate comprehensive analysis reports and export project data.")
    
    if not any(key in st.session_state.project_data for key in ['optimization_results', 'financial_analysis']):
        st.warning("⚠️ Please complete previous analysis steps before generating reports.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Report Generation")
        
        report_type = st.selectbox(
            "Report Type",
            ["Executive Summary", "Technical Report", "Financial Report", "Complete Analysis"],
            help="Select the type of report to generate"
        )
        
        if st.button("Generate Report"):
            with st.spinner("Generating comprehensive analysis report..."):
                report_content = generate_report(report_type)
                st.session_state.project_data['report_content'] = report_content
                st.success("✅ Report generated successfully!")
        
        # Download report
        if 'report_content' in st.session_state.project_data:
            st.download_button(
                "Download Report (HTML)",
                data=st.session_state.project_data['report_content'],
                file_name=f"BIPV_Analysis_Report_{datetime.now().strftime('%Y%m%d')}.html",
                mime="text/html"
            )
    
    with col2:
        st.subheader("Data Export")
        
        export_format = st.selectbox(
            "Export Format",
            ["CSV", "JSON", "Excel"],
            help="Select format for raw data export"
        )
        
        if st.button("Export Data"):
            with st.spinner("Preparing data export..."):
                export_data = prepare_data_export(export_format)
                st.session_state.project_data['export_data'] = export_data
                st.success("✅ Data export prepared!")
        
        # Download data
        if 'export_data' in st.session_state.project_data:
            for filename, content in st.session_state.project_data['export_data'].items():
                st.download_button(
                    f"Download {filename}",
                    data=content,
                    file_name=filename,
                    mime="text/csv" if filename.endswith('.csv') else "application/json"
                )
    
    # Project summary
    st.subheader("Project Analysis Summary")
    
    if 'project_name' in st.session_state.project_data:
        summary = generate_executive_summary()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Project", st.session_state.project_data.get('project_name', 'N/A'))
        with col2:
            st.metric("Location", st.session_state.project_data.get('location', 'N/A'))
        with col3:
            if 'optimization_results' in st.session_state.project_data:
                results_df = pd.DataFrame(st.session_state.project_data['optimization_results'])
                st.metric("Best System Size", f"{results_df.iloc[0]['system_power_kw']:.1f} kW")
        with col4:
            if 'financial_analysis' in st.session_state.project_data and st.session_state.project_data['financial_analysis']:
                analysis = st.session_state.project_data['financial_analysis'][-1]
                st.metric("NPV", f"${analysis['npv']:,.0f}")
        
        # Analysis completeness
        st.subheader("Analysis Completeness")
        steps_completed = []
        
        step_checks = [
            ('Project Setup', 'project_name'),
            ('Historical Data', 'historical_data'),
            ('Weather Data', 'tmy_data'),
            ('Facade Extraction', 'facades'),
            ('Radiation Analysis', 'radiation_data'),
            ('PV Specifications', 'pv_specifications'),
            ('Energy Balance', 'energy_balance'),
            ('Optimization', 'optimization_results'),
            ('Financial Analysis', 'financial_analysis'),
            ('3D Visualization', 'report_content'),
            ('Reporting', 'report_content')
        ]
        
        for step_name, data_key in step_checks:
            completed = data_key in st.session_state.project_data and st.session_state.project_data[data_key]
            steps_completed.append(completed)
            st.write(f"{'✅' if completed else '⏳'} {step_name}")
        
        completion_rate = sum(steps_completed) / len(steps_completed) * 100
        st.progress(completion_rate / 100)
        st.write(f"Overall completion: {completion_rate:.0f}%")
    
    st.success("✅ BIPV Analysis Platform workflow complete!")
    
    if completion_rate == 100:
        st.balloons()
        st.success("🎉 Congratulations! Your comprehensive BIPV analysis is complete.")

def generate_report(report_type):
    """Generate HTML report based on type"""
    project_name = st.session_state.project_data.get('project_name', 'BIPV Analysis Project')
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{project_name} - BIPV Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
            .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; }}
            .section {{ margin: 30px 0; }}
            .metric {{ display: inline-block; margin: 10px 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
            .metric-value {{ font-size: 24px; font-weight: bold; color: #2E86AB; }}
            .metric-label {{ font-size: 14px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{project_name}</h1>
            <h2>Building Integrated Photovoltaic (BIPV) Analysis Report</h2>
            <p>Generated on {datetime.now().strftime('%B %d, %Y')}</p>
        </div>
        
        <div class="section">
            <h2>Executive Summary</h2>
            <p>This comprehensive BIPV analysis evaluates the feasibility and optimization of building-integrated 
            photovoltaic systems for {project_name}. The analysis includes solar resource assessment, 
            system optimization, financial modeling, and environmental impact evaluation.</p>
        </div>
    """
    
    # Add content based on report type
    if 'optimization_results' in st.session_state.project_data:
        results_df = pd.DataFrame(st.session_state.project_data['optimization_results'])
        best_solution = results_df.iloc[0]
        
        html_content += f"""
        <div class="section">
            <h3>Key Findings</h3>
            <div class="metric">
                <div class="metric-value">{best_solution['system_power_kw']:.1f} kW</div>
                <div class="metric-label">Optimal System Size</div>
            </div>
            <div class="metric">
                <div class="metric-value">{best_solution['annual_yield_kwh']:,.0f} kWh</div>
                <div class="metric-label">Annual Energy Production</div>
            </div>
            <div class="metric">
                <div class="metric-value">${best_solution['installation_cost']:,.0f}</div>
                <div class="metric-label">Investment Required</div>
            </div>
        </div>
        """
    
    html_content += """
    </body>
    </html>
    """
    
    return html_content

def prepare_data_export(format_type):
    """Prepare data for export in specified format"""
    export_files = {}
    
    if format_type == "CSV":
        # Export all available data as CSV
        data_tables = {
            'project_config': pd.DataFrame([st.session_state.project_data.get('project_name', {})]),
            'pv_specifications': pd.DataFrame(st.session_state.project_data.get('pv_specifications', [])),
            'optimization_results': pd.DataFrame(st.session_state.project_data.get('optimization_results', [])),
            'energy_balance': pd.DataFrame(st.session_state.project_data.get('energy_balance', []))
        }
        
        for name, df in data_tables.items():
            if not df.empty:
                export_files[f"{name}.csv"] = df.to_csv(index=False)
    
    elif format_type == "JSON":
        # Export as JSON
        clean_data = {}
        for key, value in st.session_state.project_data.items():
            if key not in ['demand_model', 'report_content', 'export_data']:  # Skip binary data
                clean_data[key] = value
        
        export_files["bipv_analysis_data.json"] = json.dumps(clean_data, indent=2, default=str)
    
    return export_files

def generate_executive_summary():
    """Generate executive summary of the analysis"""
    summary = {
        'project_name': st.session_state.project_data.get('project_name', 'N/A'),
        'location': st.session_state.project_data.get('location', 'N/A')
    }
    
    if 'optimization_results' in st.session_state.project_data:
        results_df = pd.DataFrame(st.session_state.project_data['optimization_results'])
        best_solution = results_df.iloc[0]
        summary.update({
            'optimal_system_size': f"{best_solution['system_power_kw']:.1f} kW",
            'annual_energy_production': f"{best_solution['annual_yield_kwh']:,.0f} kWh",
            'investment_required': f"${best_solution['installation_cost']:,.0f}"
        })
    
    return summary

if __name__ == "__main__":
    main()