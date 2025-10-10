# BIPV Optimizer

## Overview
BIPV Optimizer is a comprehensive Building Integrated Photovoltaics (BIPV) optimization platform built with Streamlit for academic research at Technische Universität Berlin. It provides a complete 10-step workflow, with a bonus AI consultation (10+1), for analyzing and optimizing BIPV system installations where semi-transparent PV cells replace existing window glass using exact building element data. The platform features intelligent window type selection based on historical significance and architectural constraints, ensuring only suitable windows are analyzed throughout the workflow. It covers interactive map-based location selection, AI model training, ISO-compliant TMY generation, BIM data processing with window filtering, radiation analysis on selected windows, BIPV glass specification, multi-objective optimization, financial analysis, and AI-powered research consultation. Its business vision is to accelerate the adoption of BIPV technologies by providing a robust, research-backed tool for precise performance and financial forecasting of viable window installations.

## Recent Changes & Updates (October 2025)

### BIPV Manufacturer Database Update (2025-10-10)
- **Replaced Legacy Manufacturers**: Updated all 5 BIPV glass manufacturers with verified 2025 commercial and research options
- **New Manufacturers**: Polysolar PS-CT (UK, 13.5%), Climacy CLI400M10 (Switzerland, 17.25%), UbiQD WENDOW (US, 4.3%), CitySolar Tandem (EU, 12.3%), Tohoku Ultra-Clear (Japan, 2%)
- **Verified Specifications**: All efficiency, transparency, and cost data verified against 2025 European market research
- **Market-Aligned Pricing**: Costs range from €225-420/m² based on current BIPV glass market pricing
- **Technology Diversity**: Includes monocrystalline, quantum dot, perovskite-organic tandem, and ultra-transparent options

### Data Export & Financial Analysis Enhancements (September 2025)
- **Fixed Financial Analysis CSV Export**: Resolved issue where financial analysis export button showed "ready" status but failed to trigger downloads
- **Complete Cash Flow Integration**: Added comprehensive 25-year cash flow projections, sensitivity analysis, and structured financial data to CSV exports
- **Optimized Window Selection Export**: Fixed CSV export to show only optimization solution results (~13-15 selected windows) instead of all analyzed elements (146 windows)
- **Enhanced Database Storage**: Updated database schema to store complete financial analysis data including cash flow details for proper export functionality

### Technical Infrastructure Updates
- **Database Schema Enhancement**: Comprehensive PostgreSQL schema supporting all workflow steps with proper data relationships
- **Clean Architecture**: Maintained modular design with essential components only, removing unused development files
- **Performance Optimizations**: Streamlined data flow between optimization results and financial analysis for accurate calculations
- **Export System Validation**: All CSV exports now include authentic data with proper filtering and data integrity checks

### Quality Assurance Improvements
- **Data Validation**: Enhanced verification that financial analysis uses authentic optimization solution data only
- **Error Handling**: Improved error messages and data validation throughout the workflow
- **Documentation Accuracy**: Updated technical documentation to reflect current system architecture and capabilities

## User Preferences

**Communication Style**: Simple, everyday language avoiding technical jargon for non-technical users.

**UI Preferences**:
- Clean sidebar without headers, navigation at bottom of pages for improved user experience
- No balloon celebrations or animations for professional appearance
- Professional BIPV Optimizer branding with light green color scheme and OptiSunny character integration

**Technical Preferences**:
- **CRITICAL PhD Research Integrity**: ZERO tolerance for fallback data - all calculations must use authentic database sources only
- **Comprehensive Fallback Elimination (2025-08-21)**: Systematically removed ALL default values, placeholder data, and fallback mechanisms across entire platform
- **Enhanced Data Export (2025-09-05)**: Fixed financial analysis CSV export with complete 25-year cash flow projections, sensitivity analysis, and structured data format
- **Authentic Data Requirements**: Only real TMY and BIM data used - no synthetic/estimated values allowed
- Complete 11-step workflow with proper step dependencies and validation
- PostgreSQL database persistence with comprehensive schema supporting all workflow steps
- Multi-source API integration for weather data (TU Berlin + OpenWeatherMap) with explicit error handling
- **Optimized Window Selection**: CSV export now correctly filters to show only optimized solution elements (~13-15 windows) instead of all analyzed elements (146)
- Comprehensive reporting with real calculated values and complete data traceability
- Research-grade academic attribution to TU Berlin and Mostafa Gabr PhD research
- Element duplication prevention system ensuring each building element is processed exactly once
- **North Facade Configuration**: User-configurable facade orientation settings with include_north_facade database field

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web application with a clean, professional UI.
- **Navigation**: 11-step workflow system with dynamic progress tracking.
- **Visualization**: Plotly for interactive charts, maps (Folium), and dashboards.
- **State Management**: Streamlit session state with PostgreSQL persistence.
- **UI Components**: Professional BIPV Optimizer branding with OptiSunny character.

