#! /usr/bin/python3

# running python3.10 and cplex 22.1.1
import sys
import time
import os
import shutil
import importlib
import random


from math import *
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np

import cplex
from cplex.callbacks import IncumbentCallback
from cplex.callbacks import LazyConstraintCallback
from cplex.callbacks import UserCutCallback
from cplex.exceptions import CplexSolverError

from src.output_func import *
from src.functions import *
from src.classes import *

# ---------------------------------------------------
# --- let's start
# ---------------------------------------------------

if __name__ == '__main__':

    try:

        filename = sys.argv[1]

        filepath = os.path.join("cfg", filename + '.py')

        if os.path.isfile(filepath):

            instance = importlib.import_module("cfg." + filename)
            start_time = time.time()

    except IndexError:

        print("File not found in the 'cfg' folder.")
    
    # creating an output directory and copy config file
    if not os.path.exists('outputs'):
        os.mkdir('outputs')
    outdir = 'outputs/' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '_' + filename
    os.mkdir(outdir)
    shutil.copy2("./cfg/" + filename + ".py", outdir)

    # redirect output to screen and logfile
    sys.stdout = Logger(outdir) 

    print(f"BISON - "+color.BOLD+"BI"+color.END+"static "+color.BOLD+"S"+color.END+"onar "+color.BOLD+"O"+color.END+"ptimizatio"+color.BOLD+"N"+color.END)
    print(f"")
    print(f"                                                                                           ")
    print(f"                                   @@@@@@@@@                                               ")
    print(f"                               @@@@         @@@@                                           ")
    print(f"                            @@@                 @@@                                        ")
    print(f"                         @@@                       @@@@                                    ")
    print(f"                       @@                             @@@@@                                ")
    print(f"                     @@@                                   @@@@                            ")
    print(f"                   @@@                                         @@@@                        ")
    print(f"         @@@@@@@@@@                                                @@@@                    ")
    print(f"     @@@@                                   @                          @@@@@               ")
    print(f"   @@                                       @@                              @@@@@@         ")
    print(f"  @@           @                              @@                              @@@@@        ")
    print(f" @@            @@                              @                                 @@@@      ")
    print(f" @            @ @                               @                                  @@@     ")
    print(f" @            @ @                               @                                    @@    ")
    print(f" @          @@@ @@                             @@                                   @  @   ")
    print(f"@@            @@@                             @                                     @@  @  ")
    print(f" @@                                           @@               @@                   @@@ @@ ")
    print(f"  @                                         @@                   @                  @ @@@@ ")
    print(f"   @@         @                             @                     @@                @ @ @@ ")
    print(f"     @@    @@@                               @                     @@              @@ @ @  ")
    print(f"      @@                                     @@                 @@@  @             @ @@@@  ")
    print(f"        @                                    @@               @@     @@@          @@ @  @@ ")
    print(f"        @                                     @@     @@@@@@@@@     @@   @@@@        @@   @@")
    print(f"         @                 @                  @@@@@@@       @     @         @@@       @   @")
    print(f"          @@@@@@@@@        @@                @@             @     @            @      @@ @ ")
    print(f"                   @@@   @@  @              @               @    @              @@    @@   ")
    print(f"                      @  @    @            @               @    @                @@   @@   ")
    print(f"                       @@      @@          @             @@    @                 @@   @@   ")
    print(f"                       @@       @@    @@@@@            @@@   @@                  @@   @@   ")
    print(f"                               @@@  @@@              @@    @@                    @@   @@   ")
    print(f"                             @@    @@              @@@@@@@@                     @    @@@   ")
    print(f"                             @@@@@@@@                                          @@@@@@@     ")
    print(f"")
    print(f"")

    print(f"Called")
    
    # ---------------------------------------------------
    # --- read ocean elevation data file
    # ---------------------------------------------------

    map, ocean, ocean_surface, min_depth, max_depth = reading_in_ocean_data(instance)

    # ---------------------------------------------------
    # --- create outputs
    # ---------------------------------------------------

    # output latex map
    create_latex_map(instance, map, min_depth, max_depth, outdir)

    # output ocean pixels
    create_ocean_dat(ocean, outdir)

    # output map
    create_map_dat(instance, map, outdir)

    # plot function g
    create_plot_func_g(instance, outdir)

    # ---------------------------------------------------
    # --- compute model
    # ---------------------------------------------------

    # compute coverage

    detection_prob = compute_coverage_triples(instance, ocean, ocean_surface)

    if len(instance.TS) == 0:
        instance.STEPS = 180

    # computing the rowsum in detection_prob

    print(f"Computing detection prob")

    # should we maybe go only with one varient???

    start_time_prob = time.time()

    detection_prob_rowsum_r = {}

    max = -10e+10
    min = 10e+10

    for tar_x, tar_y, tar_z in ocean:
        for theta in range(0,180,instance.STEPS): # target angle
            for rx_x, rx_y, rx_z in ocean_surface:
                sum = 0
                for tx_x, tx_y, tx_z in ocean_surface:

                    if (tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z, rx_x, rx_y, rx_z) in detection_prob:
                        sum = sum + detection_prob[tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z, rx_x, rx_y, rx_z]

                detection_prob_rowsum_r[tar_x, tar_y, tar_z, theta, rx_x, rx_y, rx_z] = sum

                if sum > max:
                    max = sum
                if sum < min:
                    min = sum

    if instance.BOUND == 1:
            
        for tar_x, tar_y, tar_z in ocean:
            for theta in range(0,180,instance.STEPS): # target angle
                for rx_x, rx_y, rx_z in ocean_surface:

                    detection_prob_rowsum_r[tar_x, tar_y, tar_z, theta, rx_x, rx_y, rx_z] = max


    detection_prob_rowsum_s = {}

    for tar_x, tar_y, tar_z in ocean:
        for theta in range(0,180,instance.STEPS): # target angle
            for tx_x, tx_y, tx_z in ocean_surface:
                sum = 0
                for rx_x, rx_y, rx_z in ocean_surface:
                    if (tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z, rx_x, rx_y, rx_z) in detection_prob:
                        sum = sum + detection_prob[tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z, rx_x, rx_y, rx_z]

                detection_prob_rowsum_s[tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z] = sum

                if sum > max:
                    max = sum
                if sum < min:
                    min = sum

    if instance.BOUND == 1:
        for tar_x, tar_y, tar_z in ocean:
            for theta in range(0,180,instance.STEPS): # target angle
                for tx_x, tx_y, tx_z in ocean_surface:

                    detection_prob_rowsum_s[tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z] = max

    end_time_prob = time.time()

    print(f"It took {(end_time_prob - start_time_prob):.2f} sec to calc detection prob")

    # ---------------------------------------------------
    # --- set up optimization model
    # ---------------------------------------------------

    model = cplex.Cplex()

    print(f"IBM ILOG CPLEX version number: {model.get_version()}")

    # VARIABLES

    s = {} # sources, =1, if a source is located on candidate location tx_x, tx_y, tx_z
    r = {} # receivers, =1, if a receiver is located on candidate location tx_x, tx_y, tx_z

    for tx_x, tx_y, tx_z in ocean_surface:
        
        s[tx_x, tx_y, tx_z] = "s#"+str(tx_x)+"#"+str(tx_y)+"#"+str(tx_z)
        r[tx_x, tx_y, tx_z] = "r#"+str(tx_x)+"#"+str(tx_y)+"#"+str(tx_z)

        if instance.GOAL == 0: # optimization goal: cover all pixels, minimize deployment cost
            model.variables.add(obj = [instance.S], names = [s[tx_x, tx_y, tx_z]], lb = [0], ub = [1], types = ["B"])
            model.variables.add(obj = [instance.R], names = [r[tx_x, tx_y, tx_z]], lb = [0], ub = [1], types = ["B"])
        else: # deploy equipment, maximize coverage
            model.variables.add(names = [s[tx_x, tx_y, tx_z]], lb = [0], ub = [1], types = ["B"])
            model.variables.add(names = [r[tx_x, tx_y, tx_z]], lb = [0], ub = [1], types = ["B"])

    if instance.GOAL == 1: # deploy equipment, maximize coverage
        c = {} # coverage, =1, if some source-receiver pair covers location tar_x, tar_y, tar_z

        percentage = float("{0:.3f}".format(100.0/len(ocean)))

        for tar_x, tar_y, tar_z in ocean:
            c[tar_x, tar_y, tar_z] = "c#"+str(tar_x)+"#"+str(tar_y)+"#"+str(tar_z)
            model.variables.add(obj = [percentage], names = [c[tar_x, tar_y, tar_z]], lb = [0], ub = [1], types = ["B"])

    y = {}

    for tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z in detection_prob_rowsum_s:
        y[tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z] = "y#"+str(tar_x)+"#"+str(tar_y)+"#"+str(tar_z)+"#"+str(theta)+"#"+str(tx_x)+"#"+str(tx_y)+"#"+str(tx_z)

        model.variables.add(names = [y[tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z]], ub = [detection_prob_rowsum_s[tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z]], lb = [0], types = ["C"])

        # TODO: Setting y to general integer seems to help for cookie-cutter. Perform a deeper analysis of this initial observation
        #model.variables.add(names = [y[tar_x, tar_y, tar_z,theta,tx_x, tx_y, tx_z]], ub = [detection_prob_rowsum_s[tar_x, tar_y, tar_z,theta,tx_x, tx_y, tx_z]], lb = [0], types = ["I"])

    # CONSTRAINTS

    if instance.GOAL == 1:
        # for all models below, if the goal is to 'deploy equipment, maximize coverage', then here the equipment gets fixed

        thevars = []
        thecoefs = []

        for tx_x, tx_y, tx_z in ocean_surface:

            thevars.append(s[tx_x, tx_y, tx_z])
            thecoefs.append(1.0)

        model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [instance.S])

        thevars = []
        thecoefs = []

        for rx_x, rx_y, rx_z in ocean_surface:

            thevars.append(r[rx_x, rx_y, rx_z])
            thecoefs.append(1.0)

        model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [instance.R])

    else: # GOAL = 0
        # for all models below, if the goal is to 'minimize equipment', then at least one source and one receiver have to be deployed

        thevars = []
        thecoefs = []

        for tx_x, tx_y, tx_z in ocean_surface:

            thevars.append(s[tx_x, tx_y, tx_z])
            thecoefs.append(1.0)

        model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [1.0])

        thevars = []
        thecoefs = []

        for rx_x, rx_y, rx_z in ocean_surface:

            thevars.append(r[rx_x, rx_y, rx_z])
            thecoefs.append(1.0)

        model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [1.0])

    # 1st linearization from Oral, Kettani (1992) for senders

    # coverage for each ocean pixel
    
    for tar_x, tar_y, tar_z in ocean:
        for theta in range(0,180,instance.STEPS): # target angle
            thevars = []
            thecoefs = []
            
            for tx_x, tx_y, tx_z in ocean_surface:

                thevars.append(s[tx_x, tx_y, tx_z])
                thevars.append(y[tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z])
                thecoefs.append(detection_prob_rowsum_s[tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z])
                thecoefs.append(-1.0)

            if instance.GOAL == 1: # goal: deploy equipment, maximize coverage
                thevars.append(c[tar_x, tar_y, tar_z])
                thecoefs.append(-1.0)
                    
            if instance.GOAL == 0: # goal: cover all pixels
                model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [1.0])
            else: # goal: deploy equipment
                model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [0.0]) 
    
    # linearization constraints
    
    for tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z in detection_prob_rowsum_s:
        thevars = [y[tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z],s[tx_x, tx_y, tx_z]]
        thecoefs = [1.0,-detection_prob_rowsum_s[tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z]]
        
        for rx_x, rx_y, rx_z in ocean_surface:
            if (tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z, rx_x, rx_y, rx_z) in detection_prob:
                thevars.append(r[rx_x, rx_y, rx_z])
                thecoefs.append(detection_prob[tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z, rx_x, rx_y, rx_z])

        model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [0.0])  



    if instance.USERCUTS == 1:
        usercut_cb = model.register_callback(UsercutCallback)
        usercut_cb.number_of_calls = 0
        usercut_cb.number_of_cuts_added = 0
    else:
        usercut_cb = None

    # OBJECTIVE FUNCTION

    if instance.GOAL == 0: # goal: minimize cost for deployed equipment
        model.objective.set_sense(model.objective.sense.minimize)
    else: # goal: maximize coverage
        model.objective.set_sense(model.objective.sense.maximize)

    # set optimization parameters

    #model.parameters.threads.set(1);   # single core, no parallelism

    # HEURISTIC

    if instance.HEURISTIC > 0:
        print(f"Running {instance.HEURISTIC} rounds of heuristic")

        model.set_results_stream(None) # turn off messaging to screen
        model.set_warning_stream(None)

        if instance.GOAL == 0:
            best_obj = 10**10

            best_sources = []
            best_receivers = []

            #print(f"----------0-----------")

            # PREQUEL

            fixed_receivers = ocean_surface

            old_obj = 10**10

            while True:

                # fix the receiver variables of the positions in fixed_receivers to 1, and all others to 0
                # free the sources

                for (rx_x, rx_y, rx_z) in ocean_surface:
                    if (rx_x, rx_y, rx_z) in fixed_receivers:
                        model.variables.set_lower_bounds(r[rx_x, rx_y, rx_z],1)
                        model.variables.set_upper_bounds(r[rx_x, rx_y, rx_z],1)
                    else:
                        model.variables.set_lower_bounds(r[rx_x, rx_y, rx_z],0)
                        model.variables.set_upper_bounds(r[rx_x, rx_y, rx_z],0)

                for (tx_x, tx_y, tx_z) in ocean_surface:
                    model.variables.set_lower_bounds(s[tx_x, tx_y, tx_z],0)
                    model.variables.set_upper_bounds(s[tx_x, tx_y, tx_z],1)

                model.write(outdir+"/bison.lp")

                # get positions of sources

                model.solve()

                obj = model.solution.get_objective_value()
                #print(f"Solution value = {obj}")

                fixed_sources = {}

                for (tx_x, tx_y, tx_z) in ocean_surface:
                    if model.solution.get_values(s[tx_x, tx_y, tx_z]) > 0.999:
                        #print(f"got one source at {sx} {sy}")
                        fixed_sources[tx_x, tx_y, tx_z] = 1

                # fix the source variables of the positions in fixed_sources to 1, and all others to 0
                # free the receiver variables again

                for (tx_x, tx_y, tx_z) in ocean_surface:
                    if (tx_x, tx_y, tx_z) in fixed_sources:
                        model.variables.set_lower_bounds(s[tx_x, tx_y, tx_z],1)
                        model.variables.set_upper_bounds(s[tx_x, tx_y, tx_z],1)
                    else:
                        model.variables.set_lower_bounds(s[tx_x, tx_y, tx_z],0)
                        model.variables.set_upper_bounds(s[tx_x, tx_y, tx_z],0)

                for (rx_x, rx_y, rx_z) in ocean_surface:
                    model.variables.set_lower_bounds(r[rx_x, rx_y, rx_z],0)
                    model.variables.set_upper_bounds(r[rx_x, rx_y, rx_z],1)

                # get positions of sources
                
                model.solve()

                obj = model.solution.get_objective_value()
                #print(f"Solution value = {obj}")

                fixed_receivers = {}
                for (rx_x, rx_y, rx_z) in ocean_surface:
                    if model.solution.get_values(r[rx_x, rx_y, rx_z]) > 0.999:
                        #print(f"got one receiver at {rx} {ry}")
                        fixed_receivers[rx_x, rx_y, rx_z] = 1

                # LOOP
                if (old_obj > obj):
                    old_obj = obj
                else:
                    break

            best_receivers = fixed_receivers
            best_sources = fixed_sources
            best_obj = obj

            number_of_sources = len(fixed_sources)
            number_of_receivers = len(fixed_receivers)

            print(f"  Found new incumbent at iteration 0 with objective value {obj}")

            # number of sources fixed in the model

            thevars = []
            thecoefs = []

            for tx_x, tx_y, tx_z in ocean_surface:
                thevars.append(s[tx_x, tx_y, tx_z])
                thecoefs.append(1.0)

            model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [number_of_sources])

            # LOOP HEURISTIC

            list_of_fixed_sources = []

            for round in range(instance.HEURISTIC - 1):
                print(f"----------{round+1}-----------")

                # INNER LOOP

                while True:

                    fixed_sources = {}

                    while len(fixed_sources) < number_of_sources:
                        tx_x, tx_y, tx_z = random.choice(list(ocean_surface.keys()))

                        if (tx_x, tx_y, tx_z) not in fixed_sources:
                            fixed_sources[tx_x, tx_y, tx_z] = 1

                    if (fixed_sources not in list_of_fixed_sources):
                        list_of_fixed_sources.append(fixed_sources)
                        break

                    #print(f"do it again")

                # fix the source variables of the positions in fixed_sources to 1, and all others to 0
                # free the receivers

                for (tx_x, tx_y, tx_z) in ocean_surface:
                    if (tx_x, tx_y, tx_z) in fixed_sources:
                        model.variables.set_lower_bounds(s[tx_x, tx_y, tx_z],1)
                        model.variables.set_upper_bounds(s[tx_x, tx_y, tx_z],1)
                    else:
                        model.variables.set_lower_bounds(s[tx_x, tx_y, tx_z],0)
                        model.variables.set_upper_bounds(s[tx_x, tx_y, tx_z],0)

                for (rx_x, rx_y, rx_z) in ocean_surface:
                    model.variables.set_lower_bounds(r[rx_x, rx_y, rx_z],0)
                    model.variables.set_upper_bounds(r[rx_x, rx_y, rx_z],1)

                model.write(outdir+"/bison.lp")

                # get positions of sources

                model.solve()

                if (model.solution.get_status_string() != 'integer infeasible'):

                    obj = model.solution.get_objective_value()
                    #print(f"Solution value = {obj}")

                    fixed_receivers = {}
                    for (rx_x, rx_y, rx_z) in ocean_surface:
                        if model.solution.get_values(r[rx_x, rx_y, rx_z]) > 0.999:
                            #print(f"got one receiver at {rx} {ry}")
                            fixed_receivers[rx_x, rx_y, rx_z] = 1

                    if best_obj > obj:
                        best_obj = obj
                        best_receivers = fixed_receivers
                        best_sources = fixed_sources
                        print(f"  Found new incumbent at iteration {round} with objective value {obj}")

        else: # GOAL = 1
            best_obj = -1

            best_sources = []
            best_receivers = []

            list_of_fixed_sources = []

            for round in range(instance.HEURISTIC):
                print(f"----------{round}-----------")
                
                # INNER LOOP

                while True:
                    fixed_sources = {}

                    while len(fixed_sources) < instance.S:
                        tx_x, tx_y, tx_z = random.choice(list(ocean_surface.keys()))

                        if (tx_x, tx_y, tx_z) not in fixed_sources:
                            fixed_sources[tx_x, tx_y, tx_z] = 1

                    if fixed_sources not in list_of_fixed_sources:
                        list_of_fixed_sources.append(fixed_sources)
                        print(f"New: {fixed_sources}")
                        break

                    print(f"(Do it again)")

                print(f"Fixing sources at: {fixed_sources}")

                old_obj = -1

                while True:

                    # fix the source variables of the positions in fixed_sources to 1, and all others to 0
                    # free the receivers

                    for (tx_x, tx_y, tx_z) in ocean_surface:
                        if (tx_x, tx_y, tx_z) in fixed_sources:
                            model.variables.set_lower_bounds(s[tx_x, tx_y, tx_z],1)
                            model.variables.set_upper_bounds(s[tx_x, tx_y, tx_z],1)
                        else:
                            model.variables.set_lower_bounds(s[tx_x, tx_y, tx_z],0)
                            model.variables.set_upper_bounds(s[tx_x, tx_y, tx_z],0)

                    for (rx_x, rx_y, rx_z) in ocean_surface:
                        model.variables.set_lower_bounds(r[rx_x, rx_y, rx_z],0)
                        model.variables.set_upper_bounds(r[rx_x, rx_y, rx_z],1)

                    model.write(outdir+"/bison.lp")

                    # get positions of receivers

                    model.solve()

                    print(f"Solution value (ocean coverage percentage) = {model.solution.get_objective_value()}")

                    fixed_receivers = {}
                    for (rx_x, rx_y, rx_z) in ocean_surface:
                        if model.solution.get_values(r[rx_x, rx_y, rx_z]) > 0.999:
                            #print(f"got one receiver at {rx} {ry}")
                            fixed_receivers[rx_x, rx_y, rx_z] = 1

                    # fix the receiver variables of the positions in fixed_receivers to 1, and all others to 0
                    # free the source variables again

                    for (rx_x, rx_y, rx_z) in ocean_surface:
                        if (rx_x, rx_y, rx_z) in fixed_receivers:
                            model.variables.set_lower_bounds(r[rx_x, rx_y, rx_z],1)
                            model.variables.set_upper_bounds(r[rx_x, rx_y, rx_z],1)
                        else:
                            model.variables.set_lower_bounds(r[rx_x, rx_y, rx_z],0)
                            model.variables.set_upper_bounds(r[rx_x, rx_y, rx_z],0)

                    for (tx_x, tx_y, tx_z) in ocean_surface:
                        model.variables.set_lower_bounds(s[tx_x, tx_y, tx_z],0)
                        model.variables.set_upper_bounds(s[tx_x, tx_y, tx_z],1)

                    # get positions of sources

                    model.solve()

                    obj = model.solution.get_objective_value()
                    print(f"Solution value (ocean coverage percentage) = {obj}")

                    fixed_sources = {}
                    for (tx_x, tx_y, tx_z) in ocean_surface:
                        if model.solution.get_values(s[tx_x, tx_y, tx_z]) > 0.999:
                            #print(f"got one source at {sx} {sy}")
                            fixed_sources[tx_x, tx_y, tx_z] = 1

                    # LOOP
                    if (old_obj < obj):
                        old_obj = obj
                    else:
                        break


                if best_obj < obj:
                    best_obj = obj
                    best_receivers = fixed_receivers
                    best_sources = fixed_sources
                    print(f"  Found new incumbent at iteration {round} with objective value {obj}")

        # resort to best solution (as MIP starter)

        #print(f"best objective {best_obj}")
        #print(f"best receivers {best_receivers}")
        #print(f"best sources {best_sources}")

        for (rx_x, rx_y, rx_z) in ocean_surface:
            if (rx_x, rx_y, rx_z) in best_receivers:
                model.variables.set_lower_bounds(r[rx_x, rx_y, rx_z],1)
                model.variables.set_upper_bounds(r[rx_x, rx_y, rx_z],1)
            else:
                model.variables.set_lower_bounds(r[rx_x, rx_y, rx_z],0)
                model.variables.set_upper_bounds(r[rx_x, rx_y, rx_z],0)

        for (tx_x, tx_y, tx_z) in ocean_surface:
                    if (tx_x, tx_y, tx_z) in best_sources:
                        model.variables.set_lower_bounds(s[tx_x, tx_y, tx_z],1)
                        model.variables.set_upper_bounds(s[tx_x, tx_y, tx_z],1)
                    else:
                        model.variables.set_lower_bounds(s[tx_x, tx_y, tx_z],0)
                        model.variables.set_upper_bounds(s[tx_x, tx_y, tx_z],0)

        #model.write(outdir+"/bison.lp")
        model.solve()

        # free everything

        for (tx_x, tx_y, tx_z) in ocean_surface:
                    model.variables.set_lower_bounds(s[tx_x, tx_y, tx_z],0)
                    model.variables.set_upper_bounds(s[tx_x, tx_y, tx_z],1)

        for (rx_x, rx_y, rx_z) in ocean_surface:
                    model.variables.set_lower_bounds(r[rx_x, rx_y, rx_z],0)
                    model.variables.set_upper_bounds(r[rx_x, rx_y, rx_z],1)

        # turn on messaging to screen

        model.set_results_stream(sys.stdout)
        model.set_warning_stream(sys.stdout)


    # write model

    model.write(outdir + "/bison.lp")

    # solve model

    if instance.SOLVE == 0: # solve root relaxation (without cuts)
        model.set_problem_tar_ype(tar_ype=model.problem_tar_ype.LP)

        try:
            start = time.time()
            model.solve()
            end = time.time()
            print(f"It took {(end - start):.2f} sec to solve root")

        except (CplexSolverError) as exc:
            print(f"** Exception: {exc}")

        solution = model.solution
        print(f"Solution value = {solution.get_objective_value()}")
        quit()

    if instance.SOLVE == 1: # solve roots+cuts
        model.parameters.mip.limits.nodes.set(0)

        try:
            start = time.time()
            model.solve()
            end = time.time()
            print(f"It took {(end - start):.2f} sec to solve root+cuts")

        except (CplexSolverError) as exc:
            print(f"** Exception: {exc}")

        solution = model.solution
        print(f"Solution value = {solution.get_objective_value()}")
        print(f"Best bound = {solution.MIP.get_best_objective()}")
        quit()

    # solve to optimalitar_y (0.0%), until timelimit reached

    model.parameters.timelimit.set(instance.TIMELIMIT)
    model.parameters.mip.tolerances.mipgap.set(0.0)
    model.parameters.workmem.set(instance.RAM)
    model.parameters.mip.strategy.file.set(2)               # store node file on disk (uncompressed) when workmem is exceeded

    try:
        start = time.time()
        model.solve()
        end = time.time()
        print(f"It took {(end - start):.2f} sec to solve")

    except (CplexSolverError) as exc:
        print(f"** Exception: {exc}")

    # solution interpretation

    solution = model.solution

    objval = 0

    #print(f"Solution status = ", solution.get_status())

    if solution.get_status() == solution.status.MIP_optimal:
        print(f"MIP optimal")
    elif solution.get_status() == solution.status.MIP_time_limit_feasible:
        print(f"MIP time limit feasible")

    if solution.is_primal_feasible():
        objval = solution.get_objective_value()

        print(f"Solution value = {objval}")
        solution.write(outdir + "/bison.sol")
    else:
        print(f"No solution available.")

    bestbound = solution.MIP.get_best_objective()

    print(f"Best bound = {bestbound:.2f}")

    gap = 100.0

    if instance.GOAL == 0: # minimize cost
        if objval > 0:
            gap = (objval - bestbound) / objval * 100
    else: # maximize coverage
        if bestbound > 0:
            gap = (bestbound - objval) / bestbound * 100

    print(f"MIP gap = {gap:.2f}%")

    if instance.USERCUTS == 1:
        print(f"Calls of user cut callback: {usercut_cb.number_of_calls}")
        print(f"Number of user cut added: {usercut_cb.number_of_cuts_added}")

    if not solution.is_primal_feasible():
        quit()

    # ---------------------------------------------------
    # --- output solution on screen
    # ---------------------------------------------------

    print(f"Source locations:")
    for tx_x, tx_y, tx_z in ocean_surface:
        if solution.get_values(s[tx_x, tx_y, tx_z]) > 0.999:
            print(f"  ({tx_x}, {tx_y})")

    print(f"Receiver locations:")
    for rx_x, rx_y, rx_z in ocean_surface:
        if solution.get_values(r[rx_x, rx_y, rx_z]) > 0.999:
            print(f"  ({rx_x}, {rx_y})")

    if instance.GOAL == 1:
        print(f"Covered ocean pixels:")
        for tar_x, tar_y, tar_z in ocean:
            if solution.get_values(c[tar_x, tar_y, tar_z]) > 0.999:
                print(f"  ({tar_x}, {tar_y}, {tar_z})")

        print(f"Not covered ocean pixels:")
        for tar_x, tar_y, tar_z in ocean:
            if solution.get_values(c[tar_x, tar_y, tar_z]) < 0.001:
                print(f"  ({tar_x}, {tar_y}, {tar_z})")

    # ---------------------------------------------------
    # --- output solution to files
    # ---------------------------------------------------

    file = open(outdir + "/solution-r.csv","w+")

    file.write("rx ry\n")

    for rx_x, rx_y, rx_z in ocean_surface:
        if solution.get_values(r[rx_x, rx_y, rx_z]) > 0.999:
            file.write(str(rx_x)+" "+str(rx_y)+"\n")

    file.close()

    file = open(outdir+"/solution-s.csv","w+")

    file.write("sx sy\n")

    for tx_x, tx_y, tx_z in ocean_surface:
        if solution.get_values(s[tx_x, tx_y, tx_z]) > 0.999:
            file.write(str(tx_x)+" "+str(tx_y)+"\n")

    file.close()

    # ---------------------------------------------------
    # --- compute coverage value per pixel
    # ---------------------------------------------------

    cov_val = {}

    for tar_x, tar_y, tar_z in ocean:
        cov_val[tar_x, tar_y, tar_z] = 0

    for tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z, rx_x, rx_y, rx_z in detection_prob:
        if solution.get_values(s[tx_x, tx_y, tx_z]) > 0.999 and solution.get_values(r[rx_x, rx_y, rx_z]) > 0.999:
            cov_val[tar_x, tar_y, tar_z] = cov_val[tar_x, tar_y, tar_z] + detection_prob[tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z, rx_x, rx_y, rx_z]

    
    # ---------------------------------------------------
    # --- output solution as latex
    # ---------------------------------------------------

    paperwidth = instance.X+5
    paperheight = instance.Y+5

    file = open(outdir+"/solution.tex","w+")

    file.write("\\documentclass[12pt]{article}\n")
    file.write("\\usepackage{tikz}\n")
    file.write("\\usepackage{pgfplots}\n")
    file.write("\\usepackage[paperwidth="+str(paperwidth)+"cm, paperheight="+str(paperheight)+"cm, margin=1cm]{geometry}\n")
    file.write("\\begin{document}\n")
    file.write("\\begin{tikzpicture}\n")
    file.write("	\\begin{axis}[\n")
    file.write("	xtick={1,...,"+str(instance.X)+"},\n")
    file.write("	ytick={1,...,"+str(instance.Y)+"},\n")
    file.write("	width="+str(instance.X+1)+"cm,\n")
    file.write("	height="+str(instance.Y+1)+"cm,\n")
    file.write("	xmin=0.5,\n")
    file.write("	xmax="+str(instance.X+0.5)+",\n")
    file.write("	ymin=0.5,\n")
    file.write("	ymax="+str(instance.Y+0.5)+",\n")
    file.write("	xlabel={$x$},\n")
    file.write("	ylabel={$y$},\n")
    file.write("	grid=major,\n")
    file.write("	title=\\color{red}sender\\color{black}/\\color{blue}receiver \\color{black} location and \\color{cyan}area covered\\color{black}]\n")

    for x in range(0,instance.X):
        for y in range(0,instance.Y):
            if map[x,y] < 0.0:
                val = int(30 + 70 * map[x,y] / min_depth)
                file.write("    \\addplot[only marks,mark=square*,blue!"+str(val)+",opacitar_y=.7,mark size=0.42cm] coordinates{("+str(x)+","+str(y)+")};\n")
                file.write("    \\node at (axis cs:"+str(x)+","+str(y)+") [above,font=\\scriptsize] {"+str(int(map[x,y]))+"};\n")
            else:
                val = int(30 + 70 * map[x,y] / max_depth)
                file.write("    \\addplot[only marks,mark=square*,green!"+str(val)+",opacitar_y=.7,mark size=0.42cm] coordinates{("+str(x)+","+str(y)+")};\n")
                file.write("    \\node at (axis cs:"+str(x)+","+str(y)+") [above,font=\\scriptsize] {"+str(int(map[x,j]))+"};\n")

    if instance.GOAL == 1: # goal: maximize coverage
        for tar_x, tar_y, tar_z in ocean:
            if solution.get_values(c[tar_x, tar_y, tar_z]) > 0.999:
                val = str(cov_val[tar_x, tar_y, tar_z])
            else:
                val = "X"

            file.write("    \\node at (axis cs:"+str(tar_x)+","+str(tar_y)+") [below,font=\\scriptsize] {"+val+"};\n")

    else: # goal: minimize cost for deployed equipment
        for tar_x, tar_y, tar_z in ocean:
            val = str(cov_val[tar_x, tar_y, tar_z])


            file.write("    \\node at (axis cs:"+str(tar_x)+","+str(tar_y)+") [below,font=\\scriptsize] {"+val+"};\n")

    file.write("    \\addplot[only marks,mark=*,red,mark size=0.20cm] table\n")
    file.write("         [\n")
    file.write("           x expr=\\thisrow{sx},\n")
    file.write("           y expr=\\thisrow{sy}\n")
    file.write("         ] {solution-s.csv};\n")
    file.write("    \\addplot[only marks,mark=triangle*,blue,mark size=0.20cm] table\n")
    file.write("         [\n")
    file.write("           x expr=\\thisrow{rx},\n")
    file.write("           y expr=\\thisrow{ry}\n")
    file.write("         ] {solution-r.csv};\n")

    file.write("	\\end{axis}\n")
    file.write("\\end{tikzpicture}\n")
    file.write("\\end{document}\n")

    file.close()

    # ---------------------------------------------------
    # --- farewell
    # ---------------------------------------------------

    print(f"The total time spent is {(time.time()-start_time):.0f} seconds")

    print(f"Output written to '{outdir}'")

    print(f"This is the end, my only friend, the end...")

