"""Craft zone along the NNE glazing + double-sided spine divider. Re-runnable.

Craft zone (replaces placeholder Component_1489559 and friends), model frame +X = SSW:
  - north of the tool-wall row (y 30.25-34.15): craft counter A (0.90 m, standing) with
    2x Cricut + Mayku, craft counter B (0.75 m, seated) with Brother sewing, embroidery,
    overlocker and two profile stools; coloured bins below.
  - south of the row (y 26.5-28.8): 2x Roland vinyl cutter on rolling profile stands
    with vinyl-roll racks (mobile; the aisle to the benches is ~0.75 m).
Spine (x 27.62-28.22, y 31.55-36.65): double-sided profile shelving, birch-ply spine;
  bank/workshop side (-x) = SAMLA boxes, lounge side (+x) = books, plants, display.
"""
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = bpy.path.abspath("//scripts/")
lib = {}
exec(open(HERE + "profile_furniture.py").read(), lib)
MAT = lib["materials"]()
_m = open(HERE + "build_machines.py").read()
mach = {}
exec(_m[:_m.index("\ndef build():")], mach)
mach["materials"]()
_b = open(HERE + "build_bank_lounge.py").read()
bank = {}
exec(_b[:_b.index("\ndef build():")], bank)                # SAMLA boxes, fill helpers, put(), clear_collection()
Part = lib["Part"]
mat = lib["simple_mat"]
rng = random.Random(11)

LEAF = mat("Plant_Leaf", "#3E6B35", 0.55)
POT = mat("Plant_Pot", "#D9D4CB", 0.6)
BOOKS = MAT["bins"] + [mat("Book_Cream", "#E9E1CF", 0.6), mat("Book_Navy", "#22314F", 0.6), mat("Book_Black", "#1C1C1C", 0.6)]


def stool(h=0.62):
    p = Part()
    s = 0.36
    for x in (0.0, s - 0.02):
        for y in (0.0, s - 0.02):
            p.profile(0.02, "z", x, y, 0.035, h - 0.06)
            lib["foot"](p, x + 0.01, y + 0.01)
    for z in (0.20, h - 0.045):
        for y in (0.0, s - 0.02):
            p.profile(0.02, "x", 0.02, y, z, s - 0.04)
        for x in (0.0, s - 0.02):
            p.profile(0.02, "y", x, 0.02, z, s - 0.04)
    p.box(MAT["ply"], -0.01, s + 0.01, -0.01, s + 0.01, h - 0.025, h, bevel=0.003)
    return p


def vinyl_stand(w=0.95, d=0.50, h=0.82):
    """Rolling profile stand for a vinyl cutter, roll rack below."""
    p, _ = lib["table_unit"](w, d, h, [0.0, w - 0.04], lower=(0.20,), feet_h=0.08)
    for x in (0.02, w - 0.02):                                          # castors replace the feet
        for y in (0.02, d - 0.02):
            p.cyl(MAT["foot"], (x - 0.012, y, 0.035), (x + 0.012, y, 0.035), 0.035, seg=16)
    for i, y in enumerate((0.12, 0.25, 0.38)):                          # vinyl rolls on the lower shelf
        for j in range(2):
            p.cyl(MAT["bins"][(i * 2 + j) % 6], (0.06 + j * 0.44, y, 0.26), (0.06 + j * 0.44 + 0.40, y, 0.26), 0.045, seg=20)
    return p


def books_and_plants(part, x0, x1, depth, z, clear):
    """Fill a lounge-side shelf: runs of books, a plant or a display object."""
    x = x0 + 0.03
    while x < x1 - 0.12:
        r = rng.random()
        if r < 0.22 and x + 0.26 < x1:                                  # plant
            part.cyl(POT, (x + 0.12, depth / 2, z), (x + 0.12, depth / 2, z + 0.16), 0.08, seg=20)
            bmesh.ops.create_icosphere(part.bm(LEAF), subdivisions=2, radius=min(0.15, clear * 0.35),
                                       matrix=Matrix.Translation((x + 0.12, depth / 2, z + 0.16 + min(0.13, clear * 0.3))))
            x += 0.28
        elif r < 0.32 and x + 0.22 < x1:                                # display: a 3D-printed object on a block
            part.box(MAT["ply"], x, x + 0.18, 0.04, 0.22, z, z + 0.05, bevel=0.003)
            bmesh.ops.create_icosphere(part.bm(rng.choice(MAT["bins"])), subdivisions=1, radius=0.07,
                                       matrix=Matrix.Translation((x + 0.09, 0.13, z + 0.12)))
            x += 0.24
        else:                                                           # run of books
            n = rng.randint(5, 14)
            for _ in range(n):
                t = rng.uniform(0.018, 0.045)
                if x + t > x1 - 0.03:
                    break
                h = min(clear - 0.03, rng.uniform(0.18, 0.30))
                dd = rng.uniform(0.15, 0.22)
                part.box(rng.choice(BOOKS), x, x + t, 0.02, 0.02 + dd, z, z + h, bevel=0.0015)
                x += t + 0.001
            x += 0.05


