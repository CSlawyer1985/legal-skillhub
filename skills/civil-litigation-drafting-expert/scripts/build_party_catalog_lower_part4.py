#!/usr/bin/env python3
"""Append lower-volume file 4 and finish the party-filing catalog.

The file contains Chapters 18-22 plus the 44 forms/examples attached to the
2024 trial pleading models. The latter are retained as historical nodes but
marked superseded because 法〔2025〕82号 expressly repealed 法〔2024〕46号.
No textbook form body is copied into the catalog.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from build_party_catalog_lower_part2 import extract_pages, normalize


ACTIVE_FORMS = [
    ("SUP", "审判监督程序", 1, 1, "民事再审申请书（申请再审用）", "民事再审申请书"),
    ("PAY", "督促程序", 1, 5, "申请书（申请支付令用）", "支付令申请书"),
    ("PAY", "督促程序", 2, 7, "申请书（撤回支付令申请用）", "撤回支付令申请书"),
    ("PAY", "督促程序", 3, 9, "异议书（对支付令提出异议用）", "支付令异议书"),
    ("PAY", "督促程序", 4, 11, "申请书（撤回支付令异议用）", "撤回支付令异议申请书"),
    ("PCL", "公示催告程序", 1, 15, "申请书（申请公示催告用）", "公示催告申请书"),
    ("PCL", "公示催告程序", 2, 17, "申请书（撤回公示催告申请用）", "撤回公示催告申请书"),
    ("PCL", "公示催告程序", 3, 19, "申报书（利害关系人申报权利用）", "公示催告权利申报书"),
    ("ENF", "执行程序", 1, 23, "申请书（申请执行用）", "申请执行书"),
    ("ENF", "执行程序", 2, 26, "被执行人财产状况表（申请执行人提供被执行人财产状况用）", "被执行人财产状况表"),
    ("ENF", "执行程序", 3, 28, "执行异议书（当事人、利害关系人提出异议用）", "执行行为异议书"),
    ("ENF", "执行程序", 4, 30, "复议申请书（当事人、利害关系人申请复议用）", "执行异议复议申请书"),
    ("ENF", "执行程序", 5, 32, "申请书（申请提级执行用）", "提级执行申请书"),
    ("ENF", "执行程序", 6, 34, "执行异议书（案外人提出异议用）", "案外人执行异议书"),
    ("ENF", "执行程序", 7, 36, "执行异议书（对财产分配方案提出异议用）", "财产分配方案异议书"),
    ("ENF", "执行程序", 8, 38, "保证书（执行担保用）", "执行担保保证书"),
    ("FOR", "涉外民事诉讼程序的特别规定", 1, 41, "申请书（当事人申请承认和执行外国法院生效判决、裁定或仲裁裁决用）", "承认和执行外国判决、裁定或仲裁裁决申请书"),
]


APPENDIX_TITLES = [
    (46, "民间借贷纠纷起诉状"), (51, "民间借贷纠纷答辩状"),
    (54, "民间借贷纠纷起诉状实例"), (58, "民间借贷纠纷答辩状实例"),
    (61, "离婚纠纷起诉状"), (64, "离婚纠纷答辩状"),
    (66, "离婚纠纷起诉状实例"), (70, "离婚纠纷答辩状实例"),
    (72, "买卖合同纠纷起诉状"), (77, "买卖合同纠纷答辩状"),
    (81, "买卖合同纠纷起诉状实例"), (86, "买卖合同纠纷答辩状实例"),
    (90, "金融借款合同纠纷起诉状"), (95, "金融借款合同纠纷答辩状"),
    (98, "金融借款合同纠纷起诉状实例"), (103, "金融借款合同纠纷答辩状实例"),
    (107, "物业服务合同纠纷起诉状"), (111, "物业服务合同纠纷答辩状"),
    (114, "物业服务合同纠纷起诉状实例"), (118, "物业服务合同纠纷答辩状实例"),
    (121, "银行信用卡纠纷起诉状"), (125, "银行信用卡纠纷答辩状"),
    (128, "银行信用卡纠纷起诉状实例"), (132, "银行信用卡纠纷答辩状实例"),
    (135, "机动车交通事故责任纠纷起诉状"), (138, "机动车交通事故责任纠纷答辩状"),
    (140, "机动车交通事故责任纠纷起诉状实例"), (144, "机动车交通事故责任纠纷答辩状实例"),
    (146, "劳动争议起诉状"), (149, "劳动争议答辩状"),
    (151, "劳动争议起诉状实例"), (154, "劳动争议答辩状实例"),
    (156, "融资租赁合同纠纷起诉状"), (161, "融资租赁合同纠纷答辩状"),
    (165, "融资租赁合同纠纷起诉状实例"), (171, "融资租赁合同纠纷答辩状实例"),
    (175, "保证保险合同纠纷起诉状"), (179, "保证保险合同纠纷答辩状"),
    (182, "保证保险合同纠纷起诉状实例"), (186, "保证保险合同纠纷答辩状实例"),
    (189, "证券虚假陈述责任纠纷起诉状"), (193, "证券虚假陈述责任纠纷答辩状"),
    (196, "证券虚假陈述责任纠纷起诉状实例"), (201, "证券虚假陈述责任纠纷答辩状实例"),
]


RULES = {
    "SUP": ("生效民事裁判或调解书再审审查", ["中华人民共和国民事诉讼法（2023年修正）审判监督程序", "最高人民法院关于适用《中华人民共和国民事诉讼法》的解释（2022年修正）审判监督程序", "最高人民法院第四巡回法庭民商事案件申请再审指南（2025年）"], ["申请对象、法院、资格和六个月期间", "再审请求是否对应原裁判主文", "法定再审事由、事实和证据是否逐项对应"], ["一二审裁判及送达、生效材料", "原审诉辩、庭审和证据要点", "再审事由证据及知悉时间凭证"]),
    "PAY": ("无争议金钱或有价证券债权的支付令", ["中华人民共和国民事诉讼法（2023年修正）督促程序", "最高人民法院关于适用《中华人民共和国民事诉讼法》的解释（2022年修正）督促程序"], ["债权是否为确定到期的金钱或有价证券给付", "债权人与债务人是否存在其他债务纠纷并可直接送达", "异议是否针对债务本身且在法定期间提出"], ["合同、结算、付款期限和催告材料", "债务人准确送达地址", "支付令、送达凭证及异议事实证据"]),
    "PCL": ("票据等可背书转让证券的公示催告", ["中华人民共和国民事诉讼法（2023年修正）公示催告程序", "最高人民法院关于适用《中华人民共和国民事诉讼法》的解释（2022年修正）公示催告程序", "中华人民共和国票据法"], ["申请人是否为最后持有人且证券符合适用范围", "票据丧失事实、票面信息和支付地法院", "权利申报是否在公示催告期间且有原始权利材料"], ["票据复印件、底单或完整票面信息", "最后合法持有及丧失经过证据", "公告、权利凭证和交易链材料"]),
    "ENF": ("生效法律文书执行及执行程序救济", ["中华人民共和国民事诉讼法（2023年修正）执行程序", "最高人民法院关于适用《中华人民共和国民事诉讼法》的解释（2022年修正）执行程序", "最高人民法院关于人民法院办理执行异议和复议案件若干问题的规定（2020年修正）"], ["执行依据、履行期、法院和申请时效", "异议对象属于执行行为还是案外人实体权利", "复议、提级、分配方案异议或担保的专项条件"], ["生效法律文书和生效、送达证明", "履行情况、财产线索和查控材料", "执行裁定、异议材料、权属或担保证据"]),
    "FOR": ("外国判决、裁定或外国仲裁裁决的承认执行", ["中华人民共和国民事诉讼法（2023年修正）涉外程序", "中华人民共和国仲裁法（2025年修订）", "中国缔结或参加的相关国际条约及互惠原则", "《承认及执行外国仲裁裁决公约》", "指导性案例235号"], ["裁判或仲裁裁决是否生效且属于可承认执行对象", "条约、互惠或公约路径及有管辖权的中级人民法院", "送达、陈述机会、管辖、欺诈、重复裁判和公共政策审查"], ["经认证的裁判或裁决正本及生效证明", "合法传唤、送达和程序参与材料", "认证、附证明的中文译本及财产或住所连接点"]),
}


TIME_OVERRIDES = {
    "SUP-001": "原则上在判决、裁定发生法律效力后六个月内申请；法定特殊事由从知道或应当知道之日起计算的，须另行复核起算点。",
    "PAY-003": "债务人应在收到支付令之日起十五日内清偿债务或提出书面异议。",
    "PCL-003": "在人民法院公告确定的申报期间内申报权利；迟延的程序后果须结合公告和现行法核验。",
    "ENF-001": "申请执行期间通常为二年；从法律文书规定履行期间的最后一日起等法定起点计算，并核验中止、中断。",
    "ENF-004": "对执行行为异议裁定不服的，通常自裁定送达之日起十日内向上一级人民法院申请复议。",
    "ENF-005": "执行法院自收到申请执行书之日起超过六个月未执行的，方进入向上一级人民法院申请执行的法定路径；先核验执行进展和扣除期间。",
    "ENF-007": "依参与分配程序及分配方案送达后的法定异议期间提出，并以实际送达凭证复算。",
}


APPENDIX_BASES = {
    "民间借贷": ["中华人民共和国民法典", "最高人民法院关于审理民间借贷案件适用法律若干问题的规定（2020年修正）"],
    "离婚": ["中华人民共和国民法典婚姻家庭编", "最高人民法院关于适用《中华人民共和国民法典》婚姻家庭编的解释（一）（二）"],
    "买卖合同": ["中华人民共和国民法典合同编", "最高人民法院关于适用《中华人民共和国民法典》合同编通则若干问题的解释"],
    "金融借款": ["中华人民共和国民法典合同编", "现行金融监管强制性规范（按合同和主体核验）"],
    "物业服务": ["中华人民共和国民法典物业服务合同章", "物业管理条例及现行相关司法解释"],
    "银行信用卡": ["中华人民共和国民法典", "最高人民法院关于审理银行卡民事纠纷案件若干问题的规定"],
    "机动车交通事故": ["中华人民共和国民法典侵权责任编", "最高人民法院关于审理道路交通事故损害赔偿案件适用法律若干问题的解释（2020年修正）"],
    "劳动争议": ["中华人民共和国劳动法", "中华人民共和国劳动合同法", "中华人民共和国劳动争议调解仲裁法", "最高人民法院关于审理劳动争议案件适用法律问题的解释（一）（二）"],
    "融资租赁": ["中华人民共和国民法典融资租赁合同章", "最高人民法院关于适用《中华人民共和国民法典》合同编通则若干问题的解释"],
    "保证保险": ["中华人民共和国保险法", "中华人民共和国民法典", "保险法相关现行司法解释"],
    "证券虚假陈述": ["中华人民共和国证券法（2019年修订）", "最高人民法院关于审理证券市场虚假陈述侵权民事赔偿案件的若干规定（法释〔2022〕2号）"],
}


def basis_lead(pages: list[str], form_page: int, next_page: int) -> str:
    segment = normalize("\n".join(pages[form_page - 1:max(form_page + 1, next_page - 1)]))
    match = re.search(r"【说明】(.{0,1600}?)(?:【应用】|【法律依据】|$)", segment)
    return match.group(1)[:1600] if match else "OCR未完整提取说明，须回到标注页人工核对"


def purpose(name: str) -> str:
    match = re.search(r"（(.+?)）", name)
    text = match.group(1) if match else name
    return text[:-1] if text.endswith("用") else text


def logical_structure(name: str) -> list[str]:
    if "再审申请书" in name:
        return ["标题", "全部当事人及原审诉讼地位", "原审法院、案号和裁判", "具体再审请求", "法定再审事由", "逐项事实、证据和法律理由", "致送法院", "签章日期与附件"]
    if "起诉状" in name or "答辩状" in name:
        return ["标题", "当事人与诉讼地位", "诉讼请求或答辩结论", "要素化事实及争议回应", "证据和现行法律依据", "致送法院", "签章日期与附件"]
    if "财产状况表" in name:
        return ["执行案件信息", "被执行人身份", "财产类别和精确线索", "权属及控制状态", "查控建议", "线索来源与附件", "提供人签章日期"]
    if "保证书" in name:
        return ["标题", "保证人资格", "执行案件信息", "担保范围、方式和期间", "担保财产或能力", "责任承诺", "签章日期与附件"]
    return ["标题", "申请人及相对方", "案件或程序信息", "明确请求或异议事项", "触发事实与理由", "证据和现行法律依据", "致送法院", "签章日期与附件"]


def base_node(document_id: str, name: str, canonical: str, chapter: str, file_page: int,
              topic: str, bases: list[str], focus: list[str], evidence: list[str],
              status: str, update_note: str, book_basis: list[str]) -> dict:
    use = purpose(name)
    key = document_id.split("PARTY-L4-", 1)[-1]
    return {
        "document_id": document_id,
        "document_name": name,
        "canonical_name": canonical,
        "document_role": "party_filing",
        "document_function": f"供当事人或其他依法有权主体处理“{use}”事项；如属历史示范节点，仅用于识别旧版结构和映射现行示范文本。",
        "applicable_cases": [f"存在“{use}”事项的民事案件", f"案件处于{chapter}相关阶段且满足对应要件"],
        "applicable_procedure": [chapter, topic, use],
        "start_conditions": [f"存在与“{use}”对应的法定程序事实", "主体资格和授权真实有效", "向有权法院提出且未超过法定期间", "关键事实有可核查证据"],
        "applicant_or_maker": ["依法享有该程序权利的当事人、申请执行人、被执行人、案外人、利害关系人或其他法定主体；按文书类型逐项核验"],
        "counterparty_or_recipient": ["依法受理该事项的人民法院；有被申请人、债务人或其他利害关系人的，须完整列明并核对诉讼地位"],
        "competent_court": ["按原审、执行、票据支付地、被申请人住所地、财产所在地、涉外级别管辖及专项规则确定，不得沿用占位法院"],
        "book_original_basis": book_basis,
        "current_legal_basis": bases,
        "legal_update_note": update_note,
        "judicial_interpretations": ([x for x in bases if "解释" in x or "规定" in x or "法释" in x] or ["本节点未预置单一专项司法解释；生成具体案件文书时按争点检索并核验最高人民法院现行司法解释"]),
        "case_authorities": ["涉外节点预置指导性案例235号；其他节点仅在具体争点需要时，从指导性案例或人民法院案例库核验后加入" if chapter == "涉外民事诉讼程序的特别规定" else "未预置案例；具体争点需要时，仅从最高人民法院指导性案例或人民法院案例库核验后加入，并说明可比事实"],
        "court_focus": focus,
        "submission_or_making_time": [TIME_OVERRIDES.get(key, f"在“{use}”的法定阶段及时提出；必须用送达日、生效日、知悉日或公告期间单独计算")],
        "burden_of_proof": ["提出申请、异议、主张或线索的一方先证明触发程序权利的事实", "法院依职权审查不免除申请人提供可核查线索和基础材料的责任"],
        "evidence_requirements": evidence,
        "risk_analysis": ["主体、法院、程序路径或请求错误可能导致不予受理或驳回", "错过期间可能造成程序失权", "事实与证据不对应会降低审查通过率", update_note],
        "logical_structure": logical_structure(name),
        "smart_template_fields": ["filing.title", "party[].identity_and_role", "case.stage_number_cause", "request[].specific_result", "fact[].status_and_source", "law[].name_article_purpose_condition_status", "evidence[].name_fact_source", "court.recipient_and_basis", "deadline.trigger_calculation_evidence", "signature.real_authorized_person", "attachments.count_and_copies"],
        "court_review_logic": ["审查主体、资格和授权", "审查程序、法院和期限", *focus, "核对请求、事实、证据和法律后果"],
        "lawyer_writing_tips": ["先拆程序要件和请求权要件，再建立请求—事实—证据—法律矩阵", "请求必须指向法院在本程序中能够作出的处理", "案号、日期、诉讼地位、财产线索和附件逐项核对原件", "旧示范文本只作问题清单，不直接复制"],
        "ai_generation_flow": ["识别阶段、文书类型和现行示范文本", "核对触发条件、主体、法院与期限", "列出阻断级缺失信息", "建立请求—事实—证据—法律映射", "核验官方现行法和案件时点", "生成案件专属文本", "执行六类质量校验并输出风险"],
        "automatic_validation_rules": ["document_role_is_party_filing", "document_matches_procedure_and_requested_relief", "party_identity_roles_and_authority_consistent", "competent_court_has_current_legal_basis", "deadline_has_trigger_date_calculation_and_evidence", "each_material_fact_has_source", "law_citations_are_official_current_and_case_date_matched", "attachments_exist_and_copy_count_is_checked", "superseded_model_never_used_for_current_generation", "no_court_seal_judge_signature_or_internal_opinion"],
        "common_errors": ["套用相邻程序或已废止示范文本", "主体和诉讼地位前后不一致", "请求空泛或超出程序处理范围", "遗漏期限起算凭证", "事实没有证据映射", "继续引用教材旧条号", "签章、授权或附件不完整"],
        "excellent_example_policy": "不复制教材正文或实例；优秀示范必须基于经核验事实、现行法和现行示范文本，解释结构选择并去标识化。无案件事实时只生成变量模板和信息收集表。",
        "source_locator": {"source_edition": "第二版", "volume": "下册", "source_file_part": 4, "pdf_file_page": file_page, "scan_global_page": 618 + file_page, "printed_book_page": 1465 + file_page, "chapter": chapter, "coverage_note": "第4分卷全部属于当事人参考民事诉讼文书；仅提取标题、说明线索和知识结构，不复制模板或实例正文"},
        "validation_status": status,
        "version": "1.2.0",
        "effective_from": None,
        "supersedes": None,
    }


def active_node(spec, pages: list[str], next_page: int) -> dict:
    code, chapter, number, file_page, name, canonical = spec
    topic, bases, focus, evidence = RULES[code]
    key = f"{code}-{number:03d}"
    note = "教材说明用于定位；正式制作须按2023年修正民事诉讼法和现行司法解释重新核验条号、管辖、期间及文书名称。"
    if code == "FOR":
        note = "教材将外国法院判决、裁定与外国仲裁裁决并列；现行系统必须分别识别条约／互惠路径与《纽约公约》路径，并适用2023年民诉法涉外新规则及2025年修订仲裁法。"
    return base_node(f"PARTY-L4-{key}", name, canonical, chapter, file_page, topic, bases, focus, evidence, "book_verified", note, [basis_lead(pages, file_page, next_page)])


def appendix_bases(name: str) -> list[str]:
    specific = next((value for key, value in APPENDIX_BASES.items() if key in name), ["案件类型对应的现行实体法和司法解释"])
    return ["法〔2025〕82号《部分案件起诉状答辩状示范文本》", "中华人民共和国民事诉讼法（2023年修正）", *specific]


def appendix_node(number: int, file_page: int, name: str) -> dict:
    dispute = name.replace("起诉状实例", "").replace("答辩状实例", "").replace("起诉状", "").replace("答辩状", "")
    update = "【本书原规定】法〔2024〕46号试行示范文本；【现行规定】自2025年7月14日起适用法〔2025〕82号67类示范文本；【变化原因】首批11类经试用后修订并扩充；【影响】法〔2024〕46号已同时废止，本节点仅作历史映射，严禁直接用于当前生成。"
    focus = ["是否选用法〔2025〕82号中对应现行要素式文本", "诉讼请求或答辩结论与案件要件是否完整", "身份、送达、事实、证据和争议要素是否逐项填写"]
    evidence = ["主体、授权和送达信息材料", "按纠纷要件整理的合同、履行、损害或身份关系证据", "请求金额计算表、时间线和证据目录"]
    canonical = name.replace("实例", "")
    return base_node(f"PARTY-L4-APPX-{number:03d}", name, canonical, "附录：部分案件民事起诉状、答辩状示范文本（试行）", file_page, f"{dispute}要素式起诉答辩", appendix_bases(name), focus, evidence, "superseded", update, ["法〔2024〕46号《部分案件民事起诉状、答辩状示范文本（试行）》所附样式或实例；该文件已于2025年7月14日同时废止"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-catalog", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if not args.base_catalog.is_file() or not args.source.is_file():
        raise SystemExit("Base catalog and Part 4 PDF must both exist")
    base = json.loads(args.base_catalog.read_text())
    if base.get("document_count") != 88:
        raise SystemExit("Part 4 base catalog must contain exactly 88 Parts 2-3 nodes")
    pages = extract_pages(args.source)
    if len(pages) not in {205, 206}:  # extractor may retain one trailing form-feed page
        raise SystemExit(f"Expected 205 PDF pages (optionally trailing blank), got {len(pages)}")
    if "民事再审申请书" not in pages[0] or normalize(pages[204]):
        raise SystemExit("Part 4 boundary check failed")
    documents = list(base["documents"])
    for pos, spec in enumerate(ACTIVE_FORMS):
        if normalize(spec[4]) not in normalize(pages[spec[3] - 1]):
            raise SystemExit(f"Active form title/page mismatch at PDF page {spec[3]}: {spec[4]}")
        next_page = ACTIVE_FORMS[pos + 1][3] if pos + 1 < len(ACTIVE_FORMS) else 44
        documents.append(active_node(spec, pages, next_page))
    for number, (file_page, name) in enumerate(APPENDIX_TITLES, start=1):
        if normalize(name) not in normalize(pages[file_page - 1]):
            raise SystemExit(f"Appendix title/page mismatch at PDF page {file_page}: {name}")
        documents.append(appendix_node(number, file_page, name))
    payload = {
        "catalog_name": "中国民事诉讼文书AI专家—当事人参考文书完整目录",
        "scope": "第二版下册第二部分‘当事人参考民事诉讼文书样式’（完整）",
        "source": {
            "title": "民事诉讼文书样式应用及法律依据（第二版）",
            "volume": "下册",
            "source_file_parts_imported": [2, 3, 4],
            "files": [*base["source"]["files"], str(args.source)],
            "scan_global_pages": "402—823",
            "printed_book_pages": "1249—1669",
            "coverage": "下册第二部分当事人参考民事诉讼文书全部章节及附录；44个法〔2024〕46号附录节点保留为已废止历史映射",
        },
        "limitations": ["只覆盖当事人可制作、签署或提交的文书，不含人民法院制作文书", "教材OCR不作为最终法律引用证明", "教材样式和实例正文未复制入数据库", "法〔2024〕46号44个附录节点已标记superseded，现行生成须转用法〔2025〕82号"],
        "document_count": len(documents),
        "active_document_count": sum(doc["validation_status"] != "superseded" for doc in documents),
        "historical_superseded_count": sum(doc["validation_status"] == "superseded" for doc in documents),
        "documents": documents,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {len(documents)} nodes: {payload['active_document_count']} active/book nodes + {payload['historical_superseded_count']} superseded historical appendix nodes")


if __name__ == "__main__":
    main()
