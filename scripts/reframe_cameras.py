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
    # --- branch alternate-ideas 2026-11-26 (my framings; the review pass found them stale). Old framings, for undo:
    # FeltDetail (22.4, 28.7, 1.7) fwd (-0.288, 0.865, 0.412) 30 mm; Craft (24.4, 30.7, 1.6) fwd (-0.865, 0.459,
    # -0.203) 18; SewingDetail (22.1, 33.4, 1.35) fwd (-0.704, -0.616, -0.352) 35; Micro (25.6, 33.3, 1.65) fwd
    # (-0.454, -0.881, -0.133) 20; Workshop (26.6, 33.9, 1.65) fwd (-0.336, -0.941, -0.05) 18; ShopBot (23.55, 22.55,
    # 1.75) fwd (-0.403, -0.891, -0.208) 20.
    # felt: looking up where two arched tops meet (orange panel 1 | green panel 2), against the concrete soffit
    "Cam_FeltDetail": ((23.62, 27.9, 0.75), (23.62, 29.4, 1.6), 24, {}),
    # craft corner: large-format bench with its cupboard, sewing bench, SSW glass
    "Cam_Craft": ((28.6, 29.9, 1.6), (31.6, 27.7, 0.9), 20, {}),
    # sewing bench close-up: embroidery machine, threads, cutting mat (was pointing at the electronics drawers)
    "Cam_SewingDetail": ((30.2, 28.5, 1.25), (30.7, 27.35, 0.85), 35, {}),
    # electronics from the window corner: bank-wall counter, whiteboard, teaching table, tool library
    "Cam_Micro": ((21.9, 30.3, 1.65), (25.0, 33.6, 0.9), 20, {}),
    # workshop from the column: standing + sitting tables, print farm, mural portal, hand-tool wall
    "Cam_Workshop": ((27.9, 29.0, 1.65), (24.0, 22.0, 1.0), 18, {}),
    # inside the CNC room from the glass-side aisle: the ShopBot bed, boom and loading door
    "Cam_ShopBot": ((21.25, 21.35, 1.85), (23.0, 18.8, 0.85), 20, {}),
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
