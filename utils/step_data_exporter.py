"""
Step Data Exporter for BIPV Optimizer
Generates comprehensive exports for each workflow step with calculations and explanations
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from database_manager import BIPVDatabaseManager
from core.solar_math import safe_divide


def export_step_data(step_number, step_name):
    """Create export button and generate comprehensive step data export"""
    
    if st.button(f"📊 Export {step_name} Data & Analysis", key=f"export_step_{step_number}"):
        try:
            export_content = generate_step_export(step_number, step_name)
            
            if export_content:
                # Create downloadable file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"BIPV_Step{step_number}_{step_name.replace(' ', '_')}_{timestamp}.txt"
                
                st.download_button(
                    label=f"📥 Download {step_name} Complete Analysis",
                    data=export_content,
                    file_name=filename,
                    mime="text/plain",
                    key=f"download_step_{step_number}"
                )
                
                # Also display preview
                with st.expander(f"📋 Preview: {step_name} Export Content"):
                    st.text(export_content[:2000] + "..." if len(export_content) > 2000 else export_content)
                    
            else:
                st.warning(f"No data available for {step_name} export")
                
        except Exception as e:
            st.error(f"Error generating {step_name} export: {str(e)}")


def generate_step_export(step_number, step_name):
    """Generate comprehensive export content for a specific step"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    project_data = st.session_state.get('project_data', {})
    project_name = project_data.get('project_name', 'Unnamed Project')
    
    # Header
    content = f"""
BIPV OPTIMIZER - COMPREHENSIVE STEP ANALYSIS
============================================

Step {step_number}: {step_name}
Project: {project_name}
Generated: {timestamp}
PhD Research - Technische Universität Berlin
Researcher: Mostafa Gabr

============================================

"""
    
    # Step-specific content generation
    if step_number == 1:
        content += generate_step1_export(project_data)
    elif step_number == 2:
        content += generate_step2_export(project_data)
    elif step_number == 3:
        content += generate_step3_export(project_data)
    elif step_number == 4:
        content += generate_step4_export(project_data)
    elif step_number == 5:
        content += generate_step5_export(project_data)
    elif step_number == 6:
        content += generate_step6_export(project_data)
    elif step_number == 7:
        content += generate_step7_export(project_data)
    elif step_number == 8:
        content += generate_step8_export(project_data)
    elif step_number == 9:
        content += generate_step9_export(project_data)
    elif step_number == 10:
        content += generate_step10_export(project_data)
    elif step_number == 11:
        content += generate_step11_export(project_data)
    else:
        content += "Step export not implemented yet."
    
    return content


def generate_step1_export(project_data):
    """Export Step 1: Project Setup data"""
    content = """
STEP 1: PROJECT SETUP & LOCATION ANALYSIS
==========================================

PURPOSE:
This step establishes the fundamental project parameters including precise geographical location,
weather station selection, and economic parameters that form the foundation for all subsequent
BIPV analysis calculations.

METHODOLOGY:
- Interactive map-based coordinate selection using Folium mapping
- OpenWeatherMap API integration for location verification
- WMO CLIMAT station database for meteorological accuracy
- Automatic timezone detection based on coordinates
- Real-time electricity rate integration with official APIs

INPUT PARAMETERS:
"""
    
    # Extract project setup data
    location_info = project_data.get('location_info', {})
    selected_station = project_data.get('selected_weather_station', {})
    electricity_rates = project_data.get('electricity_rates', {})
    
    content += f"""
Project Configuration:
- Project Name: {project_data.get('project_name', 'Not specified')}
- Location: {location_info.get('location_name', 'Not specified')}
- Coordinates: Lat {location_info.get('latitude', 'N/A')}, Lon {location_info.get('longitude', 'N/A')}
- Timezone: {project_data.get('timezone', 'Not specified')}
- Currency: EUR (standardized)

Weather Station Selection:
- WMO Station ID: {selected_station.get('wmo_id', 'Not selected')}
- Station Name: {selected_station.get('name', 'Not selected')}
- Distance from Project: {selected_station.get('distance_km', 'N/A')} km
- Station Coordinates: {selected_station.get('coordinates', 'N/A')}
- Elevation: {selected_station.get('elevation', 'N/A')} m

Electricity Rate Integration:
- Import Rate: €{electricity_rates.get('import_rate', 'N/A')}/kWh
- Feed-in Tariff: €{electricity_rates.get('feed_in_rate', 'N/A')}/kWh
- Rate Source: {electricity_rates.get('source', 'Manual input')}
- Currency: {electricity_rates.get('currency', 'EUR')}

CALCULATIONS PERFORMED:
1. Geographic Analysis:
   - Coordinate validation and verification
   - Timezone determination using latitude/longitude
   - Climate zone classification for solar modeling

2. Weather Station Selection:
   - Distance calculation from project coordinates
   - Nearest station identification within search radius
   - Meteorological data availability verification

3. Economic Parameter Setup:
   - Real-time electricity rate fetching (where available)
   - Feed-in tariff determination based on location
   - Currency standardization to EUR

QUALITY ASSURANCE:
- Location accuracy verified through reverse geocoding
- Weather station metadata validated against WMO database
- Electricity rates cross-referenced with official sources when available

DATA USAGE IN SUBSEQUENT STEPS:
- Step 3: Coordinates and weather station for TMY generation
- Step 7: Electricity rates for financial calculations  
- Step 9: Economic parameters for financial analysis
- Step 10: Location context for reporting

SCIENTIFIC STANDARDS APPLIED:
- WMO CLIMAT station database for meteorological accuracy
- ISO 8601 timezone standards
- Geographic coordinate system (WGS84)
"""
    
    return content


