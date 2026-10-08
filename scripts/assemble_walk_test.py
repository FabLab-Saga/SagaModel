"""Assemble renders/walk_test/*.jpg (every 3rd frame) into renders/walk_test.mp4 with placeholder
intro/outro cards and titles (ffmpeg drawtext; real titles come from fframes later).
    python3 scripts/assemble_walk_test.py [step]
Shot frame ranges + titles are read from scripts/build_walkthrough.py (SHOTS, FPS)."""
import ast, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
step = int(sys.argv[1]) if len(sys.argv) > 1 else 3
src = open(os.path.join(ROOT, "scripts/build_walkthrough.py")).read()
tree = ast.parse(src)
vals = {t.targets[0].id: ast.literal_eval(t.value) for t in tree.body
        if isinstance(t, ast.Assign) and isinstance(t.targets[0], ast.Name) and t.targets[0].id in ("SHOTS", "FPS")}
FPS, SHOTS = vals["FPS"], vals["SHOTS"]
BOLD = os.path.join(ROOT, "refs/branding/fonts/Roboto-Bold.ttf")
LIGHT = os.path.join(ROOT, "refs/branding/fonts/Roboto-Light.ttf")
INTRO, OUTRO = 4.0, 5.0
tmp = os.path.join(ROOT, "renders/walk_test_tmp"); os.makedirs(tmp, exist_ok=True)

def esc(s): return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\u2019").replace("%", "\\%")

def card(name, secs, lines):
    dt = ",".join(f"drawtext=fontfile={f}:text='{esc(t)}':fontcolor=white:fontsize={sz}:x=(w-text_w)/2:y={y}"
                  for f, t, sz, y in lines)
    out = os.path.join(tmp, name)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=black:s=640x360:r={FPS}:d={secs}",
                    "-vf", dt, "-c:v", "libx264", "-pix_fmt", "yuv420p", out], check=True)
    return out

intro = card("intro.mp4", INTRO, [(BOLD, "FAB LAB SAGA", 44, "(h-text_h)/2")])
outro = card("outro.mp4", OUTRO, [(BOLD, "FAB LAB SAGA", 36, "(h/2)-60"),
            (LIGHT, "HÍ Verkfræði- og náttúruvísindasvið  |  HÍ Menntavísindasvið  |  Reykjavík  |  Mixtúra", 13, "(h/2)+10")])
# body: titles 1 s after a shot starts, 3 s long; bold prefix + light name, lower left
f0, draws = 1, []
for name, secs, title, _ in SHOTS:
    t0 = (f0 - 1) / FPS
    if title:
        pre, _, nm = title.rpartition("// ")
        en = f"enable='between(t,{t0 + 1:.2f},{t0 + 4:.2f})'"
        if pre:
            draws.append(f"drawtext=fontfile={BOLD}:text='{esc(pre + '// ')}':fontcolor=white:fontsize=22:x=40:y=h-60:{en}")
            draws.append(f"drawtext=fontfile={LIGHT}:text='{esc(nm)}':fontcolor=white:fontsize=22:x=40+{len(pre + '// ') * 11.2:.0f}:y=h-60:{en}")
        else:
            draws.append(f"drawtext=fontfile={LIGHT}:text='{esc(nm)}':fontcolor=white:fontsize=22:x=40:y=h-60:{en}")
    draws.append(f"drawtext=fontfile={BOLD}:text='{esc(name)}':fontcolor=yellow@0.7:fontsize=12:x=w-tw-10:y=10:enable='between(t,{t0:.2f},{t0 + secs:.2f})'")
    f0 += round(secs * FPS)
body = os.path.join(tmp, "body.mp4")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS / step), "-pattern_type", "glob", "-i",
                os.path.join(ROOT, "renders/walk_test/f*.jpg"), "-vf", "fps=%d,%s" % (FPS, ",".join(draws)),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", body], check=True)
lst = os.path.join(tmp, "list.txt")
open(lst, "w").write("".join(f"file '{p}'\n" for p in (intro, body, outro)))
out = os.path.join(ROOT, "renders/walk_test.mp4")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
print(out)
