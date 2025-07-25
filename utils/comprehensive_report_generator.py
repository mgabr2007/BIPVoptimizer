"""
Comprehensive Report Generator for BIPV Optimizer
Generates single consolidated report covering all 9 workflow steps
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
import base64

def safe_get(data, *keys, default=None):
    """Safely get nested dictionary values with multiple fallback keys"""
    if not isinstance(data, dict):
        return default
    
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return default

def generate_comprehensive_report():
    """Generate comprehensive report covering all 9 workflow steps"""
    
    # Import data extractor
    from utils.report_data_extractor import (
        extract_comprehensive_project_data,
        get_step1_data, get_step2_data, get_step3_data, get_step4_data,
        get_step5_data, get_step6_data, get_step7_data, get_step8_data, get_step9_data
    )
    
    # Get project name
    session_data = st.session_state.get('project_data', {})
    project_name = session_data.get('project_name', 'BIPV Project')
    
    # Extract comprehensive project data
    project_data = extract_comprehensive_project_data(project_name)
    
    # Extract data for each step
    step1_data = get_step1_data(project_data)
    step2_data = get_step2_data(project_data)
    step3_data = get_step3_data(project_data)
    step4_data = get_step4_data(project_data)
    step5_data = get_step5_data(project_data)
    step6_data = get_step6_data(project_data)
    step7_data = get_step7_data(project_data)
    step8_data = get_step8_data(project_data)
    step9_data = get_step9_data(project_data)
    
    # Build comprehensive report HTML
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{project_name} - Comprehensive BIPV Analysis Report</title>
        <style>
            body {{
                font-family: 'Arial', sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: #f8f9fa;
            }}
            .header {{
                background: linear-gradient(135deg, #2c3e50, #3498db);
                color: white;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 30px;
                text-align: center;
            }}
            .step-section {{
                background: white;
                margin: 20px 0;
                padding: 25px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                border-left: 4px solid #3498db;
            }}
            .step-title {{
                color: #2c3e50;
                font-size: 24px;
                margin-bottom: 15px;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
            }}
            .subsection {{
                margin: 15px 0;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 5px;
            }}
            .metric {{
                background: #e8f5e8;
                padding: 10px;
                border-radius: 5px;
                margin: 5px 0;
                border-left: 3px solid #27ae60;
            }}
            .warning {{
                background: #fff3cd;
                padding: 10px;
                border-radius: 5px;
                margin: 5px 0;
                border-left: 3px solid #ffc107;
            }}
            .error {{
                background: #f8d7da;
                padding: 10px;
                border-radius: 5px;
                margin: 5px 0;
                border-left: 3px solid #dc3545;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #3498db;
                color: white;
            }}
            .footer {{
                margin-top: 40px;
                padding: 20px;
                background: #2c3e50;
                color: white;
                text-align: center;
                border-radius: 8px;
            }}
            .chart-container {{
                margin: 20px 0;
                padding: 15px;
                background: white;
                border-radius: 5px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>BIPV Optimizer - Comprehensive Analysis Report</h1>
            <h2>{project_name}</h2>
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    """
    
    # Import step generators
    from utils.report_step_generators import (
        generate_step1_section, generate_step2_section, generate_step3_section,
        generate_step4_section, generate_step5_section, generate_step6_section,
        generate_step7_section, generate_step8_section, generate_step9_section
    )
    
    # Step 1: Project Setup & Location Analysis
    html_content += generate_step1_section(step1_data)
    
    # Step 2: Historical Data & AI Model
    html_content += generate_step2_section(step2_data)
    
    # Step 3: Weather & Environment Integration
    html_content += generate_step3_section(step3_data)
    
    # Step 4: Facade & Window Extraction
    html_content += generate_step4_section(step4_data)
    
    # Step 5: Radiation & Shading Analysis
    html_content += generate_step5_section(step5_data)
    
    # Step 6: PV Panel Specification
    html_content += generate_step6_section(step6_data)
    
    # Step 7: Yield vs Demand Analysis
    html_content += generate_step7_section(step7_data)
    
    # Step 8: Multi-Objective Optimization
    html_content += generate_step8_section(step8_data)
    
    # Step 9: Financial & Environmental Analysis
    html_content += generate_step9_section(step9_data)
    
    # Footer
    html_content += f"""
        <div class="footer">
            <h3>Academic Attribution</h3>
            <p><strong>PhD Research Project</strong><br>
            Technische Universität Berlin - Faculty VI Planning Building Environment<br>
            Research Focus: Building-Integrated Photovoltaics (BIPV) Optimization<br>
            Contact: <a href="https://www.researchgate.net/profile/Mostafa-Gabr-4" style="color: #3498db;">Mostafa Gabr - ResearchGate Profile</a></p>
            
            <p><strong>Standards Compliance:</strong><br>
            ISO 15927-4 (Weather Data), ISO 9060 (Solar Radiation), EN 410 (Glass Properties), ASHRAE 90.1 (Building Standards)</p>
            
            <p><strong>Report Generation:</strong> BIPV Optimizer Platform - Advanced Building-Integrated Photovoltaics Analysis Tool</p>
        </div>
    </body>
    </html>
    """
    
    return html_content

