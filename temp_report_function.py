def generate_enhanced_html_report(include_charts, include_recommendations):
    """Generate comprehensive HTML report with detailed equations and methodology"""
    from datetime import datetime
    
    # Get data from session state
    project_name = st.session_state.get('project_name', 'BIPV Analysis Project')
    location = st.session_state.get('selected_location', 'Unknown Location')
    coordinates = st.session_state.get('coordinates', {'lat': 0, 'lon': 0})
    currency_symbol = "€"
    
    # Get analysis data from session state
    pv_data = st.session_state.get('pv_specifications', {})
    financial_analysis = st.session_state.get('financial_results', {})
    energy_balance = st.session_state.get('energy_balance', {})
    optimization_results = st.session_state.get('optimization_results', {})
    radiation_data = st.session_state.get('radiation_data', {})
    building_elements = st.session_state.get('suitable_elements', [])
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BIPV Analysis Report - {project_name}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
                color: #333;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 0 20px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #2E8B57;
                border-bottom: 3px solid #2E8B57;
                padding-bottom: 10px;
                text-align: center;
                font-size: 2.5em;
                margin-bottom: 30px;
            }}
            h2 {{
                color: #2E8B57;
                border-left: 5px solid #2E8B57;
                padding-left: 15px;
                margin-top: 40px;
                font-size: 1.8em;
            }}
            h3 {{
                color: #228B22;
                margin-top: 25px;
                font-size: 1.3em;
            }}
            .section {{
                margin-bottom: 40px;
                padding: 20px;
                background: #fafafa;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }}
            .subsection {{
                margin: 20px 0;
                padding: 15px;
                background: white;
                border-radius: 5px;
                border-left: 3px solid #2E8B57;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                background: white;
                border-radius: 5px;
                overflow: hidden;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #2E8B57;
                color: white;
                font-weight: bold;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            .equation {{
                background: #e8f5e8;
                padding: 15px;
                border-radius: 5px;
                margin: 15px 0;
                border-left: 4px solid #2E8B57;
                font-family: 'Courier New', monospace;
            }}
            .highlight {{
                background: #fff3cd;
                padding: 10px;
                border-radius: 5px;
                border-left: 4px solid #ffc107;
                margin: 15px 0;
            }}
            .summary-card {{
                background: linear-gradient(135deg, #2E8B57, #228B22);
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
                text-align: center;
            }}
            .summary-card h3 {{
                color: white;
                margin-top: 0;
            }}
            ol, ul {{
                padding-left: 25px;
            }}
            li {{
                margin: 8px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Building Integrated Photovoltaic (BIPV) Analysis Report</h1>
            
            <div class="summary-card">
                <h3>Project Overview</h3>
                <p><strong>Project:</strong> {project_name}</p>
                <p><strong>Location:</strong> {location}</p>
                <p><strong>Coordinates:</strong> {coordinates['lat']:.4f}°N, {coordinates['lon']:.4f}°E</p>
                <p><strong>Analysis Date:</strong> {datetime.now().strftime("%B %d, %Y")}</p>
            </div>

            <div class="section">
                <h2>1. Executive Summary</h2>
                <div class="subsection">
                    <p>This comprehensive BIPV analysis evaluates the integration of photovoltaic technology into building facades and windows. 
                    The analysis considers technical feasibility, financial viability, and environmental impact of replacing conventional 
                    glazing with semi-transparent photovoltaic modules.</p>
                    
                    <div class="highlight">
                        <strong>Key Findings:</strong>
                        <ul>
                            <li>Building Elements Analyzed: {len(building_elements)} windows and facades</li>
                            <li>Recommended PV Technology: {pv_data.get('panel_type', 'Semi-transparent BIPV')}</li>
                            <li>Total System Capacity: {pv_data.get('total_capacity', 0):.1f} kW</li>
                            <li>Expected Annual Generation: {energy_balance.get('total_generation', 0):,.0f} kWh</li>
                            <li>Investment Payback Period: {financial_analysis.get('payback_period', 0):.1f} years</li>
                        </ul>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>2. Building Analysis</h2>
                <div class="subsection">
                    <h3>BIM-Extracted Building Elements</h3>
                    <p>Analysis based on {len(building_elements)} building elements extracted from BIM model data:</p>
                    
                    <table>
                        <tr><th>Element Type</th><th>Count</th><th>Total Area (m²)</th><th>Average Area (m²)</th></tr>
                        <tr><td>Windows</td><td>{len([e for e in building_elements if 'window' in e.get('type', '').lower()])}</td>
                        <td>{sum(e.get('glass_area', 0) for e in building_elements if 'window' in e.get('type', '').lower()):.1f}</td>
                        <td>{sum(e.get('glass_area', 0) for e in building_elements if 'window' in e.get('type', '').lower()) / max(len([e for e in building_elements if 'window' in e.get('type', '').lower()]), 1):.1f}</td></tr>
                        <tr><td>Curtain Walls</td><td>{len([e for e in building_elements if 'curtain' in e.get('type', '').lower()])}</td>
                        <td>{sum(e.get('glass_area', 0) for e in building_elements if 'curtain' in e.get('type', '').lower()):.1f}</td>
                        <td>{sum(e.get('glass_area', 0) for e in building_elements if 'curtain' in e.get('type', '').lower()) / max(len([e for e in building_elements if 'curtain' in e.get('type', '').lower()]), 1):.1f}</td></tr>
                    </table>
                </div>
            </div>

            <div class="section">
                <h2>3. Financial Analysis</h2>
                <div class="subsection">
                    <h3>Investment Overview</h3>
                    <table>
                        <tr><th>Financial Metric</th><th>Value</th></tr>
                        <tr><td>Initial Investment</td><td>{currency_symbol}{financial_analysis.get('initial_investment', 0):,.0f}</td></tr>
                        <tr><td>Annual Savings</td><td>{currency_symbol}{financial_analysis.get('annual_savings', 0):,.0f}</td></tr>
                        <tr><td>Net Present Value</td><td>{currency_symbol}{financial_analysis.get('npv', 0):,.0f}</td></tr>
                        <tr><td>Internal Rate of Return</td><td>{financial_analysis.get('irr', 0):.1%}</td></tr>
                        <tr><td>Payback Period</td><td>{financial_analysis.get('payback_period', 0):.1f} years</td></tr>
                    </table>
                </div>
            </div>

            <div class="section">
                <h2>4. Environmental Impact</h2>
                <div class="subsection">
                    <h3>Carbon Footprint Reduction</h3>
                    <table>
                        <tr><th>Environmental Metric</th><th>Value</th></tr>
                        <tr><td>Annual CO₂ Savings</td><td>{financial_analysis.get('co2_savings_annual', 0):.1f} tons</td></tr>
                        <tr><td>25-Year CO₂ Savings</td><td>{financial_analysis.get('co2_savings_lifetime', 0):.0f} tons</td></tr>
                        <tr><td>Equivalent Trees Planted</td><td>{financial_analysis.get('trees_equivalent', 0):,.0f} trees</td></tr>
                    </table>
                </div>
            </div>

            <div class="section">
                <h2>5. Technical Specifications</h2>
                <div class="subsection">
                    <h3>BIPV System Parameters</h3>
                    <table>
                        <tr><th>Parameter</th><th>Value</th><th>Unit</th></tr>
                        <tr><td>PV Technology</td><td>{pv_data.get('panel_type', 'Semi-transparent')}</td><td>-</td></tr>
                        <tr><td>Module Efficiency</td><td>{pv_data.get('efficiency', 0):.1f}</td><td>%</td></tr>
                        <tr><td>Transparency Level</td><td>{pv_data.get('transparency', 0):.0f}</td><td>%</td></tr>
                        <tr><td>Total Capacity</td><td>{pv_data.get('total_capacity', 0):.1f}</td><td>kW</td></tr>
                        <tr><td>Annual Generation</td><td>{energy_balance.get('total_generation', 0):,.0f}</td><td>kWh</td></tr>
                    </table>
                </div>
            </div>

            <div class="section">
                <h2>6. Conclusions and Recommendations</h2>
                <div class="subsection">
                    <p>The BIPV analysis demonstrates significant potential for integrating photovoltaic technology into the building envelope. 
                    The combination of energy generation, aesthetic integration, and financial viability makes BIPV an attractive option for this project.</p>
                    
                    <h3>Implementation Recommendations:</h3>
                    <ol>
                        <li>Begin with south and west-facing facades for maximum solar exposure</li>
                        <li>Use high-efficiency semi-transparent modules for optimal balance of energy generation and daylighting</li>
                        <li>Implement monitoring systems for performance optimization</li>
                        <li>Consider phased installation to distribute costs and minimize disruption</li>
                    </ol>
                </div>
            </div>
        </div>
        
        <footer style="margin-top: 50px; padding: 20px; border-top: 2px solid #2E8B57; text-align: center; font-size: 12px; color: #666;">
            <p><strong>BIPV Optimizer</strong> - Building Integrated Photovoltaic Analysis Platform</p>
            <p>PhD Research Project | Technische Universität Berlin</p>
            <p>Contact: Mostafa Gabr | ResearchGate: https://www.researchgate.net/profile/Mostafa-Gabr</p>
            <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </footer>
    </body>
    </html>"""
    
    return html_content