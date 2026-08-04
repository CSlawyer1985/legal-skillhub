#!/usr/bin/env python3
"""
合同清洗系统 - 输出清洗后的Markdown文件

极简架构：
  1. 文档转换为Markdown（docx/pdf → MD）
  2. 格式清洗（format_cleaner）
  3. 工业级清洗（规则引擎 → AI分段 → 质量验证 → 收敛 → 最终润色）
  4. 输出清洗后的MD文件

首次使用:
  python auto_cleaner.py --config
  
日常使用:
  python auto_cleaner.py -i 合同.docx
  python auto_cleaner.py -i 合同.pdf -o ./output/
"""

import argparse
import logging
import os
import stat
import sys
import tempfile
import shutil
import json
import time
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass, asdict

# ============================================
# 常量定义
# ============================================
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
SUPPORTED_EXTENSIONS = {'.docx', '.doc', '.pdf', '.md', '.txt'}

# ============================================
# 配置类
# ============================================
@dataclass
class APIConfig:
    """API配置数据类"""
    provider: str = "anthropic"
    model: str = "claude-3-5-sonnet-20241022"
    api_key: str = ""
    base_url: str = "https://api.anthropic.com"
    api_version: str = "2023-06-01"
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'APIConfig':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

# ============================================
# 日志配置
# ============================================
def setup_logging(log_dir: Optional[Path] = None) -> logging.Logger:
    """配置日志记录"""
    logger = logging.getLogger('contract_cleaner')
    logger.setLevel(logging.DEBUG)
    
    # 清除现有处理器
    logger.handlers.clear()
    
    # 控制台处理器（INFO级别）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # 文件处理器（DEBUG级别）
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"contract_cleaner_{time.strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
        logger.info(f"日志文件: {log_file}")
    
    return logger

logger = logging.getLogger('contract_cleaner')

# ============================================
# 全局配置（在main中初始化）
# ============================================
API_CONFIG = None

# ============================================
# 配置文件管理
# ============================================
CONFIG_DIR = Path.home() / ".config" / "contract-cleaner-pro"
CONFIG_FILE = CONFIG_DIR / "api_config.json"
LOG_DIR = CONFIG_DIR / "logs"

