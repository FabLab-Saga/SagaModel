# RENDER.md — presentation renders + video (Fab Lab SAGA)

Working document for the render/video phase (started 2026-10-08). CLAUDE.md stays the brief for the model
itself; this file holds everything about stills, the presentation video, its script and its branding rules.
Decisions marked (Magnús) are his; everything else is Claude's proposal and can be changed.

## Deliverables
1. New stills `renders/final4/` (the final3 set is outdated). Reframe the stale cameras first (Entrance,
   Lounge, SecretDoor, Counter, Craft, Interior_01, Mural, ...) and add an entrance hero shot (TV + on-call desk).
2. One presentation video: ~90 s (Magnús), 1920x1080, 30 fps (Magnús) = 2,700 frames. Structure (Magnús): one
   continuous walkthrough spine cut with short detail shots. On-screen text in Icelandic only (Magnús).

## Script v2 (approved by Magnús as "solid"; timings are approximate)
    0:00-0:04  INTRO       Black, FAB LAB SAGA lockup centred, white, fade only
    0:04-0:12  HALL        Push-in through the hotel hall to the Fab Lab door   "FAB LAB SAGA // Hagatorg 1"
    0:12-0:24  SPINE 1     Door -> TV + on-call desk -> past the conversation pit -> into the lab
    0:24-0:30  REVEAL      Crane-up over the work tables to a high corner
    0:30-0:36  LASER       Dolly along the laser bench                 "FAB LAB SAGA // Geislaskeri"
    0:36-0:41  PRINT FARM  Sideways track past the cabins, one open    "FAB LAB SAGA // Þrívíddarprentari"
    0:41-0:49  CNC         Push through the dotted glass to the ShopBot "FAB LAB SAGA // Fræsivél"
    0:49-0:55  ELECTRONICS Low over the SRM-20 bench                   "FAB LAB SAGA // Rafeindaverkstæði"
    0:55-1:00  CRAFT       Presses, sewing/embroidery, clay printer    "FAB LAB SAGA // Textílsvæði"
    1:00-1:05  TOOL WALL   Glass tool wall + felt wall                 "FAB LAB SAGA // Verkfæri"
    1:05-1:12  BANK        Secret door swings open (new animation)     "Búnaðarbanki SFS"  (no prefix; Magnús)
    1:12-1:19  LOUNGE      Low dolly down the pit axis (the MAIN-AREA lounge by the SSW glass, never the
                           staff room; no title - Magnús), rising into...
    1:19-1:25  SPINE 2     ...the pull-back over the whole lab
    1:25-1:30  OUTRO       Black, manual variant B: FAB LAB SAGA lockup | HÍ Verkfræði- og náttúruvísindasvið,
                           HÍ Menntavísindasvið, Reykjavík, Mixtúra (all white, thin divider)
Kaffistofa is NOT in the video: staff only (Magnús). Zone names are Magnús's.
Craft (mine): detail shots 4-6 s, one slow move each, no whip pans; 0.5 s crossfades only into/out of the spine;
the only animation besides cameras is the secret door (optionally the TV playing).

