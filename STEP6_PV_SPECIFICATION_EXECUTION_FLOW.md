# Step 6 BIPV Panel Specifications: Complete Execution Flow and Mathematical Foundation

## OVERVIEW

Step 6 transforms solar radiation data from Step 5 into detailed BIPV (Building Integrated Photovoltaic) system specifications. It calculates capacity, energy yield, and costs for each suitable building element using commercial BIPV glass technologies, providing the foundation for optimization and financial analysis in subsequent steps.

## EXECUTION FLOW ARCHITECTURE

### 1. MAIN EXECUTION MODULE

**File**: `pages_modules/pv_specification_unified.py`
**Primary Function**: `render_pv_specification()`

The execution follows a structured pipeline:

```python
def render_pv_specification():
    # Step 1: Validate Prerequisites
    - Check project data is loaded
    - Verify radiation analysis completion (Step 5)
    - Validate building elements availability (Step 4)
    
    # Step 2: Filter Suitable Elements
    - Apply azimuth-based filtering (South/East/West facing)
    - Calculate suitability rate
    
    # Step 3: BIPV Technology Selection
    - Present commercial BIPV glass database
    - Allow customization of panel specifications
    
    # Step 4: Calculate BIPV Specifications
    - Execute unified calculation function
    - Apply standardized field names for workflow consistency
    
    # Step 5: Save Results and Visualization
    - Store results in database with standardized format
    - Generate performance analysis and charts
    - Prepare data for subsequent workflow steps
```

### 2. DATA INTEGRATION AND PREREQUISITES

#### Input Data Sources

**From Step 5 (Radiation Analysis)**:
- `radiation_analysis_data`: Element-specific annual radiation values (kWh/m²/year)
- `element_radiation[]`: Individual element radiation records
- Database table: `element_radiation`

**From Step 4 (Facade Extraction)**:
- `building_elements`: Window geometry and orientation data
- Fields: `element_id`, `glass_area`, `orientation`, `azimuth`
- Database table: `building_elements`

**From Step 1 (Project Setup)**:
- `project_id`: Current project identifier
- Database table: `projects`

#### Prerequisites Validation

```python
# Check radiation analysis completion
radiation_analysis_data = db_manager.get_radiation_analysis_data(project_id)
if not radiation_analysis_data or len(radiation_analysis_data.get('element_radiation', [])) == 0:
    st.error("No radiation analysis found. Please complete Step 5 first.")
    return

# Check building elements availability
building_elements = db_manager.get_building_elements(project_id)
if not building_elements or len(building_elements) == 0:
    st.error("No building elements found. Please complete Step 4 first.")
    return
```

## BIPV TECHNOLOGY DATABASE

### 1. COMMERCIAL BIPV GLASS SPECIFICATIONS

**Function**: `get_bipv_panel_database()`

The system includes 5 verified commercial BIPV glass technologies:

#### Heliatek HeliaSol (Organic Photovoltaic)
```python
'Heliatek HeliaSol': {
    'efficiency': 0.089,      # 8.9% solar conversion efficiency
    'transparency': 0.15,     # 15% visible light transmission
    'power_density': 85,      # 85 W/m² under STC
    'cost_per_m2': 350,      # €350/m² material cost
    'thickness_mm': 5.8,     # 5.8mm glass thickness
    'u_value': 1.1,          # 1.1 W/m²K thermal transmittance
    'description': 'Ultra-light OPV film with excellent low-light performance'
}
```

#### SUNOVATION eFORM (Crystalline Silicon)
```python
'SUNOVATION eFORM': {
    'efficiency': 0.12,       # 12% solar conversion efficiency
    'transparency': 0.20,     # 20% visible light transmission
    'power_density': 120,     # 120 W/m² under STC
    'cost_per_m2': 380,      # €380/m² material cost
    'thickness_mm': 8.0,     # 8.0mm glass thickness
    'u_value': 1.0,          # 1.0 W/m²K thermal transmittance
    'description': 'Crystalline silicon with customizable transparency'
}
```

#### Solarnova SOL_GT (Thin-Film)
```python
'Solarnova SOL_GT': {
    'efficiency': 0.15,       # 15% solar conversion efficiency
    'transparency': 0.25,     # 25% visible light transmission
    'power_density': 150,     # 150 W/m² under STC
    'cost_per_m2': 420,      # €420/m² material cost
    'thickness_mm': 10.0,    # 10.0mm glass thickness
    'u_value': 0.9,          # 0.9 W/m²K thermal transmittance
    'description': 'High-efficiency thin-film with architectural integration'
}
```

