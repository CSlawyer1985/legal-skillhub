# 违法辞退赔偿金计算脚本
# 支持N、N+1、2N计算，含社平工资封顶规则

import argparse
import json
import os
from datetime import datetime, date

# 2023年度各地社平工资参考值（月均，元）
SOCIAL_AVG_SALARY = {
    "北京": 13887,
    "上海": 12849,
    "深圳": 14568,
    "广州": 12693,
    "杭州": 10739,
    "南京": 11000,
    "成都": 8693,
    "武汉": 9500,
    "重庆": 8500,
    "西安": 8200,
    "天津": 9300,
    "苏州": 10500,
    "长沙": 8800,
    "郑州": 7800,
    "青岛": 8900,
    "宁波": 10200,
    "济南": 8600,
    "合肥": 8400,
    "福州": 8700,
    "厦门": 9200,
}


def calculate_work_years(start_date: str, end_date: str) -> float:
    """计算工作年限，满6个月按1年，不满6个月按0.5年"""
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    total_days = (end - start).days
    total_months = total_days / 30.4375
    years = total_months / 12

    if years < 0.5:
        return 0.5
    # 满6个月不满1年按1年，之后每满1年+1
    full_years = int(years)
    remainder = years - full_years
    if remainder >= 0.5:
        full_years += 1
    return float(full_years)


def calculate_compensation(
    monthly_salary: float,
    work_years: float,
    city: str = None,
    compensation_type: str = "N",
    social_avg_salary: float = None,
):
    """
    计算经济补偿金或赔偿金

    Args:
        monthly_salary: 月平均工资
        work_years: 工作年限
        city: 城市（用于查询社平工资）
        compensation_type: N / N+1 / 2N
        social_avg_salary: 手动指定社平工资（优先于city）

    Returns:
        dict: 计算结果
    """
    # 确定社平工资
    if social_avg_salary is None:
        if city and city in SOCIAL_AVG_SALARY:
            social_avg_salary = SOCIAL_AVG_SALARY[city]
        else:
            social_avg_salary = 8000  # 默认参考值

    three_times_avg = social_avg_salary * 3

    # 判断是否需要封顶
    capped = False
    base_salary = monthly_salary
    capped_years = work_years

    if monthly_salary > three_times_avg:
        capped = True
        base_salary = three_times_avg
        if work_years > 12:
            capped_years = 12.0

    # 计算N
    n = base_salary * capped_years

    # 计算结果
    result = {
        "monthly_salary": monthly_salary,
        "work_years": work_years,
        "city": city or "未指定",
        "social_avg_salary": social_avg_salary,
        "three_times_avg": three_times_avg,
        "capped": capped,
        "base_salary": base_salary,
        "capped_years": capped_years,
        "N": round(n, 2),
        "N_plus_1": round(n + monthly_salary, 2),
        "2N": round(n * 2, 2),
        "type": compensation_type,
    }

    # 根据类型确定最终金额
    if compensation_type == "N":
        result["amount"] = result["N"]
    elif compensation_type == "N+1":
        result["amount"] = result["N_plus_1"]
    elif compensation_type == "2N":
        result["amount"] = result["2N"]
    else:
        result["amount"] = result["N"]

    result["amount"] = round(result["amount"], 2)
    return result


