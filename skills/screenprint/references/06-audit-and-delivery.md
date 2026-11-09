# Audit, export and on-site packaging

Everything here exists because "it opened fine on my machine" is not evidence.

## 1. PowerPoint COM export (the only renderer that matters)

```powershell
$pp = New-Object -ComObject PowerPoint.Application
$pres = $pp.Presentations.Open($src, $true, $false, $false)   # ReadOnly, Untitled, WithWindow
foreach ($i in 1..$pres.Slides.Count) {
    $pres.Slides.Item($i).Export(("{0}\p{1:d2}.png" -f $pngDir, $i), "PNG", 1600, 900)
}
$pres.Close(); $pp.Quit()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($pp) | Out-Null
```

Rules:

- **One PDF per COM session.** `SaveAs($path, 32)` works once per open presentation; a second
  call silently does nothing. Open a fresh presentation for the second PDF.
- To strip hidden backup pages from the printable PDF, set
  `$slide.SlideShowTransition.Hidden = -1` for those slides and
  `$pres.PrintOptions.PrintHiddenSlides = 0` before `SaveAs`.
- `Slide.Export` renders the *final* animation state. Animated build steps are invisible here —
  never claim an animation works because the PNG looks right.
- Export at 1600×900 for review; keep the PNGs in `build/native_vNN/` so before/after sheets can
  be built later without re-exporting.

## 2. Structural audits

`scripts/verify_package.py` answers, from the file alone:

- zip integrity (`testzip() is None`), slide count, hidden-slide list
- per-slide click-group count (total and per page)
- text identity vs a reference deck (normalised `a:t` concatenation)
- media: count, sha256 per mp4, which parts changed
- animation inventory: effects, ink-rise (`ppt_y`) count, chart builds (`a:bldChart bld=`)
- loop flags, `repeatCount="indefinite"`

`scripts/diff_decks.py` answers *what the user changed*: text edits, moved shapes, recolours,
media swaps, click-count deltas. Run it before judging a hand-edited deck.

`scripts/layout_audit.py` answers geometry sanity: bleed, off-slide, zero-size, overflow
estimate, overlapping text boxes, rail intrusions.

## 3. Pixel checks

- Same page, before vs after: `mean abs diff < 1` on unchanged regions; if larger, find out why
  (recompression, moved shape, different export scale).
- Full-deck contact sheets (`make_contact_sheet.py`) for the delivery message; label each tile
  with the version and page so the user can point at one.
- Before/after sheets: two columns, same crop, so the difference is legible without opening files.

## 4. On-site package

```
talk_kit_YYYYMMDD/
  00_现场提示卡.md              # one-page cue card
  README_导读.md               # what to grab in a hurry
  FILE_INDEX.csv               # file → purpose
  SHA256SUMS.txt
  01_slides_放映/              # the .pptx, and only that
  02_pdf_静态备份/             # main + all
  03_speech_讲稿/              # EN only, EN+ZH, cue card, timing table
  04_qa_问答/                  # Q&A bank, quick reference
  05_operation_操作指引/       # click map, page map, rehearsal plan
  06_design_设计说明/          # design + animation notes, photo credits
  07_manuscript_稿件/          # frozen manuscript artefacts
  08_preview_预览/             # contact sheets
```

Zip it, write `SHA256SUMS.txt`, and record the zip hash in your reply. Rebuild the kit from the
newest release every iteration — never edit a kit by hand.

## 5. Delivery message template

```
1. What changed      — table: item / was / now
2. Proof             — screenshot or before/after sheet inline
3. Checks            — table: pages, clicks, videos, text parity, PDF pages
4. Files             — links to pptx, sheet, note, kit
5. Needs your eyes   — the 1–3 things only a human can confirm (animation pacing, projector
                       colour, video legibility), with the exact pages to press F5 on
6. Still open        — decisions you deliberately left to the user
```

Keep 5 and 6 short; they are the part the user actually acts on.

## 6. Failure handling

- **PowerPoint says "could not open the file"**: your XML is invalid. Undo the last structural
  edit, compare against a known-good snippet, re-validate. Do not retry the same write.
- **PDF is missing pages**: check the hidden-slide flags you just wrote and the COM-session rule.
- **Renders show white gaps**: a background shape moved; check bleed.
- **File size dropped a lot after the user edited**: media dedupe, not quality loss — verify by
  pixel diff before saying anything.
