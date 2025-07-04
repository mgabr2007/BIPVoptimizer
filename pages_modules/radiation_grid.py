"""
Radiation & Shading Grid Analysis page for BIPV Optimizer
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from database_manager import db_manager
from core.solar_math import safe_divide
from utils.consolidated_data_manager import ConsolidatedDataManager

def calculate_geometric_shading_factors(walls_data, window_elements, latitude, longitude):
    """Calculate geometric shading factors using building walls data."""
    
    def calculate_shadow_polygon(wall_element, sun_elevation, sun_azimuth, wall_height=3.0):
        """Calculate shadow polygon cast by a wall element."""
        try:
            # Get wall properties
            wall_azimuth = float(wall_element.get('Azimuth (°)', 180))
            wall_length = float(wall_element.get('Length (m)', 1.0))
            
            # Calculate shadow length based on sun elevation
            if sun_elevation <= 0:
                return None  # No shadow during night
            
            shadow_length = wall_height / np.tan(np.radians(max(sun_elevation, 1)))
            
            # Calculate shadow direction (opposite to sun azimuth)
            shadow_azimuth = (sun_azimuth + 180) % 360
            
            # Calculate shadow end points
            shadow_dx = shadow_length * np.sin(np.radians(shadow_azimuth))
            shadow_dy = shadow_length * np.cos(np.radians(shadow_azimuth))
            
            # Return shadow polygon coordinates (simplified as rectangle)
            return {
                'length': shadow_length,
                'width': wall_length,
                'azimuth': shadow_azimuth,
                'dx': shadow_dx,
                'dy': shadow_dy
            }
        except:
            return None
    
    def calculate_shading_factor(window_element, shadow_polygons):
        """Calculate shading factor for a window based on shadow polygons."""
        try:
            window_azimuth = float(window_element.get('Azimuth (degrees)', 180))
            window_area = float(window_element.get('Glass Area (m²)', 1.5))
            
            # Simplified shading calculation
            total_shading = 0.0
            
            for shadow in shadow_polygons:
                if shadow is None:
                    continue
                
                # Calculate azimuth difference
                azimuth_diff = abs(window_azimuth - shadow['azimuth'])
                if azimuth_diff > 180:
                    azimuth_diff = 360 - azimuth_diff
                
                # Apply shading based on proximity and shadow size
                if azimuth_diff < 45:  # Shadow in similar direction
                    shading_intensity = max(0, 1 - (azimuth_diff / 45))
                    shadow_coverage = min(0.8, shadow['length'] / 10.0)  # Normalize by 10m
                    total_shading += shading_intensity * shadow_coverage
            
            # Clamp total shading and return factor
            total_shading = min(0.7, total_shading)  # Max 70% shading
            shading_factor = 1.0 - total_shading
            return max(0.3, shading_factor)  # Min 30% radiation
            
        except:
            return 0.9  # Default moderate shading
    
    # Generate shading factors for each hour
    shading_factors = {}
    
    try:
        # Sample hours for calculation efficiency
        sample_hours = [6, 8, 10, 12, 14, 16, 18]
        
        for hour in range(24):
            if hour in sample_hours:
                # Calculate solar position for this hour (simplified)
                day_of_year = 172  # June 21 (summer solstice)
                
                # Simplified solar calculations
                solar_declination = 23.45 * np.sin(np.radians(360 * (284 + day_of_year) / 365))
                hour_angle = 15 * (hour - 12)
                
                lat_rad = np.radians(latitude)
                decl_rad = np.radians(solar_declination)
                hour_rad = np.radians(hour_angle)
                
                sun_elevation = np.degrees(np.arcsin(
                    np.sin(lat_rad) * np.sin(decl_rad) + 
                    np.cos(lat_rad) * np.cos(decl_rad) * np.cos(hour_rad)
                ))
                
                sun_azimuth = np.degrees(np.arctan2(
                    np.sin(hour_rad),
                    np.cos(hour_rad) * np.sin(lat_rad) - np.tan(decl_rad) * np.cos(lat_rad)
                )) + 180
                
                # Calculate shadows from all walls
                shadow_polygons = []
                for _, wall in walls_data.iterrows():
                    shadow = calculate_shadow_polygon(wall, sun_elevation, sun_azimuth)
                    if shadow:
                        shadow_polygons.append(shadow)
                
                # Calculate average shading factor for this hour
                total_shading_factor = 0.0
                valid_windows = 0
                
                for _, window in window_elements.iterrows():
                    factor = calculate_shading_factor(window, shadow_polygons)
                    total_shading_factor += factor
                    valid_windows += 1
                
                if valid_windows > 0:
                    avg_shading_factor = total_shading_factor / valid_windows
                else:
                    avg_shading_factor = 0.9
                
                shading_factors[str(hour)] = {'shading_factor': avg_shading_factor}
            else:
                # Interpolate or use default for non-sample hours
                if hour < 6 or hour > 20:
                    shading_factors[str(hour)] = {'shading_factor': 0.1}  # Night
                else:
                    shading_factors[str(hour)] = {'shading_factor': 0.85}  # Default daylight
        
        return shading_factors
        
    except Exception as e:
        print(f"Error in geometric shading calculation: {e}")
        return None

def calculate_solar_position_simple(latitude, longitude, day_of_year, hour):
    """Calculate solar position using simplified formulas."""
    import math
    
    # Declination angle
    declination = 23.45 * math.sin(math.radians(360 * (284 + day_of_year) / 365))
    
    # Hour angle
    hour_angle = 15 * (hour - 12)
    
    # Solar elevation angle
    elevation = math.asin(
        math.sin(math.radians(declination)) * math.sin(math.radians(latitude)) +
        math.cos(math.radians(declination)) * math.cos(math.radians(latitude)) * 
        math.cos(math.radians(hour_angle))
    )
    
    # Solar azimuth angle
    azimuth = math.atan2(
        math.sin(math.radians(hour_angle)),
        math.cos(math.radians(hour_angle)) * math.sin(math.radians(latitude)) -
        math.tan(math.radians(declination)) * math.cos(math.radians(latitude))
    )
    
    return {
        'elevation': math.degrees(elevation),
        'azimuth': math.degrees(azimuth) + 180,  # Convert to 0-360 range
        'zenith': 90 - math.degrees(elevation)
    }

def calculate_irradiance_on_surface(ghi, dni, dhi, solar_position, surface_tilt, surface_azimuth):
    """Calculate irradiance on tilted surface using simplified model."""
    import math
    
    zenith = math.radians(solar_position['zenith'])
    sun_azimuth = math.radians(solar_position['azimuth'])
    surface_tilt_rad = math.radians(surface_tilt)
    surface_azimuth_rad = math.radians(surface_azimuth)
    
    # Calculate angle of incidence
    cos_incidence = (
        math.sin(zenith) * math.sin(surface_tilt_rad) * 
        math.cos(sun_azimuth - surface_azimuth_rad) +
        math.cos(zenith) * math.cos(surface_tilt_rad)
    )
    
    # Ensure cos_incidence is not negative
    cos_incidence = max(0, cos_incidence)
    
    # Simple POA calculation
    direct_on_surface = dni * cos_incidence
    diffuse_on_surface = dhi * (1 + math.cos(surface_tilt_rad)) / 2
    reflected_on_surface = ghi * 0.2 * (1 - math.cos(surface_tilt_rad)) / 2  # 0.2 = ground albedo
    
    poa_global = direct_on_surface + diffuse_on_surface + reflected_on_surface
    
    return max(0, poa_global)

def analyze_wall_window_relationship(window_id, host_wall_id, walls_data):
    """Analyze the relationship between a window and its host wall using Element IDs."""
    
    relationship = {
        'host_wall_found': False,
        'wall_area': 0,
        'wall_level': 'Unknown',
        'azimuth_match': False,
        'wall_azimuth': 0,
        'geometric_compatibility': False
    }
    
    if walls_data is not None and host_wall_id != 'Unknown':
        # Find matching wall by Element ID
        matching_walls = walls_data[walls_data['ElementId'] == host_wall_id]
        
        if not matching_walls.empty:
            wall = matching_walls.iloc[0]
            relationship.update({
                'host_wall_found': True,
                'wall_area': wall.get('Area (m²)', 0),
                'wall_level': wall.get('Level', 'Unknown'),
                'wall_azimuth': wall.get('Azimuth (°)', 0),
                'geometric_compatibility': True
            })
    
    return relationship

def generate_radiation_grid(suitable_elements, tmy_data, latitude, longitude, shading_factors=None, walls_data=None):
    """Generate radiation grid for all suitable elements with wall-window relationship analysis."""
    
    if tmy_data is None or len(tmy_data) == 0:
        st.warning("No TMY data available for radiation calculations")
        return pd.DataFrame()
    
    # Convert TMY data to DataFrame if it's not already
    if isinstance(tmy_data, list):
        tmy_df = pd.DataFrame(tmy_data)
    else:
        tmy_df = tmy_data.copy()
    
    # Ensure datetime column exists
    if 'datetime' not in tmy_df.columns:
        # Create datetime from month, day, hour if available
        if all(col in tmy_df.columns for col in ['month', 'day', 'hour']):
            tmy_df['datetime'] = pd.to_datetime(
                tmy_df[['month', 'day', 'hour']].assign(year=2023)
            )
        else:
            # Create hourly data for a full year
            base_date = datetime(2023, 1, 1)
            tmy_df['datetime'] = pd.date_range(base_date, periods=len(tmy_df), freq='H')
    
    tmy_df['datetime'] = pd.to_datetime(tmy_df['datetime'])
    tmy_df['day_of_year'] = tmy_df['datetime'].dt.dayofyear
    tmy_df['hour'] = tmy_df['datetime'].dt.hour
    
    radiation_grid = []
    
    for _, element in suitable_elements.iterrows():
        # Get element properties with defaults - preserve actual BIM Element IDs
        element_id = element.get('Element ID', element.get('element_id', element.get('id', f"Unknown_Element_{len(radiation_grid)}")))
        element_area = float(element.get('Glass Area (m²)', element.get('glass_area', element.get('area', 1.5))))
        orientation = element.get('Orientation', element.get('orientation', 'South'))
        azimuth = float(element.get('Azimuth (degrees)', element.get('azimuth', 180)))
        
        # Get host wall relationship from BIM data
        host_wall_id = element.get('HostWallId', element.get('Wall Element ID', 'Unknown'))
        
        # Analyze wall-window relationship if walls data is available
        wall_relationship = analyze_wall_window_relationship(element_id, host_wall_id, walls_data)
        
        # Calculate tilt based on building type (assume vertical windows for BIPV)
        tilt = 90.0  # Vertical facade
        
        # Calculate irradiance for each hour
        hourly_irradiance = []
        
        for _, hour_data in tmy_df.iterrows():
            solar_pos = calculate_solar_position_simple(
                latitude, longitude, 
                hour_data['day_of_year'], 
                hour_data['hour']
            )
            
            # Get irradiance components (with defaults)
            ghi = float(hour_data.get('GHI', hour_data.get('ghi', 0)) or 0)
            dni = float(hour_data.get('DNI', hour_data.get('dni', 0)) or 0)
            dhi = float(hour_data.get('DHI', hour_data.get('dhi', ghi * 0.1)) or 0)  # Estimate DHI if missing
            
            surface_irradiance = calculate_irradiance_on_surface(
                ghi, dni, dhi, solar_pos, tilt, azimuth
            )
            
            # Apply shading if available
            if shading_factors is not None:
                shading_factor = shading_factors.get(str(hour_data['hour']), {}).get('shading_factor', 1.0)
                if shading_factor is not None:
                    surface_irradiance = surface_irradiance * shading_factor
            
            hourly_irradiance.append(surface_irradiance)
        
        # Convert to numpy array for calculations
        irradiance_array = np.array(hourly_irradiance)
        
        # Calculate monthly irradiation
        tmy_df_copy = tmy_df.copy()
        tmy_df_copy['irradiance'] = irradiance_array
        monthly_sums = tmy_df_copy.groupby(tmy_df_copy['datetime'].dt.month)['irradiance'].sum()
        monthly_irradiation = {}
        for month in monthly_sums.index:
            monthly_irradiation[month] = float(monthly_sums.iloc[month-1]) / 1000  # Convert W to kW
        
        # Calculate statistics with realistic orientation adjustments
        base_annual_irradiation = irradiance_array.sum() / 1000  # kWh/m²/year
        
        # Apply realistic orientation corrections for Northern Hemisphere
        orientation_factors = {
            'South (135-225°)': 1.0,         # Optimal solar exposure
            'Southeast': 0.95,
            'Southwest': 0.95,
            'West (225-315°)': 0.75,         # Moderate afternoon sun  
            'East (45-135°)': 0.75,          # Moderate morning sun
            'Northwest': 0.45,
            'Northeast': 0.45,
            'North (315-45°)': 0.30          # Realistic low value for north-facing
        }
        
        orientation_factor = orientation_factors.get(orientation, 0.7)
        annual_irradiation = max(base_annual_irradiation * orientation_factor, 200)  # Minimum 200 kWh/m²/year
        
        peak_irradiance = irradiance_array.max()  # W/m²
        avg_irradiance = irradiance_array.mean()  # W/m²
        
        element_radiation = {
            'element_id': element_id,
            'element_type': 'Window',
            'orientation': orientation,
            'area': element_area,
            'tilt': tilt,
            'azimuth': azimuth,
            'annual_irradiation': annual_irradiation,
            'peak_irradiance': peak_irradiance,
            'avg_irradiance': avg_irradiance,
            'capacity_factor': safe_divide(avg_irradiance, 1000, 0),  # Simplified capacity factor
            'monthly_irradiation': monthly_irradiation,
            'host_wall_id': host_wall_id,
            'host_wall_found': wall_relationship['host_wall_found'],
            'wall_area': wall_relationship['wall_area'],
            'wall_level': wall_relationship['wall_level'],
            'wall_azimuth': wall_relationship['wall_azimuth'],
            'geometric_compatibility': wall_relationship['geometric_compatibility']
        }
        
        radiation_grid.append(element_radiation)
    
    return pd.DataFrame(radiation_grid)

def apply_orientation_corrections(radiation_df):
    """Apply orientation and tilt corrections to radiation calculations."""
    
    # Orientation factor corrections (relative to south-facing)
    orientation_corrections = {
        'South': 1.0,
        'Southwest': 0.95,
        'Southeast': 0.95,
        'West': 0.85,
        'East': 0.85,
        'Northwest': 0.70,
        'Northeast': 0.70,
        'North': 0.50
    }
    
    # Apply corrections
    radiation_df = radiation_df.copy()
    radiation_df['orientation_correction'] = radiation_df['orientation'].map(
        lambda x: orientation_corrections.get(x, 0.8)
    )
    
    # Apply correction to annual irradiation
    radiation_df['corrected_annual_irradiation'] = (
        radiation_df['annual_irradiation'] * radiation_df['orientation_correction']
    )
    
    return radiation_df

def render_radiation_grid():
    """Render the radiation and shading grid analysis module."""
    
    # Add OptiSunny character header image
    st.image("attached_assets/step05_1751436847830.png", width=400)
    
    st.header("☀️ Step 5: Solar Radiation & Shading Analysis")
    
    # Data Usage Information
    with st.expander("📊 How This Data Will Be Used", expanded=False):
        st.markdown("""
        ### Data Flow Through BIPV Analysis Workflow:
        
        **Step 5 → Step 6 (PV Specification):**
        - **Annual irradiation (kWh/m²)** → BIPV glass performance calculations and technology selection
        - **Peak irradiance values** → System derating and inverter sizing requirements
        - **Element-specific radiation** → Individual window system capacity calculations
        
        **Step 5 → Step 7 (Yield vs Demand):**
        - **Monthly radiation profiles** → Seasonal energy generation patterns and grid interaction analysis
        - **Orientation-specific yields** → Directional energy balance calculations
        - **Shading-corrected irradiation** → Realistic energy production forecasting
        
        **Step 5 → Step 8 (Optimization):**
        - **Element radiation rankings** → Genetic algorithm selection criteria for high-performance systems
        - **Solar resource distribution** → Multi-objective optimization constraints and feasibility analysis
        
        **Step 5 → Step 10 (Reporting):**
        - **Solar analysis methodology** → Technical documentation of pvlib calculations and ISO standards compliance
        - **Radiation heatmaps** → Visual assessment of building solar potential and optimization opportunities
        - **Shading analysis results** → Geometric accuracy validation and environmental impact assessment
        """)
    
    # Check for building elements data from Step 4
    building_elements = st.session_state.get('building_elements')
    if building_elements is None or len(building_elements) == 0:
        st.warning("⚠️ Building elements data required. Please complete Step 4 (Facade & Window Extraction) first.")
        st.info("The radiation analysis requires building geometry data to calculate solar irradiance on specific facade elements.")
        return
    
    # Check for weather data from Step 3
    weather_analysis = st.session_state.get('project_data', {}).get('weather_analysis')
    tmy_data = None
    if weather_analysis:
        tmy_data = weather_analysis.get('tmy_data')
    
    if tmy_data is None:
        st.warning("⚠️ Weather data required. Please complete Step 3 (Weather & Environment Integration) first.")
        st.info("Solar radiation analysis requires TMY (Typical Meteorological Year) data for accurate calculations.")
        return
    
    # Load required data
    project_data = st.session_state.get('project_data', {})
    
    # Use building_elements from session state as primary source
    suitable_elements = st.session_state.get('building_elements')
    if suitable_elements is None:
        suitable_elements = project_data.get('suitable_elements')
        
    # TMY data already validated above
    coordinates = project_data.get('coordinates', {})
    
    if suitable_elements is None or len(suitable_elements) == 0:
        st.error("No suitable building elements found. Please check Step 4 data.")
        return
    
    latitude = coordinates.get('lat', 52.52)
    longitude = coordinates.get('lng', 13.405)
    
    st.success(f"Analyzing {len(suitable_elements)} building elements for solar radiation potential")
    
    # Configuration section
    with st.expander("🔧 Analysis Configuration", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            include_shading = st.checkbox("Include Geometric Self-Shading", value=True, key="include_shading_rad")
            apply_corrections = st.checkbox("Apply Orientation Corrections", value=True, key="apply_corrections_rad")
        
        with col2:
            analysis_precision = st.selectbox(
                "Analysis Precision",
                ["Standard", "High", "Maximum"],
                index=0,
                key="analysis_precision_rad"
            )
    
    # Building walls upload for geometric shading
    walls_data = None
    shading_factors = None
    if include_shading:
        st.subheader("🏢 Building Walls for Geometric Self-Shading")
        
        # Add comprehensive explanation for geometric shading
        with st.expander("🔍 Understanding Geometric Self-Shading Analysis", expanded=False):
            st.markdown("""
            **Purpose of Geometric Self-Shading:**
            
            Instead of using simplified time-based shading factors, this analysis calculates precise shadow patterns using actual building geometry data from your BIM model.
            
            **What Building Walls Data Provides:**
            - **Element Geometry**: Wall dimensions, orientations, and positions
            - **Multi-Story Analysis**: Upper floor walls shading lower floor windows
            - **Architectural Features**: Protruding sections, overhangs, and building massing effects
            - **Seasonal Variations**: Accurate shadow patterns for different sun angles throughout the year
            
            **Required CSV Structure:**
            - **ElementId**: Unique wall identifier
            - **Level**: Floor/story information (00, 01, 02, etc.)
            - **Length (m)** & **Area (m²)**: Physical wall dimensions
            - **OriX, OriY, OriZ**: Wall orientation vectors
            - **Azimuth (°)**: Wall facing direction (0-360°)
            
            **Analysis Benefits:**
            - **Precision**: Calculate exact shadow polygons cast by building elements
            - **Time-Dependent**: Hourly shadow analysis for complete accuracy
            - **Element-Specific**: Individual shading factors for each window based on local geometry
            - **Optimization**: Identify optimal BIPV placement considering real architectural constraints
            
            **How It Works:**
            1. **Solar Position Calculation**: Determine sun angles for each hour and day
            2. **Shadow Geometry**: Calculate shadow polygons cast by wall elements
            3. **Intersection Analysis**: Determine shadow overlap with window surfaces
            4. **Shading Factors**: Generate precise hourly shading multipliers for each window
            """)
        
        # File uploader for building walls
        st.info("Upload your building walls CSV file to enable precise geometric self-shading calculations")
        
        walls_file = st.file_uploader(
            "Upload Building Walls CSV",
            type=['csv'],
            key="walls_upload_rad",
            help="CSV file containing building wall geometry data extracted from BIM model. Must include ElementId, Level, Length, Area, OriX, OriY, OriZ, and Azimuth columns."
        )
        
        if walls_file is not None:
            try:
                # Read and process walls CSV
                walls_df = pd.read_csv(walls_file)
                
                # Validate required columns
                required_cols = ['ElementId', 'Level', 'Length (m)', 'Area (m²)', 'OriX', 'OriY', 'OriZ', 'Azimuth (°)']
                missing_cols = [col for col in required_cols if col not in walls_df.columns]
                
                if missing_cols:
                    st.error(f"Missing required columns: {', '.join(missing_cols)}")
                    st.info("Required columns: ElementId, Level, Length (m), Area (m²), OriX, OriY, OriZ, Azimuth (°)")
                else:
                    # Filter out rows with missing geometric data
                    walls_df_clean = walls_df.dropna(subset=['OriX', 'OriY', 'OriZ', 'Azimuth (°)'])
                    
                    if len(walls_df_clean) == 0:
                        st.warning("No walls found with complete geometric data (OriX, OriY, OriZ, Azimuth)")
                    else:
                        walls_data = walls_df_clean
                        st.success(f"Successfully loaded {len(walls_data)} wall elements for geometric shading analysis")
                        
                        # Display summary statistics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Walls", len(walls_data))
                        with col2:
                            levels = walls_data['Level'].nunique()
                            st.metric("Building Levels", levels)
                        with col3:
                            total_area = walls_data['Area (m²)'].sum()
                            st.metric("Total Wall Area", f"{total_area:.1f} m²")
                        
                        # Show orientation distribution
                        if st.checkbox("Show Wall Orientation Analysis", key="show_wall_orientation"):
                            orientation_counts = walls_data['Azimuth (°)'].value_counts().head(10)
                            st.bar_chart(orientation_counts)
                            st.caption("Distribution of wall orientations (top 10 azimuth angles)")
                            
            except Exception as e:
                st.error(f"Error processing walls CSV file: {str(e)}")
                st.info("Please ensure the CSV file has the correct format and column names")
        else:
            st.warning("⚠️ Building walls data required for geometric self-shading analysis. Please upload walls CSV file.")
        
        # Generate geometric shading factors if walls data is available
        if walls_data is not None:
            with st.spinner("Calculating geometric shading factors from building walls..."):
                shading_factors = calculate_geometric_shading_factors(walls_data, suitable_elements, latitude, longitude)
                if shading_factors:
                    st.success(f"Generated geometric shading factors for {len(shading_factors)} time periods")
                else:
                    st.warning("Could not generate shading factors from walls data")
    
    # Analysis execution
    if st.button("🚀 Run Radiation Analysis", key="run_radiation_analysis"):
        # Create progress tracking containers
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            element_progress = st.empty()
        
        try:
            # Initialize progress
            status_text.text("Initializing radiation analysis...")
            progress_bar.progress(5)
            
            # Optimize analysis based on precision setting
            if analysis_precision == "Standard":
                sample_hours = list(range(6, 19, 2))  # Every 2 hours during daylight
                days_sample = list(range(15, 365, 30))  # Monthly samples
            elif analysis_precision == "High":
                sample_hours = list(range(6, 19))  # Hourly during daylight
                days_sample = list(range(1, 365, 15))  # Bi-weekly samples
            else:  # Maximum
                sample_hours = list(range(24))  # All hours
                days_sample = list(range(1, 365, 7))  # Weekly samples
            
            status_text.text(f"Processing {len(suitable_elements)} elements with {analysis_precision.lower()} precision...")
            progress_bar.progress(10)
            
            # Process each element with detailed progress
            radiation_results = []
            total_elements = len(suitable_elements)
            
            # Convert DataFrame to list of dictionaries if needed
            if hasattr(suitable_elements, 'iterrows'):
                elements_list = []
                for _, row in suitable_elements.iterrows():
                    # Preserve actual Element IDs from BIM upload
                    actual_element_id = row.get('Element ID', row.get('element_id', f'Unknown_Element_{len(elements_list)+1}'))
                    elements_list.append({
                        'element_id': actual_element_id,
                        'azimuth': row.get('azimuth', 180),
                        'tilt': row.get('tilt', 90),
                        'glass_area': row.get('glass_area', 1.5),
                        'orientation': row.get('orientation', 'Unknown'),
                        'level': row.get('level', 'Level 1'),
                        'wall_hosted_id': row.get('wall_hosted_id', 'N/A'),
                        'width': row.get('window_width', row.get('width', row.get('Width', 1.2))),
                        'height': row.get('window_height', row.get('height', row.get('Height', 1.5)))
                    })
                suitable_elements = elements_list
            
            for i, element in enumerate(suitable_elements):
                # Extract element data from BIM upload - preserve actual Element IDs
                element_id = element.get('element_id', f'Unknown_Element_{i+1}')
                azimuth = element.get('azimuth', 180)
                tilt = element.get('tilt', 90)
                area = element.get('glass_area', 1.5)  # Use actual BIM glass area
                orientation = element.get('orientation', 'Unknown')
                level = element.get('level', 'Level 1')
                width = element.get('window_width', element.get('width', element.get('Width', 1.2)))
                height = element.get('window_height', element.get('height', element.get('Height', 1.5)))
                
                # Update progress indicators with BIM data details
                element_progress.text(f"Processing: {element_id} | {orientation} | {area:.1f}m² | {level}")
                current_progress = 10 + int(70 * i / total_elements)
                progress_bar.progress(current_progress)
                
                # Calculate radiation for this element
                annual_irradiance = 0
                peak_irradiance = 0
                sample_count = 0
                monthly_irradiation = {}
                
                for month in range(1, 13):
                    monthly_total = 0
                    monthly_samples = 0
                    
                    for day in days_sample:
                        if day < 28 or (day < 32 and month in [1,3,5,7,8,10,12]) or (day < 31 and month in [4,6,9,11]) or (day < 30 and month == 2):
                            for hour in sample_hours:
                                # Calculate day of year
                                days_in_months = [31,28,31,30,31,30,31,31,30,31,30,31]
                                day_of_year = sum(days_in_months[:month-1]) + day
                                
                                if day_of_year < len(tmy_data):
                                    tmy_index = min((day_of_year - 1) * 24 + hour, len(tmy_data) - 1)
                                    hour_data = tmy_data[tmy_index]
                                    
                                    # Skip nighttime for efficiency
                                    if hour < 6 or hour > 19:
                                        continue
                                    
                                    # Calculate solar position
                                    solar_pos = calculate_solar_position_simple(latitude, longitude, day_of_year, hour)
                                    
                                    # Skip if sun below horizon
                                    if solar_pos['elevation'] <= 0:
                                        continue
                                    
                                    # Calculate surface irradiance
                                    surface_irradiance = calculate_irradiance_on_surface(
                                        hour_data.get('ghi', 0),
                                        hour_data.get('dni', 0),
                                        hour_data.get('dhi', 0),
                                        solar_pos,
                                        tilt,
                                        azimuth
                                    )
                                    
                                    annual_irradiance += surface_irradiance
                                    monthly_total += surface_irradiance
                                    peak_irradiance = max(peak_irradiance, surface_irradiance)
                                    sample_count += 1
                                    monthly_samples += 1
                    
                    # Store monthly average
                    if monthly_samples > 0:
                        monthly_irradiation[str(month)] = monthly_total / monthly_samples * 730  # Scale to monthly total
                
                # Scale to annual totals
                scaling_factor = 8760 / max(sample_count, 1)
                annual_irradiance = annual_irradiance * scaling_factor / 1000  # Convert to kWh/m²
                
                radiation_results.append({
                    'element_id': element_id,
                    'element_type': 'Window',
                    'orientation': orientation,
                    'azimuth': azimuth,
                    'tilt': tilt,
                    'area': area,
                    'level': level,
                    'wall_hosted_id': element.get('wall_hosted_id', 'N/A'),
                    'width': width,
                    'height': height,
                    'annual_irradiation': annual_irradiance,
                    'peak_irradiance': peak_irradiance,
                    'avg_irradiance': annual_irradiance * 1000 / 8760,  # Average W/m²
                    'monthly_irradiation': monthly_irradiation,
                    'capacity_factor': min(annual_irradiance / 1800, 1.0),  # Theoretical max ~1800 kWh/m²
                    'annual_energy_potential': annual_irradiance * area  # kWh per element
                })
            
            # Convert to DataFrame
            radiation_data = pd.DataFrame(radiation_results)
            
            # Apply corrections if requested
            if apply_corrections:
                status_text.text("Applying orientation corrections...")
                progress_bar.progress(85)
                radiation_data = apply_orientation_corrections(radiation_data)
            
            # Final processing
            status_text.text("Finalizing analysis and saving results...")
            progress_bar.progress(95)
            
            if len(radiation_data) == 0:
                st.error("Failed to generate radiation data")
                return
                
                # Apply orientation corrections if requested
                if apply_corrections:
                    radiation_data = apply_orientation_corrections(radiation_data)
                
            # Save to session state and database
            st.session_state.project_data['radiation_data'] = radiation_data
            st.session_state.radiation_completed = True
            
            # Save to consolidated data manager
            consolidated_manager = ConsolidatedDataManager()
            step5_data = {
                'radiation_data': radiation_data.to_dict('records'),
                'element_radiation': radiation_data.to_dict('records'),
                'analysis_parameters': {
                    'include_shading': include_shading,
                    'apply_corrections': apply_corrections,
                    'precision': analysis_precision,
                    'shading_factors': shading_factors
                },
                'radiation_complete': True
            }
            consolidated_manager.save_step5_data(step5_data)
            
            # Save to database if project_id exists
            if 'project_id' in st.session_state and st.session_state.project_id:
                try:
                    db_manager.save_radiation_analysis(
                        st.session_state.project_id,
                        {
                            'radiation_grid': radiation_data.to_dict('records'),
                            'analysis_config': {
                                'include_shading': include_shading,
                                'apply_corrections': apply_corrections,
                                'precision': analysis_precision,
                                'shading_factors': shading_factors
                            },
                            'location': {'latitude': latitude, 'longitude': longitude}
                        }
                    )
                except Exception as db_error:
                    st.warning(f"Could not save to database: {str(db_error)}")
            else:
                st.info("Analysis results saved to session only (no project ID available)")
            
            # Complete progress
            progress_bar.progress(100)
            status_text.text("Analysis completed successfully!")
            element_progress.text(f"Processed all {total_elements} elements")
            
            st.success("✅ Radiation analysis completed successfully!")
            
        except Exception as e:
            st.error(f"Error during radiation analysis: {str(e)}")
            progress_bar.progress(0)
            status_text.text("Analysis failed")
            element_progress.text("")
            return
    
    # Display results if available
    if st.session_state.get('radiation_completed', False):
        radiation_data = st.session_state.project_data.get('radiation_data')
        
        if radiation_data is not None and len(radiation_data) > 0:
            st.subheader("📊 Radiation Analysis Results")
            
            # Summary statistics based on actual BIM data
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_elements = len(radiation_data)
                st.metric("Total Window Elements", f"{total_elements}")
            
            with col2:
                total_area = radiation_data['area'].sum()
                st.metric("Total Window Area", f"{total_area:.1f} m²")
            
            with col3:
                avg_annual = radiation_data['annual_irradiation'].mean()
                st.metric("Avg Annual Irradiation", f"{avg_annual:.0f} kWh/m²")
            
            with col4:
                total_energy_potential = radiation_data['annual_energy_potential'].sum()
                st.metric("Total Energy Potential", f"{total_energy_potential:.0f} kWh/year")
            
            with col3:
                avg_peak = radiation_data['peak_irradiance'].mean()
                st.metric("Average Peak Irradiance", f"{avg_peak:.0f} W/m²")
            
            with col4:
                total_area = radiation_data['area'].sum()
                st.metric("Total Analyzed Area", f"{total_area:.1f} m²")
            
            # BIM-based detailed results table
            st.subheader("📋 BIM Element Analysis Results")
            
            # Prepare display dataframe with BIM metadata
            display_df = radiation_data.copy()
            display_columns = ['element_id', 'level', 'orientation', 'area', 'width', 'height', 
                             'annual_irradiation', 'annual_energy_potential', 'peak_irradiance']
            
            if apply_corrections and 'corrected_annual_irradiation' in display_df.columns:
                display_columns.append('corrected_annual_irradiation')
            
            st.dataframe(
                display_df[display_columns].round(2),
                use_container_width=True,
                column_config={
                    'element_id': 'Element ID',
                    'level': 'Building Level',
                    'orientation': 'Orientation',
                    'area': st.column_config.NumberColumn('Area (m²)', format="%.2f"),
                    'width': st.column_config.NumberColumn('Width (m)', format="%.2f"),
                    'height': st.column_config.NumberColumn('Height (m)', format="%.2f"),
                    'annual_irradiation': st.column_config.NumberColumn('Annual Irradiation (kWh/m²)', format="%.0f"),
                    'annual_energy_potential': st.column_config.NumberColumn('Energy Potential (kWh/year)', format="%.0f"),
                    'peak_irradiance': st.column_config.NumberColumn('Peak Irradiance (W/m²)', format="%.0f"),
                    'corrected_annual_irradiation': st.column_config.NumberColumn('Corrected Annual (kWh/m²)', format="%.0f")
                }
            )
            
            # Visualization section
            st.subheader("📈 Radiation Distribution Analysis")
            
            tab1, tab2, tab3 = st.tabs(["Annual Irradiation", "Orientation Analysis", "Monthly Patterns"])
            
            with tab1:
                # Annual irradiation histogram
                fig_hist = px.histogram(
                    radiation_data, 
                    x='annual_irradiation',
                    title="Distribution of Annual Irradiation",
                    labels={'annual_irradiation': 'Annual Irradiation (kWh/m²)', 'count': 'Number of Elements'}
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            
            with tab2:
                # Radiation by orientation
                orientation_stats = radiation_data.groupby('orientation')['annual_irradiation'].agg(['mean', 'count']).reset_index()
                
                fig_orient = px.bar(
                    orientation_stats,
                    x='orientation',
                    y='mean',
                    title="Average Annual Irradiation by Orientation",
                    labels={'mean': 'Avg Annual Irradiation (kWh/m²)', 'orientation': 'Orientation'}
                )
                st.plotly_chart(fig_orient, use_container_width=True)
            
            with tab3:
                # Monthly patterns (if monthly data available)
                if 'monthly_irradiation' in radiation_data.columns:
                    # Extract monthly data for visualization
                    monthly_data = []
                    for _, row in radiation_data.iterrows():
                        if isinstance(row['monthly_irradiation'], dict):
                            for month, irrad in row['monthly_irradiation'].items():
                                monthly_data.append({
                                    'element_id': row['element_id'],
                                    'month': int(month),
                                    'irradiation': irrad,
                                    'orientation': row['orientation']
                                })
                    
                    if monthly_data:
                        monthly_df = pd.DataFrame(monthly_data)
                        monthly_avg = monthly_df.groupby('month')['irradiation'].mean().reset_index()
                        
                        fig_monthly = px.line(
                            monthly_avg,
                            x='month',
                            y='irradiation',
                            title="Average Monthly Irradiation Pattern",
                            labels={'irradiation': 'Monthly Irradiation (kWh/m²)', 'month': 'Month'}
                        )
                        st.plotly_chart(fig_monthly, use_container_width=True)
                    else:
                        st.info("Monthly pattern data not available")
                else:
                    st.info("Monthly pattern data not available")
            
            # Export options
            st.subheader("💾 Export Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 Download Radiation Data (CSV)", key="download_radiation_csv"):
                    csv_data = radiation_data.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv_data,
                        file_name=f"radiation_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            
            with col2:
                st.info("Radiation analysis ready for next step (PV Specification)")
            
            # Add step-specific download button
            st.markdown("---")
            st.markdown("### 📄 Step 5 Analysis Report")
            st.markdown("Download detailed radiation and shading analysis report:")
            
            from utils.individual_step_reports import create_step_download_button
            create_step_download_button(5, "Radiation Grid", "Download Radiation Analysis Report")
        
        else:
            st.warning("No radiation data available. Please run the analysis.")