### Backend Architecture
- **Language**: Python 3.11 with comprehensive scientific computing stack (NumPy 1.24.4, Pandas 2.0.3, scikit-learn 1.7.0).
- **Structure**: Clean modular design with essential components only (pages_modules/, services/, utils/, core/).
- **Data Management**: Unified data flow system with PostgreSQL 16 persistence and comprehensive database schema.
- **Data Integrity (2025-08-21)**: All modules enforce authentic data requirements with ValueError exceptions for missing data
- **Export Functionality (2025-09-05)**: Complete CSV export system with optimized window selection, financial analysis data, and cash flow projections
- **Machine Learning**: Scikit-learn RandomForestRegressor for demand prediction with R² performance tracking.
- **Optimization**: DEAP genetic algorithms (NSGA-II) for multi-objective optimization (cost, yield, ROI) with Pareto-optimal solution generation.
- **APIs**: Multi-source integration for weather data and real-time electricity rates with explicit error handling.

### Core Workflow Components
- **Project Setup**: Interactive map for location selection, geocoding, and weather station integration.
- **Historical Data**: AI model training for energy consumption using RandomForestRegressor.
- **Weather & Environment**: ISO 15927-4 compliant TMY generation and environmental shading factors.
- **Window Selection & BIM Extraction**: Mandatory BIM data upload (CSV) with window type filtering for BIPV suitability based on historical significance and architectural constraints.
- **Radiation & Shading Analysis**: pvlib for solar position, irradiance modeling, and self-shading calculations on selected window types only.
- **BIPV Glass Specification**: Built-in database with 5 commercial BIPV glass types and customization for selected windows.
- **Yield vs Demand Analysis**: Compares PV energy generation from selected windows with predicted building demand.
- **Multi-Objective Optimization**: NSGA-II genetic algorithm for cost, yield, and ROI optimization of selected window installations.
- **Financial & Environmental Analysis**: NPV, IRR, payback analysis with 25-year cash flow projections, sensitivity analysis, and real-time electricity rates integration.
- **Comprehensive Reporting**: Multi-format export system (CSV, HTML) with complete data traceability and interactive Plotly visualizations.
- **Data Export System**: Optimized CSV exports for selected window solutions, complete financial analysis data, and comprehensive project reports.
- **Bonus AI Consultation**: Perplexity AI integration for research-based BIPV recommendations using authentic project data.

## External Dependencies

### Core Framework & Data Processing
- **streamlit (1.46.0+)**: Web application framework with enhanced UI components
- **pandas (2.0.3)**: Data manipulation and analysis with optimized performance
- **numpy (1.24.4)**: Numerical computing with stable version compatibility
- **plotly (6.1.2+)**: Interactive visualization and chart generation
- **folium (0.20.0+)**: Interactive mapping and geographical visualization
- **streamlit-folium (0.25.0+)**: Streamlit integration for Folium maps

### Scientific Computing & Machine Learning
- **scikit-learn (1.7.0+)**: Machine learning algorithms and model validation
- **pvlib (0.13.0+)**: Professional solar energy modeling and calculations
- **deap (1.4.3+)**: Genetic algorithm optimization framework for NSGA-II
- **pytz (2025.2+)**: Comprehensive timezone handling and conversions

### Database & Data Persistence
- **psycopg2-binary (2.9.10+)**: PostgreSQL database connectivity and operations
- **asyncpg (0.30.0+)**: Asynchronous PostgreSQL operations for performance
- **pydantic (2.11.7+)**: Data validation and settings management
- **pandera (0.25.0+)**: DataFrame validation and quality assurance

### Report Generation & Export
- **reportlab (4.4.3+)**: PDF report generation with professional formatting
- **python-docx (1.2.0+)**: Word document generation for comprehensive reports
- **kaleido (1.0.0+)**: Static image export for Plotly visualizations
- **openpyxl (3.1.5+)**: Excel file processing and export capabilities

### API Integration & External Services
- **requests (2.32.4+)**: HTTP client for weather and electricity rate APIs
- **beautifulsoup4 (4.13.4+)**: Web scraping for data extraction
- **trafilatura (2.0.0+)**: Advanced web content extraction
- **OpenWeatherMap API**: Global weather data and meteorological services
- **TU Berlin Climate Portal**: Academic-grade meteorological data for Germany
- **Perplexity AI**: Advanced AI research consultation and literature analysis
- **German SMARD, UK Ofgem, US EIA, EU Eurostat**: Official electricity rate APIs

### Development & Quality Assurance
- **pytest (8.4.1+)** & **pytest-asyncio (1.0.0+)**: Comprehensive testing framework
- **great-expectations (0.18.22+)**: Data quality validation and monitoring
- **sentry-sdk (2.33.0+)**: Error monitoring and performance tracking
- **loguru (0.7.3+)**: Advanced logging with structured output
- **streamlit-extras (0.7.5+)**: Extended Streamlit components and utilities