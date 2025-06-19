import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from deap import base, creator, tools, algorithms
import random
import multiprocessing

def create_optimization_problem():
    """Create DEAP optimization problem for BIPV system optimization."""
    
    # Create fitness and individual classes if they don't exist
    if not hasattr(creator, "FitnessMulti"):
        creator.create("FitnessMulti", base.Fitness, weights=(1.0, -1.0))  # Maximize ROI, Minimize Net Import
    if not hasattr(creator, "Individual"):
        creator.create("Individual", list, fitness=creator.FitnessMulti)
    
    toolbox = base.Toolbox()
    
    # Individual represents binary selection of each PV-suitable element
    # 1 = install PV, 0 = don't install
    def create_individual(n_elements):
        return [random.randint(0, 1) for _ in range(n_elements)]
    
    return toolbox, creator.Individual

def evaluate_individual(individual, pv_specs, energy_balance, financial_params):
    """Evaluate fitness of an individual solution."""
    
    try:
        # Convert individual to selection mask
        selection_mask = np.array(individual, dtype=bool)
        
        if not any(selection_mask):
            return (0.0, float('inf'))  # No systems selected
        
        # Calculate selected systems metrics
        selected_specs = pv_specs[selection_mask]
        
        # Calculate total installation cost
        total_cost = selected_specs['total_installation_cost'].sum()
        
        # Calculate total annual yield
        total_annual_yield = selected_specs['annual_energy_kwh'].sum()
        
        # Calculate net import reduction
        original_net_import = energy_balance['net_import'].sum()
        new_net_import = max(0, original_net_import - total_annual_yield)
        net_import_reduction = original_net_import - new_net_import
        
        # Calculate annual savings
        electricity_price = financial_params.get('electricity_price', 0.12)
        annual_savings = net_import_reduction * electricity_price
        
        # Calculate ROI (simple payback consideration)
        if annual_savings > 0:
            roi = annual_savings / total_cost if total_cost > 0 else 0
        else:
            roi = 0
        
        # Fitness: (ROI, -Net Import)
        return (roi, -new_net_import)
    
    except Exception as e:
        return (0.0, float('inf'))

def run_genetic_algorithm(pv_specs, energy_balance, financial_params, ga_params):
    """Run genetic algorithm optimization."""
    
    n_elements = len(pv_specs)
    
    # Create toolbox
    toolbox, Individual = create_optimization_problem()
    
    # Register genetic operators
    toolbox.register("individual", lambda: Individual([random.randint(0, 1) for _ in range(n_elements)]))
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", evaluate_individual, 
                    pv_specs=pv_specs, energy_balance=energy_balance, financial_params=financial_params)
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", tools.mutFlipBit, indpb=ga_params['mutation_rate'])
    toolbox.register("select", tools.selNSGA2)
    
    # Initialize population
    population = toolbox.population(n=ga_params['population_size'])
    
    # Evaluate initial population
    fitnesses = list(map(toolbox.evaluate, population))
    for ind, fit in zip(population, fitnesses):
        ind.fitness.values = fit
    
    # Evolution tracking
    fitness_history = []
    best_individuals = []
    
    # Evolution loop
    for generation in range(ga_params['generations']):
        # Select next generation
        offspring = toolbox.select(population, len(population))
        offspring = list(map(toolbox.clone, offspring))
        
        # Apply crossover and mutation
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < ga_params.get('crossover_rate', 0.7):
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values
        
        for mutant in offspring:
            if random.random() < ga_params['mutation_rate']:
                toolbox.mutate(mutant)
                del mutant.fitness.values
        
        # Evaluate invalid individuals
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
        
        # Replace population
        population[:] = offspring
        
        # Track progress
        fitnesses = [ind.fitness.values for ind in population]
        if fitnesses:
            roi_values = [f[0] for f in fitnesses]
            net_import_values = [-f[1] for f in fitnesses]
            
            fitness_history.append({
                'generation': generation,
                'best_roi': max(roi_values) if roi_values else 0,
                'avg_roi': np.mean(roi_values) if roi_values else 0,
                'best_net_import': min(net_import_values) if net_import_values else 0,
                'avg_net_import': np.mean(net_import_values) if net_import_values else 0
            })
            
            # Track best individual
            best_idx = np.argmax(roi_values)
            best_individuals.append({
                'generation': generation,
                'individual': population[best_idx][:],
                'fitness': population[best_idx].fitness.values
            })
    
    # Get final results
    final_fitnesses = [ind.fitness.values for ind in population]
    pareto_front = tools.sortNondominated(population, len(population), first_front_only=True)[0]
    
    return population, pareto_front, fitness_history, best_individuals