def init_config():
    """初始化配置目录并设置权限"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        os.chmod(CONFIG_DIR, stat.S_IRWXU)
    except Exception as e:
        logger.warning(f"无法设置配置目录权限: {e}")

def check_config_file_permissions() -> bool:
    """检查配置文件权限是否安全"""
    if not CONFIG_FILE.exists():
        return True
    
    try:
        stat_info = os.stat(CONFIG_FILE)
        mode = stat_info.st_mode
        
        if mode & stat.S_IRWXO or mode & stat.S_IRWXG:
            logger.warning("配置文件权限过于开放，建议设置为仅所有者可读写")
            return False
        return True
    except Exception as e:
        logger.warning(f"检查配置文件权限失败: {e}")
        return True

def secure_save_config(config: APIConfig):
    """安全保存配置（设置权限）"""
    init_config()
    
    temp_file = CONFIG_FILE.with_suffix('.tmp')
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
        
        os.chmod(temp_file, stat.S_IRUSR | stat.S_IWUSR)
        temp_file.replace(CONFIG_FILE)
        logger.info(f"✓ 配置已安全保存到: {CONFIG_FILE}")
    except Exception as e:
        if temp_file.exists():
            temp_file.unlink()
        raise RuntimeError(f"保存配置失败: {e}")

def load_api_config() -> APIConfig:
    """加载API配置，优先从文件，其次环境变量"""
    config = APIConfig()
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                config = APIConfig.from_dict(file_data)
                logger.info(f"已加载配置文件: {CONFIG_FILE}")
                check_config_file_permissions()
        except Exception as e:
            logger.warning(f"配置文件读取失败: {e}")
    
    if os.getenv("ANTHROPIC_API_KEY"):
        config.provider = "anthropic"
        config.api_key = os.getenv("ANTHROPIC_API_KEY")
        config.base_url = "https://api.anthropic.com"
        config.api_version = "2023-06-01"
        config.model = "claude-3-5-sonnet-20241022"
        logger.info("使用环境变量 ANTHROPIC_API_KEY")
    elif os.getenv("DEEPSEEK_API_KEY"):
        config.provider = "deepseek"
        config.api_key = os.getenv("DEEPSEEK_API_KEY")
        config.base_url = "https://api.deepseek.com"
        config.api_version = None
        config.model = "deepseek-chat"
        logger.info("使用环境变量 DEEPSEEK_API_KEY")
    
    return config

def prompt_for_config() -> APIConfig:
    """交互式配置API设置"""
    print("\n" + "=" * 60)
    print("首次使用配置向导")
    print("=" * 60)
    print("\n请选择API提供商:")
    print("  1. Anthropic (Claude) - 推荐")
    print("  2. DeepSeek")
    print("  3. 其他OpenAI兼容API")
    
    choice = input("\n请选择 (1-3, 默认1): ").strip() or "1"
    
    config = APIConfig()
    
    if choice == "1":
        config.provider = "anthropic"
        config.base_url = "https://api.anthropic.com"
        config.api_version = "2023-06-01"
        config.model = "claude-3-5-sonnet-20241022"
        config.api_key = input("请输入 Anthropic API Key (sk-ant-...): ").strip()
        
    elif choice == "2":
        config.provider = "deepseek"
        config.base_url = "https://api.deepseek.com"
        config.api_version = None
        config.model = "deepseek-chat"
        config.api_key = input("请输入 DeepSeek API Key: ").strip()
        
    elif choice == "3":
        config.provider = input("请输入提供商名称 (如: openai, azure): ").strip()
        config.base_url = input("请输入 API Base URL: ").strip()
        config.api_key = input("请输入 API Key: ").strip()
        config.model = input("请输入模型名称 (默认: gpt-4): ").strip() or "gpt-4"
        api_version = input("请输入 API Version (没有则留空): ").strip()
        config.api_version = api_version if api_version else None
    
    else:
        print("无效选择，使用默认Claude配置")
        config.provider = "anthropic"
        config.base_url = "https://api.anthropic.com"
        config.api_version = "2023-06-01"
        config.model = "claude-3-5-sonnet-20241022"
        config.api_key = input("请输入 Anthropic API Key: ").strip()
    
    if not config.api_key:
        print("错误: API Key不能为空")
        sys.exit(1)
    
    print("\n正在测试API连接...")
    if test_api_connection(config):
        secure_save_config(config)
        print("\n✓ 配置完成！")
        return config
    else:
        print("\n✗ API连接测试失败，请检查配置")
        retry = input("是否重新配置? (y/n): ").strip().lower()
        if retry == 'y':
            return prompt_for_config()
        else:
            sys.exit(1)

def test_api_connection(config: APIConfig) -> bool:
    """测试API连接"""
    try:
        import requests
        
        if config.provider == "anthropic":
            headers = {
                "x-api-key": config.api_key,
                "Content-Type": "application/json",
                "anthropic-version": config.api_version
            }
            payload = {
                "model": config.model,
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hi"}]
            }
            response = requests.post(
                f"{config.base_url}/v1/messages",
                headers=headers,
                json=payload,
                timeout=30
            )
        else:
            headers = {
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": config.model,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 10
            }
            response = requests.post(
                f"{config.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
        
        if response.status_code == 200:
            print("  ✓ API连接成功")
            return True
        else:
            print(f"  ✗ API错误: {response.status_code} - {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"  ✗ 连接失败: {e}")
        return False

# ============================================
# 输入验证
# ============================================
def validate_input_file(file_path: Path) -> Tuple[bool, str]:
    """验证输入文件"""
    logger.debug(f"验证输入文件: {file_path}")
    
    if not file_path.exists():
        return False, f"文件不存在: {file_path}"
    
    if not file_path.is_file():
        return False, f"不是普通文件: {file_path}"
    
    suffix = file_path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        return False, (
            f"不支持的文件格式: {suffix}\n"
            f"支持的格式: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    
    try:
        file_size = file_path.stat().st_size
        if file_size == 0:
            return False, "文件为空"
        if file_size > MAX_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            max_mb = MAX_FILE_SIZE / (1024 * 1024)
            return False, f"文件过大: {size_mb:.1f}MB (最大支持 {max_mb:.0f}MB)"
        logger.debug(f"文件大小: {file_size} bytes")
    except Exception as e:
        return False, f"无法读取文件信息: {e}"
    
    if not os.access(file_path, os.R_OK):
        return False, "文件不可读（权限问题）"
    
    try:
        with open(file_path, 'rb') as f:
            header = f.read(8)
            is_valid, msg = check_file_magic(header, suffix)
            if not is_valid:
                return False, f"文件类型验证失败: {msg}"
    except Exception as e:
        return False, f"无法读取文件头: {e}"
    
    return True, ""

def check_file_magic(header: bytes, suffix: str) -> Tuple[bool, str]:
    """检查文件魔数"""
    if suffix == '.pdf':
        if not header.startswith(b'%PDF'):
            return False, "不是有效的PDF文件（魔数不匹配）"
    
    if suffix in {'.docx', '.doc'}:
        if header[:2] != b'PK':
            if header[:8] != b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1':
                return False, "不是有效的Word文档"
    
    if suffix in {'.md', '.txt'}:
        if b'\x00' in header[:8]:
            return False, "看起来是二进制文件，不是文本文件"
    
    return True, ""

# ============================================
# 分步执行函数（Agent 代劳模式，不需要 API Key）
# ============================================

def _clean_original_lightweight(text: str) -> str:
    """
    原合同轻量清理：仅做段首符号清理 + {.underline} 清理 + 轻量规则引擎

    目的：生成 pandiff 对比的"原合同"基线，保留原始内容，
          只清理从 docx 转换带来的格式噪音。
    """
    import re

    lines = text.split('\n')
    result_lines = []

    # 段首垃圾符号集合（从 docx 转来的项目符号、乱码等）
    # 注意：只在行首清理，避免误删正文中的合法符号
    leading_junk_pattern = re.compile(
        r'^[·•●○■▪◆◇►▸▹‣⁃⁌⁍◦\、\\]+\s*'
    )

    for line in lines:
        # 清理行首垃圾符号
        cleaned = leading_junk_pattern.sub('', line)
        result_lines.append(cleaned)

    text = '\n'.join(result_lines)

    # 清理 pandoc 下划线标记 {.underline}
    text = text.replace('{.underline}', '')

    # 调用轻量规则引擎（编号规范化 + 空行清理等）
    from rule_engine import RuleEngine
    engine = RuleEngine()
    text, _ = engine.apply_minimal_rules(text)

    return text


def run_preprocess(input_path: Path, output_dir: Path, args) -> Optional[Path]:
    """
    预处理阶段：文档转换 + 格式清洗 + 规则引擎 + 分块
    输出 chunk 文件到会话目录，返回会话目录路径。

    不需要 API Key。
    """
    global logger
    logger = setup_logging(LOG_DIR if args.verbose else None)
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    scripts_dir = Path(__file__).parent
    stem = input_path.stem
    suffix = input_path.suffix.lower()

    # 创建会话目录
    session_name = f"清洗会话_{stem}_{int(time.time())}"
    session_dir = output_dir / session_name
    session_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"会话目录: {session_dir}")

    # 临时文件
    temp_dir = Path(tempfile.mkdtemp(prefix="contract_cleaner_"))
    temp_raw = temp_dir / f"{stem}_raw.md"
    temp_cleaned = temp_dir / f"{stem}_cleaned.md"
    temp_format = temp_dir / f"{stem}_format_cleaned.md"

    try:
        logger.info("=" * 60)
        logger.info("预处理阶段（不需要 API Key）")
        logger.info("=" * 60)
        logger.info(f"输入文件: {input_path}")

        # --- 步骤1: 文档转换为 Markdown ---
        if suffix == '.md':
            logger.info("【步骤1】复制 Markdown 文件")
            shutil.copy(input_path, temp_raw)
        else:
            logger.info("【步骤1】文档转换为 Markdown")
            from document_converter import convert_word_to_md
            if not convert_word_to_md(str(input_path), str(temp_raw)):
                logger.error("文档转换失败，无法继续")
                return None
            logger.info(f"  转换完成")

        with open(temp_raw, 'r', encoding='utf-8') as f:
            raw_md = f.read()
        logger.info(f"  原始文本: {len(raw_md)} 字符")

        # --- 步骤1.5: 生成原合同轻量清理版（用于 pandiff 对比基线） ---
        logger.info("【步骤1.5】生成原合同轻量清理版")
        original_lightweight = _clean_original_lightweight(raw_md)
        original_lightweight_path = session_dir / "_原始轻量.md"
        with open(original_lightweight_path, 'w', encoding='utf-8') as f:
            f.write(original_lightweight)
        logger.info(f"  原合同轻量版: {original_lightweight_path} ({len(original_lightweight)} 字符)")

        # --- 步骤2: 格式清洗 ---
        logger.info("【步骤2】格式清洗")
        from format_cleaner import clean_format
        cleaned_md = clean_format(raw_md)
        with open(temp_cleaned, 'w', encoding='utf-8') as f:
            f.write(cleaned_md)
        logger.info(f"  清洗后: {len(cleaned_md)} 字符")

        # 保存格式清洗后的快照
        with open(temp_format, 'w', encoding='utf-8') as f:
            f.write(cleaned_md)

        # --- 步骤3: 规则引擎（18 条确定性规则，0 API） ---
        logger.info("【步骤3】规则引擎（确定性规则，0 API 调用）")
        from rule_engine import RuleEngine
        rule_engine = RuleEngine()
        ruled_md, rule_changes = rule_engine.apply_all_rules(cleaned_md)
        if rule_changes:
            logger.info(f"  规则引擎执行了 {len(rule_changes)} 项修改:")
            for change in rule_changes[:5]:
                logger.info(f"    - {change}")
            if len(rule_changes) > 5:
                logger.info(f"    ... 共 {len(rule_changes)} 项")
        else:
            logger.info("  规则引擎: 无需修改")

        ruled_md_path = session_dir / "00_规则引擎输出.md"
        with open(ruled_md_path, 'w', encoding='utf-8') as f:
            f.write(ruled_md)
        logger.info(f"  规则引擎输出: {ruled_md_path}")

        # --- 步骤3.5: AI 编号规范化（由 Agent 执行，0 API） ---
        # 规则引擎只能处理已有的"第X条"格式编号，但合同原文可能用
        # "一、""1.""（一）"等各种非标编号。此步骤由 AI 统一调整为
        # "第一条、1.1、（1）"标准层级体系，且只改编号不改内容。
        logger.info("【步骤3.5】AI 编号规范化（由 Agent 执行，0 API 调用）")
        numbering_md_path = session_dir / "01_编号规范化输入.md"
        with open(numbering_md_path, 'w', encoding='utf-8') as f:
            f.write(ruled_md)
        logger.info(f"  编号规范化输入: {numbering_md_path}")

        # 检查 02_编号规范化输出.md 是否已存在
        numbered_md_path = session_dir / "02_编号规范化输出.md"
        if numbered_md_path.exists():
            with open(numbered_md_path, 'r', encoding='utf-8') as f:
                ruled_md = f.read()
            logger.info(f"  ✓ 已加载编号规范化输出: {numbered_md_path}")
        else:
            logger.info(f"  ⏳ 编号规范化输出尚未生成")
            logger.info(f"  → 请 Agent 读取 references/prompts/numbering.md，")
            logger.info(f"    对 01_编号规范化输入.md 执行编号规范化，")
            logger.info(f"    结果写入 02_编号规范化输出.md")
            logger.info(f"  ⚠️ 此步骤只改编号，不改任何文字内容")
            logger.info(f"  ⚠️ 编号规范化未完成，使用规则引擎输出继续分块")
            logger.info(f"     编号规范化完成后，将 02 文件放入此会话目录，")
            session_dir_abs = str(session_dir.resolve())
            logger.info(f"     再运行: python auto_cleaner.py --stage preprocess-continue --session \"{session_dir_abs}\"")

        # --- 步骤4: 合同分块 ---
        logger.info("【步骤4】合同分块")
        from industrial_cleaner import ContractChunker
        chunks = ContractChunker.chunk(ruled_md)
        ai_chunks = [c for c in chunks if c.needs_ai]
        logger.info(f"  共 {len(chunks)} 块（其中 {len(ai_chunks)} 块需要 AI 处理）")

        # --- 导出 chunks ---
        chunks_dir = session_dir / "chunks"
        chunks_dir.mkdir(parents=True, exist_ok=True)

        # 保存原始全文
        with open(chunks_dir / "_原始全文.md", 'w', encoding='utf-8') as f:
            f.write(ruled_md)

        for chunk in chunks:
            chunk_path = chunks_dir / f"chunk_{chunk.chunk_id:02d}.md"
            with open(chunk_path, 'w', encoding='utf-8') as f:
                f.write(chunk.content)
            logger.info(
                f"  块 {chunk.chunk_id:02d} [{chunk.chunk_type}] "
                f"{chunk.article_range} ({len(chunk.content)} 字符, "
                f"AI={'是' if chunk.needs_ai else '否'}) → {chunk_path.name}"
            )

        # 写入 manifest.json
        manifest = {
            "session_name": session_name,
            "input_file": str(input_path),
            "output_dir": str(session_dir),
            "total_chunks": len(chunks),
            "ai_chunks": len(ai_chunks),
            "chunks": [
                {
                    "chunk_id": chunk.chunk_id,
                    "file": f"chunk_{chunk.chunk_id:02d}.md",
                    "type": chunk.chunk_type,
                    "range": chunk.article_range,
                    "needs_ai": chunk.needs_ai,
                    "chars": len(chunk.content)
                }
                for chunk in chunks
            ]
        }
        manifest_path = session_dir / "manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        logger.info(f"  manifest: {manifest_path}")
        logger.info("\n" + "=" * 60)
        logger.info("预处理完成！")
        logger.info("=" * 60)
        logger.info(f"\n会话目录: {session_dir}")
        logger.info(f"\n后续步骤:")
        logger.info(f"  1. 编号规范化: 读取 references/prompts/numbering.md，")
        logger.info(f"     对 {session_dir}/01_编号规范化输入.md 执行编号规范化，")
        logger.info(f"     结果写入 {session_dir}/02_编号规范化输出.md")
        logger.info(f"  2. AI 清洗: 由 Agent 执行（义务句式 → 结构重组 → 格式清理）")
        logger.info(f"  3. 收尾: python auto_cleaner.py --stage finalize --session \"{session_dir_abs}\"")

    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

    return session_dir


def run_preprocess_continue(session_dir: Path, args) -> Optional[Path]:
    """
    预处理继续阶段：在已有会话目录上，加载编号规范化输出 + 分块
    用于 Agent 完成编号规范化后继续流程。

    不需要 API Key。
    """
    global logger
    logger = setup_logging(LOG_DIR if args.verbose else None)
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # 检查编号规范化输出文件
    numbered_md_path = session_dir / "02_编号规范化输出.md"
    if not numbered_md_path.exists():
        logger.error(f"编号规范化输出不存在: {numbered_md_path}")
        logger.error("请先完成编号规范化步骤，将结果写入 02_编号规范化输出.md")
        return None

    with open(numbered_md_path, 'r', encoding='utf-8') as f:
        ruled_md = f.read()

    logger.info("=" * 60)
    logger.info("预处理继续阶段（不需要 API Key）")
    logger.info("=" * 60)
    logger.info(f"会话目录: {session_dir}")
    logger.info(f"编号规范化输出: {numbered_md_path} ({len(ruled_md)} 字符)")

    # --- 合同分块 ---
    logger.info("【步骤4】合同分块")
    from industrial_cleaner import ContractChunker
    chunks = ContractChunker.chunk(ruled_md)
    ai_chunks = [c for c in chunks if c.needs_ai]
    logger.info(f"  共 {len(chunks)} 块（其中 {len(ai_chunks)} 块需要 AI 处理）")

    # --- 导出 chunks ---
    chunks_dir = session_dir / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)

    # 保存原始全文（用编号规范化后的版本覆盖）
    with open(chunks_dir / "_原始全文.md", 'w', encoding='utf-8') as f:
        f.write(ruled_md)

    for chunk in chunks:
        chunk_path = chunks_dir / f"chunk_{chunk.chunk_id:02d}.md"
        with open(chunk_path, 'w', encoding='utf-8') as f:
            f.write(chunk.content)
        logger.info(
            f"  块 {chunk.chunk_id:02d} [{chunk.chunk_type}] "
            f"{chunk.article_range} ({len(chunk.content)} 字符, "
            f"AI={'是' if chunk.needs_ai else '否'}) → {chunk_path.name}"
        )

    # 更新 manifest.json（保留原有的 input_file）
    session_name = session_dir.name
    manifest_path = session_dir / "manifest.json"

    # 读取原有 manifest，保留 input_file
    original_input_file = ""
    if manifest_path.exists():
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                old_manifest = json.load(f)
            original_input_file = old_manifest.get('input_file', '')
        except Exception:
            pass

    manifest = {
        "session_name": session_name,
        "input_file": original_input_file,
        "output_dir": str(session_dir),
        "total_chunks": len(chunks),
        "ai_chunks": len(ai_chunks),
        "numbering_normalized": True,
        "chunks": [
            {
                "chunk_id": chunk.chunk_id,
                "file": f"chunk_{chunk.chunk_id:02d}.md",
                "type": chunk.chunk_type,
                "range": chunk.article_range,
                "needs_ai": chunk.needs_ai,
                "chars": len(chunk.content)
            }
            for chunk in chunks
        ]
    }
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    logger.info(f"  manifest: {manifest_path}")
    logger.info("\n" + "=" * 60)
    logger.info("预处理继续完成！")
    logger.info("=" * 60)
    logger.info(f"\n后续步骤:")
    logger.info(f"  1. AI 清洗: 由 Agent 执行（义务句式 → 结构重组 → 格式清理）")
    logger.info(f"  2. 收尾: python auto_cleaner.py --stage finalize --session {session_name}")

    return session_dir


def run_finalize(session_dir: Path, output_dir: Path, args) -> bool:
    """
    收尾阶段：拼接 chunks + 自检 + 规则引擎防退化 + 导出 docx
    不需要 API Key（使用纯规则引擎，无 AI 验证和 AI 润色）。
    """
    global logger
    logger = setup_logging(LOG_DIR if args.verbose else None)
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    manifest_path = session_dir / "manifest.json"
    if not manifest_path.exists():
        logger.error(f"manifest.json 不存在: {manifest_path}")
        logger.error("请先运行 preprocess 阶段")
        return False

    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    chunks_dir = session_dir / "chunks"
    if not chunks_dir.exists():
        logger.error(f"chunks 目录不存在: {chunks_dir}")
        return False

    # 确定原始文件信息，输出到原始文件夹
    input_file_str = manifest.get('input_file', '')
    if input_file_str:
        input_path = Path(input_file_str)
        original_dir = input_path.parent
        original_stem = input_path.stem
    else:
        original_dir = output_dir
        original_stem = manifest.get('session_name', '合同').replace(f"清洗会话_", "")

    # 覆盖为原始目录
    output_dir = original_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = original_stem

    logger.info("=" * 60)
    logger.info("收尾阶段（纯规则引擎，0 API 调用）")
    logger.info("=" * 60)
    logger.info(f"会话: {manifest['session_name']}")
    logger.info(f"输出目录: {output_dir}")

    # --- 拼接 chunks（按顺序） ---
    logger.info("\n【步骤1】拼接 chunks")
    chunks_list = sorted(manifest['chunks'], key=lambda x: x['chunk_id'])
    assembled_parts = []

    for chunk_info in chunks_list:
        chunk_path = chunks_dir / chunk_info['file']
        if not chunk_path.exists():
            logger.warning(f"  chunk 文件不存在，跳过: {chunk_path}")
            continue
        with open(chunk_path, 'r', encoding='utf-8') as f:
            assembled_parts.append(f.read())

    assembled = "\n\n".join(assembled_parts)
    # 清理多余空行
    import re
    assembled = re.sub(r'\n{3,}', '\n\n', assembled)
    logger.info(f"  拼接完成: {len(assembled)} 字符")

    # --- 自检验证（纯代码，0 API） ---
    logger.info("\n【步骤2】自检验证（纯规则）")
    try:
        from self_verifier import ContractSelfVerifier
        verifier = ContractSelfVerifier()
        original_md = chunks_dir / "_原始全文.md"
        original_content = ""
        if original_md.exists():
            with open(original_md, 'r', encoding='utf-8') as f:
                original_content = f.read()

        report = verifier.verify(original_content, assembled)
        logger.info(f"  总检查项: {report.total_checks}")
        logger.info(f"  通过: {report.passed}, 失败: {report.failed}")

        errors = [i for i in report.issues if i.severity == "ERROR"]
        warnings = [i for i in report.issues if i.severity == "WARNING"]
        if errors:
            logger.warning(f"  ⚠️ 发现 {len(errors)} 个错误（代码自检）:")
            for issue in errors[:5]:
                logger.warning(f"    - [{issue.rule}] {issue.message}")
        else:
            logger.info("  ✓ 代码自检无 ERROR")
    except Exception as e:
        logger.warning(f"  自检出错（非致命）: {e}")

    # --- 规则引擎防退化 ---
    logger.info("\n【步骤3】规则引擎防退化")
    from rule_engine import RuleEngine
    fix_engine = RuleEngine()
    fixed, fix_changes = fix_engine.apply_all_rules(assembled)
    if fix_changes:
        logger.info(f"  修复了 {len(fix_changes)} 处退化问题")
        for fc in fix_changes[:5]:
            logger.info(f"    - {fc}")
    assembled = fixed

    # 嵌套应当兜底修复
    fixed2, nested_changes = fix_engine.apply_nested_yingdang_fix(assembled)
    if nested_changes:
        logger.info(f"  嵌套应当兜底修复: {len(nested_changes)} 处")
        assembled = fixed2

    # 清理 pandoc 下划线标记 {.underline}
    if '{.underline}' in assembled:
        assembled = assembled.replace('{.underline}', '')
        logger.info(f"  已清理 {{.underline}} 标记")

    # 导出 docx（不输出 _清洗版.md，最终只保留4个交付物）
    temp_original = Path(tempfile.mkdtemp(prefix="contract_finalize_")) / "original.md"
    temp_final = Path(tempfile.mkdtemp(prefix="contract_finalize_")) / "final.md"

    # 优先使用轻量清理版作为 pandiff 原始文本，回退到 _原始全文.md
    original_lightweight_path = session_dir / "_原始轻量.md"
    original_full_path = chunks_dir / "_原始全文.md"
    if original_lightweight_path.exists():
        original_path = original_lightweight_path
        logger.info(f"  使用原合同轻量版作为对比基线")
    elif original_full_path.exists():
        original_path = original_full_path
    else:
        original_path = None

    with open(temp_original, 'w', encoding='utf-8') as f:
        if original_path and original_path.exists():
            f.write(original_path.read_text(encoding='utf-8'))
        else:
            f.write("")
    with open(temp_final, 'w', encoding='utf-8') as f:
        f.write(assembled)

    try:
        from docx_exporter import export_docx_outputs
        docx_results = export_docx_outputs(
            original_md=temp_original,
            cleaned_md=temp_final,
            output_dir=output_dir,
            stem=stem,
        )
        for key, path in docx_results.items():
            if path:
                logger.info(f"  输出 {key}: {path}")
    except Exception as e:
        logger.warning(f"  docx 导出出错（非致命）: {e}")

    # 清理临时目录
    for td in [temp_original.parent]:
        if td.exists() and td.name.startswith("contract_finalize_"):
            shutil.rmtree(td, ignore_errors=True)

    # 清理过程性文件：删除 session 目录
    logger.info("\n【步骤4】清理过程性文件")
    if session_dir.exists():
        try:
            shutil.rmtree(session_dir, ignore_errors=True)
            logger.info(f"  已删除会话目录: {session_dir}")
        except Exception as e:
            logger.warning(f"  删除会话目录失败: {e}")

    # 删除可能残留的 _清洗版.md（旧版本产物）
    legacy_md = output_dir / f"{stem}_清洗版.md"
    if legacy_md.exists():
        try:
            legacy_md.unlink()
            logger.info(f"  已删除遗留文件: {legacy_md.name}")
        except Exception:
            pass

    logger.info("\n" + "=" * 60)
    logger.info("收尾完成！")
    logger.info("=" * 60)
    logger.info(f"\n输出目录: {output_dir}")
    logger.info(f"\n最终交付物（4个）:")
    logger.info(f"  📄 {stem}-原合同（预处理后）.md")
    logger.info(f"  📄 {stem}-新合同（预处理后）.md")
    logger.info(f"  📄 {stem}-清洁版.docx")
    logger.info(f"  