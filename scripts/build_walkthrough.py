"""Presentation walkthrough v1: keyframed shot cameras on one 30 fps timeline (RENDER.md, script v2).
Re-runnable inside Blender (rebuilds collection "Walkthrough"). Each shot = one camera "Walk_<NN>_<name>";
timeline markers bind the cameras, so rendering the scene frame range renders the whole film body.

Directing rules (presentation-video-production skill, references/cinematography.md):
- ONE motion per shot: a straight-line move (dolly / truck / pedestal or a straight diagonal) at CONSTANT speed
  (linear keys, no easing), with a FIXED view direction. No rotation while moving, no pans, no S-curves.
- Cameras are LEVEL (pitch 0, roll 0); up/down framing comes from lens shift (two-point perspective).
- Cuts land on bar lines of the music (Stairwell Harmony, 103.4 BPM -> 1 bar = 2.322 s).
Shot poses come from zone geometry (AGENTS.md), NOT from the old Cam_* stills cameras.

SHOTS: (name, bars, title or None, eye_start, eye_end, look_target, lens). The look target only sets the
fixed yaw and the lens shift (from the target's height); it is not tracked.
"""
import math

import bpy
from mathutils import Vector

FPS = 30
BAR = 4 * 60 / 103.36            # s per bar
INTRO_BARS = 3                   # fframes title card; Blender frame 1 = end of the intro
COL = "Walkthrough"
SENSOR = 36.0

SHOTS = [
    ("Hall", 2, None,
     (42.0, 37.10, 1.65), (37.6, 37.10, 1.65), (34.44, 36.7, 1.85), 24),     # hall set (build_entrance_bay.py)
    ("Entrance", 2, None,
     (33.90, 37.00, 1.62), (31.90, 36.28, 1.62), (28.3, 34.95, 1.95), 22),   # just inside the corner-bay door
    ("Overview", 4, None, None, None, None, 30),                            # dollhouse cutaway orbit (OVERVIEW)
    ("Laser", 3, "FAB LAB SAGA // Geislaskerar",
     (31.00, 26.55, 1.60), (31.00, 25.05, 1.60), (30.9, 19.0, 1.05), 18),    # down the laser room: bench + Epilog
    ("PrintFarm", 2, "FAB LAB SAGA // Þrívíddarprentarar",
     (26.80, 24.90, 1.55), (26.80, 22.90, 1.55), (28.8, 24.90, 1.45), 22),     # square to the farm
    ("CNCGlass", 2, "FAB LAB SAGA // ShopBot Fræsir",
     (22.90, 25.40, 1.60), (22.90, 23.90, 1.60), (22.9, 19.7, 1.10), 20),
    ("CNCRoom", 2, None,
     (22.70, 16.40, 1.90), (22.70, 15.40, 1.90), (22.9, 20.0, 1.00), 20),     # pull-back from the ShopBot
    ("ToolWide", 2, "FAB LAB SAGA // Vinnurými",
     (25.15, 22.90, 1.70), (25.15, 24.30, 1.70), (21.2, 27.8, 1.10), 20),    # tool wall + cutters + felt from the aisle
    ("ElectronicsWide", 2, None,
     (27.25, 34.00, 1.70), (26.05, 34.00, 1.70), (21.4, 30.7, 1.00), 18),    # whole commons in context
    ("Electronics", 2, None,
     (24.70, 32.70, 1.50), (22.50, 32.70, 1.50), (24.70, 30.20, 1.05), 24),
    ("Craft", 2, "FAB LAB SAGA // Textílsvæði",
     (30.70, 29.10, 1.50), (30.70, 30.00, 1.50), (30.8, 27.00, 1.00), 20),     # pull-back from the wall bench
    ("Bank", 3, "Búnaðarbanki SFS",
     (33.60, 37.05, 1.60), (29.40, 37.05, 1.60), (27.8, 37.10, 1.30), 24),
    ("LoungeWide", 2, None,
     (29.00, 27.40, 1.65), (29.00, 28.70, 1.65), (31.4, 33.6, 0.90), 20),    # pit + desk + entrance in context
    ("Lounge", 2, None,
     (28.45, 31.70, 1.05), (29.85, 31.70, 1.05), (32.3, 31.70, 0.60), 24),
    ("Closing", 2, None,
     (29.70, 28.80, 1.75), (29.80, 31.30, 1.75), (27.3, 22.0, 1.10), 18),     # pull-back at eye height, no rise
]
# Dollhouse overview: camera orbits a pivot over the lab centre, looking down (a committed steep tilt), ceiling slab,
# services and fixtures hidden for that shot only (keyed hide_render + hide_viewport).
OVERVIEW = dict(pivot=(26.9, 27.2, 0.0), radius=24.0, height=21.0, az0=-14.0, az1=14.0)
CUTAWAY_HIDE = ("Ceiling_Slab", "Ceiling_SlabRing")
CUTAWAY_HIDE_COLS = ("Services",)


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


