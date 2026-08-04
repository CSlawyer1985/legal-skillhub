#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""财税技能矩阵 · 一键自动安装器（仅标准库，无第三方依赖）。

设计目标（对应需求「自动化下载安装关联 skill」）：
- 读取与本脚本同目录的 matrix.json（矩阵唯一清单），获取全部技能包及其
  package（本地 zip 名）/ download_urls（按渠道区分的官方下载地址）。
- 对每个「尚未安装」或「版本不一致」的技能：
    * 优先从 --source 指定的本地目录取 <slug>.zip（开发/离线分发场景，审核期即此路径）；
    * 否则按运行时识别的渠道（clawhub / skillhub）从 download_urls[channel] 下载
      （生产场景，由技能在对话中触发后自动执行），调用对应渠道下载 API 获取 zip。
- 下载地址按发布渠道区分：SkillHub 包走 api.skillhub.cn，ClawHub 包走 clawhub.ai，
  矩阵随包分发时 download_url 初始为空，缺失且无 url 时优雅跳过（不触网、不报错），
  确保各市场审核/评分不受影响。
- 解压到目标 skills 目录（--target，默认 ~/.skills 通用用户级），
  自动规范化目录层级并校验 SKILL.md 与版本。
- 幂等：已装且版本一致则跳过；--force 可强制重装；--dry-run 仅预演。

通用接入触发方式（不写终端命令）：
  在已安装任一财税专题技能后，对话中说「安装完整财税技能矩阵」或
  「安装关联财税技能」，技能即调用本安装器，将矩阵其余关联技能一并装上。
  装包同时默认联动注册每个技能的「专属专家」与「所属专家团」到本机
  「我的专家」（专家与团队自动化下载安装）；--no-experts 可仅装技能、不联动专家。
