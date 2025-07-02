"""
Reporting and Export page for BIPV Optimizer
"""
import streamlit as st
from datetime import datetime
from services.io import get_project_report_data
from core.solar_math import get_currency_symbol, safe_divide
from pages_modules.detailed_report_generator import generate_comprehensive_detailed_report


def generate_window_elements_csv():
    """Generate CSV file with window element data for BIPV calculations"""
    # Get building elements from session state or database
    project_name = st.session_state.get('project_data', {}).get('project_name', 'Unnamed Project')
    db_data = get_project_report_data(project_name)
    
    building_elements = []
    if db_data and db_data.get('building_elements'):
        building_elements = db_data['building_elements']
    elif 'building_elements' in st.session_state:
        building_elements = st.session_state.building_elements
        if hasattr(building_elements, 'to_dict'):
            building_elements = building_elements.to_dict('records')
    
    if not building_elements:
        return "No building elements data available"
    
    # CSV header
    csv_content = [
        "Element_ID,Wall_Hosted_ID,Glass_Area,Orientation,Azimuth,Annual_Radiation,Expected_Production,BIPV_Selected,Window_Width,Window_Height,Building_Level"
    ]
    
    for element in building_elements:
        element_id = element.get('element_id', 'Unknown')
        wall_id = element.get('wall_element_id', element.get('wall_hosted_id', 'Unknown'))
        glass_area = element.get('glass_area', element.get('window_area', 0))
        orientation = element.get('orientation', 'Unknown')
        azimuth = element.get('azimuth', 0)
        
        # Estimate radiation and production based on orientation
        radiation_factors = {
            "South (135-225°)": 1800,
            "East (45-135°)": 1400,
            "West (225-315°)": 1400,
            "North (315-45°)": 900
        }
        annual_radiation = radiation_factors.get(orientation, 1200)
        
        # Estimate production (kWh) = area * radiation * efficiency * performance ratio
        efficiency = 0.15  # 15% for semi-transparent BIPV
        performance_ratio = 0.8
        
        # Convert to float to handle decimal.Decimal types from database
        glass_area_float = float(glass_area) if glass_area else 0.0
        annual_radiation_float = float(annual_radiation)
        
        expected_production = glass_area_float * annual_radiation_float * efficiency * performance_ratio / 1000
        
        bipv_selected = element.get('pv_suitable', element.get('suitable', False))
        
        # Window dimensions - use float conversion
        window_width = (glass_area_float ** 0.5) * 1.2 if glass_area_float > 0 else 0
        window_height = glass_area_float / window_width if window_width > 0 else 0
        
        building_level = element.get('level', element.get('building_level', 'Ground Floor'))
        
        csv_row = f"{element_id},{wall_id},{glass_area_float:.2f},{orientation},{azimuth},{annual_radiation_float:.1f},{expected_production:.1f},{bipv_selected},{window_width:.2f},{window_height:.2f},{building_level}"
        csv_content.append(csv_row)
    
    return '\n'.join(csv_content)


