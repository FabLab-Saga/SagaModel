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
import math
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


PLANT_SPOTS = []                                     # (placement, local x, local y, z, max height)

COVERS = ["#2E3A4F", "#7A2E2A", "#C9B48A", "#3F5A45", "#1F1F1F", "#E8E2D2", "#8C6A3E", "#5B6E7F", "#A33B33",
          "#D9C7A3", "#304B6B", "#6B5B4B", "#B8A27A", "#43403B", "#9AA3A8", "#E03A3F", "#1245DE"]
PAGES = mat("Book_Pages", "#EDE6D3", 0.8)
SPINE_INK = [mat("Book_Foil_Gold", "#C9A35A", 0.3, metal=1.0), mat("Book_Label_Cream", "#EFE8D6", 0.6),
             mat("Book_Ink_Black", "#141414", 0.5), mat("Book_Foil_Silver", "#C8CBCE", 0.3, metal=1.0)]


def cover_mat(h):
    return mat("Book_" + h[1:], h, rng.uniform(0.45, 0.7))


def book(part, x, y, z, t, h, d, tilt=0.0):
    """Hard-cover book on its tail, spine to the front; tilt leans it towards +x."""
    m = cover_mat(rng.choice(COVERS))
    marks = [(part.bm(mm), len(part.bm(mm).verts)) for mm in [m, PAGES] + SPINE_INK]
    part.box(m, x, x + t, y, y + d, z, z + h, bevel=0.0015)
    part.box(PAGES, x + 0.002, x + t - 0.002, y + 0.004, y + d + 0.0008, z + 0.003, z + h + 0.0008)
    ink = rng.choice(SPINE_INK)                                          # spine: bands + title block
    for zb in rng.sample((0.07, 0.11, 0.86, 0.90), rng.randint(1, 2)):
        part.box(ink, x + 0.001, x + t - 0.001, y - 0.0006, y, z + h * zb, z + h * zb + 0.006)
    if rng.random() < 0.6:
        lo = rng.uniform(0.30, 0.45)
        part.box(ink if rng.random() < 0.5 else SPINE_INK[1], x + 0.003, x + t - 0.003, y - 0.0006, y,
                 z + h * lo, z + h * (lo + rng.uniform(0.18, 0.32)))
    if tilt:
        for bmx, k in marks:
            bmx.verts.ensure_lookup_table()
            for v in list(bmx.verts)[k:]:
                v.co.x += (v.co.z - z) * math.tan(tilt)


def books_and_plants(part, x0, x1, depth, z, clear, place):
    x = x0 + 0.03
    while x < x1 - 0.12:
        r = rng.random()
        if False:                                                       # plant spots removed (user)
            PLANT_SPOTS.append((place, x + 0.12, depth / 2, z, clear - 0.04))
            x += 0.28
        elif r < 0.30 and x + 0.26 < x1:
            zz = z
            for _ in range(rng.randint(3, 6)):
                t = rng.uniform(0.02, 0.04); w = rng.uniform(0.17, 0.24); d = rng.uniform(0.15, 0.21)
                part.box(cover_mat(rng.choice(COVERS)), x, x + w, 0.03, 0.03 + d, zz, zz + t, bevel=0.0015)
                part.box(PAGES, x + 0.004, x + w + 0.0008, 0.034, 0.03 + d - 0.003, zz + 0.002, zz + t - 0.002)
                zz += t
            x += 0.30
        else:
            for _ in range(rng.randint(6, 16)):
                t = rng.uniform(0.018, 0.045)
                if x + t > x1 - 0.03:
                    break
                book(part, x, 0.02, z, t, min(clear - 0.03, rng.uniform(0.19, 0.29)), rng.uniform(0.14, 0.21))
                x += t + 0.0008
            if x + 0.06 < x1 - 0.03 and rng.random() < 0.5:
                book(part, x + 0.002, 0.02, z, 0.025, min(clear - 0.04, 0.24), 0.17, tilt=math.radians(rng.uniform(8, 16)))
                x += 0.06
            x += 0.05


