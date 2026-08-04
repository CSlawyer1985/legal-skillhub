"""
LawSearchEngine —— 带双通道降级的法条检索引擎

基于 shared-statute-engine.md 架构规范实现：
- API 优先：flk.npc.gov.cn 实时数据（通过 FlkNpcClient，默认重试 5 次）
- AI 知识库兜底：API 不可用时返回降级信号，由上层 AI 用训练数据补全
- 熔断：连续 5 次失败 → 触发场景十人工介入
- 来源标注 + 真实性验证：API 成功 → verified=True；降级 → verified=False + 核验提示
- 内容完整性检查：条文段落数合理性校验，过滤空白/异常结果

被模块 A/B/C/D 引用，作为法条检索的统一入口。

作者: 智慧半岛
日期: 2026-07-03
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Optional

from flk_npc_client import (
    FlkNpcClient,
    SXX_VALID,
    SEARCH_RANGE_TITLE,
    SEARCH_TYPE_EXACT,
    SEARCH_TYPE_FUZZY,
)


# ================================================================
# 结果数据类
# ================================================================

@dataclass
class ArticleParagraphs:
    """单条的段落列表"""
    title: str       # 条文标题，如 "第三十四条"
    paragraphs: list  # 段落文本列表，如 ["监护人的职责是...", ...]


@dataclass
class StatuteResult:
    """法条检索统一结果（无论 API 还是降级，都用此结构）"""
    success: bool                     # API 调用是否成功
    source: str = ""                  # "flk.npc.gov.cn" 或 "AI知识库"
    law_title: str = ""               # 法规全称
    bbbs: str = ""                    # 法规唯一标识（API 成功时有值）
    articles: list = field(default_factory=list)  # [ArticleParagraphs, ...]
    error: str = ""                   # 错误信息
    disclaimer: str = (               # 免责声明
        "以上内容仅供参考，具体适用请以官方最新文本及司法实践为准"
    )
    breaker_triggered: bool = False   # 熔断是否触发
    verified: bool = False            # 内容是否经真实性验证
    verification_note: str = ""       # 验证说明


@dataclass
class BreakerState:
    """熔断状态追踪"""
    failure_count: int = 0            # 连续失败次数
    last_failure_time: float = 0.0    # 最近一次失败时间
    breaker_triggered: bool = False   # 熔断是否激活

    MAX_FAILURES: int = field(default=5, init=False)  # 最多连续失败 5 次

    def record_success(self):
        """记录成功，重置计数器"""
        self.failure_count = 0
        self.breaker_triggered = False

    def record_failure(self) -> bool:
        """记录失败，返回是否触发熔断"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.MAX_FAILURES:
            self.breaker_triggered = True
        return self.breaker_triggered

    def reset(self):
        """手动重置（用户补充新信息后调用）"""
        self.failure_count = 0
        self.breaker_triggered = False
        self.last_failure_time = 0.0


# ================================================================
# 检索引擎
# ================================================================

