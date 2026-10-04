#!/usr/bin/env python3
"""Merge every per-model results file into data/results/benchmark.json.

run_benchmark.py rewrites benchmark.json with only the models of the latest run, so an
earlier model (llm-jp-3-1.8b) was silently dropped from the published dataset. Run this
before scripts/upload_hf.py.
"""
import json
from pathlib import Path

RESULTS = Path("data/results")
rows = []
for f in sorted(RESULTS.glob("*.json")):
    if f.name == "benchmark.json":
        continue
    rows.extend(json.loads(f.read_text()))
(RESULTS / "benchmark.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False))
models = sorted({r["model"] for r in rows})
print(f"merged {len(rows)} rows from {len(models)} models: {models}")
