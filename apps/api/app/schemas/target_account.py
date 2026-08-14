from typing import Any

from pydantic import BaseModel, Field


class TargetAccountResponse(BaseModel):
    id: str
    company_id: str
    opportunity_id: str | None = None
    company_name: str
    industry: str | None = None
    country: str | None = None
    matched_icp_key: str | None = None
    matched_icp_name: str | None = None
    service_match: str | None = None
    fit_score: float
    intent_score: float
    budget_score: float
    budget_band: str | None = None
    urgency_score: float
    accessibility_score: float
    competition_score: float
    revenue_opportunity_score: float
    tier: str
    why_now: str
    buying_signals: list[Any] = Field(default_factory=list)
    negative_signals: list[Any] = Field(default_factory=list)
    score_breakdown: list[Any] = Field(default_factory=list)
    evidence_chain: list[Any] = Field(default_factory=list)
    explanations: dict[str, Any] = Field(default_factory=dict)
    hunter_triggered: bool = False
    hunter_tasks: list[Any] = Field(default_factory=list)
    proceed_to_copilot: bool = False
    scoring_version: str
    created_at: str | None = None


class TargetAccountListResponse(BaseModel):
    targets: list[TargetAccountResponse]
    total: int


class ICPProfileBody(BaseModel):
    key: str
    name: str
    service_match: str
    priority: int = 100
    company_size_min: int | None = None
    company_size_max: int | None = None
    employee_count_min: int | None = None
    employee_count_max: int | None = None
    industries: list[str] = Field(default_factory=list)
    revenue_bands: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    funding_stages: list[str] = Field(default_factory=list)
    hiring_signals: list[str] = Field(default_factory=list)
    technology_stack: list[str] = Field(default_factory=list)
    business_models: list[str] = Field(default_factory=list)
    growth_signals: list[str] = Field(default_factory=list)
    decision_makers: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    buying_signals: list[str] = Field(default_factory=list)
    negative_signals: list[str] = Field(default_factory=list)
    headquarters_cities: list[str] = Field(default_factory=list)
    specialties: list[str] = Field(default_factory=list)
    company_types: list[str] = Field(default_factory=list)
    year_founded_min: int | None = None
    year_founded_max: int | None = None
    linkedin_url_required: bool = False
    company_name_contains: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    lists: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ICPProfileUpdateBody(BaseModel):
    name: str | None = None
    service_match: str | None = None
    priority: int | None = None
    company_size_min: int | None = None
    company_size_max: int | None = None
    employee_count_min: int | None = None
    employee_count_max: int | None = None
    industries: list[str] | None = None
    revenue_bands: list[str] | None = None
    countries: list[str] | None = None
    funding_stages: list[str] | None = None
    hiring_signals: list[str] | None = None
    technology_stack: list[str] | None = None
    business_models: list[str] | None = None
    growth_signals: list[str] | None = None
    decision_makers: list[str] | None = None
    pain_points: list[str] | None = None
    buying_signals: list[str] | None = None
    negative_signals: list[str] | None = None
    headquarters_cities: list[str] | None = None
    specialties: list[str] | None = None
    company_types: list[str] | None = None
    year_founded_min: int | None = None
    year_founded_max: int | None = None
    linkedin_url_required: bool | None = None
    company_name_contains: list[str] | None = None
    domains: list[str] | None = None
    lists: list[str] | None = None
    metadata: dict[str, Any] | None = None


class ICPProfileResponse(BaseModel):
    id: str
    key: str
    name: str
    service_match: str
    priority: int
    company_size_min: int | None = None
    company_size_max: int | None = None
    employee_count_min: int | None = None
    employee_count_max: int | None = None
    industries: list[Any] = Field(default_factory=list)
    revenue_bands: list[Any] = Field(default_factory=list)
    countries: list[Any] = Field(default_factory=list)
    funding_stages: list[Any] = Field(default_factory=list)
    hiring_signals: list[Any] = Field(default_factory=list)
    technology_stack: list[Any] = Field(default_factory=list)
    business_models: list[Any] = Field(default_factory=list)
    growth_signals: list[Any] = Field(default_factory=list)
    decision_makers: list[Any] = Field(default_factory=list)
    pain_points: list[Any] = Field(default_factory=list)
    buying_signals: list[Any] = Field(default_factory=list)
    negative_signals: list[Any] = Field(default_factory=list)
    is_active: bool = True
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    # Flattened from metadata_json for Lead Engine UI
    headquarters_cities: list[Any] = Field(default_factory=list)
    specialties: list[Any] = Field(default_factory=list)
    company_types: list[Any] = Field(default_factory=list)
    year_founded_min: int | None = None
    year_founded_max: int | None = None
    linkedin_url_required: bool = False
    company_name_contains: list[Any] = Field(default_factory=list)
    domains: list[Any] = Field(default_factory=list)
    lists: list[Any] = Field(default_factory=list)


class HunterStartBody(BaseModel):
    company_id: str


class HunterStatusResponse(BaseModel):
    status: str
    job_id: str | None = None
    company_id: str | None = None
    tasks: list[Any] = Field(default_factory=list)
    completed_tasks: list[Any] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)
    started_at: str | None = None
    completed_at: str | None = None
    jobs: int | None = None
