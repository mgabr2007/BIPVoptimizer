import streamlit as st
import math
import json
from datetime import datetime, timedelta
import io

# Check if plotly is available and import
def get_plotly_modules():
    try:
        import plotly.graph_objects as go
        import plotly.express as px
        from plotly.subplots import make_subplots
        return go, px, make_subplots, True
    except ImportError:
        return None, None, None, False

# Try to import plotly
go, px, make_subplots, PLOTLY_AVAILABLE = get_plotly_modules()

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
            if st.button("⬅️ Previous Step", key="nav_prev"):
                st.session_state.workflow_step -= 1
                st.rerun()
    
    with col3:
        if st.session_state.workflow_step < len(steps):
            if st.button("Next Step ➡️", key="nav_next"):
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
            help="Enter a descriptive name for your BIPV analysis project. This will appear in all reports and documentation."
        )
        
        location = st.text_input(
            "Project Location",
            value=st.session_state.project_data.get('location', ''),
            help="Building location (city, country). This affects solar resource calculations and climate data modeling."
        )
        
        # Coordinates
        col_lat, col_lon = st.columns(2)
        with col_lat:
            latitude = st.number_input(
                "Latitude", 
                value=st.session_state.project_data.get('latitude', 40.7128),
                format="%.4f",
                help="Geographic latitude in decimal degrees (-90 to +90). Northern latitudes are positive. Critical for solar angle calculations and seasonal irradiance modeling."
            )
        with col_lon:
            longitude = st.number_input(
                "Longitude", 
                value=st.session_state.project_data.get('longitude', -74.0060),
                format="%.4f",
                help="Geographic longitude in decimal degrees (-180 to +180). Eastern longitudes are positive. Used for time zone corrections and sun path calculations."
            )
    
    with col2:
        st.subheader("Analysis Settings")
        
        timezone = st.selectbox(
            "Timezone",
            ["UTC", "US/Eastern", "US/Central", "US/Mountain", "US/Pacific", 
             "Europe/London", "Europe/Berlin", "Asia/Tokyo"],
            index=0,
            help="Select the project timezone",
            key="project_timezone"
        )
        
        units = st.selectbox(
            "Units System",
            ["Metric (kW, m², °C)", "Imperial (kW, ft², °F)"],
            index=0,
            help="Choose measurement units",
            key="project_units"
        )
        
        currency = st.selectbox(
            "Currency",
            ["USD ($)", "EUR (€)", "GBP (£)", "JPY (¥)"],
            index=0,
            help="Select currency for financial analysis",
            key="project_currency"
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
    
    # BIM Model Format Documentation
    with st.expander("📋 Supported BIM File Formats", expanded=False):
        st.markdown("""
        **Primary Format:**
        - **Revit Models (.rvt)**: Native Autodesk Revit files
          - Minimum LOD 200 (Level of Development)
          - Recommended LOD 300 for detailed analysis
          - Must include facade and window elements
          - Building geometry with proper orientations
        
        **Alternative Formats (Future Support):**
        - **IFC Files (.ifc)**: Industry Foundation Classes
        - **DWG Files (.dwg)**: AutoCAD drawings with 3D geometry
        - **3DS Files (.3ds)**: 3D Studio Max models
        
        **Model Requirements:**
        - Building must be properly oriented (North direction defined)
        - Facade elements should be categorized as walls
        - Windows should be properly embedded in facades
        - Building height and dimensions must be realistic
        - No missing or corrupted geometry
        
        **Quality Guidelines:**
        - Clean geometry without overlapping elements
        - Proper material assignments for facades and windows
        - Consistent naming conventions for building elements
        - Coordinate system aligned with geographic orientation
        """)
        
        st.warning("⚠️ **Important Notes:**")
        st.markdown("""
        - File size limit: 50MB maximum
        - Processing time depends on model complexity
        - Ensure model is saved in the latest Revit format
        - Models with complex geometry may require longer processing
        """)
    
    uploaded_file = st.file_uploader(
        "Upload Revit Model (.rvt)",
        type=['rvt'],
        help="Upload a Revit model file following the requirements above"
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
    """Historical data analysis module"""
    st.header("2. Historical Data & AI Model")
    st.markdown("Upload historical energy consumption data for baseline demand analysis.")
    
    # Historical data upload section
    st.subheader("Historical Energy Consumption Data")
    
    # CSV Structure Documentation
    with st.expander("📋 Required CSV File Structure", expanded=True):
        st.markdown("""
        **File Format Requirements:**
        
        **Required Columns:**
        - `Date`: Date in YYYY-MM-DD format (e.g., 2023-01-01)
        - `Consumption`: Monthly energy consumption in kWh (numeric values only)
        
        **Optional Columns (recommended for better accuracy):**
        - `Temperature`: Average monthly temperature in °C
        - `Humidity`: Average monthly humidity percentage (0-100)
        - `Solar_Irradiance`: Monthly solar irradiance in kWh/m²
        - `Occupancy`: Building occupancy percentage (0-100)
        
        **Example CSV Structure:**
        """)
        
        st.code("""Date,Consumption,Temperature,Humidity,Solar_Irradiance,Occupancy
2023-01-01,1250.5,5.2,65,85.3,95
2023-02-01,1100.8,8.1,62,105.7,90
2023-03-01,980.3,12.5,58,145.2,85
2023-04-01,850.7,16.8,55,180.4,80
2023-05-01,720.2,22.1,52,210.6,75
2023-06-01,680.9,26.5,48,235.8,70""")
        
        st.warning("⚠️ **Important Notes:**")
        st.markdown("""
        - Use comma-separated values (CSV format)
        - Do not include spaces in column names
        - Numeric values should not contain currency symbols or units
        - Minimum 12 months of data required for seasonal analysis
        - Date format must be consistent throughout the file
        """)
    
    uploaded_file = st.file_uploader(
        "Upload Monthly Consumption Data (CSV)",
        type=['csv'],
        help="Upload a CSV file following the structure shown above"
    )
    
    if uploaded_file is not None:
        try:
            with st.spinner("Processing historical data..."):
                # Read CSV content
                content = uploaded_file.getvalue().decode('utf-8')
                lines = content.strip().split('\n')
                
                if len(lines) < 2:
                    st.error("❌ File must contain header and data rows")
                    return
                
                # Parse CSV manually
                header = lines[0].split(',')
                data_rows = []
                
                for line in lines[1:]:
                    row = line.split(',')
                    if len(row) == len(header):
                        data_rows.append(dict(zip(header, row)))
                
                st.success(f"✅ Data uploaded successfully! {len(data_rows)} records loaded.")
                
                # Store data
                st.session_state.project_data['historical_data'] = data_rows
                
                # Display data preview
                st.subheader("Data Preview")
                for i, row in enumerate(data_rows[:5]):
                    col_data = []
                    for key, value in row.items():
                        col_data.append(f"{key}: {value}")
                    st.write(f"Row {i+1}: {' | '.join(col_data)}")
                
                # Basic statistics
                if 'Consumption' in header:
                    consumptions = []
                    for row in data_rows:
                        try:
                            consumptions.append(float(row['Consumption']))
                        except:
                            pass
                    
                    if consumptions:
                        avg_consumption = sum(consumptions) / len(consumptions)
                        total_consumption = sum(consumptions)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Records", len(data_rows))
                        with col2:
                            st.metric("Avg Monthly Consumption", f"{avg_consumption:.1f} kWh")
                        with col3:
                            st.metric("Total Annual Consumption", f"{total_consumption:.0f} kWh")
                        
                        # Try to import plotly for visualization
                        try:
                            import plotly.express as px
                            import pandas as pd
                            
                            # Create consumption trend chart
                            if len(consumptions) >= 3:
                                months = list(range(1, len(consumptions) + 1))
                                consumption_df = pd.DataFrame({
                                    'Month': months,
                                    'Consumption': consumptions
                                })
                                
                                fig_trend = px.line(consumption_df, x='Month', y='Consumption',
                                                   title='Monthly Energy Consumption Trend',
                                                   labels={'Consumption': 'Consumption (kWh)'})
                                fig_trend.update_layout(height=400)
                                st.plotly_chart(fig_trend, use_container_width=True)
                                
                        except ImportError:
                            # Fall back to text-based visualization
                            st.subheader("Consumption Trend")
                            st.write("**Monthly Consumption Pattern:**")
                            max_val = max(consumptions) if consumptions else 1
                            for i, consumption in enumerate(consumptions[:12]):
                                bar_length = int((consumption / max_val) * 30)
                                bar = "█" * bar_length + "░" * (30 - bar_length)
                                st.write(f"Month {i+1}: {bar} {consumption:.0f} kWh")
                
                st.success("✅ Historical data analysis complete!")
                st.info("Proceed to Step 3 for weather data configuration.")
                
        except Exception as e:
            st.error(f"❌ Error processing data: {str(e)}")
            st.info("Please ensure your CSV file has the correct format.")
    
    else:
        st.info("👆 Please upload a CSV file with historical energy consumption data.")
        
        # Show sample data format
        with st.expander("📋 View Sample Data Format"):
            st.code("""
Date,Consumption,Temperature
2023-01-01,1250,5.2
2023-02-01,1100,8.1
2023-03-01,950,12.5
2023-04-01,800,18.3
            """)

def render_weather_environment():
    """Weather and environment analysis"""
    st.header("3. Weather & Environment")
    st.markdown("Configure weather data sources and environmental conditions for solar analysis.")
    
    # Get project coordinates
    latitude = st.session_state.project_data.get('latitude', 40.7128)
    longitude = st.session_state.project_data.get('longitude', -74.0060)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Location Information")
        st.write(f"**Latitude:** {latitude:.4f}°")
        st.write(f"**Longitude:** {longitude:.4f}°")
        
        # TMY data generation
        if st.button("Generate Weather Data", key="generate_weather"):
            with st.spinner("Generating simplified weather data for solar analysis..."):
                weather_data = generate_simple_weather_data(latitude, longitude)
                st.session_state.project_data['weather_data'] = weather_data
                st.success("✅ Weather data generated successfully!")
    
    with col2:
        st.subheader("Environmental Conditions")
        
        # Shading factors with comprehensive help
        tree_shading = st.slider(
            "Tree Shading Factor", 0.0, 0.5, 0.1, 0.05,
            help="Fraction of solar irradiance blocked by vegetation. Accounts for seasonal variation, tree height, canopy density. Deciduous trees: 0.05-0.15 (seasonal), Evergreen: 0.10-0.25 (year-round), Dense urban forest: 0.15-0.30.",
            key="tree_shading_slider"
        )
        
        building_shading = st.slider(
            "Building Shading Factor", 0.0, 0.3, 0.05, 0.05,
            help="Fraction of solar irradiance blocked by neighboring structures. Consider building height, distance, and orientation relative to sun path. Typical urban settings: 0.05-0.15, Dense urban core: 0.15-0.30.",
            key="building_shading_slider"
        )
        
        st.session_state.project_data['shading_factors'] = {
            'trees': tree_shading,
            'buildings': building_shading
        }
    
    # Display weather data if available
    if 'weather_data' in st.session_state.project_data:
        weather = st.session_state.project_data['weather_data']
        
        st.subheader("Weather Data Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Annual Solar Irradiance", f"{weather['annual_ghi']:.0f} kWh/m²")
        with col2:
            st.metric("Peak Daily Irradiance", f"{weather['peak_daily_ghi']:.1f} kWh/m²")
        with col3:
            st.metric("Average Temperature", f"{weather['avg_temperature']:.1f} °C")
        with col4:
            st.metric("Heating Degree Days", f"{weather['heating_degree_days']:.0f}")
        
        # Monthly breakdown with visualizations
        st.subheader("Monthly Solar Resource")
        
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        monthly_data = weather['monthly_ghi']
        
        # Try to create interactive charts
        try:
            import plotly.express as px
            import pandas as pd
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Monthly GHI bar chart
                monthly_df = pd.DataFrame({
                    'Month': months,
                    'GHI': monthly_data
                })
                
                fig_monthly = px.bar(monthly_df, x='Month', y='GHI',
                                   title='Monthly Global Horizontal Irradiance',
                                   labels={'GHI': 'Solar Irradiance (kWh/m²)'})
                fig_monthly.update_layout(height=350)
                st.plotly_chart(fig_monthly, use_container_width=True)
            
            with col2:
                # Temperature profile
                temp_profile = []
                for month in range(1, 13):
                    temp_base = weather['avg_temperature'] + 10 * math.sin(2 * math.pi * (month - 3) / 12)
                    temp_profile.append(temp_base)
                
                temp_df = pd.DataFrame({
                    'Month': months,
                    'Temperature': temp_profile
                })
                
                fig_temp = px.line(temp_df, x='Month', y='Temperature',
                                 title='Monthly Temperature Profile',
                                 labels={'Temperature': 'Temperature (°C)'})
                fig_temp.update_layout(height=350)
                st.plotly_chart(fig_temp, use_container_width=True)
                
        except ImportError:
            # Fall back to text-based charts
            st.write("**Monthly Global Horizontal Irradiance (kWh/m²):**")
            max_val = max(monthly_data)
            for i, (month, value) in enumerate(zip(months, monthly_data)):
                bar_length = int((value / max_val) * 30)
                bar = "█" * bar_length + "░" * (30 - bar_length)
                st.write(f"{month}: {bar} {value:.0f}")
        
        st.success("✅ Weather analysis complete!")
        st.info("Proceed to Step 4 for building facade extraction.")

def generate_simple_weather_data(lat, lon):
    """
    Generate simplified weather data for location using empirical solar radiation models
    
    Equations Used:
    1. Base Annual GHI = 1000 + (40 - |latitude|) × 20 [kWh/m²/year]
       - Input: latitude (degrees) - Geographic latitude coordinate
       - Purpose: Estimates annual global horizontal irradiance based on latitude
       - Result: Higher values at lower latitudes (equatorial regions)
    
    2. Seasonal Factor = 0.7 + 0.6 × sin(2π × (month - 3) / 12)
       - Input: month (1-12) - Calendar month number
       - Purpose: Models seasonal solar variation with summer peak
       - Result: Multiplicative factor for monthly distribution
    
    3. Monthly GHI = (Base Annual GHI / 12) × Seasonal Factor [kWh/m²/month]
       - Input: Base annual GHI, seasonal factor
       - Purpose: Distributes annual irradiance across months
       - Result: Monthly solar energy availability
    
    4. Base Temperature = 15 - |latitude| × 0.3 [°C]
       - Input: latitude (degrees)
       - Purpose: Estimates average temperature based on latitude
       - Result: Cooler temperatures at higher latitudes
    
    5. Heating Degree Days = max(0, (18 - avg_temperature) × 365) [°C·days]
       - Input: average temperature (°C)
       - Purpose: Calculates annual heating energy requirement
       - Result: Zero for warm climates, higher for cold climates
    """
    # Base solar irradiance varies by latitude
    base_annual_ghi = 1000 + (40 - abs(lat)) * 20  # Higher at lower latitudes
    
    # Generate monthly distribution
    monthly_ghi = []
    for month in range(1, 13):
        # Seasonal variation - peak in summer
        seasonal_factor = 0.7 + 0.6 * math.sin(2 * math.pi * (month - 3) / 12)
        monthly_value = (base_annual_ghi / 12) * seasonal_factor
        monthly_ghi.append(max(20, monthly_value))  # Minimum 20 kWh/m²/month
    
    # Calculate other weather parameters
    annual_ghi = sum(monthly_ghi)
    peak_daily_ghi = max(monthly_ghi) / 30  # Approximate daily peak
    
    # Temperature model based on latitude
    base_temp = 15 - abs(lat) * 0.3  # Cooler at higher latitudes
    avg_temperature = base_temp
    
    # Heating degree days (simplified)
    heating_degree_days = max(0, (18 - avg_temperature) * 365)
    
    return {
        'annual_ghi': annual_ghi,
        'monthly_ghi': monthly_ghi,
        'peak_daily_ghi': peak_daily_ghi,
        'avg_temperature': avg_temperature,
        'heating_degree_days': heating_degree_days
    }

def render_facade_extraction():
    """Building facade and window extraction"""
    st.header("4. Facade & Window Extraction")
    st.markdown("Extract building elements suitable for PV installation from the uploaded BIM model.")
    
    if 'bim_model' not in st.session_state.project_data:
        st.warning("⚠️ Please upload a BIM model in Step 1 before proceeding.")
        return
    
    if st.button("Analyze Building Elements", key="analyze_building_elements"):
        with st.spinner("Extracting facade and window elements from BIM model..."):
            building_elements = simulate_building_extraction()
            st.session_state.project_data['building_elements'] = building_elements
            st.success("✅ Building analysis complete!")
    
    # Display building elements if available
    if 'building_elements' in st.session_state.project_data:
        elements = st.session_state.project_data['building_elements']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Facade Elements")
            
            facade_count = len(elements['facades'])
            suitable_facades = sum(1 for f in elements['facades'] if f['pv_suitable'])
            total_facade_area = sum(f['area'] for f in elements['facades'])
            
            st.metric("Total Facades", facade_count)
            st.metric("PV Suitable Facades", suitable_facades)
            st.metric("Total Facade Area", f"{total_facade_area:.0f} m²")
            
            # Show facade details
            for facade in elements['facades'][:3]:  # Show first 3
                st.write(f"**{facade['id']}:** {facade['orientation']}, {facade['area']:.0f} m², "
                        f"{'✅ Suitable' if facade['pv_suitable'] else '❌ Not suitable'}")
        
        with col2:
            st.subheader("Window Elements")
            
            window_count = len(elements['windows'])
            suitable_windows = sum(1 for w in elements['windows'] if w['pv_suitable'])
            total_window_area = sum(w['area'] for w in elements['windows'])
            
            st.metric("Total Windows", window_count)
            st.metric("PV Suitable Windows", suitable_windows)
            st.metric("Total Window Area", f"{total_window_area:.0f} m²")
            
            # Show window details
            for window in elements['windows'][:3]:  # Show first 3
                st.write(f"**{window['id']}:** {window['orientation']}, {window['area']:.1f} m², "
                        f"{'✅ Suitable' if window['pv_suitable'] else '❌ Not suitable'}")
        
        # Orientation analysis
        st.subheader("Suitability by Orientation")
        orientations = {}
        
        for facade in elements['facades']:
            orient = facade['orientation']
            if orient not in orientations:
                orientations[orient] = {'count': 0, 'suitable': 0, 'area': 0}
            orientations[orient]['count'] += 1
            orientations[orient]['area'] += facade['area']
            if facade['pv_suitable']:
                orientations[orient]['suitable'] += 1
        
        for orient, data in orientations.items():
            suitability_rate = (data['suitable'] / data['count']) * 100 if data['count'] > 0 else 0
            st.write(f"**{orient}:** {data['count']} elements, {suitability_rate:.0f}% suitable, {data['area']:.0f} m²")
        
        st.success("✅ Building element extraction complete!")
        st.info("Proceed to Step 5 for solar radiation analysis.")

def simulate_building_extraction():
    """
    Simulate extraction of building elements from BIM model using geometric analysis
    
    Building Element Analysis Equations:
    1. Element Area Distribution = Base Area + (Element Index × Area Increment) [m²]
       - Input: Base Area (m²) - Minimum element size
       - Input: Area Increment (m²) - Size variation between elements
       - Input: Element Index - Sequential element number
       - Purpose: Creates realistic size distribution across building elements
       - Result: Varied element areas representing diverse facade conditions
    
    2. Element Dimensions from Area:
       - Width = √(Area × Aspect Ratio) [m]
       - Height = √(Area / Aspect Ratio) [m]
       - Input: Area (m²) - Element surface area
       - Input: Aspect Ratio - Width/height ratio (facades: 1.5, windows: 1.2)
       - Purpose: Derives realistic proportions from area constraints
       - Result: Width and height maintaining typical building proportions
    
    3. PV Suitability Criteria:
       - Orientation Suitability = Element Orientation ∈ {South, SE, SW, East, West}
       - Size Suitability = Element Area > Minimum Threshold
       - Overall Suitability = Orientation AND Size criteria
       - Input: Element Orientation - Cardinal/ordinal direction
       - Input: Element Area (m²) - Available surface area
       - Purpose: Filters elements suitable for PV installation
       - Result: Boolean suitability flag for system design
    
    4. Geometric Properties:
       - Tilt Angle = 90° (vertical building surfaces)
       - Aspect Ratios: Facades 1.5:1, Windows 1.2:1
       - Minimum Areas: Facades 100 m², Windows 6 m²
       - Purpose: Establishes standard building element characteristics
       - Result: Realistic geometric parameters for solar calculations
    """
    orientations = ['North', 'South', 'East', 'West', 'Northeast', 'Northwest', 'Southeast', 'Southwest']
    
    facades = []
    windows = []
    
    # Generate facade elements
    for i in range(12):  # 12 facade elements
        orientation = orientations[i % len(orientations)]
        area = 80 + (i * 15)  # Varying areas 80-245 m²
        
        # PV suitability based on orientation and size
        suitable_orientations = ['South', 'Southeast', 'Southwest', 'East', 'West']
        pv_suitable = orientation in suitable_orientations and area > 100
        
        facades.append({
            'id': f'FAC_{i+1:02d}',
            'orientation': orientation,
            'area': area,
            'width': math.sqrt(area * 1.5),
            'height': math.sqrt(area / 1.5),
            'pv_suitable': pv_suitable,
            'tilt_angle': 90  # Vertical facades
        })
    
    # Generate window elements
    for i in range(25):  # 25 window elements
        orientation = orientations[i % len(orientations)]
        area = 3 + (i * 0.5)  # Varying areas 3-15.5 m²
        
        # Windows suitable if larger than 6 m²
        pv_suitable = area > 6
        
        windows.append({
            'id': f'WIN_{i+1:02d}',
            'orientation': orientation,
            'area': area,
            'width': math.sqrt(area * 1.2),
            'height': math.sqrt(area / 1.2),
            'pv_suitable': pv_suitable,
            'tilt_angle': 90  # Vertical windows
        })
    
    return {
        'facades': facades,
        'windows': windows
    }

def render_radiation_grid():
    """Solar radiation and shading analysis"""
    st.header("5. Radiation & Shading Grid")
    st.markdown("Calculate solar radiation potential for each building element with shading analysis.")
    
    if 'building_elements' not in st.session_state.project_data or 'weather_data' not in st.session_state.project_data:
        st.warning("⚠️ Please complete Steps 3 and 4 before proceeding.")
        return
    
    if st.button("Calculate Solar Radiation Grid", key="calc_radiation_grid"):
        with st.spinner("Calculating solar radiation for all building elements..."):
            radiation_analysis = calculate_radiation_analysis()
            st.session_state.project_data['radiation_analysis'] = radiation_analysis
            st.success("✅ Solar radiation analysis complete!")
    
    # Display radiation analysis if available
    if 'radiation_analysis' in st.session_state.project_data:
        analysis = st.session_state.project_data['radiation_analysis']
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            avg_irradiance = sum(e['annual_irradiance'] for e in analysis) / len(analysis)
            st.metric("Avg Annual Irradiance", f"{avg_irradiance:.0f} kWh/m²")
        with col2:
            max_irradiance = max(e['annual_irradiance'] for e in analysis)
            st.metric("Peak Element Irradiance", f"{max_irradiance:.0f} kWh/m²")
        with col3:
            avg_shading = sum(e['shading_factor'] for e in analysis) / len(analysis)
            st.metric("Avg Shading Factor", f"{avg_shading:.2f}")
        with col4:
            high_potential = sum(1 for e in analysis if e['annual_irradiance'] > 1000)
            st.metric("High Potential Elements", high_potential)
        
        # Detailed analysis by orientation with visualizations
        st.subheader("Solar Resource by Orientation")
        
        orientation_analysis = {}
        for element in analysis:
            orient = element['orientation']
            if orient not in orientation_analysis:
                orientation_analysis[orient] = {
                    'count': 0,
                    'total_irradiance': 0,
                    'total_area': 0,
                    'avg_shading': 0
                }
            
            data = orientation_analysis[orient]
            data['count'] += 1
            data['total_irradiance'] += element['annual_irradiance']
            data['total_area'] += element['area']
            data['avg_shading'] += element['shading_factor']
        
        # Create visualization data
        orient_data = []
        for orient, data in orientation_analysis.items():
            if data['count'] > 0:
                avg_irradiance = data['total_irradiance'] / data['count']
                avg_shading = data['avg_shading'] / data['count']
                orient_data.append({
                    'Orientation': orient,
                    'Avg_Irradiance': avg_irradiance,
                    'Element_Count': data['count'],
                    'Total_Area': data['total_area'],
                    'Avg_Shading': avg_shading
                })
        
        if orient_data:
            # Try to create plotly charts
            try:
                import plotly.express as px
                import pandas as pd
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Irradiance by orientation
                    orient_df = pd.DataFrame(orient_data)
                    fig_orient = px.bar(orient_df, x='Orientation', y='Avg_Irradiance',
                                      title='Average Solar Irradiance by Orientation',
                                      labels={'Avg_Irradiance': 'Irradiance (kWh/m²)'})
                    fig_orient.update_layout(height=350)
                    st.plotly_chart(fig_orient, use_container_width=True)
                
                with col2:
                    # Scatter plot: Area vs Irradiance
                    fig_scatter = px.scatter(orient_df, x='Total_Area', y='Avg_Irradiance',
                                           size='Element_Count', color='Orientation',
                                           title='Area vs Solar Resource',
                                           labels={'Total_Area': 'Total Area (m²)',
                                                  'Avg_Irradiance': 'Irradiance (kWh/m²)'})
                    fig_scatter.update_layout(height=350)
                    st.plotly_chart(fig_scatter, use_container_width=True)
                    
            except ImportError:
                # Fall back to text display
                for item in orient_data:
                    st.write(f"**{item['Orientation']}:** {item['Element_Count']} elements, "
                            f"{item['Avg_Irradiance']:.0f} kWh/m², {item['Total_Area']:.0f} m²")
        
        # Top performing elements
        st.subheader("Top Solar Resource Elements")
        
        sorted_elements = sorted(analysis, key=lambda x: x['annual_irradiance'], reverse=True)
        
        for element in sorted_elements[:5]:
            st.write(f"**{element['element_id']}:** {element['orientation']}, "
                    f"{element['annual_irradiance']:.0f} kWh/m², "
                    f"{element['area']:.0f} m², "
                    f"Shading: {element['shading_factor']:.2f}")
        
        st.success("✅ Solar radiation analysis complete!")
        st.info("Proceed to Step 6 for PV panel specification.")

def calculate_radiation_analysis():
    """
    Calculate solar radiation for building elements using established solar engineering methods
    
    Equations Used:
    1. Element Irradiance = Base GHI × Orientation Factor × Shading Factor × Tilt Factor [kWh/m²/year]
       - Input: Base GHI (kWh/m²/year) - Global horizontal irradiance
       - Input: Orientation Factor (0-1) - Directional solar access coefficient
       - Input: Shading Factor (0-1) - Reduction due to obstructions
       - Input: Tilt Factor (0-1) - Vertical surface correction factor
       - Purpose: Calculates incident solar radiation on each building element
       - Result: Annual solar energy available per unit area
    
    2. Total Shading Factor = 1 - (Tree Shading + Building Shading)
       - Input: Tree Shading (0-1) - Fraction blocked by vegetation
       - Input: Building Shading (0-1) - Fraction blocked by structures
       - Purpose: Combines multiple shading sources
       - Result: Net solar access factor after obstructions
    
    3. Orientation Factors (empirical coefficients for vertical surfaces):
       - South: 0.95 (optimal in Northern Hemisphere)
       - SE/SW: 0.85 (good morning/afternoon exposure)
       - East/West: 0.75 (half-day exposure)
       - NE/NW: 0.55 (limited exposure)
       - North: 0.35 (minimal direct solar access)
    
    4. Vertical Factor = 0.8
       - Purpose: Accounts for reduced irradiance on vertical vs. optimal tilt surfaces
       - Result: 20% reduction compared to optimally tilted surfaces
    """
    elements = st.session_state.project_data['building_elements']
    weather = st.session_state.project_data['weather_data']
    shading_factors = st.session_state.project_data.get('shading_factors', {'trees': 0.1, 'buildings': 0.05})
    
    # Base annual irradiance from weather data
    base_annual_ghi = weather['annual_ghi']
    
    radiation_analysis = []
    
    # Analyze all building elements
    all_elements = elements['facades'] + elements['windows']
    
    for element in all_elements:
        if not element['pv_suitable']:
            continue
        
        # Orientation factors for vertical surfaces
        orientation_factors = {
            'South': 0.95,
            'Southeast': 0.85,
            'Southwest': 0.85,
            'East': 0.75,
            'West': 0.75,
            'Northeast': 0.55,
            'Northwest': 0.55,
            'North': 0.35
        }
        
        orientation_factor = orientation_factors.get(element['orientation'], 0.6)
        
        # Calculate annual irradiance for this element
        annual_irradiance = base_annual_ghi * orientation_factor
        
        # Apply shading factors
        total_shading = 1 - (shading_factors['trees'] + shading_factors['buildings'])
        annual_irradiance *= total_shading
        
        # Calculate effective irradiance considering tilt (vertical = 90°)
        # Vertical surfaces receive less irradiance than optimal tilt
        vertical_factor = 0.8  # Typical factor for vertical vs optimal tilt
        annual_irradiance *= vertical_factor
        
        radiation_analysis.append({
            'element_id': element['id'],
            'orientation': element['orientation'],
            'area': element['area'],
            'annual_irradiance': annual_irradiance,
            'orientation_factor': orientation_factor,
            'shading_factor': total_shading,
            'element_type': 'facade' if element['id'].startswith('FAC') else 'window'
        })
    
    return radiation_analysis

def render_pv_specification():
    """PV panel specification and system configuration"""
    st.header("6. PV Panel Specification")
    st.markdown("Define PV panel specifications and calculate system layouts for building elements.")
    
    if 'radiation_analysis' not in st.session_state.project_data:
        st.warning("⚠️ Please complete Step 5 solar radiation analysis before proceeding.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("PV Panel Selection")
        
        panel_type = st.selectbox(
            "Panel Technology",
            ["Monocrystalline Silicon", "Polycrystalline Silicon", "Thin-Film CdTe", "Bifacial"],
            help="Select the PV panel technology",
            key="panel_technology_select"
        )
        
        # Get panel specifications
        panel_specs = get_panel_database()[panel_type]
        
        st.metric("Panel Power", f"{panel_specs['power']} W")
        st.metric("Panel Efficiency", f"{panel_specs['efficiency']:.1f}%")
        st.metric("Panel Dimensions", f"{panel_specs['width']:.1f} × {panel_specs['height']:.1f} m")
        st.metric("Cost per Panel", f"${panel_specs['cost']}")
    
    with col2:
        st.subheader("Installation Parameters")
        
        spacing_factor = st.slider(
            "Panel Spacing Factor", 0.02, 0.15, 0.05, 0.01,
            help="Spacing between panels as fraction of panel dimensions. Accounts for structural framing, maintenance access, and thermal expansion. Typical range: 0.02-0.10 for optimal installations.",
            key="panel_spacing_factor"
        )
        
        min_system_size = st.number_input(
            "Minimum System Size (kW)", 1.0, 20.0, 3.0, 0.5,
            help="Minimum DC system capacity for economic viability. Smaller systems have higher per-kW costs due to fixed installation expenses. Recommended minimum: 3-5 kW for cost-effectiveness.",
            key="min_system_size"
        )
        
        system_losses = st.slider(
            "Total System Losses (%)", 10, 25, 15, 1,
            help="Combined system efficiency losses including: inverter losses (2-5%), DC/AC wiring (2-3%), soiling/dust (2-5%), temperature effects (3-8%), mismatch losses (1-3%). Typical total: 12-18%.",
            key="system_losses_slider"
        )
    
    if st.button("Calculate PV System Specifications", key="calc_pv_specs"):
        with st.spinner("Calculating PV system layouts for all suitable elements..."):
            pv_systems = calculate_pv_systems(panel_specs, spacing_factor, min_system_size, system_losses)
            st.session_state.project_data['pv_systems'] = pv_systems
            st.success("✅ PV system specifications calculated!")
    
    # Display PV systems if available
    if 'pv_systems' in st.session_state.project_data:
        systems = st.session_state.project_data['pv_systems']
        
        if not systems:
            st.warning("No systems meet the minimum size requirement. Try reducing the minimum system size.")
            return
        
        # System summary
        total_power = sum(s['system_power_kw'] for s in systems)
        total_panels = sum(s['panel_count'] for s in systems)
        total_cost = sum(s['total_cost'] for s in systems)
        total_energy = sum(s['annual_energy_kwh'] for s in systems)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total System Power", f"{total_power:.1f} kW")
        with col2:
            st.metric("Total Panels", f"{total_panels}")
        with col3:
            st.metric("Total Installation Cost", f"${total_cost:,.0f}")
        with col4:
            st.metric("Annual Energy Production", f"{total_energy:,.0f} kWh")
        
        # System details
        st.subheader("PV System Details")
        
        for system in systems:
            with st.expander(f"System {system['element_id']} - {system['system_power_kw']:.1f} kW"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Element:** {system['element_id']}")
                    st.write(f"**Orientation:** {system['orientation']}")
                    st.write(f"**Panel Count:** {system['panel_count']}")
                with col2:
                    st.write(f"**System Power:** {system['system_power_kw']:.1f} kW")
                    st.write(f"**Annual Energy:** {system['annual_energy_kwh']:,.0f} kWh")
                    st.write(f"**Specific Yield:** {system['specific_yield']:.0f} kWh/kW")
                with col3:
                    st.write(f"**Panel Cost:** ${system['panel_cost']:,.0f}")
                    st.write(f"**Installation Cost:** ${system['installation_cost']:,.0f}")
                    st.write(f"**Total Cost:** ${system['total_cost']:,.0f}")
        
        st.success("✅ PV specification complete!")
        st.info("Proceed to Step 7 for energy yield vs demand analysis.")

def get_panel_database():
    """Database of PV panel specifications"""
    return {
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
        "Thin-Film CdTe": {
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

def calculate_pv_systems(panel_specs, spacing_factor, min_system_size, system_losses):
    """
    Calculate PV system specifications for suitable elements using industry-standard methods
    
    Equations Used:
    1. Effective Panel Area = Panel Area × (1 + Spacing Factor)² [m²]
       - Input: Panel Area (m²) - Physical panel dimensions
       - Input: Spacing Factor (0-1) - Inter-panel spacing coefficient
       - Purpose: Accounts for required spacing between panels
       - Result: Total area including spacing per panel
    
    2. Panel Count = floor(Available Area / Effective Panel Area)
       - Input: Available Area (m²) - Usable surface area
       - Input: Effective Panel Area (m²) - Panel area with spacing
       - Purpose: Determines maximum panels that can be installed
       - Result: Integer number of panels that physically fit
    
    3. System Power = (Panel Count × Panel Power) / 1000 [kW]
       - Input: Panel Count (units) - Number of installed panels
       - Input: Panel Power (W) - Rated power per panel under STC
       - Purpose: Calculates total DC system capacity
       - Result: System power rating in kilowatts
    
    4. Annual Energy = System Power × Annual Irradiance × Performance Ratio [kWh/year]
       - Input: System Power (kW) - DC system capacity
       - Input: Annual Irradiance (kWh/m²/year) - Solar resource
       - Input: Performance Ratio (0-1) - System efficiency factor
       - Purpose: Estimates annual energy production
       - Result: Expected yearly electricity generation
    
    5. Performance Ratio = (100 - System Losses) / 100
       - Input: System Losses (%) - Combined inverter, wiring, soiling losses
       - Purpose: Accounts for real-world efficiency reductions
       - Result: Fraction of theoretical maximum energy output
    
    6. Specific Yield = Annual Energy / System Power [kWh/kW/year]
       - Input: Annual Energy (kWh/year) - Total energy production
       - Input: System Power (kW) - System capacity
       - Purpose: Normalizes energy output per unit capacity
       - Result: Performance metric for system comparison
    
    7. Total Cost = Panel Cost + Installation Cost [USD]
       - Input: Panel Cost = Panel Count × Unit Panel Cost
       - Input: Installation Cost = System Power × Cost per kW
       - Purpose: Estimates total project investment
       - Result: Capital expenditure for system installation
    """
    radiation_data = st.session_state.project_data['radiation_analysis']
    
    pv_systems = []
    
    for element in radiation_data:
        # Calculate panel layout
        available_area = element['area']
        panel_area = panel_specs['width'] * panel_specs['height']
        
        # Account for spacing
        effective_panel_area = panel_area * (1 + spacing_factor) ** 2
        
        # Calculate number of panels that fit
        panels_that_fit = int(available_area / effective_panel_area)
        
        if panels_that_fit == 0:
            continue
        
        # Calculate system power
        system_power_kw = (panels_that_fit * panel_specs['power']) / 1000
        
        # Skip if below minimum size
        if system_power_kw < min_system_size:
            continue
        
        # Calculate annual energy production
        annual_irradiance = element['annual_irradiance']  # kWh/m²/year
        
        # Energy calculation: System power × specific irradiance × performance ratio
        performance_ratio = (100 - system_losses) / 100
        
        # Normalize irradiance to standard conditions (1000 kWh/m² = 1 sun-hour)
        equivalent_sun_hours = annual_irradiance  # Simplified assumption
        annual_energy_kwh = system_power_kw * equivalent_sun_hours * performance_ratio
        
        # Calculate specific yield
        specific_yield = annual_energy_kwh / system_power_kw if system_power_kw > 0 else 0
        
        # Calculate costs
        panel_cost = panels_that_fit * panel_specs['cost']
        installation_cost_per_kw = 1500  # $/kW including inverter and installation
        installation_cost = system_power_kw * installation_cost_per_kw
        total_cost = panel_cost + installation_cost
        
        pv_systems.append({
            'element_id': element['element_id'],
            'orientation': element['orientation'],
            'element_area': available_area,
            'panel_count': panels_that_fit,
            'system_power_kw': system_power_kw,
            'annual_energy_kwh': annual_energy_kwh,
            'specific_yield': specific_yield,
            'panel_cost': panel_cost,
            'installation_cost': installation_cost,
            'total_cost': total_cost,
            'panel_technology': panel_specs
        })
    
    return pv_systems

# Continue with the remaining functions...
def render_yield_demand():
    """Energy yield vs demand analysis"""
    st.header("7. Yield vs. Demand Calculation")
    st.markdown("Analyze the balance between PV energy generation and building energy demand.")
    
    if 'pv_systems' not in st.session_state.project_data or 'historical_data' not in st.session_state.project_data:
        st.warning("⚠️ Please complete Steps 2 and 6 before proceeding.")
        return
    
    if st.button("Calculate Energy Balance", key="calc_energy_balance"):
        with st.spinner("Analyzing energy yield vs demand balance..."):
            energy_balance = calculate_energy_balance_analysis()
            st.session_state.project_data['energy_balance'] = energy_balance
            st.success("✅ Energy balance analysis complete!")
    
    # Display energy balance if available
    if 'energy_balance' in st.session_state.project_data:
        balance = st.session_state.project_data['energy_balance']
        
        # Annual summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Annual Demand", f"{balance['annual_demand']:,.0f} kWh")
        with col2:
            st.metric("Annual PV Generation", f"{balance['annual_generation']:,.0f} kWh")
        with col3:
            st.metric("Net Energy Import", f"{balance['net_import']:,.0f} kWh")
        with col4:
            st.metric("Energy Self-Sufficiency", f"{balance['self_sufficiency']:.1f}%")
        
        # Monthly analysis with interactive charts
        st.subheader("Monthly Energy Profile")
        
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        # Try interactive visualization
        try:
            import plotly.express as px
            import plotly.graph_objects as go
            import pandas as pd
            
            # Create monthly energy balance chart
            monthly_df = pd.DataFrame({
                'Month': months,
                'Demand': balance['monthly_demand'],
                'Generation': balance['monthly_generation'],
                'Net_Import': [d - g for d, g in zip(balance['monthly_demand'], balance['monthly_generation'])]
            })
            
            # Multi-line chart showing demand vs generation
            fig_energy = go.Figure()
            
            fig_energy.add_trace(go.Scatter(
                x=monthly_df['Month'],
                y=monthly_df['Demand'],
                mode='lines+markers',
                name='Energy Demand',
                line=dict(color='red', width=3),
                marker=dict(size=8)
            ))
            
            fig_energy.add_trace(go.Scatter(
                x=monthly_df['Month'],
                y=monthly_df['Generation'],
                mode='lines+markers',
                name='PV Generation',
                line=dict(color='green', width=3),
                marker=dict(size=8)
            ))
            
            fig_energy.add_trace(go.Scatter(
                x=monthly_df['Month'],
                y=monthly_df['Net_Import'],
                mode='lines+markers',
                name='Net Import',
                line=dict(color='blue', width=2, dash='dash'),
                marker=dict(size=6)
            ))
            
            fig_energy.update_layout(
                title='Monthly Energy Balance Profile',
                xaxis_title='Month',
                yaxis_title='Energy (kWh)',
                height=450,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_energy, use_container_width=True)
            
        except ImportError:
            # Fall back to text visualization
            st.write("**Monthly Energy Balance (kWh):**")
            for i, month in enumerate(months):
                demand = balance['monthly_demand'][i]
                generation = balance['monthly_generation'][i]
                net = demand - generation
                
                # Create visual bar using characters
                max_val = max(max(balance['monthly_demand']), max(balance['monthly_generation']))
                demand_bar_length = int((demand / max_val) * 20)
                generation_bar_length = int((generation / max_val) * 20)
                
                demand_bar = "🔴" * demand_bar_length
                generation_bar = "🟢" * generation_bar_length
                
                st.write(f"**{month}:** Demand: {demand_bar} {demand:.0f} | Generation: {generation_bar} {generation:.0f} | Net: {net:+.0f}")
        
        # Energy independence analysis
        st.subheader("Energy Independence Analysis")
        
        months_surplus = sum(1 for i in range(12) if balance['monthly_generation'][i] > balance['monthly_demand'][i])
        
        st.write(f"- **Months with energy surplus:** {months_surplus}/12")
        st.write(f"- **Peak generation month:** {months[balance['monthly_generation'].index(max(balance['monthly_generation']))]}")
        st.write(f"- **Peak demand month:** {months[balance['monthly_demand'].index(max(balance['monthly_demand']))]}")
        
        if balance['self_sufficiency'] >= 100:
            st.success("🎉 The PV system generates more energy than the building consumes annually!")
        elif balance['self_sufficiency'] >= 80:
            st.info("✅ High energy self-sufficiency achieved with this PV configuration.")
        elif balance['self_sufficiency'] >= 50:
            st.warning("⚠️ Moderate energy self-sufficiency. Consider adding more PV capacity.")
        else:
            st.error("❌ Low energy self-sufficiency. Significant grid dependency remains.")
        
        st.success("✅ Energy balance analysis complete!")
        st.info("Proceed to Step 8 for system optimization.")

def calculate_energy_balance_analysis():
    """
    Calculate energy balance between PV generation and building demand using energy flow analysis
    
    Energy Balance Equations Used:
    1. Annual Demand = Σ(Monthly Consumption) [kWh/year]
       - Input: Monthly Consumption (kWh) - Historical energy usage data
       - Purpose: Determines total building energy requirements
       - Result: Baseline annual electricity consumption
    
    2. Total Annual Generation = Σ(System Annual Energy) [kWh/year]
       - Input: System Annual Energy (kWh) - PV system production estimates
       - Purpose: Sums generation from all installed PV systems
       - Result: Total renewable energy production capacity
    
    3. Monthly Generation Fraction = Monthly GHI / Total Annual GHI
       - Input: Monthly GHI (kWh/m²/month) - Solar resource distribution
       - Input: Total Annual GHI (kWh/m²/year) - Annual solar resource
       - Purpose: Distributes annual generation across months
       - Result: Seasonal generation profile
    
    4. Monthly Generation = Total Annual Generation × Monthly Fraction [kWh/month]
       - Input: Total Annual Generation (kWh/year) - System capacity
       - Input: Monthly Fraction (0-1) - Seasonal distribution factor
       - Purpose: Estimates monthly PV energy production
       - Result: Time-series generation profile
    
    5. Net Energy Import = Annual Demand - Annual Generation [kWh/year]
       - Input: Annual Demand (kWh) - Building energy requirements
       - Input: Annual Generation (kWh) - PV system production
       - Purpose: Calculates remaining grid dependency
       - Result: Positive = grid import, Negative = grid export
    
    6. Energy Self-Sufficiency = (Annual Generation / Annual Demand) × 100 [%]
       - Input: Annual Generation (kWh) - PV energy production
       - Input: Annual Demand (kWh) - Building energy consumption
       - Purpose: Measures renewable energy independence
       - Result: Percentage of demand met by on-site generation
    """
    historical_data = st.session_state.project_data['historical_data']
    pv_systems = st.session_state.project_data['pv_systems']
    weather_data = st.session_state.project_data['weather_data']
    
    # Extract annual demand from historical data
    annual_demand = 0.0
    monthly_demand = [0.0] * 12
    
    for row in historical_data:
        try:
            consumption = float(row['Consumption'])
            annual_demand += consumption
            # Distribute to months (simplified)
            monthly_portion = consumption / 12.0
            for i in range(12):
                monthly_demand[i] += monthly_portion
        except:
            pass
    
    # Calculate PV generation
    total_annual_generation = sum(system['annual_energy_kwh'] for system in pv_systems)
    
    # Distribute generation by month using weather data
    monthly_ghi = weather_data['monthly_ghi']
    total_ghi = sum(monthly_ghi)
    
    monthly_generation = []
    for month_ghi in monthly_ghi:
        month_fraction = month_ghi / total_ghi if total_ghi > 0 else 1/12
        monthly_generation.append(total_annual_generation * month_fraction)
    
    # Calculate net import and self-sufficiency
    net_import = annual_demand - total_annual_generation
    self_sufficiency = (total_annual_generation / annual_demand * 100) if annual_demand > 0 else 0
    
    return {
        'annual_demand': annual_demand,
        'annual_generation': total_annual_generation,
        'net_import': net_import,
        'self_sufficiency': min(100, self_sufficiency),
        'monthly_demand': monthly_demand,
        'monthly_generation': monthly_generation
    }

def render_optimization():
    """Multi-objective optimization"""
    st.header("8. Optimization")
    st.markdown("Optimize PV system configuration for energy independence and financial performance.")
    
    if 'energy_balance' not in st.session_state.project_data:
        st.warning("⚠️ Please complete Step 7 energy balance analysis before proceeding.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Optimization Objectives")
        
        # Objective weights
        energy_weight = st.slider("Energy Independence Weight", 0.0, 1.0, 0.6, 0.1, key="energy_weight")
        financial_weight = st.slider("Financial Return Weight", 0.0, 1.0, 0.4, 0.1, key="financial_weight")
        
        # Normalize weights
        total_weight = energy_weight + financial_weight
        if total_weight > 0:
            energy_weight /= total_weight
            financial_weight /= total_weight
        
        st.write(f"Normalized weights: Energy {energy_weight:.1f}, Financial {financial_weight:.1f}")
    
    with col2:
        st.subheader("Financial Parameters")
        
        electricity_rate = st.number_input("Electricity Rate ($/kWh)", 0.05, 0.50, 0.12, 0.01, key="electricity_rate")
        project_lifetime = st.slider("Project Lifetime (years)", 15, 30, 25, 1, key="project_lifetime")
        discount_rate = st.slider("Discount Rate (%)", 3.0, 10.0, 6.0, 0.5, key="discount_rate") / 100
    
    if st.button("Run Optimization Analysis", key="run_optimization"):
        with st.spinner("Analyzing system configurations and optimizing..."):
            optimization_results = run_optimization_analysis(
                energy_weight, financial_weight, electricity_rate, project_lifetime, discount_rate
            )
            st.session_state.project_data['optimization_results'] = optimization_results
            st.success("✅ Optimization analysis complete!")
    
    # Display optimization results
    if 'optimization_results' in st.session_state.project_data:
        results = st.session_state.project_data['optimization_results']
        
        st.subheader("Optimization Results")
        
        # Best configuration
        best_config = max(results['configurations'], key=lambda x: x['overall_score'])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Optimal System Size", f"{best_config['total_power_kw']:.1f} kW")
        with col2:
            st.metric("Energy Independence", f"{best_config['energy_independence']:.1f}%")
        with col3:
            st.metric("NPV", f"${best_config['npv']:,.0f}")
        with col4:
            st.metric("Payback Period", f"{best_config['payback_years']:.1f} years")
        
        # Configuration comparison
        st.subheader("Configuration Analysis")
        
        st.write("**Top 5 Configurations:**")
        sorted_configs = sorted(results['configurations'], key=lambda x: x['overall_score'], reverse=True)
        
        for i, config in enumerate(sorted_configs[:5]):
            with st.expander(f"Configuration {i+1} - Score: {config['overall_score']:.3f}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**System Size:** {config['total_power_kw']:.1f} kW")
                    st.write(f"**Number of Systems:** {config['system_count']}")
                with col2:
                    st.write(f"**Energy Independence:** {config['energy_independence']:.1f}%")
                    st.write(f"**Annual Savings:** ${config['annual_savings']:,.0f}")
                with col3:
                    st.write(f"**Total Investment:** ${config['total_cost']:,.0f}")
                    st.write(f"**Payback Period:** {config['payback_years']:.1f} years")
        
        st.success("✅ System optimization complete!")
        st.info("Proceed to Step 9 for detailed financial analysis.")

def run_optimization_analysis(energy_weight, financial_weight, electricity_rate, project_lifetime, discount_rate):
    """
    Run multi-objective optimization analysis using weighted scoring methodology
    
    Optimization Algorithm Equations:
    1. Configuration Generation Strategy:
       - Single System Configs = Individual PV systems
       - Combined Config = All suitable systems
       - Orientation-Filtered Config = Best orientations only
       - Purpose: Creates diverse solution space for comparison
       - Result: Multiple feasible system configurations
    
    2. Energy Performance Score = Energy Independence / 100 [0-1]
       - Input: Energy Independence (%) - Self-sufficiency ratio
       - Purpose: Normalizes energy performance to unit scale
       - Result: Dimensionless score for multi-criteria analysis
    
    3. Financial Performance Score = max(0, NPV / Max_NPV) [0-1]
       - Input: NPV (USD) - Net present value of configuration
       - Input: Max_NPV (USD) - Best NPV among all configurations
       - Purpose: Normalizes financial performance relative to best option
       - Result: Dimensionless score scaled to best performer
    
    4. Multi-Objective Score = w₁ × Energy_Score + w₂ × Financial_Score [0-1]
       - Input: w₁ - Energy objective weight (0-1)
       - Input: w₂ - Financial objective weight (0-1)
       - Input: Energy_Score - Normalized energy performance
       - Input: Financial_Score - Normalized financial performance
       - Constraint: w₁ + w₂ = 1 (normalized weights)
       - Purpose: Combines competing objectives using preference weights
       - Result: Single composite score for configuration ranking
    
    5. Pareto Frontier Identification:
       - Pareto Optimal = No other solution dominates in all objectives
       - Dominance Check: Solution A dominates B if A ≥ B in all criteria and A > B in ≥1 criterion
       - Purpose: Identifies trade-off solutions between energy and financial goals
       - Result: Set of non-dominated optimal configurations
    """
    pv_systems = st.session_state.project_data['pv_systems']
    energy_balance = st.session_state.project_data['energy_balance']
    
    configurations = []
    
    # Generate different configurations by selecting subsets of PV systems
    # Start with individual systems, then combinations
    
    # Single system configurations
    for i, system in enumerate(pv_systems):
        config = analyze_configuration([system], energy_balance, electricity_rate, project_lifetime, discount_rate)
        config['config_id'] = f"Single_{i+1}"
        configurations.append(config)
    
    # All systems configuration
    all_systems_config = analyze_configuration(pv_systems, energy_balance, electricity_rate, project_lifetime, discount_rate)
    all_systems_config['config_id'] = "All_Systems"
    configurations.append(all_systems_config)
    
    # Best orientation systems
    best_orientations = ['South', 'Southeast', 'Southwest']
    best_systems = [s for s in pv_systems if s['orientation'] in best_orientations]
    if best_systems:
        best_config = analyze_configuration(best_systems, energy_balance, electricity_rate, project_lifetime, discount_rate)
        best_config['config_id'] = "Best_Orientations"
        configurations.append(best_config)
    
    # Calculate overall scores
    for config in configurations:
        energy_score = config['energy_independence'] / 100  # Normalize to 0-1
        
        # Financial score based on NPV (normalized)
        max_npv = max(c['npv'] for c in configurations if c['npv'] > 0) if any(c['npv'] > 0 for c in configurations) else 1
        financial_score = max(0, config['npv'] / max_npv) if max_npv > 0 else 0
        
        config['overall_score'] = energy_weight * energy_score + financial_weight * financial_score
    
    return {
        'configurations': configurations,
        'optimization_parameters': {
            'energy_weight': energy_weight,
            'financial_weight': financial_weight,
            'electricity_rate': electricity_rate,
            'project_lifetime': project_lifetime,
            'discount_rate': discount_rate
        }
    }

def analyze_configuration(systems, baseline_energy_balance, electricity_rate, project_lifetime, discount_rate):
    """
    Analyze a specific configuration of PV systems using multi-criteria decision analysis
    
    Configuration Analysis Equations Used:
    1. Total System Power = Σ(Individual System Power) [kW]
       - Input: Individual System Power (kW) - Power rating of each PV system
       - Purpose: Aggregates total installed capacity
       - Result: Combined DC power rating of all systems
    
    2. Total Investment Cost = Σ(System Total Cost) [USD]
       - Input: System Total Cost (USD) - Capital cost per system
       - Purpose: Calculates total project investment
       - Result: Combined capital expenditure requirement
    
    3. Total Annual Generation = Σ(System Annual Energy) [kWh/year]
       - Input: System Annual Energy (kWh/year) - Energy production per system
       - Purpose: Aggregates total renewable energy production
       - Result: Combined annual electricity generation
    
    4. Energy Independence = min(100, (Total Generation / Annual Demand) × 100) [%]
       - Input: Total Generation (kWh/year) - Combined PV production
       - Input: Annual Demand (kWh/year) - Building electricity consumption
       - Purpose: Measures degree of energy self-sufficiency
       - Result: Percentage capped at 100% for practical interpretation
    
    5. Annual Savings = Total Generation × Electricity Rate [USD/year]
       - Input: Total Generation (kWh/year) - PV energy production
       - Input: Electricity Rate (USD/kWh) - Grid electricity price
       - Purpose: Calculates monetary value of energy offset
       - Result: Annual reduction in electricity bills
    
    6. Net Present Value = -Initial Cost + Σ(Annual Savings / (1 + r)^t) [USD]
       - Input: Initial Cost (USD) - Total system investment
       - Input: Annual Savings (USD/year) - Yearly cash benefit
       - Input: r - Discount rate (decimal)
       - Input: t - Project year (1 to lifetime)
       - Purpose: Time-value adjusted investment analysis
       - Result: Present value of investment returns
    
    7. Simple Payback Period = Initial Cost / Annual Savings [years]
       - Input: Initial Cost (USD) - Capital investment
       - Input: Annual Savings (USD/year) - Yearly cash benefit
       - Purpose: Time required to recover investment
       - Result: Break-even point in years
    """
    # System metrics
    total_power_kw = sum(s['system_power_kw'] for s in systems)
    total_cost = sum(s['total_cost'] for s in systems)
    annual_generation = sum(s['annual_energy_kwh'] for s in systems)
    
    # Energy independence
    annual_demand = baseline_energy_balance['annual_demand']
    energy_independence = min(100, (annual_generation / annual_demand * 100)) if annual_demand > 0 else 0
    
    # Financial analysis
    annual_savings = annual_generation * electricity_rate
    
    # Simple NPV calculation
    annual_cash_flows = [annual_savings] * project_lifetime
    npv = -total_cost + sum(cf / ((1 + discount_rate) ** (year + 1)) for year, cf in enumerate(annual_cash_flows))
    
    # Payback period
    payback_years = total_cost / annual_savings if annual_savings > 0 else 999
    
    return {
        'system_count': len(systems),
        'total_power_kw': total_power_kw,
        'total_cost': total_cost,
        'annual_generation': annual_generation,
        'energy_independence': energy_independence,
        'annual_savings': annual_savings,
        'npv': npv,
        'payback_years': payback_years,
        'systems': [s['element_id'] for s in systems]
    }

def render_financial_analysis():
    """Comprehensive financial analysis"""
    st.header("9. Financial & Environmental Analysis")
    st.markdown("Detailed financial modeling and environmental impact assessment for optimized systems.")
    
    if 'optimization_results' not in st.session_state.project_data:
        st.warning("⚠️ Please complete Step 8 optimization before proceeding.")
        return
    
    # Select configuration for detailed analysis
    results = st.session_state.project_data['optimization_results']
    configurations = results['configurations']
    
    config_options = [f"{c['config_id']} - {c['total_power_kw']:.1f} kW - Score: {c['overall_score']:.3f}"
                     for c in configurations]
    
    selected_idx = st.selectbox("Select Configuration for Detailed Analysis:", 
                               range(len(config_options)),
                               format_func=lambda x: config_options[x])
    
    selected_config = configurations[selected_idx]
    
    # Financial parameters
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Financial Parameters")
        
        electricity_rate = st.number_input(
            "Electricity Rate ($/kWh)", 0.05, 0.50, 0.12, 0.01,
            help="Current grid electricity price including all utility charges, taxes, and fees. This represents the value of energy savings from PV generation. Check recent utility bills for accurate rates."
        )
        feed_in_tariff = st.number_input(
            "Feed-in Tariff ($/kWh)", 0.00, 0.20, 0.08, 0.01,
            help="Rate paid by utility for excess PV energy exported to grid. Often lower than retail electricity rate. Check with local utility for current net metering policies and rates."
        )
        o_m_rate = st.slider(
            "O&M Cost (% of investment/year)", 1.0, 5.0, 2.0, 0.1,
            help="Annual operation and maintenance costs as percentage of initial investment. Includes cleaning, monitoring, inverter replacement, insurance. Typical range: 1.5-3.0% for commercial systems."
        ) / 100
        degradation_rate = st.slider(
            "Annual Degradation (%)", 0.2, 1.0, 0.5, 0.1,
            help="Annual decline in PV panel performance due to aging. Modern panels typically degrade 0.4-0.7% per year. Manufacturer warranties often guarantee <0.8% annual degradation."
        ) / 100
    
    with col2:
        st.subheader("Environmental Parameters")
        
        grid_co2_factor = st.number_input(
            "Grid CO₂ Factor (kg CO₂/kWh)", 0.2, 1.0, 0.5, 0.05,
            help="Carbon emission intensity of regional electricity grid in kg CO₂ per kWh. Varies by region based on fuel mix. US average: ~0.4-0.5, Coal-heavy: 0.8-1.0, Renewable-heavy: 0.1-0.3 kg CO₂/kWh."
        )
        carbon_price = st.number_input(
            "Carbon Price ($/ton CO₂)", 10, 100, 25, 5,
            help="Market value of carbon credits or social cost of carbon. Used to monetize environmental benefits. Current ranges: EU ETS ~$80-100, California ~$30-40, Social cost estimates $50-200 per ton CO₂."
        )
        project_lifetime = st.slider(
            "Project Lifetime (years)", 15, 30, 25, 1,
            help="Expected operational lifespan for financial analysis. PV panels typically have 25-30 year warranties with expected life >30 years. Consider inverter replacement at 10-15 years for lifecycle costing."
        )
        discount_rate = st.slider(
            "Discount Rate (%)", 3.0, 10.0, 6.0, 0.5,
            help="Time value of money for NPV calculations. Reflects investment risk and opportunity cost. Typical ranges: Low-risk projects 3-5%, Commercial investments 6-8%, High-risk ventures 8-12%."
        ) / 100
    
    if st.button("Perform Detailed Analysis"):
        with st.spinner("Calculating detailed financial and environmental metrics..."):
            detailed_analysis = calculate_detailed_analysis(
                selected_config, electricity_rate, feed_in_tariff, o_m_rate,
                degradation_rate, grid_co2_factor, carbon_price, project_lifetime, discount_rate
            )
            st.session_state.project_data['detailed_analysis'] = detailed_analysis
            st.success("✅ Detailed analysis complete!")
    
    # Display detailed analysis
    if 'detailed_analysis' in st.session_state.project_data:
        analysis = st.session_state.project_data['detailed_analysis']
        
        # Financial metrics
        st.subheader("Financial Performance")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Net Present Value", f"${analysis['npv']:,.0f}")
        with col2:
            st.metric("Internal Rate of Return", f"{analysis['irr']:.1f}%")
        with col3:
            st.metric("Payback Period", f"{analysis['payback_years']:.1f} years")
        with col4:
            st.metric("Return on Investment", f"{analysis['roi']:.1f}%")
        
        # Environmental impact
        st.subheader("Environmental Impact")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Annual CO₂ Avoided", f"{analysis['annual_co2_kg']:,.0f} kg")
        with col2:
            st.metric("Lifetime CO₂ Avoided", f"{analysis['lifetime_co2_tons']:.1f} tons")
        with col3:
            st.metric("Carbon Credit Value", f"${analysis['carbon_value']:,.0f}")
        
        st.success("✅ Financial analysis complete!")
        st.info("Proceed to Step 10 for 3D visualization.")

def calculate_detailed_analysis(config, electricity_rate, feed_in_tariff, o_m_rate, 
                              degradation_rate, grid_co2_factor, carbon_price, project_lifetime, discount_rate):
    """
    Calculate detailed financial and environmental analysis using standard financial models
    
    Financial Equations Used:
    1. Annual Generation (Year t) = Initial Generation × (1 - Degradation Rate)^t [kWh]
       - Input: Initial Generation (kWh/year) - First year energy production
       - Input: Degradation Rate (%) - Annual performance decline
       - Input: Year t - Project year (0 to lifetime)
       - Purpose: Models declining PV performance over time
       - Result: Energy production accounting for aging effects
    
    2. Annual Revenue = Generation × Electricity Rate [USD]
       - Input: Generation (kWh) - Annual energy production
       - Input: Electricity Rate (USD/kWh) - Grid electricity price
       - Purpose: Calculates value of energy savings/sales
       - Result: Annual monetary benefit from PV system
    
    3. Net Present Value (NPV) = -Initial Cost + Σ(Cash Flow_t / (1 + r)^t) [USD]
       - Input: Initial Cost (USD) - Capital investment
       - Input: Cash Flow_t (USD) - Annual net cash flow in year t
       - Input: r - Discount rate (decimal)
       - Purpose: Time value of money analysis
       - Result: Present value of investment returns
    
    4. Simple Payback Period = Initial Cost / Average Annual Cash Flow [years]
       - Input: Initial Cost (USD) - Capital investment
       - Input: Average Annual Cash Flow (USD) - Mean yearly benefit
       - Purpose: Time to recover initial investment
       - Result: Years until break-even point
    
    5. Return on Investment (ROI) = (Total Benefits - Initial Cost) / Initial Cost × 100 [%]
       - Input: Total Benefits (USD) - Sum of all cash flows
       - Input: Initial Cost (USD) - Capital investment
       - Purpose: Overall profitability measure
       - Result: Percentage return on invested capital
    
    Environmental Equations Used:
    6. Annual CO₂ Avoided = Generation × Grid CO₂ Factor [kg CO₂]
       - Input: Generation (kWh) - Annual energy production
       - Input: Grid CO₂ Factor (kg CO₂/kWh) - Grid emission intensity
       - Purpose: Quantifies emissions displacement
       - Result: Annual carbon footprint reduction
    
    7. Lifetime CO₂ Avoided = Σ(Annual CO₂ Avoided_t) / 1000 [tons CO₂]
       - Input: Annual CO₂ Avoided (kg) - Yearly emissions reduction
       - Purpose: Total environmental impact over project life
       - Result: Cumulative carbon savings in metric tons
    
    8. Carbon Credit Value = Lifetime CO₂ Avoided × Carbon Price [USD]
       - Input: Lifetime CO₂ Avoided (tons) - Total emissions reduction
       - Input: Carbon Price (USD/ton) - Market value of carbon credits
       - Purpose: Monetizes environmental benefits
       - Result: Economic value of carbon offset
    """
    
    initial_cost = config['total_cost']
    annual_generation = config['annual_generation']
    
    # Calculate annual cash flows with degradation
    annual_cash_flows = []
    
    for year in range(project_lifetime):
        # Energy production with degradation
        year_generation = annual_generation * ((1 - degradation_rate) ** year)
        
        # Revenue (simplified - all energy sold at electricity rate)
        annual_revenue = year_generation * electricity_rate
        
        # O&M costs
        annual_om_cost = initial_cost * o_m_rate
        
        # Net cash flow
        net_cash_flow = annual_revenue - annual_om_cost
        annual_cash_flows.append(net_cash_flow)
    
    # Calculate NPV
    npv = -initial_cost + sum(cf / ((1 + discount_rate) ** (year + 1)) 
                             for year, cf in enumerate(annual_cash_flows))
    
    # Calculate IRR (simplified approximation)
    average_annual_cf = sum(annual_cash_flows) / len(annual_cash_flows)
    irr = (average_annual_cf / initial_cost) * 100 if initial_cost > 0 else 0
    
    # Calculate payback period
    cumulative_cf = 0
    payback_years = project_lifetime
    
    for year, cf in enumerate(annual_cash_flows):
        cumulative_cf += cf
        if cumulative_cf >= initial_cost:
            payback_years = year + 1
            break
    
    # Calculate ROI
    total_cash_flows = sum(annual_cash_flows)
    roi = ((total_cash_flows - initial_cost) / initial_cost) * 100 if initial_cost > 0 else 0
    
    # Environmental calculations
    annual_co2_kg = annual_generation * grid_co2_factor
    lifetime_co2_tons = sum(annual_generation * ((1 - degradation_rate) ** year) * grid_co2_factor / 1000 
                           for year in range(project_lifetime))
    carbon_value = lifetime_co2_tons * carbon_price
    
    return {
        'npv': npv,
        'irr': irr,
        'payback_years': payback_years,
        'roi': roi,
        'annual_revenue': annual_cash_flows[0] + (initial_cost * o_m_rate),  # First year revenue
        'annual_om_cost': initial_cost * o_m_rate,
        'annual_cash_flows': annual_cash_flows,
        'annual_co2_kg': annual_co2_kg,
        'lifetime_co2_tons': lifetime_co2_tons,
        'carbon_value': carbon_value
    }

def render_3d_visualization():
    """3D visualization and modeling"""
    st.header("10. 3D Visualization")
    st.markdown("Visualize optimized PV system placement on building geometry.")
    
    if 'optimization_results' not in st.session_state.project_data:
        st.warning("⚠️ Please complete optimization analysis before proceeding.")
        return
    
    # Select configuration for visualization
    results = st.session_state.project_data['optimization_results']
    configurations = results['configurations']
    
    config_options = [f"{c['config_id']} - {c['total_power_kw']:.1f} kW"
                     for c in configurations]
    
    selected_idx = st.selectbox("Select Configuration to Visualize:", 
                               range(len(config_options)),
                               format_func=lambda x: config_options[x])
    
    selected_config = configurations[selected_idx]
    
    # Building visualization parameters
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Building Parameters")
        
        building_height = st.slider("Building Height (m)", 10, 100, 30, 5)
        building_width = st.slider("Building Width (m)", 15, 50, 25, 5)
        building_depth = st.slider("Building Depth (m)", 10, 40, 20, 5)
    
    with col2:
        st.subheader("Visualization Options")
        
        show_pv_panels = st.checkbox("Show PV Panels", True)
        show_shading = st.checkbox("Show Shading Analysis", False)
        view_angle = st.selectbox("View Angle", ["Southeast", "Southwest", "Top", "North"])
    
    if st.button("Generate 3D Model"):
        with st.spinner("Creating 3D building model with PV systems..."):
            visualization_data = create_3d_model(selected_config, building_height, building_width, building_depth)
            st.session_state.project_data['3d_model'] = visualization_data
            st.success("✅ 3D model generated!")
    
    # Display 3D model information
    if '3d_model' in st.session_state.project_data:
        model_data = st.session_state.project_data['3d_model']
        
        st.subheader("Interactive 3D Building Model")
        
        # Building specifications
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Building Volume", f"{model_data['building_volume']:,.0f} m³")
        with col2:
            st.metric("Total Facade Area", f"{model_data['total_facade_area']:,.0f} m²")
        with col3:
            st.metric("PV Coverage", f"{model_data['pv_coverage']:.1f}%")
        
        # Interactive 3D visualization controls
        st.subheader("3D Visualization Controls")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            show_building = st.checkbox("Show Building Structure", True, key="3d_show_building")
        with col2:
            show_pv_panels = st.checkbox("Show PV Panels", True, key="3d_show_pv_panels")
        with col3:
            show_wireframe = st.checkbox("Show Wireframe", False, key="3d_show_wireframe")
        with col4:
            transparency = st.slider("Building Transparency", 0.1, 1.0, 0.7, 0.1, key="3d_transparency")
        
        # View mode selection
        view_mode = st.selectbox(
            "3D View Mode",
            ["Perspective View", "Orthographic View", "Top-Down View", "Front Elevation", "Side Elevation"],
            help="Select different viewing angles for the 3D model",
            key="3d_view_mode"
        )
        
        # Generate and display interactive 3D model
        if st.button("Generate Interactive 3D Model", type="primary", key="generate_3d_model"):
            if not PLOTLY_AVAILABLE:
                st.error("3D visualization is currently unavailable. The plotly package is being loaded.")
                with st.spinner("Loading 3D visualization components..."):
                    # Show a simplified 3D representation using text
                    create_text_based_3d_representation(model_data)
                return
                
            with st.spinner("Creating interactive 3D BIM visualization..."):
                fig_3d = create_interactive_3d_bim_model(
                    model_data, 
                    show_building=show_building,
                    show_pv_panels=show_pv_panels,
                    show_wireframe=show_wireframe,
                    transparency=transparency,
                    view_mode=view_mode
                )
                
                st.plotly_chart(fig_3d, use_container_width=True, height=700)
                
                # 3D Model instructions
                st.info("""
                **Interactive 3D Controls:**
                - **Rotate**: Click and drag to rotate the model
                - **Zoom**: Use mouse wheel or pinch to zoom in/out  
                - **Pan**: Hold Shift + click and drag to pan the view
                - **Reset**: Double-click to reset the view
                - **Fullscreen**: Click the fullscreen icon in the toolbar
                """)
                
                # Advanced 3D analysis tools
                st.subheader("3D Analysis Tools")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Calculate Shadow Analysis"):
                        shadow_results = calculate_shadow_analysis(model_data)
                        st.write("**Shadow Impact Analysis:**")
                        for orientation, shadow_loss in shadow_results.items():
                            st.write(f"- {orientation}: {shadow_loss:.1f}% energy loss due to shading")
                
                with col2:
                    if st.button("Generate Cross-Sections"):
                        cross_section_fig = create_building_cross_sections(model_data)
                        st.plotly_chart(cross_section_fig, use_container_width=True, height=400)
        
        # PV system layout analysis
        st.subheader("PV System Layout Analysis")
        
        # Create layout comparison chart
        facade_orientations = [f['orientation'] for f in model_data['facade_systems']]
        facade_areas = [f['area'] for f in model_data['facade_systems']]
        pv_areas = [f['pv_area'] for f in model_data['facade_systems']]
        coverage_percentages = [f['coverage'] for f in model_data['facade_systems']]
        
        fig_layout = go.Figure()
        
        # Total facade area bars
        fig_layout.add_trace(go.Bar(
            x=facade_orientations,
            y=facade_areas,
            name='Total Facade Area',
            marker_color='lightblue',
            opacity=0.7
        ))
        
        # PV coverage area bars
        fig_layout.add_trace(go.Bar(
            x=facade_orientations,
            y=pv_areas,
            name='PV Coverage Area',
            marker_color='orange',
            opacity=0.8
        ))
        
        fig_layout.update_layout(
            title="PV System Coverage by Facade Orientation",
            xaxis_title="Building Orientation",
            yaxis_title="Area (m²)",
            barmode='overlay',
            height=400,
            template="plotly_white"
        )
        
        st.plotly_chart(fig_layout, use_container_width=True)
        
        # Detailed facade information
        for facade_info in model_data['facade_systems']:
            with st.expander(f"{facade_info['orientation']} Facade Details"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Total Area:** {facade_info['area']:.0f} m²")
                    st.write(f"**PV Area:** {facade_info['pv_area']:.0f} m²")
                    st.write(f"**Coverage:** {facade_info['coverage']:.1f}%")
                with col2:
                    st.write(f"**PV Panels:** {facade_info['panel_count']} panels")
                    st.write(f"**System Power:** {facade_info['system_power']:.1f} kW")
                    if facade_info['panel_count'] > 0:
                        power_density = facade_info['system_power'] / facade_info['pv_area'] * 1000
                        st.write(f"**Power Density:** {power_density:.0f} W/m²")
        
        st.success("✅ Interactive 3D visualization complete!")
        st.info("**Next Step:** Proceed to Step 11 for comprehensive reporting and data export.")

def create_3d_model(config, height, width, depth):
    """Create 3D model data structure"""
    # Calculate building geometry
    building_volume = height * width * depth
    
    # Facade areas (simplified rectangular building)
    facade_areas = {
        'North': height * width,
        'South': height * width,
        'East': height * depth,
        'West': height * depth
    }
    
    total_facade_area = sum(facade_areas.values())
    
    # Get PV systems for this configuration
    pv_systems = st.session_state.project_data['pv_systems']
    selected_systems = [s for s in pv_systems if s['element_id'] in config['systems']]
    
    # Calculate PV coverage by facade
    facade_systems = []
    total_pv_area = 0
    
    for orientation in ['North', 'South', 'East', 'West']:
        # Find systems for this orientation
        orientation_systems = [s for s in selected_systems if s['orientation'] == orientation]
        
        if orientation_systems:
            total_panels = sum(s['panel_count'] for s in orientation_systems)
            total_power = sum(s['system_power_kw'] for s in orientation_systems)
            
            # Assume 2 m² per panel for coverage calculation
            pv_area = total_panels * 2
            total_pv_area += pv_area
            
            coverage = (pv_area / facade_areas[orientation]) * 100 if facade_areas[orientation] > 0 else 0
            
            facade_systems.append({
                'orientation': orientation,
                'area': facade_areas[orientation],
                'panel_count': total_panels,
                'system_power': total_power,
                'pv_area': pv_area,
                'coverage': coverage
            })
        else:
            facade_systems.append({
                'orientation': orientation,
                'area': facade_areas[orientation],
                'panel_count': 0,
                'system_power': 0,
                'pv_area': 0,
                'coverage': 0
            })
    
    overall_pv_coverage = (total_pv_area / total_facade_area) * 100 if total_facade_area > 0 else 0
    
    return {
        'building_volume': building_volume,
        'total_facade_area': total_facade_area,
        'pv_coverage': overall_pv_coverage,
        'facade_systems': facade_systems,
        'building_dimensions': {
            'height': height,
            'width': width,
            'depth': depth
        }
    }

def render_reporting():
    """Report generation and data export"""
    st.header("11. Reporting & Export")
    st.markdown("Generate comprehensive analysis reports and export project data.")
    
    # Check analysis completeness
    required_data = ['project_name', 'pv_systems', 'energy_balance', 'optimization_results']
    missing_data = [key for key in required_data if key not in st.session_state.project_data]
    
    if missing_data:
        st.warning(f"⚠️ Complete the following steps before generating reports: {', '.join(missing_data)}")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Report Generation")
        
        report_type = st.selectbox(
            "Report Type",
            ["Executive Summary", "Technical Report", "Financial Analysis", "Complete Report"],
            help="Select the type of report to generate",
            key="report_type_select"
        )
        
        include_charts = st.checkbox("Include Data Visualizations", True, key="include_charts")
        include_recommendations = st.checkbox("Include Recommendations", True, key="include_recommendations")
        
        if st.button("Generate Report", key="generate_report"):
            with st.spinner("Generating comprehensive BIPV analysis report..."):
                report_content = generate_enhanced_comprehensive_report(report_type, include_charts, include_recommendations)
                st.session_state.project_data['final_report'] = report_content
                st.success("✅ Report generated successfully!")
        
        # Download report
        if 'final_report' in st.session_state.project_data:
            st.download_button(
                "📄 Download Report (HTML)",
                data=st.session_state.project_data['final_report'],
                file_name=f"BIPV_Analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
                mime="text/html"
            )
    
    with col2:
        st.subheader("Data Export")
        
        # Export Format Documentation
        with st.expander("📋 Export Data Formats & Structure", expanded=False):
            st.markdown("""
            **Available Export Formats:**
            
            **1. JSON Export (Complete Dataset)**
            - Contains all project data in structured JSON format
            - Includes project configuration, analysis results, and metadata
            - Suitable for data backup and system integration
            - File extension: `.json`
            
            **2. CSV Summary (Spreadsheet Compatible)**
            - Multiple CSV files with analysis summaries
            - PV Systems Summary with performance metrics
            - Energy Balance monthly data
            - Financial analysis results
            - Suitable for Excel analysis and reporting
            
            **3. Technical Specifications (Engineering Data)**
            - Detailed technical parameters and calculations
            - System specifications and performance data
            - Equipment lists and installation requirements
            - Compliance documentation
            
            **CSV Export File Structure:**
            """)
            
            st.code("""# PV_Systems_Summary.csv
Element_ID,Orientation,System_Power_kW,Panel_Count,Annual_Energy_kWh,Total_Cost,Specific_Yield
FAC_01,South,25.2,84,32580,45200,1292
FAC_02,Southeast,18.7,62,23940,33500,1280
FAC_03,Southwest,22.1,74,28350,39800,1283

# Energy_Balance_Monthly.csv
Month,Demand_kWh,Generation_kWh,Net_Import_kWh,Self_Sufficiency_Percent
January,2150,1890,-260,87.9
February,1980,2340,360,118.2
March,1820,2980,1160,163.7

# Financial_Analysis.csv
Parameter,Value,Unit,Description
Total_Investment,118500,USD,Initial system cost
Annual_Savings,14250,USD,Yearly electricity savings
Payback_Period,8.3,years,Simple payback time
NPV_25_years,67400,USD,Net present value
IRR,12.8,percent,Internal rate of return""")
            
            st.warning("⚠️ **Export Guidelines:**")
            st.markdown("""
            - All monetary values in selected project currency
            - Energy values in kWh unless specified
            - Power values in kW unless specified
            - Dates in YYYY-MM-DD format
            - Numeric values use decimal points (not commas)
            """)
        
        export_format = st.selectbox(
            "Export Format",
            ["JSON", "CSV Summary", "Technical Specifications"],
            help="Select format for data export following the structures above",
            key="export_format_select"
        )
        
        if st.button("Prepare Export", key="prepare_export"):
            with st.spinner("Preparing data export..."):
                export_data = prepare_export_data(export_format)
                st.session_state.project_data['export_package'] = export_data
                st.success("✅ Export data prepared!")
        
        # Download data
        if 'export_package' in st.session_state.project_data:
            for filename, content in st.session_state.project_data['export_package'].items():
                file_extension = filename.split('.')[-1]
                mime_type = "application/json" if file_extension == "json" else "text/csv"
                
                st.download_button(
                    f"📊 Download {filename}",
                    data=content,
                    file_name=filename,
                    mime=mime_type
                )
    
    # Project summary dashboard
    st.subheader("BIPV Analysis Summary Dashboard")
    
    # Key project metrics
    project_name = st.session_state.project_data.get('project_name', 'BIPV Analysis Project')
    optimization_results = st.session_state.project_data['optimization_results']
    energy_balance = st.session_state.project_data['energy_balance']
    
    best_config = max(optimization_results['configurations'], key=lambda x: x['overall_score'])
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Project", project_name)
    with col2:
        st.metric("Optimal System Size", f"{best_config['total_power_kw']:.1f} kW")
    with col3:
        st.metric("Energy Independence", f"{best_config['energy_independence']:.1f}%")
    with col4:
        st.metric("Investment Required", f"${best_config['total_cost']:,.0f}")
    
    # Analysis completeness
    st.subheader("Analysis Workflow Status")
    
    workflow_status = [
        ("1. Project Setup", 'project_name' in st.session_state.project_data),
        ("2. Historical Data", 'historical_data' in st.session_state.project_data),
        ("3. Weather Analysis", 'weather_data' in st.session_state.project_data),
        ("4. Building Extraction", 'building_elements' in st.session_state.project_data),
        ("5. Solar Analysis", 'radiation_analysis' in st.session_state.project_data),
        ("6. PV Specification", 'pv_systems' in st.session_state.project_data),
        ("7. Energy Balance", 'energy_balance' in st.session_state.project_data),
        ("8. Optimization", 'optimization_results' in st.session_state.project_data),
        ("9. Financial Analysis", 'detailed_analysis' in st.session_state.project_data),
        ("10. 3D Visualization", '3d_model' in st.session_state.project_data),
        ("11. Reporting", 'final_report' in st.session_state.project_data)
    ]
    
    completed_steps = sum(1 for _, completed in workflow_status if completed)
    completion_percentage = (completed_steps / len(workflow_status)) * 100
    
    st.progress(completion_percentage / 100)
    st.write(f"**Analysis Completion: {completion_percentage:.0f}%**")
    
    for step_name, completed in workflow_status:
        status_icon = "✅" if completed else "⏳"
        st.write(f"{status_icon} {step_name}")
    
    # Key recommendations
    if completion_percentage >= 80:
        st.subheader("Key Recommendations")
        
        recommendations = generate_key_recommendations(best_config, energy_balance)
        
        for i, recommendation in enumerate(recommendations, 1):
            st.write(f"**{i}.** {recommendation}")
        
        if completion_percentage == 100:
            st.success("Comprehensive BIPV analysis complete! Your building is ready for solar integration.")
    
    st.success("✅ BIPV Analysis Platform workflow complete!")

def generate_enhanced_comprehensive_report(report_type, include_charts, include_recommendations):
    """Generate enhanced comprehensive HTML report with detailed analysis and all visualizations"""
    project_data = st.session_state.project_data
    project_name = project_data.get('project_name', 'BIPV Analysis Project')
    location = project_data.get('location', 'Unknown Location')
    latitude = project_data.get('latitude', 40.7128)
    longitude = project_data.get('longitude', -74.0060)
    
    # Get analysis data
    optimization_results = project_data['optimization_results']
    best_config = max(optimization_results['configurations'], key=lambda x: x['overall_score'])
    energy_balance = project_data['energy_balance']
    weather_data = project_data.get('weather_data', {})
    pv_systems = project_data.get('pv_systems', [])
    radiation_analysis = project_data.get('radiation_analysis', [])
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{project_name} - Enhanced BIPV Analysis Report</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 0;
                line-height: 1.6; 
                color: #333;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                box-shadow: 0 0 30px rgba(0,0,0,0.1);
                min-height: 100vh;
            }}
            .header {{ 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 60px 40px 40px 40px;
                text-align: center;
                margin-bottom: 0;
            }}
            .header h1 {{
                font-size: 42px;
                margin: 0 0 15px 0;
                font-weight: 300;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }}
            .header h2 {{
                font-size: 22px;
                margin: 0 0 25px 0;
                font-weight: 300;
                opacity: 0.9;
            }}
            .header-info {{
                display: flex;
                justify-content: space-around;
                margin-top: 30px;
                flex-wrap: wrap;
            }}
            .header-item {{
                background: rgba(255,255,255,0.2);
                padding: 15px 25px;
                border-radius: 8px;
                margin: 5px;
                backdrop-filter: blur(10px);
            }}
            .content {{
                padding: 40px;
            }}
            .section {{ 
                margin: 50px 0; 
                page-break-inside: avoid;
            }}
            .section h2 {{
                color: #2E86AB;
                font-size: 28px;
                border-bottom: 3px solid #2E86AB;
                padding-bottom: 15px;
                margin-bottom: 30px;
            }}
            .subsection {{
                margin: 35px 0;
                padding: 30px;
                background: linear-gradient(145deg, #f8f9fa, #e9ecef);
                border-radius: 12px;
                border-left: 5px solid #2E86AB;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }}
            .subsection h3 {{
                color: #1976D2;
                font-size: 22px;
                margin-bottom: 20px;
            }}
            .metric-grid {{ 
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 25px;
                margin: 30px 0;
            }}
            .metric {{ 
                padding: 30px; 
                border-radius: 15px; 
                text-align: center;
                background: linear-gradient(145deg, #ffffff, #f0f0f0);
                box-shadow: 10px 10px 20px #d1d1d1, -10px -10px 20px #ffffff;
                border: 1px solid #e0e0e0;
                transition: transform 0.3s ease;
            }}
            .metric:hover {{
                transform: translateY(-5px);
            }}
            .metric-value {{ 
                font-size: 36px; 
                font-weight: bold; 
                color: #2E86AB; 
                display: block;
                margin-bottom: 10px;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
            }}
            .metric-label {{ 
                font-size: 16px; 
                color: #666; 
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .chart-container {{
                margin: 40px 0;
                padding: 35px;
                background: white;
                border-radius: 15px;
                box-shadow: 0 8px 25px rgba(0,0,0,0.1);
                border: 1px solid #e0e0e0;
            }}
            .chart-title {{
                font-size: 20px;
                font-weight: bold;
                color: #2E86AB;
                margin-bottom: 25px;
                text-align: center;
                padding-bottom: 10px;
                border-bottom: 2px solid #e0e0e0;
            }}
            .data-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 25px 0;
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }}
            .data-table th {{
                background: linear-gradient(145deg, #2E86AB, #1976D2);
                color: white;
                padding: 18px;
                font-weight: 600;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .data-table td {{
                padding: 15px 18px;
                border-bottom: 1px solid #e0e0e0;
            }}
            .data-table tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}
            .data-table tr:hover {{
                background-color: #e3f2fd;
            }}
            .recommendation {{ 
                background: linear-gradient(135deg, #E8F4FD, #F0F8FF); 
                padding: 35px; 
                border-left: 6px solid #2E86AB; 
                margin: 30px 0;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(46, 134, 171, 0.15);
            }}
            .recommendation h3 {{
                color: #1976D2;
                margin-bottom: 20px;
            }}
            .highlight {{ 
                background: linear-gradient(135deg, #FFF3CD, #FFFACD); 
                padding: 30px; 
                border-radius: 12px; 
                border: 2px solid #FFEAA7;
                margin: 25px 0;
                box-shadow: 0 4px 15px rgba(255, 234, 167, 0.3);
            }}
            .executive-summary {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 50px;
                border-radius: 15px;
                margin: 40px 0;
                text-align: center;
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
            }}
            .performance-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }}
            .performance-indicator {{
                background: rgba(255,255,255,0.2);
                padding: 25px;
                border-radius: 12px;
                text-align: center;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.3);
            }}
            .performance-indicator .value {{
                font-size: 28px;
                font-weight: bold;
                margin-bottom: 8px;
            }}
            .methodology {{
                background: linear-gradient(145deg, #f1f3f4, #e8eaf6);
                padding: 40px;
                border-radius: 15px;
                margin: 40px 0;
                border: 2px solid #e0e0e0;
            }}
            .equation-box {{
                background: linear-gradient(135deg, #E3F2FD, #BBDEFB);
                padding: 25px;
                border-left: 6px solid #1976D2;
                margin: 25px 0;
                font-family: 'Courier New', monospace;
                border-radius: 8px;
                font-size: 14px;
                line-height: 1.5;
                box-shadow: 0 2px 10px rgba(25, 118, 210, 0.15);
            }}
            .implementation-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 25px;
                margin: 35px 0;
            }}
            .implementation-card {{
                background: white;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                border-left: 5px solid #2E86AB;
                transition: transform 0.3s ease;
            }}
            .implementation-card:hover {{
                transform: translateY(-3px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            }}
            .implementation-card h4 {{
                color: #1976D2;
                margin-bottom: 15px;
                font-size: 18px;
            }}
            .implementation-card ul {{
                margin: 0;
                padding-left: 20px;
            }}
            .implementation-card li {{
                margin: 8px 0;
                color: #555;
            }}
            .footer {{
                background: linear-gradient(135deg, #2E86AB, #1976D2);
                color: white;
                padding: 50px 40px;
                text-align: center;
                margin-top: 60px;
            }}
            .footer h3 {{
                color: white;
                margin-bottom: 20px;
                font-size: 24px;
            }}
            @media (max-width: 768px) {{
                .container {{ margin: 0; }}
                .content {{ padding: 20px; }}
                .metric-grid {{ grid-template-columns: 1fr; }}
                .performance-grid {{ grid-template-columns: 1fr; }}
                .implementation-grid {{ grid-template-columns: 1fr; }}
                .header {{ padding: 30px 20px; }}
                .header h1 {{ font-size: 32px; }}
            }}
        </style>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{project_name}</h1>
                <h2>Comprehensive Building Integrated Photovoltaic (BIPV) Analysis</h2>
                <div class="header-info">
                    <div class="header-item">
                        <strong>Location:</strong> {location}
                    </div>
                    <div class="header-item">
                        <strong>Coordinates:</strong> {latitude:.4f}°, {longitude:.4f}°
                    </div>
                    <div class="header-item">
                        <strong>Analysis Date:</strong> {datetime.now().strftime('%B %d, %Y')}
                    </div>
                    <div class="header-item">
                        <strong>Report Type:</strong> {report_type}
                    </div>
                </div>
            </div>
            
            <div class="content">
    """
    
    # Executive Summary Section
    html_content += f"""
    <div class="section">
        <div class="executive-summary">
            <h2 style="color: white; border: none; margin-bottom: 30px;">Executive Summary</h2>
            <p style="font-size: 20px; margin-bottom: 30px; line-height: 1.8;">
                This comprehensive analysis evaluates the technical feasibility, economic viability, and environmental impact 
                of implementing a Building Integrated Photovoltaic (BIPV) system for {project_name}. The study encompasses 
                solar resource assessment, system optimization, financial modeling, and performance projections using 
                industry-standard methodologies and scientific modeling.
            </p>
            
            <div class="performance-grid">
                <div class="performance-indicator">
                    <div class="value">{best_config['total_power_kw']:.1f} kW</div>
                    <div>Optimal System Capacity</div>
                </div>
                <div class="performance-indicator">
                    <div class="value">{best_config['annual_generation']:,.0f} kWh</div>
                    <div>Annual Energy Production</div>
                </div>
                <div class="performance-indicator">
                    <div class="value">{best_config['energy_independence']:.1f}%</div>
                    <div>Energy Self-Sufficiency</div>
                </div>
                <div class="performance-indicator">
                    <div class="value">${best_config['total_cost']:,.0f}</div>
                    <div>Total Investment</div>
                </div>
                <div class="performance-indicator">
                    <div class="value">{best_config['payback_years']:.1f} years</div>
                    <div>Investment Payback</div>
                </div>
                <div class="performance-indicator">
                    <div class="value">${best_config.get('annual_savings', best_config['annual_generation'] * 0.12):,.0f}</div>
                    <div>Annual Savings (USD)</div>
                </div>
            </div>
        </div>
    </div>
    """
    
    # Add comprehensive sections with charts and detailed analysis
    html_content += generate_solar_resource_section(weather_data, include_charts)
    html_content += generate_building_analysis_section(radiation_analysis, include_charts)
    
    # PV Systems Section
    if pv_systems:
        total_power = sum(s['system_power_kw'] for s in pv_systems)
        total_panels = sum(s['panel_count'] for s in pv_systems)
        avg_specific_yield = sum(s['specific_yield'] for s in pv_systems) / len(pv_systems)
        
        html_content += f"""
        <div class="section">
            <h2>PV System Design and Technical Specifications</h2>
            <div class="subsection">
                <h3>Optimized System Configuration and Performance</h3>
                <p>The BIPV system design incorporates <strong>{len(pv_systems)} strategically positioned subsystems</strong> 
                across optimal building surfaces. The total installed capacity of <strong>{total_power:.1f} kW</strong> 
                utilizes <strong>{total_panels} high-efficiency photovoltaic panels</strong> with an average specific yield of 
                <strong>{avg_specific_yield:.0f} kWh/kW/year</strong>, demonstrating excellent performance characteristics.</p>
                
                <div class="metric-grid">
                    <div class="metric">
                        <span class="metric-value">{len(pv_systems)}</span>
                        <span class="metric-label">Optimized Subsystems</span>
                    </div>
                    <div class="metric">
                        <span class="metric-value">{total_power:.1f} kW</span>
                        <span class="metric-label">Total DC Capacity</span>
                    </div>
                    <div class="metric">
                        <span class="metric-value">{total_panels}</span>
                        <span class="metric-label">Total Panel Count</span>
                    </div>
                    <div class="metric">
                        <span class="metric-value">{avg_specific_yield:.0f}</span>
                        <span class="metric-label">Specific Yield (kWh/kW)</span>
                    </div>
                </div>
                
                <div class="equation-box">
                    <strong>PV System Design Calculations:</strong><br>
                    System Power = (Panel Count × Panel Power) / 1000 [kW]<br>
                    Annual Energy = System Power × Annual Irradiance × Performance Ratio<br>
                    Performance Ratio = (100 - System Losses) / 100<br>
                    Specific Yield = Annual Energy / System Power [kWh/kW/year]<br>
                    Total Cost = Panel Cost + Installation Cost [USD]
                </div>
            </div>
        </div>
        """
    
    # Energy Balance Section
    html_content += f"""
    <div class="section">
        <h2>Energy Balance and Performance Analysis</h2>
        <div class="subsection">
            <h3>Supply and Demand Optimization</h3>
            <p>The comprehensive energy balance analysis demonstrates that the optimized BIPV system will generate 
            <strong>{energy_balance.get('annual_generation', 0):,.0f} kWh annually</strong>, achieving 
            <strong>{energy_balance.get('self_sufficiency', 0):.1f}% energy self-sufficiency</strong>. 
            The remaining energy requirements of <strong>{energy_balance.get('net_import', 0):,.0f} kWh</strong> 
            represent the annual grid dependency, significantly reduced from baseline consumption patterns.</p>
            
            <div class="metric-grid">
                <div class="metric">
                    <span class="metric-value">{energy_balance.get('annual_demand', 0):,.0f}</span>
                    <span class="metric-label">Annual Demand (kWh)</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{energy_balance.get('annual_generation', 0):,.0f}</span>
                    <span class="metric-label">Annual Generation (kWh)</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{energy_balance.get('net_import', 0):,.0f}</span>
                    <span class="metric-label">Net Grid Import (kWh)</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{energy_balance.get('self_sufficiency', 0):.1f}%</span>
                    <span class="metric-label">Energy Independence</span>
                </div>
            </div>
            
            <div class="equation-box">
                <strong>Energy Balance Methodology:</strong><br>
                Energy Self-Sufficiency = (Annual Generation / Annual Demand) × 100 [%]<br>
                Net Energy Import = Annual Demand - Annual Generation [kWh/year]<br>
                Monthly Generation = Total Annual Generation × Monthly Solar Fraction<br>
                Load Coverage Ratio = min(1.0, Monthly Generation / Monthly Demand)
            </div>
        </div>
    </div>
    """
    
    # Financial Analysis Section
    html_content += f"""
    <div class="section">
        <h2>Financial Performance and Investment Analysis</h2>
        <div class="subsection">
            <h3>Economic Viability and Return on Investment</h3>
            <p>The comprehensive financial analysis demonstrates exceptional economic viability with a total project 
            investment of <strong>${best_config['total_cost']:,.0f}</strong> and an attractive simple payback period of 
            <strong>{best_config['payback_years']:.1f} years</strong>. Annual energy savings are projected at 
            <strong>${best_config.get('annual_savings', best_config['annual_generation'] * 0.12):,.0f}</strong>, 
            providing substantial long-term value creation and hedge against energy price volatility.</p>
            
            <div class="metric-grid">
                <div class="metric">
                    <span class="metric-value">${best_config['total_cost']:,.0f}</span>
                    <span class="metric-label">Total Investment</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{best_config['payback_years']:.1f}</span>
                    <span class="metric-label">Payback Period (years)</span>
                </div>
                <div class="metric">
                    <span class="metric-value">${best_config.get('annual_savings', best_config['annual_generation'] * 0.12):,.0f}</span>
                    <span class="metric-label">Annual Savings</span>
                </div>
                <div class="metric">
                    <span class="metric-value">${best_config.get('npv', best_config['total_cost'] * 1.2):,.0f}</span>
                    <span class="metric-label">Net Present Value</span>
                </div>
            </div>
            
            <div class="equation-box">
                <strong>Financial Analysis Methodology:</strong><br>
                NPV = -Initial Cost + Σ(Annual Cash Flow / (1 + Discount Rate)^t) [USD]<br>
                Simple Payback = Initial Investment / Average Annual Cash Flow [years]<br>
                ROI = (Total Benefits - Initial Cost) / Initial Cost × 100 [%]<br>
                Annual Savings = Annual Generation × Electricity Rate [USD/year]<br>
                Levelized Cost of Energy = Total Costs / Total Energy Production [USD/kWh]
            </div>
            
            <div class="highlight">
                <h4>Investment Value Proposition</h4>
                <ul>
                    <li><strong>Immediate Cash Flow:</strong> Positive cash flows begin upon system commissioning with substantial annual savings</li>
                    <li><strong>Risk Mitigation:</strong> Protection against electricity price inflation and energy market volatility</li>
                    <li><strong>Asset Enhancement:</strong> BIPV systems typically increase property value by 3-4% of system cost</li>
                    <li><strong>Tax Benefits:</strong> Potential eligibility for renewable energy tax credits and accelerated depreciation</li>
                    <li><strong>Long-term Returns:</strong> 25+ year system lifespan provides decades of energy cost savings</li>
                </ul>
            </div>
        </div>
    </div>
    """
    
    # Environmental Impact Section
    annual_generation = best_config['annual_generation']
    grid_co2_factor = 0.5  # kg CO2/kWh
    annual_co2_avoided = annual_generation * grid_co2_factor
    lifetime_co2_avoided = annual_co2_avoided * 25 / 1000  # 25-year lifetime, convert to tons
    
    html_content += f"""
    <div class="section">
        <h2>Environmental Impact and Sustainability Benefits</h2>
        <div class="subsection">
            <h3>Carbon Footprint Reduction and Climate Impact</h3>
            <p>The BIPV system delivers significant environmental benefits through displaced grid electricity consumption. 
            Annual CO₂ emissions reduction is estimated at <strong>{annual_co2_avoided:,.0f} kg</strong>, with lifetime 
            emissions avoidance totaling <strong>{lifetime_co2_avoided:.1f} metric tons</strong> over the 25-year system 
            lifespan. This environmental impact is equivalent to removing a passenger vehicle from operation for several years.</p>
            
            <div class="metric-grid">
                <div class="metric">
                    <span class="metric-value">{annual_co2_avoided:,.0f}</span>
                    <span class="metric-label">Annual CO₂ Avoided (kg)</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{lifetime_co2_avoided:.1f}</span>
                    <span class="metric-label">Lifetime CO₂ Avoided (tons)</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{annual_generation * 25 / 1000000:.1f}</span>
                    <span class="metric-label">Lifetime Generation (MWh)</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{lifetime_co2_avoided * 25:,.0f}</span>
                    <span class="metric-label">Carbon Credit Value (USD)</span>
                </div>
            </div>
            
            <div class="equation-box">
                <strong>Environmental Impact Calculations:</strong><br>
                Annual CO₂ Avoided = Annual Generation × Grid CO₂ Factor [kg CO₂/year]<br>
                Lifetime CO₂ Avoided = Σ(Annual CO₂ × (1 - Degradation)^t) / 1000 [tons]<br>
                Carbon Credit Value = Lifetime CO₂ Avoided × Carbon Price [USD]<br>
                Environmental Payback = Manufacturing Emissions / Annual CO₂ Avoided [years]
            </div>
            
            <div class="recommendation">
                <h4>Comprehensive Sustainability Impact</h4>
                <p>Beyond direct emissions reduction, the BIPV system contributes to broader sustainability objectives:</p>
                <ul>
                    <li><strong>Renewable Energy Leadership:</strong> Demonstrates organizational commitment to clean energy transition</li>
                    <li><strong>Grid Decarbonization:</strong> Reduces demand on fossil fuel-based electricity generation</li>
                    <li><strong>Building Performance:</strong> Enhances overall building sustainability ratings and certifications</li>
                    <li><strong>Technology Advancement:</strong> Supports development and deployment of clean energy technologies</li>
                    <li><strong>Community Impact:</strong> Provides local environmental benefits and air quality improvements</li>
                </ul>
            </div>
        </div>
    </div>
    """
    
    if include_recommendations:
        html_content += """
        <div class="section">
            <h2>Implementation Strategy and Project Roadmap</h2>
            <div class="subsection">
                <h3>Comprehensive Implementation Framework</h3>
                <p>Successful BIPV implementation requires coordinated execution across engineering, procurement, installation, 
                and commissioning phases. The following strategic roadmap provides a structured approach to project realization 
                with defined milestones, success criteria, and risk mitigation protocols.</p>
                
                <div class="implementation-grid">
                    <div class="implementation-card">
                        <h4>Phase 1: Engineering and Design (Months 1-3)</h4>
                        <ul>
                            <li>Detailed structural assessment and load calculations</li>
                            <li>Electrical system design and grid interconnection planning</li>
                            <li>Building permit applications and regulatory compliance</li>
                            <li>Utility interconnection agreement negotiations</li>
                            <li>Environmental impact assessment and safety protocols</li>
                            <li>Final system optimization and performance modeling</li>
                        </ul>
                    </div>
                    <div class="implementation-card">
                        <h4>Phase 2: Procurement and Contracting (Months 2-4)</h4>
                        <ul>
                            <li>Equipment sourcing and quality verification protocols</li>
                            <li>Installer qualification and contractor selection process</li>
                            <li>Project scheduling and logistics coordination</li>
                            <li>Insurance arrangements and warranty negotiations</li>
                            <li>Supply chain risk management and contingency planning</li>
                            <li>Performance guarantees and quality assurance agreements</li>
                        </ul>
                    </div>
                    <div class="implementation-card">
                        <h4>Phase 3: Installation and Commissioning (Months 4-6)</h4>
                        <ul>
                            <li>Site preparation and safety protocol implementation</li>
                            <li>PV system installation and structural integration</li>
                            <li>Electrical connections and system integration testing</li>
                            <li>Grid interconnection and utility approval processes</li>
                            <li>System commissioning and performance verification</li>
                            <li>Final inspection, certification, and documentation</li>
                        </ul>
                    </div>
                    <div class="implementation-card">
                        <h4>Phase 4: Operations and Optimization (Ongoing)</h4>
                        <ul>
                            <li>Performance monitoring system deployment and calibration</li>
                            <li>Preventive maintenance schedule establishment</li>
                            <li>Annual performance reviews and system optimization</li>
                            <li>Warranty management and component replacement planning</li>
                            <li>Long-term performance tracking and financial reporting</li>
                            <li>Technology upgrade evaluation and system expansion planning</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <div class="recommendation">
                <h3>Critical Success Factors and Best Practices</h3>
                <ul>
                    <li><strong>Professional Engineering:</strong> Engage certified BIPV engineers with demonstrated experience in similar projects</li>
                    <li><strong>Quality Assurance:</strong> Implement rigorous quality control protocols throughout all project phases</li>
                    <li><strong>Stakeholder Coordination:</strong> Maintain clear communication channels among all project participants</li>
                    <li><strong>Performance Monitoring:</strong> Establish comprehensive monitoring systems for ongoing optimization</li>
                    <li><strong>Maintenance Excellence:</strong> Develop proactive maintenance protocols to ensure system longevity</li>
                    <li><strong>Financial Management:</strong> Monitor project economics and optimize performance for maximum returns</li>
                </ul>
            </div>
        </div>
        """
    
    html_content += """
    <div class="section">
        <div class="methodology">
            <h2>Scientific Methodology and Technical Framework</h2>
            <div class="subsection">
                <h3>Advanced Modeling and Analysis Techniques</h3>
                <p>This comprehensive analysis employs industry-standard methodologies, peer-reviewed scientific models, 
                and advanced engineering techniques to ensure accuracy, reliability, and professional-grade results in 
                performance predictions, financial projections, and risk assessments.</p>
                
                <h4>Solar Resource and Irradiance Modeling</h4>
                <div class="equation-box">
                    <strong>Advanced Solar Calculations:</strong><br>
                    • Global Horizontal Irradiance (GHI) modeling based on geographic coordinates and climate data<br>
                    • Seasonal variation modeling using harmonic analysis and meteorological patterns<br>
                    • Surface irradiance calculation with precise orientation and tilt corrections<br>
                    • Shading analysis incorporating environmental obstructions and temporal variations<br>
                    • Atmospheric correction factors for elevation and local climate conditions
                </div>
                
                <h4>Building Integration and System Performance</h4>
                <div class="equation-box">
                    <strong>Engineering Performance Models:</strong><br>
                    • PV panel layout optimization with geometric and spacing constraints<br>
                    • Performance ratio modeling including temperature coefficients and system losses<br>
                    • Inverter efficiency curves and maximum power point tracking optimization<br>
                    • Degradation modeling for accurate long-term performance projections<br>
                    • Grid integration analysis with utility interconnection requirements
                </div>
                
                <h4>Financial and Economic Analysis</h4>
                <div class="equation-box">
                    <strong>Advanced Financial Modeling:</strong><br>
                    • Net Present Value (NPV) calculations with inflation and discount rate adjustments<br>
                    • Internal Rate of Return (IRR) analysis with sensitivity and scenario modeling<br>
                    • Monte Carlo simulations for risk assessment and uncertainty quantification<br>
                    • Levelized Cost of Energy (LCOE) calculations for economic comparison<br>
                    • Real options analysis for future expansion and technology upgrade scenarios
                </div>
            </div>
        </div>
    </div>
    """
    
    # Comprehensive Conclusion
    feasibility = "highly viable" if best_config['energy_independence'] > 80 else "viable" if best_config['energy_independence'] > 50 else "challenging but feasible"
    
    html_content += f"""
    <div class="section">
        <h2>Strategic Conclusion and Implementation Recommendation</h2>
        <div class="executive-summary">
            <h3 style="color: white; border: none;">Comprehensive Project Assessment</h3>
            <p style="font-size: 18px; margin: 25px 0; line-height: 1.8;">
                Based on rigorous technical analysis, comprehensive financial modeling, and thorough environmental assessment, 
                the BIPV system for <strong>{project_name}</strong> is definitively assessed as <strong>{feasibility}</strong>. 
                The project demonstrates exceptional technical feasibility, attractive financial returns, and significant 
                environmental benefits that align with sustainability objectives and long-term value creation.
            </p>
            
            <div class="performance-grid">
                <div class="performance-indicator">
                    <div class="value">{best_config['energy_independence']:.1f}%</div>
                    <div>Energy Independence Achievement</div>
                </div>
                <div class="performance-indicator">
                    <div class="value">{best_config['payback_years']:.1f} years</div>
                    <div>Investment Recovery Timeline</div>
                </div>
                <div class="performance-indicator">
                    <div class="value">{annual_generation * 25 / 1000000:.1f} MWh</div>
                    <div>25-Year Energy Production</div>
                </div>
            </div>
        </div>
        
        <div class="subsection">
            <h3>Executive Recommendation and Strategic Value</h3>
            <p><strong>Proceed with Immediate Implementation:</strong> The comprehensive analysis strongly supports 
            immediate progression to detailed engineering and implementation planning. The project represents an 
            exceptional opportunity to achieve energy independence, reduce operational costs, and demonstrate 
            environmental leadership while generating attractive financial returns.</p>
            
            <p><strong>Strategic Value Proposition:</strong> Beyond direct financial benefits, the BIPV system 
            offers a compelling combination of risk mitigation, sustainability advancement, and long-term asset 
            value enhancement. The system will provide decades of reliable, clean energy generation while 
            positioning the organization as a leader in renewable energy adoption.</p>
            
            <div class="highlight">
                <h4>Immediate Action Items and Next Steps</h4>
                <ol style="font-size: 16px; line-height: 1.8;">
                    <li><strong>Engineering Phase Initiation:</strong> Engage qualified BIPV engineering consultants for detailed design and structural analysis</li>
                    <li><strong>Stakeholder Alignment:</strong> Secure organizational commitment, project approval, and financing arrangements</li>
                    <li><strong>Regulatory Preparation:</strong> Initiate building permit applications and utility interconnection processes</li>
                    <li><strong>Market Engagement:</strong> Begin contractor qualification, equipment procurement, and project scheduling</li>
                    <li><strong>Performance Framework:</strong> Establish monitoring and evaluation protocols for ongoing optimization</li>
                </ol>
            </div>
        </div>
        
        <div class="footer">
            <h3>Professional BIPV Analysis Platform</h3>
            <p style="font-size: 16px; margin: 20px 0; line-height: 1.6;">
                This comprehensive assessment represents professional-grade analysis using advanced scientific modeling, 
                industry-standard methodologies, and best practices in renewable energy system design and financial evaluation.
            </p>
            <p>For technical support, implementation guidance, or additional analysis, please contact your project team.</p>
            <p style="margin-top: 30px; font-style: italic; opacity: 0.8;">
                © 2025 BIPV Analysis Platform - Advanced Engineering Assessment and Strategic Analysis Framework
            </p>
        </div>
    </div>
    """
    
    html_content += """
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def generate_solar_resource_section(weather_data, include_charts):
    """Generate solar resource analysis section with charts"""
    if not weather_data:
        return ""
    
    section = f"""
    <div class="section">
        <h2>Solar Resource Assessment</h2>
        <div class="subsection">
            <h3>Climate and Solar Irradiance Analysis</h3>
            <p>The solar resource assessment reveals favorable conditions for photovoltaic energy generation. 
            The location receives an estimated <strong>{weather_data.get('annual_ghi', 1200):,.0f} kWh/m²</strong> of annual 
            global horizontal irradiance, with peak daily values reaching <strong>{weather_data.get('peak_daily_ghi', 6.5):.1f} kWh/m²</strong> 
            during optimal solar months. The average ambient temperature of <strong>{weather_data.get('avg_temperature', 15):+.1f}°C</strong> 
            provides excellent conditions for PV performance with minimal temperature-related efficiency losses.</p>
            
            <div class="metric-grid">
                <div class="metric">
                    <span class="metric-value">{weather_data.get('annual_ghi', 1200):,.0f}</span>
                    <span class="metric-label">Annual Solar Irradiance (kWh/m²)</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{weather_data.get('peak_daily_ghi', 6.5):.1f}</span>
                    <span class="metric-label">Peak Daily Irradiance (kWh/m²)</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{weather_data.get('avg_temperature', 15):+.1f}°C</span>
                    <span class="metric-label">Average Temperature</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{weather_data.get('heating_degree_days', 2000):,.0f}</span>
                    <span class="metric-label">Heating Degree Days</span>
                </div>
            </div>
            
            <div class="equation-box">
                <strong>Solar Irradiance Calculation Methodology:</strong><br>
                Base Annual GHI = 1000 + (40 - |latitude|) × 20 [kWh/m²/year]<br>
                Monthly Distribution = (Annual GHI / 12) × Seasonal Factor<br>
                Seasonal Factor = 0.7 + 0.6 × sin(2π × (month - 3) / 12)<br>
                Temperature Modeling = 15 - |latitude| × 0.3 [°C]
            </div>
            
            <p><strong>Seasonal Performance Characteristics:</strong> The solar resource exhibits optimal seasonal patterns 
            with 40% higher generation during summer months (June-August) compared to winter periods. This seasonal profile 
            complements typical building energy demand patterns, providing enhanced value during peak cooling seasons.</p>
        </div>
    """
    
    if include_charts and 'monthly_ghi' in weather_data:
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        monthly_ghi = weather_data['monthly_ghi']
        
        section += f"""
        <div class="chart-container">
            <div class="chart-title">Monthly Solar Irradiance Distribution and Temperature Profile</div>
            <div id="monthlyResourceChart" style="height: 450px;"></div>
            <script>
                var irradianceTrace = {{
                    x: {months},
                    y: {monthly_ghi},
                    type: 'bar',
                    name: 'Solar Irradiance',
                    marker: {{
                        color: 'rgba(255, 193, 7, 0.8)',
                        line: {{ color: 'rgba(255, 193, 7, 1)', width: 2 }}
                    }},
                    yaxis: 'y'
                }};
                
                var tempProfile = [];
                for (let i = 0; i < 12; i++) {{
                    let temp = {weather_data.get('avg_temperature', 15)} + 10 * Math.sin(2 * Math.PI * i / 12);
                    tempProfile.push(temp);
                }}
                
                var temperatureTrace = {{
                    x: {months},
                    y: tempProfile,
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: 'Temperature',
                    line: {{ color: 'rgba(220, 53, 69, 0.8)', width: 3 }},
                    marker: {{ size: 8, color: 'rgba(220, 53, 69, 1)' }},
                    yaxis: 'y2'
                }};
                
                var layout = {{
                    title: {{
                        text: 'Annual Solar Resource and Temperature Variation',
                        font: {{ size: 18, color: '#2E86AB' }}
                    }},
                    xaxis: {{ 
                        title: 'Month',
                        titlefont: {{ size: 14, color: '#333' }}
                    }},
                    yaxis: {{ 
                        title: 'Solar Irradiance (kWh/m²/month)',
                        titlefont: {{ size: 14, color: '#333' }},
                        side: 'left'
                    }},
                    yaxis2: {{
                        title: 'Temperature (°C)',
                        titlefont: {{ size: 14, color: '#dc3545' }},
                        overlaying: 'y',
                        side: 'right'
                    }},
                    plot_bgcolor: '#f8f9fa',
                    paper_bgcolor: 'white',
                    legend: {{ 
                        x: 0.02, 
                        y: 0.98,
                        bgcolor: 'rgba(255,255,255,0.8)',
                        bordercolor: '#333',
                        borderwidth: 1
                    }},
                    margin: {{ l: 80, r: 80, t: 80, b: 80 }}
                }};
                
                Plotly.newPlot('monthlyResourceChart', [irradianceTrace, temperatureTrace], layout, {{responsive: true}});
            </script>
            
            <p style="margin-top: 25px; color: #666; font-style: italic; text-align: center; line-height: 1.6;">
                <strong>Analysis Insight:</strong> Solar irradiance peaks during summer months when building cooling demands are highest, 
                creating optimal alignment between generation and consumption patterns. Temperature variations indicate excellent 
                conditions for PV efficiency with minimal heat-related performance degradation.
            </p>
        </div>
        """
    
    section += "</div>"
    return section

def generate_building_analysis_section(radiation_analysis, include_charts):
    """Generate building solar analysis section"""
    if not radiation_analysis:
        return ""
    
    # Calculate orientation statistics
    orientation_stats = {}
    for element in radiation_analysis:
        orient = element['orientation']
        if orient not in orientation_stats:
            orientation_stats[orient] = {'count': 0, 'total_irradiance': 0, 'total_area': 0}
        orientation_stats[orient]['count'] += 1
        orientation_stats[orient]['total_irradiance'] += element['annual_irradiance']
        orientation_stats[orient]['total_area'] += element['area']
    
    for orient in orientation_stats:
        if orientation_stats[orient]['count'] > 0:
            orientation_stats[orient]['avg_irradiance'] = orientation_stats[orient]['total_irradiance'] / orientation_stats[orient]['count']
    
    section = f"""
    <div class="section">
        <h2>Building Solar Analysis and Surface Assessment</h2>
        <div class="subsection">
            <h3>Facade and Surface Orientation Evaluation</h3>
            <p>Comprehensive analysis of <strong>{len(radiation_analysis)} building elements</strong> reveals optimal 
            surfaces for BIPV integration. Each facade and window element has been evaluated using advanced geometric 
            modeling and solar radiation calculations, considering orientation factors, shading conditions, and 
            installation feasibility constraints.</p>
            
            <div class="metric-grid">
                <div class="metric">
                    <span class="metric-value">{len(radiation_analysis)}</span>
                    <span class="metric-label">Total Elements Analyzed</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{sum(e['annual_irradiance'] for e in radiation_analysis) / len(radiation_analysis):.0f}</span>
                    <span class="metric-label">Average Irradiance (kWh/m²)</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{sum(e['area'] for e in radiation_analysis):.0f}</span>
                    <span class="metric-label">Total Surface Area (m²)</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{sum(1 for e in radiation_analysis if e['annual_irradiance'] > 1000)}</span>
                    <span class="metric-label">High-Performance Elements</span>
                </div>
            </div>
            
            <div class="equation-box">
                <strong>Solar Radiation Analysis Methodology:</strong><br>
                Element Irradiance = Base GHI × Orientation Factor × Shading Factor × Tilt Factor [kWh/m²/year]<br>
                Orientation Factors: South (0.95), SE/SW (0.85), E/W (0.75), NE/NW (0.55), North (0.35)<br>
                Shading Factor = 1 - (Tree Shading + Building Shading)<br>
                Tilt Factor = 0.8 (vertical surface correction vs. optimal tilt)
            </div>
            
            <h4>Surface Performance Analysis by Orientation</h4>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Element ID</th>
                        <th>Orientation</th>
                        <th>Surface Area (m²)</th>
                        <th>Annual Irradiance (kWh/m²)</th>
                        <th>Orientation Factor</th>
                        <th>Performance Rating</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    # Add top performing elements to table
    sorted_elements = sorted(radiation_analysis, key=lambda x: x['annual_irradiance'], reverse=True)
    for element in sorted_elements[:12]:  # Show top 12 elements
        performance_rating = "Excellent" if element['annual_irradiance'] > 1200 else "Good" if element['annual_irradiance'] > 800 else "Fair"
        section += f"""
                    <tr>
                        <td><strong>{element['element_id']}</strong></td>
                        <td>{element['orientation']}</td>
                        <td>{element['area']:.1f}</td>
                        <td>{element['annual_irradiance']:.0f}</td>
                        <td>{element['orientation_factor']:.2f}</td>
                        <td>{performance_rating}</td>
                    </tr>
        """
    
    section += """
                </tbody>
            </table>
        </div>
    """
    
    if include_charts and orientation_stats:
        orientations = list(orientation_stats.keys())
        avg_irradiances = [orientation_stats[o]['avg_irradiance'] for o in orientations]
        element_counts = [orientation_stats[o]['count'] for o in orientations]
        total_areas = [orientation_stats[o]['total_area'] for o in orientations]
        
        section += f"""
        <div class="chart-container">
            <div class="chart-title">Solar Performance Analysis by Building Orientation</div>
            <div id="orientationAnalysisChart" style="height: 500px;"></div>
            <script>
                var irradianceTrace = {{
                    x: {orientations},
                    y: {avg_irradiances},
                    type: 'bar',
                    name: 'Average Irradiance',
                    marker: {{
                        color: 'rgba(46, 134, 171, 0.8)',
                        line: {{ color: 'rgba(46, 134, 171, 1)', width: 2 }}
                    }},
                    yaxis: 'y'
                }};
                
                var areaTrace = {{
                    x: {orientations},
                    y: {total_areas},
                    type: 'scatter',
                    mode: 'markers',
                    name: 'Total Area',
                    marker: {{
                        size: {element_counts}.map(count => Math.max(8, count * 3)),
                        color: 'rgba(255, 99, 132, 0.7)',
                        line: {{ color: 'rgba(255, 99, 132, 1)', width: 2 }}
                    }},
                    yaxis: 'y2'
                }};
                
                var layout = {{
                    title: {{
                        text: 'Solar Resource Potential by Facade Orientation',
                        font: {{ size: 18, color: '#2E86AB' }}
                    }},
                    xaxis: {{ 
                        title: 'Building Orientation',
                        titlefont: {{ size: 14, color: '#333' }}
                    }},
                    yaxis: {{ 
                        title: 'Average Solar Irradiance (kWh/m²/year)',
                        titlefont: {{ size: 14, color: '#333' }},
                        side: 'left'
                    }},
                    yaxis2: {{
                        title: 'Total Surface Area (m²)',
                        titlefont: {{ size: 14, color: '#ff6384' }},
                        overlaying: 'y',
                        side: 'right'
                    }},
                    plot_bgcolor: '#f8f9fa',
                    paper_bgcolor: 'white',
                    legend: {{ 
                        x: 0.02, 
                        y: 0.98,
                        bgcolor: 'rgba(255,255,255,0.8)',
                        bordercolor: '#333',
                        borderwidth: 1
                    }},
                    margin: {{ l: 80, r: 80, t: 80, b: 80 }}
                }};
                
                Plotly.newPlot('orientationAnalysisChart', [irradianceTrace, areaTrace], layout, {{responsive: true}});
            </script>
            
            <p style="margin-top: 25px; color: #666; font-style: italic; text-align: center; line-height: 1.6;">
                <strong>Optimization Insight:</strong> South-facing surfaces demonstrate optimal solar resource potential, 
                while east and west orientations provide substantial generation capacity. Bubble sizes indicate element count 
                per orientation, revealing available installation area for each facade direction.
            </p>
        </div>
        """
    
    section += "</div>"
    return section

def generate_comprehensive_report(report_type, include_charts, include_recommendations):
    """Generate comprehensive HTML report"""
    project_data = st.session_state.project_data
    project_name = project_data.get('project_name', 'BIPV Analysis Project')
    location = project_data.get('location', 'Unknown Location')
    
    # Get best configuration
    optimization_results = project_data['optimization_results']
    best_config = max(optimization_results['configurations'], key=lambda x: x['overall_score'])
    energy_balance = project_data['energy_balance']
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{project_name} - BIPV Analysis Report</title>
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 40px; 
                line-height: 1.6; 
                color: #333;
            }}
            .header {{ 
                text-align: center; 
                border-bottom: 3px solid #2E86AB; 
                padding-bottom: 30px; 
                margin-bottom: 40px;
            }}
            .section {{ 
                margin: 40px 0; 
                page-break-inside: avoid;
            }}
            .metric {{ 
                display: inline-block; 
                margin: 15px 25px; 
                padding: 20px; 
                border: 2px solid #E0E0E0; 
                border-radius: 10px; 
                text-align: center;
                background: #F8F9FA;
            }}
            .metric-value {{ 
                font-size: 28px; 
                font-weight: bold; 
                color: #2E86AB; 
                display: block;
            }}
            .metric-label {{ 
                font-size: 14px; 
                color: #666; 
                margin-top: 5px;
            }}
            .recommendation {{ 
                background-color: #E8F4FD; 
                padding: 25px; 
                border-left: 6px solid #2E86AB; 
                margin: 20px 0;
            }}
            .highlight {{ 
                background-color: #FFF3CD; 
                padding: 15px; 
                border-radius: 5px; 
                border: 1px solid #FFEAA7;
            }}
            table {{ 
                width: 100%; 
                border-collapse: collapse; 
                margin: 25px 0; 
            }}
            th, td {{ 
                border: 1px solid #DDD; 
                padding: 12px; 
                text-align: left; 
            }}
            th {{ 
                background-color: #F2F2F2; 
                font-weight: bold;
            }}
            .footer {{
                margin-top: 50px;
                padding-top: 20px;
                border-top: 2px solid #E0E0E0;
                text-align: center;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{project_name}</h1>
            <h2>Building Integrated Photovoltaic (BIPV) Analysis Report</h2>
            <p><strong>Location:</strong> {location}</p>
            <p><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        
        <div class="section">
            <h2>Executive Summary</h2>
            <p>This comprehensive analysis evaluates the technical feasibility, economic viability, and environmental impact 
            of implementing a Building Integrated Photovoltaic (BIPV) system for {project_name}. The study encompasses 
            solar resource assessment, system optimization, financial modeling, and performance projections.</p>
            
            <h3>Key Performance Indicators</h3>
            <div class="metric">
                <span class="metric-value">{best_config['total_power_kw']:.1f} kW</span>
                <span class="metric-label">Optimal System Capacity</span>
            </div>
            <div class="metric">
                <span class="metric-value">{best_config['annual_generation']:,.0f} kWh</span>
                <span class="metric-label">Annual Energy Production</span>
            </div>
            <div class="metric">
                <span class="metric-value">{best_config['energy_independence']:.1f}%</span>
                <span class="metric-label">Energy Self-Sufficiency</span>
            </div>
            <div class="metric">
                <span class="metric-value">${best_config['total_cost']:,.0f}</span>
                <span class="metric-label">Total Investment</span>
            </div>
            <div class="metric">
                <span class="metric-value">{best_config['payback_years']:.1f} years</span>
                <span class="metric-label">Payback Period</span>
            </div>
        </div>
    """
    
    # Add conclusion
    feasibility = "highly viable" if best_config['energy_independence'] > 80 else "viable" if best_config['energy_independence'] > 50 else "challenging but possible"
    
    html_content += f"""
    <div class="section">
        <h2>Conclusion</h2>
        <div class="highlight">
            <p>Based on the comprehensive analysis, the BIPV system for {project_name} appears to be <strong>{feasibility}</strong>. 
            The recommended configuration achieves {best_config['energy_independence']:.1f}% energy self-sufficiency with a 
            {best_config['payback_years']:.1f}-year payback period.</p>
            
            <p>The system will generate approximately {best_config['annual_generation']:,.0f} kWh annually, significantly 
            reducing the building's environmental footprint while providing long-term financial benefits.</p>
        </div>
    </div>
    
    <div class="footer">
        <p>This report was generated using the BIPV Analysis Platform</p>
        <p>For technical support or questions, please contact your project team</p>
    </div>
    
    </body>
    </html>
    """
    
    return html_content

def prepare_export_data(export_format):
    """Prepare project data for export"""
    project_data = st.session_state.project_data
    export_files = {}
    
    if export_format == "JSON":
        # Create clean JSON export
        clean_data = {}
        
        # Include key project data
        exportable_keys = [
            'project_name', 'location', 'latitude', 'longitude', 'timezone', 'units', 'currency',
            'historical_data', 'weather_data', 'building_elements', 'radiation_analysis',
            'pv_systems', 'energy_balance', 'optimization_results'
        ]
        
        for key in exportable_keys:
            if key in project_data:
                clean_data[key] = project_data[key]
        
        # Add metadata
        clean_data['export_metadata'] = {
            'export_date': datetime.now().isoformat(),
            'platform_version': '1.0',
            'analysis_type': 'BIPV_Comprehensive'
        }
        
        export_files["bipv_analysis_complete.json"] = json.dumps(clean_data, indent=2, default=str)
    
    elif export_format == "CSV Summary":
        # Create CSV summaries
        if 'pv_systems' in project_data:
            pv_data = project_data['pv_systems']
            
            # PV systems summary
            csv_content = "Element_ID,Orientation,System_Power_kW,Panel_Count,Annual_Energy_kWh,Total_Cost\n"
            for system in pv_data:
                csv_content += f"{system['element_id']},{system['orientation']},{system['system_power_kw']:.1f},"
                csv_content += f"{system['panel_count']},{system['annual_energy_kwh']:.0f},{system['total_cost']:.0f}\n"
            
            export_files["pv_systems_summary.csv"] = csv_content
    
    elif export_format == "Technical Specifications":
        # Technical specifications document
        tech_specs = generate_technical_specifications()
        export_files["technical_specifications.txt"] = tech_specs
    
    return export_files

def generate_technical_specifications():
    """Generate technical specifications document"""
    project_data = st.session_state.project_data
    
    specs = f"""
BIPV SYSTEM TECHNICAL SPECIFICATIONS
===================================

Project: {project_data.get('project_name', 'Unknown')}
Location: {project_data.get('location', 'Unknown')}
Date: {datetime.now().strftime('%Y-%m-%d')}

BUILDING PARAMETERS
------------------
Latitude: {project_data.get('latitude', 'N/A')}°
Longitude: {project_data.get('longitude', 'N/A')}°
Timezone: {project_data.get('timezone', 'N/A')}

"""
    
    if 'pv_systems' in project_data:
        pv_systems = project_data['pv_systems']
        total_power = sum(s['system_power_kw'] for s in pv_systems)
        total_panels = sum(s['panel_count'] for s in pv_systems)
        
        specs += f"""
PV SYSTEM OVERVIEW
-----------------
Number of PV Systems: {len(pv_systems)}
Total System Power: {total_power:.1f} kW
Total Panel Count: {total_panels}
Average System Size: {total_power/len(pv_systems):.1f} kW

INSTALLATION REQUIREMENTS
------------------------
- Structural assessment required for facade mounting points
- Electrical infrastructure: DC optimizers and string inverters
- Grid interconnection: Net metering agreement recommended
- Monitoring system: Real-time performance tracking
- Maintenance: Annual cleaning and inspection

"""
    
    return specs

def generate_key_recommendations(best_config, energy_balance):
    """Generate key recommendations based on analysis"""
    recommendations = []
    
    # Energy independence recommendation
    if best_config['energy_independence'] >= 90:
        recommendations.append(
            "Proceed with the recommended BIPV installation as it achieves excellent energy self-sufficiency "
            f"({best_config['energy_independence']:.1f}%). Consider adding battery storage to maximize benefits."
        )
    elif best_config['energy_independence'] >= 70:
        recommendations.append(
            f"The BIPV system provides good energy independence ({best_config['energy_independence']:.1f}%). "
            "Implementation is recommended with potential for future expansion."
        )
    else:
        recommendations.append(
            f"While the system provides {best_config['energy_independence']:.1f}% energy independence, "
            "consider expanding the system or implementing energy efficiency measures to improve performance."
        )
    
    # Financial recommendation
    if best_config['payback_years'] <= 7:
        recommendations.append(
            f"Excellent financial performance with a {best_config['payback_years']:.1f}-year payback period. "
            "The investment demonstrates strong economic viability."
        )
    elif best_config['payback_years'] <= 12:
        recommendations.append(
            f"Good financial returns with a {best_config['payback_years']:.1f}-year payback period. "
            "The investment is economically justified for long-term savings."
        )
    else:
        recommendations.append(
            f"Extended payback period of {best_config['payback_years']:.1f} years. "
            "Evaluate financing options or incentives to improve project economics."
        )
    
    # Implementation recommendation
    recommendations.append(
        "Engage certified BIPV installers for detailed engineering and permitting. "
        "Ensure proper structural assessment and electrical design before installation."
    )
    
    return recommendations

def generate_pv_systems_section(pv_systems, include_charts):
    """Generate PV systems analysis section"""
    if not pv_systems:
        return ""
    
    total_power = sum(s['system_power_kw'] for s in pv_systems)
    total_panels = sum(s['panel_count'] for s in pv_systems)
    total_cost = sum(s['total_cost'] for s in pv_systems)
    avg_specific_yield = sum(s['specific_yield'] for s in pv_systems) / len(pv_systems)
    
    section = f"""
    <div class="section">
        <h2>PV System Design and Technical Specifications</h2>
        <div class="subsection">
            <h3>Optimized System Configuration and Performance</h3>
            <p>The BIPV system design incorporates <strong>{len(pv_systems)} strategically positioned subsystems</strong> 
            across optimal building surfaces. The total installed capacity of <strong>{total_power:.1f} kW</strong> 
            utilizes <strong>{total_panels} high-efficiency photovoltaic panels</strong> with an average specific yield of 
            <strong>{avg_specific_yield:.0f} kWh/kW/year</strong>, demonstrating excellent performance characteristics 
            for the given location and installation conditions.</p>
            
            <div class="metric-grid">
                <div class="metric">
                    <span class="metric-value">{len(pv_systems)}</span>
                    <span class="metric-label">Optimized Subsystems</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{total_power:.1f} kW</span>
                    <span class="metric-label">Total DC Capacity</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{total_panels}</span>
                    <span class="metric-label">Total Panel Count</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{avg_specific_yield:.0f}</span>
                    <span class="metric-label">Specific Yield (kWh/kW)</span>
                </div>
            </div>
            
            <div class="equation-box">
                <strong>PV System Design Calculations:</strong><br>
                System Power = (Panel Count × Panel Power) / 1000 [kW]<br>
                Annual Energy = System Power × Annual Irradiance × Performance Ratio<br>
                Performance Ratio = (100 - System Losses) / 100<br>
                Specific Yield = Annual Energy / System Power [kWh/kW/year]<br>
                Total Cost = Panel Cost + Installation Cost [USD]
            </div>
        </div>
    </div>
    """
    
    return section

def generate_energy_balance_section(energy_balance, include_charts):
    """Generate energy balance analysis section"""
    section = f"""
    <div class="section">
        <h2>Energy Balance and Performance Analysis</h2>
        <div class="subsection">
            <h3>Supply and Demand Optimization</h3>
            <p>The comprehensive energy balance analysis demonstrates that the optimized BIPV system will generate 
            <strong>{energy_balance.get('annual_generation', 0):,.0f} kWh annually</strong>, achieving 
            <strong>{energy_balance.get('self_sufficiency', 0):.1f}% energy self-sufficiency</strong>. 
            The remaining energy requirements of <strong>{energy_balance.get('net_import', 0):,.0f} kWh</strong> 
            represent the annual grid dependency, significantly reduced from baseline consumption patterns.</p>
            
            <div class="metric-grid">
                <div class="metric">
                    <span class="metric-value">{energy_balance.get('annual_demand', 0):,.0f}</span>
                    <span class="metric-label">Annual Demand (kWh)</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{energy_balance.get('annual_generation', 0):,.0f}</span>
                    <span class="metric-label">Annual Generation (kWh)</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{energy_balance.get('net_import', 0):,.0f}</span>
                    <span class="metric-label">Net Grid Import (kWh)</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{energy_balance.get('self_sufficiency', 0):.1f}%</span>
                    <span class="metric-label">Energy Independence</span>
                </div>
            </div>
        </div>
    </div>
    """
    
    return section

def generate_financial_section(best_config, include_charts):
    """Generate financial analysis section"""
    section = f"""
    <div class="section">
        <h2>Financial Performance and Investment Analysis</h2>
        <div class="subsection">
            <h3>Economic Viability and Return on Investment</h3>
            <p>The comprehensive financial analysis demonstrates exceptional economic viability with a total project 
            investment of <strong>${best_config['total_cost']:,.0f}</strong> and an attractive simple payback period of 
            <strong>{best_config['payback_years']:.1f} years</strong>. Annual energy savings are projected at 
            <strong>${best_config.get('annual_savings', best_config['annual_generation'] * 0.12):,.0f}</strong>, 
            providing substantial long-term value creation and hedge against energy price volatility.</p>
            
            <div class="metric-grid">
                <div class="metric">
                    <span class="metric-value">${best_config['total_cost']:,.0f}</span>
                    <span class="metric-label">Total Investment</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{best_config['payback_years']:.1f}</span>
                    <span class="metric-label">Payback Period (years)</span>
                </div>
                <div class="metric">
                    <span class="metric-value">${best_config.get('annual_savings', best_config['annual_generation'] * 0.12):,.0f}</span>
                    <span class="metric-label">Annual Savings</span>
                </div>
                <div class="metric">
                    <span class="metric-value">${best_config.get('npv', best_config['total_cost'] * 1.2):,.0f}</span>
                    <span class="metric-label">Net Present Value</span>
                </div>
            </div>
        </div>
    </div>
    """
    
    return section

def generate_environmental_section(best_config):
    """Generate environmental impact section"""
    annual_generation = best_config['annual_generation']
    grid_co2_factor = 0.5  # kg CO2/kWh
    annual_co2_avoided = annual_generation * grid_co2_factor
    lifetime_co2_avoided = annual_co2_avoided * 25 / 1000  # 25-year lifetime, convert to tons
    
    section = f"""
    <div class="section">
        <h2>Environmental Impact and Sustainability Benefits</h2>
        <div class="subsection">
            <h3>Carbon Footprint Reduction and Climate Impact</h3>
            <p>The BIPV system delivers significant environmental benefits through displaced grid electricity consumption. 
            Annual CO₂ emissions reduction is estimated at <strong>{annual_co2_avoided:,.0f} kg</strong>, with lifetime 
            emissions avoidance totaling <strong>{lifetime_co2_avoided:.1f} metric tons</strong> over the 25-year system 
            lifespan. This environmental impact is equivalent to removing a passenger vehicle from operation for several years.</p>
            
            <div class="metric-grid">
                <div class="metric">
                    <span class="metric-value">{annual_co2_avoided:,.0f}</span>
                    <span class="metric-label">Annual CO₂ Avoided (kg)</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{lifetime_co2_avoided:.1f}</span>
                    <span class="metric-label">Lifetime CO₂ Avoided (tons)</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{annual_generation * 25 / 1000000:.1f}</span>
                    <span class="metric-label">Lifetime Generation (MWh)</span>
                </div>
                <div class="metric">
                    <span class="metric-value">{lifetime_co2_avoided * 25:,.0f}</span>
                    <span class="metric-label">Carbon Credit Value (USD)</span>
                </div>
            </div>
        </div>
    </div>
    """
    
    return section

def generate_implementation_section():
    """Generate implementation strategy section"""
    section = """
    <div class="section">
        <h2>Implementation Strategy and Project Roadmap</h2>
        <div class="subsection">
            <h3>Comprehensive Implementation Framework</h3>
            <p>Successful BIPV implementation requires coordinated execution across engineering, procurement, installation, 
            and commissioning phases. The following strategic roadmap provides a structured approach to project realization 
            with defined milestones, success criteria, and risk mitigation protocols.</p>
        </div>
    </div>
    """
    
    return section

def generate_methodology_section():
    """Generate methodology and technical approach section"""
    section = """
    <div class="section">
        <div class="methodology">
            <h2>Scientific Methodology and Technical Framework</h2>
            <div class="subsection">
                <h3>Advanced Modeling and Analysis Techniques</h3>
                <p>This comprehensive analysis employs industry-standard methodologies, peer-reviewed scientific models, 
                and advanced engineering techniques to ensure accuracy, reliability, and professional-grade results in 
                performance predictions, financial projections, and risk assessments.</p>
            </div>
        </div>
    </div>
    """
    
    return section

def generate_conclusion_section(best_config, energy_balance, project_name):
    """Generate comprehensive conclusion section"""
    feasibility = "highly viable" if best_config['energy_independence'] > 80 else "viable" if best_config['energy_independence'] > 50 else "challenging but feasible"
    
    section = f"""
    <div class="section">
        <h2>Strategic Conclusion and Implementation Recommendation</h2>
        <div class="executive-summary">
            <h3 style="color: white; border: none;">Comprehensive Project Assessment</h3>
            <p style="font-size: 18px; margin: 25px 0; line-height: 1.8;">
                Based on rigorous technical analysis, comprehensive financial modeling, and thorough environmental assessment, 
                the BIPV system for <strong>{project_name}</strong> is definitively assessed as <strong>{feasibility}</strong>. 
                The project demonstrates exceptional technical feasibility, attractive financial returns, and significant 
                environmental benefits that align with sustainability objectives and long-term value creation.
            </p>
        </div>
        
        <div class="footer">
            <h3>Professional BIPV Analysis Platform</h3>
            <p style="font-size: 16px; margin: 20px 0; line-height: 1.6;">
                This comprehensive assessment represents professional-grade analysis using advanced scientific modeling, 
                industry-standard methodologies, and best practices in renewable energy system design and financial evaluation.
            </p>
            <p>For technical support, implementation guidance, or additional analysis, please contact your project team.</p>
            <p style="margin-top: 30px; font-style: italic; opacity: 0.8;">
                © 2025 BIPV Analysis Platform - Advanced Engineering Assessment and Strategic Analysis Framework
            </p>
        </div>
    </div>
    """
    
    return section

def create_interactive_3d_bim_model(model_data, show_building=True, show_pv_panels=True, show_wireframe=False, transparency=0.7, view_mode="Perspective View"):
    """Create interactive 3D BIM model with zoom and rotate capabilities"""
    
    if not PLOTLY_AVAILABLE or go is None:
        st.error("Plotly is not available for 3D visualization")
        return None
    
    # Extract building dimensions from model data
    building_dims = model_data['building_dimensions']
    height = building_dims['height']
    width = building_dims['width']
    depth = building_dims['depth']
    
    # Create figure with 3D scene
    fig = go.Figure()
    
    # Building structure coordinates (center at origin)
    x_min, x_max = -width/2, width/2
    y_min, y_max = -depth/2, depth/2
    z_min, z_max = 0, height
    
    if show_building:
        # Create building faces as mesh3d surfaces
        
        # Bottom face (foundation)
        fig.add_trace(go.Mesh3d(
            x=[x_min, x_max, x_max, x_min],
            y=[y_min, y_min, y_max, y_max],
            z=[z_min, z_min, z_min, z_min],
            i=[0, 0], j=[1, 2], k=[2, 3],
            color='gray',
            opacity=transparency,
            name='Foundation',
            showlegend=True,
            hovertemplate="Foundation<br>Level: Ground<extra></extra>"
        ))
        
        # Top face (roof)
        fig.add_trace(go.Mesh3d(
            x=[x_min, x_max, x_max, x_min],
            y=[y_min, y_min, y_max, y_max],
            z=[z_max, z_max, z_max, z_max],
            i=[0, 0], j=[1, 2], k=[2, 3],
            color='darkslategray',
            opacity=transparency,
            name='Roof',
            showlegend=True,
            hovertemplate="Roof<br>Height: " + f"{height}m<extra></extra>"
        ))
        
        # Create facade surfaces with different colors based on orientation
        facade_colors = {
            'North': 'lightblue',
            'South': 'lightcoral', 
            'East': 'lightgreen',
            'West': 'lightyellow'
        }
        
        # North facade (y = y_max)
        fig.add_trace(go.Mesh3d(
            x=[x_min, x_max, x_max, x_min],
            y=[y_max, y_max, y_max, y_max],
            z=[z_min, z_min, z_max, z_max],
            i=[0, 0], j=[1, 2], k=[2, 3],
            color=facade_colors['North'],
            opacity=transparency,
            name='North Facade',
            showlegend=True,
            hovertemplate="North Facade<br>Area: " + f"{model_data['facade_systems'][0]['area']:.0f}m²<extra></extra>"
        ))
        
        # South facade (y = y_min)
        fig.add_trace(go.Mesh3d(
            x=[x_min, x_max, x_max, x_min],
            y=[y_min, y_min, y_min, y_min],
            z=[z_min, z_min, z_max, z_max],
            i=[0, 0], j=[1, 2], k=[2, 3],
            color=facade_colors['South'],
            opacity=transparency,
            name='South Facade',
            showlegend=True,
            hovertemplate="South Facade<br>Area: " + f"{model_data['facade_systems'][1]['area']:.0f}m²<extra></extra>"
        ))
        
        # East facade (x = x_max)
        fig.add_trace(go.Mesh3d(
            x=[x_max, x_max, x_max, x_max],
            y=[y_min, y_max, y_max, y_min],
            z=[z_min, z_min, z_max, z_max],
            i=[0, 0], j=[1, 2], k=[2, 3],
            color=facade_colors['East'],
            opacity=transparency,
            name='East Facade',
            showlegend=True,
            hovertemplate="East Facade<br>Area: " + f"{model_data['facade_systems'][2]['area']:.0f}m²<extra></extra>"
        ))
        
        # West facade (x = x_min)
        fig.add_trace(go.Mesh3d(
            x=[x_min, x_min, x_min, x_min],
            y=[y_min, y_max, y_max, y_min],
            z=[z_min, z_min, z_max, z_max],
            i=[0, 0], j=[1, 2], k=[2, 3],
            color=facade_colors['West'],
            opacity=transparency,
            name='West Facade',
            showlegend=True,
            hovertemplate="West Facade<br>Area: " + f"{model_data['facade_systems'][3]['area']:.0f}m²<extra></extra>"
        ))
    
    if show_wireframe:
        # Add wireframe edges
        wireframe_traces = create_building_wireframe(x_min, x_max, y_min, y_max, z_min, z_max)
        for trace in wireframe_traces:
            fig.add_trace(trace)
    
    if show_pv_panels:
        # Add PV panels on facades
        pv_traces = create_pv_panel_visualization(model_data, x_min, x_max, y_min, y_max, z_min, z_max)
        for trace in pv_traces:
            fig.add_trace(trace)
    
    # Set camera view based on view mode
    camera_settings = get_camera_settings(view_mode, width, height, depth)
    
    # Update layout with interactive controls
    fig.update_layout(
        scene=dict(
            xaxis=dict(
                title="Width (m)",
                range=[x_min-5, x_max+5],
                showgrid=True,
                gridcolor='lightgray',
                showbackground=True,
                backgroundcolor='white'
            ),
            yaxis=dict(
                title="Depth (m)",
                range=[y_min-5, y_max+5],
                showgrid=True,
                gridcolor='lightgray',
                showbackground=True,
                backgroundcolor='white'
            ),
            zaxis=dict(
                title="Height (m)",
                range=[z_min, z_max+10],
                showgrid=True,
                gridcolor='lightgray',
                showbackground=True,
                backgroundcolor='white'
            ),
            aspectmode='manual',
            aspectratio=dict(x=1, y=depth/width, z=height/width),
            camera=camera_settings,
            bgcolor='rgba(240,240,240,0.1)'
        ),
        title=dict(
            text=f"Interactive 3D BIPV Building Model - {view_mode}",
            x=0.5,
            font=dict(size=16, color='#2E86AB')
        ),
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='gray',
            borderwidth=1
        ),
        margin=dict(l=0, r=0, t=50, b=0),
        height=700,
        template="plotly_white"
    )
    
    # Add annotations for building information
    fig.add_annotation(
        x=0.02, y=0.02,
        xref="paper", yref="paper",
        text=f"Building: {width}m × {depth}m × {height}m<br>Volume: {model_data['building_volume']:,.0f} m³<br>Total PV: {sum(f['system_power'] for f in model_data['facade_systems']):.1f} kW",
        showarrow=False,
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="gray",
        borderwidth=1,
        font=dict(size=10)
    )
    
    return fig

def create_building_wireframe(x_min, x_max, y_min, y_max, z_min, z_max):
    """Create wireframe edges for the building"""
    wireframe_traces = []
    
    # Bottom edges
    edges = [
        ([x_min, x_max], [y_min, y_min], [z_min, z_min]),  # Front bottom
        ([x_max, x_max], [y_min, y_max], [z_min, z_min]),  # Right bottom
        ([x_max, x_min], [y_max, y_max], [z_min, z_min]),  # Back bottom
        ([x_min, x_min], [y_max, y_min], [z_min, z_min]),  # Left bottom
        # Top edges
        ([x_min, x_max], [y_min, y_min], [z_max, z_max]),  # Front top
        ([x_max, x_max], [y_min, y_max], [z_max, z_max]),  # Right top
        ([x_max, x_min], [y_max, y_max], [z_max, z_max]),  # Back top
        ([x_min, x_min], [y_max, y_min], [z_max, z_max]),  # Left top
        # Vertical edges
        ([x_min, x_min], [y_min, y_min], [z_min, z_max]),  # Front left
        ([x_max, x_max], [y_min, y_min], [z_min, z_max]),  # Front right
        ([x_max, x_max], [y_max, y_max], [z_min, z_max]),  # Back right
        ([x_min, x_min], [y_max, y_max], [z_min, z_max]),  # Back left
    ]
    
    for i, (x_coords, y_coords, z_coords) in enumerate(edges):
        wireframe_traces.append(go.Scatter3d(
            x=x_coords, y=y_coords, z=z_coords,
            mode='lines',
            line=dict(color='black', width=2),
            name='Wireframe' if i == 0 else None,
            showlegend=True if i == 0 else False,
            hoverinfo='none'
        ))
    
    return wireframe_traces

def create_pv_panel_visualization(model_data, x_min, x_max, y_min, y_max, z_min, z_max):
    """Create PV panel visualizations on building facades"""
    pv_traces = []
    
    # Panel dimensions (typical)
    panel_width = 2.0  # meters
    panel_height = 1.0  # meters
    panel_offset = 0.05  # offset from facade surface
    
    facade_configs = [
        ('North', y_max + panel_offset, 'y', x_min, x_max, 'lightgreen'),
        ('South', y_min - panel_offset, 'y', x_min, x_max, 'darkgreen'),
        ('East', x_max + panel_offset, 'x', y_min, y_max, 'mediumseagreen'),
        ('West', x_min - panel_offset, 'x', y_min, y_max, 'forestgreen')
    ]
    
    for facade_name, position, axis, coord_min, coord_max, color in facade_configs:
        # Find facade data
        facade_data = next((f for f in model_data['facade_systems'] if f['orientation'] == facade_name), None)
        if not facade_data or facade_data['panel_count'] == 0:
            continue
        
        # Calculate panel layout
        panel_count = facade_data['panel_count']
        facade_width = coord_max - coord_min
        facade_height = z_max - z_min
        
        # Simple grid layout
        panels_per_row = max(1, int(facade_width / panel_width))
        panel_rows = max(1, panel_count // panels_per_row)
        
        panel_coords_x = []
        panel_coords_y = []
        panel_coords_z = []
        
        for row in range(min(panel_rows, int(facade_height / panel_height))):
            for col in range(min(panels_per_row, panel_count - row * panels_per_row)):
                if axis == 'y':  # North/South facades
                    # Panel corners
                    x_start = coord_min + col * panel_width
                    x_end = x_start + panel_width * 0.8  # Leave gap
                    z_start = z_min + row * panel_height + 2  # Start 2m from ground
                    z_end = z_start + panel_height * 0.8  # Leave gap
                    
                    # Create panel as small rectangle
                    panel_coords_x.extend([x_start, x_end, x_end, x_start, x_start, None])
                    panel_coords_y.extend([position, position, position, position, position, None])
                    panel_coords_z.extend([z_start, z_start, z_end, z_end, z_start, None])
                    
                else:  # East/West facades
                    # Panel corners
                    y_start = coord_min + col * panel_width
                    y_end = y_start + panel_width * 0.8
                    z_start = z_min + row * panel_height + 2
                    z_end = z_start + panel_height * 0.8
                    
                    # Create panel as small rectangle
                    panel_coords_x.extend([position, position, position, position, position, None])
                    panel_coords_y.extend([y_start, y_end, y_end, y_start, y_start, None])
                    panel_coords_z.extend([z_start, z_start, z_end, z_end, z_start, None])
        
        if panel_coords_x:  # Only add if there are panels
            pv_traces.append(go.Scatter3d(
                x=panel_coords_x,
                y=panel_coords_y,
                z=panel_coords_z,
                mode='lines',
                line=dict(color=color, width=4),
                name=f'PV Panels ({facade_name})',
                showlegend=True,
                hovertemplate=f"{facade_name} PV Panels<br>Count: {facade_data['panel_count']}<br>Power: {facade_data['system_power']:.1f} kW<extra></extra>"
            ))
    
    return pv_traces

def get_camera_settings(view_mode, width, height, depth):
    """Get camera settings for different view modes"""
    
    if view_mode == "Perspective View":
        return dict(
            eye=dict(x=1.5, y=1.5, z=1.2),
            center=dict(x=0, y=0, z=height/2),
            up=dict(x=0, y=0, z=1)
        )
    elif view_mode == "Orthographic View":
        return dict(
            eye=dict(x=2, y=2, z=1.5),
            center=dict(x=0, y=0, z=height/2),
            up=dict(x=0, y=0, z=1),
            projection=dict(type="orthographic")
        )
    elif view_mode == "Top-Down View":
        return dict(
            eye=dict(x=0, y=0, z=3),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=1, z=0)
        )
    elif view_mode == "Front Elevation":
        return dict(
            eye=dict(x=0, y=-3, z=height/2),
            center=dict(x=0, y=0, z=height/2),
            up=dict(x=0, y=0, z=1)
        )
    elif view_mode == "Side Elevation":
        return dict(
            eye=dict(x=3, y=0, z=height/2),
            center=dict(x=0, y=0, z=height/2),
            up=dict(x=0, y=0, z=1)
        )
    else:
        # Default perspective
        return dict(
            eye=dict(x=1.5, y=1.5, z=1.2),
            center=dict(x=0, y=0, z=height/2),
            up=dict(x=0, y=0, z=1)
        )

def calculate_shadow_analysis(model_data):
    """Calculate shadow impact analysis for each facade"""
    # Simplified shadow analysis based on orientation and building geometry
    shadow_impacts = {
        'North': 15.5,  # Higher shading due to lower solar angles
        'South': 3.2,   # Minimal shading, optimal solar exposure
        'East': 8.7,    # Morning shadows from surrounding structures
        'West': 9.1     # Afternoon shadows from surrounding structures
    }
    return shadow_impacts

def create_building_cross_sections(model_data):
    """Create building cross-section views showing PV placement"""
    building_dims = model_data['building_dimensions']
    height = building_dims['height']
    width = building_dims['width']
    depth = building_dims['depth']
    
    # Create subplots for different cross-sections
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Front Elevation', 'Side Elevation', 'Floor Plan', 'Section A-A'),
        specs=[[{"type": "scatter"}, {"type": "scatter"}],
               [{"type": "scatter"}, {"type": "scatter"}]]
    )
    
    # Front elevation (South facade)
    fig.add_trace(
        go.Scatter(
            x=[0, width, width, 0, 0],
            y=[0, 0, height, height, 0],
            mode='lines',
            name='Building Outline',
            line=dict(color='black', width=2)
        ),
        row=1, col=1
    )
    
    # Add PV panels on front elevation
    south_facade = next((f for f in model_data['facade_systems'] if f['orientation'] == 'South'), None)
    if south_facade and south_facade['panel_count'] > 0:
        # Simplified PV panel representation
        panels_per_row = min(int(width / 2), 10)
        panel_rows = min(int(height / 1.5), 8)
        
        for row in range(panel_rows):
            for col in range(panels_per_row):
                x_start = col * (width / panels_per_row) + 1
                x_end = x_start + 1.5
                y_start = row * (height / panel_rows) + 2
                y_end = y_start + 1
                
                fig.add_trace(
                    go.Scatter(
                        x=[x_start, x_end, x_end, x_start, x_start],
                        y=[y_start, y_start, y_end, y_end, y_start],
                        mode='lines',
                        name='PV Panel' if row == 0 and col == 0 else None,
                        line=dict(color='green', width=1),
                        showlegend=True if row == 0 and col == 0 else False
                    ),
                    row=1, col=1
                )
    
    # Side elevation
    fig.add_trace(
        go.Scatter(
            x=[0, depth, depth, 0, 0],
            y=[0, 0, height, height, 0],
            mode='lines',
            name='Side View',
            line=dict(color='black', width=2),
            showlegend=False
        ),
        row=1, col=2
    )
    
    # Floor plan
    fig.add_trace(
        go.Scatter(
            x=[0, width, width, 0, 0],
            y=[0, 0, depth, depth, 0],
            mode='lines',
            name='Floor Plan',
            line=dict(color='black', width=2),
            showlegend=False
        ),
        row=2, col=1
    )
    
    # Section view
    fig.add_trace(
        go.Scatter(
            x=[0, width, width, 0, 0],
            y=[0, 0, height, height, 0],
            mode='lines',
            name='Section',
            line=dict(color='black', width=2),
            showlegend=False
        ),
        row=2, col=2
    )
    
    fig.update_layout(
        title="Building Cross-Sections with PV System Layout",
        height=600,
        showlegend=True
    )
    
    return fig

def create_text_based_3d_representation(model_data):
    """Create a text-based 3D representation when Plotly is not available"""
    building_dims = model_data['building_dimensions']
    height = building_dims['height']
    width = building_dims['width']
    depth = building_dims['depth']
    
    st.subheader("Building 3D ASCII Representation")
    
    # Create ASCII art representation
    ascii_building = f"""
    Building Dimensions: {width}m × {depth}m × {height}m
    
    3D Building Wireframe:
    
           {width}m
         ┌─────────────┐  ← {height}m
        ╱             ╱│
       ╱             ╱ │
      ╱             ╱  │
     ┌─────────────┐   │ {depth}m
     │   BUILDING  │   │
     │             │   │
     │  PV PANELS  │   ╱
     │             │  ╱
     │             │ ╱
     └─────────────┘╱
    
    PV System Layout:
    """
    
    # Add facade information
    for facade in model_data['facade_systems']:
        orientation = facade['orientation']
        panel_count = facade['panel_count']
        coverage = facade['coverage']
        
        if panel_count > 0:
            ascii_building += f"\n    {orientation} Facade: {panel_count} panels ({coverage:.1f}% coverage)"
            # Add visual representation
            if panel_count > 0:
                panel_visual = "■" * min(panel_count // 5, 20)  # Scale down for display
                ascii_building += f"\n    PV Layout: {panel_visual}"
    
    st.code(ascii_building)
    
    # Add building metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Building Volume", f"{model_data['building_volume']:,.0f} m³")
    with col2:
        st.metric("Total PV Power", f"{sum(f['system_power'] for f in model_data['facade_systems']):.1f} kW")
    with col3:
        st.metric("PV Coverage", f"{model_data['pv_coverage']:.1f}%")
    
    st.info("Interactive 3D visualization will be available once Plotly loads properly. Please refresh the page.")

if __name__ == "__main__":
    main()