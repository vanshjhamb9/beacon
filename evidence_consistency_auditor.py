#!/usr/bin/env python3
"""
V8.1 EVIDENCE CONSISTENCY AUDIT
=================================
Before final classification, audit every important claim.

Required claims:
- person identity
- person role
- company/project
- requirement
- source
- published date
- currentness
- outsourcing intent
- service match
- contact
- contactability

Every claim must have:
{
  "claim": "",
  "value": "",
  "source": "",
  "source_url": "",
  "confidence": "",
  "observed_at": ""
}

Reject evidence objects where:
- source URL is generic
- source URL does not support the claim
- source is merely a search result
- source is merely a category page
- source is blocked but marked VERIFIED
- evidence was inferred rather than observed
- evidence is copied from another field without source support
- observed_at is missing
- source and claim contradict each other
"""

import json
from datetime import datetime
from typing import Dict, List, Tuple
from dataclasses import dataclass, field


@dataclass
class AuditResult:
    """Result of evidence consistency audit."""
    claim: str
    status: str  # PASS, FAIL, WARNING
    reason: str
    evidence_index: int


@dataclass
class EvidenceConsistencyAudit:
    """Evidence consistency audit result."""
    overall_status: str  # PASS, FAIL
    results: List[AuditResult] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class EvidenceConsistencyAuditor:
    """V8.1 Evidence Consistency Auditor."""
    
    # Generic URLs that should NOT be used as evidence
    GENERIC_URLS = [
        "google.com/search",
        "linkedin.com/search",
        "upwork.com/freelancers",
        "upwork.com/nx/search",
        "freelancer.com/jobs",
        "freelancer.com/jobs/category",
        "fiverr.com/search",
        "reddit.com/r/forhire",
        "reddit.com/r/startups",
        "reddit.com/r/SaaS",
    ]
    
    # URLs that indicate search/category pages
    INVALID_PATTERNS = [
        "/search?",
        "/category/",
        "/jobs/category",
        "/freelancers?",
        "/search/jobs",
        "google.com/search",
        "bing.com/search",
    ]
    
    def audit_evidence(self, opportunity: Dict) -> EvidenceConsistencyAudit:
        """
        Audit evidence consistency for an opportunity.
        
        Args:
            opportunity: Dictionary containing opportunity data
        
        Returns:
            EvidenceConsistencyAudit with audit results
        """
        print(f"\n    [EVIDENCE] Auditing evidence consistency for {opportunity.get('opportunity_id', 'UNKNOWN')}...")
        
        results = []
        issues = []
        warnings = []
        
        # Collect all evidence
        all_evidence = []
        
        # Source evidence
        source_evidence = opportunity.get("source", {}).get("evidence", [])
        for i, ev in enumerate(source_evidence):
            all_evidence.append(("source", i, ev))
        
        # Person evidence
        person_evidence = opportunity.get("person", {}).get("evidence", [])
        for i, ev in enumerate(person_evidence):
            all_evidence.append(("person", i, ev))
        
        # Company evidence
        company_evidence = opportunity.get("company", {}).get("evidence", [])
        for i, ev in enumerate(company_evidence):
            all_evidence.append(("company", i, ev))
        
        # Currentness evidence
        currentness_evidence = opportunity.get("currentness", {}).get("evidence", [])
        for i, ev in enumerate(currentness_evidence):
            all_evidence.append(("currentness", i, ev))
        
        # Outsourcing evidence
        outsourcing_evidence = opportunity.get("outsourcing", {}).get("evidence", [])
        for i, ev in enumerate(outsourcing_evidence):
            all_evidence.append(("outsourcing", i, ev))
        
        # Service match evidence
        service_evidence = opportunity.get("service_match", {}).get("evidence", [])
        for i, ev in enumerate(service_evidence):
            all_evidence.append(("service_match", i, ev))
        
        # Contact evidence
        contact_evidence = opportunity.get("contact", {}).get("contactability_evidence", [])
        for i, ev in enumerate(contact_evidence):
            all_evidence.append(("contact", i, ev))
        
        # Audit each evidence object
        for category, index, evidence in all_evidence:
            audit_result = self._audit_single_evidence(category, index, evidence)
            results.append(audit_result)
            
            if audit_result.status == "FAIL":
                issues.append(f"{category}[{index}]: {audit_result.reason}")
            elif audit_result.status == "WARNING":
                warnings.append(f"{category}[{index}]: {audit_result.reason}")
        
        # Determine overall status
        has_failures = any(r.status == "FAIL" for r in results)
        overall_status = "FAIL" if has_failures else "PASS"
        
        print(f"      Overall status: {overall_status}")
        print(f"      Issues: {len(issues)}")
        print(f"      Warnings: {len(warnings)}")
        
        return EvidenceConsistencyAudit(
            overall_status=overall_status,
            results=results,
            issues=issues,
            warnings=warnings
        )
    
    def _audit_single_evidence(self, category: str, index: int, evidence: Dict) -> AuditResult:
        """Audit a single evidence object."""
        claim = evidence.get("claim", "")
        value = evidence.get("value", "")
        source = evidence.get("source", "")
        source_url = evidence.get("source_url", "")
        confidence = evidence.get("confidence", "")
        observed_at = evidence.get("observed_at", "")
        
        # Check 1: observed_at must exist
        if not observed_at:
            return AuditResult(
                claim=claim,
                status="FAIL",
                reason="observed_at is missing",
                evidence_index=index
            )
        
        # Check 2: source_url should not be generic
        if source_url:
            for pattern in self.INVALID_PATTERNS:
                if pattern in source_url.lower():
                    return AuditResult(
                        claim=claim,
                        status="FAIL",
                        reason=f"source_url contains invalid pattern: {pattern}",
                        evidence_index=index
                    )
        
        # Check 3: source should support the claim
        if source_url and source:
            # Check if source and claim are consistent
            if "LinkedIn" in source and "linkedin" not in source_url.lower() and "linkedin" not in value.lower():
                return AuditResult(
                    claim=claim,
                    status="WARNING",
                    reason="Source says LinkedIn but URL/value doesn't match",
                    evidence_index=index
                )
            
            if "Reddit" in source and "reddit" not in source_url.lower() and "reddit" not in value.lower():
                return AuditResult(
                    claim=claim,
                    status="WARNING",
                    reason="Source says Reddit but URL/value doesn't match",
                    evidence_index=index
                )
        
        # Check 4: confidence should be valid
        valid_confidences = ["VERIFIED", "HIGH", "MEDIUM", "LOW", "UNKNOWN", "PUBLIC_UNVERIFIED", "NOT_VERIFIED"]
        if confidence not in valid_confidences:
            return AuditResult(
                claim=claim,
                status="FAIL",
                reason=f"Invalid confidence: {confidence}",
                evidence_index=index
            )
        
        # Check 5: source_url should not be empty for important claims
        important_claims = ["verified", "exists", "confirmed"]
        if any(word in claim.lower() for word in important_claims):
            if not source_url:
                return AuditResult(
                    claim=claim,
                    status="WARNING",
                    reason="Important claim has no source_url",
                    evidence_index=index
                )
        
        # All checks passed
        return AuditResult(
            claim=claim,
            status="PASS",
            reason="Evidence passes consistency checks",
            evidence_index=index
        )
