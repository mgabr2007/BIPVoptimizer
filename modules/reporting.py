import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import base64
import io

def generate_executive_summary(project_data):
    """Generate executive summary for the report."""
    
    # Extract key metrics
    pv_specs = pd.DataFrame(project_data.get('pv_specifications', {}))
    optimization_results = pd.DataFrame(project_data.get('optimization_results', {}))
    financial_analysis = project_data.get('financial_analysis', [])
    energy_balance = pd.DataFrame(project_data.get('energy_balance', {}))
    
    summary = {
        'project_name': project_data.get('project_name', 'BIPV Analysis Project'),
        'total_roof_area': f"{pv_specs['element_area'].sum():.0f} m²" if len(pv_specs) > 0 else "N/A",
        'optimal_system_size': f"{optimization_results.iloc[0]['system_power_kw']:.1f} kW" if len(optimization_results) > 0 else "N/A",
        'annual_energy_production': f"{optimization_results.iloc[0]['annual_yield_kwh']:,.0f} kWh" if len(optimization_results) > 0 else "N/A",
        'investment_required': f"${optimization_results.iloc[0]['installation_cost']:,.0f}" if len(optimization_results) > 0 else "N/A",
        'annual_savings': f"${optimization_results.iloc[0]['annual_savings']:,.0f}" if len(optimization_results) > 0 else "N/A",
        'payback_period': f"{financial_analysis[0]['payback_period']:.1f} years" if financial_analysis else "N/A",
        'npv': f"${financial_analysis[0]['npv']:,.0f}" if financial_analysis else "N/A",
        'co2_savings': f"{financial_analysis[0]['lifetime_co2_savings_tons']:.1f} tons" if financial_analysis else "N/A",
        'energy_independence': f"{optimization_results.iloc[0]['energy_independence']:.1f}%" if len(optimization_results) > 0 else "N/A"
    }
    
    return summary

def create_technical_charts(project_data):
    """Create technical charts for the report."""
    charts = {}
    
    try:
        # Energy balance chart
        if 'energy_balance' in project_data:
            energy_balance = pd.DataFrame(project_data['energy_balance'])
            
            fig_energy = go.Figure()
            fig_energy.add_trace(go.Scatter(
                x=energy_balance['date'],
                y=energy_balance['predicted_demand'],
                mode='lines+markers',
                name='Energy Demand',
                line=dict(color='red', width=3)
            ))
            fig_energy.add_trace(go.Scatter(
                x=energy_balance['date'],
                y=energy_balance['total_pv_yield'],
                mode='lines+markers',
                name='PV Generation',
                line=dict(color='green', width=3)
            ))
            fig_energy.update_layout(
                title='Monthly Energy Profile',
                xaxis_title='Month',
                yaxis_title='Energy (kWh)',
                height=400
            )
            charts['energy_balance'] = fig_energy
        
        # System performance by orientation
        if 'pv_specifications' in project_data:
            pv_specs = pd.DataFrame(project_data['pv_specifications'])
            
            orientation_perf = pv_specs.groupby('orientation').agg({
                'system_power_kw': 'sum',
                'annual_energy_kwh': 'sum'
            }).reset_index()
            
            fig_orientation = px.bar(
                orientation_perf,
                x='orientation',
                y='annual_energy_kwh',
                title='Annual Energy Production by Orientation',
                labels={'annual_energy_kwh': 'Annual Energy (kWh)'}
            )
            fig_orientation.update_layout(height=400)
            charts['orientation_performance'] = fig_orientation
        
        # Financial cash flow
        if 'financial_analysis' in project_data and project_data['financial_analysis']:
            financial_data = project_data['financial_analysis'][0]
            annual_details = pd.DataFrame(financial_data['annual_details'])
            
            fig_cashflow = go.Figure()
            fig_cashflow.add_trace(go.Scatter(
                x=annual_details['year'],
                y=annual_details['cumulative_cash_flow'],
                mode='lines+markers',
                name='Cumulative Cash Flow',
                line=dict(color='blue', width=3)
            ))
            fig_cashflow.add_hline(y=0, line_dash="dot", line_color="gray")
            fig_cashflow.update_layout(
                title='Cumulative Cash Flow Over Time',
                xaxis_title='Year',
                yaxis_title='Cash Flow ($)',
                height=400
            )
            charts['cash_flow'] = fig_cashflow
        
    except Exception as e:
        st.error(f"Error creating technical charts: {str(e)}")
    
    return charts

