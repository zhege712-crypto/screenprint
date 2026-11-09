# screenprint（丝网印刷）

**命名来由**：这套 deck 的整体视觉就是「暖纸上印油墨」——半调网点、单一家族条纹、藏青底上的冰白印字、套准圆环。所以技能名直接取 **screenprint（丝网印刷）**；它不是某一个文件格式工具，而是这套印刷式 deck 的引擎。

**命名家族**：screenprint 是引擎（工作流 + OOXML 配方 + 脚本 + 视觉标识）；同名前缀的兄弟技能是题材变体——现已有 screenprint-defense（答辩），后续可加 screenprint-poster / screenprint-viva / screenprint-lecture。变体**不复制引擎**，只加载 screenprint 并补差异。

把一整套"做报告 PPT"的实战流程固化下来：从基本要求、视觉标识、探测旧稿、改页、
渲染核对、结构审计，到动画/视频、讲稿提示卡、现场资料打包。

## 装在哪

规范位置是 `~/.codex/skills/screenprint`（Codex 原生读取），镜像一份到
`~/.dsh/skills/screenprint`（DSH 技能目录）。两份内容一致，用
`scripts/sync_skill.ps1` 同步（会自动跳过"源=目标"的那份）。

```powershell
powershell -ExecutionPolicy Bypass -File scripts\sync_skill.ps1
```

装好后：

- **DSH**：技能出现在会话 skill catalog，用 `skill` 工具按名加载，或 `$screenprint` 点名；
- **Codex**：`agents/openai.yaml` 提供显示名与默认提示，重启会话后按目录扫描生效。

## 三层结构

| 层 | 文件 | 说明 |
|---|---|---|
| 通用要求 | `references/00-deck-fundamentals.md` | 页数/时间预算、投影可读性、信息密度、内容纪律、现场自检——与设计无关的及格线 |
| 视觉标识 | `assets/identity/brand-tokens.json`<br>`assets/identity/IDENTITY_CARD.png`<br>`references/08-house-identity.md` | 本套 deck 的色板、字阶、版面骨架、母题、动效语言、禁忌；**唯一需要为新 deck 替换的部分** |
| 引擎 | `SKILL.md`、`references/01`–`07`、`09`、`scripts/` | 与 deck 无关的方法与脚本 |

## 工具授权

做 deck 期间可自由调用本机创作工具，不需要逐次申请（细节与路径见
`references/09-local-tools.md`）：

- **Blender** `%BLENDER_EXE%` —— 复用 `.blend` 场景渲染概念动画；
- **ComfyUI** `%COMFYUI%\draw.cmd` —— 按需启动出概念图/纹理母图，出完自动退出；
- **ffmpeg/ffprobe** —— 逐帧转 mp4、探规格、抽封面帧；
- **Python** 两套：DSH 运行时（python-pptx/lxml/Pillow/pypdf）与 `D:\python`（matplotlib/cv2/torch）；
- **PowerPoint COM** —— 唯一可信的渲染校验与 PNG/PDF 导出。

约束：不联网装新东西、只动 deck 工作目录、每个生成素材都要有回执（参数/种子/脚本）。

## 依赖

- Python：`python-pptx`、`lxml`、`Pillow`、`pypdf`（DSH 运行时已含）
- PowerPoint（Windows COM）：渲染校验、导出
- 可选：`ffmpeg`、Blender、ComfyUI

## 目录

```
SKILL.md                         控制层：触发边界、铁律、7 阶段、路由、命令、陷阱表
assets/identity/                 视觉标识（tokens + 标识卡）
references/
  00-deck-fundamentals.md        演讲 PPT 基本要求（及格线）
  01-workflow-and-versioning.md  目录约定、迭代环、用户手改稿处理、回执
  02-ooxml-recipes.md            动画/图表构建/媒体循环/填充/rels 正确写法
  03-figure-assets.md            网点、条纹、渐变、羽化避让、烘焙进纸面
  04-video-pipeline.md           Blender 渲染、ffmpeg 编码、换视频与封面、循环
  05-layout-and-typography.md    字级表、对比度阈值、几何审计、改动汇报
  06-audit-and-delivery.md       COM 导出、结构审计、像素比对、现场包
  07-speech-and-cues.md          讲稿结构、指屏话术、提示卡、时间预算
  08-house-identity.md           本套标识说明 + 如何派生给下一套 deck
  09-local-tools.md              本机工具清单、路径、用法、授权与禁令
scripts/
  pptx_probe.py                  整本清点
  verify_package.py              结构校验 + 与旧版对比 + 回执
  diff_decks.py                  两份 deck 的差异
  layout_audit.py                出血/越界/溢出/重叠/压底栏
  ooxml_ops.py                   图表构建/擦除/循环/换色/换媒体/移动
  make_contact_sheet.py          缩略总表与前后对照
  make_identity_card.py          由 tokens 生成标识卡
  export.ps1                     COM 导 PNG/PDF（含隐藏页剥离）
  sync_skill.ps1                 同步到 .codex / .dsh
agents/openai.yaml               Codex 显示名与默认提示
```

## 一次迭代的最小命令链

```powershell
python scripts/pptx_probe.py old.pptx --json probe.json
powershell -ExecutionPolicy Bypass -File scripts\export.ps1 -Pptx copy.pptx -OutDir out\png -Png
python scripts/verify_package.py copy.pptx --ref old.pptx --expect-slides 30 --json audit.json
python scripts/layout_audit.py copy.pptx
python scripts/ooxml_ops.py chart-build copy.pptx --slide 10 --shape-id 5 --mode category --wipe right
python scripts/make_contact_sheet.py out\png --out preview.png --pages 1,5,10,15
```