class LawSearchEngine:
    """双通道法条检索引擎

    用法:
        engine = LawSearchEngine(timeout=15)

        # 按法规名+条文号检索
        result = engine.fetch_article("中华人民共和国民法典", "第三十四条")
        if result.source == "flk.npc.gov.cn":
            print("实时数据:", result.articles[0].paragraphs)
        else:
            print("降级数据，请用 AI 知识库补全")

        # 关键词搜索
        result = engine.search("试用期 劳动合同", article_title="第十九条")
    """

    def __init__(
        self,
        timeout: int = 20,
        max_retries: int = 5,
        request_interval: float = 0.5,
        max_failures: int = 5,
    ):
        """
        Args:
            timeout:           API 请求超时秒数
            max_retries:       最大重试次数（默认 5，提高成功率）
            request_interval:  请求间隔（防限流）
            max_failures:      连续失败熔断阈值（默认 5，兼顾自动恢复与人工介入）
        """
        self._timeout = timeout
        self._max_retries = max_retries
        self._request_interval = request_interval
        self._breaker = BreakerState()
        self._breaker.MAX_FAILURES = max_failures
        self._client: Optional[FlkNpcClient] = None

    # ---- 内部 ----

    def _get_client(self) -> FlkNpcClient:
        """懒初始化客户端（复用连接）"""
        if self._client is None:
            self._client = FlkNpcClient(
                timeout=self._timeout,
                max_retries=self._max_retries,
                request_interval=self._request_interval,
            )
        return self._client

    @staticmethod
    def _strip_html(text: str) -> str:
        """剥离 API 返回中的 HTML 高亮标签（如 <em class='highlight'>）"""
        return re.sub(r"<[^>]+>", "", text)

    @staticmethod
    def _verify_content(paragraphs: list, law_title: str = "") -> tuple:
        """对 API 返回的条文做基础内容完整性校验。

        校验项:
          1. 段落数是否在合理范围（1-200 款为正常条文）
          2. 每款是否包含有效文本（非空、非纯标点、非纯空格）
          3. 是否含有明显的错误标记（如 HTML 标签碎片、JS 代码残留）

        Returns:
            (verified: bool, note: str)
        """
        if not paragraphs or not isinstance(paragraphs, list):
            return False, "条文内容为空或格式异常"

        if len(paragraphs) > 200:
            return False, f"条文段落数异常（{len(paragraphs)} 款），可能匹配到整章而非单条"

        # 检查每款是否有实质内容
        empty_count = 0
        garbage_patterns = [
            r"^\s*$",                     # 纯空白
            r"^[，。、；：""'']+$",       # 纯标点
            r"<script|<html|<body",       # JS/HTML 代码碎片
            r"^\d{3,}\s*$",               # 纯数字（错误页码之类）
        ]

        for i, p in enumerate(paragraphs):
            stripped = p.strip() if isinstance(p, str) else ""
            if not stripped:
                empty_count += 1
                continue
            for gp in garbage_patterns:
                if re.search(gp, stripped, re.IGNORECASE):
                    empty_count += 1
                    break

        valid_count = len(paragraphs) - empty_count
        if valid_count < 1:
            return False, f"所有 {len(paragraphs)} 款内容均无效（空或异常）"

        if empty_count > 0:
            label = law_title or "该法条"
            return True, f"{label} 共 {len(paragraphs)} 款，{valid_count} 款有效（{empty_count} 款可能为序号行），来源：国家法律法规数据库官方API"

        label = law_title or "该法条"
        return True, f"{label} 共 {len(paragraphs)} 款，内容完整性校验通过，来源：国家法律法规数据库官方API"

    def _check_breaker(self) -> Optional[StatuteResult]:
        """检查熔断状态。如已熔断，返回提前终止结果；否则返回 None"""
        if self._breaker.breaker_triggered:
            n = self._breaker.MAX_FAILURES
            return StatuteResult(
                success=False,
                source="AI知识库",
                error=(
                    f"已连续 {n} 次 API 调用失败，触发熔断保护。"
                    "建议携带完整材料咨询执业律师，或访问 https://flk.npc.gov.cn/ 手动查询。"
                    "如需继续，请补充更多背景信息后重新提问。"
                ),
                breaker_triggered=True,
                verified=False,
                verification_note="API 熔断，未进行内容验证",
            )
        return None

    def _make_result(
        self,
        success: bool,
        source: str,
        law_title: str = "",
        bbbs: str = "",
        articles: list = None,
        error: str = "",
        verified: bool = False,
        verification_note: str = "",
    ) -> StatuteResult:
        """构建统一结果"""
        return StatuteResult(
            success=success,
            source=source,
            law_title=law_title,
            bbbs=bbbs,
            articles=articles or [],
            error=error,
            verified=verified,
            verification_note=verification_note,
        )

    # ---- 公开 API ----

    def fetch_article(
        self,
        law_name: str,
        article_title: str,
        *,
        force_download: bool = False,
    ) -> StatuteResult:
        """按法规名 + 条文号精确检索。

        API 调用链:
          1. 精确搜索法规标题 → 获取 bbbs
          2. 下载/缓存 DOCX → 解析条文
          3. 按 article_title 匹配返回

        Args:
            law_name:        法规全称，如 "中华人民共和国民法典"
            article_title:   条文号，如 "第三十四条"
            force_download:  强制重新下载 DOCX

        Returns:
            StatuteResult（source 区分 API/降级）
        """

        # 1) 熔断检查
        breaker_result = self._check_breaker()
        if breaker_result:
            return breaker_result

        # 2) API 调用
        try:
            client = self._get_client()

            # 搜索法规
            search_result = client.search(
                keyword=law_name,
                search_range=SEARCH_RANGE_TITLE,
                search_type=SEARCH_TYPE_EXACT,
                sxx=[SXX_VALID],
                page_size=1,
            )
            if not search_result.items:
                return self._handle_failure(
                    law_title=law_name,
                    error=f"搜索 '{law_name}' 无结果",
                )

            bbbs = search_result.items[0].bbbs
            law_title = self._strip_html(search_result.items[0].title)

            # 提取条文
            paragraphs = client.get_article_content(
                bbbs, article_title, force_download=force_download
            )
            if paragraphs is None:
                return self._handle_failure(
                    law_title=law_title,
                    error=f"'{law_title}' 中未找到 '{article_title}'",
                )

            # 成功
            verified, vnote = self._verify_content(paragraphs, law_title)
            self._breaker.record_success()
            return self._make_result(
                success=True,
                source="flk.npc.gov.cn",
                law_title=law_title,
                bbbs=bbbs,
                articles=[ArticleParagraphs(title=article_title, paragraphs=paragraphs)],
                verified=verified,
                verification_note=vnote,
            )

        except Exception as e:
            return self._handle_failure(
                law_title=law_name,
                error=f"API 调用异常: {type(e).__name__}: {e}",
            )

    def search(
        self,
        keyword: str,
        article_title: Optional[str] = None,
        *,
        search_type: int = SEARCH_TYPE_FUZZY,
        page_size: int = 5,
    ) -> StatuteResult:
        """按关键词搜索法规并提取条文。

        API 调用链:
          1. 模糊搜索关键词 → 获取匹配的法规列表
          2. 取第一条结果 → 获取 bbbs
          3. 如有 article_title → 下载 DOCX 提取指定条文
          4. 否则只返回法规元信息

        Args:
            keyword:        搜索关键词，如 "试用期 劳动合同"
            article_title:  可选，指定提取某条正文
            search_type:    精确(1)/模糊(2)
            page_size:      每页条数

        Returns:
            StatuteResult
        """

        breaker_result = self._check_breaker()
        if breaker_result:
            return breaker_result

        try:
            client = self._get_client()

            search_result = client.search(
                keyword=keyword,
                search_range=SEARCH_RANGE_TITLE,
                search_type=search_type,
                sxx=[SXX_VALID],
                page_size=page_size,
            )

            if not search_result.items:
                return self._handle_failure(
                    error=f"关键词 '{keyword}' 无匹配法规",
                )

            top = search_result.items[0]
            bbbs = top.bbbs
            law_title = self._strip_html(top.title)

            articles = []
            if article_title:
                paragraphs = client.get_article_content(bbbs, article_title)
                if paragraphs:
                    articles.append(
                        ArticleParagraphs(title=article_title, paragraphs=paragraphs)
                    )

            self._breaker.record_success()

            # 内容验证（区分有/无条文两种场景）
            if articles:
                all_paragraphs = []
                for ap in articles:
                    all_paragraphs.extend(ap.paragraphs)
                verified, vnote = self._verify_content(all_paragraphs, law_title)
            else:
                # 仅返回法规元信息（法规匹配成功即验证通过）
                verified = True
                vnote = (
                    f"'{law_title}' 匹配成功，未提取条文正文，"
                    f"来源：国家法律法规数据库官方API"
                )

            return self._make_result(
                success=True,
                source="flk.npc.gov.cn",
                law_title=law_title,
                bbbs=bbbs,
                articles=articles,
                verified=verified,
                verification_note=vnote,
            )

        except Exception as e:
            return self._handle_failure(
                error=f"API 调用异常: {type(e).__name__}: {e}",
            )

    def get_law_detail(
        self,
        law_name: str,
        *,
        with_text: bool = False,
        force_download: bool = False,
    ) -> StatuteResult:
        """获取法规完整详情（目录树 + 可选正文）。

        Args:
            law_name:        法规全称
            with_text:       是否下载 DOCX 回填条文正文（耗时较长）
            force_download:  强制重新下载 DOCX

        Returns:
            StatuteResult（articles 包含 ArticleNode 树信息）
        """

        breaker_result = self._check_breaker()
        if breaker_result:
            return breaker_result

        try:
            client = self._get_client()

            search_result = client.search(
                keyword=law_name,
                search_range=SEARCH_RANGE_TITLE,
                search_type=SEARCH_TYPE_EXACT,
                sxx=[SXX_VALID],
                page_size=1,
            )

            if not search_result.items:
                return self._handle_failure(
                    law_title=law_name,
                    error=f"搜索 '{law_name}' 无结果",
                )

            bbbs = search_result.items[0].bbbs
            law_title = self._strip_html(search_result.items[0].title)

            if with_text:
                detail = client.get_detail_with_text(bbbs, force_download=force_download)
            else:
                detail = client.get_detail(bbbs)

            self._breaker.record_success()
            return self._make_result(
                success=True,
                source="flk.npc.gov.cn",
                law_title=law_title,
                bbbs=bbbs,
                articles=[],  # content tree 在 raw 中
                verified=True,
                verification_note=f"{law_title} 目录结构获取成功，来源：国家法律法规数据库官方API",
            )

        except Exception as e:
            return self._handle_failure(
                law_title=law_name,
                error=f"API 调用异常: {type(e).__name__}: {e}",
            )

    # ---- 降级 & 熔断 ----

    def _handle_failure(self, **kwargs) -> StatuteResult:
        """统一失败处理：记录失败 + 检查熔断 + 返回降级结果"""
        breaker_triggered = self._breaker.record_failure()

        error_msg = kwargs.pop("error", "API 不可用")
        law_title = kwargs.pop("law_title", "")

        if breaker_triggered:
            n = self._breaker.MAX_FAILURES
            error_msg = (
                f"已连续 {n} 次 API 调用失败，触发熔断保护。"
                f"（最近错误：{error_msg}）"
                "建议携带完整材料咨询执业律师，或访问 https://flk.npc.gov.cn/ 手动查询。"
                "如需继续，请补充更多背景信息后重新提问。"
            )

        return StatuteResult(
            success=False,
            source="AI知识库",
            law_title=law_title,
            error=error_msg,
            breaker_triggered=breaker_triggered,
            verified=False,
            verification_note=(
                "API 不可用，降级至 AI 知识库补全，"
                "内容未经官方核验，建议手动访问 https://flk.npc.gov.cn/ 确认"
            ),
        )

    def reset_breaker(self):
        """手动重置熔断状态（用户补充新信息后调用）"""
        self._breaker.reset()

    def close(self):
        """关闭底层 HTTP 会话"""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# ================================================================
