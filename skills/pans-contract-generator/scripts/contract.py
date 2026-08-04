#!/usr/bin/env python3
"""GPU租赁协议合同生成器

生成标准GPU租赁协议，包含完整法律条款。
输出Markdown格式。
"""

import argparse
import sys
from datetime import datetime, timedelta


def generate_contract(client: str, gpu: str, count: int, price: float, duration: int) -> str:
    """生成GPU租赁协议Markdown文本"""

    today = datetime.now()
    end_date = today + timedelta(days=duration * 30)
    total_monthly = price * count
    total_contract = total_monthly * duration

    contract = f"""# GPU算力租赁服务协议

**合同编号：** GPU-{today.strftime("%Y%m%d")}-{hash(client) % 10000:04d}

**签订日期：** {today.strftime("%Y年%m月%d日")}

---

## 协议双方

**甲方（出租方）：** 算力服务提供商

**乙方（承租方）：** {client}

---

## 第一条 服务范围

1.1 甲方向乙方提供以下GPU算力租赁服务：

| 项目 | 规格 |
|------|------|
| GPU型号 | {gpu} |
| GPU数量 | {count} 张 |
| 租赁期限 | {duration} 个月（{today.strftime("%Y年%m月%d日")} 至 {end_date.strftime("%Y年%m月%d日")}） |
| 月租总价 | ¥{total_monthly:.2f} 万元 |

1.2 服务内容包括：
- GPU服务器托管及运行维护
- 7×24小时基础设施保障
- 网络接入及带宽保障
- 电力供应及温控保障
- 基础运维监控及告警

1.3 甲方保证提供的GPU设备均为正品行货，性能指标符合官方规格。

---

## 第二条 价格与付款条款

2.1 **收费标准：**

| 费用项 | 单价 | 数量 | 月费 |
|--------|------|------|------|
| {gpu} GPU租赁 | ¥{price:.2f} 万元/卡/月 | {count} 卡 | ¥{total_monthly:.2f} 万元 |

2.2 **合同总金额：** ¥{total_contract:.2f} 万元

2.3 **付款方式：**
- 按月预付，每月5日前支付当月费用
- 首期款项于合同生效后5个工作日内支付
- 逾期付款按日加收0.05%滞纳金

2.4 **价格调整：**
- 合同期内价格锁定，不受市场波动影响
- 合同续签时，按届时市场价重新协商

2.5 **发票：** 甲方在收到付款后10个工作日内开具增值税专用发票。

---

## 第三条 服务等级协议（SLA）

3.1 **可用性承诺：** GPU服务月可用率不低于99.9%（每月不可用时间≤43.8分钟）。

3.2 **故障响应：**

| 故障等级 | 响应时间 | 恢复时间 |
|----------|----------|----------|
| P0-完全不可用 | ≤15分钟 | ≤4小时 |
| P1-部分功能降级 | ≤30分钟 | ≤8小时 |
| P2-性能下降 | ≤2小时 | ≤24小时 |
| P3-咨询与建议 | ≤4小时 | ≤48小时 |

3.3 **SLA违约赔偿：**
- 月可用率99.9%~99.0%：赔偿月费的10%
- 月可用率99.0%~95.0%：赔偿月费的30%
- 月可用率低于95.0%：赔偿月费的50%
- 连续3个月未达SLA标准，乙方有权无责解约

3.4 以下情况不计入不可用时间：
- 计划内维护（提前48小时通知，每月不超过4小时）
- 乙方自主操作导致的故障
- 不可抗力事件

---

## 第四条 数据安全与隐私保护

4.1 甲方承诺采取合理的技术和管理措施保护乙方数据安全，包括但不限于：
- 数据传输加密（TLS 1.2+）
- 存储数据加密（AES-256）
- 网络隔离（VPC / 专属子网）
- 访问控制与审计日志

4.2 乙方对其数据享有完全的所有权和控制权。甲方不得访问、使用、复制或向第三方披露乙方数据，除非：
- 获得乙方书面授权
- 法律法规要求
- 紧急情况下的必要措施

4.3 数据留存与销毁：
- 合同期内，甲方持续保管乙方数据
- 合同终止后30日内，甲方应彻底销毁乙方所有数据
- 应乙方要求，提供数据销毁证明

4.4 安全事件通知：甲方在发现安全事件后24小时内通知乙方，并配合调查和补救。

---

## 第五条 知识产权

5.1 乙方在使用GPU算力过程中产生的所有成果（包括但不限于模型、数据、算法、软件）的知识产权归乙方所有。

5.2 甲方提供的平台软件、工具和管理系统的知识产权归甲方所有。

5.3 任何一方不得侵犯对方的知识产权。

---

## 第六条 保密条款

6.1 双方对在合作过程中获知的对方商业秘密、技术秘密及其他保密信息负有保密义务。

6.2 保密期限：合同期内及合同终止后3年。

6.3 保密信息不包括：
- 已公开或非因接收方过错变为公开的信息
- 接收方在披露前已合法拥有的信息
- 接收方从无保密义务的第三方合法获取的信息

6.4 违反保密义务的一方应赔偿对方因此遭受的全部损失。

---

## 第七条 违约责任

7.1 **甲方违约：**
- 未按约定提供GPU服务，按实际中断时间等比例退还费用
- 未达SLA标准，按第三条约定赔偿
- 擅自终止服务，退还剩余费用并支付等额1个月租金作为违约金

7.2 **乙方违约：**
- 逾期付款超过15日，甲方有权暂停服务
- 逾期付款超过30日，甲方有权终止合同并要求支付欠款及违约金
- 擅自转租或超范围使用，甲方有权终止合同

7.3 **不可抗力：** 因不可抗力导致无法履行合同的，受影响方应在48小时内通知对方，双方协商解决，均不承担违约责任。

---

## 第八条 合同期限与终止

8.1 本合同自双方签字盖章之日起生效，有效期{duration}个月。

8.2 终止条件：
- 合同期满自然终止
- 双方协商一致提前终止
- 一方严重违约，守约方书面通知终止
- 乙方连续3个月SLA不达标，乙方有权终止

8.3 合同终止后的处理：
- 甲方在30日内退还乙方预付但未使用的费用（扣除已发生费用）
- 乙方在15日内完成数据迁移
- 甲方在30日内销毁乙方全部数据

8.4 续签：任何一方有意续签，应在合同到期前30日书面通知对方。

---

## 第九条 争议解决

9.1 本协议的订立、效力、解释、履行及争议解决均适用中华人民共和国法律。

9.2 因本协议引起的争议，双方应首先通过友好协商解决。

9.3 协商不成的，任何一方均可向甲方所在地有管辖权的人民法院提起诉讼。

---

## 第十条 其他条款

10.1 本协议一式两份，双方各执一份，具有同等法律效力。

10.2 本协议未尽事宜，双方可另行签订补充协议。补充协议与本协议具有同等法律效力。

10.3 本协议的任何修改须经双方书面确认。

10.4 本协议附件为本协议不可分割的组成部分。

---

**甲方（盖章）：** ____________________　　　**乙方（盖章）：** ____________________

**授权代表：** ____________________　　　　**授权代表：** ____________________

**日期：** {today.strftime("%Y年%m月%d日")}　　　　　　　**日期：** {today.strftime("%Y年%m月%d日")}
"""

    return contract


def main():
    parser = argparse.ArgumentParser(description="GPU租赁协议合同生成器")
    parser.add_argument("--client", required=True, help="客户公司名称")
    parser.add_argument("--gpu", required=True, help="GPU型号（如H100/A100/L40S等）")
    parser.add_argument("--count", type=int, required=True, help="GPU数量")
    parser.add_argument("--price", type=float, required=True, help="单卡月租价格（万元）")
    parser.add_argument("--duration", type=int, required=True, help="租赁期限（月）")
    parser.add_argument("--output", help="输出文件路径（默认stdout）")

    args = parser.parse_args()

    # 参数校验
    if args.count <= 0:
        print("错误：GPU数量必须大于0", file=sys.stderr)
        sys.exit(1)
    if args.price <= 0:
        print("错误：价格必须大于0", file=sys.stderr)
        sys.exit(1)
    if args.duration <= 0:
        print("错误：租赁期限必须大于0", file=sys.stderr)
        sys.exit(1)

    contract = generate_contract(
        client=args.client,
        gpu=args.gpu,
        count=args.count,
        price=args.price,
        duration=args.duration,
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(contract)
        print(f"合同已生成：{args.output}", file=sys.stderr)
    else:
        print(contract)


if __name__ == "__main__":
    main()
