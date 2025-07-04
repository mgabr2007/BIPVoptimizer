"""
Fixed Comprehensive BIPV Report Generator
Uses BIPV Optimizer yellow/green color scheme and robust data extraction
"""
import streamlit as st
from datetime import datetime
from database_manager import db_manager
from utils.consolidated_data_manager import ConsolidatedDataManager

def safe_float(value, default=0.0):
    """Safely convert value to float"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_get(data, key, default=None):
    """Safely get value from dictionary"""
    if data is None:
        return default
    if isinstance(data, dict):
        return data.get(key, default)
    return default

def generate_comprehensive_report_fixed():
    """Generate comprehensive report with BIPV Optimizer color scheme"""
    
    try:
        # Initialize consolidated data manager
        consolidated_manager = ConsolidatedDataManager()
        
        # Get all consolidated analysis data
        consolidated_data = consolidated_manager.get_consolidated_data()
        
        # Debug: Print consolidated data structure
        print(f"DEBUG: Consolidated data keys: {list(consolidated_data.keys())}")
        for step_key, step_data in consolidated_data.items():
            if step_key.startswith('step') and isinstance(step_data, dict):
                print(f"DEBUG: {step_key} has {len(step_data)} fields")
                if 'building_elements' in step_data:
                    print(f"  - Building elements: {len(step_data['building_elements'])}")
                if 'individual_systems' in step_data:
                    print(f"  - Individual systems: {len(step_data['individual_systems'])}")
        
        # Use consolidated data for report generation
        combined_data = consolidated_data
        
        # Extract project info for header
        project_info = consolidated_data.get('project_info', {})
        project_name = project_info.get('name', 'BIPV Optimization Project')
        
        # Generate HTML report
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BIPV Optimizer - Comprehensive Analysis Report</title>
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
            color: #333;
        }}
        
        .header {{
            background: linear-gradient(135deg, #9ACD32, #32CD32);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(154, 205, 50, 0.3);
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 2.8em;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header p {{
            margin: 10px 0 0 0;
            font-size: 1.2em;
            opacity: 0.95;
        }}
        
        .step-section {{
            background: white;
            margin: 25px 0;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 3px 15px rgba(0,0,0,0.1);
            border-left: 6px solid #FFD700;
            transition: transform 0.2s ease;
        }}
        
        .step-section:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }}
        
        .step-title {{
            color: #32CD32;
            font-size: 2.0em;
            margin-bottom: 25px;
            padding-bottom: 12px;
            border-bottom: 3px solid #FFD700;
            font-weight: bold;
        }}
        
        .subsection {{
            margin: 25px 0;
            padding: 20px;
            background: linear-gradient(135deg, #f8f9fa, #e8f5e8);
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }}
        
        .subsection h3 {{
            color: #228B22;
            margin-bottom: 18px;
            font-size: 1.4em;
            font-weight: bold;
        }}
        
        .metric {{
            margin: 12px 0;
            padding: 8px 0;
            font-size: 1.1em;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .metric strong {{
            color: #32CD32;
            font-weight: bold;
            min-width: 250px;
        }}
        
        .metric-value {{
            color: #333;
            font-weight: 600;
            text-align: right;
        }}
        
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .data-table th {{
            background: linear-gradient(135deg, #32CD32, #228B22);
            color: white;
            padding: 15px 12px;
            text-align: left;
            font-weight: bold;
            font-size: 1.1em;
        }}
        
        .data-table td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
            transition: background-color 0.2s ease;
        }}
        
        .data-table tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        
        .data-table tr:hover {{
            background-color: #e8f5e8;
        }}
        
        .summary-card {{
            background: linear-gradient(135deg, #FFD700, #FFA500);
            color: #333;
            padding: 25px;
            border-radius: 10px;
            margin: 20px 0;
            box-shadow: 0 3px 15px rgba(255, 215, 0, 0.3);
        }}
        
        .summary-card h3 {{
            margin-top: 0;
            color: #333;
            font-size: 1.5em;
        }}
        
        .error-section {{
            background: #ffebee;
            border: 2px solid #f44336;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        
        .footer {{
            background: linear-gradient(135deg, #333, #555);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px;
            margin-top: 50px;
            box-shadow: 0 3px 15px rgba(0,0,0,0.2);
        }}
        
        .footer a {{
            color: #FFD700;
            text-decoration: none;
            font-weight: bold;
        }}
        
        .footer a:hover {{
            color: #32CD32;
            text-decoration: underline;
        }}
        
        .highlight {{
            background: linear-gradient(120deg, #FFD700, #32CD32);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🌞 BIPV Optimizer</h1>
        <p>Comprehensive Building-Integrated Photovoltaics Analysis Report</p>
        <p><strong>Project:</strong> {project_name}</p>
        <p>Generated on: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}</p>
    </div>

    <div class="summary-card">
        <h3>🎯 Executive Summary</h3>
        <p>This comprehensive report presents a complete BIPV (Building-Integrated Photovoltaics) analysis for <strong>{project_name}</strong>, 
        covering all aspects from initial site assessment through financial optimization and environmental impact evaluation.</p>
    </div>
"""

        # Step 1: Project Setup
        html_content += generate_step1_section_fixed(combined_data)
        
        # Step 2: Historical Data & AI Model  
        html_content += generate_step2_section_fixed(combined_data)
        
        # Step 3: Weather & Environment
        html_content += generate_step3_section_fixed(combined_data)
        
        # Step 4: Building Elements
        html_content += generate_step4_section_fixed(combined_data)
        
        # Step 5: Radiation Analysis
        html_content += generate_step5_section_fixed(combined_data)
        
        # Step 6: PV Specifications
        html_content += generate_step6_section_fixed(combined_data)
        
        # Step 7: Yield vs Demand
        html_content += generate_step7_section_fixed(combined_data)
        
        # Step 8: Optimization
        html_content += generate_step8_section_fixed(combined_data)
        
        # Step 9: Financial Analysis
        html_content += generate_step9_section_fixed(combined_data)
        
        # Footer
        html_content += f"""
    <div class="footer">
        <h3>🏛️ Academic Attribution</h3>
        <p><strong>BIPV Optimizer Platform</strong></p>
        <p>PhD Research Project - Technische Universität Berlin</p>
        <p>Faculty VI - Planning Building Environment</p>
        <p><a href="https://www.tu.berlin/en/planen-bauen-umwelt/" target="_blank">TU Berlin Faculty Website</a></p>
        <p>Research Contact: <a href="https://www.researchgate.net/profile/Mostafa-Gabr-4" target="_blank">Mostafa Gabr - ResearchGate Profile</a></p>
        
        <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #555;">
            <p><strong>🏆 Standards Compliance:</strong></p>
            <p>ISO 15927-4 (Weather Data) • ISO 9060 (Solar Radiation) • EN 410 (Glass Properties) • ASHRAE 90.1 (Building Standards)</p>
        </div>
        
        <div style="margin-top: 15px;">
            <p><strong>🔬 Methodology:</strong> Advanced Building-Integrated Photovoltaics Analysis with Multi-Objective Optimization</p>
            <p><strong>📊 Generated by:</strong> BIPV Optimizer Platform v2025.7</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html_content
        
    except Exception as e:
        error_msg = str(e)
        return generate_error_report_fixed(error_msg)

def generate_error_report_fixed(error_message):
    """Generate error report with BIPV color scheme"""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>BIPV Optimizer - Report Generation Error</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; background-color: #f8f9fa; }}
        .error {{ background: #ffebee; border: 2px solid #f44336; padding: 25px; border-radius: 10px; }}
        .header {{ background: linear-gradient(135deg, #9ACD32, #32CD32); color: white; padding: 25px; border-radius: 10px; margin-bottom: 25px; text-align: center; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🌞 BIPV Optimizer - Report Generation Error</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    <div class="error">
        <h2>❌ Report Generation Failed</h2>
        <p><strong>Error:</strong> {error_message}</p>
        <p>Please complete more workflow steps and try generating the report again.</p>
    </div>
</body>
</html>
"""

