"""
Individual Step Report Generators for BIPV Optimizer
Creates detailed HTML reports for each workflow step
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

def get_base_html_template(step_title, step_number):
    """Get base HTML template for individual step reports"""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BIPV Optimizer - {step_title}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #f8f9fa;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 1000px;
                margin: 0 auto;
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 0 20px rgba(0,0,0,0.1);
                padding: 30px;
            }}
            .header {{
                text-align: center;
                border-bottom: 3px solid #2E8B57;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            .header h1 {{
                color: #2E8B57;
                font-size: 2.2em;
                margin: 0;
            }}
            .step-badge {{
                background: linear-gradient(135deg, #2E8B57, #3CB371);
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-weight: bold;
                display: inline-block;
                margin-bottom: 10px;
            }}
            .content-section {{
                margin-bottom: 30px;
                padding: 20px;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: #fafafa;
            }}
            .content-section h2 {{
                color: #2E8B57;
                border-bottom: 2px solid #2E8B57;
                padding-bottom: 8px;
                margin-top: 0;
            }}
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }}
            .metric-card {{
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 15px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .metric-value {{
                font-size: 1.8em;
                font-weight: bold;
                color: #2E8B57;
                margin-bottom: 5px;
            }}
            .metric-label {{
                color: #666;
                font-size: 0.9em;
            }}
            .data-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
            }}
            .data-table th, .data-table td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            .data-table th {{
                background-color: #2E8B57;
                color: white;
            }}
            .chart-container {{
                margin: 20px 0;
                text-align: center;
            }}
            .footer {{
                text-align: center;
                border-top: 2px solid #2E8B57;
                padding-top: 15px;
                margin-top: 30px;
                color: #666;
                font-size: 0.9em;
            }}
            .footer a {{
                color: #2E8B57;
                text-decoration: none;
            }}
            .status-indicator {{
                padding: 5px 10px;
                border-radius: 15px;
                font-size: 0.8em;
                font-weight: bold;
            }}
            .status-complete {{
                background-color: #d4edda;
                color: #155724;
            }}
            .status-pending {{
                background-color: #fff3cd;
                color: #856404;
            }}
            @media (max-width: 768px) {{
                .metrics-grid {{
                    grid-template-columns: 1fr;
                }}
                .container {{
                    padding: 15px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="step-badge">Step {step_number}</div>
                <h1>{step_title}</h1>
                <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            </div>
    """

def get_footer_html():
    """Get footer HTML for reports"""
    return """
            <div class="footer">
                <p><strong>BIPV Optimizer Platform</strong></p>
                <p>Developed by <strong>Mostafa Gabr</strong>, PhD Candidate<br>
                Technische Universität Berlin, Faculty VI - Planning Building Environment</p>
                <p><a href="https://www.researchgate.net/profile/Mostafa-Gabr-4" target="_blank">ResearchGate Profile</a> | 
                <a href="https://www.tu.berlin/en/planen-bauen-umwelt/" target="_blank">TU Berlin Faculty VI</a></p>
            </div>
        </div>
    </body>
    </html>
    """

def generate_step1_report():
    """Generate Step 1: Project Setup Report"""
    project_data = st.session_state.get('project_data', {})
    
    html = get_base_html_template("Project Setup & Location Configuration", 1)
    
    location = safe_get(project_data, 'location', 'Unknown Location')
    coordinates = safe_get(project_data, 'coordinates', {})
    weather_station = safe_get(project_data, 'selected_weather_station', {})
    
    html += f"""
            <div class="content-section">
                <h2>🗺️ Project Configuration</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">{safe_get(project_data, 'project_name', 'BIPV Project')}</div>
                        <div class="metric-label">Project Name</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{location}</div>
                        <div class="metric-label">Location</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{safe_float(coordinates.get('lat'), 0):.4f}°, {safe_float(coordinates.get('lon'), 0):.4f}°</div>
                        <div class="metric-label">Coordinates</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">EUR</div>
                        <div class="metric-label">Base Currency</div>
                    </div>
                </div>
            </div>
            
            <div class="content-section">
                <h2>🌦️ Weather Station Integration</h2>
                <table class="data-table">
                    <tr><th>Parameter</th><th>Value</th></tr>
                    <tr><td>Station Name</td><td>{safe_get(weather_station, 'name', 'Not selected')}</td></tr>
                    <tr><td>WMO ID</td><td>{safe_get(weather_station, 'wmo_id', 'N/A')}</td></tr>
                    <tr><td>Distance from Project</td><td>{safe_float(safe_get(weather_station, 'distance'), 0):.1f} km</td></tr>
                    <tr><td>Country</td><td>{safe_get(weather_station, 'country', 'N/A')}</td></tr>
                    <tr><td>Timezone</td><td>{safe_get(project_data, 'timezone', 'UTC')}</td></tr>
                </table>
            </div>
    """
    
    html += get_footer_html()
    return html

