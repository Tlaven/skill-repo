# 模块地图

> 本文件定义 skill 的模块边界与状态表。**不写规则正文**；每条规则的正文只在所属模块。
> 读法：§一 看 7 个模块；§二 看边界纪律；§三 看 M0 的四节；§四 看模块状态。

## 一、7 个模块

`kit` = 投进目标项目的那份文件。快照型 / 工作副本型的区分见 `deployment.md`。

| 模块 | job | 读的时机 | 正文 | kit | 不写 |
| --- | --- | --- | --- | --- | --- |
| **M0 入口/契约** | 何时用/不用、作者边界、硬约束、引用/索引、五段主线、路由 | 每次 | `SKILL.md` + `glossary.md`（已建） | 无 | 模块规则、模板、脚本 |
| **M1 建立** | 判起点、最小骨架、按清单投、首轮收尾、建立出口 | 开项 / 重建 / 2B–2D 补差 | `setup.md`（已建） | 全部 kit 的投放动作（清单归 `deployment.md`） | 层/深度、验收、复核、模板内容 |
| **M2 写入** | 访谈、三段式、L1–L4、N0–N2、五件套、一处成文 | 写文档 | `authoring.md`（已建） | L1 / architecture / module / glossary / core-analysis 模板 | 验收造法、记录寿命、复核触发、脚本 |
| **M3 维护** | 三时间桶、四类路由、E-1–E-7、记录寿命、术语退役、DoD | 改文档 / 定期 | `lifecycle.md`（已建） | `lifecycle.md`（快照）+ decisions / adr 模板 | E-5 执行、层/深度、复核流程、脚本 |
| **M4 验收** | 五种手段、非功能四步、视觉双测、审美兜底、反模式、两道闸门 | 定 N2 / 非功能 | `acceptance.md`（已建） | `acceptance`（快照） | 五件套结构、复核流程、脚本执行 |
| **M5 复核/核对** | 四信号、档位、teach-back、校准、E-5 执行、记录退役 | 改代码前 / 版本审计 | `verification.md`（已建：复核 + 核对） | `verification`、`teach-back-prompt`（快照）；calibration 不投 | 验收造法、记录寿命、脚本内部 |
| **M6 工具** | 脚本清单、接线、证据状态、改动纪律 | 接线 / 跑检查 | `tooling.md`（已建） | 核心 + 可选脚本、`l2-docs.txt`、`_doc_common.py` | 文档内容规则、验收语义、复核判定 |
| **— deployment** | 模块↔项目接口：谁投什么、投到哪、哪份算原文 | 建立 / 升级 | `deployment.md`（已建） | —（它就是清单） | 规则正文 |

## 二、边界纪律

1. 一条规则一个正文模块；别处只写一句指针。
2. 模块只写自己的 job：M1 不解释层级，M2 不解释记录寿命，M4 不解释复核。
3. 入口只做三件事：契约、引用/索引、主线/路由。
4. **E-5**：执行正文在 M5；M3 只留「E-5 是跨时间核对，执行见 `verification.md`」一句。
5. **验收**：造法在 M4；M2 只留「N2 必须有可跑验收」。
6. **投放**：清单在 `deployment.md`；M1 只写「按清单投」。
7. **cross-doc 不单列**：核心进 M0 §0.2，长尾例子进 M2 或附录。
8. **模板内容**归使用它的模块；M1 只负责「何时投」。

## 三、M0 的四节

### 0.1 契约

产出 / 不适用 / 作者边界 / 硬约束。正文在 `SKILL.md`。

### 0.2 引用与索引

索引上指下 / 引用下指上 / 代号 / 同侧引用 / 目录 vs 条款。正文在 `SKILL.md`。

### 0.3 五段主线

建立 → 写入 → 复核 → 交付 → 收尾。正文在 `SKILL.md`。

### 0.4 路由

见 `SKILL.md` 的表。

## 四、模块状态

| 目标 | 现在在哪 | 动作 | 状态 |
| --- | --- | --- | --- |
| M0 | `SKILL.md`（已重写）+ `references/glossary.md` | 保持 | **已建** |
| M1 | `references/setup.md` | 保持；`layout` 已由 `deployment.md` 替代 | **已建** |
| M2 | `references/authoring.md` | 保持 | **已建** |
| M3 | `references/lifecycle.md` | 保持 | **已建** |
| M4 | `references/acceptance.md` | 保持 | **已建** |
| M5 | `references/verification.md`（复核 + 核对）+ `references/teach-back-verifier-prompt.md`（prompt） | 保持 | **已建** |
| M6 | `references/tooling.md` | 保持 | **已建** |
| deployment | `references/deployment.md` | 保持 | **已建** |

## 五、已解决

- **D2**：检索面规则已在 `lifecycle.md` §九（`.ignore` 只影响 rg；退役才挡 `git grep`）。
- **D3**：ADR 示例已用 `decisions-readme.md` 的迷你示例，不恢复独立文件。
