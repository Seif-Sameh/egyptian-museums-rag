#!/bin/bash
# Orchestration script — runs all stages end-to-end.
# Use after the long-running builds complete.

set -e
cd "$(dirname "$0")/.."

echo "[1/5] Wikipedia AR/EN pipeline …"
python3 scripts/build_dataset.py
echo "[2/5] Met Museum public-domain Egyptian objects …"
python3 scripts/met_museum.py 200
echo "[3/5] Museums + halls master index …"
python3 scripts/build_museums.py
echo "[4/5] Enrich missing Arabic content via deterministic glossary …"
python3 scripts/enrich_ar.py
echo "[5/5] Retry failed seeds and re-enrich …"
python3 scripts/retry_failed.py || true
python3 scripts/enrich_ar.py
echo "[6/8] Refresh Met-record Arabic translations …"
python3 scripts/refresh_met_ar.py
echo "[7/8] Compute artifact-to-artifact relations …"
python3 scripts/compute_relations.py
echo "[8/9] Generate Q&A …"
python3 scripts/build_qa.py
echo "[9/9] Validate, dedupe, package + dataset card …"
python3 scripts/package.py
python3 scripts/dataset_card.py
python3 scripts/status.py
echo
echo "DONE. Open viewer.html with a local server to browse the dataset."
echo "Tip:  python3 -m http.server 8000  (then http://localhost:8000/viewer.html)"
