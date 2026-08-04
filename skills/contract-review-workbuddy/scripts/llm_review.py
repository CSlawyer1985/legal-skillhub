#!/usr/bin/env python3
"""
LLM 审查模块 v4.0
调用大模型进行语义理解和深度审查
支持 OpenAI / 本地模型（Ollama）/ 兼容 API
v3.2 新增：按合同类型加载专用 LLM 提示词模板
v4.0 新增：按行业追加专项合规审查视角与术语上下文
"""

import json
import os
from pathlib import Path
import requests
from typing import Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# System Prompt 模板
SYSTEM_PROMPT = """你是一位资深的中国执业律师，专精于合同审查和风险管理。
请对以下合同进行风险审查，重点关注：

1. 合同主体的合法性
2. 合同条款的完整性和明确性
3. 权利义务的对等性
4. 违约责任的合理性
5. 争议解决方式的合法性
6. 是否有违反法律强制性规定的条款

审查标准：
- 以中国现行法律法规为依据（民法典、合同编、公司法、劳动合同法等）
- 参考最高人民法院司法解释和指导案例
- 考虑行业惯例和商业合理性
- 从{party_role}视角进行审查

输出要求（严格 JSON 格式）：
```json
{{
  "risks": [
    {{
      "risk_type": "主体风险|条款风险|金额风险|履行风险|争议解决风险|合规风险|其他风险",
      "severity": "严重|中等|一般|提示",
      "clause_ref": "条款编号或页码（如：第3条、第5页）",
      "text_snippet": "原文引用（50字内）",
      "title": "风险标题（简洁描述）",
      "description": "风险描述（通俗易懂）",
      "legal_basis": "法律依据（法条）",
      "suggestion": "修改建议（具体可行）",
      "template": "推荐的标准表述（可选）"
    }}
  ],
  "missing_clauses": ["缺失的必备条款列表"],
  "special_notes": ["特别提示信息"]
}}
```

如果没有发现任何风险，返回：
```json
{{
  "risks": [],
  "missing_clauses": [],
  "special_notes": ["合同条款相对完善，未发现明显风险"]
}}
```

重要：
1. 只输出 JSON，不要输出其他文字
2. 每个风险点必须包含完整信息
3. 修改建议必须具体可行，给出推荐的标准表述
4. 法律引用必须准确"""

USER_PROMPT_TEMPLATE = """请审查以下合同：

合同类型：{contract_type}
审查视角：{party_role}

合同内容：
{contract_text}

请按 JSON 格式输出审查结果。"""

# v3.2 合同类型与专用提示词文件映射
CONTRACT_TYPE_PROMPT_FILES = {
    '股权转让合同': 'equity_transfer.md',
    '增资扩股协议': 'capital_increase.md',
    '对赌协议': 'valuation_adjustment.md',
    'NDA保密协议': 'nda.md',
    '知识产权许可协议': 'ip_license.md',
    '建设工程合同': 'construction.md',
    '采购框架协议': 'procurement_framework.md',
}

# v4.0 行业专项审查视角（追加到 system prompt 末尾）
INDUSTRY_FOCUS = {
    'medical': (
        "医疗/医药行业", [
            "医疗器械注册证、经营许可证、生产许可证等资质有效性",
            "药品/器械采购的两票制、集中带量采购、医保支付政策合规",
            "临床试验的伦理审查、受试者知情同意、数据归属与保险",
            "医疗数据与患者个人信息（敏感个人信息）处理合规",
            "冷链运输、不良事件报告、召回与追溯责任划分",
            "反商业贿赂与医药合规（禁止学术推广变相返利）",
        ]),
    'construction': (
        "建筑/建设工程行业", [
            "施工资质等级、安全生产许可证、项目负责人资格匹配",
            "违法分包、转包、挂靠导致合同无效的风险",
            "工程款支付节点、进度款比例、农民工工资专用账户",
            "工期顺延、签证变更、索赔时效与证据留存",
            "质量保证金比例与返还期限（不得超过3%）",
            "安全生产责任划分、意外伤害保险、第三方责任",
        ]),
    'cross_border': (
        "跨境电商/国际贸易行业", [
            "国际贸易术语（Incoterms 2020）与风险转移节点",
            "适用法律、管辖与仲裁地选择，CISG 排除与否",
            "信用证/托收/电汇结算方式与单据一致性",
            "出口管制、制裁名单、原产地规则与关税合规",
            "外汇管制、跨境资金结算与税务合规",
            "跨境数据传输、平台规则（VAT/EPR）与知识产权海外布局",
        ]),
    'internet': (
        "互联网/软件行业", [
            "软件著作权与源代码归属、开源组件许可（GPL 传染性）",
            "SLA 可用性承诺、故障赔偿与责任上限合理性",
            "个人信息告知同意、最小必要、敏感信息单独同意",
            "数据出境安全评估/标准合同、委托处理协议（DPA）",
            "平台责任与避风港、格式条款提示说明义务、自动续费",
            "生成式 AI 备案、深度合成标识、训练数据合法来源",
        ]),
}

