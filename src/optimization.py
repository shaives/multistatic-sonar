from pyomo.environ import *
import time
import random

def create_optimization_model(instance, ocean_surface, ocean, detection_prob_rowsum_s, detection_prob):
    # Create concrete model
    model = ConcreteModel()
    
    # Convert all dictionary keys to lists for Set initialization
    # ocean_surface and ocean are dictionaries with coordinate tuples as keys
    model.ocean_surface = Set(initialize=list(ocean_surface.keys()))
    model.ocean = Set(initialize=list(ocean.keys()))
    model.theta_range = Set(initialize=list(range(0, 180, instance.STEPS)))
    
    # Create set for the detection keys from detection_prob_rowsum_s
    # These are 7-tuples (tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z)
    model.detection_keys = Set(dimen=7, initialize=list(detection_prob_rowsum_s.keys()))
    
    # VARIABLES
    # Sources and receivers are indexed by 3D coordinates from ocean_surface
    model.s = Var(model.ocean_surface, domain=Binary)
    model.r = Var(model.ocean_surface, domain=Binary)
    
    # Coverage variable for GOAL=1, indexed by ocean coordinates
    if instance.GOAL == 1:
        model.c = Var(model.ocean, domain=Binary)
    
    # Y variables for linearization, indexed by detection_keys
    def y_bounds(model, *keys):
        return (0, detection_prob_rowsum_s[keys])
    
    model.y = Var(model.detection_keys, domain=NonNegativeReals, bounds=y_bounds)
    
    # OBJECTIVE
    if instance.GOAL == 0:
        # Minimize deployment cost
        def obj_cost_rule(model):
            return (sum(instance.S * model.s[loc] for loc in model.ocean_surface) +
                   sum(instance.R * model.r[loc] for loc in model.ocean_surface))
        model.objective = Objective(rule=obj_cost_rule, sense=minimize)
    else:
        # Maximize coverage
        def obj_coverage_rule(model):
            percentage = 100.0/len(ocean)
            return sum(percentage * model.c[loc] for loc in model.ocean)
        model.objective = Objective(rule=obj_coverage_rule, sense=maximize)
    
    # CONSTRAINTS
    if instance.GOAL == 1:
        # Fix equipment quantities for coverage maximization
        def fix_sources_rule(model):
            return sum(model.s[loc] for loc in model.ocean_surface) == instance.S
        model.fix_sources = Constraint(rule=fix_sources_rule)
        
        def fix_receivers_rule(model):
            return sum(model.r[loc] for loc in model.ocean_surface) == instance.R
        model.fix_receivers = Constraint(rule=fix_receivers_rule)
    else:
        # Ensure at least one source and receiver for cost minimization
        def min_sources_rule(model):
            return sum(model.s[loc] for loc in model.ocean_surface) >= 1
        model.min_sources = Constraint(rule=min_sources_rule)
        
        def min_receivers_rule(model):
            return sum(model.r[loc] for loc in model.ocean_surface) >= 1
        model.min_receivers = Constraint(rule=min_receivers_rule)
    
    # Coverage constraints
    def coverage_rule(model, tar_x, tar_y, tar_z, theta):
        relevant_keys = [k for k in model.detection_keys 
                        if k[0] == tar_x and k[1] == tar_y and k[2] == tar_z and k[3] == theta]
        
        expr = sum(detection_prob_rowsum_s[k] * model.s[(k[4], k[5], k[6])] -
                  model.y[k] for k in relevant_keys)
        
        if instance.GOAL == 1:
            expr -= model.c[(tar_x, tar_y, tar_z)]
            return expr >= 0
        else:
            return expr >= 1
    
    # Generate coverage constraint for each ocean point and angle
    model.coverage_constraints = Constraint(
        ((x, y, z, theta) for x, y, z in model.ocean for theta in model.theta_range),
        rule=coverage_rule
    )
    
    # Linearization constraints
    def linearization_rule(model, *keys):
        tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z = keys
        source_loc = (tx_x, tx_y, tx_z)
        
        expr = (model.y[keys] - detection_prob_rowsum_s[keys] * model.s[source_loc])
        
        # Add receiver terms if they exist in detection_prob
        for rx_x, rx_y, rx_z in model.ocean_surface:
            full_key = (tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z, rx_x, rx_y, rx_z)
            if full_key in detection_prob:
                expr += detection_prob[full_key] * model.r[(rx_x, rx_y, rx_z)]
        
        return expr >= 0
    
    model.linearization = Constraint(model.detection_keys, rule=linearization_rule)
    
    return model

