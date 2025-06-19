# BIPV Analysis Platform

## Overview

This is a comprehensive Building Integrated Photovoltaics (BIPV) Analysis Platform built with Streamlit. The application provides a complete workflow for analyzing and optimizing photovoltaic system installations on building facades and windows, from initial project setup through financial analysis and 3D visualization.

The platform follows an 11-step workflow that guides users through the entire BIPV analysis process, including historical data analysis, weather integration, facade extraction, radiation modeling, PV specification, yield calculations, optimization, and financial analysis.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web application with wide layout and expandable sidebar
- **Navigation**: Multi-page workflow system with 11 sequential modules
- **Visualization**: Plotly for interactive charts, graphs, and 3D building visualization
- **State Management**: Streamlit session state for workflow progress and data persistence

### Backend Architecture
- **Language**: Python 3.11
- **Structure**: Modular design with separate modules for each workflow step
- **Data Processing**: Pandas and NumPy for data manipulation and analysis
- **Machine Learning**: Scikit-learn for energy demand prediction models
- **Optimization**: DEAP (Distributed Evolutionary Algorithms in Python) for genetic algorithm optimization

### Module Structure
```
modules/
├── project_setup.py          # Project configuration and BIM model upload
├── historical_data.py         # Energy consumption data analysis and AI model training
├── weather_environment.py     # Weather data integration and TMY generation
├── facade_extraction.py       # Building facade and window extraction from BIM
├── radiation_grid.py          # Solar radiation grid generation and shading analysis
├── pv_specification.py        # PV panel specification and layout calculation
├── yield_demand.py           # Energy yield vs demand calculation
├── optimization.py           # Multi-objective optimization using genetic algorithms
├── financial_analysis.py     # Financial modeling and environmental impact
├── visualization_3d.py       # 3D building and PV system visualization
└── reporting.py              # Report generation and data export
```

## Key Components

### 1. Project Setup Module
- **Purpose**: Initialize project configuration and handle BIM model uploads
- **Features**: Timezone selection, currency settings, units configuration
- **File Support**: Revit model uploads (.rvt files at LOD 200 and LOD 100)

### 2. Historical Data & AI Model
- **Purpose**: Analyze historical energy consumption and train demand prediction models
- **Technology**: RandomForestRegressor for baseline demand modeling
- **Input**: CSV files with monthly consumption data, temperature, and environmental factors

### 3. Weather & Environment Integration
- **Purpose**: Fetch weather data and generate Typical Meteorological Year (TMY) datasets
- **API Integration**: OpenWeatherMap API for current and historical weather data
- **Output**: Hourly DNI/DHI/GHI solar irradiance data with quality reports

### 4. Facade & Window Extraction
- **Purpose**: Extract building geometry from BIM models for PV suitability analysis
- **Technology**: Simulated Revit API integration (pythonnet for future implementation)
- **Output**: Facade and window elements with geometry metadata and PV suitability flags

### 5. Radiation & Shading Grid
- **Purpose**: Calculate solar radiation on building surfaces with shading analysis
- **Technology**: pvlib for solar position calculations and irradiance modeling
- **Features**: Orientation/tilt corrections, tree shading factors, spatial radiation grids

### 6. PV Panel Specification
- **Purpose**: Define PV panel specifications and calculate system layouts
- **Database**: Built-in PV panel database with efficiency, cost, and dimension data
- **Panel Types**: Monocrystalline, polycrystalline, thin-film, and bifacial options

### 7. Yield vs Demand Calculation
- **Purpose**: Compare PV energy generation with predicted building demand
- **Integration**: Uses trained demand model and calculated PV yields
- **Output**: Net import calculations and energy balance profiles

### 8. Multi-Objective Optimization
- **Purpose**: Optimize PV system selection using genetic algorithms
- **Technology**: DEAP for evolutionary optimization
- **Objectives**: Minimize net energy import, maximize return on investment (ROI)
- **Output**: Pareto-optimal solutions with alternative configurations

### 9. Financial & Environmental Analysis
- **Purpose**: Comprehensive financial modeling and environmental impact assessment
- **Calculations**: NPV, IRR, payback period, CO₂ savings
- **Features**: Cash flow analysis, sensitivity analysis, emissions tracking

### 10. 3D Visualization
- **Purpose**: Interactive 3D visualization of building and PV system placement
- **Technology**: Plotly 3D graphics for building geometry and PV overlay visualization
- **Features**: Interactive building models with PV panel placement indicators

