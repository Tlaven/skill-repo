# 检索面:让历史不被关键词撞见

> **问题:** 关键词检索会把已作废的决策一起命中。Agent 打开一段失效记录时,不会自动知道那是哪一年的、还有没有效——这是 stale-document poisoning:检索到过期证据,会让本来答得对的模型答错。目录解决的是"有哪些决策",解决不了"搜出来的是不是现行"——所以历史不进检索面。

## 三层,只有第一层改得了结果

| 层 | 机制 | 覆盖 | 失效场合 |
|---|---|---|---|
| **检索** | `docs/.ignore` 写 `decisions/` 与 `reviews/`;`.vscode/settings.json` 的 `search.exclude` | rg / Claude Code / OpenCode / VS Code / Cursor | `git grep`、`grep -r`、任何不读这两个配置的工具 |
| **命中** | 记录标题下的状态横幅 | 所有工具,前提是文件被打开 | 只读匹配行、不打开文件 |
| **解释** | L1 一行:命中 `docs/decisions` / `docs/reviews` 时那是理由,不是规则 | 所有工具 | L1 没加载(子 agent / 只喂了片段) |

**只有第一层能改变"搜到什么"。** 目录名、`archive/` 的位置、另外写一份索引都改不了 grep 的结果——实测:把文件移进 `archive/`,`rg 关键词 .` 照样命中,目录对内容搜索没有任何意义。

## 第一层怎么配

**默认:整个 `docs/decisions/` 退出检索面。** ADR 是日志,连现役记录也只是「当时的陈述」——关键词命中的 ADR 永远不是现行规则,而是某一年的理由。所以不区分现役 / 归档,整目录排除。

`docs/.ignore`:

```
decisions/
reviews/
```

- **名字层由目录承担**:问"有哪些决策",`ls docs/decisions/`——主目录是现役与在议,`archive/` 是历史;搜索不是入口,也不需要另维护一份清单。
- 考古两种:`rg --no-ignore 关键词`,或 `rg 关键词 docs/decisions`——指定目录时父级 `.ignore` 不生效,这是有意的(指定目录 = 故意查)。
- `.ignore` 不受版本控制,`decisions/` 照常提交。

**最小方案(项目坚持现役 ADR 可搜):只排除 `archive/`**,写在 `docs/decisions/.ignore`:

```
archive/
```

- **必须放在 `docs/decisions/` 里**,不能放仓库根写 `docs/decisions/archive/`——实测放根目录时,从根目录搜 `docs` 会漏(ripgrep 不读搜索根之外的祖先目录里的 `.ignore`)。

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

- **`git grep` 不认 `.ignore`**,也没有排除开关——它照常搜到历史。这是本方案唯一的洞;Agent 默认用 rg,但用 `git grep` 的场合就会漏。
- IDE 全局搜索只认 `search.exclude`;换编辑器要各自配。
- 整目录排除后 `rg --files` 也列不出名字——按名字找用 `ls`。这是有意的:名字层是目录,不是搜索。
- 想 100% 只有一个办法:让字节不在工作区(稀疏检出 / 独立分支)。代价是**连文件名也看不见**,与"先看名、再看细节"的读法相反。

## 残留(只针对最小方案)

只排除 `archive/` 时,现役 ADR 正文里提到已退役的术语仍会被搜到——那是现役记录的正确内容,压不得,只能靠第二层(横幅)与第三层(L1 解读)兜。

整目录排除后这部分一并消失:实测一个 48 条 ADR 的项目,搜一个已退役术语从 17 个命中降到 2 个(只剩现行文档)。