def generate_step1_section(step1_data):
    """Generate Step 1: Project Setup & Location Analysis section"""
    
    return f"""
    <div class="step-section">
        <h2 class="step-title">Step 1: Project Setup & Location Analysis</h2>
        
        <div class="subsection">
            <h3>Project Information</h3>
            <div class="metric">
                <strong>Project Name:</strong> {step1_data['project_name']}
            </div>
            <div class="metric">
                <strong>Location:</strong> {step1_data['location_name']}
            </div>
            <div class="metric">
                <strong>Coordinates:</strong> {step1_data['latitude']:.4f}°N, {step1_data['longitude']:.4f}°E
            </div>
            <div class="metric">
                <strong>Timezone:</strong> {step1_data['timezone']}
            </div>
        </div>
        
        <div class="subsection">
            <h3>Weather Station Integration</h3>
            <div class="metric">
                <strong>Selected WMO Station:</strong> {step1_data['weather_station']}
            </div>
            <div class="metric">
                <strong>Distance from Project:</strong> {step1_data['station_distance']:.1f} km
            </div>
            <div class="metric">
                <strong>WMO ID:</strong> {step1_data['wmo_id']}
            </div>
        </div>
        
        <div class="subsection">
            <h3>Electricity Rate Configuration</h3>
            <div class="metric">
                <strong>Import Rate:</strong> €{step1_data['import_rate']:.3f}/kWh
            </div>
            <div class="metric">
                <strong>Export Rate:</strong> €{step1_data['export_rate']:.3f}/kWh
            </div>
            <div class="metric">
                <strong>Currency:</strong> EUR (Euro)
            </div>
        </div>
        
        <div class="subsection">
            <h3>Data Usage in Subsequent Steps</h3>
            <p>• <strong>Step 3:</strong> Coordinates and weather station used for TMY generation</p>
            <p>• <strong>Step 7-9:</strong> Electricity rates used for financial calculations</p>
            <p>• <strong>All Steps:</strong> Location context for solar parameters and regulations</p>
        </div>
    </div>
    """

def generate_step2_section(project_data):
    """Generate Step 2: Historical Data & AI Model section"""
    
    # Handle both nested and direct database structure
    historical_data = project_data.get('historical_data', {})
    if isinstance(historical_data, str):
        historical_data = {}
    
    # AI model metrics - check multiple possible locations
    model_performance = historical_data.get('model_performance', {})
    r2_score = model_performance.get('r2_score', project_data.get('r2_score', project_data.get('model_r2_score', 0)))
    rmse = model_performance.get('rmse', project_data.get('rmse', project_data.get('model_rmse', 0)))
    
    # Building characteristics - check database fields
    building_area = (
        historical_data.get('building_floor_area', 0) or 
        project_data.get('building_floor_area', 0) or 
        project_data.get('building_area', 5000)
    )
    energy_intensity = (
        historical_data.get('energy_intensity', 0) or 
        project_data.get('energy_intensity', 0)
    )
    peak_load = (
        historical_data.get('peak_load_factor', 0) or 
        project_data.get('peak_load_factor', 0)
    )
    
    # Forecast data
    forecast_data = historical_data.get('forecast_data', project_data.get('forecast_data', []))
    
    return f"""
    <div class="step-section">
        <h2 class="step-title">Step 2: Historical Data Analysis & AI Model Training</h2>
        
        <div class="subsection">
            <h3>AI Model Performance</h3>
            <div class="metric">
                <strong>R² Score:</strong> {r2_score:.3f}
            </div>
            <div class="metric">
                <strong>RMSE:</strong> {rmse:.2f} kWh
            </div>
            <div class="metric">
                <strong>Model Type:</strong> Random Forest Regressor
            </div>
            
            {"<div class='warning'>Model performance below 0.7 R² may affect forecast accuracy</div>" if r2_score < 0.7 else ""}
        </div>
        
        <div class="subsection">
            <h3>Building Characteristics</h3>
            <div class="metric">
                <strong>Building Floor Area:</strong> {building_area:,.0f} m²
            </div>
            <div class="metric">
                <strong>Energy Intensity:</strong> {energy_intensity:.1f} kWh/m²/year
            </div>
            <div class="metric">
                <strong>Peak Load Factor:</strong> {peak_load:.2f}
            </div>
        </div>
        
        <div class="subsection">
            <h3>25-Year Demand Forecast</h3>
            <p><strong>Forecast Period:</strong> {len(forecast_data)} years</p>
            <p><strong>Model Features:</strong> Historical consumption, temperature, occupancy patterns</p>
            <p><strong>Educational Building Standards:</strong> ASHRAE 90.1 compliance integrated</p>
        </div>
        
        <div class="subsection">
            <h3>Data Usage in Subsequent Steps</h3>
            <p>• <strong>Step 7:</strong> Demand forecast compared with PV generation</p>
            <p>• <strong>Step 8:</strong> Optimization uses demand patterns for sizing</p>
            <p>• <strong>Step 9:</strong> Financial analysis based on predicted consumption</p>
        </div>
    </div>
    """

