---
name: seeding-skills
description: "Use when creating a new skill, transforming an existing skill into seeding format, or auditing a seeding skill. TRIGGER: seeding, compound word, atom vocabulary, build skill, create skill, transform skill, audit skill, seeding-skill, 做skill, 写skill, 构建skill, 改造skill."
---

# Seeding Skills — 不给命令，给种子

## 范式

传统 skill 给 agent 一本命令手册。Seeding skill 给 agent 三样东西：

1. **原子词表** — 最小语义单元，三类：动作、对象、定位
2. **底层库** — 可 import 的函数，接口清晰
3. **组合示例** — 2-3 个示例，展示原子如何组合

Agent 遇到需求 → 组合复合词 → 查找已有实现 → 没有则自实现（import 库写代码）→ 记录 → 下次复用。

---

## 原子词表

每个 seeding skill 根据自己的领域定义原子。原子分三类，但具体内容因领域而异。

**三类原子**：
- **动作** — 表示操作。文档类举例：replace, insert, delete, get, set。API 类举例：send, fetch, poll, authenticate。数据处理举例：filter, aggregate, transform, join。
- **对象** — 领域实体。文档类举例：paragraph, section, table。项目管理举例：task, milestone, assignee。数据库举例：row, column, table, index。
- **定位** — 指定操作目标的策略。举例：text, title, index, style, after, before, first, last, all, range, inside。

原子对应领域实体模型，从领域操作中提取，不是凭空列举。每类控制在 20 个以内。

---

## 组合规则

**没有固定顺序。** 复合词是 LLM 给自己写的函数名——从词表里选原子，用 `-` 连起来，任何排列都合法。LLM 能理解每个原子的语义角色（哪个是动作、哪个是对象），不靠位置判断。

以下都是同一个操作，全都正确：

```
section-content-replace-text
replace-section-content-text
text-replace-content-section
```

唯一要求：原子来自词表，语义明确。每个原子是一个不含 `-` 的单词。

参数不嵌入复合词，自然地跟在后面：

```
section-content-replace-text anchor="3.2" old="图6-" new="图3-"
replace-paragraph-after anchor="实验方法" content="我们采用了X方法"
```

**`-` 只是视觉连接符**，没有语法意义。复合词不是被机器解析的 token，是 LLM 写给自己的语义标签。LLM 看到自己之前存的代码就认得，不需要字符串精确匹配。

---

## 边界

**能拆才拆，不能拆就不拆。**

| 类型 | 判断标准 | 举例 |
|------|---------|------|
| 复合词 | 单步操作，能用词表原子拼出 | section-content-replace |
| 单一词 | 跨对象/全局操作，拆了反而不清 | export-markdown, renumber-figures |
| 脚本 | 多步编排，需要条件/循环/顺序 | "先删空段落再重编号" |

一个操作需要很多修饰词才能说明白 → 不适合复合词 → 单一词或写脚本。

---

## 自实现循环

```
Agent 识别需求
→ 组合复合词（如 paragraph-insert-after）
→ 检查是否有已记录的实现
→ 没有 → import 底层库 + 写调用代码 → 执行
→ 记录实现（复合词 → 代码片段）
→ 下次遇到同名复合词，直接复用
```

这是**信号驱动演进**：频繁使用的复合词实现被固化 → 变成 skill 能力的一部分。

---

## 歧义消解

复合词可能有歧义。靠对象层级消解：

```
paragraph-delete-text    → 删整个段落（paragraph 是顶层对象）
content-replace-text     → 改段落中的文字（content 是段落属性）
```

对象粒度分清楚，歧义自然消解。`paragraph` 是独立对象，`content` 是对象的属性。

---

## 错误处理

不追求一次正确。LLM 会犯错是既定事实。

关键是**犯错后有正向反馈**：
- 错误信息 → agent 理解为什么错 → 修正组合或参数 → 更新记录
- 不追求防呆，追求快速修正

---

## Workflow 1: Create — 从零构建 seeding skill

### 步骤

1. **识别领域实体模型** — 列出领域操作的所有对象类型。这些成为对象原子。
2. **识别操作** — 分为 CRUD 类（→ 动作原子）和领域特有操作（→ 动作原子或单一词）。
3. **识别定位方式** — 用户怎么指定操作对象？按文本、按标题、按索引、位置关系？→ 定位原子。
4. **写原子词表** — 三列表格：类别 | 原子 | 语义说明。每类 ≤ 20。
5. **准备底层库** — 为每个对象类型提供基本操作函数。签名清晰。
6. **写 2-3 个组合示例** — 每个示例：复合词 → 原子分解 → 含义 → 自实现代码思路。
7. **写 SKILL.md** — 模板见下。

### SKILL.md 模板

