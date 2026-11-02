# M6 工具

> 本模块管：原则、工具矩阵、逐个工具、证据状态、用法、接线、改动纪律。
> 读的时机：接线 / 跑检查 / 改脚本。
> 文档内容规则在 M2 / M3；验收语义在 M4；复核判定在 M5。

## 一、原则

1. **只给高精度、低噪音的规则配脚本**；语义一致性、可读性判断交给 `verification.md` / teach-back。
2. **三层执行面**：`[脚本可查]` / `[需独立复核]` / `[只能靠自觉]`。工具只承担第一层。
3. **核心脚本是基座**，扩展不替换；可选脚本不默认接入；已决移除的不再接。
4. **警告类脚本不要接成硬门禁**；结构性检查（`check-doc-refs`）可以在结果稳定后加 `--strict`；启发式警告（`check-consistency`）不进硬门禁。
5. **机器只认写法，语义归复核。**「检查器过了」≠「文档对了」。
6. **扫描面按工具不同**：Python 工具默认只扫 `.live` 白名单 + L1；`check-doc-refs` 按目录排除；`run-n2-acceptance` 的 L2 来自 `l2-docs.txt`。
7. **`--strict` 不是统一含义**：有的「有发现就退 1」，有的「只对特定发现退 1」，有的「`--run` 失败才退 1」。用前看各自说明。
8. **平台双份**：`.sh` 与 `.ps1` 必须同输入同输出；改一边要两边都测。

> **术语：** 基线 = 文档基线（`last verified` SHA）/ 校准基线（见 `calibration-guide.md`）/ 分档基线；快照 = 现状快照；冻结 = 冻结计数 / 冻结期望。裸用这几个词时按本行限定。

## 二、工具集

| 工具 | 状态 | 平台 |
| --- | --- | --- |
| `check-doc-refs` | **核心** | `.sh` / `.ps1` |
| `review-backlog` | **核心** | `.sh` / `.ps1` |
| `run-n2-acceptance` | **核心** | Python |
| `check-code-refs` | **可选** | Python |
| `check-consistency` | **保留待瘦身** | Python |
| `_doc_common.py` | **依赖** | Python |
| `l2-docs.txt` | **依赖** | 清单 |
| `eval/run.ps1` | **skill 自测** | PowerShell |

**为什么这么定：**

- **`check-docs-sync` 删**：只查「代码动了、文档没动」，不查对不对；纯重构必误报，还逼人「碰一下文档」。**这一问现在没有脚本**，复核时看 `review-backlog` 的契约变化。
- **`lint-doc-structure` 删**：段落 / 标题 / 示例的风格启发式；可读性归复核与作者自检。
- **`check-code-refs` 降为可选**：反引号路径有独特价值，但窄且与 `check-doc-refs` 重叠；只在项目大量使用反引号路径时接。
- **`check-consistency` 保留待瘦身**：重复定义 / 悬空代号直接服务「一处成文」；下一轮砍掉数值、别名、单模块术语等低价值启发式。
- **`eval/run.ps1` 不随项目落地**：只跑 skill 侧单元测试，是维护入口，不是项目检查器。

## 三、工具矩阵

