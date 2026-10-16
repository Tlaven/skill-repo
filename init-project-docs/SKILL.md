---
name: init-project-docs
description: "为 AI 协作初始化项目文档骨架(AGENTS.md / CLAUDE.md + docs/)。当用户新起项目、立项、项目初始化,或想写 CLAUDE.md / AGENTS.md、为项目建术语表骨架(glossary)、把 AI 未见领域(N2)的核心逻辑写到可实现时使用。TRIGGER: 新项目, 项目初始化, 立项, 写 CLAUDE.md, 写 AGENTS.md, init docs, bootstrap docs, 初始化文档骨架, 补 L1 记忆文件, 术语表骨架, 新领域核心逻辑, N2, teach-back, 复述确认。不适用: 已有完善文档且无改动诉求; 只要一份代码速查(改用内置 init); 单次任务 / 一次性脚本。"
---

# Init Project Docs — AI 协作时代项目文档初始化

## 定位

项目文档**骨架**的引导者。不是文档内容的作者——内容靠和用户对话涌现。

skill 提供四样东西:

1. **方法论框架**——让 agent 知道有这套思维方式(三段式 × 4 层)
2. **文件结构骨架**——项目应该有哪些文档文件、放哪里
3. **对话地图**——告诉 agent 该问什么,而不是替用户答
4. **可判定化护栏**——术语先定义、N2 写到可实现、进实现前 teach-back

**关键边界:** 不替用户写内容——但**允许"从代码 / 证据推断草稿 + 标注『推断,待确认』"**,禁止凭空编造。**证据 vs 编造判据:能在既有作者文档 / git / 代码里查到出处的 = 证据(允许,标来源即可);查不到、只能靠猜的 = 编造(禁止,进"开放问题"清单)。** **信息不足时可判定化优先于"不替写"**(空洞文档比待确认草稿更糟)。**规则正文的唯一归属是项目根的记忆文件**(由 `templates/l1-memory.md` 落入项目);本 skill 只讲流程、不重述规则。

---

## 宿主适配(先定:L1 文件叫什么?)

**宿主 ↔ L1 文件名的映射,唯一归属在 `templates/l1-memory.md` 顶部那张表**(本 skill 不重述,避免两处漂移)——决定文件名前读那里。

- **不确定就问用户"你用哪个 agent 宿主?"**;检测到 `.claude/` 用 `CLAUDE.md`,否则默认 `AGENTS.md`。
- **多宿主并存:** 选一个当主文件,其余放一行指针(`见 AGENTS.md`)——不要各写一份,**两份规则必然漂移**(细则同见 `l1-memory.md` 顶部)。

---

## 核心理念

文档是人和 AI 的"共享内存"。写**决策需要的信息**,不写**实现需要的信息**。

- 人类 vibe coding 不读代码 → 文档是人类对项目的唯一心智模型
- AI 不会自动读全部代码 → 文档是 AI 加载上下文的入口
- 双方必须在同一份信息上对齐 → 文档是唯一共享协议

内容靠对话产生,因为对话本身就是确立文档内容的核心方法。**skill 不能跳过对话**。

---

## 去模糊与可实现(对话时的三个动作)

文档不只是"索引",更是让 AI 在**没见过的领域**里能正确动手的唯一依据。**规则正文在 L1 记忆文件**;这里只讲**对话时该怎么做**:

1. **术语先定义**:听到领域专有名词 / 易混词,追问并登记 `docs/glossary.md`(一个词只定义一次)。
   - AI 用模糊词(「优化」「合理处理」「相关逻辑」)= 你没给它可判定的指称物。追问:`"具体指什么?给出两个互斥解释让我选。"`
   - 换写法见 `templates/glossary.md` 的"去模糊词表"。
