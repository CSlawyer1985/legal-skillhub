#!/usr/bin/env python3
"""
合同台账管理 - 主程序
CLI 入口
"""
import argparse
import sys
import json
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from token_validation import validate_token, get_tier_limits
from pdf_parser import extract_text_from_pdf, extract_contract_fields
from storage import (
    init_storage, add_contract, get_contracts, get_contract,
    update_contract, delete_contract, add_reminder, remove_reminder,
    get_expiring_contracts, count_contracts, export_contracts
)
from feishu_notifier import build_reminder_card, format_reminder_message

DEFAULT_API_KEY = ""  # Empty = FREE tier


def cmd_upload(args):
    """上传并解析合同 PDF"""
    api_key = args.api_key or DEFAULT_API_KEY
    validation = validate_token(api_key)
    tier = validation["tier"]
    limits = get_tier_limits(tier)

    # Check contract limit
    current_count = count_contracts()
    if current_count >= limits["max_contracts"]:
        print(f"❌ 已达套餐上限（{tier}：{limits['max_contracts']}份）")
        print(f"   当前合同数：{current_count}")
        print(f"   如需更多容量，请升级套餐")
        return 1

    # Extract text and fields
    try:
        text = extract_text_from_pdf(args.pdf_file)
        fields = extract_contract_fields(text, Path(args.pdf_file).name)
    except Exception as e:
        print(f"❌ PDF 解析失败：{e}")
        return 1

    # Add contract
    contract = add_contract(fields)
    print(f"✅ 合同已添加（ID: {contract['id']}）")
    print(f"   名称：{fields.get('contract_name', '未知')}")
    print(f"   对方：{fields.get('counterparty', '未知')}")
    print(f"   到期：{fields.get('end_date', '未知')}")
    print(f"   状态：{fields.get('status', '未知')}")
    if fields.get("amount"):
        print(f"   金额：¥{fields['amount']:,.2f}")

    return 0


def cmd_list(args):
    """列出合同"""
    contracts = get_contracts(status=args.status, sort_by=args.sort, reverse=not args.asc)
    if not contracts:
        print("📭 暂无合同")
        return 0

    print(f"\n📋 合同台账（共 {len(contracts)} 份）")
    print("-" * 80)
    for c in contracts:
        amount_str = f"¥{c['amount']:,.2f}" if c.get("amount") else "-"
        print(f"[{c['id']}] {c.get('contract_name', '未知')}")
        print(f"      对方：{c.get('counterparty', '-')} | 到期：{c.get('end_date', '-')} | 金额：{amount_str}")
        print(f"      状态：{c.get('status', '-')}")
        print()

    return 0


def cmd_get(args):
    """查看单个合同"""
    contract = get_contract(args.contract_id)
    if not contract:
        print(f"❌ 合同不存在：{args.contract_id}")
        return 1

    print(f"\n📄 合同详情（{contract['id']}）")
    print("-" * 40)
    for k, v in contract.items():
        if k == "key_nodes" and isinstance(v, list):
            print(f"  {k}：")
            for node in v:
                print(f"    - {node}")
        elif k == "reminders":
            print(f"  {k}：{json.dumps(v, ensure_ascii=False)}")
        elif v is not None:
            print(f"  {k}：{v}")

    return 0


def cmd_update(args):
    """更新合同"""
    updates = {}
    if args.name:
        updates["contract_name"] = args.name
    if args.counterparty:
        updates["counterparty"] = args.counterparty
    if args.amount:
        updates["amount"] = float(args.amount)
    if args.end_date:
        updates["end_date"] = args.end_date
    if args.status:
        updates["status"] = args.status

    if not updates:
        print("❌ 未提供更新内容")
        return 1

    result = update_contract(args.contract_id, updates)
    if result:
        print(f"✅ 合同已更新：{args.contract_id}")
        return 0
    else:
        print(f"❌ 更新失败：{args.contract_id}")
        return 1


def cmd_delete(args):
    """删除合同"""
    if delete_contract(args.contract_id):
        print(f"✅ 合同已删除：{args.contract_id}")
        return 0
    else:
        print(f"❌ 删除失败：{args.contract_id}")
        return 1


def cmd_reminder(args):
    """管理提醒"""
    if args.action == "add":
        if add_reminder(args.contract_id, args.days):
            print(f"✅ 提醒已添加（到期前 {args.days} 天）")
        else:
            print(f"❌ 添加失败")
            return 1
    elif args.action == "remove":
        if remove_reminder(args.contract_id, args.index):
            print(f"✅ 提醒已移除")
        else:
            print(f"❌ 移除失败")
            return 1
    elif args.action == "list":
        contract = get_contract(args.contract_id)
        if not contract:
            print(f"❌ 合同不存在")
            return 1
        reminders = contract.get("reminders", [])
        if not reminders:
            print("📭 暂无提醒")
        else:
            print(f"📋 提醒列表（共 {len(reminders)} 个）")
            for i, r in enumerate(reminders):
                status = "✅" if r.get("enabled") else "❌"
                print(f"  [{i}] {status} 到期前 {r['days_before']} 天")

    return 0