| 子问题 | 工具 | 类型 | 什么时候跑 | 输出 |
| --- | --- | --- | --- | --- |
| 对标代码 | `scripts/check-code-refs.py`（可选） | 脚本 | 项目需要时 | 路径 / 文件引用不存在；按需创建的 doc 标 `pending-doc` |
| 对标代码 | `last verified` SHA（可选） | 约定 | 批次 / 里程碑 | 文档基线过期提醒 |
| 自洽 | `scripts/check-doc-refs.sh/.ps1` | 脚本 | 编辑后 / CI（可选）/ 收尾 | 死链 / 占位符 / N2 缺验收（仅 N2 家：architecture / modules）/ 危险清单未填 / N2 模块缺失败语义 / 现状文档引记录 / 入口文档点具体 ADR 条目（`l1-entry-ref`） |
| 自洽 | `scripts/check-consistency.py` | 脚本（警告） | 约束性变更 / 批次 | 重复定义 / 同名数值冲突 / 重复字面量 / 未登记术语定义 / 悬空条款代号 / 超行数预算 / 参数别名跨文档 / 单模块术语（可选） |
| 核心逻辑 | `scripts/run-n2-acceptance.py` | 脚本 | 改代码前 / 批次 | 验收命令执行结果；无 manifest 只列不跑 |
| 复核范围 | `scripts/review-backlog.sh/.ps1` | 脚本（辅助） | 复核前 | 上次复核以来的契约变化 + 编号变化 |
| 可读性 | 复核 / 作者自检 | 约定 | 编辑后 / 批次 | 主流程长度 / 结构 / 是否抄实现 |
| 历史边界 | `check-doc-refs` 的「现状文档引记录」 | 脚本代理 | 编辑后 / CI（可选）/ 收尾 | 现状文档引记录 |
| 语义一致性 | `verification.md` / teach-back | 独立复核 | 改代码前 / 里程碑 | 缺口 + 判定 |
| 未来 | 无脚本 | 约定 / 复核 | 批次 | 状态 / 拍板人 / 结案条件 |

## 四、逐个工具

### 1. `check-doc-refs.sh` / `.ps1`

| 项 | 内容 |
| --- | --- |
| **功能** | `docs/` 的结构性对账：死链、占位符、N2 缺件、现状引记录、L1 点具体 ADR |
| **适用范围** | `docs/`（按 `DOC_EXCLUDE` 排除）；N2 家；`LIVE_DOCS`；L1 |
| **不适用** | 语义一致性；L4 当 N2 家；记录正文；模板正文 |
| **查什么** | 死链（含大小写错链）、未填占位符、N2 缺 `**验收**` / 「危险实现清单」、N2 模块缺「失败语义」、危险清单行未填、现状文档引记录、L1 点具体 ADR 条目 |
| **输入 / 参数** | `--strict` |
| **输出 / 退出码** | 结构发现；默认 0，`--strict` 有发现 1 |
| **保证 / 不保证** | 只查「结构上在不在」；不判验收有效、不判语义；模块按 `novelty=N2` 与验收计数 |
| **配置点** | `DOC_EXT`、`DOC_EXCLUDE`、`scripts/l2-docs.txt`、`LIVE_DOCS`、L1 名单 |
| **已知边界** | L2 改名要改 `scripts/l2-docs.txt`；仍是字面计数，短语出现在正文别处可能误判 |

### 2. `review-backlog.sh` / `.ps1`

| 项 | 内容 |
| --- | --- |
| **功能** | 列出「自上次复核以来」契约文档的变化，以及被增删改的编号 |
| **适用范围** | L1、L2、术语表、`docs/modules/`；git diff |
| **不适用** | 判定 / 拦门禁；上 pre-commit / CI；非 git；L4（阅读视图不算契约文件） |
| **输入 / 参数** | 无参数；起点在 `docs/reviews/.last-review` |
| **输出 / 退出码** | diff stat + 编号命中 + 写入起点的命令；恒 0 |
| **保证 / 不保证** | 只列清单；不判该不该复核；编号是启发式，可能漏 |
| **配置点** | `CONTRACT`（L2 来自 `scripts/l2-docs.txt`）、`MARKER`、编号族正则 |
| **已知边界** | 编号族仍是启发式；非 git 退化为人工清单；L4 按设计不监控 |

### 3. `run-n2-acceptance.py`

