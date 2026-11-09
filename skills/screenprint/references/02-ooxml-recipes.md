# OOXML recipes that actually open in PowerPoint

All snippets assume:

```python
from lxml import etree as E
from pptx import Presentation
P  = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
A  = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
R  = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
C  = "{http://schemas.openxmlformats.org/drawingml/2006/chart}"
NS = {"p": P[1:-1], "a": A[1:-1], "c": C[1:-1]}
```

Rule of thumb: **edit with python-pptx when the API exists, edit XML when it does not**, and
always re-open the result in PowerPoint before believing it.

## 1. Shapes: find, move, restyle

```python
def shapes_with_text(slide, needle):
    for sh in slide.shapes:
        if sh.has_text_frame and needle in sh.text_frame.text:
            yield sh

# geometry (EMU)
sh.left, sh.top, sh.width, sh.height = Emu(x), Emu(y), Emu(cx), Emu(cy)
```

`left/top` are `None` for placeholders inheriting position — set them explicitly.

Colour without touching size/weight:

```python
from pptx.dml.color import RGBColor
for p in sh.text_frame.paragraphs:
    for r in p.runs:
        r.font.color.rgb = RGBColor(0x4C, 0x5D, 0x66)
```

Bulk recolour of a *family* is better done on the XML tree, because it also fixes
`lstStyle/defRPr` so newly typed text inherits the new colour:

```python
MAP = {"647681": "4C5D66", "A9C6D4": "4F6B78"}
for clr in sh.text_frame._txBody.iter(A + "srgbClr"):
    v = (clr.get("val") or "").upper()
    if v in MAP:
        clr.set("val", MAP[v])
```

## 2. Fills

`solidFill` / `gradFill` / `blipFill` / `pattFill` / `noFill` must sit inside `p:spPr` **after**
`a:xfrm`, and the whole `spPr` child order is:

```
a:xfrm, (a:custGeom|a:prstGeom), fill, a:ln, a:effectLst, a:scene3d, a:sp3d, a:extLst
```

Pattern presets that exist (anything else corrupts the file):

```
pct5 pct10 pct20 pct25 pct30 pct40 pct50 pct60 pct70 pct75 pct80 pct90
horz ver ltHorz ltVer diagH diagV ltDiagH ltDiagV ...  (no pct35!)
```

## 3. Image parts and rels (the classic trap)

Replacing a picture's *shared* media part changes every slide that uses it. To change one
slide, add the image to that slide and repoint the blip:

```python
part, rid = slide.part.get_or_add_image_part(path)      # returns (image_part, rId)
blip = shape._element.find(".//" + A + "blip")
blip.set("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed", rid)
```

Do **not** use `ImagePart.from_image` (does not exist) or `.find('.//a:blip', NS)` with a Clark
string as the namespace map — the latter raises `TypeError`, and a surrounding `try/except` will
hide it.

## 4. Animation: the shapes that matter

An entrance effect for one shape is a click group (`nodeType="clickEffect"`) whose child list
contains a visibility `p:set`, an `p:animEffect`, and optionally a property `p:anim`:

```xml
<p:par><p:cTn id="5" presetID="22" presetClass="entr" presetSubtype="4"
              fill="hold" grpId="0" nodeType="clickEffect">
  <p:stCondLst><p:cond delay="0"/></p:stCondLst>
  <p:childTnLst>
    <p:set><p:cBhvr><p:cTn id="6" dur="1" fill="hold"/><p:tgtEl><p:spTgt spid="5"/></p:tgtEl>
      <p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>
      <p:to><p:strVal val="visible"/></p:to></p:set>
    <p:animEffect transition="in" filter="wipe(up)">
      <p:cBhvr><p:cTn id="7" dur="600" decel="10000"/><p:tgtEl><p:spTgt spid="5"/></p:tgtEl></p:cBhvr>
    </p:animEffect>
  </p:childTnLst>
</p:cTn></p:par>
```

Useful `filter` values: `fade`, `wipe(up|down|left|right)`, `circle`, `box`, `dissolve`.

A vertical "rise" is the same `p:set` + `p:animEffect filter="fade"` plus a sibling `p:anim` on
`ppt_y` with `a:tav` values `#ppt_y+0.024` → `#ppt_y` (values are fractions of slide height).

