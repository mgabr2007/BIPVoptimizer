# BIPV Optimizer: Complete Technical Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [Mathematical Models & Equations](#mathematical-models--equations)
4. [Workflow Steps Documentation](#workflow-steps-documentation)
5. [Input Parameters Reference](#input-parameters-reference)
6. [Database Schema](#database-schema)
7. [API Integration](#api-integration)
8. [Installation & Deployment](#installation--deployment)

---

## 1. Introduction

### 1.1 Purpose
The BIPV (Building-Integrated Photovoltaics) Optimizer is a comprehensive platform for analyzing and optimizing photovoltaic system installations on building facades and windows. The system specializes in **semi-transparent PV glass replacement** where conventional window glass is substituted with energy-generating photovoltaic panels.

### 1.2 Target Applications
- Educational buildings (K-12 schools, universities)
- Commercial office buildings
- Research facilities and libraries
- Institutional buildings with significant glazed areas

### 1.3 Key Features
- **BIM Integration**: Direct import of building element data from Revit models
- **Weather Integration**: Real-time weather data via OpenWeatherMap API
- **Advanced Solar Modeling**: ISO-compliant solar position and irradiance calculations
- **Multi-Objective Optimization**: Genetic algorithm-based optimization (NSGA-II)
- **Financial Analysis**: Comprehensive economic modeling with NPV, IRR, and payback calculations
- **3D Visualization**: Interactive building and PV system visualization

---

## 2. System Architecture

### 2.1 Frontend Architecture
- **Framework**: Streamlit with wide layout configuration
- **Components**: Modular page structure with dynamic workflow visualization
- **State Management**: Session-based state persistence with PostgreSQL database integration
- **Visualization**: Plotly for interactive charts and 3D building models

### 2.2 Backend Architecture
- **Database**: PostgreSQL with comprehensive schema for project data persistence
- **Weather Service**: OpenWeatherMap API integration for TMY data generation
- **Optimization Engine**: DEAP (Distributed Evolutionary Algorithms in Python)
- **Solar Calculations**: pvlib for accurate solar position and irradiance modeling

---

## 3. Mathematical Models & Equations

### 3.1 Solar Position Calculations

#### Solar Declination Angle
```
δ = 23.45° × sin(360° × (284 + n) / 365)
```
Where:
- δ = Solar declination angle (degrees)
- n = Day of year (1-365)

#### Hour Angle
```
ω = 15° × (t - 12)
```
Where:
- ω = Hour angle (degrees)
- t = Solar time (hours)

#### Solar Elevation Angle
```
α = arcsin(sin(φ) × sin(δ) + cos(φ) × cos(δ) × cos(ω))
```
Where:
- α = Solar elevation angle (degrees)
- φ = Latitude (degrees)
- δ = Solar declination angle (degrees)
- ω = Hour angle (degrees)

#### Solar Azimuth Angle
```
γ = arccos((sin(δ) × cos(φ) - cos(δ) × sin(φ) × cos(ω)) / cos(α))
```
Where:
- γ = Solar azimuth angle (degrees)

### 3.2 Irradiance on Tilted Surfaces

#### Direct Normal Irradiance on Tilted Surface
```
Ib,t = Ib × cos(θ)
```
Where:
- Ib,t = Direct irradiance on tilted surface (W/m²)
- Ib = Direct normal irradiance (W/m²)
- θ = Angle of incidence (degrees)

#### Angle of Incidence
```
cos(θ) = sin(α) × cos(β) + cos(α) × sin(β) × cos(γ - γs)
```
Where:
- θ = Angle of incidence (degrees)
- α = Solar elevation angle (degrees)
- β = Surface tilt angle (degrees)
- γ = Solar azimuth angle (degrees)
- γs = Surface azimuth angle (degrees)

#### Diffuse Irradiance on Tilted Surface (Hay-Davies Model)
```
Id,t = Id × [f × Rb + (1 - f) × (1 + cos(β))/2 × (1 + √(Ib/I) × sin³(β/2))]
```
Where:
- Id,t = Diffuse irradiance on tilted surface (W/m²)
- Id = Horizontal diffuse irradiance (W/m²)
- f = Modulating factor for circumsolar diffuse irradiance
- Rb = Geometric factor for beam radiation
- β = Surface tilt angle (degrees)
- I = Global horizontal irradiance (W/m²)

### 3.3 PV Energy Yield Calculations

#### PV Module Power Output
```
P = η × A × G × (1 - γ × (Tc - 25))
```
Where:
- P = Power output (W)
- η = Module efficiency (%)
- A = Module area (m²)
- G = Solar irradiance (W/m²)
- γ = Temperature coefficient (%/°C)
- Tc = Cell temperature (°C)

#### Cell Temperature
```
Tc = Ta + (NOCT - 20) × G / 800
```
Where:
- Tc = Cell temperature (°C)
- Ta = Ambient temperature (°C)
- NOCT = Nominal Operating Cell Temperature (°C)
- G = Solar irradiance (W/m²)

#### Annual Energy Yield
```
E_annual = Σ(P(t) × Δt) / 1000
```
Where:
- E_annual = Annual energy yield (kWh)
- P(t) = Instantaneous power output (W)
- Δt = Time interval (hours)

### 3.4 BIPV-Specific Calculations

#### Semi-Transparent Module Efficiency
```
η_BIPV = η_opaque × (1 - VLT)
```
Where:
- η_BIPV = BIPV module efficiency (%)
- η_opaque = Equivalent opaque module efficiency (%)
- VLT = Visible Light Transmission (%)

#### Window Heat Gain Reduction
```
SHGC_BIPV = SHGC_glass × (1 - SC × η_BIPV)
```
Where:
- SHGC_BIPV = Solar Heat Gain Coefficient with BIPV (%)
- SHGC_glass = Original glass SHGC (%)
- SC = Shading coefficient (0.85-0.95)
- η_BIPV = BIPV module efficiency (%)

### 3.5 Shading Analysis

#### Tree Shading Factor
```
SF_tree = 1 - (A_shadow / A_panel) × (1 - LT)
```
Where:
- SF_tree = Tree shading factor (0-1)
- A_shadow = Shadowed area (m²)
- A_panel = Total panel area (m²)
- LT = Light transmission through foliage (0.1-0.3)

#### Building Self-Shading
```
h_shadow = h_obstruction × tan(90° - α)
```
Where:
- h_shadow = Shadow height (m)
- h_obstruction = Height of shading element (m)
- α = Solar elevation angle (degrees)

### 3.6 Financial Analysis Equations

#### Net Present Value (NPV)
```
NPV = Σ(CFt / (1 + r)^t) - C0
```
Where:
- NPV = Net Present Value (€)
- CFt = Cash flow in year t (€)
- r = Discount rate (%)
- t = Year (1, 2, 3, ...)
- C0 = Initial investment (€)

#### Internal Rate of Return (IRR)
```
0 = Σ(CFt / (1 + IRR)^t) - C0
```
Solved iteratively using Newton-Raphson method.

#### Levelized Cost of Energy (LCOE)
```
LCOE = Σ(Ct / (1 + r)^t) / Σ(Et / (1 + r)^t)
```
Where:
- LCOE = Levelized Cost of Energy (€/kWh)
- Ct = Cost in year t (€)
- Et = Energy generation in year t (kWh)

#### Simple Payback Period
```
PBP = C0 / CF_annual
```
Where:
- PBP = Payback period (years)
- CF_annual = Annual cash flow (€/year)

#### Discounted Payback Period
```
DPP = t when Σ(CFt / (1 + r)^t) ≥ C0
```

### 3.7 Environmental Impact Calculations

#### CO₂ Emissions Savings
```
CO2_savings = E_annual × CF_grid × LT
```
Where:
- CO2_savings = Total CO₂ savings (kg CO₂)
- E_annual = Annual energy generation (kWh)
- CF_grid = Grid carbon factor (kg CO₂/kWh)
- LT = System lifetime (years)

#### Energy Payback Time
```
EPBT = E_manufacturing / E_annual_generation
```
Where:
- EPBT = Energy Payback Time (years)
- E_manufacturing = Manufacturing energy (kWh)
- E_annual_generation = Annual energy generation (kWh)

### 3.8 Multi-Objective Optimization

#### Fitness Functions

**Objective 1: Minimize Net Energy Import**
```
f1 = Σ(max(0, Demand(t) - Generation(t)))
```

**Objective 2: Maximize Return on Investment**
```
f2 = -NPV / C0
```

#### NSGA-II Selection Criteria
```
rank(i) = number of solutions that dominate solution i
crowding_distance(i) = Σ(|f_k(i+1) - f_k(i-1)|) / (f_k^max - f_k^min)
```

### 3.9 Building Energy Integration

#### Window Area Calculation
```
A_glazed = Width × Height × Glazing_Ratio
```
Where:
- A_glazed = Effective glazed area (m²)
- Glazing_Ratio = Ratio of glass to total window area (0.8-0.95)

#### Heat Transfer Coefficient
```
U_BIPV = 1 / (1/hi + t_glass/k_glass + 1/ho + R_air_gap)
```
Where:
- U_BIPV = Overall heat transfer coefficient (W/m²K)
- hi, ho = Interior/exterior convection coefficients (W/m²K)
- t_glass = Glass thickness (m)
- k_glass = Glass thermal conductivity (W/mK)
- R_air_gap = Air gap thermal resistance (m²K/W)

---

## 4. Workflow Steps Documentation

### Step 1: Project Setup & Configuration
**Purpose**: Initialize project parameters and select building location
**Inputs**:
- Project name
- Geographic coordinates (latitude, longitude)
- Timezone selection
- Currency (standardized to EUR)

**Outputs**:
- Project configuration database record
- Location-based solar parameters
- Regional electricity rates

### Step 2: Historical Data Analysis & AI Model Training
**Purpose**: Analyze historical energy consumption and train demand prediction models
**Inputs**:
- CSV file with monthly consumption data
- Optional: Temperature, humidity, occupancy data

**Processing**:
- RandomForestRegressor model training
- Consumption pattern analysis
- Seasonal variation identification

**Outputs**:
- Trained demand prediction model
- Baseline consumption metrics
- Consumption pattern visualization

### Step 3: Weather & Environment Integration
**Purpose**: Generate Typical Meteorological Year (TMY) data
**Inputs**:
- Geographic coordinates
- OpenWeatherMap API key

**Processing**:
- 5-day forecast data retrieval
- TMY data generation using ISO 15927-4 standards
- Solar resource classification per ISO 9060

**Outputs**:
- Hourly TMY dataset (DNI, DHI, GHI)
- Solar resource quality assessment
- Weather parameter summaries

### Step 4: Facade & Window Extraction (MANDATORY)
**Purpose**: Extract building geometry from BIM models
**Inputs**:
- CSV file from BIM extraction (Dynamo script provided)
- Window element data with orientations

**Processing**:
- Element geometry analysis
- Orientation-based solar potential scoring
- PV suitability assessment

**Outputs**:
- Building element database
- Orientation analysis results
- PV-suitable element identification

### Step 5: Radiation & Shading Grid Analysis
**Purpose**: Calculate solar radiation on building surfaces
**Dependencies**: Requires Step 4 completion

**Processing**:
- pvlib solar position calculations
- Surface irradiance modeling
- Shading factor application

**Outputs**:
- Annual radiation maps
- Monthly irradiance profiles
- Shading analysis results

### Step 6: PV Panel Specification & Layout
**Purpose**: Define BIPV panel specifications and calculate layouts
**Dependencies**: Requires Step 4 completion

**Processing**:
- Panel selection from BIPV database
- Layout optimization for window elements
- System capacity calculations

**Outputs**:
- Selected panel specifications
- Layout configurations
- System capacity summary

### Step 7: Yield vs Demand Analysis
**Purpose**: Compare PV generation with building energy demand
**Dependencies**: Requires Steps 2, 5, 6 completion

**Processing**:
- Hourly yield calculations
- Demand-generation matching
- Net energy balance computation

**Outputs**:
- Energy balance profiles
- Grid import/export calculations
- Self-consumption ratios

### Step 8: Multi-Objective Optimization
**Purpose**: Optimize PV system selection using genetic algorithms
**Dependencies**: Requires Steps 6, 7 completion

**Processing**:
- NSGA-II genetic algorithm execution
- Pareto frontier identification
- Solution ranking and selection

**Outputs**:
- Optimal PV configurations
- Trade-off analysis
- Alternative solution sets

### Step 9: Financial & Environmental Analysis
**Purpose**: Comprehensive economic and environmental assessment
**Dependencies**: Requires Step 8 completion

**Processing**:
- NPV, IRR, payback calculations
- Cash flow modeling
- CO₂ savings quantification

**Outputs**:
- Financial performance metrics
- Investment analysis
- Environmental impact assessment

### Step 10: Reporting & Documentation
**Purpose**: Generate comprehensive analysis reports
**Dependencies**: All previous steps

**Processing**:
- Data consolidation from database
- Report template generation
- Visualization compilation

**Outputs**:
- HTML comprehensive report
- CSV data export
- Executive summary

---

## 5. Input Parameters Reference

### 5.1 Geographic Parameters
- **Latitude**: -90° to +90° (decimal degrees)
- **Longitude**: -180° to +180° (decimal degrees)
- **Timezone**: Standard timezone identifiers (e.g., "Europe/Berlin")

### 5.2 BIPV Panel Parameters
- **Efficiency**: 0.10 to 0.25 (10% to 25%)
- **Cost per Wp**: €0.50 to €2.00 per watt-peak
- **Visible Light Transmission**: 0.10 to 0.50 (10% to 50%)
- **Dimensions**: Width × Height in meters

### 5.3 Financial Parameters
- **Discount Rate**: 0.02 to 0.12 (2% to 12%)
- **System Lifetime**: 20 to 30 years
- **Electricity Rate**: €0.10 to €0.40 per kWh
- **Feed-in Tariff**: €0.05 to €0.20 per kWh

### 5.4 Building Parameters
- **Window-to-Wall Ratio**: 0.20 to 0.80 (20% to 80%)
- **Glazing Ratio**: 0.80 to 0.95 (80% to 95%)
- **Building Height**: 3 to 100 meters
- **Floor Area**: 100 to 50,000 m²

### 5.5 Environmental Parameters
- **Tree Density**: 0 to 100 trees per hectare
- **Tree Height**: 5 to 30 meters
- **Shading Coefficient**: 0.10 to 0.90

---

## 6. Database Schema

### 6.1 Projects Table
```sql
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    timezone VARCHAR(50),
    currency VARCHAR(3) DEFAULT 'EUR',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 6.2 Weather Data Table
```sql
CREATE TABLE weather_data (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    timestamp TIMESTAMP,
    ghi DECIMAL(8,2),
    dni DECIMAL(8,2),
    dhi DECIMAL(8,2),
    temperature DECIMAL(5,2),
    humidity DECIMAL(5,2),
    wind_speed DECIMAL(5,2)
);
```

### 6.3 Building Elements Table
```sql
CREATE TABLE building_elements (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    element_id VARCHAR(255),
    element_type VARCHAR(50),
    level_name VARCHAR(100),
    orientation VARCHAR(50),
    azimuth DECIMAL(5,2),
    area DECIMAL(10,2),
    width DECIMAL(8,2),
    height DECIMAL(8,2),
    is_pv_suitable BOOLEAN DEFAULT FALSE
);
```

### 6.4 PV Specifications Table
```sql
CREATE TABLE pv_specifications (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    panel_type VARCHAR(100),
    efficiency DECIMAL(5,4),
    cost_per_wp DECIMAL(6,2),
    power_rating DECIMAL(8,2),
    width DECIMAL(5,3),
    height DECIMAL(5,3),
    vlt DECIMAL(4,3)
);
```

### 6.5 Financial Analysis Table
```sql
CREATE TABLE financial_analysis (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    total_investment DECIMAL(12,2),
    annual_savings DECIMAL(10,2),
    npv DECIMAL(12,2),
    irr DECIMAL(5,4),
    payback_period DECIMAL(5,2),
    co2_savings DECIMAL(10,2)
);
```

---

## 7. API Integration

### 7.1 OpenWeatherMap API
**Base URL**: `https://api.openweathermap.org/data/2.5/`

**Current Weather Endpoint**:
```
GET /weather?lat={lat}&lon={lon}&appid={API_key}&units=metric
```

**Forecast Endpoint**:
```
GET /forecast?lat={lat}&lon={lon}&appid={API_key}&units=metric
```

**Response Parameters**:
- Temperature (°C)
- Humidity (%)
- Cloud cover (%)
- Wind speed (m/s)
- Solar irradiance (calculated)

### 7.2 Error Handling
- API rate limiting: 1000 calls/day
- Timeout handling: 30-second timeout
- Fallback: Historical average data

---

## 8. Installation & Deployment

### 8.1 System Requirements
- Python 3.11+
- PostgreSQL 12+
- 4GB RAM minimum
- 10GB storage space

### 8.2 Dependencies
```
streamlit==1.28.0
pandas==2.0.3
numpy==1.24.3
plotly==5.15.0
pvlib==0.10.2
deap==1.3.3
psycopg2-binary==2.9.7
requests==2.31.0
scikit-learn==1.3.0
folium==0.14.0
streamlit-folium==0.13.0
```

### 8.3 Environment Variables
```
DATABASE_URL=postgresql://user:password@host:port/database
OPENWEATHER_API_KEY=your_api_key_here
```

### 8.4 Deployment Configuration
```toml
[server]
headless = true
address = "0.0.0.0"
port = 5000

[theme]
base = "light"
```

### 8.5 Performance Optimization
- Database indexing on project_id and timestamp fields
- Caching of weather data and solar calculations
- Lazy loading of large datasets
- Async processing for optimization algorithms

---

## 9. Validation & Quality Assurance

### 9.1 Input Validation
- Geographic coordinates within valid ranges
- Panel efficiency within realistic bounds (10-25%)
- Financial parameters within market ranges
- File format validation for CSV uploads

### 9.2 Calculation Verification
- Solar position accuracy: ±0.01° compared to NREL SPA
- Irradiance calculations: ±5% compared to measured data
- Financial calculations: Cross-verified with industry standards
- Energy yield: ±10% compared to monitoring data

### 9.3 Error Handling
- Graceful degradation for missing data
- User-friendly error messages
- Automatic data validation
- Fallback calculations for edge cases

---

## 10. Troubleshooting Guide

### 10.1 Common Issues
**Database Connection Errors**:
- Verify DATABASE_URL environment variable
- Check PostgreSQL service status
- Confirm network connectivity

**API Integration Failures**:
- Validate OPENWEATHER_API_KEY
- Check API rate limits
- Verify internet connectivity

**Performance Issues**:
- Monitor database query performance
- Check memory usage during optimization
- Verify adequate storage space

### 10.2 Support Resources
- GitHub repository: [Project URL]
- Documentation: [Documentation URL]
- Research contact: mostafa.gabr@tu-berlin.de
- ResearchGate: [Profile URL]

---

## 11. References & Standards

1. **ISO 15927-4:2005** - Hygrothermal performance of buildings
2. **ISO 9060:2018** - Solar energy specification and classification of instruments
3. **IEC 61215:2016** - Crystalline silicon photovoltaic modules
4. **ASHRAE 90.1** - Energy Standard for Buildings
5. **NREL Solar Position Algorithm (SPA)**
6. **pvlib Documentation** - Solar energy modeling
7. **DEAP Documentation** - Evolutionary algorithms

---

*This documentation is part of the PhD research conducted at Technische Universität Berlin by Mostafa Gabr. For technical inquiries, please contact: mostafa.gabr@tu-berlin.de*