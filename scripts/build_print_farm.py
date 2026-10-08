"""Print farm against the laser room's NNE partition (front faces -x, x 28.78-29.50, y 21.95-25.31). Re-runnable
("PrintFarm" collection). One black 40x40 profile wall, 5 bays x 3 rows of birch-ply cells + an open spool shelf:

  row 2 (deck 1.48)  Prusa | Prusa | CR-200B | CR-200B | CR-200B        (Prusa cells: cabins, CR-200Bs: open cells)
  row 1 (deck 0.80)  Prusa | Prusa | Prusa   | Prusa   | Prusa
  row 0 (deck 0.12)  Bambu P2S | Flashforge AD5M Pro | filament dry cell x3
  top   (deck 2.16)  spare spools, open

Every Prusa MK3S+ sits in its own cabin: birch sides/back/top, a clear acrylic front door hinged on the bay's left
post (black hinges, bar handle, magnetic catch), a cool-white LED strip and a power strip inside. The self-enclosed
printers (Creality CR-200B x3, Flashforge Adventurer 5M Pro, Bambu Lab P2S) stand in open cells; the dry cells have
the same doors. Bay 0 starts at the mural-wall corner (y 21.95), bay 4 ends 0.5 m short of the laser-room door.
Models: build_machines.py. Counts per MACHINES.md (7 Prusas, user decision 2026-10-08).
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
M = mach["M"]
M.update(alusatin=mach["mat"]("Mach_AluSatin", "#C3C7CB", 0.3, metal=1.0))
rng = random.Random(77)

POST, BAY, NB = 0.04, 0.624, 5
L = NB * BAY + (NB + 1) * POST                                     # 3.36
D = 0.72
DECKS = [0.12, 0.80, 1.48, 2.16]
H = 2.42
LAYOUT = {                                                           # (bay, row) -> what
    (0, 1): "prusa", (1, 1): "prusa", (2, 1): "prusa", (3, 1): "prusa", (4, 1): "prusa",
    (0, 2): "prusa", (1, 2): "prusa", (2, 2): "cr200b", (3, 2): "cr200b", (4, 2): "cr200b",
    (0, 0): "bambu", (1, 0): "ad5m", (2, 0): "dry", (3, 0): "dry", (4, 0): "dry",
}
DOORS = {"prusa", "dry"}
OPEN = {(2, 1): 78.0, (4, 0): 35.0}                                  # doors left open (degrees)


def bay_u(b):
    return POST + b * (BAY + POST)                                   # inner left edge of bay b


def obox(part, m, center, size, rot_z):
    bmesh.ops.create_cube(part.bm(m), size=1.0, matrix=Matrix.Translation(center) @ Matrix.Rotation(rot_z, 4, "Z")
                          @ Matrix.Diagonal((size[0], size[1], size[2], 1.0)))


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


def frame():
    p = lib["Part"]()
    ply = MAT["ply"]
    us = [b * (BAY + POST) for b in range(NB + 1)]                   # post positions (left edge)
    for u in us:                                                     # uprights + feet
        for v in (0.0, D - POST):
            p.profile(POST, "z", u, v, 0.035, H - 0.035)
            lib["foot"](p, u + POST / 2, v + POST / 2)
    for zi, z in enumerate(DECKS + [H]):
        s = POST if zi in (0, len(DECKS)) else 0.02
        zr = z - (0.018 if zi < len(DECKS) else 0.0) - s
        for b in range(NB):
            ua, ub = bay_u(b), bay_u(b) + BAY
            for v in (0.0, D - s):
                p.profile(s, "x", ua, v, zr, ub - ua)
            if zi < len(DECKS):
                lib["board"](p, ua, ub, 0.002, D - 0.002, z)         # deck
        for u in us:
            p.profile(s, "y", u, POST, zr, D - 2 * POST)
    for b in range(NB):                                              # back panels (rows 0-2) + cell sides
        ua = bay_u(b)
        for r in range(3):
            z0, z1 = DECKS[r], DECKS[r + 1] - 0.018 - 0.02
            p.box(ply, ua, ua + BAY, D - POST - 0.012, D - POST, z0, z1)
    for u in us:
        for r in range(3):
            z0, z1 = DECKS[r], DECKS[r + 1] - 0.018 - 0.02
            p.box(ply, u + 0.014, u + 0.026, POST, D - POST - 0.012, z0, z1)
    return p


def cell_kit(p, b, r):
    """LED strip under the deck above + power strip on the back panel."""
    ua, z1 = bay_u(b), DECKS[r + 1] - 0.018 - 0.02
    led = mach["mat"]("LED_CoolWhite", "#EAF2FF", 0.3, emit=6.0)
    p.box(MAT["strip"], ua + 0.04, ua + BAY - 0.04, 0.05, 0.065, z1 - 0.012, z1)
    p.box(led, ua + 0.05, ua + BAY - 0.05, 0.052, 0.063, z1 - 0.0135, z1 - 0.012)
    p.box(MAT["strip"], ua + 0.08, ua + 0.42, D - POST - 0.052, D - POST - 0.012, DECKS[r] + 0.02, DECKS[r] + 0.06)
    p.box(MAT["led"], ua + 0.09, ua + 0.10, D - POST - 0.054, D - POST - 0.052, DECKS[r] + 0.035, DECKS[r] + 0.045)


def door(p, b, r, angle_deg):
    """Clear acrylic door on the bay's left post, hinge axis at the front-left corner; positive angle opens out."""
    acr = mach["_acrylic"]("Acrylic_Door", "#C9D6DC", 0.03, 0.07)
    blk = MAT["profile"]
    ua = bay_u(b)
    z0, z1 = DECKS[r] - 0.016, DECKS[r + 1] - 0.022
    hinge = Vector((ua - 0.012, -0.010, 0.0))
    a = -math.radians(angle_deg)                                    # rotate about z: out of the cell = towards -v
    R = Matrix.Rotation(a, 3, "Z")
    W, T, Hh = BAY + 0.020, 0.005, z1 - z0

    def at(du, dv, z):
        return hinge + R @ Vector((du, dv, 0.0)) + Vector((0, 0, z))
    obox(p, acr, at(W / 2, 0.0, z0 + Hh / 2), (W, T, Hh), a)
    for zz in (z0 + 0.08, z1 - 0.08):                               # hinges on the post face
        obox(p, blk, at(0.012, 0.004, zz), (0.030, 0.010, 0.050), a)
    hu = W - 0.045                                                  # bar handle near the free edge
    obox(p, blk, at(hu, -0.030, z0 + Hh * 0.5), (0.012, 0.012, 0.18), a)
    for dz in (-0.08, 0.08):
        obox(p, blk, at(hu, -0.015, z0 + Hh * 0.5 + dz), (0.010, 0.026, 0.010), a)
    obox(p, MAT["zinc"], at(W - 0.010, 0.006, z0 + Hh * 0.5), (0.016, 0.006, 0.030), a)   # magnet plate