2. **给逻辑分档**:填 novelty(N0 通用 / N1 项目特有 / **N2 AI 未见**)。N2 = 领域特有 / 创新逻辑,**必须**写到"步骤级说明 + 精确例子 + 可跑验收"(怎么造验收见 `references/verifying-n2.md`);N0 / N1 不必。
3. **进实现前 teach-back**:派一个**独立 subagent**(看不到本会话)复述并列出缺口,不过关就**改文档**(见 Step 3.5)。

---

## 何时使用

**适合:**
- 用户开始新项目(空目录或刚 git init)
- 用户说"写 CLAUDE.md / AGENTS.md / 项目初始化 / 立项 / init docs"
- 已有项目但没有 L1 记忆文件,用户想补
- **已有 L1 记忆文件但用户想引入这套方法论**(走合并模式,见 Workflow Step 2B)
- 项目结构变了,需要重建文档骨架
- 项目含 **AI 未见的领域 / 创新核心(N2)**,需把核心逻辑写到"可实现"

**不适合:**
- 已有完整 L1 记忆文件且用户没说要改(应看现有结构,不主动推销)
- 单次任务、一次性脚本(不需要长期文档)
- 用户没明确要求(避免主动推销方法论)
- **用户只想快速给老项目生成一份速查**(命令、目录结构、依赖、代码风格)→ 改用内置 `init` skill。它扫 codebase 自动填**实现信息**;本 skill 专注**决策信息**(为什么、被拒方案、不变量)。两者互补——`init` 写 [是什么] 事实段,本 skill 写 [为什么] + [不变量] 段。

---

## 方法论速查（指针）

方法论正文分两处归属:**三段式 / 4 层 / 跨层工件 / novelty 分档 / 铁律 11 条** → `templates/l1-memory.md`(随 L1 落地到项目根);**演化期规则 E1–E7** → `references/evolution-rules.md`(随项目落地到 `docs-templates/evolution-rules.md`)。**本 skill 只讲流程、不重述规则**——需要结构定义时读这两处,此处不复述。

各文件落地位置见下方「产出文件结构」。

---

## 执行面:规则靠什么生效

规则只是文字时,LLM 遵守是概率性的。所以每条规则按"靠什么生效"分三层——**能机器判定就机器判定,能交给验证者就交给验证者,剩下的老实认了**:

| 层 | 谁能执行 | 适用 | 本 skill 的做法 |
|---|---|---|---|
| **机器** | 检查器 / pre-commit / CI | 可机器判定的 | `scripts/` 两个检查器(接线见 `references/wiring.md`) |
| **验证者** | 一个独立、看不到本会话的 agent | 需要判断的 | Step 3.5 的 teach-back 验证者 |
| **约定** | 无——只能靠自觉 | 不可判定的 | 明确承认无法保证 |

L1 铁律每条末尾都带这个标签(`[机器]` / `[验证者]` / `[约定]`)。

**自带两个检查器**(均 `.sh` + `.ps1`):

1. `scripts/check-docs-sync.sh` —— 只查一件事:`git diff` 里代码变了、但 `docs/**` 与 L1 记忆文件都没变 → 提醒。**只查"有没有动过",不判对错**。
2. `scripts/check-doc-refs.sh` —— 结构性对账:`docs/` 里的死链、未填占位符、标了 N2 却缺「验收」。

接线方式(pre-commit / CI / 宿主钩子)与示例见 `references/wiring.md`;skill 不硬绑宿主。

> 别给"约定型"规则硬配检查器——那只会制造噪音,让人开始无视所有提示。

---

## Workflow

### Step 1: 检查环境 + 决定模式 + 定宿主

- 当前目录是否已有 L1 记忆文件(`CLAUDE.md` / `AGENTS.md`)?
  - **没有 L1**,且**基本空 / 新项目** → 走 **Step 2A 全新模式**
  - **没有 L1,但已有成体系文档**(README + `docs/` / 设计规格)→ 走 **Step 2C 嫁接模式**
  - **有 + 用户想引入这套方法论** → 走 **Step 2B 合并模式**
  - **有 + 用户没说要改** → 不要主动推销,只回应具体问题
