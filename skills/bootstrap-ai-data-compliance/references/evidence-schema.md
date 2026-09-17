# 证据中台结构

## source_record

`source_id, external_id, source_type, title, version, effect_status, authority_level, official_url, file_location, locator, verification_date, verification_status, evidence_label, evidence_boundary`

## claim_record

`claim_id, claim, evidence_label, legal_effect, applicability_conditions, source_ids, locator, paths, events, risks, gates, documents, lawyer_review_status, claim_boundary`

## fact_record

`fact_id, fact, evidence_id, evidence_location, owner, confirmation_status, confirmed_by, confirmed_at, conflict_status, boundary`

## assessment_record

`assessment_id, source_id, theme, assessment_text, method, criteria, expected_evidence, applicability_status, legal_effect, customer_fact_status, assessment_status, risk_level, remediation_status, retest_status, lawyer_review_status`

## issue_record

`issue_id, fact_ids, assessment_ids, risk, evidence_label, severity, remediation, owner, due_date, retest_method, closure_evidence, status, lawyer_review_status`

多值引用使用分号分隔。外部项目原编号放入`external_id`或保留为记录主ID，不强制改写CL、LIT、GENAI等既有稳定编号。