def analyze_optimization_results(pareto_front, pv_specs, energy_balance, financial_params):
    """Analyze optimization results and generate alternatives."""
    
    results = []
    
    for i, individual in enumerate(pareto_front[:10]):  # Top 10 solutions
        selection_mask = np.array(individual, dtype=bool)
        
        if any(selection_mask):
            selected_specs = pv_specs[selection_mask]
            
            # Calculate metrics
            total_cost = selected_specs['total_installation_cost'].sum()
            total_yield = selected_specs['annual_energy_kwh'].sum()
            system_power = selected_specs['system_power_kw'].sum()
            
            # Energy impact
            original_demand = energy_balance['predicted_demand'].sum()
            original_net_import = energy_balance['net_import'].sum()
            new_net_import = max(0, original_net_import - total_yield)
            
            # Financial metrics
            electricity_price = financial_params.get('electricity_price', 0.12)
            annual_savings = (original_net_import - new_net_import) * electricity_price
            simple_payback = total_cost / annual_savings if annual_savings > 0 else float('inf')
            
            results.append({
                'solution_id': f"SOL_{i+1:02d}",
                'selected_elements': selection_mask.sum(),
                'total_elements': len(selection_mask),
                'system_power_kw': system_power,
                'annual_yield_kwh': total_yield,
                'installation_cost': total_cost,
                'annual_savings': annual_savings,
                'simple_payback_years': simple_payback,
                'net_import_reduction': original_net_import - new_net_import,
                'energy_independence': (total_yield / original_demand) * 100 if original_demand > 0 else 0,
                'roi': individual.fitness.values[0],
                'net_import': -individual.fitness.values[1],
                'selection_mask': selection_mask,
                'selected_element_ids': pv_specs[selection_mask]['element_id'].tolist()
            })
    
    return pd.DataFrame(results)

