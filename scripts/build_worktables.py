"""Main work-table area (replaces the colleague's six 0.87 x 1.6 m benches Component_237631*). Re-runnable
("WorkTables" collection). Model frame: +X = SSW, +Y = ESE.

Option 7b (Magnús 2026-11-25): four 2440 x 915 tables, each top one piece from a 2440 x 1220 board; the 305 rip of
every board goes back in: two strips side by side = a 610 platform under each standing table (4 boards, no waste).
All on locking castors (move and combine). Long side along y, in two lines:
  sitting  (0.75 m, 3 profile chairs per long side = 12 seats) on the hand-tool-wall side, x 23.03-23.945
  standing (1.10 m, European tall-table height: Icelandic adults avg ~181/168 cm, staff 185+; ~6 people each,
           610 platform at 0.20 m for stability + misc) on the print-farm side, x 26.47-27.38
  each line two tables end to end, y 23.20-25.64 / 25.74-28.18; ~1.45 m aisle between the lines, ~0.9 m to the
  hand-tool wall and the print farm, ~0.9 m to the mural cupboard, ~1.0 m to the felt dividers.
No low shelf under the sitting tables (chairs tuck in; Magnús). Props come from build_life.py, which must run after.
"""
import math
import random

import bpy
from mathutils import Matrix, Vector

HERE = bpy.path.abspath("//scripts/")
lib = {}
exec(open(HERE + "profile_furniture.py").read(), lib)
MAT = lib["materials"]()
_t = open(HERE + "build_textile.py").read()
tex = {}
exec(_t[:_t.index("\ndef build():")], tex)                         # chair()
rng = random.Random(42)

TL, TD = 2.44, 0.915                                               # one board minus the 305 rip
SIT_H, STAND_H, CASTOR_H = 0.75, 1.10, 0.11                           # standing = European Stehtisch 1.10 m (Magnús)
SIT_X, STAND_X = 23.4875, 26.9225                                  # line centres x
YS = (24.42, 26.96)                                                # table centres y
PLAT_Z, PLAT_W = 0.20, 0.305                                       # two 305 strips per platform
OLD = "Component_237631"                                           # colleague's benches


def clear_collection(name):
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    for o in list(col.objects):
        data = o.data
        bpy.data.objects.remove(o)
        if isinstance(data, bpy.types.Mesh) and data.users == 0:
            bpy.data.meshes.remove(data)
    return col


def table(h, platform):
    rubber = bpy.data.materials.get("Rubber_Black") or lib["simple_mat"]("Rubber_Black", "#151515", 0.8)
    steel = bpy.data.materials.get("Castor_Steel") or lib["simple_mat"]("Castor_Steel", "#B8BCC0", 0.35, metal=1.0)
    p, _ = lib["table_unit"](TL, TD, h, [0.0, TL - 0.04], lower=(), feet_h=CASTOR_H)
    for x in (0.02, TL - 0.02):                                    # locking castors under the legs
        for y in (0.02, TD - 0.02):
            p.box(steel, x - 0.03, x + 0.03, y - 0.03, y + 0.03, CASTOR_H - 0.012, CASTOR_H)
            p.box(steel, x - 0.006, x + 0.006, y - 0.025, y + 0.025, 0.03, CASTOR_H - 0.012)
            p.cyl(rubber, (x - 0.012, y, 0.05), (x + 0.012, y, 0.05), 0.05, seg=20)
            p.box(MAT["profile"], x + 0.012, x + 0.03, y - 0.02, y + 0.02, 0.07, 0.085)   # brake pedal
    if platform:
        tot = 2 * PLAT_W + 0.004
        y0 = (TD - tot) / 2
        for y in (0.0, TD - 0.04):                                 # 40x40 rails leg to leg, front and back
            p.profile(0.04, "x", 0.04, y, PLAT_Z - 0.018 - 0.04, TL - 0.08)
        for x in (0.0, TL - 0.04):                                 # end rails between the leg pairs
            p.profile(0.04, "y", x, 0.04, PLAT_Z - 0.018 - 0.04, TD - 0.08)
        p.profile(0.02, "y", TL / 2 - 0.01, 0.04, PLAT_Z - 0.018 - 0.02, TD - 0.08)   # mid support
        for k in range(2):
            ya = y0 + k * (PLAT_W + 0.004)
            lib["board"](p, 0.04, TL - 0.04, ya, ya + PLAT_W, PLAT_Z)
    return p


def build():
    col = clear_collection("WorkTables")
    for o in [o for o in bpy.data.objects if o.name.startswith(OLD)]:
        for k in (o, *o.children_recursive):
            k.hide_render = k.hide_viewport = True
    k = n = 0
    for cx, h, plat in ((SIT_X, SIT_H, False), (STAND_X, STAND_H, True)):
        for cy in YS:
            t = table(h, plat)
            loc, rot = lib["placement"](cx, cy, TL, TD, "-x")
            t.emit(f"WorkTable_{k}", col, loc, rot)
            if not plat:
                for side, r0 in ((-1, math.pi / 2), (1, -math.pi / 2)):     # chairs face the table
                    for j, dy in enumerate((-0.81, 0.0, 0.81)):
                        r = r0 + rng.uniform(-0.12, 0.12)
                        x = cx + side * (TD / 2 + rng.uniform(0.10, 0.22))
                        off = Matrix.Rotation(r, 4, "Z") @ Vector((-0.22, -0.22, 0))
                        tex["chair"]().emit(f"WorkChair_{k}_{side}_{j}", col, Vector((x, cy + dy, 0)) + off, r)
                        n += 1
            k += 1
    print("work tables built: %d tables, %d chairs" % (k, n))


build()

# Placements come from layout/layout.yaml (layout/README.md): built at this builder's coordinates, then moved there.
_lay = {}
exec(open(bpy.path.abspath("//scripts/layout_blender.py")).read(), _lay)
_lay["apply"]()
