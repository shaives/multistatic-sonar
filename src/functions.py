import numpy as np
import re
import time

from math import *

# Euclidean distance between two points
def d(x1, y1, z1, x2, y2, z2):
    return sqrt((x1-x2)**2 + (y1-y2)**2 + (z1-z2)**2)

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

def check_line(x1, y1, z1, x2, y2, z2, ocean):

    """
    Check if a line intersects with any obstacle in the map.

    Ref: https://www.geeksforgeeks.org/bresenhams-algorithm-for-3-d-line-drawing/

    Parameters:
    - x1 (int): x-coordinate of the starting point of the line.
    - y1 (int): y-coordinate of the starting point of the line.
    - z1 (int): z-coordinate of the starting point of the line.
    - x2 (int): x-coordinate of the ending point of the line.
    - y2 (int): y-coordinate of the ending point of the line.
    - z2 (int): z-coordinate of the ending point of the line.
    - ocean (dictonary): 3D dictonary representing ocean

    Returns:
    - int: If the line intersects with an obstacle, returns 1.
    - None: If the line does not intersect with any obstacle.
    """

    ListOfPoints = []
    ListOfPoints.append((x1, y1, z1))

    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    dz = abs(z2 - z1)

    if (x2 > x1):
        xs = 1
    else:
        xs = -1
    if (y2 > y1):
        ys = 1
    else:
        ys = -1
    if (z2 > z1):
        zs = 1
    else:
        zs = -1
 
    # Driving axis is X-axis"
    if (dx >= dy and dx >= dz):        
        p1 = 2 * dy - dx
        p2 = 2 * dz - dx
        while (x1 != x2):
            x1 += xs
            if (p1 >= 0):
                y1 += ys
                p1 -= 2 * dx
            if (p2 >= 0):
                z1 += zs
                p2 -= 2 * dx
            p1 += 2 * dy
            p2 += 2 * dz
            ListOfPoints.append((x1, y1, z1))
 
    # Driving axis is Y-axis"
    elif (dy >= dx and dy >= dz):       
        p1 = 2 * dx - dy
        p2 = 2 * dz - dy
        while (y1 != y2):
            y1 += ys
            if (p1 >= 0):
                x1 += xs
                p1 -= 2 * dy
            if (p2 >= 0):
                z1 += zs
                p2 -= 2 * dy
            p1 += 2 * dx
            p2 += 2 * dz
            ListOfPoints.append((x1, y1, z1))
 
    # Driving axis is Z-axis"
    else:        
        p1 = 2 * dy - dz
        p2 = 2 * dx - dz
        while (z1 != z2):
            z1 += zs
            if (p1 >= 0):
                y1 += ys
                p1 -= 2 * dz
            if (p2 >= 0):
                x1 += xs
                p2 -= 2 * dz
            p1 += 2 * dy
            p2 += 2 * dx
            ListOfPoints.append((x1, y1, z1))

    #check this have to check all points

    for point in ListOfPoints:

        if point not in ocean:

            return 1
            

    return None     

def reading_in_ocean_data(instance):

    print(f"reading '{instance.DIR + instance.INPUT}'")

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
    ocean_surface = {}
    min_depth = -11022.0
    max_depth = 0.0

    # depth up to 400m in 40m steps
    for z in range(0, 11, 1):

        # for each line in the data
        for y, line_str in enumerate(elevation_data[(nrows - 100 - instance.Y):nrows - 100]):
            
            # for each element in the line
            for x, element in enumerate(re.split("\s+", line_str)[:instance.X]):

                element = float(element)

                # if needed, here has to be the code for avg of depths

                if z == 0 and element < 0:

                    ocean_surface[x,y,z] = 1

                # if element < step * -40m
                if element < z*-40:

                    ocean[x,y,z] = 1

                    if z == 0:

                        if element > min_depth and element < 0:

                            min_depth = element

                        if element < max_depth:

                            max_depth = element

                if z == 0:
                    
                    map[x,y] = element


    return map, ocean, ocean_surface, min_depth, max_depth

