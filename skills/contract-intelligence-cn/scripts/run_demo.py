#!/usr/bin/env python3
"""一键复现《合同智审》竞赛Demo。

从虚构示例原稿生成：
- 自动检查报告
- 示例审核意见书
- 修改留痕版与待签署清洁版
- PDF（环境存在LibreOffice时）
- 两份自动核验报告

脚本返回非零即表示Demo未通过。
"""
from pathlib import Path
import json, shutil, subprocess, sys

ROOT=Path(__file__).resolve().parents[1]
DEMO=ROOT/'examples'
TOOL=ROOT/'scripts'/'contract_skill.py'
PY=sys.executable

def run(args):
    print('+',' '.join(map(str,args)))
    subprocess.run(list(map(str,args)),check=True,cwd=ROOT)

def main():
    src=DEMO/'示例合同_原稿.docx'; red=DEMO/'示例合同_修改留痕版.docx'; clean=DEMO/'示例合同_清洁签署版.docx'
    run([PY,TOOL,'inspect',src,'--out',DEMO/'自动检查报告.json'])
    run([PY,TOOL,'review-memo','--out',DEMO/'示例合同审核意见书.md'])
    run([PY,TOOL,'demo-redline',src,'--red',red,'--clean',clean])
    soffice=shutil.which('soffice') or shutil.which('libreoffice')
    red_pdf=DEMO/'示例合同_修改留痕版.pdf'; clean_pdf=DEMO/'示例合同_清洁签署版.pdf'
    if soffice:
        for docx in (red,clean):
            run([soffice,'--headless','--convert-to','pdf','--outdir',DEMO,docx])
    if not red_pdf.exists() or not clean_pdf.exists():
        raise SystemExit('缺少PDF且环境无法转换，不能完成版式页数验证')
    required=['任一期逾期不导致其他未到期款项提前到期','完整处分权']
    cmd=[PY,TOOL,'verify',red,'--pdf',red_pdf,'--out',DEMO/'自动核验报告.json']
    for x in required: cmd += ['--contains',x]
    run(cmd)
    cmd=[PY,TOOL,'verify',clean,'--pdf',clean_pdf,'--out',DEMO/'清洁版核验报告.json']
    for x in required: cmd += ['--contains',x]
    run(cmd)
    a=json.loads((DEMO/'自动核验报告.json').read_text(encoding='utf-8'))
    b=json.loads((DEMO/'清洁版核验报告.json').read_text(encoding='utf-8'))
    if not a['passed'] or a['red_blocks']!=7 or not b['passed'] or b['red_blocks']!=0:
        raise SystemExit('核验指标未通过')
    print(json.dumps({'passed':True,'issues':7,'red_blocks':7,'clean_red_blocks':0,'pdf_pages':[a['pdf_pages'],b['pdf_pages']]},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
