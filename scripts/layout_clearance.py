"""Clearance checks from room.json rules.clearance_policy (layout/clearance_policy.json; research proposal of
2026-11-25, merged by layout_export.py). Mechanical checks run on footprints; everything that needs inputs the
model doesn't have (face mapping, stock paths, ventilation, egress plans, door schedules) is a review note.

Used by layout_snapshot.py:  audit(items, room) -> {"violations": [...], "advisory": [...], "review": [...]}
A rule overridden in clearance_policy.overrides (e.g. Magnús accepting reduced ShopBot clearance) reports as
advisory with the decision quoted. No item is ever moved by this module."""
import math
import re

MECH = {"body_edge_offsets", "clear_height_from_deck", "nested_rectangles", "nested_rectangles_and_stock_sweep",
        "cabinet_internal_offsets"}


def _obb(it, pad=(0.0, 0.0)):
    (cx, cy), r = it["pos"], math.radians(it.get("rot") or 0)
    w, d = it["size"][0] / 2 + pad[0], it["size"][1] / 2 + pad[1]
    c, s = math.cos(r), math.sin(r)
    return [(cx + sx * w * c - sy * d * s, cy + sx * w * s + sy * d * c) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def _local(it, p):
    r = math.radians(it.get("rot") or 0); dx, dy = p[0] - it["pos"][0], p[1] - it["pos"][1]
    return (dx * math.cos(r) + dy * math.sin(r), -dx * math.sin(r) + dy * math.cos(r))


def _seg_pts(a, b, n=12):
    return [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]


def _z_overlap(a, b):
    za, zb = a.get("z") or 0, b.get("z") or 0
    return min(za + a["size"][2], zb + b["size"][2]) - max(za, zb) > 0.02


def side_gaps(it, obstacles):
    """Clear distance (m) from each footprint face of `it` to the nearest obstacle point in front of that face,
    within the face's span. Faces in the item's own frame: -y, +y, -x, +x. obstacles = list of point lists."""
    w, d = it["size"][0] / 2, it["size"][1] / 2
    gaps = {"-y": 9.9, "+y": 9.9, "-x": 9.9, "+x": 9.9}
    for pts in obstacles:
        for p in pts:
            u, v = _local(it, p)
            if abs(u) <= w + 0.01:
                if v < -d: gaps["-y"] = min(gaps["-y"], -d - v)
                if v > d: gaps["+y"] = min(gaps["+y"], v - d)
            if abs(v) <= d + 0.01:
                if u < -w: gaps["-x"] = min(gaps["-x"], -w - u)
                if u > w: gaps["+x"] = min(gaps["+x"], u - w)
    return gaps


def _obstacles(it, items, room):
    out = []
    for w in room["walls"]:
        out.append(_seg_pts(w["a"], w["b"], max(2, int(math.dist(w["a"], w["b"]) / 0.05))))
    for c in room["columns"]:
        out.append(_obb({"pos": c["pos"], "size": c["size"] + [1], "rot": 0}))
    for o in items:
        if o["id"] == it["id"] or not o.get("size") or o.get("on") == it["id"] or it.get("on") == o["id"]:
            continue
        if math.dist(o["pos"], it["pos"]) > 6 or not _z_overlap(o, it):
            continue
        pts = _obb(o)
        out.append([q for a, b in zip(pts, pts[1:] + pts[:1]) for q in _seg_pts(a, b, 8)])
    return out


def audit(items, room, only=None):
    pol = (room.get("rules") or {}).get("clearance_policy")
    res = {"violations": [], "advisory": [], "review": []}
    if not pol:
        return res
    ov = {o["rule"]: o for o in pol.get("overrides", [])}
    by_id = {it["id"]: it for it in items}
    for rule in pol["machine_clearances"]:
        pat = re.compile(rule["id_pattern"])
        hits = [it for it in items if pat.fullmatch(it["id"]) and it.get("size")]
        if only is not None:
            hits = [it for it in hits if it["id"] in only]
        status = ov.get(rule["id"], {}).get("status", rule["status"])
        if not hits:
            if only is None:
                res["review"].append({"rule": rule["id"], "items": [], "note": "selector matches no layout item"})
            continue
        if rule["check"] not in MECH:
            res["review"].append({"rule": rule["id"], "items": [h["id"] for h in hits], "check": rule["check"],
                                  "note": rule.get("applies_when", "")})
            continue
        P = rule.get("parameters") or {}
        for it in hits:
            found = []                                         # (value, need, label)
            if rule["check"] == "body_edge_offsets":
                g = side_gaps(it, _obstacles(it, items, room))
                side, fr, bk = rule.get("side_mm"), rule.get("front_mm"), rule.get("back_mm")
                if side is not None:
                    for f in ("-x", "+x"):
                        found.append((g[f], side / 1000, f"side {f}"))
                if fr is not None and bk is not None and fr == bk:
                    for f in ("-y", "+y"):
                        found.append((g[f], fr / 1000, f"front/back {f}"))
                elif fr is not None or bk is not None:
                    res["review"].append({"rule": rule["id"], "items": [it["id"]], "check": "face_mapping",
                                          "note": f"front {fr} / back {bk} mm need the verified operator front; "
                                                  f"gaps by own-frame face (m): {', '.join(f'{k} {v:.2f}' for k, v in g.items())}"})
            elif rule["check"] == "clear_height_from_deck":
                need = P.get("min_install_height_mm", 0) / 1000
                fp = _obb(it)
                above = [o for o in items if o["id"] != it["id"] and o.get("size") and (o.get("z") or 0) > (it.get("z") or 0) + 0.05
                         and any(abs(_local(it, q)[0]) < it["size"][0] / 2 and abs(_local(it, q)[1]) < it["size"][1] / 2
                                 for q in [o["pos"]] + _obb(o))]
                if above:
                    clear = min(o["z"] for o in above) - (it.get("z") or 0)
                    found.append((clear, need, "clear height to the item above (" + min(above, key=lambda o: o["z"])["id"] + ")"))
            elif rule["check"] == "cabinet_internal_offsets":
                top = P.get("top_mm")
                above = [o for o in items if o["id"] != it["id"] and o.get("on") != it["id"] and o.get("size") and (o.get("z") or 0) > (it.get("z") or 0) + 0.05
                         and abs(_local(it, o["pos"])[0]) < it["size"][0] / 2 and abs(_local(it, o["pos"])[1]) < it["size"][1] / 2]
                if top is not None and above:
                    gap = min(o["z"] for o in above) - ((it.get("z") or 0) + it["size"][2])
                    found.append((gap, top / 1000, "top gap to the cell above (cabin roof not modelled as an item; upper bound)"))
                res["review"].append({"rule": rule["id"], "items": [it["id"]], "check": "cabinet back/door",
                                      "note": "back and door offsets need the cabin geometry"})
            elif rule["check"].startswith("nested_rectangles"):
                zmin = P.get("min_support_z_mm")
                if zmin is not None:
                    found.append((it.get("z") or 0, zmin / 1000, "support height"))
                wx, wy = [v / 1000 for v in P.get("work_xy_mm", [0, 0])]
                env = _obb(it, ((wx - it["size"][0]) / 2, (wy - it["size"][1]) / 2)) if wx else None
                if env:
                    for o in hits:
                        if o["id"] <= it["id"]:
                            continue
                        envo = _obb(o, ((wx - o["size"][0]) / 2, (wy - o["size"][1]) / 2))
                        pen = _sat(env, envo)
                        if pen > 0.01:
                            res_entry = {"rule": rule["id"], "items": [it["id"], o["id"]], "value": round(pen, 3),
                                         "need": 0, "what": f"{wx * 1000:.0f} x {wy * 1000:.0f} mm work envelopes overlap "
                                         "(peer simultaneous use; fine if never run at the same time)", "where": it["pos"]}
                            _put(res, status, res_entry, ov.get(rule["id"]))
                if rule["check"].endswith("stock_sweep"):
                    res["review"].append({"rule": rule["id"], "items": [it["id"]], "check": "stock_sweep",
                                          "note": "material feed path front/back needs the operating position"})
            for val, need, label in found:
                if val + 1e-6 < need:
                    _put(res, status, {"rule": rule["id"], "items": [it["id"]], "value": round(val, 3),
                                       "need": round(need, 3), "what": label, "where": it["pos"]}, ov.get(rule["id"]))
    if only is None:
        for rc in pol["room_checks"]:
            if rc["check"] in ("connected_clear_width", "polygon_intrusion") and rc["id"] in ("project-aisles", "door-strips"):
                continue                                       # = walkway_min / keepout checks in layout_snapshot
            res["review"].append({"rule": rc["id"], "items": [], "check": rc["check"], "note": rc.get("title", "")})
    return res


def _put(res, status, entry, override):
    if override:
        entry["decision"] = f"{override['by']} {override['date']}: \"{override['quote']}\""
        res["advisory"].append(entry)
    elif status == "mandatory":
        res["violations"].append(entry)
    else:
        res["advisory"].append(entry)


def _axes(poly):
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        n = (y1 - y2, x2 - x1); l = math.hypot(*n) or 1
        yield (n[0] / l, n[1] / l)


def _sat(a, b):
    depth = 1e9
    for ax in list(_axes(a)) + list(_axes(b)):
        pa = [ax[0] * x + ax[1] * y for x, y in a]; pb = [ax[0] * x + ax[1] * y for x, y in b]
        o = min(max(pa), max(pb)) - max(min(pa), min(pb))
        if o <= 0:
            return 0.0
        depth = min(depth, o)
    return depth
