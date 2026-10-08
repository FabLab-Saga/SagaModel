"""Bill of materials for the black T-slot aluminium profile in the model: total length and cut list, split into
20x20 and 40x40, per collection. Read-only. Run inside Blender (MCP / bmcp.py) or headless:
    blender -b SagaV2_work.blend --python scripts/profile_bom.py [-- out.csv]

How it measures: every profile member is a separate mesh island with the profile material (Alu_Black_Anodized*) -
Part.profile() copies the Profile_2020/4040 template per member. Each island is measured in its own principal frame
(PCA), so rotated furniture counts correctly: two short extents = the section (20 or 40 mm), the long one = length.
Islands with the template's vertex count (72 = 20x20, 136 = 40x40) or a 20/40 mm section count as profile; the
rest (door handles, latches, strips that reuse the material) are listed as "other". Only render-visible objects count.
"""
import sys
from collections import defaultdict

import bpy
import numpy as np

TOL = 0.004


def islands(me, mat_idx):
    parent = list(range(len(me.vertices)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    used = set()
    for p in me.polygons:
        if p.material_index not in mat_idx:
            continue
        vs = list(p.vertices)
        used.update(vs)
        r = find(vs[0])
        for v in vs[1:]:
            parent[find(v)] = r
    groups = defaultdict(list)
    for v in used:
        groups[find(v)].append(v)
    return groups.values()


def measure(pts):
    """Length = extent along the principal (long) axis; section = the two other extents measured in the plane
    across it, rotated to the tightest box (a square section's PCA axes are arbitrary, often at 45 deg)."""
    c = pts - pts.mean(axis=0)
    _, vecs = np.linalg.eigh(np.cov(c.T) + np.eye(3) * 1e-12)
    axis = vecs[:, 2]
    L = float(np.ptp(c @ axis))
    u, v = vecs[:, 0], vecs[:, 1]
    q = np.stack([c @ u, c @ v], axis=1)
    best = None
    for k in range(90):
        t = np.radians(k)
        r = q @ np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])
        e = np.ptp(r, axis=0)
        if best is None or e[0] * e[1] < best[0] * best[1]:
            best = e
    a, b = sorted(best)
    return a, b, L


def run():
    rows = []
    for o in bpy.data.objects:
        if o.type != "MESH" or o.hide_render or not o.visible_get():
            continue
        idx = {i for i, s in enumerate(o.material_slots) if s.material and s.material.name.startswith("Alu_Black_Anodized")}
        if not idx:
            continue
        me = o.data
        mw = np.array(o.matrix_world)
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        co = co @ mw[:3, :3].T + mw[:3, 3]
        col = o.users_collection[0].name if o.users_collection else "-"
        for g in islands(me, idx):
            a, b, L = measure(co[g])
            kind = "other"                                           # handles, latches, strips in the same material
            for s, name, nv in ((0.02, "20x20", 72), (0.04, "40x40", 136)):
                if len(g) == nv or (abs(a - s) < TOL and abs(b - s) < TOL):
                    kind = name
            rows.append((kind, round(float(L), 3), col, o.name))
    return rows


def report(rows, csv_path=None):
    tot, n = defaultdict(float), defaultdict(int)
    bycol = defaultdict(lambda: defaultdict(float))
    cuts = defaultdict(lambda: defaultdict(int))
    for kind, L, col, _ in rows:
        tot[kind] += L
        n[kind] += 1
        bycol[col][kind] += L
        cuts[kind][round(L, 2)] += 1
    print("PROFILE TOTALS")
    for k in ("20x20", "40x40", "other"):
        if n[k]:
            print(f"  {k}: {tot[k]:8.2f} m in {n[k]} pieces")
    print("BY COLLECTION (m)")
    for c in sorted(bycol, key=lambda c: -(bycol[c]["20x20"] + bycol[c]["40x40"])):
        print(f"  {c:22s} 20x20 {bycol[c]['20x20']:7.2f}   40x40 {bycol[c]['40x40']:7.2f}"
              + (f"   other {bycol[c]['other']:.2f}" if bycol[c]["other"] else ""))
    if csv_path:
        with open(csv_path, "w") as f:
            f.write("section,length_m,count\n")
            for k in ("20x20", "40x40", "other"):
                for L in sorted(cuts[k]):
                    f.write(f"{k},{L},{cuts[k][L]}\n")
        print("cut list ->", csv_path)
    return tot, n


argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
report(run(), argv[0] if argv else globals().get("CSV"))
