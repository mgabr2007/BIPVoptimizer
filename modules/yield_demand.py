import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pickle
import io
from datetime import datetime, timedelta

def load_demand_model():
    """Load the trained demand prediction model."""
    try:
        model_data = st.session_state.project_data.get('demand_model')
        if model_data:
            model_dict = pickle.loads(model_data)
            return model_dict['model'], model_dict['feature_columns'], model_dict['metrics']
        return None, None, None
    except Exception as e:
        st.error(f"Error loading demand model: {str(e)}")
        return None, None, None

def predict_future_demand(model, feature_columns, start_date, end_date):
    """Predict energy demand for a future period."""
    
    # Generate date range
    dates = pd.date_range(start_date, end_date, freq='MS')  # Monthly start
    
    # Create feature matrix
    features_df = pd.DataFrame({
        'Month': dates.month,
        'Quarter': dates.quarter,
        'DayOfYear': dates.dayofyear
    })
    
    # Add any additional features that were used in training
    for feature in feature_columns:
        if feature not in features_df.columns:
            if feature == 'Temperature':
                # Simulate temperature based on month
                features_df[feature] = 15 + 10 * np.sin(2 * np.pi * (features_df['Month'] - 3) / 12)
            elif feature == 'Humidity':
                features_df[feature] = 60 + 20 * np.sin(2 * np.pi * (features_df['Month'] - 6) / 12)
            elif feature == 'Solar_Irradiance':
                features_df[feature] = 500 + 300 * np.sin(2 * np.pi * (features_df['Month'] - 3) / 12)
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
    
    tmy_df = pd.DataFrame(tmy_data)
    tmy_df['datetime'] = pd.to_datetime(tmy_df['datetime'])
    tmy_df['month'] = tmy_df['datetime'].dt.month
    
    yield_profiles = []
    
    for _, system in pv_specs.iterrows():
        element_id = system['element_id']
        
        # Get radiation data for this element
        element_radiation = radiation_data[radiation_data['element_id'] == element_id]
        
        if len(element_radiation) > 0:
            monthly_irradiation = element_radiation.iloc[0]['monthly_irradiation']
            
            if isinstance(monthly_irradiation, dict):
                for month in range(1, 13):
                    month_irradiation = monthly_irradiation.get(str(month), 0)
                    
                    # Calculate monthly yield
                    # Yield = System Power (kW) × Monthly Irradiation (kWh/m²) × Panel Efficiency / Reference Irradiance
                    monthly_yield = (system['system_power_kw'] * month_irradiation * 
                                   st.session_state.project_data['panel_specs']['efficiency'] / 1000)
                    
                    yield_profiles.append({
                        'element_id': element_id,
                        'month': month,
                        'yield_kwh': monthly_yield,
                        'system_power_kw': system['system_power_kw']
                    })
    
    return pd.DataFrame(yield_profiles)

def calculate_net_energy_balance(demand_df, yield_df):
    """Calculate net energy balance (demand - generation)."""
    
    # Aggregate monthly yield
    monthly_yield = yield_df.groupby('month')['yield_kwh'].sum().reset_index()
    monthly_yield.columns = ['month', 'total_pv_yield']
    
    # Merge with demand data
    balance_df = demand_df.merge(monthly_yield, on='month', how='left')
    balance_df['total_pv_yield'] = balance_df['total_pv_yield'].fillna(0)
    
    # Calculate net balance
    balance_df['net_import'] = balance_df['predicted_demand'] - balance_df['total_pv_yield']
    balance_df['self_consumption_ratio'] = np.minimum(
        balance_df['total_pv_yield'] / balance_df['predicted_demand'], 1.0
    )
    balance_df['excess_generation'] = np.maximum(
        balance_df['total_pv_yield'] - balance_df['predicted_demand'], 0
    )
    
    return balance_df

