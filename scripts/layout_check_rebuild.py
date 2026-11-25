"""Rebuild acceptance: run the item builders (CLAUDE.md order) on the open .blend, then compare every object's
world transform with the state before. Never saves. Run:
    blender -b SagaV2_work.blend --python scripts/layout_check_rebuild.py [-- --only build_worktables,build_life]
Prints REBUILD {json}: objects compared/missing/new, max geometric-centre deviation (mm), max rotation (deg),
the worst objects, and which builders failed."""
import json
import math
import os
import sys
import traceback

import bpy
from mathutils import Vector

ROOT = bpy.path.abspath("//")
ORDER = ["build_machines", "build_print_farm", "build_laser_room", "build_bank_lounge", "build_sofas",
         "build_craft_spine", "build_worktables", "build_life", "build_microelectronics", "build_felt_dividers", "build_textile",
         "build_bank_walls", "build_cupboard", "build_material_storage", "build_welcome", "build_staff_area",
         "build_cnc_room"]
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if "--only" in argv:
    ORDER = argv[argv.index("--only") + 1].split(",")


def state():
    out = {}
    for o in bpy.data.objects:
        if o.type in {"MESH", "CURVE", "FONT"}:
            c = sum((o.matrix_world @ Vector(v) for v in o.bound_box), Vector()) / 8
        else:
            c = o.matrix_world.translation.copy()
        out[o.name] = (c, o.matrix_world.to_quaternion())
    return out


L = {}
exec(open(os.path.join(ROOT, "scripts", "layout_blender.py")).read(), L)
L["apply"](verbose=False)                                   # the file as Magnús will have it (parented, applied)
bpy.context.view_layer.update()
before = state()
failed = []
for n in ORDER:
    try:
        g = {"__name__": "__main__", "__file__": os.path.join(ROOT, "scripts", n + ".py")}
        exec(compile(open(g["__file__"]).read(), g["__file__"], "exec"), g)
        bpy.context.view_layer.update()
    except Exception as e:
        failed.append((n, repr(e)[:200]))
        traceback.print_exc()
after = state()
common = [k for k in before if k in after]
dev = []
for k in common:
    (c0, q0), (c1, q1) = before[k], after[k]
    dp = (c0 - c1).length
    a = math.degrees(q0.rotation_difference(q1).angle); a = min(a, 360 - a)
    dev.append((dp, a, k))
dev.sort(reverse=True)
res = {"builders": ORDER, "failed": failed, "objects_before": len(before), "objects_after": len(after),
       "compared": len(common), "missing_after": sorted(set(before) - set(after))[:15],
       "new_after": sorted(set(after) - set(before))[:15],
       "max_mm": round(dev[0][0] * 1000, 3) if dev else 0, "max_deg": round(max(d[1] for d in dev), 4) if dev else 0,
       "over_1mm_or_0.1deg": sum(1 for d in dev if d[0] > 0.001 or d[1] > 0.1),
       "worst": [(k, round(p * 1000, 2), round(a, 3)) for p, a, k in dev[:10]]}
P = L["poses"]()
dev_p = []
for it in L["load"]()["items"]:
    p = P.get(it["id"])
    if not p or p.get("missing"):
        continue
    dp = math.hypot(p["pos"][0] - it["pos"][0], p["pos"][1] - it["pos"][1])
    dr = abs((p["rot"] - it.get("rot", 0) + 180) % 360 - 180)
    dev_p.append((round(dp * 1000, 3), round(dr, 3), it["id"]))
dev_p.sort(reverse=True)
res["pose_vs_layout_worst"] = dev_p[:3]                      # measured item pose vs layout.yaml after the rebuild
print("REBUILD " + json.dumps(res))
