import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def calculate_npv(cash_flows, discount_rate):
    """Calculate Net Present Value of cash flows."""
    npv = 0
    for i, cash_flow in enumerate(cash_flows):
        npv += cash_flow / ((1 + discount_rate) ** i)
    return npv

def calculate_irr(cash_flows, max_iterations=1000, tolerance=1e-6):
    """Calculate Internal Rate of Return using Newton-Raphson method."""
    if len(cash_flows) < 2:
        return None
    
    # Initial guess
    rate = 0.1
    
    for _ in range(max_iterations):
        # Calculate NPV and its derivative
        npv = sum(cf / ((1 + rate) ** i) for i, cf in enumerate(cash_flows))
        npv_derivative = sum(-i * cf / ((1 + rate) ** (i + 1)) for i, cf in enumerate(cash_flows))
        
        if abs(npv) < tolerance:
            return rate
        
        if abs(npv_derivative) < tolerance:
            break
        
        # Newton-Raphson iteration
        rate = rate - npv / npv_derivative
        
        # Ensure rate stays reasonable
        if rate < -0.99 or rate > 10:
            return None
    
    return rate if abs(npv) < tolerance else None

def calculate_payback_period(cash_flows):
    """Calculate simple and discounted payback periods."""
    if len(cash_flows) < 2:
        return None, None
    
    # Simple payback
    cumulative = 0
    simple_payback = None
    
    for i, cash_flow in enumerate(cash_flows):
        cumulative += cash_flow
        if cumulative >= 0 and simple_payback is None:
            if i == 0:
                simple_payback = 0
            else:
                # Interpolate between years
                simple_payback = i - 1 + (cash_flows[i-1] / (cash_flows[i-1] - cash_flow))
            break
    
    return simple_payback

def calculate_co2_savings(annual_energy_kwh, grid_co2_factor, system_lifetime):
    """Calculate CO2 emissions savings."""
    # CO2 savings per year (kg)
    annual_co2_savings = annual_energy_kwh * grid_co2_factor
    
    # Lifetime CO2 savings (tons)
    lifetime_co2_savings = (annual_co2_savings * system_lifetime) / 1000
    
    return annual_co2_savings, lifetime_co2_savings

def create_cash_flow_analysis(solution_data, financial_params, system_lifetime):
    """Create detailed cash flow analysis for a solution."""
    
    initial_cost = solution_data['installation_cost']
    annual_savings = solution_data['annual_savings']
    annual_energy = solution_data['annual_yield_kwh']
    
    # Financial parameters
    discount_rate = financial_params['discount_rate']
    electricity_price = financial_params['electricity_price']
    price_escalation = financial_params.get('price_escalation', 0.02)
    maintenance_cost_rate = financial_params.get('maintenance_cost_rate', 0.01)
    inverter_replacement_cost = financial_params.get('inverter_replacement_cost', 0.15)
    inverter_replacement_year = financial_params.get('inverter_replacement_year', 12)
    
    # Incentives
    federal_tax_credit = financial_params.get('federal_tax_credit', 0.30)
    state_incentive = financial_params.get('state_incentive', 0.0)
    rebate_amount = financial_params.get('rebate_amount', 0.0)
    
    cash_flows = []
    annual_details = []
    
    for year in range(system_lifetime + 1):
        if year == 0:
            # Initial investment
            cash_flow = -initial_cost
            
            # Apply incentives
            tax_credit = initial_cost * federal_tax_credit
            state_incentive_amount = initial_cost * state_incentive
            
            cash_flow += tax_credit + state_incentive_amount + rebate_amount
            
            annual_details.append({
                'year': year,
                'energy_production': 0,
                'energy_savings': 0,
                'maintenance_cost': 0,
                'net_cash_flow': cash_flow,
                'cumulative_cash_flow': cash_flow,
                'present_value': cash_flow
            })
            
        else:
            # Energy production degradation (typically 0.5% per year)
            degradation_rate = 0.005
            energy_production = annual_energy * ((1 - degradation_rate) ** (year - 1))
            
            # Escalating energy savings
            electricity_price_year = electricity_price * ((1 + price_escalation) ** (year - 1))
            energy_savings = energy_production * electricity_price_year
            
            # Maintenance costs
            maintenance_cost = initial_cost * maintenance_cost_rate
            
            # Inverter replacement
            inverter_cost = 0
            if year == inverter_replacement_year:
                inverter_cost = initial_cost * inverter_replacement_cost
            
            # Net cash flow
            cash_flow = energy_savings - maintenance_cost - inverter_cost
            
            # Present value
            present_value = cash_flow / ((1 + discount_rate) ** year)
            
            # Cumulative cash flow
            cumulative_cash_flow = annual_details[-1]['cumulative_cash_flow'] + cash_flow
            
            annual_details.append({
                'year': year,
                'energy_production': energy_production,
                'energy_savings': energy_savings,
                'maintenance_cost': maintenance_cost,
                'inverter_cost': inverter_cost,
                'net_cash_flow': cash_flow,
                'cumulative_cash_flow': cumulative_cash_flow,
                'present_value': present_value
            })
        
        cash_flows.append(cash_flow)
    
    return cash_flows, annual_details

