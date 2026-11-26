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
- WNW end wall: the 2.3 m gap is a LOADING DOOR, classic double door with two swinging leaves (user); steel leaves,
  opening outward (my details); glass windows either side and above the door frame (user), façade-style frames.
- Outside the end wall the colleague's parquet ran on to y 12.81: concrete pavers there now.
- The back hallway's WNW end (x 26.22-27.51) is a GLASS DOOR (user): framed glass leaf + sidelight + fanlight (my details).
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


def manifestation_mat(pitch=0.20, pitch_z=0.20, radius=0.05):
    """Sandblasted dot manifestation (safety marking on glass): satin-white frosted dots in a square grid, procedural in
    world space (dots run along x on this wall, rows in z), everything between the dots fully clear."""
    m = bpy.data.materials.get("Glass_Manifestation_Dots") or bpy.data.materials.new("Glass_Manifestation_Dots")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    out = N("ShaderNodeOutputMaterial")
    geo, sep = N("ShaderNodeNewGeometry"), N("ShaderNodeSeparateXYZ")
    L(geo.outputs["Position"], sep.inputs[0])

    def math(op, a, b=None):
        n = N("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L(v, n.inputs[i])
        return n.outputs[0]

    def centred(c, pt):                                              # (fract(c / pt) - 0.5) * pt, metres
        return math("MULTIPLY", math("SUBTRACT", math("FRACT", math("DIVIDE", c, pt)), 0.5), pt)
    u, v = centred(sep.outputs["X"], pitch), centred(sep.outputs["Z"], pitch_z)
    d = math("SQRT", math("ADD", math("MULTIPLY", u, u), math("MULTIPLY", v, v)))
    mask = math("LESS_THAN", d, radius)
    frost = N("ShaderNodeBsdfPrincipled")
    frost.inputs["Base Color"].default_value = (0.93, 0.95, 0.96, 1)
    frost.inputs["Roughness"].default_value = 0.55
    frost.inputs["Transmission Weight"].default_value = 0.25
    clear = N("ShaderNodeBsdfTransparent")
    mix = N("ShaderNodeMixShader")
    L(mask, mix.inputs["Fac"])
    L(clear.outputs[0], mix.inputs[1])
    L(frost.outputs[0], mix.inputs[2])
    L(mix.outputs[0], out.inputs["Surface"])
    m.surface_render_method = "DITHERED"
    m.diffuse_color = (0.9, 0.92, 0.93, 0.3)
    return m


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
    # manifestation (user: make the glass read as a divider without hiding the ShopBot): two rows of sandblasted dots
    # across every pane incl. the door, on the main-room face - 100 mm dots 200 mm apart (user: bigger, then every
    # other dot dropped, then bigger again): one row at 0.90 m, one at 1.50 m; the rest of the glass stays clear. Gap on
    # the door round the pull handle. The pattern RESTARTS ON EVERY PANE (2026-11-25; it used to run on across the
    # butt joints like one sheet): each pane gets a whole number of dots, centred, >= 80 mm from its edges. Real discs,
    # not a world-space procedural mask.
    frost = bpy.data.materials.get("Glass_Manifestation_Frost") or bpy.data.materials.new("Glass_Manifestation_Frost")
    frost.use_nodes = True
    bs = frost.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (0.93, 0.95, 0.96, 1)
    bs.inputs["Roughness"].default_value = 0.55
    bs.inputs["Transmission Weight"].default_value = 0.25
    frost.diffuse_color = (0.9, 0.92, 0.93, 1)
    md = Part()
    ym = yc + 0.0015
    hx0 = lx1 - 0.17                                                 # handle zone on the door leaf
    PITCH, RAD, EDGE = 0.20, 0.05, 0.08
    spans = [(x0, d0 - J), (d0 + 0.02, hx0)] + list(zip(xs[:-1], [v - J for v in xs[1:]]))
    for xa, xb in spans:
        n = int((xb - xa - 2 * EDGE) / PITCH) + 1
        if n < 1:
            continue
        c = (xa + xb) / 2
        for z in (0.90, 1.50):                                       # single rows at 0.90 / 1.50
            for i in range(n):
                x = c + (i - (n - 1) / 2) * PITCH
                md.cyl(frost, (x, ym, z), (x, ym + 0.0004, z), RAD, seg=24)
    md.emit("CNC_GlassWall_Manifestation", col, Vector((0, 0, 0)))


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
    # E9 (2026-11-26, my design on Magnus's go-ahead to iterate): the pegboard sits in a shallow ply wall cabinet
    # (0.20 deep: clears the bit blocks and ear defenders) behind a pair of clear acrylic doors with one e-lock
    # (scripts/lockdown.py); the room is locked as well.
    cz0, cz1, cd = 1.02, 1.98, 0.20
    p.box(ply, wx - cd, wx - 0.012, by0 - 0.02, by1 + 0.02, cz0, cz0 + 0.018, bevel=0.0015)     # bottom
    p.box(ply, wx - cd, wx - 0.012, by0 - 0.02, by1 + 0.02, cz1 - 0.018, cz1, bevel=0.0015)     # top
    for y in (by0 - 0.02, by1 + 0.002):
        p.box(ply, wx - cd, wx - 0.012, y, y + 0.018, cz0, cz1)                                # ends
    p.emit("CNC_ToolBench", col, Vector((0, 0, 0)))
    ld = {}
    exec(open(bpy.path.abspath("//scripts/lockdown.py")).read(), ld)
    dr = Part()
    ld["door_run"](dr, "-x", wx - cd, by0 - 0.017, by1 + 0.017, cz0 + 0.003, cz1 - 0.003, leaves=2, lock_z=1.36)
    dob = dr.emit("CNC_ToolBench_Doors", col, Vector((0, 0, 0)))
    for o in [dob, *dob.children_recursive]:
        o["layout_skip"] = True


def utilities(col, M):
    p = Part()
    # shop vac next to the collector - cleaning the bed between jobs
    vx, vy = 22.20, 16.45
    p.cyl(mat("ShopVac_Green", "#2E7D4F", 0.45), (vx, vy, 0.06), (vx, vy, 0.52), 0.19, seg=32)
    p.cyl(M["black"], (vx, vy, 0.52), (vx, vy, 0.62), 0.17, seg=32)
    for a in range(4):
        t = a * math.pi / 2 + 0.4
        p.cyl(M["black"], (vx + 0.17 * math.cos(t), vy + 0.17 * math.sin(t), 0.0),
              (vx + 0.17 * math.cos(t), vy + 0.17 * math.sin(t), 0.06), 0.025, seg=10)
    # CO2 extinguisher on the board rack's end post, by the hallway door
    ex, ey = 24.30, 16.60
    p.box(M["black"], ex + 0.06, ex + 0.10, ey - 0.03, ey + 0.03, 0.80, 0.95)                 # bracket
    p.cyl(mat("Extinguisher_Red", "#C62828", 0.35, coat=0.4), (ex, ey, 0.30), (ex, ey, 0.92), 0.075, seg=24)
    p.cyl(M["black"], (ex, ey, 0.92), (ex, ey, 1.02), 0.02, seg=12)
    p.cyl(M["black"], (ex, ey - 0.05, 0.98), (ex - 0.12, ey - 0.10, 0.98), 0.012, seg=8)
    p.emit("CNC_Utilities", col, Vector((0, 0, 0)))


WIN_TOP = 3.60                                                       # glazing height (as the façades)


def end_windows(col):
    """WNW end wall (user): glass windows either side of the loading door and above its frame. Same dark aluminium
    window frames and thin glass as the façades: floor-to-3.60 panes with a transom at the door-head line (2.46),
    a glazed fanlight over the door; the colleague's wall either side is cut away (Cut_CNC_WinL / _WinR)."""
    n0, n1 = 14.868, 15.075
    yc = (n0 + n1) / 2
    fr, gl = bpy.data.materials["Alu_Frame_Dark"], bpy.data.materials["Glass_Clear"]
    cutter("Cut_CNC_WinL", 20.86, 22.397, n0 - 0.02, n1 + 0.02, -0.05, WIN_TOP)
    cutter("Cut_CNC_WinR", 24.721, 25.742, n0 - 0.02, n1 + 0.02, -0.05, WIN_TOP)
    p, g = Part(), Part()
    F, TR = 0.06, 2.40
    for xa, xb in ((20.80, 22.397), (24.721, 25.743)):
        p.box(fr, xa, xa + F, yc - 0.035, yc + 0.035, 0.0, WIN_TOP)            # jambs
        p.box(fr, xb - F, xb, yc - 0.035, yc + 0.035, 0.0, WIN_TOP)
        p.box(fr, xa, xb, yc - 0.035, yc + 0.035, 0.0, F)                      # sill
        p.box(fr, xa, xb, yc - 0.035, yc + 0.035, TR, TR + F)                  # transom (door-head line)
        p.box(fr, xa, xb, yc - 0.035, yc + 0.035, WIN_TOP - F, WIN_TOP)        # head
        p.box(bpy.data.materials["Paint_White"], xa, xb, n0, n1, WIN_TOP, SOFFIT)   # wall above stays
        g.box(gl, xa + F, xb - F, yc - 0.0005, yc + 0.0005, F, TR)
        g.box(gl, xa + F, xb - F, yc - 0.0005, yc + 0.0005, TR + F, WIN_TOP - F)
    a0, a1 = 22.397, 24.721                                          # fanlight over the door frame
    mid = (a0 + a1) / 2
    p.box(fr, a0, a1, yc - 0.035, yc + 0.035, WIN_TOP - F, WIN_TOP)
    p.box(fr, mid - F / 2, mid + F / 2, yc - 0.035, yc + 0.035, TR + F, WIN_TOP)
    for xa, xb in ((a0 + F, mid - F / 2), (mid + F / 2, a1 - F)):
        g.box(gl, xa, xb, yc - 0.0005, yc + 0.0005, TR + F, WIN_TOP - F)
    p.emit("CNC_EndWindows_Frame", col, Vector((0, 0, 0)))
    g.emit("CNC_EndWindows_Glass", col, Vector((0, 0, 0)))


def hall_end_door(col):
    """Back hallway's WNW end (x 26.22-27.514, the colleague left it as an open full-height gap): a GLASS DOOR (user).
    My details: exterior aluminium glass door in the same dark frames as the end windows - 1.0 m leaf (fully glazed,
    lever + lock, opens outward) with a narrow fixed glass sidelight, glazed fanlight above to 3.60 m, wall above."""
    n0, n1 = 14.868, 15.075
    yc = (n0 + n1) / 2
    a0, a1 = 26.22, 27.514
    fr, gl = bpy.data.materials["Alu_Frame_Dark"], bpy.data.materials["Glass_Clear"]
    alu = mat("Alu_Brushed_Door", "#C8CBCE", 0.32, metal=1.0)
    F, H = 0.06, 2.40
    d0 = a0 + F                                                      # leaf hinge jamb (by the CNC wall)
    d1 = d0 + 1.00
    p, g = Part(), Part()
    for xa in (a0, d1, a1 - F):                                      # jambs + mullion between leaf and sidelight
        p.box(fr, xa, xa + F, yc - 0.035, yc + 0.035, 0.0, WIN_TOP)
    p.box(fr, a0, a1, yc - 0.035, yc + 0.035, H, H + F)              # transom
    p.box(fr, a0, a1, yc - 0.035, yc + 0.035, WIN_TOP - F, WIN_TOP)  # head
    p.box(fr, d1 + F, a1 - F, yc - 0.035, yc + 0.035, 0.0, F)        # sidelight sill
    p.box(bpy.data.materials["Paint_White"], a0, a1, n0, n1, WIN_TOP, SOFFIT)
    g.box(gl, a0 + F, a1 - F, yc - 0.0005, yc + 0.0005, H + F, WIN_TOP - F)           # fanlight
    g.box(gl, d1 + F, a1 - F, yc - 0.0005, yc + 0.0005, F, H)                          # sidelight
    # leaf (closed): 70 mm stiles, deeper bottom rail, glass, lever handles both faces + lock
    lx0, lx1 = d0 + 0.003, d1 - 0.003
    for xa, xb in ((lx0, lx0 + 0.07), (lx1 - 0.07, lx1)):
        p.box(fr, xa, xb, yc - 0.03, yc + 0.03, 0.005, H - 0.003)
    p.box(fr, lx0, lx1, yc - 0.03, yc + 0.03, 0.005, 0.16)
    p.box(fr, lx0, lx1, yc - 0.03, yc + 0.03, H - 0.07, H - 0.003)
    g.box(gl, lx0 + 0.07, lx1 - 0.07, yc - 0.0005, yc + 0.0005, 0.16, H - 0.07)
    hx = lx1 - 0.035
    for sgn in (-1, 1):
        y = yc + sgn * 0.03
        p.box(alu, hx - 0.018, hx + 0.018, y, y + sgn * 0.008, 0.95, 1.20, bevel=0.003)
        p.cyl(alu, (hx, y, 1.06), (hx, y + sgn * 0.05, 1.06), 0.009, seg=12)
        p.cyl(alu, (hx, y + sgn * 0.05, 1.06), (hx - 0.14, y + sgn * 0.05, 1.06), 0.010, seg=12)
    for z in (0.25, 1.20, 2.10):                                     # hinges on the outside face
        p.cyl(alu, (d0 + 0.004, n0 + 0.06, z), (d0 + 0.004, n0 + 0.06, z + 0.10), 0.010, seg=12)
    p.emit("Hall_EndDoor_Frame", col, Vector((0, 0, 0)))
    g.emit("Hall_EndDoor_Glass", col, Vector((0, 0, 0)))


def exterior_paving(col):
    """The colleague's parquet floor runs on outside the WNW end of the building (to y 12.81): cover the outdoor strip
    with concrete pavers (Ground_Pavers, Poly Haven concrete_pavers, CC0), stepped like the building line."""
    pav = bpy.data.materials["Ground_Pavers"]
    p = Part()
    p.box(pav, 20.74, 29.25, 12.81, 14.862, 0.0, 0.004)
    p.box(pav, 29.25, 32.59, 12.81, 13.10, 0.0, 0.004)
    p.emit("Exterior_Paving_WNW", col, Vector((0, 0, 0)))


def loading_door(col, M):
    """WNW end wall (y 14.868-15.075): the colleague's 2.32 m full-height gap (x 22.397-24.721) is a LOADING DOOR - a
    classic double door, two swinging leaves (user). My details: painted-steel leaves 2 x 1.10 x 2.40 m in a steel
    frame, glazed fanlight above (end_windows), opening OUTWARD (exterior door),
    fixed leaf with flush bolts, active leaf with a lever handle + lock, drawn ajar so the door reads as a door."""
    a0, a1, n0, n1 = 22.397, 24.721, 14.868, 15.075
    H, FW = 2.40, 0.06
    wall = bpy.data.materials["Paint_White"]
    steel = mat("Door_Steel_Grey", "#C9CCCE", 0.45, metal=0.2)
    frame = mat("Door_Frame_Grey", "#8A8F93", 0.4, metal=0.4)
    alu = mat("Alu_Brushed_Door", "#C8CBCE", 0.32, metal=1.0)
    p = Part()
    p.box(wall, a0, a1, n0, n1, WIN_TOP, SOFFIT)                     # wall above the glazing
    p.box(frame, a0, a0 + FW, n0 - 0.005, n1 + 0.005, 0.0, H + FW)  # frame
    p.box(frame, a1 - FW, a1, n0 - 0.005, n1 + 0.005, 0.0, H + FW)
    p.box(frame, a0, a1, n0 - 0.005, n1 + 0.005, H, H + FW)
    p.box(frame, a0 + FW, a1 - FW, n0 + 0.02, n1 - 0.02, 0.0, 0.012)  # threshold
    p.emit("CNC_LoadingDoor_Frame", col, Vector((0, 0, 0)))
    LW = (a1 - a0 - 2 * FW) / 2 - 0.004
    T = 0.055
    yo = n0 + 0.03                                                   # leaves sit near the outer face
    for k, (hx, sgn, ang) in enumerate(((a0 + FW + 0.002, 1, 0.0), (a1 - FW - 0.002, -1, 35.0))):
        q = Part()
        q.box(steel, 0.0, LW, -T / 2, T / 2, 0.012, H - 0.004, bevel=0.003)
        for z0 in (0.95, 1.85):                                      # pressed stiffener lines
            q.box(steel, 0.08, LW - 0.08, -T / 2 - 0.002, -T / 2, z0, z0 + 0.01)
            q.box(steel, 0.08, LW - 0.08, T / 2, T / 2 + 0.002, z0, z0 + 0.01)
        for z in (0.20, 1.20, 2.15):                                 # hinges
            q.cyl(frame, (-0.006, -T / 2 - 0.005, z), (-0.006, -T / 2 - 0.005, z + 0.12), 0.012, seg=12)
        if k == 1:                                                    # active leaf: levers both sides + lock
            for side in (-1, 1):
                y = side * (T / 2 + 0.05)
                q.box(alu, LW - 0.10, LW - 0.06, side * T / 2, side * (T / 2 + 0.008), 0.96, 1.18, bevel=0.003)
                q.cyl(alu, (LW - 0.08, side * T / 2, 1.05), (LW - 0.08, y, 1.05), 0.009, seg=12)
                q.cyl(alu, (LW - 0.08, y, 1.05), (LW - 0.22, y, 1.05), 0.010, seg=12)
        else:                                                         # fixed leaf: flush bolts top + bottom
            q.box(alu, LW - 0.04, LW - 0.015, T / 2, T / 2 + 0.006, 0.05, 0.25)
            q.box(alu, LW - 0.04, LW - 0.015, T / 2, T / 2 + 0.006, H - 0.25, H - 0.05)
        rot = (0.0 if sgn > 0 else math.pi) - sgn * math.radians(ang)   # opens outward (towards -y)
        q.emit(f"CNC_LoadingDoor_Leaf_{k + 1}", col, Vector((hx, yo, 0)), rot)


def build():
    col = clear_collection("CNCRoom")
    M = sa["mats"]()
    n = delete_colleague_parts()
    walls(col)
    operator_corner(col, M)
    utilities(col, M)
    loading_door(col, M)
    end_windows(col)
    hall_end_door(col)
    exterior_paving(col)
    print("CNC room built,", n, "colleague parts deleted,", len(col.objects), "objects")


if __name__ == "__main__":
    build()
    # Placements come from layout/layout.yaml (layout/README.md): built at this builder's coordinates, then moved there.
    _lay = {}
    exec(open(bpy.path.abspath("//scripts/layout_blender.py")).read(), _lay)
    _lay["apply"]()
