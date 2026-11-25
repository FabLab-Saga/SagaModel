"""Generate layout/room.json (always) and layout/layout.yaml (only items it doesn't already have) from the .blend.

    blender -b SagaV2_work.blend --python scripts/layout_export.py            # room.json + new items only
    blender -b SagaV2_work.blend --python scripts/layout_export.py -- --fresh # rewrite layout.yaml from the scene

layout.yaml is hand-edited and the source of truth for positions once it exists: without --fresh this script
never changes an existing item's pos/rot/z, id, label, note or locked flag; it only refreshes `size` and adds
items for new builder objects. room.json is read-only for everyone else and fully regenerated each run.
"""
import json
import math
import os
import re
import subprocess
import sys

import bpy

ROOT = os.environ.get("SAGA_ROOT") or bpy.path.abspath("//")
L = {}
exec(open(os.path.join(ROOT, "scripts", "layout_blender.py")).read(), L)
layout_io = L["layout_io"]
measure = L["measure"]
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
FRESH = "--fresh" in argv
OUT = os.path.join(ROOT, "layout")
os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------------ zones (Blender model coordinates, metres)
# Laser room, entrance bay, CNC room walls and the bank box come from CLAUDE.md (city drawings + builders);
# the other boundaries follow the plan slice at 1.1 m. "approx" marks lines I drew from furniture/walls, not drawings.
ZONES = [
    ("laser-room", "Laser room", [(29.67, 20.14), (32.53, 20.14), (32.53, 26.92), (29.67, 26.92)], "CLAUDE.md"),
    ("cnc-room", "CNC room", [(20.85, 15.08), (25.75, 15.08), (25.75, 19.42), (24.26, 19.42), (24.26, 21.66),
                              (20.85, 21.66)], "CLAUDE.md + builders"),
    ("wc", "WC", [(24.26, 19.42), (25.75, 19.42), (25.75, 21.66), (24.26, 21.66)], "build_staff_area.py"),
    ("back-hallway", "Back hallway", [(25.9, 15.0), (27.6, 15.0), (27.6, 21.66), (25.9, 21.66)], "approx"),
    ("staff-room", "Staff room", [(27.73, 17.0), (32.53, 17.0), (32.53, 20.06), (29.67, 20.06), (29.67, 21.66),
                                  (27.73, 21.66)], "approx (y 17.0 boundary to the store room)"),
    ("store-room", "Electrical + store room", [(27.73, 15.0), (32.53, 15.0), (32.53, 17.0), (27.73, 17.0)],
     "approx; interior not modelled"),
    ("bank", "Búnaðarbanki SFS (equipment bank)", [(20.9, 34.31), (27.58, 34.31), (27.58, 38.35), (20.9, 38.35)],
     "build_bank_walls.py"),
    ("entrance-bay", "Entrance bay", [(32.6, 34.7), (34.3, 34.7), (34.3, 38.3), (32.6, 38.3)], "CLAUDE.md (drawings)"),
    ("lounge", "Lounge + on-call (fjölnota kennslurými)", [(28.25, 30.2), (32.53, 30.2), (32.53, 38.35),
                                                           (27.58, 38.35), (27.58, 34.31), (28.25, 34.31)],
     "approx (drawing label 110.8 m2)"),
    ("main-lab", "Main lab", [(20.85, 21.82), (29.67, 21.82), (29.67, 26.92), (32.53, 26.92), (32.53, 30.2),
                              (28.25, 30.2), (28.25, 34.31), (20.85, 34.31)], "approx"),
]
ZONE_PREFIX = {"laser-room": "laser", "cnc-room": "cnc", "wc": "wc", "back-hallway": "hall", "staff-room": "staff",
               "store-room": "store", "bank": "bank", "entrance-bay": "entrance", "lounge": "lounge",
               "main-lab": "lab"}


def in_poly(p, poly):
    x, y = p; c = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def zone_of(p):
    for zid, _, poly, _ in ZONES:
        if in_poly(p, poly):
            return zid
    best = min(ZONES, key=lambda z: min(math.dist(p, q) for q in z[2]))
    return best[0]


# ------------------------------------------------------------------ items
FURN = ["Machines", "LaserRoom", "PrintFarm", "CraftZone", "Textile", "WorkTables", "Welcome", "Lounge", "Spine",
        "MaterialStorage", "Microelectronics", "EquipmentBank", "MuralCupboard", "CNCRoom", "StaffArea", "Life"]
