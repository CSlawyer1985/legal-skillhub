# Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm.
#!/usr/bin/env python3
"""二进制模板打包 / 还原 —— 让 skill 能通过 SkillHub 发布。

为什么需要它（2026-09-12 实测）：
  SkillHub 服务端**不接受二进制 Office 模板**。上传 .docx 会返回
  `400 不允许的文件类型`（连不存在的扩展名都没有，服务端只认文本类扩展）。
  佐证：商店上已发布的 element-complaint-filler 与 pandoc，其安装包内均**不含**
  本地版本里的 assets/*.docx。因此二进制模板必须以 **base64 文本**随包分发，
  安装后再还原成 .docx。

两种模式：
  pack    扫描 skill 内的 .docx 模板 → 生成 references/templates-b64.json（含 md5）
  unpack  读取该 json → 还原 .docx 到原位，逐文件校验 md5；**已存在的文件默认跳过**

用法：
  python3 scripts/restore_templates.py pack     [--skill-dir DIR]
  python3 scripts/restore_templates.py unpack   [--skill-dir DIR] [--force]
  python3 scripts/restore_templates.py check    [--skill-dir DIR]   # 只校验，不写文件

注意：
  * pack **不会删除** .docx；发布时由发布流程在副本中移除（本地保留工作副本）。
  * unpack 默认跳过已存在文件，因此对已有模板的本地目录是安全的空操作。
  * **模板统一放在顶层 `assets/`**：Skill 包只允许「根目录/二级目录/文件」两级结构，
    `references/assets/xxx.docx` 这种三级路径会被平台判为「目录层级超限」（2026-09-12 实测）。
"""
import argparse
import base64
import hashlib
import json
import sys
from pathlib import Path

PATTERNS = ("assets/*.docx",)   # 二进制模板统一放顶层 assets/（Skill 包只允许两级目录）
PAYLOAD = "references/templates-b64.json"


def collect(skill_dir: Path):
    files = []
    for pat in PATTERNS:
        files.extend(sorted(skill_dir.glob(pat)))
    return files


def md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def do_pack(skill_dir: Path):
    files = collect(skill_dir)
    if not files:
        sys.exit("❌ 未找到任何 .docx 模板——请确认 assets/ 下存在二进制模板")
    payload = {
        "_readme": "二进制模板的 base64 载体——SkillHub 不接受 .docx，故随包分发此文件；"
                   "安装后用 `python3 scripts/restore_templates.py unpack` 还原。",
        "files": {},
    }
    for f in files:
        rel = str(f.relative_to(skill_dir))
        payload["files"][rel] = {
            "md5": md5(f),
            "bytes": f.stat().st_size,
            "b64": base64.b64encode(f.read_bytes()).decode("ascii"),
        }
        print(f"  + {rel}  ({f.stat().st_size} 字节 → {len(payload['files'][rel]['b64'])} 字符 base64)")
    out = skill_dir / PAYLOAD
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n✅ 已生成 {PAYLOAD}（{len(files)} 个模板，{out.stat().st_size} 字节）")
    return len(files)


def do_unpack(skill_dir: Path, force=False):
    src = skill_dir / PAYLOAD
    if not src.exists():
        sys.exit(f"❌ 找不到 {PAYLOAD}——本 skill 的模板已随包提供，无需还原")
    payload = json.loads(src.read_text(encoding="utf-8"))
    files = payload.get("files", {})
    if not files:
        sys.exit(f"❌ {PAYLOAD} 中没有任何文件")

    need, skipped, bad = [], [], []
    for rel, meta in files.items():
        dst = skill_dir / rel
        if dst.exists():
            if force:
                need.append((dst, rel, meta))
            elif md5(dst) == meta["md5"]:
                skipped.append(rel)
            else:
                bad.append(rel)
        else:
            need.append((dst, rel, meta))

    if bad:
        sys.exit("❌ 下列文件已存在但内容与包内不一致（为避免覆盖你的本地模板，已中止）：\n  - "
                 + "\n  - ".join(bad) + "\n  确认要覆盖请加 --force")

    for dst, rel, meta in need:
        dst.parent.mkdir(parents=True, exist_ok=True)
        data = base64.b64decode(meta["b64"])
        dst.write_bytes(data)
        got = hashlib.md5(data).hexdigest()
        ok = "✅" if got == meta["md5"] else "❌"
        print(f"  {ok} 还原 {rel}（{len(data)} 字节，md5 {got[:8]}）")
        if got != meta["md5"]:
            sys.exit("❌ md5 校验失败，已中止")

    print(f"\n✅ 完成：新还原 {len(need)} 个，已存在跳过 {len(skipped)} 个")
    if skipped:
        print("   跳过（md5 一致）：" + "、".join(skipped))


def do_check(skill_dir: Path):
    src = skill_dir / PAYLOAD
    if not src.exists():
        sys.exit(f"❌ 找不到 {PAYLOAD}")
    payload = json.loads(src.read_text(encoding="utf-8"))
    miss, ok = [], 0
    for rel, meta in payload.get("files", {}).items():
        dst = skill_dir / rel
        if dst.exists() and md5(dst) == meta["md5"]:
            ok += 1
        else:
            miss.append(rel)
    print(f"载体清单 {len(payload.get('files', {}))} 个：就位且一致 {ok} 个")
    if miss:
        print("缺失或不一致：\n  - " + "\n  - ".join(miss))
        print("→ 运行 `python3 scripts/restore_templates.py unpack` 还原")
    else:
        print("✅ 全部模板就位")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("pack", "unpack", "check"))
    ap.add_argument("--skill-dir", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--force", action="store_true", help="unpack 时覆盖已存在且不一致的文件")
    a = ap.parse_args()
    d = Path(a.skill_dir).resolve()
    {"pack": lambda: do_pack(d),
     "unpack": lambda: do_unpack(d, a.force),
     "check": lambda: do_check(d)}[a.mode]()
