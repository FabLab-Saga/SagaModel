"""Craft & large-format corner by the SSW glass, between the laser room's glazed ESE partition (y 26.94) and the
lounge nook; the main circulation x 28.0-29.5 stays clear. Re-runnable ("Textile" collection).
- Sewing/heat-transfer wall bench 2.6 x 0.75 m against the partition (sit facing it, 3 profile chairs): LOKLiK Auto
  Heat Press, Cricut Mug Press, overlocker, Brother embroidery + sewing machine; 2 Cricut EasyPress 3 on the shelf.
- Large-format/clay bench 1.9 x 0.8 m on the SSW glass (x 31.65-32.45, y 28.18-30.08): red industrial clam press,
  Eazao Zero clay printer (microwave + clay buckets on the shelf), Creality CR-10 Max.
- One lockable rolling cabinet 813 x 610 x 0.90 (E5, replaced the two BEKANT carts) against felt panel 1 by the cutter
  corner: Cricut Maker 3 and the handheld 3D scanner kit stored inside behind acrylic doors.
- Cutter counter (Cricut Maker + Mayku FormBox, 1.0 x 0.55 m, standing height) on the NNE glass next to the
  vinyl cutters (y 28.55-29.55): all the cutters in one corner; lockable cupboard underneath (E5).
"""
import math
import random

import bpy
from mathutils import Vector

HERE = bpy.path.abspath("//scripts/")
lib = {}
exec(open(HERE + "profile_furniture.py").read(), lib)
MAT = lib["materials"]()
_m = open(HERE + "build_machines.py").read()
mach = {}
exec(_m[:_m.index("\ndef build():")], mach)
mach["materials"]()
M = mach["M"]
Part, mat = lib["Part"], lib["simple_mat"]
rng = random.Random(9)


def chair(seat_h=0.46):
    """Profile chair: 20x20 frame, birch seat + curved-look back panel, local front = -y."""
    p = Part()
    w, d = 0.44, 0.44
    for x in (0.0, w - 0.02):
        p.profile(0.02, "z", x, 0.0, 0.035, seat_h - 0.055)                 # front legs
        p.profile(0.02, "z", x, d - 0.02, 0.035, 0.86 - 0.035)              # back legs up to the backrest
        lib["foot"](p, x + 0.01, 0.01); lib["foot"](p, x + 0.01, d - 0.01)
        p.profile(0.02, "y", x, 0.02, seat_h - 0.04, d - 0.04)              # seat rails
        p.profile(0.02, "y", x, 0.02, 0.18, d - 0.04)                       # low rails
    for y in (0.0, d - 0.02):
        p.profile(0.02, "x", 0.02, y, seat_h - 0.04, w - 0.04)
    p.box(MAT["ply"], -0.005, w + 0.005, -0.01, d, seat_h - 0.02, seat_h, bevel=0.004)           # seat
    p.box(MAT["ply"], 0.0, w, d - 0.02, d - 0.005, 0.62, 0.84, bevel=0.004)                      # back
    return p


def under_cupboard(cb, cd, bays, depth, z0, z1, ld, trays=()):
    """Lockable cupboard under a table_unit top (E6/E5 detail, my design): ply back + end panels, clear acrylic door
    pair with one e-lock per bay (scripts/lockdown.py), in the table's local frame (front = local -y). bays: list of
    (x0, x1) between legs; trays: (x0, x1, z) pull-out trays on grey runners."""
    ply = MAT["ply"]
    run = mat("Drawer_Runner", "#8E9296", 0.35, metal=0.8)
    for x0, x1 in bays:
        cb.box(ply, x0, x1, depth - 0.022, depth - 0.004, z0, z1)                     # back
        for x in (x0, x1 - 0.018):
            cb.box(ply, x, x + 0.018, 0.04, depth - 0.022, z0, z1)                     # ends
        ld["door_run"](cd, "-y", -0.004, x0 + 0.003, x1 - 0.003, z0 - 0.01, z1 - 0.005, leaves=2, lock_z=z1 - 0.08)
    for x0, x1, z in trays:
        cb.box(ply, x0 + 0.03, x1 - 0.03, 0.05, depth - 0.03, z, z + 0.012, bevel=0.001)     # tray
        cb.box(ply, x0 + 0.03, x1 - 0.03, 0.05, 0.062, z, z + 0.05, bevel=0.002)            # front lip
        for x in (x0 + 0.018, x1 - 0.03):
            cb.box(run, x, x + 0.012, 0.05, depth - 0.03, z, z + 0.035)                      # runners


