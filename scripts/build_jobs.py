"""Machines at work (branch alternate-ideas, 2026-11-26; my design on Magnús's go-ahead to iterate): jobs in progress
on the machines, tied to the projects on the work tables, so the lab reads as used rather than a showroom. Re-runnable
("Jobs" collection). Each job is built in its machine's local frame and placed on the machine's current pose, so it
must run AFTER the machine builders (machines, print farm, laser room); layout.yaml carries each job as an `on:` item.

- ShopBot: a 2440 x 1220 x 18 birch sheet screwed to the spoilboard, mid-way through the CNC-stool nest that is being
  dry-fitted on work table 2: six seats cut, the leg row being cut under the spindle, the rest still to come.
- Glowforge Pro HD 1: 3 mm ply on the crumb tray with the finger-joint box (work table 0's laser-cut box) cut out and
  its lid engraving in progress; the head carriage over it.
- Prusa MK3S+ 01/03/04/06: one print each in its own filament - a project enclosure for the electronics table (half
  printed), a spiral vase (half), a pencil holder (half) next to finished Fab Lab key tags, and a finished batch of
  hex tiles for the art wall.
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
    BEDZ, NX, NY = 0.064, 0.245, 0.24                                # PEI top, nozzle x/y (prusa(): ex + 0.035, fy - 0.07)
    H = 0.150 - BEDZ                                                  # nozzle tip height above the sheet
    for no, fil, kind in ((1, "Orange", "enclosure"), (3, "Green", "vase"), (4, "Yellow", "holder"), (6, "Blue", "hex")):
        f = frame(f"Prusa_MK3S_{no:02d}")
        if not f:
            continue
        m = bpy.data.materials.get(f"Filament_{fil}") or mat(f"Filament_{fil}", "#888888", 0.4)
        inner = mat(f"Print_Shadow_{fil}", "#1E1E1E", 0.8)
        p = Part()
        z = BEDZ
        if kind == "enclosure":                                     # 90 x 60 box shell, walls 2 mm, half printed
            w, d, t, h = 0.09, 0.06, 0.002, H - 0.0004
            p.box(m, NX - w / 2, NX + w / 2, NY - d / 2, NY + d / 2, z, z + 0.002)            # floor
            for a, b, c, e in ((-w / 2, w / 2, -d / 2, -d / 2 + t), (-w / 2, w / 2, d / 2 - t, d / 2),
                               (-w / 2, -w / 2 + t, -d / 2, d / 2), (w / 2 - t, w / 2, -d / 2, d / 2)):
                p.box(m, NX + a, NX + b, NY + c, NY + e, z, z + h)
            for sx in (-1, 1):                                        # screw bosses
                for sy in (-1, 1):
                    p.cyl(m, (NX + sx * 0.036, NY + sy * 0.021, z), (NX + sx * 0.036, NY + sy * 0.021, z + h), 0.004, seg=12)
        elif kind == "vase":
            p.cyl(m, (NX, NY, z), (NX, NY, z + H - 0.0004), 0.042, seg=48)
            p.cyl(inner, (NX, NY, z + H - 0.0004), (NX, NY, z + H - 0.0002), 0.0405, seg=48)
        elif kind == "holder":
            p.cyl(m, (NX, NY, z), (NX, NY, z + H - 0.0004), 0.036, seg=6)
            p.cyl(inner, (NX, NY, z + H - 0.0004), (NX, NY, z + H - 0.0002), 0.033, seg=6)
            for k in range(4):                                       # finished key tags beside it
                tx, ty = 0.15 + k * 0.03, 0.15
                p.box(m, tx, tx + 0.022, ty, ty + 0.045, z, z + 0.003, bevel=0.0008)
        else:                                                        # finished batch of art-wall hex tiles
            for i in range(4):
                for j in range(3):
                    cx = 0.165 + i * 0.056 + (0.028 if j % 2 else 0.0)
                    cy = 0.16 + j * 0.05
                    p.cyl(m, (cx, cy, z), (cx, cy, z + 0.008 + 0.004 * ((i + j) % 3)), 0.027, seg=6)
        p.emit(f"Job_Prusa_{no:02d}", col, *f)


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
    print("jobs built:", ", ".join(o.name for o in col.objects if o.parent is None))


build()

_lay = {}
exec(open(bpy.path.abspath("//scripts/layout_blender.py")).read(), _lay)
_lay["apply"]()
