#! /usr/bin/python3

# running python3.10 and cplex 22.1.1
import sys
import re
import time
import os
import shutil
import random
import importlib

from math import *
from datetime import datetime

import matplotlib
import matplotlib.pyplot as pltf
import numpy as np

import cplex
from cplex.exceptions import CplexSolverError

from src.output_func import *
from src.classes import *

# Euclidean distance between two points
def d(x0,y0,x1,y1):
	return sqrt((x0-x1)**2 + (y0-y1)**2)

# target strength piecewise linear function g(cos(theta))
def g_cos(theta):
	theta = np.asarray(theta)
	scalar_input = False
	if theta.ndim == 0:
		theta = theta[None]
		scalar_input = True

	ret = []

	for x in theta:
		for i in range(len(instance.TS)-1):
			w_i = cos(instance.TS[i][0]/180.0*pi)
			w_ip1 = cos(instance.TS[i+1][0]/180.0*pi)
			s_i = instance.TS[i][1]
			s_ip1 = instance.TS[i+1][1]
			alpha = cos(x)

			if w_i >= alpha and alpha >= w_ip1:
				ret.append( s_i + ( (s_ip1 - s_i) * (alpha - w_i) ) / ( w_ip1 - w_i ) )
				break
			elif -w_i <= alpha and alpha <= -w_ip1:
				ret.append( s_i + ( (s_ip1 - s_i) * (alpha + w_i) ) / ( w_i - w_ip1 ) )
				break

	if scalar_input:
		return np.squeeze(ret)
	return ret

def g(alpha):
	for i in range(len(instance.TS)-1):
		w_i = cos(instance.TS[i][0]/180.0*pi)
		w_ip1 = cos(instance.TS[i+1][0]/180.0*pi)
		s_i = instance.TS[i][1]
		s_ip1 = instance.TS[i+1][1]

		if w_i >= alpha and alpha >= w_ip1:
			return ( s_i + ( (s_ip1 - s_i) * (alpha - w_i) ) / ( w_ip1 - w_i ) )
		elif -w_i <= alpha and alpha <= -w_ip1:
			return ( s_i + ( (s_ip1 - s_i) * (alpha + w_i) ) / ( w_i - w_ip1 ) )

	return 0

# the check_line routine checks if there are obstacles
# along a line (from source to target, or target to receiver)
# it is an implementation of Bresenham's line algorithm,
# see https://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm
# returns 'None', if no obstacle was found
# and '1' otherwise

def check_line(x0,y0,x1,y1):
	dx = abs(x1-x0)
	if x0<x1:
		sx = 1
	else:
		sx = -1
	dy = -abs(y1-y0)
	if y0<y1:
		sy = 1
	else:
		sy = -1
	err = dx+dy

	while (1):
		if map[x0][y0] >= 0.0:
			return 1
		if x0==x1 and y0==y1:
			return None
		e2 = 2*err
		if e2 > dy:
			err = err + dy
			x0 = x0 + sx
		if e2 < dx:
			err = err + dx
			y0 = y0 + sy

# ---------------------------------------------------
# --- let's start
# ---------------------------------------------------