- 是否 git 仓库?是否基本空目录?
- 用哪个宿主?→ 决定 L1 文件名(见「宿主适配」)

### Step 2A: 全新模式——落 L1 + 整套 `docs-templates/`

**关键:`docs/` 下的"契约"不要预先建空骨架**(会被遗忘、最终空着);但 `docs-templates/` 是"运行期手册 + 待复制 stub",属"对账忽略",**应一次性放齐**——否则 L1 正文里指向它们的指针会悬空。

1. 复制 `templates/l1-memory.md` → 项目根的 L1 文件名。
2. 把**整套** `docs-templates/` 落地(拷进 `docs-templates/`):`templates/module-doc.md`、`templates/adr-template.md`、`references/evolution-rules.md`、`references/verifying-n2.md`、`references/teach-back-verifier-prompt.md`。

然后立即进入 Step 3 对话。**`docs/` 下的契约文件按需在对应阶段创建:**

- 出现领域名词 / 易混词 → 复制 `templates/glossary.md` → `docs/glossary.md`
- 进入 L2 讨论 → 复制 `templates/architecture.md` → `docs/architecture.md`
- 首次要写模块文档 → 从已在 `docs-templates/module-doc.md` 的 stub 生成 `docs/modules/<name>.md`
- 首次记 ADR → 复制 `templates/decisions-readme.md` → `docs/decisions/README.md`(单条模板已在 `docs-templates/adr-template.md`)
- 首次对账(teach-back / 文档考古)→ 产出写 `docs/reviews/YYYY-MM-DD-<主题>.md`(无需模板)
- 用户明确要 L4 → 复制 `templates/core-code.md` → `docs/core-code.md`

### Step 2B: 合并模式——已有 L1 记忆文件

**核心原则:不破坏现有内容,只补方法论 + 缺失层。**

1. **读现有 L1 文件**,识别已有段落(项目概述、命令、架构、约束等)
2. 把 `templates/l1-memory.md` 的"文档方法论"整段插入合适位置(通常在项目概述之后、架构之前)
3. **不动用户原有内容**——不替换、不重排
4. 检查现有内容里的 [不变量] 信息:很多项目把约束散落在各段,可提示用户归并到 L1 [不变量] 段,但**让用户决定**
5. `docs/` 目录按需创建(先问用户)
6. 进入 Step 3,但**起点是补缺**,不是从零问(用户已有的内容跳过)

### Step 2C: 嫁接模式——已有文档、缺 L1

**场景:** 项目**已有成体系文档**(README 很全 / `docs/` 下有架构、设计、规格),但**没有 L1 记忆文件**。**不要当成空项目重造一套**——那会和既有文档撞车(见 E4:"两套并存物必须有 ADR 解释区别")。

**核心原则:先映射,再落骨架;既有的"现状事实"文档 = 指针目标,不新造重复层。**

1. **通读既有文档,映射到 4 层:**
   - 既有的**现状事实**文档(架构描述 / 模块清单)→ 它就是 L2 的事实源。**新 `docs/architecture.md` 只放指针 + 决策 + 不变量,不重抄事实**(E1 指针优先)。
   - 既有的**设计动机 / 不变量 / 验收**文档 → 对应 L1/L2 的 `[为什么]`/`[不变量]` 与 L4;用**指针**指过去,别搬。
   - 既有的**存档 / 旧方案**(如 `docs/legacy/`)→ **考古层**,不是活契约;不迁、不删,标注边界即可(对账要排除它——见 `scripts/check-doc-refs` 的 `DOC_EXCLUDE`)。
