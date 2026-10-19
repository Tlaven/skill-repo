# 独立复核报告 — pptx-delivery 测试证据复跑核对

**复核者**: Agent D(独立复核者,未参与原证据产出)
**复核时间**: 2026-10-19 11:06–11:09
**仓库(只读)**: `C:\Users\TL\skills-repo\pptx-delivery`
**副本(全部运行发生在此)**: `C:\Users\TL\AppData\Local\Temp\commandcode\C--Users-TL-skills-repo-essentials\23d8f706-fe95-40d3-bb8a-f8c8cfc83279\scratchpad\verify\agentD\pptx-delivery`
**总判定**: **证据可复现(REPRODUCIBLE)** — 0 处内容不一致。

---

## 1. 复跑方法

| 项 | 值 |
|---|---|
| 复制方式 | `robocopy <repo> <dest> /E /NFL /NDL /NJH /NP /R:1 /W:1`(含 `tests/out` 既有产物) |
| 复制结果 | robocopy exit=1(= 成功复制,非错误);Dirs 30/31(1 跳过),**Files 147 复制 / 0 FAILED**,4.11 MB |
| 复跑命令 | `python tests/run_tests.py --no-build --no-render`(cwd = 副本根) |
| 解释器 | Python 3.12.4 (`C:\Users\TL\.pyenv\pyenv-win\versions\3.12.4\python.exe`) |
| **退出码** | **0** |
| 复跑结果 | **9/9 PASS** |

**运行范围说明(诚实声明)**:`--no-build --no-render` 按要求只重跑 QA 阶段,复用副本内既有的
`.pptx` 与 `.pdf`(自仓库复制而来)。因此本次复跑证明的是 **QA 引擎对同一输入的判定与报告输出确定性一致**;
它 **不** 独立重证 build 步骤(node/pptxgenjs)与 render 步骤(WPS/PowerPoint COM)的字节级可复现性。
仓库 `tests/out/` 本身是 gitignore 的工作产物,严格意义上的"已提交证据"是 `tests/evidence/`;
`tests/out/reports/` 亦被一并对比并全部一致。

## 2. 复跑输出(关键行原样)

```
== summary ==
[PASS] clean: fired: (none) | flags=0, errors=0
[PASS] c1_placeholder: fired: C2-placeholder | flags=3, errors=0
[PASS] c2_lowcontrast: fired: C5-contrast | flags=2, errors=0
[PASS] c3_overflow: fired: C8-render-text | flags=1, errors=0
[PASS] c4_stretched: fired: C6-image-aspect | flags=1, errors=0
[PASS] c5_tinyfont: fired: C3-min-font | flags=1, errors=0
[PASS] c6_flatslide: fired: C9-editable | flags=1, errors=0
[PASS] c7_badcolor: fired: C4-color-hygiene, C5-contrast | flags=2, errors=1
[PASS] e2e_deck: flags=0, errors=0
```
退出码:`EXITCODE=0`

## 3. 对读表 [deck | 仓库证据 vs 复跑 | 一致? | 差异说明]

