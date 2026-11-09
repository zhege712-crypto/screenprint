# Layout, typography and projection readability

Most "make it look better" requests decompose into a small set of measurable rules. Measure,
then change, then re-measure.

## 1. The page furniture system

Decide these once, apply everywhere, assert them in the audit:

| Element | Rule used in the reference deck |
|---|---|
| Header band | full-width `#17364A` rect, `h = 800000` EMU, `top = 0` |
| Footer rail | same colour, `top = 6480000`, `h = 378000` |
| Logos | ice-ink PNG, vertically centred in the band (`top = 400000 - h/2`) |
| Title | body `31.5 pt bold`; divider `46.5 pt bold`; cover `42`; closing `48` |
| Eyebrow / nav | ice `#DDEBEF`, `10.5–15 pt bold` |
| Caption | `13.2 pt regular`, `#4C5D66`, `top ≈ 6172200` |
| Footer text | `9.5 pt regular` ice, vertically centred in the rail |
| Page number | `12 pt regular` ice, right aligned inside the rail |
| Paper | `#FBF6EE` texture, full bleed |

Anything that repeats on ≥3 pages belongs in this table; if two instances disagree, one is a bug.

## 2. Type scale discipline

Users notice inconsistent weight far more than inconsistent size. Audit by *role*, not by shape
name:

```python
roles = {
  "footer": lambda t: t.startswith("LABEL"),
  "page":   lambda t: re.fullmatch(r"(Backup )?\d+ / \d+", t.strip()),
  "caption":lambda t, sz: sz == 13.15,
}
```

Then assert one signature per role:

```python
assert sig["footer"] == {(9.5, False)}
assert sig["page"]   == {(12.0, False)}
```

Real defects this catches: outline items 1–2 bold and 3–4 regular on the same page; three
parallel bullets at 22.5/20.25/20.25 pt; footer 9.5 pt on body pages and 9.75 pt on dividers;
page numbers 12 pt vs 10.5 pt.

Fix by writing a table into the design note (role → size → weight), so the next iteration cannot
silently drift.

## 3. Contrast on paper and on ink

Measure, do not eyeball:

```python
def lum(c):
    def f(v):
        v = v / 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = c
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)
```

Thresholds used: body/small text ≥ 4.5:1, large (≥ 24 pt or ≥ 19 pt bold) ≥ 3:1. On this paper
`#FBF6EE` that means secondary text below `#5A6B74` is too light; `#647681` sits at 4.39:1 and
*dies on a projector* even though it passes on a monitor. Practical target for captions: ≥ 6:1
(`#4C5D66` = 6.37:1).

Light text on the navy band is fine (`#DDEBEF` on `#17364A` ≈ 9:1); light blue on paper is not
(`#A9C6D4` = 1.67:1 — invisible).

## 4. Geometry audits (cheap, catches the expensive bugs)

- **Bleed**: exactly one background shape at `(0,0,W,H)`. A dragged layer leaves a 1 cm white
  stripe that survives into the PDF and shows only on the venue screen.
- **Off-slide**: `x+cx <= 0` or `y+cy <= 0` or `x >= W` — usually a mis-signed move.
- **Rails**: nothing but footer furniture may sit inside `y > 6480000`; captions must end above.
- **Overlaps**: two text boxes with > 25 % intersection. Top-anchored single lines tolerate it,
  anything else will collide when the text grows.
- **Alignment**: left edges of sibling blocks must be equal. In the reference deck the right chart
  title was inset 209550 EMU while the left was 114300 — invisible in a screenshot, obvious on a
  projector.
- **Vertical distribution**: after moving content, compute the gaps between blocks. Uneven gaps
  (528 / 152 / 124 k EMU) read as "the text sank to the bottom"; equalising them is the whole fix.

## 5. Making text survive texture

Bake the texture into the background JPEG with feathered keep-clear zones (see
`03-figure-assets.md`). Never place semi-transparent texture shapes *over* text to "integrate" it;
you will either dim the text or get a visible rectangle.

## 6. Presentation of changes to the user

A typography/layout iteration should be reported as a table of *roles*, plus a short list of the
specific defects repaired, e.g.:

| Role | Was | Now |
|---|---|---|
| outline items | 2 bold / 2 regular, 24/24/24/24 | 4 regular, 24 pt |
| conclusions | 24.75 / 24.75 / 24, mixed weight | 3 bold, 24 pt |
| footer | 9.5 / 9.75 | 9.5 everywhere |
| page number | 12 / 10.5 | 12 everywhere |

and a contrast table for anything recoloured (old → new → measured ratio).

## 7. What not to touch

If the user chose a colour or weight deliberately ("the colours are intentional"), do not
normalise it. Report measurable consequences (contrast 2.8:1) and let them decide; offer one
alternative, not five.
