# 账本检查器 · 负控留档(2026-10-22)

> **这一轮测的是“检查器自己会不会红”,不是决策质量。**
> 夹具在 `tests/ledger-check/`;原始输出见 `runs.txt`。

## 结果

| 夹具 | 期望 | 实际 | 退出码 |
|---|---|---|---|
| `good.md` | 全绿 | FAIL=0 WARN=0 | 0 |
| `good-retire.md` | 带退役记录的全绿 | FAIL=0 WARN=0 | 0 |
| `bad-missing-action.md` | 缺证伪动作必须红 | `L-FALSIFY-ACT` | 1 |
| `bad-vocab.md` | 动作/层/判据三处红 | `L-FALSIFY-ACT-VOCAB`、`L-LAYER`、`L-JUDGE-VOCAB`,外加载体空 WARN | 1 |
| `bad-retire-unrecorded.md` | 退役未留档、退役条目仍在视图 | `L-RETIRE-RECORD`、`L-VIEW-RETIRED` | 1 |
| `bad-retire-incomplete.md` | 退役记录缺证据/缺替代、视图仍留退役条目 | `L-RETIRE-EVID`、`L-RETIRE-ALT`、`L-VIEW-RETIRED` | 1 |
| `view-overflow.md` | 视图 6 条只 WARN,不红 | `L-VIEW`,FAIL=0 | 0 |

模板自身:`L-PLACEHOLDER` NOTE,FAIL=0,WARN=0,exit 0。

## 覆盖

**条目表:** 表头列名、列数、断言空、证伪条件空、证伪动作四选一(`复跑:` / `对照:` / `盲评:` / `人看:`)、层枚举(`[通用]`/`[本地]`)、判据来源前缀(用户编码/用户确认/AI 自拟/用户裁决)、编号重复(FAIL)、编号未递增(WARN)、状态空(WARN)、载体空(WARN)。

**退役记录:** 表头含「替代」列;每行必须有证据、有替代(写替代 ID 或「无替代」);状态为退役的条目必须有一条退役记录;退役记录引用的条目必须还在账本里。

**视图:** >5 条 WARN;出现已退役条目 FAIL。

## 不覆盖

- **不判对错:** 断言是否成立、判据是否真取过证、视图排序是否合理——这些只有人看/复跑能答。
- **无法检测“编号复用”**:没有历史时只能查重复与递增;真正的复用要靠 git 历史核。
- **单元格里写 `|`** 会被当成列分隔(夹具里已避开);需要转义时应改写措辞。

## 已知局限

- 只测了 Windows PowerShell 5.1 + UTF-8 BOM;macOS/Linux 未测。
- **PS 5.1 把弯引号(“ ”)当字符串定界符**——脚本正文里只能用「」或转义,否则解析错;写脚本时踩过一次。
- 退役形态选了“候选可删、生效必保号”,检查器按此写;若将来改链,`L-RETIRE-*` 四条要重写。
