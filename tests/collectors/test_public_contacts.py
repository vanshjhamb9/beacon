"""OFC public contact extraction — evidence only, never invent."""

from collectors.extraction.public_contacts import extract_public_contacts


def test_extracts_same_domain_email_phone_linkedin_and_founder():
    html = """
    <html><body>
      <a href="mailto:hello@screenpi.pe">Email us</a>
      <p>Call +1 (415) 555-0199</p>
      <a href="https://www.linkedin.com/in/johndoe">John</a>
      <a href="https://www.linkedin.com/company/screenpipe">Company</a>
      <p>Jane Doe, Founder</p>
      <p>CEO: Alex Smith</p>
    </body></html>
    """
    out = extract_public_contacts(html, page_url="https://screenpi.pe/about", domain="screenpi.pe")
    assert "hello@screenpi.pe" in out["emails"]
    assert out["phones"]
    assert any("/in/" in u for u in out["linkedin"])
    assert any(p["name"] == "Jane Doe" and "Founder" in p["role"] for p in out["decision_makers"])


def test_skips_platform_and_example_emails():
    html = '<a href="mailto:test@example.com">x</a><a href="mailto:x@sentry.io">y</a>'
    out = extract_public_contacts(html, page_url="https://acme.io/contact", domain="acme.io")
    assert out["emails"] == []


def test_rejects_off_domain_and_garbage_phones():
    html = """
    <a href="mailto:other@anulum.li">x</a>
    <p>0009-0009-3560-0851</p>
    <p>+1 415 555 0199</p>
    <a href="mailto:hello@acme.io">us</a>
    """
    out = extract_public_contacts(html, page_url="https://acme.io/contact", domain="acme.io")
    assert out["emails"] == ["hello@acme.io"]
    assert any("415" in p for p in out["phones"])
    assert not any("0009" in p for p in out["phones"])
