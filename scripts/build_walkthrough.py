"""Presentation walkthrough v1: keyframed shot cameras on one 30 fps timeline (RENDER.md, script v2).
Re-runnable inside Blender (rebuilds collection "Walkthrough"). Each shot = one camera "Walk_<NN>_<name>";
timeline markers bind the cameras, so rendering the scene frame range renders the whole film body.

Directing rules (presentation-video-production skill, references/cinematography.md):
- ONE motion per shot: a straight-line move (dolly / truck / pedestal or a straight diagonal) at CONSTANT speed
  (linear keys, no easing), with a FIXED view direction. No rotation while moving, no pans, no S-curves.
- Cameras are LEVEL (pitch 0, roll 0); up/down framing comes from lens shift (two-point perspective).
- Cuts land on bar lines of the music (Stairwell Harmony, 103.4 BPM -> 1 bar = 2.322 s).
Shot poses come from zone geometry (CLAUDE.md), NOT from the old Cam_* stills cameras.

SHOTS: (name, bars, title or None, eye_start, eye_end, look_target, lens). The look target only sets the
fixed yaw and the lens shift (from the target's height); it is not tracked.
"""
import math

import bpy
from mathutils import Vector

FPS = 30
BAR = 4 * 60 / 103.36            # s per bar
INTRO_BARS = 2                   # film starts with the intro card; Blender frame 1 = end of the intro
COL = "Walkthrough"
SENSOR = 36.0

SHOTS = [
    ("Hall", 3, "FAB LAB SAGA // Hagatorg 1",
     (42.6, 37.10, 1.65), (37.6, 37.10, 1.65), (34.44, 36.7, 1.85), 24),     # hall set (build_entrance_bay.py)
    ("Entrance", 2, None,
     (33.90, 37.00, 1.62), (31.90, 36.28, 1.62), (28.3, 34.95, 1.95), 22),   # just inside the corner-bay door
    ("Corridor", 2, None,
     (30.05, 33.30, 1.62), (30.05, 29.60, 1.62), (29.6, 22.0, 1.40), 22),
    ("Reveal", 3, None,
     (29.20, 29.30, 1.60), (29.20, 29.30, 2.85), (24.0, 25.0, 1.20), 20),
    ("Laser", 2, "FAB LAB SAGA // Geislaskeri",
     (30.45, 25.30, 1.50), (30.45, 23.00, 1.50), (32.3, 24.15, 1.00), 24),
    ("LaserDetail", 2, None,
     (30.85, 24.20, 1.35), (31.50, 23.80, 1.32), (32.2, 23.38, 1.05), 35),
    ("PrintFarm", 2, "FAB LAB SAGA // Þrívíddarprentari",
     (27.00, 25.30, 1.55), (27.00, 23.00, 1.55), (28.8, 24.15, 1.45), 22),
    ("CNCGlass", 2, "FAB LAB SAGA // Fræsivél",
     (22.90, 24.60, 1.60), (22.90, 22.50, 1.60), (22.9, 19.7, 1.10), 20),
    ("CNCRoom", 2, None,
     (22.70, 15.50, 1.90), (22.70, 17.40, 1.90), (22.9, 20.0, 1.00), 20),
    ("Electronics", 2, "FAB LAB SAGA // Rafeindaverkstæði",
     (24.70, 32.70, 1.50), (22.50, 32.70, 1.50), (24.70, 30.20, 1.05), 24),
    ("Craft", 2, "FAB LAB SAGA // Textílsvæði",
     (30.80, 30.20, 1.50), (30.80, 28.30, 1.50), (30.8, 27.00, 1.00), 22),
    ("ToolWall", 2, "FAB LAB SAGA // Verkfæri",
     (23.30, 24.00, 1.60), (23.30, 26.20, 1.60), (21.0, 24.00, 1.30), 24),
    ("Bank", 3, "Búnaðarbanki SFS",
     (33.60, 37.05, 1.60), (29.40, 37.05, 1.60), (27.8, 37.10, 1.30), 24),
    ("Lounge", 2, None,
     (28.45, 31.70, 1.05), (29.85, 31.70, 1.05), (32.3, 31.70, 0.60), 24),
    ("Closing", 3, None,
     (29.80, 29.20, 1.70), (30.40, 33.00, 2.75), (27.5, 22.0, 1.00), 18),
]


def level_pose(eye, tgt, lens):
    """Level camera looking toward tgt in plan; vertical aim via lens shift (clamped)."""
    e, t = Vector(eye), Vector(tgt)
    d = t - e
    yaw = math.atan2(d.y, d.x)
    pitch = math.atan2(d.z, d.xy.length)
    rot = (math.pi / 2, 0.0, yaw - math.pi / 2)                  # camera looks along local -Z
    shift = max(-0.3, min(0.3, lens * math.tan(pitch) / SENSOR))
    return rot, shift