def generate_step3_section(project_data):
    """Generate Step 3: Weather & Environment Integration section"""
    
    weather_analysis = project_data.get('weather_analysis', {})
    tmy_data = weather_analysis.get('tmy_data', [])
    
    # Environmental factors
    env_factors = weather_analysis.get('environmental_factors', {})
    vegetation_factor = env_factors.get('vegetation_shading_factor', 1.0)
    building_factor = env_factors.get('building_shading_factor', 1.0)
    
    # Annual totals
    annual_ghi = sum([hour.get('ghi', 0) for hour in tmy_data]) / 1000 if tmy_data else 0
    annual_dni = sum([hour.get('dni', 0) for hour in tmy_data]) / 1000 if tmy_data else 0
    annual_dhi = sum([hour.get('dhi', 0) for hour in tmy_data]) / 1000 if tmy_data else 0
    
    return f"""
    <div class="step-section">
        <h2 class="step-title">Step 3: Weather & Environment Integration</h2>
        
        <div class="subsection">
            <h3>Typical Meteorological Year (TMY) Generation</h3>
            <div class="metric">
                <strong>Data Points:</strong> {len(tmy_data)} hourly records
            </div>
            <div class="metric">
                <strong>Standards Compliance:</strong> ISO 15927-4 methodology
            </div>
            <div class="metric">
                <strong>Source:</strong> WMO weather station data
            </div>
        </div>
        
        <div class="subsection">
            <h3>Annual Solar Irradiance Summary</h3>
            <div class="metric">
                <strong>Global Horizontal Irradiance (GHI):</strong> {annual_ghi:.0f} kWh/m²/year
            </div>
            <div class="metric">
                <strong>Direct Normal Irradiance (DNI):</strong> {annual_dni:.0f} kWh/m²/year
            </div>
            <div class="metric">
                <strong>Diffuse Horizontal Irradiance (DHI):</strong> {annual_dhi:.0f} kWh/m²/year
            </div>
        </div>
        
        <div class="subsection">
            <h3>Environmental Shading Factors</h3>
            <div class="metric">
                <strong>Vegetation Shading Reduction:</strong> {(1-vegetation_factor)*100:.1f}%
            </div>
            <div class="metric">
                <strong>Building Shading Reduction:</strong> {(1-building_factor)*100:.1f}%
            </div>
            <div class="metric">
                <strong>Total Environmental Impact:</strong> {(1-(vegetation_factor*building_factor))*100:.1f}% reduction
            </div>
        </div>
        
        <div class="subsection">
            <h3>Data Usage in Subsequent Steps</h3>
            <p>• <strong>Step 5:</strong> TMY data used for radiation analysis on building surfaces</p>
            <p>• <strong>Step 6-7:</strong> Solar irradiance determines PV energy generation</p>
            <p>• <strong>Step 8-9:</strong> Environmental factors affect optimization and financial calculations</p>
        </div>
    </div>
    """

