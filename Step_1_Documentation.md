# Step 1: Project Setup & Configuration Documentation

## Overview
Step 1 is the foundation of the BIPV Optimizer platform, where users configure their project parameters and establish the essential data sources needed for the entire analysis workflow. This step prepares location-specific data, weather API connections, and financial parameters that feed into all subsequent analysis steps.

## Main Settings & Configuration Options

### 1️⃣ Project Information
- **Project Name**: Descriptive name for the BIPV analysis project
  - Default: "BIPV Optimization Project"
  - Purpose: Used in reports and database storage
  - Validation: Text input, no special requirements

- **Currency**: Fixed to EUR (European Euro)
  - All financial calculations standardized to EUR
  - Automatic exchange rate conversion for international projects
  - Cannot be changed (enforced for consistency)

### 2️⃣ Location Selection
Two methods for specifying project location:

#### Interactive Map Method
- **Folium Map Interface**: Interactive OpenStreetMap with clickable location selection
- **Weather Station Markers**: Shows nearby WMO CLIMAT stations as reference points
- **Real-time Coordinate Updates**: Map click automatically updates coordinates
- **Location Name Detection**: Uses OpenWeatherMap reverse geocoding for detailed location names
- **Features**:
  - Zoom control and map dragging
  - Project marker with detailed popup information
  - Weather station markers with distance and metadata
  - Coordinate change threshold (0.02°) to prevent accidental updates

#### Manual Coordinates Method
- **Latitude Input**: Decimal degrees (-90.0 to 90.0)
- **Longitude Input**: Decimal degrees (-180.0 to 180.0)
- **Precision**: 6 decimal places for high accuracy
- **Validation**: Automatic coordinate range checking
- **Static Map Display**: Shows selected coordinates without interaction

### 3️⃣ Weather API Selection & Data Sources
Advanced hybrid weather API system with intelligent routing:

#### API Coverage Analysis
- **Automatic API Detection**: Determines best weather API based on location
- **Coverage Assessment**: Evaluates data quality and availability for each API
- **Recommendation Engine**: Suggests optimal API based on geographic coverage

#### Available Weather APIs
1. **TU Berlin Climate Portal** (Academic Grade)
   - **Coverage**: Berlin/Germany region
   - **Quality**: High-precision academic data
   - **Data Sources**: German meteorological stations
   - **Advantages**: Research-grade accuracy, local expertise

2. **OpenWeatherMap Global** (International Coverage)
   - **Coverage**: Worldwide
   - **Quality**: Standard commercial data
   - **Data Sources**: Global weather networks
   - **Advantages**: Universal coverage, real-time updates

#### API Selection Options
- **🤖 Automatic**: System recommends best API based on location
- **🎓 TU Berlin**: Force academic API (Berlin/Germany only)
- **🌍 OpenWeatherMap**: Force global API (worldwide coverage)

#### Weather Station Loading
- **Dynamic Station Fetching**: Loads stations from selected API
- **Station Metadata**: Name, distance, data quality, API source
- **API Validation**: Tests connection and data availability
- **Error Handling**: Fallback mechanisms for API failures

### 4️⃣ Data Integration & Configuration

#### Electricity Rate Integration
Comprehensive real-time electricity rate system:

**Live Rate Sources**:
- **German SMARD**: Federal Network Agency official data
- **UK Ofgem**: Official UK electricity market data
- **US EIA**: Energy Information Administration rates
- **EU Eurostat**: European statistical office data

**Manual Rate Fallback**:
- **Import Rate**: €0.10 - €0.50/kWh (cost to buy from grid)
- **Export Rate**: €0.05 - €0.20/kWh (payment for selling to grid)
- **Regional Guidance**: Location-specific rate recommendations
- **Validation**: Reasonableness checks on entered rates

#### Rate Configuration Options
- **Live API Integration**: Automatic rate fetching from official sources
- **Manual Override**: Custom rate input with validation
- **Location Detection**: Automatic API selection based on coordinates
- **Data Quality Indicators**: Source transparency and confidence levels

### 5️⃣ Configuration Review & Save
Final step to consolidate and save all project parameters:

#### Project Data Structure
```python
project_data = {
    'project_name': str,                    # User-defined project name
    'location': str,                        # Detailed location name
    'coordinates': {                        # Geographic coordinates
        'lat': float,                       # Latitude (decimal degrees)
        'lon': float                        # Longitude (decimal degrees)
    },
    'timezone': str,                        # Auto-detected timezone
    'currency': 'EUR',                      # Fixed currency
    'setup_complete': bool,                 # Completion status
    'location_method': str,                 # 'Interactive Map' or 'Manual Coordinates'
    'weather_api_choice': str,              # 'auto', 'tu_berlin', 'openweathermap'
    'selected_weather_station': dict,       # Selected weather station data
    'solar_parameters': dict,               # Location-specific solar parameters
    'electricity_rates': dict              # Rate configuration
}
```

## Key Functions & Processes

### Location Processing Functions

#### `get_location_from_coordinates(lat, lon)`
**Purpose**: Convert coordinates to detailed location names using OpenWeatherMap API
**Process**:
1. Makes reverse geocoding API calls with limit=10 for detailed hierarchy
2. Processes multiple API results for comprehensive location data
3. Extracts neighborhood, district, city, state, country information
4. Builds hierarchical location names with 3-component maximum
5. Provides fallback coordinate display if API fails