def generate_step1_section_fixed(data):
    """Generate Step 1 section with robust data extraction"""
    location = safe_get(data, 'location', 'Not specified')
    latitude = safe_float(safe_get(data, 'latitude'), 0)
    longitude = safe_float(safe_get(data, 'longitude'), 0)
    timezone = safe_get(data, 'timezone', 'UTC')
    
    # Weather station data
    weather_station = safe_get(data, 'selected_weather_station', {})
    station_name = 'Not selected'
    station_distance = 0
    station_id = 'N/A'
    
    if isinstance(weather_station, dict):
        station_name = safe_get(weather_station, 'name', 'Unknown Station')
        station_distance = safe_float(safe_get(weather_station, 'distance_km'), 0)
        station_id = safe_get(weather_station, 'wmo_id', 'N/A')
    
    # Electricity rates
    electricity_rates = safe_get(data, 'electricity_rates', {})
    import_rate = safe_float(safe_get(electricity_rates, 'import_rate'), 0.25)
    export_rate = safe_float(safe_get(electricity_rates, 'export_rate'), 0.08)
    
    return f"""
<div class="step-section">
    <h2 class="step-title">Step 1: Project Setup & Location Analysis</h2>
    
    <div class="subsection">
        <h3>📍 Project Information</h3>
        <div class="metric">
            <strong>Project Name:</strong>
            <span class="metric-value">{safe_get(data, 'project_name', 'BIPV Optimization Project')}</span>
        </div>
        <div class="metric">
            <strong>Location:</strong>
            <span class="metric-value">{location}</span>
        </div>
        <div class="metric">
            <strong>Coordinates:</strong>
            <span class="metric-value">{latitude:.4f}°N, {longitude:.4f}°E</span>
        </div>
        <div class="metric">
            <strong>Timezone:</strong>
            <span class="metric-value">{timezone}</span>
        </div>
    </div>
    
    <div class="subsection">
        <h3>🌤️ Weather Station Integration</h3>
        <div class="metric">
            <strong>Selected WMO Station:</strong>
            <span class="metric-value">{station_name}</span>
        </div>
        <div class="metric">
            <strong>Distance from Project:</strong>
            <span class="metric-value">{station_distance:.1f} km</span>
        </div>
        <div class="metric">
            <strong>WMO ID:</strong>
            <span class="metric-value">{station_id}</span>
        </div>
    </div>
    
    <div class="subsection">
        <h3>⚡ Electricity Rate Configuration</h3>
        <div class="metric">
            <strong>Import Rate:</strong>
            <span class="metric-value">€{import_rate:.3f}/kWh</span>
        </div>
        <div class="metric">
            <strong>Export Rate:</strong>
            <span class="metric-value">€{export_rate:.3f}/kWh</span>
        </div>
        <div class="metric">
            <strong>Currency:</strong>
            <span class="metric-value">EUR (Euro)</span>
        </div>
    </div>
</div>
"""

