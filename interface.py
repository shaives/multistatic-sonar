import streamlit as st
import folium
import os

from streamlit_folium import st_folium
from folium.plugins import Draw
from datetime import datetime
from src.elevation_retriever import *


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
            "50",
            "100",
            "200",
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
    if area_size in ["10x10 NM", "30x30 NM", "60x60 NM"] and st.session_state.last_clicked is not None:
        # Create job directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        job_dir = f"bison_job_{timestamp}"
        
        # Get area dimensions
            # Add area-specific data
        if area_size == "10x10 NM" or area_size == "30x30 NM":
            x_dim = y_dim = resolution =  10  # Setting both dimensions to the area size
            size = 10
        elif area_size == "30x30 NM": 
            x_dim = y_dim = resolution =  10  # Setting both dimensions to the area size
            size = 30
        elif area_size == "60x60 NM":
            x_dim = y_dim = resolution = 16  # Setting both dimensions to the area size
            size = 60

        
        # Get corners and retrieve elevation data based on area type
        if st.session_state.last_clicked:
            center = st.session_state.last_clicked
            box_coords = create_box_coordinates(center["lat"], center["lng"], size)
            
            try:
                # Create full path in outputs directory
                full_job_path = os.path.join("outputs", job_dir)
                os.makedirs(full_job_path, exist_ok=True)
                
                with st.spinner('Retrieving elevation data and creating configuration...'):
                    # Get elevation data
                    grid, metadata = get_elevation_grid(
                        {
                            "nw": {"lat": box_coords[0][0], "lon": box_coords[0][1]},
                            "sw": {"lat": box_coords[3][0], "lon": box_coords[3][1]}
                        }, 
                        resolution = resolution, 
                        res_size = size * 1852 / resolution
                    )
                    
                    # Save elevation data
                    elevation_file = os.path.join(full_job_path, 'elevation.asc')
                    save_as_esri_ascii(grid, metadata, elevation_file)

                    # Create configuration file content
                    config_content = [
                        f'DIR        = "Instances/{job_dir}/"           # directory where to find input and store output files',
                        f'INPUT      = "elevation.asc"            # file name of ocean floor data',
                        f'RAM        = {16 * 8192}                     # RAM allocation in MB',
                        f'X          = {x_dim}                         # number of pixels in x-direction',
                        f'Y          = {y_dim}                         # number of pixels in y-direction',
                        f'GOAL       = {0 if opt_type == "Cost" else 1}                          # optimization goal: cover all pixels, minimize cost (0), or maximize coverage (1)',
                        '',
                        '# Equipment parameters',
                    ]
                    
                    # Add equipment-specific parameters
                    if opt_type == "Cost":
                        config_content.extend([
                            f'S          = {tx_price}               # cost for each deployed source',
                            f'R          = {rx_price}                 # cost for each deployed receiver',
                        ])
                    else:
                        config_content.extend([
                            f'S          = {tx_buoys}                    # number of deployed sources',
                            f'R          = {rx_buoys}                    # number of deployed receivers',
                        ])
                    
                    # Add physical parameters
                    config_content.extend([
                        '',
                        '# Physical parameters',
                        f'RHO_0      = 8000                # range of the day (in yards)',
                        f'RB         = 750                 # pulse length (for direct-blast-effect) (in yards)',
                        'FREQ       = 8000                # frequency of the sonar (in Hz)',
                        '',
                        '# Depth configuration',
                        'RX_DEPTHS  = [90, 200, 400, 1000]',
                        'TX_DEPTHS  = [50, 150, 300, 90, 400, 1500]',
                        '',
                        '# Target strength configuration',
                        'TS         = [(0.0,2000),(10.0,0),(20.0,2000),(30.0,3000),(40.0,4000),(50.0,2000),(60.0,4000),(70.0,6000),(80.0,6000),(90.0,10000),(100.0,8000),(110.0,6000),(120.0,0),(130.0,2000),(140.0,4000),(150.0,-3000),(160.0,-2000),(170.0,-2500),(180.0,2000)]          # target strength (in yards), added to range of the day'
                    ])
                    
                    # Add optimization parameters
                    config_content.extend([
                        '',
                        '# Optimization parameters',
                        'STEPS               = 30         # step size for discretization of half-circle',
                        'BOUND               = 1          # 0=individual bound per row, 1=min/max over all rows',
                        'USERCUTS            = 0          # 0=no user cuts, 1=user cuts on',
                        'USERCUTSTRENGTH     = 1.0        # how deep must user cuts be to be separated?',
                        f'HEURISTIC           = {heuristic}       # 0=no heuristic, >0: with heuristic, number of rounds',
                        'SOLVE               = 2          # 0=only root relaxation, 1=root+cuts, 2=to the end',
                        f'TIMELIMIT           = {time_limit}      # time limit in seconds',
                        f'TIMELIMIT_HEURISTIC = {int(time_limit/50)}        # time limit in seconds'
                    ])
                    
                    # Save configuration file
                    config_file = os.path.join(full_job_path, 'config.py')
                    with open(config_file, 'w') as f:
                        f.write('\n'.join(config_content))
                    
                    st.success(f"""Job submitted successfully! 
                    Files saved to outputs/{job_dir}:
                    - elevation.asc (Elevation data)
                    - config.py (BISON configuration)
                    
                    Grid dimensions: {x_dim} x {y_dim} points""")
                    
            except Exception as e:
                st.error(f"Error preparing job files: {str(e)}")

        print(f"Starting BISON job")