"""Fast flat-shaded draft of the whole walkthrough at 1920x1080 (Workbench via OpenGL viewport rendering: no path
tracing, ~0.15 s/frame). Needs a display, so it starts its OWN windowed Blender (the user's GUI session is untouched):
    DISPLAY=:0 blender SagaV2_work.blend --python scripts/render_walk_flat.py
Writes renders/walk_flat/f####.jpg (git-ignored) and quits. Assemble with:
    /usr/bin/python3 scripts/assemble_film.py renders/walk_flat renders/walk_flat.mp4
Background mode (-b) can't do OpenGL renders; Workbench F12 renders in -b work but take ~1 s/frame.
"""
import os
import time

import bpy


def run():
    sc = bpy.context.scene
    for _g in ("Ground_Paving", "Ground_Grass"):                   # real ground: the HDRI ground is a static picture
        if _g in bpy.data.objects:                                  # at infinity (no parallax through glass, huge in the cutaway)
            bpy.data.objects[_g].hide_render = False
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light, sh.color_type = "STUDIO", "MATERIAL"
    sh.show_shadows, sh.show_cavity, sh.cavity_type = True, True, "BOTH"
    sc.view_settings.view_transform, sc.view_settings.look, sc.view_settings.exposure = "Standard", "None", 0.5
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
    sc.display.render_aa = "8"
    for o in sc.objects:                                   # boolean cutters + other render-hidden helpers
        if o.hide_render:
            o.hide_viewport = True
    out = os.path.join(bpy.path.abspath("//"), "renders/walk_flat")
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        os.remove(os.path.join(out, f))
    sc.render.image_settings.file_format, sc.render.image_settings.quality = "JPEG", 92
    sc.render.filepath = os.path.join(out, "f")
    sc.frame_step = 1
    t = time.time()
    with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
        bpy.ops.render.opengl(animation=True, view_context=False)
    n = sc.frame_end - sc.frame_start + 1
    print(f"WALKFLAT {n} frames in {time.time() - t:.0f} s ({(time.time() - t) / n:.3f} s/frame)", flush=True)
    bpy.ops.wm.quit_blender()                             # never saves: draft settings stay out of the work file


bpy.app.timers.register(run, first_interval=3)
