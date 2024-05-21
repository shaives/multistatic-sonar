import numpy as np
import re

from math import *

# Euclidean distance between two points
def d(x0, y0, x1, y1):
	return sqrt((x0-x1)**2 + (y0-y1)**2)

# target strength piecewise linear function g(cos(theta))
def g_cos(theta, instance):
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

def g(alpha, instance):
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

def check_line(x0, y0, x1, y1, map):
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

def reading_in_ocean_data(instance):

	print ("reading '" + instance.DIR + instance.INPUT + "'")

	file = open(instance.DIR + "/" + instance.INPUT, "r")
	elevation_data = file.read()
	file.close()

	ncols = int(re.search("ncols (.*)", elevation_data).group(1))
	print ("number of columns:",ncols)

	nrows = int(re.search("nrows (.*)", elevation_data).group(1))
	print ("number of rows:", nrows)

	latitude = float(re.search("xllcorner (.*)", elevation_data).group(1))
	longitude = float(re.search("yllcorner (.*)", elevation_data).group(1))
	data_delta = float(re.search("cellsize (.*)", elevation_data).group(1))

	elevation_data = re.split("\n+", elevation_data)[6:-1]

	if (nrows != len(elevation_data)+1):

		print ("Not enough data in file")
		quit()

	map = {}
	ocean = {}
	min_depth = -11022.0
	max_depth = 0.0

	for i, line_str in enumerate(elevation_data[(nrows - 100 - instance.Y):nrows - 100]):

		line_dict = {}
		
		for j, element in enumerate(re.split("\s+", line_str)[:instance.X]):

			# if needed, here has to be the code for avg of depths

			if float(element) < 0:

				ocean[i,j] = 1

				if float(element) > min_depth and float(element) < 0:

					min_depth = float(element)

				if float(element) < max_depth:

					max_depth = float(element)

				line_dict[j] = float(element)

		map[i] = line_dict

	return map, ocean, min_depth, max_depth