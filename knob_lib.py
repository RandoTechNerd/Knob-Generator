import numpy as np
import math
from stl import mesh

# --- CONSTANTS ---
NUT_TYPES = {
    "None": None,
    "M3 Nut": {"width": 5.5, "height": 2.4, "tolerance": 0.2},
    "M4 Nut": {"width": 7.0, "height": 3.2, "tolerance": 0.2},
    "M5 Nut": {"width": 8.0, "height": 4.0, "tolerance": 0.2},
    "M6 Nut": {"width": 10.0, "height": 5.0, "tolerance": 0.25},
    '1/4" Nut': {"width": 11.11, "height": 5.56, "tolerance": 0.25},
    "M8 Nut": {"width": 13.0, "height": 6.5, "tolerance": 0.3},
}

def create_circle_profile(diameter, segments=60):
    radius = diameter / 2.0
    vertices = []
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        vertices.append((radius * math.cos(angle), radius * math.sin(angle)))
    return vertices

def create_lobed_profile(diameter, lobes, protrusion_ratio, segments=60):
    r_outer = diameter / 2.0
    depth_factor = 0.6 * protrusion_ratio
    r_inner = r_outer * (1.0 - depth_factor)
    r_mid = (r_outer + r_inner) / 2.0
    amp = (r_outer - r_inner) / 2.0
    vertices = []
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        r = r_mid + amp * math.cos(lobes * angle)
        vertices.append((r * math.cos(angle), r * math.sin(angle)))
    return vertices

def create_polygon_profile(diameter, sides, segments=60):
    radius = (diameter / 2.0) / (math.sqrt(3)/2.0) 
    rotation = 0 
    apothem = diameter / 2.0
    period = 2 * math.pi / sides
    vertices = []
    for i in range(segments):
        theta = 2 * math.pi * i / segments
        angle_in_sector = (theta - rotation) % period
        angle_from_center = angle_in_sector - (period / 2.0)
        r = apothem / math.cos(angle_from_center)
        vertices.append((r * math.cos(theta), r * math.sin(theta)))
    return vertices

def create_d_shaft_profile(diameter, flat_to_opposite, segments=60):
    radius = diameter / 2.0
    d_center_to_flat = flat_to_opposite - radius
    vertices = []
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        rx = radius * math.cos(angle)
        ry = radius * math.sin(angle)
        if rx > d_center_to_flat:
             rx_new = d_center_to_flat
             ry_new = d_center_to_flat * math.tan(angle)
             vertices.append((rx_new, ry_new))
        else:
            vertices.append((rx, ry))
    return vertices


