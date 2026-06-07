"""Find X.BaseUrl and culture values in the JS bundle."""
import re
from pathlib import Path

js = Path("/tmp/em_main.js").read_text()

# Find variable X with BaseUrl
print("=== BaseUrl candidates ===")
for m in re.finditer(r"BaseUrl\s*[:=]\s*['\"]([^'\"]+)['\"]", js):
    print("BaseUrl =", m.group(1))

print("\n=== Culture candidates ===")
for m in re.finditer(r"Culture\s*[:=]\s*['\"]([^'\"]+)['\"]", js):
    print("Culture =", m.group(1))

print("\n=== X = {...} object literal ===")
# Find module pattern X={BaseUrl:'...',Culture:'...'}
for m in re.finditer(r"\{[^{}]{0,100}BaseUrl\s*:\s*['\"]([^'\"]+)['\"][^{}]{0,200}\}", js):
    print(m.group(0)[:300])

print("\n=== Look for assignments to .BaseUrl ===")
for m in re.finditer(r"(\w+)\.BaseUrl\s*=\s*['\"]([^'\"]+)['\"]", js):
    print(f"{m.group(1)}.BaseUrl = {m.group(2)}")

# Also dump the runtime.js (small) and polyfills as well
runtime = Path("/tmp/em_main.js").read_text()  # placeholder

print("\n=== Lines containing 'BaseUrl' ===")
for i, line in enumerate(re.split(r"[;\n]", js)):
    if "BaseUrl" in line and len(line) < 400:
        print(line.strip()[:400])
