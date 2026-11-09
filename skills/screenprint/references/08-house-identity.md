# 本套 deck 的视觉标识（house identity，可替换）

这是**可替换层**。引擎（SKILL.md、references/01–07、scripts/）不变，换一套 `brand-tokens.json`
+ 重跑 `scripts/make_identity_card.py`，就是另一场报告的风格。

当前标识：**screenprint —— 暖纸上的丝网印刷**
（深藏青油墨 + 冰白印字 + 单色网点纹理，像印在纸上的技术手册，不像"科技蓝渐变 PPT"。）

![identity card](assets/identity/IDENTITY_CARD.png)

机器可读版本：`assets/identity/brand-tokens.json`（脚本应优先读它，不要把颜色抄进代码）。

## 1. 色板

| 名称 | 值 | 用途 | 对比度 |
|---|---|---|---|
| paper | `#FBF6EE` | 纸面（满版纹理底） | — |
| ink_navy | `#17364A` | 深色带、深色面板、表头、主字、数据系列一 | 11.7:1 于纸面 |
| ink_teal | `#087F8C` | 强调：标题竖条、正文页眉标、关键陈述 | 4.4:1 |
| ink_orange | `#CB672A` | 数据系列二、对照强调 | 3.5:1（仅限大字/粗体） |
| ink_ice | `#DDEBEF` | 深色带上的字、冰白 logo | 9+:1 于藏青 |
| caption | `#4C5D66` | 图注、副标题、注释 | 6.4:1 |
| grey_strip | `#C7D2D7` | 照片下方说明条底 | — |
| accent_theme2 | `#E97132`（用户选定） | 目录序号、封面竖条、结束页标题 | 2.8:1（大字勉强，慎用） |
| accent_amber | `#FFC000`（用户选定） | 章节页眉标 | 于藏青 ~8:1 |

规则：**一个强调色 + 两个数据色**；数据只用 navy/orange，绝不引入第三种数据色。
用户手选的橙色（`E97132` / `FFC000`）即使在对比度上不理想，也不要擅自改——报告数据，让他决定。

## 2. 字体阶梯（pt）

| 角色 | 字号 | 字重 |
|---|---|---|
| 封面标题 / 结束页标题 | 42 / 48 | Bold |
| 正文页标题 | 31.5 | Bold |
| 章节页标题 / 序数 | 46.5 / 142.5 | Bold |
| 目录条目 | 24 | Regular |
| 结论条目 | 24 | Bold |
| 陈述 / 注释型要点 | 21.75 | Bold |
| 侧栏要点 / 面板标题 | 20.25 | Bold |
| 图内小标题 / 副标题 | 18.75 | Bold / Regular |
| 图注 | 13.15 | Regular |
| 页码 | 12 | Regular |
| 页脚 | 9.5 | Regular |
| 照片说明 / 署名 | 9.0 | Regular |

一种字体（Arial / Helvetica），只用粗细和字号区分层级。

## 3. 版面骨架（EMU）

```
header band : (0, 0, 12192000, 800000)      ink_navy，满宽
footer rail : (0, 6480000, 12192000, 378000) ink_navy，满宽
margin      : 609600 左右对称
title       : top 866775，左侧 609600，前面一条 47625×371475 的 teal 竖条
caption     : top ≈ 6172200
logo        : 冰白单色，垂直居中于 header band（top = 400000 - h/2）
page number : 12 pt，right 对齐，垂直居中于 footer rail
```

章节页：左侧 ≥ 60% 宽的深色面板（`pattFill` 网点 5%），右侧照片或大号序数；
照片下方 0.2 cm 说明条底色 `#C7D2D7`。

## 4. 母题（motifs）

- **monochrome halftone**：旋转栅格网点，1920 宽时 pitch 13–18 px，从"干净中心"向外加密，
  最外圈压藏青 + 一条发丝套准圆环。用于封面/结束页装饰盘。
- **single-family stripes**：45° 单一家族，pitch 13 px、线宽 2.4 px；**不做交叉网格**。
- **pattern tile**：深色块（表头、章节面板）用 navy 底 + 5–30% 纸色圆点的 `pattFill`。
- **ice logos**：把校标/会标的彩色版本转成冰白单色（去白底、按亮度映射 alpha），直接压在
  navy 带上，**不要白色斜切底板**。

## 5. 动效语言

- 入场：文字 `fade + ink rise`（`ppt_y+0.024/0.038`，0.52–0.66 s，decel 20000）；
- 图表：`bldSub + a:bldChart`（单系列/堆叠用 `category`，成对柱用 `series`）+ 相应擦除；
- 视频：1280×520 @ 60 fps，点击播放、循环，poster 用末帧/中间帧；
- 点击预算：21 页主讲 = 43 组点击；丰富动效时**不加点击停点**。

## 6. 禁忌

- 标签白底板、第三种数据色、柱子里的渐变、页脚/页码"部分页面有部分没有"；
- 不存在的 `pattFill` 预设（`pct35` 会毁文件）；
- 小于 4.5:1 的小字、4 个以上要点一页、把论文里没有的数字放上幻灯片。

## 7. 为下一套 deck 派生

1. 复制 `assets/identity/brand-tokens.json` 为新名字（如 `brand-tokens-<slug>.json`）；
2. 改 palette / type_scale / geometry / motifs；把 `identity` 字段换成新 deck 的名字；
3. `python scripts/make_identity_card.py --tokens <新json> --out IDENTITY_CARD.png`；
4. 新 skill 目录里替换 `assets/identity/`，`references/08-house-identity.md` 改标题与说明，
   其余引擎文件原样保留（或引用本 skill 作为实现依赖）。
