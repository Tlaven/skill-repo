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

**纪律:** 新增机器判据先写反向测试(必须能红),再确认它数的是什么,最后两平台各跑一遍。
