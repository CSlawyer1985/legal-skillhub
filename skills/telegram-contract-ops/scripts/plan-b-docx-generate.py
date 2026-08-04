#!/usr/bin/env python3

from zipfile import ZipFile, ZIP_DEFLATED
from pathlib import Path
import json
import re
import shutil
import sys
import xml.etree.ElementTree as ET

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

WORKSPACE = Path('/Users/vtammm/.openclaw/workspace')
DEFAULT_INPUT = WORKSPACE / 'plan-b-sample-input.json'
DEFAULT_TEMPLATE = WORKSPACE / 'plan-b' / 'templates' / 'talent_individual_template_structured.docx'
DEFAULT_ORIGINAL = WORKSPACE / 'plan-b' / 'originals' / 'talent_individual_original.docx'
DEFAULT_OUTDIR = WORKSPACE / 'plan-b' / 'output'

PARA_REPLACEMENTS = {
    'Số: HĐKV- 070326 - FF - TÔ HOÀNG THY': 'Số: {{contract_no}}',
    'Hôm nay, ngày 07 tháng 03 năm 2026, tại Thành phố Hồ Chí Minh, chúng tôi gồm có:': 'Hôm nay, ngày {{sign_day}} tháng {{sign_month}} năm {{sign_year}}, tại {{sign_city}}, chúng tôi gồm có:',
    'Người đại diện theo pháp luật là: Ông NGUYỄN ANH TÚ': 'Người đại diện theo pháp luật là: {{party_a_representative_pronoun}} {{party_a_legal_representative}}',
    'Theo yêu cầu của bên A về việc thực hiện dự án “VLU ADMISSION 2026”, bên B đảm nhận và thực hiện công việc Diễn viên ghi hình trong dự án với các điều kiện sau:': 'Theo yêu cầu của bên A về việc thực hiện dự án “{{project_name}}”, bên B đảm nhận và thực hiện công việc {{job_title}} trong dự án với các điều kiện sau:',
    'Mục đích sử dụng hình ảnh diễn viên: Trên các phương tiện truyền thông kỹ thuật số dưới dạng video, không bao gồm screenshot hình ảnh từ phim quảng cáo để sử dụng trên các phương tiện truyền thông kỹ thuật số hay các phương tiện in ấn trong phạm vi lãnh thổ Việt Nam': 'Mục đích sử dụng hình ảnh diễn viên: {{usage_purpose}}',
    'Thời hạn sử dụng hình ảnh diễn viên: 1 năm không độc quyền kể từ ngày phát sóng đầu tiên': 'Thời hạn sử dụng hình ảnh diễn viên: {{usage_term}}',
    'Lãnh thổ sử dụng: Việt Nam': 'Lãnh thổ sử dụng: {{usage_territory}}',
    'Thời gian Hợp đồng này được thực hiện là 3 ngày, từ ngày 07/03/2026 đến 09/03/2026': 'Thời gian Hợp đồng này được thực hiện là {{duration_days}} ngày, từ ngày {{start_date}} đến {{end_date}}',
    'Tiền dịch vụ: Thực hiện công việc tại Điều 1 là: 3.000.000 đồng/dự án': 'Tiền dịch vụ: Thực hiện công việc tại Điều 1 là: {{service_fee}} đồng/dự án',
    '(Bằng chữ: Ba triệu đồng), chưa bao gồm tiền thuế thu nhập cá nhân': '(Bằng chữ: {{service_fee_text}}), {{tax_note}}',
    'Phương thức thanh toán: Chuyển khoản': 'Phương thức thanh toán: {{payment_method}}',
    'Bên A thanh toán cho Bên B 100% giá trị hợp đồng tương đương: 3.000.000 đồng (Bằng chữ: Ba triệu đồng), sau khi hai bên ký kết hợp đồng, trong vòng 45 ngày làm việc sau khi hai bên hoàn thành công việc, Bên B bên bàn giao thành phẩm hoàn chỉnh cho Bên A.': '{{payment_terms}}',
}

