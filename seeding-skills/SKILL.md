---
name: seeding-skills
description: "Skill design guide built on the seeding paradigm: skills are seeds that grow through practice. Covers dual philosophy (static navigation + dynamic evolution), what to write vs not write, structure template, evolution workflow, and audit checklist. Use when creating, refactoring, or auditing a Claude Code skill. TRIGGER: build skill, create skill, design skill, refactor skill, audit skill, 做skill, 写skill, 构建skill, 改造skill, skill设计, skill审查, evolve skill"
---

# Seeding Skills — 在实践中生长的 skill

## 核心哲学(双维度)

**skill 是一颗在实践中生长的种子。**

从两个维度理解:

**静态维度:skill 是给 agent 加速的导航。** agent 有完整 context、能读代码、能写脚本——它不需要被"封装"。它需要的是:它不知道的领域知识 + 真实工具的入口 + 防踩坑的护栏。

**动态维度:skill 是从小开始、在复盘中演化的种子。** 一次性写完美的 skill 不存在。skill 的价值在于:**给 agent 一个可用的起点,让 agent 的实际使用反过来塑造 skill**。高频路径被固化为库函数,常见错误沉淀为约束规则,文档膨胀后拆分文件。

**seeding 范式的核心不是任何具体的实现技巧,而是这种"种子—生长"的工作方式。** 早期的"原子词表 + 复合词组合"尝试是种子的一种形式,但被实践证明无效——agent 会绕过抽象层直接调真实 API。实现可以变,核心范式不变。

---

## Skill 文件格式与加载机制

### 必需的文件结构

每个 skill 必须是一个独立目录,内含 `SKILL.md` 主入口:

```
<skill-name>/
├── SKILL.md          # 必需,主入口
└── (辅助文件按需)
```

### SKILL.md 的 frontmatter(必需)

每个 SKILL.md 必须以 yaml frontmatter 开头:

```yaml
---
name: <skill-name>                                      # 必需
description: "<做什么>. TRIGGER: <触发关键词>"            # 必需
---
```

字段规则:

- `name`:全小写,只用字母 / 数字 / `-`,≤ 64 字符。**必须和目录名一致**(否则加载机制找不到)。
- `description`:agent 判断"何时加载"的**唯一依据**。必须包含两类信息:做什么 + 何时触发(具体关键词)。

### description 的加载机制(关键)

Claude Code 启动时:

1. 扫描所有 skill 目录,**只读 frontmatter 的 description 字段**
2. 所有 description 进入 agent 的常驻 context(每个 skill 占几十~几百 token)
3. 用户说话时,agent 根据 description 关键词匹配,判断"这个任务要不要加载这个 skill"
4. **触发后**才读取 SKILL.md 正文;正文引用辅助文件时才读辅助文件

**这意味着:**

- description 是 skill 的"广告位"——必须让 agent 一眼看出"什么任务该用我"
- description 占的 token 是**常态成本**(不管用不用都占),所以精简但精准
- 不要写空泛的 "helps with documents",要写 "Use when working with PDF files or when the user mentions PDFs"
- TRIGGER 关键词覆盖用户的实际话术(跨语言使用时中英都列)

### 辅助文件组织(按需)

| 子目录 / 文件 | 用途 | 何时用 | 例子 |
|---|---|---|---|
| `SKILL.md` | 主入口:frontmatter + 导航 + 入口 API + 示例 + 边界 | 必需 | 所有 skill |
| `references/` | 领域知识详细文档 | 知识量大,需要拆分时 | thesis-docx |
| `templates/` | 模板文件,执行时复制到目标 | skill 产出文件模板时 | init-project-docs |
| `examples/` | 完整可跑的示例代码 | 示例较长,不适合嵌入 SKILL.md 时 | — |
| `core/` / `lib/` | 底层库代码 | skill 提供可调用 API 时 | thesis-docx |
| `scripts/` | 命令行脚本 | skill 提供命令行工具时 | drawio-export |
| 平级 `.md` 文件 | 主题文档(如 `lessons.md`) | 单一辅助文档够用时 | pptx |

### 引用深度(关键)

- ✅ `SKILL.md` → `references/foo.md`(一层)
- ❌ `SKILL.md` → `references/a.md` → `references/b.md`(两层)

