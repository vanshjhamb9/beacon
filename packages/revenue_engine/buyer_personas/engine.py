from revenue_engine.models.types import (
    BuyerPersona,
    BuyerPersonaResult,
    RevenueOpportunityInput,
    ServiceMatch,
)


class BuyerPersonaEngine:
    def infer(self, item: RevenueOpportunityInput, primary: ServiceMatch) -> list[BuyerPersonaResult]:
        service_text = f"{primary.service.name} {primary.service.category}".lower()
        pain_keys = {str(pain.get("category", "")).lower() for pain in item.pains}
        stage = (item.company_stage or "").lower()
        personas: list[BuyerPersonaResult] = []

        if stage in {"startup", "early", "seed", "series_a"} or "founder" in service_text:
            personas.append(
                self._persona(
                    BuyerPersona.FOUNDER,
                    88.0,
                    "Early-stage companies typically keep buying authority with founders.",
                    {"company_stage": item.company_stage},
                )
            )

        if "support" in pain_keys or "chatbot" in service_text or "customer" in service_text:
            personas.append(
                self._persona(
                    BuyerPersona.SUPPORT_HEAD,
                    86.0,
                    "Support pain aligns with Support Head ownership.",
                    {"pain_overlap": sorted(pain_keys & {"support", "customer_experience"})},
                )
            )
            personas.append(
                self._persona(
                    BuyerPersona.COO,
                    72.0,
                    "Operational sponsor is likely when support efficiency is strategic.",
                    {"service_category": primary.service.category},
                )
            )

        if (
            "engineering" in pain_keys
            or "development" in service_text
            or "api" in service_text
            or "ai" in service_text
            or primary.service.category in {"ai", "ai_platform", "software", "integration"}
        ):
            personas.append(
                self._persona(
                    BuyerPersona.CTO,
                    84.0,
                    "Technical delivery requires CTO sponsorship.",
                    {"service_key": primary.service.service_key},
                )
            )
            personas.append(
                self._persona(
                    BuyerPersona.ENGINEERING_MANAGER,
                    76.0,
                    "Implementation ownership typically sits with Engineering Manager.",
                    {"complexity": primary.service.complexity},
                )
            )

        if "automation" in pain_keys or "operations" in pain_keys or "workflow" in service_text:
            personas.append(
                self._persona(
                    BuyerPersona.OPERATIONS_HEAD,
                    82.0,
                    "Workflow and operations pains map to Operations Head ownership.",
                    {"pain_overlap": sorted(pain_keys & {"automation", "operations"})},
                )
            )
            personas.append(
                self._persona(
                    BuyerPersona.COO,
                    78.0,
                    "Operational transformation needs COO executive sponsorship.",
                    {"service_category": primary.service.category},
                )
            )

        if (
            "marketing" in pain_keys
            or "website" in service_text
            or "ui/ux" in service_text
            or "shopify" in service_text
            or "woocommerce" in service_text
        ):
            personas.append(
                self._persona(
                    BuyerPersona.MARKETING_HEAD,
                    78.0,
                    "Digital presence and storefront projects often originate with Marketing Head.",
                    {"service_key": primary.service.service_key},
                )
            )

        personas.append(
            self._persona(
                BuyerPersona.CEO,
                64.0,
                "CEO validates budget priority and strategic timing.",
                {"opportunity_score": item.opportunity_score},
            )
        )

        unique: dict[str, BuyerPersonaResult] = {}
        for persona in personas:
            current = unique.get(persona.persona)
            if current is None or persona.confidence > current.confidence:
                unique[persona.persona] = persona
        return sorted(unique.values(), key=lambda persona: persona.confidence, reverse=True)[:4]

    def _persona(
        self,
        persona: BuyerPersona,
        confidence: float,
        explanation: str,
        evidence: dict[str, object],
    ) -> BuyerPersonaResult:
        return BuyerPersonaResult(
            persona=persona.value,
            confidence=confidence,
            explanation=explanation,
            evidence=evidence,
        )
