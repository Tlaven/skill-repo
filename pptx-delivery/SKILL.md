---
name: pptx-delivery
description: "Delivery-grade PPTX skill: create, edit, QA, and vet slide decks. Use when a .pptx file is involved as input, output, or reference. Trigger on \"deck,\" \"slides,\" \"presentation,\" \"PPT,\" \"幻灯片,\" \"演示文稿,\" \"答辩,\" or any .pptx filename. Do not use for converting non-PPTX file formats or for image-only processing."
license: Proprietary. LICENSE.txt has complete terms
---

# pptx-delivery — PPTX 生成、编辑与交付验收

## Quick Reference

| Task | Guide |
|------|-------|
| Read/analyze content | `python -m markitdown presentation.pptx` |
| Edit or create from template | Read [editing.md](editing.md) |
| Create from scratch | Read [pptxgenjs.md](pptxgenjs.md) |
| Operational lessons | Read [lessons.md](lessons.md) |
| **Automated QA (executable)** | `python scripts/qa_check.py output.pptx --pdf render/output.pdf --strict` |
| **Delivery acceptance checklist** | Read [acceptance-checklist.md](acceptance-checklist.md) |
| **CJK typography** | Read [typography.md](typography.md) |
| **Visual quality (judgment layer)** | Read [docs/scaffolds/visual-quality-essentials.md](docs/scaffolds/visual-quality-essentials.md) |
| **Layout patterns (richness)** | Read [docs/scaffolds/slide-patterns-essentials.md](docs/scaffolds/slide-patterns-essentials.md) |
| **Reference example** | Open [examples/acceptance-sample/](examples/acceptance-sample/)(deck + 渲染 + 证据 + 检查指引) |
| Render (COM / LibreOffice) | `scripts/render_slides.ps1 -Pptx deck.pptx -OutDir render/ -Pdf` |

> 检测逻辑自测(无需渲染器):`python tests/c5_selftest.py`(叠层背景:有衬底不误报 / 无衬底照报)、`python tests/c7_selftest.py`(人造跨缘 PDF,验证 C7 能红)。

---

## When to NOT Use

- **纯图片处理**（批量裁剪/调色/水印）→ 用 ImageMagick / sharp，不用这个 skill
- **纯格式转换**（如 PDF→PPTX，只求能打开、不做设计与内容加工）→ 转换本身交给专门工具；但转换产物若要交付，回到本 skill 跑验收（见 [acceptance-checklist.md](acceptance-checklist.md)）
- **文档排版**（纯文字排版需求）→ 用 Word / thesis-docx skill

---

## Reading Content

```bash
# Text extraction
python -m markitdown presentation.pptx

# Visual overview
python scripts/thumbnail.py presentation.pptx

# Raw XML
python scripts/office/unpack.py presentation.pptx unpacked/
```

---

## Editing Workflow

**Read [editing.md](editing.md) for full details.**

1. Analyze template with `thumbnail.py`
2. Unpack → manipulate slides → edit content → clean → pack

---

## Creating from Scratch

**Read [pptxgenjs.md](pptxgenjs.md) for full details.**

Use when no template or reference presentation is available.

---

## Design Ideas

**Don't create boring slides.** Plain bullets on a white background won't impress anyone. Consider ideas from this list for each slide.

### Before Starting

- **Pick a bold, content-informed color palette**: The palette should feel designed for THIS topic. If swapping your colors into a completely different presentation would still "work," you haven't made specific enough choices.
- **Dominance over equality**: One color should dominate (60-70% visual weight), with 1-2 supporting tones and one sharp accent. Never give all colors equal weight.
- **Dark/light contrast**: Dark backgrounds for title + conclusion slides, light for content ("sandwich" structure). Or commit to dark throughout for a premium feel.
- **Commit to a visual motif**: Pick ONE distinctive element and repeat it — rounded image frames, icons in colored circles, thick single-side borders. Carry it across every slide.

### Color Palettes

Choose colors that match your topic — don't default to generic blue. Use these palettes as inspiration:

| Theme | Primary | Secondary | Accent |
|-------|---------|-----------|--------|
| **Midnight Executive** | `1E2761` (navy) | `CADCFC` (ice blue) | `FFFFFF` (white) |
| **Forest & Moss** | `2C5F2D` (forest) | `97BC62` (moss) | `F5F5F5` (cream) |
| **Coral Energy** | `F96167` (coral) | `F9E795` (gold) | `2F3C7E` (navy) |
| **Warm Terracotta** | `B85042` (terracotta) | `E7E8D1` (sand) | `A7BEAE` (sage) |
| **Ocean Gradient** | `065A82` (deep blue) | `1C7293` (teal) | `21295C` (midnight) |
| **Charcoal Minimal** | `36454F` (charcoal) | `F2F2F2` (off-white) | `212121` (black) |
| **Teal Trust** | `028090` (teal) | `00A896` (seafoam) | `02C39A` (mint) |
| **Berry & Cream** | `6D2E46` (berry) | `A26769` (dusty rose) | `ECE2D0` (cream) |
| **Sage Calm** | `84B59F` (sage) | `69A297` (eucalyptus) | `50808E` (slate) |
| **Cherry Bold** | `990011` (cherry) | `FCF6F5` (off-white) | `2F3C7E` (navy) |