2. **落 L1 + 整套 `docs-templates/`**(同 Step 2A)。
3. **填 L1 时标清"内容从哪来":** 从既有作者文档 / git 提取的 = **证据**(允许,标来源);查不到、只能猜的 → 进"开放问题"清单,别硬填(见「关键边界」)。
4. **消歧:** 冲突时在**新骨架文件**顶部加一行 banner 声明"谁是事实源、谁是契约",**不要默默并存**;**但只改新文件、不动作者原有文件**——既有文件的定性冲突(如 README 说"当前实现"、重置章程说"考古层")记为开放问题,交作者拍板(同 2B"不动用户原有内容")。
5. 进入 Step 3 对话,但**起点是"补既有文档缺的那部分"**。嫁接模式下 `docs/architecture.md` 可作**证据草稿**先行创建(映射素材已由既有文档提供),不必等 L1 对话共识——但仍是草案,标 `推断,待确认`。

> **若项目方向尚未收敛**(重立项 / "是什么"未定稿):L1 概述可写成**双段**(现状事实 / 方向草案)+ 显式"开放问题"清单,**不要假装收敛**。teach-back 会正确地卡在这里——那不是文档没写好,是信息还没收敛,补它需要人。

### Step 3: 边对话边写入(核心步骤)

**硬性要求:每段对话产出立即写入对应文档段落,让用户看到进度。** 不要囤积——用户说完一段,马上 Edit 写入,再问下一段。

- **第一阶段(填 L1 主轴):** 按 [是什么] → [为什么] → [不变量] 顺序,每段问 1-2 个核心问题,答完立即写入 L1 文件
- **第二阶段(填 L2 主流程):** L1 有共识后**才创建** `docs/architecture.md`,重点产出**主流程叙述**(10-20 行,从入口到出口)
- **第三阶段(按需,不在初建时一次做完):** 模块开发前建 L3;决策发生时建 ADR;L4 默认不建,**但命中收录标准的 N2(跨模块 / 骨架 / 高扇入)必须建**
- **若 [是什么] 尚未收敛**(重立项 / 方向未定):L1 概述写成**双段**(现状 / 方向草案)+ 显式"开放问题",**别假装收敛**;teach-back 会正确卡在这里(需人拍板,不是 agent 能补的)

### Step 3.5: teach-back 闸门(每层写完 + 进实现前)

**硬性要求:任何实现动作之前,先做 teach-back。** 这是"文档够不够实现"的判据,不是可选项。

**必须派一个全新 subagent 来做——不继承本会话历史,只喂文档本身。** 当前会话自己复述 = 自证(误读会一起误读),不算数。用 `references/teach-back-verifier-prompt.md` 的模板。

- **何时跑:** N1 / N2,或任何"进实现前"的闸门。**N0 跳过**(通用模式,模型自己能补)。
- 产出:① 独立复述三段式;② "我需要但你没写"的缺口清单;③ 判定 通过 / 不通过。
- **不通过 → 改文档**,不是改提示词;改完重跑。
- 冒出的假设 / 歧义 → 当场澄清:登记 `docs/glossary.md` / 补不变量 / 记 open questions。
- 遇 **N2**(新领域核心逻辑)→ **必须**先把"步骤级说明 + 例子 + 验收"补进 core-code / L3,再放行实现。

**退化路径(宿主 / 会话派不出"看不到本会话"的独立 agent 时):** 不要自评充数(自评 = 自证,不算数),也不要卡死。① 把待验证文档正文 + 验证者 prompt 打包成一份"待验证"记录写进 `docs/reviews/`;② 明确标注**闸门未通过(未执行)**;**冻结实现**;③ 把"跑一次独立验证"作为移交项交给宿主 / 人。

只有验证者判"通过"后,才进入下一阶段。

### Step 4: 收尾说明

初轮对话(L1 + L2 主流程)完成后,告诉用户后续机制:

```
文档方法论已落地。接下来:
- 开发新模块前,从 docs-templates/ 复制 module-doc.md 到 docs/modules/<name>.md,先填后写代码
- 重大决策发生时,在 docs/decisions/ 记一条 ADR
- 大改动前,先更新对应层文档,再写代码
- L4 默认不要——只有 core 代码"牵一发动全身"时才补
- 出现新领域名词 → 登记 docs/glossary.md;N2 逻辑 → 补"步骤级 + 例子 + 验收"
- 任何实现前先跑 teach-back(独立 subagent,见 references/teach-back-verifier-prompt.md)
- (可选)把 scripts/ 拷进项目,按 references/wiring.md 接到 pre-commit / CI——挡"改代码忘文档"、查死链 / N2 缺验收(Windows:先按 wiring.md 加一行 `.gitattributes`,否则 `.sh` 会被检出成 CRLF、根本跑不起来)

本文件已含方法论精要,后续 agent 启动会自动加载,不需要再调用这个 skill。
```

