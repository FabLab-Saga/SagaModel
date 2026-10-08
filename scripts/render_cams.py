"""Fast GPU review renders of any cameras (1280x720, 32 spp, denoised) into renders/tmp/review/<Name>.png.
    blender -b SagaV2_work.blend --python scripts/render_cams.py -- Bank LaserRoom   # names without "Cam_"
    blender -b SagaV2_work.blend --python scripts/render_cams.py                     # all cameras (~5 s each)
Same per-camera rules as render_finals.py (exposure_offset, show_ground, cutaway hides slab/services/fixtures).
"""
import sys
import time

import bpy

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
ground = [bpy.data.objects[n] for n in ("Ground_Paving", "Ground_Grass", "Ceiling_SlabRing") if n in bpy.data.objects]
cut = [bpy.data.objects["Ceiling_Slab"]] + list(bpy.data.collections["Services"].objects) + \
      [o for o in bpy.data.collections["Signs"].objects if o.name.endswith("_Cables")] + \
      [o for o in bpy.data.collections["Lighting"].objects if o.type == "MESH"]
base = sc.view_settings.exposure
want = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
for cam in sorted((o for o in bpy.data.objects if o.type == "CAMERA" and (not want or o.name[4:] in want)), key=lambda o: o.name):
    is_cut = cam.name == "Cam_Cutaway"
    for o in cut:
        o.hide_render = is_cut
    for o in ground:
        o.hide_render = not (is_cut or cam.get("show_ground", False))
    sc.camera = cam
    sc.view_settings.exposure = base + cam.get("exposure_offset", 0.0)
    sc.render.filepath = f"//renders/tmp/review/{cam.name[4:]}.png"
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print("DONE", cam.name, round(time.time() - t), flush=True)
