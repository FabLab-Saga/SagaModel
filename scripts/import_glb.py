"""Import an openskp GLB into a fresh Blender scene and fix it up:

- rescale mm -> m (openskp writes millimetres, glTF/Blender assume metres)
- restore SketchUp names (openskp emits n0, n0_g0, ...; node nI is the I-th
  node of a depth-first walk of the metadata's scene_hierarchy)
- put objects into one collection per SketchUp tag

Then save a .blend and render a quick preview.

Usage: blender -b --factory-startup --python scripts/import_glb.py -- \
           in.glb in_metadata.json out.blend preview.png
"""
import json
import math
import re
import sys

import bpy
from mathutils import Vector

glb, meta_path, blend, png = sys.argv[sys.argv.index("--") + 1:]
MM = 0.001

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
scene = bpy.context.scene

# --- metadata ------------------------------------------------------------
meta = json.load(open(meta_path))
flat = []
def walk(node):
    flat.append(node)
    for child in node["children"]:
        walk(child)
walk(meta["scene_hierarchy"])
res_def = {r["id"]: r["definition_name"] for r in meta["mesh_resources"]}

# --- scale: translations and (shared) mesh data, so instancing survives ----
for ob in scene.objects:
    ob.location *= MM
for me in {ob.data for ob in scene.objects if ob.type == "MESH"}:
    me.transform([[MM, 0, 0, 0], [0, MM, 0, 0], [0, 0, MM, 0], [0, 0, 0, 1]])

# --- tags -> collections ---------------------------------------------------
tag_cols = {}
def tag_collection(tag):
    label = "Untagged" if tag in ("Layer0", "DEFAULT") else tag
    if label not in tag_cols:
        col = bpy.data.collections.new(label)
        scene.collection.children.link(col)
        col.hide_viewport = col.hide_render = meta["layer_hidden"].get(tag, False)
        tag_cols[label] = col
    return tag_cols[label]

def move_to(ob, col):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    col.objects.link(ob)

# SketchUp: geometry on Layer0 inherits its parent's tag
node_tag = {}
def resolve_tags(node, inherited):
    tag = node["layer"] if node["layer"] not in ("Layer0", "DEFAULT") else inherited
    node_tag[id(node)] = tag
    for child in node["children"]:
        resolve_tags(child, tag)
resolve_tags(meta["scene_hierarchy"], "Layer0")

# --- rename ----------------------------------------------------------------
objs = {ob.name: ob for ob in scene.objects}
for i, node in enumerate(flat):
    ob = objs.get(f"n{i}")
    if ob is None:
        continue
    label = node["name"] or node["definition_name"]
    ob.name = label
    col = tag_collection(node_tag[id(node)])
    move_to(ob, col)
    for child in list(ob.children):
        m = re.fullmatch(rf"n{i}_g(\d+)", child.name)
        if not m:
            continue
        child.name = f"{label}.geo{m.group(1)}"
        move_to(child, col)
        if child.type == "MESH":
            res = child.data.name.rsplit("_", 1)[0]
            if res in res_def and not child.data.get("skp_named"):
                child.data.name = f"{res_def[res]}_{child.data.name.rsplit('_', 1)[1]}"
                child.data["skp_named"] = True
for ob in list(scene.collection.objects):
    move_to(ob, tag_collection("Layer0"))

bpy.context.view_layer.update()

# glTF importer sizes empties from node scale; some come out tens of metres
for ob in scene.objects:
    if ob.type == "EMPTY":
        ob.empty_display_size = 0.05 / max(max(abs(v) for v in ob.matrix_world.to_scale()), 1e-6)

# --- stats -----------------------------------------------------------------
meshes = [o for o in scene.objects if o.type == "MESH"]
pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = Vector([min(p[k] for p in pts) for k in range(3)])
hi = Vector([max(p[k] for p in pts) for k in range(3)])
size, centre = hi - lo, (hi + lo) / 2
print(f"STATS objects={len(scene.objects)} meshes={len(meshes)} "
      f"unique_meshes={len({o.data for o in meshes})} materials={len(bpy.data.materials)} "
      f"images={len(bpy.data.images)} size_m={tuple(round(v, 2) for v in size)} "
      f"collections={[c.name for c in tag_cols.values()]}")

# --- preview -----------------------------------------------------------------
cam = bpy.data.objects.new("PreviewCam", bpy.data.cameras.new("PreviewCam"))
scene.collection.objects.link(cam)
scene.camera = cam
d = max(size) * 0.75
cam.location = centre + Vector((d * 0.6, -d * 0.9, d * 0.8))
cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.clip_end = d * 10
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 3
sun.rotation_euler = (math.radians(40), 0, math.radians(30))
scene.collection.objects.link(sun)
world = bpy.data.worlds.new("World")
world.color = (0.8, 0.8, 0.8)
scene.world = world
scene.unit_settings.system = "METRIC"
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_shadows = True
scene.render.resolution_x, scene.render.resolution_y = 1600, 1000
scene.render.filepath = png
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=blend)
