![JaCite-Bench results](https://raw.githubusercontent.com/raihan-js/jacite-bench/HEAD/images/jacite.png)

# Do LLMs Invent Japanese Law Articles? A Bilingual Benchmark

*Checking every statute article an LLM cites against the official e-Gov law registry.*

---

> Scope note: 3 local Japanese-capable LLMs (1.8B–8B), 600 questions generated from official article captions. Not a legal accuracy test — a grounding test.

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

**Two of the three local models invent Japanese law articles more often when asked in Japanese.** The llm-jp model's JA rate is 3.7× its EN rate; Qwen2.5-7B shows the same direction (1.40% vs 0%). Swallow-8B, a Japanese-adapted Llama, invents none in either language.

### Uncertainty

Wilson 95% intervals and Fisher exact tests on the citation counts (rate = invented / all cited articles):

| Model | JA invented | EN invented | JA 95% CI | EN 95% CI | Fisher p, JA vs EN |
|---|---|---|---|---|---|
| llm-jp-3-1.8b | 63/1,554 | 7/642 | [3.2%, 5.2%] | [0.5%, 2.2%] | 1.4e-4 |
| Qwen2.5-7B | 9/643 | 0/567 | [0.7%, 2.6%] | [0.0%, 0.7%] | 0.0043 |
| Swallow-8B | 0/793 | 0/670 | [0.0%, 0.5%] | [0.0%, 0.6%] | n/a |

These treat each cited article as independent. Citations cluster within answers (300 questions per language), so the intervals and p-values are optimistic; a question-level bootstrap is the stricter test. The denominators differ because models cite more articles when answering in Japanese (1,554 vs 642 for llm-jp).

### Did it cite the gold article?

Share of questions where the cited articles include the gold article (from `benchmark.json`):

| Model | JA | EN |
|---|---|---|
| llm-jp-3-1.8b | 292/300 (97.3%) | 298/300 (99.3%) |
| Qwen2.5-7B | 273/300 (91.0%) | 300/300 (100%) |
| Swallow-8B | 300/300 (100%) | 300/300 (100%) |

The `real_not_gold` field in the dataset also records citations that exist in the registry but are not the gold article, so a "real but wrong" rate can be reported from the same data.

## Key findings

1. **Language matters**: JA prompts produce more invented citations than EN prompts for 2 of 3 models
2. **Size is not the whole story**: the 1.8B model has the highest JA rate and the 8B Japanese-adapted model has 0%, but the models also differ in training data, so this is not a clean size comparison
3. **The normaliser is the hard part**: Kanji numerals, の-branch numbers, and English forms must all map to one canonical ID
4. **Caption-generated questions have a known gold article** without needing a legal expert, at the price of being easier than real questions

## Limitations

- Checks that an article exists, not whether the legal reasoning is right
- Questions are template-generated from captions — easier and less natural than real use
- 3 local models only; no frontier API baselines

## What's next

- Add frontier API baselines (GPT-4o, Claude)
- Expand to more laws and more models
- Report the "real but wrong article" rate (the `real_not_gold` field is already in the dataset)

---

*Repo: github.com/raihan-js/jacite-bench · HF dataset: huggingface.co/datasets/raihan-js/jacite-bench · 25 tests green*
