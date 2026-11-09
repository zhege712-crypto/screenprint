---
name: screenprint
description: Screenprint (丝网印刷) is the deck ENGINE for this machine — screen-printed house style, build, redesign, animate, audit, and package a conference talk deck (.pptx) with native charts, embedded video, custom figure assets, and a matching speech script. Use when the user wants a talk/defence/pitch deck produced or iterated end-to-end with real PowerPoint fidelity (OOXML-level edits, PowerPoint-verified exports), not just a text outline. Genre variants load this engine and add only their differences (e.g. screenprint-defense).
whenToUse: 用户要求制作/打磨一套报告幻灯片（会议报告、答辩、路演、组会），需要原生图表、内嵌视频、自定义图形素材、动画、以及配套讲稿；或需要审查已有 pptx 的排版、字号、对齐、动画与投放可用性；或需要把 pptx 导出为 PDF/PNG 并打包成现场资料。
---

# Screenprint — talk deck engine (丝网印刷)

**Name.** `screenprint` = 丝网印刷. The whole house style is ink printed on warm paper — halftone
dots, single-family stripes, ice marks on navy, registration rings — so the engine carries that name.

**Name family.** `screenprint` is the engine for every deck skill on this machine: it carries the
workflow, the OOXML recipes, the scripts and the house identity. Variants live beside it as
siblings sharing the prefix — `screenprint-defense` (答辩), and later `screenprint-poster`,
`screenprint-viva`, `screenprint-lecture`. A variant **must not fork the engine**: it loads
`screenprint`, and only adds what is different for its genre.

This skill treats a talk deck as a **product with evidence**: every page is rendered and
inspected, every animation is validated in PowerPoint, every claim in the deck is traceable
to the paper/data, and each iteration is a new immutable version directory.

The control layer is this file. It decides the phase, routes to one reference, and enforces
the non-negotiables. Detailed recipes live in `references/`; runnable helpers live in `scripts/`.

## Trigger boundary

Use for: producing or iterating a real `.pptx` (or ODP/KEY converted to pptx) that will be
projected; auditing layout/typography/animation of such a deck; building the speech script and
cue card that go with it; packaging the on-site delivery folder.

Do **not** use for: pure content drafting in Markdown, writing papers (see
`academic-paper-writing`), generic document conversion, or a single slide that needs no
verification loop.

## Non-negotiables

1. **The source paper/data is frozen** unless the user explicitly reopens it. The deck must
   not introduce numbers the paper does not support.
2. **Never edit a released deck in place.** Each iteration gets its own directory:
   `presentation/<date>_<slug>_vNN/{output,build,assets_vNN}`. Old versions stay untouched.
3. **Nothing counts until PowerPoint renders it.** python-pptx "saving fine" means nothing;
   open the file in PowerPoint, export, and look at the pixels.
4. **Verify animations by structure, then by eye.** Read back the XML after PowerPoint saves
   it; but tell the user plainly when a playback property could not be observed.
5. **Every claim of parity is a command output.** "Text unchanged", "videos identical",
   "43 click groups" — each comes from a script, quoted in the receipt.
6. **One change set per iteration.** If the user asks for three things, deliver the three,
   list them in a table, and name the ones you deliberately left for them to decide.
7. **Ask before redesigning taste.** Colour/font/taste choices the user made deliberately are
   not yours to "improve"; flag conflicts, do not silently normalise them.

## Deck fundamentals (satisfy these before styling)

The pass/fail line for any talk deck, independent of design — see
`references/00-deck-fundamentals.md` for the full checklist:

- **Budget**: 1 slide ≈ 40–90 s; a 12-minute talk is 16–22 main slides plus 6–10 hidden backups.
- **One message per slide**: titles are conclusion sentences ("Explicit plans use less effort"),
  not topic labels ("Effort results").
- **Projection floor**: body ≥ 18 pt, captions ≥ 12 pt, chart labels ≥ 8–9 pt, contrast ≥ 4.5:1
  (small) / ≥ 3:1 (large). Light grey small text on cream is the classic failure.