引用越深,agent 跟丢的概率越大。保持一层深度。

### 加载层级(token 经济)

| 层级 | 何时加载 | 占 context |
|---|---|---|
| frontmatter 的 description | **总是**(所有 skill) | 持续成本 |
| SKILL.md 正文 | 触发时 | 触发后立即全文 |
| references / templates / etc | 正文引用时 | 按需 |

这就是为什么静态原则强调"少即是多"——每个层级都要克制:

- description 精准但精简(常态成本)
- SKILL.md 100-300 行(触发后立即占满)
- references 按主题拆分(只在需要时加载相关文件)

---

## 静态原则:skill 当下怎么写

### 1. 顺着 agent 的自然工作流

agent 的默认路径是:

```
读需求 → 找入口 → 看示例 → 读代码 → 写脚本 → 执行 → 反馈 → 修正
```

skill 必须在这条路径上**加速**,不能要求 agent 走非自然路径。任何要求 agent "先做 X 再做 Y"的设计,如果 X 不是 agent 自然会做的,就会被跳过。

### 2. 给真实 API + 示例,不要新抽象

**直接给函数签名和真实代码示例**。不要发明中间抽象层(伪命令名、词表、DSL)。

```
✅ 好:  safe.replace_text(anchor, new_text)
❌ 坏:  content-replace-text → (翻译) → safe.replace_text(...)
```

任何中间层必须证明它**减少了 agent 的总工作量**,否则就是冗余。判断标准:agent 看到中间层后,会不会立刻把它翻译回真实 API?会 → 中间层无用。

### 3. 写代码读不出来的信息

| 写 | 不写 |
|---|---|
| 领域知识(为什么这么设计) | 函数实现细节 |
| 边界条件、陷阱、不变量 | 函数做什么(看代码就知道) |
| 何时用 / 何时不用 | 参数定义(看签名) |
| 反模式(防踩坑) | 基础语法(agent 已经会) |
| 真实可复制的代码示例 | 罗列所有可能的操作 |

**测试每段内容:** "这能从代码直接看出来吗?"能 → 删掉。

### 4. 确定性 > 优雅

agent 宁可走**确定性高的长路**(直接调函数,签名错立刻挂),也不走**优雅但不确定的短路**(组合后翻译,翻译可能错、可能跳过)。

函数签名是客观的——错了立刻报错。抽象层是主观的——错了可能不报错,等执行才发现,甚至永远不被发现。

### 5. 少即是多

context 是公共资源,skill 跟对话历史、其他 skill 共享 window。

- SKILL.md 正文 ≤ 500 行(目标 100-300 行,越短越好)
- 引用文件**保持一层深度**(SKILL.md → ref1.md,不要 → ref2.md → ref3.md)
- 每段都问"这占的 token 值得吗?"

### 6. 示例驱动

真实可复制的代码示例,比抽象规则有用 10 倍。agent 从示例学模式,从规则学不到。

- 2-3 个示例覆盖典型场景即可
- 示例必须**可直接跑**(或最小修改后能跑)
- 示例优先于规则——规则补充示例,不替代

---

## 动态原则:skill 怎么演化(seeding 的真正核心)

静态原则回答"怎么写第一个版本"。动态原则回答"怎么让 skill 在实践中变好"。**这才是 seeding 范式的核心。**

### 1. 从小开始

skill 的初始版本应该尽可能小。只写最关键的:库名 + 入口 + 2-3 个示例 + 边界。

不预测未来需求,不预先列出所有可能操作。预测出来的多半是错的或冗余的——你不知道 agent 实际会怎么用它,等用过了才知道。

### 2. 观察实际使用

skill 不是写完就完。要在实际使用中观察 agent 怎么走:

- 它真的用了你给的示例吗?
- 它绕过你的某些部分吗?(被绕过的部分是冗余)
- 它在哪些地方反复写类似的脚本?(固化信号)
- 它在哪些地方反复踩同样的坑?(沉淀信号)
- 它在哪些地方需要看 references/ 才能继续?(SKILL.md 缺什么)

观察方法:用第二个 agent 实例跑典型任务,第一个 agent 实例(作者)在旁边看。或者复盘自己的对话历史。

### 3. 固化高频路径

