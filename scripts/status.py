"""Print a one-shot status snapshot of the dataset."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
IMG_DIR = ROOT / "images"


def main() -> None:
    files = list(DATA_DIR.glob("*.json"))
    SKIP = {"manifest.json", "artifacts_index.json", "dataset_card.json"}
    artifact_files = [f for f in files if not f.name.startswith("_") and f.name not in SKIP]
    by_source: Counter[str] = Counter()
    by_museum: Counter[str] = Counter()
    n_with_ar = 0
    n_with_en = 0
    n_imgs = 0
    licenses: Counter[str] = Counter()
    qa_pairs = 0
    for p in artifact_files:
        rec = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(rec, dict) or "id" not in rec:
            continue
        if rec["id"].startswith("MET_"):
            by_source["Met Museum"] += 1
        else:
            by_source["Wikipedia"] += 1
        by_museum[rec["current_location"].get("museum_id", "?")] += 1
        if rec["description"].get("ar"):
            n_with_ar += 1
        if rec["description"].get("en"):
            n_with_en += 1
        for img in rec.get("images", []):
            n_imgs += 1
            licenses[img.get("license", "?")] += 1
        qa_pairs += len(rec.get("qa_pairs_ar", []))

    img_files = list(IMG_DIR.glob("*"))
    img_bytes = sum(f.stat().st_size for f in img_files if f.is_file())

    print("== DATASET STATUS ==")
    print(f"Artifact records:     {len(artifact_files)}")
    print(f"  ├ Wikipedia source: {by_source.get('Wikipedia', 0)}")
    print(f"  └ Met OA source:    {by_source.get('Met Museum', 0)}")
    print(f"With AR description:  {n_with_ar}")
    print(f"With EN description:  {n_with_en}")
    print(f"Image files on disk:  {len(img_files)} ({img_bytes / (1024*1024):.1f} MB)")
    print(f"Image-record entries: {n_imgs}")
    print(f"Q&A pairs:            {qa_pairs}")
    print()
    print("Artifacts by museum:")
    for m, c in by_museum.most_common():
        print(f"  {m or '(unspecified)':<10} {c}")
    print()
    print("Image licenses:")
    for lic, c in licenses.most_common():
        print(f"  {lic:<25} {c}")


if __name__ == "__main__":
    main()
