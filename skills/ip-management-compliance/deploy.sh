#!/bin/bash
# ============================================================
# ⚠️  注意：此脚本适用于 Linux/WSL/macOS CI 环境
# Windows 用户请使用同目录下的 deploy.ps1
# ============================================================

# ============================================================
# IP管理合规技能包 部署脚本
# 依据：ISO 56005:2020 知识产权全流程管控
# 版本：V2.9.0 | 日期：2026-05-31
# ============================================================

set -e

# ============================================================
# 配置区域
# ============================================================

# 技能根目录（WorkBuddy用户级技能目录）
SKILL_ROOT="$HOME/.workbuddy/skills"
# 技能包名称
SKILL_NAME="ip-management-compliance"
# 技能包完整路径
SKILL_DIR="${SKILL_ROOT}/${SKILL_NAME}"

# 法规库路径（Windows/WSL环境）
LAW_LIB_BASE="/mnt/e/Resilio Sync助手/法律法规/知识产权法典/中国知识产权/专利"
# 注意：在纯Windows环境下需要替换路径

# ============================================================
# 颜色定义
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================
# 辅助函数
# ============================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dir() {
    if [ -d "$1" ]; then
        log_success "目录已存在: $1"
        return 0
    else
        return 1
    fi
}

create_dir() {
    if mkdir -p "$1"; then
        log_success "目录已创建: $1"
        return 0
    else
        log_error "目录创建失败: $1"
        return 1
    fi
}

# ============================================================
# 主流程
# ============================================================

echo "============================================================"
echo "  IP管理合规技能包 部署脚本"
echo "  ISO 56005:2020 知识产权全流程管控"
echo "  版本: V2.9.0"
echo "============================================================"
echo ""

# Step 1: 检查/创建技能根目录
log_info "Step 1: 检查技能根目录..."
if ! check_dir "${SKILL_ROOT}"; then
    create_dir "${SKILL_ROOT}"
fi
echo ""

# Step 2: 创建母技能包主目录结构
log_info "Step 2: 创建母技能包目录结构..."

DIRS=(
    "${SKILL_DIR}"
    "${SKILL_DIR}/mcp-config"
    "${SKILL_DIR}/references"
    "${SKILL_DIR}/templates"
)

for dir in "${DIRS[@]}"; do
    create_dir "${dir}"
done
echo ""

# Step 3: 复制参考文件（如法规库存在）
log_info "Step 3: 检查并复制参考文件..."

if [ -d "${LAW_LIB_BASE}" ]; then
    # 专利审查指南2023版
    if [ -f "${LAW_LIB_BASE}/专利审查指南2023版.pdf" ]; then
        cp "${LAW_LIB_BASE}/专利审查指南2023版.pdf" \
           "${SKILL_DIR}/references/专利审查指南2023版.pdf"
        log_success "已复制: 专利审查指南2023版.pdf"
    else
        log_warn "未找到: 专利审查指南2023版.pdf"
    fi

    # 专利法2020修正
    if [ -f "${LAW_LIB_BASE}/中华人民共和国专利法2020修正.docx" ]; then
        cp "${LAW_LIB_BASE}/中华人民共和国专利法2020修正.docx" \
           "${SKILL_DIR}/references/中华人民共和国专利法2020修正.docx"
        log_success "已复制: 中华人民共和国专利法2020修正"
    else
        log_warn "未找到: 中华人民共和国专利法2020修正"
    fi

    # 专利法实施细则2024修订
    if [ -f "${LAW_LIB_BASE}/中华人民共和国专利法实施细则2023年12月11日修订-2024年1月20日实行.docx" ]; then
        cp "${LAW_LIB_BASE}/中华人民共和国专利法实施细则2023年12月11日修订-2024年1月20日实行.docx" \
           "${SKILL_DIR}/references/专利法实施细则2024修订.docx"
        log_success "已复制: 专利法实施细则2024修订"
    else
        log_warn "未找到: 专利法实施细则2024修订"
    fi
else
    log_warn "法规库路径不存在: ${LAW_LIB_BASE}"
    log_info "跳过参考文件复制，请手动放置。"
fi

# ISO 56005 标准文件需要手动下载
if [ ! -f "${SKILL_DIR}/references/ISO_56005_2020E.pdf" ]; then
    log_warn "ISO_56005_2020E.pdf 不存在，请手动下载后放入 references/ 目录"
fi
echo ""

# Step 4: 验证文件完整性
log_info "Step 4: 验证部署完整性..."
echo ""

ERRORS=0

