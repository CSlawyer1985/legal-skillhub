#!/usr/bin/env python3
"""
法院文书照片 OCR + 结构解析脚本
双级 OCR 策略：Tesseract（本地轻量）→ MinerU（云端高精度）。
每级结果经质量门控判断是否「可接受」，通过则停止，不通过则降级到下一级。

用法:
  python3 court_photo_ocr.py <image_path>
  python3 court_photo_ocr.py --text "手动输入文本..."
  python3 court_photo_ocr.py --ocr-tier <tesseract|mineru> <image_path>

依赖（按需安装）:
  Tier 1: tesseract + chi_sim (brew install tesseract tesseract-lang)
  Tier 2: mineru-open-api (npm install -g mineru-open-api)
"""

import sys
import os
import re
import json
import subprocess
import shutil
import tempfile
from pathlib import Path

# 图片预处理依赖（Tier 1 增强）
try:
    from PIL import Image, ImageEnhance
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False


# ============================================================
#  质量门控 — 判断 OCR 结果是否「可接受」
# ============================================================

# 法院文书关键字（只要命中一个即加 15 分）
_COURT_DOC_KEYWORDS = [
    '判决书', '裁定书', '传票', '起诉状', '答辩状',
    '应诉通知书', '出庭通知书', '举证通知书', '受理通知书',
    '上诉须知', '人民法院', '开庭', '案号', '案由',
    '原告', '被告', '申请人', '被申请人',
]


def ocr_quality_score(text):
    """
    对 OCR 输出文本打分（0-100），判断是否可直接用于后续解析。
    阈值：>= 50 分视为「可接受」，停止降级。

    打分规则（第一性原理——法院文书 OCR 需要什么）:
      - 有足够中文字符（>=10个，且占比>=20%）+30  （法院文书主体是中文）
      - 长度 > 50 字符       +20  （太短可能是碎片/失败）
      - 长度 > 200 字符      +20  （足够长说明覆盖了大部分内容）
      - 可提取案号            +15  （核心字段，说明 OCR 质量好）
      - 命中法院文书关键字    +15  （说明确实是法院文书）
    """
    if not text or not text.strip():
        return 0

    score = 0
    stripped = text.strip()
    total_len = len(stripped)

    # 1. 是否有足够中文字符（CJK Unified Ideographs + 中文标点）
    cjk_chars = re.findall(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', stripped)
    cjk_count = len(cjk_chars)
    # 排除垃圾输出：中文字符太少（<10个）或占比太低（<20%）→ 不给分
    cjk_ratio = cjk_count / max(total_len, 1)
    if cjk_count >= 10 and cjk_ratio >= 0.20:
        score += 30

    # 2. 文本长度
    if total_len > 50:
        score += 20
    if total_len > 200:
        score += 20

    # 3. 是否可提取案号
    if re.search(r'[（(]\s*\d{4}\s*[）)]\s*[^号]*?\d+号', stripped):
        score += 15

    # 4. 是否命中法院文书关键字
    keyword_hits = sum(1 for kw in _COURT_DOC_KEYWORDS if kw in stripped)
    if keyword_hits >= 1:
        score += min(keyword_hits * 5, 15)  # 最多 15 分

    return score


def ocr_acceptable(text):
    """OCR 结果是否满足最低质量要求"""
    return ocr_quality_score(text) >= 50


# ============================================================
#  图片校验与预处理
# ============================================================

# 支持的图片格式
_SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}
# 最大文件大小（20MB，超过可能是原始相机 RAW 或误传）
_MAX_FILE_SIZE = 20 * 1024 * 1024


def validate_image(image_path):
    """
    校验图片是否适合 OCR 处理。
    返回 (ok: bool, reason: str)。
    """
    if not os.path.isfile(image_path):
        return False, f"文件不存在: {image_path}"

    path = Path(image_path)
    ext = path.suffix.lower()
    if ext not in _SUPPORTED_FORMATS:
        return False, f"不支持的图片格式: {ext}，支持: {', '.join(sorted(_SUPPORTED_FORMATS))}"

    size = os.path.getsize(image_path)
    if size > _MAX_FILE_SIZE:
        return False, f"文件过大: {size / 1024 / 1024:.1f}MB（上限 {_MAX_FILE_SIZE / 1024 / 1024:.0f}MB）"

    if size < 100:
        return False, "文件过小，可能不是有效图片"

    return True, "ok"


def preprocess_for_ocr(image_path):
    """
    Tesseract 图片预处理：灰度化 + 对比度增强。
    对手机拍摄的法院文书照片效果显著——消除阴影、锐化文字边缘。

    返回预处理后的临时文件路径，或原路径（PIL 不可用时）。
    调用方负责清理临时文件。
    """
    if not _HAS_PIL:
        return image_path

    try:
        img = Image.open(image_path)

        # 超大图片缩放到合理尺寸（避免 Tesseract 处理 4000px+ 原图耗时过长）
        w, h = img.size
        max_dim = 3000
        if w > max_dim or h > max_dim:
            ratio = max_dim / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

        # 转灰度
        if img.mode != 'L':
            img = img.convert('L')

        # 对比度增强（1.5x），让文字更锐利
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)

        # 保存到临时文件
        tmp = tempfile.NamedTemporaryFile(suffix='.png', prefix='court_pre_', delete=False)
        tmp_path = tmp.name
        tmp.close()
        img.save(tmp_path, 'PNG')

        print(f"  🖼️  预处理: {w}x{h} → {img.size[0]}x{img.size[1]} 灰度+对比度增强", file=sys.stderr)
        return tmp_path

    except Exception as e:
        print(f"  ⚠️  图片预处理失败 ({e})，使用原图", file=sys.stderr)
        return image_path


