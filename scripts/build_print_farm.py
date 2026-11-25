"""Print farm against the laser room's NNE partition (front faces -x, x 28.78-29.50, y 21.95-25.31). Re-runnable
("PrintFarm" collection). One black 40x40 profile wall, 5 bays x 3 rows of birch-ply cells + an open spool shelf:

  row 2 (deck 1.48)  Prusa | Prusa | CR-200B | CR-200B | CR-200B        (all cells doored and locked)
  row 1 (deck 0.80)  (P2S) | Prusa | Prusa   | Prusa   | Prusa
  row 0 (deck 0.12)  Bambu P2S + AMS 2 Pro | Flashforge AD5M Pro | Prusa | filament dry cell x2
Bay 0 has no 0.80 deck: the P2S with its top-mounted AMS 2 Pro needs >= 0.80 m clear (architects' schedule); the
double cell gives 1.32 m. Prusa 03 moved from there into the first dry cell (Magnús, 2026-11-25).
  top   (deck 2.16)  spare spools, open

Lock-down (2026-11-25): EVERY cell has a clear acrylic door with the standard cabinet-lock detail (cam lock or an
electronic cabinet lock in the same cut-out), and every printer stands between two steel angle cleats screwed to the
deck (PrintFarm_Anchors). Doors on the open cells, the cleats and the lock detail are my design.

Every Prusa MK3S+ sits in its own cabin: birch sides/back/top, a clear acrylic front door hinged on the bay's left
post (black hinges, bar handle, magnetic catch), a cool-white LED strip and a power strip inside. The self-enclosed
printers (Creality CR-200B x3, Flashforge Adventurer 5M Pro, Bambu Lab P2S) and the dry cells have the same doors. Bay 0 starts at the mural-wall corner (y 21.95), bay 4 ends 0.5 m short of the laser-room door.
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
    (1, 1): "prusa", (2, 1): "prusa", (3, 1): "prusa", (4, 1): "prusa",
    (0, 2): "prusa", (1, 2): "prusa", (2, 2): "cr200b", (3, 2): "cr200b", (4, 2): "cr200b",
    (0, 0): "bambu", (1, 0): "ad5m", (2, 0): "prusa", (3, 0): "dry", (4, 0): "dry",
}
MERGED = {0: (0, 2)}                                                # bay -> (row a, row b): one cell from deck a to deck b
PRUSA_NO = {(0, 2): 1, (1, 2): 2, (2, 0): 3, (1, 1): 4, (2, 1): 5, (3, 1): 6, (4, 1): 7}   # stable object names


def skip_deck(b, zi):
    """True where deck zi is left out of bay b (inside a merged cell)."""
    return b in MERGED and MERGED[b][0] < zi < MERGED[b][1]


def cell_span(b, r):
    """(z bottom, z top) of the cell at bay b, row r, honouring merged cells."""
    a, c = MERGED.get(b, (r, r + 1)) if b in MERGED and MERGED[b][0] <= r < MERGED[b][1] else (r, r + 1)
    return DECKS[a], DECKS[c] - 0.018 - 0.02
DOORS = {"prusa", "dry", "cr200b", "ad5m", "bambu"}                  # every cell doored + locked (lock-down)
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
            if skip_deck(b, zi):
                continue
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
            if b in MERGED and MERGED[b][0] < r < MERGED[b][1]:
                continue
            z0, z1 = cell_span(b, r)
            p.box(ply, ua, ua + BAY, D - POST - 0.012, D - POST, z0, z1)
    for u in us:
        for r in range(3):
            z0, z1 = DECKS[r], DECKS[r + 1] - 0.018 - 0.02
            p.box(ply, u + 0.014, u + 0.026, POST, D - POST - 0.012, z0, z1)
    return p


def cell_kit(p, b, r):
    """LED strip under the deck above + power strip on the back panel."""
    ua, z1 = bay_u(b), cell_span(b, r)[1]
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
    top = MERGED[b][1] if b in MERGED and MERGED[b][0] <= r < MERGED[b][1] else r + 1
    z0, z1 = DECKS[r] - 0.016, DECKS[top] - 0.022
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
    lz = z0 + Hh * 0.5 - 0.13                                       # cam lock below the handle
    lock(p, at, a, W - 0.040, lz)


def lock(p, at, a, du, z):
    """Cabinet lock position on a door (local frame of door()): a 19 mm cam-lock face + escutcheon on the outside and
    the cam/keeper behind; the same cut-out takes an electronic cabinet lock. One standard detail on every door."""
    chrome = M["alusatin"]
    obox(p, MAT["profile"], at(du, -0.0045, z), (0.030, 0.004, 0.044), a)          # escutcheon plate
    obox(p, chrome, at(du, -0.0075, z + 0.004), (0.019, 0.003, 0.019), a)          # lock face
    obox(p, MAT["profile"], at(du, -0.0092, z + 0.004), (0.002, 0.0008, 0.010), a) # key slot
    obox(p, MAT["zinc"], at(du + 0.012, 0.012, z), (0.030, 0.016, 0.006), a)       # cam behind the door


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
    dobj = doors.emit("PrintFarm_Doors", col, loc, rot)
    for o in [dobj, *dobj.children_recursive]:
        o["layout_skip"] = True                                      # open doors don't count in the footprint

    anchors = lib["Part"]()

    def put(part, name, b, r, w, v_front=0.07, du=0.0, anchor=True):
        """Machine of width w centred in bay b on row r's deck, its front at v_front. anchor: two black steel angle
        cleats screwed to the deck tight against the machine's sides (it can't be lifted out without unscrewing
        them; the screws can be security screws if the staff want)."""
        u = bay_u(b) + BAY / 2 - w / 2 + du
        if anchor:
            z = DECKS[r]
            for ux, sgn in ((u, -1), (u + w, 1)):
                x0 = ux + (0.0 if sgn > 0 else -0.003)
                anchors.box(MAT["profile"], min(x0, x0 + sgn * 0.040), max(x0, x0 + sgn * 0.040),
                            v_front + 0.06, v_front + 0.10, z, z + 0.003)                  # flange on the deck
                anchors.box(MAT["profile"], min(ux, ux + sgn * 0.003), max(ux, ux + sgn * 0.003),
                            v_front + 0.06, v_front + 0.10, z, z + 0.040)                  # upstand against the machine
        o = lib["to_world"](loc, rot, (u, v_front, 0.0)) + Vector((0, 0, DECKS[r]))
        return part.emit(name, col, o, rot)

    c = 0
    for (b, r), what in sorted(LAYOUT.items(), key=lambda kv: (-kv[0][1], kv[0][0])):
        if what == "prusa":
            k = PRUSA_NO[(b, r)]
            put(mach["prusa"](M["spools"][(k * 3) % len(M["spools"])]), f"Prusa_MK3S_{k:02d}", b, r, 0.50, 0.075)
        elif what == "cr200b":
            c += 1
            put(mach["creality_cr200b"](), f"Creality_CR200B_{c}", b, r, 0.411, 0.10)
        elif what == "ad5m":
            put(mach["flashforge_ad5m_pro"](), "Flashforge_AD5M_Pro", b, r, 0.380, 0.10)
        elif what == "bambu":
            put(mach["bambu"](ams=True), "Bambu_P2S", b, r, 0.392, 0.10)
        elif what == "dry":                                           # filament dry cell: spools on edge + desiccant
            sp = mach["Part"]()
            for j in range(6):
                mach["spool_part"](sp, M["spools"][rng.randrange(len(M["spools"]))], 0.05 + j * 0.088, 0.24, 0.10,
                                   axis="x", width=0.064)
            sp.box(mach["mat"]("Desiccant_Blue", "#2F6FD8", 0.6), 0.02, 0.14, 0.42, 0.52, 0.0, 0.06, bevel=0.006)
            sp.box(M["white"], 0.44, 0.56, 0.44, 0.52, 0.0, 0.05, bevel=0.004)          # hygrometer box
            put(sp, f"DryCell_{b}", b, r, 0.58, 0.05, anchor=False)
    top = mach["Part"]()                                             # spare spools on the open top shelf
    for j in range(34):
        top_u = 0.06 + j * 0.0965
        if any(abs(top_u - (bay_u(bb) - POST / 2)) < 0.05 for bb in range(1, NB)):
            continue                                                 # skip the post lines
        mach["spool_part"](top, M["spools"][rng.randrange(len(M["spools"]))], top_u, 0.30, 0.10, axis="x", width=0.062)
    anchors.emit("PrintFarm_Anchors", col, loc, rot)
    top.emit("PrintFarm_Spools", col, lib["to_world"](loc, rot, (0.0, 0.0, 0.0)) + Vector((0, 0, DECKS[3])), rot)
    print("print farm: %d Prusa cabins, %d CR-200B, AD5M Pro, P2S + AMS 2 Pro, %d dry cells"
          % (len(PRUSA_NO), c, sum(v == "dry" for v in LAYOUT.values())))


build()

# Placements come from layout/layout.yaml (layout/README.md): built at this builder's coordinates, then moved there.
_lay = {}
exec(open(bpy.path.abspath("//scripts/layout_blender.py")).read(), _lay)
_lay["apply"]()
