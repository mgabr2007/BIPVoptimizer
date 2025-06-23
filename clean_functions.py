def generate_window_elements_csv():
    """Generate CSV file with window element data for BIPV calculations"""
    if 'building_elements' not in st.session_state or not st.session_state.building_elements:
        return None
    
    # Prepare CSV content
    csv_content = []
    csv_content.append("Element_ID,Wall_Hosted_ID,Glass_Area_m2,Orientation,Azimuth_Degrees,Annual_Radiation_kWh_m2,Expected_Production_kWh,BIPV_Selected,Window_Width_m,Window_Height_m,Building_Level")
    
    building_elements = st.session_state.building_elements
    pv_specs = st.session_state.get('pv_specs', {})
    radiation_data = st.session_state.get('radiation_data', {})
    
    for idx, element in building_elements.iterrows():
        element_id = element.get('Element_ID', f'Element_{idx}')
        wall_id = element.get('Wall_Hosted_ID', 'N/A')
        glass_area = element.get('Glass_Area', 1.5)  # Default 1.5m² if missing
        orientation = element.get('Orientation', 'Unknown')
        azimuth = element.get('Azimuth', 0)
        
        # Get radiation data for this element
        annual_radiation = radiation_data.get(element_id, 800)  # Default 800 kWh/m²
        
        # Calculate expected production
        panel_efficiency = pv_specs.get('efficiency', 20) / 100  # Convert % to decimal
        expected_production = glass_area * annual_radiation * panel_efficiency
        
        # Determine BIPV selection based on orientation and radiation
        bipv_selected = "Yes" if annual_radiation > 600 and orientation in ['South', 'Southeast', 'Southwest', 'East', 'West'] else "No"
        
        # Window dimensions (estimated from area)
        window_width = (glass_area ** 0.5) * 1.2  # Assuming rectangular, slightly wider
        window_height = glass_area / window_width
        
        building_level = element.get('Level', 'Ground Floor')
        
        # Add row to CSV
        csv_row = f"{element_id},{wall_id},{glass_area:.2f},{orientation},{azimuth},{annual_radiation:.1f},{expected_production:.1f},{bipv_selected},{window_width:.2f},{window_height:.2f},{building_level}"
        csv_content.append(csv_row)
    
    return '\n'.join(csv_content)


def generate_enhanced_html_report(include_charts, include_recommendations):
    """Generate comprehensive HTML report with detailed equations and methodology"""
    from datetime import datetime
    
    # Get session state data
    project_data = st.session_state.get('project_setup', {})
    building_elements = st.session_state.get('building_elements', None)
    pv_specs = st.session_state.get('pv_specs', {})
    financial_analysis = st.session_state.get('financial_analysis', {})
    optimization_results = st.session_state.get('optimization_results', {})
    energy_balance = st.session_state.get('energy_balance', {})
    radiation_data = st.session_state.get('radiation_data', {})
    
    # Calculate key metrics
    total_elements = len(building_elements) if building_elements is not None else 0
    suitable_elements = sum(1 for _, row in building_elements.iterrows() if row.get('PV_Suitable', False)) if building_elements is not None else 0
    total_glass_area = building_elements['Glass_Area'].sum() if building_elements is not None and 'Glass_Area' in building_elements.columns else 0
    
    # Currency symbol
    currency_symbol = "€"
    
    # Generate HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BIPV Analysis Report - {project_data.get('project_name', 'Unnamed Project')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; color: #333; }}
        .header {{ text-align: center; margin-bottom: 40px; padding: 20px; background: linear-gradient(135deg, #2E8B57, #228B22); color: white; border-radius: 10px; }}
        .section {{ margin-bottom: 30px; padding: 20px; border-left: 4px solid #2E8B57; background: #f9f9f9; }}
        .subsection {{ margin: 15px 0; padding: 15px; background: white; border-radius: 5px; }}
        .equation {{ background: #e8f4f8; padding: 15px; margin: 10px 0; border-radius: 5px; font-family: monospace; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #2E8B57; color: white; }}
        .highlight {{ background-color: #ffffcc; padding: 2px 4px; }}
        .chart-container {{ margin: 20px 0; padding: 15px; background: white; border-radius: 5px; border: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Building Integrated Photovoltaic (BIPV) Analysis Report</h1>
        <h2>{project_data.get('project_name', 'Unnamed Project')}</h2>
        <p>Location: {project_data.get('selected_location', 'Unknown Location')} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="section">
        <h2>Executive Summary</h2>
        <div class="subsection">
            <p>This comprehensive BIPV analysis evaluates the integration of photovoltaic technology into building facades and windows. 
            The analysis covers {total_elements} building elements with {suitable_elements} identified as suitable for BIPV installation, 
            representing {total_glass_area:.1f} m² of total glazed area.</p>
            
            <table>
                <tr><th>Key Metric</th><th>Value</th></tr>
                <tr><td>Total Building Elements</td><td>{total_elements}</td></tr>
                <tr><td>BIPV Suitable Elements</td><td>{suitable_elements}</td></tr>
                <tr><td>Total Glazed Area</td><td>{total_glass_area:.1f} m²</td></tr>
                <tr><td>Estimated Annual Generation</td><td>{energy_balance.get('annual_generation', 0):,.0f} kWh</td></tr>
                <tr><td>Project Investment</td><td>{currency_symbol}{financial_analysis.get('initial_investment', 0):,.0f}</td></tr>
                <tr><td>Payback Period</td><td>{financial_analysis.get('payback_period', 0):.1f} years</td></tr>
            </table>
        </div>
    </div>

    <div class="section">
        <h2>Technical Analysis</h2>
        <div class="subsection">
            <h3>PV Technology Specifications</h3>
            <table>
                <tr><th>Parameter</th><th>Value</th><th>Unit</th></tr>
                <tr><td>Panel Technology</td><td>{pv_specs.get('panel_type', 'N/A')}</td><td>-</td></tr>
                <tr><td>Module Efficiency</td><td>{pv_specs.get('efficiency', 0):.1f}</td><td>%</td></tr>
                <tr><td>Transparency Level</td><td>{pv_specs.get('transparency', 0):.0f}</td><td>%</td></tr>
                <tr><td>Cost per m²</td><td>{currency_symbol}{pv_specs.get('cost_per_m2', 0):,.0f}</td><td>EUR/m²</td></tr>
            </table>
        </div>
    </div>

    <div class="section">
        <h2>Financial Analysis</h2>
        <div class="subsection">
            <h3>Investment Summary</h3>
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
        <h2>Environmental Impact</h2>
        <div class="subsection">
            <table>
                <tr><th>Environmental Metric</th><th>Value</th></tr>
                <tr><td>Annual CO₂ Savings</td><td>{financial_analysis.get('co2_savings_annual', 0):.1f} tons</td></tr>
                <tr><td>Lifetime CO₂ Savings</td><td>{financial_analysis.get('co2_savings_lifetime', 0):.0f} tons</td></tr>
                <tr><td>Equivalent Trees Planted</td><td>{financial_analysis.get('trees_equivalent', 0):,.0f} trees</td></tr>
            </table>
        </div>
    </div>

    <div class="section">
        <h2>Conclusion</h2>
        <p>This BIPV analysis demonstrates the technical feasibility and financial viability of integrating 
        photovoltaic technology into the building envelope. The optimization ensures maximum energy generation 
        while maintaining architectural aesthetics and building functionality.</p>
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