**Output**: Detailed location string (e.g., "Mitte, Berlin, Germany")

#### `find_nearest_stations(lat, lon, max_distance_km)`
**Purpose**: Locate nearby WMO CLIMAT weather stations for reference
**Process**:
1. Searches comprehensive WMO station database
2. Calculates haversine distances to all stations
3. Filters by maximum distance (500km default)
4. Returns sorted list by distance with metadata
5. Provides station names, countries, WMO IDs, elevations

**Output**: Pandas DataFrame with station information

### Weather API Management

#### Weather API Manager Integration
**Purpose**: Unified interface for multiple weather APIs
**Process**:
1. Analyzes location coordinates for API coverage
2. Determines optimal API based on geographic position
3. Fetches station data from selected API
4. Validates API access and data quality
5. Provides fallback mechanisms for API failures

#### Station Data Processing
**Purpose**: Standardize weather station data across different APIs
**Process**:
1. Extracts station metadata from API responses
2. Calculates distances from project location
3. Standardizes data formats between APIs
4. Provides quality indicators and source information
5. Stores in session state for workflow access

### Data Validation & Error Handling

#### Coordinate Validation
- **Range Checking**: Validates latitude (-90° to 90°) and longitude (-180° to 180°)
- **Precision Limits**: Enforces 6 decimal places for coordinate accuracy
- **Change Detection**: Prevents unnecessary updates from minor coordinate changes
- **Error Messages**: Clear user feedback for invalid coordinates

#### API Error Handling
- **Connection Timeouts**: 10-second timeout for API requests
- **Fallback Mechanisms**: Automatic API switching on failures
- **User Feedback**: Clear error messages with suggested actions
- **Data Persistence**: Maintains functionality even with API failures

### Data Flow Integration

#### Step 1 → Step 3 (Weather Integration)
- **Location Coordinates**: Precise coordinates for solar position calculations
- **Selected Weather Station**: Meteorological data source for TMY generation
- **API Configuration**: Weather service settings for authentic data retrieval
- **Timezone Information**: Proper time zone conversion for solar calculations

#### Step 1 → Steps 7-9 (Financial Analysis)
- **Electricity Rates**: Import/export rates for economic calculations
- **Currency Settings**: EUR standardization for financial modeling
- **Location Parameters**: Regional economic factors and market conditions

#### Step 1 → Step 10 (Reporting)
- **Project Metadata**: Report headers and location context
- **Configuration Summary**: Technical specifications and analysis parameters
- **Data Source Documentation**: Traceability for scientific transparency

## Technical Implementation Details

### Session State Management
- **project_data**: Main project configuration object
- **map_coordinates**: Current map position and coordinate tracking
- **location_name**: Detailed location string from reverse geocoding
- **selected_weather_station**: Active weather station configuration
- **weather_validated**: API validation status
- **live_electricity_rates**: Real-time rate data from APIs

### Database Integration
- **Project Storage**: Saves complete project configuration to PostgreSQL
- **Data Persistence**: Maintains project state across sessions
- **Project ID Generation**: Creates unique identifiers for workflow tracking
- **Configuration Retrieval**: Loads saved projects for continued analysis

### Map Integration (Folium + Streamlit)
- **Interactive Map**: Folium map with click detection via streamlit-folium
- **Marker System**: Project location and weather station markers
- **Coordinate Updates**: Real-time coordinate tracking with change detection
- **Visual Feedback**: Map markers with detailed popup information
- **Performance Optimization**: Prevents unnecessary map re-renders

### Error Recovery Systems
- **API Fallbacks**: Multiple weather API options with automatic switching
- **Data Validation**: Comprehensive input validation with user feedback
- **Session Recovery**: Maintains progress even with connection issues
- **Graceful Degradation**: Continues functionality with limited data

## Success Indicators

### Project Setup Complete
- ✅ Project name configured
- ✅ Location selected with coordinates
- ✅ Weather API chosen and validated
- ✅ Weather station loaded from API
- ✅ Electricity rates configured (live or manual)
- ✅ Data saved to database successfully

### Ready for Step 2
- **Location Data**: Coordinates and detailed location name available
- **Weather Configuration**: API selection and station data ready
- **Financial Parameters**: Electricity rates configured for economic analysis
- **Database Integration**: Project ID generated for workflow tracking

## User Experience Features

### Unified Success Messages
- Consolidated feedback system prevents message clutter
- Clear success indicators for each configuration step
- Comprehensive project summary after successful save
- Progress tracking with visual indicators

### Data Usage Transparency
- Clear explanations of how each data point is used
- Workflow connections between steps documented
- Data source attribution for transparency
- Academic references for methodology validation

### Performance Optimizations
- Map rendering optimized to prevent continuous refreshing
- Coordinate change thresholds to avoid unnecessary updates
- Session state management for efficient data flow
- API request optimization with caching and error handling

This comprehensive setup in Step 1 provides the foundation for all subsequent BIPV analysis steps, ensuring accurate, location-specific, and scientifically validated analysis throughout the entire workflow.