def generate_step2_report():
    """Generate Step 2: Historical Data Analysis Report"""
    project_data = st.session_state.get('project_data', {})
    historical_data = safe_get(project_data, 'historical_data', {})
    
    html = get_base_html_template("Historical Data Analysis & AI Model Training", 2)
    
    if not historical_data:
        html += """
            <div class="content-section">
                <h2>⚠️ No Analysis Data Available</h2>
                <p>Historical data analysis has not been completed for this project.</p>
            </div>
        """
    else:
        model_performance = safe_get(historical_data, 'model_performance', {})
        r2_score = safe_float(safe_get(model_performance, 'r2_score'), 0.0)
        demand_forecast = safe_get(historical_data, 'demand_forecast', {})
        
        html += f"""
            <div class="content-section">
                <h2>🤖 AI Model Performance</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">{r2_score:.3f}</div>
                        <div class="metric-label">R² Score</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{'Excellent' if r2_score >= 0.85 else 'Good' if r2_score >= 0.70 else 'Needs Improvement'}</div>
                        <div class="metric-label">Performance Status</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">Random Forest</div>
                        <div class="metric-label">Algorithm</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">25 Years</div>
                        <div class="metric-label">Forecast Period</div>
                    </div>
                </div>
            </div>
            
            <div class="content-section">
                <h2>📊 Demand Forecast Results</h2>
                <table class="data-table">
                    <tr><th>Metric</th><th>Value</th></tr>
                    <tr><td>Annual Growth Rate</td><td>{safe_float(safe_get(demand_forecast, 'growth_rate'), 0.0):.2f}%</td></tr>
                    <tr><td>Baseline Annual Consumption</td><td>{safe_float(safe_get(demand_forecast, 'baseline_annual'), 0.0):,.0f} kWh</td></tr>
                    <tr><td>Building Floor Area</td><td>{safe_float(safe_get(historical_data, 'building_area'), 0.0):,.0f} m²</td></tr>
                    <tr><td>Energy Intensity</td><td>{safe_float(safe_get(historical_data, 'energy_intensity'), 0.0):.1f} kWh/m²/year</td></tr>
                </table>
            </div>
        """
    
    html += get_footer_html()
    return html

