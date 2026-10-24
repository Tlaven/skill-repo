# 工具体系:当下层的可执行检查

> **原则**:只给**高精度、低噪音**的规则配脚本;语义一致性、可读性判断交给 `review-panel.md` / teach-back。现有脚本是基座,扩展不替换。
>
> 三层执行面:**`[脚本可查]`** / **`[需独立复核]`** / **`[只能靠自觉]`**。工具只承担第一层。
>
> **术语:** 未接入 = `scripts/` 未拷入;未复跑 = 脚本在但这次只列未执行;基线 = **文档基线**(`last verified` SHA)/ **校准基线**(另见 `calibration-guide.md`)/ **分档基线**;快照 = **现状快照**;冻结 = **冻结计数 / 冻结期望**。裸用这几个词时按本行限定。

## 一、工具矩阵

| 子问题 | 工具 | 类型 | 什么时候跑 | 输出 |
|---|---|---|---|---|
| 对标代码 | `scripts/check-code-refs.py` | 脚本 | 改代码前(文档基线)/ commit | 路径 / 文件引用不存在;按需创建的 doc 标 `pending-doc` |
| 对标代码 | `scripts/check-docs-sync.sh/.ps1` | 脚本 | commit | 代码动了、文档没动 |
| 对标代码 | `last verified` SHA(可选) | 约定 | 批次 / 里程碑 | 文档基线过期提醒 |
| 自洽 | `scripts/check-doc-refs.sh/.ps1` | 脚本 | 编辑后 / CI(可选) / 收尾 | 死链 / 占位符 / N2 缺验收 / 危险清单未填 / 模块缺失败语义 / 现状文档引记录 |
| 自洽 | `scripts/check-consistency.py` | 脚本(警告) | 契约级变更 | 重复定义 / 同名数值冲突 / 未登记术语定义 |
| 核心逻辑 | `scripts/run-n2-acceptance.py` | 脚本 | 改代码前 / 批次 | 验收命令执行结果;无 manifest 只列不跑 |
| 可读性 | `scripts/lint-doc-structure.py` | 脚本(警告) | 编辑后 / 批次 | 段落过长 / 缺小标题 / 缺示例 |
| 历史边界 | `check-doc-refs` 的「现状文档引记录」 | 脚本代理 | 编辑后 / CI(可选) / 收尾 | 现状文档引记录 |
| 历史边界 | `scripts/adr-index.py` | 脚本 | 记 ADR / commit | 索引漂移 / 状态非法 / 关系悬空 / 引用悬空或指向已废记录 / superseded 未归档 / 追加式违例 |
| 语义一致性 | `review-panel.md` / teach-back | 独立复核 | 改代码前 / 里程碑 | 缺口 + 判定 |
| 未来 | 无脚本 | 约定 / 复核 | 批次 | 状态 / 拍板人 / 结案条件 |

## 二、脚本清单

### 现有

- `check-docs-sync.sh/.ps1` —— 代码动了但 `docs/` 与 L1 没动 → 提醒。只查"有没有动过"。
- `check-doc-refs.sh/.ps1` —— 结构性对账:死链(含大小写)、占位符、N2 缺 `**验收**` / 危险清单、模块缺失败语义、危险清单行未填、现状文档引记录。
- `review-backlog.sh/.ps1` —— 不判定、不拦截;列出上次复核以来的契约 delta。

### 新增(Python 3.8+,仅标准库)

