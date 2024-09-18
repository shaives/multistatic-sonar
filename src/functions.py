import numpy as np
import re
import time

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

def check_line(x0, y0, x1, y1, map):

	"""
	Check if a line intersects with any obstacle in the map.

	Ref: https://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm

	Parameters:
	- x0 (int): x-coordinate of the starting point of the line.
	- y0 (int): y-coordinate of the starting point of the line.
	- x1 (int): x-coordinate of the ending point of the line.
	- y1 (int): y-coordinate of the ending point of the line.
	- map (list): 2D list representing the map with obstacle values.

	Returns:
	- int: If the line intersects with an obstacle, returns 1.
	- None: If the line does not intersect with any obstacle.
	"""

	dx = abs(x1-x0)

	if x0 < x1:
		sx = 1 

	else:
		sx = -1

	dy = -abs(y1-y0)

	if y0 < y1:
		sy = 1

	else:
		sy = -1

	err = dx + dy

	while True:

		if map[x0][y0] >= 0.0:
			return 1
		
		if x0 == x1 and y0 == y1:
			return None
		
		e2 = 2 * err

		if e2 > dy:
			err = err + dy
			x0 = x0 + sx

		if e2 < dx:
			err = err + dx
			y0 = y0 + sy

def reading_in_ocean_data(instance):

	print(f"reading '" + instance.DIR + instance.INPUT + "'")

	file = open(instance.DIR + "/" + instance.INPUT, "r")
	elevation_data = file.read()
	file.close()

	ncols = int(re.search("ncols (.*)", elevation_data).group(1))
	print(f"number of columns: {ncols}")

	nrows = int(re.search("nrows (.*)", elevation_data).group(1))
	print(f"number of rows: {nrows}")

	latitude = float(re.search("xllcorner (.*)", elevation_data).group(1))
	longitude = float(re.search("yllcorner (.*)", elevation_data).group(1))
	data_delta = float(re.search("cellsize (.*)", elevation_data).group(1))

	elevation_data = re.split("\n+", elevation_data)[6:-1]

	if (nrows != len(elevation_data)+1):

		print(f"Not enough data in file")
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

