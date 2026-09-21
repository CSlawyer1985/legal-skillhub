#!/usr/bin/env python3
"""安全 XML 解析：一律拒绝 DTD 与实体定义，防实体扩展攻击。

案件材料（DOCX 内嵌 XML 等）可能来自不可信来源；Python 标准库
ElementTree 按官方文档对十亿笑话（billion laughs）、外部实体（XXE）
等实体扩展脆弱。合法 OOXML 不含 DTD，故本模块先用 expat 探针截获
DOCTYPE／ENTITY 声明并直接拒绝，再交 ElementTree 完成正常解析。

思路与 defusedxml 的 DefusedXMLParser 一致；项目保持零第三方依赖，
故在标准库内实现同等防线。
"""

from __future__ import annotations

from xml.etree import ElementTree as ET
from xml.parsers.expat import ExpatError, ParserCreate


class UnsafeXMLError(ValueError):
    """XML 含 DTD／实体定义，已拒绝解析。"""


def _reject_doctype(*_args) -> None:
    raise UnsafeXMLError("XML 含 DOCTYPE 声明，已拒绝解析")


def _reject_entity(*_args) -> None:
    raise UnsafeXMLError("XML 含实体定义，已拒绝解析")


def fromstring(data) -> ET.Element:
    """解析 XML（str 或 bytes）；含 DTD／实体定义时抛 UnsafeXMLError。

    一般性语法错误仍由 ElementTree 抛出 ParseError，调用方原有
    的异常处理不受影响。
    """
    raw = data.encode("utf-8") if isinstance(data, str) else data
    probe = ParserCreate()
    probe.StartDoctypeDeclHandler = _reject_doctype
    probe.EntityDeclHandler = _reject_entity
    try:
        probe.Parse(raw, True)
    except UnsafeXMLError:
        raise
    except ExpatError:
        pass  # 语法问题交给 ElementTree 抛规范异常
    return ET.fromstring(data)