| 项 | 内容 |
| --- | --- |
| **功能** | 发现 N2 单元，列出或执行验收命令 |
| **适用范围** | N2 家 + manifest；`.live` 生效；发现模式只扫 N2 家，阅读视图不扫 |
| **不适用** | L4；从文档正文自动抽命令；判断验收是否有效 |
| **输入 / 参数** | `--root`、`--manifest`、`--run`、`--timeout`（默认 300s）、`--strict`、`--json` |
| **输出 / 退出码** | 默认**只列不跑**并标「未复跑」；`--run` 才执行清单显式命令，输出 `[PASS]` / `[FAIL]`；`--strict` 缺验收 / 空 N2 家 / manifest 覆盖不足退 1；`--run` 模式任一命令失败也退 1 |
| **保证 / 不保证** | 只执行 manifest 显式命令，不接受从文档抽的命令；会报覆盖不足，但不保证验收语义有效 |
| **配置点** | `scripts/l2-docs.txt`；manifest 路径（相对 `--root`） |
| **已知边界** | 一个模块只有一个 `novelty=N2` 标记时，后续单元可能被吞——多单元要每个单元一个标记（`check-doc-refs` 只能按标记计数）；`manifest.doc` 只是来源标记，不校验存在，错的 manifest 仍可能跑；`shell=True` / `cwd` 是信任边界（cwd 已限制在项目根内） |

### 4. `check-code-refs.py`（可选）

| 项 | 内容 |
| --- | --- |
| **功能** | 检查当前文档里的内联代码路径 / 文件名是否指向存在的文件 |
| **适用范围** | `docs/`（按 `.live` 或目录排除）+ L1；反引号 token；只把**已知路径前缀或文件扩展名**当路径，无斜杠 token 还必须是 ASCII |
| **不适用** | Markdown 链接（归 `check-doc-refs`）；代码行为；语义断言；不接 pre-commit |
| **查什么** | 路径 / 文件引用不存在；按需创建的文档缺失标 `pending-doc`（不算错误） |
| **跳过** | fenced code block、HTML 注释、URL、占位符、glob、裸扩展名与备选宿主文件名；记录类文档（`docs/decisions/`、`docs/reviews/`）不扫 |
| **输入 / 参数** | `--strict`、`--json` |
| **输出 / 退出码** | `[missing-ref]`、`[pending-doc]`；`--strict` 且仅有真发现时 1（pending 不算） |
| **保证 / 不保证** | 只保证「引用指向的文件存在」；不保证内容对 |
| **配置点** | `PENDING_DOCS`（L2 来自 `scripts/l2-docs.txt`）、`PATH_PREFIXES`、`EXT_RE` |
| **已知边界** | 非 ASCII 文件名按标识符跳过；L2 改名后缺失会算真发现 |

### 5. `check-consistency.py`（保留待瘦身）

| 项 | 内容 |
| --- | --- |
| **功能** | 启发式一致性警告 |
| **适用范围** | 当前文档 + README；`.live` 白名单；`--all-docs` 才扫全库；记录类文档不扫 |
| **不适用** | 语义正确性；向下引用判断（故意不做）；验收有效性 |
| **查什么** | 重复定义、未登记术语定义、同名数值冲突、重复字面量、参数别名跨文档、悬空条款代号、超行数预算（显式）、单模块术语候选（可选）、`live-missing` |
| **输入 / 参数** | `--strict`、`--json`、`--ignore`、`--ignore-alias`、`--max-lines`、`--no-budget`、`--glossary-locality`、`--min-term-mentions`、`--all-docs` |
| **输出 / 退出码** | 警告清单；默认 0，`--strict` 有警告 1 |
| **保证 / 不保证** | 只作启发式；不判语义；默认没有行数预算；不进 pre-commit 门禁 |
| **配置点** | 术语表路径、忽略键 / 别名、行数预算 |
| **已知边界** | 定义语境、术语表表头、单模块术语候选仍是启发式；语义判断归复核 |

### 6. `_doc_common.py` / `l2-docs.txt`（依赖）