### For Each Slide

**Every slide needs a visual element** — image, chart, icon, or shape. Text-only slides are forgettable.

**Layout options:**
- Two-column (text left, illustration on right)
- Icon + text rows (icon in colored circle, bold header, description below)
- 2x2 or 2x3 grid (image on one side, grid of content blocks on other)
- Half-bleed image (full left or right side) with content overlay

**Data display:**
- Large stat callouts (big numbers 60-72pt with small labels below)
- Comparison columns (before/after, pros/cons, side-by-side options)
- Timeline or process flow (numbered steps, arrows)

**Visual polish:**
- Icons in small colored circles next to section headers
- Italic accent text for key stats or taglines

### Typography

**Choose an interesting font pairing** — don't default to Arial. Pick a header font with personality and pair it with a clean body font.

| Header Font | Body Font |
|-------------|-----------|
| Georgia | Calibri |
| Arial Black | Arial |
| Calibri | Calibri Light |
| Cambria | Calibri |
| Trebuchet MS | Calibri |
| Impact | Arial |
| Palatino | Garamond |
| Consolas | Calibri |

| Element | Size |
|---------|------|
| Slide title | 36-44pt bold |
| Section header | 20-24pt bold |
| Body text | 14-16pt |
| Captions | 10-12pt muted |

**中文（CJK）**：回到 [typography.md](typography.md)——字体跨平台可用性、字号下限、行距与混排规则（带来源）。

### Spacing

- 0.5" minimum margins
- 0.3-0.5" between content blocks
- Leave breathing room—don't fill every inch

### Avoid (Common Mistakes)

- **Don't repeat the same layout** — vary columns, cards, and callouts across slides
- **Don't center body text** — left-align paragraphs and lists; center only titles
- **Don't skimp on size contrast** — titles need 36pt+ to stand out from 14-16pt body
- **Don't default to blue** — pick colors that reflect the specific topic
- **Don't mix spacing randomly** — choose 0.3" or 0.5" gaps and use consistently
- **Don't style one slide and leave the rest plain** — commit fully or keep it simple throughout
- **Don't create text-only slides** — add images, icons, charts, or visual elements; avoid plain title + bullets
- **Don't forget text box padding** — when aligning lines or shapes with text edges, set `margin: 0` on the text box or offset the shape to account for padding
- **Don't use low-contrast elements** — icons AND text need strong contrast against the background; avoid light text on light backgrounds or dark text on dark backgrounds
- **NEVER use accent lines under titles** — these are a hallmark of AI-generated slides; use whitespace or background color instead

---

## QA (Required)

**Assume there are problems. Your job is to find them.**

Your first render is almost never correct. Approach QA as a bug hunt, not a confirmation step. If you found zero issues on first inspection, you weren't looking hard enough.

### Automated checks first (this port)

Run the executable assertions before eyes touch it:

```bash
# 0) pptxgenjs 产出先归一化(修 notesMasterIdLst 次序,见 normalize_pptx_order.py):
python scripts/normalize_pptx_order.py inplace output.pptx

# 1) render (Windows: WPS/PowerPoint COM; 或 LibreOffice):
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/render_slides.ps1 -Pptx output.pptx -OutDir render/ -Pdf
python scripts/office/soffice.py --headless --convert-to pdf --outdir render output.pptx

# 2) assertions C1-C9: structure / placeholders / font sizes / color hygiene /
#    contrast (WCAG) / image aspect / pdf bounds / render fidelity / editability
python scripts/qa_check.py output.pptx --pdf render/output.pdf --strict --json render/qa.json
```

All thresholds + the full acceptance workflow: [acceptance-checklist.md](acceptance-checklist.md). What the tools cannot judge (overlaps, spacing, wrapping) goes to the visual pass below.

### Content QA

```bash
python -m markitdown output.pptx
```

Check for missing content, typos, wrong order.

**When using templates, check for leftover placeholder text:**

```bash
python -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum|this.*(page|slide).*layout"
```

If grep returns results, fix them before declaring success.

### Visual QA

**⚠️ USE SUBAGENTS** — even for 2-3 slides. You've been staring at the code and will see what you expect, not what's there. Subagents have fresh eyes.

宿主不支持子代理时:退化为「拼图(contact sheet)+ 逐页自查」,并仍需完成至少一轮 fix→verify。

