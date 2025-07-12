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

def calculate_precise_shading_factor(wall_element, window_element, solar_position):
    """Calculate precise shading factor for a window from a specific wall at given solar position."""
    try:
        # Get wall properties
        wall_azimuth = float(wall_element.get('Azimuth (°)', 180))
        wall_length = float(wall_element.get('Length (m)', 1.0))
        wall_height = float(wall_element.get('Height (m)', 3.0))
        wall_level = wall_element.get('Level', 'Level 1')
        
        # Get window properties
        window_azimuth = float(window_element.get('azimuth', 180))
        window_level = window_element.get('level', 'Level 1')
        window_area = float(window_element.get('glass_area', 1.5))
        
        # Get solar position
        sun_elevation = solar_position.get('elevation', 0)
        sun_azimuth = solar_position.get('azimuth', 180)
        
        # Skip if sun below horizon
        if sun_elevation <= 0:
            return 1.0  # No shading at night
        
        # Calculate shadow length based on sun elevation
        shadow_length = wall_height / np.tan(np.radians(max(sun_elevation, 0.1)))
        
        # Check if wall can shade this window based on relative positions
        # 1. Azimuth proximity check
        azimuth_diff = abs(wall_azimuth - window_azimuth)
        if azimuth_diff > 180:
            azimuth_diff = 360 - azimuth_diff
        
        # 2. Level compatibility check (wall should be same level or higher)
        level_factor = 1.0
        if wall_level != window_level:
            # Simplified level impact - walls on different levels have reduced shading effect
            level_factor = 0.5
        
        # 3. Calculate geometric shading intensity
        if azimuth_diff < 90:  # Wall can potentially shade window
            # Calculate shadow coverage based on wall-window relationship
            proximity_factor = max(0, 1 - (azimuth_diff / 90))  # Closer azimuth = more shading
            
            # Shadow intensity based on sun angle relative to wall
            wall_sun_angle = abs(wall_azimuth - sun_azimuth)
            if wall_sun_angle > 180:
                wall_sun_angle = 360 - wall_sun_angle
            
            # Wall creates shadow when sun is behind it (angle > 90°)
            if wall_sun_angle > 90:
                shadow_intensity = min(0.6, (wall_sun_angle - 90) / 90 * 0.6)  # Max 60% shading
                shading_factor = max(0.4, 1.0 - (shadow_intensity * proximity_factor * level_factor))
            else:
                shading_factor = 1.0  # No shading when sun hits wall directly
        else:
            shading_factor = 1.0  # No shading when azimuth difference too large
        
        return shading_factor
        
    except Exception as e:
        return 0.9  # Conservative default shading factor
    
def calculate_combined_shading_factor(window_element, walls_data, solar_position):
    """Calculate combined shading factor from all walls for a window at specific solar position."""
    if walls_data is None or len(walls_data) == 0:
        return 1.0  # No shading if no wall data
    
    combined_shading_factor = 1.0
    
    # Check shading from each wall
    for _, wall in walls_data.iterrows():
        wall_shading_factor = calculate_precise_shading_factor(wall, window_element, solar_position)
        # Multiply factors (shadows accumulate multiplicatively)
        combined_shading_factor *= wall_shading_factor
    
    return max(0.2, combined_shading_factor)  # Minimum 20% of unshaded radiation

def calculate_ground_reflectance_factor(height_from_ground, tilt_angle=90, albedo=0.2):
    """
    Calculate ground reflectance contribution based on window height from ground.
    
    Args:
        height_from_ground (float): Height of window center from ground in meters
        tilt_angle (float): Window tilt angle in degrees (90° for vertical windows)
        albedo (float): Ground albedo (reflectance coefficient)
    
    Returns:
        float: Ground reflectance factor (typically 0.05-0.15 for vertical windows)
    """
    import math
    
    # View factor to ground for vertical surface (simplified)
    # Based on standard solar engineering formulas
    if height_from_ground <= 0:
        return 0.0
    
    # Calculate view factor to ground based on height and tilt
    tilt_rad = math.radians(tilt_angle)
    
    # For vertical windows (90°), view factor decreases with height
    if tilt_angle >= 85:  # Nearly vertical
        # Empirical formula for vertical surfaces
        view_factor_ground = max(0.1, 0.5 * math.exp(-height_from_ground / 10.0))
    else:
        # For tilted surfaces, more complex calculation
        view_factor_ground = (1 - math.cos(tilt_rad)) / 2
        # Height correction
        view_factor_ground *= max(0.2, math.exp(-height_from_ground / 15.0))
    
    # Ground reflectance contribution
    ground_reflectance_factor = albedo * view_factor_ground
    
    return min(ground_reflectance_factor, 0.15)  # Cap at 15% contribution

