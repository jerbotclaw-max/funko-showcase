#!/usr/bin/env python3
"""Build V8 as geometric caricature sculpts.

The browser GLB and printable STL come from the same geometry.  Identity cues
are raised solids; no photograph, UV map, decal, or image plane is used on the
figure.  Coordinates are millimetres and Z is up.
"""
from __future__ import annotations

from pathlib import Path
import math

import numpy as np
import trimesh
from trimesh.transformations import rotation_matrix


ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"
STL = ROOT / "stl"
MODELS.mkdir(exist_ok=True)
STL.mkdir(exist_ok=True)


RGBA = {
    "black": (18, 18, 20, 255),
    "offblack": (31, 33, 38, 255),
    "navy": (28, 47, 76, 255),
    "navy2": (36, 55, 87, 255),
    "denim": (33, 48, 65, 255),
    "white": (245, 242, 234, 255),
    "brown": (74, 48, 34, 255),
    "darkbrown": (43, 31, 26, 255),
    "jeremy_skin": (226, 169, 128, 255),
    "ray_skin": (207, 146, 106, 255),
    "glenn_skin": (220, 164, 116, 255),
    "plate": (48, 48, 55, 255),
}


PEOPLE = {
    "jeremy": {
        "skin": RGBA["jeremy_skin"], "hair": RGBA["brown"],
        "shirt": RGBA["navy2"], "pants": RGBA["denim"],
        "traits": "short side-parted brown hair; short full brown beard; no glasses; navy collared shirt",
    },
    "ray": {
        "skin": RGBA["ray_skin"], "hair": RGBA["darkbrown"],
        "shirt": RGBA["black"], "pants": RGBA["offblack"],
        "traits": "tousled dark hair; thick rectangular black glasses; clean jaw; black shirt",
    },
    "glenn": {
        "skin": RGBA["glenn_skin"], "hair": RGBA["black"],
        "shirt": RGBA["navy"], "pants": RGBA["black"],
        "traits": "swept short black hair; clean-shaven smiling face; navy blazer over black shirt",
    },
}


def colored(mesh: trimesh.Trimesh, color) -> trimesh.Trimesh:
    mesh.visual.face_colors = np.asarray(color, dtype=np.uint8)
    return mesh


def ellipsoid(scale, center, color, subdivisions=3) -> trimesh.Trimesh:
    mesh = trimesh.creation.icosphere(subdivisions=subdivisions, radius=1.0)
    mesh.apply_scale(scale)
    mesh.apply_translation(center)
    return colored(mesh, color)


def rounded_box(scale, center, color, exponent=0.55, subdivisions=4) -> trimesh.Trimesh:
    """Rounded rectangular solid by remapping an icosphere."""
    mesh = trimesh.creation.icosphere(subdivisions=subdivisions, radius=1.0)
    verts = mesh.vertices
    verts = np.sign(verts) * np.power(np.abs(verts), exponent)
    verts *= np.asarray(scale)
    mesh.vertices = verts
    mesh.apply_translation(center)
    mesh.update_faces(mesh.unique_faces())
    mesh.remove_unreferenced_vertices()
    return colored(mesh, color)


def capsule_between(a, b, radius, color, sections=20) -> trimesh.Trimesh:
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    vector = b - a
    length = float(np.linalg.norm(vector))
    mesh = trimesh.creation.capsule(height=max(0.01, length), radius=radius, count=[sections, sections])
    z = np.array([0.0, 0.0, 1.0])
    direction = vector / length
    axis = np.cross(z, direction)
    dot = float(np.clip(np.dot(z, direction), -1.0, 1.0))
    if np.linalg.norm(axis) > 1e-8:
        mesh.apply_transform(rotation_matrix(math.acos(dot), axis))
    elif dot < 0:
        mesh.apply_transform(rotation_matrix(math.pi, [1, 0, 0]))
    mesh.apply_translation((a + b) / 2.0)
    return colored(mesh, color)


def torus_front(center, major, minor, scale_x, scale_z, color) -> trimesh.Trimesh:
    mesh = trimesh.creation.torus(major_radius=major, minor_radius=minor, major_sections=36, minor_sections=12)
    # XY torus -> XZ eyeglass frame.
    mesh.apply_transform(rotation_matrix(math.pi / 2, [1, 0, 0]))
    mesh.apply_scale([scale_x, 1.0, scale_z])
    mesh.apply_translation(center)
    return colored(mesh, color)


def merge(parts):
    return trimesh.util.concatenate([p.copy() for p in parts])