def generate_comprehensive_html_report():
    """Generate comprehensive HTML report with all analysis results"""
    project_name = st.session_state.get('project_data', {}).get('project_name', 'Unnamed Project')
    db_data = get_project_report_data(project_name)
    
    if not db_data:
        return "<h1>Error: No project data found</h1>"
    
    # Add debugging information
    try:
        st.info(f"Report data keys: {list(db_data.keys())}")
        for key, value in db_data.items():
            if key in ['initial_investment', 'annual_savings', 'npv', 'payback_period', 'co2_savings_annual', 'co2_savings_lifetime']:
                st.info(f"{key}: {value} (type: {type(value)})")
    except Exception as debug_error:
        st.warning(f"Debug info error: {debug_error}")
    
    # Extract data safely
    location = db_data.get('location', 'Unknown Location')
    coordinates = {'lat': db_data.get('latitude', 0), 'lon': db_data.get('longitude', 0)}
    building_elements = db_data.get('building_elements', [])
    
    # Calculate metrics with null value handling
    total_elements = len(building_elements)
    suitable_elements = sum(1 for elem in building_elements if elem.get('pv_suitable', False))
    
    # Safe glass area calculation
    total_glass_area = 0
    for elem in building_elements:
        glass_area = elem.get('glass_area', 0)
        if glass_area is not None:
            try:
                total_glass_area += float(glass_area)
            except (ValueError, TypeError):
                total_glass_area += 0
    
    # Safe calculations
    suitability_rate = safe_divide(suitable_elements, total_elements, 0) * 100
    avg_glass_area = safe_divide(total_glass_area, total_elements, 0)
    
    # Safe financial data conversion
    def safe_float(value, default=0):
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    initial_investment = safe_float(db_data.get('initial_investment', 0))
    annual_savings = safe_float(db_data.get('annual_savings', 0))
    npv = safe_float(db_data.get('npv', 0))
    payback_period = safe_float(db_data.get('payback_period', 0))
    
    # Environmental data
    co2_savings_annual = safe_float(db_data.get('co2_savings_annual', 0))
    co2_savings_lifetime = safe_float(db_data.get('co2_savings_lifetime', 0))
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BIPV Analysis Report - {project_name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
            .header {{ background-color: #2E8B57; color: white; padding: 20px; border-radius: 8px; }}
            .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }}
            .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
            .metric {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; }}
            .metric-value {{ font-size: 24px; font-weight: bold; color: #2E8B57; }}
            .metric-label {{ font-size: 14px; color: #666; }}
            table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>BIPV Optimization Analysis Report</h1>
            <p><strong>Project:</strong> {project_name}</p>
            <p><strong>Location:</strong> {location}</p>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="section">
            <h2>Executive Summary</h2>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value">{total_elements}</div>
                    <div class="metric-label">Total Building Elements</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{suitable_elements}</div>
                    <div class="metric-label">BIPV Suitable Elements</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{suitability_rate:.1f}%</div>
                    <div class="metric-label">Suitability Rate</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{total_glass_area:.1f} m²</div>
                    <div class="metric-label">Total Glass Area</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Financial Analysis</h2>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value">€{initial_investment:,.0f}</div>
                    <div class="metric-label">Initial Investment</div>
                </div>
                <div class="metric">
                    <div class="metric-value">€{annual_savings:,.0f}</div>
                    <div class="metric-label">Annual Savings</div>
                </div>
                <div class="metric">
                    <div class="metric-value">€{npv:,.0f}</div>
                    <div class="metric-label">Net Present Value</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{payback_period:.1f} years</div>
                    <div class="metric-label">Payback Period</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Environmental Impact</h2>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value">{co2_savings_annual:.1f} tons</div>
                    <div class="metric-label">Annual CO₂ Savings</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{co2_savings_lifetime:.0f} tons</div>
                    <div class="metric-label">Lifetime CO₂ Savings</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Building Elements Analysis</h2>
            <table>
                <thead>
                    <tr>
                        <th>Element ID</th>
                        <th>Orientation</th>
                        <th>Glass Area (m²)</th>
                        <th>BIPV Suitable</th>
                        <th>Level</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    # Add building elements to table
    for element in building_elements[:20]:  # Limit to first 20 elements
        element_id = element.get('element_id', 'Unknown')
        orientation = element.get('orientation', 'Unknown')
        glass_area = element.get('glass_area', 0)
        suitable = 'Yes' if element.get('pv_suitable', False) else 'No'
        level = element.get('building_level', element.get('level', 'Unknown'))
        
        html_content += f"""
                    <tr>
                        <td>{element_id}</td>
                        <td>{orientation}</td>
                        <td>{glass_area:.2f}</td>
                        <td>{suitable}</td>
                        <td>{level}</td>
                    </tr>
        """
    
    html_content += f"""
                </tbody>
            </table>
            {f"<p><em>Showing first 20 of {total_elements} elements</em></p>" if total_elements > 20 else ""}
        </div>
        
        <div class="section">
            <h2>Research Attribution</h2>
            <p><strong>Developed by:</strong> Mostafa Gabr</p>
            <p><strong>Institution:</strong> Technische Universität Berlin</p>
            <p><strong>Research Focus:</strong> Building-Integrated Photovoltaics Optimization</p>
            <p><strong>Contact:</strong> <a href="https://www.researchgate.net/profile/Mostafa-Gabr-4">ResearchGate Profile</a></p>
        </div>
    </body>
    </html>
    """
    
    return html_content


def render_reporting():
    """Render the reporting and export module."""
    
    # Add OptiSunny character header image
    st.image("attached_assets/step10_1751436847832.png", width=400)
    
    st.header("Step 10: Comprehensive Reporting & Data Export")
    st.markdown("Generate detailed analysis reports and export project data for further use.")
    
    # Data Usage Information
    with st.expander("📊 How This Data Will Be Used", expanded=False):
        st.markdown("""
        ### Data Flow Through BIPV Analysis Workflow:
        
        **Step 10 → Project Documentation:**
        - **Standard HTML reports** → Executive summary for stakeholders and decision-makers
        - **Detailed scientific reports** → Technical documentation for engineers and researchers
        - **Window elements CSV** → Building-specific implementation data for contractors and architects
        
        **Step 10 → External Applications:**
        - **Financial analysis results** → Integration with business planning and investment tools
        - **BIM element specifications** → CAD software import for architectural drawing updates
        - **Performance calculations** → Energy modeling software validation and benchmarking
        
        **Step 10 → Future Analysis:**
        - **Complete project archive** → Baseline for monitoring and performance validation
        - **Methodology documentation** → Replication and scaling to additional building projects
        - **Research data export** → Academic publication and industry benchmarking studies
        """)
    
    # Check if analysis is complete
    project_data = st.session_state.get('project_data', {})
    
    if not project_data.get('extraction_complete'):
        st.error("Please complete the previous analysis steps first.")
        return
    
    # Report generation options
    st.subheader("📊 Report Generation Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("**Standard Report**\nExecutive summary with key metrics and financial analysis")
        if st.button("📋 Generate Standard Report", key="generate_standard_report"):
            with st.spinner("Generating standard BIPV analysis report..."):
                try:
                    html_report = generate_comprehensive_html_report()
                    
                    st.success("Standard report generated successfully!")
                    
                    # Download button for HTML report
                    st.download_button(
                        label="📥 Download Standard Report (HTML)",
                        data=html_report,
                        file_name=f"BIPV_Standard_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                        mime="text/html",
                        key="download_standard_report"
                    )
                    
                except Exception as e:
                    st.error(f"Error generating standard report: {str(e)}")
    
    with col2:
        st.info("**Detailed Scientific Report**\nComplete methodology with equations, assumptions, and validation")
        if st.button("🔬 Generate Detailed Scientific Report", key="generate_detailed_report"):
            with st.spinner("Generating comprehensive detailed report with all equations and methodology..."):
                try:
                    detailed_report = generate_comprehensive_detailed_report()
                    
                    st.success("Detailed scientific report generated successfully!")
                    
                    # Download button for detailed report
                    st.download_button(
                        label="📥 Download Detailed Scientific Report (HTML)",
                        data=detailed_report.encode('utf-8'),
                        file_name=f"BIPV_Detailed_Scientific_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                        mime="text/html",
                        key="download_detailed_report"
                    )
                    
                    st.info("📋 Detailed report includes: Complete methodology, mathematical equations, validation framework, uncertainty analysis, and scientific documentation following international standards.")
                    
                except Exception as e:
                    st.error(f"Error generating detailed report: {str(e)}")
                    # Provide fallback
                    st.warning("Generating simplified report due to data constraints...")
                    simple_report = "<h1>BIPV Analysis Report</h1><p>Basic analysis completed. Please ensure all workflow steps are completed for comprehensive reporting.</p>"
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    st.download_button(
                        label="📥 Download Basic Report",
                        data=simple_report.encode('utf-8'),
                        file_name=f"BIPV_Basic_Report_{timestamp}.html",
                        mime="text/html",
                        key="download_fallback_report"
                    )
    
    # CSV data export
    st.subheader("Data Export")
    
    if st.button("Generate Window Elements CSV", key="generate_csv"):
        csv_content = generate_window_elements_csv()
        
        st.download_button(
            label="Download Window Elements CSV",
            data=csv_content,
            file_name=f"BIPV_Window_Elements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="download_csv"
        )
        
        st.success("CSV file generated successfully!")
    
    # Workflow completion
    st.subheader("Analysis Complete")
    
    st.success("BIPV optimization analysis workflow completed successfully!")
    
    if st.button("Start New Analysis", key="new_analysis", type="primary"):
        # Clear session state for new analysis
        for key in list(st.session_state.keys()):
            if key not in ['current_step']:
                del st.session_state[key]
        
        st.session_state.current_step = 'welcome'
        st.session_state.scroll_to_top = True
        st.rerun()