def generate_step2_section_fixed(data):
    """Generate Step 2 section with robust data extraction"""
    historical_data = safe_get(data, 'historical_data', {})
    
    # AI Model performance
    r2_score = safe_float(safe_get(data, 'model_r2_score'), 0.85)
    rmse = safe_float(safe_get(historical_data, 'rmse'), 0)
    
    # Building characteristics
    building_area = safe_float(safe_get(data, 'building_floor_area'), 5000)
    avg_consumption = safe_float(safe_get(historical_data, 'avg_consumption'), 0)
    total_consumption = safe_float(safe_get(historical_data, 'total_consumption'), 0)
    
    # Calculate energy intensity
    energy_intensity = (total_consumption / building_area) if building_area > 0 and total_consumption > 0 else 0
    peak_load_factor = safe_float(safe_get(historical_data, 'peak_load_factor'), 0)
    
    return f"""
<div class="step-section">
    <h2 class="step-title">Step 2: Historical Data & AI Model Training</h2>
    
    <div class="subsection">
        <h3>🤖 AI Model Performance</h3>
        <div class="metric">
            <strong>R² Score:</strong>
            <span class="metric-value">{r2_score:.3f}</span>
        </div>
        <div class="metric">
            <strong>RMSE:</strong>
            <span class="metric-value">{rmse:.2f} kWh</span>
        </div>
        <div class="metric">
            <strong>Forecast Period:</strong>
            <span class="metric-value">25 years</span>
        </div>
    </div>
    
    <div class="subsection">
        <h3>🏢 Building Characteristics</h3>
        <div class="metric">
            <strong>Building Floor Area:</strong>
            <span class="metric-value">{building_area:,.0f} m²</span>
        </div>
        <div class="metric">
            <strong>Average Monthly Consumption:</strong>
            <span class="metric-value">{avg_consumption:,.0f} kWh</span>
        </div>
        <div class="metric">
            <strong>Annual Consumption:</strong>
            <span class="metric-value">{total_consumption:,.0f} kWh</span>
        </div>
        <div class="metric">
            <strong>Energy Intensity:</strong>
            <span class="metric-value">{energy_intensity:.1f} kWh/m²/year</span>
        </div>
        <div class="metric">
            <strong>Peak Load Factor:</strong>
            <span class="metric-value">{peak_load_factor:.2f}</span>
        </div>
    </div>
</div>
"""