## Brand rules for the video (Fab Lab Ísland brand manual 2021, pp. 56-57)
- Intro frame: logo centred, monochrome: white on black, or black on Black 10% (#E4E4E4). Never recolour,
  condense, rotate or re-compose the logo. Collaboration = variant B: logos side by side with a thin vertical line.
- Video frame: small white logo bottom-right (~168x92 px at 1080p); title lower-left, white, aligned with the
  logo's first word, ~47 pt, bold first part + light second part ("FAB LAB SAGA // Name").
- Fonts: Roboto family only (`refs/branding/fonts/`). Headlines Roboto Condensed.
- Logo: the FAB LAB SAGA lockup as on `refs/branding/Poster_FabLabSaga_A4.svg` (sublogo grid).

## Signs in the model
`scripts/make_signs.py` re-letters the manual's sign PDFs (typos VERKÆRI / ELECTRONCS fixed) with Magnús's names:
GEISLASKERI, ÞRÍVÍDDARPRENTARI, FRÆSIVÉL, RAFEINDAVERKSTÆÐI, TEXTÍLSVÆÐI, VERKFÆRI, VÍNYLSKERI (English sub-lines
are mine). Then re-run `build_signs.py` (reload the images first).

## Partner logos
`assets/partners/` + `SOURCES.md` there; licence notes in LICENSES.md (partner trademarks, approved by Magnús).
White versions: Reykjavík official; HÍ schools = our white recolour (HÍ standard allows white); Mixtúra = archived
2021 wordmark, cropped, white recolour (Magnús) until Mixtúra supplies a current file. Reykjavík rule: one
shield-width of clear space to the next logo; shield + "Reykjavík", no department name.

## Music
CC0 only (same rule as every asset). Shortlist being built in `~/Documents/AgentWork/saga-video/music/`;
Magnús picks. Record the pick in LICENSES.md.

## Hall shot
The entrance was wrong in the colleague's model (city drawings, Andrúm AT 20-10-02, 2026-06-30): the lab includes the
corner bay x 32.6-34.3, y 34.6-38.3 and the door (EI2 30 fire door, y 36.54-37.47) is in its SSW wall at x ~34.3,
opening onto the university hall "háskóli 01-01". Fixed in the model by `scripts/build_entrance_bay.py` (approved by
Magnús), which also builds the hall SET for the opening shot (stone floor, acoustic ceiling, glass façade on the
left, WC box, check-in kiosk, seating; finishes are my inference from lobby photos). Research:
`~/Documents/AgentWork/saga-video/hall/HALL.md`. The drawing also shows a lab escape door in the SSW façade at
y ~32.4-34.3, where the lounge pit stands; not modelled yet (open question).

## Pipeline + tools (MPDESKTOP)
- Blender 5.2.2 (Cycles, OptiX, RTX 4070 Ti SUPER): camera paths keyframed by a builder (planned
  `scripts/build_walkthrough.py`), each shot rendered to its own PNG sequence so shots re-render independently.
- fframes (Rust/SVG, `cargo fframes`): intro/outro and title overlays as ProRes 4444 with alpha.
- ffmpeg 9 (NVENC, x264/x265, ProRes): composite, crossfades, music trim/fades, loudness (EBU R128), master.
- Kdenlive 26.08 (Flatpak; bundles melt): the cut is also written as a .kdenlive project for hand edits.
- Inkscape 1.4.4, GIMP 3.2, ImageMagick 7 (`magick`): SVG/logo rasterising, contact sheets, frame checks.

## Cut v3 (2026-10-08, Magnús's notes)
- Titles: Geislaskerar (shot shows the Epilog), Þrívíddarprentarar, ShopBot Fræsir; 'Hagatorg 1' removed (Magnús).
- fframes title card (3 bars): ~/Documents/AgentWork/saga-video/fframes-title/ (6x6 brand grid draws on, brand-colour
  cells flash on the beats, white lockup fades in, tagline 'SKÖPUNAR- OG TÆKNISMIÐJA' + 'BÆNDAHÖLLIN · REYKJAVÍK'
  (my wording, from the poster)). assemble_film.py uses it when present.
- Context shots (Magnús: show the whole space and where areas sit): dollhouse cutaway orbit 'Overview' (slab,
  services, fixtures hidden by keyed hide_render/hide_viewport for that shot), ElectronicsWide, ToolWide (replaces
  the close tool wall), LoungeWide; Reveal, Corridor, LaserDetail dropped.

## Drafts (user wants quick drafts until he approves the cut)
- `renders/walk_flat.mp4`: 1080p flat-shaded Workbench draft, whole film in ~7 min (`render_walk_flat.py`).
- `renders/walk_test.mp4`: 640x360 Cycles 8 spp animatic (~5 min).
No final-quality render until Magnús says so.

## Render budget (measured 2026-10-08, Cam_WorkshopLong, 1920x1080, persistent data)
    64 spp + OptiX denoiser   ~4.7 s/frame   (first frame 6.9 s)
    64 spp + OIDN             ~9.3 s/frame
    128 spp + OIDN            ~14 s/frame
~2,460 Blender frames (titles cards are fframes): ~3.2 h at 64/OptiX, ~6.4 h at 64/OIDN. Check moving test
shots for denoiser flicker before choosing; OIDN is steadier, OptiX twice as fast.
