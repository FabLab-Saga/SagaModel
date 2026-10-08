"""Craft & large-format corner by the SSW glass, between the laser room's glazed ESE partition (y 26.94) and the
lounge nook; the main circulation x 28.0-29.5 stays clear. Re-runnable ("Textile" collection).
- Sewing/heat-transfer wall bench 2.6 x 0.75 m against the partition (sit facing it, 3 profile chairs): LOKLiK Auto
  Heat Press, Cricut Mug Press, overlocker, Brother embroidery + sewing machine; 2 Cricut EasyPress 3 on the shelf.
- Large-format/clay bench 1.9 x 0.8 m on the SSW glass (x 31.65-32.45, y 28.18-30.08): red industrial clam press,
  Eazao Zero clay printer (microwave + clay buckets on the shelf), Creality CR-10 Max.
- Two IKEA BEKANT rolling carts (birch-ply top) against felt panel 1 by the cutter corner: Cricut Maker 3, handheld 3D scanner kit (tripod, turntable, case).
- Cutter counter (Cricut Maker + Mayku FormBox, 1.0 x 0.55 m, standing height) on the NNE glass next to the
  vinyl cutters (y 28.55-29.55): all the cutters in one corner.
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
    put(mach["overlock"](), "Overlock", loc, rot, 1.14, 0.30, BH, 0.33, 0.28)
    put(mach["cricut_easypress3"](), "Cricut_EasyPress3_1", loc, rot, 0.30, 0.34, 0.16, 0.305, 0.254)   # shelf
    put(mach["cricut_easypress3"](), "Cricut_EasyPress3_2", loc, rot, 0.72, 0.34, 0.16, 0.305, 0.254)
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
    put(mach["microwave"](), "Clay_Microwave", gloc, grot, 0.98, 0.30, 0.16, 0.45, 0.35)
    for i, lx in enumerate((0.20, 0.47)):
        put(mach["clay_bucket"](0.12, 0.22), f"Clay_Bucket_{i}", gloc, grot, lx, 0.40, 0.16, 0.0, 0.0)
    sp = mach["Part"]()
    for j in range(4):
        mach["spool_part"](sp, M["spools"][(j * 3 + 1) % len(M["spools"])], 0.06 + j * 0.10, 0.12, 0.10, axis="x", width=0.07)
    put(sp, "GlassBench_Spools", gloc, grot, 1.52, 0.40, 0.16, 0.40, 0.24)

    # ---- two BEKANT rolling carts (from the equipment list, birch-ply top) parked against felt panel 1
    for i, (cx, what) in enumerate(((21.805, "cricut3"), (22.465, "scanner"))):
        cloc_, crot_ = lib["placement"](cx, 29.62 - 0.225, 0.61, 0.45, "-y")       # tool-wall base starts at y 29.64
        put(mach["bekant_cart"](), f"Bekant_Cart_{i + 1}", cloc_, crot_, 0.305, 0.225, 0.0, 0.61, 0.45)
        zt = 1.01 + 0.018
        if what == "cricut3":
            blue = mat("Cricut3_Blue", "#C7D5E2", 0.35, coat=0.2)
            put(mach["cricut"](0.538, 0.178, 0.151, body=blue), "Cricut_Maker_3", cloc_, crot_, 0.305, 0.20, zt, 0.538, 0.178)
        else:
            put(mach["revopoint_pop3_kit"](), "Handheld_3DScanner", cloc_, crot_, 0.305, 0.20, zt, 0.40, 0.40)
        stuff = Part()                                                  # kit boxes on the cart shelves
        for zs in (0.448, 0.698):
            x = 0.02
            while x < 0.52:
                bw = rng.uniform(0.12, 0.22)
                stuff.box(MAT["bins"][rng.randrange(6)], x, min(x + bw, 0.58), 0.05, 0.38, zs, zs + rng.uniform(0.08, 0.18), bevel=0.004)
                x += bw + 0.02
        stuff.emit(f"Bekant_Cart_{i + 1}_Boxes", col, cloc_, crot_)

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
    print("textile area built")


build()
