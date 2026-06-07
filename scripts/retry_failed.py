"""Retry seed entries that didn't produce a per-artifact JSON.

Reads the seed list, computes the set of expected IDs, and reruns the build
for any IDs missing from data/. Uses longer pauses to avoid timing out.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import wiki_client as wc
from seed_artifacts import SEED
from build_dataset import build_record, write_record, log


def main() -> None:
    DATA_DIR = ROOT / "data"
    missing: list[tuple[str, str, str, str]] = []
    for entry in SEED:
        aid, en_title, ar_hint, museum_hint = entry
        if not (DATA_DIR / f"{aid}.json").exists():
            missing.append(entry)

    log(f"Retrying {len(missing)} missing artifact records.")
    # bump retries / longer pauses
    wc.MAX_RETRIES = 6
    wc.REQUEST_DELAY = 0.8

    built = 0
    still_failing: list[str] = []
    for aid, en_title, ar_hint, museum_hint in missing:
        try:
            rec = build_record(aid, en_title, ar_hint, museum_hint)
            if rec is None:
                still_failing.append(aid)
                continue
            write_record(rec)
            built += 1
            log(f"  retried ok {aid}: AR={'Y' if rec['description']['ar'] else 'N'} imgs={len(rec['images'])}")
        except Exception as e:
            log(f"  retried XX {aid}: {type(e).__name__}: {e}")
            still_failing.append(aid)
        time.sleep(1.0)

    log(f"\nRETRY DONE. built={built} still_failing={len(still_failing)}")
    if still_failing:
        log("still failing: " + ", ".join(still_failing))


if __name__ == "__main__":
    main()
