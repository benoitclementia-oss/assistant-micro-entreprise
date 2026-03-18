"""Tests pour scripts/ingest.py — utilitaire _strip_html."""

from scripts.ingest import _strip_html


class TestStripHtml:
    def test_simple_tags(self):
        assert _strip_html("<p>Hello</p>") == "Hello"

    def test_nested_tags(self):
        assert _strip_html("<div><p>Hello</p></div>") == "Hello"

    def test_tags_with_attributes(self):
        assert _strip_html('<a href="http://example.com">link</a>') == "link"

    def test_no_tags(self):
        assert _strip_html("Hello world") == "Hello world"

    def test_empty(self):
        assert _strip_html("") == ""

    def test_only_tags(self):
        assert _strip_html("<br><hr>") == ""

    def test_html_entities_not_decoded(self):
        # _strip_html retire les balises mais ne décode pas les entités
        result = _strip_html("<p>&amp; &lt; &gt;</p>")
        assert "&amp;" in result
        assert "&lt;" in result
