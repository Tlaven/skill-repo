# AGENTS.md — skills-repo

> **定位**:本仓库的 repo 级 L1 记忆文件(Command Code 宿主加载;若将来接第二宿主,主文件仍为本文件,另一份只放指针,不复制内容)。
> **边界**:方法论本体(三段式 / 4 层 / novelty / 铁律 / E1–E7)**不在本文件复述**——唯一归属是 `init-project-docs` skill;本文件只承载 **repo 级增量**。
> **状态**:2026-10-19 由 agent 按证据起草;标 `【推断待确认】` 的行待作者拍板。

## [是什么]

- 个人 **skill 单源仓库**:每个顶层目录 = 一个可加载的 skill;使用点(`~/.commandcode/skills/`、`~/.claude/skills/`、`~/.config/opencode/skills/`)以 **junction** 指回本仓库(现有一处例外:OpenCode 侧 `macro-market-radar` 为普通副本,见开放问题)。
- 根 `scripts/` = 仓库级工具(门禁脚本);各 skill 的 `scripts/` 归各 skill 自己。
- 根 `notes/` = 「agent」抽象项目的汇总脚手架(非 skill;自带生长纪律,见其 README)——与具体项目层的 `docs/scaffolds/` 同族异层;项目向下取用后各自独立、不设同步。【作者拍板 2026-10-19】
- skill 地图(9 个):

| skill | 一句话 |
|---|---|
| aigc-derate | 论文降重 / AIGC 降率:标色检测、往返翻译改写、字数偏差检查(配合 thesis-docx) |
| drawio-export | JSON 描述生成 .drawio,本地 draw.io 导出 SVG/PNG(配合 thesis-docx 插图) |
| essentials | 弱领域方法论:从外部来源提炼可复用的判断脚手架(essentials 文档) |
| init-project-docs | 项目文档骨架引导;三段式 × 4 层方法论的**唯一归属** |
| macro-market-radar | 全球宏观市场雷达:数据快照 → 收集 → 交叉验证 → 融合解读 |
| pptx-delivery | PPTX 生成 / 编辑 / QA:可执行断言 C1–C9 + 负控套件 + 交付验收清单 |
| seeding-skills | skill 设计范式:种子式演化(静态导航 + 动态生长) |
| thesis-docx | 中文论文 .docx 读写:Locator → Anchor → Mutation 内容寻址 |
| video-decode | 视频链接 → 完整文字稿 + 结构化解读(可按需逐条核查) |

- **不做(边界)**:① 使用点旁另放副本——使用点是 junction,改仓库即改使用点;② 运行产物 / 本地物料入库(见不变量 7)。

## [已定](作者指定,不得擅改)

- L1 文件名:Command Code → `AGENTS.md`(不用 `CLAUDE.md`);多宿主并存时主文件唯一,其余放指针。
- skill 单源:本体只在本仓库;使用点只挂 junction。
- 各 skill 的契约 = 各自 `SKILL.md`(frontmatter `description` 即触发面)。

## [为什么]

- 单源 + junction:多份副本必然漂移(与"文档同源"同一原则,见 init-project-docs 的 E1)。
- 门禁脚本只查"有没有动过"、不判对错:判对错交给独立复核(teach-back);检查器只做确定性对账。

## [不变量](repo 级)

1. **代码-文档同步门禁**:pre-commit 跑 `scripts/check-docs-sync.sh --staged --strict` —— 改 `scripts/` 下 `.sh/.ps1/.py` 必须同时动文档(`templates|references/`、任一 `SKILL.md` 或本文件),否则被挡;确不需要同步才 `--no-verify`,自担。【实测:hook 接线 2026-10-17】
2. **`.sh` 必须 LF**:根 `.gitattributes` 已钉 `*.sh text eol=lf` —— CRLF 会让 bash 拒绝执行。【实测】
3. **新增 skill 必须登记**:新 skill 的 `SKILL.md` 要加进 `scripts/check-docs-sync.sh` 的 `L1_FILES`(essentials 曾漏登记,2026-10-19 补——"缺对账点"的实证)。【实测】
4. **许可分层**:改编自外部来源的 skill 保留上游许可文件、不与个人文本混写(样板:pptx-delivery 的 `LICENSE.txt`)。【实测:pptx-delivery;是否升格全仓约定【推断待确认】】
5. **证据标签**:新增断言 / 阈值标【实测:位置】/【引用:来源】/【假设待测】;假设待测占比尽量 <30%。【实测:pptx-delivery 落地;是否升格全仓约定【推断待确认】】
6. **布局跟随项目**:各 skill 目录形态自定(flat / references / scripts / core……),不强制统一。【实测:三种形态并存】
7. **本地物料不入库**:校准 / 盲测等物料放 `<skill>/.calibration/` 并在 `.gitignore` 声明(样板:`init-project-docs/.calibration/`)。【实测】

## 维护 checklist(新增 / 修改 skill 时)

1. 新 skill → 登记 `L1_FILES`(不变量 3);
2. 改脚本 → 同步文档,否则 hook 挡(不变量 1);
3. 提交信息:`type(scope): 中文摘要——要点`,细节在正文分点(参考 `git log`);
4. 写 AI 未见领域逻辑(N2)前 → 按 `init-project-docs` 的 teach-back 做一次独立复核(按需、可攒批);
5. 新机器恢复门禁:把 `bash scripts/check-docs-sync.sh --staged --strict` 接进 `.git/hooks/pre-commit`(现网 hook 首注释即模板)。

## 常用命令

```bash
bash scripts/check-docs-sync.sh            # 门禁自测:工作区 vs HEAD
bash scripts/check-docs-sync.sh --staged   # 同 pre-commit
```

## 开放问题

- [ ] **使用点覆盖(2026-10-19 核)**:OpenCode 挂 5 个(pptx-delivery / drawio-export / thesis-docx / init-project-docs / video-decode),CC 挂 5 个(essentials / init-project-docs / macro-market-radar / seeding-skills / video-decode),Claude 挂 2 个(init-project-docs / seeding-skills)。待拍:① `aigc-derate` 是唯一未挂任何使用点的(与已挂 OpenCode 的 thesis-docx / drawio-export 同属论文套件)——补挂还是判停用?② OpenCode 侧 `macro-market-radar` 为普通副本目录(非 junction;当前与 repo 版一致,仅运行缓存不同)——改 junction 还是保留?
- [ ] 不变量 4 / 5 是否升格为全仓约定(现仅 pptx-delivery 一例)?

## 指针

- 方法论本体 + teach-back 流程:`init-project-docs` skill(`references/evolution-rules.md` 是 E1–E7 唯一归属)。
- skill 设计范式:`seeding-skills`。
- 各 skill 行为契约:对应 `SKILL.md`。
