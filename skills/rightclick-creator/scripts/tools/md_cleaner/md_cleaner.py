#!/usr/bin/env python3
"""
MD整理工具 - 使用通义千问API修复PDF转Markdown后的混乱文档
"""

import re
import sys
import os
import json
import argparse
import subprocess
import time
from pathlib import Path
from typing import Optional
import urllib.parse

# 优先使用 requests（流式传输更稳定），降级到 http.client
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def show_dialog(title: str, message: str, buttons = None) -> str:
    """显示macOS对话框"""
    if buttons is None:
        buttons = ["确定"]

    button_str = ", ".join([f'"{b}"' for b in buttons])
    script = f'''
    tell application "System Events"
        display dialog "{message}" with title "{title}" buttons {{{button_str}}} default button 1
        set buttonReturned to button returned of result
    end tell
    '''

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return buttons[0] if buttons else ""


def show_notification(title: str, message: str):
    """显示macOS通知"""
    try:
        subprocess.run([
            "osascript", "-e",
            f'display notification "{message}" with title "{title}"'
        ], check=False)
    except:
        pass


class MDCleaner:
    """Markdown文档清理器"""

    # DeepSeek 模型分级配置
    DS_TIERS = {
        "small": {"model": "deepseek-v4-pro", "max_tokens": 6000, "input_price": 0.27, "output_price": 1.10},
        "medium": {"model": "deepseek-v4-pro", "max_tokens": 30000, "input_price": 0.27, "output_price": 1.10},
        "large": {"model": "deepseek-v4-pro", "max_tokens": 60000, "input_price": 0.27, "output_price": 1.10}
    }

    # 通义千问模型分级配置
    QWEN_TIERS = {
        "small": {"model": "qwen-turbo", "max_tokens": 6000, "input_price": 0.3, "output_price": 9.6},
        "medium": {"model": "qwen-plus", "max_tokens": 30000, "input_price": 0.8, "output_price": 2.0},
        "large": {"model": "qwen3.5-plus", "max_tokens": 60000, "input_price": 0.8, "output_price": 4.8}
    }

    def __init__(self):
        self.config = self._load_config()
        # 自动选择 API：优先 DeepSeek，其次千问
        self.deepseek_key = self.config.get('deepseek_api_key', '')
        self.qwen_key = self.config.get('api_key', '')  # 兼容旧配置

        if self.deepseek_key:
            self.provider = 'deepseek'
            self.api_key = self.deepseek_key
            self.base_url = 'api.deepseek.com'
            self.model_tiers = self.DS_TIERS
        elif self.qwen_key:
            self.provider = 'qwen'
            self.api_key = self.qwen_key
            self.base_url = 'dashscope.aliyuncs.com'
            self.model_tiers = self.QWEN_TIERS
        else:
            self.provider = None
            self.api_key = ''
            self.base_url = ''
            self.model_tiers = self.QWEN_TIERS  # fallback

        self.model = 'auto'

    @property
    def provider_name(self) -> str:
        """返回当前供应商的中文名"""
        return 'DeepSeek' if self.provider == 'deepseek' else '通义千问'

    def _detect_corruption(self, content: str) -> str:
        """检测文档损坏程度，返回 'low' | 'high'"""
        lines = content.split('\n')
        non_empty = [l.strip() for l in lines if l.strip()]
        if not non_empty:
            return 'low'
        garbage_patterns = [
            r'^\s*[a-zA-Z]{1,4}\s*$',
            r'^\s*\d{1,2}\s*$',
            r'^\s*[`°*.·\-]+\s*$',
            r'^\s*---\s*第?\s*\d+\s*页?\s*---',
            r'^\s*第?\s*\d+\s*页?\s*---',
            r'^\s*---\s*PDF处理报告\s*---',
            r'^(总页数|成功识别|OCR降级|识别失败):',
            r'^```\s*\w*\s*$',
        ]
        garbage_lines = 0
        for stripped in non_empty:
            for pattern in garbage_patterns:
                if re.match(pattern, stripped, re.IGNORECASE):
                    garbage_lines += 1
                    break
        return 'high' if garbage_lines / len(non_empty) > 0.12 else 'low'

    def _preprocess(self, content: str) -> str:
        """预处理：去除代码块包裹、分页线、PDF处理报告、垃圾行"""
        content = re.sub(r'^\s*```\s*\w*\s*\n', '', content)
        content = re.sub(r'\n\s*```\s*$', '', content)
        lines = content.split('\n')
        cleaned_lines = []
        skip_pdf_report = False
        for line in lines:
            stripped = line.strip()
            if re.match(r'^(---\s*)?第?\s*\d+\s*页?\s*---', stripped):
                continue
            if re.match(r'^---\s*PDF处理报告\s*---', stripped):
                skip_pdf_report = True
                continue
            if re.match(r'^第?\s*\d+\s*页\s*---', stripped):
                continue
            if skip_pdf_report:
                continue
            if re.match(r'^(总页数|成功识别|OCR降级|识别失败):', stripped):
                continue
            if re.match(r'^\s*[a-zA-Z]{1,4}\s*$', stripped):
                continue
            if re.match(r'^\s*\d{1,2}\s*$', stripped):
                continue
            if re.match(r'^\s*[`°*.·\-]+\s*$', stripped):
                continue
            cleaned_lines.append(line)
        return '\n'.join(cleaned_lines)

    def _postprocess(self, content: str) -> str:
        """后处理：去除模型返回的代码块包裹、规范化空行"""
        content = re.sub(r'^\s*```\s*\w*\s*\n', '', content)
        content = re.sub(r'\n\s*```\s*$', '', content)
        content = re.sub(r'^\s*#+\s*.*\n', '', content, count=1)
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = '\n'.join(line.rstrip() for line in content.split('\n'))
        return content.strip()

    def _select_model(self, token_count: int, corruption_level: str = 'low') -> tuple:
        """
        根据token数量和文档损坏程度自动选择模型
        返回: (模型名称, 最大输出tokens, 分级名称)
        """
        tiers = sorted(self.model_tiers.items(), key=lambda x: x[1]['max_tokens'])
        if corruption_level == 'high':
            for tier_name, tier_config in tiers:
                if tier_name in ('medium', 'large') and token_count <= tier_config['max_tokens']:
                    return tier_config['model'], tier_config['max_tokens'], tier_name
            largest = tiers[-1][1]
            return largest['model'], largest['max_tokens'], tiers[-1][0]
        for tier_name, tier_config in tiers:
            if token_count <= tier_config['max_tokens']:
                return tier_config['model'], tier_config['max_tokens'], tier_name
        largest = tiers[-1][1]
        return largest['model'], largest['max_tokens'], tiers[-1][0]

    def _load_config(self) -> dict:
        """加载配置文件"""
        config_paths = [
            Path.home() / '.rightclick-creator' / 'config' / 'md_cleaner.json',
            Path.home() / '.tools' / 'config' / 'md_cleaner.json',     # 旧路径兼容
            Path.home() / '.config' / 'md_cleaner' / 'config.json',
        ]

        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    print(f"警告：无法读取配置文件 {config_path}: {e}")

        return {}

    def _estimate_tokens(self, text: str) -> int:
        """估算文本的token数量（中文约1.5-2 tokens/字）"""
        # 简单估算：中文字符按2 tokens，英文按0.5 tokens
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars * 2 + other_chars * 0.5)

    def _split_content(self, content: str, max_tokens: int = 6000) -> list:
        """
        智能分段处理
        按段落分割，保持上下文完整性
        """
        total_tokens = self._estimate_tokens(content)

        # 如果总token数在安全范围内，直接返回
        if total_tokens <= max_tokens:
            return [content]

        print(f"  文档较大（约{total_tokens} tokens），将分段处理...")

        # 按段落分割
        paragraphs = content.split('\n\n')
        segments = []
        current_segment = []
        current_tokens = 0

        for para in paragraphs:
            para_tokens = self._estimate_tokens(para)

            # 如果当前段落单独就超过限制，需要进一步分割
            if para_tokens > max_tokens:
                # 先保存当前段
                if current_segment:
                    segments.append('\n\n'.join(current_segment))
                    current_segment = []
                    current_tokens = 0

                # 按句子分割大段落
                sentences = para.replace('。', '。\n').replace('！', '！\n').replace('？', '？\n').split('\n')
                temp_segment = []
                temp_tokens = 0

                for sent in sentences:
                    sent_tokens = self._estimate_tokens(sent)
                    if temp_tokens + sent_tokens > max_tokens and temp_segment:
                        segments.append('\n'.join(temp_segment))
                        temp_segment = [sent]
                        temp_tokens = sent_tokens
                    else:
                        temp_segment.append(sent)
                        temp_tokens += sent_tokens

                if temp_segment:
                    segments.append('\n'.join(temp_segment))
            else:
                # 正常段落，检查是否可以加入当前段
                if current_tokens + para_tokens > max_tokens and current_segment:
                    segments.append('\n\n'.join(current_segment))
                    current_segment = [para]
                    current_tokens = para_tokens
                else:
                    current_segment.append(para)
                    current_tokens += para_tokens

        # 保存最后一段
        if current_segment:
            segments.append('\n\n'.join(current_segment))

        print(f"  已分割为 {len(segments)} 个段落")
        return segments

    def _call_qwen_api(self, content: str, model: str = None, max_output_tokens: int = 16384) -> Optional[str]:
        """调用AI API（requests流式优先，降级到http.client）"""
        if not self.api_key:
            print("错误：未配置 API Key")
            show_dialog("MD整理", "❌ 未配置 API Key\n\n请通过 WorkBuddy 配置 DeepSeek 或 通义千问 的 API Key", ["确定"])
            return None

        if model is None:
            model = self.model

        prompt = f"""你是一位专业的文档修复专家。以下文本是从扫描版PDF通过OCR识别后转换而来的Markdown文档，存在严重的识别错误。你的任务是尽可能还原原始文档的真实内容。

## 修复要求（按优先级排序）

1. **修复乱码和错误字符**：
   - 将明显的乱码（如纯无意义的字母组合 `Be Ze ri]`、`Tres"`、`gua`、`Seat`、`CARI`、`Sih`、纯数字行、纯符号行等）根据上下文语义推断并替换为正确的中文字符。
   - 注意：出租方公司名称、金额数字、人名、地址等关键信息必须尽力推断还原。
   - 示例：`成部佳之峰` 应修正为 `成都佳之峰`；`龙朵又区` 应修正为 `龙泉驿区`。

2. **修复断行和排版**：
   - 将被错误断开的句子合并为自然段落，恢复正常的阅读流。
   - 去除无意义的短行和孤立字符。

3. **修正错别字和标点**：
   - 修正 OCR 识别导致的错别字（如 `哲免`→`暂免`、`不子退还`→`不予退还`、`是额`→`足额` 等）。
   - 修正标点符号错误（中英文标点混用、多余空格等）。

4. **规范化格式**：
   - 保持合同条文的层次结构（第一条、第二条…）。
   - 使用标准 Markdown 格式，但不要添加原始文档中没有的标题或层级。

## 重要约束

- 必须保持原文的内容完整，不得增删条款。
- 不得添加任何解释、说明或总结。
- 直接输出修复后的纯文本内容，不要包裹在代码块（```）中。

---

待修复文档：

{content}"""

        # DeepSeek 和千问的 API 路径不同
        api_path = '/v1/chat/completions' if self.provider == 'deepseek' else '/compatible-mode/v1/chat/completions'
        api_url = f"https://{self.base_url}{api_path}"

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": max_output_tokens,
            "stream": True  # 启用流式传输
        }

        # ── 主方案：requests + stream=True ──
        if HAS_REQUESTS:
            try:
                resp = requests.post(api_url, headers=headers, json=payload, stream=True, timeout=300)
                resp.raise_for_status()

                full_content = ""
                for line in resp.iter_lines(decode_unicode=True):
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]  # 去掉 "data: " 前缀
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        piece = delta.get("content", "")
                        if piece:
                            full_content += piece
                    except json.JSONDecodeError:
                        continue

                if full_content:
                    return full_content
                print("API流式响应为空")
                return None

            except requests.exceptions.RequestException as e:
                print(f"requests流式请求失败: {e}")
                # 降级到 http.client（不直接返回None，继续执行降级逻辑）
                pass

        # ── 降级方案：http.client + IncompleteRead容错 ──
        try:
            conn = http.client.HTTPSConnection(self.base_url, timeout=360)
            body = json.dumps(payload)
            conn.request("POST", api_path, body, headers)
            response = conn.getresponse()

            if response.status != 200:
                error_body = response.read().decode('utf-8')
                print(f"API调用失败: HTTP {response.status}")
                print(f"错误详情: {error_body}")
                conn.close()
                return None

            # 读取响应体，增加 IncompleteRead 容错
            try:
                raw_data = response.read()
            except http.client.IncompleteRead as e:
                # 服务端 chunked 传输中途断连，使用已读取的部分数据
                raw_data = e.partial
                print(f"警告: 响应读取不完整，使用已接收的 {len(raw_data)} 字节")

            conn.close()

            data = json.loads(raw_data.decode('utf-8'))

            if 'choices' in data and len(data['choices']) > 0:
                return data['choices'][0]['message']['content']
            else:
                print(f"API响应格式异常: {data}")
                return None

        except Exception as e:
            print(f"API调用出错: {e}")
            return None

    def clean_file(self, file_path: str) -> bool:
        """清理单个Markdown文件"""
        path = Path(file_path)

        if not path.exists():
            print(f"错误：文件不存在 {file_path}")
            return False

        if path.suffix.lower() not in ['.md', '.markdown']:
            print(f"跳过非Markdown文件: {file_path}")
            return False

        try:
            # 读取原文件
            with open(path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            if not original_content.strip():
                print(f"跳过空文件: {file_path}")
                return False

            # 预处理：去除代码块包裹、分页线、PDF报告、垃圾行
            preprocessed = self._preprocess(original_content)
            print(f"  预处理完成：去除代码块包裹、分页线、垃圾行")

            # 检测文档损坏程度
            corruption_level = self._detect_corruption(original_content)
            if corruption_level == 'high':
                print(f"  检测到文档损坏严重，将升级模型")

            # 估算token数量（基于预处理后的内容）
            total_tokens = self._estimate_tokens(preprocessed)
            print(f"  文档大小: 约{total_tokens} tokens")

            # 自动选择模型（考虑损坏程度）
            selected_model, max_output, tier_name = self._select_model(total_tokens, corruption_level)
            print(f"  自动选择模型: {selected_model} ({tier_name}级)")

            # 检查是否需要分段（超过最大模型限制）
            if total_tokens > self.model_tiers['large']['max_tokens']:
                print(f"  文档超过最大模型限制，将使用{self.model_tiers['large']['model']}分段处理")
                segments = self._split_content(preprocessed, max_tokens=self.model_tiers['large']['max_tokens'])
                total_segments = len(segments)

                show_dialog(
                    "MD整理",
                    f"✅ 已与{self.provider_name}连接成功！\n\n正在处理: {path.name}\n\n文档超大，将使用{self.model_tiers['large']['model']}分{total_segments}段处理\n\n⏱️ 预计需要 {total_segments * 2}-{total_segments * 3} 分钟\n\n在此期间请勿操作该文档",
                    ["我知道了"]
                )

                # 分段处理
                cleaned_segments = []
                for i, segment in enumerate(segments, 1):
                    print(f"  处理第 {i}/{total_segments} 段...")

                    cleaned_segment = self._call_qwen_api(
                        segment,
                        model=self.model_tiers['large']['model'],
                        max_output_tokens=self.model_tiers['large']['max_tokens']
                    )

                    if cleaned_segment is None:
                        print(f"第 {i} 段处理失败")
                        show_dialog("MD整理", f"❌ 处理失败: {path.name}\n\n第 {i}/{total_segments} 段处理失败\n\n请检查网络连接或API配置", ["确定"])
                        return False

                    cleaned_segments.append(cleaned_segment)

                    if i < total_segments:
                        show_notification("MD整理", f"进度: {i}/{total_segments} 段完成，继续处理...")

                cleaned_content = '\n\n'.join(cleaned_segments)
            else:
                # 一次性处理
                show_dialog(
                    "MD整理",
                    f"✅ 已与{self.provider_name}连接成功！\n\n正在处理: {path.name}\n\n使用模型: {selected_model}\n\n⏱️ 预计需要 1-3 分钟\n\n在此期间请勿操作该文档",
                    ["我知道了"]
                )

                cleaned_content = self._call_qwen_api(
                    preprocessed,
                    model=selected_model,
                    max_output_tokens=max_output
                )

                if cleaned_content is None:
                    print(f"处理失败: {path.name}")
                    show_dialog("MD整理", f"❌ 处理失败: {path.name}\n\n请检查网络连接或API配置", ["确定"])
                    return False

            # 后处理：去除代码块包裹、规范化空行
            cleaned_content = self._postprocess(cleaned_content)

            # 备份原文件
            backup_path = path.with_suffix('.md.backup')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)

            # 写入修复后的内容
            with open(path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)

            print(f"✓ 完成: {path.name}")

            # 删除备份文件
            if backup_path.exists():
                backup_path.unlink()
                print(f"  已删除备份: {backup_path.name}")

            # 显示完成弹窗
            show_dialog(
                "MD整理",
                f"✅ 整理完毕！\n\n文件: {path.name}\n\n已修复内容并保存",
                ["确定"]
            )

            # 显示完成通知
            show_notification("MD整理", f"✅ {path.name} 处理完成！")
            return True

        except Exception as e:
            print(f"处理文件时出错 {file_path}: {e}")
            show_dialog("MD整理", f"❌ 处理出错: {path.name}\n\n错误: {str(e)}", ["确定"])
            return False

    def clean_files(self, file_paths: list) -> dict:
        """批量清理多个文件"""
        results = {'success': [], 'failed': []}

        for file_path in file_paths:
            if self.clean_file(file_path):
                results['success'].append(file_path)
            else:
                results['failed'].append(file_path)

        return results


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='MD整理工具 - 使用AI修复Markdown文档')
    parser.add_argument('files', nargs='+', help='要处理的Markdown文件路径')
    parser.add_argument('--config', '-c', help='配置文件路径')

    args = parser.parse_args()

    # 限制处理文件数量
    if len(args.files) > 5:
        print("警告：一次最多处理5个文件，将只处理前5个")
        args.files = args.files[:5]

    cleaner = MDCleaner()
    results = cleaner.clean_files(args.files)

    # 输出统计
    print(f"\n处理完成:")
    print(f"  成功: {len(results['success'])} 个文件")
    print(f"  失败: {len(results['failed'])} 个文件")

    if results['failed']:
        print(f"\n失败的文件:")
        for f in results['failed']:
            print(f"  - {f}")

    sys.exit(0 if len(results['failed']) == 0 else 1)


if __name__ == '__main__':
    main()