- **`check-code-refs.py`** —— 扫 `docs/` + L1 里的反引号 token;**记录类文档(`docs/decisions/`、`docs/reviews/`)不扫**(历史可以引用已删文件,那不是漂移);只把**已知路径前缀或文件扩展名**当路径,无斜杠 token 还必须是 ASCII(`父.h`/`邻.h` 是标识符,不是文件名)。跳过 fenced code block、HTML 注释、URL、占位符(`<…>`/`…`)、glob、裸扩展名(`.sh`)与 L1 文件名(`AGENTS.md` / `CLAUDE.md` 等,避免把备选宿主名当缺失文件);按需创建的 `docs/architecture.md|.markdown` / `glossary.*` / `core-code.*` / `scaffolds/` / `modules/…` / `decisions/…` / `reviews/…` 与 `task_plan.md` 缺失时标 `pending-doc`,不算错误。
- **`run-n2-acceptance.py`** —— 读 N2 验收 manifest,列出或执行验收命令。**默认只列不跑并标「未复跑」**;`--run` 才执行 manifest 里显式列出的命令;`--strict` 只在**无 manifest 的发现模式**下要求每条 N2 都有 `**验收**` 行。
- **`check-consistency.py`** —— 启发式警告:同一术语在 `docs/` 多处定义、同名数值在**内联代码 / 表格**里出现不同值、非 glossary 的术语定义未登记。**记录类文档不扫**;定义只认"定义语境"小节(`是什么 / 定义 / 术语 / 概念`)或无小标题的文件——`[为什么]` / `[不变量]` 的粗体领起句是论述,不是定义。L1 的强调 bullet 不算术语定义;glossary 自己的唯一一条不算重复。只作警告,不进 pre-commit 门禁。
- **`lint-doc-structure.py`** —— 结构警告:段落过长(默认 >20 行)、没有小标题、没有示例 / 表格 / 代码块 / 列表。只作警告。
- **`adr-index.py`** —— ADR 索引生成 + 元数据对账。**索引必须生成,不能手写**(手写的索引在第一个忙周就会漂);`--write` 重写 `README.md` / `README.markdown` 里 `<!-- adr-index:begin -->` / `<!-- adr-index:end -->` 之间的块,`--strict` 在有 finding 时退 1。查的是**确定性**部分:ID 唯一、标题 `# <ID>: <title>`（`:` 与 `：` 都认）与文件名一致、状态在规范集内（`superseded` 必须带 `superseded_by`）、关系目标存在（本目录或 `archive/`）、索引与记录一致。**只列现役（accepted / accepted(修订)）与在议（proposed）**;被取代 / 弃用 / 被拒的不进索引。警告（不失败）:superseded 仍留在主目录（应移进 `archive/`）、`archive/` 有记录但 `docs/decisions/.ignore` 没写 `archive/`（`adr-no-ignore`——机制失效是静默的,见 `references/search-surface.md`）、单条超词数上限（默认 800,`--max-words` 可调;超过 3 条时只打一行汇总 + 最长三条,免得淹没别的警告）。**状态取前导词**:`accepted(2026-10-15)`、`accepted(已落地：…照它改了)`、`⚠️ accepted(…)` 都算 `accepted`,括号与后面的散文是注记不是状态;只有前导词不在规范集内才报。状态优先读 frontmatter,没有则回退到旧格式的 `## 状态` 段——**按记录逐条迁移即可**,不需要一次性改写全部历史。
  - **引用对账（默认开）:** 扫 L1、`docs/`（记录类除外）、`SKILL.md`、`references/`;`--scan DIR|FILE` 可加路径（如代码目录）。引用了不存在的 ID → finding;引用了 `superseded` / `deprecated` / `rejected` 的记录 → warning（「改引现行记录，或删掉引用」）。**记录类文档不扫**——历史引用历史是常态。
  - **追加式校验（`--immutable`,默认关）:** 拿 `--base`（默认 `HEAD`）里的记录与工作区比,允许 frontmatter 改动、标题下的 superseded 注记、**在文末追加补充**;正文被改写 / 删除 → finding;记录消失 → finding（应移进 `archive/`,不是删掉）。非 git 或 base 不存在时跳过并说明。
  - **它不判断语义**:「考虑过的方案」里哪条是被拒的、结论是不是自洽,仍靠复核。
- **`_doc_common.py`** —— **共享模块**:上面 5 个 Python 检查器都 import 它,必须与它们同拷;不要单独漏掉。

> **脚本落地:** Step 2A 默认把 `scripts/` 拷进 `<repo>/scripts/`;未拷则 L1 标「scripts: 未接入」,后续命令按「未复跑」处理。
> **两种证据状态:** **未接入** = `scripts/` 未拷入(没有任何扫描证据);**未复跑** = 脚本在但只列未执行(有扫描,无执行)。留档写「未接入 / 未复跑」复合式,不得当成已通过。

## 三、用法