对比口径:忽略绝对路径前缀(同时替换 JSON 转义 `\\` 与非转义 `\` 两种拼写)。

| deck | 仓库证据 fired / summary | 复跑 fired / summary | 一致? | 差异说明 |
|---|---|---|---|---|
| clean | `[]` / e0 f0 i10 | `[]` / e0 f0 i10 | ✅ | 无。34 字段逐字段相同 |
| c1_placeholder | `[C2-placeholder]` / e0 f3 i9 | 同左 | ✅ | 无。40 字段相同(含 3 条 FLAG 明细文本) |
| c2_lowcontrast | `[C5-contrast]` / e0 f2 i10 | 同左 | ✅ | 无。40 字段相同(ratio 1.36 / 1.16 明细一致) |
| c3_overflow | `[C8-render-text]` / e0 f1 i9 | 同左 | ✅ | 无。34 字段相同 |
| c4_stretched | `[C6-image-aspect]` / e0 f1 i9 | 同左 | ✅ | 无。34 字段相同(deviation 50.0% 一致) |
| c5_tinyfont | `[C3-min-font]` / e0 f1 i10 | 同左 | ✅ | 无。37 字段相同(7.0pt vs min 10.0pt 一致) |
| c6_flatslide | `[C9-editable]` / e0 f1 i9 | 同左 | ✅ | 无。34 字段相同 |
| c7_badcolor | `[C4-color-hygiene, C5-contrast]` / e1 f2 i9 | 同左 | ✅ | 无。40 字段相同(ERROR `srgbClr val='#1E2761'` 一致) |
| e2e_deck | `[]` / e0 f0 i10 | 同左 | ✅ | 无。34 字段相同 |
| clean (out) | 同上 | 同上 | ✅ | 无 |
| c1_placeholder (out) | 同上 | 同上 | ✅ | 无 |
| c2_lowcontrast (out) | 同上 | 同上 | ✅ | 无 |
| c3_overflow (out) | 同上 | 同上 | ✅ | 无 |
| c4_stretched (out) | 同上 | 同上 | ✅ | 无 |
| c5_tinyfont (out) | 同上 | 同上 | ✅ | 无 |
| c6_flatslide (out) | 同上 | 同上 | ✅ | 无 |
| c7_badcolor (out) | 同上 | 同上 | ✅ | 无 |
| e2e_deck (out) | 同上 | 同上 | ✅ | 无 |

**18/18 组对比全部一致。**

### 3.1 报告文件:原始文本级一致性

不满足于"解析后 JSON 相等",进一步做了**原文逐字节**比对(路径替换后):

| 文件组 | 结果 |
|---|---|
| `tests/evidence/reports/*.json`(9 个) | **9/9 原文逐字节相同**(替换路径后) |
| `tests/out/reports/*.json`(9 个) | **9/9 原文逐字节相同**(替换路径后) |
| 复跑自身内部:`evidence/reports/*.json` vs `out/reports/*.json` | 9/9 相同(脚本按设计逐字复制) |

→ 连键顺序、缩进、空行都一致,不存在"值相同但结构被改写"的情况。

### 3.2 `tests/evidence/run.log`

| 项 | 值 |
|---|---|
| 仓库 run.log 行数 | 276 |
| 复跑 run.log 行数 | 243 |
| QA + summary 区段行数 | 仓库 242 / 复跑 242 |
| QA + summary 区段比对 | **逐行逐字节相同(True)** |

**唯一差异 = 我自己的运行参数造成的,不是证据差异**:
仓库日志比复跑多 33 行,全部是 build 段与 render 段的命令行/产物行
(`== build fixtures ==`、`$ node .../make_controls.js`、`$ node .../make_e2e_deck.js`、
`$ .../make_badcolor.py`、`wrote .../out/*.pptx`、`controls done`、`e2e deck done`、
`c7_badcolor.pptx written (corrupted=True)`、`== render <deck> ==` 与 9 条
`$ powershell ... render_slides.ps1 ...`)——这些正因 `--no-build --no-render` 而被跳过。
**复跑侧没有任何一行是仓库里没有的**(`rerun unique lines = 0`)。

## 4. 负控抽查结论

对 2 个负控做了"不信转述、独立验算"的抽查。

### 4.1 `c2_lowcontrast`
- `expected.json` 规定 `must_include = ["C5-contrast"]`
- 复跑实际命中:`["C5-contrast"]` → **相符**
- summary:`flags=2, errors=0, info=10`
- **独立 WCAG 重算**(用报告自己打印的 hex 值重算对比度,不采信工具口径):

| slide | 报告声称 | 我重算 | 前景/背景 | 偏差 | 结论 |
|---|---|---|---|---|---|
| 1 | 1.36 | **1.36** | `#DDDDDD` on `#FFFFFF` | 0.00 | 一致 |
| 2 | 1.16 | **1.16** | `#FCF6F5` on `#F9E795` | 0.00 | 一致 |

- 阈值 4.5(普通文本)下两条均远低于阈值 → 命中**真阳性**,非误报。
- 溯源 `tests/make_controls.js:92-113`:slide 1 用 `color:"DDDDDD"` 压 `C.white`;slide 2 用 `color:"FCF6F5"` 压 `C.cream`;
  `tests/lib.js:21` 定义 `cream: "F9E795"`、`:15` `white: "FFFFFF"` —— **报告记录的底色与夹具源码完全对得上**,说明背景色识别正确。

### 4.2 `c6_flatslide`
- `expected.json` 规定 `must_include = ["C9-editable"]`
- 复跑实际命中:`["C9-editable"]` → **相符**
- summary:`flags=1, errors=0, info=9`
- **独立开箱复检**(直接解压副本内 `c6_flatslide.pptx` 读 `ppt/slides/slide1.xml`,不采信工具结论):

| 检查 | 我实测 |
|---|---|
| 幻灯片尺寸 | `12192000 x 6858000 EMU` = 13.333in × 7.500in |
| slide 1 图片数 | 1 |
| 图片 extent | off=(0,0), ext=(12191695 × 6858000) → **覆盖 100.0% 画布** |
| 非空 `<a:t>` 文本 run 数 | **0** |
| 工具 C9 明细 | `slide looks non-editable: a picture covers 100% of the slide and no text was found` |

→ **独立判定:CONFIRMED**。整页图片 + 零文本客观存在,C9 命中是真阳性。
- 溯源 `tests/make_controls.js:170-177`:`s1.addImage({ path: flat-1600x900.png, x:0, y:0, w:13.333, h:7.5 })` —— 与实测完全吻合。

### 4.3 附带观察(非缺陷)
`c7_badcolor` 复跑命中 `[C4-color-hygiene, C5-contrast]`,而 `expected.json` 只要求 `C4-color-hygiene`。
这是 `must_include` 的**超集**(`check_expectation()` 只做子集断言),两侧一致,不构成差异;
C5 的 flag 也有客观成因(该 deck 同时含 `#FFFFFF` on `#FFFFFF` 与 `#CADCFC` on `#FFFFFF` 低对比文本)。
干净基线 `clean` 的误报闸门(`max_flags=0 / max_errors=0`)在复跑中同样通过。

## 5. 约束遵守与仓库完整性

| 约束 | 遵守情况 |
|---|---|
| 只读仓库(除复制动作) | ✅ 全部运行均以副本为 cwd;脚本经 `Path(__file__).resolve().parent.parent` 解析,`qa_check.py` / `render_slides.ps1` 均取副本内路径 |
| 不移动/改动原目录 | ✅ 仅 `robocopy` 单向读取 |
| 不修改仓库任何文件 | ✅ 见下方哈希/时间戳快照 |
| 全部运行在副本内 | ✅ |
| 不派子代理 | ✅ |

**仓库完整性证据**:原仓库 `tests/evidence/*` 全部 `LastWriteTime` 为 `2026-10-19 08:50:40`–`10:52:40`,
早于本次复核(`11:06` 起),即复核期间**未发生任何写入**;且仓库 `scripts/__pycache__` 不存在
(`Test-Path` = False),证明 Python 未在仓库侧生成字节码缓存。

复核后仓库证据 SHA-256(前 16 位)快照:

```
5824aeb5d8a0e235  2026-10-19 08:50:40  tests\evidence\normalize_check.log
ca46526625bae7d2  2026-10-19 10:52:27  tests\evidence\reports\c1_placeholder.json
1bb8ac3d3a885b49  2026-10-19 10:52:29  tests\evidence\reports\c2_lowcontrast.json
965a082065154e66  2026-10-19 10:52:30  tests\evidence\reports\c3_overflow.json
efe706a5e00dbad0  2026-10-19 10:52:32  tests\evidence\reports\c4_stretched.json
daf7c017f989e076  2026-10-19 10:52:34  tests\evidence\reports\c5_tinyfont.json
4f375d27a60ea1a6  2026-10-19 10:52:36  tests\evidence\reports\c6_flatslide.json
27deff263e910bc4  2026-10-19 10:52:38  tests\evidence\reports\c7_badcolor.json
b0ddb075f30e39bc  2026-10-19 10:52:25  tests\evidence\reports\clean.json
77065d308ff3c714  2026-10-19 10:52:40  tests\evidence\reports\e2e_deck.json
64d2204e6eebad74  2026-10-19 10:52:40  tests\evidence\run.log
```

## 6. 总判定

# 证据可复现(REPRODUCIBLE)—— 差异清单为空

- 复跑退出码 **0**,**9/9 PASS**,与仓库 `run.log` summary 区段逐字节相同。
- **18/18** 组报告(evidence 9 + out 9)在路径归一后**原文逐字节相同**;PASS/FAIL、命中的检查 ID 集合、
  errors/flags/info 计数、每条明细文本与关键数值(1.36 / 1.16 / 50.0% / 7.0pt / `#1E2761`)全部一致。
- **差异清单:无**。`run.log` 中唯一的多出行差异(33 行)完全由本次复核使用的 `--no-build --no-render`
  参数解释,且方向单一(仅仓库侧有 build/render 行,复跑侧无新增行)。
- 2/2 负控抽查与 `expected.json` 的 `must_include` 相符,并经**独立验算**(WCAG 重算 + 解压 pptx 实测)确认为真阳性。

**遗留不确定性(不影响上述判定)**:因按指定参数运行,未重跑 build/render,故 build 与 render 两个阶段的
字节级可复现性本次未获独立验证;若需覆盖该范围,应另跑一次不带 `--no-build --no-render` 的全量
`python tests/run_tests.py`(需 Node 全局 pptxgenjs/sharp 与 WPS/PowerPoint COM 渲染器)。

---

### 附:复核产物(均在副本同级的 agentD 目录,未落入仓库)
| 文件 | 内容 |
|---|---|
| `compare.py` / `crossread.txt` | 18 组报告解析后 JSON 逐字段对读 |
| `rawcheck2.py` / `rawcheck2.txt` | 修正后原文逐字节一致性 + 仓库 SHA-256 快照 |
| `spotcheck.py` / `spotcheck.txt` | 2 个负控的独立验算(WCAG 重算、pptx 解压复检) |
| `rawcheck.py` / `rawcheck.txt` | 首版原文比对(含一处我自己的归一化 bug,已被 `rawcheck2.py` 修正取代) |
