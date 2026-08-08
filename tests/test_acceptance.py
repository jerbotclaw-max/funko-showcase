#!/usr/bin/env python3
"""Acceptance tests for the current custom-figure release."""
from pathlib import Path
import json
import re

import trimesh


ROOT = Path(__file__).resolve().parents[1]
PEOPLE = ("jeremy", "ray", "glenn")


def test_v8_assets_exist():
    for person in PEOPLE:
        assert (ROOT / "models" / f"{person}_funko_v8.glb").stat().st_size > 10_000
        assert (ROOT / "stl" / f"{person}_funko_v8.stl").stat().st_size > 10_000


def test_print_meshes_are_single_watertight_figures_on_floor():
    for person in PEOPLE:
        mesh = trimesh.load(ROOT / "stl" / f"{person}_funko_v8.stl", force="mesh")
        assert mesh.is_watertight, person
        assert len(mesh.split(only_watertight=False)) == 1, person
        assert mesh.volume > 1_000, person
        assert abs(float(mesh.bounds[0, 2])) < 0.01, person
        assert float(mesh.extents[2]) > float(mesh.extents[0]) * 1.2, person


def test_glbs_have_geometric_identity_parts():
    required = {"head", "eye_l", "eye_r", "hair", "body", "base", "nameplate"}
    person_specific = {
        "jeremy": {"beard", "hair_sidepart"},
        "ray": {"glasses", "hair_tousled"},
        "glenn": {"hair_swept", "blazer"},
    }
    for person in PEOPLE:
        scene = trimesh.load(ROOT / "models" / f"{person}_funko_v8.glb", force="scene")
        names = set(scene.geometry)
        assert required <= names, (person, required - names)
        assert person_specific[person] <= names, (person, person_specific[person] - names)


def test_page_labels_downloads_and_version_controls():
    page = (ROOT / "index.html").read_text()
    assert "V8" in page
    for person in PEOPLE:
        assert f'{person}_funko_v8.glb' in page
        assert f'{person}_funko_v8.stl' in page
        assert f'images/{person}-ref.jpg' in page
    for version in ("v8", "v7", "v5", "v3", "v1"):
        assert re.search(rf"showVer\([^\n]+['\"]{version}['\"]", page), version