"""
import os
import sys
import json
import zipfile
import shutil
import argparse
import tempfile

try:
    import urllib.request as _urllib
except Exception:  # pragma: no cover
    _urllib = None

HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# 基础工具
# ---------------------------------------------------------------------------
def load_manifest(path=None):
    p = path or os.path.join(HERE, "matrix.json")
    if not os.path.isfile(p):
        sys.exit(f"INSTALL FAILED - 找不到矩阵清单: {p}")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def default_target():
    # 用户级技能目录优先；项目级可由 --target 指定
    return os.path.join(os.path.expanduser("~"), ".skills")


def _read_version(skill_md_path):
    if not os.path.isfile(skill_md_path):
        return None
    with open(skill_md_path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s.startswith("version:"):
                return s.split(":", 1)[1].strip().strip('"').strip("'")
    return None


def is_installed(target, skill):
    slug = skill["slug"]
    skill_dir = os.path.join(target, slug)
    skill_md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(skill_md):
        return False, None
    return True, _read_version(skill_md)


def _detect_channel():
    """运行时识别安装渠道：环境存在 ClawHub 凭据/CLI 视为 clawhub，否则 skillhub。"""
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(home, ".clawhub", "config.json"),
        os.path.join(home, "AppData", "Roaming", "clawhub", "config.json"),
        os.path.join(home, ".config", "clawhub", "config.json"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return "clawhub"
    try:
        if shutil.which("clawhub"):
            return "clawhub"
    except Exception:
        pass
    return "skillhub"


def resolve_package(skill, source_dir, channel=None):
    """返回 (path_or_url, kind) 或 (None, 'missing')。本地优先，其次按渠道下载。

    channel: 'skillhub' | 'clawhub' | None(自动识别)。优先用 download_urls[channel]
    （发布时按渠道回填的对应官方下载 API），回退到 download_url；确保无论从哪个
    市场安装都走对应渠道的下载地址。
    """
    if source_dir:
        local = os.path.join(source_dir, skill["package"])
        if os.path.isfile(local):
            return local, "local"
    if channel is None:
        channel = _detect_channel()
    urls = skill.get("download_urls") or {}
    url = urls.get(channel) or skill.get("download_url")
    if url and _urllib is not None:
        return url, "download:" + channel
    return None, "missing"


def _fetch(url, dest):
    req = _urllib.Request(url, headers={"User-Agent": "tax-matrix-installer/1.0"})
    with _urllib.urlopen(req, timeout=60) as r, open(dest, "wb") as w:
        shutil.copyfileobj(r, w)


def _normalize(skill_dir):
    """若解压出单层子目录（如 skill/SKILL.md）则上移到 skill_dir 根。"""
    entries = os.listdir(skill_dir)
    if len(entries) == 1 and os.path.isdir(os.path.join(skill_dir, entries[0])):
        sub = os.path.join(skill_dir, entries[0])
        if os.path.isfile(os.path.join(sub, "SKILL.md")):
            for item in os.listdir(sub):
                shutil.move(os.path.join(sub, item), os.path.join(skill_dir, item))
            os.rmdir(sub)


# ---------------------------------------------------------------------------
# 安装单个技能
# ---------------------------------------------------------------------------
def install_one(skill, target, source_dir, force, dry_run, manifest_version=None, channel=None):
    slug = skill["slug"]
    # 每技能 version 为权威版本（renewable 等可能不同于顶层版本），
    # 仅在缺省时回落顶层版本，确保幂等跳过与版本校验准确。
    want_ver = skill.get("version") or manifest_version
    inst, cur_ver = is_installed(target, skill)
    if inst and not force:
        if cur_ver == want_ver:
            print(f"  [skip] {slug} 已安装 (v{cur_ver})")
            return "skip"
        print(f"  [warn] {slug} 已装 v{cur_ver} ≠ 目标 v{want_ver}；--force 可重装")
        return "skip"

    pkg, kind = resolve_package(skill, source_dir, channel)
    if pkg is None:
        # 审核/分发安全：download_url 初始为空时不应触网或报错，
        # 仅优雅跳过，待发布到 SkillHub / ClawHub 回填官方地址后自动可用。
        print(f"  [skip] {slug} 暂无需安装（无本地 source 且未配置 download_url；"
              f"发布到 SkillHub / ClawHub 后自动可用）")
        return "skip-offline"

    if dry_run:
        print(f"  [dry] 将安装 {slug} <- {kind}:{pkg}")
        return "dry"

    tmp_zip = None
    try:
        if kind.startswith("download"):
            os.makedirs(target, exist_ok=True)
            fd, tmp_zip = tempfile.mkstemp(suffix=".zip", prefix=f"mtrx_{slug}_")
            os.close(fd)
            _fetch(pkg, tmp_zip)
            zpath = tmp_zip
        else:
            zpath = pkg

        with zipfile.ZipFile(zpath) as z:
            names = z.namelist()
            if not any(n.replace("\\", "/").endswith("SKILL.md") for n in names):
                raise ValueError("zip 内缺少 SKILL.md，疑似损坏包")
            # 路径穿越防护：解压前校验所有条目均落在目标目录内（防 zip slip 投毒）
            skill_dir = os.path.join(target, slug)
            skill_dir_abs = os.path.abspath(skill_dir)
            for n in names:
                dest = os.path.abspath(os.path.join(skill_dir_abs, n))
                if not (dest == skill_dir_abs or dest.startswith(skill_dir_abs + os.sep)):
                    raise ValueError(f"zip 含非法路径（疑似穿越）：{n}")
            if os.path.isdir(skill_dir):
                shutil.rmtree(skill_dir)
            os.makedirs(skill_dir, exist_ok=True)
            z.extractall(skill_dir)
        _normalize(skill_dir)

        got = _read_version(os.path.join(skill_dir, "SKILL.md"))
        if want_ver and got != want_ver:
            print(f"  [warn] {slug} 安装后版本 v{got} ≠ 清单 v{want_ver}")
        print(f"  [ok] {slug} 安装完成 <- {kind}")
        return "ok"
    except Exception as e:
        print(f"  [fail] {slug} 安装异常: {e}")
        return "fail"
    finally:
        if tmp_zip and os.path.isfile(tmp_zip):
            try:
                os.remove(tmp_zip)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------
def main(argv=None):
    # 跨平台输出稳健性：Windows 控制台默认 GBK，强制 stdout/stderr 为 utf-8，避免乱码与解码异常
    for _s in (sys.stdout, sys.stderr):
        try:
            if getattr(_s, "reconfigure", None):
                _s.reconfigure(encoding="utf-8")
        except Exception:
            pass

    ap = argparse.ArgumentParser(description="财税技能矩阵一键安装器")
    ap.add_argument("--target", default=default_target(), help="目标 skills 目录（默认 ~/.skills）")
    ap.add_argument("--source", default=None, help="本地含 <slug>.zip 的目录，优先于下载")
    ap.add_argument("--only", default=None, help="仅安装指定 slug（如 tax-restructuring）")
    ap.add_argument("--force", action="store_true", help="强制重装已安装项")
    ap.add_argument("--dry-run", action="store_true", help="仅预演不写入")
    ap.add_argument("--no-experts", action="store_true",
                    help="关闭联动注册（默认会联动注册每个技能的专属专家与所属专家团）")
    ap.add_argument("--experts-src", default=None,
                    help="experts_build 目录（默认脚本同级的 experts_build/）")
    ap.add_argument("--marketplace-dir", default=None,
                    help="专家注册目标 marketplace（默认真实 ~/.workbuddy 我的专家；测试用临时目录）")
    args = ap.parse_args(argv)

    manifest = load_manifest()
    skills = manifest["skills"]
    if args.only:
        skills = [s for s in skills if s["slug"] == args.only]
        if not skills:
            sys.exit(f"INSTALL FAILED - 未知 slug: {args.only}")

    os.makedirs(args.target, exist_ok=True) if not args.dry_run else None
    print(f"财税技能矩阵安装 -> 目标: {args.target}")
    print(f"矩阵版本: {manifest.get('version')}  技能数: {len(skills)}")
    if args.source:
        print(f"本地源: {args.source}")
    print("-" * 48)

    results = {}
    mver = manifest.get("version")
    channel = _detect_channel()
    print(f"检测到安装渠道: {channel}（调用对应渠道下载 API 获取技能包）")
    for s in skills:
        results[s["slug"]] = install_one(s, args.target, args.source, args.force, args.dry_run, mver, channel)

    ok = sum(1 for v in results.values() if v in ("ok", "skip", "dry", "skip-offline"))
    fail = [k for k, v in results.items() if v == "fail"]
    print("-" * 48)

    # ---- 专家与专家团自动化注册（默认开启，--no-experts 可关闭） ----
    with_experts = not args.no_experts
    if with_experts:
        try:
            import matrix_expert_install as ME
        except Exception as e:  # pragma: no cover
            print(f"  [warn] 无法加载专家注册模块（跳过专家联动）: {e}")
        else:
            try:
                mk = args.marketplace_dir or ME._import_register().get_marketplace_base()
                print(f"联动注册专家/团队 -> marketplace: {mk}")
                rep = ME.install_experts_for_slugs(
                    [s["slug"] for s in skills], mk,
                    experts_src=args.experts_src, dry_run=args.dry_run, verbose=True)
                c = rep["counts"]
                print(f"  专家: ok={c['agents_ok']} skip={c['agents_skip']} dry={c['agents_dry']} "
                      f"missing={c['agents_missing']} fail={c['agents_fail']}")
                print(f"  团队: ok={c['teams_ok']} skip={c['teams_skip']} dry={c['teams_dry']} "
                      f"missing={c['teams_missing']} fail={c['teams_fail']}")
                if c["agents_missing"] or c["teams_missing"] or c["agents_fail"] or c["teams_fail"]:
                    print("  [warn] 存在缺失/失败的专家/团队包，请检查 experts_build/")
            except Exception as e:  # 专家联动异常不得中断技能安装主流程
                print(f"  [warn] 专家联动注册异常（已跳过，技能安装已完成）: {e}")

    print(f"完成：成功/跳过 {ok}，失败 {len(fail)}")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
