#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_target_patent.py —— 目标专利解构 + 攻击点诊断
========================================================

本脚本解构目标专利文本（.docx 或 .pdf），抽取权利要求，构建权利要求树，
输出"攻击点诊断清单"（供无效理由组合设计参考）。

**v1.0.8 升级**：新增 `--domain` 选项，支持领域专项 checklist：
    - all（默认，通用）
    - chem（化学 / 医药 / 生物领域专项）
    - mech（机械 / 电气，暂与 all 相同）
    - bio（同 chem）

**v1.1.0 修复**：chem 医药用途主题检测收紧为句式共现（杜绝"药物组合物"误报）；
通用 checklist 细则条款编号更新为 2024 版（细则22 / 细则23.2）。

领域专项依据 references/化学医药专项.md（5 大攻击维度 + 10 类 checklist）。

用法:
    python analyze_target_patent.py --patent <目标专利文本.docx/.pdf> [--out <输出.md>] [--domain chem]

说明: 本脚本只做结构化抽取与初步提示，不替代法律判断；最终理由组合须人工/智能体结合证据裁定。
"""
import argparse, os, re, sys

try:
    from docx import Document
except ImportError:
    Document = None

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


def extract_text(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.docx':
        if Document is None:
            raise RuntimeError('python-docx 未安装')
        doc = Document(path)
        return '\n'.join(p.text for p in doc.paragraphs)
    elif ext == '.pdf':
        if fitz is None:
            raise RuntimeError('PyMuPDF 未安装')
        d = fitz.open(path)
        return '\n'.join(d[i].get_text() for i in range(d.page_count))
    else:
        raise RuntimeError('仅支持 .docx / .pdf')


def parse_claims(text):
    """抽取权利要求，识别编号与引用关系（支持 '权利要求N' / '权N'）。

    v1.0.9 修复：先定位"权利要求书"锚点，仅在权项段内解析，避免著录项
    （申请号/申请日/公开号/年份等）被误识别为权利要求（CN2023113881976 案曾误识 3 项）。
    """
    # 1. 定位"权利要求书"段起点（兼容全角空格、"权利要求："等写法）
    start = 0
    m = re.search(r'权\s*利\s*要\s*求\s*书', text)
    if m:
        start = m.end()
    else:
        # 回退：匹配行首"权利要求"后跟冒号/换行（PatSeek 输出常为 "权利要求:"）
        m2 = re.search(r'(?:^|\n)\s*权\s*利\s*要\s*求\s*[:：]?\s*(?:\n|$)', text)
        if m2:
            start = m2.end()
    # 2. 定位段终点（说明书 / 说明书附图 / 摘要 等下一大节）
    end = len(text)
    for end_pat in [r'\n\s*说\s*明\s*书', r'\n\s*摘\s*要\b', r'\n\s*说\s*明\s*书\s*附\s*图']:
        em = re.search(end_pat, text[start:])
        if em:
            end = min(end, start + em.start())
    segment = text[start:end] if start > 0 else text

    # 3. 元数据守卫：明显著录项行不计为权利要求（双保险）
    META_HINT = re.compile(
        r'(申请号|申请日|公开号|公开日|公告号|公告日|IPC|分类号|申请人|发明人|'
        r'优先权|代理|代理人|地址|专利号|授权|国际申请|国际公开)'
    )

    claims = {}
    pattern = re.compile(r'(?:权利要求\s*)?(\d+)\s*[\.、]\s*(.*?)(?=(?:\n\s*(?:权利要求\s*)?\d+\s*[\.、])|\Z)', re.S)
    for m in pattern.finditer(segment):
        num = int(m.group(1))
        body = m.group(2).strip()
        # 著录项守卫：编号过大（如申请号 202311388197）或正文以著录关键词开头则跳过
        if num > 200:
            continue
        if META_HINT.search(body[:30]):
            continue
        if 4 < len(body) < 4000:
            claims[num] = body
    ref_map = {}
    for num, body in claims.items():
        refs = re.findall(r'权利要求\s*(\d+)\s*', body)
        if refs:
            ref_map[num] = sorted(set(int(r) for r in refs))
    return claims, ref_map


def build_tree(claims, ref_map):
    lines = []
    for num in sorted(claims):
        refs = ref_map.get(num, [])
        tag = '独立' if not refs else '从属→' + ','.join(map(str, refs))
        preview = claims[num][:60].replace('\n', ' ')
        lines.append(f'  - 权利要求{num} [{tag}]: {preview}...')
    return '\n'.join(lines)


# ── 通用攻击点 checklist ──────────────────────────────────

def attack_checklist(claims, ref_map):
    items = [
        '[ ] 权利要求树：独立权利要求必要技术特征是否可被现有技术逐项公开（攻新颖性/创造性）',
        '[ ] 从属权利要求是否对独立权利要求作出实质性限定（否则可一并无效）',
        '[ ] 说明书是否清楚完整记载技术问题/方案/效果（攻法26.3充分公开）',
        '[ ] 权利要求有无自造词/含义模糊（攻细则22（旧细则20.1）不清楚，可作佯攻）',
        '[ ] 权利要求概括是否超出说明书实施例（攻法26.4支持）',
        '[ ] 授权文本相对原始申请是否补入特征（攻法33修改超范围，可设两难陷阱）',
        '[ ] 独立权利要求是否缺必要技术特征（攻细则23.2（旧细则20.2）缺必特）',
        '[ ] 是否存在申请人审查中限制性陈述/承诺（禁反言，用于解释或证伪创造性）',
        '[ ] 是否存在同日/本人另一相同专利（攻法9.1重复授权）',
        '[ ] 是否属排除客体（法5/25）',
    ]
    return '\n'.join(items)


# ── 化学医药专项 checklist（v1.0.8 新增）────────────────────

def chem_checklist(claims, ref_map, full_text: str = ''):
    """化学/医药/生物领域专项 checklist。依据 references/化学医药专项.md。"""
    items = []

    # 0. 自动检测：是否涉及化学医药特殊主题
    all_text = ' '.join(claims.values()).lower()
    if full_text:
        all_text += ' ' + full_text.lower()

    has_compound = bool(re.search(r'(化合物|通式|衍生物|salt|crystal|polymorph|prodrug|前药|晶型|多晶型|盐|马库什|markush)', all_text, re.IGNORECASE))
    # v1.1.0 修复：医药用途检测由宽泛关键词命中收紧为"句式共现"——
    # 单独出现"药/用途/use"（如"药物组合物"）不再误判为医药用途主题；
    # 须命中"用于治疗/预防……"、"在制备……药物中的应用"（瑞士型）、
    # "医药用途/适应症/第二医药用途"等明确用途句式才判定。
    has_pharm = bool(re.search(
        r'(用于治疗|用于预防|在制备.{0,30}药物中的应用|在制备.{0,30}药品中的应用|'
        r'医药用途|制药用途|第二医药用途|瑞士型|swiss[- ]?type|second medical use|'
        r'治疗.{0,8}(疾病|癌症|肿瘤|感染|炎症|糖尿病)|预防.{0,8}(疾病|癌症|肿瘤|感染)|适应症)',
        all_text, re.IGNORECASE))
    has_crystal = bool(re.search(r'(晶型|多晶型|crystal form|polymorph|pxrd|衍射峰)', all_text, re.IGNORECASE))
    has_markush = bool(re.search(r'(马库什|markush|通式|结构通式)', all_text, re.IGNORECASE))
    has_combo = bool(re.search(r'(组合物|组合|composition|formulation|协同|synergy)', all_text, re.IGNORECASE))

    if has_compound or has_pharm or has_crystal or has_markush or has_combo:
        items.append('### 🔬 自动检测结果')
        items.append('')
        detections = []
        if has_compound: detections.append('化合物')
        if has_crystal: detections.append('晶型')
        if has_markush: detections.append('马库什')
        if has_pharm: detections.append('医药用途')
        if has_combo: detections.append('组合物')
        items.append(f'- 权利要求涉及：**{", ".join(detections)}**')
        items.append('- 已应用化学医药专项 checklist（references/化学医药专项.md）')
        items.append('')

    # 1. 化合物层
    items.append('### 10.1 化合物层')
    items.append('- [ ] 权利要求是否覆盖**多个化合物 / 一类化合物**（马库什 / 表格 / 通式）？')
    items.append('- [ ] 独立权利要求的化合物是**新化合物**还是**已知化合物的新用途 / 新晶型 / 新盐**？')
    items.append('- [ ] 化合物确认数据是否完整（核磁 / 质谱 / 元素分析 / 红外）？')
    items.append('- [ ] 制备方法是否**可重复**（关键中间体、试剂、反应条件）？')
    items.append('- [ ] 用途 / 效果数据是否齐备（活性、选择性、毒性、药代）？')
    items.append('')

    # 2. 晶型层
    items.append('### 10.2 晶型层')
    items.append('- [ ] 权利要求是否限定**特定晶型**（如"晶型 I"）？')
    items.append('- [ ] 晶型表征数据是否齐备（PXRD / DSC / TGA）？')
    items.append('- [ ] 晶型 vs 其他晶型 / 无定形**优势数据**是否给出？')
    items.append('- [ ] 制备方法（结晶溶剂、温度、晶种）是否可重复？')
    items.append('')

    # 3. 马库什层
    items.append('### 10.3 马库什层')
    items.append('- [ ] 权利要求是马库什式？涵盖化合物数量级？')
    items.append('- [ ] 效果实施例数 vs 涵盖化合物数（建议 ≥ 0.3）？')
    items.append('- [ ] 效果实施例分布是否均匀？或集中在某一子结构？')
    items.append('- [ ] 共同结构 / 共同作用方式是否明确？')
    items.append('- [ ] 优先权文件（前申请）是否给出马库什 / 涵盖哪些具体化合物？')
    items.append('')

    # 4. 医药用途层
    items.append('### 10.4 医药用途层')
    items.append('- [ ] 权利要求是**化合物 / 组合物** 还是**瑞士型医药用途**？')
    items.append('- [ ] 用途是"已知化合物的第二医药用途" 还是"新化合物 + 用途"？')
    items.append('- [ ] 用途效果数据是否齐备（剂量、给药方式、患者群体、终点指标、对照）？')
    items.append('- [ ] 是否可主张"现有技术无改进动机 / 无合理成功预期"？——**注意是第三步**（参指导案例 276 号）')
    items.append('')

    # 5. 组合物层
    items.append('### 10.5 组合物层')
    items.append('- [ ] 权利要求是组合物（多组分）？各组分范围？')
    items.append('- [ ] 组合物是否主张**协同效果**？协同证据是否齐备？')
    items.append('- [ ] 与各组分单独使用 vs 组合使用的对比数据？')
    items.append('')

    # 6. 优先权层
    items.append('### 10.6 优先权层')
    items.append('- [ ] 在后申请是否要求优先权？优先权日？')
    items.append('- [ ] 化合物 / 晶型 / 马库什 / 数值范围 / 医药用途的"相同主题"判断（详见 §八）')
    items.append('')

    # 7. 实验数据层
    items.append('### 10.7 实验数据层')
    items.append('- [ ] 实验数据是否齐备（样品来源、测量条件、人员、方法、数据处理）？')
    items.append('- [ ] 是否含孤立图谱 / 单一数值？')
    items.append('- [ ] 与最接近现有技术的对比数据是否来自**同一实验模型**？')
    items.append('- [ ] 是否为申请日后补交？补交数据是否"本领域技术人员从原申请可得"？')
    items.append('')

    # 8. 创造性辅助判断
    items.append('### 10.8 创造性辅助判断')
    items.append('- [ ] 是否陷入"生物电子等排"式后见之明？（自我警告）')
    items.append('- [ ] 技术启示三校验（问题同源 / 结构兼容 / 公知常识证据化）是否过？')
    items.append('')

    # 9. 攻击优先级（基于检测结果）
    items.append('### 攻击优先级建议（基于自动检测）')
    if has_markush:
        items.append('1. **马库什支持问题**（法26.4）—— 效果实施例分布不均的攻击')
        items.append('2. **优先权不成立**（马库什 → 具体化合物未明确记载）')
        items.append('3. **充分公开**（化合物三维度）')
        items.append('4. **创造性**（第三步 + 合理成功预期，避免生物电子等排后见之明）')
    elif has_crystal:
        items.append('1. **晶型效果门槛**（法26.4 / 法22.3）—— 晶型 vs 其他晶型 / 无定形优势无数据')
        items.append('2. **晶型充分公开**（PXRD 表征数据不全）')
        items.append('3. **预料不到技术效果**（法22.3 第三步）')
        items.append('4. **使用公开 + 补交实验数据**（呋喹替尼晶型案）')
    elif has_pharm:
        items.append('1. **医药用途创造性**（法22.3 第三步，合理成功预期在第三步，**不是第一步**）')
        items.append('2. **充分公开**（用途 / 效果三维度）')
        items.append('3. **优先权相同主题**（化合物 → 医药用途）')
    elif has_combo:
        items.append('1. **组合物协同效果证据规则**（依达拉奉右莰醇案）')
        items.append('2. **充分公开**（组分范围 / 协同效果数据）')
        items.append('3. **创造性**（现有技术是否给出组合启示）')
    else:
        items.append('1. **充分公开**（化合物三维度）')
        items.append('2. **创造性**（第三步 + 合理成功预期）')
        items.append('3. **优先权不成立**')
    items.append('')

    # 10. 常见误区警告
    items.append('### 常见误区（化学医药特有）')
    items.append('- ❌ 用"无合理成功预期"反推最接近现有技术（指导案例276号：这是**第三步**）')
    items.append('- ❌ 攻击"晶型表征数据不全"但本专利已给 PXRD——应攻"晶型 vs 其他晶型优势无数据"')
    items.append('- ❌ 用"不同实验模型数据"主张创造性（克唑替尼案：不可比）')
    items.append('- ❌ 攻击"申请日后补交数据不采信"——补交数据**可被采信**只要"本领域技术人员从原申请可得"')
    items.append('- ❌ 攻击"医药用途创造性"忽略第三步——必须过技术启示三校验')
    items.append('')

    return '\n'.join(items)


# ── 主函数 ───────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description='目标专利解构 + 攻击点诊断（支持 --domain chem 化学医药专项）')
    ap.add_argument('--patent', required=True, help='目标专利文本 .docx/.pdf')
    ap.add_argument('--out', default=None, help='输出 markdown 路径')
    ap.add_argument('--domain', default='all',
                    choices=['all', 'chem', 'mech', 'bio'],
                    help='领域专项（v1.0.8+）：all=通用 / chem=化学医药 / bio=同 chem / mech=机械电气（暂同 all）')
    args = ap.parse_args()

    text = extract_text(args.patent)
    claims, ref_map = parse_claims(text)
    tree = build_tree(claims, ref_map)
    checklist = attack_checklist(claims, ref_map)

    md_parts = [
        f"# 目标专利解构报告（领域：{args.domain}）",
        "",
        f"## 一、权利要求树（共 {len(claims)} 项）",
        tree,
        "",
        "## 二、引用关系",
        '\n'.join(f'- 权利要求{k} 引用 {v}' for k, v in ref_map.items()) or '（无从属引用，或为独立权利要求集合）',
        "",
        "## 三、攻击点诊断清单（通用 · references/无效理由体系与论证要点.md）",
        checklist,
        "",
    ]

    # 化学医药专项
    if args.domain in ('chem', 'bio'):
        chem_cl = chem_checklist(claims, ref_map, full_text=text)
        md_parts.append("## 四、化学医药专项攻击点 checklist（references/化学医药专项.md）")
        md_parts.append("")
        md_parts.append(chem_cl)
        md_parts.append("")
        md_parts.append("---")
        md_parts.append("**配套脚本与文档**:")
        md_parts.append("- `references/化学医药专项.md` —— 完整 5 大攻击维度 + 10 类 checklist")
        md_parts.append("- `references/无效理由体系与论证要点.md` §4 —— 化合物三维度")
        md_parts.append("- `references/无效宣告典型案例.md` —— 缬沙坦沙库巴曲/马昔腾坦/呋喹替尼晶型 等")
        md_parts.append("")

    md_parts.extend([
        "## 五、下一步",
        "- 据攻击点检索证据（公开日须早于申请日/优先权日）",
        "- 设计\"主攻+辅助佯攻\"理由组合（参见 references/理由组合策略.md）",
        "- 调用 make_invalidation_doc.py 生成请求书骨架",
        "- 化学医药案件：用 scripts/invalidation_search.py 时启用关键词扩展（化合物/晶型/盐/前药/医药用途/组合物）",
    ])

    md = '\n'.join(md_parts)

    if args.out:
        with open(args.out, 'w', encoding='utf-8') as f:
            f.write(md)
        print('已写出:', args.out)
    else:
        print(md)


if __name__ == '__main__':
    main()
