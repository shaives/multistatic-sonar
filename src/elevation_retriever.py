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

def get_elevation_grid(corners: Dict, resolution: float = 0.01) -> Tuple[np.ndarray, Dict]:
    """
    Get elevation data for area defined by corners.
    """
    # Extract boundaries
    min_lat = corners['se']['lat']
    max_lat = corners['nw']['lat']
    min_lon = corners['nw']['lon']
    max_lon = corners['se']['lon']
    
    # Calculate grid dimensions
    lat_points = int((max_lat - min_lat) / resolution) + 1
    lon_points = int((max_lon - min_lon) / resolution) + 1
    
    # Create metadata
    metadata = {
        'ncols': lon_points,
        'nrows': lat_points,
        'xllcorner': min_lon,
        'yllcorner': min_lat,
        'cellsize': resolution,
        'nodata_value': -9999
    }
    
    # Create empty grid
    grid = np.zeros((lat_points, lon_points))
    
    # Calculate total points and estimated time
    total_points = lat_points * lon_points
    estimated_time = total_points * 0.5  # 0.5 seconds per point
    print(f"Retrieving elevation data for {lat_points}x{lon_points} grid ({total_points} points)")
    print(f"Estimated time: {estimated_time/60:.1f} minutes")
    
    start_time = time.time()
    points_completed = 0
    
    # Get elevation data
    for i in range(lat_points):
        for j in range(lon_points):
            lat = max_lat - i * resolution  # Start from top
            lon = min_lon + j * resolution
            
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