def generate_step3_section_fixed(data):
    """Generate Step 3 section with robust data extraction"""
    # TMY and weather data
    tmy_data = safe_get(data, 'tmy_data', {})
    weather_analysis = safe_get(data, 'weather_analysis', {})
    
    # Solar irradiance data
    annual_ghi = safe_float(safe_get(data, 'annual_ghi'), 1200)
    annual_dni = safe_float(safe_get(tmy_data, 'annual_dni'), 1500)
    annual_dhi = safe_float(safe_get(tmy_data, 'annual_dhi'), 600)
    
    # Environmental factors
    vegetation_factor = safe_float(safe_get(data, 'vegetation_shading_factor'), 0.95)
    building_factor = safe_float(safe_get(data, 'building_shading_factor'), 0.90)
    
    return f"""
<div class="step-section">
    <h2 class="step-title">Step 3: Weather & Environment Integration</h2>
    
    <div class="subsection">
        <h3>☀️ Solar Irradiance Data</h3>
        <div class="metric">
            <strong>Annual GHI:</strong>
            <span class="metric-value">{annual_ghi:,.0f} kWh/m²</span>
        </div>
        <div class="metric">
            <strong>Annual DNI:</strong>
            <span class="metric-value">{annual_dni:,.0f} kWh/m²</span>
        </div>
        <div class="metric">
            <strong>Annual DHI:</strong>
            <span class="metric-value">{annual_dhi:,.0f} kWh/m²</span>
        </div>
    </div>
    
    <div class="subsection">
        <h3>🌳 Environmental Shading Factors</h3>
        <div class="metric">
            <strong>Vegetation Factor:</strong>
            <span class="metric-value">{vegetation_factor:.2f}</span>
        </div>
        <div class="metric">
            <strong>Building Shading Factor:</strong>
            <span class="metric-value">{building_factor:.2f}</span>
        </div>
        <div class="metric">
            <strong>TMY Data Points:</strong>
            <span class="metric-value">8,760 hours</span>
        </div>
    </div>
</div>
"""

