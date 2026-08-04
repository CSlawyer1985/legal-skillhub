"""
LegalConsult — 中国法律咨询AI技能套装
基于中国法律知识库，提供合同审查、法律问答、合规检查等自动化服务
"""
import os
import json
import httpx
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="LegalConsult AI", version="0.1.0")

BASE_DIR = Path(__file__).parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge_base"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
SKILLS_DIR = BASE_DIR / "skills"

# Ensure dirs exist
TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
KNOWLEDGE_DIR.mkdir(exist_ok=True)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"


# ==================== Knowledge Base ====================

def load_knowledge_base() -> dict:
    """Load all legal knowledge files"""
    kb = {}
    if KNOWLEDGE_DIR.exists():
        for f in KNOWLEDGE_DIR.glob("*.md"):
            kb[f.stem] = f.read_text(encoding="utf-8")
        for f in KNOWLEDGE_DIR.glob("*.json"):
            kb[f.stem] = json.loads(f.read_text(encoding="utf-8"))
    return kb


def get_relevant_law(skill_type: str) -> str:
    """Return relevant law context for skill type"""
    kb = load_knowledge_base()
    parts = []
    
    # Map skills to relevant laws
    law_map = {
        "contract_review": ["contract_law", "civil_code"],
        "legal_qa": ["civil_code", "contract_law", "labor_law", "company_law"],
        "compliance_check": ["labor_law", "company_law", "civil_code"],
        "labor_dispute": ["labor_law", "labor_contract_law"],
        "ip_protection": ["civil_code", "trademark_law"],
        "debt_collection": ["civil_code", "contract_law"],
    }
    
    relevant_keys = law_map.get(skill_type, ["civil_code"])
    for key in relevant_keys:
        if key in kb:
            if isinstance(kb[key], str):
                parts.append(f"=== {key} ===\n{kb[key]}")
            else:
                parts.append(f"=== {key} ===\n{json.dumps(kb[key], ensure_ascii=False, indent=2)}")
    
    return "\n\n".join(parts) if parts else "暂无相关法律条文。"


# ==================== LLM ====================

async def call_llm(system_prompt: str, user_prompt: str) -> str:
    """Call LLM API with fallback"""
    if not DEEPSEEK_API_KEY:
        return generate_fallback_response(system_prompt, user_prompt)
    
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 4096,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception:
        return generate_fallback_response(system_prompt, user_prompt)


def generate_fallback_response(system_prompt: str, user_prompt: str) -> str:
    """Template-based fallback when LLM unavailable"""
    if "合同" in user_prompt or "contract" in user_prompt.lower():
        return _contract_review_fallback(user_prompt)
    elif "劳动" in user_prompt or "labor" in user_prompt.lower():
        return _labor_fallback(user_prompt)
    elif "合规" in user_prompt or "compliance" in user_prompt.lower():
        return _compliance_fallback(user_prompt)
    else:
        return _legal_qa_fallback(user_prompt)


def _contract_review_fallback(prompt: str) -> str:
    """Contract review template"""
    return """# 合同审查报告

## 审查概述
- **审查日期：** """ + datetime.now().strftime("%Y年%m月%d日") + """
- **审查类型：** 合同风险评估

## 常见风险点提示

### 1. 主体资格风险
- [ ] 确认合同各方主体名称与营业执照一致
- [ ] 核实签约人是否有授权委托书
- [ ] 检查法人代表/代理人身份

### 2. 权利义务风险
- [ ] 双方权利义务是否对等
- [ ] 违约责任条款是否明确
- [ ] 免责条款是否合理

### 3. 付款条款风险
- [ ] 付款金额、方式、时间是否明确
- [ ] 发票条款是否约定
- [ ] 逾期付款违约金是否合理

### 4. 争议解决风险
- [ ] 是否约定了争议解决方式（仲裁/诉讼）
- [ ] 管辖地是否明确
- [ ] 适用法律是否约定

### 5. 终止与解除
- [ ] 合同终止条件是否明确
- [ ] 提前解除的通知期限
- [ ] 解除后的清算条款

## 法律依据
- 《中华人民共和国民法典》合同编
- 《中华人民共和国合同法》（已废止，参考历史案例）

## 建议
> ⚠️ 本报告为AI初步审查建议，不构成法律意见。重大合同请咨询专业律师。

---
*LegalConsult AI | 模板模式（配置DEEPSEEK_API_KEY获取深度分析）*"""


