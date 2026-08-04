#!/usr/bin/env python3
import argparse, difflib, json

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("old_file")
    ap.add_argument("new_file")
    ap.add_argument("--out", default="contract_diff.md")
    args = ap.parse_args()
    old = open(args.old_file, "r", encoding="utf-8").read().splitlines()
    new = open(args.new_file, "r", encoding="utf-8").read().splitlines()
    diff = difflib.unified_diff(old, new, fromfile=args.old_file, tofile=args.new_file, lineterm="")
    content = "# Contract Diff\n\n```diff\n" + "\n".join(diff) + "\n```\n"
    open(args.out, "w", encoding="utf-8").write(content)
    print(f"Wrote {args.out}")

if __name__ == "__main__":
    main()
