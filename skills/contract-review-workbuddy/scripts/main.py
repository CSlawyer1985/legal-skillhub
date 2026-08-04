#!/usr/bin/env python3
"""
合同审查主入口 v4.0
完整工作流：文本提取 → 结构解析 → 风险审查 → 报告生成
新增：硬件自适应调度、历史版本对比、Word 报告生成、更新检测、危险文件拦截
"""

import json
import sys
import time
import subprocess
import hashlib
from pathlib import Path
from typing import Optional
import argparse
import logging

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_step(step_num: int, total: int, message: str):
    """打印进度步骤"""
    print(f"\n[{step_num}/{total}] {message}", flush=True)


def print_success(message: str):
    """打印成功信息"""
    print(f"  ✅ {message}", flush=True)


def print_warning(message: str):
    """打印警告信息"""
    print(f"  ⚠️  {message}", flush=True)


def print_error(message: str):
    """打印错误信息"""
    print(f"  ❌ {message}", flush=True)


def print_progress(step: str, detail: str = "", done: bool = False):
    """打印实时进度"""
    if done:
        print(f"  ✅ {step} {detail}", flush=True)
    else:
        print(f"  ⏳ {step} {detail}...", flush=True)


def get_skill_version(default: str = "4.0.0") -> str:
    """v4.0 从 SKILL.md frontmatter 读取版本号，避免版本硬编码脱节"""
    try:
        skill_md = Path(__file__).parent.parent / 'SKILL.md'
        if not skill_md.exists():
            return default
        with open(skill_md, 'r', encoding='utf-8') as f:
            for _ in range(30):  # 只读 frontmatter 区域
                line = f.readline()
                if not line:
                    break
                if line.startswith('version:'):
                    return line.split(':', 1)[1].strip().strip('"\'') or default
    except Exception:
        pass
    return default


def print_banner(version: str = None):
    """打印工具横幅"""
    version = version or get_skill_version()
    print("\n" + "=" * 50, flush=True)
    print(f"📋 合同智能审查 v{version}", flush=True)
    print("=" * 50, flush=True)


def check_ollama_installed() -> bool:
    """检查 Ollama 是否已安装"""
    try:
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False


def install_ollama():
    """一键安装 Ollama"""
    print("\n" + "=" * 50)
    print("🦙 Ollama 本地模型安装向导")
    print("=" * 50)
    print()
    print("Ollama 允许您在本地运行 AI 模型，无需 API 密钥。")
    print()
    
    if check_ollama_installed():
        print("✅ Ollama 已安装！")
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
            if 'qwen' in result.stdout.lower() or 'llama' in result.stdout.lower():
                print("✅ 已检测到本地模型。")
                return True
            else:
                print("⏳ 检测到 Ollama，但未安装中文模型。")
                print()
                install_model = input("是否下载中文模型 qwen2.5:7b（约 4.7GB）？[y/N]: ").strip().lower()
                if install_model in ('y', 'yes', '是'):
                    print("⏳ 正在下载模型（可能需要几分钟）...")
                    subprocess.run(['ollama', 'pull', 'qwen2.5:7b'], check=True)
                    print("✅ 模型下载完成！")
                    return True
                else:
                    print("您可以稍后手动运行: ollama pull qwen2.5:7b")
                    return True
        except Exception:
            pass
        return True
    
    print("Ollama 未安装。请选择安装方式：")
    print()
    print("1. macOS / Linux（一键安装）")
    print("   运行: curl -fsSL https://ollama.ai/install.sh | sh")
    print()
    print("2. Windows")
    print("   访问 https://ollama.ai/download 下载 OllamaSetup.exe")
    print()
    
    open_browser = input("是否打开 Ollama 下载页面？[y/N]: ").strip().lower()
    if open_browser in ('y', 'yes', '是'):
        import webbrowser
        webbrowser.open('https://ollama.ai/download')
    
    return False