def generate_step3_report():
    """Generate Step 3: Weather Environment Report"""
    project_data = st.session_state.get('project_data', {})
    weather_analysis = safe_get(project_data, 'weather_analysis', {})
    
    html = get_base_html_template("Weather Environment & TMY Generation", 3)
    
    if not weather_analysis:
        html += """
            <div class="content-section">
                <h2>⚠️ No Weather Analysis Available</h2>
                <p>Weather environment analysis has not been completed for this project.</p>
            </div>
        """
    else:
        tmy_data = safe_get(weather_analysis, 'tmy_data', {})
        solar_resource = safe_get(weather_analysis, 'solar_resource_assessment', {})
        
        annual_ghi = safe_float(safe_get(solar_resource, 'annual_ghi'), 0.0)
        peak_sun_hours = safe_float(safe_get(solar_resource, 'peak_sun_hours'), 0.0)
        
        html += f"""
            <div class="content-section">
                <h2>☀️ Solar Resource Assessment</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">{annual_ghi:,.0f} kWh/m²</div>
                        <div class="metric-label">Annual GHI</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{peak_sun_hours:.1f} hours</div>
                        <div class="metric-label">Peak Sun Hours/Day</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{safe_get(solar_resource, 'resource_class', 'Unknown')}</div>
                        <div class="metric-label">Solar Resource Class</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{safe_get(solar_resource, 'climate_zone', 'Unknown')}</div>
                        <div class="metric-label">Climate Zone</div>
                    </div>
                </div>
            </div>
            
            <div class="content-section">
                <h2>🌦️ TMY Data Quality</h2>
                <table class="data-table">
                    <tr><th>Parameter</th><th>Value</th></tr>
                    <tr><td>Data Points</td><td>8,760 hourly records</td></tr>
                    <tr><td>Standards Compliance</td><td>ISO 15927-4</td></tr>
                    <tr><td>Data Source</td><td>WMO weather station</td></tr>
                    <tr><td>Quality Score</td><td>{safe_get(tmy_data, 'quality_score', 'High')}</td></tr>
                    <tr><td>Generation Method</td><td>Authentic meteorological data</td></tr>
                </table>
            </div>
        """
    
    html += get_footer_html()
    return html

def generate_step5_report():
    """Generate Step 5: Radiation Analysis Report"""
    consolidated_manager = ConsolidatedDataManager()
    step5_data = consolidated_manager.get_step_data(5)
    
    html = get_base_html_template("Solar Radiation & Shading Analysis", 5)
    
    radiation_results = safe_get(step5_data, 'radiation_results', {})
    analysis_summary = safe_get(step5_data, 'analysis_summary', {})
    
    if not radiation_results:
        html += """
            <div class="content-section">
                <h2>⚠️ No Radiation Analysis Available</h2>
                <p>Solar radiation and shading analysis has not been completed for this project.</p>
            </div>
        """
    else:
        total_elements = safe_get(analysis_summary, 'total_elements', 0)
        avg_radiation = safe_float(safe_get(analysis_summary, 'average_radiation'), 0.0)
        max_radiation = safe_float(safe_get(analysis_summary, 'max_radiation'), 0.0)
        
        html += f"""
            <div class="content-section">
                <h2>☀️ Solar Radiation Results</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">{total_elements:,}</div>
                        <div class="metric-label">Elements Analyzed</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{avg_radiation:,.0f} kWh/m²</div>
                        <div class="metric-label">Average Annual Radiation</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{max_radiation:,.0f} kWh/m²</div>
                        <div class="metric-label">Highest Performing Element</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">pvlib</div>
                        <div class="metric-label">Calculation Method</div>
                    </div>
                </div>
            </div>
            
            <div class="content-section">
                <h2>🏢 Shading Analysis</h2>
                <table class="data-table">
                    <tr><th>Analysis Component</th><th>Details</th></tr>
                    <tr><td>Self-Shading</td><td>Building geometry considered</td></tr>
                    <tr><td>Environmental Factors</td><td>Vegetation and urban shading</td></tr>
                    <tr><td>Time Resolution</td><td>Hourly calculations</td></tr>
                    <tr><td>Precision Level</td><td>{safe_get(step5_data, 'precision_level', 'Standard')}</td></tr>
                    <tr><td>Solar Position Model</td><td>Astronomical algorithms</td></tr>
                </table>
            </div>
        """
    
    html += get_footer_html()
    return html