def build():
    col = bank["clear_collection"]("CraftZone")
    sp = bank["clear_collection"]("Spine")
    # placeholders: NNE-glazing run + boards, spine units
    names = ["Component_1489559", "Component_1491551", "Component_680686", "Component_680688", "Component_289763", "osb st2.002"]
    for o in bpy.data.objects["ROOT"].children:
        if o.name.startswith(("Component_1484326", "Component_240712", "Plywood_4x8")):
            pts = [k.matrix_world @ Vector(c) for k in (o, *o.children_recursive) if k.type == "MESH" for c in k.bound_box]
            if pts and (max(p.x for p in pts) < 21.2 or 27.5 < min(p.x for p in pts) < 28.4):
                names.append(o.name)                                    # NNE-glazing run, loose sheets, spine bits
    hidden = 0
    for n in names:
        o = bpy.data.objects.get(n)
        if o:
            for k in (o, *o.children_recursive):
                k.hide_render = k.hide_viewport = True
            hidden += 1

    put = bank["put"]
    XG = 20.90                                                         # just inside the NNE glazing frames
    # ---- craft counter A (standing) and B (seated), north of the tool-wall row
    for name, y0, L, H in (("CraftCounter_A", 30.25, 1.92, 0.90), ("CraftCounter_B", 32.22, 1.92, 0.75)):
        part, _ = lib["table_unit"](L, 0.70, H, [0.0, L - 0.04], lower=(0.16,))
        loc, rot = lib["placement"](XG + 0.35, y0 + L / 2, L, 0.70, "+x")
        part.emit(name, col, loc, rot)
        b = Part()
        for j in range(4):
            lib["bin_box"](b, MAT["bins"][(j + (0 if H > 0.8 else 3)) % 6], 0.06 + j * 0.46, 0.08, 0.16, w=0.42, d=0.40, h=0.24)
        b.emit(name + "_Bins", col, loc, rot)
        if H > 0.8:
            put(mach["cricut"](), "Cricut_Maker_1", col, loc, rot, (0.42, 0.25), H, 0.60, 0.179)
            put(mach["cricut"](), "Cricut_Maker_3", col, loc, rot, (1.12, 0.25), H, 0.60, 0.179)
            put(mach["mayku"](), "Mayku_FormBox", col, loc, rot, (1.66, 0.36), H, 0.274, 0.466)
        else:
            put(mach["sewing"](), "Brother_Sewing", col, loc, rot, (0.40, 0.30), H, 0.42, 0.20)
            put(mach["sewing"](0.50, 0.24, 0.32), "Brother_Embroidery", col, loc, rot, (1.05, 0.30), H, 0.50, 0.24)
            put(mach["overlock"](), "Overlock", col, loc, rot, (1.66, 0.32), H, 0.33, 0.28)
            for i, lx in enumerate((0.40, 1.05)):
                c = lib["to_world"](loc, rot, (lx, -0.35, 0))
                stool().emit(f"Stool_{i + 1}", col, Vector((c.x - 0.18, c.y - 0.18, 0)))
    # ---- vinyl cutters on rolling stands, south of the tool-wall row
    for i, yc in enumerate((27.05, 28.20)):
        loc, rot = lib["placement"](XG + 0.25, yc, 0.95, 0.50, "+x")
        vinyl_stand().emit(f"VinylStand_{i + 1}", col, loc, rot)
        put(mach["vinyl"](), f"Roland_VinylCutter_{i + 1}", col, loc, rot, (0.475, 0.22), 0.82, 0.851, 0.310)

    # ---- spine: two back-to-back 0.30 m shelf units with a birch-ply spine between
    lv = [0.10, 0.48, 0.86, 1.24, 1.62, 2.00]
    bays = [1.18] * 4
    for side, facing, xc in (("Boxes", "-x", 27.62 + 0.15), ("Lounge", "+x", 28.22 - 0.15)):
        part, slots, L = lib["shelf_unit"](bays, 0.30, 2.42, lv)
        loc, rot = lib["placement"](xc, 31.55 + L / 2, L, 0.30, facing)
        part.emit(f"Spine_{side}_Shelving", sp, loc, rot)
        fill = Part()
        if side == "Boxes":
            fill = bank["fill_unit"](slots, lv, 2.42, 0.30, big=False)
        else:
            tops = lv + [2.42]
            for (bi, li), (xa, xb, _, _, zt) in slots.items():
                books_and_plants(fill, xa, xb, 0.30, zt, tops[li + 1] - zt - 0.06)
        fill.emit(f"Spine_{side}_Contents", sp, loc, rot)
    spine = Part()
    spine.box(MAT["ply"], 27.913, 27.929, 31.57, 31.55 + 4 * 1.22 + 0.04 - 0.02, 0.05, 2.40)
    spine.emit("Spine_Panel", sp, Vector((0, 0, 0)))
    return hidden


h = build()
print("craft zone + spine built; placeholders hidden:", h)
