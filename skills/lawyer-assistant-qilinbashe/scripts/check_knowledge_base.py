# -*- coding: utf-8 -*-
"""
check_knowledge_base.py —— 外置法律法规知识库安装校验

背景：
    技能包按「核心轻量化」原则，将 5 部重资料（离线法条全集 / 省域司法指引全集 /
    案例库全集 / 使用手册全集 / 相关法规汇编）外置到「法律法规知识库」，
    不随 SkillHub 包携带。安装环境需先注入知识库，本技能相关能力才完整可用。

用法：
    python check_knowledge_base.py [--kb-dir 知识库根目录]

    不传 --kb-dir 时，自动探测常见位置：
      ~/.workbuddy/skills/qilinbashe__skillhub/知识库
      ~/.hermes/knowledge/legal
      <技能包目录>/../知识库

输出：
    每部外置资料的注入状态（已注入 / 缺失），缺失时给出影响范围与补救建议。
    全部注入 -> exit 0；存在缺失 -> exit 1（提示但不阻断）。

说明：
    本脚本只做「存在性 + 规模」校验，不校验内容深度；
    详细清单见 README「安装前置条件」章节。
"""
import os
import sys
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

# 5 部外置重资料（PRECHECK「重资料已外置」条目对应的合并全集）
KB_ITEMS = [
    {
        "name": "离线法条全集",
        "file": "离线法条精华.md",
        "min_size": 50_000,
        "impact": "离线降级 / MCP 不可用时的法条兜底",
    },
    {
        "name": "省域司法指引全集",
        "file": "省域司法指引.md",
        "min_size": 30_000,
        "impact": "区域化裁判口径 / 地域指引能力",
    },
    {
        "name": "案例库全集",
        "file": "案例库.md",
        "min_size": 30_000,
        "impact": "律师助手.md 实操 case-library（12 个案例）",
    },
    {
        "name": "使用手册全集",
        "file": "使用手册.md",
        "min_size": 20_000,
        "impact": "QUICKSTART / 深度模式引导",
    },
    {
        "name": "相关法规汇编",
        "file": "相关法规汇编.md",
        "min_size": 50_000,
        "impact": "跨领域法规检索（刑事/行政/破产联动）",
    },
]


def probe_kb_dirs(src_dir):
    """探测候选知识库目录。"""
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(src_dir, "知识库"),
        os.path.join(src_dir, "..", "知识库"),
        os.path.join(home, ".workbuddy", "skills", "qilinbashe__skillhub", "知识库"),
        os.path.join(home, ".hermes", "knowledge", "legal"),
        os.path.join(home, "Desktop", "法律专家", "知识库"),
    ]
    return [os.path.abspath(p) for p in candidates]


def main():
    src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kb_dir = None
    if "--kb-dir" in sys.argv:
        idx = sys.argv.index("--kb-dir")
        if idx + 1 < len(sys.argv):
            kb_dir = os.path.abspath(sys.argv[idx + 1])

    if kb_dir is None:
        for cand in probe_kb_dirs(src):
            if os.path.isdir(cand):
                kb_dir = cand
                break

    if kb_dir is None or not os.path.isdir(kb_dir):
        print("❌ 未找到法律法规知识库目录。")
        print("   候选位置均已探测：")
        for cand in probe_kb_dirs(src):
            print("     - %s" % cand)
        print("   请先按 README「安装前置条件」注入 5 部重资料，或用 --kb-dir 指定。")
        sys.exit(1)

    print("知识库目录: %s\n" % kb_dir)
    missing = []
    ok_count = 0
    for item in KB_ITEMS:
        fp = os.path.join(kb_dir, item["file"])
        if os.path.exists(fp):
            size = os.path.getsize(fp)
            ok = size >= item["min_size"]
            status = "✅ 已注入(%d KB)" % (size // 1024) if ok else \
                     "⚠️ 存在但过小(%d KB, 建议≥%d KB)" % (size // 1024, item["min_size"] // 1024)
            if ok:
                ok_count += 1
            else:
                missing.append(item["name"])
        else:
            status = "❌ 缺失"
            missing.append(item["name"])
        print("  %s: %s" % (item["name"], status))
        if status.startswith(("❌", "⚠️")):
            print("     影响: %s" % item["impact"])

    print("\n%s/5 部已注入" % ok_count)
    if missing:
        print("缺失: %s" % ", ".join(missing))
        print("提示: 缺失部对应能力将降级（不影响技能包本体加载），注入后重跑本脚本确认。")
        sys.exit(1)
    print("✅ 知识库完整，全部能力可用。")
    sys.exit(0)


if __name__ == "__main__":
    main()