发现 agent 反复写同样的脚本 → **把这个脚本固化为库函数**,SKILL.md 里改成"用 X 函数"。

这样新的 agent 实例不用每次重新发明轮子。固化的库比文字指令更可靠(签名错立刻挂)。

### 4. 沉淀常见错误

发现 agent 反复踩同样的坑 → **加一条安全规则 / 反模式到 SKILL.md**。

错误信息是最好的老师。一条"不要 X,因为 Y"的反模式,胜过十条正面指令。

### 5. 拆分膨胀文件

SKILL.md 超过 500 行 → 把领域知识拆到 `references/`,把示例拆到 `examples/`,SKILL.md 只留导航和入口。

引用保持一层深度。拆分的标准是**领域边界**,不是行数——同主题的内容聚一起,跨主题的拆开。

### 6. 演化是作者的事,不是 agent 运行时

agent 不会自动更新 skill。**作者在复盘时观察、判断、动手。** agent 用 skill,作者养 skill。

这是 seeding 范式的关键——agent 和作者的角色分工:agent 跑任务,作者基于 agent 的实际行为迭代 skill。

### 7. 保留生长空间

写 SKILL.md 时,结构要模块化,未来拆分时能干净地抽出。引用保持一层深度,章节边界清晰,不要交叉引用纠缠。

---

## Skill 该写什么

### 标准结构模板

```markdown
---
name: <skill-name>
description: "<做什么>. TRIGGER: <精准触发词>"
---

# <Skill 名称>

## 定位
一句话说什么 + 关键边界(不做什么 / 不替用户做什么)。

## 何时用 / 不该用
精准的触发条件 + 排除场景(防误触发)。

## Workflow
1. Step 1: ...
2. Step 2: ...
3. ...

## 入口与关键 API
直接给库名、入口、关键函数签名。不要抽象层。

## 示例
2-3 个真实代码示例,覆盖典型场景。

## 边界
- 能做 / 不能做
- 安全规则
- 反模式(防踩坑)

## 参考(可选)
links to references/*.md(一层深度)
```

### 该写 / 不该写(完整对照)

| 该写 | 不该写 |
|---|---|
| 库的入口和关键函数签名 | 函数实现细节 |
| 真实代码示例(可复制) | 抽象规则 / 命名规范 / 词表 |
| 领域知识(代码读不出来的) | 代码能直接读出来的事实 |
| 何时用 / 何时不用 | agent 已经知道的常识 |
| 边界条件、安全规则、陷阱 | 罗列所有可能的操作 |
| 反模式(防踩坑) | "优雅的"抽象层 |

---

## 通用要点

### description 写法

- 第三人称("Processes PDF files" 而非 "I can help you...")
- 包含两个信息:**做什么 + 什么时候触发**
- 写具体的触发关键词,不要空泛的 "helps with documents"

```
# 好
description: "Extract text and tables from PDF files. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction."

# 差
description: "Helps with documents"
```

### name 写法

- 全小写,只用字母、数字、`-`
- ≤ 64 字符
- 动名词或名词短语(`processing-pdfs`、`pdf-processing`)
- 避免空泛名字(`helper`、`utils`、`tools`)

### 自由度匹配

根据任务的脆弱性设定自由度:

- **高自由**(文字指令):多种做法都行、决策依赖上下文。如代码审查、文档生成。
- **中自由**(伪代码 / 带参数脚本):有推荐模式但允许变化。
- **低自由**(精确脚本):操作脆弱、必须精确执行。如数据库迁移。**不要加 `--no-verify` 之类的额外 flag**。

### 反馈循环

复杂操作要有 `validate → fix → repeat` 循环。不要让 agent 一步到位——让它在中间步骤检查结果,发现错误及时修正。

### 脚本相关

