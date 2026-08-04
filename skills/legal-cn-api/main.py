"""
legal-cn-api - 中国法律条文检索付费API
Author: Felix Feng + Asaking
License: MIT
"""

from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from meilisearch import Client
from pydantic import BaseModel
import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Meilisearch client
meili = Client(config.MEILISEARCH_HOST, config.MEILISEARCH_MASTER_KEY)
INDEX_NAME = "legal_cn"
index = meili.index(INDEX_NAME)

app = FastAPI(
    title="legal-cn-api",
    description="中国法律条文检索付费API (x402微支付)",
    version="1.0.0",
)

class SearchResponse(BaseModel):
    success: bool
    results: list
    total: int

class SearchResult(BaseModel):
    law_title: str
    article_no: str
    article_title: str
    content: str
    effective_date: str
    category: str
    score: float

# 限流
from collections import defaultdict
from datetime import datetime, timedelta
request_counts = defaultdict(list)

def check_rate_limit(client_ip: str) -> bool:
    now = datetime.now()
    minute_ago = now - timedelta(minutes=1)
    # 清理旧请求
    request_counts[client_ip] = [t for t in request_counts[client_ip] if t > minute_ago]
    request_counts[client_ip].append(now)
    return len(request_counts[client_ip]) <= config.MAX_REQUESTS_PER_MINUTE

# Base mainnet constants
BASE_CHAIN_ID = 8453
# USDC on Base
USDC_ADDRESS = "0x833589fCD6eDb6AD44080C48D3068386FBDC3170"

# ====== x402 支付验证 ======
# Use official FastAPI middleware integration
from x402.http.middleware.fastapi import payment_middleware_from_config
from x402.mechanisms.evm.exact.server import ExactEvmScheme
from eth_account import Account
from web3 import Web3

x402_enabled = False
if config.X402_ENABLED and config.X402_WALLET_PRIVATE_KEY:
    try:
        # Create local account from private key
        account = Account.from_key(config.X402_WALLET_PRIVATE_KEY)
        # Verify address matches
        derived_address = account.address
        expected_recipient = Web3.to_checksum_address(config.X402_WALLET_ADDRESS)
        if derived_address.lower() != expected_recipient.lower():
            logger.error(f"❌ Address mismatch: derived {derived_address} != configured {expected_recipient}")
            raise ValueError("Private key does not match configured address")
        
        # Create the exact mechanism instance
        mechanism = ExactEvmScheme()
        
        # Configure route
        price_decimal = float(config.PRICE_PER_REQUEST) / 1e6
        routes_config = {
            f"GET /api/v1/search": {
                "accepts": [
                    {
                        "scheme": "exact",
                        "payTo": derived_address,
                        "price": str(price_decimal),
                        "network": f"eip155:{BASE_CHAIN_ID}",
                    }
                ]
            }
        }
        
        # Schemes - list of dicts with 'network' and 'server'
        schemes = [
            {
                "network": "eip155:*",
                "server": mechanism
            }
        ]
        
        # Add middleware
        app.middleware("http")(
            payment_middleware_from_config(
                routes=routes_config,
                schemes=schemes
            )
        )
        
        logger.info("✅ x402 payment verification enabled")
        logger.info(f"   Network: Base (eip155:8453)")
        logger.info(f"   Recipient: {derived_address}")
        logger.info(f"   Token: USDC {USDC_ADDRESS}")
        logger.info(f"   Price per search: {price_decimal} USDC")
        x402_enabled = True
    except Exception as e:
        logger.error(f"❌ Failed to initialize x402: {e}")
        import traceback
        traceback.print_exc()
        x402_enabled = False
else:
    x402_enabled = False
    logger.info("⚠️ x402 payment disabled - running in open access mode")

@app.get("/api/v1/search", response_model=SearchResponse)
def search(
    q: str = Query(..., description="搜索关键词"),
    limit: int = Query(10, description="返回结果数量", ge=1, le=50),
    authorization: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False))
):
    # 限流检查
    client_ip = "127.0.0.1"  # TODO: get client ip from request
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded, try again later")
    
    # x402 middleware already handles payment verification
    # If we reach here, payment is verified or not required
    
    # 搜索
    search_result = index.search(q, {"limit": limit})
    
    results = []
    for hit in search_result["hits"]:
        results.append(SearchResult(
            law_title=hit.get("law_title", ""),
            article_no=hit.get("article_no", ""),
            article_title=hit.get("article_title", ""),
            content=hit.get("content", ""),
            effective_date=hit.get("effective_date", ""),
            category=hit.get("category", ""),
            score=hit.get("_score", 0.0)
        ))
    
    return SearchResponse(
        success=True,
        results=results,
        total=search_result["estimatedTotalHits"]
    )

@app.get("/categories")
def get_categories():
    """获取所有法律分类，免费发现"""
    # 免费接口，不需要支付
    # 获取facet分布统计
    facet_result = index.search("", {
        "facets": ["category"],
        "limit": 1
    })
    
    categories = []
    if "facetDistribution" in facet_result and "category" in facet_result["facetDistribution"]:
        for category, count in facet_result["facetDistribution"]["category"].items():
            categories.append({
                "name": category,
                "count": count
            })
    
    # 按名称排序
    categories.sort(key=lambda x: x["name"])
    
    return {
        "success": True,
        "categories": categories,
        "total": len(categories)
    }

@app.get("/health")
def health():
    """健康检查"""
    return {
        "status": "ok", 
        "service": "legal-cn-api",
        "x402_enabled": x402_enabled
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT)
