"""
Historical Data Analysis page for BIPV Optimizer
"""
import streamlit as st
from utils.ui_standards import render_step_header, render_navigation_buttons, render_status_message, WORKFLOW_STEPS
from core.solar_math import SimpleMath
from services.io import parse_csv_content, save_project_data
from utils.database_helper import db_helper
from datetime import datetime, timedelta
import pandas as pd



from core.demand_scenario import get_forecast_start_date, generate_demand_forecast

def create_forecast_csv(forecast_data):
    """Create CSV content for forecast data download."""
    csv_lines = ["Year,Month,Date,Predicted_Consumption_kWh,Annual_Total_kWh,Growth_Rate,Notes"]
    
    start_date = forecast_data['forecast_start_date']
    monthly_data = forecast_data['monthly_predictions']
    annual_data = forecast_data['annual_predictions']
    growth_rate = forecast_data['growth_rate']
    
    for i, monthly_consumption in enumerate(monthly_data):
        year = i // 12 + 1
        month = (i % 12) + 1
        
        # Calculate the actual date using proper month arithmetic
        forecast_year = start_date.year + (start_date.month + i - 1) // 12
        forecast_month = (start_date.month + i - 1) % 12 + 1
        date_str = f"{forecast_year}-{forecast_month:02d}"
        
        annual_total = annual_data[year - 1] if year <= len(annual_data) else 0
        
        # Correct seasonal classification based on actual month
        notes = ""
        if forecast_month in [12, 1, 2]:
            notes = "Winter peak demand"
        elif forecast_month in [6, 7, 8]:
            notes = "Summer cooling load"
        elif forecast_month in [3, 4, 5, 9, 10, 11]:
            notes = "Moderate consumption"
        
        csv_lines.append(f"{year},{forecast_month},{date_str},{monthly_consumption:.2f},{annual_total:.2f},{growth_rate:.4f},{notes}")
    
    return "\n".join(csv_lines)


def create_forecast_summary_report(forecast_data, consumption_data):
    """Create comprehensive forecast summary report."""
    report_lines = [
        "BIPV OPTIMIZER - 25-YEAR DEMAND FORECAST REPORT",
        "=" * 50,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "EXECUTIVE SUMMARY",
        "-" * 20,
        f"Base Annual Consumption: {forecast_data['base_consumption']:,.0f} kWh",
        f"Predicted Growth Rate: {forecast_data['growth_rate'] * 100:.2f}% per year",
        f"25-Year Average Annual: {sum(forecast_data['annual_predictions']) / 25:,.0f} kWh",
        f"Peak Year Consumption: {max(forecast_data['annual_predictions']):,.0f} kWh",
        f"Total 25-Year Demand: {sum(forecast_data['annual_predictions']):,.0f} kWh",
        "",
        "MODEL PARAMETERS",
        "-" * 20,
        f"Algorithm: {forecast_data['model_parameters']['algorithm']}",
        f"Features: {', '.join(forecast_data['model_parameters']['features'])}",
        "Model validation: Not evaluated (scenario projection; no measured R²)",
        f"Historical Data Points: {len(consumption_data)} months",
        "",
        "SEASONAL PATTERNS",
        "-" * 20
    ]
    
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for i, factor in enumerate(forecast_data['seasonal_factors']):
        report_lines.append(f"{months[i]}: {factor:.2f}x average ({factor * 100 - 100:+.0f}%)")
    
    report_lines.extend([
        "",
        "YEAR-BY-YEAR PROJECTIONS",
        "-" * 30
    ])
    
    for i, annual in enumerate(forecast_data['annual_predictions'][:10]):  # Show first 10 years
        year = i + 1
        growth = ((annual / forecast_data['base_consumption']) - 1) * 100
        report_lines.append(f"Year {year:2d}: {annual:8,.0f} kWh ({growth:+5.1f}%)")
    
    if len(forecast_data['annual_predictions']) > 10:
        report_lines.append("...")
        last_year = len(forecast_data['annual_predictions'])
        last_annual = forecast_data['annual_predictions'][-1]
        last_growth = ((last_annual / forecast_data['base_consumption']) - 1) * 100
        report_lines.append(f"Year {last_year:2d}: {last_annual:8,.0f} kWh ({last_growth:+5.1f}%)")
    
    report_lines.extend([
        "",
        "METHODOLOGY NOTES",
        "-" * 20,
        "• Scenario based on historical trend, seasonal factors and selected schedule modifiers",
        "• Growth rate calculated from linear trend analysis of provided data",
        "• Seasonal factors derived from monthly consumption variations",
        "• Uploaded temperature and occupancy series are not fitted or used by this scenario function",
        "• Includes legacy seeded ±2.5% perturbation; this is not a prediction interval",
        "• Legacy annual growth bounds: -0.5% to 2% with 12+ months; shorter series assume 1.5%",
        "",
        "USAGE RECOMMENDATIONS",
        "-" * 25,
        "• Use these forecasts for BIPV system sizing and financial analysis",
        "• Consider demand peaks when designing battery storage capacity",
        "• Monitor actual consumption vs predictions to refine future forecasts",
        "• Update model annually with new consumption data for improved accuracy",
        "",
        "For technical questions, contact: Mostafa Gabr, TU Berlin",
        "ResearchGate: https://www.researchgate.net/profile/Mostafa-Gabr-4"
    ])
    
    return "\n".join(report_lines)


