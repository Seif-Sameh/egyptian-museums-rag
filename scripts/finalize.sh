#!/bin/bash
# Run the post-build integration pipeline.
# Use after the long-running Wikipedia + Met builds have completed.

set -e
cd "$(dirname "$0")/.."
echo "=== [1/6] Refreshing Met-record Arabic translations ==="
python3 scripts/refresh_met_ar.py
echo "=== [2/6] Retrying failed Wikipedia seeds with fixed titles ==="
python3 scripts/retry_failed.py || true
echo "=== [3/6] Enriching missing AR descriptions deterministically ==="
python3 scripts/enrich_ar.py
echo "=== [4/6] Computing artifact relations ==="
python3 scripts/compute_relations.py
echo "=== [5/6] Generating Q&A + packaging ==="
python3 scripts/build_qa.py
python3 scripts/package.py
echo "=== [6/6] Writing dataset card ==="
python3 scripts/dataset_card.py
echo
echo "=== STATUS ==="
python3 scripts/status.py
echo
echo "DONE. View the dataset by running:"
echo "  cd \"$(pwd)\" && python3 -m http.server 8000"
echo "Then open http://localhost:8000/viewer.html"
