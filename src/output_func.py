import matplotlib.pyplot as plt
import numpy as np

from math import *

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

def create_config_file(job_data: dict, job_dir: str, elevation_file: str, metadata: dict, filename: str = 'config.py') -> None:
    """
    Create optimization configuration file from job data.
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
    
    # Get heuristic rounds
    heuristic_mode = job_data.get("heuristic", "Medium (1000 rounds)")
    if heuristic_mode == "None":
        heuristic_value = 0
    elif heuristic_mode == "Fast (100 rounds)":
        heuristic_value = 100
    elif heuristic_mode == "Medium (1000 rounds)":
        heuristic_value = 1000
    elif heuristic_mode == "Thorough (5000 rounds)":
        heuristic_value = 5000
    else:  # Custom
        heuristic_value = job_data.get("heuristic_rounds", 1000)
    
    # Get time limit
    time_limit = job_data.get("time_limit", 36000)
    
    # Format the DIR path
    dir_path = f"outputs/{job_dir}/"
    
    # Create configuration content
    config = f'''DIR = "{dir_path}"           # directory where to find input and store output files

INPUT = "{elevation_file}"   # file name of ocean floor data

RAM = 4*8192    # 0=use disk, 1=use RAM for storing data

X = {x_points}      # number of pixels in x-direction
Y = {y_points}      # number of pixels in y-direction

GOAL = {goal}    # optimization goal: cover all pixels, minimize cost for deployed equipment (0), or: deploy equipment, maximize coverage (1)

S = {s_value}     # EITHER: cost for each deployed source (if GOAL=0), OR: number of deployed sources (if GOAL=1)
R = {r_value}      # EITHER: cost for each deployed receiver (if GOAL=0), OR: number of deployed receivers (if GOAL=1)

rho_0 = 2   # range of the day (in pixels)
rb = 1    # pulse length (for direct-blast-effect) (in pixels)

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