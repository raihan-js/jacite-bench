#!/usr/bin/env python3
"""Run JaCite-Bench: 4 local Japanese LLMs, both languages, invented-citation rate.

Usage:
  PYTHONPATH=src python scripts/run_benchmark.py
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np

from jacite.normaliser import extract_cited_articles

MODELS = [
    "llm-jp/llm-jp-3-1.8b-instruct3",
    "sbintuitions/sarashina2.2-1b-instruct-v0.1",
    "tokyotech-llm/Llama-3.1-Swallow-8B-Instruct-v0.3",
    "Qwen/Qwen2.5-7B-Instruct",
]

RESULTS = Path("data/results")


def load_registry(path: str) -> dict:
    """Load registry and build lookup: (law_id, article) -> exists."""
    registry = json.loads(Path(path).read_text())
    lookup = {}
    for law in registry["laws"]:
        law_id = law["law_id"]
        for article in law["articles"]:
            from jacite.normaliser import normalise_article_ref
            canonical = normalise_article_ref(article["article"])
            if canonical:
                lookup[(law_id, canonical)] = article
    return registry, lookup


def check_citations(text: str, lookup: dict, law_id: str) -> dict:
    """Check cited articles against the registry.

    Returns dict with: cited (list), invented (list), real_not_gold (list).
    """
    cited = extract_cited_articles(text)
    invented = []
    real_not_gold = []
    for ref in cited:
        if (law_id, ref) in lookup:
            real_not_gold.append(ref)
        else:
            invented.append(ref)
    return {"cited": cited, "invented": invented, "real_not_gold": real_not_gold}


def bootstrap_ci(invented: list, n: int, n_bootstrap: int = 2000,
                  seed: int = 42) -> tuple[float, float]:
    """Bootstrap 95% CI for invented-citation rate."""
    rng = np.random.default_rng(seed)
    arr = np.array(invented, dtype=float)
    if n == 0:
        return 0.0, 0.0
    boot = np.zeros(n_bootstrap)
    for i in range(n_bootstrap):
        sample = rng.choice(arr, size=n, replace=True)
        boot[i] = sample.mean()
    return float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))


def run_model(model_name: str, questions: list, lookup: dict,
              device: str = "cuda", max_new_tokens: int = 512) -> list:
    """Run one model on all questions."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    print(f"  Loading {model_name}...", flush=True)
    tok = AutoTokenizer.from_pretrained(model_name)

    from transformers import BitsAndBytesConfig
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map=device,
    )
    model.eval()

    results = []
    for i, q in enumerate(questions):
        messages = [{"role": "user", "content": q["question"]}]
        formatted = tok.apply_chat_template(messages, tokenize=False,
                                            add_generation_prompt=True)
        inputs = tok(formatted, return_tensors="pt").to(device)

        t0 = time.time()
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=max_new_tokens,
                                do_sample=False)
        elapsed = time.time() - t0

        response = tok.decode(out[0][inputs.input_ids.shape[1]:],
                              skip_special_tokens=True)

        citation = check_citations(response, lookup, q["law_id"])
        results.append({
            "id": q["id"],
            "model": model_name,
            "language": q["language"],
            "law": q["law"],
            "law_id": q["law_id"],
            "gold_article": q["gold_article"],
            "response": response,
            "cited": citation["cited"],
            "invented": citation["invented"],
            "real_not_gold": citation["real_not_gold"],
            "n_cited": len(citation["cited"]),
            "n_invented": len(citation["invented"]),
            "elapsed": round(elapsed, 2),
        })

        if (i + 1) % 50 == 0:
            print(f"    {i+1}/{len(questions)}", flush=True)

    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", default="data/registry.json")
    ap.add_argument("--questions", default="data/questions.json")
    ap.add_argument("--models", nargs="*", default=MODELS)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--max-new-tokens", type=int, default=512)
    args = ap.parse_args()

    registry, lookup = load_registry(args.registry)
    questions = json.loads(Path(args.questions).read_text())
    print(f"Registry: {len(registry['laws'])} laws, {len(lookup)} articles")
    print(f"Questions: {len(questions)}")
    print(f"Models: {args.models}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    all_results = []

    for model_name in args.models:
        print(f"\n=== {model_name} ===", flush=True)
        results = run_model(model_name, questions, lookup,
                            device=args.device, max_new_tokens=args.max_new_tokens)
        all_results.extend(results)

        # Save per-model results
        model_file = RESULTS / f"{model_name.replace('/', '_')}.json"
        model_file.write_text(json.dumps(results, indent=2, ensure_ascii=False))
        print(f"  Saved {model_file}")

    # Summary
    (RESULTS / "benchmark.json").write_text(json.dumps(all_results, indent=2, ensure_ascii=False))

    print(f"\n{'model':45s} {'lang':5s} {'n':>5s} {'cited':>7s} {'invented':>10s} {'rate':>7s} {'95% CI':>15s}")
    for model_name in args.models:
        for lang in ["ja", "en"]:
            rows = [r for r in all_results if r["model"] == model_name and r["language"] == lang]
            n = len(rows)
            total_cited = sum(r["n_cited"] for r in rows)
            total_invented = sum(r["n_invented"] for r in rows)
            rate = total_invented / total_cited if total_cited > 0 else 0.0
            ci_low, ci_high = bootstrap_ci([r["n_invented"] for r in rows], n)
            print(f"{model_name:45s} {lang:5s} {n:5d} {total_cited:7d} {total_invented:10d} {rate:7.4f} [{ci_low:.4f}, {ci_high:.4f}]")

    print(f"\nSaved {RESULTS / 'benchmark.json'}")


if __name__ == "__main__":
    main()
