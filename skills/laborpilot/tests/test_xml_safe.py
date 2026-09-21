"""xml_safe：DTD／实体一律拒绝，正常 XML 与异常类型兼容性不受影响。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from xml_safe import UnsafeXMLError, fromstring


class XmlSafeTest(unittest.TestCase):
    def test_normal_xml_parses(self):
        root = fromstring('<w:a xmlns:w="u"><w:b>正文</w:b></w:a>')
        self.assertEqual(root[0].text, "正文")

    def test_plain_doctype_rejected(self):
        with self.assertRaises(UnsafeXMLError):
            fromstring(b"<!DOCTYPE document><a/>")

    def test_internal_entity_rejected(self):
        with self.assertRaises(UnsafeXMLError):
            fromstring(b'<?xml version="1.0"?><!DOCTYPE a [<!ENTITY lol "lol">]><a>&lol;</a>')

    def test_external_entity_rejected(self):
        with self.assertRaises(UnsafeXMLError):
            fromstring(b'<!DOCTYPE a [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><a>&xxe;</a>')

    def test_billion_laughs_pattern_rejected(self):
        payload = (
            b'<?xml version="1.0"?><!DOCTYPE lolz [<!ENTITY lol "lol">'
            b'<!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">'
            b'<!ENTITY lol2 "&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;">'
            b']><lolz>&lol2;</lolz>'
        )
        with self.assertRaises(UnsafeXMLError):
            fromstring(payload)

    def test_malformed_xml_keeps_parse_error_type(self):
        with self.assertRaises(ET.ParseError):
            fromstring(b"<a>")


if __name__ == "__main__":
    unittest.main()