def compute_coverage_triples(instance, ocean, ocean_surface):

    detection_prob = {}

    start_time_coverage = time.time()

    if len(instance.TS) == 0: # without TS

        for tar_x, tar_y, tar_z in ocean: # target

            for tx_x, tx_y, tx_z in ocean_surface: # source

                for rx_x, rx_y, rx_z in ocean_surface: # receiver

                    # no obstacles between source-target and target-receiver, and source-reiver	
                    if check_line(tx_x, tx_y, tx_z, tar_x, tar_y, tar_z, ocean) == None and check_line(tar_x, tar_y, tar_z, rx_x, rx_y, rx_z, ocean) == None:

                        if d(tx_x, tx_y, tx_z, tar_x, tar_y, tar_z) * d(rx_x, rx_y, rx_z, tar_x, tar_y, tar_z) <= instance.rho_0**2 and d(tx_x, tx_y, tx_z, tar_x, tar_y, tar_z) + d(rx_x, rx_y, rx_z, tar_x, tar_y, tar_z) >= d(tx_x, tx_y, tx_z, rx_x, rx_y, rx_z) + 2*instance.rb: # check for inside range-of-day Cassini oval and outside direct-blast-effect
                            
                            detection_prob[tar_x, tar_y, tar_z, 0, tx_x, tx_y, tx_z, rx_x, rx_y, rx_z] = 1 # sure detection

    else: # with TS

        for tar_x, tar_y, tar_z in ocean: # target

            for tx_x, tx_y, tx_z in ocean_surface: # source

                if (tx_x, tx_y, tx_z) != (tar_x, tar_y, tar_z): # exclude equalitar_y of source and target (direct blast effect)
                    
                    for rx_x, rx_y, rx_z in ocean_surface: # receiver

                        if (rx_x, rx_y, rx_z) != (tar_x, tar_y, tar_z): # exclude equalitar_y of receiver and target (direct blast effect)
                        
                            # no obstacles between source-target and target-receiver, and source-reiver
                            if check_line(tx_x, tx_y, tx_z, tar_x, tar_y, tar_z, ocean) == None and check_line(tar_x, tar_y, tar_z, rx_x, rx_y, rx_z, ocean) == None:

                                sqrt_tx_tar = 0.5 / ( sqrt((tx_x-tar_x)**2 + (tx_y-tar_y)**2 + (tx_z-tar_z)**2) )
                                sqrt_rx_tar = 0.5 / ( sqrt((rx_x-tar_x)**2 + (rx_y-tar_y)**2 + (rx_z-tar_z)**2) )

                                for theta in range(0, 180, instance.STEPS): # target angle

                                    my_theta = theta / 180.0 * pi
                                    my_sin_theta = sin(my_theta)
                                    my_cos_theta = cos(my_theta)
                                      
                                    if d(tx_x, tx_y, tx_z, tar_x, tar_y, tar_z) + d(rx_x, rx_y, rx_z, tar_x, tar_y, tar_z) >= d(tx_x, tx_y, tx_z, rx_x, rx_y, rx_z) + 2*instance.rb: # check for outside direct-blast-effect

                                        alpha = ( ((tx_x-tar_x) * my_cos_theta + (tx_y-tar_y) * my_sin_theta ) * sqrt_tx_tar + ((rx_x-tar_x) * my_cos_theta + (rx_y-tar_y) * my_sin_theta ) * sqrt_rx_tar )

                                        #print("target:",tar_x,tar_y,"angle:",theta,"source:",tx_x,tx_y,"receiver:",rx_x,rx_y,"E-angle:",alpha*180/pi,"TS:",g_cos(alpha))

                                        if d(tx_x, tx_y, tx_z, tar_x, tar_y, tar_z) * d(rx_x, rx_y, rx_z, tar_x, tar_y, tar_z) <= (instance.rho_0 + g(alpha, instance))**2: # check for inside range-of-day Cassini oval

                                            detection_prob[tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z, rx_x, rx_y, rx_z] = 1 # sure detection

                                            #print("target:",tar_x,tar_y,"angle:",theta,"source:",tx_x,tx_y,"receiver:",rx_x,rx_y,"E-angle:",alpha*180/pi,"TS:",g_cos(alpha))

    end_time_coverage = time.time()

    print(f"it took {(end_time_coverage - start_time_coverage):.2f} sec to get {len(detection_prob)} detection triples")

    return detection_prob

def compute_rowsum_detection_prob(instance, ocean, ocean_surface, detection_prob):

    start_time_prob = time.time()

    # Do we even need the detection_prob_rowsum_r?

    detection_prob_rowsum_r = {}

    max = -10e+10
    min = 10e+10

    for tar_x, tar_y, tar_z in ocean:
        for theta in range(0,180,instance.STEPS): # target angle
            for rx_x, rx_y, rx_z in ocean_surface:
                sum = 0
                for tx_x, tx_y, tx_z in ocean_surface:

                    if (tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z, rx_x, rx_y, rx_z) in detection_prob:
                        sum = sum + detection_prob[tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z, rx_x, rx_y, rx_z]

                detection_prob_rowsum_r[tar_x, tar_y, tar_z, theta, rx_x, rx_y, rx_z] = sum

                if sum > max:
                    max = sum
                if sum < min:
                    min = sum

    if instance.BOUND == 1:
            
        for tar_x, tar_y, tar_z in ocean:
            for theta in range(0,180,instance.STEPS): # target angle
                for rx_x, rx_y, rx_z in ocean_surface:

                    detection_prob_rowsum_r[tar_x, tar_y, tar_z, theta, rx_x, rx_y, rx_z] = max


    detection_prob_rowsum_s = {}

    for tar_x, tar_y, tar_z in ocean:
        for theta in range(0,180,instance.STEPS): # target angle
            for tx_x, tx_y, tx_z in ocean_surface:
                sum = 0
                for rx_x, rx_y, rx_z in ocean_surface:
                    if (tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z, rx_x, rx_y, rx_z) in detection_prob:
                        sum = sum + detection_prob[tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z, rx_x, rx_y, rx_z]

                detection_prob_rowsum_s[tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z] = sum

                if sum > max:
                    max = sum
                if sum < min:
                    min = sum

    if instance.BOUND == 1:
        for tar_x, tar_y, tar_z in ocean:
            for theta in range(0,180,instance.STEPS): # target angle
                for tx_x, tx_y, tx_z in ocean_surface:

                    detection_prob_rowsum_s[tar_x, tar_y, tar_z, theta, tx_x, tx_y, tx_z] = max

    end_time_prob = time.time()

    print(f"It took {(end_time_prob - start_time_prob):.2f} sec to calc detection prob")

    return detection_prob_rowsum_r, detection_prob_rowsum_s