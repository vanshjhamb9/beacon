from collectors.extraction.quality import enrichment_metadata, strip_html


def test_strip_html_and_enrichment_metadata() -> None:
    content = "<p>Acme Labs is hiring for automation roles.</p>"
    cleaned = strip_html(content)
    assert "<" not in cleaned
    metadata = enrichment_metadata(
        title="Acme Labs raises seed",
        content=cleaned,
        url="https://news.example.com/acme",
        extra={"feed_url": "https://news.example.com/feed"},
    )
    assert metadata["feed_url"] == "https://news.example.com/feed"
    assert metadata["domain"] == "news.example.com"
    assert metadata["extraction_quality"] > 0
    assert "hiring" in metadata["signal_tags"] or "fundrais" in " ".join(metadata["signal_tags"])
