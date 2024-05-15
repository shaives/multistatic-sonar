#! /usr/bin/python3

# running python3.10 and cplex 22.1.1
import sys
import re
import time
import os
import shutil
import importlib

from math import *
from datetime import datetime

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from src.output_func import *
from src.opt_model	import *
from src.functions import *
from src.classes import *

# ---------------------------------------------------
# --- let's start
# ---------------------------------------------------

if __name__ == '__main__':

	try:

		filename = sys.argv[1]
		print(filename)
		filepath = os.path.join("cfg", filename + '.py')
		print(filepath)
		if os.path.isfile(filepath):

			instance = importlib.import_module("cfg." + filename)
			timestamp = str(datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))

		else:
			print("File not found in the 'cfg' folder.")

	except IndexError:
		print("No command line argument provided.")
	
	# creating an output directory and copy config file
	outdir = 'outputs/' + filename+ '_' + timestamp 
	os.mkdir(outdir)
	shutil.copy2("./cfg/" + filename + ".py", outdir)

	# redirect output to screen and logfile
	sys.stdout = Logger(outdir) 

	print ("BISON - " + color.BOLD + "BI" + color.END + "static " + color.BOLD + "S" + color.END + "onar " + color.BOLD + "O" + color.END + "ptimizatio" + color.BOLD + "N" + color.END)
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

	print ("reading '" + instance.DIR + "/" + instance.INPUT + "'")

	file = open(instance.DIR+"/" + instance.INPUT, "r")
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

	file = open(outdir + "/ocean.dat", "w+")

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
		s = g_cos(t, instance)

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
									if check_line(gx,gy,tx,ty, map) == None and check_line(tx,ty,g1x,g1y, map) == None: # no obstacles between source-target and target-receiver, and source-reiver
										detection_prob[tx,ty,0,gx,gy,g1x,g1y] = log(1 - aux) # detection probability

						else: # cookie-cutter model
							if d(gx,gy,tx,ty) * d(g1x,g1y,tx,ty, map) <= instance.rho_0**2 and d(gx,gy,tx,ty) + d(g1x,g1y,tx,ty) >= d(gx,gy,g1x,g1y) + 2*instance.rb: # check for inside range-of-day Cassini oval and outside direct-blast-effect
								if check_line(gx,gy,tx,ty, map) == None and check_line(tx,ty,g1x,g1y, map) == None: # no obstacles between source-target, target-receiver, and source-reiver
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

									if (((d(gx,gy,tx,ty) * d(g1x,g1y,tx,ty)) / ((instance.rho_0 + g(alpha, instance))**2) - 1)/instance.b1) < e+10: # avoid numerical trouble from powers of large numbers
										aux = instance.pmax * (1 / (1 + 10**(((d(gx,gy,tx,ty) * d(g1x,g1y,tx,ty)) / ((instance.rho_0 + g(alpha, instance))**2) - 1)/instance.b1))) * (1 / (1 + 10**((1 - (d(gx,gy,tx,ty) + d(g1x,g1y,tx,ty)) / (d(gx,gy,g1x,g1y) + 2*instance.rb))/instance.b2)))
										if aux > instance.pmin:
											if check_line(gx,gy,tx,ty, map) == None and check_line(tx,ty,g1x,g1y, map) == None: # no obstacles between source-target and target-receiver, and source-reiver
												detection_prob[tx,ty,theta,gx,gy,g1x,g1y] = log(1 - aux) # detection probability

								else: # cookie-cutter model
									if d(gx,gy,tx,ty) + d(g1x,g1y,tx,ty) >= d(gx,gy,g1x,g1y) + 2*instance.rb: # check for outside direct-blast-effect
										alpha = ( ((gx-tx)*my_cos_theta + (gy-ty)*my_sin_theta ) * my_sqrt1 + ((g1x-tx)*my_cos_theta + (g1y-ty)*my_sin_theta ) * my_sqrt2 )

										#print ("target:",tx,ty,"angle:",theta,"source:",gx,gy,"receiver:",g1x,g1y,"E-angle:",alpha*180/pi,"TS:",g_cos(alpha))

										if d(gx,gy,tx,ty) * d(g1x,g1y,tx,ty) <= (instance.rho_0 + g(alpha, instance))**2: # check for inside range-of-day Cassini oval
											if check_line(gx,gy,tx,ty, map) == None and check_line(tx,ty,g1x,g1y, map) == None: # no obstacles between source-target, target-receiver
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

	solution = opt_model(instance)
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

