"""Assemble the walkthrough animatic: renders/walk_test/f*.jpg + placeholder intro/outro cards and titles
(ffmpeg drawtext; final titles come from fframes) + the music, into renders/walk_test.mp4.
    /usr/bin/python3 scripts/assemble_walk_test.py [step]      (system python: needs Pillow for text widths)
Shot timing/titles are read from scripts/build_walkthrough.py (SHOTS, FPS, INTRO_BARS).
Music: CC0 "Stairwell Harmony" (Amarent), window from MUSIC_IN, 90.2 s, fades.
"""
import ast
import os
import subprocess
import sys

from PIL import ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
step = int(sys.argv[1]) if len(sys.argv) > 1 else 1
MUSIC = os.path.expanduser("~/Documents/AgentWork/saga-video/music/1_Amarent_-_Stairwell_Harmony.mp3")
MUSIC_IN, FILM = 25.57, 90.2

src = ast.parse(open(os.path.join(ROOT, "scripts/build_walkthrough.py")).read())
V = {}
for t in src.body:
    if isinstance(t, ast.Assign) and isinstance(t.targets[0], ast.Name) and t.targets[0].id in ("SHOTS", "FPS", "INTRO_BARS"):
        V[t.targets[0].id] = ast.literal_eval(t.value)
FPS, SHOTS, INTRO_BARS = V["FPS"], V["SHOTS"], V["INTRO_BARS"]
BAR = 4 * 60 / 103.36
W, H = 640, 360
K = H / 1080                                           # scale the manual's 1080p sizes to the test size
BOLD = os.path.join(ROOT, "refs/branding/fonts/Roboto-Bold.ttf")
LIGHT = os.path.join(ROOT, "refs/branding/fonts/Roboto-Light.ttf")
TS = round(47 * 1.333 * K)                             # ~47 pt title at 1080p (manual p.56)
tmp = os.path.join(ROOT, "renders/walk_test_tmp")
os.makedirs(tmp, exist_ok=True)


def esc(s):
    return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\u2019").replace("%", "\\%")


def run(args):
    subprocess.run(["ffmpeg", "-y", "-v", "error"] + args, check=True)


def card(name, secs, lines, fade_out):
    dt = ",".join(f"drawtext=fontfile={f}:text='{esc(t)}':fontcolor=white:fontsize={sz}:x=(w-text_w)/2:y={y}"
                  for f, t, sz, y in lines)
    fades = "fade=in:st=0:d=0.6" + (f",fade=out:st={secs - 0.4:.3f}:d=0.4" if fade_out else "")
    out = os.path.join(tmp, name)
    run(["-f", "lavfi", "-i", f"color=black:s={W}x{H}:r={FPS}:d={secs:.3f}", "-vf", f"{dt},{fades}",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", out])
    return out


intro_s = INTRO_BARS * BAR
body_frames = round(sum(s[1] for s in SHOTS) * BAR * FPS)
outro_s = FILM - intro_s - body_frames / FPS
intro = card("intro.mp4", intro_s, [(BOLD, "FAB LAB SAGA", 34, "(h-text_h)/2")], True)
outro = card("outro.mp4", outro_s, [
    (BOLD, "FAB LAB SAGA", 30, "(h/2)-50"),
    (LIGHT, "HÍ Verkfræði- og náttúruvísindasvið  |  HÍ Menntavísindasvið  |  Reykjavík  |  Mixtúra", 13, "(h/2)+10")],
    False)

fb = ImageFont.truetype(BOLD, TS)
x0, y0 = round(65 * W / 1920), H - round(110 * K)       # manual: 65 px margins at 1080p
draws, b = [], 0
for name, bars, title, *_ in SHOTS:
    t0 = b * BAR
    if title:
        pre, sep, nm = title.rpartition("// ")
        en = f"enable='between(t,{t0 + 0.6:.2f},{t0 + bars * BAR - 0.4:.2f})'"
        x = x0
        if sep:
            draws.append(f"drawtext=fontfile={BOLD}:text='{esc(pre + sep)}':fontcolor=white:fontsize={TS}:x={x}:y={y0}:{en}")
            x += round(fb.getlength(pre + sep))
        draws.append(f"drawtext=fontfile={LIGHT}:text='{esc(nm)}':fontcolor=white:fontsize={TS}:x={x}:y={y0}:{en}")
    draws.append(f"drawtext=fontfile={BOLD}:text='{esc(name)}':fontcolor=yellow@0.6:fontsize=11:x=w-tw-8:y=8:"
                 f"enable='between(t,{t0:.2f},{t0 + bars * BAR:.2f})'")
    b += bars
draws.append(f"drawtext=fontfile={BOLD}:text='FAB LAB SAGA':fontcolor=white@0.9:fontsize={round(TS * 0.8)}:x=w-tw-{x0}:y={y0}")
body = os.path.join(tmp, "body.mp4")
run(["-framerate", str(FPS / step), "-pattern_type", "glob", "-i", os.path.join(ROOT, "renders/walk_test/f*.jpg"),
     "-vf", f"fps={FPS},{','.join(draws)}", "-c:v", "libx264", "-pix_fmt", "yuv420p", body])
lst = os.path.join(tmp, "list.txt")
open(lst, "w").write("".join(f"file '{p}'\n" for p in (intro, body, outro)))
silent = os.path.join(tmp, "film_silent.mp4")
run(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent])
out = os.path.join(ROOT, "renders/walk_test.mp4")
run(["-i", silent, "-ss", f"{MUSIC_IN}", "-t", f"{FILM}", "-i", MUSIC, "-map", "0:v", "-map", "1:a",
     "-af", f"afade=in:st=0:d=0.3,afade=out:st={FILM - 3:.2f}:d=3", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
     "-shortest", out])
print(out, f"intro {intro_s:.2f}s body {body_frames / FPS:.2f}s outro {outro_s:.2f}s")
