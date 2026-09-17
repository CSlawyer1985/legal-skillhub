#!/usr/bin/env python3
"""
律典·法律检索 flk 检索封装脚本（Step 2/Step 2.4 强制调用）
==========================================================
作用：输入法规名，自动调国家法律法规数据库后端 API，
      返回目标法规的 bbbs 直链 + 同名多版本时效信息。
      禁止 AI 手写 curl/自行构造请求（从源头消灭检索参数错误）。

用法：
  python3 scripts/flk_search.py --name "中华人民共和国行政处罚法"
  python3 scripts/flk_search.py --name "工伤保险条例" --name "劳动合同法"
  python3 scripts/flk_search.py --name "养犬" --fulltext --pages 5   # 全文搜索

输出（stdout）：
  法规名 | 候选直链(按施行日期排序，有效性未核验) | 直链 | 多版本清单（sxx/sxrq）
  ⚠️ 免责声明：sxx/sxrq 字段不可靠，脚本不判定「现行有效」；有效性须按 SKILL.md Step 3 另行核验。

行为增强说明：
  - 候选分级（P2）：国家层法规（法律/行政法规）优先输出候选直链；仅地方性法规
    命中时输出显式「未检索到国家层面法规」警示（实测 S2：搜「城市房屋拆迁管理
    条例」7 条全为地方条例，旧版直接拿江苏省条例当候选直链的教训）。
  - 新法替代追踪（P1）：命中 SUPERSEDED 表中已被新法取代的旧法规（含检索词本身
    即旧法名）时输出替代警示（实测 S5：旧《危险化学品安全管理条例》第77条
    罚 10-20 万，已被新《危险化学品安全法》第100条 10-50 万取代的教训）。
  - 标题搜索单页化（P5）：第 1 页非空即停（flk pageSize=200 已覆盖单法规全部
    同名版本/近似条目，翻页仅重复）。实测 flk 服务器拒绝并发连接（并发 RST
    ConnectionReset），故批量检索保持串行 + 单页化：4 部法规 28s → 约 5s。
    全文搜索（--fulltext）仍按 --pages 翻页。

幂等只读：不修改任何文件。
"""

import argparse
import json
import re
import sys
import time
import urllib.request

FLK_LIST_URL = "https://flk.npc.gov.cn/law-search/search/list"
TIMEOUT = 20
DEFAULT_PAGES = 3

# 省级行政区名称（用于识别地方性法规标题，如「江苏省…条例」「北京市…办法」）
PROVINCES = (
    "北京", "天津", "上海", "重庆", "河北", "山西", "辽宁", "吉林", "黑龙江",
    "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南", "湖北", "湖南",
    "广东", "海南", "四川", "贵州", "云南", "陕西", "甘肃", "青海",
    "内蒙古", "广西", "西藏", "宁夏", "新疆", "香港", "澳门", "台湾",
)

# 已被新法取代的旧法规（新法替代追踪，P1，2026-08-20 实测 S5/S2 教训固化）
# 维护铁律：新法公布/施行、旧法废止时须同步更新本表 + references/common-laws.md 对应分区。
SUPERSEDED = {
    "危险化学品安全管理条例": {
        "replacement": "中华人民共和国危险化学品安全法",
        "num": "主席令第64号",
        "effective": "2026-05-01",
        "note": "旧条例第77条罚 10万-20万；新法第100条罚 10万-50万（2026-05-01 起），禁止再引旧条例作处罚依据",
    },
    "城市房屋拆迁管理条例": {
        "replacement": "国有土地上房屋征收与补偿条例",
        "num": "国务院令第590号",
        "effective": "2011-01-21",
        "note": "2011-01-21 废止，拆迁模式转为征收补偿模式",
    },
}


def clean(t: str) -> str:
    return re.sub(r"<[^>]+>", "", t or "")


def is_local(title: str) -> bool:
    """判断法规标题是否属地方性法规（省/市/自治州等地方层）。

    国家层特征：以「中华人民共和国」开头（法律/行政法规），或不含任何地方特征。
    地方层特征：标题含省级行政区名称，或以「X市/自治州/自治县」开头
    （至少 2 个汉字+市，排除「城市」「都市」等通用词——2026-08-20 实测
    「城市房屋拆迁管理条例」曾被误判为地方条例的教训）。
    """
    if not title or title.startswith("中华人民共和国"):
        return False
    if any(p in title for p in PROVINCES):
        return True
    if re.match(r"^[\u4e00-\u9fff]{2,8}(自治州|自治县|市)", title):
        return True
    return False


def supersede_notes(kw: str, hits: list) -> list:
    """新法替代追踪：检索词或命中标题命中 SUPERSEDED 表时返回替代警示文案。"""
    titles = [kw] + [h.get("title", "") for h in hits]
    notes = []
    for old, info in SUPERSEDED.items():
        if any(old in t for t in titles):
            notes.append(
                f"  🔴 新法替代警示：检索目标命中的《{old}》已被《{info['replacement']}》"
                f"（{info['num']}，{info['effective']} 施行）取代——{info['note']}"
            )
    return notes


