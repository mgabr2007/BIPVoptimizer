# Step 5 Radiation Analysis: Complete Execution Flow and Mathematical Foundation

## OVERVIEW

Step 5 serves as the computational core of the BIPV Optimizer, transforming TMY weather data and building geometry into precise solar radiation calculations for each window element. This analysis determines BIPV suitability and forms the foundation for energy yield calculations in subsequent steps.

## EXECUTION FLOW ARCHITECTURE

### 1. MAIN EXECUTION ORCHESTRATOR

**File**: `services/step5_execution_flow.py`
**Class**: `Step5ExecutionFlow`

The execution flow follows a structured pipeline:

```python
def run_complete_analysis(self, project_id: int, analysis_config: Dict[str, Any]):
    # Step 1: Validate Prerequisites
    validation = self.validate_prerequisites(project_id)
    
    # Step 2: Clear Previous Analysis
    self.clear_previous_analysis(project_id)
    
    # Step 3: Execute Analysis (3 engines available)
    if analysis_type == 'ultra_fast':
        results = self.execute_ultra_fast_analysis(project_id, config)
    elif analysis_type == 'optimized':
        results = self.execute_optimized_analysis(project_id, config)
    else:
        results = self.execute_advanced_analysis(project_id, config)
    
    # Step 4: Save Results and Update Session State
    self.save_results_to_database(project_id, results)
    self.update_session_state(project_id, results)
```

### 2. THREE ANALYSIS ENGINES

#### Ultra-Fast Engine (10-15 seconds)
**File**: `services/ultra_fast_radiation_analyzer.py`
- **Purpose**: Rapid analysis for initial assessments
- **Method**: Pre-loads all data to eliminate database bottlenecks
- **Optimization**: Reduces 2,277 database calls to 3 batch queries
- **Target**: Simple mode processing in 10-15 seconds

#### Optimized Engine (3-5 minutes)
**File**: `services/optimized_radiation_analyzer.py`
- **Purpose**: Balanced speed and accuracy for production use
- **Method**: Vectorized calculations with batch processing
- **Features**: Supports all precision levels (Hourly, Daily Peak, Monthly, Yearly)
- **Performance**: Reduces processing from 2+ hours to 3-5 minutes

#### Advanced Engine (Research Grade)
**File**: `services/advanced_radiation_analyzer.py`
- **Purpose**: Maximum accuracy for research applications
- **Method**: Sophisticated calculations with environmental factors
- **Features**: Height-dependent effects, ground reflectance, atmospheric clarity

## MATHEMATICAL FOUNDATIONS

### 1. SOLAR POSITION CALCULATIONS

#### Solar Declination Angle
```
δ = 23.45° × sin(360° × (284 + day_of_year) / 365°)
```

**Implementation** (`core/solar_math.py`):
```python
def calculate_solar_position(latitude: float, longitude: float, timestamp: datetime):
    # Convert to radians
    lat_rad = math.radians(latitude)
    
    # Day of year
    day_of_year = timestamp.timetuple().tm_yday
    
    # Solar declination angle
    declination = math.radians(23.45 * math.sin(math.radians(360 * (284 + day_of_year) / 365)))
```

#### Solar Elevation Angle
```
α = arcsin(sin(δ) × sin(φ) + cos(δ) × cos(φ) × cos(h))
```

Where:
- φ = latitude (radians)
- h = hour angle (radians)
- δ = declination angle (radians)

**Implementation**:
```python
# Solar elevation
elevation_rad = math.asin(
    math.sin(declination) * math.sin(lat_rad) + 
    math.cos(declination) * math.cos(lat_rad) * math.cos(hour_angle)
)
elevation = math.degrees(elevation_rad)
```

#### Solar Azimuth Angle
```
γ = arctan2(sin(h), cos(h) × sin(φ) - tan(δ) × cos(φ)) + 180°
```

**Implementation**:
```python
# Solar azimuth
azimuth_rad = math.atan2(
    math.sin(hour_angle),
    math.cos(hour_angle) * math.sin(lat_rad) - math.tan(declination) * math.cos(lat_rad)
)
azimuth = math.degrees(azimuth_rad) + 180  # Convert from south = 0 to north = 0
```

#### Hour Angle Calculation
```
h = 15° × (solar_time - 12)
solar_time = local_time + 4 × (longitude - time_zone_meridian) / 60
```

### 2. SURFACE IRRADIANCE MODELS

#### Angle of Incidence (Vertical Surfaces)
```
cos(θ) = sin(Z) × sin(β) × cos(γ_s - γ_surf) + cos(Z) × cos(β)
```