# 母技能文件
FILES_TO_CHECK=(
    "${SKILL_DIR}/SKILL.md:母技能SKILL.md"
    "${SKILL_DIR}/meta.yaml:母技能meta.yaml"
    "${SKILL_ROOT}/ip-mgmt-framework/SKILL.md:框架搭建-SKILL.md"
    "${SKILL_ROOT}/ip-mgmt-framework/meta.yaml:框架搭建-meta.yaml"
    "${SKILL_ROOT}/ip-mgmt-strategy/SKILL.md:战略制定-SKILL.md"
    "${SKILL_ROOT}/ip-mgmt-strategy/meta.yaml:战略制定-meta.yaml"
    "${SKILL_ROOT}/ip-mgmt-innovation/SKILL.md:创新流程-SKILL.md"
    "${SKILL_ROOT}/ip-mgmt-innovation/meta.yaml:创新流程-meta.yaml"
    "${SKILL_ROOT}/ip-mgmt-tools/SKILL.md:工具方法-SKILL.md"
    "${SKILL_ROOT}/ip-mgmt-tools/meta.yaml:工具方法-meta.yaml"
    "${SKILL_ROOT}/ip-mgmt-examination/SKILL.md:审查合规-SKILL.md"
    "${SKILL_ROOT}/ip-mgmt-examination/meta.yaml:审查合规-meta.yaml"
    "${SKILL_ROOT}/ip-mgmt-risk/SKILL.md:风险管理-SKILL.md"
    "${SKILL_ROOT}/ip-mgmt-risk/meta.yaml:风险管理-meta.yaml"
    "${SKILL_ROOT}/ip-mgmt-exploitation/SKILL.md:商业化-SKILL.md"
    "${SKILL_ROOT}/ip-mgmt-exploitation/meta.yaml:商业化-meta.yaml"
    "${SKILL_ROOT}/ip-mgmt-audit/SKILL.md:审计评估-SKILL.md"
    "${SKILL_ROOT}/ip-mgmt-audit/meta.yaml:审计评估-meta.yaml"
    "${SKILL_DIR}/mcp-config/mcp-rpc.json:MCP通信协议"
    "${SKILL_DIR}/mcp-config/linkage-rules.yaml:联动触发规则"
    "${SKILL_DIR}/templates/IP战略制定模板.md:IP战略制定模板"
    "${SKILL_DIR}/templates/专利申请文件合规检查表.md:合规检查表"
    "${SKILL_DIR}/templates/IP风险评估矩阵.md:风险评估矩阵"
    "${SKILL_DIR}/templates/IP许可协议框架.md:许可协议框架"
)

for entry in "${FILES_TO_CHECK[@]}"; do
    IFS=':' read -r filepath desc <<< "${entry}"
    if [ -f "${filepath}" ]; then
        log_success "${desc}"
    else
        log_error "缺失: ${desc} (${filepath})"
        ERRORS=$((ERRORS + 1))
    fi
done
echo ""

# Step 5: 部署摘要
log_info "Step 5: 部署摘要"
echo ""
echo "============================================================"
echo "  部署摘要"
echo "============================================================"
echo ""
echo "  技能包名称: ${SKILL_NAME}"
echo "  部署路径:   ${SKILL_DIR}"
echo ""
echo "  目录结构:"
echo "  ├── core-skill/          (母技能)"
echo "  │   ├── SKILL.md         ✓"
echo "  │   └── meta.yaml        ✓"
echo "  ├── 8个独立技能  (位于 \$SKILL_ROOT/ 下)"
echo "  │   ├── ip-mgmt-framework/           ✓"
echo "  │   ├── ip-mgmt-strategy/            ✓"
echo "  │   ├── ip-mgmt-innovation/         ✓"
echo "  │   ├── ip-mgmt-tools/              ✓"
echo "  │   ├── ip-mgmt-examination/        ✓"
echo "  │   ├── ip-mgmt-risk/              ✓"
echo "  │   ├── ip-mgmt-exploitation/       ✓"
echo "  │   └── ip-mgmt-audit/             ✓"
echo "  ├── mcp-config/          (MCP联动配置)"
echo "  │   ├── mcp-rpc.json     ✓"
echo "  │   └── linkage-rules.yaml ✓"
echo "  ├── references/          (基准参考文件)"
echo "  │   └── [见README.md]"
echo "  └── templates/           (实务模板)"
echo "      ├── IP战略制定模板.md            ✓"
echo "      ├── 专利申请文件合规检查表.md      ✓"
echo "      ├── IP风险评估矩阵.xlsx/.md       ✓"
echo "      └── IP许可协议框架.md            ✓"
echo ""
echo "  与现有技能的联动:"
echo "  ├── patent-infringement-guide     (双向)"
echo "  └── IMA知识库 (MCP)               (动态检索)"
echo ""

if [ ${ERRORS} -eq 0 ]; then
    log_success "部署完成！所有文件验证通过。"
    echo ""
    echo "  后续操作:"
    echo "  1. 手动下载 ISO_56005_2020E.pdf 放入 references/ 目录"
    echo "  2. 重启 WorkBuddy 使技能生效"
    echo "  3. 使用触发词测试技能激活"
    echo ""
    exit 0
else
    log_error "部署完成但有 ${ERRORS} 个错误，请检查缺失文件。"
    exit 1
fi