EXCLUDE = re.compile(r"(Door|Glass(?!Bench|TW|ToolWall)|Infill|Tiles|Paving|Fixture|Plaque|Wall_Details|^WC_|"
                     r"Exterior|^Hall_|Window|SecretDoor|Art_HexRelief|Floff|Mural$|^Staff_LaserWall)")
KEEP_FRAME = {"PrintFarm_Frame", "GlassToolWall_Frame"}
MACHINE = re.compile(r"^(Glowforge|Epilog_FusionEdge|xTool_F1_Ultra$|ShopBot_PRSAlpha|ACword|Prusa_MK3S|Bambu|"
                     r"Roland_|Cricut_|Mayku|Brother_|Overlock|Creality|Flashforge|Eazao|Clay_Microwave|"
                     r"Handheld_3DScanner|HeatPress|LOKLiK)")
STORAGE = re.compile(r"Shelving|Rack|Storage|Cab|Cupboard|Cart|ToolLibrary|BoardRack|Bin|DryCell|Demo_Pieces|Box|"
                     r"PrintFarm_Frame|ToolWall|ToolChest|Utilities")
FURNITURE = re.compile(r"Table|Chair|Stool|Sofa|Pouf|Desk|Bench|Counter|Armchair|PCStation|Stand")
LOCKED = {"Exhaust_Central", "Staff_Kitchen", "Electronics_BoardRun", "LaserSafety", "Staff_CoatHooks",
          "Staff_Whiteboard"}
COMPANION_RE = [(re.compile(r"^WB_Text"), "Electronics_BoardRun"), (re.compile(r"^Staff_Coat_"), "Staff_CoatHooks"),
                (re.compile(r"^(DrawerCab_|ToolRail_)"), "MicroBench")]
FLOOR_Z = 0.05
COMPANION = {"Spine_Panel": "Spine_Boxes_Shelving", "ShopBot_DustBoom": "ShopBot_PRSAlpha_120",
             "ShopBot_DustHose": "ShopBot_PRSAlpha_120", "Epilog_Logo": "Epilog_FusionEdge24",
             "Epilog_Model": "Epilog_FusionEdge24", "xTool_Wordmark": "xTool_F1_Ultra",
             "LaserBench_Staging": "LaserBench", "Staff_Appliances": "Staff_Kitchen", "Staff_Mugs": "Staff_Kitchen",
             "Staff_Tote": "Staff_CoatHooks", "SMD_Reels": "ComponentStorage", "GlassBench_Spools": "GlassBench",
             "Clay_Bucket_0": "GlassBench", "Clay_Bucket_1": "GlassBench", "Lounge_Table": None}


def candidates():
    out = []
    for cn in FURN:
        col = bpy.data.collections.get(cn)
        if not col:
            continue
        for o in col.objects:
            if o.parent is not None or o.name in [c.name for c in out]:
                continue
            if (EXCLUDE.search(o.name) or (o.name.endswith("_Frame") and o.name not in KEEP_FRAME)):
                continue
            if o.type not in {"EMPTY", "MESH", "FONT"}:
                continue
            m = measure([o])
            if m is None or m["size"][0] * m["size"][1] < 1e-4 and o.type != "FONT":
                continue
            out.append(o)
    return out