def place_plants(col):
    """Scanned CC0 potted plants (Poly Haven) at the recorded spots, scaled to the shelf."""
    from mathutils import Matrix
    lib_col = bpy.data.collections.get("AssetLibrary") or bpy.data.collections.new("AssetLibrary")
    if lib_col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(lib_col)
    bpy.context.view_layer.layer_collection.children[lib_col.name].exclude = True
    srcs = []
    for a in ("potted_plant_01", "potted_plant_02", "potted_plant_04"):
        root = bpy.data.objects.get("PH_" + a)
        if root is None:
            before = set(bpy.data.objects)
            bpy.ops.import_scene.gltf(filepath=bpy.path.abspath(f"//assets/polyhaven/models/{a}/{a}.gltf"))
            new = [o for o in bpy.data.objects if o not in before]
            root = bpy.data.objects.new("PH_" + a, None)
            lib_col.objects.link(root)
            for o in new:
                for c in list(o.users_collection):
                    c.objects.unlink(o)
                lib_col.objects.link(o)
                if o.parent is None:
                    o.parent = root
        meshes = [o for o in root.children_recursive if o.type == "MESH"]
        pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
        srcs.append((meshes, min(p.z for p in pts), max(p.z for p in pts),
                     (min(p.x for p in pts) + max(p.x for p in pts)) / 2, (min(p.y for p in pts) + max(p.y for p in pts)) / 2))
    for i, ((loc, rot), lx, ly, z, maxh) in enumerate(PLANT_SPOTS):
        meshes, z0, z1, cx, cy = srcs[i % len(srcs)]
        k = min(1.0, maxh / (z1 - z0))
        w = lib["to_world"](loc, rot, (lx, ly, 0))
        holder = bpy.data.objects.new(f"Plant_{i + 1:02d}", None)
        col.objects.link(holder)
        holder.location = (w.x, w.y, z)
        holder.rotation_euler = (0, 0, rng.uniform(0, 6.28))
        holder.scale = (k, k, k)
        for m in meshes:
            inst = bpy.data.objects.new(f"Plant_{i + 1:02d}_{m.name}", m.data)
            col.objects.link(inst)
            inst.parent = holder
            inst.matrix_basis = Matrix.Translation((-cx, -cy, -z0)) @ m.matrix_world
    PLANT_SPOTS.clear()


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
    for name, y0, L, H in ():   # craft counters moved to the textile area (build_textile.py), 2026-10-08
        part, _ = lib["table_unit"](L, 0.70, H, [0.0, L - 0.04], lower=(0.16,))
        loc, rot = lib["placement"](XG + 0.35, y0 + L / 2, L, 0.70, "+x")
        part.emit(name, col, loc, rot)
        b = Part()
        for j in range(4):
            lib["bin_box"](b, MAT["bins"][(j + (0 if H > 0.8 else 3)) % 6], 0.06 + j * 0.46, 0.08, 0.16, w=0.42, d=0.40, h=0.24)
            bx = 0.06 + j * 0.46
            if (j + int(H * 10)) % 2:                                   # vinyl rolls lying in the bin
                for r in range(4):
                    p_col = rng.choice(MAT["bins"] + [mat("Vinyl_White", "#F2F2EE", 0.3), mat("Vinyl_Black", "#151515", 0.3)])
                    b.cyl(p_col, (bx + 0.02, 0.13 + r * 0.085, 0.215), (bx + 0.40, 0.13 + r * 0.085, 0.215), 0.04, seg=24)
            else:                                                       # folded fabric stacked
                zz = 0.165
                for r in range(rng.randint(4, 7)):
                    fm = rng.choice([bpy.data.materials["Sofa_LightGrey"], mat("Fabric_Navy", "#2B3550", 0.9),
                                     mat("Fabric_Mustard", "#C99A2E", 0.9), mat("Fabric_Rust", "#9B4A2C", 0.9)])
                    b.box(fm, bx + 0.03, bx + 0.39, 0.10, 0.46, zz, zz + 0.035, bevel=0.012)
                    zz += 0.036
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
    for i, yc in enumerate((26.98, 28.00)):          # packed up to leave y 28.55-29.55 for the cutter counter
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
        if side == "Boxes":                                            # workshop side: tool library, filled by
            fill = Part()                                              # build_microelectronics.tool_library()
        else:
            tops = lv + [2.42]
            for (bi, li), (xa, xb, _, _, zt) in slots.items():
                books_and_plants(fill, xa, xb, 0.30, zt, tops[li + 1] - zt - 0.06, (loc, rot))
        fill.emit(f"Spine_{side}_Contents", sp, loc, rot)
    PLANT_SPOTS.clear()                                                # no plants indoors (user)
    spine = Part()
    spine.box(MAT["ply"], 27.913, 27.929, 31.57, 31.55 + 4 * 1.22 + 0.04 - 0.02, 0.05, 2.40)
    spine.emit("Spine_Panel", sp, Vector((0, 0, 0)))
    return hidden


h = build()
print("craft zone + spine built; placeholders hidden:", h)

# Placements come from layout/layout.yaml (layout/README.md): built at this builder's coordinates, then moved there.
_lay = {}
exec(open(bpy.path.abspath("//scripts/layout_blender.py")).read(), _lay)
_lay["apply"]()