# ============================================================
#  Tier 1 — Tesseract（本地轻量 OCR）
# ============================================================

def _has_tesseract():
    return subprocess.run(['which', 'tesseract'], capture_output=True).returncode == 0


def _check_tesseract_chinese():
    """检查 tesseract 是否有中文语言包"""
    r = subprocess.run(['tesseract', '--list-langs'], capture_output=True, text=True)
    return 'chi_sim' in r.stdout


def run_tesseract_ocr(image_path):
    """
    Tesseract 简体中文 OCR。
    快、免费、本地、零网络依赖。适合清晰打印文书。
    自动对图片做灰度化+对比度增强预处理，提升模糊照片成功率。
    返回 (text, quality_score) 或 (None, 0)。
    """
    if not _has_tesseract():
        print("⚠️  Tier 1: tesseract 未安装，跳过", file=sys.stderr)
        print("   安装: brew install tesseract tesseract-lang", file=sys.stderr)
        return None, 0

    if not _check_tesseract_chinese():
        print("⚠️  Tier 1: tesseract 缺少 chi_sim 语言包，跳过", file=sys.stderr)
        print("   安装: brew install tesseract-lang", file=sys.stderr)
        return None, 0

    print("🔍 Tier 1: Tesseract (chi_sim) ...", file=sys.stderr)

    # 图片预处理（灰度+增强对比度）
    preprocessed = preprocess_for_ocr(image_path)
    is_temp = preprocessed != image_path

    try:
        # 使用工作目录作为 tesseract 输出目录（避免 /tmp 沙箱隔离问题）
        tmp_dir = tempfile.mkdtemp(prefix='court_tess_',
                                    dir=os.path.dirname(image_path) if os.path.isdir(os.path.dirname(image_path)) else None)
        out_base = os.path.join(tmp_dir, 'tess_output')

        result = subprocess.run(
            ['tesseract', preprocessed, out_base, '-l', 'chi_sim'],
            capture_output=True, text=True, timeout=60
        )

        out_txt = out_base + '.txt'
        if os.path.exists(out_txt):
            with open(out_txt, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read().strip()
        else:
            text = ''

        # 清理
        try:
            shutil.rmtree(tmp_dir)
        except OSError:
            pass

        if not text:
            print("  ❌ Tesseract 无输出", file=sys.stderr)
            return None, 0

        score = ocr_quality_score(text)
        if ocr_acceptable(text):
            print(f"  ✅ Tesseract 质量分 {score}/100，通过", file=sys.stderr)
            return text, score
        else:
            print(f"  ⚠️  Tesseract 质量分 {score}/100，未达阈值(50)，降级", file=sys.stderr)
            return text, score

    except subprocess.TimeoutExpired:
        print("  ❌ Tesseract 超时", file=sys.stderr)
        return None, 0
    except Exception as e:
        print(f"  ❌ Tesseract 异常: {e}", file=sys.stderr)
        return None, 0
    finally:
        if is_temp and os.path.exists(preprocessed):
            try:
                os.unlink(preprocessed)
            except OSError:
                pass


# ============================================================
#  Tier 2 — MinerU（云端高精度 OCR）
# ============================================================

def _has_mineru():
    return subprocess.run(['which', 'mineru-open-api'], capture_output=True).returncode == 0


def _install_mineru():
    """自动安装 mineru-open-api（需用户确认，非静默下载）"""
    print("", file=sys.stderr)
    print("📦 Tier 2 需要 mineru-open-api（约 30MB，首次安装）。", file=sys.stderr)
    print("   正在安装...", file=sys.stderr)
    r = subprocess.run(['npm', 'install', '-g', 'mineru-open-api'],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        print(f"❌ MinerU 安装失败: {r.stderr[:200]}", file=sys.stderr)
        print("   请手动运行: npm install -g mineru-open-api", file=sys.stderr)
        return False
    print("✅ MinerU 安装完成", file=sys.stderr)
    return True


def run_mineru_ocr(image_path):
    """
    MinerU flash-extract 云端 OCR。
    高精度，适合复杂排版、手写体混排的法院文书。
    需要网络连接。Tier 1 失败后自动尝试。
    返回 (text, quality_score) 或 (None, 0)。
    """
    if not _has_mineru():
        print("⚠️  Tier 2: mineru-open-api 未安装，尝试自动安装...", file=sys.stderr)
        if not _install_mineru():
            return None, 0

    print("🔍 Tier 2: MinerU (flash-extract) ...", file=sys.stderr)

    try:
        result = subprocess.run(
            ['mineru-open-api', 'flash-extract', image_path],
            capture_output=True, text=True, timeout=120
        )

        if result.returncode != 0:
            stderr_text = result.stderr[:300]
            # 区分错误类型
            if 'ECONNREFUSED' in stderr_text or 'ENOTFOUND' in stderr_text or 'getaddrinfo' in stderr_text:
                print(f"  ❌ MinerU 网络不可达，请检查网络连接", file=sys.stderr)
            elif '401' in stderr_text or '403' in stderr_text or 'unauthorized' in stderr_text.lower():
                print(f"  ❌ MinerU API 认证失败，请检查 API Key", file=sys.stderr)
            elif 'timeout' in stderr_text.lower() or 'ETIMEDOUT' in stderr_text:
                print(f"  ❌ MinerU 请求超时，服务器可能繁忙", file=sys.stderr)
            else:
                print(f"  ❌ MinerU 提取失败: {stderr_text}", file=sys.stderr)
            return None, 0

        text = result.stdout.strip()
        if not text or len(text) < 10:
            print("  ❌ MinerU 结果为空或过短", file=sys.stderr)
            return None, 0

        score = ocr_quality_score(text)
        if ocr_acceptable(text):
            print(f"  ✅ MinerU 质量分 {score}/100，通过", file=sys.stderr)
            return text, score
        else:
            print(f"  ⚠️  MinerU 质量分 {score}/100，未达阈值(50)", file=sys.stderr)
            return text, score

    except subprocess.TimeoutExpired:
        print("  ❌ MinerU 超时（网络慢或服务器无响应）", file=sys.stderr)
        return None, 0
    except Exception as e:
        err_msg = str(e)
        if 'timeout' in err_msg.lower() or 'timed out' in err_msg.lower():
            print(f"  ❌ MinerU 网络超时，请检查网络连接", file=sys.stderr)
        else:
            print(f"  ❌ MinerU 异常: {err_msg[:200]}", file=sys.stderr)
        return None, 0


# ============================================================
#  双级 OCR 编排器 — 核心入口
# ============================================================

def run_ocr_tiered(image_path, force_tier=None):
    """
    双级降级 OCR 主入口。

    策略（第一性原理）:
      Tier 1 (Tesseract)     → 本地/轻量/零成本，适合清晰打印件
                                  自动灰度+对比度增强预处理
      Tier 2 (MinerU)        → 云端/高精度，适合复杂排版/模糊照片

    每级结果经质量门控（ocr_acceptable）判断，>=50 分即停止降级。
    双级全部失败 → 返回最佳结果（最高分）+ 降级标记。

    返回 (text, metadata_dict)
      metadata: { tier, quality_score, acceptable, tiers_tried }
    """
    tiers = [
        ('tesseract', run_tesseract_ocr, 'Tesseract'),
        ('mineru', run_mineru_ocr, 'MinerU'),
    ]

    # 强制指定某级（调试/手动指定用）
    if force_tier:
        tiers = [(t[0], t[1], t[2]) for t in tiers if t[0] == force_tier]
        if not tiers:
            print(f"❌ 无效的 OCR 层级: {force_tier}", file=sys.stderr)
            print(f"   可选: tesseract, mineru", file=sys.stderr)
            return None, {'tier': None, 'quality_score': 0, 'acceptable': False, 'tiers_tried': []}

    best_text = None
    best_score = 0
    best_tier = None
    tiers_tried = []

    for tier_id, ocr_func, tier_name in tiers:
        tiers_tried.append(tier_id)
        text, score = ocr_func(image_path)

        if text and score > best_score:
            best_text = text
            best_score = score
            best_tier = tier_id

        if ocr_acceptable(text):
            # 质量达标，停止降级
            return text, {
                'tier': tier_id,
                'quality_score': score,
                'acceptable': True,
                'tiers_tried': tiers_tried,
            }

    # 全部未达标 → 返回最高分结果 + 降级标记
    if best_text:
        print(f"\n⚠️  双级 OCR 均未达质量阈值。", file=sys.stderr)
        print(f"   最佳: {best_tier} (质量分 {best_score}/100)", file=sys.stderr)
        print(f"   结果可能不完整，请人工核对。", file=sys.stderr)
        _suggest_paddleocr()
        return best_text, {
            'tier': best_tier,
            'quality_score': best_score,
            'acceptable': False,
            'tiers_tried': tiers_tried,
        }

    print(f"\n❌ 双级 OCR 全部失败", file=sys.stderr)
    print(f"   💡 建议: 确认图片清晰、光线充足，或手动输入文本。", file=sys.stderr)
    _suggest_paddleocr()
    return None, {
        'tier': None,
        'quality_score': 0,
        'acceptable': False,
        'tiers_tried': tiers_tried,
    }


def _suggest_paddleocr():
    """双级失败后，向用户建议 PaddleOCR 作为额外选项（不自动安装）。"""
    print("", file=sys.stderr)
    print("   ─────────────────────────────────────────────", file=sys.stderr)
    print("   💡 如需更强的中文 OCR（约 500MB 磁盘空间）：", file=sys.stderr)
    print("      pip install paddlepaddle paddleocr", file=sys.stderr)
    print("      安装后无需任何配置，下次 OCR 会自动使用。", file=sys.stderr)
    print("      PaddleOCR 中文法院文书场景精度最高，且无需网络。", file=sys.stderr)
    print("   ─────────────────────────────────────────────", file=sys.stderr)


# ============================================================
#  兼容层 — 保留旧 run_ocr 接口
# ============================================================

def run_ocr(image_path):
    """
    旧接口兼容：直接调用双级 OCR 编排器。
    行为与之前 run_ocr(image_path) 一致——返回纯文本或 None。
    """
    text, meta = run_ocr_tiered(image_path)
    return text


# ============================================================
#  文本解析
# ============================================================

def parse_court_text(text):
    """从法院文书 OCR 文本提取结构化信息，含置信度标记"""
    if not text or not text.strip():
        return {"error": "文本为空", "document_type": "未知",
                "confidence": {}, "review_required": True}

    confidence = {}
    result = {
        "document_type": "未知", "case_no": None, "case_type": None,
        "parties": {}, "court_name": None, "hearing_time": None,
        "hearing_location": None, "judge_name": None,
        "appeal_deadline_days": None,
        "confidence": confidence, "review_required": False,
    }

    # 1. 文书类型
    if re.search(r'(?:应到时间|应到处所)', text):
        result['document_type'] = '传票'
        confidence['document_type'] = 'high'
    else:
        types = [
            ('判决书', ['判决书', '民事判决书', '刑事判决书', '行政判决书']),
            ('裁定书', ['裁定书', '民事裁定书', '刑事裁定书']),
            ('应诉通知书', ['应诉通知书', '应诉通知']),
            ('出庭通知书', ['出庭通知书', '出庭通知']),
            ('起诉状', ['起诉状', '民事起诉状', '刑事自诉状']),
            ('上诉须知', ['上诉须知']),
            ('举证通知书', ['举证通知书', '举证通知']),
        ]
        found = False
        for dtype, keywords in types:
            for kw in keywords:
                if kw in text:
                    result['document_type'] = dtype; found = True; break
            if found: break
        confidence['document_type'] = 'high' if found else 'low'

    # 2. 案号（关键，标记复核）
    case_m = re.search(r'[（(]\s*(\d{4})\s*[）)]\s*[^号]*?\d+号', text)
    if case_m:
        result['case_no'] = case_m.group(0).strip().replace(' ', '')
        confidence['case_no'] = 'high'
    else:
        confidence['case_no'] = 'low'; result['review_required'] = True

    # 3. 案由
    m = re.search(r'案\s*由[：:]\s*(.+?)(?:\n|$)', text)
    if not m:
        m = re.search(r'([\u4e00-\u9fff]{2,20}(?:纠纷|争议|赔偿|确认|变更|履行|解除)(?:一案)?)', text)
    if m:
        result['case_type'] = m.group(1).strip().rstrip('一案')
        confidence['case_type'] = 'high'
    else:
        confidence['case_type'] = 'low'

    # 4. 法院
    m = re.search(r'([\u4e00-\u9fff]{2,10}?(?:省|市|县|区))?\s*([\u4e00-\u9fff]{2,12}?(?:人民法院|中级法院))', text)
    if m:
        result['court_name'] = m.group(0).strip(); confidence['court_name'] = 'high'
    elif '人民法院' in text:
        idx = text.index('人民法院')
        result['court_name'] = text[max(0,idx-20):idx+5].replace('\n',' ').strip()
        confidence['court_name'] = 'medium'
    else:
        confidence['court_name'] = 'low'

    # 5. 当事人
    parties_found = False
    for role, prefix in [
        ('plaintiff','原告'),('defendant','被告'),('applicant','申请人'),
        ('respondent','被申请人'),('appellant','上诉人'),('appellee','被上诉人'),
        ('defendant_criminal','被告人'),('prosecutor','公诉机关'),
    ]:
        m = re.search(rf'{prefix}[：:]\s*(.+?)(?:\n|，|。|$)', text)
        if m:
            p = m.group(1).strip().rstrip('，。')
            p = re.sub(r'(?:公民身份号码|身份证号)\s*\d{15,18}[0-9Xx]','',p)
            p = re.sub(r'\d{15,18}[0-9Xx]','',p)
            p = re.sub(r'住\s*.+','',p).strip()
            result['parties'][role] = p; parties_found = True
    has_noise = any(re.search(r'\d{5,}',v) for v in result['parties'].values())
    confidence['parties'] = 'medium' if parties_found and not has_noise else ('low' if not parties_found else 'medium')
    if confidence['parties'] == 'low' or has_noise:
        result['review_required'] = True

    # 6. 开庭时间（关键，永远标记复核）
    found = False
    for pat in [
        r'应到时间[：:]\s*(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日.{0,10}?(\d{1,2})[：:](\d{2})',
        r'开庭时间[：:]\s*(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日.{0,10}?(\d{1,2})[：:](\d{2})',
        r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日\s*(?:上午|下午)?\s*(\d{1,2})[：:](\d{2})',
        r'定于\s*(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日\s*(?:上午|下午)?\s*(\d{1,2})[：:]\s*(\d{2})',
        r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日\s*(?:上午|下午)?\s*(\d{1,2})\s*时',
    ]:
        m = re.search(pat, text)
        if m:
            g = m.groups()
            y,mo,d = g[0],g[1],g[2]
            h,mi = g[3], g[4] if len(g)>=5 else '00'
            result['hearing_time'] = f"{y}-{mo.zfill(2)}-{d.zfill(2)} {h.zfill(2)}:{mi.zfill(2)}"
            found = True; break
    confidence['hearing_time'] = 'high' if found else 'low'
    result['review_required'] = True  # 永远复核

    # 7. 地点
    found = False
    for pat in [r'应到处所[：:]\s*(.+?)(?:\n|$)', r'开庭地点[：:]\s*(.+?)(?:\n|$)',
                r'地点[：:]\s*(.+?法庭)', r'(第\s*\d+\s*法庭)']:
        m = re.search(pat, text)
        if m:
            result['hearing_location'] = m.group(1).strip() if m.lastindex else m.group(0).strip()
            found = True; break
    confidence['hearing_location'] = 'high' if found else 'low'

    # 8. 法官
    m = re.search(r'(?:审判[员长]|审判员|审判长|承办法官)\s*[：:]?\s*([\u4e00-\u9fff]{2,4})', text)
    if m:
        result['judge_name'] = m.group(1).strip(); confidence['judge_name'] = 'high'
    else:
        confidence['judge_name'] = 'low'

    # 9. 上诉期限
    m = re.search(r'(?:送达之日|判决书送达|收到.*判决书).*?起\s*(\d+)\s*[日内天]', text)
    if m:
        result['appeal_deadline_days'] = int(m.group(1))
        confidence['appeal_deadline_days'] = 'high'
    else:
        confidence['appeal_deadline_days'] = 'low'

    return result


# ============================================================
#  复核界面
# ============================================================

def _icon(level):
    return {'high':'✅','medium':'⚠️','low':'❓'}.get(level,'❓')

CRITICAL = {'case_no', 'hearing_time'}
ROLE_NAMES = {
    'plaintiff':'原告','defendant':'被告','defendant_criminal':'被告人',
    'prosecutor':'公诉机关','applicant':'申请人','respondent':'被申请人',
    'appellant':'上诉人','appellee':'被上诉人',
}

def format_for_review(parsed):
    confidence = parsed.get('confidence', {})
    ocr_meta = parsed.get('ocr_meta', {})

    # OCR 引擎信息
    tier_names = {'tesseract': 'Tesseract (轻量本地)', 'mineru': 'MinerU (云端高精度)'}
    tier_name = tier_names.get(ocr_meta.get('tier', ''), '未知')
    tier_score = ocr_meta.get('quality_score', '?')
    tier_accept = '✅' if ocr_meta.get('acceptable') else '⚠️'

    lines = [
        "=" * 55,
        f"📋 请复核 OCR 识别结果",
        f"   OCR引擎: {tier_name}  |  质量分: {tier_score}/100  {tier_accept}",
        "=" * 55, "",
    ]
    for label, key in [('文书类型','document_type'),('案号','case_no'),('案由','case_type'),
                        ('法院','court_name'),('开庭时间','hearing_time'),
                        ('开庭地点','hearing_location'),('法官','judge_name'),
                        ('上诉期限(天)','appeal_deadline_days')]:
        conf = confidence.get(key,'low')
        icon = _icon(conf)
        is_crit = key in CRITICAL
        flag = ' ⚠️ 请核对原文确认' if (is_crit or conf in ('low','medium')) else ''
        val = parsed.get(key)
        val = str(val) if isinstance(val,(int,float)) else val
        lines.append(f"  {icon} {label}: {val or '（未识别）'}{flag}")
        if not val and is_crit:
            lines.append(f"      ⚠️ 此字段为空，必须手动输入！")

    parties = parsed.get('parties',{})
    if parties:
        lines.extend(["","  当事人（核对姓名）:"])
        for role, name in parties.items():
            lines.append(f"    {_icon(confidence.get('parties','low'))} {ROLE_NAMES.get(role,role)}: {name}")
        if confidence.get('parties','low') != 'high':
            lines.append("    ⚠️ 当事人姓名可能有 OCR 误差，请核对")

    lines.extend(["","-"*50,"👉 确认无误回复「确认」，需修改请告知具体字段。","-"*50])
    return '\n'.join(lines)


def should_create_calendar(parsed):
    return parsed.get('document_type','') in ('传票','应诉通知书','出庭通知书')


# ============================================================
#  自动归纳 — 案卷文件夹管理
# ============================================================

DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")


def find_case_folder(case_no, parties=None, search_dir=None):
    """
    查找已有的案卷文件夹（案号优先 → 当事人名称兜底）。

    匹配规则（按优先级）:
      1. 文件夹名含案号（忽略括号全半角差异）
      2. 文件夹名含当事人姓名（原告/被告/申请人任一方即可）
      3. 都没匹配到 → 返回 None，由调用方建新案卷

    搜索范围：桌面优先 → search_dir（如有）
    """
    clean_no = case_no.replace('（', '(').replace('）', ')').replace(' ', '')
    core = re.sub(r'[（(]\d{4}[）)]', '', clean_no).strip()

    dirs_to_search = [DESKTOP]
    if search_dir and os.path.isdir(search_dir):
        dirs_to_search.append(search_dir)

    for base in dirs_to_search:
        if not os.path.isdir(base):
            continue
        for name in os.listdir(base):
            full = os.path.join(base, name)
            if not os.path.isdir(full):
                continue
            name_clean = name.replace('（', '(').replace('）', ')').replace(' ', '')

            # 规则 1: 案号匹配（案号为空时跳过，避免 '' in 任意字符串恒为真而短路命中）
            if clean_no and (clean_no in name_clean or core in name_clean):
                return full

            # 规则 2: 当事人姓名匹配
            if parties:
                for role, party_name in parties.items():
                    if not party_name:
                        continue
                    # 拆分多当事人："耿平、朱玲秀" → ["耿平","朱玲秀"]
                    names = re.split(r'[、，,;\s]+', party_name)
                    for pn in names:
                        pn = pn.strip()
                        if len(pn) < 2:
                            continue
                        # 精确匹配
                        if pn in name_clean:
                            return full
                        # 滑动窗口模糊匹配（2 字窗口）：应对简称/别字
                        for i in range(len(pn) - 1):
                            window = pn[i:i+2]
                            if window in name_clean:
                                return full
    return None


def create_case_folder(case_no="", case_type="", court_name="", parties=None, location=DESKTOP):
    """
    自动创建案卷文件夹。
    命名格式（按优先级）:
      1. {原告/申请人}诉{被告/被申请人} {案由}   ← 双方都有
      2. {当事人} {案由}                          ← 只有一方
      3. {案由}                                   ← 无当事人信息
    不去案号、不去法院名，只用双方姓名+案由，和人脑命名习惯一致。
    """
    # 提取第一个当事人姓名（多当事人取第一个）
    def _first_party(role_key):
        if not parties:
            return None
        raw = parties.get(role_key, '')
        if not raw:
            return None
        return re.split(r'[、，,;\s]+', raw.strip())[0]

    # 原告方 / 申请人 / 上诉人
    plaintiff = _first_party('plaintiff') or _first_party('applicant') or _first_party('appellant') or _first_party('defendant_criminal')
    # 被告方 / 被申请人 / 被上诉人
    defendant = _first_party('defendant') or _first_party('respondent') or _first_party('appellee') or _first_party('prosecutor')

    if plaintiff and defendant:
        folder_name = f"{plaintiff}诉{defendant}"
    elif plaintiff:
        folder_name = plaintiff
    elif defendant:
        folder_name = defendant
    else:
        folder_name = ""

    if case_type:
        if folder_name:
            folder_name = f"{folder_name} {case_type}"
        else:
            folder_name = case_type

    if not folder_name:
        # 最终回退：用案号
        folder_name = case_no.replace(' ', '') if case_no else "未命名案卷"

    # 清理非法字符
    folder_name = re.sub(r'[<>:"|?*/\\]', '', folder_name).strip()
    folder_path = os.path.join(location, folder_name)

    os.makedirs(folder_path, exist_ok=True)

    # 自动创建标准化子目录结构
    _create_standard_subdirs(folder_path)

    return folder_path


# ============================================================
#  标准化案卷目录结构
# ============================================================

STANDARD_SUBDIRS = [
    ("01 法院送达文书", "传票、判决书、保全裁定等法院名义发布的所有材料"),
    ("02 我方提交资料", "我方向法院递交的起诉状、答辩状、证据清单、代理词等"),
    ("03 对方提交资料", "对方通过法院送达给我方的证据、起诉状、答辩状等"),
    ("04 案件原始材料", "从当事人收到的所有案件原始材料，以备查验"),
    ("05 律师工作文本", "律师工作过程中产生的文书——法律意见、庭审提纲等"),
    ("06 委托签署材料", "委托代理合同、授权委托书、风险告知书、发票等"),
    ("07 邮件收寄记录", "与法院、当事人、对方律师的邮件往来记录"),
    ("08 法规类案检索", "法律法规、司法解释、类案检索报告"),
    ("09 法院庭审笔录", "庭审笔录、听证笔录、勘验笔录等"),
    ("10 案件保全资料", "财产保全、证据保全、行为保全相关文书及回执"),
]


def _create_standard_subdirs(case_folder):
    """在案卷文件夹下创建标准化子目录。已有则不重复创建。"""
    created = 0
    for name, _desc in STANDARD_SUBDIRS:
        sub = os.path.join(case_folder, name)
        if not os.path.exists(sub):
            os.makedirs(sub)
            created += 1
    if created:
        print(f"  📂 已创建 {created} 个标准子目录", file=sys.stderr)


# 法院文书 → 01 的归类映射
COURT_DOC_TYPES = {
    '判决书', '裁定书', '传票', '应诉通知书', '出庭通知书',
    '举证通知书', '受理通知书', '上诉须知',
}


def _categorize_document(parsed):
    """根据文书类型归类到标准子目录，返回子目录名或 None。"""
    doc_type = parsed.get('document_type', '')
    if doc_type in COURT_DOC_TYPES:
        return "01 法院送达文书"
    return None


def check_duplicates(target_dir, filename, file_size):
    """
    检查目标目录是否有重复文件。
    返回 (is_dup: bool, matches: list[str])
    """
    matches = []
    if not os.path.isdir(target_dir):
        return False, matches
    for existing in os.listdir(target_dir):
        existing_path = os.path.join(target_dir, existing)
        if not os.path.isfile(existing_path):
            continue
        # 规则1: 同名文件
        if existing == filename:
            matches.append(f"同名: {existing}")
            continue
        # 规则2: 相似大小（±5%）
        try:
            es = os.path.getsize(existing_path)
            if es > 0 and abs(es - file_size) / es < 0.05:
                matches.append(f"大小接近 ({es}B vs {file_size}B): {existing}")
        except OSError:
            pass
    return len(matches) > 0, matches


def file_photo(parsed, photo_path, case_folder):
    """
    将原始照片归档到案卷文件夹对应子目录中。
    法院文书 → 01 法院送达文书/{文书类型}/
    其他类型 → 根目录/{文书类型}/
    """
    sub_dir = _categorize_document(parsed)
    if sub_dir:
        target = os.path.join(case_folder, sub_dir, parsed.get('document_type', '其他'))
    else:
        target = os.path.join(case_folder, parsed.get('document_type', '其他'))

    os.makedirs(target, exist_ok=True)

    # 原始照片
    ext = os.path.splitext(photo_path)[1] or '.jpg'
    dest = os.path.join(target, f"原照片{ext}")

    # 重复检测
    orig_size = os.path.getsize(photo_path)
    is_dup, matches = check_duplicates(target, f"原照片{ext}", orig_size)
    if is_dup:
        print(f"  ⚠️ 目标目录可能存在重复文件:", file=sys.stderr)
        for m in matches:
            print(f"     {m}", file=sys.stderr)
        print(f"  💡 如确认重复，可跳过此文件。文件仍将归档但请人工核对。", file=sys.stderr)

    shutil.copy2(photo_path, dest)
    print(f"  📷 照片已归档: {dest}", file=sys.stderr)

    # OCR 识别文本
    text_path = os.path.join(target, "OCR识别结果.txt")
    raw = parsed.get('raw_text', '')
    if raw:
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(raw)
        print(f"  📝 OCR 文本已保存: {text_path}", file=sys.stderr)

    return target


def _match_strength(folder_name, parties):
    """
    判断当事人姓名匹配的强弱（同名同姓对抗性审查核心）。
      'both' : 双方姓名都出现在案卷名 → 强信号
      'one'  : 仅一方姓名出现       → 弱信号，同名同姓风险更高
      None   : 未匹配到姓名
    """
    if not parties:
        return None
    name_clean = folder_name.replace('（', '(').replace('）', ')').replace(' ', '')

    def _any_hit(role_val):
        if not role_val:
            return False
        for pn in re.split(r'[、，,;\s]+', role_val.strip()):
            pn = pn.strip()
            if len(pn) >= 2 and pn in name_clean:
                return True
        return False

    p = parties.get('plaintiff') or parties.get('applicant') or parties.get('appellant') or parties.get('defendant_criminal')
    d = parties.get('defendant') or parties.get('respondent') or parties.get('appellee') or parties.get('prosecutor')
    p_hit, d_hit = _any_hit(p), _any_hit(d)
    if p and d:
        if p_hit and d_hit:
            return 'both'
        if p_hit or d_hit:
            return 'one'
        return None
    return 'one' if (p_hit or d_hit) else None


def _confirm_reason(matched_by, parties, folder):
    base = f"已在桌面匹配到案卷：{os.path.basename(folder)}\n"
    if matched_by == 'case_no':
        base += "匹配依据：案号（暗号）精确一致——唯一标识，可信度最高，仍建议核对案号。"
    elif matched_by == 'both':
        base += ("匹配依据：双方当事人的姓名均出现在案卷名中（强信号）。\n"
                 "⚠️ 同名同姓风险：中国常见姓名重复率极高，仍请律师核对身份证号/案号后再归档。")
    elif matched_by == 'one':
        base += ("匹配依据：仅一方当事人姓名出现在案卷名中（弱信号）。\n"
                 "⚠️ 同名同姓风险高：单方姓名极易误命中，务必核对身份后再归档。")
    else:
        base += "匹配依据：当事人姓名部分匹配，请人工核对。"
    return base


def auto_file_photo(parsed, photo_path=None):
    """
    自动归纳入口（重构版）。

    业务规则（第一性原理 + 同名同姓对抗性审查）：
      A. 匹配优先级：案号(暗号)精确 → 当事人姓名兜底（以姓名为主，因扫描件习惯写姓名）。
      B. 找到已有案卷 → 不自动归档，返回 requires_confirmation=True，
         由律师确认。错误归档会污染既有案卷，且同名同姓高频，必须人工把关。
      C. 找不到     → 按既定命名规则在桌面新建案卷（安全，不污染既有），并自动归档照片。

    返回 dict，供上层 agent 驱动确认流程：
      status / case_folder / matched_by / parties / requires_confirmation / reason
    """
    case_no = parsed.get('case_no') or ''
    parties = parsed.get('parties') or {}

    # 任一可识别才继续（去掉原 case_no 硬前置校验，启用姓名兜底）
    if not case_no and not parties:
        return {
            'status': 'unresolved',
            'case_folder': None,
            'matched_by': None,
            'parties': parties,
            'requires_confirmation': False,
            'reason': '未识别到案号或当事人姓名，无法定位案卷。请人工指定案卷或补全信息。',
        }

    # 1. 匹配已有案卷
    existing = find_case_folder(case_no, parties)
    if existing:
        nc = case_no.replace('（', '(').replace('）', ')').replace(' ', '')
        if case_no and nc in existing.replace('（', '(').replace('）', ')').replace(' ', ''):
            matched_by = 'case_no'
        else:
            matched_by = _match_strength(existing, parties) or 'parties'
        return {
            'status': 'matched',
            'case_folder': existing,
            'matched_by': matched_by,
            'parties': parties,
            'requires_confirmation': True,
            'reason': _confirm_reason(matched_by, parties, existing),
            'suggested_action': '请律师核对当事人姓名/案号确认是否归档；若同名同姓误命中，请勿归档。确认后可带 --to-folder 重新运行本脚本完成归档。',
        }

    # 2. 未找到 → 按既定命名规则在桌面新建（安全，可自动归档）
    case_type = parsed.get('case_type') or ''
    court = parsed.get('court_name') or ''
    case_folder = create_case_folder(case_no, case_type, court, parties)
    print(f"📁 已创建案卷: {case_folder}", file=sys.stderr)
    status = {
        'status': 'created',
        'case_folder': case_folder,
        'matched_by': 'new',
        'parties': parties,
        'requires_confirmation': False,
        'reason': '本机未找到匹配案卷，已按命名规则（{原告}诉{被告} {案由}）在桌面新建。',
    }
    if photo_path and os.path.exists(photo_path):
        file_photo(parsed, photo_path, case_folder)
        status['archived'] = True
    return status


# ============================================================
#  CLI
# ============================================================

def main():
    args = sys.argv[1:]
    if not args:
        print("用法: python3 court_photo_ocr.py <image_path> [--to-folder <folder>] [--ocr-tier <tier>]")
        print("      python3 court_photo_ocr.py --text '文书文本...'")
        print("")
        print("OCR 策略: Tesseract(轻量本地) → MinerU(云端高精度) 双级降级")
        print("  --ocr-tier tesseract|mineru  强制使用指定 OCR（跳过降级）")
        print("依赖: tesseract + chi_sim / mineru-open-api（按需安装）")
        sys.exit(1)

    # 律师确认后的归档模式：直接归档到指定案卷
    to_folder = None
    if '--to-folder' in args:
        i = args.index('--to-folder')
        to_folder = args[i + 1]
        args = args[:i] + args[i + 2:]

    # 强制指定 OCR 层级
    force_tier = None
    if '--ocr-tier' in args:
        i = args.index('--ocr-tier')
        force_tier = args[i + 1]
        args = args[:i] + args[i + 2:]

    if args and args[0] == '--text' and len(args) >= 2:
        text = args[1]
        image_path = None
        ocr_meta = None
    else:
        image_path = args[0] if args else None
        if not image_path or image_path.startswith('-'):
            print("❌ 缺少图片路径", file=sys.stderr); sys.exit(1)

        # 图片校验
        ok, reason = validate_image(image_path)
        if not ok:
            print(f"❌ 图片校验失败: {reason}", file=sys.stderr); sys.exit(1)

        print(f"📷 正在 OCR: {image_path}", file=sys.stderr)

        text, ocr_meta = run_ocr_tiered(image_path, force_tier=force_tier)
        if not text:
            print('{"error":"双级 OCR 全部失败"}', file=sys.stderr); sys.exit(1)

    result = parse_court_text(text)
    result['raw_text'] = text[:500]
    # 追加 OCR 元数据
    if ocr_meta:
        result['ocr_meta'] = ocr_meta

    if to_folder:
        # 律师已确认 → 直接归档到指定案卷
        if not image_path:
            print('{"error":"--to-folder 需配合图片路径使用"}', file=sys.stderr); sys.exit(1)
        if not os.path.isdir(to_folder):
            print(f"❌ 目标案卷不存在: {to_folder}", file=sys.stderr); sys.exit(1)
        file_photo(result, image_path, to_folder)
        result['case_folder'] = to_folder
        result['status'] = 'archived_confirmed'
        result['archived'] = True
        result['requires_confirmation'] = False
        print(f"✅ 已按律师确认归档至: {to_folder}", file=sys.stderr)
    else:
        # 自动归纳：匹配已有(待确认) 或 新建(自动)
        resolution = auto_file_photo(result, image_path)
        result.update(resolution)

    print(format_for_review(result), file=sys.stderr)
    print(file=sys.stderr)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
