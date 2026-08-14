"""Tests for TechnologyFilter."""

from __future__ import annotations

from discovery_quality_engine.technology_filter import TechnologyFilter, TechnologyFilterResult
from discovery_quality_engine.quality_engine import QualityDecision, QualityGate, RejectionReason


class TestTechnologyFilter:
    def setup_method(self) -> None:
        self.filter = TechnologyFilter()

    def test_ai_model_rejected(self) -> None:
        result = self.filter.evaluate(description="We build an AI model for natural language")
        assert result.decision == QualityDecision.REJECT
        assert "AI_COMPANY" in result.reasons

    def test_llm_rejected(self) -> None:
        result = self.filter.evaluate(description="Our LLM platform powers enterprise")
        assert result.decision == QualityDecision.REJECT

    def test_ai_startup_rejected(self) -> None:
        result = self.filter.evaluate(description="We are an AI startup from YC")
        assert result.decision == QualityDecision.REJECT

    def test_open_source_ai_rejected(self) -> None:
        result = self.filter.evaluate(description="Open source AI framework for developers")
        assert result.decision == QualityDecision.REJECT

    def test_ai_developer_tools_rejected(self) -> None:
        result = self.filter.evaluate(description="AI developer tools for MLOps")
        assert result.decision == QualityDecision.REJECT

    def test_ai_infrastructure_rejected(self) -> None:
        result = self.filter.evaluate(description="AI infrastructure for model hosting")
        assert result.decision == QualityDecision.REJECT

    def test_llm_sdk_rejected(self) -> None:
        result = self.filter.evaluate(description="LLM SDK for building applications")
        assert result.decision == QualityDecision.REJECT

    def test_model_hosting_rejected(self) -> None:
        result = self.filter.evaluate(description="Model hosting platform for inference")
        assert result.decision == QualityDecision.REJECT

    def test_prompt_engineering_rejected(self) -> None:
        result = self.filter.evaluate(description="Prompt engineering tools for LLMs")
        assert result.decision == QualityDecision.REJECT

    def test_inference_platform_rejected(self) -> None:
        result = self.filter.evaluate(description="Inference platform for AI models")
        assert result.decision == QualityDecision.REJECT

    def test_ai_framework_rejected(self) -> None:
        result = self.filter.evaluate(description="AI framework for deep learning")
        assert result.decision == QualityDecision.REJECT

    def test_machine_learning_rejected(self) -> None:
        result = self.filter.evaluate(description="Machine learning platform")
        assert result.decision == QualityDecision.REJECT

    def test_deep_learning_rejected(self) -> None:
        result = self.filter.evaluate(description="Deep learning solutions")
        assert result.decision == QualityDecision.REJECT

    def test_generative_ai_rejected(self) -> None:
        result = self.filter.evaluate(description="Generative AI for content creation")
        assert result.decision == QualityDecision.REJECT

    def test_foundation_model_rejected(self) -> None:
        result = self.filter.evaluate(description="Foundation model for enterprise")
        assert result.decision == QualityDecision.REJECT

    def test_normal_company_accepted(self) -> None:
        result = self.filter.evaluate(description="We provide cloud-based CRM software")
        assert result.decision == QualityDecision.ACCEPT

    def test_ecommerce_accepted(self) -> None:
        result = self.filter.evaluate(description="E-commerce platform for retailers")
        assert result.decision == QualityDecision.ACCEPT

    def test_fintech_accepted(self) -> None:
        result = self.filter.evaluate(description="Digital payments for businesses")
        assert result.decision == QualityDecision.ACCEPT

    def test_no_description_accepted(self) -> None:
        result = self.filter.evaluate()
        assert result.decision == QualityDecision.ACCEPT

    def test_disabled_filter(self) -> None:
        filter = TechnologyFilter(enabled=False)
        result = filter.evaluate(description="AI model company")
        assert result.decision == QualityDecision.ACCEPT

    def test_tags_checked(self) -> None:
        result = self.filter.evaluate(tags=["ai", "llm", "machine learning"])
        assert result.decision == QualityDecision.REJECT

    def test_industry_checked(self) -> None:
        result = self.filter.evaluate(industry="ai infrastructure")
        assert result.decision == QualityDecision.REJECT

    def test_company_name_checked(self) -> None:
        result = self.filter.evaluate(company_name="AI Innovations Inc")
        assert result.decision == QualityDecision.ACCEPT

    def test_company_name_ai_model(self) -> None:
        result = self.filter.evaluate(company_name="AI Model Labs")
        assert result.decision == QualityDecision.REJECT

    def test_gate_name(self) -> None:
        assert self.filter.gate_name() == QualityGate.AI_COMPANY_FILTER.value

    def test_matched_keywords_populated(self) -> None:
        result = self.filter.evaluate(description="AI model and LLM platform")
        assert len(result.matched_keywords) > 0

    def test_custom_keywords(self) -> None:
        filter = TechnologyFilter(ai_keywords=["blockchain", "web3"])
        result = filter.evaluate(description="We build blockchain solutions")
        assert result.decision == QualityDecision.REJECT

    def test_case_insensitive(self) -> None:
        result = self.filter.evaluate(description="AI MODEL company")
        assert result.decision == QualityDecision.REJECT

    def test_gpu_cloud_rejected(self) -> None:
        result = self.filter.evaluate(description="GPU cloud for AI training")
        assert result.decision == QualityDecision.REJECT

    def test_ai_as_a_service_rejected(self) -> None:
        result = self.filter.evaluate(description="AI as a service for enterprise")
        assert result.decision == QualityDecision.REJECT

    def test_mlops_rejected(self) -> None:
        result = self.filter.evaluate(description="MLOps platform for model deployment")
        assert result.decision == QualityDecision.REJECT

    def test_nlp_rejected(self) -> None:
        result = self.filter.evaluate(description="NLP platform for text analysis")
        assert result.decision == QualityDecision.REJECT

    def test_computer_vision_rejected(self) -> None:
        result = self.filter.evaluate(description="Computer vision platform for images")
        assert result.decision == QualityDecision.REJECT

    def test_transformer_rejected(self) -> None:
        result = self.filter.evaluate(description="Transformer model for NLP tasks")
        assert result.decision == QualityDecision.REJECT

    def test_neural_network_rejected(self) -> None:
        result = self.filter.evaluate(description="Neural network solutions for enterprise")
        assert result.decision == QualityDecision.REJECT

    def test_ai_chip_rejected(self) -> None:
        result = self.filter.evaluate(description="AI chip for edge computing")
        assert result.decision == QualityDecision.REJECT

    def test_language_model_rejected(self) -> None:
        result = self.filter.evaluate(description="Language model for chatbots")
        assert result.decision == QualityDecision.REJECT
