#!/usr/bin/env bash
# 环境检查 — cross-border-service-tax skill
# 用法: bash setup.sh
set -e

echo "=========================================="
echo "  跨境服务贸易涉税业务 Skill — 环境检查"
echo "=========================================="
echo

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
echo "Skill 目录: $SKILL_DIR"
echo

# Python 检查
PY=""
for cmd in python python3; do
    if command -v $cmd &>/dev/null; then
        ver=$($cmd --version 2>&1)
        # Windows 上 python3 可能是 Microsoft Store stub,检查能否真正执行
        if echo "$ver" | grep -qi "python 3"; then
            PY="$cmd"
            echo "✅ Python: $ver ($cmd)"
            break
        fi
    fi
done
if [ -z "$PY" ]; then
    echo "❌ 未找到可用的 Python 3"
    echo "   Windows 上若 python3 无输出,请用 python"
    exit 1
fi
echo

# 依赖检查
echo "--- 依赖检查 ---"
MISSING=0
$PY -c "import yaml" 2>/dev/null && echo "✅ PyYAML" || { echo "❌ PyYAML 缺失 (pip install pyyaml)"; MISSING=1; }
$PY -c "import docx" 2>/dev/null && echo "✅ python-docx (docx 生成可选)" || echo "⚠️  python-docx 缺失 (docx 生成需要: pip install python-docx) — 可选"

if [ "$MISSING" -ne 0 ]; then
    echo
    echo "❌ 必要依赖缺失,请安装后重试"
    exit 1
fi
echo

# 脚本自检
echo "--- 脚本自检 ---"
$PY "$SKILL_DIR/scripts/tax_calc.py" treaty.lookup --country 新加坡 --income-type royalty >/dev/null 2>&1 \
    && echo "✅ tax_calc.py 运行正常" || echo "❌ tax_calc.py 运行失败"
$PY "$SKILL_DIR/scripts/tax_calc.py" ftc.calc --type direct --foreign-income 1000000 --foreign-tax-paid 200000 >/dev/null 2>&1 \
    && echo "✅ ftc.calc(境外抵免)运行正常" || echo "❌ ftc.calc 运行失败"
$PY "$SKILL_DIR/scripts/postcheck.py" --help >/dev/null 2>&1 \
    || true  # postcheck 无 --help,忽略

# 持续进化闭环自检(2026-08-11 接入)
# 注意:此处不阻断 setup.sh 返回——warning 应被记录但不应阻止 skill 启动
# 若需 CI 门禁,直接跑 "exp_lint --strict" 即可,退出码会被 CI 捕获
echo "--- 持续进化闭环自检 ---"
# 协定税率表时效性
$PY "$SKILL_DIR/scripts/tax_calc.py" treaty.check 2>&1 \
    | python -c "import sys,json;
try:
    d=json.load(sys.stdin)['data']
    s='✅' if d['status']=='fresh' else '⚠️ '
    print(f'{s}treaty.check: 协定税率表 {d[\"months_since_verified\"]} 个月前核实,状态 {d[\"status\"]}({len(d[\"covered_countries\"])} 国)')
except: print('❌ treaty.check 解析失败')"
# 经验库质量门(warning 仅记录,不阻断)
lint_out=$($PY "$SKILL_DIR/scripts/exp_lint.py" 2>&1) || true
if echo "$lint_out" | grep -q "结果: ✅"; then
    echo "✅ exp_lint: 经验库质量门通过(0 error)"
else
    err_count=$(echo "$lint_out" | grep -c "^❌" || echo "0")
    warn_count=$(echo "$lint_out" | grep -c "^⚠️" || echo "0")
    echo "⚠️  exp_lint: 经验库质量门有 $err_count 个 error / $warn_count 个 warning(非阻断,需复核)"
fi
echo

# 结构检查
echo "--- 文件结构检查 ---"
for f in SKILL.md references/指引要点提炼.md references/尽职调查要素清单.md \
         references/税收协定待遇审查指引.md references/纳税申报与税收优惠备案.md \
         references/税率速查表.md scripts/tax_calc.py assets/涉税业务分析报告模板.md; do
    if [ -f "$SKILL_DIR/$f" ]; then
        echo "✅ $f"
    else
        echo "❌ $f 缺失"
    fi
done
echo
echo "=========================================="
echo "  环境检查完成"
echo "=========================================="
