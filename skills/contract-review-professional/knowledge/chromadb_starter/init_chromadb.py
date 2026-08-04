# -*- coding: utf-8 -*-
"""
ChromaDB 初始化脚本 — 创建合同审查知识库空壳
在首次使用技能前运行一次即可
"""

import os
import sys
from pathlib import Path

def init_chromadb(knowledge_dir: str = None):
    """初始化 ChromaDB 数据库"""
    if knowledge_dir is None:
        knowledge_dir = Path(__file__).parent.parent / "chromadb"
    else:
        knowledge_dir = Path(knowledge_dir)
    
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        import chromadb
        client = chromadb.PersistentClient(str(knowledge_dir))
        
        # 创建 5 个 Collection
        collections = [
            ("pkulaw_laws", "北大法宝法条库（PKULaw MCP 实时摄入）"),
            ("pkulaw_cases", "北大法宝案例库（PKULaw MCP 实时摄入）"),
            ("lawyer_laws", "本地法条库"),
            ("lawyer_cases", "本地案例库"),
            ("lawyer_knowledge", "合规治理知识库"),
        ]
        
        for name, desc in collections:
            try:
                client.get_or_create_collection(name=name, metadata={"description": desc, "hnsw:space": "cosine"})
                print(f"  ✅ {name} — {desc}")
            except Exception as e:
                print(f"  ❌ {name}: {e}")
        
        print(f"\nChromaDB 已初始化，数据目录：{knowledge_dir}")
        return True
    
    except ImportError:
        print("❌ chromadb 未安装，请先运行：pip install chromadb")
        return False

if __name__ == "__main__":
    init_chromadb()
