"""COMAI B2B Partner Discovery Engine - Export Pipeline.

This module implements the export pipeline for generating partner discovery results.
Creates JSON files and final report for partner qualification.

COMAI B2B IS NOT AN AGENCY DIRECTORY.
WE ARE BUILDING A PARTNER ACQUISITION ENGINE.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.models.partner import (
    ExportData,
    PartnerRecord,
    PartnerTier,
    FinalVerdict,
)


# ============================================================
# EXPORT PIPELINE
# ============================================================

class PartnerExportPipeline:
    """Export pipeline for partner discovery results.
    
    This pipeline generates:
    - comai_b2b_hot_partners.json (Tier A)
    - comai_b2b_high_potential.json (Tier B)
    - comai_b2b_nurture.json (Tier C)
    - comai_b2b_rejected.json (Rejected)
    - comai_b2b_evidence_audit.json (Evidence audit)
    - comai_b2b_contactability_audit.json (Contactability audit)
    - COMAI_B2B_FINAL_REPORT.md (Executive summary)
    """
    
    def __init__(self, output_dir: str = "exports/comai_b2b_partners"):
        """Initialize the export pipeline.
        
        Args:
            output_dir: Output directory for exported files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_results(self, partners: list[PartnerRecord]) -> ExportData:
        """Export partner discovery results.
        
        Args:
            partners: List of PartnerRecord objects
            
        Returns:
            ExportData with all export information
        """
        export_data = ExportData(
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
        
        # Categorize partners
        for partner in partners:
            export_data.total_discovered += 1
            
            if partner.final_verdict == "REJECT":
                export_data.rejected += 1
                export_data.rejected_list.append(partner)
                continue
            
            # Count verified agencies
            if partner.agency_type:
                export_data.verified_agencies += 1
            
            # Count explicit partnership intent
            if partner.partner_intent == "EXPLICIT":
                export_data.explicit_partnership_intent += 1
            
            # Count contactable
            if partner.contactability in ["HIGH", "MEDIUM"]:
                export_data.contactable += 1
            
            # Categorize by tier
            if partner.partner_tier == "A":
                export_data.tier_a += 1
                export_data.hot_partners += 1
                export_data.hot_partners_list.append(partner)
            elif partner.partner_tier == "B":
                export_data.tier_b += 1
                export_data.high_potential += 1
                export_data.high_potential_list.append(partner)
            else:
                export_data.tier_c += 1
                export_data.nurture_list.append(partner)
            
            # Build evidence audit
            export_data.evidence_audit.append({
                "opportunity_id": partner.opportunity_id,
                "agency_name": partner.agency_name,
                "client_access_score": partner.client_access_score,
                "client_access_evidence": partner.client_access_evidence,
                "comai_partner_fit": partner.comai_partner_fit,
                "comai_fit_evidence": partner.comai_fit_evidence,
                "partner_intent": partner.partner_intent,
                "partner_intent_evidence": partner.partner_intent_evidence,
            })
            
            # Build contactability audit
            export_data.contactability_audit.append({
                "opportunity_id": partner.opportunity_id,
                "agency_name": partner.agency_name,
                "email": partner.email,
                "email_status": partner.email_status,
                "email_evidence": partner.email_evidence,
                "linkedin_url": partner.linkedin_url,
                "linkedin_status": partner.linkedin_status,
                "contactability": partner.contactability,
                "contactability_evidence": partner.contactability_evidence,
            })
        
        # Export to files
        self._export_hot_partners(export_data.hot_partners_list)
        self._export_high_potential(export_data.high_potential_list)
        self._export_nurture(export_data.nurture_list)
        self._export_rejected(export_data.rejected_list)
        self._export_evidence_audit(export_data.evidence_audit)
        self._export_contactability_audit(export_data.contactability_audit)
        self._export_final_report(export_data)
        
        return export_data
    
    def _export_hot_partners(self, partners: list[PartnerRecord]):
        """Export Tier A hot partners."""
        data = [p.to_dict() for p in partners]
        self._write_json("comai_b2b_hot_partners.json", data)
    
    def _export_high_potential(self, partners: list[PartnerRecord]):
        """Export Tier B high potential partners."""
        data = [p.to_dict() for p in partners]
        self._write_json("comai_b2b_high_potential.json", data)
    
    def _export_nurture(self, partners: list[PartnerRecord]):
        """Export Tier C nurture partners."""
        data = [p.to_dict() for p in partners]
        self._write_json("comai_b2b_nurture.json", data)
    
    def _export_rejected(self, partners: list[PartnerRecord]):
        """Export rejected partners."""
        data = [p.to_dict() for p in partners]
        self._write_json("comai_b2b_rejected.json", data)
    
    def _export_evidence_audit(self, audit: list[dict]):
        """Export evidence audit."""
        self._write_json("comai_b2b_evidence_audit.json", audit)
    
    def _export_contactability_audit(self, audit: list[dict]):
        """Export contactability audit."""
        self._write_json("comai_b2b_contactability_audit.json", audit)
    
    def _export_final_report(self, export_data: ExportData):
        """Export final report as Markdown."""
        report = self._generate_markdown_report(export_data)
        report_path = self.output_dir / "COMAI_B2B_FINAL_REPORT.md"
        report_path.write_text(report, encoding="utf-8")
    
    def _generate_markdown_report(self, export_data: ExportData) -> str:
        """Generate Markdown final report."""
        lines = [
            "# COMAI B2B Partner Discovery Report",
            "",
            "## Executive Summary",
            "",
            f"- **Generated At**: {export_data.generated_at}",
            f"- **Total Discovered**: {export_data.total_discovered}",
            f"- **Verified Agencies**: {export_data.verified_agencies}",
            f"- **Explicit Partnership Intent**: {export_data.explicit_partnership_intent}",
            f"- **High Potential**: {export_data.high_potential}",
            f"- **Hot Partners**: {export_data.hot_partners}",
            f"- **Contactable**: {export_data.contactable}",
            f"- **Tier A (Hot)**: {export_data.tier_a}",
            f"- **Tier B (High Potential)**: {export_data.tier_b}",
            f"- **Tier C (Nurture)**: {export_data.tier_c}",
            f"- **Rejected**: {export_data.rejected}",
            "",
            "## Discovery Funnel",
            "",
            "```",
            "DISCOVERED",
            "    ↓",
            "AGENCY VERIFIED",
            "    ↓",
            "CLIENT BASE VERIFIED",
            "    ↓",
            "COMAI FIT",
            "    ↓",
            "PARTNER INTENT / POTENTIAL",
            "    ↓",
            "DECISION MAKER",
            "    ↓",
            "CONTACTABLE",
            "    ↓",
            "PARTNER READY",
            "    ↓",
            "OUTREACH QUEUE",
            "```",
            "",
            "## Tier A Partners (Immediate Outreach)",
            "",
        ]
        
        if export_data.hot_partners_list:
            for partner in export_data.hot_partners_list:
                lines.append(f"### {partner.agency_name}")
                lines.append(f"- **URL**: {partner.agency_url}")
                lines.append(f"- **Country**: {partner.country}")
                lines.append(f"- **Agency Type**: {partner.agency_type}")
                lines.append(f"- **Client Access Score**: {partner.client_access_score}")
                lines.append(f"- **COMAI Partner Fit**: {partner.comai_partner_fit}")
                lines.append(f"- **Partner Intent**: {partner.partner_intent}")
                lines.append(f"- **Contactability**: {partner.contactability}")
                lines.append(f"- **Email**: {partner.email} ({partner.email_status})")
                lines.append(f"- **Decision Maker**: {partner.founder_name} ({partner.founder_role})")
                lines.append(f"- **Why This Agency**: {partner.why_this_agency}")
                lines.append(f"- **Recommended Pitch Angle**: {partner.recommended_pitch_angle}")
                lines.append("")
        else:
            lines.append("No Tier A partners found.")
            lines.append("")
        
        lines.extend([
            "## Tier B Partners (High Potential)",
            "",
        ])
        
        if export_data.high_potential_list:
            for partner in export_data.high_potential_list:
                lines.append(f"### {partner.agency_name}")
                lines.append(f"- **URL**: {partner.agency_url}")
                lines.append(f"- **Country**: {partner.country}")
                lines.append(f"- **Agency Type**: {partner.agency_type}")
                lines.append(f"- **Client Access Score**: {partner.client_access_score}")
                lines.append(f"- **COMAI Partner Fit**: {partner.comai_partner_fit}")
                lines.append(f"- **Partner Intent**: {partner.partner_intent}")
                lines.append(f"- **Contactability**: {partner.contactability}")
                lines.append(f"- **Email**: {partner.email} ({partner.email_status})")
                lines.append(f"- **Decision Maker**: {partner.founder_name} ({partner.founder_role})")
                lines.append(f"- **Why This Agency**: {partner.why_this_agency}")
                lines.append(f"- **Recommended Pitch Angle**: {partner.recommended_pitch_angle}")
                lines.append("")
        else:
            lines.append("No Tier B partners found.")
            lines.append("")
        
        lines.extend([
            "## Tier C Partners (Nurture)",
            "",
            f"Count: {export_data.tier_c}",
            "",
        ])
        
        if export_data.nurture_list:
            lines.append("### Top Nurture Partners")
            lines.append("")
            for partner in export_data.nurture_list[:10]:
                lines.append(f"- **{partner.agency_name}** ({partner.country}) - {partner.agency_type}")
            lines.append("")
        
        lines.extend([
            "## Rejected Agencies",
            "",
            f"Count: {export_data.rejected}",
            "",
        ])
        
        if export_data.rejected_list:
            lines.append("### Top Rejection Reasons")
            lines.append("")
            rejection_reasons = {}
            for partner in export_data.rejected_list:
                for reason in partner.rejection_reason.split("; "):
                    if reason:
                        rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
            
            for reason, count in sorted(rejection_reasons.items(), key=lambda x: x[1], reverse=True)[:5]:
                lines.append(f"- **{reason}**: {count}")
            lines.append("")
        
        lines.extend([
            "## Evidence Audit",
            "",
            "### Client Access Score Distribution",
            "",
        ])
        
        # Calculate score distribution
        scores = [p.client_access_score for p in export_data.hot_partners_list + export_data.high_potential_list + export_data.nurture_list]
        if scores:
            avg_score = sum(scores) / len(scores)
            lines.append(f"- **Average Score**: {avg_score:.1f}")
            lines.append(f"- **Min Score**: {min(scores)}")
            lines.append(f"- **Max Score**: {max(scores)}")
        else:
            lines.append("No scores available.")
        lines.append("")
        
        lines.extend([
            "### COMAI Partner Fit Distribution",
            "",
        ])
        
        fits = [p.comai_partner_fit for p in export_data.hot_partners_list + export_data.high_potential_list + export_data.nurture_list]
        if fits:
            avg_fit = sum(fits) / len(fits)
            lines.append(f"- **Average Fit**: {avg_fit:.1f}")
            lines.append(f"- **Min Fit**: {min(fits)}")
            lines.append(f"- **Max Fit**: {max(fits)}")
        else:
            lines.append("No fit scores available.")
        lines.append("")
        
        lines.extend([
            "## Contactability Audit",
            "",
        ])
        
        # Calculate contactability distribution
        contactability_counts = {}
        for partner in export_data.hot_partners_list + export_data.high_potential_list + export_data.nurture_list:
            level = partner.contactability
            contactability_counts[level] = contactability_counts.get(level, 0) + 1
        
        for level, count in sorted(contactability_counts.items()):
            lines.append(f"- **{level}**: {count}")
        lines.append("")
        
        lines.extend([
            "## Final CTO Test",
            "",
            "> \"If I were running COMAI, would I genuinely want this agency to introduce COMAI to its clients?\"",
            "",
            "### YES requires evidence that:",
            "",
            "1. They work with businesses.",
            "2. Those businesses overlap with COMAI's target market.",
            "3. They have an ongoing client relationship.",
            "4. They can influence client technology/service decisions.",
            "5. They have a credible decision maker.",
            "6. Beacon has a legitimate contact route.",
            "7. COMAI solves a relevant client problem.",
            "",
            "## Final Principle",
            "",
            "- **COMAI B2B IS NOT AN AGENCY DIRECTORY.**",
            "- **WE ARE BUILDING A PARTNER ACQUISITION ENGINE.**",
            "- Do NOT optimize for number of agencies.",
            "- Find agencies that can actually introduce COMAI to businesses.",
            "- **CLIENT ACCESS > AGENCY SIZE.**",
            "- **PARTNER POTENTIAL > WEBSITE QUALITY.**",
            "- **BUYING/PARTNERSHIP INTENT > GENERIC AGENCY EXISTENCE.**",
            "- **EVIDENCE > ASSUMPTION.**",
            "- **QUALITY > QUANTITY.**",
            "- **DO NOT SEND OUTREACH AUTOMATICALLY.**",
            "- Only qualified Tier A and selected Tier B partners enter the outreach queue after approval.",
            "- **STOP AFTER GENERATING THE REPORT.**",
            "",
        ])
        
        return "\n".join(lines)
    
    def _write_json(self, filename: str, data: Any):
        """Write data to JSON file."""
        filepath = self.output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
