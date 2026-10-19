# agentE — pptx-delivery「编辑路径」冷启动测试报告

日期:2026-10-19 · 受访者:agentE(仅凭任务书 + `C:\Users\TL\skills-repo\pptx-delivery\` 技能目录作业)
状态:**DONE**(4 处修改完成;`qa_check.py --strict` 0 error / 0 flag;经历真实 fix→verify 一轮)

简称(下文通用):

- `SKILL_DIR` = `C:\Users\TL\skills-repo\pptx-delivery`(全程只读,未修改任何文件)
- `BASE` = `C:\Users\TL\AppData\Local\Temp\commandcode\C--Users-TL-skills-repo-essentials\23d8f706-fe95-40d3-bb8a-f8c8cfc83279\scratchpad\verify\agentE`

---

## 1. 输入与产物

| 项 | 路径 | 说明 |
|---|---|---|
| 客户初稿(只读源) | `SKILL_DIR\tests\out\e2e_deck.pptx` | MD5 `AA252784BB7D78952D95E6B6B358F2D3` |
| 初稿副本(工作用) | `BASE\client-draft.pptx` | 与源 MD5 一致(复制校验通过),未再改动 |
| **改后交付件** | `BASE\client-final.pptx` | MD5 `7D364DB18E438B4D609B8155A9544E6B` |
| 渲染图 | `BASE\render\slide-01..07.png` + `BASE\render\client-final.pdf` | WPS COM,1920×1080 |
| QA JSON | `BASE\render\qa.json` | qa_check --strict 报告 |
| 对比图(改前/改后上下拼) | `BASE\compare\cmp-01|02|05|07.png` | 目检用 |
| 编辑工作区 | `BASE\unpacked\` | unpack→edit→clean→pack 的中间物 |
| 留痕脚本 | `BASE\inspect_runs.py`(读码位)、`BASE\check_edits.py`(断言改动)、`BASE\compare_slides.py`(像素差+拼图) | 均为只读/取证用 |

## 2. 四处修改(件内精确前后对比)

改动经 `unpack → edit_file(Edit 工具,非 sed/脚本)→ clean → pack` 完成,均为 run 内文本替换,**未新增/删除任何形状、未改字号/颜色/位置**。

| # | 页 | 位置 | 原文 | 改后 |
|---|---|---|---|---|
| 1 | 1 | 主标题 run | `AI 生成 PPTX 的交付验收` | `我的季度汇报` |
| 1 | 1 | 副标题 run | `把「看起来差不多」变成「逐项查过」—— 一份陌生团队也能直接照用的清单` | `一次实测走完生成 → 检查 → 交付的完整链路` |
| 2 | 2 | 第 2 列说明 | `可自动检查的断言,由本 skill 的脚本执行` | `可自动检查的断言,全部由 qa_check.py 一条命令执行` |
| 3 | 5 | 表格「正文字号」行·阈值 | `≥ 10pt` | `≥ 12pt`(阈值收紧一档) |
| 3 | 5 | 表格「正文字号」行·来源(说明文字同步) | `本项目规范` | `本项目规范(收紧)` |
| 4 | 7 | 第一条要点 | `生成后先跑 qa_check.py,再进入视觉检查` | `改动完成后必须重新跑一遍检查` |

标点/空格保真:依靠 `inspect_runs.py` 的**码位导出**确认初稿通篇使用 ASCII 标点(`U+002C` 逗号、ASCII 括号、符号两侧单空格 `U+0020`),新文本沿用同款(新副标题箭头为 `U+2192` 两侧 `U+0020`);改后 `check_edits.py` 复验码位 → `ALL_OK`。

### 改动 3 的选择理由(判断留痕)

- 表格 6 行阈值中,`≥4.5:1`/`≥3:1`/`≤2%` 的数值在第 4 页(C5/C6 说明)被引用,改它们会造成跨页不一致,而任务书要求"其余内容保持原样"(不能同步去改第 4 页);`正文字号 ≥10pt` 是全稿唯一未被其他页引用的数值,收紧为 `≥12pt` 不会牵动任何其他页面。
- 该收紧与稿内既有口径自洽:第 6 页明示"阈值可按项目在上限内收紧",acceptance-checklist.md 也说明字号下限是"默认,--min-font-pt 可调"。
- "说明文字同步"落在该行的「来源」单元:`本项目规范` → `本项目规范(收紧)`,风格与既有来源格式(如 `实测容差(qa_check)`)一致。

## 3. 执行流水(命令原样 + 结果)

> 全部命令以绝对路径执行;未修改 `SKILL_DIR` 任何文件;未把 shell cwd 切到 scratchpad;未派子代理。
> 备注:本机 PowerShell 输出偶带 CLIXML 进度噪声,已用 `2>$null` 压掉,不影响结果。

1. **复制初稿**:
   `New-Item -ItemType Directory -Force -Path "$BASE" | Out-Null; Copy-Item "SKILL_DIR\tests\out\e2e_deck.pptx" "$BASE\client-draft.pptx"` → 成功;MD5 与源一致。
2. **内容勘察**:`python -m markitdown "$BASE\client-draft.pptx"` → 7 页文本全部取得(封面 / 三列统计 / 四步流程 / C1–C9 / 阈值表 / 图表页 / 结尾页)。
3. **解包**:`python "SKILL_DIR\scripts\office\unpack.py" "$BASE\client-draft.pptx" "$BASE\unpacked"` → `Unpacked … (44 XML files)`。
4. **L0 基线验证**:`python "SKILL_DIR\scripts\office\validate.py" "$BASE\client-draft.pptx"` → **FAILED**(`notesMasterIdLst` 次序,即 pptxgenjs 已知问题;exit=1)。记录为待修复项(见 §4)。
5. **码位勘察**:`python "$BASE\inspect_runs.py"` → 确认 ① 逗号为 ASCII`,`;② 括号为 ASCII `()`;③ 空格为 `U+0020`;④ 标题/副标题字面量精确。
6. **编辑(Edit 工具 ×6)**:`edit_file` 依次替换 slide1(标题、副标题)、slide2(列说明)、slide5(阈值、来源)、slide7(要点),均 1 replacement 成功。
7. **改后断言**:`python "$BASE\check_edits.py"` → 12 项 PRESENT/ABSENT 全 True,新文本码位正确,`ALL_OK`。
8. **清理**:`python "SKILL_DIR\scripts\clean.py" "$BASE\unpacked"` → `No unreferenced files found`(无结构改动,符合预期)。
9. **打包**:`python "SKILL_DIR\scripts\office\pack.py" "$BASE\unpacked" "$BASE\client-final.pptx" --original "$BASE\client-draft.pptx"` → `All validations PASSED!` + `Successfully packed`。
10. **归一化(L0 修复)**:`python "SKILL_DIR\scripts\office\validate.py" "$BASE\client-final.pptx"` → FAILED(次序问题继承自初稿);
    `python "SKILL_DIR\scripts\normalize_pptx_order.py" inplace "$BASE\client-final.pptx"` → `moved notesMasterIdLst before sldIdLst`;
    复跑 validate → **`All validations PASSED!`**(exit=0)。← **fix→verify 第 1 轮**
11. **渲染**:`& "SKILL_DIR\scripts\render_slides.ps1" -Pptx "$BASE\client-final.pptx" -OutDir "$BASE\render" -Pdf` → 7 PNG + `client-final.pdf`,exit=0。
12. **内容 QA**:`python -m markitdown "$BASE\client-final.pptx"` → 4 处修改全部在;追加占位扫描 `… | Select-String 'xxxx|lorem|ipsum|click to edit|单击此处|待填|请输入|TBD'` → `no placeholder hits`。
13. **自动断言(带 PDF 复跑)**:`python "SKILL_DIR\scripts\qa_check.py" "$BASE\client-final.pptx" --pdf "$BASE\render\client-final.pdf" --strict --json "$BASE\render\qa.json"` → **errors=0, flags=0, info=10, exit=0**(明细见 §4)。
14. **视觉 QA(逐页自查 + 拼图)**:`python "$BASE\compare_slides.py"` → 像素差:slide 3/4/6 = `None`(与初稿渲染逐像素一致,未被触碰);slide 1/2/5/7 的差异 bbox 均严格落在改动区域。人工逐张查看 7 页新渲染 + 4 张改前/改后对比拼图。
15. **哈希留痕**:`Get-FileHash … -Algorithm MD5`(见 §1)。

## 4. QA 结果汇总

| 层 | 手段 | 结果 |
|---|---|---|
| L0 包结构 | `validate.py`(OOXML XSD) | 修复前 FAILED → `normalize_pptx_order.py` → 复跑 PASSED ✅ |
| L1 自动断言 | `qa_check.py --strict --pdf` | **0 error / 0 flag**(C1 结构 7 页/1 图;C2 无占位;C3 字号低于下限=0;C4 hex 合规;C5 对比度 80 处全过、0 待目检;C6 图片比例合规;C7 无越界词框;C8 PDF 文本层无丢字;C9 无整页图;I1 字体仅 Microsoft YaHei×80) |
| L2 渲染目检 | 7 页 PNG 逐页 + 4 张对照拼图 + 像素差 | 无重叠/裁切/错位;改动以外区域零像素差异;观察项见下 |
| 内容 QA | markitdown + 占位 grep | 4 处修改精确落地,无占位残留 |

**fix→verify 说明**:本轮唯一发现的真实缺陷是 L0 的 `notesMasterIdLst` 次序(初稿继承的 pptxgenjs 已知破坏项,由 validate.py 抓到),已对交付件执行 `normalize` 修复并复跑验证通过;随后渲染与 qa_check 均针对**修复后**的交付件执行。视觉首轮未发现需修复项(改动为保守内文替换,渲染像素差证明除目标区域外零扰动),已将观察项记录如下:

- slide-02 第 2 列说明自然折行为两行(`…一条` / `命令执行`),与第 1 列既有两行折行风格一致(中文任意折行,非孤字、未溢出)——判定无需修。
- slide-06 图片的替代文本仍是 pptxgenjs 写入的本地路径(`C:\Users\TL\skills-repo\...\chart-bars.png`)——**初稿原有**,不属本次 4 处修改范围,未动;如需交付优化可在后续任务处理(属 L3 元数据项)。
- 交付件元数据/讲者备注等继承初稿,未修改(超范围)。

## 5. 为确定下一步翻过的文档(按阅读顺序)

1. `SKILL_DIR\SKILL.md` — 总入口;确定:编辑工作流(指 editing.md)、QA 必跑命令、render 脚本用法、`normalize_pptx_order.py` 属"pptxgenjs 产出先归一化"步骤。
2. `SKILL_DIR\editing.md` — 编辑流程与规则;确定:unpack→改内容→clean→pack 的顺序、"Edit 工具而非 sed/脚本"、智能引号/实体注意项。
3. `SKILL_DIR\acceptance-checklist.md` — 验收阈值与流程;确定:§0 快速通道三段(归一化→渲染→`qa_check --strict`)、C1–C9 阈值、§5 已知盲区(含 pptxgenjs 次序破坏项)。
4. `SKILL_DIR\lessons.md` — 操作经验;确定:脚本从何处运行、QA 工具链的 Windows 兜底、依赖勿重装。
5. `SKILL_DIR\tests\README.md` — 确证 `e2e_deck.pptx` 由 `make_e2e_deck.js`(pptxgenjs)生成 → 归一化步骤适用;了解负控/基线语义。
6. `SKILL_DIR\scripts\normalize_pptx_order.py`、`render_slides.ps1`、`office\unpack.py`、`office\pack.py` 源码 — 确定 CLI 形态与行为(退出码、输出命名、验证时机)。
7. `SKILL_DIR\tests\out\render\e2e_deck\slide-01..07.png` — 改前渲染基准(对比与像素差)。

## 6. 摩擦清单(逐条:文档出处 + 当时的疑问)

1. **初稿本身就有 L0 校验错误,技能未直说"输入有缺陷时交付件要不要修"** — 出处:acceptance-checklist.md §0/§5 与 SKILL.md QA 节均只对"pptxgenjs 产出"讲归一化;疑问:改动路径的产物 file 继承该缺陷,`validate.py` FAILED 时,交付前是否必须 normalize?(我的判断:是——脚本 docstring 明示"交付前建议",且不改动内容语义。若判断错,影响为零,因为只动了 presentation.xml 元素次序。)
2. **editing.md 的文本编辑规则没有覆盖 CJK 标点保真** — 出处:editing.md「Smart Quotes」只讲英文智能引号/实体;疑问:全角/半角逗号、括号、粗空格在初稿里到底是哪种码位?Edit 工具显示层无法可靠区分,而换错会破坏"风格保持一致"。对策:`inspect_runs.py` 导出码位再编辑(建议技能补一节"CJK 标点核验").
3. **任务要求"说明文字同步"与"其余内容保持原样"存在张力** — 出处:任务书第 3 条;疑问:若改第 4 页引用过的数值(4.5:1/2%),同步文字需牵连第 4 页,与"保持原样"冲突;最终选唯一无跨页引用的行(正文字号),把同步落在同行「来源」单元。判断依据已写进 §2。
4. **SKILL.md 要求视觉 QA 用子代理,而任务书明令禁止** — 出处:SKILL.md「Visual QA — USE SUBAGENTS」;任务书降级协议。对策:采用技能给出的降级路线「拼图 + 逐页自查」,并用像素差补充"未触碰页零扰动"证据。
5. **slide-06 图片 alt 文本是本地绝对路径(初稿遗留)** — 出处:markitdown 输出;qa_check 不检查 alt/元数据,属 acceptance-checklist §4「本地链接」L3 人工项;疑问:是否顺手清理?(判定:超本次 4 处修改范围,保留原样并记录,避免擅自扩大改动面。)
6. **环境噪声** — PowerShell 工具每次输出夹带 CLIXML 进度记录;对策:`2>$null` 抑制 + 忽略。不影响任务(非技能文档问题,备注以免误读日志)。
7. **无被拒命令、无降级执行** — 白名单约束(不可 cwd 到 scratchpad、skills-repo 只读)下,全部命令均以绝对路径正常执行,无需替代方案。

## 7. 结论

- 4 处内容修改全部按任务书字面完成,格式/样式与初稿一致(除 slide-02 说明文字正常折行为两行外,无版式变化)。
- QA 全链路通过:validate(PASSED)→ render(7 页)→ qa_check --strict 带 PDF(0 error/0 flag)→ 逐页目检 + 像素差对照(无新问题)。
- 交付件:`BASE\client-final.pptx`;配套渲染 `BASE\render\*`、对照图 `BASE\compare\*`、QA 报告 `BASE\render\qa.json`。
