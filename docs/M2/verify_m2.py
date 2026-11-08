#!/usr/bin/env python3
"""Run: python3 docs/M2/verify_m2.py. QA validation for M2 report PDF."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent
base = root / "N01_M2_THU_NGHIEM_MODULE"
tex = base.with_suffix(".tex").read_text()
log = base.with_suffix(".log").read_text()

# Check fatal compilation log issues
for token in ("undefined", "Missing character", "LaTeX Font Warning"):
    assert token not in log, f"Found '{token}' in log file!"

# Citation order verification
refs = re.findall(r"\\bibitem\{(source\d+)\}", tex)
cites = [key for group in re.findall(r"\\cite\{([^}]+)\}", tex) for key in group.split(",")]
assert list(dict.fromkeys(cites)) == refs, "IEEE first-citation order mismatch!"
assert len(refs) >= 8, f"Expected at least 8 citations, found {len(refs)}"

# Content and metric presence
required_tokens = [
    "23520804", "23520716", "Nguyễn Duy Xuân Bách",
    "top=3cm", "bottom=3.5cm", "left=3.5cm", "right=2cm",
    "\\setmainfont{Times New Roman}", "\\@setfontsize\\normalsize{13}{16}",
    "0{,}1300", "0{,}0652", "20261108_133915", "20261107_101837", "20261107_103243",
    "Gate G1", "Gate G2", "SITL", "Ground Truth", "EKF2", "Optical Flow", "Rangefinder",
    "AUTO\\_LAND", "DISARMED"
]
for token in required_tokens:
    assert token in tex, f"Missing required token in TeX: '{token}'"

# PDF text and undefined reference check
text = subprocess.check_output(["pdftotext", "-layout", str(base.with_suffix(".pdf")), "-"], text=True)
pages = [p for p in text.split("\f") if p.strip()]
assert len(pages) >= 5, f"PDF has too few pages ({len(pages)})"
assert "??" not in text, "Found undefined reference '??' in rendered PDF!"

# Geometry check
xml = subprocess.check_output(["pdftohtml", "-xml", "-hidden", "-i", "-stdout", str(base.with_suffix(".pdf"))], text=True)
for page in ET.fromstring(xml).findall("page"):
    width, height = float(page.attrib["width"]), float(page.attrib["height"])
    for element in page.findall("text"):
        a = element.attrib
        assert 0 <= float(a["left"]) and float(a["left"]) + float(a["width"]) <= width + 5
        assert 0 <= float(a["top"]) and float(a["top"]) + float(a["height"]) <= height + 5

result = {
    "report_name": "N01_M2_THU_NGHIEM_MODULE.pdf",
    "pages_total": len(pages),
    "references_count": len(refs),
    "first_citation_order": "PASS",
    "content_verification": "PASS",
    "page_bounds": "PASS",
    "fatal_warnings": "NONE",
    "sha256": hashlib.sha256(base.with_suffix(".pdf").read_bytes()).hexdigest(),
    "qa_status": "PASS"
}

out_file = root / "QA_M2_RESULT.json"
out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2))
print(json.dumps(result, ensure_ascii=False, indent=2))
