#!/usr/bin/env bash
# check-doc-refs.sh — 结构性对账:docs/ 里的死链、未填占位符、标了 N2 却缺「验收」。
# 只做能机器判定的部分;语义一致性交给 teach-back 验证者(references/teach-back-verifier-prompt.md)。
#
# 用法:
#   bash check-doc-refs.sh            # 全量扫 docs/,只提醒(退 0)
#   bash check-doc-refs.sh --strict   # 有发现即退 1(可当门禁)
#
# 从仓库根运行。

set -u
STRICT=0
for a in "$@"; do [ "$a" = "--strict" ] && STRICT=1; done

# 按项目改:文档扩展名(不含点,空格分隔)。默认同时认 .md 与 .markdown。
DOC_EXT="md markdown"

ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$ROOT" || exit 0
if [ ! -d docs ]; then echo "[check-doc-refs] 无 docs/,跳过"; exit 0; fi

# 组装 --include 参数(用数组,避免 * 被 shell 展开)
INC=()
for e in $DOC_EXT; do INC+=("--include=*.$e"); done

# 探测是否真的匹配到文件(否则会静默假阴性)
NFILES=0
for e in $DOC_EXT; do
  n=$(find docs -type f -name "*.$e" 2>/dev/null | wc -l | tr -d ' ')
  NFILES=$((NFILES + n))
done
if [ "$NFILES" -eq 0 ]; then
  echo "[check-doc-refs] 警告:docs/ 下没有匹配 DOC_EXT=\"$DOC_EXT\" 的文件。" >&2
  echo "                 若你的文档用别的扩展名,改脚本顶部的 DOC_EXT。" >&2
  exit 0
fi

found=0

# 1) 死链:docs/ 内 markdown 链接指向的本地目标是否存在
while IFS= read -r hit; do
  [ -z "$hit" ] && continue
  file=${hit%%:*}
  target=$(printf '%s' "$hit" | grep -oE '\]\([^)]+\)' | head -n1 | sed -E 's/^\]\(//; s/\)$//')
  case "$target" in http*|\#*|mailto:*|"") continue ;; esac
  target=${target%%#*}
  [ -z "$target" ] && continue
  # 只看"像路径"的目标(含 / 或 .);形如 `](被拒)` 的标注不是链接,跳过
  case "$target" in */*|*.*) ;; *) continue ;; esac
  d=$(dirname "$file")
  if [ ! -e "$d/$target" ] && [ ! -e "$target" ]; then
    echo "[dead-link] $file -> $target"; found=1
  fi
done <<EOF
$(grep -rno "${INC[@]}" -E '\]\([^)]+\)' docs 2>/dev/null)
EOF

# 2) 未填占位符 / TODO
PH=$(grep -rn "${INC[@]}" -E 'TODO|TBD|与用户对话后填' docs 2>/dev/null)
if [ -n "$PH" ]; then
  echo "[placeholder] docs/ 仍有未填占位符 / TODO:"
  printf '%s\n' "$PH"
  found=1
fi

# 3) 标了 N2 却缺「验收」(兼容 .md / .markdown)
for f in docs/core-code.md docs/core-code.markdown docs/modules/*.md docs/modules/*.markdown; do
  [ -f "$f" ] || continue
  n2=$(grep -c 'novelty=N2' "$f" 2>/dev/null || true)
  acc=$(grep -c '验收' "$f" 2>/dev/null || true)
  : "${n2:=0}"; : "${acc:=0}"
  if [ "$n2" -gt "$acc" ]; then
    echo "[n2-missing-verification] $f: N2 条目 $n2 个,「验收」仅 $acc 处"
    found=1
  fi
done

if [ "$found" = 0 ]; then
  echo "[check-doc-refs] 无结构性发现(扫描 $NFILES 个文档)。"
else
  echo "[check-doc-refs] 以上为结构性提醒;语义一致性请跑 teach-back 验证者。"
  [ "$STRICT" = 1 ] && exit 1
fi
exit 0