def generate_step4_report():
    """Generate Step 4: Facade Extraction Report"""
    consolidated_manager = ConsolidatedDataManager()
    step4_data = consolidated_manager.get_step_data(4)
    
    html = get_base_html_template("Facade & Window Extraction from BIM", 4)
    
    building_elements = safe_get(step4_data, 'building_elements', [])
    
    if not building_elements:
        html += """
            <div class="content-section">
                <h2>⚠️ No Building Elements Available</h2>
                <p>BIM facade extraction has not been completed for this project.</p>
            </div>
        """
    else:
        total_elements = len(building_elements)
        total_area = sum(safe_float(elem.get('glass_area', 0)) for elem in building_elements)
        
        # Count by orientation
        orientations = {}
        for elem in building_elements:
            orientation = elem.get('orientation', 'Unknown')
            orientations[orientation] = orientations.get(orientation, 0) + 1
        
        html += f"""
            <div class="content-section">
                <h2>🏢 Building Elements Summary</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">{total_elements:,}</div>
                        <div class="metric-label">Total Elements</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{total_area:,.1f} m²</div>
                        <div class="metric-label">Total Glass Area</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{len(orientations)}</div>
                        <div class="metric-label">Orientations</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">BIM CSV</div>
                        <div class="metric-label">Data Source</div>
                    </div>
                </div>
            </div>
            
            <div class="content-section">
                <h2>📊 Orientation Distribution</h2>
                <table class="data-table">
                    <tr><th>Orientation</th><th>Element Count</th><th>Percentage</th></tr>
        """
        
        for orientation, count in orientations.items():
            percentage = (count / total_elements) * 100
            html += f"<tr><td>{orientation}</td><td>{count:,}</td><td>{percentage:.1f}%</td></tr>"
        
        html += """
                </table>
            </div>
            
            <div class="content-section">
                <h2>📋 Sample Elements (First 10)</h2>
                <table class="data-table">
                    <tr><th>Element ID</th><th>Orientation</th><th>Glass Area (m²)</th><th>Level</th></tr>
        """
        
        for elem in building_elements[:10]:
            html += f"""
                <tr>
                    <td>{elem.get('element_id', 'Unknown')}</td>
                    <td>{elem.get('orientation', 'Unknown')}</td>
                    <td>{safe_float(elem.get('glass_area', 0)):.2f}</td>
                    <td>{elem.get('building_level', elem.get('level', 'Unknown'))}</td>
                </tr>
            """
        
        html += "</table></div>"
    
    html += get_footer_html()
    return html

def generate_step6_report():
    """Generate Step 6: PV Specification Report"""
    consolidated_manager = ConsolidatedDataManager()
    step6_data = consolidated_manager.get_step_data(6)
    
    html = get_base_html_template("BIPV Glass Specification & System Design", 6)
    
    individual_systems = safe_get(step6_data, 'individual_systems', [])
    system_summary = safe_get(step6_data, 'system_summary', {})
    
    if not individual_systems:
        html += """
            <div class="content-section">
                <h2>⚠️ No PV Systems Available</h2>
                <p>BIPV system specification has not been completed for this project.</p>
            </div>
        """
    else:
        total_capacity = safe_float(safe_get(system_summary, 'total_capacity_kw'), 0.0)
        total_cost = safe_float(safe_get(system_summary, 'total_cost_eur'), 0.0)
        
        html += f"""
            <div class="content-section">
                <h2>⚡ BIPV System Overview</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">{len(individual_systems):,}</div>
                        <div class="metric-label">Total Systems</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{total_capacity:,.1f} kW</div>
                        <div class="metric-label">Total Capacity</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">€{total_cost:,.0f}</div>
                        <div class="metric-label">Total Investment</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{total_cost/total_capacity if total_capacity > 0 else 0:,.0f} €/kW</div>
                        <div class="metric-label">Cost per kW</div>
                    </div>
                </div>
            </div>
            
            <div class="content-section">
                <h2>🔬 BIPV Glass Technology</h2>
                <table class="data-table">
                    <tr><th>Parameter</th><th>Specification</th></tr>
                    <tr><td>Technology Type</td><td>Semi-transparent BIPV Glass</td></tr>
                    <tr><td>Efficiency Range</td><td>8-15% (typical BIPV)</td></tr>
                    <tr><td>Transparency</td><td>15-40%</td></tr>
                    <tr><td>Glass Thickness</td><td>6-12mm</td></tr>
                    <tr><td>Integration Method</td><td>Window Glass Replacement</td></tr>
                </table>
            </div>
        """
    
    html += get_footer_html()
    return html

