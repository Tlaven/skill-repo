# ADR 示例（填好的真实记录）

> **这是一条示例，不是本项目的决策。** 读它是为了知道各段该填成什么样；不要把它复制进 `docs/decisions/`，也不要列进索引。
>
> 来源：system-analyzer 项目 v0.9。示例按**旧格式**（状态写在 `## 状态` 段）给出，便于对照历史记录；新记录的状态与关系写在 frontmatter，见 `adr-template.md`。

```markdown
# ADR-007: 边模型从 class 级迁到实例级

## 状态
accepted

## 背景
v0.8 边通过 class.edges 静态字面量声明 + attrs 里的 null 引用槽实现。
问题:
- 多对一/多对多/同目标多边表达困难(class.edges 是 class 共享,实例无法独立声明)
- attrs 里的 null 槽是"占位待填"的隐式契约,scanner 要特殊处理,容易踩坑
- "边"和"属性"概念混淆,attrs 既有数据属性又有 edges 占位

## 考虑过的方案

### 方案 A: 保持 class.edges,加 instance.edges override(被拒)
- 优点:向后兼容
- 缺点:两套机制并存,scanner 必须处理两层覆盖,概念复杂度爆炸
- **拒绝理由**:违反"统一模型优先",两套机制必然有边界情况

### 方案 B: 引入独立的 Edge 类(被拒)
- 优点:类型清晰,OO 风格
- 缺点:用户写启动代码时要 new Edge(src, tgt),对 DSL 不友好
- **拒绝理由**:破坏 v0.9 "声明式 sourceCode"的体感,显式构造器是噪音

### 方案 C: 边作为实例级 attrs.edges 数组(采纳)
- 优点:概念归一(边就是 attrs 里的一个数组字段),天然支持任意多条
- 缺点:scanner 要从 attrs 里过滤掉 edges 键,不当作数据属性
- 适合场景:声明式 sourceCode + 实例级 mutable model

## 选择
选方案 C。理由:
1. 概念统一——边和属性都是实例 attrs 的字段,只是语义不同
2. 多边天然支持——数组结构,任意条数
3. `GraphStarter.add()` 返回 attrs 代理,`X.edges = [{target: Y, ...}]` 是原生 JS 赋值,无需额外抽象

取舍:为了概念统一,放弃了对旧 v0.8 数据的兼容(load 时硬切换,旧 sa_data 直接丢弃)。

## 后果

### 正面后果
- 多边表达自然,任意 source-target-idx 组合都支持
- scanner 简化(只扫实例 attrs 三个字段,不再扫 static/constructor/class.edges)
- 边 id = `<srcVar>><tgtVar>>idx`,天然区分同对多边

### 负面后果
- v0.8 及之前的项目数据无法迁移(version !== 6 直接丢弃)
- 文档/CLAUDE.md 要大改(从 class 模型迁到实例模型)

### 需要跟进的
- 旧文档(docs/node-interaction-redesign.md)标注"已被 v0.9 部分取代"
- bootstrap 教学示例重写
```
