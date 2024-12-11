import matplotlib.pyplot as plt
import numpy as np

from math import *
from pyomo.environ import value

from src.functions import *

def create_latex_map(instance, map, minval, maxval, outdir):

    paperwidth = instance.X + 5
    paperheight = instance.Y + 5

    file = open(outdir + "/oceanmap.tex","w+")

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
                val = int(30 + 70 * map[x,y] / minval)
                file.write("    \\addplot[only marks,mark=square*,blue!"+str(val)+",opacity=.7,mark size=0.42cm] coordinates{("+str(x)+","+str(y)+")};\n")
                file.write("    \\node at (axis cs:"+str(x)+","+str(y)+") [above,font=\\scriptsize] {"+str(int(map[x,y]))+"};\n")

            else:
                val = int(30 + 70 * map[x,y] / maxval)
                file.write("    \\addplot[only marks,mark=square*,green!"+str(val)+",opacity=.7,mark size=0.42cm] coordinates{("+str(x)+","+str(y)+")};\n")
                file.write("    \\node at (axis cs:"+str(x)+","+str(y)+") [above,font=\\scriptsize] {"+str(int(map[x,y]))+"};\n")

    file.write("	\\end{axis}\n")
    file.write("\\end{tikzpicture}\n")
    file.write("\\end{document}\n")

    file.close()

def create_ocean_dat(ocean, outdir):   

	file = open(outdir + "/ocean.dat", "w+")

	for x,y,z in ocean:

		file.write(str(x) + " " + str(y) + " " + str(z) + "\n")

	file.close()

	print(f"number of ocean pixels: {len(ocean)}")
     
def create_map_dat(instance, map, outdir):

    file = open(outdir + "/map.dat", "w+")

    for x in range(0,instance.X):

        for y in range(0,instance.Y):

            file.write(str(x) + " " + str(y) + " " + str(map[x,y]) + "\n")

    file.close()

def create_plot_func_g(instance, outdir):

    if len(instance.TS) > 0:

        # Data for plotting
        t = np.arange(0.0, 2.0*pi, 0.01)
        tt = t/180.0*pi
        s = g_cos(t, instance)

        fig, ax = plt.subplots()
        ax.plot(t, s)

        ax.set(xlabel='angle (deg)', ylabel='TS (pixels)',
                    title='Target Strength as a Function of Degree')
        ax.grid()

        fig.savefig(outdir+"/g_cos_theta.png")
        #plt.show()

        fig, ax = plt.subplots(subplot_kw=dict(polar=True))

        # is this even working?
        #plt.subplot(111,projection='polar')
        ax.plot(tt, s)
        ax.grid()
        ax.set(xlabel='angle (deg)', ylabel='TS (pixels)',
                    title='Target Strength as a Function of Degree')
        ax.grid()

        fig.savefig(outdir+"/g_cos_theta_polar.png")
        #plt.show()