def search(kw: str, st: int = 1, pages: int = DEFAULT_PAGES) -> list:
    """遍历多页，收集同名/近似条目（去重），区分精确匹配与包含匹配。

    早停优化：
    - 标题搜索（st=1）第 1 页出现精确匹配（title==kw，可能含同名多版本）
      即停止翻页——实测第 1 页即命中时，2 次空翻页 + sleep 约浪费 4s/法规；
    - 扩展为「第 1 页非空即停」——flk pageSize=200 已覆盖单法规全部
      同名版本/近似条目，翻页仅重复；且实测 flk 拒绝并发连接（并发 RST），
      批量检索保持串行 + 单页化（4 部法规 28s → 约 5s）。
    全文搜索（st=2）不早停，按 pages 翻页。
    """
    raw = []
    for p in range(1, pages + 1):
        body = {
            "searchContent": kw, "searchRange": 1,
            "sxrq": [], "gbrq": [], "sxx": [],
            "searchType": st, "page": p, "pageSize": 200, "sortType": 1,
        }
        req = urllib.request.Request(
            FLK_LIST_URL,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
        )
        page_rows = []
        try:
            data = json.load(urllib.request.urlopen(req, timeout=TIMEOUT))
            page_rows = data.get("rows", [])
        except Exception:
            time.sleep(1)
            continue  # 该页超时跳过，继续翻页
        for x in page_rows:
            t = clean(x.get("title", ""))
            raw.append({
                "title": t,
                "bbbs": x.get("bbbs"),
                "sxx": x.get("sxx"),
                "sxrq": x.get("sxrq"),
            })
        # 早停：标题搜索且本页非空（pageSize=200 已覆盖全部同名版本/近似条目）
        if st == 1 and page_rows:
            break
    # 按 bbbs 去重（翻页可能重复返回）
    seen = set()
    hits = []
    for h in raw:
        if h["bbbs"] and h["bbbs"] not in seen:
            seen.add(h["bbbs"])
            hits.append(h)
    # 精确匹配（title == kw）优先；无精确匹配才保留包含匹配（过滤明显无关长标题）
    exact = [h for h in hits if h["title"] == kw]
    if exact:
        return exact
    return [h for h in hits if len(h["title"]) < 40]


def pick_current(hits: list) -> dict:
    """从多版本中选取「候选」直链：施行日期最新者优先；sxx 仅供参考（不可靠）。
    注意：仅作候选排序，不构成『现行有效』判定（有效性须另行核验）。"""
    if not hits:
        return {}
    dated = [h for h in hits if h.get("sxrq")]
    if dated:
        # 施行日期最新
        return max(dated, key=lambda h: h["sxrq"] or "")
    # 无施行日期的，优先 sxx=3（数据库常见现行码），否则取第一个
    sxx3 = [h for h in hits if h.get("sxx") == 3]
    return (sxx3[0] if sxx3 else hits[0])


def main():
    ap = argparse.ArgumentParser(description="律典 flk 检索封装")
    ap.add_argument("--name", action="append", required=True, help="法规名（可多次）")
    ap.add_argument("--fulltext", action="store_true", help="全文搜索（searchType=2）")
    ap.add_argument("--pages", type=int, default=DEFAULT_PAGES, help="翻页数")
    args = ap.parse_args()

    st = 2 if args.fulltext else 1

    # 批量检索：串行 + 标题搜索单页化早停（实测 flk 拒绝并发连接，RST；串行单页约 1s/部）
    for kw in args.name:
        hits = search(kw, st=st, pages=args.pages)
        print("=" * 70)
        print(f"检索：{kw}（{'全文' if args.fulltext else '标题'}搜索）共命中 {len(hits)} 条")

        # P1：新法替代追踪（先于一切，即使 flk 未收录也须提示）
        for n in supersede_notes(kw, hits):
            print(n)

        if not hits:
            print("  ⚠️ flk 未收录（可能为部门规章/规范性文件/已废止法规）→ 按法规类型路由到对应权威源；若目标法规疑似已被新法取代，须按 SKILL.md Step 3 以国务院公报/国家行政法规库核验替代法规")
            time.sleep(0.3)
            continue

        # P2：候选分级——国家层优先；仅地方层命中且检索词为国家层名称时显式警示
        national = [h for h in hits if not is_local(h["title"])]
        local = [h for h in hits if is_local(h["title"])]
        if not national and local and not is_local(kw):
            print("  ⚠️ 未检索到国家层面法规！以下命中均为地方性法规，与检索目标（国家法律/行政法规）位阶不符，禁止直接引用为现行依据：")
            for h in hits:
                print(f"    - {h['title']} | sxx={h.get('sxx')} | sxrq={h.get('sxrq')} | bbbs={h.get('bbbs')}")
            print("  ⚠️ 若目标法规为已废止国家行政法规，国家法律法规数据库不再收录（如《城市房屋拆迁管理条例》2011-01-21 废止）——须按 SKILL.md Step 3 以国务院公报/国家行政法规库核验替代法规")
            time.sleep(0.3)
            continue

        cur = pick_current(national if national else hits)
        print(f"  候选直链（有效性未核验）：{cur.get('title','')} | 施行={cur.get('sxrq')}")
        print(f"  ⚠️ 免责：sxx/sxrq 字段不可靠，脚本不判定『现行有效』；有效性须按 SKILL.md Step 3 以官方权威源（政府公报/人大公告）或可用 MCP 的时效性标注另行核验")
        print(f"  直链：https://flk.npc.gov.cn/detail?id={cur.get('bbbs')}")
        print("  多版本清单（sxx 仅供参考，不可靠）：")
        for h in hits:
            print(f"    - {h['title']} | sxx={h.get('sxx')} | sxrq={h.get('sxrq')} | bbbs={h.get('bbbs')}")
        time.sleep(0.3)


if __name__ == "__main__":
    main()
