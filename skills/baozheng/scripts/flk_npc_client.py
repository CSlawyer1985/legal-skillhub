"""
flk.npc.gov.cn 国家法律法规数据库 API 查询客户端 (v2)

基于 flk 二期升级 (2025-08-20) 后的新 API:
- 搜索:    POST /law-search/search/list
- 详情:    GET  /law-search/search/flfgDetails?bbbs={bbbs}
- 下载:    GET  /law-search/download/pc?format={docx|pdf}&bbbs={bbbs}
- 元数据:  GET  /law-search/search/enumData
- 联想:    GET  /law-search/prompts/search?title={keyword}
- 推荐:    GET  /law-search/search/recommend?bbbs={bbbs}
- 正文提取: 下载 OSS DOCX → python-docx 解析（flfgDetails 不返回条文正文）

旧版 API (/api/, /api/detail) 已废弃，请勿使用。

作者: 智慧半岛
日期: 2026-07-03
"""

import json
import os
import re
import time
import random
import tempfile
from dataclasses import dataclass, field
from typing import Optional, Any

try:
    import requests
except ImportError:
    raise ImportError(
        "flk_npc_client 需要 requests 库。请执行: pip install requests\n"
        "或运行: pip install -r requirements.txt (安装全部依赖)"
    )


# ============================================================
# 常量 & 枚举
# ============================================================

BASE_URL = "https://flk.npc.gov.cn"

# 搜索范围
SEARCH_RANGE_TITLE   = 1   # 标题搜索
SEARCH_RANGE_CONTENT = 2   # 正文搜索

# 匹配方式
SEARCH_TYPE_EXACT = 1  # 精确匹配
SEARCH_TYPE_FUZZY = 2  # 模糊匹配

# 时效性过滤
SXX_ABOLISHED  = 1   # 已废止
SXX_MODIFIED   = 2   # 已修改
SXX_VALID      = 3   # 现行有效
SXX_NOT_YET    = 4   # 尚未生效

SXX_LABELS = {1: "已废止", 2: "已修改", 3: "现行有效", 4: "尚未生效"}

# 法规分类 codeId (部分常用)
FLFG_CODE = {
    "宪法":         100,
    "法律":         110,
    "行政法规":      120,
    "监察法规":      130,
    "司法解释":      140,
    "地方性法规":    150,
    "部门规章":      210,
}

# 每页条数合法值
PAGE_SIZES = (10, 20, 30, 40, 50, 100)


@dataclass
class LawItem:
    """法规列表条目"""
    bbbs: str = ""             # 法规唯一标识（新版用 bbbs 替代 id）
    title: str = ""
    gbrq: str = ""             # 公布日期
    sxrq: str = ""             # 施行日期
    sxx: str = ""              # 时效性: 1=废止 2=修改 3=有效 4=未生效
    flxz: str = ""             # 法律性质（法律/行政法规/司法解释等）
    zdjg_name: str = ""        # 制定机关
    flfg_code_id: str = ""
    zdjg_code_id: str = ""
    score: float = 0.0
    title_highlights: list = field(default_factory=list)

    @property
    def status_text(self) -> str:
        return SXX_LABELS.get(int(self.sxx) if self.sxx else 0, "未知")


@dataclass
class LawDetail:
    """法规详情"""
    bbbs: str = ""
    title: str = ""
    sxx: str = ""              # 时效性
    flxz: str = ""             # 法律性质
    zdjg_name: str = ""        # 制定机关
    gbrq: str = ""             # 公布日期
    sxrq: str = ""             # 施行日期
    content: Any = field(default_factory=list)     # 章节结构树 (dict/ArticleNode/list)
    history: list = field(default_factory=list)    # 历史沿革
    oss_word_path: str = ""    # OSS Word 路径
    oss_pdf_path: str = ""     # OSS PDF 路径
    raw: dict = field(default_factory=dict)


@dataclass
class SearchResult:
    """搜索结果"""
    total: int = 0
    page: int = 1
    size: int = 10
    items: list = field(default_factory=list)
    code: int = 0
    msg: str = ""
    raw: dict = field(default_factory=dict)


@dataclass
class EnumData:
    """分类元数据"""
    flfg_tree: list = field(default_factory=list)   # 法律法规分类树
    zdjg_tree: list = field(default_factory=list)   # 制定机关分类树


