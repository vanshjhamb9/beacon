export type Opportunity = {
  id: string;
  company_id: string;
  company_name: string;
  status: string;
  recommendation: string;
  opportunity_score: number;
  confidence_score: number;
  timing_score: number;
  urgency_score: number;
  narrative: string;
  created_from_context_ids: string[];
  score_breakdown: Record<string, unknown>;
  delta: {
    direction?: string;
    previous_score?: number | null;
    current_score?: number;
    score_change?: number;
    reason?: string;
    [key: string]: unknown;
  };
  created_at: string;
};

export type RevenueBuyerPersona = {
  persona: string;
  confidence: number;
  explanation: string;
};

export type RevenuePlaybook = {
  business_pain: string;
  recommended_service: string;
  why: string;
  conversation_angle: string;
  decision_maker: string;
  expected_outcome: string;
  risk: string;
};

export type RevenueOpportunity = {
  company: { id: string; name: string; industry?: string | null };
  opportunity_id: string;
  solution_match_id: string;
  opportunity_score: number;
  business_pain: string | null;
  recommended_service: string;
  secondary_service: string | null;
  buyer_persona: RevenueBuyerPersona | null;
  buyer_personas: RevenueBuyerPersona[];
  estimated_budget_range: string | null;
  project_size: string | null;
  implementation_complexity: string | null;
  priority: string | null;
  confidence: number;
  evidence: Record<string, unknown>;
  reason: string;
  playbook: RevenuePlaybook | null;
  created_at: string;
};

export type Company = {
  id: string;
  name: string;
  normalized_name: string;
  primary_domain: string | null;
  industry: string | null;
  last_seen_at: string | null;
  signal_frequency: number;
  memory_summary: string | null;
  attributes: Record<string, unknown>;
};

export type CompanyDNA = {
  id: string;
  company_id: string;
  industry: string | null;
  business_model: string;
  company_stage: string;
  growth_pattern: string;
  technology_stack: string[];
  digital_maturity: number;
  ai_adoption: number;
  automation_adoption: number;
  hiring_pattern: string;
  expansion_pattern: string;
  innovation_score: number;
  support_maturity: number;
  operational_maturity: number;
  technology_maturity: number;
  customer_maturity: number;
  completeness_score: number;
  evidence: Record<string, unknown>;
  created_at: string;
};

export type BusinessContext = {
  id: string;
  company_id: string;
  classified_signal_id: string;
  raw_event_id: string;
  quality_report_id: string;
  business_urgency: string;
  buying_stage: string;
  decision_stage: string;
  growth_stage: string;
  digital_maturity: number;
  ai_readiness: number;
  automation_readiness: number;
  budget_probability: number;
  technology_maturity: number;
  expansion_probability: number;
  operational_pressure: number;
  customer_experience_pressure: number;
  support_pressure: number;
  engineering_pressure: number;
  marketing_pressure: number;
  sales_pressure: number;
  confidence: number;
  evidence: Record<string, unknown>;
  created_at: string;
};

export type ContextInference = {
  id: string;
  company_id: string;
  business_context_id: string;
  category: string;
  value: string;
  confidence: number;
  evidence: Record<string, unknown>;
  created_at: string;
};

export type ContextEvidence = {
  id: string;
  business_context_id: string;
  evidence_type: string;
  reference_id: string | null;
  reference_key: string | null;
  confidence: number;
  details: Record<string, unknown>;
  created_at: string;
};

export type TimelineEvent = {
  id?: string;
  timestamp: string;
  event_id?: string;
  source?: string;
  signal_type: string;
  summary: string;
  confidence: number;
  evidence?: Record<string, unknown>;
};

export type OpportunityEvidence = {
  id: string;
  opportunity_id: string;
  company_id: string;
  source_type: string;
  reference_id: string;
  category: string;
  summary: string;
  confidence: number;
  polarity: string;
  weight: number;
  details: Record<string, unknown>;
  created_at: string;
};

export type OpportunityHistory = {
  id: string;
  opportunity_id: string | null;
  company_id: string;
  action: string;
  actor: string;
  details: Record<string, unknown>;
  created_at: string;
};

export type SourceHealth = {
  source: string;
  status: string;
  last_success_at: string | null;
  last_failure_at: string | null;
  last_checked_at: string | null;
  last_error: string | null;
  consecutive_failures: number;
  average_latency_ms: number | null;
};

