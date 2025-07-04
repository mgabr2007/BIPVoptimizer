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

- Python 3.11+
- PostgreSQL database
- OpenWeatherMap API key
- Replit environment (recommended)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/bipv-optimizer.git
cd bipv-optimizer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export OPENWEATHER_API_KEY="your_api_key_here"
export DATABASE_URL="postgresql://user:password@host:port/database"
```

4. Run the application:
```bash
streamlit run app.py --server.port 5000
```

## 🏗️ Architecture

### 11-Step Workflow

1. **Welcome & Introduction** - Platform overview and methodology
2. **Project Setup** - Location selection with weather station integration
3. **Historical Data Analysis** - AI model training for demand prediction
4. **Weather Integration** - TMY generation with ISO standards
5. **Facade Extraction** - BIM data processing for building elements
6. **Radiation Analysis** - Solar modeling with shading calculations
7. **PV Specification** - BIPV glass technology parameters
8. **Yield vs Demand** - Energy balance analysis
9. **Optimization** - Multi-objective genetic algorithms
10. **Financial Analysis** - Economic viability assessment
11. **Comprehensive Reporting** - Scientific reports with real calculated values

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
├── app.py                      # Main application entry point
├── core/                       # Core mathematical functions
│   ├── solar_math.py          # Solar calculations & utilities
│   └── carbon_factors.py      # Grid CO₂ intensity database
├── pages_modules/              # Workflow step implementations
│   ├── project_setup.py       # Location & configuration
│   ├── historical_data.py     # AI model training
│   ├── weather_environment.py # TMY generation
│   ├── facade_extraction.py   # BIM data processing
│   ├── radiation_grid.py      # Solar radiation analysis
│   ├── pv_specification.py    # BIPV system design
│   ├── yield_demand.py        # Energy balance calculations
│   ├── optimization.py        # Genetic algorithm optimization
│   ├── financial_analysis.py  # Economic assessment
│   └── reporting.py           # Comprehensive report generation
├── utils/                      # Utility functions
│   ├── consolidated_data_manager.py # Centralized data management
│   ├── comprehensive_report_fixed.py # Report generation engine
│   └── color_schemes.py       # UI styling utilities
├── components/                 # UI components
│   └── workflow_visualization.py # Progress tracking
├── database_manager.py         # PostgreSQL operations
└── attached_assets/           # Images and resources
```

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

## 📊 Data Sources

### Weather Data
- **Primary**: WMO CLIMAT stations (40+ global locations)
- **API**: OpenWeatherMap for current/historical data
- **Standards**: ISO 15927-4 compliant TMY generation

### Economic Data
- **Electricity Rates**: Real-time APIs (SMARD, Ofgem, EIA, Eurostat)
- **Currency**: Standardized EUR calculations with exchange rates
- **CO₂ Factors**: Official sources (IEA, EEA, national TSOs)

### Building Data
- **BIM Integration**: Revit/CAD model extraction
- **Element Types**: Windows, curtain walls, glazing systems
- **Properties**: Dimensions, orientations, glass areas, levels

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

## 🤝 Contributing

This project is developed as part of PhD research at Technische Universität Berlin. Contributions are welcome through:

1. **Issue Reports**: Bug reports and feature requests
2. **Code Contributions**: Pull requests for improvements
3. **Academic Collaboration**: Research partnerships
4. **Data Validation**: Verification of calculations and standards

### Development Guidelines

- Follow PEP 8 Python style guidelines
- Maintain comprehensive docstrings
- Include unit tests for new functionality
- Update documentation for API changes
- Preserve academic attribution and references

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