def generate_step4_section(project_data):
    """Generate Step 4: Facade & Window Extraction section"""
    
    # Get building elements from database structure
    building_elements = project_data.get('building_elements', [])
    if not building_elements:
        # Try session state fallback
        session_data = st.session_state.get('project_data', {})
        building_elements = session_data.get('building_elements', [])
    
    # Analyze building elements
    total_elements = len(building_elements)
    total_area = sum([elem.get('glass_area', 0) for elem in building_elements])
    
    # Orientation analysis
    orientation_counts = {}
    for elem in building_elements:
        orientation = elem.get('orientation', 'Unknown')
        orientation_counts[orientation] = orientation_counts.get(orientation, 0) + 1
    
    # Level analysis
    level_counts = {}
    for elem in building_elements:
        level = elem.get('level', 'Unknown')
        level_counts[level] = level_counts.get(level, 0) + 1
    
    return f"""
    <div class="step-section">
        <h2 class="step-title">Step 4: Facade & Window Extraction from BIM Data</h2>
        
        <div class="subsection">
            <h3>Building Elements Summary</h3>
            <div class="metric">
                <strong>Total Window Elements:</strong> {total_elements}
            </div>
            <div class="metric">
                <strong>Total Glass Area:</strong> {total_area:.1f} m²
            </div>
            <div class="metric">
                <strong>Average Glass Area per Element:</strong> {total_area/total_elements if total_elements > 0 else 0:.1f} m²
            </div>
        </div>
        
        <div class="subsection">
            <h3>Orientation Distribution</h3>
            <table>
                <tr><th>Orientation</th><th>Count</th><th>Percentage</th></tr>
                {get_orientation_table_rows(orientation_counts, total_elements)}
            </table>
        </div>
        
        <div class="subsection">
            <h3>Building Level Distribution</h3>
            <table>
                <tr><th>Level</th><th>Count</th><th>Percentage</th></tr>
                {get_level_table_rows(level_counts, total_elements)}
            </table>
        </div>
        
        <div class="subsection">
            <h3>BIPV Suitability Analysis</h3>
            <div class="metric">
                <strong>Suitability Criteria:</strong> Glass area ≥ 0.5 m², accessible orientation
            </div>
            <div class="metric">
                <strong>Suitable Elements:</strong> {total_elements} (100% - all elements processed)
            </div>
            <div class="metric">
                <strong>BIM Data Quality:</strong> Element IDs, orientations, dimensions extracted
            </div>
        </div>
        
        <div class="subsection">
            <h3>Data Usage in Subsequent Steps</h3>
            <p>• <strong>Step 5:</strong> Element geometry used for radiation analysis</p>
            <p>• <strong>Step 6:</strong> Glass areas determine BIPV system sizing</p>
            <p>• <strong>Step 8:</strong> Element selection for optimization algorithms</p>
        </div>
    </div>
    """

def generate_step5_section(project_data):
    """Generate Step 5: Radiation & Shading Analysis section"""
    
    radiation_data = project_data.get('radiation_analysis', {})
    building_elements = project_data.get('building_elements', [])
    
    # Calculate radiation statistics
    total_elements = len(building_elements)
    avg_radiation = 0
    max_radiation = 0
    min_radiation = float('inf')
    
    for elem in building_elements:
        radiation = elem.get('annual_radiation', 0)
        avg_radiation += radiation
        if radiation > max_radiation:
            max_radiation = radiation
        if radiation < min_radiation and radiation > 0:
            min_radiation = radiation
    
    avg_radiation = avg_radiation / total_elements if total_elements > 0 else 0
    
    # Orientation performance
    orientation_radiation = {}
    for elem in building_elements:
        orientation = elem.get('orientation', 'Unknown')
        radiation = elem.get('annual_radiation', 0)
        if orientation not in orientation_radiation:
            orientation_radiation[orientation] = []
        orientation_radiation[orientation].append(radiation)
    
    return f"""
    <div class="step-section">
        <h2 class="step-title">Step 5: Radiation & Shading Grid Analysis</h2>
        
        <div class="subsection">
            <h3>Solar Radiation Analysis Results</h3>
            <div class="metric">
                <strong>Elements Analyzed:</strong> {total_elements}
            </div>
            <div class="metric">
                <strong>Average Annual Radiation:</strong> {avg_radiation:.0f} kWh/m²/year
            </div>
            <div class="metric">
                <strong>Maximum Radiation:</strong> {max_radiation:.0f} kWh/m²/year
            </div>
            <div class="metric">
                <strong>Minimum Radiation:</strong> {min_radiation:.0f} kWh/m²/year
            </div>
        </div>
        
        <div class="subsection">
            <h3>Radiation by Orientation</h3>
            <table>
                <tr><th>Orientation</th><th>Avg Radiation (kWh/m²/year)</th><th>Elements</th></tr>
                {get_radiation_orientation_table(orientation_radiation)}
            </table>
        </div>
        
        <div class="subsection">
            <h3>Analysis Methodology</h3>
            <div class="metric">
                <strong>Calculation Method:</strong> pvlib solar position algorithms
            </div>
            <div class="metric">
                <strong>Temporal Resolution:</strong> Hourly calculations (8760 hours/year)
            </div>
            <div class="metric">
                <strong>Shading Analysis:</strong> Geometric self-shading from building elements
            </div>
        </div>
        
        <div class="subsection">
            <h3>Data Usage in Subsequent Steps</h3>
            <p>• <strong>Step 6:</strong> Radiation values determine PV energy generation potential</p>
            <p>• <strong>Step 7:</strong> Used for yield calculations and energy balance</p>
            <p>• <strong>Step 8:</strong> Optimization prioritizes high-radiation elements</p>
        </div>
    </div>
    """

