#!/usr/bin/env bash
# Recreate the Fab Lab SAGA working environment on a new Linux x86-64 machine.
# Idempotent: safe to re-run. Run from the project root:  ./setup.sh
# What it sets up (mirrors the original laptop, 2026-10-08):
#   1. system packages: poppler-utils (pdftoppm/pdftotext), curl, git, python3-venv  [needs sudo/apt]
#   2. Blender 5.2.2 LTS official tarball -> ~/opt, sha256-verified, `blender` on PATH (~/.local/bin)
#   3. uv/uvx (Astral installer)
#   4. MCP for Blender: add-on installed + enabled in Blender, MCP server registered with Claude Code
#      for this project (telemetry disabled)
#   5. Python venv .venv with openskp 1.3.0 (+ textures extra) - only needed to re-convert the .skp
#   6. Node tools (tools/: puppeteer-core) - needs Node >= 18 and Google Chrome/Chromium
#   7. Restores the Claude Code conversation transcript + memory from claude_state/ (if present)
# Then: open Blender with SagaV2_work.blend and run `claude --continue` in this folder.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
BL_VER=5.2.2; BL_SERIES=5.2
BL_DIR="$HOME/opt/blender-${BL_VER}-linux-x64"
say() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

say "1. System packages"
if command -v apt-get >/dev/null; then
  need=(); for p in poppler-utils curl git python3-venv xz-utils; do dpkg -s "$p" >/dev/null 2>&1 || need+=("$p"); done
  if ((${#need[@]})); then sudo apt-get update && sudo apt-get install -y "${need[@]}"; else echo "ok"; fi
else
  echo "Not Debian/Ubuntu: install poppler-utils, curl, git, python3-venv, xz manually."
fi

say "2. Blender ${BL_VER}"
if [ ! -x "$BL_DIR/blender" ]; then
  mkdir -p "$HOME/opt" && cd "$HOME/opt"
  T=blender-${BL_VER}-linux-x64.tar.xz
  curl -sSLO "https://download.blender.org/release/Blender${BL_SERIES}/$T"
  curl -sSL "https://download.blender.org/release/Blender${BL_SERIES}/blender-${BL_VER}.sha256" | grep linux-x64 | sha256sum -c -
  tar xf "$T" && rm "$T"
  cd "$ROOT"
fi
mkdir -p "$HOME/.local/bin" && ln -sf "$BL_DIR/blender" "$HOME/.local/bin/blender"
export PATH="$HOME/.local/bin:$PATH"
blender --version | head -1

say "3. uv"
command -v uvx >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
uv --version

say "4. MCP for Blender (add-on + Claude Code server)"
ADDONS="$HOME/.config/blender/${BL_SERIES}/scripts/addons"
mkdir -p "$ADDONS"
if [ -f "$ROOT/claude_state/blender_mcp.py" ]; then
  cp "$ROOT/claude_state/blender_mcp.py" "$ADDONS/blender_mcp.py"     # the exact add-on version used so far
else
  uvx mcp-for-blender install-addon
fi
blender -b --factory-startup --python-expr 'import bpy,addon_utils; addon_utils.enable("blender_mcp", default_set=True, persistent=True); bpy.ops.wm.save_userpref(); print("ADDON", "blender_mcp" in bpy.context.preferences.addons)' 2>&1 | grep ADDON
if command -v claude >/dev/null; then
  (cd "$ROOT" && claude mcp get blender >/dev/null 2>&1) || \
    (cd "$ROOT" && claude mcp add blender -s local -e DISABLE_TELEMETRY=true -- "$(command -v uvx)" mcp-for-blender)
  (cd "$ROOT" && claude mcp get blender | head -3)
else
  echo "Claude Code not installed yet: npm i -g @anthropic-ai/claude-code (or see claude.com/claude-code), then re-run."
fi

say "5. Python venv with openskp (SketchUp converter)"
if [ ! -x "$ROOT/.venv/bin/python" ]; then python3 -m venv "$ROOT/.venv"; fi
"$ROOT/.venv/bin/pip" -q install 'openskp[textures]==1.3.0'
"$ROOT/.venv/bin/python" -c "import openskp; print('openskp', openskp.__version__)"

say "6. Node tools (headless Chrome helpers)"
if command -v node >/dev/null; then
  (cd "$ROOT/tools" && npm install --silent)
  CH=$(command -v google-chrome || command -v chromium || command -v chromium-browser || true)
  echo "node $(node --version); chrome: ${CH:-NOT FOUND (install Google Chrome; tools expect /usr/bin/google-chrome)}"
else
  echo "Node not found: install Node >= 18 (e.g. via nvm) if you need tools/ (SketchUp capture, SVG raster)."
fi

say "7. Claude Code transcript + memory"
if [ -d "$ROOT/claude_state" ]; then
  PROJ_KEY=$(printf '%s' "$ROOT" | sed 's#[/.]#-#g')                 # Claude Code's per-project folder name
  PARENT_KEY=$(printf '%s' "$(dirname "$ROOT")" | sed 's#[/.]#-#g')
  mkdir -p "$HOME/.claude/projects/$PROJ_KEY" "$HOME/.claude/projects/$PARENT_KEY/memory"
  cp -n "$ROOT"/claude_state/transcript/*.jsonl "$HOME/.claude/projects/$PROJ_KEY/" 2>/dev/null || true
  cp "$ROOT"/claude_state/memory/sagamodel-project.md "$HOME/.claude/projects/$PARENT_KEY/memory/"
  M="$HOME/.claude/projects/$PARENT_KEY/memory/MEMORY.md"
  grep -q sagamodel-project "$M" 2>/dev/null || cat "$ROOT/claude_state/memory/MEMORY.md" >> "$M"
  echo "transcript -> ~/.claude/projects/$PROJ_KEY/ ; memory -> ~/.claude/projects/$PARENT_KEY/memory/"
fi

say "8. Assets check"
[ -f "$ROOT/assets/polyhaven/hdri/buikslotermeerplein_4k.exr" ] || \
  curl -sSL -o "$ROOT/assets/polyhaven/hdri/buikslotermeerplein_4k.exr" \
  https://dl.polyhaven.org/file/ph-assets/HDRIs/exr/4k/buikslotermeerplein_4k.exr
ls -lh "$ROOT/assets/polyhaven/hdri/"
blender -b "$ROOT/SagaV2_work.blend" --python-expr 'import bpy; m=[i.filepath for i in bpy.data.images if i.filepath and not i.packed_file and not __import__("os").path.exists(bpy.path.abspath(i.filepath))]; print("MISSING IMAGES:", m or "none")' 2>&1 | grep "MISSING IMAGES"

say "Done"
echo "Next: blender $ROOT/SagaV2_work.blend &   (add-on starts its MCP socket on 127.0.0.1:9876)"
echo "      cd $ROOT && claude --continue        (resumes the previous conversation; AGENTS.md is loaded either way)"
echo "      Finals: blender -b SagaV2_work.blend --python scripts/render_finals.py   (GPU auto-selected)"