if __name__ == '__main__':

	import_name = "cfg." + sys.argv[1]

	instance = importlib.import_module(import_name)

	timestamp = str(datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
	outdir = instance.DIR + timestamp + '_' + instance.OUTPUT

	os.mkdir(outdir)
	shutil.copy2("./cfg/" + instance.OUTPUT + ".py", outdir)

	sys.stdout = Logger(outdir) # redirect output to screen and logfile


	print ("BISON - "+color.BOLD+"BI"+color.END+"static "+color.BOLD+"S"+color.END+"onar "+color.BOLD+"O"+color.END+"ptimizatio"+color.BOLD+"N"+color.END)
	print ("")
	print ("                                                                                           ")
	print ("                                   @@@@@@@@@                                               ")
	print ("                               @@@@         @@@@                                           ")
	print ("                            @@@                 @@@                                        ")
	print ("                         @@@                       @@@@                                    ")
	print ("                       @@                             @@@@@                                ")
	print ("                     @@@                                   @@@@                            ")
	print ("                   @@@                                         @@@@                        ")
	print ("         @@@@@@@@@@                                                @@@@                    ")
	print ("     @@@@                                   @                          @@@@@               ")
	print ("   @@                                       @@                              @@@@@@         ")
	print ("  @@           @                              @@                              @@@@@        ")
	print (" @@            @@                              @                                 @@@@      ")
	print (" @            @ @                               @                                  @@@     ")
	print (" @            @ @                               @                                    @@    ")
	print (" @          @@@ @@                             @@                                   @  @   ")
	print ("@@            @@@                             @                                     @@  @  ")
	print (" @@                                           @@               @@                   @@@ @@ ")
	print ("  @                                         @@                   @                  @ @@@@ ")
	print ("   @@         @                             @                     @@                @ @ @@ ")
	print ("     @@    @@@                               @                     @@              @@ @ @  ")
	print ("      @@                                     @@                 @@@  @             @ @@@@  ")
	print ("        @                                    @@               @@     @@@          @@ @  @@ ")
	print ("        @                                     @@     @@@@@@@@@     @@   @@@@        @@   @@")
	print ("         @                 @                  @@@@@@@       @     @         @@@       @   @")
	print ("          @@@@@@@@@        @@                @@             @     @            @      @@ @ ")
	print ("                   @@@   @@  @              @               @    @              @@    @@   ")
	print ("                      @  @    @            @               @    @                @@   @@   ")
	print ("                       @@      @@          @             @@    @                 @@   @@   ")
	print ("                       @@       @@    @@@@@            @@@   @@                  @@   @@   ")
	print ("                               @@@  @@@              @@    @@                    @@   @@   ")
	print ("                             @@    @@              @@@@@@@@                     @    @@@   ")
	print ("                             @@@@@@@@                                          @@@@@@@     ")
	print ("")
	print ("")

	print ("called at "+timestamp)
	
	# ---------------------------------------------------
	# --- read ocean elevation data file
	# ---------------------------------------------------

	print ("reading '"+instance.DIR+"/"+instance.INPUT+"'")

	file = open(instance.DIR+"/"+instance.INPUT, "r")
	elevation_data = file.read()
	file.close()

	ncols_string = re.search("ncols (.*)",elevation_data).group(1)
	ncols = float(ncols_string)
	print ("number of columns:",ncols)

	nrows_string = re.search("nrows (.*)",elevation_data).group(1)
	nrows = float(nrows_string)
	print ("number of rows:",nrows)

	if (nrows == 0 or ncols == 0):
		print ("something wrong here")
		quit()

	entries = re.split("\n+", elevation_data)

	numberstart_line = re.compile("\d+");

	i = 0
	data = {}

	for line in entries:
		if re.match("-?\d+", line):
			data[i] = re.split("\s+", line)
			i = i + 1


	# ---------------------------------------------------
	# --- aggregate data
	# ---------------------------------------------------

	deltaX = int(ncols / instance.X)
	deltaY = int(nrows / instance.Y)
	minval = 1000000
	maxval = -1000000

	map = {}
	ocean = {}

	for i in range(1,instance.X+1):
		map[i] = {}

		for j in range(1,instance.Y+1):
			av = 0.0
			for ii in range(1,deltaX+1):
				for jj in range(1,deltaY+1):
					av = av + float(data[(instance.Y-j) * deltaY + (jj-1)][(i-1) * deltaX + (ii-1)])

			map[i][j] = av / (deltaX * deltaY)

			if map[i][j] < 0.0:
				ocean[i,j] = 1

			if map[i][j] < minval:
				minval = map[i][j]

			if map[i][j] > maxval:
				maxval = map[i][j]


	# ---------------------------------------------------
	# --- create latex output of map
	# ---------------------------------------------------

	create_latex_map(instance, map, minval, maxval, outdir)

	# ---------------------------------------------------
	# --- output ocean pixels
	# ---------------------------------------------------

	file = open(outdir + "/ocean.dat","w+")

	for i,j in ocean:
		file.write(str(i) + " " + str(j)+"\n")

	file.close()

	print ("number of ocean pixels:",len(ocean))

	# ---------------------------------------------------
	# --- output map
	# ---------------------------------------------------

	file = open(outdir + "/map.dat","w+")

	for i in range(1,instance.X+1):
		for j in range(1,instance.Y+1):
			file.write(str(i)+" "+str(j)+" "+str(map[i][j])+"\n")

	file.close()

	# ---------------------------------------------------
	# --- plot function g
	# ---------------------------------------------------

	if len(instance.TS) > 0:

		# Data for plotting
		t = np.arange(0.0, 2.0*pi, 0.01)
		tt = t/180.0*pi
		s = g_cos(t)

		fig, ax = plt.subplots()
		ax.plot(t, s)

		ax.set(xlabel='angle (deg)', ylabel='TS (pixels)',
					title='Target Strength as a Function of Degree')
		ax.grid()

		fig.savefig(outdir+"/g_cos_theta.png")
		#plt.show()

		fig, ax = plt.subplots(subplot_kw=dict(polar=True))

		#plt.subplot(111,projection='polar')
		ax.plot(tt, s)
		ax.grid()
		ax.set(xlabel='angle (deg)', ylabel='TS (pixels)',
					title='Target Strength as a Function of Degree')
		ax.grid()

		fig.savefig(outdir+"/g_cos_theta_polar.png")
		#plt.show()

	# ---------------------------------------------------
	# --- coverage
	# ---------------------------------------------------

	detection_prob = {}

	start = time.time()

	if len(instance.TS) == 0: # without TS
		for tx,ty in ocean: # target
			for gx,gy in ocean: # source
				for g1x,g1y in ocean: # receiver
					#if check_line(gx,gy,g1x,g1y) == None: # no obstacles between source-reiver

						if instance.CC == 0: # probabilistic model
							if (((d(gx,gy,tx,ty) * d(g1x,g1y,tx,ty)) / (instance.rho_0**2) - 1)/instance.b1) < e+10: # avoid numerical trouble from powers of large numbers
								aux = instance.pmax * (1 / (1 + 10**(((d(gx,gy,tx,ty) * d(g1x,g1y,tx,ty)) / (instance.rho_0**2) - 1)/instance.b1))) * (1 / (1 + 10**((1 - (d(gx,gy,tx,ty) + d(g1x,g1y,tx,ty)) / (d(gx,gy,g1x,g1y) + 2*instance.rb))/instance.b2)))
								if aux > instance.pmin:
									if check_line(gx,gy,tx,ty) == None and check_line(tx,ty,g1x,g1y) == None: # no obstacles between source-target and target-receiver, and source-reiver
										detection_prob[tx,ty,0,gx,gy,g1x,g1y] = log(1 - aux) # detection probability

						else: # cookie-cutter model
							if d(gx,gy,tx,ty) * d(g1x,g1y,tx,ty) <= instance.rho_0**2 and d(gx,gy,tx,ty) + d(g1x,g1y,tx,ty) >= d(gx,gy,g1x,g1y) + 2*instance.rb: # check for inside range-of-day Cassini oval and outside direct-blast-effect
								if check_line(gx,gy,tx,ty) == None and check_line(tx,ty,g1x,g1y) == None: # no obstacles between source-target, target-receiver, and source-reiver
									detection_prob[tx,ty,0,gx,gy,g1x,g1y] = 1 # sure detection

	else: # with TS

		for tx,ty in ocean: # target
			for theta in range(0,180,instance.STEPS): # target angle
				my_theta = theta/180.0*pi
				my_sin_theta = sin(my_theta)
				my_cos_theta = cos(my_theta)

				for gx,gy in ocean: # source
					if (gx,gy) != (tx,ty): # exclude equality of source and target (direct blast effect)
						my_sqrt1 = 0.5 / ( sqrt((gx-tx)**2 + (gy-ty)**2) )
						for g1x,g1y in ocean: # receiver
							# (note that there may be obstacles between source-reiver!)
							if (g1x,g1y) != (tx,ty): # exclude equality of receiver and target (direct blast effect)
								my_sqrt2 = 0.5 / ( sqrt((g1x-tx)**2 + (g1y-ty)**2) )

								if instance.CC == 0: # probabilistic model
									alpha = ( ((gx-tx)*my_cos_theta + (gy-ty)*my_sin_theta ) * my_sqrt1 + ((g1x-tx)*my_cos_theta + (g1y-ty)*my_sin_theta ) * my_sqrt2 )

									if (((d(gx,gy,tx,ty) * d(g1x,g1y,tx,ty)) / ((instance.rho_0 + g(alpha))**2) - 1)/instance.b1) < e+10: # avoid numerical trouble from powers of large numbers
										aux = instance.pmax * (1 / (1 + 10**(((d(gx,gy,tx,ty) * d(g1x,g1y,tx,ty)) / ((instance.rho_0 + g(alpha))**2) - 1)/instance.b1))) * (1 / (1 + 10**((1 - (d(gx,gy,tx,ty) + d(g1x,g1y,tx,ty)) / (d(gx,gy,g1x,g1y) + 2*instance.rb))/instance.b2)))
										if aux > instance.pmin:
											if check_line(gx,gy,tx,ty) == None and check_line(tx,ty,g1x,g1y) == None: # no obstacles between source-target and target-receiver, and source-reiver
												detection_prob[tx,ty,theta,gx,gy,g1x,g1y] = log(1 - aux) # detection probability

								else: # cookie-cutter model
									if d(gx,gy,tx,ty) + d(g1x,g1y,tx,ty) >= d(gx,gy,g1x,g1y) + 2*instance.rb: # check for outside direct-blast-effect
										alpha = ( ((gx-tx)*my_cos_theta + (gy-ty)*my_sin_theta ) * my_sqrt1 + ((g1x-tx)*my_cos_theta + (g1y-ty)*my_sin_theta ) * my_sqrt2 )

										#print ("target:",tx,ty,"angle:",theta,"source:",gx,gy,"receiver:",g1x,g1y,"E-angle:",alpha*180/pi,"TS:",g_cos(alpha))

										if d(gx,gy,tx,ty) * d(g1x,g1y,tx,ty) <= (instance.rho_0 + g(alpha))**2: # check for inside range-of-day Cassini oval
											if check_line(gx,gy,tx,ty) == None and check_line(tx,ty,g1x,g1y) == None: # no obstacles between source-target, target-receiver
												detection_prob[tx,ty,theta,gx,gy,g1x,g1y] = 1 # sure detection
												#print ("target:",tx,ty,"angle:",theta,"source:",gx,gy,"receiver:",g1x,g1y,"E-angle:",alpha*180/pi,"TS:",g_cos(alpha))

	end = time.time()

	print ("it took","{0:.2f}".format(end - start),"sec to get",len(detection_prob),"detection triples")

	if len(instance.TS) == 0:
		instance.STEPS = 180

	# ---------------------------------------------------
	# --- computing the rowsum in detection_prob
	# ---------------------------------------------------

	detection_prob_rowsum_r = {}

	max = -10e+10
	min = 10e+10

	for tx,ty in ocean:
		for theta in range(0,180,instance.STEPS): # target angle
			for g1x,g1y in ocean:
				sum = 0
				for gx,gy in ocean:
					if (tx,ty,theta,gx,gy,g1x,g1y) in detection_prob:
						sum = sum + detection_prob[tx,ty,theta,gx,gy,g1x,g1y]
				detection_prob_rowsum_r[tx,ty,theta,g1x,g1y] = sum

				if sum > max:
					max = sum
				if sum < min:
					min = sum

	if instance.BOUND == 1:
		if instance.CC == 0: # probabilistic model
			for tx,ty in ocean:
				for theta in range(0,180,instance.STEPS): # target angle
					for g1x,g1y in ocean:
						detection_prob_rowsum_r[tx,ty,theta,g1x,g1y] = min

		else: # cookie-cutter model
			for tx,ty in ocean:
				for theta in range(0,180,instance.STEPS): # target angle
					for g1x,g1y in ocean:
						detection_prob_rowsum_r[tx,ty,theta,g1x,g1y] = max


	detection_prob_rowsum_s = {}

	for tx,ty in ocean:
		for theta in range(0,180,instance.STEPS): # target angle
			for gx,gy in ocean:
				sum = 0
				for g1x,g1y in ocean:
					if (tx,ty,theta,gx,gy,g1x,g1y) in detection_prob:
						sum = sum + detection_prob[tx,ty,theta,gx,gy,g1x,g1y]
				detection_prob_rowsum_s[tx,ty,theta,gx,gy] = sum

				if sum > max:
					max = sum
				if sum < min:
					min = sum

	if instance.BOUND == 1:
		if instance.CC == 0: # probabilistic model
			for tx,ty in ocean:
				for theta in range(0,180,instance.STEPS): # target angle
					for gx,gy in ocean:
						detection_prob_rowsum_s[tx,ty,theta,gx,gy] = min

		else: # cookie-cutter model
			for tx,ty in ocean:
				for theta in range(0,180,instance.STEPS): # target angle
					for gx,gy in ocean:
						detection_prob_rowsum_s[tx,ty,theta,gx,gy] = max

	# ---------------------------------------------------
	# --- output to file
	# ---------------------------------------------------

	#file = open(outdir+"/detection_prob.dat","w+")

	#for tx,ty,theta,gx,gy,g1x,g1y in detection_prob:
	#  file.write(str(tx)+" "+str(ty)+" "+str(theta)+" "+str(gx)+" "+str(gy)+" "+str(g1x)+" "+str(g1y)+" "+str(detection_prob[tx,ty,gx,gy,g1x,g1y])+"\n")

	#file.close()

	# ---------------------------------------------------
	# --- set up optimization model
	# ---------------------------------------------------

	model = cplex.Cplex()

	print ("IBM ILOG CPLEX version number: ", model.get_version())

	# VARIABLES

	s = {} # sources, =1, if a source is located on candidate location gx,gy
	r = {} # receivers, =1, if a receiver is located on candidate location gx,gy

	for gx,gy in ocean:
		s[gx,gy] = "s#"+str(gx)+"#"+str(gy)
		r[gx,gy] = "r#"+str(gx)+"#"+str(gy)

		if instance.GOAL == 0: # optimization goal: cover all pixels, minimize deployment cost
			model.variables.add(obj = [instance.S], names = [s[gx,gy]], lb = [0], ub = [1], types = ["B"])
			model.variables.add(obj = [instance.R], names = [r[gx,gy]], lb = [0], ub = [1], types = ["B"])
		else: # deploy equipment, maximize coverage
			model.variables.add(names = [s[gx,gy]], lb = [0], ub = [1], types = ["B"])
			model.variables.add(names = [r[gx,gy]], lb = [0], ub = [1], types = ["B"])

	if instance.GOAL == 1: # deploy equipment, maximize coverage
		c = {} # coverage, =1, if some source-receiver pair covers location tx,ty

		percentage = float("{0:.3f}".format(100.0/len(ocean)))

		for tx,ty in ocean:
			c[tx,ty] = "c#"+str(tx)+"#"+str(ty)
			model.variables.add(obj = [percentage], names = [c[tx,ty]], lb = [0], ub = [1], types = ["B"])

	if instance.MODELTYPE in {4,5,7,8,10,11,13,14}:
		y = {}

		for tx,ty,theta,gx,gy in detection_prob_rowsum_s:
			y[tx,ty,theta,gx,gy] = "y#"+str(tx)+"#"+str(ty)+"#"+str(theta)+"#"+str(gx)+"#"+str(gy)

			if instance.CC == 0: # probabilistic model
				model.variables.add(names = [y[tx,ty,theta,gx,gy]], lb = [detection_prob_rowsum_s[tx,ty,theta,gx,gy]], ub = [0], types = ["C"])
			else: # cookie-cutter model
				model.variables.add(names = [y[tx,ty,theta,gx,gy]], ub = [detection_prob_rowsum_s[tx,ty,theta,gx,gy]], lb = [0], types = ["C"])

				# TODO: Setting y to general integer seems to help for cookie-cutter. Perform a deeper analysis of this initial observation
				#model.variables.add(names = [y[tx,ty,theta,gx,gy]], ub = [detection_prob_rowsum_s[tx,ty,theta,gx,gy]], lb = [0], types = ["I"])

	# CONSTRAINTS

	# probabilistic models

	if instance.GOAL == 1:
		# for all models below, if the goal is to 'deploy equipment, maximize coverage', then here the equipment gets fixed

		thevars = []
		thecoefs = []

		for gx,gy in ocean:
			thevars.append(s[gx,gy])
			thecoefs.append(1.0)

		model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [instance.S])

		thevars = []
		thecoefs = []

		for g1x,g1y in ocean:
			thevars.append(r[g1x,g1y])
			thecoefs.append(1.0)

		model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [instance.R])

	else: # GOAL = 0
		# for all models below, if the goal is to 'minimize equipment', then at least one source and one receiver have to be deployed

		thevars = []
		thecoefs = []

		for gx,gy in ocean:
			thevars.append(s[gx,gy])
			thecoefs.append(1.0)

		model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [1.0])

		thevars = []
		thecoefs = []

		for g1x,g1y in ocean:
			thevars.append(r[g1x,g1y])
			thecoefs.append(1.0)

		model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [1.0])

	if instance.MODELTYPE == 7:
		# 1st linearization from Oral, Kettani (1992) for senders

		# coverage for each ocean pixel

		for tx,ty in ocean:
			for theta in range(0,180,instance.STEPS): # target angle
				thevars = []
				thecoefs = []

				for gx,gy in ocean:
					thevars.append(s[gx,gy])
					thevars.append(y[tx,ty,theta,gx,gy])
					thecoefs.append(detection_prob_rowsum_s[tx,ty,theta,gx,gy])
					thecoefs.append(-1.0)

				if instance.GOAL == 1: # goal: deploy equipment, maximize coverage
					thevars.append(c[tx,ty])
					if instance.CC == 0: # probabilistic model
						thecoefs.append(-log(1-instance.dp))
					else: # cookie-cutter model
						thecoefs.append(-1.0)

				if instance.CC == 0: # probabilistic model
					if instance.GOAL == 0: # goal: cover all pixels
						model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [log(1-instance.dp)])
					else: # goal: deploy equipment
						model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
				else: # cookie-cutter model
					if instance.GOAL == 0: # goal: cover all pixels
						model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [1.0])
					else: # goal: deploy equipment
						model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [0.0])

		# linearization constraints

		for tx,ty,theta,gx,gy in detection_prob_rowsum_s:
			thevars = [y[tx,ty,theta,gx,gy],s[gx,gy]]
			thecoefs = [1.0,-detection_prob_rowsum_s[tx,ty,theta,gx,gy]]

			for g1x,g1y in ocean:
				if (tx,ty,theta,gx,gy,g1x,g1y) in detection_prob:
					thevars.append(r[g1x,g1y])
					thecoefs.append(detection_prob[tx,ty,theta,gx,gy,g1x,g1y])

			if instance.CC == 0: # probabilistic model
				model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
			else: # cookie-cutter model
				model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [0.0])

	if instance.MODELTYPE == 10:
		# 2nd linearization from Oral, Kettani (1992) for sources

		# coverage for each ocean pixel

		for tx,ty in ocean:
			for theta in range(0,180,instance.STEPS): # target angle
				thevars = []
				thecoefs = []

				for gx,gy in ocean:
					thevars.append(y[tx,ty,theta,gx,gy])
					thecoefs.append(-1.0)

				for g1x,g1y in ocean:
					sum = 0
					for gx,gy in ocean:
						if (tx,ty,theta,gx,gy,g1x,g1y) in detection_prob:
							sum = sum + detection_prob[tx,ty,theta,gx,gy,g1x,g1y]

					thevars.append(r[g1x,g1y])
					thecoefs.append(sum)

				if instance.GOAL == 1: # goal: deploy equipment, maximize coverage
					thevars.append(c[tx,ty])
					if instance.CC == 0: # probabilistic model
						thecoefs.append(-log(1-instance.dp))
					else: # cookie-cutter model
						thecoefs.append(-1.0)

				if instance.CC == 0: # probabilistic model
					if instance.GOAL == 0: # goal: cover all pixels
						model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [log(1-instance.dp)])
					else: # goal: deploy equipment
						model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
				else: # cookie-cutter model
					if instance.GOAL == 0: # goal: cover all pixels
						model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [1.0])
					else: # goal: deploy equipment
						model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [0.0])

		# linearization constraints

		for tx,ty,theta,gx,gy in detection_prob_rowsum_s:
			thevars = [y[tx,ty,theta,gx,gy],s[gx,gy]]
			thecoefs = [-1.0,-detection_prob_rowsum_s[tx,ty,theta,gx,gy]]

			for g1x,g1y in ocean:
				if (tx,ty,theta,gx,gy,g1x,g1y) in detection_prob:
					thevars.append(r[g1x,g1y])
					thecoefs.append(detection_prob[tx,ty,theta,gx,gy,g1x,g1y])

			if instance.CC == 0: # probabilistic model
				model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [0.0])
			else: # cookie-cutter model
				model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])

	if instance.MODELTYPE == 13:
		# linearization from Chaovalitwongse, Pardalos, Prokopyev (2004) for sources

		# coverage for each ocean pixel

		for tx,ty in ocean:
			for theta in range(0,180,instance.STEPS): # target angle
				thevars = []
				thecoefs = []

				for gx,gy in ocean:
					thevars.append(y[tx,ty,theta,gx,gy])
					thecoefs.append(1.0)

				if instance.GOAL == 1: # goal: deploy equipment, maximize coverage
					thevars.append(c[tx,ty])
					if instance.CC == 0: # probabilistic model
						thecoefs.append(-log(1-instance.dp))
					else: # cookie-cutter model
						thecoefs.append(-1.0)

				if instance.CC == 0: # probabilistic model
					if instance.GOAL == 0: # goal: cover all pixels
						model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [log(1-instance.dp)])
					else: # goal: deploy equipment
						model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
				else: # cookie-cutter model
					if instance.GOAL == 0: # goal: cover all pixels
						model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [1.0])
					else: # goal: deploy equipment
						model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [0.0])

		# linearization constraints

		for tx,ty,theta,gx,gy in detection_prob_rowsum_s:
			thevars = [y[tx,ty,theta,gx,gy],s[gx,gy]]
			thecoefs = [-1.0,detection_prob_rowsum_s[tx,ty,theta,gx,gy]]

			if instance.CC == 0: # probabilistic model
				model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
			else: # cookie-cutter model
				model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [0.0])

		for tx,ty,theta,gx,gy in detection_prob_rowsum_s:
			thevars = [y[tx,ty,theta,gx,gy]]
			thecoefs = [-1.0]

			for g1x,g1y in ocean:
				if (tx,ty,theta,gx,gy,g1x,g1y) in detection_prob:
					thevars.append(r[g1x,g1y])
					thecoefs.append(detection_prob[tx,ty,theta,gx,gy,g1x,g1y])

			if instance.CC == 0: # probabilistic model
				model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
			else: # cookie-cutter model
				model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [0.0])

	if instance.USERCUTS == 1:
		usercut_cb = model.register_callback(UsercutCallback)
		usercut_cb.number_of_calls = 0
		usercut_cb.number_of_cuts_added = 0

	# OBJECTIVE FUNCTION

	if instance.GOAL == 0: # goal: minimize cost for deployed equipment
		model.objective.set_sense(model.objective.sense.minimize)
	else: # goal: maximize coverage
		model.objective.set_sense(model.objective.sense.maximize)

	# set optimization parameters

	#model.parameters.threads.set(1);   # single core, no parallelism

	# HEURISTIC

	if instance.HEURISTIC > 0:
		print ("running",instance.HEURISTIC,"rounds of heuristic")

		model.set_results_stream(None) # turn off messaging to screen
		model.set_warning_stream(None)

		if instance.GOAL == 0:
			best_obj = 10**10

			best_sources = []
			best_receivers = []

			#print ("----------",0,"-----------")

			# PREQUEL

			fixed_receivers = ocean

			old_obj = 10**10

			while True:

				# fix the receiver variables of the positions in fixed_receivers to 1, and all others to 0
				# free the sources

				for (rx,ry) in ocean:
					if (rx,ry) in fixed_receivers:
						model.variables.set_lower_bounds(r[rx,ry],1)
						model.variables.set_upper_bounds(r[rx,ry],1)
					else:
						model.variables.set_lower_bounds(r[rx,ry],0)
						model.variables.set_upper_bounds(r[rx,ry],0)

				for (sx,sy) in ocean:
					model.variables.set_lower_bounds(s[sx,sy],0)
					model.variables.set_upper_bounds(s[sx,sy],1)

				#model.write(outdir+"/bison.lp")

				# get positions of sources

				model.solve()

				obj = model.solution.get_objective_value()
				#print ("Solution value = ",obj)

				fixed_sources = {}

				for (sx,sy) in ocean:
					if model.solution.get_values(s[sx,sy]) > 0.999:
						#print ("got one source at ",sx,sy)
						fixed_sources[sx,sy] = 1

				# fix the source variables of the positions in fixed_sources to 1, and all others to 0
				# free the receiver variables again

				for (sx,sy) in ocean:
					if (sx,sy) in fixed_sources:
						model.variables.set_lower_bounds(s[sx,sy],1)
						model.variables.set_upper_bounds(s[sx,sy],1)
					else:
						model.variables.set_lower_bounds(s[sx,sy],0)
						model.variables.set_upper_bounds(s[sx,sy],0)

				for (rx,ry) in ocean:
					model.variables.set_lower_bounds(r[rx,ry],0)
					model.variables.set_upper_bounds(r[rx,ry],1)

				# get positions of sources

				model.solve()

				obj = model.solution.get_objective_value()
				#print ("Solution value = ",obj)

				fixed_receivers = {}
				for (rx,ry) in ocean:
					if model.solution.get_values(r[rx,ry]) > 0.999:
						#print ("got one receiver at ",rx,ry)
						fixed_receivers[rx,ry] = 1

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

			print ("  found new incumbent at iteration 0 with objective value",obj)

			# number of sources fixed in the model

			thevars = []
			thecoefs = []

			for gx,gy in ocean:
				thevars.append(s[gx,gy])
				thecoefs.append(1.0)

			model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [number_of_sources])

			# LOOP HEURISTIC

			list_of_fixed_sources = []

			for round in range(instance.HEURISTIC - 1):
				print ("----------",round+1,"-----------")

				# INNER LOOP

				while True:
					fixed_sources = {}

					while len(fixed_sources) < number_of_sources:
						sx,sy = random.choice(list(ocean.keys()))

						if (sx,sy) not in fixed_sources:
							fixed_sources[sx,sy] = 1

					if (fixed_sources not in list_of_fixed_sources):
						list_of_fixed_sources.append(fixed_sources)
						break

					#print ("do it again")

				# fix the source variables of the positions in fixed_sources to 1, and all others to 0
				# free the receivers

				for (sx,sy) in ocean:
					if (sx,sy) in fixed_sources:
						model.variables.set_lower_bounds(s[sx,sy],1)
						model.variables.set_upper_bounds(s[sx,sy],1)
					else:
						model.variables.set_lower_bounds(s[sx,sy],0)
						model.variables.set_upper_bounds(s[sx,sy],0)

				for (rx,ry) in ocean:
					model.variables.set_lower_bounds(r[rx,ry],0)
					model.variables.set_upper_bounds(r[rx,ry],1)

				#model.write(outdir+"/bison.lp")

				# get positions of sources

				model.solve()

				if (model.solution.get_status_string() != 'integer infeasible'):

					obj = model.solution.get_objective_value()
					#print ("Solution value = ",obj)

					fixed_receivers = {}
					for (rx,ry) in ocean:
						if model.solution.get_values(r[rx,ry]) > 0.999:
							#print ("got one receiver at ",rx,ry)
							fixed_receivers[rx,ry] = 1

					if best_obj > obj:
						best_obj = obj
						best_receivers = fixed_receivers
						best_sources = fixed_sources
						print ("  found new incumbent at iteration",round,"with objective value",obj)

		else: # GOAL = 1
			best_obj = -1

			best_sources = []
			best_receivers = []

			list_of_fixed_sources = []

			for round in range(instance.HEURISTIC):
				print ("----------",round,"-----------")

				# INNER LOOP

				while True:
					fixed_sources = {}

					while len(fixed_sources) < instance.S:
						sx,sy = random.choice(list(ocean.keys()))

						if (sx,sy) not in fixed_sources:
							fixed_sources[sx,sy] = 1

					if fixed_sources not in list_of_fixed_sources:
						list_of_fixed_sources.append(fixed_sources)
						#print ("new:",fixed_sources)
						break

					print ("(do it again)")

				print ("fixing sources at:",fixed_sources)

				old_obj = -1

				while True:

					# fix the source variables of the positions in fixed_sources to 1, and all others to 0
					# free the receivers

					for (sx,sy) in ocean:
						if (sx,sy) in fixed_sources:
							model.variables.set_lower_bounds(s[sx,sy],1)
							model.variables.set_upper_bounds(s[sx,sy],1)
						else:
							model.variables.set_lower_bounds(s[sx,sy],0)
							model.variables.set_upper_bounds(s[sx,sy],0)

					for (rx,ry) in ocean:
						model.variables.set_lower_bounds(r[rx,ry],0)
						model.variables.set_upper_bounds(r[rx,ry],1)

					#model.write(outdir+"/bison.lp")

					# get positions of receivers

					model.solve()

					print ("Solution value (ocean coverage percentage) = ", model.solution.get_objective_value())

					fixed_receivers = {}
					for (rx,ry) in ocean:
						if model.solution.get_values(r[rx,ry]) > 0.999:
							#print ("got one receiver at ",rx,ry)
							fixed_receivers[rx,ry] = 1

					# fix the receiver variables of the positions in fixed_receivers to 1, and all others to 0
					# free the source variables again

					for (rx,ry) in ocean:
						if (rx,ry) in fixed_receivers:
							model.variables.set_lower_bounds(r[rx,ry],1)
							model.variables.set_upper_bounds(r[rx,ry],1)
						else:
							model.variables.set_lower_bounds(r[rx,ry],0)
							model.variables.set_upper_bounds(r[rx,ry],0)

					for (sx,sy) in ocean:
						model.variables.set_lower_bounds(s[sx,sy],0)
						model.variables.set_upper_bounds(s[sx,sy],1)

					# get positions of sources

					model.solve()

					obj = model.solution.get_objective_value()
					print ("Solution value (ocean coverage percentage) = ", obj)

					fixed_sources = {}
					for (sx,sy) in ocean:
						if model.solution.get_values(s[sx,sy]) > 0.999:
							#print ("got one source at ",sx,sy)
							fixed_sources[sx,sy] = 1

					# LOOP
					if (old_obj < obj):
						old_obj = obj
					else:
						break


				if best_obj < obj:
					best_obj = obj
					best_receivers = fixed_receivers
					best_sources = fixed_sources
					print ("  found new incumbent at iteration",round,"with objective value",obj)

		# resort to best solution (as MIP starter)

		#print ("best objective ",best_obj)
		#print ("best receivers ",best_receivers)
		#print ("best sources ",best_sources)

		for (rx,ry) in ocean:
			if (rx,ry) in best_receivers:
				model.variables.set_lower_bounds(r[rx,ry],1)
				model.variables.set_upper_bounds(r[rx,ry],1)
			else:
				model.variables.set_lower_bounds(r[rx,ry],0)
				model.variables.set_upper_bounds(r[rx,ry],0)

		for (sx,sy) in ocean:
					if (sx,sy) in best_sources:
						model.variables.set_lower_bounds(s[sx,sy],1)
						model.variables.set_upper_bounds(s[sx,sy],1)
					else:
						model.variables.set_lower_bounds(s[sx,sy],0)
						model.variables.set_upper_bounds(s[sx,sy],0)

		#model.write(outdir+"/bison.lp")
		model.solve()

		# free everything

		for (sx,sy) in ocean:
					model.variables.set_lower_bounds(s[sx,sy],0)
					model.variables.set_upper_bounds(s[sx,sy],1)

		for (rx,ry) in ocean:
					model.variables.set_lower_bounds(r[rx,ry],0)
					model.variables.set_upper_bounds(r[rx,ry],1)

		# turn on messaging to screen

		model.set_results_stream(sys.stdout)
		model.set_warning_stream(sys.stdout)


	# write model

	model.write(outdir + "/bison.lp")

	# solve model

	if instance.SOLVE == 0: # solve root relaxation (without cuts)
		model.set_problem_type(type=model.problem_type.LP)

		try:
			start = time.time()
			model.solve()
			end = time.time()
			print ("it took","{0:.2f}".format(end - start),"sec to solve root")

		except (CplexSolverError) as exc:
			print ("** Exception: ",exc)

		solution = model.solution
		print ("Solution value = ", solution.get_objective_value())
		quit()

	if instance.SOLVE == 1: # solve roots+cuts
		model.parameters.mip.limits.nodes.set(0)

		try:
			start = time.time()
			model.solve()
			end = time.time()
			print ("it took","{0:.2f}".format(end - start),"sec to solve root+cuts")

		except (CplexSolverError) as exc:
			print ("** Exception: ",exc)

		solution = model.solution
		print ("Solution value = ", solution.get_objective_value())
		print ("Best bound = ", solution.MIP.get_best_objective())
		quit()

	# solve to optimality (0.0%), until timelimit reached

	model.parameters.timelimit.set(instance.TIMELIMIT)
	model.parameters.mip.tolerances.mipgap.set(0.0)
	model.parameters.workmem.set(8192)                      # set workmem to 8 GByte
	model.parameters.mip.strategy.file.set(2)               # store node file on disk (uncompressed) when workmem is exceeded

	try:
		start = time.time()
		model.solve()
		end = time.time()
		print ("it took","{0:.2f}".format(end - start),"sec to solve")

	except (CplexSolverError) as exc:
		print ("** Exception: ",exc)

	# solution interpretation

	solution = model.solution
	objval = 0

	#print ("Solution status = ", solution.get_status())

	if solution.get_status() == solution.status.MIP_optimal:
		print ("MIP optimal")
	elif solution.get_status() == solution.status.MIP_time_limit_feasible:
		print ("MIP time limit feasible")

	if solution.is_primal_feasible():
		objval = solution.get_objective_value()

		print ("Solution value = ",objval)
		solution.write(outdir+"/bison.sol")
	else:
		print ("No solution available.")

	bestbound = solution.MIP.get_best_objective()

	print ("Best bound = ","{0:.2f}".format(bestbound))

	gap = 100.0

	if instance.GOAL == 0: # minimize cost
		if objval > 0:
			gap = (objval - bestbound) / objval * 100
	else: # maximize coverage
		if bestbound > 0:
			gap = (bestbound - objval) / bestbound * 100

	print ("MIP gap = ","{0:.2f}".format(gap),"%")

	if instance.USERCUTS == 1:
		print ("calls of user cut callback:",usercut_cb.number_of_calls)
		print ("number of user cut added:",usercut_cb.number_of_cuts_added)

	if not solution.is_primal_feasible():
		quit()

	# ---------------------------------------------------
	# --- output solution on screen
	# ---------------------------------------------------

	print ("source locations:")
	for gx,gy in ocean:
		if solution.get_values(s[gx,gy]) > 0.999:
			print ("  ("+str(gx)+", "+str(gy)+")")

	print ("receiver locations:")
	for g1x,g1y in ocean:
		if solution.get_values(r[g1x,g1y]) > 0.999:
			print ("  ("+str(g1x)+", "+str(g1y)+")")

	if instance.GOAL == 1:
		print ("covered ocean pixels:")
		for tx,ty in ocean:
			if solution.get_values(c[tx,ty]) > 0.999:
				print ("  ("+str(tx)+", "+str(ty)+")")

		print ("not covered ocean pixels:")
		for tx,ty in ocean:
			if solution.get_values(c[tx,ty]) < 0.001:
				print ("  ("+str(tx)+", "+str(ty)+")")

	# ---------------------------------------------------
	# --- output solution to files
	# ---------------------------------------------------

	file = open(outdir + "/solution-r.csv","w+")

	file.write("rx ry\n")

	for g1x,g1y in ocean:
		if solution.get_values(r[g1x,g1y]) > 0.999:
			file.write(str(g1x)+" "+str(g1y)+"\n")

	file.close()

	file = open(outdir+"/solution-s.csv","w+")

	file.write("sx sy\n")

	for gx,gy in ocean:
		if solution.get_values(s[gx,gy]) > 0.999:
			file.write(str(gx)+" "+str(gy)+"\n")

	file.close()

	# ---------------------------------------------------
	# --- compute coverage value per pixel
	# ---------------------------------------------------

	cov_val = {}

	for tx,ty in ocean:
		cov_val[tx,ty] = 0

	for tx,ty,theta,gx,gy,g1x,g1y in detection_prob:
		if solution.get_values(s[gx,gy]) > 0.999 and solution.get_values(r[g1x,g1y]) > 0.999:
			cov_val[tx,ty] = cov_val[tx,ty] + detection_prob[tx,ty,theta,gx,gy,g1x,g1y]

	# ---------------------------------------------------
	# --- output solution as latex
	# ---------------------------------------------------

	write_latex_solution(outdir, instance, ocean, map, minval, maxval, cov_val, c, solution)

	# ---------------------------------------------------
	# --- farewell
	# ---------------------------------------------------

	print ("output written to '" + color.RED + outdir + color.END + "'")

	print ("this is the end, my only friend, the end...")

