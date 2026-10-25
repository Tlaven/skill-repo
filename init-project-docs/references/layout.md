# 产出文件结构与模板清单

> 本文件是 `SKILL.md`「产出文件结构」的展开。SKILL.md 只留落点;这里放完整目录与模板表。

## 一、产出文件结构

```
./AGENTS.md  (或 ./CLAUDE.md,按宿主)  # L1:项目记忆,只指活文档
./task_plan.md                  # 未来桶:唯一待办
./docs/
  ├── .live                    # 活文档白名单(一行一个路径,相对 docs/)
  ├── .ignore                  # 让 decisions/、reviews/、archive/、experiment/ 退出 rg
  ├── architecture.md          # L2:模块图 / 主流程 / 坐标,≤80 行
  ├── design-contract.md       # 设计约束(若有),≤100 行
  ├── glossary.md              # 跨模块术语,2 列,≤40 词
  ├── modules/<name>.md        # L3:N1 一页 / N2 五件套
  ├── core-code.md             # 跨模块 N2 的家(需要时才建)
  ├── reviews/                 # 历史:对账 / 复核
  ├── decisions/               # 历史:ADR
  ├── archive/                 # 历史:退役文档(文件名带日期)
  └── experiment/              # 实验:scaffolds / experiment-log,不进开发入口
./scripts/                  # 从 skill 拷入;未拷则 L1 标「scripts: 未接入」,命令按「未复跑」处理
./docs-templates/           # 协议 / 模板(不是本项目当前维护的文档:对账忽略)
  ├── methodology.md                 # 协议正文(不自动加载;L1 只留指针)
  ├── module-doc.md                  # 待填件:复制到 docs/modules/<name>.md 再填
  ├── adr-template.md                # 待填件:复制成 adr-XXX-<短描述>.md 再填
  ├── glossary.md                    # 待填件:复制到 docs/glossary.md 再填
  ├── decisions-readme.md            # 待填件:复制到 docs/decisions/README.md 再填
  ├── core-code.md                   # 待填件:复制到 docs/core-code.md 再填
  ├── architecture.md                # 待填件:按需复制到 docs/architecture.md 再填
  ├── evolution-rules.md             # 就地读件:E1–E7(项目 L1 只留指针)
  ├── temporal-model.md              # 就地读件:三时间轴 / 四类路由 / 当下 DoD
  ├── review-panel.md                # 就地读件:当下层多镜复核
  ├── verifying-n2.md                # 就地读件:怎么给 N2 造验收
  ├── verifying-nonfunctional.md     # 就地读件:非功能 / 主观需求怎么造验收
  └── teach-back-verifier-prompt.md  # 就地读件:teach-back 验证者 prompt
```

除 L1、`task_plan.md` 与**当前用到的 `docs-templates/`** 外,`docs/` 下当前维护的文档**全部按需创建**;`docs/.live` 是唯一活文档清单。

> **待填件** = 复制到 `docs/` 后再填写的模板;**就地读件** = 留在 `docs-templates/` 直接引用的规则正文;两者都不是本项目当前维护的文档,对账忽略。

## 二、模板文件清单

