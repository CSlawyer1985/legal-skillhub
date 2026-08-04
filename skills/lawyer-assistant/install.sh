#!/bin/bash
# 律师助手技能安装脚本

echo "🔧 正在安装律师助手技能..."

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 创建技能目录（如果不存在）
SKILL_DIR="$HOME/.openclaw/skills/lawyer-assistant"
mkdir -p "$SKILL_DIR"

# 复制技能文件
echo "📁 复制技能文件..."
cp "$SCRIPT_DIR/SKILL.md" "$SKILL_DIR/"
cp "$SCRIPT_DIR/lawyer_assistant.py" "$SKILL_DIR/"

# 添加执行权限
chmod +x "$SKILL_DIR/lawyer_assistant.py"

echo "✅ 律师助手技能安装完成！"
echo ""
echo "📍 技能位置：$SKILL_DIR"
echo ""
echo "📖 使用方法："
echo "在对话中提供案件信息，包括："
echo "  - 当事人信息"
echo "  - 对手信息"
echo "  - 纠纷类型"
echo "  - 案件起因"
echo "  - 诉讼诉求"
echo "  - 现有证据（如有）"
echo ""
echo "示例："
echo "  请帮我分析这个案件："
echo "  - 当事人：张三"
echo "  - 对手：李四"
echo "  - 纠纷类型：借款合同纠纷"
echo "  - 起因：2023 年 1 月李四向张三借款 10 万元，约定 2023 年 12 月归还，至今未还"
echo "  - 诉求：要求归还本金及利息"
echo ""
echo "⚠️ 免责声明：本技能仅供参考，不构成正式法律意见。复杂案件请咨询执业律师。"
