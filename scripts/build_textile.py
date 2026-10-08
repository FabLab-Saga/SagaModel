"""Textile area by the SSW glass, on the open floor between the laser room's NNE partition (y 26.94) and the
lounge nook (x 29.7-31.7, y 27.5-29.6; daylight, ~1.5 m path to the spine side kept clear). Re-runnable ("Textile").
- Sewing table 2.0 x 1.0 m (profile + birch) with Brother sewing + embroidery + overlocker,
  fabric, scissors, pin cushion, cutting mat; four profile chairs with birch seat and back.
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

    # ---- sewing table, long side along x, chairs on both long sides
    TL, TD, TH = 2.00, 1.00, 0.76
    tc = Vector((30.70, 28.55))
    part, _ = lib["table_unit"](TL, TD, TH, [0.0, TL - 0.04], lower=())
    loc, rot = lib["placement"](tc.x, tc.y, TL, TD, "-y")
    part.emit("SewingTable", col, loc, rot)
    put(mach["sewing"](), "Brother_Sewing", loc, rot, 0.45, 0.30, TH, 0.42, 0.20)
    put(mach["sewing"](0.50, 0.24, 0.32), "Brother_Embroidery", loc, rot, 1.20, 0.30, TH, 0.50, 0.24)
    put(mach["overlock"](), "Overlock", loc, rot, 1.75, 0.72, TH, 0.33, 0.28)
    props = Part()
    fab = [bpy.data.materials["Sofa_LightGrey"], mat("Fabric_Navy", "#2B3550", 0.9),
           mat("Fabric_Mustard", "#C99A2E", 0.9), mat("Fabric_Rust", "#9B4A2C", 0.9)]
    cm = bpy.data.materials.get("CuttingMat") or MAT["ply"]
    props.box(cm, 0.15, 0.95, 0.52, 0.95, TH, TH + 0.003)                               # A1 cutting mat
    props.box(fab[2], 0.25, 0.80, 0.58, 0.90, TH + 0.003, TH + 0.008, bevel=0.002)      # fabric laid out
    props.box(fab[1], 0.20, 0.55, 0.62, 0.88, TH + 0.008, TH + 0.011, bevel=0.002)
    zz = TH
    for k in range(4):                                                                  # folded stack
        props.box(fab[k % 4], 1.55, 1.90, 0.10, 0.40, zz, zz + 0.03, bevel=0.01)
        zz += 0.031
    props.box(M["steel"] if "steel" in M else M["chrome"], 0.90, 1.08, 0.70, 0.72, TH + 0.012, TH + 0.016)   # shears blades
    props.box(mat("Shears_Orange", "#E2631C", 0.5), 0.80, 0.90, 0.69, 0.73, TH + 0.011, TH + 0.022, bevel=0.004)
    props.cyl(mat("Pincushion_Red", "#C0262D", 0.8), (0.70, 0.30, TH), (0.70, 0.30, TH + 0.05), 0.04, seg=24)
    for k in range(6):                                                                  # thread spools
        x = 0.10 + k * 0.035
        props.cyl(MAT["bins"][k % 6], (x, 0.12, TH), (x, 0.12, TH + 0.055), 0.013, seg=14)
    props.emit("SewingTable_Props", col, loc, rot)
    # four chairs, two per long side, pulled out a little at random
    for side, ry in ((-1, math.pi), (1, 0.0)):                         # chairs face the table
        for dx in (-0.55, 0.45):
            cx = tc.x + dx + rng.uniform(-0.06, 0.06)
            cy = tc.y + side * (TD / 2 + rng.uniform(0.12, 0.32))
            r = ry + rng.uniform(-0.18, 0.18)
            off = __import__("mathutils").Matrix.Rotation(r, 4, "Z") @ Vector((-0.22, -0.22, 0))
            chair().emit(f"Chair_{side}_{int(dx > 0)}", col, Vector((cx, cy, 0)) + off, r)

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