- **Density**: ≤ 6 lines, ≤ 6 bullets, ≤ 2 visual elements per slide; split rather than shrink.
- **Consistency**: one type family, one accent colour, two data colours; identical page furniture
  on every page; captions/footers/page numbers never appear on "some" pages.
- **Evidence**: a slide may simplify but never strengthen a claim; every shown number exists in
  the paper, the supplementary material, or the recorded results.
- **Field readiness**: embedded media, no auto-advance, no network dependency, and a static PDF
  backup of both the main pages and the full book.

## Tool authorization

You may freely invoke the creative tools installed on this machine — no per-call permission is
needed. Manifest, paths and recipes: `references/09-local-tools.md`. Current capability set:

| Tool | Use it for |
|---|---|
| **Blender** (`%BLENDER_EXE%`, or whatever `detect_tools.py` finds) | concept clips from an existing `.blend` scene: render frames with `-b -P script.py -- mode` |
| **ComfyUI** (`%COMFYUI%\draw.cmd`) | concept art / texture masters; on-demand start, exits by itself, ~2.7 GB VRAM, output in `%COMFYUI%\output\draw` |
| **ffmpeg / ffprobe** | frames → mp4, probing existing clips, extraction for posters |
| **Python (pptx runtime)** | pptx work: python-pptx, lxml, Pillow, numpy, pypdf |
| **Python (alt, image science)** | image/video science: matplotlib, cv2, torch (no pptx there) |
| **PowerPoint COM** | the only trustworthy renderer; PNG/PDF export, media/animation properties |
| **pypdf** | split main/full PDF, metadata |

Three constraints:

1. **Installs are allowed after asking.** If a new tool, model, font or library would do the job
   better, request approval directly (what, size, where, why). The user has pre-authorised
   asking; do not silently install, and do not give up on a better tool just because it is missing.
2. **Touch only the deck work tree** and the registered output folders — never other people's data.
3. **Every generated asset ships with a receipt** (fps, size, seed, model, script, tool version)
   so it can be reproduced.

## House identity

Every deck in this family carries a swappable identity layer — **this is what makes a deck look
like it belongs to the same house**, and it is the only part a future talk should need to fork:

- `assets/identity/brand-tokens.json` — palette, type scale, page geometry, motifs, media and
  animation rules, forbidden list. **Scripts must read the tokens, never hard-code colours.**
- `assets/identity/IDENTITY_CARD.png` — one-page visual summary (palette, type ladder, furniture
  diagram, motif samples, rules), regenerated by `scripts/make_identity_card.py`.
- `references/08-house-identity.md` — the human-readable version and how to fork it.

Rules of use: read the tokens before designing anything; every page must satisfy the geometry in
`geometry_emu`; placeholder/deviation is only allowed if written into the delivery note. When the
user has chosen colours deliberately, keep them — report measurable consequences instead of
"fixing" them.


## Workflow

| Phase | What you do | Exit evidence |
|---|---|---|
| 0. Intake | read the source deck/paper; `references/00-deck-fundamentals.md` for the pass/fail line; probe with `scripts/pptx_probe.py`; list every page, chart, video, click group | probe report + open questions |
| 0.5 Identity | read `assets/identity/brand-tokens.json` (or fork it for a new deck); check the deck against the palette / type scale / geometry | list of deviations, or "in spec" |
| 1. Model the request | turn the ask into 3–6 concrete page-level changes; mark which are content vs chrome vs timing | a change table before editing |
| 2. Build in a sandbox | copy the newest release into `build/`, edit with python-pptx + lxml, save as `candidate_vNN.pptx` | candidate file |
| 3. Render and look | `scripts/export.ps1 -Slides`, view the changed pages as images, not descriptions | screenshots actually read |
| 4. Audit | `scripts/verify_package.py` + `scripts/layout_audit.py` + `scripts/diff_decks.py` against the previous release | receipt JSON |
| 5. Package | PDFs (main + full), previews, design/animation notes, speech pack, checksums | output folder |
| 6. Deliver | present the deck, the before/after sheet, the note, the on-site zip; state what still needs human confirmation | final message with table |