def generate_step7_report():
    """Generate Step 7: Yield vs Demand Report"""
    consolidated_manager = ConsolidatedDataManager()
    step7_data = consolidated_manager.get_step_data(7)
    
    html = get_base_html_template("Energy Yield vs Demand Analysis", 7)
    
    annual_metrics = safe_get(step7_data, 'annual_metrics', {})
    energy_balance = safe_get(step7_data, 'energy_balance', [])
    
    if not annual_metrics:
        html += """
            <div class="content-section">
                <h2>⚠️ No Yield Analysis Available</h2>
                <p>Energy yield vs demand analysis has not been completed for this project.</p>
            </div>
        """
    else:
        total_yield = safe_float(safe_get(annual_metrics, 'total_annual_yield'), 0.0)
        annual_demand = safe_float(safe_get(annual_metrics, 'annual_demand'), 0.0)
        coverage_ratio = safe_float(safe_get(annual_metrics, 'coverage_ratio'), 0.0)
        annual_savings = safe_float(safe_get(annual_metrics, 'total_annual_savings'), 0.0)
        
        html += f"""
            <div class="content-section">
                <h2>⚡ Energy Balance Summary</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">{total_yield:,.0f} kWh</div>
                        <div class="metric-label">Annual PV Yield</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{annual_demand:,.0f} kWh</div>
                        <div class="metric-label">Annual Demand</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{coverage_ratio:.1f}%</div>
                        <div class="metric-label">Coverage Ratio</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">€{annual_savings:,.0f}</div>
                        <div class="metric-label">Annual Savings</div>
                    </div>
                </div>
            </div>
            
            <div class="content-section">
                <h2>💰 Economic Performance</h2>
                <table class="data-table">
                    <tr><th>Metric</th><th>Value</th></tr>
                    <tr><td>Annual Savings</td><td>€{annual_savings:,.0f}</td></tr>
                    <tr><td>Feed-in Revenue</td><td>€{safe_float(safe_get(annual_metrics, 'total_feed_in_revenue'), 0.0):,.0f}</td></tr>
                    <tr><td>Self-Consumption Priority</td><td>Yes</td></tr>
                    <tr><td>Grid Export</td><td>Surplus energy sold</td></tr>
                    <tr><td>Monthly Analysis</td><td>{len(energy_balance)} months</td></tr>
                </table>
            </div>
        """
    
    html += get_footer_html()
    return html

def generate_step8_report():
    """Generate Step 8: Optimization Report"""
    consolidated_manager = ConsolidatedDataManager()
    step8_data = consolidated_manager.get_step_data(8)
    
    html = get_base_html_template("Multi-Objective BIPV Optimization", 8)
    
    solutions = safe_get(step8_data, 'solutions', [])
    optimization_results = safe_get(step8_data, 'optimization_results', {})
    
    if not solutions:
        html += """
            <div class="content-section">
                <h2>⚠️ No Optimization Results Available</h2>
                <p>Multi-objective optimization has not been completed for this project.</p>
            </div>
        """
    else:
        html += f"""
            <div class="content-section">
                <h2>🎯 Optimization Results</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">{len(solutions):,}</div>
                        <div class="metric-label">Solutions Found</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">NSGA-II</div>
                        <div class="metric-label">Algorithm Used</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">3 Objectives</div>
                        <div class="metric-label">Optimization Goals</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">Pareto-Optimal</div>
                        <div class="metric-label">Solution Type</div>
                    </div>
                </div>
            </div>
            
            <div class="content-section">
                <h2>📊 Best Solutions (Top 5)</h2>
                <table class="data-table">
                    <tr><th>Rank</th><th>Investment (€)</th><th>Annual Energy (kWh)</th><th>ROI (%)</th><th>Fitness Score</th></tr>
        """
        
        for i, solution in enumerate(solutions[:5]):
            html += f"""
                <tr>
                    <td>{i+1}</td>
                    <td>€{safe_float(solution.get('total_investment', 0)):,.0f}</td>
                    <td>{safe_float(solution.get('annual_energy_kwh', 0)):,.0f}</td>
                    <td>{safe_float(solution.get('roi', 0)):.1f}%</td>
                    <td>{safe_float(solution.get('weighted_fitness', 0)):.3f}</td>
                </tr>
            """
        
        html += "</table></div>"
    
    html += get_footer_html()
    return html

