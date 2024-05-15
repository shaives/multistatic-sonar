from math import *

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

    for i in range(1,instance.X+1):

        for j in range(1,instance.Y+1):

            if map[i][j] < 0.0:
                val = int(30 + 70 * map[i][j] / minval)
                file.write("    \\addplot[only marks,mark=square*,blue!"+str(val)+",opacity=.7,mark size=0.42cm] coordinates{("+str(i)+","+str(j)+")};\n")
                file.write("    \\node at (axis cs:"+str(i)+","+str(j)+") [above,font=\\scriptsize] {"+str(int(map[i][j]))+"};\n")

            else:
                val = int(30 + 70 * map[i][j] / maxval)
                file.write("    \\addplot[only marks,mark=square*,green!"+str(val)+",opacity=.7,mark size=0.42cm] coordinates{("+str(i)+","+str(j)+")};\n")
                file.write("    \\node at (axis cs:"+str(i)+","+str(j)+") [above,font=\\scriptsize] {"+str(int(map[i][j]))+"};\n")

    file.write("	\\end{axis}\n")
    file.write("\\end{tikzpicture}\n")
    file.write("\\end{document}\n")

    file.close()

def write_latex_solution(outdir, instance, ocean, map, minval, maxval, cov_val, c, solution):

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

    for i in range(1,instance.X+1):
        for j in range(1,instance.Y+1):
            if map[i][j] < 0.0:
                val = int(30 + 70 * map[i][j] / minval)
                file.write("    \\addplot[only marks,mark=square*,blue!"+str(val)+",opacity=.7,mark size=0.42cm] coordinates{("+str(i)+","+str(j)+")};\n")
                file.write("    \\node at (axis cs:"+str(i)+","+str(j)+") [above,font=\\scriptsize] {"+str(int(map[i][j]))+"};\n")
            else:
                val = int(30 + 70 * map[i][j] / maxval)
                file.write("    \\addplot[only marks,mark=square*,green!"+str(val)+",opacity=.7,mark size=0.42cm] coordinates{("+str(i)+","+str(j)+")};\n")
                file.write("    \\node at (axis cs:"+str(i)+","+str(j)+") [above,font=\\scriptsize] {"+str(int(map[i][j]))+"};\n")

    if instance.GOAL == 1: # goal: maximize coverage
        for tx,ty in ocean:
            if instance.CC == 1: # cookie-cutter model
                if solution.get_values(c[tx,ty]) > 0.999:
                    val = str(cov_val[tx,ty])
                else:
                    val = "X"
            else: # probabilistic model
                if solution.get_values(c[tx,ty]) > 0.999:
                    val = str(int(100*(1-exp(cov_val[tx,ty]))))
                else:
                    val = "X("+str(int(100*(1-exp(cov_val[tx,ty]))))+")"

            file.write("    \\node at (axis cs:"+str(tx)+","+str(ty)+") [below,font=\\scriptsize] {"+val+"};\n")

    else: # goal: minimize cost for deployed equipment
        for tx,ty in ocean:
            if instance.CC == 1: # cookie-cutter model
                val = str(cov_val[tx,ty])
            else: # probabilistic model
                val = str(int(100*(1-exp(cov_val[tx,ty]))))

            file.write("    \\node at (axis cs:"+str(tx)+","+str(ty)+") [below,font=\\scriptsize] {"+val+"};\n")

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