def output_solution(model, instance, ocean_surface, ocean, detection_prob, map, min_depth, max_depth, outdir, start_time):
    """
    Output the solution in various formats
    Parameters:
        model: Pyomo model
        instance: Problem instance
        ocean_surface: Dictionary of surface coordinates
        ocean: Dictionary of ocean points
        detection_prob: Dictionary of detection probabilities
        map: Dictionary or 2D array with depth values
        min_depth: Minimum depth value
        max_depth: Maximum depth value
        outdir: Output directory
        start_time: Start time for timing calculation
    """
    # ---------------------------------------------------
    # --- output solution on screen
    # ---------------------------------------------------
    print("Source locations:")
    for tx_x, tx_y, tx_z in ocean_surface:
        if value(model.s[tx_x, tx_y, tx_z]) > 0.999:
            print(f"  ({tx_x}, {tx_y})")

    print("Receiver locations:")
    for rx_x, rx_y, rx_z in ocean_surface:
        if value(model.r[rx_x, rx_y, rx_z]) > 0.999:
            print(f"  ({rx_x}, {rx_y})")

    if instance.GOAL == 1 and hasattr(model, 'c'):
        print("Covered ocean pixels:")
        for tar_x, tar_y, tar_z in ocean:
            if value(model.c[tar_x, tar_y, tar_z]) > 0.999:
                print(f"  ({tar_x}, {tar_y}, {tar_z})")

        print("Not covered ocean pixels:")
        for tar_x, tar_y, tar_z in ocean:
            if value(model.c[tar_x, tar_y, tar_z]) < 0.001:
                print(f"  ({tar_x}, {tar_y}, {tar_z})")

    # ---------------------------------------------------
    # --- output solution to files
    # ---------------------------------------------------
    with open(outdir + "/solution-r.csv", "w+") as file:
        file.write("rx ry\n")
        for rx_x, rx_y, rx_z in ocean_surface:
            if value(model.r[rx_x, rx_y, rx_z]) > 0.999:
                file.write(f"{rx_x} {rx_y}\n")

    with open(outdir + "/solution-s.csv", "w+") as file:
        file.write("sx sy\n")
        for tx_x, tx_y, tx_z in ocean_surface:
            if value(model.s[tx_x, tx_y, tx_z]) > 0.999:
                file.write(f"{tx_x} {tx_y}\n")

    # ---------------------------------------------------
    # --- compute coverage value per pixel
    # ---------------------------------------------------
    cov_val = {(tar_x, tar_y, tar_z): 0 for tar_x, tar_y, tar_z in ocean}

    for tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z, rx_x, rx_y, rx_z in detection_prob:
        if (value(model.s[tx_x, tx_y, tx_z]) > 0.999 and 
            value(model.r[rx_x, rx_y, rx_z]) > 0.999):
            cov_val[tar_x, tar_y, tar_z] += detection_prob[tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z, rx_x, rx_y, rx_z]

    # ---------------------------------------------------
    # --- output solution as latex
    # ---------------------------------------------------
    paperwidth = instance.X + 5
    paperheight = instance.Y + 5

    with open(outdir + "/solution.tex", "w+") as file:
        file.write("\\documentclass[12pt]{article}\n")
        file.write("\\usepackage{tikz}\n")
        file.write("\\usepackage{pgfplots}\n")
        file.write(f"\\usepackage[paperwidth={paperwidth}cm, paperheight={paperheight}cm, margin=1cm]{{geometry}}\n")
        file.write("\\begin{document}\n")
        file.write("\\begin{tikzpicture}\n")
        file.write("    \\begin{axis}[\n")
        file.write(f"    xtick={{1,...,{instance.X}}},\n")
        file.write(f"    ytick={{1,...,{instance.Y}}},\n")
        file.write(f"    width={instance.X+1}cm,\n")
        file.write(f"    height={instance.Y+1}cm,\n")
        file.write("    xmin=0.5,\n")
        file.write(f"    xmax={instance.X+0.5},\n")
        file.write("    ymin=0.5,\n")
        file.write(f"    ymax={instance.Y+0.5},\n")
        file.write("    xlabel={$x$},\n")
        file.write("    ylabel={$y$},\n")
        file.write("    grid=major,\n")
        file.write("    title=\\color{red}sender\\color{black}/\\color{blue}receiver \\color{black} location and \\color{cyan}area covered\\color{black}]\n")

        # Map visualization
        for x in range(0, instance.X):
            for y in range(0, instance.Y):
                if map[x,y] < 0.0:
                    val = int(30 + 70 * map[x,y] / min_depth)
                    file.write(f"    \\addplot[only marks,mark=square*,blue!{val},opacity=.7,mark size=0.42cm] coordinates{{({x},{y})}};\n")
                    file.write(f"    \\node at (axis cs:{x},{y}) [above,font=\\scriptsize] {{{int(map[x,y])}}};\n")
                else:
                    val = int(30 + 70 * map[x,y] / max_depth)
                    file.write(f"    \\addplot[only marks,mark=square*,green!{val},opacity=.7,mark size=0.42cm] coordinates{{({x},{y})}};\n")
                    file.write(f"    \\node at (axis cs:{x},{y}) [above,font=\\scriptsize] {{{int(map[x,y])}}};\n")

        # Coverage visualization
        if instance.GOAL == 1 and hasattr(model, 'c'):
            for tar_x, tar_y, tar_z in ocean:
                if value(model.c[tar_x, tar_y, tar_z]) > 0.999:
                    val = str(cov_val[tar_x, tar_y, tar_z])
                else:
                    val = "X"
                file.write(f"    \\node at (axis cs:{tar_x},{tar_y}) [below,font=\\scriptsize] {{{val}}};\n")
        else:
            for tar_x, tar_y, tar_z in ocean:
                val = str(cov_val[tar_x, tar_y, tar_z])
                file.write(f"    \\node at (axis cs:{tar_x},{tar_y}) [below,font=\\scriptsize] {{{val}}};\n")

        # Plot sources and receivers
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

        file.write("    \\end{axis}\n")
        file.write("\\end{tikzpicture}\n")
        file.write("\\end{document}\n")

    # ---------------------------------------------------
    # --- farewell
    # ---------------------------------------------------
    print(f"The total time spent is {(time.time()-start_time):.0f} seconds")
    print(f"Output written to '{outdir}'")
    print("This is the end, my only friend, the end...")

