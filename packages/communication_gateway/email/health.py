from __future__ import annotations

"""Lightweight email health + DNS auth status helpers (compose-only)."""


def email_health_score(
    *,
    bounce_rate: float = 0.0,
    spam_complaint_rate: float = 0.0,
    open_rate: float = 0.0,
    dkim_ok: bool = True,
    spf_ok: bool = True,
) -> dict[str, object]:
    score = 100.0
    evidence: list[str] = []
    if bounce_rate > 0.02:
        score -= min(40.0, bounce_rate * 400)
        evidence.append(f"bounce_rate:{bounce_rate}")
    if spam_complaint_rate > 0.001:
        score -= min(30.0, spam_complaint_rate * 5000)
        evidence.append(f"spam_complaint_rate:{spam_complaint_rate}")
    if open_rate < 0.15:
        score -= 10.0
        evidence.append(f"open_rate:{open_rate}")
    if not dkim_ok:
        score -= 15.0
        evidence.append("dkim:fail")
    else:
        evidence.append("dkim:pass")
    if not spf_ok:
        score -= 15.0
        evidence.append("spf:fail")
    else:
        evidence.append("spf:pass")
    score = max(0.0, min(100.0, round(score, 4)))
    status = "healthy" if score >= 75 else ("watch" if score >= 50 else "at_risk")
    return {"score": score, "status": status, "dkim": dkim_ok, "spf": spf_ok, "evidence": evidence}
