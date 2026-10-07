# Setting up on a new machine

## 1. Project
Unpack the bundle so the project lands at the **same path** as before if you can:
`/home/gnus/Documents/Reposepos/SagaModel` (needed for step 4 to resume the exact conversation).
If your username/path differs, it still works — only step 4 changes (see note there).

## 2. Blender 5.2.x LTS
Install from blender.org (official tarball), e.g. `~/opt/blender-5.2.2-linux-x64`, and put `blender` on
PATH. Open `SagaV2_work.blend` once in the GUI and **File → External Data → Find Missing Files** if any
texture path is reported missing (paths are stored relative to the .blend, so normally nothing to do).
The world HDRI `assets/polyhaven/hdri/buikslotermeerplein_4k.exr` is included in the bundle (it is
git-ignored; re-fetch from polyhaven.com/a/buikslotermeerplein if lost).

## 3. Live-Blender tooling for Claude Code
```
curl -LsSf https://astral.sh/uv/install.sh | sh                 # uv
cd <project> && claude mcp add blender -s local -e DISABLE_TELEMETRY=true -- ~/.local/bin/uvx mcp-for-blender
uvx mcp-for-blender install-addon                                 # Blender add-on
```
Or copy `claude_state/blender_mcp.py` from the bundle into `~/.config/blender/5.2/scripts/addons/`
and enable "MCP for Blender" in Preferences → Add-ons. Open Blender (GUI) with the work file; the add-on
listens on 127.0.0.1:9876. `scripts/bmcp.py` works even without the MCP tools.
Optional (only to re-convert the .skp): `python3 -m venv .venv && .venv/bin/pip install openskp==1.3.0`.

## 4. Resume the exact Claude conversation (optional but recommended)
The bundle's `claude_state/` holds the previous session transcript and memory:
```
P=~/.claude/projects/-home-gnus-Documents-Reposepos-SagaModel        # dir name = project path with / -> -
mkdir -p "$P" && cp claude_state/transcript/*.jsonl "$P/"
mkdir -p ~/.claude/projects/-home-gnus-Documents-Reposepos/memory && cp claude_state/memory/*.md ~/.claude/projects/-home-gnus-Documents-Reposepos/memory/
cd /home/gnus/Documents/Reposepos/SagaModel && claude --continue
```
If the project path differs, name the transcript folder after the NEW path (replace every `/` with `-`).
Even without the transcript, `CLAUDE.md` is loaded automatically and contains the full state.

## 5. Rendering finals on this machine
```
blender -b SagaV2_work.blend --python scripts/render_finals.py                 # all cameras
SAGA_OUT=final3 SAGA_SPP=256 blender -b SagaV2_work.blend --python scripts/render_finals.py -- 02_entrance_lounge
```
The script picks the GPU automatically (OptiX > CUDA > HIP > oneAPI > Metal; `SAGA_DEVICE=CPU` forces CPU)
and prints `RENDER DEVICE:` at start. Output: `renders/<SAGA_OUT>/NN_<shot>.png`, 1920x1080.
