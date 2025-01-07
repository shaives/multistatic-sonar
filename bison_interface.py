import streamlit as st
import folium
import json
import os

from streamlit_folium import st_folium
from folium.plugins import Draw
from datetime import datetime
from src.elevation_retriever import *

from bison import bison


def create_box_coordinates(center_lat, center_lon, size_nm):
    """Create box coordinates given center point and size in nautical miles"""
    deg_per_nm = 1/60
    half_size_deg = (size_nm/2) * deg_per_nm
    return [
        [center_lat + half_size_deg, center_lon - half_size_deg],  # NW
        [center_lat + half_size_deg, center_lon + half_size_deg],  # NE
        [center_lat - half_size_deg, center_lon + half_size_deg],  # SE
        [center_lat - half_size_deg, center_lon - half_size_deg]   # SW
    ]

def save_job_data(job_data):
    """Save job data to a JSON file with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"bison_job_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(job_data, f, indent=4)
    return filename

# Set page config
st.set_page_config(layout="wide", page_title="BISON Rancher", page_icon="🦬")

# CSS for layout control
st.markdown("""
    <style>
        /* Title styling */
        .title {
            text-align: center;
            font-size: 1.5rem;
            padding: 5px;
            border-bottom: 1px solid #ddd;
            margin-bottom: 1rem;
        }
        
        /* Button styling */
        .stButton > button {
            background-color: #FF6B00;
            color: white !important;
        }
        .stButton > button:hover {
            background-color: #FF8533;
            color: white !important;
        }
        .stButton > button:active {
            background-color: #FF6B00;
            color: white !important;
        }
        .stButton > button:focus {
            background-color: #FF6B00;
            color: white !important;
        }
        
        /* Prevent scrollbar */
        .main {
            overflow: hidden;
        }
    </style>
    """, unsafe_allow_html=True)

# Title
st.markdown("""
    <div class='title'>
        <span style='color: #FF6B00; font-weight: bold'> BISON </span> - 
        <span style='color: #FF6B00'>BI</span>static 
        <span style='color: #FF6B00'>S</span>onar 
        <span style='color: #FF6B00'>O</span>ptimizatio<span style='color: #FF6B00'>N</span>
    </div>
    """, unsafe_allow_html=True)

# Initialize session state
if 'last_clicked' not in st.session_state:
    st.session_state.last_clicked = None
if 'zoom' not in st.session_state:
    st.session_state.zoom = 5
if 'center' not in st.session_state:
    st.session_state.center = [62.0, -7.0]
if 'coordinate_area' not in st.session_state:
    st.session_state.coordinate_area = None

# Sidebar controls
with st.sidebar:
    st.header("Settings")
    
    # Optimization type
    opt_type = st.radio("Optimization Type:", ["Cost", "Coverage"])
    
    # Input fields based on optimization type
    if opt_type == "Cost":
        tx_price = st.number_input("TX Buoy Price ($)", value=12000)
        rx_price = st.number_input("RX Buoy Price ($)", value=800)
    else:
        tx_buoys = st.number_input("TX Buoys", value=4)
        rx_buoys = st.number_input("RX Buoys", value=12)

    # Area selection  
    area_size = st.radio(
        "Area Size:",
        ["10x10 NM", "30x30 NM", "60x60 NM", "Coordinates"]
    )
    
    # Coordinate inputs if selected
    if area_size == "Coordinates":
        col1, col2 = st.columns(2)
        with col1:
            nw_lat = st.number_input("NW Latitude", value=68.0)
            nw_lon = st.number_input("NW Longitude", value=-22.0)
        with col2:
            se_lat = st.number_input("SE Latitude", value=67.0)
            se_lon = st.number_input("SE Longitude", value=-21.0)
            
        # Button to draw coordinate box
        draw_coords = st.button("Draw Area")
    
    # Add divider
    st.markdown("---")
    
    # Solver Settings
    st.subheader("Solver Settings")
    
    # Heuristic selection
    heuristic = st.radio(
        "Heuristic Mode:",
        [
            "None",
            "Fast (100 rounds)",
            "Medium (250 rounds)",
            "Thorough (1000 rounds)",
        ],
        help="Heuristic search intensity. More rounds may find better solutions but take longer."
    )
    
    # Time limit selection
    time_limit_unit = st.selectbox(
        "Time Limit Unit",
        ["Hours", "Minutes", "Seconds"]
    )
    
    # Adjust time limit input based on unit
    if time_limit_unit == "Hours":
        time_limit = st.number_input(
            "Time Limit (hours)",
            min_value=1,
            max_value=168,  # 1 week
            value=10,
            help="Maximum time allowed for optimization"
        ) * 3600
    elif time_limit_unit == "Minutes":
        time_limit = st.number_input(
            "Time Limit (minutes)",
            min_value=1,
            max_value=10080,  # 1 week
            value=600,
            help="Maximum time allowed for optimization"
        ) * 60
    else:  # Seconds
        time_limit = st.number_input(
            "Time Limit (seconds)",
            min_value=1,
            max_value=604800,  # 1 week
            value=36000,
            help="Maximum time allowed for optimization"
        )

    submit = st.button("Submit Job to HPC")

# Initialize map
m = folium.Map(location=st.session_state.center, zoom_start=st.session_state.zoom)

# Add rectangles based on area type
if area_size in ["10x10 NM", "30x30 NM", "60x60 NM"] and st.session_state.last_clicked:
    coords = st.session_state.last_clicked
    size = int(area_size.split('x')[0])
    box_coords = create_box_coordinates(coords['lat'], coords['lng'], size)
    folium.Polygon(
        locations=box_coords,
        color='#FF6B00',
        fill=True,
        fillColor='#FF6B00',
        fillOpacity=0.2,
        popup=f'{size}x{size} NM Area'
    ).add_to(m)

# Add coordinate box if requested
if area_size == "Coordinates":
    if 'draw_coords' in locals() and draw_coords:
        coord_box = [
            [nw_lat, nw_lon],
            [nw_lat, se_lon],
            [se_lat, se_lon],
            [se_lat, nw_lon]
        ]
        st.session_state.coordinate_area = coord_box
    
    if st.session_state.coordinate_area:
        folium.Polygon(
            locations=st.session_state.coordinate_area,
            color='#FF6B00',
            fill=True,
            fillColor='#FF6B00',
            fillOpacity=0.2,
            popup="Coordinate-defined Area"
        ).add_to(m)

# Display the map
map_data = st_folium(
    m,
    width="100%",
    height=850,
    returned_objects=["last_clicked", "last_active_drawing", "zoom", "center"]
)

# Update stored zoom and center
if map_data.get("zoom"):
    st.session_state.zoom = map_data["zoom"]
if map_data.get("center"):
    st.session_state.center = [
        map_data["center"]["lat"],
        map_data["center"]["lng"]
    ]

# Handle map clicks for predefined sizes
if (map_data["last_clicked"] and 
    area_size in ["10x10 NM", "30x30 NM", "60x60 NM"] and 
    map_data["last_clicked"] != st.session_state.last_clicked):
    
    st.session_state.last_clicked = map_data["last_clicked"]
    st.rerun()

# Handle custom area drawing
if area_size == "Custom" and map_data["last_active_drawing"]:
    st.session_state.custom_area = map_data["last_active_drawing"]
    st.rerun()

# Clear areas when changing modes
if 'last_area_size' not in st.session_state:
    st.session_state.last_area_size = area_size
elif st.session_state.last_area_size != area_size:
    st.session_state.last_clicked = None
    st.session_state.coordinate_area = None
    st.session_state.last_area_size = area_size
    st.rerun()

# Handle form submission
if submit:
    # Check if an area was selected/drawn
    area_size in ["10x10 NM", "30x30 NM", "60x60 NM"] and st.session_state.last_clicked is not None
    
    # Create job directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_dir = f"bison_job_{timestamp}"
    os.makedirs(job_dir, exist_ok=True)
    
    # Collect all data
    job_data = {
        "optimization_type": opt_type,
        "timestamp": datetime.now().isoformat(),
        "area_size": area_size,
    }

    # Add area-specific data
    if area_size == "10x10":
        job_data.update({
            "x": 10,
            "y": 10
        })
    elif area_size == "30x30":
        job_data.update({
            "x": 10,
            "y": 10
        })
    else:
        job_data.update({
            "x": 16,
            "y": 16
        })

    job_data.update({
        "x": 10,
        "y": 10,
        "heuristic": heuristic,
        "ram": 8 * 8192,
        "time_limit": time_limit,
        "time_limit_heuristic": time_limit / 50
    })
    
    # Add type-specific data
    if opt_type == "Cost":
        job_data.update({
            "tx_price": tx_price,
            "rx_price": rx_price
        })
    else:
        job_data.update({
            "tx_buoys": tx_buoys,
            "rx_buoys": rx_buoys
        })
    
    job_data.update({
            "rho0": 8000,
            "rb": 750,
            "rx_depths": [90, 200, 400, 1000],
            "tx_depths": [50, 150, 300, 90, 400, 1500],
            "frequency": 8000
        })

    # Get corners and retrieve elevation data based on area type
    corners = None
        
    if st.session_state.last_clicked:
        size = int(area_size.split('x')[0])
        center = st.session_state.last_clicked
        box_coords = create_box_coordinates(center["lat"], center["lng"], size)
        corners = {
            "nw": {"lat": box_coords[0][0], "lon": box_coords[0][1]},
            "se": {"lat": box_coords[2][0], "lon": box_coords[2][1]}
        }
        job_data.update({
            "center_point": {"lat": center["lat"], "lon": center["lng"]},
            "size_nm": size,
            "corners": {
                "nw": corners["nw"],
                "ne": {"lat": box_coords[1][0], "lon": box_coords[1][1]},
                "se": corners["se"],
                "sw": {"lat": box_coords[3][0], "lon": box_coords[3][1]}
            }
        })
        
        try:
            
            # Create full path in outputs directory
            full_job_path = os.path.join("outputs", job_dir)
            os.makedirs(full_job_path, exist_ok=True)
            job_file = os.path.join(full_job_path, 'job_config.json')
            
            with st.spinner('Retrieving elevation data and creating configuration...'):
                # Get elevation data
                grid, metadata = get_elevation_grid(corners, resolution=10, res_size=size*2025.37/10)
                
                # Save elevation data
                elevation_file = os.path.join(full_job_path, 'elevation.asc')
                save_as_esri_ascii(grid, metadata, elevation_file)

                job_data.update({
                "job_dir": job_dir,
                "job_file": 'job_config.json',
                })
                
                # Save job data

                with open(job_file, 'w') as f:
                    json.dump(job_data, f, indent=4)
                
                st.success(f"""Job submitted successfully! 
                Files saved to outputs/{job_dir}:
                - elevation.asc (Elevation data)
                - job_config.json (Job configuration)
                
                Grid dimensions: {job_data.x} x {job_data.y} points""")
                
        except Exception as e:
            st.error(f"Error preparing job files: {str(e)}")

    print(f"Starting BISON job")

    bison(name=job_dir)