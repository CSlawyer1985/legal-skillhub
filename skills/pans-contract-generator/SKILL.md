---
name: pans-contract-generator
description: |
  AI算力销售合同生成器。根据商定条款（客户名称、GPU型号、数量、价格、期限）
  生成标准 GPU 租赁协议 Markdown 草案。内置服务范围、价格条款、SLA、
  数据安全、违约责任、知识产权、保密条款、争议解决等关键条款模板。
  触发词：合同生成, 销售合同, GPU租赁协议, 框架协议, POC协议,
  补充协议, contract generator, SLA条款, 合同草案
---

# pans-contract-generator

AI算力销售合同生成器。根据商定条款生成标准GPU租赁协议。
内置关键条款模板（服务范围、价格条款、SLA、数据安全、违约责任、知识产权、保密条款、争议解决），
支持CLI参数快速生成和预览，输出Markdown格式合同草案。

## 触发词

合同生成, 销售合同, GPU租赁协议, 框架协议, POC协议, 补充协议, contract generator, SLA条款

## 使用方式

```bash
python3 scripts/contract.py \
  --client "客户公司名称" \
  --gpu H100 \
  --count 8 \
  --price 2.0 \
  --duration 12 \
  --output contract.md
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| --client | 是 | 客户公司名称 |
| --gpu | 是 | GPU型号（H100/A100/L40S/A10G等） |
| --count | 是 | GPU数量 |
| --price | 是 | 单卡月租价格（万元） |
| --duration | 是 | 租赁期限（月） |
| --output | 否 | 输出文件路径，默认输出到stdout |

## 输出内容

生成的合同包含以下章节：
1. 合同基本信息
2. 服务范围
3. 价格与付款条款
4. 服务等级协议（SLA）
5. 数据安全与隐私保护
6. 知识产权
7. 保密条款
8. 违约责任
9. 合同期限与终止
10. 争议解决
11. 其他条款
