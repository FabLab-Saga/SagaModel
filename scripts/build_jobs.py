"""Machines at work (branch alternate-ideas, 2026-11-26; my design on Magnús's go-ahead to iterate): jobs in progress
on the machines, tied to the projects on the work tables, so the lab reads as used rather than a showroom. Re-runnable
("Jobs" collection). Each job is built in its machine's local frame and placed on the machine's current pose, so it
must run AFTER the machine builders (machines, print farm, laser room); layout.yaml carries each job as an `on:` item.

- ShopBot: a 2440 x 1220 x 18 birch sheet screwed to the spoilboard, mid-way through the CNC-stool nest that is being
  dry-fitted on work table 2: six seats cut, the leg row being cut under the spindle, the rest still to come.
- Glowforge Pro HD 1: 3 mm ply on the crumb tray with the finger-joint box (work table 0's laser-cut box) cut out and
  its lid engraving in progress; the head carriage over it.
- SRM-20 1: isolation-milling a small ATtiny board in the copper blank (end mill down on the board).
- xTool F1 Ultra: engraving a slate coaster (hex motif half done, pointer spot on).
- Prusa MK3S+ 01/03/04/06: one print each in its own filament, each printer's nozzle at the job's current height
  (PRUSA_ZX in build_print_farm.py): a project enclosure for the electronics table (half printed), a spiral vase (half),
  six SAGA keyring tags (the teaching wiki's print-cycle tag, scripts/saga_tag.py) with the lettering half printed,
  and a finished batch of hex tiles for the art wall.
"""
import math

import bpy
from mathutils import Vector

HERE = bpy.path.abspath("//scripts/")
lib = {}
exec(open(HERE + "profile_furniture.py").read(), lib)
MAT = lib["materials"]()
Part, mat = lib["Part"], lib["simple_mat"]

KERF = mat("Kerf_Dark", "#3B2A1D", 0.9)
SCORE = mat("Laser_Engrave", "#6E4A2B", 0.85)
ZINC = MAT["zinc"]


def frame(name):
    o = bpy.data.objects.get(name)
    if o is None:
        return None
    m = o.matrix_world
    return m.translation.copy(), m.to_euler().z


def ring(p, m, cx, cy, z, r, w=0.006, seg=40, a0=0.0, a1=2 * math.pi):
    """Kerf / engrave line along a circle arc (thin boxes, lying on z)."""
    for k in range(seg):
        t0 = a0 + (a1 - a0) * k / seg
        t1 = a0 + (a1 - a0) * (k + 1) / seg
        x0, y0 = cx + r * math.cos(t0), cy + r * math.sin(t0)
        x1, y1 = cx + r * math.cos(t1), cy + r * math.sin(t1)
        line(p, m, x0, y0, x1, y1, z, w)


def line(p, m, x0, y0, x1, y1, z, w=0.006, h=0.0004):
    import bmesh
    from mathutils import Matrix
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 1e-6:
        return
    mtx = Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, z + h / 2)) @ Matrix.Rotation(math.atan2(y1 - y0, x1 - x0), 4, "Z") \
        @ Matrix.Diagonal((L + w * 0.5, w, h, 1))
    bmesh.ops.create_cube(p.bm(m), size=1.0, matrix=mtx)


def rect_lines(p, m, x0, y0, x1, y1, z, w=0.006):
    for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        line(p, m, *a, *b, z, w)