- 脚本要**解决问题**,不要把问题抛回给 agent(不要写 `return open(path).read()` 然后期望 agent 处理 FileNotFound)
- 配置参数要有**理由**(不要写 `TIMEOUT = 47` 而不解释为什么是 47)
- 路径一律用正斜杠 `/`,不用 `\`
- 列出依赖包

### 测试

- 写 skill 之前先建评估。先跑 agent 不带 skill 看它哪里失败,再针对性写
- 用一个 agent 实例写 skill,另一个实例测 skill,观察行为后回来改
- 在你计划使用的模型上都测一遍。强模型不需要过度解释,弱模型需要更多细节

---

## Workflow A: 创建新 skill

### 步骤

1. **识别领域**——这个 skill 解决什么问题?agent 没它会怎么失败?
2. **找底层库**——已有的库 / 工具 / API 是什么?记下入口和关键签名。
3. **写 2-3 个真实示例**——覆盖典型场景,代码可直接跑。
4. **列出边界和陷阱**——agent 容易踩的坑、不能做的事、安全规则。
5. **写 SKILL.md**——按上面的结构模板。每段问"这能从代码看出来吗?",能 → 删。
6. **测试**——另一个 agent 实例跑典型任务,观察是否按预期走。

### 设计原则

- **从小开始**。只写入口 + 示例 + 边界。不预测所有未来需求。
- **库优先于文档**。能写成库函数的就不要写进 SKILL.md 当文字指令。
- **保留生长空间**。结构模块化,未来拆分时能干净抽出。
- **删比加难**。写完一遍后再删一遍——能删的全删掉。

---

## Workflow B: 演化现有 skill(seeding 的核心动作)

这是 seeding 范式真正区别于"一次性写好"的地方。**好 skill 是养出来的,不是写出来的。**

### 何时回顾 skill

- 完成 N 次任务后(N=5~10,样本够看模式)
- 发现 agent 反复绕过 skill 的某些部分
- 发现 agent 反复踩同样的坑
- SKILL.md 接近 500 行
- 项目本身发生了大改动(库升级、架构变化)

### 演化动作

| 信号 | 动作 |
|---|---|
| agent 反复写同样的脚本 | 固化为库函数,SKILL.md 改用函数 |
| agent 反复踩同样的坑 | 加安全规则 / 反模式到 SKILL.md |
| SKILL.md > 500 行 | 拆分领域知识到 references/ |
| agent 反复看某个 references/ | 把它的入口提到 SKILL.md |
| agent 绕过 SKILL.md 的某段 | 这段是冗余,删掉 |
| agent 反复问同一个问题 | 在 SKILL.md 加一段说明 |
| 子领域独立成型 | 分裂为单独 skill |

### 演化原则

- **基于观察,不基于预测。** 等事情发生了再改,不要预先准备。
- **加比删容易。** 大胆删冗余,谨慎加新内容。
- **保留演化痕迹。** 重要决策可以在 SKILL.md 或 references/ 留简短注释(为什么这么设计)。
- **作者定期复盘。** 不要等 skill 完全失控才改。每月或每十次使用回看一次。

---

## Audit checklist

逐项检查目标 skill 的 SKILL.md:

### 内容健康

- [ ] 是否有"核心定位"一句话说明做什么?
- [ ] 是否有"何时用 / 不该用"的精准触发条件?
- [ ] 关键 API 入口和签名是否清晰?
- [ ] 至少 2 个真实代码示例?
- [ ] 边界 / 安全规则 / 反模式是否列出?

### 简洁健康

- [ ] SKILL.md ≤ 500 行?
- [ ] 每段都过"代码读得出来吗?"测试?(读得出来 → 删)
- [ ] 引用保持一层深度?
- [ ] 没有重复信息(SKILL.md 不复述 references/ 内容)?

### 抽象健康

- [ ] **没有伪命令名 / 词表 / DSL**?(所有"命令"必须对应真实函数)
- [ ] **没有"翻译步骤"**?(agent 不需要把 skill 的概念翻译成代码)
- [ ] **没有"先组合再调用"的两步流程**?(必须一步直接调)
- [ ] 所有示例都是真实可跑的代码,不是伪代码?

### 演化健康(seeding 核心)

- [ ] 初始版本是否克制(只写入口+示例+边界,没预测未来)?
- [ ] 是否有最近一次基于实际使用的更新?
- [ ] 高频路径是否已固化为库函数?(反复同样的脚本 → 写成库)
- [ ] 常见错误是否有约束规则?(反复踩坑 → 加安全规则)
- [ ] 是否有该拆分但未拆分的部分?(SKILL.md 太长 / 子领域独立)
- [ ] 是否有 agent 绕过但未删除的冗余?

**评分:** 0-2 项不通过 → 健康。3-5 项 → 需修订。6+ 项 → 需重新设计。
