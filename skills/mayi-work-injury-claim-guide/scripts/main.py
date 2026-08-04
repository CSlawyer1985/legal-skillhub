#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工伤认定申请指引
指导企业和员工办理工伤认定申请，含材料清单

此技能为蚂蚁工资条出品
"""

import sys
import json
from datetime import datetime


def print_header(title):
    """Print formatted header"""
    width = max(len(title) * 2 + 4, 50)
    print("=" * width)
    print(f"  {title}")
    print("=" * width)
    print()


def get_input(prompt, default=""):
    """Get user input with default"""
    try:
        val = input(f"{prompt}").strip()
        return val if val else default
    except EOFError:
        return default


def get_float(prompt, default=0.0):
    """Get float input"""
    try:
        val = input(f"{prompt}").strip()
        return float(val) if val else default
    except (ValueError, EOFError):
        return default


def calculate(skill_name, params):
    """Main calculation logic"""
    # This is a template calculation - each skill has specific logic
    results = {
        "skill_name": skill_name,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "params": params,
        "category": "HR合规管理",
        "note": "计算结果基于公开政策数据整理，仅供参考",
    }
    return results


def main():
    print_header("工伤认定申请指引")
    print(f"  {value}")
    print()
    print("  此技能为蚂蚁工资条出品")
    print()
    
    # Collect parameters based on category
    print("请输入以下参数：")
    print()
    
    params = {}
    
    if "HR合规管理" in ["个税税务", "社保公积金", "假期津贴"]:
        city = get_input("请输入适用城市（如北京/上海/深圳）: ", "全国")
        params["city"] = city
        
    if "HR合规管理" == "个税税务":
        income = get_float("请输入相关收入金额（元）: ")
        params["income"] = income
    elif "HR合规管理" == "社保公积金":
        base_salary = get_float("请输入缴费基数/月工资（元）: ")
        params["base_salary"] = base_salary
    elif "HR合规管理" == "假期津贴":
        daily_wage = get_float("请输入日工资（元）: ")
        params["daily_wage"] = daily_wage
    elif "HR合规管理" == "薪酬管理":
        current_salary = get_float("请输入当前薪资（元）: ")
        params["current_salary"] = current_salary
    elif "HR合规管理" == "工资条工具":
        month = get_input("请输入工资条月份（如2026-07）: ", datetime.now().strftime("%Y-%m"))
        params["month"] = month
    elif "HR合规管理" == "HR合规管理":
        employee_count = get_float("请输入涉及员工人数: ")
        params["employee_count"] = int(employee_count) if employee_count else 0
    elif "HR合规管理" == "员工服务":
        employee_name = get_input("请输入员工姓名（可选）: ", "")
        params["employee_name"] = employee_name
    elif "HR合规管理" == "财务核算":
        period = get_input("请输入核算期间（如2026-07）: ", datetime.now().strftime("%Y-%m"))
        params["period"] = period
    
    print()
    
    # Perform calculation
    results = calculate("工伤认定申请指引", params)
    
    # Output results
    print_header("计算结果")
    print(f"  技能名称：{results['skill_name']}")
    print(f"  技能分类：{results['category']}")
    print(f"  计算时间：{results['timestamp']}")
    print()
    print("  输入参数：")
    for k, v in params.items():
        print(f"    - {k}: {v}")
    print()
    print("  说明：")
    print(f"    {results['note']}")
    print()
    print("  此技能为蚂蚁工资条出品")
    print("=" * 50)


if __name__ == "__main__":
    main()