def render_yield_demand():
    """Render the yield vs demand analysis module."""
    
    st.header("7. Yield vs. Demand Calculation")
    st.markdown("Analyze PV energy yield against predicted demand and calculate net energy balance.")
    
    # Check prerequisites
    prerequisites = ['pv_specifications', 'radiation_grid', 'demand_model']
    missing = [p for p in prerequisites if p not in st.session_state.project_data]
    
    if missing:
        st.warning(f"⚠️ Missing required data: {', '.join(missing)}")
        st.info("Please complete previous steps: PV specifications and demand model training.")
        return
    
    # Load data
    pv_specs = pd.DataFrame(st.session_state.project_data['pv_specifications'])
    radiation_df = pd.DataFrame(st.session_state.project_data['radiation_grid'])
    tmy_data = st.session_state.project_data['tmy_data']
    
    # Load demand model
    model, feature_columns, metrics = load_demand_model()
    
    if model is None:
        st.error("❌ Could not load demand prediction model. Please retrain in Step 2.")
        return
    
    st.subheader("Analysis Configuration")
    
    # Analysis period configuration
    col1, col2 = st.columns(2)
    
    with col1:
        analysis_start = st.date_input(
            "Analysis Start Date",
            value=datetime(2024, 1, 1),
            help="Start date for yield vs demand analysis"
        )
    
    with col2:
        analysis_years = st.selectbox(
            "Analysis Period",
            [1, 5, 10, 20, 25],
            index=4,
            help="Number of years to analyze"
        )
    
    analysis_end = analysis_start + timedelta(days=365 * analysis_years)
    
    # Display model performance
    st.subheader("Demand Model Performance")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Training R²", f"{metrics['train_r2']:.3f}")
    with col2:
        st.metric("Testing R²", f"{metrics['test_r2']:.3f}")
    with col3:
        st.metric("Training MAE", f"{metrics['train_mae']:.1f} kWh")
    with col4:
        st.metric("Testing MAE", f"{metrics['test_mae']:.1f} kWh")
    
    # Run analysis
    if st.button("Calculate Yield vs Demand Analysis"):
        with st.spinner("Calculating energy yield and demand predictions..."):
            try:
                # Predict future demand
                demand_df = predict_future_demand(model, feature_columns, analysis_start, analysis_end)
                
                # Calculate PV yield profiles
                yield_df = calculate_pv_yield_profiles(pv_specs, radiation_df, tmy_data)
                
                # Calculate net energy balance
                balance_df = calculate_net_energy_balance(demand_df, yield_df)
                
                # Store results
                st.session_state.project_data['demand_predictions'] = demand_df.to_dict()
                st.session_state.project_data['yield_profiles'] = yield_df.to_dict()
                st.session_state.project_data['energy_balance'] = balance_df.to_dict()
                
                st.success("✅ Yield vs demand analysis completed!")
                
                # Display summary metrics
                annual_demand = demand_df['predicted_demand'].sum()
                annual_yield = yield_df['yield_kwh'].sum()
                annual_net_import = balance_df['net_import'].sum()
                avg_self_consumption = balance_df['self_consumption_ratio'].mean()
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Annual Demand", f"{annual_demand:,.0f} kWh")
                with col2:
                    st.metric("Annual PV Yield", f"{annual_yield:,.0f} kWh")
                with col3:
                    st.metric("Net Import", f"{annual_net_import:,.0f} kWh")
                with col4:
                    st.metric("Avg Self-Consumption", f"{avg_self_consumption:.1%}")
                
            except Exception as e:
                st.error(f"❌ Error in analysis: {str(e)}")
                return
    
    # Display analysis results if available
    if 'energy_balance' in st.session_state.project_data:
        balance_df = pd.DataFrame(st.session_state.project_data['energy_balance'])
        demand_df = pd.DataFrame(st.session_state.project_data['demand_predictions'])
        yield_df = pd.DataFrame(st.session_state.project_data['yield_profiles'])
        
        st.subheader("Energy Balance Analysis")
        
        # Monthly energy profile
        fig_balance = go.Figure()
        
        fig_balance.add_trace(go.Scatter(
            x=balance_df['date'],
            y=balance_df['predicted_demand'],
            mode='lines+markers',
            name='Predicted Demand',
            line=dict(color='red', width=3)
        ))
        
        fig_balance.add_trace(go.Scatter(
            x=balance_df['date'],
            y=balance_df['total_pv_yield'],
            mode='lines+markers',
            name='PV Generation',
            line=dict(color='green', width=3)
        ))
        
        fig_balance.add_trace(go.Scatter(
            x=balance_df['date'],
            y=balance_df['net_import'],
            mode='lines+markers',
            name='Net Import',
            line=dict(color='blue', width=3)
        ))
        
        fig_balance.update_layout(
            title='Monthly Energy Profile: Demand vs Generation',
            xaxis_title='Date',
            yaxis_title='Energy (kWh)',
            height=500,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_balance, use_container_width=True)
        
        # Self-consumption analysis
        col1, col2 = st.columns(2)
        
        with col1:
            # Monthly self-consumption ratio
            fig_self_consumption = px.bar(
                balance_df,
                x='month',
                y='self_consumption_ratio',
                title='Monthly Self-Consumption Ratio',
                labels={'self_consumption_ratio': 'Self-Consumption Ratio', 'month': 'Month'}
            )
            fig_self_consumption.update_yaxis(tickformat='.1%')
            st.plotly_chart(fig_self_consumption, use_container_width=True)
        
        with col2:
            # Excess generation
            fig_excess = px.bar(
                balance_df,
                x='month',
                y='excess_generation',
                title='Monthly Excess Generation',
                labels={'excess_generation': 'Excess Generation (kWh)', 'month': 'Month'},
                color='excess_generation',
                color_continuous_scale='Greens'
            )
            st.plotly_chart(fig_excess, use_container_width=True)
        
        # Detailed energy table
        st.subheader("Monthly Energy Balance Table")
        
        # Format the balance dataframe for display
        display_balance = balance_df.copy()
        display_balance['date'] = pd.to_datetime(display_balance['date']).dt.strftime('%Y-%m')
        display_balance = display_balance.round(0)
        
        # Rename columns for better display
        display_balance = display_balance.rename(columns={
            'date': 'Month',
            'predicted_demand': 'Demand (kWh)',
            'total_pv_yield': 'PV Yield (kWh)',
            'net_import': 'Net Import (kWh)',
            'self_consumption_ratio': 'Self-Consumption (%)',
            'excess_generation': 'Excess Gen (kWh)'
        })
        
        # Convert percentage to display format
        display_balance['Self-Consumption (%)'] = (display_balance['Self-Consumption (%)'] * 100).round(1)
        
        st.dataframe(display_balance[['Month', 'Demand (kWh)', 'PV Yield (kWh)', 
                                     'Net Import (kWh)', 'Self-Consumption (%)', 'Excess Gen (kWh)']], 
                    use_container_width=True)
        
        # PV system contribution analysis
        st.subheader("PV System Contribution Analysis")
        
        # Contribution by element
        element_contribution = yield_df.groupby('element_id')['yield_kwh'].sum().reset_index()
        element_contribution = element_contribution.merge(
            pv_specs[['element_id', 'orientation', 'system_power_kw']], 
            on='element_id'
        )
        element_contribution['yield_per_kw'] = element_contribution['yield_kwh'] / element_contribution['system_power_kw']
        
        # Top contributing elements
        top_contributors = element_contribution.nlargest(10, 'yield_kwh')
        
        fig_contribution = px.bar(
            top_contributors,
            x='element_id',
            y='yield_kwh',
            color='orientation',
            title='Top 10 PV Systems by Annual Yield',
            labels={'yield_kwh': 'Annual Yield (kWh)'}
        )
        st.plotly_chart(fig_contribution, use_container_width=True)
        
        # Performance by orientation
        orientation_performance = element_contribution.groupby('orientation').agg({
            'yield_kwh': 'sum',
            'system_power_kw': 'sum',
            'element_id': 'count'
        }).reset_index()
        orientation_performance['specific_yield'] = (
            orientation_performance['yield_kwh'] / orientation_performance['system_power_kw']
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_orient_yield = px.pie(
                orientation_performance,
                values='yield_kwh',
                names='orientation',
                title='Total Yield by Orientation'
            )
            st.plotly_chart(fig_orient_yield, use_container_width=True)
        
        with col2:
            fig_orient_specific = px.bar(
                orientation_performance,
                x='orientation',
                y='specific_yield',
                title='Specific Yield by Orientation',
                labels={'specific_yield': 'Specific Yield (kWh/kW)'}
            )
            st.plotly_chart(fig_orient_specific, use_container_width=True)
        
        # Annual summary
        st.subheader("Annual Summary")
        
        # Calculate annual totals
        annual_demand_total = balance_df['predicted_demand'].sum()
        annual_yield_total = balance_df['total_pv_yield'].sum()
        annual_net_import = balance_df['net_import'].sum()
        annual_excess = balance_df['excess_generation'].sum()
        pv_coverage_ratio = annual_yield_total / annual_demand_total if annual_demand_total > 0 else 0
        
        summary_metrics = {
            "Metric": [
                "Total Annual Demand",
                "Total PV Generation",
                "Net Grid Import",
                "Excess Generation",
                "PV Coverage Ratio",
                "Grid Independence"
            ],
            "Value": [
                f"{annual_demand_total:,.0f} kWh",
                f"{annual_yield_total:,.0f} kWh",
                f"{annual_net_import:,.0f} kWh",
                f"{annual_excess:,.0f} kWh",
                f"{pv_coverage_ratio:.1%}",
                f"{max(0, 1 - annual_net_import/annual_demand_total):.1%}" if annual_demand_total > 0 else "0%"
            ]
        }
        
        st.table(summary_metrics)
        
        # Export analysis results
        st.subheader("Export Analysis Results")
        
        if st.button("Export Energy Analysis"):
            # Combine all data for export
            export_data = balance_df.merge(
                yield_df.groupby('month')['yield_kwh'].sum().reset_index(),
                on='month'
            )
            
            csv_data = export_data.to_csv(index=False)
            st.download_button(
                label="Download Energy Analysis CSV",
                data=csv_data,
                file_name="energy_yield_demand_analysis.csv",
                mime="text/csv"
            )
        
        st.success("✅ Yield vs demand analysis completed! Ready for optimization.")
        
    else:
        st.info("👆 Please run the yield vs demand calculation to proceed with analysis.")
        
        # Show analysis preview
        with st.expander("📋 About Yield vs Demand Analysis"):
            st.markdown("""
            **This analysis will calculate:**
            - Monthly energy demand predictions using the trained AI model
            - Monthly PV energy yield for each system element
            - Net energy balance (import/export from grid)
            - Self-consumption ratios and excess generation
            - System performance by orientation and element
            - Annual energy independence metrics
            
            **Key outputs:**
            - Monthly energy profiles
            - Self-consumption analysis
            - Grid independence assessment
            - System contribution analysis
            - Performance benchmarking
            """)
