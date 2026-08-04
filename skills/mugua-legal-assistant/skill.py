import requests
from typing import Dict, Optional, List

# ====================== Skill基础配置 ======================
SKILL_META = {
    "name": "木瓜法律助手",
    "description": "对接木瓜法律API，提供法律咨询、案件要素提取/完整分析能力",
    "version": "1.0.4",
    "triggers": ["法律咨询", "案件分析", "要素提取"],
    "endpoint": "/skills/mugua-legal",
    "auth_type": "api_key",
    "config": {
        "base_url": "https://api.test.mugua.muguafabao.com/",
        "timeout": 30,  # 请求超时时间
        "max_file_size": 10 * 1024 * 1024  # 10MB文件大小限制
    }
}


def _resolve_base_url(event: Dict, context: Dict) -> str:
    """与 metadata.json 中 base_url 配置一致：优先运行时注入，否则用 SKILL_META 默认。"""
    creds = context.get("credentials") or {}
    ctx_cfg = context.get("config") or {}
    ev_cfg = event.get("config") or {}
    url = creds.get("base_url") or ctx_cfg.get("base_url") or ev_cfg.get("base_url")
    if not url:
        url = SKILL_META["config"]["base_url"]
    return url.rstrip("/") + "/"


# ====================== 法律咨询接口封装 ======================
def legal_chat_completions(
    prompt: str,
    base_url: str,
    stream: bool = False,
    enable_network: bool = False,
    api_key: str = ""
) -> Dict:
    """
    封装木瓜法律咨询接口 /v1/legal-chat/completions
    :param prompt: 法律咨询问题
    :param stream: 是否流式响应
    :param enable_network: 是否联网检索
    :param base_url: API 根地址（含尾斜杠）
    :param api_key: 木瓜API鉴权Key
    :return: 标准化响应结果
    """
    url = f"{base_url}v1/legal-chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"  # 替换为实际鉴权方式
    }
    payload = {
        "prompt": prompt,
        "stream": stream,
        "enable_network": enable_network
    }

    try:
        response = requests.post(
            url=url,
            json=payload,
            headers=headers,
            timeout=SKILL_META['config']['timeout']
        )
        response.raise_for_status()
        resp_json = response.json()
        return {
            "success": True,
            "data": resp_json,
            "request_id": resp_json.get("request_id", ""),
            "code": response.status_code
        }
    except requests.exceptions.HTTPError as e:
        return {
            "success": False,
            "error": f"HTTP错误: {str(e)}",
            "code": e.response.status_code if e.response else None,
            "request_id": None
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"请求异常: {str(e)}",
            "code": None,
            "request_id": None
        }

