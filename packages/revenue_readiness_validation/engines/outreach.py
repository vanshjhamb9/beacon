from __future__ import annotations

from typing import Any

from revenue_readiness_validation.models.types import PhaseStatus


class OutreachInfrastructureEngine:
    """Phase 8 — production send gate from live config/probes (never assume healthy)."""

    CHECKS = (
        "gmail_oauth",
        "whatsapp_business",
        "calendly",
        "domain_auth_spf_dkim_dmarc",
        "email_sandbox",
        "rate_limits",
        "unsubscribe_handling",
        "bounce_handling",
        "reply_threading",
        "stop_on_reply",
        "production_send_flag",
    )

    def evaluate(self, probes: dict[str, Any]) -> dict[str, Any]:
        results: dict[str, dict[str, Any]] = {}
        for key in self.CHECKS:
            ok = bool(probes.get(key))
            results[key] = {
                "ok": ok,
                "value": probes.get(f"{key}_detail", "configured" if ok else "not_configured"),
                "evidence": probes.get(f"{key}_evidence") or ([f"{key}:true"] if ok else [f"{key}:false"]),
            }
        passed = sum(1 for r in results.values() if r["ok"])
        total = len(results)
        # Production requires all critical send-path checks
        critical = ("gmail_oauth", "email_sandbox", "rate_limits", "unsubscribe_handling", "stop_on_reply", "production_send_flag")
        critical_ok = all(results[k]["ok"] for k in critical)
        status = PhaseStatus.PASS if critical_ok and passed == total else (
            PhaseStatus.WARN if passed >= total // 2 else PhaseStatus.BLOCKED
        )
        return {
            "checks": results,
            "passed": passed,
            "total": total,
            "production_allowed": critical_ok and bool(probes.get("production_send_flag")),
            "status": status.value,
            "blockers": [k for k, v in results.items() if not v["ok"]],
        }
