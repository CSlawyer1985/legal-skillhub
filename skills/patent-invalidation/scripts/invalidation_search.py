#!/usr/bin/env python3
"""
无效检索专用助手（基于内置 PatSeek 引擎）

按无效宣告的检索目的，构造并执行检索：
  - 目标专利画像（patent） → 拿权要 / IPC / 申请日 / 公开日 / 申请人
  - 现有技术 Bool 检索（强制 PD<优先权日，IPC 限领域）
  - 语义补盲（找 Bool 漏掉的隐蔽文献）
  - 抵触申请 / 重复授权专项（同一申请人拉网）

用法（dry-run，仅生成并展示检索式，不需 API Key）：
  python scripts/invalidation_search.py --target-patent CNxxxxA --priority-date 20150310 \
      --ipc G02B --features "光学减振;测量装置;恒温" --applicant "申请人名称"

执行（需 PATSEEK_API_KEY 或 --api-key，且已装 requests）：
  python scripts/invalidation_search.py --target-patent CNxxxxA --priority-date 20150310 \
      --ipc G02B --features "光学减振;测量装置" --applicant "申请人名称" --run

无 Key 降级（v1.1.0 新增，不联网，输出四条免费通道人工检索清单）：
  python scripts/invalidation_search.py --target-patent CNxxxxA --priority-date 20150310 \
      --ipc G02B --features "光学减振;测量装置" --offline
"""

import argparse
import os
import sys

# 允许从同目录导入内置 PatSeek 引擎
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from patseek_client import bool_search, get_patent, semantic_search_async, _load_dotenv
except Exception:
    bool_search = get_patent = semantic_search_async = None
    _load_dotenv = None  # type: ignore

# 启动时尝试加载 .env（若 patseek_client 不可用，本地轻量兜底）
if _load_dotenv is None:
    def _load_dotenv():
        """轻量兜底：从 scripts/.env / skill_root/.env / cwd/.env 加载 KEY=VALUE，不覆盖已有环境变量。"""
        here = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(here, ".env"),
            os.path.normpath(os.path.join(here, "..", ".env")),
            os.path.join(os.getcwd(), ".env"),
        ]
        for p in candidates:
            if not os.path.isfile(p):
                continue
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for ln in f:
                        ln = ln.strip()
                        if not ln or ln.startswith("#") or "=" not in ln:
                            continue
                        k, v = ln.split("=", 1)
                        k, v = k.strip(), v.strip().strip('"').strip("'")
                        if k and k not in os.environ:
                            os.environ[k] = v
            except OSError:
                pass
        return None

_load_dotenv()


def norm_date(d: str) -> str:
    """YYYY-MM-DD / YYYY/MM/DD / YYYYMMDD → YYYYMMDD"""
    return d.replace("-", "").replace("/", "")[:8]


def build_prior_art_query(features, ipc, prio):
    feats = [f.strip() for f in features.split(";") if f.strip()] if features else []
    # 每个特征先用原词成组 (OR 扩展由调用方/模型补充，详见 patseek_关键词扩展.md)
    feat_groups = " ".join(f"({f})" for f in feats)
    q = feat_groups
    if ipc:
        q += f" IPC=({ipc})"
    q += f" PD<{prio}"
    return q, feats, feat_groups


