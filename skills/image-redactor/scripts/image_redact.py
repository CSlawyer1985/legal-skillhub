#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""图片脱敏打码核心工具：文字行定位 + 敏感字段识别 + 黑色矩形打码 + 像素级自验证。
配套 image-redactor skill 使用（~/.workbuddy/skills/image-redactor/）。

本模块与图片类型无关：聊天截图、文档扫描件、网页截图、证件照、表单、代码/密钥
截图、支付凭证等任意含文字的图片均可处理。敏感字段识别支持两种方式：
  1) 语义筛选（AI 读 OCR 结果挑选）——见 SKILL.md 工作流；
  2) 正则自动检测（detect_sensitive）——通用模式匹配，对所有图型都稳。

依赖：PIL / numpy / re（已随常用环境安装；缺则 pip install pillow numpy）
用法示例见 SKILL.md「脚本用法」一节。
"""
import json
import os
import re
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def scan_text_bands(path, dark_threshold=200, min_dark=8, gap=5):
    """扫描图片中的文字带（深色像素密集的 y 连续段）。

    这是「精确定位敏感字段行」的唯一可靠手段——不要用看图工具/预览
    的视觉坐标，渲染有缩放与 padding，与真实像素坐标偏差可达数百像素。

    Args:
        path: 图片路径
        dark_threshold: 灰度低于此值视为深色像素（默认 200）
        min_dark: 一行深色像素超过此数才视为文字行（默认 8）
        gap: 相邻文字行间隔超过此像素才断开（默认 5）

    Returns:
        [(y_start, y_end), ...] 文字带列表
    """
    arr = np.array(Image.open(path).convert("L"))
    dark = (arr < dark_threshold).sum(axis=1)
    text_ys = np.where(dark > min_dark)[0]
    if len(text_ys) == 0:
        return []
    bands = []
    s = text_ys[0]
    p = s
    for y in text_ys[1:]:
        if y - p > gap:
            bands.append((s, p))
            s = y
        p = y
    bands.append((s, p))
    return bands


def redact(path, out, boxes, fill=(20, 20, 20), style="fill"):
    """在指定区域打码，实现脱敏。支持三种样式（借鉴 PII Detection & Masking System）：

    - fill（默认）：实心矩形，最强脱敏，可通过像素级纯黑校验
    - blur：高斯模糊，观感柔和，但属弱脱敏（理论上有被还原风险）
    - pixelate：像素化马赛克，观感复古，同样属弱脱敏

    Args:
        path: 源图片路径
        out: 输出路径
        boxes: [(x1, y1, x2, y2), ...] 矩形列表（可一次多块）
        fill: 填充色，默认近黑 (20,20,20)，仅 fill 样式使用
        style: 打码样式 fill / blur / pixelate

    Returns:
        输出路径
    """
    img = Image.open(path).convert("RGB")
    for box in boxes:
        x1, y1, x2, y2 = (int(v) for v in box)
        if style == "fill":
            ImageDraw.Draw(img).rectangle((x1, y1, x2, y2), fill=fill)
        elif style == "blur":
            region = img.crop((x1, y1, x2, y2)).filter(ImageFilter.GaussianBlur(radius=8))
            img.paste(region, (x1, y1))
        elif style == "pixelate":
            region = img.crop((x1, y1, x2, y2))
            w, h = region.size
            small = region.resize((max(1, w // 10), max(1, h // 10)), Image.NEAREST)
            img.paste(small.resize((w, h), Image.NEAREST), (x1, y1))
        else:
            raise ValueError("style 须为 fill / blur / pixelate")
    img.save(out, optimize=True)  # 重存不回写 EXIF → 输出天然剥离 GPS 等元数据
    return out


def verify_redaction(path, boxes=None, pure_black_max=50, residual_dark=120, min_px=8, style="fill"):
    """像素级自验证打码是否生效。

    Args:
        path: 打码后的图片路径
        boxes: 打码矩形列表（有则逐块验证纯黑）
        pure_black_max: 打码区域灰度上限，低于此值视为已涂黑（默认 50）
        residual_dark: 全图扫描时，灰度低于此值视为深色（默认 120）
        min_px: 一行深色像素超过此数才视为「未打码残留行」（默认 8）
        style: 打码样式；仅 fill 可做纯黑校验，blur/pixelate 跳过该项

    Returns:
        (ok, report): ok=bool（打码区域全部纯黑）；report=str 列表
    """
    arr = np.array(Image.open(path).convert("L"))
    H, W = arr.shape
    report = []
    ok = True

    # 1) 打码区域纯黑验证（仅 fill 样式适用；blur/pixelate 属弱脱敏，无法以纯黑判定）
    if boxes:
        if style != "fill":
            report.append("ℹ️ style=%s：非实心填充，跳过纯黑校验（blur/pixelate 属弱脱敏，对外发布建议用 fill）" % style)
        else:
            for (x1, y1, x2, y2) in boxes:
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                region = arr[y1:y2, x1:x2]
                if region.size == 0:
                    continue
                m = int(region.min())
                if m >= pure_black_max:
                    ok = False
                    report.append(f"⚠️ 区域 ({x1},{y1})-({x2},{y2}) 非纯黑，min={m}")
                else:
                    report.append(f"✓ 区域 ({x1},{y1})-({x2},{y2}) 已涂黑 (min={m})")

    # 2) 全图扫描未打码深色行（提示人工核对是否非敏感结构）
    residual = []
    for y in range(H):
        row = arr[y]
        dc = int((row < residual_dark).sum())
        if dc > min_px and int(row.min()) > pure_black_max:
            residual.append(y)
    if residual:
        shown = residual[:20]
        report.append(
            f"ℹ️ 未涂黑深色行（多为非敏感结构：菜单/tab/标题，需人工确认）: "
            f"{shown}{' ...' if len(residual) > 20 else ''}（共 {len(residual)} 行）"
        )
    return ok, report


# ---------------------------------------------------------------------------
# 通用敏感字段识别（与图片类型无关，基于 OCR 文本正则匹配）
# ---------------------------------------------------------------------------

# 默认敏感字段正则。新增类型只需在此加一行，或调用时传 extra_patterns。
# 数字类均加 (?<!\\d) / (?![\\d\\w]) 边界，避免身份证/银行卡等长数字串内部被误判为手机号。
SENSITIVE_PATTERNS = {
    "phone": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),                       # 手机号（11 位，独立数字串）
    "id_card": re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),                    # 身份证号（18 位）
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "ip": re.compile(r"(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)"),
    "bank_card": re.compile(r"(?<!\d)\d{16,19}(?!\d)"),                      # 银行卡号（16–19 位）
    "wechat_appid": re.compile(r"(?<![\w])wx[0-9a-fA-F]{16}(?![\w])"),       # 微信 AppID
    "wechat_original_id": re.compile(r"(?<![\w])gh_[0-9a-zA-Z]+(?![\w])"),   # 微信原始 ID
    "iban": re.compile(r"(?<![A-Z0-9])[A-Z]{2}\d{2}[A-Z0-9]{11,30}(?![A-Z0-9])"),  # 国际银行账号
}


# ---------------------------------------------------------------------------
# 校验和：降低数字类字段的假阳性（借鉴 ShotShield 的 checksum 思路）
# 仅对"带校验和的类型"生效；无校验和的类型（手机号/邮箱/IP）不参与，避免漏盖。
# ---------------------------------------------------------------------------

def luhn_valid(number):
    """Luhn 算法校验（银行卡/信用卡）。返回 bool。"""
    digits = [int(c) for c in number if c.isdigit()]
    if len(digits) < 12:
        return False
    total = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def iban_valid(iban):
    """IBAN mod-97 校验。返回 bool。"""
    iban = iban.replace(" ", "").upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]+", iban):
        return False
    rearranged = iban[4:] + iban[:4]
    s = "".join(str(ord(c) - 55) if c.isalpha() else c for c in rearranged)
    remainder = 0
    for ch in s:
        remainder = (remainder * 10 + int(ch)) % 97
    return remainder == 1


def cn_id_valid(idnum):
    """中国大陆 18 位身份证号校验码验证。返回 bool。"""
    if not re.fullmatch(r"\d{17}[\dXx]", idnum):
        return False
    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    check_map = "10X98765432"
    total = sum(int(idnum[i]) * weights[i] for i in range(17))
    return check_map[total % 11] == idnum[17].upper()


# 各类型对应的校验函数（None 表示该类型无校验和）
_CHECKSUM_FN = {
    "bank_card": luhn_valid,
    "id_card": cn_id_valid,
    "iban": iban_valid,
}


def validate(label, text):
    """对命中项做校验和验证。无校验和的类型返回 None（不参与过滤）。"""
    fn = _CHECKSUM_FN.get(label)
    if fn is None:
        return None
    try:
        return bool(fn(text))
    except Exception:
        return None


def load_config(path):
    """从 JSON 加载自定义正则规则（Privacy-Mask 风格）。

    JSON 格式：{"rules": [{"name": "MY_ID", "pattern": "CUSTOM-\\d{8}", "flags": ["IGNORECASE"]}, ...]}
    返回 {name: compiled_regex}，可直接作为 detect_sensitive 的 extra_patterns。
    """
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    flag_map = {"IGNORECASE": re.I, "MULTILINE": re.M, "DOTALL": re.S, "VERBOSE": re.X}
    patterns = {}
    for rule in cfg.get("rules", []):
        flags = 0
        for fl in rule.get("flags", []):
            flags |= flag_map.get(str(fl).upper(), 0)
        patterns[rule["name"]] = re.compile(rule["pattern"], flags)
    return patterns


def parse_ocr_line(line):
    """解析 ocr_vision.swift 的一行输出 `conf|text|x y w h` -> (text, (x,y,w,h))。

    OCR 文字本身可能包含 '|'（如微信消息中的分隔符），因此按最后一个 '|'
    切分坐标，中间部分全部视为文字。解析失败（格式不符/缺字段）返回 None。
    """
    line = line.strip()
    if not line:
        return None
    parts = line.split("|")
    if len(parts) < 3:
        return None
    # 格式：conf|text|x y w h；text 中也可能有 |
    text = "|".join(parts[1:-1])
    try:
        x, y, w, h = (float(v) for v in parts[-1].split())
    except ValueError:
        return None
    return (text, (int(round(x)), int(round(y)), int(round(w)), int(round(h))))


def parse_ocr(text):
    """把 ocr_vision.swift 的多行输出解析为 [(text, (x,y,w,h)), ...]。"""
    items = []
    for ln in text.splitlines():
        r = parse_ocr_line(ln)
        if r:
            items.append(r)
    return items


def _char_units(s):
    """按等效西文字宽统计字符串长度：CJK 字符计 2，其余计 1。"""
    return sum(2 if "\u4e00" <= c <= "\u9fff" else 1 for c in s)


def _estimate_sub_box(text, box, sub):
    """根据子串在整行中的字符位置，估算子串的像素 bbox (x, y, w, h)。

    Args:
        text: 整行 OCR 文字
        box: 整行 bbox (x, y, w, h)
        sub: 需要定位的子串（如人名）

    Returns:
        (x, y, w, h) 或 None（子串不存在）
    """
    idx = text.find(sub)
    if idx < 0:
        return None
    x, y, w, h = box
    total = _char_units(text)
    if total == 0:
        return None
    prefix = text[:idx]
    prefix_units = _char_units(prefix)
    sub_units = _char_units(sub)
    x1 = x + (prefix_units / total) * w
    sub_w = (sub_units / total) * w
    return (int(round(x1)), y, int(round(sub_w)), h)


def detect_sensitive(ocr_items, extra_patterns=None, extra_names=None,
                     require_valid=False, config_path=None):
    """从 OCR 结果中自动识别敏感字段（通用，与图片类型无关）。

    先用 SENSITIVE_PATTERNS（或 config_path 指定的自定义规则）做正则匹配，
    再按 extra_names 强制遮盖指定姓名/关键词。数字类字段附带校验和验证
    （银行卡 Luhn / 身份证 cn_id / IBAN mod-97），用于降假阳性。

    Args:
        ocr_items: [(text, (x,y,w,h)), ...]，通常来自 parse_ocr()
        extra_patterns: dict {label: compiled_regex}，自定义补充正则
        extra_names: list[str]，需强制遮盖的姓名/关键词
        require_valid: True 时仅保留通过校验和的命中（无校验和的类型不受影响）；
                      用于 dry-run 后自动降假阳性。默认 False（隐私优先：正则命中即盖）
        config_path: JSON 规则文件路径，加载后并入 patterns（Privacy-Mask 风格）

    Returns:
        [(label, matched_text, (x,y,w,h), valid), ...]
        valid 为 bool（通过校验）/ None（该类型无校验和）
    """
    patterns = dict(SENSITIVE_PATTERNS)
    if config_path:
        patterns.update(load_config(config_path))
    if extra_patterns:
        patterns.update(extra_patterns)

    results = []
    seen = set()  # (label, matched_text, box) 去重
    for text, box in ocr_items:
        claimed = []  # 已认领的字符区间：同串被多标签命中时优先认领
        for label, rx in patterns.items():
            for m in rx.finditer(text):
                s, e = m.span()
                if any(not (e <= cs or s >= ce) for cs, ce in claimed):
                    continue
                claimed.append((s, e))
                key = (label, m.group(), box)
                if key in seen:
                    continue
                seen.add(key)
                valid = validate(label, m.group())
                if require_valid and valid is False:
                    continue
                results.append((label, m.group(), box, valid))
        if extra_names:
            for name in extra_names:
                if not name or name not in text:
                    continue
                # 按节制原则，只覆盖姓名本身，不拉整条文字带
                sub_box = _estimate_sub_box(text, box, name)
                if sub_box is None:
                    continue
                key = ("name", name, sub_box)
                if key not in seen:
                    seen.add(key)
                    results.append(("name", name, sub_box, None))
    return results


def auto_redact(path, out, ocr_items, extra_patterns=None, extra_names=None,
                fill=(20, 20, 20), padding=2, verify=True, require_valid=False,
                dry_run=False, include_faces=False, face_script=None,
                style="fill", **verify_kwargs):
    """端到端：识别 ->（可选人脸检测）-> 打码 ->（可选）像素验证。

    Args:
        path: 源图路径
        out: 输出路径
        ocr_items: parse_ocr() 结果
        extra_patterns / extra_names: 见 detect_sensitive
        fill / padding: 打码颜色与紧贴外扩像素
        style: 打码样式 fill / blur / pixelate（fill 最强、可纯黑校验）
        verify: 是否像素级自验证
        require_valid: 仅保留通过校验和的命中（降假阳性）
        dry_run: True 时只检测不落盘，返回命中供人工复核（Privacy-Mask 风格安全阀）
        include_faces: True 时额外用 Vision 检测人脸并遮盖（弥补"只处理文字"盲区）
        face_script: faces_vision.swift 路径，默认脚本同目录

    Returns:
        (out_or_None, report_list, boxes)
        dry_run 时 out 返回 None（未生成文件）
    """
    hits = detect_sensitive(ocr_items, extra_patterns=extra_patterns,
                            extra_names=extra_names, require_valid=require_valid)
    text_boxes = [(int(x - padding), int(y - padding), int(x + w + padding), int(y + h + padding))
                  for _l, _t, (x, y, w, h), _v in hits]
    face_boxes = []
    if include_faces:
        face_boxes = [(int(fx - padding), int(fy - padding), int(fx + fw + padding), int(fy + fh + padding))
                      for (fx, fy, fw, fh) in detect_faces(path, script_path=face_script)]
    boxes = text_boxes + face_boxes

    report = ["[命中] %d 处敏感字段（文字）：" % len(hits) +
              "，".join("%s=%s%s" % (l, t, "" if v is None else ("✓" if v else "✗"))
                        for l, t, _, v in hits)]
    if include_faces:
        report.append("[人脸] 检测到 %d 张，将一并遮盖" % len(face_boxes))

    if dry_run:
        report.append("[dry-run] 仅检测，未实际打码")
        return None, report, boxes

    redact(path, out, boxes, fill=fill, style=style)
    if verify:
        ok, vrep = verify_redaction(out, boxes=boxes, style=style, **verify_kwargs)
        report.append("[验证] %s" % ("通过" if ok else "未通过"))
        report.extend(vrep)
    return out, report, boxes


# ---------------------------------------------------------------------------
# 人脸检测（弥补"只处理文字"的盲区）：用 macOS Vision 的 VNDetectFaceRectanglesRequest，
# 与 ocr_vision.swift 同源，无需额外 pip 依赖。输出像素坐标 (x,y,w,h)，左上角原点。
# ---------------------------------------------------------------------------

def detect_faces(image_path, script_path=None):
    """用 Vision 人脸检测返回人脸像素 bbox 列表 [(x,y,w,h), ...]。

    依赖 scripts/faces_vision.swift（macOS 内置 Vision 框架）。无脸/不可用时返回 []。
    """
    if script_path is None:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "faces_vision.swift")
    if not os.path.exists(script_path):
        return []
    try:
        proc = subprocess.run(["swift", script_path, image_path],
                              capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return []
    boxes = []
    for ln in proc.stdout.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            x, y, w, h = (int(round(float(v))) for v in ln.split())
        except ValueError:
            continue
        boxes.append((x, y, w, h))
    return boxes


def redact_faces(image_path, out, fill=(20, 20, 20), padding=4,
                 script_path=None, verify=True, **verify_kwargs):
    """检测并遮盖图片中的人脸（证件照/合照场景）。返回 (out, report, boxes)。"""
    boxes = [(int(fx - padding), int(fy - padding), int(fx + fw + padding), int(fy + fh + padding))
             for (fx, fy, fw, fh) in detect_faces(image_path, script_path=script_path)]
    report = ["[人脸] 检测到 %d 张，已遮盖" % len(boxes)]
    if not boxes:
        report.append("[人脸] 未检测到人脸，原图未改动")
        return image_path, report, boxes
    redact(image_path, out, boxes, fill=fill)
    if verify:
        ok, vrep = verify_redaction(out, boxes=boxes, **verify_kwargs)
        report.append("[验证] %s" % ("通过" if ok else "未通过"))
        report.extend(vrep)
    return out, report, boxes


# ---------------------------------------------------------------------------
# 批量处理 / OCR 调用 / 元数据剥离
# ---------------------------------------------------------------------------

def run_ocr(image_path, script_path=None):
    """调用 ocr_vision.swift 对图片做 OCR，返回 parse_ocr 结果。

    batch_redact 内部即用此函数；也可单独调用。swift 不可用时返回 []。
    """
    if script_path is None:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ocr_vision.swift")
    if not os.path.exists(script_path):
        return []
    try:
        proc = subprocess.run(["swift", script_path, image_path],
                              capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.SubprocessError):
        return []
    return parse_ocr(proc.stdout)


def sample_color(path, box=None):
    """取区域内的主色（像素众数），用于「叠加层/遮罩背景下用同色填充」的取色。

    为什么需要：微信/iOS 分享菜单弹出时整屏会压一层半透明遮罩（实测底色恒为
    (127,127,127)）。此处若按惯例打黑块，会在灰底上戳出一个突兀的黑洞；采样底色后
    `redact(..., fill=sample_color(path, box))` 与遮罩同色，敏感文字消失且视觉无缝。
    注意：非黑填充**不能**用 verify_redaction 的纯黑校验，改查「区域灰度恒定
    （min == max == 填充色） + 框外零改动」。

    Args:
        path: 图片路径
        box: 采样区 (x1, y1, x2, y2)，给一块纯遮罩底（不含文字）；None 表示整图

    Returns:
        (r, g, b)
    """
    im = np.array(Image.open(path).convert("RGB"))
    full_h, full_w = im.shape[:2]
    if box:
        x1, y1, x2, y2 = (int(v) for v in box)
        im = im[y1:y2, x1:x2]
    if im.size == 0:
        raise ValueError(f"采样区为空：box={box}，图片尺寸 {full_w}x{full_h}"
                         f"（box 顺序是 x1,y1,x2,y2）")
    colors, counts = np.unique(im.reshape(-1, 3), axis=0, return_counts=True)
    return tuple(int(v) for v in colors[int(np.argmax(counts))])


def strip_exif(path, out=None):
    """剥离图片 EXIF/GPS 等元数据（借鉴 ShotShield 的导出剥离思路）。

    redact()/auto_redact() 的输出本就不回写 EXIF；此函数供"仅去元数据、不打码"场景：
    重建像素后重存，彻底甩掉 EXIF/GPS 等元数据块。返回输出路径。
    """
    if out is None:
        root, ext = os.path.splitext(path)
        out = root + "_noexif" + (ext or ".png")
    img = Image.open(path)
    clean = Image.new(img.mode, img.size)
    clean.putdata(list(img.getdata()))
    clean.save(out)
    return out


def batch_redact(sources, out_dir, ocr_items_map=None, extra_names=None,
                 extra_patterns=None, require_valid=False, include_faces=False,
                 style="fill", fill=(20, 20, 20), padding=2, verify=True,
                 ocr_script=None, face_script=None, log_name="redact-log.json"):
    """批量脱敏 + 输出 JSON 脱敏日志（借鉴 AutoRedact 批量 / Image PII Redactor 日志）。

    Args:
        sources: 图片路径列表，或一个目录（自动收集 png/jpg/jpeg/bmp/tiff/webp）
        out_dir: 输出目录（自动创建），每张写 <原名>_safe.png
        ocr_items_map: {路径: parse_ocr 结果}。传入则跳过 swift OCR
                      （适合已有 OCR 结果或测试；键需与 sources 中的路径一致）
        其余参数同 auto_redact
        log_name: 脱敏日志文件名（JSON：图片/输出/坐标/报告，供审计留痕）

    Returns:
        (results, log_path)：results 为逐图字典列表，log_path 为 JSON 日志路径
    """
    if isinstance(sources, str) and os.path.isdir(sources):
        exts = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp")
        sources = [os.path.join(sources, p) for p in sorted(os.listdir(sources))
                   if p.lower().endswith(exts)]
    elif isinstance(sources, str):
        sources = [sources]
    os.makedirs(out_dir, exist_ok=True)

    results = []
    for src in sources:
        base = os.path.splitext(os.path.basename(src))[0]
        out = os.path.join(out_dir, base + "_safe.png")
        if ocr_items_map and src in ocr_items_map:
            items = ocr_items_map[src]
        else:
            items = run_ocr(src, script_path=ocr_script)
        o, report, boxes = auto_redact(src, out, items,
                                       extra_patterns=extra_patterns,
                                       extra_names=extra_names,
                                       require_valid=require_valid,
                                       include_faces=include_faces,
                                       face_script=face_script,
                                       style=style, fill=fill, padding=padding,
                                       verify=verify)
        results.append({"image": src, "output": o, "boxes": boxes, "report": report})
    log_path = os.path.join(out_dir, log_name)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return results, log_path


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(0)
    src = sys.argv[1]
    print("文字带:", scan_text_bands(src))

# 法律科技实务工具 · 维护者陆凌燕律师（北京德恒·无锡）
