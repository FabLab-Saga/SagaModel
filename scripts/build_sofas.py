"""Upholstered sofas (Cleveland-style, light grey) replacing the box sofas in the Lounge.

Each part is its own subdivided, slightly inflated mesh so cushions read as soft volumes with
real seams. Re-runnable: deletes Sofa_* objects in the Lounge and rebuilds from the existing
sofa roots' placement (location + rotation are kept).
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

rng = random.Random(3)


def soft_box(name, col, parent, x0, x1, y0, y1, z0, z1, mat, puff=0.012, sag=0.0, levels=2):
    """Box -> subdivision surface (with creased-ish bevel) -> inflated along normals."""
    bm = bmesh.new()
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r["verts"]:
        v.co = Vector((x1 if v.co.x > 0 else x0, y1 if v.co.y > 0 else y0, z1 if v.co.z > 0 else z0))
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(0.03, (x1 - x0) / 6, (y1 - y0) / 6, (z1 - z0) / 6),
                    segments=2, affect="EDGES", profile=0.7)
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=3, use_grid_fill=True)
    cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
    hx, hy, hz = (x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2
    bm.normal_update()
    for v in bm.verts:                                   # pillow: push face centres out, keep edges
        fx = 1 - min(1, abs(v.co.x - cx) / hx) ** 2
        fy = 1 - min(1, abs(v.co.y - cy) / hy) ** 2
        fz = 1 - min(1, abs(v.co.z - cz) / hz) ** 2
        v.co += v.normal * puff * (fx * fy + fy * fz + fx * fz) / 1.5
        if sag and v.co.z > cz:                          # seat sag in the middle
            v.co.z -= sag * fx * fy
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    o.parent = parent
    sd = o.modifiers.new("Subd", "SUBSURF")
    sd.levels, sd.render_levels = 1, levels
    return o


def leg(name, col, parent, x, y, mat):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.016, radius2=0.022, depth=0.12,
                          matrix=Matrix.Translation((x, y, 0.06)))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    o.parent = parent


def sofa(root, L, d=0.86, h=0.81):
    col = root.users_collection[0]
    fab = bpy.data.materials["Sofa_LightGrey"]
    blk = bpy.data.materials["Foot_Black"]
    arm, base_z, seat_z = 0.17, 0.12, 0.42
    for x in (0.06, L - 0.06):
        for y in (0.07, d - 0.07):
            leg(f"{root.name}_Leg", col, root, x, y, blk)
    soft_box(f"{root.name}_Base", col, root, 0.0, L, 0.0, d, base_z, base_z + 0.17, fab, puff=0.004)
    for x0 in (0.0, L - arm):                                                    # arms
        soft_box(f"{root.name}_Arm", col, root, x0, x0 + arm, 0.0, d, base_z, 0.63, fab, puff=0.010)
    soft_box(f"{root.name}_Back", col, root, arm, L - arm, d - 0.18, d, base_z + 0.17, h - 0.02, fab, puff=0.008)
    n = 3 if L > 2.0 else 2
    cw = (L - 2 * arm) / n
    for i in range(n):
        x = arm + i * cw
        soft_box(f"{root.name}_Seat{i + 1}", col, root, x + 0.004, x + cw - 0.004, 0.0, d - 0.18,
                 base_z + 0.17, seat_z + rng.uniform(-0.006, 0.006), fab, puff=0.022, sag=0.012)
        soft_box(f"{root.name}_BackCushion{i + 1}", col, root, x + 0.01, x + cw - 0.01, d - 0.38, d - 0.17,
                 seat_z - 0.01, h + rng.uniform(-0.01, 0.01), fab, puff=0.03)


def run():
    lounge = bpy.data.collections["Lounge"]
    roots = [o for o in lounge.objects if o.type == "EMPTY" and o.name.startswith("Sofa_Cleveland")]
    for r in roots:
        L = 2.08 if "3" in r.name else 1.79
        for k in list(r.children):
            data = k.data
            bpy.data.objects.remove(k)
            if data and data.users == 0:
                bpy.data.meshes.remove(data)
        sofa(r, L)
    m = bpy.data.materials["Sofa_LightGrey"]
    mix = next((n for n in m.node_tree.nodes if n.type == "MIX"), None)
    if mix:                                                   # less white: real light-grey linen
        mix.inputs["B"].default_value = (0.42, 0.42, 0.40, 1)
        mix.inputs["Factor"].default_value = 0.75
    print("sofas rebuilt:", [r.name for r in roots])


run()