def render_financial_analysis():
    """Render the financial and environmental analysis module."""
    
    st.header("9. Financial & Environmental Analysis")
    st.markdown("Comprehensive financial modeling and environmental impact assessment for optimized PV solutions.")
    
    # Check prerequisites
    prerequisites = ['optimization_results']
    missing = [p for p in prerequisites if p not in st.session_state.project_data]
    
    if missing:
        st.warning(f"⚠️ Missing required data: {', '.join(missing)}")
        st.info("Please complete optimization in Step 8 before proceeding.")
        return
    
    # Load optimization results
    results_df = pd.DataFrame(st.session_state.project_data['optimization_results'])
    
    st.subheader("Financial Modeling Parameters")
    
    # Financial parameters configuration
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Economic Parameters**")
        
        discount_rate = st.number_input(
            "Discount Rate (%)",
            value=6.0,
            min_value=1.0,
            max_value=15.0,
            step=0.5,
            help="Annual discount rate for NPV calculations"
        ) / 100
        
        system_lifetime = st.number_input(
            "System Lifetime (years)",
            value=25,
            min_value=15,
            max_value=35,
            step=1,
            help="Expected operational lifetime of PV system"
        )
        
        price_escalation = st.number_input(
            "Electricity Price Escalation (%/year)",
            value=2.0,
            min_value=0.0,
            max_value=8.0,
            step=0.1,
            help="Annual electricity price increase rate"
        ) / 100
        
        maintenance_cost_rate = st.number_input(
            "Annual Maintenance Cost (% of initial cost)",
            value=1.0,
            min_value=0.5,
            max_value=3.0,
            step=0.1,
            help="Annual maintenance as percentage of initial cost"
        ) / 100
    
    with col2:
        st.markdown("**Incentives & Costs**")
        
        federal_tax_credit = st.number_input(
            "Federal Tax Credit (%)",
            value=30.0,
            min_value=0.0,
            max_value=50.0,
            step=1.0,
            help="Federal investment tax credit percentage"
        ) / 100
        
        state_incentive = st.number_input(
            "State Incentive (%)",
            value=0.0,
            min_value=0.0,
            max_value=25.0,
            step=1.0,
            help="State incentive as percentage of cost"
        ) / 100
        
        rebate_amount = st.number_input(
            "Utility Rebate ($)",
            value=0,
            min_value=0,
            max_value=50000,
            step=500,
            help="Fixed utility rebate amount"
        )
        
        inverter_replacement_cost = st.number_input(
            "Inverter Replacement Cost (% of initial cost)",
            value=15.0,
            min_value=5.0,
            max_value=25.0,
            step=1.0,
            help="Cost of inverter replacement as percentage of initial cost"
        ) / 100
        
        inverter_replacement_year = st.number_input(
            "Inverter Replacement Year",
            value=12,
            min_value=8,
            max_value=20,
            step=1,
            help="Year when inverter replacement is needed"
        )
    
    # Environmental parameters
    st.subheader("Environmental Impact Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        grid_co2_factor = st.number_input(
            "Grid CO₂ Factor (kg CO₂/kWh)",
            value=0.4,
            min_value=0.1,
            max_value=1.0,
            step=0.05,
            help="CO₂ emissions factor for grid electricity"
        )
    
    with col2:
        co2_price = st.number_input(
            "CO₂ Price ($/ton)",
            value=50.0,
            min_value=0.0,
            max_value=200.0,
            step=5.0,
            help="Price per ton of CO₂ for carbon credit valuation"
        )
    
    # Store financial parameters
    financial_params = {
        'discount_rate': discount_rate,
        'electricity_price': st.session_state.project_data.get('financial_params', {}).get('electricity_price', 0.12),
        'price_escalation': price_escalation,
        'maintenance_cost_rate': maintenance_cost_rate,
        'federal_tax_credit': federal_tax_credit,
        'state_incentive': state_incentive,
        'rebate_amount': rebate_amount,
        'inverter_replacement_cost': inverter_replacement_cost,
        'inverter_replacement_year': inverter_replacement_year,
        'grid_co2_factor': grid_co2_factor,
        'co2_price': co2_price
    }
    
    # Solution selection for analysis
    st.subheader("Solution Selection")
    
    solution_options = results_df['solution_id'].tolist()
    selected_solutions = st.multiselect(
        "Select Solutions for Financial Analysis",
        solution_options,
        default=solution_options[:3] if len(solution_options) >= 3 else solution_options,
        help="Choose up to 5 solutions for detailed financial comparison"
    )
    
    if len(selected_solutions) > 5:
        st.warning("⚠️ Please select maximum 5 solutions for detailed analysis.")
        selected_solutions = selected_solutions[:5]
    
    # Run financial analysis
    if selected_solutions and st.button("Calculate Financial Analysis"):
        with st.spinner("Performing detailed financial and environmental analysis..."):
            try:
                financial_results = []
                
                for solution_id in selected_solutions:
                    solution_data = results_df[results_df['solution_id'] == solution_id].iloc[0]
                    
                    # Create cash flow analysis
                    cash_flows, annual_details = create_cash_flow_analysis(
                        solution_data, financial_params, system_lifetime
                    )
                    
                    # Calculate financial metrics
                    npv = calculate_npv(cash_flows, discount_rate)
                    irr = calculate_irr(cash_flows)
                    payback = calculate_payback_period(cash_flows)
                    
                    # Environmental calculations
                    annual_co2, lifetime_co2 = calculate_co2_savings(
                        solution_data['annual_yield_kwh'], 
                        grid_co2_factor, 
                        system_lifetime
                    )
                    
                    # Carbon credit value
                    carbon_credit_value = lifetime_co2 * co2_price
                    
                    financial_results.append({
                        'solution_id': solution_id,
                        'npv': npv,
                        'irr': irr * 100 if irr else 0,
                        'payback_period': payback,
                        'annual_co2_savings_kg': annual_co2,
                        'lifetime_co2_savings_tons': lifetime_co2,
                        'carbon_credit_value': carbon_credit_value,
                        'cash_flows': cash_flows,
                        'annual_details': annual_details,
                        'initial_cost': solution_data['installation_cost'],
                        'annual_savings': solution_data['annual_savings']
                    })
                
                # Store results
                st.session_state.project_data['financial_analysis'] = financial_results
                st.session_state.project_data['financial_params_used'] = financial_params
                
                st.success("✅ Financial analysis completed!")
                
            except Exception as e:
                st.error(f"❌ Error in financial analysis: {str(e)}")
                return
    
    # Display financial analysis results
    if 'financial_analysis' in st.session_state.project_data:
        financial_results = st.session_state.project_data['financial_analysis']
        
        st.subheader("Financial Analysis Results")
        
        # Summary table
        summary_data = []
        for result in financial_results:
            summary_data.append({
                'Solution': result['solution_id'],
                'NPV ($)': f"${result['npv']:,.0f}",
                'IRR (%)': f"{result['irr']:.1f}%" if result['irr'] > 0 else "N/A",
                'Payback (years)': f"{result['payback_period']:.1f}" if result['payback_period'] else "N/A",
                'CO₂ Savings (tons)': f"{result['lifetime_co2_savings_tons']:.1f}",
                'Carbon Value ($)': f"${result['carbon_credit_value']:,.0f}"
            })
        
        st.table(summary_data)
        
        # NPV comparison chart
        npv_data = pd.DataFrame([{
            'Solution': r['solution_id'],
            'NPV': r['npv']
        } for r in financial_results])
        
        fig_npv = px.bar(
            npv_data,
            x='Solution',
            y='NPV',
            title='Net Present Value Comparison',
            labels={'NPV': 'NPV ($)'},
            color='NPV',
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig_npv, use_container_width=True)
        
        # Cash flow analysis
        st.subheader("Cash Flow Analysis")
        
        # Select solution for detailed cash flow
        selected_for_cashflow = st.selectbox(
            "Select Solution for Detailed Cash Flow",
            [r['solution_id'] for r in financial_results]
        )
        
        if selected_for_cashflow:
            result = next(r for r in financial_results if r['solution_id'] == selected_for_cashflow)
            
            # Cash flow chart
            annual_df = pd.DataFrame(result['annual_details'])
            
            fig_cashflow = go.Figure()
            
            fig_cashflow.add_trace(go.Scatter(
                x=annual_df['year'],
                y=annual_df['net_cash_flow'],
                mode='lines+markers',
                name='Annual Cash Flow',
                line=dict(color='blue', width=3)
            ))
            
            fig_cashflow.add_trace(go.Scatter(
                x=annual_df['year'],
                y=annual_df['cumulative_cash_flow'],
                mode='lines+markers',
                name='Cumulative Cash Flow',
                line=dict(color='green', width=3)
            ))
            
            # Add payback line
            if result['payback_period']:
                fig_cashflow.add_vline(
                    x=result['payback_period'],
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Payback: {result['payback_period']:.1f} years"
                )
            
            fig_cashflow.add_hline(y=0, line_dash="dot", line_color="gray")
            
            fig_cashflow.update_layout(
                title=f'Cash Flow Analysis - {selected_for_cashflow}',
                xaxis_title='Year',
                yaxis_title='Cash Flow ($)',
                height=500
            )
            
            st.plotly_chart(fig_cashflow, use_container_width=True)
            
            # Detailed annual breakdown
            st.subheader("Annual Financial Breakdown")
            
            # Format annual details for display
            display_annual = annual_df.copy()
            display_annual = display_annual.round(0)
            
            # Format currency columns
            currency_cols = ['energy_savings', 'maintenance_cost', 'inverter_cost', 
                           'net_cash_flow', 'cumulative_cash_flow', 'present_value']
            
            for col in currency_cols:
                if col in display_annual.columns:
                    display_annual[col] = display_annual[col].apply(lambda x: f"${x:,.0f}")
            
            # Format energy column
            if 'energy_production' in display_annual.columns:
                display_annual['energy_production'] = display_annual['energy_production'].apply(lambda x: f"{x:,.0f} kWh")
            
            # Rename columns
            display_annual = display_annual.rename(columns={
                'year': 'Year',
                'energy_production': 'Energy Production',
                'energy_savings': 'Energy Savings',
                'maintenance_cost': 'Maintenance Cost',
                'inverter_cost': 'Inverter Cost',
                'net_cash_flow': 'Net Cash Flow',
                'cumulative_cash_flow': 'Cumulative Cash Flow',
                'present_value': 'Present Value'
            })
            
            st.dataframe(display_annual, use_container_width=True)
        
        # Environmental impact analysis
        st.subheader("Environmental Impact Analysis")
        
        # CO2 savings comparison
        co2_data = pd.DataFrame([{
            'Solution': r['solution_id'],
            'Annual CO2 Savings (kg)': r['annual_co2_savings_kg'],
            'Lifetime CO2 Savings (tons)': r['lifetime_co2_savings_tons'],
            'Carbon Credit Value ($)': r['carbon_credit_value']
        } for r in financial_results])
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_co2_annual = px.bar(
                co2_data,
                x='Solution',
                y='Annual CO2 Savings (kg)',
                title='Annual CO₂ Emissions Savings',
                color='Annual CO2 Savings (kg)',
                color_continuous_scale='Greens'
            )
            st.plotly_chart(fig_co2_annual, use_container_width=True)
        
        with col2:
            fig_co2_lifetime = px.bar(
                co2_data,
                x='Solution',
                y='Lifetime CO2 Savings (tons)',
                title='Lifetime CO₂ Emissions Savings',
                color='Lifetime CO2 Savings (tons)',
                color_continuous_scale='Greens'
            )
            st.plotly_chart(fig_co2_lifetime, use_container_width=True)
        
        # Environmental equivalents
        if financial_results:
            best_solution = max(financial_results, key=lambda x: x['lifetime_co2_savings_tons'])
            co2_savings = best_solution['lifetime_co2_savings_tons']
            
            # Calculate equivalents
            cars_equivalent = co2_savings / 4.6  # Average car emissions per year
            trees_equivalent = co2_savings / 0.02  # CO2 absorbed by tree per year
            
            st.markdown("**Environmental Impact Equivalents (Best Solution):**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("CO₂ Savings", f"{co2_savings:.1f} tons")
            with col2:
                st.metric("Equivalent to removing cars", f"{cars_equivalent:.0f} cars/year")
            with col3:
                st.metric("Equivalent to planting trees", f"{trees_equivalent:.0f} trees")
        
        # Export financial analysis
        st.subheader("Export Financial Analysis")
        
        if st.button("Export Financial Analysis"):
            # Create comprehensive export data
            export_data = []
            
            for result in financial_results:
                annual_df = pd.DataFrame(result['annual_details'])
                for _, row in annual_df.iterrows():
                    export_data.append({
                        'solution_id': result['solution_id'],
                        'year': row['year'],
                        'energy_production_kwh': row.get('energy_production', 0),
                        'energy_savings_usd': row.get('energy_savings', 0),
                        'maintenance_cost_usd': row.get('maintenance_cost', 0),
                        'net_cash_flow_usd': row['net_cash_flow'],
                        'cumulative_cash_flow_usd': row['cumulative_cash_flow'],
                        'present_value_usd': row['present_value']
                    })
            
            export_df = pd.DataFrame(export_data)
            csv_data = export_df.to_csv(index=False)
            
            st.download_button(
                label="Download Financial Analysis CSV",
                data=csv_data,
                file_name="bipv_financial_analysis.csv",
                mime="text/csv"
            )
        
        st.success("✅ Financial and environmental analysis completed! Ready for 3D visualization.")
        
    else:
        st.info("👆 Please select solutions and run financial analysis.")
        
        # Show financial analysis info
        with st.expander("💰 About Financial Analysis"):
            st.markdown("""
            **Financial Metrics Calculated:**
            - **NPV (Net Present Value)**: Present value of all future cash flows
            - **IRR (Internal Rate of Return)**: Discount rate that makes NPV = 0
            - **Payback Period**: Time to recover initial investment
            - **Cash Flow Analysis**: Year-by-year financial performance
            
            **Environmental Metrics:**
            - **CO₂ Emissions Savings**: Based on grid emission factor
            - **Carbon Credit Value**: Monetary value of CO₂ reductions
            - **Environmental Equivalents**: Cars removed, trees planted
            
            **Considerations:**
            - System degradation over time
            - Electricity price escalation
            - Maintenance costs
            - Inverter replacement
            - Tax credits and incentives
            """)