def create_config_file(job_data: dict, job_dir: str, elevation_file: str, filename: str = 'config.py') -> None:
    """
    Create optimization configuration file from job data.
    
    Args:
        job_data: Dictionary containing job configuration
        job_dir: Directory name for the job
        elevation_file: Name of the elevation data file
        metadata: Dictionary containing grid metadata (nrows, ncols)
        filename: Output configuration filename
    """
    # Extract grid dimensions from metadata
    x_points = metadata['ncols']
    y_points = metadata['nrows']
    
    # Extract values from job data
    is_cost_opt = job_data["optimization_type"] == "Cost"
    
    # Get source/receiver numbers or costs based on optimization type
    if is_cost_opt:
        s_value = job_data["tx_price"]
        r_value = job_data["rx_price"]
        goal = 0
    else:
        s_value = job_data["tx_buoys"]
        r_value = job_data["rx_buoys"]
        goal = 1
    
    # Get heuristic value
    heuristic_mode = job_data.get("heuristic", "Medium (1000 rounds)")
    if heuristic_mode == "None":
        heuristic_value = 0
    elif heuristic_mode == "Fast (100 rounds)":
        heuristic_value = 100
    elif heuristic_mode == "Medium (250 rounds)":
        heuristic_value = 2500
    elif heuristic_mode == "Thorough (1000 rounds)":
        heuristic_value = 1000
    else:  # Custom
        heuristic_value = job_data.get("heuristic_rounds", 1000)
    
    # Get time limit
    time_limit = job_data.get("time_limit", 36000)
    
    # Create configuration content
    config = f'''DIR = "{job_dir}"           # directory where to find input and store output files

INPUT = "{elevation_file}"   # file name of ocean floor data

RAM = 4*8192    # 0=use disk, 1=use RAM for storing data

X = {x_points}      # number of pixels in x-direction
Y = {y_points}      # number of pixels in y-direction

GOAL = {goal}    # optimization goal: cover all pixels, minimize cost for deployed equipment (0), or: deploy equipment, maximize coverage (1)

S = {s_value}     # EITHER: cost for each deployed source (if GOAL=0), OR: number of deployed sources (if GOAL=1)
R = {r_value}      # EITHER: cost for each deployed receiver (if GOAL=0), OR: number of deployed receivers (if GOAL=1)

rho_0 = 2000   # range of the day (in yards)
rb = 750    # pulse length (for direct-blast-effect) (in yards)

TS = [(0.0,0.1),(30.0,0.4),(75.0,0.3),(90.0,1.0)] # target strength (in pixels), added to the range of the day
#TS = []     # if TS is an empty list, the target angle is not considered
STEPS = 30     # step size for discretization of half-circle

BOUND = 1     # for models 3-14: 0=individual bound per row, 1=min/max over all rows

USERCUTS = 0 # 0=no user cuts, 1=user cuts on

USERCUTSTRENGTH = 1.0 # how deep must user cuts be to be separated?

HEURISTIC = {heuristic_value} # 0=no heuristic, >0: with heuristic, number of rounds

SOLVE = 2 # 0=only root relaxation, 1=root+cuts, 2=to the end (optimality or timelimit reached)

TIMELIMIT = {time_limit} # time limit in seconds
'''
    
    # Write to file
    with open(filename, 'w') as f:
        f.write(config)