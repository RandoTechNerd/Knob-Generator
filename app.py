import streamlit as st
import numpy as np
import io
import os
import plotly.graph_objects as go
import base64 # Still needed for st.logo
from knob_lib import generate_knob_mesh, NUT_TYPES

# --- HELPER FUNCTIONS ---
def get_path(filename):
    """Resolves the path to an asset, handling dev/prod/exe environments."""
    # Check if the file exists in the current working directory (dev mode from parent)
    if os.path.exists(os.path.join("Knob STL", filename)):
        return os.path.join("Knob STL", filename)
    # Check if the file exists in the same directory as this script (dev mode from inside, or flattened exe)
    elif os.path.exists(os.path.join(os.path.dirname(__file__), filename)):
        return os.path.join(os.path.dirname(__file__), filename)
    # Fallback to just the filename
    return filename

def _get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Knob Generator",
    page_icon=get_path("icon_solid.png"),
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- BRANDING ---
st.logo(get_path("logo_main.png"), icon_image=get_path("icon_solid.png"))

# --- STATE MANAGEMENT ---
if 'knob_style' not in st.session_state:
    st.session_state.knob_style = "Round"

# --- STYLING ---
# Colors
NAVY_COLOR = "#1e293b"
SILVER_GREY_COLOR = "#cbd5e1"
WHITE_COLOR = "#ffffff"
LIGHT_GREY_TEXT = "#94a3b8" # slate-400
SIDEBAR_BG = "#e2e8f0" # Darker grey for sidebar contrast

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;500;700&display=swap');

    /* Global aggressive reset */
    html, body {{
        margin: 0 !important;
        padding: 0 !important;
        overflow-x: hidden; /* Prevent horizontal scroll */
    }}

    /* Streamlit's root app div */
    .stApp {{
        margin-top: 0 !important;
        padding-top: 0 !important;
    }}

    /* Primary Button (Orange) */
    .stButton > button {{
        background-color: #f97316 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
        box-shadow: 0 2px 4px rgba(249, 115, 22, 0.2) !important;
    }}
    .stButton > button:hover {{
        background-color: #ea580c !important;
        box-shadow: 0 4px 6px rgba(249, 115, 22, 0.3) !important;
    }}

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background-color: {SIDEBAR_BG};
        border-right: 1px solid #cbd5e1;
    }}
    /* Force text color in sidebar */
    section[data-testid="stSidebar"] .stMarkdown, 
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] label {{
        color: {NAVY_COLOR} !important;
    }}
    
    /* AGGRESSIVE HEADER REMOVAL */
    header[data-testid="stHeader"] {{
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        max-height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        visibility: hidden !important;
    }}
    .stApp > header {{
        display: none !important;
        height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }}
    
    /* Main Content Block Container Adjustments */
    .block-container {{
        padding-top: 0px !important;
        padding-bottom: 1rem !important;
        margin-top: -40px !important; /* Adjusted to avoid cutoff */
    }}
    
    h1 {{
        padding-top: 0rem !important;
        margin-top: 0rem !important;
        line-height: 1.2 !important;
    }}
    
    footer {{visibility: hidden;}}

    /* --- PROFILE STYLE BUTTONS --- */
    button[data-testid^="stButton-"] {{ 
        height: 45px; 
        font-size: 1.1rem; 
        font-weight: 600;
        border-radius: 10px;
        transition: all 0.2s ease;
        margin: 5px; 
    }}

    /* Round Button Styling */
    button[data-testid="stButton-primary-btn_round_style"] {{
        background-color: {NAVY_COLOR} !important;
    }}
    
    /* Lobed Button Styling */
    button[data-testid="stButton-primary-btn_lobed_style"] {{
        background-color: {NAVY_COLOR} !important;
    }}

    /* Inspiration link styling */
    .inspiration-link {{
        color: {LIGHT_GREY_TEXT};
        font-size: 0.85rem;
        text-align: center;
        margin-top: 20px;
    }}
    .inspiration-link a {{
        color: {LIGHT_GREY_TEXT};
        text-decoration: underline;
    }}
    .inspiration-link a:hover {{
        color: {NAVY_COLOR};
    }}


</style>
""", unsafe_allow_html=True)

# --- Dynamic Button Styling with Session State ---
# Round button
st.markdown(f"""
<style>
    button[data-testid="stButton-primary-btn_round_style"] {{
        background-color: {'#1e293b' if st.session_state.knob_style == 'Round' else '#cbd5e1'} !important;
        color: {'white' if st.session_state.knob_style == 'Round' else '#1e293b'} !important;
    }}
