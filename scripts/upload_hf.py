#!/usr/bin/env python3
"""Upload JaCite-Bench dataset to Hugging Face."""
from huggingface_hub import HfApi

api = HfApi()

files = [
    ("data/registry.json", "registry.json"),
    ("data/questions.json", "questions.json"),
    ("data/results/benchmark.json", "benchmark.json"),
]

for local, remote in files:
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

- `registry.json` — 11 laws, 6,913 articles from e-Gov Law API v2
- `questions.json` — 600 questions (300 JA, 300 EN) generated from article captions
- `benchmark.json` — 3 models x 600 questions with invented-citation rates

## Key finding

LLMs invent Japanese law articles more often when asked in Japanese:
- llm-jp-3-1.8b: JA 4.05%, EN 1.09%
- Qwen2.5-7B: JA 1.40%, EN 0.00%
- Swallow-8B: 0% both languages
"""

api.upload_file(
    path_or_fileobj=readme.encode(),
    path_in_repo="README.md",
    repo_id="raihan-js/jacite-bench",
    repo_type="dataset",
)
print("  uploaded README.md")
print("Done: raihan-js/jacite-bench")
