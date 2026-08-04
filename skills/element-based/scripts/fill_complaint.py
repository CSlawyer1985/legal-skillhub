"""Element-based（要素式起诉状）填充 CLI。"""
import argparse
import json

try:
    import fill_engine as fe
except ImportError as e:
    raise SystemExit(
        "缺少依赖：python-docx。请先安装：\n    python -m pip install python-docx\n"
        f"(原始错误：{e})"
    )


def main(argv=None):
    ap = argparse.ArgumentParser(description="把值表 JSON 填入要素式起诉状模板")
    ap.add_argument("--template", required=True, help="token 化模板 .docx 路径")
    ap.add_argument("--values", required=True, help="值表 JSON 路径（UTF-8）")
    ap.add_argument("--out", required=True, help="输出 .docx 路径")
    args = ap.parse_args(argv)

    with open(args.values, encoding="utf-8") as f:
        values = json.load(f)
    n = fe.fill_document(args.template, values, args.out)
    print(f"filled {n} paragraph(s) -> {args.out}")


if __name__ == "__main__":
    main()
