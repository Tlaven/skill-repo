# PPTX 交付验收清单(面向 AI 生成 / 人机协作产出)

> **适用**:一份 .pptx 交出去之前(发同事 / 上会 / 投标 / 入仓)的最后质量关卡。
> **立场**:能机器判的绝不靠眼睛;眼睛只处理机器判不了的。先自动、再目检、后签字。
> **每条检查带来源标签**:`【引用:URL】` / `【实测:位置】` / `【假设待测】`。
> 配套:`scripts/qa_check.py`(执行器)+ `tests/`(负控套件)。

## 0. 六十秒快速通道

```bash
# 0) pptxgenjs 产出的文件先归一化(生成器已知问题,见 §5;其他工具产出可跳过):
python scripts/normalize_pptx_order.py inplace deck.pptx

# 1) 渲染(WPS/PowerPoint COM,或 LibreOffice 二选一):
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/render_slides.ps1 -Pptx deck.pptx -OutDir render/ -Pdf
python scripts/office/soffice.py --headless --convert-to pdf --outdir render deck.pptx

# 2) 断言(C1–C9;--strict = 有任何 error/flag 即非零退出,可挂 CI):
python scripts/qa_check.py deck.pptx --pdf render/deck.pdf --strict --json render/qa.json
```

无自动结论的部分(重叠 / 间距 / 换行 / 观感)走 §3 目检。

## 1. 分层结论

| 层 | 手段 | 覆盖 |
|---|---|---|
| L0 文件有效性 | `python scripts/office/validate.py deck.pptx`(pptxgenjs 产出先归一化,见 §0) | OOXML schema / 包结构 |
| L1 自动断言 C1–C9 | `qa_check.py` | 结构 / 占位 / 字号 / 颜色 / 对比度 / 形变 / 越界 / 渲染保真 / 可编辑 |
| L2 渲染目检 | 转图逐页看(自检 + 他人或子代理) | 重叠 / 间距 / 换行 / 观感 |
| L3 人工签字 | 人 | 编辑性抽查 / 元数据 / 内容本身 |

## 2. L1 阈值表(全部可执行)

| 检查 | 阈值 | 来源 |
|---|---|---|
| C1 结构 | 页数 / 媒体 / 图片清点;`--expect-slides` 可断言页数 | 工具默认 |
| C2 占位残留 | 命中模式表(lorem / xxxx / click to edit / 单击此处 / 待填 / 请输入 / TBD…) | 【实测:tests/expected.json c1/clean】 |
| C3 字号下限 | ≥ 10pt(默认,`--min-font-pt` 可调) | 本项目规范(定值);微软演示建议 18pt+【引用】 |
| C4 颜色卫生 | srgbClr 必须 6 位 hex、无 `#`;无负向 shadow dist | pptxgenjs 破坏项【实测:c4 同族】 |
| C5 对比度 | 普通 ≥ 4.5:1;大文本(≥18pt 或 ≥14pt 粗)≥ 3:1;**不四舍五入** | 【引用:https://www.w3.org/TR/WCAG21/#contrast-minimum】 |
| C6 图片形变 | 显示比例 vs 原始像素比例,偏差 ≤ 2% | 【实测:clean 0.0% vs c4 50%】 |
| C7 页面越界 | 渲染 PDF 中不得有词框越过页面边界 | 【实测:tests/ (C7 检查器)】 |
| C8 渲染保真 | 每个段落必须完整出现在渲染 PDF 文本层 | 【实测:c3 尾行被裁 → 命中】 |
| C9 可编辑性 | 不得"整页图片 + 零文本"(覆盖率阈值 80%,可调) | 【实测:c6 命中】;外部实践【引用:PPTLint / Marp】 |

## 3. L2 目检清单(机器判不了的部分)

- [ ] **重叠与遮挡**:文字压形状 / 压图片,或元素彼此叠放
- [ ] **换行与截断**:标题变两行引发的下方元素错位;行尾单字(孤字)
- [ ] **间距**:同类元素间距一致(0.3–0.5in);页面边距 ≥ 0.5in
- [ ] **对齐**:多列 / 卡片 / 网格的基准线一致
- [ ] **对比**:渐变或图片背景上的文字(工具测不了)
- [ ] **图片观感**:裁切构图、是否被压扁、与文字的区域平衡
- [ ] **中文观感**:标点统一、字重自然(无伪粗)、行距均匀见 [typography.md](typography.md)
- [ ] **内容层**:页序、页数、术语一致

修复后**重跑受影响页的渲染**再确认(一轮 fix→verify 是下限)。

## 4. L3 人工签字项

- [ ] **可编辑性抽查**:随机抽 2 页,现场改一个字 / 挪一个元素,确认不是"图片化的假 PPTX"
- [ ] **元数据与隐藏内容**:讲者备注、批注、作者信息、隐藏页、本地链接(PPTLint 等可作扩展)
- [ ] **字体替换风险**:交付环境没有的字体 → 换行挪位;混合环境改用开源字体或嵌入子集
- [ ] **口径确认**:本清单管"交付质量",不管"内容对不对"——内容由你签字

## 5. 已知盲区(诚实声明)

- **生成器已知问题**:pptxgenjs 4.0.1 把 `<p:notesMasterIdLst>` 写在 `<p:sldIdLst>` 之后,严格 schema 校验(validate.py)报次序错误——PowerPoint/WPS 仍能打开,但交付前建议跑 `normalize_pptx_order.py` 修复。【实测:tests/evidence/normalize_check.log(raw FAILED → normalized PASSED)】
- 对比度:渐变 / 图片背景、主题色继承、透明叠加 —— 仅目检;表格主题条纹填充不可解析。
- CJK 的"等价大字号"WCAG 未给数值;本工具按 18pt/14pt 罗马值执行,对中文属**偏宽**(可能少判,不会多判)。
- 行距 / 字距美观、孤字控制:无自动判据。
- 音视频、动画、图表内部:不在本清单。

## 6. 负控与回归

6 组负控 + 干净基线(误报闸门),一键复跑见 [tests/README.md](tests/README.md):

```powershell
python tests/run_tests.py --which controls
```

## 7. 外部参考(可选扩展)

- [PPTLint](https://github.com/kdnsna/pptlint)(MIT):交付前预检 —— 字体替换 / 重叠 / 整页图 / 元数据泄漏
- [pptx-lint](https://github.com/leppardwang/pptx-lint)(MIT):几何与字号硬阈值(如 < 8pt)
- [OOXML-Validator](https://github.com/mikeebowen/OOXML-Validator)(MIT):schema 级校验
- [PowerPoint 无障碍检查器规则](https://support.microsoft.com/en-us/accessibility/office-accessibility/rules-for-the-accessibility-checker):12 条规则(含官方盲区:透明文本框上的对比度检不出)