def print_offline_checklist(args, prio, feats, q_prior):
    """无 PatSeek Key 时的降级工作流（v1.1.0 新增）：
    输出四条免费官方/公开通道的逐步人工检索清单，不联网、不需 Key。"""
    feat_str = "；".join(feats) if feats else "（未指定核心特征）"
    ipc = args.ipc or "（未指定）"
    print("\n" + "=" * 64)
    print("OFFLINE 人工检索清单（无 PatSeek Key 降级工作流）")
    print("=" * 64)
    print(f"目标专利: {args.target_patent} | 时间死线: 公开日 < {prio} | IPC: {ipc}")
    print(f"核心特征: {feat_str}")
    print("""
【通道 1】CNIPA 专利检索及分析系统（pss-system.cponline.cnipa.gov.cn，需注册、免费）
  1) 登录 → "常规检索" → 检索式转写：将上述 Bool 式特征词放入"发明名称/摘要/权利要求"字段，
     IPC 填入"分类号"字段（前 4 位），申请日/公开日字段设上限为死线日期；
  2) 逐条打开命中文献，核对公开日 < 死线，导出/截图著录页；
  3) 用途：现有技术主检索 + 同申请人抵触申请/重复授权拉网（申请人字段 = 目标申请人）。

【通道 2】CNIPA 中国专利公布公告系统（epub.cnipa.gov.cn，免注册）
  1) 以目标专利公开号/申请号检索 → 下载官方专利单行本 PDF（含附图；有图形验证码，需人工完成）；
  2) 对通道 1 锁定的 CN 对比文件，同样经本通道取官方全文 PDF 与原始附图（供 G7 同色标注）；
  3) 证据清单标注"来源：epub.cnipa.gov.cn，下载日期：YYYY-MM-DD"。
  4) 可用 scripts/cnipa_epub.py url <公开号> 先打印直达链接。

【通道 3】Espacenet（worldwide.espacenet.com，免费，覆盖全球）
  1) 检索式转写：ctxt = "特征关键词" AND ipc = {ipc}（Classification search 辅助定 IPC）；
     结果按 publication date 升序筛，丢弃 ≥ 死线的文献；
  2) "Smart search"示例：ctxt all "{特征1}" and ctxt all "{特征2}" and ipc="{ipc}*"；
  3) 命中后下载原始 PDF（含说明书+附图）；同族（INPADOC）页核对同族最早的公开日；
  4) 用途：国外文献主检索 + 同族核验 + PCT 优先权基础全文获取。

【通道 4】Google Patents（patents.google.com，免费，语义扩展强）
  1) 直接用自然语言/关键词组合检索，利用其自动同义扩展补 Espacenet 漏检；
  2) 每条结果核对 "Publication" 日期 < 死线；附图可单独右键下载（供 G7 标注）；
  3) "Scholar/Non-patent"联动：非专利文献（论文/标准）经 Google Scholar 补检。

【固定与自检】
  □ 每条候选证据记录：公开号/文献名、公开日、来源通道、获取日期、具体出处（段落/图号）；
  □ 公开日 < {prio}（有优先权时以优先权日为死线；存疑权利要求另行核算窗口期）；
  □ 抵触申请：公开日在目标申请日之后、申请日在之前的 CN 文献（通道 1 申请人字段拉网）；
  □ 国外文献需附图/全文时可用 scripts/foreign_patent_fetch.py（Google Patents/Espacenet 自动抓取）；
  □ 检索结果回填 M4 理由组合与证据清单，后续 M4–M11 流程不受影响。
""".replace("{ipc}", ipc).replace("{特征1}", feats[0] if len(feats) > 0 else "特征1").replace("{特征2}", feats[1] if len(feats) > 1 else "特征2").replace("{prio}", prio))
    print("[PatSeek 检索式参考（有 Key 后可直接执行）]")
    print(f"  python scripts/patseek_client.py bool \"{q_prior}\" --page-size 30")


