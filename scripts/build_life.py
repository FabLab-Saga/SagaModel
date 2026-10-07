"""Signs of use: stools at the workbenches and work in progress on them. Re-runnable ("Life" collection).

Benches = colleague's Component_237631 group (7 units). Props: green self-healing cutting mats
(procedural grid), plywood/acrylic offcuts, laptops, small prints, steel rulers, pencils, a CC0
cordless drill (Poly Haven Drill_01) and a cardboard box (cardboard_box_01) - credits in
assets/polyhaven/CREDITS.md.
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = bpy.path.abspath("//scripts/")
lib = {}
exec(open(HERE + "profile_furniture.py").read(), lib)
MAT = lib["materials"]()
_c = open(HERE + "build_craft_spine.py").read()
craft = {}
exec(_c[:_c.index("\ndef build():")], craft)                     # stool(), Part, mats, bank helpers
Part, mat, lin = lib["Part"], lib["simple_mat"], lib["lin"]
rng = random.Random(21)


def cutting_mat():
    m = bpy.data.materials.get("CuttingMat") or bpy.data.materials.new("CuttingMat")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    out, b = N("ShaderNodeOutputMaterial"), N("ShaderNodeBsdfPrincipled")
    geo = N("ShaderNodeNewGeometry")
    sep = N("ShaderNodeSeparateXYZ")
    L(geo.outputs["Position"], sep.inputs["Vector"])
    lines = None
    for comp in ("X", "Y"):                                        # 1 cm grid lines, every 5th bolder
        mul = N("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 100.0
        L(sep.outputs[comp], mul.inputs[0])
        fr = N("ShaderNodeMath"); fr.operation = "FRACT"; L(mul.outputs[0], fr.inputs[0])
        lt = N("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = 0.06
        L(fr.outputs[0], lt.inputs[0])
        if lines is None:
            lines = lt
        else:
            mx = N("ShaderNodeMath"); mx.operation = "MAXIMUM"
            L(lines.outputs[0], mx.inputs[0]); L(lt.outputs[0], mx.inputs[1]); lines = mx
    mix = N("ShaderNodeMix"); mix.data_type = "RGBA"
    mix.inputs["A"].default_value = lin("#2F6B4F"); mix.inputs["B"].default_value = lin("#D8E3D8")
    L(lines.outputs[0], mix.inputs["Factor"])
    L(mix.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.8
    L(b.outputs["BSDF"], out.inputs["Surface"])
    m.diffuse_color = lin("#2F6B4F")
    return m


def import_lib(asset):
    root = bpy.data.objects.get("PH_" + asset)
    lib_col = bpy.data.collections["AssetLibrary"]
    if root is None:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=bpy.path.abspath(f"//assets/polyhaven/models/{asset}/{asset}.gltf"))
        new = [o for o in bpy.data.objects if o not in before]
        root = bpy.data.objects.new("PH_" + asset, None)
        lib_col.objects.link(root)
        for o in new:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            lib_col.objects.link(o)
            if o.parent is None:
                o.parent = root
    meshes = [o for o in root.children_recursive if o.type == "MESH"]
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return meshes, lo, hi


def instance(asset, col, name, x, y, z, rz, target=None):
    meshes, lo, hi = import_lib(asset)
    k = (target / (hi - lo).length) if target else 1.0
    holder = bpy.data.objects.new(name, None)
    col.objects.link(holder)
    holder.location, holder.rotation_euler, holder.scale = (x, y, z), (0, 0, rz), (k, k, k)
    c = (lo + hi) / 2
    for m in meshes:
        inst = bpy.data.objects.new(f"{name}_{m.name}", m.data)
        col.objects.link(inst)
        inst.parent = holder
        inst.matrix_basis = Matrix.Translation((-c.x, -c.y, -lo.z)) @ m.matrix_world


def bench_top(name):
    o = bpy.data.objects[name]
    pts = [k.matrix_world @ Vector(c) for k in o.children_recursive if k.type == "MESH" and not k.hide_render for c in k.bound_box]
    return (min(p.x for p in pts), max(p.x for p in pts), min(p.y for p in pts), max(p.y for p in pts), max(p.z for p in pts))


def build():
    scene = bpy.context.scene
    col = bpy.data.collections.get("Life") or bpy.data.collections.new("Life")
    if col.name not in scene.collection.children:
        scene.collection.children.link(col)
    for o in list(col.objects):
        data = o.data
        bpy.data.objects.remove(o)
        if isinstance(data, bpy.types.Mesh) and data.users == 0:
            bpy.data.meshes.remove(data)
    cm = cutting_mat()
    alu = bpy.data.materials.get("Mach_AluSatin") or mat("Mach_AluSatin", "#C3C7CB", 0.3, metal=1.0)
    laptop_body = mat("Laptop_Body", "#9EA2A6", 0.35, metal=0.8)
    screen = mat("Laptop_Screen", "#20242A", 0.1, emit=0.0)
    paper = mat("Paper", "#F4F2EC", 0.8)
    pencil = mat("Pencil", "#E8B21E", 0.5)
    acr = [mat("Acrylic_Clear", "#DDE8EE", 0.05), MAT["bins"][0], MAT["bins"][2]]
    ply = MAT["ply"]
    benches = sorted([o.name for o in bpy.data.objects["ROOT"].children if o.name.startswith("Component_237631")])
    for bi, bn in enumerate(benches):
        x0, x1, y0, y1, zt = bench_top(bn)
        long_x = (x1 - x0) > (y1 - y0)
        p = Part()
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        L, W = (x1 - x0, y1 - y0) if long_x else (y1 - y0, x1 - x0)

        def at(u, v):                                              # u along the long side, v across, from centre
            return (cx + u, cy + v) if long_x else (cx + v, cy + u)
        # cutting mat (A2) + offcuts + ruler + pencil
        u0 = rng.uniform(-0.2, 0.2)
        mu, mv = at(u0, rng.uniform(-0.1, 0.1))
        hw, hd = (0.30, 0.21) if long_x else (0.21, 0.30)
        p.box(cm, mu - hw, mu + hw, mv - hd, mv + hd, zt, zt + 0.003)
        for _ in range(rng.randint(2, 4)):
            ou, ov = at(rng.uniform(-L / 2 + 0.15, L / 2 - 0.15), rng.uniform(-W / 2 + 0.12, W / 2 - 0.12))
            a, b = rng.uniform(0.05, 0.22), rng.uniform(0.04, 0.16)
            t = rng.choice((0.003, 0.004, 0.006, 0.009))
            p.box(rng.choice([ply, ply] + acr), ou - a / 2, ou + a / 2, ov - b / 2, ov + b / 2, zt + 0.003, zt + 0.003 + t, bevel=0.0008)
        ru, rv = at(u0 + 0.05, -0.05)
        p.box(alu, ru - 0.25, ru + 0.25, rv - 0.015, rv + 0.015, zt + 0.003, zt + 0.0045) if long_x else \
            p.box(alu, ru - 0.015, ru + 0.015, rv - 0.25, rv + 0.25, zt + 0.003, zt + 0.0045)
        pu, pv = at(u0 - 0.15, 0.12)
        p.cyl(pencil, (pu - 0.08, pv, zt + 0.007), (pu + 0.08, pv + 0.02, zt + 0.007), 0.0035, seg=6)
        # laptop on every other bench, opened
        if bi % 2 == 0:
            lu, lv = at(rng.choice((-1, 1)) * (L / 2 - 0.25), 0.0)
            p.box(laptop_body, lu - 0.16, lu + 0.16, lv - 0.11, lv + 0.11, zt, zt + 0.012, bevel=0.003)
            lid = Part()
            lid.box(laptop_body, -0.16, 0.16, 0.0, 0.005, 0.0, 0.22, bevel=0.002)
            lid.box(screen, -0.15, 0.15, -0.0005, 0.0, 0.01, 0.21)
            facing = -math.pi / 2 if long_x else 0.0
            lid_obj = lid.emit(f"Laptop_{bi}", col, Vector((lu, lv, zt + 0.012)) +
                               Matrix.Rotation(facing, 4, "Z") @ Vector((0, 0.105, 0)), facing)
            lid_obj.rotation_euler.x = math.radians(-15)
        # a sheet of paper
        su, sv = at(rng.uniform(-0.3, 0.3), rng.uniform(-0.15, 0.15))
        p.box(paper, su - 0.105, su + 0.105, sv - 0.148, sv + 0.148, zt, zt + 0.0006)
        p.emit(f"BenchProps_{bi}", col, Vector((0, 0, 0)))
        # stools: two per long side
        for side in (-1, 1):
            for su_ in (-L / 4, L / 4):
                if rng.random() < 0.25:
                    continue                                       # not every seat taken / pushed in
                su2, sv2 = at(su_ + rng.uniform(-0.05, 0.05), side * (W / 2 + rng.uniform(0.12, 0.30)))
                craft["stool"](0.62).emit(f"Stool_{bi}_{side}_{int(su_ > 0)}", col,
                                          Vector((su2 - 0.18, sv2 - 0.18, 0)), rng.uniform(-0.15, 0.15))
    # tools: drill on two benches, a cardboard box on the floor by the craft zone
    for k, bn in enumerate(benches[:2]):
        x0, x1, y0, y1, zt = bench_top(bn)
        instance("Drill_01", col, f"Drill_{k}", x1 - 0.25, y0 + 0.2, zt, rng.uniform(0, 6.28), target=0.30)
    instance("cardboard_box_01", col, "CardboardBox_1", 24.6, 31.4, 0.0, 0.3, target=0.75)
    print("life built:", len(benches), "benches")


build()
