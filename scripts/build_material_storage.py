"""Material storage in the CNC room (user, 2026-10-08: no big sheet table - store material VERTICALLY and use the
3.93 m height; option A = upright sheet rack). Re-runnable (collection "MaterialStorage").

Layout (my design, in the loading zone between the double loading door, y 15.08, and the ShopBot's loading end, y 17.90):
- Upright board rack in the ex-WC corner against the hallway wall (x 24.40-25.70, y 15.15-16.70): full 2440x1220
  boards standing on their short edge (2.44 m tall) in 10 slots between 20x20 dividers, faces across the slots, so one
  person slides a board out sideways into the free loading zone, turns it and lays it on the ShopBot bed. Ply, MDF,
  OSB, XPS foam, HDPE. Above it (deck at 2.60 m): offcut boxes and foam blocks, with cantilever arms at 2.95/3.30 m
  for rods, dowels and aluminium profile (cut lengths, kept clear of the window wall and the hallway door).
- Offcut cart: low rolling slot cart (0.95 x 0.50 x 0.95) in the window corner by the dust collector.
- 2-step safety step by the rack for the top storage.
Board path: loading door (x 22.40-24.72) -> loading zone -> ShopBot bed end, all in a straight line.
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
                pvc=mat("PVC_Grey", "#8E9396", 0.45), caster=mat("Foot_Black", "#121212", 0.6),
                osb=osb_mat(), xps=mat("XPS_Blue", "#7FA9D6", 0.8), xps_pink=mat("XPS_Pink", "#E9A6B4", 0.8),
                hdpe=mat("HDPE_White", "#ECEDEA", 0.35))


def osb_mat():
    """OSB from the Poly Haven oriented_strand_board set (CC0), box-mapped."""
    m = bpy.data.materials.get("OSB") or bpy.data.materials.new("OSB")
    m.use_nodes = True
    nt = m.node_tree
    if any(n.type == "TEX_IMAGE" for n in nt.nodes):
        return m
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    import glob
    import os
    d = bpy.path.abspath("//assets/polyhaven/oriented_strand_board/")
    diff = (glob.glob(os.path.join(d, "**", "*diff*"), recursive=True) or [None])[0]
    if diff:
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(diff, check_existing=True)
        t.projection, t.projection_blend = "BOX", 0.2
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (0.8, 0.8, 0.8)
        nt.links.new(nt.nodes.new("ShaderNodeTexCoord").outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs[0], t.inputs["Vector"])
        nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    else:
        b.inputs["Base Color"].default_value = lib["lin"]("#C49A5E")
    b.inputs["Roughness"].default_value = 0.8
    return m


def stack(p, x0, y0, z, w, d, layers):
    """Flat sheets, slightly misaligned; layers = [(material, thickness), ...] bottom-up."""
    for m, t in layers:
        dx, dy = rng.uniform(-0.012, 0.012), rng.uniform(-0.012, 0.012)
        p.box(m, x0 + dx, x0 + w + dx, y0 + dy, y0 + d + dy, z, z + t, bevel=0.0008)
        z += t
    return z


RACK = dict(x0=24.40, x1=25.70, y0=15.15, y1=16.70)


def board_rack(m, col):
    x0, x1, y0, y1 = RACK["x0"], RACK["x1"], RACK["y0"], RACK["y1"]
    TOP, DECK = 2.56, 2.60
    p = Part()
    for x in (x0, x1 - 0.04):                                        # 40x40 frame: corner + mid posts
        for y in (y0, (y0 + y1) / 2 - 0.02, y1 - 0.04):
            p.profile(0.04, "z", x, y, 0.035, TOP - 0.035)
            lib["foot"](p, x + 0.02, y + 0.02)
        p.profile(0.04, "y", x, y0 + 0.04, 0.035, y1 - y0 - 0.08)      # base rails
        p.profile(0.04, "y", x, y0 + 0.04, TOP - 0.04, y1 - y0 - 0.08)  # top rails
    for y in (y0, y1 - 0.04):
        p.profile(0.04, "x", x0 + 0.04, y, TOP - 0.04, x1 - x0 - 0.08)
    p.box(MAT["ply"], x0, x1, y0, y1, 0.075, 0.093, bevel=0.001)      # slot floor
    p.box(MAT["ply"], x0 - 0.01, x1, y0 - 0.01, y1 + 0.01, TOP, DECK, bevel=0.002)   # top deck
    n = 10
    edges = [y0 + 0.04 + k * (y1 - y0 - 0.08) / n for k in range(n + 1)]
    for ys in edges[1:-1]:                                            # slot dividers, front + back, to 2.30 m
        for x in (x0, x1 - 0.06):
            p.profile(0.02, "z", x + 0.02, ys - 0.01, 0.093, 2.20)
        for z in (1.10, 2.25):
            p.profile(0.02, "x", x0 + 0.04, ys - 0.01, z, x1 - x0 - 0.10)
    osb = m["osb"]
    fills = [  # (material, thickness, count) per slot
        [(MAT["ply"], 0.018, 6)], [(MAT["ply"], 0.012, 6), (MAT["ply"], 0.009, 3)], [(MAT["ply"], 0.006, 8), (MAT["ply"], 0.004, 4)],
        [(m["mdf"], 0.018, 5)], [(m["mdf"], 0.012, 5), (m["mdf"], 0.006, 4)], [(osb, 0.015, 5)], [(osb, 0.011, 3)],
        [(m["xps"], 0.05, 2)], [(m["hdpe"], 0.012, 3), (m["hdpe"], 0.006, 2)], [(MAT["ply"], 0.018, 2)]]
    BW, BH = 1.22, 2.44
    for k, (a, b) in enumerate(zip(edges, edges[1:])):
        y = a + 0.004
        for mm, t, cnt in fills[k]:
            for _ in range(cnt):
                if y + t > b - 0.012:
                    break
                xa = x1 - 0.045 - BW + rng.uniform(-0.03, 0.0)
                h = BH if k != 9 else rng.uniform(1.1, 1.6)              # last slot: part sheets
                p.box(mm, xa, xa + BW, y, y + t, 0.093, 0.093 + h, bevel=0.0008)
                y += t + rng.uniform(0.0005, 0.004)
    # top storage: offcut boxes + foam blocks on the deck, rods/profile on cantilever arms above
    bx = mat("Box_Birch_Crate", "#CDB48C", 0.7)
    for i, (ya, yb) in enumerate(((y0 + 0.03, y0 + 0.50), (y0 + 0.55, y0 + 1.02))):
        p.box(bx, x0 + 0.05, x0 + 0.60, ya, yb, DECK, DECK + 0.30, bevel=0.004)
        for j in range(4):
            p.box(rng.choice([MAT["ply"], m["mdf"], osb]), x0 + 0.10 + j * 0.11, x0 + 0.115 + j * 0.11, ya + 0.05,
                  yb - 0.05, DECK + 0.02, DECK + 0.30 + rng.uniform(0.02, 0.12))
    p.box(m["xps"], x0 + 0.70, x1 - 0.10, y1 - 0.62, y1 - 0.05, DECK, DECK + 0.15)
    p.box(m["xps_pink"], x0 + 0.72, x1 - 0.14, y1 - 0.60, y1 - 0.08, DECK + 0.15, DECK + 0.25)
    WALL = WALL_X - 0.01
    for y in (y0 + 0.20, y1 - 0.24):                                  # wall posts + arms
        p.profile(0.04, "z", WALL - 0.04, y, DECK + 0.02, 0.88)
        for z in (2.95, 3.30):
            p.profile(0.02, "x", WALL - 0.04 - 0.55, y + 0.01, z, 0.55)
            p.box(MAT["zinc"], WALL - 0.61, WALL - 0.59, y + 0.01, y + 0.03, z + 0.02, z + 0.06)
    L, ya = y1 - y0 - 0.10, y0 + 0.05
    for i in range(6):                                                # aluminium profile lengths
        p.profile(0.02 if i % 2 else 0.04, "y", WALL - 0.56 + i * 0.07, ya + rng.uniform(0, 0.08), 2.97, L - rng.uniform(0, 0.25))
    for i in range(9):                                                # threaded rod, dowels, PVC pipe
        r = rng.choice((0.005, 0.008, 0.012, 0.016))
        x = WALL - 0.56 + i * 0.055
        mm = m["steel"] if i < 3 else (MAT["ply"] if i < 7 else m["pvc"])
        p.cyl(mm, (x, ya + rng.uniform(0, 0.08), 3.32 + r), (x, ya + L - rng.uniform(0, 0.2), 3.32 + r), r, seg=12)
    p.emit("BoardRack", col, Vector((0, 0, 0)))


def offcut_cart(m, col, x0=20.88, y0=15.15, L=0.95, D=0.50, h=0.95):
    """Low rolling slot cart for offcuts, long side along y, in the window corner by the collector."""
    x1, y1 = x0 + D, y0 + L
    p = Part()
    for x in (x0, x1 - 0.04):
        p.profile(0.04, "y", x, y0, 0.10, L)
        p.profile(0.04, "y", x, y0, h - 0.04, L)
        for y in (y0, y1 - 0.04):
            p.profile(0.04, "z", x, y, 0.10, h - 0.14)
            p.box(MAT["zinc"], x - 0.01, x + 0.05, y - 0.01, y + 0.05, 0.085, 0.10)
            p.cyl(m["caster"], (x + 0.008, y + 0.02, 0.045), (x + 0.032, y + 0.02, 0.045), 0.045, seg=20)
    p.box(MAT["ply"], x0, x1, y0, y1, 0.14, 0.158, bevel=0.001)
    slots = [y0 + 0.04 + k * (L - 0.08) / 5 for k in range(6)]
    for ys in slots[1:-1]:
        for x in (x0, x1 - 0.04):
            p.profile(0.02, "z", x + 0.01, ys, 0.158, h - 0.20)
    stock = [MAT["ply"], MAT["ply"], m["mdf"], m["osb"], m["hdpe"]]
    for a, b in zip(slots, slots[1:]):
        y = a + 0.02
        for _ in range(rng.randint(3, 6)):
            t = rng.choice((0.006, 0.009, 0.012, 0.018))
            if y + t > b - 0.01:
                break
            w, hh = rng.uniform(0.20, 0.44), rng.uniform(0.25, 0.95)
            xa = x0 + 0.03 + rng.uniform(0, D - 0.06 - w)
            p.box(rng.choice(stock), xa, xa + w, y, y + t, 0.158, 0.158 + hh, bevel=0.0008)
            y += t + rng.uniform(0.002, 0.02)
    p.emit("OffcutCart", col, Vector((0, 0, 0)))


def step_stool(m, col, x0=24.02, y0=15.70):
    """2-step safety step (0.50 high) for the storage on top of the board rack."""
    p = Part()
    yel = mat("Step_Yellow", "#F2C200", 0.5)
    p.box(yel, x0, x0 + 0.30, y0, y0 + 0.45, 0.24, 0.27, bevel=0.005)
    p.box(yel, x0, x0 + 0.30, y0 + 0.20, y0 + 0.45, 0.47, 0.50, bevel=0.005)
    for x in (x0 + 0.01, x0 + 0.27):
        p.box(m["caster"], x, x + 0.02, y0, y0 + 0.45, 0.0, 0.24)
        p.box(m["caster"], x, x + 0.02, y0 + 0.20, y0 + 0.45, 0.27, 0.47)
    p.emit("StepStool", col, Vector((0, 0, 0)))


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
    board_rack(m, col)
    offcut_cart(m, col)
    step_stool(m, col)
    print("material storage built")


build()

# Placements come from layout/layout.yaml (layout/README.md): built at this builder's coordinates, then moved there.
_lay = {}
exec(open(bpy.path.abspath("//scripts/layout_blender.py")).read(), _lay)
_lay["apply"]()
