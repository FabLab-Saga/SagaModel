"""Import a machine from one of the lab's teaching wikis (the WebGL part list behind the wiki figure, exported to JSON by
the wiki's own generator; see assets/wiki/README.md) as script-built geometry in a SagaModel Part.

The wiki describes every part as a primitive in centimetres (z up): box (min/max), prism (frame F = o, a, u, v; polygon
in (u, v); extruded s0..s1 along a), lathe (profile [s, r] revolved about F.a, radial u/v), tube (route + radius) and
lines. This module rebuilds them with the same tessellation rules as the wiki's gl-live.js, finer for photoreal
renders, in metres in the machine's local frame (wiki cm * 0.01); the caller places the Part.

    exec(open(HERE + "wiki_machine.py").read(), ns)
    p = ns["wiki_part"](Part, json_path, material_for, skip=re.compile(...), retarget={name: (dx, dy, dz)})

Wikis whose generator already emits triangles (Epilog: generator/gl/model.mjs build(), mm, per-group arrays + part
list) go through wiki_tri_part(Part, path, material_for, offsets={group: (dx, dy, dz) mm}).
"""
import json
import math
import re

import bmesh
from mathutils import Matrix, Vector

CM = 0.01


def _v(p):
    return Vector((p[0] * CM, p[1] * CM, p[2] * CM))


def _frame(F):
    return Vector(F["o"]) * CM, Vector(F["a"]).normalized(), Vector(F["u"]).normalized(), Vector(F["v"]).normalized()


def _box(p, m, e):
    x0, y0, z0 = e["min"]
    x1, y1, z1 = e["max"]
    small = min(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)) * CM
    p.box(m, x0 * CM, x1 * CM, y0 * CM, y1 * CM, z0 * CM, z1 * CM, bevel=min(0.0015, small * 0.2) if small > 0.002 else 0.0)


def _prism(p, m, e):
    o, a, u, v = _frame(e["F"])
    poly = e["poly"]
    area = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
    ring = poly if area >= 0 else list(reversed(poly))
    at = lambda s, q: o + a * (s * CM) + u * (q[0] * CM) + v * (q[1] * CM)
    bm = p.bm(m)
    lo = [bm.verts.new(at(e["s0"], q)) for q in ring]
    hi = [bm.verts.new(at(e["s1"], q)) for q in ring]
    n = len(ring)
    for i in range(n):
        j = (i + 1) % n
        try:
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
        except ValueError:
            pass
    for cap in (list(reversed(lo)), hi):
        try:
            bm.faces.new(cap)
        except ValueError:
            pass


def _lathe(p, m, e):
    o, a, u, v = _frame(e["F"])
    prof = e["profile"]
    rmax = max(r for _, r in prof) * CM
    steps = max(e.get("steps", 28), 24 if rmax < 0.01 else 40 if rmax < 0.06 else 64)
    mer = [(prof[0][0], 0.0)] + [tuple(q) for q in prof] + [(prof[-1][0], 0.0)]
    bm = p.bm(m)
    rings = []
    for s, r in mer:
        if r <= 0:
            rings.append([bm.verts.new(o + a * (s * CM))])
        else:
            rings.append([bm.verts.new(o + a * (s * CM) + (u * math.cos(2 * math.pi * i / steps) +
                                                             v * math.sin(2 * math.pi * i / steps)) * (r * CM))
                          for i in range(steps)])
    for A, B in zip(rings, rings[1:]):
        if len(A) == 1 and len(B) == 1:
            continue
        for i in range(steps):
            j = (i + 1) % steps
            try:
                if len(A) == 1:
                    bm.faces.new((A[0], B[i], B[j]))
                elif len(B) == 1:
                    bm.faces.new((A[i], B[0], A[j]))
                else:
                    bm.faces.new((A[i], B[i], B[j], A[j]))
            except ValueError:
                pass


def _tube(p, m, e, offset=None):
    pts = [_v(q) for q in e["route"]]
    if offset is not None:                                       # retarget the far end, blended along the length
        L = [0.0]
        for a_, b_ in zip(pts, pts[1:]):
            L.append(L[-1] + (b_ - a_).length)
        tot = L[-1] or 1.0
        pts = [q + offset * (0.5 - 0.5 * math.cos(math.pi * l / tot)) for q, l in zip(pts, L)]
    r = e["r"] * CM
    around = 24 if r > 0.02 else 16 if r > 0.008 else 10
    bm = p.bm(m)
    prev, u = None, None
    first = last = None
    for k, q in enumerate(pts):
        d = (pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]).normalized()
        if u is None:
            ref = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
            u = d.cross(ref).normalized()
        else:
            u = (u - d * u.dot(d)).normalized()
        w = d.cross(u)
        ring = [bm.verts.new(q + (u * math.cos(2 * math.pi * i / around) + w * math.sin(2 * math.pi * i / around)) * r)
                for i in range(around)]
        if prev:
            for i in range(around):
                j = (i + 1) % around
                try:
                    bm.faces.new((prev[i], prev[j], ring[j], ring[i]))
                except ValueError:
                    pass
        else:
            first = ring
        prev = ring
    last = prev
    for cap in (list(reversed(first)), last):
        try:
            bm.faces.new(cap)
        except ValueError:
            pass


