# JC Dream custom figure requirements

Source: requirements explicitly stated in JC Dream chat through 2026-08-08.

## Product requirements

1. Three separate, recognizable Funko-style figures: Jeremy, Ray, and Glenn.
2. Actual 3D geometry, not image planes, standees, or face decals presented as 3D.
3. Upright, front-facing figures with person-specific hair, facial hair, glasses, clothing, and skin tone derived from the same-chat reference photos.
4. Printable STL for each person. The mesh must be watertight, have positive volume, stand on a flat base, and contain no detached decorative shells.
5. Colored GLB for browser inspection. Facial features must remain visible even if all textures fail to load.
6. The web page must label every person, show the real reference photo beside the current rendered figure, provide STL/GLB downloads, and support drag/zoom.
7. Earlier revisions remain available for judging, with a working version switcher.
8. Do not announce a revision as successful until front, three-quarter, side, and back renders have been inspected for all three people.

## V8 acceptance gate

- Automated: all three GLBs and STLs exist; GLBs contain geometric eyes/hair and person-specific details; STLs are watertight, one connected component, and rest on Z=0; page includes current labels, downloads, and prior-version controls.
- Visual: correct orientation; no blank faces; no smeared color; no occluded eyes; no corpse pose; recognizable distinguishing traits for each person.
- Honest limitation: likeness is a stylized caricature from one low-resolution reference image per person, not a scan-quality portrait.
