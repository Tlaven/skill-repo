# Skill 的结构与加载

> 本文件是 `SKILL.md`「结构与加载(要点)」「写作要点」的展开。SKILL.md 只留要点;这里放字段、目录、token 经济与写作细则。

## 一、目录与 frontmatter

每个 skill 必须是一个独立目录,内含 `SKILL.md` 主入口:

```
<skill-name>/
├── SKILL.md          # 必需,主入口
└── (辅助文件按需)
```

SKILL.md 必须以 yaml frontmatter 开头:

```yaml
---
name: <skill-name>                                      # 必需
description: "<做什么>. TRIGGER: <触发关键词>"            # 必需
---
```

字段规则:

- `name`:全小写,只用字母 / 数字 / `-`,≤64 字符。**必须和目录名一致**(否则加载机制找不到)。
- `description`:agent 判断"何时加载"的**唯一依据**。必须包含两类信息:做什么 + 何时触发(具体关键词)。

## 二、description 的加载机制

宿主(Claude Code / Command Code / OpenCode 等)启动时:

1. 扫描所有 skill 目录,**只读 frontmatter 的 description 字段**。
2. 所有 description 进入 agent 的常驻 context(每个 skill 占几十~几百 token)。
3. 用户说话时,agent 根据 description 关键词匹配,判断"这个任务要不要加载这个 skill"。
4. **触发后**才读取 SKILL.md 正文;正文引用辅助文件时才读辅助文件。

这意味着:

- description 是 skill 的"广告位"——必须让 agent 一眼看出"什么任务该用我"。
- description 占的 token 是**常态成本**(不管用不用都占),所以精简但精准。
- 不要写空泛的 "helps with documents",要写 "Use when working with PDF files or when the user mentions PDFs"。
- TRIGGER 关键词覆盖用户的实际话术(跨语言使用时中英都列)。

## 三、辅助文件组织(按需)

| 子目录 / 文件 | 用途 | 何时用 | 例子 |
|---|---|---|---|
| `SKILL.md` | 主入口:frontmatter + 导航 + 入口(按主型)+ 示例 + 边界 | 必需 | 所有 skill |
| `references/` | 详细文档(领域知识 / 方法细则 / 类型判据) | 知识量大,需要拆分时 | thesis-docx / seeding-skills |
| `templates/` | 模板文件,执行时复制到目标 | skill 产出文件模板时 | init-project-docs |
| `examples/` | 完整示例(代码或样例产物) | 示例较长,不适合嵌入 SKILL.md 时 | — |
| `core/` / `lib/` | 底层库代码 | skill 提供可调用 API 时 | thesis-docx |
| `scripts/` | 命令行脚本 | skill 提供命令行工具时 | drawio-export |
| 平级 `.md` 文件 | 主题文档(如 `typography.md`) | 单一辅助文档够用时 | pptx-delivery |

## 四、引用深度

- ✅ `SKILL.md` → `references/foo.md`(一层)
- ❌ `SKILL.md` → `references/a.md` → `references/b.md`(两层)

引用越深,agent 跟丢的概率越大。**深度按"最终消费者所在的位置"算,不按文件此刻在仓库里的位置算。** 若 skill 的文件会被复制进目标项目后**换身份**(如 `templates/l1-memory.md` 落地成项目根的 `AGENTS.md`),仓库里看着是两层的链,在项目里可能仍是一层——别按仓库视角误判。**在同一坐标系内**保持一层深度。

## 五、加载层级(token 经济)

| 层级 | 何时加载 | 占 context |
|---|---|---|
| frontmatter 的 description | **总是**(所有 skill) | 持续成本 |
| SKILL.md 正文 | 触发时 | 触发后立即全文 |
| references / templates / etc | 正文引用时 | 按需 |

每个层级都要克制:

- description 精准但精简(常态成本)。
- SKILL.md 正文触发后立即占满(行数预算见 SKILL.md 静态原则 §5)。
- references 按主题拆分,只在需要时加载相关文件。

## 六、description / name 写法

### description

- 第三人称("Processes PDF files" 而非 "I can help you...")。
- 包含两个信息:**做什么 + 什么时候触发**。
- 写具体的触发关键词,不要空泛的 "helps with documents"。

```
# 好
description: "Extract text and tables from PDF files. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction."

# 差
description: "Helps with documents"
```

### name

- 硬规则见「frontmatter」(小写 / 字母数字与 `-` / ≤64 / 与目录名一致)。
- 风格用动名词或名词短语(`processing-pdfs`、`pdf-processing`)。
- 避免空泛名字(`helper`、`utils`、`tools`)。

## 七、自由度匹配

根据任务的脆弱性设定自由度:

- **高自由**(文字指令):多种做法都行、决策依赖上下文。如代码审查、文档生成(判断 / 知识 / 元型偏高自由)。
- **中自由**(伪代码 / 带参数脚本):有推荐模式但允许变化(流程型)。
- **低自由**(精确脚本):操作脆弱、必须精确执行。如数据库迁移(能力型)。**不要加 `--no-verify` 之类的额外 flag**。

## 八、反馈循环与脚本

- 复杂操作要有 `validate → fix → repeat` 循环。不要让 agent 一步到位——让它在中间步骤检查结果,发现错误及时修正。
- 脚本要**解决问题**,不要把问题抛回给 agent(不要写 `return open(path).read()` 然后期望 agent 处理 FileNotFound)。
- 配置参数要有**理由**(不要写 `TIMEOUT = 47` 而不解释为什么是 47)。
- 路径一律用正斜杠 `/`,不用 `\`。
- 列出依赖包。

## 九、测试

- 写 skill 之前先建评估——与「判型」同一问:先跑 agent 不带 skill,看它哪里失败,再针对性写。
- 用一个 agent 实例写 skill,另一个实例测 skill,观察行为后回来改。
- 在你计划使用的模型上都测一遍。强模型不需要过度解释,弱模型需要更多细节。
