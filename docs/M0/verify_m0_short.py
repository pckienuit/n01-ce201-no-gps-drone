"""QA bản M0 rút gọn: chạy từ root bằng python3 docs/M0/verify_m0_short.py."""
from pathlib import Path
import datetime as dt
import json
import re
import subprocess
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent
base = root / 'N01_M0_DAC_TA_RUT_GON'
tex = base.with_suffix('.tex').read_text()
log = base.with_suffix('.log').read_text()
for token in ['Overfull', 'undefined', 'Missing character', 'LaTeX Font Warning', 'Suppressing empty link']:
    assert token not in log, token
refs = re.findall(r'\\bibitem\{([^}]+)\}', tex)
cites = [key for group in re.findall(r'\\cite\{([^}]+)\}', tex) for key in group.split(',')]
assert list(dict.fromkeys(cites)) == refs, 'IEEE reference order mismatch'
assert len(refs) >= 9, 'Expected advisor source plus at least eight survey sources'
weeks = re.findall(r'W(\d{2})\\newline(\d{2}/\d{2})--(\d{2}/\d{2})', tex)
assert len(weeks) == 13
for i, (week, first, last) in enumerate(weeks):
    start = dt.date(2026, 9, 28) + dt.timedelta(weeks=i)
    assert int(week) == i + 1
    assert first == start.strftime('%d/%m')
    assert last == (start + dt.timedelta(days=6)).strftime('%d/%m')
for token in ['23520804', '23520716', '05/10', '19/10', '09/11', '30/11', '14/12', '28/12',
              'dự kiến, chưa đo', 'Đã có', 'Cần mượn', 'Cần mua',
              'tháo cánh', 'Không bỏ prearm', 'GT', 'e_{hold}', 'e_{est}',
              # Bản gửi GVHD: phân công phải ghi là đề xuất, chưa được hai thành viên chốt.
              'Phân công dưới đây là phương án đề xuất, hai thành viên chưa chốt',
              'trong nước', 'chưa khóa',
              # Trạng thái thật thay cho câu "Chưa nộp M0": bản nộp phải nêu chưa chạy thử.
              'chưa chạy SITL',
              # KPI gốc giữ nguyên văn; diễn giải và module phải ghi rõ chưa được duyệt.
              'giữ vị trí sai lệch ≤±0,5~m trong 30~s', '2×2~m', 'ground truth',
              'chưa được duyệt', 'cần GVHD xác nhận', 'p_{sp}', 'p_{GT}', '\\hat p']:
    assert token in tex, token
# Link Form cũ bị lỗi không được xuất hiện; link nộp đúng lưu ở progress/SUBMISSION_CONFIG.md.
assert 'TZAZpMQfSAvGi9x6A' not in tex, 'Old broken form link'
# Không nhận đã nộp, đã được duyệt hoặc đã chạy/bay đạt.
for claim in ['đã nộp', 'đã duyệt', 'đã được duyệt', 'đã phê duyệt', 'đã xác nhận',
              'sitl pass', 'flight pass', 'bench pass', 'đã bay thật', 'đã chạy sitl']:
    assert claim not in tex.lower(), f'Unsupported claim: {claim}'
for token in ['top=3cm', 'bottom=3.5cm', 'left=3.5cm', 'right=2cm',
              '\\setmainfont{Times New Roman}', '\\@setfontsize\\normalsize{13}{16}', '\\onehalfspacing']:
    assert token in tex, token
# Văn bản, bảng, chú thích và tài liệu tham khảo đều 13pt; chỉ nhãn trong hình TikZ được nhỏ hơn.
for cmd in ['\\small', '\\footnotesize', '\\scriptsize', '\\tiny', '\\large', '\\Large']:
    assert cmd not in tex, cmd
outside_figures = re.sub(r'\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}', '', tex, flags=re.S)
small_sizes = [int(size) for size in re.findall(r'\\fontsize\{(\d+)\}', outside_figures)]
assert all(size >= 13 for size in small_sizes), f'Font below 13pt outside figures: {small_sizes}'
text = subprocess.check_output(['pdftotext', '-layout', str(base.with_suffix('.pdf')), '-'], text=True)
pages = [page for page in text.split('\f') if page.strip()]
assert 3 <= len(pages) <= 5, f'Page limit failed: {len(pages)}'
assert all(len(page.strip()) > 500 for page in pages), 'Near-empty page'
assert '??' not in text
xml_text = subprocess.check_output(['pdftohtml', '-xml', '-hidden', '-i', '-stdout', str(base.with_suffix('.pdf'))], text=True)
tree = ET.fromstring(xml_text)
for page in tree.findall('page'):
    width, height = float(page.attrib['width']), float(page.attrib['height'])
    for element in page.findall('text'):
        a = element.attrib
        assert float(a['left']) >= 0 and float(a['left']) + float(a['width']) <= width + 2
        assert float(a['top']) >= 0 and float(a['top']) + float(a['height']) <= height + 2
result = {'pages': len(pages), 'page_limit_3_5': 'PASS', 'weeks': len(weeks),
          'references': len(refs), 'citation_order': 'PASS', 'tex_warnings': 'NONE',
          'page_bounds': 'PASS', 'required_content': 'PASS', 'no_unsupported_claims': 'PASS',
          'font_13pt_outside_figures': 'PASS',
          'note': 'Automated checks do not imply advisor approval, submission or flight validation.'}
(root / 'QA_SHORT_RESULT.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
print(json.dumps(result, ensure_ascii=False, indent=2))
