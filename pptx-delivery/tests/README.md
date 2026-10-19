# pptx-delivery 测试与负控(交付验收)

一个可一键复跑的夹具套件:7 组蓄意缺陷 deck(负控)+ 干净基线 + 1 组真实中文 deck(端到端)。
用于验证 `scripts/qa_check.py` 的检出能力,并给交付验收提供可复现的基线。

## 一键复跑

```powershell
pip install -r requirements.txt           # 首次:Python 依赖(以下命令均在仓库根目录运行)
npm install -g pptxgenjs sharp            # 首次:Node 依赖
$env:NODE_PATH = (npm root -g)            # Windows 需要(全局包解析)

python tests/run_tests.py                 # 全部(负控 + 端到端)
python tests/run_tests.py --which controls  # 只跑负控
python tests/run_tests.py --no-build --no-render  # 只复用已有产物重测
```

另有检测逻辑自测(无需渲染器):`python tests/c5_selftest.py`(叠层背景:有衬底不误报 / 无衬底照报)、`python tests/c7_selftest.py`(人造跨缘 PDF,验证 C7 能红)。

前提:渲染器(WPS / PowerPoint COM,经 `scripts/render_slides.ps1`)、poppler(`pdftotext` 在 PATH)。

## 负控套件(全部必须被抓)

| deck | 蓄意缺陷 | 必须命中的检查 |
|---|---|---|
| `c1_placeholder` | 占位符残留(`XXXX` / `Click to edit` / `单击此处`) | C2 |
| `c2_lowcontrast` | 低对比度文字(1.36:1 / 1.16:1) | C5 |
| `c3_overflow` | 文本溢出到画布外,尾行被导出裁掉 | C8(渲染保真) |
| `c4_stretched` | 图片拉伸(形变 50%) | C6 |
| `c5_tinyfont` | 字号 7pt(低于 10pt 下限) | C3 |
| `c6_flatslide` | 整页图片、零文本(不可编辑交付) | C9 |
| `c7_badcolor` | 非法 hex 颜色(`#` 前缀注入) | C4 |

## 干净基线(误报闸门)

`clean.pptx` 必须 0 error / 0 flag——任何 flag 都算误报,会拉挂套件。

## 端到端

`make_e2e_deck.js` 生成真实中文 deck(主题:AI 生成 PPTX 的交付验收,7 页),
走完「生成 → 自动检查 → 渲染 → 目检 → 修正 → 复验」,记录在 `evidence/`。

## 产物

- `out/`(gitignored):deck 文件、渲染图、JSON 报告
- `evidence/`(提交):`run.log` 全量记录 + 各 deck 报告副本

## 添加新负控

1. 在 `make_controls.js` 里加一个 `buildXX()`,复刻一个新的蓄意缺陷;
2. 在 `expected.json` 的 `decks` 里登记 `must_include`(必须命中的检查 ID);
3. 重跑 `python tests/run_tests.py --which controls`。
