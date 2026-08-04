"""
Query order payment status (single query).
Usage: python query_order.py <orderNo>
Called after user confirms payment.
Output: ORDER_PAID|orderNo=xxx|detail=xxx|summary=... or ORDER_UNPAID|orderNo=xxx|payStatus=xxx
"""

import json
import sys

from common import ensure_dirs, http_request, auth_header, save_json, load_json, TEMP_DIR, CREDENTIAL_CACHE_PATH

# Category code to name mapping
CATEGORY_MAP = {
    101: "文章",
    102: "摄影",
    103: "设计",
    104: "绘画",
    199: "其它",
}


def query_order(order_no):
    """Query order status once. If PAID, save detail and print summary."""
    ensure_dirs()

    result = http_request(
        "GET",
        f"/xrl-cloud-asset/v7/batch-micro-chain/order/{order_no}",
        headers=auth_header()
    )

    if not result.get("success"):
        msg = result.get("message", str(result))
        print(f"QUERY_FAILED|message={msg}")
        return None

    data = result.get("data", {})
    pay_status = data.get("payStatus", "UNKNOWN")

    if pay_status == "PAID":
        # Save order detail
        detail_path = f"{TEMP_DIR}/order_detail.json"
        save_json(detail_path, result)

        # Extract summary info
        apps = data.get("apps", [])
        pay_price_fen = data.get("payPrice", 0)
        pay_price_yuan = pay_price_fen / 100 if pay_price_fen else 0

        # Load credential name from cache
        cert_name = ""
        try:
            cred = load_json(CREDENTIAL_CACHE_PATH)
            credentials = cred.get("credentials", [])
            if credentials:
                primary = credentials[0]
                for c in credentials:
                    if c.get("isPrimary"):
                        primary = c
                        break
                cert_name = primary.get("certName", "")
        except Exception:
            pass

        # Print structured output
        print(f"ORDER_PAID|orderNo={order_no}|detail={detail_path}")
        print(f"SUMMARY_START")
        print(f"订单号：{order_no}")
        print(f"权属人：{cert_name}")
        for app in apps:
            opus = app.get("opus", {})
            title = opus.get("title", "")
            category_code = opus.get("category", 199)
            category_name = CATEGORY_MAP.get(category_code, "其它")
            print(f"作品名称：{title}")
            print(f"作品类型：{category_name}")
        print(f"支付金额：{pay_price_yuan:.2f}元")
        print(f"SUMMARY_END")
    else:
        print(f"ORDER_UNPAID|orderNo={order_no}|payStatus={pay_status}")

    return pay_status


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python query_order.py <orderNo>")
        sys.exit(1)

    query_order(sys.argv[1])
