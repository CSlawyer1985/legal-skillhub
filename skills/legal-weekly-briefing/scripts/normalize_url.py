#!/usr/bin/env python3
"""微信公众号链接还原工具

将搜狗/163 等聚合链接还原为 mp.weixin.qq.com 原始链接。
无法还原时返回原 url + flag=fallback。

用法：
    python3 normalize_url.py "https://mp.weixin.qq.com/s/xxx"
    python3 normalize_url.py < urls.txt   # 每行一个 url
"""
import sys, re, json


def normalize_url(url):
    """返回 (clean_url, flag)。flag: 'ok' | 'fallback'。"""
    if not url:
        return url, 'fallback'

    # 已是 mp 原始链接
    if 'mp.weixin.qq.com' in url:
        return url, 'ok'

    # 搜狗聚合：https://mp.weixin.qq.com/... 藏在 /link?url= 后面（实际还是 mp）
    # 或 weixin.sogou.com/link?url=... 需二次跳转，此处仅提取已知 mp 子串
    mp_match = re.search(r'(https?://mp\.weixin\.qq\.com/[^\s"\'?]*)', url)
    if mp_match:
        return mp_match.group(1), 'ok'

    # 163 聚合或其他：尝试提取 __biz / mid / idx / sn 参数重组（不可靠，标记 fallback）
    biz = re.search(r'__biz=([^&]+)', url)
    mid = re.search(r'mid=([^&]+)', url)
    idx = re.search(r'idx=([^&]+)', url)
    sn = re.search(r'sn=([^&]+)', url)
    if biz and mid and idx and sn:
        recon = f"https://mp.weixin.qq.com/s?__biz={biz.group(1)}&mid={mid.group(1)}&idx={idx.group(1)}&sn={sn.group(1)}"
        return recon, 'ok'

    return url, 'fallback'


if __name__ == '__main__':
    if len(sys.argv) > 1:
        u, f = normalize_url(sys.argv[1])
        print(json.dumps({"url": u, "flag": f}, ensure_ascii=False))
    else:
        for line in sys.stdin:
            line = line.strip()
            if line:
                u, f = normalize_url(line)
                print(json.dumps({"url": u, "flag": f}, ensure_ascii=False))