---

## 对话地图(L1 三段式的问题清单)

给 agent 的对话地图,**不是问卷**——根据用户回答自然展开,不要机械地一条条问。

### [是什么] 段——问项目定位

- 这个项目要解决什么问题?(一句话能说清吗)
- 谁会用?用在什么场景?
- **不做什么**(明确边界同样重要,边界外写出来)
- 主要功能 / 模块的大致预想?

### [是什么] 段——问术语(填 `docs/glossary.md`)

- 有没有**外人听不懂**的词?(行业黑话、自定义概念)
- 哪些词**最容易混**?(记下来当反例)
- 有没有**旧叫法**已废弃?(记下来当"禁用别名")
- 生成代码时必须知道**类型 / 结构**的词有哪些?

### [为什么] 段——问设计哲学

- 为什么用这个技术栈 / 架构风格?(强约束还是偏好)
- 核心价值观 / 设计哲学,2-3 条?(例:统一模型优先于扩展、性能优先于优雅)
- 考虑过哪些替代方案?为什么拒绝?(被拒方案是金矿)

### [不变量] 段——问硬约束

- 性能预算?(响应时间、吞吐、内存上限)
- 技术栈锁定?(必须用 / 必须不用什么)
- 可维护性底线?(测试覆盖、文档要求)
- 安全 / 合规约束?

---

## 反模式(checklist)

> 涉及 E1–E7 的详细判据见 `references/evolution-rules.md`(项目内:`docs-templates/evolution-rules.md`);此处只列**症状**。

skill 自身要避免的:

- ❌ **凭空编造 L1 内容**(目标、设计哲学优先对话产生;但"从代码 / 既有作者文档 / git 等**证据推断草稿 + 标注『推断,待确认』 + 标来源**"是允许的,不算编造——**判据:有出处=证据,只能靠猜=编造**)
- ❌ **跳过对话直接生成"看起来完整"的文档**(空洞内容比空骨架更糟)
- ❌ **一次性把 `docs/` 契约都建成空骨架**(会被遗忘);但 `docs-templates/` 属"对账忽略"、**应一次放齐**(否则 L1 指针悬空)
- ❌ **在已有 L1 文件的项目静默覆盖**(走 Step 2B,只补方法论段)
- ❌ **一次问完所有问题**(应分阶段,边讨论边记录)
- ❌ **囤积对话产出**(说一段就立即写入)
- ❌ **主动生成 L4**(默认不要,用户问了才加)
- ❌ **把 skill 硬套到已有完善文档的项目**(应区分:无 L1 → 走 Step 2C 嫁接;已有 L1 且没诉求 → 不推销)
- ❌ **[是什么] 新旧陈述并存**([为什么] 被推翻要标 `⚠️ 已被推翻,见 ADR-YYY`)
- ❌ **改代码绕过不变量**(违反却不修订文档 = 不变量失效的开端)
- ❌ **代码注释写版本变更史**(历史归 ADR / git log)
- ❌ **方向性陈述混进事实段裸留**(意向不会变假,只会悬置)
- ❌ **完成 / 放弃的计划留在活跃清单**(done 移出,dropped 带理由升格为"不做 X"的 ADR)
- ❌ **领域名词不定义就直接用**(AI 会拿训练数据里的通用含义去猜,新领域必错)——先登记术语表
- ❌ **N2 核心逻辑只写职责、不给步骤 / 例子 / 验收**
- ❌ **实现前不做 teach-back**
- ❌ **接受模糊词**("优化 / 合理处理"当需求)——换可判定写法
- ❌ **多宿主各写一份规则**(两份必然漂移——主文件 + 指针)