def build():
    scene = bpy.context.scene
    col = bpy.data.collections.get("Textile") or bpy.data.collections.new("Textile")
    if col.name not in scene.collection.children:
        scene.collection.children.link(col)
    for o in list(col.objects):
        data = o.data
        bpy.data.objects.remove(o)
        if isinstance(data, bpy.types.Mesh) and data.users == 0:
            bpy.data.meshes.remove(data)
    put = lambda part, name, loc, rot, lx, ly, z, w, d: part.emit(
        name, col, lib["to_world"](loc, rot, (lx, ly, 0)) + Vector((0, 0, z)) +
        __import__("mathutils").Matrix.Rotation(rot, 4, "Z") @ Vector((-w / 2, -d / 2, 0)), rot)

    # ---- sewing + heat-transfer wall bench along the laser room's glazed ESE partition (y 26.94), sit facing it
    BL, BD, BH = 2.60, 0.75, 0.76
    part, _ = lib["table_unit"](BL, BD, BH, [0.0, BL / 2 - 0.02, BL - 0.04], lower=(0.16,))
    loc, rot = lib["placement"](32.35 - BL / 2, 26.96 + BD / 2, BL, BD, "+y")    # local x=0 at the glass end
    part.emit("SewingBench", col, loc, rot)
    put(mach["loklik_auto_press"](), "LOKLiK_AutoPress", loc, rot, 0.29, 0.30, BH, 0.50, 0.40)
    put(mach["cricut_mug_press"](), "Cricut_MugPress", loc, rot, 0.70, 0.22, BH, 0.275, 0.157)
    put(mach["overlock"](), "Overlock", loc, rot, 1.14, 0.30, BH, 0.335, 0.282)
    put(mach["cricut_easypress3"](), "Cricut_EasyPress3_1", loc, rot, 0.20, 0.36, 0.16, 0.305, 0.254)   # in the cupboard
    put(mach["cricut_easypress3"](), "Cricut_EasyPress3_2", loc, rot, 0.52, 0.36, 0.16, 0.305, 0.254)
    # E6 (2026-11-26, my design on Magnús's go-ahead to iterate): lockable cupboard under the glass end of the sewing
    # bench (lx 0.04-0.70, clear of the three knee spaces): both EasyPresses on the floor, a pull-out tray above for
    # the mug-press blanks; acrylic pair + one e-lock. LOKLiK held between steel angle cleats on the top.
    ld = {}
    exec(open(HERE + "lockdown.py").read(), ld)
    zt = BH - 0.025 - 0.04
    cb, cd = Part(), Part()
    under_cupboard(cb, cd, [(0.04, 0.70)], BD, 0.16, zt, ld, trays=[(0.04, 0.70, 0.45)])
    white = mat("Mug_Blank", "#F4F4F2", 0.25, coat=0.4)
    for k in range(4):                                                                  # boxed mug blanks on the tray
        cb.box(mat("Kraft_Box", "#B98F5E", 0.8), 0.10 + k * 0.13, 0.22 + k * 0.13, 0.12, 0.24, 0.462, 0.572, bevel=0.003)
    cb.cyl(white, (0.16, 0.40, 0.462), (0.16, 0.40, 0.557), 0.041, seg=24)
    cb.cyl(white, (0.27, 0.42, 0.462), (0.27, 0.42, 0.557), 0.041, seg=24)
    cb.emit("SewingBench_Cupboard", col, loc, rot)
    dob = cd.emit("SewingBench_Doors", col, loc, rot)
    for o in [dob, *dob.children_recursive]:
        o["layout_skip"] = True
    cl = Part()                                                                         # LOKLiK anchor cleats
    for ax in (0.04, 0.54):
        for ay in (0.13, 0.43):
            x0, x1 = (ax - 0.04, ax) if ax < 0.3 else (ax, ax + 0.04)
            cl.box(MAT["zinc"], x0, x1, ay, ay + 0.04, BH, BH + 0.003)
            cl.box(MAT["zinc"], (x1 - 0.003) if ax < 0.3 else x0, x1 if ax < 0.3 else x0 + 0.003, ay, ay + 0.04, BH, BH + 0.035)
    cl.emit("LOKLiK_Anchors", col, loc, rot)
    put(mach["sewing"](0.50, 0.24, 0.32), "Brother_Embroidery", loc, rot, 1.62, 0.26, BH, 0.50, 0.24)
    put(mach["sewing"](), "Brother_Sewing", loc, rot, 2.30, 0.26, BH, 0.42, 0.20)
    props = Part()
    fab = [bpy.data.materials["Sofa_LightGrey"], mat("Fabric_Navy", "#2B3550", 0.9),
           mat("Fabric_Mustard", "#C99A2E", 0.9), mat("Fabric_Rust", "#9B4A2C", 0.9)]
    cm = bpy.data.materials.get("CuttingMat") or MAT["ply"]
    props.box(cm, 1.95, 2.55, 0.48, 0.72, BH, BH + 0.003)                               # cutting mat by the sewing
    props.box(fab[2], 2.00, 2.45, 0.52, 0.70, BH + 0.003, BH + 0.008, bevel=0.002)      # fabric laid out
    zz = BH
    for k in range(4):                                                                  # folded stack
        props.box(fab[k % 4], 1.30, 1.55, 0.50, 0.70, zz, zz + 0.03, bevel=0.01)
        zz += 0.031
    props.box(M["chrome"], 2.10, 2.28, 0.10, 0.12, BH + 0.012, BH + 0.016)              # shears
    props.box(mat("Shears_Orange", "#E2631C", 0.5), 2.00, 2.10, 0.09, 0.13, BH + 0.011, BH + 0.022, bevel=0.004)
    props.cyl(mat("Pincushion_Red", "#C0262D", 0.8), (1.92, 0.62, BH), (1.92, 0.62, BH + 0.05), 0.04, seg=24)
    for k in range(6):                                                                  # thread spools
        x = 2.20 + k * 0.035
        props.cyl(MAT["bins"][k % 6], (x, 0.66, BH), (x, 0.66, BH + 0.055), 0.013, seg=14)
    tee = mat("Tee_White", "#F1F0EC", 0.9)                                             # T-shirt waiting by the press
    props.box(tee, 0.56, 0.86, 0.48, 0.70, BH, BH + 0.012, bevel=0.004)
    props.box(MAT["bins"][2], 0.63, 0.78, 0.53, 0.64, BH + 0.012, BH + 0.0135)
    for k in range(3):                                                                  # HTV rolls on the shelf
        props.cyl(MAT["bins"][(k * 2) % 6], (1.00, 0.20 + k * 0.08, 0.16 + 0.032), (1.25, 0.20 + k * 0.08, 0.16 + 0.032), 0.032, seg=20)
    props.emit("SewingBench_Props", col, loc, rot)
    for i, lx in enumerate((2.30, 1.62, 1.02)):                         # three chairs facing the bench
        c = lib["to_world"](loc, rot, (lx, 0, 0))
        cx = c.x + rng.uniform(-0.05, 0.05)
        cy = 26.96 + BD + rng.uniform(0.10, 0.24) + 0.22
        r = rng.uniform(-0.15, 0.15)
        off = __import__("mathutils").Matrix.Rotation(r, 4, "Z") @ Vector((-0.22, -0.22, 0))
        chair().emit(f"Chair_{i}", col, Vector((cx, cy, 0)) + off, r)

    # ---- large-format / clay bench on the SSW glass (x 31.65-32.45, y 28.18-30.08), front faces -x
    GL, GD, GH = 1.90, 0.80, 0.75
    part, _ = lib["table_unit"](GL, GD, GH, [0.0, GL / 2 - 0.02, GL - 0.04], lower=(0.16,))
    gloc, grot = lib["placement"](32.45 - GD / 2, 28.18 + GL / 2, GL, GD, "-x")     # local x=0 at the nook end
    part.emit("GlassBench", col, gloc, grot)
    put(mach["secabo_tc7"](), "HeatPress_RedClam", gloc, grot, 0.30, 0.37, GH, 0.43, 0.57)
    put(mach["eazao_zero"](), "Eazao_Zero", gloc, grot, 0.98, 0.30, GH, 0.35, 0.30)
    put(mach["creality_cr10_max"](), "Creality_CR10_Max", gloc, grot, 1.52, 0.4125, GH, 0.65, 0.785)
    put(mach["microwave"](), "Clay_Microwave", gloc, grot, 1.20, 0.25, 0.16, 0.45, 0.35)
    for i, lx in enumerate((1.10, 1.33)):                                            # clay behind the microwave
        put(mach["clay_bucket"](0.11, 0.20), f"Clay_Bucket_{i}", gloc, grot, lx, 0.62, 0.16, 0.0, 0.0)
    # E6: lockable cupboard under the whole large-format bench (2 bays between the legs, acrylic pairs, one e-lock per
    # bay; my design): microwave, clay buckets and spools in bay 2; bay 1 = pull-out tray for the sewing machines and the
    # overlocker overnight (they stand rotated: 0.20 + 0.24 + 0.335 m < 0.85) with a fabric box behind.
    gb, gd = Part(), Part()
    gz = GH - 0.025 - 0.04
    under_cupboard(gb, gd, [(0.04, 0.93), (0.97, 1.86)], GD, 0.16, gz, ld, trays=[(0.04, 0.93, 0.172)])
    for k, c in enumerate((mat("Fabric_Navy", "#2B3550", 0.9), mat("Fabric_Mustard", "#C99A2E", 0.9))):
        gb.box(c, 0.62, 0.88, 0.46 + k * 0.0, 0.74, 0.184 + k * 0.05, 0.234 + k * 0.05, bevel=0.012)
    gb.emit("GlassBench_Cupboard", col, gloc, grot)
    dob = gd.emit("GlassBench_Doors", col, gloc, grot)
    for o in [dob, *dob.children_recursive]:
        o["layout_skip"] = True
    sp = mach["Part"]()
    for j in range(4):
        mach["spool_part"](sp, M["spools"][(j * 3 + 1) % len(M["spools"])], 0.06 + j * 0.10, 0.12, 0.10, axis="x", width=0.07)
    put(sp, "GlassBench_Spools", gloc, grot, 1.645, 0.40, 0.16, 0.40, 0.24)

    # ---- E5 (Magnús 2026-11-26): ONE lockable rolling cabinet replaces the two BEKANT carts - 813 x 610 (a third of a
    # 2440 strip), worktop 0.90 m for standing work (his picks), along felt panel 1 at x 22.20-23.01 so 0.75 m stays
    # free in front of the cutter counter. 40x40 frame on four locking castors, birch-ply top/bottom/shelf/sides/back,
    # a pair of clear acrylic doors with one e-lock (scripts/lockdown.py). Stored inside: Cricut Maker 3 on the bottom,
    # handheld scanner kit on the shelf (his option text); mats + material packs beside them. Frame/panel details mine.
    ld = {}
    exec(open(HERE + "lockdown.py").read(), ld)
    KW, KD, KH, KZ0 = 0.813, 0.61, 0.90, 0.10              # cabinet; frame starts on the castor plates at KZ0
    kloc, krot = lib["placement"](22.20 + KW / 2, 29.18 - KD / 2, KW, KD, "-y")
    kc, kdr, kin = Part(), Part(), Part()
    ply = MAT["ply"]
    ft = KH - 0.018                                        # frame top / underside of the worktop
    for x in (0.0, KW - 0.04):
        for y in (0.0, KD - 0.04):
            kc.profile(0.04, "z", x, y, KZ0, ft - KZ0)
    for z in (KZ0, ft - 0.04):
        for y in (0.0, KD - 0.04):
            kc.profile(0.04, "x", 0.04, y, z, KW - 0.08)
        for x in (0.0, KW - 0.04):
            kc.profile(0.04, "y", x, 0.04, z, KD - 0.08)
    kc.box(ply, 0.0, KW, 0.0, KD, ft, KH, bevel=0.002)                                   # worktop
    kc.box(ply, 0.04, KW - 0.04, 0.052, 0.567, KZ0 + 0.04, KZ0 + 0.058, bevel=0.001)         # bottom 733 x 515
    kc.box(ply, 0.04, KW - 0.04, KD - 0.031, KD - 0.013, KZ0 + 0.04, ft - 0.04)        # back (in the slots)
    for x in (0.011, KW - 0.029):
        kc.box(ply, x, x + 0.018, 0.04, KD - 0.04, KZ0 + 0.04, ft - 0.04)              # sides
    ZS = 0.50
    kc.box(ply, 0.04, KW - 0.04, 0.06, 0.575, ZS, ZS + 0.018, bevel=0.001)              # shelf 733 x 515 (both carcasses nest in two boards: AGENTS.md)
    for x in (0.045, KW - 0.045):                                                      # locking castors
        for y in (0.045, KD - 0.045):
            kc.box(MAT["zinc"], x - 0.035, x + 0.035, y - 0.035, y + 0.035, KZ0 - 0.006, KZ0)      # top plate
            kc.box(MAT["zinc"], x - 0.016, x + 0.016, y - 0.02, y + 0.02, 0.06, KZ0 - 0.006)       # fork
            kc.cyl(MAT["foot"], (x - 0.012, y, 0.0375), (x + 0.012, y, 0.0375), 0.0375, seg=18)  # 75 mm wheel
            kc.box(mat("Castor_Brake_Red", "#B3261E", 0.5), x - 0.012, x + 0.012, y - 0.055, y - 0.02, 0.05, 0.058)
    kc.emit("CutterCart", col, kloc, krot)
    blue = mat("Cricut3_Blue", "#C7D5E2", 0.35, coat=0.2)
    put(mach["cricut"](0.538, 0.178, 0.151, body=blue), "Cricut_Maker_3", kloc, krot, 0.32, 0.32, KZ0 + 0.058, 0.538, 0.178)
    put(mach["revopoint_pop3_kit"](), "Handheld_3DScanner", kloc, krot, 0.30, 0.32, ZS + 0.018, 0.40, 0.40)
    zb = KZ0 + 0.058
    for k in range(4):                                                                 # Cricut mats standing at the side
        kin.box(MAT["bins"][(1, 2, 4, 3)[k]], 0.64 + k * 0.006, 0.643 + k * 0.006, 0.12, 0.45, zb, zb + 0.33)
    kin.box(mat("Cardstock_Pack", "#E8DCC4", 0.7), 0.66, 0.76, 0.10, 0.45, ZS + 0.018, ZS + 0.07, bevel=0.002)
    kin.box(MAT["bins"][5], 0.66, 0.76, 0.12, 0.43, ZS + 0.07, ZS + 0.10, bevel=0.002)
    kin.emit("CutterCart_Contents", col, kloc, krot)
    ld["door_run"](kdr, "-y", -0.004, 0.01, KW - 0.01, KZ0 + 0.01, ft - 0.005, leaves=2, lock_z=ft - 0.08)
    dob = kdr.emit("CutterCart_Doors", col, kloc, krot)
    for o in [dob, *dob.children_recursive]:
        o["layout_skip"] = True

    # ---- standing cutter counter on the NNE glass (x 20.90), next to the vinyl stands, front faces +x
    CL, CD, CH = 1.00, 0.55, 0.92
    part, _ = lib["table_unit"](CL, CD, CH, [0.0, CL - 0.04], lower=(0.16,))
    cloc, crot = lib["placement"](20.90 + CD / 2, 29.05, CL, CD, "+x")
    part.emit("CutterCounter", col, cloc, crot)
    put(mach["cricut"](), "Cricut_Maker_1", cloc, crot, 0.35, 0.30, CH, 0.60, 0.179)
    put(mach["mayku"](), "Mayku_FormBox", cloc, crot, 0.82, 0.30, CH, 0.274, 0.466)
    b = Part()
    lib["bin_box"](b, MAT["bins"][3], 0.05, 0.08, 0.16, w=0.42, d=0.40, h=0.22)
    lib["bin_box"](b, MAT["bins"][5], 0.52, 0.08, 0.16, w=0.42, d=0.40, h=0.22)
    b.cyl(MAT["bins"][2], (0.09, 0.18, 0.26), (0.43, 0.18, 0.26), 0.04, seg=20)        # vinyl rolls
    b.cyl(MAT["bins"][0], (0.09, 0.30, 0.26), (0.43, 0.30, 0.26), 0.04, seg=20)
    b.emit("CutterCounter_Bins", col, cloc, crot)
    # E5 (Magnús 2026-11-26): lockable cupboard under the counter - ply back + sides in the frame, a mid shelf, and a
    # pair of clear acrylic doors with one e-lock on the front (the scripts/lockdown.py detail). Room inside for both
    # machines (Cricut Maker 0.60 x 0.18 x 0.24 + Mayku 0.27 x 0.47 x 0.32 side by side on the mid shelf); the model
    # shows them out on the counter in use, consumables inside (my choice). Panel sizes are mine.
    ld = {}
    exec(open(HERE + "lockdown.py").read(), ld)
    ply = MAT["ply"]
    za = CH - 0.025 - 0.04                                              # apron underside
    cb, cd = Part(), Part()
    cb.box(ply, 0.04, CL - 0.04, CD - 0.022, CD - 0.004, 0.16, za)      # back
    for x in (0.011, CL - 0.029):
        cb.box(ply, x, x + 0.018, 0.04, CD - 0.04, 0.16, za)            # sides (in the leg slots)
    zs = 0.50
    cb.box(ply, 0.04, CL - 0.04, 0.05, CD - 0.022, zs, zs + 0.018, bevel=0.0015)   # mid shelf
    for k in range(5):                                                  # cutting mats (12x12 / 12x24) lying flat
        cb.box(MAT["bins"][(1, 2, 4, 1, 3)[k]], 0.06, 0.40, 0.08, 0.42, zs + 0.018 + k * 0.004, zs + 0.021 + k * 0.004)
    cb.box(mat("Mayku_Sheet", "#E9EEF0", 0.25), 0.46, 0.66, 0.10, 0.40, zs + 0.018, zs + 0.07, bevel=0.002)  # forming sheets
    cb.box(mat("Cardstock_Pack", "#E8DCC4", 0.7), 0.70, 0.92, 0.10, 0.40, zs + 0.018, zs + 0.055, bevel=0.002)
    cb.box(MAT["bins"][0], 0.72, 0.90, 0.12, 0.38, zs + 0.055, zs + 0.075, bevel=0.002)
    cb.emit("CutterCounter_Cupboard", col, cloc, crot)
    ld["door_run"](cd, "-y", -0.004, 0.02, CL - 0.02, 0.15, za - 0.005, leaves=2, lock_z=za - 0.08)
    dob = cd.emit("CutterCounter_Doors", col, cloc, crot)
    for o in [dob, *dob.children_recursive]:
        o["layout_skip"] = True
    print("textile area built")


build()

# Placements come from layout/layout.yaml (layout/README.md): built at this builder's coordinates, then moved there.
_lay = {}
exec(open(bpy.path.abspath("//scripts/layout_blender.py")).read(), _lay)
_lay["apply"]()
