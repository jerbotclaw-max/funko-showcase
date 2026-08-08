#!/usr/bin/env python3
"""
Funko Pop STL Generator — Builds real 3D printable Funko Pop geometry.
Creates proper 3D mesh: oversized head sphere, body cylinder, arms, legs, base.
Outputs binary STL files.
"""

import struct
import math
import sys
import os

def normalize(v):
    l = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
    if l == 0: return [0,0,1]
    return [v[0]/l, v[1]/l, v[2]/l]

def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]

def sub(a, b):
    return [a[0]-b[0], a[1]-b[1], a[2]-b[2]]

class Mesh:
    def __init__(self):
        self.triangles = []
    
    def add_triangle(self, v1, v2, v3):
        normal = normalize(cross(sub(v2,v1), sub(v3,v1)))
        self.triangles.append((normal, v1, v2, v3))
    
    def add_quad(self, v1, v2, v3, v4):
        self.add_triangle(v1, v2, v3)
        self.add_triangle(v1, v3, v4)
    
    def merge(self, other):
        self.triangles.extend(other.triangles)
    
    def save_stl(self, filepath):
        with open(filepath, 'wb') as f:
            # 80-byte header
            f.write(b'Funko Pop 3D Model'.ljust(80, b'\0'))
            # triangle count
            f.write(struct.pack('<I', len(self.triangles)))
            for normal, v1, v2, v3 in self.triangles:
                for v in (normal,):
                    f.write(struct.pack('<fff', v[0], v[1], v[2]))
                for v in (v1, v2, v3):
                    f.write(struct.pack('<fff', v[0], v[1], v[2]))
                f.write(struct.pack('<H', 0))  # attribute byte count
        print(f"  Saved {filepath} ({len(self.triangles)} triangles)")

def make_sphere(cx, cy, cz, rx, ry, rz, segments=24, rings=16):
    """Ellipsoid mesh"""
    mesh = Mesh()
    for i in range(rings):
        lat0 = math.pi * (-0.5 + i / rings)
        lat1 = math.pi * (-0.5 + (i+1) / rings)
        y0 = math.sin(lat0); yr0 = math.cos(lat0)
        y1 = math.sin(lat1); yr1 = math.cos(lat1)
        for j in range(segments):
            lon0 = 2*math.pi * j / segments
            lon1 = 2*math.pi * (j+1) / segments
            x0 = math.cos(lon0); z0 = math.sin(lon0)
            x1 = math.cos(lon1); z1 = math.sin(lon1)
            
            v1 = [cx + rx*x0*yr0, cy + ry*y0, cz + rz*z0*yr0]
            v2 = [cx + rx*x1*yr0, cy + ry*y0, cz + rz*z1*yr0]
            v3 = [cx + rx*x1*yr1, cy + ry*y1, cz + rz*z1*yr1]
            v4 = [cx + rx*x0*yr1, cy + ry*y1, cz + rz*z0*yr1]
            mesh.add_quad(v1, v2, v3, v4)
    return mesh

def make_cylinder(cx, cz, y_bottom, y_top, r_bottom, r_top, segments=24):
    """Tapered cylinder"""
    mesh = Mesh()
    # Side faces
    pts_bottom = []
    pts_top = []
    for j in range(segments):
        angle = 2*math.pi * j / segments
        x = math.cos(angle)
        z = math.sin(angle)
        pts_bottom.append([cx + r_bottom*x, y_bottom, cz + r_bottom*z])
        pts_top.append([cx + r_top*x, y_top, cz + r_top*z])
    
    for j in range(segments):
        jn = (j+1) % segments
        mesh.add_quad(pts_bottom[j], pts_bottom[jn], pts_top[jn], pts_top[j])
    
    # Bottom cap
    center_b = [cx, y_bottom, cz]
    for j in range(segments):
        jn = (j+1) % segments
        mesh.add_triangle(center_b, pts_bottom[jn], pts_bottom[j])
    
    return mesh