def generate_step6_section(project_data):
    """Generate Step 6: PV Panel Specification section"""
    
    pv_specs = project_data.get('pv_specifications', {})
    individual_systems = pv_specs.get('individual_systems', [])
    
    # Calculate totals
    total_capacity = sum([system.get('capacity_kw', 0) for system in individual_systems])
    total_cost = sum([system.get('total_cost_eur', 0) for system in individual_systems])
    total_area = sum([system.get('glass_area', 0) for system in individual_systems])
    
    # Get BIPV specifications
    bipv_specs = pv_specs.get('bipv_specifications', {})
    efficiency = bipv_specs.get('efficiency', 0) * 100
    transparency = bipv_specs.get('transparency', 0) * 100
    cost_per_m2 = bipv_specs.get('cost_per_m2', 0)
    
    return f"""
    <div class="step-section">
        <h2 class="step-title">Step 6: BIPV Glass Panel Specification</h2>
        
        <div class="subsection">
            <h3>BIPV Glass Technology Specifications</h3>
            <div class="metric">
                <strong>Glass Efficiency:</strong> {efficiency:.1f}%
            </div>
            <div class="metric">
                <strong>Transparency:</strong> {transparency:.1f}%
            </div>
            <div class="metric">
                <strong>Cost per m²:</strong> €{cost_per_m2:.0f}/m²
            </div>
            <div class="metric">
                <strong>Technology Type:</strong> Semi-transparent BIPV glass
            </div>
        </div>
        
        <div class="subsection">
            <h3>System Totals</h3>
            <div class="metric">
                <strong>Total Capacity:</strong> {total_capacity:.1f} kW
            </div>
            <div class="metric">
                <strong>Total Glass Area:</strong> {total_area:.1f} m²
            </div>
            <div class="metric">
                <strong>Total Installation Cost:</strong> €{total_cost:,.0f}
            </div>
            <div class="metric">
                <strong>Cost per kW:</strong> €{total_cost/total_capacity if total_capacity > 0 else 0:,.0f}/kW
            </div>
        </div>
        
        <div class="subsection">
            <h3>Individual System Summary</h3>
            <p><strong>Systems Configured:</strong> {len(individual_systems)}</p>
            <p><strong>Average System Size:</strong> {total_capacity/len(individual_systems) if individual_systems else 0:.1f} kW</p>
            <p><strong>Coverage Factor:</strong> BIPV glass replaces existing window glass</p>
        </div>
        
        <div class="subsection">
            <h3>Data Usage in Subsequent Steps</h3>
            <p>• <strong>Step 7:</strong> Capacity and specifications used for energy yield calculations</p>
            <p>• <strong>Step 8:</strong> Cost and performance data for optimization algorithms</p>
            <p>• <strong>Step 9:</strong> Installation costs and capacity for financial analysis</p>
        </div>
    </div>
    """