| 项 | 内容 |
| --- | --- |
| **功能** | `_doc_common.py`：Python 检查器共享库；`l2-docs.txt`：L2 文件名清单（不是脚本，但所有检查器都读它） |
| **适用范围** | 共享库被 `run-n2-acceptance` / `check-consistency`（以及可选的 `check-code-refs`）import；清单随 `scripts/` 同拷 |
| **不适用** | 独立运行；项目文档规则 |
| **内容** | L1 文件名、默认排除目录、`.live` 白名单、`scripts/l2-docs.txt`、`iter_docs`、fenced / comment mask、`read_lines`、`rel` |
| **输出 / 退出码** | 无 |
| **保证 / 不保证** | 保证几个 Python 检查器口径一致；不单独拷会 import 失败 |
| **配置点** | 无；必须与其他 Python 脚本同拷。L2 文件名改这里，不要在脚本里再写一份 |
| **已知边界** | 空 `.live` 会让 `iter_docs` 只产出 L1；注释 mask 按行处理 |

### 7. `eval/run.ps1`（skill 自身验收）

| 项 | 内容 |
| --- | --- |
| **功能** | 跑 skill 侧单元测试，作为 skill 发布 / 维护的验收入口 |
| **适用范围** | skill 维护者；`tests/test_scripts.py` |
| **不适用** | 项目文档检查；不随项目落地 |
| **输入 / 参数** | 无 |
| **输出 / 退出码** | `PASS` / `FAIL`；测试失败退 1 |
| **保证 / 不保证** | 保证测试通过；不保证被测文档语义正确 |
| **配置点** | 无 |
| **已知边界** | PowerShell 入口；用 `cmd` 合并 stdout / stderr |

## 五、两种证据状态

| 状态 | 含义 | 有没有扫描证据 | 能不能算通过 |
| --- | --- | --- | --- |
| **未接入** | `scripts/` 没投进项目 | 无 | 不能 |
| **未复跑** | 脚本在，但只列未执行 | 有扫描，无执行 | 不能 |

留档写「未接入 / 未复跑」复合式，**不得当成已通过**。本文只定义脚本产生的两种证据状态；复核状态「未复核」不由脚本产生，但同样不得当成通过。

**非 git 项目**：`review-backlog` 的变化对比能力不可用 → 退化为人工清单，并在文档里标「未复跑」。

## 六、用法

```bash
# 0) 核心结构核对（与 .ps1 同名）
bash scripts/check-doc-refs.sh
bash scripts/review-backlog.sh

# 1) 可选：内联代码引用（只在项目大量使用反引号路径时）
python scripts/check-code-refs.py --root . --strict

# 2) N2 验收：先列，不跑
python scripts/run-n2-acceptance.py --root . --manifest docs/n2-acceptance.json

# 3) N2 验收：真的跑（只在显式 manifest 下执行）
python scripts/run-n2-acceptance.py --root . --manifest docs/n2-acceptance.json --run

# 4) 一致性警告（约束性变更 / 批次；--ignore 可忽略指定数值键）
python scripts/check-consistency.py --root . --ignore localhost,http,https
#    术语下沉候选（可选、粗判，人工复核）
python scripts/check-consistency.py --root . --glossary-locality --ignore amp,wl
#    只关心预算（显式给值才查；不传就不查；--no-budget 强制关闭）
python scripts/check-consistency.py --root . --max-lines 400
```

通用参数（仅 Python 脚本）：`--root DIR`（默认当前目录）、`--json PATH`（机器可读输出；`run-n2-acceptance.py` 的列表模式也支持）。

**`--strict` 的含义按脚本不同**：`check-code-refs`（可选）/ `check-consistency` = 有 finding 退 1；`run-n2-acceptance` = **无 manifest 的发现模式**下缺 `**验收**` 行退 1、`--run` 模式**总是**在任一命令失败时退 1（与 `--strict` 无关）；manifest 列表模式不检查验收行。

**L1 文件集**：`AGENTS.md` / `CLAUDE.md` / `.cursorrules` / `.cursor/rules/project.mdc` / `.windsurfrules` / `.github/copilot-instructions.md`。

### N2 验收 manifest 格式

```json
{
  "units": [
    {
      "id": "N2-1",
      "doc": "docs/modules/foo.md",
      "command": "python -m pytest tests/test_foo.py -q",
      "cwd": "."
    }
  ]
}
```

