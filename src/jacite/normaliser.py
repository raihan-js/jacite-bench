"""Japanese article reference normaliser.

Maps Japanese and English article references to one canonical ID:
- Kanji numerals: 第五百四十一条 → 541
- の-branch numbers: 第四百十五条の二 → 415-2
- English forms: Article 541 → 541
- Mixed forms: 第541条 → 541
"""

from __future__ import annotations

import re

KANJI_DIGITS = {
    '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
    '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
    '十': 10, '百': 100, '千': 1000,
}

KANJI_NUMERAL_RE = re.compile(r'[零一二三四五六七八九十百千]+')


def kanji_to_int(s: str) -> int | None:
    """Convert a kanji numeral string to an integer.

    Handles 十/百/千 place values: 五百四十一 → 541.
    """
    if not s:
        return None
    if s.isdigit():
        return int(s)

    total = 0
    current = 0
    for ch in s:
        if ch not in KANJI_DIGITS:
            return None
        val = KANJI_DIGITS[ch]
        if val >= 10:
            if current == 0:
                current = 1
            total += current * val
            current = 0
        else:
            current = current * 10 + val if current > 0 else val
    return total + current


def normalise_article_ref(ref: str) -> str | None:
    """Normalise an article reference to a canonical ID.

    Returns a string like "541" or "415-2" (for の-branch articles).
    Returns None if the reference cannot be parsed.

    Examples:
        第五百四十一条 → "541"
        第541条 → "541"
        Article 541 → "541"
        第四百十五条の二 → "415-2"
        第415条の2 → "415-2"
    """
    if not ref or not isinstance(ref, str):
        return None

    ref = ref.strip()

    # English form: "Article 541" or "Article 541-2"
    m = re.match(r'Article\s+(\d+)(?:-(\d+))?', ref, re.IGNORECASE)
    if m:
        num = m.group(1)
        branch = m.group(2)
        return f"{num}-{branch}" if branch else num

    # Japanese form with の-branch: 第四百十五条の二 or 第415条の2
    m = re.match(r'第([零一二三四五六七八九十百千\d]+)条の([零一二三四五六七八九十百千\d]+)', ref)
    if m:
        num = kanji_to_int(m.group(1))
        branch = kanji_to_int(m.group(2))
        if num is not None and branch is not None:
            return f"{num}-{branch}"
        return None

    # Japanese form: 第五百四十一条 or 第541条
    m = re.match(r'第([零一二三四五六七八九十百千\d]+)条', ref)
    if m:
        num = kanji_to_int(m.group(1))
        if num is not None:
            return str(num)
        return None

    # Bare kanji numeral (e.g., from a caption): 第五百四十一条
    m = re.match(r'^([零一二三四五六七八九十百千]+)条$', ref)
    if m:
        num = kanji_to_int(m.group(1))
        if num is not None:
            return str(num)
        return None

    # Bare number: "541" or "Article 541"
    m = re.match(r'^(\d+)$', ref)
    if m:
        return m.group(1)

    return None


_NUM = r'[零一二三四五六七八九十百千\d]+'
# One left-to-right pass. The first version ran three patterns one after the other over the whole text, which (a) returned citations grouped by pattern instead of in
# text order and (b) reported the prefix 第二条 of every branch citation 第二条の二 as a second, phantom citation ("2"). Fixed 2026-10-06; see README, "Correction".
_CITATION_RE = re.compile(rf'第({_NUM})条((?:の{_NUM})*)|Article\s+(\d+(?:-\d+)*)', re.IGNORECASE)


def extract_cited_articles(text: str) -> list[str]:
    """Extract every article citation (one entry per mention, in text order) as a canonical id: 第二条の二 -> "2-2", 第百二十五条の二の三 -> "125-2-3", Article 541 -> "541"."""
    if not text:
        return []
    found = []
    for m in _CITATION_RE.finditer(text):
        if m.group(1):
            parts = [kanji_to_int(m.group(1))] + [kanji_to_int(b) for b in re.findall(rf'の({_NUM})', m.group(2))]
            if None in parts:
                continue
            found.append("-".join(str(p) for p in parts))
        else:
            found.append(m.group(3))
    return found