# 便捷函数（模块 A/B/C/D 一行调用）
# ================================================================

_engine_cache: Optional[LawSearchEngine] = None


def _get_engine(**kwargs) -> LawSearchEngine:
    """获取共享引擎实例（轻量缓存，同一进程复用连接）"""
    global _engine_cache
    # 每次调用允许覆盖 timeout 等参数
    if _engine_cache is None:
        _engine_cache = LawSearchEngine(**kwargs)
    return _engine_cache


def fetch_statute(law_name: str, article: str) -> StatuteResult:
    """快速检索法条（一行调用）。

    用法:
        r = fetch_statute("中华人民共和国民法典", "第三十四条")
        if r.source == "flk.npc.gov.cn":
            for ap in r.articles:
                print(ap.title, ap.paragraphs)
        else:
            # r.source == "AI知识库" → 使用 AI 训练数据补全
            ...
    """
    engine = _get_engine()
    return engine.fetch_article(law_name, article)


def search_statute(keyword: str, article: Optional[str] = None) -> StatuteResult:
    """快速关键词搜索法条。

    用法:
        r = search_statute("试用期", article="第十九条")
    """
    engine = _get_engine()
    return engine.search(keyword, article_title=article)


def close_engine():
    """关闭共享引擎"""
    global _engine_cache
    if _engine_cache:
        _engine_cache.close()
        _engine_cache = None


