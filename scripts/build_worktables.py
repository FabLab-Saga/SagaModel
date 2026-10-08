"""Main work-table area (replaces the colleague's six 0.87 x 1.6 m benches Component_237631*). Re-runnable
("WorkTables" collection). Model frame: +X = SSW, +Y = ESE.

2 x 2 grid of profile work tables, 1.8 x 0.9 x 0.75 m (black 40x40 legs/apron, birch top, no low shelf so chairs tuck in), long side
along x, two profile chairs (build_textile.chair) per long side = 16 seats.
  columns x 22.6-24.4 / 25.9-27.7 -> 1.5 m central aisle (table ends), ~1.0 m to the glass tool wall / vinyl
                                      stands, 1.2 m to the print farm
  rows    y 24.3-25.2 / 27.0-27.9 -> 1.8 m between rows (chairs back to back + a walkway), chairs >= 0.65 m from
                                      the CNC-room window wall, ~1.3 m from the felt wall
Props (cutting mats, laptops, offcuts, drills) come from build_life.py, which must run after this.
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

TL, TD, TH = 1.80, 0.90, 0.75
COLS = (23.50, 26.80)                                              # table centres x
ROWS = (24.75, 27.45)                                              # table centres y
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


def build():
    col = clear_collection("WorkTables")
    for o in [o for o in bpy.data.objects if o.name.startswith(OLD)]:
        for k in (o, *o.children_recursive):
            k.hide_render = k.hide_viewport = True
    k = 0
    for ry_, cy in enumerate(ROWS):
        for cx_, cx in enumerate(COLS):
            t, _ = lib["table_unit"](TL, TD, TH, [0.0, TL - 0.04], lower=())     # no low shelf: chairs tuck in
            loc, rot = lib["placement"](cx, cy, TL, TD, "-y")
            t.emit(f"WorkTable_{k}", col, loc, rot)
            for side, face in ((-1, math.pi), (1, 0.0)):           # chairs face the table
                for j, dx in enumerate((-0.45, 0.45)):
                    x = cx + dx + rng.uniform(-0.05, 0.05)
                    y = cy + side * (TD / 2 + rng.uniform(0.10, 0.26))
                    r = face + rng.uniform(-0.15, 0.15)
                    off = Matrix.Rotation(r, 4, "Z") @ Vector((-0.22, -0.22, 0))
                    tex["chair"]().emit(f"WorkChair_{k}_{side}_{j}", col, Vector((x, y, 0)) + off, r)
            k += 1
    print("work tables built: %d tables, %d chairs" % (k, 4 * k))


build()
