#!/usr/bin/env python3
"""
海关知识产权备案查询自动化脚本
使用 nodriver 控制 Chrome 浏览器，访问海关备案查询系统，
绕过 WAF 防护，自动查询品牌备案信息。

用法:
    python3 customs_search.py --brand "TRW"
    python3 customs_search.py --check-env
    python3 customs_search.py --install-deps
"""

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


# ── 常量 ──────────────────────────────────────────────
CUSTOMS_URL = "http://202.127.48.145:8888/zscq/search/jsp/vBrandSearchIndex.jsp"
TIMEOUT_PAGE = 40
TIMEOUT_WAF = 15
QUERY_DELAY = 2

CSV_FIELDS = [
    "查询品牌", "权利名称", "权利人名称", "权利人国别", "权利号",
    "备案号", "权利类别", "商品分类", "备案状态",
    "备案开始日期", "备案截止日期", "查询时间"
]
CSV_FILENAME = "知识产权海关保护备案.csv"


# ── 环境检测 ──────────────────────────────────────────
def find_chrome():
    """检测 Chrome 浏览器安装路径"""
    candidates = []

    if sys.platform == "darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ]
    elif sys.platform == "win32":
        # 使用 os.environ 而非 expandvars，因为在 bash 子进程中
        # Windows 环境变量（如 %ProgramFiles%）可能无法正确解析
        pf = os.environ.get("ProgramFiles", r"C:\Program Files")
        pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        local = os.environ.get("LocalAppData", os.path.expanduser("~/AppData/Local"))
        candidates = [
            os.path.join(pf, "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(pf86, "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(local, "Google", "Chrome", "Application", "chrome.exe"),
        ]
    else:
        candidates = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
            "/snap/bin/chromium",
        ]

    for path in candidates:
        if os.path.isfile(path):
            return path

    try:
        if sys.platform == "win32":
            # Windows 下用 where 命令，指定 encoding 避免 UTF-8 解码错误
            result = subprocess.run(
                ["where", "chrome"],
                capture_output=True, text=True, timeout=5,
                encoding="gbk", errors="replace"
            )
            if result.returncode == 0 and result.stdout.strip():
                path = result.stdout.strip().splitlines()[0]
                if os.path.isfile(path):
                    return path
        else:
            result = subprocess.run(
                ["which", "google-chrome"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().splitlines()[0]
    except Exception:
        pass

    return None


def check_python_version():
    """检测 Python 版本是否满足要求"""
    version = sys.version_info
    return version.major == 3 and version.minor >= 9


def _get_venv_python():
    """获取 venv 中的 Python 路径"""
    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if sys.platform == "win32":
        venv_python = os.path.join(skill_dir, ".venv", "Scripts", "python.exe")
    else:
        venv_python = os.path.join(skill_dir, ".venv", "bin", "python")
    if os.path.isfile(venv_python):
        return venv_python
    return None


def _ensure_venv():
    """确保 venv 存在，返回 venv 的 Python 路径"""
    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    venv_dir = os.path.join(skill_dir, ".venv")
    if sys.platform == "win32":
        venv_python = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        venv_python = os.path.join(venv_dir, "bin", "python")

    if not os.path.isfile(venv_python):
        print(json.dumps({"action": "create_venv", "path": venv_dir}))
        subprocess.run(
            [sys.executable, "-m", "venv", venv_dir],
            capture_output=True, text=True, timeout=60
        )

    return venv_python


def _is_in_venv():
    """判断当前是否已在虚拟环境中"""
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )


def check_env():
    """检测运行环境"""
    result = {
        "chrome": False,
        "chrome_path": None,
        "python_ok": False,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "nodriver": False,
        "venv_python": None,
        "errors": [],
    }

    chrome_path = find_chrome()
    if chrome_path:
        result["chrome"] = True
        result["chrome_path"] = chrome_path
    else:
        result["errors"].append(
            "Chrome 浏览器未找到，请安装: https://www.google.com/chrome/"
        )

    if check_python_version():
        result["python_ok"] = True
    else:
        result["errors"].append(
            f"Python 版本过低 ({result['python_version']})，需要 >= 3.9"
        )

    # 检测 nodriver（先检查 venv，再检查系统）
    venv_python = _get_venv_python()
    if venv_python:
        result["venv_python"] = venv_python
        check_cmd = [venv_python, "-c", "import nodriver"]
    else:
        check_cmd = [sys.executable, "-c", "import nodriver"]

    try:
        r = subprocess.run(
            check_cmd, capture_output=True, text=True, timeout=10,
            encoding="gbk" if sys.platform == "win32" else "utf-8",
            errors="replace"
        )
        if r.returncode == 0:
            result["nodriver"] = True
    except Exception:
        pass

    if not result["nodriver"]:
        result["errors"].append("nodriver 未安装，请运行 --install-deps")

    return result


def install_dependencies(mirror=False):
    """安装 Python 依赖到 venv"""
    if _is_in_venv():
        pip_args = [sys.executable, "-m", "pip", "install", "--quiet", "nodriver"]
    else:
        venv_python = _ensure_venv()
        pip_args = [venv_python, "-m", "pip", "install", "--quiet", "nodriver"]

    if mirror:
        pip_args.extend(["-i", "https://pypi.tuna.tsinghua.edu.cn/simple"])

    print(json.dumps({"action": "install_deps", "mirror": mirror, "cmd": " ".join(pip_args)}))

    try:
        result = subprocess.run(pip_args, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            return True
        elif not mirror:
            print(json.dumps({"action": "install_retry", "reason": "pip failed, retrying with mirror"}))
            return install_dependencies(mirror=True)
        else:
            print(json.dumps({"action": "install_failed", "stderr": result.stderr}))
            return False
    except subprocess.TimeoutExpired:
        if not mirror:
            print(json.dumps({"action": "install_retry", "reason": "timeout, retrying with mirror"}))
            return install_dependencies(mirror=True)
        return False


# ── CSV 缓存管理 ──────────────────────────────────────
def get_csv_path():
    """获取 CSV 文件路径"""
    workspace = os.environ.get("OPENCLAW_WORKSPACE", "")
    if workspace:
        return os.path.join(workspace, CSV_FILENAME)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", CSV_FILENAME)


def read_csv_cache(csv_path):
    """读取 CSV 缓存，返回按品牌分组的记录"""
    if not os.path.isfile(csv_path):
        return {}

    records = {}
    try:
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                brand = row.get("查询品牌", "").strip().upper()
                if not brand:
                    continue
                if brand not in records:
                    records[brand] = []
                records[brand].append(row)
    except Exception as e:
        print(json.dumps({"action": "csv_read_error", "error": str(e)}))
        return {}

    return records


def is_cache_valid(records, max_age_days=7):
    """判断缓存是否在有效期内"""
    if not records:
        return False

    latest_time = None
    for r in records:
        ts = r.get("查询时间", "")
        try:
            t = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            if latest_time is None or t > latest_time:
                latest_time = t
        except ValueError:
            continue

    if latest_time is None:
        return False

    age = (datetime.now() - latest_time).total_seconds() / 86400
    return age < max_age_days


def write_csv_cache(csv_path, brand, new_records):
    """写入/更新 CSV 缓存（替换该品牌旧记录，保留其他品牌）"""
    existing = []
    if os.path.isfile(csv_path):
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("查询品牌", "").strip().upper() != brand.upper():
                    existing.append(row)

    all_records = existing + new_records

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(all_records)


# ── CDP 辅助函数 ──────────────────────────────────────
def _cdp_value(send_result):
    """从 page.send(cdp.runtime.evaluate()) 返回的 tuple 中提取值"""
    if send_result and len(send_result) >= 1:
        remote_obj = send_result[0]
        return remote_obj.value if remote_obj else None
    return None


async def _cdp_eval(page, expression):
    """执行 JS 并返回值"""
    import nodriver as uc
    result = await page.send(uc.cdp.runtime.evaluate(
        expression, return_by_value=True
    ))
    return _cdp_value(result)


# ── 浏览器自动化查询 ──────────────────────────────────
def _get_python_for_search():
    """获取用于执行查询的 Python（优先 venv）"""
    venv_python = _get_venv_python()
    if venv_python:
        return venv_python
    return sys.executable


async def do_search(brand, chrome_path=None):
    """使用 nodriver 执行海关备案查询"""
    import nodriver as uc
    import asyncio

    results = []
    browser = None

    try:
        # 启动浏览器
        kwargs = {}
        if chrome_path:
            kwargs["browser_executable_path"] = chrome_path
        browser = await uc.start(**kwargs)

        page = await browser.get(CUSTOMS_URL)

        # 等待 WAF 验证通过 + 页面真正加载
        # 轮询检测页面内容，比固定 sleep 更可靠
        loaded = False
        for i in range(TIMEOUT_PAGE):
            await asyncio.sleep(1)
            try:
                html = await page.get_content()
                if len(html) > 500:
                    loaded = True
                    break
            except:
                pass

        if not loaded:
            print(json.dumps({"action": "error", "message": "页面加载超时，WAF 验证未通过"}))
            return results

        # 额外等待确保动态内容加载完成
        await asyncio.sleep(2)

        # 通过 CDP Runtime.evaluate 查找输入框并输入
        # 实际页面表单结构:
        #   input[name="APPLY_USER_NAME"] — 权利人名称
        #   input[name="RECORD_NAME"]     — 权利名称
        #   input[name="RECORD_NUM"]      — 备案号
        #   input[name="REGISTER_NUM"]    — 权利号
        #   input#find_btn  value="模糊查询"
        #   input#find_btn2 value="精确查询"
        input_result = await _cdp_eval(page, f"""
            (function() {{
                // 找权利名称输入框
                let el = document.querySelector('input[name="RECORD_NAME"]');
                if (!el) {{
                    // 备选：第二个文本输入框
                    let inputs = document.querySelectorAll('input[type="text"]');
                    if (inputs.length > 1) el = inputs[1];
                    else if (inputs.length > 0) el = inputs[0];
                }}
                if (!el) return {{ found: false }};

                // 用原生 setter 输入，触发 input/change 事件
                let nativeSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                nativeSetter.call(el, {json.dumps(brand)});
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));

                return {{ found: true, name: el.name, id: el.id, value: el.value }};
            }})()
        """)

        if not input_result or not input_result.get("found"):
            print(json.dumps({"action": "error", "message": "未找到权利名称输入框"}))
            return results

        await asyncio.sleep(0.5)

        # 点击模糊查询按钮
        btn_result = await _cdp_eval(page, """
            (function() {
                // 精确匹配模糊查询按钮
                let btn = document.querySelector('input#find_btn');
                if (btn && btn.value === '模糊查询') {
                    btn.click();
                    return { clicked: true, value: btn.value };
                }
                // 备选匹配
                let buttons = document.querySelectorAll('input[type="button"]');
                for (let b of buttons) {
                    if (b.value && b.value.includes('模糊查询')) {
                        b.click();
                        return { clicked: true, value: b.value };
                    }
                }
                return { clicked: false };
            })()
        """)

        if not btn_result or not btn_result.get("clicked"):
            print(json.dumps({"action": "error", "message": "未找到模糊查询按钮"}))
            return results

        # 等待结果加载
        await asyncio.sleep(5)

        # 通过 CDP 从结果表格中提取结构化数据
        # 页面表格有隐藏列（如数据库ID），需要跳过
        # 使用 JS 直接提取，按"表头列名"匹配来定位正确字段
        result_data = await _cdp_eval(page, """
            (function() {
                let rows = [];
                // 先找表头，确定列位置
                let allTrs = document.querySelectorAll('table tr');
                let headerMap = {};
                for (let tr of allTrs) {
                    let ths = tr.querySelectorAll('th');
                    if (ths.length > 0) {
                        ths.forEach((th, i) => {
                            headerMap[th.textContent.trim()] = i;
                        });
                        break;
                    }
                }
                
                // 如果没有 th，用 td 表头行推断
                if (Object.keys(headerMap).length === 0) {
                    for (let tr of allTrs) {
                        let tds = tr.querySelectorAll('td');
                        if (tds.length >= 8) {
                            let first = tds[0].textContent.trim();
                            if (first === '权利标识' || first === '权利名称') {
                                tds.forEach((td, i) => {
                                    headerMap[td.textContent.trim()] = i;
                                });
                                break;
                            }
                        }
                    }
                }
                
                // 提取数据行
                for (let tr of allTrs) {
                    let tds = tr.querySelectorAll('td');
                    if (tds.length >= 8) {
                        let cells = Array.from(tds).map(td => td.textContent.trim());
                        // 跳过表头行
                        if (cells[0] === '权利标识' || cells[0] === '权利名称') continue;
                        // 跳过空行
                        if (!cells.some(c => c)) continue;
                        
                        // 返回完整 cells + headerMap
                        rows.push(cells);
                    }
                }
                return { headers: headerMap, rows: rows };
            })()
        """)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if result_data and result_data.get("rows"):
            headers = result_data.get("headers", {})
            for cells in result_data["rows"]:
                # 根据表头映射取值，比固定偏移更可靠
                def h(key):
                    """按表头名取值"""
                    idx = headers.get(key, -1)
                    return cells[idx] if idx >= 0 and idx < len(cells) else ""
                
                record = {
                    "查询品牌": brand,
                    "权利名称": h("权利名称") or h("权利标识"),
                    "权利人名称": h("权利人名称"),
                    "权利人国别": h("权利人国别"),
                    "权利号": h("权利号"),
                    "备案号": h("备案号"),
                    "权利类别": h("权利类别"),
                    "商品分类": _format_category(h("商品分类")),
                    "备案状态": h("备案状态"),
                    "备案开始日期": h("备案开始日期"),
                    "备案截止日期": h("备案截止日期"),
                    "查询时间": now_str,
                }
                # 过滤掉表头行、分页信息行、空行
                rn = record["权利名称"]
                if rn in ("权利标识", "权利名称", "", None):
                    continue
                if "共" in rn and "页" in rn:
                    continue
                if "条" in rn and "共" in rn:
                    continue
                results.append(record)

        # 如果表格解析失败，尝试从 innerText 解析
        if not results:
            result_text = await _cdp_eval(page, "document.body.innerText")
            if result_text:
                results = _parse_result_text(brand, result_text)

        # 最后尝试 HTML 正则
        if not results:
            page_html = await page.get_content()
            results = _parse_fallback(brand, page_html, now_str)

    except Exception as e:
        print(json.dumps({"action": "search_error", "brand": brand, "error": str(e)}))
    finally:
        if browser:
            try:
                browser.stop()
            except Exception:
                pass

    return results


def _parse_result_text(brand, text):
    """从页面 innerText 解析查询结果"""
    results = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 页面结果区域格式（每行用 tab 分隔）:
    # TRW    TRW知识产权公司    美国    244497    T2016-50578    国内注册    9    生效    2026-02-28    2036-02-27
    lines = text.split('\n')

    for line in lines:
        parts = [p.strip() for p in line.split('\t')]
        # 有效数据行：至少 6 列，且第一列不为空
        if len(parts) >= 6 and parts[0] and parts[0] not in ('权利标识', '权利名称'):
            record = {
                "查询品牌": brand,
                "权利名称": _nth(parts, 0),
                "权利人名称": _nth(parts, 1),
                "权利人国别": _nth(parts, 2),
                "权利号": _nth(parts, 3),
                "备案号": _nth(parts, 4),
                "权利类别": _nth(parts, 5),
                "商品分类": _format_category(_nth(parts, 6)),
                "备案状态": _nth(parts, 7),
                "备案开始日期": _nth(parts, 8),
                "备案截止日期": _nth(parts, 9),
                "查询时间": now_str,
            }
            # 过滤掉表头行
            if record["权利名称"] not in ("权利标识", "权利名称", "", None):
                results.append(record)

    return results


def _format_category(cat):
    """格式化商品分类，如 '9' → '第9类'"""
    if not cat:
        return ""
    cat = cat.strip()
    if cat.isdigit() and not cat.startswith("第"):
        return f"第{cat}类"
    return cat


def _nth(lst, idx):
    """安全取列表元素"""
    if idx < len(lst):
        return lst[idx]
    return ""


def _parse_fallback(brand, html, now_str):
    """备用解析：从 HTML 中用正则提取备案数据"""
    results = []
    row_pattern = re.compile(
        r'<td[^>]*>([^<]*)</td>\s*'
        r'<td[^>]*>([^<]*)</td>\s*'
        r'<td[^>]*>([^<]*)</td>\s*'
        r'<td[^>]*>([^<]*)</td>\s*'
        r'<td[^>]*>([^<]*)</td>',
        re.IGNORECASE
    )
    for m in row_pattern.finditer(html):
        cells = [g.strip() for g in m.groups()]
        if cells[0] and cells[0] != "权利名称":
            results.append({
                "查询品牌": brand,
                "权利名称": cells[0],
                "权利人名称": _nth(cells, 1),
                "权利人国别": _nth(cells, 2),
                "权利号": "",
                "备案号": _nth(cells, 3),
                "权利类别": "",
                "商品分类": "",
                "备案状态": _nth(cells, 4),
                "备案开始日期": "",
                "备案截止日期": "",
                "查询时间": now_str,
            })
    return results


def run_search(brand, chrome_path=None):
    """同步入口"""
    import asyncio
    return asyncio.run(do_search(brand, chrome_path))


# ── 风险评估 ──────────────────────────────────────────
def assess_risk(records):
    """根据备案状态评估风险等级和物流建议"""
    if not records:
        return {
            "level": "low",
            "emoji": "🟢",
            "label": "低风险",
            "advice": "该品牌未在海关备案系统查到记录，通关风险较低。",
        }

    statuses = [r.get("备案状态", "").strip() for r in records]
    has_active = any(s == "生效" for s in statuses)
    has_expired = any(s in ("到期",) for s in statuses)
    has_cancelled = any(s in ("撤销", "注销") for s in statuses)

    if has_active:
        return {
            "level": "high",
            "emoji": "🔴",
            "label": "高风险",
            "advice": "品牌已备案生效，海关重点监控。请确认货物是否有品牌授权书，无授权情况下退运/扣货风险极高。",
        }
    elif has_expired:
        return {
            "level": "medium",
            "emoji": "🟡",
            "label": "中风险",
            "advice": "备案已到期但曾有保护记录，仍存在追溯风险，建议谨慎处理。",
        }
    elif has_cancelled:
        return {
            "level": "low",
            "emoji": "🟢",
            "label": "低风险",
            "advice": "备案已撤销/注销，常规通关即可，但建议定期复查。",
        }
    else:
        return {
            "level": "low",
            "emoji": "🟢",
            "label": "低风险",
            "advice": "未发现生效备案，通关风险较低。",
        }


# ── 主流程 ────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="海关知识产权备案查询")
    parser.add_argument("--brand", type=str, help="要查询的品牌名称")
    parser.add_argument("--check-env", action="store_true", help="检测运行环境")
    parser.add_argument("--install-deps", action="store_true", help="安装依赖")
    parser.add_argument("--cache-file", type=str, help="CSV 缓存文件路径")
    args = parser.parse_args()

    if args.check_env:
        result = check_env()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if not result["errors"] else 1)

    if args.install_deps:
        ok = install_dependencies()
        print(json.dumps({"installed": ok}))
        sys.exit(0 if ok else 1)

    if not args.brand:
        print(json.dumps({"error": "请通过 --brand 指定品牌名称"}))
        sys.exit(1)

    # 如果不在 venv 中且 venv 存在，用 venv python 重新执行自己
    if not _is_in_venv():
        venv_python = _get_venv_python()
        if venv_python:
            os.execv(venv_python, [venv_python] + sys.argv)

    brand = args.brand.strip()
    csv_path = args.cache_file or get_csv_path()

    # 环境检测
    env = check_env()
    if env["errors"]:
        print(json.dumps({"action": "env_check_failed", "errors": env["errors"]}, ensure_ascii=False))
        sys.exit(1)

    # 检查缓存
    cache = read_csv_cache(csv_path)
    brand_key = brand.upper()
    cached = cache.get(brand_key, [])

    if cached and is_cache_valid(cached):
        risk = assess_risk(cached)
        output = {
            "brand": brand,
            "source": "cache",
            "count": len(cached),
            "records": cached,
            "risk": risk,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        sys.exit(0)

    # 在线查询
    print(json.dumps({"action": "searching", "brand": brand, "source": "online"}, ensure_ascii=False))

    results = run_search(brand, chrome_path=env["chrome_path"])

    if results:
        write_csv_cache(csv_path, brand, results)

    risk = assess_risk(results)
    output = {
        "brand": brand,
        "source": "online",
        "count": len(results),
        "records": results,
        "risk": risk,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
