"""Tests for the MCP server article post-processing."""

import googlenews


def test_attach_extracted_text_aligns_and_preserves_google_link():
    """Texts stay aligned with articles and the original Google link is kept.

    Regression test: when a URL fails to decode (``None`` in the middle of
    ``decoded_urls``) the old code desynced its text index, mis-assigning text
    and eventually raising IndexError; and it overwrote ``link`` before saving
    ``google_link``, losing the original.
    """
    articles = [
        {"link": "google://a"},
        {"link": "google://b"},  # this one fails to decode
        {"link": "google://c"},
    ]
    decoded_urls = ["real://a", None, "real://c"]
    extracted_texts = ["text-a", None, "text-c"]

    result = googlenews._attach_extracted_text(articles, decoded_urls, extracted_texts)

    # Decoded entries: original link preserved in google_link, link replaced,
    # and the correct (aligned) text attached.
    assert result[0]["google_link"] == "google://a"
    assert result[0]["link"] == "real://a"
    assert result[0]["text"] == "text-a"

    assert result[2]["google_link"] == "google://c"
    assert result[2]["link"] == "real://c"
    assert result[2]["text"] == "text-c"

    # Failed decode: left untouched, no misaligned text, no IndexError.
    assert result[1] == {"link": "google://b"}


def test_attach_extracted_text_handles_empty_text():
    """A decoded article with no extracted text gets an empty string."""
    articles = [{"link": "google://a"}]
    result = googlenews._attach_extracted_text(articles, ["real://a"], [None])
    assert result[0]["link"] == "real://a"
    assert result[0]["text"] == ""
