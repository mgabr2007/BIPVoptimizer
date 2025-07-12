# BIPV Optimizer 🌟

![BIPV Optimizer Logo](attached_assets/logo_1751541516828.png)

**Building Integrated Photovoltaics Analysis Platform**

A comprehensive AI-powered platform for analyzing, optimizing, and visualizing Building-Integrated Photovoltaic (BIPV) deployment scenarios with focus on educational building retrofitting.

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28-red.svg)](https://streamlit.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Latest-blue.svg)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-Academic-green.svg)](#license)

## 🎯 Overview

BIPV Optimizer is a cutting-edge platform developed as part of PhD research at **Technische Universität Berlin** that enables comprehensive analysis of Building-Integrated Photovoltaic systems. The platform models BIPV installations where semi-transparent PV cells replace existing window glass using exact building element data extracted from BIM models.

### Key Features

- 🗺️ **Interactive Location Selection** - Map-based project setup with weather station integration
- 🤖 **AI-Powered Analysis** - Machine learning models for energy demand prediction and optimization
- 🏢 **BIM Integration** - Direct processing of building element data from Revit/CAD models
- ☀️ **ISO-Compliant Weather Modeling** - TMY generation following ISO 15927-4 standards
- 🔬 **Multi-Objective Optimization** - NSGA-II genetic algorithms for Pareto-optimal solutions
- 💰 **Financial Analysis** - NPV, IRR, payback period with real-time electricity rates
- 🌍 **Environmental Impact** - CO₂ emissions analysis with official grid factors
- 📊 **Comprehensive Reporting** - Scientific reports with real calculated values and methodology
- 🔗 **Database Persistence** - PostgreSQL for reliable project data management
- 🎯 **Consolidated Data Management** - Unified data flow system for accurate reporting

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.11+ with essential packages (streamlit, pandas, plotly, scikit-learn, pvlib, deap)
- **Database**: PostgreSQL 16+ for project data persistence
- **API Keys**: 
  - OpenWeatherMap API key (global weather data)
  - Perplexity API key (AI research consultation)
- **Environment**: Replit platform (recommended) or local Python environment

### Quick Deployment on Replit

1. **Fork this repository** on Replit platform
2. **Set required secrets** in Replit environment:
   ```
   OPENWEATHER_API_KEY = "your_openweather_api_key"
   PERPLEXITY_API_KEY = "your_perplexity_api_key"
   DATABASE_URL = "automatically_provided_by_replit_postgresql"
   ```
3. **Install dependencies** (automatic on Replit):
   ```bash
   # Dependencies auto-installed from pyproject.toml
   streamlit, pandas, numpy, plotly, scikit-learn, pvlib, deap, 
   psycopg2-binary, requests, folium, streamlit-folium, beautifulsoup4
   ```
4. **Run the application**:
   ```bash
   streamlit run app.py --server.port 5000
   ```

### Local Installation

1. **Clone and setup**:
   ```bash
   git clone https://github.com/yourusername/bipv-optimizer.git
   cd bipv-optimizer
   pip install -r requirements.txt
   ```

2. **Database setup**:
   ```bash
   # Install PostgreSQL locally or use cloud service
   createdb bipv_optimizer
   export DATABASE_URL="postgresql://user:password@localhost:5432/bipv_optimizer"
   ```

3. **Environment configuration**:
   ```bash
   export OPENWEATHER_API_KEY="your_api_key_here"
   export PERPLEXITY_API_KEY="your_perplexity_key"
   export DATABASE_URL="postgresql://user:password@host:port/database"
   ```

4. **Launch application**:
   ```bash
   streamlit run app.py --server.port 5000
   # Access at http://localhost:5000
   ```

### Required API Keys Setup

1. **OpenWeatherMap**: Register at [openweathermap.org](https://openweathermap.org/api) for weather data access
2. **Perplexity AI**: Get API key from [perplexity.ai](https://www.perplexity.ai/) for research consultation features
3. **PostgreSQL**: Database automatically provided on Replit, or setup locally/cloud

## 🏗️ Architecture

### 11-Step Complete Workflow

1. **🌞 Welcome & Introduction** - Platform overview, standards implementation, methodology
2. **📍 Project Setup** - Interactive map location selection, weather station integration, real-time electricity rates
3. **📊 Historical Data Analysis** - AI model training (R² tracking), educational building patterns, demand forecasting
4. **🌤️ Weather Integration** - ISO 15927-4 TMY generation, dual API support (TU Berlin/OpenWeatherMap)
5. **🏢 BIM Extraction** - CSV upload processing, BIPV suitability assessment, orientation analysis
6. **☀️ Radiation Analysis** - Height-dependent effects, ground reflectance, atmospheric modeling
7. **⚡ PV Specification** - BIPV glass technology (2-25% efficiency), suitable elements only
8. **🔋 Yield vs Demand** - Monthly energy balance, seasonal patterns, cost savings analysis
9. **🎯 Optimization** - NSGA-II genetic algorithms, weighted multi-objective (cost/yield/ROI)
10. **💰 Financial Analysis** - NPV/IRR/payback, real electricity rates, grid CO₂ factors
11. **📄 Reporting** - Step-by-step reports, comprehensive master analysis
12. **🤖 AI Consultation** - Perplexity-powered research consultation with project data

### Technology Stack

- **Frontend**: Streamlit with Plotly visualizations
- **Backend**: Python with modular architecture
- **Database**: PostgreSQL for data persistence
- **Data Management**: ConsolidatedDataManager for unified data flow
- **ML/Optimization**: Scikit-learn, DEAP genetic algorithms
- **Solar Modeling**: pvlib for accurate calculations
- **APIs**: OpenWeatherMap, electricity rate services
- **GIS**: Folium for interactive mapping

## 📁 Project Structure

```
bipv-optimizer/
├── app.py                          # Main application entry point with 11-step routing
├── database_manager.py             # PostgreSQL operations and schema management
├── test_messages.py                # Message validation test environment
│
├── core/                           # Core mathematical functions
│   ├── solar_math.py              # Solar calculations, coordinates, currency utils
│   └── carbon_factors.py          # Official grid CO₂ intensity database (20+ countries)
│
├── pages_modules/                  # Complete workflow step implementations
│   ├── welcome.py                 # Introduction, standards overview, sample files
│   ├── project_setup.py           # Interactive map, weather stations, electricity rates
│   ├── historical_data.py         # AI training, R² tracking, educational building patterns
│   ├── weather_environment.py     # ISO TMY generation, dual API support
│   ├── facade_extraction.py       # BIM CSV processing, suitability assessment
│   ├── radiation_grid.py          # Height-dependent radiation, ground effects
│   ├── pv_specification.py        # BIPV glass technology, suitable filtering
│   ├── yield_demand.py            # Energy balance, seasonal patterns, financial flows
│   ├── optimization.py            # NSGA-II algorithms, weighted objectives
│   ├── financial_analysis.py      # NPV/IRR, real rates, environmental impact
│   ├── reporting.py               # Individual step reports, master analysis
│   └── detailed_report_generator.py # Scientific documentation engine
│
├── services/                       # External service integrations
│   ├── io.py                      # File operations, API clients
│   ├── weather_api_manager.py     # TU Berlin + OpenWeatherMap integration
│   └── perplexity_agent.py        # AI consultation with research integration
│
├── utils/                          # Utility functions and managers
│   ├── consolidated_data_manager.py # Centralized data flow system
│   ├── individual_step_reports.py  # Step-by-step report generation
│   ├── comprehensive_report_generator.py # Master report compilation
│   ├── color_schemes.py           # UI styling and chart themes
│   └── wmo_station_parser.py      # Weather station database management
│
├── components/                     # UI components
│   └── workflow_visualization.py  # Dynamic progress tracking, milestones
│
└── attached_assets/               # Resources and sample files
    ├── BIPV_Specifications_*.csv  # Sample BIPV technology data
    ├── TMY_Data_*.csv             # Sample weather datasets
    ├── TUB_H_Building_*.csv       # Sample building energy data
    ├── *.dyn                      # Dynamo scripts for BIM extraction
    ├── *.png                      # UI images, logos, step graphics
    └── *.html                     # Generated analysis reports
```

### Key Architecture Features
- **Modular Design**: Separate modules for each workflow step with clear dependencies
- **Centralized Data Management**: ConsolidatedDataManager ensures data consistency
- **Database Integration**: PostgreSQL for reliable project persistence
- **API Abstraction**: WeatherAPIManager handles multiple weather data sources
- **Report Generation**: Multiple report formats with authentic calculated values
- **Error Handling**: Comprehensive validation and fallback mechanisms

## 🔬 Scientific Methodology

### Standards Implementation

- **ISO 15927-4**: Typical Meteorological Year calculations
- **ISO 9060**: Solar resource classification
- **EN 410**: Glass optical properties for BIPV
- **ASHRAE 90.1**: Building energy standards
- **IEA PVPS**: Photovoltaic system guidelines

### Mathematical Framework

The platform implements comprehensive equations for:

- Solar position calculations (sun elevation, azimuth)
- Irradiance modeling (DNI, DHI, GHI decomposition)
- PV yield estimation with temperature corrections
- Multi-objective optimization (minimize cost, maximize yield/ROI)
- Financial modeling (NPV, IRR, payback period)
- Environmental impact (CO₂ emissions, lifecycle assessment)

## 📊 Data Sources & APIs

### Weather Data Integration
- **Primary Source**: WMO CLIMAT stations (40+ global locations with authentic metadata)
- **TU Berlin Climate Portal**: Academic-grade meteorological data for Berlin/Germany
- **OpenWeatherMap API**: Global coverage for international projects
- **Standards Compliance**: ISO 15927-4 TMY generation with astronomical algorithms
- **Quality Assurance**: Air mass corrections, climate zone modeling, elevation adjustments

### Economic Data Sources  
- **Live Electricity Rates**: Real-time API integration
  - **Germany**: SMARD (Federal Network Agency)
  - **UK**: Ofgem official rates
  - **USA**: EIA (Energy Information Administration)
  - **EU**: Eurostat regional averages
- **Currency System**: Standardized EUR calculations with real-time exchange rates
- **CO₂ Grid Factors**: Official sources (IEA World Energy Outlook 2023, EEA, national TSOs)

### Building Data Processing
- **BIM Integration**: CSV extraction from Revit/CAD models via Dynamo scripts
- **Element Types**: Windows, curtain walls, glazing systems with complete metadata
- **Authentic Properties**: Element IDs, dimensions, orientations, glass areas, building levels
- **Suitability Assessment**: Automated filtering for South/East/West orientations (excludes north-facing)
- **Quality Control**: Zero fallback values - only authentic BIM data used

### AI & Optimization
- **Machine Learning**: RandomForestRegressor for demand prediction with R² score tracking
- **Genetic Algorithms**: NSGA-II multi-objective optimization (cost/yield/ROI)
- **Research Integration**: Perplexity AI for literature-based recommendations
- **Performance Metrics**: Real-time model performance monitoring and improvement guidance

## 🎯 Use Cases

### Primary Applications
- **Educational Buildings**: Schools, universities, research facilities
- **Commercial Retrofits**: Office buildings, mixed-use developments
- **Feasibility Studies**: Pre-design BIPV assessment
- **Research Projects**: Academic studies and publications

### Target Users
- **Architects & Engineers**: Building design professionals
- **Energy Consultants**: Renewable energy specialists
- **Researchers**: Academic and industry R&D
- **Property Developers**: Investment decision support

## 🔄 Recent Improvements

### Complete Platform Enhancement (July 2025)
- **11-Step Complete Workflow**: Fully functional analysis pipeline from welcome through AI consultation
- **Height-Dependent Radiation Analysis**: 5-20% radiation enhancement factors for ground floors vs upper levels
- **BIPV Suitability Filtering**: Intelligent exclusion of 191 north-facing windows from 950 total elements
- **Perplexity AI Integration**: Research-based consultation using actual project data
- **Multi-Source Data Integration**: TU Berlin API for Germany, OpenWeatherMap globally
- **Real-Time Electricity Rates**: Live API integration for authentic financial calculations

### Consolidated Data Management System (January 2025)
- **Centralized Data Flow**: Implemented ConsolidatedDataManager for unified data collection across all workflow steps
- **Real Value Reporting**: Eliminated placeholder zeros in comprehensive reports with authentic calculated values
- **Enhanced Data Integrity**: Standardized data structures between workflow steps and report generation
- **Improved Reliability**: Robust error handling and data validation throughout the analysis pipeline

### Key Technical Enhancements
- **Unified Data Architecture**: Single source of truth for all analysis results
- **Real-time Data Capture**: Automatic data collection as each workflow step completes
- **Enhanced Debugging**: Comprehensive logging system for data flow tracking
- **Improved User Experience**: Accurate reports with actual project-specific calculations
- **PostgreSQL Integration**: Reliable project data persistence and retrieval
- **Height-Based Solar Modeling**: Ground reflectance, GHI adjustments, atmospheric effects
- **Authentic Data Requirements**: Zero fallback values - only real TMY and BIM data used

## 🤝 Contributing

This project is developed as part of PhD research at Technische Universität Berlin. Contributions are welcome through:

1. **Issue Reports**: Bug reports and feature requests via GitHub Issues
2. **Code Contributions**: Pull requests for improvements and new features
3. **Academic Collaboration**: Research partnerships and methodology validation
4. **Data Validation**: Verification of calculations, standards implementation, and results
5. **Documentation**: Improvements to technical documentation and user guides

### Development Guidelines

- **Code Style**: Follow PEP 8 Python style guidelines with comprehensive docstrings
- **Testing**: Include unit tests for new functionality, validate against known benchmarks
- **Documentation**: Update technical docs for API changes, maintain academic references
- **Data Integrity**: Preserve authentic data requirements - no fallback/synthetic values
- **Academic Attribution**: Maintain proper citation to TU Berlin research and sources
- **Modular Design**: Follow existing architecture patterns in pages_modules/ structure

### Research Collaboration

- **Academic Partnerships**: Welcome collaboration on BIPV methodology and validation
- **Standards Implementation**: Assistance with ISO, EN, ASHRAE standards verification
- **Performance Validation**: Real-world project testing and results comparison
- **Publication Support**: Co-authorship opportunities for peer-reviewed publications

### Technical Contributions Priority

1. **Enhanced BIM Integration**: Additional CAD/BIM format support beyond CSV
2. **Advanced Optimization**: Multi-criteria decision analysis, sensitivity analysis
3. **Regional Expansion**: Additional weather APIs, local electricity rate sources
4. **Validation Tools**: Comparison with commercial BIPV analysis software
5. **Performance Optimization**: Large-scale building analysis (1000+ elements)

## 📜 License

This software is developed for academic research purposes at Technische Universität Berlin. Commercial use requires permission.

**Academic Attribution Required**:
- Mostafa Gabr, PhD Candidate
- Technische Universität Berlin, Faculty VI
- ResearchGate: [Mostafa Gabr Profile](https://www.researchgate.net/profile/Mostafa-Gabr-4)

## 📞 Contact

**Developer**: Mostafa Gabr  
**Institution**: Technische Universität Berlin  
**Faculty**: VI - Planning Building Environment  
**ResearchGate**: https://www.researchgate.net/profile/Mostafa-Gabr-4  
**University**: https://www.tu.berlin/en/planen-bauen-umwelt/

---

## 🏆 Acknowledgments

- **Technische Universität Berlin** - Research institution
- **Faculty VI** - Planning Building Environment
- **IEA PVPS Task 15** - BIPV methodology guidelines
- **ISO Technical Committees** - International standards
- **OpenWeatherMap** - Weather data services
- **Replit Platform** - Development and deployment environment

---

**Made with ☀️ by OptiSunny - Your BIPV Analysis Companion**

*Advancing building-integrated photovoltaics through scientific analysis and AI-powered optimization.*