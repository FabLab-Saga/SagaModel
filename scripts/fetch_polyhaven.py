"""Download CC0 PBR textures from Poly Haven (api.polyhaven.com) into assets/polyhaven/<id>/.

Usage: python3 scripts/fetch_polyhaven.py [res] id [id ...]
Writes diff/nor_gl/rough(/disp) as jpg (png when jpg is not offered) and info.json
(with the real-world size in mm, used for texture scale in Blender).
"""
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "assets" / "polyhaven"
UA = {"User-Agent": "SagaModel/1.0 (Fab Lab SAGA reference renders)"}
MAPS = {"Diffuse": "diff", "nor_gl": "nor_gl", "Rough": "rough", "Displacement": "disp"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read()


def fetch(asset, res="2k"):
    out = ROOT / asset
    out.mkdir(parents=True, exist_ok=True)
    info = json.loads(get(f"https://api.polyhaven.com/info/{asset}"))
    files = json.loads(get(f"https://api.polyhaven.com/files/{asset}"))
    (out / "info.json").write_text(json.dumps({"id": asset, "name": info.get("name"), "dimensions_mm": info.get("dimensions"),
                                                "license": "CC0", "source": f"https://polyhaven.com/a/{asset}"}, indent=1))
    got = []
    for key, short in MAPS.items():
        entry = files.get(key, {}).get(res)
        if not entry:
            continue
        fmt = "jpg" if "jpg" in entry else "png"
        dst = out / f"{short}.{fmt}"
        if not dst.exists():
            dst.write_bytes(get(entry[fmt]["url"]))
        got.append(dst.name)
    return got


if __name__ == "__main__":
    args = sys.argv[1:]
    res = args.pop(0) if args and args[0].endswith("k") else "2k"
    for a in args:
        print(a, fetch(a, res), flush=True)
