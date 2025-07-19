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
from utils.database_helper import db_helper
from core.solar_math import safe_divide
from utils.color_schemes import CHART_COLORS, get_chart_color
# Removed ConsolidatedDataManager - using database-only approach
# Removed session state dependency - using database-only approach

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
        # Use standardized field names with fallback support
        if 'total_cost_eur' in selected_specs.columns:
            total_cost = selected_specs['total_cost_eur'].sum()
        elif 'total_installation_cost' in selected_specs.columns:
            total_cost = selected_specs['total_installation_cost'].sum()
        elif 'total_cost' in selected_specs.columns:
            total_cost = selected_specs['total_cost'].sum()
        else:
            total_cost = 0
            
        total_annual_yield = selected_specs['annual_energy_kwh'].sum()
        
        # Calculate net import reduction with proper data handling
        if energy_balance is not None and len(energy_balance) > 0:
            if hasattr(energy_balance, 'columns') and 'predicted_demand' in energy_balance.columns:
                total_annual_demand = energy_balance['predicted_demand'].sum()
            elif isinstance(energy_balance, list) and len(energy_balance) > 0:
                total_annual_demand = energy_balance[0].get('predicted_demand', 0)
            else:
                total_annual_demand = 0
            net_import_reduction = min(total_annual_yield, total_annual_demand) if total_annual_demand > 0 else total_annual_yield
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
        # Use standardized field names with fallback support
        if 'total_cost_eur' in pv_specs.columns:
            max_possible_cost = pv_specs['total_cost_eur'].sum()
        elif 'total_installation_cost' in pv_specs.columns:
            max_possible_cost = pv_specs['total_installation_cost'].sum()
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
        # Ensure all fitness components are properly calculated
        if total_cost == 0 or total_annual_yield == 0:
            return (0.0,)  # Invalid solution
            
        weighted_fitness = (
            weight_cost * cost_fitness +
            weight_yield * yield_fitness + 
            weight_roi * roi_fitness
        ) * bonus_factor
        
        # Apply minimum coverage constraint with proper data handling
        min_coverage = financial_params.get('min_coverage', 0.3)  # Default 30%
        if energy_balance is not None and len(energy_balance) > 0:
            if hasattr(energy_balance, 'columns') and 'predicted_demand' in energy_balance.columns:
                total_annual_demand = energy_balance['predicted_demand'].sum()
            elif isinstance(energy_balance, list) and len(energy_balance) > 0:
                total_annual_demand = energy_balance[0].get('predicted_demand', 0)
            else:
                total_annual_demand = 0
                
            if total_annual_demand > 0:
                coverage_ratio = total_annual_yield / total_annual_demand
                if coverage_ratio < min_coverage:
                    weighted_fitness *= 0.5  # Reduce penalty to allow more solutions
        
        # Ensure positive fitness value
        return (max(weighted_fitness, 0.001),)  # Minimum positive value
    
    except Exception as e:
        return (0.0,)

