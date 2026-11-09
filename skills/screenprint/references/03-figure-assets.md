# Figure assets: halftone, stripes, hatching, gradient ramps

The rule that saves the deck: **bake texture into the background image, keep text on top.**
A full-bleed JPEG (1920×1080) is cheaper to animate and impossible to misalign; shapes drawn
over it will always leave seams.

## 1. Geometry

Slide is 12192000 × 6858000 EMU (13.333 × 7.5 in). For a 1920×1080 raster that is
**142.2 EMU per pixel**; a "0.5 cm" visual gap is ~284 px.

Keep a small helper so you can talk in both units:

```python
EMU_W, EMU_H = 12192000, 6858000
PX_W, PX_H = 1920, 1080
def px(emu): return emu / (EMU_W / PX_W)
def emu(p):  return int(p * (EMU_W / PX_W))
```

## 2. Halftone dot screen (analytic, seamless by construction)

Do **not** jitter a point cloud and then wrap it — every seam shows. Rotate the coordinate grid
and take the cell index; periodicity is then exact.

```python
import numpy as np
def dot_screen(w, h, pitch, angle=35.0, dot_frac=0.42, aa=0.8):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    t = np.deg2rad(angle); c, s = np.cos(t), np.sin(t)
    u = xx * c + yy * s
    v = -xx * s + yy * c
    cu = (u / pitch) % 1.0 - 0.5
    cv = (v / pitch) % 1.0 - 0.5
    r = np.sqrt(cu * cu + cv * cv)                       # 0 at dot centre
    edge = dot_frac * 0.7071
    return 1.0 / (1.0 + np.exp(-(r - edge) / (aa / pitch)))   # 1 = dot
```

Compose it as *ink over paper*: multiply the screen into the paper colour, then multiply again by
a radial or arc "ramp" so the texture fades out where text lives:

```python
ink_alpha = screen * ramp            # ramp in [0,1], 0 near text
img = paper[None, None, :] * (1 - ink_alpha[..., None]) + ink[None, None, :] * ink_alpha[..., None]
```

## 3. Radial / arc ramps and feathered keep-clear zones

```python
yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
d = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
ramp = np.clip((d - d0) / (d1 - d0), 0, 1) ** 1.4           # clean centre → dense rim
keep = Image.new("L", (w, h), 0)
ImageDraw.Draw(keep).rectangle(text_box, fill=255)
keep = np.array(keep.filter(ImageFilter.GaussianBlur(blur_px)), np.float32) / 255
ramp *= (1 - keep)                                          # feather the text zone
```

Blur radius ≈ text height × 0.6 looks natural; a hard rectangle reads as an error.

## 4. Stripes / cross-hatch

One family (45°) reads as a printed tone; two families read as a lattice and get busy.

```python
def stripes(w, h, pitch, width, angle=45.0):
    u = xx * np.cos(np.deg2rad(angle)) + yy * np.sin(np.deg2rad(angle))
    return ((u % pitch) < width).astype(np.float32)
```

## 5. Seam check (30 seconds, saves a redraw)

```python
a = np.asarray(img, np.int16)
assert np.abs(a[:, 0] - a[:, -1]).mean() < 3      # vertical seam
assert np.abs(a[0, :] - a[-1, :]).mean() < 3      # horizontal seam
```

For tiles used as `a:tile` fills the check is the same — build them periodic, then check.

## 6. Baking order

```
paper base → ramp mask → texture (dots/stripes/hatch) → rim ring / hairlines → grain noise
```

Save JPEG quality 92–93 at 1920×1080 (~300–600 KB). PNG only if you need hard edges
(hairline rings, type) at small sizes.

## 7. Placing it in the deck

1. Replace the full-bleed background picture's blip on the specific slide (see
   `02-ooxml-recipes.md` §3). Never replace the shared media part if other slides reuse it.
2. Assert the picture sits at `(0, 0, 12192000, 6858000)` — a dragged background produces white
   gaps that survive into the PDF and only show up on the projector.
3. Keep every text shape *after* the background in `spTree` order, or the texture will print
   over the words.

## 8. Reusing an earlier design safely

When the user says "go back to how v12 looked", do not rebuild from prose — read the old
release: `ppt/media/*` parts plus the slide XML tell you exactly which asset was where. Copy the
bytes forward and keep a hash table so you can state "assets identical to v12" in the receipt.
