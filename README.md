> **Implementation status (September 2026 repair branch):** The executable optimizer is weighted genetic search, not NSGA-II. The historical-data page uses an unevaluated trend/seasonal scenario, not a fitted RandomForest. See [repair notes](docs/REPAIR_NOTES_2026-09-09.md) for changes, validation limits and remaining work. Older method descriptions below require reconciliation.

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

## 🆕 Latest Updates (September 2025)

### Enhanced Data Export & Financial Analysis
- ✅ **Fixed Financial Analysis CSV Export**: Resolved export button functionality with complete 25-year cash flow data
- ✅ **Optimized Window Selection**: CSV exports now show only optimization solution results (~13-15 selected windows)
- ✅ **Complete Financial Data Integration**: Added sensitivity analysis, NPV variations, and structured data formats
- ✅ **Database Schema Enhancement**: Updated PostgreSQL schema for complete workflow data persistence

### Technical Improvements
- ✅ **Clean Architecture Maintenance**: Streamlined codebase with essential components only
- ✅ **Performance Optimization**: Enhanced data flow between optimization and financial analysis
- ✅ **Data Validation**: Strengthened authentic data requirements with comprehensive error handling
- ✅ **Export System Validation**: All CSV exports now include authentic data with proper filtering

### Key Features

- 🗺️ **Interactive Location Selection** - Map-based project setup with weather station integration
- 🤖 **AI-Powered Analysis** - Machine learning models for energy demand prediction and optimization
- 🏢 **BIM Integration** - Direct processing of building element data from Revit/CAD models
- ☀️ **ISO-Compliant Weather Modeling** - TMY generation following ISO 15927-4 standards
- 🔬 **Multi-Objective Optimization** - NSGA-II genetic algorithms for Pareto-optimal solutions with complete solution traceability
- 💰 **Financial Analysis** - NPV, IRR, payback analysis with 25-year cash flow projections and sensitivity analysis
- 🌍 **Environmental Impact** - CO₂ emissions analysis with official grid factors and carbon value calculations
- 📊 **Advanced Data Export** - Multi-format exports (CSV, HTML) with optimized window selection and complete financial data
- 📋 **Comprehensive Reporting** - Scientific reports with authentic calculated values and complete methodology documentation
- 🔗 **Database Persistence** - Enhanced PostgreSQL schema supporting all workflow steps with complete data relationships
- 🎯 **Authentic Data Management** - Unified data flow system ensuring zero fallback data and complete audit trails

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

### 10-Step Workflow + Bonus AI Consultation

**Main Analysis Workflow (Steps 1-10):**
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

**Bonus Step:**
11. **🤖 AI Research Consultation** - Advanced Perplexity-powered research consultation using your actual project data for expert BIPV recommendations and literature-based insights

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
├── app.py                          # Main Streamlit application entry point
├── database_manager.py             # PostgreSQL operations and data persistence
├── wmo_stations_complete.py        # Global weather station database (CLIMAT)
│
├── core/                           # Core mathematical functions
│   ├── solar_math.py              # Solar position, irradiance calculations
│   └── carbon_factors.py          # Grid CO₂ intensity database (20+ countries)
│
├── pages_modules/                  # 10+1 step workflow implementation
│   ├── welcome.py                 # Platform introduction and methodology
│   ├── project_setup.py           # Map-based location, weather stations
│   ├── historical_data.py         # AI model training, R² tracking
│   ├── weather_environment.py     # ISO TMY generation, meteorological data
│   ├── facade_extraction.py       # BIM data processing, BIPV suitability
│   ├── radiation_grid.py          # Solar radiation analysis, shading effects
│   ├── pv_specification_unified.py # BIPV glass technology specifications
│   ├── yield_demand.py            # Energy balance, seasonal analysis
│   ├── optimization.py            # NSGA-II genetic algorithms
│   ├── financial_analysis.py      # NPV/IRR, electricity rates, CO₂ impact
│   ├── comprehensive_dashboard.py # Master reporting and data export
│   ├── detailed_report_generator.py # Scientific report generation
│   └── step7_yield_demand/        # Modular yield analysis components
│       ├── data_validation.py     # Input validation and dependency checks
│       ├── calculation_engine.py  # Core yield calculations with caching
│       └── ui_components.py       # User interface rendering
│
├── services/                       # External integrations and analyzers
│   ├── io.py                      # File operations, project ID management
│   ├── weather_api_manager.py     # Multi-source weather data integration
│   ├── perplexity_agent.py        # AI research consultation
│   ├── optimized_radiation_analyzer.py # High-performance radiation analysis
│   ├── ultra_fast_radiation_analyzer.py # 8-second processing optimization
│   ├── advanced_radiation_analyzer.py # Comprehensive TMY integration
│   ├── electricity_rates.py       # Real-time electricity rate APIs
│   └── database_state_manager.py  # Database session management
│
├── utils/                          # Data management and reporting utilities
│   ├── consolidated_data_manager.py # Unified data flow across workflow
│   ├── database_helper.py         # Database operations abstraction
│   ├── comprehensive_report_generator.py # Master report compilation
│   ├── individual_step_reports.py # Step-specific report generation
│   ├── report_data_extractor.py   # Authentic data extraction for reports
│   ├── calculations.py            # Mathematical utility functions
│   └── color_schemes.py           # UI styling and visualization themes
│
├── components/                     # UI components
│   └── workflow_visualization.py  # Progress tracking and navigation
│
├── static/                         # Web assets
│   ├── manifest.json              # PWA configuration
│   ├── robots.txt                 # Search engine directives
│   └── sitemap.xml                # Site structure for SEO
│
└── attached_assets/               # Sample data and resources
    ├── BIPV_Specifications_*.csv  # Sample BIPV technology datasets
    ├── TMY_Data_*.csv             # Weather and irradiance samples
    ├── TU_Berlin_*.csv            # Building energy consumption data
    ├── get_windowMetadata_*.dyn    # Dynamo scripts for BIM extraction
    ├── BIPVOptiLogo*.png          # Branding and UI graphics
    └── *.html                     # Generated analysis reports
