# 法律知识库 - 使用说明

## 快速开始

### 1. 首次使用 - 重建索引
```bash
cd 合同审查助手
python -c "
from scripts.law_search import LawSearch
# 首次会自动提示索引不存在
searcher = LawSearch()
"
```

### 2. 手动重建索引（如需要）
```bash
python knowledge-base/scripts/index_files.py knowledge_base_compressed knowledge_base_compressed/law_index.json
```

### 3. 完整上传到SkillHub时排除的文件
- `knowledge_base/*.docx` - 原始文档（太大）
- `*.db` - 数据库文件
- `审查报告.*` - 测试生成的报告

### 4. 上传到SkillHub后
用户下载Skill后可以直接使用本地知识库，无需额外配置。

### 在线查询功能
- 重要条款会自动查询全国人大法规库
- 需要网络连接
- 查询失败时会降级使用本地知识库

## 文件大小说明
- 压缩版知识库（仅txt）：764 KB
- 索引文件：992 KB
- 建议：不上传索引文件，运行时自动重建或用户自行生成
