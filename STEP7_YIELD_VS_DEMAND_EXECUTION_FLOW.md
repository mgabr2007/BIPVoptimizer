# Step 7 Yield vs Demand Analysis: Complete Execution Flow and Mathematical Foundation

## OVERVIEW

Step 7 performs comprehensive energy balance analysis by comparing BIPV energy generation from Step 6 with building energy demand from Step 2. This analysis calculates monthly energy flows, grid interactions, financial savings, and self-consumption rates, providing the foundation for economic optimization in subsequent steps.

## EXECUTION FLOW ARCHITECTURE

### 1. MAIN EXECUTION MODULE

**File**: `pages_modules/yield_demand_modular.py`
**Primary Function**: `render_yield_demand()`

The execution follows a structured modular pipeline:

```python
def render_yield_demand():
    # Step 1: Render header and introduction
    render_step7_header()
    
    # Step 2: Validate dependencies and get project data
    project_id, project_data, validation_passed = get_validated_project_data()
    
    # Step 3: Render data usage information
    render_data_usage_info()
    
    # Step 4: Get analysis configuration from user
    config = render_analysis_configuration()
    
    # Step 5: Display environmental factors from Step 3
    environmental_factors = render_environmental_factors(project_data)
    
    # Step 6: Execute energy balance calculations
    - calculate_monthly_demand()
    - calculate_pv_yields()
    - calculate_energy_balance()
    - save_analysis_results()
    
    # Step 7: Display results and export functionality
    render_analysis_results()
    render_data_export()
```

### 2. MODULAR ARCHITECTURE COMPONENTS

**File**: `pages_modules/step7_yield_demand/`

#### A. Data Validation Module (`data_validation.py`)
- Validates project data availability
- Checks dependencies from previous steps
- Ensures data integrity before calculations

#### B. Calculation Engine (`calculation_engine.py`)
- Core energy calculations with caching
- Monthly demand modeling
- PV yield calculations
- Energy balance analysis

#### C. UI Components (`ui_components.py`)
- Streamlit interface rendering
- Configuration controls
- Results visualization
- Data export functionality

## DATA INTEGRATION AND PREREQUISITES

### 1. INPUT DATA SOURCES

#### From Step 2 (Historical Data Analysis)
- `historical_data`: Building energy consumption patterns
- Fields: `consumption_data`, `forecast_data`, `avg_monthly_consumption`
- Database table: `historical_analysis`

#### From Step 6 (BIPV Specifications)
- `pv_specifications`: Individual BIPV system specifications
- Fields: `capacity_kw`, `annual_energy_kwh`, `glass_area_m2`, `efficiency`
- Database table: `pv_specifications`

#### From Step 3 (Weather Environment)
- `tmy_data`: Typical Meteorological Year solar radiation data
- Fields: `ghi`, `dni`, `dhi` (Global, Direct, Diffuse Horizontal Irradiance)
- Environmental factors: `shading_reduction`, temperature corrections

#### From Step 1 (Project Setup)
- `electricity_rates`: Grid electricity pricing
- Fields: `import_rate` (purchase price), `export_rate` (feed-in tariff)

### 2. PREREQUISITES VALIDATION

```python
def validate_step7_dependencies(project_id):
    # Check historical data
    historical_data = db_manager.get_historical_data(project_id)
    has_historical = historical_data and historical_data.get('consumption_data')
    
    # Check PV specifications
    pv_specs = db_manager.get_pv_specifications(project_id)
    has_pv_specs = pv_specs is not None and len(pv_specs) > 0
    
    # Check TMY data
    weather_data = project_data.get('weather_analysis', {})
    has_tmy = weather_data.get('tmy_data') is not None
    
    return has_historical and has_pv_specs and has_tmy
```

## MATHEMATICAL FOUNDATIONS

### 1. MONTHLY DEMAND CALCULATION

**Function**: `calculate_monthly_demand(project_id, historical_data)`

#### A. Base Consumption Extraction
```python
# Extract historical consumption data
avg_consumption = safe_float(consumption_data.get('avg_monthly_consumption', 0))
annual_consumption = safe_float(consumption_data.get('annual_consumption', 0))
consumption_pattern = consumption_data.get('consumption_pattern', [])

# Fallback calculation if monthly average not available
if avg_consumption <= 0 and annual_consumption > 0:
    avg_consumption = annual_consumption / 12
```

