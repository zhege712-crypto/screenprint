# Workflow, directories and versioning

## 1. Directory convention

```
presentation/
  <date>_<slug>_vNN/            # one immutable release per iteration
    output/                     # what the user opens
      <Name>_vNN.pptx
      <Name>_vNN_main21.pdf     # hidden backup pages stripped
      <Name>_vNN_all30.pdf      # everything, for archive
      PREVIEW_vNN.png
      PREVIEW_vNN_before_after.png
      DESIGN_AND_ASSETS_vNN.md
      ANIMATION_SPEC_vNN_ZH.md
      SPEECH_EN_ONLY_vNN.txt
      SPEECH_EN_ZH_vNN.txt
      CUE_CARD_vNN.md
      TIMING_TABLE_vNN.md
      DELIVERY_AUDIT_vNN.json
  <date>_<slug>_vNN/build/      # scratch: candidates, probes, export caches
    candidate_vNN.pptx
    native_vNN/p01.png ...      # rendered pages of *this* candidate
    build_vNN.py                # the edit script, kept for reproducibility
    deliver_vNN.py              # packaging + audit script
    assets_vNN/                 # generated figures, videos, logos
```

Rules that keep this sane:

- `output/` is append-only. A correction becomes `vNN+1`, never an in-place edit.
- `build/` is disposable but kept, because "how did you make this page" has an answer.
- Assets live under the version that introduced them; never overwrite a previous
  `assets_vNN/` (a later version may reuse its bytes by hash).
- Batch versions (`deliverables/<kit>_YYYYMMDD/`) are rebuilt from the newest release,
  not hand-edited.

## 2. The iteration loop

```
probe → change table → candidate → render → diff/audit → package → present
```

1. **Probe**: `scripts/pptx_probe.py` gives pages, shapes, charts, videos, click groups,
   hidden pages. Paste the interesting rows into your own notes before touching anything.
2. **Change table**: state, per item, *what* changes (text? geometry? colour? timing?) and
   *what must not change* (page count, click count, paper numbers). This table becomes the
   table in the final reply.
3. **Candidate**: one script per iteration (`build_vNN.py`), reading the previous release and
   writing `candidate_vNN.pptx`. Never a chain of undocumented manual fixes; the script is the
   audit trail.
4. **Render**: export every changed page (and one unchanged neighbour as a control) and *look*.
5. **Audit**: `diff_decks.py` (what changed) + `verify_package.py` (counts/hashes) +
   `layout_audit.py` (geometry sanity).
6. **Package**: `deliver_vNN.py` writes docs, PDFs, previews, receipt.
7. **Present**: contact sheet + before/after + a table of changes + what still needs human eyes.

## 3. Handling the user's own edits

The user will open the pptx and change things by hand. That file is now the source of truth.

- Find it by mtime: `Get-ChildItem -Recurse -Include *.pptx | Where LastWriteTime -gt <release>`
- Diff it against the last release before judging anything:
  `python scripts/diff_decks.py release.pptx edited.pptx`
- Classify each change: **intended** (colour, wording), **accidental** (dragged full-bleed
  layer, indented one bullet, moved a frame), **side effect** (PowerPoint re-saved and
  deduplicated media, 13.9 MB → 10.9 MB — not quality loss).
- Repair only the accidental ones; keep the intended ones exactly; report the side effects.
- When a user-visible change interacts with a measurable rule (contrast < 3:1 for large text,
  two accent colours), recommend — do not silently override.

## 4. Keeping the paper frozen

If the deck accompanies a submitted/frozen paper:

- The deck may *omit*, *simplify* or *visualise*; it may not introduce a new number.
- Every number that appears on a slide must exist in the paper, the supplementary material,
  the recorded results, or the deck's own earlier version.
- Hidden backup pages are where extra detail lives; they are excluded from the printed PDF.
- When you must add content for Q&A, derive it from the data already inside the deck
  (chart caches, table values) and say so.

## 5. Receipts

`DELIVERY_AUDIT_vNN.json` is the machine-checkable story of the release:

```json
{
  "final_pptx": "...\\output\\<Name>_vNN.pptx",
  "sha256": "...", "bytes": 10922464,
  "slides": 30, "hidden_slides": [22, 23, ...],
  "click_groups_main": 43,
  "chart_builds": {"10": ["category"], "15": ["series", "series"]},
  "looped_videos": 2,
  "per_slide_text_identical_to_previous": true,
  "videos_byte_identical_to_v27": true,
  "main_pdf_pages": 21, "all_pdf_pages": 30,
  "previous_release_untouched": true
}
```

The receipt is how you answer "did you break anything" without re-deriving it by hand.

## 6. Scripts, not inline strings

- Write edit scripts to files (`build_vNN.py`) and run them. Do not assemble 200-character
  Python one-liners in a shell: quoting, encoding (`∫`, `·`, `²`) and escaping will bite.
- On Windows: `$env:PYTHONIOENCODING="utf-8"` for any script that prints non-ASCII.
- Prefer `write`/`edit` tools over PowerShell `-replace` for patching code. `-replace` has
  silently corrupted Chinese text and Python triple-quotes more than once.
- Keep the script's assumptions asserted: `assert len(blds) == 5`, `assert page_count == N`.
  A silent no-op edit is worse than a crash.
