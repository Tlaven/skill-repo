# AGENTS.md — skills-repo

> **定位**:本仓库的 repo 级 L1 记忆文件(Command Code 宿主加载;若将来接第二宿主,主文件仍为本文件,另一份只放指针,不复制内容)。
> **边界**:方法论本体(三时间轴 / 三段式 / 4 层 / novelty / 铁律 / E1–E7)**不在本文件复述**——唯一归属是 `init-project-docs` skill;本文件只承载 **repo 级增量**。
> **状态**:2026-10-19 由 agent 按证据起草;标 `【推断待确认】` 的行待作者拍板。

## [是什么]

- 个人 **skill 单源仓库**:每个顶层目录 = 一个可加载的 skill;使用点(`~/.commandcode/skills/`、`~/.claude/skills/`、`~/.config/opencode/skills/`)以 **junction** 指回本仓库。
- 根 `scripts/` = 仓库级工具(门禁 / 验收 runner);各 skill 的 `scripts/` 归各 skill 自己。
- 根 `notes/` = 「agent」抽象项目的汇总脚手架(非 skill;自带生长纪律,见其 README)——与具体项目层的 `docs/scaffolds/` 同族异层;项目向下取用后各自独立、不设同步。【作者拍板 2026-10-19;本地目录,不入库】
- skill 地图(9 个;「验收档」定义见各 SKILL.md 的 `## 验收` 段):

| skill | 一句话 | 验收档 |
|---|---|---|
| aigc-derate | 论文降重 / AIGC 降率:标色检测、往返翻译改写、字数偏差检查(配合 thesis-docx) | 未验收 |
| drawio-export | JSON 描述生成 .drawio,本地 draw.io 导出 SVG/PNG(配合 thesis-docx 插图) | smoke |
| essentials | 弱领域方法论:从外部来源提炼可复用的判断脚手架(essentials 文档) | teach-back |
| init-project-docs | 项目记忆协议:历史 / 当下 / 未来 + 三段式 × 4 层 + 多镜复核;seeding 子 skill | teach-back |
| macro-market-radar | 全球宏观市场雷达:数据快照 → 收集 → 交叉验证 → 融合解读 | 未验收 |
| pptx-delivery | PPTX 生成 / 编辑 / QA:可执行断言 C1–C9 + 负控套件 + 交付验收清单 | acceptance |
| seeding-skills | skill 设计范式:上下文 / 约束定位 + 类型分诊 + 种子式演化 | 未验收 |
| thesis-docx | 中文论文 .docx 读写:Locator → Anchor → Mutation 内容寻址 | 未验收 |
| video-decode | 视频链接 → 完整文字稿 + 结构化解读(可按需逐条核查) | 未验收 |

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
8. **`.ps1` 必须 UTF-8 带 BOM**:Windows PowerShell 5.1 对无 BOM 文件按 ANSI(GBK)解码,中文字符串会被撕裂成语法错。【实测:skills-eval 首跑解析失败,补 BOM 后通过;同日全仓扫描并修正 `render_slides.ps1`】

## 维护 checklist(新增 / 修改 skill 时)

1. 新 skill → 登记 `L1_FILES`(不变量 3);
2. 改脚本 → 同步文档,否则 hook 挡(不变量 1);
3. 提交信息:`type(scope): 中文摘要——要点`,细节在正文分点(参考 `git log`);
4. 写 AI 未见领域逻辑(N2)前 → 按 `init-project-docs` 的 teach-back 做一次独立复核(按需、可攒批);
5. 新机器恢复门禁:把 `bash scripts/check-docs-sync.sh --staged --strict`、`powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/skills-eval.ps1 -Changed || true`(只提示)与 `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check-skills.ps1 -Changed || true`(只提示)接进 `.git/hooks/pre-commit`(现网 hook 首注释即模板);
6. 改 skill 行为 → 跑 `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/skills-eval.ps1 -Changed`;无验收入口的 skill 显示「未接入」,补 `## 验收` 段(档位:smoke / golden / acceptance / teach-back)+ 可选 `eval/run.ps1` 再接入;
7. 改 skill 结构(新 skill / frontmatter / 引用 / SKILL.md 篇幅)→ 跑 `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check-skills.ps1`;FAIL 清零,WARN 记账;
8. 新增 / 修改 `.ps1` → 跑 `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check-ps1-bom.ps1`;缺 BOM 必须补(不变量 8)。

## 常用命令

```bash
bash scripts/check-docs-sync.sh            # 门禁自测:工作区 vs HEAD
bash scripts/check-docs-sync.sh --staged   # 同 pre-commit
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/skills-eval.ps1 -Changed   # 变更涉及的 skill 验收（-Name / -All；默认提示不阻断）
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/package-skill.ps1 -Name <skill>   # 打交付包（dist/<name>-<version>.zip + manifest + sha256；非 golden/acceptance 需 -Force）
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check-skills.ps1   # 结构检查：frontmatter / TRIGGER / 死链 / 行数（-Changed / -Name / -Strict）
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check-ps1-bom.ps1  # .ps1 BOM 检查（-Strict / -Root）
```

## 开放问题

- [x] **使用点覆盖(2026-10-19 核 / 同日处置)**:① `aigc-derate` 已补挂 OpenCode(与论文套件 thesis-docx / drawio-export 同宿主);② OpenCode 侧 `macro-market-radar` 已由副本改为 junction(改前核验:9 文件全同,仅 `.cache/index_history.json` 不同;旧副本备份留在会话沙盒)。当前:OpenCode 挂 7 个(pptx-delivery / drawio-export / thesis-docx / init-project-docs / video-decode / macro-market-radar / aigc-derate),CC 挂 5 个(essentials / init-project-docs / macro-market-radar / seeding-skills / video-decode),Claude 挂 2 个(init-project-docs / seeding-skills)。
- [ ] 不变量 4 / 5 是否升格为全仓约定(现仅 pptx-delivery 一例)?

## 指针

- 方法论本体 + teach-back 流程:`init-project-docs` skill(`references/evolution-rules.md` 是 E1–E7 唯一正文归属)。
- 术语:`init-project-docs` 的自有词(历史 / 当下 / 未来、契约、对账 / 复核、镜头等)以 `init-project-docs/references/skill-glossary.md` 为准;与通用义冲突时按该表。
- skill 设计范式:`seeding-skills`。
- 各 skill 行为契约:对应 `SKILL.md`。