def core_body(cfg):
    parts = {}
    parts["base"] = colored(trimesh.creation.cylinder(radius=27, height=3.2, sections=64), RGBA["black"])
    parts["base"].apply_translation([0, 0, 1.6])
    parts["nameplate"] = colored(trimesh.creation.box(extents=[24, 4.5, 4.2]), RGBA["plate"])
    parts["nameplate"].apply_translation([0, -24.2, 3.0])

    shoe_l = rounded_box([8.0, 10.5, 4.8], [-9, -1.8, 7.2], RGBA["black"], .58, 3)
    shoe_r = rounded_box([8.0, 10.5, 4.8], [9, -1.8, 7.2], RGBA["black"], .58, 3)
    parts["shoes"] = merge([shoe_l, shoe_r])
    leg_l = capsule_between([-8.5, 0, 8.5], [-7, 0, 31], 5.8, cfg["pants"])
    leg_r = capsule_between([8.5, 0, 8.5], [7, 0, 31], 5.8, cfg["pants"])
    parts["legs"] = merge([leg_l, leg_r])
    parts["body"] = rounded_box([15.5, 9.7, 20.0], [0, 0, 39.5], cfg["shirt"], .62, 3)
    arm_l = capsule_between([-13, 0, 47], [-18, -1, 28], 4.7, cfg["shirt"])
    arm_r = capsule_between([13, 0, 47], [18, -1, 28], 4.7, cfg["shirt"])
    hand_l = ellipsoid([4.8, 4.8, 5.2], [-18, -1, 27], cfg["skin"], 2)
    hand_r = ellipsoid([4.8, 4.8, 5.2], [18, -1, 27], cfg["skin"], 2)
    parts["arms"] = merge([arm_l, arm_r, hand_l, hand_r])
    parts["neck"] = colored(trimesh.creation.cylinder(radius=7.0, height=8, sections=32), cfg["skin"])
    parts["neck"].apply_translation([0, 0, 55])
    return parts


def face(cfg):
    parts = {}
    parts["head"] = rounded_box([24.5, 18.0, 20.5], [0, 0, 75], cfg["skin"], .48, 4)
    ear_l = ellipsoid([4.0, 3.2, 6.0], [-23.5, 0, 74], cfg["skin"], 2)
    ear_r = ellipsoid([4.0, 3.2, 6.0], [23.5, 0, 74], cfg["skin"], 2)
    parts["ears"] = merge([ear_l, ear_r])
    eye_l = ellipsoid([5.8, 3.9, 6.8], [-9.0, -17.5, 78], RGBA["black"], 3)
    eye_r = ellipsoid([5.8, 3.9, 6.8], [9.0, -17.5, 78], RGBA["black"], 3)
    parts["eye_l"], parts["eye_r"] = eye_l, eye_r
    brow_l = capsule_between([-14, -18.0, 86], [-5, -18.5, 87], 1.15, cfg["hair"])
    brow_r = capsule_between([5, -18.5, 87], [14, -18.0, 86], 1.15, cfg["hair"])
    parts["brows"] = merge([brow_l, brow_r])
    nose = trimesh.creation.cone(radius=2.2, height=5.8, sections=24)
    nose.apply_transform(rotation_matrix(math.pi / 2, [1, 0, 0]))
    nose.apply_translation([0, -16.4, 72.5])
    parts["nose"] = colored(nose, cfg["skin"])
    return parts


def jeremy_details(cfg):
    parts = {}
    cap = ellipsoid([23.0, 17.0, 8.5], [0, 1.8, 92.0], cfg["hair"], 3)
    parts["hair"] = cap
    clumps = []
    for x, z, tilt, length in [(-17,92,-.35,9),(-11,96,-.18,11),(-4,98,.05,12),(4,98,.18,12),(11,96,.30,11),(17,92,.42,9)]:
        clumps.append(capsule_between([x-length*.45, -12.8, z-1], [x+length*.45, -14.3, z+tilt*5], 2.6, cfg["hair"]))
    parts["hair_sidepart"] = merge(clumps)
    jaw = []
    for x, z, sx in [(-18,69,5.2),(-13,65.5,5.5),(-7,63.5,5.4),(0,62.5,5.8),(7,63.5,5.4),(13,65.5,5.5),(18,69,5.2)]:
        jaw.append(ellipsoid([sx, 3.4, 4.8], [x, -17.0, z], cfg["hair"], 2))
    jaw += [capsule_between([-8,-18.5,70],[-1,-19.3,68],2.2,cfg["hair"]),
            capsule_between([1,-19.3,68],[8,-18.5,70],2.2,cfg["hair"])]
    parts["beard"] = merge(jaw)
    collar_l = capsule_between([-7,-9.2,52],[-1,-11,47],1.8,RGBA["white"])
    collar_r = capsule_between([7,-9.2,52],[1,-11,47],1.8,RGBA["white"])
    parts["polo"] = merge([collar_l, collar_r])
    return parts


