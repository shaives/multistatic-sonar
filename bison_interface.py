import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw
import json
from datetime import datetime

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
if 'custom_area' not in st.session_state:
    st.session_state.custom_area = None
if 'coordinate_area' not in st.session_state:
    st.session_state.coordinate_area = None

# Sidebar controls
with st.sidebar:
    st.header("Settings")
    
    # Optimization type
    opt_type = st.radio("Optimization Type:", ["Cost", "Coverage"])
    
    # Input fields based on optimization type
    if opt_type == "Cost":
        tx_price = st.number_input("TX Buoy Price ($)", value=10000)
        rx_price = st.number_input("RX Buoy Price ($)", value=1000)
    else:
        tx_buoys = st.number_input("TX Buoys", value=3)
        rx_buoys = st.number_input("RX Buoys", value=9)
    
    # Area selection
    area_size = st.radio(
        "Area Size:",
        ["10x10 NM", "30x30 NM", "100x100 NM", "Custom", "Coordinates"]
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

    submit = st.button("Submit Job to HPC")

# Initialize map
m = folium.Map(location=st.session_state.center, zoom_start=st.session_state.zoom)

# Add drawing controls if in custom mode
if area_size == "Custom":
    draw = Draw(
        draw_options={
            'rectangle': True,
            'polyline': False,
            'circle': False,
            'polygon': False,
            'marker': False,
            'circlemarker': False,
            'rectangle': {
                'shapeOptions': {
                    'color': '#FF6B00',
                    'fillColor': '#FF6B00',
                    'fillOpacity': 0.2
                }
            }
        },
        edit_options={'edit': False}
    )
    m.add_child(draw)

    # Draw the stored custom area in orange if it exists
    if st.session_state.custom_area:
        coords = st.session_state.custom_area['geometry']['coordinates'][0]
        folium.Polygon(
            locations=[[p[1], p[0]] for p in coords],  # Flip coordinates for folium
            color='#FF6B00',
            fill=True,
            fillColor='#FF6B00',
            fillOpacity=0.2,
            popup="Custom Area"
        ).add_to(m)

# Add rectangles based on area type
if area_size in ["10x10 NM", "30x30 NM", "100x100 NM"] and st.session_state.last_clicked:
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
    area_size in ["10x10 NM", "30x30 NM", "100x100 NM"] and 
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
    st.session_state.custom_area = None
    st.session_state.coordinate_area = None
    st.session_state.last_area_size = area_size
    st.rerun()

# Handle form submission
if submit:
    # Check if an area was selected/drawn
    area_selected = (
        (area_size == "Coordinates" and st.session_state.coordinate_area is not None) or
        (area_size == "Custom" and st.session_state.custom_area is not None) or
        (area_size in ["10x10 NM", "30x30 NM", "100x100 NM"] and st.session_state.last_clicked is not None)
    )
    
    if not area_selected:
        st.error("Please select or draw an area before submitting!")
    else:
        # Collect all data
        job_data = {
            "optimization_type": opt_type,
            "timestamp": datetime.now().isoformat(),
            "area_size": area_size
        }
        
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
        
        # Add area-specific data
        if area_size == "Coordinates":
            job_data.update({
                "coordinates": {
                    "nw": {"lat": nw_lat, "lon": nw_lon},
                    "se": {"lat": se_lat, "lon": se_lon},
                    "sw": {"lat": se_lat, "lon": nw_lon},
                    "ne": {"lat": nw_lat, "lon": se_lon}
                }
            })
        elif area_size == "Custom" and "custom_area" in st.session_state:
            coords = st.session_state.custom_area['geometry']['coordinates'][0]
            # For custom area, get corners from drawn rectangle
            lats = [p[1] for p in coords]
            lons = [p[0] for p in coords]
            job_data.update({
                "custom_area": st.session_state.custom_area,
                "corners": {
                    "sw": {"lat": min(lats), "lon": min(lons)},
                    "ne": {"lat": max(lats), "lon": max(lons)},
                    "nw": {"lat": max(lats), "lon": min(lons)},
                    "se": {"lat": min(lats), "lon": max(lons)}
                }
            })
        elif st.session_state.last_clicked:
            size = int(area_size.split('x')[0])
            center = st.session_state.last_clicked
            box_coords = create_box_coordinates(center["lat"], center["lng"], size)
            job_data.update({
                "center_point": {"lat": center["lat"], "lon": center["lng"]},
                "size_nm": size,
                "corners": {
                    "nw": {"lat": box_coords[0][0], "lon": box_coords[0][1]},
                    "ne": {"lat": box_coords[1][0], "lon": box_coords[1][1]},
                    "se": {"lat": box_coords[2][0], "lon": box_coords[2][1]},
                    "sw": {"lat": box_coords[3][0], "lon": box_coords[3][1]}
                }
            })
        
        # Save to file
        saved_file = save_job_data(job_data)
        st.success(f"Job submitted successfully! Data saved to {saved_file}")