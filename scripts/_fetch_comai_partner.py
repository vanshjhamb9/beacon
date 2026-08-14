"""Fetch ComAI public pages to study agency partnership messaging."""
from __future__ import annotations

import re
from pathlib import Path

import httpx

OUT = Path(__file__).resolve().parents[1] / "exports" / "comai_partner_research"
OUT.mkdir(parents=True, exist_ok=True)

urls = [
    "https://getcomai.com/",
    "https://www.getcomai.com/",
    "https://getcomai.com/partners",
    "https://getcomai.com/partner",
    "https://getcomai.com/agencies",
    "https://getcomai.com/agency",
    "https://getcomai.com/for-agencies",
    "https://getcomai.com/white-label",
    "https://getcomai.com/pricing",
    "https://www.inowix.in/",
    "https://inowix.in/comai",
    "https://www.inowix.in/comai",
]

with httpx.Client(timeout=20, follow_redirects=True) as client:
    for url in urls:
        try:
            r = client.get(url)
            safe = re.sub(r"[^a-zA-Z0-9]+", "_", url.strip("/"))[:80]
            (OUT / f"{safe}.html").write_bytes(r.content)
            text = re.sub(r"<script[\s\S]*?</script>", " ", r.text, flags=re.I)
            text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            (OUT / f"{safe}.txt").write_text(text[:8000], encoding="utf-8")
            links = sorted(set(re.findall(r'href=["\']([^"\']+)["\']', r.text, flags=re.I)))
            print(f"OK {r.status_code} {url} -> {r.url} len={len(r.text)} links={len(links)}")
            for L in links[:40]:
                print("  ", L)
            print("---")
            print(text[:1200])
            print("====")
        except Exception as e:
            print(f"ERR {url}: {e}")