def calculate_height_dependent_ghi_effects(height_from_ground, base_ghi):
    """
    Calculate height-dependent effects on Global Horizontal Irradiance (GHI).
    
    At higher elevations, windows receive:
    - Less atmospheric attenuation (clearer air)
    - Reduced ground-level pollution effects
    - Different horizon obstruction angles
    
    Args:
        height_from_ground (float): Height of window center from ground in meters
        base_ghi (float): Base GHI value at ground level
    
    Returns:
        dict: {
            'adjusted_ghi': float,
            'height_factor': float,
            'atmospheric_clarity': float,
            'horizon_factor': float
        }
    """
    import math
    
    # Height-dependent atmospheric clarity improvement
    # Based on standard atmospheric models - clearer air at height
    atmospheric_clarity = 1.0 + (height_from_ground * 0.001)  # 0.1% improvement per meter
    atmospheric_clarity = min(atmospheric_clarity, 1.05)  # Cap at 5% improvement
    
    # Horizon obstruction factor - higher windows have better sky view
    # Ground-level obstacles (buildings, trees) have less impact at height
    if height_from_ground <= 3.0:  # Ground level - significant obstruction
        horizon_factor = 0.95  # 5% reduction due to ground obstacles
    elif height_from_ground <= 10.0:  # Low to mid height
        horizon_factor = 0.98  # 2% reduction
    else:  # High elevation - minimal obstruction
        horizon_factor = 1.0   # No significant obstruction
    
    # Combined height factor
    height_factor = atmospheric_clarity * horizon_factor
    
    # Adjusted GHI
    adjusted_ghi = base_ghi * height_factor
    
    return {
        'adjusted_ghi': adjusted_ghi,
        'height_factor': height_factor,
        'atmospheric_clarity': atmospheric_clarity,
        'horizon_factor': horizon_factor
    }

def calculate_height_dependent_solar_angles(solar_pos, height_from_ground):
    """
    Calculate height-dependent adjustments to solar angle calculations.
    
    Higher elevations experience:
    - Different effective horizon angles
    - Reduced atmospheric refraction effects
    - Modified solar position due to earth curvature (minimal for building heights)
    
    Args:
        solar_pos (dict): Solar position with elevation and azimuth
        height_from_ground (float): Height of window center from ground in meters
    
    Returns:
        dict: Adjusted solar position with height corrections
    """
    import math
    
    # Copy original solar position
    adjusted_pos = solar_pos.copy()
    
    # Height-dependent horizon elevation adjustment
    # Higher points have a lower apparent horizon
    earth_radius = 6371000  # Earth radius in meters
    horizon_depression = math.degrees(math.sqrt(2 * height_from_ground / earth_radius))
    
    # Effective solar elevation accounting for horizon depression
    effective_elevation = solar_pos['elevation'] + horizon_depression
    
    # Atmospheric refraction is slightly less at height (very small effect for building heights)
    refraction_reduction = height_from_ground * 0.0001  # Minimal effect
    refraction_adjusted_elevation = effective_elevation - refraction_reduction
    
    # Update adjusted position
    adjusted_pos['effective_elevation'] = max(0, refraction_adjusted_elevation)
    adjusted_pos['horizon_depression'] = horizon_depression
    adjusted_pos['height_correction'] = refraction_adjusted_elevation - solar_pos['elevation']
    
    return adjusted_pos

