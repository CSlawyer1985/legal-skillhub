# -*- coding: utf-8 -*-
"""
差旅费报销数据校验脚本
在生成文档前运行，检查数据完整性并打印"按截图分组复核"输出。

用法：
    python validate_data.py

校验内容：
  1. 必填字段完整性
  2. 日期格式 (YYYY-MM-DD)
  3. 时间格式 (HH:MM 或 —)
  4. 金额为正数
  5. 序号连续 (1..N)
  6. 总额 = 各项求和
  7. 截图文件存在
  8. 按截图分组复核（同图多日期时警告，防止误套首日期）
"""
import json
import os
import sys
import re
from collections import defaultdict

DATA_PATH = r".\expense_data.json"
IMAGE_DIRS = [r".\images", r"."]
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME_RE = re.compile(r"^\d{2}:\d{2}$")

REQUIRED_FIELDS = ["seq", "date", "time", "type", "from", "to", "amount", "img", "note"]


def find_image(case_short, img_name):
    """在 IMAGE_DIRS/<case_short>/ 下查找图片"""
    if not img_name or img_name == "__no_image__":
        return None
    for d in IMAGE_DIRS:
        p = os.path.join(d, case_short, img_name)
        if os.path.exists(p):
            return p
    return None


def validate():
    if not os.path.exists(DATA_PATH):
        print(f"❌ 找不到数据文件: {DATA_PATH}")
        sys.exit(1)

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 复核提醒横幅：每次运行打印关键规则
    print("=" * 60)
    print("⚠ 复核提醒（生成前必看）")
    print("=" * 60)
    print("  1. 同图多日期：每条订单对照自身紧邻的日期表头，禁止套首日期")
    print("  2. 唯一丢弃的时间：手机状态栏系统时间（有电池/信号/WiFi图标，通常只有时分无日期）")
    print("  3. 其他所有时间都保留：下单/购票/支付/乘车时间都是确定行程的依据，绝不丢弃")
    print("  4. 优先用行程时间（乘车/出发/起飞）；没有行程时间时用下单/购票/支付时间代替")
    print("  5. 拿不准是不是状态栏时间→不要擅自决定，问用户或在文档末尾红字标注待确认")
    print("=" * 60)

    errors = []
    warnings = []

    for case_idx, case in enumerate(data):
        case_name = case.get("case_name", f"案件{case_idx + 1}")
        case_short = case.get("case_short", "")
        items = case.get("items", [])

        print(f"\n{'=' * 60}")
        print(f"案件: {case_name}  (共 {len(items)} 条)")
        print(f"{'=' * 60}")

        # --- 1. 逐条字段校验 ---
        print("\n[1] 字段校验")
        for i, item in enumerate(items):
            seq = item.get("seq", f"?{i}")
            for field in REQUIRED_FIELDS:
                if field not in item:
                    errors.append(f"  序号{seq}: 缺少字段 '{field}'")

            # 日期格式
            date_val = item.get("date", "")
            if date_val and not DATE_RE.match(str(date_val)):
                errors.append(f"  序号{seq}: 日期格式错误 '{date_val}'（应为 YYYY-MM-DD）")

            # 时间格式
            time_val = item.get("time", "")
            if time_val and time_val != "—" and not TIME_RE.match(str(time_val)):
                errors.append(f"  序号{seq}: 时间格式错误 '{time_val}'（应为 HH:MM 或 —）")

            # 金额
            amount = item.get("amount", 0)
            try:
                amt = float(amount)
                if amt <= 0:
                    warnings.append(f"  序号{seq}: 金额 <= 0 ({amt})")
            except (ValueError, TypeError):
                errors.append(f"  序号{seq}: 金额不是数字 '{amount}'")

            # 截图文件存在
            img_name = item.get("img", "")
            if img_name and img_name != "__no_image__":
                img_path = find_image(case_short, img_name)
                if not img_path:
                    errors.append(f"  序号{seq}: 截图文件不存在 '{img_name}'（在 images/{case_short}/ 下未找到）")

        if not errors:
            print("  ✓ 全部字段校验通过")

        # --- 2. 序号连续性 ---
        print("\n[2] 序号连续性")
        seqs = [item.get("seq") for item in items]
        expected = list(range(1, len(items) + 1))
        if seqs == expected:
            print(f"  ✓ 序号连续 1..{len(items)}")
        else:
            errors.append(f"  序号不连续: 实际 {seqs}，应为 {expected}")

        # --- 3. 日期排序 ---
        print("\n[3] 日期排序")
        sorted_ok = True
        for i in range(1, len(items)):
            prev = items[i - 1]
            curr = items[i]
            prev_key = (prev.get("date", ""), prev.get("time", "") if prev.get("time", "") != "—" else "99:99")
            curr_key = (curr.get("date", ""), curr.get("time", "") if curr.get("time", "") != "—" else "99:99")
            if curr_key < prev_key:
                sorted_ok = False
                warnings.append(f"  序号{prev.get('seq')} → 序号{curr.get('seq')}: 日期/时间未排序 ({prev_key} → {curr_key})")
        if sorted_ok:
            print("  ✓ 日期时间排序正确")
        else:
            print("  ⚠ 排序异常，详见警告")

        # --- 4. 总额校验 ---
        print("\n[4] 总额校验")
        actual_total = round(sum(float(item.get("amount", 0)) for item in items), 2)
        stored_total = round(float(case.get("total", 0)), 2)
        if actual_total == stored_total:
            print(f"  ✓ 总额一致: ¥{actual_total:.2f}")
        else:
            warnings.append(f"  总额不一致: 存储={stored_total}, 实际求和={actual_total}（生成脚本会自动校正）")
            print(f"  ⚠ 总额不一致: 存储={stored_total}, 实际={actual_total}（生成时会自动校正）")

        # --- 5. 按截图分组复核（核心防错）---
        print("\n[5] 按截图分组复核（请逐图核对每条日期是否与截图日期表头一致）")
        img_groups = defaultdict(list)
        for item in items:
            img_name = item.get("img", "")
            if img_name and img_name != "__no_image__":
                img_groups[img_name].append(item)

        for img_name, group_items in img_groups.items():
            dates = sorted(set(it.get("date", "") for it in group_items))
            seqs_str = ",".join(str(it.get("seq")) for it in group_items)
            multi_date_flag = ""
            if len(dates) > 1:
                multi_date_flag = f"  ⚠ 本图含 {len(dates)} 个不同日期: {', '.join(dates)}"
                warnings.append(f"  截图 {img_name} 含多个日期({', '.join(dates)})，请回看截图确认每条序号对应正确的乘车日期表头")

            # 截图文件名太长则截断显示
            display_name = img_name if len(img_name) <= 24 else img_name[:21] + "..."
            print(f"\n  📷 [{display_name}] 共{len(group_items)}条 (序号{seqs_str}){multi_date_flag}")
            for it in group_items:
                date_val = it.get("date", "—")
                time_val = it.get("time", "—")
                type_val = it.get("type", "")
                from_val = it.get("from", "")
                to_val = it.get("to", "")
                amt = float(it.get("amount", 0))
                note = it.get("note", "")
                note_str = f"  [{note}]" if note else ""
                print(f"     序号{it.get('seq'):>2}  {date_val} {time_val:>5}  {type_val:<22}  {from_val}→{to_val}  ¥{amt:>8.2f}{note_str}")

        # --- 6. 预支信息 ---
        print("\n[6] 预支信息")
        prep = case.get("prepayment")
        if prep:
            print(f"  预支金额: ¥{prep.get('amount', 0):.2f}  日期: {prep.get('date', '—')}  备注: {prep.get('note', '')}")
            prep_img = prep.get("img", "")
            if prep_img:
                prep_path = find_image(case_short, prep_img)
                if prep_path:
                    print(f"  ✓ 预支凭证存在: {prep_img}")
                else:
                    errors.append(f"  预支凭证文件不存在: {prep_img}")
        else:
            print("  无预支（当事人未预支差旅费）")

    # --- 汇总 ---
    print(f"\n{'=' * 60}")
    print("校验汇总")
    print(f"{'=' * 60}")
    if errors:
        print(f"\n❌ 发现 {len(errors)} 个错误：")
        for e in errors:
            print(f"  {e}")
    else:
        print("\n✅ 无错误")

    if warnings:
        print(f"\n⚠ 发现 {len(warnings)} 个警告：")
        for w in warnings:
            print(f"  {w}")
    else:
        print("✅ 无警告")

    print(f"\n{'=' * 60}")
    if errors:
        print("❌ 存在错误，请修复后再生成文档！")
        sys.exit(1)
    elif warnings:
        print("⚠ 存在警告，请确认无误后再生成文档。")
    else:
        print("✅ 数据校验全部通过，可以生成文档。")


if __name__ == "__main__":
    validate()