FIELD_RUN_REPLACEMENTS = {
    'Tên tổ chức: CÔNG TY TNHH FLEX FILMS': ('party_a_company_name', 2),
    'Địa chỉ trụ sở: Số 79 Đường 30, Phường Tân Hưng, Thành phố Hồ Chí Minh': ('party_a_address', 3),
    'Mã số doanh nghiệp: 0315637917': ('party_a_tax_code', 2),
    'Chức vụ: Tổng Giám Đốc': ('party_a_title', 2),
    'Họ và tên: TÔ HOÀNG THY': ('party_b_name', 3),
    'Ngày tháng năm sinh:\xa0 06/04/2004': ('party_b_dob', 2),
    'Căn cước công dân số:\xa0079304002466, ngày cấp 07/04/2021,\xa0 nơi cấp: CTCCS QLHC VTTXH': ('party_b_id_full', 2),
    'Nơi thường trú: 63/7A TL29, KP3C Thạnh Lộc, Quận 12, Thành phố Hồ Chí Minh': ('party_b_permanent_address', 2),
    'Chỗ ở hiện tại:\xa044 Võ Thị Thừa, Phường An Phú Đông, Thành phố Hồ Chí Minh': ('party_b_current_address', 2),
    'Điện thoại:\xa00909898773': ('party_b_phone', 2),
    'Email : hoangthy.to@gmail.com': ('party_b_email', 2),
    'Số TK ngân hàng: 77706042004': ('party_b_bank_account', 2),
    'Tên ngân hàng: Ngân hàng thương mại cổ phần Kỹ Thương Việt Nam (Techcombank)': ('party_b_bank_name', 3),
    'NGUYỄN ANH TÚ                                                                          TÔ HOÀNG THY': ('signature_names', None),
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def slugify(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize('NFD', s)
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
    s = s.replace('đ', 'd').replace('Đ', 'D')
    s = re.sub(r'[^A-Za-z0-9]+', '-', s).strip('-').lower()
    return s or 'output'


def paragraph_text(p):
    return ''.join((t.text or '') for t in p.findall('.//w:t', NS)).strip()


def set_paragraph_text_keep_style(p, new_text):
    texts = p.findall('.//w:t', NS)
    if not texts:
        r = ET.SubElement(p, W + 'r')
        t = ET.SubElement(r, W + 't')
        t.text = new_text
        return
    texts[0].text = new_text
    for t in texts[1:]:
        t.text = ''


def set_value_runs(p, start_index, new_text):
    texts = p.findall('.//w:t', NS)
    if not texts:
        set_paragraph_text_keep_style(p, new_text)
        return
    if start_index >= len(texts):
        texts[-1].text = new_text
        return
    texts[start_index].text = new_text
    for t in texts[start_index + 1:]:
        t.text = ''


def set_signature_runs(p, left_text, right_text):
    texts = p.findall('.//w:t', NS)
    if len(texts) >= 5:
        texts[0].text = '           ' + left_text
        texts[1].text = '                                           '
        texts[2].text = '                     '
        texts[3].text = '   '
        texts[4].text = right_text
    else:
        set_paragraph_text_keep_style(p, f'{left_text}                                                                          {right_text}')


def build_structured_template(src: Path, out: Path):
    tmp = out.parent / '_tmp_structured'
    if tmp.exists():
        shutil.rmtree(tmp)
    ensure_dir(tmp)
    with ZipFile(src) as z:
        z.extractall(tmp)
    doc = tmp / 'word' / 'document.xml'
    tree = ET.parse(doc)
    root = tree.getroot()
    for p in root.findall('.//w:p', NS):
        txt = paragraph_text(p)
        if txt in PARA_REPLACEMENTS:
            set_paragraph_text_keep_style(p, PARA_REPLACEMENTS[txt])
    tree.write(doc, encoding='utf-8', xml_declaration=True)
    with ZipFile(out, 'w', ZIP_DEFLATED) as z:
        for f in tmp.rglob('*'):
            if f.is_file():
                z.write(f, f.relative_to(tmp))
    shutil.rmtree(tmp)


def render_string(s: str, data: dict):
    def repl(m):
        key = m.group(1)
        return str(data.get(key, m.group(0)))
    return re.sub(r'\{\{\s*([A-Za-z0-9_]+)\s*\}\}', repl, s)


def render_docx(template: Path, data: dict, out: Path):
    tmp = out.parent / '_tmp_render'
    if tmp.exists():
        shutil.rmtree(tmp)
    ensure_dir(tmp)
    with ZipFile(template) as z:
        z.extractall(tmp)
    doc = tmp / 'word' / 'document.xml'
    tree = ET.parse(doc)
    root = tree.getroot()
    unresolved = set()

    enriched = dict(data)
    enriched['party_a_representative_full'] = f"{data.get('party_a_representative_pronoun', '')} {data.get('party_a_legal_representative', '')}".strip()
    enriched['party_b_id_full'] = f"{data.get('party_b_id_number', '')}, ngày cấp {data.get('party_b_id_issue_date', '')}, nơi cấp: {data.get('party_b_id_issue_place', '')}".strip()

    for p in root.findall('.//w:p', NS):
        txt = paragraph_text(p)
        if txt in FIELD_RUN_REPLACEMENTS:
            field_name, start_index = FIELD_RUN_REPLACEMENTS[txt]
            if field_name == 'signature_names':
                set_signature_runs(p, data.get('party_a_sign_name', ''), data.get('party_b_sign_name', ''))
                continue
            set_value_runs(p, start_index, str(enriched.get(field_name, '')))
            continue
        if txt in PARA_REPLACEMENTS:
            rendered = render_string(PARA_REPLACEMENTS[txt], data)
            leftovers = re.findall(r'\{\{\s*([A-Za-z0-9_]+)\s*\}\}', rendered)
            unresolved.update(leftovers)
            set_paragraph_text_keep_style(p, rendered)
            continue
        if '{{' in txt and '}}' in txt:
            rendered = render_string(txt, data)
            leftovers = re.findall(r'\{\{\s*([A-Za-z0-9_]+)\s*\}\}', rendered)
            unresolved.update(leftovers)
            set_paragraph_text_keep_style(p, rendered)
    tree.write(doc, encoding='utf-8', xml_declaration=True)
    with ZipFile(out, 'w', ZIP_DEFLATED) as z:
        for f in tmp.rglob('*'):
            if f.is_file():
                z.write(f, f.relative_to(tmp))
    shutil.rmtree(tmp)
    return sorted(unresolved)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'generate'
    if mode == 'build-template':
        out = DEFAULT_TEMPLATE
        ensure_dir(out.parent)
        build_structured_template(DEFAULT_ORIGINAL, out)
        print(json.dumps({'ok': True, 'template': str(out)}, ensure_ascii=False, indent=2))
        return

    input_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_INPUT
    template_path = Path(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_TEMPLATE
    out_dir = Path(sys.argv[4]) if len(sys.argv) > 4 else DEFAULT_OUTDIR
    ensure_dir(out_dir)
    if not template_path.exists():
        build_structured_template(DEFAULT_ORIGINAL, template_path)
    data = load_json(input_path)
    base = f"{slugify(data.get('contract_no','contract'))}__{slugify(data.get('party_b_name','unknown'))}"
    out = out_dir / f'{base}.structured.docx'
    unresolved = render_docx(template_path, data, out)
    print(json.dumps({'ok': True, 'input': str(input_path), 'template': str(template_path), 'output': str(out), 'unresolved': unresolved}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
