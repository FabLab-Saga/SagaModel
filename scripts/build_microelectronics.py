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
    # colleague's hammers/saws off every tool wall in the row
    for n in ROW:
        for c in bpy.data.objects[n].children:
            if c.name.split(".")[0] in ("Hammer", "Component_1212695"):
                for k in (c, *c.children_recursive):
                    k.hide_render = k.hide_viewport = True
    # ESE face of the boards (ray from the open side)
    dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, *_ = scene.ray_cast(dg, Vector((24.1, 31.0, 1.4)), Vector((0, -1, 0)))
    yf = loc.y + 0.001
    print("tool-wall ESE face at y %.3f" % yf)
    rot = math.pi                                                    # local front (-y) faces +y
    for wi, (wx0, wx1) in enumerate(((21.05, 23.05), (23.11, 25.11), (25.17, 27.17))):
        wall = Part()
        # two drawer cabinets left, tool rail + wire rod + multimeter right (mirrored per wall for variety)
        for k in range(2):                                           # cabinets stand off the board (body local y 0..0.14)
            c2, cw2, ch2 = drawer_cabinet(m)
            c2.emit(f"DrawerCab_{wi}_{k}", col, Vector((wx0 + 0.12 + (k + 1) * (cw2 + 0.04), yf + 0.14, 1.00)), rot)
        rx = wx0 + 1.15                                              # rail zone (local x measured in world, mirrored by rot)
        tools = Part()
        tools.box(m["steel"], 0.0, 0.75, -0.02, 0.0, 1.55, 1.57)
        x = 0.05
        for t in range(9):
            kind = t % 4
            if kind == 0:
                pliers(tools, m, x, 1.48, rng.choice((m["red"], m["blue"])))
            elif kind == 1:
                screwdriver(tools, m, x, 1.40, rng.choice((m["red"], m["yellow"], m["blue"])))
            elif kind == 2:
                tweezers(tools, m, x, 1.53)
            else:
                pliers(tools, m, x, 1.48, m["black"])
            x += 0.08
        wire_rod(tools, m, 0.05, 1.86)
        multimeter(tools, m, 0.55, 1.12)
        tools.emit(f"ToolRail_{wi}", col, Vector((rx + 0.75, yf, 0.0)), rot)
    # ---- workbench in front of the row
    L, D, H = X1 - 21.75, 0.75, 0.90
    legs = [0.0, L / 3, 2 * L / 3, L - 0.04]
    bench, _ = lib["table_unit"](L, D, H, legs, lower=(0.16,))
    bloc, brot = lib["placement"](21.75 + L / 2, yf + 0.25 + D / 2, L, D, "-y")
    bench.emit("MicroBench", col, bloc, brot)
    top = H

    def on_bench(part, name, wx, wy, w, d, facing=math.pi):
        part.emit(name, col, Vector((wx + w, wy + d, top)), facing)
    by = yf + 0.25                                                   # bench back edge (against the tool wall)
    on_bench(mdx20(m), "Roland_MDX20", 22.05, by + 0.05, 0.362, 0.300)
    for i, sx in enumerate((23.2, 24.6, 26.0)):
        on_bench(soldering_station(m), f"Solder_{i}", sx, by + 0.12, 0.25, 0.16)
        on_bench(fume_extractor(m), f"Fume_{i}", sx + 0.30, by + 0.05, 0.20, 0.08)
    on_bench(scope_and_psu(m), "ScopePSU", 26.45, by + 0.04, 0.56, 0.25)
    on_bench(magnifier_lamp(m), "Magnifier", 24.15, by + 0.02, 0.06, 0.06)
    pc = Part()                                                      # PCBs + parts tray + solder spool on the bench
    for i in range(5):
        x, y = 22.6 + i * 0.9 + rng.uniform(-0.1, 0.1), by + 0.42 + rng.uniform(-0.05, 0.08)
        pc.box(m["pcb"], x, x + rng.uniform(0.06, 0.12), y, y + rng.uniform(0.04, 0.09), top, top + 0.0016)
    pc.box(m["grey"], 25.3, 25.55, by + 0.30, by + 0.45, top, top + 0.02, bevel=0.003)
    pc.cyl(m["solder"], (24.9, by + 0.35, top + 0.025), (24.9, by + 0.38, top + 0.025), 0.025, seg=24)
    pc.emit("BenchStuff", col, Vector((0, 0, 0)))
    for i, sx in enumerate((22.3, 23.4, 24.8, 26.2)):                 # stools on the open side
        craft["stool"](0.68).emit(f"MicroStool_{i}", col, Vector((sx, by + D + 0.12, 0.0)), rng.uniform(-0.2, 0.2))

    # ---- low tool shelving along the NNE glass in the work-table area
    lv = [0.10, 0.48, 0.86]
    part, slots, Ls = lib["shelf_unit"]([1.00, 1.00, 1.00], 0.45, 1.05, lv)
    sloc, srot = lib["placement"](20.95 + 0.225, 23.25 + Ls / 2, Ls, 0.45, "+x")
    part.emit("GlassShelving_NNE", col, sloc, srot)
    stuff = Part()
    for (bi, li), (xa, xb, _, _, zt) in slots.items():
        x = xa + 0.03
        while x < xb - 0.30:
            r = rng.random()
            if r < 0.4:
                c = rng.choice((m["red"], m["yellow"], m["blue"], m["black"]))
                w = rng.uniform(0.35, 0.45)
                toolbox(stuff, m, c, x, 0.06, zt, w=w, d=0.30, h=rng.uniform(0.12, 0.25))
                x += w + 0.04
            else:
                lib["bin_box"](stuff, rng.choice(MAT["bins"]), x, 0.06, zt, w=0.30, d=0.32, h=0.18)
                x += 0.34
    stuff.emit("GlassShelving_Contents", col, sloc, srot)
    print("microelectronics built; bench length %.2f m" % L)


build()