def generate_knob_mesh(
    # Geometry
    knob_diameter=25.0, 
    knob_height=15.0,
    knob_style="Round",
    lobes=6,
    lobe_protrusion=0.3,
    
    # NEW: Grip Ridges for Round Style
    ridges=0, 
    
    top_fillet_radius=2.0, 
    top_fillet_height=2.0, 
    bottom_fillet_radius=0.0,
    bottom_fillet_height=0.0, 
    is_dome=False,
    
    # Boss
    boss_height=0.0,
    boss_diameter=10.0,
    
    # Recess
    recess_depth=0.0,
    recess_diameter=15.0,
    
    # Shaft
    shaft_type="D-Shaft", 
    shaft_dia=6.0, 
    hole_depth=10.0, 
    through_hole=False, 
    nut_info=None,
    nut_location="Bottom", 
    
    segments=64
):
    
    # --- 1. PROFILES ---
    if knob_style == "Lobed":
        body_profile = create_lobed_profile(knob_diameter, lobes, lobe_protrusion, segments)
    else:
        # Round Style
        if ridges > 0:
            # Use lobed profile logic for ridges
            # Low protrusion for "grip" (e.g. 0.05 or 0.1)
            # We treat 'ridges' as 'lobes'.
            # Default grip depth: 0.05 (5%)
            grip_depth = 0.05 
            body_profile = create_lobed_profile(knob_diameter, ridges, grip_depth, segments)
        else:
            body_profile = create_circle_profile(knob_diameter, segments)
        
    boss_profile = create_circle_profile(boss_diameter, segments)
    
    if shaft_type == "D-Shaft":
        flat_val = 4.5 if shaft_dia == 6.0 else (shaft_dia * 0.75)
        shaft_profile = create_d_shaft_profile(shaft_dia, flat_val, segments)
    elif shaft_type == "Nut Trap" and nut_info:
        shaft_profile = create_circle_profile(shaft_dia, segments) 
    else:
        shaft_profile = create_circle_profile(shaft_dia, segments)


    # --- 2. MESH STATE ---
    all_vertices = []
    all_faces = []
    
    def add_quad(p1, p2, p3, p4, flip=False):
        idx = len(all_vertices)
        all_vertices.extend([p1, p2, p3, p4])
        if flip:
            all_faces.append([idx, idx+2, idx+1])
            all_faces.append([idx, idx+3, idx+2])
        else:
            all_faces.append([idx, idx+1, idx+2])
            all_faces.append([idx, idx+2, idx+3])

    # --- 3. OUTER SHELL ---
    outer_rings = []
    z_base = 0.0
    
    # Boss First
    if boss_height > 0.1:
        z_base = boss_height
        outer_rings.append([(p[0], p[1], 0.0) for p in boss_profile])
        outer_rings.append([(p[0], p[1], boss_height) for p in boss_profile])
        
    # Main Body with Bottom Fillet
    if bottom_fillet_radius > 0 or bottom_fillet_height > 0:
        b_fillet_steps = 6
        for s in range(b_fillet_steps + 1):
            t = s / b_fillet_steps
            z_f = z_base + bottom_fillet_height * t
            
            # Concave Cove Logic
            if bottom_fillet_height > 0:
                ratio = 1.0 - math.sin(t * math.pi / 2.0)
                inset = bottom_fillet_radius * ratio
            else:
                inset = 0.0
            
            new_ring = []
            for p in body_profile:
                mag = math.sqrt(p[0]**2 + p[1]**2)
                scale = (mag - inset) / mag if mag > 0.001 else 1.0
                new_ring.append((p[0]*scale, p[1]*scale, z_f))
            outer_rings.append(new_ring)
            
        current_z = z_base + bottom_fillet_height
    else:
        outer_rings.append([(p[0], p[1], z_base) for p in body_profile])
        current_z = z_base

    # Main Wall -> Top Fillet
    z_top_abs = z_base + knob_height
    z_fillet_start = max(current_z, z_top_abs - top_fillet_height)
    if is_dome: z_fillet_start = current_z 
        
    outer_rings.append([(p[0], p[1], z_fillet_start) for p in body_profile])
    
    # Top Fillet / Dome
    if is_dome:
        dome_steps = 12
        h_dome = z_top_abs - z_fillet_start
        for s in range(1, dome_steps + 1):
            t = s / dome_steps
            z_curr = z_fillet_start + h_dome * t
            z_local = z_curr - z_fillet_start
            r_factor = math.sqrt(max(0, 1 - (z_local/h_dome)**2)) if h_dome > 0 else 0
            new_ring = []
            for p in body_profile:
                new_ring.append((p[0]*r_factor, p[1]*r_factor, z_curr))
            outer_rings.append(new_ring)
            
    elif top_fillet_radius > 0 or top_fillet_height > 0:
        fillet_steps = 8 
        for s in range(1, fillet_steps + 1):
            t = s / fillet_steps 
            dz_fillet_local = top_fillet_height * t 
            z_curr = z_fillet_start + dz_fillet_local
            
            if top_fillet_height > 0:
                # Standard Convex Roundover for Top
                inset = top_fillet_radius * (1 - math.sqrt(max(0, 1 - (dz_fillet_local / top_fillet_height)**2)))
            else:
                inset = 0.0
            
            new_ring = []
            for p in body_profile:
                mag = math.sqrt(p[0]**2 + p[1]**2)
                scale = (mag - inset) / mag if mag > 0.001 else 1.0
                new_ring.append((p[0]*scale, p[1]*scale, z_curr))
            outer_rings.append(new_ring)
            
    # Stitch Outer Shell
    for r in range(len(outer_rings) - 1):
        ring_curr = outer_rings[r]
        ring_next = outer_rings[r+1]
        for i in range(segments):
            next_i = (i + 1) % segments
            add_quad(ring_curr[i], ring_curr[next_i], ring_next[next_i], ring_next[i])

    # --- 4. TOP CLOSURE / RECESS ---
    top_outer_ring = outer_rings[-1]
    z_top_mesh = top_outer_ring[0][2]
    
    total_z_height = z_base + knob_height
    z_shaft_top_limit = hole_depth
    
    if through_hole:
        if is_dome:
            z_shaft_top_limit = total_z_height 
        elif recess_depth > 0:
            z_shaft_top_limit = max(z_base, total_z_height - recess_depth)
        else:
            z_shaft_top_limit = total_z_height

    if is_dome:
        final_r = math.sqrt(top_outer_ring[0][0]**2 + top_outer_ring[0][1]**2)
        if final_r > 0.1: 
             center = [0.0, 0.0, z_top_mesh]
             idx_c = len(all_vertices)
             all_vertices.append(center)
             for i in range(segments):
                next_i = (i + 1) % segments
                idx_o1 = len(all_vertices)
                idx_o2 = idx_o1 + 1
                all_vertices.extend([top_outer_ring[i], top_outer_ring[next_i]])
                all_faces.append([idx_c, idx_o1, idx_o2])
                
    elif recess_depth > 0:
        z_floor_abs = z_top_mesh - recess_depth
        recess_start_poly = create_circle_profile(recess_diameter, segments)
        recess_start_ring = [(p[0], p[1], z_top_mesh) for p in recess_start_poly]
        for i in range(segments):
            next_i = (i + 1) % segments
            add_quad(top_outer_ring[i], top_outer_ring[next_i], 
                     recess_start_ring[next_i], recess_start_ring[i])
        dish_steps = 5
        dish_rings = [recess_start_ring]
        hole_r = shaft_dia / 2.0 if through_hole else 0.0
        for s in range(1, dish_steps + 1):
            t = s / dish_steps
            curr_radius_factor = (1.0 - t) 
            curr_r = (recess_diameter/2.0) * curr_radius_factor
            z_curr = z_top_mesh - recess_depth * (1.0 - curr_radius_factor**2)
            if curr_r < hole_r: curr_r = hole_r
            poly = []
            for i in range(segments):
                angle = 2 * math.pi * i / segments
                poly.append((curr_r * math.cos(angle), curr_r * math.sin(angle), z_curr))
            dish_rings.append(poly)
            if curr_r <= hole_r + 0.001: break 
        for r in range(len(dish_rings) - 1):
            curr = dish_rings[r]
            nxt = dish_rings[r+1]
            for i in range(segments):
                next_i = (i + 1) % segments
                add_quad(curr[i], curr[next_i], nxt[next_i], nxt[i])
        final_ring = dish_rings[-1]
        z_final = final_ring[0][2]
        z_shaft_top_limit = z_final
        final_r = math.sqrt(final_ring[0][0]**2 + final_ring[0][1]**2)
        is_open = through_hole or (shaft_type == "Nut Trap" and nut_location == "Top")
        if not is_open and final_r > 0.1:
            center = [0.0, 0.0, z_final]
            idx_c = len(all_vertices)
            all_vertices.append(center)
            for i in range(segments):
                next_i = (i + 1) % segments
                idx_r1 = len(all_vertices)
                idx_r2 = idx_r1 + 1
                all_vertices.extend([final_ring[i], final_ring[next_i]])
                all_faces.append([idx_c, idx_r1, idx_r2])
    else:
        is_open = through_hole or (shaft_type == "Nut Trap" and nut_location == "Top")
        if is_open:
             p = create_circle_profile(shaft_dia, segments)
             if shaft_type == "Nut Trap" and nut_location == "Top":
                 w = nut_info["width"] + nut_info.get("tolerance", 0.2)
                 p = create_polygon_profile(w, 6, segments)
             hole_poly = [(v[0], v[1], z_top_mesh) for v in p]
             for i in range(segments):
                next_i = (i + 1) % segments
                add_quad(top_outer_ring[i], top_outer_ring[next_i], hole_poly[next_i], hole_poly[i])
             z_shaft_top_limit = z_top_mesh
        else:
            center = [0.0, 0.0, z_top_mesh]
            idx_c = len(all_vertices)
            all_vertices.append(center)
            for i in range(segments):
                next_i = (i + 1) % segments
                idx_o1 = len(all_vertices)
                idx_o2 = idx_o1 + 1
                all_vertices.extend([top_outer_ring[i], top_outer_ring[next_i]])
                all_faces.append([idx_c, idx_o1, idx_o2])

    # --- 5. INNER & 6. BOTTOM ---
    if shaft_type == "Nut Trap" and nut_info:
        w = nut_info["width"] + nut_info.get("tolerance", 0.2)
        h = nut_info["height"] + 0.2
        trap_poly = create_polygon_profile(w, 6, segments)
        if nut_location == "Bottom":
            for i in range(segments):
                next_i = (i + 1) % segments
                p1 = [trap_poly[i][0], trap_poly[i][1], 0.0]
                p2 = [trap_poly[next_i][0], trap_poly[next_i][1], 0.0]
                p3 = [trap_poly[next_i][0], trap_poly[next_i][1], h]
                p4 = [trap_poly[i][0], trap_poly[i][1], h]
                add_quad(p1, p2, p3, p4, flip=True)
            shaft_p = create_circle_profile(shaft_dia, segments)
            for i in range(segments):
                next_i = (i + 1) % segments
                t1 = [trap_poly[i][0], trap_poly[i][1], h]
                t2 = [trap_poly[next_i][0], trap_poly[next_i][1], h]
                s1 = [shaft_p[i][0], shaft_p[i][1], h]
                s2 = [shaft_p[next_i][0], shaft_p[next_i][1], h]
                add_quad(t2, t1, s1, s2) 

    z_bot = 0.0
    z_top = hole_depth
    if through_hole: z_top = z_shaft_top_limit
    
    if shaft_type == "Nut Trap" and nut_location == "Bottom":
        z_bot = nut_info["height"] + 0.2
        
    if z_top > z_bot:
        for i in range(segments):
            next_i = (i + 1) % segments
            p1 = [shaft_profile[i][0], shaft_profile[i][1], z_bot]
            p2 = [shaft_profile[next_i][0], shaft_profile[next_i][1], z_bot]
            p3 = [shaft_profile[next_i][0], shaft_profile[next_i][1], z_top]
            p4 = [shaft_profile[i][0], shaft_profile[i][1], z_top]
            add_quad(p1, p2, p3, p4, flip=True)
        if not through_hole and shaft_type != "Nut Trap":
             center = [0.0, 0.0, z_top]
             idx_c = len(all_vertices)
             all_vertices.append(center)
             for i in range(segments):
                next_i = (i + 1) % segments
                idx_p1 = len(all_vertices)
                idx_p2 = idx_p1 + 1
                all_vertices.extend([
                    [shaft_profile[i][0], shaft_profile[i][1], z_top],
                    [shaft_profile[next_i][0], shaft_profile[next_i][1], z_top]
                ])
                all_faces.append([idx_c, idx_p1, idx_p2])

    bottom_outer_ring = outer_rings[0]
    inner_bottom = []
    if shaft_type == "Nut Trap" and nut_location == "Bottom":
         w = nut_info["width"] + nut_info.get("tolerance", 0.2)
         p = create_polygon_profile(w, 6, segments)
         inner_bottom = [(v[0], v[1], 0.0) for v in p]
    else:
         inner_bottom = [(v[0], v[1], 0.0) for v in shaft_profile]
         
    for i in range(segments):
        next_i = (i + 1) % segments
        add_quad(bottom_outer_ring[next_i], bottom_outer_ring[i], inner_bottom[i], inner_bottom[next_i])

    data = np.zeros(len(all_faces), dtype=mesh.Mesh.dtype)
    np_verts = np.array(all_vertices)
    for i, face in enumerate(all_faces):
        for j in range(3):
            data['vectors'][i][j] = np_verts[face[j]]
            
    return mesh.Mesh(data)