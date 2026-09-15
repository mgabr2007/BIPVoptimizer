"""Weighted genetic search; outputs are not a Pareto front. No Streamlit/DB I/O."""
import random
import numpy as np
import pandas as pd
from core.energy_contracts import annual_element_yield, annual_netting, BALANCE_METHOD, ENERGY_MODEL_VERSION

def safe_divide(numerator, denominator, default=0.0):
    return numerator / denominator if denominator else default

def create_individual(n_elements, rng=None):
    """Create a random individual for genetic algorithm."""
    rng = rng or random.Random()
    return [rng.randint(0, 1) for _ in range(n_elements)]

def evaluate_individual(individual, pv_specs, energy_balance, financial_params, radiation_lookup=None):
    """Evaluate fitness of an individual solution using weighted multi-objective approach."""
    
    try:
        # Convert individual to selection mask
        selection_mask = np.array(individual, dtype=bool)
        
        if not any(selection_mask):
            return (0.0,)  # No systems selected - return single fitness value
        
        # Calculate selected systems metrics
        selected_specs = pv_specs[selection_mask]
        
        # Calculate total metrics using ONLY authentic standardized data
        if 'total_cost_eur' in selected_specs.columns:
            total_cost = selected_specs['total_cost_eur'].sum()
        else:
            raise ValueError("Optimization requires authentic cost data with 'total_cost_eur' field from Step 6")
            
        # Calculate authentic annual yield using Step 5 radiation data ONLY
        if not radiation_lookup:
            # CRITICAL: No fallback data allowed - require authentic Step 5 radiation data
            raise ValueError("Optimization requires authentic radiation data from Step 5. Please complete radiation analysis first.")
        
        total_annual_yield = sum(annual_element_yield(row, radiation_lookup[str(row['element_id'])])
                                 for _, row in selected_specs.iterrows())

        # Calculate net import reduction with proper data handling
        if energy_balance is not None and len(energy_balance) > 0:
            if hasattr(energy_balance, 'columns') and 'predicted_demand' in energy_balance.columns:
                total_annual_demand = energy_balance['predicted_demand'].sum()
            elif isinstance(energy_balance, list) and len(energy_balance) > 0:
                total_annual_demand = sum(float(row['predicted_demand']) for row in energy_balance)
            else:
                total_annual_demand = 0
            net_import_reduction = min(total_annual_yield, total_annual_demand) if total_annual_demand > 0 else total_annual_yield
        else:
            net_import_reduction = total_annual_yield
        
        # Calculate annual savings and ROI using authentic electricity rates
        electricity_price = financial_params.get('electricity_price')
        if electricity_price is None:
            raise ValueError("Optimization requires authentic electricity rates from project configuration")
        annual_savings = annual_netting(total_annual_yield, total_annual_demand,
                                        electricity_price, financial_params['export_rate'])['gross_benefit']
        
        # Include maintenance costs if enabled
        include_maintenance = financial_params.get('include_maintenance', True)
        if include_maintenance:
            # Apply typical BIPV maintenance cost (1-2% of investment annually)
            annual_maintenance = total_cost * financial_params.get('maintenance_rate', 0.015)  # 1.5% annual maintenance
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
        # Use ONLY standardized field names - no fallbacks allowed
        if 'total_cost_eur' in pv_specs.columns:
            max_possible_cost = pv_specs['total_cost_eur'].sum()
        else:
            raise ValueError("Optimization requires authentic cost data with 'total_cost_eur' field from Step 6")
            
        normalized_cost = total_cost / max_possible_cost if max_possible_cost > 0 else 0
        cost_fitness = 1 / (1 + normalized_cost)  # Higher is better
        
        # For yield: higher is better
        max_possible_yield = sum(annual_element_yield(row, radiation_lookup[str(row['element_id'])])
                                 for _, row in pv_specs.iterrows())
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
                total_annual_demand = sum(float(row['predicted_demand']) for row in energy_balance)
            else:
                total_annual_demand = 0
                
            if total_annual_demand > 0:
                coverage_ratio = total_annual_yield / total_annual_demand
                if coverage_ratio < min_coverage:
                    return (0.0,)  # Required coverage is a feasibility constraint
        
        # Ensure positive fitness value
        return (max(weighted_fitness, 0.001),)  # Minimum positive value
    
    except (KeyError, TypeError, ValueError) as e:
        raise ValueError(f"Invalid optimization input: {e}") from e