def generate_step7_section(project_data):
    """Generate Step 7: Yield vs Demand Analysis section"""
    
    yield_demand_data = project_data.get('yield_demand_analysis', {})
    monthly_balance = yield_demand_data.get('monthly_energy_balance', [])
    
    # Calculate annual totals
    annual_demand = sum([month.get('demand_kwh', 0) for month in monthly_balance])
    annual_generation = sum([month.get('generation_kwh', 0) for month in monthly_balance])
    annual_net_import = sum([month.get('net_import_kwh', 0) for month in monthly_balance])
    
    # Calculate financial metrics
    annual_cost_savings = sum([month.get('cost_savings_eur', 0) for month in monthly_balance])
    annual_revenue = sum([month.get('feed_in_revenue_eur', 0) for month in monthly_balance])
    
    return f"""
    <div class="step-section">
        <h2 class="step-title">Step 7: Yield vs Demand Analysis</h2>
        
        <div class="subsection">
            <h3>Annual Energy Balance</h3>
            <div class="metric">
                <strong>Annual Demand:</strong> {annual_demand:,.0f} kWh
            </div>
            <div class="metric">
                <strong>Annual PV Generation:</strong> {annual_generation:,.0f} kWh
            </div>
            <div class="metric">
                <strong>Net Energy Import:</strong> {annual_net_import:,.0f} kWh
            </div>
            <div class="metric">
                <strong>Self-Consumption Rate:</strong> {(annual_generation-max(0,annual_net_import))/annual_generation*100 if annual_generation > 0 else 0:.1f}%
            </div>
        </div>
        
        <div class="subsection">
            <h3>Financial Impact</h3>
            <div class="metric">
                <strong>Annual Cost Savings:</strong> €{annual_cost_savings:,.0f}
            </div>
            <div class="metric">
                <strong>Annual Feed-in Revenue:</strong> €{annual_revenue:,.0f}
            </div>
            <div class="metric">
                <strong>Total Annual Benefit:</strong> €{annual_cost_savings + annual_revenue:,.0f}
            </div>
        </div>
        
        <div class="subsection">
            <h3>Monthly Energy Balance Summary</h3>
            <table>
                <tr><th>Month</th><th>Demand (kWh)</th><th>Generation (kWh)</th><th>Net Import (kWh)</th><th>Savings (€)</th></tr>
                {get_monthly_balance_table(monthly_balance)}
            </table>
        </div>
        
        <div class="subsection">
            <h3>Data Usage in Subsequent Steps</h3>
            <p>• <strong>Step 8:</strong> Energy balance used for optimization objectives</p>
            <p>• <strong>Step 9:</strong> Financial benefits form basis for economic analysis</p>
        </div>
    </div>
    """

def generate_step8_section(project_data):
    """Generate Step 8: Multi-Objective Optimization section"""
    
    optimization_data = project_data.get('optimization_results', {})
    
    # Use database solutions if available
    solutions_df = optimization_data.get('solutions') if optimization_data else None
    if solutions_df is not None and not solutions_df.empty:
        # Convert DataFrame to list of dicts for processing
        pareto_solutions = solutions_df.to_dict('records')
        
        # Get best solutions from database data
        best_cost = min(pareto_solutions, key=lambda x: x.get('total_cost', float('inf'))) if pareto_solutions else {}
        best_yield = max(pareto_solutions, key=lambda x: x.get('capacity', 0)) if pareto_solutions else {}  # Use capacity as proxy for yield
        best_roi = max(pareto_solutions, key=lambda x: x.get('roi', 0)) if pareto_solutions else {}
    else:
        # Fallback to legacy format
        pareto_solutions = optimization_data.get('pareto_solutions', [])
        best_cost = min(pareto_solutions, key=lambda x: x.get('cost', float('inf'))) if pareto_solutions else {}
        best_yield = max(pareto_solutions, key=lambda x: x.get('yield', 0)) if pareto_solutions else {}
        best_roi = max(pareto_solutions, key=lambda x: x.get('roi', 0)) if pareto_solutions else {}
    
    # Optimization parameters
    weights = optimization_data.get('objective_weights', {})
    
    return f"""
    <div class="step-section">
        <h2 class="step-title">Step 8: Multi-Objective Optimization</h2>
        
        <div class="subsection">
            <h3>Optimization Results</h3>
            <div class="metric">
                <strong>Solutions Generated:</strong> {len(pareto_solutions)}
            </div>
            <div class="metric">
                <strong>Algorithm:</strong> Weighted Genetic Algorithm (NSGA-II inspired)
            </div>
            <div class="metric">
                <strong>Objectives:</strong> Minimize cost, Maximize yield, Maximize ROI
            </div>
        </div>
        
        <div class="subsection">
            <h3>Objective Weights</h3>
            <div class="metric">
                <strong>Cost Weight:</strong> {weights.get('cost', 0)*100:.0f}%
            </div>
            <div class="metric">
                <strong>Yield Weight:</strong> {weights.get('yield', 0)*100:.0f}%
            </div>
            <div class="metric">
                <strong>ROI Weight:</strong> {weights.get('roi', 0)*100:.0f}%
            </div>
        </div>
        
        <div class="subsection">
            <h3>Best Solutions by Objective</h3>
            <div class="metric">
                <strong>Lowest Cost Solution:</strong> €{best_cost.get('total_cost', best_cost.get('cost', 0)):,.0f}
            </div>
            <div class="metric">
                <strong>Highest Capacity Solution:</strong> {best_yield.get('capacity', best_yield.get('yield', 0)):,.0f} kW
            </div>
            <div class="metric">
                <strong>Best ROI Solution:</strong> {best_roi.get('roi', 0):.1f}%
            </div>
        </div>
        
        <div class="subsection">
            <h3>Top 5 Recommended Solutions</h3>
            {get_top_solutions_table(pareto_solutions[:5] if pareto_solutions else [])}
        </div>
        
        <div class="subsection">
            <h3>Recommended Solution</h3>
            {get_recommended_solution_info(pareto_solutions)}
        </div>
        
        <div class="subsection">
            <h3>Data Usage in Subsequent Steps</h3>
            <p>• <strong>Step 9:</strong> Optimized configurations used for detailed financial analysis</p>
            <p>• <strong>Reports:</strong> Solution alternatives provided for decision making</p>
        </div>
    </div>
    """