Never merge phases 3 and 4: rendering finds visual bugs, audits find structural ones.

## Route to the right reference

| Situation | Load |
|---|---|
| general deck requirements (budget, projection legibility, evidence, field readiness) | `references/00-deck-fundamentals.md` |
| which local tool to use, paths, recipes, guardrails | `references/09-local-tools.md` |
| the house style: palette, type ladder, furniture, motifs, forbidden list, how to fork | `references/08-house-identity.md` + `assets/identity/brand-tokens.json` |
| first time on this deck, deciding the page system, type scale, bands/rails | `references/01-workflow-and-versioning.md` then `references/05-layout-and-typography.md` |
| animation, chart build, media loop, pattern/gradient fills, rels | `references/02-ooxml-recipes.md` |
| figure assets: halftone, stripes, hatching, gradient ramps, baking into paper | `references/03-figure-assets.md` |
| embedded video: render, encode, swap, poster, loop | `references/04-video-pipeline.md` |
| typography/alignment/contrast audit, projection readability | `references/05-layout-and-typography.md` |
| PDF/PNG export, audits, kit packaging, checksums | `references/06-audit-and-delivery.md` |
| speech script, pointer phrases, cue card, timing | `references/07-speech-and-cues.md` |

## Ten commands that do most of the work

```powershell
# 1. what is in this deck (slides, charts, videos, clicks, hidden pages)
python scripts/pptx_probe.py deck.pptx --json probe.json

# 2. render every page as PNG (1600x900) for eyeballing
powershell -ExecutionPolicy Bypass -File scripts\export.ps1 -Pptx deck.pptx -OutDir out\png -Png

# 3. export PDFs: full deck, and main-only (hidden backup pages stripped)
powershell -ExecutionPolicy Bypass -File scripts\export.ps1 -Pptx deck.pptx -OutDir out -Pdf -AllPdf all30.pdf -MainPdf main21.pdf -MainPages 21

# 4. structural diff against the previous release
python scripts/diff_decks.py old.pptx new.pptx

# 5. layout heuristics: bleed, off-slide, overflow, overlaps, edges
python scripts/layout_audit.py deck.pptx

# 6. chart build animation (grow bars) + wipe entrance
python scripts/ooxml_ops.py chart-build deck.pptx --slide 10 --shape-id 5 --mode category --wipe right

# 7. loop an embedded video
python scripts/ooxml_ops.py media-loop deck.pptx --slide 5

# 8. recolor a family of secondary text (no font/size change)
python scripts/ooxml_ops.py recolor deck.pptx --map 647681=4C5D66 --map A9C6D4=4F6B78

# 9. swap a video and its poster with new renders
python scripts/ooxml_ops.py replace-media deck.pptx --part ppt/media/media2.mp4 --file new.mp4

# 10. contact sheet for review
python scripts/make_contact_sheet.py out\png --pages 1,5,10,15 --out sheet.png

# 11. regenerate the identity card after forking the brand tokens
python scripts/make_identity_card.py --tokens assets/identity/brand-tokens.json --out IDENTITY_CARD.png

# 12. concept frames / texture masters from local tools
%COMFYUI%\draw.cmd "screen-printed halftone texture, navy on warm paper" -Count 4
& "%BLENDER_EXE%" -b -P build\render_panels.py -- insertion
```

## Pitfalls that cost hours (learned the hard way)