| 文件 | 用途 | 何时用 | 落地到(项目内) |
|---|---|---|---|
| `templates/l1-memory.md` | 待填件:L1 记忆文件(项目记忆;方法论只留指针) | **立即**(Step 2A) | 项目根 `<AGENTS.md / CLAUDE.md>` |
| `templates/methodology.md` | 就地读件:三段式 / 4 层 / novelty / 铁律 / 加载表(不自动加载) | **立即**(Step 2A) | `docs-templates/methodology.md` |
| `templates/architecture.md` | 待填件:L2 架构层 | **立即**(Step 2A) | `docs-templates/architecture.md`(按需复制到 `docs/architecture.md`) |
| `templates/module-doc.md` | 待填件:L3 模块详细(含 novelty 标记) | **立即**(Step 2A) | `docs-templates/module-doc.md` |
| `templates/glossary.md` | 待填件:术语表(受控词汇) | **立即**(Step 2A) | `docs-templates/glossary.md`(按需复制到 `docs/glossary.md`) |
| `templates/core-code.md` | 待填件:L4 核心代码(含 novelty 分档 / N2 附加栏) | **立即**(Step 2A) | `docs-templates/core-code.md`(按需复制到 `docs/core-code.md`) |
| `templates/decisions-readme.md` | 待填件:ADR 索引 + 格式约定 | **立即**(Step 2A) | `docs-templates/decisions-readme.md` |
| `templates/adr-template.md` | 待填件:单条 ADR 模板(frontmatter 状态 / 关系) | **立即**(Step 2A) | `docs-templates/adr-template.md` |
| `references/adr-example.md` | 就地读件:填好的 ADR 示例(**不是决策**) | 写 ADR 时 | `docs-templates/adr-example.md` |
| `references/evolution-rules.md` | 就地读件:E1–E7 | **立即**(Step 2A) | `docs-templates/evolution-rules.md` |
| `references/temporal-model.md` | 就地读件:三时间轴 / 四类路由 / 当下 DoD | **立即**(Step 2A) | `docs-templates/temporal-model.md` |
| `references/review-panel.md` | 就地读件:多镜复核(镜头 / 触发 / 回路) | **立即**(Step 2A) | `docs-templates/review-panel.md` |
| `references/verifying-n2.md` | 就地读件:N2 验收手段 / 反模式 | **立即**(Step 2A) | `docs-templates/verifying-n2.md` |
| `references/verifying-nonfunctional.md` | 就地读件:非功能 / 主观需求怎么造验收 | **立即**(Step 2A) | `docs-templates/verifying-nonfunctional.md` |
| `references/teach-back-verifier-prompt.md` | 就地读件:teach-back 验证者 prompt | **立即**(Step 2A) | `docs-templates/teach-back-verifier-prompt.md` |
| `references/conversation-map.md` | 对话地图(问题清单) | skill 侧使用 | **不落地** |
| `references/skill-glossary.md` | skill 自有术语表(历史 / 当下 / 未来、契约、对账 / 复核等) | skill 侧使用 | **不落地** |
| `references/tooling.md` | 工具矩阵 / 用法 / 触发 | skill 侧使用 | **不落地** |
| `references/search-surface.md` | 检索面:为什么历史会被 grep 撞见、`.ignore` 怎么放、边界与残留 | 建 ADR 目录 / 发现 Agent 引用了废决策时 | **不落地**(机制已内联进 `decisions-readme` 模板) |
| `references/calibration-guide.md` | 验证者 / 镜头校准手册 | 改判定措辞或换模型时 | **不落地** |
| `references/wiring.md` | 接线指南(pre-commit / CI / 宿主钩子) | 初始化后接线时 | **不落地** |

## 三、活文档白名单 `docs/.live`

- 一行一个路径，相对 `docs/`；`#` 注释、空行忽略。
- 只有列出的文档算“当前”；未列出的按历史 / 参考处理，不进日常加载。
- Python 检查器默认只扫白名单 + L1；`check-consistency --all-docs` 才扫全库（迁移 / 对账用）。`check-doc-refs` 仍按目录排除（archive / experiment / decisions / reviews / templates 不扫）。
- 新增活文档必须合并 / 替换 / 归档一个（net-negative）。

```text
# docs/.live
design-contract.md
architecture.md
modules/run.md
```

## 四、脚本清单

- 对账:`scripts/check-docs-sync.sh/.ps1`、`scripts/check-doc-refs.sh/.ps1`、`scripts/review-backlog.sh/.ps1`
- 新增:`scripts/check-code-refs.py`、`scripts/run-n2-acceptance.py`、`scripts/check-consistency.py`、`scripts/lint-doc-structure.py`、`scripts/adr-index.py`
- 共享:`scripts/_doc_common.py`(5 个 Python 检查器必须同拷)
- 用法与触发见 `references/tooling.md`;接线见 `references/wiring.md`。
