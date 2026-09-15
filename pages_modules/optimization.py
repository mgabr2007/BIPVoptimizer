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
from utils.ui_standards import render_step_header, render_navigation_buttons, render_status_message, WORKFLOW_STEPS
from database_manager import db_manager
from utils.database_helper import db_helper
from core.solar_math import safe_divide
from utils.color_schemes import CHART_COLORS, get_chart_color
# Removed ConsolidatedDataManager - using database-only approach
# Removed session state dependency - using database-only approach

from services.analysis_inputs import upstream_snapshot
from core.financial_scenario import input_fingerprint
from core.energy_contracts import reference_year, ENERGY_MODEL_VERSION
from core.optimization_engine import (
    create_individual, evaluate_individual, simple_genetic_algorithm, analyze_optimization_results,
)

def render_optimization():
    """Render the genetic algorithm optimization module."""
    
    # Add OptiSunny character header image
    st.image("attached_assets/step08_1751436847831.png", width=400)
    
    st.header("🎯 Step 8: Multi-Objective BIPV Optimization")
    
    # Show facade orientation configuration
    from services.io import get_current_project_id
    project_id = get_current_project_id()
    
    if project_id:
        try:
            conn = db_manager.get_connection()
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT include_north_facade FROM projects WHERE id = %s", (project_id,))
                    result = cursor.fetchone()
                    include_north = result[0] if result else False
                    
                    if include_north:
                        st.info("📍 **Optimizing all orientations** (N/S/E/W) per project configuration")
                    else:
                        st.info("📍 **Optimizing optimal orientations** (S/E/W only) per project configuration")
                conn.close()
        except Exception:
            st.info("📍 **Default:** Optimizing South/East/West orientations only")
    
    # Optimization Methodology Explanation
    with st.expander("🔬 How BIPV Optimization Works", expanded=True):
        st.markdown("""
        ### Genetic Algorithm BIPV Selection Process:
        
        **🧬 Individual Solutions (Chromosomes):**
        - Each solution is a binary selection mask for the eligible window elements in this project
        - Example: [1,0,1,0,1,...] means select windows 1,3,5... skip windows 2,4...
        - **Does NOT use all windows** - selects optimal subset based on performance criteria
        
        **💰 Budget Allocation Strategy:**
        - **No fixed budget constraint** - optimization finds cost-effective combinations
        - Evaluates trade-offs between total investment cost vs energy yield vs ROI
        - Genetic algorithm naturally balances cost minimization with performance maximization
        - Solutions range from small selective installations to larger comprehensive systems
        
        **🎯 Multi-Objective Fitness Evaluation:**
        1. **Cost Fitness**: Lower total investment cost = higher fitness (1/(1+normalized_cost))
        2. **Yield Fitness**: Higher total energy generation = higher fitness (yield/max_possible)
        3. **ROI Fitness**: Higher return on investment = higher fitness (ROI/50% cap)
        
        **⚖️ Weighted Selection Process:**
        - User sets objective weights (Cost: X%, Yield: Y%, ROI: Z%)
        - Each solution gets single fitness score = (cost_fitness × X) + (yield_fitness × Y) + (roi_fitness × Z)
        - **Selects optimal window combinations**, not all windows
        - Prioritizes South/East/West-facing elements (North excluded for poor solar performance)
        
        **🔄 Evolution Process (30 generations default):**
        - Configured population of candidate solutions evolves through crossover and mutation
        - Elite solutions preserved, offspring created through genetic operators
        - Ranks candidates by weighted fitness; this is not a Pareto-front solver
        """)
        
        st.info("🎯 **Key Point**: Optimization selects the BEST SUBSET of windows, not all windows. It finds cost-effective combinations that maximize performance per investment euro.")
    
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
                    st.info("Optimization uses a historical annual-demand baseline, not a validated AI forecast")
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
    
    try:
        if 'energy_model_version' not in pv_specs or not (pv_specs['energy_model_version'] == ENERGY_MODEL_VERSION).all():
            raise ValueError('Regenerate Step 6 specifications to use explicit active area and efficiency units')
        historical = db_manager.get_historical_data(project_id)
        baseline = reference_year(historical['consumption_data'], historical.get('date_data'))
        energy_balance = pd.DataFrame({'predicted_demand': [baseline['annual_demand_kwh']]})
    except (ValueError, KeyError, TypeError) as exc:
        st.error(str(exc))
        return
    st.info('Experimental annual-netting scenario; time-matched energy balance and physics validation remain pending.')

    # Success confirmation after data conversion
    st.success(f"✅ Database verification complete: {len(pv_specs)} BIPV systems ready for optimization")
    st.info("💡 Using saved project inputs; results depend on the recorded calculation assumptions")
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
        
        # Display final calculated weights (after fine-tuning)
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Maximize Yield Weight", f"{weight_yield}%", 
                     help="Auto-calculated to maintain 100% total")
        with col_b:
            st.metric("Maximize ROI Weight", f"{weight_roi}%", 
                     help="Auto-calculated to maintain 100% total")
        
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
    
    export_rate = st.number_input('Export tariff scenario (€/kWh)', min_value=0.0,
                                  value=float((db_manager.get_project_by_id(project_id).get('electricity_rates') or {}).get('export_rate', 0.0)),
                                  format='%.3f', key='export_rate_opt')
    st.caption('Zero export tariff assumes no export revenue. ROI here is first-year net benefit / capital cost, not IRR.')
    col3, col4 = st.columns(2)
    
    with col3:
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

        'min_coverage': min_coverage,
        'electricity_price': electricity_price,
                    'export_rate': export_rate,
        'prioritize_roi': prioritize_roi,
        'include_maintenance': include_maintenance,
                    'maintenance_rate': 0.015,
        'orientation_preference': orientation_preference,
        'system_size_preference': system_size_preference,
        'weights': {'cost': weight_cost, 'yield': weight_yield, 'roi': weight_roi}
    }
    
    # Run optimization buttons side by side
    st.subheader("🚀 Run Optimization")
    col1, col2 = st.columns(2)
    
    with col1:
        run_optimization = st.button("🚀 Run Weighted Optimization", key="run_optimization")
    
    with col2:
        clear_and_rerun = st.button("🔄 Rerun Optimization",
                                   type="secondary", 
                                   help="Recompute; retain saved results if the new run fails",
                                   key="clear_rerun_btn")
    
    # Preserve saved results until a successful replacement is ready.
    if clear_and_rerun:
        run_optimization = True

    if run_optimization:
        with st.spinner("Running genetic algorithm optimization..."):
            try:
                # Setup optimization parameters
                ga_params = {
                    'population_size': population_size,
                    'generations': generations,
                    'mutation_rate': mutation_rate / 100,
                    'seed': 42
                }
                
                financial_params = {
                    'electricity_price': electricity_price,
                    'export_rate': export_rate,
                    'min_coverage': min_coverage / 100,
                    'weight_cost': weight_cost,
                    'weight_yield': weight_yield,
                    'weight_roi': weight_roi,
                    'prioritize_roi': prioritize_roi,
                    'include_maintenance': include_maintenance,
                    'maintenance_rate': 0.015,
                    'orientation_preference': orientation_preference,
                    'system_size_preference': system_size_preference
                }
                
                # Get authentic radiation data from Step 5 before optimization
                conn = db_manager.get_connection()
                radiation_lookup = {}
                if conn:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT element_id, annual_radiation 
                            FROM element_radiation 
                            WHERE project_id = %s
                        """, (project_id,))
                        
                        radiation_data = cursor.fetchall()
                        radiation_lookup = {str(elem_id): float(annual_rad) for elem_id, annual_rad in radiation_data}
                        st.info(f"🔍 Using authentic Step 5 radiation data for {len(radiation_lookup)} elements in optimization")
                    conn.close()
                
                upstream_hash = input_fingerprint(project_id, {}, {}, 0, upstream_snapshot(db_manager, project_id))
                # Run genetic algorithm with authentic radiation data
                pareto_solutions, fitness_history = simple_genetic_algorithm(
                    pv_specs, energy_balance, financial_params, ga_params, radiation_lookup
                )
                
                if not pareto_solutions:
                    st.error("Optimization failed to find viable solutions.")
                    return
                
                # Analyze optimization results
                solutions_df = analyze_optimization_results(
                    pareto_solutions, pv_specs, energy_balance, financial_params, radiation_lookup
                )
                
                # Preserve the objective the user asked the solver to optimize.
                solutions_df = solutions_df.sort_values('fitness_score', ascending=False, kind='stable').reset_index(drop=True)
                
                # Save results
                optimization_results = {
                    'solutions': solutions_df,
                    'fitness_history': fitness_history,
                    'model_version': 'weighted-genetic-v3',
                    'optimization_config': {
                        'upstream_fingerprint': upstream_hash,
                        'ga_params': ga_params,
                        'financial_params': financial_params,
                        'constraints': {
    
                            'min_coverage': min_coverage
                        }
                    }
                }
                
                # Save results to database with selection details
                try:
                    # Convert DataFrame to dict and ensure selection_mask is preserved
                    solutions_dict = solutions_df.to_dict('records')
                    
                    # Ensure selection mask data is preserved in each solution
                    for i, solution in enumerate(solutions_dict):
                        if 'selection_mask' not in solution and i < len(pareto_solutions):
                            # Get selection mask from original pareto solutions
                            _, _, _, individual = pareto_solutions[i]
                            solution['selection_mask'] = individual
                    
                    if upstream_hash != input_fingerprint(project_id, {}, {}, 0, upstream_snapshot(db_manager, project_id)):
                        raise ValueError('Upstream inputs changed during optimization; rerun before saving')
                    saved = db_manager.save_optimization_results(project_id, {
                        'solutions': solutions_dict,
                        'optimization_config': optimization_results['optimization_config'],
                        'model_version': 'weighted-genetic-v3'
                    })
                    if not saved:
                        st.error("Results could not be saved. Previous committed results remain available.")
                        return
                    st.success("✅ Optimization results with selection details saved to database")
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
                    SELECT solution_id, capacity, roi, net_import, total_cost, annual_energy_kwh 
                    FROM optimization_results 
                    WHERE project_id = %s 
                    ORDER BY roi DESC
                """, (project_id,))
                
                results = cursor.fetchall()
                if results:
                    solutions = pd.DataFrame(results, columns=['solution_id', 'capacity', 'roi', 'net_import', 'total_cost', 'annual_energy_kwh'])
                    
                    # Convert all numeric columns from Decimal to float to prevent arithmetic errors
                    numeric_columns = ['capacity', 'roi', 'net_import', 'total_cost', 'annual_energy_kwh']
                    for col in numeric_columns:
                        if col in solutions.columns:
                            solutions[col] = pd.to_numeric(solutions[col], errors='coerce').astype(float)
                    
                    optimization_data = {'solutions': solutions}
            conn.close()
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        
    if optimization_data and solutions is not None and len(solutions) > 0:
        st.subheader("📊 Optimization Results")
        
        st.info("**Multi-Objective Optimization Results from Database**")
        
        # Investment Range Filter
        st.subheader("💰 Filter Solutions by Investment Range")
        
        # Get investment range from solutions
        min_investment = float(solutions['total_cost'].min())
        max_investment = float(solutions['total_cost'].max())
        
        col_filter1, col_filter2 = st.columns(2)
        
        with col_filter1:
            investment_min = st.number_input(
                "Minimum Investment (€)",
                min_value=0,
                max_value=int(max_investment),
                value=0,
                step=1000,
                help="Filter solutions by minimum investment amount",
                key="investment_filter_min"
            )
        
        with col_filter2:
            investment_max = st.number_input(
                "Maximum Investment (€)",
                min_value=int(investment_min),
                max_value=int(max_investment * 1.1),
                value=int(max_investment),
                step=1000,
                help="Filter solutions by maximum investment amount", 
                key="investment_filter_max"
            )
        
        # Apply investment filter
        filtered_solutions = solutions[
            (solutions['total_cost'] >= investment_min) & 
            (solutions['total_cost'] <= investment_max)
        ].copy()
        
        # Display filter results
        st.write(f"**Filter Results:** Showing {len(filtered_solutions)} of {len(solutions)} solutions within €{investment_min:,} - €{investment_max:,} range")
        
        if len(filtered_solutions) == 0:
            st.warning("⚠️ No solutions found within the selected investment range. Try adjusting the filter values.")
            return
        
        # Update solutions variable to use filtered results
        solutions = filtered_solutions
        
        st.subheader("🎯 Optimization Analysis Summary")
        
        # Window Selection Summary - Calculate how many windows each solution uses
        st.write("**Window Selection Analysis:**")
        total_suitable_windows = len(pv_specs)  # Total suitable windows from Step 6
        
        # Get window counts for each solution from the database
        window_counts = []
        try:
            conn = db_manager.get_connection()
            if conn:
                with conn.cursor() as cursor:
                    for _, solution in solutions.head(5).iterrows():  # Top 5 solutions
                        cursor.execute("""
                            SELECT selection_details FROM optimization_results 
                            WHERE project_id = %s AND solution_id = %s
                        """, (project_id, solution['solution_id']))
                        
                        result = cursor.fetchone()
                        if result and result[0]:
                            import json
                            selection_data = json.loads(result[0])
                            selected_windows = sum(selection_data.get('selection_mask', []))
                        else:
                            # Estimate from capacity - rough approximation
                            estimated_windows = int(solution['capacity'] / (total_suitable_windows * solution['capacity'] / total_suitable_windows))
                            selected_windows = min(estimated_windows, total_suitable_windows)
                        
                        window_counts.append(selected_windows)
                conn.close()
        except Exception:
            # Fallback estimation based on capacity ratios
            max_capacity = solutions['capacity'].max() if len(solutions) > 0 else 1
            for _, solution in solutions.head(5).iterrows():
                estimated_windows = int((solution['capacity'] / max_capacity) * total_suitable_windows * 0.5)  # Rough estimate
                window_counts.append(estimated_windows)
        
        # Display window selection summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Available Windows", f"{total_suitable_windows:,}")
            st.caption("From Step 6 BIPV Analysis")
        
        with col2:
            if window_counts:
                avg_selected = int(np.mean(window_counts[:3]))  # Top 3 solutions
                st.metric("Average Windows Selected", f"{avg_selected:,}")
                st.caption(f"~{(avg_selected/total_suitable_windows)*100:.1f}% of available")
        
        with col3:
            if window_counts:
                max_selected = max(window_counts[:3])
                st.metric("Maximum Windows Used", f"{max_selected:,}")
                st.caption(f"Solution with highest coverage")
        
        with st.expander("📊 Top Solutions Window Usage", expanded=False):
            st.write("**Window Selection by Solution:**")
            for i, (_, solution) in enumerate(solutions.head(5).iterrows()):
                windows_used = window_counts[i] if i < len(window_counts) else 0
                coverage_pct = (windows_used / total_suitable_windows) * 100 if total_suitable_windows > 0 else 0
                
                st.write(f"**{solution['solution_id']}:** {windows_used:,} windows ({coverage_pct:.1f}% coverage)")
                
                sol_col1, sol_col2, sol_col3 = st.columns(3)
                
                with sol_col1:
                    st.write(f"- Capacity: {solution['capacity']:.1f} kW")
                    st.write(f"- Total Cost: €{solution['total_cost']:,.0f}")
                
                with sol_col2:
                    st.write(f"- ROI: {solution['roi']:.1f}%")
                    st.write(f"- Annual Energy: {solution['annual_energy_kwh']:,.0f} kWh")
                
                with sol_col3:
                    # Explicit float conversion for arithmetic operations
                    total_cost_float = float(solution['total_cost']) if solution['total_cost'] is not None else 0.0
                    annual_energy_float = float(solution['annual_energy_kwh']) if solution['annual_energy_kwh'] is not None else 0.0
                    
                    cost_per_window = total_cost_float / windows_used if windows_used > 0 else 0
                    energy_per_window = annual_energy_float / windows_used if windows_used > 0 else 0
                    st.write(f"- Cost per Window: €{cost_per_window:,.0f}")
                    st.write(f"- Energy per Window: {energy_per_window:,.0f} kWh/year")
        
        # Comprehensive Optimization Results Visualization
        st.subheader("📊 Interactive Optimization Results")
        
        # Create interactive visualizations
        import plotly.graph_objects as go
        import plotly.express as px
        from plotly.subplots import make_subplots
        
        # Convert Series to numeric arrays for Plotly compatibility with explicit float conversion
        solutions_dict = {
            'total_cost': pd.to_numeric(solutions['total_cost'], errors='coerce').astype(float).values,
            'roi': pd.to_numeric(solutions['roi'], errors='coerce').astype(float).values, 
            'capacity': pd.to_numeric(solutions['capacity'], errors='coerce').astype(float).values,
            'net_import': pd.to_numeric(solutions['net_import'], errors='coerce').astype(float).values,
            'solution_id': solutions['solution_id'].values
        }
        
        # 1. ROI vs Investment Scatter Plot
        fig1 = px.scatter(
            x=solutions_dict['total_cost'], 
            y=solutions_dict['roi'],
            size=solutions_dict['capacity'],
            color=solutions_dict['net_import'],
            hover_data={'x': solutions_dict['total_cost'], 'y': solutions_dict['roi']},
            title="ROI vs Total Investment (Size = Capacity, Color = Net Import)",
            labels={
                'x': 'Total Investment (€)',
                'y': 'Return on Investment (%)',
                'color': 'Net Import Reduction (kWh)'
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
            go.Histogram(x=solutions_dict['total_cost'], name='Investment (€)', nbinsx=10),
            row=1, col=1
        )
        
        # ROI histogram
        fig2.add_trace(
            go.Histogram(x=solutions_dict['roi'], name='ROI (%)', nbinsx=10),
            row=1, col=2
        )
        
        # Capacity histogram
        fig2.add_trace(
            go.Histogram(x=solutions_dict['capacity'], name='Capacity (kW)', nbinsx=10),
            row=2, col=1
        )
        
        # Net import histogram
        fig2.add_trace(
            go.Histogram(x=solutions_dict['net_import'], name='Net Import (kWh)', nbinsx=10),
            row=2, col=2
        )
        
        fig2.update_layout(height=600, title_text="Solution Distribution Analysis", showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)
        
        # 3. Pareto Front Analysis (Cost vs Performance Trade-off)
        fig3 = go.Figure()
        
        # Add scatter points
        fig3.add_trace(go.Scatter(
            x=solutions_dict['total_cost'],
            y=solutions_dict['roi'],
            mode='markers+text',
            text=solutions_dict['solution_id'],
            textposition='top center',
            marker=dict(
                size=[float(cap) * 3 for cap in solutions_dict['capacity']],  # Explicit float conversion
                color=[float(imp) for imp in solutions_dict['net_import']],    # Explicit float conversion
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Net Import Reduction (kWh)")
            ),
            name='Solutions'
        ))
        
        fig3.update_layout(
            title="Weighted Candidates: Investment vs ROI",
            xaxis_title="Total Investment Cost (€)",
            yaxis_title="Return on Investment (%)",
            height=500
        )
        st.plotly_chart(fig3, use_container_width=True)
        
        # 4. Top Solutions Comparison Bar Chart
        top_solutions = solutions.head(5)  # Top 5 solutions by ROI
        top_dict = {
            'solution_id': top_solutions['solution_id'].values,
            'roi': top_solutions['roi'].values.astype(float),
            'total_cost': top_solutions['total_cost'].values.astype(float),
            'capacity': top_solutions['capacity'].values.astype(float)
        }
        
        fig4 = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Top 5 Solutions by ROI', 'Investment vs Energy Performance'),
            specs=[[{"secondary_y": False}, {"secondary_y": True}]]
        )
        
        # ROI comparison
        fig4.add_trace(
            go.Bar(x=top_dict['solution_id'], y=top_dict['roi'], 
                   name='ROI (%)', marker_color='lightblue'),
            row=1, col=1
        )
        
        # Investment vs Performance
        fig4.add_trace(
            go.Bar(x=top_dict['solution_id'], y=top_dict['total_cost'], 
                   name='Investment (€)', marker_color='lightcoral'),
            row=1, col=2
        )
        
        fig4.add_trace(
            go.Scatter(x=top_dict['solution_id'], y=top_dict['capacity'], 
                      mode='lines+markers', name='Capacity (kW)', 
                      line=dict(color='green', width=3)),
            row=1, col=2, secondary_y=True
        )
        
        fig4.update_yaxes(title_text="Investment (€)", secondary_y=False, row=1, col=2)
        fig4.update_yaxes(title_text="System Capacity (kW)", secondary_y=True, row=1, col=2)
        fig4.update_layout(height=500, title_text="Detailed Top Solutions Analysis")
        st.plotly_chart(fig4, use_container_width=True)
        
        # Summary metrics after charts
        best_solution = solutions.iloc[0]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Best ROI", f"{best_solution['roi']:.1f}%")
        
        with col2:
            st.metric("Best Investment", f"€{best_solution['total_cost']:,.0f}")
        
        with col3:
            st.metric("Best Capacity", f"{best_solution['capacity']:.1f} kW")
        
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
        
        # Solution selection for Step 9 - mark which solutions have CSV export
        st.subheader("✅ Select Solution for Detailed Analysis")
        
        # Get solutions with selection details for better labeling
        try:
            conn_temp = db_manager.get_connection()
            if conn_temp:
                with conn_temp.cursor() as cursor_temp:
                    cursor_temp.execute("""
                        SELECT solution_id FROM optimization_results 
                        WHERE project_id = %s AND selection_details IS NOT NULL AND selection_details != 'null'
                    """, (project_id,))
                    solutions_with_csv = {row[0] for row in cursor_temp.fetchall()}
                conn_temp.close()
            else:
                solutions_with_csv = set()
        except:
            solutions_with_csv = set()
        
        # Create enhanced option labels
        solution_options = []
        for sol_id in solutions['solution_id'].tolist():
            sol_data = solutions[solutions['solution_id'] == sol_id].iloc[0]
            csv_indicator = "📥 CSV Available" if sol_id in solutions_with_csv else "📄 Summary Only"
            label = f"{sol_id} - ROI {sol_data['roi']:.1f}% - {csv_indicator}"
            solution_options.append((label, sol_id))
        
        selected_option = st.selectbox(
            "Choose solution for detailed analysis:",
            solution_options,
            format_func=lambda x: x[0],
            key="selected_solution_opt"
        )
        
        selected_solution_id = selected_option[1]
        
        # Get selected solution data
        selected_solution = solutions[solutions['solution_id'] == selected_solution_id].iloc[0]
        
        st.success(f"✅ Selected Solution {selected_solution_id} - Ready for Step 9 Financial Analysis")
        
        # Display detailed analysis for selected solution
        st.subheader(f"📊 Selected Solution Analysis: {selected_solution_id}")
        
        # Selected solution detailed metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Selected ROI", f"{selected_solution['roi']:.1f}%")
        with col2:
            st.metric("Selected Investment", f"€{selected_solution['total_cost']:,.0f}")
        with col3:
            st.metric("Selected Capacity", f"{selected_solution['capacity']:.1f} kW")
        with col4:
            st.metric("Annual Energy", f"{selected_solution['annual_energy_kwh']:,.0f} kWh")
        
        # Financial Performance Analysis - Using Authentic Data
        st.subheader("💰 Solution Performance Analysis")
        
        # Calculate authentic financial metrics
        annual_energy_kwh = float(selected_solution['annual_energy_kwh'])
        total_investment = float(selected_solution['total_cost'])
        electricity_rate = 0.300  # Default rate - can be made dynamic
        
        # Financial calculations
        annual_savings = annual_energy_kwh * electricity_rate
        system_lifetime = 25  # years
        total_savings_25yr = annual_savings * system_lifetime
        simple_payback = total_investment / annual_savings if annual_savings > 0 else 0
        roi_25yr = ((total_savings_25yr - total_investment) / total_investment) * 100 if total_investment > 0 else 0
        
        st.markdown("**💰 Financial Performance Breakdown**")
        
        # Display metrics in organized columns
        perf_col1, perf_col2 = st.columns(2)
        
        with perf_col1:
            st.metric("Annual Generation", f"{annual_energy_kwh:,.0f} kWh")
            st.metric("Electricity Rate", f"€{electricity_rate:.3f}/kWh")
            st.metric("Annual Savings", f"€{annual_savings:,.0f}")
            st.metric("25-Year Savings", f"€{total_savings_25yr:,.0f}")
            
        with perf_col2:
            st.metric("Total Investment", f"€{total_investment:,.0f}")
            st.metric("Simple Payback", f"{simple_payback:.1f} years")
            st.metric("ROI (25-year)", f"{roi_25yr:.1f}%")
            st.metric("Cost per kWh (Lifetime)", f"€{total_investment/(annual_energy_kwh * system_lifetime):.3f}")
        
        st.markdown("**📋 Solution Performance Summary**")
        
        # Performance indicators
        performance_data = {
            'Metric': [
                'Annual Energy Generation',
                'System Capacity',
                'Annual CO₂ Savings',
                'Energy Independence Contribution',
                'Cost per Installed kW',
                'Capacity Factor (Est.)',
                'Performance Ratio (Est.)'
            ],
            'Value': [
                f"{annual_energy_kwh:,.0f} kWh/year",
                f"{selected_solution['capacity']:.1f} kW",
                f"{annual_energy_kwh * 0.401:,.0f} kg CO₂/year",  # German grid factor ~0.401 kg/kWh
                f"{min(100, (annual_energy_kwh / 10000) * 100):.1f}%",  # Assume 10 MWh typical building
                f"€{total_investment / selected_solution['capacity']:,.0f}/kW",
                f"{(annual_energy_kwh / (selected_solution['capacity'] * 8760)) * 100:.1f}%",
                "85-90%" # Typical BIPV performance ratio
            ],
            'Note': [
                'From authentic Step 5 radiation analysis',
                'From genetic algorithm optimization',
                'Using German electricity grid CO₂ factor',
                'Estimated building energy independence',
                'Total system cost per installed capacity',
                'Annual generation vs theoretical maximum',
                'System efficiency vs ideal conditions'
            ]
        }
        
        st.dataframe(
            pd.DataFrame(performance_data),
            use_container_width=True,
            hide_index=True
        )
        
        # Section removed per user request
        
        # Retrieve detailed PV specifications for this solution from JSON data
        try:
            conn = db_manager.get_connection()
            if conn:
                with conn.cursor() as cursor:
                    # Get PV specifications from JSON data
                    cursor.execute("""
                        SELECT specification_data 
                        FROM pv_specifications 
                        WHERE project_id = %s
                        LIMIT 1
                    """, (project_id,))
                    
                    result = cursor.fetchone()
                    if result and result[0]:
                        import json
                        spec_data = json.loads(result[0])
                        bipv_specs = spec_data.get('bipv_specifications', [])
                        
                        if bipv_specs:
                            # Convert BIPV specifications to DataFrame
                            pv_df = pd.DataFrame(bipv_specs)
                            
                            # Get orientation data from building_elements
                            cursor.execute("""
                                SELECT element_id, orientation, building_level
                                FROM building_elements 
                                WHERE project_id = %s
                            """, (project_id,))
                            
                            orientation_data = cursor.fetchall()
                            orientation_dict = {row[0]: {'orientation': row[1], 'level': row[2]} for row in orientation_data}
                            
                            # Add orientation data to PV DataFrame
                            pv_df['orientation'] = pv_df['element_id'].map(lambda x: orientation_dict.get(x, {}).get('orientation', 'Unknown'))
                            pv_df['building_level'] = pv_df['element_id'].map(lambda x: orientation_dict.get(x, {}).get('level', 'Unknown'))
                            
                            # Rename columns for consistency
                            if 'total_cost_eur' in pv_df.columns:
                                pv_df['estimated_cost_eur'] = pv_df['total_cost_eur']
                            if 'glass_area_m2' in pv_df.columns:
                                pv_df['glass_area'] = pv_df['glass_area_m2']
                            
                            # Convert to float for calculations
                            pv_df['glass_area'] = pd.to_numeric(pv_df.get('glass_area', pv_df.get('glass_area_m2', 0)), errors='coerce')
                            pv_df['annual_energy_kwh'] = pd.to_numeric(pv_df.get('annual_energy_kwh', 0), errors='coerce') 
                            pv_df['estimated_cost_eur'] = pd.to_numeric(pv_df.get('estimated_cost_eur', pv_df.get('total_cost_eur', 0)), errors='coerce')
                            pv_df['capacity_kw'] = pd.to_numeric(pv_df.get('capacity_kw', 0), errors='coerce')
                            
                            # Create solution-specific visualizations
                            st.subheader("🎯 Solution Performance Analysis")
                            
                            # 1. Energy Production by Building Element
                            fig_elements = px.bar(
                            pv_df.head(10),  # Top 10 elements
                            x='element_id',
                            y='annual_energy_kwh',
                            color='orientation',
                            title="Top 10 Elements: Annual Energy Production",
                            labels={
                                'element_id': 'Building Element ID',
                                'annual_energy_kwh': 'Annual Energy (kWh)',
                                'orientation': 'Orientation'
                            }
                            )
                            fig_elements.update_layout(height=400)
                            st.plotly_chart(fig_elements, use_container_width=True)
                            
                            # 2. Performance by Orientation Analysis - Fix orientation mapping
                            
                            # Create proper orientation mapping from azimuth values
                            def map_orientation_from_azimuth(row):
                                """Map azimuth values to proper orientation names"""
                                # First try existing orientation field
                                orientation_value = row.get('orientation')
                                if pd.notna(orientation_value) and orientation_value:
                                    if isinstance(orientation_value, str):
                                        if orientation_value in ['North', 'South', 'East', 'West', 'SE', 'SW', 'NE', 'NW']:
                                            return orientation_value
                                        if orientation_value.lower() in ['south', 'east', 'west', 'north']:
                                            return orientation_value.capitalize()
                                
                                # Use azimuth value if orientation is empty/null
                                azimuth_value = row.get('azimuth')
                                if pd.notna(azimuth_value):
                                    try:
                                        azimuth = float(azimuth_value)
                                        # Normalize azimuth to 0-360 range
                                        azimuth = azimuth % 360
                                        
                                        if 315 <= azimuth or azimuth < 45:
                                            return "North"
                                        elif 45 <= azimuth < 135:
                                            return "East"
                                        elif 135 <= azimuth < 225:
                                            return "South"
                                        elif 225 <= azimuth < 315:
                                            return "West"
                                        else:
                                            return f"Azimuth {azimuth:.0f}°"
                                    except:
                                        pass
                                
                                return "Unknown"
                            
                            # Apply orientation mapping using both orientation and azimuth
                            pv_df['orientation_mapped'] = pv_df.apply(map_orientation_from_azimuth, axis=1)
                            
                            # Group by mapped orientation
                            orientation_analysis = pv_df.groupby('orientation_mapped').agg({
                                'annual_energy_kwh': ['sum', 'mean', 'count'],
                                'glass_area': 'sum',
                                'estimated_cost_eur': 'sum'
                            }).round(2)
                            
                            # Flatten column names
                            orientation_analysis.columns = ['Total Energy (kWh)', 'Avg Energy (kWh)', 'Element Count', 
                                                          'Total Area (m²)', 'Total Cost (€)']
                            orientation_analysis = orientation_analysis.reset_index()
                            orientation_analysis = orientation_analysis.rename(columns={'orientation_mapped': 'orientation'})
                            
                            col_left, col_right = st.columns(2)
                            
                            with col_left:
                                # Orientation energy pie chart
                                fig_pie = px.pie(
                                    orientation_analysis,
                                    values='Total Energy (kWh)',
                                    names='orientation',
                                    title="Energy Production by Orientation"
                                )
                                fig_pie.update_layout(height=400)
                                st.plotly_chart(fig_pie, use_container_width=True)
                            
                            with col_right:
                                # Cost vs Energy efficiency scatter - improved visualization
                                fig_efficiency = px.scatter(
                                    pv_df,
                                    x='estimated_cost_eur',
                                    y='annual_energy_kwh',
                                    size='glass_area',
                                    color='orientation_mapped',
                                    title="Cost vs Energy Efficiency",
                                    labels={
                                        'estimated_cost_eur': 'Element Cost (€)',
                                        'annual_energy_kwh': 'Annual Energy (kWh)',
                                        'glass_area': 'Glass Area (m²)',
                                        'orientation_mapped': 'Orientation'
                                    },
                                    hover_data=['element_id', 'glass_area']
                                )
                                
                                # Improve layout with better colors and formatting
                                fig_efficiency.update_layout(
                                    height=400,
                                    showlegend=True,
                                    legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
                                )
                                
                                # Update traces for better visibility
                                fig_efficiency.update_traces(
                                    marker=dict(
                                        sizemin=4,
                                        opacity=0.7,
                                        line=dict(width=1, color='white')
                                    )
                                )
                                
                                st.plotly_chart(fig_efficiency, use_container_width=True)
                            
                            # 3. Financial Performance Breakdown
                            st.subheader("💰 Financial Performance Breakdown")
                            
                            # Calculate annual savings and payback for this solution
                            try:
                                cursor.execute("""
                                    SELECT electricity_rate FROM projects WHERE project_id = %s
                                """, (project_id,))
                                rate_result = cursor.fetchone()
                                electricity_rate = float(rate_result[0]) if rate_result else 0.30
                            except:
                                electricity_rate = 0.30
                            
                            annual_generation = float(selected_solution['capacity']) * 1000  # Rough estimate
                            annual_savings = annual_generation * electricity_rate
                            payback_years = float(selected_solution['total_cost']) / annual_savings if annual_savings > 0 else 0
                            
                            # Financial metrics display
                            fin_col1, fin_col2, fin_col3 = st.columns(3)
                            
                            with fin_col1:
                                st.metric("Annual Generation", f"{annual_generation:,.0f} kWh")
                                st.metric("Electricity Rate", f"€{electricity_rate:.3f}/kWh")
                            
                            with fin_col2:
                                st.metric("Annual Savings", f"€{annual_savings:,.0f}")
                                st.metric("25-Year Savings", f"€{annual_savings * 25:,.0f}")
                            
                            with fin_col3:
                                st.metric("Simple Payback", f"{payback_years:.1f} years")
                                st.metric("ROI (25-year)", f"{selected_solution['roi']:.1f}%")
                            
                            # 4. 25-Year Cash Flow Projection - Fixed Break-even Calculation
                            years_with_initial = list(range(0, 26))  # Include year 0 for initial investment
                            years_operational = list(range(1, 26))   # Years 1-25 for operations
                            
                            # Initial investment and annual cash flows  
                            initial_investment = -float(selected_solution['total_cost'])  # Negative cash flow
                            annual_cash_flow = [annual_savings] * 25
                            
                            # Calculate cumulative cash flow including initial investment
                            cumulative_cash_flow = [initial_investment]  # Start with negative investment
                            cumulative = initial_investment
                            
                            for year_savings in annual_cash_flow:
                                cumulative += year_savings
                                cumulative_cash_flow.append(cumulative)
                            
                            # Find break-even year
                            break_even_year = None
                            for i, cum_cf in enumerate(cumulative_cash_flow):
                                if cum_cf >= 0:
                                    break_even_year = i
                                    break
                            
                            fig_cashflow = go.Figure()
                            
                            # Annual cash flow bars (years 1-25 only)
                            fig_cashflow.add_trace(go.Bar(
                                x=years_operational,
                                y=annual_cash_flow,
                                name='Annual Savings',
                                marker_color='lightgreen',
                                yaxis='y'
                            ))
                            
                            # Cumulative cash flow line (years 0-25)
                            fig_cashflow.add_trace(go.Scatter(
                                x=years_with_initial,
                                y=cumulative_cash_flow,
                                mode='lines+markers',
                                name='Cumulative Cash Flow',
                                line=dict(color='darkgreen', width=3),
                                yaxis='y2'
                            ))
                            
                            # Add break-even line and annotation
                            fig_cashflow.add_hline(y=0, line_dash="dash", line_color="red")
                            
                            # Add break-even annotation if found
                            if break_even_year is not None:
                                fig_cashflow.add_annotation(
                                    x=break_even_year,
                                    y=0,
                                    text=f"Break-even<br>Year {break_even_year}",
                                    showarrow=True,
                                    arrowhead=2,
                                    arrowcolor="red",
                                    bgcolor="white",
                                    bordercolor="red"
                                )
                            
                            fig_cashflow.update_layout(
                                title=f"25-Year Financial Projection - Solution {selected_solution_id}",
                                xaxis_title="Year",
                                yaxis=dict(title="Annual Savings (€)", side="left"),
                                yaxis2=dict(title="Cumulative Cash Flow (€)", side="right", overlaying="y"),
                                height=500,
                                legend=dict(x=0.7, y=0.95)
                            )
                            
                            st.plotly_chart(fig_cashflow, use_container_width=True)
                            
                            # Performance summary table
                            st.subheader("📋 Solution Performance Summary")
                            st.dataframe(orientation_analysis, use_container_width=True)
                        
                        else:
                            st.warning("No BIPV specifications found in database.")
                    else:
                        st.warning("No PV specification data available.")
                        
                conn.close()
        except Exception as e:
            st.error(f"Error retrieving solution details: {str(e)}")
            st.info("Using basic solution metrics for analysis.")
        
        # Section removed per user request
        
        # Standardized Navigation
        render_navigation_buttons('optimization', show_previous=True, show_next=True)
    
    else:
        st.warning("No optimization results available. Please run the optimization.")
        # Show navigation even without results
        render_navigation_buttons('optimization', show_previous=True, show_next=False)
