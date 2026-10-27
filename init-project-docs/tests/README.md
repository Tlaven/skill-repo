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
- `check-doc-refs.ps1`:N2 缺「失败语义」只对 N2 模块文档报;`> 出处：…` 行与普通引用一样必须报(该写法已退役);入口文档点具体 ADR 条目要报 `l1-entry-ref`,L1 活文档索引里的目录级行(含 `docs/decisions/`)与 `adr-000` 模板名放行。

**纪律:** 新增机器判据先写反向测试(必须能红),再确认它数的是什么,最后两平台各跑一遍。