def frame_at(bars):
    return round(bars * BAR * FPS)


def linearize(ob):
    """LINEAR interpolation on every key of the object's action (Blender 5 layered actions)."""
    act = ob.animation_data.action
    curves = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for bag in getattr(strip, "channelbags", []):
                curves.extend(bag.fcurves)
    if not curves and hasattr(act, "fcurves"):
        curves = list(act.fcurves)
    for fc in curves:
        for k in fc.keyframe_points:
            k.interpolation = "LINEAR"
    return len(curves)


def secret_door(fa, fb, angle=75.0):
    """Bank shot: the secret door in the birch-fin relief swings open into the bank (hinge at the WNW face of the
    wall, y 36.62 jamb; build_bank_walls.py). Eased (a real door accelerates/decelerates); closed outside the shot."""
    leaf = bpy.data.objects.get("SecretDoor_Leaf")
    if not leaf:
        return
    hinge = bpy.data.objects.get("SecretDoor_Hinge") or bpy.data.objects.new("SecretDoor_Hinge", None)
    if hinge.name not in bpy.data.collections["EquipmentBank"].objects:
        bpy.data.collections["EquipmentBank"].objects.link(hinge)
    hinge.animation_data_clear()
    hinge.location, hinge.rotation_euler = (27.495, 36.625, 0.0), (0.0, 0.0, 0.0)
    hinge.empty_display_size = 0.2
    bpy.context.view_layer.update()
    if leaf.parent != hinge:
        mw = leaf.matrix_world.copy()
        leaf.parent = hinge
        leaf.matrix_parent_inverse = hinge.matrix_world.inverted()
        leaf.matrix_world = mw
    for fr, a in ((fa, 0.0), (fb, angle)):
        hinge.rotation_euler.z = math.radians(a)
        hinge.keyframe_insert("rotation_euler", index=2, frame=fr)


def build():
    sc = bpy.context.scene
    col = bpy.data.collections.get(COL) or bpy.data.collections.new(COL)
    if col.name not in sc.collection.children:
        sc.collection.children.link(col)
    for o in list(col.objects):
        cam = o.data
        bpy.data.objects.remove(o)
        if cam and cam.users == 0:
            bpy.data.cameras.remove(cam)
    for m in [m for m in sc.timeline_markers if m.name.startswith("Walk_")]:
        sc.timeline_markers.remove(m)
    for a in [a for a in bpy.data.actions if a.name.startswith("Walk_") and a.users == 0]:
        bpy.data.actions.remove(a)

    sc.render.fps, sc.render.fps_base = FPS, 1.0
    b = 0
    for i, (name, bars, title, e0, e1, tgt, lens) in enumerate(SHOTS):
        f0, f1 = frame_at(b) + 1, frame_at(b + bars)
        cname = f"Walk_{i + 1:02d}_{name}"
        cam = bpy.data.cameras.new(cname)
        cam.clip_start, cam.lens = 0.05, lens
        ob = bpy.data.objects.new(cname, cam)
        col.objects.link(ob)
        rot, shift = level_pose(e0, tgt, lens)
        ob.rotation_euler, cam.shift_y = rot, shift
        secs = (f1 - f0 + 1) / FPS
        speed = (Vector(e1) - Vector(e0)).length / secs
        ob["title"], ob["frames"], ob["bars"], ob["speed_mps"] = title or "", (f0, f1), bars, round(speed, 2)
        for fr, e in ((f0, e0), (f1 + 1, e1)):                   # e1 one frame past the cut: constant speed
            ob.location = e
            ob.keyframe_insert("location", frame=fr)
        assert linearize(ob) == 3, cname
        m = sc.timeline_markers.new(cname, frame=f0)
        m.camera = ob
        print(f"{cname:22s} frames {f0:4d}-{f1:4d}  {secs:4.2f} s  {speed:4.2f} m/s  shift {shift:+.2f}")
        if name == "Bank":
            secret_door(f0 + 20, f1 - 30)
        b += bars
    sc.frame_start, sc.frame_end = 1, frame_at(b)
    sc.frame_set(1)                                                      # stills/peeks see the closed door
    sc.camera = col.objects[0]
    print(f"walkthrough v1: {len(SHOTS)} shots, {b} bars, frames 1-{sc.frame_end} ({sc.frame_end / FPS:.1f} s)"
          f" + intro {INTRO_BARS} bars")


build()
