# -*- coding: utf-8 -*-
"""
合同修改引擎 v1.0 — WPS COM 模板保留修改
东润律师事务所 · 合同审查技能辅助工具

遵循模板定律：在原始文档上精确修改，完整保留全部格式（背景图/字体/排版/页眉页脚）。

输出两份文件：
  - 修订标注版：原位置红笔标注 + 修改说明（WPS批注）
  - 清洁版：所有修改已应用，无标注

使用方式：
  python apply_changes.py <原合同路径> <修改清单JSON>
"""

import sys, os, json, time, subprocess
from datetime import datetime


def wps_apply_changes(doc_path, changes, output_dir):
    """
    通过WPS COM在原始文档上应用修改，生成修订版和清洁版

    changes结构:
    [
        {
            "type": "replace",           # replace | insert | delete | comment
            "find": "原文（精确匹配）",      # 需要修改的原文
            "replace": "修改后文本",        # 替换文本
            "reason": "修改理由（显示在批注中）",
            "position_hint": "第X章第X条",  # 位置提示，用于定位
        },
        ...
    ]
    """

    try:
        import comtypes.client
    except ImportError:
        print("安装comtypes...")
        os.system(r'"C:\Users\Admin1\.workbuddy\binaries\python\envs\default\Scripts\pip.exe" install comtypes')
        import comtypes.client

    base_name = os.path.splitext(os.path.basename(doc_path))[0]
    os.makedirs(output_dir, exist_ok=True)

    tracked_path = os.path.join(output_dir, f"{base_name}_修订标注版.docx")
    clean_path = os.path.join(output_dir, f"{base_name}_清洁版.docx")

    wps = None
    doc = None
    results = {"tracked": None, "clean": None, "applied": 0, "failed": []}

    try:
        # 清理残留WPS进程
        subprocess.run(['taskkill', '/F', '/IM', 'wps.exe'],
                       capture_output=True, timeout=3)
        time.sleep(1)

        # ========================================
        # 第一遍：生成修订标注版
        # ========================================
        print("=" * 50)
        print("第一遍：生成修订标注版...")
        wps = comtypes.client.CreateObject('KWPS.Application')
        wps.Visible = False
        wps.DisplayAlerts = False
        doc = wps.Documents.Open(doc_path)
        time.sleep(1)

        applied = 0
        for i, change in enumerate(changes):
            ctype = change.get('type', 'replace')
            find_text = change.get('find', '')
            replace_text = change.get('replace', '')
            reason = change.get('reason', '')
            pos = change.get('position_hint', '')

            print(f"  [{i+1}/{len(changes)}] {ctype}: {find_text[:30]}...")

            try:
                # 定位文本
                rng = doc.Content
                rng.Find.ClearFormatting()
                rng.Find.Text = find_text
                rng.Find.Forward = True
                rng.Find.Wrap = 1  # wdFindContinue
                rng.Find.Format = False
                rng.Find.MatchCase = False
                rng.Find.MatchWholeWord = False

                if not rng.Find.Execute():
                    print(f"    ⚠️ 未找到: {find_text[:50]}")
                    results['failed'].append({
                        'index': i, 'find': find_text, 'error': '文本未找到'
                    })
                    continue

                if ctype == 'replace':
                    # 修改文本 + 标红 + 添加批注
                    comment_text = f"[修改说明] {reason}\n原文：{find_text}\n改为：{replace_text}"
                    doc.Comments.Add(rng, comment_text)

                    # 将修改后的文本设为红色（在原位置标注）
                    rng.Text = replace_text
                    rng.Font.ColorIndex = 6  # wdRed = 6
                    rng.Font.Bold = True

                    applied += 1
                    print(f"    ✅ 已标注: {pos}")

                elif ctype == 'delete':
                    # 删除线 + 红色 + 批注
                    comment_text = f"[删除说明] {reason}\n删除内容：{find_text}"
                    doc.Comments.Add(rng, comment_text)
                    rng.Font.ColorIndex = 6
                    rng.Font.StrikeThrough = True
                    applied += 1
                    print(f"    ✅ 已标注删除: {pos}")

                elif ctype == 'insert':
                    # 在指定位置后插入红色文本 + 批注
                    comment_text = f"[新增说明] {reason}\n新增内容：{replace_text}"
                    doc.Comments.Add(rng, comment_text)
                    rng.Collapse(0)  # wdCollapseEnd
                    new_rng = rng.Duplicate
                    new_rng.Text = replace_text
                    new_rng.Font.ColorIndex = 6
                    new_rng.Font.Bold = True
                    applied += 1
                    print(f"    ✅ 已标注新增: {pos}")

                elif ctype == 'comment':
                    # 仅添加批注，不修改文本
                    comment_text = f"[关注说明] {reason}"
                    doc.Comments.Add(rng, comment_text)
                    rng.Font.ColorIndex = 6
                    applied += 1
                    print(f"    ✅ 已添加批注: {pos}")

            except Exception as e:
                print(f"    ❌ 错误: {e}")
                results['failed'].append({
                    'index': i, 'find': find_text, 'error': str(e)
                })

        # 另存修订标注版
        doc.SaveAs2(tracked_path, FileFormat=12)
        doc.Close(SaveChanges=False)
        wps.Quit()
        time.sleep(1)

        results['tracked'] = tracked_path
        results['applied'] = applied
        print(f"\n修订标注版已保存: {tracked_path} ({applied}处修改)")

        # ========================================
        # 第二遍：生成清洁版
        # ========================================
        print("\n" + "=" * 50)
        print("第二遍：生成清洁版...")
        wps = comtypes.client.CreateObject('KWPS.Application')
        wps.Visible = False
        wps.DisplayAlerts = False
        doc = wps.Documents.Open(doc_path)
        time.sleep(1)

        clean_applied = 0
        for i, change in enumerate(changes):
            if change.get('type') not in ('replace', 'delete'):
                if change.get('type') == 'insert':
                    # 插入操作在清洁版中需要特殊处理
                    find_text = change.get('find', '')
                    replace_text = change.get('replace', '')
                    reason = change.get('reason', '')

                    rng = doc.Content
                    rng.Find.ClearFormatting()
                    rng.Find.Text = find_text
                    rng.Find.Forward = True
                    rng.Find.Wrap = 1
                    rng.Find.Format = False
                    rng.Find.MatchCase = False
                    rng.Find.MatchWholeWord = False

                    if rng.Find.Execute():
                        rng.Collapse(0)  # wdCollapseEnd
                        rng.Text = replace_text
                        clean_applied += 1
                continue

            find_text = change.get('find', '')
            replace_text = change.get('replace', '')

            rng = doc.Content
            rng.Find.ClearFormatting()
            rng.Find.Text = find_text
            rng.Find.Replacement.ClearFormatting()
            rng.Find.Replacement.Text = replace_text if change['type'] == 'replace' else ''
            rng.Find.Forward = True
            rng.Find.Wrap = 1
            rng.Find.Format = False
            rng.Find.MatchCase = False
            rng.Find.MatchWholeWord = False

            if rng.Find.Execute(Replace=2):  # wdReplaceAll
                clean_applied += 1
                print(f"  [{i+1}] ✅ 已替换: {find_text[:30]}...")
            else:
                print(f"  [{i+1}] ⚠️ 未找到: {find_text[:30]}...")

        # 接受所有修订
        try:
            doc.Revisions.AcceptAll()
        except:
            pass

        doc.SaveAs2(clean_path, FileFormat=12)
        doc.Close(SaveChanges=False)
        wps.Quit()

        results['clean'] = clean_path
        results['clean_applied'] = clean_applied
        print(f"\n清洁版已保存: {clean_path} ({clean_applied}处修改)")

    except Exception as e:
        print(f"\n❌ 整体错误: {e}")
        results['error'] = str(e)
    finally:
        try:
            if doc: doc.Close(SaveChanges=False)
        except: pass
        try:
            if wps: wps.Quit()
        except: pass

    return results


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('用法: python apply_changes.py <原合同路径> <修改清单JSON> [输出目录]')
        print()
        print('JSON格式:')
        print(json.dumps([{
            "type": "replace",
            "find": "原文",
            "replace": "修改后文本",
            "reason": "修改理由",
            "position_hint": "第X章第X条"
        }], ensure_ascii=False, indent=2))
        sys.exit(1)

    doc_path = sys.argv[1]
    json_path = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else os.path.dirname(doc_path)

    with open(json_path, 'r', encoding='utf-8') as f:
        changes = json.load(f)

    print(f"合同文件: {doc_path}")
    print(f"修改项数: {len(changes)}")
    print(f"输出目录: {output_dir}")
    print()

    results = wps_apply_changes(doc_path, changes, output_dir)

    print("\n" + "=" * 50)
    print("完成摘要:")
    print(f"  修订标注版: {results.get('tracked', '❌ 失败')}")
    print(f"  清洁版:     {results.get('clean', '❌ 失败')}")
    print(f"  成功修改:   {results.get('applied', 0)}处")
    if results.get('failed'):
        print(f"  失败:       {len(results['failed'])}处")
