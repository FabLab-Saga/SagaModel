"""CNC (ShopBot) room: walls, doors and fit-out. Re-runnable ("CNCRoom" collection + boolean cutters on ROOT.geo0).
Run after build_machines, build_material_storage and build_staff_area. Model frame: +X = SSW, +Y = ESE.

Facts (user, 2026-10-08):
- The CNC room's wall to the main room is FLUSH WITH THE MURAL WALL (y 21.66-21.82) and is a VERY TALL GLASS WALL WITH
  A TALL GLASS DOOR (frameless, floor to slab, no aluminium frames; standard office glass door 1.0 x 2.70 m with
  brushed aluminium glass-to-glass hinges, by the NNE glass).
  The colleague's front wall at y 23.05-23.14 (glass door + window) and the side wall's window (x 24.15-24.26,
  y 21.96-22.89) are removed (Cut_CNC_Front / Cut_CNC_Side + their window/door objects deleted); the strip
  x 20.8-24.2, y 21.82-23.14 becomes main lab.
- The colleague's 1.08 x 2.49 m hallway door was made up: replaced by a normal Icelandic interior door (90 cm leaf,
  2.1 m) in a frame, and the wall completed normally round it (infill + wall up to the slab). The knocked-down WC's
  old hallway doorway right next to it is walled up too, so the CNC room has one normal door to the hallway.
Layout (my choices): the ShopBot keeps its orientation along the interior wall (the room is 3.34 m wide, the
machine 2.15 x 4.30), moved back to y 17.15-21.45 so it clears the new front wall; glass door by
the glass, opening onto the 1.1 m glass-side aisle; sheet cart at the bed's WNW (loading) end; collector stays in
the far glass corner; operator corner in the ex-WC bay: ShopBot PC station (standing desk, control box under it) on
the WC partition + tool bench with drawers and a pegboard (bits, collets, wrenches, hearing/eye protection) on the
hallway wall; shop vac by the collector, extinguisher on the WNW wall.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = bpy.path.abspath("//scripts/")
_s = open(HERE + "build_staff_area.py").read()
sa = {}
exec(_s[:_s.index("\ndef build():")], sa)                          # Part, door_in_wall, mats, helpers
Part, mat, MAT, lib = sa["Part"], sa["mat"], sa["MAT"], sa["lib"]
SOFFIT = sa["SOFFIT"]

FRONT_Y = (21.66, 21.82)                       # new front wall = mural-wall line
GLASS_X, INNER_X = 20.805, 24.146              # NNE glass, interior wall (WC partition side)
HALL_WALL = (25.743, 25.911)                   # CNC/hallway wall
SB = dict(x0=24.05 - 2.15, x1=24.05, y0=21.45 - 4.30, y1=21.45)   # ShopBot footprint (build_machines.py)

COLLEAGUE = ("glass door#1", "WINDOW.geo0.026", "WINDOW.geo2.026", "WINDOW.geo0.027", "WINDOW.geo2.027",
             "Component_46928", "Component_46955", "Component_47140", "Component_47490", "Component_48523",
             "Component_47517")


def clear_collection(name):
    return sa["clear_collection"](name)


def delete_colleague_parts():
    """The colleague's CNC glass door + windows and his 1.08 x 2.49 m hallway door (re-runnable: finds nothing)."""
    gone, parents = 0, set()
    for o in list(bpy.data.objects):
        if o.name.startswith(COLLEAGUE):
            if o.parent:
                parents.add(o.parent.name)
            data = o.data
            bpy.data.objects.remove(o)
            if isinstance(data, bpy.types.Mesh) and data.users == 0:
                bpy.data.meshes.remove(data)
            gone += 1
    for n in parents:
        o = bpy.data.objects.get(n)
        if o and o.type == "EMPTY" and not o.children:
            bpy.data.objects.remove(o)
    return gone


def cutter(name, x0, x1, y0, y1, z0=-0.05, z1=3.94):
    cut_col = bpy.data.collections["Facade_Cutters"]
    me = bpy.data.meshes.get(name) or bpy.data.meshes.new(name)
    bm = bmesh.new()
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r["verts"]:
        v.co = Vector((x1 if v.co.x > 0 else x0, y1 if v.co.y > 0 else y0, z1 if v.co.z > 0 else z0))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.get(name) or bpy.data.objects.new(name, me)
    if ob.name not in cut_col.objects:
        cut_col.objects.link(ob)
    ob.display_type, ob.hide_render = "WIRE", True
    ob.hide_set(True)
    root = bpy.data.objects["ROOT.geo0"]
    mod = root.modifiers.get(name) or root.modifiers.new(name, "BOOLEAN")
    mod.operation, mod.solver, mod.object = "DIFFERENCE", "EXACT", ob


