# init-project-docs 工具测试

```bash
cd init-project-docs
python -m unittest discover -s tests -v
```

覆盖:

- `check-code-refs.py`:缺引用必须报;补上后必须绿;fenced code block 里的示例不误报。
- `run-n2-acceptance.py`:无 manifest 只列不跑;`--run` 下 PASS / FAIL 都正确。
- `check-consistency.py`:重复定义 / 同名数值冲突必须报。
- `lint-doc-structure.py`:长段落警告;`--strict` 才会退 1。
- `adr-index.py`:索引漂移必须报;`--write` 后必须绿;重复 ID / 非规范状态 / `superseded` 缺目标 / 关系悬空 / 文件名与标题不符都要报;旧格式 `## 状态` 要能回退解析;`adr-archive` / `adr-long` 只警告不退 1。
- `adr-index.py` 引用对账:引用了不存在的 ID 必须报;引用 superseded 记录只警告;fenced block 里的编号不算引用;`--no-citations` 能关。
- `adr-index.py --immutable`:正文改写必须报;文末追加补充、改 frontmatter、加 superseded 注记、移进 `archive/` 都必须放过;记录被删必须报。
- `adr-index.py` 旧格式容忍:状态带注记(`accepted(2026-10-15)` / `⚠️ accepted(已落地：…)`)、标题用全角冒号、索引叫 `README.markdown`、引用 `ADR-000` 模板——都不得误报;真正未知的前导词(`已定`)仍必须报。超词警告超过 3 条时只打一行汇总,`--max-words` 能调阈值。

**纪律:** 新增机器判据先写反向测试(必须能红),再确认它数的是什么,最后两平台各跑一遍。
