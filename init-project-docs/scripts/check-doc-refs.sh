#!/usr/bin/env bash
# check-doc-refs.sh — 结构性对账:docs/ 里的死链(含大小写错链:目标存在但大小写不一致,大小写敏感系统上会断)、未填占位符、标了 N2 却缺 `**验收**` / 没有「危险实现清单」、N2 模块缺「失败语义」、危险实现清单行未填(空/占位符)、现状文档引记录、入口文档点具体 ADR 条目。
# Windows:本文件必须以 LF 检出(项目根 `.gitattributes` 加 `*.sh text eol=lf`)——CRLF 在 Linux / WSL / CI 上会直接语法错(Git Bash 多数版本能容忍,但别赌)。
# 只做能机器判定的部分;语义一致性交给 teach-back 验证者(docs-templates/teach-back-verifier-prompt.md)。
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

# 按项目改:对账要**排除**的路径(扩展正则,匹配即跳过)。默认排除"不是本项目当前维护的文档"的那些:
# 存档层(如 docs/legacy/、docs/archive/、docs/experiment/、docs/scaffolds/)、**记录类**
# (docs/decisions/、docs/reviews/——历史快照,引用退役术语 / 旧链接是常态,不是错误)、与
# **待填件目录**(docs/templates/——有些项目把待填件放在 docs/ 内,待填件里的占位符不算本项目
# 当前维护的文档内容)。置空则不过滤。
DOC_EXCLUDE='^(docs/legacy/|docs/archive/|docs/experiment/|docs/scaffolds/|docs/decisions/|docs/templates/|docs/reviews/)'

ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$ROOT" || exit 0
if [ ! -d docs ]; then echo "[check-doc-refs] 无 docs/,跳过"; exit 0; fi

# 组装 --include 参数(用数组,避免 * 被 shell 展开)
INC=()
for e in $DOC_EXT; do INC+=("--include=*.$e"); done

