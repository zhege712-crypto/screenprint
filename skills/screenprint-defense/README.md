# screenprint-defense（答辩 deck）

答辩变体，加载 `screenprint` 引擎（丝网印刷视觉体系 + OOXML/导出/审计脚本），只补答辩专属的结构与追问预案。

答辩（本科/硕士/博士/项目验收/开题/中期）专用 skill：结构与追问预案是本 skill 的职责，
做页/动画/审计/打包的引擎直接复用同机的 `screenprint`，不重复实现。

## 结构

```
SKILL.md                         答辩特有的铁律、结构模板、与会议报告的差异表、工作流叠加、停止条件
references/defense-playbook.md   贡献一句话模板、页面级证据规则、15 个备份页清单、
                                 按评委类型的追问预案、排练清单、交付清单补充
agents/openai.yaml               Codex 显示名与默认提示
```

引擎依赖（同机路径，按需加载）：

```
~/.codex/skills/screenprint/SKILL.md
~/.codex/skills/screenprint/references/00-09
~/.codex/skills/screenprint/scripts/
~/.codex/skills/screenprint/assets/identity/
```

## 装在哪

```powershell
# 本 skill 已在：
#   %USERPROFILE%\.codex\skills\screenprint-defense      (Codex)
#   %USERPROFILE%\.dsh\skills\screenprint-defense        (DSH)
# 从任一位置同步到另一个宿主：
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\screenprint\scripts\sync_skill.ps1" -Name screenprint-defense -Source "$env:USERPROFILE\.codex\skills\screenprint-defense"
```

## 最小使用流程

1. 让用户先写出 **一句话贡献**（写不出就停下）；
2. 按 `SKILL.md` 的 16 页结构列页面清单 + 15 页备份清单；
3. 用 `screenprint` 的引擎建页：`pptx_probe.py` → 版本目录 → `export.ps1` → `verify_package.py` → `layout_audit.py`；
4. 生成 `CUE_CARD`（含"可能被问 → 跳 Bx"列）、`QUESTION_BANK.md`、时间检查点表；
5. 交付：主讲 PDF + 全本 PDF（含备份页）+ 讲稿 + 追问预案。

## 与会议报告 skill 的分工

- 会议报告：叙事、时间紧、听众陌生 → `screenprint`；
- 答辩：贡献前置、证据带范围、备份页即答案库 → 本 skill；
- 两者共用同一套引擎与视觉标识（院校模板需替换 `brand-tokens.json` 后重新生成标识卡）。