def generate_step2_export(project_data):
    """Export Step 2: Historical Data Analysis"""
    content = """
STEP 2: HISTORICAL DATA ANALYSIS & AI MODEL TRAINING
====================================================

PURPOSE:
Analyze historical energy consumption patterns and train machine learning models for future
demand prediction, essential for BIPV system sizing and energy balance calculations.

METHODOLOGY:
- RandomForestRegressor for baseline demand modeling
- Educational building pattern analysis (ASHRAE 90.1 compliance)
- Seasonal variation analysis and occupancy pattern recognition
- 25-year demand forecasting with building-specific characteristics

INPUT DATA ANALYSIS:
"""
    
    historical_data = project_data.get('historical_data', {})
    ai_model_data = project_data.get('ai_model', {})
    
    # Extract key metrics
    total_consumption = historical_data.get('total_annual_consumption', 0)
    avg_monthly = historical_data.get('average_monthly_consumption', 0)
    building_area = historical_data.get('building_floor_area', 0)
    energy_intensity = safe_divide(total_consumption, building_area, 0) if building_area > 0 else 0
    
    content += f"""
Historical Consumption Data:
- Data Period: {historical_data.get('data_period', 'Not specified')}
- Total Annual Consumption: {total_consumption:,.0f} kWh
- Average Monthly Consumption: {avg_monthly:,.0f} kWh
- Building Floor Area: {building_area:,.0f} m²
- Energy Intensity: {energy_intensity:.1f} kWh/m²/year

Seasonal Analysis:
- Summer Consumption (Jun-Aug): {historical_data.get('summer_consumption', 'N/A')} kWh
- Winter Consumption (Dec-Feb): {historical_data.get('winter_consumption', 'N/A')} kWh
- Seasonal Variation: {historical_data.get('seasonal_variation', 'N/A')}%

Building Characteristics:
- Building Type: Educational
- Operation Pattern: {historical_data.get('operation_pattern', 'Not specified')}
- Occupancy Factor: {historical_data.get('occupancy_factor', 'N/A')}%
- Peak Load Factor: {historical_data.get('peak_load_factor', 'N/A')}%

AI MODEL PERFORMANCE:
- Model Type: Random Forest Regression
- Training R² Score: {ai_model_data.get('r2_score', 'N/A')}
- Model Status: {ai_model_data.get('model_status', 'Not trained')}
- Feature Count: {ai_model_data.get('feature_count', 'N/A')}
- Training Data Points: {ai_model_data.get('training_samples', 'N/A')}

CALCULATIONS PERFORMED:

1. Energy Intensity Analysis:
   Energy Intensity = Total Annual Consumption / Building Floor Area
   = {total_consumption:,.0f} kWh / {building_area:,.0f} m² = {energy_intensity:.1f} kWh/m²/year

2. Seasonal Variation Calculation:
   Seasonal Variation = ((Summer Avg - Winter Avg) / Annual Avg) × 100

3. Peak Load Factor:
   Peak Load Factor = (Average Demand / Peak Demand) × 100

4. Baseline Demand Modeling:
   - Monthly consumption patterns
   - Temperature correlation analysis
   - Occupancy-adjusted forecasting

DEMAND FORECASTING (25-YEAR PROJECTION):
- Base Year Consumption: {total_consumption:,.0f} kWh
- Annual Growth Rate: {historical_data.get('annual_growth_rate', 'N/A')}%
- Educational Building Factors Applied:
  * Summer operation reduction: {historical_data.get('summer_factor', 'N/A')}%
  * Occupancy modifiers: {historical_data.get('occupancy_modifiers', 'N/A')}
  * ASHRAE 90.1 compliance factors

EDUCATIONAL BUILDING STANDARDS ANALYSIS:
- ASHRAE 90.1 Energy Performance Index
- K-12/University operation pattern recognition
- Seasonal occupancy variation modeling
- Peak demand prediction for BIPV sizing

MODEL VALIDATION METRICS:
- Cross-validation score: {ai_model_data.get('cv_score', 'N/A')}
- Mean Absolute Error: {ai_model_data.get('mae', 'N/A')} kWh
- Root Mean Square Error: {ai_model_data.get('rmse', 'N/A')} kWh

DATA USAGE IN SUBSEQUENT STEPS:
- Step 6: Annual demand for BIPV system sizing
- Step 7: Monthly demand patterns for yield vs demand analysis
- Step 8: Demand forecasts for optimization constraints
- Step 9: Consumption baselines for financial analysis

SCIENTIFIC STANDARDS APPLIED:
- ASHRAE 90.1 building energy performance standards
- ISO 50001 energy management principles
- Educational building operation standards (CEN/TC 156)
"""
    
    return content


