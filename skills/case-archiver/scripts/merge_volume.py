#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""merge_volume.py — 可选合并：归档文件转PDF -> 合并 -> 页脚页码 -> 回填目录

用法:
  python merge_volume.py <输出文件夹> [firm_config_base] [plan_json]
或经 archive_case.py 在用户本次明确同意并传入 --merge yes 时调用。
只处理「可完卷」时的合并需求；非所有律师需要（见 preferences.merge_pdf）。
"""
import os, sys, json, tempfile, glob

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pdf_util


def ordered_files(out_dir, plan):
    """按归档顺序返回输出目录下实际存在的文件列表（含每项的起始页信息原料）。"""
    found = []
    for item in plan['order']:
        if item['type'] == 'skip':
            continue
        base = item['out']
        matches = [f for f in os.listdir(out_dir)
                   if f.startswith(base) and not f.startswith('.') and f != '归档卷宗合集.pdf'
                   and not f.endswith('.txt') and f != plan.get('directory_template_out', '')]
        if matches:
            # 按文件名稳定排序
            matches.sort()
            found.append((item['seq'], item['name'], os.path.join(out_dir, matches[0])))
    return found


def merge_volume(out_dir, firm_base, plan):
    items = ordered_files(out_dir, plan)
    if not items:
        print("[合并] 没有可合并的文件")
        return
    tmp = tempfile.mkdtemp(prefix='merge_')
    pdfs = []
    page_map = []  # (name, start_page)
    cur = 1

    # 整个合并过程复用同一个 Word 实例，避免反复启动/退出 COM 导致代理断开
    import win32com.client, pythoncom
    pythoncom.CoInitialize()
    wd = None
    try:
        wd = win32com.client.Dispatch('Word.Application')
        wd.Visible = False
    except Exception as e:
        print(f"[合并] Word 不可用，doc/docx 将跳过: {e}")
        wd = None
    try:
        for seq, name, fpath in items:
            out_pdf = os.path.join(tmp, f"{seq:02d}_{os.path.basename(fpath)}.pdf")
            r = pdf_util.to_pdf(fpath, out_pdf, wd)
            if not r or str(r).startswith('['):
                print(f"  [跳过] {name}: 转PDF失败 ({r})")
                continue
            pdfs.append(r)
            # 计算页数
            try:
                import fitz
                n = fitz.open(r).page_count
            except Exception:
                n = 1
            page_map.append((name, cur, cur + n - 1))
            cur += n

        if not pdfs:
            print("[合并] 无有效PDF")
            return

        merged = os.path.join(out_dir, '归档卷宗合集.pdf')
        pdf_util.merge_pdfs(pdfs, merged)
        pdf_util.add_page_numbers(merged)
        print(f"[合并] 已生成 {merged}（{cur-1} 页）")

        # 回填目录页码
        _fill_directory(out_dir, plan, page_map, firm_base)

        # 输出页码对照（始终生成，便于核对/Word 不可用时兜底）
        with open(os.path.join(out_dir, '目录页码对照.txt'), 'w', encoding='utf-8') as f:
            for name, s, e in page_map:
                f.write(f"{name}: 第{s}-{e}页\n")
        print("[合并] 目录页码对照.txt 已生成")
    finally:
        if wd is not None:
            try:
                wd.Quit()
            except Exception:
                pass
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass


def _fill_directory(out_dir, plan, page_map, firm_base):
    dt_out = os.path.join(out_dir, plan.get('directory_template_out', '0.归档卷宗目录.doc'))
    if not os.path.exists(dt_out):
        return
    try:
        import win32com.client, pythoncom
        pythoncom.CoInitialize()
        wd = win32com.client.Dispatch('Word.Application')
        wd.Visible = False
        doc = wd.Documents.Open(dt_out)
        # 在第一个表格中，按行匹配目录项名称并写入页码（起始页）
        pm = {name: f"{s}-{e}" for name, s, e in page_map}
        for table in doc.Tables:
            for row in table.Rows:
                cells = [c.Range.Text for c in row.Cells]
                rowtext = ''.join(cells)
                for name, pg in pm.items():
                    if name in rowtext and '页' not in rowtext:
                        # 找最后一个空单元格写入页码
                        for c in row.Cells:
                            if not c.Range.Text.strip().strip('\x07').strip():
                                c.Range.Text = pg
                                break
                        break
        doc.Save()
        doc.Close()
        wd.Quit()
        pythoncom.CoUninitialize()
        print("[合并] 已用 Word 回填目录页码")
    except Exception as e:
        print(f"[合并] 目录回填跳过（Word不可用或格式不符）: {e}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: merge_volume.py <输出文件夹> [firm_base] [plan_json]")
        sys.exit(1)
    out = sys.argv[1]
    if len(sys.argv) > 2:
        fb = sys.argv[2]
    else:
        # 从 settings.json 读取默认律所，fallback tongjing
        config_root = os.path.join(os.path.expanduser('~'), '.workbuddy', 'case-archiver')
        settings = os.path.join(config_root, 'settings.json')
        firm = 'tongjing'
        if os.path.exists(settings):
            try:
                firm = json.load(open(settings, encoding='utf-8')).get('default_firm', 'tongjing')
            except Exception:
                pass
        fb = os.path.join(config_root, 'firm_config', firm)
    pj = sys.argv[3] if len(sys.argv) > 3 else os.path.join(fb, 'archive_plan.json')
    plan = json.load(open(pj, encoding='utf-8'))
    merge_volume(out, fb, plan)