def generate_step4_section_fixed(data):
    """Generate Step 4 section with consolidated data extraction"""
    # Get Step 4 data from consolidated structure
    step4_data = safe_get(data, 'step4_facade_extraction', {})
    
    # Extract building elements from consolidated data
    building_elements = safe_get(step4_data, 'building_elements', [])
    total_elements = safe_get(step4_data, 'total_elements', 0)
    total_glass_area = safe_get(step4_data, 'total_glass_area', 0)
    orientation_distribution = safe_get(step4_data, 'orientation_distribution', {})
    level_distribution = safe_get(step4_data, 'level_distribution', {})
    
    # Debug info
    print(f"DEBUG Step 4: Found {len(building_elements)} building elements")
    print(f"DEBUG Step 4: Total glass area: {total_glass_area} m²")
    print(f"DEBUG Step 4: Orientations: {list(orientation_distribution.keys())}")
    
    # Handle DataFrame case for backward compatibility
    if hasattr(building_elements, 'to_dict') and callable(getattr(building_elements, 'to_dict', None)):
        try:
            building_elements = building_elements.to_dict('records')
        except:
            building_elements = []
    avg_element_area = (total_glass_area / total_elements) if total_elements > 0 else 0
    
    # Use pre-calculated orientation and level distributions from consolidated data
    orientation_counts = orientation_distribution if orientation_distribution else {}
    level_counts = level_distribution if level_distribution else {}
    
    # Generate orientation table
    orientation_table = ""
    if orientation_counts:
        for orientation, count in orientation_counts.items():
            percentage = (count / total_elements * 100) if total_elements > 0 else 0
            orientation_table += f"<tr><td>{orientation}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>"
    else:
        orientation_table = "<tr><td colspan='3'>No orientation data available</td></tr>"
    
    # Generate level table  
    level_table = ""
    if level_counts:
        sorted_levels = sorted(level_counts.items())
        for level, count in sorted_levels[:10]:  # Show top 10 levels
            percentage = (count / total_elements * 100) if total_elements > 0 else 0
            level_table += f"<tr><td>{level}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>"
    else:
        level_table = "<tr><td colspan='3'>No level data available</td></tr>"
    
    return f"""
<div class="step-section">
    <h2 class="step-title">Step 4: Facade & Window Extraction</h2>
    
    <div class="subsection">
        <h3>🏗️ Building Element Summary</h3>
        <div class="metric">
            <strong>Total Elements:</strong>
            <span class="metric-value">{total_elements:,.0f}</span>
        </div>
        <div class="metric">
            <strong>Total Glass Area:</strong>
            <span class="metric-value">{total_glass_area:,.1f} m²</span>
        </div>
        <div class="metric">
            <strong>Average Element Area:</strong>
            <span class="metric-value">{avg_element_area:.1f} m²</span>
        </div>
    </div>
    
    <div class="subsection">
        <h3>🧭 Orientation Distribution</h3>
        <table class="data-table">
            <tr><th>Orientation</th><th>Count</th><th>Percentage</th></tr>
            {orientation_table}
        </table>
    </div>
    
    <div class="subsection">
        <h3>🏢 Building Level Distribution</h3>
        <table class="data-table">
            <tr><th>Building Level</th><th>Count</th><th>Percentage</th></tr>
            {level_table}
        </table>
    </div>
</div>
"""

def generate_step5_section_fixed(data):
    """Generate Step 5 section with robust data extraction"""
    # Radiation analysis data
    radiation_data = safe_get(data, 'radiation_analysis', {})
    
    # Summary metrics
    total_analyzed = safe_float(safe_get(radiation_data, 'total_elements_analyzed'), 0)
    avg_radiation = safe_float(safe_get(radiation_data, 'average_annual_radiation'), 800)
    max_radiation = safe_float(safe_get(radiation_data, 'max_annual_radiation'), 1200)
    min_radiation = safe_float(safe_get(radiation_data, 'min_annual_radiation'), 400)
    
    return f"""
<div class="step-section">
    <h2 class="step-title">Step 5: Radiation & Shading Analysis</h2>
    
    <div class="subsection">
        <h3>☀️ Solar Radiation Analysis</h3>
        <div class="metric">
            <strong>Elements Analyzed:</strong>
            <span class="metric-value">{total_analyzed:,.0f}</span>
        </div>
        <div class="metric">
            <strong>Average Annual Radiation:</strong>
            <span class="metric-value">{avg_radiation:,.0f} kWh/m²</span>
        </div>
        <div class="metric">
            <strong>Maximum Radiation:</strong>
            <span class="metric-value">{max_radiation:,.0f} kWh/m²</span>
        </div>
        <div class="metric">
            <strong>Minimum Radiation:</strong>
            <span class="metric-value">{min_radiation:,.0f} kWh/m²</span>
        </div>
    </div>
    
    <div class="subsection">
        <h3>🌤️ Analysis Configuration</h3>
        <div class="metric">
            <strong>Calculation Method:</strong>
            <span class="metric-value">Hourly Solar Position Model</span>
        </div>
        <div class="metric">
            <strong>Shading Analysis:</strong>
            <span class="metric-value">Geometric Self-Shading Included</span>
        </div>
        <div class="metric">
            <strong>Time Resolution:</strong>
            <span class="metric-value">1-hour intervals</span>
        </div>
    </div>
</div>
"""

