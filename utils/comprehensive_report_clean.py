"""
Comprehensive BIPV Report Generator
Generates complete HTML reports with all 9 workflow steps and reliable data extraction
"""
import streamlit as st
from datetime import datetime
from utils.report_data_extractor import (
    extract_comprehensive_project_data,
    get_step1_data, get_step2_data, get_step3_data, get_step4_data,
    get_step5_data, get_step6_data, get_step7_data, get_step8_data, get_step9_data
)
from utils.report_step_generators import (
    generate_step1_section, generate_step2_section, generate_step3_section,
    generate_step4_section, generate_step5_section, generate_step6_section,
    generate_step7_section, generate_step8_section, generate_step9_section
)

def generate_comprehensive_report():
    """Generate comprehensive report covering all 9 workflow steps"""
    
    # Get project name
    session_data = st.session_state.get('project_data', {})
    project_name = session_data.get('project_name', 'BIPV Project')
    
    # Extract comprehensive project data
    project_data = extract_comprehensive_project_data(project_name)
    
    # Extract data for each step with safe handling
    try:
        step1_data = get_step1_data(project_data)
        step2_data = get_step2_data(project_data)
        step3_data = get_step3_data(project_data)
        step4_data = get_step4_data(project_data)
        step5_data = get_step5_data(project_data)
        step6_data = get_step6_data(project_data)
        step7_data = get_step7_data(project_data)
        step8_data = get_step8_data(project_data)
        step9_data = get_step9_data(project_data)
    except Exception as e:
        st.error(f"Error extracting data: {e}")
        return None
    
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
                background-color: #f5f5f5;
                color: #333;
            }}
            .header {{
                background: linear-gradient(135deg, #4a90e2, #7b68ee);
                color: white;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 2.5em;
                font-weight: bold;
            }}
            .header p {{
                margin: 10px 0 0 0;
                font-size: 1.2em;
                opacity: 0.9;
            }}
            .step-section {{
                background: white;
                margin: 20px 0;
                padding: 25px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                border-left: 5px solid #4a90e2;
            }}
            .step-title {{
                color: #4a90e2;
                font-size: 1.8em;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 2px solid #e0e0e0;
            }}
            .subsection {{
                margin: 20px 0;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 5px;
            }}
            .subsection h3 {{
                color: #333;
                margin-bottom: 15px;
                font-size: 1.3em;
            }}
            .metric {{
                margin: 8px 0;
                padding: 5px 0;
                font-size: 1.1em;
            }}
            .metric strong {{
                color: #4a90e2;
                display: inline-block;
                min-width: 200px;
            }}
            .data-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
                background: white;
            }}
            .data-table th {{
                background-color: #4a90e2;
                color: white;
                padding: 12px;
                text-align: left;
                font-weight: bold;
            }}
            .data-table td {{
                padding: 10px 12px;
                border-bottom: 1px solid #ddd;
            }}
            .data-table tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            .footer {{
                background: #333;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 8px;
                margin-top: 40px;
            }}
            .footer a {{
                color: #4a90e2;
                text-decoration: none;
            }}
            .footer a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>BIPV Optimizer</h1>
            <p>Comprehensive Building-Integrated Photovoltaics Analysis Report</p>
            <p><strong>Project:</strong> {project_name}</p>
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    """
    
    # Generate all step sections
    try:
        html_content += generate_step1_section(step1_data)
        html_content += generate_step2_section(step2_data)
        html_content += generate_step3_section(step3_data)
        html_content += generate_step4_section(step4_data)
        html_content += generate_step5_section(step5_data)
        html_content += generate_step6_section(step6_data)
        html_content += generate_step7_section(step7_data)
        html_content += generate_step8_section(step8_data)
        html_content += generate_step9_section(step9_data)
    except Exception as e:
        html_content += f"""
        <div class="step-section">
            <h2 class="step-title">Report Generation Error</h2>
            <div class="subsection">
                <p>Error generating section: {str(e)}</p>
                <p>Project data available: {list(project_data.keys()) if project_data else 'None'}</p>
            </div>
        </div>
        """
    
    # Footer
    html_content += f"""
        <div class="footer">
            <p><strong>BIPV Optimizer Platform</strong></p>
            <p>PhD Research Project - Technische Universität Berlin</p>
            <p>Faculty VI - Planning Building Environment</p>
            <p><a href="https://www.tu.berlin/en/planen-bauen-umwelt/" target="_blank">https://www.tu.berlin/en/planen-bauen-umwelt/</a></p>
            <p>Research Contact: <a href="https://www.researchgate.net/profile/Mostafa-Gabr-4" target="_blank">Mostafa Gabr - ResearchGate Profile</a></p>
            
            <p><strong>Standards Compliance:</strong><br>
            ISO 15927-4 (Weather Data), ISO 9060 (Solar Radiation), EN 410 (Glass Properties), ASHRAE 90.1 (Building Standards)</p>
            
            <p><strong>Report Generation:</strong> BIPV Optimizer Platform - Advanced Building-Integrated Photovoltaics Analysis Tool</p>
        </div>
    </body>
    </html>
    """
    
    return html_content