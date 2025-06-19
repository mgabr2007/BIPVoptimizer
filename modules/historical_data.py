import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import pickle
import io

def render_historical_data():
    """Render the historical data analysis and AI model training module."""
    
    st.header("2. Historical Data & AI Model")
    st.markdown("Upload historical energy consumption data and train a baseline demand prediction model.")
    
    # Historical data upload section
    st.subheader("Historical Energy Consumption Data")
    
    uploaded_file = st.file_uploader(
        "Upload Monthly Consumption Data (CSV)",
        type=['csv'],
        help="Upload a CSV file with columns: Date, Consumption (kWh), Temperature (°C), and other relevant features"
    )
    
    if uploaded_file is not None:
        try:
            with st.spinner("Processing historical data..."):
                # Read the CSV file
                df = pd.read_csv(uploaded_file)
                st.success(f"✅ Data uploaded successfully! {len(df)} records loaded.")
                
                # Display data preview
                st.subheader("Data Preview")
                st.dataframe(df.head(10))
                
                # Data validation and preprocessing
                required_columns = ['Date', 'Consumption']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    st.error(f"❌ Missing required columns: {missing_columns}")
                    st.info("Required columns: Date, Consumption. Optional: Temperature, Humidity, Solar_Irradiance")
                    return
                
                # Process dates
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.sort_values('Date')
                
                # Extract time features
                df['Year'] = df['Date'].dt.year
                df['Month'] = df['Date'].dt.month
                df['DayOfYear'] = df['Date'].dt.dayofyear
                df['Quarter'] = df['Date'].dt.quarter
                
                # Store data in session state
                st.session_state.project_data['historical_data'] = df.to_dict()
                
                # Display data statistics
                st.subheader("Data Statistics")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Records", len(df))
                with col2:
                    st.metric("Date Range", f"{df['Date'].min().strftime('%Y-%m')} to {df['Date'].max().strftime('%Y-%m')}")
                with col3:
                    st.metric("Avg Monthly Consumption", f"{df['Consumption'].mean():.1f} kWh")
                with col4:
                    st.metric("Total Annual Consumption", f"{df['Consumption'].sum():.0f} kWh")
                
                # Trend visualization
                st.subheader("Consumption Trends")
                
                # Monthly trend chart
                fig = px.line(df, x='Date', y='Consumption', 
                             title='Monthly Energy Consumption Over Time',
                             labels={'Consumption': 'Consumption (kWh)', 'Date': 'Date'})
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                # Seasonal analysis
                col1, col2 = st.columns(2)
                
                with col1:
                    # Monthly averages
                    monthly_avg = df.groupby('Month')['Consumption'].mean().reset_index()
                    fig_month = px.bar(monthly_avg, x='Month', y='Consumption',
                                      title='Average Consumption by Month',
                                      labels={'Consumption': 'Avg Consumption (kWh)'})
                    st.plotly_chart(fig_month, use_container_width=True)
                
                with col2:
                    # Quarterly analysis
                    quarterly_avg = df.groupby('Quarter')['Consumption'].mean().reset_index()
                    fig_quarter = px.pie(quarterly_avg, values='Consumption', names='Quarter',
                                        title='Consumption Distribution by Quarter')
                    st.plotly_chart(fig_quarter, use_container_width=True)
                
                # AI Model Training Section
                st.subheader("AI Demand Prediction Model")
                
                if st.button("Train Baseline Demand Model"):
                    with st.spinner("Training RandomForest model..."):
                        # Prepare features for model training
                        feature_columns = ['Month', 'Quarter', 'DayOfYear']
                        
                        # Add additional features if available
                        optional_features = ['Temperature', 'Humidity', 'Solar_Irradiance']
                        for feature in optional_features:
                            if feature in df.columns and df[feature].notna().sum() > len(df) * 0.5:
                                feature_columns.append(feature)
                        
                        # Prepare training data
                        X = df[feature_columns].fillna(df[feature_columns].mean())
                        y = df['Consumption']
                        
                        # Split data
                        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                        
                        # Train model
                        model = RandomForestRegressor(n_estimators=100, random_state=42)
                        model.fit(X_train, y_train)
                        
                        # Make predictions
                        y_pred_train = model.predict(X_train)
                        y_pred_test = model.predict(X_test)
                        
                        # Calculate metrics
                        train_mae = mean_absolute_error(y_train, y_pred_train)
                        test_mae = mean_absolute_error(y_test, y_pred_test)
                        train_r2 = r2_score(y_train, y_pred_train)
                        test_r2 = r2_score(y_test, y_pred_test)
                        
                        # Save model
                        model_buffer = io.BytesIO()
                        pickle.dump({
                            'model': model,
                            'feature_columns': feature_columns,
                            'metrics': {
                                'train_mae': train_mae,
                                'test_mae': test_mae,
                                'train_r2': train_r2,
                                'test_r2': test_r2
                            }
                        }, model_buffer)
                        
                        st.session_state.project_data['demand_model'] = model_buffer.getvalue()
                        
                        st.success("✅ Model trained successfully!")
                        
                        # Display model performance
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Training MAE", f"{train_mae:.1f} kWh")
                        with col2:
                            st.metric("Testing MAE", f"{test_mae:.1f} kWh")
                        with col3:
                            st.metric("Training R²", f"{train_r2:.3f}")
                        with col4:
                            st.metric("Testing R²", f"{test_r2:.3f}")
                        
                        # Feature importance
                        importance_df = pd.DataFrame({
                            'Feature': feature_columns,
                            'Importance': model.feature_importances_
                        }).sort_values('Importance', ascending=False)
                        
                        fig_importance = px.bar(importance_df, x='Importance', y='Feature',
                                               title='Feature Importance in Demand Prediction',
                                               orientation='h')
                        st.plotly_chart(fig_importance, use_container_width=True)
                        
                        # Prediction vs Actual plot
                        comparison_df = pd.DataFrame({
                            'Actual': y_test,
                            'Predicted': y_pred_test
                        })
                        
                        fig_pred = px.scatter(comparison_df, x='Actual', y='Predicted',
                                             title='Predicted vs Actual Consumption (Test Set)',
                                             labels={'Actual': 'Actual Consumption (kWh)', 
                                                    'Predicted': 'Predicted Consumption (kWh)'})
                        
                        # Add perfect prediction line
                        min_val = min(comparison_df['Actual'].min(), comparison_df['Predicted'].min())
                        max_val = max(comparison_df['Actual'].max(), comparison_df['Predicted'].max())
                        fig_pred.add_trace(go.Scatter(x=[min_val, max_val], y=[min_val, max_val],
                                                     mode='lines', name='Perfect Prediction',
                                                     line=dict(dash='dash', color='red')))
                        
                        st.plotly_chart(fig_pred, use_container_width=True)
                
                # Model status
                if 'demand_model' in st.session_state.project_data:
                    st.success("✅ Baseline demand model is trained and ready!")
                    st.info("The model will be used in Step 7 to predict future energy demand.")
                else:
                    st.warning("⚠️ Please train the demand model before proceeding to energy analysis.")
                
        except Exception as e:
            st.error(f"❌ Error processing data: {str(e)}")
            st.info("Please ensure your CSV file has the correct format with 'Date' and 'Consumption' columns.")
    
    else:
        st.info("👆 Please upload a CSV file with historical energy consumption data.")
        
        # Show sample data format
        with st.expander("📋 View Sample Data Format"):
            sample_data = {
                'Date': ['2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01'],
                'Consumption': [1250, 1100, 950, 800],
                'Temperature': [5.2, 8.1, 12.5, 18.3],
                'Humidity': [75, 70, 65, 60]
            }
            st.dataframe(pd.DataFrame(sample_data))
            st.caption("Sample format: Date (YYYY-MM-DD), Consumption (kWh), Temperature (°C) [optional], Humidity (%) [optional]")
