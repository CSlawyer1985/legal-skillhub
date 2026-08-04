#!/bin/bash
# smart-contract-reviewer - scripts/validate.sh
# 验证合同审查报告完整性的Bash脚本
# 用法: bash validate.sh <report-file.md>

REPORT_FILE="$1"

if [ -z "$REPORT_FILE" ]; then
    echo "用法: bash validate.sh <报告文件.md>"
    exit 1
fi

if [ ! -f "$REPORT_FILE" ]; then
    echo "❌ FAIL: 文件不存在: $REPORT_FILE"
    exit 1
fi

echo "=========================================="
echo "合同审查报告验证 - smart-contract-reviewer"
echo "=========================================="
echo ""

SCORE=0
TOTAL=10

# 1. 检查基本信息章节
if grep -q "## 基本信息" "$REPORT_FILE"; then
    echo "✅ PASS: 包含'基本信息'章节"
    SCORE=$((SCORE + 1))
else
    echo "❌ FAIL: 缺少'基本信息'章节"
fi

# 2. 检查总体风险评估
if grep -q "总体风险评估\|风险评估" "$REPORT_FILE"; then
    echo "✅ PASS: 包含风险评估内容"
    SCORE=$((SCORE + 1))
else
    echo "❌ FAIL: 缺少风险评估内容"
fi

# 3. 检查风险等级标注（🔴/🟡/🟢）
if grep -qE "🔴|🟡|🟢|高风险|中风险|低风险" "$REPORT_FILE"; then
    echo "✅ PASS: 包含风险等级标注"
    SCORE=$((SCORE + 1))
else
    echo "❌ FAIL: 缺少风险等级标注"
fi

# 4. 检查关键条款审核章节
if grep -q "关键条款\|条款审核\|条款审查" "$REPORT_FILE"; then
    echo "✅ PASS: 包含关键条款审核"
    SCORE=$((SCORE + 1))
else
    echo "❌ FAIL: 缺少关键条款审核"
fi

# 5. 检查修改建议
if grep -q "修改建议\|修改意见\|建议" "$REPORT_FILE"; then
    echo "✅ PASS: 包含修改建议"
    SCORE=$((SCORE + 1))
else
    echo "❌ FAIL: 缺少修改建议"
fi

# 6. 检查法律依据
if grep -q "法律依据\|民法典\|法律" "$REPORT_FILE"; then
    echo "✅ PASS: 包含法律依据"
    SCORE=$((SCORE + 1))
else
    echo "❌ FAIL: 缺少法律依据"
fi

# 7. 检查缺失条款建议
if grep -q "缺失条款\|缺少.*条款\|建议增加" "$REPORT_FILE"; then
    echo "✅ PASS: 包含缺失条款建议"
    SCORE=$((SCORE + 1))
else
    echo "⚠️  WARN: 可能缺少缺失条款建议"
fi

# 8. 检查综合建议
if grep -q "综合建议\|总结建议\|总体建议" "$REPORT_FILE"; then
    echo "✅ PASS: 包含综合建议"
    SCORE=$((SCORE + 1))
else
    echo "❌ FAIL: 缺少综合建议"
fi

# 9. 检查报告是否包含具体条款引用
if grep -qE "条款[0-9]|第[一二三四五六七八九十]+条|Article [0-9]" "$REPORT_FILE"; then
    echo "✅ PASS: 包含具体条款引用"
    SCORE=$((SCORE + 1))
else
    echo "⚠️  WARN: 可能缺少具体条款引用"
fi

# 10. 检查文件大小（报告不应过小）
LINE_COUNT=$(wc -l < "$REPORT_FILE" | tr -d ' ')
if [ "$LINE_COUNT" -gt 30 ]; then
    echo "✅ PASS: 报告长度充足 ($LINE_COUNT 行)"
    SCORE=$((SCORE + 1))
else
    echo "❌ FAIL: 报告过短（仅 $LINE_COUNT 行，建议>30行）"
fi

echo ""
echo "=========================================="
echo "得分: $SCORE/$TOTAL"

if [ "$SCORE" -ge 8 ]; then
    echo "结果: ✅ PASS (得分≥8/10)"
    exit 0
elif [ "$SCORE" -ge 6 ]; then
    echo "结果: ⚠️  PARTIAL (得分6-7/10，需要补充)"
    exit 1
else
    echo "结果: ❌ FAIL (得分<6/10)"
    exit 1
fi
