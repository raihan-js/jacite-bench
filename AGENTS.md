# AGENTS.md — jacite-bench

Portfolio project for Raihan Sikder. Target roles: Noeon Research (Senior ML Engineer, LLMOps), PayPay Card, Money Forward, Treasure AI, Citadel AI.

## Project: JaCite-Bench

Do LLMs invent Japanese law articles, and does asking in Japanese or English change the rate? A bilingual benchmark that checks every statute article an LLM cites against the official e-Gov law registry.

## Why this project

Most Japanese LLM evals score answers against gold labels. This one checks grounding against a symbolic source of truth — the e-Gov Law API v2. The hard, Japan-specific engineering is a normaliser that maps kanji numerals and の-branch numbers to one canonical ID. Same idea as FedProc (a registry decides whether a clause is real) carried into a second language and a second legal system.

## Stack

Python, e-Gov Law API v2, Hugging Face Transformers, 4-bit quantization (bitsandbytes), pytest.

## Compute

One RTX 3060 12GB. 4 models in 4-bit (~5-6 GB VRAM each) over 600 prompts. A few hours total.

## Milestones

1. **Registry and normaliser** (5d) — e-Gov API v2, kanji numeral normalisation, 100+ pytest cases
2. **Caption-generated question set** (4d) — 300 questions per language from article captions
3. **Run the benchmark** (5d) — 4 local LLMs, both languages, invented-citation rate with 95% bootstrap CIs
4. **Write-up and release** (3d) — HF dataset, dev.to article

## Conventions

- Python 3.10+, pytest for all normaliser and registry tests.
- All models compared on the same fixed question set.
- Questions generated from official captions, not hand-written (limited Japanese).
- Every result cites the exact law_id and revision_id.

## Development

```bash
cd jacite-bench
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v

# Build registry
PYTHONPATH=src python -m jacite.registry

# Generate questions
PYTHONPATH=src python -m jacite.questions

# Run benchmark
PYTHONPATH=src python scripts/run_benchmark.py
```

## Current status

- Registry: 11 laws, 6,913 articles from e-Gov API
- Normaliser: 25 tests passing
- Questions: 600 generated (300 JA, 300 EN)
- Benchmark: running (4 models × 600 questions)
- Pending: HF dataset, dev.to article