def _labor_fallback(prompt: str) -> str:
    """Labor dispute template"""
    return """# 劳动法律咨询报告

## 咨询概述
- **日期：** """ + datetime.now().strftime("%Y年%m月%d日") + """
- **类型：** 劳动法律咨询

## 常见劳动争议类型

### 1. 劳动合同争议
- 未签书面劳动合同 → 双倍工资（《劳动合同法》第82条）
- 违法解除劳动合同 → 经济补偿金2倍赔偿（第87条）

### 2. 工资报酬争议
- 拖欠工资 → 补发 + 25%经济补偿金
- 加班费 → 工作日1.5倍，休息日2倍，法定假日3倍

### 3. 社会保险争议
- 未缴纳社保 → 可要求补缴，解除合同可获经济补偿
- 工伤认定 → 用人单位举证责任

### 4. 经济补偿金
- N+1：每工作满一年补偿一个月工资
- 违法解除：2N赔偿
- 月工资上限：当地社平工资3倍

## 法律依据
- 《中华人民共和国劳动合同法》
- 《中华人民共和国劳动法》
- 《劳动争议调解仲裁法》

## 维权途径
1. **协商** → 与用人单位直接沟通
2. **调解** → 向劳动争议调解组织申请
3. **仲裁** → 向劳动争议仲裁委员会申请（免费，1年时效）
4. **诉讼** → 对仲裁裁决不服可向法院起诉

---
*LegalConsult AI | 模板模式*"""


def _compliance_fallback(prompt: str) -> str:
    """Compliance check template"""
    return """# 企业合规检查报告

## 检查概述
- **日期：** """ + datetime.now().strftime("%Y年%m月%d日") + """

## 合规检查清单

### 一、公司治理合规
- [ ] 公司章程是否完善
- [ ] 股东会/董事会决议程序是否合规
- [ ] 关联交易披露是否充分

### 二、劳动用工合规
- [ ] 劳动合同签订率100%
- [ ] 社保公积金缴纳合规
- [ ] 规章制度经民主程序制定并公示

### 三、知识产权合规
- [ ] 商标注册是否完善
- [ ] 商业秘密保护措施
- [ ] 竞业限制协议签署

### 四、数据合规
- [ ] 隐私政策是否符合PIPL
- [ ] 数据安全等级保护
- [ ] 个人信息收集授权合规

### 五、税务合规
- [ ] 发票管理规范
- [ ] 纳税申报及时
- [ ] 税收优惠资格维护

## 法律依据
- 《公司法》《劳动合同法》《个人信息保护法》《税收征收管理法》

---
*LegalConsult AI | 模板模式*"""


def _legal_qa_fallback(prompt: str) -> str:
    """Legal Q&A template"""
    return f"""# 法律问答

**提问时间：** {datetime.now().strftime("%Y年%m月%d日")}

## 您的问题
{prompt[:500]}

## 通用法律建议

由于当前为模板模式（未配置LLM API），无法针对您的具体问题给出个性化建议。

### 推荐操作步骤：
1. **明确法律关系** → 确定是民事、刑事还是行政法律关系
2. **收集证据** → 合同、聊天记录、转账记录、证人证言
3. **确定时效** → 民事诉讼一般3年（《民法典》第188条）
4. **选择途径** → 协商→调解→仲裁→诉讼

### 常用法律热线：
- **12348** → 全国法律援助热线（免费）
- **12315** → 消费者投诉
- **12333** → 劳动保障咨询

---
*LegalConsult AI | 配置DEEPSEEK_API_KEY获取个性化法律分析*"""


# ==================== Skills ====================

