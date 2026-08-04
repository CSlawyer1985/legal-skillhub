#!/bin/bash
# 一人公司法律顾问 Skill 安装脚本
# 使用方法：bash install.sh

SKILL_NAME="solo-company-legal-advisor"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QCLAW_SKILLS_DIR="$HOME/.qclaw/skills"

echo "========================================="
echo "  一人公司法律顾问 Skill 安装程序"
echo "========================================="
echo ""

# 检测操作系统
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "检测到 Windows 系统"
    QCLAW_SKILLS_DIR="$USERPROFILE/.qclaw/skills"
    echo "目标目录: $QCLAW_SKILLS_DIR"
else
    echo "检测到 Unix/Linux/macOS 系统"
    echo "目标目录: $QCLAW_SKILLS_DIR"
fi

# 创建目标目录
if [ ! -d "$QCLAW_SKILLS_DIR" ]; then
    echo "创建技能目录: $QCLAW_SKILLS_DIR"
    mkdir -p "$QCLAW_SKILLS_DIR"
fi

# 复制 Skill 文件
echo ""
echo "正在安装 Skill..."
if [ -d "$QCLAW_SKILLS_DIR/$SKILL_NAME" ]; then
    echo "⚠️  检测到已存在的 Skill，是否覆盖？(y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        rm -rf "$QCLAW_SKILLS_DIR/$SKILL_NAME"
        echo "已删除旧版本"
    else
        echo "❌ 安装已取消"
        exit 1
    fi
fi

cp -r "$SKILL_DIR" "$QCLAW_SKILLS_DIR/$SKILL_NAME"
echo "✅ Skill 文件已复制到: $QCLAW_SKILLS_DIR/$SKILL_NAME"

# 重启 Gateway（如果已安装 QClaw）
echo ""
echo "是否重启 QClaw Gateway 以加载新 Skill？(y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    if command -v openclaw &> /dev/null; then
        echo "正在重启 Gateway..."
        openclaw gateway restart
        echo "✅ Gateway 已重启"
    else
        echo "⚠️  未检测到 openclaw 命令，请手动重启 Gateway"
    fi
fi

echo ""
echo "========================================="
echo "  ✅ 安装完成！"
echo "========================================="
echo ""
echo "使用方法："
echo "  1. 重启 Gateway 后，Skill 将自动加载"
echo "  2. 在 QClaw 中提问一人公司相关法律问题"
echo "  3. 触发关键词：一人公司、法律顾问、公司章程等"
echo ""
echo "如需卸载："
echo "  rm -rf $QCLAW_SKILLS_DIR/$SKILL_NAME"
echo ""
