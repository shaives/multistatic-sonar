import numpy as np

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