def first_time_setup():
    """首次使用向导"""
    config_path = Path.home() / '.contract-review' / 'config.json'
    
    if config_path.exists():
        return True
    
    print("\n" + "=" * 50)
    print("🎉 欢迎使用合同智能审查！")
    print("=" * 50)
    print()
    print("本工具支持以下运行模式：")
    print()
    print("  🥇 最佳体验：安装 Ollama（免费本地模型）")
    print("     - 完全本地运行，保护隐私")
    print("     - 无需 API 密钥")
    print("     - 首次下载模型约 4-8GB")
    print()
    print("  🥈 高级体验：配置 OpenAI API")
    print("     - 设置环境变量 OPENAI_API_KEY")
    print("     - 需要付费，但效果最佳")
    print()
    print("  🥉 基础体验：仅规则引擎")
    print("     - 开箱即用，无需额外配置")
    print("     - 覆盖常见风险点")
    print()
    
    choice = input("请选择 [1/2/3，默认 3]: ").strip() or "3"
    
    if choice == "1":
        install_ollama()
    elif choice == "2":
        print()
        print("请设置环境变量：")
        print("  Windows: set OPENAI_API_KEY=sk-xxx")
        print("  macOS/Linux: export OPENAI_API_KEY=sk-xxx")
    else:
        print("已选择基础模式。您可以随时通过安装 Ollama 升级到完整体验。")
    
    # 保存配置
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config = {
        'setup_completed': True,
        'mode': 'ollama' if choice == '1' else 'openai' if choice == '2' else 'basic'
    }
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    return True


def show_history(contract_text: Optional[str] = None):
    """显示历史审查记录"""
    from history_manager import HistoryManager
    
    manager = HistoryManager()
    
    if contract_text:
        # 显示特定合同的历史
        history = manager.get_history(contract_text)
        if not history or not history.get('versions'):
            print("📋 该合同暂无历史审查记录")
            return
        
        versions = history['versions']
        contract_hash = history.get('contract_hash', 'unknown')
        print(f"\n{'=' * 60}")
        print(f"📋 合同审查历史 (ID: {contract_hash})")
        print(f"{'=' * 60}")
        
        for v in versions:
            ts = v.get('timestamp', '')
            score = v.get('score', 0)
            summary = v.get('summary', {})
            print(f"\n  📅 {ts} | ⭐ 评分: {score}/100")
            print(f"     风险: 严重{summary.get('critical',0)} 中等{summary.get('medium',0)} "
                  f"一般{summary.get('low',0)} 提示{summary.get('info',0)}")
    else:
        # 列出所有合同
        contracts = manager.list_all_contracts()
        if not contracts:
            print("📋 暂无历史审查记录")
            return
        
        print(f"\n{'=' * 60}")
        print(f"📋 所有审查记录 ({len(contracts)} 份合同)")
        print(f"{'=' * 60}")
        for c in contracts:
            print(f"\n  📄 {c['title']}")
            print(f"     类型: {c['contract_type']}")
            print(f"     审查次数: {c['total_versions']}")
            print(f"     最近审查: {c['last_reviewed']}")


# v4.0 行业展示名与可选别名
INDUSTRY_DISPLAY = {
    'medical': ('医疗/医药', '医疗器械采购、临床试验、药品配送、多点执业'),
    'construction': ('建筑/建设工程', '施工总承包、专业分包、EPC、监理、材料设备采购'),
    'cross_border': ('跨境电商/国际贸易', '国际货物买卖、跨境平台入驻、海外仓、国际物流'),
    'internet': ('互联网/软件', '软件开发外包、SaaS 服务、数据合规、平台运营、AI 应用'),
}


