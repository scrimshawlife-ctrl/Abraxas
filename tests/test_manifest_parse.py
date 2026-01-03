from __future__ import annotations

from abraxas.acquisition.manifest_parse import parse_index_html, parse_sitemap_xml


def test_parse_sitemap_xml_deterministic() -> None:
    raw = """
    <urlset>
      <url><loc>https://example.com/z</loc></url>
      <url><loc>https://example.com/a#fragment</loc></url>
    </urlset>
    """
    urls = parse_sitemap_xml(raw)
    assert urls == ["https://example.com/a", "https://example.com/z"]


def test_parse_index_html_deterministic() -> None:
    raw = """
    <html>
      <body>
        <a href="https://example.com/b">b</a>
        <a href="https://example.com/a#section">a</a>
      </body>
    </html>
    """
    urls = parse_index_html(raw)
    assert urls == ["https://example.com/a", "https://example.com/b"]
