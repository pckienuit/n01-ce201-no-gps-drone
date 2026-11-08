"""Run after latexmk. Check dates, citations, required content and PDF layout."""
from pathlib import Path
import collections
import datetime as dt
import json
import re
import subprocess
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent
base = root / 'N01_M0_DAC_TA_OPUS'
tex = base.with_suffix('.tex').read_text()
log = base.with_suffix('.log').read_text()
assert not any(x in log for x in ['Overfull', 'undefined', 'Missing character', 'LaTeX Font Warning'])
refs = re.findall(r'\\bibitem\{([^}]+)\}', tex)
cites = [k for group in re.findall(r'\\cite\{([^}]+)\}', tex) for k in group.split(',')]
assert list(dict.fromkeys(cites)) == refs, 'IEEE reference order mismatch'
weeks = re.findall(r'W(\d{2})\\newline(\d{2}/\d{2})--(\d{2}/\d{2})', tex)
assert len(weeks) == 13
for i, (w, first, last) in enumerate(weeks):
    start = dt.date(2026, 9, 28) + dt.timedelta(weeks=i)
    assert int(w) == i + 1
    assert first == start.strftime('%d/%m') and last == (start + dt.timedelta(days=6)).strftime('%d/%m')
for date in ['05/10', '19/10', '09/11', '30/11', '14/12', '28/12']:
    assert date in tex
for token in ['23520804', '23520716', 'vkhZSLVSyV9zHrgx7', 'e_{hold}', 'e_{est}', 'chưa được phê duyệt riêng', 'chưa chạy SITL', 'thị sai']:
    assert token in tex, token
text = subprocess.check_output(['pdftotext', '-layout', str(base.with_suffix('.pdf')), '-'], text=True)
pages = [p for p in text.split('\f') if p.strip()]
assert all(len(p.strip()) > 150 for p in pages), 'Near-empty page'
assert '??' not in text
xml = root / 'm0-layout.xml'
subprocess.run(['pdftohtml', '-xml', '-hidden', '-i', str(base.with_suffix('.pdf')), str(xml)], check=True, stdout=subprocess.DEVNULL)
tree = ET.parse(xml)
fonts = collections.Counter()
specs = {s.attrib['id']: s.attrib for s in tree.findall('.//fontspec')}
for page in tree.findall('.//page'):
    width, height = int(page.attrib['width']), int(page.attrib['height'])
    for el in page.findall('text'):
        a = el.attrib
        assert int(a['left']) >= 0 and int(a['left']) + int(a['width']) <= width + 2
        assert int(a['top']) >= 0 and int(a['top']) + int(a['height']) <= height + 2
        spec = specs.get(a.get('font'), {})
        fonts[(spec.get('family', ''), spec.get('size', ''))] += len(''.join(el.itertext()))
result = {'pages': len(pages), 'weeks': len(weeks), 'references': len(refs), 'citation_order': 'PASS', 'tex_warnings': 'NONE', 'page_bounds': 'PASS', 'dominant_fonts_pdftohtml_scale_1_5': [(str(k), v) for k, v in fonts.most_common(6)]}
(root / 'QA_RESULT.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
print(json.dumps(result, ensure_ascii=False, indent=2))
