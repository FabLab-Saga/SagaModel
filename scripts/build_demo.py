"""Demo-piece display by the entrance: the back-wall run past the spine (bays 2-5 of Bank_A2,
x ~27.4-32.4, y 37.73-38.33) shows imaginary Fab Lab projects instead of boxes.
Exec'd from build_bank_lounge.py with `demo_fill(slots, levels, H, depth, loc, rot, col)`.
Pieces: low-poly 3D-printed busts, a voronoi/geodesic lamp, a stacked-slice acrylic sculpture,
twisted printed vases, a CNC-milled topographic relief, a laser-cut living-hinge box, plywood
gears, a little robot arm, PCB badges, a stack of printed shapes. Plus a neon LED sign on the wall.
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
        p.cyl(m["neon"], (cx, cy + 0.02, z + 0.0018), (cx, cy + 0.02, z + 0.004), 0.003, seg=8)


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


def demo_fill(lib, slots, levels, H, depth, loc, rot, col, bays):
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
    p.emit("Demo_Pieces", col, loc, rot)
    # neon sign on the wall above the display
    cu = bpy.data.curves.get("Demo_NeonSign") or bpy.data.curves.new("Demo_NeonSign", "FONT")
    cu.body = "make anything"
    cu.size = 0.30
    cu.extrude = 0.006
    cu.bevel_depth = 0.004
    cu.align_x = "CENTER"
    cu.materials.clear(); cu.materials.append(m["neon"])
    ob = bpy.data.objects.new("Demo_NeonSign", cu)
    col.objects.link(ob)
    ob.location = (30.45, 38.30, 2.78)
    ob.rotation_euler = (math.pi / 2, 0, 0)                             # reads left-to-right from the room
    back = lib["Part"]()
    back.box(m["acrylic"], 29.15, 31.75, 38.315, 38.325, 2.66, 3.10)
    back.emit("Demo_NeonBacking", col, Vector((0, 0, 0)))
    return k
