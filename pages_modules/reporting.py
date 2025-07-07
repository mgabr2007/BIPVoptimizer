"""
Step 10: Report Upload & Master Analysis Generator
Upload individual step reports to create comprehensive master analysis
"""
import streamlit as st
from datetime import datetime
import io
from bs4 import BeautifulSoup
import pandas as pd
from utils.individual_step_reports import create_step_download_button


def parse_html_report(html_content, step_key):
    """Parse HTML report and extract key data points"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract basic information
        data = {
            'html_content': html_content,
            'step_number': step_key,
            'parsed_successfully': True
        }
        
        # Extract key metrics based on step
        if step_key == 1:
            # Project setup data
            data['project_type'] = 'setup'
        elif step_key == 2:
            # Historical data metrics
            data['project_type'] = 'historical'
        elif step_key == 3:
            # Weather data
            data['project_type'] = 'weather'
        elif step_key == 4:
            # Building elements
            data['project_type'] = 'building'
        elif step_key == 5:
            # Radiation analysis
            data['project_type'] = 'radiation'
        elif step_key == 6:
            # PV specifications
            data['project_type'] = 'pv_specs'
        elif step_key == 7:
            # Yield analysis
            data['project_type'] = 'yield'
        elif step_key == 8:
            # Optimization
            data['project_type'] = 'optimization'
        elif step_key == 9:
            # Financial analysis
            data['project_type'] = 'financial'
        
        return data
    except Exception as e:
        return {
            'html_content': html_content,
            'step_number': step_key,
            'parsed_successfully': False,
            'error': str(e)
        }


def display_report_summary(report_data, step_key):
    """Display summary of uploaded report data"""
    if report_data.get('parsed_successfully'):
        st.success(f"✅ Step {step_key} report parsed successfully")
        st.info(f"Report type: {report_data.get('project_type', 'Unknown')}")
    else:
        st.error(f"❌ Failed to parse Step {step_key} report")
        if 'error' in report_data:
            st.error(f"Error: {report_data['error']}")


def generate_master_report_from_uploads():
    """Generate comprehensive master report from all uploaded step reports"""
    uploaded_reports = st.session_state.get('uploaded_reports', {})
    
    if not uploaded_reports:
        return None
    
    # Generate master HTML combining all reports
    master_html = generate_master_html_report(uploaded_reports)
    
    # Store master report
    st.session_state.master_report = {
        'html_content': master_html,
        'generated_at': datetime.now(),
        'included_steps': list(uploaded_reports.keys())
    }
    
    return st.session_state.master_report


def generate_master_html_report(uploaded_reports):
    """Generate HTML content for master analysis report"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>BIPV Master Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background: #f0f8ff; padding: 20px; border-radius: 10px; }}
            .step-section {{ margin: 30px 0; border-left: 4px solid #4CAF50; padding-left: 20px; }}
            .step-title {{ color: #2E7D32; font-size: 1.5em; margin-bottom: 15px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>BIPV Master Analysis Report</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Included Steps: {len(uploaded_reports)} of 9 workflow steps</p>
        </div>
    """
    
    # Add each uploaded report
    for step_num in sorted(uploaded_reports.keys()):
        report_data = uploaded_reports[step_num]
        html += f"""
        <div class="step-section">
            <div class="step-title">Step {step_num}: {report_data.get('project_type', 'Analysis').title()}</div>
            {report_data.get('html_content', '<p>No content available</p>')}
        </div>
        """
    
    html += """
    </body>
    </html>
    """
    
    return html


def display_master_report_summary(master_report):
    """Display summary of generated master report"""
    if master_report:
        st.success(f"✅ Master report generated successfully!")
        st.info(f"Generated at: {master_report['generated_at'].strftime('%Y-%m-%d %H:%M:%S')}")
        st.info(f"Includes {len(master_report['included_steps'])} steps: {', '.join(map(str, master_report['included_steps']))}")
        
        # Download button for master report
        st.download_button(
            label="📄 Download Master Analysis Report",
            data=master_report['html_content'],
            file_name=f"BIPV_Master_Analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            mime="text/html",
            key="download_master_report"
        )


def render_reporting():
    """Render the comprehensive report upload and integration interface"""
    st.header("Step 10: Report Upload & Master Analysis")
    st.markdown("Upload individual step reports to create a comprehensive master analysis document.")
    
    # Initialize uploaded reports in session state
    if 'uploaded_reports' not in st.session_state:
        st.session_state.uploaded_reports = {}
    
    st.markdown("### 📤 Upload Individual Step Reports")
    st.info("Upload HTML reports from Steps 1-9 to create a comprehensive master analysis. You can upload reports in any order.")
    
    # Create upload interface for each step
    col1, col2, col3 = st.columns(3)
    
    step_titles = {
        1: "Project Setup",
        2: "Historical Data", 
        3: "Weather Analysis",
        4: "Facade Extraction",
        5: "Radiation Analysis",
        6: "PV Specification",
        7: "Yield vs Demand",
        8: "Optimization",
        9: "Financial Analysis"
    }
    
    # Display upload widgets in a grid
    for i, (step_num, title) in enumerate(step_titles.items()):
        if i % 3 == 0:
            column = col1
        elif i % 3 == 1:
            column = col2
        else:
            column = col3
        
        with column:
            st.markdown(f"**Step {step_num}: {title}**")
            
            # Check if already uploaded
            if step_num in st.session_state.uploaded_reports:
                st.success("✅ Uploaded")
                if st.button(f"Remove Step {step_num}", key=f"remove_{step_num}"):
                    del st.session_state.uploaded_reports[step_num]
                    st.rerun()
            else:
                uploaded_file = st.file_uploader(
                    f"Upload Step {step_num}",
                    type=['html'],
                    key=f"upload_step_{step_num}",
                    help=f"Upload the HTML report from {title}"
                )
                
                if uploaded_file is not None:
                    # Read and parse the uploaded file
                    with st.spinner(f"Processing Step {step_num} report..."):
                        html_content = uploaded_file.read().decode('utf-8')
                        report_data = parse_html_report(html_content, step_num)
                        
                        # Store in session state
                        st.session_state.uploaded_reports[step_num] = report_data
                        
                        # Display summary
                        display_report_summary(report_data, step_num)
                        
                        st.rerun()
    
    # Progress tracking
    st.markdown("---")
    st.markdown("### 📊 Upload Progress")
    
    uploaded_count = len(st.session_state.uploaded_reports)
    progress = uploaded_count / 9
    
    st.progress(progress)
    st.info(f"Progress: {uploaded_count}/9 reports uploaded ({progress*100:.0f}%)")
    
    # Show uploaded reports summary
    if st.session_state.uploaded_reports:
        st.markdown("**Uploaded Reports:**")
        for step_num in sorted(st.session_state.uploaded_reports.keys()):
            report_type = st.session_state.uploaded_reports[step_num].get('project_type', 'Unknown')
            st.write(f"• Step {step_num}: {step_titles[step_num]} ({report_type})")
    
    # Generate master report
    st.markdown("---")
    st.markdown("### 📄 Generate Master Report")
    
    if uploaded_count >= 3:  # Minimum 3 reports to generate master
        st.info(f"Ready to generate master report with {uploaded_count} uploaded reports.")
        
        if st.button("🔄 Generate Master Analysis Report", type="primary", key="generate_master"):
            with st.spinner("Generating comprehensive master report..."):
                master_report = generate_master_report_from_uploads()
                
                if master_report:
                    display_master_report_summary(master_report)
                else:
                    st.error("Failed to generate master report")
    else:
        st.warning(f"Upload at least 3 reports to generate master analysis. Currently: {uploaded_count}/9")
    
    # Display master report if available
    if 'master_report' in st.session_state:
        st.markdown("---")
        st.markdown("### 📋 Master Report Status")
        display_master_report_summary(st.session_state.master_report)
    
    # Clear all uploads option
    if st.session_state.uploaded_reports:
        st.markdown("---")
        if st.button("🗑️ Clear All Uploads", key="clear_uploads"):
            st.session_state.uploaded_reports = {}
            if 'master_report' in st.session_state:
                del st.session_state.master_report
            st.success("All uploads cleared!")
            st.rerun()