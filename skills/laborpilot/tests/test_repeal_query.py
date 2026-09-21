"""废止复核：内嵌知识摘录不得丢失历史警示，也不得丢卡。"""
import ast
import base64
import importlib.util
import marshal
from pathlib import Path
import unittest
import zlib

SCRIPT=Path(__file__).resolve().parents[1]/'scripts/issue_router.py'
spec=importlib.util.spec_from_file_location('repeal_query',SCRIPT)
router=importlib.util.module_from_spec(spec)
spec.loader.exec_module(router)


class RepealQueryTest(unittest.TestCase):
    def test_all_revised_cards_keep_notice_in_returned_excerpt(self):
        cards=marshal.loads(zlib.decompress(base64.b64decode(router._COMPILED_KNOWLEDGE)))
        revised=[c for c in cards if '废止复核（2026-09-07）' in c['bd']]
        self.assertEqual(len(cards),96)
        self.assertEqual(len(revised),38)
        for card in revised:
            with self.subTest(issue=card['t']):
                # 用主争点查询，避免标题括号里的“加班”等伴生词改变既有意图路由。
                query=card['t'].split('(')[0]
                matched=[r for r in router.query_knowledge(query) if r['issue']==card['t']]
                self.assertTrue(matched)
                self.assertTrue(matched[0]['analysis_points'].startswith('废止复核：'))
                self.assertTrue(matched[0]['zhejiang_guidance'].startswith('废止复核：'))

    def test_long_excerpts_keep_notice_within_existing_limits(self):
        body='历史依据已废止。\n'+('关键词'+('甲'*800)+'\n')*4
        output=router._excerpt(body,['关键词'],None,max_chars=280)
        self.assertTrue(output.startswith('废止复核：'))
        self.assertLessEqual(len(output),281)

    def test_unaffected_plain_text_is_not_tagged(self):
        self.assertFalse(router._excerpt('加班事实应核验。',['加班'],None).startswith('废止复核：'))


if __name__=='__main__': unittest.main()
