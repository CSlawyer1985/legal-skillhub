#!/bin/bash
# 法律数据库自动更新脚本
# 功能：从 GitHub 拉取最新数据，重新导入到 Meilisearch

set -e

# 配置
DATA_DIR="data/full_laws_markdown"
REPO_URL="https://github.com/AdamBear/laws-markdown.git"
LOG_FILE="update_log_$(date +%Y%m%d).log"

echo "====== 法律数据库自动更新开始 ======"
echo "开始时间: $(date)"
echo "日志文件: $LOG_FILE"
echo ""

# 进入项目目录
cd "$(dirname "$0")"

# 检查是否已经克隆
if [ ! -d "$DATA_DIR/.git" ]; then
    echo "⚠️  数据目录不存在，正在克隆..."
    git clone "$REPO_URL" "$DATA_DIR"
else
    echo "✅ 数据目录已存在，正在拉取最新更新..."
    cd "$DATA_DIR"
    git pull
    cd ..
fi

echo ""
echo "📊 数据拉取完成，统计文件数量:"
find "$DATA_DIR/content" -name "*.md" | wc -l

echo ""
echo "🚀 开始导入数据到 Meilisearch..."
python3 utils/import_adambear.py --data-dir="$DATA_DIR/content"

echo ""
echo "✅ 导入完成！"
echo "结束时间: $(date)"
echo "====== 更新完成 ======"

# 记录日志
echo "更新完成于 $(date)" > "$LOG_FILE"
