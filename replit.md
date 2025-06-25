# BIPV Optimizer

## Overview

BIPV Optimizer is a comprehensive Building Integrated Photovoltaics optimization platform built with Streamlit. The application provides a complete workflow for analyzing and optimizing photovoltaic system installations on building facades and windows, from initial project setup through financial analysis and 3D visualization.

The platform follows a 10-step workflow that guides users through the entire BIPV analysis process, including historical data analysis, weather integration, facade extraction, radiation modeling, PV specification, yield calculations, optimization, and financial analysis.

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
core/
├── solar_math.py             # Mathematical functions and solar calculations
└── __init__.py

services/
├── io.py                     # External I/O services (DB, APIs, file parsing)
└── __init__.py

pages/
├── welcome.py                # Welcome and introduction page
├── project_setup.py          # Project configuration and location setup
├── historical_data.py        # Energy consumption analysis and AI model training
├── weather_environment.py    # Weather data integration and TMY generation
├── facade_extraction.py      # Building facade and window extraction from BIM
├── reporting.py              # Report generation and data export
└── __init__.py

Legacy modules/ (to be refactored):
├── radiation_grid.py         # Solar radiation grid generation and shading analysis
├── pv_specification.py       # PV panel specification and layout calculation
├── yield_demand.py          # Energy yield vs demand calculation
├── optimization.py          # Multi-objective optimization using genetic algorithms
├── financial_analysis.py    # Financial modeling and environmental impact
└── visualization_3d.py      # 3D building and PV system visualization
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

### 4. Facade & Window Extraction (REQUIRED)
- **Purpose**: Extract building geometry from BIM models for PV suitability analysis
- **Technology**: CSV upload from BIM model extraction with comprehensive window element data
- **Requirement**: This step is MANDATORY - all subsequent analysis steps require building element data
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

### 10. Reporting & Export
- **Purpose**: Generate comprehensive reports and export analysis results
- **Formats**: PDF/HTML reports, CSV/JSON data export
- **Content**: Executive summary, technical analysis, financial projections

## Data Flow

1. **Project Initialization**: User configures project settings (location, timezone, currency)
2. **Historical Analysis**: Energy consumption data is processed and ML models are trained
3. **Weather Integration**: TMY data is fetched and processed for solar calculations
4. **Building Analysis (REQUIRED)**: BIM-extracted window elements uploaded via CSV - MANDATORY for all subsequent steps
5. **Solar Modeling**: Radiation grids are generated with shading analysis using exact building geometry
6. **System Design**: PV panels are specified and layouts calculated for specific window elements
7. **Energy Modeling**: Yield predictions compared with demand forecasts using actual building data
8. **Optimization**: Genetic algorithms find optimal PV configurations for specific building elements
9. **Financial Analysis**: Economic viability assessed using exact system specifications
10. **Reporting**: Comprehensive analysis reports generated with building-specific results

