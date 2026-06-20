# Architecture Decision Records (ADR)

本目录记录项目所有重要架构决策。每条 ADR 一个文件,按编号递增。

## 为什么记 ADR

- **决策的"为什么"比"是什么"更重要**——代码能读出做了什么,读不出为什么
- **被拒方案是金矿**——记下"考虑过 X 但拒绝了,因为 Y",防止后续重复踩坑
- **AI 协作的护栏**——AI 不知道历史,会反复提出已经否决的方案;ADR 是唯一挡箭牌

## ADR 格式

每条 ADR 包含五段:

```
# ADR-XXX: [决策标题]

## 状态
proposed / accepted / deprecated / superseded by ADR-YYY

## 背景
为什么需要这个决策?遇到了什么问题?

## 考虑过的方案
列出所有考虑过的方案(包括被拒绝的),每个方案的优缺点

## 选择
选了哪个?为什么?

## 后果
正面 / 负面后果
```

模板见 `adr-000-template.md`。

## 何时记 ADR

- **必记**:架构级决策(技术栈、模块拆分、通信方式、数据模型)
- **必记**:被明确拒绝的方案(这是金矿)
- **必记**:颠覆先前决策的新决策(superseded 关系)
- **不记**:实现细节、命名约定、小重构

**铁律:决策当下就记,事后补 90% 会丢。**

## 命名规则

```
adr-XXX-[短描述].md
```

- `XXX` 是零填充的递增编号(001, 002, ...)
- 短描述用英文 kebab-case(例:`adr-003-use-event-sourcing.md`)

## ADR 索引

<!-- 列出所有 ADR,按编号倒序(最新在上) -->
<!-- 示例:
- [ADR-003: 用事件溯源替代直接 CRUD](adr-003-use-event-sourcing.md) — accepted
- [ADR-002: 模块间用消息队列通信](adr-002-message-queue.md) — superseded by ADR-003
- [ADR-001: 选 PostgreSQL 作为主数据库](adr-001-postgres.md) — accepted
- [ADR-000: 模板文件](adr-000-template.md) — template, not a real decision
-->

- [ADR-000: 模板文件](adr-000-template.md) — template