# HTML 注释 + fenced code block 剥离(行数保真;模板引导注释 / 示例代码不算正文)——#3 的计数与 #4 的引用扫描共用
COMMENT_STRIP='
  BEGIN { infence=0 }
  { s=$0; sub(/^[ \t]+/,"",s)
    if (infence) { if (s ~ /^```/ || s ~ /^~~~/) infence=0; print ""; next }
    if (s ~ /^```/ || s ~ /^~~~/) { infence=1; print ""; next }
    buf=$0; line=""
    while (buf != "") {
      if (inc) { i=index(buf,"-->");  if (i==0) { buf=""; break } buf=substr(buf,i+3); inc=0 }
      else     { i=index(buf,"<!--"); if (i==0) { line=line buf; buf=""; break } line=line substr(buf,1,i-1); buf=substr(buf,i+4); inc=1 }
    }
    print line
  }'

# 探测是否真的匹配到文件(否则会静默假阴性);计数按"排除后"口径,与 .ps1 一致
NFILES=0
while IFS= read -r f; do
  [ -z "$f" ] && continue
  if [ -n "$DOC_EXCLUDE" ] && printf '%s' "$f" | grep -Eq "$DOC_EXCLUDE"; then continue; fi
  NFILES=$((NFILES + 1))
done <<EOF
$(for e in $DOC_EXT; do find docs -type f -name "*.$e" 2>/dev/null; done)
EOF
if [ "$NFILES" -eq 0 ]; then
  DEXT_LABEL=".$(printf '%s' "$DOC_EXT" | sed 's/ /,./g')"
  echo "[check-doc-refs] 警告:docs/ 下没有匹配 DocExt=$DEXT_LABEL 的文件。"
  echo '                 若你的文档用别的扩展名,改脚本顶部的 DocExt / DOC_EXT。'
  exit 0
fi

found=0

# 1) 死链:docs/ 内 markdown 链接指向的本地目标是否存在
while IFS= read -r hit; do
  [ -z "$hit" ] && continue
  file=${hit%%:*}
  if [ -n "$DOC_EXCLUDE" ] && printf '%s' "$file" | grep -Eq "$DOC_EXCLUDE"; then continue; fi
  target=$(printf '%s' "$hit" | grep -oE '\]\([^)]+\)' | head -n1 | sed -E 's/^\]\(//; s/\)$//')
  if printf '%s' "$target" | grep -Eqi '^(https?:|#|mailto:)'; then continue; fi
  target=${target%%#*}
  [ -z "$target" ] && continue
  # 只看"像路径"的目标(含 / 或 .);形如 `](被拒)` 的标注不是链接,跳过
  case "$target" in */*|*.*) ;; *) continue ;; esac
  # 存在性之后再做字面大小写比对:大小写不敏感文件系统(Windows/默认 macOS)会放过
  # 错大小写链接,在大小写敏感系统(Linux CI)上会断。find|sed|grep -qFx = 字面精确匹配
  # (GNU/BSD find 都不吃 quoting 坑;ls 在 GNU 管道输出会给含空格名加引号,故不用)。
  d=$(dirname "$file")
  exact=0; casehit=0
  # 根相对链接(/docs/…):从仓库根解析(与 .ps1 的 Join-Path $root 对齐)
  CANDS=("$d/$target" "$target")
  case "$target" in /*) CANDS+=("$ROOT$target");; esac
  for p in "${CANDS[@]}"; do
    if [ -e "$p" ]; then
      if find "$(dirname "$p")" -maxdepth 1 2>/dev/null | sed -e 's|.*/||' | grep -qFx -- "$(basename "$p")"; then
        exact=1
      else
        casehit=1
      fi
    fi
  done
  if [ "$exact" = 0 ] && [ "$casehit" = 1 ]; then
    echo "[case-mismatch] $file -> $target(目标存在但大小写不一致,大小写敏感系统上会断)"; found=1
  elif [ "$exact" = 0 ]; then
    echo "[dead-link] $file -> $target"; found=1
  fi
done <<EOF
$(grep -rno "${INC[@]}" -E '\]\([^)]+\)' docs 2>/dev/null)
EOF

# 2) 未填占位符 / TODO
PH=$(grep -rni "${INC[@]}" -E 'TODO|TBD|与用户对话后填|novelty=N[?]|未填写|待补充' docs 2>/dev/null)
[ -n "$DOC_EXCLUDE" ] && PH=$(printf '%s\n' "$PH" | grep -Evi "$DOC_EXCLUDE")
if [ -n "$PH" ]; then
  echo "[placeholder] docs/ 仍有未填占位符 / TODO:"
  printf '%s\n' "$PH" | sed 's/^/  /'
  found=1
fi

# 3) 标了 N2 却缺 `**验收**` / 没有「危险实现清单」;N2 模块缺「失败语义」(共用同一批文件与剥注释后的 body)
#    先剥掉 HTML 注释——模板里的引导文字本身含这些词,不剥会把计数算花(假阴性)。
#    「危险实现清单」这条要求出自 module-doc 模板(N2 必须给"步骤级说明 + 危险实现清单 + 例子 + 验收 + 失败语义")。
#    没有"指针形"豁免:跨模块 N2 的正文与 novelty=N2 只写在承载它的那份里;模块文档不声明、也不写
#    "验收见 docs/…"的指针行——所以"只声明、不写正文"的形态不该存在。
#    边界(如实说):它数的是**短语出现**,不是"那一节在不在一句话之上"——短语出现在正文别处会漏报。
# 按项目改:若项目改了 L2 文件名(如 architecture-l2.md),把实际名字加进这一行。
# N2 的家 = L2 的「N2 单元规格」节(跨模块)与模块 L3(模块内);L4 core-analysis 是阅读视图,不再扫。
# 模块文档顶部的 novelty= 是模块档位(五件套上移 L2 后仍是 N2),不表示规格住在这里;
# 模块侧改用「危险实现清单」判"本文件是否承载五件套"——承载了才要求验收与失败语义。
for f in docs/architecture.md docs/architecture.markdown docs/modules/*.md docs/modules/*.markdown; do
  [ -f "$f" ] || continue
  body=$(awk "$COMMENT_STRIP" "$f")
  # grep -o|wc -l 数"次数"(grep -c 数"行"——一行多个标记会漏计,n2 偏低即漏报);
  # 语义对齐 .ps1 版的 [regex]::Matches().Count。
  n2=$(printf '%s\n' "$body" | grep -o 'novelty=N2' 2>/dev/null | wc -l | tr -d ' ')
  acc=$(printf '%s\n' "$body" | grep -o '\*\*验收\*\*' 2>/dev/null | wc -l | tr -d ' ')
  dan=$(printf '%s\n' "$body" | grep -o '危险实现清单' 2>/dev/null | wc -l | tr -d ' ')
  : "${n2:=0}"; : "${acc:=0}"; : "${dan:=0}"
  case "$f" in
    docs/modules/*)
      if [ "$dan" -gt 0 ] && [ "$acc" -eq 0 ]; then
        echo "[n2-missing-verification] $f: 本文件承载五件套(含「危险实现清单」),但没有 \`**验收**\` 行"
        found=1
      fi
      if [ "$dan" -gt 0 ] && ! printf '%s\n' "$body" | grep -q '失败语义'; then
        echo "[module-missing-failure-semantics] $f: 承载五件套的模块文档没有「失败语义」一节"
        found=1
      fi
      continue ;;
  esac
  if [ "$n2" -gt "$acc" ]; then
    echo "[n2-missing-verification] $f: N2 条目 $n2 个,「**验收**」仅 $acc 处"
    found=1
  fi
  # 标了 N2 却没有「危险实现清单」(没有指针形豁免)
  if [ "$n2" -gt 0 ] && [ "$dan" -eq 0 ]; then
    echo "[n2-missing-checklist] $f: 标了 N2 却没有「危险实现清单」"
    found=1
  fi
done

# 4) 现状文档里出现指向"记录类文档"的引用
#    规则(E-1):引用只指稳定代号,不指位置。条款代号(`D-14` / `A-1` / `E-4`)可以引;
#    记录类(ADR / `docs/decisions/` / `docs/reviews/`)不引——记录会过期,条款不会。
#    活文档里唯一允许出现记录类目录的地方,是入口文档的「活文档索引」那张表的目录级行;
#    正文里零容忍——依据、`> 出处：` 行、记录编号都算;具体 ADR 条目另由 4b) 检查。
#    按项目改:LIVE_DOCS = 现状 / 规则类文档(默认 L2 是 docs/architecture.md;L2 改名或另有现状类文档时加进来)。
LIVE_DOCS="docs/architecture.md docs/architecture.markdown docs/design-contract.md docs/glossary.md docs/glossary.markdown"
REF_PAT='docs/decisions/|docs/reviews/|ADR-[0-9]{3}|adr-[0-9]{3}-'
for f in $LIVE_DOCS docs/architecture.md docs/architecture.markdown docs/modules/*.md docs/modules/*.markdown; do
  [ -f "$f" ] || continue
  # 先剥 HTML 注释(引导注释里的示例引用不算正文;与 #3 同一套状态机,行号保真)。
  # 不再跳过 `⚠` 行 / `> 出处：` 行——那两种写法已退役,命中即报。
  LREF=$(awk "$COMMENT_STRIP" "$f" 2>/dev/null | awk '{printf "%d:%s\n", NR, $0}' | grep -iE "$REF_PAT" 2>/dev/null)
  if [ -n "$LREF" ]; then
    printf '%s\n' "$LREF" | while IFS= read -r l; do
      echo "[live-doc-refs] $f:$l: 现状类文档引了记录类文档(记录会过期,条款不会;引条款请用稳定代号,如 D-14;要理由/被拒方案,从 L1 的活文档索引进)"
    done
    found=1
  fi
done

# 4b) 入口文档(L1)里出现指向**具体** ADR 条目的引用
#    规则(E-1):L1 的活文档索引可以写"为什么这么定 / 被拒方案 → docs/decisions/"(目录级),但不得点条目。
#    例外只有一个:`adr-000-template` 这类模板文件名不是决策(跳过 000)。
#    按项目改:L1 的宿主文件名(存在的才查)。
for f in AGENTS.md CLAUDE.md .cursor/rules/project.mdc .windsurfrules .github/copilot-instructions.md; do
  [ -f "$f" ] || continue
  L1REF=$(grep -inE 'ADR-[0-9]{3}|adr-[0-9]{3}' "$f" 2>/dev/null | grep -vE 'ADR-000|adr-000')
  if [ -n "$L1REF" ]; then
    printf '%s\n' "$L1REF" | while IFS= read -r l; do
      echo "[l1-entry-ref] $f:$l: 入口文档点了具体 ADR 条目(索引只写『哪份文档管什么』,不点条目)"
    done
    found=1
  fi
done

# 5) 危险实现清单的行级粗检:数据行的「挡住者」列要有内容、不能是占位符
#    列位置由表头定位(找含"挡住"的那一列;表头没有这一列 → 不猜、不报),因此**不看列数与写法**——
#    填完的文档会演化出两列 / 四列等不同形状,判据只认"这一格填没填"。
#    起始形态:标题(`### 危险实现清单…`)或粗体(`**危险实现清单**——`,含 `- ` 前缀);
#    表结束(表开始后的第一个非表行)即停止——避免把同节后续的普通表格算进来。
#    机器只查"填没填";写法是否真挡得住仍是 teach-back 验证者的事
for f in docs/architecture.md docs/architecture.markdown docs/modules/*.md docs/modules/*.markdown; do
  [ -f "$f" ] || continue
  DB=$(awk "$COMMENT_STRIP" "$f" 2>/dev/null | awk -F'|' '
    /^#+[[:space:]]*\**危险实现清单/ || /^([[:space:]]*-[[:space:]]+)?\*\*危险实现清单/ { insec=1; intab=0; bcol=0; next }
    !insec { next }
    /^#/ { insec=0; intab=0; bcol=0; next }
    /^\|/ {
      if (!intab) {                                    # 表头行:定位"挡住者"列
        intab=1; bcol=0
        for (i=2; i<=NF; i++) if ($i ~ /挡住/) { bcol=i; break }
        next
      }
      if (bcol == 0) next                              # 表头没有"挡住"列 → 不猜
      if ($0 ~ /^\|[[:space:]:|-]+\|[[:space:]]*$/) next   # 分隔行
      cell=(bcol <= NF) ? $bcol : ""; lc=tolower(cell); gsub(/^[[:space:]]+|[[:space:]]+$/, "", lc)
      if (lc == "" || lc ~ /^(-|—|待补|tbd|todo|\?|n\/a)$/)
        printf "%d:%s\n", FNR, $0
      next
    }
    { if (intab) { insec=0; intab=0; bcol=0 } }        # 表后首个非表行 → 结束
  ')
  if [ -n "$DB" ]; then
    printf '%s\n' "$DB" | while IFS= read -r l; do
      echo "[danger-blocker] $f:$l: 危险实现清单行未填(\"挡住者\"列为空 / 占位符)"
    done
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