def generate_step9_report():
    """Generate Step 9: Financial Analysis Report"""
    consolidated_manager = ConsolidatedDataManager()
    step9_data = consolidated_manager.get_step_data(9)
    
    html = get_base_html_template("Financial & Environmental Analysis", 9)
    
    economic_metrics = safe_get(step9_data, 'economic_metrics', {})
    environmental_impact = safe_get(step9_data, 'environmental_impact', {})
    
    if not economic_metrics:
        html += """
            <div class="content-section">
                <h2>⚠️ No Financial Analysis Available</h2>
                <p>Financial and environmental analysis has not been completed for this project.</p>
            </div>
        """
    else:
        npv = safe_float(safe_get(economic_metrics, 'npv'), 0.0)
        irr = safe_float(safe_get(economic_metrics, 'irr'), 0.0)
        payback = safe_float(safe_get(economic_metrics, 'payback_period'), 0.0)
        co2_savings = safe_float(safe_get(environmental_impact, 'lifetime_co2_savings'), 0.0)
        
        html += f"""
            <div class="content-section">
                <h2>💰 Financial Performance</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">€{npv:,.0f}</div>
                        <div class="metric-label">Net Present Value</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{irr:.1f}%</div>
                        <div class="metric-label">Internal Rate of Return</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{payback:.1f} years</div>
                        <div class="metric-label">Payback Period</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{'Excellent' if npv > 50000 else 'Good' if npv > 0 else 'Marginal'}</div>
                        <div class="metric-label">Investment Viability</div>
                    </div>
                </div>
            </div>
            
            <div class="content-section">
                <h2>🌱 Environmental Impact</h2>
                <table class="data-table">
                    <tr><th>Environmental Metric</th><th>Value</th></tr>
                    <tr><td>Lifetime CO₂ Savings</td><td>{co2_savings:,.0f} kg</td></tr>
                    <tr><td>Annual CO₂ Reduction</td><td>{safe_float(safe_get(environmental_impact, 'annual_co2_savings'), 0.0):,.0f} kg</td></tr>
                    <tr><td>Carbon Monetary Value</td><td>€{safe_float(safe_get(environmental_impact, 'carbon_value'), 0.0):,.0f}</td></tr>
                    <tr><td>Grid CO₂ Factor</td><td>{safe_float(safe_get(environmental_impact, 'grid_co2_factor'), 0.0):.3f} kg/kWh</td></tr>
                </table>
            </div>
        """
    
    html += get_footer_html()
    return html

def generate_individual_step_report(step_number):
    """Generate individual step report based on step number"""
    report_generators = {
        1: generate_step1_report,
        2: generate_step2_report,
        3: generate_step3_report,
        4: generate_step4_report,
        5: generate_step5_report,
        6: generate_step6_report,
        7: generate_step7_report,
        8: generate_step8_report,
        9: generate_step9_report,
    }
    
    if step_number in report_generators:
        return report_generators[step_number]()
    else:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Step {step_number} Report</title></head>
        <body>
            <h1>Step {step_number} Report</h1>
            <p>Report generation for this step is not yet implemented.</p>
        </body>
        </html>
        """

def create_step_download_button(step_number, step_name, button_text="Download Step Report"):
    """Create download button for individual step report"""
    try:
        html_content = generate_individual_step_report(step_number)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"BIPV_Step_{step_number}_{step_name.replace(' ', '_')}_{timestamp}.html"
        
        return st.download_button(
            label=f"📄 {button_text}",
            data=html_content.encode('utf-8'),
            file_name=filename,
            mime="text/html",
            key=f"download_step_{step_number}_report",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Error generating Step {step_number} report: {str(e)}")
        return False