```

### Key Architecture Features
- **Clean Modular Design**: Essential files only with streamlined architecture
- **10+1 Step Workflow**: Complete BIPV analysis (Steps 1-10) plus bonus AI research consultation (Step 11)
- **Database-Driven**: Enhanced PostgreSQL persistence with comprehensive schema and centralized project ID system
- **Performance Optimized**: High-speed radiation analysis with optimized data processing
- **Authentic Data Pipeline**: Complete data traceability from source APIs to final reports with zero fallback values
- **Advanced Export System**: Multi-format data export with optimized filtering and complete financial analysis integration
- **Professional Interface**: Clean navigation with professional branding and user experience optimization
- **Research Grade**: ISO standards compliance, academic references, and peer-reviewed methodology implementation

### Workflow Dependencies & Data Flow

The BIPV Optimizer follows a structured data flow across all workflow steps:

#### **Data Dependencies Chain**:
1. **Step 1** → Location data, electricity rates → **Used by all subsequent steps**
2. **Step 2** → Historical energy data, AI model → **Required for Step 7 demand predictions**
3. **Step 3** → TMY weather data → **Required for Steps 5, 6, 7**
4. **Step 4** → BIM building elements → **Required for Steps 5, 6, 7, 8**
5. **Step 5** → Radiation analysis → **Required for Steps 6, 7, 8**
6. **Step 6** → BIPV specifications → **Required for Steps 7, 8, 9**
7. **Step 7** → Yield vs demand analysis → **Required for Steps 8, 9**
8. **Step 8** → Optimization results → **Required for Steps 9, 10, 11**
9. **Step 9** → Financial analysis → **Required for Steps 10, 11**
10. **Step 10** → Comprehensive reporting → **Data source for Step 11**
11. **Step 11** → AI consultation using all previous data

#### **Critical Data Validation Points**:
- **Authentic Data Only**: Each step validates input data authenticity with ValueError exceptions
- **Zero Fallback Policy**: No default or synthetic values allowed - requires real data sources
- **Complete Traceability**: All calculations maintain full audit trails back to source data
- **Optimization Integration**: Financial analysis exclusively uses optimization solution results (~13-15 selected windows)
- **Database Persistence**: All step data stored in PostgreSQL with complete relationships and validation

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


## 🤝 Contributing

This project is developed as part of PhD research at Technische Universität Berlin. Contributions are welcome through:

1. **Issue Reports**: Bug reports and feature requests via GitHub Issues
2. **Code Contributions**: Pull requests for improvements and new features
3. **Academic Collaboration**: Research partnerships and methodology validation
4. **Data Validation**: Verification of calculations, standards implementation, and results
5. **Documentation**: Improvements to technical documentation and user guides

### Development Guidelines

- **Clean Codebase**: Only essential files - no development artifacts or unused documentation
- **Code Style**: PEP 8 compliance with comprehensive docstrings and academic references
- **Testing**: Validate against known benchmarks, ensure ISO standards compliance
- **Documentation**: Maintain README.md and replit.md accuracy with architectural changes
- **Data Integrity**: Use only authentic data sources - no fallback or synthetic values

## 📞 Contact & Attribution

**Research Context**: This platform is developed as part of PhD research at **Technische Universität Berlin**.

**Primary Researcher**: Mostafa Gabr  
**Research Profile**: [ResearchGate Profile](https://www.researchgate.net/profile/Mostafa-Gabr-4)  
**Institution**: Technische Universität Berlin, Faculty of Planning Building Environment  
**Research Focus**: Building-Integrated Photovoltaics, Educational Building Retrofitting

**Academic Collaboration**: Available for research partnerships, methodology validation, and peer review.

## 📜 License

This project is developed for academic research purposes at Technische Universität Berlin. 

**Usage Rights**:
- ✅ **Academic Research**: Free use for educational and research purposes
- ✅ **Non-Commercial**: Open access for non-profit applications
- ✅ **Citation Required**: Must cite research source and ResearchGate profile
- ❌ **Commercial Use**: Requires explicit permission and licensing agreement

**Citation Format**:
```
Gabr, M. (2025). BIPV Optimizer: Building-Integrated Photovoltaics Analysis Platform. 
PhD Research, Technische Universität Berlin. 
Available: https://www.researchgate.net/profile/Mostafa-Gabr-4
```

---

**Built with ❤️ at Technische Universität Berlin for advancing sustainable building technologies.**

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