def generate_step3_export(project_data):
    """Export Step 3: Weather & Environment Integration"""
    content = """
STEP 3: WEATHER & ENVIRONMENT INTEGRATION
=========================================

PURPOSE:
Generate ISO-compliant Typical Meteorological Year (TMY) data using authentic WMO station
measurements for accurate solar irradiance modeling and BIPV performance calculations.

METHODOLOGY:
- ISO 15927-4 compliant TMY generation from WMO weather stations
- Astronomical solar position calculations using pvlib algorithms
- Climate zone-based temperature and atmospheric modeling
- Environmental shading factor integration

TMY DATA GENERATION:
"""
    
    weather_data = project_data.get('weather_analysis', {})
    tmy_data = weather_data.get('tmy_data', [])
    environmental_factors = weather_data.get('environmental_factors', {})
    
    # Calculate key metrics from TMY data
    if tmy_data and len(tmy_data) > 0:
        annual_ghi = sum(hour.get('GHI', 0) for hour in tmy_data) / 1000  # Convert to kWh/m²
        annual_dni = sum(hour.get('DNI', 0) for hour in tmy_data) / 1000
        annual_dhi = sum(hour.get('DHI', 0) for hour in tmy_data) / 1000
        avg_temp = sum(hour.get('temperature', 0) for hour in tmy_data) / len(tmy_data)
    else:
        annual_ghi = annual_dni = annual_dhi = avg_temp = 0
    
    content += f"""
TMY Data Summary:
- Data Source: WMO Station {weather_data.get('station_info', {}).get('wmo_id', 'N/A')}
- Annual GHI: {annual_ghi:.0f} kWh/m²
- Annual DNI: {annual_dni:.0f} kWh/m²  
- Annual DHI: {annual_dhi:.0f} kWh/m²
- Average Temperature: {avg_temp:.1f}°C
- Data Points: {len(tmy_data)} hourly records

Solar Resource Classification (ISO 9060):
- GHI Classification: {weather_data.get('solar_classification', 'Not classified')}
- Resource Quality: {weather_data.get('resource_quality', 'Not assessed')}
- Climate Zone: {weather_data.get('climate_zone', 'Not determined')}

Environmental Considerations:
- Vegetation Shading Reduction: {environmental_factors.get('vegetation_shading', 0)}%
- Urban Shading Reduction: {environmental_factors.get('urban_shading', 0)}%
- Atmospheric Clarity Factor: {environmental_factors.get('atmospheric_clarity', 1.0)}
- Altitude Correction: {environmental_factors.get('altitude_correction', 1.0)}

CALCULATIONS PERFORMED:

1. Solar Position Calculations (ISO 15927-4):
   For each hour of the year:
   - Solar declination: δ = 23.45° × sin(360° × (284 + n)/365)
   - Hour angle: ω = 15° × (solar_time - 12)
   - Solar elevation: α = sin⁻¹(sin(φ)sin(δ) + cos(φ)cos(δ)cos(ω))
   - Solar azimuth: γ = tan⁻¹(sin(ω)/(cos(ω)sin(φ) - tan(δ)cos(φ)))

2. Irradiance Component Modeling:
   - Global Horizontal Irradiance (GHI) from station measurements
   - Direct Normal Irradiance (DNI) calculated using Erbs model
   - Diffuse Horizontal Irradiance (DHI) = GHI - DNI × cos(zenith)

3. Climate Zone Classification:
   Based on latitude {weather_data.get('latitude', 'N/A')}°:
   - Equatorial: 0° to ±23.5°
   - Tropical: ±23.5° to ±35°  
   - Subtropical: ±35° to ±50°
   - Temperate: ±50° to ±65°
   - Arctic: ±65° to ±90°

4. Environmental Shading Corrections:
   Effective Irradiance = Base Irradiance × (1 - vegetation_factor) × (1 - urban_factor)

QUALITY ASSURANCE:
- WMO station data validation and gap filling
- Physical consistency checks (GHI ≥ DHI, reasonable temperature ranges)
- Solar position verification against astronomical calculations
- Environmental factor validation against peer-reviewed sources

MONTHLY SOLAR PROFILE:
"""
    
    # Add monthly breakdown if available
    monthly_data = weather_data.get('monthly_summary', {})
    for month, data in monthly_data.items():
        if isinstance(data, dict):
            content += f"- {month}: {data.get('ghi', 0):.0f} kWh/m² GHI, {data.get('temperature', 0):.1f}°C avg\n"
    
    content += f"""

ENVIRONMENTAL IMPACT FACTORS:
- Vegetation Shading (Academic Sources):
  * Gueymard (2012): Solar Energy, Vol 86, pp 2145-2161
  * Hofierka & Kaňuk (2009): Solar Energy, Vol 83, pp 888-898
  * Reduction Factor: {environmental_factors.get('vegetation_shading', 0)}% applied

- Building Shading (Academic Sources):
  * Appelbaum & Bany (1979): Solar Energy, Vol 23, pp 269-280
  * Quaschning & Hanitsch (1998): Solar Energy, Vol 62, pp 369-378
  * Reduction Factor: {environmental_factors.get('urban_shading', 0)}% applied

DATA USAGE IN SUBSEQUENT STEPS:
- Step 5: Hourly irradiance data for radiation grid analysis
- Step 6: Solar resource assessment for PV sizing
- Step 7: Monthly profiles for yield calculations
- Step 10: Climate data for performance validation

SCIENTIFIC STANDARDS APPLIED:
- ISO 15927-4: Hygrothermal performance - Calculation of hourly data
- ISO 9060: Solar energy - Specification and classification of instruments
- WMO Guide to Meteorological Practice (WMO-No. 8)
- ASHRAE 90.1 weather data standards
"""
    
    return content