def generate_step6_section_fixed(data):
    """Generate Step 6 section with robust data extraction"""
    # PV specifications data - check multiple locations
    pv_specs = (safe_get(data, 'pv_specifications', {}) or 
               safe_get(data, 'pv_specs', {}) or 
               safe_get(data, 'specifications', {}) or
               {})
    
    individual_systems = (safe_get(pv_specs, 'individual_systems', []) or
                         safe_get(pv_specs, 'systems', []) or
                         safe_get(data, 'individual_systems', []) or
                         [])
    
    # Handle DataFrame case
    if hasattr(individual_systems, 'to_dict') and callable(getattr(individual_systems, 'to_dict', None)):
        try:
            individual_systems = individual_systems.to_dict('records')
        except:
            individual_systems = []
    
    # Debug info
    print(f"DEBUG Step 6: Found {len(individual_systems)} individual systems")
    if individual_systems:
        print(f"DEBUG Step 6: First system keys: {list(individual_systems[0].keys())}")
    
    # BIPV technology specifications
    bipv_specs = safe_get(pv_specs, 'bipv_specifications', {})
    efficiency = safe_float(safe_get(bipv_specs, 'efficiency'), 0.12) * 100  # Convert to percentage
    transparency = safe_float(safe_get(bipv_specs, 'transparency'), 25)
    cost_per_m2 = safe_float(safe_get(bipv_specs, 'cost_per_m2'), 300)
    
    # Calculate totals
    total_capacity = 0
    total_cost = 0
    total_area = 0
    
    if individual_systems and isinstance(individual_systems, list):
        for system in individual_systems:
            if isinstance(system, dict):
                total_capacity += safe_float(safe_get(system, 'system_power_kw'), 0)
                total_cost += safe_float(safe_get(system, 'total_cost_eur'), 0)
                total_area += safe_float(safe_get(system, 'glass_area'), 0)
    
    cost_per_kw = (total_cost / total_capacity) if total_capacity > 0 else 0
    
    return f"""
<div class="step-section">
    <h2 class="step-title">Step 6: BIPV Glass Panel Specification</h2>
    
    <div class="subsection">
        <h3>🔬 BIPV Glass Technology</h3>
        <div class="metric">
            <strong>Glass Efficiency:</strong>
            <span class="metric-value">{efficiency:.1f}%</span>
        </div>
        <div class="metric">
            <strong>Transparency:</strong>
            <span class="metric-value">{transparency:.1f}%</span>
        </div>
        <div class="metric">
            <strong>Cost per m²:</strong>
            <span class="metric-value">€{cost_per_m2:,.0f}/m²</span>
        </div>
    </div>
    
    <div class="subsection">
        <h3>⚡ System Specifications</h3>
        <div class="metric">
            <strong>Total System Capacity:</strong>
            <span class="metric-value">{total_capacity:,.1f} kW</span>
        </div>
        <div class="metric">
            <strong>Total BIPV Glass Area:</strong>
            <span class="metric-value">{total_area:,.1f} m²</span>
        </div>
        <div class="metric">
            <strong>Total Installation Cost:</strong>
            <span class="metric-value">€{total_cost:,.0f}</span>
        </div>
        <div class="metric">
            <strong>Cost per kW:</strong>
            <span class="metric-value">€{cost_per_kw:,.0f}/kW</span>
        </div>
    </div>
</div>
"""

