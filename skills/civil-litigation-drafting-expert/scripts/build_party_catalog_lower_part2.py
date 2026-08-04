#!/usr/bin/env python3
"""Build the party-filing catalog from lower-volume OCR file 2.

The source file contains court documents on PDF file pages 1-195. Those pages
are deliberately excluded. Import begins at file page 196, where Part II
"当事人参考民事诉讼文书样式" starts. Textbook form bodies are not copied.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path


FORMS = [
    {
        "code": "JUR-001", "chapter": "管辖", "file_page": 199, "printed_page": 1252,
        "name": "异议书（对管辖权提出异议用）", "short_name": "管辖权异议书",
        "function": "请求第一审人民法院审查其对已受理案件是否具有管辖权，并在异议成立时移送有管辖权的人民法院。",
        "cases": ["被告认为受诉人民法院对本案无管辖权的第一审民事案件", "存在地域、级别、专属、协议或其他管辖争议的案件"],
        "procedure": ["第一审", "提交答辩状期间", "管辖权异议审查"],
        "conditions": ["人民法院已受理案件", "异议人具有提出管辖权异议的资格", "尚在提交答辩状期间", "能够指出具体无管辖权理由及应受移送法院"],
        "maker": ["通常为被告；其他依法有权提出管辖异议的当事人须单独核验资格"],
        "recipient": ["受诉第一审人民法院；对方当事人为原告及其他相关诉讼当事人"],
        "court": ["已经受理案件的第一审人民法院"],
        "basis": ["《中华人民共和国民事诉讼法》（2023年修正）第一百三十条第一款", "民事诉讼法及其司法解释中与具体管辖连接点、专属管辖、协议管辖有关的现行规定", "《最高人民法院关于部分民事案件管辖适用法律有关问题的批复》（法释〔2025〕15号，2025年12月31日起施行）"],
        "focus": ["异议人资格和提出时点", "受诉法院管辖连接点是否成立", "是否存在专属管辖或有效管辖协议", "建议移送法院是否确有管辖权", "异议是否针对管辖而非实体争议"],
        "time": ["应在提交答辩状期间提出；必须依据送达日期重新计算并保留送达凭证"],
        "burden": ["异议人应对否定受诉法院管辖的事实及支持其他法院管辖的连接事实提供材料", "依法应由法院依职权审查的专属或级别管辖事项仍应提出清晰线索"],
        "evidence": ["起诉状副本、应诉通知和送达凭证", "住所地、经常居住地、合同履行地、侵权地等连接点证据", "完整合同及管辖协议", "登记信息和专属管辖标的材料"],
        "structure": ["标题", "异议人及诉讼参加人信息", "案号和案由", "明确请求移送的法院", "管辖事实", "管辖规则与适用理由", "证据清单", "致送法院", "签章日期和副本附件"],
        "review": ["审查资格和期限", "识别法定管辖规则及优先顺序", "核实连接事实和协议效力", "排除专属管辖冲突", "确定驳回或移送及救济告知"],
        "tips": ["先写清应适用哪一条管辖规则，再写连接事实和证据", "请求中明确拟移送法院，不使用‘移送有管辖权法院’的空泛表述", "实体抗辩与管辖理由分开，避免提前暴露无关策略"],
    },
    {
        "code": "JUR-002", "chapter": "管辖", "file_page": 201, "printed_page": 1254,
        "name": "民事上诉状（对驳回管辖权异议裁定提起上诉用）", "short_name": "管辖权异议裁定上诉状",
        "function": "对第一审人民法院驳回管辖权异议的裁定提起上诉，请求上一级人民法院撤销裁定并依法确定或移送管辖。",
        "cases": ["当事人不服驳回管辖权异议裁定的民事案件", "境内或在中国领域内无住所的当事人依法提起裁定上诉的案件"],
        "procedure": ["管辖权异议裁定上诉", "第二审程序", "裁定上诉"],
        "conditions": ["已收到驳回管辖权异议的第一审裁定", "上诉人是有权提起上诉的当事人", "上诉期尚未届满", "能够提出具体撤销和移送请求"],
        "maker": ["不服驳回管辖权异议裁定的当事人"],
        "recipient": ["通过原审人民法院提出，受理审查机关为上一级人民法院；被上诉人为对方当事人"],
        "court": ["上一级人民法院；上诉状通常通过原审人民法院递交"],
        "basis": ["《中华人民共和国民事诉讼法》（2023年修正）第一百五十七条第一款第二项、第二款", "《中华人民共和国民事诉讼法》（2023年修正）第一百七十一条第二款、第一百七十二条、第一百七十三条", "在中华人民共和国领域内没有住所的当事人还须核验第二百八十六条", "《最高人民法院关于部分民事案件管辖适用法律有关问题的批复》（法释〔2025〕15号，2025年12月31日起施行）"],
        "focus": ["裁定是否属于可上诉裁定", "送达日和上诉期限", "上诉请求是否与原异议一致且明确", "原审对连接事实、专属管辖或协议效力的认定是否错误", "递交路径和副本数量"],
        "time": ["境内一般情形为裁定书送达之日起十日内；在中国领域内没有住所的当事人适用期限须按现行法单独核验，教材提示为三十日"],
        "burden": ["上诉人应指出原裁定事实认定或法律适用错误，并提交原裁定、送达凭证和管辖连接证据", "新证据应说明未在异议阶段提交的原因及其证明目的"],
        "evidence": ["驳回管辖权异议裁定书", "裁定送达凭证", "原管辖权异议书及证据", "支持拟移送法院管辖的新证据", "主体和授权材料"],
        "structure": ["标题", "上诉人与被上诉人信息及原审地位", "原审法院、案号、案由和裁定日期", "上诉请求", "事实与理由", "法律适用分析", "致送法院", "副本和证据附件", "签章日期"],
        "review": ["确认可上诉性、资格和期限", "复核受诉法院管辖依据", "审查原裁定回应是否完整", "判断撤销、维持或确定移送", "核对后续审理衔接"],
        "tips": ["第一段即指出原裁定的核心错误类型", "围绕管辖连接点组织，不把实体胜败写成上诉主轴", "逐项对应原裁定理由，附送达凭证并独立计算上诉期限"],
    },
    {
        "code": "REC-001", "chapter": "回避", "file_page": 205, "printed_page": 1258,
        "name": "申请书（申请回避用）", "short_name": "回避申请书",
        "function": "请求人民法院依法决定具有法定回避情形的审判人员或其他适用回避规则的人员退出本案相关工作。",
        "cases": ["审判人员、书记员、翻译人员、鉴定人、勘验人等可能存在法定回避事由的民事案件", "执行程序中依法适用回避规则的事项"],
        "procedure": ["审理或执行中的回避申请", "法庭辩论终结前的程序申请"],
        "conditions": ["被申请人属于法定回避对象", "存在具体法定回避事实", "申请人说明理由并在法定阶段提出", "申请不是仅基于对裁判倾向的不满"],
        "maker": ["案件当事人及依法有权提出回避申请的主体"],
        "recipient": ["正在审理或执行案件的人民法院；被申请回避人为具体审判或辅助人员"],
        "court": ["正在处理本案并对该回避事项有决定权限的人民法院"],
        "basis": ["《中华人民共和国民事诉讼法》（2023年修正）第四十七条、第四十八条", "回避决定权限、决定期限及复议须结合现行民事诉讼法后续条款和民诉法解释核验"],
        "focus": ["被申请人是否属于回避对象", "事实是否落入法定事由或足以影响公正审理", "申请提出时点及迟延原因", "证据来源是否合法可靠", "紧急措施期间是否应暂停参与"],
        "time": ["原则上在案件开始审理时提出；审理开始后才知道回避事由的，可以在法庭辩论终结前提出"],
        "burden": ["申请人应具体说明回避事实并提供初步材料或可核查线索", "对违反规定会见、请客送礼或利害关系等事实，不得仅作无依据推测"],
        "evidence": ["被申请人的身份和参与本案材料", "亲属、利害关系或既往参与材料", "接触、会见、利益往来或公开表达的合法证据", "获知回避事由的时间证明"],
        "structure": ["标题", "申请人信息", "案件信息", "被申请回避人的姓名和诉讼职务", "请求事项", "具体事实和法定事由", "证据及来源", "获知时间和提出时点", "致送法院", "签章日期"],
        "review": ["识别回避对象", "审查法定事由和证据线索", "核对提出时点", "确定决定权限并处理紧急措施", "作出决定并告知复议权利"],
        "tips": ["只陈述可核验事实，避免情绪化指责", "将‘可能影响公正审理’与具体关系、行为和案件联系起来", "明确何时获知事由，以解释申请时点"],
    },
]


def extract_pages(pdf: Path) -> list[str]:
    try:
        from pypdf import PdfReader
        return [(page.extract_text() or "") for page in PdfReader(str(pdf)).pages]
    except Exception:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "source.txt"
            subprocess.run(["pdftotext", "-layout", str(pdf), str(output)], check=True)
            return output.read_text(errors="ignore").split("\f")[:-1]


def normalize(text: str) -> str:
    return re.sub(r"\s+", "", text).replace("笫", "第").replace("栽定", "裁定")


def book_basis(pages: list[str], form_page: int, explanation_page: int) -> str:
    compact = normalize("\n".join(pages[form_page - 1:explanation_page]))
    match = re.search(r"【说明】(.{0,900}?)(?:【应用】|【法律依据】)", compact)
    return match.group(1)[:900] if match else "OCR未完整提取说明，须回到标注页人工核对"


def make_node(spec: dict, pages: list[str]) -> dict:
    explanation_page = spec["file_page"] + 1
    return {
        "document_id": f"PARTY-L2-{spec['code']}",
        "document_name": spec["name"],
        "canonical_name": spec["short_name"],
        "document_role": "party_filing",
        "document_function": spec["function"],
        "applicable_cases": spec["cases"],
        "applicable_procedure": spec["procedure"],
        "start_conditions": spec["conditions"],
        "applicant_or_maker": spec["maker"],
        "counterparty_or_recipient": spec["recipient"],
        "competent_court": spec["court"],
        "book_original_basis": [book_basis(pages, spec["file_page"], explanation_page)],
        "current_legal_basis": spec["basis"],
        "legal_update_note": "教材说明仅作历史和定位线索；具体案件须按行为发生时点复核官方现行法律、司法解释和法院程序要求。",
        "judicial_interpretations": ["具体案件生成时，按争点从最高人民法院现行司法解释中核验并记录条号；当前节点不以教材OCR替代官方原文"],
        "case_authorities": ["未预置案例；仅在具体案件需要时检索最高人民法院指导性案例或人民法院案例库并做可比性分析"],
        "court_focus": spec["focus"],
        "submission_or_making_time": spec["time"],
        "burden_of_proof": spec["burden"],
        "evidence_requirements": spec["evidence"],
        "risk_analysis": ["法定期间届满可能导致程序权利丧失", "主体、法院或请求对象错误可能导致不予处理", "关键事实无证据会使申请或上诉被驳回", "教材条号虽按2023年民诉法更新，正式提交前仍须复核官方现行文本"],
        "logical_structure": spec["structure"],
        "smart_template_fields": ["filing.title", "party[].identity_and_role", "case.original_court_number_and_cause", "request[].specific_result", "fact[].status_and_source", "law[].name_article_purpose_condition_status", "evidence[].name_fact_source", "court.recipient", "deadline.trigger_and_calculation", "signature.real_party_or_authorized_agent", "attachments.count_and_copies"],
        "court_review_logic": spec["review"],
        "lawyer_writing_tips": spec["tips"],
        "ai_generation_flow": ["识别案件与当前程序", "匹配文书触发条件", "收集阻断级缺失信息", "复算期限并确定受理法院", "建立请求—事实—证据—法律映射", "核验官方现行法", "生成案件专属智能文书", "执行一致性、完整性、法律、逻辑、引用和法院实践校验"],
        "automatic_validation_rules": ["document_role_is_party_filing", "party_identity_and_roles_consistent", "case_number_and_court_match_source_document", "request_is_specific_and_procedurally_available", "deadline_has_trigger_date_evidence_and_calculation", "each_material_fact_has_source", "law_citations_are_official_and_current", "attachments_exist_and_copy_count_is_checked", "no_court_seal_or_fabricated_judicial_signature"],
        "common_errors": ["标题与程序不匹配", "当事人诉讼地位沿用错误", "请求不具体", "事实与程序要件无对应", "未附送达或原裁定材料", "未计算期限", "引用教材OCR而未核对官方原文"],
        "excellent_example_policy": "不照抄教材样式。优秀示范必须以经核验的案件事实为基础，逐项解释写作理由，并将隐私信息去标识化；没有事实时只生成变量模板。",
        "source_locator": {
            "source_edition": "第二版",
            "volume": "下册",
            "source_file_part": 2,
            "pdf_file_page": spec["file_page"],
            "scan_global_page": 206 + spec["file_page"],
            "printed_book_page": spec["printed_page"],
            "chapter": spec["chapter"],
            "coverage_note": "仅导入PDF文件页196以后‘第二部分 当事人参考民事诉讼文书样式’；前195页法院文书明确排除",
        },
        "validation_status": "book_verified",
        "version": "1.0.0",
        "effective_from": None,
        "supersedes": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if not args.source.is_file():
        raise SystemExit(f"Source PDF not found: {args.source}")
    pages = extract_pages(args.source)
    if len(pages) != 206:
        raise SystemExit(f"Expected 206 PDF pages, got {len(pages)}")
    if "当事人参考民事诉讼" not in pages[195]:
        raise SystemExit("Expected party-reference section to start on PDF file page 196")
    documents = [make_node(spec, pages) for spec in FORMS]
    payload = {
        "catalog_name": "中国民事诉讼文书AI专家—当事人参考文书累计目录",
        "scope": "第二版下册第二部分‘当事人参考民事诉讼文书样式’",
        "source": {
            "title": "民事诉讼文书样式应用及法律依据（第二版）",
            "volume": "下册",
            "source_file_part": 2,
            "file": str(args.source),
            "pdf_pages": 206,
            "included_pdf_pages": "196—206",
            "excluded_pdf_pages": "1—195（人民法院制作文书样式）",
            "coverage": "第二部分标题、管辖2种、回避1种；回避章在本文件末尾未完",
        },
        "limitations": ["当前附件在当事人参考文书部分只覆盖3种文书", "回避章及后续章节须由后续分卷接续", "教材OCR不作为最终法律引用证明", "教材样式正文未复制入数据库"],
        "document_count": len(documents),
        "documents": documents,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {len(documents)} party-filing nodes to {args.output}")


if __name__ == "__main__":
    main()
