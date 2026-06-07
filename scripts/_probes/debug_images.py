"""Debug: check what images Wikipedia parse API returns."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wiki_client as wc

for title in ("Mask of Tutankhamun", "Narmer Palette"):
    print(f"\n=== {title} ===")
    parsed = wc.page_html_parse("en", title)
    if parsed:
        imgs = parsed.get("images", [])
        print(f"Total images on page: {len(imgs)}")
        for i, f in enumerate(imgs[:30]):
            relevant = wc.is_relevant_image(f)
            print(f"  [{ 'Y' if relevant else 'N'}] {f}")
