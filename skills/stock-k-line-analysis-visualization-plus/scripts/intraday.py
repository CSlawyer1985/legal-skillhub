"""日内分时图（time-sharing）数据共享模块。

负责从东方财富拉取指定标的当日分时数据，并解析为结构化数组，
供 analyze.py（静态 PNG）、build_report.py（ECharts HTML）、build_docx.py（DOCX 内嵌图）复用。

API: push2his.eastmoney.com/api/qt/stock/trends2/get
字段顺序（trends 每行逗号分隔）:
  时间, 开, 收(当前价), 高, 低, 成交量(手), 成交额, 均价, 手数, 涨跌幅%, 成交量(累计)
"""
import os
import json
import argparse
import subprocess
import urllib.request


def fetch_intraday(secid, code, workspace, timeout=15):
    """拉取当日分时数据，保存为 <CODE>_intraday.json。返回 dict 或 None。"""
    url = (
        "https://push2his.eastmoney.com/api/qt/stock/trends2/get"
        f"?secid={secid}&fields1=f1,f2,f3,f7"
        "&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"
        "&iscr=0&ndays=1&forcect=1"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except Exception as e:  # noqa: BLE001
        print("分时数据拉取失败:", e)
        return None
    out_path = os.path.join(workspace, f"{code}_intraday.json")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(raw)
    return json.loads(raw)


def load_intraday(workspace, code):
    """读取已保存的分时 JSON，返回解析后的结构化数据；无数据返回 None。"""
    path = os.path.join(workspace, f"{code}_intraday.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    d = data.get("data")
    if not d or "trends" not in d:
        return None
    trends = d["trends"]
    if not trends:
        return None
    times, prices, avg_prices, vols = [], [], [], []
    # 优先用 K线文件中的真实昨收（前一交易日收盘价）作为基准；
    # 分时接口 data.preClose / data.preSettlement 可能缺失或为 None，
    # 直接回退到今日开盘价会导致基准线与涨跌幅计算偏差。
    pre_close = _kline_preclose(workspace, code)
    if pre_close is None:
        pre_close = float(d.get("preClose") or d.get("preSettlement") or trends[0].split(",")[2])
    for row in trends:
        p = row.split(",")
        times.append(p[0])                  # "2026-07-24 09:30"
        prices.append(float(p[2]))          # 当前价（收盘字段）
        avg_prices.append(float(p[7]))      # 均价
        vols.append(float(p[5]))            # 成交量（手）
    last_price = prices[-1]
    chg_pct = (last_price / pre_close - 1) * 100 if pre_close else 0.0
    day_high = max(float(r.split(",")[3]) for r in trends)
    day_low = min(float(r.split(",")[4]) for r in trends)
    return dict(
        times=times, prices=prices, avg_prices=avg_prices, vols=vols,
        pre_close=pre_close, last_price=last_price, chg_pct=chg_pct,
        day_high=day_high, day_low=day_low, trade_date=times[0][:10],
    )


def _kline_preclose(workspace, code):
    """从同目录的 <CODE>_kline.json 读取前一交易日收盘价作为昨收基准。

    返回 float 或 None（无 K线文件 / 数据不足时）。
    """
    kpath = os.path.join(workspace, f"{code}_kline.json")
    if not os.path.exists(kpath):
        return None
    try:
        with open(kpath, encoding="utf-8") as f:
            kdata = json.load(f)
        klines = kdata.get("data", {}).get("klines", [])
        if len(klines) < 2:
            return None
        # 倒数第二条为前一交易日收盘（最后一条是当日）
        return float(klines[-2].split(",")[2])
    except Exception:  # noqa: BLE001
        return None


# secid 前缀：深圳=0，上海=1
def secid_of(code):
    code = code.lstrip("0").zfill(6) if code.startswith("0") else code
    if code.startswith(("60", "68", "9", "5")):
        return f"1.{code}"
    return f"0.{code}"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--code", required=True)
    args = ap.parse_args()
    sid = secid_of(args.code)
    res = fetch_intraday(sid, args.code, args.workspace)
    if res:
        print("分时数据已保存:", os.path.join(args.workspace, f"{args.code}_intraday.json"))
    else:
        print("分时数据获取为空")
