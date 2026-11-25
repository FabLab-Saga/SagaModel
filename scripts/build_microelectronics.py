"""Microelectronics zone at the tool-wall row + low tool shelving along the NNE glass. Re-runnable.

Tool-wall row: three 2 m OSB walls (x 21.05-27.17), felt on the WNW (-y) side, tools on the
ESE (+y) side. This replaces the colleague's hammers/saws with electronics: wall-mounted
small-parts drawer cabinets, a tool rail (pliers, flush cutters, screwdrivers, tweezers),
hook-up wire spools on a rod, a hanging multimeter. In front: a profile workbench with the
Roland MDX-20, 3 soldering stations + fume extractors, oscilloscope, bench PSU, PCBs,
magnifier lamp, stools. Along the NNE glass (y 23.25-26.35): low profile shelving with
tool cases, toolboxes and bins (low so the daylight stays).
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
_c = open(HERE + "build_craft_spine.py").read()
craft = {}
exec(_c[:_c.index("\ndef build():")], craft)
Part, mat = lib["Part"], lib["simple_mat"]
rng = random.Random(42)

ROW = ["Component_1346962", "Component_1346962.001", "Component_1346962.002"]
X0, X1 = 21.05, 27.17


def mats():
    return dict(
        red=mat("Tool_RedGrip", "#B5221E", 0.55), blue=mat("Tool_BlueGrip", "#1F4E9C", 0.55),
        yellow=mat("Tool_Yellow", "#E8B41C", 0.45), black=mat("Tool_Black", "#151515", 0.5),
        steel=mat("Tool_Steel", "#B9BDC1", 0.25, metal=1.0), grey=mat("Cab_Grey", "#5E6266", 0.45),
        clear=mat("Drawer_Clear", "#D9E2E6", 0.08), label=mat("Drawer_Label", "#F3F1EA", 0.6),
        pcb=mat("PCB_Green", "#1E6B3A", 0.35), copper=mat("PCB_Copper", "#C88A4B", 0.3, metal=1.0),
        screen=mat("Scope_Screen", "#0F2236", 0.15, emit=0.6), cream=mat("MDX_Cream", "#E7E2D6", 0.4),
        solder=mat("Solder", "#C9CCCF", 0.3, metal=1.0), lampwhite=mat("Lamp_White", "#EEEEEA", 0.35),
    )


# ---------------------------------------------------------------- small objects (local frame: front = -y, z up)
def drawer_cabinet(m, cols=6, rows=8):
    """Wall-mounted small-parts cabinet (Raaco/Akro style): grey frame, clear drawers, white labels."""
    p = Part()
    dw, dh, d = 0.065, 0.045, 0.14
    W, H = cols * dw + 0.02, rows * dh + 0.02
    p.box(m["grey"], 0, W, 0.0, d, 0, H, bevel=0.003)
    for i in range(cols):
        for j in range(rows):
            x, z = 0.01 + i * dw, 0.01 + j * dh
            p.box(m["clear"], x + 0.003, x + dw - 0.003, -0.004, 0.002, z + 0.003, z + dh - 0.003, bevel=0.002)
            p.box(m["label"], x + 0.015, x + dw - 0.015, -0.0045, -0.004, z + dh - 0.016, z + dh - 0.008)
            if rng.random() < 0.7:                                       # parts visible through the clear front
                c = rng.choice((m["red"], m["blue"], m["yellow"], m["black"], m["steel"], m["copper"], m["pcb"]))
                p.box(c, x + 0.008, x + dw - 0.008, 0.0, 0.03, z + 0.005, z + 0.005 + rng.uniform(0.008, 0.02))
    return p, W, H


def pliers(p, m, x, z, grip):
    """Hanging pliers/cutters: two handles + steel head, hanging head-up."""
    p.box(m["steel"], x - 0.008, x + 0.008, -0.012, -0.002, z, z + 0.05, bevel=0.002)
    for dx in (-0.012, 0.012):
        p.box(grip, x + dx - 0.006, x + dx + 0.006, -0.013, -0.001, z - 0.12, z, bevel=0.004)


def screwdriver(p, m, x, z, grip):
    p.cyl(m["steel"], (x, -0.008, z - 0.10), (x, -0.008, z + 0.04), 0.0025, seg=8)
    p.cyl(grip, (x, -0.008, z + 0.04), (x, -0.008, z + 0.15), 0.013, seg=12)


def tweezers(p, m, x, z):
    p.box(m["steel"], x - 0.004, x - 0.002, -0.006, -0.004, z - 0.11, z)
    p.box(m["steel"], x + 0.002, x + 0.004, -0.006, -0.004, z - 0.11, z)


def multimeter(p, m, x, z):
    p.box(m["yellow"], x, x + 0.09, -0.04, 0.0, z, z + 0.18, bevel=0.01)
    p.box(m["screen"], x + 0.015, x + 0.075, -0.0405, -0.04, z + 0.12, z + 0.165)
    p.cyl(m["black"], (x + 0.045, -0.042, z + 0.075), (x + 0.045, -0.04, z + 0.075), 0.024, seg=24)
    for dx, c in ((0.025, m["red"]), (0.065, m["black"])):               # test leads hanging
        p.cyl(c, (x + dx, -0.02, z), (x + dx, -0.03, z - 0.35), 0.0025, seg=6)


def wire_rod(p, m, x0, z):
    cols = MAT["bins"] + [m["black"], mat("Wire_White", "#EDEDE8", 0.4)]
    p.cyl(m["steel"], (x0, -0.06, z), (x0 + 0.62, -0.06, z), 0.005, seg=8)
    for i in range(8):
        cx = x0 + 0.04 + i * 0.075
        p.cyl(m["black"], (cx - 0.028, -0.06, z), (cx - 0.026, -0.06, z), 0.045, seg=24)
        p.cyl(cols[i % len(cols)], (cx - 0.026, -0.06, z), (cx + 0.026, -0.06, z), 0.036, seg=24)
        p.cyl(m["black"], (cx + 0.026, -0.06, z), (cx + 0.028, -0.06, z), 0.045, seg=24)
    for x in (x0, x0 + 0.62):
        p.box(m["steel"], x - 0.005, x + 0.005, -0.065, 0.0, z - 0.06, z + 0.01)


def mdx20(m):
    """Roland MDX-20: cream base + yellow-tinted clear cover, spindle carriage visible."""
    p = Part()
    w, d, h = 0.362, 0.300, 0.305
    p.box(m["cream"], 0, w, 0, d, 0, 0.07, bevel=0.01)
    p.box(m["cream"], 0, 0.04, 0.0, d, 0.07, h, bevel=0.006)
    p.box(m["cream"], w - 0.04, w, 0.0, d, 0.07, h, bevel=0.006)
    p.box(m["cream"], 0.04, w - 0.04, d - 0.05, d, 0.07, h, bevel=0.006)
    p.box(m["steel"], 0.07, w - 0.07, 0.04, d - 0.06, 0.07, 0.08)                     # table
    p.box(m["pcb"], 0.10, 0.22, 0.08, 0.18, 0.08, 0.0815)                              # FR1 blank on the bed
    p.box(m["copper"], 0.10, 0.22, 0.08, 0.18, 0.0815, 0.082)
    p.box(m["cream"], 0.15, 0.22, d - 0.12, d - 0.05, 0.13, 0.26, bevel=0.006)        # Z carriage
    p.cyl(m["steel"], (0.185, d - 0.10, 0.10), (0.185, d - 0.10, 0.14), 0.004, seg=8)  # end mill
    amber = bpy.data.materials.get("Mach_AmberWindow")
    p.box(amber, 0.04, w - 0.04, -0.005, 0.0, 0.07, h - 0.01)                          # front cover
    p.box(amber, 0.04, w - 0.04, 0.0, d - 0.05, h - 0.01, h)
    return p


def soldering_station(m):
    p = Part()
    p.box(m["blue"], 0, 0.13, 0, 0.16, 0, 0.09, bevel=0.008)                          # base unit
    p.box(m["screen"], 0.02, 0.11, -0.001, 0.0, 0.045, 0.075)
    p.cyl(m["black"], (0.20, 0.08, 0.0), (0.20, 0.08, 0.02), 0.04, seg=24)             # iron holder base
    p.cyl(m["steel"], (0.20, 0.08, 0.02), (0.24, 0.02, 0.12), 0.018, seg=16)           # spiral holder
    p.cyl(m["black"], (0.21, 0.065, 0.045), (0.25, 0.0, 0.15), 0.008, seg=10)          # iron grip
    p.cyl(m["steel"], (0.20, 0.08, 0.025), (0.21, 0.065, 0.045), 0.002, seg=6)         # tip
    p.box(mat("Sponge_Yellow", "#E8C547", 0.9), 0.17, 0.23, 0.12, 0.16, 0.0, 0.012)
    for k in range(6):                                                                 # cable to the station
        a = (0.25 - k * 0.04, 0.0 + 0.02 * k, 0.15 - 0.025 * k)
        b = (0.21 - k * 0.04, 0.02 + 0.02 * k, 0.125 - 0.025 * k)
        p.cyl(m["black"], a, b, 0.0025, seg=6)
    return p


def weller_we1010(m):
    """Weller WE1010 (the lab has a Weller; WE1010 is my stand-in pick): black power unit 120 W x 150 D x 98 H (Weller
    data sheet) with a blue-grey right flank, a back-lit LCD, up/down/menu buttons and the iron socket at the lower
    left; PH 70 safety rest beside it (black base, yellow sponge, steel spiral) with the WEP 70 iron (teal sleeve,
    black foam grip) in it. From the weller-tools.com product photo. Front at local y=0, x = width."""
    p = Part()
    blk = mat("Weller_Black", "#1B1C1E", 0.45)
    flank = mat("Weller_BlueGrey", "#9FB9C4", 0.35)
    teal = mat("Weller_Teal", "#7FC4C9", 0.35)
    lcd = mat("Weller_LCD", "#B8CCD6", 0.2, emit=0.6)
    w, d, h = 0.120, 0.150, 0.098
    p.box(blk, 0.0, w - 0.012, 0.0, d, 0.006, h, bevel=0.008)                          # housing
    p.box(flank, w - 0.012, w, 0.010, d, 0.006, h - 0.004, bevel=0.004)                # blue-grey right flank
    p.box(blk, 0.004, w - 0.004, 0.004, d - 0.004, 0.0, 0.008)                          # foot plinth
    p.box(lcd, 0.018, 0.088, -0.001, 0.0, 0.050, 0.082)                                 # LCD
    for z in (0.074, 0.058):                                                           # up/down buttons
        p.box(m["grey"], 0.094, 0.108, -0.003, 0.0, z - 0.006, z + 0.006, bevel=0.002)
    p.cyl(m["grey"], (0.101, -0.003, 0.038), (0.101, 0.0, 0.038), 0.007, seg=16)        # menu button
    p.box(m["red"], 0.006, 0.016, -0.002, 0.0, 0.026, 0.040)                            # mains rocker
    p.cyl(blk, (0.040, -0.020, 0.026), (0.040, 0.0, 0.026), 0.010, seg=16)              # iron socket + plug
    # PH 70 safety rest to the right: base, sponge, spiral, iron
    bx = w + 0.025
    p.box(blk, bx, bx + 0.10, 0.0, 0.16, 0.0, 0.030, bevel=0.006)
    p.box(mat("Sponge_Yellow", "#E8C547", 0.9), bx + 0.015, bx + 0.085, 0.015, 0.085, 0.030, 0.040)
    p.cyl(blk, (bx + 0.05, 0.125, 0.030), (bx + 0.05, 0.125, 0.055), 0.022, seg=20)
    p.cyl(m["steel"], (bx + 0.05, 0.120, 0.055), (bx + 0.05, 0.075, 0.150), 0.020, seg=18)        # spiral (as a sleeve)
    p.cyl(blk, (bx + 0.05, 0.072, 0.152), (bx + 0.05, 0.064, 0.170), 0.024, seg=18)               # funnel top
    p.cyl(blk, (bx + 0.05, 0.060, 0.175), (bx + 0.05, 0.020, 0.250), 0.014, seg=14)               # foam grip
    p.cyl(teal, (bx + 0.05, 0.020, 0.250), (bx + 0.05, 0.000, 0.290), 0.010, seg=14)              # teal sleeve
    p.cyl(m["steel"], (bx + 0.05, 0.125, 0.040), (bx + 0.05, 0.110, 0.070), 0.0035, seg=8)        # tip in the spiral
    for k in range(5):                                                                 # cable to the socket
        a = (bx + 0.05 - k * 0.03, 0.000 + 0.004 * k, 0.290 - 0.055 * k)
        b = (bx + 0.05 - (k + 1) * 0.03, 0.000 + 0.004 * (k + 1), max(0.020, 0.290 - 0.055 * (k + 1)))
        p.cyl(blk, a, b, 0.0028, seg=6)
    return p


def zd915(m):
    """ZD-915 desoldering station ("AliExpress special", Magnús; ZD-915 is my stand-in pick): beige-grey steel box
    130 W x 225 D x 158 H (retail listing), rounded front bezel with a green LCD and three grey arrow buttons, red power
    button, gun socket and white air knob below; black cradle on the left flank holding the beige pistol-grip
    desoldering gun. From the eleshop.eu product photo. Front at local y=0."""
    p = Part()
    beige = mat("ZD_Beige", "#C9C6BA", 0.45)
    lcd = mat("ZD_LCD", "#8FA88A", 0.25, emit=0.3)
    blk = m["black"]
    w, d, h = 0.130, 0.225, 0.158
    p.box(beige, 0.0, w, 0.008, d, 0.0, h, bevel=0.004)                                 # case
    p.box(beige, 0.006, w - 0.006, 0.0, 0.010, 0.006, h - 0.006, bevel=0.008)           # front bezel
    p.box(lcd, 0.025, 0.095, -0.001, 0.0, 0.098, 0.135)                                 # LCD
    for z in (0.090, 0.072, 0.054):
        p.box(m["grey"], 0.100, 0.118, -0.003, 0.0, z - 0.006, z + 0.006, bevel=0.002)
    p.cyl(m["red"], (0.025, -0.004, 0.022), (0.025, 0.0, 0.022), 0.008, seg=14)         # power
    p.cyl(m["steel"], (0.062, -0.012, 0.022), (0.062, 0.0, 0.022), 0.008, seg=14)       # gun socket
    p.cyl(blk, (0.100, -0.010, 0.022), (0.100, 0.0, 0.022), 0.013, seg=18)              # air knob
    p.cyl(m["lampwhite"], (0.100, -0.011, 0.022), (0.100, -0.010, 0.022), 0.008, seg=16)
    # cradle on the left flank + gun resting in it, nose forward
    p.box(blk, -0.030, 0.0, 0.10, 0.16, 0.10, 0.125, bevel=0.004)
    p.box(beige, -0.075, -0.020, 0.06, 0.19, 0.105, 0.135, bevel=0.010)                 # gun body
    p.box(beige, -0.068, -0.030, 0.15, 0.19, 0.025, 0.110, bevel=0.010)                 # grip
    p.cyl(m["steel"], (-0.048, 0.06, 0.122), (-0.048, -0.02, 0.122), 0.008, seg=12)     # barrel + tip
    p.cyl(m["steel"], (-0.048, -0.02, 0.122), (-0.048, -0.045, 0.118), 0.003, seg=8)
    p.cyl(blk, (-0.049, 0.19, 0.03), (0.06, 0.20, 0.0), 0.004, seg=6)                   # hose/cable
    return p


def fume_extractor(m):
    p = Part()
    p.box(m["black"], 0, 0.20, 0, 0.08, 0, 0.22, bevel=0.01)
    p.box(m["grey"], 0.02, 0.18, -0.001, 0.0, 0.03, 0.19)                              # carbon filter face
    return p


def scope_and_psu(m):
    p = Part()
    p.box(m["grey"], 0, 0.32, 0, 0.13, 0, 0.16, bevel=0.01)                            # oscilloscope
    p.box(m["screen"], 0.02, 0.19, -0.001, 0.0, 0.03, 0.14)
    for i in range(6):
        p.cyl(m["black"], (0.22 + (i % 3) * 0.03, -0.006, 0.05 + (i // 3) * 0.05), (0.22 + (i % 3) * 0.03, 0.0, 0.05 + (i // 3) * 0.05), 0.009, seg=12)
    p.box(m["black"], 0.36, 0.56, 0, 0.25, 0, 0.13, bevel=0.008)                       # bench PSU
    p.box(m["screen"], 0.38, 0.50, -0.001, 0.0, 0.07, 0.11)
    for x, c in ((0.42, m["red"]), (0.46, m["black"]), (0.50, m["red"])):
        p.cyl(c, (x, -0.008, 0.035), (x, 0.0, 0.035), 0.006, seg=10)
    return p


def magnifier_lamp(m):
    p = Part()
    p.box(m["lampwhite"], 0, 0.06, 0, 0.06, 0, 0.03)                                  # clamp
    p.cyl(m["lampwhite"], (0.03, 0.03, 0.03), (0.05, -0.05, 0.42), 0.008, seg=10)
    p.cyl(m["lampwhite"], (0.05, -0.05, 0.42), (0.10, -0.30, 0.38), 0.008, seg=10)
    p.cyl(m["lampwhite"], (0.10, -0.33, 0.37), (0.10, -0.33, 0.40), 0.09, seg=32)      # lens ring
    return p


def toolbox(p, m, c, x, y, z, w=0.45, d=0.25, h=0.22):
    p.box(c, x, x + w, y, y + d, z, z + h, bevel=0.01)
    p.box(m["black"], x + 0.02, x + w - 0.02, y - 0.002, y, z + h * 0.55, z + h * 0.62)
    p.box(m["black"], x + w * 0.3, x + w * 0.7, y + d * 0.4, y + d * 0.6, z + h, z + h + 0.03, bevel=0.005)


# ---------------------------------------------------------------- glass tool wall
def pegboard_mat():
    """Black powder-coated perforated steel: 10 mm holes on a 25 mm grid (world Y/Z, panel faces +x)."""
    m = bpy.data.materials.get("Pegboard_Black")
    if m:
        return m
    m = bpy.data.materials.new("Pegboard_Black")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    out, b, tr, mix = N("ShaderNodeOutputMaterial"), N("ShaderNodeBsdfPrincipled"), N("ShaderNodeBsdfTransparent"), N("ShaderNodeMixShader")
    b.inputs["Base Color"].default_value = (0.02, 0.02, 0.022, 1)
    b.inputs["Roughness"].default_value = 0.45
    geo, sep = N("ShaderNodeNewGeometry"), N("ShaderNodeSeparateXYZ")
    L(geo.outputs["Position"], sep.inputs["Vector"])
    d = None
    for comp in ("Y", "Z"):
        mu = N("ShaderNodeMath"); mu.operation = "MULTIPLY"; mu.inputs[1].default_value = 40.0
        L(sep.outputs[comp], mu.inputs[0])
        fr = N("ShaderNodeMath"); fr.operation = "FRACT"; L(mu.outputs[0], fr.inputs[0])
        sb = N("ShaderNodeMath"); sb.operation = "SUBTRACT"; sb.inputs[1].default_value = 0.5; L(fr.outputs[0], sb.inputs[0])
        sq = N("ShaderNodeMath"); sq.operation = "MULTIPLY"; L(sb.outputs[0], sq.inputs[0]); L(sb.outputs[0], sq.inputs[1])
        if d is None:
            d = sq
        else:
            ad = N("ShaderNodeMath"); L(d.outputs[0], ad.inputs[0]); L(sq.outputs[0], ad.inputs[1]); d = ad
    hole = N("ShaderNodeMath"); hole.operation = "LESS_THAN"; hole.inputs[1].default_value = 0.04   # r = 0.2 of pitch
    L(d.outputs[0], hole.inputs[0])
    L(hole.outputs[0], mix.inputs["Fac"]); L(b.outputs[0], mix.inputs[1]); L(tr.outputs[0], mix.inputs[2])
    L(mix.outputs[0], out.inputs["Surface"])
    m.diffuse_color = (0.02, 0.02, 0.022, 1)
    return m


def glass_toolwall(m, col):
    """Along the NNE glass (x ~20.85, y 24.06-26.46; starts >= 1.0 m past the CNC-room door at y 23.04): profile frame with a work counter (0.90 m),
    under-counter drawer cabinets + toolbox, and above: perforated pegboard with hung tools,
    an open shelf with bins and a small-parts cabinet, a clamp rack, a cable reel - varied, not a
    plain shelf. Faces +x (into the room).
    Lock-down (2026-11-25, my design; Magnús: acrylic doors, electronic locks): the whole upper zone (pegboard + shelf
    block) is a 0.32 m deep cabinet behind four clear acrylic doors (two pairs, an electronic cabinet lock on each
    pair), acrylic ends and a birch top; the under-counter zone (drawer cabinets, tool chest) is closed by four more
    acrylic doors on the counter front. Only the bolted vice, a parts tray and the cable reel stay on the counter."""
    Y0, Y1, XB = 24.06, 26.46, 20.88                                   # XB = back (glass side); door clearance 1.02 m
    L = Y1 - Y0
    D, H, TOP = 0.65, 0.90, 2.25
    peg = pegboard_mat()
    ply = MAT["ply"]
    p = Part()                                                          # build in world coords directly
    def prof(size, axis, x, y, z, length):
        p.profile(size, axis, x, y, z, length)
    # frame: 4 posts front + back to 2.25 m (back posts) / counter height (front posts)
    for y in (Y0, Y0 + L / 2 - 0.02, Y1 - 0.04):
        prof(0.04, "z", XB, y, 0.035, TOP - 0.035)
        prof(0.04, "z", XB + D - 0.04, y, 0.035, H - 0.025 - 0.035)
        lib["foot"](p, XB + 0.02, y + 0.02); lib["foot"](p, XB + D - 0.02, y + 0.02)
        prof(0.04, "x", XB + 0.04, y, H - 0.065, D - 0.08)               # counter bearers
        prof(0.02, "x", XB + 0.04, y + 0.01, 0.16, D - 0.08)
    for x in (XB, XB + D - 0.04):                                        # long rails
        prof(0.04, "y", x, Y0 + 0.04, H - 0.065, L - 0.08)
        prof(0.02, "y", x + 0.01, Y0 + 0.04, 0.14, L - 0.08)
    prof(0.04, "y", XB, Y0 + 0.04, TOP - 0.04, L - 0.08)                 # top rail
    prof(0.02, "y", XB + 0.01, Y0 + 0.04, 1.62, L - 0.08)                # mid rail behind pegboard/shelf split
    p.box(ply, XB - 0.01, XB + D + 0.01, Y0, Y1, H - 0.025, H, bevel=0.002)     # counter top (25 mm birch)
    p.box(ply, XB + 0.04, XB + D - 0.04, Y0 + 0.04, Y1 - 0.80, 0.16, 0.178)     # lower shelf (gap for the tool chest)
    # upper zone (back plane x = XB + 0.04): pegboard left 1.9 m, open shelves right
    PX = XB + 0.045
    p.box(peg, PX, PX + 0.002, Y0 + 0.06, Y0 + 1.95, H + 0.10, 1.60)
    # shelf block right: two shelves 0.30 deep with bins + a parts cabinet
    for z in (1.25, 1.62, 1.98):
        p.box(ply, PX, PX + 0.30, Y0 + 1.98, Y1 - 0.06, z - 0.018, z, bevel=0.0015)
    shelf_bins = Part()
    lib["bin_box"](shelf_bins, MAT["bins"][2], 0.0, 0.0, 0.0, w=0.32, d=0.24, h=0.15)
    shelf_bins.emit("GlassTW_Bin_0", col, Vector((PX + 0.27, Y0 + 2.01, 1.62)), math.pi / 2)
    cab, cw, ch = drawer_cabinet(m, cols=4, rows=6)
    cab.emit("GlassTW_PartsCab", col, Vector((PX + 0.142, Y0 + 2.02, 1.25)), math.pi / 2)
    tbx = Part()
    toolbox(tbx, m, m["red"], 0, 0, 0, w=0.30, d=0.24, h=0.18)
    tbx.emit("GlassTW_Toolbox_top", col, Vector((PX + 0.27, Y1 - 0.38, 1.98)), math.pi / 2)
    # pegboard tools (local frame of the hanging helpers: x along board, -y = out of board -> rotate to face +x)
    hung = Part()
    x = 0.08
    kinds = ["pliers", "screw", "screw", "pliers", "tweez", "screw", "pliers", "screw", "pliers", "screw"]
    for k in kinds:
        g = rng.choice((m["red"], m["blue"], m["yellow"], m["black"]))
        if k == "pliers": pliers(hung, m, x, 1.38, g)
        elif k == "screw": screwdriver(hung, m, x, 1.30, g)
        else: tweezers(hung, m, x, 1.42)
        x += 0.075
    # spanners in a row, a hammer, a saw, a square
    for i in range(6):
        sx = 0.90 + i * 0.05
        hung.box(m["steel"], sx - 0.007, sx + 0.007, -0.008, -0.003, 1.08, 1.08 + 0.10 + i * 0.02, bevel=0.002)
        hung.cyl(m["steel"], (sx, -0.006, 1.08 + 0.10 + i * 0.02), (sx, -0.002, 1.08 + 0.10 + i * 0.02), 0.012 + i * 0.001, seg=12)
    hung.box(m["black"], 1.30, 1.33, -0.02, -0.004, 1.05, 1.36, bevel=0.006)          # hammer handle
    hung.box(m["steel"], 1.27, 1.36, -0.022, -0.004, 1.36, 1.40, bevel=0.004)          # hammer head
    hung.box(m["steel"], 1.42, 1.48, -0.004, -0.002, 1.02, 1.42)                        # try square blade
    hung.box(m["black"], 1.42, 1.62, -0.012, -0.002, 1.40, 1.44, bevel=0.002)           # square stock
    multimeter(hung, m, 1.68, 1.22)
    # second row below the pliers: scissors, utility knives, calipers, coping saw, glue gun, files
    for i, sx in enumerate((0.10, 0.18)):                                              # scissors
        hung.box(m["steel"], sx - 0.004, sx + 0.004, -0.010, -0.006, 1.10, 1.21)
        for dx in (-0.012, 0.012):
            hung.cyl((m["red"], m["blue"])[i], (sx + dx, -0.012, 1.08), (sx + dx, -0.004, 1.08), 0.014, seg=14)
    for i, sx in enumerate((0.27, 0.32)):                                              # utility knives
        hung.box(m["yellow"], sx - 0.012, sx + 0.012, -0.020, -0.004, 1.04, 1.17, bevel=0.004)
        hung.box(m["steel"], sx - 0.004, sx + 0.004, -0.014, -0.010, 1.17, 1.20)
    hung.box(m["steel"], 0.40, 0.41, -0.008, -0.003, 1.03, 1.27)                        # calipers
    hung.box(m["steel"], 0.38, 0.43, -0.009, -0.003, 1.24, 1.27)
    hung.box(m["steel"], 0.38, 0.425, -0.010, -0.003, 1.18, 1.20)
    for a, b in (((0.48, 1.06), (0.48, 1.24)), ((0.48, 1.24), (0.62, 1.24)), ((0.62, 1.24), (0.62, 1.06))):  # coping saw
        hung.cyl(m["steel"], (a[0], -0.008, a[1]), (b[0], -0.008, b[1]), 0.004, seg=8)
    hung.cyl(m["steel"], (0.48, -0.008, 1.07), (0.62, -0.008, 1.07), 0.0008, seg=6)
    hung.cyl(m["black"], (0.48, -0.008, 1.06), (0.48, -0.008, 1.00), 0.012, seg=12)
    hung.box(m["blue"], 0.66, 0.80, -0.035, -0.005, 1.17, 1.22, bevel=0.008)            # glue gun barrel
    hung.box(m["blue"], 0.75, 0.79, -0.030, -0.010, 1.04, 1.18, bevel=0.006)            # grip
    hung.cyl(m["steel"], (0.64, -0.02, 1.195), (0.66, -0.02, 1.195), 0.004, seg=8)
    for i in range(3):                                                                  # files
        fx = 0.84 + i * 0.03
        hung.box(m["steel"], fx - 0.005, fx + 0.005, -0.006, -0.003, 1.00, 1.07)
        hung.box(m["black"], fx - 0.007, fx + 0.007, -0.010, -0.002, 0.93, 1.00, bevel=0.002)
    for i, tz in enumerate((1.50, 1.38, 1.26)):                                        # tape measures, right end
        hung.cyl((m["yellow"], m["black"], m["yellow"])[i], (1.82, -0.042, tz), (1.82, -0.004, tz), 0.035, seg=24)
    for i in range(7):                                                                  # allen key fan
        hung.box(m["black"], 1.74 + i * 0.008, 1.745 + i * 0.008, -0.008, -0.003, 1.02, 1.08 + i * 0.012)
    # clamp rack: rail + 5 F-clamps hanging below the pegboard top edge
    hung.box(m["steel"], 0.10, 0.80, -0.03, 0.0, 1.57, 1.59)
    for i in range(5):
        cx = 0.15 + i * 0.13
        hung.box(m["steel"], cx - 0.006, cx + 0.006, -0.03, -0.018, 1.30, 1.58)        # bar
        hung.box(m["red"], cx - 0.010, cx + 0.06, -0.034, -0.014, 1.52, 1.56, bevel=0.004)   # top jaw
        hung.box(m["red"], cx - 0.010, cx + 0.06, -0.034, -0.014, 1.33, 1.37, bevel=0.004)   # sliding jaw
        hung.cyl(m["black"], (cx + 0.05, -0.024, 1.33), (cx + 0.05, -0.024, 1.25), 0.011, seg=12)  # handle
    # place: local x -> world +y from Y0, local -y -> world +x (out of board)
    hung.emit("GlassTW_Tools", col, Vector((PX + 0.002, Y0 + 0.06, 0.0)), math.pi / 2)
    # under counter: two drawer cabinets on the lower shelf + a rolling tool chest
    for i, yy in enumerate((Y0 + 0.10, Y0 + 0.60)):
        c2, cw2, ch2 = drawer_cabinet(m, cols=6, rows=6)
        c2.emit(f"GlassTW_UnderCab_{i}", col, Vector((XB + 0.20, yy, 0.178)), math.pi / 2)
    chest = Part()
    chest.box(m["red"], 0, 0.55, 0, 0.40, 0.08, 0.62, bevel=0.01)
    for j in range(5):
        z = 0.12 + j * 0.095
        chest.box(m["steel"], 0.04, 0.51, -0.006, 0.0, z + 0.06, z + 0.07)                # drawer pulls
        chest.box(m["black"], 0.0, 0.55, -0.002, 0.0, z, z + 0.004)                      # drawer gaps
    for xx in (0.05, 0.50):
        for yy in (0.05, 0.35):
            chest.cyl(m["black"], (xx - 0.01, yy, 0.04), (xx + 0.01, yy, 0.04), 0.04, seg=16)
    chest.emit("GlassTW_ToolChest", col, Vector((XB + 0.58, Y1 - 0.75, 0.0)), math.pi / 2)
    # on the counter: a vice, a cordless driver case, a parts tray, a cable reel
    on = Part()
    dv = 0.07                                                                          # in front of the cabinet doors
    on.box(m["grey"], XB + 0.35 + dv, XB + 0.55 + dv, Y0 + 2.07, Y0 + 2.22, H, H + 0.06, bevel=0.005)          # vice body
    on.box(m["steel"], XB + 0.53 + dv, XB + 0.56 + dv, Y0 + 2.05, Y0 + 2.24, H + 0.03, H + 0.11, bevel=0.003)
    on.cyl(m["steel"], (XB + 0.56 + dv, Y0 + 2.145, H + 0.05), (XB + 0.68, Y0 + 2.145, H + 0.05), 0.008, seg=10)  # handle past the edge (as before)
    on.box(m["grey"], XB + 0.40, XB + 0.62, Y0 + 0.40, Y0 + 0.62, H, H + 0.03, bevel=0.003)                   # parts tray
    on.cyl(m["yellow"], (XB + 0.50, Y0 + 0.87, H + 0.085), (XB + 0.50, Y0 + 0.97, H + 0.085), 0.085, seg=32)   # cable reel
    on.cyl(m["black"], (XB + 0.50, Y0 + 0.865, H + 0.085), (XB + 0.50, Y0 + 0.975, H + 0.085), 0.035, seg=24)
    on.emit("GlassTW_Counter", col, Vector((0, 0, 0)))
    # a stool at the counter
    craft["stool"](0.68).emit("GlassTW_Stool", col, Vector((XB + D + 0.10, Y0 + 1.6, 0.0)), 0.2)
    # lock-down enclosures
    ld = {}
    exec(open(HERE + "lockdown.py").read(), ld)
    acr = ld["_ld_mats"]()[0]
    FX = PX + 0.32                                                     # upper cabinet door plane
    for y in (Y0 + 0.02, Y0 + L / 2 - 0.01, Y1 - 0.04):
        prof(0.02, "z", FX - 0.02, y, H, TOP - H)                      # front posts (doors close on them)
    prof(0.02, "y", FX - 0.02, Y0 + 0.02, TOP - 0.02, L - 0.04)        # front top rail
    p.box(ply, XB, FX, Y0, Y1, TOP, TOP + 0.018, bevel=0.002)          # cabinet top
    for y in (Y0, Y1 - 0.005):
        p.box(acr, XB + 0.04, FX, y, y + 0.005, H, TOP)                # acrylic ends
    doors = Part()
    ld["door_run"](doors, "+x", FX, Y0 + 0.02, Y1 - 0.02, H + 0.006, TOP - 0.004, leaves=4, lock_z=1.45)
    ux = XB + D                                                        # under-counter door plane (counter front)
    ld["door_run"](doors, "+x", ux, Y0 + 0.02, Y1 - 0.02, 0.05, H - 0.035, leaves=4, lock_z=0.70)
    dobj = doors.emit("GlassTW_Doors", col, Vector((0, 0, 0)))
    for o in [dobj, *dobj.children_recursive]:
        o["layout_skip"] = True                                        # doors don't count in the footprint
    p.emit("GlassToolWall_Frame", col, Vector((0, 0, 0)))


def component_storage(m, col):
    """Electronics component storage on the NNE glass, micro side (y 30.25-34.15): low profile
    counter (1.05 m) of drawer units, carrying stacked drawer cabinets and a reel rack for SMD reels."""
    Y0, Y1, XB = 30.30, 34.10, 20.88
    L, D, H = Y1 - Y0, 0.50, 1.05
    part, slots, Lu = lib["shelf_unit"]([1.20, 1.20, 1.20], D, H, [0.12], power=False)   # frame only; drawers fill it
    loc, rot = lib["placement"](XB + D / 2, Y0 + Lu / 2, Lu, D, "+x")
    part.emit("ComponentStorage", col, loc, rot)
    top = Part()                                                       # solid birch top for the cabinets
    top.box(MAT["ply"], XB - 0.005, XB + D + 0.01, Y0, Y0 + Lu, H, H + 0.025, bevel=0.002)
    top.emit("ComponentStorage_Top", col, Vector((0, 0, 0)))
    # drawers instead of open shelves: each bay filled with birch drawer fronts (4 rows, graded heights)
    blk = mat("Handle_Black", "#151515", 0.4)
    gap = mat("Drawer_Shadow", "#0E0E0E", 0.9)
    dr = Part()
    for bi in range(3):
        xa, xb, _, _, _ = slots[(bi, 0)]
        z0, z1 = 0.10, H - 0.045
        heights = [0.30, 0.25, 0.20, 0.17]
        tot = sum(heights)
        z = z0
        for k, hgt in enumerate(heights):
            hh = (z1 - z0) * hgt / tot
            dr.box(gap, xa, xb, 0.010, D - 0.01, z, z + hh)                                # carcass inside
            dr.box(MAT["ply"], xa + 0.003, xb - 0.003, -0.002, 0.016, z + 0.003, z + hh - 0.003, bevel=0.0015)  # front
            dr.box(blk, (xa + xb) / 2 - 0.08, (xa + xb) / 2 + 0.08, -0.020, -0.002, z + hh - 0.05, z + hh - 0.035, bevel=0.002)  # handle
            dr.box(MAT["label"] if "label" in MAT else mat("Drawer_Label", "#F3F1EA", 0.6),
                   xa + 0.04, xa + 0.14, -0.0025, -0.002, z + hh - 0.06, z + hh - 0.035)  # label card
            z += hh
    dr.emit("ComponentStorage_Drawers", col, loc, rot)
    # On top (Magnús 2026-11-25: "the equipment in cabinets on top of the shelf alongside the window"; layout mine):
    # a full-length (3.76 m) lockable acrylic-door cabinet (6 leaves, 3 e-locks) holding the scope/PSU, hot-air
    # station, spare irons, meters, kits, component drawers, SMD reels, class kit sets and FR1 stock. (The SRM-20s moved
    # to the PCB bench on the bank wall in the overhaul pass.)
    ld = {}
    exec(open(HERE + "lockdown.py").read(), ld)
    acr = ld["_ld_mats"]()[0]
    T = H + 0.025                                                      # counter top
    CX0, CX1, CY0, CY1, CZ1 = XB + 0.01, XB + 0.47, Y0, Y0 + Lu, 2.20             # full counter length
    cabs, cdoor = Part(), Part()
    ply = MAT["ply"]
    cabs.box(ply, CX0, CX1, CY0, CY1, CZ1, CZ1 + 0.018, bevel=0.002)                  # top
    for y in (CY0, CY0 + Lu / 3 - 0.009, CY0 + 2 * Lu / 3 - 0.009, CY1 - 0.018):
        cabs.box(ply, CX0, CX1, y, y + 0.018, T, CZ1)                                 # ends + bay dividers
    cabs.box(ply, CX0, CX0 + 0.012, CY0, CY1, T, CZ1)                                 # back (glass side)
    for z in (T + 0.40, T + 0.78):
        cabs.box(ply, CX0 + 0.012, CX1 - 0.01, CY0 + 0.018, CY1 - 0.018, z, z + 0.018, bevel=0.0015)   # shelves
    z0, z1, z2 = T, T + 0.418, T + 0.798
    scope_and_psu(m).emit("ScopePSU", col, Vector((CX1 - 0.03, CY0 + 0.05, z0)), math.pi / 2)   # front faces +x
    for k in range(2):
        c2, cw2, ch2 = drawer_cabinet(m, cols=6, rows=6)
        c2.emit(f"CompCab_{k}_0", col, Vector((CX0 + 0.04 + 0.142, CY0 + 1.30 + k * (cw2 + 0.03), z0)), math.pi / 2)
    toolbox(cabs, m, m["red"], CX0 + 0.04, CY0 + 0.05, z1, w=0.36, d=0.38, h=0.14)        # hot-air rework station
    toolbox(cabs, m, m["blue"], CX0 + 0.04, CY0 + 0.45, z1, w=0.34, d=0.36, h=0.11)       # spare irons + tips
    toolbox(cabs, m, m["grey"], CX0 + 0.04, CY0 + 0.83, z1, w=0.32, d=0.36, h=0.09)       # solder, wick, flux
    for k in range(4):                                                                   # multimeters
        y = CY0 + 1.32 + k * 0.12
        cabs.box(m["yellow"], CX0 + 0.20, CX0 + 0.245, y, y + 0.09, z1, z1 + 0.18, bevel=0.006)
    toolbox(cabs, m, m["black"], CX0 + 0.04, CY0 + 1.85, z1, w=0.36, d=0.36, h=0.12)      # probes, leads
    kits = [mat("Kit_Teal", "#0E8C8C", 0.5), mat("Kit_Blue", "#1245DE", 0.5), m["red"], mat("Kit_Grey", "#5E6266", 0.5)]
    y = CY0 + 0.05
    while y < CY0 + 2 * Lu / 3 - 0.30:                                                   # kit boxes, top shelf
        w = rng.uniform(0.18, 0.30)
        cabs.box(rng.choice(kits), CX0 + 0.05, CX0 + 0.38, y, y + w, z2, z2 + rng.uniform(0.10, 0.22), bevel=0.004)
        y += w + 0.02
    for j in range(10):                                                                  # SMD reels, top shelf end
        yy = CY0 + 2 * Lu / 3 - 0.26 + j * 0.02
        cabs.cyl(mat("Reel_Blue", "#1E5FA8", 0.3) if j % 3 else mat("Reel_Clear", "#D8DEE2", 0.1),
                 (CX0 + 0.22, yy, z2 + 0.09), (CX0 + 0.22, yy + 0.012, z2 + 0.09), 0.09, seg=32)
    ld["door_run"](cdoor, "+x", CX1, CY0 + 0.005, CY1 - 0.005, T + 0.006, CZ1 - 0.004, leaves=6, lock_z=1.55)
    # third bay: class kit sets (6 identical kit boxes, one per teaching-table seat) + PCB stock
    for k in range(6):
        y = CY0 + 2.56 + (k % 3) * 0.38
        zz = z0 if k < 3 else z1
        cabs.box(kits[1], CX0 + 0.05, CX0 + 0.40, y, y + 0.34, zz, zz + 0.14, bevel=0.005)
        cabs.box(MAT["label"] if "label" in MAT else mat("Drawer_Label", "#F3F1EA", 0.6),
                 CX0 + 0.40, CX0 + 0.401, y + 0.10, y + 0.24, zz + 0.04, zz + 0.10)
    for k in range(8):                                                                   # FR1 blanks, top shelf
        cabs.box(mat("FR1_Copper", "#C27A4A", 0.35, metal=0.6), CX0 + 0.05, CX0 + 0.33, CY1 - 1.0 + k * 0.004,
                 CY1 - 1.0 + k * 0.004 + 0.0016, z2, z2 + 0.16)
    cabs.emit("WindowCabinets", col, Vector((0, 0, 0)))
    dob = cdoor.emit("WindowCabinets_Doors", col, Vector((0, 0, 0)))
    for o in [dob, *dob.children_recursive]:
        o["layout_skip"] = True
    # (C) one bay (the second from the bench, so its doors swing clear of the bench end) behind acrylic doors:
    # locked drawers for meters and soldering spares (lockdown, Magnús 2026-11-25; my placement).
    cd = Part()
    b0, b1 = Y0 + Lu / 3, Y0 + 2 * Lu / 3
    ld["door_run"](cd, "+x", XB + D + 0.024, b0 + 0.02, b1 - 0.02, 0.10, H - 0.03, leaves=2, lock_z=0.75)
    dob = cd.emit("ComponentStorage_Doors", col, Vector((0, 0, 0)))
    for o in [dob, *dob.children_recursive]:
        o["layout_skip"] = True


# ---------------------------------------------------------------- build
def build():
    m = mats()
    scene = bpy.context.scene
    col = bpy.data.collections.get("Microelectronics") or bpy.data.collections.new("Microelectronics")
    if col.name not in scene.collection.children:
        scene.collection.children.link(col)
    for o in list(col.objects):
        data = o.data
        bpy.data.objects.remove(o)
        if isinstance(data, bpy.types.Mesh) and data.users == 0:
            bpy.data.meshes.remove(data)
    # The three colleague tool walls behind the bench are REMOVED (Magnús 2026-11-25: no permanent tool wall, nothing
    # stored there); hidden here, deleted by purge_hidden. The felt panels that hung on their backs are free-standing
    # mobile screens now (build_felt_dividers.py). yf = the walls' old ESE face, kept so the bench stays put.
    for n in ROW:
        o = bpy.data.objects.get(n)
        if o:
            for k in (o, *o.children_recursive):
                k.hide_render = True
                k.hide_set(True)
    yf = 29.953
    rot = math.pi                                                    # local front (-y) faces +y
    # ---- (2026-11-25, Magnús) the tall soldering/SRM-20 bench is GONE: the area is de-crowded into flexible teaching
    # space. Soldering moves to a desk on the bank wall (electronics_commons), the SRM-20s and every portable
    # instrument into locked cabinets on the window counter (component_storage), the teaching table towards the column.
    glass_toolwall(m, col)
    component_storage(m, col)
    electronics_commons(m, col)
    tool_library(m, col)
    print("microelectronics built (no tall bench; soldering desk on the bank wall)")



SPINE_Y0 = 31.55 + 1.22      # spine shrunk by one bay at the column end (Magnús 2026-11-25): way in ~2.2 m


def tool_library(m, col):
    """Tool library on the workshop face of the spine (faces -x, toward electronics). Spine unit: 4 bays x 1.18 m,
    0.30 deep, levels 0.10..2.00. Since 2026-11-25 the workshop-side unit has only the 2 bays facing the room
    (y 31.55-34.03, still called bays 3 and 2 here); the other two faced the bank wall 5 cm away and are gone."""
    lv = [0.10, 0.48, 0.86, 1.24, 1.62, 2.00]
    _, slots4, L4 = lib["shelf_unit"]([1.18] * 4, 0.30, 2.42, lv)      # 2026-11-25: the unit has 2 bays; keep the
    _, slots1, L = lib["shelf_unit"]([1.18] * 1, 0.30, 2.42, lv)       # old bay numbers (names, contents); since the
    slots = {(3, li): slots1[(0, li)] for (bi, li) in slots4 if bi == 3}  # spine shrink (Magnús 2026-11-25) only bay 3
    loc, rot = lib["placement"](27.62 + 0.15, SPINE_Y0 + L / 2, L, 0.30, "-x")
    W = lambda x, y, z: lib["to_world"](loc, rot, (x, y, z))
    p = Part()
    case_red = mat("Case_Red", "#B3201C", 0.45)
    case_blk = mat("Case_Black", "#1C1D1F", 0.5)
    case_grn = mat("Case_Teal", "#1E6E6A", 0.45)

    def case(c, x, z, w=0.40, d=0.27, h=0.16, latch=None):              # systainer-style stackable case
        p.box(c, x, x + w, 0.02, 0.02 + d, z, z + h, bevel=0.008)
        p.box(m["black"], x + 0.01, x + w - 0.01, 0.018, 0.02, z + h - 0.03, z + h - 0.025)
        p.box(latch or m["yellow"], x + w / 2 - 0.03, x + w / 2 + 0.03, 0.012, 0.02, z + h - 0.06, z + h - 0.02, bevel=0.003)
        p.box(m["black"], x + w * 0.3, x + w * 0.7, 0.10, 0.18, z + h, z + h + 0.02, bevel=0.005)    # handle
        p.box(m["label"], x + 0.03, x + 0.13, 0.0185, 0.019, z + 0.03, z + 0.07)
        return z + h

    def labelled_box(x, z, w, h, c):
        p.box(c, x, x + w, 0.02, 0.28, z, z + h, bevel=0.004)
        p.box(m["label"], x + w * 0.25, x + w * 0.75, 0.0185, 0.02, z + h * 0.45, z + h * 0.75)

    for bi in (3,):
        xa, xb, _, _, z0 = slots[(bi, 0)]                               # bottom: toolboxes + case stack
        if bi == 3:
            z = case(case_blk, xa + 0.05, z0)
            case(case_red, xa + 0.05, z, latch=m["black"])
            toolbox(p, m, m["red"], xa + 0.55, 0.03, z0, w=0.50, d=0.24, h=0.24)
        else:
            toolbox(p, m, m["blue"], xa + 0.05, 0.03, z0, w=0.45, d=0.24, h=0.22)
            z = case(case_grn, xa + 0.62, z0)
            case(case_blk, xa + 0.62, z)
        xa, xb, _, _, z1 = slots[(bi, 1)]                               # power tools
        if bi == 3:
            p.box(m["black"], xa + 0.70, xa + 0.90, 0.06, 0.20, z1, z1 + 0.07, bevel=0.008)    # charger
            p.box(m["yellow"], xa + 0.72, xa + 0.88, 0.09, 0.17, z1 + 0.07, z1 + 0.13, bevel=0.006)
            for k in range(2):                                                                 # spare batteries
                p.box(m["black"], xa + 0.95 + k * 0.09, xa + 1.03 + k * 0.09, 0.08, 0.20, z1, z1 + 0.08, bevel=0.006)
                p.box(m["yellow"], xa + 0.95 + k * 0.09, xa + 1.03 + k * 0.09, 0.08, 0.20, z1 + 0.08, z1 + 0.10, bevel=0.004)
        else:
            case(case_blk, xa + 0.05, z1, w=0.42, h=0.13)                                      # jigsaw case
            case(case_red, xa + 0.52, z1, w=0.30, d=0.22, h=0.11, latch=m["black"])           # rotary tool kit
            for k in range(3):                                                                 # glue guns in a ply rack
                gx = xa + 0.90 + k * 0.08
                p.box(m["blue"], gx, gx + 0.03, 0.08, 0.22, z1 + 0.10, z1 + 0.15, bevel=0.006)
                p.box(m["blue"], gx, gx + 0.03, 0.17, 0.21, z1 + 0.02, z1 + 0.11, bevel=0.005)
            p.box(MAT["ply"], xa + 0.88, xa + 1.14, 0.05, 0.25, z1, z1 + 0.02, bevel=0.002)
        xa, xb, _, _, z2 = slots[(bi, 2)]                               # soldering / measuring
        if bi == 3:
            p.box(m["grey"], xa + 0.05, xa + 0.30, 0.04, 0.22, z2, z2 + 0.11, bevel=0.008)    # hot-air rework station
            p.box(m["screen"], xa + 0.07, xa + 0.18, 0.039, 0.04, z2 + 0.05, z2 + 0.09)
            p.cyl(m["black"], (xa + 0.38, 0.12, z2), (xa + 0.38, 0.12, z2 + 0.16), 0.02, seg=16)  # hot-air wand holder
            for k in range(2):                                                                 # helping hands
                hx = xa + 0.52 + k * 0.20
                p.box(m["black"], hx, hx + 0.12, 0.06, 0.18, z2, z2 + 0.02, bevel=0.004)
                for a in (-1, 1):
                    p.cyl(m["steel"], (hx + 0.06, 0.12, z2 + 0.02), (hx + 0.06 + a * 0.05, 0.09, z2 + 0.17), 0.003, seg=6)
                    p.cyl(m["steel"], (hx + 0.06 + a * 0.05, 0.09, z2 + 0.17), (hx + 0.06 + a * 0.06, 0.07, z2 + 0.19), 0.006, seg=8)
            p.cyl(m["steel"], (xa + 0.95, 0.12, z2), (xa + 0.95, 0.12, z2 + 0.20), 0.012, seg=12)  # desoldering pump
            p.cyl(m["blue"], (xa + 0.95, 0.12, z2 + 0.20), (xa + 0.95, 0.12, z2 + 0.24), 0.008, seg=10)
            for k in range(3):                                                                 # solder spools
                p.cyl(m["solder"], (xa + 1.03, 0.08 + k * 0.06, z2 + 0.03), (xa + 1.10, 0.08 + k * 0.06, z2 + 0.03), 0.03, seg=20)
        else:
            sp_ = scope_and_psu(m)
            sp_.emit("ToolLib_ScopePSU", col, W(xa + 0.05, 0.03, z2), rot)
            for k in range(3):                                                                 # multimeters on stands
                mx = xa + 0.68 + k * 0.15
                p.box(m["yellow"], mx, mx + 0.09, 0.10, 0.14, z2, z2 + 0.18, bevel=0.01)
                p.box(m["screen"], mx + 0.015, mx + 0.075, 0.099, 0.10, z2 + 0.12, z2 + 0.165)
                p.cyl(m["black"], (mx + 0.045, 0.098, z2 + 0.075), (mx + 0.045, 0.10, z2 + 0.075), 0.024, seg=24)
                p.box(m["black"], mx + 0.02, mx + 0.07, 0.14, 0.20, z2, z2 + 0.012)              # kickstand foot
        xa, xb, _, _, z3 = slots[(bi, 3)]                               # eye level: small-parts drawer cabinets
        for k in range(2):
            cab, cw, ch = drawer_cabinet(m, cols=6, rows=6)
            cab.emit(f"ToolLib_Cab_{bi}_{k}", col, W(xa + 0.08 + k * 0.54, 0.05, z3), rot)
        xa, xb, _, _, z4 = slots[(bi, 4)]                               # hand tools standing in ply blocks
        if bi == 3:
            p.box(MAT["ply"], xa + 0.05, xa + 0.45, 0.08, 0.20, z4, z4 + 0.05, bevel=0.003)   # screwdriver block
            for k in range(9):
                sx = xa + 0.08 + k * 0.042
                g = (m["red"], m["blue"], m["yellow"], m["black"])[k % 4]
                p.cyl(m["steel"], (sx, 0.14, z4 + 0.05), (sx, 0.14, z4 + 0.13), 0.0025, seg=8)
                p.cyl(g, (sx, 0.14, z4 + 0.13), (sx, 0.14, z4 + 0.23), 0.012, seg=12)
            p.box(MAT["ply"], xa + 0.55, xa + 1.05, 0.08, 0.20, z4, z4 + 0.04, bevel=0.003)   # plier block
            for k in range(6):
                px = xa + 0.60 + k * 0.075
                g = (m["red"], m["blue"], m["black"])[k % 3]
                p.box(m["steel"], px - 0.008, px + 0.008, 0.13, 0.15, z4 + 0.17, z4 + 0.22, bevel=0.002)
                for dx in (-0.012, 0.012):
                    p.box(g, px + dx - 0.006, px + dx + 0.006, 0.13, 0.15, z4 + 0.04, z4 + 0.17, bevel=0.004)
        else:
            p.box(m["grey"], xa + 0.05, xa + 0.55, 0.04, 0.26, z4, z4 + 0.04, bevel=0.004)    # tray: tweezers, calipers
            for k in range(5):
                tx = xa + 0.10 + k * 0.025
                p.box(m["steel"], tx, tx + 0.006, 0.07, 0.20, z4 + 0.04, z4 + 0.046)
            p.box(m["steel"], xa + 0.30, xa + 0.50, 0.10, 0.12, z4 + 0.04, z4 + 0.048)
            p.box(m["steel"], xa + 0.30, xa + 0.32, 0.07, 0.15, z4 + 0.04, z4 + 0.048)
            for k in range(8):                                                                 # hex key fan in a holder
                p.box(m["black"], xa + 0.65 + k * 0.012, xa + 0.655 + k * 0.012, 0.13, 0.135, z4 + 0.03, z4 + 0.08 + k * 0.012)
            p.box(m["red"], xa + 0.63, xa + 0.77, 0.12, 0.15, z4, z4 + 0.04, bevel=0.004)
            case(case_grn, xa + 0.85, z4, w=0.28, d=0.22, h=0.10)                              # crimp kit
        xa, xb, _, _, z5 = slots[(bi, 5)]                               # top: labelled kit boxes
        for k in range(3):
            labelled_box(xa + 0.04 + k * 0.38, z5, 0.34, 0.22, (MAT["bins"][(bi + k) % 6] if k == 1 else m["grey"]))
    p.emit("ToolLibrary", col, loc, rot)


def whiteboard_schematic(b, ink, yf, col):
    """555 LED blinker drawn in marker on the whiteboard (x 23.95-25.55, z 1.1-2.1), plus handwritten-ish text."""
    def stroke(c, p0, p1, w=0.0035):
        (x0, z0), (x1, z1) = p0, p1
        L = math.hypot(x1 - x0, z1 - z0)
        mtx = Matrix.Translation(((x0 + x1) / 2, yf - 0.0002, (z0 + z1) / 2)) @ Matrix.Rotation(-math.atan2(z1 - z0, x1 - x0), 4, "Y") \
            @ Matrix.Diagonal((L + w, 0.0004, w, 1))
        bmesh.ops.create_cube(b.bm(c), size=1.0, matrix=mtx)

    def poly(c, pts):
        for p0, p1 in zip(pts, pts[1:]):
            stroke(c, p0, p1)

    def zigzag(c, p0, p1, n=6, amp=0.012):
        (x0, z0), (x1, z1) = p0, p1
        dx, dz = (x1 - x0), (z1 - z0)
        L = math.hypot(dx, dz)
        nx, nz = -dz / L, dx / L
        pts = [p0]
        for k in range(1, n):
            t = k / n
            sgn = 1 if k % 2 else -1
            pts.append((x0 + dx * t + nx * amp * sgn, z0 + dz * t + nz * amp * sgn))
        pts.append(p1)
        poly(c, pts)

    blk, blue, red = ink[0], ink[1], ink[2]
    poly(blk, [(24.10, 1.86), (25.35, 1.86)])                                     # VCC rail
    poly(blk, [(24.10, 1.30), (25.35, 1.30)])                                     # GND rail
    poly(blk, [(24.62, 1.42), (24.88, 1.42), (24.88, 1.76), (24.62, 1.76), (24.62, 1.42)])   # 555
    poly(blk, [(24.75, 1.76), (24.75, 1.86)])                                     # pin 8 VCC
    poly(blk, [(24.75, 1.42), (24.75, 1.30)])                                     # pin 1 GND
    poly(blk, [(24.30, 1.86), (24.30, 1.80)]); zigzag(blk, (24.30, 1.80), (24.30, 1.70))   # R1
    poly(blk, [(24.30, 1.70), (24.62, 1.70)])                                     # -> pin 7
    zigzag(blk, (24.30, 1.70), (24.30, 1.58)); poly(blk, [(24.30, 1.58), (24.30, 1.50)])  # R2
    poly(blk, [(24.30, 1.54), (24.62, 1.54)])                                     # -> pins 2/6
    poly(blk, [(24.27, 1.50), (24.33, 1.50)]); poly(blk, [(24.27, 1.48), (24.33, 1.48)])  # C
    poly(blk, [(24.30, 1.48), (24.30, 1.30)])
    poly(blk, [(24.88, 1.62), (24.98, 1.62)]); zigzag(red, (24.98, 1.62), (25.12, 1.62))  # pin 3 -> R3
    poly(red, [(25.12, 1.62), (25.20, 1.62), (25.20, 1.52)])
    poly(red, [(25.16, 1.52), (25.24, 1.52), (25.20, 1.45), (25.16, 1.52)])       # LED
    poly(red, [(25.16, 1.45), (25.24, 1.45)]); poly(red, [(25.20, 1.45), (25.20, 1.30)])
    poly(red, [(25.26, 1.50), (25.30, 1.54)]); poly(red, [(25.27, 1.47), (25.31, 1.51)])  # light arrows
    for t, (x, z), size, c in (("555 blinker", (24.06, 1.98), 0.075, blk), ("NE555", (24.66, 1.57), 0.035, blk),
                               ("f = 1.44 / ((R1 + 2 R2) C)", (24.06, 1.14), 0.040, blue),
                               ("Soldering 101 - tue 18:00", (24.98, 2.03), 0.030, blue), ("R1", (24.18, 1.75), 0.028, blk),
                               ("R2", (24.18, 1.62), 0.028, blk), ("10uF", (24.36, 1.46), 0.025, blk), ("330", (25.02, 1.65), 0.025, red)):
        cu = bpy.data.curves.new("WB_Text", "FONT")
        cu.body, cu.size = t, size
        cu.materials.append(c)
        ob = bpy.data.objects.new("WB_Text", cu)
        col.objects.link(ob)
        ob.location = (x, yf - 0.0003, z)
        ob.rotation_euler = (math.pi / 2, 0, 0)


def electronics_commons(m, col):
    """Open floor between the micro bench and the bank wall (x 21.6-27.4, y 31.5-35.1):
    - on the bank wall (faces -y at y 34.32): a profile-framed board run: pin-up board with
      schematics and project sheets, a whiteboard with circuit sketches, a pegboard with coiled
      cables / jumper wires, and a shelf of kit boxes above;
    - an electronics teaching table (two 1.6 x 0.8 tables pushed together) with 6 chairs,
      laptops, breadboards, Arduino kit boxes and a USB hub."""
    _t = open(HERE + "build_textile.py").read()
    tex = {}
    exec(_t[:_t.index("\ndef build():")], tex)
    YW = 34.315                                                        # wall face (moved bank wall)
    cork = mat("Cork", "#B98D5E", 0.85)
    paper = mat("Paper", "#F4F2EC", 0.8)
    wb = mat("Whiteboard", "#F7F7F5", 0.15, coat=0.6)
    ink = [mat("Marker_Blue", "#1A3FB0", 0.4), mat("Marker_Black", "#151515", 0.4), mat("Marker_Red", "#C0262D", 0.4)]
    peg = bpy.data.materials.get("Pegboard_Black") or pegboard_mat()
    # ---- Bank wall (Magnús 2026-11-25): ONE continuous counter along the wall with the soldering place, open work
    # surface and the two SRM-20s (open, no hood); a big whiteboard in the middle between two wall cabinets; storage
    # under the counter and in the wall cabinets, all built in-house (40x40 profile + birch ply, laser-cut acrylic doors,
    # standard e-lock). One fully equipped soldering place: the Weller (reference model) + the desoldering station +
    # fume extractor (a cheap bought item, Magnús), ESD mat, tip cleaner, solder reel, helping hands, tool tray. No
    # magnifier, no task lamps (the ceiling LED arrays light the area). Stretch lengths and heights are my choice.
    ld = {}
    exec(open(HERE + "lockdown.py").read(), ld)
    ply = MAT["ply"]
    gapm = mat("Drawer_Shadow", "#0E0E0E", 0.9)
    CX0, CX1, CD, CH = 21.42, 27.50, 0.65, 0.75          # counter (window cabinet ends at x 21.39; wall ends x 27.57)
    cy1 = YW - 0.005
    cy0 = cy1 - CD
    S1, S2 = 23.02, 25.60                                # soldering | open work surface | SRM-20s
    legs = [0.0, S1 - CX0 - 0.02, S2 - CX0 - 0.02, CX1 - CX0 - 0.04]
    c, _ = lib["table_unit"](CX1 - CX0, CD, CH, legs, lower=())
    cloc, crot = lib["placement"]((CX0 + CX1) / 2, (cy0 + cy1) / 2, CX1 - CX0, CD, "-y")
    c.emit("ElecCounter", col, cloc, crot)
    # under-counter units (carcass between the legs; knee space left at the soldering chair and the PC chair)
    UZ0, UZ1 = 0.10, CH - 0.025 - 0.045                  # below the apron
    yf = cy0 + 0.03                                      # door plane, set back behind the top's front edge
    units = [(22.44, S1 - 0.02, 1), (S1 + 0.02, S2 - 0.02, 4), (S2 + 0.02, 26.66, 2)]   # (x0, x1, door leaves)
    un, ud = Part(), Part()
    for ux0, ux1, nl in units:
        un.box(ply, ux0, ux1, yf + 0.005, cy1 - 0.02, UZ0 - 0.018, UZ0, bevel=0.0015)        # bottom
        un.box(ply, ux0, ux1, cy1 - 0.032, cy1 - 0.02, UZ0, UZ1)                           # back
        for x in (ux0, ux1 - 0.018):
            un.box(ply, x, x + 0.018, yf + 0.005, cy1 - 0.02, UZ0, UZ1)                    # sides
        un.box(ply, ux0 + 0.018, ux1 - 0.018, yf + 0.02, cy1 - 0.032, (UZ0 + UZ1) / 2, (UZ0 + UZ1) / 2 + 0.018)  # shelf
        un.box(gapm, ux0 + 0.018, ux1 - 0.018, cy1 - 0.0325, cy1 - 0.032, UZ0, UZ1)
        ld["door_run"](ud, "-y", yf, ux0 + 0.003, ux1 - 0.003, UZ0 - 0.015, UZ1, leaves=nl, lock_z=UZ1 - 0.08)
    # contents seen through the acrylic: grey bins, kit boxes, an end-mill drawer cabinet under the SRM-20s
    bins = [mat("Bin_Grey", "#6B6F73", 0.6), mat("Kit_Blue", "#1245DE", 0.5), mat("Kit_Teal", "#0E8C8C", 0.5)]
    zs = (UZ0, (UZ0 + UZ1) / 2 + 0.018)
    for ux0, ux1, nl in units[:2]:
        for zz in zs:
            x = ux0 + 0.03
            while x < ux1 - 0.30:
                wdt = rng.uniform(0.22, 0.34)
                un.box(rng.choice(bins), x, x + wdt, yf + 0.06, cy1 - 0.06, zz, zz + rng.uniform(0.12, 0.22), bevel=0.004)
                x += wdt + 0.03
    ec, ecw, ech = drawer_cabinet(m, cols=4, rows=4)
    ec.emit("EndMill_Drawers", col, Vector((S2 + 0.06, yf + 0.05, zs[1])), 0.0)
    un.emit("ElecCounter_Units", col, Vector((0, 0, 0)))
    dob = ud.emit("ElecCounter_Doors", col, Vector((0, 0, 0)))
    for o in [dob, *dob.children_recursive]:
        o["layout_skip"] = True
    # soldering place (window end): Weller, desoldering station, fume extractor on the ESD mat; kit around it
    esd = mat("ESD_Mat_Grey", "#5C6E78", 0.85)
    brass = mat("Brass_Wool", "#B8913A", 0.5, metal=0.8)
    solder = mat("Solder_Wire", "#BFC3C6", 0.3, metal=0.9)
    k = Part()
    k.box(esd, 21.56, 22.86, cy1 - 0.58, cy1 - 0.04, CH, CH + 0.003)                        # ESD mat
    k.box(m["black"], 22.30, 22.33, cy1 - 0.06, cy1 - 0.04, CH + 0.003, CH + 0.04)          # earth stud + lead
    T = CH + 0.003
    k.cyl(m["black"], (22.08, cy1 - 0.42, T), (22.08, cy1 - 0.42, T + 0.035), 0.040, seg=24)   # tip cleaner cup
    k.cyl(brass, (22.08, cy1 - 0.42, T + 0.035), (22.08, cy1 - 0.42, T + 0.05), 0.033, seg=24)
    k.box(m["black"], 22.18, 22.30, cy1 - 0.47, cy1 - 0.37, T, T + 0.02)                    # solder reel stand
    k.box(m["black"], 22.235, 22.245, cy1 - 0.42, cy1 - 0.41, T + 0.02, T + 0.08)
    k.cyl(solder, (22.21, cy1 - 0.415, T + 0.08), (22.27, cy1 - 0.415, T + 0.08), 0.035, seg=24)
    k.box(m["black"], 22.42, 22.54, cy1 - 0.50, cy1 - 0.40, T, T + 0.015)                   # helping hands base
    for dx, dz in ((-0.05, 0.16), (0.06, 0.13)):
        k.cyl(m["black"], (22.48, cy1 - 0.45, T + 0.015), (22.48 + dx, cy1 - 0.47, T + dz), 0.005, seg=8)
        k.box(solder, 22.48 + dx - 0.01, 22.48 + dx + 0.01, cy1 - 0.48, cy1 - 0.46, T + dz - 0.01, T + dz + 0.005)
    k.box(m["grey"], 22.60, 22.84, cy1 - 0.52, cy1 - 0.36, T, T + 0.03, bevel=0.003)        # tool tray
    for n in range(4):                                                                       # tweezers, cutters, pliers
        x = 22.63 + n * 0.05
        k.box(m["red"] if n % 2 else m["black"], x, x + 0.018, cy1 - 0.50, cy1 - 0.38, T + 0.03, T + 0.04)
    k.emit("Solder_Kit", col, Vector((0, 0, 0)))
    weller_we1010(m).emit("Solder_Weller", col, Vector((21.62, cy1 - 0.20, T)), 0.0)
    zd915(m).emit("Desolder_ZD915", col, Vector((22.56, cy1 - 0.24, T)), 0.0)
    fume_extractor(m).emit("Fume_0", col, Vector((21.86, cy1 - 0.14, T)), 0.0)
    rr = math.pi + rng.uniform(-0.12, 0.12)
    tex["chair"]().emit("Solder_Chair_1", col, Vector((22.02, cy0 - 0.30, 0))
                        + Matrix.Rotation(rr, 4, "Z") @ Vector((-0.22, -0.22, 0)), rr)
    # SRM-20s (column end), open on the counter between anchor cleats; milling PC at the end with knee space
    pk = Part()
    for n, sx in enumerate((S2 + 0.08, S2 + 0.60)):
        mach["srm20"]().emit(f"Roland_SRM20_{n + 1}", col, Vector((sx, cy1 - 0.05 - 0.426, CH)), 0.0)
        for ux, sg in ((sx, -1), (sx + 0.451, 1)):
            for yy in (cy1 - 0.42, cy1 - 0.14):
                pk.box(MAT["profile"], min(ux, ux + sg * 0.04), max(ux, ux + sg * 0.04), yy, yy + 0.04, CH, CH + 0.003)
                pk.box(MAT["profile"], min(ux, ux + sg * 0.003), max(ux, ux + sg * 0.003), yy, yy + 0.04, CH, CH + 0.04)
    mx = 27.14
    pk.box(m["black"], mx - 0.08, mx + 0.08, cy1 - 0.20, cy1 - 0.08, CH, CH + 0.01)          # monitor foot + stem
    pk.box(m["black"], mx - 0.015, mx + 0.015, cy1 - 0.15, cy1 - 0.12, CH, CH + 0.12)
    pk.box(m["black"], mx - 0.27, mx + 0.27, cy1 - 0.17, cy1 - 0.14, CH + 0.10, CH + 0.42, bevel=0.004)
    pk.box(m["screen"], mx - 0.26, mx + 0.26, cy1 - 0.1705, cy1 - 0.170, CH + 0.11, CH + 0.41)
    pk.box(m["black"], mx - 0.22, mx + 0.22, cy0 + 0.08, cy0 + 0.22, CH, CH + 0.015, bevel=0.003)   # keyboard
    pk.box(m["black"], 27.30, 27.45, cy1 - 0.20, cy1 - 0.05, CH - 0.10, CH - 0.03)           # mini PC under the top
    pk.emit("SRM_Station", col, Vector((0, 0, 0)))
    rr = math.pi + rng.uniform(-0.12, 0.12)
    tex["chair"]().emit("PCB_Chair", col, Vector((mx, cy0 - 0.30, 0))
                        + Matrix.Rotation(rr, 4, "Z") @ Vector((-0.22, -0.22, 0)), rr)
    # wall cabinets above the soldering place and the SRM-20s; whiteboard between them
    WZ0, WZ1, WD = 1.45, 2.25, 0.35
    wc, wdr = Part(), Part()
    for ax0, ax1 in ((CX0 + 0.02, S1 - 0.04), (S2 + 0.04, CX1 - 0.02)):
        wc.box(ply, ax0, ax1, YW - WD, YW - 0.005, WZ0, WZ0 + 0.018, bevel=0.0015)
        wc.box(ply, ax0, ax1, YW - WD, YW - 0.005, WZ1 - 0.018, WZ1, bevel=0.0015)
        wc.box(ply, ax0, ax1, YW - 0.017, YW - 0.005, WZ0, WZ1)
        for x in (ax0, (ax0 + ax1) / 2 - 0.009, ax1 - 0.018):
            wc.box(ply, x, x + 0.018, YW - WD, YW - 0.005, WZ0, WZ1)
        zm = (WZ0 + WZ1) / 2
        wc.box(ply, ax0 + 0.018, ax1 - 0.018, YW - WD + 0.01, YW - 0.017, zm, zm + 0.018, bevel=0.0015)
        ld["door_run"](wdr, "-y", YW - WD, ax0 + 0.003, ax1 - 0.003, WZ0 + 0.003, WZ1 - 0.003, leaves=2, lock_z=WZ0 + 0.12)
        for zz in (WZ0 + 0.018, zm + 0.018):                                                 # boxes inside
            x = ax0 + 0.04
            while x < ax1 - 0.28:
                wdt = rng.uniform(0.20, 0.32)
                wc.box(rng.choice(bins), x, x + wdt, YW - WD + 0.04, YW - 0.04, zz, zz + rng.uniform(0.12, 0.28), bevel=0.004)
                x += wdt + 0.03
    wc.emit("Elec_WallCabinets", col, Vector((0, 0, 0)))
    dob = wdr.emit("Elec_WallCabinets_Doors", col, Vector((0, 0, 0)))
    for o in [dob, *dob.children_recursive]:
        o["layout_skip"] = True
    # whiteboard: standard 2400 x 1200, aluminium frame, marker tray (bought)
    alu = mat("Alu_Frame", "#C9CCCF", 0.35, metal=0.9)
    w = Part()
    WX0, WX1, BZ0, BZ1 = 23.11, 25.51, 1.00, 2.20
    w.box(alu, WX0, WX1, YW - 0.022, YW - 0.004, BZ0, BZ1, bevel=0.004)
    w.box(wb, WX0 + 0.02, WX1 - 0.02, YW - 0.0225, YW - 0.022, BZ0 + 0.02, BZ1 - 0.02)
    w.box(alu, WX0 + 0.3, WX1 - 0.3, YW - 0.08, YW - 0.004, BZ0 - 0.02, BZ0)                # marker tray
    for n, cc in enumerate(ink):
        w.cyl(cc, (WX0 + 0.5 + n * 0.08, YW - 0.05, BZ0 + 0.008), (WX0 + 0.57 + n * 0.08, YW - 0.05, BZ0 + 0.008), 0.008, seg=10)
    for n in range(12):                                                                       # sketch strokes
        z = 2.05 - n * 0.075
        x0 = WX0 + 0.15 + (n % 3) * 0.75
        w.box(ink[n % 3], x0, x0 + rng.uniform(0.25, 0.6), YW - 0.0228, YW - 0.0225, z, z + 0.006)
    w.emit("Elec_Whiteboard", col, Vector((0, 0, 0)))

    # teaching table with 6 chairs, moved towards the column (Magnús 2026-11-25); props cleared (lock-down)
    TL, TD, TH = 3.20, 1.20, 0.75
    tc = Vector((24.55, 31.15))
    t, _ = lib["table_unit"](TL, TD, TH, [0.0, TL / 2 - 0.02, TL - 0.04], lower=())
    loc, rot = lib["placement"](tc.x, tc.y, TL, TD, "-y")
    t.emit("Electronics_Table", col, loc, rot)
    for side, ry in ((-1, math.pi), (1, 0.0)):
        for dx in (-1.05, 0.0, 1.05):
            cx = tc.x + dx + rng.uniform(-0.05, 0.05)
            cy = tc.y + side * (TD / 2 + rng.uniform(0.10, 0.28))
            r = ry + rng.uniform(-0.15, 0.15)
            off = Matrix.Rotation(r, 4, "Z") @ Vector((-0.22, -0.22, 0))
            tex["chair"]().emit(f"Elec_Chair_{side}_{int(dx * 10)}", col, Vector((cx, cy, 0)) + off, r)


build()

# Placements come from layout/layout.yaml (layout/README.md): built at this builder's coordinates, then moved there.
_lay = {}
exec(open(bpy.path.abspath("//scripts/layout_blender.py")).read(), _lay)
_lay["apply"]()