def render_optimization():
    """Render the genetic algorithm optimization module."""
    
    st.header("8. Optimization")
    st.markdown("Use genetic algorithms to optimize PV system selection for maximum ROI and minimum grid dependency.")
    
    # Check prerequisites
    prerequisites = ['pv_specifications', 'energy_balance']
    missing = [p for p in prerequisites if p not in st.session_state.project_data]
    
    if missing:
        st.warning(f"⚠️ Missing required data: {', '.join(missing)}")
        st.info("Please complete previous steps: PV specifications and yield analysis.")
        return
    
    # Load data
    pv_specs = pd.DataFrame(st.session_state.project_data['pv_specifications'])
    energy_balance = pd.DataFrame(st.session_state.project_data['energy_balance'])
    
    st.subheader("Optimization Configuration")
    
    # Genetic Algorithm Parameters
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Genetic Algorithm Settings**")
        
        population_size = st.number_input(
            "Population Size",
            value=50,
            min_value=20,
            max_value=200,
            step=10,
            help="Number of solutions in each generation"
        )
        
        generations = st.number_input(
            "Generations",
            value=30,
            min_value=10,
            max_value=100,
            step=5,
            help="Number of evolutionary generations"
        )
        
        mutation_rate = st.slider(
            "Mutation Rate",
            min_value=0.01,
            max_value=0.30,
            value=0.10,
            step=0.01,
            help="Probability of mutation for each gene"
        )
        
        crossover_rate = st.slider(
            "Crossover Rate",
            min_value=0.50,
            max_value=0.95,
            value=0.70,
            step=0.05,
            help="Probability of crossover between parents"
        )
    
    with col2:
        st.markdown("**Optimization Objectives**")
        
        roi_weight = st.slider(
            "ROI Weight",
            min_value=0.0,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="Weight for ROI maximization objective"
        )
        
        import_weight = st.slider(
            "Net Import Weight",
            min_value=0.0,
            max_value=2.0,
            value=1.0,
            step=0.1,
            help="Weight for net import minimization objective"
        )
        
        # Financial parameters
        st.markdown("**Financial Parameters**")
        
        electricity_price = st.number_input(
            "Electricity Price ($/kWh)",
            value=0.12,
            min_value=0.05,
            max_value=0.50,
            step=0.01,
            help="Current electricity price for savings calculation"
        )
        
        max_budget = st.number_input(
            "Maximum Budget ($)",
            value=int(pv_specs['total_installation_cost'].sum() * 0.8),
            min_value=0,
            step=1000,
            help="Maximum available budget for PV installation"
        )
    
    # Store parameters
    ga_params = {
        'population_size': population_size,
        'generations': generations,
        'mutation_rate': mutation_rate,
        'crossover_rate': crossover_rate,
        'roi_weight': roi_weight,
        'import_weight': import_weight
    }
    
    financial_params = {
        'electricity_price': electricity_price,
        'max_budget': max_budget
    }
    
    # Display current system overview
    st.subheader("Current System Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Available Elements", len(pv_specs))
    with col2:
        st.metric("Total Potential Power", f"{pv_specs['system_power_kw'].sum():.1f} kW")
    with col3:
        st.metric("Total Potential Cost", f"${pv_specs['total_installation_cost'].sum():,.0f}")
    with col4:
        st.metric("Annual Energy Potential", f"{pv_specs['annual_energy_kwh'].sum():,.0f} kWh")
    
    # Run optimization
    if st.button("Run Genetic Algorithm Optimization"):
        with st.spinner(f"Running optimization: {generations} generations with population of {population_size}..."):
            try:
                # Filter by budget constraint
                budget_feasible = pv_specs[pv_specs['total_installation_cost'] <= max_budget]
                
                if len(budget_feasible) == 0:
                    st.error("❌ No systems fit within the specified budget.")
                    return
                
                # Run GA optimization
                population, pareto_front, fitness_history, best_individuals = run_genetic_algorithm(
                    budget_feasible, energy_balance, financial_params, ga_params
                )
                
                # Analyze results
                optimization_results = analyze_optimization_results(
                    pareto_front, budget_feasible, energy_balance, financial_params
                )
                
                # Store results
                st.session_state.project_data['optimization_results'] = optimization_results.to_dict()
                st.session_state.project_data['fitness_history'] = fitness_history
                st.session_state.project_data['ga_params'] = ga_params
                st.session_state.project_data['financial_params'] = financial_params
                
                st.success(f"✅ Optimization completed! Found {len(optimization_results)} optimal solutions.")
                
                # Display top solution metrics
                if len(optimization_results) > 0:
                    best_solution = optimization_results.iloc[0]
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Best Solution Power", f"{best_solution['system_power_kw']:.1f} kW")
                    with col2:
                        st.metric("Installation Cost", f"${best_solution['installation_cost']:,.0f}")
                    with col3:
                        st.metric("Annual Savings", f"${best_solution['annual_savings']:,.0f}")
                    with col4:
                        st.metric("Payback Period", f"{best_solution['simple_payback_years']:.1f} years")
                
            except Exception as e:
                st.error(f"❌ Optimization failed: {str(e)}")
                return
    
    # Display optimization results
    if 'optimization_results' in st.session_state.project_data:
        results_df = pd.DataFrame(st.session_state.project_data['optimization_results'])
        fitness_history = st.session_state.project_data['fitness_history']
        
        st.subheader("Optimization Results")
        
        # Evolution progress
        if fitness_history:
            history_df = pd.DataFrame(fitness_history)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_roi_evolution = px.line(
                    history_df,
                    x='generation',
                    y=['best_roi', 'avg_roi'],
                    title='ROI Evolution Over Generations',
                    labels={'value': 'ROI', 'generation': 'Generation'}
                )
                st.plotly_chart(fig_roi_evolution, use_container_width=True)
            
            with col2:
                fig_import_evolution = px.line(
                    history_df,
                    x='generation',
                    y=['best_net_import', 'avg_net_import'],
                    title='Net Import Evolution Over Generations',
                    labels={'value': 'Net Import (kWh)', 'generation': 'Generation'}
                )
                st.plotly_chart(fig_import_evolution, use_container_width=True)
        
        # Pareto front analysis
        st.subheader("Pareto Optimal Solutions")
        
        # Top solutions table
        display_cols = ['solution_id', 'selected_elements', 'system_power_kw', 'installation_cost',
                       'annual_savings', 'simple_payback_years', 'energy_independence']
        
        display_results = results_df[display_cols].copy()
        display_results['installation_cost'] = display_results['installation_cost'].apply(lambda x: f"${x:,.0f}")
        display_results['annual_savings'] = display_results['annual_savings'].apply(lambda x: f"${x:,.0f}")
        display_results['energy_independence'] = display_results['energy_independence'].apply(lambda x: f"{x:.1f}%")
        
        display_results.columns = ['Solution', 'Elements', 'Power (kW)', 'Cost', 'Savings', 'Payback (years)', 'Independence']
        
        st.dataframe(display_results, use_container_width=True)
        
        # Solution comparison
        st.subheader("Solution Comparison")
        
        # Pareto front visualization
        fig_pareto = px.scatter(
            results_df,
            x='simple_payback_years',
            y='energy_independence',
            size='system_power_kw',
            color='annual_savings',
            hover_data=['solution_id', 'selected_elements'],
            title='Pareto Front: Payback vs Energy Independence',
            labels={
                'simple_payback_years': 'Payback Period (years)',
                'energy_independence': 'Energy Independence (%)',
                'annual_savings': 'Annual Savings ($)'
            }
        )
        st.plotly_chart(fig_pareto, use_container_width=True)
        
        # Cost vs benefit analysis
        fig_cost_benefit = px.scatter(
            results_df,
            x='installation_cost',
            y='annual_savings',
            size='system_power_kw',
            color='simple_payback_years',
            hover_data=['solution_id'],
            title='Cost vs Benefit Analysis',
            labels={
                'installation_cost': 'Installation Cost ($)',
                'annual_savings': 'Annual Savings ($)',
                'simple_payback_years': 'Payback (years)'
            }
        )
        st.plotly_chart(fig_cost_benefit, use_container_width=True)
        
        # Detailed solution analysis
        st.subheader("Detailed Solution Analysis")
        
        selected_solution = st.selectbox(
            "Select Solution for Details",
            results_df['solution_id'].tolist(),
            help="Choose a solution to view detailed breakdown"
        )
        
        if selected_solution:
            solution_data = results_df[results_df['solution_id'] == selected_solution].iloc[0]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**System Configuration**")
                st.write(f"Selected Elements: {solution_data['selected_elements']} of {solution_data['total_elements']}")
                st.write(f"Total System Power: {solution_data['system_power_kw']:.1f} kW")
                st.write(f"Annual Energy Production: {solution_data['annual_yield_kwh']:,.0f} kWh")
                st.write(f"Energy Independence: {solution_data['energy_independence']:.1f}%")
            
            with col2:
                st.markdown("**Financial Analysis**")
                st.write(f"Installation Cost: ${solution_data['installation_cost']:,.0f}")
                st.write(f"Annual Savings: ${solution_data['annual_savings']:,.0f}")
                st.write(f"Simple Payback: {solution_data['simple_payback_years']:.1f} years")
                st.write(f"Net Import Reduction: {solution_data['net_import_reduction']:,.0f} kWh")
            
            # Selected elements details
            if 'selected_element_ids' in solution_data and solution_data['selected_element_ids']:
                st.markdown("**Selected PV Elements**")
                selected_elements = pv_specs[pv_specs['element_id'].isin(solution_data['selected_element_ids'])]
                
                element_summary = selected_elements[['element_id', 'orientation', 'system_power_kw', 
                                                   'annual_energy_kwh', 'total_installation_cost']].copy()
                element_summary['total_installation_cost'] = element_summary['total_installation_cost'].apply(lambda x: f"${x:,.0f}")
                element_summary.columns = ['Element ID', 'Orientation', 'Power (kW)', 'Annual Energy (kWh)', 'Cost']
                
                st.dataframe(element_summary, use_container_width=True)
        
        # Export results
        st.subheader("Export Optimization Results")
        
        if st.button("Export Optimization Results"):
            csv_data = results_df.to_csv(index=False)
            st.download_button(
                label="Download Optimization Results CSV",
                data=csv_data,
                file_name="bipv_optimization_results.csv",
                mime="text/csv"
            )
        
        st.success("✅ Optimization analysis completed! Ready for financial analysis.")
        
    else:
        st.info("👆 Please run the genetic algorithm optimization to find optimal PV configurations.")
        
        # Show optimization info
        with st.expander("🔧 About Genetic Algorithm Optimization"):
            st.markdown("""
            **The genetic algorithm will:**
            1. Create a population of potential PV system configurations
            2. Evaluate each configuration for ROI and net import reduction
            3. Evolve solutions over multiple generations using:
               - Selection (choosing best performers)
               - Crossover (combining good solutions)
               - Mutation (introducing random variations)
            4. Find Pareto-optimal solutions balancing multiple objectives
            
            **Optimization objectives:**
            - **Maximize ROI**: Return on investment from energy savings
            - **Minimize Net Import**: Reduce grid dependency
            - **Budget Constraint**: Stay within specified budget limits
            
            **Key features:**
            - Multi-objective optimization using NSGA-II algorithm
            - Real-time evolution tracking
            - Multiple optimal solutions for comparison
            - Detailed financial and energy analysis
            """)