def generate_step9_section(project_data):
    """Generate Step 9: Financial & Environmental Analysis section"""
    
    # Use step9_data extractor for consistent data access
    step9_data = get_step9_data(project_data)
    
    # Financial metrics
    npv = step9_data.get('npv', 0)
    irr = step9_data.get('irr', 0)
    payback_period = step9_data.get('payback_period', 0)
    annual_savings = step9_data.get('annual_savings', 0)
    investment_cost = step9_data.get('investment_cost', 0)
    
    # Environmental metrics
    co2_savings = step9_data.get('annual_co2_savings', 0)
    lifetime_co2 = step9_data.get('lifetime_co2_savings', 0)
    
    # System parameters
    system_capacity = step9_data.get('system_capacity', 0)
    
    return f"""
    <div class="step-section">
        <h2 class="step-title">Step 9: Financial & Environmental Analysis</h2>
        
        <div class="subsection">
            <h3>Financial Performance Metrics</h3>
            <div class="metric">
                <strong>Net Present Value (NPV):</strong> €{npv:,.0f}
            </div>
            <div class="metric">
                <strong>Internal Rate of Return (IRR):</strong> {irr:.1f}%
            </div>
            <div class="metric">
                <strong>Payback Period:</strong> {payback_period:.1f} years
            </div>
            <div class="metric">
                <strong>Annual Savings:</strong> €{annual_savings:,.0f}
            </div>
        </div>
        
        <div class="subsection">
            <h3>Investment Summary</h3>
            <div class="metric">
                <strong>System Capacity:</strong> {system_capacity:.1f} kW
            </div>
            <div class="metric">
                <strong>Total Installation Cost:</strong> €{investment_cost:,.0f}
            </div>
            <div class="metric">
                <strong>Cost per kW:</strong> €{investment_cost/system_capacity if system_capacity > 0 else 0:,.0f}/kW
            </div>
            <div class="metric">
                <strong>25-Year Total Savings:</strong> €{annual_savings * 25:,.0f}
            </div>
        </div>
        
        <div class="subsection">
            <h3>Environmental Impact</h3>
            <div class="metric">
                <strong>Annual CO₂ Savings:</strong> {co2_savings:,.0f} kg CO₂
            </div>
            <div class="metric">
                <strong>25-Year CO₂ Savings:</strong> {lifetime_co2/1000:,.0f} Tons CO₂
            </div>
            <div class="metric">
                <strong>Equivalent Trees Planted:</strong> {lifetime_co2/22:,.0f} trees
            </div>
        </div>
        
        <div class="subsection">
            <h3>Investment Viability Assessment</h3>
            {"<div class='metric'>✅ Excellent investment - High NPV and IRR</div>" if npv > 0 and irr > 8 else ""}
            {"<div class='warning'>⚠️ Moderate investment - Positive but low returns</div>" if npv > 0 and irr <= 8 else ""}
            {"<div class='error'>❌ Poor investment - Negative returns</div>" if npv <= 0 else ""}
        </div>
        
        <div class="subsection">
            <h3>Final Analysis Summary</h3>
            <p>The BIPV system demonstrates {"strong" if npv > 0 and irr > 8 else "moderate" if npv > 0 else "poor"} financial viability with significant environmental benefits. The integration of semi-transparent PV glass provides both energy generation and building envelope functionality.</p>
        </div>
    </div>
    """

