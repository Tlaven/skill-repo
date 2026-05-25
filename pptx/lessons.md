---
name: pptx-lessons
description: Accumulated operational lessons for PPTX creation and editing with pptxgenjs.
type: reference
---

# PPT 生成操作经验

## 1. 图片宽高比是布局的锚点

### 1.1 先扫图后定布局，不可倒置

```javascript
// ❌ 错误：先定盒子尺寸，再用 contain 模式"期望"它自适应
slide.addImage({ path, x: 0, y: 0, w: 9, h: 2.5, sizing: { type: "contain", w: 9, h: 2.5 } });

// ✓ 正确：先用 sharp 读原图宽高，反推渲染尺寸，再定周围文字位置
const meta = await sharp(path).metadata(); // { width, height }
const ratio = meta.width / meta.height;
// 给定 maxW×maxH 盒子 → 计算等比例 (w, h) + 居中偏移 (cx, cy)
function fitInside(ow, oh, maxW, maxH) {
  const ratio = ow / oh;
  let w = maxW, h = maxW / ratio;
  if (h > maxH) { h = maxH; w = maxH * ratio; }
  return { w, h, cx: (maxW - w) / 2, cy: (maxH - h) / 2 };
}
```

### 1.2 不同比例的图需要不同的盒子

| 图片类型 | 典型比例 | 盒子策略 |
|---------|---------|---------|
| UI截图(宽屏) | 3.3–4.2:1 | 宽盒子(满宽)，上下留空 |
| 流程图/模块图 | 1:1 附近 | 方形盒子，左右或上下与文字并排 |
| 算法结构图 | 0.8–0.9:1 (略高) | 竖盒子，放在一侧，文字放另一侧 |
| 实物照片(竖) | 0.7:1 | 竖盒子，两列并排 |
| 折线图/雷达图 | 1.8–2:1 (宽) | 宽盒子(满宽)，最佳利用率 |

### 1.3 一页不能只有图

每页图片必须有配套文字，纯图页会让答辩显得空洞：
- 角色卡片（需求分析页）
- 特征说明块（技术页）
- 流程步骤描述（实现页）
- 功能亮点汇总条（界面展示页）
- 性能指标卡（测试页）

## 2. pptxgenjs 避坑

- `sizing: { type: "contain" }` **不可靠**，实测仍会拉伸。必须手动算 w/h
- 不要复用 option 对象，PptxGenJS 会原地修改（用工厂函数每次创建新对象）
- `lineSpacingMultiple` **不是有效属性**，用 `lineSpacing`（单位 pt）
- 不要在 hex 颜色前加 `#`（如 `"#FF0000"`），会导致文件损坏。用 `"FF0000"`
- 全局安装的 npm 包需要 `$env:NODE_PATH = "$(npm root -g)"` 才能被找到
- 中文字体用 `"Microsoft YaHei"` 在 Windows 上兼容性最好

## 3. 先行规划，再动手做

答辩PPT页数多(15-20页)，必须出详细规划让用户确认后再写代码：

- 先出逐页规划（每页标题、布局、内容要点、用哪张图）
- 用户确认后再生成，避免大方向错了白做工
- 用户说"任务比较长"是信号——意味着需要更谨慎、分步确认

### 3.1 一页内容改大了一个元素，整页布局都得重排

不要在已有布局里"只换个图片尺寸"——图片变了，周围的文字位置、留白、对齐全部要跟着调。正确做法是一次性把整页重新设计。

## 4. 答辩PPT不需要论文编号

答辩场景中图片不用标"图X-X"，直接写描述性文字即可（如"系统登录界面"而不是"图5-8 系统登录界面"）。论文式引用编号在PPT里显得冗余。

## 5. QA不可跳过

### 5.1 视觉QA工具链（Windows 适配）

- LibreOffice 转 PDF → pdftoppm 转图片做视觉检查是最可靠的方案
- `soffice.py` 已适配 Windows：自动检测 LibreOffice 安装路径（`Program Files\LibreOffice\program\soffice.exe`），跳过 LD_PRELOAD shim
- 兜底方案：解压 PPTX，统计 slides/ + media/ 文件数，提取文本检查占位符（见 SKILL.md [Windows Fallback]）

### 5.2 文本校验用解压XML

```powershell
# 统计幻灯片数量 + 媒体文件数
Add-Type -A 'System.IO.Compression.FileSystem'
$z = [System.IO.Compression.ZipFile]::OpenRead("out.pptx")
$entries = $z.Entries
$slides = ($entries | Where-Object { $_.FullName -match '^ppt/slides/slide\d+\.xml$' }).Count
$imgs = ($entries | Where-Object { $_.FullName -match '^ppt/media/' }).Count
$z.Dispose()
Write-Host "Slides: $slides, Media: $imgs"
```

## 6. 运行脚本注意路径

运行 `scripts/` 下的 Python 脚本时，在 `scripts/` 目录下执行（不要进到 `office/` 子目录）：

```powershell
cd scripts
python thumbnail.py input.pptx
python office/unpack.py input.pptx unpacked/
```

现在 `thumbnail.py` 已不依赖相对路径导入，从任意目录都能运行。

---

## 7. 经验要写对地方

写操作经验前先确认：这个经验归属于哪个skill？不要写错地方。例如PPT生成经验属于 pptx skill，不是 thesis-docx skill。

## 8. 从用户纠正中提炼通用原则

用户的每次具体纠正常常藏着通用规则：

| 用户原话 | 提炼出的原则 |
|---------|-------------|
| "图片不能过度横向拉伸或压缩" | 手动算宽高比，不用 contain |
| "当页的布局就出问题了" | 改图片大小=改整页布局 |
| "一页ppt不能只有图片" | 每页都要有配套文字 |
| "ppt中不需要出现图X.X编号" | 答辩PPT不做论文式引用 |

## 9. 推荐工作流

```
1. 装依赖: pip install -r requirements.txt
2. 选配色（与主题匹配，不默认蓝色）
3. 出逐页详细规划 → 用户确认
4. sharp 扫所有图片原始尺寸 → 记录宽高比
5. 按比例设计每页布局（图多大 → 文字放哪）
6. 写 JS 脚本一次性生成
7. QA：解压 PPTX 统计 slide 数 + media 数，markitdown 检查文本
8. 如果经验跨多个skill，确认归属再写入
```
