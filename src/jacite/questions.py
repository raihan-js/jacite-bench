"""Generate caption-based questions in Japanese and English.

Each question is generated from an article's official caption (見出し) and
has a known gold article. The model's task is to answer the question, and
we check if the articles it cites exist in the registry.

Usage:
  PYTHONPATH=src python -m jacite.questions
"""
import argparse
import json
import random
from pathlib import Path

from jacite.normaliser import normalise_article_ref

# Question templates
JA_TEMPLATES = [
    "【{law}】{ref}の内容を教えてください。",
    "【{law}】{ref}について説明してください。",
    "【{law}】{ref}は何を定めていますか。",
    "【{law}】{ref}の条文を提示してください。",
    "【{law}】{ref}を解説してください。",
]

EN_TEMPLATES = [
    "What does {ref} of the {law} state?",
    "Explain {ref} of the {law}.",
    "What is stipulated in {ref} of the {law}?",
    "Please provide the text of {ref} of the {law}.",
    "Describe {ref} of the {law}.",
]

# English law name mapping
LAW_NAMES_EN = {
    "民法": "Civil Code",
    "民法施行法": "Civil Code Enforcement Act",
    "刑法": "Penal Code",
    "商法": "Commercial Code",
    "会社法": "Companies Act",
    "労働基準法": "Labor Standards Act",
    "健康保険法": "Health Insurance Act",
    "刑事訴訟法": "Code of Criminal Procedure",
    "国家賠償法": "State Redress Act",
    "国家公務員法": "National Public Service Act",
    "地方自治法": "Local Autonomy Act",
}


def generate_questions(registry: dict, n_per_language: int = 300,
                       seed: int = 42) -> list[dict]:
    """Generate questions from article captions.

    Args:
        registry: The law registry dict.
        n_per_language: Number of questions per language.
        seed: Random seed.

    Returns:
        List of question dicts with keys: id, language, law, law_id,
        article, question, gold_article, revision_id.
    """
    rng = random.Random(seed)
    questions = []
    ja_count = 0
    en_count = 0

    for law in registry["laws"]:
        law_id = law["law_id"]
        title = law["title"]
        revision_id = law["revision_id"]
        law_en = LAW_NAMES_EN.get(title, title)

        for article in law["articles"]:
            ref = article["article"]
            caption = article.get("caption", "")

            if not caption:
                continue

            canonical = normalise_article_ref(ref)
            if canonical is None:
                continue

            # Japanese question
            if ja_count < n_per_language:
                template = rng.choice(JA_TEMPLATES)
                q = template.format(law=title, ref=ref)
                questions.append({
                    "id": f"q{len(questions):04d}",
                    "language": "ja",
                    "law": title,
                    "law_id": law_id,
                    "article": ref,
                    "question": q,
                    "gold_article": canonical,
                    "revision_id": revision_id,
                    "caption": caption,
                })
                ja_count += 1

            # English question
            if en_count < n_per_language:
                template = rng.choice(EN_TEMPLATES)
                q = template.format(law=law_en, ref=f"Article {canonical}")
                questions.append({
                    "id": f"q{len(questions):04d}",
                    "language": "en",
                    "law": law_en,
                    "law_id": law_id,
                    "article": ref,
                    "question": q,
                    "gold_article": canonical,
                    "revision_id": revision_id,
                    "caption": caption,
                })
                en_count += 1

            if ja_count >= n_per_language and en_count >= n_per_language:
                break
        if ja_count >= n_per_language and en_count >= n_per_language:
            break

    return questions


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", default="data/registry.json")
    ap.add_argument("--output", default="data/questions.json")
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    registry = json.loads(Path(args.registry).read_text())
    questions = generate_questions(registry, n_per_language=args.n, seed=args.seed)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(questions, indent=2, ensure_ascii=False))

    ja = sum(1 for q in questions if q["language"] == "ja")
    en = sum(1 for q in questions if q["language"] == "en")
    print(f"Generated {len(questions)} questions ({ja} JA, {en} EN)")
    print(f"Saved to {output}")


if __name__ == "__main__":
    main()
