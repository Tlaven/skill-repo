# 独立验收记录 — pptx-delivery @ 7062480

> **口径**：独立复跑 + 自造负控 + 声称回验。验收对象钉在提交 `7062480`（干净 worktree），不使用工作区的在途改动。
> **方法**：`notes/verification-essentials.md` 通例 1/2/3（先让它红一次 / 三态 / 只认确定性证据）+ 测试器红测。
> **环境**：Windows + WPS/PowerPoint COM（`scripts/render_slides.ps1`），Python 3.12.4，Node 22.23.2（全局 pptxgenjs/sharp），poppler 24.08（`pdftotext`）。

## 结论

**有条件通过**：既有 9 项夹具全部 PASS；独立负控发现 1 个阻断级假阴性（C5 背景解析），**已在后续提交修复，但缺回归夹具**。补 `c8_bgshape` 后可复验。

## 1. 全量复跑（7062480）

命令：`python tests/run_tests.py`（工作目录 = `pptx-delivery/`）→ **exit 0，9/9 PASS**。

| deck | 命中 | flags/errors |
|---|---|---|
| clean | none | 0 / 0 |
| c1_placeholder | C2（XXXX / Click to edit / 单击此处） | 3 / 0 |
| c2_lowcontrast | C5（1.36:1、1.16:1） | 2 / 0 |
| c3_overflow | C8（缺末 8 字「导出时就丢内容。」） | 1 / 0 |
| c4_stretched | C6（偏差 50.0%） | 1 / 0 |
| c5_tinyfont | C3（7.0pt < 10pt） | 1 / 0 |
| c6_flatslide | C9（整页图覆盖 100%，零文本） | 1 / 0 |
| c7_badcolor | C4（`#1E2761`，error）+ C5 | 2 / 1 |
| e2e_deck | 无 | 0 / 0 |

**声称回验**：C5 的 1.36 / 1.16、C6 的 50.0%、C9 的 100% 覆盖、clean 的 0/0、e2e 的 0/0——全部与文档一致。

## 2. 独立负控（套件未见过；python-pptx 直接生成，非 pptxgenjs）

- **slide 1**：`#808080` 文字叠 `#999999` 全幅矩形（理论对比度 **1.386:1**，28pt → 大文本阈值 3:1）。
  - **7062480：未命中 C5**（`checked=2, below-threshold=0`）——假阴性。
  - 根因：`check_contrast` 构建背景候选时 `if shp.has_text_frame ...: continue`。python-pptx / PowerPoint 的矩形默认带 text frame，被整体排除 → 背景回落到页面白底（3.95:1）→ 大文本阈值 3:1 放过。
  - **当前 HEAD（`f3e3e41`）：已改为只跳过表格形状**；同一 deck 命中 `ratio 1.39 … bg=#999999`。
- **slide 2**：图片纵向拉伸 100%（显示 1:1 vs 原生 2:1，偏差 50%）。
  - **C6 命中**（`deviation 50.0% > 2.0%`）——跨生成器路径有效。

## 3. 判据证伪与测试器红测

- **C3 阈值响应**：c5 deck 以 `--min-font-pt 5` 复跑 → `below-min=0`（不命中）；默认 10 → 命中 7pt。判据不是恒红。
- **测试器红测**：篡改 `tests/expected.json`（给 c1 追加 `C9-editable`）→ c1 **FAIL**，套件 **exit 1**；恢复后 `git diff` 为空。套件不是恒绿。

## 4. 非阻断观察

- c7 的 C5 顺带命中「白字白底 1.00:1」与「`#CADCFC` on white 1.39:1」：c7 由 clean 注入非法色生成，若非法色位于背景，渲染后确实可能浅底浅字；暂判合理，未深挖。
- C7 仍无触发夹具（与验收清单 §5 的声明一致）。
- C3 不查继承字号（与 §5 的声明一致）。

## 5. 建议

1. 把 slide 1 场景固化为 `c8_bgshape`（`must_include: ["C5-contrast"]`），给当前修复补上回归保护；
2. 同步 `make_controls.js` + `tests/README.md` 的负控表；
3. 可选：C5 背景解析明确优先级——文本形状自身填充 > 其下方最近的实色形状 > 页面底色（现逻辑已是此序，只需保持）。

## 6. 证据与复现

- 全量记录：worktree 内 `tests/evidence/run.log` 与 `tests/out/reports/*.json`（9 份）。
- 独立负控：本会话 scratchpad 的 `make_independent_control.py`；由它生成 `indep_control.pptx` → `render_slides.ps1` → `qa_check.py --pdf`。
- 复现步骤：
  ```powershell
  git worktree add --detach <tmp> 7062480
  cd <tmp>\pptx-delivery
  python tests/run_tests.py
  # 独立负控: 用 python-pptx 建 2 页(灰底灰字 / 纵向拉伸图), 渲染后跑 scripts/qa_check.py --pdf
  ```

## 补记：c8_bgshape 已固化（2026-10-19）

- 新增 `tests/make_bgshape.py`（python-pptx 构造：全幅 `#999999` 矩形自带 text frame + `#808080` 28pt 文字）。
- `run_tests.py` 构建链加入该脚本；`expected.json` 登记 `c8_bgshape`（`must_include: C5`，`max_flags: 1`）。
- `tests/README.md` / `acceptance-checklist.md` 的组数同步为 8 组。
- **双向验证**：
  - 当前 HEAD（含修复）→ C5 命中（`ratio 1.39, bg=#999999`），controls **9/9 PASS，exit 0**；
  - 7062480 版 `qa_check.py` → 同一 deck **0 flag**（复现原假阴性）。修复若退化，该夹具会立即变红。
