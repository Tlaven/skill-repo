# 产出文件结构与模板清单

> 本文件是 `SKILL.md`「产出文件结构」的展开。SKILL.md 只留落点;这里放完整目录与模板表。

## 一、产出文件结构

```
./AGENTS.md  (或 ./CLAUDE.md,按宿主)  # L1 主战场 —— Step 2A 立即创建
./docs/                     # 本项目当前维护的文档 —— 对账扫这里(排除 reviews/legacy/archive/templates)
  ├── architecture.md       # L2 —— 进入 L2 讨论时创建
  ├── glossary.md           # 术语表 —— 出现领域名词时创建
  ├── scaffolds/            # 可选:项目自搭的跨领域脚手架(见 essentials skill);L1 用目录规则声明
  ├── modules/<name>.md     # L3 —— 每模块开发前
  ├── core-code.md          # L4 —— 可选:被 ≥2 个工作场景共同加载的核心单元才建;不建时跨模块契约写进 architecture.md 的「架构级约束」
  ├── reviews/              # E5 对账 / 多镜复核产出 —— 首次对账时创建;含 .last-review(复核覆盖的提交);多镜 panel 的 dispatch/outputs 放 docs/reviews/<日期>-<主题>-panel/
  └── decisions/
      ├── README.md         # ADR 索引(由 scripts/adr-index.py 生成) —— 首次记 ADR 时创建
      ├── adr-XXX-*.md      # 现役 / 在议的真实 ADR
      └── archive/          # 被取代 / 弃用的记录(不进索引、不进默认检索)
./scripts/                  # 从 skill 拷入;未拷则 L1 标「scripts: 未接入」,命令按「未复跑」处理
./docs-templates/           # skill 提供的两类件(不是本项目当前维护的文档:对账忽略) —— Step 2A 整套落地
  ├── module-doc.md                   # 待填件:复制到 docs/modules/<name>.md 再填
  ├── adr-template.md                 # 待填件:复制成 adr-XXX-<短描述>.md 再填
  ├── glossary.md                     # 待填件:复制到 docs/glossary.md 再填
  ├── decisions-readme.md             # 待填件:复制到 docs/decisions/README.md 再填
  ├── core-code.md                    # 待填件:复制到 docs/core-code.md 再填
  ├── architecture.md                 # 待填件:按需复制到 docs/architecture.md 再填
  ├── evolution-rules.md              # 就地读件:演化期规则 E1–E7(L1 只留指针)
  ├── temporal-model.md               # 就地读件:三时间轴 / 四类路由 / 当下 DoD
  ├── review-panel.md                 # 就地读件:当下层多镜复核
  ├── verifying-n2.md                 # 就地读件:怎么给 N2 造验收
  ├── verifying-nonfunctional.md      # 就地读件:非功能 / 主观需求怎么造验收
  └── teach-back-verifier-prompt.md   # 就地读件:teach-back 验证者 prompt
```

除 L1 与**整套 `docs-templates/`** 外,`docs/` 下本项目当前维护的文档**全部按需创建**。

> **待填件** = 复制到 `docs/` 后再填写的模板;**就地读件** = 留在 `docs-templates/` 直接引用的规则正文;两者都不是本项目当前维护的文档,对账忽略。

## 二、模板文件清单

| 文件 | 用途 | 何时用 | 落地到(项目内) |
|---|---|---|---|
| `templates/l1-memory.md` | 待填件:L1 记忆文件(三段式 / 4 层 / novelty / 铁律) | **立即**(Step 2A) | 项目根 `<AGENTS.md / CLAUDE.md>` |
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
| `references/calibration-guide.md` | 验证者 / 镜头校准手册 | 改判定措辞或换模型时 | **不落地** |
| `references/wiring.md` | 接线指南(pre-commit / CI / 宿主钩子) | 初始化后接线时 | **不落地** |

## 三、脚本清单

- 对账:`scripts/check-docs-sync.sh/.ps1`、`scripts/check-doc-refs.sh/.ps1`、`scripts/review-backlog.sh/.ps1`
- 新增:`scripts/check-code-refs.py`、`scripts/run-n2-acceptance.py`、`scripts/check-consistency.py`、`scripts/lint-doc-structure.py`、`scripts/adr-index.py`
- 共享:`scripts/_doc_common.py`(5 个 Python 检查器必须同拷)
- 用法与触发见 `references/tooling.md`;接线见 `references/wiring.md`。