#### Solarwatt Vision AM (Premium Crystalline)
```python
'Solarwatt Vision AM': {
    'efficiency': 0.19,       # 19% solar conversion efficiency
    'transparency': 0.30,     # 30% visible light transmission
    'power_density': 190,     # 190 W/m² under STC
    'cost_per_m2': 480,      # €480/m² material cost
    'thickness_mm': 12.0,    # 12.0mm glass thickness
    'u_value': 0.8,          # 0.8 W/m²K thermal transmittance
    'description': 'Premium efficiency with maximum transparency'
}
```

#### Onyx Solar Custom (Customizable)
```python
'Onyx Solar Custom': {
    'efficiency': 0.165,      # 16.5% solar conversion efficiency
    'transparency': 0.35,     # 35% visible light transmission
    'power_density': 165,     # 165 W/m² under STC
    'cost_per_m2': 450,      # €450/m² material cost
    'thickness_mm': 9.0,     # 9.0mm glass thickness
    'u_value': 0.85,         # 0.85 W/m²K thermal transmittance
    'description': 'Balanced performance with high customization options'
}
```

### 2. PANEL CUSTOMIZATION

Users can customize any technology with:
- **Efficiency**: 2% - 25% range
- **Transparency**: 10% - 50% range  
- **Cost**: €150 - €600/m² range

Custom power density calculation:
```python
custom_power_density = custom_efficiency_percent * 10  # Approximate W/m²
```

## MATHEMATICAL FOUNDATIONS

### 1. ELEMENT SUITABILITY FILTERING

#### Azimuth-Based Filtering
Only elements with favorable solar orientations are included:

```python
def filter_suitable_elements(building_elements):
    suitable_orientations = ['South', 'East', 'West', 'SE', 'SW', 'NE', 'NW']
    
    suitable_elements = []
    for element in building_elements:
        orientation = element.get('orientation', 'Unknown')
        
        # Calculate azimuth if not available
        if 'azimuth' not in element:
            element_id = str(element.get('element_id', ''))
            element_hash = abs(hash(element_id)) % 360
            element['azimuth'] = element_hash
        
        # Filter by orientation
        if orientation in suitable_orientations:
            suitable_elements.append(element)
    
    return suitable_elements
```

### 2. BIPV SYSTEM CALCULATIONS

**Primary Function**: `calculate_unified_bipv_specifications()`

For each suitable building element, the system calculates:

#### A. BIPV Area Calculation
```
BIPV_Area = Glass_Area × Coverage_Factor
```

**Implementation**:
```python
bipv_area = float(glass_area) * float(coverage_factor)
```

Where:
- `glass_area`: Total window area (m²) from Step 4
- `coverage_factor`: Fraction covered by BIPV glass (0.60-0.95, default 0.85)

#### B. System Capacity Calculation
```
Capacity_kW = BIPV_Area × Power_Density / 1000
```

**Implementation**:
```python
capacity_kw = float(bipv_area) * float(panel_specs['power_density']) / 1000.0
```

Where:
- `bipv_area`: Effective BIPV area (m²)
- `power_density`: Panel power density (W/m²) under Standard Test Conditions
- Division by 1000 converts W to kW

#### C. Specific Yield Calculation
```
Specific_Yield_kWh/m² = Annual_Radiation × Panel_Efficiency
```

**Implementation**:
```python
specific_yield_kwh_m2 = float(annual_radiation) * float(panel_specs['efficiency'])
```

Where:
- `annual_radiation`: Solar radiation from Step 5 (kWh/m²/year)
- `panel_efficiency`: BIPV glass conversion efficiency (decimal, e.g., 0.12 for 12%)

#### D. Annual Energy Generation
```
Annual_Energy_kWh = BIPV_Area × Specific_Yield_kWh/m²
```

**Implementation**:
```python
annual_energy_kwh = float(bipv_area) * float(specific_yield_kwh_m2)
```

This equation combines:
- Physical area available for BIPV installation
- Site-specific solar radiation (from Step 5 analysis)
- Technology-specific conversion efficiency

#### E. Investment Cost Calculation
```
Total_Cost_EUR = BIPV_Area × Cost_per_m²
```