def glazed_front(col):
    """Front wall to the main room, flush with the mural wall: a very tall FRAMELESS glass wall with a tall glass door
    (user): butt-jointed floor-to-slab panes, no frames or mullions. Standard office glass door, 1.0 x 2.70 m, by the
    NNE glass (x 20.90-21.90): glass-to-glass hinges in brushed aluminium clamping the leaf to the fixed pane beside it,
    brushed aluminium lock patch + pull handle, fixed glass transom above. Glass = thin Glass_Clear planes (fix_glass.py)."""
    gl = bpy.data.materials["Glass_Clear"]
    alu = mat("Alu_Brushed_Door", "#C8CBCE", 0.32, metal=1.0)   # brushed, not chrome (user)
    yc = sum(FRONT_Y) / 2
    x0, x1 = GLASS_X + 0.003, INNER_X - 0.003
    d0, d1, DH = 20.90, 21.90, 2.70
    J = 0.004                                                         # silicone butt joints
    g, p = Part(), Part()

    def pane(xa, xb, za, zb):
        g.box(gl, xa, xb, yc - 0.0005, yc + 0.0005, za, zb)
    pane(x0, d0 - J, 0.0, SOFFIT)                                    # narrow pane between façade and door
    pane(d0, d1, DH + J, SOFFIT)                                     # transom over the door
    n = max(1, round((x1 - d1) / 1.2))
    xs = [d1 + J + (x1 - d1 - J) * i / n for i in range(n + 1)]
    for xa, xb in zip(xs, xs[1:]):
        pane(xa, xb - J, 0.0, SOFFIT)
    lx0, lx1 = d0 + 0.004, d1 - 0.004                                 # door leaf (closed)
    g.box(gl, lx0, lx1, yc - 0.0005, yc + 0.0005, 0.008, DH - 0.002)
    g.emit("CNC_GlassWall_Glass", col, Vector((0, 0, 0)))
    # glass-to-glass hinges on the door side next to the fixed pane (hinge axis at x = d0)
    for z in (0.25, DH - 0.35):
        p.box(alu, d0 - 0.055, d0 + 0.055, yc - 0.014, yc + 0.014, z, z + 0.09, bevel=0.004)
        p.cyl(alu, (d0, yc, z - 0.005), (d0, yc, z + 0.095), 0.011, seg=16)
    # top pivot patch at the transom line, lock patch at the bottom on the opening side
    p.box(alu, lx1 - 0.16, lx1, yc - 0.016, yc + 0.016, 0.02, 0.10, bevel=0.004)
    p.cyl(alu, (lx1 - 0.08, yc - 0.017, 0.06), (lx1 - 0.08, yc + 0.017, 0.06), 0.012, seg=16)
    # pull handle both faces: brushed aluminium bar 0.6 m
    hx = lx1 - 0.10
    for sgn in (-1, 1):
        for z in (0.80, 1.30):
            p.cyl(alu, (hx, yc + sgn * 0.001, z), (hx, yc + sgn * 0.055, z), 0.008, seg=12)
        p.cyl(alu, (hx, yc + sgn * 0.055, 0.75), (hx, yc + sgn * 0.055, 1.35), 0.0125, seg=20)
    p.emit("CNC_GlassWall_Fittings", col, Vector((0, 0, 0)))


def walls(col):
    # old front wall (y 23.05-23.14, glass door + window) and the side wall's window stretch beyond the mural line
    cutter("Cut_CNC_Front", GLASS_X + 0.005, 24.27, 23.00, 23.20)
    cutter("Cut_CNC_Side", 24.10, 24.30, FRONT_Y[1] + 0.001, 23.20)
    glazed_front(col)
    wall = bpy.data.materials["Paint_White"]
    # hallway: normal door in the colleague's 1.08 m opening (y 16.81-17.89), the wall completed round it, and the
    # knocked-down WC's old doorway (y 18.14-18.93) walled up
    hc, ht = sum(HALL_WALL) / 2, HALL_WALL[1] - HALL_WALL[0]
    sa["door_in_wall"](col, "CNC_Door_Hall", "y", hc, ht, 16.807, 17.894, -1, 0, angle=70)
    p = Part()
    p.box(wall, HALL_WALL[0], HALL_WALL[1], 18.13, 18.94, 0.0, SOFFIT)
    p.emit("CNC_HallWall_Infill", col, Vector((0, 0, 0)))


