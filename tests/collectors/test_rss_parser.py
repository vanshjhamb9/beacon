from collectors.rss_parser import parse_rss_events


def test_parse_rss_events_returns_normalized_events() -> None:
    xml = """
    <rss version="2.0">
      <channel>
        <item>
          <title>Nike opens UK office</title>
          <link>https://example.com/nike-uk</link>
          <description>Nike expanded its UK operations.</description>
          <pubDate>Fri, 10 Jul 2026 09:00:00 GMT</pubDate>
        </item>
      </channel>
    </rss>
    """

    events = parse_rss_events(xml, source="rss", feed_url="https://example.com/feed", max_items=10)

    assert len(events) == 1
    assert events[0].source == "rss"
    assert events[0].url == "https://example.com/nike-uk"
    assert events[0].title == "Nike opens UK office"
    assert events[0].metadata["feed_url"] == "https://example.com/feed"
    assert "extraction_quality" in events[0].metadata
    assert "company_hints" in events[0].metadata
