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

def get_dashboard_data(project_id):
    """Load all authentic data from database for dashboard display"""
    if not project_id:
        return None
    
    dashboard_data = {}
    
    try:
        conn = db_manager.get_connection()
        if not conn:
            return None
        
        with conn.cursor() as cursor:
            # Project Information (Step 1) with electricity rates
            cursor.execute("""
                SELECT project_name, location, latitude, longitude, timezone, 
                       currency, electricity_rates, created_at
                FROM projects WHERE id = %s
            """, (project_id,))
            project_info = cursor.fetchone()
            
            if project_info:
                # Parse electricity rates from JSON
                electricity_rate = 0.30  # Default fallback
                if project_info[6]:  # electricity_rates JSON
                    try:
                        import json
                        rates_data = json.loads(project_info[6])
                        electricity_rate = float(rates_data.get('import_rate', 0.30))
                    except (json.JSONDecodeError, ValueError, TypeError):
                        electricity_rate = 0.30
                
                dashboard_data['project'] = {
                    'name': project_info[0],
                    'location': project_info[1],
                    'latitude': project_info[2],
                    'longitude': project_info[3],
                    'timezone': project_info[4],
                    'currency': project_info[5],
                    'electricity_rate': electricity_rate,
                    'created_at': project_info[7]
                }
            
            # Historical Data & AI Model (Step 2)
            cursor.execute("""
                SELECT am.model_type, am.r_squared_score, am.training_data_size, am.forecast_years,
                       am.building_area, am.growth_rate, am.peak_demand, am.base_consumption
                FROM ai_models am 
                WHERE am.project_id = %s 
                ORDER BY am.created_at DESC LIMIT 1
            """, (project_id,))
            ai_model = cursor.fetchone()
            
            if ai_model:
                dashboard_data['ai_model'] = {
                    'model_type': ai_model[0],
                    'r2_score': float(ai_model[1]) if ai_model[1] else 0.0,
                    'training_data_points': ai_model[2],
                    'forecast_years': ai_model[3],
                    'building_area': float(ai_model[4]) if ai_model[4] else 0.0,
                    'growth_rate': float(ai_model[5]) if ai_model[5] else 0.0,
                    'peak_demand': float(ai_model[6]) if ai_model[6] else 0.0,
                    'annual_consumption': float(ai_model[7]) if ai_model[7] else 0.0
                }
            
            # Weather Data (Step 3)
            cursor.execute("""
                SELECT temperature, humidity, description, annual_ghi, annual_dni, annual_dhi
                FROM weather_data WHERE project_id = %s ORDER BY created_at DESC LIMIT 1
            """, (project_id,))
            weather_result = cursor.fetchone()
            
            if weather_result:
                temperature = weather_result[0]
                humidity = weather_result[1] 
                dashboard_data['weather'] = {
                    'temperature': float(temperature) if temperature else 0,
                    'humidity': float(humidity) if humidity else 0,
                    'annual_ghi': float(weather_result[3]) if weather_result[3] else 0,
                    'annual_dni': float(weather_result[4]) if weather_result[4] else 0,
                    'annual_dhi': float(weather_result[5]) if weather_result[5] else 0,
                    'total_solar_resource': (float(weather_result[3]) if weather_result[3] else 0) + 
                                          (float(weather_result[4]) if weather_result[4] else 0) + 
                                          (float(weather_result[5]) if weather_result[5] else 0),
                    'data_points': 8760  # Standard TMY hours per year
                }
            
            # Building Elements (Step 4)
            cursor.execute("""
                SELECT COUNT(*) as total_elements,
                       SUM(glass_area) as total_glass_area,
                       COUNT(DISTINCT orientation) as unique_orientations,
                       COUNT(DISTINCT building_level) as building_levels
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
                    'total_glass_area': float(building_stats[1]) if building_stats[1] else 0,
                    'unique_orientations': building_stats[2],
                    'building_levels': building_stats[3],
                    'orientation_distribution': [
                        {'orientation': row[0], 'count': row[1], 'avg_area': float(row[2]) if row[2] else 0}
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
                    'avg_radiation': float(radiation_stats[1]) if radiation_stats[1] else 0,
                    'max_radiation': float(radiation_stats[2]) if radiation_stats[2] else 0,
                    'min_radiation': float(radiation_stats[3]) if radiation_stats[3] else 0,
                    'std_radiation': float(radiation_stats[4]) if radiation_stats[4] else 0,
                    'by_orientation': [
                        {'orientation': row[0], 'avg_radiation': float(row[1]) if row[1] else 0, 'count': row[2]}
                        for row in radiation_by_orientation
                    ]
                }
            
            # PV Specifications (Step 6) - Enhanced with BIPV specifications data
            pv_specs_data = db_manager.get_pv_specifications(project_id)
            if pv_specs_data and 'bipv_specifications' in pv_specs_data:
                bipv_specs = pv_specs_data['bipv_specifications']
                if isinstance(bipv_specs, list) and len(bipv_specs) > 0:
                    total_capacity = sum(float(spec.get('capacity_kw', 0)) for spec in bipv_specs)
                    total_annual_yield = sum(float(spec.get('annual_energy_kwh', 0)) for spec in bipv_specs)
                    total_cost = sum(float(spec.get('total_cost_eur', 0)) for spec in bipv_specs)
                    total_area = sum(float(spec.get('glass_area_m2', 0)) for spec in bipv_specs)
                    
                    dashboard_data['pv_systems'] = {
                        'total_systems': len(bipv_specs),
                        'total_capacity_kw': total_capacity,
                        'total_annual_yield_kwh': total_annual_yield,
                        'total_cost_eur': total_cost,
                        'total_area_m2': total_area,
                        'avg_power_density': (total_capacity / total_area * 1000) if total_area > 0 else 0,  # W/m²
                        'avg_efficiency': sum(float(spec.get('efficiency', 0)) for spec in bipv_specs) / len(bipv_specs),
                        'avg_cost_per_m2': (total_cost / total_area) if total_area > 0 else 0
                    }
                else:
                    # Fallback to database query if BIPV specs not properly structured
                    cursor.execute("""
                        SELECT COUNT(*) as pv_systems,
                               AVG(power_density) as avg_power_density,
                               AVG(efficiency) as avg_efficiency,
                               AVG(cost_per_m2) as avg_cost_per_m2
                        FROM pv_specifications WHERE project_id = %s
                    """, (project_id,))
                    pv_stats = cursor.fetchone()
                    
                    if pv_stats and pv_stats[0] > 0:
                        dashboard_data['pv_systems'] = {
                            'total_systems': pv_stats[0],
                            'avg_power_density': float(pv_stats[1]) if pv_stats[1] else 0,
                            'avg_efficiency': float(pv_stats[2]) if pv_stats[2] else 0,
                            'avg_cost_per_m2': float(pv_stats[3]) if pv_stats[3] else 0
                        }
            
            # Energy Analysis (Step 7)
            cursor.execute("""
                SELECT annual_generation, annual_demand, net_energy_balance,
                       self_consumption_rate, energy_yield_per_m2
                FROM energy_analysis WHERE project_id = %s ORDER BY created_at DESC LIMIT 1
            """, (project_id,))
            energy_result = cursor.fetchone()
            
            if energy_result:
                dashboard_data['energy'] = {
                    'annual_generation': float(energy_result[0]) if energy_result[0] else 0,
                    'annual_demand': float(energy_result[1]) if energy_result[1] else 0,
                    'net_energy_balance': float(energy_result[2]) if energy_result[2] else 0,
                    'self_consumption_rate': float(energy_result[3]) if energy_result[3] else 0,
                    'energy_yield_per_m2': float(energy_result[4]) if energy_result[4] else 0
                }
            
            # Optimization Results (Step 8) - Direct database approach
            optimization_results = db_manager.get_optimization_results(project_id)
            
            if optimization_results and 'solutions' in optimization_results:
                solutions_df = optimization_results['solutions']
                if not solutions_df.empty:
                    # Get top 5 solutions
                    top_5 = solutions_df.head(5)
                    
                    dashboard_data['optimization'] = {
                        'total_solutions': len(solutions_df),
                        'avg_capacity_kw': float(solutions_df['capacity'].mean()),
                        'avg_roi_percentage': float(solutions_df['roi'].mean()),
                        'avg_cost_eur': float(solutions_df['total_cost'].mean()),
                        'min_cost_eur': float(solutions_df['total_cost'].min()),
                        'max_roi_percentage': float(solutions_df['roi'].max()),
                        'top_solutions': [
                            {
                                'solution_id': row['solution_id'],
                                'capacity_kw': float(row['capacity']),
                                'roi_percentage': float(row['roi']),
                                'total_cost_eur': float(row['total_cost']),
                                'net_import_kwh': float(row['net_import']),
                                'rank': row['rank_position']
                            }
                            for _, row in top_5.iterrows()
                        ],
                        'recommended_solution': {
                            'solution_id': top_5.iloc[0]['solution_id'],
                            'capacity_kw': float(top_5.iloc[0]['capacity']),
                            'roi_percentage': float(top_5.iloc[0]['roi']),
                            'total_cost_eur': float(top_5.iloc[0]['total_cost'])
                        } if not top_5.empty else None
                    }
            

            
            # Financial Analysis (Step 9)
            cursor.execute("""
                SELECT initial_investment, npv, irr, payback_period, annual_savings
                FROM financial_analysis WHERE project_id = %s ORDER BY created_at DESC LIMIT 1
            """, (project_id,))
            financial_result = cursor.fetchone()
            
            if financial_result:
                dashboard_data['financial'] = {
                    'total_investment_eur': float(financial_result[0]) if financial_result[0] else 0,  # initial_investment
                    'npv_eur': float(financial_result[1]) if financial_result[1] else 0,              # npv
                    'irr_percentage': float(financial_result[2]) if financial_result[2] else 0,       # irr
                    'payback_period_years': float(financial_result[3]) if financial_result[3] else 0, # payback_period
                    'total_savings_25_years': float(financial_result[4]) * 25 if financial_result[4] else 0  # annual_savings * 25
                }
            
            # Environmental Impact
            cursor.execute("""
                SELECT co2_savings_annual, co2_savings_lifetime
                FROM environmental_impact WHERE project_id = %s ORDER BY created_at DESC LIMIT 1
            """, (project_id,))
            environmental_result = cursor.fetchone()
            
            if environmental_result:
                dashboard_data['environmental'] = {
                    'annual_co2_reduction_kg': float(environmental_result[0]) if environmental_result[0] else 0,  # co2_savings_annual
                    'lifetime_co2_reduction_kg': float(environmental_result[1]) if environmental_result[1] else 0 # co2_savings_lifetime
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
            avg_power = data['pv_systems']['avg_power_density']
            total_systems = data['pv_systems']['total_systems']
            st.metric(
                "PV Power Density",
                f"{avg_power:.1f} W/m²",
                f"{total_systems} systems"
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
            st.write(f"• **25-Year CO₂ Reduction:** {env['lifetime_co2_reduction_kg'] / 1000:,.0f} Tons")

def create_optimization_section(data):
    """Create optimization results section with selected solutions"""
    if not data or 'optimization' not in data:
        st.warning("❌ No optimization results available - Complete Step 8 Multi-Objective Optimization")
        return
    
    st.markdown("### 🎯 Optimization Results (Step 8)")
    
    opt = data['optimization']
    

    
    # Overview metrics with safe key access
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Solutions", opt.get('total_solutions', 0))
    with col2:
        st.metric("Avg Capacity", f"{opt.get('avg_capacity_kw', 0):.1f} kW")
    with col3:
        st.metric("Best ROI", f"{opt.get('max_roi_percentage', 0):.1f}%")
    with col4:
        st.metric("Min Cost", f"€{opt.get('min_cost_eur', 0):,.0f}")
    
    # Recommended solution highlight
    if opt.get('recommended_solution'):
        rec = opt['recommended_solution']
        st.markdown("#### ⭐ **RECOMMENDED SOLUTION**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Solution ID:** {rec['solution_id']}")
            st.markdown(f"**Capacity:** {rec['capacity_kw']:.1f} kW")
            st.markdown(f"**Total Cost:** €{rec['total_cost_eur']:,.0f}")
        
        with col2:
            st.markdown(f"**ROI:** {rec['roi_percentage']:.1f}%")
            
            # ROI indicator
            if rec['roi_percentage'] > 8:
                st.success("✅ Excellent ROI")
            elif rec['roi_percentage'] > 5:
                st.info("✓ Good ROI")
            else:
                st.warning("⚠️ Low ROI")
    
    # Top 5 solutions table
    if opt.get('top_solutions'):
        st.markdown("#### 📊 Top 5 Solutions")
        
        solutions_df = pd.DataFrame(opt['top_solutions'])
        
        # Format the DataFrame for display
        display_df = solutions_df.copy()
        display_df['capacity_kw'] = display_df['capacity_kw'].round(1)
        display_df['roi_percentage'] = display_df['roi_percentage'].round(1)
        display_df['total_cost_eur'] = display_df['total_cost_eur'].apply(lambda x: f"€{x:,.0f}")
        display_df['net_import_kwh'] = display_df['net_import_kwh'].apply(lambda x: f"{x:,.0f}")
        
        # Rename columns for better display
        display_df = display_df.rename(columns={
            'solution_id': 'Solution ID',
            'capacity_kw': 'Capacity (kW)',
            'roi_percentage': 'ROI (%)',
            'total_cost_eur': 'Total Cost',
            'net_import_kwh': 'Net Import (kWh)',
            'rank': 'Rank'
        })
        
        st.dataframe(display_df, use_container_width=True)
        
        # Create ROI vs Cost scatter plot
        fig = px.scatter(
            solutions_df, 
            x='total_cost_eur', 
            y='roi_percentage',
            size='capacity_kw',
            hover_data=['solution_id'],
            title="Optimization Solutions: ROI vs Cost",
            labels={
                'total_cost_eur': 'Total Cost (€)',
                'roi_percentage': 'ROI (%)',
                'capacity_kw': 'Capacity (kW)'
            }
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

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
    
    dashboard_data = get_dashboard_data(get_current_project_id())
    
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
        if st.button("🔄 Refresh Dashboard Data", type="secondary", key="refresh_dashboard"):
            st.rerun()
        
        if st.button("🤖 Continue to Step 11: AI Consultation →", type="primary", key="nav_step11"):
            st.query_params['step'] = 'ai_consultation'
            st.rerun()
        
        st.markdown("**Analysis Complete!** 🎉")
        st.markdown("All workflow steps have been completed and results are displayed above.")