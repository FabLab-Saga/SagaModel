"""Material storage in the CNC room, around the ShopBot's loading end. Re-runnable (collection "MaterialStorage").

- Sheet cart: rolling 40x40 profile cart for flat 1220x2440 stock (birch ply, MDF, acrylic) right in front of
  the ShopBot bed end (y 18.45), so sheets slide straight onto the bed. Top = breakdown surface.
- Offcut rack: vertical slots (20x20 dividers) against the side wall (x 25.74, y 15.2-16.7, short of the door
  at y 16.8), offcuts and half sheets standing on edge.
- Rod rack: two 40x40 wall posts with cantilever arms above the offcut rack: aluminium profile, threaded rod,
  dowels, PVC pipe.
"""
import random

import bpy
from mathutils import Vector

HERE = bpy.path.abspath("//scripts/")
lib = {}
exec(open(HERE + "profile_furniture.py").read(), lib)
MAT = lib["materials"]()
Part, mat = lib["Part"], lib["simple_mat"]
rng = random.Random(23)

WALL_X = 25.74                     # side wall of the CNC room end (faces -x)


def mats():
    acr = [mat(f"Acrylic_{n}", h, 0.06, coat=0.8) for n, h in (("Red", "#E03A3F"), ("Blue", "#1245DE"), ("Yellow", "#F2C200"),
                                                                ("Green", "#009967"), ("White", "#F2F2EE"), ("Black", "#111111"))]
    return dict(mdf=mat("MDF", "#B48C5C", 0.8), acr=acr, clear=mat("Acrylic_Smoke", "#9FB7C4", 0.05, coat=0.6),
                paper=mat("Sheet_Paper", "#EDEBE4", 0.9), steel=mat("Tool_Steel", "#B9BDC1", 0.25, metal=1.0),
                pvc=mat("PVC_Grey", "#8E9396", 0.45), caster=mat("Foot_Black", "#121212", 0.6))


def stack(p, x0, y0, z, w, d, layers):
    """Flat sheets, slightly misaligned; layers = [(material, thickness), ...] bottom-up."""
    for m, t in layers:
        dx, dy = rng.uniform(-0.012, 0.012), rng.uniform(-0.012, 0.012)
        p.box(m, x0 + dx, x0 + w + dx, y0 + dy, y0 + d + dy, z, z + t, bevel=0.0008)
        z += t
    return z


def sheet_cart(m, col, x0=22.35, y0=16.95):
    L, D, H = 2.55, 1.30, 0.80
    part, _ = lib["table_unit"](L, D, H, [0.0, L / 2 - 0.02, L - 0.04], lower=(0.20, 0.50), feet_h=0.11)
    loc, rot = lib["placement"](x0 + L / 2, y0 + D / 2, L, D, "+y")
    part.emit("SheetCart", col, loc, rot)
    p = Part()
    for x in (x0 + 0.02, x0 + L / 2, x0 + L - 0.02):                    # braked swivel casters instead of feet
        for y in (y0 + 0.02, y0 + D - 0.02):
            p.box(MAT["zinc"], x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.095, 0.11)
            p.cyl(m["caster"], (x - 0.012, y, 0.045), (x + 0.012, y, 0.045), 0.045, seg=20)
    sx, sy, sw, sd = x0 + 0.06, y0 + 0.05, 2.44, 1.22
    ply = [(MAT["ply"], 0.018)] * 5 + [(MAT["ply"], 0.012)] * 4 + [(MAT["ply"], 0.009)] * 3
    stack(p, sx, sy, 0.20, sw, sd, ply)                                  # birch ply, lower level
    stack(p, sx, sy, 0.50, sw, sd, [(m["mdf"], 0.018)] * 4 + [(m["mdf"], 0.012)] * 3 + [(m["mdf"], 0.006)] * 4)
    acr = [(m["paper"], 0.004)] + [(rng.choice(m["acr"]), 0.003) for _ in range(5)] + [(m["clear"], 0.005)] * 2
    stack(p, x0 + 0.10, y0 + 0.08, 0.80 + 0.025, 1.22, 0.61, acr)       # acrylic half sheets on top
    stack(p, x0 + 1.40, y0 + 0.20, 0.80 + 0.025, 1.0, 0.80, [(MAT["ply"], 0.009), (MAT["ply"], 0.006)])
    p.emit("SheetCart_Stock", col, Vector((0, 0, 0)))


