"""
UI rendering components for Step 7 Yield vs Demand Analysis
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime as dt
import io


def render_step7_header():
    """Render the Step 7 header and introduction."""
    try:
        st.image("attached_assets/step07_1751436847830.png", width=400)
    except:
        pass  # Skip image if not found
    st.header("⚖️ Energy Yield vs Demand Analysis")
    
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


def render_data_usage_info():
    """Render data usage information section."""
    with st.expander("📊 How This Data Will Be Used", expanded=False):
        st.markdown("""
        **Data Flow from Previous Steps:**
        
        **Step 2 → Historical Consumption:** Your building's energy usage patterns and AI demand model
        **Step 3 → Weather Data:** TMY solar irradiance for accurate yield calculations
        **Step 6 → PV Systems:** BIPV specifications, capacities, and expected performance
        
        **This Analysis Creates:**
        - Monthly energy balance comparing demand vs generation
        - Financial savings calculations using actual electricity rates
        - Self-consumption ratios and grid interaction analysis
        - System performance validation against building needs
        
        **Next Steps Will Use:**
        - **Step 8:** Energy balance data for optimization algorithms
        - **Step 9:** Financial metrics for economic analysis
        - **Step 10:** Complete analysis results for reporting
        """)


def render_analysis_configuration():
    """
    Render analysis configuration inputs.
    
    Returns:
        dict: Configuration parameters
    """
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
        
        # CRITICAL: Require authentic electricity rates from Step 1 - no placeholders
        st.info("Electricity rates MUST be configured in Step 1 project setup - no fallback values allowed")
        
        # Allow custom rates override
        override_rates = st.checkbox("Use custom electricity rates", value=False, 
                                   help="Override the rates from Step 1 if needed")
        
        if override_rates:
            electricity_price = st.number_input(
                "Electricity Purchase Price (€/kWh)",
                0.10, 0.50, 0.25, 0.01,
                key="electricity_price_yield",
                help="How much you pay for electricity from the grid"
            )
            
            feed_in_tariff = st.number_input(
                "Feed-in Price (€/kWh)",
                0.05, 0.20, 0.08, 0.01,
                key="feed_in_price_yield",
                help="How much you receive for excess electricity fed into the grid"
            )
        else:
            # CRITICAL: No fallback values - require authentic rates from database
            electricity_price = None  # Must be loaded from project configuration
            feed_in_tariff = None     # Must be loaded from project configuration
    
    # Advanced parameters
    with st.expander("⚙️ Advanced Analysis Parameters", expanded=False):
        col3, col4 = st.columns(2)
        
        with col3:
            demand_growth_rate = st.slider(
                "Annual Demand Growth Rate (%)",
                -2.0, 3.0, 0.5, 0.1,
                key="demand_growth_yield",
                help="Expected annual change in building energy consumption"
            )
            
        with col4:
            system_degradation = st.slider(
                "System Degradation Rate (%/year)",
                0.0, 1.0, 0.5, 0.1,
                key="system_degradation_yield",
                help="Annual reduction in PV system performance"
            )
    
    return {
        'start_date': analysis_start.strftime('%Y-%m-%d'),
        'period': analysis_period,
        'electricity_price': electricity_price,
        'feed_in_tariff': feed_in_tariff,
        'demand_growth_rate': demand_growth_rate,
        'system_degradation': system_degradation
    }


def render_environmental_factors(project_data):
    """
    Render environmental factors display.
    
    Returns:
        dict: Environmental factors data
    """
    # Extract environmental factors from Step 3
    weather_analysis = project_data.get('weather_analysis', {})
    environmental_factors = weather_analysis.get('environmental_factors', {})
    
    trees_nearby = environmental_factors.get('trees_nearby', False)
    tall_buildings = environmental_factors.get('tall_buildings', False)
    
    if trees_nearby or tall_buildings:
        # Calculate shading reduction
        shading_reduction = 0
        if trees_nearby:
            shading_reduction += 15
        if tall_buildings:
            shading_reduction += 10
        
        st.warning(f"🌳 Environmental shading detected: {shading_reduction}% reduction applied")
        
        factors = []
        if trees_nearby:
            factors.append("trees/vegetation (15%)")
        if tall_buildings:
            factors.append("tall buildings (10%)")
        
        if factors:
            st.info(f"Shading sources: {', '.join(factors)}")
        
        return {'shading_reduction': shading_reduction}
    else:
        st.success("🌞 No environmental shading factors - optimal solar conditions")
        return {}


def render_analysis_results(analysis_data):
    """Render comprehensive analysis results."""
    
    if not analysis_data or not analysis_data.get('is_valid'):
        st.error("❌ Analysis failed. Please check your data and try again.")
        return
    
    # Key Performance Indicators
    st.subheader("📊 Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Annual Generation",
            f"{analysis_data['annual_generation']:,.0f} kWh",
            delta=f"vs {analysis_data['annual_demand']:,.0f} kWh demand"
        )
    
    with col2:
        st.metric(
            "Energy Coverage",
            f"{analysis_data['coverage_ratio']:.1f}%",
            delta="of building demand"
        )
    
    with col3:
        st.metric(
            "Annual Savings",
            f"€{analysis_data['total_annual_savings']:,.0f}",
            delta=f"€{analysis_data['average_monthly_savings']:.0f}/month"
        )
    
    with col4:
        st.metric(
            "Feed-in Revenue",
            f"€{analysis_data['total_feed_in_revenue']:,.0f}",
            delta="from excess energy"
        )
    
    # Monthly Energy Balance Chart
    st.subheader("📈 Monthly Energy Balance")
    
    energy_balance = analysis_data['energy_balance']
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Create DataFrame for plotting
    chart_data = pd.DataFrame({
        'Month': months,
        'Demand': [month['demand_kwh'] for month in energy_balance],
        'Generation': [month['generation_kwh'] for month in energy_balance],
        'Self-Consumption': [month['self_consumption_kwh'] for month in energy_balance]
    })
    
    # Create grouped bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Energy Demand',
        x=chart_data['Month'],
        y=chart_data['Demand'],
        marker_color='lightcoral'
    ))
    
    fig.add_trace(go.Bar(
        name='BIPV Generation',
        x=chart_data['Month'],
        y=chart_data['Generation'],
        marker_color='lightgreen'
    ))
    
    fig.add_trace(go.Bar(
        name='Self-Consumption',
        x=chart_data['Month'],
        y=chart_data['Self-Consumption'],
        marker_color='gold'
    ))
    
    fig.update_layout(
        title="Monthly Energy Flow Analysis",
        xaxis_title="Month",
        yaxis_title="Energy (kWh)",
        barmode='group',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Monthly Financial Analysis
    st.subheader("💰 Monthly Financial Analysis")
    
    financial_data = pd.DataFrame({
        'Month': months,
        'Cost_Savings': [month['electricity_cost_savings'] for month in energy_balance],
        'Feed_in_Revenue': [month['feed_in_revenue'] for month in energy_balance],
        'Total_Savings': [month['total_monthly_savings'] for month in energy_balance]
    })
    
    fig_financial = px.bar(
        financial_data,
        x='Month',
        y=['Cost_Savings', 'Feed_in_Revenue'],
        title="Monthly Financial Benefits",
        labels={'value': 'Savings (€)', 'variable': 'Type'},
        color_discrete_map={
            'Cost_Savings': 'lightblue',
            'Feed_in_Revenue': 'lightgreen'
        }
    )
    
    st.plotly_chart(fig_financial, use_container_width=True)


def render_data_export(analysis_data, config):
    """Render data export section."""
    st.subheader("📤 Export Analysis Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Monthly energy balance CSV
        if analysis_data and analysis_data.get('energy_balance'):
            energy_balance = analysis_data['energy_balance']
            
            # Create monthly DataFrame
            monthly_df = pd.DataFrame(energy_balance)
            
            # Add summary row
            annual_summary = {
                'month': 'Annual Total',
                'demand_kwh': analysis_data['annual_demand'],
                'generation_kwh': analysis_data['annual_generation'],
                'net_import_kwh': sum(month['net_import_kwh'] for month in energy_balance),
                'surplus_export_kwh': sum(month['surplus_export_kwh'] for month in energy_balance),
                'self_consumption_kwh': sum(month['self_consumption_kwh'] for month in energy_balance),
                'self_consumption_ratio': analysis_data['coverage_ratio'] / 100,
                'electricity_cost_savings': sum(month['electricity_cost_savings'] for month in energy_balance),
                'feed_in_revenue': analysis_data['total_feed_in_revenue'],
                'total_monthly_savings': analysis_data['total_annual_savings']
            }
            monthly_df = pd.concat([monthly_df, pd.DataFrame([annual_summary])], ignore_index=True)
            
            # Generate CSV
            csv_buffer = io.StringIO()
            monthly_df.to_csv(csv_buffer, index=False, float_format='%.2f')
            csv_string = csv_buffer.getvalue()
            
            # Generate filename with timestamp
            timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
            filename = f"BIPV_Monthly_Energy_Balance_{timestamp}.csv"
    
    with col2:
        # Analysis configuration CSV
        if config:
            config_summary = {
                'Analysis_Start_Date': config.get('start_date', 'Not specified'),
                'Analysis_Period': config.get('period', 'Not specified'),
                'Electricity_Purchase_Price_EUR_kWh': config.get('electricity_price', 0),
                'Feed_in_Tariff_EUR_kWh': config.get('feed_in_tariff', 0),
                'Annual_Demand_Growth_Rate_%': config.get('demand_growth_rate', 0),
                'System_Degradation_Rate_%': config.get('system_degradation', 0),
                'Total_Annual_Yield_kWh': analysis_data['annual_generation'],
                'Total_Annual_Demand_kWh': analysis_data['annual_demand'],
                'Energy_Coverage_Ratio_%': analysis_data['coverage_ratio'],
                'Total_Annual_Savings_EUR': analysis_data['total_annual_savings'],
                'Annual_Feed_in_Revenue_EUR': analysis_data['total_feed_in_revenue']
            }
            
            # Create config summary CSV
            config_df = pd.DataFrame(list(config_summary.items()), columns=['Parameter', 'Value'])
            
            config_csv_buffer = io.StringIO()
            config_df.to_csv(config_csv_buffer, index=False)
            config_csv_string = config_csv_buffer.getvalue()
            
            config_filename = f"BIPV_Analysis_Summary_{timestamp}.csv"
    
    st.info("💡 **CSV Contents:** Monthly energy balance, individual system yields, and complete analysis configuration for integration with financial modeling or further analysis tools.")


def render_step_report_download():
    """Render Step 7 individual report download."""
    st.markdown("---")
    st.markdown("### 📄 Step 7 Analysis Report")
    st.markdown("Download detailed yield vs demand analysis report:")
    
    from utils.individual_step_reports import create_step_download_button
    create_step_download_button(7, "Yield vs Demand", "Download Yield Analysis Report")