def simple_genetic_algorithm(pv_specs, energy_balance, financial_params, ga_params, radiation_lookup=None):
    """Run optimized genetic algorithm with enhanced performance."""
    
    n_elements = len(pv_specs)
    if n_elements < 1:
        raise ValueError("At least one eligible PV element is required")
    required = {'element_id', 'glass_area_m2', 'efficiency', 'bipv_area_m2', 'total_cost_eur'}
    if not required.issubset(pv_specs.columns):
        raise ValueError(f"Missing PV fields: {sorted(required - set(pv_specs.columns))}")
    if pv_specs['element_id'].astype(str).duplicated().any():
        raise ValueError("PV element IDs must be unique")
    numeric = pv_specs[list(required - {'element_id'})].astype(float).to_numpy()
    if not np.isfinite(numeric).all() or (numeric < 0).any():
        raise ValueError("PV inputs must be finite and nonnegative")
    if not radiation_lookup or any(str(i) not in radiation_lookup for i in pv_specs['element_id']):
        raise ValueError("Step 5 radiation is required for every PV element")
    if any(not np.isfinite(float(v)) or float(v) < 0 for v in radiation_lookup.values()):
        raise ValueError("Radiation must be finite and nonnegative")
    for _, row in pv_specs.iterrows():
        annual_element_yield(row, radiation_lookup[str(row['element_id'])])
    annual_netting(0, 0, financial_params['electricity_price'], financial_params['export_rate'])
    if financial_params.get('electricity_price') is None:
        raise ValueError("An explicit electricity price is required")
    if energy_balance is None or len(energy_balance) == 0:
        raise ValueError("Demand data are required")
    demand = (energy_balance['predicted_demand'].to_numpy(dtype=float) if hasattr(energy_balance, 'columns')
              else np.asarray([row['predicted_demand'] for row in energy_balance], dtype=float))
    if not np.isfinite(demand).all() or (demand < 0).any() or demand.sum() <= 0:
        raise ValueError("Demand must be finite, nonnegative and have a positive total")
    if not np.isfinite(float(financial_params['electricity_price'])):
        raise ValueError("Electricity price must be finite")
    if not 0 <= financial_params.get('min_coverage', 0.3) <= 1:
        raise ValueError("Minimum coverage must be a fraction between 0 and 1")
    if ga_params['population_size'] < 1 or ga_params['generations'] < 1:
        raise ValueError("Population size and generations must be positive")
    if not 0 <= ga_params['mutation_rate'] <= 1:
        raise ValueError("Mutation rate must be between 0 and 1")
    rng = random.Random(ga_params.get('seed', 42))
    # Optimize population size for better performance vs quality balance
    population_size = min(ga_params['population_size'], max(50, n_elements * 2))  # Cap at reasonable size
    generations = ga_params['generations']
    mutation_rate = ga_params['mutation_rate']
    
    # Fixed generation count; no unimplemented early-convergence claim.
    
    # Initialize population
    population = [create_individual(n_elements, rng) for _ in range(population_size)]
    
    if n_elements == 1:
        population[0] = [1]  # Evaluate the only nonempty candidate deterministically

    # Evolution tracking
    best_individuals = []
    fitness_history = []
    
    for generation in range(generations):
        # Evaluate population
        fitness_scores = []
        for individual in population:
            fitness = evaluate_individual(individual, pv_specs, energy_balance, financial_params, radiation_lookup)
            fitness_scores.append(fitness)
        
        # Find best individuals (handle single fitness values)
        ranked_candidates = []
        for i, fitness in enumerate(fitness_scores):
            # Handle single fitness value (weighted score)
            if isinstance(fitness, tuple) and len(fitness) == 1:
                fitness_value = fitness[0]
            elif isinstance(fitness, (int, float)):
                fitness_value = fitness
            else:
                fitness_value = 0
            
            if fitness_value > 0:
                ranked_candidates.append((i, fitness_value, fitness_value, population[i][:]))
        
        # Store best individuals
        if ranked_candidates:
            best_individuals.extend(ranked_candidates)
            avg_fitness = np.mean([fitness_val for _, fitness_val, _, _ in ranked_candidates])
            fitness_history.append({'generation': generation, 'avg_fitness': avg_fitness})
        
        # Selection: retain elites and use uniform random parents (legacy method)
        new_population = []
        
        # Keep best individuals
        elite_size = max(1, population_size // 10)
        elite_indices = sorted(range(len(fitness_scores)), key=lambda i: fitness_scores[i], reverse=True)[:elite_size]
        for idx in elite_indices:
            new_population.append(population[idx][:])
        
        # Generate offspring
        while len(new_population) < population_size:
            # Uniform random parent selection
            parent1 = population[rng.choice(range(len(population)))]
            parent2 = population[rng.choice(range(len(population)))]
            
            # Simple crossover
            crossover_point = rng.randint(1, n_elements - 1) if n_elements > 1 else 1
            child = parent1[:crossover_point] + parent2[crossover_point:]
            
            # Mutation
            for i in range(len(child)):
                if rng.random() < mutation_rate:
                    child[i] = 1 - child[i]  # Flip bit
            
            new_population.append(child)
        
        population = new_population
    
    # Deduplicate masks; these are weighted candidates, not a Pareto front.
    unique = {tuple(item[3]): item for item in best_individuals}
    ranked = sorted(unique.values(), key=lambda item: item[1], reverse=True)
    return ranked, fitness_history

def analyze_optimization_results(pareto_solutions, pv_specs, energy_balance, financial_params, radiation_lookup=None):
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
                
            total_annual_yield = sum(annual_element_yield(row, radiation_lookup[str(row['element_id'])])
                                     for _, row in selected_specs.iterrows())
            selected_elements = selected_specs['element_id'].tolist() if 'element_id' in selected_specs.columns else [f"Element_{j}" for j in range(len(selected_specs))]
            
            # Calculate net import reduction
            if energy_balance is not None and len(energy_balance) > 0:
                total_annual_demand = (energy_balance['predicted_demand'].sum() if hasattr(energy_balance, 'columns')
                                       else sum(float(row['predicted_demand']) for row in energy_balance))
                net_import = max(0, total_annual_demand - total_annual_yield)
            else:
                net_import = 0
            
            # Calculate ROI with proper demand handling
            electricity_price = financial_params['electricity_price']
            
            # Get proper total annual demand
            if energy_balance is not None and len(energy_balance) > 0:
                if hasattr(energy_balance, 'columns') and 'predicted_demand' in energy_balance.columns:
                    total_annual_demand = energy_balance['predicted_demand'].sum()
                elif isinstance(energy_balance, list) and len(energy_balance) > 0:
                    total_annual_demand = sum(float(row['predicted_demand']) for row in energy_balance)
                else:
                    total_annual_demand = total_annual_yield
            else:
                total_annual_demand = total_annual_yield
                
            # Calculate annual savings (grid import reduction)
            energy_offset = min(total_annual_yield, total_annual_demand) if total_annual_demand > 0 else total_annual_yield
            gross_annual_savings = annual_netting(total_annual_yield, total_annual_demand,
                                                  electricity_price, financial_params['export_rate'])['gross_benefit']
            
            # Include realistic maintenance and operational costs
            include_maintenance = financial_params.get('include_maintenance', True)
            if include_maintenance:
                # Use the same explicit maintenance assumption as fitness evaluation
                annual_maintenance = total_cost * financial_params.get('maintenance_rate', 0.015)  # Shared maintenance assumption
                net_annual_savings = gross_annual_savings - annual_maintenance
            else:
                net_annual_savings = gross_annual_savings
            
            # Calculate ROI with net savings (after maintenance)
            roi = (net_annual_savings / total_cost * 100) if total_cost > 0 and net_annual_savings > 0 else 0
            
            # Store both gross and net savings for transparency
            annual_savings = net_annual_savings
            
            solution = {
                'solution_id': f"Solution_{i+1}",
                'optimization_method': 'weighted-genetic-v3',
                'energy_model_version': ENERGY_MODEL_VERSION,
                'annual_demand_kwh': float(total_annual_demand),
                'balance_method': BALANCE_METHOD,
                'fitness_score': float(fitness_value),
                'total_power_kw': float(total_power_kw),  # Ensure float conversion
                'total_investment': float(total_cost),    # Ensure float conversion
                'annual_energy_kwh': float(total_annual_yield),  # Ensure float conversion
                'annual_savings': float(annual_savings),  # Net annual savings after maintenance
                'gross_annual_savings': float(gross_annual_savings),  # Gross savings before maintenance
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

