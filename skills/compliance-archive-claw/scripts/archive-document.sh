#!/usr/bin/env bash
# archive-document.sh — 合规制度归档核心脚本
# 依赖: bash, sqlite3, pdftotext(可选), pandoc(可选)

set -euo pipefail

ARCHIVE_ROOT="${ARCHIVE_ROOT:-$HOME/.compliance-archive}"
DB="$ARCHIVE_ROOT/archive.db"

# 初始化数据库
init_db() {
  mkdir -p "$ARCHIVE_ROOT"
  sqlite3 "$DB" <<'SQL'
CREATE TABLE IF NOT EXISTS documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  archive_no TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  version TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT '生效中',
  effective_date TEXT,
  file_path TEXT,
  keywords TEXT,
  created_at TEXT DEFAULT (datetime('now','localtime')),
  updated_at TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS version_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  archive_no TEXT NOT NULL,
  version TEXT NOT NULL,
  status TEXT NOT NULL,
  changed_at TEXT DEFAULT (datetime('now','localtime')),
  changed_by TEXT,
  change_note TEXT
);
CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(archive_no, name, keywords, content='documents', content_rowid='id');
SQL
}

# 生成档案编号
gen_archive_no() {
  local type_code="$1"
  local year
  year=$(date +%Y)
  local last
  last=$(sqlite3 "$DB" "SELECT COUNT(*) FROM documents WHERE archive_no LIKE '${type_code}-${year}-%'")
  printf "%s-%s-%03d" "$type_code" "$year" "$((last + 1))"
}

# 归档新文件
cmd_archive() {
  local file="" type="" version="v1.0" effective_date="" changed_by="${USER:-unknown}" note=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --file) file="$2"; shift 2 ;;
      --type) type="$2"; shift 2 ;;
      --version) version="$2"; shift 2 ;;
      --effective-date) effective_date="$2"; shift 2 ;;
      --by) changed_by="$2"; shift 2 ;;
      --note) note="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  [[ -z "$file" || -z "$type" ]] && { echo "ERROR: --file and --type required"; exit 1; }

  init_db

  # 类型代码映射
  local type_code="REG"
  case "$type" in
    法律法规*) type_code="LAW" ;;
    行业规范*) type_code="STD" ;;
    合同模板*) type_code="TPL" ;;
    操作手册*) type_code="MAN" ;;
  esac

  local name
  name=$(basename "$file")
  local archive_no
  archive_no=$(gen_archive_no "$type_code")

  # 废止同名旧版本
  local old_nos
  old_nos=$(sqlite3 "$DB" "SELECT archive_no FROM documents WHERE name='$name' AND status='生效中'")
  if [[ -n "$old_nos" ]]; then
    sqlite3 "$DB" "UPDATE documents SET status='已废止', updated_at=datetime('now','localtime') WHERE name='$name' AND status='生效中'"
    while IFS= read -r old_no; do
      sqlite3 "$DB" "INSERT INTO version_history(archive_no,version,status,changed_by,change_note) SELECT archive_no,version,'已废止','$changed_by','被 $archive_no 替代' FROM documents WHERE archive_no='$old_no'"
    done <<< "$old_nos"
    echo "已废止旧版本: $old_nos"
  fi

  # 复制文件到档案库
  local dest_dir="$ARCHIVE_ROOT/$type"
  mkdir -p "$dest_dir"
  [[ -f "$file" ]] && cp "$file" "$dest_dir/"

  # 提取关键词（简单实现）
  local keywords="$name $type $version"

  sqlite3 "$DB" "INSERT INTO documents(archive_no,name,type,version,status,effective_date,file_path,keywords) VALUES('$archive_no','$name','$type','$version','生效中','$effective_date','$dest_dir/$name','$keywords')"
  sqlite3 "$DB" "INSERT INTO version_history(archive_no,version,status,changed_by,change_note) VALUES('$archive_no','$version','生效中','$changed_by','$note')"
  sqlite3 "$DB" "INSERT INTO docs_fts(rowid,archive_no,name,keywords) SELECT id,'$archive_no','$name','$keywords' FROM documents WHERE archive_no='$archive_no'"

  echo "✅ 归档成功"
  echo "   档案编号: $archive_no"
  echo "   文件名称: $name"
  echo "   版本: $version"
  echo "   归档路径: $dest_dir/$name"
}

# 全文检索
cmd_search() {
  local keyword=""
  while [[ $# -gt 0 ]]; do
    case "$1" in --keyword) keyword="$2"; shift 2 ;; *) shift ;; esac
  done
  [[ -z "$keyword" ]] && { echo "ERROR: --keyword required"; exit 1; }
  init_db
  echo "🔍 搜索: $keyword"
  sqlite3 -column -header "$DB" \
    "SELECT d.archive_no, d.name, d.type, d.version, d.status, d.effective_date FROM documents d JOIN docs_fts f ON d.id=f.rowid WHERE docs_fts MATCH '$keyword' ORDER BY d.updated_at DESC"
}

# 导出文件清单
cmd_export() {
  local type="" start_date="" end_date=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --type) type="$2"; shift 2 ;;
      --start-date) start_date="$2"; shift 2 ;;
      --end-date) end_date="$2"; shift 2 ;;
      *) shift ;;
    esac
  done
  init_db
  local where="1=1"
  [[ -n "$type" ]] && where="$where AND type LIKE '%$type%'"
  [[ -n "$start_date" ]] && where="$where AND effective_date >= '$start_date'"
  [[ -n "$end_date" ]] && where="$where AND effective_date <= '$end_date'"
  sqlite3 -column -header "$DB" \
    "SELECT archive_no, name, type, version, status, effective_date, file_path FROM documents WHERE $where ORDER BY type, effective_date DESC"
}

# 更新版本
cmd_update_version() {
  local file="" old_version="" changed_by="${USER:-unknown}" note=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --file) file="$2"; shift 2 ;;
      --old-version) old_version="$2"; shift 2 ;;
      --by) changed_by="$2"; shift 2 ;;
      --note) note="$2"; shift 2 ;;
      *) shift ;;
    esac
  done
  init_db
  local name
  name=$(basename "$file")
  sqlite3 "$DB" "UPDATE documents SET status='已废止', updated_at=datetime('now','localtime') WHERE name LIKE '%${name%v*}%' AND version='$old_version' AND status='生效中'"
  echo "✅ 旧版本 $old_version 已标记为废止"
}

# 主入口
CMD="${1:-}"
shift || true
case "$CMD" in
  archive)        cmd_archive "$@" ;;
  search)         cmd_search "$@" ;;
  export)         cmd_export "$@" ;;
  update-version) cmd_update_version "$@" ;;
  *) echo "Usage: $0 {archive|search|export|update-version} [options]"; exit 1 ;;
esac
