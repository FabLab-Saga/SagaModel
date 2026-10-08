"""Parametric aluminium-profile furniture: black anodised 20x20 / 40x40 T-slot,
zinc corner brackets, levelling feet, birch-plywood boards.

A first cut of what the shelving add-on will do. Everything is built in a local
frame (x = length along the wall, y = depth with the FRONT at y = 0, z up) and
placed with Part.emit(name, collection, location, rot_z).

Exec this file inside Blender before the build scripts that use it.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

UNIT = 0.3048                      # Profile_2020/4040 meshes: corner origin, length along +Z = 0.3048


def lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c) + (1,)


def simple_mat(name, hexcol, rough=0.4, metal=0.0, coat=0.0, emit=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = lin(hexcol)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = lin(hexcol)
        b.inputs["Emission Strength"].default_value = emit
    m.diffuse_color = lin(hexcol)
    return m


def birch_ply():
    """Pale birch plywood face with soft grain, world-space so any board size works."""
    m = bpy.data.materials.get("Plywood_Birch")
    if m:
        return m
    m = bpy.data.materials.new("Plywood_Birch")
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 9.0, 9.0)        # grain runs along x (board length)
    nt.links.new(geo.outputs["Position"], mp.inputs["Vector"])
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = 3.0
    wave.inputs["Distortion"].default_value = 4.0
    wave.inputs["Detail"].default_value = 2.0
    nt.links.new(mp.outputs["Vector"], wave.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = lin("#D8BE94")
    ramp.color_ramp.elements[1].color = lin("#E8D4AE")
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.5
    b.inputs["Coat Weight"].default_value = 0.1
    m.diffuse_color = lin("#E0C9A2")
    return m


MAT = {}


def materials():
    MAT.update(
        profile=bpy.data.materials.get("Alu_Black_Anodized"),
        zinc=simple_mat("Zinc_Bracket", "#C7CACD", 0.3, metal=1.0),
        ply=birch_ply(),
        foot=simple_mat("Foot_Black", "#121212", 0.6),
        strip=simple_mat("PowerStrip_Black", "#1A1A1A", 0.4),
        led=simple_mat("PowerStrip_LED", "#FF3B2F", 0.3, emit=3.0),
    )
    MAT["bins"] = [simple_mat(f"Bin_{n}", h, 0.45) for n, h in (("Red", "#E03A3F"), ("Green", "#009967"), ("Blue", "#1245DE"),
                                                                  ("Orange", "#FFA13D"), ("Yellow", "#F2C200"), ("Pink", "#E099AB"))]
    return MAT


# ---------------------------------------------------------------- geometry collector
class Part:
    """Geometry per material in a local frame; emit() places it as one parent empty + one mesh per material."""

    def __init__(self):
        self.bms = {}

    def bm(self, m):
        if m.name not in self.bms:
            self.bms[m.name] = (m, bmesh.new())
        return self.bms[m.name][1]

    def box(self, m, x0, x1, y0, y1, z0, z1, bevel=0.0):
        bm = self.bm(m)
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r["verts"]:
            v.co = Vector((x1 if v.co.x > 0 else x0, y1 if v.co.y > 0 else y0, z1 if v.co.z > 0 else z0))
        if bevel:
            edges = list({e for v in r["verts"] for e in v.link_edges})
            bmesh.ops.bevel(bm, geom=edges, offset=bevel, segments=2, affect="EDGES")

    def cyl(self, m, a, b, r, seg=16):
        a, b = Vector(a), Vector(b)
        d = b - a
        mtx = Matrix.Translation((a + b) / 2) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
        bmesh.ops.create_cone(self.bm(m), cap_ends=True, segments=seg, radius1=r, radius2=r, depth=d.length, matrix=mtx)

    def profile(self, size, axis, x, y, z, length):
        """T-slot member: cross-section corner at (x, y, z), running `length` along `axis`."""
        src = bpy.data.meshes["Profile_2020" if size < 0.03 else "Profile_4040"]
        k = length / UNIT
        if axis == "z":
            f = lambda c: (x + c.x, y + c.y, z + c.z * k)
        elif axis == "x":
            f = lambda c: (x + c.z * k, y + c.x, z + c.y)
        else:
            f = lambda c: (x + c.x, y + c.z * k, z + c.y)
        bm = self.bm(MAT["profile"])
        vs = [bm.verts.new(f(v.co)) for v in src.vertices]
        for p in src.polygons:
            try:
                bm.faces.new([vs[i] for i in p.vertices])
            except ValueError:
                pass

    def emit(self, name, col, loc, rot_z=0.0):
        root = bpy.data.objects.new(name, None)
        col.objects.link(root)
        root.matrix_world = Matrix.Translation(loc) @ Matrix.Rotation(rot_z, 4, "Z")
        for mname, (m, bm) in self.bms.items():
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            me = bpy.data.meshes.new(f"{name}_{mname}")
            bm.to_mesh(me)
            for f in me.polygons:                           # auto-smooth: flat boxes, round cylinders
                f.use_smooth = True
            me.set_sharp_from_angle(angle=math.radians(30))
            bm.free()
            me.materials.append(m)
            o = bpy.data.objects.new(f"{name}_{mname}", me)
            col.objects.link(o)
            o.parent = root
        return root


FACE = {"-x": -math.pi / 2, "+x": math.pi / 2, "-y": 0.0, "+y": math.pi}   # local front (-y) faces this way


def placement(cx, cy, w, d, facing):
    """(location, rot_z) that centres a local w x d footprint at (cx, cy), front facing `facing`."""
    rot = FACE[facing]
    return Vector((cx, cy, 0)) + Matrix.Rotation(rot, 4, "Z") @ Vector((-w / 2, -d / 2, 0)), rot


def to_world(loc, rot, p):
    return Vector(loc) + Matrix.Rotation(rot, 4, "Z") @ Vector(p)


# ---------------------------------------------------------------- details
def bracket(part, s, x, y, z):
    """Die-cast corner bracket (cube of profile size s, slightly smaller)."""
    e = s * 0.9
    part.box(MAT["zinc"], x, x + e, y, y + e, z, z + e, bevel=0.0015)


def foot(part, cx, cy):
    part.cyl(MAT["zinc"], (cx, cy, 0.012), (cx, cy, 0.035), 0.006, seg=10)
    part.cyl(MAT["foot"], (cx, cy, 0.0), (cx, cy, 0.012), 0.022, seg=20)


def board(part, x0, x1, y0, y1, ztop, t=0.018):
    part.box(MAT["ply"], x0, x1, y0, y1, ztop - t, ztop, bevel=0.001)


def bin_box(part, m, x0, y0, z0, w=0.40, d=0.30, h=0.20, t=0.004):
    """Open storage bin."""
    part.box(m, x0, x0 + w, y0, y0 + d, z0, z0 + t)
    part.box(m, x0, x0 + w, y0, y0 + t, z0, z0 + h)
    part.box(m, x0, x0 + w, y0 + d - t, y0 + d, z0, z0 + h)
    part.box(m, x0, x0 + t, y0, y0 + d, z0, z0 + h)
    part.box(m, x0 + w - t, x0 + w, y0, y0 + d, z0, z0 + h)


# ---------------------------------------------------------------- units
def shelf_unit(bays, depth, height, levels, post=0.04, rail=0.02, feet_h=0.035, power=False, omit=()):
    """Wall shelving. bays: list of clear bay widths; levels: shelf-top heights.

    Uprights 40x40 at every bay boundary, front and back; 20x20 rails front/back
    and at the sides under every board; 40x40 frame at the top. Returns (part, slots)
    with slots[(bay, level)] = (x0, x1, y0, y1, ztop) of the board in local coords.
    omit: {(bay, level)} boards (and their rails) left out, e.g. a desk niche in a run.
    """
    p = Part()
    xs = [0.0]
    for w in bays:
        xs.append(xs[-1] + post + w)
    L = xs[-1] + post
    z0 = feet_h
    for x in xs:                                                       # uprights + feet
        for y in (0.0, depth - post):
            p.profile(post, "z", x, y, z0, height - z0)
            foot(p, x + post / 2, y + post / 2)
    slots = {}
    tops = list(levels) + [height]
    for li, zt in enumerate(tops):
        s = post if li in (0, len(tops) - 1) else rail                 # heavier frame at bottom and top
        zr = zt - (0.018 if li < len(levels) else 0.0) - s
        for bi in range(len(bays)):
            xa, xb = xs[bi] + post, xs[bi + 1]
            if (bi, li) in omit:
                continue
            for y in (0.0, depth - s):                                 # front/back rails
                p.profile(s, "x", xa, y, zr, xb - xa)
                bracket(p, s, xa, y + (s if y == 0 else -s * 0.9), zr)
                bracket(p, s, xb - s * 0.9, y + (s if y == 0 else -s * 0.9), zr)
            if li < len(levels):
                board(p, xa, xb, 0.002, depth - 0.002, zt)
                slots[(bi, li)] = (xa, xb, 0.0, depth, zt)
                if power:                                              # power strip on the back rail
                    p.box(MAT["strip"], xa + 0.05, xa + 0.65, depth - s - 0.045, depth - s - 0.005, zr - 0.04, zr)
                    p.box(MAT["led"], xa + 0.06, xa + 0.07, depth - s - 0.047, depth - s - 0.045, zr - 0.025, zr - 0.015)
        for x in xs:                                                   # side rails (along depth)
            p.profile(s, "y", x, post, zr, depth - 2 * post)
    return p, slots, L


def table_unit(length, depth, height, legs_x, top_t=0.025, lower=(0.14,), apron=0.04, feet_h=0.035):
    """Purpose-built work table: 40x40 legs at legs_x, 40x40 apron, plywood top, lower shelves."""
    p = Part()
    post = 0.04
    for x in legs_x:
        for y in (0.0, depth - post):
            p.profile(post, "z", x, y, feet_h, height - top_t - feet_h)
            foot(p, x + post / 2, y + post / 2)
    za = height - top_t - apron
    xs = sorted(legs_x)
    for xa, xb in zip(xs, xs[1:]):
        for y in (0.0, depth - apron):
            p.profile(apron, "x", xa + post, y, za, xb - xa - post)
            bracket(p, apron, xa + post, y + (apron if y == 0 else -apron * 0.9), za - apron * 0.9)
            bracket(p, apron, xb - apron * 0.9, y + (apron if y == 0 else -apron * 0.9), za - apron * 0.9)
        for zl in lower:                                               # lower shelves on 20x20 rails
            for y in (0.0, depth - 0.02):
                p.profile(0.02, "x", xa + post, y, zl - 0.018 - 0.02, xb - xa - post)
            board(p, xa + post, xb, 0.002, depth - 0.002, zl)
    for x in xs:
        p.profile(apron, "y", x, post, za, depth - 2 * post)
        for zl in lower:
            p.profile(0.02, "y", x + 0.01, post, zl - 0.018 - 0.02, depth - 2 * post)
    board(p, 0.0, xs[-1] + post, -0.01, depth + 0.01, height, t=top_t)  # top overhangs 1 cm front/back
    return p, (0.0, xs[-1] + post, 0.0, depth, height)
