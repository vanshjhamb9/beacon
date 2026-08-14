from __future__ import annotations

from sales_copilot.context.assembler import ContextAssembler
from sales_copilot.evaluation.grounding import GroundingValidator
from sales_copilot.evaluation.scorer import QualityScorer
from sales_copilot.generation.outreach_generator import OutreachGenerator
from sales_copilot.generation.package_generator import PackageGenerator
from sales_copilot.llm.factory import LLMProviderConfig, LLMProviderFactory
from sales_copilot.metrics.timing import CopilotTimer
from sales_copilot.models.types import (
    GenerationMetadata,
    LLMProviderName,
    LLMRequest,
    QualityScores,
    SalesCopilotInput,
    SalesIntelligencePackage,
)
from sales_copilot.prompting.versions import CURRENT_PROMPT_VERSION, get_prompt_version


class SalesCopilotPipeline:
    def __init__(
        self,
        *,
        assembler: ContextAssembler | None = None,
        package_generator: PackageGenerator | None = None,
        outreach_generator: OutreachGenerator | None = None,
        scorer: QualityScorer | None = None,
        grounding: GroundingValidator | None = None,
        llm_factory: LLMProviderFactory | None = None,
        timer: CopilotTimer | None = None,
        prompt_version: str | None = None,
    ) -> None:
        self.assembler = assembler or ContextAssembler()
        self.package_generator = package_generator or PackageGenerator()
        self.outreach_generator = outreach_generator or OutreachGenerator()
        self.scorer = scorer or QualityScorer()
        self.grounding = grounding or GroundingValidator()
        self.llm_factory = llm_factory or LLMProviderFactory(LLMProviderConfig())
        self.timer = timer or CopilotTimer()
        self.prompt_version = prompt_version or CURRENT_PROMPT_VERSION

    def process(self, item: SalesCopilotInput, *, version: int = 1) -> SalesIntelligencePackage:
        result, latency_ms = self.timer.time_call(lambda: self._process(item, version=version))
        generation = result.generation.model_copy(update={"generation_time_ms": latency_ms})
        return result.model_copy(update={"generation": generation})

    def _process(self, item: SalesCopilotInput, *, version: int) -> SalesIntelligencePackage:
        facts = self.assembler.assemble(item)
        sections = self.package_generator.generate(facts)
        style_variants = self.outreach_generator.generate_all_styles(facts)
        prompt = get_prompt_version(self.prompt_version)
        provider = self.llm_factory.create(item.preferred_provider)
        evidence_block = "\n".join(f"- [{ev.category}] {ev.summary}" for ev in facts.get("evidence") or [])
        request = LLMRequest(
            system_prompt=prompt.system_prompt,
            user_prompt=prompt.user_prompt_template.format(
                company_name=facts.get("company_name"),
                recommended_service=facts.get("recommended_service") or "Insufficient verified information.",
                business_pain=facts.get("business_pain") or "Insufficient verified information.",
                evidence_block=evidence_block or "Insufficient verified information.",
            ),
            model=provider.model,
            temperature=prompt.temperature,
        )
        llm_response = provider.complete(request)

        placeholder_quality = QualityScores(
            personalization=0,
            evidence_coverage=0,
            readability=0,
            professional_tone=0,
            length=0,
            call_to_action=0,
            confidence=0,
            overall=0,
        )
        draft_package = SalesIntelligencePackage(
            company_id=item.company_id,
            opportunity_id=item.opportunity_id,
            company_name=item.company_name,
            opportunity_score=float(item.opportunity_score or 0.0),
            recommended_service=str(facts.get("recommended_service") or ""),
            business_pain=str(facts.get("business_pain") or ""),
            version=version,
            sections=sections,
            style_variants=style_variants,
            evidence_chain=list(facts.get("evidence") or []),
            quality=placeholder_quality,
            generation=GenerationMetadata(
                prompt_version=prompt.version,
                llm_provider=LLMProviderName(provider.name),
                model=llm_response.model,
                temperature=prompt.temperature,
                prompt_tokens=llm_response.prompt_tokens,
                completion_tokens=llm_response.completion_tokens,
                total_tokens=llm_response.total_tokens,
                latency_ms=llm_response.latency_ms,
                cost_estimate_usd=llm_response.cost_estimate_usd,
            ),
            package_payload={
                "facts": {key: value for key, value in facts.items() if key not in {"evidence", "evidence_index"}},
                "llm_preview": llm_response.content[:2000],
                "grounding_issues": [],
            },
        )
        quality = self.scorer.score(draft_package)
        issues = self.grounding.validate(draft_package.model_copy(update={"quality": quality}))
        payload = dict(draft_package.package_payload)
        payload["grounding_issues"] = issues
        return draft_package.model_copy(update={"quality": quality, "package_payload": payload})