def shopbot_job(col):
    f = frame("ShopBot_PRSAlpha_120")
    if not f:
        return
    p = Part()
    ply = MAT["ply"]
    X0, X1, Y0, Y1, Z = 0.545, 1.765, 0.36, 2.80, 0.86              # sheet on the spoilboard (machine frame)
    zt = Z + 0.018
    p.box(ply, X0, X1, Y0, Y1, Z, zt, bevel=0.001)
    for x in (X0 + 0.03, (X0 + X1) / 2, X1 - 0.03):                  # hold-down screws round the edge
        for y in (Y0 + 0.03, Y0 + 0.62, Y0 + 1.22, Y0 + 1.82, Y1 - 0.03):
            if x == (X0 + X1) / 2 and Y0 + 0.1 < y < Y1 - 0.1:
                continue
            p.cyl(ZINC, (x, y, zt), (x, y, zt + 0.002), 0.005, seg=10)
    seats = [(X0 + 0.205 + i * 0.405, Y0 + 0.24 + j * 0.405) for j in range(2) for i in range(3)]
    for cx, cy in seats:                                             # seats: cut (held by tabs)
        for a0 in (0.15, 0.15 + math.pi / 2, 0.15 + math.pi, 0.15 + 3 * math.pi / 2):
            ring(p, KERF, cx, cy, zt, 0.17, seg=10, a0=a0, a1=a0 + math.pi / 2 - 0.06)
        p.cyl(KERF, (cx, cy, zt), (cx, cy, zt + 0.0004), 0.004, seg=10)          # centre drill mark
    spx, spy = 1.04, 3.66 * 0.42 - 0.21                              # spindle (shopbot(): cx = W * 0.45, gy - 0.21)
    ly0 = spy - 0.02                                                 # leg strip under the spindle
    x = X0 + 0.05
    k = 0
    while x + 0.075 < X1 - 0.04:
        if x + 0.075 < spx - 0.005:                                  # legs left of the cutter: done
            rect_lines(p, KERF, x, ly0, x + 0.075, ly0 + 0.44, zt)
        elif x < spx:                                                # the leg being cut: 3 sides so far
            line(p, KERF, x, ly0, x, ly0 + 0.44, zt)
            line(p, KERF, x, ly0 + 0.44, x + 0.075, ly0 + 0.44, zt)
            line(p, KERF, x + 0.075, ly0 + 0.44, x + 0.075, spy, zt)
        x += 0.10
        k += 1
    dust = mat("Sawdust", "#D9BE8E", 0.95)
    for i, (dx, dy, s) in enumerate(((0.03, 0.02, 0.05), (-0.06, 0.05, 0.035), (0.09, -0.04, 0.03), (-0.02, -0.08, 0.04),
                                     (0.14, 0.07, 0.025), (-0.12, -0.02, 0.03))):
        p.cyl(dust, (spx + dx, spy + dy, zt), (spx + dx, spy + dy, zt + 0.0015 + 0.001 * (i % 2)), s, seg=14)
    p.emit("Job_ShopBot", col, *f)


def glowforge_job(col):
    f = frame("Glowforge_ProHD_1")
    if not f:
        return
    p = Part()
    z = 0.0432                                                       # on the machine's honeycomb tray
    thin = MAT["ply"]
    p.box(thin, 0.16, 0.66, 0.09, 0.37, z, z + 0.003, bevel=0.0005)  # 3 mm ply
    zt = z + 0.003
    for i in range(3):                                               # box sides, finger edges, cut
        for j in range(2):
            x0, y0 = 0.18 + i * 0.155, 0.11 + j * 0.13
            x1, y1 = x0 + 0.14, y0 + 0.11
            rect_lines(p, KERF, x0, y0, x1, y1, zt, w=0.0015)
            for k in range(1, 7, 2):                                 # finger notches along the long edges
                u = x0 + k * 0.14 / 7
                for yy, s in ((y0, 1), (y1, -1)):
                    rect_lines(p, KERF, u, yy, u + 0.02, yy + s * 0.006, zt, w=0.0012)
    # lid engraving in progress on the last panel: "FAB LAB SAGA" plate, half rastered
    x0, y0 = 0.18 + 2 * 0.155 + 0.02, 0.11 + 0.13 + 0.03
    for r in range(9):
        p.box(SCORE, x0, x0 + 0.10, y0 + r * 0.0055, y0 + r * 0.0055 + 0.004, zt, zt + 0.0003)
    alu = mat("Glowforge_Gantry", "#C9CCCE", 0.35, metal=0.8)
    gx = x0 + 0.05                                                   # gantry + head over the job
    p.box(alu, gx - 0.012, gx + 0.012, 0.055, 0.40, 0.120, 0.140)
    p.box(mat("Glowforge_Head", "#2B2D30", 0.45), gx - 0.03, gx + 0.03, y0 + 0.03, y0 + 0.08, 0.075, 0.135, bevel=0.004)
    led = mat("Glowforge_InnerLight", "#EAF4FF", 0.3, emit=6.0)        # running: the bed lights are on
    for y in (0.052, 0.398):
        p.box(led, 0.08, 0.885, y - 0.002, y + 0.002, 0.175, 0.18)
    p.emit("Job_Glowforge_1", col, *f)


