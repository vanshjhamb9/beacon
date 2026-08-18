"""COMAI B2B Partner Discovery Engine — Standalone Run Script.

Runs the complete partner discovery pipeline WITHOUT triggering
the existing app.services.__init__.py import chain.

COMAI B2B IS NOT AN AGENCY DIRECTORY.
WE ARE BUILDING A PARTNER ACQUISITION ENGINE.

Usage:
    python scripts/run_comai_b2b_partner_discovery.py
    python scripts/run_comai_b2b_partner_discovery.py --limit 20
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ── Direct module loader (avoids app.services.__init__.py chain) ──────

def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_models = _load_module(
    "app.models.partner",
    ROOT / "apps" / "api" / "app" / "models" / "partner.py",
)

_discovery = _load_module(
    "app.services.partner_discovery",
    ROOT / "apps" / "api" / "app" / "services" / "partner_discovery.py",
)

_scoring = _load_module(
    "app.services.partner_scoring",
    ROOT / "apps" / "api" / "app" / "services" / "partner_scoring.py",
)

_contactability = _load_module(
    "app.services.partner_contactability",
    ROOT / "apps" / "api" / "app" / "services" / "partner_contactability.py",
)

_export = _load_module(
    "app.services.partner_export",
    ROOT / "apps" / "api" / "app" / "services" / "partner_export.py",
)

PartnerDiscoveryEngine = _discovery.PartnerDiscoveryEngine
PartnerScoringEngine = _scoring.PartnerScoringEngine
ContactabilityVerificationEngine = _contactability.ContactabilityVerificationEngine
PartnerExportPipeline = _export.PartnerExportPipeline
PartnerRecord = _models.PartnerRecord


# ── Sample agency URLs — INDIA ONLY, 5-50 employees, NON-COMPETITOR ────
# COMAI B2B: Find distribution partners with business clients
# REJECT: WhatsApp/chatbot/white-label SaaS providers (competitors)

SAMPLE_AGENCIES = [
    # ──── MARKETING AGENCIES (D2C/Ecommerce Focus) ────
    {"url": "https://flashreach.io", "name": "FlashReach", "source": "web_research"},
    {"url": "https://www.havstrategy.com", "name": "HavStrategy", "source": "web_research"},
    {"url": "https://www.neuroidmedia.com", "name": "Neuroid", "source": "web_research"},
    {"url": "https://performify.in", "name": "Performify", "source": "web_research"},
    {"url": "https://iblixdigital.com", "name": "Iblix Digital", "source": "web_research"},
    {"url": "https://sqroot.in", "name": "Sqroot", "source": "web_research"},
    {"url": "https://www.dropscalemedia.com", "name": "Drop Scale Media", "source": "web_research"},
    {"url": "https://truimpact.io", "name": "TruImpact", "source": "web_research"},
    {"url": "https://aimnlaunch.com", "name": "Aim n Launch", "source": "web_research"},
    {"url": "https://sociolabs.in", "name": "Socio Labs", "source": "web_research"},
    {"url": "https://www.tangence.in", "name": "Tangence", "source": "web_research"},
    {"url": "https://d2cwolf.com", "name": "D2C Wolf", "source": "web_research"},
    
    # ──── SHOPIFY DEVELOPMENT AGENCIES ────
    {"url": "https://carryup.in", "name": "Carryup", "source": "web_research"},
    {"url": "https://farziengineer.com", "name": "FarziEngineer", "source": "web_research"},
    {"url": "https://www.cvinfotech.com", "name": "CV Infotech", "source": "web_research"},
    {"url": "https://cognitoitconsultancy.com", "name": "Cognito IT", "source": "web_research"},
    {"url": "https://ecommerce.bmconsulting.in", "name": "BM Consulting", "source": "web_research"},
    {"url": "https://aumentoinfoway.com", "name": "Aumento Infoway", "source": "web_research"},
    {"url": "https://marmeto.com", "name": "Marmeto", "source": "web_research"},
    
    # ──── CREATIVE/CONTENT AGENCIES ────
    {"url": "https://digidonut.com", "name": "Digidonut", "source": "web_research"},
    {"url": "https://itdgrowthlabs.com", "name": "ITD GrowthLabs", "source": "web_research"},
    {"url": "https://ixoric.com", "name": "Ixoric Technologies", "source": "web_research"},
    {"url": "https://www.thebrief.in", "name": "The Brief", "source": "web_research"},
    {"url": "https://www.wortham.in", "name": "Wortham", "source": "web_research"},
    {"url": "https://www.agenz.co.in", "name": "Agenz", "source": "web_research"},
    {"url": "https://www.createwithforty.com", "name": "Forty", "source": "web_research"},
    {"url": "https://akartha.com", "name": "Akartha", "source": "web_research"},
]


# ── Helpers ───────────────────────────────────────────────────────────

def _why_this_agency(p: PartnerRecord) -> str:
    parts = []
    if p.client_count_evidence:
        parts.append(f"Has {p.client_count_evidence}")
    if p.services:
        parts.append(f"Services: {', '.join(p.services[:3])}")
    if p.client_industries:
        parts.append(f"Industries: {', '.join(p.client_industries[:3])}")
    if p.partner_intent == "EXPLICIT":
        parts.append("Actively seeking partnership opportunities")
    return "; ".join(parts) if parts else "Relevant agency with potential client overlap"


def _pitch_angle(p: PartnerRecord) -> str:
    if p.partner_intent == "EXPLICIT":
        return "Partnership-focused: Agency is actively seeking tools for clients"
    if p.client_access_score >= 70:
        return "High client access: Strong client base for COMAI introduction"
    if p.comai_partner_fit >= 70:
        return "Strong COMAI fit: Agency's clients match COMAI ICP"
    return "General partnership: Agency could introduce COMAI to clients"


# ── Main engine ───────────────────────────────────────────────────────

async def run(limit: int = 50, output_dir: str = "exports/comai_b2b_partners"):
    print("=" * 70)
    print("  COMAI B2B PARTNER DISCOVERY ENGINE")
    print("=" * 70)
    print()
    print("  SEPARATE from:")
    print("  - COMAI direct ecommerce leads")
    print("  - INOWIX software-development leads")
    print("  - Cybersecurity leads")
    print()
    print("  COMAI B2B IS NOT AN AGENCY DIRECTORY.")
    print("  WE ARE BUILDING A PARTNER ACQUISITION ENGINE.")
    print()

    discovery_engine = PartnerDiscoveryEngine()
    scoring_engine = PartnerScoringEngine()
    contactability_engine = ContactabilityVerificationEngine()
    export_pipeline = PartnerExportPipeline(output_dir)

    agencies = SAMPLE_AGENCIES[:limit]
    print(f"  Processing {len(agencies)} agencies ...")
    print()

    partners: list[PartnerRecord] = []
    t0 = time.time()

    for i, ag in enumerate(agencies, 1):
        print(f"[{i}/{len(agencies)}] {ag['name']} ...", end=" ", flush=True)
        try:
            dr = await discovery_engine.discover_partner(
                url=ag["url"],
                company_name=ag["name"],
                source=ag["source"],
            )

            if dr.classification == "REJECT":
                reason = "; ".join(dr.rejection_reasons) if dr.rejection_reasons else "Rejected"
                print(f"REJECT — {reason}")
                if dr.partner_record:
                    dr.partner_record.rejection_reason = reason
                    dr.partner_record.final_verdict = "REJECT"
                    partners.append(dr.partner_record)
                continue

            partner = dr.partner_record
            if not partner:
                print("SKIP — no record")
                continue

            sr = scoring_engine.score_partner(partner)
            partner.client_access_score = sr.client_access_score
            partner.client_access_evidence = sr.client_access_evidence
            partner.comai_partner_fit = sr.comai_partner_fit
            partner.comai_fit_evidence = sr.comai_fit_evidence
            partner.partner_intent = sr.partner_intent
            partner.partner_intent_evidence = sr.partner_intent_evidence
            partner.partner_tier = sr.partner_tier
            partner.final_verdict = sr.final_verdict

            cr = contactability_engine.verify_contactability(partner)
            partner.email_status = cr.email_status
            partner.email_evidence = cr.email_evidence
            partner.linkedin_status = cr.linkedin_status
            partner.contactability = cr.contactability_level
            partner.contactability_evidence = cr.contactability_evidence

            partner.why_this_agency = _why_this_agency(partner)
            partner.recommended_pitch_angle = _pitch_angle(partner)

            partners.append(partner)

            tier = f"TIER_{partner.partner_tier}"
            intent = partner.partner_intent
            print(
                f"{tier} | "
                f"ClientAccess={partner.client_access_score} | "
                f"ComaiFit={partner.comai_partner_fit} | "
                f"Intent={intent} | "
                f"Contact={partner.contactability}"
            )

        except Exception as e:
            print(f"ERROR — {e}")

    # ── Export ─────────────────────────────────────────────────────
    print()
    print("Exporting results ...")
    ed = export_pipeline.export_results(partners)

    elapsed = time.time() - t0

    # ── Print summary ─────────────────────────────────────────────
    print()
    print("=" * 70)
    print("  DISCOVERY COMPLETE")
    print("=" * 70)
    print(f"  Total Discovered:            {ed.total_discovered}")
    print(f"  Verified Agencies:           {ed.verified_agencies}")
    print(f"  Explicit Partnership Intent: {ed.explicit_partnership_intent}")
    print(f"  High Potential:              {ed.high_potential}")
    print(f"  Hot Partners:                {ed.hot_partners}")
    print(f"  Contactable:                 {ed.contactable}")
    print()
    print(f"  Tier A (Hot):                {ed.tier_a}")
    print(f"  Tier B (High Potential):     {ed.tier_b}")
    print(f"  Tier C (Nurture):            {ed.tier_c}")
    print(f"  Rejected:                    {ed.rejected}")
    print()
    print(f"  Processing Time:             {elapsed:.1f}s")
    print()
    print(f"  Output:  {output_dir}/")
    print()
    print("  Files:")
    for f in [
        "comai_b2b_hot_partners.json",
        "comai_b2b_high_potential.json",
        "comai_b2b_nurture.json",
        "comai_b2b_rejected.json",
        "comai_b2b_evidence_audit.json",
        "comai_b2b_contactability_audit.json",
        "COMAI_B2B_FINAL_REPORT.md",
    ]:
        print(f"    - {f}")

    # ── Print HOT + HIGH POTENTIAL partners inline ────────────────
    print()
    print("=" * 70)
    print("  HIGH-INTENT PARTNER LEADS")
    print("=" * 70)

    hot = [p for p in partners if p.partner_tier == "A" and p.final_verdict != "REJECT"]
    high = [p for p in partners if p.partner_tier == "B" and p.final_verdict != "REJECT"]

    if hot:
        print()
        print("  -- TIER A -- HOT PARTNERS ---------------------------------")
        for p in hot:
            print()
            print(f"  {p.agency_name}")
            print(f"    URL:              {p.agency_url}")
            print(f"    Country:          {p.country}")
            print(f"    Type:             {p.agency_type}")
            print(f"    Services:         {', '.join(p.services[:4])}")
            print(f"    Clients:          {p.client_count_evidence}")
            print(f"    Industries:       {', '.join(p.client_industries[:3])}")
            print(f"    Client Access:    {p.client_access_score}/100")
            print(f"    COMAI Fit:        {p.comai_partner_fit}/100")
            print(f"    Intent:           {p.partner_intent}")
            print(f"    Decision Maker:   {p.founder_name} ({p.founder_role})")
            print(f"    Email:            {p.email} [{p.email_status}]")
            print(f"    LinkedIn:         {p.linkedin_url}")
            print(f"    Contactability:   {p.contactability}")
            print(f"    Why:              {p.why_this_agency}")
            print(f"    Pitch:            {p.recommended_pitch_angle}")

    if high:
        print()
        print("  -- TIER B -- HIGH POTENTIAL PARTNERS ----------------------")
        for p in high:
            print()
            print(f"  {p.agency_name}")
            print(f"    URL:              {p.agency_url}")
            print(f"    Country:          {p.country}")
            print(f"    Type:             {p.agency_type}")
            print(f"    Services:         {', '.join(p.services[:4])}")
            print(f"    Clients:          {p.client_count_evidence}")
            print(f"    Industries:       {', '.join(p.client_industries[:3])}")
            print(f"    Client Access:    {p.client_access_score}/100")
            print(f"    COMAI Fit:        {p.comai_partner_fit}/100")
            print(f"    Intent:           {p.partner_intent}")
            print(f"    Decision Maker:   {p.founder_name} ({p.founder_role})")
            print(f"    Email:            {p.email} [{p.email_status}]")
            print(f"    LinkedIn:         {p.linkedin_url}")
            print(f"    Contactability:   {p.contactability}")
            print(f"    Why:              {p.why_this_agency}")
            print(f"    Pitch:            {p.recommended_pitch_angle}")

    if not hot and not high:
        print()
        print("  No Tier A or Tier B partners found in this run.")
        print("  Increase --limit or add more agency URLs to the seed list.")

    print()
    print("=" * 70)
    print("  FINAL PRINCIPLE")
    print("  QUALITY > QUANTITY")
    print("  DO NOT SEND OUTREACH AUTOMATICALLY.")
    print("  Only qualified Tier A and selected Tier B enter outreach queue.")
    print("  STOP AFTER GENERATING THE REPORT.")
    print("=" * 70)

    return ed


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="COMAI B2B Partner Discovery Engine")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--output", type=str, default="exports/comai_b2b_partners")
    args = parser.parse_args()
    asyncio.run(run(limit=args.limit, output_dir=args.output))