def show_industries():
    """v4.0 列出支持的行业专项及规则数量"""
    from pathlib import Path as _Path
    import yaml as _yaml

    base = _Path(__file__).parent.parent / 'references' / 'industries'
    print(f"\n{'=' * 60}")
    print("🏭 支持的行业专项合规审查 (v4.0)")
    print(f"{'=' * 60}")

    total = 0
    for code, (name, scope) in INDUSTRY_DISPLAY.items():
        rule_path = base / code / 'rules.yaml'
        count = 0
        if rule_path.exists():
            try:
                with open(rule_path, 'r', encoding='utf-8') as f:
                    data = _yaml.safe_load(f.read(2 * 1024 * 1024)) or {}
                count = len(data.get('rules', []))
            except Exception:
                count = 0
        total += count
        status = '✅' if count else '⚠️ 规则文件缺失'
        print(f"\n  {status} {name}  （--industry {code}）")
        print(f"     专项规则：{count} 条")
        print(f"     适用场景：{scope}")

    print(f"\n{'-' * 60}")
    print(f"  合计 {total} 条行业专项规则")
    print(f"  用法：python scripts/main.py 合同.pdf --industry medical")
    print(f"{'=' * 60}\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='合同智能审查工具 v4.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python scripts/main.py 合同.pdf                      # 基础审查
  python scripts/main.py 合同.pdf --role 甲方          # 从甲方视角审查
  python scripts/main.py 合同.pdf --format docx        # 输出 Word 报告
  python scripts/main.py 合同.pdf --diff old.json      # 版本对比审查
  python scripts/main.py 合同.pdf --industry medical   # 医疗行业专项审查（v4.0）
  python scripts/main.py 合同.pdf --revise             # 生成一键修订稿（v4.0）
  python scripts/main.py 合同.pdf --revise --revise-output 修订稿.docx
  python scripts/main.py --list-industries             # 查看支持的行业（v4.0）
  python scripts/main.py --history                     # 查看历史记录
  python scripts/main.py --history --text "合同内容"    # 查看该合同历史
  python scripts/main.py 合同.pdf --install-ollama     # 安装本地模型
  python scripts/main.py 合同.pdf --first-time         # 首次使用向导
  python scripts/main.py --check-update                # 检查更新
        """
    )
    parser.add_argument('file', nargs='?', help='合同文件路径（PDF/Word/图片/纯文本）')
    parser.add_argument('--type', '-t', default='', help='合同类型（如不指定则自动识别）')
    parser.add_argument('--role', '-r', default='双方', choices=['甲方', '乙方', '双方'],
                        help='审查视角（默认：双方）')
    parser.add_argument('--output', '-o', default='', help='输出文件路径（默认：report.md）')
    parser.add_argument('--format', '-f', default='markdown',
                        choices=['markdown', 'json', 'docx'],
                        help='输出格式（默认：markdown，v3.0 新增 docx）')
    parser.add_argument('--scope', default='全面审查', choices=['全面审查', '重点审查', '快速审查'],
                        help='审查范围（默认：全面审查）')
    parser.add_argument('--no-llm', action='store_true',
                        help='跳过 LLM 审查（仅使用规则引擎）')
    parser.add_argument('--text', '-x', default='', help='直接传入合同文本（而非文件路径）')
    parser.add_argument('--install-ollama', action='store_true',
                        help='一键安装 Ollama 本地模型')
    parser.add_argument('--first-time', action='store_true',
                        help='首次使用向导')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细日志')
    parser.add_argument('--history', action='store_true',
                        help='查看历史审查记录（v3.0）')
    parser.add_argument('--diff', default='',
                        help='对比指定历史报告 JSON 路径（v3.0），只高亮新增风险')
    parser.add_argument('--show-hardware', action='store_true',
                        help='显示硬件信息和性能配置（v3.0）')
    parser.add_argument('--check-update', action='store_true',
                        help='检查 Skill 更新（v3.0）')
    # ===== v4.0 新增参数 =====
    parser.add_argument('--industry', default='',
                        help='行业专项审查（v4.0）：medical/construction/cross_border/internet，'
                             '也支持中文如 医疗/建筑/跨境/互联网')
    parser.add_argument('--list-industries', action='store_true',
                        help='列出支持的行业专项及规则数量（v4.0）')
    parser.add_argument('--revise', action='store_true',
                        help='生成一键修订稿，自动匹配条款库推荐文本（v4.0）')
    parser.add_argument('--revise-output', default='',
                        help='修订稿输出路径（v4.0，默认 revision.docx）')
    parser.add_argument('--revise-format', default='auto',
                        choices=['auto', 'docx', 'md'],
                        help='修订稿格式（v4.0，默认按输出后缀自动判断）')
    parser.add_argument('--full-revision', action='store_true',
                        help='修订稿包含合同全文并就地标记（v4.0，默认仅输出修订清单）')
    parser.add_argument('--no-clause-match', action='store_true',
                        help='关闭条款库自动匹配（v4.0）')

    args = parser.parse_args()
    
    start_time = time.time()
    
    # ===== v3.0 特殊命令处理 =====
    
    if args.list_industries:
        show_industries()
        return
    
    if args.check_update:
        from updater import UpdateChecker
        checker = UpdateChecker()
        update_info = checker.check(force=True)
        if update_info:
            print(checker.get_update_message(update_info))
        else:
            print("✅ 当前已是最新版本")
        return
    
    if args.show_hardware:
        from hardware_detector import HardwareDetector
        detector = HardwareDetector()
        info = detector.detect(force_refresh=True)
        config = detector.get_optimal_config(info)
        print(f"\n{'=' * 50}")
        print("🖥️  硬件信息")
        print(f"{'=' * 50}")
        print(f"  CPU: {info.get('cpu_cores', '?')} 核 @ {info.get('cpu_freq_mhz', 0):.0f} MHz")
        print(f"  内存: {info.get('memory_total_gb', 0):.1f} GB (可用 {info.get('memory_available_gb', 0):.1f} GB)")
        gpu = info.get('gpu_name', '无独立 GPU') if info.get('has_gpu') else '无独立 GPU'
        print(f"  GPU: {gpu}")
        print(f"\n📊 性能配置")
        print(f"  等级: {config['hardware_tier']}")
        print(f"  OCR 并行: {config['ocr_batch_size']} 页/批")
        print(f"  LLM 超时: {config['llm_timeout']}s")
        print(f"  并发审查: {config['max_concurrent_reviews']}")
        return
    
    if args.history:
        show_history(args.text if args.text else None)
        return
    
    # 特殊命令
    if args.first_time:
        first_time_setup()
        if not args.file:
            return
    
    if args.install_ollama:
        install_ollama()
        if not args.file:
            return
    
    # ===== 硬件检测与性能调度 =====
    print_banner()
    
    from hardware_detector import HardwareDetector
    hw_detector = HardwareDetector()
    hw_config = hw_detector.get_optimal_config()
    hw_summary = hw_detector.format_hardware_summary()
    print(f"🖥️  {hw_summary} | 等级: {hw_config['hardware_tier']}", flush=True)
    
    # ===== v3.0 异步更新检测（不阻塞） =====
    update_info = None
    try:
        from updater import UpdateChecker
        update_checker = UpdateChecker()
        update_info = update_checker.check()
    except Exception:
        pass  # 更新检测失败不影响审查
    
    try:
        total_steps = 5
        
        # Step 1: 获取合同文件
        print_step(1, total_steps, "接收合同文件")
        
        if args.text:
            contract_text = args.text
            file_type = "txt"
            metadata = {}
            contract_hash = hashlib.sha256(''.join(contract_text.split()).encode('utf-8')).hexdigest()[:16]
            print_success(f"收到文本输入（{len(contract_text)} 字符）")
        elif args.file:
            from extract_text import TextExtractor
            extractor = TextExtractor(enable_security=True)
            result = extractor.extract(args.file)
            contract_text = result['text']
            file_type = result['file_type']
            metadata = result.get('metadata', {})
            warnings = result.get('warnings', [])
            contract_hash = hashlib.sha256(''.join(contract_text.split()).encode('utf-8')).hexdigest()[:16]
            
            print_success(
                f"文件类型={file_type}, "
                f"页数={metadata.get('total_pages', '?')}, "
                f"字数={metadata.get('total_words', '?')}"
            )
            
            if result.get('ocr_confidence'):
                conf = result['ocr_confidence']
                if conf >= 0.95:
                    print_success(f"OCR 置信度: {conf:.0%}")
                else:
                    print_warning(f"OCR 置信度: {conf:.0%}，建议核对扫描件")
            
            for w in warnings:
                print_warning(w)
        else:
            print_error("请提供合同文件路径或文本内容")
            print("  --file <路径>    上传合同文件")
            print("  --text \"内容\"    直接审查文本")
            print("  --first-time     首次使用向导")
            print("  --history        查看历史记录")
            print("  --check-update   检查更新")
            sys.exit(1)
        
        # Step 2: 结构解析
        print_step(2, total_steps, "结构化解析")
        
        from parse_structure import ContractParser
        parser = ContractParser()
        structure = parser.parse(contract_text)
        
        if args.type:
            structure.contract_type = args.type
        
        print_success(
            f"标题={structure.title[:30] if structure.title else '未知'}, "
            f"类型={structure.contract_type}, "
            f"条款数={len(structure.clauses)}"
        )
        
        # Step 3: 规则引擎检查
        print_step(3, total_steps, "规则引擎检查")
        
        from rule_engine import RuleEngine, normalize_industry
        rules_path = Path(__file__).parent.parent / 'references' / 'risk_rules.yaml'
        engine = RuleEngine(str(rules_path))
        
        # v4.0 行业专项审查
        industry_code = normalize_industry(args.industry)
        industry_name = ''
        if args.industry and not industry_code:
            print_warning(
                f"未识别的行业「{args.industry}」，已忽略行业专项规则。"
                f"可用值：{', '.join(INDUSTRY_DISPLAY.keys())}"
            )
        elif industry_code:
            industry_name = INDUSTRY_DISPLAY.get(industry_code, (industry_code, ''))[0]
            print(f"  🏭 启用 {industry_name} 行业专项规则")
        
        rule_risks = engine.check_all(
            contract_text, structure.contract_type, structure.to_dict(),
            industry=industry_code,
        )
        
        print_success(f"完成 {len(rule_risks)} 项硬规则检查")
        
        # v4.0 行业专项规则均为语义审查型，需 LLM 参与才能生效，
        # 在 --no-llm 模式下明确告知用户，避免误以为已完成行业审查。
        if industry_code and args.no_llm:
            print_warning(
                f"{industry_name}行业专项规则为语义审查型，需 AI 参与才能生效。"
                f"当前为 --no-llm 模式，本次仅执行通用硬规则检查。"
            )
        
        # Step 4: LLM 审查（可选）
        print_step(4, total_steps, "AI 审查")
        
        llm_risks = []
        missing_clauses = []
        special_notes = []
        
        if not args.no_llm:
            from llm_review import LLMReviewer
            reviewer = LLMReviewer()
            
            if reviewer.backend != "none":
                print(f"  🤖 使用 {reviewer.backend} / {reviewer.model}")
                llm_result = reviewer.review(
                    contract_text=contract_text,
                    contract_type=structure.contract_type,
                    party_role=args.role,
                    industry=industry_code,
                )
                llm_risks = llm_result.get('risks', [])
                missing_clauses = llm_result.get('missing_clauses', [])
                special_notes = llm_result.get('special_notes', [])
                
                print_success(f"发现 {len(llm_risks)} 个 AI 识别风险")
                
                for note in special_notes:
                    print_warning(note)
            else:
                print_warning("未检测到 LLM 后端，仅使用规则引擎结果")
                print("  💡 安装 Ollama 后可启用完整 AI 审查功能")
                special_notes.append("LLM 审查未启用（未检测到 OpenAI API 或本地模型）")
        else:
            print("  ⏭️  跳过 LLM 审查（--no-llm）")
        
        # Step 5: 生成审查报告
        print_step(5, total_steps, "生成审查报告")
        
        all_risks = []
        
        for r in rule_risks:
            all_risks.append(r.to_dict())
        
        for r in llm_risks:
            all_risks.append({
                'risk_id': r.get('risk_id', f'LLM_{len(all_risks)+1:03d}'),
                'risk_type': r.get('risk_type', '其他风险'),
                'severity': r.get('severity', '中等'),
                'title': r.get('title', ''),
                'description': r.get('description', ''),
                'suggestion': r.get('suggestion', ''),
                'legal_basis': r.get('legal_basis', ''),
                'text_snippet': r.get('text_snippet', ''),
                'clause_ref': r.get('clause_ref', ''),
                'template': r.get('template', ''),
            })
        
        # 去重
        seen = set()
        unique_risks = []
        for r in all_risks:
            key = f"{r.get('risk_type', '')}_{r.get('clause_ref', '')}_{r.get('title', '')}"
            if key not in seen:
                seen.add(key)
                unique_risks.append(r)
        
        from generate_report import ReportGenerator
        
        contract_info = {
            'title': structure.title,
            'contract_type': structure.contract_type,
            'party_role': args.role,
            'parties': [{'role': p.role, 'name': p.name} for p in structure.parties],
            'total_amount': structure.total_amount,
            'currency': structure.currency,
            'missing_clauses': missing_clauses,
            'special_notes': special_notes,
            'industry': industry_code,
            'industry_name': industry_name,
            'file_name': Path(args.file).name if args.file else '文本输入',
        }
        
        generator = ReportGenerator(enable_clause_match=not args.no_clause_match)
        
        # v4.0 条款库匹配（统一在此执行，Word/Markdown/JSON 三种格式共享结果）
        if not args.no_clause_match:
            unique_risks = generator._enrich_with_clauses(
                unique_risks, structure.contract_type
            )
            matched = sum(1 for r in unique_risks if r.get('clause_id'))
            if matched:
                print_success(f"条款库匹配 {matched} 条推荐替换文本")
        
        # ===== v3.0 版本对比 =====
        diff_result = None
        if args.diff:
            try:
                import json
                from history_manager import HistoryManager
                with open(args.diff, 'r', encoding='utf-8') as f:
                    old_report = json.load(f)
                old_risks = old_report.get('risks', [])
                new_risks = unique_risks
                
                manager = HistoryManager()
                diff_result = manager.diff_reviews(
                    {'risks': old_risks},
                    {'risks': new_risks}
                )
                if diff_result['new_risks']:
                    print_success(f"版本对比：发现 {len(diff_result['new_risks'])} 个新增风险点")
                if diff_result['resolved_risks']:
                    print_success(f"版本对比：{len(diff_result['resolved_risks'])} 个风险已解决")
            except Exception as e:
                print_warning(f"版本对比失败: {e}")
        
        # 根据格式生成报告
        if args.format == 'docx':
            # v3.0 Word 报告生成
            try:
                from docx_generator import DocxGenerator
                docx_generator = DocxGenerator()
                output_path = args.output or 'report.docx'
                docx_generator.generate(unique_risks, contract_info, output_path)
                print_success(f"Word 报告已生成: {output_path}")
                report = f"Word 报告已保存至 {output_path}"
            except ImportError as e:
                print_error(f"Word 生成依赖缺失: {e}")
                print("  回退到 Markdown 格式")
                report = generator.generate(unique_risks, contract_info, 'markdown')
                args.format = 'markdown'
                output_path = args.output or 'report.md'
        else:
            report = generator.generate(unique_risks, contract_info, args.format)
        
        # 标准输出
        if args.format != 'docx':
            output_path = args.output or f'report.{args.format}'
            if output_path and args.format != 'docx':
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(report)
                print_success(f"报告已保存至: {output_path}")
        
        # ===== v4.0 一键修订稿 =====
        if args.revise:
            try:
                from contract_reviser import ContractReviser
                reviser = ContractReviser()
                revise_out = args.revise_output or 'revision.docx'
                revise_result = reviser.revise(
                    unique_risks,
                    contract_info,
                    revise_out,
                    contract_text=contract_text if args.full_revision else '',
                    fmt=args.revise_format,
                )
                print_success(
                    f"修订稿已生成: {revise_result['output']}"
                    f"（{revise_result['count']} 条修订建议"
                    + (f"，原文定位 {revise_result['located']} 处" if args.full_revision else "")
                    + "）"
                )
                if revise_result['count'] == 0:
                    if not unique_risks:
                        print("  ℹ️  本次未发现需修订的风险点，修订稿为空稿", flush=True)
                    else:
                        print_warning("未生成修订条目：风险点缺少推荐条款文本")
            except Exception as e:
                print_warning(f"修订稿生成失败: {e}")
        
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 50, flush=True)
        print(f"🎉 审查完成！耗时 {elapsed:.1f} 秒", flush=True)
        print("=" * 50, flush=True)
        print(flush=True)
        
        # ===== v3.0 保存到历史记录 =====
        try:
            from history_manager import HistoryManager
            import json
            from datetime import datetime
            
            review_result_for_history = {
                'score': generator._calculate_score(unique_risks),
                'contract_info': contract_info,
                'risks': unique_risks,
                'report_summary': f"审查完成，发现 {len(unique_risks)} 个风险点",
            }
            
            manager = HistoryManager()
            record_id = manager.save_review(contract_text, review_result_for_history)
            
            # 保存完整 report JSON（用于未来 --diff 对比）
            report_json_path = Path.home() / '.contract-review' / 'history' / f"{contract_hash}_last.json"
            with open(report_json_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'report_id': record_id,
                    'generated_at': datetime.now().isoformat(),
                    'contract_info': contract_info,
                    'risks': unique_risks,
                    'diff_result': diff_result,
                }, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 审查记录已保存 (ID: {record_id})", flush=True)
            print(f"   使用 --diff {report_json_path} 可进行版本对比", flush=True)
            
            # 显示 diff 结果
            if diff_result:
                print(f"\n{'=' * 50}")
                print(f"📊 版本对比结果")
                print(f"{'=' * 50}")
                print(diff_result['summary'])
                if diff_result['new_risks']:
                    print(f"\n🆕 新增风险点:")
                    for r in diff_result['new_risks']:
                        print(f"  - [{r.get('severity', '?')}] {r.get('title', '')}")
                if diff_result['resolved_risks']:
                    print(f"\n✅ 已解决风险点:")
                    for r in diff_result['resolved_risks']:
                        print(f"  - {r.get('title', '')}")
                if diff_result['changed_risks']:
                    print(f"\n⚠️ 等级变化:")
                    for r in diff_result['changed_risks']:
                        print(f"  - {r['title']}: {r['old_severity']} → {r['new_severity']}")
        except Exception as e:
            logger.debug(f"保存历史记录失败: {e}")
        
        # 打印报告（非 docx 格式）
        if args.format != 'docx':
            print(report)
        
        # ===== v3.0 更新提醒 =====
        if update_info and update_info.get('should_notify'):
            print("\n" + "=" * 50, flush=True)
            print(f"📢 发现新版本", flush=True)
            print(f"{'=' * 50}", flush=True)
            local_v = update_info.get('local_version', '?')
            remote_v = update_info.get('remote_version', '?')
            print(f"📢 发现新版本 v{remote_v} (当前 v{local_v})", flush=True)
            print(f"更新内容：新增 Word 报告生成、历史版本对比、硬件自适应、安全风险拦截等功能。", flush=True)
            print(f"更新方法：运行 skillhub install contract-review", flush=True)
            print(f"{'=' * 50}", flush=True)
            try:
                from updater import UpdateChecker
                UpdateChecker().record_notified(remote_v)
            except Exception:
                pass
        
    except FileNotFoundError as e:
        print_error(f"文件不存在: {e}")
        sys.exit(1)
    except ImportError as e:
        print_error(f"依赖缺失: {e}")
        print("请运行: pip install -r requirements.txt")
        sys.exit(1)
    except PermissionError as e:
        print_error(f"安全拦截: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"审查失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