# ====================== 案件分析接口封装 ======================
def case_analysis_generate(
    analysis_mode: str,
    base_url: str,
    stream: bool = False,
    input_text: Optional[str] = None,
    files: Optional[List[Dict]] = None,
    parties: Optional[List[Dict]] = None,
    case_reasons: Optional[List[Dict]] = None,
    facts: Optional[List[Dict]] = None,
    demands: Optional[List[Dict]] = None,
    api_key: str = ""
) -> Dict:
    """
    封装木瓜案件分析接口 /v1/case-analysis/generate
    :param analysis_mode: 分析模式（element_extract/full_analysis）
    :param stream: 是否流式响应
    :param input_text: 文本输入（要素提取模式）
    :param files: 文件列表 [{"name": 文件名, "content": 文件二进制, "type": 文件类型}]
    :param parties: 当事人信息（完整分析模式）
    :param case_reasons: 案由（完整分析模式）
    :param facts: 案件事实（完整分析模式）
    :param demands: 诉求（完整分析模式）
    :param base_url: API 根地址（含尾斜杠）
    :param api_key: 鉴权Key
    :return: 标准化响应结果
    """
    # 校验分析模式
    if analysis_mode not in ["element_extract", "full_analysis"]:
        return {
            "success": False,
            "error": f"无效的分析模式: {analysis_mode}，仅支持element_extract/full_analysis",
            "code": 400,
            "request_id": None
        }

    url = f"{base_url}v1/case-analysis/generate"
    headers = {"Authorization": f"Bearer {api_key}"}

    # 文件上传模式（form-data）
    if files:
        # 校验文件大小
        for f in files:
            if len(f.get("content", b"")) > SKILL_META['config']['max_file_size']:
                return {
                    "success": False,
                    "error": f"文件 {f['name']} 超过10MB大小限制",
                    "code": 400,
                    "request_id": None
                }
        data = {
            "analysis_mode": analysis_mode,
            "stream": str(stream).lower(),
            "input": input_text or ""
        }
        files_data = [("files[]", (f["name"], f["content"], f["type"])) for f in files]
        try:
            response = requests.post(
                url=url,
                data=data,
                files=files_data,
                headers=headers,
                timeout=60  # 文件上传超时时间更长
            )
            response.raise_for_status()
            resp_json = response.json()
            return {
                "success": True,
                "data": resp_json,
                "request_id": resp_json.get("request_id", ""),
                "code": response.status_code
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"文件上传失败: {str(e)}",
                "code": getattr(e.response, "status_code", None) if hasattr(e, "response") else None,
                "request_id": None
            }
    # JSON请求模式
    else:
        payload = {"analysis_mode": analysis_mode, "stream": stream}
        if analysis_mode == "element_extract":
            if not input_text:
                return {
                    "success": False,
                    "error": "要素提取模式必须提供input_text参数",
                    "code": 400,
                    "request_id": None
                }
            payload["input"] = input_text
        elif analysis_mode == "full_analysis":
            # 校验完整分析模式必填参数
            required_fields = [parties, case_reasons, facts, demands]
            if not all(required_fields):
                return {
                    "success": False,
                    "error": "完整分析模式必须提供parties/case_reasons/facts/demands参数",
                    "code": 400,
                    "request_id": None
                }
            payload.update({
                "parties": parties,
                "selected_party_names": [p["name"] for p in parties],
                "case_reasons": case_reasons,
                "facts": facts,
                "demands": demands
            })
        try:
            response = requests.post(
                url=url,
                json=payload,
                headers=headers,
                timeout=SKILL_META['config']['timeout']
            )
            response.raise_for_status()
            resp_json = response.json()
            return {
                "success": True,
                "data": resp_json,
                "request_id": resp_json.get("request_id", ""),
                "code": response.status_code
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"JSON请求失败: {str(e)}",
                "code": getattr(e.response, "status_code", None) if hasattr(e, "response") else None,
                "request_id": None
            }

# ====================== OpenClaw Skill入口 ======================
def skill_handler(event: Dict, context: Dict) -> Dict:
    """
    OpenClaw Skill统一入口函数
    :param event: OpenClaw传入参数（含用户输入、Skill配置）
    :param context: 运行上下文（含鉴权信息）
    :return: OpenClaw标准化响应
    """
    # 解析入参
    skill_params = event.get("params", {})
    action = skill_params.get("action")
    api_key = context.get("credentials", {}).get("api_key", "")
    base_url = _resolve_base_url(event, context)

    # 路由到对应接口
    if not action:
        result = {"success": False, "error": "缺少action参数（legal_chat/case_analysis）", "code": 400}
    elif action == "legal_chat":
        result = legal_chat_completions(
            prompt=skill_params.get("prompt", ""),
            base_url=base_url,
            stream=skill_params.get("stream", False),
            enable_network=skill_params.get("enable_network", False),
            api_key=api_key
        )
    elif action == "case_analysis":
        result = case_analysis_generate(
            analysis_mode=skill_params.get("analysis_mode", ""),
            base_url=base_url,
            stream=skill_params.get("stream", False),
            input_text=skill_params.get("input_text"),
            files=skill_params.get("files"),
            parties=skill_params.get("parties"),
            case_reasons=skill_params.get("case_reasons"),
            facts=skill_params.get("facts"),
            demands=skill_params.get("demands"),
            api_key=api_key
        )
    else:
        result = {"success": False, "error": f"无效的action: {action}，仅支持legal_chat/case_analysis", "code": 400}

    # 标准化响应
    return {
        "code": result.get("code", 200 if result["success"] else 500),
        "message": "success" if result["success"] else result["error"],
        "data": result.get("data", {}),
        "request_id": result.get("request_id", ""),
        "success": result["success"]
    }

# 本地测试入口
if __name__ == "__main__":
    # 测试法律咨询接口
    test_event = {
        "params": {
            "action": "legal_chat",
            "prompt": "员工被口头辞退，应该先做什么？",
            "stream": False,
            "enable_network": False
        }
    }
    test_context = {
        "credentials": {
            "api_key": "your_mugua_api_key"  # 替换为真实API Key
        }
    }
    print("法律咨询接口测试结果：")
    print(skill_handler(test_event, test_context))