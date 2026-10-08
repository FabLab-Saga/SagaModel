"""Quick-and-dirty animatic of the walkthrough (scripts/build_walkthrough.py) for timing/framing review.
    blender -b SagaV2_work.blend --python scripts/render_walk_test.py -- [step] [first] [last]
Renders every <step>-th frame at 640x360, 8 spp, OptiX denoiser, persistent data, into renders/walk_test/.
Assemble with scripts/assemble_walk_test.sh.
"""
import os
import sys
import time

import bpy

a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
step = int(a[0]) if a else 3
sc = bpy.context.scene
first = int(a[1]) if len(a) > 1 else sc.frame_start
last = int(a[2]) if len(a) > 2 else sc.frame_end
p = bpy.context.preferences.addons["cycles"].preferences
p.compute_device_type = "OPTIX"
p.get_devices()
for d in p.devices:
    d.use = d.type == "OPTIX"
sc.cycles.device = "GPU"
sc.cycles.samples, sc.cycles.use_denoising, sc.cycles.denoiser = 8, True, "OPTIX"
sc.cycles.use_adaptive_sampling = False
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 640, 360, 100
sc.render.use_persistent_data = True
sc.render.image_settings.file_format = "JPEG"
out = os.path.join(bpy.path.abspath("//"), "renders/walk_test")
os.makedirs(out, exist_ok=True)
t0 = time.time()
n = 0
for f in range(first, last + 1, step):
    sc.frame_set(f)
    sc.render.filepath = os.path.join(out, f"f{f:05d}.jpg")
    bpy.ops.render.render(write_still=True)
    n += 1
print(f"WALKTEST {n} frames in {time.time() - t0:.1f} s ({(time.time() - t0) / max(n, 1):.2f} s/frame)")
