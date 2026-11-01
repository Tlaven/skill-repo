# 把检查器接上（pre-commit / CI / 宿主钩子）

> 目的：让 methodology 铁律里标 `[脚本可查]` 的规则**真的会触发**，而不是停在脚本里等人手动跑。
> 两个检查器脚本（Windows 用同名 `.ps1`）：
> - `scripts/check-docs-sync.sh` —— 代码动了但本项目当前维护的文档(`docs/` 除 `docs/reviews/` 对账留档——历史快照不算同步)与 L1 记忆文件都没动 → 提醒。
> - `scripts/check-doc-refs.sh` —— `docs/` 的结构性检查(能力清单见 `references/tooling.md`)。
>
> 另有 `scripts/review-backlog` —— **辅助脚本,不属于本页的接线面**:不判定、不拦截(退出码恒 0),复核前手动跑,列出"自上次复核以来的契约 delta"。不上 pre-commit / CI。
>
> **新增(Python 3.8+,仅标准库):** `check-code-refs.py`、`run-n2-acceptance.py`、`check-consistency.py`、`lint-doc-structure.py`;共享模块 `_doc_common.py` 必须与它们同拷。**能力清单只在 `references/tooling.md` 成文**,这里不复述。

## 先分清两个时机

- **改代码前(主战场):** `check-code-refs` + 契约变更时 `check-consistency` + N2 变更时 `run-n2-acceptance` + 相关镜头的 review panel。文档是实现的契约,这一步才是"提前拦截"。
- **commit(轻):** `check-docs-sync` + `check-code-refs`。只做事后漂移提醒;不跑完整 panel。

## 先拷进项目

把 `scripts/` 拷进项目（如 `<repo>/scripts/`），并按项目改 `check-docs-sync.sh` 顶部的三行路径：

> 脚本里 `CODE_GLOB` 默认是**扩展名式**（形如 `\.(js|ts|py|...)$`，适配代码散落或在根目录的项目）；若代码集中在少数目录，改成下面的**目录式**更准。

```bash
CODE_GLOB='^(src|lib|app|packages)/'
DOC_GLOB='^docs/'
L1_FILES='AGENTS.md CLAUDE.md .cursorrules .cursor/rules/project.mdc .windsurfrules .github/copilot-instructions.md'
```

> `check-doc-refs.sh` 顶部另有两项:`DOC_EXT`(文档扩展名,默认 `.md` + `.markdown`)与 `DOC_EXCLUDE`(对账要**排除**的路径,默认排除 `docs/legacy/`、`docs/archive/` 等**存档层**、`docs/reviews/` **对账留档**(历史快照,引用退役术语/旧链是常态)、以及 `docs/templates/` 等**待填件目录**——它们不是本项目当前维护的文档,扫进来只会制造噪音)。

> **Windows 必读——先把换行符定死。**
> Windows 默认 `core.autocrlf=true`，拷进项目的 `.sh` 会被检出成 CRLF；**Linux / WSL / CI 上这会直接语法错**（`$'\r': command not found`），若已接 pre-commit，会挡住**每一次**提交，报错还像"hook 坏了"——很容易被整个删掉。（Git Bash 多数版本能容忍 CRLF，但别赌。）落地一行防住（`.gitattributes` 不存在就新建，存在就追加）：
>
> ```bash
> printf '*.sh text eol=lf\n' >> .gitattributes
> ```
>
> `.ps1` 不受换行影响；但**必须保持 UTF-8 BOM**——PowerShell 5.1 读无 BOM 的 UTF-8 会乱码甚至解析失败，别把文件重存成 ANSI / 无 BOM。

## 接入前先对齐五条书写格式（否则别接）

`check-doc-refs` 认的是**当前 skill 的五条书写格式**——脚本按字面识别,对不上就漏报(这不是"只能靠自觉"那类约定):

- N2 条目用**字面量** `novelty=N2` 标记;
- 每个 N2 配一个独立一行 `**验收**:…`;
- N2 文档必须有「危险实现清单」;N2 模块文档必须有「失败语义」一节——**按 `novelty=N2` 字面量判**:跨模块 N2 的五件套与 `novelty=N2` 只写在一处(`architecture.md` 的 `N2: <单元>` 节),模块文档不声明、也不写"验收见 docs/…"的引用行,因此不会被误报;
- 危险实现清单的数据行，「挡住者」列要有内容、不能是占位符——列位置由表头定位（表头那一格须含"挡住"），**不看列数与写法**;
- 边界如实说:判据数的是**字面**（短语在别处出现会让"缺清单"漏报）;**没有文件级豁免**。唯一例外是 L1 的「活文档索引」：它允许出现**目录级**记录引用（`docs/decisions/` / `docs/reviews/`），但**具体 ADR 条目**仍报 `l1-entry-ref`；子索引(架构 → 模块等)里出现记录类目录照报(能力边界见 `tooling.md`)。

**"N2 缺验收"只做次数粗检**（仅 N2 家：`architecture` / `modules`；`novelty=N2` 计数 > `**验收**` 计数才报；检查器为兼容旧文档也接受行内写法；**文档规范仍要求独立一行**），逐条配对不对仍归复核。
**"缺危险实现清单 / 缺失败语义"只做字面级下界**——那节是否写清、清单是否真挡住，仍归复核。
**危险实现清单只做行级粗检**（"挡住者"列非空、非占位符）——写法是否真挡得住仍归复核。
**「现状文档引记录」的边界**:`docs/` 下的现状文档出现 `docs/decisions/`、`docs/reviews/`、`ADR-0NN` 任一即报；L1 例外——活文档索引里的**目录级**记录引用放行，具体 `ADR-0NN` 条目报，`adr-000-template` 放行。"`> 出处：…`"与"含 ⚠ 的行"都不再豁免（那两种写法已退役）。

