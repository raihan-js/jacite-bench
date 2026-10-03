import pytest
from jacite.normaliser import kanji_to_int, normalise_article_ref, extract_cited_articles


class TestKanjiToInt:
    def test_single_digits(self):
        assert kanji_to_int('一') == 1
        assert kanji_to_int('二') == 2
        assert kanji_to_int('九') == 9

    def test_tens(self):
        assert kanji_to_int('十') == 10
        assert kanji_to_int('十一') == 11
        assert kanji_to_int('二十') == 20
        assert kanji_to_int('二十三') == 23

    def test_hundreds(self):
        assert kanji_to_int('百') == 100
        assert kanji_to_int('二百') == 200
        assert kanji_to_int('三百四十一') == 341

    def test_thousands(self):
        assert kanji_to_int('千') == 1000
        assert kanji_to_int('五千') == 5000

    def test_complex(self):
        assert kanji_to_int('五百四十一') == 541
        assert kanji_to_int('四百十五') == 415
        assert kanji_to_int('千二百三十四') == 1234

    def test_arabic(self):
        assert kanji_to_int('541') == 541
        assert kanji_to_int('0') == 0

    def test_empty(self):
        assert kanji_to_int('') is None

    def test_invalid(self):
        assert kanji_to_int('abc') is None


class TestNormaliseArticleRef:
    def test_kanji_with_条(self):
        assert normalise_article_ref('第五百四十一条') == '541'
        assert normalise_article_ref('第四百十五条') == '415'
        assert normalise_article_ref('第一条') == '1'

    def test_arabic_with_条(self):
        assert normalise_article_ref('第541条') == '541'
        assert normalise_article_ref('第1条') == '1'

    def test_english(self):
        assert normalise_article_ref('Article 541') == '541'
        assert normalise_article_ref('article 541') == '541'
        assert normalise_article_ref('Article 1') == '1'

    def test_english_with_branch(self):
        assert normalise_article_ref('Article 541-2') == '541-2'

    def test_kanji_branch(self):
        assert normalise_article_ref('第四百十五条の二') == '415-2'
        assert normalise_article_ref('第415条の2') == '415-2'
        assert normalise_article_ref('第五条の三') == '5-3'

    def test_bare_number(self):
        assert normalise_article_ref('541') == '541'

    def test_bare_kanji(self):
        assert normalise_article_ref('第五百四十一条') == '541'

    def test_empty(self):
        assert normalise_article_ref('') is None
        assert normalise_article_ref(None) is None

    def test_invalid(self):
        assert normalise_article_ref('hello') is None
        assert normalise_article_ref('条') is None

    def test_whitespace(self):
        assert normalise_article_ref('  第541条  ') == '541'
        assert normalise_article_ref('  Article 541  ') == '541'


class TestExtractCitedArticles:
    def test_single_citation(self):
        text = 'According to 第五百四十一条, ...'
        assert extract_cited_articles(text) == ['541']

    def test_multiple_citations(self):
        text = 'See 第541条 and 第415条の二'
        result = extract_cited_articles(text)
        assert '541' in result
        assert '415-2' in result

    def test_english_citation(self):
        text = 'As stated in Article 541, ...'
        assert extract_cited_articles(text) == ['541']

    def test_mixed_citations(self):
        text = '第541条 and Article 415 both apply'
        result = extract_cited_articles(text)
        assert '541' in result
        assert '415' in result

    def test_no_citations(self):
        text = 'No articles cited here'
        assert extract_cited_articles(text) == []

    def test_empty_text(self):
        assert extract_cited_articles('') == []
        assert extract_cited_articles(None) == []

    def test_duplicate_citations(self):
        text = '第541条 and 第541条'
        result = extract_cited_articles(text)
        assert result.count('541') == 2