</style>
""", unsafe_allow_html=True)

# Lobed button
st.markdown(f"""
<style>
    button[data-testid="stButton-primary-btn_lobed_style"] {{
        background-color: {'#1e293b' if st.session_state.knob_style == 'Lobed' else '#cbd5e1'} !important;
        color: {'white' if st.session_state.knob_style == 'Lobed' else '#1e293b'} !important;
    }}
</style>
""", unsafe_allow_html=True)


# --- MAIN PAGE ---
st.title("Knob Generator") 

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.subheader("Shape & Size")
    
    st.markdown("**Profile Style**")
    
    col_r, col_l = st.columns(2)
    with col_r:
        if st.button("Round", key="btn_round_style"):
            st.session_state.knob_style = "Round"
            st.rerun()
    with col_l:
        if st.button("Lobed", key="btn_lobed_style"):
            st.session_state.knob_style = "Lobed"
            st.rerun()
            
    col_dim1, col_dim2 = st.columns(2)
    with col_dim1:
        knob_dia = st.number_input("Diameter (mm)", 10.0, 80.0, 25.0, step=0.5)
    with col_dim2:
        knob_height = st.number_input("Height (mm)", 5.0, 50.0, 15.0, step=0.5)
        
    if st.session_state.knob_style == "Lobed":
        lobes = st.slider("Lobes", 3, 32, 5) # Reverted max to 32
        lobe_protrusion = st.slider("Lobe Depth", 0.01, 1.0, 0.3, step=0.01) # Min to 0.01
        grip_ridges = 0
    else:
        lobes, lobe_protrusion = 6, 0.3
        # Grip Ridges for Round
        grip_ridges = st.select_slider("Grip Ridges (Knurling)", options=[0, 32, 64, 128], value=0)
        
    st.divider()
    st.subheader("Features")
    
    # Features Section - Dome & Fillets
    is_dome = st.checkbox("Dome Cap (Full Round)")
    
    st.markdown("**Top Rounding**")
    c_top_rad, c_top_h = st.columns(2)
    with c_top_rad:
        top_fillet_radius = st.slider("Radius (mm)", 0.0, 10.0, 2.0, 0.5, disabled=is_dome, key="top_rad")
    with c_top_h:
        top_fillet_height = st.slider("Height (mm)", 0.0, 10.0, 2.0, 0.5, disabled=is_dome, key="top_h")
    
    st.markdown("**Bottom Rounding**")
    c_bot_rad, c_bot_h = st.columns(2)
    with c_bot_rad:
        bottom_fillet_radius = st.slider("Radius (mm)", 0.0, 10.0, 0.0, 0.5, key="bot_rad")
    with c_bot_h:
        bottom_fillet_height = st.slider("Height (mm)", 0.0, 10.0, 0.0, 0.5, key="bot_h")
    
    recess_depth = 0.0
    recess_dia = 15.0
    if not is_dome:
        recess_depth = st.number_input("Finger Dish Depth (mm)", 0.0, 10.0, 0.0, step=0.5)
        if recess_depth > 0:
            recess_dia = st.slider("Dish Diameter", 5.0, knob_dia * 1.2, knob_dia * 0.8)
        
    boss_height = st.number_input("Stand-off Boss Height (mm)", 0.0, 10.0, 0.0, step=0.5)
    boss_dia = 10.0
    if boss_height > 0:
        boss_dia = st.number_input("Boss Diameter", 5.0, knob_dia, 10.0)

    st.divider()
    st.subheader("Shaft Connection")
    shaft_mode = st.selectbox("Type", ["D-Shaft", "Round Hole", "Nut Trap"])
    
    through_hole = False
    nut_info = None
    nut_loc = "Bottom"
    shaft_dia = 6.0
    hole_depth = 10.0
    
    if shaft_mode == "Nut Trap":
        c1, c2 = st.columns(2)
        with c1:
            nut_choice = st.selectbox("Nut Size", [k for k in NUT_TYPES.keys() if k != "None"])
        with c2:
            st.markdown("**Location**")
            st.caption("✅ Bottom")
            nut_loc = "Bottom"
            
        nut_info = NUT_TYPES[nut_choice]
        st.caption(f"Trap: {nut_info['width']}mm Hex x {nut_info['height']}mm H")
        
        through_hole = st.checkbox("Bolt Through-Hole?", value=True)
        shaft_dia = st.number_input("Bolt Clearance Dia", 2.0, 10.0, 3.2 if "M3" in nut_choice else 6.0)
        hole_depth = knob_height
            
    else:
        shaft_dia = st.number_input("Shaft Diameter", 2.0, 15.0, 6.0, 0.1)
        is_through = st.checkbox("Through-Hole", value=False)
        through_hole = is_through
        if not is_through:
            hole_depth = st.slider("Hole Depth", 1.0, knob_height, 10.0)

    st.divider()
    resolution = st.select_slider("Mesh Resolution", options=[32, 64, 128], value=64)


# --- MAIN VIEW ---
col_preview, col_dl = st.columns([3, 1])

with col_preview:
    try:
        mesh_obj = generate_knob_mesh(
            knob_diameter=knob_dia,
            knob_height=knob_height,
            knob_style=st.session_state.knob_style, 
            lobes=lobes,
            lobe_protrusion=lobe_protrusion,
            ridges=grip_ridges, # Pass ridges
            top_fillet_radius=top_fillet_radius, 
            top_fillet_height=top_fillet_height, 
            bottom_fillet_radius=bottom_fillet_radius, 
            bottom_fillet_height=bottom_fillet_height,
            is_dome=is_dome, 
            boss_height=boss_height,
            boss_diameter=boss_dia,
            recess_depth=recess_depth,
            recess_diameter=recess_dia,
            shaft_type=shaft_mode,
            shaft_dia=shaft_dia,
            hole_depth=hole_depth,
            through_hole=through_hole,
            nut_info=nut_info,
            nut_location=nut_loc,
            segments=resolution
        )
        
        vecs = mesh_obj.vectors
        x = vecs[:, :, 0].flatten()
        y = vecs[:, :, 1].flatten()
        z = vecs[:, :, 2].flatten()
        
        i_idx = np.arange(0, len(x), 3)
        j_idx = np.arange(1, len(x), 3)
        k_idx = np.arange(2, len(x), 3)
        
        fig = go.Figure(data=[
            go.Mesh3d(
                x=x, y=y, z=z,
                i=i_idx, j=j_idx, k=k_idx,
                color='#3b82f6', 
                opacity=1.0,
                flatshading=False, 
                lighting=dict(
                    ambient=0.4, 
                    diffuse=0.9, 
                    specular=0.1, 
                    roughness=0.5
                )
            )
        ])
        
        fig.update_layout(
            scene=dict(
                aspectmode='data',
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                zaxis=dict(visible=False),
                camera=dict(eye=dict(x=1.3, y=1.3, z=1.3)),
                bgcolor='#f8fafc' 
            ),
            margin=dict(l=0, r=0, b=0, t=0),
            height=500,
            paper_bgcolor='#f8fafc'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Generation Error: {e}")

with col_dl:
    st.metric("Volume", f"{mesh_obj.get_mass_properties()[0] / 1000:.1f} cc")
    
    out_io = io.BytesIO()
    mesh_obj.save("temp_knob.stl", fh=out_io)
    out_io.seek(0)
    
    fname = f"Knob_{st.session_state.knob_style}_{knob_dia}mm.stl"
    st.download_button("Download STL", out_io, file_name=fname, mime="application/octet-stream")
    
    st.caption("Use 'Resolution' 128 for final high-quality export.")

# --- FOOTER ---
st.markdown(f"""
<div class="inspiration-link">
    <p>Knob Generator inspired by: 
    <a href="https://forum.makerforums.info/t/openscad/94500" target="_blank" style="color: {LIGHT_GREY_TEXT}; text-decoration: underline;">Post</a>
     on 
    <a href="https://forum.makerforums.info/" target="_blank" style="color: {LIGHT_GREY_TEXT}; text-decoration: underline;">Maker Forums</a>
    </p>
    <br>
    <p style="font-size: 0.8rem; color: {LIGHT_GREY_TEXT};">
    Powered by Open Source:
    <a href="https://streamlit.io/" target="_blank" style="color: {NAVY_COLOR}; font-weight: bold;">Streamlit</a> |
    <a href="https://numpy.org/" target="_blank" style="color: {NAVY_COLOR}; font-weight: bold;">NumPy</a> |
    <a href="https://pypi.org/project/numpy-stl/" target="_blank" style="color: {NAVY_COLOR}; font-weight: bold;">numpy-stl</a> |
    <a href="https://plotly.com/python/" target="_blank" style="color: {NAVY_COLOR}; font-weight: bold;">Plotly</a>
    </p>
</div>
""", unsafe_allow_html=True)
