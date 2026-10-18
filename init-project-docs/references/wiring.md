# 把检查器接上（pre-commit / CI / 宿主钩子）

> 目的：让 L1 铁律里标 `[机器]` 的规则**真的会触发**，而不是停在脚本里等人手动跑。
> 两个检查器脚本（Windows 用同名 `.ps1`）：
> - `scripts/check-docs-sync.sh` —— 代码动了但本项目当前维护的文档(`docs/` 除 `docs/reviews/` 对账留档——历史快照不算同步)与 L1 记忆文件都没动 → 提醒。
> - `scripts/check-doc-refs.sh` —— `docs/` 里的死链(含大小写错链)、未填占位符、标了 N2 却缺 `**验收**`、危险清单行缺"挡住者"、活文档引记录。
>
> 另有 `scripts/review-backlog` —— **辅助脚本,不属于本页的接线面**:不判定、不拦截(退出码恒 0),复核前手动跑,列出"自上次复核以来的契约 delta"。不上 pre-commit / CI。

## 先拷进项目

把 `scripts/` 拷进项目（如 `<repo>/scripts/`），并按项目改 `check-docs-sync.sh` 顶部的三行路径：

> 脚本里 `CODE_GLOB` 默认是**扩展名式**（形如 `\.(js|ts|py|...)$`，适配代码散落或在根目录的项目）；若代码集中在少数目录，改成下面的**目录式**更准。

```bash
CODE_GLOB='^(src|lib|app|packages)/'
DOC_GLOB='^docs/'
L1_FILES='AGENTS.md CLAUDE.md .cursorrules .cursor/rules/project.mdc .windsurfrules .github/copilot-instructions.md'
```

> `check-doc-refs.sh` 顶部另有两项:`DOC_EXT`(文档扩展名,默认 `.md` + `.markdown`)与 `DOC_EXCLUDE`(对账要**排除**的路径,默认排除 `docs/legacy/`、`docs/archive/` 等**考古 / 存档层**、`docs/reviews/` **对账留档**(历史快照,引用退役术语/旧链是常态)、以及 `docs/templates/` 等**模板 stub 目录**——它们不是本项目当前维护的文档,扫进来只会制造噪音)。

> **Windows 必读——先把换行符定死（否则脚本根本跑不起来）。**
> Windows 默认 `core.autocrlf=true`，拷进项目的 `.sh` 会被检出成 CRLF，bash 会以 `$'\r': command not found` 语法错直接拒绝执行；若已接 pre-commit，会挡住**每一次**提交，报错还像"hook 坏了"——很容易被整个删掉。落地一行防住（`.gitattributes` 不存在就新建，存在就追加）：
>
> ```bash
> printf '*.sh text eol=lf\n' >> .gitattributes
> ```
>
> `.ps1` 用 Windows 换行、不受影响，无需处理。

## 接入前先对齐约定（否则别接）

`check-doc-refs` 认的是**当前 skill 的三条约定**:

- N2 条目用**字面量** `novelty=N2` 标记;
- 每个 N2 配一个独立一行 `**验收**:…`;
- 危险实现清单每行的"由谁挡住"要有内容,且是编号(`I-2` / `Q-1`)或"验收 / 不变量"字样。

**"N2 缺验收"只做次数粗检**（`novelty=N2` 计数 > `**验收**` 计数才报；`**验收**` 写在行内也算数），逐条配对不对仍归复核。
**危险清单只做行级形式粗检**（列非空 + 形如编号 / 验收 / 不变量）——挡不挡得住仍归复核。

(写法见 `docs-templates/module-doc.md` / `docs/core-code.md`——后者按需从 skill 的 `templates/core-code.md` 落地。)

> **扫哪些文件:** `docs/core-code.md`、`docs/architecture.md`、`docs/modules/*`。
> N2 落在 **L2 的公共节**(跨模块契约、未建 L4 时的家)也算——那里标了 `novelty=N2` 就得配 `**验收**:`。
> 项目 L2 用了别的文件名 → 把名字加进脚本顶部**两张表**(N2 扫描表与 `LIVE_DOCS`,都有"按项目改"标注),否则对应检查对它空跑。

若项目用的是**别的写法**——典型是**早期版本**的 L1(只有"N2 必须给步骤 / 例子 / 验收"这样的**文字规则**,文档里没有 `novelty=N2` 标记)——直接接上会:

- **漏报**:没有 `novelty=N2` 字面量 → 对账永远看不到 N2 条目,这道门禁形同虚设;
- **噪音**:`DOC_EXT` / `DOC_EXCLUDE` 没调好时,不该扫的文件(模板 stub / 考古层)被当成对账对象扫。

**对策(二选一):**

1. 先把项目对齐到当前约定(用 `docs-templates/` 里的模板);或
2. **只接 `check-docs-sync`**——它只查"代码动没动、文档动没动",**与约定无关**,任何项目都能接;`check-doc-refs` 等约定对齐了再上。

## 方式 A：pre-commit（最省事）

`.git/hooks/pre-commit`（记得 `chmod +x`）：

```bash
#!/usr/bin/env bash
bash scripts/check-docs-sync.sh --staged --strict || {
  echo "改代码但没同步文档。要跳过：git commit --no-verify"; exit 1; }
bash scripts/check-doc-refs.sh
```

或写进 [pre-commit 框架] 的 `.pre-commit-config.yaml`，便于团队分发。

> 建议 `check-docs-sync` 用 `--strict`（它是"动不动"检查，误报极低——纯重构提交只改代码、不碰文档时会命中，属已知例外，用 `git commit --no-verify` 放行）；`check-doc-refs` 初期先不加 `--strict`，当提醒用，等基线干净了再收紧。

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

| 脚本 | 查什么 | 误报 | 建议 |
|---|---|---|---|
| `check-docs-sync` | 代码动了但 `docs/` 与 L1 没动 | 极低（纯重构会命中，属例外） | pre-commit / CI 加 `--strict` |
| `check-doc-refs` | 死链(含大小写错链) / 未填占位符 / N2 缺 `**验收**` / 危险清单缺"挡住者" / 活文档引记录 | 低-中 | 先当提醒，基线干净后加 `--strict` |

## 记住边界

机器只查**结构性**（动不动、链在不在、字段缺不缺）；**语义对不对**仍靠 teach-back 验证者 + 人 review。
**不要把"检查器过了"当成"文档对了"。**
