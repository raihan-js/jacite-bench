"""e-Gov law registry builder.

Fetches commonly cited Japanese laws from the e-Gov Law API v2 and builds a
versioned registry of (law_id, article, branch, caption, revision_date).

The registry is the symbolic source of truth: an article citation is "real" if
and only if it exists in the registry at the pinned revision.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import requests

API_BASE = "https://laws.e-gov.go.jp/api/2"

# ~30 commonly cited Japanese laws with known law_ids
# Format: (name, law_id)
COMMON_LAWS = [
    ("民法", "129AC0000000089"),
    ("民法施行法", "131AC0000000011"),
    ("刑法", "140AC0000000045"),
    ("商法", "132AC0000000048"),
    ("会社法", "417AC0000000086"),
    ("労働基準法", "322AC0000000049"),
    ("健康保険法", "211AC0000000070"),
    ("刑事訴訟法", "323AC0000000131"),
    ("国家賠償法", "322AC0000000125"),
    ("国家公務員法", "322AC0000000120"),
    ("地方自治法", "322AC0000000067"),
]


def search_law(name: str) -> dict | None:
    """Search for a law by name. Returns the best matching current law."""
    resp = requests.get(f"{API_BASE}/laws", params={"name": name}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    laws = data.get("laws", [])
    if not laws:
        return None

    # Score laws: prefer exact title match, current enforced, Act type
    def score(law):
        rev = law.get("revision_info", {})
        title = rev.get("law_title", "")
        law_type = law.get("law_info", {}).get("law_type", "")
        s = 0
        if title == name:
            s += 1000
        elif name in title:
            s += 100
        if rev.get("current_revision_status") == "CurrentEnforced":
            s += 50
        if law_type == "Act":
            s += 10
        return s

    laws.sort(key=score, reverse=True)
    return laws[0]


def fetch_law_data(law_id: str) -> dict | None:
    """Fetch full law data including articles."""
    resp = requests.get(f"{API_BASE}/law_data/{law_id}", timeout=60)
    if resp.status_code != 200:
        return None
    return resp.json()


def extract_articles(law_full_text: dict) -> list[dict]:
    """Extract articles with captions from the nested law text tree.

    Returns list of {article, branch, caption} dicts.
    """
    articles = []

    def walk(node):
        if not isinstance(node, dict):
            if isinstance(node, list):
                for item in node:
                    walk(item)
            return

        tag = node.get("tag", "")
        children = node.get("children", [])

        if tag == "Article":
            article_num = None
            caption = None
            for child in children:
                if isinstance(child, dict):
                    if child.get("tag") == "ArticleTitle":
                        # ArticleTitle children contain the number
                        for c in child.get("children", []):
                            if isinstance(c, str):
                                article_num = c.strip()
                                break
                    elif child.get("tag") == "ArticleCaption":
                        for c in child.get("children", []):
                            if isinstance(c, str):
                                caption = c.strip()
                                break
            if article_num:
                articles.append({
                    "article": article_num,
                    "caption": caption or "",
                })

        for child in children:
            walk(child)

    walk(law_full_text)
    return articles


def build_registry(laws: list[tuple[str, str]], output_path: Path,
                   delay: float = 0.5) -> dict:
    """Build a versioned registry of laws and their articles.

    Args:
        laws: List of (name, law_id) tuples.
        output_path: Where to save the registry JSON.
        delay: Delay between API calls (seconds).

    Returns:
        Registry dict with metadata and laws.
    """
    registry = {
        "source": "e-Gov Law API v2",
        "api_version": "2.1.139",
        "laws": [],
    }

    for name, law_id in laws:
        print(f"  Fetching: {name} ({law_id})...", flush=True)
        full = fetch_law_data(law_id)
        if full is None:
            print(f"    FAILED (404 or error)")
            continue

        rev = full.get("revision_info", {})
        title = rev.get("law_title", name)
        revision_id = rev.get("law_revision_id", "")
        updated = rev.get("updated", "")

        articles = extract_articles(full.get("law_full_text", {}))
        print(f"    {len(articles)} articles extracted", flush=True)

        registry["laws"].append({
            "law_id": law_id,
            "title": title,
            "revision_id": revision_id,
            "updated": updated,
            "articles": articles,
        })
        time.sleep(delay)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False))
    print(f"\nRegistry saved to {output_path}")
    print(f"  {len(registry['laws'])} laws, {sum(len(l['articles']) for l in registry['laws'])} total articles")
    return registry


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="data/registry.json")
    ap.add_argument("--delay", type=float, default=0.5)
    args = ap.parse_args()

    build_registry(COMMON_LAWS, Path(args.output), delay=args.delay)


if __name__ == "__main__":
    main()
