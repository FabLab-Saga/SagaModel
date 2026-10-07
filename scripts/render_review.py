"""Quick review renders of all cameras in the LIVE Blender (via MCP exec), same rules as
render_finals.py (cutaway hides ceiling/services and shows the ground; per-camera
exposure_offset). Writes renders/tmp/review_<cam>.png and renders/tmp/review.png (3x3 sheet).
"""
import bpy

CAMS = ["Cam_Cutaway", "Cam_Entrance", "Cam_Micro", "Cam_FeltWall", "Cam_Mural",
        "Cam_CNCRoom", "Cam_PrintFarm", "Cam_WorkshopLong", "Cam_Craft"]
OUT = bpy.path.abspath("//renders/tmp/")
sc = bpy.context.scene
res = (sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples)
sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples = 960, 540, 12   # fast: denoiser does the rest
cut = [bpy.data.objects["Ceiling_Slab"]] + list(bpy.data.collections["Services"].objects) + \
      [o for o in bpy.data.collections["Signs"].objects if o.name.endswith("_Cables")]
ground = [bpy.data.objects[n] for n in ("Ground_Paving", "Ground_Grass", "Ceiling_SlabRing") if n in bpy.data.objects]
base = sc.view_settings.exposure
for c in CAMS:
    top = c == "Cam_Cutaway"
    for o in cut:
        o.hide_render = top
    for o in ground:
        o.hide_render = not top
    sc.camera = bpy.data.objects[c]
    sc.view_settings.exposure = base + sc.camera.get("exposure_offset", 0.0)
    sc.render.filepath = OUT + f"review_{c}.png"
    bpy.ops.render.render(write_still=True)
for o in cut:
    o.hide_render = False
for o in ground:
    o.hide_render = True
sc.view_settings.exposure = base
sc.render.resolution_x, sc.render.resolution_y, sc.cycles.samples = res

sheet = bpy.data.images.new("review_sheet", 1920, 1080)
px = [0.0] * (1920 * 1080 * 4)
for k, c in enumerate(CAMS):
    im = bpy.data.images.load(OUT + f"review_{c}.png", check_existing=False)
    im.scale(640, 360)
    src = im.pixels[:]
    ox, oy = (k % 3) * 640, (2 - k // 3) * 360
    for y in range(360):
        row = ((oy + y) * 1920 + ox) * 4
        px[row:row + 640 * 4] = src[y * 640 * 4:(y + 1) * 640 * 4]
    bpy.data.images.remove(im)
sheet.pixels = px
sheet.filepath_raw = OUT + "review.png"
sheet.file_format = "PNG"
sheet.save()
bpy.data.images.remove(sheet)
print("review done")