def obb(m, pad=0.0):
    (cx, cy), r = m["pos"], math.radians(m["rot"])
    w, d = m["size"][0] / 2 + pad, m["size"][1] / 2 + pad
    ux, uy, vx, vy = math.cos(r), math.sin(r), -math.sin(r), math.cos(r)
    return [(cx + sx * w * ux + sy * d * vx, cy + sx * w * uy + sy * d * vy) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def build_items(existing):
    objs = candidates()
    meas = {o.name: measure([o]) for o in objs}
    by_name = {o.name: o for o in objs}
    host = {}                                                         # companion -> primary
    names = [o.name for o in objs]
    area = {n: meas[n]["size"][0] * meas[n]["size"][1] for n in names}
    for n in names:
        if n in COMPANION:
            if COMPANION[n] and COMPANION[n] in by_name:
                host[n] = COMPANION[n]
            continue
        rx = [h for rgx, h in COMPANION_RE if rgx.search(n) and h in by_name]
        if rx:
            host[n] = rx[0]; continue
        pre = [p for p in names if p != n and n.startswith(p + "_") and not MACHINE.match(n)]
        if pre:
            host[n] = max(pre, key=len); continue
    clusters = []                                                     # same origin + rotation -> one piece
    for n in names:
        o = by_name[n]
        if n in host or o.location.length < 0.01 or MACHINE.match(n) or n in LOCKED:
            continue
        for cl in clusters:
            q = by_name[cl[0]]
            if (q.location.xy - o.location.xy).length < 0.005 and abs(q.rotation_euler.z - o.rotation_euler.z) < 1e-3:
                cl.append(n); break
        else:
            clusters.append([n])
    for cl in clusters:
        if len(cl) > 1:
            prim = max(cl, key=lambda x: area[x])
            for x in cl:
                if x != prim:
                    host[x] = prim
    floor = [n for n in names if n not in host and meas[n]["z"] < FLOOR_Z]
    on = {}
    for n in names:                                                   # things standing/hanging on another item
        if n in host or meas[n]["z"] < FLOOR_Z or n in LOCKED:
            continue
        p = meas[n]["pos"]
        hits = [f for f in floor if f != n and in_poly(p, obb(meas[f], 0.2))
                and meas[f]["z"] + meas[f]["size"][2] >= meas[n]["z"] - 0.2]
        if not hits:
            continue
        h = min(hits, key=lambda f: (round(abs(meas[f]["z"] + meas[f]["size"][2] - meas[n]["z"]), 1), area[f]))
        if MACHINE.match(n):
            on[n] = h
        else:
            host[n] = h
    for n in list(host):                                              # resolve chains
        while host[n] in host:
            host[n] = host[host[n]]
    groups = {}
    for n in names:
        if n not in host:
            groups[n] = [n]
    for n, h in host.items():
        if h in groups:
            groups[h].append(n)
    old_by_obj = {it["objects"][0]: it for it in existing.get("items", [])} if existing else {}
    used = {it["id"] for it in old_by_obj.values()}
    items = []
    ids = {}
    for prim, members in groups.items():
        m = measure([by_name[x] for x in members])
        zone = zone_of(m["pos"])
        kind = "machine" if MACHINE.match(prim) or prim in ("ShopBot_Control",) else \
            "fixture" if prim in LOCKED else "storage" if STORAGE.search(prim) else \
            "furniture" if FURNITURE.search(prim) else "fixture"
        old = old_by_obj.get(prim)
        if old:
            iid = old["id"]
        else:
            slug = re.sub(r"[^a-z0-9]+", "-", prim.replace("_-", "_m").lower()).strip("-")
            iid = f"{ZONE_PREFIX[zone]}.{slug}"
            k = 2
            while iid in used:
                iid = f"{ZONE_PREFIX[zone]}.{slug}-{k}"; k += 1
        used.add(iid)
        ids[prim] = iid
        it = {"id": iid, "label": prim.replace("_", " "), "kind": kind, "zone": zone,
              "pos": [round(m["pos"][0], 3), round(m["pos"][1], 3)], "z": round(m["z"], 3), "rot": round(m["rot"], 1),
              "size": [round(v, 3) for v in m["size"]], "on": None, "locked": prim in LOCKED, "note": None,
              "objects": members}
        if old and not FRESH:
            for k2 in ("label", "kind", "zone", "pos", "z", "rot", "locked", "machine", "count", "note"):
                if k2 in old:
                    it[k2] = old[k2]
        items.append(it)
    for it in items:
        if it["objects"][0] in on:
            it["on"] = ids.get(on[it["objects"][0]])
    zorder = [z[0] for z in ZONES]
    items.sort(key=lambda it: (zorder.index(it["zone"]), it["on"] or "", it["id"]))
    return items


# ------------------------------------------------------------------ room.json
ARCH_SKIP = {"Lighting", "Cameras", "Walkthrough", "Site", "Reference", "Life", "Signs", "Facade_Cutters", "Hall",
             "HallEntrance", "AssetLibrary", "Services", "Acoustics", "Branding"}


def wall_kind(o):
    n = o.name
    if "Glass" in n and (n.startswith("Facade") or "EndWindows" in n or "EndDoor" in n):
        return "glazing"
    if "Glass" in n or "FireGlass" in n:
        return "glass-partition"
    return "wall"


def pair_walls(segs):
    """Turn the two faces of each wall into one centreline with thickness t."""
    def geom(s):
        (a, b) = s
        th = math.atan2(b[1] - a[1], b[0] - a[0]) % math.pi
        ux, uy = math.cos(th), math.sin(th)
        off = -uy * a[0] + ux * a[1]
        s1, s2 = sorted((ux * a[0] + uy * a[1], ux * b[0] + uy * b[1]))
        return th, off, s1, s2, ux, uy
    G = [geom(s) for s in segs]
    used = set(); out = []
    order = sorted(range(len(G)), key=lambda i: -(G[i][3] - G[i][2]))
    for i in order:
        if i in used:
            continue
        th, off, s1, s2, ux, uy = G[i]
        best = None
        for j in order:
            if j == i or j in used:
                continue
            th2, off2, t1, t2, _, _ = G[j]
            dth = abs(th - th2); dth = min(dth, math.pi - dth)
            if dth > math.radians(1.0):
                continue
            d = abs(off - off2 if abs(th - th2) < 1 else off + off2)
            if not 0.004 < d < 0.45:
                continue
            ov = min(s2, t2) - max(s1, t1)
            if ov < 0.6 * min(s2 - s1, t2 - t1):
                continue
            if best is None or d < best[1]:
                best = (j, d)
        if best is None:
            used.add(i)
            out.append((s1, s2, off, 0.05, ux, uy)); continue
        j, d = best
        used.update((i, j))
        th2, off2, t1, t2, _, _ = G[j]
        o2 = off2 if abs(th - th2) < 1 else -off2
        out.append((min(s1, t1), max(s2, t2), (off + o2) / 2, d, ux, uy))
    res = []
    for s1, s2, off, t, ux, uy in out:
        a = (ux * s1 - uy * off, uy * s1 + ux * off); b = (ux * s2 - uy * off, uy * s2 + ux * off)
        res.append((a, b, t))
    return res


def split_columns(segs):
    """Clusters of short connected segments: round/square columns (0.35-0.95 m, near-square) are returned as
    columns; other small clusters under 0.3 m (props, fittings) are dropped; everything else stays a wall."""
    short = [i for i, s in enumerate(segs) if math.dist(*s) < 0.2]
    parent = {i: i for i in short}
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    grid = {}
    for i in short:
        for p in segs[i]:
            k = (round(p[0] / 0.03), round(p[1] / 0.03))
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for j in grid.get((k[0] + dx, k[1] + dy), []):
                        parent[find(i)] = find(j)
            grid.setdefault(k, []).append(i)
    groups = {}
    for i in short:
        groups.setdefault(find(i), []).append(i)
    drop, cols = set(), []
    for g in groups.values():
        xs = [p[0] for i in g for p in segs[i]]; ys = [p[1] for i in g for p in segs[i]]
        w, d = max(xs) - min(xs), max(ys) - min(ys)
        if len(g) >= 10 and 0.35 <= w <= 0.95 and 0.35 <= d <= 0.95 and abs(w - d) < 0.12:
            cols.append({"pos": [round((max(xs) + min(xs)) / 2, 3), round((max(ys) + min(ys)) / 2, 3)],
                         "size": [round(w, 3), round(d, 3)], "shape": "round" if len(g) >= 16 else "square"})
            drop.update(g)
        elif max(w, d) < 0.3:
            drop.update(g)
    return [s for i, s in enumerate(segs) if i not in drop], cols


def room_json(items):
    item_objs = set()
    for it in items:
        for n in it["objects"]:
            o = bpy.data.objects.get(n)
            if o:
                item_objs.update(x.name for x in L["_tree"](o))
    by_kind = {"wall": [], "glazing": [], "glass-partition": []}
    for col in bpy.data.collections:
        if col.name in ARCH_SKIP:
            continue
        for o in col.objects:
            if o.type != "MESH" or o.hide_render or o.name in item_objs or o.display_type in {"BOUNDS", "WIRE"}:
                continue
            if "Frame" in o.name or o.name in ("Floor", "Ceiling_Slab"):
                continue
            by_kind[wall_kind(o)].append(o)
    walls, columns = [], []
    n = 0
    for kind, objs in by_kind.items():
        segs = L["merge_segments"](L["slice_segments"](objs, 1.1))
        if kind == "wall":
            segs, cols = split_columns(segs)
            for c in cols:
                columns.append(dict(id=f"col-{len(columns) + 1}", source="section", **c))
            gx = sorted({round(c["pos"][0], 1) for c in cols}); gy = sorted({round(c["pos"][1], 1) for c in cols})
            for x in gx:                                              # 8.40 m grid: fill columns hidden in walls
                for y in gy:
                    if not any(math.dist((x, y), c["pos"]) < 0.5 for c in columns):
                        ref = min(cols, key=lambda c: abs(c["pos"][0] - x))
                        columns.append({"id": f"col-{len(columns) + 1}", "source": "grid",
                                        "pos": [ref["pos"][0], min(cols, key=lambda c: abs(c["pos"][1] - y))["pos"][1]],
                                        "size": [0.64, 0.64], "shape": "round"})
        for a, b, t in pair_walls(segs):
            if math.dist(a, b) < 0.08:
                continue
            n += 1
            walls.append({"id": f"w{n}", "kind": kind, "a": [round(a[0], 3), round(a[1], 3)],
                          "b": [round(b[0], 3), round(b[1], 3)], "t": round(max(t, 0.01), 3)})
    doors = DOORS
    keepout = []
    for d in doors:
        keepout.extend(door_keepouts(d))
    fl = bpy.data.objects["Floor"]
    xs = [(fl.matrix_world @ __import__("mathutils").Vector(c)) for c in fl.bound_box]
    try:
        sha = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    except OSError:
        sha = ""
    return {
        "version": 1,
        "frame": "Blender model coordinates in metres; +Y = ESE (bearing 116 deg), +X = SSW (sunny facade); "
                 "rotations deg CCW about +Z seen from above",
        "bounds": {"min": [round(min(v.x for v in xs), 3), round(min(v.y for v in xs), 3)],
                   "max": [round(max(v.x for v in xs), 3), round(max(v.y for v in xs), 3)]},
        "section_height": 1.1,
        "walls": walls, "doors": doors, "columns": columns,
        "zones": [{"id": z, "label": lbl, "polygon": [list(p) for p in poly], "source": src} for z, lbl, poly, src in ZONES],
        "keepout": keepout, "services": SERVICES,
        "rules": {"walkway_min": 1.2, "aisle_laser_min": 1.0, "door_clear": 0.9},
        "source_commit": sha,
    }


# Doors: positions from CLAUDE.md / builders. hinge = the end (a|b) the leaf turns on; swing = in|out relative to
# `side`, a point on the room side the door belongs to. source: drawing | model | assumed (hinge/swing guessed).
DOORS = [
    {"id": "entrance", "a": [34.34, 36.54], "b": [34.34, 37.47], "hinge": "b", "swing": "in", "side": [33.8, 37.0],
     "kind": "fire", "source": "drawing", "note": "EI2 30 fire door to the university hall, held open"},
    {"id": "escape-ssw-1", "a": [32.53, 32.4], "b": [32.53, 33.35], "hinge": "a", "swing": "out", "side": [32.0, 32.9],
     "kind": "escape", "source": "drawing", "note": "pair ÚT in the SSW glazing per Andrúm AT 20-10-02; NOT modelled (open item)"},
    {"id": "escape-ssw-2", "a": [32.53, 33.35], "b": [32.53, 34.3], "hinge": "b", "swing": "out", "side": [32.0, 33.8],
     "kind": "escape", "source": "drawing", "note": "second leaf of the pair; NOT modelled (open item)"},
    {"id": "laser-nne", "a": [29.67, 25.81], "b": [29.67, 26.88], "hinge": "b", "swing": "in", "side": [30.2, 26.3],
     "kind": "glass", "source": "assumed", "note": "laser room door from the main lab; hinge/swing not checked"},
    {"id": "laser-exterior", "a": [32.53, 25.28], "b": [32.53, 26.76], "hinge": "b", "swing": "out", "side": [32.0, 26.0],
     "kind": "standard", "source": "assumed", "note": "laser room exterior door; hinge/swing not checked"},
    {"id": "cnc-glass", "a": [20.9, 21.74], "b": [21.9, 21.74], "hinge": "a", "swing": "in", "side": [21.4, 21.2],
     "kind": "glass", "source": "assumed", "note": "CNC room glass door 1.0 x 2.70; swing not checked"},
    {"id": "cnc-hall", "a": [25.83, 16.85], "b": [25.83, 17.85], "hinge": "a", "swing": "in", "side": [25.3, 17.35],
     "kind": "standard", "source": "model", "note": "CNC room door from the back hallway"},
    {"id": "cnc-loading-1", "a": [22.4, 14.97], "b": [23.56, 14.97], "hinge": "a", "swing": "out", "side": [23.0, 15.5],
     "kind": "standard", "source": "model", "note": "loading double door, leaf 1, opens outward"},
    {"id": "cnc-loading-2", "a": [23.56, 14.97], "b": [24.72, 14.97], "hinge": "b", "swing": "out", "side": [24.2, 15.5],
     "kind": "standard", "source": "model", "note": "loading double door, leaf 2"},
    {"id": "hall-end", "a": [26.22, 14.97], "b": [27.22, 14.97], "hinge": "a", "swing": "out", "side": [26.7, 15.5],
     "kind": "glass", "source": "model", "note": "back hallway glass end door, opens outward; hinge side assumed"},
    {"id": "wc", "a": [25.83, 19.55], "b": [25.83, 20.6], "hinge": "a", "swing": "in", "side": [25.3, 20.0],
     "kind": "standard", "source": "model"},
    {"id": "staff", "a": [27.62, 20.31], "b": [27.62, 21.36], "hinge": "b", "swing": "in", "side": [28.2, 20.8],
     "kind": "standard", "source": "model"},
    {"id": "store", "a": [27.62, 15.1], "b": [27.62, 16.06], "hinge": "a", "swing": "in", "side": [28.2, 15.6],
     "kind": "standard", "source": "assumed", "note": "electrical/store room, closed in the model"},
    {"id": "bank-secret", "a": [27.87, 36.505], "b": [27.87, 37.665], "hinge": "a", "swing": "out", "side": [27.4, 37.1],
     "kind": "standard", "source": "model", "note": "bookcase door into the bank"},
]

SERVICES = [
    {"id": "exhaust-laser-riser", "kind": "exhaust", "pos": [32.35, 25.17], "note": "laser exhaust riser to the vent (approx x)"},
    {"id": "water-staff-kitchen", "kind": "water", "pos": [28.08, 18.86]},
    {"id": "water-wc", "kind": "water", "pos": [24.43, 20.13]},
]


def door_keepouts(d):
    a, b = d["a"], d["b"]
    hx, hy = a if d["hinge"] == "a" else b
    fx, fy = b if d["hinge"] == "a" else a
    w = math.dist(a, b)
    ux, uy = (fx - hx) / w, (fy - hy) / w
    nx, ny = -uy, ux                                                  # a normal; flip towards the swing side
    sx, sy = d["side"]
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    if (sx - mx) * nx + (sy - my) * ny < 0:
        nx, ny = -nx, -ny
    if d["swing"] == "out":
        nx, ny = -nx, -ny
    arc = [(hx, hy)] + [(hx + w * (math.cos(t) * ux + math.sin(t) * nx), hy + w * (math.cos(t) * uy + math.sin(t) * ny))
                        for t in [i * math.pi / 2 / 8 for i in range(9)]]
    out = [{"id": f"swing-{d['id']}", "reason": "door swing", "door": d["id"],
            "polygon": [[round(x, 3), round(y, 3)] for x, y in arc]}]
    if d["kind"] in ("escape", "fire"):
        c = 0.9
        for sgn, tag in ((1, "a"), (-1, "b")):
            px, py = nx * sgn * c, ny * sgn * c
            poly = [a, b, (b[0] + px, b[1] + py), (a[0] + px, a[1] + py)]
            out.append({"id": f"clear-{d['id']}-{tag}", "reason": "escape route", "door": d["id"],
                        "polygon": [[round(x, 3), round(y, 3)] for x, y in poly]})
    return out


path = os.path.join(OUT, "layout.yaml")
existing = layout_io.load(path) if os.path.exists(path) and not FRESH else {}
items = build_items(existing)
if existing and not FRESH:                                            # keep hand edits; only add / refresh sizes
    have = {it["id"]: it for it in existing["items"]}
    for it in items:
        if it["id"] in have:
            have[it["id"]]["size"] = it["size"]
        else:
            existing["items"].append(it)
    data = existing
else:
    data = {"version": 1, "items": items}
HEADER = """# Fab Lab SAGA layout: the ONLY source of item positions. Format: layout/README.md.
# Blender model coordinates, metres. +Y = ESE, +X = SSW (sunny facade). rot = degrees CCW about +Z, seen from above.
# pos = footprint centre [x, y], z = base height, size = [w, d, h] in the item's own frame. `objects` = Blender
# root objects that move together (first = primary). Builders read this file; scripts/layout_snapshot.py diffs it."""
layout_io.save(data, path, HEADER)
room = room_json(data["items"])
with open(os.path.join(OUT, "room.json"), "w", encoding="utf-8") as f:
    json.dump(room, f, ensure_ascii=False, indent=1)
print("layout_export: %d items, %d walls, %d columns, %d doors, %d keepouts" % (
    len(data["items"]), len(room["walls"]), len(room["columns"]), len(room["doors"]), len(room["keepout"])))