**Implementation**:
```python
total_cost_eur = float(bipv_area) * float(panel_specs['cost_per_m2'])
```

#### F. Performance Metrics
```
Specific_Yield_kWh/kW = Annual_Energy_kWh / Capacity_kW
Cost_per_kW_EUR = Total_Cost_EUR / Capacity_kW
```

**Implementation**:
```python
specific_yield_kwh_kw = annual_energy_kwh / capacity_kw if capacity_kw > 0 else 0
cost_per_kw_eur = total_cost_eur / capacity_kw if capacity_kw > 0 else 0
```

## STANDARDIZED DATA OUTPUT

### 1. FIELD STANDARDIZATION

The system uses standardized field names for consistent workflow integration:

```python
STANDARD_FIELD_NAMES = {
    'element_id': 'element_id',
    'capacity_kw': 'capacity_kw', 
    'annual_energy_kwh': 'annual_energy_kwh',
    'total_cost_eur': 'total_cost_eur',
    'glass_area_m2': 'glass_area_m2',
    'orientation': 'orientation',
    'efficiency': 'efficiency',
    'transparency': 'transparency',
    'specific_yield_kwh_kw': 'specific_yield_kwh_kw',
    'power_density_w_m2': 'power_density_w_m2'
}
```

### 2. OUTPUT DATA STRUCTURE

Each element specification contains:

```python
bipv_spec = {
    'element_id': element_id,                    # Unique element identifier
    'capacity_kw': capacity_kw,                  # System capacity (kW)
    'annual_energy_kwh': annual_energy_kwh,      # Annual generation (kWh)
    'total_cost_eur': total_cost_eur,           # Total investment (EUR)
    'glass_area_m2': glass_area,                # Window area (m²)
    'orientation': orientation,                  # Building orientation
    'efficiency': panel_specs['efficiency'],     # Panel efficiency (decimal)
    'transparency': panel_specs['transparency'], # Glass transparency (decimal)
    'specific_yield_kwh_kw': specific_yield,    # Performance ratio (kWh/kW)
    'power_density_w_m2': power_density,       # Power density (W/m²)
    'bipv_area_m2': bipv_area,                 # Effective BIPV area (m²)
    'azimuth': azimuth,                        # Surface azimuth (degrees)
    'annual_radiation_kwh_m2': annual_radiation, # Solar radiation (kWh/m²/year)
    'coverage_factor': coverage_factor,         # Coverage factor (decimal)
    'panel_technology': technology_name,        # BIPV technology used
    'cost_per_kw_eur': cost_per_kw             # Cost per capacity (EUR/kW)
}
```

## DATABASE INTEGRATION

### 1. STORAGE STRUCTURE

**Primary Table**: `pv_specifications`

```sql
CREATE TABLE pv_specifications (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    bipv_specifications JSONB,     -- Individual element specifications
    panel_specs JSONB,             -- Selected panel technology details
    coverage_factor DECIMAL(3,2),  -- Glass coverage factor
    technology_used VARCHAR(100),  -- BIPV technology name
    total_elements INTEGER,        -- Number of elements processed
    calculation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. SAVE OPERATION

```python
pv_data = {
    'bipv_specifications': bipv_specifications.to_dict('records'),
    'panel_specs': {
        'efficiency': panel_specs['efficiency'],
        'transparency': panel_specs['transparency'], 
        'cost_per_m2': panel_specs['cost_per_m2'],
        'power_density': panel_specs['power_density'],
        'panel_type': panel_specs.get('technology_name', selected_panel),
        'installation_factor': 1.2  # Default installation factor
    },
    'coverage_factor': coverage_factor,
    'technology_used': panel_specs['technology_name'],
    'calculation_date': datetime.now().isoformat(),
    'total_elements': len(bipv_specifications)
}

save_result = db_manager.save_pv_specifications(project_id, pv_data)
```

## PERFORMANCE ANALYSIS AND VISUALIZATION

### 1. SYSTEM SUMMARY METRICS

The system calculates and displays key performance indicators:

```python
# Total system metrics
total_capacity = bipv_specifications[STANDARD_FIELD_NAMES['capacity_kw']].sum()
total_area = bipv_specifications[STANDARD_FIELD_NAMES['glass_area_m2']].sum()
total_energy = bipv_specifications[STANDARD_FIELD_NAMES['annual_energy_kwh']].sum()
total_cost = bipv_specifications[STANDARD_FIELD_NAMES['total_cost_eur']].sum()

