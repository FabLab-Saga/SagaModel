"""Exposed ceiling services: galvanised ducts, wire-mesh cable trays, sprinkler
mains + heads, round industrial pendants. Re-runnable: clears and rebuilds the
"Services" collection.

Run inside Blender (e.g. via the MCP: exec(open(path).read())).
Model frame: +Y runs along the building (ESE), +X across it (SSW); slab soffit 3.93 m.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

SOFFIT = 3.93
Y0, Y1 = 13.6, 42.2          # interior extent along the building
PENDANT_W = 180.0            # watts per pendant (Cycles point light)
COLUMNS = [(27.6, 30.2, 0.45), (27.6, 21.3, 0.45)]  # x, y, clearance radius


def lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c) + (1,)


# ---------------------------------------------------------------- materials
def material(name, build):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    build(m, m.node_tree)
    return m


def _out(nt, shader):
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(shader.outputs[0], o.inputs["Surface"])


def galvanised(m, nt):
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = lin("#B9BEC2")
    b.inputs["Metallic"].default_value = 1.0
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    spangle = nt.nodes.new("ShaderNodeTexVoronoi")      # zinc spangle
    spangle.inputs["Scale"].default_value = 60
    nt.links.new(geo.outputs["Position"], spangle.inputs["Vector"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = 0.28
    rr.inputs["To Max"].default_value = 0.48
    nt.links.new(spangle.outputs["Distance"], rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], b.inputs["Roughness"])
    _out(nt, b)
    m.diffuse_color = lin("#B9BEC2")


def enamel_black(m, nt):
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = lin("#1A1A1A")
    b.inputs["Roughness"].default_value = 0.3
    b.inputs["Coat Weight"].default_value = 0.4
    _out(nt, b)
    m.diffuse_color = lin("#1A1A1A")


def enamel_white(m, nt):
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = lin("#F3F1EC")
    b.inputs["Roughness"].default_value = 0.35
    _out(nt, b)
    m.diffuse_color = lin("#F3F1EC")


def bulb(m, nt):
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (1.0, 0.86, 0.68, 1)   # ~3000 K
    e.inputs["Strength"].default_value = 25.0
    _out(nt, e)
    m.diffuse_color = (1.0, 0.9, 0.7, 1)


def cable(m, nt):
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = lin("#111111")
    b.inputs["Roughness"].default_value = 0.5
    _out(nt, b)
    m.diffuse_color = lin("#111111")


# ---------------------------------------------------------------- geometry
def cyl(bm, a, b, r, seg=12, cap=True):
    a, b = Vector(a), Vector(b)
    d = b - a
    rot = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    mtx = Matrix.Translation((a + b) / 2) @ rot
    bmesh.ops.create_cone(bm, cap_ends=cap, segments=seg, radius1=r, radius2=r, depth=d.length, matrix=mtx)


def box(bm, lo, hi):
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r["verts"]:
        v.co = Vector([hi[i] if v.co[i] > 0 else lo[i] for i in range(3)])


def emit(name, bm, mat, col, smooth=False):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    return ob


def clear_of_columns(x, y, r):
    return all(math.hypot(x - cx, y - cy) > r + cr for cx, cy, cr in COLUMNS)


# ---------------------------------------------------------------- services
def duct(col, name, x, d, y0, y1, mat):
    r = d / 2
    zc = SOFFIT - 0.08 - r
    bm = bmesh.new()
    cyl(bm, (x, y0, zc), (x, y1, zc), r, seg=40)
    # spiral lock seams every 0.15 m (slightly proud rings read as the spiral)
    y = y0 + 0.075
    while y < y1:
        cyl(bm, (x, y, zc), (x, y + 0.006, zc), r + 0.003, seg=40)
        y += 0.15
    emit(name, bm, mat, col, smooth=True)
    # hangers: strap ring + rod every 2.4 m
    bm = bmesh.new()
    y = y0 + 0.6
    while y < y1:
        cyl(bm, (x, y, zc + r), (x, y, SOFFIT), 0.005, seg=6)
        cyl(bm, (x, y - 0.012, zc), (x, y + 0.012, zc), r + 0.006, seg=40, cap=False)
        y += 2.4
    emit(name + "_Hangers", bm, mat, col)


def cable_tray(col, name, x, y0, y1, mat, w=0.30, h=0.06, z=3.35):
    bm = bmesh.new()
    wr = 0.002
    xs = [x - w / 2 + i * w / 6 for i in range(7)]
    for xi in xs:                                            # longitudinal floor wires
        cyl(bm, (xi, y0, z), (xi, y1, z), wr, seg=5, cap=False)
    for side in (-1, 1):                                     # side wires + top edge
        for zz in (z + h / 2, z + h):
            cyl(bm, (x + side * w / 2, y0, zz), (x + side * w / 2, y1, zz), wr * 1.5 if zz == z + h else wr, seg=5, cap=False)
    y = y0
    while y <= y1:                                           # U-shaped cross wires every 0.1 m
        cyl(bm, (x - w / 2, y, z), (x + w / 2, y, z), wr, seg=5, cap=False)
        for side in (-1, 1):
            cyl(bm, (x + side * w / 2, y, z), (x + side * w / 2, y, z + h), wr, seg=5, cap=False)
        y += 0.1
    emit(name, bm, mat, col)
    bm = bmesh.new()                                         # trapeze hangers every 1.5 m
    y = y0 + 0.4
    while y < y1:
        box(bm, (x - w / 2 - 0.06, y - 0.02, z - 0.042), (x + w / 2 + 0.06, y + 0.02, z - 0.002))
        for side in (-1, 1):
            cyl(bm, (x + side * (w / 2 + 0.035), y, z - 0.042), (x + side * (w / 2 + 0.035), y, SOFFIT), 0.005, seg=6)
        y += 1.5
    emit(name + "_Hangers", bm, mat, col)


def sprinkler(col, name, x, y0, y1, mat, z=3.80, spacing=3.0):
    bm = bmesh.new()
    cyl(bm, (x, y0, z), (x, y1, z), 0.030, seg=16)
    y = y0 + 1.0
    while y < y1:
        cyl(bm, (x, y, z), (x, y, z - 0.10), 0.012, seg=10)            # drop
        cyl(bm, (x, y, z - 0.10), (x, y, z - 0.12), 0.010, seg=10)     # head body
        cyl(bm, (x, y, z - 0.125), (x, y, z - 0.128), 0.022, seg=16)   # deflector
        y += spacing
    y = y0 + 0.3
    while y < y1:
        cyl(bm, (x, y, z + 0.03), (x, y, SOFFIT), 0.004, seg=6)
        y += 3.0
    emit(name, bm, mat, col, smooth=True)


def pendants(col, mats, points, bottom=2.55, d=0.40):
    shell, inner, glow, wire = mats
    sh, inn, gl, wr = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
    r = d / 2
    for x, y in points:
        # dome: half-sphere shell, open at the bottom
        for target, rad in ((sh, r), (inn, r - 0.004)):
            res = bmesh.ops.create_uvsphere(target, u_segments=32, v_segments=16, radius=rad,
                                            matrix=Matrix.Translation((x, y, bottom)))
            target.verts.ensure_lookup_table()
            bmesh.ops.delete(target, geom=[v for v in res["verts"] if v.co.z < bottom - 1e-5], context="VERTS")
        cyl(sh, (x, y, bottom + r), (x, y, bottom + r + 0.09), 0.025, seg=16)        # neck
        bmesh.ops.create_uvsphere(gl, u_segments=16, v_segments=8, radius=0.055,
                                  matrix=Matrix.Translation((x, y, bottom + 0.09)))  # bulb
        cyl(wr, (x, y, bottom + r + 0.09), (x, y, SOFFIT), 0.003, seg=6)             # cable
        cyl(wr, (x, y, SOFFIT - 0.02), (x, y, SOFFIT), 0.045, seg=16)                # ceiling rose
    for p in inn.faces:                                       # inner shell faces inward
        p.normal_flip()
    light = bpy.data.lights.get("Pendant_Light") or bpy.data.lights.new("Pendant_Light", "POINT")
    light.energy = PENDANT_W
    light.color = (1.0, 0.80, 0.60)                      # ~3000 K
    light.shadow_soft_size = 0.04
    for i, (x, y) in enumerate(points):                   # real light at each bulb; the dome shades it upward
        lo = bpy.data.objects.new(f"Pendant_Light_{i + 1:02d}", light)
        lo.location = (x, y, bottom + 0.08)
        col.objects.link(lo)
    emit("Pendant_Shells", sh, shell, col, smooth=True)
    emit("Pendant_Inner", inn, inner, col, smooth=True)
    emit("Pendant_Bulbs", gl, glow, col, smooth=True)
    emit("Pendant_Cables", wr, wire, col)


def pendant_points():
    """2.4 m grid over open floor; skip tall furniture/walls below and the small rooms."""
    scene = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for x in (22.5, 24.6, 26.7, 29.9, 31.5):
        y = 17.9
        while y < 41.0:
            in_rooms = (x > 24.3 and y < 23.3) or (x > 29.4 and 19.6 < y < 27.1)
            if not in_rooms and clear_of_columns(x, y, 0.25):
                ok = True
                for dx, dy in ((0, 0), (0.25, 0), (-0.25, 0), (0, 0.25), (0, -0.25)):
                    hit, loc, *_ = scene.ray_cast(dg, Vector((x + dx, y + dy, 3.3)), Vector((0, 0, -1)))
                    if hit and loc.z > 1.2:
                        ok = False
                        break
                if ok:
                    pts.append((x, y))
            y += 2.4
    return pts


def build():
    scene = bpy.context.scene
    col = bpy.data.collections.get("Services") or bpy.data.collections.new("Services")
    if col.name not in scene.collection.children:
        scene.collection.children.link(col)
    for o in list(col.objects):
        data = o.data
        bpy.data.objects.remove(o)
        if isinstance(data, bpy.types.Mesh) and data.users == 0:
            bpy.data.meshes.remove(data)
    galv = material("Galvanised", galvanised)
    mats = (material("Enamel_Black", enamel_black), material("Enamel_White", enamel_white),
            material("Bulb_Warm", bulb), material("Cable_Black", cable))
    pts = pendant_points()                       # before adding services (rays must not hit them)
    duct(col, "Duct_Main_450", 25.9, 0.45, Y0, Y1, galv)
    duct(col, "Duct_Branch_300", 30.6, 0.30, 27.4, Y1, galv)
    cable_tray(col, "CableTray_A", 23.2, Y0, Y1, galv)
    cable_tray(col, "CableTray_B", 29.0, Y0, Y1, galv)
    for i, x in enumerate((22.0, 28.4, 31.7)):
        sprinkler(col, f"Sprinkler_{i + 1}", x, Y0, Y1, galv)
    pendants(col, mats, pts)
    return len(pts)


if __name__ == "__main__" or True:
    n = build()
    print("services built;", n, "pendants")
