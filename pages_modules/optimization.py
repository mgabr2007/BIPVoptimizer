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
from utils.color_schemes import CHART_COLORS, get_chart_color
from utils.consolidated_data_manager import ConsolidatedDataManager

def create_individual(n_elements):
    """Create a random individual for genetic algorithm."""
    return [random.randint(0, 1) for _ in range(n_elements)]

def evaluate_individual(individual, pv_specs, energy_balance, financial_params):
    """Evaluate fitness of an individual solution using weighted multi-objective approach."""
    
    try:
        # Convert individual to selection mask
        selection_mask = np.array(individual, dtype=bool)
        
        if not any(selection_mask):
            return (0.0,)  # No systems selected - return single fitness value
        
        # Calculate selected systems metrics
        selected_specs = pv_specs[selection_mask]
        
        # Calculate total metrics (handle different possible column names)
        if 'total_installation_cost' in selected_specs.columns:
            total_cost = selected_specs['total_installation_cost'].sum()
        elif 'total_cost_eur' in selected_specs.columns:
            total_cost = selected_specs['total_cost_eur'].sum()
        elif 'total_cost' in selected_specs.columns:
            total_cost = selected_specs['total_cost'].sum()
        else:
            total_cost = 0
            
        total_annual_yield = selected_specs['annual_energy_kwh'].sum()
        
        # Calculate net import reduction
        if energy_balance is not None and len(energy_balance) > 0:
            total_annual_demand = energy_balance['predicted_demand'].sum()
            net_import_reduction = min(total_annual_yield, total_annual_demand)
        else:
            net_import_reduction = total_annual_yield
        
        # Calculate annual savings and ROI
        electricity_price = financial_params.get('electricity_price', 0.25)
        annual_savings = net_import_reduction * electricity_price
        
        # Include maintenance costs if enabled
        include_maintenance = financial_params.get('include_maintenance', True)
        if include_maintenance:
            # Apply typical BIPV maintenance cost (1-2% of investment annually)
            annual_maintenance = total_cost * 0.015  # 1.5% annual maintenance
            net_annual_savings = annual_savings - annual_maintenance
        else:
            net_annual_savings = annual_savings
        
        if net_annual_savings > 0 and total_cost > 0:
            roi = (net_annual_savings / total_cost) * 100  # ROI as percentage
        else:
            roi = 0
        
        # Get objective weights
        weight_cost = financial_params.get('weight_cost', 33) / 100.0
        weight_yield = financial_params.get('weight_yield', 33) / 100.0
        weight_roi = financial_params.get('weight_roi', 34) / 100.0
        
        # Normalize objectives (0-1 scale)
        # For cost: lower is better, so use 1/(1+normalized_cost)
        if 'total_installation_cost' in pv_specs.columns:
            max_possible_cost = pv_specs['total_installation_cost'].sum()
        elif 'total_cost_eur' in pv_specs.columns:
            max_possible_cost = pv_specs['total_cost_eur'].sum()
        elif 'total_cost' in pv_specs.columns:
            max_possible_cost = pv_specs['total_cost'].sum()
        else:
            max_possible_cost = 1
            
        normalized_cost = total_cost / max_possible_cost if max_possible_cost > 0 else 0
        cost_fitness = 1 / (1 + normalized_cost)  # Higher is better
        
        # For yield: higher is better
        max_possible_yield = pv_specs['annual_energy_kwh'].sum()  # If all systems selected
        yield_fitness = total_annual_yield / max_possible_yield if max_possible_yield > 0 else 0
        
        # For ROI: higher is better (already normalized as percentage)
        roi_fitness = min(roi / 50.0, 1.0)  # Cap at 50% ROI for normalization
        
        # Apply advanced optimization preferences
        bonus_factor = 1.0
        
        # Orientation preference bonus
        orientation_preference = financial_params.get('orientation_preference', 'None')
        if orientation_preference != 'None' and 'orientation' in selected_specs.columns:
            preferred_count = (selected_specs['orientation'] == orientation_preference).sum()
            total_selected = len(selected_specs)
            if total_selected > 0:
                orientation_bonus = (preferred_count / total_selected) * 0.1  # 10% max bonus
                bonus_factor += orientation_bonus
        
        # System size preference bonus
        system_size_preference = financial_params.get('system_size_preference', 'Balanced')
        if 'capacity_kw' in selected_specs.columns:
            avg_capacity = selected_specs['capacity_kw'].mean()
            if system_size_preference == 'Favor Large' and avg_capacity > 2.0:  # Above 2kW average
                bonus_factor += 0.05  # 5% bonus for large systems
            elif system_size_preference == 'Favor Small' and avg_capacity < 1.0:  # Below 1kW average
                bonus_factor += 0.05  # 5% bonus for small systems
        
        # ROI prioritization adjustment
        prioritize_roi = financial_params.get('prioritize_roi', True)
        if prioritize_roi:
            # Increase ROI weight relative to others
            roi_fitness *= 1.2  # 20% boost to ROI fitness
        
        # Calculate weighted fitness (single objective)
        weighted_fitness = (
            weight_cost * cost_fitness +
            weight_yield * yield_fitness + 
            weight_roi * roi_fitness
        ) * bonus_factor
        
        # Apply minimum coverage constraint as hard constraint
        min_coverage = financial_params.get('min_coverage', 0.30)
        if energy_balance is not None and len(energy_balance) > 0:
            total_demand = energy_balance['predicted_demand'].sum()
            coverage_ratio = net_import_reduction / total_demand if total_demand > 0 else 0
            if coverage_ratio < min_coverage:
                weighted_fitness *= 0.1  # Heavy penalty for not meeting minimum coverage
        
        return (weighted_fitness,)
    
    except Exception as e:
        return (0.0,)

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
        
        # Find best individuals (handle single fitness values)
        pareto_front = []
        for i, fitness in enumerate(fitness_scores):
            # Handle single fitness value (weighted score)
            if isinstance(fitness, tuple) and len(fitness) == 1:
                fitness_value = fitness[0]
            elif isinstance(fitness, (int, float)):
                fitness_value = fitness
            else:
                fitness_value = 0
            
            pareto_front.append((i, fitness_value, fitness_value, population[i]))
        
        # Store best individuals
        if pareto_front:
            best_individuals.extend(pareto_front)
            avg_fitness = np.mean([fitness_val for _, fitness_val, _, _ in pareto_front])
            fitness_history.append({'generation': generation, 'avg_fitness': avg_fitness})
        
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
    
    for i, (idx, fitness_value, _, individual) in enumerate(pareto_solutions):
        selection_mask = np.array(individual, dtype=bool)
        selected_specs = pv_specs[selection_mask]
        
        if len(selected_specs) > 0:
            # Calculate solution metrics
            if 'system_power_kw' in selected_specs.columns:
                total_power_kw = selected_specs['system_power_kw'].sum()
            elif 'capacity_kw' in selected_specs.columns:
                total_power_kw = selected_specs['capacity_kw'].sum()
            else:
                total_power_kw = 0
                
            # Handle different cost column names
            if 'total_installation_cost' in selected_specs.columns:
                total_cost = selected_specs['total_installation_cost'].sum()
            elif 'total_cost_eur' in selected_specs.columns:
                total_cost = selected_specs['total_cost_eur'].sum()
            elif 'total_cost' in selected_specs.columns:
                total_cost = selected_specs['total_cost'].sum()
            else:
                total_cost = 0
                
            total_annual_yield = selected_specs['annual_energy_kwh'].sum()
            selected_elements = selected_specs['element_id'].tolist() if 'element_id' in selected_specs.columns else [f"Element_{j}" for j in range(len(selected_specs))]
            
            # Calculate net import reduction
            if energy_balance is not None and len(energy_balance) > 0:
                total_annual_demand = energy_balance['predicted_demand'].sum()
                net_import = max(0, total_annual_demand - total_annual_yield)
            else:
                net_import = 0
            
            # Calculate ROI
            electricity_price = financial_params.get('electricity_price', 0.25)
            annual_savings = min(total_annual_yield, total_annual_demand if 'total_annual_demand' in locals() else total_annual_yield) * electricity_price
            roi = (annual_savings / total_cost * 100) if total_cost > 0 else 0
            
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
    
    # Add OptiSunny character header image
    st.image("attached_assets/step08_1751436847831.png", width=400)
    
    st.header("🎯 Step 8: Multi-Objective BIPV Optimization")
    
    # Data Usage Information
    with st.expander("📊 How This Data Will Be Used", expanded=False):
        st.markdown("""
        ### Data Flow Through BIPV Analysis Workflow:
        
        **Step 8 → Step 9 (Financial Analysis):**
        - **Optimized system selection** → Investment cost calculations and lifecycle financial modeling
        - **Pareto-optimal solutions** → Risk assessment and sensitivity analysis for multiple scenarios
        - **Cost-benefit trade-offs** → NPV and IRR calculations for optimal vs alternative configurations
        
        **Step 8 → Step 10 (Reporting):**
        - **Genetic algorithm results** → Technical documentation of optimization methodology and convergence
        - **Multi-objective performance** → Visual analysis of cost, yield, and ROI trade-offs
        - **Optimal system schedule** → Implementation recommendations and prioritization strategy
        - **Comparative analysis** → Performance benchmarking against non-optimized baseline configurations
        """)
    
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
        
        # Removed persistent warning message
    
    # Check for actual data instead of completion flags
    project_data = st.session_state.get('project_data', {})
    
    # Check for PV specifications from Step 6 (multiple possible locations)
    pv_specs = project_data.get('pv_specifications')
    if pv_specs is None:
        pv_specs = st.session_state.get('pv_specifications')
    
    # Check for yield/demand analysis from Step 7
    yield_demand_analysis = project_data.get('yield_demand_analysis', {})
    energy_balance = yield_demand_analysis.get('energy_balance')
    
    # Validate required data
    missing_data = []
    if pv_specs is None or len(pv_specs) == 0:
        missing_data.append("Step 6 (PV Specification)")
    
    if energy_balance is None or len(energy_balance) == 0:
        missing_data.append("Step 7 (Yield vs Demand Analysis)")
    
    if missing_data:
        st.error("⚠️ Required data missing. Please complete the following steps first:")
        for step in missing_data:
            st.error(f"• {step}")
        return
    
    # Success confirmation
    st.success(f"✅ Ready for optimization: {len(pv_specs)} PV systems, energy balance analysis complete")
    
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
        st.write("**Multi-Objective Weights**")
        st.caption("Set the importance of each objective (must sum to 100%)")
        
        # Auto-balancing objective weights that sum to 100%
        st.write("🎯 **Objective Weights (Auto-balanced to 100%)**")
        
        # Initialize weights if not in session state
        if 'opt_weight_cost' not in st.session_state:
            st.session_state.opt_weight_cost = 33
            st.session_state.opt_weight_yield = 33
            st.session_state.opt_weight_roi = 34
        
        # Primary weight selector
        weight_cost = st.slider(
            "Minimize Cost Weight (%)",
            0, 100, st.session_state.opt_weight_cost, 1,
            help="Weight for minimizing total system cost. Higher values prioritize lower-cost solutions.",
            key="weight_cost_slider"
        )
        
        # Auto-balance the remaining two weights
        remaining = 100 - weight_cost
        if remaining > 0:
            # Calculate proportional split of remaining weight
            current_yield = st.session_state.opt_weight_yield
            current_roi = st.session_state.opt_weight_roi
            current_total = current_yield + current_roi
            
            if current_total > 0:
                weight_yield = int((current_yield / current_total) * remaining)
                weight_roi = remaining - weight_yield
            else:
                weight_yield = remaining // 2
                weight_roi = remaining - weight_yield
        else:
            weight_yield = 0
            weight_roi = 0
        
        # Update session state
        st.session_state.opt_weight_cost = weight_cost
        st.session_state.opt_weight_yield = weight_yield
        st.session_state.opt_weight_roi = weight_roi
        
        # Display auto-calculated weights
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Maximize Yield Weight", f"{weight_yield}%", 
                     help="Auto-calculated to maintain 100% total")
        with col_b:
            st.metric("Maximize ROI Weight", f"{weight_roi}%", 
                     help="Auto-calculated to maintain 100% total")
        
        # Secondary adjustment option
        if st.checkbox("Fine-tune Yield vs ROI balance", key="fine_tune_weights"):
            if weight_yield + weight_roi > 0:
                yield_portion = st.slider(
                    "Yield portion of remaining weight (%)",
                    0, 100, int((weight_yield / (weight_yield + weight_roi)) * 100) if (weight_yield + weight_roi) > 0 else 50,
                    help="Adjust the balance between Yield and ROI objectives"
                )
                remaining_for_yield_roi = 100 - weight_cost
                weight_yield = int((yield_portion / 100) * remaining_for_yield_roi)
                weight_roi = remaining_for_yield_roi - weight_yield
        
        # Always show balanced total
        st.success(f"✅ Auto-balanced objectives: Cost {weight_cost}%, Yield {weight_yield}%, ROI {weight_roi}% = 100%")
        
        # Configuration summary will be shown after parameter definitions
    
    # Financial parameters section
    st.write("**Financial Parameters**")
    
    # Get electricity price from project data (Step 1)
    electricity_rates = project_data.get('electricity_rates', {})
    electricity_price = electricity_rates.get('import_rate', 0.25)
    
    # Show rate source information
    rate_source = electricity_rates.get('source', 'default_fallback')
    if electricity_rates.get('live_rates_enabled'):
        st.info(f"💡 Using live electricity rate from Step 1: {electricity_price:.3f} €/kWh (Source: {rate_source})")
    else:
        st.info(f"💡 Using electricity rate from Step 1: {electricity_price:.3f} €/kWh (Source: {rate_source})")
    
    col3, col4 = st.columns(2)
    
    with col3:
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
        st.info("🔧 **All settings below directly affect the genetic algorithm optimization**")
        
        adv_col1, adv_col2 = st.columns(2)
        
        with adv_col1:
            prioritize_roi = st.checkbox(
                "Prioritize ROI over Coverage",
                value=True,
                help="✅ ACTIVE: Applies 20% boost to ROI fitness scores during optimization. Focuses algorithm on return on investment rather than maximum energy coverage.",
                key="prioritize_roi_opt"
            )
            
            include_maintenance = st.checkbox(
                "Include Maintenance Costs",
                value=True,
                help="✅ ACTIVE: Deducts 1.5% annual maintenance costs from ROI calculations. More realistic financial modeling but reduces apparent ROI.",
                key="include_maintenance_opt"
            )
        
        with adv_col2:
            orientation_preference = st.selectbox(
                "Orientation Preference",
                ["None", "South", "Southwest", "Southeast"],
                index=0,
                help="✅ ACTIVE: Applies up to 10% fitness bonus for solutions with preferred orientation. Algorithm favors systems facing the selected direction.",
                key="orientation_pref_opt"
            )
            
            system_size_preference = st.selectbox(
                "System Size Preference",
                ["Balanced", "Favor Large", "Favor Small"],
                index=0,
                help="✅ ACTIVE: Applies 5% fitness bonus based on average system capacity. Large: >2kW average, Small: <1kW average.",
                key="size_pref_opt"
            )
    
    # Show optimization parameters summary
    with st.expander("📋 Current Optimization Configuration Summary", expanded=False):
        st.write("**Objective Weights:**")
        st.write(f"• Minimize Cost: {weight_cost}%")
        st.write(f"• Maximize Yield: {weight_yield}%") 
        st.write(f"• Maximize ROI: {weight_roi}%")
        st.write("")
        st.write("**Algorithm Parameters:**")
        st.write(f"• Population Size: {population_size}")
        st.write(f"• Generations: {generations}")
        st.write(f"• Mutation Rate: {mutation_rate}%")
        st.write("")
        st.write("**Financial Constraints:**")
        st.write(f"• Maximum Investment: €{max_investment:,}")
        st.write(f"• Minimum Coverage: {min_coverage}%")
        st.write(f"• Electricity Price: €{electricity_price:.3f}/kWh")
        st.write("")
        st.write("**Advanced Settings (All Active in Algorithm):**")
        st.write(f"• Prioritize ROI: {'✅ Yes (+20% ROI boost)' if prioritize_roi else '❌ No'}")
        st.write(f"• Include Maintenance: {'✅ Yes (1.5% annual cost)' if include_maintenance else '❌ No'}")
        st.write(f"• Orientation Preference: {orientation_preference} {'(+10% bonus)' if orientation_preference != 'None' else ''}")
        st.write(f"• System Size Preference: {system_size_preference} {'(+5% bonus)' if system_size_preference != 'Balanced' else ''}")

    # Store variables in session state to ensure proper scope access
    if 'opt_max_investment' not in st.session_state:
        st.session_state.opt_max_investment = max_investment
    else:
        st.session_state.opt_max_investment = max_investment
    
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
                    'min_coverage': min_coverage / 100,
                    'weight_cost': weight_cost,
                    'weight_yield': weight_yield,
                    'weight_roi': weight_roi,
                    'prioritize_roi': prioritize_roi,
                    'include_maintenance': include_maintenance,
                    'orientation_preference': orientation_preference,
                    'system_size_preference': system_size_preference
                }
                
                # Filter systems by budget constraint
                if 'total_installation_cost' in pv_specs.columns:
                    cost_column = 'total_installation_cost'
                elif 'total_cost_eur' in pv_specs.columns:
                    cost_column = 'total_cost_eur'
                elif 'total_cost' in pv_specs.columns:
                    cost_column = 'total_cost'
                else:
                    st.error("Cost information not found in PV specifications data.")
                    return
                
                affordable_specs = pv_specs[pv_specs[cost_column] <= max_investment]
                
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
                
                # Save to consolidated data manager
                consolidated_manager = ConsolidatedDataManager()
                step8_data = {
                    'optimization_results': optimization_results,
                    'pareto_solutions': solutions_df.to_dict('records'),
                    'solutions': solutions_df.to_dict('records'),
                    'fitness_history': fitness_history,
                    'optimization_complete': True
                }
                consolidated_manager.save_step8_data(step8_data)
                
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
            
            # Weighted objectives summary
            config = optimization_data.get('optimization_config', {})
            financial_params = config.get('financial_params', {})
            
            st.info(f"""
            **Multi-Objective Optimization Results**
            Weighted objectives used: Cost {financial_params.get('weight_cost', 33)}%, 
            Yield {financial_params.get('weight_yield', 33)}%, 
            ROI {financial_params.get('weight_roi', 34)}%
            """)
            
            # Key metrics from best solutions
            best_solution = solutions.iloc[0]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Best Weighted Score", f"{best_solution.get('weighted_fitness', 0.0):.3f}")
            
            with col2:
                st.metric("Best Investment", f"€{best_solution['total_investment']:,.0f}")
            
            with col3:
                st.metric("Annual Energy", f"{best_solution['annual_energy_kwh']:,.0f} kWh")
            
            with col4:
                st.metric("Solutions Found", len(solutions))
            
            # Objectives breakdown visualization
            st.subheader("🎯 Multi-Objective Performance Analysis")
            
            # Create objectives breakdown chart
            if len(solutions) >= 3:
                top_solutions = solutions.head(3)
                
                # Calculate individual objective scores for top solutions
                objectives_data = []
                for _, sol in top_solutions.iterrows():
                    # Normalize scores (0-1 scale for visualization)
                    max_inv = st.session_state.get('opt_max_investment', 100000)
                    cost_score = 1 / (1 + sol['total_investment'] / max_inv) if max_inv > 0 else 0
                    yield_score = sol['annual_energy_kwh'] / solutions['annual_energy_kwh'].max() if solutions['annual_energy_kwh'].max() > 0 else 0
                    roi_score = min(sol['roi'] / 0.5, 1.0) if sol['roi'] > 0 else 0  # Cap at 50% ROI
                    
                    objectives_data.extend([
                        {'Solution': sol['solution_id'], 'Objective': 'Cost Efficiency', 'Score': cost_score * 100, 'Weight': financial_params.get('weight_cost', 33)},
                        {'Solution': sol['solution_id'], 'Objective': 'Energy Yield', 'Score': yield_score * 100, 'Weight': financial_params.get('weight_yield', 33)},
                        {'Solution': sol['solution_id'], 'Objective': 'ROI Performance', 'Score': roi_score * 100, 'Weight': financial_params.get('weight_roi', 34)}
                    ])
                
                objectives_df = pd.DataFrame(objectives_data)
                
                # Create grouped bar chart
                fig_objectives = px.bar(
                    objectives_df,
                    x='Solution',
                    y='Score',
                    color='Objective',
                    title="Multi-Objective Performance Breakdown (Top 3 Solutions)",
                    labels={'Score': 'Normalized Score (%)', 'Solution': 'Solution ID'},
                    text='Weight'
                )
                fig_objectives.update_traces(texttemplate='%{text}% weight', textposition='outside')
                fig_objectives.update_layout(height=400)
                st.plotly_chart(fig_objectives, use_container_width=True)
            
            # Solution selection and comparison
            st.subheader("📊 Detailed Solution Comparison")
            
            # Solutions table with weighted score
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
                if isinstance(selected_elements, list) and len(selected_elements) > 0:
                    # Display actual Element IDs directly (they're already correctly stored)
                    for element_id in selected_elements[:5]:  # Show first 5
                        st.write(f"• {element_id}")
                    if len(selected_elements) > 5:
                        st.write(f"• ... and {len(selected_elements) - 5} more")
                else:
                    st.write("No elements selected in this solution")
            
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
            
            # Add step-specific download button
            st.markdown("---")
            st.markdown("### 📄 Step 8 Analysis Report")
            st.markdown("Download detailed multi-objective optimization analysis report:")
            
            from utils.individual_step_reports import create_step_download_button
            create_step_download_button(8, "Optimization", "Download Optimization Analysis Report")
        
        else:
            st.warning("No optimization results available. Please run the optimization.")