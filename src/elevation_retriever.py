import requests
import numpy as np
from typing import Dict, Tuple
import time

def get_elevation_single_point(lat: float, lon: float, retry_count: int = 3) -> float:
    """
    Get elevation for a single point, trying multiple APIs if needed.
    """
    # List of APIs to try with their rate limits
    apis = [
        {
            'name': 'Home API',
            'url': "http://localhost:5000/v1/gebco2024",
            'params': lambda lat, lon: f"?locations={lat},{lon}",
            'extract': lambda r: r.json()['results'][0]['elevation'],
            'rate_limit': 0.2  # 1 request per 0.2 seconds (5 per second)
        },
        {
            'name': 'OpenTopoData',
            'url': "https://api.opentopodata.org/v1/gebco2020",
            'params': lambda lat, lon: f"?locations={lat},{lon}",
            'extract': lambda r: r.json()['results'][0]['elevation'],
            'rate_limit': 1  # 1 request per 1 seconds (1 per second)
        }
    ]
    
    last_api_used = None
    for api in apis:
        # Add delay if using same API repeatedly
        if last_api_used == api['name']:
            time.sleep(api['rate_limit'])
            
        for attempt in range(retry_count):
            try:
                full_url = f"{api['url']}{api['params'](lat, lon)}"
                print(f"Trying {api['name']} API...")
                
                response = requests.get(full_url, timeout=10)
                last_api_used = api['name']
                
                if response.status_code == 200:
                    return api['extract'](response)
                elif response.status_code == 429:  # Too Many Requests
                    print(f"{api['name']} rate limit hit, waiting {api['rate_limit']*2} seconds...")
                    time.sleep(api['rate_limit'] * 2)  # Wait longer on rate limit
                else:
                    print(f"{api['name']} returned status {response.status_code}")
                    
            except Exception as e:
                print(f"Error with {api['name']}: {str(e)}")
                if attempt < retry_count - 1:
                    wait_time = api['rate_limit'] * (attempt + 1)  # Exponential backoff
                    print(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
    
    print(f"All APIs failed for lat={lat}, lon={lon}")
    return None

def get_elevation_grid(corners: Dict, resolution: int = 10, res_size: float = 1852) -> Tuple[np.ndarray, Dict]:
    """
    Get elevation data for area defined by corners.
    """

    # Create metadata
    metadata = {
        'ncols': resolution,
        'nrows': resolution,
        'xllcorner': corners['sw']['lon'],
        'yllcorner': corners['sw']['lat'],
        'cellsize': res_size,
        'nodata_value': -9999
    }
    
    # Create empty grid
    grid = np.zeros((resolution, resolution))
    
    # Calculate total points and estimated time
    total_points = resolution * resolution
    estimated_time = total_points * 0.5  # 0.5 seconds per point
    print(f"Retrieving elevation data for {resolution}x{resolution} grid ({total_points} points)")
    print(f"Estimated time: {estimated_time/60:.1f} minutes")
    
    start_time = time.time()
    points_completed = 0
    
    # Constants for converting meters to degrees
    # At the equator, 1 degree of latitude = 111,320 meters
    # Longitude degrees vary with latitude due to the Earth's curvature
    METERS_PER_DEGREE_LAT = 111320.0
    
    def meters_per_degree_lon(lat):
        """Calculate meters per degree of longitude at a given latitude"""
        return METERS_PER_DEGREE_LAT * np.cos(np.radians(lat))
    
    # Calculate center latitude for longitude conversion
    center_lat = (corners['nw']['lat'] + corners['sw']['lat']) / 2
    meters_per_degree_longitude = meters_per_degree_lon(center_lat)
    
    # Calculate cell sizes in degrees
    cell_size_lat = res_size / METERS_PER_DEGREE_LAT
    cell_size_lon = res_size / meters_per_degree_longitude
    
    # Get elevation data
    for i in range(resolution):
        for j in range(resolution):
            # Calculate lat/lon for current cell
            # Start from top-left (northwest) corner and add half cell size to get center
            lat = corners['nw']['lat'] - (i * cell_size_lat) - (0.5 * cell_size_lat)
            lon = corners['nw']['lon'] + (j * cell_size_lon) + (0.5 * cell_size_lon)
            
            elevation = get_elevation_single_point(lat, lon)
            grid[i, j] = elevation if elevation is not None else metadata['nodata_value']
            
            # Update progress
            points_completed += 1
            if points_completed % 10 == 0:
                elapsed_time = time.time() - start_time
                points_per_second = points_completed / elapsed_time
                remaining_points = total_points - points_completed
                estimated_remaining = remaining_points / points_per_second
                
                print(f"Progress: {points_completed}/{total_points} points ({points_completed/total_points*100:.1f}%)")
                print(f"Estimated time remaining: {estimated_remaining/60:.1f} minutes")
    
    return grid, metadata

def save_as_esri_ascii(grid: np.ndarray, metadata: Dict, filename: str) -> None:
    """Save elevation data in ESRI ASCII grid format."""
    with open(filename, 'w') as f:
        # Write header
        f.write(f"ncols {metadata['ncols']}\n")
        f.write(f"nrows {metadata['nrows']}\n")
        f.write(f"xllcorner {metadata['xllcorner']}\n")
        f.write(f"yllcorner {metadata['yllcorner']}\n")
        f.write(f"cellsize {metadata['cellsize']}\n")
        f.write(f"nodata_value {metadata['nodata_value']}\n")
        
        # Write data rows
        for row in grid:
            formatted_row = ' '.join([f"{val:.2f}" for val in row])
            f.write(f"{formatted_row}\n")