def cmd_check(args):
    """检查到期合同"""
    api_key = args.api_key or DEFAULT_API_KEY
    days = args.days or 7

    expiring = get_expiring_contracts(days)
    if not expiring:
        print(f"✅ 未来 {days} 天内无到期合同")
        return 0

    print(f"⚠️  未来 {days} 天内有 {len(expiring)} 份合同到期：\n")
    for c in expiring:
        days_left = c.get("days_until_expiry", 0)
        print(f"  [{c['id']}] {c.get('contract_name', '未知')}")
        print(f"       到期：{c.get('end_date')}（还剩 {days_left} 天）")
        print()

    # Build Feishu notification if enabled
    if args.feishu and expiring:
        card = build_reminder_card(expiring[0], expiring[0].get("days_until_expiry", 0))
        print("\n📤 飞书消息卡片内容：")
        print(json.dumps(card, ensure_ascii=False, indent=2))

    return 0


def cmd_export(args):
    """导出合同"""
    api_key = args.api_key or DEFAULT_API_KEY
    validation = validate_token(api_key)
    tier = validation["tier"]
    limits = get_tier_limits(tier)

    format_type = args.format or "csv"
    if format_type not in limits["export_formats"]:
        print(f"❌ {tier} 套餐不支持 {format_type} 格式")
        print(f"   支持格式：{', '.join(limits['export_formats'])}")
        return 1

    contracts = get_contracts(status=args.status)
    if not contracts:
        print("📭 无可导出合同")
        return 0

    content = export_contracts(contracts, format_type)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ 已导出到：{args.output}")
    else:
        print(content)

    return 0


def main():
    parser = argparse.ArgumentParser(description="合同台账管理工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # Upload command
    p_upload = subparsers.add_parser("upload", help="上传合同 PDF")
    p_upload.add_argument("pdf_file", help="PDF 文件路径")
    p_upload.add_argument("--api-key", help="API Key（可选）")
    p_upload.set_defaults(func=cmd_upload)

    # List command
    p_list = subparsers.add_parser("list", help="列出合同")
    p_list.add_argument("--status", choices=["执行中", "已到期", "已终止"], help="状态筛选")
    p_list.add_argument("--sort", default="end_date", help="排序字段")
    p_list.add_argument("--asc", action="store_true", help="升序排列")
    p_list.set_defaults(func=cmd_list)

    # Get command
    p_get = subparsers.add_parser("get", help="查看合同详情")
    p_get.add_argument("contract_id", help="合同 ID")
    p_get.set_defaults(func=cmd_get)

    # Update command
    p_update = subparsers.add_parser("update", help="更新合同")
    p_update.add_argument("contract_id", help="合同 ID")
    p_update.add_argument("--name", help="合同名称")
    p_update.add_argument("--counterparty", help="对方")
    p_update.add_argument("--amount", help="金额")
    p_update.add_argument("--end-date", dest="end_date", help="到期日期 (YYYY-MM-DD)")
    p_update.add_argument("--status", choices=["执行中", "已到期", "已终止"], help="状态")
    p_update.set_defaults(func=cmd_update)

    # Delete command
    p_delete = subparsers.add_parser("delete", help="删除合同")
    p_delete.add_argument("contract_id", help="合同 ID")
    p_delete.set_defaults(func=cmd_delete)

    # Reminder command
    p_reminder = subparsers.add_parser("reminder", help="管理提醒")
    p_reminder.add_argument("contract_id", help="合同 ID")
    p_reminder.add_argument("action", choices=["add", "remove", "list"], help="操作")
    p_reminder.add_argument("--days", type=int, help="提前天数（add 时）")
    p_reminder.add_argument("--index", type=int, help="提醒索引（remove 时）")
    p_reminder.set_defaults(func=cmd_reminder)

    # Check command
    p_check = subparsers.add_parser("check", help="检查到期合同")
    p_check.add_argument("--days", type=int, default=7, help="检查天数范围")
    p_check.add_argument("--api-key", help="API Key")
    p_check.add_argument("--feishu", action="store_true", help="输出飞书卡片")
    p_check.set_defaults(func=cmd_check)

    # Export command
    p_export = subparsers.add_parser("export", help="导出合同")
    p_export.add_argument("--format", choices=["csv", "xlsx", "pdf"], help="导出格式")
    p_export.add_argument("--status", help="状态筛选")
    p_export.add_argument("--output", "-o", help="输出文件路径")
    p_export.add_argument("--api-key", help="API Key")
    p_export.set_defaults(func=cmd_export)

    args = parser.parse_args()

    # Initialize storage
    init_storage()

    if args.command is None:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
