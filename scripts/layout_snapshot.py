#!/usr/bin/env python3
"""Layout snapshot: what moved, and which moves break a rule. Format and flow: layout/README.md.

    python3 scripts/layout_snapshot.py                 # target = live Blender (socket 9876) if open, else working yaml
    python3 scripts/layout_snapshot.py --blend F.blend # target = a saved .blend (headless Blender)
    python3 scripts/layout_snapshot.py --yaml F.yaml   # target = another layout file
    python3 scripts/layout_snapshot.py --ref layout/drafts [--base main]
    python3 scripts/layout_snapshot.py --json          # contract JSON
    python3 scripts/layout_snapshot.py --write         # accept: write the target poses into layout/layout.yaml

Base defaults to layout/layout.yaml at git HEAD. System python3, stdlib only.
"""
import argparse
import json
import math
import os
import socket
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import layout_io  # noqa: E402
import layout_clearance  # noqa: E402

YAML = os.path.join(ROOT, "layout", "layout.yaml")
ROOM = os.path.join(ROOT, "layout", "room.json")
TOL_POS, TOL_ROT = 0.002, 0.2                      # below this a pose is "unchanged" (m, deg)
SEAT = ("chair", "stool", "pouf")
SURFACE = ("table", "bench", "desk", "counter", "station")

POSE_CODE = r'''
import json, os, bpy
_L = {}
_root = os.environ.get("SAGA_ROOT") or bpy.path.abspath("//")
exec(open(os.path.join(_root, "scripts", "layout_blender.py")).read(), _L)
print("@@POSES@@" + json.dumps(_L["poses"]()) + "@@END@@")
'''


def git_show(ref, path="layout/layout.yaml"):
    r = subprocess.run(["git", "-C", ROOT, "show", f"{ref}:{path}"], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"git show {ref}:{path} failed: {r.stderr.strip()}")
    return r.stdout


def git_sha(ref):
    r = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", ref], capture_output=True, text=True)
    return r.stdout.strip() or ref


def _parse_poses(text):
    if "@@POSES@@" not in text:
        raise SystemExit("no poses returned from Blender:\n" + text[-2000:])
    return json.loads(text.split("@@POSES@@", 1)[1].split("@@END@@", 1)[0])


def live_poses():
    s = socket.create_connection(("127.0.0.1", 9876), timeout=120)
    s.sendall(json.dumps({"type": "execute_code", "params": {"code": POSE_CODE}}).encode())
    buf = b""
    while True:
        chunk = s.recv(1 << 20)
        if not chunk:
            break
        buf += chunk
        try:
            json.loads(buf); break
        except ValueError:
            pass
    text = buf.decode("utf-8", "replace")
    try:                               # the add-on wraps stdout in a JSON reply: unwrap it (quotes come escaped)
        def strings(o):
            if isinstance(o, str):
                yield o
            elif isinstance(o, dict):
                for v in o.values():
                    yield from strings(v)
            elif isinstance(o, list):
                for v in o:
                    yield from strings(v)
        text = next((s for s in strings(json.loads(text)) if "@@POSES@@" in s), text)
    except ValueError:
        pass
    return _parse_poses(text)


def blend_poses(path):
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(POSE_CODE)
    env = dict(os.environ, SAGA_ROOT=ROOT)
    cmd = ["blender", "-b", os.path.abspath(path), "--python", f.name]
    if subprocess.run(["systemd-run", "--version"], capture_output=True).returncode == 0:
        cmd = ["systemd-run", "--user", "--scope", "-q", "-p", "MemoryMax=12G", f"--setenv=SAGA_ROOT={ROOT}"] + cmd
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    os.unlink(f.name)
    return _parse_poses(r.stdout + r.stderr)


def socket_up():
    try:
        socket.create_connection(("127.0.0.1", 9876), timeout=0.5).close(); return True
    except OSError:
        return False


def items_from_poses(base, poses):
    out = []
    for it in base["items"]:
        p = poses.get(it["id"])
        it = dict(it)
        if p and not p.get("missing"):
            it["pos"], it["z"], it["rot"], it["size"] = p["pos"], p["z"], p["rot"], p["size"]
        out.append(it)
    return {"version": base.get("version", 1), "items": out}