def prusa_jobs(col):
    import re
    zx = eval(re.search(r"PRUSA_ZX = (\{[^}]*\})", open(HERE + "build_print_farm.py").read())[1])
    tag = {}
    exec(open(HERE + "saga_tag.py").read(), tag)
    BEDZ, NX, NY = 0.064, 0.245, 0.24                                # PEI top, nozzle x/y (prusa(): ex + 0.035, fy - 0.07)
    for no, fil, kind in ((1, "Orange", "enclosure"), (3, "Green", "vase"), (4, "Yellow", "tags"), (6, "Blue", "hex")):
        f = frame(f"Prusa_MK3S_{no:02d}")
        if not f:
            continue
        H = zx.get(no, 0.20) - 0.05 - BEDZ                           # print height = nozzle tip above the sheet
        m = bpy.data.materials.get(f"Filament_{fil}") or mat(f"Filament_{fil}", "#888888", 0.4)
        inner = mat(f"Print_Shadow_{fil}", "#1E1E1E", 0.8)
        p = Part()
        z = BEDZ
        if kind == "enclosure":                                     # 90 x 60 x 60 box shell, walls 2 mm, half printed
            w, d, t, h = 0.09, 0.06, 0.002, H - 0.0003
            p.box(m, NX - w / 2, NX + w / 2, NY - d / 2, NY + d / 2, z, z + 0.002)            # floor
            for a, b, c, e in ((-w / 2, w / 2, -d / 2, -d / 2 + t), (-w / 2, w / 2, d / 2 - t, d / 2),
                               (-w / 2, -w / 2 + t, -d / 2, d / 2), (w / 2 - t, w / 2, -d / 2, d / 2)):
                p.box(m, NX + a, NX + b, NY + c, NY + e, z, z + h)
            for sx in (-1, 1):                                        # screw bosses
                for sy in (-1, 1):
                    p.cyl(m, (NX + sx * 0.036, NY + sy * 0.021, z), (NX + sx * 0.036, NY + sy * 0.021, z + h), 0.004, seg=12)
        elif kind == "vase":                                         # spiral vase, 60 of 120 mm printed
            p.cyl(m, (NX, NY, z), (NX, NY, z + H - 0.0003), 0.042, seg=48)
            p.cyl(inner, (NX, NY, z + H - 0.0003), (NX, NY, z + H - 0.0001), 0.0405, seg=48)
        elif kind == "hex":                                          # finished batch of art-wall hex tiles
            for i in range(4):
                for j in range(3):
                    cx = 0.165 + i * 0.056 + (0.028 if j % 2 else 0.0)
                    cy = 0.16 + j * 0.05
                    p.cyl(m, (cx, cy, z), (cx, cy, z + 0.008 + 0.004 * ((i + j) % 3)), 0.027, seg=6)
        if kind != "tags":
            p.emit(f"Job_Prusa_{no:02d}", col, *f)
        else:                                           # 2 x 3 SAGA tags, lettering half printed
            me = tag["saga_tag_mesh"](raise_mm=round((H - 0.003) * 1000, 2))
            me.materials.clear()
            me.materials.append(m)
            loc, rot = f
            from mathutils import Matrix
            base = Matrix.Translation(loc) @ Matrix.Rotation(rot, 4, "Z")
            root = bpy.data.objects.new(f"Job_Prusa_{no:02d}", None)
            col.objects.link(root)
            root.matrix_world = base
            for i in range(2):
                for j in range(3):
                    t = bpy.data.objects.new(f"Job_Prusa_{no:02d}_Tag_{i}{j}", me)
                    col.objects.link(t)
                    t.parent = root
                    cx, cy = NX + 0.006 - 0.064 + i * 0.064, NY - 0.03 + j * 0.03   # nozzle over tag (1, 1)'s lettering
                    t.matrix_parent_inverse.identity()
                    t.location = (cx, cy, z)