没有 manifest 时，脚本只在 N2 家（`docs/architecture.*`，以及**实际承载五件套**的 `docs/modules/*`——以文件里出现「危险实现清单」为准）扫描 `novelty=N2`，并取**从该标记到下一个 `novelty=` 标记（或文件末）**之间的第一条 `**验收**`，打印「发现但未执行」，输出明确标 **未复跑**；这不算通过。`--strict` 可要求每条 N2 都有 `**验收**` 行。`--timeout`（默认 300s）控制 `--run` 时单条命令的超时。

**里程碑 / 发布**：全部脚本；命中四信号才开复核，档位按 `P-1` 选（见 M5）。

**非 git 项目**：`review-backlog` 的 delta 能力不可用 → 退化为人工清单，并在文档里标「未复跑」。

## 七、接入项目

### 7.1 先分清两个时机

- **改代码前（主战场）**：可选 `check-code-refs` + 约束变更时 `check-consistency` + N2 变更时 `run-n2-acceptance` + 相关视角的复核（M5）。文档是实现的约束，这一步才是「提前拦截」。
- **commit（轻）**：不默认接脚本；结构检查放 CI / 收尾，复核时用 `review-backlog` 看契约 delta。

### 7.2 先拷进项目

按 `deployment.md` 投**核心脚本 + `l2-docs.txt`**（如 `<repo>/scripts/`）：

- `check-doc-refs.sh/.ps1`
- `review-backlog.sh/.ps1`
- `run-n2-acceptance.py` + `_doc_common.py`
- `l2-docs.txt`

**可选**：`check-code-refs.py` / `check-consistency.py`（同样需要 `_doc_common.py`）。

**已决移除的不投**：`check-docs-sync` / `lint-doc-structure`。

> `check-doc-refs.sh` 顶部有两项：`DOC_EXT`（文档扩展名，默认 `.md` + `.markdown`）与 `DOC_EXCLUDE`（核对要**排除**的路径，默认排除 `docs/legacy/`、`docs/archive/` 等归档区、`docs/reviews/` 核对留档、以及 `docs/templates/` 等模板目录）。L2 文件名改 `l2-docs.txt`。

### 7.3 换行符与编码

**Windows 必读——先把换行符定死。**

Windows 默认 `core.autocrlf=true`，投进项目的 `.sh` 会被检出成 CRLF；**Linux / WSL / CI 上这会直接语法错**（`$'\r': command not found`），若已接 pre-commit，会挡住**每一次**提交，报错还像「hook 坏了」——很容易被整个删掉。（Git Bash 多数版本能容忍 CRLF，但别赌。）落地一行防住（`.gitattributes` 不存在就新建，存在就追加）：

```bash
printf '*.sh text eol=lf\n' >> .gitattributes
```

`.ps1` 不受换行影响；但**必须保持 UTF-8 BOM**——PowerShell 5.1 读无 BOM 的 UTF-8 会乱码甚至解析失败，别把文件重存成 ANSI / 无 BOM。

### 7.4 对齐五条书写格式（否则别接）

`check-doc-refs` 认的是**当前 skill 的五条书写格式**——脚本按字面识别，对不上就漏报（这不是「只能靠自觉」那类约定）：

- N2 条目用**字面量** `novelty=N2` 标记；
- 每个 N2 配一个独立一行 `**验收**:…`；
- N2 文档必须有「危险实现清单」；承载五件套的模块文档必须有「失败语义」一节——**L2 按 `novelty=N2` 字面量判，模块按「危险实现清单」判**：模块顶部的 `novelty=` 是**模块档位**（五件套上移 L2 后仍是 N2），不代表规格住在这个文件里；模块文档不写「验收见 docs/…」的引用行，因此不会因为档位被误报；
- 危险实现清单的数据行，「挡住者」列要有内容、不能是占位符——列位置由表头定位（表头那一格须含「挡住」），**不看列数与写法**；
- 边界如实说：判据数的是**字面**（短语在别处出现会让「缺清单」漏报）；**没有文件级豁免**。唯一例外是 L1 的「活文档索引」：它允许出现**目录级**记录引用（`docs/decisions/` / `docs/reviews/`），但**具体 ADR 条目**仍报 `l1-entry-ref`；子索引（架构 → 模块等）里出现记录类目录照报。