def build():
    col = clear_collection("PrintFarm")
    for name in ("PrintFarm_Shelving", "PrintFarm_Bins"):           # the old open shelving (build_machines)
        o = bpy.data.objects.get(name)
        if o:
            for k in reversed([o, *o.children_recursive]):
                bpy.data.objects.remove(k)
    loc, rot = lib["placement"](29.50 - D / 2, 21.95 + L / 2, L, D, "-x")
    fr = frame()
    for (b, r), what in LAYOUT.items():
        if what in DOORS:
            cell_kit(fr, b, r)
    fr.emit("PrintFarm_Frame", col, loc, rot)
    doors = lib["Part"]()
    for (b, r), what in LAYOUT.items():
        if what in DOORS:
            door(doors, b, r, OPEN.get((b, r), 0.0))
    doors.emit("PrintFarm_Doors", col, loc, rot)

    def put(part, name, b, r, w, v_front=0.07, du=0.0):
        """Machine of width w centred in bay b on row r's deck, its front at v_front."""
        u = bay_u(b) + BAY / 2 - w / 2 + du
        o = lib["to_world"](loc, rot, (u, v_front, 0.0)) + Vector((0, 0, DECKS[r]))
        return part.emit(name, col, o, rot)

    k = c = 0
    for (b, r), what in sorted(LAYOUT.items(), key=lambda kv: (-kv[0][1], kv[0][0])):
        if what == "prusa":
            k += 1
            put(mach["prusa"](M["spools"][(k * 3) % len(M["spools"])]), f"Prusa_MK3S_{k:02d}", b, r, 0.50, 0.075)
        elif what == "cr200b":
            c += 1
            put(mach["creality_cr200b"](), f"Creality_CR200B_{c}", b, r, 0.411, 0.10)
        elif what == "ad5m":
            put(mach["flashforge_ad5m_pro"](), "Flashforge_AD5M_Pro", b, r, 0.380, 0.10)
        elif what == "bambu":
            put(mach["bambu"](), "Bambu_P2S", b, r, 0.392, 0.10)
        elif what == "dry":                                           # filament dry cell: spools on edge + desiccant
            sp = mach["Part"]()
            for j in range(6):
                mach["spool_part"](sp, M["spools"][rng.randrange(len(M["spools"]))], 0.05 + j * 0.088, 0.24, 0.10,
                                   axis="x", width=0.064)
            sp.box(mach["mat"]("Desiccant_Blue", "#2F6FD8", 0.6), 0.02, 0.14, 0.42, 0.52, 0.0, 0.06, bevel=0.006)
            sp.box(M["white"], 0.44, 0.56, 0.44, 0.52, 0.0, 0.05, bevel=0.004)          # hygrometer box
            put(sp, f"DryCell_{b}", b, r, 0.58, 0.05)
    top = mach["Part"]()                                             # spare spools on the open top shelf
    for j in range(34):
        top_u = 0.06 + j * 0.0965
        if any(abs(top_u - (bay_u(bb) - POST / 2)) < 0.05 for bb in range(1, NB)):
            continue                                                 # skip the post lines
        mach["spool_part"](top, M["spools"][rng.randrange(len(M["spools"]))], top_u, 0.30, 0.10, axis="x", width=0.062)
    top.emit("PrintFarm_Spools", col, lib["to_world"](loc, rot, (0.0, 0.0, 0.0)) + Vector((0, 0, DECKS[3])), rot)
    print("print farm: %d Prusa cabins, %d CR-200B, AD5M Pro, P2S, 3 dry cells" % (k, c))


build()
