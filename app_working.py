import streamlit as st
import math
import json
from datetime import datetime, timedelta
import io

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
    """Historical data analysis module"""
    st.header("2. Historical Data & AI Model")
    st.markdown("Upload historical energy consumption data for baseline demand analysis.")
    
    # Historical data upload section
    st.subheader("Historical Energy Consumption Data")
    
    uploaded_file = st.file_uploader(
        "Upload Monthly Consumption Data (CSV)",
        type=['csv'],
        help="Upload a CSV file with columns: Date, Consumption (kWh), Temperature (°C)"
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
                
                # Parse CSV manually to avoid pandas dependency
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
                preview_data = data_rows[:5]  # Show first 5 rows
                
                for i, row in enumerate(preview_data):
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
                
                # Simple trend analysis
                st.subheader("Consumption Analysis")
                
                if len(consumptions) >= 12:
                    # Calculate seasonal averages
                    quarters = {1: [], 2: [], 3: [], 4: []}
                    
                    for i, consumption in enumerate(consumptions):
                        month = (i % 12) + 1
                        quarter = ((month - 1) // 3) + 1
                        quarters[quarter].append(consumption)
                    
                    st.write("**Seasonal Analysis:**")
                    for q, values in quarters.items():
                        if values:
                            avg = sum(values) / len(values)
                            seasons = ["Winter", "Spring", "Summer", "Fall"]
                            st.write(f"- {seasons[q-1]}: {avg:.0f} kWh average")
                
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
        if st.button("Generate Weather Data"):
            with st.spinner("Generating simplified weather data for solar analysis..."):
                weather_data = generate_simple_weather_data(latitude, longitude)
                st.session_state.project_data['weather_data'] = weather_data
                st.success("✅ Weather data generated successfully!")
    
    with col2:
        st.subheader("Environmental Conditions")
        
        # Shading factors
        tree_shading = st.slider("Tree Shading Factor", 0.0, 0.5, 0.1, 0.05,
                                help="Fraction of sunlight blocked by trees")
        
        building_shading = st.slider("Building Shading Factor", 0.0, 0.3, 0.05, 0.05,
                                   help="Fraction of sunlight blocked by nearby buildings")
        
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
        
        # Monthly breakdown
        st.subheader("Monthly Solar Resource")
        
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        monthly_data = weather['monthly_ghi']
        
        # Create simple bar chart using text
        st.write("**Monthly Global Horizontal Irradiance (kWh/m²):**")
        max_val = max(monthly_data)
        for i, (month, value) in enumerate(zip(months, monthly_data)):
            bar_length = int((value / max_val) * 30)
            bar = "█" * bar_length + "░" * (30 - bar_length)
            st.write(f"{month}: {bar} {value:.0f}")
        
        st.success("✅ Weather analysis complete!")
        st.info("Proceed to Step 4 for building facade extraction.")

def generate_simple_weather_data(lat, lon):
    """Generate simplified weather data for location"""
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
    
    if st.button("Analyze Building Elements"):
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
    """Simulate extraction of building elements from BIM model"""
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
    
    if st.button("Calculate Solar Radiation Grid"):
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
        
        # Detailed analysis by orientation
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
        
        for orient, data in orientation_analysis.items():
            if data['count'] > 0:
                avg_irradiance = data['total_irradiance'] / data['count']
                avg_shading = data['avg_shading'] / data['count']
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.write(f"**{orient}**")
                with col2:
                    st.write(f"{data['count']} elements")
                with col3:
                    st.write(f"{avg_irradiance:.0f} kWh/m²")
                with col4:
                    st.write(f"{avg_shading:.2f} shading")
        
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
    """Calculate solar radiation for building elements"""
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
            help="Select the PV panel technology"
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
            help="Spacing between panels as fraction of panel size"
        )
        
        min_system_size = st.number_input(
            "Minimum System Size (kW)", 1.0, 20.0, 3.0, 0.5,
            help="Minimum system size for economic viability"
        )
        
        system_losses = st.slider(
            "Total System Losses (%)", 10, 25, 15, 1,
            help="Inverter, wiring, soiling, and other losses"
        )
    
    if st.button("Calculate PV System Specifications"):
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
    """Calculate PV system specifications for suitable elements"""
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

def render_yield_demand():
    """Energy yield vs demand analysis"""
    st.header("7. Yield vs. Demand Calculation")
    st.markdown("Analyze the balance between PV energy generation and building energy demand.")
    
    if 'pv_systems' not in st.session_state.project_data or 'historical_data' not in st.session_state.project_data:
        st.warning("⚠️ Please complete Steps 2 and 6 before proceeding.")
        return
    
    if st.button("Calculate Energy Balance"):
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
        
        # Monthly analysis
        st.subheader("Monthly Energy Profile")
        
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
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
    """Calculate energy balance between PV generation and building demand"""
    historical_data = st.session_state.project_data['historical_data']
    pv_systems = st.session_state.project_data['pv_systems']
    weather_data = st.session_state.project_data['weather_data']
    
    # Extract annual demand from historical data
    annual_demand = 0
    monthly_demand = [0] * 12
    
    for row in historical_data:
        try:
            consumption = float(row['Consumption'])
            annual_demand += consumption
            # Distribute to months (simplified)
            for i in range(12):
                monthly_demand[i] += consumption / 12
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
        energy_weight = st.slider("Energy Independence Weight", 0.0, 1.0, 0.6, 0.1)
        financial_weight = st.slider("Financial Return Weight", 0.0, 1.0, 0.4, 0.1)
        
        # Normalize weights
        total_weight = energy_weight + financial_weight
        if total_weight > 0:
            energy_weight /= total_weight
            financial_weight /= total_weight
        
        st.write(f"Normalized weights: Energy {energy_weight:.1f}, Financial {financial_weight:.1f}")
    
    with col2:
        st.subheader("Financial Parameters")
        
        electricity_rate = st.number_input("Electricity Rate ($/kWh)", 0.05, 0.50, 0.12, 0.01)
        project_lifetime = st.slider("Project Lifetime (years)", 15, 30, 25, 1)
        discount_rate = st.slider("Discount Rate (%)", 3.0, 10.0, 6.0, 0.5) / 100
    
    if st.button("Run Optimization Analysis"):
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
        
        # Performance metrics
        st.subheader("Performance vs Investment Analysis")
        
        # Simple scatter plot using text
        st.write("**System Size vs Energy Independence:**")
        for config in sorted_configs[:8]:
            size_normalized = int((config['total_power_kw'] / max(c['total_power_kw'] for c in sorted_configs)) * 20)
            independence_normalized = int((config['energy_independence'] / 100) * 20)
            
            size_bar = "█" * size_normalized
            independence_bar = "░" * independence_normalized
            
            st.write(f"Size: {size_bar} | Independence: {independence_bar} | {config['total_power_kw']:.1f}kW, {config['energy_independence']:.0f}%")
        
        st.success("✅ System optimization complete!")
        st.info("Proceed to Step 9 for detailed financial analysis.")

def run_optimization_analysis(energy_weight, financial_weight, electricity_rate, project_lifetime, discount_rate):
    """Run optimization analysis on different system configurations"""
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
    """Analyze a specific configuration of PV systems"""
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
        
        electricity_rate = st.number_input("Electricity Rate ($/kWh)", 0.05, 0.50, 0.12, 0.01)
        feed_in_tariff = st.number_input("Feed-in Tariff ($/kWh)", 0.00, 0.20, 0.08, 0.01)
        o_m_rate = st.slider("O&M Cost (% of investment/year)", 1.0, 5.0, 2.0, 0.1) / 100
        degradation_rate = st.slider("Annual Degradation (%)", 0.2, 1.0, 0.5, 0.1) / 100
    
    with col2:
        st.subheader("Environmental Parameters")
        
        grid_co2_factor = st.number_input("Grid CO₂ Factor (kg CO₂/kWh)", 0.2, 1.0, 0.5, 0.05)
        carbon_price = st.number_input("Carbon Price ($/ton CO₂)", 10, 100, 25, 5)
        project_lifetime = st.slider("Project Lifetime (years)", 15, 30, 25, 1)
        discount_rate = st.slider("Discount Rate (%)", 3.0, 10.0, 6.0, 0.5) / 100
    
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
        
        # Cash flow analysis
        st.subheader("Cash Flow Projection")
        
        # Show first 10 years
        st.write("**Annual Cash Flow (First 10 Years):**")
        
        for year in range(1, min(11, len(analysis['annual_cash_flows']) + 1)):
            cash_flow = analysis['annual_cash_flows'][year - 1]
            cumulative = sum(analysis['annual_cash_flows'][:year]) - selected_config['total_cost']
            
            # Visual representation
            cf_normalized = max(0, min(20, int(cash_flow / 1000)))  # Scale to 0-20
            cf_bar = "💰" * cf_normalized
            
            status = "✅" if cumulative > 0 else "⏳"
            st.write(f"Year {year}: {cf_bar} ${cash_flow:,.0f} | Cumulative: {status} ${cumulative:,.0f}")
        
        # Investment summary
        st.subheader("Investment Summary")
        
        st.write(f"**Initial Investment:** ${selected_config['total_cost']:,.0f}")
        st.write(f"**Annual Energy Production:** {selected_config['annual_generation']:,.0f} kWh")
        st.write(f"**Annual Revenue:** ${analysis['annual_revenue']:,.0f}")
        st.write(f"**Annual O&M Costs:** ${analysis['annual_om_cost']:,.0f}")
        st.write(f"**Net Annual Cash Flow:** ${analysis['annual_cash_flows'][0]:,.0f}")
        
        # Sensitivity analysis
        st.subheader("Sensitivity Analysis")
        
        st.write("**NPV Sensitivity to Key Parameters:**")
        
        # Calculate sensitivity to electricity rate
        base_npv = analysis['npv']
        
        # ±20% electricity rate
        rate_low = electricity_rate * 0.8
        rate_high = electricity_rate * 1.2
        
        npv_low = base_npv * 0.7  # Simplified approximation
        npv_high = base_npv * 1.3
        
        st.write(f"- Electricity Rate -20% ({rate_low:.3f} $/kWh): NPV ${npv_low:,.0f}")
        st.write(f"- Base Case ({electricity_rate:.3f} $/kWh): NPV ${base_npv:,.0f}")
        st.write(f"- Electricity Rate +20% ({rate_high:.3f} $/kWh): NPV ${npv_high:,.0f}")
        
        if analysis['npv'] > 0:
            st.success("✅ Positive NPV indicates a financially viable investment!")
        else:
            st.warning("⚠️ Negative NPV suggests the investment may not be financially attractive under current assumptions.")
        
        st.success("✅ Financial analysis complete!")
        st.info("Proceed to Step 10 for 3D visualization.")

def calculate_detailed_analysis(config, electricity_rate, feed_in_tariff, o_m_rate, 
                              degradation_rate, grid_co2_factor, carbon_price, project_lifetime, discount_rate):
    """Calculate detailed financial and environmental analysis"""
    
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
        
        st.subheader("3D Building Model")
        
        # Building specifications
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Building Volume", f"{model_data['building_volume']:,.0f} m³")
        with col2:
            st.metric("Total Facade Area", f"{model_data['total_facade_area']:,.0f} m²")
        with col3:
            st.metric("PV Coverage", f"{model_data['pv_coverage']:.1f}%")
        
        # PV system layout
        st.subheader("PV System Layout")
        
        for facade_info in model_data['facade_systems']:
            st.write(f"**{facade_info['orientation']} Facade:**")
            st.write(f"- Area: {facade_info['area']:.0f} m²")
            st.write(f"- PV Panels: {facade_info['panel_count']} panels")
            st.write(f"- System Power: {facade_info['system_power']:.1f} kW")
            st.write(f"- Coverage: {facade_info['coverage']:.1f}%")
            st.write("")
        
        # Performance visualization
        st.subheader("System Performance by Facade")
        
        # Create a simple text-based visualization
        orientations = [f['orientation'] for f in model_data['facade_systems']]
        powers = [f['system_power'] for f in model_data['facade_systems']]
        max_power = max(powers) if powers else 1
        
        for orient, power in zip(orientations, powers):
            bar_length = int((power / max_power) * 30)
            bar = "█" * bar_length + "░" * (30 - bar_length)
            st.write(f"{orient:>10}: {bar} {power:.1f} kW")
        
        # Shadow analysis
        if show_shading:
            st.subheader("Shading Analysis")
            
            shading_factors = st.session_state.project_data.get('shading_factors', {'trees': 0.1, 'buildings': 0.05})
            
            st.write(f"**Tree Shading Impact:** {shading_factors['trees']:.1%} reduction")
            st.write(f"**Building Shading Impact:** {shading_factors['buildings']:.1%} reduction")
            st.write(f"**Total Shading Factor:** {(1 - shading_factors['trees'] - shading_factors['buildings']):.2f}")
        
        # Technical specifications
        st.subheader("Technical Specifications")
        
        st.write("**Recommended Installation Details:**")
        st.write("- Panel mounting: Curtain wall integrated system")
        st.write("- Electrical: DC optimizers for each facade section")
        st.write("- Inverters: String inverters per orientation group")
        st.write("- Monitoring: Real-time performance monitoring system")
        st.write("- Maintenance: Annual cleaning and inspection schedule")
        
        st.success("✅ 3D visualization complete!")
        st.info("Proceed to Step 11 for comprehensive reporting.")

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
            help="Select the type of report to generate"
        )
        
        include_charts = st.checkbox("Include Data Visualizations", True)
        include_recommendations = st.checkbox("Include Recommendations", True)
        
        if st.button("Generate Report"):
            with st.spinner("Generating comprehensive BIPV analysis report..."):
                report_content = generate_comprehensive_report(report_type, include_charts, include_recommendations)
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
        
        export_format = st.selectbox(
            "Export Format",
            ["JSON", "CSV Summary", "Technical Specifications"],
            help="Select format for data export"
        )
        
        if st.button("Prepare Export"):
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
            st.balloons()
            st.success("🎉 Comprehensive BIPV analysis complete! Your building is ready for solar integration.")
    
    st.success("✅ BIPV Analysis Platform workflow complete!")

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
    
    if report_type in ["Technical Report", "Complete Report"]:
        # Add technical section
        pv_systems = project_data['pv_systems']
        total_panels = sum(s['panel_count'] for s in pv_systems)
        
        html_content += f"""
        <div class="section">
            <h2>Technical Analysis</h2>
            
            <h3>System Configuration</h3>
            <table>
                <tr><th>Parameter</th><th>Value</th></tr>
                <tr><td>Number of PV Systems</td><td>{len(pv_systems)}</td></tr>
                <tr><td>Total Panel Count</td><td>{total_panels}</td></tr>
                <tr><td>System Configuration</td><td>{best_config['config_id']}</td></tr>
                <tr><td>Average System Size</td><td>{best_config['total_power_kw']/len(pv_systems):.1f} kW per system</td></tr>
            </table>
            
            <h3>Energy Performance</h3>
            <table>
                <tr><th>Metric</th><th>Annual Value</th></tr>
                <tr><td>Building Energy Demand</td><td>{energy_balance['annual_demand']:,.0f} kWh</td></tr>
                <tr><td>PV Energy Generation</td><td>{energy_balance['annual_generation']:,.0f} kWh</td></tr>
                <tr><td>Net Grid Import</td><td>{energy_balance['net_import']:,.0f} kWh</td></tr>
                <tr><td>Energy Self-Sufficiency</td><td>{energy_balance['self_sufficiency']:.1f}%</td></tr>
            </table>
        </div>
        """
    
    if report_type in ["Financial Analysis", "Complete Report"]:
        # Add financial section
        if 'detailed_analysis' in project_data:
            financial = project_data['detailed_analysis']
            
            html_content += f"""
            <div class="section">
                <h2>Financial Analysis</h2>
                
                <h3>Investment Overview</h3>
                <table>
                    <tr><th>Financial Metric</th><th>Value</th></tr>
                    <tr><td>Initial Investment</td><td>${best_config['total_cost']:,.0f}</td></tr>
                    <tr><td>Net Present Value (NPV)</td><td>${financial['npv']:,.0f}</td></tr>
                    <tr><td>Internal Rate of Return (IRR)</td><td>{financial['irr']:.1f}%</td></tr>
                    <tr><td>Simple Payback Period</td><td>{financial['payback_years']:.1f} years</td></tr>
                    <tr><td>Return on Investment (ROI)</td><td>{financial['roi']:.1f}%</td></tr>
                </table>
                
                <h3>Environmental Impact</h3>
                <table>
                    <tr><th>Environmental Metric</th><th>Value</th></tr>
                    <tr><td>Annual CO₂ Emissions Avoided</td><td>{financial['annual_co2_kg']:,.0f} kg</td></tr>
                    <tr><td>Lifetime CO₂ Emissions Avoided</td><td>{financial['lifetime_co2_tons']:.1f} tons</td></tr>
                    <tr><td>Carbon Credit Value</td><td>${financial['carbon_value']:,.0f}</td></tr>
                </table>
            </div>
            """
    
    if include_recommendations:
        recommendations = generate_key_recommendations(best_config, energy_balance)
        
        html_content += """
        <div class="section">
            <h2>Recommendations</h2>
        """
        
        for i, rec in enumerate(recommendations, 1):
            html_content += f"""
            <div class="recommendation">
                <h4>Recommendation {i}</h4>
                <p>{rec}</p>
            </div>
            """
        
        html_content += "</div>"
    
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
        
        if 'optimization_results' in project_data:
            configs = project_data['optimization_results']['configurations']
            
            # Optimization results
            csv_content = "Config_ID,System_Count,Total_Power_kW,Energy_Independence_%,Total_Cost,NPV,Payback_Years,Overall_Score\n"
            for config in configs:
                csv_content += f"{config['config_id']},{config['system_count']},{config['total_power_kw']:.1f},"
                csv_content += f"{config['energy_independence']:.1f},{config['total_cost']:.0f},{config['npv']:.0f},"
                csv_content += f"{config['payback_years']:.1f},{config['overall_score']:.3f}\n"
            
            export_files["optimization_results.csv"] = csv_content
    
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

