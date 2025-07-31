# BIPV Optimizer

## Overview
BIPV Optimizer is a comprehensive Building Integrated Photovoltaics (BIPV) optimization platform built with Streamlit for academic research at Technische Universität Berlin. It provides a complete 10-step workflow, with a bonus AI consultation (10+1), for analyzing and optimizing BIPV system installations where semi-transparent PV cells replace existing window glass using exact building element data. The platform covers interactive map-based location selection, AI model training, ISO-compliant TMY generation, BIM data processing, radiation analysis, BIPV glass specification, multi-objective optimization, financial analysis, and AI-powered research consultation. Its business vision is to accelerate the adoption of BIPV technologies by providing a robust, research-backed tool for precise performance and financial forecasting.

## User Preferences

**Communication Style**: Simple, everyday language avoiding technical jargon for non-technical users.

**UI Preferences**:
- Clean sidebar without headers, navigation at bottom of pages for improved user experience
- No balloon celebrations or animations for professional appearance
- Professional BIPV Optimizer branding with light green color scheme and OptiSunny character integration

**Technical Preferences**:
- Authentic data requirements - zero fallback values, only real TMY and BIM data used
- Complete 11-step workflow with proper step dependencies and validation
- PostgreSQL database persistence for reliable project data management
- Multi-source API integration for weather data (TU Berlin + OpenWeatherMap)
- Comprehensive reporting with real calculated values instead of placeholder data
- Research-grade academic attribution to TU Berlin and Mostafa Gabr PhD research
- Element duplication prevention system ensuring each building element is processed exactly once

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web application with a clean, professional UI.
- **Navigation**: 11-step workflow system with dynamic progress tracking.
- **Visualization**: Plotly for interactive charts, maps (Folium), and dashboards.
- **State Management**: Streamlit session state with PostgreSQL persistence.
- **UI Components**: Professional BIPV Optimizer branding with OptiSunny character.

### Backend Architecture
- **Language**: Python 3.11 with a comprehensive scientific computing stack.
- **Structure**: Modular design (pages_modules/, services/, utils/, core/).
- **Data Management**: ConsolidatedDataManager for unified data flow and PostgreSQL 16 for persistence.
- **Machine Learning**: Scikit-learn RandomForestRegressor for demand prediction with R² tracking.
- **Optimization**: DEAP genetic algorithms (NSGA-II) for multi-objective optimization (cost, yield, ROI).
- **APIs**: Multi-source integration for weather data and electricity rates.

### Core Workflow Components
- **Project Setup**: Interactive map for location selection, geocoding, and weather station integration.
- **Historical Data**: AI model training for energy consumption using RandomForestRegressor.
- **Weather & Environment**: ISO 15927-4 compliant TMY generation and environmental shading factors.
- **Facade & Window Extraction**: Mandatory BIM data upload (CSV) for building element geometry.
- **Radiation & Shading Analysis**: pvlib for solar position, irradiance modeling, and self-shading calculations.
- **BIPV Glass Specification**: Built-in database with 5 commercial BIPV glass types and customization.
- **Yield vs Demand Analysis**: Compares PV energy generation with predicted building demand.
- **Multi-Objective Optimization**: NSGA-II genetic algorithm for cost, yield, and ROI optimization.
- **Financial & Environmental Analysis**: NPV, IRR, payback analysis with real-time electricity rates and CO₂ savings.
- **Comprehensive Reporting**: Consolidated reporting system with HTML reports and interactive Plotly charts.
- **Bonus AI Consultation**: Perplexity AI integration for research-based BIPV recommendations.

## External Dependencies

- **streamlit**: Web application framework.
- **pandas**: Data manipulation and analysis.
- **numpy**: Numerical computing.
- **plotly**: Interactive visualization.
- **scikit-learn**: Machine learning.
- **pvlib**: Solar energy modeling.
- **deap**: Genetic algorithm optimization.
- **requests**: HTTP client.
- **OpenWeatherMap API**: Real-time and historical weather data.
- **TU Berlin Climate Portal**: Academic-grade meteorological data for Berlin/Germany.
- **PostgreSQL**: Database for data persistence.
- **Perplexity AI**: For bonus AI consultation.
- **pytz**: Timezone handling.
- **openpyxl**: Excel file export.
- **German SMARD, UK Ofgem, US EIA, EU Eurostat**: Official APIs for real-time electricity rates.