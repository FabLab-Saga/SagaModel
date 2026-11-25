"""Blender side of the layout system (layout/README.md). Load inside Blender:

    L = {}; exec(open(bpy.path.abspath("//scripts/layout_blender.py")).read(), L)
    L["apply"]()                 # move every layout item to its layout/layout.yaml placement
    L["apply"]("PrintFarm")      # only items whose objects live in that collection (builders call this)
    L["poses"]()                 # {id: {"pos": [x, y], "z": z, "rot": deg, "size": [w, d, h]}} of the live scene

An item is one or more ROOT objects (`objects:` in layout.yaml; the first is the primary). Its pose is measured
from the geometry, not from origins: the footprint box of all its objects (and their children) in the primary's
rotation frame. pos = box centre on the floor plane, z = box bottom, rot = primary's rotation about +Z, size =
box w/d/h. apply() rigidly moves all of an item's objects (rotation about the box centre, then translation) so the
measured pose equals the yaml pose, and skips items already within 0.8 mm / 0.06 deg, so applying an unchanged
layout leaves the scene bit-identical. Builders build at their own coordinates and call apply() last.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

ROOT = os.environ.get("SAGA_ROOT") or bpy.path.abspath("//")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import layout_io  # noqa: E402

LAYOUT = os.path.join(ROOT, "layout", "layout.yaml")
EPS_POS, EPS_ROT = 0.0008, 0.06


def _angle(m):
    return math.atan2(m[1][0], m[0][0])


def _norm_deg(a):
    a = (a + 180.0) % 360.0 - 180.0
    return 180.0 if abs(a + 180.0) < 1e-9 else a


def _tree(o):
    yield o
    for c in o.children:
        yield from _tree(c)


def frame_of(o):
    m = o.matrix_world
    return Matrix.Translation(m.translation) @ Matrix.Rotation(_angle(m), 4, "Z")


def measure(objs):
    """Pose of a group of root objects (see module doc). Returns None if nothing has geometry."""
    F = frame_of(objs[0])
    Fi = F.inverted()
    lo, hi = [1e9] * 3, [-1e9] * 3
    for root in objs:
        for o in _tree(root):
            if o.type not in {"MESH", "CURVE", "FONT", "SURFACE", "META"}:
                continue
            if o.display_type in {"BOUNDS", "WIRE"} or o.hide_render:
                continue                                            # boolean cutters, per-shot hidden helpers
            mw = Fi @ o.matrix_world
            for c in o.bound_box:
                p = mw @ Vector(c)
                for i in range(3):
                    lo[i] = min(lo[i], p[i]); hi[i] = max(hi[i], p[i])
    if lo[0] > hi[0]:
        return None
    anchor = F @ Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]))
    return {"pos": [anchor.x, anchor.y], "z": anchor.z, "rot": _norm_deg(math.degrees(_angle(F))),
            "size": [hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]], "_anchor": anchor}


def load(path=LAYOUT):
    return layout_io.load(path)


def resolve(item):
    objs = [bpy.data.objects.get(n) for n in item.get("objects") or []]
    return [o for o in objs if o is not None]


def poses(path=LAYOUT, data=None):
    data = data or load(path)
    out = {}
    for it in data["items"]:
        objs = resolve(it)
        m = measure(objs) if objs else None
        if m is None:
            out[it["id"]] = {"missing": True}
            continue
        m.pop("_anchor")
        out[it["id"]] = {k: (round(v, 4) if isinstance(v, float) else [round(x, 4) for x in v]) for k, v in m.items()}
    return out


def apply(collection=None, path=LAYOUT, data=None, verbose=True):
    data = data or load(path)
    col = bpy.data.collections.get(collection) if collection else None
    moved, missing = [], []
    for it in data["items"]:
        objs = resolve(it)
        if not objs:
            missing.append(it["id"]); continue
        if col is not None and objs[0].name not in col.all_objects:
            continue
        cur = measure(objs)
        if cur is None:
            continue
        tx, ty = it["pos"]
        tz = float(it.get("z", cur["z"]))
        d_rot = _norm_deg(float(it.get("rot", cur["rot"])) - cur["rot"])
        dp = math.hypot(tx - cur["pos"][0], ty - cur["pos"][1])
        if dp < EPS_POS and abs(tz - cur["z"]) < EPS_POS and abs(d_rot) < EPS_ROT:
            continue
        a = cur["_anchor"]
        D = Matrix.Translation(Vector((tx, ty, tz))) @ Matrix.Rotation(math.radians(d_rot), 4, "Z") \
            @ Matrix.Translation(-a)
        for o in objs:
            o.matrix_world = D @ o.matrix_world
        moved.append((it["id"], round(dp, 3), round(d_rot, 1)))
    if verbose:
        print("layout: %d item(s) moved%s%s" % (len(moved), (": " + ", ".join(m[0] for m in moved[:12])) if moved else "",
              ("; missing objects for " + ", ".join(missing[:12])) if missing and col is None else ""))
    return moved


# ---------------------------------------------------------------- plan slice (room.json walls)
def slice_segments(objs, z):
    """Plan section at height z: list of ((x1, y1), (x2, y2)) from the evaluated meshes (booleans applied)."""
    dg = bpy.context.evaluated_depsgraph_get()
    segs = []
    for o in objs:
        oe = o.evaluated_get(dg)
        try:
            me = oe.to_mesh()
        except RuntimeError:
            continue
        if me is None:
            continue
        mw = oe.matrix_world
        vs = [mw @ v.co for v in me.vertices]
        if not vs or min(v.z for v in vs) > z or max(v.z for v in vs) < z:
            oe.to_mesh_clear(); continue
        me.calc_loop_triangles()
        for t in me.loop_triangles:
            p = [vs[i] for i in t.vertices]
            pts = []
            for i in range(3):
                a, b = p[i], p[(i + 1) % 3]
                if (a.z - z) * (b.z - z) < 0:
                    f = (z - a.z) / (b.z - a.z)
                    pts.append((a.x + f * (b.x - a.x), a.y + f * (b.y - a.y)))
            if len(pts) == 2 and math.dist(pts[0], pts[1]) > 1e-4:
                segs.append((pts[0], pts[1]))
        oe.to_mesh_clear()
    return segs


def merge_segments(segs, ang_step=0.5, off_step=0.004, gap=0.01):
    """Merge collinear overlapping segments: group by direction (deg mod 180) and normal offset."""
    groups = {}
    for (a, b) in segs:
        dx, dy = b[0] - a[0], b[1] - a[1]
        th = math.degrees(math.atan2(dy, dx)) % 180.0
        k = round(th / ang_step) % int(180 / ang_step)
        t = math.radians(k * ang_step)
        ux, uy = math.cos(t), math.sin(t)
        off = -uy * a[0] + ux * a[1]
        key = (k, round(off / off_step))
        s1, s2 = sorted((ux * a[0] + uy * a[1], ux * b[0] + uy * b[1]))
        groups.setdefault(key, []).append((s1, s2))
    out = []
    for (k, ko), iv in groups.items():
        t = math.radians(k * ang_step); ux, uy = math.cos(t), math.sin(t); off = ko * off_step
        iv.sort()
        cs, ce = iv[0]
        for s1, s2 in iv[1:] + [(1e9, 1e9)]:
            if s1 <= ce + gap:
                ce = max(ce, s2)
            else:
                if ce - cs > 0.02:
                    out.append(((ux * cs - uy * off, uy * cs + ux * off), (ux * ce - uy * off, uy * ce + ux * off)))
                cs, ce = s1, s2
    return out