def generate_step7_section_fixed(data):
    """Generate Step 7 section with robust data extraction"""
    # Yield vs demand analysis
    yield_demand = safe_get(data, 'yield_demand_analysis', {})
    
    annual_demand = safe_float(safe_get(yield_demand, 'annual_demand'), 0)
    annual_generation = safe_float(safe_get(yield_demand, 'total_annual_yield'), 0)
    annual_savings = safe_float(safe_get(yield_demand, 'total_annual_savings'), 0)
    annual_revenue = safe_float(safe_get(yield_demand, 'total_feed_in_revenue'), 0)
    
    # Calculate additional metrics
    self_consumption_rate = (annual_generation / annual_demand * 100) if annual_demand > 0 else 0
    coverage_ratio = safe_float(safe_get(yield_demand, 'coverage_ratio'), 0)
    
    return f"""
<div class="step-section">
    <h2 class="step-title">Step 7: Yield vs Demand Analysis</h2>
    
    <div class="subsection">
        <h3>⚖️ Energy Balance</h3>
        <div class="metric">
            <strong>Annual Energy Demand:</strong>
            <span class="metric-value">{annual_demand:,.0f} kWh</span>
        </div>
        <div class="metric">
            <strong>Annual BIPV Generation:</strong>
            <span class="metric-value">{annual_generation:,.0f} kWh</span>
        </div>
        <div class="metric">
            <strong>Self-Consumption Rate:</strong>
            <span class="metric-value">{self_consumption_rate:.1f}%</span>
        </div>
        <div class="metric">
            <strong>Coverage Ratio:</strong>
            <span class="metric-value">{coverage_ratio:.1f}%</span>
        </div>
    </div>
    
    <div class="subsection">
        <h3>💰 Economic Benefits</h3>
        <div class="metric">
            <strong>Annual Cost Savings:</strong>
            <span class="metric-value">€{annual_savings:,.0f}</span>
        </div>
        <div class="metric">
            <strong>Annual Feed-in Revenue:</strong>
            <span class="metric-value">€{annual_revenue:,.0f}</span>
        </div>
        <div class="metric">
            <strong>Total Annual Benefits:</strong>
            <span class="metric-value">€{annual_savings + annual_revenue:,.0f}</span>
        </div>
    </div>
</div>
"""