SKILLS_REGISTRY = {
    "contract_review": {
        "name": "合同审查",
        "icon": "📋",
        "description": "AI自动审查合同条款，识别法律风险",
        "system_prompt": """你是一位资深中国法律律师，专精合同审查。根据用户提供的合同内容或描述：
1. 逐条分析合同条款的法律风险
2. 标注风险等级（高/中/低）
3. 给出修改建议
4. 引用相关法律条文
请用中文回复，格式清晰。""",
    },
    "legal_qa": {
        "name": "法律问答",
        "icon": "❓",
        "description": "中国法律知识问答，覆盖民事/刑事/行政",
        "system_prompt": """你是一位经验丰富的中国法律顾问。请用通俗易懂的语言回答用户的法律问题：
1. 先给出直接明确的答案
2. 再解释法律依据和条文
3. 给出实操建议
4. 提示风险和注意事项
请用中文回复。重要提示：你的回答仅供参考，不构成正式法律意见。""",
    },
    "compliance_check": {
        "name": "企业合规检查",
        "icon": "✅",
        "description": "企业运营合规性全面检查",
        "system_prompt": """你是一位企业合规顾问。根据用户描述的企业情况：
1. 按照公司治理、劳动用工、知识产权、数据合规、税务合规等维度逐一检查
2. 标注每项合规状态（合规/不合规/需关注）
3. 给出整改建议和优先级
4. 引用相关法规
请用中文回复。""",
    },
    "labor_dispute": {
        "name": "劳动争议咨询",
        "icon": "👷",
        "description": "劳动合同、工资、社保、工伤等劳动争议",
        "system_prompt": """你是一位专精劳动法的中国律师。请分析用户的劳动争议问题：
1. 明确争议焦点和法律关系
2. 分析各方的权利义务
3. 给出维权路径和步骤
4. 提供时效和证据提示
5. 引用《劳动合同法》《劳动法》等条文
请用中文回复。""",
    },
    "ip_protection": {
        "name": "知识产权保护",
        "icon": "🔒",
        "description": "商标、专利、著作权、商业秘密保护",
        "system_prompt": """你是一位知识产权律师。请分析用户的知识产权问题：
1. 确定涉及的知识产权类型（商标/专利/著作权/商业秘密）
2. 分析侵权行为的认定标准
3. 给出保护策略和维权途径
4. 估算可能的赔偿范围
请用中文回复。""",
    },
    "debt_collection": {
        "name": "债务催收指导",
        "icon": "💰",
        "description": "欠款追讨、债务纠纷法律指导",
        "system_prompt": """你是一位擅长债务纠纷的律师。请分析用户的债务问题：
1. 确认债权债务关系及证据
2. 分析诉讼时效状态
3. 给出催收策略（协商→律师函→诉讼→执行）
4. 提示财产保全等保障措施
5. 估算维权成本
请用中文回复。""",
    },
}


# ==================== Routes ====================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Landing page with all skills"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "skills": SKILLS_REGISTRY, "llm_configured": bool(DEEPSEEK_API_KEY)},
    )


@app.post("/api/consult")
async def consult(
    skill_type: str = Form(...),
    question: str = Form(...),
):
    """Main consultation endpoint"""
    if skill_type not in SKILLS_REGISTRY:
        raise HTTPException(400, f"不支持的技能类型: {skill_type}")
    
    skill = SKILLS_REGISTRY[skill_type]
    law_context = get_relevant_law(skill_type)
    
    system_prompt = f"""{skill['system_prompt']}

=== 相关法律条文 ===
{law_context}
=== 条文结束 ===
"""
    
    answer = await call_llm(system_prompt, question)
    
    return JSONResponse({
        "success": True,
        "skill_type": skill_type,
        "skill_name": skill["name"],
        "question": question,
        "answer": answer,
        "llm_mode": bool(DEEPSEEK_API_KEY),
        "generated_at": datetime.now().isoformat(),
    })


@app.get("/api/skills")
async def list_skills():
    """List all available skills"""
    return {
        "skills": {
            k: {"name": v["name"], "icon": v["icon"], "description": v["description"]}
            for k, v in SKILLS_REGISTRY.items()
        },
        "total": len(SKILLS_REGISTRY),
        "llm_configured": bool(DEEPSEEK_API_KEY),
    }


@app.get("/api/health")
async def health():
    """Health check"""
    kb = load_knowledge_base()
    return {
        "status": "ok",
        "version": "0.1.0",
        "skills_count": len(SKILLS_REGISTRY),
        "knowledge_base": list(kb.keys()),
        "llm_configured": bool(DEEPSEEK_API_KEY),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
