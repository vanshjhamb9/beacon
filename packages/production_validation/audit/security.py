from __future__ import annotations

from production_validation.models.types import (
    HealthStatus,
    ProductionValidationInput,
    SecurityAuditFinding,
    SecurityAuditReport,
)


CONTROLS = (
    ("oauth_tokens", "OAuth token storage encrypted and refreshable"),
    ("secrets", "Secrets not committed; env-based configuration"),
    ("encryption", "At-rest encryption helpers present for sensitive payloads"),
    ("webhook_signatures", "Webhook HMAC verification for Meta/Gmail paths"),
    ("rbac", "JWT role claims available for API auth"),
    ("audit_logs", "Append-only campaign/LRE audit trails"),
    ("rate_limits", "Daily/hourly send quotas and dedupe"),
    ("csrf", "Browser cookie CSRF posture reviewed for dashboard"),
    ("jwt", "JWT utilities available in API security core"),
    ("api_keys", "Provider API keys loaded from settings/secrets"),
)


class SecurityAuditEngine:
    def audit(self, item: ProductionValidationInput) -> SecurityAuditReport:
        flags = item.security_flags or {}
        findings: list[SecurityAuditFinding] = []
        for control, detail in CONTROLS:
            ok = bool(flags.get(control, True))
            status = HealthStatus.PASS if ok else HealthStatus.FAIL
            findings.append(
                SecurityAuditFinding(
                    control=control,
                    status=status,
                    detail=detail if ok else f"{detail} — MISSING/FAILED",
                    recommendation="OK" if ok else f"Remediate {control} before production sends.",
                )
            )
        if not item.oauth_ok:
            findings.append(
                SecurityAuditFinding(
                    control="oauth_live",
                    status=HealthStatus.FAIL,
                    detail="Live OAuth status unhealthy",
                    recommendation="Refresh OAuth tokens immediately.",
                )
            )
        score = sum(100.0 if f.status == HealthStatus.PASS else 0.0 for f in findings) / max(len(findings), 1)
        overall = HealthStatus.PASS if score >= 90 else HealthStatus.WARNING if score >= 70 else HealthStatus.FAIL
        return SecurityAuditReport(
            findings=findings,
            overall_status=overall,
            score=round(score, 4),
            evidence=[f"controls:{len(findings)}", f"score:{score}"],
        )
