"""Signs of use: work in progress on the work tables. Re-runnable ("Life" collection).

Benches = the four WorkTable_* of build_worktables.py (run that first; it also builds the chairs). Props: green self-healing cutting mats
(procedural grid), plywood/acrylic offcuts, laptops, small prints, steel rulers, pencils. All script-built
(the Poly Haven drill + cardboard box were removed 2026-11-25, Magnús: only our own models).
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


def bench_top(name):
    bpy.context.view_layer.update()                                # fresh emits: children's matrix_world not evaluated yet
    o = bpy.data.objects[name]
    pts = [k.matrix_world @ Vector(c) for k in o.children_recursive if k.type == "MESH" and not k.hide_render for c in k.bound_box]
    return (min(p.x for p in pts), max(p.x for p in pts), min(p.y for p in pts), max(p.y for p in pts), max(p.z for p in pts))


def screen_mat(name, img):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    out, b = N("ShaderNodeOutputMaterial"), N("ShaderNodeBsdfPrincipled")
    t = N("ShaderNodeTexImage")
    t.image = bpy.data.images.load(bpy.path.abspath(f"//assets/screens/{img}"), check_existing=True)
    L(N("ShaderNodeTexCoord").outputs["UV"], t.inputs["Vector"])
    b.inputs["Base Color"].default_value = (0.01, 0.01, 0.012, 1)
    b.inputs["Roughness"].default_value = 0.15
    L(t.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 1.6
    L(b.outputs["BSDF"], out.inputs["Surface"])
    return m


def laptop(col, p, name, x, y, z, yaw, body, screen=None):
    """Laptop with its user on local -y; yaw turns that side to the user. screen=None -> closed."""
    R = Matrix.Rotation(yaw, 4, "Z")
    if screen is None:
        q = Part()
        q.box(body, -0.16, 0.16, -0.11, 0.11, 0.0, 0.018, bevel=0.003)
        o = q.emit(name, col, Vector((x, y, z)), yaw)
        return o
    p_body = Part()
    p_body.box(body, -0.16, 0.16, -0.11, 0.11, 0.0, 0.012, bevel=0.003)
    p_body.box(MAT["profile"], -0.13, 0.13, -0.07, 0.04, 0.012, 0.0125)                     # keyboard field
    lid = Part()
    lid.box(body, -0.16, 0.16, 0.0, 0.005, 0.0, 0.22, bevel=0.002)
    o = lid.emit(name, col, Vector((x, y, z + 0.012)) + R @ Vector((0, 0.105, 0)), yaw)
    o.rotation_euler = (math.radians(-18), 0.0, yaw)
    me = bpy.data.meshes.new(name + "_Screen")
    me.from_pydata([(-0.15, -0.0006, 0.012), (0.15, -0.0006, 0.012), (0.15, -0.0006, 0.207), (-0.15, -0.0006, 0.207)],
                   [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new()
    for li, (u, v) in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[li].uv = (u, v)
    me.materials.append(screen)
    so = bpy.data.objects.new(name + "_Screen", me)
    col.objects.link(so)
    so.parent = o
    p_body.emit(name + "_Base", col, Vector((x, y, z)), yaw)
    return o


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
    body = mat("Laptop_Body", "#9EA2A6", 0.35, metal=0.8)
    blk = mat("Prop_Black", "#18181A", 0.5)
    ply = MAT["ply"]
    burnt = mat("Laser_Burnt_Edge", "#4E3220", 0.7)
    acr = mat("Acrylic_Clear", "#DDE8EE", 0.05)
    acr_o = mat("Acrylic_Orange", "#FFA13D", 0.1)
    paper = mat("Paper", "#F4F2EC", 0.8)
    benches = sorted(o.name for o in bpy.data.collections["WorkTables"].objects if o.name.startswith("WorkTable_")
                     and o.parent is None)
    tops = {bn: bench_top(bn) for bn in benches}

    def frame(bn):                                                 # long axis y: u along y, v along x (+v = SSW)
        x0, x1, y0, y1, zt = tops[bn]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        return (lambda u, v: (cx + v, cy + u)), zt

    def rect(p, m, at, u, v, du, dv, z, h, bevel=0.0):
        x, y = at(u, v)
        p.box(m, x - dv / 2, x + dv / 2, y - du / 2, y + du / 2, z, z + h, bevel=bevel)

    # ---- WorkTable_0: laser-cut design
    at, zt = frame(benches[0])
    p = Part()
    rect(p, cm, at, 0.0, -0.05, 0.60, 0.45, zt, 0.003)                                       # A2 mat
    z = zt + 0.003
    rect(p, ply, at, -0.02, -0.06, 0.40, 0.30, z, 0.003)                                     # cut sheet 400 x 300
    for k, (u, v, du, dv, gone) in enumerate(((-0.12, -0.12, 0.13, 0.08, True), (0.05, -0.12, 0.13, 0.08, True),
                                              (-0.12, 0.01, 0.13, 0.09, False), (0.05, 0.01, 0.13, 0.09, False),
                                              (0.14, -0.06, 0.05, 0.22, False))):
        if gone:                                                                             # part popped out: mat shows
            rect(p, cm, at, u, v, du, dv, z + 0.0031, 0.0002)
        for (a, b, c, d) in ((u, v - dv / 2, du, 0.0015), (u, v + dv / 2, du, 0.0015),
                             (u - du / 2, v, 0.0015, dv), (u + du / 2, v, 0.0015, dv)):
            rect(p, burnt, at, a, b, c, d, z + 0.003, 0.0003)                               # kerf lines
    bu, bv = -0.55, 0.05                                                                     # the assembled box
    rect(p, ply, at, bu, bv, 0.14, 0.10, zt, 0.08)
    for du_, dv_ in ((-0.07, -0.05), (-0.07, 0.05), (0.07, -0.05), (0.07, 0.05)):
        for k in range(4):                                                                   # finger joints on the corners
            if k % 2 == 0:
                rect(p, burnt, at, bu + du_, bv + dv_, 0.004, 0.004, zt + k * 0.02, 0.02)
    rect(p, ply, at, bu + 0.17, bv - 0.02, 0.14, 0.10, zt, 0.003)                            # its lid beside it
    rect(p, alu, at, 0.36, -0.12, 0.15, 0.012, zt, 0.004)                                   # calipers
    rect(p, alu, at, 0.30, -0.10, 0.006, 0.04, zt, 0.004)
    for k, mm in enumerate((acr, acr, acr_o)):                                               # acrylic test cuts
        rect(p, mm, at, 0.30 + k * 0.06, 0.16, 0.05, 0.03, zt, 0.003)
    rect(p, paper, at, 0.0, 0.30, 0.42, 0.30, zt, 0.0006)                                   # printed layout, other side
    p.emit(f"BenchProps_0", col, Vector((0, 0, 0)))
    x, y = at(0.81, -0.20)
    laptop(col, None, "Laptop_0", x, y, zt, -math.pi / 2, body, screen_mat("Screen_Vector", "vector.png"))

    # ---- WorkTable_1: electronics + programming
    at, zt = frame(benches[1])
    p = Part()
    rect(p, cm, at, -0.05, -0.10, 0.45, 0.30, zt, 0.003)                                     # A3 mat
    z = zt + 0.003
    bb = mat("Breadboard_White", "#ECEBE6", 0.6)
    rect(p, bb, at, -0.05, -0.12, 0.165, 0.055, z, 0.009)                                   # breadboard
    for k in range(2):
        rect(p, mat("Breadboard_Rail", "#C9302C" if k else "#2E5FB5", 0.6), at, -0.05, -0.145 + k * 0.05, 0.15, 0.002, z + 0.009, 0.0002)
    rect(p, mat("DevBoard_Blue", "#1C3F8C", 0.4), at, -0.09, -0.12, 0.05, 0.018, z + 0.009, 0.006)   # dev board
    rect(p, blk, at, -0.09, -0.12, 0.012, 0.010, z + 0.015, 0.0015)
    wires = [("#C9302C", -0.03, -0.01), ("#151515", -0.01, 0.01), ("#E8B21E", 0.01, 0.03), ("#1E9E52", 0.03, 0.05)]
    for c, ua, ub in wires:                                                                  # jumper wires (arched)
        wm = mat("Jumper_" + c[1:], c, 0.4)
        xa, ya = at(ua - 0.05, -0.13); xb, yb = at(ub - 0.04, -0.105)
        zz = z + 0.009
        p.cyl(wm, (xa, ya, zz), (xa, ya, zz + 0.012), 0.0011, seg=6)
        p.cyl(wm, (xa, ya, zz + 0.012), (xb, yb, zz + 0.012), 0.0011, seg=6)
        p.cyl(wm, (xb, yb, zz + 0.012), (xb, yb, zz), 0.0011, seg=6)
    fr1 = mat("FR1_Copper", "#C27A4A", 0.35, metal=0.6)
    rect(p, fr1, at, 0.10, -0.10, 0.076, 0.051, z, 0.0016)                                   # SRM-20 board
    for k in range(5):
        rect(p, mat("FR1_Isolation", "#7A4A2A", 0.6), at, 0.075 + k * 0.012, -0.10, 0.0008, 0.04, z + 0.0016, 0.0001)
    oe = mat("Print_Orange", "#FFA13D", 0.45)
    rect(p, oe, at, 0.10, 0.02, 0.09, 0.06, z, 0.003)                                        # printed enclosure: tray
    for (du_, dv_, a, b) in ((0.0, -0.0285, 0.09, 0.003), (0.0, 0.0285, 0.09, 0.003), (-0.0435, 0.0, 0.003, 0.06), (0.0435, 0.0, 0.003, 0.06)):
        rect(p, oe, at, 0.10 + du_, 0.02 + dv_, a, b, z, 0.025)
    rect(p, oe, at, 0.21, 0.02, 0.09, 0.06, z, 0.003)                                        # its lid
    ym = mat("Meter_Yellow", "#E8B21E", 0.5)
    rect(p, ym, at, -0.36, 0.0, 0.16, 0.08, zt, 0.035, bevel=0.006)                          # multimeter in use
    rect(p, mat("Meter_LCD", "#9FB49A", 0.3), at, -0.40, 0.0, 0.04, 0.06, zt + 0.035, 0.0005)
    def cable(m_, pts, r):                                                                   # lies on the table
        for (ua, va, za), (ub, vb, zb) in zip(pts, pts[1:]):
            xa, ya = at(ua, va); xb, yb = at(ub, vb)
            p.cyl(m_, (xa, ya, za + r), (xb, yb, zb + r), r, seg=8)
    for c, dv_ in (("#C9302C", 0.012), ("#151515", -0.012)):                                # meter leads to the board
        cable(mat("Lead_" + c[1:], c, 0.4), [(-0.28, dv_, zt), (-0.20, dv_ + 0.05, zt), (-0.10, 0.06 + dv_, zt),
                                              (0.02, 0.0 + dv_, z), (0.09, -0.09 + dv_, z + 0.0016)], 0.0018)
    cable(blk, [(0.62, -0.22, zt), (0.48, -0.30, zt), (0.30, -0.33, zt), (0.15, -0.30, zt), (0.05, -0.22, zt),
                (-0.02, -0.17, z), (-0.06, -0.13, z + 0.009)], 0.0022)                       # USB laptop -> dev board
    laptop(col, p, "Laptop_1b", *at(-0.81, 0.24), zt, math.pi / 2, body)                    # second laptop, closed
    p.emit(f"BenchProps_1", col, Vector((0, 0, 0)))
    x, y = at(0.81, -0.20)
    laptop(col, None, "Laptop_1", x, y, zt, -math.pi / 2, body, screen_mat("Screen_Code", "code.png"))

    # ---- WorkTable_2: CNC stool kit, dry fit (standing)
    at, zt = frame(benches[2])
    p = Part()
    # stool from the ShopBot nest (build_jobs.py): seat ø340 x 18 birch ply upside down, two tapered legs wedged into
    # their mortises and splayed 10 deg, a stretcher between them; the third leg and its wedge wait beside the open
    # slot (branch remodel 2026-11-26, my design). Ply laminations on the seat edge as alternating 2 mm rings.
    sx, sy = at(0.0, 0.0)
    lam = (ply, mat("Ply_Lamination_Dark", "#B48A5A", 0.75))
    for k in range(9):
        p.cyl(lam[k % 2], (sx, sy, zt + k * 0.002), (sx, sy, zt + (k + 1) * 0.002), 0.17 - (0.0015 if k in (0, 8) else 0),
              seg=64)
    p.cyl(ply, (sx, sy, zt + 0.0179), (sx, sy, zt + 0.0182), 0.1685, seg=64)                   # seat face (up)
    dark = mat("Mortise_Shadow", "#2A1E14", 0.9)
    def leg(ang, splay, z0, lying=None):
        """Tapered leg: 75 mm wide at the tenon end, 50 at the foot, 440 long, 18 thick."""
        bm = p.bm(ply)
        vs = []
        if lying is None:
            c_, s_ = math.cos(ang), math.sin(ang)
            pts = []
            for (r_, zz, hw) in ((0.105, z0, 0.0375), (0.105 + 0.44 * math.sin(splay), z0 + 0.44 * math.cos(splay), 0.025)):
                pts.append((r_, zz, hw))
            for (r_, zz, hw) in pts:
                for (w_, t_) in ((-hw, -0.009), (hw, -0.009), (hw, 0.009), (-hw, 0.009)):
                    vs.append(bm.verts.new((sx + r_ * c_ - w_ * s_ + t_ * c_, sy + r_ * s_ + w_ * c_ + t_ * s_, zz)))
        else:
            lu, lv = lying
            for (uu, hw) in ((0.0, 0.0375), (0.44, 0.025)):
                for (w_, zz) in ((-hw, zt), (hw, zt), (hw, zt + 0.018), (-hw, zt + 0.018)):
                    x_, y_ = at(lu + uu, lv + w_)
                    vs.append(bm.verts.new((x_, y_, zz)))
            vs = [vs[i] for i in (0, 1, 2, 3, 4, 5, 6, 7)]
        for f in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
            try:
                bm.faces.new([vs[i] for i in f])
            except ValueError:
                pass
    for ang in (math.radians(90), math.radians(210)):
        leg(ang, math.radians(10), zt + 0.018)
        c_, s_ = math.cos(ang), math.sin(ang)
        wx, wy = sx + 0.105 * c_, sy + 0.105 * s_                                               # wedge in the tenon
        p.box(mat("Wedge_Walnut", "#5A3B24", 0.6), wx - 0.004, wx + 0.004, wy - 0.004, wy + 0.004, zt + 0.018, zt + 0.024)
    a3 = math.radians(330)                                                                     # open mortise
    mxx, myy = sx + 0.105 * math.cos(a3), sy + 0.105 * math.sin(a3)
    bmm = p.bm(dark)
    import bmesh as _bm
    from mathutils import Matrix as _Mx
    _bm.ops.create_cube(bmm, size=1.0, matrix=_Mx.Translation((mxx, myy, zt + 0.0182)) @ _Mx.Rotation(a3 + math.pi / 2, 4, "Z")
                        @ _Mx.Diagonal((0.075, 0.018, 0.0006, 1)))
    # stretcher between the two fitted legs, 200 mm up their length
    def legpt(ang, t):
        r_ = 0.105 + 0.44 * t * math.sin(math.radians(10))
        return (sx + r_ * math.cos(ang), sy + r_ * math.sin(ang), zt + 0.018 + 0.44 * t * math.cos(math.radians(10)))
    pa, pb = legpt(math.radians(90), 0.48), legpt(math.radians(210), 0.48)
    p.cyl(ply, pa, pb, 0.011, seg=12)
    leg(None, None, None, lying=(0.40, -0.05))                                                  # third leg, waiting
    rect(p, mat("Wedge_Walnut", "#5A3B24", 0.6), at, 0.92, -0.05, 0.03, 0.008, zt, 0.008)   # its wedge
    rect(p, ply, at, 0.45, 0.07, 0.30, 0.06, zt, 0.018)                                     # spare stretcher blank
    mx, my = at(-0.40, 0.12)                                                                 # rubber mallet
    p.cyl(blk, (mx - 0.05, my, zt + 0.03), (mx + 0.05, my, zt + 0.03), 0.03, seg=20)
    hx, hy = at(-0.40 - 0.25, 0.12)
    p.cyl(mat("Handle_Wood", "#B08452", 0.6), (mx, my, zt + 0.03), (hx, hy, zt + 0.012), 0.012, seg=10)
    red = mat("Clamp_Red", "#C0262D", 0.4)
    for k in range(2):                                                                       # F-clamps, lying flat
        u = -0.78 + k * 0.14
        rect(p, alu, at, u, -0.08, 0.025, 0.30, zt, 0.006)                                   # bar
        rect(p, alu, at, u + 0.045, -0.225, 0.07, 0.015, zt, 0.012)                          # fixed jaw
        rect(p, red, at, u + 0.045, -0.10, 0.07, 0.022, zt, 0.014)                           # sliding jaw
        rect(p, red, at, u + 0.09, -0.10, 0.03, 0.03, zt, 0.03, bevel=0.008)                 # screw handle
    laptop(col, p, "Laptop_2", *at(0.90, -0.20), zt, -math.pi / 2, body)                    # closed
    p.emit(f"BenchProps_2", col, Vector((0, 0, 0)))

    # ---- WorkTable_3: textile cutting (standing)
    at, zt = frame(benches[3])
    p = Part()
    rect(p, cm, at, 0.0, 0.0, 0.90, 0.60, zt, 0.003)                                         # A1 mat
    z = zt + 0.003
    fab = mat("Fabric_Linen_Blue", "#3E5F8A", 0.95)
    fab2 = mat("Fabric_Mustard", "#C99A2E", 0.95)
    rect(p, fab, at, -0.02, 0.0, 0.80, 0.52, z, 0.0012)                                      # fabric laid out
    pat = mat("Pattern_Paper", "#E9DCC0", 0.85)
    pins = mat("Pin_Head_Red", "#C0262D", 0.4)
    for (u, v, du, dv) in ((-0.20, -0.08, 0.30, 0.22), (0.15, -0.10, 0.22, 0.18), (0.05, 0.14, 0.40, 0.14)):
        rect(p, pat, at, u, v, du, dv, z + 0.0012, 0.0004)                                   # paper pattern pieces
        for cu, cv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            px, py = at(u + cu * (du / 2 - 0.02), v + cv * (dv / 2 - 0.02))
            p.cyl(pins, (px, py, z + 0.0016), (px, py, z + 0.006), 0.0018, seg=8)
    rect(p, acr, at, 0.30, 0.18, 0.60, 0.15, z + 0.0016, 0.003)                              # quilting ruler
    rx, ry = at(0.36, -0.02)                                                                 # rotary cutter
    p.box(mat("Cutter_Grey", "#5E6266", 0.5), rx - 0.015, rx + 0.015, ry - 0.08, ry + 0.06, z + 0.0016, z + 0.02, bevel=0.005)
    p.cyl(alu, (rx - 0.004, ry + 0.065, z + 0.023), (rx + 0.004, ry + 0.065, z + 0.023), 0.022, seg=24)
    so = mat("Scissor_Orange", "#FFA13D", 0.45)                                              # fabric scissors
    rect(p, alu, at, 0.62, -0.20, 0.13, 0.012, zt, 0.004)
    rect(p, so, at, 0.52, -0.21, 0.07, 0.05, zt, 0.008)
    for k in range(3):                                                                       # cut pieces stacked
        rect(p, fab, at, 0.70, 0.12, 0.26, 0.18, zt + k * 0.0015, 0.0012)
    for k, m_ in enumerate((fab2, fab2, fab, fab, mat("Fabric_Grey", "#8B8E8F", 0.95))):   # folded fabric
        rect(p, m_, at, -0.80 + 0.006 * (k % 2), 0.0, 0.30, 0.22, zt + k * 0.009, 0.009, bevel=0.004)
    tx_, ty_ = at(0.50, 0.24)                                                                # tape measure
    p.cyl(mat("Tape_Yellow", "#F2C200", 0.5), (tx_, ty_, zt), (tx_, ty_, zt + 0.012), 0.03, seg=24)
    p.emit(f"BenchProps_3", col, Vector((0, 0, 0)))
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
