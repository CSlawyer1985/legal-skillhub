"""知识产权官文自动归档系统 - 脚本包

本包包含系统的所有核心脚本模块：
  - config: 全局配置常量与路径管理
  - csv_manager: CSV 文件增删改查操作
  - pdf_parser: PDF 文本提取与字段解析
  - legal_status: 法律状态判定与更新
  - script1_process: 扫描处理（PDF解析→归档→写入CSV）
  - script2_sync: 文件路径同步（按标识号重组目录结构）
  - script3_report: 报表生成（汇总最新状态）
  - main: 系统入口（调度三个核心脚本）
  - run_archive: CLI 入口（支持命令行参数）
"""