# v4.0 行业专项提示词补充模板
INDUSTRY_PROMPT_SUFFIX = """

---

## 行业专项审查要求（{industry_name}）

本合同属于{industry_name}，除通用审查要点外，必须额外重点核查以下专项合规事项：

{focus_list}

要求：
1. 行业专项风险须在 risk_type 中标注为「合规风险」或对应类型，并在 title 前加「[行业]」前缀
2. 法律依据须引用该行业的专门法规、部门规章或行业标准，不得只引用《民法典》
3. 修改建议须符合该行业监管实践，给出可直接落地的条款表述"""


class LLMReviewer:
    """LLM 审查器"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = None,
                 api_base: Optional[str] = None, timeout: int = 120,
                 backend: str = "auto"):
        """
        初始化 LLM 审查器
        
        Args:
            api_key: API 密钥（默认从环境变量读取）
            model: 使用的模型名称（默认自动检测）
            api_base: API 基础 URL（默认从环境变量读取）
            timeout: 请求超时时间（秒）
            backend: 后端类型（auto/openai/ollama/local）
        """
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY', '')
        self.model = model or os.environ.get('OPENAI_MODEL', 'gpt-4')
        self.api_base = api_base or os.environ.get('OPENAI_API_BASE', 'https://api.openai.com/v1')
        self.timeout = timeout
        self.backend = backend
        self.system_prompt = SYSTEM_PROMPT
        
        # 自动检测后端
        if self.backend == "auto":
            self.backend = self._detect_backend()
        
        logger.info(f"LLM 后端: {self.backend}, 模型: {self.model}")
    
    def _detect_backend(self) -> str:
        """自动检测可用的 LLM 后端"""
        # 1. 检查 OpenAI
        if self.api_key:
            return "openai"
        
        # 2. 检查 Ollama（本地模型）
        try:
            resp = requests.get("http://localhost:11434/api/tags", timeout=3)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                if models:
                    # 自动选择第一个可用模型
                    self.model = models[0]["name"]
                    return "ollama"
        except Exception:
            pass
        
        # 3. 检查本地 LLM 服务（如 LM Studio、vLLM 等）
        for port in [1234, 8080, 5000]:
            try:
                resp = requests.get(f"http://localhost:{port}/v1/models", timeout=2)
                if resp.status_code == 200:
                    self.api_base = f"http://localhost:{port}/v1"
                    data = resp.json()
                    if data.get("data"):
                        self.model = data["data"][0]["id"]
                        return "openai"
            except Exception:
                pass
        
        return "none"
    
    def review(self, contract_text: str, contract_type: str = "",
               party_role: str = "双方", structure: Dict = None,
               industry: str = "") -> Dict[str, Any]:
        """
        调用 LLM 进行审查
        
        Args:
            contract_text: 合同全文
            contract_type: 合同类型
            party_role: 审查视角（甲方/乙方/双方）
            structure: 合同结构
            industry: v4.0 行业代码（medical/construction/cross_border/internet）
            
        Returns:
            审查结果字典
        """
        if self.backend == "none":
            logger.warning("未检测到可用的 LLM 后端，跳过 LLM 审查")
            return {
                'risks': [],
                'missing_clauses': [],
                'special_notes': [
                    'LLM 审查不可用（未检测到 OpenAI API 或本地模型），仅使用规则引擎结果',
                    '如需启用 LLM 审查，请安装 Ollama 或设置 OPENAI_API_KEY 环境变量'
                ]
            }
        
        # v3.2 加载专用提示词模板
        system_prompt = self._load_contract_specific_prompt(contract_type)
        # 填充审查视角占位符（通用模板含 {party_role}，专用模板通常不含）
        system_prompt = self._fill_prompt_placeholders(system_prompt, party_role)
        # v4.0 追加行业专项审查要求
        system_prompt += self._build_industry_suffix(industry)
        
        # 截断过长文本
        max_length = 15000
        if len(contract_text) > max_length:
            contract_text = contract_text[:max_length] + "\n...（合同过长，已截断）"
        
        user_prompt = USER_PROMPT_TEMPLATE.format(
            contract_type=contract_type or "未指定",
            party_role=party_role,
            contract_text=contract_text,
        )
        
        try:
            if self.backend == "ollama":
                result = self._call_ollama(system_prompt, user_prompt)
            else:
                result = self._call_openai(system_prompt, user_prompt)
            return self._parse_response(result)
        except Exception as e:
            logger.error(f"LLM 审查失败: {e}")
            return {
                'risks': [],
                'missing_clauses': [],
                'special_notes': [f'LLM 审查失败: {str(e)}，仅使用规则引擎结果']
            }
    
    def _load_contract_specific_prompt(self, contract_type: str) -> str:
        """v3.2 加载合同类型专用 LLM 提示词模板"""
        if not contract_type or contract_type not in CONTRACT_TYPE_PROMPT_FILES:
            return self.system_prompt
        
        prompt_file = CONTRACT_TYPE_PROMPT_FILES[contract_type]
        prompts_dir = Path(__file__).parent.parent / 'references' / 'llm_prompts'
        prompt_path = prompts_dir / prompt_file
        
        if not prompt_path.exists():
            logger.debug(f"专用提示词文件不存在: {prompt_path}")
            return self.system_prompt
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"加载 {contract_type} 专用提示词模板")
            return content
        except Exception as e:
            logger.warning(f"加载专用提示词失败: {e}")
            return self.system_prompt
    
    @staticmethod
    def _fill_prompt_placeholders(prompt: str, party_role: str) -> str:
        """填充提示词中的审查视角占位符，并还原 JSON 示例的转义大括号"""
        if '{party_role}' in prompt:
            prompt = prompt.replace('{party_role}', party_role or '双方')
        # 模板中 JSON 示例使用 {{ }} 转义，此处还原为单层大括号
        if '{{' in prompt or '}}' in prompt:
            prompt = prompt.replace('{{', '{').replace('}}', '}')
        return prompt
    
    def _build_industry_suffix(self, industry: str) -> str:
        """v4.0 构建行业专项审查提示词补充段"""
        try:
            from rule_engine import normalize_industry
        except ImportError:
            try:
                from .rule_engine import normalize_industry
            except ImportError:
                normalize_industry = None
        
        code = normalize_industry(industry) if normalize_industry else (industry or '').strip().lower()
        if not code or code not in INDUSTRY_FOCUS:
            return ''
        
        industry_name, focus_points = INDUSTRY_FOCUS[code]
        focus_list = '\n'.join(f"{i}. {p}" for i, p in enumerate(focus_points, 1))
        logger.info(f"启用 {industry_name} 专项审查视角")
        return INDUSTRY_PROMPT_SUFFIX.format(
            industry_name=industry_name,
            focus_list=focus_list,
        )
    
    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """调用 OpenAI 兼容 API"""
        # 优先使用 OpenAI SDK
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.api_base,
                timeout=self.timeout,
            )
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=4000,
            )
            
            return response.choices[0].message.content
        except ImportError:
            pass
        
        # 回退到直接 HTTP 请求
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 4000,
        }
        
        resp = requests.post(url, headers=headers, json=data, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    
    def _call_ollama(self, system_prompt: str, user_prompt: str) -> str:
        """调用 Ollama 本地模型"""
        url = "http://localhost:11434/api/chat"
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 4000,
            }
        }
        
        resp = requests.post(url, json=data, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()["message"]["content"]
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析 LLM 响应"""
        # 尝试提取 JSON
        if '```json' in response:
            json_str = response.split('```json')[1].split('```')[0]
        elif '```' in response:
            json_str = response.split('```')[1].split('```')[0]
        else:
            json_str = response
        
        # 清理
        json_str = json_str.strip()
        
        try:
            data = json.loads(json_str)
            return {
                'risks': data.get('risks', []),
                'missing_clauses': data.get('missing_clauses', []),
                'special_notes': data.get('special_notes', []),
            }
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            return {
                'risks': [],
                'missing_clauses': [],
                'special_notes': [f'解析失败: {str(e)}']
            }


def main():
    """命令行入口"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python llm_review.py <合同文本文件> [合同类型] [审查视角]")
        sys.exit(1)
    
    text_path = sys.argv[1]
    contract_type = sys.argv[2] if len(sys.argv) > 2 else ""
    party_role = sys.argv[3] if len(sys.argv) > 3 else "双方"
    
    with open(text_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    reviewer = LLMReviewer()
    result = reviewer.review(text, contract_type, party_role)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
