![JaCite-Bench results](https://raw.githubusercontent.com/raihan-js/jacite-bench/HEAD/images/jacite.png)

# Do LLMs Invent Japanese Law Articles? A Bilingual Benchmark

*Checking every statute article an LLM cites against the official e-Gov law registry.*

---

> Scope note: 3 local Japanese-capable LLMs (1.8B–8B), 600 questions generated from official article captions. Not a legal accuracy test — a grounding test.

## A correction before the results

The first version of this repo, public since 2 October, used a citation extractor that reported the prefix of every branch citation as a second, phantom citation: 第二条の二 produced both "2-2" and "2". I found it while reusing the extractor in another project, where a test of branch articles failed. It inflated the citation counts in Japanese answers (llm-jp 1,554 to 1,379 mentions, Qwen2.5-7B 643 to 597, Swallow-8B 793 to 753; English unchanged) and counted two phantom Qwen citations as invented. The numbers below are corrected: llm-jp's Japanese rate goes from 4.05% to 4.57% (the Japanese/English ratio from 3.7× to 4.2×), Qwen2.5-7B's from 1.40% (9/643) to 1.17% (7/597), Swallow-8B stays at 0, the gold-hit counts do not change, and neither do the conclusions. `scripts/rescore.py` reproduces the first release's recorded counts exactly and the corrected ones from the published responses.

A second caveat from the same audit: the registry's 6,913 listed articles include supplementary provisions and deleted placeholders ("削除"), so a citation of a deleted article such as 民法第208条 counts as real. Treating deleted placeholders as non-existent gives 66/1,379 (llm-jp, Japanese), 12/597 (Qwen2.5-7B, Japanese) and 2/753 (Swallow-8B, Japanese); the English counts do not change.

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
| llm-jp-3-1.8b | 63/1,379 | 7/642 | **4.57%** | **1.09%** |
| Swallow-8B | 0/753 | 0/670 | 0.00% | 0.00% |
| Qwen2.5-7B | 7/597 | 0/567 | **1.17%** | 0.00% |

**Two of the three local models invent Japanese law articles more often when asked in Japanese.** The llm-jp model's JA rate is 4.2× its EN rate; Qwen2.5-7B shows the same direction (1.17% vs 0%). Swallow-8B, a Japanese-adapted Llama, invents none in either language (under the registry definition below; 2 of 753 Japanese mentions if deleted placeholders are excluded).

### Uncertainty

Wilson 95% intervals and Fisher exact tests on the citation counts (rate = invented mentions / all cited mentions; a citation repeated in an answer counts each time):

| Model | JA invented | EN invented | JA 95% CI | EN 95% CI | Fisher p, JA vs EN |
|---|---|---|---|---|---|
| llm-jp-3-1.8b | 63/1,379 | 7/642 | [3.6%, 5.8%] | [0.5%, 2.2%] | 2.1e-5 |
| Qwen2.5-7B | 7/597 | 0/567 | [0.6%, 2.4%] | [0.0%, 0.7%] | 0.016 |
| Swallow-8B | 0/753 | 0/670 | [0.0%, 0.5%] | [0.0%, 0.6%] | n/a |

These treat each cited article as independent. Citations cluster within answers (300 questions per language), so the intervals and p-values are optimistic; a question-level bootstrap is the stricter test. The denominators differ because models cite more articles when answering in Japanese (1,379 vs 642 for llm-jp).

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