**「N2 缺验收」只做次数粗检**（仅 N2 家：`architecture` / 承载五件套的 `modules`；L2 数 `novelty=N2` > `**验收**` 才报，模块按「含「危险实现清单」却无 `**验收**`」报；检查器为兼容旧文档也接受行内写法；**文档规范仍要求独立一行**），逐条配对不对仍归复核。

**「缺危险实现清单 / 缺失败语义」只做字面级下界**——那节是否写清、清单是否真挡住，仍归复核。

**「现状文档引记录」的边界**：`docs/` 下的现状文档出现 `docs/decisions/`、`docs/reviews/`、`ADR-0NN` 任一即报；L1 例外——活文档索引里的**目录级**记录引用放行，具体 `ADR-0NN` 条目报，`adr-000-template` 放行。「`> 出处：…`」与「含 ⚠ 的行」都不再豁免（那两种写法已退役）。

（写法见 `docs-templates/module-doc.md` 的 N2 节 / `docs-templates/architecture.md` 的「N2 单元规格」——后者按需从 skill 的 `templates/architecture.md` 落地。）

> **扫哪些文件**：N2 计数与危险实现清单看 `docs/architecture.md`、`docs/modules/*`；`docs/core-analysis.md`（L4）**不再扫**——它是阅读视图，不给验收；「现状文档引记录」还看 `docs/glossary.md`。
> 项目 L2 改名 → 改 `scripts/l2-docs.txt`；N2 家（架构 / 模块）仍按脚本顶部的扫描表。改完跑一次 `check-doc-refs`，确认没有空跑。

若项目用的是**别的写法**——典型是**早期版本**的 L1（只有「N2 必须给步骤 / 例子 / 验收」这样的文字规则，文档里没有 `novelty=N2` 标记）——直接接上会：

- **漏报**：没有 `novelty=N2` 字面量 → 核对永远看不到 N2 条目，这道门禁形同虚设；
- **噪音**：`DOC_EXT` / `DOC_EXCLUDE` 没调好时，不该扫的文件（模板 / 归档区）被当成核对对象扫。

**对策（二选一）：**

1. 先把项目对齐到上面的书写格式（用 `docs-templates/` 里的模板）；或
2. **只接 `review-backlog`**——它只列契约文件变化，**与书写格式无关**；`check-doc-refs` 等书写格式对齐了再上。

### 7.5 接法

**A. pre-commit（可选，不默认）**

`.git/hooks/pre-commit`（记得 `chmod +x`）：

```bash
#!/usr/bin/env bash
bash scripts/check-doc-refs.sh || true
# 可选：项目大量使用反引号路径时
# python scripts/check-code-refs.py --root . || true
```

或写进 pre-commit 框架的 `.pre-commit-config.yaml`，便于团队分发。

> **不要默认挡每次提交**；结构检查放 CI / 收尾。`check-doc-refs` 初期先不加 `--strict`，当提醒用，等**检查结果干净**了再收紧。

**B. CI（GitHub Actions）**

`.github/workflows/docs-guard.yml`：

```yaml
name: docs-guard
on: [pull_request]
jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - run: bash scripts/check-doc-refs.sh
      - run: bash scripts/review-backlog.sh
```

**C. 宿主钩子（Claude Code / OpenCode / …）**

各宿主机制不同（Claude Code 有 hooks 事件如 Stop / PreToolUse；OpenCode 有 plugin），**skill 不硬绑**。
通用做法：在「一轮结束 / 每次写文件后」触发 `check-doc-refs.sh`（非 `--strict`），**只打印提醒、不阻塞**。
宿主钩子更适合轻提醒；**门禁交给 CI / pre-commit**。

### 7.6 何时用哪个

