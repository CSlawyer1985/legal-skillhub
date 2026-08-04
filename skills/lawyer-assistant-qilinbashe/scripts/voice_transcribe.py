# -*- coding: utf-8 -*-
"""
voice_transcribe.py —— 录音/语音材料转写工具（轻量版）

用法：
    python voice_transcribe.py <音频文件> [--out 输出.txt] [--whisper]

说明：
    - 有 whisper 环境（openai-whisper / faster-whisper）时自动使用，输出带时间戳转写稿；
    - 无 whisper 时降级输出"转写指引"（提示可用在线工具/人工转写），不报错退出；
    - 纯标准库 + 可选依赖，SkillHub 不携带重型模型文件。

配套技能：agents/108-语音证据处理.md（转写稿 → 合法性审查 → 质证意见）
"""
import os
import sys
import json
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass


def probe_whisper():
    """探测可用的 whisper 实现，返回 (模块名, 调用函数)。"""
    try:
        import whisper  # openai-whisper
        return "openai-whisper", whisper
    except ImportError:
        pass
    try:
        from faster_whisper import WhisperModel  # faster-whisper
        return "faster-whisper", WhisperModel
    except ImportError:
        pass
    return None, None


def transcribe_openai(path):
    import whisper
    model = whisper.load_model("base")  # 轻量模型；可换 small/medium 提升精度
    result = model.transcribe(path, verbose=False)
    lines = []
    for seg in result.get("segments", []):
        start = seg["start"]
        end = seg["end"]
        text = seg["text"].strip()
        if text:
            lines.append("[%02d:%02d-%02d:%02d] %s" % (
                int(start // 60), int(start % 60),
                int(end // 60), int(end % 60), text))
    return "\n".join(lines)


def transcribe_faster(path):
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _info = model.transcribe(path, beam_size=5)
    lines = []
    for seg in segments:
        text = seg.text.strip()
        if text:
            lines.append("[%02d:%02d-%02d:%02d] %s" % (
                int(seg.start // 60), int(seg.start % 60),
                int(seg.end // 60), int(seg.end % 60), text))
    return "\n".join(lines)


def fallback_guide(path):
    return (
        "# 转写指引（未检测到 whisper 环境）\n"
        "\n"
        "音频文件: %s\n"
        "本机未安装 openai-whisper / faster-whisper，未自动转写。可选方案：\n"
        "1. 安装：pip install faster-whisper （约需下载模型，首次运行较慢）\n"
        "2. 或使用在线转写工具导出文字后，粘贴给 108-语音证据处理 做审查分析\n"
        "3. 或人工逐段转述录音内容（标注时间点），供证据分析使用\n"
        "\n"
        "⚠️ 转写稿仅供分析，关键内容务必人工核对原始录音。\n"
    ) % path


def main():
    if len(sys.argv) < 2:
        print("用法: python voice_transcribe.py <音频文件> [--out 输出.txt]")
        sys.exit(1)

    audio = sys.argv[1]
    out_path = None
    if "--out" in sys.argv:
        idx = sys.argv.index("--out")
        if idx + 1 < len(sys.argv):
            out_path = sys.argv[idx + 1]

    if not os.path.exists(audio):
        print("❌ 文件不存在: %s" % audio)
        sys.exit(1)

    print("音频文件: %s (%d KB)" % (audio, os.path.getsize(audio) // 1024))
    backend, _mod = probe_whisper()

    if backend == "openai-whisper":
        print("后端: openai-whisper（转写中，长音频可能耗时…）")
        result = transcribe_openai(audio)
    elif backend == "faster-whisper":
        print("后端: faster-whisper（转写中…）")
        result = transcribe_faster(audio)
    else:
        result = fallback_guide(audio)
        backend = "降级-无whisper"

    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result)
        print("✅ 已保存: %s" % out_path)
    else:
        print(result)

    print("\n[voice_transcribe] 后端=%s 完成" % backend)


if __name__ == "__main__":
    main()