Convert slides to images (see [Converting to Images](#converting-to-images)), then use this prompt:

```
Visually inspect these slides. Assume there are issues — find them.

Look for:
- Overlapping elements (text through shapes, lines through words, stacked elements)
- Text overflow or cut off at edges/box boundaries
- Decorative lines positioned for single-line text but title wrapped to two lines
- Source citations or footers colliding with content above
- Elements too close (< 0.3" gaps) or cards/sections nearly touching
- Uneven gaps (large empty area in one place, cramped in another)
- Insufficient margin from slide edges (< 0.5")
- Columns or similar elements not aligned consistently
- Low-contrast text (e.g., light gray text on cream-colored background)
- Low-contrast icons (e.g., dark icons on dark backgrounds without a contrasting circle)
- Text boxes too narrow causing excessive wrapping
- Leftover placeholder content

For each slide, list issues or areas of concern, even if minor.

Read and analyze these images:
1. /path/to/slide-01.jpg (Expected: [brief description])
2. /path/to/slide-02.jpg (Expected: [brief description])

Report ALL issues found, including minor ones.
```

### Verification Loop

1. Generate slides → Convert to images → Inspect
2. **List issues found** (if none found, look again more critically)
3. Fix issues
4. **Re-verify affected slides** — one fix often creates another problem
5. Repeat until a full pass reveals no new issues

**Do not declare success until you've completed at least one fix-and-verify cycle.**

### Common Rationalizations for Skipping QA

| Excuse | Reality |
|--------|---------|
| "只改了一个字，不用重新验证" | 一个改动经常导致其他元素位移。重新验证受影响页面。 |
| "代码逻辑没问题，不需要看渲染" | 代码正确 ≠ 布局正确。文本框溢出、元素重叠只有渲染后能发现。 |
| "我已经手动检查过了" | 你在看代码，不是看渲染结果。你的眼睛会脑补正确布局。 |
| "等全部做完再统一 QA" | 问题越早发现越容易修。做完一页就先验证一页。 |
| "一轮检查就够了" | 第一轮渲染几乎永远有问题。至少一轮 fix→verify 循环。 |
| "没时间做视觉 QA" | 输出有 bug 的 PPTX 比花 2 分钟做 QA 更浪费时间。 |

---

## Converting to Images

Convert presentations to individual slide images for visual inspection:

```bash
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
```

This creates `slide-01.jpg`, `slide-02.jpg`, etc.

To re-render specific slides after fixes:

```bash
pdftoppm -jpeg -r 150 -f N -l N output.pdf slide-fixed
```

### Windows without LibreOffice

Windows 上无需 LibreOffice 也能完整跑 QA：用 `scripts/render_slides.ps1`（PowerPoint/WPS COM 导出 PNG+PDF；WPS 场景实测）渲染后交给 `scripts/qa_check.py`。两个渲染器都不可用时，qa_check.py 仍执行 XML 层检查（C1–C6、C9；C7/C8 需要渲染产物）——结构、占位、字号、对比度照样管住。

---

## Dependencies

```bash
# Python (use requirements.txt) - incl. python-pptx (qa_check.py), Pillow, defusedxml, markitdown
pip install -r requirements.txt

# Node (creating from scratch) - global; set NODE_PATH to `npm root -g` if resolution fails
npm install -g pptxgenjs sharp
# icon workflow only (optional) — pptxgenjs.md additionally needs: npm install -g react-icons react react-dom
```

| Tool | Purpose | Windows Install |
|------|---------|-----------------|
| WPS Office or MS PowerPoint | render to PNG/PDF via COM (`scripts/render_slides.ps1`) | any |
| LibreOffice | render to PDF (`scripts/office/soffice.py`) | [Download](https://www.libreoffice.org/download/) or `scoop install extras/libreoffice` |
| Poppler (`pdftoppm`/`pdftotext`) | PDF → images; C7/C8 text checks | `winget install poppler` or [download](https://github.com/oschwartz10612/poppler-windows/releases/) |

On Windows, `soffice.py` auto-detects common install paths (`Program Files\LibreOffice\...`, scoop's `apps\libreoffice\current\LibreOffice\program\`); override anytime with the `SOFFICE_PATH` env var.

## 验收（acceptance）

- **档位:** acceptance（交付级）
- **一键复跑:** `python tests/run_tests.py`（8 组负控 + 干净基线 + 端到端；证据落 `tests/evidence/`）
- **免渲染自测:** `python tests/c5_selftest.py`、`python tests/c7_selftest.py`（检查器自身的红/绿验证——先红一次原则）
- **交付清单:** [acceptance-checklist.md](acceptance-checklist.md)（分层检查 + 目检 + 签字项）
- **独立复核留档:** `docs/reviews/2026-10-19-cold-verification.md`（冷眼复核记录）
- **判据:** META=PASS、负控全中、干净基线 0 error / 0 flag；改动后必须同套件复跑（比较绑版本）。
- **注意:** 需先按 `requirements.txt` 与 Node 依赖装好环境；渲染器（WPS/PowerPoint COM 或 LibreOffice）仅影响 C7/C8，缺失时自动降级为 XML 层检查。

## Sources & License

- Base material: Anthropic's pptx skill (© 2025 Anthropic PBC; see LICENSE.txt — distribution restrictions apply, keep that file with any copy).
- Local additions of this port: `qa_check.py` / `render_slides.ps1` / `tests/` / `acceptance-checklist.md` / `typography.md` + Chinese-localized guidance; claims are tagged 【实测】/【引用】/【假设待测】 where they are made.