# ------------------------------------------------------------------ geometry
def obb(it, pad=0.0):
    (cx, cy), r = it["pos"], math.radians(it.get("rot", 0) or 0)
    w, d = it["size"][0] / 2 + pad, it["size"][1] / 2 + pad
    c, s = math.cos(r), math.sin(r)
    return [(cx + sx * w * c - sy * d * s, cy + sx * w * s + sy * d * c) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def _axes(poly):
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        n = (y1 - y2, x2 - x1); l = math.hypot(*n) or 1
        yield (n[0] / l, n[1] / l)


def convex_overlap(a, b):
    """Penetration depth (m) of two convex polygons via SAT; 0 if they don't overlap."""
    depth = 1e9
    for ax in list(_axes(a)) + list(_axes(b)):
        pa = [ax[0] * x + ax[1] * y for x, y in a]; pb = [ax[0] * x + ax[1] * y for x, y in b]
        o = min(max(pa), max(pb)) - max(min(pa), min(pb))
        if o <= 0:
            return 0.0
        depth = min(depth, o)
    return depth


def _seg_dist(p, q, a, b):
    def pt(p, a, b):
        ax, ay = b[0] - a[0], b[1] - a[1]; l2 = ax * ax + ay * ay
        t = 0 if l2 == 0 else max(0, min(1, ((p[0] - a[0]) * ax + (p[1] - a[1]) * ay) / l2))
        return math.hypot(p[0] - a[0] - t * ax, p[1] - a[1] - t * ay)
    return min(pt(p, a, b), pt(q, a, b), pt(a, p, q), pt(b, p, q))


def poly_dist(a, b):
    if convex_overlap(a, b) > 0:
        return 0.0
    return min(_seg_dist(a[i], a[(i + 1) % len(a)], b[j], b[(j + 1) % len(b)]) for i in range(len(a)) for j in range(len(b)))


def in_poly(p, poly):
    x, y = p; c = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def is_floor(it):
    return not it.get("on") and (it.get("z") or 0) < 0.3


def _kindword(it, words):
    s = (it["id"] + " " + str(it.get("label", ""))).lower()
    return any(w in s for w in words)


def wall_rects(room):
    out = []
    for w in room["walls"]:
        (ax, ay), (bx, by), t = w["a"], w["b"], max(w["t"], 0.02) / 2
        l = math.hypot(bx - ax, by - ay) or 1
        nx, ny = -(by - ay) / l * t, (bx - ax) / l * t
        out.append((w, [(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny), (ax - nx, ay - ny)]))
    for c in room["columns"]:
        (x, y), (sw, sd) = c["pos"], c["size"]
        out.append((c, [(x - sw / 2, y - sd / 2), (x + sw / 2, y - sd / 2), (x + sw / 2, y + sd / 2), (x - sw / 2, y + sd / 2)]))
    return out


# ------------------------------------------------------------------ diff + rules
def direction(dx, dy):
    parts = []
    for v, pos, neg in ((dx, "+X (SSW)", "-X (NNE)"), (dy, "+Y (ESE)", "-Y (WNW)")):
        if abs(v) >= 0.02:
            parts.append((abs(v), pos if v > 0 else neg))
    parts.sort(reverse=True)
    return " / ".join(p for _, p in parts)


def diff(base, target):
    B = {it["id"]: it for it in base["items"]}; T = {it["id"]: it for it in target["items"]}
    moves = []
    for iid, t in T.items():
        b = B.get(iid)
        if not b:
            continue
        dx, dy = t["pos"][0] - b["pos"][0], t["pos"][1] - b["pos"][1]
        drot = ((t.get("rot", 0) - b.get("rot", 0)) + 180) % 360 - 180
        dz = (t.get("z") or 0) - (b.get("z") or 0)
        if math.hypot(dx, dy) >= TOL_POS or abs(drot) >= TOL_ROT or abs(dz) >= TOL_POS:
            moves.append({"id": iid, "from": {"pos": b["pos"], "rot": b.get("rot", 0), "z": b.get("z", 0)},
                          "to": {"pos": [round(t["pos"][0], 3), round(t["pos"][1], 3)], "rot": round(t.get("rot", 0), 1),
                                 "z": round(t.get("z") or 0, 3)},
                          "dist": round(math.hypot(dx, dy), 3), "drot": round(drot, 1), "dz": round(dz, 3),
                          "zone_from": b.get("zone"), "dx": dx, "dy": dy})
    added = [T[i] for i in T if i not in B]
    removed = [i for i in B if i not in T]
    return moves, added, removed


def rules(base, target, room, moves, added):
    R = room["rules"]; T = {it["id"]: it for it in target["items"]}; B = {it["id"]: it for it in base["items"]}
    changed = [m["id"] for m in moves] + [a["id"] for a in added]
    floor = [it for it in target["items"] if is_floor(it) and it.get("size")]
    walls = wall_rects(room)
    zones = {z["id"]: z for z in room["zones"]}
    out = []
    mv = {m["id"]: m for m in moves}
    for iid in changed:
        it = T[iid]
        if not it.get("size") or not it.get("pos"):
            continue
        box = obb(it)
        if iid in mv and it.get("locked"):
            out.append({"rule": "locked", "items": [iid], "value": mv[iid]["dist"], "where": it["pos"]})
        z = zones.get(it.get("zone"))
        if z and not in_poly(it["pos"], z["polygon"]):
            inside = [zz["id"] for zz in room["zones"] if in_poly(it["pos"], zz["polygon"])]
            out.append({"rule": "zone", "items": [iid], "value": inside[0] if inside else "outside",
                        "where": it["pos"]})
        for k in room["keepout"]:
            d = convex_overlap(box, [tuple(p) for p in k["polygon"]]) if is_floor(it) else 0
            if d > 0.01:
                out.append({"rule": "keepout:" + k["reason"], "items": [iid, k["id"]], "value": round(d, 3),
                            "where": it["pos"]})
        for ch in target["items"]:                            # on-children left behind
            if ch.get("on") == iid and iid in mv and ch["id"] not in mv:
                out.append({"rule": "child_left_behind", "items": [iid, ch["id"]], "value": mv[iid]["dist"],
                            "where": ch["pos"]})
        if not is_floor(it):
            continue
        gap_min = R["aisle_laser_min"] if it.get("zone") == "laser-room" else R["walkway_min"]
        bbox_base = obb(B[iid]) if iid in B else None
        for o in floor:
            if o["id"] == iid or o.get("on") == iid or it.get("on") == o["id"]:
                continue
            ob = obb(o)
            pen = convex_overlap(box, ob)
            seat_pair = (_kindword(it, SEAT) and _kindword(o, SURFACE)) or (_kindword(o, SEAT) and _kindword(it, SURFACE))
            if pen > 0.02 and not seat_pair:
                out.append({"rule": "overlap", "items": [iid, o["id"]], "value": round(pen, 3), "where": it["pos"]})
                continue
            if pen > 0 or seat_pair:
                continue
            d = poly_dist(box, ob)
            if 0.05 < d < gap_min and math.dist(it["pos"], o["pos"]) < 6:
                was = poly_dist(bbox_base, obb(B[o["id"]])) if bbox_base and o["id"] in B else None
                if was is None or d < was - 0.05:              # only gaps this change created or narrowed
                    out.append({"rule": "walkway_min" if gap_min == R["walkway_min"] else "aisle_laser_min",
                                "items": [iid, o["id"]], "value": round(d, 3), "where": it["pos"]})
        for w, rect in walls:
            pen = convex_overlap(box, rect)
            if pen > 0.01:
                out.append({"rule": "wall", "items": [iid, w["id"]], "value": round(pen, 3), "where": it["pos"]})
    seen, uniq = set(), []
    for v in out:
        k = (v["rule"], tuple(sorted(v["items"])))
        if k not in seen:
            seen.add(k); uniq.append(v)
    return uniq


def text_report(res):
    lines = [f"layout snapshot: base {res['base']} -> {res['target']}: {len(res['moves'])} moved, "
             f"{len(res['added'])} added, {len(res['removed'])} removed, {len(res['violations'])} rule notes"]
    for m in res["moves"]:
        if m.get("with"):
            lines.append(f"  {m['id']} moved with {m['with']}")
            continue
        dirn = direction(m["dx"], m["dy"])
        s = f"  {m['id']} moved {m['dist']:.2f} m" + (f" towards {dirn}" if dirn else "")
        if abs(m["drot"]) >= TOL_ROT:
            s += f", rotated {m['drot']:+.0f}°"
        if abs(m["dz"]) >= TOL_POS:
            s += f", height {m['dz']:+.2f} m"
        if m.get("zone_to") and m["zone_to"] != m.get("zone_from"):
            s += f", now in {m['zone_to']}"
        lines.append(s)
    for a in res["added"]:
        lines.append(f"  {a['id']} added at {a.get('pos')}")
    for r in res["removed"]:
        lines.append(f"  {r} removed")
    for v in res["violations"]:
        need = f" < {v['need']}" if v.get("need") else (" m overlap" if "need" in v else "")
        what = f" {v['what']}" if v.get("what") else ""
        lines.append(f"  ! {v['rule']}: {', '.join(v['items'])}{what} ({v['value']}{need})")
    for v in res.get("advisory", []):
        lines.append(f"  ~ advisory {v['rule']}: {', '.join(v['items'])} {v.get('what', '')} ({v['value']} < {v['need']})"
                     + (f" [{v['decision']}]" if v.get("decision") else ""))
    if res.get("review"):
        lines.append(f"  review notes ({len(res['review'])}): " + "; ".join(
            r["rule"] + (f" [{', '.join(r['items'][:3])}{'...' if len(r['items']) > 3 else ''}]" if r["items"] else "")
            for r in res["review"]))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="HEAD")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--blend"); g.add_argument("--yaml"); g.add_argument("--ref")
    g.add_argument("--live", action="store_true"); g.add_argument("--worktree", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--audit", action="store_true", help="also run the clearance policy over ALL items, not only moved ones")
    ap.add_argument("--write", action="store_true", help="write target poses into layout/layout.yaml")
    a = ap.parse_args()
    base = layout_io.loads(git_show(a.base))
    if a.yaml:
        target, tname = layout_io.load(a.yaml), a.yaml
    elif a.ref:
        target, tname = layout_io.loads(git_show(a.ref)), git_sha(a.ref)
    elif a.blend:
        target, tname = items_from_poses(base, blend_poses(a.blend)), os.path.basename(a.blend)
    elif a.live or (not a.worktree and socket_up()):
        target, tname = items_from_poses(base, live_poses()), "live Blender"
    else:
        target, tname = layout_io.load(YAML), "working tree"
    room = json.load(open(ROOM))
    cp = os.path.join(ROOT, "layout", "clearance_policy.json")
    if "clearance_policy" not in room.get("rules", {}) and os.path.exists(cp):
        room["rules"]["clearance_policy"] = json.load(open(cp))     # until the next layout_export run merges it
    moves, added, removed = diff(base, target)
    zone_of = lambda p: next((z["id"] for z in room["zones"] if in_poly(p, z["polygon"])), None)
    T = {it["id"]: it for it in target["items"]}
    mv = {m["id"]: m for m in moves}
    for m in moves:
        m["zone_to"] = zone_of(T[m["id"]]["pos"])
        host = T[m["id"]].get("on")
        if host in mv and abs(mv[host]["drot"] - m["drot"]) < 0.5:
            m["with"] = host                                  # carried by its parent (Blender parenting / planner)
    res = {"base": git_sha(a.base), "target": tname, "moves": moves, "added": added, "removed": removed,
           "violations": rules(base, target, room, moves, added)}
    changed = {m["id"] for m in moves} | {x["id"] for x in added}
    cl = layout_clearance.audit(target["items"], room, None if a.audit else changed)
    res["violations"] += cl["violations"]
    res["advisory"] = cl["advisory"]
    res["review"] = cl["review"] if a.audit else []
    if a.write:
        cur = layout_io.load(YAML)
        hdr = open(YAML).read().split("version:", 1)[0]
        for it in cur["items"]:
            t = T.get(it["id"])
            if t:
                it["pos"] = [round(t["pos"][0], 3), round(t["pos"][1], 3)]
                it["rot"], it["z"] = round(t.get("rot", 0), 1), round(t.get("z") or 0, 3)
        for m in moves:                                       # keep zone in step with where it now stands
            if m["zone_to"]:
                next(it for it in cur["items"] if it["id"] == m["id"])["zone"] = m["zone_to"]
        layout_io.save(cur, YAML, hdr)
    if a.json:
        for m in res["moves"]:
            m.pop("dx"); m.pop("dy")
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        print(text_report(res))


if __name__ == "__main__":
    main()