def apply_heuristic(model, instance, ocean_surface, solver_name='cplex'):

    print(f"Running {instance.HEURISTIC} rounds of heuristic")
    # Create solver interface
    if solver_name == 'cplex':
        solver = SolverFactory('cplex_direct', executable='~/opt/ibm/ILOG/CPLEX_Studio1210/cplex/bin/x86-64_linux/cplex')
    elif solver_name == 'gurobi':    
        solver = SolverFactory(solver_name)
    
    if instance.GOAL == 0:  # minimize cost for deployed equipment

        print(f"Running heuristic for cost minimization = 0")

        best_obj = float('inf')
        best_sources = {}
        best_receivers = {}
        
        # PREQUEL
        fixed_receivers = dict(ocean_surface)  # Start with all positions
        old_obj = float('inf')
        
        while True:
            # Fix receivers and free sources
            for rx_x, rx_y, rx_z in model.ocean_surface:
                if (rx_x, rx_y, rx_z) in fixed_receivers:
                    model.r[rx_x, rx_y, rx_z].fix(1)
                else:
                    model.r[rx_x, rx_y, rx_z].fix(0)
                    
            for tx_x, tx_y, tx_z in model.ocean_surface:
                model.s[tx_x, tx_y, tx_z].unfix()
            
            # Solve for sources
            print("Solving for sources")
            results = solver.solve(model, tee=True)
            print(f"Solver status: {results.solver.status}")
            if results.solver.status == SolverStatus.ok:

                obj = value(model.objective)
                fixed_sources = {(tx_x, tx_y, tx_z): 1 for tx_x, tx_y, tx_z in model.ocean_surface if value(model.s[tx_x, tx_y, tx_z]) > 0.999}
                
                # Fix sources and free receivers
                for tx_x, tx_y, tx_z in model.ocean_surface:
                    if (tx_x, tx_y, tx_z) in fixed_sources:
                        model.s[tx_x, tx_y, tx_z].fix(1)
                    else:
                        model.s[tx_x, tx_y, tx_z].fix(0)
                        
                for rx_x, rx_y, rx_z in model.ocean_surface:
                    model.r[rx_x, rx_y, rx_z].unfix()
                
                # Solve for receivers
                print("Solving for receivers")
                results = solver.solve(model, tee=True)
                
                if results.solver.status == SolverStatus.ok:
                    obj = value(model.objective)
                    fixed_receivers = {(rx_x, rx_y, rx_z): 1 for rx_x, rx_y, rx_z in model.ocean_surface if value(model.r[rx_x, rx_y, rx_z]) > 0.999}
                    
                    if old_obj > obj:
                        old_obj = obj
                    else:
                        break
            
            best_receivers = fixed_receivers
            best_sources = fixed_sources
            best_obj = obj
            
            number_of_sources = len(fixed_sources)
            number_of_receivers = len(fixed_receivers)
            
            print(f"  Found new incumbent at iteration 0 with objective value {obj}")
            
            # Add constraint for number of sources
            model.del_component('source_count_constraint')
            model.source_count_constraint = Constraint(
                expr = sum(model.s[tx_x, tx_y, tx_z] for tx_x, tx_y, tx_z in model.ocean_surface) == number_of_sources
            )
            
            # LOOP HEURISTIC
            list_of_fixed_sources = []
            
            for round in range(1, instance.HEURISTIC + 1, 1):
                print(f"----------{round+1}-----------")
                
                while True:

                    fixed_sources = {}
                    ocean_surface_list = list(ocean_surface.keys())

                    while len(fixed_sources) < number_of_sources:

                        tx_x, tx_y, tx_z = random.choice(ocean_surface_list)

                        if (tx_x, tx_y, tx_z) not in fixed_sources:

                            fixed_sources[tx_x, tx_y, tx_z] = 1

                    if fixed_sources not in list_of_fixed_sources:

                        list_of_fixed_sources.append(fixed_sources)
                        break

                # Fix sources and free receivers
                for tx_x, tx_y, tx_z in model.ocean_surface:

                    if (tx_x, tx_y, tx_z) in fixed_sources:
                        model.s[tx_x, tx_y, tx_z].fix(1)
                    else:
                        model.s[tx_x, tx_y, tx_z].fix(0)

                for rx_x, rx_y, rx_z in model.ocean_surface:
                    model.r[rx_x, rx_y, rx_z].unfix()
                    
                results = solver.solve(model, tee=True)

                if results.solver.termination_condition != TerminationCondition.infeasible:
                    obj = value(model.objective)
                    fixed_receivers = {(rx_x, rx_y, rx_z): 1 for rx_x, rx_y, rx_z in model.ocean_surface if value(model.r[rx_x, rx_y, rx_z]) > 0.999}

                    if best_obj > obj:

                        best_obj = obj
                        best_receivers = fixed_receivers
                        best_sources = fixed_sources
                        print(f"  Found new incumbent at iteration {round} with objective value {obj}")
    
    else:  # GOAL = 1 (maximize coverage)

        print(f"Running heuristic for coverage maximization = 1")

        best_obj = -1
        best_sources = []
        best_receivers = []
        list_of_fixed_sources = []
        
        for round in range(1, instance.HEURISTIC + 1, 1):
            print(f"----------{round}-----------")
            
            while True:
                fixed_sources = {}
                ocean_surface_list = list(ocean_surface.keys())

                while len(fixed_sources) < instance.S:

                    tx_x, tx_y, tx_z = random.choice(ocean_surface_list)

                    if (tx_x, tx_y, tx_z) not in fixed_sources:
                        fixed_sources[tx_x, tx_y, tx_z] = 1

                if fixed_sources not in list_of_fixed_sources:

                    list_of_fixed_sources.append(fixed_sources)
                    break
            
            print(f"Fixing sources at: {fixed_sources}")
            old_obj = -1
            
            while True:

                # Fix sources and free receivers
                for tx_x, tx_y, tx_z in model.ocean_surface:

                    if (tx_x, tx_y, tx_z) in fixed_sources:
                        model.s[tx_x, tx_y, tx_z].fix(1)
                    else:
                        model.s[tx_x, tx_y, tx_z].fix(0)

                for rx_x, rx_y, rx_z in model.ocean_surface:
                    model.r[rx_x, rx_y, rx_z].unfix()

                results = solver.solve(model, tee=False)

                if results.solver.status == SolverStatus.ok:

                    obj = value(model.objective)
                    print(f"Solution value (ocean coverage percentage) = {obj}")
                    
                    fixed_receivers = {(rx_x, rx_y, rx_z): 1 
                    for rx_x, rx_y, rx_z in model.ocean_surface 
                        if value(model.r[rx_x, rx_y, rx_z]) > 0.999}
                    
                    # Fix receivers and free sources
                    for rx_x, rx_y, rx_z in model.ocean_surface:

                        if (rx_x, rx_y, rx_z) in fixed_receivers:
                            model.r[rx_x, rx_y, rx_z].fix(1)
                        else:
                            model.r[rx_x, rx_y, rx_z].fix(0)
                            
                    for tx_x, tx_y, tx_z in model.ocean_surface:
                        model.s[tx_x, tx_y, tx_z].unfix()
                    
                    results = solver.solve(model, tee=False)
                    
                    if results.solver.status == SolverStatus.ok:

                        obj = value(model.objective)
                        print(f"Solution value (ocean coverage percentage) = {obj}")
                        
                        fixed_sources = {(tx_x, tx_y, tx_z): 1 
                        for tx_x, tx_y, tx_z in model.ocean_surface 
                            if value(model.s[tx_x, tx_y, tx_z]) > 0.999}
                        
                        if old_obj < obj:
                            old_obj = obj
                        else:
                            break
            
            if best_obj < obj:
                best_obj = obj
                best_receivers = fixed_receivers
                best_sources = fixed_sources
                print(f"  Found new incumbent at iteration {round} with objective value {obj}")
    
    # Set model to best solution found
    for rx_x, rx_y, rx_z in model.ocean_surface:

        if (rx_x, rx_y, rx_z) in best_receivers:
            model.r[rx_x, rx_y, rx_z].fix(1)
        else:
            model.r[rx_x, rx_y, rx_z].fix(0)
            
    for tx_x, tx_y, tx_z in model.ocean_surface:

        if (tx_x, tx_y, tx_z) in best_sources:
            model.s[tx_x, tx_y, tx_z].fix(1)
        else:
            model.s[tx_x, tx_y, tx_z].fix(0)
    
    # Solve one more time with fixed values
    results = solver.solve(model, tee=False)
    
    # Unfix all variables for the main solve
    for tx_x, tx_y, tx_z in model.ocean_surface:
        model.s[tx_x, tx_y, tx_z].unfix()
    for rx_x, rx_y, rx_z in model.ocean_surface:
        model.r[rx_x, rx_y, rx_z].unfix()
    
    return best_obj, best_sources, best_receivers

