"""Demo-piece display by the entrance: the back-wall run past the spine (bays 2-5 of Bank_A2,
x ~27.4-32.4, y 37.73-38.33) shows imaginary Fab Lab projects instead of boxes.
Exec'd from build_bank_lounge.py with `demo_fill(slots, levels, H, depth, loc, rot, col)`.
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
    pieces = [
        lambda x, z, cl: (bust(p, m, x, yc, plinth(p, m, x, yc, z), min(0.22, cl * 0.5), m["pla"][6])),
        lambda x, z, cl: geodesic_lamp(p, m, x, yc, z, min(0.16, cl * 0.42)),
        lambda x, z, cl: slice_sculpture(p, m, x, yc, plinth(p, m, x, yc, z, 0.2, 0.2, 0.02), min(0.30, cl - 0.06)),
        lambda x, z, cl: [twisted_vase(p, m, x - 0.07 + k * 0.07, yc, z, min(0.22, cl - 0.05) * (0.7 + 0.15 * k), m["pla"][k * 2], sides=5 + k) for k in range(3)],
        lambda x, z, cl: topo_relief(p, m, x, yc, z + 0.012, 0.34, 0.26),
        lambda x, z, cl: (hinge_box(p, m, x - 0.08, yc, z), gear(p, m, x + 0.10, yc + 0.08, z + 0.09, 0.09, 14, m["ply"]),
                          gear(p, m, x + 0.20, yc + 0.08, z + 0.06, 0.06, 10, m["pla"][0])),
        lambda x, z, cl: robot_arm(p, m, x, yc, z, m["pla"][3]),
        lambda x, z, cl: (pcb_badges(p, m, x, yc, plinth(p, m, x, yc, z, 0.26, 0.14, 0.02))),
        lambda x, z, cl: shape_stack(p, m, x, yc, z),
        lambda x, z, cl: (bust(p, m, x, yc, plinth(p, m, x, yc, z), min(0.14, cl * 0.4), m["pla"][rng.choice((0, 2, 4))])),
    ]
    k = 0
    for (bi, li), (xa, xb, _, _, zt) in sorted(slots.items()):
        if bi not in bays:
            continue
        clear = tops[li + 1] - zt - 0.06
        n = 3 if (xb - xa) > 1.0 else 2
        for j in range(n):
            if rng.random() < 0.08:                                     # leave some breathing room
                continue
            x = xa + (j + 0.5) * (xb - xa) / n + rng.uniform(-0.05, 0.05)
            pieces[k % len(pieces)](x, zt, clear)
            k += 1
    p.emit(name, col, loc, rot)
    if not sign:
        return k
    hex_relief(lib, m, col)
    return k
