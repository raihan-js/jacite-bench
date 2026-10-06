#!/usr/bin/env python3
"""Re-score saved model responses with the CURRENT extractor and registry; writes data/results/benchmark.json and prints the tables.

  hf download raihan-js/jacite-bench benchmark.json registry.json --repo-type dataset --local-dir data/hf
  python scripts/rescore.py --benchmark data/hf/benchmark.json --registry data/hf/registry.json

The old fields are kept as cited_v1 / invented_v1 / n_cited_v1 / n_invented_v1 (what the first release computed with the first extractor); `--check-v1` reproduces
them with the first extractor's behaviour to show the recorded numbers were exactly its output. Rates are per MENTION (a citation repeated in an answer counts each time).
"""
import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

from scipy.stats import fisher_exact

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from jacite.normaliser import extract_cited_articles, normalise_article_ref  # noqa: E402


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark", default="data/hf/benchmark.json")
    ap.add_argument("--registry", default="data/hf/registry.json")
    ap.add_argument("--out", default="data/results/benchmark.json")
    a = ap.parse_args()
    rows = json.loads(Path(a.benchmark).read_text())
    reg = json.loads(Path(a.registry).read_text())
    known = {l["law_id"]: {normalise_article_ref(x["article"]) for x in l["articles"]} - {None} for l in reg["laws"]}
    out = []
    for r in rows:
        r = dict(r)
        if "cited_v1" not in r:
            r["cited_v1"], r["invented_v1"], r["n_cited_v1"], r["n_invented_v1"] = r["cited"], r["invented"], r["n_cited"], r["n_invented"]
        cited = extract_cited_articles(r["response"])
        ids = known[r["law_id"]]
        r["cited"], r["invented"] = cited, [c for c in cited if c not in ids]
        r["real_not_gold"] = sorted({c for c in cited if c in ids and c != r["gold_article"]})
        r["n_cited"], r["n_invented"] = len(cited), len(r["invented"])
        out.append(r)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=2, ensure_ascii=False))
    agg = defaultdict(lambda: defaultdict(int))
    for r in out:
        k = (r["model"].split("/")[-1], r["language"])
        agg[k]["n"] += r["n_cited"]; agg[k]["inv"] += r["n_invented"]; agg[k]["n_v1"] += r["n_cited_v1"]; agg[k]["inv_v1"] += r["n_invented_v1"]
        agg[k]["q"] += 1; agg[k]["gold"] += r["gold_article"] in set(r["cited"]); agg[k]["gold_v1"] += r["gold_article"] in set(eval(r["cited_v1"]) if isinstance(r["cited_v1"], str) else r["cited_v1"])
    print(f"{'model':36s} {'lang':4s} | first release  | corrected      | rate [Wilson 95%]       | gold hit")
    for (m, lang), v in sorted(agg.items()):
        lo, hi = wilson(v["inv"], v["n"])
        print(f"{m:36s} {lang:4s} | {v['inv_v1']:3d}/{v['n_v1']:5d}  | {v['inv']:3d}/{v['n']:5d}  | {100 * v['inv'] / max(v['n'], 1):5.2f}% [{100 * lo:.1f}, {100 * hi:.1f}] | {v['gold']}/{v['q']} (was {v['gold_v1']})")
    print("\nFisher exact, Japanese vs English (per mention):")
    for m in sorted({k[0] for k in agg}):
        j, e = agg[(m, "ja")], agg[(m, "en")]
        p = fisher_exact([[j["inv"], j["n"] - j["inv"]], [e["inv"], e["n"] - e["inv"]]])[1] if j["inv"] + e["inv"] else float("nan")
        ratio = (j["inv"] / j["n"]) / (e["inv"] / e["n"]) if e["inv"] else float("nan")
        print(f"  {m:36s} JA {j['inv']}/{j['n']} vs EN {e['inv']}/{e['n']}  ratio {ratio:.2f}  p = {p:.3g}")


if __name__ == "__main__":
    main()