```markdown
---
name: <skill-name>
description: "<一句话能力描述>. TRIGGER: <触发关键词>"
---

# <Skill 名称>

## 定位
一句话说明这个 skill 做什么。

## 原子词表

| 类别 | 原子 | 说明 |
|------|------|------|
| 动作 | replace, insert, delete, ... | ... |
| 对象 | paragraph, section, table, ... | ... |
| 定位 | text, title, after, ... | ... |

## 组合规则

无固定顺序。从词表选原子，`-` 连接，任何排列都合法。

## 示例

### section-content-replace-text
- 原子：section, content, replace, text
- 含义：按文本匹配找到节，替换其正文内容
- 自实现思路：import <库>; 找到匹配节; 替换 content

### insert-paragraph-after
- 原子：paragraph, insert, after
- 含义：在指定段落后插入新段落
- 自实现思路：import <库>; 定位锚点段落; 在其后插入

## 底层库

路径：<库文件路径>
关键函数签名：<列出>

## 边界

- 复合词范围：<能组合的操作>
- 单一词：<不可分解的操作列表>
- 需写脚本：<多步操作列表>
```

---

## Workflow 2: Transform — 改造现有 skill

### 步骤

1. **清点命令** — 列出源 skill 的所有命令/工具。

2. **分解** — 把每个命令名按 `-` 拆开，将片段分类为动作/对象/定位。

3. **分类** — 每个命令归入三桶：
   - **可组合**（能用词表原子拼出）→ 复合词
   - **不可分解**（跨对象/全局操作）→ 单一词
   - **多步编排**（需要条件/循环）→ 脚本

4. **提取原子词表** — 跨命令去重片段。目标：~10-15 动作原子，~10-15 对象原子，~5-10 定位原子。

5. **映射参数到定位** — 命令的 `--by-text`、`--after`、`--chapter` 等参数 → 定位原子。

6. **识别底层库** — 源 skill 的内部函数（`lib/` 目录、类方法）就是库。记录签名。

7. **按 Create 模板写新 SKILL.md。**

8. **验证** — 选 5 个原命令，写出复合词等价物，确认 agent 能从库自实现。

---

## Workflow 3: Audit — 审查 seeding skill 质量

逐项检查目标 skill 的 SKILL.md：

### 原子质量

- [ ] 原子边界清晰？（没有原子本身是短语或复合体）
- [ ] 每个原子在领域内语义无歧义？
- [ ] 原子总数有界？（每类 ≤ 20）
- [ ] 原子对应实体模型，非随意列举？

### 组合规则

- [ ] 组合规则是否说明了"无固定顺序"？
- [ ] 原子选自词表，语义明确？
- [ ] 有歧义消解规则？（对象层级消歧）
- [ ] 单一词例外已列出？

### 底层库

- [ ] 库函数覆盖原子隐含的所有基本操作？
- [ ] 函数签名清晰（参数、返回值）？
- [ ] 有兜底机制处理库未覆盖的操作？

### 边界纪律

- [ ] 不适合复合词的操作被明确分类为单一词或脚本？
- [ ] 复合词与脚本的边界有清晰说明？
- [ ] 没有多步工作流被伪装成复合词？

### 实用性

- [ ] 不了解范式的 agent 能仅凭 SKILL.md 理解？
- [ ] 至少 2 个组合示例？
- [ ] 自实现循环有描述？

**评分**：0-2 项不通过 → 健康。3-5 项 → 需修订。6+ 项 → 需重新设计。

---

## Skill 编写通用要点

以下适用于所有 skill，不分范式。

### description 写法

- 用第三人称（"Processes PDF files" 而非 "I can help you process PDFs"）
- 包含两个信息：做什么 + 什么时候触发
- 写具体的触发关键词，不要写空泛的 "helps with documents"

```
# 好
description: "Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction."

# 差
description: "Helps with documents"
```

### name 写法

- 全小写，只用字母、数字、`-`
- 不超过 64 字符
- 用动名词（verb + -ing）或名词短语：`processing-pdfs`、`pdf-processing`
- 避免空泛名字：`helper`、`utils`、`tools`

### 简洁原则

- context window 是公共资源，skill 跟对话历史、其他 skill 共享
- 只写 agent 不知道的信息。每一段都问：这占的 token 值得吗？
- SKILL.md 正文控制在 500 行以内。超了就拆到单独文件，SKILL.md 里链接过去
- 引用文件保持一层深度，不要 SKILL.md → ref1.md → ref2.md 的链式引用

### 自由度匹配

根据任务的脆弱性设定自由度：

- **高自由**（文字指令）：多种做法都行、决策依赖上下文。如代码审查。
- **中自由**（伪代码/带参数的脚本）：有推荐模式但允许变化。
- **低自由**（精确脚本）：操作脆弱、必须精确执行。如数据库迁移。不要加 `--no-verify` 之类的额外 flag。

### 反馈循环

复杂操作要有 validate → fix → repeat 循环。不要让 agent 一步到位——让它在中间步骤检查结果，发现错误及时修正。

### 脚本相关

- 脚本要解决问题，不要把问题抛回给 agent（不要写 `return open(path).read()` 然后期望 agent 处理 FileNotFound）
- 配置参数要有理由（不要写 `TIMEOUT = 47` 而不解释为什么是 47）
- 路径一律用正斜杠 `/`，不用 `\`
- 列出依赖包

### 测试

- 写 skill 之前先建评估。先跑 agent 不带 skill 看它哪里失败，再针对性写
- 用一个 agent 实例写 skill，另一个实例测 skill，观察行为后回来改
- 在你计划使用的模型上都测一遍。强模型不需要过度解释，弱模型需要更多细节

---

## 参考

无。
