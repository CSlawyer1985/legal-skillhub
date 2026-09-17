# -*- coding: utf-8 -*-
"""
transcribe_audio.py — 录音转写（阶段2 录音通道）完整实现

引擎: faster-whisper (SYSTRAN, MIT) + OpenAI Whisper small 模型
安全: 100% 本地离线推理，数据不出律所电脑
下载: 通过 hf-mirror.com 国内镜像拉取模型（避免 HuggingFace 直连被墙）

四段式输出:
  1. full_text       — 完整转写文本（供 AI 语义抽取）
  2. segments        — 带时间轴的逐段文本（供回听核对）
  3. low_confidence   — 低置信度片段汇总（进确认表「待复核」）
  4. stats           — 转写统计（时长/置信度均值/模型信息）

置信度规则（与 extract_case 三档对齐，已针对中文电话录音校准）:
  >= 0.5   绿色，直接采信
  0.3~0.5  黄色，采信但建议回听核对 ⚠️
  < 0.3    红色，列入 low_confidence，必须人工核对

映射公式: confidence = clamp((avg_logprob + 0.50) / 0.55, 0, 1)
  avg_logprob ≈ -0.2 → 置信度 0.55（small 模型高质量段落）
  avg_logprob ≈ -0.35 → 置信度 0.27（口音/噪音干扰，须复核）
  理由: 中文电话录音 avg_logprob 常见范围 -0.5~-0.1，旧公式 (raw+1.5)/2
        将正常段落映射到 0.6 附近导致大量假阳性低置信警告

用法:
  # 基本转写
  python transcribe_audio.py <录音.mp3>

  # 指定模型和输出格式
  python transcribe_audio.py <录音.m4a> --model small --out result.json --format json

  # 只用 tiny 模型快速测试
  python transcribe_audio.py <录音.wav> --model tiny --out quick.txt --format text

模型文件存放: ~/ai-models/ （首次运行自动下载 ~2.4GB，仅一次，可自行修改路径）
"""
import os
import sys
import json
import argparse
from pathlib import Path
from datetime import timedelta

# 国内镜像——避免 HuggingFace 直连被墙（仅影响首次下载，后续本地加载无网络依赖）
HF_MIRROR = "https://hf-mirror.com"

# 下载源列表（按顺序 fallback）——hf-mirror 不可达时回退魔搭 modelscope
# 下载的是开源通用模型权重（MIT 协议），不含任何客户数据；录音隐私由本地离线推理保证，与下载源无关
MODEL_SOURCES = [
    {"name": "hf-mirror", "repo": "Systran/faster-whisper-{size}",
     "list_api": "https://hf-mirror.com/api/models/{repo}",
     "download": "https://hf-mirror.com/{repo}/resolve/main/{file}", "kind": "hf"},
    {"name": "modelscope", "repo": "pengzhendong/faster-whisper-{size}",
     "list_api": "https://www.modelscope.cn/api/v1/models/{repo}/repo/files?Revision=master&Recursive=true",
     "download": "https://www.modelscope.cn/models/{repo}/resolve/master/{file}", "kind": "ms"},
]

# 本地模型路径（优先本地加载，不存在时从镜像下载）
LOCAL_MODELS = {
    "tiny": str(Path.home() / ".cache/whisper-models/faster-whisper-tiny"),
    "small": str(Path.home() / ".cache/whisper-models/faster-whisper-small"),
    "base": str(Path.home() / ".cache/whisper-models/faster-whisper-base"),
    "medium": str(Path.home() / ".cache/whisper-models/faster-whisper-medium"),
}

_model_sizes = {
    "tiny": "~75MB",
    "base": "~150MB",
    "small": "~2.4GB",
    "medium": "~5GB",
}


