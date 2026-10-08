"""Back staff area: hallway WC, staff room (cafeteria / meeting / ranting lounge), the knocked-down second WC.
Re-runnable ("StaffArea" collection + the Cut_WC2 boolean on the colleague's wall mesh ROOT.geo0).
Model frame: +X = SSW (sunny façade), +Y = ESE.

Facts (user, 2026-10-08):
- Of the two tiny WCs off the back hallway, the one further north (x 24.26-25.74, y 17.89-19.27) has been knocked
  down and is now part of the CNC room; its hallway doorway (y 18.14-18.93) stays as an OPEN PASSAGE, no door.
  The other (x 24.26-25.735, y 19.42-21.66, door y 19.58-20.57) stays: standard WC - wall-hung toilet on a tiled
  cistern box, small basin + mirror, wall tiles to 1.2 m, floor tiles, extractor fan, roll holder, brush, towels.
- The large room next to the laser room (x 27.73-32.44, y 17.65-19.98 + an entry bay x 27.73-29.52, y 19.98-21.63,
  doorway from the hallway at y 20.31-21.35) is the staff cafeteria / meeting room / ranting lounge. Contents (user):
  kitchenette with sink, fridge, coffee machine, microwave, dishwasher and wall cupboards; a meeting table for 3-4;
  whiteboard (no screen); a sofa/armchair corner; coat hooks (no lockers).
Layout (my choices, not the user's): kitchenette along the hallway wall, fridge at its open end by the entry bay (its
door must open: keep >= 1 m clear in front of the whole run); meeting table for 4 in the middle with its end on the
WNW wall; ranting corner in the window end (IKEA GLOSTAD 2-seat sofa on the WNW wall, POÄNG armchair facing it from the
laser-wall corner, small round table); whiteboard on the laser-room wall over the route; coat hooks + hat shelf on the
laser partition in the entry bay. Door into the staff room shown open. Hallway sign in Icelandic: "KAFFISTOFA /
starfsfólk".
Real furniture at catalogue size, modelled from IKEA product photos: GLOSTAD 121 x 78 x 68 (seat 41, arm 57, arm
3.5 cm, 23 cm free under, thin angled black legs); POÄNG 68 x 82 x 100 (seat 42, bentwood birch cantilever frame).
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = bpy.path.abspath("//scripts/")
lib = {}
exec(open(HERE + "profile_furniture.py").read(), lib)
MAT = lib["materials"]()
_t = open(HERE + "build_textile.py").read()
tex = {}
exec(_t[:_t.index("\ndef build():")], tex)                         # chair()
mat, Part, lin = lib["simple_mat"], lib["Part"], lib["lin"]

# room geometry (measured by ray casts on the colleague's walls)
WC = dict(x0=24.26, x1=25.735, y0=19.42, y1=21.66, door=(19.576, 20.573))
ST = dict(x0=27.73, x1=32.435, y0=17.645, y1=19.984, bay_x1=29.517, bay_y1=21.63, door=(20.31, 21.35))
HALL_X = (25.90, 27.51)
SOFFIT = 3.93


def clear_collection(name):
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    for o in list(col.objects):
        data = o.data
        bpy.data.objects.remove(o)
        if isinstance(data, bpy.types.Mesh) and data.users == 0:
            bpy.data.meshes.remove(data)
        elif isinstance(data, bpy.types.Light) and data.users == 0:
            bpy.data.lights.remove(data)
    return col


def fabric(name, hexcol, sheen=0.3):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = lin(hexcol)
    b.inputs["Roughness"].default_value = 0.9
    b.inputs["Sheen Weight"].default_value = sheen
    if not any(n.type == "TEX_NOISE" for n in nt.nodes):
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 700
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.15
        nt.links.new(geo.outputs["Position"], nz.inputs["Vector"])
        nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    m.diffuse_color = lin(hexcol)
    return m


def tile(name, hexcol, grout, size, plane):
    """Square tiles with grout lines in world space; plane = 'xy' (floor), 'yz' (walls facing x), 'xz'."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    out, b = N("ShaderNodeOutputMaterial"), N("ShaderNodeBsdfPrincipled")
    geo, sep, comb = N("ShaderNodeNewGeometry"), N("ShaderNodeSeparateXYZ"), N("ShaderNodeCombineXYZ")
    L(geo.outputs["Position"], sep.inputs[0])
    a, c = {"xy": ("X", "Y"), "yz": ("Y", "Z"), "xz": ("X", "Z")}[plane]
    L(sep.outputs[a], comb.inputs["X"])
    L(sep.outputs[c], comb.inputs["Y"])
    br = N("ShaderNodeTexBrick")
    br.offset, br.squash = 0.0, 1.0
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = size
    br.inputs["Row Height"].default_value = size
    br.inputs["Mortar Size"].default_value = 0.0022
    br.inputs["Mortar Smooth"].default_value = 0.3
    br.inputs["Bias"].default_value = 0.0
    br.inputs["Color1"].default_value = lin(hexcol)
    br.inputs["Color2"].default_value = tuple(v * 0.97 for v in lin(hexcol)[:3]) + (1,)
    br.inputs["Mortar"].default_value = lin(grout)
    L(comb.outputs[0], br.inputs["Vector"])
    L(br.outputs["Color"], b.inputs["Base Color"])
    rough = N("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value, rough.inputs["To Max"].default_value = 0.12, 0.7
    L(br.outputs["Fac"], rough.inputs["Value"])
    L(rough.outputs[0], b.inputs["Roughness"])
    bump = N("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.002
    inv = N("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    L(br.outputs["Fac"], inv.inputs[1])
    L(inv.outputs[0], bump.inputs["Height"])
    L(bump.outputs["Normal"], b.inputs["Normal"])
    L(b.outputs["BSDF"], out.inputs["Surface"])
    m.diffuse_color = lin(hexcol)
    return m


def mats():
    M = {}
    M["ceramic"] = mat("Ceramic_White", "#F3F3F0", 0.06, coat=0.6)
    M["steel"] = mat("Steel_Brushed", "#B9BDC1", 0.28, metal=1.0)
    M["chrome"] = mat("Chrome", "#E8EAEC", 0.05, metal=1.0)
    M["black"] = mat("Cart_Black", "#1F1F20", 0.45, metal=0.3)
    M["blackglass"] = mat("Glass_BlackGloss", "#0B0C0D", 0.05, coat=0.8)
    M["worktop"] = mat("Worktop_Compact_Anthracite", "#2C2E30", 0.35)
    M["mirror"] = mat("Mirror", "#F2F4F5", 0.0, metal=1.0)
    M["white"] = mat("Paint_White_Gloss", "#F1F1EE", 0.3)
    M["board"] = mat("Whiteboard_Enamel", "#FAFAF8", 0.08, coat=0.5)
    M["alu"] = mat("Alu_Satin", "#C4C7CA", 0.3, metal=1.0)
    M["door"] = mat("Door_Birch_Veneer", "#D9C29E", 0.45)
    M["wall_tile_x"] = tile("Tile_Wall_X", "#F2F2EE", "#C9C9C4", 0.15, "yz")
    M["wall_tile_y"] = tile("Tile_Wall_Y", "#F2F2EE", "#C9C9C4", 0.15, "xz")
    M["floor_tile"] = tile("Tile_Floor_Grey", "#6B6D6E", "#4D4F50", 0.30, "xy")
    M["sofa"] = fabric("Knisa_DarkGrey", "#3B3D40")
    M["poang"] = fabric("Kelinge_DarkYellow", "#B38A2E", 0.3)
    M["coats"] = [fabric(n, h, 0.2) for n, h in (("Coat_Navy", "#1E2A3E"), ("Coat_Olive", "#4D5233"),
                                                    ("Coat_Red", "#B3262B"), ("Coat_Black", "#1C1C1D"))]
    M["mugs"] = [mat(n, h, 0.25, coat=0.4) for n, h in (("Mug_White", "#F4F3EF"), ("Mug_Green", "#009967"),
                                                         ("Mug_Orange", "#FFA13D"))]
    return M


def put(p, name, col, cx, cy, w, d, facing):
    loc, rot = lib["placement"](cx, cy, w, d, facing)
    return p.emit(name, col, loc, rot)


def strip(p, m, pts, x, w=0.045, t=0.026):
    """Bent-laminate strip through (y, z) points at lateral position x (POÄNG frame)."""
    bm = p.bm(m)
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        d = Vector((0, y1 - y0, z1 - z0))
        ang = math.atan2(d.z, d.y)
        mtx = Matrix.Translation((x, (y0 + y1) / 2, (z0 + z1) / 2)) @ Matrix.Rotation(ang, 4, "X") \
            @ Matrix.Diagonal((w, d.length + t * 0.9, t, 1))
        bmesh.ops.create_cube(bm, size=1.0, matrix=mtx)


def soften(root, names, width=0.02):
    for k in root.children:
        if any(k.name.endswith(n) for n in names):
            bv = k.modifiers.new("Soft", "BEVEL")
            bv.width, bv.segments, bv.limit_method = width, 3, "ANGLE"
            sd = k.modifiers.new("Subd", "SUBSURF")
            sd.levels, sd.render_levels = 1, 2


# ------------------------------------------------------------------ the knocked-down WC
def demolish_wc2():
    """Boolean cutter on ROOT.geo0 removes WC 2's walls (the CNC-side wall and the WNW wall) so its floor joins the
    CNC room; the hallway wall (x 25.735-25.90) and WC 1's wall (y >= 19.27) stay - the old doorway at y 18.14-18.93
    becomes an open passage from the hallway into the CNC room."""
    cut_col = bpy.data.collections["Facade_Cutters"]
    me = bpy.data.meshes.get("Cut_WC2") or bpy.data.meshes.new("Cut_WC2")
    bm = bmesh.new()
    r = bmesh.ops.create_cube(bm, size=1.0)
    x0, x1, y0, y1, z0, z1 = 24.08, 25.735, 17.85, 19.265, -0.05, 3.94
    for v in r["verts"]:
        v.co = Vector((x1 if v.co.x > 0 else x0, y1 if v.co.y > 0 else y0, z1 if v.co.z > 0 else z0))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.get("Cut_WC2") or bpy.data.objects.new("Cut_WC2", me)
    if ob.name not in cut_col.objects:
        cut_col.objects.link(ob)
    ob.display_type, ob.hide_render = "WIRE", True
    ob.hide_set(True)                       # like the façade cutters: hidden in the viewport too (else the Rendered
                                            # viewport shows the cutter as a solid block where the WC used to be)
    root = bpy.data.objects["ROOT.geo0"]
    mod = root.modifiers.get("Cut_WC2") or root.modifiers.new("Cut_WC2", "BOOLEAN")
    mod.operation, mod.solver, mod.object = "DIFFERENCE", "EXACT", ob


# ------------------------------------------------------------------ WC 1
def door(col, name, hinge, width, opening_dir, angle_deg, h=2.10, t=0.04, plaque=None):
    """Flush birch-veneer door: hinge = (x, y) on the wall line, closed leaf runs along `opening_dir` (unit 2D)
    from the hinge; it is drawn swung open by angle_deg (positive = counter-clockwise seen from above)."""
    p = Part()
    p.box(MAT["ply"] if False else bpy.data.materials["Door_Birch_Veneer"], 0, width, -t / 2, t / 2, 0.005, h, bevel=0.003)
    blk = bpy.data.materials["Cart_Black"]
    for side in (-1, 1):                                              # lever handles both sides
        p.cyl(blk, (width - 0.07, side * t / 2, 1.02), (width - 0.07, side * (t / 2 + 0.05), 1.02), 0.009, seg=12)
        p.cyl(blk, (width - 0.07, side * (t / 2 + 0.05), 1.02), (width - 0.20, side * (t / 2 + 0.05), 1.02), 0.009, seg=12)
    for z in (0.25, 1.85):                                            # hinges
        p.cyl(bpy.data.materials["Steel_Brushed"], (-0.004, 0, z), (-0.004, 0, z + 0.10), 0.008, seg=10)
    base = math.atan2(opening_dir[1], opening_dir[0])
    root = p.emit(name, col, Vector((hinge[0], hinge[1], 0)), base + math.radians(angle_deg))
    return root


def door_in_wall(col, name, along, wall_c, wall_t, a0, a1, swing, hinge_end, angle=80.0, H=2.12, leaf=0.90):
    """Standard Icelandic interior door (90 cm leaf, 2.1 m) set properly into a colleague's full-height opening:
    the rough opening a0..a1 is narrowed to leaf + frame with wall infill (centred), the wall is closed above the
    frame head up to the slab, white painted frame + casings both faces, birch-veneer leaf drawn open by `angle`.
    along = 'y' (wall runs along y at x = wall_c) or 'x' (runs along x at y = wall_c); swing = +1/-1 = side of the
    wall the leaf opens into (along the wall normal); hinge_end = 0 (hinge at the a0 jamb) or 1 (a1 jamb)."""
    JW, CW, CT = 0.045, 0.07, 0.012                                   # jamb, casing width, casing thickness
    W_o = leaf + 2 * JW + 0.006
    c = (a0 + a1) / 2
    o0, o1 = (c - W_o / 2, c + W_o / 2) if a1 - a0 > W_o + 0.005 else (a0, a1)
    n0, n1 = wall_c - wall_t / 2, wall_c + wall_t / 2

    def bx(p, m, A0, A1, N0, N1, z0, z1):
        if along == "y":
            p.box(m, N0, N1, A0, A1, z0, z1)
        else:
            p.box(m, A0, A1, N0, N1, z0, z1)

    wall = bpy.data.materials["Paint_White"]
    trim = bpy.data.materials["Paint_White_Gloss"]
    p = Part()
    if o0 > a0 + 0.001:
        bx(p, wall, a0, o0, n0, n1, 0.0, SOFFIT)
    if o1 < a1 - 0.001:
        bx(p, wall, o1, a1, n0, n1, 0.0, SOFFIT)
    bx(p, wall, o0, o1, n0, n1, H, SOFFIT)                              # wall above the door, up to the slab
    bx(p, trim, o0, o0 + JW, n0 - 0.005, n1 + 0.005, 0.0, H)           # jambs + head
    bx(p, trim, o1 - JW, o1, n0 - 0.005, n1 + 0.005, 0.0, H)
    bx(p, trim, o0, o1, n0 - 0.005, n1 + 0.005, H - JW, H)
    for N0, N1 in ((n0 - CT, n0), (n1, n1 + CT)):                      # casings on both faces
        bx(p, trim, o0 - CW + JW, o0 + JW, N0, N1, 0.0, H + CW - JW)
        bx(p, trim, o1 - JW, o1 + CW - JW, N0, N1, 0.0, H + CW - JW)
        bx(p, trim, o0 - CW + JW, o1 + CW - JW, N0, N1, H - JW, H + CW - JW)
    p.emit(f"{name}_Frame", col, Vector((0, 0, 0)))
    ha = o0 + JW + 0.003 if hinge_end == 0 else o1 - JW - 0.003
    hn = wall_c + swing * (wall_t / 2 - 0.025)
    d0 = (1.0 if hinge_end == 0 else -1.0)                            # closed leaf runs from the hinge along +-a
    if along == "y":
        hinge, dvec, nvec = (hn, ha), (0.0, d0), (float(swing), 0.0)
    else:
        hinge, dvec, nvec = (ha, hn), (d0, 0.0), (0.0, float(swing))
    sgn = 1.0 if dvec[0] * nvec[1] - dvec[1] * nvec[0] > 0 else -1.0
    door(col, name, hinge, W_o - 2 * JW - 0.006, dvec, sgn * angle, h=H - JW - 0.006)
    return o0, o1


def wc(col, M):
    x0, x1, y0, y1 = WC["x0"], WC["x1"], WC["y0"], WC["y1"]
    d0, d1 = WC["door"]
    T, TH = 0.008, 1.20                                                # tile thickness, tiled height
    # floor tiles
    p = Part()
    p.box(M["floor_tile"], x0, x1, y0, y1, 0.0, 0.006)
    p.emit("WC_FloorTiles", col, Vector((0, 0, 0)))
    # wall tiles (to 1.2 m), split round the door
    p = Part()
    p.box(M["wall_tile_x"], x0, x0 + T, y0, y1, 0.006, TH)                          # CNC-side wall
    p.box(M["wall_tile_x"], x1 - T, x1, y0, d0, 0.006, TH)                          # hallway wall, both sides of door
    p.box(M["wall_tile_x"], x1 - T, x1, d1, y1, 0.006, TH)
    p.box(M["wall_tile_y"], x0, x1, y0, y0 + T, 0.006, TH)                          # partition to the CNC room
    p.box(M["wall_tile_y"], x0, x1, y1 - T, y1, 0.006, TH)                          # end wall
    # cistern box (concealed frame), full width, tiled, with a tiled ledge
    bx0 = y1 - 0.20
    p.box(M["wall_tile_y"], x0 + T, x1 - T, bx0, y1 - T, 0.006, 1.12)
    p.emit("WC_Tiles", col, Vector((0, 0, 0)))
    p = Part()
    p.box(M["white"], x0 + T, x1 - T, bx0 - 0.01, y1 - T, 1.12, 1.135, bevel=0.003)   # ledge cap
    cx = (x0 + x1) / 2
    p.box(M["white"], cx - 0.12, cx + 0.12, bx0 - 0.012, bx0, 0.92, 1.085, bevel=0.003)    # flush plate
    for dx in (-0.055, 0.055):
        p.box(M["chrome"], cx + dx - 0.045, cx + dx + 0.045, bx0 - 0.016, bx0 - 0.011, 0.95, 1.055, bevel=0.002)
    p.emit("WC_FlushPlate", col, Vector((0, 0, 0)))
    # wall-hung toilet: oval bowl (projection 0.53, width 0.36) + seat + lid, top at 0.42
    p = Part()
    bm = p.bm(M["ceramic"])
    for z0, z1, sx, sy in ((0.24, 0.30, 0.15, 0.21), (0.30, 0.38, 0.175, 0.255), (0.38, 0.40, 0.18, 0.265)):
        bmesh.ops.create_cone(bm, cap_ends=True, segments=40, radius1=1.0, radius2=1.0, depth=z1 - z0,
                              matrix=Matrix.Translation((cx, bx0 - 0.265, (z0 + z1) / 2)) @ Matrix.Diagonal((sx, sy, 1, 1)))
    p.box(M["ceramic"], cx - 0.17, cx + 0.17, bx0 - 0.20, bx0, 0.26, 0.40, bevel=0.03)      # back of the bowl to the wall
    bm = p.bm(M["white"])
    bmesh.ops.create_cone(bm, cap_ends=True, segments=40, radius1=1.0, radius2=1.0, depth=0.02,
                          matrix=Matrix.Translation((cx, bx0 - 0.27, 0.41)) @ Matrix.Diagonal((0.18, 0.255, 1, 1)))
    lid = Matrix.Translation((cx, bx0 - 0.05, 0.42)) @ Matrix.Rotation(math.radians(-100), 4, "X") \
        @ Matrix.Translation((0, -0.22, 0.01)) @ Matrix.Diagonal((0.175, 0.24, 1, 1))     # lid up, leaning on the box
    bmesh.ops.create_cone(bm, cap_ends=True, segments=40, radius1=1.0, radius2=1.0, depth=0.018, matrix=lid)
    p.emit("WC_Toilet", col, Vector((0, 0, 0)))
    # basin on the CNC-side wall, facing +x, opposite the door; tap, mirror, soap
    by = (d0 + d1) / 2
    p = Part()
    p.box(M["ceramic"], x0 + T, x0 + 0.34, by - 0.225, by + 0.225, 0.70, 0.85, bevel=0.03)
    p.box(M["white"], x0 + 0.06, x0 + 0.29, by - 0.17, by + 0.17, 0.846, 0.852)            # bowl shadow line
    p.cyl(M["chrome"], (x0 + 0.06, by, 0.85), (x0 + 0.06, by, 1.02), 0.014, seg=16)        # tap
    p.cyl(M["chrome"], (x0 + 0.06, by, 1.01), (x0 + 0.17, by, 0.98), 0.010, seg=12)
    p.cyl(M["chrome"], (x0 + 0.03, by, 0.98), (x0 + 0.03, by, 1.05), 0.006, seg=8)         # lever
    p.cyl(M["chrome"], (x0 + 0.08, by, 0.55), (x0 + 0.08, by, 0.70), 0.016, seg=12)        # trap
    p.box(M["mirror"], x0 + T, x0 + T + 0.006, by - 0.23, by + 0.23, 1.10, 1.80)
    p.box(M["white"], x0 + T, x0 + T + 0.05, by + 0.26, by + 0.34, 1.05, 1.25, bevel=0.008)   # soap dispenser
    p.emit("WC_Basin", col, Vector((0, 0, 0)))
    # paper towels + bin on the partition (facing +y), roll holder + brush by the toilet, fan grille high on the end
    p = Part()
    p.box(M["white"], x0 + 0.30, x0 + 0.58, y0 + T, y0 + T + 0.11, 1.15, 1.55, bevel=0.01)
    p.box(M["black"], x0 + 0.33, x0 + 0.55, y0 + T + 0.105, y0 + T + 0.112, 1.16, 1.19)
    p.cyl(M["steel"], (x0 + 0.44, y0 + 0.22, 0.0), (x0 + 0.44, y0 + 0.22, 0.42), 0.13, seg=28)   # bin
    p.cyl(M["chrome"], (x0 + T, bx0 - 0.30, 0.75), (x0 + 0.13, bx0 - 0.30, 0.75), 0.006, seg=8)  # roll holder
    p.cyl(M["white"], (x0 + 0.03, bx0 - 0.30, 0.75), (x0 + 0.13, bx0 - 0.30, 0.75), 0.055, seg=24)
    p.cyl(M["white"], (x0 + 0.12, bx0 - 0.08, 0.0), (x0 + 0.12, bx0 - 0.08, 0.36), 0.05, seg=20)   # brush holder
    p.cyl(M["black"], (x0 + 0.12, bx0 - 0.08, 0.36), (x0 + 0.12, bx0 - 0.08, 0.50), 0.008, seg=8)
    p.cyl(M["white"], (x1 - 0.30, y1 - 0.002, 2.55), (x1 - 0.30, y1 - 0.035, 2.55), 0.09, seg=32)   # fan
    for k in range(5):
        p.box(M["black"], x1 - 0.37, x1 - 0.23, y1 - 0.036, y1 - 0.034, 2.505 + k * 0.022, 2.512 + k * 0.022)
    p.emit("WC_Accessories", col, Vector((0, 0, 0)))
    # standard 90 cm door in a frame, wall closed above it (the colleague's opening ran to the slab); hinged at the
    # CNC end, opens inward, drawn ajar so the room reads from the hallway
    door_in_wall(col, "WC_Door", "y", 25.822, 0.168, d0, d1, -1, 0, angle=62)
    plaque(col, "WC", "WC", (HALL_X[0] + 0.012, d1 + 0.20, 1.55), (1, 0))


def plaque(col, name, text, pos, normal, w=0.18, h=0.18, size=0.08):
    """Door sign: birch backing + white face flat on the wall at `pos` (point on the wall surface), facing `normal`
    (unit 2D, out of the wall), black Roboto Bold text; multi-line text with \\n."""
    n = Vector((normal[0], normal[1], 0)).normalized()
    rot = math.atan2(n.y, n.x) + math.pi / 2                       # maps local -y (front) onto the normal
    p = Part()
    p.box(MAT["ply"], -w / 2 - 0.01, w / 2 + 0.01, -0.010, 0.0, -h / 2 - 0.01, h / 2 + 0.01, bevel=0.003)
    p.box(bpy.data.materials["Paint_White_Gloss"], -w / 2, w / 2, -0.014, -0.010, -h / 2, h / 2, bevel=0.003)
    p.emit(f"Plaque_{name}_Board", col, Vector(pos), rot)
    cu = bpy.data.curves.get(f"Plaque_{name}") or bpy.data.curves.new(f"Plaque_{name}", "FONT")
    cu.body, cu.size, cu.align_x, cu.align_y = text, size, "CENTER", "CENTER"
    cu.space_line = 1.1
    cu.font = bpy.data.fonts.load(bpy.path.abspath("//refs/branding/fonts/Roboto-Bold.ttf"), check_existing=True)
    cu.extrude = 0.0006
    cu.materials.clear()
    cu.materials.append(bpy.data.materials["Cart_Black"])
    o = bpy.data.objects.new(f"Plaque_{name}", cu)
    col.objects.link(o)
    o.location = Vector(pos) + n * 0.0150
    o.rotation_euler = (math.pi / 2, 0, rot)


# ------------------------------------------------------------------ staff room
def kitchenette(col, M):
    """Along the hallway wall (x 27.73, faces +x): dishwasher, sink, drawers from the WNW corner (coffee machine +
    microwave on the worktop), fridge-freezer at the open end by the entry bay, wall cupboards, tiled splashback.
    Keep >= 1.0 m free in front of the whole run (doors, dishwasher, fridge must open)."""
    X, Y0 = ST["x0"], ST["y0"]
    D, H = 0.60, 0.90
    r0, r1 = Y0 + 0.01, Y0 + 0.01 + 1.80                             # base run from the WNW corner: DW, sink, drawers
    fy0, fy1 = r1 + 0.01, r1 + 0.61                                   # fridge at the open end: door swings into the
                                                                      # entry zone (nothing in front of it)
    p = Part()
    # fridge-freezer, stainless, 1.86 m, two doors, recessed handles
    p.box(M["steel"], X + 0.02, X + 0.67, fy0, fy1, 0.0, 1.86, bevel=0.008)
    p.box(M["black"], X + 0.67, X + 0.672, fy0 + 0.02, fy1 - 0.02, 1.15, 1.152)       # door split
    for z0, z1 in ((1.30, 1.60), (0.80, 1.05)):
        p.box(M["black"], X + 0.672, X + 0.69, fy0 + 0.04, fy0 + 0.06, z0, z1)           # handles (hinge at fy1)
    # carcasses on a black plinth
    p.box(M["black"], X + 0.06, X + D - 0.06, r0, r1, 0.0, 0.10)
    ply = MAT["ply"]
    p.box(ply, X + 0.0, X + D - 0.02, r0, r1, 0.10, H - 0.03)
    for k in range(3):                                                # fronts (dishwasher front is stainless)
        a, b = r0 + k * 0.60 + 0.002, r0 + (k + 1) * 0.60 - 0.002
        if k == 0:
            p.box(M["steel"], X + D - 0.02, X + D, a, b, 0.10, H - 0.03, bevel=0.002)
            p.box(M["black"], X + D, X + D + 0.002, a + 0.05, b - 0.05, H - 0.10, H - 0.06)   # control strip
        elif k == 1:
            p.box(ply, X + D - 0.02, X + D, a, b, 0.10, H - 0.03, bevel=0.002)
        else:
            for z0, z1 in ((0.10, 0.38), (0.385, 0.62), (0.625, H - 0.03)):
                p.box(ply, X + D - 0.02, X + D, a, b, z0 + 0.002, z1 - 0.002, bevel=0.002)
                p.box(M["black"], X + D, X + D + 0.02, (a + b) / 2 - 0.12, (a + b) / 2 + 0.12, z1 - 0.05, z1 - 0.035)
        if k == 1:
            p.box(M["black"], X + D, X + D + 0.02, b - 0.06, b - 0.045, H - 0.25, H - 0.10)
    # worktop with the sink cut-out, stainless sink, tap
    sy0, sy1 = r0 + 0.60 + 0.08, r0 + 1.20 - 0.08
    sx0, sx1 = X + 0.12, X + 0.52
    wt = M["worktop"]
    p.box(wt, X, X + 0.62, r0, sy0, H - 0.03, H)
    p.box(wt, X, X + 0.62, sy1, r1 + 0.01, H - 0.03, H)
    p.box(wt, X, sx0, sy0, sy1, H - 0.03, H)
    p.box(wt, sx1, X + 0.62, sy0, sy1, H - 0.03, H)
    st = M["steel"]
    p.box(st, sx0, sx1, sy0, sy1, H - 0.20, H - 0.19)
    p.box(st, sx0, sx0 + 0.005, sy0, sy1, H - 0.20, H)
    p.box(st, sx1 - 0.005, sx1, sy0, sy1, H - 0.20, H)
    p.box(st, sx0, sx1, sy0, sy0 + 0.005, H - 0.20, H)
    p.box(st, sx0, sx1, sy1 - 0.005, sy1, H - 0.20, H)
    p.box(st, sx0 - 0.015, sx1 + 0.015, sy0 - 0.015, sy1 + 0.015, H, H + 0.002)       # rim (drawn as a frame)
    ty = (sy0 + sy1) / 2
    p.cyl(M["chrome"], (X + 0.06, ty, H), (X + 0.06, ty, H + 0.32), 0.016, seg=16)
    p.cyl(M["chrome"], (X + 0.06, ty, H + 0.32), (X + 0.24, ty, H + 0.30), 0.011, seg=12)
    p.cyl(M["chrome"], (X + 0.24, ty, H + 0.30), (X + 0.24, ty, H + 0.25), 0.011, seg=12)
    # tiled splashback between worktop and wall cupboards
    p.box(M["wall_tile_x"], X, X + 0.008, r0, r1, H, 1.45)
    # wall cupboards (0.35 deep) over the run + one over the fridge
    p.box(ply, X, X + 0.33, r0, r1, 1.45, 2.15)
    for k in range(3):
        a, b = r0 + k * 0.60 + 0.002, r0 + (k + 1) * 0.60 - 0.002
        p.box(ply, X + 0.33, X + 0.35, a, b, 1.452, 2.148, bevel=0.002)
        p.box(M["black"], X + 0.35, X + 0.365, b - 0.05 if k % 2 else a + 0.035, (b - 0.035) if k % 2 else a + 0.05, 1.47, 1.62)
    p.box(ply, X, X + 0.60, fy0, fy1, 1.92, 2.15)
    p.box(ply, X + 0.60, X + 0.62, fy0 + 0.002, fy1 - 0.002, 1.922, 2.148, bevel=0.002)
    # under-cupboard LED strip
    p.box(bpy.data.materials["Fixture_Opal"], X + 0.25, X + 0.31, r0 + 0.02, r1 - 0.02, 1.445, 1.45)
    p.emit("Staff_Kitchen", col, Vector((0, 0, 0)))
    # microwave + coffee machine on the worktop (drawer end), mugs
    p = Part()
    my0 = r1 - 0.52
    p.box(M["black"], X + 0.06, X + 0.42, my0, my0 + 0.48, H, H + 0.28, bevel=0.01)                # microwave
    p.box(M["blackglass"], X + 0.42, X + 0.425, my0 + 0.03, my0 + 0.34, H + 0.03, H + 0.25)
    p.box(M["alu"], X + 0.42, X + 0.426, my0 + 0.37, my0 + 0.45, H + 0.04, H + 0.24)
    cy0 = r0 + 0.08
    p.box(M["black"], X + 0.08, X + 0.46, cy0, cy0 + 0.25, H, H + 0.37, bevel=0.015)               # bean-to-cup
    p.box(M["alu"], X + 0.46, X + 0.47, cy0 + 0.03, cy0 + 0.22, H + 0.20, H + 0.33)
    p.box(M["blackglass"], X + 0.47, X + 0.472, cy0 + 0.07, cy0 + 0.18, H + 0.25, H + 0.31)
    p.box(M["alu"], X + 0.38, X + 0.46, cy0 + 0.08, cy0 + 0.17, H + 0.13, H + 0.16)                  # spout
    p.box(M["steel"], X + 0.36, X + 0.47, cy0 + 0.04, cy0 + 0.21, H, H + 0.015)                      # drip tray
    p.emit("Staff_Appliances", col, Vector((0, 0, 0)))
    p = Part()
    for i, (dx, dy) in enumerate(((0.42, 0.06), (0.30, 0.42), (0.36, 0.52))):
        p.cyl(M["mugs"][i], (X + dx, r0 + 0.60 + dy, H), (X + dx, r0 + 0.60 + dy, H + 0.095), 0.04, seg=24)
    p.emit("Staff_Mugs", col, Vector((0, 0, 0)))


def glostad(M):
    """IKEA GLOSTAD 2-seat sofa, Knisa dark grey: 121 x 78 x 68, seat 41 (seat width 114, depth 54), armrests 3.5 cm
    thick and 57 high, 23 cm free under, thin black steel legs angled slightly outward, two soft back cushions."""
    W, D = 1.21, 0.78
    f, blk = M["sofa"], M["black"]
    p = Part()
    p.box(f, 0.035, W - 0.035, 0.0, D - 0.06, 0.23, 0.41, bevel=0.04)                       # seat block
    p.box(f, 0.035, W - 0.035, D - 0.10, D, 0.23, 0.50, bevel=0.03)                         # low back frame
    for x0 in (0.0, W - 0.035):
        p.box(f, x0, x0 + 0.035, 0.0, D, 0.23, 0.57, bevel=0.015)                           # thin padded arms
    for i in range(2):
        cx = 0.035 + (i + 0.5) * (W - 0.07) / 2
        mtx = Matrix.Translation((cx, D - 0.17, 0.62)) @ Matrix.Rotation(math.radians(-12), 4, "X") \
            @ Matrix.Diagonal(((W - 0.07) / 2 - 0.015, 0.16, 0.40, 1))
        bmesh.ops.create_cube(p.bm(f), size=1.0, matrix=mtx)
    for x, sx in ((0.06, -1), (W - 0.06, 1)):
        for y, sy in ((0.06, -1), (D - 0.06, 1)):
            p.cyl(blk, (x, y, 0.235), (x + 0.025 * sx, y + 0.02 * sy, 0.0), 0.011, seg=12)
    return p, W, D


def poang(M):
    """IKEA POÄNG armchair, birch veneer / Kelinge dark yellow: 68 x 82 x 100, seat 42. Bent-laminate birch frame: a
    floor runner that curls up at the front into the cantilever under the seat, and an arm that rolls over at the
    front, runs back and rises into the back frame; one long cushion (seat + back + headrest)."""
    W = 0.68
    p = Part()
    ply = MAT["ply"]
    base = [(0.74, 0.03), (0.70, 0.013), (0.12, 0.013), (0.05, 0.03), (0.03, 0.08), (0.07, 0.14), (0.30, 0.26),
            (0.50, 0.35)]
    arm = [(0.46, 0.37), (0.14, 0.40), (0.05, 0.44), (0.04, 0.51), (0.09, 0.56), (0.38, 0.58), (0.56, 0.62),
           (0.66, 0.74), (0.80, 0.99)]
    for x in (0.022, W - 0.022):
        strip(p, ply, base, x)
        strip(p, ply, arm, x)
    for y, z in ((0.50, 0.35), (0.79, 0.97), (0.70, 0.80)):            # cross bars
        p.box(ply, 0.02, W - 0.02, y - 0.02, y + 0.02, z - 0.015, z + 0.015)
    c = M["poang"]
    seat = Matrix.Translation((W / 2, 0.30, 0.42)) @ Matrix.Rotation(math.radians(-8), 4, "X") \
        @ Matrix.Diagonal((0.56, 0.50, 0.08, 1))
    back = Matrix.Translation((W / 2, 0.61, 0.71)) @ Matrix.Rotation(math.radians(-23), 4, "X") \
        @ Matrix.Diagonal((0.54, 0.08, 0.56, 1))                      # leans back along the frame
    head = Matrix.Translation((W / 2, 0.715, 0.95)) @ Matrix.Rotation(math.radians(-23), 4, "X") \
        @ Matrix.Diagonal((0.52, 0.10, 0.15, 1))
    for mtx in (seat, back, head):
        bmesh.ops.create_cube(p.bm(c), size=1.0, matrix=mtx)
    return p, W, 0.82


def staff_room(col, M):
    X0, X1, Y0, Y1 = ST["x0"], ST["x1"], ST["y0"], ST["y1"]
    # the colleague's laser-room/staff-room wall (y 19.984-20.14) stopped at x 32.15, leaving a full-height 37 cm
    # slot open to the glass: close it (user) with a wall infill up to the glazing, black seal strip at the glass
    p = Part()
    p.box(bpy.data.materials["Paint_White"], 32.14, 32.515, 19.984, 20.14, 0.0, SOFFIT)
    p.box(M["black"], 32.515, 32.522, 19.984, 20.14, 0.0, SOFFIT)
    p.emit("Staff_LaserWall_Infill", col, Vector((0, 0, 0)))
    kitchenette(col, M)
    # meeting table for 4 in the middle, its end against the WNW wall, a chair pair each side; the kitchen keeps
    # >= 1 m in front, the route bay -> window runs along the laser wall (y 18.87-19.98, ~1.1 m)
    TX0, TX1, TY0, TY1, TH = 29.80, 30.60, Y0 + 0.02, Y0 + 1.22, 0.74
    t = Part()
    for x in (TX0 + 0.03, TX1 - 0.07):
        for y in (TY0 + 0.03, TY1 - 0.07):
            t.profile(0.04, "z", x, y, 0.035, TH - 0.06)
            lib["foot"](t, x + 0.02, y + 0.02)
    for x in (TX0 + 0.03, TX1 - 0.07):
        t.profile(0.04, "y", x, TY0 + 0.07, TH - 0.065, TY1 - TY0 - 0.14)
    for y in (TY0 + 0.03, TY1 - 0.07):
        t.profile(0.04, "x", TX0 + 0.07, y, TH - 0.065, TX1 - TX0 - 0.14)
    t.box(MAT["ply"], TX0, TX1, TY0, TY1, TH - 0.025, TH, bevel=0.003)
    sk = bpy.data.materials.get("Sketchbook") or mat("Sketchbook", "#F2F0EA", 0.8)
    t.box(sk, TX0 + 0.25, TX0 + 0.55, TY0 + 0.40, TY0 + 0.62, TH, TH + 0.008)
    t.cyl(M["mugs"][0], (TX0 + 0.20, TY1 - 0.25, TH), (TX0 + 0.20, TY1 - 0.25, TH + 0.095), 0.04, seg=24)
    t.cyl(M["mugs"][1], (TX1 - 0.18, TY0 + 0.25, TH), (TX1 - 0.18, TY0 + 0.25, TH + 0.095), 0.04, seg=24)
    t.emit("Staff_MeetingTable", col, Vector((0, 0, 0)))
    cw = 0.44
    for k, (cx, cy, facing) in enumerate(((TX0 - 0.19, TY0 + 0.32, "+x"), (TX0 - 0.19, TY1 - 0.30, "+x"),
                                          (TX1 + 0.19, TY0 + 0.32, "-x"), (TX1 + 0.19, TY1 - 0.30, "-x"))):
        put(tex["chair"](), f"Staff_Chair_{k + 1}", col, cx, cy, cw, cw, facing)
    # ranting corner in the window end: GLOSTAD on the WNW wall (side to the glass), POÄNG facing it from the
    # laser-wall corner, small round table on the open side
    p, W, D = glostad(M)
    sx1 = X1 - 0.04
    root = put(p, "Staff_Sofa_GLOSTAD", col, sx1 - W / 2, Y0 + 0.01 + D / 2, W, D, "+y")
    soften(root, ("Knisa_DarkGrey",), 0.015)
    p, W2, D2 = poang(M)
    ang = math.radians(20)                                            # front faces -y, turned a little to the room
    c = Vector((sx1 - W / 2 + 0.05, Y1 - 0.51, 0))
    loc = c + Matrix.Rotation(ang, 4, "Z") @ Vector((-W2 / 2, -D2 / 2, 0))
    root = p.emit("Staff_Armchair_POANG", col, loc, ang)
    soften(root, ("Kelinge_DarkYellow",), 0.015)
    t = Part()
    tx, ty = sx1 - W - 0.035, Y0 + 1.375
    t.cyl(MAT["ply"], (tx, ty, 0.43), (tx, ty, 0.45), 0.20, seg=40)
    t.cyl(M["black"], (tx, ty, 0.0), (tx, ty, 0.43), 0.02, seg=12)
    t.cyl(M["black"], (tx, ty, 0.0), (tx, ty, 0.012), 0.16, seg=32)
    t.cyl(M["mugs"][2], (tx + 0.06, ty - 0.04, 0.45), (tx + 0.06, ty - 0.04, 0.545), 0.04, seg=24)
    t.emit("Staff_SideTable", col, Vector((0, 0, 0)))
    # whiteboard on the laser-room wall (faces -y), seen from the sofa and the table
    p = Part()
    wx0, wx1 = 29.55, 30.95
    p.box(M["board"], wx0, wx1, Y1 - 0.02, Y1, 0.95, 1.90)
    for z0, z1 in ((0.93, 0.95), (1.90, 1.92)):
        p.box(M["alu"], wx0 - 0.02, wx1 + 0.02, Y1 - 0.025, Y1, z0, z1)
    for x0, x1 in ((wx0 - 0.02, wx0), (wx1, wx1 + 0.02)):
        p.box(M["alu"], x0, x1, Y1 - 0.025, Y1, 0.93, 1.92)
    p.box(M["alu"], wx0 + 0.2, wx1 - 0.2, Y1 - 0.08, Y1, 0.90, 0.93)                 # pen tray
    for i, h in enumerate(("#E03A3F", "#1245DE", "#009967", "#1F1F20")):
        mm = mat(f"Marker_{h[1:]}", h, 0.4)
        p.cyl(mm, (wx0 + 0.30 + i * 0.05, Y1 - 0.05, 0.94), (wx0 + 0.42 + i * 0.05, Y1 - 0.05, 0.94), 0.009, seg=10)
    for i, (x, z, h) in enumerate(((0.15, 1.70, "#F2C200"), (0.27, 1.68, "#E099AB"), (0.15, 1.56, "#F2C200"),
                                   (1.05, 1.72, "#FFA13D"), (1.17, 1.72, "#009967"))):
        mm = mat(f"Note_{h[1:]}", h, 0.7)
        p.box(mm, wx0 + x, wx0 + x + 0.076, Y1 - 0.0215, Y1 - 0.02, z, z + 0.076)
    # sketched "rant" diagram: a few dark strokes
    ink = mat("Marker_Ink", "#20242A", 0.5)
    for (xa, za, xb, zb) in ((0.45, 1.70, 0.85, 1.70), (0.45, 1.70, 0.45, 1.35), (0.45, 1.35, 0.85, 1.35),
                             (0.85, 1.70, 0.85, 1.35), (0.55, 1.58, 0.78, 1.58), (0.55, 1.48, 0.72, 1.48),
                             (0.25, 1.25, 1.20, 1.25), (0.95, 1.55, 1.15, 1.40)):
        a, b = Vector((wx0 + xa, Y1 - 0.0205, za)), Vector((wx0 + xb, Y1 - 0.0205, zb))
        p.cyl(ink, a, b, 0.0025, seg=6)
    p.emit("Staff_Whiteboard", col, Vector((0, 0, 0)))
    # coat hooks + hat shelf on the laser partition in the entry bay (faces -x), a few coats and a tote
    p = Part()
    HX, hy0, hy1 = ST["bay_x1"], 20.25, 21.45
    p.box(MAT["ply"], HX - 0.02, HX, hy0, hy1, 1.62, 1.74, bevel=0.003)
    p.box(MAT["ply"], HX - 0.28, HX, hy0, hy1, 1.88, 1.90, bevel=0.002)
    for y in (hy0 + 0.1, hy1 - 0.1):
        p.box(M["black"], HX - 0.26, HX - 0.02, y - 0.01, y + 0.01, 1.84, 1.88)
    n = 7
    for i in range(n):
        y = hy0 + 0.1 + i * (hy1 - hy0 - 0.2) / (n - 1)
        p.cyl(M["black"], (HX - 0.02, y, 1.68), (HX - 0.07, y, 1.70), 0.007, seg=8)
        p.cyl(M["black"], (HX - 0.07, y, 1.70), (HX - 0.075, y, 1.74), 0.007, seg=8)
    p.emit("Staff_CoatHooks", col, Vector((0, 0, 0)))
    for i, k in enumerate((0, 2, 4)):
        y = hy0 + 0.1 + k * (hy1 - hy0 - 0.2) / (n - 1)
        p = Part()
        m = M["coats"][i]
        bm = p.bm(m)
        for mtx in (Matrix.Translation((0, 0, -0.48)) @ Matrix.Diagonal((0.12, 0.33, 0.78, 1)),          # body
                    Matrix.Translation((0, 0, -0.10)) @ Matrix.Diagonal((0.13, 0.36, 0.12, 1)),          # shoulders
                    Matrix.Translation((0, -0.15, -0.40)) @ Matrix.Diagonal((0.10, 0.07, 0.60, 1)),      # sleeves
                    Matrix.Translation((0, 0.15, -0.40)) @ Matrix.Diagonal((0.10, 0.07, 0.60, 1)),
                    Matrix.Translation((0.01, 0, -0.02)) @ Matrix.Diagonal((0.10, 0.20, 0.10, 1))):      # collar/hood
            bmesh.ops.create_cube(bm, size=1.0, matrix=mtx)
        root = p.emit(f"Staff_Coat_{i + 1}", col, Vector((HX - 0.11, y, 1.73)), 0)
        soften(root, (m.name,), 0.03)
    p = Part()                                                        # canvas tote on the last hook
    y = hy0 + 0.1 + 6 * (hy1 - hy0 - 0.2) / (n - 1)
    tote = mat("Canvas_Natural", "#D8CDB4", 0.9)
    p.box(tote, HX - 0.10, HX - 0.04, y - 0.18, y + 0.18, 1.12, 1.52, bevel=0.01)
    p.cyl(tote, (HX - 0.07, y - 0.10, 1.52), (HX - 0.07, y, 1.72), 0.008, seg=6)
    p.cyl(tote, (HX - 0.07, y + 0.10, 1.52), (HX - 0.07, y, 1.72), 0.008, seg=6)
    p.emit("Staff_Tote", col, Vector((0, 0, 0)))
    # door from the hallway: hinged at the far (y 21.35) jamb, opens into the bay, drawn open
    d0, d1 = ST["door"]
    door_in_wall(col, "Staff_Door", "y", 27.62, 0.22, d0, d1, +1, 1, angle=80)
    plaque(col, "Kaffistofa", "KAFFISTOFA\nstarfsfólk", (HALL_X[1], d0 - 0.24, 1.55), (-1, 0), w=0.30, h=0.14, size=0.042)


def lights(col):
    """Same black linear LED fixtures as the lab (build_lighting.py), 2.95 m bottom: two in the staff room (along x),
    one in the WC, two in the hallway."""
    body = bpy.data.materials["Fixture_Black"]
    opal = bpy.data.materials["Fixture_Opal"]
    cable = bpy.data.materials["Cable_Black"]
    B, FW, FH = 2.95, 0.06, 0.06
    ld = bpy.data.lights.get("Staff_LED") or bpy.data.lights.new("Staff_LED", "AREA")
    ld.shape, ld.size, ld.size_y = "RECTANGLE", 1.40, FW - 0.01
    ld.energy, ld.color = 42.0, (1.0, 0.95, 0.88)
    ld.spread = math.radians(110)
    ldy = bpy.data.lights.get("Staff_LED_Y") or bpy.data.lights.new("Staff_LED_Y", "AREA")
    ldy.shape, ldy.size, ldy.size_y = "RECTANGLE", FW - 0.01, 1.10
    ldy.energy, ldy.color = 30.0, (1.0, 0.95, 0.88)
    ldy.spread = math.radians(110)
    fixtures = [((29.05, 18.85), 1.44, "x", ld), ((31.25, 18.85), 1.44, "x", ld),
                ((25.0, 20.55), 1.14, "y", ldy), ((26.70, 16.40), 1.14, "y", ldy), ((26.70, 19.60), 1.14, "y", ldy)]
    for i, ((cx, cy), L, ax, data) in enumerate(fixtures):
        p = Part()
        hx, hy = (L / 2, FW / 2) if ax == "x" else (FW / 2, L / 2)
        p.box(body, cx - hx, cx + hx, cy - hy, cy + hy, B + 0.004, B + FH)
        p.box(opal, cx - hx + 0.004, cx + hx - 0.004, cy - hy + 0.004, cy + hy - 0.004, B, B + 0.004)
        for s in (-1, 1):
            q = Vector((cx + s * (hx - 0.15), cy)) if ax == "x" else Vector((cx, cy + s * (hy - 0.15)))
            p.cyl(cable, (q.x, q.y, B + FH), (q.x, q.y, SOFFIT), 0.0012, seg=6)
            p.cyl(body, (q.x, q.y, SOFFIT - 0.012), (q.x, q.y, SOFFIT), 0.025, seg=16)
        p.emit(f"StaffLED_Fixture_{i + 1}", col, Vector((0, 0, 0)))
        lo = bpy.data.objects.new(f"StaffLED_{i + 1}", data)
        lo.location = (cx, cy, B - 0.002)
        col.objects.link(lo)


def build():
    col = clear_collection("StaffArea")
    M = mats()
    demolish_wc2()
    wc(col, M)
    staff_room(col, M)
    lights(col)
    print("staff area built:", len(col.objects), "objects")


if __name__ == "__main__":
    build()
