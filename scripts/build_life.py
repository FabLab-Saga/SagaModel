"""Signs of use: work in progress on the work tables. Re-runnable ("Life" collection).

Benches = the four WorkTable_* of build_worktables.py (run that first; it also builds the chairs). Props: green self-healing cutting mats
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
    bpy.context.view_layer.update()                                # fresh emits: children's matrix_world not evaluated yet
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
    benches = sorted(o.name for o in bpy.data.collections["WorkTables"].objects if o.name.startswith("WorkTable_")
                     and o.parent is None)                         # build_worktables.py (seats are built there)
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
    # tools: drill on two benches, a cardboard box on the floor by the craft zone
    for k, bn in enumerate(benches[:2]):
        x0, x1, y0, y1, zt = bench_top(bn)
        instance("Drill_01", col, f"Drill_{k}", x1 - 0.25, y0 + 0.2, zt, rng.uniform(0, 6.28), target=0.30)
    instance("cardboard_box_01", col, "CardboardBox_1", 27.30, 31.75, 0.0, 0.3, target=0.75)
    print("life built:", len(benches), "benches")


build()


def laser_room_life():
    """CO2 extinguisher by the door, sheet stock leaning on the partition, filter unit by the Epilog."""
    col = bpy.data.collections["Life"]
    red = mat("Extinguisher_Red", "#B3141B", 0.35, coat=0.6)
    blk = mat("Extinguisher_Black", "#111111", 0.5)
    p = Part()
    ex, ey = 29.80, 26.55                                          # inside the laser room by the door
    p.cyl(red, (ex, ey, 0.30), (ex, ey, 0.92), 0.075, seg=32)
    p.cyl(blk, (ex, ey, 0.92), (ex, ey, 1.00), 0.03, seg=16)       # valve
    p.cyl(blk, (ex, ey + 0.03, 0.97), (ex + 0.0, ey + 0.30, 0.55), 0.012, seg=10)  # horn hose
    p.box(blk, ex - 0.10, ex - 0.07, ey - 0.06, ey + 0.06, 0.70, 0.95)            # wall bracket
    # sheet stock leaning against the NNE partition (plywood + acrylic)
    sx = 29.72
    for i, m in enumerate([MAT["ply"], MAT["ply"], MAT["ply"], bpy.data.materials.get("Acrylic_Clear") or MAT["ply"], MAT["ply"]]):
        lean = 0.10 + i * 0.012
        bm = p.bm(m)
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r["verts"]:
            top = v.co.z > 0
            v.co = Vector((sx + (0.0 if top else lean) + i * 0.012 + (0.006 if v.co.x > 0 else 0.0),
                           23.40 + (1.22 if v.co.y > 0 else 0.0), 2.40 if top else 0.0))
    # fume filter unit next to the Epilog
    gry = bpy.data.materials.get("Mach_Grey")
    p.box(gry, 29.72, 30.27, 22.10, 22.60, 0.0, 0.85, bevel=0.012)
    p.box(blk, 29.80, 30.20, 22.098, 22.10, 0.55, 0.78)
    p.emit("LaserRoom_Life", col, Vector((0, 0, 0)))


# laser_room_life() retired: the laser room (incl. extinguishers) is built by build_laser_room.py


def wall_details():
    """Power sockets above the benches/counters, switches by doors, exit sign over the entrance."""
    col = bpy.data.collections["Life"]
    white = mat("Fitting_White", "#F2F1EE", 0.35)
    grey = mat("Fitting_Grey", "#9A9C9E", 0.4)
    exitg = mat("Exit_Green", "#1E9E52", 0.3, emit=2.0)
    p = Part()

    def socket(x, y, z, nx, ny, double=True):
        w = 0.155 if double else 0.085
        if nx:                                                     # on a wall facing +-x
            p.box(white, x, x + 0.012 * nx, y - w / 2, y + w / 2, z - 0.043, z + 0.043, bevel=0.003)
            for dy in ((-0.035, 0.035) if double else (0.0,)):
                p.cyl(grey, (x + 0.012 * nx, y + dy, z), (x + 0.0135 * nx, y + dy, z), 0.019, seg=20)
        else:
            p.box(white, x - w / 2, x + w / 2, y, y + 0.012 * ny, z - 0.043, z + 0.043, bevel=0.003)
            for dx in ((-0.035, 0.035) if double else (0.0,)):
                p.cyl(grey, (x + dx, y + 0.012 * ny, z), (x + dx, y + 0.0135 * ny, z), 0.019, seg=20)
    # mural wall (faces +y at 21.84): sockets either side of the sink and door, switch by the door
    for x in (25.35, 27.45, 28.45):
        socket(x, 21.845, 1.10, 0, 1)
    socket(25.85, 21.845, 1.20, 0, 1, double=False)
    # laser-room partition, workshop side (faces -x at 29.52): sockets for the print farm
    for y in (22.2, 24.9):
        socket(29.515, y, 0.30, -1, 0)
    # (the exit sign above the entrance door is built by build_entrance_bay.py: the door moved to the corner bay)
    p.emit("Wall_Details", col, Vector((0, 0, 0)))


wall_details()

# Placements come from layout/layout.yaml (layout/README.md): built at this builder's coordinates, then moved there.
_lay = {}
exec(open(bpy.path.abspath("//scripts/layout_blender.py")).read(), _lay)
_lay["apply"]()