| 脚本 | 查什么 | 误报 | 建议 |
| --- | --- | --- | --- |
| `check-doc-refs` | 结构类 → 见 §四 | 低-中 | 先当提醒，**检查结果干净**后加 `--strict`；建议放编辑后 / CI（可选）/ 收尾，不挡每次提交 |
| `review-backlog` | 复核 delta | 无判定 | 复核前手动跑；不拦门禁 |
| `check-code-refs.py`（可选） | 内联代码引用 → 见 §四 | 低 | 只在项目大量使用反引号路径时接 |
| `run-n2-acceptance.py` | N2 验收命令执行结果；无 manifest 只列不跑 | 取决于项目 | 改代码前 / 批次；`--run` 才执行 |
| `check-consistency.py`（保留待瘦身） | 启发式若干项 → 见 §四 | 中（启发式） | 只当警告，不进 pre-commit |

## 八、已知抓不到（不打算修）

- 单模块术语按提及次数粗判，不等于「当作规则使用」；
- 别名判据依赖术语表里的反引号，术语下沉后失效；
- 改写式副本与纯文本引用（`见核对记录 …`）不报——加了易误伤；
- 机器只查**结构性**（动不动、链在不在、字段缺不缺）；语义对不对仍靠复核 + 人。

`run-n2-acceptance.py --run` 会执行命令：只跑清单里显式列出的，不接受从文档里自动抽取的命令。

## 九、改动纪律

### 1. 新增脚本

每个新机器判据上线前必须：

1. **反向测试**：构造一个「必须报」的输入（如把路径改成不存在的），看它报不报。
2. **确认它数的是什么**：是字面出现，还是语义成立？把边界写进脚本注释与本文档。
3. **两平台各跑一遍**、输出对齐。
4. **先补内容、再上判据**。

上线同时更新四处：本文「工具集」加一行、「逐个工具」加一张卡片、「工具矩阵」加一行、补测试；标证据状态，写清「不保证什么」。

**执行面**：`[脚本可查]`（`tests/` 里必须有对应用例）；「两平台各跑一遍」没有自动化，靠自觉。

测试：`python -m unittest discover -s tests`（skill 侧 `tests/`）。

### 2. 修改行为

**只改行为时**，同步改脚本、对应卡片和测试；只有状态或取舍变了，才动「工具集」和「工具矩阵」。**不要只改脚本。**

### 3. 脚本注释标准

文件头最多三行：

```text
# <tool> — <一句话：把什么变成什么>
# 合同: <输入 → 输出；退出码>
# 边界: <只写那条会让人误信绿灯的边界；没有就不写>
```

代码里只留两类注释：

- **平台陷阱**：BOM / CRLF / PowerShell 5.1 / Git Bash 这类不写就会再踩的坑；
- **非显然决策**：为什么只能这样、被拒方案是什么。

不写：

- 日期 / 版本史 / 变更记录（进 git）；
- 「不保证 A、B、C……」的开放清单（进本文的保证 / 不保证表）；
- 复述代码；
- 没有条件的 TODO / 愿望；
- 把已知 bug 写成「设计」。

判定：删掉这条注释，下一个人会不会改错？不会 → 删。

### 4. 本文件不是第二套规则

与脚本实际行为冲突时，**以脚本行为为准**，并回来修正本文件。

## 十、自检

- [ ] 脚本是投进来了，还是标了「未接入」？
- [ ] 跑了的标「已复跑」，没跑的标「未复跑」了吗？
- [ ] 只接「核心清单」了吗？已决移除的 `check-docs-sync` / `lint-doc-structure` 没有被接进来吧？
- [ ] `check-doc-refs` 是否在结果干净后才加 `--strict`？
- [ ] `.sh` 是 LF、`.ps1` 保留 BOM 吗？
- [ ] 项目的 L2 文件名改过吗？改过有没有改 `scripts/l2-docs.txt`？
- [ ] 新增 / 修改脚本时，工具集、卡片、矩阵、测试同步了吗？
- [ ] 新增脚本有没有反向测试、两平台跑过？
- [ ] 脚本注释是否只留了平台陷阱与非显然决策？