def offcut_rack(m, col, y0=15.20, y1=16.70, depth=0.50, h=1.30):
    x1, x0 = WALL_X - 0.01, WALL_X - 0.01 - depth
    p = Part()
    for x in (x0, x1 - 0.04):                                            # base + top frame, 40x40
        p.profile(0.04, "y", x, y0, 0.035, y1 - y0)
        p.profile(0.04, "y", x, y0, h - 0.04, y1 - y0)
        for y in (y0, y1 - 0.04):
            p.profile(0.04, "z", x, y, 0.035, h - 0.075)
            lib["foot"](p, x + 0.02, y + 0.02)
    p.box(MAT["ply"], x0, x1, y0, y1, 0.075, 0.093, bevel=0.001)          # ply floor of the slots
    slots = [y0 + 0.04 + k * 0.235 for k in range(7)]
    for ys in slots[1:-1]:                                               # 20x20 dividers front and back
        for x in (x0, x1 - 0.06):
            p.profile(0.02, "z", x, ys, 0.093, h - 0.133)
        p.profile(0.02, "x", x0 + 0.02, ys, h - 0.06, depth - 0.08)
    stock = [MAT["ply"], MAT["ply"], m["mdf"], m["clear"]] + m["acr"]
    for a, b in zip(slots, slots[1:]):
        y = a + 0.02
        for _ in range(rng.randint(3, 6)):
            t = rng.choice((0.003, 0.006, 0.009, 0.012, 0.018))
            if y + t > b - 0.01:
                break
            w, hh = rng.uniform(0.25, 0.62), rng.uniform(0.30, 1.15)
            xa = x1 - 0.02 - w + rng.uniform(-0.06, 0.12)
            p.box(rng.choice(stock), xa, xa + w, y, y + t, 0.093, 0.093 + hh, bevel=0.0008)
            y += t + rng.uniform(0.002, 0.02)
    p.emit("OffcutRack", col, Vector((0, 0, 0)))


def rod_rack(m, col, y0=15.30, y1=16.60, z0=1.55):
    p = Part()
    posts = (y0 + 0.15, y1 - 0.19)
    for y in posts:
        p.profile(0.04, "z", WALL_X - 0.05, y, z0, 0.95)
        for k in range(3):                                               # cantilever arms, upturned tips
            z = z0 + 0.12 + k * 0.30
            p.profile(0.02, "x", WALL_X - 0.05 - 0.38, y + 0.01, z, 0.38)
            p.box(MAT["zinc"], WALL_X - 0.44, WALL_X - 0.42, y + 0.01, y + 0.03, z + 0.02, z + 0.06)
    L = y1 - y0 + 0.30
    ya = y0 - 0.15
    z = z0 + 0.12 + 0.02                                                 # lowest arm: aluminium profile lengths
    for i in range(5):
        p.profile(0.02 if i % 2 else 0.04, "y", WALL_X - 0.40 + i * 0.065, ya + rng.uniform(0, 0.1), z, L - rng.uniform(0, 0.25))
    z = z0 + 0.42 + 0.02                                                 # middle: threaded rod + steel tube
    for i in range(7):
        r = rng.choice((0.004, 0.005, 0.006, 0.008))
        x = WALL_X - 0.40 + i * 0.045
        p.cyl(m["steel"], (x, ya + rng.uniform(0, 0.1), z + r), (x, ya + L - rng.uniform(0, 0.2), z + r), r, seg=10)
    z = z0 + 0.72 + 0.02                                                 # top: dowels + PVC pipe
    for i in range(6):
        r = rng.choice((0.006, 0.009, 0.012, 0.016))
        x = WALL_X - 0.40 + i * 0.055
        p.cyl(MAT["ply"] if i < 4 else m["pvc"], (x, ya + rng.uniform(0, 0.1), z + r), (x, ya + L - rng.uniform(0, 0.2), z + r), r, seg=14)
    p.emit("RodRack", col, Vector((0, 0, 0)))


def build():
    scene = bpy.context.scene
    col = bpy.data.collections.get("MaterialStorage") or bpy.data.collections.new("MaterialStorage")
    if col.name not in scene.collection.children:
        scene.collection.children.link(col)
    for o in list(col.objects):
        data = o.data
        bpy.data.objects.remove(o)
        if isinstance(data, bpy.types.Mesh) and data.users == 0:
            bpy.data.meshes.remove(data)
    m = mats()
    sheet_cart(m, col)
    offcut_rack(m, col)
    rod_rack(m, col)
    print("material storage built")


build()
