"""Assemble the presentation film: intro card -> walkthrough frames (+ logo bug + shot titles) -> outro card, with
the music, as an H.264 1920x1080 30 fps MP4.
    /usr/bin/python3 scripts/assemble_film.py [frames_dir] [out.mp4]
    defaults: renders/walk_test (animatic JPGs, any size, scaled up) -> renders/walk_test.mp4
    final:    renders/walk/final -> renders/FabLabSAGA_film.mp4
Needs renders/video_titles/ from scripts/make_titles.py. Shot timing/titles come from build_walkthrough.py.
Music: CC0 "Stairwell Harmony" (Amarent), from MUSIC_IN, faded out at the end.
"""
import ast
import glob
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frames = os.path.join(ROOT, sys.argv[1] if len(sys.argv) > 1 else "renders/walk_test")
out = os.path.join(ROOT, sys.argv[2] if len(sys.argv) > 2 else "renders/walk_test.mp4")
T = os.path.join(ROOT, "renders/video_titles")
MUSIC = os.path.expanduser("~/Documents/AgentWork/saga-video/music/1_Amarent_-_Stairwell_Harmony.mp3")
MUSIC_IN, OUTRO_S = 25.57, 5.4
CARD = os.path.expanduser("~/Documents/AgentWork/saga-video/fframes-title/title_card.mp4")   # fframes intro
OUTRO_CARD = os.path.expanduser("~/Documents/AgentWork/saga-video/fframes-title/outro_card.mp4")  # fframes outro
#   (cd fframes-title && cargo run --release -- render --card outro -o outro_card.mp4); falls back to outro.png

src = ast.parse(open(os.path.join(ROOT, "scripts/build_walkthrough.py")).read())
V = {t.targets[0].id: ast.literal_eval(t.value) for t in src.body
     if isinstance(t, ast.Assign) and getattr(t.targets[0], "id", "") in ("SHOTS", "FPS", "INTRO_BARS")}
FPS, SHOTS, INTRO_BARS = V["FPS"], V["SHOTS"], V["INTRO_BARS"]
BAR = 4 * 60 / 103.36
INTRO_S = INTRO_BARS * BAR
ext = "png" if glob.glob(os.path.join(frames, "f*.png")) else "jpg"

card = os.path.exists(CARD)
ocard = os.path.exists(OUTRO_CARD)
if ocard:
    OUTRO_S = 3 * BAR                                                       # 3-bar fframes card, beat-aligned
inputs = ["-f", "lavfi", "-t", f"{INTRO_S:.3f}", "-i", f"color=black:s=1920x1080:r={FPS}"]            # 0 intro bg
inputs += (["-i", CARD] if card else                                                                   # 1 fframes card
           ["-loop", "1", "-framerate", str(FPS), "-t", f"{INTRO_S:.3f}", "-i", os.path.join(T, "intro.png")])
inputs += [
          "-framerate", str(FPS), "-pattern_type", "glob", "-i", os.path.join(frames, f"f*.{ext}"),        # 2 body
          "-loop", "1", "-framerate", str(FPS), "-i", os.path.join(T, "bug.png"),                       # 3
          "-f", "lavfi", "-t", f"{OUTRO_S:.3f}", "-i", f"color=black:s=1920x1080:r={FPS}"]              # 4 outro bg
inputs += (["-i", OUTRO_CARD] if ocard else                                                        # 5 outro
           ["-loop", "1", "-framerate", str(FPS), "-t", f"{OUTRO_S:.3f}", "-i", os.path.join(T, "outro.png")])
fc = ([f"[1]fps={FPS},trim=duration={INTRO_S:.3f},setpts=PTS-STARTPTS,format=yuv420p,"
       f"fade=out:st={INTRO_S - 0.5:.3f}:d=0.5[intro]"] if card else
      [f"[1]format=rgba,fade=in:st=0.3:d=0.8:alpha=1,fade=out:st={INTRO_S - 0.6:.3f}:d=0.5:alpha=1[il]",
       "[0][il]overlay=format=auto[intro]"])
fc += [
      f"[2]scale=1920:1080:flags=lanczos,setsar=1,fps={FPS}[b0]",
      "[b0][3]overlay=shortest=1:format=auto[b1]"]
fc = [x for x in fc]
idx, last, b = 6, "b1", 0
for name, bars, title, *_ in SHOTS:
    t0, dur = b * BAR, bars * BAR
    if title:
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur - 0.5:.3f}",
                   "-i", os.path.join(T, f"title_{name}.png")]
        fc.append(f"[{idx}]format=rgba,setpts=PTS-STARTPTS,fade=in:st=0:d=0.4:alpha=1,"           # fade on local time,
                  f"fade=out:st={dur - 1.0:.3f}:d=0.3:alpha=1,setpts=PTS+{t0 + 0.5:.3f}/TB[t{idx}]")  # then shift
        fc.append(f"[{last}][t{idx}]overlay=eof_action=pass:format=auto[o{idx}]")
        last, idx = f"o{idx}", idx + 1
    b += bars
if ocard:
    fc.append(f"[5]fps={FPS},trim=duration={OUTRO_S:.3f},setpts=PTS-STARTPTS,format=yuv420p[outro]")
else:
    fc.append("[5]format=rgba,fade=in:st=0.2:d=0.8:alpha=1[ol]")
    fc.append("[4][ol]overlay=format=auto[outro]")
body_s = b * BAR
fc.append(f"[{last}]trim=duration={body_s:.3f},fade=in:st=0:d=0.4,fade=out:st={body_s - 0.5:.3f}:d=0.5[body]")  # dip
fc.append("[intro][body][outro]concat=n=3:v=1:a=0,format=yuv420p[v]")                                   # from/to black
film_s = INTRO_S + b * BAR + OUTRO_S
cmd = ["ffmpeg", "-y", "-v", "error"] + inputs + ["-ss", f"{MUSIC_IN}", "-t", f"{film_s:.3f}", "-i", MUSIC,
       "-filter_complex", ";".join(fc), "-map", "[v]", "-map", f"{idx}:a",
       "-af", f"afade=in:st=0:d=0.3,afade=out:st={film_s - 3:.2f}:d=3,loudnorm=I=-16:TP=-1.5:LRA=11",
       "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-profile:v", "high", "-r", str(FPS),
       "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest", out]
subprocess.run(cmd, check=True)
print(out, f"{film_s:.2f} s (intro {INTRO_S:.2f}, body {b * BAR:.2f}, outro {OUTRO_S})")