```bash
# 0) 旧对账脚本(与 .ps1 同名;只接受各自的 --strict / --staged 参数)
bash scripts/check-docs-sync.sh --staged --strict
bash scripts/check-doc-refs.sh
bash scripts/review-backlog.sh

# 1) 内联代码引用(改代码前 / commit 轻量)
python scripts/check-code-refs.py --root . --strict

# 2) N2 验收:先列,不跑
python scripts/run-n2-acceptance.py --root . --manifest docs/n2-acceptance.json

# 3) N2 验收:真的跑(只在显式 manifest 下执行)
python scripts/run-n2-acceptance.py --root . --manifest docs/n2-acceptance.json --run

# 4) 一致性警告(契约级变更 / 批次;--ignore 可忽略指定数值键)
python scripts/check-consistency.py --root . --ignore localhost,http,https

# 5) 结构警告(编辑后 / 批次;--max-paragraph-lines 默认 20)
python scripts/lint-doc-structure.py --root .

# 6) ADR 索引:生成 + 对账(记 ADR 后 / commit)
python scripts/adr-index.py --root . --write      # 重新生成索引块
python scripts/adr-index.py --root . --strict     # CI / pre-commit 对账
python scripts/adr-index.py --root . --strict --immutable --base HEAD   # 追加式校验
```

通用参数(仅 Python 脚本):`--root DIR`(默认当前目录)、`--json PATH`(机器可读输出;`run-n2-acceptance.py` 的列表模式也支持)。
`adr-index.py` 另有 `--dir`(默认 `docs/decisions`)、`--index`(默认 `<dir>/README.md`,没有则用 `README.markdown`)、`--write`(就地重新生成索引块)、`--no-citations`(跳过引用对账)、`--scan`(追加扫描路径,可重复)、`--max-words`(超词警告阈值,默认 800)、`--immutable` + `--base`(追加式校验,默认 `HEAD`)。
`--strict` 的含义按脚本不同:`check-code-refs` / `check-consistency` / `lint-doc-structure` / `adr-index` = 有 finding 退 1（`adr-index` 的 `adr-archive` / `adr-long` / `adr-cite-retired` / `adr-no-ignore` 是 warning,不参与退 1）;`run-n2-acceptance` = **无 manifest 的发现模式**下缺 `**验收**` 行退 1、`--run` 模式**总是**在任一命令失败时退 1(与 `--strict` 无关);manifest 列表模式不检查验收行。
**L1 文件集**(与 `check-docs-sync` 对齐):`AGENTS.md` / `CLAUDE.md` / `.cursorrules` / `.cursor/rules/project.mdc` / `.windsurfrules` / `.github/copilot-instructions.md`。

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

没有 manifest 时,脚本只扫描 `novelty=N2` 与 `**验收**:`(在 N2 行后 40 行内查找)并打印"发现但未执行",输出明确标 **未复跑**;这不算通过。`--strict` 可要求每条 N2 都有 `**验收**` 行。`--timeout`(默认 300s)控制 `--run` 时单条命令的超时。

## 四、什么时候跑

| 时机 | 跑什么 |
|---|---|
| 改代码前(主) | `check-code-refs` + `check-consistency`(契约变更)+ `run-n2-acceptance`(N2 变更)+ 相关镜头 panel |
| commit(轻) | `check-docs-sync` + `check-code-refs` + `adr-index --strict` |
| 里程碑 / 发布 / 大改 | 全部脚本 + 全 panel + 校准探针 |
| 编辑后(可选) | `check-doc-refs` + `lint-doc-structure` |

**非 git 项目**:`check-docs-sync` / `review-backlog` 的 delta 能力不可用 → 退化为人工清单,并在文档里标"未复跑"。

## 五、新增脚本的验收纪律

每个新机器判据上线前必须:

1. **反向测试**:构造一个"必须报"的输入(如把路径改成不存在的),看它报不报。
2. **确认它数的是什么**:是字面出现,还是语义成立?把边界写进脚本注释与本文档。
3. **两平台各跑一遍**、输出对齐。
4. **先补内容、再上判据**:内容没写完就上检查器,只会把"没写"变成噪音。

测试:`python -m unittest discover -s tests`(skill 侧 `tests/`)。

## 六、边界

- 工具只查**结构性 / 可证伪**的东西;**语义对不对**仍靠 panel / teach-back + 人。
- **不要把"检查器过了"当成"文档对了"**。
- 警告类脚本不要接成硬门禁;否则噪音会让人开始无视所有提示。
- `run-n2-acceptance.py --run` 会执行命令:只跑 manifest 里显式列出的,不接受从文档里自动抽取的命令。