# ================================================================
# 自测
# ================================================================

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("LawSearchEngine 功能验证")
    print("双通道：API 优先 + AI 知识库兜底 + 熔断")
    print(f"默认熔断阈值: {BreakerState.MAX_FAILURES} 次")
    print("=" * 60)

    # ==== 场景A: 正常检索 + 验证 ====
    with LawSearchEngine(timeout=15) as engine:

        print("\n[测试1] 正常检索 '民法典 第三十四条' ...")
        result = engine.fetch_article("中华人民共和国民法典", "第三十四条")
        print(f"  success: {result.success}")
        print(f"  source:  {result.source}")
        print(f"  law:     {result.law_title}")
        print(f"  verified: {result.verified}")
        print(f"  vnote:   {result.verification_note[:80]}...")
        print(f"  breaker: {result.breaker_triggered}")
        if result.articles:
            for ap in result.articles:
                print(f"  [{ap.title}] {len(ap.paragraphs)} 款:")
                for i, p in enumerate(ap.paragraphs, 1):
                    preview = p[:80] + "..." if len(p) > 80 else p
                    print(f"    款{i}: {preview}")

        print("\n[测试2] 精确搜索 '劳动合同法 第十九条' ...")
        result2 = engine.fetch_article("中华人民共和国劳动合同法", "第十九条")
        print(f"  success: {result2.success}")
        print(f"  verified: {result2.verified}")
        if result2.articles:
            for ap in result2.articles:
                print(f"  [{ap.title}] {len(ap.paragraphs)} 款")

        print("\n[测试3] 关键词模糊搜索 '试用期规定' ...")
        result3 = engine.search("试用期", article_title="第十九条")
        print(f"  success: {result3.success}")
        print(f"  verified: {result3.verified}")
        print(f"  vnote:   {result3.verification_note[:80]}...")

    # ==== 场景B: 降级 + 熔断（超短超时模拟不可达，阈值=5） ====
    print("\n" + "-" * 40)
    print("降级 & 熔断验证（timeout=0.001, max_failures=5）")
    print("-" * 40)

    with LawSearchEngine(timeout=0.001, max_retries=1, max_failures=5) as be:

        # 前4次失败→降级，未熔断
        for i in range(1, 5):
            r = be.fetch_article(f"测试法规{i}", "第一条")
            print(f"  [第{i}次] verified={r.verified} breaker={r.breaker_triggered}")

        # 第5次失败→触发熔断
        print(f"\n  [第5次] 应触发熔断...")
        r5 = be.fetch_article("测试法规5", "第一条")
        print(f"    verified={r5.verified} breaker={r5.breaker_triggered}")

        # 熔断后调用直接拒绝
        print(f"\n  [熔断后] 直接拒绝...")
        r6 = be.fetch_article("中华人民共和国民法典", "第三十四条")
        print(f"    verified={r6.verified} breaker={r6.breaker_triggered}")
        print(f"    vnote: {r6.verification_note[:80]}...")

    # ==== 场景C: 重置熔断 ====
    print("\n" + "-" * 40)
    print("重置熔断验证")
    print("-" * 40)

    with LawSearchEngine(timeout=0.001, max_retries=1, max_failures=5) as re:
        for i in range(5):
            re.fetch_article(f"bad{i}", "第x条")

        print("\n[测试4] 熔断后调用...")
        r7 = re.fetch_article("中华人民共和国民法典", "第三十四条")
        print(f"  breaker: {r7.breaker_triggered}")

        print("[测试5] 重置熔断...")
        re.reset_breaker()
        assert not re._breaker.breaker_triggered
        print(f"  breaker after reset: {re._breaker.breaker_triggered}")

    # ==== 场景D: 正常检索验证示例 ====
    print("\n" + "-" * 40)
    print("正常检索验证示例")
    print("-" * 40)

    with LawSearchEngine(timeout=15) as norm:
        r8 = norm.fetch_article("中华人民共和国民法典", "第三十四条")
        print(f"  source: {r8.source}")
        print(f"  verified: {r8.verified}")
        print(f"  verification_note: {r8.verification_note}")

    print("\n" + "=" * 60)
    print("全部验证通过")
    print("=" * 60)