| Symptom | Cause | Fix |
|---|---|---|
| PowerPoint: "could not open the file" | invalid `a:pattFill prst` value (`pct35` does not exist) | only use `pct5,10,20,25,30,40,50,60,70,75,80,90` |
| PowerPoint: repair prompt after editing chart build | wrote `<p:bldChart>` directly under `<p:bldGraphic>` | correct shape is `<p:bldGraphic spid="5" grpId="0"><p:bldSub><a:bldChart bld="series"/></p:bldSub></p:bldGraphic>` |
| chart data labels disappear / " > 100 ms" garbage | injected `<p:cTn>` into `c:dLbls` or wrong child order | rebuild the whole `c:dLbls` in schema order (numFmt, spPr, txPr, dLblPos, show*) |
| inserted `c:spPr` rejected | `c:spPr` placed first in `c:ser` | insert after `a:xfrm`/correct position per order |
| logo image shows old picture after swap | swapped the shared media part but the slide blip still points to it via a *different* rel | per-slide `slide.part.get_or_add_image_part(path)` + `slide._element.find('.//a:blip').set('{r}embed', rid)` |
| PDF export silently skips the second file | PowerPoint COM allows one `SaveAs(..., 32)` per open presentation | export each PDF in a **separate** COM session |
| slide background has white gaps | a full-bleed background shape was dragged/resized | assert full-bleed shapes are exactly `(0,0,W,H)`; `layout_audit.py` flags it |
| video does not loop | only the shape is a video, nothing in timing says so | set `repeatCount="indefinite"` on the `p:video/p:cMediaNode/p:cTn`; verify it survives a PowerPoint round-trip |
| charts "build" but look like one block | `bldSub` present but entrance is a plain fade | pair the build with a wipe (`wipe(up)` vertical bars, `wipe(right)` horizontal bars) |
| fonts/colours change "by themselves" | PowerPoint re-saved and deduplicated media, re-encoded JPEGs | never trust file size; compare renders and media hashes, not bytes |
| PowerShell mangles Chinese/emoji in inline edits | `-replace` + console code page | use file-writing tools / `PYTHONIOENCODING=utf-8`; never patch code with `-replace` |
| screen capture of a running slideshow grabs the wrong window | slideshow window is separate/behind | do not fake verification; ask the user to press F5, or capture the `screenClass` window explicitly |
| `%` formatting crashes on `∫`, `·`, `²` | Windows console GBK encoding | `$env:PYTHONIOENCODING="utf-8"` and ASCII-safe logging |

## Deliverable checklist

- [ ] `output/<Name>_vNN.pptx` — the only file to project
- [ ] `output/*_main.pdf` and `*_all.pdf` — hidden backup pages stripped / kept
- [ ] `PREVIEW_vNN.png` + `PREVIEW_vNN_before_after.png` — contact sheet and delta sheet
- [ ] `DESIGN_AND_ASSETS_vNN.md` — what changed, with measured numbers (contrast, EMU offsets)
- [ ] `ANIMATION_SPEC_vNN_ZH.md` — per-slide entrance/build/cue rules
- [ ] speech pack: `SPEECH_EN_ONLY`, `SPEECH_EN_ZH`, `CUE_CARD`, `TIMING_TABLE`
- [ ] `DELIVERY_AUDIT_vNN.json` — hashes, counts, page counts, "old version untouched"
- [ ] on-site folder + zip + `SHA256SUMS.txt`

## Forking this skill for another talk

The engine (this file, `references/01`–`07`, `scripts/`) is deck-agnostic; only the identity layer
is specific. To produce a skill for the next deck:

1. copy the skill folder to `~/.codex/skills/<new-name>` and `~/.dsh/skills/<new-name>`;
2. replace `assets/identity/brand-tokens.json` and regenerate `IDENTITY_CARD.png`;
3. rewrite the first paragraph of `references/08-house-identity.md` (palette/type/furniture) and
   the frontmatter `description`;
4. keep `references/00`–`07`, `09` and every script as-is — that is the reusable part;
5. add a `notes/<deck>-history.md` recording the deck's own decisions (what the user chose, which
   version introduced what) so a later session does not relitigate them.

If the new deck shares the same house style, do not fork at all: just point this skill at it and
keep the identity unchanged.

## Stop conditions — ask instead of guessing

- A taste decision conflicts with a measurable rule (contrast under 3:1, two accent colours).
- The user's manual edit moved a full-bleed layer or broke a frame; repair and *report*, never
  silently "improve" their layout choices.
- Behaviour that can only be confirmed by human eyes (animation pacing, video legibility on the
  venue projector) — say so and give the exact pages to check.