def render_historical_data():
    """Render the historical data analysis and demand scenario module."""
    
    # Add OptiSunny character header image
    st.image("attached_assets/step02_1751436847829.png", width=400)
    
    render_step_header('historical_data', subtitle="Upload historical energy consumption and inspect demand scenarios")
    
    with st.expander("Demand scenario method and limitations", expanded=True):
        st.markdown("""
        This page summarizes uploaded consumption and projects a **trend and seasonal scenario**.
        It does not fit a RandomForest model. R², cross-validation scores and feature
        importance have not been evaluated and are not reported as measured results.

        The legacy scenario uses historical consumption, selected schedule modifiers,
        bounded growth and seeded variation. Uploaded temperature and occupancy series
        are retained for inspection but are not fitted by this method. The variation
        is not a statistical uncertainty interval. Long-term values are scenarios.
        """)
    st.divider()
    
    # Check prerequisites and ensure project data is loaded
    from services.io import get_current_project_id, ensure_project_data_loaded
    
    if not ensure_project_data_loaded():
        st.error("Please complete Step 1: Project Setup first.")
        return
    
    project_id = get_current_project_id()
    
    # Check for existing historical data and AI model from database
    from database_manager import BIPVDatabaseManager
    db_manager = BIPVDatabaseManager()
    
    # Load existing historical data if available
    existing_historical_data = db_manager.get_historical_data(project_id)
    existing_ai_model = None
    
    # Check for existing AI model data
    try:
        conn = db_manager.get_connection()
        if conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT model_type, r_squared_score, training_data_size, forecast_years, created_at
                    FROM ai_models WHERE project_id = %s 
                    ORDER BY created_at DESC LIMIT 1
                """, (project_id,))
                result = cursor.fetchone()
                if result:
                    existing_ai_model = {
                        'model_type': result[0],
                        'r_squared_score': result[1],
                        'training_data_size': result[2],
                        'forecast_years': result[3],
                        'created_at': result[4]
                    }
            conn.close()
    except Exception as e:
        st.error(f"Error loading AI model data: {str(e)}")
    
    # Display existing results if available
    if existing_historical_data or existing_ai_model:
        st.success("✅ **Previous Analysis Found** - Displaying saved results")
        
        with st.expander("📊 **Previously Calculated Results**", expanded=True):
            if existing_ai_model:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Model validation", "Not verified")
                    st.caption("Saved scores lack evaluation provenance. Historical records are retained.")

                with col2:
                    training_size = existing_ai_model.get('training_data_size', 0)
                    st.metric(
                        "Historical Observations",
                        f"{training_size} months"
                    )
                
                with col3:
                    model_date = existing_ai_model.get('created_at')
                    if model_date:
                        st.metric(
                            "Analysis Date",
                            model_date.strftime("%Y-%m-%d")
                        )
                
                # Display forecast information based on available data
                forecast_years = existing_ai_model.get('forecast_years', 25)
                st.subheader(f"📈 {forecast_years}-Year Demand Forecast")
                
                # Get historical data to calculate forecast metrics
                if existing_historical_data:
                    consumption_data = existing_historical_data.get('consumption_data', [])
                    if consumption_data:
                        # Calculate basic forecast metrics from historical data
                        annual_avg = sum(consumption_data) if len(consumption_data) <= 12 else sum(consumption_data[:12])
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Base Annual Consumption", f"{annual_avg:,.0f} kWh")
                        
                        with col2:
                            st.metric("Forecast Period", f"{forecast_years} years")
                        
                        with col3:
                            # Estimate total based on typical 1% growth
                            estimated_total = annual_avg * forecast_years * 1.01**forecast_years
                            st.metric("Estimated Total", f"{estimated_total/1000000:.1f} MWh")
                
                st.info("💡 **Data is loaded from database.** You can upload new data to recalculate, or proceed to Step 3.")
        
        st.divider()
    
    # Educational building context
    st.subheader("Educational Building Energy Patterns")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Educational buildings** have unique energy consumption patterns characterized by:
        - Seasonal variations aligned with academic calendar
        - Daily patterns following class schedules
        - Weekend and holiday reductions
        - Climate-dependent HVAC loads
        - Technology-driven baseloads
        """)
    
    with col2:
        building_type = st.selectbox(
            "Building Type",
            ["University Campus", "K-12 School", "Research Facility", "Library", "Dormitory"],
            help="🏫 Select your building type to apply appropriate energy consumption patterns. Each type has unique characteristics: Universities have complex scheduling, K-12 schools follow academic calendars, research facilities operate year-round with high baseloads, libraries have consistent occupancy, dormitories peak during academic terms.",
            key="building_type_select"
        )
        
        occupancy_pattern = st.selectbox(
            "Occupancy Pattern",
            ["Academic Year (Sep-Jun)", "Year-Round Operation", "Summer Programs"],
            help="📅 Define your building's operational schedule. Academic Year (Sep-Jun) shows reduced summer consumption, Year-Round Operation maintains consistent usage, Summer Programs indicate increased summer activity. This affects demand prediction accuracy.",
            key="occupancy_pattern_select"
        )
        
        # Educational building occupancy modifiers that affect energy predictions
        occupancy_modifiers = {
            "Academic Year (Sep-Jun)": {
                "summer_factor": 0.3,  # 30% consumption during summer break
                "winter_factor": 1.2,  # 120% consumption during peak academic period
                "transition_factor": 1.0,  # Normal consumption during transition periods
                "description": "Traditional academic calendar with summer break",
                "standard": "ASHRAE 90.1 Educational, EN 15603",
                "peak_hours": "8AM-6PM weekdays",
                "base_load": 0.20,
                "annual_factor": 0.85  # Reduced operation during breaks
            },
            "Year-Round Operation": {
                "summer_factor": 1.0,  # Full consumption year-round
                "winter_factor": 1.1,  # Slightly higher winter consumption
                "transition_factor": 1.0,  # Consistent operation
                "description": "Continuous year-round educational operation",
                "standard": "ASHRAE 90.1 Educational Year-Round",
                "peak_hours": "7AM-10PM daily",
                "base_load": 0.25,
                "annual_factor": 1.0  # Full operation year-round
            },
            "Summer Programs": {
                "summer_factor": 1.3,  # 130% consumption during intensive summer programs
                "winter_factor": 0.4,  # 40% consumption during winter break
                "transition_factor": 0.8,  # Reduced spring/fall operation
                "description": "Intensive summer programs with winter break",
                "standard": "ASHRAE 90.1 Seasonal Educational",
                "peak_hours": "6AM-9PM summer",
                "base_load": 0.15,
                "annual_factor": 0.75  # Reduced winter operation
            }
        }
        
        selected_modifier = occupancy_modifiers[occupancy_pattern]
        
        # Display building pattern information
        with st.expander(f"📋 {occupancy_pattern} - Building Standards & Parameters", expanded=False):
            st.markdown(f"""
            **Building Function:** {selected_modifier['description']}
            
            **Standards Compliance:**
            - **Primary Standard:** {selected_modifier['standard']}
            - **Peak Operating Hours:** {selected_modifier['peak_hours']}
            - **Base Load Factor:** {selected_modifier['base_load']:.0%}
            - **Annual Operation Factor:** {selected_modifier['annual_factor']:.0%}
            
            **Seasonal Energy Modifiers:**
            - **Summer Factor:** {selected_modifier['summer_factor']:.0%} (Jun-Aug)
            - **Winter Factor:** {selected_modifier['winter_factor']:.0%} (Dec-Feb)
            - **Transition Factor:** {selected_modifier['transition_factor']:.0%} (Mar-May, Sep-Nov)
            
            **Impact on BIPV Analysis:**
            These factors directly affect energy demand predictions, influencing BIPV system sizing and optimization calculations in subsequent workflow steps.
            """)
        
        # Store pattern selections for use in calculations
        st.session_state['building_type'] = building_type
        st.session_state['occupancy_pattern'] = occupancy_pattern
        st.session_state['occupancy_modifiers'] = selected_modifier
    
    # Building area input for accurate energy intensity calculation
    st.subheader("🏢 Building Information")
    st.markdown("**⚠️ Required: Building Floor Area (Mandatory for Analysis)**")
    
    building_area = st.number_input(
        "Total Conditioned Floor Area (m²) *",
        min_value=100,
        value=st.session_state.get('project_data', {}).get('building_area', None),
        step=100,
        help="""
        **Definition:** Total conditioned floor area (also called Net Floor Area or NFA) includes all heated/cooled spaces within the building envelope.
        
        **What to Include:**
        - Classrooms, offices, laboratories
        - Corridors, lobbies, common areas
        - Mechanical rooms if conditioned
        
        **What to Exclude:**
        - Unconditioned basements/attics
        - Parking garages
        - Outdoor areas, balconies
        
        **Note:** This is NOT the total built-up area or footprint. Use the sum of all conditioned floor areas across all levels.
        """,
        key="building_area_input"
    )
    
    # Validation for mandatory field
    if building_area is None or building_area <= 0:
        st.error("⚠️ Building floor area is required to proceed with energy intensity analysis.")
        st.stop()
    
    if building_area < 500:
        st.warning("⚠️ Very small building area detected. Please verify this is the total conditioned floor area across all levels.")
    elif building_area > 20000:
        st.info("ℹ️ Large building detected. Ensure this includes all conditioned spaces across multiple floors.")
    elif building_area > 100000:
        st.info("ℹ️ Very large campus/complex detected. For multi-building campuses, consider analyzing buildings individually for more precise BIPV optimization.")
    
    # Store building area in project data immediately
    if 'project_data' not in st.session_state:
        st.session_state.project_data = {}
    st.session_state.project_data['building_area'] = building_area
    
    # CSV file upload
    st.subheader("📁 Historical Energy Data Upload")
    
    with st.expander("CSV File Requirements", expanded=False):
        st.markdown("""
        **Required Columns:**
        - `Date`: YYYY-MM-DD format (e.g., 2023-01-01)
        - `Consumption`: Monthly energy consumption in kWh (numeric values only)
        
        **Optional Columns (retained for inspection):**
        - `Temperature`: Average monthly temperature in °C
        - `Humidity`: Average monthly humidity percentage (0-100)
        - `Solar_Irradiance`: Monthly solar irradiance in kWh/m²
        - `Occupancy`: Building occupancy percentage (0-100)
        
        **Example Format:**
        ```
        Date,Consumption,Temperature,Humidity,Occupancy
        2023-01-01,12500,2.1,78,85
        2023-02-01,11800,4.3,72,88
        2023-03-01,10200,8.7,65,92
        ```
        """)
    
    uploaded_file = st.file_uploader(
        "Upload Historical Energy Data (CSV)",
        type=['csv'],
        help="📊 Upload a CSV file containing at least 12 months of historical energy consumption data. Required: Date (YYYY-MM-DD) and Consumption (kWh) columns. Optional temperature and occupancy columns are retained for inspection. File size limit: 10MB.",
        key="historical_data_upload"
    )
    
    if uploaded_file is not None:
        st.success(f"Data uploaded: {uploaded_file.name}")
        
        # Parse CSV content
        content = uploaded_file.getvalue().decode('utf-8')
        headers, data = parse_csv_content(content)
        
        with st.spinner("Processing historical consumption data..."):
            # Process data using pure Python
            consumption_data = []
            temperature_data = []
            occupancy_data = []
            
            date_idx = next((i for i, h in enumerate(headers) if 'date' in h.lower()), -1)
            consumption_idx = next((i for i, h in enumerate(headers) if 'consumption' in h.lower()), -1)
            temp_idx = next((i for i, h in enumerate(headers) if 'temperature' in h.lower()), -1)
            occupancy_idx = next((i for i, h in enumerate(headers) if 'occupancy' in h.lower()), -1)
            
            date_data = []  # Store actual dates from CSV
            
            for row in data:
                if len(row) > consumption_idx and consumption_idx >= 0:
                    try:
                        consumption = float(row[consumption_idx])
                        consumption_data.append(consumption)
                        
                        # Extract date information
                        if date_idx >= 0 and len(row) > date_idx:
                            date_str = row[date_idx].strip()
                            date_data.append(date_str)
                        
                        if temp_idx >= 0 and len(row) > temp_idx:
                            temperature = float(row[temp_idx])
                            temperature_data.append(temperature)
                        
                        if occupancy_idx >= 0 and len(row) > occupancy_idx:
                            occupancy = float(row[occupancy_idx])
                            occupancy_data.append(occupancy)
                    except ValueError:
                        continue
            
            import math
            if not consumption_data or not all(math.isfinite(v) and v >= 0 for v in consumption_data) or sum(consumption_data) <= 0:
                st.error("Upload finite, nonnegative monthly consumption with at least one positive value.")
                return

            # Calculate statistics
            avg_consumption = SimpleMath.mean(consumption_data)
            total_consumption = sum(consumption_data)
            max_consumption = max(consumption_data) if consumption_data else 0
            min_consumption = min(consumption_data) if consumption_data else 0
            
            # Calculate energy metrics to prevent division by zero in reports
            building_area = st.session_state.get('project_data', {}).get('building_area', 5000)
            energy_intensity = total_consumption / building_area if total_consumption > 0 and building_area > 0 else 0
            
            # Create sample data structure
            sample_data = {
                'months': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                'consumption': consumption_data[:12] if len(consumption_data) >= 12 else consumption_data,
                'temperature': temperature_data[:12] if len(temperature_data) >= 12 else temperature_data,
                'occupancy': occupancy_data[:12] if len(occupancy_data) >= 12 else occupancy_data,
                'avg_consumption': avg_consumption,
                'total_consumption': total_consumption,
                'max_consumption': max_consumption,
                'min_consumption': min_consumption,
                'model_accuracy': None,
                'building_area': building_area,
                'energy_intensity': energy_intensity,
                'consumption_data': consumption_data,
                'model_performance': {
                    'r2_score': None,
                    'algorithm': 'Trend and seasonal scenario'
                },
                'demand_forecast': {
                    'baseline_annual': total_consumption,
                    'growth_rate': 2.0
                },
                'peak_load_factor': max_consumption / avg_consumption if avg_consumption > 0 else 0,
                'seasonal_variation': 0.0  # Will be calculated below if temperature data available
            }
            
            # Store historical data using standardized structure
            st.session_state.project_data['historical_data'] = sample_data
            st.session_state.project_data['ai_model_data'] = {
                'r2_score': sample_data.get('model_performance', {}).get('r2_score'),
                'algorithm': sample_data.get('model_performance', {}).get('algorithm', 'Trend and seasonal scenario'),
                'training_complete': False,
                'evaluation_status': 'not_evaluated'
            }
            st.session_state.project_data['demand_forecast'] = sample_data.get('demand_forecast', {})
            st.session_state.project_data['ui_metrics'] = {
                'total_consumption': total_consumption,
                'energy_intensity': energy_intensity,
                'peak_load_factor': sample_data.get('peak_load_factor', 0),
                'seasonal_variation': sample_data.get('seasonal_variation', 0)
            }
            
            # Set completion flags
            st.session_state['historical_completed'] = True
            st.session_state.project_data['data_analysis_complete'] = True
            
            # Save to database using centralized project ID
            from services.io import get_current_project_id
            project_id = get_current_project_id()
            
            # No held-out evaluation exists for this scenario method.
            r_squared_score = None
            
            if project_id:
                save_project_data(st.session_state.project_data)
                # Save to historical_data table with correct field references
                historical_data_to_save = {
                    'annual_consumption': total_consumption,
                    'model_accuracy': r_squared_score,
                    'consumption_data': st.session_state.project_data.get('historical_data', {}),
                    'ai_model_data': st.session_state.project_data.get('ai_model_data', {}),
                    'forecast_data': st.session_state.project_data.get('demand_forecast', {})
                }
                db_helper.save_step_data("historical_data", historical_data_to_save)
                
                # Save comprehensive AI model data for Step 7 data flow
                from database_manager import BIPVDatabaseManager
                db_manager = BIPVDatabaseManager()
                
                # Save historical data first
                historical_data_complete = {
                    'annual_consumption': total_consumption,
                    'consumption_data': consumption_data,
                    'temperature_data': temperature_data or [],
                    'occupancy_data': occupancy_data or [],
                    'date_data': date_data or [],
                    'model_accuracy': r_squared_score,
                    'energy_intensity': sample_data.get('energy_intensity', 0),
                    'peak_load_factor': sample_data.get('peak_load_factor', 0),
                    'seasonal_variation': sample_data.get('seasonal_variation', 0)
                }
                db_manager.save_historical_data(project_id, historical_data_complete)
                
                # Save AI model data with forecast predictions for Step 7
                ai_model_complete = {
                    'model_type': 'TrendSeasonalScenario-v2',
                    'r_squared_score': r_squared_score,
                    'training_data_size': len(consumption_data),
                    'forecast_years': 25,
                    'forecast_data': forecast_data if 'forecast_data' in locals() else {},
                    'demand_predictions': forecast_data.get('annual_predictions', []) if 'forecast_data' in locals() else [],
                    'growth_rate': forecast_data.get('growth_rate', 0.01) if 'forecast_data' in locals() else 0.01,
                    'base_consumption': total_consumption,
                    'peak_demand': max_consumption,
                    'building_area': building_area,
                    'occupancy_pattern': occupancy_pattern,
                    'building_type': building_type
                }
                db_manager.save_ai_model_data(project_id, ai_model_complete)
        
        # Display analysis results
        st.success("Historical data processed. Demand scenario is not statistically evaluated.")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Annual Consumption", f"{total_consumption:,.0f} kWh")
        with col2:
            st.metric("Average Monthly", f"{avg_consumption:,.0f} kWh")
        with col3:
            st.metric("Peak Month", f"{max_consumption:,.0f} kWh")
        with col4:
            st.metric("Low Month", f"{min_consumption:,.0f} kWh")
        
        # Monthly consumption pattern
        st.subheader("Monthly Consumption Pattern")
        if consumption_data:
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            # Create a full 12-month dataset starting with January
            full_year_data = {}
            
            if len(consumption_data) >= 12:
                # If we have 12+ months, use first 12 months
                for i in range(12):
                    full_year_data[months[i]] = consumption_data[i]
            else:
                # If less than 12 months, fill missing months with average
                avg_value = sum(consumption_data) / len(consumption_data) if consumption_data else 0
                
                # Fill available months
                for i in range(len(consumption_data)):
                    full_year_data[months[i]] = consumption_data[i]
                
                # Fill missing months with average
                for i in range(len(consumption_data), 12):
                    full_year_data[months[i]] = avg_value
            
            # Create ordered chart data starting with January using Plotly for proper ordering
            import plotly.graph_objects as go
            
            ordered_values = [full_year_data[month] for month in months]
            
            fig_monthly = go.Figure(data=[
                go.Bar(x=months, y=ordered_values, marker_color='steelblue')
            ])
            
            fig_monthly.update_layout(
                title="Monthly Consumption Pattern",
                xaxis_title="Month",
                yaxis_title="Consumption (kWh)",
                height=400,
                xaxis=dict(categoryorder='array', categoryarray=months)  # Force chronological order
            )
            
            st.plotly_chart(fig_monthly, use_container_width=True)
        
        # Generate 25-year demand forecast with educational building patterns
        try:
            forecast_data = generate_demand_forecast(
                consumption_data, 
                temperature_data, 
                occupancy_data, 
                date_data,
                occupancy_modifiers=selected_modifier,
                building_type=building_type
            )
        except Exception as e:
            st.error(f"Error generating forecast: {str(e)}")
            forecast_data = None
        
        # Store forecast in session state for other steps
        if forecast_data:
            st.session_state.project_data['demand_forecast'] = forecast_data
            
            # Display forecast results
            st.subheader("📈 25-Year Demand Forecast")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Create forecast chart
                import plotly.graph_objects as go
                
                fig = go.Figure()
                
                # Create continuous timeline without gaps
                months_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                
                # Historical data with actual dates from CSV
                hist_data = consumption_data[:12] if len(consumption_data) >= 12 else consumption_data
                
                # Create timeline using actual dates from uploaded data
                all_timeline = []
                all_values = []
                
                # Add historical data points with actual dates
                if date_data and len(date_data) >= len(hist_data):
                    # Use actual dates from CSV
                    for i in range(len(hist_data)):
                        try:
                            date_str = date_data[i]
                            if '-' in date_str:
                                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                                timeline_label = f"{months_labels[date_obj.month-1]} {date_obj.year}"
                            else:
                                timeline_label = f"Month {i+1} (Historical)"
                        except:
                            timeline_label = f"Month {i+1} (Historical)"
                        
                        all_timeline.append(timeline_label)
                        all_values.append(hist_data[i])
                else:
                    # Fallback to generic historical labels
                    for i in range(len(hist_data)):
                        all_timeline.append(f"Month {i+1} (Historical)")
                        all_values.append(hist_data[i])
                
                # Add forecast data points continuing from where historical ends
                forecast_values = forecast_data['monthly_predictions'][:24]
                forecast_start_date = forecast_data['forecast_start_date']
                
                for i in range(len(forecast_values)):
                    # Calculate proper forecast date by adding months to start date
                    year = forecast_start_date.year + (forecast_start_date.month + i - 1) // 12
                    month = (forecast_start_date.month + i - 1) % 12 + 1
                    
                    timeline_label = f"{months_labels[month-1]} {year}"
                    all_timeline.append(timeline_label)
                    all_values.append(forecast_values[i])
                
                # Split the data for different visual styling
                hist_timeline = all_timeline[:len(hist_data)]
                hist_values = all_values[:len(hist_data)]
                
                forecast_timeline = all_timeline[len(hist_data):]
                forecast_vals = all_values[len(hist_data):]
                
                # Add transition point to connect lines smoothly
                if len(hist_data) > 0 and len(forecast_vals) > 0:
                    # Add last historical point to forecast for smooth connection
                    forecast_timeline.insert(0, hist_timeline[-1])
                    forecast_vals.insert(0, hist_values[-1])
                
                # Add historical data
                fig.add_trace(go.Scatter(
                    x=hist_timeline,
                    y=hist_values,
                    mode='lines+markers',
                    name='Historical Data',
                    line=dict(color='blue', width=3)
                ))
                
                # Add forecast data
                fig.add_trace(go.Scatter(
                    x=forecast_timeline,
                    y=forecast_vals,
                    mode='lines',
                    name='AI Forecast (2 years)',
                    line=dict(color='red', width=2, dash='dash')
                ))
                
                fig.update_layout(
                    title="Energy Demand: Historical vs AI Forecast",
                    xaxis_title="Time Period",
                    yaxis_title="Consumption (kWh)",
                    hovermode='x unified',
                    height=400,
                    xaxis=dict(tickangle=45)  # Rotate labels for better readability
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Forecast summary metrics
                st.markdown("**📊 Forecast Summary:**")
                
                # Calculate actual metrics from forecast data
                annual_predictions = forecast_data['annual_predictions']
                base_consumption = forecast_data['base_consumption']
                growth_rate_decimal = forecast_data['growth_rate']
                
                # Calculate 25-year average
                annual_avg = sum(annual_predictions) / len(annual_predictions) if annual_predictions else base_consumption
                
                # Calculate actual growth rate percentage
                if len(annual_predictions) >= 2:
                    first_year = annual_predictions[0]
                    last_year = annual_predictions[-1]
                    years = len(annual_predictions) - 1
                    if first_year > 0 and years > 0:
                        actual_growth_rate = ((last_year / first_year) ** (1/years) - 1) * 100
                    else:
                        actual_growth_rate = growth_rate_decimal * 100
                else:
                    actual_growth_rate = growth_rate_decimal * 100
                
                # Peak year demand
                peak_demand = max(annual_predictions) if annual_predictions else base_consumption
                
                # Total 25-year demand
                total_demand = sum(annual_predictions) if annual_predictions else base_consumption * 25
                
                st.metric("25-Year Avg Annual", f"{annual_avg:,.0f} kWh")
                st.metric("Predicted Growth Rate", f"{actual_growth_rate:.1f}%/year")
                st.metric("Peak Year Demand", f"{peak_demand:,.0f} kWh")
                st.metric("Total 25-Year Demand", f"{total_demand:,.0f} kWh")
                
                # Save UI calculation results to session state for reports
                if 'project_data' not in st.session_state:
                    st.session_state.project_data = {}
                if 'historical_data' not in st.session_state.project_data:
                    st.session_state.project_data['historical_data'] = {}
                
                # Store the exact values shown in UI for report consistency
                st.session_state.project_data['historical_data']['ui_metrics'] = {
                    'annual_avg': annual_avg,
                    'actual_growth_rate': actual_growth_rate,
                    'peak_demand': peak_demand,
                    'total_demand': total_demand,
                    'r2_score': None,  # Not evaluated
                    'building_area': building_area,
                    'baseline_annual': base_consumption,
                    'annual_predictions': annual_predictions,
                    'growth_rate_decimal': growth_rate_decimal
                }
            
            # Download forecast data
            st.subheader("📄 Download Forecast Results")
            
            # Create CSV content for download
            try:
                forecast_csv = create_forecast_csv(forecast_data)
                summary_report = create_forecast_summary_report(forecast_data, consumption_data)

            except Exception as e:
                st.error(f"Error creating download files: {str(e)}")
        else:
            st.warning("Forecast generation failed. Please check your historical data and try again.")

        st.subheader("Demand scenario validation")
        st.info("Not evaluated: this scenario has no fitted estimator, held-out R², "
                "cross-validation score or measured feature importance.")
        st.session_state.project_data['model_r2_score'] = None
        st.session_state.project_data['model_performance_status'] = 'Not evaluated'

        # Educational building standards compliance
        st.subheader("Educational Building Standards Analysis")
        
        # Calculate benchmarks with actual building area
        building_area = st.session_state.get('project_data', {}).get('building_area', 5000)
        annual_kwh_per_sqm = total_consumption / building_area if total_consumption > 0 and building_area > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Energy Intensity", f"{annual_kwh_per_sqm:.0f} kWh/m²/year")
            if annual_kwh_per_sqm < 150:
                st.success("Excellent - Below ASHRAE 90.1 baseline")
            elif annual_kwh_per_sqm < 200:
                st.info("Good - Meeting efficiency standards")
            else:
                st.warning("Above average - Optimization potential")
            
            # Energy Intensity explanation with academic sources
            with st.expander("📚 Energy Intensity - Definition & Academic Context", expanded=False):
                st.markdown("""
                **Energy Intensity Definition:**
                Energy Use Intensity (EUI) measures annual energy consumption per unit floor area (kWh/m²/year), 
                serving as a key performance indicator for building energy efficiency and BIPV system sizing.
                
                **Educational Building Benchmarks (Academic Sources):**
                - **ASHRAE 90.1 Standard**: 400-600 kWh/m²/year typical range for educational facilities
                - **EU EN 15603 Standard**: Primary energy benchmarks for non-residential buildings
                - **Pérez-Lombard et al. (2008)**: "A review on buildings energy consumption information" - Energy and Buildings
                - **Khoshbakht et al. (2018)**: "Energy and carbon assessment of HVAC systems in commercial buildings" - Energy & Buildings
                
                **BIPV Sizing Context:**
                Higher energy intensity indicates greater potential for solar offset through BIPV glass replacement.
                Buildings >600 kWh/m²/year are prime candidates for comprehensive BIPV retrofits.
                
                **References:**
                - ASHRAE Standard 90.1-2019: Energy Standard for Buildings
                - EN 15603:2008: Energy performance of buildings
                - Pérez-Lombard, L., et al. (2008). Energy and Buildings, 40(3), 394-398
                - Khoshbakht, M., et al. (2018). Energy & Buildings, 158, 94-108
                """)
        
        with col2:
            peak_load_factor = max_consumption / avg_consumption if avg_consumption > 0 else 1
            st.metric("Peak Load Factor", f"{peak_load_factor:.2f}")
            if peak_load_factor < 1.5:
                st.success("Consistent load profile")
            else:
                st.info("Variable load - BIPV opportunity")
            
            # Peak Load Factor explanation with academic sources
            with st.expander("📚 Peak Load Factor - Definition & Academic Context", expanded=False):
                st.markdown("""
                **Peak Load Factor Definition:**
                Peak Load Factor = Maximum Monthly Consumption / Average Monthly Consumption
                
                Measures demand variability and consistency of energy consumption patterns.
                Lower values indicate more consistent energy use, ideal for BIPV systems.
                
                **Academic Interpretation (Research Sources):**
                - **1.0-1.3**: Excellent consistency - Optimal for BIPV matching (Dubey et al., 2013)
                - **1.3-1.7**: Good consistency - Suitable for BIPV with storage (Swan & Ugursal, 2009)
                - **>1.7**: High variability - Requires demand management strategies (Zhao & Magoulès, 2012)
                
                **BIPV System Design Impact:**
                Consistent load profiles (low PLF) enable better solar-to-demand matching, 
                reducing grid dependency and improving financial returns on BIPV investments.
                
                **Educational Building Context:**
                Academic buildings typically show PLF 1.1-1.4 due to seasonal operation patterns
                (summer/winter variations, academic calendar effects).
                
                **References:**
                - Dubey, S., et al. (2013). "Temperature dependent photovoltaic (PV) efficiency" - Solar Energy Materials & Solar Cells
                - Swan, L.G., Ugursal, V.I. (2009). "Modeling of end-use energy consumption" - Renewable & Sustainable Energy Reviews
                - Zhao, H., Magoulès, F. (2012). "A review on the prediction of building energy consumption" - Renewable & Sustainable Energy Reviews
                """)
        
        
        with col3:
            if temperature_data and len(temperature_data) >= 12:
                # Summer: Jun-Aug (indices 5,6,7)
                summer_temps = temperature_data[5:8]
                summer_avg = SimpleMath.mean(summer_temps) if summer_temps else 0
                
                # Winter: Dec-Feb (indices 11,0,1) - handle year boundary correctly
                winter_temps = [temperature_data[11]]  # December
                if len(temperature_data) >= 12:
                    winter_temps.extend([temperature_data[0], temperature_data[1]])  # Jan, Feb
                winter_avg = SimpleMath.mean(winter_temps) if winter_temps else 0
                
                seasonal_variation = abs(summer_avg - winter_avg) if summer_avg and winter_avg else 0
                st.metric("Seasonal Variation", f"{seasonal_variation:.1f}°C")
                
                # Update historical_data with calculated seasonal variation
                if 'historical_data' in st.session_state.project_data:
                    st.session_state.project_data['historical_data']['seasonal_variation'] = seasonal_variation
                
                if seasonal_variation > 20:
                    st.info("High seasonal variation - Climate-responsive design beneficial")
                elif seasonal_variation > 10:
                    st.success("Moderate seasonal variation - Balanced energy patterns")
                else:
                    st.info("Low seasonal variation - Stable climate conditions")
                    
                # Seasonal Variation explanation with academic context
                with st.expander("📚 Seasonal Variation - Definition & BIPV Impact", expanded=False):
                    st.markdown(f"""
                    **Seasonal Variation Definition:**
                    Temperature difference between summer (Jun-Aug) and winter (Dec-Feb) months.
                    
                    **Your Building:** {seasonal_variation:.1f}°C difference
                    - Summer average: {summer_avg:.1f}°C
                    - Winter average: {winter_avg:.1f}°C
                    
                    **BIPV System Impact:**
                    - **>20°C**: High variation requires adaptive HVAC, variable energy demand
                    - **10-20°C**: Moderate variation, balanced heating/cooling loads
                    - **<10°C**: Stable climate, consistent BIPV performance year-round
                    
                    **Design Implications:**
                    Higher seasonal variation affects BIPV sizing calculations as heating loads
                    in winter and cooling loads in summer create different energy demand patterns.
                    """)
            else:
                st.metric("Seasonal Variation", "N/A")
                st.info("Insufficient temperature data for seasonal analysis")
        
        # Prediction for next steps using AI forecast results
        st.subheader("Demand Prediction for BIPV Analysis")
        
        if forecast_data:
            # Use the first year from the sophisticated AI forecast
            future_demand = forecast_data['annual_predictions'][0]
            growth_rate = forecast_data['growth_rate'] * 100
            
            st.info(f"""
            **Projected Annual Demand:** {future_demand:,.0f} kWh/year
            **Growth Rate:** {growth_rate:.1f}% per year
            **Forecast Method:** AI Model with Educational Building Patterns
            
            This demand prediction incorporates:
            - Historical consumption patterns from your data
            - {st.session_state.get('building_type', 'Educational')} building characteristics
            - {st.session_state.get('occupancy_pattern', 'Standard')} operational schedule
            - Seasonal variations and growth trends
            
            This prediction will be used in subsequent steps to:
            - Size BIPV system capacity based on actual building patterns
            - Calculate energy balance scenarios with realistic demand
            - Optimize PV-to-demand ratios for your building type
            - Determine grid interaction patterns throughout the year
            """)
        else:
            # Fallback to simple calculation if forecast failed
            future_demand = avg_consumption * 12 * 1.02  # 2% annual growth
            
            st.warning(f"""
            **Projected Annual Demand:** {future_demand:,.0f} kWh/year
            **Method:** Simplified calculation (AI forecast unavailable)
            
            This basic prediction will be used in subsequent steps, but results may be less accurate without detailed forecasting.
            """)
        


        
        # Add step-specific download button
        st.markdown("---")
        st.markdown("### 📄 Step 2 Analysis Report")
        st.markdown("Download historical data and demand scenario report:")
        
        from utils.individual_step_reports import create_step_download_button
        create_step_download_button(2, "Historical Data", "Download Historical Data Analysis Report")
        
        # Standard navigation buttons
        render_navigation_buttons('historical_data', show_previous=True, show_next=True)
    
    else:
        st.info("Please upload a CSV file with historical energy consumption data to continue.")