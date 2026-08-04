# ============================================================
# IP管理合规技能包 部署脚本 (Windows PowerShell)
# 依据：ISO 56005:2020 知识产权全流程管控
# 版本：V2.9.0 | 日期：2026-05-31
# 适用：Windows 11 / WorkBuddy 用户
# ============================================================

# --------------------------------------------------
# 配置区域
# --------------------------------------------------
$SkillRoot = "$HOME/.workbuddy/skills"
$SkillName = "ip-management-compliance"
$SkillDir = "$SkillRoot/$SkillName"

# 法规库路径（与 deploy.sh 保持一致）
$LawLibBase = "E:\Resilio Sync助手\法律法规\知识产权法典\中国知识产权\专利"

# 颜色定义
function Log-Info { Write-Host "[INFO] $args" -ForegroundColor Cyan }
function Log-Success { Write-Host "[OK]   $args" -ForegroundColor Green }
function Log-Warn { Write-Host "[WARN] $args" -ForegroundColor Yellow }
function Log-Error { Write-Host "[ERROR] $args" -ForegroundColor Red }

# --------------------------------------------------
# 主流程
# --------------------------------------------------
Write-Host ""
Write-Host "============================================================"
Write-Host "  IP管理合规技能包 部署脚本 (Windows)"
Write-Host "  ISO 56005:2020 知识产权全流程管控"
Write-Host "  版本: V2.9.0"
Write-Host "============================================================"
Write-Host ""

# Step 1: 检查技能根目录
Log-Info "Step 1: 检查技能根目录..."
if (-not (Test-Path $SkillRoot)) {
    New-Item -ItemType Directory -Path $SkillRoot -Force | Out-Null
    Log-Success "目录已创建: $SkillRoot"
} else {
    Log-Success "目录已存在: $SkillRoot"
}

# Step 2: 创建母技能目录结构
Log-Info "Step 2: 创建母技能目录结构..."

$AllDirs = @($SkillDir) + @(
    "$SkillDir/mcp-config",
    "$SkillDir/references",
    "$SkillDir/templates"
)

foreach ($dir in $AllDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Log-Success "已创建: $dir"
    } else {
        Log-Success "已存在: $dir"
    }
}

# Step 3: 检查法规库并复制参考文件
Log-Info "Step 3: 检查并复制参考文件..."

if (Test-Path $LawLibBase) {
    $LawFiles = @{
        "专利审查指南2023版.pdf" = "$SkillDir/references/专利审查指南2023版.pdf"
        "中华人民共和国专利法2020修正.docx" = "$SkillDir/references/中华人民共和国专利法2020修正.docx"
        "专利法实施细则2024修订.docx" = "$SkillDir/references/专利法实施细则2024修订.docx"
    }

    foreach ($src in $LawFiles.Keys) {
        $srcPath = Join-Path $LawLibBase $src
        if (Test-Path $srcPath) {
            Copy-Item $srcPath $LawFiles[$src] -Force
            Log-Success "已复制: $src"
        } else {
            Log-Warn "未找到: $src"
        }
    }
} else {
    Log-Warn "法规库路径不存在: $LawLibBase"
    Log-Info "跳过参考文件复制，请手动放置。"
}

# ISO 56005 标准文件需要手动下载
$IsoFile = "$SkillDir/references/ISO_56005_2020E.pdf"
if (-not (Test-Path $IsoFile)) {
    Log-Warn "ISO_56005_2020E.pdf 不存在，请手动下载后放入 references/ 目录"
}

# Step 4: 验证文件完整性
Log-Info "Step 4: 验证部署完整性..."
Write-Host ""

$ErrorCount = 0