export type QualityReport = {
  id: string;
  raw_event_id: string;
  source: string;
  decision: string;
  grade: string;
  schema_score: number;
  spam_score: number;
  trust_score: number;
  freshness_score: number;
  completeness_score: number;
  entity_confidence_score: number;
  duplicate_probability: number;
  overall_quality_score: number;
  processing_time_ms: number;
  queue_time_ms: number | null;
  reason_codes: string[];
  explanation: Record<string, unknown>;
  created_at: string;
  metrics?: Array<{
    id: string;
    stage: string;
    metric_name: string;
    metric_value: number;
    passed: boolean;
    duration_ms: number;
    reason_codes: string[];
    details: Record<string, unknown>;
  }>;
};

export type HealthResponse = {
  status: string;
  environment: string;
  dependencies: Record<string, { status: string; latency_ms?: number }>;
};

export type SalesReadyLeadProfile = {
  company_id: string;
  opportunity_id: string;
  company_name: string;
  opportunity_score: number;
  business_pain: string;
  recommended_service: string;
  buyer_persona: string;
  company_profile: {
    company_name: string;
    website?: string | null;
    domain?: string | null;
    industry?: string | null;
    sub_industry?: string | null;
    description?: string | null;
    location?: string | null;
    country?: string | null;
    founded_year?: number | null;
    employee_count_estimate?: number | null;
    company_size_range?: string | null;
    revenue_estimate?: string | null;
    attributions?: Array<Record<string, unknown>>;
  };
  technology_stack: Array<{
    name: string;
    category: string;
    confidence: number;
    source: string;
    source_url?: string | null;
    signal?: string | null;
  }>;
  decision_makers: Array<{
    name: string;
    role: string;
    department?: string | null;
    linkedin_url?: string | null;
    work_email?: string | null;
    business_phone?: string | null;
    confidence: number;
    source: string;
  }>;
  public_contact_information: Array<{
    kind: string;
    value: string;
    label?: string | null;
    confidence: number;
    source: string;
    is_public?: boolean;
  }>;
  team_insights: {
    leadership_team_size?: number | null;
    engineering_team_estimate?: number | null;
    support_team_estimate?: number | null;
    operations_team_estimate?: number | null;
    recent_hires: string[];
    open_positions: string[];
    hiring_trends?: string | null;
  };
  social_profiles: Array<{
    platform: string;
    url: string;
    handle?: string | null;
    confidence: number;
    source: string;
  }>;
  open_jobs?: Array<{
    title: string;
    department?: string | null;
    location?: string | null;
    url?: string | null;
    confidence: number;
    source: string;
  }>;
  estimated_budget?: string | null;
  priority?: string | null;
  why_now: string;
  best_outreach_angle: string;
  evidence_chain: Array<{
    category: string;
    summary: string;
    source: string;
    confidence: number;
    source_url?: string | null;
  }>;
  source_attribution: Array<{
    source: string;
    fields: string[];
    confidence: number;
    licensed: boolean;
    notes?: string;
    source_url?: string | null;
  }>;
  enrichment_confidence: {
    profile_completeness: number;
    contact_availability: number;
    technology_confidence: number;
    decision_maker_confidence: number;
    overall_enrichment_confidence: number;
  };
  enrichment_report_id?: string | null;
  created_at?: string | null;
};

export type VerificationCompany = {
  company_id: string;
  opportunity_id: string;
  enrichment_report_id: string;
  company_name: string;
  overall_readiness: number;
  overall_data_quality: number;
  freshness_score: number;
  freshness_status: string;
  trust_score: number;
  coverage_percent: number;
  verification_percent: number;
  decision: string;
  completeness: {
    overall_completeness: number;
    company_profile_completeness: number;
    contact_completeness: number;
    leadership_completeness: number;
    technology_completeness: number;
    revenue_completeness: number;
    hiring_completeness: number;
    social_profile_completeness: number;
    evidence_completeness: number;
    timeline_completeness: number;
  };
  readiness_checklist: {
    company_profile: boolean;
    technology: boolean;
    leadership: boolean;
    public_business_email: boolean;
    public_phone: boolean;
    hiring: boolean;
    funding: boolean;
    timeline: boolean;
  };
  missing_fields: string[];
  automatic_actions: string[];
  reason_codes: string[];
  verification_report_id?: string | null;
  created_at?: string | null;
};