**Critical Requirement**: Steps 5-10 cannot proceed without BIM data from Step 4, as BIPV analysis requires exact building element geometry for accurate calculations.

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
- June 19, 2025: Fixed Streamlit duplicate element ID errors by adding unique keys to all interactive elements
- June 19, 2025: Rebranded application to "BIPV Optimizer" with updated titles and project references
- June 19, 2025: Resolved numpy dependency conflicts by implementing pure Python mathematical operations
- June 19, 2025: Enhanced report generation with downloadable HTML reports and comprehensive content
- June 19, 2025: Added comprehensive interactive visualizations to all report types including energy balance charts, financial projections, solar radiation heatmaps, PV technology comparisons, and CO₂ savings analysis
- June 19, 2025: Implemented proper integration of location, timezone, and currency settings throughout all calculations including location-based solar parameters, electricity rates, currency conversion, and localized financial metrics display
- June 20, 2025: Modified Step 11 reporting to remove data export functionality and create single comprehensive report option with complete equations, detailed calculation methodologies, and enhanced process explanations
- June 20, 2025: Streamlined Step 1 project setup by removing unused inputs (Units System, Interface Language, Building Type, BIM file upload) to focus only on essential parameters used in calculations
- June 20, 2025: Cleaned up project structure by removing multiple legacy app files (app_complete.py, app_dependency_fixed.py, app_fixed.py, app_minimal.py, app_minimal_test.py, app_pure_python.py, app_streamlit_only.py, app_working_minimal.py, app_working.py) and consolidated to single main app.py file
- June 20, 2025: Enhanced Step 4 with CSV upload functionality for BIM-extracted windows and facade data including orientation mapping, glass area filtering, and comprehensive building element analysis
- June 20, 2025: Simplified Step 9 by fixing numeric type errors in financial analysis inputs and removed Step 10 (3D visualization) to streamline workflow from 11 to 10 steps due to lacking required inputs and viewers
- June 20, 2025: Updated Step 4 to process all window elements regardless of glass area and maintain Element IDs for calculations, with default 1.5m² window area when glass area is 0
- June 20, 2025: Modified report footer to include PhD research attribution at Technische Universität Berlin with contact information for Mostafa Gabr and ResearchGate profile link
- June 20, 2025: Enhanced report generation with comprehensive BIPV-specific equations including BIM-based window analysis, PV suitability threshold calculations, orientation-based filtering, BIPV glass technology specifications, multi-objective optimization (NSGA-II), BIPV-specific cash flow analysis, lifecycle assessment, and updated technical appendices with BIPV technology parameters and optimization algorithm settings
- June 20, 2025: Added CSV download functionality to Step 10 (Reporting) with detailed window element data including Element ID, Wall-hosted ID, glass area, orientation, azimuth, annual radiation (kWh/m²), expected production (kWh), BIPV selection status, window dimensions, and building level for comprehensive data export and further analysis
- June 20, 2025: Updated Step 10 navigation button from "Next Step" to "Finish & New Calculation" to properly conclude the workflow and provide option to start fresh analysis while preserving project data integrity
- June 21, 2025: Enhanced Step 1 with interactive map-based location selection using folium and streamlit-folium for precise coordinate selection
- June 21, 2025: Integrated OpenWeatherMap API for real-time weather data retrieval based on map-selected coordinates with automatic API key loading from environment
- June 21, 2025: Implemented comprehensive global location database with 25+ regions including Middle East, Asia, Africa, and Americas for accurate solar irradiance and electricity rate parameters
- June 21, 2025: Added latitude-based solar parameter estimation for unknown locations using climate zone classification (equatorial, tropical, subtropical, temperate, arctic)
- June 21, 2025: Enhanced WMO weather station finder with 40+ global stations for nearest meteorological reference data
- June 21, 2025: Enhanced Step 6 economic parameters with comprehensive calculation methodology, research references, cost equations, and validation against market benchmarks from IRENA, IEA PVPS, NREL, and academic sources
- June 21, 2025: Enhanced Step 7 with direct CSV occupancy data extraction from Step 2 AI model and comprehensive educational building standards including K-12 schools, universities, research facilities, libraries, and dormitories with ASHRAE 90.1 compliance and occupancy pattern analysis
- June 21, 2025: Enhanced Step 4 to include ALL window area elements from BIM data upload with comprehensive orientation analysis, expanded window type recognition (windows, curtain walls, glazing), enhanced BIM property extraction (dimensions, levels, families), and orientation-based solar performance scoring
- June 21, 2025: Removed Location-Specific Parameters display from Step 1 to streamline interface while preserving calculated parameters for use in subsequent calculations
- June 21, 2025: Closed PV Suitability Threshold info notes in Step 4 to clean up interface while keeping methodology details accessible via expander
- June 21, 2025: Added Dynamo script download functionality to Step 4 with comprehensive instructions for extracting BIM data from Revit models including window metadata, orientations, and glass areas
- June 21, 2025: Standardized all calculations and symbols to use Euros (EUR) as base currency with updated electricity rates, currency symbols, and exchange rate calculations throughout the application
- June 21, 2025: Removed currency selection from Step 1 interface to enforce Euro-only calculations with automatic EUR assignment
- June 21, 2025: Unified and improved Step 1 UI with consistent messaging, enhanced visual layout, improved location information cards, better button styling, and streamlined project configuration summary
- June 21, 2025: Added comprehensive Welcome step with BIPV explanation, workflow overview, scientific methodology, research context, and visual workflow guide to introduce users to the platform capabilities
- June 23, 2025: Implemented critical BIM data validation throughout workflow - Step 4 (Facade & Window Extraction) is now MANDATORY for all subsequent analysis steps (5-10) with comprehensive error messages explaining why building element data is essential for accurate BIPV calculations
- June 23, 2025: Fixed critical application startup errors by replacing corrupted HTML report template with clean functions, restored proper Python syntax throughout codebase, and implemented missing render_reporting function for Step 10 workflow completion
- June 23, 2025: Enhanced Step 10 report generation to use actual processed data from all workflow steps instead of placeholder values, including real BIM data, weather analysis, PV specifications, financial calculations, and environmental impact results for authentic project-specific reports
- June 24, 2025: Implemented comprehensive PostgreSQL database system for persistent data storage with dedicated tables for projects, weather data, building elements, radiation analysis, PV specifications, financial analysis, and environmental impact metrics
- June 24, 2025: Created database manager module with full CRUD operations for all workflow data, enabling reliable data persistence across sessions and comprehensive project management capabilities
- June 24, 2025: Integrated project selector interface in sidebar allowing users to save, load, and delete previously analyzed projects from database with automatic session state restoration
- June 24, 2025: Enhanced report generation to prioritize database data over session state, providing consistent and reliable reporting from persistently stored analysis results
- June 24, 2025: Implemented comprehensive data persistence for all 10 workflow steps with automatic database saving after each step completion, including historical data analysis, TMY generation, yield calculations, optimization results, and complete session state restoration when loading projects
- June 24, 2025: Refactored monolithic app.py into modular package structure with core/, services/, and pages/ directories for improved maintainability and separation of concerns
- June 24, 2025: Enhanced Step 10 report download functionality with timestamp-based filenames, content validation, session state persistence, CSV preview capabilities, and comprehensive error handling with fallback reports
- June 24, 2025: Added Streamlit caching optimization (@st.cache_data with ttl=3600) for WMO station parsing and location parameter functions, significantly improving application performance
- June 24, 2025: Fixed critical syntax errors in report generation including indentation issues, try-except block structure, and duplicate else statements that prevented application startup
- June 24, 2025: Completed comprehensive function analysis - application fully operational with 6 workflow steps (Welcome, Project Setup, Historical Data, Weather Integration, Facade Extraction, Reporting) and modular architecture providing clean separation of concerns with PostgreSQL database integration
- June 24, 2025: Implemented complete workflow integration - all 11 steps now fully functional including radiation analysis, PV specification, yield vs demand analysis, multi-objective optimization, and financial analysis with no remaining placeholders
- June 24, 2025: Improved UI by removing title and workflow headers from sidebar, starting directly with "Loading the project" section, and moved step navigation from top of pages to bottom for better user experience
- June 24, 2025: Removed balloon celebration animations from all workflow steps to create a cleaner, more professional interface
- June 24, 2025: Fixed sidebar folder links by renaming pages/ to pages_modules/ to prevent Streamlit's automatic multipage detection
- June 24, 2025: Implemented dynamic workflow visualization with intuitive step progression including progress tracking, milestone visualization, completion status, and enhanced navigation with visual feedback
- June 24, 2025: Created comprehensive technical documentation (BIPV_Documentation.md) with complete mathematical equations, workflow descriptions, input parameter references, database schema, and API integration details
- June 24, 2025: Added detailed help text and info notes to all input fields throughout the application providing context, typical values, calculation methods, and regional variations for user guidance
- June 25, 2025: Enhanced welcome page with comprehensive standards implementation guide explaining where ISO 15927-4, ISO 9060, EN 410, and ASHRAE 90.1 standards are used throughout the analysis workflow
- June 25, 2025: Added detailed mathematical foundation section with complete optimization and analysis equations including solar calculations, PV yield formulas, NSGA-II optimization parameters, financial analysis equations, and environmental impact calculations
- June 25, 2025: Revised welcome page to focus on standards implementation mapping and equations overview while avoiding duplication with existing technical documentation, providing clear workflow-specific context for users
- June 25, 2025: Fixed UTF-8 decoding error in Step 3 Weather Environment by implementing robust encoding fallback mechanism (utf-8, latin-1, iso-8859-1, cp1252) for WMO stations file reading and enhanced error handling with user-friendly messages
- June 25, 2025: Fixed Step 5 building elements data recognition issue by correcting session state variable checks and ensuring proper data flow from Step 4 facade extraction to Step 5 radiation analysis

## User Preferences

Preferred communication style: Simple, everyday language.
UI preferences: Clean sidebar without headers, navigation at bottom of pages for improved user experience, no balloon celebrations or animations.