def _list_files(src, repo):
    """从下载源列文件清单，返回 [(文件名, sha256或None)]。"""
    import requests
    r = requests.get(src["list_api"].format(repo=repo), timeout=20)
    r.raise_for_status()
    data = r.json()
    files = []
    if src["kind"] == "hf":
        for s in data.get("siblings", []):
            fn = s["rfilename"]
            if not fn.startswith(".") and fn != "README.md":
                files.append((fn, None))
    else:  # modelscope
        for s in data.get("Data", {}).get("Files", []):
            fn = s.get("Path", "")
            if not fn or fn.startswith(".") or fn == "README.md":
                continue
            files.append((fn, s.get("Sha256")))
    return files


def _sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _download_from_source(src, repo, local):
    """从单个源下载模型（含哈希校验，源提供哈希时）。失败抛异常。"""
    import requests
    files = _list_files(src, repo)
    for fname, expected_sha in files:
        flocal = local / fname
        if flocal.exists():
            continue
        url = src["download"].format(repo=repo, file=fname)
        print(f"  [{src['name']} 下载] {fname} ...", end=" ", flush=True)
        resp = requests.get(url, stream=True, timeout=300)
        resp.raise_for_status()
        with open(flocal, "wb") as f:
            for chunk in resp.iter_content(65536):
                f.write(chunk)
        size_mb = flocal.stat().st_size / (1024 * 1024)
        if expected_sha:
            if _sha256(flocal) != expected_sha.lower():
                flocal.unlink()  # 删坏文件，触发换源
                raise RuntimeError(f"sha256 校验失败: {fname}")
            print(f"{size_mb:.0f}MB (sha256 校验通过)")
        else:
            print(f"{size_mb:.0f}MB")


def ensure_model_local(model_size):
    """确保模型文件存在本地；不存在则从多源 fallback 下载（hf-mirror → modelscope）。"""
    local = Path(LOCAL_MODELS.get(model_size, model_size))

    # 如果已是目录路径（不是 model_size 字符串），直接用
    if local.is_dir():
        if not (local / "model.bin").exists():
            raise FileNotFoundError(f"模型目录存在但无 model.bin: {local}")
        return str(local)

    # 否则作为 model_size，从多源下载
    local = Path.home() / ".cache" / "whisper-models" / f"faster-whisper-{model_size}"
    local.mkdir(parents=True, exist_ok=True)

    errors = []
    for src in MODEL_SOURCES:
        repo = src["repo"].format(size=model_size)
        try:
            _download_from_source(src, repo, local)
        except Exception as e:
            errors.append(f"{src['name']}: {e}")
            print(f"  [!] 源 {src['name']} 下载失败（{e}），尝试下一源...")
            continue
        break  # 成功
    else:
        raise RuntimeError("所有下载源均失败: " + " | ".join(errors))

    if not (local / "model.bin").exists():
        raise RuntimeError(f"模型下载失败: {local} 中无 model.bin")
    return str(local)

MODEL_ROOT = Path.home() / ".cache/whisper-models"
SUPPORTED_FORMATS = {".mp3", ".m4a", ".wav", ".ogg", ".flac", ".aac", ".wma", ".opus", ".webm"}


def fmt_ts(seconds):
    """秒数 → HH:MM:SS.m 格式（回听时间戳）。"""
    td = timedelta(seconds=seconds)
    total = int(td.total_seconds())
    h, r = divmod(total, 3600)
    m, s = divmod(r, 60)
    ms = int((seconds - int(seconds)) * 10)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms}"


def load_model(model_size="small"):
    """加载 faster-whisper 模型（CPU, INT8 量化）。本地已有则直接加载，否则从镜像 HTTP 下载。"""
    from faster_whisper import WhisperModel

    model_path = ensure_model_local(model_size)
    print(f"[模型] 加载 {model_size} 模型 ({model_path})")

    model = WhisperModel(
        model_path,
        device="cpu",
        compute_type="int8",
        num_workers=2,
    )
    return model