### 11. Reporting & Export
- **Purpose**: Generate comprehensive reports and export analysis results
- **Formats**: PDF/HTML reports, CSV/JSON data export
- **Content**: Executive summary, technical analysis, financial projections

## Data Flow

1. **Project Initialization**: User configures project settings and uploads BIM models
2. **Historical Analysis**: Energy consumption data is processed and ML models are trained
3. **Weather Integration**: TMY data is fetched and processed for solar calculations
4. **Building Analysis**: Facade and window elements are extracted and analyzed for PV suitability
5. **Solar Modeling**: Radiation grids are generated with shading analysis
6. **System Design**: PV panels are specified and layouts are calculated
7. **Energy Modeling**: Yield predictions are compared with demand forecasts
8. **Optimization**: Genetic algorithms find optimal PV system configurations
9. **Financial Analysis**: Economic viability and environmental impact are assessed
10. **Visualization**: 3D models display optimized PV placement
11. **Reporting**: Comprehensive analysis reports are generated

## External Dependencies

### Core Dependencies
- **streamlit**: Web application framework
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing
- **plotly**: Interactive visualization and 3D graphics
- **scikit-learn**: Machine learning for demand prediction
- **pvlib**: Solar energy modeling and calculations
- **deap**: Genetic algorithm optimization
- **requests**: HTTP client for weather API integration

### Weather Data Integration
- **OpenWeatherMap API**: Real-time and historical weather data
- **API Requirements**: API key for weather data access
- **Data Types**: Current conditions, historical data, solar irradiance

### BIM Integration (Future)
- **pythonnet**: .NET integration for Revit API access
- **Revit API**: Building model data extraction
- **File Formats**: .rvt files at LOD 200 and LOD 100

### Financial Modeling
- **pytz**: Timezone handling for financial calculations
- **openpyxl**: Excel file export for financial models

## Deployment Strategy

### Platform Configuration
- **Deployment Target**: Replit autoscale deployment
- **Runtime**: Python 3.11 with Nix package management
- **Port Configuration**: Streamlit server on port 5000
- **Environment**: Stable Nix channel (24_05) with glibc locales

### Application Startup
- **Entry Point**: `streamlit run app.py --server.port 5000`
- **Configuration**: Headless server mode with light theme
- **Address Binding**: 0.0.0.0 for external access

### Scalability Considerations
- **Session State**: Uses Streamlit session state for data persistence
- **Memory Management**: Modular loading of large datasets
- **API Rate Limiting**: Weather API calls optimized for usage limits

## CSV File Upload Requirements

The platform now includes comprehensive CSV file structure documentation for all upload modules:

### 1. Historical Energy Data Upload (Step 2)
**Required Columns:**
- `Date`: YYYY-MM-DD format (e.g., 2023-01-01)
- `Consumption`: Monthly energy consumption in kWh (numeric values only)

**Optional Columns:**
- `Temperature`: Average monthly temperature in °C
- `Humidity`: Average monthly humidity percentage (0-100)
- `Solar_Irradiance`: Monthly solar irradiance in kWh/m²
- `Occupancy`: Building occupancy percentage (0-100)

### 2. BIM Model Upload (Step 1)
**Primary Format:**
- Revit Models (.rvt): Minimum LOD 200, recommended LOD 300
- Must include facade and window elements with proper orientations
- File size limit: 50MB maximum

**Alternative Formats (Future Support):**
- IFC Files (.ifc): Industry Foundation Classes
- DWG Files (.dwg): AutoCAD drawings with 3D geometry
- 3DS Files (.3ds): 3D Studio Max models

### 3. Data Export Formats (Step 11)
**CSV Export Structure:**
- PV_Systems_Summary.csv: Element data with performance metrics
- Energy_Balance_Monthly.csv: Monthly demand/generation analysis
- Financial_Analysis.csv: Economic parameters and projections

**Export Guidelines:**
- All monetary values in selected project currency
- Energy values in kWh, power values in kW
- Dates in YYYY-MM-DD format
- Numeric values use decimal points (not commas)

## Changelog

- June 19, 2025: Initial setup
- June 19, 2025: Enhanced documentation with detailed equation explanations and comprehensive HTML reports
- June 19, 2025: Implemented interactive 3D BIM model visualization with zoom and rotate capabilities
- June 19, 2025: Added comprehensive CSV file structure documentation for all upload modules

## User Preferences

Preferred communication style: Simple, everyday language.