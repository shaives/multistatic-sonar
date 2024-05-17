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