> **新增机器判据的验收**（否则它会在真实项目里误报或漏报）:① **反向测试**——构造一个"必须报"的输入（如把那一节的标题改名），看它报不报;② **确认它数的是什么**（字面出现 ≠ 那一节存在），把这个边界写进注释与文档;③ 两平台各跑一遍、输出对齐。**先补内容、再上判据**——内容还没写完就上检查器，只会把"没写"变成噪音。

(写法见 `docs-templates/module-doc.md` 的 N2 节 / `docs-templates/architecture.md` 的「N2 单元规格」——后者按需从 skill 的 `templates/architecture.md` 落地。)

> **扫哪些文件:** N2 计数与危险实现清单看 `docs/architecture.md`、`docs/modules/*`；`docs/core-code.md`（L4）**不再扫**——它是阅读视图，不给验收；「现状文档引记录」还看 `docs/glossary.md`。
> 跨模块 N2 的**五件套正文**在 **L2 `docs/architecture.md` 的 `N2: <单元>` 节**。理由：判据是"被 ≥2 个**模块**的工作场景当前置读"（不是数加载表行数），而 L2 本来就在这些场景的加载集里；L4 可选、不默认加载，**把规格放 L4 = 没人读得到**。
> 项目改了 N2 家文件名 → 把新名字加进脚本顶部的 **N2 扫描表**；项目 L2 改名 → 加进 `LIVE_DOCS`（两张表都有“按项目改”标注），否则对应检查会对它空跑。

若项目用的是**别的写法**——典型是**早期版本**的 L1(只有"N2 必须给步骤 / 例子 / 验收"这样的**文字规则**,文档里没有 `novelty=N2` 标记)——直接接上会:

- **漏报**:没有 `novelty=N2` 字面量 → 对账永远看不到 N2 条目,这道门禁形同虚设;
- **噪音**:`DOC_EXT` / `DOC_EXCLUDE` 没调好时,不该扫的文件(待填件 / 存档层)被当成对账对象扫。

**对策(二选一):**

1. 先把项目对齐到上面的书写格式(用 `docs-templates/` 里的模板);或
2. **只接 `check-docs-sync`**——它只查"代码动没动、文档动没动",**与书写格式无关**,任何项目都能接;`check-doc-refs` 等书写格式对齐了再上。

## 方式 A：pre-commit（最省事）

`.git/hooks/pre-commit`（记得 `chmod +x`）：

```bash
#!/usr/bin/env bash
bash scripts/check-docs-sync.sh --staged --strict || {
  echo "改代码但没同步文档。要跳过：git commit --no-verify"; exit 1; }
[ -f scripts/check-code-refs.py ] && python scripts/check-code-refs.py --root . || true
# check-doc-refs 建议放 CI / 收尾;不要挡每次提交(见 tooling.md)
```

或写进 [pre-commit 框架] 的 `.pre-commit-config.yaml`，便于团队分发。

> 建议 `check-docs-sync` 用 `--strict`（它是"动不动"检查，误报极低——纯重构提交只改代码、不碰文档时会命中，属已知例外，用 `git commit --no-verify` 放行）；`check-doc-refs` 初期先不加 `--strict`，当提醒用，等**检查结果干净**了再收紧。

## 方式 B：CI（GitHub Actions）

`.github/workflows/docs-guard.yml`：

```yaml
name: docs-guard
on: [pull_request]
jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }      # check-docs-sync 需要历史
      - run: bash scripts/check-docs-sync.sh origin/${{ github.base_ref }} --strict
      - run: bash scripts/check-doc-refs.sh
```

## 方式 C：宿主钩子（Claude Code / OpenCode / …）

各宿主机制不同（Claude Code 有 hooks 事件如 Stop / PreToolUse；OpenCode 有 plugin），**skill 不硬绑**。
通用做法：在"一轮结束 / 每次写文件后"触发 `check-docs-sync.sh`（非 `--strict`），**只打印提醒、不阻塞**。
宿主钩子更适合轻提醒；**门禁交给 CI / pre-commit**。

## 何时用哪个

> 「查什么」列只做**接线视角的索引**;能力清单的定义以 `references/tooling.md` 为准,这里不复述。

| 脚本 | 查什么 | 误报 | 建议 |
|---|---|---|---|
| `check-docs-sync` | 代码动了但 `docs/` 与 L1 没动 | 极低（纯重构会命中，属例外） | pre-commit / CI 加 `--strict` |
| `check-doc-refs` | 结构类 → 见 `tooling.md` | 低-中 | 先当提醒，**检查结果干净**后加 `--strict`;建议放 **编辑后 / CI(可选) / 收尾**,不挡每次提交 |
| `check-code-refs.py` | 内联代码引用 → 见 `tooling.md` | 低 | 改代码前 + commit;可 `--strict` |
| `run-n2-acceptance.py` | N2 验收命令执行结果;无 manifest 只列不跑 | 取决于项目 | 改代码前 / 批次;`--run` 才执行 |
| `check-consistency.py` | 启发式若干项 → 见 `tooling.md` | 中(启发式) | 只当警告,不进 pre-commit |
| `lint-doc-structure.py` | 结构启发式 → 见 `tooling.md` | 中(启发式) | 只当警告,不进门禁 |

## 记住边界

机器只查**结构性**（动不动、链在不在、字段缺不缺）；**语义对不对**仍靠 teach-back 验证者 + 人 review。
**不要把"检查器过了"当成"文档对了"。**