def ray_details(cfg):
    parts = {}
    cap = ellipsoid([23.0, 17.0, 8.0], [0, 2, 92], cfg["hair"], 3)
    parts["hair"] = cap
    spikes = []
    for x, y, z, dx in [(-18,-7,91,2),(-13,-11,95,4),(-7,-12,98,5),(0,-12,100,2),(7,-11,99,-2),(14,-9,96,-4),(19,-5,92,-3)]:
        spikes.append(capsule_between([x-dx*.3,y+2,z-4],[x+dx,y-1,z+4],2.7,cfg["hair"]))
    parts["hair_tousled"] = merge(spikes)
    frame_l = torus_front([-9.0,-19.0,78], 6.2, .9, 1.15, .9, RGBA["black"])
    frame_r = torus_front([9.0,-19.0,78], 6.2, .9, 1.15, .9, RGBA["black"])
    bridge = capsule_between([-4.0,-19.4,79],[4.0,-19.4,79],1.1,RGBA["black"])
    temple_l = capsule_between([-15,-18.5,79],[-23,-12,80],1.0,RGBA["black"])
    temple_r = capsule_between([15,-18.5,79],[23,-12,80],1.0,RGBA["black"])
    parts["glasses"] = merge([frame_l,frame_r,bridge,temple_l,temple_r])
    return parts


def glenn_details(cfg):
    parts = {}
    cap = ellipsoid([22.8, 16.8, 7.2], [0, 2.0, 92.0], cfg["hair"], 3)
    parts["hair"] = cap
    sweep = []
    for x, z, dx in [(-16,93,8),(-10,96,10),(-3,98,11),(5,98,9),(12,96,7),(17,93,5)]:
        sweep.append(capsule_between([x-dx*.55,-13.5,z-2],[x+dx*.45,-14.2,z+1.5],2.3,cfg["hair"]))
    parts["hair_swept"] = merge(sweep)
    inner = rounded_box([8.5, 10.3, 15], [0,-1.5,40], RGBA["black"], .7, 2)
    lapel_l = capsule_between([-11,-9.0,51],[-3,-11.0,38],2.0,RGBA["navy2"])
    lapel_r = capsule_between([11,-9.0,51],[3,-11.0,38],2.0,RGBA["navy2"])
    parts["blazer"] = merge([inner,lapel_l,lapel_r])
    # Glenn's broad smile is a distinguishing solid, not a texture.
    mouth = capsule_between([-7,-18.2,68.2],[7,-18.2,68.2],1.8,RGBA["white"])
    parts["smile"] = mouth
    return parts


def build(person):
    cfg = PEOPLE[person]
    parts = {**core_body(cfg), **face(cfg)}
    details = {"jeremy": jeremy_details, "ray": ray_details, "glenn": glenn_details}[person](cfg)
    parts.update(details)

    # Add a stable semantic alias used by tests/viewer QA.
    if person == "jeremy":
        pass
    elif person == "ray":
        pass
    elif person == "glenn":
        pass

    scene = trimesh.Scene(base_frame=person)
    # STL/CAD convention is Z-up; glTF/model-viewer convention is Y-up.
    # Rotate the browser copy so former +Z becomes +Y and former -Y face
    # becomes +Z (the model-viewer default front camera).
    gltf_up = rotation_matrix(-math.pi / 2, [1, 0, 0])
    for name, mesh in parts.items():
        browser_mesh = mesh.copy()
        browser_mesh.apply_transform(gltf_up)
        scene.add_geometry(browser_mesh, geom_name=name, node_name=name)
    glb_path = MODELS / f"{person}_funko_v8.glb"
    scene.export(glb_path)

    # One boolean-unioned solid for printing. All cosmetic features overlap the
    # head/body, so color can be removed without losing identity geometry.
    solids = [m.copy() for m in parts.values()]
    printable = trimesh.boolean.union(solids, engine="manifold", check_volume=False)
    if isinstance(printable, list):
        printable = trimesh.util.concatenate(printable)
    printable.remove_unreferenced_vertices()
    printable.fix_normals()
    printable.apply_translation([0, 0, -float(printable.bounds[0, 2])])
    stl_path = STL / f"{person}_funko_v8.stl"
    printable.export(stl_path)
    print(person, glb_path.stat().st_size, stl_path.stat().st_size,
          "watertight", printable.is_watertight,
          "parts", len(printable.split(only_watertight=False)),
          "size", np.round(printable.extents, 2).tolist())


if __name__ == "__main__":
    for person in PEOPLE:
        build(person)
