"""
Yield vs Demand Analysis page for BIPV Optimizer
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pickle
from database_manager import db_manager
from core.solar_math import safe_divide

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
        'Month': dates.month,
        'Quarter': dates.quarter,
        'DayOfYear': dates.dayofyear
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
        'month': dates.month,
        'year': dates.year
    })
    
    return demand_df

def calculate_pv_yield_profiles(pv_specs, radiation_data, tmy_data):
    """Calculate monthly PV yield profiles for each system."""
    
    if pv_specs is None or len(pv_specs) == 0:
        return pd.DataFrame()
    
    yield_profiles = []
    
    for _, system in pv_specs.iterrows():
        element_id = system['element_id']
        
        # Get radiation data for this element
        element_radiation = radiation_data[radiation_data['element_id'] == element_id]
        
        if len(element_radiation) > 0:
            monthly_irradiation = element_radiation.iloc[0].get('monthly_irradiation', {})
            
            if isinstance(monthly_irradiation, dict):
                for month in range(1, 13):
                    month_irradiation = monthly_irradiation.get(str(month), monthly_irradiation.get(month, 0))
                    
                    # Calculate monthly yield
                    # Yield = System Power (kW) × Monthly Irradiation (kWh/m²) × Performance Ratio
                    performance_ratio = 0.85  # System efficiency factor
                    monthly_yield = system['system_power_kw'] * month_irradiation * performance_ratio
                    
                    yield_profiles.append({
                        'element_id': element_id,
                        'month': month,
                        'yield_kwh': monthly_yield,
                        'system_power_kw': system['system_power_kw'],
                        'irradiation': month_irradiation,
                        'orientation': system.get('orientation', 'Unknown')
                    })
            else:
                # If monthly data not available, distribute annually
                annual_yield = system['annual_energy_kwh']
                monthly_distribution = [0.05, 0.06, 0.08, 0.09, 0.11, 0.12, 0.12, 0.11, 0.09, 0.08, 0.06, 0.05]
                
                for month in range(1, 13):
                    monthly_yield = annual_yield * monthly_distribution[month-1]
                    
                    yield_profiles.append({
                        'element_id': element_id,
                        'month': month,
                        'yield_kwh': monthly_yield,
                        'system_power_kw': system['system_power_kw'],
                        'irradiation': 0,
                        'orientation': system.get('orientation', 'Unknown')
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
    
    st.header("⚖️ Step 7: Energy Yield vs Demand Analysis")
    
    # Check dependencies - look for actual data instead of flags
    project_data = st.session_state.get('project_data', {})
    
    # Check for PV specifications from Step 6
    pv_specs = project_data.get('pv_specifications')
    if pv_specs is None or len(pv_specs) == 0:
        st.error("⚠️ PV system specifications not available. Please complete Step 6 (PV Specification).")
        return
    
    # Check for historical data model from Step 2
    historical_data = st.session_state.get('historical_data')
    demand_model = project_data.get('demand_model')
    if historical_data is None and demand_model is None:
        st.error("⚠️ Historical data analysis not available. Please complete Step 2 (Historical Data Analysis).")
        return
    
    # Check for radiation data from Step 5
    radiation_data = project_data.get('radiation_data')
    if radiation_data is None or len(radiation_data) == 0:
        st.error("⚠️ Radiation analysis not available. Please complete Step 5 (Radiation Analysis).")
        return
    
    # Load demand model
    model, feature_columns, metrics = load_demand_model()
    
    # If no model available, create a simple baseline model
    if model is None:
        st.info("Using baseline demand model based on historical data patterns.")
        feature_columns = ['Month', 'Temperature', 'Humidity']
        metrics = {'mae': 'N/A', 'r2': 'N/A'}
    
    st.success(f"Analyzing energy balance for {len(pv_specs)} BIPV systems")
    
    # Analysis configuration
    st.subheader("🔧 Analysis Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        analysis_start = st.date_input(
            "Analysis Start Date",
            value=datetime(2024, 1, 1),
            key="analysis_start_yield"
        )
        
        analysis_period = st.selectbox(
            "Analysis Period",
            ["1 Year", "2 Years", "5 Years", "10 Years"],
            index=0,
            key="analysis_period_yield"
        )
    
    with col2:
        electricity_price = st.number_input(
            "Electricity Price (€/kWh)",
            0.10, 0.50, 0.25, 0.01,
            key="electricity_price_yield"
        )
        
        feed_in_tariff = st.number_input(
            "Feed-in Tariff (€/kWh)",
            0.05, 0.20, 0.08, 0.01,
            help="Price for excess energy fed back to grid",
            key="feed_in_tariff_yield"
        )
    
    # Advanced settings
    with st.expander("⚙️ Advanced Analysis Settings", expanded=False):
        adv_col1, adv_col2 = st.columns(2)
        
        with adv_col1:
            demand_growth_rate = st.slider(
                "Annual Demand Growth Rate (%)",
                -2.0, 5.0, 1.0, 0.1,
                help="Expected annual increase in energy demand",
                key="demand_growth_yield"
            )
            
            system_degradation = st.slider(
                "Annual System Degradation (%)",
                0.0, 1.0, 0.5, 0.1,
                help="Annual decrease in PV system performance",
                key="system_degradation_yield"
            )
        
        with adv_col2:
            include_demand_response = st.checkbox(
                "Include Demand Response",
                value=False,
                help="Consider demand shifting to optimize self-consumption",
                key="demand_response_yield"
            )
            
            seasonal_adjustment = st.checkbox(
                "Apply Seasonal Adjustments",
                value=True,
                help="Account for seasonal variations in demand and generation",
                key="seasonal_adjustment_yield"
            )
    
    # Run analysis
    if st.button("🚀 Run Yield vs Demand Analysis", key="run_yield_analysis"):
        with st.spinner("Calculating energy balance and economic impact..."):
            try:
                # Determine analysis end date
                period_months = {"1 Year": 12, "2 Years": 24, "5 Years": 60, "10 Years": 120}
                end_date = analysis_start + timedelta(days=period_months[analysis_period] * 30)
                
                # Predict future demand
                demand_forecast = predict_future_demand(model, feature_columns, analysis_start, end_date)
                
                # Apply demand growth if specified
                if demand_growth_rate != 0:
                    years_elapsed = (demand_forecast['date'] - demand_forecast['date'].iloc[0]).dt.days / 365.25
                    growth_factor = (1 + demand_growth_rate/100) ** years_elapsed
                    demand_forecast['predicted_demand'] *= growth_factor
                
                # Calculate PV yield profiles
                tmy_data = project_data.get('tmy_data', [])
                yield_profiles = calculate_pv_yield_profiles(pv_specs, radiation_data, tmy_data)
                
                # Apply system degradation
                if system_degradation > 0:
                    # For multi-year analysis, apply degradation
                    yield_profiles_degraded = []
                    for year in range(period_months[analysis_period] // 12 + 1):
                        degradation_factor = (1 - system_degradation/100) ** year
                        year_yields = yield_profiles.copy()
                        year_yields['yield_kwh'] *= degradation_factor
                        year_yields['year'] = year + 1
                        yield_profiles_degraded.append(year_yields)
                    
                    if yield_profiles_degraded:
                        yield_profiles = pd.concat(yield_profiles_degraded, ignore_index=True)
                
                # Calculate net energy balance
                energy_balance = calculate_net_energy_balance(demand_forecast, yield_profiles)
                
                # Economic calculations
                if len(energy_balance) > 0:
                    energy_balance['electricity_cost_savings'] = np.minimum(
                        energy_balance['total_yield_kwh'], 
                        energy_balance['predicted_demand']
                    ) * electricity_price
                    
                    energy_balance['feed_in_revenue'] = energy_balance['excess_generation'] * feed_in_tariff
                    energy_balance['net_electricity_cost'] = np.maximum(0, energy_balance['net_import']) * electricity_price
                    energy_balance['total_savings'] = (energy_balance['electricity_cost_savings'] + 
                                                     energy_balance['feed_in_revenue'])
                
                # Save results
                st.session_state.project_data['yield_demand_analysis'] = {
                    'demand_forecast': demand_forecast,
                    'yield_profiles': yield_profiles,
                    'energy_balance': energy_balance,
                    'analysis_config': {
                        'start_date': analysis_start.isoformat(),
                        'period': analysis_period,
                        'electricity_price': electricity_price,
                        'feed_in_tariff': feed_in_tariff,
                        'demand_growth_rate': demand_growth_rate,
                        'system_degradation': system_degradation
                    }
                }
                st.session_state.yield_demand_completed = True
                
                # Save to database
                db_manager.save_yield_demand_data(
                    st.session_state.project_data['project_id'],
                    st.session_state.project_data['yield_demand_analysis']
                )
                
                st.success("✅ Yield vs demand analysis completed successfully!")
                
            except Exception as e:
                st.error(f"Error during yield analysis: {str(e)}")
                return
    
    # Display results if available
    if st.session_state.get('yield_demand_completed', False):
        analysis_data = st.session_state.project_data.get('yield_demand_analysis', {})
        energy_balance = analysis_data.get('energy_balance')
        
        if energy_balance is not None and len(energy_balance) > 0:
            st.subheader("📊 Energy Balance Results")
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_demand = energy_balance['predicted_demand'].sum()
                st.metric("Total Energy Demand", f"{total_demand:,.0f} kWh")
            
            with col2:
                total_generation = energy_balance['total_yield_kwh'].sum()
                st.metric("Total BIPV Generation", f"{total_generation:,.0f} kWh")
            
            with col3:
                avg_self_consumption = energy_balance['self_consumption_ratio'].mean() * 100
                st.metric("Avg Self-Consumption", f"{avg_self_consumption:.1f}%")
            
            with col4:
                total_savings = energy_balance['total_savings'].sum() if 'total_savings' in energy_balance.columns else 0
                st.metric("Total Energy Savings", f"€{total_savings:,.0f}")
            
            # Monthly analysis table
            st.subheader("📋 Monthly Energy Balance")
            
            display_columns = ['date', 'predicted_demand', 'total_yield_kwh', 'net_import', 'self_consumption_ratio']
            if 'total_savings' in energy_balance.columns:
                display_columns.append('total_savings')
            
            st.dataframe(
                energy_balance[display_columns].round(2),
                use_container_width=True,
                column_config={
                    'date': 'Date',
                    'predicted_demand': st.column_config.NumberColumn('Demand (kWh)', format="%.0f"),
                    'total_yield_kwh': st.column_config.NumberColumn('Generation (kWh)', format="%.0f"),
                    'net_import': st.column_config.NumberColumn('Net Import (kWh)', format="%.0f"),
                    'self_consumption_ratio': st.column_config.NumberColumn('Self-Consumption (%)', format="%.1%"),
                    'total_savings': st.column_config.NumberColumn('Monthly Savings (€)', format="€%.0f")
                }
            )
            
            # Visualizations
            st.subheader("📈 Energy Balance Visualization")
            
            tab1, tab2, tab3, tab4 = st.tabs(["Monthly Balance", "Cumulative Analysis", "Self-Consumption", "Economic Impact"])
            
            with tab1:
                # Monthly demand vs generation
                fig_monthly = go.Figure()
                
                fig_monthly.add_trace(go.Scatter(
                    x=energy_balance['date'],
                    y=energy_balance['predicted_demand'],
                    mode='lines+markers',
                    name='Energy Demand',
                    line=dict(color='red')
                ))
                
                fig_monthly.add_trace(go.Scatter(
                    x=energy_balance['date'],
                    y=energy_balance['total_yield_kwh'],
                    mode='lines+markers',
                    name='BIPV Generation',
                    line=dict(color='green')
                ))
                
                fig_monthly.update_layout(
                    title="Monthly Energy Demand vs BIPV Generation",
                    xaxis_title="Date",
                    yaxis_title="Energy (kWh)",
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig_monthly, use_container_width=True)
            
            with tab2:
                # Cumulative analysis
                energy_balance['cumulative_demand'] = energy_balance['predicted_demand'].cumsum()
                energy_balance['cumulative_generation'] = energy_balance['total_yield_kwh'].cumsum()
                energy_balance['cumulative_net_import'] = energy_balance['net_import'].cumsum()
                
                fig_cumulative = go.Figure()
                
                fig_cumulative.add_trace(go.Scatter(
                    x=energy_balance['date'],
                    y=energy_balance['cumulative_demand'],
                    mode='lines',
                    name='Cumulative Demand',
                    line=dict(color='red')
                ))
                
                fig_cumulative.add_trace(go.Scatter(
                    x=energy_balance['date'],
                    y=energy_balance['cumulative_generation'],
                    mode='lines',
                    name='Cumulative Generation',
                    line=dict(color='green')
                ))
                
                fig_cumulative.update_layout(
                    title="Cumulative Energy Analysis",
                    xaxis_title="Date",
                    yaxis_title="Cumulative Energy (kWh)"
                )
                
                st.plotly_chart(fig_cumulative, use_container_width=True)
            
            with tab3:
                # Self-consumption analysis
                fig_self_cons = px.line(
                    energy_balance,
                    x='date',
                    y='self_consumption_ratio',
                    title="Self-Consumption Ratio Over Time",
                    labels={'self_consumption_ratio': 'Self-Consumption Ratio', 'date': 'Date'}
                )
                fig_self_cons.update_traces(line_color='blue')
                fig_self_cons.update_layout(yaxis_tickformat='.1%')
                
                st.plotly_chart(fig_self_cons, use_container_width=True)
                
                # Monthly self-consumption distribution
                monthly_self_cons = energy_balance.groupby(energy_balance['date'].dt.month)['self_consumption_ratio'].mean()
                
                fig_monthly_self = px.bar(
                    x=monthly_self_cons.index,
                    y=monthly_self_cons.values,
                    title="Average Self-Consumption by Month",
                    labels={'x': 'Month', 'y': 'Self-Consumption Ratio'}
                )
                fig_monthly_self.update_layout(yaxis_tickformat='.1%')
                
                st.plotly_chart(fig_monthly_self, use_container_width=True)
            
            with tab4:
                if 'total_savings' in energy_balance.columns:
                    # Economic impact over time
                    energy_balance['cumulative_savings'] = energy_balance['total_savings'].cumsum()
                    
                    fig_savings = px.line(
                        energy_balance,
                        x='date',
                        y='cumulative_savings',
                        title="Cumulative Energy Cost Savings",
                        labels={'cumulative_savings': 'Cumulative Savings (€)', 'date': 'Date'}
                    )
                    fig_savings.update_traces(line_color='green')
                    
                    st.plotly_chart(fig_savings, use_container_width=True)
                    
                    # Monthly savings breakdown
                    if all(col in energy_balance.columns for col in ['electricity_cost_savings', 'feed_in_revenue']):
                        fig_savings_breakdown = go.Figure()
                        
                        fig_savings_breakdown.add_trace(go.Bar(
                            x=energy_balance['date'],
                            y=energy_balance['electricity_cost_savings'],
                            name='Electricity Cost Savings',
                            marker_color='lightgreen'
                        ))
                        
                        fig_savings_breakdown.add_trace(go.Bar(
                            x=energy_balance['date'],
                            y=energy_balance['feed_in_revenue'],
                            name='Feed-in Revenue',
                            marker_color='darkgreen'
                        ))
                        
                        fig_savings_breakdown.update_layout(
                            title="Monthly Savings Breakdown",
                            xaxis_title="Date",
                            yaxis_title="Savings (€)",
                            barmode='stack'
                        )
                        
                        st.plotly_chart(fig_savings_breakdown, use_container_width=True)
                else:
                    st.info("Economic impact data not available")
            
            # Export results
            st.subheader("💾 Export Analysis Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 Download Energy Balance (CSV)", key="download_energy_balance"):
                    csv_data = energy_balance.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv_data,
                        file_name=f"energy_balance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            
            with col2:
                st.info("Energy balance ready for optimization analysis")
        
        else:
            st.warning("No energy balance data available. Please run the analysis.")