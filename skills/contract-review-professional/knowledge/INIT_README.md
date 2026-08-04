# 合同审查知识库初始化说明

本技能附带知识库空壳，用于存储合同审查相关的向量检索数据。

## 知识库用途

| 数据库 | 用途 | 数据来源 |
|--------|------|---------|
| ChromaDB 法律法条库 | 法条语义检索 | 用户自行导入或 PKULaw MCP 实时摄入 |
| ChromaDB 案例库 | 类案语义检索 | 用户自行导入或 PKULaw MCP 实时摄入 |
| ChromaDB 合规知识库 | 合规治理知识 | 用户自行导入 |

## 初始化方法

### 方法 1：从零开始（推荐）

技能在首次使用时自动创建 ChromaDB 数据库文件，存储在技能目录下的 `knowledge/chromadb/`。

```bash
pip install chromadb
```

### 方法 2：导入现有数据

如果你已有 ChromaDB 数据，将整个 `chromadb/` 目录复制到：

```
{技能安装目录}/knowledge/chromadb/
```

### 方法 3：使用 PKULaw MCP 实时增强

连接 PKULaw MCP 后，每次审查自动将检索结果摄入 ChromaDB，无需手动维护。

## 目录结构

```
knowledge/
├── INIT_README.md          ← 本文件
├── chromadb_starter/       ← 初始化脚本
│   └── init_chromadb.py    ← 一键创建空数据库
└── chromadb/               ← 实际数据库（首次使用后生成）
```

> 知识库为可选增强功能。没有知识库不影响核心审查流程，仅缺少语义检索增强。