def srm20_job(col):
    """SRM-20 1 isolation-milling a small ATtiny board on the copper blank (blank x 0.13-0.27, y 0.15-0.27 in srm20()):
    milled isolation paths show the FR1 substrate; the back strip under the end mill is still to come."""
    f = frame("Roland_SRM20_1")
    if not f:
        return
    p = Part()
    fr1 = mat("FR1_Substrate", "#B07A3E", 0.75)
    z = 0.117
    cut = lambda x0, y0, x1, y1: rect_lines(p, fr1, x0, y0, x1, y1, z, w=0.0009)
    X0, Y0 = 0.165, 0.205                                          # board origin; the end mill is on its back-right outline
    cut(X0, Y0, X0 + 0.07, Y0 + 0.05)                              # board outline (isolation round the edge)
    for i in range(4):                                             # SOIC-8: 2 rows of 4 pads
        for r in (0, 1):
            x = X0 + 0.022 + i * 0.00635
            y = Y0 + 0.018 + r * 0.011
            cut(x - 0.0012, y - 0.0018, x + 0.0012, y + 0.0018)
    for i in range(3):                                             # 2 x 3 ISP header
        for r in (0, 1):
            x, y = X0 + 0.052 + r * 0.00254 * 2, Y0 + 0.012 + i * 0.00254 * 2
            cut(x - 0.0016, y - 0.0016, x + 0.0016, y + 0.0016)
    for (x, y) in ((X0 + 0.010, Y0 + 0.040), (X0 + 0.018, Y0 + 0.040), (X0 + 0.010, Y0 + 0.008), (X0 + 0.018, Y0 + 0.008)):
        cut(x - 0.0018, y - 0.0012, x + 0.0018, y + 0.0012)        # LED + resistor 1206 pads
    for (x0, y0, x1, y1) in ((X0 + 0.014, Y0 + 0.010, X0 + 0.028, Y0 + 0.016), (X0 + 0.040, Y0 + 0.020, X0 + 0.050, Y0 + 0.014),
                             (X0 + 0.040, Y0 + 0.031, X0 + 0.056, Y0 + 0.024), (X0 + 0.020, Y0 + 0.031, X0 + 0.014, Y0 + 0.038)):
        for o in (-0.0011, 0.0011):                                # trace isolation both sides (L-shaped traces)
            line(p, fr1, x0, y0 + o, x1, y0 + o, z, 0.0009)
            line(p, fr1, x1 + o, y0, x1 + o, y1, z, 0.0009)
    for k in range(5):                                             # copper dust round the cutter
        p.cyl(mat("Copper_Dust", "#C98B5A", 0.6, metal=0.6), (0.225 + 0.008 * math.cos(k), 0.252 + 0.006 * math.sin(k * 2), z),
              (0.225 + 0.008 * math.cos(k), 0.252 + 0.006 * math.sin(k * 2), z + 0.0004), 0.004, seg=10)
    p.emit("Job_SRM20_1", col, *f)


def xtool_job(col):
    """xTool F1 Ultra engraving a slate coaster under the galvo (lens at w*0.45, d*0.45; slatted panel top 0.024)."""
    f = frame("xTool_F1_Ultra")
    if not f:
        return
    p = Part()
    slate = mat("Slate_Coaster", "#2E3135", 0.7)
    etch = mat("Slate_Etch", "#B9BCBF", 0.85)
    cx, cy, z = 0.273 * 0.45, 0.373 * 0.45, 0.024
    p.box(slate, cx - 0.05, cx + 0.05, cy - 0.05, cy + 0.05, z, z + 0.005, bevel=0.002)
    zt = z + 0.005
    for r in (0.042, 0.038):                                       # engraved double ring
        ring(p, etch, cx, cy, zt, r, w=0.0012, seg=48)
    for k in range(7):                                             # hex-tile motif, half engraved (raster in progress)
        a = 2 * math.pi * k / 6
        hx, hy = (cx, cy) if k == 6 else (cx + 0.016 * math.cos(a), cy + 0.016 * math.sin(a))
        if hy > cy + 0.012:
            continue
        p.cyl(etch, (hx, hy, zt), (hx, hy, zt + 0.0002), 0.0075, seg=6)
    red = mat("Laser_Pointer", "#FF2A2A", 0.3, emit=8.0)          # blue/red pointer spot on the work
    p.cyl(red, (cx, cy + 0.012, zt), (cx, cy + 0.012, zt + 0.0003), 0.0012, seg=10)
    p.emit("Job_xTool", col, *f)


def build():
    scene = bpy.context.scene
    col = bpy.data.collections.get("Jobs") or bpy.data.collections.new("Jobs")
    if col.name not in scene.collection.children:
        scene.collection.children.link(col)
    for o in list(col.objects):
        data = o.data
        bpy.data.objects.remove(o)
        if isinstance(data, bpy.types.Mesh) and data.users == 0:
            bpy.data.meshes.remove(data)
    bpy.context.view_layer.update()
    shopbot_job(col)
    glowforge_job(col)
    prusa_jobs(col)
    srm20_job(col)
    xtool_job(col)
    print("jobs built:", ", ".join(o.name for o in col.objects if o.parent is None))


build()

_lay = {}
exec(open(bpy.path.abspath("//scripts/layout_blender.py")).read(), _lay)
_lay["apply"]()
