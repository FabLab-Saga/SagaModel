"""Demo-piece display by the entrance: the back-wall run past the spine (bays 2-5 of Bank_A2,
x ~27.4-32.4, y 37.73-38.33) shows imaginary Fab Lab projects instead of boxes.
Exec'd from build_bank_lounge.py with `demo_fill(slots, levels, H, depth, loc, rot, col)`.
Curated fill: 1-2 labelled projects per shelf, no kind repeated within a bay, hero pieces at eye level.
Pieces: low-poly 3D-printed busts, a voronoi/geodesic lamp, a stacked-slice acrylic sculpture,
twisted printed vases, a CNC-milled topographic relief, a laser-cut living-hinge box, plywood
gears, a little robot arm, PCB badges, a stack of printed shapes. Above the display: a large wall relief of
3D-printed hexagonal tiles in the brand colours (replaced the neon sign), lit by one ceiling spotlight.
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector, noise

rng = random.Random(77)


def _mats(lib):
    mat, lin = lib["simple_mat"], lib["lin"]
    MAT = lib["MAT"]
    glow = bpy.data.materials.get("Neon_Pink") or bpy.data.materials.new("Neon_Pink")
    glow.use_nodes = True
    nt = glow.node_tree; nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = lin("#FF4FA0"); e.inputs["Strength"].default_value = 12
    o = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], o.inputs["Surface"])
    warm = bpy.data.materials.get("Lamp_WarmGlow") or bpy.data.materials.new("Lamp_WarmGlow")
    warm.use_nodes = True
    nt = warm.node_tree; nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (1.0, 0.72, 0.42, 1); e.inputs["Strength"].default_value = 6
    o = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], o.inputs["Surface"])
    return dict(
        pla=[mat(f"PLA_{n}", h, 0.42) for n, h in (("Red", "#E03A3F"), ("Green", "#009967"), ("Blue", "#1245DE"),
                                                    ("Orange", "#FFA13D"), ("Yellow", "#F2C200"), ("Pink", "#E099AB"),
                                                    ("White", "#EEEEEA"), ("Grey", "#6E7276"))],
        ply=MAT["ply"], acrylic=mat("Acrylic_Smoke", "#9FB7C4", 0.05, coat=0.6),
        pcb=mat("PCB_Green", "#1E6B3A", 0.35), copper=mat("PCB_Copper", "#C88A4B", 0.3, metal=1.0),
        steel=mat("Tool_Steel", "#B9BDC1", 0.25, metal=1.0), black=mat("Tool_Black", "#151515", 0.5),
        neon=glow, warm=warm, mdf=mat("MDF", "#B48C5C", 0.8),
        led=mat("LED_Red_Small", "#FF3B2F", 0.3, emit=1.5),
    )


def plinth(p, m, x, y, z, w=0.16, d=0.16, h=0.04):
    p.box(m["ply"], x - w / 2, x + w / 2, y - d / 2, y + d / 2, z, z + h, bevel=0.002)
    return z + h


def bust(p, m, x, y, z, s, c):
    """Low-poly faceted head + shoulders, like a decimated 3D scan printed in PLA."""
    bm = p.bm(c)
    head = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.5 * s,
                                      matrix=Matrix.Translation((x, y, z + 0.95 * s)) @ Matrix.Diagonal((0.85, 0.95, 1.15, 1)))
    for v in head["verts"]:
        v.co += Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * 0.04 * s
    bmesh.ops.create_cone(bm, cap_ends=True, segments=7, radius1=0.62 * s, radius2=0.28 * s, depth=0.5 * s,
                          matrix=Matrix.Translation((x, y, z + 0.25 * s)))


def geodesic_lamp(p, m, x, y, z, r):
    bm = p.bm(m["pla"][6])
    tmp = bmesh.new()
    bmesh.ops.create_icosphere(tmp, subdivisions=2, radius=r, matrix=Matrix.Translation((x, y, z + r)))
    bmesh.ops.wireframe(tmp, faces=list(tmp.faces), thickness=0.006, use_replace=True)
    me = bpy.data.meshes.new("_tmp"); tmp.to_mesh(me); tmp.free(); bm.from_mesh(me); bpy.data.meshes.remove(me)
    bmesh.ops.create_uvsphere(p.bm(m["warm"]), u_segments=16, v_segments=8, radius=0.03, matrix=Matrix.Translation((x, y, z + r)))


def slice_sculpture(p, m, x, y, z, h):
    """Stacked laser-cut acrylic slices of a blobby form (contour sculpture)."""
    n = 18
    for i in range(n):
        t = i / (n - 1)
        r = 0.04 + 0.07 * math.sin(math.pi * t) * (1 + 0.25 * math.sin(6 * t))
        rx, ry = r * (1 + 0.3 * math.sin(3 * t)), r
        zz = z + t * h
        bmesh.ops.create_cone(p.bm(m["acrylic"]), cap_ends=True, segments=24, radius1=1.0, radius2=1.0, depth=0.004,
                              matrix=Matrix.Translation((x, y, zz)) @ Matrix.Diagonal((rx, ry, 1, 1)))


def twisted_vase(p, m, x, y, z, h, c, sides=6, twist=1.6):
    bm = p.bm(c)
    rings, verts = 24, []
    for i in range(rings + 1):
        t = i / rings
        r = 0.045 + 0.03 * math.sin(math.pi * t * 0.9)
        ring = []
        for k in range(sides):
            a = 2 * math.pi * k / sides + twist * t
            ring.append(bm.verts.new((x + r * math.cos(a), y + r * math.sin(a), z + t * h)))
        verts.append(ring)
    for i in range(rings):
        for k in range(sides):
            bm.faces.new((verts[i][k], verts[i][(k + 1) % sides], verts[i + 1][(k + 1) % sides], verts[i + 1][k]))
    bm.faces.new(list(reversed(verts[0])))


def topo_relief(p, m, x, y, z, w, d):
    """CNC-milled terrain in MDF with stepped contour terraces."""
    bm = p.bm(m["mdf"])
    n = 28
    grid = []
    for i in range(n + 1):
        row = []
        for j in range(n + 1):
            u, v = i / n, j / n
            hgt = 0.01 + 0.05 * max(0.0, noise.noise(Vector((u * 2.2, v * 2.2, 0.3))) * 0.5 + 0.5) ** 2
            hgt = round(hgt / 0.006) * 0.006                       # terraces
            row.append(bm.verts.new((x - w / 2 + u * w, y - d / 2 + v * d, z + hgt)))
        grid.append(row)
    for i in range(n):
        for j in range(n):
            bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    p.box(m["mdf"], x - w / 2, x + w / 2, y - d / 2, y + d / 2, z - 0.012, z + 0.006)


def hinge_box(p, m, x, y, z, w=0.16, d=0.10, h=0.09):
    p.box(m["ply"], x - w / 2, x + w / 2, y - d / 2, y + d / 2, z, z + h, bevel=0.002)
    for k in range(10):                                              # living-hinge kerf lines on the front
        xx = x - w / 2 + 0.02 + k * (w - 0.04) / 9
        p.box(m["black"], xx - 0.0005, xx + 0.0005, y - d / 2 - 0.0005, y - d / 2, z + 0.01, z + h - 0.01)


def gear(p, m, x, y, z, r, teeth, c, t=0.006):
    bm = p.bm(c)
    pts = []
    for k in range(teeth * 2):
        a = math.pi * k / teeth
        rr = r if k % 2 == 0 else r * 0.86
        pts.append((x + rr * math.cos(a), z + rr * math.sin(a)))
    front = [bm.verts.new((px, y, pz)) for px, pz in pts]
    back = [bm.verts.new((px, y + t, pz)) for px, pz in pts]
    bm.faces.new(front); bm.faces.new(list(reversed(back)))
    for k in range(len(pts)):
        bm.faces.new((front[k], front[(k + 1) % len(pts)], back[(k + 1) % len(pts)], back[k]))


def robot_arm(p, m, x, y, z, c):
    p.cyl(m["black"], (x, y, z), (x, y, z + 0.03), 0.06, seg=24)
    p.cyl(c, (x, y, z + 0.03), (x, y, z + 0.07), 0.04, seg=20)
    a = Vector((x, y, z + 0.07)); b = a + Vector((0.05, 0, 0.14)); e = b + Vector((0.10, 0, -0.02))
    for s0, s1, r in ((a, b, 0.018), (b, e, 0.014)):
        p.cyl(c, s0, s1, r, seg=12)
        p.cyl(m["black"], s1 - Vector((0, 0.022, 0)), s1 + Vector((0, 0.022, 0)), r * 1.25, seg=16)
    p.box(m["steel"], e.x, e.x + 0.03, y - 0.012, y + 0.012, e.z - 0.03, e.z)          # gripper


def pcb_badges(p, m, x, y, z):
    for i in range(3):
        cx, cy = x + (i - 1) * 0.07, y + rng.uniform(-0.02, 0.02)
        p.box(m["pcb"], cx - 0.03, cx + 0.03, cy - 0.04, cy + 0.04, z, z + 0.0016)
        p.box(m["copper"], cx - 0.022, cx + 0.022, cy - 0.032, cy + 0.032, z + 0.0016, z + 0.0018)
        p.cyl(m["led"], (cx, cy + 0.02, z + 0.0018), (cx, cy + 0.02, z + 0.004), 0.003, seg=8)


def shape_stack(p, m, x, y, z):
    zz = z
    for i, (kind, s) in enumerate((("cube", 0.07), ("cyl", 0.05), ("cube", 0.045), ("ico", 0.035))):
        c = m["pla"][(i * 3) % 6]
        if kind == "cube":
            p.box(c, x - s / 2, x + s / 2, y - s / 2, y + s / 2, zz, zz + s, bevel=0.004); zz += s
        elif kind == "cyl":
            p.cyl(c, (x, y, zz), (x, y, zz + s), s * 0.6, seg=24); zz += s
        else:
            bmesh.ops.create_icosphere(p.bm(c), subdivisions=1, radius=s, matrix=Matrix.Translation((x, y, zz + s)))


# ---------------------------------------------------------------- larger projects (curated display)
def obox(p, c, ctr, size, rx=0.0, rz=0.0):
    """Oriented box: centre, (sx, sy, sz), tilted rx about X then rz about Z."""
    mtx = Matrix.Translation(ctr) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(rx, 4, "X") @ Matrix.Diagonal((*size, 1))
    bmesh.ops.create_cube(p.bm(c), size=1.0, matrix=mtx)


def cnc_stool(p, m, x, y, z, h=0.34):
    """Opendesk-style CNC-cut birch stool: two slotted side panels, seat, through-tenoned stretcher."""
    for sx in (-0.12, 0.12):
        p.box(m["ply"], x + sx - 0.009, x + sx + 0.009, y - 0.12, y + 0.12, z, z + h - 0.018, bevel=0.002)
        p.box(m["black"], x + sx - 0.0095, x + sx + 0.0095, y - 0.035, y + 0.035, z, z + 0.07)       # foot cut-out
    p.box(m["ply"], x - 0.15, x + 0.15, y - 0.13, y + 0.13, z + h - 0.018, z + h, bevel=0.003)
    p.box(m["ply"], x - 0.14, x + 0.14, y - 0.02, y + 0.02, z + 0.12, z + 0.20, bevel=0.002)


def kerf_lamp(p, m, x, y, z, h=0.36):
    """Kerf-bent plywood lamp: ring of thin birch slats on a disc base, warm bulb inside."""
    p.cyl(m["ply"], (x, y, z), (x, y, z + 0.02), 0.11, seg=40)
    p.cyl(m["black"], (x, y, z + 0.02), (x, y, z + h * 0.55), 0.006, seg=8)
    for k in range(30):
        a = 2 * math.pi * k / 30
        r = 0.11 + 0.025 * math.sin(3 * a)
        cx, cy = x + r * math.cos(a), y + r * math.sin(a)
        obox(p, m["ply"], (cx, cy, z + 0.06 + (h - 0.06) / 2), (0.014, 0.003, h - 0.06), rz=a + math.pi / 2)
    bmesh.ops.create_uvsphere(p.bm(m["warm"]), u_segments=16, v_segments=8, radius=0.028, matrix=Matrix.Translation((x, y, z + h * 0.58)))


def lattice_vase(p, m, x, y, z, h, c):
    """3D-printed lattice vase: lathe profile turned into a wireframe, solid foot."""
    bm = p.bm(c)
    tmp = bmesh.new()
    rings, seg, vs = 12, 14, []
    for i in range(rings + 1):
        t = i / rings
        r = 0.045 + 0.045 * math.sin(math.pi * (0.15 + 0.8 * t)) - 0.02 * t
        vs.append([tmp.verts.new((x + r * math.cos(2 * math.pi * k / seg + 0.22 * i), y + r * math.sin(2 * math.pi * k / seg + 0.22 * i),
                                  z + 0.01 + t * (h - 0.01))) for k in range(seg)])
    for a, b in zip(vs, vs[1:]):
        for k in range(seg):
            tmp.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    bmesh.ops.wireframe(tmp, faces=list(tmp.faces), thickness=0.004, use_replace=True)
    me = bpy.data.meshes.new("_tmp"); tmp.to_mesh(me); tmp.free(); bm.from_mesh(me); bpy.data.meshes.remove(me)
    p.cyl(c, (x, y, z), (x, y, z + 0.012), 0.05, seg=28)


def layered_map(p, m, x, y, z, w=0.42, h=0.30):
    """Laser-cut layered map: terraced island in ply/MDF on blue acrylic sea, framed, leaning on a stand."""
    tilt = math.radians(-12)
    n_x, n_z = 28, 20
    cw, ch = w / n_x, h / n_z
    shades = [m["pla"][2], m["mdf"], m["ply"], m["mdf"], m["ply"]]
    for i in range(n_x):
        for j in range(n_z):
            u, v = i / n_x, j / n_z
            e = noise.noise(Vector((u * 2.4 + 3.1, v * 2.4, 1.7))) * 0.5 + 0.5 - 0.35 * ((u - 0.5) ** 2 + (v - 0.5) ** 2) * 4
            lvl = max(0, min(4, int(e * 6) - 1))
            d = 0.004 + lvl * 0.003
            lz = j * ch + ch / 2 + 0.03
            ly = 0.02 - d / 2
            cz, cy = z + lz * math.cos(tilt) - ly * math.sin(tilt), y + 0.06 + lz * math.sin(tilt) + ly * math.cos(tilt)
            obox(p, shades[lvl], (x - w / 2 + i * cw + cw / 2, cy, cz), (cw, d, ch), rx=tilt)
    fz = h / 2 + 0.03
    obox(p, m["black"], (x, y + 0.06 + fz * math.sin(tilt) + 0.024, z + fz * math.cos(tilt)), (w + 0.03, 0.012, h + 0.03), rx=tilt)
    p.box(m["ply"], x - w / 2, x + w / 2, y + 0.02, y + 0.05, z, z + 0.03, bevel=0.002)             # ledge


def synth(p, m, x, y, z):
    """PCB synth on a tilted acrylic stand: knobs, keys, a jack row."""
    tilt = math.radians(28)
    for sx in (-0.15, 0.15):
        obox(p, m["acrylic"], (x + sx, y + 0.02, z + 0.05), (0.004, 0.16, 0.10))
    cz, cy = z + 0.07, y + 0.02
    obox(p, m["pcb"], (x, cy, cz), (0.30, 0.15, 0.0016), rx=tilt)
    up = Vector((0, -math.sin(tilt), math.cos(tilt)))
    for k in range(6):
        b = Vector((x - 0.12 + k * 0.045, cy + 0.04 * math.cos(tilt), cz + 0.04 * math.sin(tilt)))
        p.cyl(m["black"], tuple(b), tuple(b + up * 0.018), 0.009, seg=16)
    for k in range(13):
        b = Vector((x - 0.13 + k * 0.0215, cy - 0.04 * math.cos(tilt), cz - 0.04 * math.sin(tilt)))
        obox(p, m["pla"][6] if k % 3 else m["black"], tuple(b + up * 0.004), (0.018, 0.05, 0.006), rx=tilt)
    for k in range(4):
        b = Vector((x + 0.06 + k * 0.02, cy + 0.06 * math.cos(tilt), cz + 0.06 * math.sin(tilt)))
        p.cyl(m["steel"], tuple(b), tuple(b + up * 0.008), 0.004, seg=10)


def embroidery(p, m, x, y, z):
    """Embroidery hoop (machine-embroidered patch) in a little ply foot."""
    cz, r = z + 0.16, 0.13
    fab = bpy.data.materials.get("Fabric_Navy") or m["black"]
    bmesh.ops.create_cone(p.bm(m["ply"]), cap_ends=False, segments=48, radius1=r, radius2=r, depth=0.014,
                          matrix=Matrix.Translation((x, y, cz)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    p.cyl(fab, (x, y - 0.001, cz), (x, y + 0.001, cz), r - 0.004, seg=48)
    for k, c in enumerate((m["pla"][3], m["pla"][4], m["pla"][0], m["pla"][5], m["pla"][1])):
        a = 2 * math.pi * k / 5
        p.cyl(c, (x + 0.06 * math.cos(a), y - 0.002, cz + 0.06 * math.sin(a)), (x + 0.06 * math.cos(a), y - 0.0035, cz + 0.06 * math.sin(a)), 0.028, seg=24)
    p.cyl(m["pla"][6], (x, y - 0.002, cz), (x, y - 0.004, cz), 0.03, seg=24)
    p.box(m["ply"], x - 0.06, x + 0.06, y - 0.03, y + 0.03, z, z + 0.035, bevel=0.003)


def automaton(p, m, x, y, z):
    """Wooden automaton: open ply box, cams on a crank shaft, a little bird on push rods."""
    w, d, h = 0.26, 0.16, 0.18
    for sx in (-w / 2, w / 2 - 0.012):
        for sy in (-d / 2, d / 2 - 0.012):
            p.box(m["ply"], x + sx, x + sx + 0.012, y + sy, y + sy + 0.012, z, z + h)
    p.box(m["ply"], x - w / 2, x + w / 2, y - d / 2, y + d / 2, z + h, z + h + 0.012, bevel=0.002)
    p.box(m["ply"], x - w / 2, x + w / 2, y - d / 2, y + d / 2, z, z + 0.012, bevel=0.002)
    p.cyl(m["steel"], (x - w / 2 - 0.03, y, z + 0.07), (x + w / 2, y, z + 0.07), 0.004, seg=10)      # shaft
    p.cyl(m["pla"][0], (x - w / 2 - 0.03, y, z + 0.07), (x - w / 2 - 0.03, y, z + 0.11), 0.006, seg=10)  # crank
    for k, ox in enumerate((-0.06, 0.0, 0.06)):
        gear(p, m, x + ox - 0.003, y - 0.003, z + 0.07, 0.035, 10, m["ply"] if k != 1 else m["pla"][3])
        p.cyl(m["steel"], (x + ox, y, z + 0.10), (x + ox, y, z + h + 0.06 + 0.02 * k), 0.003, seg=8)
    bz = z + h + 0.09
    bmesh.ops.create_uvsphere(p.bm(m["pla"][4]), u_segments=16, v_segments=10, radius=0.035,
                              matrix=Matrix.Translation((x, y, bz)) @ Matrix.Diagonal((1.4, 1, 1, 1)))
    bmesh.ops.create_cone(p.bm(m["pla"][3]), cap_ends=True, segments=8, radius1=0.012, radius2=0.0, depth=0.03,
                          matrix=Matrix.Translation((x + 0.06, y, bz + 0.01)) @ Matrix.Rotation(math.pi / 2, 4, "Y"))
    obox(p, m["pla"][1], (x - 0.01, y, bz + 0.03), (0.05, 0.004, 0.025), rx=0.0, rz=0.0)


def mini_chairs(p, m, x, y, z):
    """Two 1:5 scale chair models (design-class exercise): birch + one printed."""
    for k, (ox, c) in enumerate(((-0.07, m["ply"]), (0.07, m["pla"][1]))):
        cx = x + ox
        for lx in (-0.035, 0.035):
            for ly in (-0.035, 0.035):
                p.box(c, cx + lx - 0.004, cx + lx + 0.004, y + ly - 0.004, y + ly + 0.004, z, z + 0.09)
        p.box(c, cx - 0.042, cx + 0.042, y - 0.042, y + 0.042, z + 0.09, z + 0.098, bevel=0.001)
        p.box(c, cx - 0.042, cx + 0.042, y + 0.034, y + 0.042, z + 0.098, z + 0.17, bevel=0.001)


def swatch_board(p, m, x, y, z):
    """Leaning ply board with a 3x3 grid of material samples (acrylics, veneers, felt, MDF)."""
    tilt = math.radians(-14)
    s, h = 0.28, 0.28
    cz, cy = z + h / 2 * math.cos(tilt), y + 0.05 + h / 2 * math.sin(tilt)
    obox(p, m["ply"], (x, cy, cz), (s, 0.009, h), rx=tilt)
    samples = [m["pla"][0], m["mdf"], m["acrylic"], m["pla"][2], m["ply"], m["pla"][4], m["black"], m["pla"][5], m["pla"][1]]
    for i in range(3):
        for j in range(3):
            lz, ly = (j - 1) * 0.085, -0.008
            obox(p, samples[i * 3 + j], (x + (i - 1) * 0.085, cy + lz * math.sin(tilt) + ly * math.cos(tilt),
                                         cz + lz * math.cos(tilt) - ly * math.sin(tilt)), (0.07, 0.005, 0.07), rx=tilt)


def toy_truck(p, m, x, y, z):
    p.box(m["ply"], x - 0.12, x + 0.12, y - 0.05, y + 0.05, z + 0.03, z + 0.055, bevel=0.002)
    p.box(m["ply"], x + 0.04, x + 0.12, y - 0.05, y + 0.05, z + 0.055, z + 0.13, bevel=0.004)
    p.box(m["pla"][0], x - 0.11, x + 0.03, y - 0.045, y + 0.045, z + 0.055, z + 0.11, bevel=0.003)
    for wx in (-0.08, 0.08):
        for wy in (-0.055, 0.055):
            p.cyl(m["black"], (x + wx, y + wy - 0.01, z + 0.03), (x + wx, y + wy + 0.01, z + 0.03), 0.03, seg=20)


def label(p, m, x, y, z):
    """Little project card on the shelf edge."""
    p.box(m["card"], x - 0.035, x + 0.035, y, y + 0.002, z, z + 0.04)
    for k in range(3):
        p.box(m["black"], x - 0.028, x + 0.028 - k * 0.012, y - 0.0003, y, z + 0.028 - k * 0.009, z + 0.031 - k * 0.009)


# (name, width, height, depth, hero, builder(p, m, x, yc, z))
KINDS = [
    ("map", 0.46, 0.34, 0.14, True, lambda p, m, x, y, z: layered_map(p, m, x, y, z)),
    ("kerf_lamp", 0.28, 0.36, 0.28, True, lambda p, m, x, y, z: kerf_lamp(p, m, x, y, z)),
    ("synth", 0.34, 0.16, 0.20, True, lambda p, m, x, y, z: synth(p, m, x, y, z)),
    ("embroidery", 0.28, 0.30, 0.08, True, lambda p, m, x, y, z: embroidery(p, m, x, y, z)),
    ("automaton", 0.30, 0.33, 0.18, True, lambda p, m, x, y, z: automaton(p, m, x, y, z)),
    ("lattice", 0.16, 0.30, 0.16, True, lambda p, m, x, y, z: lattice_vase(p, m, x, y, z, 0.28, m["pla"][rng.choice((0, 1, 2, 3, 5))])),
    ("bust", 0.20, 0.30, 0.18, True, lambda p, m, x, y, z: bust(p, m, x, y, plinth(p, m, x, y, z), 0.24, m["pla"][6])),
    ("slices", 0.22, 0.32, 0.20, False, lambda p, m, x, y, z: slice_sculpture(p, m, x, y, plinth(p, m, x, y, z, 0.2, 0.2, 0.02), 0.28)),
    ("stool", 0.32, 0.34, 0.26, False, lambda p, m, x, y, z: cnc_stool(p, m, x, y, z)),
    ("chairs", 0.26, 0.17, 0.10, False, lambda p, m, x, y, z: mini_chairs(p, m, x, y, z)),
    ("geo_lamp", 0.26, 0.28, 0.26, False, lambda p, m, x, y, z: geodesic_lamp(p, m, x, y, z, 0.13)),
    ("vases", 0.24, 0.22, 0.10, False, lambda p, m, x, y, z: [twisted_vase(p, m, x - 0.07 + k * 0.07, y, z, 0.20 * (0.7 + 0.15 * k), m["pla"][k * 2], sides=5 + k) for k in range(3)]),
    ("arm", 0.22, 0.24, 0.14, False, lambda p, m, x, y, z: robot_arm(p, m, x - 0.05, y, z, m["pla"][3])),
    ("gears", 0.40, 0.18, 0.18, False, lambda p, m, x, y, z: (hinge_box(p, m, x - 0.11, y, z), gear(p, m, x + 0.07, y + 0.05, z + 0.09, 0.09, 14, m["ply"]),
                                                              gear(p, m, x + 0.17, y + 0.05, z + 0.06, 0.06, 10, m["pla"][0]))),
    ("topo", 0.36, 0.08, 0.26, False, lambda p, m, x, y, z: topo_relief(p, m, x, y, z + 0.012, 0.34, 0.24)),
    ("badges", 0.26, 0.04, 0.14, False, lambda p, m, x, y, z: pcb_badges(p, m, x, y, plinth(p, m, x, y, z, 0.26, 0.14, 0.02))),
    ("swatches", 0.30, 0.30, 0.10, False, lambda p, m, x, y, z: swatch_board(p, m, x, y, z)),
    ("truck", 0.26, 0.14, 0.12, False, lambda p, m, x, y, z: toy_truck(p, m, x, y, z)),
    ("shapes", 0.10, 0.22, 0.08, False, lambda p, m, x, y, z: shape_stack(p, m, x, y, z)),
]


def hex_relief(lib, m, col, x0=27.75, x1=32.20, z0=2.62, z1=3.45, wall=38.33, r=0.042):
    """Wall art above the demo bays: ~700 3D-printed hex tiles, brand-colour gradient across the wall
    (blue -> green -> yellow -> orange -> red -> pink, noise-blended), depths following a slow wave so the
    spotlight rakes across it; on a black backing board. Plus the ceiling spot that lights it."""
    p = lib["Part"]()
    order = [m["pla"][i] for i in (2, 1, 4, 3, 0, 5)]
    p.box(m["black"], x0 - 0.05, x1 + 0.05, wall - 0.012, wall - 0.002, z0 - 0.05, z1 + 0.05, bevel=0.003)
    dx, dz = r * math.sqrt(3), r * 1.5
    row = 0
    z = z0 + r
    while z < z1 - r * 0.5:
        x = x0 + (dx / 2 if row % 2 else 0) + dx / 2
        while x < x1 - dx * 0.4:
            u = (x - x0) / (x1 - x0)
            t = min(0.999, max(0.0, u + 0.12 * noise.noise(Vector((x * 1.7, z * 1.7, 0.5))) + rng.uniform(-0.045, 0.045)))
            c = order[int(t * len(order))]
            wave = 0.5 + 0.5 * math.sin(u * 7.0 + (z - z0) * 4.0 + 0.6 * noise.noise(Vector((x, z, 2.0))))
            depth = 0.010 + 0.040 * wave + rng.uniform(0, 0.004)
            yf = wall - 0.012 - depth
            bmesh.ops.create_cone(p.bm(c), cap_ends=True, segments=6, radius1=r * 0.93, radius2=r * 0.93, depth=depth,
                                  matrix=Matrix.Translation((x, yf + depth / 2, z)) @ Matrix.Rotation(math.pi / 2, 4, "X")
                                  @ Matrix.Rotation(math.pi / 6, 4, "Z"))
            x += dx
        z += dz
        row += 1
    # ceiling spot (black can on a short stem) aimed at the relief
    sx, sy, sz = (x0 + x1) / 2, wall - 1.6, 3.80
    p.cyl(m["black"], (sx, sy, 3.93), (sx, sy, sz + 0.06), 0.008, seg=8)
    aim = Vector(((x0 + x1) / 2, wall, (z0 + z1) / 2)) - Vector((sx, sy, sz))
    q = aim.to_track_quat("Z", "Y").to_matrix().to_4x4()
    can = Matrix.Translation((sx, sy, sz)) @ q
    bmesh.ops.create_cone(p.bm(m["black"]), cap_ends=True, segments=20, radius1=0.045, radius2=0.045, depth=0.14, matrix=can)
    p.emit("Art_HexRelief", col, Vector((0, 0, 0)))
    ld = bpy.data.lights.get("Art_Spot") or bpy.data.lights.new("Art_Spot", "SPOT")
    ld.energy, ld.spot_size, ld.spot_blend, ld.shadow_soft_size = 220.0, math.radians(62), 0.35, 0.03
    ld.color = (1.0, 0.93, 0.85)
    lo = bpy.data.objects.new("Art_Spot", ld)
    col.objects.link(lo)
    lo.matrix_world = Matrix.Translation(can @ Vector((0, 0, 0.08))) @ aim.to_track_quat("-Z", "Y").to_matrix().to_4x4()


def demo_fill(lib, slots, levels, H, depth, loc, rot, col, bays, sign=True, name="Demo_Pieces"):
    m = _mats(lib)
    p = lib["Part"]()
    tops = list(levels) + [H]
    yc = depth * 0.45
    m["card"] = lib["simple_mat"]("Label_Card", "#F4F2EC", 0.6)
    use = {}                                                            # kinds used per bay (no repeats in a bay)
    count = {}                                                          # and spread across bays
    k = 0
    for (bi, li), (xa, xb, _, _, zt) in sorted(slots.items(), key=lambda kv: (kv[0][0], -abs(kv[1][4] - 1.25))):
        if bi not in bays:
            continue
        clear = tops[li + 1] - zt - 0.05
        eye = 0.85 < zt < 1.65
        fit = [kd for kd in KINDS if kd[2] <= clear and kd[3] <= depth - 0.06 and kd[0] not in use.setdefault(bi, set())]
        fit.sort(key=lambda kd: 1.5 * count.get(kd[0], 0) - (1.0 if kd[4] and eye else 0.0) + 0.3 * rng.random())
        span, chosen = (xb - xa) - 0.16, []
        for kd in fit:                                                  # 1-2 pieces per shelf, the best first
            if sum(c[1] for c in chosen) + kd[1] + 0.14 * len(chosen) <= span and len(chosen) < 2:
                chosen.append(kd)
            if len(chosen) == 2 or (chosen and chosen[0][1] > 0.42):
                break
        if not chosen:
            continue
        gap = (span - sum(c[1] for c in chosen)) / (len(chosen) + 1)
        x = xa + 0.08 + gap
        for kd in chosen:
            cx = x + kd[1] / 2 + rng.uniform(-0.03, 0.03)
            kd[5](p, m, cx, yc, zt)
            label(p, m, cx + kd[1] / 2 - 0.02, 0.012, zt)
            use[bi].add(kd[0])
            count[kd[0]] = count.get(kd[0], 0) + 1
            x += kd[1] + gap
            k += 1
    p.emit(name, col, loc, rot)
    if not sign:
        return k
    hex_relief(lib, m, col)
    return k
