"""
Submit preservation order.
Usage: python submit_order.py <order_data.json>
  order_data.json format:
  {
    "credentialId": "xxx",
    "batchData": [
      {
        "hash": "xxx",
        "title": "xxx",
        "category": 101,
        "ossFileId": "xxx"
      }
    ]
  }
Output: orderNo and QR code URL
"""

import sys

from common import ensure_dirs, http_request, auth_header, save_json, TEMP_DIR


def submit_order(order_data_path):
    """Submit preservation order, return orderNo and code_url."""
    ensure_dirs()

    from common import load_json
    order_data = load_json(order_data_path)

    body = {
        "appId": "wxb4cf8b313474f183",
        "payChannel": "WECHAT_PAY",
        "paymentMethod": "NATIVE",
        "source": "AI_MINI",
        "remark": "",
        "credentialId": order_data["credentialId"],
        "storage": order_data.get("storage", True),
        "batchData": order_data["batchData"]
    }

    result = http_request(
        "POST",
        "/xrl-cloud-asset/v7/batch-micro-chain/order",
        headers=auth_header(),
        body=body
    )

    if result.get("success") and result.get("data"):
        order_no = result["data"].get("orderNo", "")
        code_url = ""
        prepay = result["data"].get("prepay", {})
        if prepay:
            code_url = prepay.get("code_url", "")

        # Save full response for later use
        save_json(f"{TEMP_DIR}/order_submit_resp.json", result)

        print(f"ORDER_SUCCESS|orderNo={order_no}|code_url={code_url}")
        return order_no, code_url
    else:
        msg = result.get("message", str(result))
        print(f"ORDER_FAILED|message={msg}")
        return None, None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python submit_order.py <order_data.json>")
        print("  order_data.json format:")
        print('  {"credentialId":"xxx","batchData":[{"hash":"xxx","title":"xxx","category":101,"ossFileId":"xxx"}]}')
        sys.exit(1)

    submit_order(sys.argv[1])
