import arlpy.uwapm as pm

from math import sqrt

def place_in_middle_of_cell(x, y):
    """
    Takes integer x and y coordinates and places them in the middle of the grid cell.
    
    Parameters:
    - x, y: Grid coordinates (integers only)
    
    Returns:
    - x_mid, y_mid: Coordinates adjusted to the middle of the cell
    """
    return x + 0.5, y + 0.5

def getting_seafloor_depths(a_x, a_y, b_x, b_y, map_data, resolution):
    """
    Calculate seafloor depths along a line from point A to point B.
    Points are automatically placed in the middle of their respective grid cells.
    
    Parameters:
    - a_x, a_y: Coordinates of point A (integers)
    - b_x, b_y: Coordinates of point B (integers)
    - map_data: Dictionary with (x,y) keys and depth values
    - resolution: Spatial resolution of the grid in meters
    
    Returns:
    - list of [distance, depth] pairs forming a bathymetric profile
    """
    # Place points in the middle of their grid cells
    a_x, a_y = place_in_middle_of_cell(a_x, a_y)
    b_x, b_y = place_in_middle_of_cell(b_x, b_y)
    
    bathy_profile = []
    
    # Handle the case where A and B are in the same grid cell
    if int(a_x) == int(b_x) and int(a_y) == int(b_y):
        distance_ab = resolution * sqrt((b_x - a_x)**2 + (b_y - a_y)**2)
        grid_x, grid_y = int(a_x), int(a_y)
        depth = map_data.get((grid_x, grid_y), None)
        bathy_profile.append([0, depth])
        bathy_profile.append([distance_ab, depth])
        return bathy_profile
    
    # Calculate line parameters
    dx = b_x - a_x
    dy = b_y - a_y
    
    # Handle vertical or horizontal lines as special cases
    if dx == 0:  # Vertical line
        return handle_vertical_line(a_x, a_y, b_x, b_y, map_data, resolution)
    elif dy == 0:  # Horizontal line
        return handle_horizontal_line(a_x, a_y, b_x, b_y, map_data, resolution)
    
    # Calculate the slope and y-intercept of the line
    slope = dy / dx
    y_intercept = a_y - slope * a_x
    
    # Add the starting point
    grid_x_start, grid_y_start = int(a_x), int(a_y)
    depth_start = map_data.get((grid_x_start, grid_y_start), None)
    bathy_profile.append([0, depth_start])
    
    # Keep track of all intersection points
    intersections = []
    
    # Find all vertical grid line intersections
    x_start, x_end = min(a_x, b_x), max(a_x, b_x)
    x_grid_lines = range(int(x_start) + 1, int(x_end) + 1)
    
    for x in x_grid_lines:
        y = slope * x + y_intercept
        dist = resolution * sqrt((x - a_x)**2 + (y - a_y)**2)
        
        # Determine which grid cell this point belongs to
        if dx > 0:  # Moving right
            grid_x = x - 1  # The cell to the left of the grid line
        else:  # Moving left
            grid_x = x  # The cell to the right of the grid line
            
        grid_y = int(y)
        depth = map_data.get((grid_x, grid_y), None)
        intersections.append((dist, depth))
    
    # Find all horizontal grid line intersections
    y_start, y_end = min(a_y, b_y), max(a_y, b_y)
    y_grid_lines = range(int(y_start) + 1, int(y_end) + 1)
    
    for y in y_grid_lines:
        x = (y - y_intercept) / slope
        dist = resolution * sqrt((x - a_x)**2 + (y - a_y)**2)
        
        # Determine which grid cell this point belongs to
        grid_x = int(x)
        if dy > 0:  # Moving up
            grid_y = y - 1  # The cell below the grid line
        else:  # Moving down
            grid_y = y  # The cell above the grid line
            
        depth = map_data.get((grid_x, grid_y), None)
        intersections.append((dist, depth))
    
    # Add the ending point
    grid_x_end, grid_y_end = int(b_x), int(b_y)
    depth_end = map_data.get((grid_x_end, grid_y_end), None)
    distance_ab = resolution * sqrt((b_x - a_x)**2 + (b_y - a_y)**2)
    intersections.append((distance_ab, depth_end))
    
    # Sort all intersections by distance from A
    sorted_intersections = sorted(intersections)
    
    # Remove duplicates in distance and keep the depth that is different from the depth before they are the same
    previous_depth = None
    previous_distnace = None

    for dist, depth in sorted_intersections:
        if previous_depth is None or (depth != previous_depth and dist != previous_distnace):
            bathy_profile.append([dist, depth])
            previous_depth = depth
            previous_distnace = dist
        elif depth != previous_depth and dist == previous_distnace:
            bathy_profile[-1][1] = depth
            previous_depth = depth

    return bathy_profile

