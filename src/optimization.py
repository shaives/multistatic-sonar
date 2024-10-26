from pyomo.environ import *
import random
import time
import sys

def create_optimization_model(instance, ocean_surface, ocean, detection_prob_rowsum_s, detection_prob, outdir):
    # Create concrete model
    model = ConcreteModel()
    
    # SETS
    model.ocean_surface = Set(initialize=ocean_surface.keys())
    model.ocean = Set(initialize=ocean)
    model.theta_range = Set(initialize=range(0, 180, instance.STEPS))
    
    # VARIABLES
    # Sources
    model.s = Var(model.ocean_surface, domain=Binary)
    # Receivers
    model.r = Var(model.ocean_surface, domain=Binary)
    
    # Coverage variable for GOAL=1
    if instance.GOAL == 1:
        model.c = Var(model.ocean, domain=Binary)
    
    # Y variables for linearization
    detection_keys = [(tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z) 
                     for tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z in detection_prob_rowsum_s]
    model.detection_keys = Set(initialize=detection_keys)
    
    def y_bounds(model, *keys):
        return (0, detection_prob_rowsum_s[keys])
    
    model.y = Var(model.detection_keys, domain=NonNegativeReals, bounds=y_bounds)
    
    # OBJECTIVE
    if instance.GOAL == 0:
        # Minimize deployment cost
        def obj_cost_rule(model):
            return (sum(instance.S * model.s[tx_x, tx_y, tx_z] for tx_x, tx_y, tx_z in model.ocean_surface) +
                   sum(instance.R * model.r[tx_x, tx_y, tx_z] for tx_x, tx_y, tx_z in model.ocean_surface))
        model.objective = Objective(rule=obj_cost_rule, sense=minimize)
    else:
        # Maximize coverage
        def obj_coverage_rule(model):
            percentage = 100.0/len(ocean)
            return sum(percentage * model.c[tar_x, tar_y, tar_z] 
                      for tar_x, tar_y, tar_z in model.ocean)
        model.objective = Objective(rule=obj_coverage_rule, sense=maximize)
    
    # CONSTRAINTS
    if instance.GOAL == 1:
        # Fix equipment quantities for coverage maximization
        def fix_sources_rule(model):
            return sum(model.s[tx_x, tx_y, tx_z] for tx_x, tx_y, tx_z in model.ocean_surface) == instance.S
        model.fix_sources = Constraint(rule=fix_sources_rule)
        
        def fix_receivers_rule(model):
            return sum(model.r[rx_x, rx_y, rx_z] for rx_x, rx_y, rx_z in model.ocean_surface) == instance.R
        model.fix_receivers = Constraint(rule=fix_receivers_rule)
    else:
        # Ensure at least one source and receiver for cost minimization
        def min_sources_rule(model):
            return sum(model.s[tx_x, tx_y, tx_z] for tx_x, tx_y, tx_z in model.ocean_surface) >= 1
        model.min_sources = Constraint(rule=min_sources_rule)
        
        def min_receivers_rule(model):
            return sum(model.r[rx_x, rx_y, rx_z] for rx_x, rx_y, rx_z in model.ocean_surface) >= 1
        model.min_receivers = Constraint(rule=min_receivers_rule)
    
    # Coverage constraints
    def coverage_rule(model, tar_x, tar_y, tar_z, theta):
        expr = sum(detection_prob_rowsum_s[tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z] * model.s[tx_x, tx_y, tx_z] -
                  model.y[tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z]
                  for tx_x, tx_y, tx_z in model.ocean_surface
                  if (tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z) in detection_prob_rowsum_s)
        
        if instance.GOAL == 1:
            expr -= model.c[tar_x, tar_y, tar_z]
            return expr >= 0
        else:
            return expr >= 1
            
    model.coverage_constraint = Constraint(model.ocean, model.theta_range, rule=coverage_rule)
    
    # Linearization constraints
    def linearization_rule(model, tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z):
        if (tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z) in detection_prob_rowsum_s:
            expr = (model.y[tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z] -
                   detection_prob_rowsum_s[tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z] * model.s[tx_x, tx_y, tx_z])
            
            for rx_x, rx_y, rx_z in model.ocean_surface:
                if (tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z, rx_x, rx_y, rx_z) in detection_prob:
                    expr += (detection_prob[tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z, rx_x, rx_y, rx_z] * 
                            model.r[rx_x, rx_y, rx_z])
            
            return expr >= 0
        return Constraint.Skip
    
    model.linearization = Constraint(model.detection_keys, rule=linearization_rule)
    
    return model

def solve_model(model, instance, solver_name='glpk'):
    # Create solver interface
    solver = SolverFactory(solver_name)
    
    # Set solver options
    if solver_name == 'cplex':
        solver.options['timelimit'] = instance.TIMELIMIT
        solver.options['mipgap'] = 0.0
        solver.options['workmem'] = instance.RAM
    elif solver_name == 'gurobi':
        solver.options['TimeLimit'] = instance.TIMELIMIT
        solver.options['MIPGap'] = 0.0
    # Add other solver-specific options as needed
    
    # Solve
    start_time = time.time()
    results = solver.solve(model, tee=True)
    end_time = time.time()
    
    print(f"Solution time: {end_time - start_time:.2f} seconds")
    
    # Process results
    if (results.solver.status == SolverStatus.ok and
        results.solver.termination_condition == TerminationCondition.optimal):
        print("Optimal solution found")
        print(f"Objective value: {value(model.objective)}")
    elif results.solver.termination_condition == TerminationCondition.maxTimeLimit:
        print("Time limit reached")
        print(f"Best objective value found: {value(model.objective)}")
    else:
        print("Solver Status:", results.solver.status)
        print("Termination Condition:", results.solver.termination_condition)
    
    return results

