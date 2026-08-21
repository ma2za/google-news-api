import pytest

from google_news_api.exceptions import ValidationError
from google_news_api.query import NewsQuery


def test_news_query_text_only():
    query = NewsQuery("python programming").build()
    assert query == "python programming"
    assert str(NewsQuery("python programming")) == "python programming"


def test_news_query_exact_phrase():
    query = NewsQuery(exact_phrase="artificial intelligence").build()
    assert query == '"artificial intelligence"'


def test_news_query_any_words():
    query = NewsQuery(text="python", any_words=["rust", "go language"]).build()
    assert query == 'python (rust OR "go language")'


def test_news_query_exclude_words():
    query = NewsQuery(text="apple", exclude_words=["fruit", "pie recipe"]).build()
    assert query == 'apple -fruit -"pie recipe"'


def test_news_query_in_title():
    query = NewsQuery(in_title="release 0.0.16").build()
    assert query == 'intitle:"release 0.0.16"'


def test_news_query_combined():
    query = NewsQuery(
        text="machine learning",
        exact_phrase="neural networks",
        any_words=["AI", "deep learning"],
        exclude_words=["robot", "sci-fi movie"],
        in_title="breakthrough",
    ).build()

    expected = (
        'machine learning "neural networks" (AI OR "deep learning") '
        '-robot -"sci-fi movie" intitle:"breakthrough"'
    )
    assert query == expected


def test_news_query_escaping():
    query = NewsQuery(
        exact_phrase='quote " test \\ backslash',
        exclude_words=['another " quote'],
    ).build()

    assert query == '"quote \\" test \\\\ backslash" -"another \\" quote"'


def test_news_query_strips_and_cleans():
    query = NewsQuery(
        text="  python  ",
        exact_phrase="  ",
        any_words=["", "  ", "rust", "rust", "go"],
        exclude_words=[None, "java", "java  ", " c "],
    ).build()

    assert query == 'python (rust OR go) -java -c'


def test_news_query_requires_positive_term():
    with pytest.raises(ValidationError) as exc:
        NewsQuery()
    assert "At least one positive term" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        NewsQuery(exclude_words=["bad"])
    assert "At least one positive term" in str(exc.value)


def test_news_query_with_none_values():
    query = NewsQuery(
        text=None,
        exact_phrase=None,
        any_words=None,
        exclude_words=None,
        in_title="Valid",
    ).build()
    assert query == 'intitle:"Valid"'