def compute_coverage_triples(instance, map, ocean):

	print(f"Computing coverage")

	detection_prob = {}

	start_time_coverage = time.time()

	if len(instance.TS) == 0: # without TS

		for tar_x, tar_y in ocean: # target

			for tx_x, tx_y in ocean: # source

				for rx_x, rx_y in ocean: # receiver

					# no obstacles between source-target and target-receiver, and source-reiver	
					if check_line(tx_x, tx_y, tar_x, tar_y, map) == None and check_line(tar_x, tar_y, rx_x, rx_y, map) == None:

						if instance.CC == 0: # probabilistic model
							
							if (((d(tx_x, tx_y, tar_x, tar_y) * d(rx_x, rx_y, tar_x, tar_y)) / (instance.rho_0**2) - 1) / instance.b1) < e+10: # avoid numerical trouble from powers of large numbers
								aux = instance.pmax * (1 / (1 + 10**(((d(tx_x, tx_y, tar_x, tar_y) * d(rx_x, rx_y, tar_x, tar_y)) / (instance.rho_0**2) - 1) / instance.b1))) * (1 / (1 + 10**((1 - (d(tx_x, tx_y, tar_x, tar_y) + d(rx_x, rx_y, tar_x, tar_y)) / (d(tx_x, tx_y, rx_x, rx_y) + 2*instance.rb)) / instance.b2)))
								
								if aux > instance.pmin:
									
									detection_prob[tar_x,tar_y,0,tx_x,tx_y,rx_x,rx_y] = log(1 - aux) # detection probabilitar_y

						else: # cookie-cutter model

							if d(tx_x, tx_y, tar_x, tar_y) * d(rx_x, rx_y, tar_x, tar_y) <= instance.rho_0**2 and d(tx_x, tx_y, tar_x, tar_y) + d(rx_x, rx_y, tar_x, tar_y) >= d(tx_x, tx_y, rx_x, rx_y) + 2*instance.rb: # check for inside range-of-day Cassini oval and outside direct-blast-effect
								
								detection_prob[tar_x, tar_y, 0, tx_x, tx_y, rx_x, rx_y] = 1 # sure detection

	else: # with TS

		# only compute the angle we need to compute???

		for tar_x, tar_y in ocean: # target

			for tx_x, tx_y in ocean: # source

				if (tx_x,tx_y) != (tar_x,tar_y): # exclude equalitar_y of source and target (direct blast effect)
					
					for rx_x, rx_y in ocean: # receiver

						if (rx_x,rx_y) != (tar_x,tar_y): # exclude equalitar_y of receiver and target (direct blast effect)
						
							# no obstacles between source-target and target-receiver, and source-reiver
							if check_line(tx_x, tx_y, tar_x, tar_y, map) == None and check_line(tar_x, tar_y, rx_x, rx_y, map) == None:

								sqrt_tx_tar = 0.5 / ( sqrt((tx_x-tar_x)**2 + (tx_y-tar_y)**2) )
								sqrt_rx_tar = 0.5 / ( sqrt((rx_x-tar_x)**2 + (rx_y-tar_y)**2) )

								for theta in range(0, 180, instance.STEPS): # target angle

									my_theta = theta / 180.0 * pi
									my_sin_theta = sin(my_theta)
									my_cos_theta = cos(my_theta)

									if instance.CC == 0: # probabilistic model

										alpha = ( ((tx_x-tar_x)*my_cos_theta + (tx_y-tar_y)*my_sin_theta ) * sqrt_tx_tar + ((rx_x-tar_x)*my_cos_theta + (rx_y-tar_y)*my_sin_theta ) * sqrt_rx_tar )

										if (((d(tx_x,tx_y,tar_x,tar_y) * d(rx_x,rx_y,tar_x,tar_y)) / ((instance.rho_0 + g(alpha, instance))**2) - 1)/instance.b1) < e+10: # avoid numerical trouble from powers of large numbers
											
											aux = instance.pmax * (1 / (1 + 10**(((d(tx_x,tx_y,tar_x,tar_y) * d(rx_x,rx_y,tar_x,tar_y)) / ((instance.rho_0 + g(alpha, instance))**2) - 1)/instance.b1))) * (1 / (1 + 10**((1 - (d(tx_x,tx_y,tar_x,tar_y) + d(rx_x,rx_y,tar_x,tar_y)) / (d(tx_x,tx_y,rx_x,rx_y) + 2*instance.rb))/instance.b2)))
											
											if aux > instance.pmin:
												
												detection_prob[tar_x,tar_y,theta,tx_x,tx_y,rx_x,rx_y] = log(1 - aux) # detection probabilitar_y

									else: # cookie-cutter model
										
										if d(tx_x,tx_y,tar_x,tar_y) + d(rx_x,rx_y,tar_x,tar_y) >= d(tx_x,tx_y,rx_x,rx_y) + 2*instance.rb: # check for outside direct-blast-effect

											alpha = ( ((tx_x-tar_x) * my_cos_theta + (tx_y-tar_y) * my_sin_theta ) * sqrt_tx_tar + ((rx_x-tar_x) * my_cos_theta + (rx_y-tar_y) * my_sin_theta ) * sqrt_rx_tar )

											#print("target:",tar_x,tar_y,"angle:",theta,"source:",tx_x,tx_y,"receiver:",rx_x,rx_y,"E-angle:",alpha*180/pi,"TS:",g_cos(alpha))

											if d(tx_x,tx_y,tar_x,tar_y) * d(rx_x,rx_y,tar_x,tar_y) <= (instance.rho_0 + g(alpha, instance))**2: # check for inside range-of-day Cassini oval

												detection_prob[tar_x,tar_y,theta,tx_x,tx_y,rx_x,rx_y] = 1 # sure detection

												#print("target:",tar_x,tar_y,"angle:",theta,"source:",tx_x,tx_y,"receiver:",rx_x,rx_y,"E-angle:",alpha*180/pi,"TS:",g_cos(alpha))

	end_time_coverage = time.time()

	print(f"it took {(end_time_coverage - start_time_coverage):.2f} sec to get {len(detection_prob)} detection triples")

	return detection_prob