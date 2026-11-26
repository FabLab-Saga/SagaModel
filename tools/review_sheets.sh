#!/usr/bin/env bash
# Review pass in one go: render cameras (all Cam_* if none named) with render_cams.py, then tile them 6 per sheet
# into renders/tmp/sheets/review_<n>.png (labelled). Usage: tools/review_sheets.sh [Name ...]   (names without "Cam_")
set -euo pipefail
cd "$(dirname "$0")/.."
if [ $# -eq 0 ]; then
  set -- $(blender -b SagaV2_work.blend --python-expr 'import bpy; print("CAMS:"+" ".join(o.name[4:] for o in bpy.data.objects if o.type=="CAMERA" and o.name.startswith("Cam_")))' 2>/dev/null | grep -o 'CAMS:.*' | cut -d: -f2)
fi
rm -f renders/tmp/review/*.png
systemd-run --user --scope -q -p MemoryMax=14G blender -b SagaV2_work.blend --python scripts/render_cams.py -- "$@" >/dev/null 2>&1
python3 - "$@" <<'EOF'
import os, sys
from PIL import Image, ImageDraw, ImageFont
f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
names = [n for n in sys.argv[1:] if os.path.exists(f"renders/tmp/review/{n}.png")]
os.makedirs("renders/tmp/sheets", exist_ok=True)
for old in [x for x in os.listdir("renders/tmp/sheets") if x.startswith("review_")]:
    os.remove(f"renders/tmp/sheets/{old}")
for k in range(0, len(names), 6):
    sh = Image.new("RGB", (1280, 1080), "black")
    for i, n in enumerate(names[k:k + 6]):
        im = Image.open(f"renders/tmp/review/{n}.png").convert("RGB").resize((640, 360))
        d = ImageDraw.Draw(im); d.rectangle([0, 0, 12 + 14 * len(n), 30], fill="black"); d.text((6, 3), n, fill="yellow", font=f)
        sh.paste(im, ((i % 2) * 640, (i // 2) * 360))
    out = f"renders/tmp/sheets/review_{k // 6}.png"; sh.save(out); print(out)
print(len(names), "cameras")
EOF