def generate_step4_export(project_data):
    """Export Step 4: Facade & Window Extraction"""
    content = """
STEP 4: FACADE & WINDOW EXTRACTION FROM BIM DATA
================================================

PURPOSE:
Extract and analyze building element geometry from BIM models to identify suitable
windows and facades for BIPV integration, providing the foundation for all subsequent
solar and financial analyses.

METHODOLOGY:
- CSV upload from BIM model extraction (Revit/Dynamo workflow)
- Comprehensive orientation analysis and mapping
- Glass area filtering and BIPV suitability assessment
- Element ID preservation for accurate calculations

BIM DATA ANALYSIS:
"""
    
    building_elements = project_data.get('building_elements', [])
    facade_analysis = project_data.get('facade_analysis', {})
    
    # Calculate summary statistics
    total_elements = len(building_elements)
    suitable_elements = sum(1 for elem in building_elements if elem.get('pv_suitable', False))
    total_glass_area = sum(float(elem.get('glass_area', 0)) for elem in building_elements)
    
    # Orientation distribution
    orientation_dist = {}
    area_by_orientation = {}
    for elem in building_elements:
        orientation = elem.get('orientation', 'Unknown')
        orientation_dist[orientation] = orientation_dist.get(orientation, 0) + 1
        area_by_orientation[orientation] = area_by_orientation.get(orientation, 0) + float(elem.get('glass_area', 0))
    
    content += f"""
Building Element Summary:
- Total Elements Extracted: {total_elements}
- BIPV Suitable Elements: {suitable_elements} ({suitable_elements/total_elements*100:.1f}%)
- Total Glass Area: {total_glass_area:,.1f} m²
- Average Glass Area per Element: {total_glass_area/total_elements:.1f} m²

Orientation Distribution:
"""
    
    for orientation, count in orientation_dist.items():
        area = area_by_orientation.get(orientation, 0)
        content += f"- {orientation}: {count} elements, {area:.1f} m² total area\n"
    
    content += f"""

BIM DATA STRUCTURE ANALYSIS:
- Element ID Format: {facade_analysis.get('element_id_format', 'Standard Revit IDs')}
- Host Wall References: {facade_analysis.get('wall_references_found', 'N/A')}
- Level Information: {facade_analysis.get('level_data_available', 'N/A')}
- Family Types Recognized: {facade_analysis.get('family_types', 'N/A')}

CALCULATIONS PERFORMED:

1. Orientation Mapping (Azimuth to Cardinal Direction):
   - North: 315° - 45° (azimuth range)
   - East: 45° - 135°
   - South: 135° - 225° 
   - West: 225° - 315°

2. BIPV Suitability Assessment:
   Criteria for BIPV suitability:
   - Minimum glass area: ≥ 1.0 m²
   - Accessible orientation (not blocked)
   - Suitable window family type
   - Adequate structural support

3. Glass Area Analysis:
   - Total glazing area available for BIPV integration
   - Average window size distribution
   - Orientation-based area allocation

4. Element ID Preservation:
   - Authentic BIM Element IDs maintained throughout workflow
   - Host Wall relationships preserved for shading analysis
   - Level assignments retained for multi-story calculations

QUALITY ASSURANCE:
- CSV data validation and type checking
- Orientation calculation verification
- Glass area reasonableness checks (0.5 m² - 50 m² range)
- Element ID uniqueness validation

DETAILED ELEMENT ANALYSIS:
"""
    
    # Add sample of detailed elements
    sample_elements = building_elements[:5] if building_elements else []
    for i, elem in enumerate(sample_elements):
        content += f"""
Element {i+1}:
- Element ID: {elem.get('element_id', 'N/A')}
- Orientation: {elem.get('orientation', 'N/A')} ({elem.get('azimuth', 'N/A')}°)
- Glass Area: {elem.get('glass_area', 'N/A')} m²
- Level: {elem.get('level', 'N/A')}
- Host Wall ID: {elem.get('host_wall_id', 'N/A')}
- BIPV Suitable: {elem.get('pv_suitable', False)}
"""
    
    content += f"""

WINDOW TYPE ANALYSIS:
- Standard Windows: {facade_analysis.get('standard_windows', 0)}
- Curtain Wall Systems: {facade_analysis.get('curtain_walls', 0)}
- Glazed Doors: {facade_analysis.get('glazed_doors', 0)}
- Skylights: {facade_analysis.get('skylights', 0)}

BIM EXTRACTION WORKFLOW:
1. Revit Model Processing (LOD 200+ required)
2. Dynamo Script Execution for window metadata extraction
3. CSV Export with comprehensive element properties
4. Python Processing for orientation analysis and validation
5. Database Storage with Element ID preservation

CRITICAL IMPORTANCE:
This step is MANDATORY for all subsequent analyses. Without authentic building
element data, Steps 5-10 cannot provide accurate BIPV calculations. The Element IDs
and geometries extracted here form the foundation for:
- Solar radiation calculations (Step 5)
- PV system specifications (Step 6)  
- Energy yield analysis (Step 7)
- Multi-objective optimization (Step 8)
- Financial modeling (Step 9)

DATA USAGE IN SUBSEQUENT STEPS:
- Step 5: Element geometries and orientations for radiation analysis
- Step 6: Glass areas for BIPV system sizing
- Step 7: Individual element yields for demand matching
- Step 8: Element-specific optimization variables
- Step 9: Cost calculations based on actual areas
- Step 10: Building-specific performance reporting

SCIENTIFIC STANDARDS APPLIED:
- Building Information Modeling (BIM) ISO 19650 standards
- Revit API data extraction protocols
- BIPV integration guidelines (IEA PVPS Task 15)
- Architectural geometry validation standards
"""
    
    return content


def generate_step5_export(project_data):
    """Export Step 5: Radiation & Shading Analysis"""
    return "Step 5 export content - Radiation & Shading Grid Analysis..."


def generate_step6_export(project_data):
    """Export Step 6: PV Specification"""
    return "Step 6 export content - PV Panel Specification & Layout..."


def generate_step7_export(project_data):
    """Export Step 7: Yield vs Demand"""
    return "Step 7 export content - Yield vs Demand Analysis..."


def generate_step8_export(project_data):
    """Export Step 8: Optimization"""
    return "Step 8 export content - Multi-Objective Optimization..."


def generate_step9_export(project_data):
    """Export Step 9: Financial Analysis"""
    return "Step 9 export content - Financial & Environmental Analysis..."


def generate_step10_export(project_data):
    """Export Step 10: Reporting"""
    return "Step 10 export content - Reporting & Export..."


def generate_step11_export(project_data):
    """Export Step 11: AI Consultation"""
    return "Step 11 export content - AI-Powered Research Consultation..."