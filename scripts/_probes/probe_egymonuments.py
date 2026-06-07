"""Probe egymonuments.gov.eg JS bundle for API endpoints — broader patterns."""
import re
from pathlib import Path

js = Path("/tmp/em_main.js").read_text()

print("=== All WebAPI / api endpoints ===")
patterns = re.findall(r"""['"]?(/[A-Za-z][A-Za-z0-9_]*WebAPI/[A-Za-z0-9_?=&]+)""", js)
for p in sorted(set(patterns)):
    print(p)

print("\n=== /_api or /api or /Services ===")
patterns = re.findall(r"""['"](/(?:_api|api|Services|services)/[^'"\s]+)""", js)
for p in sorted(set(patterns))[:80]:
    print(p)

print("\n=== Generic strings starting with `/` and with API hints ===")
patterns = re.findall(r"""['"](/[A-Za-z][A-Za-z0-9_/?&=.-]{4,200})['"]""", js)
hits = [p for p in patterns if "API" in p or "Get" in p or "List" in p or "Detail" in p]
for p in sorted(set(hits))[:80]:
    print(p)