def secret_door(fa, fb, angle=-90.0):
    """Bank shot: the bookcase door swings open on its hinge (spine-side front corner; build_bank_walls.py puts the
    leaf origin on the hinge), outward into the room. Eased like a real heavy door; closed outside the shot."""
    leaf = bpy.data.objects.get("SecretDoor_Leaf")
    if not leaf:
        return
    leaf.animation_data_clear()
    for fr, a in ((fa, 0.0), (fb, angle)):
        leaf.rotation_euler.z = math.radians(a)
        leaf.keyframe_insert("rotation_euler", index=2, frame=fr)
    leaf.rotation_euler.z = 0.0


def cutaway_keys(f0, f1):
    """Hide slab/services/fixture bodies during the overview shot only (constant keys; lights keep shining)."""
    obs = [bpy.data.objects[n] for n in CUTAWAY_HIDE if n in bpy.data.objects]
    for c in CUTAWAY_HIDE_COLS:
        obs += list(bpy.data.collections[c].all_objects) if c in bpy.data.collections else []
    obs += [o for o in bpy.data.collections["Lighting"].objects if o.type == "MESH"]
    obs += [o for o in bpy.data.collections["Signs"].objects if o.name.endswith("_Cables")]
    obs += [o for o in bpy.data.collections["Hall"].objects if o.type == "MESH" and
            any(k in o.name for k in ("Ceiling", "Paint_White", "Concrete", "LED_Panel"))]
    for o in obs:
        if o.animation_data:
            o.animation_data_clear()
        for fr, hid in ((1, False), (f0, True), (f1 + 1, False)):
            o.hide_render = o.hide_viewport = hid
            o.keyframe_insert("hide_render", frame=fr)
            o.keyframe_insert("hide_viewport", frame=fr)
        o.hide_render = o.hide_viewport = False
    return len(obs)


def overview(ob, f0, f1):
    """Orbit (camera parented to a pivot empty) from az0 to az1 at constant angular speed; returns deg/s."""
    O = OVERVIEW
    piv = bpy.data.objects.get("Walk_OverviewPivot") or bpy.data.objects.new("Walk_OverviewPivot", None)
    if piv.name not in bpy.data.collections[COL].objects:
        bpy.data.collections[COL].objects.link(piv)
    piv.animation_data_clear()
    piv.location = O["pivot"]
    ob.parent = piv
    ob.location = (O["radius"], 0.0, O["height"])                      # +x = SSW side, looking back at the pivot
    d = Vector((0, 0, 0)) - Vector(ob.location)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    for fr, az in ((f0, O["az0"]), (f1 + 1, O["az1"])):
        piv.rotation_euler = (0.0, 0.0, math.radians(az))
        piv.keyframe_insert("rotation_euler", index=2, frame=fr)
    linearize(piv)
    n = cutaway_keys(f0, f1)
    print(f"  overview: {n} objects hidden during frames {f0}-{f1}")
    return (O["az1"] - O["az0"]) / ((f1 - f0 + 1) / FPS)


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
    piv = bpy.data.objects.get("Walk_OverviewPivot")
    if piv:
        bpy.data.objects.remove(piv)
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
        secs = (f1 - f0 + 1) / FPS
        if name == "Overview":
            speed, shift = overview(ob, f0, f1), 0.0
        else:
            rot, shift = level_pose(e0, tgt, lens)
            ob.rotation_euler, cam.shift_y = rot, shift
            speed = (Vector(e1) - Vector(e0)).length / secs
            for fr, e in ((f0, e0), (f1 + 1, e1)):               # e1 one frame past the cut: constant speed
                ob.location = e
                ob.keyframe_insert("location", frame=fr)
            assert linearize(ob) == 3, cname
        ob["title"], ob["frames"], ob["bars"], ob["speed_mps"] = title or "", (f0, f1), bars, round(speed, 2)
        m = sc.timeline_markers.new(cname, frame=f0)
        m.camera = ob
        print(f"{cname:22s} frames {f0:4d}-{f1:4d}  {secs:4.2f} s  {speed:4.2f} m/s  shift {shift:+.2f}")
        if name == "Bank":
            secret_door(f0 + 20, f1 - 30)
        b += bars
    sc.frame_start, sc.frame_end = 1, frame_at(b)
    sc.frame_set(1)                                                      # stills/peeks see the closed door
    sc.camera = col.objects[0]
    print(f"walkthrough v3: {len(SHOTS)} shots, {b} bars, frames 1-{sc.frame_end} ({sc.frame_end / FPS:.1f} s)"
          f" + intro {INTRO_BARS} bars")


build()
