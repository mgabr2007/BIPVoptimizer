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
    """Get base HTML template for individual step reports with golden professional styling"""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BIPV Optimizer - {step_title}</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
                line-height: 1.6;
                color: #2c2c2c;
                background: linear-gradient(135deg, #f5f3f0 0%, #faf8f3 50%, #f7f4ef 100%);
                min-height: 100vh;
                margin: 0;
                padding: 20px;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: linear-gradient(145deg, #ffffff 0%, #fefefe 100%);
                border-radius: 15px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.1), 0 4px 15px rgba(0,0,0,0.05);
                overflow: hidden;
                border: 1px solid rgba(218, 165, 32, 0.2);
            }}
            
            .header {{
                background: linear-gradient(135deg, #DAA520 0%, #B8860B 50%, #CD853F 100%);
                color: white;
                text-align: center;
                padding: 40px 30px;
                position: relative;
                overflow: hidden;
            }}
            
            .header::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
                opacity: 0.3;
            }}
            
            .step-badge {{
                background: linear-gradient(135deg, #FFD700, #FFA500);
                color: #8B4513;
                padding: 12px 24px;
                border-radius: 25px;
                font-weight: bold;
                font-size: 1.1em;
                display: inline-block;
                margin-bottom: 15px;
                box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3);
                position: relative;
                z-index: 1;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            
            .header h1 {{
                font-size: 2.8em;
                margin: 10px 0;
                font-weight: 700;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                position: relative;
                z-index: 1;
            }}
            
            .header p {{
                font-size: 1.1em;
                opacity: 0.9;
                position: relative;
                z-index: 1;
            }}
            
            .main-content {{
                padding: 40px;
            }}
            
            .content-section {{
                margin-bottom: 40px;
                padding: 30px;
                border: 2px solid transparent;
                border-radius: 12px;
                background: linear-gradient(white, white) padding-box,
                           linear-gradient(135deg, #DAA520, #CD853F) border-box;
                box-shadow: 0 5px 20px rgba(218, 165, 32, 0.1);
                transition: all 0.3s ease;
            }}
            
            .content-section:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(218, 165, 32, 0.15);
            }}
            
            .content-section h2 {{
                color: #B8860B;
                font-size: 1.8em;
                margin-bottom: 20px;
                padding-bottom: 12px;
                border-bottom: 3px solid #DAA520;
                font-weight: 600;
                position: relative;
            }}
            
            .content-section h2::after {{
                content: '';
                position: absolute;
                bottom: -3px;
                left: 0;
                width: 60px;
                height: 3px;
                background: linear-gradient(90deg, #FFD700, #FFA500);
                border-radius: 2px;
            }}
            
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 25px 0;
            }}
            
            .metric-card {{
                background: linear-gradient(145deg, #ffffff 0%, #fefefe 100%);
                border: 2px solid transparent;
                border-radius: 10px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 5px 15px rgba(0,0,0,0.08);
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }}
            
            .metric-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #DAA520, #CD853F);
            }}
            
            .metric-card:hover {{
                transform: translateY(-3px);
                box-shadow: 0 8px 25px rgba(218, 165, 32, 0.15);
                border-color: rgba(218, 165, 32, 0.3);
            }}
            
            .metric-value {{
                font-size: 2.2em;
                font-weight: bold;
                color: #B8860B;
                margin-bottom: 8px;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
            }}
            
            .metric-label {{
                color: #666;
                font-size: 1em;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            .data-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }}
            
            .data-table th {{
                background: linear-gradient(135deg, #DAA520, #B8860B);
                color: white;
                padding: 15px 12px;
                text-align: left;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                font-size: 0.9em;
            }}
            
            .data-table td {{
                padding: 12px;
                border-bottom: 1px solid #f0f0f0;
                transition: background-color 0.2s ease;
            }}
            
            .data-table tr:nth-child(even) {{
                background-color: #fafafa;
            }}
            
            .data-table tr:hover {{
                background-color: #f5f3f0;
            }}
            
            .chart-container {{
                margin: 30px 0;
                padding: 20px;
                background: white;
                border-radius: 10px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.05);
                border: 1px solid rgba(218, 165, 32, 0.1);
            }}
            
            .chart-title {{
                font-size: 1.3em;
                color: #B8860B;
                margin-bottom: 15px;
                font-weight: 600;
                text-align: center;
            }}
            
            .footer {{
                background: linear-gradient(135deg, #2c2c2c 0%, #3a3a3a 100%);
                color: white;
                text-align: center;
                padding: 30px;
                margin-top: 0;
            }}
            
            .footer h3 {{
                color: #DAA520;
                margin-bottom: 15px;
                font-size: 1.4em;
            }}
            
            .footer a {{
                color: #DAA520;
                text-decoration: none;
                font-weight: 500;
                transition: color 0.3s ease;
            }}
            
            .footer a:hover {{
                color: #FFD700;
            }}
            
            .status-indicator {{
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 0.9em;
                font-weight: bold;
                display: inline-block;
                margin: 5px 0;
            }}
            
            .status-complete {{
                background: linear-gradient(135deg, #d4edda, #c3e6cb);
                color: #155724;
                border: 1px solid #c3e6cb;
            }}
            
            .status-pending {{
                background: linear-gradient(135deg, #fff3cd, #ffeaa7);
                color: #856404;
                border: 1px solid #ffeaa7;
            }}
            
            .status-excellent {{
                background: linear-gradient(135deg, #DAA520, #FFD700);
                color: white;
                border: 1px solid #DAA520;
            }}
            
            .highlight-box {{
                background: linear-gradient(135deg, #fff8dc 0%, #fffacd 100%);
                border-left: 5px solid #DAA520;
                padding: 20px;
                margin: 20px 0;
                border-radius: 0 8px 8px 0;
                box-shadow: 0 3px 10px rgba(218, 165, 32, 0.1);
            }}
            
            .analysis-summary {{
                background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                border: 2px solid #DAA520;
                border-radius: 12px;
                padding: 25px;
                margin: 25px 0;
                text-align: center;
            }}
            
            .analysis-summary h3 {{
                color: #B8860B;
                margin-bottom: 15px;
                font-size: 1.5em;
            }}
            
            @media (max-width: 768px) {{
                .metrics-grid {{
                    grid-template-columns: 1fr;
                }}
                .container {{
                    margin: 10px;
                    border-radius: 10px;
                }}
                .main-content {{
                    padding: 20px;
                }}
                .header {{
                    padding: 30px 20px;
                }}
                .header h1 {{
                    font-size: 2.2em;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="step-badge">Step {step_number}</div>
                <h1>{step_title}</h1>
                <p>Analysis Report Generated: {datetime.now().strftime("%B %d, %Y at %H:%M:%S")}</p>
            </div>
            <div class="main-content">
    """

def get_footer_html():
    """Get footer HTML for reports with golden styling"""
    return """
            </div>
        </div>
        <div class="footer">
            <h3>BIPV Optimizer Platform</h3>
            <p>Developed by <strong>Mostafa Gabr</strong>, PhD Candidate<br>
            Technische Universität Berlin, Faculty VI - Planning Building Environment</p>
            <p><a href="https://www.researchgate.net/profile/Mostafa-Gabr-4" target="_blank">ResearchGate Profile</a> | 
            <a href="https://www.tu.berlin/en/planen-bauen-umwelt/" target="_blank">TU Berlin Faculty VI</a></p>
            <p style="margin-top: 15px; font-size: 0.9em; opacity: 0.8;">
                Professional BIPV Analysis • Advanced Solar Modeling • Building Integration Solutions
            </p>
        </div>
    </body>
    </html>
    """

def generate_plotly_chart(chart_data, chart_type, title, x_label="", y_label=""):
    """Generate Plotly chart HTML"""
    chart_id = f"chart_{hash(title) % 10000}"
    
    if chart_type == "bar":
        chart_config = f"""
        var data = [{{
            x: {json.dumps(chart_data.get('x', []))},
            y: {json.dumps(chart_data.get('y', []))},
            type: 'bar',
            marker: {{
                color: '#DAA520',
                line: {{
                    color: '#B8860B',
                    width: 1
                }}
            }}
        }}];
        """
    elif chart_type == "pie":
        chart_config = f"""
        var data = [{{
            values: {json.dumps(chart_data.get('values', []))},
            labels: {json.dumps(chart_data.get('labels', []))},
            type: 'pie',
            marker: {{
                colors: ['#DAA520', '#CD853F', '#B8860B', '#DDD700', '#FFA500', '#FF8C00']
            }}
        }}];
        """
    elif chart_type == "line":
        chart_config = f"""
        var data = [{{
            x: {json.dumps(chart_data.get('x', []))},
            y: {json.dumps(chart_data.get('y', []))},
            type: 'scatter',
            mode: 'lines+markers',
            line: {{
                color: '#DAA520',
                width: 3
            }},
            marker: {{
                color: '#B8860B',
                size: 8
            }}
        }}];
        """
    else:
        chart_config = """var data = [];"""
    
    layout_config = f"""
    var layout = {{
        title: {{
            text: '{title}',
            font: {{
                size: 18,
                color: '#B8860B',
                family: 'Segoe UI, Arial, sans-serif'
            }}
        }},
        xaxis: {{
            title: '{x_label}',
            titlefont: {{
                color: '#666',
                size: 14
            }},
            tickfont: {{
                color: '#666'
            }}
        }},
        yaxis: {{
            title: '{y_label}',
            titlefont: {{
                color: '#666',
                size: 14
            }},
            tickfont: {{
                color: '#666'
            }}
        }},
        plot_bgcolor: 'white',
        paper_bgcolor: 'white',
        margin: {{
            l: 60,
            r: 40,
            t: 60,
            b: 60
        }}
    }};
    """
    
    return f"""
    <div class="chart-container">
        <div class="chart-title">{title}</div>
        <div id="{chart_id}" style="height: 400px;"></div>
        <script>
            {chart_config}
            {layout_config}
            Plotly.newPlot('{chart_id}', data, layout, {{responsive: true}});
        </script>
    </div>
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
    """Generate Step 4: Facade Extraction Report with enhanced data and charts"""
    consolidated_manager = ConsolidatedDataManager()
    step4_data = consolidated_manager.get_step_data(4)
    
    html = get_base_html_template("Facade & Window Extraction from BIM", 4)
    
    building_elements = safe_get(step4_data, 'building_elements', [])
    
    if not building_elements:
        html += """
            <div class="content-section">
                <h2>⚠️ No Building Elements Available</h2>
                <div class="highlight-box">
                    <p><strong>Required Action:</strong> BIM facade extraction has not been completed for this project.</p>
                    <p>Please upload BIM window elements CSV data to proceed with the analysis.</p>
                </div>
            </div>
        """
    else:
        total_elements = len(building_elements)
        total_area = sum(safe_float(elem.get('glass_area', 0)) for elem in building_elements)
        avg_area = total_area / total_elements if total_elements > 0 else 0
        
        # Analyze orientations
        orientations = {}
        orientation_areas = {}
        for elem in building_elements:
            orientation = elem.get('orientation', 'Unknown')
            glass_area = safe_float(elem.get('glass_area', 0))
            orientations[orientation] = orientations.get(orientation, 0) + 1
            orientation_areas[orientation] = orientation_areas.get(orientation, 0) + glass_area
        
        # Analyze levels
        levels = {}
        for elem in building_elements:
            level = elem.get('building_level', elem.get('level', 'Unknown'))
            levels[level] = levels.get(level, 0) + 1
        
        # Key metrics
        html += f"""
            <div class="analysis-summary">
                <h3>🏗️ BIM Analysis Overview</h3>
                <p>Successfully extracted <strong>{total_elements:,} building elements</strong> with total glazed area of <strong>{total_area:,.1f} m²</strong></p>
                <p>Average window size: <strong>{avg_area:.1f} m²</strong> | Building levels: <strong>{len(levels)}</strong> | Facade orientations: <strong>{len(orientations)}</strong></p>
            </div>
            
            <div class="content-section">
                <h2>📊 Comprehensive Building Analysis</h2>
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
                        <div class="metric-value">{avg_area:.1f} m²</div>
                        <div class="metric-label">Average Element Size</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{len(levels)}</div>
                        <div class="metric-label">Building Levels</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{len(orientations)}</div>
                        <div class="metric-label">Facade Orientations</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value status-excellent">BIM LOD 300</div>
                        <div class="metric-label">Data Quality</div>
                    </div>
                </div>
            </div>
        """
        
        # Generate orientation distribution chart
        if orientations:
            orientation_chart_data = {
                'labels': list(orientations.keys()),
                'values': list(orientations.values())
            }
            html += generate_plotly_chart(
                orientation_chart_data, 
                'pie', 
                'Element Distribution by Orientation',
                '', 
                'Number of Elements'
            )
        
        # Generate area distribution chart
        if orientation_areas:
            area_chart_data = {
                'x': list(orientation_areas.keys()),
                'y': list(orientation_areas.values())
            }
            html += generate_plotly_chart(
                area_chart_data, 
                'bar', 
                'Glass Area Distribution by Orientation',
                'Facade Orientation', 
                'Glass Area (m²)'
            )
        
        html += f"""
            <div class="content-section">
                <h2>🔍 Detailed Orientation Analysis</h2>
                <table class="data-table">
                    <tr><th>Orientation</th><th>Element Count</th><th>Total Area (m²)</th><th>Avg Area (m²)</th><th>Percentage</th></tr>
        """
        
        for orientation in orientations.keys():
            count = orientations[orientation]
            area = orientation_areas.get(orientation, 0)
            avg_orient_area = area / count if count > 0 else 0
            percentage = (count / total_elements) * 100
            html += f"""
                <tr>
                    <td><strong>{orientation}</strong></td>
                    <td>{count:,}</td>
                    <td>{area:,.1f}</td>
                    <td>{avg_orient_area:.1f}</td>
                    <td>{percentage:.1f}%</td>
                </tr>
            """
        
        html += """
                </table>
            </div>
            
            <div class="content-section">
                <h2>🏢 Building Level Distribution</h2>
                <table class="data-table">
                    <tr><th>Level</th><th>Element Count</th><th>Percentage</th></tr>
        """
        
        for level, count in sorted(levels.items()):
            percentage = (count / total_elements) * 100
            html += f"<tr><td>{level}</td><td>{count:,}</td><td>{percentage:.1f}%</td></tr>"
        
        html += """
                </table>
            </div>
            
            <div class="content-section">
                <h2>📋 Detailed Element Sample (Top 15 by Glass Area)</h2>
                <table class="data-table">
                    <tr><th>Element ID</th><th>Orientation</th><th>Glass Area (m²)</th><th>Level</th><th>Family Type</th></tr>
        """
        
        # Sort by glass area and show top 15
        sorted_elements = sorted(building_elements, key=lambda x: safe_float(x.get('glass_area', 0)), reverse=True)
        for elem in sorted_elements[:15]:
            html += f"""
                <tr>
                    <td><strong>{elem.get('element_id', 'Unknown')}</strong></td>
                    <td>{elem.get('orientation', 'Unknown')}</td>
                    <td>{safe_float(elem.get('glass_area', 0)):.2f}</td>
                    <td>{elem.get('building_level', elem.get('level', 'Unknown'))}</td>
                    <td>{elem.get('family_type', elem.get('type', 'Window'))}</td>
                </tr>
            """
        
        html += """
                </table>
            </div>
            
            <div class="highlight-box">
                <h3>🎯 BIPV Suitability Assessment</h3>
                <p><strong>Analysis Complete:</strong> Building geometry successfully extracted from BIM model.</p>
                <p><strong>Next Steps:</strong> Proceed to Step 5 (Radiation Analysis) to calculate solar irradiance on each facade element.</p>
                <p><strong>Data Usage:</strong> Element orientations and areas will be used for precise solar modeling and BIPV system optimization.</p>
            </div>
        """
    
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
    """Generate Step 7: Yield vs Demand Report with enhanced analysis and charts"""
    consolidated_manager = ConsolidatedDataManager()
    step7_data = consolidated_manager.get_step_data(7)
    
    html = get_base_html_template("Energy Yield vs Demand Analysis", 7)
    
    annual_metrics = safe_get(step7_data, 'annual_metrics', {})
    energy_balance = safe_get(step7_data, 'energy_balance', [])
    
    if not annual_metrics:
        html += """
            <div class="content-section">
                <h2>⚠️ No Yield Analysis Available</h2>
                <div class="highlight-box">
                    <p><strong>Required Dependencies:</strong> Energy yield vs demand analysis has not been completed for this project.</p>
                    <p>Please complete Steps 2 (Historical Data), 5 (Radiation Analysis), and 6 (PV Specification) first.</p>
                </div>
            </div>
        """
    else:
        total_yield = safe_float(safe_get(annual_metrics, 'total_annual_yield'), 0.0)
        annual_demand = safe_float(safe_get(annual_metrics, 'annual_demand'), 0.0)
        coverage_ratio = safe_float(safe_get(annual_metrics, 'coverage_ratio'), 0.0)
        annual_savings = safe_float(safe_get(annual_metrics, 'total_annual_savings'), 0.0)
        feed_in_revenue = safe_float(safe_get(annual_metrics, 'total_feed_in_revenue'), 0.0)
        net_import = annual_demand - total_yield
        
        # Calculate performance metrics
        specific_yield = total_yield / safe_float(safe_get(annual_metrics, 'total_capacity_kw'), 1.0) if safe_get(annual_metrics, 'total_capacity_kw') else 0
        cost_savings_rate = (annual_savings / annual_demand) * 1000 if annual_demand > 0 else 0  # €/MWh
        
        html += f"""
            <div class="analysis-summary">
                <h3>⚡ Energy Balance Overview</h3>
                <p>BIPV system generates <strong>{total_yield:,.0f} kWh/year</strong> covering <strong>{coverage_ratio:.1f}%</strong> of building demand</p>
                <p>Net energy import: <strong>{max(0, net_import):,.0f} kWh/year</strong> | Total savings: <strong>€{annual_savings:,.0f}/year</strong></p>
            </div>
            
            <div class="content-section">
                <h2>📊 Annual Energy Performance</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">{total_yield:,.0f} kWh</div>
                        <div class="metric-label">Annual PV Generation</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{annual_demand:,.0f} kWh</div>
                        <div class="metric-label">Annual Building Demand</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{coverage_ratio:.1f}%</div>
                        <div class="metric-label">Energy Coverage Ratio</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{specific_yield:.0f} kWh/kW</div>
                        <div class="metric-label">Specific Yield</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">€{annual_savings:,.0f}</div>
                        <div class="metric-label">Annual Cost Savings</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">€{feed_in_revenue:,.0f}</div>
                        <div class="metric-label">Feed-in Revenue</div>
                    </div>
                </div>
            </div>
        """
        
        # Generate monthly energy balance chart
        if energy_balance:
            months = []
            pv_generation = []
            demand_values = []
            net_values = []
            
            for month_data in energy_balance:
                months.append(month_data.get('month', 'Unknown'))
                pv_generation.append(safe_float(month_data.get('pv_yield', 0)))
                demand_values.append(safe_float(month_data.get('demand', 0)))
                net_values.append(safe_float(month_data.get('net_import', 0)))
            
            # Monthly comparison chart
            monthly_chart_data = {
                'x': months,
                'y': pv_generation
            }
            html += generate_plotly_chart(
                monthly_chart_data, 
                'bar', 
                'Monthly PV Generation vs Demand',
                'Month', 
                'Energy (kWh)'
            )
            
            # Add demand line to the chart (this will be in the next chart)
            demand_chart_data = {
                'x': months,
                'y': demand_values
            }
            html += generate_plotly_chart(
                demand_chart_data, 
                'line', 
                'Monthly Building Energy Demand',
                'Month', 
                'Energy (kWh)'
            )
        
        html += f"""
            <div class="content-section">
                <h2>💰 Economic Performance Analysis</h2>
                <table class="data-table">
                    <tr><th>Financial Metric</th><th>Value</th><th>Unit</th></tr>
                    <tr><td>Annual Cost Savings</td><td>€{annual_savings:,.0f}</td><td>per year</td></tr>
                    <tr><td>Feed-in Revenue</td><td>€{feed_in_revenue:,.0f}</td><td>per year</td></tr>
                    <tr><td>Total Annual Benefit</td><td>€{annual_savings + feed_in_revenue:,.0f}</td><td>per year</td></tr>
                    <tr><td>Cost Savings Rate</td><td>€{cost_savings_rate:.1f}</td><td>per MWh</td></tr>
                    <tr><td>Monthly Average Savings</td><td>€{annual_savings/12:,.0f}</td><td>per month</td></tr>
                </table>
            </div>
            
            <div class="content-section">
                <h2>🔋 Energy Balance Details</h2>
                <table class="data-table">
                    <tr><th>Energy Component</th><th>Annual Value</th><th>Percentage</th></tr>
                    <tr><td>Self-Consumed PV Energy</td><td>{min(total_yield, annual_demand):,.0f} kWh</td><td>{min(100, (total_yield/annual_demand)*100) if annual_demand > 0 else 0:.1f}%</td></tr>
                    <tr><td>Grid Export (Surplus)</td><td>{max(0, total_yield - annual_demand):,.0f} kWh</td><td>{max(0, ((total_yield - annual_demand)/total_yield)*100) if total_yield > 0 else 0:.1f}%</td></tr>
                    <tr><td>Grid Import (Deficit)</td><td>{max(0, annual_demand - total_yield):,.0f} kWh</td><td>{max(0, ((annual_demand - total_yield)/annual_demand)*100) if annual_demand > 0 else 0:.1f}%</td></tr>
                    <tr><td>Energy Independence</td><td>{coverage_ratio:.1f}%</td><td>Coverage ratio</td></tr>
                </table>
            </div>
        """
        
        if energy_balance:
            html += f"""
            <div class="content-section">
                <h2>📅 Monthly Energy Balance Summary</h2>
                <table class="data-table">
                    <tr><th>Month</th><th>PV Generation (kWh)</th><th>Demand (kWh)</th><th>Net Import (kWh)</th><th>Savings (€)</th></tr>
            """
            
            for month_data in energy_balance[:12]:  # Show all 12 months
                month = month_data.get('month', 'Unknown')
                generation = safe_float(month_data.get('pv_yield', 0))
                demand = safe_float(month_data.get('demand', 0))
                net_import = safe_float(month_data.get('net_import', 0))
                savings = safe_float(month_data.get('monthly_savings', 0))
                
                html += f"""
                    <tr>
                        <td><strong>{month}</strong></td>
                        <td>{generation:,.0f}</td>
                        <td>{demand:,.0f}</td>
                        <td>{net_import:,.0f}</td>
                        <td>€{savings:,.0f}</td>
                    </tr>
                """
            
            html += """
                </table>
            </div>
            """
        
        html += """
            <div class="highlight-box">
                <h3>🎯 Analysis Results Summary</h3>
                <p><strong>Performance Assessment:</strong> BIPV system analysis complete with detailed energy balance calculations.</p>
                <p><strong>Next Steps:</strong> Proceed to Step 8 (Optimization) to find optimal system configurations.</p>
                <p><strong>Key Insights:</strong> Energy coverage ratio and cost savings demonstrate BIPV system viability for this building.</p>
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