#### B. Seasonal Demand Modeling
Educational buildings have distinct seasonal patterns:

```python
# Realistic seasonal factors for educational buildings
seasonal_factors = [1.1, 1.0, 0.9, 0.8, 0.7, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]
monthly_demand = [float(avg_consumption) * factor for factor in seasonal_factors]
```

**Seasonal Pattern Explanation**:
- **Winter (Dec-Feb)**: Higher consumption (heating, longer hours) - factors 1.1-1.2
- **Spring (Mar-May)**: Decreasing consumption - factors 0.8-0.9
- **Summer (Jun-Aug)**: Lowest consumption (vacation, minimal heating) - factors 0.6-0.7
- **Autumn (Sep-Nov)**: Increasing consumption (return to full operations) - factors 0.9-1.1

#### C. Demand Calculation Output
```python
return {
    'avg_consumption': avg_consumption,           # Average monthly consumption (kWh)
    'total_consumption': sum(monthly_demand),     # Annual consumption (kWh)
    'monthly_demand': monthly_demand,             # 12-month demand array (kWh)
    'is_valid': True
}
```

### 2. PV YIELD CALCULATION

**Function**: `calculate_pv_yields(project_id, pv_specs, tmy_data, environmental_factors)`

#### A. Environmental Shading Factor
```python
# Get environmental shading reduction from Step 3
shading_reduction = environmental_factors.get('shading_reduction', 0)  # Percentage
shading_factor = 1 - (shading_reduction / 100)  # Convert to multiplier
```

#### B. TMY Solar Radiation Processing
```python
# Calculate annual TMY radiation from 8760 hourly records
tmy_annual_ghi = 0
if tmy_data and len(tmy_data) > 0:
    tmy_annual_ghi = sum(
        record.get('ghi', record.get('GHI_Wm2', record.get('GHI', 0))) 
        for record in tmy_data
    ) / 1000  # Convert W/m² to kWh/m²/year
```

#### C. BIPV System Energy Calculation
**Core Energy Equation**:
```
Annual_Energy = Area × Efficiency × Solar_Radiation × Performance_Ratio × Environmental_Shading
```

**Implementation**:
```python
# System parameters from Step 6
capacity_kw = safe_float(system.get('capacity_kw', 0))
glass_area = safe_float(system.get('glass_area_m2', 1.5))
efficiency = safe_float(system.get('efficiency', 0.08))

# Performance factors
performance_ratio = 0.85  # Typical for BIPV systems (includes inverter losses, wiring, soiling)

# Solar radiation source priority
if tmy_annual_ghi > 100:  # Valid TMY data available
    annual_radiation = tmy_annual_ghi
else:
    annual_radiation = 1200  # Central Europe fallback (kWh/m²/year)

# Final energy calculation
annual_energy = glass_area * efficiency * annual_radiation * performance_ratio * shading_factor
```

#### D. Monthly Distribution Modeling
```python
# Realistic monthly solar distribution (Central Europe)
monthly_distribution = [0.03, 0.05, 0.08, 0.11, 0.14, 0.15, 0.14, 0.12, 0.09, 0.06, 0.03, 0.02]
monthly_yields = [annual_energy * factor for factor in monthly_distribution]
```

**Monthly Pattern Explanation**:
- **Winter (Dec-Feb)**: Low solar availability - 3-5% of annual
- **Spring (Mar-May)**: Increasing solar - 8-14% of annual
- **Summer (Jun-Aug)**: Peak solar season - 12-15% of annual
- **Autumn (Sep-Nov)**: Decreasing solar - 6-9% of annual

#### E. Performance Metrics
```python
# Calculate capacity if missing
if capacity_kw <= 0:
    capacity_kw = glass_area * efficiency  # Approximate capacity calculation

# Specific yield (performance indicator)
specific_yield = annual_energy / capacity_kw if capacity_kw > 0 else 0  # kWh/kW/year
```

### 3. ENERGY BALANCE CALCULATION

**Function**: `calculate_energy_balance(demand_data, yield_data, electricity_rates)`

#### A. Monthly Energy Flow Analysis
For each month, the system calculates:

