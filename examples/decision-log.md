# Case study: one real 30-slide talk deck

A condensed, anonymised decision log from building a conference talk deck with this skill.
Useful as a worked example of what "the deck is a product with evidence" looks like in
practice. Names, venues and paper identifiers were removed.

## Non-negotiable choices (the user made them; the skill keeps them)

| Item | Choice | Why |
|---|---|---|
| Ink palette | deep navy `#17364A` + ice `#DDEBEF` + warm paper `#FBF6EE` | screen-print feel, not "tech gradient" |
| Accent | orange chosen by the user (`#E97132` theme accent, `#FFC000` eyebrow) | deliberate; contrast 2.8:1 was *reported*, not silently "fixed" |
| Type | one family (Arial), hierarchy by size/weight only | projection legibility |
| Decoration | none: no footer rule, no corner squares, no dot grids | less chrome, more signal |
| Data colours | two only: navy + orange | never a third series colour |
| Paper | frozen; the deck may simplify but never add a number | evidence discipline |

## Version timeline (what each iteration bought)

| Version | Change | Lesson |
|---|---|---|
| v20–v22 | visual exploration, screen-print language established | halftone + warm paper reads as "printed", not "clip-art" |
| v24–v25 | animation system | fade + 24–38 EMU ink rise, 0.52–0.66 s, decel 20000 |
| v26 | constructivist layout | divider numerals, side statements, delete leftover marks |
| v27 | consistency pass | page furniture identical on every page |
| v28–v31 | print-style charts + baked textures | texture goes into the background JPEG, text stays on top |
| v32 | header band system | navy band + ice logos, no white plates |
| v33 | stripe discs + footer rail | bottom rail mirrors the header band |
| v34 | plain cover/closing | removing the decorative disc fixed "too busy" |
| v35 | one type scale | 12 same-role size/weight mismatches normalised |
| v36 | repair hand-edited deck | a dragged full-bleed layer = white gaps; diff before judging |
| v37 | contrast pass | captions 4.39 → 6.37:1; side text 1.67 → 5.27:1 |
| v38 | chart build | `bldSub + a:bldChart` + wipe; labels on the bars |
| v39 | real video | insertion and braking clips rendered from the project scene, looped |
| v40 | speech pack | pointer phrases, cue card, 1238 words / 717 s |

## Numbers that acted as anchors

- 30 slides = 21 main + 9 hidden backups
- 43 click groups across the main pages
- 6 embedded clips, all 1280×520 @ 60 fps, 6 s
- page geometry: 12192000 × 6858000 EMU; header band 800000; footer rail 378000; margin 609600

## Time sinks (avoid them)

1. `pattFill prst="pct35"` does not exist — the file will not open.
2. `<p:bldChart>` goes inside `<p:bldSub>`; anywhere else triggers a repair prompt.
3. `c:dLbls` must be rebuilt in schema order; inserting one child mangles labels.
4. PowerPoint COM allows one `SaveAs(..., 32)` per open presentation.
5. Repointing a logo means re-relating the blip per slide; replacing shared media hits every page.
6. Screen-capturing a running slideshow grabs the wrong window — ask the user to press F5 instead.
7. When a hand-edited file shrinks by 3 MB, it is media dedupe, not quality loss — pixel-diff first.
