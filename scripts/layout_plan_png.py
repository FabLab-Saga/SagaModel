import json, math, sys
sys.path.insert(0, "scripts"); import layout_io
from PIL import Image, ImageDraw
room = json.load(open("layout/room.json")); lay = layout_io.load("layout/layout.yaml")
x0, x1, y0, y1 = 14.0, 35.5, 12.5, 39.5
S = 45
W, H = int((y1 - y0) * S), int((x1 - x0) * S)
im = Image.new("RGB", (W, H), "white"); dr = ImageDraw.Draw(im)
P = lambda x, y: ((y - y0) * S, (x - x0) * S)          # +Y right, +X down (SSW facade at the bottom)
for z in room["zones"]:
    dr.polygon([P(*p) for p in z["polygon"]], fill=None, outline=(200, 200, 255))
    cx = sum(p[0] for p in z["polygon"]) / len(z["polygon"]); cy = sum(p[1] for p in z["polygon"]) / len(z["polygon"])
    dr.text(P(cx, cy), z["id"], fill=(120, 120, 255))
for k in room["keepout"]:
    dr.polygon([P(*p) for p in k["polygon"]], outline=(255, 150, 0))
col = {"wall": (0, 0, 0), "glazing": (0, 150, 255), "glass-partition": (0, 200, 120)}
for w in room["walls"]:
    dr.line([P(*w["a"]), P(*w["b"])], fill=col[w["kind"]], width=max(1, int(w["t"] * S)))
for c in room["columns"]:
    x, y = c["pos"]; r = c["size"][0] / 2 * S
    a, b = P(x, y); dr.ellipse([a - r, b - r, a + r, b + r], outline=(120, 0, 0), width=2)
for d in room["doors"]:
    dr.line([P(*d["a"]), P(*d["b"])], fill=(255, 0, 0), width=4)
kc = {"machine": (220, 0, 0), "furniture": (120, 70, 20), "storage": (0, 110, 0), "fixture": (130, 130, 130)}
for it in lay["items"]:
    if it.get("on"): c = (255, 120, 120)
    else: c = kc[it["kind"]]
    (cx, cy), r = it["pos"], math.radians(it["rot"]); w, d = it["size"][0] / 2, it["size"][1] / 2
    pts = [(cx + sx * w * math.cos(r) - sy * d * math.sin(r), cy + sx * w * math.sin(r) + sy * d * math.cos(r)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    dr.polygon([P(*p) for p in pts], outline=c)
for gx in range(15, 35):
    dr.text(P(gx, y0 + 0.05), f"x{gx}", fill=(160, 160, 160))
for gy in range(13, 40):
    dr.text(P(x0 + 0.05, gy), f"y{gy}", fill=(160, 160, 160))
im.save(sys.argv[1])
