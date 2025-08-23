"""
Comprehensive BIPV Optimization HTML Report Generator
Generates detailed HTML reports with authentic data and visualizations for download
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime
import base64
import io
import tempfile
import os
from database_manager import db_manager

# Configure Kaleido to use system Chromium
os.environ['PLOTLY_KALEIDO_EXECUTABLE'] = '/nix/store/zi4f80l169xlmivz8vja8wlphq74qqk0-chromium-125.0.6422.141/bin/chromium'

class BIPVReportGenerator:
    def __init__(self, project_id):
        self.project_id = project_id
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_title = f"BIPV Comprehensive Analysis Report - Project {project_id}"
        
    def generate_html_report(self):
        """Generate comprehensive HTML report with all Step 10 data and charts"""
        try:
            conn = db_manager.get_connection()
            if not conn:
                return None
            cursor = conn.cursor()
            
            # Get all data from database
            # Project information
            cursor.execute("""
                SELECT project_name, latitude, longitude, timezone, created_at
                FROM projects WHERE id = %s
            """, (self.project_id,))
            project_info = cursor.fetchone()
            
            # Building elements summary
            cursor.execute("""
                SELECT COUNT(*) as total_elements,
                       COUNT(CASE WHEN pv_suitable = true THEN 1 END) as suitable_elements,
                       SUM(glass_area) as total_area,
                       AVG(glass_area) as avg_area,
                       COUNT(DISTINCT family) as unique_families,
                       COUNT(DISTINCT building_level) as unique_levels
                FROM building_elements WHERE project_id = %s
            """, (self.project_id,))
            building_summary = cursor.fetchone()
            
            # Orientation distribution using azimuth
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN azimuth >= 315 OR azimuth < 45 THEN 'North'
                        WHEN azimuth >= 45 AND azimuth < 135 THEN 'East'
                        WHEN azimuth >= 135 AND azimuth < 225 THEN 'South'
                        WHEN azimuth >= 225 AND azimuth < 315 THEN 'West'
                    END as orientation,
                    COUNT(*) as count,
                    AVG(glass_area) as avg_area
                FROM building_elements 
                WHERE project_id = %s AND azimuth IS NOT NULL
                GROUP BY 
                    CASE 
                        WHEN azimuth >= 315 OR azimuth < 45 THEN 'North'
                        WHEN azimuth >= 45 AND azimuth < 135 THEN 'East'
                        WHEN azimuth >= 135 AND azimuth < 225 THEN 'South'
                        WHEN azimuth >= 225 AND azimuth < 315 THEN 'West'
                    END
                HAVING 
                    CASE 
                        WHEN azimuth >= 315 OR azimuth < 45 THEN 'North'
                        WHEN azimuth >= 45 AND azimuth < 135 THEN 'East'
                        WHEN azimuth >= 135 AND azimuth < 225 THEN 'South'
                        WHEN azimuth >= 225 AND azimuth < 315 THEN 'West'
                    END IS NOT NULL
                ORDER BY count DESC
            """, (self.project_id,))
            orientation_data = cursor.fetchall()
            
            # Start building HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{self.report_title}</title>
                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                    .header {{ text-align: center; border-bottom: 3px solid #1f4e79; padding-bottom: 20px; margin-bottom: 30px; }}
                    h1 {{ color: #1f4e79; font-size: 28px; margin-bottom: 10px; }}
                    h2 {{ color: #2e75b6; font-size: 20px; margin-top: 30px; margin-bottom: 15px; border-left: 4px solid #2e75b6; padding-left: 15px; }}
                    h3 {{ color: #2e75b6; font-size: 16px; margin-top: 20px; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                    th {{ background-color: #2e75b6; color: white; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    .chart-container {{ margin: 30px 0; }}
                    .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
                    .metric-card {{ background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 20px; }}
                    .metric-value {{ font-size: 24px; font-weight: bold; color: #2e75b6; }}
                    .metric-label {{ color: #6c757d; font-size: 14px; }}
                    .timestamp {{ color: #6c757d; font-style: italic; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>BIPV Comprehensive Analysis Report</h1>
                    <p class="timestamp">Project {self.project_id} | Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
                    <p><strong>Research Standards:</strong> TU Berlin PhD Research | <strong>Data Integrity:</strong> Authentic Sources Only</p>
                </div>
            """
            
            # Project Information Section
            if project_info:
                html_content += f"""
                <h2>Project Information</h2>
                <table>
                    <tr><th>Parameter</th><th>Value</th></tr>
                    <tr><td>Project Name</td><td>{project_info[0] if project_info[0] else 'N/A'}</td></tr>
                    <tr><td>Location</td><td>{project_info[1]:.4f}, {project_info[2]:.4f}</td></tr>
                    <tr><td>Timezone</td><td>{project_info[3] if project_info[3] else 'N/A'}</td></tr>
                    <tr><td>Created</td><td>{project_info[4].strftime('%Y-%m-%d') if project_info[4] else 'N/A'}</td></tr>
                </table>
                """
            
            # Building Analysis Section
            if building_summary:
                suitability_rate = (building_summary[1]/building_summary[0]*100) if building_summary[0] and building_summary[1] else 0
                html_content += f"""
                <h2>Building Analysis Summary</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">{building_summary[0]:,}</div>
                        <div class="metric-label">Total Elements</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{building_summary[1]:,}</div>
                        <div class="metric-label">Suitable Elements</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{suitability_rate:.1f}%</div>
                        <div class="metric-label">Suitability Rate</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{building_summary[2]:,.1f} m²</div>
                        <div class="metric-label">Total Glass Area</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{building_summary[3]:.2f} m²</div>
                        <div class="metric-label">Average Element Area</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{building_summary[4]}</div>
                        <div class="metric-label">Unique Families</div>
                    </div>
                </div>
                """
            
            # Orientation Distribution Chart
            if orientation_data:
                orientation_labels = [row[0] for row in orientation_data]
                orientation_counts = [row[1] for row in orientation_data]
                orientation_colors = {'South': '#ff7f0e', 'East': '#1f77b4', 'West': '#2ca02c', 'North': '#9467bd'}
                
                fig = go.Figure(data=[go.Pie(
                    labels=orientation_labels,
                    values=orientation_counts,
                    marker_colors=[orientation_colors.get(label, '#808080') for label in orientation_labels]
                )])
                fig.update_layout(
                    title="Building Element Distribution by Orientation",
                    width=800, height=600
                )
                
                chart_html = pio.to_html(fig, include_plotlyjs=False, div_id="orientation_chart")
                
                html_content += f"""
                <h2>Orientation Distribution Analysis</h2>
                <div class="chart-container">
                    {chart_html}
                </div>
                
                <h3>Orientation Summary</h3>
                <table>
                    <tr><th>Orientation</th><th>Element Count</th><th>Average Area (m²)</th></tr>
                """
                
                for row in orientation_data:
                    orientation, count, avg_area = row
                    html_content += f"""
                    <tr><td>{orientation}</td><td>{count:,}</td><td>{avg_area:.1f}</td></tr>
                    """
                
                html_content += "</table>"
            
            # Get radiation data if available
            cursor.execute("""
                SELECT COUNT(*) as analyzed_elements,
                       AVG(er.annual_radiation) as avg_radiation,
                       MAX(er.annual_radiation) as max_radiation,
                       MIN(er.annual_radiation) as min_radiation
                FROM element_radiation er
                JOIN building_elements be ON er.element_id = be.element_id
                WHERE be.project_id = %s AND er.annual_radiation IS NOT NULL
            """, (self.project_id,))
            radiation_summary = cursor.fetchone()
            
            if radiation_summary and radiation_summary[0] > 0:
                html_content += f"""
                <h2>Radiation Analysis Results</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">{radiation_summary[0]:,}</div>
                        <div class="metric-label">Analyzed Elements</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{radiation_summary[1]:,.1f}</div>
                        <div class="metric-label">Average Radiation (kWh/m²/year)</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{radiation_summary[2]:,.1f}</div>
                        <div class="metric-label">Maximum Radiation (kWh/m²/year)</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{radiation_summary[3]:,.1f}</div>
                        <div class="metric-label">Minimum Radiation (kWh/m²/year)</div>
                    </div>
                </div>
                """
            
            # Get BIPV specifications data from JSON
            cursor.execute("""
                SELECT panel_type, efficiency, transparency, cost_per_m2, power_density, specification_data
                FROM pv_specifications
                WHERE project_id = %s
            """, (self.project_id,))
            pv_data = cursor.fetchone()
            
            bipv_specs = None
            if pv_data and pv_data[5]:  # specification_data exists
                import json
                try:
                    spec_data = json.loads(pv_data[5])
                    if 'bipv_specifications' in spec_data:
                        specs = spec_data['bipv_specifications']
                        spec_count = len(specs)
                        total_capacity = sum(float(s['capacity_kw']) for s in specs)
                        total_energy = sum(float(s['annual_energy_kwh']) for s in specs)
                        avg_capacity = total_capacity / spec_count if spec_count > 0 else 0
                        avg_energy = total_energy / spec_count if spec_count > 0 else 0
                        bipv_specs = (spec_count, avg_capacity, total_energy, avg_energy, pv_data[0], pv_data[1], pv_data[2])
                except:
                    bipv_specs = None
            
            if bipv_specs and bipv_specs[0] > 0:
                html_content += f"""
                <h2>BIPV Specifications Summary</h2>
                <table>
                    <tr><th>Parameter</th><th>Value</th></tr>
                    <tr><td>Panel Technology</td><td>{bipv_specs[4] if bipv_specs[4] else 'N/A'}</td></tr>
                    <tr><td>Efficiency</td><td>{bipv_specs[5]:.1%} if bipv_specs[5] else 'N/A'</td></tr>
                    <tr><td>Transparency</td><td>{bipv_specs[6]:.1%} if bipv_specs[6] else 'N/A'</td></tr>
                </table>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">{bipv_specs[0]:,}</div>
                        <div class="metric-label">Specified Elements</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{bipv_specs[1]:,.1f} kW</div>
                        <div class="metric-label">Average Capacity</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{bipv_specs[2]:,.0f} kWh</div>
                        <div class="metric-label">Total Annual Energy</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{bipv_specs[3]:,.1f} kWh</div>
                        <div class="metric-label">Average Annual Energy</div>
                    </div>
                </div>
                """
            
            # Close HTML
            html_content += """
            </body>
            </html>
            """
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"BIPV_Comprehensive_Analysis_Report_{timestamp}.html"
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8')
            temp_file.write(html_content)
            temp_file.close()
            
            conn.close()
            return temp_file.name, filename
            
        except Exception as e:
            st.error(f"Error generating HTML report: {str(e)}")
            return None, None


def create_download_links(pdf_content, docx_content, project_id):
    """Create download links for generated reports (legacy function)"""
    st.info("HTML reports now available - more reliable than PDF/Word formats")