def _lines(p, m, e):
    bm = p.bm(m)
    for a_, b_ in e["segments"]:
        a_, b_ = _v(a_), _v(b_)
        d = b_ - a_
        mtx = Matrix.Translation((a_ + b_) / 2) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4() @ \
            Matrix.Diagonal((0.0012, 0.0012, d.length, 1))
        bmesh.ops.create_cube(bm, size=1.0, matrix=mtx)


def wiki_part(Part, path, material_for, skip=None, retarget=None):
    """Part with every wiki mesh not matching `skip` (regex on the part name); material_for(mat_name, entry) -> Material.
    retarget: {part name: (dx, dy, dz) metres} shifts a tube's far end (blended along it)."""
    d = json.load(open(path))
    p = Part()
    n = 0
    for e in d["meshes"]:
        if skip and skip.search(e["name"]):
            continue
        m = material_for(e["mat"], e, d["mats"])
        k = e["kind"]
        if k == "box":
            _box(p, m, e)
        elif k == "prism":
            _prism(p, m, e)
        elif k == "lathe":
            _lathe(p, m, e)
        elif k == "tube":
            off = (retarget or {}).get(e["name"])
            _tube(p, m, e, Vector(off) if off else None)
        elif k == "lines":
            _lines(p, m, e)
        n += 1
    return p, n, d


def wiki_tri_part(Part, path, material_for, offsets=None, skip=None, scale=0.001, part_offsets=()):
    """Part from a triangle-soup wiki model (groups -> base64 float32 pos/attr; attr = part id, mat, smooth, 0).
    offsets: rest-pose translation per moving group, in the model's units (default: the export's `home`, if any).
    part_offsets: [(regex, (dx, dy, dz))] extra shift for matching parts (e.g. a controller moved to the other side).
    Vertices are welded per material."""
    import base64
    import struct
    d = json.load(open(path))
    p = Part()
    mats = d["mats"]
    names = [q["name"] for q in d["parts"]]
    used = set()
    home = {g: v["t"] for g, v in d.get("home", {}).items()}
    for g, G in d["groups"].items():
        off = Vector((offsets or {}).get(g, home.get(g, (0, 0, 0))))
        for block in (G, G["glass"]):
            n = block["n"]
            if not n:
                continue
            pos = struct.unpack(f"<{n * 3}f", base64.b64decode(block["pos"]))
            att = struct.unpack(f"<{n * 4}f", base64.b64decode(block["attr"]))
            for t in range(n // 3):
                pid = int(att[t * 12] + 0.5)
                if skip and skip.search(names[pid]):
                    continue
                po = next((Vector(o_) for rx, o_ in part_offsets if rx.search(names[pid])), Vector((0, 0, 0)))
                o2 = off + po
                mi = int(att[t * 12 + 1] + 0.5)
                m = material_for(mats[mi]["n"], mats[mi], names[pid])
                bm = p.bm(m)
                vs = [bm.verts.new(((pos[(t * 3 + k) * 3] + o2.x) * scale, (pos[(t * 3 + k) * 3 + 1] + o2.y) * scale,
                                    (pos[(t * 3 + k) * 3 + 2] + o2.z) * scale)) for k in range(3)]
                try:
                    bm.faces.new(vs)
                except ValueError:
                    pass
                used.add(m.name)
    for mname, (m, bm) in p.bms.items():
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=scale * 0.02)
    return p, d


GL_METAL = {"alu": 1.0, "steel": 1.0, "silver": 0.7, "tool": 1.0, "copper": 1.0, "plate": 0.6, "brass": 1.0}


def gl_material_factory(bpy, prefix, overrides=None, metal=None, glass_alpha=None):
    """material_for() for wiki_tri_part: Principled per wiki material (colour, spec -> roughness, alpha -> blended).
    overrides: {wiki mat name: bpy Material}; glass_alpha: {wiki mat name: alpha} to replace the wiki's."""
    metal = metal or GL_METAL

    def f(name, mt, part):
        if overrides and name in overrides:
            return overrides[name]
        key = f"{prefix}_{name}"
        if key in bpy.data.materials:
            return bpy.data.materials[key]
        m_ = bpy.data.materials.new(key)
        m_.use_nodes = True
        bs = next(n_ for n_ in m_.node_tree.nodes if n_.type == "BSDF_PRINCIPLED")
        c = [min(1.0, v) for v in mt["c"]]
        bs.inputs["Base Color"].default_value = (*c, 1)
        bs.inputs["Metallic"].default_value = metal.get(name, 0.0)
        bs.inputs["Roughness"].default_value = max(0.08, 0.7 - 0.45 * min(1.0, mt["s"]))
        a = (glass_alpha or {}).get(name, mt["a"])
        if a < 1:
            bs.inputs["Alpha"].default_value = a
            bs.inputs["Coat Weight"].default_value = 0.2
            if hasattr(m_, "surface_render_method"):
                m_.surface_render_method = "BLENDED"
        if name in ("led", "screen"):
            bs.inputs["Emission Color"].default_value = (*c, 1)
            bs.inputs["Emission Strength"].default_value = 1.2 if name == "led" else 0.6
        m_.diffuse_color = (*c, 1)
        return m_
    return f