$FilesToCheck = @{
    "$SkillDir/SKILL.md" = "母技能 SKILL.md"
    "$SkillDir/meta.yaml" = "母技能 meta.yaml"
    "$SkillRoot/ip-mgmt-framework/SKILL.md" = "框架搭建(SKILL.md)"
    "$SkillRoot/ip-mgmt-framework/meta.yaml" = "框架搭建(meta.yaml)"
    "$SkillRoot/ip-mgmt-strategy/SKILL.md" = "战略制定(SKILL.md)"
    "$SkillRoot/ip-mgmt-strategy/meta.yaml" = "战略制定(meta.yaml)"
    "$SkillRoot/ip-mgmt-innovation/SKILL.md" = "创新流程(SKILL.md)"
    "$SkillRoot/ip-mgmt-innovation/meta.yaml" = "创新流程(meta.yaml)"
    "$SkillRoot/ip-mgmt-tools/SKILL.md" = "工具方法(SKILL.md)"
    "$SkillRoot/ip-mgmt-tools/meta.yaml" = "工具方法(meta.yaml)"
    "$SkillRoot/ip-mgmt-examination/SKILL.md" = "审查合规(SKILL.md)"
    "$SkillRoot/ip-mgmt-examination/meta.yaml" = "审查合规(meta.yaml)"
    "$SkillRoot/ip-mgmt-risk/SKILL.md" = "风险管理(SKILL.md)"
    "$SkillRoot/ip-mgmt-risk/meta.yaml" = "风险管理(meta.yaml)"
    "$SkillRoot/ip-mgmt-exploitation/SKILL.md" = "商业化(SKILL.md)"
    "$SkillRoot/ip-mgmt-exploitation/meta.yaml" = "商业化(meta.yaml)"
    "$SkillRoot/ip-mgmt-audit/SKILL.md" = "审计评估(SKILL.md)"
    "$SkillRoot/ip-mgmt-audit/meta.yaml" = "审计评估(meta.yaml)"
    "$SkillDir/mcp-config/mcp-rpc.json" = "MCP通信协议"
    "$SkillDir/mcp-config/linkage-rules.yaml" = "联动触发规则"
    "$SkillDir/templates/IP战略制定模板.md" = "IP战略制定模板"
    "$SkillDir/templates/专利申请文件合规检查表.md" = "合规检查表"
    "$SkillDir/templates/IP风险评估矩阵.md" = "风险评估矩阵"
    "$SkillDir/templates/IP许可协议框架.md" = "许可协议框架"
}

foreach ($file in $FilesToCheck.Keys) {
    if (Test-Path $file) {
        Log-Success "$($FilesToCheck[$file])"
    } else {
        Log-Error "缺失: $($FilesToCheck[$file]) ($file)"
        $ErrorCount++
    }
}

Write-Host ""

# Step 5: 部署摘要
Log-Info "Step 5: 部署摘要"
Write-Host ""
Write-Host "============================================================"
Write-Host "  部署摘要"
Write-Host "============================================================"
Write-Host ""
Write-Host "  技能包名称: $SkillName"
Write-Host "  部署路径:   $SkillDir"
Write-Host ""
Write-Host "  独立技能目录（独立部署，位于 skills/ 下）:"
Write-Host "  ├── ip-mgmt-framework/           (IP management Framework/P0)"
Write-Host "  ├── ip-mgmt-strategy/            (IP strategy/P1)"
Write-Host "  ├── ip-mgmt-innovation/         (创新流程/P1)"
Write-Host "  ├── ip-mgmt-tools/              (工具方法/P2)"
Write-Host "  ├── ip-mgmt-examination/         (审查合规/P0)"
Write-Host "  ├── ip-mgmt-risk/              (FTO风险/P0)"
Write-Host "  ├── ip-mgmt-exploitation/       (商业化/P2)"
Write-Host "  └── ip-mgmt-audit/             (审计评价/P1)"
Write-Host ""
Write-Host "  与现有技能的联动:"
Write-Host "  ├── patent-infringement-guide     (双向)"
Write-Host "  └── IMA知识库 (MCP)              (动态检索)"
Write-Host ""

if ($ErrorCount -eq 0) {
    Log-Success "部署完成！所有文件验证通过。"
    Write-Host ""
    Write-Host "  后续操作:"
    Write-Host "  1. 手动下载 ISO_56005_2020E.pdf 放入 references/ 目录"
    Write-Host "  2. 重启 WorkBuddy 使技能生效"
    Write-Host "  3. 使用触发词测试技能激活"
    Write-Host ""
    exit 0
} else {
    Log-Error "部署完成但有 $ErrorCount 个错误，请检查缺失文件。"
    exit 1
}
