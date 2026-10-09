"""Final-quality render of the walkthrough (scripts/build_walkthrough.py) as a PNG sequence.
    blender -b SagaV2_work.blend --python scripts/render_walk_final.py -- <first> <last> [tag]
Env: SAGA_SPP (default 64), SAGA_DENOISER (OPTIX | OPENIMAGEDENOISE, default OPENIMAGEDENOISE),
SAGA_RES (default 100 = 1920x1080). Output: renders/walk/<tag>/f#####.png (existing frames are skipped, so a crashed
overnight run resumes where it stopped). Motion blur on (shutter 0.5 frame), persistent data, OptiX device.
"""
import os
import sys
import time

import bpy

a = sys.argv[sys.argv.index("--") + 1:]
sc = bpy.context.scene
for _g in ("Ground_Paving", "Ground_Grass"):                   # real ground: the HDRI ground is a static picture
    if _g in bpy.data.objects:                                  # at infinity (no parallax through glass, huge in the cutaway)
        bpy.data.objects[_g].hide_render = False
first, last = int(a[0]), int(a[1])
tag = a[2] if len(a) > 2 else "final"
p = bpy.context.preferences.addons["cycles"].preferences
p.compute_device_type = "OPTIX"
p.get_devices()
for d in p.devices:
    d.use = d.type == "OPTIX"
sc.render.engine = "CYCLES"
sc.cycles.device = "GPU"
sc.cycles.samples = int(os.environ.get("SAGA_SPP", "64"))
sc.cycles.use_adaptive_sampling = True
sc.cycles.adaptive_threshold = 0.015
sc.cycles.use_denoising = True
sc.cycles.denoiser = os.environ.get("SAGA_DENOISER", "OPENIMAGEDENOISE")
sc.cycles.seed, sc.cycles.use_animated_seed = 0, True
sc.render.use_motion_blur, sc.render.motion_blur_shutter = True, 0.5
sc.render.use_persistent_data = True
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.render.resolution_percentage = int(os.environ.get("SAGA_RES", "100"))
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_depth = "8"
out = os.path.join(bpy.path.abspath("//"), "renders/walk", tag)
os.makedirs(out, exist_ok=True)
t0, n = time.time(), 0
for f in range(first, last + 1):
    path = os.path.join(out, f"f{f:05d}.png")
    if os.path.exists(path):
        continue
    sc.frame_set(f)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    n += 1
    if n % 25 == 0:
        print(f"WALKFINAL {f} ({(time.time() - t0) / n:.1f} s/frame)", flush=True)
print(f"WALKFINAL done {n} frames in {time.time() - t0:.0f} s ({(time.time() - t0) / max(n, 1):.1f} s/frame)", flush=True)