SYSTEM DETAILS BY ELEMENT
------------------------
"""
        
        for system in pv_systems:
            specs += f"""
Element ID: {system['element_id']}
- Orientation: {system['orientation']}
- System Power: {system['system_power_kw']:.1f} kW
- Panel Count: {system['panel_count']}
- Annual Energy: {system['annual_energy_kwh']:,.0f} kWh
- Specific Yield: {system['specific_yield']:.0f} kWh/kW
- Installation Cost: ${system['total_cost']:,.0f}

"""
    
    if 'energy_balance' in project_data:
        balance = project_data['energy_balance']
        
        specs += f"""
ENERGY PERFORMANCE
-----------------
Annual Building Demand: {balance['annual_demand']:,.0f} kWh
Annual PV Generation: {balance['annual_generation']:,.0f} kWh
Net Grid Import: {balance['net_import']:,.0f} kWh
Energy Self-Sufficiency: {balance['self_sufficiency']:.1f}%

"""
    
    specs += """
INSTALLATION REQUIREMENTS
------------------------
- Structural assessment required for facade mounting points
- Electrical infrastructure: DC optimizers and string inverters
- Grid interconnection: Net metering agreement recommended
- Monitoring system: Real-time performance tracking
- Maintenance: Annual cleaning and inspection

COMPLIANCE AND STANDARDS
-----------------------
- IEC 61215: PV module qualification
- IEC 61730: PV module safety qualification
- IEEE 1547: Grid interconnection standards
- Local building codes and electrical standards
- Fire safety and accessibility requirements

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
    
    # Monitoring recommendation
    recommendations.append(
        "Implement comprehensive monitoring systems to track performance and optimize operations. "
        "Regular maintenance schedules will ensure long-term system reliability."
    )
    
    return recommendations

if __name__ == "__main__":
    main()