def make_funko_pop(config):
    """
    Build a Funko Pop figure from config.
    Config has: name, head_rx, head_ry, head_rz, head_y, body_r_top, body_r_bot, 
                body_height, arm_r, leg_r, leg_height, hair config, base_r, base_h
    """
    mesh = Mesh()
    
    # Base/stand
    base = make_cylinder(0, 0, 0, config.get('base_h', 3), config.get('base_r', 14), config.get('base_r_top', 12), 24)
    mesh.merge(base)
    
    base_top = config.get('base_h', 3)
    
    # Legs
    leg_h = config.get('leg_height', 10)
    leg_r = config.get('leg_r', 4)
    leg_offset = config.get('leg_offset', 4)
    left_leg = make_cylinder(-leg_offset, 0, base_top, base_top + leg_h, leg_r, leg_r*0.9, 16)
    right_leg = make_cylinder(leg_offset, 0, base_top, base_top + leg_h, leg_r, leg_r*0.9, 16)
    mesh.merge(left_leg)
    mesh.merge(right_leg)
    
    # Body (torso) - tapered cylinder, wider at bottom
    body_bottom = base_top + leg_h
    body_h = config.get('body_height', 22)
    body_top = body_bottom + body_h
    body_r_bot = config.get('body_r_bot', 12)
    body_r_top = config.get('body_r_top', 9)
    body = make_cylinder(0, 0, body_bottom, body_top, body_r_bot, body_r_top, 24)
    mesh.merge(body)
    
    # Arms (cylinders on sides of body)
    arm_r = config.get('arm_r', 3.5)
    arm_h = config.get('arm_height', 18)
    arm_offset = body_r_top + arm_r * 0.7
    left_arm = make_cylinder(-arm_offset, 0, body_top - arm_h + 2, body_top + 1, arm_r*1.1, arm_r*0.9, 12)
    right_arm = make_cylinder(arm_offset, 0, body_top - arm_h + 2, body_top + 1, arm_r*1.1, arm_r*0.9, 12)
    mesh.merge(left_arm)
    mesh.merge(right_arm)
    
    # Head (oversized ellipsoid) - classic Funko Pop proportions
    head_rx = config.get('head_rx', 14)
    head_ry = config.get('head_ry', 15)
    head_rz = config.get('head_rz', 13)
    head_y = body_top + head_ry * 0.7  # head sits slightly embedded in body
    head = make_sphere(0, head_y, 0, head_rx, head_ry, head_rz, 32, 20)
    mesh.merge(head)
    
    # Hair (dome on top of head, slightly larger than head sphere)
    hair_rx = config.get('hair_rx', head_rx * 1.05)
    hair_ry = config.get('hair_ry', head_ry * 0.5)
    hair_rz = config.get('hair_rz', head_rz * 1.05)
    hair_y = head_y + head_ry * 0.4
    # Build upper hemisphere for hair
    hair = Mesh()
    rings = 12
    segments = 32
    for i in range(rings):
        lat0 = math.pi * (0.0 + i / (rings*2))  # upper hemisphere only
        lat1 = math.pi * (0.0 + (i+1) / (rings*2))
        y0 = math.sin(lat0); yr0 = math.cos(lat0)
        y1 = math.sin(lat1); yr1 = math.cos(lat1)
        for j in range(segments):
            lon0 = 2*math.pi * j / segments
            lon1 = 2*math.pi * (j+1) / segments
            x0 = math.cos(lon0); z0 = math.sin(lon0)
            x1 = math.cos(lon1); z1 = math.sin(lon1)
            v1 = [hair_rx*x0*yr0, hair_y + hair_ry*y0, hair_rz*z0*yr0]
            v2 = [hair_rx*x1*yr0, hair_y + hair_ry*y0, hair_rz*z1*yr0]
            v3 = [hair_rx*x1*yr1, hair_y + hair_ry*y1, hair_rz*z1*yr1]
            v4 = [hair_rx*x0*yr1, hair_y + hair_ry*y1, hair_rz*z0*yr1]
            hair.add_quad(v1, v2, v3, v4)
    mesh.merge(hair)
    
    # Funko Pop neck connector (small cylinder between body and head)
    neck_r = config.get('neck_r', 5)
    neck = make_cylinder(0, 0, body_top - 1, body_top + 3, neck_r, neck_r*0.8, 12)
    mesh.merge(neck)
    
    return mesh

# ===== CHARACTER CONFIGS =====

jeremy_config = {
    'name': 'Jeremy',
    'base_h': 3, 'base_r': 14, 'base_r_top': 12,
    'leg_height': 10, 'leg_r': 4, 'leg_offset': 4,
    'body_height': 22, 'body_r_bot': 12, 'body_r_top': 9,
    'arm_r': 3.5, 'arm_height': 18,
    'head_rx': 14, 'head_ry': 15, 'head_rz': 13,
    'hair_rx': 14.7, 'hair_ry': 8, 'hair_rz': 13.7,  # short textured hair
    'neck_r': 5,
}

ray_config = {
    'name': 'Ray',
    'base_h': 3, 'base_r': 14, 'base_r_top': 12,
    'leg_height': 10, 'leg_r': 4, 'leg_offset': 4,
    'body_height': 22, 'body_r_bot': 12, 'body_r_top': 9,
    'arm_r': 3.5, 'arm_height': 18,
    'head_rx': 14, 'head_ry': 15, 'head_rz': 13,
    'hair_rx': 14.5, 'hair_ry': 7, 'hair_rz': 13.5,  # short black hair
    'neck_r': 5,
}

glenn_config = {
    'name': 'Glenn',
    'base_h': 3, 'base_r': 14, 'base_r_top': 12,
    'leg_height': 10, 'leg_r': 4.5, 'leg_offset': 4,
    'body_height': 22, 'body_r_bot': 13, 'body_r_top': 10,
    'arm_r': 3.5, 'arm_height': 18,
    'head_rx': 14, 'head_ry': 15, 'head_rz': 13,
    'hair_rx': 14.8, 'hair_ry': 10, 'hair_rz': 13.8,  # voluminous upward hair
    'neck_r': 5,
}

outdir = os.path.dirname(os.path.abspath(__file__))
stl_dir = os.path.join(outdir, 'stl')
os.makedirs(stl_dir, exist_ok=True)

for config in [jeremy_config, ray_config, glenn_config]:
    print(f"Generating {config['name']}...")
    mesh = make_funko_pop(config)
    filepath = os.path.join(stl_dir, f"{config['name'].lower()}-funko-v5.stl")
    mesh.save_stl(filepath)

print("Done! All STL files generated.")
