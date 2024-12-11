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