def handle_vertical_line(a_x, a_y, b_x, b_y, map_data, resolution):
    """Handle the special case of a vertical line."""
    bathy_profile = []
    x = a_x  # x is constant for a vertical line
    
    # Add starting point
    grid_x_start, grid_y_start = int(a_x), int(a_y)
    depth_start = map_data.get((grid_x_start, grid_y_start), None)
    bathy_profile.append([0, depth_start])
    
    # Find all horizontal grid line intersections
    y_start, y_end = min(a_y, b_y), max(a_y, b_y)
    y_grid_lines = range(int(y_start) + 1, int(y_end) + 1)
    
    intersections = []
    # Calculate intersections with horizontal grid lines
    for y in y_grid_lines:
        dist = resolution * sqrt((x - a_x)**2 + (y - a_y)**2)
        
        # Determine which grid cell this point belongs to
        grid_x = int(x)
        if b_y > a_y:  # Moving up
            grid_y = y - 1
        else:  # Moving down
            grid_y = y
            
        depth = map_data.get((grid_x, grid_y), None)
        intersections.append((dist, depth))
    
    # Add ending point
    grid_x_end, grid_y_end = int(b_x), int(b_y)
    depth_end = map_data.get((grid_x_end, grid_y_end), None)
    distance_ab = resolution * abs(b_y - a_y)
    intersections.append((distance_ab, depth_end))
    
    # Add all intersections in order of distance
    for dist, depth in sorted(intersections):
        bathy_profile.append([dist, depth])
    
    return bathy_profile

def handle_horizontal_line(a_x, a_y, b_x, b_y, map_data, resolution):
    """Handle the special case of a horizontal line."""
    bathy_profile = []
    y = a_y  # y is constant for a horizontal line
    
    # Add starting point
    grid_x_start, grid_y_start = int(a_x), int(a_y)
    depth_start = map_data.get((grid_x_start, grid_y_start), None)
    bathy_profile.append([0, depth_start])
    
    # Find all vertical grid line intersections
    x_start, x_end = min(a_x, b_x), max(a_x, b_x)
    x_grid_lines = range(int(x_start) + 1, int(x_end) + 1)
    
    intersections = []
    # Calculate intersections with vertical grid lines
    for x in x_grid_lines:
        dist = resolution * sqrt((x - a_x)**2 + (y - a_y)**2)
        
        # Determine which grid cell this point belongs to
        if b_x > a_x:  # Moving right
            grid_x = x - 1
        else:  # Moving left
            grid_x = x
            
        grid_y = int(y)
        depth = map_data.get((grid_x, grid_y), None)
        intersections.append((dist, depth))
    
    # Add ending point
    grid_x_end, grid_y_end = int(b_x), int(b_y)
    depth_end = map_data.get((grid_x_end, grid_y_end), None)
    distance_ab = resolution * abs(b_x - a_x)
    intersections.append((distance_ab, depth_end))
    
    # Add all intersections in order of distance
    for dist, depth in sorted(intersections):
        bathy_profile.append([dist, depth])
    
    return bathy_profile

def create_adaptive_sound_speed_profile(bathy):
    """
    Generate a sound speed profile dynamically based on bathymetry depths.
    
    Args:
        bathy (list): Bathymetry data containing depth information
    
    Returns:
        list: Sound speed profile with points distributed from surface to seabed
    """
    # Find the maximum depth from the bathymetry data
    max_depth = max(point[1] for point in bathy)
    
    # Basic sound speed profile parameters
    surface_speed = 1540  # Surface sound speed (m/s)
    bottom_speed = 1535   # Sound speed near the seabed (m/s)
    
    # Create a sound speed profile with depth points
    ssp = [
        [0, surface_speed],  # Surface sound speed
    ]
    
    # Define depth intervals for sound speed variation
    depth_intervals = [
        (max_depth * 0.2, 1530),   # Approximate 20% depth point
        (max_depth * 0.4, 1532),   # Approximate 40% depth point
        (max_depth * 0.6, 1533),   # Approximate 60% depth point
        (max_depth * 0.8, 1534),   # Approximate 80% depth point
        (max_depth, bottom_speed)  # Seabed sound speed
    ]
    
    # Add interpolated sound speed points
    ssp.extend(depth_intervals)
    
    return ssp

def get_environment(a_x, a_y, a_z, b_x, b_y, b_z, map_data, resolution):
    """
    Create an underwater acoustic environment between two points using Bellhop ray tracing.
    
    Args:
        a_x, a_y, a_z: Coordinates of the first point (source)
        b_x, b_y, b_z: Coordinates of the second point (receiver)
        map_data: Bathymetry map data
        resolution: Resolution for bathymetry sampling
    
    Returns:
        env: The created underwater acoustic environment
    """
    # Get seafloor depths between the two points
    bathy = getting_seafloor_depths(a_x, a_y, b_x, b_y, map_data, resolution)

    # Define the sound speed profile
    ssp = create_adaptive_sound_speed_profile(bathy)

    # Create the environment
    env = pm.create_env2d(
        depth=bathy,
        soundspeed=ssp,
        bottom_soundspeed=1450,
        bottom_density=1200,
        bottom_absorption=1.0,
        frequency=8000,
        tx_depth=a_z,
        rx_depth=b_z,
        rx_range=bathy[-1][0]  # Complete distance from bathy
    )

    return env



def check_line_bellhop(tx_x, tx_y, tx_z, rx_x, rx_y, rx_z, map_data, resolution):
    """
    Check the line between transmitter and receiver using Bellhop ray tracing.
    
    Args:
        tx_x, tx_y, tx_z: Coordinates of the transmitter
        rx_x, rx_y, rx_z: Coordinates of the receiver
        map_data: Bathymetry map data
        resolution: Resolution for bathymetry sampling
    
    Returns:
        arrivals: The computed acoustic arrivals from Bellhop, or None if no rays found
    """
    
    # Create the environment
    env = get_environment(tx_x, tx_y, tx_z, rx_x, rx_y, rx_z, map_data, resolution)
    
    # Compute eigenrays
    rays = pm.compute_eigenrays(env)

    if rays is None:
        return None
    
    arrivals = pm.compute_arrivals(env)
    
    return arrivals