---

## 产出文件结构

```
./AGENTS.md  (或 ./CLAUDE.md,按宿主)  # L1 主战场 —— Step 2A 立即创建
./docs/                     # 契约(durable)—— 对账只扫这里
  ├── architecture.md       # L2 —— 进入 L2 讨论时创建
  ├── glossary.md           # 术语表 —— 出现领域名词时创建
  ├── modules/<name>.md     # L3 —— 每模块开发前
  ├── core-code.md          # L4 —— 可选,命中收录标准的 N2 才建
  ├── reviews/              # E5 对账产出(teach-back / 文档考古) —— 首次对账时创建
  └── decisions/
      ├── README.md         # ADR 索引 —— 首次记 ADR 时创建
      └── adr-XXX-*.md      # 真实 ADR
./docs-templates/           # skill 提供、随项目落地的文件(非契约:对账忽略) —— Step 2A 整套落地
  ├── module-doc.md
  ├── adr-template.md
  ├── evolution-rules.md              # 运行核心:演化期规则 E1–E7(L1 只留指针)
  ├── verifying-n2.md                 # 运行核心:怎么给 N2 造验收
  └── teach-back-verifier-prompt.md   # 运行核心:teach-back 验证者 prompt
```

除 L1 与**整套 `docs-templates/`** 外,`docs/` 下契约**全部按需创建**(理由见 Step 2A)。

---

## 模板文件清单

| 文件 | 用途 | 何时用 | 落地到(项目内) |
|---|---|---|---|
| `templates/l1-memory.md` | L1 记忆文件(三段式 / 4 层 / novelty / 铁律;E1–E7 另见 evolution-rules) | **立即**(Step 2A) | 项目根 `<AGENTS.md / CLAUDE.md>` |
| `templates/architecture.md` | L2 架构层 | 按需 | `docs/architecture.md` |
| `templates/module-doc.md` | L3 模块详细 stub(含 novelty 标记) | **立即**(Step 2A) | `docs-templates/module-doc.md` |
| `templates/glossary.md` | 术语表(受控词汇) | 按需 | `docs/glossary.md` |
| `templates/core-code.md` | L4 核心代码(含 novelty 分档 / N2 附加栏) | 按需 | `docs/core-code.md` |
| `templates/decisions-readme.md` | ADR 索引 + 格式约定 | 按需 | `docs/decisions/README.md` |
| `templates/adr-template.md` | 单条 ADR 模板(状态/背景/方案/选择/后果) | **立即**(Step 2A) | `docs-templates/adr-template.md` |
| `references/evolution-rules.md` | 运行核心:演化期规则 E1–E7 | **立即**(Step 2A) | `docs-templates/evolution-rules.md` |
| `references/verifying-n2.md` | 运行核心:N2 验收手段 / 反模式 / 闸门 | **立即**(Step 2A) | `docs-templates/verifying-n2.md` |
| `references/teach-back-verifier-prompt.md` | 运行核心:teach-back 独立验证者 prompt | **立即**(Step 2A) | `docs-templates/teach-back-verifier-prompt.md` |

---

## 参考来源(改版时借鉴)

- **去模糊**(先摊开假设 / 把模糊指令改写成成功标准):`addyosmani/agent-skills` → `spec-driven-development`
- **上下文分层 / 冲突时"停下问、别自己编" / 可重启会话边界**:`addyosmani/agent-skills` → `context-engineering`
- **先探上下文 → 提方案 → 写 design → spec 自审 → 用户批准**:`superpowers:brainstorming`
- **零上下文也能执行、无占位符、精确路径与验收命令**:`superpowers:writing-plans`
- **锁定的评估面 / durable log**:`Agent-Skills-for-Context-Engineering` → `harness-engineering`
- **规范驱动开发整体流程**(specify → plan → tasks → implement):GitHub Spec Kit
