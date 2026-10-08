"""Quick GPU still from an ad-hoc viewpoint (no camera needed), into renders/tmp/<out>.png:
    blender -b SagaV2_work.blend --python scripts/peek.py -- ex ey ez  tx ty tz  out.png  [lens_mm]
e.g. the xTool close-up:  -- 31.15 23.95 1.40  32.20 23.38 1.0  xtool.png 35
"""
import sys

import bpy
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
eye, tgt, out = Vector(map(float, a[0:3])), Vector(map(float, a[3:6])), a[6]
sc = bpy.context.scene
prefs = bpy.context.preferences.addons["cycles"].preferences
for t in ("OPTIX", "CUDA", "HIP", "ONEAPI", "METAL"):
    try:
        prefs.compute_device_type = t
        prefs.get_devices()
        if any(d.type == t for d in prefs.devices):
            for d in prefs.devices:
                d.use = d.type == t
            sc.cycles.device = "GPU"
            break
    except TypeError:
        pass
sc.cycles.samples, sc.cycles.use_denoising = 32, True
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
cd = bpy.data.cameras.new("peek")
cd.lens = float(a[7]) if len(a) > 7 else 20
cam = bpy.data.objects.new("peek", cd)
sc.collection.objects.link(cam)
if "Ceiling_SlabRing" in bpy.data.objects:
    bpy.data.objects["Ceiling_SlabRing"].hide_render = True
cam.location = eye
cam.rotation_euler = (tgt - eye).to_track_quat("-Z", "Y").to_euler()
sc.camera = cam
sc.render.filepath = "//renders/tmp/" + out
bpy.ops.render.render(write_still=True)