def transcribe(audio_path, model_size="small"):
    """
    转写主函数。
    返回:
      {
        "full_text": "完整转写文本...",
        "segments": [{"start": "00:00:00.0", "end": "00:00:03.2", "text": "...", "confidence": 0.92}],
        "low_confidence_ranges": [...],
        "stats": {"duration_seconds": 123, "avg_confidence": 0.88, "model": "small", "segments": 15}
      }
    """
    p = Path(audio_path)
    if not p.exists():
        raise FileNotFoundError(f"录音文件不存在: {audio_path}")
    if p.suffix.lower() not in SUPPORTED_FORMATS:
        print(f"[!] 未列在支持格式中: {p.suffix}，尝试转写（faster-whisper 通常能处理常见音频格式）")

    model = load_model(model_size)
    print(f"[转写] 开始处理: {p.name}")

    segments_out, generated = model.transcribe(str(p), language="zh", beam_size=5)
    segments = list(segments_out)  # 消费生成器
    info = generated

    # 组装输出
    all_text = []
    seg_list = []
    low_list = []
    confidences = []

    for seg in segments:
        ts_start = fmt_ts(seg.start)
        ts_end = fmt_ts(seg.end)
        raw = seg.avg_logprob

        # 将 avg_logprob 映射为 0~1 置信度
        # 针对中文法律电话录音校准：avg_logprob 常见范围 -0.5 ~ -0.1
        # -0.2 → 0.55（绿色）| -0.3 → 0.36（黄色）| -0.35 → 0.27（红色）
        confidence = max(0, min(1, (raw + 0.50) / 0.55))
        confidences.append(confidence)

        seg_item = {
            "start": ts_start,
            "end": ts_end,
            "text": seg.text.strip(),
            "confidence": round(confidence, 3),
        }
        seg_list.append(seg_item)
        all_text.append(seg.text.strip())

        if confidence < 0.3:
            low_list.append({
                "start": ts_start,
                "end": ts_end,
                "text": seg.text.strip(),
                "confidence": round(confidence, 3),
                "raw_logprob": round(raw, 3),
            })

    duration = info.duration if hasattr(info, 'duration') else segments[-1].end if segments else 0
    avg_conf = sum(confidences) / len(confidences) if confidences else 0

    stats = {
        "duration_seconds": round(duration, 1),
        "segments": len(segments),
        "avg_confidence": round(avg_conf, 3),
        "model": model_size,
        "engine": "faster-whisper (SYSTRAN, MIT) + OpenAI Whisper",
    }

    result = {
        "full_text": "".join(all_text),
        "segments": seg_list,
        "low_confidence_ranges": low_list,
        "stats": stats,
    }
    return result


def main():
    ap = argparse.ArgumentParser(description="录音转写 · faster-whisper 本地离线引擎")
    ap.add_argument("audio", help="录音文件路径 (mp3/m4a/wav/ogg/flac/aac)")
    ap.add_argument("--model", default="small", choices=["tiny", "base", "small", "medium"],
                    help="模型大小 (默认 small，中文推荐)")
    ap.add_argument("--out", default=None, help="输出文件路径（默认打印到控制台）")
    ap.add_argument("--format", default="auto", choices=["auto", "json", "text"],
                    help="输出格式: json=完整结构化 / text=纯文本 (auto 按 --out 后缀推断)")
    args = ap.parse_args()

    result = transcribe(args.audio, args.model)
    stats = result["stats"]

    # 输出格式
    out_fmt = args.format
    if out_fmt == "auto":
        out_fmt = "json" if (args.out and args.out.endswith(".json")) else "text"

    if out_fmt == "json":
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        output = result["full_text"]

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"[完成] 转写输出 → {args.out}")
    else:
        print(output)

    # 元信息
    print(f"\n[统计] 时长 {stats['duration_seconds']}s | 段落数 {stats['segments']} | 均置信度 {stats['avg_confidence']}")
    low = len(result["low_confidence_ranges"])
    if low:
        print(f"[警告] {low} 个段落置信度低于 0.3，必须人工核对（见 low_confidence_ranges）")
    else:
        print("[通过] 无低置信度段落")


if __name__ == "__main__":
    main()
