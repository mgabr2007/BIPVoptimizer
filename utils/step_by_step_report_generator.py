"""
Step-by-Step HTML Report Generator for BIPV Optimizer
Creates detailed HTML reports showing analysis results from each workflow step
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
from utils.consolidated_data_manager import ConsolidatedDataManager

def safe_get(data, key, default=None):
    """Safely get value from dictionary"""
    if isinstance(data, dict):
        return data.get(key, default)
    return default

def safe_float(value, default=0.0):
    """Safely convert value to float"""
    try:
        if value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

def generate_step1_section(project_data):
    """Generate Step 1: Project Setup section"""
    location = safe_get(project_data, 'location', 'Unknown Location')
    coordinates = safe_get(project_data, 'coordinates', {})
    lat = safe_float(coordinates.get('lat'), 0.0)
    lon = safe_float(coordinates.get('lon'), 0.0)
    weather_station = safe_get(project_data, 'selected_weather_station', {})
    
    return f"""
    <div class="step-section">
        <h2>🗺️ Step 1: Project Setup</h2>
        <div class="content-grid">
            <div class="info-card">
                <h3>Project Information</h3>
                <p><strong>Project Name:</strong> {safe_get(project_data, 'project_name', 'BIPV Analysis Project')}</p>
                <p><strong>Location:</strong> {location}</p>
                <p><strong>Coordinates:</strong> {lat:.4f}°, {lon:.4f}°</p>
                <p><strong>Timezone:</strong> {safe_get(project_data, 'timezone', 'UTC')}</p>
                <p><strong>Currency:</strong> EUR (Standardized)</p>
            </div>
            
            <div class="info-card">
                <h3>Weather Station Integration</h3>
                <p><strong>Station Name:</strong> {safe_get(weather_station, 'name', 'Not selected')}</p>
                <p><strong>WMO ID:</strong> {safe_get(weather_station, 'wmo_id', 'N/A')}</p>
                <p><strong>Distance:</strong> {safe_float(safe_get(weather_station, 'distance'), 0):.1f} km</p>
                <p><strong>Country:</strong> {safe_get(weather_station, 'country', 'N/A')}</p>
            </div>
        </div>
    </div>
    """

def generate_step2_section(historical_data):
    """Generate Step 2: Historical Data Analysis section"""
    if not historical_data:
        return """
        <div class="step-section">
            <h2>🤖 Step 2: Historical Data Analysis</h2>
            <p class="no-data">No historical data analysis completed</p>
        </div>
        """
    
    model_performance = safe_get(historical_data, 'model_performance', {})
    r2_score = safe_float(safe_get(model_performance, 'r2_score'), 0.0)
    demand_forecast = safe_get(historical_data, 'demand_forecast', {})
    
    return f"""
    <div class="step-section">
        <h2>🤖 Step 2: Historical Data Analysis</h2>
        <div class="content-grid">
            <div class="info-card">
                <h3>AI Model Performance</h3>
                <p><strong>R² Score:</strong> {r2_score:.3f}</p>
                <p><strong>Model Type:</strong> Random Forest Regressor</p>
                <p><strong>Training Features:</strong> Temperature, Seasonality, Occupancy</p>
                <p><strong>Performance:</strong> {'Excellent' if r2_score >= 0.85 else 'Good' if r2_score >= 0.70 else 'Needs Improvement'}</p>
            </div>
            
            <div class="info-card">
                <h3>Demand Forecast</h3>
                <p><strong>Forecast Period:</strong> 25 years</p>
                <p><strong>Annual Growth Rate:</strong> {safe_float(safe_get(demand_forecast, 'growth_rate'), 0.0):.2f}%</p>
                <p><strong>Baseline Consumption:</strong> {safe_float(safe_get(demand_forecast, 'baseline_annual'), 0.0):,.0f} kWh/year</p>
            </div>
        </div>
    </div>
    """

def generate_step3_section(weather_data):
    """Generate Step 3: Weather Environment section"""
    if not weather_data:
        return """
        <div class="step-section">
            <h2>☀️ Step 3: Weather Environment</h2>
            <p class="no-data">No weather analysis completed</p>
        </div>
        """
    
    tmy_data = safe_get(weather_data, 'tmy_data', {})
    solar_params = safe_get(weather_data, 'solar_parameters', {})
    
    return f"""
    <div class="step-section">
        <h2>☀️ Step 3: Weather Environment</h2>
        <div class="content-grid">
            <div class="info-card">
                <h3>Solar Resource Assessment</h3>
                <p><strong>Annual GHI:</strong> {safe_float(safe_get(solar_params, 'annual_ghi'), 0.0):,.0f} kWh/m²</p>
                <p><strong>Peak Sun Hours:</strong> {safe_float(safe_get(solar_params, 'peak_sun_hours'), 0.0):.1f} hours/day</p>
                <p><strong>Solar Resource Class:</strong> {safe_get(solar_params, 'resource_class', 'Unknown')}</p>
                <p><strong>Climate Zone:</strong> {safe_get(solar_params, 'climate_zone', 'Unknown')}</p>
            </div>
            
            <div class="info-card">
                <h3>TMY Data Quality</h3>
                <p><strong>Data Points:</strong> 8,760 hourly records</p>
                <p><strong>Standard:</strong> ISO 15927-4 compliant</p>
                <p><strong>Source:</strong> WMO weather station data</p>
                <p><strong>Quality Score:</strong> {safe_get(tmy_data, 'quality_score', 'High')}</p>
            </div>
        </div>
    </div>
    """

def generate_step4_section(building_data):
    """Generate Step 4: Facade Extraction section"""
    if not building_data or not safe_get(building_data, 'building_elements'):
        return """
        <div class="step-section">
            <h2>🏢 Step 4: Facade Extraction</h2>
            <p class="no-data">No building elements extracted</p>
        </div>
        """
    
    elements = safe_get(building_data, 'building_elements', [])
    total_elements = len(elements)
    total_area = sum(safe_float(elem.get('glass_area', 0)) for elem in elements)
    
    # Count by orientation
    orientations = {}
    for elem in elements:
        orientation = elem.get('orientation', 'Unknown')
        orientations[orientation] = orientations.get(orientation, 0) + 1
    
    return f"""
    <div class="step-section">
        <h2>🏢 Step 4: Facade Extraction</h2>
        <div class="content-grid">
            <div class="info-card">
                <h3>Building Elements Summary</h3>
                <p><strong>Total Elements:</strong> {total_elements:,}</p>
                <p><strong>Total Glass Area:</strong> {total_area:,.1f} m²</p>
                <p><strong>Element Types:</strong> Windows, Curtain Walls, Glazing</p>
                <p><strong>Data Source:</strong> BIM Model (CSV Export)</p>
            </div>
            
            <div class="info-card">
                <h3>Orientation Distribution</h3>
                {''.join([f'<p><strong>{orientation}:</strong> {count} elements</p>' for orientation, count in orientations.items()])}
            </div>
        </div>
    </div>
    """

def generate_step5_section(radiation_data):
    """Generate Step 5: Radiation Analysis section"""
    if not radiation_data:
        return """
        <div class="step-section">
            <h2>☀️ Step 5: Radiation Analysis</h2>
            <p class="no-data">No radiation analysis completed</p>
        </div>
        """
    
    radiation_results = safe_get(radiation_data, 'radiation_results', {})
    analysis_summary = safe_get(radiation_data, 'analysis_summary', {})
    
    return f"""
    <div class="step-section">
        <h2>☀️ Step 5: Radiation Analysis</h2>
        <div class="content-grid">
            <div class="info-card">
                <h3>Solar Radiation Results</h3>
                <p><strong>Elements Analyzed:</strong> {safe_get(analysis_summary, 'total_elements', 0):,}</p>
                <p><strong>Average Annual Radiation:</strong> {safe_float(safe_get(analysis_summary, 'average_radiation'), 0.0):,.0f} kWh/m²</p>
                <p><strong>Highest Performing Element:</strong> {safe_float(safe_get(analysis_summary, 'max_radiation'), 0.0):,.0f} kWh/m²</p>
                <p><strong>Analysis Method:</strong> pvlib solar position calculations</p>
            </div>
            
            <div class="info-card">
                <h3>Shading Analysis</h3>
                <p><strong>Self-Shading:</strong> Building geometry considered</p>
                <p><strong>Environmental Factors:</strong> Vegetation and urban shading</p>
                <p><strong>Time Resolution:</strong> Hourly calculations</p>
                <p><strong>Precision Level:</strong> {safe_get(radiation_data, 'precision_level', 'Standard')}</p>
            </div>
        </div>
    </div>
    """

def generate_step6_section(pv_data):
    """Generate Step 6: PV Specification section"""
    if not pv_data:
        return """
        <div class="step-section">
            <h2>🔋 Step 6: PV Specification</h2>
            <p class="no-data">No PV specifications completed</p>
        </div>
        """
    
    individual_systems = safe_get(pv_data, 'individual_systems', [])
    system_summary = safe_get(pv_data, 'system_summary', {})
    
    total_capacity = safe_float(safe_get(system_summary, 'total_capacity_kw'), 0.0)
    total_cost = safe_float(safe_get(system_summary, 'total_cost_eur'), 0.0)
    
    return f"""
    <div class="step-section">
        <h2>🔋 Step 6: PV Specification</h2>
        <div class="content-grid">
            <div class="info-card">
                <h3>BIPV System Overview</h3>
                <p><strong>Total Systems:</strong> {len(individual_systems):,}</p>
                <p><strong>Total Capacity:</strong> {total_capacity:,.1f} kW</p>
                <p><strong>Total Investment:</strong> €{total_cost:,.0f}</p>
                <p><strong>Technology:</strong> Semi-transparent BIPV glass</p>
            </div>
            
            <div class="info-card">
                <h3>BIPV Glass Specifications</h3>
                <p><strong>Efficiency Range:</strong> 8-15% (typical BIPV)</p>
                <p><strong>Transparency:</strong> 15-40%</p>
                <p><strong>Glass Thickness:</strong> 6-12mm</p>
                <p><strong>Cost Range:</strong> €300-800/m²</p>
            </div>
        </div>
    </div>
    """

def generate_step7_section(yield_data):
    """Generate Step 7: Yield vs Demand section"""
    if not yield_data:
        return """
        <div class="step-section">
            <h2>⚡ Step 7: Yield vs Demand</h2>
            <p class="no-data">No yield analysis completed</p>
        </div>
        """
    
    annual_metrics = safe_get(yield_data, 'annual_metrics', {})
    energy_balance = safe_get(yield_data, 'energy_balance', [])
    
    total_yield = safe_float(safe_get(annual_metrics, 'total_annual_yield'), 0.0)
    annual_demand = safe_float(safe_get(annual_metrics, 'annual_demand'), 0.0)
    coverage_ratio = safe_float(safe_get(annual_metrics, 'coverage_ratio'), 0.0)
    annual_savings = safe_float(safe_get(annual_metrics, 'total_annual_savings'), 0.0)
    
    return f"""
    <div class="step-section">
        <h2>⚡ Step 7: Yield vs Demand</h2>
        <div class="content-grid">
            <div class="info-card">
                <h3>Energy Balance</h3>
                <p><strong>Annual PV Yield:</strong> {total_yield:,.0f} kWh</p>
                <p><strong>Annual Demand:</strong> {annual_demand:,.0f} kWh</p>
                <p><strong>Coverage Ratio:</strong> {coverage_ratio:.1f}%</p>
                <p><strong>Monthly Balance:</strong> {len(energy_balance)} months analyzed</p>
            </div>
            
            <div class="info-card">
                <h3>Economic Performance</h3>
                <p><strong>Annual Savings:</strong> €{annual_savings:,.0f}</p>
                <p><strong>Feed-in Revenue:</strong> €{safe_float(safe_get(annual_metrics, 'total_feed_in_revenue'), 0.0):,.0f}</p>
                <p><strong>Self-Consumption:</strong> Priority energy use</p>
                <p><strong>Grid Export:</strong> Surplus energy sold</p>
            </div>
        </div>
    </div>
    """

def generate_step8_section(optimization_data):
    """Generate Step 8: Optimization section"""
    if not optimization_data:
        return """
        <div class="step-section">
            <h2>🎯 Step 8: Multi-Objective Optimization</h2>
            <p class="no-data">No optimization completed</p>
        </div>
        """
    
    solutions = safe_get(optimization_data, 'solutions', [])
    pareto_solutions = safe_get(optimization_data, 'pareto_solutions', [])
    
    return f"""
    <div class="step-section">
        <h2>🎯 Step 8: Multi-Objective Optimization</h2>
        <div class="content-grid">
            <div class="info-card">
                <h3>Optimization Results</h3>
                <p><strong>Solutions Found:</strong> {len(solutions):,}</p>
                <p><strong>Pareto-Optimal:</strong> {len(pareto_solutions):,} solutions</p>
                <p><strong>Algorithm:</strong> NSGA-II Genetic Algorithm</p>
                <p><strong>Objectives:</strong> Minimize Cost, Maximize Yield, Maximize ROI</p>
            </div>
            
            <div class="info-card">
                <h3>Best Solution Metrics</h3>
                {f'<p><strong>Best Investment:</strong> €{safe_float(solutions[0].get("total_investment", 0) if solutions else 0):,.0f}</p>' if solutions else '<p>No solutions available</p>'}
                {f'<p><strong>Best Annual Energy:</strong> {safe_float(solutions[0].get("annual_energy_kwh", 0) if solutions else 0):,.0f} kWh</p>' if solutions else ''}
                {f'<p><strong>Best ROI:</strong> {safe_float(solutions[0].get("roi", 0) if solutions else 0):.1f}%</p>' if solutions else ''}
                <p><strong>Optimization Status:</strong> Completed</p>
            </div>
        </div>
    </div>
    """

def generate_step9_section(financial_data):
    """Generate Step 9: Financial Analysis section"""
    if not financial_data:
        return """
        <div class="step-section">
            <h2>💰 Step 9: Financial Analysis</h2>
            <p class="no-data">No financial analysis completed</p>
        </div>
        """
    
    economic_metrics = safe_get(financial_data, 'economic_metrics', {})
    environmental_impact = safe_get(financial_data, 'environmental_impact', {})
    
    npv = safe_float(safe_get(economic_metrics, 'npv'), 0.0)
    irr = safe_float(safe_get(economic_metrics, 'irr'), 0.0)
    payback = safe_float(safe_get(economic_metrics, 'payback_period'), 0.0)
    co2_savings = safe_float(safe_get(environmental_impact, 'lifetime_co2_savings'), 0.0)
    
    return f"""
    <div class="step-section">
        <h2>💰 Step 9: Financial Analysis</h2>
        <div class="content-grid">
            <div class="info-card">
                <h3>Financial Performance</h3>
                <p><strong>Net Present Value:</strong> €{npv:,.0f}</p>
                <p><strong>Internal Rate of Return:</strong> {irr:.1f}%</p>
                <p><strong>Payback Period:</strong> {payback:.1f} years</p>
                <p><strong>Investment Viability:</strong> {'Excellent' if npv > 50000 else 'Good' if npv > 0 else 'Marginal'}</p>
            </div>
            
            <div class="info-card">
                <h3>Environmental Impact</h3>
                <p><strong>Lifetime CO₂ Savings:</strong> {co2_savings:,.0f} kg</p>
                <p><strong>Annual CO₂ Reduction:</strong> {safe_float(safe_get(environmental_impact, 'annual_co2_savings'), 0.0):,.0f} kg</p>
                <p><strong>Carbon Value:</strong> €{safe_float(safe_get(environmental_impact, 'carbon_value'), 0.0):,.0f}</p>
                <p><strong>Grid CO₂ Factor:</strong> {safe_float(safe_get(environmental_impact, 'grid_co2_factor'), 0.0):.3f} kg/kWh</p>
            </div>
        </div>
    </div>
    """

def generate_comprehensive_html_report():
    """Generate comprehensive HTML report with all workflow steps"""
    
    # Get consolidated data
    consolidated_manager = ConsolidatedDataManager()
    consolidated_data = consolidated_manager.get_consolidated_data()
    
    # Extract project information
    project_info = safe_get(consolidated_data, 'project_info', {})
    project_name = safe_get(project_info, 'project_name', 'BIPV Analysis Project')
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # CSS Styles
    css_styles = """
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f8f9fa;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            padding: 30px;
        }
        .header {
            text-align: center;
            border-bottom: 3px solid #2E8B57;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #2E8B57;
            font-size: 2.5em;
            margin: 0;
        }
        .header p {
            color: #666;
            font-size: 1.1em;
            margin: 10px 0 0 0;
        }
        .step-section {
            margin-bottom: 40px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 25px;
            background-color: #fafafa;
        }
        .step-section h2 {
            color: #2E8B57;
            border-bottom: 2px solid #2E8B57;
            padding-bottom: 10px;
            margin-top: 0;
        }
        .content-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 20px;
        }
        .info-card {
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .info-card h3 {
            color: #2E8B57;
            margin-top: 0;
            margin-bottom: 15px;
            font-size: 1.2em;
        }
        .info-card p {
            margin: 8px 0;
            line-height: 1.5;
        }
        .no-data {
            text-align: center;
            color: #888;
            font-style: italic;
            padding: 20px;
        }
        .footer {
            text-align: center;
            border-top: 2px solid #2E8B57;
            padding-top: 20px;
            margin-top: 40px;
            color: #666;
        }
        .footer a {
            color: #2E8B57;
            text-decoration: none;
        }
        .summary-box {
            background: linear-gradient(135deg, #2E8B57, #3CB371);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        .summary-box h2 {
            margin-top: 0;
            color: white;
        }
        @media (max-width: 768px) {
            .content-grid {
                grid-template-columns: 1fr;
            }
            .container {
                padding: 15px;
            }
        }
    </style>
    """
    
    # Generate HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BIPV Analysis Report - {project_name}</title>
        {css_styles}
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌟 BIPV Analysis Report</h1>
                <p><strong>Project:</strong> {project_name}</p>
                <p><strong>Generated:</strong> {timestamp}</p>
                <p><strong>Platform:</strong> BIPV Optimizer - Building Integrated Photovoltaics Analysis</p>
            </div>
            
            <div class="summary-box">
                <h2>📊 Analysis Summary</h2>
                <p>This comprehensive report presents the complete Building Integrated Photovoltaics (BIPV) analysis 
                workflow results. Each section corresponds to a workflow step, showing actual calculated values and 
                analysis outcomes from your project data.</p>
            </div>
            
            {generate_step1_section(safe_get(consolidated_data, 'step1_project_setup', {}))}
            {generate_step2_section(safe_get(consolidated_data, 'step2_historical_data', {}))}
            {generate_step3_section(safe_get(consolidated_data, 'step3_weather_environment', {}))}
            {generate_step4_section(safe_get(consolidated_data, 'step4_facade_extraction', {}))}
            {generate_step5_section(safe_get(consolidated_data, 'step5_radiation_analysis', {}))}
            {generate_step6_section(safe_get(consolidated_data, 'step6_pv_specification', {}))}
            {generate_step7_section(safe_get(consolidated_data, 'step7_yield_demand', {}))}
            {generate_step8_section(safe_get(consolidated_data, 'step8_optimization', {}))}
            {generate_step9_section(safe_get(consolidated_data, 'step9_financial_analysis', {}))}
            
            <div class="footer">
                <p><strong>BIPV Optimizer Platform</strong></p>
                <p>Developed by <strong>Mostafa Gabr</strong>, PhD Candidate<br>
                Technische Universität Berlin, Faculty VI - Planning Building Environment</p>
                <p><a href="https://www.researchgate.net/profile/Mostafa-Gabr-4" target="_blank">ResearchGate Profile</a> | 
                <a href="https://www.tu.berlin/en/planen-bauen-umwelt/" target="_blank">TU Berlin Faculty VI</a></p>
                <p><em>Advancing building-integrated photovoltaics through scientific analysis and AI-powered optimization</em></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def render_step_by_step_reporting():
    """Render the step-by-step reporting interface"""
    st.header("📊 Step-by-Step Analysis Report")
    
    st.info("""
    **Generate Comprehensive HTML Report**
    
    This report includes detailed analysis results from each workflow step:
    - Project setup and location configuration
    - Historical data analysis and AI model performance
    - Weather environment and solar resource assessment
    - Building facade extraction and element analysis
    - Solar radiation analysis with shading calculations
    - BIPV system specifications and technology parameters
    - Energy yield vs demand balance analysis
    - Multi-objective optimization results
    - Financial analysis and environmental impact assessment
    """)
    
    # Check for consolidated data availability
    consolidated_manager = ConsolidatedDataManager()
    consolidated_data = consolidated_manager.get_consolidated_data()
    
    # Display data availability status
    with st.expander("📋 Data Availability Status", expanded=False):
        st.write("**Available Analysis Steps:**")
        
        steps = [
            ("Step 1: Project Setup", "step1_project_setup"),
            ("Step 2: Historical Data", "step2_historical_data"),
            ("Step 3: Weather Environment", "step3_weather_environment"),
            ("Step 4: Facade Extraction", "step4_facade_extraction"),
            ("Step 5: Radiation Analysis", "step5_radiation_analysis"),
            ("Step 6: PV Specification", "step6_pv_specification"),
            ("Step 7: Yield vs Demand", "step7_yield_demand"),
            ("Step 8: Optimization", "step8_optimization"),
            ("Step 9: Financial Analysis", "step9_financial_analysis")
        ]
        
        for step_name, step_key in steps:
            step_data = consolidated_data.get(step_key, {})
            status = "✅ Complete" if step_data else "⏳ Pending"
            st.write(f"- {step_name}: {status}")
    
    # Generate report button
    if st.button("📄 Generate Step-by-Step HTML Report", type="primary", key="generate_step_report"):
        with st.spinner("Generating comprehensive analysis report..."):
            try:
                # Generate HTML report
                html_content = generate_comprehensive_html_report()
                
                # Create filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"BIPV_Step_by_Step_Report_{timestamp}.html"
                
                # Offer download
                st.download_button(
                    label="📥 Download Step-by-Step Report (HTML)",
                    data=html_content,
                    file_name=filename,
                    mime="text/html",
                    key="download_step_report"
                )
                
                st.success("✅ Step-by-step analysis report generated successfully!")
                
                # Show preview option
                with st.expander("👀 Report Preview", expanded=False):
                    st.info("Report generated successfully. Download the HTML file to view the complete formatted report.")
                    st.text_area("HTML Content Preview (first 1000 characters):", 
                               value=html_content[:1000] + "...", 
                               height=200, 
                               disabled=True)
                
            except Exception as e:
                st.error(f"Error generating report: {str(e)}")
                st.info("Please ensure you have completed the necessary workflow steps before generating the report.")