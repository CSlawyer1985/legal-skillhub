#!/usr/bin/env python3
"""
ZVec 向量检索 — 本地搜索预构建的 cy_data / cy_templates

用法:
  python scripts/search.py law --query "押金 违约金" --contract-type rental
  python scripts/search.py template --query "租房合同" --type rental

首次运行会自动安装依赖（pip install -r requirements.txt）。
"""
import os
import sys
import subprocess
from pathlib import Path

# ── 自动依赖检查（首次自动安装） ──
_REQUIREMENTS = Path(__file__).resolve().parent.parent / "requirements.txt"
def _ensure_deps():
    try:
        import zvec  # noqa: F401
        import sentence_transformers  # noqa: F401
    except ImportError:
        print("[chinese-contract-drafting] 检测到依赖缺失，正在自动安装...", file=sys.stderr)
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(_REQUIREMENTS), "--quiet"]
        )
        print("[chinese-contract-drafting] ✅ 依赖安装完成", file=sys.stderr)

_ensure_deps()

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

import argparse
import json
from pathlib import Path
import zvec
from sentence_transformers import SentenceTransformer

SKILL_DIR = Path(__file__).resolve().parent.parent
LAW_DB = str(SKILL_DIR / "cy_data")
TEMPLATE_DB = str(SKILL_DIR / "cy_templates")


def search_law(args):
    model = SentenceTransformer("BAAI/bge-small-zh-v1.5")
    collection = zvec.open(args.db_path or LAW_DB)
    query_vec = model.encode(args.query).tolist()
    filter_expr = f"contract_type LIKE '%{args.contract_type}%'" if args.contract_type else None
    results = collection.query(zvec.VectorQuery(field_name="embedding", vector=query_vec), topk=args.topk, filter=filter_expr)
    output = []
    for doc in results:
        output.append({
            "law_name": doc.fields.get("law_name", ""),
            "article_num": doc.fields.get("article_num", ""),
            "full_text": doc.fields.get("full_text", ""),
            "score": round(getattr(doc, "score", 0), 4),
        })
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return output


def search_template(args):
    model = SentenceTransformer("BAAI/bge-small-zh-v1.5")
    collection = zvec.open(args.db_path or TEMPLATE_DB)
    query_vec = model.encode(args.query).tolist()
    filter_expr = None
    if args.type:
        filter_expr = f"contract_type LIKE '%{args.type}%'"
    results = collection.query(zvec.VectorQuery(field_name="embedding", vector=query_vec), topk=args.topk, filter=filter_expr)
    output = []
    for doc in results:
        output.append({
            "filename": doc.fields.get("filename", ""),
            "path": doc.fields.get("path", ""),
            "category": doc.fields.get("category", ""),
            "contract_type": doc.fields.get("contract_type", ""),
            "preview": doc.fields.get("preview", "")[:200],
            "score": round(getattr(doc, "score", 0), 4),
        })
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return output


def main():
    parser = argparse.ArgumentParser(description="ZVec 向量检索（本地知识库）")
    sub = parser.add_subparsers(dest="command")

    law_p = sub.add_parser("law", help="检索法律条款")
    law_p.add_argument("--query", required=True)
    law_p.add_argument("--contract-type", default=None)
    law_p.add_argument("--topk", type=int, default=5)
    law_p.add_argument("--db-path", default=None)

    tpl_p = sub.add_parser("template", help="检索合同模板")
    tpl_p.add_argument("--query", required=True)
    tpl_p.add_argument("--type", default=None)
    tpl_p.add_argument("--topk", type=int, default=5)
    tpl_p.add_argument("--db-path", default=None)

    args = parser.parse_args()
    if args.command == "law":
        search_law(args)
    elif args.command == "template":
        search_template(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
