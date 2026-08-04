---
name: giurisprudenza-lampo
description: >
  快速判例研究，以就某一法律主题获得初步的定向框架。触发词为
  "giurisprudenza-lampo [tema]"、"cerca giurisprudenza su [tema]"、
  "sentenze su [tema]"、"pronunce su [tema]"、"orientamento giurisprudenziale su [tema]"，
  或任何要求就某一法律议题搜索判决、裁定、判例要旨、判例导向或先例的变体表达。
  当用户说 "cosa dice la giurisprudenza su"、"ci sono sentenze su"、"precedenti su"、
  "come si è espressa la Cassazione/il TAR/il Consiglio di Stato su" 时，也使用本技能。
metadata:
  author: "Giovanna Panucci"
  license: "agpl-3.0"
  version: "2026-05-12"
---

你正在执行快速判例研究。
目标是获得初步的定向框架，
而非穷尽性意见。

## 调用

"giurisprudenza-lampo [法律主题]"。

## 步骤 1：搜索

在网络中搜索关于该主题的近期和相关裁定。
优先来源：DeJure、Italgiure、TAR 和国务委员会的机构网站、
最高法院（Corte di Cassazione）、在线法律期刊（Altalex、Diritto.it、
Giurisprudenza Penale、Foro Italiano）。
如可获得，至少搜索 3-5 份裁定。

## 步骤 2：框架

### 主题
[1-2 句。所审查的法律问题。]

### 找到的裁定
对每份相关裁定：
- 案号： [机构、分庭、日期、编号]
- 要旨摘要： [关于所确立原则的 1-2 句]
- 相关性： [为何对本案件重要]

### 占主导地位的导向
[1 段。多数判例如何导向。如存在分歧，予以标记。]

### 操作性含义
[为意见或策略提供 2-3 个具体要点。]

### 来源
[所用来源的链接。]

## 步骤 3：注意事项

始终以以下内容结束：
"初步定向研究。
请核实案号，并借助专业数据库完成研究。"

## 步骤 4：保存

research/giurisprudenza-[主题-slug]-[YYYY-MM-DD].md