def create_financial_charts(project_data):
    """Create financial analysis charts."""
    charts = {}
    
    try:
        if 'optimization_results' in project_data:
            optimization_results = pd.DataFrame(project_data['optimization_results'])
            
            # Cost vs savings comparison
            fig_cost_savings = px.scatter(
                optimization_results,
                x='installation_cost',
                y='annual_savings',
                size='system_power_kw',
                color='simple_payback_years',
                title='Investment vs Annual Savings',
                labels={
                    'installation_cost': 'Installation Cost ($)',
                    'annual_savings': 'Annual Savings ($)',
                    'simple_payback_years': 'Payback (years)'
                }
            )
            fig_cost_savings.update_layout(height=400)
            charts['cost_vs_savings'] = fig_cost_savings
            
            # ROI comparison
            fig_roi = px.bar(
                optimization_results.head(5),
                x='solution_id',
                y='energy_independence',
                title='Energy Independence by Solution',
                labels={'energy_independence': 'Energy Independence (%)'}
            )
            fig_roi.update_layout(height=400)
            charts['energy_independence'] = fig_roi
        
    except Exception as e:
        st.error(f"Error creating financial charts: {str(e)}")
    
    return charts

def generate_html_report(project_data, report_type):
    """Generate HTML report."""
    
    # Get project information
    project_name = project_data.get('project_name', 'BIPV Analysis Project')
    creation_date = datetime.now().strftime('%B %d, %Y')
    
    # Generate executive summary
    exec_summary = generate_executive_summary(project_data)
    
    # Start HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{project_name} - BIPV Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
            .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; }}
            .section {{ margin: 30px 0; }}
            .metric {{ display: inline-block; margin: 10px 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
            .metric-value {{ font-size: 24px; font-weight: bold; color: #2E86AB; }}
            .metric-label {{ font-size: 14px; color: #666; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .recommendation {{ background-color: #f9f9f9; padding: 20px; border-left: 4px solid #2E86AB; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{project_name}</h1>
            <h2>Building Integrated Photovoltaic (BIPV) Analysis Report</h2>
            <p>Generated on {creation_date}</p>
        </div>
    """
    
    if report_type == "Executive Summary":
        html_content += f"""
        <div class="section">
            <h2>Executive Summary</h2>
            <p>This report presents the analysis results for the Building Integrated Photovoltaic (BIPV) system 
            assessment of {exec_summary['project_name']}. The analysis encompasses solar resource assessment, 
            system optimization, financial modeling, and environmental impact evaluation.</p>
            
            <h3>Key Findings</h3>
            <div class="metric">
                <div class="metric-value">{exec_summary['optimal_system_size']}</div>
                <div class="metric-label">Optimal System Size</div>
            </div>
            <div class="metric">
                <div class="metric-value">{exec_summary['annual_energy_production']}</div>
                <div class="metric-label">Annual Energy Production</div>
            </div>
            <div class="metric">
                <div class="metric-value">{exec_summary['investment_required']}</div>
                <div class="metric-label">Investment Required</div>
            </div>
            <div class="metric">
                <div class="metric-value">{exec_summary['payback_period']}</div>
                <div class="metric-label">Payback Period</div>
            </div>
            <div class="metric">
                <div class="metric-value">{exec_summary['co2_savings']}</div>
                <div class="metric-label">Lifetime CO₂ Savings</div>
            </div>
            <div class="metric">
                <div class="metric-value">{exec_summary['energy_independence']}</div>
                <div class="metric-label">Energy Independence</div>
            </div>
        </div>
        
        <div class="section">
            <h3>Recommendations</h3>
            <div class="recommendation">
                <p><strong>Primary Recommendation:</strong> Proceed with the optimized BIPV installation as it demonstrates 
                strong financial returns with a payback period of {exec_summary['payback_period']} and significant 
                environmental benefits.</p>
                
                <p><strong>Key Benefits:</strong></p>
                <ul>
                    <li>Annual cost savings of {exec_summary['annual_savings']}</li>
                    <li>Net present value of {exec_summary['npv']}</li>
                    <li>Reduction of {exec_summary['co2_savings']} of CO₂ emissions over system lifetime</li>
                    <li>Achievement of {exec_summary['energy_independence']} energy independence</li>
                </ul>
            </div>
        </div>
        """
    
    elif report_type == "Technical Report":
        # Add technical details
        if 'pv_specifications' in project_data:
            pv_specs = pd.DataFrame(project_data['pv_specifications'])
            
            html_content += f"""
            <div class="section">
                <h2>Technical Analysis</h2>
                
                <h3>System Configuration</h3>
                <table>
                    <tr><th>Parameter</th><th>Value</th></tr>
                    <tr><td>Total Number of Elements</td><td>{len(pv_specs)}</td></tr>
                    <tr><td>Total System Power</td><td>{pv_specs['system_power_kw'].sum():.1f} kW</td></tr>
                    <tr><td>Total Panel Count</td><td>{pv_specs['panels_count'].sum()}</td></tr>
                    <tr><td>Average Specific Yield</td><td>{pv_specs['specific_yield'].mean():.0f} kWh/kW</td></tr>
                </table>
                
                <h3>Performance by Orientation</h3>
                <table>
                    <tr><th>Orientation</th><th>Elements</th><th>Total Power (kW)</th><th>Annual Energy (kWh)</th></tr>
            """
            
            orientation_summary = pv_specs.groupby('orientation').agg({
                'element_id': 'count',
                'system_power_kw': 'sum',
                'annual_energy_kwh': 'sum'
            })
            
            for orientation, row in orientation_summary.iterrows():
                html_content += f"""
                    <tr>
                        <td>{orientation}</td>
                        <td>{row['element_id']}</td>
                        <td>{row['system_power_kw']:.1f}</td>
                        <td>{row['annual_energy_kwh']:,.0f}</td>
                    </tr>
                """
            
            html_content += "</table></div>"
    
    elif report_type == "Financial Report":
        # Add financial details
        if 'financial_analysis' in project_data and project_data['financial_analysis']:
            financial_data = project_data['financial_analysis'][0]
            
            html_content += f"""
            <div class="section">
                <h2>Financial Analysis</h2>
                
                <h3>Investment Summary</h3>
                <table>
                    <tr><th>Financial Metric</th><th>Value</th></tr>
                    <tr><td>Initial Investment</td><td>${financial_data['initial_cost']:,.0f}</td></tr>
                    <tr><td>Annual Savings</td><td>${financial_data['annual_savings']:,.0f}</td></tr>
                    <tr><td>Net Present Value (NPV)</td><td>${financial_data['npv']:,.0f}</td></tr>
                    <tr><td>Internal Rate of Return (IRR)</td><td>{financial_data['irr']:.1f}%</td></tr>
                    <tr><td>Simple Payback Period</td><td>{financial_data['payback_period']:.1f} years</td></tr>
                </table>
                
                <h3>Environmental Impact</h3>
                <table>
                    <tr><th>Environmental Metric</th><th>Value</th></tr>
                    <tr><td>Annual CO₂ Savings</td><td>{financial_data['annual_co2_savings_kg']:,.0f} kg</td></tr>
                    <tr><td>Lifetime CO₂ Savings</td><td>{financial_data['lifetime_co2_savings_tons']:.1f} tons</td></tr>
                    <tr><td>Carbon Credit Value</td><td>${financial_data['carbon_credit_value']:,.0f}</td></tr>
                </table>
            </div>
            """
    
    # Close HTML
    html_content += """
    </body>
    </html>
    """
    
    return html_content

def export_raw_data(project_data, data_format):
    """Export raw analysis data."""
    
    if data_format == "CSV":
        # Combine all relevant data into CSV format
        export_data = {}
        
        # PV specifications
        if 'pv_specifications' in project_data:
            pv_specs = pd.DataFrame(project_data['pv_specifications'])
            export_data['pv_specifications.csv'] = pv_specs.to_csv(index=False)
        
        # Optimization results
        if 'optimization_results' in project_data:
            opt_results = pd.DataFrame(project_data['optimization_results'])
            export_data['optimization_results.csv'] = opt_results.to_csv(index=False)
        
        # Energy balance
        if 'energy_balance' in project_data:
            energy_balance = pd.DataFrame(project_data['energy_balance'])
            export_data['energy_balance.csv'] = energy_balance.to_csv(index=False)
        
        # Financial analysis
        if 'financial_analysis' in project_data and project_data['financial_analysis']:
            financial_data = []
            for result in project_data['financial_analysis']:
                annual_details = pd.DataFrame(result['annual_details'])
                annual_details['solution_id'] = result['solution_id']
                financial_data.append(annual_details)
            
            if financial_data:
                combined_financial = pd.concat(financial_data, ignore_index=True)
                export_data['financial_analysis.csv'] = combined_financial.to_csv(index=False)
        
        return export_data
    
    elif data_format == "JSON":
        # Export as JSON
        import json
        
        # Create clean export data
        clean_data = {}
        
        # Copy relevant project data
        for key in ['project_name', 'project_id', 'pv_specifications', 'optimization_results', 
                   'energy_balance', 'financial_analysis', 'radiation_grid']:
            if key in project_data:
                clean_data[key] = project_data[key]
        
        return json.dumps(clean_data, indent=2, default=str)
    
    return None

def render_reporting():
    """Render the reporting and export module."""
    
    st.header("11. Reporting & Export")
    st.markdown("Generate comprehensive reports and export analysis data in various formats.")
    
    # Check if analysis is complete
    required_data = ['pv_specifications', 'optimization_results']
    missing_data = [item for item in required_data if item not in st.session_state.project_data]
    
    if missing_data:
        st.warning(f"⚠️ Missing required data for reporting: {', '.join(missing_data)}")
        st.info("Please complete the optimization analysis to generate reports.")
        return
    
    # Generate executive summary
    exec_summary = generate_executive_summary(st.session_state.project_data)
    
    st.subheader("Project Summary")
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("System Size", exec_summary['optimal_system_size'])
        st.metric("Annual Production", exec_summary['annual_energy_production'])
    
    with col2:
        st.metric("Investment", exec_summary['investment_required'])
        st.metric("Annual Savings", exec_summary['annual_savings'])
    
    with col3:
        st.metric("Payback Period", exec_summary['payback_period'])
        st.metric("NPV", exec_summary['npv'])
    
    with col4:
        st.metric("CO₂ Savings", exec_summary['co2_savings'])
        st.metric("Energy Independence", exec_summary['energy_independence'])
    
    # Report generation section
    st.subheader("Report Generation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Report Type**")
        report_type = st.selectbox(
            "Select Report Type",
            ["Executive Summary", "Technical Report", "Financial Report"],
            help="Choose the type of report to generate"
        )
        
        report_format = st.selectbox(
            "Report Format",
            ["HTML", "PDF (Preview)"],
            help="Select the output format for the report"
        )
    
    with col2:
        st.markdown("**Report Options**")
        
        include_charts = st.checkbox(
            "Include Charts and Visualizations",
            value=True,
            help="Include charts and graphs in the report"
        )
        
        include_detailed_data = st.checkbox(
            "Include Detailed Data Tables",
            value=True,
            help="Include detailed data tables and specifications"
        )
        
        company_logo = st.file_uploader(
            "Company Logo (optional)",
            type=['png', 'jpg', 'jpeg'],
            help="Upload company logo for report header"
        )
    
    # Generate report
    if st.button("Generate Report"):
        with st.spinner(f"Generating {report_type} report..."):
            try:
                if report_format == "HTML":
                    html_report = generate_html_report(st.session_state.project_data, report_type)
                    
                    # Store report for download
                    st.session_state.project_data['generated_report'] = html_report
                    
                    st.success("✅ Report generated successfully!")
                    
                    # Preview report
                    with st.expander("📄 Report Preview"):
                        st.components.v1.html(html_report, height=600, scrolling=True)
                    
                    # Download button
                    st.download_button(
                        label=f"Download {report_type} Report (HTML)",
                        data=html_report,
                        file_name=f"bipv_analysis_{report_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.html",
                        mime="text/html"
                    )
                
                elif report_format == "PDF (Preview)":
                    st.info("📄 PDF generation would be available in production version with additional libraries (weasyprint, reportlab)")
                    
                    # Show HTML preview instead
                    html_report = generate_html_report(st.session_state.project_data, report_type)
                    with st.expander("📄 PDF Preview (HTML version)"):
                        st.components.v1.html(html_report, height=600, scrolling=True)
                
            except Exception as e:
                st.error(f"❌ Error generating report: {str(e)}")
    
    # Data export section
    st.subheader("Data Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Raw Data Export**")
        
        data_format = st.selectbox(
            "Export Format",
            ["CSV", "JSON", "Excel (Preview)"],
            help="Choose format for raw data export"
        )
        
        export_components = st.multiselect(
            "Select Data Components",
            ["PV Specifications", "Optimization Results", "Energy Balance", "Financial Analysis", "Radiation Grid"],
            default=["PV Specifications", "Optimization Results", "Energy Balance"],
            help="Choose which data components to include in export"
        )
    
    with col2:
        st.markdown("**BIM Model Export**")
        
        bim_format = st.selectbox(
            "BIM Export Format",
            ["IFC", "Revit Family", "SketchUp", "Not Available"],
            help="Export format for updated BIM model with PV placements"
        )
        
        include_pv_families = st.checkbox(
            "Include PV Panel Families",
            value=True,
            help="Include detailed PV panel geometry in BIM export"
        )
    
    # Export data
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export Raw Data"):
            with st.spinner("Preparing data export..."):
                try:
                    if data_format == "CSV":
                        export_data = export_raw_data(st.session_state.project_data, "CSV")
                        
                        if export_data:
                            # Create ZIP file for multiple CSVs
                            import zipfile
                            
                            zip_buffer = io.BytesIO()
                            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                                for filename, csv_data in export_data.items():
                                    zip_file.writestr(filename, csv_data)
                            
                            st.download_button(
                                label="Download CSV Data (ZIP)",
                                data=zip_buffer.getvalue(),
                                file_name=f"bipv_analysis_data_{datetime.now().strftime('%Y%m%d')}.zip",
                                mime="application/zip"
                            )
                        else:
                            st.error("No data available for export")
                    
                    elif data_format == "JSON":
                        json_data = export_raw_data(st.session_state.project_data, "JSON")
                        
                        if json_data:
                            st.download_button(
                                label="Download JSON Data",
                                data=json_data,
                                file_name=f"bipv_analysis_data_{datetime.now().strftime('%Y%m%d')}.json",
                                mime="application/json"
                            )
                        else:
                            st.error("No data available for export")
                    
                    elif data_format == "Excel (Preview)":
                        st.info("📊 Excel export would be available in production version with openpyxl library")
                
                except Exception as e:
                    st.error(f"❌ Error exporting data: {str(e)}")
    
    with col2:
        if st.button("Export BIM Model"):
            if bim_format == "Not Available":
                st.info("🏗️ BIM model export requires integration with BIM software APIs")
            else:
                st.info(f"🏗️ {bim_format} export would be available in production version with BIM API integration")
    
    # Analysis summary and insights
    st.subheader("Analysis Insights")
    
    # Create charts for summary
    technical_charts = create_technical_charts(st.session_state.project_data)
    financial_charts = create_financial_charts(st.session_state.project_data)
    
    if technical_charts:
        col1, col2 = st.columns(2)
        
        with col1:
            if 'energy_balance' in technical_charts:
                st.plotly_chart(technical_charts['energy_balance'], use_container_width=True)
        
        with col2:
            if 'orientation_performance' in technical_charts:
                st.plotly_chart(technical_charts['orientation_performance'], use_container_width=True)
    
    if financial_charts:
        col1, col2 = st.columns(2)
        
        with col1:
            if 'cost_vs_savings' in financial_charts:
                st.plotly_chart(financial_charts['cost_vs_savings'], use_container_width=True)
        
        with col2:
            if 'energy_independence' in financial_charts:
                st.plotly_chart(financial_charts['energy_independence'], use_container_width=True)
    
    # Project completion status
    st.subheader("Project Completion Status")
    
    completed_modules = []
    for module in ['project_setup', 'historical_data', 'weather_environment', 'facade_extraction', 
                   'radiation_grid', 'pv_specifications', 'yield_demand', 'optimization', 
                   'financial_analysis', 'visualization_3d']:
        if any(key.startswith(module.split('_')[0]) for key in st.session_state.project_data.keys()):
            completed_modules.append(module)
    
    completion_percentage = (len(completed_modules) / 10) * 100
    
    st.progress(completion_percentage / 100)
    st.write(f"Analysis Completion: {completion_percentage:.0f}% ({len(completed_modules)}/10 modules)")
    
    # Final recommendations
    if completion_percentage >= 80:
        st.subheader("Final Recommendations")
        
        with st.container():
            st.markdown("""
            **Based on the comprehensive BIPV analysis, the following recommendations are provided:**
            
            1. **Technical Feasibility**: The building demonstrates excellent potential for BIPV integration 
               with favorable solar exposure and suitable facade areas.
            
            2. **Financial Viability**: The optimized system configuration provides attractive financial returns 
               with reasonable payback periods and positive NPV.
            
            3. **Environmental Impact**: Significant CO₂ emission reductions contribute to sustainability goals 
               and environmental stewardship.
            
            4. **Implementation Priority**: Focus on south and west-facing facades for maximum energy yield 
               and return on investment.
            
            5. **Next Steps**: 
               - Detailed structural assessment for PV mounting systems
               - Coordination with electrical systems and grid connection
               - Permits and regulatory compliance review
               - Contractor selection and project scheduling
            """)
        
        st.success("✅ BIPV analysis completed successfully! All reports and data are ready for export.")
    
    else:
        st.warning("⚠️ Complete all analysis modules for comprehensive reporting and recommendations.")
    
    # Additional resources
    with st.expander("📚 Additional Resources"):
        st.markdown("""
        **Related Documentation:**
        - BIPV Design Guidelines and Best Practices
        - Local Building Codes and Permit Requirements
        - Utility Interconnection Standards
        - Financial Incentive Programs
        - Maintenance and Operations Guidelines
        
        **Technical Support:**
        - Contact information for technical assistance
        - Training resources for system operation
        - Warranty and service provider details
        
        **Regulatory Information:**
        - Building permit requirements
        - Electrical code compliance
        - Safety standards and certifications
        - Environmental impact assessments
        """)
