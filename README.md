# JaCite-Bench

Do LLMs invent Japanese law articles? A bilingual benchmark that checks every statute article an LLM cites against the official e-Gov law registry.

## The problem

LLMs cite Japanese law articles in their answers. But do those articles actually exist? Most Japanese LLM evals score answers against gold labels. This one checks grounding against a symbolic source of truth — the e-Gov Law API v2.

## The approach

1. **Registry**: Pull 11 commonly cited laws (民法, 会社法, 労働基準法, etc.) from e-Gov API v2 into a versioned registry of 6,913 articles
2. **Normaliser**: Map kanji numerals (第五百四十一条 → 541), の-branch numbers (第四百十五条の二 → 415-2), and English forms (Article 541 → 541) to one canonical ID
3. **Questions**: Generate 300 questions per language from official article captions — each with a known gold article
4. **Benchmark**: 3 local LLMs answer every question in both languages; every cited article is resolved against the registry

## Results

| Model | JA invented | EN invented | JA rate | EN rate |
|---|---|---|---|---|
| llm-jp-3-1.8b | 63/1554 | 7/642 | **4.05%** | **1.09%** |
| Swallow-8B | 0/793 | 0/670 | 0.00% | 0.00% |
| Qwen2.5-7B | 9/643 | 0/567 | **1.40%** | 0.00% |

**LLMs invent Japanese law articles more often when asked in Japanese.** The llm-jp model's JA rate is 3.7× its EN rate. Qwen2.5-7B shows the same pattern (1.40% vs 0%). Swallow-8B is the most grounded — 0% in both languages.

## Key findings

1. **Language matters**: JA prompts produce more invented citations than EN prompts for 2 of 3 models
2. **Model size isn't everything**: The 1.8B model has the highest JA rate; the 8B model has 0%
3. **The normaliser is the hard part**: Kanji numerals, の-branch numbers, and English forms must all map to one canonical ID
4. **Caption-generated questions are honest**: Questions are generated from official captions, not hand-written — the gold article is known without a legal expert

## Limitations

- Checks that an article exists, not whether the legal reasoning is right
- Questions are template-generated from captions — easier and less natural than real use
- 3 local models only; no frontier API baselines
- Japanese is limited; questions are generated from official text, not hand-written

## Usage

```bash
# Build registry
PYTHONPATH=src python -m jacite.registry

# Generate questions
PYTHONPATH=src python -m jacite.questions

# Run benchmark
PYTHONPATH=src python scripts/run_benchmark.py
```

## License

MIT
