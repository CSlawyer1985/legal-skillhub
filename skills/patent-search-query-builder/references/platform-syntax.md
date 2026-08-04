# 平台语法规则速查表

以下规则是不可违反的句法公理。违反则检索式不可执行。

---

## 5.4.1 Patsnap / 智慧芽

| 类别 | 语法 |
|:---|:---|
| 布尔 | AND OR NOT |
| 截词 | *（右截断）?（单字符） |
| 短语 | "..." |
| 距离 | $Wn（无序n词内）$Pn（有序n词内） |
| 全文字段 | TAC_ALL:() |
| 标题 | TI:() |
| 摘要 | AB:() |
| 权利要求 | CL:() |
| 分类号 | IPC_CPC:() |
| 申请人（原始） | PA:() |
| 当前权利人 | CURRENT_PA:() |
| 地域 | AUTHORITY:(CN OR US OR ...) |
| 日期 | APD:[20200101 TO 20231231] |
| 法律状态 | SIMPLE_LEGAL_STATUS:(1 OR 2) |
| 专利类型 | PATENT_TYPE:(A OR B OR U) |

---

## 5.4.2 中国专利公布公告

| 类别 | 语法 |
|:---|:---|
| 布尔 | AND OR NOT |
| 截词 | %（多字符） |
| 字段 | 界面下拉选择 |
| 限制 | 无位置算符；无嵌套括号深度限制说明 |
| 申请人 | 界面字段"申请人"直接输入 |

---

## 5.4.3 EPO / Espacenet

| 类别 | 语法 |
|:---|:---|
| 布尔 | AND OR NOT |
| 截词 | *（右截断）?（单字符） |
| 短语 | "..." |
| 距离 | Wn（如 W5） |
| 字段 | ta=(标题摘要) ti= ab= cl= desc= |
| 分类号 | ipc= cpc= |
| 申请人 | ap=（每个名称须独立带前缀） |
| 日期 | pd= / ap= |

⚠ **关键约束**：`(ap="A" OR ap="B")` 不可写为 `ap=("A" OR "B")`

---

## 5.4.4 USPTO Patent Public Search

| 类别 | 语法 |
|:---|:---|
| 布尔 | AND OR NOT |
| 截词 | * $（单字符） |
| 短语 | "..." |
| 距离 | ADJn NEARn WITHn SAMEn |
| 字段 | 后缀式：term.FIELD. 如 "fan".TI. |
| 全文 | .SPEC. |
| 权利要求 | .CLM. |
| 分类号 | .CPC. .IPC. |
| 权利人 | AN/("name") |

⚠ 仅英文有效

---

## 5.4.5 HimmPat

| 类别 | 语法 |
|:---|:---|
| 布尔 | AND OR NOT |
| 截词 | +（多字符）?（单字符） |
| 短语 | "..." |
| 距离 | (W)n |
| 字段 | TI= AB= CL= DESC= IPC= CPC= PA= |

---

## 5.4.6 Baiten / Lens

| 类别 | 语法 |
|:---|:---|
| 布尔 | AND OR NOT |
| 截词 | * |
| 短语 | "..." |
| 字段(Baiten) | ti: ab: cl: pa: ipc: |
| 字段(Lens) | title: abstract: claims: applicant: owner: classification_ipc: |

⚠ 部分平台不支持字段内嵌套括号，需展开笛卡尔积

---

## 平台间差异速查

| 特性 | Patsnap | 中国专利公布公告 | EPO | USPTO | HimmPat | Baiten/Lens |
|:---|:---|:---|:---|:---|:---|:---|
| 截词符 | * ? | % | * ? | * $ | + ? | * |
| 距离算符 | $Wn $Pn | 无 | Wn | ADJn NEARn | (W)n | 无 |
| 字段语法 | FIELD:() | 界面选择 | field= | term.FIELD. | FIELD= | field: |
| 申请人前缀 | PA:() | 界面字段 | ap=（独立） | AN/() | PA= | pa:/applicant: |
| 当前权利人 | CURRENT_PA:() | 无 | 无 | 无 | 无 | owner: |
| 嵌套括号 | 支持 | 未说明 | 支持（但ap=受限） | 支持 | 支持 | 部分受限 |