# Performance ratios
avg_specific_yield = total_energy / total_capacity if total_capacity > 0 else 0
avg_cost_per_kw = total_cost / total_capacity if total_capacity > 0 else 0
system_capacity_factor = total_capacity / (total_area * panel_power_density / 1000)
```

### 2. ORIENTATION-BASED ANALYSIS

Performance analysis by building orientation:

```python
orientation_performance = bipv_specifications.groupby(STANDARD_FIELD_NAMES['orientation']).agg({
    STANDARD_FIELD_NAMES['capacity_kw']: 'sum',
    STANDARD_FIELD_NAMES['annual_energy_kwh']: 'sum',
    STANDARD_FIELD_NAMES['total_cost_eur']: 'sum'
}).reset_index()
```

### 3. VISUALIZATION COMPONENTS

- **Capacity Distribution**: Bar chart showing BIPV capacity by orientation
- **Performance Matrix**: Individual element specifications table
- **Cost Analysis**: Investment distribution across elements
- **Energy Yield**: Annual generation projections

## INTEGRATION WITH SUBSEQUENT STEPS

### Step 7 (Yield vs Demand Analysis)

**Data Flow**:
```python
# Used for energy generation modeling
capacity_kw → Hourly generation calculations
annual_energy_kwh → Annual energy balance
element_id → Individual system tracking
```

**Mathematical Integration**:
- Hourly generation profiles use `capacity_kw` and radiation data
- Grid interaction analysis uses `annual_energy_kwh` projections
- Element-specific tracking maintains data granularity

### Step 8 (Multi-Objective Optimization)

**Data Flow**:
```python
# Used for optimization constraints and objectives
total_cost_eur → Investment budget constraints
capacity_kw → Power generation objectives
specific_yield_kwh_kw → Performance criteria
```

**Optimization Integration**:
- NSGA-II genetic algorithm uses cost and capacity as objectives
- High-performing elements (specific yield > 1200 kWh/kW) weighted favorably
- Investment constraints based on total system cost

### Step 9 (Financial Analysis)

**Data Flow**:
```python
# Used for economic modeling
total_cost_eur → Initial investment (CAPEX)
annual_energy_kwh → Revenue generation basis
cost_per_kw_eur → Benchmark cost analysis
```

**Financial Integration**:
- NPV calculations use `total_cost_eur` as initial investment
- IRR analysis uses `annual_energy_kwh` for revenue projections
- Payback period calculations combine cost and energy data

### Step 10 (Comprehensive Dashboard)

**Data Flow**:
```python
# Complete dataset for reporting
All standardized fields → Performance dashboards
orientation → Geographic analysis
panel_technology → Technology comparison
```

## QUALITY ASSURANCE AND VALIDATION

### 1. DATA VALIDATION

```python
# Ensure all numeric values are valid
capacity_kw = max(0, float(capacity_kw))  # Non-negative capacity
annual_energy_kwh = max(0, float(annual_energy_kwh))  # Non-negative energy
total_cost_eur = max(0, float(total_cost_eur))  # Non-negative cost

# Validate physical constraints
if capacity_kw > 0:
    specific_yield = annual_energy_kwh / capacity_kw
    if specific_yield > 2000:  # Sanity check: <2000 kWh/kW/year
        st.warning(f"High specific yield detected: {specific_yield:.0f} kWh/kW")
```

### 2. TECHNOLOGY CONSTRAINTS

- **Efficiency Range**: 2% - 25% (physical limits of current BIPV technology)
- **Transparency Range**: 10% - 50% (architectural and performance balance)
- **Cost Range**: €150 - €600/m² (market-based pricing)
- **Coverage Factor**: 60% - 95% (accounting for frames and mounting)

### 3. PERFORMANCE BENCHMARKS

- **Specific Yield Target**: >1000 kWh/kW/year for viable BIPV systems
- **Cost Benchmark**: <€3000/kW for competitive BIPV installations
- **Efficiency Target**: >10% for commercial viability
- **Capacity Factor**: 10-15% typical for vertical BIPV installations

This comprehensive Step 6 execution flow ensures accurate BIPV system specifications that seamlessly integrate with the complete BIPV optimization workflow, providing the foundation for realistic energy modeling, optimization, and financial analysis in subsequent steps.