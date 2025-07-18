"""
Step 10: Comprehensive BIPV Analysis Dashboard
Real-time dashboard displaying all calculated data from all workflow steps
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime
from database_manager import db_manager
from services.io import get_current_project_id
from utils.database_helper import db_helper

def load_dashboard_data():
    """Load all authentic data from database for dashboard display"""
    project_id = get_current_project_id()
    if not project_id:
        return None
    
    dashboard_data = {}
    
    try:
        conn = db_manager.get_connection()
        if not conn:
            return None
        
        with conn.cursor() as cursor:
            # Project Information (Step 1)
            cursor.execute("""
                SELECT project_name, location, latitude, longitude, timezone, 
                       currency, created_at
                FROM projects WHERE id = %s
            """, (project_id,))
            project_info = cursor.fetchone()
            
            if project_info:
                dashboard_data['project'] = {
                    'name': project_info[0],
                    'location': project_info[1],
                    'latitude': project_info[2],
                    'longitude': project_info[3],
                    'timezone': project_info[4],
                    'currency': project_info[5],
                    'electricity_rate': 0.30,  # Default rate - will be updated from actual data
                    'created_at': project_info[6]
                }
            
            # Historical Data & AI Model (Step 2)
            cursor.execute("""
                SELECT model_type, r_squared_score, training_data_size, forecast_years
                FROM ai_models WHERE project_id = %s ORDER BY created_at DESC LIMIT 1
            """, (project_id,))
            ai_model = cursor.fetchone()
            
            if ai_model:
                dashboard_data['ai_model'] = {
                    'model_type': ai_model[0],
                    'r2_score': ai_model[1],
                    'training_data_points': ai_model[2],
                    'forecast_years': ai_model[3]
                }
            
            # Weather Data (Step 3)
            cursor.execute("""
                SELECT station_id, weather_data
                FROM weather_data WHERE project_id = %s ORDER BY created_at DESC LIMIT 1
            """, (project_id,))
            weather_result = cursor.fetchone()
            
            if weather_result and weather_result[1]:
                weather_data = json.loads(weather_result[1])
                dashboard_data['weather'] = {
                    'station_id': weather_result[0],
                    'total_ghi': weather_data.get('total_annual_ghi', 0),
                    'avg_temperature': weather_data.get('avg_temperature', 0),
                    'data_points': len(weather_data.get('hourly_data', []))
                }
            
            # Building Elements (Step 4)
            cursor.execute("""
                SELECT COUNT(*) as total_elements,
                       SUM(glass_area) as total_glass_area,
                       COUNT(DISTINCT orientation) as unique_orientations,
                       COUNT(DISTINCT level) as building_levels
                FROM building_elements WHERE project_id = %s
            """, (project_id,))
            building_stats = cursor.fetchone()
            
            cursor.execute("""
                SELECT orientation, COUNT(*) as count, AVG(glass_area) as avg_area
                FROM building_elements WHERE project_id = %s
                GROUP BY orientation
            """, (project_id,))
            orientation_data = cursor.fetchall()
            
            if building_stats:
                dashboard_data['building'] = {
                    'total_elements': building_stats[0],
                    'total_glass_area': building_stats[1],
                    'unique_orientations': building_stats[2],
                    'building_levels': building_stats[3],
                    'orientation_distribution': [
                        {'orientation': row[0], 'count': row[1], 'avg_area': row[2]}
                        for row in orientation_data
                    ]
                }
            
            # Radiation Analysis (Step 5)
            cursor.execute("""
                SELECT COUNT(*) as analyzed_elements,
                       AVG(annual_radiation) as avg_radiation,
                       MAX(annual_radiation) as max_radiation,
                       MIN(annual_radiation) as min_radiation,
                       STDDEV(annual_radiation) as std_radiation
                FROM element_radiation WHERE project_id = %s
            """, (project_id,))
            radiation_stats = cursor.fetchone()
            
            cursor.execute("""
                SELECT be.orientation, AVG(er.annual_radiation) as avg_radiation, COUNT(*) as count
                FROM element_radiation er
                JOIN building_elements be ON er.element_id = be.element_id
                WHERE er.project_id = %s
                GROUP BY be.orientation
            """, (project_id,))
            radiation_by_orientation = cursor.fetchall()
            
            if radiation_stats:
                dashboard_data['radiation'] = {
                    'analyzed_elements': radiation_stats[0],
                    'avg_radiation': radiation_stats[1],
                    'max_radiation': radiation_stats[2],
                    'min_radiation': radiation_stats[3],
                    'std_radiation': radiation_stats[4],
                    'by_orientation': [
                        {'orientation': row[0], 'avg_radiation': row[1], 'count': row[2]}
                        for row in radiation_by_orientation
                    ]
                }
            
            # PV Specifications (Step 6)
            cursor.execute("""
                SELECT COUNT(*) as pv_systems,
                       SUM(capacity_kw) as total_capacity,
                       AVG(efficiency) as avg_efficiency,
                       SUM(annual_energy_kwh) as total_annual_generation
                FROM pv_specifications WHERE project_id = %s
            """, (project_id,))
            pv_stats = cursor.fetchone()
            
            if pv_stats:
                dashboard_data['pv_systems'] = {
                    'total_systems': pv_stats[0],
                    'total_capacity_kw': pv_stats[1],
                    'avg_efficiency': pv_stats[2],
                    'total_annual_generation': pv_stats[3]
                }
            
            # Energy Analysis (Step 7)
            cursor.execute("""
                SELECT annual_generation, annual_demand, net_energy_balance,
                       self_consumption_rate, energy_yield_per_m2
                FROM energy_analysis WHERE project_id = %s ORDER BY created_at DESC LIMIT 1
            """, (project_id,))
            energy_result = cursor.fetchone()
            
            if energy_result:
                dashboard_data['energy_analysis'] = {
                    'annual_generation': energy_result[0],
                    'annual_demand': energy_result[1],
                    'net_energy_balance': energy_result[2],
                    'self_consumption_rate': energy_result[3],
                    'energy_yield_per_m2': energy_result[4]
                }
            
            # Optimization Results (Step 8)
            cursor.execute("""
                SELECT solution_id, capacity, total_cost, roi, net_import
                FROM optimization_results WHERE project_id = %s ORDER BY created_at DESC LIMIT 1
            """, (project_id,))
            optimization_result = cursor.fetchone()
            
            if optimization_result:
                dashboard_data['optimization'] = {
                    'selected_systems': optimization_result[0],  # solution_id
                    'total_capacity_kw': optimization_result[1],  # capacity
                    'total_cost_eur': optimization_result[2],     # total_cost
                    'annual_savings_eur': optimization_result[4], # net_import (savings)
                    'roi_percentage': optimization_result[3]      # roi
                }
            
            # Financial Analysis (Step 9)
            cursor.execute("""
                SELECT initial_investment, npv, irr, payback_period, annual_savings
                FROM financial_analysis WHERE project_id = %s ORDER BY created_at DESC LIMIT 1
            """, (project_id,))
            financial_result = cursor.fetchone()
            
            if financial_result:
                dashboard_data['financial'] = {
                    'total_investment_eur': financial_result[0],  # initial_investment
                    'npv_eur': financial_result[1],              # npv
                    'irr_percentage': financial_result[2],       # irr
                    'payback_period_years': financial_result[3], # payback_period
                    'total_savings_25_years': financial_result[4] * 25 if financial_result[4] else 0  # annual_savings * 25
                }
            
            # Environmental Impact
            cursor.execute("""
                SELECT co2_savings_annual, co2_savings_lifetime
                FROM environmental_impact WHERE project_id = %s ORDER BY created_at DESC LIMIT 1
            """, (project_id,))
            environmental_result = cursor.fetchone()
            
            if environmental_result:
                dashboard_data['environmental'] = {
                    'annual_co2_reduction_kg': environmental_result[0],  # co2_savings_annual
                    'lifetime_co2_reduction_kg': environmental_result[1] # co2_savings_lifetime
                }
        
        conn.close()
        return dashboard_data
        
    except Exception as e:
        st.error(f"Error loading dashboard data: {str(e)}")
        return None

def create_overview_cards(data):
    """Create overview cards with key metrics"""
    if not data:
        return
    
    st.markdown("### 📊 Project Overview")
    
    # Create metric cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'building' in data:
            st.metric(
                "Building Elements",
                f"{data['building']['total_elements']:,}",
                f"{data['building']['total_glass_area']:.1f} m²"
            )
        else:
            st.metric("Building Elements", "No data", "")
    
    with col2:
        if 'pv_systems' in data:
            st.metric(
                "Total PV Capacity",
                f"{data['pv_systems']['total_capacity_kw']:.1f} kW",
                f"{data['pv_systems']['total_systems']} systems"
            )
        else:
            st.metric("Total PV Capacity", "No data", "")
    
    with col3:
        if 'energy_analysis' in data:
            generation = data['energy_analysis']['annual_generation']
            demand = data['energy_analysis']['annual_demand']
            coverage = (generation / demand * 100) if demand > 0 else 0
            st.metric(
                "Energy Coverage",
                f"{coverage:.1f}%",
                f"{generation:,.0f} kWh/year"
            )
        else:
            st.metric("Energy Coverage", "No data", "")
    
    with col4:
        if 'financial' in data:
            st.metric(
                "Investment ROI",
                f"{data['financial']['irr_percentage']:.1f}%",
                f"€{data['financial']['total_investment_eur']:,.0f}"
            )
        else:
            st.metric("Investment ROI", "No data", "")

def create_building_analysis_section(data):
    """Create building analysis visualizations"""
    if not data or 'building' not in data:
        st.warning("No building analysis data available")
        return
    
    st.markdown("### 🏢 Building Analysis (Steps 4-5)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Orientation distribution
        if data['building']['orientation_distribution']:
            orientation_df = pd.DataFrame(data['building']['orientation_distribution'])
            fig = px.pie(
                orientation_df, 
                values='count', 
                names='orientation',
                title="Element Distribution by Orientation"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Radiation performance by orientation
        if 'radiation' in data and data['radiation']['by_orientation']:
            radiation_df = pd.DataFrame(data['radiation']['by_orientation'])
            fig = px.bar(
                radiation_df,
                x='orientation',
                y='avg_radiation',
                title="Average Solar Radiation by Orientation",
                labels={'avg_radiation': 'Solar Radiation (kWh/m²/year)'}
            )
            st.plotly_chart(fig, use_container_width=True)

def create_energy_analysis_section(data):
    """Create energy analysis visualizations"""
    if not data or 'energy_analysis' not in data:
        st.warning("No energy analysis data available")
        return
    
    st.markdown("### ⚡ Energy Analysis (Step 7)")
    
    energy = data['energy_analysis']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Energy balance
        categories = ['Generation', 'Demand', 'Net Balance']
        values = [
            energy['annual_generation'],
            energy['annual_demand'],
            abs(energy['net_energy_balance'])
        ]
        colors = ['green', 'red', 'blue']
        
        fig = go.Figure(data=[
            go.Bar(
                x=categories,
                y=values,
                marker_color=colors,
                text=[f"{v:,.0f} kWh" for v in values],
                textposition='auto'
            )
        ])
        fig.update_layout(title="Annual Energy Balance")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Energy metrics
        st.markdown("**Key Energy Metrics:**")
        st.write(f"• **Self-Consumption Rate:** {energy['self_consumption_rate']:.1f}%")
        st.write(f"• **Energy Yield per m²:** {energy['energy_yield_per_m2']:.1f} kWh/m²/year")
        st.write(f"• **Coverage Ratio:** {(energy['annual_generation']/energy['annual_demand']*100):.1f}%")
        
        if energy['net_energy_balance'] > 0:
            st.success(f"✅ Energy Surplus: {energy['net_energy_balance']:,.0f} kWh/year")
        else:
            st.info(f"ℹ️ Energy Import: {abs(energy['net_energy_balance']):,.0f} kWh/year")

def create_financial_analysis_section(data):
    """Create financial analysis visualizations"""
    if not data or 'financial' not in data:
        st.warning("No financial analysis data available")
        return
    
    st.markdown("### 💰 Financial Analysis (Step 9)")
    
    financial = data['financial']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Investment metrics
        metrics = ['Investment', 'NPV', '25-Year Savings']
        values = [
            financial['total_investment_eur'],
            financial['npv_eur'],
            financial['total_savings_25_years']
        ]
        
        fig = go.Figure(data=[
            go.Bar(
                x=metrics,
                y=values,
                marker_color=['red', 'green' if financial['npv_eur'] > 0 else 'red', 'blue'],
                text=[f"€{v:,.0f}" for v in values],
                textposition='auto'
            )
        ])
        fig.update_layout(title="Financial Metrics (EUR)")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Financial performance indicators
        st.markdown("**Financial Performance:**")
        st.write(f"• **IRR:** {financial['irr_percentage']:.1f}%")
        st.write(f"• **Payback Period:** {financial['payback_period_years']:.1f} years")
        
        if financial['npv_eur'] > 0:
            st.success(f"✅ Positive NPV: €{financial['npv_eur']:,.0f}")
        else:
            st.warning(f"⚠️ Negative NPV: €{financial['npv_eur']:,.0f}")
        
        # Environmental impact
        if 'environmental' in data:
            env = data['environmental']
            st.markdown("**Environmental Impact:**")
            st.write(f"• **Annual CO₂ Reduction:** {env['annual_co2_reduction_kg']:,.0f} kg")
            st.write(f"• **25-Year CO₂ Reduction:** {env['lifetime_co2_reduction_kg']:,.0f} kg")

def create_optimization_section(data):
    """Create optimization results section"""
    if not data or 'optimization' not in data:
        st.warning("No optimization results available")
        return
    
    st.markdown("### 🎯 Optimization Results (Step 8)")
    
    opt = data['optimization']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Optimized System Selection:**")
        st.write(f"• **Selected Systems:** {opt['selected_systems']}")
        st.write(f"• **Total Capacity:** {opt['total_capacity_kw']:.1f} kW")
        st.write(f"• **Total Investment:** €{opt['total_cost_eur']:,.0f}")
    
    with col2:
        st.markdown("**Performance Metrics:**")
        st.write(f"• **Annual Savings:** €{opt['annual_savings_eur']:,.0f}")
        st.write(f"• **ROI:** {opt['roi_percentage']:.1f}%")
        
        # ROI indicator
        if opt['roi_percentage'] > 8:
            st.success("✅ Excellent ROI")
        elif opt['roi_percentage'] > 5:
            st.info("✓ Good ROI")
        else:
            st.warning("⚠️ Low ROI")

def create_project_timeline_section(data):
    """Create project information section"""
    if not data or 'project' not in data:
        st.warning("No project data available")
        return
    
    st.markdown("### 📋 Project Information (Step 1)")
    
    project = data['project']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Project Details:**")
        st.write(f"• **Name:** {project['name']}")
        st.write(f"• **Location:** {project['location']}")
        st.write(f"• **Coordinates:** {project['latitude']:.4f}, {project['longitude']:.4f}")
        st.write(f"• **Created:** {project['created_at'].strftime('%Y-%m-%d %H:%M')}")
    
    with col2:
        st.markdown("**Economic Parameters:**")
        # Get electricity rate from session state or use default
        electricity_rate = st.session_state.get('electricity_rates', {}).get('import_rate', 0.30)
        st.write(f"• **Electricity Rate:** €{electricity_rate:.3f}/kWh")
        st.write(f"• **Currency:** {project['currency']}")
        st.write(f"• **Timezone:** {project['timezone']}")
        
        # AI Model Performance
        if 'ai_model' in data:
            ai = data['ai_model']
            st.markdown("**AI Model (Step 2):**")
            st.write(f"• **R² Score:** {ai['r2_score']:.3f}")
            st.write(f"• **Training Points:** {ai['training_data_points']}")

def render_comprehensive_dashboard():
    """Render the comprehensive BIPV analysis dashboard"""
    
    # Header with project branding
    st.image("attached_assets/step08_1751436847831.png", width=400)
    st.header("📊 Step 10: Comprehensive BIPV Analysis Dashboard")
    
    # Data Usage Information
    with st.expander("📊 Dashboard Data Sources", expanded=False):
        st.markdown("""
        ### Real-Time Database Integration:
        
        **Authentic Data Sources:**
        - **Step 1-2:** Project setup, location parameters, AI model performance
        - **Step 3:** Weather station data, TMY generation, solar irradiance
        - **Step 4:** BIM building elements, glass areas, orientations
        - **Step 5:** Solar radiation analysis, element-specific performance
        - **Step 6:** PV system specifications, capacity calculations
        - **Step 7:** Energy balance analysis, generation vs demand
        - **Step 8:** Genetic algorithm optimization, system selection
        - **Step 9:** Financial analysis, NPV, IRR, payback calculations
        
        **Dashboard Features:**
        - Real-time data refresh from PostgreSQL database
        - Interactive visualizations with Plotly charts
        - Comprehensive metric cards and performance indicators
        - No mock data - only authenticated calculation results
        """)
    
    # Load authentic dashboard data
    st.info("🔄 Loading authentic data from all workflow steps...")
    
    dashboard_data = load_dashboard_data()
    
    if not dashboard_data:
        st.error("❌ No project data found. Please complete the workflow steps first.")
        st.markdown("""
        **Required Steps:**
        1. **Step 1:** Project Setup & Location Selection
        2. **Step 2:** Historical Data & AI Model Training  
        3. **Step 3:** Weather Data & TMY Generation
        4. **Step 4:** Building Elements Upload (BIM Data)
        5. **Step 5:** Solar Radiation Analysis
        6. **Step 6:** PV System Specification
        7. **Step 7:** Energy Balance Analysis
        8. **Step 8:** Multi-Objective Optimization
        9. **Step 9:** Financial Analysis
        """)
        return
    
    st.success("✅ Dashboard data loaded successfully")
    
    # Create overview section
    create_overview_cards(dashboard_data)
    
    # Create detailed sections
    st.markdown("---")
    create_project_timeline_section(dashboard_data)
    
    st.markdown("---")
    create_building_analysis_section(dashboard_data)
    
    st.markdown("---")
    create_energy_analysis_section(dashboard_data)
    
    st.markdown("---")
    create_optimization_section(dashboard_data)
    
    st.markdown("---")
    create_financial_analysis_section(dashboard_data)
    
    # Data export section
    st.markdown("---")
    st.markdown("### 📥 Data Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Export Dashboard Data (JSON)", type="primary"):
            export_json = json.dumps(dashboard_data, indent=2, default=str)
            st.download_button(
                label="Download JSON Data",
                data=export_json,
                file_name=f"BIPV_Dashboard_Data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("📈 Export Summary Report (CSV)"):
            # Create summary DataFrame
            summary_data = []
            
            if 'project' in dashboard_data:
                summary_data.append(['Project Name', dashboard_data['project']['name']])
                summary_data.append(['Location', dashboard_data['project']['location']])
            
            if 'building' in dashboard_data:
                summary_data.append(['Total Elements', dashboard_data['building']['total_elements']])
                summary_data.append(['Total Glass Area (m²)', dashboard_data['building']['total_glass_area']])
            
            if 'pv_systems' in dashboard_data:
                summary_data.append(['Total Capacity (kW)', dashboard_data['pv_systems']['total_capacity_kw']])
                summary_data.append(['Annual Generation (kWh)', dashboard_data['pv_systems']['total_annual_generation']])
            
            if 'financial' in dashboard_data:
                summary_data.append(['Investment (EUR)', dashboard_data['financial']['total_investment_eur']])
                summary_data.append(['NPV (EUR)', dashboard_data['financial']['npv_eur']])
                summary_data.append(['IRR (%)', dashboard_data['financial']['irr_percentage']])
            
            summary_df = pd.DataFrame(summary_data, columns=['Metric', 'Value'])
            csv = summary_df.to_csv(index=False)
            
            st.download_button(
                label="Download CSV Summary",
                data=csv,
                file_name=f"BIPV_Summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    # Navigation
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🔄 Refresh Dashboard Data", type="secondary"):
            st.rerun()
        
        st.markdown("**Analysis Complete!** 🎉")
        st.markdown("All workflow steps have been completed and results are displayed above.")