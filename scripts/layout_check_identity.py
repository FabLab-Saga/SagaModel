"""Identity check: apply layout.yaml to the scene and compare every object's world matrix before/after.
Run: blender -b SagaV2_work.blend --python scripts/layout_check_identity.py [-- --move ID DX DY DROT]
Prints max position (mm) and rotation (deg) deviation over all objects; with --move, first edits the item in
memory and reports which objects moved and by how much (expected: only that item's objects)."""
import json
import math
import os
import sys

import bpy

ROOT = os.environ.get("SAGA_ROOT") or bpy.path.abspath("//")
L = {}
exec(open(os.path.join(ROOT, "scripts", "layout_blender.py")).read(), L)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
data = L["load"]()
if "--move" in argv:
    i = argv.index("--move")
    iid, dx, dy, dr = argv[i + 1], float(argv[i + 2]), float(argv[i + 3]), float(argv[i + 4])
    it = next(x for x in data["items"] if x["id"] == iid)
    it["pos"] = [it["pos"][0] + dx, it["pos"][1] + dy]
    it["rot"] = it["rot"] + dr
from mathutils import Vector
def gcentre(o):
    if o.type not in {"MESH", "CURVE", "FONT"}:
        return o.matrix_world.translation.copy()
    return sum((o.matrix_world @ Vector(c) for c in o.bound_box), Vector()) / 8
before = {o.name: o.matrix_world.copy() for o in bpy.data.objects}
gbefore = {o.name: gcentre(o) for o in bpy.data.objects}
moved = L["apply"](data=data, verbose=False)
bpy.context.view_layer.update()
worst_p = worst_r = 0.0
changed = []
for o in bpy.data.objects:
    a, b = before[o.name], o.matrix_world
    dp = (gbefore[o.name] - gcentre(o)).length                     # geometric centre, not origin
    dr = math.degrees((a.to_quaternion().rotation_difference(b.to_quaternion())).angle)
    dr = min(dr, 360.0 - dr)
    worst_p, worst_r = max(worst_p, dp), max(worst_r, dr)
    if dp > 1e-6 or dr > 1e-4:
        changed.append((o.name, round(dp * 1000, 2), round(dr, 3)))
res = {"items_moved": moved, "objects_changed": len(changed), "max_mm": round(worst_p * 1000, 4),
       "max_deg": round(worst_r, 5), "sample": changed[:8], "objects_total": len(before)}
if "--move" in argv:
    moved_names = {n for n, _, _ in changed}
    res["moved_objects_belong_to_item"] = all(any(n == r or n.startswith(r + "_") or n.startswith(r + ".")
                                                  for r in it["objects"]) for n in moved_names if n)
    after = L["poses"](data=data)[iid]
    res["target"] = {"pos": it["pos"], "rot": it["rot"]}
    res["measured_after"] = after
print("IDENTITY " + json.dumps(res))
