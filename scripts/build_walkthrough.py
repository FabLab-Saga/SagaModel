"""Presentation walkthrough: keyframed shot cameras on one 30 fps timeline (RENDER.md, script v2).
Re-runnable inside Blender (rebuilds collection "Walkthrough"). Each shot = one camera "Walk_<NN>_<name>";
timeline markers bind the cameras, so rendering the scene frame range renders the whole film body
(0:04-1:25 of the script; intro/outro/titles are made outside Blender).

Shot poses are derived from zone geometry in CLAUDE.md, NOT from the old Cam_* stills cameras (many are stale).
KEYS: (t 0..1 within the shot, eye xyz, target xyz, lens mm). Interpolation: smooth (Bezier, auto-clamped).
Frame 1 = 0:04 of the film.
"""
import bpy
from mathutils import Vector

FPS = 30
COL = "Walkthrough"

# name, seconds, title (None = no title), keys
SHOTS = [
    ("Hall", 8, "FAB LAB SAGA // Hagatorg 1", [
        (0.0, (35.4, 37.0, 1.65), (32.6, 35.8, 1.75), 26),
        (1.0, (33.4, 35.75, 1.65), (32.0, 35.66, 1.55), 26)]),
    ("Spine1", 12, None, [
        (0.00, (33.2, 35.66, 1.62), (28.3, 35.0, 1.95), 22),   # at the door: TV + desk ahead
        (0.30, (31.6, 35.2, 1.62), (28.3, 34.9, 1.85), 22),
        (0.55, (30.2, 33.5, 1.62), (29.7, 30.0, 1.40), 22),    # between desk corner and the pit
        (0.80, (30.0, 30.6, 1.62), (28.8, 26.8, 1.30), 22),
        (1.00, (29.4, 28.4, 1.65), (25.5, 25.5, 1.10), 22)]),
    ("Reveal", 6, None, [
        (0.0, (28.6, 28.9, 1.70), (25.0, 26.0, 1.00), 20),
        (1.0, (28.8, 29.8, 3.35), (23.0, 23.5, 0.80), 18)]),
    ("Laser", 6, "FAB LAB SAGA // Geislaskeri", [
        (0.0, (30.6, 25.9, 1.50), (32.2, 24.2, 1.00), 24),
        (1.0, (30.6, 22.6, 1.50), (32.2, 20.9, 1.00), 24)]),
    ("PrintFarm", 5, "FAB LAB SAGA // Þrívíddarprentari", [
        (0.0, (27.95, 25.5, 1.50), (28.9, 24.9, 1.35), 24),
        (1.0, (27.95, 22.8, 1.50), (28.9, 22.4, 1.35), 24)]),
    ("CNC", 8, "FAB LAB SAGA // Fræsivél", [
        (0.0, (21.6, 24.2, 1.65), (22.8, 19.6, 1.10), 20),
        (1.0, (21.4, 21.2, 1.65), (22.9, 18.6, 1.10), 20)]),
    ("Electronics", 6, "FAB LAB SAGA // Rafeindaverkstæði", [
        (0.0, (24.0, 31.6, 1.40), (23.4, 30.4, 1.00), 28),
        (1.0, (22.2, 31.6, 1.40), (21.6, 30.4, 1.00), 28)]),
    ("Craft", 5, "FAB LAB SAGA // Textílsvæði", [
        (0.0, (29.4, 29.8, 1.55), (31.0, 27.4, 1.00), 24),
        (1.0, (30.4, 29.6, 1.50), (32.0, 28.6, 1.00), 24)]),
    ("ToolWall", 5, "FAB LAB SAGA // Verkfæri", [
        (0.0, (23.4, 27.2, 1.60), (21.0, 24.5, 1.30), 22),
        (1.0, (23.0, 25.8, 1.60), (21.2, 29.0, 1.50), 22)]),
    ("Bank", 7, "Búnaðarbanki SFS", [
        (0.0, (31.5, 36.4, 1.60), (27.8, 37.1, 1.30), 24),
        (1.0, (30.0, 36.9, 1.55), (27.8, 37.1, 1.30), 24)]),
    ("LoungeSpine2", 13, None, [              # lounge (no title) rising into the closing pull-back
        (0.00, (29.0, 31.7, 1.05), (32.3, 31.7, 0.60), 24),
        (0.50, (30.0, 31.7, 1.00), (32.3, 31.7, 0.60), 24),
        (1.00, (31.9, 34.4, 3.35), (24.0, 25.0, 0.80), 18)]),
]


def look(eye, tgt):
    return (Vector(tgt) - Vector(eye)).to_track_quat("-Z", "Y")


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

    sc.render.fps, sc.render.fps_base = FPS, 1.0
    f = 1
    for i, (name, secs, title, keys) in enumerate(SHOTS):
        n = round(secs * FPS)
        cname = f"Walk_{i + 1:02d}_{name}"
        cam = bpy.data.cameras.new(cname)
        cam.clip_start = 0.05
        ob = bpy.data.objects.new(cname, cam)
        col.objects.link(ob)
        ob.rotation_mode = "QUATERNION"
        ob["title"] = title or ""
        ob["frames"] = (f, f + n - 1)
        prev = None
        for t, eye, tgt, lens in keys:
            fr = f + round(t * (n - 1))
            q = look(eye, tgt)
            if prev is not None and prev.dot(q) < 0:      # keep quaternion keys on one hemisphere
                q.negate()
            prev = q
            ob.location, ob.rotation_quaternion, cam.lens = eye, q, lens
            ob.keyframe_insert("location", frame=fr)
            ob.keyframe_insert("rotation_quaternion", frame=fr)
            cam.keyframe_insert("lens", frame=fr)
        m = sc.timeline_markers.new(cname, frame=f)
        m.camera = ob
        f += n
    sc.frame_start, sc.frame_end = 1, f - 1
    sc.camera = col.objects[0]
    print(f"walkthrough: {len(SHOTS)} shots, frames 1-{f - 1} ({(f - 1) / FPS:.1f} s)")


build()
