"""Quick public website blurbs for agency personalization."""
from __future__ import annotations

import json
import re
from pathlib import Path

import httpx

leads = json.loads(
    Path(r"c:\Inowix intelligence system\New folder\exports\comai_agency_outreach_leads.json").read_text(
        encoding="utf-8"
    )
)

out = []
with httpx.Client(timeout=15, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"}) as client:
    for lead in leads:
        website = lead.get("website") or (f"https://{lead['domain']}" if lead.get("domain") else None)
        blurb = ""
        title = ""
        services = []
        ok = False
        err = ""
        if website:
            try:
                r = client.get(website)
                ok = r.status_code == 200
                html = r.text
                mt = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
                title = re.sub(r"\s+", " ", mt.group(1)).strip() if mt else ""
                md = re.search(
                    r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
                    html,
                    re.I,
                )
                if not md:
                    md = re.search(
                        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']description["\']',
                        html,
                        re.I,
                    )
                blurb = (md.group(1).strip() if md else "")[:400]
                text = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
                text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
                text = re.sub(r"<[^>]+>", " ", text)
                text = re.sub(r"\s+", " ", text)
                for kw in [
                    "performance marketing",
                    "digital marketing",
                    "social media",
                    "SEO",
                    "PPC",
                    "branding",
                    "WhatsApp",
                    "ecommerce",
                    "e-commerce",
                    "D2C",
                    "lead generation",
                    "content",
                    "influencer",
                    "Meta ads",
                    "Google ads",
                    "Shopify",
                ]:
                    if re.search(re.escape(kw), text, re.I):
                        services.append(kw)
                # suspicious: title/company mismatch signals
            except Exception as e:
                err = str(e)
        item = {
            **{k: lead[k] for k in ["founder_name", "company_name", "location", "job_title", "domain", "website", "emails"]},
            "page_title": title,
            "meta_description": blurb,
            "service_keywords": services[:8],
            "fetch_ok": ok,
            "fetch_error": err,
        }
        out.append(item)
        print(lead["company_name"], "|", title[:60] if title else "-", "|", ",".join(services[:5]) or "-", "|", lead["emails"][0])

Path(r"c:\Inowix intelligence system\New folder\exports\comai_agency_lead_context.json").write_text(
    json.dumps(out, indent=2), encoding="utf-8"
)
print("wrote", len(out))
