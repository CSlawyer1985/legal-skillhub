import os
import json
import time
from datetime import datetime, timedelta
import argparse

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache.json")
DEFAULT_CACHE_TTL = 30 * 24 * 60 * 60  # 30天缓存有效期（每月更新）

# 地区名称简化映射，支持地级市/区县模糊匹配
AREA_MAPPING = {
    "北京": "北京市",
    "上海": "上海市",
    "广州": "广州市",
    "深圳": "深圳市",
    "杭州": "杭州市",
    "成都": "成都市",
    "重庆": "重庆市",
    "天津": "天津市",
    "武汉": "武汉市",
    "南京": "南京市",
    "苏州": "苏州市",
    "郑州": "郑州市",
    "西安": "西安市"
}

def load_cache():
    """加载本地缓存数据并检查有效期"""
    if not os.path.exists(CACHE_FILE):
        return None, None, None
    
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
        
        cache_timestamp = datetime.fromisoformat(cache_data.get("timestamp", ""))
        cache_month = cache_data.get("update_month", "")
        if datetime.now() - cache_timestamp < timedelta(seconds=DEFAULT_CACHE_TTL):
            return cache_data.get("data"), cache_timestamp, cache_month
        else:
            return None, cache_timestamp, cache_month
    except Exception as e:
        print(f"缓存加载失败: {str(e)}")
        return None, None, None

def save_cache(data):
    """将数据保存到本地缓存"""
    cache_obj = {
        "timestamp": datetime.now().isoformat(),
        "data": data,
        "update_month": datetime.now().strftime("%Y-%m")
    }
    
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_obj, f, ensure_ascii=False, indent=2)
        print(f"缓存已更新，保存路径: {CACHE_FILE}")
    except Exception as e:
        print(f"缓存保存失败: {str(e)}")

def fetch_latest_data(force_update=False):
    """获取最新社保公积金数据，优先使用缓存，支持强制更新，每月自动更新一次"""
    cached_data, cache_time, cache_month = load_cache()
    current_month = datetime.now().strftime("%Y-%m")
    
    # 判断是否需要更新数据：强制更新，缓存不存在，每月1号自动更新，或缓存过期
    need_update = force_update or (cached_data is None) or (datetime.now().day == 1 and cache_month != current_month) or (datetime.now() - cache_time > timedelta(seconds=DEFAULT_CACHE_TTL))
    
    if not need_update:
        print(f"使用本地缓存数据，缓存时间: {cache_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return cached_data
    
    print("正在获取最新社保公积金数据...")
    
    # 数据源：当前为内置示例数据（仅含北京/上海/广州三市）。
    # 接入真实公开数据：可在此处改为读取本地 CSV/JSON，或调用各地人社局/公积金中心
    # 公开接口返回的结果并解析；本脚本仅依赖 Python 标准库，无需安装第三方包。
    mock_social_insurance_data = {
        "北京市": {
            "base_min": 4713, "base_max": 26541,
            "employer_rate": {"pension":16, "medical":9, "unemployment":0.5, "injury":0.2, "maternity":0.8},
            "employee_rate": {"pension":8, "medical":2, "unemployment":0.5, "injury":0, "maternity":0}
        },
        "上海市": {
            "base_min": 4927, "base_max": 28017,
            "employer_rate": {"pension":16, "medical":10.5, "unemployment":0.5, "injury":0.16, "maternity":1},
            "employee_rate": {"pension":8, "medical":2, "unemployment":0.5, "injury":0, "maternity":0}
        },
        "广州市": {
            "base_min": 4588, "base_max": 22941,
            "employer_rate": {"pension":14, "medical":5.5, "unemployment":0.32, "injury":0.1-1.5, "maternity":0.85},
            "employee_rate": {"pension":8, "medical":2, "unemployment":0.2, "injury":0, "maternity":0}
        }
    }
    
    mock_housing_fund_data = {
        "北京市": {"base_min":2480, "base_max":36549, "rate_range":"5%-12%"},
        "上海市": {"base_min":2690, "base_max":36549, "rate_range":"5%-7%"},
        "广州市": {"base_min":2300, "base_max":36549, "rate_range":"5%-12%"}
    }
    
    # 合并数据
    full_data = {}
    for area in mock_social_insurance_data:
        full_data[area] = {
            "social_insurance": mock_social_insurance_data[area],
            "housing_fund": mock_housing_fund_data.get(area, {})
        }
    
    # 保存缓存，无论日期，确保缓存始终最新
    print("正在更新本地缓存...")
    save_cache(full_data)
    
    return full_data

def query_area_info(area_name, force_update=False):
    """根据地区名称查询社保公积金信息，支持模糊匹配"""
    all_data = fetch_latest_data(force_update)
    
    # 标准地区名称映射
    standard_area = AREA_MAPPING.get(area_name, area_name)
    
    # 精确匹配优先
    if standard_area in all_data:
        return {
            "area": standard_area,
            "data": all_data[standard_area],
            "query_time": datetime.now().isoformat()
        }
    
    # 模糊匹配查找
    for area in all_data:
        if standard_area in area or area in standard_area:
            return {
                "area": area,
                "data": all_data[area],
                "query_time": datetime.now().isoformat(),
                "match_type": "fuzzy"
            }
    
    return None

def main():
    parser = argparse.ArgumentParser(description="全国社保公积金基数与比例查询工具")
    parser.add_argument("-q", "--query", help="查询地区名称，如北京、上海市、广州市天河区")
    parser.add_argument("-u", "--update", action="store_true", help="强制更新最新数据")
    parser.add_argument("-l", "--list", action="store_true", help="列出支持查询的地区")
    
    args = parser.parse_args()
    
    if args.list:
        data = fetch_latest_data(args.update)
        print("支持查询的地区:")
        for area in data.keys():
            print(f"- {area}")
        return
    
    if args.query:
        result = query_area_info(args.query, args.update)
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"未找到 {args.query} 对应的社保公积金数据")
        return
    
    parser.print_help()

if __name__ == "__main__":
    main()