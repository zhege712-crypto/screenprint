# Local tools: manifest, authorisation, recipes

**Authorisation**: while working on a deck you may call the creative tools installed on the
machine (Blender, ComfyUI, ffmpeg, the Python stacks, PowerPoint COM) without asking each time.
Three constraints:

1. **Installs are allowed after asking.** If a new tool, model, font or library would do the job
   better, request approval directly (what, size, where, why) — do not silently install, and do
   not give up on a better tool just because it is missing.
2. **Touch only the deck work tree** and the registered output folders.
3. **Every generated asset ships with a receipt** (fps, size, seed, model, script, tool version)
   so it can be reproduced.

## 1. Discover what is installed

```powershell
python scripts/detect_tools.py          # human table
python scripts/detect_tools.py --json   # machine readable
python scripts/detect_tools.py --write  # tools.json next to the script
```

Environment variables the scripts honour (all optional):

| Variable | Points at | Used by |
|---|---|---|
| `DSH_PYTHON` | python with `python-pptx`, `lxml`, `Pillow`, `numpy`, `pypdf` | every `scripts/*.py` |
| `ALT_PYTHON` | python with `matplotlib`/`cv2`/`torch` (image science) | chart replays, analysis |
| `BLENDER_EXE` | `blender.exe` | `references/04-video-pipeline.md` |
| `COMFYUI` | ComfyUI home (contains `draw.cmd`) | `scripts/gen_texture.py` |
| `PPT` | `POWERPNT.EXE` (optional) | export scripts, if Office is not on PATH |

No tool is assumed: missing ones are reported and the workflow degrades (e.g. no Blender →
skip the 3D clip, use matplotlib frames or a static diagram instead).

## 2. Tool roles

| Tool | Use it for | Notes |
|---|---|---|
| **PowerPoint (Windows COM)** | the only trustworthy renderer: PNG/PDF export, media/animation properties | one `SaveAs(..., 32)` per open presentation; `Slide.Export` shows only the final frame |
| **python-pptx + lxml** | all structural editing | python-pptx for what it exposes, lxml for the rest |
| **Pillow + numpy** | every figure asset: dot screens, stripes, ramps, contact sheets, identity card | see `references/03-figure-assets.md` |
| **matplotlib (ALT_PYTHON)** | chart-replay frames → ffmpeg | 2D data animation without Blender |
| **Blender** | 3D concept clips from an existing `.blend` scene | `-b -P script.py -- mode`; Workbench engine is fast |
| **ffmpeg / ffprobe** | frames → mp4, probing existing clips, poster extraction | `-pix_fmt yuv420p`, even dimensions |
| **ComfyUI** | concept art / texture masters, on demand | `scripts/gen_texture.py` wraps it; it starts on demand and exits after |
| **pypdf** | split main/full PDF, metadata | |

## 3. Blender recipe

```powershell
& $env:BLENDER_EXE -b -P build\render_panels.py -- insertion
```

- Reuse the project `.blend` (materials, camera, models) instead of rebuilding the scene.
- `animation_data_clear()` then set positions in a `frame_change_pre` handler — deterministic.
- Scroll the ground (lane dashes, guardrail posts) or a tracking camera reads as a still frame.
- Assert non-overlap per frame; write `RECEIPT_<mode>.json` with fps / frames / size / narrative.
- 360 frames at 1280×520 in Workbench ≈ 30–60 s; run it as a background job.

## 4. ComfyUI recipe

```powershell
$env:COMFYUI = "%COMFYUI%"          # your install
& "$env:COMFYUI\draw.cmd" "screen printed halftone texture, navy ink on warm paper" -Count 4
```

Or use the wrapper, which also does the screen-print post-processing and writes a receipt:

```powershell
python scripts/gen_texture.py --list-presets
python scripts/gen_texture.py --preset halftone-paper --count 2 --out assets\v41 --blur 3 --pitch 16
python scripts/gen_texture.py --preset halftone-paper --from-raw <raw.png> --blur 3   # re-bake, no GPU
```

- `--blur 2-4` is mandatory when re-screening an AI image, otherwise its own dots beat with the
  analytic screen (moiré).
- Generated images are **masters**: they must go through the print post-processing before they
  enter a deck; never paste a raw AI image into a slide.

## 5. What not to do

- Do not depend on the toolchain at presentation time: the deliverable is a self-contained
  `.pptx` plus PDFs. Blender/ComfyUI are production tools only.
- Do not embed unlicensed images, fonts or model output; record provenance in the receipt.
- Do not shoot a camera at a running slideshow and call it verification (wrong window, wrong
  state). Ask the human to press F5 and report what they see.