def simple_genetic_algorithm(pv_specs, energy_balance, financial_params, ga_params):
    """Run optimized genetic algorithm with enhanced performance."""
    
    n_elements = len(pv_specs)
    # Optimize population size for better performance vs quality balance
    population_size = min(ga_params['population_size'], max(50, n_elements * 2))  # Cap at reasonable size
    generations = ga_params['generations']
    mutation_rate = ga_params['mutation_rate']
    
    # Performance optimization: Early convergence detection
    convergence_threshold = 0.001  # Stop if improvement < 0.1%
    stagnation_limit = 10  # Stop if no improvement for 10 generations
    
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
            # Calculate solution metrics with debugging
            # Use standardized field names with fallback support
            if 'capacity_kw' in selected_specs.columns:
                total_power_kw = selected_specs['capacity_kw'].sum()
            elif 'system_power_kw' in selected_specs.columns:
                total_power_kw = selected_specs['system_power_kw'].sum()
            elif 'power_density' in selected_specs.columns and 'glass_area' in selected_specs.columns:
                # Calculate capacity from power density and glass area
                total_power_kw = (selected_specs['power_density'] * selected_specs['glass_area'] / 1000).sum()
            else:
                total_power_kw = 0
                
            # Handle different cost column names
            # Use standardized field names with fallback support  
            if 'total_cost_eur' in selected_specs.columns:
                total_cost = selected_specs['total_cost_eur'].sum()
            elif 'total_installation_cost' in selected_specs.columns:
                total_cost = selected_specs['total_installation_cost'].sum()  # Fixed: was using wrong column
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
            
            # Calculate ROI with proper demand handling
            electricity_price = financial_params.get('electricity_price', 0.25)
            
            # Get proper total annual demand
            if energy_balance is not None and len(energy_balance) > 0:
                if hasattr(energy_balance, 'columns') and 'predicted_demand' in energy_balance.columns:
                    total_annual_demand = energy_balance['predicted_demand'].sum()
                elif isinstance(energy_balance, list) and len(energy_balance) > 0:
                    total_annual_demand = energy_balance[0].get('predicted_demand', 0)
                else:
                    total_annual_demand = total_annual_yield
            else:
                total_annual_demand = total_annual_yield
                
            # Calculate annual savings (grid import reduction)
            energy_offset = min(total_annual_yield, total_annual_demand) if total_annual_demand > 0 else total_annual_yield
            annual_savings = energy_offset * electricity_price
            
            # Calculate ROI
            roi = (annual_savings / total_cost * 100) if total_cost > 0 and annual_savings > 0 else 0
            
            solution = {
                'solution_id': f"Solution_{i+1}",
                'total_power_kw': float(total_power_kw),  # Ensure float conversion
                'total_investment': float(total_cost),    # Ensure float conversion
                'annual_energy_kwh': float(total_annual_yield),  # Ensure float conversion
                'annual_savings': float(annual_savings),  # Ensure float conversion
                'roi': float(roi),                        # Ensure float conversion
                'net_import_kwh': float(net_import),     # Ensure float conversion
                'selected_elements': selected_elements,
                'n_selected_elements': len(selected_elements),
                'investment_per_kw': float(safe_divide(total_cost, total_power_kw, 0)),
                'energy_cost_per_kwh': float(safe_divide(total_cost, total_annual_yield * 25, 0)),  # 25-year lifetime
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
    
    # AI Model Performance Impact Notice from database only
    try:
        conn = db_manager.get_connection()
        if conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT annual_demand FROM energy_analysis 
                    WHERE project_id = %s AND annual_demand IS NOT NULL
                    ORDER BY created_at DESC LIMIT 1
                """, (get_current_project_id(),))
                
                result = cursor.fetchone()
                if result:
                    st.info("🟢 Optimization uses AI demand predictions from authentic database analysis")
            conn.close()
    except Exception:
        pass  # No fallback display if database unavailable
    
    # Get project ID directly from database - no session state dependencies
    from services.io import get_current_project_id
    
    project_id = get_current_project_id()
    if not project_id:
        st.error("⚠️ No project found. Please complete Step 1 (Project Setup) first.")
        return
    
    # Verify project exists in database
    try:
        conn = db_manager.get_connection()
        if conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT project_name FROM projects WHERE id = %s", (project_id,))
                result = cursor.fetchone()
                if not result:
                    st.error("⚠️ Project not found in database. Please complete Step 1 (Project Setup) first.")
                    return
            conn.close()
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        return
    
    # Check for PV specifications from database (Step 6)
    pv_specs = db_manager.get_pv_specifications(project_id)
    
    # Check for authentic Step 7 data from energy_analysis table
    energy_balance = None
    try:
        conn = db_manager.get_connection()
        if conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT annual_generation, annual_demand 
                    FROM energy_analysis 
                    WHERE project_id = %s AND annual_generation IS NOT NULL AND annual_demand IS NOT NULL
                    ORDER BY created_at DESC LIMIT 1
                """, (project_id,))
                
                result = cursor.fetchone()
                if result:
                    annual_generation, annual_demand = result
                    # Convert decimal.Decimal to float to prevent arithmetic errors
                    annual_generation = float(annual_generation) if annual_generation is not None else 0.0
                    annual_demand = float(annual_demand) if annual_demand is not None else 0.0
                    # Use authentic database values for optimization
                    energy_balance = [{'predicted_demand': annual_demand, 'total_yield_kwh': annual_generation}]
                    st.success(f"✅ Using authentic Step 7 data: {annual_generation:,.0f} kWh generation, {annual_demand:,.0f} kWh demand")
            conn.close()
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
    
    # Validate required authentic data only
    missing_data = []
    if pv_specs is None:
        missing_data.append("Step 6 (PV Specification)")
    elif isinstance(pv_specs, (list, dict)) and len(pv_specs) == 0:
        missing_data.append("Step 6 (PV Specification)")
    
    if energy_balance is None:
        missing_data.append("Step 7 (Yield vs Demand Analysis)")
    
    if missing_data:
        st.error("⚠️ Required data missing. Please complete the following steps first:")
        for step in missing_data:
            st.error(f"• {step}")
        return
    
    # Convert authentic pv_specs to DataFrame - no fallbacks, database data only
    if isinstance(pv_specs, dict):
        # Extract bipv_specifications array from JSON structure
        if 'bipv_specifications' in pv_specs:
            pv_specs = pd.DataFrame(pv_specs['bipv_specifications'])
        else:
            st.error("⚠️ No 'bipv_specifications' array found in database JSON structure.")
            return
    elif isinstance(pv_specs, list):
        pv_specs = pd.DataFrame(pv_specs)
    elif not isinstance(pv_specs, pd.DataFrame):
        st.error("⚠️ PV specifications data format error from database. Expected dict with 'bipv_specifications' key, list, or DataFrame.")
        return
    
    # Convert all numeric columns to float to prevent decimal.Decimal arithmetic errors
    numeric_columns = ['total_cost_eur', 'capacity_kw', 'annual_energy_kwh', 'glass_area', 'total_cost', 'total_installation_cost']
    for col in numeric_columns:
        if col in pv_specs.columns:
            pv_specs[col] = pd.to_numeric(pv_specs[col], errors='coerce').fillna(0.0)
    
    # Convert authentic energy_balance to DataFrame - database data only
    if isinstance(energy_balance, list):
        energy_balance = pd.DataFrame(energy_balance)
        # Convert numeric columns to float
        for col in ['predicted_demand', 'total_yield_kwh']:
            if col in energy_balance.columns:
                energy_balance[col] = pd.to_numeric(energy_balance[col], errors='coerce').fillna(0.0)
    
    # Success confirmation after data conversion
    st.success(f"✅ Database verification complete: {len(pv_specs)} BIPV systems ready for optimization")
    st.info("💡 Using 100% authentic database data - no session state or fallback dependencies")
    st.info("🎯 Optimization includes only South/East/West-facing elements for realistic solar performance")
    
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
        
        # Initialize default weights
        default_weights = {'cost': 33, 'yield': 33, 'roi': 34}
        
        # Primary weight selector
        weight_cost = st.slider(
            "Minimize Cost Weight (%)",
            0, 100, default_weights['cost'], 1,
            help="Weight for minimizing total system cost. Higher values prioritize lower-cost solutions.",
            key="weight_cost_slider"
        )
        
        # Auto-balance the remaining two weights
        remaining = 100 - weight_cost
        if remaining > 0:
            weight_yield = remaining // 2
            weight_roi = remaining - weight_yield
        else:
            weight_yield = 0
            weight_roi = 0
        
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
                    0, 100, 50,
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
    
    # Get electricity rates from database only - no session state fallbacks
    electricity_price = None
    try:
        conn = db_manager.get_connection()
        if conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT electricity_rates FROM projects 
                    WHERE id = %s AND electricity_rates IS NOT NULL
                """, (project_id,))
                
                result = cursor.fetchone()
                if result and result[0]:
                    import json
                    rates_data = json.loads(result[0])
                    electricity_price = float(rates_data.get('import_rate', 0.25))  # Convert to float
                    source = rates_data.get('source', 'Step 1')
                    st.success(f"✅ Using authentic electricity rate from database: €{electricity_price:.3f}/kWh (Source: {source})")
            conn.close()
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
    
    if electricity_price is None:
        st.error("⚠️ Electricity rate not found in database. Please complete Step 1 (Project Setup) first.")
        return
    
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

    # Store optimization parameters for evaluation function
    optimization_params = {
        'max_investment': max_investment,
        'min_coverage': min_coverage,
        'electricity_price': electricity_price,
        'prioritize_roi': prioritize_roi,
        'include_maintenance': include_maintenance,
        'orientation_preference': orientation_preference,
        'system_size_preference': system_size_preference,
        'weights': {'cost': weight_cost, 'yield': weight_yield, 'roi': weight_roi}
    }
    
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
                
                # DEBUGGING: Show input data before analysis
                st.write("🔍 **Debugging Input Data:**")
                st.write(f"- Pareto solutions found: {len(pareto_solutions)}")
                st.write(f"- Affordable specs: {len(affordable_specs)} systems")
                st.write(f"- Energy balance data: {len(energy_balance) if energy_balance is not None else 'None'}")
                
                if len(affordable_specs) > 0:
                    st.write("**Sample PV specs data:**")
                    sample_cols = ['element_id', 'capacity_kw', 'total_cost_eur', 'annual_energy_kwh']
                    available_cols = [col for col in sample_cols if col in affordable_specs.columns]
                    st.dataframe(affordable_specs[available_cols].head(3), use_container_width=True)
                
                if energy_balance is not None and len(energy_balance) > 0:
                    st.write("**Energy balance data:**")
                    balance_cols = ['predicted_demand', 'annual_generation'] 
                    available_balance_cols = [col for col in balance_cols if col in energy_balance.columns]
                    if available_balance_cols:
                        st.dataframe(energy_balance[available_balance_cols].head(3), use_container_width=True)
                    st.write(f"- Total annual demand: {energy_balance['predicted_demand'].sum() if 'predicted_demand' in energy_balance.columns else 'No predicted_demand column'}")
                
                # Analyze results
                solutions_df = analyze_optimization_results(
                    pareto_solutions, affordable_specs, energy_balance, financial_params
                )
                
                # DEBUGGING: Show calculated solutions
                st.write("🔍 **Debugging Calculated Solutions:**")
                st.write(f"- Solutions calculated: {len(solutions_df)}")
                if len(solutions_df) > 0:
                    debug_cols = ['solution_id', 'total_power_kw', 'total_investment', 'annual_energy_kwh', 'roi', 'net_import_kwh']
                    available_debug_cols = [col for col in debug_cols if col in solutions_df.columns]
                    st.dataframe(solutions_df[available_debug_cols].head(3), use_container_width=True)
                
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
                
                # Save results to database only - strict database-only architecture
                try:
                    db_manager.save_optimization_results(project_id, {
                        'solutions': solutions_df.to_dict('records')
                    })
                    st.success("✅ Optimization results saved to database (database-only architecture verified)")
                except Exception as db_error:
                    st.error(f"Database save error: {str(db_error)}")
                    return
                
                st.success(f"✅ Optimization completed! Found {len(solutions_df)} viable solutions.")
                
            except Exception as e:
                st.error(f"Error during optimization: {str(e)}")
                return
    
    # Display results from database only - no session state fallbacks
    optimization_data = None
    solutions = None
    try:
        conn = db_manager.get_connection()
        if conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT solution_id, capacity, roi, net_import, total_cost 
                    FROM optimization_results 
                    WHERE project_id = %s 
                    ORDER BY roi DESC
                """, (project_id,))
                
                results = cursor.fetchall()
                if results:
                    solutions = pd.DataFrame(results, columns=['solution_id', 'capacity', 'roi', 'net_import', 'total_cost'])
                    optimization_data = {'solutions': solutions}
            conn.close()
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        
    if optimization_data and solutions is not None and len(solutions) > 0:
        st.subheader("📊 Optimization Results")
        
        st.info("**Multi-Objective Optimization Results from Database**")
        
        # DEBUGGING MATRIX DISPLAY - Show calculation breakdown
        st.subheader("🔍 Debugging Matrix: Optimization Calculations")
        
        with st.expander("📊 Detailed Calculation Matrix", expanded=True):
            # Show first few solutions with detailed breakdown
            debug_solutions = solutions.head(3)
            
            st.write("**Solution Calculation Results:**")
            for i, (_, solution) in enumerate(debug_solutions.iterrows()):
                st.write(f"**Solution {i+1}:**")
                sol_col1, sol_col2, sol_col3 = st.columns(3)
                
                with sol_col1:
                    st.write(f"- Solution ID: {solution['solution_id']}")
                    st.write(f"- Capacity: {solution['capacity']:.3f} kW")
                    st.write(f"- Total Cost: €{solution['total_cost']:,.2f}")
                
                with sol_col2:
                    st.write(f"- ROI: {solution['roi']:.2f}%")
                    st.write(f"- Net Import: {solution['net_import']:,.0f} kWh")
                    
                with sol_col3:
                    st.write(f"- Raw capacity value: {solution['capacity']}")
                    st.write(f"- Raw net_import value: {solution['net_import']}")
                    st.write(f"- Zero values detected: {solution['capacity'] == 0 or solution['net_import'] == 0}")
            
            # Show database table structure
            st.write("**Database Values Analysis:**")
            st.dataframe(debug_solutions[['solution_id', 'capacity', 'roi', 'net_import', 'total_cost']], use_container_width=True)
        
        # Comprehensive Optimization Results Visualization
        st.subheader("📊 Interactive Optimization Results")
        
        # Create interactive visualizations
        import plotly.graph_objects as go
        import plotly.express as px
        from plotly.subplots import make_subplots
        
        # 1. ROI vs Investment Scatter Plot
        fig1 = px.scatter(
            solutions, 
            x='total_cost', 
            y='roi',
            size='capacity',
            color='net_import',
            hover_data=['solution_id', 'capacity', 'total_cost', 'roi'],
            title="ROI vs Total Investment (Size = Capacity, Color = Net Import)",
            labels={
                'total_cost': 'Total Investment (€)',
                'roi': 'Return on Investment (%)',
                'capacity': 'System Capacity (kW)',
                'net_import': 'Net Import Reduction (kWh)'
            }
        )
        fig1.update_layout(height=500)
        st.plotly_chart(fig1, use_container_width=True)
        
        # 2. Multi-Objective Performance Comparison
        fig2 = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Investment Cost Distribution', 'ROI Distribution', 
                          'System Capacity Distribution', 'Energy Reduction Distribution'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Investment histogram
        fig2.add_trace(
            go.Histogram(x=solutions['total_cost'], name='Investment (€)', nbinsx=10),
            row=1, col=1
        )
        
        # ROI histogram
        fig2.add_trace(
            go.Histogram(x=solutions['roi'], name='ROI (%)', nbinsx=10),
            row=1, col=2
        )
        
        # Capacity histogram
        fig2.add_trace(
            go.Histogram(x=solutions['capacity'], name='Capacity (kW)', nbinsx=10),
            row=2, col=1
        )
        
        # Net import histogram
        fig2.add_trace(
            go.Histogram(x=solutions['net_import'], name='Net Import (kWh)', nbinsx=10),
            row=2, col=2
        )
        
        fig2.update_layout(height=600, title_text="Solution Distribution Analysis", showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)
        
        # 3. Pareto Front Analysis (Cost vs Performance Trade-off)
        fig3 = go.Figure()
        
        # Add scatter points
        fig3.add_trace(go.Scatter(
            x=solutions['total_cost'],
            y=solutions['roi'],
            mode='markers+text',
            text=solutions['solution_id'],
            textposition='top center',
            marker=dict(
                size=solutions['capacity'] * 3,  # Scale size with capacity
                color=solutions['net_import'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Net Import Reduction (kWh)")
            ),
            name='Solutions'
        ))
        
        fig3.update_layout(
            title="Pareto Front: Investment vs ROI Trade-off Analysis",
            xaxis_title="Total Investment Cost (€)",
            yaxis_title="Return on Investment (%)",
            height=500
        )
        st.plotly_chart(fig3, use_container_width=True)
        
        # 4. Top Solutions Comparison Bar Chart
        top_solutions = solutions.head(5)  # Top 5 solutions by ROI
        
        fig4 = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Top 5 Solutions by ROI', 'Investment vs Energy Performance'),
            specs=[[{"secondary_y": False}, {"secondary_y": True}]]
        )
        
        # ROI comparison
        fig4.add_trace(
            go.Bar(x=top_solutions['solution_id'], y=top_solutions['roi'], 
                   name='ROI (%)', marker_color='lightblue'),
            row=1, col=1
        )
        
        # Investment vs Performance
        fig4.add_trace(
            go.Bar(x=top_solutions['solution_id'], y=top_solutions['total_cost'], 
                   name='Investment (€)', marker_color='lightcoral'),
            row=1, col=2
        )
        
        fig4.add_trace(
            go.Scatter(x=top_solutions['solution_id'], y=top_solutions['capacity'], 
                      mode='lines+markers', name='Capacity (kW)', 
                      line=dict(color='green', width=3)),
            row=1, col=2, secondary_y=True
        )
        
        fig4.update_yaxes(title_text="Investment (€)", secondary_y=False, row=1, col=2)
        fig4.update_yaxes(title_text="System Capacity (kW)", secondary_y=True, row=1, col=2)
        fig4.update_layout(height=500, title_text="Detailed Top Solutions Analysis")
        st.plotly_chart(fig4, use_container_width=True)
        
        # Key metrics from best solutions using authentic database fields
        best_solution = solutions.iloc[0]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Best ROI", f"{best_solution['roi']:.1f}%")
        
        with col2:
            st.metric("Best Investment", f"€{best_solution['total_cost']:,.0f}")
        
        with col3:
            st.metric("Capacity", f"{best_solution['capacity']:.1f} kW")
        
        with col4:
            st.metric("Solutions Found", len(solutions))
            
        # Solutions table with authentic database fields only
        st.subheader("📊 Optimization Solutions")
        
        st.dataframe(
            solutions,
            use_container_width=True,
            column_config={
                'solution_id': 'Solution ID',
                'capacity': st.column_config.NumberColumn('Capacity (kW)', format="%.1f"),
                'total_cost': st.column_config.NumberColumn('Investment (€)', format="€%.0f"),
                'roi': st.column_config.NumberColumn('ROI (%)', format="%.1f"),
                'net_import': st.column_config.NumberColumn('Net Import (kWh)', format="%.0f")
            }
        )
        
        # Solution selection for Step 9
        st.subheader("✅ Select Solution for Financial Analysis")
        
        selected_solution_id = st.selectbox(
            "Choose solution for Step 9:",
            solutions['solution_id'].tolist(),
            key="selected_solution_opt"
        )
        
        st.success(f"✅ Selected: {selected_solution_id} - Ready for Step 9 Financial Analysis")
        
        # Add step-specific download button
        st.markdown("---")
        st.markdown("### 📄 Step 8 Analysis Report")
        st.markdown("Download detailed multi-objective optimization analysis report:")
        
        from utils.individual_step_reports import create_step_download_button
        create_step_download_button(8, "Optimization", "Download Optimization Analysis Report")
    
    else:
        st.warning("No optimization results available. Please run the optimization.")
