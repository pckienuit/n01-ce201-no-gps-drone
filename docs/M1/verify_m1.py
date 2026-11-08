"""Run: python3 docs/M1/verify_m1.py. Document QA, not flight validation."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent
workspace = root.parent.parent
base = root / 'N01_M1_KHAO_SAT'
tex = base.with_suffix('.tex').read_text()
log = base.with_suffix('.log').read_text()
for token in ('Overfull', 'undefined', 'Missing character', 'LaTeX Font Warning'):
    assert token not in log, token
refs = re.findall(r'\\bibitem\{(source\d+)\}', tex)
cites = [key for group in re.findall(r'\\cite\{([^}]+)\}', tex) for key in group.split(',')]
assert list(dict.fromkeys(cites)) == refs, 'IEEE first-citation order'
assert len(refs) == 13 and len(refs) - 1 >= 8
ledger = json.loads((workspace / '.research/m1-citations.json').read_text())
assert [f"source{s['id']}" for s in ledger['sources']] == refs
assert all(s.get('quotes') for s in ledger['sources']), 'Source without literal evidence'
for token in ('23520804', '23520716', '19/10/2026', 'trong nước', 'Vicon',
              'ground truth', 'chưa có kết quả SITL', 'chưa được chọn cho CE201',
              'chưa xác nhận hai thành viên đã chốt', 'e_{hold}', 'e_{est}',
              'G1 SITL', 'G2 bench', 'G3 hover', 'G4 square', 'baseline',
              'sai số vận tốc', 'bằng chứng mô phỏng', 'tóm tắt và metadata'):
    assert token in tex, token
for token in ('top=3cm', 'bottom=3.5cm', 'left=3.5cm', 'right=2cm',
              '\\setmainfont{Times New Roman}', '\\@setfontsize\\normalsize{13}{16}',
              '\\onehalfspacing'):
    assert token in tex, token
for claim in ('đã chạy SITL', 'SITL pass.', 'đã bay thật'):
    assert claim not in tex, f'Unsupported claim: {claim}'
text = subprocess.check_output(['pdftotext', '-layout', str(base.with_suffix('.pdf')), '-'], text=True)
pages = [page for page in text.split('\f') if page.strip()]
assert len(pages) >= 5 and all(len(p.strip()) > 150 for p in pages)
assert '??' not in text
xml = subprocess.check_output(['pdftohtml', '-xml', '-hidden', '-i', '-stdout', str(base.with_suffix('.pdf'))], text=True)
for page in ET.fromstring(xml).findall('page'):
    width, height = float(page.attrib['width']), float(page.attrib['height'])
    for element in page.findall('text'):
        a = element.attrib
        assert 0 <= float(a['left']) and float(a['left']) + float(a['width']) <= width + 2
        assert 0 <= float(a['top']) and float(a['top']) + float(a['height']) <= height + 2
# A citation-only projection uses the ledger's rendered URLs without inventing mappings.
projection = root / 'CITATION_AUDIT.md'
projection.write_text('# Citation audit\n\n' + '\n'.join(
    f"Nguồn {key} đã được trích dẫn trong báo cáo.[{int(key[6:])}]" for key in refs) + '\n')
script = Path('/home/pckien/.hermes/profiles/drone-capstone/skills/research/grounded-citations/scripts/sources.py')
subprocess.run(['python3', str(script), '--ledger', str(workspace / '.research/m1-citations.json'),
                'render', '--replace-in', str(projection)], check=True)
subprocess.run(['python3', str(script), '--ledger', str(workspace / '.research/m1-citations.json'),
                'verify', str(projection), '--strict', '--evidence'], check=True)
result = {'pages_total': len(pages), 'references': len(refs), 'survey_sources_excluding_advisor': len(refs)-1,
          'first_citation_order': 'PASS', 'content': 'PASS', 'page_bounds': 'PASS',
          'literal_evidence_presence': 'PASS', 'fatal_layout_or_reference_warnings': 'NONE',
          'underfull_boxes': len(re.findall('Underfull', log)),
          'sha256': hashlib.sha256(base.with_suffix('.pdf').read_bytes()).hexdigest(),
          'note': 'QA checks structure and citation mapping, not all factual claims, advisor approval or flight performance.'}
(root / 'QA_RESULT.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
print(json.dumps(result, ensure_ascii=False, indent=2))
