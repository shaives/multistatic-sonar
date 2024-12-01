#! /usr/bin/python3

# running python3.10 and cplex 22.1.1
import sys
import time
import os
import shutil
import importlib

from math import *
from datetime import datetime

from src.outputs import *
from src.functions import *
from src.classes import *
from src.optimization import *

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

    print(f"BISON - BIstatic Sonar OptimizatioN")
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
    # --- compute coverage
    # ---------------------------------------------------

    print(f"Computing coverage")

    detection_prob = compute_coverage_triples(instance, ocean, ocean_surface)

    if len(instance.TS) == 0:
        instance.STEPS = 180

    # ---------------------------------------------------
    # --- computing the rowsum in detection_prob
    # ---------------------------------------------------

    print(f"Computing detection prob")

    detection_prob_rowsum_r, detection_prob_rowsum_s = compute_rowsum_detection_prob(instance, ocean, ocean_surface, detection_prob)

    # ---------------------------------------------------
    # --- set up & compute optimization model
    # ---------------------------------------------------

    print(f"Create optimization model")
    model = create_optimization_model(instance, ocean_surface, ocean, detection_prob_rowsum_s, detection_prob)
    
    print(f"Solve optimization model")
    results = solve_model(model, instance, ocean_surface, outdir, 'gurobi')  # or 'cplex', 'gurobi', etc.

    # ---------------------------------------------------
    # --- output optimization model results
    # ---------------------------------------------------

    output_solution(model, instance, ocean_surface, ocean, detection_prob, map, min_depth, max_depth, outdir, start_time)
