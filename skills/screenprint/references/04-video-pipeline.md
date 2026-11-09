# Embedded video: render, encode, swap, loop

A talk deck usually needs two kinds of clips: a **concept animation** (Blender/After Effects,
stylised) and a **recorded trace** (chart replay, matplotlib frames). Both follow the same
pipeline: frames → mp4 → replace media part → replace poster → verify playback flags.

## 1. Keep every clip on one spec

Existing clips in the deck define the contract. Probe them first:

```powershell
ffprobe -v error -show_entries stream=width,height,r_frame_rate,nb_frames:format=duration,size -of default=nw=1 clip.mp4
```

Typical panel spec: `1280x520, 60 fps, 360 frames, 6.0 s`. A new clip that is 1920×1080 @ 30 fps
will letterbox or stutter beside the others; render at the same spec.

The video shape's aspect must match: `5334000 × 2166938 EMU` = 2.462 = 1280/520. If you change
the clip aspect you must re-proportion the shape.

## 2. Headless Blender render (reusing the project scene)

```powershell
& "C:\Program Files\blender.exe" -b -P render_panels.py -- insertion
```

`render_panels.py` pattern that survives reuse:

```python
import bpy, sys, json
from pathlib import Path
from mathutils import Vector

MODE = sys.argv[sys.argv.index('--') + 1]          # insertion | braking
SRC  = Path(r"...\scene.blend")

bpy.ops.wm.open_mainfile(filepath=str(SRC))
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'             # fast, flat, print-like
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 520, 100
sc.render.fps = 60
sc.frame_start, sc.frame_end = 1, 360
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = str(OUT / 'frame_')

# reset animation so the scene is deterministic
for o in (follower, pred, orange, indicator):
    o.animation_data_clear()

# put the camera back where the existing panels put it
sc.camera.data.ortho_scale = 32
sc.camera.location = (0, -22, 36)
sc.camera.rotation_euler = (Vector((0, -0.65, 0)) - sc.camera.location).to_track_quat('-Z', 'Y').to_euler()

def update(scene):
    t = (scene.frame_current - 1) / 60.0
    ...                                        # move vehicles
    for o, x0 in zip(dashes, dash_x0):         # scroll the road, or it looks static
        o.location.x = x0 - (18 * t % 6.0)

bpy.app.handlers.frame_change_pre.clear()
bpy.app.handlers.frame_change_pre.append(update)
bpy.ops.render.render(animation=True)
```

Lessons:

- **Scroll the ground.** A tracking camera with static road markings reads as a still image,
  even when the cars move.
- Re-assert **non-overlap** for every frame before rendering: `assert p - 2.15 > c + 2.15`.
  Silent overlaps are the most common "why does this look wrong".
- Brake/indicator cues must be visible from the camera used. Top-down view: a thin bar on the
  roof's rear edge reads; a light behind the bumper does not.
- Write a `RECEIPT_<mode>.json` (fps, frames, size, narrative) next to the frames.
- Render takes ~30–60 s for 360 frames at this size — run it as a background job and do the
  deck edits meanwhile.

## 3. Encode

```powershell
ffmpeg -y -framerate 60 -i frames\frame_%04d.png -c:v libx264 -preset slow -crf 20 ^
       -pix_fmt yuv420p -movflags +faststart out.mp4
```

`yuv420p` and even dimensions are required for PowerPoint compatibility; `+faststart` makes it
play instantly. Target 250–400 KB per 6 s panel — the deck must stay small.

## 4. Swap into the pptx

1. Identify the shape and its parts:
   ```python
   nv = shape._element.find(".//" + P + "cNvPr")          # name + id
   vf = shape._element.find(".//" + A + "videoFile")      # rel → ppt/media/mediaN.mp4
   blip = shape._element.find(".//" + A + "blip")         # rel → poster PNG
   ```
2. Replace **both** the mp4 part and the poster image part, by part name, when rebuilding the
   zip. The poster is the first frame the audience sees; leaving the old one shows a stale
   scene until the click.
3. Poster choice: for an insertion clip use the final frame (state == panel title), for a braking
   clip a mid frame. Export it from the rendered frames, do not screenshot the video.
4. Set the loop (see `02-ooxml-recipes.md` §6) and confirm the flag survives a PowerPoint
   round-trip.

## 5. Naming and receipts

Keep a mapping table in the receipt, because media part names are opaque:

```json
{"slide5": {"left": {"shape": "V27_VIDEO_completed", "part": "ppt/media/media2.mp4",
                     "src": "v39_media/insertion.mp4", "sha256": "23eb25e6..."},
            "right": {"shape": "V27_VIDEO_braking", "part": "ppt/media/media3.mp4",
                      "src": "v39_media/braking.mp4", "sha256": "4a412b46..."}}}
```

## 6. If Blender is not available

- 2D fallback: compose frames with PIL from the deck's own sprite/background assets, then encode
  with ffmpeg. Quality is lower but consistent and reproducible.
- Chart replay: render matplotlib frames at the panel size, same fps, same poster workflow.
- Never substitute a GIF: PowerPoint's GIF playback is unreliable in slideshow and does not loop
  with the same controls as a video.

## 7. What you must tell the user

Playback smoothness, colour on the venue projector, and whether a loop feels too fast are
eye-only judgements. State which slides to press F5 on, and what to look for — do not claim
"verified" for anything you could not observe.