**Rule for keeping the click count stable**: enrich an existing click group (add `withEffect`
children inside it). Adding a new `clickEffect` par adds a new click stop — the click map, the
speech and the rehearsal all shift.

## 5. Chart build (bars growing)

There are two halves, both required.

(a) Build granularity in `p:bldLst` — note the nesting, a very common mistake:

```xml
<!-- WRONG: PowerPoint repairs the file -->
<p:bldGraphic spid="5" grpId="0"><p:bldChart bld="series"/></p:bldGraphic>

<!-- RIGHT -->
<p:bldGraphic spid="5" grpId="0"><p:bldSub><a:bldChart bld="series"/></p:bldSub></p:bldGraphic>
```

`bld` ∈ `all | series | category | seriesEl | categoryEl`. Choose by chart type:

| chart | build | entrance |
|---|---|---|
| horizontal bar (1 series, n categories) | `category` | `wipe(right)` |
| clustered bar, 2–3 series | `series` | `wipe(up)` |
| stacked bar | `category` | `wipe(up)` |
| scatter / line | leave as one block | `fade` |

(b) The entrance effect on the chart's `graphicFrame` (same par as before) must be a **wipe**,
not a fade; otherwise the build is invisible. Remove any `ppt_y` rise on chart frames — the
combination looks muddy.

Both survive a PowerPoint round-trip; verify:

```python
t = zipfile.ZipFile("out.pptx").read("ppt/slides/slide10.xml").decode()
assert 'bldChart' in t and 'wipe(' in t
```

## 6. Media: loop a video

The video shape carries the media rel; the timing says how it plays:

```xml
<p:video><p:cMediaNode vol="80000">
  <p:cTn id="42" fill="hold" display="0" repeatCount="indefinite"/>
  <p:tgtEl><p:spTgt spid="8505"/></p:tgtEl>
</p:cMediaNode></p:video>
```

`repeatCount="indefinite"` = "Loop until Stopped". Verify it survives:

```python
assert t.count('repeatCount="indefinite"') == 2
```

Replacing the bytes: overwrite the media part **and** the poster image part
(`p:blipFill` of the video shape points to a poster PNG). Keep resolution/fps/aspect identical
to the existing clips (e.g. 1280×520 @ 60 fps) so the frame does not jump between videos.

## 7. Charts: data labels

`c:dLbls` child order is: `numFmt, spPr, txPr, dLblPos, showLegendKey, showVal, showCatName,
showSerName, showPercent, showBubbleSize, ...`. Rebuild the whole element instead of inserting
single children; and insert it in `c:ser` **before** `c:cat/c:val` (`dPt` and `pictureOptions`
come before, `cat/val` after).

```python
d = E.Element(C + "dLbls")
E.SubElement(d, C + "numFmt").attrib.update({"formatCode": "0", "sourceLinked": "0"})
...  # spPr(noFill), txPr(defRPr sz="750" b="1" + srgbClr), dLblPos=outEnd, showVal=1 ...
cat = ser.find(C + "cat"); cat.addprevious(d)
```

Chart series that use **tiled image fills** (`a:blipFill` + `a:tile`) do not report a colour;
match them by the hash of the source tile, never by name or sampled mean colour.

## 8. Tables

Cell fill and text are ordinary `a:tcPr` / `a:txBody`; table styles are inherited from the
`graphicFrame`'s `a:tblPr`. To restyle a header row, set each cell's `a:tcPr/a:solidFill` and
its run colours — do not rely on a table style id.

## 9. Reading back what PowerPoint wrote

After `SaveAs`, PowerPoint re-serialises everything: shape names can change, media is
deduplicated, `pct` fills may be normalised, `latin typeface` gets `panose` attributes. That is
normal. Compare **semantics**, not bytes:

- text: concatenate `a:t` and compare
- geometry: compare `a:off`/`a:ext`
- colours: compare effective run/fill colours
- media: compare sha256 of the part contents

If PowerPoint resaved and dropped 3.7 MB, check `ppt/media` part counts (36 → 25) before
suspecting quality loss; then compare renders pixel-wise (mean abs diff < 1 is fine).

## 10. Validation loop (do this every time)

```powershell
# 1 open + save in PowerPoint (the real validator)
#    a repair dialog means the XML is wrong — fix the structure, do not retry
# 2 export pages and look at them
# 3 assert in python
python scripts/verify_package.py out.pptx --expect-slides 30 --expect-clicks 43
```
