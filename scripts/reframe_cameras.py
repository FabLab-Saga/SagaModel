"""Reframe the stale cameras after the layout work (2026-11-25) and add two missing views. Re-runnable; every value
here is my framing choice (Magnús asked for the stale ones to be reframed, not for specific views).

    blender -b SagaV2_work.blend --python scripts/reframe_cameras.py   (or exec in the live GUI), then save.

Old framings, for undo: Cam_Entrance (31.75, 35.25, 1.62) fwd (-0.478, -0.877, -0.057) 17 mm; Cam_Lounge
(28.6, 34.3, 1.55) fwd (0.437, -0.89, -0.133) 18 mm; Cam_SecretDoor (31.3, 34.2, 1.6) fwd (-0.786, 0.616, -0.043) 22 mm.
"""
import bpy
from mathutils import Vector

# name: (eye, target, lens, props)   lens shift 0, level-ish views, sensor 36 mm
VIEWS = {
    # from the mouth of the entrance bay, past the lounge, down the lab: no sofa back filling the foreground any more
    "Cam_Entrance": ((32.4, 36.3, 1.66), (25.0, 28.6, 1.1), 18, {}),
    # lounge from the on-call corner towards the SSW glass and the textile benches; stepped back off the desk corner
    "Cam_Lounge": ((29.05, 34.05, 1.55), (31.4, 29.6, 0.95), 18, {}),
    # the bookcase door is the subject: spine end left, demo shelving right, hex relief above; clears the desk
    "Cam_SecretDoor": ((30.75, 35.45, 1.55), (27.75, 37.05, 1.25), 24, {"exposure_offset": 0.5, "shot_order": 28}),
    # NEW: entrance hero, the Fab Lab TV over the on-call desk as you walk in (open item in AGENTS.md)
    "Cam_EntranceHero": ((33.25, 36.05, 1.60), (28.3, 34.95, 1.55), 24, {"exposure_offset": 0.3}),
    # NEW: the spine's workshop face (tool library), which had no camera
    "Cam_ToolLibrary": ((24.6, 30.9, 1.55), (27.62, 33.4, 1.15), 20, {}),
}


def run():
    cams = bpy.data.collections["Cameras"]
    for name, (eye, tgt, lens, props) in VIEWS.items():
        c = bpy.data.objects.get(name) or bpy.data.objects.new(name, bpy.data.cameras.new(name))
        if c.name not in cams.objects:
            cams.objects.link(c)
        c.location = eye
        c.rotation_euler = (Vector(tgt) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
        c.data.lens, c.data.sensor_width, c.data.clip_end = lens, 36, 400
        c.data.shift_x = c.data.shift_y = 0.0
        for k, v in props.items():
            c[k] = v
    print("reframed:", ", ".join(VIEWS))


run()
