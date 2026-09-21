# -*- coding: utf-8 -*-
"""本技能的自检脚本（维护用，不是运行时用）。

盯的就是 2026-09-12 真实发生过的几类"自己跟自己不一致"：

  ① 改了 references/发文机关先验.md，忘了同步 SKILL.md 第 0.5 步的**摘要表**
     → 同一技能里两处对同一事实给出不同值，而用户加载技能时先看到的是错的那份摘要。
  ② frontmatter 版本号没跟着改动走
  ③ 正文引用了不存在的脚本/文件
  ④ 同一个"第 N 步"出现两次（编号冲突，读者找不到该看哪节）
  ⑤ 条目计数口径不一致（把 21 项错写成 20 项/17 项这种）
  ⑥ 脚本语法错误 / 冒烟测试跑不过

用法：python3 scripts/self_check.py
退出码：0 = 全部通过；1 = 有问题（改完再交付）
"""
import json
import pathlib
import re
import subprocess
import sys

D = pathlib.Path(__file__).resolve().parent.parent
SK = D / 'SKILL.md'
PRIOR = D / 'references' / '发文机关先验.md'
FAIL, WARN = [], []


def chk(cond, msg):
    print(('  ✔ ' if cond else '  ✘ ') + msg)
    if not cond:
        FAIL.append(msg)


def main():
    sk = SK.read_text(encoding='utf-8')
    pri = PRIOR.read_text(encoding='utf-8')

    print('【① frontmatter】')
    try:
        import yaml
        fm = yaml.safe_load(sk.split('---')[1])
        chk(bool(fm.get('name') and fm.get('slug') and fm.get('description')
                 and fm.get('version')), f"必需字段齐备（version={fm.get('version')}）")
    except Exception as e:
        chk(False, f'frontmatter 解析失败：{e}')
        fm = {}

    print('\n【② 正文引用的文件都存在】')
    PAT = r'(?:references|scripts)/[A-Za-z0-9\u4e00-\u9fff._-]+'
    refs = set()
    for src in (sk, pri):
        for m in re.finditer(PAT, src):
            prev = src[max(0, m.start() - 60):m.start()]
            # 跳过"别的技能"的脚本（如 word-to-pdf-macos/scripts/...）
            mm = re.search(r'skills/([^/\s]+)/$', prev)
            if mm and mm.group(1) != D.name:
                continue
            if src[m.end():m.end() + 1] == '*':   # 通配符写法（table-spec-*.json）不是具体路径
                continue
            refs.add(m.group(0))
    miss = sorted(r for r in refs if not (D / r).exists())
    chk(not miss, f'{len(refs)} 个引用全部存在' + (f'，缺：{miss}' if miss else ''))

    print('\n【③ 防重复：机关参数只许有一份，SKILL.md 不许复制 references 的数据】')
    # 2026-09-12 的教训：SKILL.md 里曾有一份"机关摘要表"，与 references 各说一套
    # （改了 references 忘了改摘要）→ 加载技能先看到的是错的那份。
    # 治本做法不是"两边同步"，而是**只留一份**：数据在 references，SKILL.md 只留指针。
    DUPPAT = {
        '律协案参数': ['22.0pt', '楷体_GB2312', '黑体 11pt'],
        '公安局案参数': ['15.3pt', '15.30pt'],
    }
    for name, toks in DUPPAT.items():
        leaked = [x for x in toks if x in sk]
        chk(not leaked, f'{name}未在 SKILL.md 复制' + (f'，但发现：{leaked}' if leaked else ''))
    chk('references/发文机关先验.md' in sk, 'SKILL.md 指向了先验表（指针在）')

    print('\n【④ 章节编号不重复】')
    heads = re.findall(r'^## ([^\n]+)$', sk, re.M)
    nums = [h.strip() for h in heads if h.startswith('第')]
    dup = [n for n in set(nums) if nums.count(n) > 1]
    chk(not dup, f'{len(nums)} 个编号章节无重复' + (f'，重复：{dup}' if dup else ''))
    print('     章节序：' + ' | '.join(n[:14] for n in nums))

    print('\n【⑤ 条目计数口径一致】')
    pats = re.findall(r'(\d+)\s*项(?:里)?(?:错(?:了)?|错)\s*(\d+)\s*项', sk + pri)
    bad = [p for p in pats if not (p[0] == '21' and p[1] == '17')]
    chk(not bad, f'{len(pats)} 处计数表述统一为 21/17' + (f'，异常：{bad}' if bad else ''))

    print('\n【⑥ 脚本：语法 + 冒烟】')
    for s in sorted((D / 'scripts').glob('*.py')):
        r = subprocess.run([sys.executable, '-c',
                            f"import ast;ast.parse(open(r'{s}',encoding='utf-8').read())"],
                           capture_output=True)
        chk(r.returncode == 0, f'{s.name} 语法通过')
    # docx 类脚本的冒烟：用经核对的 spec 生成一份，再用审计脚本验它
    spec = D / 'references' / 'table-spec-律协附件3.json'
    out = pathlib.Path('/tmp/_selfcheck_out.docx')
    r = subprocess.run([sys.executable, str(D / 'scripts' / 'build_table_docx.py'),
                        str(spec), '-o', str(out)], capture_output=True, text=True)
    chk(r.returncode == 0 and out.exists(), 'build_table_docx.py 冒烟通过')
    if out.exists():
        r = subprocess.run([sys.executable, str(D / 'scripts' / 'audit_docx.py'),
                            str(out), '--spec', str(spec)],
                           capture_output=True, text=True)
        chk(r.returncode == 0, 'audit_docx.py 对"经核对样本"报 0 FAIL（期望如此）')

    print('\n【⑦ 关键规则在位】')
    NEED = {
        '先要原件': '先要原件',
        '交付目标定义': '先定交付目标',
        '输入质量分级': '输入质量分级',
        '误差预算': '误差预算',
        '可证伪五件套': '可证伪五件套',
        '可用性抽检': '可用性抽检',
        'docGrid 规则': '照抄原件',
        '同引擎对照': '同引擎',
        '工具倒逼内容': '倒逼内容',
        '参数来源 _sources': '_sources',
    }
    for k, v in NEED.items():
        where = sk if k != '参数来源 _sources' else (D / 'references/table-spec-模板.json').read_text(encoding='utf-8')
        chk(v in where, f'{k} 在位')

    print('\n【⑧ 先验表来源分级】')
    for lvl in ('【原件】', '【实证】', '【反推】', '【待验】'):
        chk(lvl in pri, f'来源分级含 {lvl}')

    print('\n' + '=' * 70)
    if FAIL:
        print(f'自检未通过：{len(FAIL)} 项 ✘')
        for f in FAIL:
            print('   ✘ ' + f)
    else:
        print('自检全部通过 ✔')
    sys.exit(1 if FAIL else 0)


if __name__ == '__main__':
    main()
