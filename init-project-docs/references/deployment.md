# 部署清单（模块 ↔ 项目接口）

> 本文件只回答三件事：谁投什么、投到哪、哪份算原文。
> 规则正文不在本文件；模块边界见 `modules.md`。

## 一、五条权威规则

1. **快照型**（dual-use）：skill 是源，项目是只读快照。项目副本顶部写 `synced-from: <skill 版本 / SHA>`；升级时重拷或 diff，**项目不改这份快照**。
2. **工作副本型**（deploy-only）：项目是工作副本，可编辑；skill 模板是上游默认。升级**不覆盖**项目副本，只提供 diff。
3. **skill-only**：skill 是唯一副本，项目没有。
4. **脚本**：skill 是源，项目是复制品；项目不改脚本，要变体回 skill 侧。
5. **dual-use 路径**：dual-use 文件用**裸文件名**（`lifecycle.md` / `verification.md` / `acceptance.md` / `teach-back-verifier-prompt.md`），两边同名；项目规则书用 `docs-templates/methodology.md`；脚本用 `scripts/`。**不写 `references/`**。

## 二、skill-only（不投）

| 文件 | 用途 |
| --- | --- |
| `SKILL.md` | M0 入口：契约、引用/索引、主线、路由 |
| `references/modules.md` | 模块边界与状态表 |
| `references/setup.md` | M1 建立 |
| `references/authoring.md` | M2 写入 |
| `references/tooling.md` | M6 工具（脚本 + 接线） |
| `references/calibration-guide.md` | 复核校准；只在 skill 侧 |
| `references/glossary.md` | skill 自有术语 |
| `tests/`、`eval/` | skill 维护与自测 |

## 三、快照型（skill 源 + 项目只读）

这 4 份是 M3 / M4 / M5 的 kit。**lifecycle 立即投；其余触发时必投**——项目侧的 `methodology` 已经点名它们，不投就是死链。

| 文件 | 投到 | 触发 |
| --- | --- | --- |
| `references/lifecycle.md` | `docs-templates/lifecycle.md` | **立即**（DoD 自检）/ 演进 / 核对 |
| `references/verification.md` | `docs-templates/verification.md` | 核对 / 版本审计 |
| `references/acceptance.md` | `docs-templates/acceptance.md` | 出现 N2 / 非功能 / 视觉需求 |
| `references/teach-back-verifier-prompt.md` | `docs-templates/teach-back-verifier-prompt.md` | 派复核 |
| `references/deployment.md`（本文件） | 不投 | — |

## 四、工作副本型（项目可编辑）

| 文件 | 投到 | 触发 | 备注 |
| --- | --- | --- | --- |
| `templates/l1-memory.md` | 项目根 `AGENTS.md` / `CLAUDE.md` / … | **立即** | 文件名按模板顶部对照表 |
| `templates/methodology.md` | `docs-templates/methodology.md` | **立即** | 项目规则书；skill 的规则在 `references/` |
| `templates/architecture.md` | `docs-templates/architecture.md` → `docs/architecture.md` | 按需 | L2 |
| `templates/module-doc.md` | `docs-templates/module-doc.md` → `docs/modules/<name>.md` | 按需 | L3 |
| `templates/glossary.md` | `docs-templates/glossary.md` → `docs/glossary.md` | 按需 | 跨模块术语 |
| `templates/core-analysis.md` | `docs-templates/core-analysis.md` → `docs/core-analysis.md` | 按需（先问作者） | L4，可选 |
| `templates/decisions-readme.md` | `docs/decisions/README.md` | 按需 | 决策读法 |
| `templates/adr-template.md` | `docs/decisions/adr-XXX-<短描述>.md` | 按需 | 单条 ADR |

## 五、脚本

| 文件 | 投? | 备注 |
| --- | --- | --- |
| `check-doc-refs.sh` / `.ps1` | **立即** | 核心结构核对 |
| `review-backlog.sh` / `.ps1` | **立即** | 复核 delta，不判定 |
| `run-n2-acceptance.py` | **立即** | N2 验收执行 |
| `_doc_common.py` | **立即** | Python 检查器共享库 |
| `l2-docs.txt` | **立即** | L2 文件名清单 |
| `check-code-refs.py` | 按需 | 项目大量用反引号路径时 |
| `check-consistency.py` | 按需 | 只要高价值警告时 |
| `check-docs-sync` / `lint-doc-structure` | 不投 | 已决移除 |

## 六、项目自建

L1、`docs/`（architecture / modules / glossary / core-analysis / n2-acceptance.json）、`docs/decisions/`、`docs/reviews/`、`docs/archive/`、`docs/experiment/`、`task_plan.md`、`.live`、`.ignore`。
这些由项目自己维护，skill 只在建立时创建骨架，之后不覆盖。

## 七、已删 / 待定

> 下表是**历史名**：原都在 `references/` 下，现已删除或并入；只写文件名，避免被行内路径检查当成活引用。

| 文件 | 原类 | 处置 |
| --- | --- | --- |
| layout.md | skill-only | 由本文件替代 |
| conversation-map.md | skill-only | 已并入 `authoring.md` §五 |
| skill-glossary.md | skill-only | 已恢复为精简版 `glossary.md` |
| temporal-model.md | 快照型 | 已并入 `lifecycle.md` |
| evolution-rules.md | 快照型 | 已并入 `lifecycle.md` |
| review-panel.md | 快照型 | 已并入 `verification.md` |
| verifying-n2.md | 快照型 | 已并入 `acceptance.md` |
| verifying-nonfunctional.md | 快照型 | 已并入 `acceptance.md` |
| wiring.md | skill-only | 已并入 `tooling.md` |
| search-surface.md | skill-only | 机制已内联进 `decisions-readme`；检索面规则已并入 `lifecycle.md` §九（D2 已解决） |
| adr-example.md | 快照型 | 已用 `decisions-readme.md` 的迷你示例替代，不恢复独立文件 |

**升级旧项目：** 投 `lifecycle.md` + `verification.md` + `acceptance.md`；把旧的 `docs-templates/temporal-model.md` / `evolution-rules.md` / `review-panel.md` / `verifying-n2.md` / `verifying-nonfunctional.md` 标 `expired` 或删除（内容已并入 lifecycle / verification / acceptance），并改项目 methodology 里的指针。

**methodology 的边界**：它是**项目的规则书**（工作副本），不是 skill 的规则书；skill 的规则在 `references/`。项目可改，skill 升级不覆盖。