Where:
- Z = solar zenith angle (90° - elevation)
- β = surface tilt angle (90° for windows)
- γ_s = solar azimuth
- γ_surf = surface azimuth

#### Simple Mode (DNI-only)
```
POA_simple = DNI × cos(θ)
```

**Used for**: Ultra-fast analysis mode with 5-15% lower accuracy but 3x faster processing.

#### Advanced Mode (Three-Component Model)
```
POA_total = POA_direct + POA_diffuse + POA_reflected

POA_direct = DNI × cos(θ)
POA_diffuse = DHI × (1 + cos(β)) / 2
POA_reflected = GHI × ρ × (1 - cos(β)) / 2
```

Where:
- ρ = ground albedo (0.2 typical)
- β = surface tilt angle

### 3. PRECISION SCALING FACTORS

#### Temporal Scaling to Annual Values
Different precision levels use different calculation frequencies:

- **Hourly (4,015 calculations)**: scaling_factor = 1.0
- **Daily Peak (365 calculations)**: scaling_factor = 8.0 (average daylight hours)
- **Monthly (12 calculations)**: scaling_factor = 8.0 × 30.4 (days/month)
- **Yearly (4 calculations)**: scaling_factor = 8.0 × 91.25 (days/season)

#### Annual Radiation Conversion
```
Annual_Radiation = (total_irradiance × scaling_factor) / 1000  // Wh to kWh
```

**Implementation**:
```python
# Convert to annual radiation (kWh/m²/year)
annual_radiation = (total_irradiance * scaling_factor) / 1000
```

## DATA FLOW AND INTEGRATION

### 1. INPUT DATA SOURCES

#### From Step 3 (Weather Environment)
- **TMY Data**: 8,760 hourly records with GHI, DNI, DHI fields
- **Database Location**: `weather_analysis.tmy_data`
- **Field Mapping**: Supports multiple naming conventions
- **Quality Validation**: Physical limits and completeness checks

#### From Step 4 (Facade Extraction)
- **Window Elements**: element_id, azimuth, glass_area, orientation
- **Database Table**: `building_elements`
- **Wall Geometry**: height, area, orientation for self-shading
- **Database Table**: `building_walls`

#### From Step 1 (Project Setup)
- **Location Data**: latitude, longitude, timezone
- **Database Table**: `projects`

### 2. PROCESSING PIPELINE

#### Step A: Data Validation
```python
def validate_prerequisites(self, project_id: int):
    # Check building elements
    cursor.execute("""
        SELECT COUNT(*) as count,
               COUNT(CASE WHEN orientation IN ('South', 'East', 'West', 'SE', 'SW') THEN 1 END) as suitable
        FROM building_elements 
        WHERE project_id = %s
    """, (project_id,))
    
    # Check TMY data availability
    cursor.execute("""
        SELECT tmy_data FROM weather_analysis 
        WHERE project_id = %s AND tmy_data IS NOT NULL
    """, (project_id,))
```

#### Step B: Time Series Generation
Based on precision level, different time series are generated:

**Hourly Mode**:
```python
def _generate_hourly_timestamps(self):
    # 4,015 daylight hours (11 hours × 365 days)
    return [(month, day, hour) for month in range(1,13) 
            for day in range(1, days_in_month+1) 
            for hour in range(6, 17)]  # 6 AM to 5 PM
```

**Daily Peak Mode**:
```python
def _generate_daily_peak_timestamps(self):
    # 365 noon calculations
    return [(month, day, 12) for month in range(1,13) 
            for day in range(1, days_in_month+1)]
```

#### Step C: Solar Calculations Loop
For each element and each time step:

```python
for element in suitable_elements:
    element_azimuth = element['azimuth']
    element_radiation = 0
    
    for timestamp in time_steps:
        # 1. Calculate solar position
        solar_elevation, solar_azimuth = calculate_solar_position(
            latitude, longitude, timestamp
        )
        
        # 2. Calculate angle of incidence
        angle_of_incidence = calculate_angle_of_incidence(
            solar_elevation, solar_azimuth, element_azimuth
        )
        
        # 3. Get weather data for this timestamp
        weather_record = get_weather_data(timestamp)
        ghi = weather_record['ghi']
        dni = weather_record['dni']
        dhi = weather_record['dhi']
        
        # 4. Calculate plane-of-array irradiance
        if calculation_mode == "simple":
            poa_irradiance = dni * math.cos(math.radians(angle_of_incidence))
        else:  # advanced mode
            poa_direct = dni * math.cos(math.radians(angle_of_incidence))
            poa_diffuse = dhi * (1 + math.cos(math.radians(90))) / 2
            poa_reflected = ghi * 0.2 * (1 - math.cos(math.radians(90))) / 2
            poa_irradiance = poa_direct + poa_diffuse + poa_reflected
        
        # 5. Apply shading factor if available
        if include_shading:
            shading_factor = calculate_shading_factor(element, wall_data, solar_position)
            poa_irradiance *= shading_factor
        
        # 6. Apply orientation correction
        if apply_corrections:
            orientation_multiplier = get_orientation_correction(element['orientation'])
            poa_irradiance *= orientation_multiplier
        
        element_radiation += poa_irradiance
    
    # 7. Convert to annual radiation
    annual_radiation = (element_radiation * scaling_factor) / 1000
    results[element['element_id']] = annual_radiation
```

