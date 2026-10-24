# 检索面:让历史不被关键词撞见

> **问题:** Agent 不读索引,但会 `rg 关键词`。命中一段已作废的决策,它不会自动知道那是哪一年的、还有没有效——这是 stale-document poisoning:检索到过期证据,会让本来答得对的模型答错。教它"先读索引"没有用,它压根不走那条路。

## 三层,只有第一层改得了结果

| 层 | 机制 | 覆盖 | 失效场合 |
|---|---|---|---|
| **检索** | `docs/decisions/.ignore` 写 `archive/`;`.vscode/settings.json` 的 `search.exclude` | rg / Claude Code / OpenCode / VS Code / Cursor | `git grep`、`grep -r`、任何不读这两个配置的工具 |
| **命中** | 记录标题下的状态横幅 | 所有工具,前提是文件被打开 | 只读匹配行、不打开文件 |
| **解释** | L1 一行:命中 `docs/decisions` / `docs/reviews` 时那是理由,不是规则 | 所有工具 | Agent 不读 L1 |

**只有第一层能改变"搜到什么"。** 索引、目录名、`archive/` 的位置都改不了 grep 的结果——实测:把文件移进 `archive/`,`rg 关键词 .` 照样命中,目录对内容搜索没有任何意义。

## 第一层怎么配

`docs/decisions/.ignore`,内容一行:

```
archive/
```

- **必须放在 `docs/decisions/` 里**,不能放仓库根写 `docs/decisions/archive/`。实测:放根目录时,从根目录搜 `docs` 会漏——ripgrep 不读"搜索根之外的祖先目录"里的 `.ignore`,而搜索根本身及其子树里的 `.ignore` 会被读到。
- `.ignore` 不是 git 文件,`archive/` 照常被版本控制。
- 考古用 `rg --no-ignore 关键词`。
- 若 `docs/reviews/` 也是过程记录,在 `docs/` 放一个 `.ignore` 写 `reviews/` 即可——但这是"默认看不见过程记录",要项目自己拍板。

`.vscode/settings.json`(与已有配置合并,不要覆盖):

```json
{
  "search.exclude": {
    "docs/decisions/archive": true,
    "docs/reviews": true
  }
}
```

## 边界(别当成保证)

- **`git grep` 不认 `.ignore`**,也没有排除开关——它照常搜到归档。这是本方案唯一的洞;Agent 默认用 rg,但用 `git grep` 的场合就会漏。
- IDE 全局搜索只认 `search.exclude`;换编辑器要各自配。
- 想 100% 只有一个办法:让字节不在工作区(稀疏检出 / 独立分支)。代价是**连文件名也看不见**,与"先看名、再看细节"的读法相反。

## 消不掉的残留

现役 ADR 正文里提到已退役的术语 / 已废弃的方案——搜那个词,命中一堆**现役**记录。这些是现役记录的正确内容,不能压、不能藏,只能靠第二层(横幅)和第三层(L1 那句解读)。

实测样本:一个 48 条 ADR 的项目搜已退役术语,17 个命中里 15 个在历史文件;只上 `.ignore` 之后,仍有 11 个现役 ADR 命中。

## 检查器

`adr-index.py` 在 `archive/` 有记录、但 `docs/decisions/.ignore` 没写 `archive/` 时报 `adr-no-ignore`(warning,不失败)。这个机制失效时是**静默**的——不报就没人会发现。
