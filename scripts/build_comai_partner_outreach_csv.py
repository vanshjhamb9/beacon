#!/usr/bin/env python3
"""Build a Partner Outreach CSV from existing comai_b2b export JSON/CSV packs."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "exports" / "comai_partner_outreach" / "from_comai_b2b_exports.csv"

SOURCE_CANDIDATES = [
    ROOT / "exports" / "comai_b2b_fresh_150" / "comai_b2b_fresh_150_latest.json",
    ROOT / "exports" / "comai_b2b_fresh_100" / "comai_b2b_fresh_100_latest.json",
    ROOT / "exports" / "comai_b2b_mega_high_potential" / "comai_b2b_mega_high_potential_latest.json",
    ROOT / "exports" / "comai_b2b_50_agencies" / "comai_b2b_final_50_plus.json",
    ROOT / "exports" / "comai_b2b_partners" / "comai_b2b_high_potential.json",
]


def _rows_from_obj(obj) -> list[dict]:
    if isinstance(obj, list):
        return [x for x in obj if isinstance(x, dict)]
    if isinstance(obj, dict):
        for key in ("leads", "partners", "items", "results", "agencies"):
            if isinstance(obj.get(key), list):
                return [x for x in obj[key] if isinstance(x, dict)]
        return [obj]
    return []


def _map_row(item: dict) -> dict | None:
    email = (
        item.get("email")
        or item.get("to_email")
        or item.get("founder_email")
        or ""
    ).strip().lower()
    if not email or "@" not in email:
        return None
    founder = item.get("founder_name") or item.get("contact_name") or ""
    first = (item.get("first_name") or "").strip() or (founder.split()[0] if founder else "")
    last = (item.get("last_name") or "").strip()
    if not last and founder and len(founder.split()) > 1:
        last = " ".join(founder.split()[1:])
    agency = (
        item.get("agency_name")
        or item.get("company_name")
        or item.get("company")
        or item.get("name")
        or ""
    )
    return {
        "first_name": first,
        "last_name": last,
        "agency_name": agency,
        "email": email,
        "agency_type": item.get("agency_type") or item.get("type") or "marketing",
        "website": item.get("website") or item.get("agency_url") or item.get("url") or "",
        "city": item.get("city") or "",
        "phone": item.get("phone") or "",
        "services": ",".join(item.get("services") or []) if isinstance(item.get("services"), list) else (item.get("services") or ""),
        "notes": item.get("why_this_agency") or item.get("recommended_pitch_angle") or item.get("why") or item.get("angle") or "",
        "client_examples": ",".join(item.get("client_examples") or []) if isinstance(item.get("client_examples"), list) else (item.get("client_examples") or ""),
    }


def main() -> int:
    seen: set[str] = set()
    rows: list[dict] = []
    for path in SOURCE_CANDIDATES:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            print(f"skip {path.name}: {exc}", file=sys.stderr)
            continue
        for item in _rows_from_obj(data):
            mapped = _map_row(item)
            if not mapped:
                continue
            if mapped["email"] in seen:
                continue
            seen.add(mapped["email"])
            rows.append(mapped)
        print(f"loaded {path.name}: cumulative {len(rows)}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "first_name",
        "last_name",
        "agency_name",
        "email",
        "agency_type",
        "website",
        "city",
        "phone",
        "services",
        "notes",
        "client_examples",
    ]
    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
