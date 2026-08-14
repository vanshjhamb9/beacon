from __future__ import annotations

from typing import Any

from revenue_quality_recovery.models.types import DuplicateMatch, DuplicateRecoveryResult, UNKNOWN


class DuplicateRecoveryEngine:
    """Rule 7 — merge by domain, linkedin, org schema, legal name, alias, favicon hash."""

    MATCH_KEYS = ("domain", "linkedin", "organization_schema", "legal_name", "alias", "favicon_hash")

    def find_duplicates(self, companies: list[dict[str, Any]]) -> DuplicateRecoveryResult:
        matches: list[DuplicateMatch] = []
        evidence: list[str] = []
        n = len(companies)
        if n < 2:
            return DuplicateRecoveryResult(duplicate_rate=0.0, evidence=["insufficient_companies"])

        for i in range(n):
            for j in range(i + 1, n):
                a, b = companies[i], companies[j]
                keys = self._match_keys(a, b)
                if not keys:
                    continue
                conf = min(99.0, 40.0 + 12.0 * len(keys))
                merge = len(keys) >= 1 and ("domain" in keys or "linkedin" in keys or len(keys) >= 2)
                matches.append(
                    DuplicateMatch(
                        company_a=str(a.get("company_id") or a.get("id") or a.get("company_name") or f"a{i}"),
                        company_b=str(b.get("company_id") or b.get("id") or b.get("company_name") or f"b{j}"),
                        match_keys=keys,
                        confidence=round(conf, 2),
                        merge_recommended=merge,
                        evidence=[f"match:{k}" for k in keys],
                    )
                )

        # Approximate duplicate rate: unique companies involved / total
        involved: set[str] = set()
        for m in matches:
            if m.merge_recommended:
                involved.add(m.company_a)
                involved.add(m.company_b)
        rate = round(100.0 * len(involved) / n, 2) if n else 0.0
        evidence.append(f"matches:{len(matches)}")
        evidence.append(f"duplicate_rate:{rate}")
        return DuplicateRecoveryResult(
            matches=matches,
            duplicate_rate=rate,
            merge_plans=sum(1 for m in matches if m.merge_recommended),
            evidence=evidence,
        )

    def _match_keys(self, a: dict[str, Any], b: dict[str, Any]) -> list[str]:
        keys: list[str] = []
        da = self._norm_domain(a.get("domain") or a.get("website") or a.get("primary_domain"))
        db = self._norm_domain(b.get("domain") or b.get("website") or b.get("primary_domain"))
        if da and db and da == db:
            keys.append("domain")

        la = self._norm(a.get("linkedin") or a.get("linkedin_company") or a.get("linkedin_url"))
        lb = self._norm(b.get("linkedin") or b.get("linkedin_company") or b.get("linkedin_url"))
        if la and lb and la == lb:
            keys.append("linkedin")

        sa = self._schema_id(a.get("organization_schema") or a.get("schema_org"))
        sb = self._schema_id(b.get("organization_schema") or b.get("schema_org"))
        if sa and sb and sa == sb:
            keys.append("organization_schema")

        na = self._norm(a.get("legal_name") or a.get("company_name") or a.get("name"))
        nb = self._norm(b.get("legal_name") or b.get("company_name") or b.get("name"))
        if na and nb and na == nb:
            keys.append("legal_name")

        aliases_a = {self._norm(x) for x in (a.get("aliases") or []) if x}
        aliases_b = {self._norm(x) for x in (b.get("aliases") or []) if x}
        if na:
            aliases_a.add(na)
        if nb:
            aliases_b.add(nb)
        if aliases_a & aliases_b and "legal_name" not in keys:
            # alias overlap distinct from exact legal name already counted
            if (aliases_a & aliases_b) - ({na, nb} & {na, nb} if na == nb else set()):
                keys.append("alias")
            elif na != nb and (na in aliases_b or nb in aliases_a):
                keys.append("alias")

        fa = str(a.get("favicon_hash") or "")
        fb = str(b.get("favicon_hash") or "")
        if fa and fb and fa == fb:
            keys.append("favicon_hash")

        return keys

    def _norm(self, value: Any) -> str:
        if not value or value == UNKNOWN:
            return ""
        return str(value).strip().lower().removeprefix("https://").removeprefix("http://").removeprefix("www.")

    def _norm_domain(self, value: Any) -> str:
        raw = self._norm(value)
        if not raw:
            return ""
        return raw.split("/")[0]

    def _schema_id(self, schema: Any) -> str:
        if not isinstance(schema, dict):
            return ""
        return self._norm(schema.get("@id") or schema.get("url") or schema.get("name"))
