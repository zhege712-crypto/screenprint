# Speech script, pointer phrases and the cue card

A deck review almost always turns into "update the speech". The speech must track the *seventh*
slide build, not the first draft: every click, loop, build animation and label the audience can
see has to be reflected in what you say.

## 1. Structure per slide

```
SLIDE NN  <title> (<seconds> s, <n> click groups)
on screen: <one line describing exactly what is visible, including panels/labels>
<spoken text: English, conversational, numbered digits spelled out for delivery>
[ cue ]  <what to click / when to wait / what to point at>
```

The bilingual variant adds `中文讲解` and a Chinese delivery cue. Keep one file per language
mode; do not mix, or you will read the wrong line on stage.

## 2. Word budget

```
words ≈ seconds × wpm / 60
```

Reference numbers: 1238 words / 717 s ≈ 104 wpm. That is deliberately slow, because the time
includes six video plays and four chart builds where nobody speaks. Plan ~100–110 wpm for a
deck with media, ~130–140 wpm for a text-only deck. Report the count and the implied rate in the
file header so the presenter can calibrate.

Silence budget rule of thumb: 6 s video ⇒ ~10 s of wall time, 2 s chart build ⇒ pause 1 s before
speaking again.

## 3. Pointer phrase bank

The purpose is to move the audience's eyes, not to decorate. One pointer phrase per slide is
usually enough; two on a busy chart page.

**English**
- "Have a look at the two curves."
- "Keep your eye on the orange car."
- "Watch the bars come in — one at a time."
- "Notice the gap between those last two bars."
- "This number right here is the one I want you to remember."
- "I have put the numbers on top, so you can check me instead of trusting my adjectives."
- "Here is the honest part: …"
- "Read this as a trade-off, not a leaderboard."
- "And yes, the second plot zooms in, so mind the axis scale."
- "Bear with me, this is the fine print."
- "Both of them loop, so you can take your time."

**中文（若中英混讲）**
- 「看这两条曲线。」
- 「注意那辆橙色的车。」
- 「看柱子一条条长出来。」
- 「看最后两根柱子之间的差。」
- 「这个数字请记一下。」
- 「我特意把数字标在柱顶，方便你核对。」
- 「说实话，这里是权衡，不是排名。」
- 「右图是放大图，注意坐标轴刻度变了。」

Rules: the pointer phrase names a *thing* ("the orange bar", "the dashed line"), never a
direction alone ("over there"); and the sentence after the pointer must deliver the point, not
describe the picture.

## 4. Cue card

One page, one row per slide, five columns: page / clicks / animation timing / where to point /
first words. It exists so the presenter can recover after a stumble without finding the page in
a 12-page script.

```
| 页 | 点击 | 动画/视频时机 | 手指向 | 开口先说什么 |
| 5 | 3 | 左循环、右循环、再出问题 | 左面板 → 右面板的间距 | "Both of them loop, take your time…" |
```

Add three iron rules at the bottom: pause after every click; point once per page; never click
past the closing slide.

## 5. Keeping speech and deck in sync

Re-derive, do not patch, whenever the deck changes structurally:

- click counts changed → click map, speech cues, rehearsal plan all change
- video now loops → "wait for it to finish" becomes "don't wait, it loops"
- chart now builds → add a pause and a pointer phrase
- labels added → say "check the numbers", not "trust me"

Verify mechanically: the per-slide `N click groups` in the speech header must equal
`click_groups` from `scripts/pptx_probe.py`. A one-line assertion in the speech build script
prevents the classic "speech says three clicks, slide has two".

## 6. Claims discipline

The speech may simplify but never strengthen a claim. If the slide says "the result is 0.9 s earlier",
the speech says "about one second earlier, roughly" — not "much earlier". Every number spoken
must appear on the slide or in the paper.

## 7. Delivery build script

Generate the speech files from a Python data structure (list of per-slide records), then the
script can compute word counts, timing tables and cue cards automatically, and re-assert the
click counts. Editing 20 hand-written .txt files will drift; a data structure will not.