```python
demand = monthly_demand[month]      # Building energy demand (kWh)
generation = monthly_yield_totals[month]  # BIPV energy generation (kWh)

# Calculate net energy flows
net_import = max(0, demand - generation)      # Grid electricity needed (kWh)
surplus_export = max(0, generation - demand) # Excess BIPV energy (kWh)
self_consumption = min(demand, generation)    # Directly used BIPV energy (kWh)
```

**Energy Flow Equations**:
```
Net_Import = max(0, Demand - Generation)
Surplus_Export = max(0, Generation - Demand)
Self_Consumption = min(Demand, Generation)
```

#### B. Self-Consumption Ratio
```python
# Self-consumption ratio (key performance indicator)
self_consumption_ratio = self_consumption / demand if demand > 0 else 0
```

**Interpretation**:
- **100%**: All demand met by BIPV (ideal scenario)
- **50-80%**: High self-consumption (good economic performance)
- **<30%**: Low self-consumption (requires grid interaction optimization)

#### C. Financial Impact Calculations

**Electricity Cost Savings**:
```
Cost_Savings = Self_Consumption × Import_Rate
```

```python
import_rate = electricity_rates.get('import_rate', 0.25)  # €/kWh
electricity_cost_savings = self_consumption * import_rate
```

**Feed-in Revenue**:
```
Feed_in_Revenue = Surplus_Export × Export_Rate
```

```python
export_rate = electricity_rates.get('export_rate', 0.08)  # €/kWh
feed_in_revenue = surplus_export * export_rate
```

**Total Monthly Savings**:
```
Monthly_Savings = Cost_Savings + Feed_in_Revenue
```

```python
monthly_savings = electricity_cost_savings + feed_in_revenue
```

#### D. Monthly Energy Balance Output
```python
month_data = {
    'month': month + 1,
    'demand_kwh': demand,
    'generation_kwh': generation,
    'net_import_kwh': net_import,
    'surplus_export_kwh': surplus_export,
    'self_consumption_kwh': self_consumption,
    'self_consumption_ratio': self_consumption_ratio,
    'electricity_cost_savings': electricity_cost_savings,
    'feed_in_revenue': feed_in_revenue,
    'total_monthly_savings': monthly_savings
}
```

### 4. ANNUAL SUMMARY CALCULATIONS

#### A. Annual Energy Metrics
```python
# Annual totals
annual_demand = sum(monthly_demand)
annual_generation = sum(monthly_yield_totals)

# Coverage ratio (key metric)
coverage_ratio = (annual_generation / annual_demand * 100) if annual_demand > 0 else 0
```

**Coverage Ratio Interpretation**:
- **>100%**: Net energy positive building (surplus generation)
- **80-100%**: High renewable coverage (minimal grid dependence)
- **50-80%**: Moderate renewable coverage (balanced grid interaction)
- **<50%**: Low renewable coverage (high grid dependence)

#### B. Annual Financial Summary
```python
# Financial totals
total_annual_savings = sum(month['total_monthly_savings'] for month in energy_balance)
total_feed_in_revenue = sum(month['feed_in_revenue'] for month in energy_balance)
average_monthly_savings = total_annual_savings / 12
```

## DATABASE INTEGRATION

### 1. RESULTS STORAGE STRUCTURE

**Primary Table**: `yield_demand_analysis`

```sql
CREATE TABLE yield_demand_analysis (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    monthly_energy_balance JSONB,     -- 12-month energy flow data
    annual_summary JSONB,             -- Annual metrics and totals
    analysis_config JSONB,            -- Analysis configuration parameters
    environmental_factors JSONB,      -- Environmental shading and corrections
    calculation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. SAVE OPERATION

**Function**: `save_analysis_results(project_id, balance_data, config)`

```python
analysis_data = {
    'monthly_energy_balance': balance_data['energy_balance'],
    'annual_summary': {
        'annual_demand': balance_data['annual_demand'],
        'annual_generation': balance_data['annual_generation'],
        'coverage_ratio': balance_data['coverage_ratio'],
        'total_annual_savings': balance_data['total_annual_savings'],
        'total_feed_in_revenue': balance_data['total_feed_in_revenue'],
        'average_monthly_savings': balance_data['average_monthly_savings']
    },
    'analysis_config': config,
    'calculation_date': datetime.now().isoformat()
}

