#!/usr/bin/env python3
"""
CCPA/CPRA Compliance Checker — 美国加州消费者隐私法合规检查工具

使用统一的 compliance_core 模块，提供标准化的 CLI、报告输出和检查引擎。
纯本地运行，零外部依赖。
"""

import sys
import os

# 确保 compliance_core 可导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from compliance_core import UnifiedCLI, CheckEngine, CheckResult, Severity


class CCPAEngine(CheckEngine):
    """CCPA/CPRA 合规检查引擎"""

    def __init__(self):
        super().__init__(
            tool_name="CCPA-Compliance",
            regulation="California Consumer Privacy Act (CCPA) / CPRA"
        )
        self._register_all()

    def _register_all(self):
        """注册所有检查项和场景"""
        
        # 注册检查项
        self.register_checker("applicability", self._check_applicability)
        self.register_checker("notice", self._check_notice)
        self.register_checker("consumer_rights", self._check_consumer_rights)
        self.register_checker("opt_out", self._check_opt_out)
        self.register_checker("sensitive_info", self._check_sensitive_info)
        self.register_checker("data_sales", self._check_data_sales)
        self.register_checker("service_provider", self._check_service_provider)
        self.register_checker("verification", self._check_verification)
        self.register_checker("non_discrimination", self._check_non_discrimination)
        self.register_checker("recordkeeping", self._check_recordkeeping)
        self.register_checker("data_security", self._check_data_security)
        self.register_checker("response_timelines", self._check_response_timelines)

        # 注册场景
        self.register_scenario("standard_business", "标准商业场景",
            ["applicability", "notice", "consumer_rights", "opt_out",
             "non_discrimination", "recordkeeping"])
        self.register_scenario("data_selling", "数据销售场景",
            ["applicability", "notice", "opt_out", "data_sales",
             "service_provider", "non_discrimination"])
        self.register_scenario("sensitive_data", "敏感数据处理",
            ["applicability", "notice", "sensitive_info", "data_security",
             "consumer_rights", "verification"])
        self.register_scenario("full_audit", "全面审计",
            ["applicability", "notice", "consumer_rights", "opt_out",
             "sensitive_info", "data_sales", "service_provider",
             "verification", "non_discrimination", "recordkeeping",
             "data_security", "response_timelines"])

    def _check_applicability(self, data: dict) -> CheckResult:
        """检查企业是否适用CCPA"""
        gross_revenue = data.get("gross_revenue", 0)
        data_volume = data.get("data_volume", "")
        sells_data = data.get("sells_data", False)

        issues = []
        if isinstance(gross_revenue, (int, float)) and gross_revenue < 25000000:
            issues.append("年收入低于2500万美元，需检查其他条件")

        return CheckResult(
            check_id="applicability",
            description="企业适用性检查 - 判断是否受CCPA管辖",
            severity=Severity.PASS if len(issues) == 0 else Severity.WARN,
            passed=len(issues) == 0,
            details="；".join(issues) if issues else "企业满足CCPA管辖条件",
            recommendation="核实年收入、数据量和数据销售情况",
            regulation_ref="CCPA §1798.140"
        )

    def _check_notice(self, data: dict) -> CheckResult:
        """检查隐私通知义务"""
        has_privacy_policy = data.get("has_privacy_policy", False)
        categories_collected = data.get("categories_collected", [])
        has_collection_notice = data.get("has_collection_notice", False)

        issues = []
        if not has_privacy_policy:
            issues.append("未提供隐私政策")
        if not categories_collected:
            issues.append("未明示收集的数据类别")
        if not has_collection_notice:
            issues.append("未提供收集通知")

        return CheckResult(
            check_id="notice",
            description="告知义务检查 - 隐私通知与数据收集告知",
            severity=Severity.PASS if len(issues) == 0 else Severity.FAIL,
            passed=len(issues) == 0,
            details="；".join(issues) if issues else "告知义务履行完整",
            recommendation="确保在数据收集点提供清晰的隐私通知",
            regulation_ref="CCPA §1798.100(b)"
        )

    def _check_consumer_rights(self, data: dict) -> CheckResult:
        """检查消费者权利保障"""
        has_rights_mechanism = data.get("has_rights_mechanism", False)
        has_know_process = data.get("has_know_process", False)
        has_delete_process = data.get("has_delete_process", False)
        has_correct_process = data.get("has_correct_process", False)

        missing = []
        if not has_rights_mechanism: missing.append("权利行使机制")
        if not has_know_process: missing.append("知情权流程")
        if not has_delete_process: missing.append("删除权流程")
        if not has_correct_process: missing.append("更正权流程")

        return CheckResult(
            check_id="consumer_rights",
            description="消费者权利保障检查",
            severity=Severity.PASS if len(missing) == 0 else Severity.FAIL,
            passed=len(missing) == 0,
            details="缺失: " + "、".join(missing) if missing else "消费者权利保障机制完整",
            recommendation="建立完整的消费者权利请求处理流程（15天内响应）",
            regulation_ref="CCPA §1798.110, §1798.105"
        )

    def _check_opt_out(self, data: dict) -> CheckResult:
        """检查选择退出机制"""
        sells_data = data.get("sells_data", False)
        has_opt_out = data.get("has_opt_out", False)
        opt_out_method = data.get("opt_out_method", "")

        issues = []
        if sells_data and not has_opt_out:
            issues.append("销售数据但未提供选择退出机制")
        if sells_data and not opt_out_method:
            issues.append("未明确选择退出方式")

        return CheckResult(
            check_id="opt_out",
            description="选择退出机制检查 - Do Not Sell/Share My Personal Information",
            severity=Severity.PASS if len(issues) == 0 else Severity.FAIL,
            passed=len(issues) == 0,
            details="；".join(issues) if issues else "选择退出机制完善",
            recommendation="在网站页脚提供清晰的 Do Not Sell or Share 链接",
            regulation_ref="CCPA §1798.120"
        )

    def _check_sensitive_info(self, data: dict) -> CheckResult:
        """检查敏感信息处理"""
        processes_sensitive = data.get("processes_sensitive", False)
        has_limited_use = data.get("has_limited_use", False)
        opt_out_sensitive = data.get("opt_out_sensitive", False)

        issues = []
        if processes_sensitive and not has_limited_use:
            issues.append("处理敏感信息但未限制使用目的")
        if processes_sensitive and not opt_out_sensitive:
            issues.append("未提供敏感信息选择退出")

        return CheckResult(
            check_id="sensitive_info",
            description="敏感个人信息处理检查",
            severity=Severity.PASS if len(issues) == 0 else Severity.FAIL,
            passed=len(issues) == 0,
            details="；".join(issues) if issues else "敏感信息处理合规",
            recommendation="实施敏感信息使用的目的限制和选择退出机制",
            regulation_ref="CPRA §1798.121"
        )

    def _check_data_sales(self, data: dict) -> CheckResult:
        """检查数据销售/共享合规"""
        sells_data = data.get("sells_data", False)
        has_contract = data.get("has_contract", False)
        has_audit_rights = data.get("has_audit_rights", False)

        issues = []
        if sells_data and not has_contract:
            issues.append("数据销售但无合同约束")
        if sells_data and not has_audit_rights:
            issues.append("未保留审计权利")

        return CheckResult(
            check_id="data_sales",
            description="数据销售与共享合规检查",
            severity=Severity.PASS if len(issues) == 0 else Severity.FAIL,
            passed=len(issues) == 0,
            details="；".join(issues) if issues else "数据销售管理合规",
            recommendation="与第三方签订数据处理协议并保留审计权",
            regulation_ref="CCPA §1798.140(t)"
        )

    def _check_service_provider(self, data: dict) -> CheckResult:
        """检查服务提供商管理"""
        has_sp_contracts = data.get("has_sp_contracts", False)
        has_usage_limits = data.get("has_usage_limits", False)
        has_subprocessing_control = data.get("has_subprocessing_control", False)

        issues = []
        if not has_sp_contracts: issues.append("与服务提供商无书面合同")
        if not has_usage_limits: issues.append("未限制服务提供商的数据使用范围")

        return CheckResult(
            check_id="service_provider",
            description="服务提供商管理检查",
            severity=Severity.PASS if len(issues) == 0 else Severity.FAIL,
            passed=len(issues) == 0,
            details="；".join(issues) if issues else "服务提供商管理合规",
            recommendation="与服务提供商签订合同并限制其数据使用目的",
            regulation_ref="CCPA §1798.140(ag)"
        )

    def _check_verification(self, data: dict) -> CheckResult:
        """检查验证程序"""
        has_verification = data.get("has_verification", False)
        has_tiered_verification = data.get("has_tiered_verification", False)
        has_denial_process = data.get("has_denial_process", False)

        issues = []
        if not has_verification: issues.append("无身份验证程序")
        if not has_denial_process: issues.append("无拒绝请求的处理流程")

        return CheckResult(
            check_id="verification",
            description="消费者身份验证程序检查",
            severity=Severity.PASS if len(issues) == 0 else Severity.FAIL,
            passed=len(issues) == 0,
            details="；".join(issues) if issues else "验证程序合规",
            recommendation="建立分级身份验证程序，高风险请求需更严格验证",
            regulation_ref="CCPA §1798.145(i)"
        )

    def _check_non_discrimination(self, data: dict) -> CheckResult:
        """检查非歧视原则"""
        denies_service = data.get("denies_service", False)
        charges_different = data.get("charges_different", False)
        provides_different_quality = data.get("provides_different_quality", False)

        issues = []
        if denies_service: issues.append("拒绝为行使权利的消费者提供服务")
        if charges_different: issues.append("对行使权利的消费者收取不同价格")
        if provides_different_quality: issues.append("提供不同质量的服务")

        return CheckResult(
            check_id="non_discrimination",
            description="非歧视原则检查",
            severity=Severity.PASS if len(issues) == 0 else Severity.FAIL,
            passed=len(issues) == 0,
            details="；".join(issues) if issues else "未发现歧视性做法",
            recommendation="不得因消费者行使CCPA权利而歧视对待",
            regulation_ref="CCPA §1798.125"
        )

    def _check_recordkeeping(self, data: dict) -> CheckResult:
        """检查记录保存义务"""
        has_requests_log = data.get("has_requests_log", False)
        has_training_records = data.get("has_training_records", False)
        keeps_24_months = data.get("keeps_24_months", False)

        issues = []
        if not has_requests_log: issues.append("未记录消费者请求")
        if not keeps_24_months: issues.append("记录保存不足24个月")

        return CheckResult(
            check_id="recordkeeping",
            description="记录保存义务检查",
            severity=Severity.PASS if len(issues) == 0 else Severity.FAIL,
            passed=len(issues) == 0,
            details="；".join(issues) if issues else "记录保存合规",
            recommendation="保存消费者请求记录至少24个月",
            regulation_ref="CCPA §1798.130(a)"
        )

    def _check_data_security(self, data: dict) -> CheckResult:
        """检查数据安全措施"""
        has_encryption = data.get("has_encryption", False)
        has_access_control = data.get("has_access_control", False)
        has_breach_response = data.get("has_breach_response", False)
        has_employee_training = data.get("has_employee_training", False)

        issues = []
        if not has_encryption: issues.append("未实施数据加密")
        if not has_access_control: issues.append("访问控制不足")
        if not has_breach_response: issues.append("无数据泄露响应计划")
        if not has_employee_training: issues.append("员工培训不足")

        return CheckResult(
            check_id="data_security",
            description="数据安全措施检查",
            severity=Severity.FAIL if not has_encryption else Severity.WARN,
            passed=has_encryption and has_access_control,
            details="缺失: " + "、".join(issues) if issues else "安全措施完善",
            recommendation="实施合理的安全措施保护个人信息",
            regulation_ref="CCPA §1798.81.5"
        )

    def _check_response_timelines(self, data: dict) -> CheckResult:
        """检查响应时限"""
        response_days = data.get("response_days", 45)
        has_extension_notice = data.get("has_extension_notice", False)
        appeal_process = data.get("appeal_process", False)

        issues = []
        if response_days > 45: issues.append(f"响应时限({response_days}天)超过法定45天")
        if response_days > 45 and not has_extension_notice:
            issues.append("超期未提供延长期限通知")

        return CheckResult(
            check_id="response_timelines",
            description="消费者请求响应时限检查",
            severity=Severity.PASS if len(issues) == 0 else Severity.FAIL,
            passed=len(issues) == 0,
            details="；".join(issues) if issues else f"响应时限合规（{response_days}天内）",
            recommendation="确保在45天内响应消费者请求，必要时可延长15天",
            regulation_ref="CCPA §1798.130(a)(2)"
        )


def main():
    engine = CCPAEngine()
    cli = UnifiedCLI(
        tool_name="ccpa-check.py",
        description="CCPA/CPRA合规检查工具 — 美国加州消费者隐私法合规评估"
    )
    args = cli.parse_args()

    if args.list_scenarios:
        cli.list_scenarios(engine.get_scenarios())
        return

    report = engine.run(
        scenario=args.scenario,
        interactive=args.interactive,
    )

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            fmt = args.format if args.format != "text" else "json"
            if fmt == "json":
                f.write(report.to_dict())
            elif fmt == "markdown":
                from compliance_core.report_core import ReportGenerator
                f.write(ReportGenerator.to_markdown(report.to_dict()))
            else:
                f.write(str(report.to_dict()))
        print(f"\n✅ 报告已保存到: {args.output}")

    cli.print_report(report, fmt=args.format)


if __name__ == "__main__":
    main()
