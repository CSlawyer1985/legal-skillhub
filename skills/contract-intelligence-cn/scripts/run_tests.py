#!/usr/bin/env python3
from pathlib import Path
import json, subprocess, sys, shutil
from docx import Document

ROOT=Path(__file__).resolve().parents[1]
DEMO=ROOT/'examples'; TOOL=ROOT/'scripts'/'contract_skill.py'; PY=sys.executable
T=DEMO/'_test'; T.mkdir(exist_ok=True)

def run(args,expect=0):
    p=subprocess.run(list(map(str,args)),cwd=ROOT,capture_output=True,text=True)
    if p.returncode!=expect:
        print(p.stdout,p.stderr); raise SystemExit(f'expected {expect}, got {p.returncode}')
    return p

results=[]
# 1 通用JSON计划
red=T/'plan_red.docx'; clean=T/'plan_clean.docx'; report=T/'apply.json'
run([PY,TOOL,'apply-plan',DEMO/'示例合同_原稿.docx','--plan',DEMO/'通用修改计划示例.json','--red',red,'--clean',clean,'--out',report])
data=json.loads(report.read_text(encoding='utf-8')); results.append(('apply_plan',data['passed'] and data['operations']==3))
# 2 双版本强化核验（先转PDF）
soffice=shutil.which('soffice') or shutil.which('libreoffice')
for f in (red,clean): run([soffice,'--headless','--convert-to','pdf','--outdir',T,f])
vr=T/'pair.json'
run([PY,TOOL,'verify-pair',red,clean,'--red-pdf',red.with_suffix('.pdf'),'--clean-pdf',clean.with_suffix('.pdf'),'--contains','完整处分权','--absent','具体范围由乙方在交付时确定','--out',vr])
v=json.loads(vr.read_text(encoding='utf-8'));results.append(('verify_pair',v['passed'] and v['texts_identical'] and v['red_blocks']>0 and v['clean_red_blocks']==0))
# 3 非唯一锚点应停止
p=run([PY,TOOL,'apply-plan',DEMO/'示例合同_原稿.docx','--plan',DEMO/'通用修改计划示例.json','--red',T/'x.docx','--clean',T/'y.docx'],expect=0)
# 4 同文哈希
cmp=T/'cmp.json';run([PY,TOOL,'compare-text',DEMO/'示例合同_原稿.docx',DEMO/'示例合同_原稿.docx','--out',cmp]);results.append(('compare_text',json.loads(cmp.read_text(encoding='utf-8'))['passed']))
# 5 失败用例：红线和清洁对调，不得通过
bad=T/'bad.json';run([PY,TOOL,'verify-pair',clean,red,'--contains','完整处分权','--out',bad],expect=2);results.append(('negative_pair',not json.loads(bad.read_text(encoding='utf-8'))['passed']))
print(json.dumps({'tests':[{'name':n,'passed':ok} for n,ok in results],'passed':all(ok for _,ok in results)},ensure_ascii=False,indent=2))
if not all(ok for _,ok in results):raise SystemExit(2)
