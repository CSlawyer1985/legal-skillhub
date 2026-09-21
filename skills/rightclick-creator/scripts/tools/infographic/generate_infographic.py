#!/usr/bin/env python3
"""
生成信息图的核心 Python 脚本 - 带AI来源标注版
由 workflow 调用
"""

import sys
import json
import re
import time
from pathlib import Path

# 优先使用 requests（流式传输更稳定），降级到 urllib
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    HAS_REQUESTS = False

MAX_CONTENT_LENGTH = 15000  # 输入内容截断阈值

def load_config():
    """加载配置文件"""
    config_paths = [
        Path.home() / '.rightclick-creator' / 'config' / 'infographic.json',
        Path.home() / '.config' / 'infographic' / 'config.json',
    ]

    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"警告：无法读取配置文件 {config_path}: {e}")

    return {}

def main():
    if len(sys.argv) < 7:
        print("Usage: generate_infographic.py <input_md_file> <output_html_file> <api_key> <api_url> <model_name> <ai_suffix> [max_tokens]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    api_key = sys.argv[3]
    api_url = sys.argv[4]
    model_name = sys.argv[5]
    ai_suffix = sys.argv[6]
    try:
        max_tokens = int(sys.argv[7]) if len(sys.argv) > 7 else 8000
    except ValueError:
        print(f"警告: max_tokens 参数无效，使用默认值 8000")
        max_tokens = 8000

    # 输入验证
    if not Path(input_file).exists():
        print(f"错误: 输入文件不存在: {input_file}")
        sys.exit(1)

    # 如果命令行未提供 api_key，尝试从配置文件加载
    if not api_key or api_key == "YOUR_API_KEY":
        config = load_config()
        api_key = config.get('api_key', '')
        if not api_key:
            print("错误：未提供 API Key")
            print("请在 ~/.rightclick-creator/config/infographic.json 中配置 api_key")
            sys.exit(1)

    # 根据 AI 来源设置显示名称
    if ai_suffix == "ds":
        ai_name = "DeepSeek"
    else:
        ai_name = "千问3.5-plus"

    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print(f"API URL: {api_url}")
    print(f"Model: {model_name}")
    print(f"AI Source: {ai_name} ({ai_suffix})")

    try:
        # 读取 markdown 内容
        with open(input_file, "r", encoding="utf-8") as f:
            md_content = f.read()

        print(f"Content length: {len(md_content)}")

        # 输入截断：防止 prompt 过长导致 API 超时或响应过大
        if len(md_content) > MAX_CONTENT_LENGTH:
            md_content = md_content[:MAX_CONTENT_LENGTH] + "\n\n[... 内容过长，已截断 ...]"
            print(f"Content truncated to {MAX_CONTENT_LENGTH} chars")

        # 构建请求
        system_prompt = f"""你是一个专业的信息图设计师。请将以下内容转换为逻辑清晰、一目了然、信息密度高的HTML信息图。

要求：
1. 使用浅色商务系配色（白、浅灰、深蓝、深灰）
2. 如果涉及逻辑和数学运算，要将步骤全部逐一列清楚
3. 使用现代简洁的CSS样式
4. 假设阅读者对相关内容不了解，要以易懂的方式展示
5. 输出完整的HTML代码，包含style标签
6. 使用中文
7. 确保HTML结构完整，包含DOCTYPE、html、head、body标签
8. 在页面底部添加一行小字标注："本信息图由 {ai_name} AI 生成"，使用灰色小字体"""

        user_prompt = f"请将以下内容转换为信息图HTML：\n\n{md_content}"

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": max_tokens,
            "stream": True  # 启用流式传输，避免大响应 IncompleteRead
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        print("Sending API request...")

        # ── 带重试的 API 调用（requests 流式优先，降级到 urllib）──
        content = ""
        last_error = None
        for attempt in range(3):
            try:
                if attempt > 0:
                    wait = 2 ** attempt
                    print(f"等待 {wait} 秒后重试...")
                    time.sleep(wait)

                if HAS_REQUESTS:
                    # 主方案：requests + stream=True（SSE 解析）
                    resp = requests.post(api_url, headers=headers, json=payload, stream=True, timeout=300)
                    resp.raise_for_status()

                    # 逐行读取 SSE 数据
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
                                content += piece
                        except json.JSONDecodeError:
                            continue
                    break  # 成功，跳出重试循环
                else:
                    # 降级方案：urllib（非流式，增加 IncompleteRead 容错）
                    req = urllib.request.Request(
                        api_url,
                        data=json.dumps(payload).encode("utf-8"),
                        headers=headers,
                        method="POST"
                    )
                    response = urllib.request.urlopen(req, timeout=300)
                    with response:
                        result = json.loads(response.read().decode("utf-8"))
                        choices = result.get("choices")
                        if choices and isinstance(choices, list):
                            content = choices[0].get("message", {}).get("content", "")
                        break  # 成功，跳出重试循环

            except urllib.error.HTTPError as e:
                last_error = e
                if e.code in (429, 502, 503, 504):
                    print(f"API 请求失败 (HTTP {e.code})，尝试重试 {attempt + 1}/3...")
                    continue
                raise
            except urllib.error.URLError as e:
                last_error = e
                print(f"API 请求失败 ({e.reason})，尝试重试 {attempt + 1}/3...")
                continue
            except Exception as e:
                # 捕获 ChunkedEncodingError、IncompleteRead 等
                last_error = e
                print(f"API 请求失败 ({type(e).__name__}: {e})，尝试重试 {attempt + 1}/3...")
                continue
        else:
            raise RuntimeError(f"API 请求在 3 次尝试后仍然失败: {last_error}")

        if not content:
            raise ValueError("API 返回内容为空")

        # 提取 HTML（从流式或非流式结果）
        result = {"choices": [{"message": {"content": content}}]}

            # 安全访问 API 响应
            choices = result.get("choices")
            if not choices or not isinstance(choices, list):
                raise ValueError(f"API 响应缺少 choices 字段: {result.keys()}")
            first_choice = choices[0]
            if not isinstance(first_choice, dict):
                raise ValueError("API 响应 choices[0] 格式异常")
            message = first_choice.get("message", {})
            content = message.get("content", "")
            if not content:
                raise ValueError("API 响应内容为空")

            # 提取 HTML
            match = re.search(r"```html\s*(.*?)```", content, re.DOTALL)
            if match:
                html_content = match.group(1)
            else:
                html_content = content

            # 确保 HTML 包含 AI 来源标注
            if f"由 {ai_name}" not in html_content and "AI 生成" not in html_content:
                # 在 </body> 前添加标注
                ai_footer = f"""
    <div style="text-align: center; margin-top: 40px; padding: 20px; color: #999; font-size: 12px; border-top: 1px solid #eee;">
        本信息图由 {ai_name} AI 生成
    </div>"""
                html_content = html_content.replace("</body>", f"{ai_footer}\n</body>")

            print(f"HTML content length: {len(html_content)}")

            # 保存 HTML
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)

            print(f"HTML saved to: {output_file}")
            print("SUCCESS")
            sys.exit(0)

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

        # 生成错误页面
        error_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>生成错误</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 40px; background: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #e74c3c; }}
        pre {{ background: #f8f9fa; padding: 15px; border-radius: 4px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>生成信息图时出错</h1>
        <p><strong>错误信息：</strong>{str(e)}</p>
        <hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">
        <h3>技术详情：</h3>
        <pre>{str(e)[:300]}</pre>
        <div style="text-align: center; margin-top: 40px; padding: 20px; color: #999; font-size: 12px; border-top: 1px solid #eee;">
            本信息图由 {ai_name} AI 生成（失败）
        </div>
    </div>
</body>
</html>"""

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(error_html)

        sys.exit(1)

if __name__ == "__main__":
    main()