def operator_corner(col, M):
    """Ex-WC bay (x 24.15-25.74, y 17.9-19.27): PC station on the WC partition (faces -y) + tool bench and pegboard on
    the hallway wall (faces -x). Clear of the hallway door (y <= 17.87 + casing)."""
    blk, ply = M["black"], MAT["ply"]
    # --- standing PC desk on the partition: 0.90 x 0.45, top 1.05, monitor on a wall arm, control box under it
    x0, x1, y1 = 24.27, 25.12, 19.26
    y0, h = y1 - 0.45, 1.05
    p = Part()
    for x in (x0, x1 - 0.04):
        for y in (y0, y1 - 0.04):
            p.profile(0.04, "z", x, y, 0.035, h - 0.06)
            lib["foot"](p, x + 0.02, y + 0.02)
    for y in (y0, y1 - 0.04):
        p.profile(0.04, "x", x0 + 0.04, y, h - 0.065, x1 - x0 - 0.08)
    p.box(ply, x0 - 0.01, x1 + 0.01, y0 - 0.01, y1, h - 0.025, h, bevel=0.003)
    mx = (x0 + x1) / 2 - 0.05
    p.box(blk, mx - 0.04, mx + 0.04, y1 - 0.01, y1, 1.30, 1.42)                           # wall plate
    p.box(blk, mx - 0.015, mx + 0.015, y1 - 0.25, y1 - 0.01, 1.34, 1.38)                  # arm
    scr = Matrix.Translation((mx, y1 - 0.27, 1.42)) @ Matrix.Rotation(math.radians(-25), 4, "Z")
    bmesh.ops.create_cube(p.bm(blk), size=1.0, matrix=scr @ Matrix.Diagonal((0.56, 0.03, 0.33, 1)))
    bmesh.ops.create_cube(p.bm(M["blackglass"]), size=1.0,
                          matrix=scr @ Matrix.Translation((0, -0.0155, 0)) @ Matrix.Diagonal((0.54, 0.001, 0.31, 1)))
    p.box(blk, mx - 0.22, mx + 0.22, y0 + 0.05, y0 + 0.19, h, h + 0.02, bevel=0.003)       # keyboard
    p.box(blk, mx + 0.27, mx + 0.33, y0 + 0.08, y0 + 0.17, h, h + 0.03, bevel=0.01)        # mouse
    red, yel = mat("EStop_Red", "#D32F2F", 0.4), mat("EStop_Yellow", "#F2C200", 0.5)       # e-stop pendant
    p.box(yel, x1 - 0.17, x1 - 0.05, y0 + 0.05, y0 + 0.17, h, h + 0.06, bevel=0.006)
    p.cyl(red, (x1 - 0.11, y0 + 0.11, h + 0.06), (x1 - 0.11, y0 + 0.11, h + 0.10), 0.03, seg=20)
    p.emit("CNC_PCStation", col, Vector((0, 0, 0)))
    # --- tool bench on the hallway wall (faces -x): 0.60 deep, 0.90 high, drawer bank, pegboard above
    wx = HALL_WALL[0]
    by0, by1 = 18.05, 19.25
    bx0 = wx - 0.60
    p = Part()
    for y in (by0, by1 - 0.04):
        for x in (bx0, wx - 0.05):
            p.profile(0.04, "z", x, y, 0.035, 0.84)
            lib["foot"](p, x + 0.02, y + 0.02)
    for x in (bx0, wx - 0.05):
        p.profile(0.04, "y", x, by0 + 0.04, 0.82, by1 - by0 - 0.08)
    p.box(ply, bx0 - 0.01, wx, by0 - 0.01, by1 + 0.01, 0.875, 0.90, bevel=0.003)
    dy0 = by0 + 0.06                                                  # drawer bank under the left half
    p.box(ply, bx0 + 0.04, wx - 0.06, dy0, dy0 + 0.55, 0.10, 0.85)
    for k in range(5):
        z0 = 0.11 + k * 0.148
        p.box(ply, bx0 + 0.02, bx0 + 0.04, dy0 + 0.005, dy0 + 0.545, z0, z0 + 0.14, bevel=0.002)
        p.box(blk, bx0 + 0.005, bx0 + 0.02, dy0 + 0.20, dy0 + 0.35, z0 + 0.10, z0 + 0.115)
    # pegboard + tools
    peg = mat("Pegboard_Birch", "#D8C29C", 0.6)
    p.box(peg, wx - 0.012, wx, by0, by1, 1.05, 1.95)
    tools = mat("Tool_Steel", "#B9BDC1", 0.25, metal=1.0)
    for i in range(6):                                                # wrenches / collet spanners
        y = by0 + 0.10 + i * 0.07
        p.box(tools, wx - 0.025, wx - 0.015, y, y + 0.025, 1.55 - i * 0.02, 1.80)
    for i in range(3):                                                # router-bit blocks (birch with holes)
        y = by0 + 0.62 + i * 0.17
        p.box(ply, wx - 0.10, wx - 0.012, y, y + 0.14, 1.20, 1.25, bevel=0.003)
        for j in range(4):
            p.cyl(tools, (wx - 0.08 + j * 0.0, y + 0.02 + j * 0.033, 1.25),
                  (wx - 0.08 + j * 0.0, y + 0.02 + j * 0.033, 1.31), 0.005, seg=8)
    for y, h in ((by1 - 0.30, "#F2C200"), (by1 - 0.14, "#E03A3F")):  # ear defenders
        m = mat(f"EarDefender_{h[1:]}", h, 0.5)
        p.cyl(m, (wx - 0.10, y - 0.05, 1.70), (wx - 0.02, y - 0.05, 1.70), 0.045, seg=20)
        p.cyl(m, (wx - 0.10, y + 0.05, 1.70), (wx - 0.02, y + 0.05, 1.70), 0.045, seg=20)
        p.cyl(blk, (wx - 0.06, y - 0.05, 1.76), (wx - 0.06, y + 0.05, 1.76), 0.008, seg=8)
    gl = mat("SafetyGlasses_Clear", "#CFE3EA", 0.05, coat=0.5)
    p.box(gl, wx - 0.05, wx - 0.015, by1 - 0.42, by1 - 0.26, 1.50, 1.55, bevel=0.005)
    p.box(blk, wx - 0.18, wx - 0.012, by0 + 0.55, by0 + 0.58, 1.40, 1.42)                 # shelf strip
    p.cyl(mat("Clamp_Orange", "#FFA13D", 0.4), (wx - 0.14, by0 + 0.25, 0.90), (wx - 0.14, by0 + 0.45, 0.90), 0.018, seg=12)
    p.emit("CNC_ToolBench", col, Vector((0, 0, 0)))


