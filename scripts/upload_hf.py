#!/usr/bin/env python3
"""Upload JaCite-Bench dataset to Hugging Face."""
import subprocess, sys
from huggingface_hub import HfApi

# data/results/benchmark.json is written by scripts/rescore.py (corrected extractor; first-release values kept as *_v1). merge_results.py is only needed when
# the per-model files from a fresh run_benchmark.py exist next to it.
import json
from pathlib import Path
if not Path("data/results/benchmark.json").exists() or "cited_v1" not in json.loads(Path("data/results/benchmark.json").read_text())[0]:
    subprocess.run([sys.executable, "scripts/merge_results.py"], check=True)

api = HfApi()

files = [
    ("data/registry.json", "registry.json"),
    ("data/questions.json", "questions.json"),
    ("data/results/benchmark.json", "benchmark.json"),
]

for local, remote in files:
    if not Path(local).exists():                      # unchanged files may not be on this machine (restore with `hf download`); skip them
        print(f"  skipped {remote} (not found locally)")
        continue
    api.upload_file(
        path_or_fileobj=local,
        path_in_repo=remote,
        repo_id="raihan-js/jacite-bench",
        repo_type="dataset",
    )
    print(f"  uploaded {remote}")

readme = """---
license: apache-2.0
task_categories:
- text-generation
tags:
- japanese-law
- hallucination
- benchmark
pretty_name: JaCite-Bench
---

# JaCite-Bench

Do LLMs invent Japanese law articles? Bilingual benchmark checking every cited article against the official e-Gov law registry.

## Files

- `registry.json` — 11 laws, 6,913 articles listed (4,842 distinct canonical ids) from e-Gov Law API v2; supplementary provisions and deleted placeholders ("削除") are included
- `questions.json` — 600 questions (300 JA, 300 EN) generated from article captions
- `benchmark.json` — 3 models x 600 questions with the model response and its citations. `cited`, `invented`, `n_cited`, `n_invented`, `real_not_gold` are the CORRECTED values; the first release's values are kept as `cited_v1`, `invented_v1`, `n_cited_v1`, `n_invented_v1`

## Correction (2026-10-06)

The first release's extractor reported the prefix of every branch citation as a phantom second citation (第二条の二 gave "2-2" and "2"). Corrected rates (invented mentions / cited mentions):
- llm-jp-3-1.8b: JA 63/1,379 = 4.57% (was 4.05%), EN 7/642 = 1.09%; ratio 4.2x (was 3.7x)
- Qwen2.5-7B: JA 7/597 = 1.17% (was 9/643 = 1.40%), EN 0/567
- Swallow-8B: 0/753 JA, 0/670 EN (unchanged)

Gold-hit counts are unchanged. A citation of a deleted placeholder (e.g. 民法第208条) counts as existing here; excluding deleted placeholders gives 66/1,379, 12/597 and 2/753 for the Japanese answers.

## Key finding

LLMs invent Japanese law articles more often when asked in Japanese (llm-jp-3-1.8b 4.57% vs 1.09%, Qwen2.5-7B 1.17% vs 0.00%); Swallow-8B invents none under the registry definition above.
"""

api.upload_file(
    path_or_fileobj=readme.encode(),
    path_in_repo="README.md",
    repo_id="raihan-js/jacite-bench",
    repo_type="dataset",
)
print("  uploaded README.md")
print("Done: raihan-js/jacite-bench")
