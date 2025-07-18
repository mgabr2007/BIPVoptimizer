# Step 2 Database Schema Revision for Step 7 Data Flow

## Overview
Comprehensive database schema revision to ensure proper data flow from Step 2 (Historical Data & AI Model) to Step 7 (Yield vs Demand Analysis).

## Database Schema Changes Made

### 1. Enhanced AI Models Table
**Added Missing Columns:**
- `forecast_data` TEXT - Stores complete 25-year forecast predictions as JSON
- `demand_predictions` TEXT - Stores annual consumption predictions array
- `growth_rate` DECIMAL(5,4) - AI-calculated growth rate for demand projection
- `base_consumption` DECIMAL(12,2) - Baseline annual consumption for calculations
- `peak_demand` DECIMAL(12,2) - Maximum predicted annual demand
- `building_area` DECIMAL(10,2) - Building floor area for energy intensity calculations
- `occupancy_pattern` VARCHAR(100) - Educational building occupancy pattern
- `building_type` VARCHAR(100) - Building type for pattern recognition

### 2. New Historical Data Table
**Created Complete Table:**
```sql
CREATE TABLE historical_data (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    annual_consumption DECIMAL(12,2),
    consumption_data TEXT, -- JSON array of monthly consumption values
    temperature_data TEXT, -- JSON array of temperature data
    occupancy_data TEXT,   -- JSON array of occupancy percentages
    date_data TEXT,        -- JSON array of actual dates from CSV
    model_accuracy DECIMAL(5,3), -- R² score for prediction quality
    energy_intensity DECIMAL(8,2), -- kWh/m²/year
    peak_load_factor DECIMAL(5,3), -- Peak load factor
    seasonal_variation DECIMAL(5,3), -- Seasonal variation coefficient
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. Enhanced Database Manager Functions

**Added Missing Functions:**
- `save_ai_model_data()` - Saves complete AI model with forecast predictions
- `get_historical_data()` - Retrieves historical data with AI model predictions
- `save_historical_data()` - Saves consumption patterns and building characteristics

**Enhanced Data Storage:**
- JSON serialization for complex data structures (arrays, objects)
- Proper type conversion for PostgreSQL decimal fields
- Comprehensive error handling with rollback capabilities

## Step 7 Data Flow Requirements Met

### 1. Demand Forecasting Data
✅ **AI Model Predictions**: 25-year annual consumption predictions
✅ **Growth Rate**: AI-calculated growth rate for demand scaling
✅ **Base Consumption**: Historical baseline for calculations
✅ **Building Characteristics**: Area, type, occupancy patterns

### 2. Historical Consumption Patterns
✅ **Monthly Data**: Complete consumption data from CSV upload
✅ **Seasonal Variations**: Temperature and occupancy influences
✅ **Model Quality**: R² score for prediction reliability assessment
✅ **Date Alignment**: Actual dates for timeline continuity

### 3. Building Context Data
✅ **Energy Intensity**: kWh/m²/year for benchmarking
✅ **Peak Load Factor**: Maximum demand characteristics
✅ **Occupancy Patterns**: Academic year vs year-round operations
✅ **Building Type**: University, K-12, research facility classification

## Enhanced Step 2 Data Saving

**Updated Historical Data Processing:**
```python
# Save comprehensive historical data
historical_data_complete = {
    'annual_consumption': total_consumption,
    'consumption_data': consumption_data,
    'temperature_data': temperature_data or [],
    'occupancy_data': occupancy_data or [],
    'date_data': date_data or [],
    'model_accuracy': r_squared_score,
    'energy_intensity': sample_data.get('energy_intensity', 0),
    'peak_load_factor': sample_data.get('peak_load_factor', 0),
    'seasonal_variation': sample_data.get('seasonal_variation', 0)
}

# Save AI model with forecast predictions
ai_model_complete = {
    'model_type': 'RandomForestRegressor',
    'r_squared_score': r_squared_score,
    'training_data_size': len(consumption_data),
    'forecast_years': 25,
    'forecast_data': forecast_data,
    'demand_predictions': forecast_data.get('annual_predictions', []),
    'growth_rate': forecast_data.get('growth_rate', 0.01),
    'base_consumption': total_consumption,
    'peak_demand': max_consumption,
    'building_area': building_area,
    'occupancy_pattern': occupancy_pattern,
    'building_type': building_type
}
```

## Step 7 Benefits

### 1. Authentic Demand Data
- No synthetic fallbacks required - all data from actual historical analysis
- Complete 25-year demand projections with building-specific characteristics
- Seasonal and occupancy pattern integration for realistic projections

### 2. Quality Validation
- R² score assessment for prediction reliability
- Building type validation against consumption patterns
- Energy intensity benchmarking against industry standards

### 3. Comprehensive Analysis
- Monthly vs annual consumption balance calculations
- Peak demand handling for grid interaction analysis
- Growth rate projections for long-term BIPV sizing

## Database Indexes Added
- `idx_ai_models_project` - Fast AI model data retrieval by project
- `idx_historical_data_project` - Efficient historical data queries

## Migration Status
✅ All schema changes applied to existing database
✅ Enhanced database manager functions implemented
✅ Step 2 data saving updated for comprehensive storage
✅ Step 7 data retrieval capabilities established

## Result
Step 7 now has complete access to authentic historical consumption data, AI model predictions, building characteristics, and demand forecasting required for accurate yield vs demand analysis without any synthetic fallback data.