@dataclass
class ArticleNode:
    """法规目录树节点（解析自 content 树）"""
    id: str = ""               # 节点唯一ID
    parent_id: str = ""        # 父节点ID
    title: str = ""            # 节点标题（章/节/条）
    index: int = 0             # 排序索引
    depth: int = 0             # 树深度（0=根）
    children: list = field(default_factory=list)  # 子节点 (ArticleNode)
    text: list = field(default_factory=list)      # 正文段落列表（仅叶子/条文节点有值）


def _parse_content_tree(raw_node: dict, depth: int = 0) -> ArticleNode:
    """递归解析 API 返回的 content 原始 dict 为 ArticleNode 树"""
    node = ArticleNode(
        id=raw_node.get("id", ""),
        parent_id=raw_node.get("parentId", ""),
        title=raw_node.get("title", ""),
        index=raw_node.get("index", 0),
        depth=depth,
    )
    for child_raw in raw_node.get("children", []):
        node.children.append(_parse_content_tree(child_raw, depth + 1))
    return node


# ============================================================
# 核心客户端
# ============================================================

class FlkNpcClient:
    """国家法律法规数据库查询客户端 (v2)"""

    def __init__(
        self,
        timeout: int = 20,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        request_interval: float = 0.5,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.request_interval = request_interval  # 避免限流
        self._last_request_time: float = 0.0

        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json;charset=utf-8",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": f"{BASE_URL}/",
            "Origin": BASE_URL,
        })

    # ---- 限流保护 ----

    def _rate_limit(self):
        """确保请求间隔 >= request_interval 秒"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)
        self._last_request_time = time.time()

    # ---- 底层 HTTP ----

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
    ) -> dict:
        """带重试和限流的 HTTP 请求，返回 parsed JSON"""
        url = f"{BASE_URL}/{path.lstrip('/')}"
        self._rate_limit()

        last_exc: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                if method == "GET":
                    resp = self._session.get(url, params=params, timeout=self.timeout)
                elif method == "POST":
                    body_str = json.dumps(json_data or {}, ensure_ascii=True)
                    resp = self._session.post(
                        url,
                        data=body_str,
                        timeout=self.timeout,
                    )
                else:
                    raise ValueError(f"不支持的 HTTP 方法: {method}")

                # 检测反爬拦截
                ct = resp.headers.get("Content-Type", "")
                if "text/html" in ct and resp.status_code == 200:
                    raise RuntimeError(
                        f"返回 HTML 而非 JSON（可能被反爬拦截），状态码 {resp.status_code}"
                    )

                resp.raise_for_status()
                return resp.json()

            except (requests.RequestException, RuntimeError, json.JSONDecodeError) as e:
                last_exc = e
                if attempt < self.max_retries:
                    wait = self.retry_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
                    time.sleep(wait)
                    continue

        raise RuntimeError(
            f"请求 {method} {url} 失败（重试 {self.max_retries} 次后）: {last_exc}"
        )

    # ---- 公开 API ----

    def search(
        self,
        keyword: str = "",
        search_range: int = SEARCH_RANGE_TITLE,
        search_type: int = SEARCH_TYPE_FUZZY,
        sxx: Optional[list] = None,
        flfg_code_id: Optional[list] = None,
        zdjg_code_id: Optional[list] = None,
        gbrq: Optional[list] = None,       # 公布日期范围 [start, end]
        sxrq: Optional[list] = None,       # 施行日期范围 [start, end]
        gbrq_year: Optional[list] = None,  # 公布年份列表 ["2020", "2021"]
        page_num: int = 1,
        page_size: int = 10,
    ) -> SearchResult:
        """搜索法律法规

        Args:
            keyword:       搜索关键词
            search_range:  1=标题搜索, 2=正文搜索
            search_type:   1=精确匹配, 2=模糊匹配
            sxx:           时效性过滤: [3]=有效, [1]=废止, [2]=修改, [4]=未生效; None/[]=全部
            flfg_code_id:  法规分类 codeId 列表
            zdjg_code_id:  制定机关 codeId 列表
            gbrq:          公布日期范围 ["2024-01-01", "2025-12-31"]
            sxrq:          施行日期范围
            gbrq_year:     公布年份列表 ["2020", "2021"]
            page_num:      页码（从1开始）
            page_size:     每页条数 (10/20/30/40/50/100)

        Returns:
            SearchResult
        """
        body: dict[str, Any] = {
            "searchContent": keyword,
            "searchRange": search_range,
            "searchType": search_type,
            "flfgCodeId": flfg_code_id or [],
            "zdjgCodeId": zdjg_code_id or [],
            "gbrqYear": gbrq_year or [],
            "gbrq": gbrq or [],
            "sxrq": sxrq or [],
            "sxx": sxx if sxx is not None else [],
            "xgzlSearch": False,
            "pageNum": page_num,
            "pageSize": page_size,
        }

        data = self._request("POST", "/law-search/search/list", json_data=body)

        items = [
            LawItem(
                bbbs=row.get("bbbs", ""),
                title=row.get("title", ""),
                gbrq=row.get("gbrq", ""),
                sxrq=row.get("sxrq", ""),
                sxx=str(row.get("sxx", "")),
                flxz=row.get("flxz", ""),
                zdjg_name=row.get("zdjgName", ""),
                flfg_code_id=str(row.get("flfgCodeId", "")),
                zdjg_code_id=str(row.get("zdjgCodeId", "")),
                score=row.get("score", 0.0),
                title_highlights=row.get("titleHightLightList", []),
            )
            for row in data.get("rows", [])
        ]

        return SearchResult(
            total=data.get("total", 0),
            page=page_num,
            size=page_size,
            items=items,
            code=data.get("code", 0),
            msg=data.get("msg", ""),
            raw=data,
        )

    def search_by_title(
        self,
        title: str,
        sxx: Optional[list] = None,
        **kwargs,
    ) -> SearchResult:
        """按标题模糊搜索（快捷方法）"""
        return self.search(
            keyword=title,
            search_range=SEARCH_RANGE_TITLE,
            search_type=SEARCH_TYPE_FUZZY,
            sxx=sxx,
            **kwargs,
        )

    def get_detail(self, bbbs: str) -> LawDetail:
        """获取法规详情

        Args:
            bbbs: 法规唯一标识（从 search 结果的 item.bbbs 获取）

        Returns:
            LawDetail
        """
        data = self._request("GET", "/law-search/search/flfgDetails", params={"bbbs": bbbs})

        detail = data.get("data", data)  # 兼容不同层级

        oss_files = detail.get("ossFile", {}) or {}
        oss_word = oss_files.get("ossWordPath", "")
        oss_pdf = oss_files.get("ossPdfPath", "")

        return LawDetail(
            bbbs=bbbs,
            title=detail.get("title", ""),
            sxx=str(detail.get("sxx", "")),
            flxz=detail.get("flxz", ""),
            zdjg_name=detail.get("zdjgName", ""),
            gbrq=detail.get("gbrq", ""),
            sxrq=detail.get("sxrq", ""),
            content=detail.get("content", []),
            history=detail.get("lsyg", []),
            oss_word_path=oss_word,
            oss_pdf_path=oss_pdf,
            raw=data,
        )

    def get_download_url(self, bbbs: str, fmt: str = "docx") -> str:
        """获取法规文件下载签名 URL（有效期约1小时）

        Args:
            bbbs: 法规标识
            fmt:  文件格式 docx/pdf

        Returns:
            带签名的完整下载 URL 字符串；失败返回空字符串
        """
        try:
            data = self._request(
                "GET",
                "/law-search/download/pc",
                params={"format": fmt, "bbbs": bbbs, "fileId": ""},
            )
            # 响应结构: {"code":200, "data": {"url": "https://..."}}
            inner = data.get("data", data)
            if isinstance(inner, dict):
                return inner.get("url", "")
            return str(inner) if inner else ""
        except Exception:
            return ""

    def download_file(self, bbbs: str, save_path: str, fmt: str = "docx") -> str:
        """下载法规文件到本地（两步：获取签名URL → 下载文件）

        Args:
            bbbs:      法规标识
            save_path: 本地保存路径
            fmt:       文件格式 docx/pdf

        Returns:
            本地文件路径；失败抛出异常
        """
        dl_url = self.get_download_url(bbbs, fmt)
        if not dl_url:
            raise RuntimeError(f"获取下载链接失败 bbbs={bbbs}")

        resp = requests.get(dl_url, timeout=60)
        resp.raise_for_status()

        with open(save_path, "wb") as f:
            f.write(resp.content)
        return save_path

    def get_enum_data(self) -> EnumData:
        """获取分类元数据（法规分类树 + 制定机关分类树）"""
        raw = self._request("GET", "/law-search/search/enumData")
        data = raw.get("data", raw)  # 兼容 {"code":200, "data":{...}} 外层
        return EnumData(
            flfg_tree=data.get("flfgfl", data.get("flfgTree", [])),
            zdjg_tree=data.get("zdjgfl", data.get("zdjgTree", [])),
        )

    def get_suggestions(self, keyword: str) -> list:
        """搜索联想建议"""
        data = self._request("GET", "/law-search/prompts/search", params={"title": keyword})
        return data.get("data", [])

    def get_recommendations(self, bbbs: str) -> list:
        """获取相关法规推荐"""
        data = self._request("GET", "/law-search/search/recommend", params={"bbbs": bbbs})
        return data.get("data", [])

    # ================================================================
    # 正文提取（基于 OSS Word 文档解析）
    # ================================================================
    # flk 新 API 的 flfgDetails 只返回目录树（id/title/children），不返回条文正文。
    # 正文唯一来源是 OSS 上的 Word 文档。本模块提供 DOCX 缓存下载 + 条文定位能力。

    def _get_cache_dir(self) -> str:
        """获取 DOCX 缓存目录（创建于系统临时目录）"""
        cache_dir = os.path.join(tempfile.gettempdir(), "flk_npc_cache")
        os.makedirs(cache_dir, exist_ok=True)
        return cache_dir

    def _get_docx_cache_path(self, bbbs: str) -> str:
        """获取指定法规的 DOCX 缓存路径"""
        return os.path.join(self._get_cache_dir(), f"{bbbs}.docx")

    def _ensure_docx_cached(self, bbbs: str, force: bool = False) -> str:
        """确保 DOCX 已缓存，返回本地文件路径。

        Args:
            bbbs:  法规标识
            force: 为 True 则强制重新下载

        Returns:
            本地 DOCX 文件路径

        Raises:
            RuntimeError: 下载或签名链接获取失败
        """
        cache_path = self._get_docx_cache_path(bbbs)
        if not force and os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
            return cache_path
        return self.download_file(bbbs, cache_path, "docx")

    def _parse_docx_articles(self, docx_path: str) -> dict:
        """解析 DOCX 文件，提取所有条文。

        Returns:
            {article_title(str): [paragraph_texts](list)}
            例如: {"第三十四条": ["监护人的职责是...", "监护人依法履行..."]}

        注意: 条文标题段落（如"第三十四条　监护人的职责是..."）的正文部分
        会合并到 text[0] 中（标题后的内容视作第1款）。
        """
        try:
            from docx import Document
        except ImportError:
            raise ImportError(
                "解析 DOCX 需要 python-docx 库，请执行: pip install python-docx"
            )

        doc = Document(docx_path)
        articles: dict = {}
        current_title: Optional[str] = None
        # 匹配"第X条"开头的段落（支持各种中文数字）
        TITLE_PATTERN = re.compile(
            r'^(第[一二三四五六七八九十百千]+条)[\s\u3000　]+(.*)$'
        )

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            m = TITLE_PATTERN.match(text)
            if m:
                title = m.group(1)          # "第三十四条"
                body = m.group(2).strip()   # 标题后的正文
                current_title = title
                parts = [body] if body else []
                articles[title] = parts
            elif current_title is not None:
                # 续行：属于当前条文的后续段落
                articles[current_title].append(text)

        return articles

    def get_article_content(
        self,
        bbbs: str,
        article_title: str,
        *,
        force_download: bool = False,
    ) -> Optional[list]:
        """获取指定条文的正文（多段落列表）。

        流程: 下载/缓存 DOCX → 解析所有条文 → 按标题匹配

        Args:
            bbbs:           法规标识
            article_title:  条文标题，如 "第三十四条"
            force_download: 强制重新下载 DOCX（默认使用缓存）

        Returns:
            段落文本列表，例如:
            ["监护人的职责是代理被监护人实施民事法律行为...",
             "监护人依法履行监护职责产生的权利，受法律保护。",
             ...]
            未找到则返回 None

        Raises:
            ImportError: python-docx 未安装
            RuntimeError: DOCX 下载失败
        """
        docx_path = self._ensure_docx_cached(bbbs, force=force_download)
        articles = self._parse_docx_articles(docx_path)
        return articles.get(article_title)

    def get_detail_with_text(
        self,
        bbbs: str,
        *,
        force_download: bool = False,
    ) -> LawDetail:
        """获取法规详情，并自动填充所有条文节点的 text 字段。

        相比 get_detail()，本方法额外下载 DOCX 提取正文，
        回填到 ArticleNode.text 中。

        Args:
            bbbs:           法规标识
            force_download: 强制重新下载 DOCX

        Returns:
            带正文的 LawDetail
        """
        detail = self.get_detail(bbbs)

        # 解析原始 content 树
        raw_content = detail.raw.get("data", detail.raw).get("content")
        if not isinstance(raw_content, dict):
            return detail  # 无 content 树，原样返回

        root = _parse_content_tree(raw_content)

        # 下载 DOCX 并提取条文
        try:
            docx_path = self._ensure_docx_cached(bbbs, force=force_download)
            articles = self._parse_docx_articles(docx_path)
        except Exception:
            # DOCX 不可用时静默降级，返回仅含目录树的结果
            detail.content = root
            return detail

        # 回填 text 到对应条文节点
        def _fill_text(node: ArticleNode):
            if node.title in articles:
                node.text = articles[node.title]
            for child in node.children:
                _fill_text(child)

        _fill_text(root)
        detail.content = root
        return detail

    def close(self):
        """关闭会话"""
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# ============================================================
# 便捷函数
# ============================================================

def search_law(keyword: str, **kwargs) -> SearchResult:
    """快速搜索法规（一行调用）"""
    with FlkNpcClient() as client:
        return client.search(keyword=keyword, **kwargs)


def get_law_detail(bbbs: str) -> LawDetail:
    """快速获取法规详情"""
    with FlkNpcClient() as client:
        return client.get_detail(bbbs)


# ============================================================
# 自测 & 示例
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("flk.npc.gov.cn API 客户端 v2 — 功能验证")
    print("(基于 2025-08-20 升级后的新 API)")
    print("=" * 60)

    with FlkNpcClient(timeout=20) as client:

        # ---- 测试1: 搜索法律 ----
        print("\n[测试1] 搜索法律 '民法典' (标题模糊，仅有效) ...")
        test1_result = None
        try:
            test1_result = client.search_by_title(
                "民法典",
                sxx=[SXX_VALID],
                page_size=5,
            )
            print(f"  code={test1_result.code}, msg={test1_result.msg}")
            total_pages = (test1_result.total + test1_result.size - 1) // max(test1_result.size, 1)
            print(f"  总数: {test1_result.total}, 第 {test1_result.page}/{total_pages} 页, 返回: {len(test1_result.items)} 条")
            for it in test1_result.items:
                print(f"  - [{it.flxz}] {it.title} | 公布: {it.gbrq} | 时效: {it.status_text} | bbbs: {it.bbbs[:30]}...")
        except Exception as e:
            print(f"  ❌ 失败: {type(e).__name__}: {e}")

        # ---- 测试2: 获取详情 ----
        if test1_result and test1_result.items:
            b = test1_result.items[0].bbbs
            print(f"\n[测试2] 获取详情 bbbs={b[:30]}...")
            try:
                detail = client.get_detail(b)
                print(f"  标题: {detail.title}")
                print(f"  性质: {detail.flxz} | 制定机关: {detail.zdjg_name}")
                print(f"  公布: {detail.gbrq} | 施行: {detail.sxrq}")
                print(f"  OSS Word: {detail.oss_word_path or '无'}")
                print(f"  OSS PDF:  {detail.oss_pdf_path or '无'}")

                # 下载链接
                dl = client.get_download_url(b, "docx")
                print(f"  下载URL: {dl[:80]}..." if dl else "  下载URL: 无")
            except Exception as e:
                print(f"  ❌ 失败: {type(e).__name__}: {e}")

        # ---- 测试3: 搜索建议 ----
        print("\n[测试3] 搜索联想 '个人' ...")
        try:
            suggestions = client.get_suggestions("个人")
            print(f"  返回: {len(suggestions)} 条建议")
            for s in suggestions[:5]:
                print(f"  - {s.get('title', s) if isinstance(s, dict) else s}")
        except Exception as e:
            print(f"  ❌ 失败: {type(e).__name__}: {e}")

        # ---- 测试4: 条文正文提取（民法典） ----
        print("\n[测试4] 搜索民法典并提取条文正文 '第三十四条' ...")
        try:
            mfd_result = client.search(
                keyword="中华人民共和国民法典",
                search_range=SEARCH_RANGE_TITLE,
                search_type=SEARCH_TYPE_EXACT,
                sxx=[SXX_VALID],
                page_size=1,
            )
            if mfd_result.items:
                mfd_bbbs = mfd_result.items[0].bbbs
                print(f"  民法典 bbbs={mfd_bbbs[:30]}...")
                paragraphs = client.get_article_content(mfd_bbbs, "第三十四条")
                if paragraphs:
                    for i, p in enumerate(paragraphs, 1):
                        print(f"  第{i}款: {p[:100]}{'...' if len(p) > 100 else ''}")
                    print(f"  共 {len(paragraphs)} 款")
                else:
                    print("  未找到")
            else:
                print("  未搜索到民法典")
        except Exception as e:
            print(f"  ❌ 失败: {type(e).__name__}: {e}")

    print("\n" + "=" * 60)
    print("验证完成")
    print("=" * 60)
