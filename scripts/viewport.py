"""Point the user's live Blender viewport (all 3D views) at something, in Rendered shading.
Run via the MCP socket:  python3 scripts/bmcp.py <<< "EYE=(31.6,35.0,1.8); TARGET=(30.6,31.9,0.6); exec(open(bpy.path.abspath('//scripts/viewport.py')).read())"
or exec it with EYE/TARGET defined. The view looks along -Z of view_rotation, so the quaternion is
(target - eye).to_track_quat('-Z', 'Y')  -  using 'Z' points the view backwards (you see the floor's underside).
Verifies with a screenshot of the area into $TMPDIR (path printed).
"""
import os

import bpy
from mathutils import Vector

eye, tgt = Vector(globals().get("EYE", (31.6, 35.0, 1.8))), Vector(globals().get("TARGET", (30.6, 31.9, 0.6)))
d = tgt - eye
shot = os.path.join(os.environ.get("TMPDIR", "/tmp"), "viewport.png")
for w in bpy.context.window_manager.windows:
    for a in w.screen.areas:
        if a.type != "VIEW_3D":
            continue
        sp = a.spaces.active
        r = sp.region_3d
        r.view_perspective = "PERSP"
        r.view_rotation = d.to_track_quat("-Z", "Y")
        r.view_location = tgt
        r.view_distance = d.length
        sp.shading.type = "RENDERED"
        a.tag_redraw()
print("viewport ->", tuple(round(v, 2) for v in eye), "looking at", tuple(round(v, 2) for v in tgt))
