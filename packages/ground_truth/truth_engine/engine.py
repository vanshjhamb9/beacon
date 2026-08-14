from __future__ import annotations

from typing import Any

from ground_truth.models.types import AttributedField, CompanyTruthProfile, TruthQuestions, UNKNOWN

QUESTIONS = (
    "who_are_they",
    "what_do_they_do",
    "why_need_us",
    "where_found",
    "can_contact",
    "who_decides",
    "why_now",
)


class CompanyTruthEngine:
    """Rule 1–2 — ONE truth profile. All 7 questions must be answered for Founder Queue."""

    def build(self, payload: dict[str, Any], *, contacts: dict[str, Any] | None = None) -> CompanyTruthProfile:
        collected_at = payload.get("collected_at") or payload.get("last_seen_at")
        source = str(payload.get("source") or "company_record")
        contacts = contacts or {}

        name = str(payload.get("company_name") or payload.get("legal_name") or payload.get("name") or UNKNOWN)
        website = AttributedField.of(
            payload.get("website") or payload.get("primary_domain") or payload.get("domain"),
            source=str(payload.get("website_source") or source),
            collected_at=collected_at,
            confidence=float(payload.get("website_confidence") or 92),
            evidence=["website_observed"],
        )
        description = AttributedField.of(
            payload.get("description") or payload.get("business_description") or payload.get("narrative") or payload.get("memory_summary"),
            source=str(payload.get("description_source") or source),
            collected_at=collected_at,
            confidence=float(payload.get("description_confidence") or 85),
            evidence=["description_observed"],
        )
        country = AttributedField.of(
            payload.get("country") or payload.get("hq") or payload.get("location"),
            source=str(payload.get("country_source") or source),
            collected_at=collected_at,
            confidence=float(payload.get("country_confidence") or 80),
            evidence=["country_observed"],
        )
        employees = AttributedField.of(
            payload.get("employees") or payload.get("employee_estimate"),
            source=str(payload.get("employees_source") or source),
            collected_at=collected_at,
            confidence=float(payload.get("employees_confidence") or 70),
            evidence=["employees_observed"],
        )
        industry = AttributedField.of(
            payload.get("industry"),
            source=str(payload.get("industry_source") or source),
            collected_at=collected_at,
            confidence=float(payload.get("industry_confidence") or 88),
            evidence=["industry_observed"],
        )
        stage = AttributedField.of(
            payload.get("stage") or self._infer_stage(payload),
            source=source,
            collected_at=collected_at,
            confidence=65.0,
            evidence=["stage_inferred_or_observed"],
        )
        funding = AttributedField.of(
            payload.get("funding") or payload.get("funding_stage"),
            source=str(payload.get("funding_source") or source),
            collected_at=collected_at,
            confidence=70.0,
            evidence=["funding_observed"],
        )

        products = [
            AttributedField.of(p if not isinstance(p, dict) else p.get("name"), source=source, collected_at=collected_at, confidence=75.0, evidence=["product"])
            for p in (payload.get("products") or [])
            if p
        ]
        technology = [
            AttributedField.of(
                t.get("name") if isinstance(t, dict) else t,
                source=str((t.get("source") if isinstance(t, dict) else None) or source),
                collected_at=collected_at,
                confidence=float((t.get("confidence") if isinstance(t, dict) else None) or 80),
                evidence=["technology"],
            )
            for t in (payload.get("technologies") or payload.get("technology") or [])
            if t
        ]

        corpus = self._corpus(payload)
        ai_usage = AttributedField.of(
            "YES" if any(x in corpus for x in ("openai", "anthropic", "llm", "ai ", "chatgpt", "machine learning")) else ("NO" if corpus else None),
            source=source,
            collected_at=collected_at,
            confidence=80.0,
            evidence=["ai_usage_signal"],
        )
        hiring_ai = self._hiring_flag(corpus, ("hiring ai", "ai engineer", "ml engineer", "machine learning"), source, collected_at)
        hiring_backend = self._hiring_flag(corpus, ("hiring backend", "backend engineer", "backend developer"), source, collected_at)
        hiring_product = self._hiring_flag(corpus, ("hiring product", "product manager", "product designer"), source, collected_at)
        hiring_ml = self._hiring_flag(corpus, ("hiring ml", "ml engineer", "machine learning"), source, collected_at)

        intent_level = payload.get("intent_level") or payload.get("buying_intent") or self._intent_level(corpus)
        intent = AttributedField.of(intent_level, source=source, collected_at=collected_at, confidence=82.0, evidence=["intent"])
        reasons = []
        if "hiring" in corpus:
            reasons.append("Hiring signals")
        if "funding" in corpus or "raised" in corpus:
            reasons.append("Funding / expansion")
        if "openai" in corpus or "automation" in corpus:
            reasons.append("AI / automation motion")
        if payload.get("products"):
            reasons.append("New products")
        intent_reason = AttributedField.of(
            "; ".join(reasons) if reasons else payload.get("intent_reason") or payload.get("why_now"),
            source=source,
            collected_at=collected_at,
            confidence=78.0,
            evidence=["intent_reason"],
        )

        needs_raw = payload.get("needs") or []
        if not needs_raw:
            if "automation" in corpus or "manual" in corpus:
                needs_raw.append("Automation")
            if "enterprise" in corpus or "ai" in corpus:
                needs_raw.append("Enterprise AI")
            if "internal tools" in corpus or "workflow" in corpus:
                needs_raw.append("Internal Tools")
        needs = [
            AttributedField.of(n, source=source, collected_at=collected_at, confidence=75.0, evidence=["need"])
            for n in needs_raw
            if n
        ]

        dms = []
        for person in contacts.get("decision_makers") or payload.get("decision_makers") or []:
            if isinstance(person, dict) and person.get("name"):
                title = person.get("title") or person.get("role") or UNKNOWN
                dms.append(
                    AttributedField.of(
                        f"{person['name']} ({title})",
                        source=str(person.get("source") or "decision_makers"),
                        collected_at=person.get("collected_at") or collected_at,
                        confidence=float(person.get("confidence") or 80),
                        evidence=["decision_maker"],
                    )
                )

        emails = self._normalize_contact_list(contacts.get("emails") or payload.get("emails") or [], "email", source, collected_at)
        phones = self._normalize_contact_list(contacts.get("phones") or payload.get("phones") or [], "phone", source, collected_at)
        linkedin = self._normalize_contact_list(
            contacts.get("linkedin")
            or ([payload.get("linkedin_company") or payload.get("linkedin_url")] if (payload.get("linkedin_company") or payload.get("linkedin_url")) else []),
            "linkedin",
            source,
            collected_at,
        )
        twitter_raw = payload.get("twitter") or []
        social = payload.get("social") or {}
        if isinstance(social, dict) and social.get("twitter"):
            twitter_raw = list(twitter_raw) + [social.get("twitter")]
        twitter = self._normalize_contact_list(twitter_raw if isinstance(twitter_raw, list) else [twitter_raw], "twitter", source, collected_at)

        evidence_sources = []
        for label in ("reddit", "hn", "jobs", "funding", "website", "github", "linkedin"):
            if label in corpus or label in str(payload.get("source") or "").lower() or any(label in str(s).lower() for s in (payload.get("signals") or [])):
                evidence_sources.append(AttributedField.of(label.title(), source=source, collected_at=collected_at, confidence=70.0, evidence=[f"source:{label}"]))
        for item in payload.get("evidence") or []:
            src = item.get("source") if isinstance(item, dict) else source
            evidence_sources.append(AttributedField.of(str(src), source=str(src), collected_at=collected_at, confidence=80.0, evidence=["evidence_item"]))

        questions = self._questions(
            name=name,
            description=description,
            intent_reason=intent_reason,
            source=source,
            collected_at=collected_at,
            emails=emails,
            phones=phones,
            dms=dms,
            why_now=payload.get("why_now") or intent_reason.value,
            payload=payload,
        )

        trust = self._trust(website, description, industry, emails, dms, questions, payload)
        sales_ready = questions.all_answered and trust >= 80 and website.value != UNKNOWN

        return CompanyTruthProfile(
            company_id=str(payload.get("company_id") or payload.get("id") or UNKNOWN),
            company_name=name,
            website=website,
            description=description,
            country=country,
            employees=employees,
            industry=industry,
            stage=stage,
            funding=funding,
            products=[p for p in products if p.value != UNKNOWN][:20],
            technology=[t for t in technology if t.value != UNKNOWN][:30],
            ai_usage=ai_usage,
            hiring_ai=hiring_ai,
            hiring_backend=hiring_backend,
            hiring_product=hiring_product,
            hiring_ml=hiring_ml,
            intent=intent,
            intent_reason=intent_reason,
            needs=[n for n in needs if n.value != UNKNOWN][:10],
            decision_makers=dms[:20],
            contacts_email=emails[:20],
            contacts_linkedin=linkedin[:10],
            contacts_phone=phones[:20],
            contacts_twitter=twitter[:10],
            evidence_sources=evidence_sources[:20],
            trust=trust,
            sales_ready=sales_ready,
            questions=questions,
            scoring_version="alpha-plus-v1",
            evidence=[f"trust:{trust}", f"sales_ready:{sales_ready}", f"questions:{questions.all_answered}"],
        )

    def _questions(self, **kwargs: Any) -> TruthQuestions:
        source = kwargs["source"]
        collected_at = kwargs["collected_at"]
        name = kwargs["name"]
        description = kwargs["description"]
        intent_reason = kwargs["intent_reason"]
        emails = kwargs["emails"]
        phones = kwargs["phones"]
        dms = kwargs["dms"]
        why_now = kwargs["why_now"]
        payload = kwargs["payload"]

        who = AttributedField.of(name if name != UNKNOWN else None, source=source, collected_at=collected_at, confidence=95.0, evidence=["identity"])
        what = description
        why_need = intent_reason if intent_reason.value != UNKNOWN else AttributedField.unknown(reason="unknown_why_need_us")
        where = AttributedField.of(payload.get("source") or payload.get("original_url"), source=source, collected_at=collected_at, confidence=90.0, evidence=["source"])
        can = AttributedField.of(
            "YES" if emails or phones or payload.get("contact_form") else None,
            source=source,
            collected_at=collected_at,
            confidence=88.0 if emails or phones else None,
            evidence=["contact_path"],
        )
        who_decides = AttributedField.of(
            dms[0].value if dms else (emails[0].value if emails else None),
            source=source,
            collected_at=collected_at,
            confidence=85.0 if dms or emails else None,
            evidence=["decision_maker_or_email"],
        )
        why_now_f = AttributedField.of(why_now if why_now and why_now != UNKNOWN else None, source=source, collected_at=collected_at, confidence=80.0, evidence=["why_now"])

        fields = {
            "who_are_they": who,
            "what_do_they_do": what,
            "why_need_us": why_need,
            "where_found": where,
            "can_contact": can,
            "who_decides": who_decides,
            "why_now": why_now_f,
        }
        missing = [k for k, v in fields.items() if v.value == UNKNOWN]
        return TruthQuestions(
            **fields,
            all_answered=len(missing) == 0,
            missing=missing,
            evidence=[f"answered:{7 - len(missing)}/7"] + [f"missing:{m}" for m in missing],
        )

    def _normalize_contact_list(self, items: list[Any], kind: str, source: str, collected_at: Any) -> list[AttributedField]:
        out: list[AttributedField] = []
        for item in items:
            if item is None or item == UNKNOWN:
                continue
            if hasattr(item, "value"):
                out.append(
                    AttributedField.of(
                        item.value,
                        source=str(getattr(item, "source", source) or source),
                        collected_at=getattr(item, "collected_at", collected_at),
                        confidence=float(getattr(item, "confidence", None) or 80),
                        evidence=list(getattr(item, "evidence", None) or [kind]),
                    )
                )
            elif isinstance(item, dict):
                out.append(
                    AttributedField.of(
                        item.get("value") or item.get(kind) or item.get("url") or item.get("email") or item.get("phone"),
                        source=str(item.get("source") or source),
                        collected_at=item.get("collected_at") or collected_at,
                        confidence=float(item.get("confidence") or 80),
                        evidence=[kind],
                    )
                )
            else:
                out.append(AttributedField.of(item, source=source, collected_at=collected_at, confidence=75.0, evidence=[kind]))
        # dedupe
        seen: set[str] = set()
        unique = []
        for f in out:
            key = str(f.value)
            if key in seen or f.value == UNKNOWN:
                continue
            seen.add(key)
            unique.append(f)
        return unique

    def _hiring_flag(self, corpus: str, keys: tuple[str, ...], source: str, collected_at: Any) -> AttributedField:
        hit = any(k in corpus for k in keys)
        return AttributedField.of("YES" if hit else "NO", source=source, collected_at=collected_at, confidence=75.0 if hit else 60.0, evidence=list(keys[:2]))

    def _intent_level(self, corpus: str) -> str:
        score = 0
        for k in ("hiring", "funding", "automation", "openai", "enterprise", "launch"):
            if k in corpus:
                score += 1
        if score >= 4:
            return "Very High"
        if score >= 2:
            return "High"
        if score >= 1:
            return "Medium"
        return "Low"

    def _infer_stage(self, payload: dict[str, Any]) -> str | None:
        funding = str(payload.get("funding") or "").lower()
        if "public" in funding or "ipo" in funding:
            return "Public"
        if "series" in funding or "growth" in funding:
            return "Growth"
        if "seed" in funding or "pre-seed" in funding:
            return "Seed"
        emp = payload.get("employees") or payload.get("employee_estimate")
        try:
            n = int(emp)
        except (TypeError, ValueError):
            return None
        if n >= 1000:
            return "Growth"
        if n >= 50:
            return "Scale-up"
        return "Startup"

    def _trust(self, website, description, industry, emails, dms, questions, payload) -> float:
        score = 0.0
        if website.value != UNKNOWN:
            score += 20
        if description.value != UNKNOWN:
            score += 15
        if industry.value != UNKNOWN:
            score += 10
        if emails:
            score += 15
        if dms:
            score += 15
        if questions.all_answered:
            score += 15
        if payload.get("ssl") or payload.get("website_alive"):
            score += 5
        if payload.get("evidence") or payload.get("timeline"):
            score += 5
        return round(min(100.0, score), 2)

    def _corpus(self, payload: dict[str, Any]) -> str:
        parts = [
            str(payload.get("narrative") or ""),
            str(payload.get("description") or ""),
            str(payload.get("business_description") or ""),
            str(payload.get("source") or ""),
        ]
        for s in payload.get("signals") or []:
            parts.append(str(s.get("value") if isinstance(s, dict) else s))
        for t in payload.get("technologies") or []:
            parts.append(str(t.get("name") if isinstance(t, dict) else t))
        for row in payload.get("timeline") or []:
            if isinstance(row, dict):
                parts.append(str(row.get("summary") or row.get("signal_type") or ""))
        for item in payload.get("evidence") or []:
            if isinstance(item, dict):
                parts.append(str(item.get("summary") or ""))
            else:
                parts.append(str(item))
        return " ".join(parts).lower()
