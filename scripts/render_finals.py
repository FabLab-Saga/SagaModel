"""Final stills. Run headless on the saved work file:
    blender -b SagaV2_work.blend --python scripts/render_finals.py -- [shot ...]
Writes renders/final/NN_<shot>.png at 1920x1080 (Cycles, adaptive, denoised).
The cutaway hides the ceiling slab, hanging services and sign cables for that shot only.
"""
import sys
import time

import bpy

SHOTS = [  # (file name, camera)
    ("01_cutaway_overview", "Cam_Cutaway"),
    ("02_entrance_lounge", "Cam_Entrance"),
    ("03_workshop_toolwall", "Cam_Workshop"),
    ("04_benches_feltwall", "Cam_FeltWall"),
    ("05_mural_printfarm", "Cam_Mural"),
    ("06_laser_room", "Cam_LaserRoom"),
    ("07_print_farm", "Cam_PrintFarm"),
    ("08_equipment_bank", "Cam_Bank"),
    ("09_craft_zone", "Cam_Craft"),
]
SHOTS += sorted(((f"{int(o['shot_order']):02d}_{o.name[4:].lower()}", o.name) for o in bpy.data.objects
                 if o.type == "CAMERA" and "shot_order" in o), key=lambda s: s[0])
want = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
sc = bpy.context.scene
sc.render.engine = "CYCLES"
def _pick_device():
    """Use the fastest GPU backend available (OptiX > CUDA > HIP > oneAPI > Metal), else CPU.
    Override with SAGA_DEVICE=CPU|OPTIX|CUDA|HIP|ONEAPI|METAL."""
    import os
    prefs = bpy.context.preferences.addons["cycles"].preferences
    order = [os.environ["SAGA_DEVICE"]] if "SAGA_DEVICE" in os.environ else ["OPTIX", "CUDA", "HIP", "ONEAPI", "METAL"]
    for t in order:
        if t == "CPU":
            break
        try:
            prefs.compute_device_type = t
            prefs.get_devices()
            devs = [d for d in prefs.devices if d.type == t]
            if devs:
                for d in prefs.devices:
                    d.use = d.type == t
                print("RENDER DEVICE:", t, [d.name for d in devs], flush=True)
                return "GPU"
        except Exception:
            pass
    print("RENDER DEVICE: CPU", flush=True)
    return "CPU"


sc.cycles.device = _pick_device()
sc.cycles.samples = int(__import__("os").environ.get("SAGA_SPP", "40"))
sc.cycles.use_adaptive_sampling = True
sc.cycles.adaptive_threshold = 0.015
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
sc.render.image_settings.file_format = "PNG"
cut_hide = [bpy.data.objects["Ceiling_Slab"]] + list(bpy.data.collections["Services"].objects) + \
           [o for o in bpy.data.collections["Signs"].objects if o.name.endswith("_Cables")] + \
           [o for o in bpy.data.collections["Lighting"].objects if o.type == "MESH"]    # fixtures (their light stays)
ground = [bpy.data.objects[n] for n in ("Ground_Paving", "Ground_Grass", "Ceiling_SlabRing") if n in bpy.data.objects]
base_exposure = sc.view_settings.exposure
for name, cam in SHOTS:
    if want and name not in want and cam not in want:
        continue
    t = time.time()
    for o in cut_hide:
        o.hide_render = name.startswith("01_")
    for o in ground:                                  # real ground only from above / outside
        o.hide_render = not (name.startswith("01_") or bpy.data.objects[cam].get("show_ground", False))
    sc.camera = bpy.data.objects[cam]
    sc.view_settings.exposure = base_exposure + sc.camera.get("exposure_offset", 0.0)
    sc.render.filepath = bpy.path.abspath(f"//renders/{__import__('os').environ.get('SAGA_OUT', 'final')}/{name}.png")
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED {name} in {time.time() - t:.0f} s", flush=True)
for o in cut_hide:
    o.hide_render = False
sc.view_settings.exposure = base_exposure
