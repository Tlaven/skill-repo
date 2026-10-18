#!/usr/bin/env bash
# review-backlog.sh — 列出"自上次复核以来"契约文档的变化（零 token，只列清单，不判定）
#
# teach-back 是按需 + 攒批做的。攒批的代价是"复核时要重读多少"；
# 本脚本把它变成"只看 delta"：哪些契约文件变了、哪些不变量/单元编号增删改。
#
# 用法: bash scripts/review-backlog.sh
# 复核完成后: echo "<sha> <yyyy-mm-dd>" > docs/reviews/.last-review
# 退出码恒为 0。

set -u

# 契约面:L1/L2/L4 + 术语表 + 模块文档(模块级不变量住 L3;术语表是复核信号 3 的所在)
CONTRACT="AGENTS.md CLAUDE.md docs/architecture.md docs/core-code.md docs/glossary.md docs/glossary.markdown docs/modules/"
MARKER="docs/reviews/.last-review"

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "[review-backlog] 不是 git 仓库，跳过。"; exit 0; }

head_sha=$(git rev-parse --short HEAD 2>/dev/null)
existing=""
for f in $CONTRACT; do [ -e "$f" ] && existing="$existing $f"; done
[ -z "$existing" ] && { echo "[review-backlog] 未找到契约文件。"; exit 0; }

since=""
[ -f "$MARKER" ] && since=$(head -n1 "$MARKER" 2>/dev/null | awk '{print $1}')

if [ -z "$since" ]; then
  echo "[review-backlog] 还没有复核起点（$MARKER 不存在）——首次按全量列。"
  echo "契约文件:"
  for f in $existing; do echo "  - $f"; done
  echo ""
  echo "复核完成后写入起点:  echo \"$head_sha $(date +%F)\" > $MARKER"
  exit 0
fi

echo "[review-backlog] 自 $since 以来的契约变化（当前 HEAD=$head_sha）："
stat=$(git diff --stat "$since..HEAD" -- $existing 2>/dev/null)
if [ -z "$stat" ]; then echo "  （无变化）"; exit 0; fi
printf '%s\n' "$stat" | sed 's/^/  /'

echo ""
echo "被增删改的编号（复核时只看这些 + 它们引用的上下文）："
hits=$(git diff -U0 "$since..HEAD" -- $existing 2>/dev/null \
  | grep -E '^[+-][^+-].*\b(I-[0-9]+|A-[0-9]+|M[0-9]+-[0-9]+|U-[0-9]+|P-A[0-9]+-[0-9]+)\b' \
  | head -n 80)
if [ -n "$hits" ]; then printf '%s\n' "$hits" | sed 's/^/  /'; else echo "  （未识别到编号变化——仍需人工扫一眼 diff）"; fi

echo ""
echo "复核完成后写入新起点:  echo \"$head_sha $(date +%F)\" > $MARKER"
exit 0
