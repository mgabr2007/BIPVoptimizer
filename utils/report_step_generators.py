"""
Step Section Generators for Comprehensive BIPV Reports
Handles HTML generation for each workflow step
"""

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
    </div>
    """

def generate_step2_section(step2_data):
    """Generate Step 2: Historical Data & AI Model section"""
    return f"""
    <div class="step-section">
        <h2 class="step-title">Step 2: Historical Data & AI Model</h2>
        
        <div class="subsection">
            <h3>AI Model Performance</h3>
            <div class="metric">
                <strong>R² Score:</strong> {step2_data['r2_score']:.3f}
            </div>
            <div class="metric">
                <strong>RMSE:</strong> {step2_data['rmse']:.2f} kWh
            </div>
            <div class="metric">
                <strong>Forecast Period:</strong> {step2_data['forecast_years']} years
            </div>
        </div>
        
        <div class="subsection">
            <h3>Building Characteristics</h3>
            <div class="metric">
                <strong>Building Floor Area:</strong> {step2_data['building_area']:,.0f} m²
            </div>
            <div class="metric">
                <strong>Energy Intensity:</strong> {step2_data['energy_intensity']:.1f} kWh/m²/year
            </div>
            <div class="metric">
                <strong>Peak Load Factor:</strong> {step2_data['peak_load_factor']:.2f}
            </div>
        </div>
    </div>
    """

def generate_step3_section(step3_data):
    """Generate Step 3: Weather & Environment Integration section"""
    return f"""
    <div class="step-section">
        <h2 class="step-title">Step 3: Weather & Environment Integration</h2>
        
        <div class="subsection">
            <h3>Solar Irradiance Data</h3>
            <div class="metric">
                <strong>Annual GHI:</strong> {step3_data['annual_ghi']:.0f} kWh/m²
            </div>
            <div class="metric">
                <strong>Annual DNI:</strong> {step3_data['annual_dni']:.0f} kWh/m²
            </div>
            <div class="metric">
                <strong>Annual DHI:</strong> {step3_data['annual_dhi']:.0f} kWh/m²
            </div>
        </div>
        
        <div class="subsection">
            <h3>Environmental Shading Factors</h3>
            <div class="metric">
                <strong>Vegetation Factor:</strong> {step3_data['vegetation_factor']:.2f}
            </div>
            <div class="metric">
                <strong>Building Shading Factor:</strong> {step3_data['building_factor']:.2f}
            </div>
            <div class="metric">
                <strong>TMY Data Points:</strong> {step3_data['tmy_hours']:,} hours
            </div>
        </div>
    </div>
    """

def generate_step4_section(step4_data):
    """Generate Step 4: Facade & Window Extraction section"""
    return f"""
    <div class="step-section">
        <h2 class="step-title">Step 4: Facade & Window Extraction</h2>
        
        <div class="subsection">
            <h3>Building Element Summary</h3>
            <div class="metric">
                <strong>Total Elements:</strong> {step4_data['total_elements']:,}
            </div>
            <div class="metric">
                <strong>Total Glass Area:</strong> {step4_data['total_area']:,.1f} m²
            </div>
            <div class="metric">
                <strong>Average Element Area:</strong> {step4_data['avg_area']:.1f} m²
            </div>
        </div>
        
        <div class="subsection">
            <h3>Orientation Distribution</h3>
            {generate_orientation_table(step4_data['orientation_counts'])}
        </div>
        
        <div class="subsection">
            <h3>Building Level Distribution</h3>
            {generate_level_table(step4_data['level_counts'])}
        </div>
    </div>
    """

def generate_step5_section(step5_data):
    """Generate Step 5: Radiation & Shading Analysis section"""
    return f"""
    <div class="step-section">
        <h2 class="step-title">Step 5: Radiation & Shading Analysis</h2>
        
        <div class="subsection">
            <h3>Radiation Analysis Summary</h3>
            <div class="metric">
                <strong>Elements Analyzed:</strong> {step5_data['total_elements']:,}
            </div>
            <div class="metric">
                <strong>Average Radiation:</strong> {step5_data['avg_radiation']:.0f} kWh/m²/year
            </div>
            <div class="metric">
                <strong>Maximum Radiation:</strong> {step5_data['max_radiation']:.0f} kWh/m²/year
            </div>
            <div class="metric">
                <strong>Minimum Radiation:</strong> {step5_data['min_radiation']:.0f} kWh/m²/year
            </div>
        </div>
        
        <div class="subsection">
            <h3>Radiation by Orientation</h3>
            {generate_radiation_by_orientation_table(step5_data['orientation_radiation'])}
        </div>
    </div>
    """

def generate_step6_section(step6_data):
    """Generate Step 6: PV Panel Specification section"""
    return f"""
    <div class="step-section">
        <h2 class="step-title">Step 6: PV Panel Specification</h2>
        
        <div class="subsection">
            <h3>BIPV System Summary</h3>
            <div class="metric">
                <strong>Total Systems:</strong> {step6_data['system_count']:,}
            </div>
            <div class="metric">
                <strong>Total Capacity:</strong> {step6_data['total_capacity']:.1f} kW
            </div>
            <div class="metric">
                <strong>Total Installation Cost:</strong> €{step6_data['total_cost']:,.0f}
            </div>
            <div class="metric">
                <strong>Total Glass Area:</strong> {step6_data['total_area']:,.1f} m²
            </div>
        </div>
        
        <div class="subsection">
            <h3>BIPV Glass Specifications</h3>
            <div class="metric">
                <strong>Glass Efficiency:</strong> {step6_data['efficiency']:.1f}%
            </div>
            <div class="metric">
                <strong>Glass Transparency:</strong> {step6_data['transparency']:.1f}%
            </div>
            <div class="metric">
                <strong>Cost per m²:</strong> €{step6_data['cost_per_m2']:.0f}/m²
            </div>
            <div class="metric">
                <strong>Cost per kW:</strong> €{step6_data['cost_per_kw']:,.0f}/kW
            </div>
        </div>
    </div>
    """

def generate_step7_section(step7_data):
    """Generate Step 7: Yield vs Demand Analysis section"""
    return f"""
    <div class="step-section">
        <h2 class="step-title">Step 7: Yield vs Demand Analysis</h2>
        
        <div class="subsection">
            <h3>Annual Energy Balance</h3>
            <div class="metric">
                <strong>Annual Demand:</strong> {step7_data['annual_demand']:,.0f} kWh
            </div>
            <div class="metric">
                <strong>Annual Generation:</strong> {step7_data['annual_generation']:,.0f} kWh
            </div>
            <div class="metric">
                <strong>Self-Consumption Rate:</strong> {step7_data['self_consumption_rate']:.1f}%
            </div>
        </div>
        
        <div class="subsection">
            <h3>Financial Performance</h3>
            <div class="metric">
                <strong>Annual Cost Savings:</strong> €{step7_data['annual_savings']:,.0f}
            </div>
            <div class="metric">
                <strong>Annual Feed-in Revenue:</strong> €{step7_data['annual_revenue']:,.0f}
            </div>
            <div class="metric">
                <strong>Total Annual Benefit:</strong> €{step7_data['annual_savings'] + step7_data['annual_revenue']:,.0f}
            </div>
        </div>
    </div>
    """

def generate_step8_section(step8_data):
    """Generate Step 8: Multi-Objective Optimization section"""
    return f"""
    <div class="step-section">
        <h2 class="step-title">Step 8: Multi-Objective Optimization</h2>
        
        <div class="subsection">
            <h3>Optimization Results</h3>
            <div class="metric">
                <strong>Solution Alternatives:</strong> {step8_data['solution_count']:,}
            </div>
            <div class="metric">
                <strong>Best Cost Solution:</strong> €{step8_data['best_cost']:,.0f}
            </div>
            <div class="metric">
                <strong>Best Yield Solution:</strong> {step8_data['best_yield']:,.0f} kWh/year
            </div>
            <div class="metric">
                <strong>Best ROI Solution:</strong> {step8_data['best_roi']:.1f}%
            </div>
        </div>
        
        <div class="subsection">
            <h3>Optimization Objectives</h3>
            {generate_optimization_weights_table(step8_data['weights'])}
        </div>
    </div>
    """

def generate_step9_section(step9_data):
    """Generate Step 9: Financial & Environmental Analysis section"""
    return f"""
    <div class="step-section">
        <h2 class="step-title">Step 9: Financial & Environmental Analysis</h2>
        
        <div class="subsection">
            <h3>Financial Metrics</h3>
            <div class="metric">
                <strong>Net Present Value (NPV):</strong> €{step9_data['npv']:,.0f}
            </div>
            <div class="metric">
                <strong>Internal Rate of Return (IRR):</strong> {step9_data['irr']:.1f}%
            </div>
            <div class="metric">
                <strong>Payback Period:</strong> {step9_data['payback_period']:.1f} years
            </div>
            <div class="metric">
                <strong>Installation Cost:</strong> €{step9_data['installation_cost']:,.0f}
            </div>
        </div>
        
        <div class="subsection">
            <h3>Environmental Impact</h3>
            <div class="metric">
                <strong>System Capacity:</strong> {step9_data['system_capacity']:.1f} kW
            </div>
            <div class="metric">
                <strong>Annual CO₂ Savings:</strong> {step9_data['annual_co2_savings']:,.1f} kg CO₂
            </div>
            <div class="metric">
                <strong>25-Year CO₂ Savings:</strong> {step9_data['lifetime_co2_savings']:,.0f} kg CO₂
            </div>
            <div class="metric">
                <strong>Annual Energy Savings:</strong> €{step9_data['annual_savings']:,.0f}
            </div>
        </div>
    </div>
    """

def generate_orientation_table(orientation_counts):
    """Generate HTML table for orientation distribution"""
    if not orientation_counts:
        return "<p>No orientation data available</p>"
    
    html = '<table class="data-table">'
    html += '<tr><th>Orientation</th><th>Count</th><th>Percentage</th></tr>'
    
    total = sum(orientation_counts.values())
    for orientation, count in orientation_counts.items():
        percentage = (count / total * 100) if total > 0 else 0
        html += f'<tr><td>{orientation}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>'
    
    html += '</table>'
    return html

def generate_level_table(level_counts):
    """Generate HTML table for building level distribution"""
    if not level_counts:
        return "<p>No level data available</p>"
    
    html = '<table class="data-table">'
    html += '<tr><th>Building Level</th><th>Count</th><th>Percentage</th></tr>'
    
    total = sum(level_counts.values())
    for level, count in level_counts.items():
        percentage = (count / total * 100) if total > 0 else 0
        html += f'<tr><td>{level}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>'
    
    html += '</table>'
    return html

def generate_radiation_by_orientation_table(orientation_radiation):
    """Generate HTML table for radiation by orientation"""
    if not orientation_radiation:
        return "<p>No radiation data available</p>"
    
    html = '<table class="data-table">'
    html += '<tr><th>Orientation</th><th>Avg Radiation (kWh/m²/year)</th><th>Elements</th></tr>'
    
    for orientation, data in orientation_radiation.items():
        if isinstance(data, dict):
            avg_radiation = data.get('avg', 0)
            count = data.get('count', 0)
        else:
            avg_radiation = data
            count = 1
        
        html += f'<tr><td>{orientation}</td><td>{avg_radiation:.0f}</td><td>{count}</td></tr>'
    
    html += '</table>'
    return html

def generate_optimization_weights_table(weights):
    """Generate HTML table for optimization weights"""
    if not weights:
        return "<p>No optimization weights data available</p>"
    
    html = '<table class="data-table">'
    html += '<tr><th>Objective</th><th>Weight</th></tr>'
    
    for objective, weight in weights.items():
        html += f'<tr><td>{objective}</td><td>{weight:.1f}%</td></tr>'
    
    html += '</table>'
    return html