def utilities(col, M):
    p = Part()
    # shop vac next to the collector (glass corner) - cleaning the bed between jobs
    vx, vy = 21.30, 15.45
    p.cyl(mat("ShopVac_Green", "#2E7D4F", 0.45), (vx, vy, 0.06), (vx, vy, 0.52), 0.19, seg=32)
    p.cyl(M["black"], (vx, vy, 0.52), (vx, vy, 0.62), 0.17, seg=32)
    for a in range(4):
        t = a * math.pi / 2 + 0.4
        p.cyl(M["black"], (vx + 0.17 * math.cos(t), vy + 0.17 * math.sin(t), 0.0),
              (vx + 0.17 * math.cos(t), vy + 0.17 * math.sin(t), 0.06), 0.025, seg=10)
    # CO2 extinguisher on the WNW wall
    ex, ey = 22.15, 15.17
    p.cyl(mat("Extinguisher_Red", "#C62828", 0.35, coat=0.4), (ex, ey, 0.30), (ex, ey, 0.92), 0.075, seg=24)
    p.cyl(M["black"], (ex, ey, 0.92), (ex, ey, 1.02), 0.02, seg=12)
    p.cyl(M["black"], (ex, ey - 0.05, 0.98), (ex + 0.12, ey - 0.10, 0.98), 0.012, seg=8)
    p.emit("CNC_Utilities", col, Vector((0, 0, 0)))


def build():
    col = clear_collection("CNCRoom")
    M = sa["mats"]()
    n = delete_colleague_parts()
    walls(col)
    operator_corner(col, M)
    utilities(col, M)
    print("CNC room built,", n, "colleague parts deleted,", len(col.objects), "objects")


if __name__ == "__main__":
    build()