### 3. SHADING CALCULATIONS

#### Geometric Self-Shading
When wall data is available, the system calculates shading from building geometry:

```python
def calculate_shading_factor(element, wall_data, solar_position):
    """Calculate shading factor from building walls"""
    
    shading_factor = 1.0  # No shading initially
    
    for wall in wall_data:
        # Check if wall can cast shadow on element
        if wall_can_shade_element(wall, element, solar_position):
            # Calculate shadow geometry
            shadow_coverage = calculate_shadow_coverage(wall, element, solar_position)
            shading_factor *= (1.0 - shadow_coverage)
    
    return max(0.0, shading_factor)  # Ensure non-negative
```

### 4. PERFORMANCE OPTIMIZATIONS

#### Database Optimization
**Ultra-Fast Mode**:
- Pre-loads all data in single query
- Eliminates 2,277 individual database calls
- Uses vectorized numpy operations

**Optimized Mode**:
- Batch processing of elements
- Cached weather data lookup
- Vectorized solar position calculations

#### Memory Management
```python
# Batch processing to manage memory
batch_size = 50 if calculation_mode == "advanced" else 100
for i in range(0, len(suitable_elements), batch_size):
    batch = suitable_elements[i:i+batch_size]
    process_element_batch(batch, weather_data, time_steps)
```

## RESULTS PROCESSING AND STORAGE

### 1. DATABASE STORAGE

#### Radiation Analysis Table
```sql
CREATE TABLE radiation_analysis (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    total_elements INTEGER,
    avg_irradiance DECIMAL(10,2),
    peak_irradiance DECIMAL(10,2),
    analysis_complete BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Element Radiation Table
```sql
CREATE TABLE element_radiation (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    element_id VARCHAR(100),
    annual_radiation DECIMAL(10,2),
    irradiance DECIMAL(10,2),
    orientation_multiplier DECIMAL(5,2),
    calculation_method VARCHAR(50),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. SESSION STATE MANAGEMENT

```python
def update_session_state(self, project_id: int, results: Dict[str, Any]):
    """Update Streamlit session state with results"""
    if 'project_data' not in st.session_state:
        st.session_state.project_data = {}
    
    # Save radiation data
    analysis_results = results['results']
    st.session_state.project_data['radiation_data'] = analysis_results.get('element_radiation', {})
    st.session_state.radiation_completed = True
    st.session_state.step5_completed = True
    
    # Save performance metrics
    st.session_state.radiation_performance = results.get('performance_metrics', {})
```

### 3. RESULTS VISUALIZATION

The system provides comprehensive visualization of results:

#### Performance Matrix
- Total elements analyzed
- Completion rate
- Processing time and speed
- Radiation statistics (min, max, average)

#### Suitability Categories
- **Excellent (>1200 kWh/m²/year)**: Prime BIPV candidates
- **Good (800-1200 kWh/m²/year)**: Suitable for BIPV
- **Poor (<800 kWh/m²/year)**: Not recommended

#### Orientation Analysis
- Average radiation by building orientation
- Element count per orientation
- Performance comparison

## INTEGRATION WITH SUBSEQUENT STEPS

### Step 6 (BIPV Specification)
- Annual radiation values determine PV panel suitability
- Elements with >800 kWh/m²/year prioritized for BIPV installation
- Radiation data feeds into energy yield calculations

### Step 7 (Yield vs Demand)
- Monthly radiation profiles calculate seasonal energy generation
- Shading factors adjust realistic energy output
- Building-specific radiation data ensures accurate energy balance

### Step 8 (Optimization)
- High-radiation elements weighted favorably in genetic algorithms
- Orientation-specific performance influences optimal BIPV selection
- Cost-benefit analysis uses actual radiation for ROI calculations

This comprehensive execution flow ensures accurate, efficient, and scalable radiation analysis that forms the foundation for the entire BIPV optimization process.