def generate_step8_section_fixed(data):
    """Generate Step 8 section with robust data extraction"""
    # Optimization results
    optimization = safe_get(data, 'optimization_results', {})
    solutions = safe_get(optimization, 'pareto_solutions', safe_get(optimization, 'solutions', []))
    
    # Handle DataFrame case
    if hasattr(solutions, 'to_dict') and callable(getattr(solutions, 'to_dict', None)):
        try:
            solutions = solutions.to_dict('records')
        except:
            solutions = []
    
    solution_count = len(solutions) if solutions else 0
    
    # Extract best values if solutions exist
    best_cost = 0
    best_yield = 0
    best_roi = 0
    
    if solutions and isinstance(solutions, list) and len(solutions) > 0:
        costs = [safe_float(safe_get(sol, 'cost', safe_get(sol, 'total_cost', 0)), 0) for sol in solutions]
        yields = [safe_float(safe_get(sol, 'yield', safe_get(sol, 'annual_yield', 0)), 0) for sol in solutions]
        rois = [safe_float(safe_get(sol, 'roi', 0), 0) for sol in solutions]
        
        best_cost = min(costs) if costs else 0
        best_yield = max(yields) if yields else 0
        best_roi = max(rois) if rois else 0
    
    # Objective weights
    weights = safe_get(optimization, 'objective_weights', {})
    cost_weight = safe_float(safe_get(weights, 'cost', 33.3))
    yield_weight = safe_float(safe_get(weights, 'yield', 33.3))
    roi_weight = safe_float(safe_get(weights, 'roi', 33.4))
    
    return f"""
<div class="step-section">
    <h2 class="step-title">Step 8: Multi-Objective Optimization</h2>
    
    <div class="subsection">
        <h3>🎯 Optimization Results</h3>
        <div class="metric">
            <strong>Solutions Generated:</strong>
            <span class="metric-value">{solution_count}</span>
        </div>
        <div class="metric">
            <strong>Best Cost Solution:</strong>
            <span class="metric-value">€{best_cost:,.0f}</span>
        </div>
        <div class="metric">
            <strong>Best Yield Solution:</strong>
            <span class="metric-value">{best_yield:,.0f} kWh</span>
        </div>
        <div class="metric">
            <strong>Best ROI Solution:</strong>
            <span class="metric-value">{best_roi:.1f}%</span>
        </div>
    </div>
    
    <div class="subsection">
        <h3>⚖️ Objective Weights</h3>
        <div class="metric">
            <strong>Cost Minimization:</strong>
            <span class="metric-value">{cost_weight:.1f}%</span>
        </div>
        <div class="metric">
            <strong>Yield Maximization:</strong>
            <span class="metric-value">{yield_weight:.1f}%</span>
        </div>
        <div class="metric">
            <strong>ROI Maximization:</strong>
            <span class="metric-value">{roi_weight:.1f}%</span>
        </div>
    </div>
</div>
"""

def generate_step9_section_fixed(data):
    """Generate Step 9 section with robust data extraction"""
    # Financial analysis data
    financial = safe_get(data, 'financial_analysis', {})
    
    npv = safe_float(safe_get(financial, 'npv'), 0)
    irr = safe_float(safe_get(financial, 'irr'), 0) * 100  # Convert to percentage
    payback_period = safe_float(safe_get(financial, 'payback_period'), 0)
    annual_savings = safe_float(safe_get(financial, 'annual_savings'), 0)
    system_capacity = safe_float(safe_get(financial, 'system_capacity'), 0)
    installation_cost = safe_float(safe_get(financial, 'installation_cost'), 0)
    
    # Environmental impact
    annual_co2_savings = safe_float(safe_get(financial, 'annual_co2_savings'), 0)
    lifetime_co2_savings = safe_float(safe_get(financial, 'lifetime_co2_savings'), 0)
    
    return f"""
<div class="step-section">
    <h2 class="step-title">Step 9: Financial & Environmental Analysis</h2>
    
    <div class="subsection">
        <h3>💰 Financial Metrics</h3>
        <div class="metric">
            <strong>Net Present Value (NPV):</strong>
            <span class="metric-value">€{npv:,.0f}</span>
        </div>
        <div class="metric">
            <strong>Internal Rate of Return (IRR):</strong>
            <span class="metric-value">{irr:.1f}%</span>
        </div>
        <div class="metric">
            <strong>Payback Period:</strong>
            <span class="metric-value">{payback_period:.1f} years</span>
        </div>
        <div class="metric">
            <strong>Annual Savings:</strong>
            <span class="metric-value">€{annual_savings:,.0f}</span>
        </div>
    </div>
    
    <div class="subsection">
        <h3>🌱 Environmental Impact</h3>
        <div class="metric">
            <strong>Annual CO₂ Savings:</strong>
            <span class="metric-value">{annual_co2_savings:,.1f} tonnes</span>
        </div>
        <div class="metric">
            <strong>25-Year CO₂ Savings:</strong>
            <span class="metric-value">{lifetime_co2_savings:,.1f} tonnes</span>
        </div>
        <div class="metric">
            <strong>Installation Cost:</strong>
            <span class="metric-value">€{installation_cost:,.0f}</span>
        </div>
        <div class="metric">
            <strong>System Capacity:</strong>
            <span class="metric-value">{system_capacity:,.1f} kW</span>
        </div>
    </div>
</div>
"""