def solve_model(model, instance, ocean_surface, outdir, solver_name='cplex'):
    
    # Create solver interface
    if solver_name == 'cplex':
        solver = SolverFactory('cplex_direct', executable='~/opt/ibm/ILOG/CPLEX_Studio1210/cplex/bin/x86-64_linux/cplex')
        solver.options['timelimit'] = instance.TIMELIMIT_HEURISTIC
    elif solver_name == 'gurobi':    
        solver = SolverFactory(solver_name)
        solver.options['TimeLimit'] = instance.TIMELIMIT_HEURISTIC

    # Apply heuristic if requested
    if instance.HEURISTIC > 0:

        best_obj, best_sources, best_receivers = apply_heuristic(model, instance, ocean_surface, solver_name)
        print(f"Heuristic found solution with objective value: {best_obj}")
        
        # Use heuristic solution to warm start the main solve
        # First fix the best solution found
        for tx_x, tx_y, tx_z in model.ocean_surface:

            if (tx_x, tx_y, tx_z) in best_sources:
                model.s[tx_x, tx_y, tx_z].fix(1)
            else:
                model.s[tx_x, tx_y, tx_z].fix(0)
                
        for rx_x, rx_y, rx_z in model.ocean_surface:

            if (rx_x, rx_y, rx_z) in best_receivers:
                model.r[rx_x, rx_y, rx_z].fix(1)
            else:
                model.r[rx_x, rx_y, rx_z].fix(0)
        
        # Solve once with fixed values to get a valid starting point
        results = solver.solve(model, tee=True)
        
        # Unfix all variables for the main solve
        for tx_x, tx_y, tx_z in model.ocean_surface:
            model.s[tx_x, tx_y, tx_z].unfix()
        for rx_x, rx_y, rx_z in model.ocean_surface:
            model.r[rx_x, rx_y, rx_z].unfix()
    
    # Write the model before main solve
    model.write(outdir + "/bison.lp", io_options={'symbolic_solver_labels': True})
    
    # Set solver parameters
    if solver.name == 'cplex':
        solver.options['timelimit'] = instance.TIMELIMIT
        solver.options['mip_start'] = 1
        solver.options['mipgap'] = 0.0
        solver.options['workmem'] = instance.RAM
        solver.options['mip.pool.capacity'] = 5
    elif solver.name == 'gurobi':
        solver.options['TimeLimit'] = instance.TIMELIMIT
        solver.options['WarmStart'] = 1
        solver.options['MIPGap'] = 0.0
        solver.options['PoolSolutions'] = 5
        solver.options['PoolSearchMode'] = 2
    
    # Set solver parameters for main solve
    if instance.SOLVE == 0:  # solve root relaxation
        # Relax integer variables
        for v in model.component_data_objects(Var):
            if v.domain == Binary:
                v.domain = UnitInterval
                
        # Write relaxed model
        model.write(outdir + "/bison_relaxed.lp", io_options={'symbolic_solver_labels': True})

        start_time = time.time()
        results = solver.solve(model, tee=True, load_solutions=True)
        solve_time = time.time() - start_time

        print(f"Root relaxation objective value: {value(model.objective)}")
        
    elif instance.SOLVE == 1:  # solve root + cuts
        solver.options['cuts'] = 2  # Enable cuts
        solver.options['maxnodes'] = 0  # Only root node
        
        # Write model with cuts enabled
        model.write(outdir + "/bison_cuts.lp", io_options={'symbolic_solver_labels': True})

        start_time = time.time()
        results = solver.solve(model, tee=True, load_solutions=True)
        solve_time = time.time() - start_time

        print(f"Root + cuts objective value: {value(model.objective)}")
    
    else:  # full solve

        start_time = time.time()
        results = solver.solve(model, tee=True, load_solutions=True)
        solve_time = time.time() - start_time
        
        if (results.solver.status == SolverStatus.ok and results.solver.termination_condition == TerminationCondition.optimal):
            print("Optimal solution found")
        elif results.solver.termination_condition == TerminationCondition.maxTimeLimit:
            print("Time limit reached")
        
        final_obj = value(model.objective)
        print(f"Final objective value: {final_obj}")
        
        # Compare with heuristic if it was used
        if instance.HEURISTIC > 0:
            if instance.GOAL == 0:  # minimization
                improvement = ((best_obj - final_obj) / best_obj * 100)
                if improvement > 0:
                    print(f"Final solution improved heuristic solution by {improvement:.2f}%")
            else:  # maximization
                improvement = ((final_obj - best_obj) / best_obj * 100)
                if improvement > 0:
                    print(f"Final solution improved heuristic solution by {improvement:.2f}%")
        
    # Write final model state
    model.write(outdir + "/bison_final.lp", io_options={'symbolic_solver_labels': True})
        
    print(f"Total solve time: {solve_time:.2f} seconds")
    return None