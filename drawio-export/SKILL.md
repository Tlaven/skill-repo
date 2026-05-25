---
name: drawio-export
description: Use when creating diagrams (flowcharts, architecture, state machines) or mentioning draw.io. Triggers: user asks to draw/create a diagram, mentions draw.io, needs figures for a thesis. Works with thesis-docx skill.
---

# Draw.io 图表工具

## Overview

通过 JSON 描述生成 .drawio 图表文件，用本地 draw.io 桌面版导出为 SVG/PNG/PDF，可配合 thesis-docx 插入论文。核心流程：`check → create → export → insert`。

```bash
python drawio_helper.py <command> [options]
```

## 工作流（配合 thesis-docx）

```
1. check   → 检测环境（draw.io 是否可用）
2. create  → 生成 .drawio 文件
3. export  → 导出为 SVG/PNG
4. thesis-docx insert-image → 插入论文
```

## 命令

### check — 检测导出环境

```bash
python drawio_helper.py check
```

检测 draw.io 桌面版、Docker 可用性，返回环境状态。如果默认路径找不到，会建议用户安装或让 Agent 修正路径。

**对 Agent 的指引**：若 draw.io 不在默认路径，不要自行实现复杂 fallback。直接提示用户安装，或让用户告知实际路径，Agent 修改本 SKILL 中的 `DRAWIO_EXE` 配置做一次性适配。

返回 JSON，包含 `drawio_exe`、`graphviz_available`、`docker_available`、`can_export`、`suggestion` 等字段。

### create — 从 JSON 描述生成 .drawio

```bash
python drawio_helper.py create --spec '<JSON>' -o output.drawio
python drawio_helper.py create --spec-file diagram.json -o output.drawio
```

**提示**：默认字号 13pt。论文黑白风格可通过 `style` 覆盖，如 `"style": {"fillColor": "none", "strokeColor": "#000000", "fontColor": "#000000"}`。

### 自动布局

JSON 中不写 `x`/`y` 坐标时，create 调用 Graphviz `dot` 排版，避免节点重叠。

| 参数 | 作用 |
|------|------|
| `--max-width N` | 约束图宽不超过 N 英寸（默认 5.5） |
| `--rankdir DIR` | 布局方向：`TB`（竖排）、`LR`（横排）（默认 TB） |

```bash
python drawio_helper.py create --spec '<JSON>' -o diagram.drawio --max-width 5.5 --rankdir TB
python drawio_helper.py create --spec-file diagram.json -o diagram.drawio --rankdir LR
```

**依赖**：Graphviz（`dot` 命令），运行 `check` 可检测是否已安装。

**注意**：自动布局只对**所有节点都不含 `x`/`y`** 的页面生效。只要有一个节点有坐标，就按手动布局处理。

**格式校验**：create 会自动校验 JSON 规格，确保生成的 .drawio 文件能被 draw.io 正常打开。校验规则：

| 级别 | 检测项 | 处理方式 |
|------|--------|---------|
| error | 节点/边 id 重复 | 拒绝生成，返回详细错误列表 |
| error | 边 `from`/`to` 引用不存在的节点 | 同上 |
| error | `parent` 引用不存在的节点 | 同上 |
| warning | 未知的 shape 类型（含拼写建议） | 仍然生成，warnings 附在成功输出中 |
| warning | 未知的 edge 类型 | 同上 |
| warning | 宽/高为负数 | 同上 |
| warning | waypoints 格式错误 | 同上 |



### JSON 规范格式

```json
{
  "pages": [
    {
      "name": "页面名称",
      "nodes": [
        {"id": "n1", "label": "文字", "type": "rectangle", "x": 100, "y": 50, "w": 120, "h": 60},
        {"id": "n2", "label": "判断", "type": "diamond", "x": 100, "y": 200, "w": 140, "h": 80},
        {"id": "inner", "label": "子模块", "type": "rectangle", "parent": "n1", "x": 10, "y": 30, "w": 100, "h": 40}
      ],
      "edges": [
        {"from": "n1", "to": "n2", "type": "orthogonal"},
        {"from": "n2", "to": "n3", "label": "是", "exitX": 0.5, "exitY": 1, "entryX": 0.5, "entryY": 0}
      ]
    }
  ]
}
```

**节点字段：**

| 字段 | 说明 | 必填 |
|------|------|------|
| `id` | 节点标识，边通过此值引用 | 是 |
| `label` | 显示文字（支持中文） | 否 |
| `type` | 形状类型（见下表） | 否（默认 rectangle） |
| `x`, `y` | 左上角坐标（在容器内时为相对坐标） | 否（默认 0） |
| `w`, `h` | 宽度、高度 | 否（默认 120×60） |
| `parent` | 父容器节点 ID，用于嵌套进 container | 否（默认顶层） |
| `style` | 样式覆盖对象 `{"fillColor": "none"}` | 否 |

**边字段：**

