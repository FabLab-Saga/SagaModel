"""Lighting: office-style suspended linear LED arrays + a few angled ceiling spotlights. Re-runnable
(collection "Lighting"). Replaces the round enamel pendants (retired 2026-10-08 at the user's request).

Linear fixtures: slim black aluminium profile with an opal diffuser, 1.5 m long, hung on two cables so the
bottom sits at 2.95 m (above the 2.42 m shelving, the 2.80 m bank walls and the CNC boom), in rows along the
building (+y). Row x positions dodge the services in build_services.py (sprinkler mains x 22.0/28.4/31.7, cable
trays x 23.2/29.0, main duct x 25.9, branch duct x 30.6) and the felt tops at y 29.3-30.4. Each fixture = a
rectangular AREA light pointing down + an emissive diffuser strip.
Spots: track-style cans on short stems, angled at the mural, felt wall, lounge nook and demo shelves
(the art relief has its own Art_Spot in build_demo.py).
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

SOFFIT, BOTTOM = 3.93, 2.95
FIX_L, FIX_W, FIX_H = 1.50, 0.06, 0.06
PITCH = 2.10                                    # fixture centres along a row
LUMEN_W = 42.0                                  # area-light watts per fixture
SPOT_W = 160.0

# (x, y0, y1): row axis and extent (fixture centres are fitted inside)
ROWS = [
    (23.65, 15.6, 21.4), (25.00, 17.0, 19.1),                       # CNC room (clear of the dust boom) + ex-WC bay (not over the board rack)
    (22.30, 22.3, 29.2), (24.50, 22.3, 29.2), (26.80, 22.2, 29.2), (28.55, 22.2, 29.2),   # workshop / benches
    (22.30, 30.5, 34.1), (24.50, 30.5, 34.1), (26.80, 30.5, 34.1),                        # electronics commons
    (22.30, 34.6, 38.0), (24.50, 34.6, 38.0), (26.80, 34.6, 38.0),                        # equipment bank
    (31.10, 20.4, 26.7),                                            # laser room
    (29.80, 27.3, 37.9), (31.45, 27.3, 34.6),                       # lounge / textile / demo / entrance
    (33.45, 35.2, 38.0),                                            # entrance corner bay (build_entrance_bay.py)
]
# (name, ceiling point, aim point)
SPOTS = [
    ("Spot_Mural_A", (25.6, 24.2, 3.80), (25.4, 21.85, 2.2)),
    ("Spot_Mural_B", (28.0, 24.2, 3.80), (28.2, 21.85, 2.2)),
    ("Spot_Felt_A", (22.9, 27.4, 3.80), (22.6, 29.6, 1.9)),
    ("Spot_Felt_B", (25.6, 27.4, 3.80), (25.9, 29.6, 1.9)),
    ("Spot_Nook", (29.9, 29.9, 3.80), (30.95, 31.6, 0.45)),
    ("Spot_Demo", (29.0, 35.6, 3.80), (29.6, 37.9, 1.2)),
]


def lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c) + (1,)


def mats():
    body = bpy.data.materials.get("Fixture_Black") or bpy.data.materials.new("Fixture_Black")
    body.use_nodes = True
    b = next(n for n in body.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = lin("#18191A")
    b.inputs["Roughness"].default_value = 0.4
    b.inputs["Metallic"].default_value = 0.6
    opal = bpy.data.materials.get("Fixture_Opal") or bpy.data.materials.new("Fixture_Opal")
    opal.use_nodes = True
    nt = opal.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (1.0, 0.95, 0.88, 1)
    e.inputs["Strength"].default_value = 3.0
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], o.inputs["Surface"])
    cable = bpy.data.materials.get("Cable_Black") or bpy.data.materials.new("Cable_Black")
    return body, opal, cable


def box(bm, x0, x1, y0, y1, z0, z1):
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r["verts"]:
        v.co = Vector((x1 if v.co.x > 0 else x0, y1 if v.co.y > 0 else y0, z1 if v.co.z > 0 else z0))


def cyl(bm, a, b, r, seg=12):
    a, b = Vector(a), Vector(b)
    d = b - a
    mtx = Matrix.Translation((a + b) / 2) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=d.length, matrix=mtx)


def emit(col, name, parts):
    for mname, (m, bm) in parts.items():
        me = bpy.data.meshes.new(f"{name}_{mname}")
        bm.to_mesh(me)
        bm.free()
        for f in me.polygons:
            f.use_smooth = True
        me.set_sharp_from_angle(angle=math.radians(30))
        me.materials.append(m)
        col.objects.link(bpy.data.objects.new(f"{name}_{mname}", me))


def build():
    scene = bpy.context.scene
    col = bpy.data.collections.get("Lighting") or bpy.data.collections.new("Lighting")
    if col.name not in scene.collection.children:
        scene.collection.children.link(col)
    for o in list(col.objects):
        data = o.data
        bpy.data.objects.remove(o)
        if isinstance(data, bpy.types.Mesh) and data.users == 0:
            bpy.data.meshes.remove(data)
    body, opal, cable = mats()
    parts = {"Body": (body, bmesh.new()), "Opal": (opal, bmesh.new()), "Cable": (cable, bmesh.new())}
    ld = bpy.data.lights.get("Linear_LED") or bpy.data.lights.new("Linear_LED", "AREA")
    ld.shape, ld.size, ld.size_y = "RECTANGLE", FIX_W - 0.01, FIX_L - 0.04
    ld.energy, ld.color = LUMEN_W, (1.0, 0.95, 0.88)
    ld.spread = math.radians(110)
    n = 0
    for x, y0, y1 in ROWS:
        k = max(1, int((y1 - y0 - FIX_L) / PITCH) + 1)
        span = (k - 1) * PITCH
        for i in range(k):
            yc = (y0 + y1) / 2 - span / 2 + i * PITCH
            ya, yb = yc - FIX_L / 2, yc + FIX_L / 2
            box(parts["Body"][1], x - FIX_W / 2, x + FIX_W / 2, ya, yb, BOTTOM + 0.004, BOTTOM + FIX_H)
            box(parts["Opal"][1], x - FIX_W / 2 + 0.004, x + FIX_W / 2 - 0.004, ya + 0.004, yb - 0.004, BOTTOM, BOTTOM + 0.004)
            for yy in (ya + 0.15, yb - 0.15):
                cyl(parts["Cable"][1], (x, yy, BOTTOM + FIX_H), (x, yy, SOFFIT), 0.0012, seg=6)
                cyl(parts["Body"][1], (x, yy, SOFFIT - 0.012), (x, yy, SOFFIT), 0.025, seg=16)     # ceiling cup
            lo = bpy.data.objects.new(f"LED_{n:02d}", ld)
            lo.location = (x, yc, BOTTOM - 0.002)
            col.objects.link(lo)
            n += 1
    sd = bpy.data.lights.get("Track_Spot") or bpy.data.lights.new("Track_Spot", "SPOT")
    sd.energy, sd.spot_size, sd.spot_blend, sd.shadow_soft_size = SPOT_W, math.radians(38), 0.45, 0.02
    sd.color = (1.0, 0.90, 0.78)
    for name, top, aim in SPOTS:
        top, aim = Vector(top), Vector(aim)
        d = (aim - top).normalized()
        cyl(parts["Body"][1], (top.x, top.y, SOFFIT), (top.x, top.y, top.z + 0.03), 0.006, seg=8)          # stem
        cyl(parts["Body"][1], (top.x, top.y, SOFFIT - 0.01), (top.x, top.y, SOFFIT), 0.03, seg=16)
        can0, can1 = top + d * 0.02, top + d * 0.15
        cyl(parts["Body"][1], tuple(can0), tuple(can1), 0.038, seg=20)
        lo = bpy.data.objects.new(name, sd)
        lo.matrix_world = Matrix.Translation(can1 + d * 0.005) @ d.to_track_quat("-Z", "Y").to_matrix().to_4x4()
        col.objects.link(lo)
    emit(col, "Lighting", parts)
    print("lighting built: %d linear fixtures, %d spots" % (n, len(SPOTS)))


build()