success = db_manager.save_yield_demand_analysis(project_id, analysis_data)
```

## PERFORMANCE ANALYSIS AND VISUALIZATION

### 1. KEY PERFORMANCE INDICATORS

#### A. Energy Performance Metrics
- **Annual Coverage Ratio**: Percentage of demand met by BIPV
- **Self-Consumption Rate**: Percentage of generation used directly
- **Grid Independence**: Months with net-positive energy balance
- **Peak Generation**: Highest monthly generation output

#### B. Economic Performance Metrics
- **Annual Savings**: Total electricity cost reductions
- **Feed-in Revenue**: Income from excess energy export
- **Return on Investment**: Annual savings as percentage of BIPV investment
- **Payback Contribution**: Savings toward BIPV system payback

### 2. MONTHLY VISUALIZATION COMPONENTS

#### A. Energy Flow Charts
- Monthly demand vs generation comparison
- Net import/export visualization
- Self-consumption ratio trends

#### B. Financial Analysis Charts
- Monthly savings accumulation
- Cost savings vs feed-in revenue breakdown
- Annual savings projection

### 3. SEASONAL ANALYSIS

#### A. Winter Performance (Dec-Feb)
- Typically net import months (heating demand, low solar)
- Focus on grid electricity cost savings
- Self-consumption optimization opportunities

#### B. Summer Performance (Jun-Aug)
- Potential net export months (low demand, high solar)
- Feed-in revenue maximization
- Grid contribution and storage opportunities

## INTEGRATION WITH SUBSEQUENT STEPS

### Step 8 (Multi-Objective Optimization)

**Data Flow**:
```python
# Used for optimization objectives and constraints
coverage_ratio → Energy independence objective
total_annual_savings → Economic optimization target
self_consumption_ratio → Grid interaction optimization
monthly_energy_balance → Seasonal performance constraints
```

**Mathematical Integration**:
- NSGA-II genetic algorithm uses coverage ratio as performance objective
- Economic optimization maximizes `total_annual_savings`
- Grid interaction optimization balances self-consumption and export revenue

### Step 9 (Financial Analysis)

**Data Flow**:
```python
# Used for detailed financial modeling
total_annual_savings → Annual cash flow input
monthly_energy_balance → Monthly cash flow projections
coverage_ratio → Energy cost escalation modeling
```

**Financial Integration**:
- NPV calculations use `total_annual_savings` as annual cash flow
- IRR analysis incorporates monthly savings variability
- Sensitivity analysis uses coverage ratio for scenario modeling

### Step 10 (Comprehensive Dashboard)

**Data Flow**:
```python
# Complete dataset for performance monitoring
monthly_energy_balance → Monthly performance tracking
annual_summary → KPI dashboard display
self_consumption_ratio → Operational optimization insights
```

## QUALITY ASSURANCE AND VALIDATION

### 1. DATA VALIDATION CHECKS

```python
# Energy balance validation
if abs(demand - (net_import + self_consumption)) > 0.01:
    raise ValueError("Energy balance equation violation")

# Financial calculation validation  
if electricity_cost_savings < 0 or feed_in_revenue < 0:
    raise ValueError("Invalid financial calculations")

# Physical constraints validation
if self_consumption > min(demand, generation):
    raise ValueError("Self-consumption exceeds physical limits")
```

### 2. PERFORMANCE BENCHMARKS

- **Specific Yield Target**: >800 kWh/kW/year for viable BIPV systems
- **Self-Consumption Target**: >50% for optimal economic performance
- **Coverage Ratio Benchmark**: >30% for meaningful renewable contribution
- **Annual Savings Target**: >€500/year per 10kW capacity for economic viability

### 3. REALISTIC ASSUMPTIONS

#### A. Performance Ratio (0.85)
Accounts for:
- Inverter efficiency losses (2-5%)
- DC/AC wiring losses (2-3%)
- Soiling and dust accumulation (2-5%)
- Temperature coefficient effects (3-8%)
- Shading and orientation losses (0-10%)

#### B. Grid Interaction Modeling
- Instantaneous energy balance (no storage modeling)
- Net metering assumptions for feed-in calculations
- Time-of-use rate potential for advanced analysis

This comprehensive Step 7 execution flow provides accurate energy balance analysis that forms the critical foundation for economic optimization and financial viability assessment in the complete BIPV optimization workflow.