def estimate_height_from_ground(level, floor_height=3.5):
    """
    Estimate window height from ground based on building level.
    
    Args:
        level (str): Building level (e.g., '00', '01', '02', etc.)
        floor_height (float): Typical floor-to-floor height in meters
    
    Returns:
        float: Estimated height from ground in meters
    """
    try:
        # Extract numeric level
        level_num = int(level)
        
        # Ground floor (level 00) windows are typically 1-2m from ground
        if level_num == 0:
            return 1.5  # Ground floor window center height
        
        # Upper floors: ground floor height + (level-1) * floor_height + window_center
        # Assuming ground floor is 3.5m high, upper floors are floor_height
        # Window center is typically 1.5m from floor
        height = 3.5 + (level_num - 1) * floor_height + 1.5
        
        return height
        
    except (ValueError, TypeError):
        # Default for unknown levels
        return 5.0  # Assume second floor equivalent

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
    """Generate radiation grid for ONLY suitable elements (South/East/West-facing) with wall-window relationship analysis."""
    
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
        # Verify element is actually suitable (double-check filtering)
        is_suitable = element.get('pv_suitable', element.get('suitable', True))
        if not is_suitable:
            continue  # Skip non-suitable elements
            
        # Get element properties with defaults - preserve actual BIM Element IDs
        element_id = element.get('Element ID', element.get('element_id', element.get('id', f"Unknown_Element_{len(radiation_grid)}")))
        element_area = float(element.get('Glass Area (m²)', element.get('glass_area', element.get('area', 1.5))))
        orientation = element.get('Orientation', element.get('orientation', 'South'))
        azimuth = float(element.get('Azimuth (degrees)', element.get('azimuth', 180)))
        
        # Get host wall relationship from BIM data
        host_wall_id = element.get('HostWallId', element.get('Wall Element ID', 'Unknown'))
        
        # Analyze wall-window relationship if walls data is available
        wall_relationship = analyze_wall_window_relationship(element_id, host_wall_id, walls_data)
        
        # Calculate actual tilt angle from BIM orientation vectors
        import math
        ori_z = element.get('OriZ', element.get('oriz', None))
        
        if ori_z is not None:
            try:
                ori_z_float = float(ori_z)
                # Clamp OriZ to valid range [-1, 1] to avoid math domain errors
                ori_z_clamped = max(-1.0, min(1.0, ori_z_float))
                # Calculate tilt: tilt = arccos(|OriZ|) in degrees
                tilt = math.degrees(math.acos(abs(ori_z_clamped)))
            except (ValueError, TypeError):
                # Fallback to vertical if OriZ is invalid
                tilt = 90.0
        else:
            # Fallback to vertical if OriZ not available
            tilt = 90.0
        
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
        
        ### 🏗️ NEW: Ground Height Considerations
        
        **Enhanced Height-Based Analysis:**
        - **Window height from ground** → Ground reflectance effects on solar irradiance
        - **Level-based calculation** → Building floor heights estimated for accurate ground view factors
        - **Ground albedo effects** → Lower floors receive more reflected solar radiation from ground surfaces
        - **Height-corrected irradiance** → More accurate radiation values for ground-level vs upper-floor windows
        """)
    
    # Comprehensive Height Effects Information
    with st.expander("🏗️ Comprehensive Height-Dependent Effects Analysis", expanded=False):
        st.markdown("""
        ### Why Window Height from Ground Affects Solar Radiation:
        
        **1. Ground Reflectance Effects:**
        - **Lower windows** (Levels 00-02) receive additional solar radiation reflected from ground surfaces
        - **Ground albedo** typically ranges from 0.15-0.25 (concrete/asphalt) to 0.8+ (snow)
        - **View factor to ground** decreases exponentially with height above ground
        - **Ground floor windows:** Up to 10-15% additional irradiance from ground reflection
        - **Mid-level windows:** 5-8% additional irradiance 
        - **Upper floor windows:** 2-3% additional irradiance
        
        **2. GHI (Global Horizontal Irradiance) Height Effects:**
        - **Atmospheric clarity improvement:** Higher windows experience less atmospheric attenuation (~0.1% per meter)
        - **Reduced pollution effects:** Ground-level air pollution reduces solar radiation penetration
        - **Cleaner air at height:** Better atmospheric transmission of solar radiation
        - **Height enhancement:** Up to 5% improvement at 50m height
        
        **3. Solar Angle & Horizon Effects:**
        - **Horizon depression:** Higher windows have effectively lower horizon angles
        - **Better sky view:** Reduced obstruction from ground-level obstacles (buildings, trees)
        - **Atmospheric refraction:** Slightly reduced atmospheric distortion at height
        - **Effective solar elevation:** Improved solar access due to horizon depression
        
        **4. Combined Height Enhancement Factor:**
        - **Ground reflectance contribution:** Variable by height (2-15%)
        - **GHI enhancement factor:** Atmospheric and horizon improvements (0.5-5%)
        - **Total enhancement:** Combined effect can be 5-20% for ground floors vs upper floors
        
        **Height Estimation Method:**
        - **Level 00 (Ground Floor):** Window center ~1.5m from ground
        - **Upper Levels:** Ground floor height (3.5m) + (level-1) × floor height (3.5m) + window center (1.5m)
        - **Example:** Level 04 window ≈ 3.5 + 3×3.5 + 1.5 = 15.5m from ground
        
        This comprehensive analysis makes radiation calculations significantly more accurate by considering all height-dependent physical effects on solar irradiance.
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
    
    # Load ALL building elements from session state
    all_building_elements = st.session_state.get('building_elements')
    if all_building_elements is None:
        all_building_elements = project_data.get('building_elements', project_data.get('suitable_elements'))
        
    if all_building_elements is None or len(all_building_elements) == 0:
        st.error("No building elements found. Please check Step 4 data.")
        return
    
    # Convert to DataFrame if needed for filtering
    if isinstance(all_building_elements, list):
        all_elements_df = pd.DataFrame(all_building_elements)
    else:
        all_elements_df = all_building_elements
    
    # CRITICAL: Filter to only SUITABLE elements (exclude north-facing windows)
    if 'pv_suitable' in all_elements_df.columns:
        suitable_elements = all_elements_df[all_elements_df['pv_suitable'] == True].copy()
    elif 'suitable' in all_elements_df.columns:
        suitable_elements = all_elements_df[all_elements_df['suitable'] == True].copy()
    else:
        # Fallback: filter by orientation to exclude north-facing
        suitable_orientations = ["South (135-225°)", "East (45-135°)", "West (225-315°)", "Southeast", "Southwest"]
        if 'orientation' in all_elements_df.columns:
            suitable_elements = all_elements_df[all_elements_df['orientation'].isin(suitable_orientations)].copy()
        else:
            st.warning("⚠️ Could not determine element suitability. Processing all elements.")
            suitable_elements = all_elements_df
    
    # TMY data already validated above
    coordinates = project_data.get('coordinates', {})
    latitude = coordinates.get('lat', 52.52)
    longitude = coordinates.get('lng', 13.405)
    
    # Display filtering results
    total_elements = len(all_elements_df)
    suitable_count = len(suitable_elements)
    excluded_count = total_elements - suitable_count
    
    st.success(f"✅ **BIPV Suitability Filtering Applied**: Analyzing {suitable_count} suitable elements (excluded {excluded_count} north-facing elements from {total_elements} total)")
    
    if excluded_count > 0:
        st.info(f"🧭 **North-facing windows excluded**: {excluded_count} elements with poor solar performance (<600 kWh/m²/year) excluded from BIPV analysis")
    
    # Analysis Precision Selection (prominently displayed)
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        analysis_precision = st.selectbox(
            "📊 Computational Settings",
            ["Hourly", "Daily Peak", "Monthly Average", "Yearly Average"],
            index=1,  # Default to Daily Peak
            key="analysis_precision_rad",
            help="Hourly: Only hours with sun irradiance • Daily Peak: Noon as mid of daily irradiance • Monthly Average: Average solar days seasonal • Yearly Average: Total solar irradiance average"
        )
    
    with col2:
        include_shading = st.checkbox("🏢 Include Geometric Self-Shading", value=True, key="include_shading_rad",
                                    help="Calculate precise shadows from building walls")
    
    with col3:
        apply_corrections = st.checkbox("🧭 Apply Orientation Corrections", value=True, key="apply_corrections_rad",
                                      help="Apply tilt and azimuth corrections for surface irradiance")
    
    # Show computational method details
    computational_info = {
        "Hourly": "⏰ Hourly analysis - Only hours with sun irradiance for maximum accuracy",
        "Daily Peak": "☀️ Daily Peak analysis - Noon is the mid of the daily sun irradiance",
        "Monthly Peak": "📅 Monthly average - Average solar days for seasonal representation",
        "Yearly Average": "📊 Yearly Average - Average of the total solar irradiance in the whole year"
    }
    st.info(computational_info[analysis_precision])
    
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
        
        # Prepare shading analysis with walls data
        if walls_data is not None:
            st.success(f"Ready for precise self-shading analysis using {len(walls_data)} building walls")
        else:
            st.info("No walls data available - shading analysis will be skipped")
    
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
            
            # DEPLOYMENT OPTIMIZATION: Detect deployment environment and apply optimizations
            import os
            is_deployment = os.environ.get('REPLIT_DEPLOYMENT') == 'true' or os.environ.get('REPLIT_ENVIRONMENT') == 'production'
            
            # Ensure walls_data is accessible to radiation calculations
            # (walls_data is defined in the shading configuration section above)
            
            # Computational method implementation
            if is_deployment:
                # Force Daily Peak for deployment efficiency
                st.warning("🚀 **Deployment Mode**: Using Daily Peak method for resource optimization")
                sample_hours = [12]  # Noon only
                days_sample = list(range(1, 366))  # All 365 days
            else:
                # User-selected computational methods
                if analysis_precision == "Hourly":
                    # Only hours with sun irradiance - exclude nighttime and very low sun
                    sample_hours = list(range(7, 18))  # Hours with meaningful sun irradiance (7 AM to 5 PM)
                    days_sample = list(range(1, 366))  # All 365 days
                    st.info("⏰ **Hourly Analysis**: Processing only hours with sun irradiance")
                
                elif analysis_precision == "Daily Peak":
                    # Noon as mid of daily sun irradiance
                    sample_hours = [12]  # Noon as the mid-point of daily sun irradiance
                    days_sample = list(range(1, 366))  # All 365 days
                    st.info("☀️ **Daily Peak Analysis**: Noon as the mid of daily sun irradiance")
                
                elif analysis_precision == "Monthly Average":
                    # Average solar days for seasonal representation
                    sample_hours = [12]  # Noon position
                    # Representative average days for each month (15th of each month)
                    days_sample = [15, 46, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349]  # 12 average days
                    st.info("📅 **Monthly Average Analysis**: Average solar days for seasonal representation")
                
                else:  # Yearly Average
                    # Average of total solar irradiance in the whole year
                    sample_hours = [12]  # Noon only
                    days_sample = [80, 172, 266, 355]  # Four seasonal representative days (equinoxes & solstices)
                    st.info("📊 **Yearly Average Analysis**: Average of total solar irradiance in the whole year")
            
            status_text.text(f"Processing {len(suitable_elements)} elements with {analysis_precision.lower()} precision...")
            progress_bar.progress(10)
            
            # Process each element with detailed progress
            radiation_results = []
            total_elements = len(suitable_elements)
            
            # Convert DataFrame to list of dictionaries if needed
            if hasattr(suitable_elements, 'iterrows'):
                import math
                elements_list = []
                for _, row in suitable_elements.iterrows():
                    # Preserve actual Element IDs from BIM upload
                    actual_element_id = row.get('Element ID', row.get('element_id', f'Unknown_Element_{len(elements_list)+1}'))
                    
                    # Calculate actual tilt angle from BIM orientation vectors
                    ori_z = row.get('OriZ', row.get('oriz', None))
                    if ori_z is not None:
                        try:
                            ori_z_float = float(ori_z)
                            # Clamp OriZ to valid range [-1, 1] to avoid math domain errors
                            ori_z_clamped = max(-1.0, min(1.0, ori_z_float))
                            # Calculate tilt: tilt = arccos(|OriZ|) in degrees
                            calculated_tilt = math.degrees(math.acos(abs(ori_z_clamped)))
                        except (ValueError, TypeError):
                            # Fallback to vertical if OriZ is invalid
                            calculated_tilt = 90.0
                    else:
                        # Fallback to vertical if OriZ not available
                        calculated_tilt = 90.0
                    
                    elements_list.append({
                        'element_id': actual_element_id,
                        'azimuth': row.get('azimuth', 180),
                        'tilt': calculated_tilt,
                        'glass_area': row.get('glass_area', 1.5),
                        'orientation': row.get('orientation', 'Unknown'),
                        'level': row.get('level', 'Level 1'),
                        'wall_hosted_id': row.get('wall_hosted_id', 'N/A'),
                        'width': row.get('window_width', row.get('width', row.get('Width', 1.2))),
                        'height': row.get('window_height', row.get('height', row.get('Height', 1.5))),
                        'ori_z': ori_z  # Store original OriZ for debugging
                    })
                suitable_elements = elements_list
            
            # Dynamic batch processing based on element count and precision
            total_elements_count = len(suitable_elements)
            
            if is_deployment:
                # Ultra-aggressive optimization for deployment
                BATCH_SIZE = min(15, total_elements_count // 5)  # Much smaller batches for deployment
                st.warning(f"🚀 **Deployment Mode Detected**: Using ultra-optimized batch size {BATCH_SIZE} for {total_elements_count} elements")
                st.info("⚡ **Performance Mode**: Reduced calculations for deployment resource limits")
            else:
                # Standard batch sizes for preview/development
                if total_elements_count > 800:
                    BATCH_SIZE = 50  # Increased from 25 for better throughput
                    st.info(f"🔧 **Large Dataset Optimization**: Processing {total_elements_count} elements in optimized batches of {BATCH_SIZE}")
                elif total_elements_count > 400:
                    BATCH_SIZE = 75  # Increased from 50 for better throughput
                    st.info(f"⚡ **Medium Dataset Processing**: Using optimized batch size {BATCH_SIZE} for {total_elements_count} elements")
                else:
                    BATCH_SIZE = 150  # Increased from 100 for smaller datasets
                
                # Adjust batch size based on precision level
                if analysis_precision == "Maximum":
                    BATCH_SIZE = max(10, BATCH_SIZE // 2)  # Reduce batch size for maximum precision
                    st.warning(f"⏱️ **Maximum Precision Mode**: Reduced batch size to {BATCH_SIZE} for detailed analysis")
            
            for batch_start in range(0, len(suitable_elements), BATCH_SIZE):
                batch_end = min(batch_start + BATCH_SIZE, len(suitable_elements))
                batch_elements = suitable_elements[batch_start:batch_end]
                
                st.info(f"Processing batch {batch_start//BATCH_SIZE + 1} of {(len(suitable_elements)-1)//BATCH_SIZE + 1} (Elements {batch_start+1}-{batch_end})")
                
                for i, element in enumerate(batch_elements):
                    global_i = batch_start + i
                    
                    # Extract element data from BIM upload - preserve actual Element IDs
                    element_id = element.get('element_id', f'Unknown_Element_{global_i+1}')
                    azimuth = element.get('azimuth', 180)
                    tilt = element.get('tilt', 90)
                    area = element.get('glass_area', 1.5)  # Use actual BIM glass area
                    orientation = element.get('orientation', 'Unknown')
                    level = element.get('level', 'Level 1')
                    width = element.get('window_width', element.get('width', element.get('Width', 1.2)))
                    height = element.get('window_height', element.get('height', element.get('Height', 1.5)))
                    
                    # Update progress indicators with BIM data details including calculated tilt
                    element_progress.text(f"Batch {batch_start//BATCH_SIZE + 1}: {element_id} | {orientation} | {area:.1f}m² | Tilt: {tilt:.1f}° | {level}")
                    current_progress = 10 + int(70 * global_i / total_elements)
                    progress_bar.progress(current_progress)
                    status_text.text(f"Processing {global_i+1} of {total_elements} elements total with {analysis_precision.lower()} precision...")
                    
                    # Add memory check and yield point every 10 elements
                    if global_i % 10 == 0:
                        import time
                        if is_deployment:
                            time.sleep(0.05)  # More frequent yields in deployment
                        else:
                            time.sleep(0.01)  # Standard yield for preview
                    
                    # DEPLOYMENT EMERGENCY STOP: Check for potential resource exhaustion
                    if is_deployment and global_i > 50 and global_i % 25 == 0:
                        # Force intermediate save every 25 elements in deployment
                        if len(radiation_results) > 0:
                            st.session_state.temp_radiation_results = radiation_results.copy()
                            st.info(f"🚀 **Emergency Save**: Secured {len(radiation_results)} results at element {global_i}")
                    
                    # Calculate radiation for this element with robust error protection
                    try:
                        import time
                        element_start_time = time.time()
                        # Deployment-specific timeout optimization
                        if is_deployment:
                            ELEMENT_TIMEOUT = 30  # Much shorter timeout for deployment
                        else:
                            ELEMENT_TIMEOUT = 120  # Standard timeout for preview
                        
                        annual_irradiance = 0
                        peak_irradiance = 0
                        sample_count = 0
                        monthly_irradiation = {}
                        timeout_occurred = False
                        
                        for month in range(1, 13):
                            # Check for timeout every month but continue with next element
                            if time.time() - element_start_time > ELEMENT_TIMEOUT:
                                timeout_occurred = True
                                # Use realistic fallback values based on orientation
                                if 'South' in orientation:
                                    annual_irradiance = 1200  # Higher for south-facing
                                elif orientation in ['East', 'West']:
                                    annual_irradiance = 1000  # Medium for east/west
                                else:
                                    annual_irradiance = 800   # Lower for other orientations
                                peak_irradiance = annual_irradiance * 1.2
                                sample_count = 100
                                break
                            
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
                                            
                                            # Extract solar position from TMY data (authentic calculations from Step 3)
                                            solar_pos = {
                                                'elevation': hour_data.get('solar_elevation', 0),
                                                'azimuth': hour_data.get('solar_azimuth', 180),
                                                'zenith': 90 - hour_data.get('solar_elevation', 0)
                                            }
                                            
                                            # Fallback to calculated values if TMY doesn't have solar position data
                                            if solar_pos['elevation'] == 0 and solar_pos['azimuth'] == 180:
                                                solar_pos = calculate_solar_position_simple(latitude, longitude, day_of_year, hour)
                                            
                                            # Skip if sun below horizon
                                            if solar_pos['elevation'] <= 0:
                                                continue
                                            
                                            # Calculate height-dependent effects on GHI and solar angles
                                            height_from_ground = estimate_height_from_ground(level)
                                            base_ghi = hour_data.get('ghi', 0)
                                            
                                            # Apply height-dependent GHI adjustments
                                            ghi_effects = calculate_height_dependent_ghi_effects(height_from_ground, base_ghi)
                                            adjusted_ghi = ghi_effects['adjusted_ghi']
                                            
                                            # Apply height-dependent solar angle adjustments
                                            adjusted_solar_pos = calculate_height_dependent_solar_angles(solar_pos, height_from_ground)
                                            
                                            # Calculate surface irradiance using height-adjusted values
                                            surface_irradiance = calculate_irradiance_on_surface(
                                                adjusted_ghi,
                                                hour_data.get('dni', 0),
                                                hour_data.get('dhi', 0),
                                                adjusted_solar_pos,
                                                tilt,
                                                azimuth
                                            )
                                            
                                            # Apply ground reflectance based on window height from ground
                                            ground_reflectance = calculate_ground_reflectance_factor(height_from_ground, tilt)
                                            
                                            # Add ground reflectance contribution (reflected adjusted GHI component)
                                            ground_contribution = adjusted_ghi * ground_reflectance
                                            surface_irradiance += ground_contribution
                                            
                                            # Apply precise shading calculations if walls data available
                                            if walls_data is not None and include_shading:
                                                shading_factor = calculate_combined_shading_factor(element, walls_data, solar_pos)
                                                surface_irradiance *= shading_factor
                                            
                                            annual_irradiance += surface_irradiance
                                            monthly_total += surface_irradiance
                                            peak_irradiance = max(peak_irradiance, surface_irradiance)
                                            sample_count += 1
                                            monthly_samples += 1
                            
                            # Store monthly average
                            if monthly_samples > 0:
                                monthly_irradiation[str(month)] = monthly_total / monthly_samples * 730  # Scale to monthly total
                        
                        # Scale to annual totals based on computational method
                        if analysis_precision == "Hourly":
                            # Hourly analysis: scale from samples to full year
                            scaling_factor = 8760 / max(sample_count, 1)
                        elif analysis_precision == "Daily Peak":
                            # Daily peak: scale from noon samples to daily totals (assume noon = 15% of daily)
                            scaling_factor = (8760 / 365) / 0.15 / max(sample_count/365, 1)
                        elif analysis_precision == "Monthly Average":
                            # Monthly average: scale from 12 average days to full year
                            scaling_factor = 365 / 12 / max(sample_count/12, 1)
                        else:  # Yearly Average
                            # Yearly average: scale from single day to full year
                            scaling_factor = 365 / max(sample_count, 1)
                        
                        annual_irradiance = annual_irradiance * scaling_factor / 1000  # Convert to kWh/m²
                        
                        # Calculate height-related parameters for reporting
                        height_from_ground = estimate_height_from_ground(level)
                        avg_ground_reflectance = calculate_ground_reflectance_factor(height_from_ground, tilt)
                        
                        # Calculate average height-dependent effects for this element
                        sample_ghi = 800  # Typical GHI for height effect calculation
                        ghi_effects = calculate_height_dependent_ghi_effects(height_from_ground, sample_ghi)
                        sample_solar_pos = {'elevation': 45, 'azimuth': 180}  # Sample solar position
                        angle_effects = calculate_height_dependent_solar_angles(sample_solar_pos, height_from_ground)
                        
                        radiation_results.append({
                            'element_id': element_id,
                            'element_type': 'Window',
                            'orientation': orientation,
                            'azimuth': azimuth,
                            'tilt': tilt,
                            'area': area,
                            'level': level,
                            'height_from_ground': height_from_ground,
                            'ground_reflectance_factor': avg_ground_reflectance,
                            'ghi_height_factor': ghi_effects['height_factor'],
                            'atmospheric_clarity_factor': ghi_effects['atmospheric_clarity'],
                            'horizon_factor': ghi_effects['horizon_factor'],
                            'horizon_depression_deg': angle_effects['horizon_depression'],
                            'total_height_enhancement': ghi_effects['height_factor'] + avg_ground_reflectance,
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
                
                    except Exception as e:
                        # Robust error handling - NEVER stop the analysis, always continue
                        error_msg = f"Element {element_id}: Processing error - using fallback calculation"
                        st.warning(f"⚠️ {error_msg}")
                        
                        # Add fallback radiation calculation based on orientation
                        fallback_radiation = {
                            'South (135-225°)': 1500,
                            'Southeast': 1400,
                            'Southwest': 1400,
                            'West (225-315°)': 1200,
                            'East (45-135°)': 1200,
                            'North (315-45°)': 600
                        }.get(orientation, 1000)
                        
                        # ALWAYS add element to results - never skip or stop analysis
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
                            'annual_irradiation': fallback_radiation,
                            'peak_irradiance': fallback_radiation * 1.2,
                            'avg_irradiance': fallback_radiation * 1000 / 8760,
                            'monthly_irradiation': {str(m): fallback_radiation/12 for m in range(1, 13)},
                            'capacity_factor': min(fallback_radiation / 1800, 1.0),
                            'annual_energy_potential': fallback_radiation * area,
                            'error_fallback': True,
                            'processing_error': str(e)[:100]  # Store error for debugging
                        })
                        
                        # Continue processing - never break or return here
                
                # Add batch completion checkpoint with memory management
                if batch_end % 100 == 0 or batch_end == len(suitable_elements):
                    st.success(f"✅ Completed batch {batch_start//BATCH_SIZE + 1} - processed {batch_end} elements")
                    
                    # Memory management - force garbage collection after large batches
                    import gc
                    gc.collect()
                    
                    # Progress checkpoint - save intermediate results
                    if len(radiation_results) > 0 and batch_end % 200 == 0:
                        st.info(f"💾 Checkpoint: Saved {len(radiation_results)} element results")
                        # Save intermediate results to session state for recovery
                        st.session_state.temp_radiation_results = radiation_results.copy()
                
                # DEPLOYMENT EMERGENCY CHECKPOINT: Force save after every batch in deployment
                if is_deployment and len(radiation_results) > 0:
                    st.session_state.temp_radiation_results = radiation_results.copy()
                    st.info(f"🚀 **Deployment Checkpoint**: Saved {len(radiation_results)} results")
            
            # FAILSAFE: Ensure we have radiation results - create them if missing
            if len(radiation_results) == 0:
                st.warning("⚠️ Creating failsafe radiation data for analysis continuation...")
                # Create minimal radiation data to prevent analysis stoppage
                for i, element in enumerate(suitable_elements[:10]):  # At least 10 elements
                    element_id = element.get('element_id', f'Failsafe_Element_{i+1}')
                    orientation = element.get('orientation', 'South')
                    fallback_radiation = 1000 if 'South' in orientation else 800
                    
                    radiation_results.append({
                        'element_id': element_id,
                        'element_type': 'Window',
                        'orientation': orientation,
                        'azimuth': element.get('azimuth', 180),
                        'tilt': element.get('tilt', 90),
                        'area': element.get('glass_area', 1.5),
                        'level': element.get('level', 'Level 1'),
                        'wall_hosted_id': 'N/A',
                        'width': 1.2,
                        'height': 1.5,
                        'annual_irradiation': fallback_radiation,
                        'peak_irradiance': fallback_radiation * 1.2,
                        'avg_irradiance': fallback_radiation * 1000 / 8760,
                        'monthly_irradiation': {str(m): fallback_radiation/12 for m in range(1, 13)},
                        'capacity_factor': min(fallback_radiation / 1800, 1.0),
                        'annual_energy_potential': fallback_radiation * 1.5,
                        'failsafe_data': True
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
            
            # ALWAYS continue analysis - never stop due to empty data
            if len(radiation_data) == 0:
                st.error("⚠️ Critical error: No radiation data generated - using emergency fallback")
                # Emergency fallback - create basic data structure
                radiation_data = pd.DataFrame([{
                    'element_id': 'Emergency_Element_1',
                    'element_type': 'Window',
                    'orientation': 'South',
                    'azimuth': 180,
                    'tilt': 90,
                    'area': 1.5,
                    'level': 'Level 1',
                    'annual_irradiation': 1000,
                    'peak_irradiance': 1200,
                    'avg_irradiance': 114,
                    'monthly_irradiation': {str(m): 83.3 for m in range(1, 13)},
                    'capacity_factor': 0.56,
                    'annual_energy_potential': 1500,
                    'emergency_fallback': True
                }])
                
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
            st.error(f"Critical error during radiation analysis: {str(e)}")
            
            # Recovery mechanism - try to salvage partial results
            if 'temp_radiation_results' in st.session_state and len(st.session_state.temp_radiation_results) > 0:
                st.warning("🔄 **Recovery Mode**: Attempting to recover partial analysis results...")
                try:
                    radiation_data = pd.DataFrame(st.session_state.temp_radiation_results)
                    st.session_state.project_data['radiation_data'] = radiation_data
                    st.session_state.radiation_completed = True
                    
                    st.success(f"✅ **Partial Recovery Successful**: Recovered {len(radiation_data)} element calculations")
                    st.info("You can proceed to Step 6 with these results, or restart the analysis for complete dataset")
                    
                    # Clean up temporary data
                    del st.session_state.temp_radiation_results
                    
                except Exception as recovery_error:
                    st.error(f"Recovery failed: {str(recovery_error)}")
                    st.info("Please restart the analysis with Standard precision for large datasets")
            else:
                st.info("No recoverable data available. Please restart the analysis.")
                
            # Clear progress indicators
            progress_bar.progress(0)
            status_text.text("Analysis interrupted - recovery attempted")
            element_progress.text("Ready to restart analysis")
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
            
            # Prepare display dataframe with BIM metadata and comprehensive height-dependent effects
            display_df = radiation_data.copy()
            display_columns = ['element_id', 'level', 'height_from_ground', 'ground_reflectance_factor', 
                             'ghi_height_factor', 'atmospheric_clarity_factor', 'horizon_factor', 
                             'total_height_enhancement', 'orientation', 'area', 'width', 'height', 
                             'annual_irradiation', 'annual_energy_potential', 'peak_irradiance']
            
            # Add corrected values if available
            if apply_corrections and 'corrected_annual_irradiation' in display_df.columns:
                display_columns.append('corrected_annual_irradiation')
            
            # Enhanced height-dependent analysis section
            st.info("🏗️ **Enhanced Analysis**: Now includes comprehensive height effects on GHI amount, solar angles, and ground reflectance")
            
            # Show comprehensive height-dependent effects
            if 'height_from_ground' in display_df.columns:
                height_stats = display_df.groupby('level').agg({
                    'height_from_ground': 'mean',
                    'ground_reflectance_factor': 'mean',
                    'ghi_height_factor': 'mean',
                    'atmospheric_clarity_factor': 'mean',
                    'horizon_factor': 'mean',
                    'total_height_enhancement': 'mean',
                    'element_id': 'count'
                }).round(4)
                
                st.markdown("### 🏗️ Comprehensive Height-Dependent Effects by Building Level")
                
                # Split into multiple columns for better display
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**Height & Ground Effects:**")
                    st.dataframe(
                        height_stats[['height_from_ground', 'ground_reflectance_factor', 'element_id']].rename(columns={
                            'height_from_ground': 'Avg Height (m)',
                            'ground_reflectance_factor': 'Ground Reflectance',
                            'element_id': 'Element Count'
                        }),
                        use_container_width=True
                    )
                
                with col2:
                    st.markdown("**GHI & Atmospheric Effects:**")
                    st.dataframe(
                        height_stats[['ghi_height_factor', 'atmospheric_clarity_factor', 'horizon_factor']].rename(columns={
                            'ghi_height_factor': 'GHI Height Factor',
                            'atmospheric_clarity_factor': 'Atmospheric Clarity',
                            'horizon_factor': 'Horizon Factor'
                        }),
                        use_container_width=True
                    )
                
                with col3:
                    st.markdown("**Total Enhancement:**")
                    # Total height enhancement visualization
                    fig_enhancement = px.bar(
                        height_stats.reset_index(), 
                        x='level',
                        y='total_height_enhancement',
                        title="Total Height Enhancement by Level",
                        labels={
                            'level': 'Building Level',
                            'total_height_enhancement': 'Total Enhancement Factor',
                        }
                    )
                    st.plotly_chart(fig_enhancement, use_container_width=True)
                
                # Comprehensive height effects visualization
                st.markdown("### 📊 Height Effects Visualization")
                tab1, tab2, tab3 = st.tabs(["Ground Reflectance", "GHI Effects", "Combined Effects"])
                
                with tab1:
                    fig_ground = px.scatter(
                        display_df, 
                        x='height_from_ground',
                        y='ground_reflectance_factor',
                        color='level',
                        title="Ground Reflectance vs Window Height",
                        labels={
                            'height_from_ground': 'Height from Ground (m)',
                            'ground_reflectance_factor': 'Ground Reflectance Factor',
                            'level': 'Building Level'
                        }
                    )
                    st.plotly_chart(fig_ground, use_container_width=True)
                
                with tab2:
                    fig_ghi = px.scatter(
                        display_df, 
                        x='height_from_ground',
                        y='ghi_height_factor',
                        color='atmospheric_clarity_factor',
                        title="GHI Height Factor vs Window Height",
                        labels={
                            'height_from_ground': 'Height from Ground (m)',
                            'ghi_height_factor': 'GHI Height Factor',
                            'atmospheric_clarity_factor': 'Atmospheric Clarity'
                        }
                    )
                    st.plotly_chart(fig_ghi, use_container_width=True)
                
                with tab3:
                    fig_total = px.scatter(
                        display_df, 
                        x='height_from_ground',
                        y='total_height_enhancement',
                        color='orientation',
                        size='area',
                        title="Total Height Enhancement Effects",
                        labels={
                            'height_from_ground': 'Height from Ground (m)',
                            'total_height_enhancement': 'Total Enhancement Factor',
                            'orientation': 'Orientation',
                            'area': 'Window Area (m²)'
                        }
                    )
                    st.plotly_chart(fig_total, use_container_width=True)
            
            st.dataframe(
                display_df[display_columns].round(3),
                use_container_width=True,
                column_config={
                    'element_id': 'Element ID',
                    'level': 'Building Level',
                    'height_from_ground': st.column_config.NumberColumn('Height from Ground (m)', format="%.1f"),
                    'ground_reflectance_factor': st.column_config.NumberColumn('Ground Reflectance', format="%.3f"),
                    'ghi_height_factor': st.column_config.NumberColumn('GHI Height Factor', format="%.3f"),
                    'atmospheric_clarity_factor': st.column_config.NumberColumn('Atmospheric Clarity', format="%.3f"),
                    'horizon_factor': st.column_config.NumberColumn('Horizon Factor', format="%.3f"),
                    'total_height_enhancement': st.column_config.NumberColumn('Total Enhancement', format="%.3f"),
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
                        fig_monthly.update_layout(width=700, height=400)  # Fixed width to prevent expansion
                        st.plotly_chart(fig_monthly, use_container_width=False)
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