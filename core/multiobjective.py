"""Weighted genetic search and NSGA-II on identical inputs and constraints.

NSGA-II: elitist nondominated sorting and crowding selection through DEAP.
The reported Pareto front is among evaluated candidates, not a global certificate.
Reference: Deb et al. (2002), DOI 10.1109/4235.996017.
"""
import random
import time
import numpy as np
import pandas as pd
from deap import base, tools
from core.energy_contracts import annual_element_yield, annual_netting
from core.optimization_engine import (validate_search_inputs, evaluate_individual,
                                      simple_genetic_algorithm, analyze_optimization_results)


class Objectives(base.Fitness):
    weights=(-1.0,1.0,1.0)  # Minimize capital cost, maximize energy and first-year ROI.


class Candidate(list):
    def __init__(self, mask):
        super().__init__(mask)
        self.fitness=Objectives()
        self.rank=0


def objective_values(mask,specs,demand,params,radiation):
    selected=specs[np.asarray(mask,dtype=bool)]
    cost=float(selected['total_cost_eur'].sum())
    energy=sum(annual_element_yield(row,radiation[str(row['element_id'])]) for _,row in selected.iterrows())
    total_demand=float(demand['predicted_demand'].sum()) if hasattr(demand,'columns') else sum(float(r['predicted_demand']) for r in demand)
    if cost<=0 or energy<=0 or energy/total_demand < params.get('min_coverage',.3):
        return None
    benefit=annual_netting(energy,total_demand,params['electricity_price'],params['export_rate'])['gross_benefit']
    maintenance=cost*params.get('maintenance_rate',.015) if params.get('include_maintenance',True) else 0
    return cost,float(energy),float((benefit-maintenance)/cost*100)


def nsga2(specs,demand,params,settings,radiation):
    n=validate_search_inputs(specs,demand,params,settings,radiation)
    size=int(settings['population_size'])
    rng=random.Random(settings.get('seed',42))
    archive={}
    evaluations=0

    def evaluate(mask):
        nonlocal evaluations
        values=objective_values(mask,specs,demand,params,radiation)
        evaluations+=1
        if values is None:
            return None
        candidate=Candidate(mask)
        candidate.fitness.values=values
        archive[tuple(mask)]=candidate
        return candidate

    # A feasible all-elements seed avoids confusing sparse random sampling with
    # infeasibility; for this monotonic coverage constraint it is a feasibility witness.
    full=evaluate([1]*n)
    if full is None:
        return pd.DataFrame(),{'evaluations':evaluations,'history':[],'seed':settings.get('seed',42)}
    population=[full]
    for _ in range(size-1):
        candidate=evaluate([rng.randrange(2) for _ in range(n)])
        population.append(candidate if candidate is not None else full)
    history=[]
    for generation in range(int(settings['generations'])):
        fronts=tools.sortNondominated(population,len(population))
        for rank,front in enumerate(fronts):
            tools.emo.assignCrowdingDist(front)
            for c in front:c.rank=rank

        def parent():
            a,b=rng.choice(population),rng.choice(population)
            if a.rank!=b.rank:return a if a.rank<b.rank else b
            if a.fitness.crowding_dist!=b.fitness.crowding_dist:
                return a if a.fitness.crowding_dist>b.fitness.crowding_dist else b
            return a if rng.random()<.5 else b

        offspring=[]
        for _ in range(size):
            a,b=parent(),parent()
            cut=rng.randrange(1,n) if n>1 else 1
            mask=list(a[:cut])+list(b[cut:])
            mask=[1-bit if rng.random()<settings['mutation_rate'] else bit for bit in mask]
            child=evaluate(mask)
            if child is not None:offspring.append(child)
        population=tools.selNSGA2(population+offspring,size)
        front=tools.sortNondominated(list(archive.values()),len(archive),first_front_only=True)[0]
        history.append({'generation':generation+1,'feasible_unique':len(archive),'front_size':len(front)})
    front=tools.sortNondominated(list(archive.values()),len(archive),first_front_only=True)[0]
    # Weighted preference orders the displayed front; it does not alter NSGA-II survival.
    ranked=sorted(front,key=lambda c:(-evaluate_individual(c,specs,demand,params,radiation)[0],tuple(c)))
    tuples=[(i,evaluate_individual(c,specs,demand,params,radiation)[0],0,list(c)) for i,c in enumerate(ranked)]
    report=analyze_optimization_results(tuples,specs,demand,params,radiation)
    report['optimization_method']='nsga-ii-v1'
    report['pareto_optimal']=True
    report['pareto_scope']='nondominated among evaluated feasible candidates'
    report['solution_id']=[f'NSGA_{i+1}' for i in range(len(report))]
    return report,{'evaluations':evaluations,'history':history,'seed':settings.get('seed',42),
                   'selection':'DEAP selNSGA2; rank/crowding binary tournament',
                   'objectives':['min capital cost','max annual generation','max first-year net ROI']}


def compare_searches(specs,demand,params,settings,radiation):
    started=time.perf_counter()
    weighted,weighted_history=simple_genetic_algorithm(specs,demand,params,settings,radiation)
    weighted_report=analyze_optimization_results(weighted,specs,demand,params,radiation)
    weighted_time=time.perf_counter()-started
    started=time.perf_counter()
    pareto,nsga_metadata=nsga2(specs,demand,params,settings,radiation)
    nsga_time=time.perf_counter()-started
    weighted_masks={tuple(row) for row in weighted_report.get('selection_mask',[])}
    pareto_masks={tuple(row) for row in pareto.get('selection_mask',[])}
    # Identical population/generations/seed, but evaluation budgets are reported,
    # not asserted equal: NSGA-II evaluates its initial population separately.
    comparison=pd.DataFrame([
        {'method':'Weighted genetic search','solutions':len(weighted_report),'runtime_seconds':weighted_time,
         'best_weighted_fitness':float(weighted_report['fitness_score'].max()) if len(weighted_report) else None,
         'scope':'weighted candidates'},
        {'method':'NSGA-II','solutions':len(pareto),'runtime_seconds':nsga_time,
         'best_weighted_fitness':float(pareto['fitness_score'].max()) if len(pareto) else None,
         'scope':'evaluated Pareto front'}])
    return {'weighted':weighted_report,'nsga2':pareto,'comparison':comparison,
            'metadata':{'seed':settings.get('seed',42),'settings':dict(settings),
                        'weighted_history':weighted_history,'nsga2':nsga_metadata,
                        'shared_masks':len(weighted_masks & pareto_masks),
                        'global_optimality_certified':False}}
