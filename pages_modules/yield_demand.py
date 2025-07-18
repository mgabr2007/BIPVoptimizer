"""
Yield vs Demand Analysis page for BIPV Optimizer
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime as dt, timedelta
import pickle
from database_manager import db_manager
from utils.database_helper import db_helper
from core.solar_math import safe_divide
from utils.consolidated_data_manager import ConsolidatedDataManager
from utils.session_state_standardizer import BIPVSessionStateManager

def safe_float(value, default=0.0):
    """Safely convert value to float."""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def load_demand_model():
    """Load the trained demand prediction model from session state."""
    try:
        model_data = st.session_state.project_data.get('demand_model')
        if model_data:
            # If model_data is already a dict, return it directly
            if isinstance(model_data, dict):
                return model_data.get('model'), model_data.get('feature_columns'), model_data.get('metrics')
            # Otherwise try to deserialize
            model_dict = pickle.loads(model_data)
            return model_dict['model'], model_dict['feature_columns'], model_dict['metrics']
        return None, None, None
    except Exception as e:
        st.error(f"Error loading demand model: {str(e)}")
        return None, None, None

def predict_future_demand(model, feature_columns, start_date, end_date):
    """Predict energy demand for a future period."""
    
    # Generate monthly date range
    dates = pd.date_range(start_date, end_date, freq='MS')  # Monthly start
    
    # Create feature matrix
    features_df = pd.DataFrame({
        'Month': dates.to_series().dt.month.values,
        'Quarter': dates.to_series().dt.quarter.values,
        'DayOfYear': dates.to_series().dt.dayofyear.values
    })
    
    # Add seasonal temperature simulation based on month
    features_df['Temperature'] = 15 + 10 * np.sin(2 * np.pi * (features_df['Month'] - 3) / 12)
    features_df['Humidity'] = 60 + 20 * np.sin(2 * np.pi * (features_df['Month'] - 6) / 12)
    features_df['Solar_Irradiance'] = 500 + 300 * np.sin(2 * np.pi * (features_df['Month'] - 3) / 12)
    
    # Add any missing features from training
    for feature in feature_columns:
        if feature not in features_df.columns:
            if 'occupancy' in feature.lower():
                # Educational building occupancy pattern
                features_df[feature] = np.where(features_df['Month'].isin([7, 8]), 0.3, 0.85)  # Summer break
            else:
                features_df[feature] = 0  # Default value
    
    # Ensure feature order matches training
    X = features_df[feature_columns]
    
    # Predict demand
    predictions = model.predict(X)
    
    # Create result dataframe
    demand_df = pd.DataFrame({
        'date': dates,
        'predicted_demand': predictions,
        'month': dates.to_series().dt.month.values,
        'year': dates.to_series().dt.year.values
    })
    
    return demand_df

def calculate_pv_yield_profiles(pv_specs, radiation_data, tmy_data, environmental_factors=None):
    """Calculate monthly PV yield profiles for each system using actual TMY data with environmental shading."""
    
    if pv_specs is None or len(pv_specs) == 0:
        return pd.DataFrame()
    
    yield_profiles = []
    
    # Get environmental shading factor from Step 3
    # NOTE: If TMY data was regenerated with environmental factors, this should be 0
    shading_reduction = 0
    if environmental_factors:
        shading_reduction = environmental_factors.get('shading_reduction', 0)
    
    # Apply shading reduction factor (1 - percentage reduction)
    # This will be 1.0 (no additional reduction) if TMY data was already adjusted
    shading_factor = 1 - (shading_reduction / 100)
    
    # Create monthly irradiation profiles from TMY data
    monthly_irradiation_profile = {}
    if tmy_data and len(tmy_data) > 0:
        # Calculate monthly totals from hourly TMY data
        for month in range(1, 13):
            month_total = 0
            hours_in_month = 0
            
            for hour_data in tmy_data:
                # Parse datetime if it's in string format
                if isinstance(hour_data, dict):
                    # Try to extract day from datetime string or day field
                    datetime_str = hour_data.get('datetime', hour_data.get('DateTime', ''))
                    if datetime_str:
                        try:
                            dt_parsed = dt.strptime(datetime_str.split()[0], '%Y-%m-%d')
                            day = dt_parsed.timetuple().tm_yday  # Day of year
                        except:
                            day = hour_data.get('day', hour_data.get('Day', 1))
                    else:
                        day = hour_data.get('day', hour_data.get('Day', 1))
                if day <= 31:
                    hour_month = 1
                elif day <= 59:
                    hour_month = 2
                elif day <= 90:
                    hour_month = 3
                elif day <= 120:
                    hour_month = 4
                elif day <= 151:
                    hour_month = 5
                elif day <= 181:
                    hour_month = 6
                elif day <= 212:
                    hour_month = 7
                elif day <= 243:
                    hour_month = 8
                elif day <= 273:
                    hour_month = 9
                elif day <= 304:
                    hour_month = 10
                elif day <= 334:
                    hour_month = 11
                else:
                    hour_month = 12
                
                if hour_month == month:
                    # Handle different GHI field names from TMY data
                    # NOTE: If TMY was regenerated, environmental shading is already applied
                    ghi_value = hour_data.get('ghi', hour_data.get('GHI_Wm2', hour_data.get('GHI', 0)))
                    
                    # Only apply additional shading if TMY wasn't already adjusted
                    if shading_factor < 1.0:
                        adjusted_ghi = ghi_value * shading_factor
                    else:
                        adjusted_ghi = ghi_value  # Use TMY data as-is (already environmentally adjusted)
                    
                    month_total += adjusted_ghi / 1000  # Convert Wh/m² to kWh/m²
                    hours_in_month += 1
            
            monthly_irradiation_profile[month] = month_total
    else:
        # No TMY data available - cannot calculate authentic yields
        st.error("❌ No TMY data available - authentic radiation calculations require TMY data from Step 3")
        return pd.DataFrame()  # Return empty DataFrame
    
    # Calculate yield for each PV system
    for _, system in pv_specs.iterrows():
        element_id = system['element_id']
        annual_yield = system.get('annual_energy_kwh', 0)
        
        # Apply environmental shading to annual yield
        adjusted_annual_yield = annual_yield * shading_factor
        
        # Get element-specific radiation data if available
        element_radiation = None
        if radiation_data is not None and len(radiation_data) > 0:
            element_matches = radiation_data[radiation_data['element_id'] == element_id]
            if len(element_matches) > 0:
                element_radiation = element_matches.iloc[0]
        
        for month in range(1, 13):
            # Use element-specific monthly irradiation if available
            if element_radiation is not None:
                monthly_irradiation_data = element_radiation.get('monthly_irradiation', {})
                if isinstance(monthly_irradiation_data, dict):
                    month_irradiation = monthly_irradiation_data.get(str(month), 
                                                                  monthly_irradiation_data.get(month, 
                                                                  monthly_irradiation_profile[month]))
                else:
                    month_irradiation = monthly_irradiation_profile[month]
            else:
                month_irradiation = monthly_irradiation_profile[month]
            
            # Calculate monthly yield based on irradiation
            # Use ratio of monthly to annual irradiation to distribute annual yield
            annual_irradiation = sum(monthly_irradiation_profile.values())
            if annual_irradiation > 0:
                monthly_yield = adjusted_annual_yield * (month_irradiation / annual_irradiation)
            else:
                # Fallback to seasonal distribution
                monthly_distribution = [0.03, 0.05, 0.08, 0.11, 0.14, 0.15, 0.14, 0.12, 0.09, 0.06, 0.03, 0.02]
                monthly_yield = adjusted_annual_yield * monthly_distribution[month-1]
            
            yield_profiles.append({
                'element_id': element_id,
                'month': month,
                'yield_kwh': monthly_yield,
                'system_power_kw': system['system_power_kw'],
                'irradiation': month_irradiation,
                'orientation': system.get('orientation', 'Unknown'),
                'shading_factor': shading_factor,
                'environmental_reduction': shading_reduction
            })
    
    return pd.DataFrame(yield_profiles)

def calculate_net_energy_balance(demand_df, yield_df):
    """Calculate net energy balance (demand - generation)."""
    
    if len(demand_df) == 0 or len(yield_df) == 0:
        return pd.DataFrame()
    
    # Aggregate monthly yields
    monthly_yield = yield_df.groupby('month')['yield_kwh'].sum().reset_index()
    monthly_yield.columns = ['month', 'total_yield_kwh']
    
    # Merge demand and yield data
    balance_df = demand_df.merge(monthly_yield, on='month', how='left')
    balance_df['total_yield_kwh'] = balance_df['total_yield_kwh'].fillna(0)
    
    # Calculate net balance
    balance_df['net_import'] = balance_df['predicted_demand'] - balance_df['total_yield_kwh']
    balance_df['self_consumption_ratio'] = np.minimum(1.0, 
        safe_divide(balance_df['total_yield_kwh'], balance_df['predicted_demand'], 0))
    balance_df['excess_generation'] = np.maximum(0, balance_df['total_yield_kwh'] - balance_df['predicted_demand'])
    
    return balance_df

def render_yield_demand():
    """Render the yield vs demand analysis module."""
    
    # Add OptiSunny character header image
    st.image("attached_assets/step07_1751436847830.png", width=400)
    
    st.header("⚖️ Energy Yield vs Demand Analysis")
    
    # Get current project ID from database
    from services.io import get_current_project_id
    project_id = get_current_project_id()
    
    if not project_id:
        st.error("⚠️ No project ID found. Please complete Step 1 (Project Setup) first.")
        return
    
    st.markdown("""
    ### What This Step Does
    
    This analysis compares the energy your BIPV systems will generate with your building's actual energy needs. 
    We calculate how much of your electricity demand can be met by solar energy and identify potential cost savings.
    
    **Key Outputs:**
    - Monthly energy balance (generation vs consumption)
    - Self-consumption percentage
    - Grid electricity savings
    - Feed-in revenue from excess energy
    """)
    
    # Data Usage Information
    with st.expander("📊 How This Data Flows to Next Steps", expanded=False):
        st.markdown("""
        **→ Step 8 (System Optimization):**
        - Energy balance data helps optimize which windows get BIPV panels
        - Self-consumption ratios guide system sizing decisions
        - Monthly patterns inform seasonal performance optimization
        
        **→ Step 9 (Financial Analysis):**
        - Energy cost savings calculate your electricity bill reductions
        - Feed-in revenue shows income from excess solar energy
        - Grid import data determines your return on investment
        
        **→ Step 10 (Final Report):**
        - Energy charts demonstrate system performance
        - Coverage metrics show building energy independence level
        - Analysis validates technical feasibility and benefits
        """)
    
    # AI Model Performance Indicator
    project_data = st.session_state.get('project_data', {})
    
    # AI Model Performance Indicator
    project_data = st.session_state.get('project_data', {})
    if project_data.get('model_r2_score') is not None:
        r2_score = project_data['model_r2_score']
        status = project_data.get('model_performance_status', 'Unknown')
        
        if r2_score >= 0.85:
            color = "green"
            icon = "🟢"
        elif r2_score >= 0.70:
            color = "orange"
            icon = "🟡"
        else:
            color = "red"
            icon = "🔴"
        
        st.info(f"{icon} Using AI model predictions with R² score: **{r2_score:.3f}** ({status} performance)")
        
        # Removed persistent warning message
    
    # Check dependencies - look for actual data instead of flags
    
    # Check for PV specifications from Step 6 - enhanced with database fallback
    pv_specs = project_data.get('pv_specifications')
    if pv_specs is None:
        pv_specs = st.session_state.get('pv_specifications')
    
    # If no PV specs in session state, try to load from database
    if pv_specs is None or len(pv_specs) == 0:
        try:
            from database_manager import db_manager
            
            project_id = get_current_project_id()
            if project_id:
                pv_data = db_manager.get_pv_specifications(project_id)
                if pv_data:
                    pv_specs = pv_data.get('bipv_specifications', [])
                    if pv_specs:
                        st.info(f"✅ Loaded {len(pv_specs)} PV specifications from database")
                    else:
                        st.warning("⚠️ PV specifications found but no BIPV specifications array")
                else:
                    st.warning("⚠️ No PV specifications found in database")
        except Exception as e:
            st.error(f"Error loading PV specifications: {e}")
    
    if pv_specs is None or len(pv_specs) == 0:
        st.error("⚠️ PV system specifications not available. Please complete Step 6 (PV Specification).")
        return
    
    # Convert to DataFrame if needed
    if isinstance(pv_specs, list):
        pv_specs = pd.DataFrame(pv_specs)
    
    # Verify we're only working with suitable elements
    suitable_count = len(pv_specs)
    st.success(f"✅ PV specifications found ({suitable_count} suitable BIPV systems)")
    st.info("💡 Analysis includes only South/East/West-facing elements with good solar performance")
    
    # Check for historical data from Step 2 - look in correct location
    historical_data_project = project_data.get('historical_data')  # This is where Step 2 saves it
    data_analysis_complete = project_data.get('data_analysis_complete', False)
    
    if historical_data_project is None and not data_analysis_complete:
        st.error("⚠️ Historical data analysis not available. Please complete Step 2 (Historical Data Analysis).")
        return
    
    # Check for radiation data from Step 5 (multiple possible locations)
    radiation_data = project_data.get('radiation_data')
    radiation_completed = st.session_state.get('radiation_completed', False)
    
    # Enhanced validation - check consolidated data manager and database
    consolidated_manager = ConsolidatedDataManager()
    
    # Try to get radiation data from multiple sources
    if radiation_data is None and not radiation_completed:
        # Check consolidated data manager
        try:
            step5_data = consolidated_manager.get_step_data('step5_radiation')
            if step5_data and step5_data.get('radiation_analysis'):
                radiation_data = step5_data.get('radiation_analysis')
                radiation_completed = True
        except Exception:
            pass
        
        # Check database for radiation analysis results
        if radiation_data is None:
            try:
                from database_manager import db_manager
                from services.io import get_current_project_id
                
                project_id = get_current_project_id()
                if project_id:
                    radiation_results = db_manager.get_radiation_analysis_data(project_id)
                    if radiation_results and len(radiation_results) > 0:
                        radiation_data = radiation_results
                        radiation_completed = True
                        st.success(f"✅ Found radiation analysis data from database: {len(radiation_results)} elements analyzed")
            except Exception as e:
                st.warning(f"Could not check database for radiation data: {e}")
    
    # Final validation
    if radiation_data is None and not radiation_completed:
        st.error("⚠️ Radiation analysis not available. Please complete Step 5 (Radiation Analysis).")
        st.info("💡 **Next Steps:**\n1. Go to Step 5 (Radiation Analysis)\n2. Run the radiation analysis\n3. Return to this step")
        return
    
    # Convert radiation data if needed
    if isinstance(radiation_data, pd.DataFrame):
        radiation_data_df = radiation_data
    elif isinstance(radiation_data, dict) and 'element_radiation' in radiation_data:
        radiation_data_df = pd.DataFrame(radiation_data['element_radiation'])
    elif isinstance(radiation_data, list):
        radiation_data_df = pd.DataFrame(radiation_data)
    else:
        radiation_data_df = None
    
    if radiation_data_df is not None:
        st.success(f"✅ Radiation analysis found ({len(radiation_data_df)} elements)")
    
    # Use historical data from Step 2
    if historical_data_project:
        # Use actual AI forecast data with seasonal variation from Step 2
        forecast_data = historical_data_project.get('forecast_25_years', [])
        consumption_pattern = historical_data_project.get('consumption', [])
        avg_consumption = historical_data_project.get('avg_consumption', 2500)
        
        st.success(f"Using AI forecast data: {avg_consumption:.0f} kWh/month average with seasonal variation")
        
        # Use actual monthly consumption pattern from Step 2
        if consumption_pattern and len(consumption_pattern) >= 12:
            monthly_demand = consumption_pattern[:12]  # Use first 12 months
        else:
            # Calculate from forecast if available
            if forecast_data and len(forecast_data) >= 12:
                monthly_demand = forecast_data[:12]
            else:
                # Apply seasonal factors to average
                seasonal_factors = [1.1, 1.0, 0.9, 0.8, 0.7, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]
                monthly_demand = [avg_consumption * factor for factor in seasonal_factors]
        
        baseline_demand = {
            'avg_consumption': avg_consumption,
            'total_consumption': sum(monthly_demand),
            'consumption': monthly_demand,
            'monthly_demand': monthly_demand
        }
    else:
        # Fallback if somehow data is missing
        baseline_demand = {
            'avg_consumption': 2500,
            'total_consumption': 30000,
            'consumption': [2400, 2200, 2100, 2000, 1900, 1800, 2000, 2100, 2200, 2400, 2500, 2600],
            'monthly_demand': [2400, 2200, 2100, 2000, 1900, 1800, 2000, 2100, 2200, 2400, 2500, 2600]
        }
        st.info("Using baseline demand patterns for analysis.")
    
    # Load demand model (optional)
    model, feature_columns, metrics = load_demand_model()
    
    st.success(f"Analyzing energy balance for {len(pv_specs)} BIPV systems")
    
    # Analysis configuration
    st.subheader("🔧 Configure Your Analysis")
    
    st.markdown("**Set up the analysis timeframe and financial parameters:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📅 Analysis Timeline**")
        
        # Information about the Analysis Timeline Start Date
        with st.expander("ℹ️ What is Analysis Timeline Start Date?", expanded=False):
            st.markdown("""
            **Purpose of Analysis Timeline Start Date:**
            
            This date sets the **beginning of your BIPV system operation** for energy balance calculations.
            
            **How It's Used:**
            1. **Demand Forecasting**: Creates a 25-year energy consumption forecast starting from this date
            2. **BIPV Yield Calculations**: Determines when solar energy generation begins 
            3. **Financial Analysis**: Sets the start point for cost savings and payback calculations
            4. **Seasonal Patterns**: Aligns monthly energy balance with actual calendar months
            
            **Recommended Settings:**
            - **Near Future**: Choose a date 6-12 months ahead for realistic project planning
            - **Calendar Start**: January 1st gives cleaner annual reporting
            - **Construction Timeline**: Consider building renovation completion dates
            
            **Example**: If you plan BIPV installation in 2025, set the start date to January 1, 2025.
            This ensures accurate seasonal energy patterns and proper financial timeline alignment.
            """)
        
        analysis_start = st.date_input(
            "Analysis Timeline Start Date",
            value=dt(2024, 1, 1),
            key="analysis_start_yield",
            help="When your BIPV system operation begins - used for demand forecasting, yield calculations, and financial analysis timeline"
        )
        
        analysis_period = st.selectbox(
            "Analysis Period",
            ["1 Year", "2 Years", "5 Years", "10 Years"],
            index=0,
            key="analysis_period_yield",
            help="How many years to analyze energy performance"
        )
    
    with col2:
        st.markdown("**💶 Electricity Pricing**")
        
        # Use electricity rates from Step 1 project configuration
        electricity_rates = project_data.get('electricity_rates', {})
        default_import_rate = electricity_rates.get('import_rate', 0.25)
        default_export_rate = electricity_rates.get('export_rate', 0.08)
        
        st.success(f"Using rates from Step 1: €{default_import_rate:.3f}/kWh (buy), €{default_export_rate:.3f}/kWh (sell)")
        
        # Allow override if needed
        override_rates = st.checkbox("Use custom electricity rates", value=False, help="Override the rates from Step 1 if needed")
        
        if override_rates:
            electricity_price = st.number_input(
                "Electricity Purchase Price (€/kWh)",
                0.10, 0.50, default_import_rate, 0.01,
                key="electricity_price_yield",
                help="How much you pay for electricity from the grid"
            )
            
            feed_in_tariff = st.number_input(
                "Feed-in Price (€/kWh)",
                0.05, 0.20, default_export_rate, 0.01,
                help="How much you receive for excess solar energy sold to the grid",
                key="feed_in_tariff_yield"
            )
        else:
            electricity_price = default_import_rate
            feed_in_tariff = default_export_rate
    
    # Advanced settings
    with st.expander("⚙️ Advanced Settings (Optional)", expanded=False):
        st.markdown("**Fine-tune the analysis with these optional parameters:**")
        
        adv_col1, adv_col2 = st.columns(2)
        
        with adv_col1:
            st.markdown("**📈 Future Trends**")
            demand_growth_rate = st.slider(
                "Annual Demand Growth (%)",
                -2.0, 5.0, 1.0, 0.1,
                help="How much your building's energy use will increase each year (typically 1-2%)",
                key="demand_growth_yield"
            )
            
            system_degradation = st.slider(
                "BIPV System Degradation (%/year)",
                0.0, 1.0, 0.5, 0.1,
                help="How much solar panel efficiency decreases annually (typically 0.5%)",
                key="system_degradation_yield"
            )
        
        with adv_col2:
            st.markdown("**🔧 Analysis Options**")
            include_demand_response = st.checkbox(
                "Smart Energy Management",
                value=False,
                help="Include potential for shifting energy use to match solar generation",
                key="demand_response_yield"
            )
            
            seasonal_adjustment = st.checkbox(
                "Seasonal Patterns",
                value=True,
                help="Account for seasonal changes in energy use and solar production",
                key="seasonal_adjustment_yield"
            )
    
    # Initialize variables to avoid scope issues
    energy_balance = []
    total_annual_savings = 0
    total_feed_in_revenue = 0
    coverage_ratio = 0
    annual_demand = 0
    total_annual_yield = 0
    
    # Load existing data if available
    existing_analysis = project_data.get('yield_demand_analysis', {})
    if existing_analysis:
        energy_balance = existing_analysis.get('energy_balance', [])
        annual_metrics = existing_analysis.get('annual_metrics', {})
        total_annual_savings = annual_metrics.get('total_annual_savings', 0)
        total_feed_in_revenue = annual_metrics.get('total_feed_in_revenue', 0)
        coverage_ratio = annual_metrics.get('coverage_ratio', 0)
        annual_demand = annual_metrics.get('annual_demand', 0)
        total_annual_yield = annual_metrics.get('total_annual_yield', 0)
    
    # Run analysis
    st.markdown("---")
    st.markdown("**Ready to see how much energy your BIPV systems will generate?**")
    
    if st.button("🚀 Calculate Energy Balance", key="run_yield_analysis", type="primary"):
        with st.spinner("Calculating energy balance and economic impact..."):
            try:
                # Determine analysis end date
                period_months = {"1 Year": 12, "2 Years": 24, "5 Years": 60, "10 Years": 120}
                # Convert date to datetime if needed
                if isinstance(analysis_start, dt):
                    analysis_datetime = analysis_start
                else:
                    analysis_datetime = dt.combine(analysis_start, dt.min.time())
                end_date = analysis_datetime + timedelta(days=period_months[analysis_period] * 30)
                
                # Skip complex demand forecasting and use historical data directly
                # This avoids potential NoneType iteration issues
                
                # Get environmental factors from Step 3
                weather_analysis = project_data.get('weather_analysis', {})
                environmental_factors = weather_analysis.get('environmental_factors', {})
                
                # Also check project-level environmental factors
                if not environmental_factors:
                    environmental_factors = project_data.get('environmental_factors', {})
                
                # Display environmental shading impact
                shading_reduction = environmental_factors.get('shading_reduction', 0)
                if shading_reduction > 0:
                    st.warning(f"🌳 Environmental shading detected: {shading_reduction}% reduction applied to yield calculations")
                    trees_nearby = environmental_factors.get('trees_nearby', False)
                    tall_buildings = environmental_factors.get('tall_buildings', False)
                    
                    factors = []
                    if trees_nearby:
                        factors.append("trees/vegetation (15%)")
                    if tall_buildings:
                        factors.append("tall buildings (10%)")
                    
                    if factors:
                        st.info(f"Shading sources: {', '.join(factors)}")
                else:
                    st.success("🌞 No environmental shading factors - optimal solar conditions")
                
                # Calculate PV yield profiles using environmental factors
                # Access TMY data from weather analysis structure (Step 3)
                tmy_data = {}
                weather_analysis = project_data.get('weather_analysis', {})
                if weather_analysis:
                    tmy_data = weather_analysis.get('tmy_data', {})
                    
                    # Check if TMY data was regenerated with environmental factors
                    is_regenerated = weather_analysis.get('regenerated', False)
                    environmental_adjustment = weather_analysis.get('environmental_adjustment', 0)
                    
                    if is_regenerated and environmental_adjustment > 0:
                        st.success(f"✅ Using regenerated TMY data with {environmental_adjustment}% environmental shading already applied")
                        st.info(f"📊 TMY data: {len(tmy_data) if tmy_data else 0} hourly records (environmentally adjusted)")
                        # Reset environmental factors since they're already applied to TMY data
                        environmental_factors = {}
                    else:
                        st.info(f"✅ Using original TMY data from Step 3: {len(tmy_data) if tmy_data else 0} hourly records")
                else:
                    # Fallback: Check direct storage
                    tmy_data = project_data.get('tmy_data', {})
                    if tmy_data:
                        st.info(f"✅ Using TMY data: {len(tmy_data)} hourly records")
                    else:
                        st.error("❌ No TMY data found - cannot proceed without authentic weather data from Step 3")
                
                # Create yield profiles using authentic TMY data and environmental shading
                yield_profiles = []
                
                # Apply environmental shading factor
                shading_factor = 1 - (shading_reduction / 100)
                
                # Check if TMY data is available before proceeding
                if not tmy_data or len(tmy_data) == 0:
                    st.error("❌ Cannot calculate energy yields without TMY data from Step 3. Please complete Step 3 first.")
                    return
                
                if pv_specs is not None and len(pv_specs) > 0:
                    st.info(f"Processing {len(pv_specs)} BIPV systems...")
                    
                    for idx, (_, system) in enumerate(pv_specs.iterrows()):
                        # Get system parameters with safe conversion
                        capacity_kw = safe_float(system.get('capacity_kw', 0))
                        glass_area = safe_float(system.get('glass_area_m2', system.get('bipv_area_m2', 1.5)))
                        efficiency = safe_float(system.get('efficiency', 0.08))  # Default 8% BIPV efficiency
                        annual_radiation = 0  # Will be calculated from TMY data only
                        
                        # Recalculate realistic annual energy based on actual physics
                        # Formula: Energy = Area × Efficiency × Solar Radiation × Performance Ratio × Environmental Shading
                        performance_ratio = 0.85  # Typical for BIPV systems
                        
                        # Use actual TMY-derived radiation - only authentic data
                        if tmy_data and len(tmy_data) > 0:
                            # Calculate annual radiation from TMY data
                            tmy_annual_ghi = sum(record.get('ghi', record.get('GHI_Wm2', record.get('GHI', 0))) for record in tmy_data) / 1000  # Convert to kWh/m²/year
                            if tmy_annual_ghi > 100:  # Valid TMY data
                                annual_radiation = tmy_annual_ghi
                                if idx < 3:
                                    st.success(f"System {idx+1}: Using authentic TMY radiation: {annual_radiation:.0f} kWh/m²/year")
                            else:
                                if idx < 3:
                                    st.error(f"System {idx+1}: Invalid TMY data - cannot calculate yield without authentic radiation data")
                                continue  # Skip this system
                        else:
                            if idx < 3:
                                st.error(f"System {idx+1}: No TMY data available - cannot calculate yield without authentic radiation data")
                            continue  # Skip this system
                        
                        # Calculate annual energy with environmental shading applied
                        annual_energy = glass_area * efficiency * annual_radiation * performance_ratio * shading_factor
                        
                        # Only show details for first few systems to avoid UI clutter
                        if idx < 3:
                            st.info(f"System {idx+1}: {annual_energy:,.0f} kWh/year for {glass_area:.1f}m² at {efficiency:.1%} efficiency")
                        
                        # Ensure capacity is realistic - if missing, calculate from area and efficiency
                        if capacity_kw <= 0:
                            # BIPV glass capacity: Area × Efficiency × 1000 W/m² (STC)
                            capacity_kw = glass_area * efficiency
                        
                        # Display calculation details only for first few systems
                        if capacity_kw > 0:
                            specific_yield = annual_energy / capacity_kw
                            if idx < 3:
                                st.info(f"System {idx+1} specific yield: {specific_yield:,.0f} kWh/kW")
                        
                        # Display energy density without constraints
                        if glass_area > 0:
                            energy_per_m2 = annual_energy / glass_area
                            if idx < 3:
                                st.info(f"System {idx+1} energy per m²: {energy_per_m2:,.0f} kWh/m²/year")
                        
                        if annual_energy > 0 and capacity_kw > 0:  # Only include valid systems
                            # Calculate monthly yields using authentic TMY data
                            monthly_yields = []
                            if tmy_data and len(tmy_data) > 0:
                                # Calculate actual monthly yields from TMY data
                                monthly_irradiation = {}
                                
                                # Debug: Check TMY data structure for first few records
                                if idx == 0 and len(tmy_data) > 0:
                                    st.info(f"TMY sample record: {list(tmy_data.keys())[:5] if isinstance(tmy_data, dict) else tmy_data[0] if isinstance(tmy_data, list) else str(tmy_data)[:200]}")
                                
                                for month in range(1, 13):
                                    month_total = 0
                                    hours_count = 0
                                    
                                    if isinstance(tmy_data, dict):
                                        # TMY data is stored as dict with hour keys
                                        for hour_key, record in tmy_data.items():
                                            try:
                                                # Extract month from various possible datetime formats
                                                datetime_str = record.get('DateTime', record.get('datetime', ''))
                                                if datetime_str:
                                                    if '-' in datetime_str:  # YYYY-MM-DD format
                                                        record_month = int(datetime_str.split('-')[1])
                                                    elif '/' in datetime_str:  # MM/DD/YYYY format  
                                                        record_month = int(datetime_str.split('/')[0])
                                                    else:
                                                        continue
                                                    
                                                    if record_month == month:
                                                        ghi = record.get('ghi', record.get('GHI_Wm2', record.get('GHI', 0)))
                                                        if ghi > 0:
                                                            month_total += ghi / 1000  # Convert to kWh/m²
                                                            hours_count += 1
                                            except (ValueError, IndexError):
                                                continue
                                    
                                    elif isinstance(tmy_data, list):
                                        # TMY data is stored as list of records
                                        for record in tmy_data:
                                            try:
                                                datetime_str = record.get('DateTime', record.get('datetime', ''))
                                                if datetime_str:
                                                    if '-' in datetime_str:  # YYYY-MM-DD format
                                                        record_month = int(datetime_str.split('-')[1])
                                                    elif '/' in datetime_str:  # MM/DD/YYYY format
                                                        record_month = int(datetime_str.split('/')[0])
                                                    else:
                                                        continue
                                                    
                                                    if record_month == month:
                                                        ghi = record.get('ghi', record.get('GHI_Wm2', record.get('GHI', 0)))
                                                        if ghi > 0:
                                                            month_total += ghi / 1000  # Convert to kWh/m²
                                                            hours_count += 1
                                            except (ValueError, IndexError):
                                                continue
                                    
                                    monthly_irradiation[month] = month_total
                                    
                                    # Debug info for first system
                                    if idx == 0 and month <= 3:
                                        st.info(f"Month {month}: {month_total:.1f} kWh/m² from {hours_count} hours")
                                
                                # Calculate monthly yield for this system
                                for month in range(1, 13):
                                    month_radiation = monthly_irradiation.get(month, 0)
                                    month_yield = glass_area * efficiency * month_radiation * performance_ratio * shading_factor
                                    monthly_yields.append(month_yield)
                            else:
                                # Skip system if no TMY data
                                continue
                            
                            # Calculate final specific yield
                            specific_yield = annual_energy / capacity_kw
                            if idx < 3:
                                st.success(f"System {idx+1} final: {annual_energy:,.0f} kWh/year, Specific yield: {specific_yield:,.0f} kWh/kW")
                            elif idx == 3:
                                st.info(f"... processing remaining {len(pv_specs)-3} systems silently ...")
                            
                            system_data = {
                                'element_id': system.get('element_id', ''),
                                'system_power_kw': capacity_kw,
                                'annual_yield': annual_energy,
                                'monthly_yields': monthly_yields,
                                'specific_yield': specific_yield,
                                'environmental_shading_reduction': shading_reduction,
                                'shading_factor': shading_factor,
                                'trees_nearby': environmental_factors.get('trees_nearby', False),
                                'tall_buildings': environmental_factors.get('tall_buildings', False)
                            }
                            yield_profiles.append(system_data)
                
                # Calculate DYNAMIC demand with proper seasonal variation from AI forecast
                monthly_demand = []
                annual_demand = 0
                
                # First priority: Use AI forecast data with seasonal variation
                if historical_data_project and 'forecast_data' in historical_data_project:
                    forecast_data = historical_data_project['forecast_data']
                    
                    if isinstance(forecast_data, list) and len(forecast_data) >= 12:
                        # Use actual monthly AI forecast values (not constant!)
                        monthly_demand = forecast_data[:12]
                        annual_demand = sum(monthly_demand)
                        st.success(f"✅ Using AI forecast with SEASONAL VARIATION: {annual_demand:,.0f} kWh/year")
                        st.info(f"Monthly range: {min(monthly_demand):,.0f} - {max(monthly_demand):,.0f} kWh")
                    else:
                        # Create seasonal pattern from forecast average if data incomplete
                        avg_monthly = sum(forecast_data) / len(forecast_data) if forecast_data else 42000
                        seasonal_factors = [1.30, 1.20, 1.10, 0.95, 0.85, 0.75, 0.80, 0.90, 1.00, 1.10, 1.20, 1.35]
                        monthly_demand = [avg_monthly * factor for factor in seasonal_factors]
                        annual_demand = sum(monthly_demand)
                        st.info(f"Generated seasonal pattern from AI average: {annual_demand:,.0f} kWh/year")
                        
                elif historical_data_project and 'consumption' in historical_data_project:
                    # Second priority: Historical consumption with actual seasonal variation
                    consumption_data = historical_data_project['consumption']
                    if len(consumption_data) >= 12:
                        monthly_demand = consumption_data[:12]
                        annual_demand = sum(monthly_demand)
                        st.success(f"✅ Using historical data with SEASONAL VARIATION: {annual_demand:,.0f} kWh/year")
                        st.info(f"Monthly range: {min(monthly_demand):,.0f} - {max(monthly_demand):,.0f} kWh")
                    else:
                        # Create seasonal pattern from historical average
                        avg_monthly = sum(consumption_data) / len(consumption_data)
                        seasonal_factors = [1.30, 1.20, 1.10, 0.95, 0.85, 0.75, 0.80, 0.90, 1.00, 1.10, 1.20, 1.35]
                        monthly_demand = [avg_monthly * factor for factor in seasonal_factors]
                        annual_demand = sum(monthly_demand)
                        st.info(f"Generated seasonal pattern from historical average: {annual_demand:,.0f} kWh/year")
                        
                else:
                    # Last resort: Educational building with STRONG seasonal variation (not constant!)
                    base_annual = 500000  # 500 MWh/year
                    # Educational buildings: high heating (winter) + cooling (summer), low spring/fall
                    seasonal_factors = [1.35, 1.25, 1.10, 0.90, 0.80, 0.70, 0.75, 0.85, 0.95, 1.05, 1.20, 1.40]
                    
                    # Normalize to get correct annual total
                    normalization_factor = base_annual / sum(seasonal_factors)
                    monthly_demand = [normalization_factor * factor for factor in seasonal_factors]
                    annual_demand = sum(monthly_demand)
                    st.warning(f"⚠️ Using default educational pattern with SEASONAL VARIATION: {annual_demand:,.0f} kWh/year")
                    st.info(f"Monthly range: {min(monthly_demand):,.0f} - {max(monthly_demand):,.0f} kWh (NOT constant!)")
                
                # Use calculated demand values without bounds checking override
                # Display demand information for user awareness
                if annual_demand > 1500000:  # > 1.5 million kWh/year
                    st.info(f"ℹ️ High annual demand detected: {annual_demand:,.0f} kWh/year. Using calculated values from AI model and building data.")
                elif annual_demand < 50000:  # < 50,000 kWh/year 
                    st.info(f"ℹ️ Low annual demand detected: {annual_demand:,.0f} kWh/year. Using calculated values from AI model and building data.")
                else:
                    st.success(f"✅ Annual demand: {annual_demand:,.0f} kWh/year. Using calculated values from AI model and building data.")
                
                # Keep the original calculated values instead of overriding them
                
                demand_profile = {
                    'monthly_demand': monthly_demand,
                    'annual_demand': annual_demand
                }
                
                # Calculate total yields using actual calculated values
                if yield_profiles:
                    total_annual_yield = sum([system['annual_yield'] for system in yield_profiles])
                    total_monthly_yields = [sum([system['monthly_yields'][i] for system in yield_profiles]) for i in range(12)]
                    
                    st.success(f"✅ Total calculated yield: {total_annual_yield:,.0f} kWh/year from {len(yield_profiles)} systems")
                    coverage_percentage = (total_annual_yield / annual_demand) * 100 if annual_demand > 0 else 0
                    st.info(f"Energy coverage: {coverage_percentage:.1f}% of building demand")
                    
                    # Only warn about extremely unrealistic values (above 100% coverage)
                    if total_annual_yield > annual_demand:
                        excess_percentage = ((total_annual_yield / annual_demand) - 1) * 100
                        st.info(f"ℹ️ System generates {excess_percentage:.1f}% excess energy - this is realistic for well-oriented BIPV installations")
                else:
                    total_annual_yield = 0
                    total_monthly_yields = [0] * 12
                
                # Create energy balance
                energy_balance = []
                months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                
                for i in range(12):
                    monthly_demand_val = monthly_demand[i] if i < len(monthly_demand) else 2500
                    monthly_generation = total_monthly_yields[i]
                    net_import = monthly_demand_val - monthly_generation
                    
                    balance_data = {
                        'month': months[i],
                        'predicted_demand': monthly_demand_val,
                        'total_yield_kwh': monthly_generation,
                        'net_import': net_import,
                        'self_consumption_ratio': min(monthly_demand_val, monthly_generation) / monthly_demand_val if monthly_demand_val > 0 else 0,
                        'surplus': max(0, monthly_generation - monthly_demand_val),
                        'electricity_cost_savings': min(monthly_demand_val, monthly_generation) * electricity_price,
                        'feed_in_revenue': max(0, monthly_generation - monthly_demand_val) * feed_in_tariff,
                        'total_savings': (min(monthly_demand_val, monthly_generation) * electricity_price) + (max(0, monthly_generation - monthly_demand_val) * feed_in_tariff)
                    }
                    energy_balance.append(balance_data)
                
                # Calculate summary metrics
                total_annual_savings = sum([month['total_savings'] for month in energy_balance])
                total_feed_in_revenue = sum([month['feed_in_revenue'] for month in energy_balance])
                coverage_ratio = (total_annual_yield / annual_demand * 100) if annual_demand > 0 else 0
                
                # Save results
                yield_demand_analysis = {
                    'demand_profile': demand_profile,
                    'yield_profiles': yield_profiles,
                    'energy_balance': energy_balance,
                    'total_annual_yield': total_annual_yield,
                    'annual_demand': annual_demand,
                    'coverage_ratio': coverage_ratio,
                    'total_annual_savings': total_annual_savings,
                    'total_feed_in_revenue': total_feed_in_revenue,
                    'analysis_config': {
                        'start_date': analysis_datetime.isoformat(),
                        'period': analysis_period,
                        'electricity_price': electricity_price,
                        'feed_in_tariff': feed_in_tariff,
                        'demand_growth_rate': demand_growth_rate,
                        'system_degradation': system_degradation
                    }
                }
                
                st.session_state.project_data['yield_demand_analysis'] = yield_demand_analysis
                
                # Save to consolidated data manager
                consolidated_manager = ConsolidatedDataManager()
                step7_data = {
                    'yield_demand_analysis': yield_demand_analysis,
                    'energy_balance': energy_balance,
                    'monthly_analysis': energy_balance,
                    'annual_metrics': {
                        'total_annual_yield': total_annual_yield,
                        'annual_demand': annual_demand,
                        'coverage_ratio': coverage_ratio,
                        'total_annual_savings': total_annual_savings,
                        'total_feed_in_revenue': total_feed_in_revenue
                    },
                    'yield_complete': True
                }
                consolidated_manager.save_step7_data(step7_data)
                
                # Display results immediately after calculation
                st.success("✅ Energy balance analysis completed!")
                
                st.subheader("📊 Your BIPV System Performance")
                
                st.markdown("**Here's how your building-integrated solar panels will perform:**")
                
                # Key metrics with better explanations
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Annual Solar Generation", 
                        f"{total_annual_yield:,.0f} kWh",
                        help="Total electricity your BIPV systems will generate per year"
                    )
                
                with col2:
                    st.metric(
                        "Building Energy Demand", 
                        f"{annual_demand:,.0f} kWh",
                        help="Total electricity your building consumes per year"
                    )
                
                with col3:
                    st.metric(
                        "Energy Independence", 
                        f"{coverage_ratio:.1f}%",
                        help="Percentage of your energy needs met by solar power"
                    )
                
                with col4:
                    st.metric(
                        "Annual Cost Savings", 
                        f"€{total_annual_savings:,.0f}",
                        help="Money saved on electricity bills plus income from excess energy"
                    )
                
                # Monthly energy balance chart
                if energy_balance:
                    st.subheader("📈 Monthly Energy Pattern")
                    
                    st.markdown("**This chart shows your building's energy demand (orange) vs solar generation (blue) throughout the year:**")
                    
                    balance_df = pd.DataFrame(energy_balance)
                    
                    import plotly.express as px
                    fig = px.bar(
                        balance_df,
                        x='month',
                        y=['predicted_demand', 'total_yield_kwh'],
                        title="Energy Demand vs Solar Generation by Month",
                        labels={
                            'value': 'Energy (kWh)', 
                            'variable': 'Energy Type',
                            'predicted_demand': 'Building Demand',
                            'total_yield_kwh': 'Solar Generation'
                        },
                        barmode='group',
                        color_discrete_map={
                            'predicted_demand': '#FFA500',  # Orange for demand
                            'total_yield_kwh': '#1f77b4'   # Blue for generation
                        }
                    )
                    fig.update_layout(
                        xaxis_title="Month",
                        yaxis_title="Energy (kWh)",
                        legend_title="Energy Type"
                    )
                    fig.update_layout(width=700, height=400)  # Fixed width to prevent expansion
                    st.plotly_chart(fig, use_container_width=False)
                    
                    # Energy balance table with clear headers
                    st.subheader("📋 Detailed Monthly Breakdown")
                    st.markdown("**Complete month-by-month analysis of energy flows and savings:**")
                    
                    # Create user-friendly display
                    display_df = balance_df[['month', 'predicted_demand', 'total_yield_kwh', 'net_import', 'total_savings']].copy()
                    display_df.columns = ['Month', 'Building Demand (kWh)', 'Solar Generation (kWh)', 'Grid Import (kWh)', 'Monthly Savings (€)']
                    st.dataframe(display_df, use_container_width=True)
                # Save to database with error handling
                if project_id:
                    try:
                        # Save only authentic yield demand data - no fallbacks
                        if energy_balance and len(energy_balance) > 0:
                            db_helper.save_step_data("yield_demand", {
                                'energy_balance': energy_balance,
                                'analysis_config': yield_demand_analysis.get('analysis_config', {}),
                            })
                            
                            # Save authentic energy analysis data to energy_analysis table
                            db_manager.save_yield_demand_data(
                                project_id,
                                yield_demand_analysis
                            )
                        else:
                            st.error("Cannot save - no authentic energy balance data generated")
                    except Exception as db_error:
                        st.warning(f"Could not save to database: {str(db_error)}")
                else:
                    st.info("Analysis saved to session only (no project ID available)")
                
                st.session_state.yield_demand_completed = True
                
                st.success("✅ Energy yield vs demand analysis completed successfully!")
                
            except Exception as e:
                st.error(f"Error during yield analysis: {str(e)}")
                return
    
    # Display results if available
    if st.session_state.get('yield_demand_completed', False):
        analysis_data = st.session_state.project_data.get('yield_demand_analysis', {})
        
        if analysis_data and 'energy_balance' in analysis_data:
            st.subheader("📊 Yield vs Demand Analysis Results")
            
            # Get summary metrics from analysis data
            total_annual_yield = analysis_data.get('total_annual_yield', 0)
            annual_demand = analysis_data.get('annual_demand', 0)
            coverage_ratio = analysis_data.get('coverage_ratio', 0)
            total_annual_savings = analysis_data.get('total_annual_savings', 0)
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Annual Yield", f"{total_annual_yield:,.0f} kWh")
            
            with col2:
                st.metric("Annual Demand", f"{annual_demand:,.0f} kWh")
            
            with col3:
                st.metric("Coverage Ratio", f"{coverage_ratio:.1f}%")
            
            with col4:
                st.metric("Annual Savings", f"€{total_annual_savings:,.0f}")
            
            # Monthly analysis table
            st.subheader("📋 Monthly Energy Balance Details")
            
            # Create detailed monthly breakdown
            balance_display = []
            for i, row in enumerate(energy_balance[:12]):  # Show first 12 months
                month_name = row.get('month', f'Month {i+1}')
                balance_display.append({
                    'Month': month_name,
                    'Demand (kWh)': f"{row.get('predicted_demand', 0):.0f}",
                    'Total Yield (kWh)': f"{row.get('total_yield_kwh', 0):.0f}",
                    'Net Import (kWh)': f"{row.get('net_import', 0):.0f}",
                    'Surplus (kWh)': f"{row.get('surplus', 0):.0f}",
                    'Self-Consumption (%)': f"{row.get('self_consumption_ratio', 0):.1%}",
                    'Cost Savings (€)': f"€{row.get('electricity_cost_savings', 0):.0f}",
                    'Feed-in Revenue (€)': f"€{row.get('feed_in_revenue', 0):.0f}",
                    'Total Savings (€)': f"€{row.get('total_savings', 0):.0f}"
                })
            
            st.dataframe(balance_display, use_container_width=True)
            
            # Summary information
            total_feed_in = analysis_data.get('total_feed_in_revenue', 0)
            st.info(f"💡 Annual feed-in revenue: €{total_feed_in:,.0f} | Monthly values now show realistic seasonal variation based on solar irradiation patterns")
            
            # CSV Download functionality
            st.markdown("---")
            st.subheader("📥 Download Yield vs Demand Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Prepare monthly energy balance CSV
                if 'energy_balance' in analysis_data:
                    energy_balance = analysis_data['energy_balance']
                    
                    # Create comprehensive monthly data
                    monthly_csv_data = []
                    for month_data in energy_balance:
                        row = {
                            'Month': month_data.get('month', 'Unknown'),
                            'Building_Demand_kWh': month_data.get('predicted_demand', 0),
                            'Solar_Generation_kWh': month_data.get('total_yield_kwh', 0),
                            'Net_Grid_Import_kWh': month_data.get('net_import', 0),
                            'Surplus_Export_kWh': month_data.get('surplus', 0),
                            'Self_Consumption_Ratio_%': month_data.get('self_consumption_ratio', 0) * 100,
                            'Cost_Savings_EUR': month_data.get('electricity_cost_savings', 0),
                            'Feed_in_Revenue_EUR': month_data.get('feed_in_revenue', 0),
                            'Total_Monthly_Savings_EUR': month_data.get('total_savings', 0)
                        }
                        monthly_csv_data.append(row)
                    
                    # Create DataFrame and CSV
                    import io
                    monthly_df = pd.DataFrame(monthly_csv_data)
                    
                    # Add annual summary row
                    annual_summary = {
                        'Month': 'ANNUAL_TOTAL',
                        'Building_Demand_kWh': annual_demand,
                        'Solar_Generation_kWh': total_annual_yield,
                        'Net_Grid_Import_kWh': annual_demand - total_annual_yield,
                        'Surplus_Export_kWh': max(0, total_annual_yield - annual_demand),
                        'Self_Consumption_Ratio_%': min(100, (total_annual_yield / annual_demand) * 100) if annual_demand > 0 else 0,
                        'Cost_Savings_EUR': sum(month['electricity_cost_savings'] for month in energy_balance),
                        'Feed_in_Revenue_EUR': total_feed_in,
                        'Total_Monthly_Savings_EUR': total_annual_savings
                    }
                    monthly_df = pd.concat([monthly_df, pd.DataFrame([annual_summary])], ignore_index=True)
                    
                    # Generate CSV
                    csv_buffer = io.StringIO()
                    monthly_df.to_csv(csv_buffer, index=False, float_format='%.2f')
                    csv_string = csv_buffer.getvalue()
                    
                    # Generate filename with timestamp
                    timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"BIPV_Monthly_Energy_Balance_{timestamp}.csv"
                    
                    st.download_button(
                        label="📊 Download Monthly Energy Balance",
                        data=csv_string,
                        file_name=filename,
                        mime="text/csv",
                        help="Download detailed monthly energy flows, savings, and performance metrics"
                    )
            
            with col2:
                # Prepare system-level yield data CSV
                if 'yield_profiles' in analysis_data:
                    yield_profiles = analysis_data['yield_profiles']
                    
                    # Create system-level data
                    system_csv_data = []
                    for i, system in enumerate(yield_profiles):
                        # Get monthly yields
                        monthly_yields = system.get('monthly_yields', [0]*12)
                        row = {
                            'Element_ID': system.get('element_id', f'System_{i+1}'),
                            'System_Power_kW': system.get('system_power_kw', 0),
                            'Annual_Yield_kWh': system.get('annual_yield', 0),
                            'Specific_Yield_kWh_kW': system.get('specific_yield', 0),
                            'Environmental_Shading_Reduction_%': system.get('environmental_shading_reduction', 0),
                            'Shading_Factor': system.get('shading_factor', 1.0),
                            'Trees_Nearby': system.get('trees_nearby', False),
                            'Tall_Buildings': system.get('tall_buildings', False),
                            'Jan_kWh': monthly_yields[0] if len(monthly_yields) > 0 else 0,
                            'Feb_kWh': monthly_yields[1] if len(monthly_yields) > 1 else 0,
                            'Mar_kWh': monthly_yields[2] if len(monthly_yields) > 2 else 0,
                            'Apr_kWh': monthly_yields[3] if len(monthly_yields) > 3 else 0,
                            'May_kWh': monthly_yields[4] if len(monthly_yields) > 4 else 0,
                            'Jun_kWh': monthly_yields[5] if len(monthly_yields) > 5 else 0,
                            'Jul_kWh': monthly_yields[6] if len(monthly_yields) > 6 else 0,
                            'Aug_kWh': monthly_yields[7] if len(monthly_yields) > 7 else 0,
                            'Sep_kWh': monthly_yields[8] if len(monthly_yields) > 8 else 0,
                            'Oct_kWh': monthly_yields[9] if len(monthly_yields) > 9 else 0,
                            'Nov_kWh': monthly_yields[10] if len(monthly_yields) > 10 else 0,
                            'Dec_kWh': monthly_yields[11] if len(monthly_yields) > 11 else 0
                        }
                        system_csv_data.append(row)
                    
                    # Create DataFrame and CSV
                    systems_df = pd.DataFrame(system_csv_data)
                    
                    systems_csv_buffer = io.StringIO()
                    systems_df.to_csv(systems_csv_buffer, index=False, float_format='%.2f')
                    systems_csv_string = systems_csv_buffer.getvalue()
                    
                    systems_filename = f"BIPV_System_Yields_{timestamp}.csv"
                    
                    st.download_button(
                        label="🔋 Download System-Level Yields",
                        data=systems_csv_string,
                        file_name=systems_filename,
                        mime="text/csv",
                        help="Download individual BIPV system yields and performance by month"
                    )
            
            # Analysis parameters summary
            st.markdown("---")
            st.subheader("📋 Analysis Configuration Summary")
            
            if 'analysis_config' in analysis_data:
                config = analysis_data['analysis_config']
                config_summary = {
                    'Analysis_Start_Date': config.get('start_date', 'Not specified'),
                    'Analysis_Period': config.get('period', 'Not specified'),
                    'Electricity_Purchase_Price_EUR_kWh': config.get('electricity_price', 0),
                    'Feed_in_Tariff_EUR_kWh': config.get('feed_in_tariff', 0),
                    'Annual_Demand_Growth_Rate_%': config.get('demand_growth_rate', 0),
                    'System_Degradation_Rate_%': config.get('system_degradation', 0),
                    'Total_Annual_Yield_kWh': total_annual_yield,
                    'Total_Annual_Demand_kWh': annual_demand,
                    'Energy_Coverage_Ratio_%': coverage_ratio,
                    'Total_Annual_Savings_EUR': total_annual_savings,
                    'Annual_Feed_in_Revenue_EUR': total_feed_in
                }
                
                # Create config summary CSV
                config_df = pd.DataFrame(list(config_summary.items()), columns=['Parameter', 'Value'])
                
                config_csv_buffer = io.StringIO()
                config_df.to_csv(config_csv_buffer, index=False)
                config_csv_string = config_csv_buffer.getvalue()
                
                config_filename = f"BIPV_Analysis_Summary_{timestamp}.csv"
                
                st.download_button(
                    label="⚙️ Download Analysis Summary",
                    data=config_csv_string,
                    file_name=config_filename,
                    mime="text/csv",
                    help="Download analysis configuration and key performance indicators"
                )
            
            st.info("💡 **CSV Contents:** Monthly energy balance, individual system yields, and complete analysis configuration for integration with financial modeling or further analysis tools.")
            
            # Add step-specific download button
            st.markdown("---")
            st.markdown("### 📄 Step 7 Analysis Report")
            st.markdown("Download detailed yield vs demand analysis report:")
            
            from utils.individual_step_reports import create_step_download_button
            create_step_download_button(7, "Yield vs Demand", "Download Yield Analysis Report")
            
        else:
            st.info("No energy balance analysis available. Please run the yield vs demand analysis first.")