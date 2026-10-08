"""Extra presentation cameras (re-runnable). Each camera gets 'shot_order', optional
'exposure_offset', 'show_ground' (outside views) and DOF settings.
Model frame: +X = SSW, +Y = ESE; main entrance at (32.5, 35.6); eye height 1.6 m.
"""
import bpy
from mathutils import Vector

# name, location, target, lens, exposure_offset, show_ground, fstop (None = no DOF)
CAMS = [
    ("Cam_WorkshopLong",  (22.6, 24.0, 1.65), (27.0, 37.0, 1.15), 18, 0.2, False, None),
    ("Cam_HighCorner",    (21.3, 23.6, 3.45), (28.5, 35.0, 0.2), 16, 0.3, False, None),
    ("Cam_BenchDetail",   (24.95, 27.55, 1.25), (23.90, 26.10, 0.80), 35, 0.4, False, 2.8),
    ("Cam_ShopBot",       (23.55, 22.55, 1.75), (21.9, 18.9, 0.9), 20, 0.2, False, None),
    ("Cam_CNCThroughGlass", (25.2, 25.6, 1.6), (22.6, 20.4, 1.1), 24, 0.3, False, None),
    ("Cam_LaserDetail",   (31.20, 21.30, 1.30), (32.20, 20.85, 0.85), 30, -0.2, False, 4.0),
    ("Cam_LoungeLow",     (28.75, 30.85, 1.05), (31.35, 31.95, 0.50), 20, 0.1, False, None),   # into the nook from its opening
    ("Cam_BookDetail",    (29.05, 35.30, 1.30), (28.22, 34.55, 1.15), 45, 0.4, False, 2.8),
    ("Cam_FeltDetail",    (22.40, 28.70, 1.70), (22.05, 29.75, 2.20), 30, 0.3, False, 4.0),
    ("Cam_MuralFront",    (27.00, 27.20, 1.60), (27.00, 21.84, 1.95), 22, 0.6, False, None),
    ("Cam_SewingDetail",  (22.10, 33.40, 1.35), (21.30, 32.70, 0.95), 35, 0.3, False, 2.8),
    ("Cam_HallEntrance",  (36.4, 37.0, 1.60), (32.5, 35.7, 1.95), 26, -0.6, True, None),   # from the hotel main hall (not outdoors)
]


def run():
    cams = bpy.data.collections["Cameras"]
    for i, (name, loc, tgt, lens, ev, ground, fstop) in enumerate(CAMS, start=10):
        c = bpy.data.objects.get(name) or bpy.data.objects.new(name, bpy.data.cameras.new(name))
        if c.name not in cams.objects:
            cams.objects.link(c)
        c.location = loc
        c.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        c.data.lens, c.data.sensor_width, c.data.clip_end = lens, 36, 400
        c.data.dof.use_dof = fstop is not None
        if fstop:
            c.data.dof.focus_distance = (Vector(tgt) - Vector(loc)).length
            c.data.dof.aperture_fstop = fstop
        c["exposure_offset"] = ev
        c["show_ground"] = ground
        c["shot_order"] = i
    print("cameras:", len(CAMS))


run()