def generate_report(case_info: dict, output_dir: str):
    """生成赔偿金计算报告"""
    result = calculate_compensation(
        monthly_salary=case_info["monthly_salary"],
        work_years=calculate_work_years(
            case_info["start_date"], case_info["end_date"]
        ),
        city=case_info.get("city"),
        compensation_type=case_info.get("type", "2N"),
        social_avg_salary=case_info.get("social_avg_salary"),
    )

    work_years = result["work_years"]
    today = date.today().strftime("%Y年%m月%d日")

    report = f"""# 违法辞退赔偿金计算表

申请人：{case_info.get("employee_name", "（待填）")}

用人单位：{case_info.get("employer_name", "（待填）")}

所在地区：{result["city"]}

生成日期：{today}

---

## 基础信息

| 项目 | 内容 |
|------|------|
| 入职日期 | {case_info["start_date"]} |
| 解除日期 | {case_info["end_date"]} |
| 工作年限 | {work_years:.1f}年 |
| 月平均工资 | ¥{result["monthly_salary"]:,.2f} |
| 当地社平工资（参考） | ¥{result["social_avg_salary"]:,.2f} |
| 社平工资3倍封顶 | ¥{result["three_times_avg"]:,.2f} |
| 是否封顶 | {"是（按3倍社平计算，年限封顶12年）" if result["capped"] else "否"} |

## 赔偿方案对比

| 方案 | 适用情形 | 计算方式 | 金额(元) |
|------|---------|---------|---------|
| N（经济补偿金） | 合法解除（协商/裁员/预告解除） | {"社平3倍" if result["capped"] else "月工资"}{result["base_salary"]:,.0f} × {result["capped_years"]:.1f}个月 | {result["N"]:,.2f} |
| N+1（经济补偿+代通知金） | 第40条非过失性解除 | N + 月工资{result["monthly_salary"]:,.0f} | {result["N_plus_1"]:,.2f} |
| 2N（违法解除赔偿金） | 违法解除，不要求继续履行 | N × 2 | {result["2N"]:,.2f} |

## 推荐方案

**选定方案：{result["type"]}**

**赔偿金额：¥{result["amount"]:,.2f}**

## 计算说明

1. **月平均工资**：离职前12个月平均工资（税前，含奖金、津贴、补贴）
2. **工作年限**：满1年=1个月工资；满6个月不满1年=1个月工资；不满6个月=0.5个月工资
3. **封顶规则**：月工资超过当地上年度职工月平均工资3倍的，按3倍计算，年限最高12年
4. **社平工资**：以上数据为参考值，实际以当地人社局公布的上年度数据为准
5. **2N vs 继续**：违法解除时，劳动者可选择2N赔偿金或要求继续履行合同（补发争议期间工资）

> **注意：** 以上计算基于参考数据，实际金额以仲裁裁决/法院判决为准。建议咨询专业律师或拨打12348公共法律服务热线。
"""

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "赔偿金计算表.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    return output_path, result


def main():
    parser = argparse.ArgumentParser(
        description="违法辞退赔偿金计算工具（支持N/N+1/2N）"
    )
    parser.add_argument("--config", help="案件信息JSON文件路径")
    parser.add_argument("--output-dir", default=".", help="输出目录")
    parser.add_argument("--monthly-salary", type=float, help="月平均工资")
    parser.add_argument("--start-date", help="入职日期 YYYY-MM-DD")
    parser.add_argument("--end-date", help="解除日期 YYYY-MM-DD")
    parser.add_argument("--city", help="所在城市")
    parser.add_argument(
        "--type",
        choices=["N", "N+1", "2N"],
        default="2N",
        help="赔偿类型：N=经济补偿, N+1=补偿+代通知金, 2N=违法解除赔偿",
    )
    parser.add_argument("--social-avg-salary", type=float, help="手动指定社平工资")

    args = parser.parse_args()

    if args.config:
        with open(args.config, "r", encoding="utf-8") as f:
            case_info = json.load(f)
    else:
        case_info = {
            "monthly_salary": args.monthly_salary,
            "start_date": args.start_date,
            "end_date": args.end_date,
            "city": args.city,
            "type": args.type,
            "social_avg_salary": args.social_avg_salary,
            "employee_name": "（待填）",
            "employer_name": "（待填）",
        }

    output_path, result = generate_report(case_info, args.output_dir)

    print(f"赔偿金计算表已生成：{output_path}")
    print(f"工作年限：{result['work_years']:.1f}年")
    print(f"N（经济补偿金）：¥{result['N']:,.2f}")
    print(f"N+1（含代通知金）：¥{result['N_plus_1']:,.2f}")
    print(f"2N（违法解除赔偿金）：¥{result['2N']:,.2f}")
    print(f"选定方案({result['type']})金额：¥{result['amount']:,.2f}")
    print(f"是否封顶：{'是' if result['capped'] else '否'}")
    print(f"输出目录：{os.path.abspath(args.output_dir)}")


if __name__ == "__main__":
    main()