| 字段 | 说明 | 必填 |
|------|------|------|
| `from` | 源节点 ID | 是 |
| `to` | 目标节点 ID | 是 |
| `label` | 边标签文字 | 否 |
| `type` | 边样式类型（见下表） | 否（默认 orthogonal） |
| `style` | 样式覆盖对象 | 否 |
| `waypoints` | 中间路径点 `[[x,y], ...]` | 否 |
| `exitX`, `exitY` | 源节点出口 (0=左/上, 0.5=中, 1=右/下) | 否 |
| `entryX`, `entryY` | 目标节点入口 | 否 |
| `exitDx`, `exitDy` | 出口像素偏移 | 否 |
| `entryDx`, `entryDy` | 入口像素偏移 | 否 |
| `labelX` | 标签沿边位置 (-1~1, 0=中点) | 否 |
| `labelY` | 标签垂直偏移 (px) | 否 |
| `labelPosition` | 标签水平位置 left/center/right | 否 |
| `verticalLabelPosition` | 标签垂直位置 top/middle/bottom | 否 |
| `labelBackgroundColor` | 标签背景色 (如 "#FFFFFF") | 否 |

### 支持的形状类型

| type | 形状 | 典型用途 |
|------|------|---------|
| `rectangle` | 矩形 | 处理步骤 |
| `rounded` | 圆角矩形 | 开始/结束 |
| `ellipse` | 椭圆 | 开始/结束 |
| `diamond` | 菱形 | 判断/条件 |
| `parallelogram` | 平行四边形 | 输入/输出 |
| `hexagon` | 六边形 | 准备/循环 |
| `cylinder` | 圆柱体 | 数据库 |
| `trapezoid` | 梯形 | 手动操作 |
| `cloud` | 云形 | 网络服务 |
| `container` | 容器（带标题栏，30px 头部） | 分组/模块 |
| `actor` | 角色 | 用例图 |
| `text` | 纯文字 | 标注 |
| `note` | 便签 | 备注/说明 |
| `process` | 进程 | 处理（双边框） |
| `double-arrow` | 双向箭头 | 双向关系 |
| `single-arrow` | 单向箭头 | 指向/流向 |

### 支持的边类型

| type | 样式 |
|------|------|
| `orthogonal` | 直角折线（默认） |
| `straight` | 直线 |
| `curved` | 弧线 |
| `dashed` | 虚线 |
| `no-arrow` | 无箭头 |
| `dot-arrow` | 空心箭头 |
| `open-arrow` | 开放箭头 |

### 连接点指南

`exitX/exitY` 和 `entryX/entryY` 控制边从节点的哪个位置出入，值为 0~1 的相对坐标。常用组合：上→下 `(0.5,1)→(0.5,0)`、左→右 `(1,0.5)→(0,0.5)`。只在回边、水平连接等自动路由出错时设置。

### export — 导出为图片

```bash
python drawio_helper.py export diagram.drawio -f svg -o output.svg
python drawio_helper.py export diagram.drawio -f png --scale 2 --transparent
python drawio_helper.py export diagram.drawio -f pdf --crop --border 10
```

| 参数 | 说明 |
|------|------|
| `-f` | 格式：svg, png, pdf, jpg, xml, html（默认 svg） |
| `-o` | 输出路径（不指定则用输入文件名改后缀） |
| `--scale` | 缩放倍数 |
| `--width` / `--height` | 限制尺寸（保持比例） |
| `--border` | 边距 |
| `--transparent` | 透明背景（PNG） |
| `--crop` | 裁剪到图表尺寸 |
| `--embed-svg-images` | 嵌入图片到 SVG |
| `--embed-svg-fonts` | 嵌入字体到 SVG（默认 true，设为 false 可大幅减小文件） |
| `--embed` | 嵌入 .drawio 副本到导出文件 |
| `--clean` | 去除 SVG 底部的 `<switch>` 兜底提示文字 |
| `--uncompressed` | 不压缩输出（SVG/XML） |
| `--page-index` | 导出指定页（1-based） |
| `--all-pages` | 导出所有页 |

**注意**：SVG 导出默认嵌入字体，`--embed-svg-fonts false` 可大幅减小文件。`--clean` 去除 `<switch>` 兜底提示，兼容不支持 `<foreignObject>` 的查看器。

### info — 查看文件信息

```bash
python drawio_helper.py info diagram.drawio
```

## 模板示例

```json
{"nodes": [
  {"id": "a", "label": "处理", "type": "rectangle", "x": 0, "y": 0},
  {"id": "b", "label": "判断", "type": "diamond",   "x": 0, "y": 100},
  {"id": "c", "label": "容器", "type": "container", "x": 300, "y": 0, "w": 200, "h": 150},
  {"id": "d", "label": "子节点", "parent": "c",     "x": 30, "y": 40}
], "edges": [
  {"from": "a", "to": "b", "label": "是"},
  {"from": "b", "to": "a", "label": "否", "exitX": 1, "exitY": 0.5}
]}
```

容器内子节点的 `x`/`y` 相对于容器内部（标题栏以下）。

## 与 thesis-docx 配合

```bash
python drawio_helper.py create ...
python drawio_helper.py export ... -o fig.svg
python thesis-docx/cli.py insert-image 论文.docx --image fig.svg
```

## 注意事项

- 导出依赖本地 draw.io 桌面版（默认 `C:\Program Files\draw.io\draw.io.exe`）
- 没有 draw.io 时运行 `check` 会提示下载，**不要自行实现复杂的 fallback 逻辑**
- 如果 draw.io 装在非默认路径，让用户告知实际路径，Agent 修改 `drawio_helper.py` 中的 `DRAWIO_EXE` 做一次性适配
- 首次导出可能较慢（draw.io 启动时间），后续会快一些
- 如果导出卡住，检查 draw.io 是否已在运行（关闭后重试）
- 回边（循环回路）通常需要手动设置 `exitX/exitY` 和 `entryX/entryY` 来控制走线方向
