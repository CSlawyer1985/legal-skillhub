# Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm.
#!/usr/bin/env python3
"""批量通过风鸟(riskbird.com)查询企业社保人数、电话、邮箱 v4
改进：从搜索页直接提取数据（无需进详情页，不消耗额度）
复用用户Chrome标签页的session
"""
import json, subprocess, time, os, re, urllib.parse, sys

CDP = "http://localhost:3456"
COMPANIES_FILE = "/tmp/wuxi_companies_final.json"
RESULT_FILE = "/tmp/wuxi_riskbird_results.json"
DEBUG = True


def get_riskbird_tab():
    """获取一个已打开的风鸟页面"""
    result = subprocess.run(
        ["curl", "-s", "--noproxy", "*", "--max-time", "10",
         f"{CDP}/targets"],
        capture_output=True, text=True, timeout=15)
    try:
        data = json.loads(result.stdout)
    except:
        print("  ❌ 无法获取targets列表")
        return None

    for t in data:
        tid = t.get("targetId", "")
        url = t.get("url", "")
        if "riskbird.com" in url:
            print(f"  ✅ 使用风鸟页面: {t.get('title','')[:50]}")
            return tid

    print("  ❌ 请在Chrome中打开 https://www.riskbird.com")
    return None


def navigate(tid, url):
    """导航到指定URL"""
    cmd = ["curl", "-s", "--noproxy", "*", "--data-raw", url,
           f"{CDP}/navigate?target={tid}"]
    subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def get_page_text(tid, max_len=8000):
    """获取页面纯文本"""
    cmd = ["curl", "-s", "--noproxy", "*", "--data-raw",
           f"document.body.innerText.slice(0, {max_len})",
           f"{CDP}/eval?target={tid}"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    out = r.stdout.strip()
    try:
        start = out.index('{"value":')
        val_str = out[start:]
        obj = json.loads(val_str)
        return obj.get("value", "")
    except:
        return out


def extract_from_search_results(text, company_name):
    """从搜索结果页文本中提取目标企业的信息"""
    # 先用企业名定位到该条结果的位置
    lines = text.split("\n")
    info = {"company": company_name, "phone": "", "email": "",
            "website": "", "socialSecurity": "", "staffSize": "",
            "address": "", "legalPerson": "", "capital": "",
            "establishDate": "", "status": "", "creditCode": ""}

    # 找到目标企业所在行
    target_idx = -1
    for i, line in enumerate(lines):
        if line.strip() == company_name:
            target_idx = i
            break

    if target_idx < 0:
        # 尝试部分匹配
        for i, line in enumerate(lines):
            if company_name in line and len(line.strip()) > 5:
                target_idx = i
                break

    if target_idx < 0:
        return None  # 没找到

    # 从target_idx开始往后找关键字段（通常就在接下来的几行内）
    for j in range(target_idx, min(target_idx + 30, len(lines))):
        line = lines[j].strip()
        if not line:
            continue

        # 企业状态
        if line in ("在营", "正常", "存续", "在营/正常", "吊销", "注销"):
            info["status"] = line

        # 电话
        if line.startswith("电话：") or line.startswith("电话:"):
            val = line.split("：")[-1].split(":")[-1].strip()
            if val:
                info["phone"] = val

        # 邮箱
        if line.startswith("邮箱：") or line.startswith("邮箱:"):
            val = line.split("：")[-1].split(":")[-1].strip()
            if val and "@" in val:
                info["email"] = val

        # 官网
        if line.startswith("官网：") or line.startswith("官网:") or line.startswith("网址："):
            val = line.split("：")[-1].split(":")[-1].strip()
            if val and val != "-":
                info["website"] = val

        # 通信地址 / 注册地址
        if "通信地址" in line or "注册地址" in line:
            parts = re.split(r'[：:]', line)
            if len(parts) >= 2:
                val = parts[-1].strip()
                if val and val != "-":
                    info["address"] = val

        # 法定代表人（可能在同一行或下一行）
        if "法定代表人" in line and "：" in line:
            info["legalPerson"] = line.split("：")[-1].strip()
        elif "法定代表人" in line and j + 1 < len(lines):
            next_l = lines[j+1].strip()
            if next_l and not next_l.startswith("注册资本") and not next_l.startswith("电话"):
                info["legalPerson"] = next_l.split("：")[-1].strip()

        # 注册资本
        if "注册资本" in line and "实缴" not in line and "：" in line:
            info["capital"] = line.split("：")[-1].strip()

        # 成立日期
        if "成立日期" in line and "：" in line:
            info["establishDate"] = line.split("：")[-1].strip()

        # 统一社会信用代码
        if "统一社会信用代码" in line and "：" in line:
            info["creditCode"] = line.split("：")[-1].strip()

        # 参保人数 - 搜索结果页可能不直接显示
        # 通过"一般纳税人"、"微型"等标签推断

    # 如果没找到电话，尝试在整个文本中搜索匹配该公司的电话
    if not info["phone"]:
        # 在公司名附近找电话模式
        context = "\n".join(lines[max(0, target_idx-2):target_idx+20])
        phone_match = re.search(r'电话[：:]\s*(\d[\d\-]{6,})', context)
        if phone_match:
            info["phone"] = phone_match.group(1).strip()

    if not info["email"]:
        context = "\n".join(lines[max(0, target_idx-2):target_idx+20])
        email_match = re.search(r'邮箱[：:]\s*([\w.%-]+@[\w.-]+\.[\w]{2,})', context)
        if email_match:
            info["email"] = email_match.group(1).strip()

    return info


def query_one(tid, company):
    """查询一家企业 - 从搜索页提取"""
    encoded = urllib.parse.quote(company)
    search_url = f"https://www.riskbird.com/search/company?keyword={encoded}&_t={int(time.time()*1000)}"

    navigate(tid, search_url)
    time.sleep(6)

    text = get_page_text(tid, 10000)

    # 检查额度
    if "额度已用完" in text:
        print(f"  ⛔ 额度已用完")
        return {"company": company, "error": "QUOTA_EXHAUSTED"}

    # 从搜索结果提取
    info = extract_from_search_results(text, company)

    if info is None:
        print(f"  ❌ 搜索结果中未找到该企业")
        return {"company": company, "error": "NOT_FOUND", "_preview": text[:500]}

    info["query_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
    return info


def save_results(results):
    with open(RESULT_FILE, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def main():
    with open(COMPANIES_FILE, "r") as f:
        companies = json.load(f)
    total = len(companies)

    print("=" * 60)
    print(f"风鸟批量查询 v4 | 共 {total} 家企业 | 搜索页直接提取")
    print("=" * 60)

    tid = get_riskbird_tab()
    if not tid:
        sys.exit(1)

    results = []
    if os.path.exists(RESULT_FILE):
        try:
            with open(RESULT_FILE, "r") as f:
                results = json.load(f)
            print(f"📂 已有记录: {len(results)} 条")
        except:
            pass

    done = set(r.get("company","") for r in results if r.get("company") and not r.get("error"))
    todo = [c for c in companies if c not in done]
    print(f"✅ 已完成: {len(done)} | ⏳ 待查询: {len(todo)}\n")

    if not todo:
        print("全部完成！")
        return

    success = 0; fail = 0

    for idx, company in enumerate(todo):
        print(f"[{idx+1}/{len(todo)}] {company}", end="")

        try:
            info = query_one(tid, company)
        except Exception as e:
            info = {"company": company, "error": f"异常: {e}"}

        results.append(info)
        save_results(results)

        err = info.get("error", "")
        if err:
            print(f"  ❌ {err}")
            fail += 1
            if "QUOTA" in err:
                break
        else:
            phone = info.get("phone","-")
            email = info.get("email","-")
            print(f"  📞{phone[:15]:15s} 📧{email[:25]:25s}", end="")
            if info.get("address"):
                print(f" 📍{info['address'][:20]}", end="")
            print()
            success += 1

        time.sleep(2)  # 给页面加载留足时间

    print(f"\n{'=' * 60}")
    print(f"完成！成功: {success} | 失败: {fail} | 总计: {len(results)}")
    print(f"结果: {RESULT_FILE}")

    valid = [r for r in results if r.get("company") and not r.get("error")]
    if valid:
        print(f"\n📋 已获取 {len(valid)} 家企业:")
        for r in valid:
            print(f"  {r['company'][:20]:20s} | {r.get('phone','-'):15s} | {r.get('email','-'):25s}")


if __name__ == "__main__":
    main()