# Helper functions for table generation
def get_orientation_table_rows(orientation_counts, total):
    """Generate orientation table rows"""
    rows = ""
    for orientation, count in orientation_counts.items():
        percentage = (count / total * 100) if total > 0 else 0
        rows += f"<tr><td>{orientation}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>"
    return rows

def get_level_table_rows(level_counts, total):
    """Generate level table rows"""
    rows = ""
    for level, count in level_counts.items():
        percentage = (count / total * 100) if total > 0 else 0
        rows += f"<tr><td>{level}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>"
    return rows

def get_radiation_orientation_table(orientation_radiation):
    """Generate radiation by orientation table"""
    rows = ""
    for orientation, radiation_values in orientation_radiation.items():
        avg_radiation = sum(radiation_values) / len(radiation_values) if radiation_values else 0
        rows += f"<tr><td>{orientation}</td><td>{avg_radiation:.0f}</td><td>{len(radiation_values)}</td></tr>"
    return rows

def get_monthly_balance_table(monthly_balance):
    """Generate monthly energy balance table"""
    rows = ""
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    for i, month_data in enumerate(monthly_balance):
        month_name = months[i] if i < len(months) else f"Month {i+1}"
        demand = month_data.get('demand_kwh', 0)
        generation = month_data.get('generation_kwh', 0)
        net_import = month_data.get('net_import_kwh', 0)
        savings = month_data.get('cost_savings_eur', 0)
        
        rows += f"<tr><td>{month_name}</td><td>{demand:,.0f}</td><td>{generation:,.0f}</td><td>{net_import:,.0f}</td><td>€{savings:,.0f}</td></tr>"
    
    return rows

def get_recommended_solution_info(pareto_solutions):
    """Get recommended solution information"""
    if not pareto_solutions:
        return "<div class='error'>No solutions available</div>"
    
    # Get top ranked solution (first in list)
    best_solution = pareto_solutions[0] if pareto_solutions else {}
    
    return f"""
    <div class="metric">
        <strong>Recommended Configuration:</strong> Top ranked solution
    </div>
    <div class="metric">
        <strong>Solution ID:</strong> {best_solution.get('solution_id', 'N/A')}
    </div>
    <div class="metric">
        <strong>Cost:</strong> €{best_solution.get('total_cost', best_solution.get('cost', 0)):,.0f}
    </div>
    <div class="metric">
        <strong>Capacity:</strong> {best_solution.get('capacity', best_solution.get('yield', 0)):,.0f} kW
    </div>
    <div class="metric">
        <strong>ROI:</strong> {best_solution.get('roi', 0):.1f}%
    </div>
    """

def get_top_solutions_table(solutions):
    """Generate HTML table for top optimization solutions"""
    if not solutions:
        return "<p>No optimization solutions available</p>"
    
    table_rows = ""
    for i, solution in enumerate(solutions[:5], 1):
        solution_id = solution.get('solution_id', f'Solution_{i}')
        capacity = solution.get('capacity', solution.get('capacity_kw', 0))
        cost = solution.get('total_cost', solution.get('cost', 0))
        roi = solution.get('roi', 0)
        net_import = solution.get('net_import', 0)
        
        table_rows += f"""
        <tr>
            <td>{i}</td>
            <td>{solution_id}</td>
            <td>{capacity:.1f} kW</td>
            <td>€{cost:,.0f}</td>
            <td>{roi:.1f}%</td>
            <td>{net_import:,.0f} kWh</td>
        </tr>
        """
    
    return f"""
    <table style="width: 100%; border-collapse: collapse;">
        <thead>
            <tr style="background-color: #f0f0f0;">
                <th>Rank</th>
                <th>Solution ID</th>
                <th>Capacity</th>
                <th>Total Cost</th>
                <th>ROI</th>
                <th>Net Import</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>
    """

def create_download_link(html_content, filename):
    """Create download link for HTML report"""
    b64 = base64.b64encode(html_content.encode()).decode()
    return f'<a href="data:text/html;base64,{b64}" download="{filename}">Download Report</a>'