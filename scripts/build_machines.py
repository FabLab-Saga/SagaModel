"""Machines from refs/equipment (the list supplied to the architects), as simplified
but recognisable models at the listed sizes. Re-runnable: rebuilds the "Machines"
collection. Run inside Blender: exec(open(path).read()).

Furniture comes from scripts/profile_furniture.py (black 20x20/40x40 profile + birch ply).
Placement (model frame: +X = SSW, +Y = ESE; main entrance = SSW door at y 35.1-36.2):
  Laser room (glazed room x 29.67-32.53, y 20.14-26.92): Epilog Fusion Edge 24 against
  the NNE partition; 2x Glowforge Pro HD, Glowforge Aura, xTool F1 Ultra on profile laser
  tables (sheet storage below) along the SSW glass; 100/80 mm exhausts straight out through
  the facade edge beam (Epilog run > 2.5 m gets an inline fan, per the spec).
  Print farm: profile shelving outside the laser room (2 bays x 4 levels, 0.58 m pitch):
  12x Prusa MK3S+, Bambu Lab P2S, filament bins.
  Mill table in the CNC corner: 2x Roland SRM-20. Craft machines (vinyl cutters, Cricut, Mayku,
  sewing) live in the equipment bank (scripts/build_bank_lounge.py); the SSW glass by the
  entrance is the lounge/entryway.
  CNC: ShopBot PRS Alpha 120 + ACword FT100 dust collector (clearance ignored per the brief).
  Colleague's placeholders in those spots are hidden, not deleted.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

SOFFIT = 3.93


def lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c) + (1,)


def mat(name, hexcol, rough=0.4, metal=0.0, emit=0.0, coat=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = lin(hexcol)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = lin(hexcol)
        b.inputs["Emission Strength"].default_value = emit
    m.diffuse_color = lin(hexcol)
    return m


M = {}


def materials():
    M.update(
        white=mat("Mach_White", "#EEEEEC", 0.35, coat=0.2),
        black=mat("Mach_Black", "#1B1B1C", 0.35),
        grey=mat("Mach_Grey", "#8C9093", 0.4),
        dark=mat("Mach_DarkGrey", "#3A3C3F", 0.4),
        smoke=mat("Mach_SmokedLid", "#2A2420", 0.06, coat=0.6),
        amber=mat("Mach_AmberWindow", "#C25A10", 0.05, coat=0.6),
        purple=mat("Mach_SRMCover", "#5A4A6E", 0.05, coat=0.6),
        red=mat("Mach_EpilogRed", "#C8102E", 0.35),
        orange=mat("Mach_PrusaOrange", "#FA6831", 0.45),
        chrome=mat("Mach_Chrome", "#D8DADC", 0.12, metal=1.0),
        alu=mat("Mach_AluFrame", "#151515", 0.3, metal=0.6),
        pei=mat("Mach_PEI", "#1E1C1A", 0.75),
        lcd=mat("Mach_LCD", "#3D7BD9", 0.2, emit=0.35),
        gold=mat("Mach_Gold", "#C9A24A", 0.3, metal=1.0),
        brass=mat("Mach_Brass", "#B58B4A", 0.3, metal=1.0),
        spoolflange=mat("Spool_Flange", "#202020", 0.35),
        mat_blue=mat("Cricut_Mat", "#6E8FB0", 0.6),
        label=mat("Spool_Label", "#EDEBE4", 0.7),
        desk=mat("Desk_Black", "#141414", 0.45),
        rubber=mat("Mach_Rubber", "#0E0E0E", 0.8),
        galv=bpy.data.materials.get("Galvanised") or mat("Galvanised", "#B9BEC2", 0.35, metal=1.0),
        # filament spools in the brand palette
        spools=[mat(f"Filament_{n}", h, 0.3) for n, h in (("Red", "#E03A3F"), ("Green", "#009967"), ("Blue", "#1245DE"),
                                                         ("Orange", "#FFA13D"), ("Yellow", "#F2C200"), ("Pink", "#E099AB"),
                                                         ("White", "#F2F2F0"), ("Black", "#1B1B1C"))],
    )


# ---------------------------------------------------------------- mesh builder
class Part:
    """Collects boxes/cylinders per material in a local frame (x = width, y = depth, front at y=0, z up)."""

    def __init__(self):
        self.bms = {}

    def bm(self, m):
        if m.name not in self.bms:
            self.bms[m.name] = (m, bmesh.new())
        return self.bms[m.name][1]

    def box(self, m, x0, x1, y0, y1, z0, z1, bevel=0.0):
        bm = self.bm(m)
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r["verts"]:
            v.co = Vector((x1 if v.co.x > 0 else x0, y1 if v.co.y > 0 else y0, z1 if v.co.z > 0 else z0))
        if bevel:
            edges = list({e for v in r["verts"] for e in v.link_edges})
            bmesh.ops.bevel(bm, geom=edges, offset=bevel, segments=3, affect="EDGES")

    def cyl(self, m, a, b, r, seg=16):
        a, b = Vector(a), Vector(b)
        d = b - a
        mtx = Matrix.Translation((a + b) / 2) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
        bmesh.ops.create_cone(self.bm(m), cap_ends=True, segments=seg, radius1=r, radius2=r, depth=d.length, matrix=mtx)

    def emit(self, name, col, loc, rot_z):
        """Place the part: local origin -> loc, rotated about Z by rot_z (radians)."""
        T = Matrix.Translation(loc) @ Matrix.Rotation(rot_z, 4, "Z")
        root = bpy.data.objects.new(name, None)
        col.objects.link(root)
        root.matrix_world = T
        for mname, (m, bm) in self.bms.items():
            me = bpy.data.meshes.new(f"{name}_{mname}")
            bm.to_mesh(me)
            bm.free()
            for p in me.polygons:
                p.use_smooth = True
            me.materials.append(m)
            o = bpy.data.objects.new(f"{name}_{mname}", me)
            col.objects.link(o)
            o.parent = root
        return root


# ---------------------------------------------------------------- models (front faces -y in local frame)
def desk(w, d=0.6, h=0.75):
    p = Part()
    p.box(M["desk"], 0, w, 0, d, h - 0.025, h, bevel=0.003)
    for x in (0.12, w - 0.12):
        p.box(M["desk"], x - 0.04, x + 0.04, d / 2 - 0.03, d / 2 + 0.03, 0.04, h - 0.025)       # column
        p.box(M["desk"], x - 0.035, x + 0.035, 0.03, d - 0.03, 0.0, 0.04, bevel=0.01)           # foot
    p.box(M["desk"], 0.12, w - 0.12, d / 2 - 0.025, d / 2 + 0.025, h - 0.085, h - 0.025)        # beam
    return p


def glowforge(w, d, h, lid):
    p = Part()
    p.box(M["white"], 0, w, 0, d, 0, h - 0.004, bevel=0.025)
    b = 0.045
    p.box(lid, b, w - b, b, d - b, h - 0.012, h, bevel=0.006)                                   # tinted lid
    p.box(M["white"], w * 0.3, w * 0.7, -0.012, 0.0, h * 0.55, h * 0.75, bevel=0.004)          # front handle lip
    return p


def epilog(w=1.055, d=0.834, h=0.967):
    p = Part()
    base = 0.60
    p.box(M["black"], 0.02, w - 0.02, 0.02, d - 0.02, 0.09, base, bevel=0.01)                    # cabinet
    for x in (0.08, w - 0.08):                                                                    # casters
        for y in (0.08, d - 0.08):
            p.cyl(M["rubber"], (x - 0.02, y, 0.04), (x + 0.02, y, 0.04), 0.04)
    p.box(M["grey"], 0, w, 0, d, base, h - 0.06, bevel=0.015)                                    # body
    # sloped smoked lid over the front 2/3
    p.box(M["smoke"], 0.03, w - 0.03, 0.02, d * 0.66, h - 0.06, h - 0.035, bevel=0.01)
    p.box(M["grey"], 0.0, w, d * 0.66, d, h - 0.06, h, bevel=0.012)                              # rear housing
    p.box(M["red"], 0.0, w, -0.002, 0.004, base + 0.08, base + 0.11)                             # red stripe
    p.box(M["dark"], w - 0.20, w - 0.05, d * 0.70, d * 0.92, h, h + 0.012, bevel=0.004)         # control panel
    p.box(M["lcd"], w - 0.18, w - 0.08, d * 0.73, d * 0.80, h + 0.012, h + 0.014)
    return p


def xtool(w=0.493, d=0.253, h=0.373):
    p = Part()
    p.box(M["dark"], 0, w, 0, d, 0, h, bevel=0.012)
    p.box(M["amber"], 0.03, w - 0.03, -0.004, 0.02, 0.08, h - 0.05, bevel=0.006)               # shield window
    return p


PRINT_RNG = __import__('random').Random(5)


def spool_part(p, filament, cx, cy, cz, axis="x", r_out=0.100, width=0.065):
    """Real filament spool: two thin flanges, cardboard/plastic hub, wound filament, axis along x."""
    ax = Vector((1, 0, 0)) if axis == "x" else Vector((0, 1, 0))
    c = Vector((cx, cy, cz))
    for side in (-1, 1):
        a0 = c + ax * side * (width / 2)
        p.cyl(M["spoolflange"], a0 - ax * 0.002, a0 + ax * 0.002, r_out, seg=48)
    p.cyl(filament, c - ax * (width / 2 - 0.003), c + ax * (width / 2 - 0.003), r_out * 0.82, seg=48)
    for k in range(1, 9):                                                    # wound-filament grooves
        g = c - ax * (width / 2 - 0.003) + ax * (width - 0.006) * k / 9
        p.cyl(M["dark"], g - ax * 0.0004, g + ax * 0.0004, r_out * 0.821, seg=48)
    lab = c + ax * (width / 2 + 0.0025)                                          # label on the outer flange
    p.cyl(M["label"], lab, lab + ax * 0.0006, 0.045, seg=32)
    p.cyl(M["dark"], c - ax * (width / 2 + 0.003), c + ax * (width / 2 + 0.003), 0.027, seg=24)


def prusa(spool):
    """Prusa MK3S+ (~500 x 550 x 400): frame plate, rods, motors, PEI bed, orange parts, LCD, spool on top."""
    p = Part()
    w, d = 0.50, 0.55
    fy = 0.31                                                                                    # frame plane (y)
    # --- base: Y frame (aluminium extrusions + printed corners) and the PSU at the back
    for x in (0.10, w - 0.12):
        p.box(M["alu"], x, x + 0.02, 0.03, d - 0.03, 0.0, 0.03, bevel=0.002)
    for y in (0.03, d - 0.06):
        p.box(M["orange"], 0.07, w - 0.07, y, y + 0.03, 0.0, 0.05, bevel=0.004)
    p.box(M["black"], w - 0.11, w - 0.02, fy + 0.02, d - 0.05, 0.0, 0.07, bevel=0.003)          # PSU
    # --- Y axis: smooth rods + carriage + heatbed
    for x in (0.16, w - 0.16):
        p.cyl(M["chrome"], (x, 0.06, 0.035), (x, d - 0.06, 0.035), 0.004, seg=10)
    bed_y = 0.12
    p.box(M["alu"], 0.12, w - 0.12, bed_y, bed_y + 0.25, 0.048, 0.054)                          # Y carriage
    p.box(M["pei"], 0.125, w - 0.125, bed_y - 0.005, bed_y + 0.255, 0.060, 0.064, bevel=0.002)  # PEI sheet
    p.box(M["gold"], 0.124, w - 0.124, bed_y - 0.006, bed_y + 0.256, 0.058, 0.0605)             # sheet edge
    # --- main frame plate (black aluminium) with its big window: four bars
    t = 0.006
    p.box(M["alu"], 0.02, 0.08, fy, fy + t, 0.0, 0.40, bevel=0.002)                              # left post
    p.box(M["alu"], w - 0.08, w - 0.02, fy, fy + t, 0.0, 0.40, bevel=0.002)                      # right post
    p.box(M["alu"], 0.02, w - 0.02, fy, fy + t, 0.35, 0.40, bevel=0.002)                         # top bar
    p.box(M["alu"], 0.02, w - 0.02, fy, fy + t, 0.0, 0.07, bevel=0.002)                          # bottom bar
    # --- Z axis: motors at the bottom, threaded + smooth rods, top bracket
    for x in (0.05, w - 0.05):
        p.box(M["black"], x - 0.021, x + 0.021, fy - 0.045, fy - 0.003, 0.0, 0.042, bevel=0.003)  # NEMA17
        p.box(M["chrome"], x - 0.021, x + 0.021, fy - 0.045, fy - 0.003, 0.042, 0.046)
        p.cyl(M["brass"], (x, fy - 0.024, 0.046), (x, fy - 0.024, 0.37), 0.004, seg=10)          # leadscrew
        p.cyl(M["chrome"], (x + 0.03 * (1 if x < w / 2 else -1), fy - 0.024, 0.07),
              (x + 0.03 * (1 if x < w / 2 else -1), fy - 0.024, 0.38), 0.004, seg=10)
        p.box(M["orange"], x - 0.03, x + 0.04 if x < w / 2 else x + 0.03, fy - 0.05, fy, 0.37, 0.40, bevel=0.004)
    # --- X axis at print height: two rods, X-ends, extruder + fan + nozzle
    zx = 0.20
    for dz in (0.0, 0.045):
        p.cyl(M["chrome"], (0.07, fy - 0.035, zx + dz), (w - 0.07, fy - 0.035, zx + dz), 0.004, seg=10)
    for x0 in (0.035, w - 0.095):
        p.box(M["orange"], x0, x0 + 0.06, fy - 0.06, fy - 0.004, zx - 0.025, zx + 0.07, bevel=0.005)
    p.box(M["black"], 0.025, 0.07, fy - 0.10, fy - 0.06, zx - 0.02, zx + 0.025, bevel=0.003)      # X motor
    ex = w * 0.42
    p.box(M["orange"], ex, ex + 0.07, fy - 0.10, fy - 0.03, zx - 0.03, zx + 0.10, bevel=0.006)    # extruder body
    p.box(M["black"], ex + 0.012, ex + 0.058, fy - 0.112, fy - 0.10, zx + 0.0, zx + 0.05, bevel=0.003)  # hotend fan
    p.box(M["black"], ex + 0.015, ex + 0.055, fy - 0.07, fy - 0.03, zx + 0.10, zx + 0.14, bevel=0.003)  # extruder motor
    p.cyl(M["brass"], (ex + 0.035, fy - 0.07, zx - 0.03), (ex + 0.035, fy - 0.07, zx - 0.05), 0.004, seg=10)  # nozzle
    p.cyl(M["dark"], (ex + 0.035, fy - 0.07, zx + 0.14), (ex + 0.035, fy + 0.04, 0.47), 0.003, seg=8)   # PTFE/filament path
    # --- close-up detail: screw heads on printed parts, hotend fan grille, sleeved cable bundle
    def screws(x0, x1, z0, z1, yface, n=2):
        for i in range(n):
            for zz in (z0 + 0.012, z1 - 0.012):
                xx = x0 + (i + 0.5) * (x1 - x0) / n
                p.cyl(M["chrome"], (xx, yface - 0.0015, zz), (xx, yface, zz), 0.0028, seg=10)
    screws(ex, ex + 0.07, zx - 0.03, zx + 0.10, fy - 0.10)
    for x0 in (0.035, w - 0.095):
        screws(x0, x0 + 0.06, zx - 0.025, zx + 0.07, fy - 0.06, n=1)
    for k in range(4):                                                                          # fan grille rings
        r = 0.006 + k * 0.0045
        p.cyl(M["dark"], (ex + 0.035, fy - 0.1125, zx + 0.025), (ex + 0.035, fy - 0.1121, zx + 0.025), r, seg=24)
        p.cyl(M["black"], (ex + 0.035, fy - 0.1127, zx + 0.025), (ex + 0.035, fy - 0.1123, zx + 0.025), r - 0.0018, seg=24)
    for k in range(5):                                                                          # sleeved bundle arc to the frame
        t0, t1 = k / 5, (k + 1) / 5
        a = (ex + 0.05 + t0 * 0.12, fy - 0.03 + t0 * 0.03, zx + 0.10 + 0.08 * (1 - (2 * t0 - 1) ** 2))
        b = (ex + 0.05 + t1 * 0.12, fy - 0.03 + t1 * 0.03, zx + 0.10 + 0.08 * (1 - (2 * t1 - 1) ** 2))
        p.cyl(M["black"], a, b, 0.006, seg=10)
    # --- LCD box at the front left
    p.box(M["orange"], 0.10, 0.36, -0.035, 0.03, 0.01, 0.085, bevel=0.006)
    p.box(M["lcd"], 0.13, 0.27, -0.0365, -0.034, 0.03, 0.07)
    p.cyl(M["dark"], (0.31, -0.045, 0.05), (0.31, -0.035, 0.05), 0.011, seg=20)                  # knob
    # --- spool holder on the top bar + spool
    p.box(M["orange"], w / 2 - 0.012, w / 2 + 0.012, fy - 0.01, fy + 0.03, 0.40, 0.46, bevel=0.003)
    spool_part(p, spool, w / 2, fy + 0.045, 0.47)
    if PRINT_RNG.random() < 0.55:                                                               # a print in progress
        kind = PRINT_RNG.choice(("box", "vase", "bracket"))
        bx, by = w / 2 + PRINT_RNG.uniform(-0.06, 0.06), bed_y + 0.12 + PRINT_RNG.uniform(-0.04, 0.04)
        hgt = PRINT_RNG.uniform(0.015, 0.09)
        if kind == "vase":
            p.cyl(spool, (bx, by, 0.064), (bx, by, 0.064 + hgt), PRINT_RNG.uniform(0.025, 0.045), seg=40)
        elif kind == "box":
            sx, sy = PRINT_RNG.uniform(0.03, 0.09), PRINT_RNG.uniform(0.03, 0.09)
            p.box(spool, bx - sx / 2, bx + sx / 2, by - sy / 2, by + sy / 2, 0.064, 0.064 + hgt, bevel=0.002)
        else:
            p.box(spool, bx - 0.05, bx + 0.05, by - 0.015, by + 0.015, 0.064, 0.072, bevel=0.0015)
            p.box(spool, bx - 0.05, bx - 0.04, by - 0.015, by + 0.015, 0.072, 0.064 + hgt, bevel=0.0015)
    return p


def bambu(w=0.392, d=0.406, h=0.478):
    p = Part()
    p.box(M["dark"], 0, w, 0, d, 0, h, bevel=0.01)
    p.box(M["smoke"], 0.02, w - 0.02, -0.004, 0.01, 0.06, h - 0.03, bevel=0.004)               # glass door
    p.box(M["smoke"], 0.02, w - 0.02, 0.02, d - 0.02, h, h + 0.004)                             # glass top
    return p


def srm20(w=0.451, d=0.426, h=0.426):
    p = Part()
    p.box(M["white"], 0, w, 0.05, d, 0, h, bevel=0.015)
    p.box(M["purple"], 0.02, w - 0.02, 0.0, 0.32, 0.06, h - 0.02, bevel=0.01)                  # tinted cover
    return p


def vinyl(w=0.851, d=0.310, h=0.235):
    """Roland desktop vinyl cutter: grey body, black end caps, pinch-roller slot, vinyl roll behind."""
    p = Part()
    p.box(M["grey"], 0.07, w - 0.07, 0.05, d - 0.02, 0.03, h, bevel=0.025)
    for x0 in (0.0, w - 0.07):
        p.box(M["black"], x0, x0 + 0.07, 0.02, d, 0.0, h + 0.01, bevel=0.02)
    p.box(M["dark"], 0.07, w - 0.07, 0.035, 0.07, 0.10, 0.125, bevel=0.003)                   # media slot
    p.box(M["white"], 0.10, w - 0.10, 0.02, 0.05, 0.106, 0.110)                               # vinyl coming out
    p.box(M["black"], w - 0.16, w - 0.08, 0.16, 0.26, h - 0.002, h + 0.006, bevel=0.003)      # control panel
    p.box(M["lcd"], w - 0.15, w - 0.11, 0.18, 0.21, h + 0.006, h + 0.007)
    p.cyl(M["spools"][2], (0.12, d + 0.07, 0.07), (w - 0.12, d + 0.07, 0.07), 0.04, seg=32)   # roll on stand
    p.cyl(M["chrome"], (0.08, d + 0.07, 0.07), (w - 0.08, d + 0.07, 0.07), 0.008, seg=12)
    return p


def mayku(w=0.274, d=0.466, h=0.315):
    p = Part()
    p.box(M["white"], 0, w, 0.05, d - 0.05, 0, h, bevel=0.02)
    for y in (0.0, d - 0.05):
        p.box(M["dark"], 0.06, w - 0.06, y, y + 0.05, h * 0.6, h * 0.7, bevel=0.008)           # handles
    return p


def sewing(w=0.42, d=0.20, h=0.30):
    """Domestic sewing machine: bed, pillar, arm, needle head, hand wheel, thread spool, screen."""
    p = Part()
    p.box(M["white"], 0, w, 0, d, 0, 0.085, bevel=0.018)                                  # bed
    p.box(M["white"], w - 0.12, w - 0.01, 0.015, d - 0.015, 0.06, h, bevel=0.025)          # pillar
    p.box(M["white"], 0.02, w - 0.01, 0.025, d - 0.025, h - 0.085, h, bevel=0.025)         # arm
    p.box(M["white"], 0.02, 0.10, 0.03, d - 0.03, 0.12, h - 0.06, bevel=0.012)            # needle head
    p.cyl(M["chrome"], (0.06, 0.07, 0.09), (0.06, 0.07, 0.125), 0.003, seg=8)            # needle
    p.box(M["chrome"], 0.045, 0.085, 0.05, 0.09, 0.085, 0.09)                             # presser foot
    p.cyl(M["white"], (w - 0.005, d / 2, h - 0.06), (w + 0.025, d / 2, h - 0.06), 0.045, seg=32)  # hand wheel
    p.cyl(M["chrome"], (w - 0.06, d / 2, h), (w - 0.06, d / 2, h + 0.05), 0.003, seg=8)  # spool pin
    p.cyl(M["spools"][0], (w - 0.06, d / 2, h + 0.005), (w - 0.06, d / 2, h + 0.045), 0.016, seg=20)
    p.box(M["lcd"], w - 0.10, w - 0.04, -0.001, 0.0, 0.15, 0.22)
    p.box(M["dark"], 0.11, w - 0.13, -0.001, 0.0, h - 0.07, h - 0.04)                     # front decal strip
    return p


def cricut(w=0.60, d=0.179, h=0.158):
    """Cricut Maker: rounded white body, lid open, grey mat feeding through the front."""
    p = Part()
    p.box(M["white"], 0, w, 0.03, d, 0, h * 0.75, bevel=0.035)
    p.box(M["grey"], 0.06, w - 0.06, 0.05, d - 0.03, h * 0.75 - 0.01, h * 0.75 + 0.005, bevel=0.004)   # carriage bay
    p.box(M["dark"], w * 0.35, w * 0.48, 0.07, 0.13, h * 0.75, h * 0.75 + 0.05, bevel=0.006)          # tool carriage
    p.box(M["white"], 0.0, w, -0.11, -0.10, h * 0.75 - 0.005, h * 0.75 + 0.12, bevel=0.01)          # open lid
    p.box(M["mat_blue"], 0.03, w - 0.03, -0.22, d + 0.08, 0.035, 0.037)                               # cutting mat
    return p


def overlock(w=0.33, d=0.28, h=0.29):
    p = Part()
    p.box(M["white"], 0, w, 0, d, 0, h * 0.7, bevel=0.03)
    for i, x in enumerate((0.08, 0.13, 0.18, 0.23)):                                            # thread cones
        p.cyl(M["spools"][i], (x, d * 0.6, h * 0.7), (x, d * 0.6, h * 1.25), 0.018, seg=12)
    return p


def shopbot(W=2.15, Lg=4.30):
    """ShopBot PRS Alpha 120 (60" x 120" table): black steel frame, MDF spoilboard, aluminium gantry."""
    p = Part()
    blk, alu, mdf = M["black"], M["alusatin"], M["mdf"]
    for x in (0.08, W - 0.20):                                                                  # side beams
        p.box(blk, x, x + 0.12, 0.0, Lg, 0.62, 0.82, bevel=0.004)
        p.box(alu, x + 0.02, x + 0.10, 0.0, Lg, 0.82, 0.85)                                    # Y rails
    for y in (0.15, 1.45, 2.85, Lg - 0.23):                                                    # legs + feet + cross members
        for x in (0.10, W - 0.18):
            p.box(blk, x, x + 0.08, y, y + 0.08, 0.04, 0.62)
            p.cyl(M["rubber"], (x + 0.04, y + 0.04, 0.0), (x + 0.04, y + 0.04, 0.04), 0.045, seg=16)
        p.box(blk, 0.10, W - 0.10, y, y + 0.06, 0.25, 0.31)
        p.box(blk, 0.10, W - 0.10, y, y + 0.06, 0.70, 0.78)
    p.box(mdf, 0.22, W - 0.22, 0.10, Lg - 0.10, 0.80, 0.86)                                   # spoilboard
    for i in range(12):                                                                         # surfacing marks
        y = 0.25 + i * 0.32
        p.box(M["mdfdark"], 0.24, W - 0.24, y, y + 0.004, 0.8601, 0.8605)
    gy = Lg * 0.42                                                                              # gantry position
    for x in (0.02, W - 0.12):                                                                  # gantry side cars
        p.box(blk, x, x + 0.10, gy - 0.20, gy + 0.20, 0.78, 1.32, bevel=0.006)
    p.box(alu, 0.0, W, gy - 0.07, gy + 0.07, 1.20, 1.40, bevel=0.006)                          # gantry beam
    p.box(blk, 0.0, W, gy + 0.07, gy + 0.09, 1.30, 1.40)                                       # cable tray on beam
    cx = W * 0.45
    p.box(blk, cx - 0.14, cx + 0.14, gy - 0.16, gy - 0.07, 1.10, 1.45, bevel=0.005)            # X car
    p.box(blk, cx - 0.08, cx + 0.08, gy - 0.26, gy - 0.16, 0.98, 1.52, bevel=0.005)            # Z axis
    p.cyl(alu, (cx, gy - 0.21, 0.95), (cx, gy - 0.21, 1.18), 0.045, seg=24)                    # spindle
    p.cyl(blk, (cx, gy - 0.21, 0.90), (cx, gy - 0.21, 0.95), 0.10, seg=24)                     # dust shoe
    p.box(blk, W - 0.06, W, 0.2, Lg - 0.2, 0.86, 0.96)                                          # cable chain
    return p


def dust_collector(w=0.84, d=0.50, h=2.20):
    """ACword FT100 single-bag collector: stand, motor/impeller, white filter bag, clear lower bag."""
    p = Part()
    cx = w / 2
    for x in (0.08, w - 0.12):
        for y in (0.08, d - 0.12):
            p.box(M["dark"], x, x + 0.04, y, y + 0.04, 0.0, 1.0)
    p.cyl(M["dark"], (cx, d / 2, 0.98), (cx, d / 2, 1.06), 0.27, seg=32)                       # ring
    p.cyl(M["grey"], (cx - 0.05, d / 2, 1.12), (cx + 0.30, d / 2, 1.12), 0.17, seg=28)         # motor
    p.cyl(M["grey"], (cx, -0.02, 1.12), (cx, d / 2, 1.12), 0.06, seg=20)                       # inlet
    p.cyl(M["felt"], (cx, d / 2, 1.06), (cx, d / 2, h - 0.06), 0.24, seg=32)                   # filter bag
    bmesh.ops.create_uvsphere(p.bm(M["felt"]), u_segments=32, v_segments=8, radius=0.24,
                              matrix=Matrix.Translation((cx, d / 2, h - 0.06)) @ Matrix.Scale(0.25, 4, (0, 0, 1)))
    p.cyl(M["bag"], (cx, d / 2, 0.10), (cx, d / 2, 0.98), 0.24, seg=32)                       # chip bag
    return p


def control_box(w=0.50, d=0.30, h=0.70):
    p = Part()
    p.box(M["grey"], 0, w, 0, d, 0, h, bevel=0.01)
    p.box(M["red"], w * 0.4, w * 0.6, -0.02, 0.0, h * 0.75, h * 0.85, bevel=0.005)            # e-stop
    return p


def sheets(n, w, d, colors):
    """A stack of material sheets (ply + coloured acrylic)."""
    p = Part()
    z = 0.0
    for i in range(n):
        t = 0.006 if i % 2 else 0.003
        p.box(colors[i % len(colors)], 0, w, 0, d, z, z + t)
        z += t
    return p


def spool_stack(n):
    """Spare spools standing on edge in a row, facing the front."""
    p = Part()
    for i in range(n):
        spool_part(p, M["spools"][i % len(M["spools"])], 0.05 + i * 0.072, 0.06, 0.10, axis="x", width=0.062)
    return p


# ---------------------------------------------------------------- placement helpers
FACE = {"-x": -math.pi / 2, "+x": math.pi / 2, "-y": 0.0, "+y": math.pi}   # rotation so local front (-y) faces this way


def place(part, name, col, cx, cy, z, w, d, facing):
    """Centre a w x d footprint at (cx, cy) on height z, front facing `facing`."""
    rot = FACE[facing]
    off = Matrix.Rotation(rot, 4, "Z") @ Vector((-w / 2, -d / 2, 0))
    return part.emit(name, col, Vector((cx, cy, z)) + off, rot)


def exhaust(col, name, pts, r=0.05):
    p = Part()
    for a, b in zip(pts, pts[1:]):
        p.cyl(M["galv"], a, b, r, seg=20)
    for q in pts[1:-1]:
        bmesh.ops.create_uvsphere(p.bm(M["galv"]), u_segments=20, v_segments=10, radius=r, matrix=Matrix.Translation(q))
    return p.emit(name, col, Vector((0, 0, 0)), 0.0)


def set_hidden(names, hidden=True):
    n = 0
    for nm in names:
        o = bpy.data.objects.get(nm)
        if not o:
            continue
        for k in (o, *o.children_recursive):
            k.hide_render = k.hide_viewport = hidden
        n += 1
    return n


def build():
    scene = bpy.context.scene
    lib = {}
    exec(open(bpy.path.abspath("//scripts/profile_furniture.py")).read(), lib)
    lib["materials"]()
    col = bpy.data.collections.get("Machines") or bpy.data.collections.new("Machines")
    fcol = bpy.data.collections.get("Furniture") or bpy.data.collections.new("Furniture")
    for c in (col, fcol):
        if c.name not in scene.collection.children:
            scene.collection.children.link(c)
        for o in list(c.objects):
            data = o.data
            bpy.data.objects.remove(o)
            if data is not None and data.users == 0:
                (bpy.data.curves if isinstance(data, bpy.types.Curve) else bpy.data.meshes).remove(data)
    materials()
    M.update(alusatin=mat("Mach_AluSatin", "#C3C7CB", 0.3, metal=1.0), mdf=mat("MDF", "#B48C5C", 0.8),
             mdfdark=mat("MDF_Mark", "#8E6C45", 0.8), felt=mat("FilterFelt", "#ECEAE4", 0.95),
             bag=mat("ChipBag", "#C9CED1", 0.25, coat=0.5), hose=mat("Hose_Flex", "#3B3F43", 0.55))

    # ---- placeholders out, ESE shelf boards back
    ph = ["Component_1046510", "Component_1046510.001", "PRSalpha 9660"]
    for o in bpy.data.objects["ROOT"].children:                       # shallow shelves along the SSW glass
        if o.name.startswith(("Component_1062473", "Component_1484326", "Component_1483885")):
            pts = [k.matrix_world @ Vector(c) for k in o.children_recursive if k.type == "MESH" for c in k.bound_box]
            if pts and min(p.x for p in pts) > 31.0:
                ph.append(o.name)
    hidden = set_hidden(ph)
    for unit in ("Component_289785", "Component_289785.001", "Component_289785.002"):
        for c in bpy.data.objects[unit].children_recursive:
            if c.type == "MESH" and c.parent.name.startswith("Plywood") and [m.name for m in c.data.materials] != ["Material_1"]:
                c.hide_render = c.hide_viewport = False

    def unit_on(part_dims, cx, cy, facing):
        w, d = part_dims
        return lib["placement"](cx, cy, w, d, facing)

    def put(part, name, loc, rot, local_xy, z, w, d):
        """Machine centred at a local point of a furniture unit, same facing as the unit."""
        c = lib["to_world"](loc, rot, (local_xy[0], local_xy[1], 0))
        off = Matrix.Rotation(rot, 4, "Z") @ Vector((-w / 2, -d / 2, 0))
        return part.emit(name, col, Vector((c.x, c.y, z)) + off, rot)

    # ---- laser room: profile laser tables along the SSW glass
    T_D, T_H = 0.65, 0.78
    tables = [("LaserTable_250", 2.5, [0.0, 1.23, 2.46], 20.30 + 1.25), ("LaserTable_200", 2.0, [0.0, 1.96], 22.85 + 1.0)]
    tloc = {}
    for name, L, legs, cy in tables:
        part, _ = lib["table_unit"](L, T_D, T_H, legs, lower=(0.16,))
        loc, rot = unit_on((L, T_D), 32.45 - T_D / 2, cy, "-x")
        part.emit(name, fcol, loc, rot)
        tloc[name] = (loc, rot, L)
        P, B = lib["MAT"]["ply"], lib["MAT"]["bins"]                    # mostly ply, a few acrylic sheets, ply on top
        st = sheets(7, L - 0.20, T_D - 0.08, [P])
        put(st, f"{name}_Sheets", loc, rot, (L / 2, T_D / 2), 0.16, L - 0.20, T_D - 0.08)
    gx = 32.45 - 0.03                                                   # back edge of the laser tables
    for i, y in enumerate((20.85, 22.00)):
        place(glowforge(0.965, 0.527, 0.211, M["smoke"]), f"Glowforge_ProHD_{i + 1}", col, gx - 0.527 / 2, y, T_H, 0.965, 0.527, "-x")
    place(glowforge(0.556, 0.521, 0.127, M["grey"]), "Glowforge_Aura", col, gx - 0.521 / 2, 23.25, T_H, 0.556, 0.521, "-x")
    place(xtool(), "xTool_F1_Ultra", col, gx - 0.02 - 0.253 / 2, 24.05, T_H, 0.493, 0.253, "-x")
    place(epilog(), "Epilog_FusionEdge24", col, 29.70 + 0.834 / 2, 20.30 + 1.055 / 2 + 0.05, 0, 1.055, 0.834, "+x")
    ZE, XOUT = 3.75, 32.85
    for name, y, z0, r in (("Glowforge_ProHD_1", 20.85, T_H + 0.10, 0.05), ("Glowforge_ProHD_2", 22.00, T_H + 0.10, 0.05),
                           ("Glowforge_Aura", 23.25, T_H + 0.08, 0.05), ("xTool_F1_Ultra", 24.05, T_H + 0.25, 0.04)):
        exhaust(col, f"Exhaust_{name}", [(gx - 0.01, y, z0), (gx - 0.01, y, ZE), (XOUT, y, ZE)], r)
    ye = 20.30 + 1.055 / 2 + 0.05
    exhaust(col, "Exhaust_Epilog", [(29.75, ye, 0.85), (29.75, ye, ZE), (XOUT, ye, ZE)], 0.05)
    fan = Part()
    fan.cyl(M["galv"], (30.9, ye, ZE), (31.25, ye, ZE), 0.13, seg=28)
    fan.emit("Exhaust_Epilog_InlineFan", col, Vector((0, 0, 0)), 0.0)
    hoods = Part()
    for y in (20.85, 22.00, 23.25, 24.05, ye):
        hoods.box(M["galv"], XOUT, XOUT + 0.06, y - 0.09, y + 0.09, ZE - 0.09, ZE + 0.09, bevel=0.01)
    hoods.emit("Exhaust_Hoods", col, Vector((0, 0, 0)), 0.0)

    # ---- print farm outside the laser room (against its NNE partition, x 28.90-29.50)
    PF_D, levels = 0.60, [0.15, 0.73, 1.31, 1.89]
    part, slots, L = lib["shelf_unit"]([1.62, 1.62], PF_D, 2.42, levels, power=True)
    loc, rot = unit_on((L, PF_D), 29.50 - PF_D / 2, 21.95 + L / 2, "-x")
    part.emit("PrintFarm_Shelving", fcol, loc, rot)
    k = 0
    for li in (1, 2):
        for bi in (0, 1):
            xa, xb, _, _, zt = slots[(bi, li)]
            for i in range(3):
                spool = M["spools"][k % len(M["spools"])]
                put(prusa(spool), f"Prusa_MK3S_{k + 1:02d}", loc, rot, (xa + 0.03 + 0.25 + i * 0.52, PF_D / 2), zt, 0.50, 0.55)
                k += 1
    xa, xb, _, _, zt = slots[(0, 3)]
    put(bambu(), "Bambu_P2S", loc, rot, (xa + 0.35, PF_D / 2), zt, 0.392, 0.406)
    put(spool_stack(8), "Spare_Spools", loc, rot, ((xa + xb) / 2 + 0.35, PF_D / 2), zt, 0.85, 0.12)
    xa, xb, _, _, zt = slots[(1, 3)]
    put(spool_stack(12), "Spare_Spools_2", loc, rot, ((xa + xb) / 2, PF_D / 2), zt, 0.85, 0.12)
    bins = Part()
    for bi in (0, 1):                                                  # filament dry bins on the bottom level
        xa, xb, _, _, zt = slots[(bi, 0)]
        for i in range(3):
            lib["bin_box"](bins, lib["MAT"]["bins"][(bi * 3 + i) % 6], xa + 0.05 + i * 0.52, 0.12, zt, w=0.46, d=0.42, h=0.30)
            for j in range(3):                                         # spare spools standing in each bin
                spool_part(bins, M["spools"][(bi * 7 + i * 3 + j) % len(M["spools"])],
                           xa + 0.05 + i * 0.52 + 0.23, 0.17 + j * 0.105, zt + 0.21, axis="y", width=0.06)
    bins.emit("PrintFarm_Bins", fcol, loc, rot)

    # ---- CNC room: ShopBot PRS Alpha 120 against the interior wall (x 24.15), collector out by the far glass
    #      corner, control box on the glass side (user layout, 2026-10-07)
    W, Lg = 2.15, 4.30
    sb_loc = Vector((24.13 - W, 22.75 - Lg, 0.0))
    shopbot(W, Lg).emit("ShopBot_PRSAlpha_120", col, sb_loc, 0.0)
    place(dust_collector(), "ACword_FT100", col, 21.50, 16.45, 0.0, 0.84, 0.50, "+y")
    place(control_box(), "ShopBot_Control", col, 21.17, 21.95, 0.0, 0.50, 0.30, "+x")
    gy = sb_loc.y + Lg * 0.42                                           # flexible hose: dust shoe -> overhead -> collector
    hx = sb_loc.x + W * 0.45
    hose_pts = [(hx, gy - 0.21, 1.52), (hx, gy - 0.21, 2.20), (hx - 0.35, gy - 0.9, 2.50), (21.90, 17.80, 2.40),
                (21.55, 17.05, 1.90), (21.50, 16.85, 1.30), (21.50, 16.72, 1.12)]
    cu = bpy.data.curves.new("ShopBot_DustHose", "CURVE")
    cu.dimensions = "3D"; cu.bevel_depth = 0.052; cu.bevel_resolution = 4; cu.resolution_u = 16
    sp = cu.splines.new("NURBS"); sp.points.add(len(hose_pts) - 1)
    for pt, q in zip(sp.points, hose_pts):
        pt.co = (*q, 1.0)
    sp.use_endpoint_u = True; sp.order_u = 4
    cu.materials.append(M["hose"])
    col.objects.link(bpy.data.objects.new("ShopBot_DustHose", cu))
    return k, hidden


k, hidden = build()
print("printers", k, "| placeholders hidden", hidden)
