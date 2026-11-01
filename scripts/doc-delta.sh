#!/usr/bin/env bash
# 这次提交的 md 增减。只报数,不判对错,不阻断。
# 临时:删掉本文件 + .git/hooks/pre-commit 里调用它的那一行即可,别处不依赖它。
set -u

numstat=$(git diff --cached --numstat -- '*.md')
[ -z "$numstat" ] && exit 0

printf '%s\n' "$numstat" | awk -F'\t' '$1!="-"{a+=$1;d+=$2} END{printf "docs: +%d / -%d (net %+d)\n", a, d, a-d}'

printf '%s\n' "$numstat" \
  | awk -F'\t' '$1!="-" && $1-$2 != 0 {printf "%d\t%s\t+%s/-%s\n", $1-$2, $3, $1, $2}' \
  | sort -rn \
  | head -3 \
  | awk -F'\t' '{printf "  %+6s  %s\n", $3, $2}'

exit 0
