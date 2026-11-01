# Architecture Decision Records (ADR)

本目录是**决策工作台**:只放**在议 / 仍在执行链上 / 理由尚未升格**的记录。决策稳定后,把仍成立的理由写进对应的现状文档,**该条 ADR 退役**(移出工作区,git 保留);目录本身和本读法文件留在原处。

每条 ADR 一个文件,按编号递增。

> 触发粒度见 E-4,推翻时的联动义务见 E-3。

## 给 Agent 的读取顺序

1. **先 `ls` 本目录**——主目录里的文件就是在议与在途;退役记录不在工作区,用 `git log -- docs/decisions/` / `git show <sha>:docs/decisions/<file>` 找回。
2. **需要理由 / 被拒方案时**再打开对应记录,打开后**先看 frontmatter 的 `status`**。
3. **`status` 不是 `accepted` / `accepted(修订)` → 不是约束**,只作历史参考。
4. 记录正文是**当时的陈述**（过去时）,不是现状;现状以代码与 `docs/` 下的现状文档为准。
5. 参数取**日期最新的「补充」**——原文 append-only,故意不改。

## ADR 格式

每条 ADR = **frontmatter + 五段**:

```markdown
---
status: accepted
date: 2026-10-24
# 被取代时只改 status: superseded；继任记录写 supersedes: ADR-012
---

# ADR-XXX: [决策标题——祈使句]

## 背景          为什么需要这个决策?把前提写成可判定条件
## 考虑过的方案   列出所有方案(包括被拒绝的),被拒的写「拒绝理由」
## 选择          选了哪个?为什么(不是"它最好",而是"在我们的约束下最合适")
## 后果          正面 / 负面后果;需要跟进的
```

- **状态取值:** `proposed` / `accepted` / `accepted(修订)` / `rejected` / `superseded` / `expired`。被取代时旧记录只改 `status: superseded`;继任记录写 `supersedes: ADR-XXX`。`expired` = 前提**有证据地**消失、没有继任决定。**两者都退役**;`expired` 不是退役候选。**弃用某条决定而没有继任决定 → 记 `expired`,理由写进正文**。
- **关系字段:** 继任记录声明**正向链接** `supersedes` / `revises` / `extends`;现役记录之间仍只声明一次。
- **句式:** 写「当时决定用 X（约束：…）」,不写「本项目使用 X」。
- **可选第六段「修订 / 补充」(append-only):** 同一决策内的修正用带日期的补充追加在文末,不改原文、不新建 ADR;换掉被选方案本身 → 新 ADR（`superseded`）。
- **长度:** 超过 800 词会被警告。

模板见 `docs-templates/adr-template.md`;填好的完整示例见 `docs-templates/adr-example.md`。

## 命名规则

```
adr-XXX-[短描述].md
```

- `XXX` 是零填充的递增编号(001, 002, ...);编号不复用,删掉的也不回收。
- 短描述用英文 kebab-case(例:`adr-003-use-event-sourcing`)。
- 文件名编号必须与标题里的 ID 一致（`adr-003-*.md` ↔ `# ADR-003:`）。

## 不做索引

**主目录即名单**:`ls` 就是工作台的清单;退役记录在 git 里,用 `git log -- docs/decisions/` 看。不维护 README 里的清单块,也不手写索引。

## 退役

记录不再约束当下时**移出工作区**:

```
docs/decisions/
├── README.md          # 读法(本文件)
└── adr-001-...md      # 在议 / 在途
```

- **git 保留**:`git log -- docs/decisions/` 看名单,`git show <sha>:docs/decisions/<file>` 取回。
- **退役前**:按 E-4「记录寿命」——退役要有正面证据(理由已升格 / 前提可证伪地消失 / 作者拍板);**"答不出"只登记退役候选、不改 `status`**,交作者。继任记录写 `supersedes: ADR-XXX`;在对账记录里留一行处置证据。
- **非 git 项目不退役**:确认前提消失后标 `expired` 留在原处(读的时候按 `status` 跳过),靠 `docs/.ignore` 退出检索面;没有恢复手段。

**整个 `docs/decisions/` 默认退出关键词检索面。** `docs/.ignore` 排掉整个目录组:

```
decisions/
reviews/
archive/
experiment/
```

- **入口不在搜索,在目录**:问"有哪些决策"就 `ls` 本目录——这条路不受 `.ignore` 影响。
- 考古:`rg --no-ignore 关键词`,或直接 `rg 关键词 docs/decisions`(指定目录时父级 `.ignore` 不生效)。
- **已知的洞:** `git grep` 不认 `.ignore`,也没有排除开关;IDE 全局搜索要各自配 `search.exclude`。
