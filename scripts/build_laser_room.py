"""Laser room (glazed room x 29.67-32.53, y 20.14-26.92). Re-runnable (collection "LaserRoom").

Machines from the equipment list, models in build_machines.py:
  Epilog Fusion Edge 24 (1055x834x967 incl. stand, white + navy band), 2x Glowforge Pro HD (965x527x211), Glowforge Aura (556x521x127),
  xTool F1 Ultra (273x373x492 upright galvo tower, green shield).
Layout (user brief 2026-10-08: material storage + work surfaces, lots of room):
  - SSW glass: one 4.86 m profile laser bench (y 20.24-25.10, 0.70 deep, 0.78 high) carrying the Glowforges and
    the xTool, with 1.3 m of free staging surface at the ESE end; flat-file sheet drawers underneath.
  - NNE partition, WNW end: Epilog, 0.20 m off the partition so its exhaust riser runs behind it.
  - NNE partition: material rack (y 21.60-23.50): upright sheet slots below a 0.98 m worktop, bins + tape rolls above.
  - Under the interior window (y 23.60-25.62): 2 m standing prep counter (masking, weeding, assembly, job setup).
  - WNW wall: safety station (CO2 extinguisher, fire blanket, first aid, laser sign) + 3 offcut sorting bins.
  - Both doors (NNE door y 25.81-26.88, exterior door y 25.28-26.76) and the aisle (>= 1.0 m) kept clear.
  - ONE central exhaust: rear ports -> short flex -> low manifold behind the bench -> riser -> ceiling collector
    (Epilog branch joins) -> inline fan -> up through the slab to the building's dedicated vent.
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
_src = open(HERE + "build_machines.py").read()
mach = {}
exec(_src[:_src.index("def build():")], mach)
mach["materials"]()
M = mach["M"]
Part, mat = lib["Part"], lib["simple_mat"]
rng = random.Random(31)

XN, XG = 29.67, 32.45            # NNE partition face, bench back line by the glass
T_D, T_H = 0.70, 0.78            # laser bench
BY0, BY1 = 20.24, 25.10
GX = 32.39                       # machine backs (manifold behind)
SOFFIT = 3.93


def clear(name):
    scene = bpy.context.scene
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if col.name not in scene.collection.children:
        scene.collection.children.link(col)
    for o in list(col.objects):
        data = o.data
        bpy.data.objects.remove(o)
        if isinstance(data, bpy.types.Mesh) and data.users == 0:
            bpy.data.meshes.remove(data)
        elif isinstance(data, bpy.types.Curve) and data.users == 0:
            bpy.data.curves.remove(data)
    return col


def drawers(p, xa, xb, depth, z0, z1, n, m_front, handle, gap, label):
    """Bay of n equal drawers between z0 and z1 (local frame, front at y=0)."""
    hh = (z1 - z0) / n
    for k in range(n):
        z = z0 + k * hh
        p.box(gap, xa, xb, 0.012, depth - 0.01, z, z + hh)
        p.box(m_front, xa + 0.003, xb - 0.003, -0.002, 0.016, z + 0.003, z + hh - 0.003, bevel=0.0015)
        p.box(handle, (xa + xb) / 2 - 0.10, (xa + xb) / 2 + 0.10, -0.018, -0.002, z + hh - 0.035, z + hh - 0.022, bevel=0.002)
        p.box(label, xa + 0.04, xa + 0.13, -0.0025, -0.002, z + hh - 0.040, z + hh - 0.018)


def laser_bench(col, mm):
    L = BY1 - BY0
    legs = [0.0, 1.20, 2.40, 3.62, L - 0.04]
    part, _ = lib["table_unit"](L, T_D, T_H, legs, lower=())
    loc, rot = lib["placement"](XG - T_D / 2, (BY0 + BY1) / 2, L, T_D, "-x")
    part.emit("LaserBench", col, loc, rot)
    p = Part()
    for i in range(3):                                                  # flat-file drawers for laser stock
        xa, xb = legs[i] + 0.04, legs[i + 1]
        drawers(p, xa, xb, T_D, 0.06, T_H - 0.09, 6, MAT["ply"], mm["handle"], mm["gap"], mm["label"])
    xa, xb = legs[3] + 0.04, legs[4]                                    # open bay: spare beds + stock boxes
    p.box(MAT["ply"], xa, xb, 0.002, T_D - 0.002, 0.10, 0.118, bevel=0.001)
    for k in range(3):                                                  # honeycomb / knife beds on edge
        x = xa + 0.06 + k * 0.035
        p.box(mm["alu"], x, x + 0.022, 0.06, 0.62, 0.118, 0.118 + 0.50)
    for k in range(3):
        x = xa + 0.30 + k * 0.27
        p.box(mm["card"], x, x + 0.25, 0.05, 0.60, 0.118, 0.118 + 0.12 + 0.04 * k, bevel=0.003)
    p.emit("LaserBench_Drawers", col, loc, rot)
    return loc, rot


def staging(col, mm):
    """Free bench end: a finished laser-cut job cooling on a tray, sample sheets, squeegee."""
    p = Part()
    z = T_H + 0.0
    p.box(mm["tray"], 31.88, 32.30, 24.05, 24.65, z, z + 0.015, bevel=0.003)
    for k in range(4):                                                  # cut parts on the tray
        x, y = 31.94 + (k % 2) * 0.17, 24.12 + (k // 2) * 0.24
        p.box(MAT["ply"], x, x + 0.14, y, y + 0.20, z + 0.015, z + 0.018)
    p.box(M["acrylic"] if "acrylic" in M else MAT["ply"], 31.90, 32.32, 24.75, 25.02, z, z + 0.003)
    for k, c in enumerate(mm["acr"][:3]):
        p.box(c, 31.92 + k * 0.01, 32.30, 24.78, 25.00, z + 0.003 + k * 0.003, z + 0.006 + k * 0.003)
    p.emit("LaserBench_Staging", col, Vector((0, 0, 0)))


def machines(col):
    gp = mach["glowforge_pro"]
    pos = {}
    y = BY0 + 0.07
    for name, model, w, d in (("Glowforge_ProHD_1", gp(), 0.965, 0.527), ("Glowforge_ProHD_2", gp(), 0.965, 0.527),
                              ("Glowforge_Aura", mach["glowforge_aura"](), 0.556, 0.521),
                              ("xTool_F1_Ultra", mach["xtool_f1_ultra"](), 0.273, 0.373)):
        cy = y + w / 2
        mach["place"](model, name, col, GX - d / 2, cy, T_H, w, d, "-x")
        pos[name] = (cy, w)
        y += w + 0.15
    cy, w = pos["xTool_F1_Ultra"]                                         # XTOOL wordmark on the upper band
    f = bpy.data.fonts.get("Roboto-Bold") or bpy.data.fonts.load(bpy.path.abspath("//refs/branding/fonts/Roboto-Bold.ttf"))
    cu = bpy.data.curves.new("xTool_Wordmark", "FONT")
    cu.body, cu.size, cu.font, cu.align_x, cu.extrude = "XTOOL", 0.030, f, "CENTER", 0.0
    cu.space_character = 1.25
    cu.materials.append(mat("Mach_White", "#EEEEEC", 0.35))
    wm = bpy.data.objects.new("xTool_Wordmark", cu)
    col.objects.link(wm)
    wm.matrix_world = Matrix.Translation((GX - 0.373 - 0.0015, cy + 0.011, T_H + 0.42)) @ Matrix.Rotation(-math.pi / 2, 4, "Z") \
        @ Matrix.Rotation(math.pi / 2, 4, "X")
    # its touchscreen controller beside it

    mach["place"](mach["xtool_controller"](), "xTool_F1_Ultra_Controller", col, GX - 0.30, cy + w / 2 + 0.10, T_H, 0.13, 0.032, "-x")
    ex, ey = 29.87 + 0.834 / 2, 20.35 + 1.055 / 2
    mach["place"](mach["epilog"](), "Epilog_FusionEdge24", col, ex, ey, 0.0, 1.055, 0.834, "+x")
    fr = bpy.data.fonts.get("Roboto-Bold") or bpy.data.fonts.load(bpy.path.abspath("//refs/branding/fonts/Roboto-Bold.ttf"))
    xf = ex + 0.834 / 2 + 0.0015                                          # front face of the navy band
    for name, body, size, ly in (("Epilog_Logo", "Epilog Laser", 0.032, 0.14), ("Epilog_Model", "Fusion Edge", 0.034, 0.66)):
        cu = bpy.data.curves.new(name, "FONT")
        cu.body, cu.size, cu.font, cu.extrude = body, size, fr, 0.0
        cu.materials.append(mat("Mach_White", "#EEEEEC", 0.35))
        ob = bpy.data.objects.new(name, cu)
        col.objects.link(ob)
        ob.matrix_world = Matrix.Translation((xf, ey - 1.055 / 2 + ly, 0.85)) @ Matrix.Rotation(math.pi / 2, 4, "Z") \
            @ Matrix.Rotation(math.pi / 2, 4, "X")
    return pos, ey


def exhaust(col, pos, ey, mm):
    flex = mm["flex"]
    galv = M["galv"]
    XM, ZM, RM = 32.465, T_H + 0.09, 0.065                              # manifold behind the bench
    YR, ZC, RC = 25.17, 3.55, 0.09                                       # riser + ceiling collector
    XO, XF0, XF1, XJ = 29.95, 30.60, 31.00, 31.80                        # slab exit, fan, Epilog junction
    p = Part()

    def sph(q, r):
        bmesh.ops.create_uvsphere(p.bm(galv), u_segments=24, v_segments=12, radius=r, matrix=Matrix.Translation(q))

    p.cyl(galv, (XM, 20.40, ZM), (XM, YR, ZM), RM, seg=24)
    p.cyl(galv, (XM, 20.39, ZM), (XM, 20.40, ZM), RM + 0.004, seg=24)
    for y in (20.95, 22.35, 23.70, 24.75):                               # saddle brackets on the bench
        p.box(galv, XM - 0.07, XG, y - 0.015, y + 0.015, T_H + 0.0, T_H + 0.005)
    ports = {"Glowforge_ProHD_1": (0.12, 0.080), "Glowforge_ProHD_2": (0.12, 0.080), "Glowforge_Aura": (0.11, 0.060),
             "xTool_F1_Ultra": (None, 0.22)}
    for name, (cy, w) in pos.items():
        off, zp = ports[name]
        yy = cy if off is None else cy - (w / 2 - off)                  # local right (rear right) -> world -y
        z = T_H + zp
        if z > ZM + 0.06:                                               # high outlet: out, then down into the manifold
            p.cyl(flex, (GX + 0.035, yy, z), (XM, yy, z), 0.045, seg=20)
            bmesh.ops.create_uvsphere(p.bm(flex), u_segments=20, v_segments=10, radius=0.045, matrix=Matrix.Translation((XM, yy, z)))
            p.cyl(flex, (XM, yy, z), (XM, yy, ZM + RM - 0.01), 0.045, seg=20)
            p.cyl(galv, (XM, yy, ZM + RM - 0.004), (XM, yy, ZM + RM + 0.004), 0.048, seg=20)
        else:
            p.cyl(flex, (GX + 0.035, yy, z), (XM - RM + 0.01, yy, z), 0.045, seg=20)
            p.cyl(galv, (XM - RM - 0.006, yy, z), (XM - RM + 0.002, yy, z), 0.048, seg=20)
        p.cyl(galv, (GX + 0.036, yy, z), (GX + 0.044, yy, z), 0.048, seg=20)
    sph((XM, YR, ZM), RC)
    p.cyl(galv, (XM, YR, ZM), (XM, YR, ZC), RC, seg=24)                  # riser
    sph((XM, YR, ZC), RC)
    p.cyl(galv, (XM, YR, ZC), (XO, YR, ZC), RC, seg=24)                  # collector
    sph((XO, YR, ZC), RC)
    p.cyl(galv, (XO, YR, ZC), (XO, YR, SOFFIT), RC, seg=24)              # up to the building vent
    p.cyl(galv, (XO, YR, SOFFIT - 0.03), (XO, YR, SOFFIT), RC + 0.04, seg=24)
    p.cyl(galv, (XF0, YR, ZC), (XF1, YR, ZC), 0.16, seg=32)              # inline fan
    for xr in (XF0, XF1):
        p.cyl(M["dark"], (xr - 0.01, YR, ZC), (xr + 0.01, YR, ZC), 0.165, seg=32)
    p.box(M["dark"], XF0 + 0.14, XF0 + 0.26, YR - 0.16, YR - 0.10, ZC - 0.06, ZC + 0.06, bevel=0.005)
    ye = ey + 0.25                                                        # Epilog branch (150 mm)
    pts = [(29.835, ye, 0.70), (29.76, ye, 0.70), (29.76, ye, ZC), (29.76, 24.80, ZC), (XJ, 24.80, ZC), (XJ, YR, ZC)]
    for a, b in zip(pts, pts[1:]):
        p.cyl(galv, a, b, 0.075, seg=20)
    for q in pts[1:-1]:
        bmesh.ops.create_uvsphere(p.bm(galv), u_segments=20, v_segments=10, radius=0.075, matrix=Matrix.Translation(q))
    for z in (1.6, 2.6):
        p.box(galv, XN + 0.002, XN + 0.02, ye - 0.05, ye + 0.05, z, z + 0.03)
    for xh, yh in ((31.6, YR), (XJ, 24.95), (29.76, 22.8), (29.76, 24.2), (30.3, YR), (30.9, 24.80)):
        p.cyl(galv, (xh, yh, ZC + 0.08), (xh, yh, SOFFIT), 0.004, seg=8)
    p.emit("Exhaust_Central", col, Vector((0, 0, 0)))


def stock_rack(col, mm, y0=21.60, depth=0.60):
    """Laser stock rack against the NNE partition, facing +x."""
    levels = [0.10, 0.98, 1.38, 1.76]
    part, slots, L = lib["shelf_unit"]([0.91, 0.91], depth, 2.10, levels)
    loc, rot = lib["placement"](XN + depth / 2, y0 + L / 2, L, depth, "+x")
    part.emit("LaserStockRack", col, loc, rot)
    p = Part()
    stock = [MAT["ply"], MAT["ply"], mm["mdf"], mm["card"], mm["cork"]] + mm["acr"]
    for bi in (0, 1):
        xa, xb, _, _, zt = slots[(bi, 0)]
        k = 0
        x = xa + 0.02
        while x < xb - 0.05:                                            # 20x20 dividers every 0.15
            p.profile(0.02, "z", x, 0.02, zt, 0.78)
            p.profile(0.02, "z", x, depth - 0.06, zt, 0.78)
            xs = x + 0.025
            for _ in range(rng.randint(3, 7)):                          # sheets on edge in the slot
                t = rng.choice((0.003, 0.003, 0.004, 0.006))
                if xs + t > x + 0.145:
                    break
                hgt = rng.choice((0.40, 0.60, 0.60, 0.30))
                dep = rng.choice((0.40, 0.50, 0.55))
                p.box(stock[(k + rng.randint(0, 3)) % len(stock)], xs, xs + t, 0.03, 0.03 + dep, zt, zt + hgt, bevel=0.0006)
                xs += t + rng.uniform(0.002, 0.008)
            k += 1
            x += 0.15
        xa, xb, _, _, zt = slots[(bi, 2)]                               # bins of small stock (felt, leather, card)
        for j in range(3):
            lib["bin_box"](p, MAT["bins"][(bi * 3 + j) % 6], xa + 0.02 + j * 0.30, 0.05, zt, w=0.28, d=0.45, h=0.22)
        xa, xb, _, _, zt = slots[(bi, 3)]
        for j in range(2):
            p.box(mm["card"], xa + 0.05 + j * 0.42, xa + 0.42 + j * 0.42, 0.05, 0.50, zt, zt + 0.18 + 0.05 * j, bevel=0.003)
    xa, xb, _, _, zt = slots[(0, 1)]                                    # worktop (board at 0.98): tape-roll stand
    for k, (r, c) in enumerate(((0.065, mm["paper"]), (0.055, mm["paper"]), (0.050, mm["clear"]))):
        x = xa + 0.10 + k * 0.33
        p.cyl(c, (x, 0.18, zt + 0.10), (x + 0.30, 0.18, zt + 0.10), r, seg=28)
        p.cyl(MAT["profile"], (x - 0.02, 0.18, zt + 0.10), (x + 0.32, 0.18, zt + 0.10), 0.008, seg=10)
        for xx in (x - 0.02, x + 0.31):
            p.box(MAT["profile"], xx, xx + 0.012, 0.15, 0.21, zt, zt + 0.11)
    xa, xb, _, _, zt = slots[(1, 1)]
    p.box(mm["mat"], xa + 0.05, xb - 0.05, 0.05, 0.50, zt, zt + 0.003)  # small cutting mat + steel rule
    p.box(M["chrome"], xa + 0.10, xa + 0.70, 0.40, 0.43, zt + 0.003, zt + 0.005)
    p.emit("LaserStockRack_Contents", col, loc, rot)


def prep_counter(col, mm, y0=23.60, L=2.02, depth=0.70, H=0.92):
    part, _ = lib["table_unit"](L, depth, H, [0.0, 0.98, L - 0.04], lower=(0.15,))
    loc, rot = lib["placement"](XN + depth / 2, y0 + L / 2, L, depth, "+x")
    part.emit("LaserPrepCounter", col, loc, rot)
    p = Part()
    drawers(p, 0.04, 0.98, depth, 0.17, H - 0.07, 4, MAT["ply"], mm["handle"], mm["gap"], mm["label"])
    z = H
    p.box(mm["mat"], 0.08, 0.98, 0.10, 0.58, z, z + 0.003)                # cutting mat
    p.box(M["chrome"], 0.15, 0.75, 0.50, 0.53, z + 0.003, z + 0.005)    # steel rule
    p.box(MAT["ply"], 0.25, 0.43, 0.20, 0.34, z + 0.003, z + 0.006)      # weeded part
    p.box(mm["paper"], 0.50, 0.70, 0.18, 0.40, z + 0.003, z + 0.0045)    # transfer tape sheet
    p.cyl(mm["black"], (0.82, 0.30, z + 0.008), (0.95, 0.30, z + 0.008), 0.004, seg=8)   # scalpel
    p.box(mm["laptop"], 1.20, 1.55, 0.15, 0.40, z, z + 0.018, bevel=0.004)  # laptop (job setup)
    bm = p.bm(mm["laptop"])
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((1.375, 0.42, z + 0.12)) @ Matrix.Rotation(math.radians(-15), 4, "X")
                          @ Matrix.Diagonal((0.35, 0.008, 0.23, 1)))
    bmesh.ops.create_cube(p.bm(mm["screen"]), size=1.0, matrix=Matrix.Translation((1.375, 0.414, z + 0.12)) @ Matrix.Rotation(math.radians(-15), 4, "X")
                          @ Matrix.Diagonal((0.32, 0.001, 0.20, 1)))
    for k in range(3):                                                  # assembled laser-cut boxes
        x = 1.68 + k * 0.10
        p.box(MAT["ply"], x, x + 0.08, 0.20 + k * 0.05, 0.28 + k * 0.05, z, z + 0.08, bevel=0.002)
    p.box(mm["tray"], 1.70, 1.95, 0.45, 0.62, z, z + 0.03, bevel=0.003)  # parts tray
    p.emit("LaserPrepCounter_Top", col, loc, rot)


def safety_station(col, mm):
    p = Part()
    yw = 20.14
    # CO2 extinguisher on a wall bracket
    ex = 30.86
    p.box(mm["black"], ex - 0.05, ex + 0.05, yw, yw + 0.03, 0.70, 0.95)
    p.cyl(mm["black"], (ex, yw + 0.11, 0.62), (ex, yw + 0.11, 1.18), 0.068, seg=32)
    p.cyl(mm["red"], (ex, yw + 0.11, 0.90), (ex, yw + 0.11, 1.00), 0.069, seg=32)       # red band
    p.cyl(mm["black"], (ex, yw + 0.11, 1.18), (ex, yw + 0.11, 1.26), 0.025, seg=16)
    p.cyl(mm["black"], (ex + 0.03, yw + 0.12, 1.22), (ex + 0.12, yw + 0.20, 0.95), 0.03, seg=16)  # horn
    # fire blanket pouch + first aid box + laser warning sign
    p.box(mm["red"], 31.38, 31.66, yw, yw + 0.06, 1.30, 1.62, bevel=0.01)
    p.box(mm["white"], 31.45, 31.59, yw + 0.06, yw + 0.062, 1.50, 1.56)
    p.box(mm["white"], 31.02, 31.30, yw, yw + 0.10, 1.30, 1.55, bevel=0.01)
    p.box(mm["green"], 31.14, 31.18, yw + 0.10, yw + 0.102, 1.36, 1.49)
    p.box(mm["green"], 31.10, 31.22, yw + 0.10, yw + 0.102, 1.405, 1.445)
    bm = p.bm(mm["yellow"])
    v = [bm.verts.new((31.16 + dx, yw + 0.004, 1.80 + dz)) for dx, dz in ((-0.14, -0.12), (0.14, -0.12), (0.0, 0.12))]
    bm.faces.new(v)
    bm2 = p.bm(mm["black"])
    v = [bm2.verts.new((31.16 + dx, yw + 0.005, 1.80 + dz)) for dx, dz in ((-0.04, -0.07), (0.04, -0.07), (0.0, 0.02))]
    bm2.faces.new(v)
    # offcut sorting bins: wood / acrylic / waste
    for k, c in enumerate((mm["green"], mm["blue"], mm["grey"])):
        x = 31.05 + k * 0.23
        p.box(c, x, x + 0.21, yw + 0.04, yw + 0.40, 0.0, 0.55, bevel=0.01)
        p.box(mm["black"], x + 0.02, x + 0.19, yw + 0.06, yw + 0.38, 0.55, 0.56)
    # powder extinguisher on a floor stand in the corner by the exterior door
    fx, fy = 32.36, 26.82                                             # corner beside the exterior door
    p.box(mm["black"], fx - 0.13, fx + 0.13, fy - 0.10, fy + 0.10, 0.0, 0.02)
    p.cyl(mm["red"], (fx, fy, 0.03), (fx, fy, 0.60), 0.075, seg=32)
    p.cyl(mm["black"], (fx, fy, 0.60), (fx, fy, 0.68), 0.028, seg=16)
    p.emit("LaserSafety", col, Vector((0, 0, 0)))


def build():
    col = clear("LaserRoom")
    for name in ("LaserRoom_Life",):                                    # retired props from build_life.py
        o = bpy.data.objects.get(name)
        if o:
            for k in list(o.children_recursive) + [o]:
                bpy.data.objects.remove(k)
    acr = [mat(f"Acrylic_{n}", h, 0.06, coat=0.8) for n, h in (("Red", "#E03A3F"), ("Blue", "#1245DE"), ("Yellow", "#F2C200"),
                                                                ("Green", "#009967"), ("White", "#F2F2EE"), ("Black", "#111111"))]
    mm = dict(acr=acr, mdf=mat("MDF", "#B48C5C", 0.8), card=mat("Cardboard", "#B08A5B", 0.85), cork=mat("Cork", "#B98A5A", 0.9),
              paper=mat("Masking_Paper", "#E9E1C8", 0.8), clear=mat("Acrylic_Smoke", "#9FB7C4", 0.05, coat=0.6),
              mat=mat("Cutting_Mat_Green", "#2E6B52", 0.7), handle=mat("Handle_Black", "#151515", 0.4),
              gap=mat("Drawer_Shadow", "#0E0E0E", 0.9), label=mat("Drawer_Label", "#F3F1EA", 0.6),
              alu=mat("Honeycomb_Alu", "#A9ADB1", 0.35, metal=1.0), tray=mat("Tray_Grey", "#7C8085", 0.5),
              flex=mat("Flex_Alu", "#B9BDC1", 0.35, metal=1.0), black=mat("Tool_Black", "#151515", 0.5),
              red=mat("Extinguisher_Red", "#B3141B", 0.35, coat=0.6), white=mat("Fitting_White", "#F2F1EE", 0.35),
              green=mat("Safety_Green", "#1E9E52", 0.4), yellow=mat("Safety_Yellow", "#F2C200", 0.4),
              blue=mat("Bin_Blue", "#1245DE", 0.45), grey=mat("Bin_Grey", "#6E7276", 0.45),
              laptop=mat("Laptop_Alu", "#B8BBBE", 0.3, metal=0.8), screen=mat("Laptop_Screen", "#20242A", 0.1, emit=0.6))
    laser_bench(col, mm)
    pos, ey = machines(col)
    staging(col, mm)
    exhaust(col, pos, ey, mm)
    stock_rack(col, mm)
    prep_counter(col, mm)
    safety_station(col, mm)
    print("laser room built:", ", ".join(f"{k} y {v[0]:.2f}" for k, v in pos.items()))


build()
