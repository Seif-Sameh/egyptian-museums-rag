"""Generate a `dataset_card.json` summary for the frontend's About panel."""
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def main() -> None:
    manifest = json.loads((DATA_DIR / "manifest.json").read_text(encoding="utf-8"))
    museums = json.loads((DATA_DIR / "_museums.json").read_text(encoding="utf-8"))
    qa_path = DATA_DIR / "_qa_eval.jsonl"
    n_qa = sum(1 for _ in qa_path.open(encoding="utf-8")) if qa_path.exists() else 0

    card = {
        "name_ar": "مجموعة بيانات المتاحف المصرية متعددة الوسائط",
        "name_en": "Egyptian Museums Multimodal Dataset",
        "purpose_ar": "دعم نظام استرجاع وإجابة أسئلة (RAG) باللغة العربية حول الآثار المصرية في المتحف المصري الكبير، المتحف المصري بالتحرير، المتحف القومي للحضارة المصرية، ومجموعات مصرية مختارة في كبرى متاحف العالم.",
        "purpose_en": "Powers an Arabic Retrieval-Augmented Generation system for Egyptian artifacts in the Grand Egyptian Museum, the Egyptian Museum at Tahrir, the National Museum of Egyptian Civilization, and major world holdings.",
        "languages": ["ar", "en"],
        "modalities": ["text", "image"],
        "size": {
            "artifacts": manifest.get("n_artifacts", 0),
            "images": manifest.get("n_images", 0),
            "rag_chunks": manifest.get("n_chunks", 0),
            "qa_pairs": n_qa,
            "museums": len(museums),
            "halls": sum(len(m.get("halls", [])) for m in museums),
        },
        "sources": [
            {
                "name": "Wikipedia",
                "languages": ["ar", "en"],
                "license": "CC BY-SA 4.0",
                "what": "Plain-text artifact descriptions, infobox metadata, interlanguage alignment",
                "url": "https://www.wikipedia.org",
            },
            {
                "name": "Wikimedia Commons",
                "license": "varies (per-file in image record)",
                "what": "Artifact photographs with curator-provided captions and credit lines",
                "url": "https://commons.wikimedia.org",
            },
            {
                "name": "The Metropolitan Museum of Art (Open Access)",
                "license": "CC0 1.0",
                "what": "Public-domain Egyptian artifact records and high-resolution photographs",
                "url": "https://www.metmuseum.org/art/collection",
            },
        ],
        "image_licenses": manifest.get("image_licenses", {}),
        "by_museum": manifest.get("by_museum", {}),
        "schema": {
            "per_artifact_record": [
                "id", "names (ar/en/alt)", "category", "period (ar/en/years)",
                "dynasty (ar/en)", "material[]", "dimensions", "provenance",
                "discovery (year/by)", "current_location (museum_id/hall_id/city)",
                "description (ar/en, with intro)", "images[] (filename/license/credit/dims)",
                "sources[]", "tags[]", "related_ids[]", "qa_pairs_ar[]"
            ],
            "frontend_files": {
                "list_view": "data/artifacts_index.json",
                "detail_view": "data/<ID>.json",
                "rag_chunks": "data/chunks.jsonl",
                "museums": "data/_museums.json",
                "halls": "data/_halls.json",
                "qa_eval": "data/_qa_eval.jsonl",
                "relations": "data/_relations.json",
            },
        },
        "usage_notes_ar": "كل قطعة تحمل صورها وحقوقها على مستوى الصورة (لا تفترض ترخيصًا واحدًا للمجموعة). النصوص العربية مأخوذة من ويكيبيديا أو مُولّدة من بيانات منظمة عبر قواميس مصرية مُنسّقة يدويًا.",
        "usage_notes_en": "Each image carries its own license — never assume one license for the corpus. Arabic text is sourced from Arabic Wikipedia or synthesized from structured fields via a hand-curated Egyptological glossary.",
        "built_with": "Wikipedia/MediaWiki API, Wikimedia Commons API, The Met Museum Open Access API, Python 3 standard library + BeautifulSoup",
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
    out = DATA_DIR / "dataset_card.json"
    out.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
