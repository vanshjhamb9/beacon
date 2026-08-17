"""Export Engine — Generates all output files for BEACON cybersecurity discoveries."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cybersecurity_engine.models import CybersecurityOpportunity, OpportunityPriority


class ExportEngine:
    """Exports discovered opportunities to various formats."""

    def __init__(self, output_dir: str = ".") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_all(
        self,
        opportunities: list[CybersecurityOpportunity],
    ) -> dict[str, str]:
        """Export all opportunity data to required file formats.

        Returns dict of filename -> filepath.
        """
        files = {}

        # Separate by classification
        sales_ready = [o for o in opportunities if o.final_verdict == "SALES_READY"]
        outreach_queue = [o for o in opportunities if o.final_verdict in {"SALES_READY", "MARKETING_READY"}]
        rejected = [o for o in opportunities if o.final_verdict == "NOT_READY"]

        # 1. cybersecurity_sales_ready.json
        files["cybersecurity_sales_ready.json"] = self._export_json(
            [o.to_dict() for o in sales_ready],
            "cybersecurity_sales_ready.json",
        )

        # 2. cybersecurity_sales_ready.xlsx
        files["cybersecurity_sales_ready.xlsx"] = self._export_xlsx(
            sales_ready,
            "cybersecurity_sales_ready.xlsx",
        )

        # 3. cybersecurity_outreach_queue.json
        files["cybersecurity_outreach_queue.json"] = self._export_json(
            [o.to_dict() for o in outreach_queue],
            "cybersecurity_outreach_queue.json",
        )

        # 4. cybersecurity_report.txt
        files["cybersecurity_report.txt"] = self._export_report(
            opportunities,
            "cybersecurity_report.txt",
        )

        # 5. cybersecurity_rejected.json
        files["cybersecurity_rejected.json"] = self._export_json(
            [o.to_dict() for o in rejected],
            "cybersecurity_rejected.json",
        )

        # 6. cybersecurity_evidence_audit.json
        files["cybersecurity_evidence_audit.json"] = self._export_evidence_audit(
            opportunities,
            "cybersecurity_evidence_audit.json",
        )

        return files

    def _export_json(
        self,
        data: list[dict[str, Any]],
        filename: str,
    ) -> str:
        """Export data to JSON file."""
        filepath = self.output_dir / filename
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)
        return str(filepath)

    def _export_xlsx(
        self,
        opportunities: list[CybersecurityOpportunity],
        filename: str,
    ) -> str:
        """Export opportunities to Excel format."""
        filepath = self.output_dir / filename

        # Create a simple CSV-like format if openpyxl not available
        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Sales Ready Opportunities"

            # Headers
            headers = [
                "Opportunity ID",
                "Company Name",
                "Company URL",
                "Country",
                "Industry",
                "Company Size",
                "Priority",
                "Final Verdict",
                "Buying Event",
                "Services Needed",
                "Service Match",
                "Why Now",
                "Decision Maker",
                "Decision Maker Role",
                "Email",
                "Email Status",
                "LinkedIn",
                "LinkedIn Status",
                "Phone",
                "Phone Status",
                "Contactability",
                "Source",
                "Source URL",
                "Evidence Count",
                "Evidence Confidence",
                "Outreach Angle",
                "Personalized Message",
            ]
            ws.append(headers)

            # Data rows
            for opp in opportunities:
                ws.append([
                    opp.opportunity_id,
                    opp.company.name,
                    opp.company.url,
                    opp.company.country,
                    opp.company.industry,
                    opp.company.company_size.value,
                    opp.priority.value,
                    opp.final_verdict,
                    opp.buying_event.description[:100],
                    "; ".join(opp.buying_event.services_needed),
                    opp.buying_event.service_match,
                    opp.buying_event.why_now,
                    opp.contact.name,
                    opp.contact.role,
                    opp.contact.email,
                    opp.contact.email_status,
                    opp.contact.linkedin_url,
                    opp.contact.linkedin_status,
                    opp.contact.phone,
                    opp.contact.phone_status,
                    opp.contactability,
                    opp.source_name,
                    opp.source_url,
                    opp.evidence_count,
                    opp.evidence_confidence.value,
                    opp.outreach_preparation.outreach_angle,
                    opp.outreach_preparation.personalized_message[:500],
                ])

            wb.save(filepath)
        except ImportError:
            # Fallback: create CSV
            import csv
            with open(filepath.with_suffix(".csv"), "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Company", "URL", "Country", "Priority", "Verdict", "Contact"])
                for opp in opportunities:
                    writer.writerow([
                        opp.company.name,
                        opp.company.url,
                        opp.company.country,
                        opp.priority.value,
                        opp.final_verdict,
                        opp.contact.email or opp.contact.linkedin_url or "No contact",
                    ])
            return str(filepath.with_suffix(".csv"))

        return str(filepath)

    def _export_report(
        self,
        opportunities: list[CybersecurityOpportunity],
        filename: str,
    ) -> str:
        """Export human-readable report."""
        filepath = self.output_dir / filename

        sales_ready = [o for o in opportunities if o.final_verdict == "SALES_READY"]
        marketing_ready = [o for o in opportunities if o.final_verdict == "MARKETING_READY"]
        not_ready = [o for o in opportunities if o.final_verdict == "NOT_READY"]

        p0 = [o for o in opportunities if o.priority == OpportunityPriority.P0]
        p1 = [o for o in opportunities if o.priority == OpportunityPriority.P1]
        p2 = [o for o in opportunities if o.priority == OpportunityPriority.P2]

        report = []
        report.append("=" * 70)
        report.append("BEACON — CYBERSECURITY BUYER DISCOVERY ENGINE")
        report.append(f"Report Generated: {datetime.now(timezone.utc).isoformat()}")
        report.append("=" * 70)
        report.append("")

        # Summary
        report.append("SUMMARY")
        report.append("-" * 40)
        report.append(f"Total Opportunities Analyzed: {len(opportunities)}")
        report.append(f"SALES_READY: {len(sales_ready)}")
        report.append(f"MARKETING_READY: {len(marketing_ready)}")
        report.append(f"NOT_READY: {len(not_ready)}")
        report.append("")

        # Priority Breakdown
        report.append("PRIORITY BREAKDOWN")
        report.append("-" * 40)
        report.append(f"P0 (Active Buying Event): {len(p0)}")
        report.append(f"P1 (Verified Security Pain): {len(p1)}")
        report.append(f"P2 (High-Potential Outbound): {len(p2)}")
        report.append("")

        # SALES READY Details
        if sales_ready:
            report.append("=" * 70)
            report.append("SALES READY OPPORTUNITIES")
            report.append("=" * 70)
            for i, opp in enumerate(sales_ready, 1):
                report.append("")
                report.append(f"--- Opportunity {i} ---")
                report.append(f"Company: {opp.company.name}")
                report.append(f"URL: {opp.company.url}")
                report.append(f"Country: {opp.company.country}")
                report.append(f"Industry: {opp.company.industry}")
                report.append(f"Priority: {opp.priority.value}")
                report.append(f"Buying Event: {opp.buying_event.description}")
                report.append(f"Services Needed: {', '.join(opp.buying_event.services_needed)}")
                report.append(f"Why Now: {opp.buying_event.why_now}")
                report.append(f"Decision Maker: {opp.contact.name} ({opp.contact.role})")
                report.append(f"Email: {opp.contact.email} [{opp.contact.email_status}]")
                report.append(f"LinkedIn: {opp.contact.linkedin_url} [{opp.contact.linkedin_status}]")
                report.append(f"Contactability: {opp.contactability}")
                report.append(f"Evidence Count: {opp.evidence_count}")
                report.append(f"Evidence Confidence: {opp.evidence_confidence.value}")
                report.append(f"Source: {opp.source_name} — {opp.source_url}")
                report.append(f"Outreach Angle: {opp.outreach_preparation.outreach_angle}")
                if opp.outreach_preparation.personalized_message:
                    report.append(f"Message Preview: {opp.outreach_preparation.personalized_message[:300]}...")
                report.append("")

        # MARKETING READY Summary
        if marketing_ready:
            report.append("")
            report.append("=" * 70)
            report.append("MARKETING READY (Nurture)")
            report.append("=" * 70)
            for opp in marketing_ready:
                report.append(f"  - {opp.company.name} [{opp.priority.value}] — {opp.buying_event.description[:80]}")

        # Rejected Summary
        if not_ready:
            report.append("")
            report.append("=" * 70)
            report.append("REJECTED")
            report.append("=" * 70)
            for opp in not_ready:
                report.append(f"  - {opp.company.name} — {opp.final_verdict}")

        # Final CTO Test
        report.append("")
        report.append("=" * 70)
        report.append("FINAL CTO TEST")
        report.append("=" * 70)
        report.append("Would a cybersecurity sales representative reasonably contact")
        report.append("this company TODAY based solely on the evidence Beacon collected?")
        report.append("")
        report.append(f"SALES_READY count: {len(sales_ready)}")
        report.append("These opportunities passed all gates.")
        report.append("")

        with open(filepath, "w") as f:
            f.write("\n".join(report))

        return str(filepath)

    def _export_evidence_audit(
        self,
        opportunities: list[CybersecurityOpportunity],
        filename: str,
    ) -> str:
        """Export evidence audit trail."""
        filepath = self.output_dir / filename

        audit = []
        for opp in opportunities:
            opp_audit = {
                "opportunity_id": opp.opportunity_id,
                "company_name": opp.company.name,
                "final_verdict": opp.final_verdict,
                "priority": opp.priority.value,
                "evidence_chain": [
                    {
                        "claim": e.claim,
                        "value": e.value,
                        "source_name": e.source_name,
                        "source_type": e.source_type,
                        "source_url": e.source_url,
                        "source_status": e.source_status,
                        "published_at": e.published_at.isoformat() if e.published_at else None,
                        "observed_at": e.observed_at.isoformat(),
                        "confidence": e.confidence,
                        "verified": e.verified,
                    }
                    for e in opp.evidence_chain
                ],
                "evidence_confidence": opp.evidence_confidence.value,
                "evidence_count": opp.evidence_count,
                "verified_evidence_count": opp.verified_evidence_count,
                "contactability": opp.contactability,
                "contactability_evidence": opp.contactability_evidence,
            }
            audit.append(opp_audit)

        with open(filepath, "w") as f:
            json.dump(audit, f, indent=2, default=str)

        return str(filepath)
