#!/usr/bin/env python3
"""Funko Pop V7 — textures BAKED into GLB at build time.
No render-time texture loading. Head = icosphere with equirect UVs,
face image composited into front hemisphere of the atlas, hair color behind.
Body parts = solid color materials. Y-up, standing.
"""
import os
import numpy as np
import trimesh
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, 'textures')
MODELS = os.path.join(ROOT, 'models')
os.makedirs(MODELS, exist_ok=True)

PEOPLE = {
    'jeremy': ((45, 60, 90), (58, 42, 30)),
    'ray':    ((55, 55, 60), (35, 32, 30)),
    'glenn':  ((70, 50, 45), (25, 22, 20)),
}

def build_figure(name, outfit, hair):
    face = Image.open(os.path.join(TEX, f'{name}.png')).convert('RGB')

    W, H = 1024, 1024
    atlas = Image.new('RGB', (W, H), hair)
    fw = W // 2
    face_r = face.resize((fw, H), Image.LANCZOS)
    atlas.paste(face_r, (W // 4, 0))

    head = trimesh.creation.icosphere(subdivisions=4, radius=1.0)
    head.apply_scale([1.0, 1.12, 0.95])
    v = head.vertices.copy()
    nrm = v / np.linalg.norm(v, axis=1, keepdims=True)
    u = 0.5 + np.arctan2(nrm[:, 0], nrm[:, 2]) / (2.0 * np.pi)
    vcoord = 0.5 - np.arcsin(np.clip(nrm[:, 1], -1.0, 1.0)) / np.pi
    uv = np.column_stack([u, vcoord])
    mat = trimesh.visual.material.SimpleMaterial(image=atlas, diffuse=(255, 255, 255), ambient=(255, 255, 255))
    head.visual = trimesh.visual.TextureVisuals(uv=uv, material=mat)
    head.apply_translation([0.0, 2.15, 0.0])

    def solid(mesh, color):
        mesh.visual.face_colors = color
        return mesh

    body = solid(trimesh.creation.capsule(height=0.85, radius=0.55), outfit + (255,))
    body.apply_translation([0.0, 1.0, 0.0])

    arm_l = solid(trimesh.creation.capsule(height=0.65, radius=0.17), outfit + (255,))
    arm_l.apply_translation([-0.72, 1.05, 0.0])
    arm_r = solid(trimesh.creation.capsule(height=0.65, radius=0.17), outfit + (255,))
    arm_r.apply_translation([0.72, 1.05, 0.0])

    leg_l = solid(trimesh.creation.capsule(height=0.45, radius=0.21), (40, 42, 48, 255))
    leg_l.apply_translation([-0.27, 0.35, 0.0])
    leg_r = solid(trimesh.creation.capsule(height=0.45, radius=0.21), (40, 42, 48, 255))
    leg_r.apply_translation([0.27, 0.35, 0.0])

    base = solid(trimesh.creation.cylinder(radius=1.15, height=0.12), (28, 28, 30, 255))
    base.apply_translation([0.0, 0.06, 0.0])

    figure = trimesh.Scene([head, body, arm_l, arm_r, leg_l, leg_r, base], base_frame=name)
    return figure

combined_meshes = []
positions = {'jeremy': -2.8, 'ray': 0.0, 'glenn': 2.8}

for name, (outfit, hair) in PEOPLE.items():
    fig = build_figure(name, outfit, hair)
    out = os.path.join(MODELS, f'{name}_funko_v7.glb')
    fig.export(out)
    print(f'wrote {out} ({os.path.getsize(out)} bytes)')

    for geom in fig.geometry.values():
        g = geom.copy()
        T = np.eye(4)
        T[0, 3] = positions[name]
        g.apply_transform(T)
        combined_meshes.append(g)

lineup = trimesh.Scene(combined_meshes)
out = os.path.join(MODELS, 'lineup_v7.glb')
lineup.export(out)
print(f'wrote {out} ({os.path.getsize(out)} bytes)')