def main():
    p = argparse.ArgumentParser(
        description="无效检索专用助手：按无效宣告目的构造并执行 PatSeek 检索",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--target-patent", required=True, help="目标专利公开号，如 CN118658342A")
    p.add_argument("--priority-date", required=True, help="目标专利优先权日 YYYYMMDD / YYYY-MM-DD（时间死线）")
    p.add_argument("--ipc", help="目标专利 IPC 前 4 位，如 G02B")
    p.add_argument("--features", help="核心技术特征，分号分隔，如 光学减振;测量装置;恒温")
    p.add_argument("--applicant", help="目标专利申请人，用于抵触申请 / 重复授权检索")
    p.add_argument("--api-key", default=os.environ.get("PATSEEK_API_KEY", ""), help="PatSeek API Key")
    p.add_argument("--run", action="store_true", help="真正执行检索（需 API Key 且已装 requests）")
    p.add_argument("--offline", action="store_true",
                   help="无 Key 降级模式（v1.1.0 新增）：不联网，输出四条免费通道人工检索清单")
    args = p.parse_args()

    prio = norm_date(args.priority_date)
    q_prior, feats, feat_groups = build_prior_art_query(args.features or "", args.ipc, prio)
    sem_q = " ".join(feats)

    print("=" * 64)
    print("无效检索计划")
    print(f"  目标专利          : {args.target_patent}")
    print(f"  优先权日(时间死线): {prio}")
    print(f"  IPC               : {args.ipc or '未指定'}")
    print(f"  申请人            : {args.applicant or '未指定'}")
    print(f"  核心特征          : {args.features or '未指定'}")
    print("=" * 64)

    if not args.run:
        print("\n[dry-run] 以下为构造好的无效专用检索式，请检查同义扩展与日期后加 --run 执行：\n")
        print(f"  [现有技术 Bool 查准]\n    python scripts/patseek_client.py bool \"{q_prior}\" --page-size 30\n")
        if sem_q:
            print(f"  [语义补盲]\n    python scripts/patseek_client.py semantic \"{sem_q}\" --timeout 180\n")
        if args.applicant:
            print(f"  [抵触申请]  (执行时自动代入目标申请日)\n    python scripts/patseek_client.py bool \"AP=({args.applicant}) {feat_groups} AD<[目标申请日] PD>[目标申请日]\" --page-size 30\n")
            print(f"  [重复授权]  (执行时自动代入目标年份范围)\n    python scripts/patseek_client.py bool \"AP=({args.applicant}) {feat_groups} AD=[目标年份±2年]\" --page-size 30\n")
        print("  （同义扩展提示：每个特征组请用 OR 补充近义/中英文变体，详见 references/patseek_关键词扩展.md）")
        if args.offline or not args.api_key:
            print_offline_checklist(args, prio, feats, q_prior)
        else:
            print("  （无 Key 时可加 --offline 生成四条免费通道人工检索清单）")
        return

    # ---- 执行模式 ----
    if not args.api_key or bool_search is None:
        print("错误: --run 需要 PATSEEK_API_KEY（或 --api-key）且已安装 requests 库。\n"
              "      无 Key 时请改用 --offline 生成人工检索清单：\n"
              "      python scripts/invalidation_search.py --target-patent ... --priority-date ... --offline",
              file=sys.stderr)
        sys.exit(1)

    appdate = None
    # 1. 画像
    print("\n[1/4] 目标专利画像 (patent)...")
    try:
        prof = get_patent(args.api_key, args.target_patent)
        pats = prof.get("patent_list", [])
        if pats:
            p0 = pats[0]
            appdate = norm_date(str(p0.get("appdate", "")))
            print(f"    公开号 {p0.get('pid')} | 申请日 {p0.get('appdate')} | 公开日 {p0.get('pubdate')} | IPC {p0.get('ipcs')} | 申请人 {p0.get('applicant')}")
    except Exception as e:
        print("    画像失败:", e, file=sys.stderr)

    # 2. 现有技术 Bool
    print("\n[2/4] 现有技术 Bool 检索...")
    print(f"  检索式: {q_prior}")
    try:
        r = bool_search(args.api_key, q_prior, page_size=30)
        print(f"  -> 命中 {r.get('total')} 条")
    except Exception as e:
        print("  失败:", e, file=sys.stderr)

    # 3. 语义补盲
    if sem_q:
        print("\n[3/4] 语义补盲...")
        try:
            res = semantic_search_async(args.api_key, sem_q, timeout=180)
            print(f"  -> {len(res)} 条; 取 PD<{prio} 的高相似度者：")
            for x in res[:20]:
                pd = norm_date(str(x.get("pubdate", "")))
                flag = "OK" if pd and pd < prio else "超期"
                print(f"    [{x.get('similarity')}%][{flag}] {x.get('pid')} {x.get('title')}")
        except Exception as e:
            print("  失败:", e, file=sys.stderr)

    # 4. 抵触申请 / 重复授权
    if args.applicant:
        print("\n[4/4] 抵触申请 / 重复授权专项...")
        # 申请日优先取画像，其次用 --priority-date（时间死线即申请日）兜底
        cutoff = appdate or prio
        if cutoff:
            q_dk = f"AP=({args.applicant}) ({' '.join(f'({f})' for f in feats)}) AD<{cutoff} PD>{cutoff}"
            yr = cutoff[:4]
            q_dup = f"AP=({args.applicant}) ({' '.join(f'({f})' for f in feats)}) AD={int(yr)-2}-{int(yr)+2}"
            for name, q in (("抵触申请", q_dk), ("重复授权", q_dup)):
                print(f"  [{name}] 检索式: {q}")
                try:
                    r = bool_search(args.api_key, q, page_size=30)
                    print(f"    -> 命中 {r.get('total')} 条")
                except Exception as e:
                    print("    失败:", e, file=sys.stderr)
        else:
            print("  未取到目标申请日，跳过自动构造（请手动填 AD<[目标申请日] / AD=[年份±2年]）")


if __name__ == "__main__":
    main()
