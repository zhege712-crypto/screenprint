---
name: screenprint-defense
description: Build a thesis / project defence deck (.pptx) end-to-end — 15-20 minute defence plus Q&A — using the screenprint engine (OOXML editing, PowerPoint-verified exports, chart/video pipeline, speech pack) with defence-specific structure, committee-facing rules, a predicted-question bank and backup pages.
whenToUse: 用户要做答辩 PPT（本科/硕士/博士/项目验收/开题/中期），需要按评委视角组织页面、控时、准备追问预案与备份页，并导出可放映文件；或需要审查已有答辩 PPT 的结构与答辩风险。
---

# Screenprint Defense — 答辩 deck

This skill is the **defence-specific layer** on top of `screenprint`. Do not duplicate the
engine: load `screenprint` for the mechanics (probe → versioned build → render → audit →
package, OOXML recipes, video/texture pipeline, speech pack) and use this file for what makes a
defence different.

Engine files to reuse (same machine, sibling skill):

```
~/.codex/skills/screenprint/SKILL.md            workflow, non-negotiables, pitfalls
~/.codex/skills/screenprint/references/00-09    fundamentals, OOXML, assets, layout, audit, speech
~/.codex/skills/screenprint/scripts/*.py|ps1    probe / verify / diff / layout / ooxml / export
~/.codex/skills/screenprint/assets/identity/    house style (fork per institution)
```

## What is different from a conference talk

| Dimension | Conference talk | Defence |
|---|---|---|
| Audience | strangers, curious | committee, adversarial, has read the thesis |
| Goal | make the result memorable | prove **you did it**, it is sound, and you know its limits |
| Structure | problem → method → evidence | background → gap → **my contribution** → validation → limitations → plan |
| Time | 12 min, 1 min Q&A | 15–20 min + 10–30 min Q&A; keep 3–5 min slack |
| Failure mode | losing attention | being unable to answer "what is yours?" / "why this baseline?" |
| Slides | narrative | narrative **plus** dense backup pages the committee can ask for |
| Claim style | headline result | claim + **evidence + scope + limitation**, in that order |

## Non-negotiables for a defence

1. **Contribution page early** (by slide 3–4): one slide that separates *what existed*,
   *what you changed*, *what it buys*. The committee decides your grade on this slide.
2. **Every claim carries its scope**: dataset / conditions / assumptions / where it breaks.
   A defence that overclaims is worse than one with modest results.
3. **Backup pages are the defence**: 8–15 hidden slides — parameter tables, extra baselines,
   ablations, failure cases, proofs/sketches, reproducibility details. Map them in a cue card
   (`B3 = …`) so you can jump instantly.
4. **Nothing on screen you cannot defend**: no borrowed figure without credit, no number you
   cannot reproduce, no "we" claim you cannot attribute to a chapter/experiment.
5. **Rehearse the clock twice**: once content, once clicks-only. Overrun is scored.
6. **Slide text is not the thesis**: 15–40 English words per slide; the argument lives in speech.

## Structure template (20 min, 16–20 main slides)

| # | Slide | Purpose | Time |
|---|---|---|---|
| 1 | Title + name + advisor + institution + date | identity | 30 s |
| 2 | Outline / one-sentence thesis statement | orientation | 30 s |
| 3 | Background & problem (with figure) | shared ground | 2.5 min |
| 4 | Gap: what existing methods cannot do | why this work exists | 2 min |
| 5 | **Contribution page** (3 bullets, each = claim) | the core | 1.5 min |
| 6–8 | Method: formulation → algorithm/architecture → key design choice | rigour | 5 min |
| 9–13 | Validation: setup, main result, ablation, comparison, robustness | evidence | 6 min |
| 14 | Limitations & threats to validity | honesty | 1.5 min |
| 15 | Conclusion + future work | closure | 1 min |
| 16 | Backup index (hidden) | navigation | — |
| B1–B15 | backup pages (hidden) | Q&A ammunition | — |

Adapt: a master's defence usually 15 min/12 slides; a PhD 40 min/30 slides. Keep the same order.

## Committee questions you must be able to answer from a slide

Load `references/defense-playbook.md` for the full bank. The top ten:

1. What exactly is your contribution versus the cited work? (→ slide 5, B1)
2. Why this method and not the obvious baseline? (→ B4/B5)
3. What are the assumptions, and what happens if they break? (→ slide 14, B7)
4. How do you know the improvement is not noise? (→ B9, repetition/CI)
5. What is the computational cost? (→ B6)
6. Which hyperparameters matter, and how were they tuned? (→ B8)
7. Does it generalise beyond the tested scenarios? (→ B10)
8. What is the failure case you saw, and why? (→ B11)
9. How would you productionise / what would you do with 6 more months? (→ slide 15)
10. Reproduce this result from scratch — what do I need? (→ B12, reproducibility)

## Workflow overlay

1. Run `screenprint` phases 0–1 as usual (probe, fundamentals, identity).
2. **Before building pages**, extract the defence backbone: contribution statement, evidence list
   with scope, limitation list, predicted questions → maps onto slides + backups.
3. Build main slides; build backup pages **at the same time** (they are the answer key).
4. Produce a `CUE_CARD` where each row is `page / clicks / what to say / likely question → backup`.
5. Audit with `verify_package.py` (page count, click count, hidden backup list, text parity) and
   `layout_audit.py`; render every page and read it as a committee member would.
6. Deliver: deck, main+full PDF, cue card, question bank, timing table, rehearsal checklist.

## Identity

Fork `screenprint/assets/identity/brand-tokens.json` for the institution template
(university logo in ice-ink on the band, school colours as the single accent). Keep the engine's
page-furniture geometry unless the institution mandates a template — if a template is mandated,
override `geometry_emu` in the new tokens and regenerate `IDENTITY_CARD.png` with
`make_identity_card.py`.

## Stop conditions

- The user cannot state the contribution in one sentence → stop and fix that before designing.
- Results shown do not match the thesis/paper → stop; a mismatch on stage is unrecoverable.
- Time budget exceeds the slot by >15% → cut content, not slides' font size.
