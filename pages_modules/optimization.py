"""
Multi-Objective Optimization page for BIPV Optimizer
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import random
from database_manager import db_manager
from core.solar_math import safe_divide

def create_individual(n_elements):
    """Create a random individual for genetic algorithm."""
    return [random.randint(0, 1) for _ in range(n_elements)]

def evaluate_individual(individual, pv_specs, energy_balance, financial_params):
    """Evaluate fitness of an individual solution."""
    
    try:
        # Convert individual to selection mask
        selection_mask = np.array(individual, dtype=bool)
        
        if not any(selection_mask):
            return (0.0, float('inf'))  # No systems selected
        
        # Calculate selected systems metrics
        selected_specs = pv_specs[selection_mask]
        
        # Calculate total metrics
        total_power_kw = selected_specs['system_power_kw'].sum()
        total_cost = selected_specs['total_installation_cost'].sum()
        total_annual_yield = selected_specs['annual_energy_kwh'].sum()
        
        # Calculate net import reduction (simplified)
        if energy_balance is not None and len(energy_balance) > 0:
            total_annual_demand = energy_balance['predicted_demand'].sum()
            net_import_reduction = min(total_annual_yield, total_annual_demand)
            new_net_import = max(0, total_annual_demand - total_annual_yield)
        else:
            # Fallback if no energy balance data
            net_import_reduction = total_annual_yield
            new_net_import = 0
        
        # Calculate annual savings
        electricity_price = financial_params.get('electricity_price', 0.25)
        annual_savings = net_import_reduction * electricity_price
        
        # Calculate ROI (simple payback consideration)
        if annual_savings > 0 and total_cost > 0:
            roi = annual_savings / total_cost
        else:
            roi = 0
        
        # Fitness: (ROI, -Net Import)
        return (roi, -new_net_import)
    
    except Exception as e:
        return (0.0, float('inf'))

def simple_genetic_algorithm(pv_specs, energy_balance, financial_params, ga_params):
    """Run simplified genetic algorithm optimization."""
    
    n_elements = len(pv_specs)
    population_size = ga_params['population_size']
    generations = ga_params['generations']
    mutation_rate = ga_params['mutation_rate']
    
    # Initialize population
    population = [create_individual(n_elements) for _ in range(population_size)]
    
    # Evolution tracking
    best_individuals = []
    fitness_history = []
    
    for generation in range(generations):
        # Evaluate population
        fitness_scores = []
        for individual in population:
            fitness = evaluate_individual(individual, pv_specs, energy_balance, financial_params)
            fitness_scores.append(fitness)
        
        # Find best individuals (Pareto front approximation)
        pareto_front = []
        for i, (roi, neg_import) in enumerate(fitness_scores):
            is_dominated = False
            for j, (other_roi, other_neg_import) in enumerate(fitness_scores):
                if i != j and other_roi >= roi and other_neg_import <= neg_import and (other_roi > roi or other_neg_import < neg_import):
                    is_dominated = True
                    break
            
            if not is_dominated:
                pareto_front.append((i, roi, -neg_import, population[i]))
        
        # Store best individuals
        if pareto_front:
            best_individuals.extend(pareto_front)
            avg_roi = np.mean([roi for _, roi, _, _ in pareto_front])
            avg_import = np.mean([net_import for _, _, net_import, _ in pareto_front])
            fitness_history.append({'generation': generation, 'avg_roi': avg_roi, 'avg_net_import': avg_import})
        
        # Selection for next generation (simple tournament selection)
        new_population = []
        
        # Keep best individuals
        elite_size = max(1, population_size // 10)
        elite_indices = sorted(range(len(fitness_scores)), key=lambda i: fitness_scores[i], reverse=True)[:elite_size]
        for idx in elite_indices:
            new_population.append(population[idx][:])
        
        # Generate offspring
        while len(new_population) < population_size:
            # Tournament selection
            parent1 = population[random.choice(range(len(population)))]
            parent2 = population[random.choice(range(len(population)))]
            
            # Simple crossover
            crossover_point = random.randint(1, n_elements - 1)
            child = parent1[:crossover_point] + parent2[crossover_point:]
            
            # Mutation
            for i in range(len(child)):
                if random.random() < mutation_rate:
                    child[i] = 1 - child[i]  # Flip bit
            
            new_population.append(child)
        
        population = new_population
    
    return best_individuals, fitness_history

def analyze_optimization_results(pareto_solutions, pv_specs, energy_balance, financial_params):
    """Analyze optimization results and generate solution alternatives."""
    
    solutions = []
    
    for i, (idx, roi, net_import, individual) in enumerate(pareto_solutions):
        selection_mask = np.array(individual, dtype=bool)
        selected_specs = pv_specs[selection_mask]
        
        if len(selected_specs) > 0:
            # Calculate solution metrics
            total_power_kw = selected_specs['system_power_kw'].sum()
            total_cost = selected_specs['total_installation_cost'].sum()
            total_annual_yield = selected_specs['annual_energy_kwh'].sum()
            selected_elements = selected_specs['element_id'].tolist()
            
            # Calculate savings
            electricity_price = financial_params.get('electricity_price', 0.25)
            annual_savings = min(total_annual_yield, net_import + total_annual_yield) * electricity_price
            
            solution = {
                'solution_id': f"Solution_{i+1}",
                'total_power_kw': total_power_kw,
                'total_investment': total_cost,
                'annual_energy_kwh': total_annual_yield,
                'annual_savings': annual_savings,
                'roi': roi,
                'net_import_kwh': net_import,
                'selected_elements': selected_elements,
                'n_selected_elements': len(selected_elements),
                'investment_per_kw': safe_divide(total_cost, total_power_kw, 0),
                'energy_cost_per_kwh': safe_divide(total_cost, total_annual_yield * 25, 0),  # 25-year lifetime
                'selection_mask': individual
            }
            
            solutions.append(solution)
    
    return pd.DataFrame(solutions)

def render_optimization():
    """Render the genetic algorithm optimization module."""
    
    st.header("🎯 Step 8: Multi-Objective BIPV Optimization")
    
    # AI Model Performance Impact Notice
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
        
        st.info(f"{icon} Optimization uses AI demand predictions (R² score: **{r2_score:.3f}** - {status} performance)")
        
        if r2_score < 0.70:
            st.warning("Low AI model performance may impact optimization accuracy. Results may be less reliable.")
    
    # Check dependencies
    required_steps = ['yield_demand_completed', 'pv_specs_completed']
    missing_steps = [step for step in required_steps if not st.session_state.get(step, False)]
    
    if missing_steps:
        st.error("⚠️ Required data missing. Please complete the following steps first:")
        for step in missing_steps:
            step_names = {
                'yield_demand_completed': "Step 7 (Yield vs Demand Analysis)",
                'pv_specs_completed': "Step 6 (PV Specification)"
            }
            st.error(f"• {step_names.get(step, step)}")
        return
    
    # Load required data
    project_data = st.session_state.get('project_data', {})
    pv_specs = project_data.get('pv_specifications')
    yield_demand_analysis = project_data.get('yield_demand_analysis', {})
    energy_balance = yield_demand_analysis.get('energy_balance')
    
    # Convert pv_specs to DataFrame if it's a list
    if pv_specs is not None:
        if isinstance(pv_specs, list):
            pv_specs = pd.DataFrame(pv_specs)
        elif not isinstance(pv_specs, pd.DataFrame):
            st.error("⚠️ PV specifications data format error.")
            return
    
    if pv_specs is None or len(pv_specs) == 0:
        st.error("⚠️ PV specifications not available.")
        return
    
    # Convert energy_balance to DataFrame if it's a list
    if energy_balance is not None:
        if isinstance(energy_balance, list):
            energy_balance = pd.DataFrame(energy_balance)
        elif not isinstance(energy_balance, pd.DataFrame):
            energy_balance = None
    
    st.success(f"Optimizing selection from {len(pv_specs)} viable BIPV systems")
    
    # Optimization configuration
    st.subheader("🔧 Optimization Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Genetic Algorithm Parameters**")
        population_size = st.slider(
            "Population Size",
            20, 200, 50, 10,
            help="🧬 Number of candidate solutions maintained in each generation of the genetic algorithm. Larger populations explore more design space but require more computation. 20-50: Fast convergence, 50-100: Balanced, 100+: Thorough exploration.",
            key="population_size_opt"
        )
        
        generations = st.slider(
            "Number of Generations",
            10, 100, 30, 5,
            help="🔄 Number of evolution cycles for the genetic algorithm. Each generation produces new solutions through crossover and mutation. More generations allow better optimization but increase computation time. 10-20: Quick results, 30-50: Standard, 50+: High precision.",
            key="generations_opt"
        )
        
        mutation_rate = st.slider(
            "Mutation Rate (%)",
            1.0, 20.0, 5.0, 1.0,
            help="🎲 Probability of random changes in each solution during evolution. Low rates (1-3%): Fine-tuning existing solutions, Medium rates (5-10%): Balanced exploration, High rates (10-20%): Aggressive exploration to escape local optima. Prevents algorithm stagnation.",
            key="mutation_rate_opt"
        )
    
    with col2:
        st.write("**Optimization Objectives**")
        electricity_price = st.number_input(
            "Electricity Price (€/kWh)",
            0.15, 0.50, 0.25, 0.01,
            help="⚡ Current electricity price for ROI calculations. Varies by region: Germany: 0.30-0.35 €/kWh, France: 0.18-0.25 €/kWh, Denmark: 0.25-0.30 €/kWh. Use peak daytime rates if available, as BIPV generates during peak hours. Higher prices improve BIPV economics.",
            key="electricity_price_opt"
        )
        
        max_investment = st.number_input(
            "Maximum Investment (€)",
            10000, 1000000, 100000, 5000,
            help="💰 Maximum available budget for BIPV installation. Acts as hard constraint during optimization - solutions exceeding this budget are rejected. Consider total project costs including panels, inverters, installation, permits, and electrical work. Typical BIPV: 800-1200 €/kW installed.",
            key="max_investment_opt"
        )
        
        min_coverage = st.slider(
            "Minimum Energy Coverage (%)",
            10, 100, 30, 5,
            help="Minimum percentage of energy demand to cover",
            key="min_coverage_opt"
        )
    
    # Advanced optimization settings
    with st.expander("⚙️ Advanced Optimization Settings", expanded=False):
        adv_col1, adv_col2 = st.columns(2)
        
        with adv_col1:
            prioritize_roi = st.checkbox(
                "Prioritize ROI over Coverage",
                value=True,
                help="Focus on return on investment rather than maximum coverage",
                key="prioritize_roi_opt"
            )
            
            include_maintenance = st.checkbox(
                "Include Maintenance Costs",
                value=True,
                help="Consider annual maintenance in ROI calculation",
                key="include_maintenance_opt"
            )
        
        with adv_col2:
            orientation_preference = st.selectbox(
                "Orientation Preference",
                ["None", "South", "Southwest", "Southeast"],
                index=0,
                help="Prefer specific orientations in optimization",
                key="orientation_pref_opt"
            )
            
            system_size_preference = st.selectbox(
                "System Size Preference",
                ["Balanced", "Favor Large", "Favor Small"],
                index=0,
                help="Preference for system sizes",
                key="size_pref_opt"
            )
    
    # Run optimization
    if st.button("🚀 Run Multi-Objective Optimization", key="run_optimization"):
        with st.spinner("Running genetic algorithm optimization..."):
            try:
                # Setup optimization parameters
                ga_params = {
                    'population_size': population_size,
                    'generations': generations,
                    'mutation_rate': mutation_rate / 100
                }
                
                financial_params = {
                    'electricity_price': electricity_price,
                    'max_investment': max_investment,
                    'min_coverage': min_coverage / 100
                }
                
                # Filter systems by budget constraint
                affordable_specs = pv_specs[pv_specs['total_installation_cost'] <= max_investment]
                
                if len(affordable_specs) == 0:
                    st.error("No systems within budget constraint. Please increase maximum investment.")
                    return
                
                # Run genetic algorithm
                pareto_solutions, fitness_history = simple_genetic_algorithm(
                    affordable_specs, energy_balance, financial_params, ga_params
                )
                
                if not pareto_solutions:
                    st.error("Optimization failed to find viable solutions.")
                    return
                
                # Analyze results
                solutions_df = analyze_optimization_results(
                    pareto_solutions, affordable_specs, energy_balance, financial_params
                )
                
                # Filter solutions by constraints
                solutions_df = solutions_df[solutions_df['total_investment'] <= max_investment]
                
                if len(solutions_df) == 0:
                    st.error("No solutions meet the specified constraints.")
                    return
                
                # Sort by ROI
                solutions_df = solutions_df.sort_values('roi', ascending=False).reset_index(drop=True)
                
                # Save results
                optimization_results = {
                    'solutions': solutions_df,
                    'fitness_history': fitness_history,
                    'optimization_config': {
                        'ga_params': ga_params,
                        'financial_params': financial_params,
                        'constraints': {
                            'max_investment': max_investment,
                            'min_coverage': min_coverage
                        }
                    }
                }
                
                st.session_state.project_data['optimization_results'] = optimization_results
                st.session_state.optimization_completed = True
                
                # Save to database with validation
                if 'project_id' in st.session_state.project_data and st.session_state.project_data['project_id']:
                    try:
                        db_manager.save_optimization_results(
                            st.session_state.project_data['project_id'],
                            optimization_results
                        )
                    except Exception as db_error:
                        st.warning(f"Could not save to database: {str(db_error)}")
                else:
                    st.info("Results saved to session. Database save skipped (no project ID).")
                
                st.success(f"✅ Optimization completed! Found {len(solutions_df)} viable solutions.")
                
            except Exception as e:
                st.error(f"Error during optimization: {str(e)}")
                return
    
    # Display results if available
    if st.session_state.get('optimization_completed', False):
        optimization_data = st.session_state.project_data.get('optimization_results', {})
        solutions = optimization_data.get('solutions')
        
        if solutions is not None and len(solutions) > 0:
            st.subheader("📊 Optimization Results")
            
            # Key metrics from best solutions
            best_solution = solutions.iloc[0]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Best ROI", f"{best_solution['roi']*100:.1f}%")
            
            with col2:
                st.metric("Best Investment", f"€{best_solution['total_investment']:,.0f}")
            
            with col3:
                st.metric("Annual Energy", f"{best_solution['annual_energy_kwh']:,.0f} kWh")
            
            with col4:
                st.metric("Solutions Found", len(solutions))
            
            # Solution selection and comparison
            st.subheader("🎯 Solution Selection & Comparison")
            
            # Solutions table
            display_columns = [
                'solution_id', 'total_power_kw', 'total_investment', 
                'annual_energy_kwh', 'annual_savings', 'roi', 'n_selected_elements'
            ]
            
            st.dataframe(
                solutions[display_columns].round(2),
                use_container_width=True,
                column_config={
                    'solution_id': 'Solution ID',
                    'total_power_kw': st.column_config.NumberColumn('Power (kW)', format="%.1f"),
                    'total_investment': st.column_config.NumberColumn('Investment (€)', format="€%.0f"),
                    'annual_energy_kwh': st.column_config.NumberColumn('Annual Energy (kWh)', format="%.0f"),
                    'annual_savings': st.column_config.NumberColumn('Annual Savings (€)', format="€%.0f"),
                    'roi': st.column_config.NumberColumn('ROI (%)', format="%.2%"),
                    'n_selected_elements': st.column_config.NumberColumn('# Elements', format="%.0f")
                }
            )
            
            # Solution selection
            st.subheader("✅ Select Preferred Solution")
            
            selected_solution_id = st.selectbox(
                "Choose solution for detailed analysis:",
                solutions['solution_id'].tolist(),
                key="selected_solution_opt"
            )
            
            selected_solution = solutions[solutions['solution_id'] == selected_solution_id].iloc[0]
            
            # Display selected solution details
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Selected Solution Summary:**")
                st.write(f"• Total Power: {selected_solution['total_power_kw']:.1f} kW")
                st.write(f"• Investment: €{selected_solution['total_investment']:,.0f}")
                st.write(f"• Annual Energy: {selected_solution['annual_energy_kwh']:,.0f} kWh")
                st.write(f"• Annual Savings: €{selected_solution['annual_savings']:,.0f}")
                st.write(f"• Return on Investment: {selected_solution['roi']*100:.1f}%")
            
            with col2:
                st.write("**Selected Elements:**")
                selected_elements = selected_solution['selected_elements']
                if isinstance(selected_elements, list):
                    for element in selected_elements[:5]:  # Show first 5
                        st.write(f"• {element}")
                    if len(selected_elements) > 5:
                        st.write(f"• ... and {len(selected_elements) - 5} more")
                else:
                    st.write("Element list not available")
            
            if st.button("💾 Save Selected Solution", key="save_solution"):
                st.session_state.project_data['selected_optimization_solution'] = selected_solution
                st.success("Solution saved for financial analysis!")
            
            # Visualization tabs
            st.subheader("📈 Optimization Analysis")
            
            tab1, tab2, tab3, tab4 = st.tabs(["Pareto Front", "Solution Comparison", "Investment Analysis", "Coverage Analysis"])
            
            with tab1:
                # Pareto front visualization
                fig_pareto = px.scatter(
                    solutions,
                    x='total_investment',
                    y='roi',
                    size='annual_energy_kwh',
                    color='n_selected_elements',
                    hover_data=['solution_id', 'annual_savings'],
                    title="Pareto Front: Investment vs ROI",
                    labels={
                        'total_investment': 'Total Investment (€)',
                        'roi': 'Return on Investment (%)',
                        'annual_energy_kwh': 'Annual Energy (kWh)',
                        'n_selected_elements': 'Number of Elements'
                    }
                )
                fig_pareto.update_traces(marker=dict(line=dict(width=1, color='DarkSlateGrey')))
                st.plotly_chart(fig_pareto, use_container_width=True)
            
            with tab2:
                # Solution comparison radar chart
                if len(solutions) >= 3:
                    top_solutions = solutions.head(3)
                    
                    # Normalize metrics for radar chart
                    metrics = ['roi', 'annual_energy_kwh', 'annual_savings']
                    normalized_data = []
                    
                    for _, solution in top_solutions.iterrows():
                        normalized_metrics = []
                        for metric in metrics:
                            max_val = solutions[metric].max()
                            min_val = solutions[metric].min()
                            if max_val != min_val:
                                norm_val = (solution[metric] - min_val) / (max_val - min_val)
                            else:
                                norm_val = 1.0
                            normalized_metrics.append(norm_val)
                        normalized_data.append(normalized_metrics)
                    
                    fig_radar = go.Figure()
                    
                    metric_labels = ['ROI', 'Annual Energy', 'Annual Savings']
                    
                    for i, (_, solution) in enumerate(top_solutions.iterrows()):
                        fig_radar.add_trace(go.Scatterpolar(
                            r=normalized_data[i] + [normalized_data[i][0]],  # Close the polygon
                            theta=metric_labels + [metric_labels[0]],
                            fill='toself',
                            name=solution['solution_id']
                        ))
                    
                    fig_radar.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 1]
                            )
                        ),
                        title="Top 3 Solutions Comparison"
                    )
                    
                    st.plotly_chart(fig_radar, use_container_width=True)
                else:
                    st.info("Need at least 3 solutions for comparison chart")
            
            with tab3:
                # Investment efficiency analysis
                solutions['efficiency_ratio'] = solutions['annual_energy_kwh'] / solutions['total_investment']
                
                fig_efficiency = px.scatter(
                    solutions,
                    x='total_investment',
                    y='efficiency_ratio',
                    size='roi',
                    color='solution_id',
                    title="Investment Efficiency: Energy Output per Euro",
                    labels={
                        'total_investment': 'Total Investment (€)',
                        'efficiency_ratio': 'Energy per Euro (kWh/€)',
                        'roi': 'ROI'
                    }
                )
                st.plotly_chart(fig_efficiency, use_container_width=True)
            
            with tab4:
                # Coverage analysis
                if energy_balance is not None and len(energy_balance) > 0:
                    total_demand = energy_balance['predicted_demand'].sum()
                    solutions['coverage_ratio'] = solutions['annual_energy_kwh'] / total_demand
                    
                    fig_coverage = px.bar(
                        solutions.head(10),  # Top 10 solutions
                        x='solution_id',
                        y='coverage_ratio',
                        color='roi',
                        title="Energy Coverage by Solution",
                        labels={'coverage_ratio': 'Coverage Ratio (%)', 'solution_id': 'Solution ID'}
                    )
                    fig_coverage.update_layout(yaxis_tickformat='.1%')
                    st.plotly_chart(fig_coverage, use_container_width=True)
                else:
                    st.info("Energy balance data not available for coverage analysis")
            
            # Export results
            st.subheader("💾 Export Optimization Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 Download Solutions (CSV)", key="download_solutions"):
                    csv_data = solutions.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv_data,
                        file_name=f"optimization_solutions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            
            with col2:
                st.info("Optimization complete - ready for financial analysis")
        
        else:
            st.warning("No optimization results available. Please run the optimization.")