import { API_BASE_URL, apiDelete, apiGet, apiPost, apiPut } from "@/lib/api/client";
import type {
  BusinessContext,
  Company,
  CompanyDNA,
  ContextEvidence,
  ContextInference,
  HealthResponse,
  Opportunity,
  OpportunityEvidence,
  OpportunityHistory,
  QualityReport,
  RevenueOpportunity,
  RevenuePlaybook,
  SalesReadyLeadProfile,
  SourceHealth,
  TimelineEvent,
  VerificationCompany,
} from "@/lib/types/api";

export type OperationsCenterStage = {
  stage: string;
  current: number;
  today: number;
  yesterday: number;
  hour: number;
  trend_7d: number[];
  delta_pct: number | null;
};

export type OperationsCenterConnector = {
  connector: string;
  enabled: boolean;
  healthy: boolean;
  status: string;
  last_run: string | null;
  last_success: string | null;
  last_failure: string | null;
  success_rate: number;
  error_count: number;
  records_today: number;
  records_total: number;
  avg_runtime: number;
  rate_limited: boolean;
  detail: string;
};

export type OperationsCenterWorker = {
  worker_name: string;
  running: boolean;
  queue_size: number;
  jobs_completed: number;
  jobs_failed: number;
  avg_duration: number;
  last_execution: string | null;
  status: string;
};

export type OperationsCenterFeedItem = {
  timestamp: string;
  kind: string;
  message: string;
  collector: string | null;
  company: string | null;
  status: string | null;
  count: number | null;
};

export type OperationsCenterLive = {
  generated_at: string;
  cards: Record<
    string,
    { current?: number; today?: number; yesterday?: number; delta_pct?: number | null; trend_7d?: number[]; value?: number }
  >;
  pipeline: OperationsCenterStage[];
  conversions: Array<{
    from_stage: string;
    to_stage: string;
    from_count: number;
    to_count: number;
    conversion_pct: number;
    drop_pct: number;
  }>;
  connectors: OperationsCenterConnector[];
  workers: OperationsCenterWorker[];
  queues: Array<{ name: string; pending: number }>;
  failures: Array<{ reason: string; count: number }>;
  feed: OperationsCenterFeedItem[];
  timeline: Array<{
    hour: string;
    collected: number;
    verified: number;
    emails: number;
    decision_makers: number;
    sales_ready: number;
    revenue_ready: number;
  }>;
  progress: {
    started_revenue_ready: number;
    current_revenue_ready: number;
    difference: number;
  };
  revenue: { pipeline: number; projected: number; meetings: number; won: number };
  source_map: Array<{
    connector: string;
    signals: number;
    verified: number;
    emails: number;
    decision_makers: number;
    revenue_ready: number;
  }>;
  health: {
    collecting: boolean;
    pipeline_healthy: boolean;
    connectors_healthy: number;
    connectors_total: number;
    workers_running: number;
    workers_total: number;
    biggest_bottleneck: string | null;
    tone: string;
    summary: string;
  };
  scoring_version: string;
};

export type CampaignRecord = {
  id: string;
  company_id: string;
  opportunity_id: string;
  sales_package_id?: string | null;
  company_name: string;
  status: string;
  priority: string;
  primary_channel: string;
  secondary_channel?: string | null;
  follow_up_count: number;
  delay_hours_between_messages: number[];
  expected_confidence: number;
  channel_choice_reason: string;
  timing_reason: string;
  message_selection_reason: string;
  recommended_service: string;
  business_pain: string;
  buyer_persona?: string | null;
  industry?: string | null;
  communication_style: string;
  timezone: string;
  evidence: Array<Record<string, unknown>>;
  quality: Record<string, unknown>;
  steps?: Array<{
    id: string;
    sequence: number;
    kind: string;
    channel: string;
    delay_hours: number;
    draft_kind: string;
    draft_style: string;
    subject_preview: string;
    body_preview: string;
    message_selection_reason: string;
    timing_reason: string;
    confidence: number;
    status: string;
    evidence: Array<Record<string, unknown>>;
  }>;
  schedules?: Array<{
    id: string;
    campaign_id: string;
    campaign_step_id?: string | null;
    planned_at: string;
    timezone: string;
    status: string;
    timing_reason: string;
  }>;
  approvals?: Array<{
    id: string;
    action: string;
    from_status: string;
    to_status: string;
    actor: string;
    notes: string;
    created_at: string;
  }>;
  created_at: string;
};

export type SalesCopilotPackage = {
  id: string;
  company_id: string;
  opportunity_id: string;
  company_name: string;
  opportunity_score: number;
  recommended_service: string;
  business_pain: string;
  version: number;
  review_status: string;
  is_favorite: boolean;
  sections: Array<{
    key: string;
    title: string;
    content: string;
    attribution: Record<string, unknown>;
  }>;
  style_variants: Array<{
    style: string;
    drafts: Array<{
      id?: string;
      kind: string;
      style: string;
      title: string;
      body: string;
      subject_lines?: string[];
      attribution: Record<string, unknown>;
    }>;
  }>;
  drafts: Array<{
    id?: string;
    kind: string;
    style: string;
    title: string;
    body: string;
    subject_lines?: string[];
    attribution: Record<string, unknown>;
  }>;
  evidence_chain: Array<Record<string, unknown>>;
  quality: {
    personalization: number;
    evidence_coverage: number;
    readability: number;
    professional_tone: number;
    length: number;
    call_to_action: number;
    confidence: number;
    overall: number;
  };
  generation: {
    prompt_version: string;
    llm_provider: string;
    llm_model: string;
    temperature: number;
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
    latency_ms: number;
    generation_time_ms: number;
    cost_estimate_usd: number;
  };
  package_payload: Record<string, unknown>;
  created_at: string;
};

export const beaconApi = {
  health: () => apiGet<HealthResponse>("/health"),
  version: () => apiGet<{ name: string; version: string; environment: string }>("/version"),

  opportunities: (params?: { status?: string; limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    query.set("limit", String(params?.limit ?? 100));
    query.set("offset", String(params?.offset ?? 0));
    return apiGet<{ opportunities: Opportunity[] }>(`/opportunities?${query}`);
  },
  opportunity: (id: string) => apiGet<Opportunity>(`/opportunities/${id}`),
  opportunityStatistics: () =>
    apiGet<{ statistics: Record<string, number | string> }>("/opportunities/statistics"),
  opportunityEvidence: (id: string) =>
    apiGet<{ evidence: OpportunityEvidence[] }>(`/opportunities/${id}/evidence`),
  opportunityHistory: (id: string) =>
    apiGet<{ history: OpportunityHistory[] }>(`/opportunities/${id}/history`),
  opportunityTimeline: (id: string) =>
    apiGet<{ timeline: Array<{ event_type: string; summary: string; details: Record<string, unknown>; created_at: string }> }>(
      `/opportunities/${id}/timeline`,
    ),
  opportunityRecommendation: (id: string) =>
    apiGet<{
      id: string;
      action: string;
      confidence: number;
      reasons: string[];
      next_step: string;
      created_at: string;
    }>(`/opportunities/${id}/recommendation`),
  opportunityFeedback: (body: {
    opportunity_id: string;
    reviewer: string;
    review_outcome: string;
    corrected_fields?: Record<string, unknown>;
    outcome_label?: string | null;
    notes?: string | null;
  }) => apiPost("/opportunities/feedback", body),

  revenueOpportunities: (params?: { priority?: string; limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.priority) query.set("priority", params.priority);
    query.set("limit", String(params?.limit ?? 100));
    query.set("offset", String(params?.offset ?? 0));
    return apiGet<{ opportunities: RevenueOpportunity[] }>(`/revenue/opportunities?${query}`);
  },
  revenueStatistics: () =>
    apiGet<{ statistics: Record<string, number | string> }>("/revenue/statistics"),
  revenueCompany: (companyId: string) =>
    apiGet<RevenueOpportunity>(`/revenue/company/${companyId}`),
  revenuePlaybook: (companyId: string) =>
    apiGet<RevenuePlaybook & { company_id: string; opportunity_id: string; solution_match_id: string; created_at: string }>(
      `/revenue/company/${companyId}/playbook`,
    ),

  enrichmentCompany: (companyId: string) =>
    apiGet<SalesReadyLeadProfile>(`/enrichment/company/${companyId}`),
  enrichmentOpportunity: (opportunityId: string) =>
    apiGet<SalesReadyLeadProfile>(`/enrichment/opportunity/${opportunityId}`),
  enrichmentRefresh: (entityId: string) =>
    apiPost<{ refreshed: boolean; profile: SalesReadyLeadProfile }>(`/enrichment/refresh/${entityId}`, {}),
  enrichmentCsvStart: (body: { csv_data: string; limit?: number }) =>
    apiPost<{
      job_id: string;
      total: number;
      warnings: string[];
      status: string;
    }>("/enrichment/csv/start", body),
  enrichmentCsvStatus: (jobId: string) =>
    apiGet<{
      job_id: string;
      status: string;
      total: number;
      processed: number;
      summary: Record<string, number | string> | null;
      error: string | null;
      current_company: string | null;
      elapsed_seconds: number | null;
    }>(`/enrichment/csv/status/${jobId}`),
  enrichmentCsvDownloadUrl: (jobId: string) =>
    `${API_BASE_URL}/enrichment/csv/download/${jobId}`,

  acquisitionDashboard: () =>
    apiGet<{
      overall_coverage_score: number;
      active_connectors: number;
      healthy_connectors: number;
      degraded_connectors: number;
      down_connectors: number;
      signals_24h: number;
      companies_24h: number;
      opportunities_24h: number;
      high_value_opportunities_24h: number;
      average_duplicate_rate: number;
      average_failure_rate: number;
      open_alerts: number;
      connectors: Array<{
        source: string;
        enabled: boolean;
        health_status: string;
        consecutive_failures: number;
        signals_collected_24h: number;
        companies_discovered_24h: number;
        opportunities_produced_24h: number;
        high_value_opportunities_24h: number;
        duplicate_rate_24h: number;
        failure_rate_24h: number;
        coverage_score: number;
        extraction_quality_avg: number;
      }>;
      leaderboard: Array<{
        source: string;
        quality_score: number;
        opportunity_yield: number;
        high_value_yield: number;
        company_discovery_rate: number;
        duplicate_rate: number;
        failure_rate: number;
        average_latency_ms: number;
        rank: number;
        explanation: string;
      }>;
      latest_daily_report: Record<string, unknown> | null;
    }>("/acquisition/dashboard"),
  acquisitionAlerts: () =>
    apiGet<{
      alerts: Array<{
        id: string;
        source: string;
        severity: string;
        code: string;
        message: string;
        consecutive_failures: number;
        created_at: string;
      }>;
    }>("/acquisition/alerts"),
  acquisitionDailyReport: () =>
    apiGet<{
      report: {
        summary: string;
        new_companies: number;
        new_opportunities: number;
        coverage_growth: number;
        duplicate_rate: number;
        missing_data_trends: Record<string, number>;
      };
    }>("/acquisition/reports/daily"),

  decisionCompany: (companyId: string) =>
    apiGet<{
      id: string;
      company_id: string;
      opportunity_id: string;
      company_name: string;
      opportunity_score: number;
      business_pain: string;
      recommended_service: string;
      primary_decision_maker: {
        id: string;
        name: string;
        role: string;
        department?: string | null;
        work_email?: string | null;
        business_phone?: string | null;
        linkedin_url?: string | null;
        confidence: number;
        buyer_match_score: number;
        evidence: string;
        source: string;
      } | null;
      secondary_decision_maker: {
        id: string;
        name: string;
        role: string;
        department?: string | null;
        confidence: number;
        buyer_match_score: number;
        evidence: string;
      } | null;
      decision_makers: Array<Record<string, unknown>>;
      departments: Array<{ name: string; signal_strength: number; evidence: string }>;
      leadership: Array<{ name: string; title: string; department?: string | null; confidence: number }>;
      contact_channels: Array<{
        kind: string;
        value: string;
        label?: string | null;
        rank: number;
        confidence: number;
        evidence: string;
      }>;
      public_emails: string[];
      public_phones: string[];
      public_profiles: Array<{ platform: string; url: string; handle?: string | null }>;
      best_outreach_sequence: Array<Record<string, unknown>>;
      no_public_contact_message?: string | null;
      buyer_match_confidence: number;
      reason: string;
      evidence_chain: Array<Record<string, unknown>>;
      confidence: {
        leadership_confidence: number;
        department_confidence: number;
        contact_confidence: number;
        buyer_match_confidence: number;
        overall_discovery_score: number;
      };
      created_at: string;
    }>(`/decision/company/${companyId}`),
  decisionRefresh: (entityId: string) =>
    apiPost<{ refreshed: boolean; report: Record<string, unknown> | null }>(`/decision/refresh/${entityId}`, {}),

  copilotCompany: (companyId: string) => apiGet<SalesCopilotPackage>(`/copilot/company/${companyId}`),
  copilotOpportunity: (opportunityId: string) =>
    apiGet<SalesCopilotPackage>(`/copilot/opportunity/${opportunityId}`),
  copilotGenerate: (entityId: string) =>
    apiPost<{ generated: boolean; package: SalesCopilotPackage | null }>(`/copilot/generate/${entityId}`, {}),
  copilotRegenerate: (entityId: string) =>
    apiPost<{ generated: boolean; package: SalesCopilotPackage | null }>(`/copilot/regenerate/${entityId}`, {}),
  copilotReview: (
    packageId: string,
    body: { action: string; reviewer?: string; notes?: string; rating?: number | null },
  ) => apiPost<{ reviewed: boolean; package: SalesCopilotPackage | null }>(`/copilot/review/${packageId}`, body),
  copilotHistory: (entityId: string) =>
    apiGet<{
      results: Array<{
        id: string;
        company_id: string;
        opportunity_id: string;
        version: number;
        review_status: string;
        is_favorite: boolean;
        prompt_version: string;
        llm_provider: string;
        llm_model: string;
        quality_overall: number;
        created_at: string;
      }>;
    }>(`/copilot/history/${entityId}`),

  campaigns: (params?: { limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    query.set("limit", String(params?.limit ?? 100));
    query.set("offset", String(params?.offset ?? 0));
    return apiGet<{ campaigns: CampaignRecord[] }>(`/campaigns?${query}`);
  },
  campaign: (id: string) => apiGet<CampaignRecord>(`/campaigns/${id}`),
  campaignsDashboard: () =>
    apiGet<{
      total_campaigns: number;
      needs_review: number;
      approved_or_scheduled: number;
      paused: number;
      cancelled: number;
      completed: number;
      average_confidence: number;
      by_status: Record<string, number>;
      by_priority: Record<string, number>;
      by_primary_channel: Record<string, number>;
      delivery_enabled: boolean;
      pending_approvals: Array<{
        id: string;
        company_id: string;
        company_name: string;
        priority: string;
        primary_channel: string;
        expected_confidence: number;
        status: string;
      }>;
      upcoming_schedules: Array<{
        id: string;
        campaign_id: string;
        company_id: string;
        planned_at: string;
        timezone: string;
        status: string;
        timing_reason: string;
      }>;
    }>("/campaigns/dashboard"),
  campaignCreate: (companyId: string) =>
    apiPost<{ created: boolean; detail?: string | null; campaign: CampaignRecord | null }>(
      `/campaigns/create/${companyId}`,
      {},
    ),
  campaignApprove: (id: string, body?: { actor?: string; notes?: string }) =>
    apiPost<{ updated: boolean; detail?: string | null; campaign: CampaignRecord | null }>(
      `/campaigns/approve/${id}`,
      body ?? {},
    ),
  campaignReject: (id: string, body?: { actor?: string; notes?: string }) =>
    apiPost<{ updated: boolean; detail?: string | null; campaign: CampaignRecord | null }>(
      `/campaigns/reject/${id}`,
      body ?? {},
    ),
  campaignBulkApprove: (campaignIds: string[], actor = "founder", notes = "bulk_approve") =>
    apiPost<{ updated: number; failed: number; results: unknown[] }>("/campaigns/bulk-approve", {
      campaign_ids: campaignIds,
      actor,
      notes,
    }),
  campaignBulkReject: (campaignIds: string[], actor = "founder", notes = "bulk_reject") =>
    apiPost<{ updated: number; failed: number; results: unknown[] }>("/campaigns/bulk-reject", {
      campaign_ids: campaignIds,
      actor,
      notes,
    }),
  campaignPause: (id: string, body?: { actor?: string; notes?: string }) =>
    apiPost<{ updated: boolean; detail?: string | null; campaign: CampaignRecord | null }>(
      `/campaigns/pause/${id}`,
      body ?? {},
    ),
  campaignCancel: (id: string, body?: { actor?: string; notes?: string }) =>
    apiPost<{ updated: boolean; detail?: string | null; campaign: CampaignRecord | null }>(
      `/campaigns/cancel/${id}`,
      body ?? {},
    ),

  verificationCompany: (companyId: string) =>
    apiGet<VerificationCompany>(`/verification/company/${companyId}`),
  verificationDashboard: () =>
    apiGet<{
      overall_data_quality: number;
      coverage_percent: number;
      verification_percent: number;
      freshness_percent: number;
      average_profile_completeness: number;
      top_missing_fields: string[];
      profiles_needing_refresh: number;
      flagged_for_review: number;
      total_verified_profiles: number;
    }>("/verification/dashboard"),
  verificationRefresh: (entityId: string) =>
    apiPost<{ refreshed: boolean; profile: VerificationCompany }>(`/verification/refresh/${entityId}`, {}),

  companies: (params?: { limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    query.set("limit", String(params?.limit ?? 100));
    query.set("offset", String(params?.offset ?? 0));
    return apiGet<{ companies: Company[] }>(`/companies?${query}`);
  },
  company: (id: string) => apiGet<Company>(`/companies/${id}`),
  companyTimeline: (id: string, limit = 100) =>
    apiGet<{ timeline: TimelineEvent[] }>(`/companies/${id}/timeline?limit=${limit}`),
  companySignals: (id: string, limit = 100) =>
    apiGet<{ signals: Array<Record<string, unknown>> }>(`/companies/${id}/signals?limit=${limit}`),

  contextCompany: (id: string, limit = 20) =>
    apiGet<{ contexts: BusinessContext[] }>(`/context/company/${id}?limit=${limit}`),
  contextDna: (id: string) => apiGet<CompanyDNA>(`/context/company/${id}/dna`),
  contextPains: (id: string, limit = 50) =>
    apiGet<{ items: ContextInference[] }>(`/context/company/${id}/pains?limit=${limit}`),
  contextGoals: (id: string, limit = 50) =>
    apiGet<{ items: ContextInference[] }>(`/context/company/${id}/goals?limit=${limit}`),
  contextEvidence: (id: string, limit = 100) =>
    apiGet<{ evidence: ContextEvidence[] }>(`/context/company/${id}/evidence?limit=${limit}`),
  contextStatistics: () =>
    apiGet<{ statistics: Record<string, unknown> }>("/context/statistics"),

  qualityDashboard: () => apiGet<{ dashboard: Record<string, unknown> }>("/quality/dashboard"),
  qualityStatistics: () =>
    apiGet<{ statistics: Record<string, unknown> }>("/quality/statistics"),
  qualityEvents: (params?: { decision?: string; limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.decision) query.set("decision", params.decision);
    query.set("limit", String(params?.limit ?? 50));
    query.set("offset", String(params?.offset ?? 0));
    return apiGet<{ events: QualityReport[] }>(`/quality/events?${query}`);
  },
  qualitySources: () => apiGet<{ sources: Array<Record<string, unknown>> }>("/quality/sources"),
  qualityRules: () => apiGet<{ rules: Array<Record<string, unknown>> }>("/quality/rules"),
  qualityReport: (reportId: string) =>
    apiGet<QualityReport>(`/quality/report?report_id=${reportId}`),

  sourcesHealth: () => apiGet<{ sources: SourceHealth[] }>("/sources/health"),

  diagnostics: () =>
    apiGet<{
      generated_at: string;
      collectors: Array<{
        source: string;
        enabled: boolean;
        health_status: string;
        consecutive_failures: number;
        average_latency_ms: number | null;
        last_success_at: string | null;
        last_failure_at: string | null;
        last_error: string | null;
        last_run_at: string | null;
        last_run_success: boolean | null;
        last_collected: number | null;
        last_emitted: number | null;
        signals_24h: number;
      }>;
      queues: Array<{ name: string; length: number; detail?: string | null }>;
      database: Record<string, number>;
      funnel: Array<{
        stage: string;
        entering: number;
        leaving: number;
        drop_off_percent: number;
        notes?: string | null;
      }>;
      worker: {
        redis_reachable: boolean;
        celery_queue_length: number;
        raw_event_stream_length: number;
        scheduler_status: string;
        worker_status: string;
        detail?: string | null;
      };
      last_successful_collection: string | null;
      last_processed_opportunity: string | null;
      last_error: string | null;
      top_failing_connectors: string[];
      missing_env: string[];
      quality_reason_breakdown: Record<string, number>;
      average_quality_processing_ms: number | null;
      extras: Record<string, unknown>;
    }>("/diagnostics"),

  operations: () =>
    apiGet<{
      generated_at: string;
      scoring_version: string;
      infrastructure: Array<{
        name: string;
        status: string;
        detail?: string | null;
        metrics?: Record<string, unknown>;
        evidence?: string[];
      }>;
      redis: {
        ok: boolean;
        version?: string | null;
        streams_ok?: boolean;
        errors?: string[];
        latency_ms?: number | null;
      };
      migrations: {
        ok: boolean;
        current_revision?: string | null;
        head_revision: string;
        pending_revisions: string[];
        missing_tables: string[];
      };
      celery: {
        worker_online: boolean;
        beat_online: boolean;
        broker_ok: boolean;
        active_tasks: number;
        scheduled_tasks: number;
        registered_task_count: number;
        queue_depth: number;
        worker_memory_mb?: number | null;
        last_heartbeat_at?: string | null;
      };
      pipeline: Array<{
        stage: string;
        input_count: number;
        output_count: number;
        dropped_count: number;
        success_percent: number;
        worker_task?: string | null;
        status: string;
      }>;
      collectors: Array<Record<string, unknown>>;
      enrichment: Record<string, number>;
      freshness: Record<string, string | null>;
      alerts: Array<{
        code: string;
        severity: string;
        cause: string;
        evidence: string[];
        recommended_fix: string;
      }>;
      production_gate: {
        allow_production: boolean;
        score: number;
        blockers: string[];
        warnings: string[];
      };
      readiness_score: number;
    }>("/operations"),

  operationsReports: () =>
    apiGet<{ generated_at: string; reports: Record<string, string> }>("/operations/reports"),

  oduDashboard: () => apiGet<Record<string, unknown>>("/operations/odu/dashboard"),
  oduConnectors: () => apiGet<Record<string, unknown>>("/operations/odu/connectors"),
  oduHealth: () => apiGet<Record<string, unknown>>("/operations/odu/health"),
  oduRecovery: (limit = 50) =>
    apiGet<{ items: Array<Record<string, unknown>>; count: number }>(`/operations/odu/recovery?limit=${limit}`),
  oduReport: () => apiGet<Record<string, unknown>>("/operations/odu/report"),
  oduUnlock: () => apiPost<Record<string, unknown>>("/operations/odu/unlock", {}),

  operationsCenterLive: () => apiGet<OperationsCenterLive>("/operations/live"),
  operationsCenterConnectors: () =>
    apiGet<{ generated_at: string; connectors: OperationsCenterLive["connectors"] }>(
      "/operations/connectors",
    ),
  operationsCenterWorkers: () =>
    apiGet<{ generated_at: string; workers: OperationsCenterLive["workers"] }>("/operations/workers"),
  operationsCenterPipeline: () =>
    apiGet<Record<string, unknown>>("/operations/pipeline"),
  operationsCenterFeed: (limit = 40) =>
    apiGet<{ generated_at: string; items: OperationsCenterLive["feed"] }>(
      `/operations/feed?limit=${limit}`,
    ),
  operationsCenterQueues: () =>
    apiGet<{ generated_at: string; queues: OperationsCenterLive["queues"] }>("/operations/queues"),
  operationsCenterHealth: () =>
    apiGet<{ generated_at: string; health: OperationsCenterLive["health"] }>("/operations/health"),
  operationsCenterDaily: () => apiGet<Record<string, unknown>>("/operations/daily"),

  explorerSearch: (q = "", limit = 25) =>
    apiGet<{
      query: string;
      count: number;
      items: Array<{
        company_id?: string;
        company?: string;
        domain?: string | null;
        email?: string | null;
        founder?: string | null;
        lead_id?: string;
        revenue_ready_id?: string | null;
        revenue_ready?: boolean;
        current_stage?: string;
        score?: number;
        source?: string | null;
      }>;
      scoring_version?: string;
    }>(`/explorer/search?q=${encodeURIComponent(q)}&limit=${limit}`),
  explorerCompany: (companyId: string) =>
    apiGet<{
      summary?: Record<string, unknown>;
      timeline?: Array<{
        id: string;
        event_type: string;
        label: string;
        headline: string;
        detail: string;
        stage?: string | null;
        status?: string | null;
        connector?: string | null;
        provider?: string | null;
        occurred_at?: string;
      }>;
      providers?: Array<{
        provider: string;
        label: string;
        status: string;
        latency_ms?: number | null;
        fields_added?: string[];
        credits_used?: number | null;
        success?: boolean | null;
        confidence?: number | null;
      }>;
      enrichments?: Record<string, unknown>;
      evidence?: Array<{
        id?: string;
        kind: string;
        label: string;
        url?: string | null;
        provider?: string | null;
        snippet?: string;
      }>;
      score?: {
        total?: number;
        explained_total?: number;
        components?: Array<{
          key: string;
          label: string;
          points: number;
          present: boolean;
          evidence?: string[];
        }>;
        source?: string;
      };
      fields?: Array<{
        id?: string;
        field_name: string;
        field_value?: string | null;
        provider: string;
        confidence: number;
        occurred_at?: string | null;
      }>;
      stages?: Array<{
        stage: string;
        label: string;
        status: string;
        reason?: string;
        duration_seconds?: number | null;
      }>;
      stage_durations?: Array<{
        stage: string;
        label: string;
        duration_seconds?: number | null;
        status?: string;
      }>;
      failure?: {
        status?: string;
        rejected_stage?: string;
        reasons?: string[];
        detail?: string;
      } | null;
      promotion?: {
        promoted?: boolean;
        reason?: string;
        passed?: string[];
        missing?: string[];
      };
      replay?: Array<{
        index: number;
        at?: string;
        focus?: { id?: string; label?: string; detail?: string };
        events_so_far?: unknown[];
      }>;
      scoring_version?: string;
      error?: string;
    }>(`/explorer/company/${companyId}`),
  explorerTimeline: (companyId: string) =>
    apiGet<Record<string, unknown>>(`/explorer/timeline?company_id=${companyId}`),
  explorerEvidence: (companyId: string) =>
    apiGet<Record<string, unknown>>(`/explorer/evidence?company_id=${companyId}`),
  explorerProviders: (companyId?: string) =>
    apiGet<Record<string, unknown>>(
      companyId ? `/explorer/providers?company_id=${companyId}` : "/explorer/providers",
    ),
  explorerScore: (companyId: string) =>
    apiGet<Record<string, unknown>>(`/explorer/score?company_id=${companyId}`),
  explorerHistory: (companyId: string) =>
    apiGet<Record<string, unknown>>(`/explorer/history?company_id=${companyId}`),
  explorerReplay: (companyId: string) =>
    apiGet<Record<string, unknown>>(`/explorer/replay?company_id=${companyId}`),
  explorerContribution: () =>
    apiGet<{
      items: Array<{
        provider: string;
        label: string;
        companies_affected: number;
        emails_added: number;
        dm_added: number;
        revenue_ready_created: number;
        success_pct: number;
      }>;
      providers?: Array<{ provider: string; label: string; status: string }>;
    }>("/explorer/contribution"),
  explorerSync: () => apiPost<Record<string, unknown>>("/explorer/sync", {}),

  discoveriesLive: (params?: {
    limit?: number;
    collector?: string;
    industry?: string;
    status?: string;
    connector?: string;
    company?: string;
    revenue_ready_only?: boolean;
    errors_only?: boolean;
  }) => {
    const qs = new URLSearchParams();
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.collector) qs.set("collector", params.collector);
    if (params?.industry) qs.set("industry", params.industry);
    if (params?.status) qs.set("status", params.status);
    if (params?.connector) qs.set("connector", params.connector);
    if (params?.company) qs.set("company", params.company);
    if (params?.revenue_ready_only) qs.set("revenue_ready_only", "true");
    if (params?.errors_only) qs.set("errors_only", "true");
    const suffix = qs.toString() ? `?${qs}` : "";
    return apiGet<{
      generated_at: string;
      items: Array<{
        id: string;
        event_type: string;
        timestamp: string;
        collector: string | null;
        connector: string | null;
        company_id: string | null;
        company_name: string | null;
        industry: string | null;
        status: string | null;
        headline: string;
        detail: string;
        score: number | null;
        is_error: boolean;
        is_revenue_ready: boolean;
      }>;
      count: number;
      facets: {
        collectors: string[];
        industries: string[];
        connectors: string[];
        statuses: string[];
      };
    }>(`/discoveries/live${suffix}`);
  },

  discoveriesCompany: (companyId: string) =>
    apiGet<{ items: Array<Record<string, unknown>>; count: number }>(
      `/discoveries/company/${companyId}`,
    ),

  connectorsRoi: () =>
    apiGet<{
      generated_at: string;
      report_date: string;
      connectors: Array<{
        connector: string;
        healthy: boolean;
        signals: number;
        companies: number;
        emails: number;
        decision_makers: number;
        revenue_ready: number;
        meetings: number;
        wins: number;
        win_pct: number;
        latency_ms: number;
        api_cost: number;
        quota_used_pct: number;
        success_pct: number;
        detail?: string;
      }>;
      enrichment_coverage: Array<Record<string, unknown>>;
    }>("/connectors/roi"),

  datasetStatistics: (days = 30) =>
    apiGet<{
      generated_at: string;
      current: Record<string, number>;
      today: Record<string, number>;
      yesterday: Record<string, number>;
      trends: Array<Record<string, number | string>>;
      heatmap: Array<{
        stage: string;
        tone: string;
        count: number;
        success_pct: number;
        avg_duration: number;
        failures: number;
      }>;
    }>(`/dataset/statistics?days=${days}`),

  companyJourney: (companyId: string) =>
    apiGet<{
      company_id: string;
      company_name: string;
      industry: string | null;
      current_stage: string;
      stages: Array<{
        stage: string;
        label: string;
        status: string;
        started_at: string | null;
        completed_at: string | null;
        duration_seconds: number | null;
        connector: string | null;
        worker: string | null;
        evidence: string[];
        retry_count: number;
        failures: string[];
        detail: string;
      }>;
      pipeline_health: Array<Record<string, unknown>>;
      events: Array<Record<string, unknown>>;
    }>(`/company/${companyId}/journey`),

  pipelineReplay: () =>
    apiGet<{
      generated_at: string;
      frames: Array<{
        hour: string;
        timestamp: string;
        signals: number;
        companies: number;
        websites: number;
        emails: number;
        decision_makers: number;
        sales_ready: number;
        revenue_ready: number;
        contacted: number;
        movements: Array<Record<string, unknown>>;
      }>;
    }>("/pipeline/replay"),

  analyticsV2: () => apiGet<Record<string, unknown>>("/analytics/v2"),

  intelligenceSearch: (q: string, limit = 40) =>
    apiGet<{
      query: string;
      companies: Array<{ id: string; name: string; domain: string | null; industry: string | null }>;
      events: Array<Record<string, unknown>>;
      journeys: Array<Record<string, unknown>>;
    }>(`/intelligence/search?q=${encodeURIComponent(q)}&limit=${limit}`),

  intelligenceSync: () => apiPost<Record<string, unknown>>("/intelligence/sync", {}),

  fswLeads: (limit = 200) =>
    apiGet<{
      items: Array<Record<string, unknown>>;
      total: number;
      stage_counts: Record<string, number>;
    }>(`/fsw/leads?limit=${limit}`),

  fswCreateLead: (data: Record<string, unknown>) =>
    apiPost<Record<string, unknown>>("/fsw/leads", data),

  leadDiscovery: () =>
    apiPost<{ status: string; result: Record<string, unknown> }>("/leads/discover", {}),

  leadSeed: () =>
    apiPost<{ status: string; result: Record<string, unknown> }>("/leads/seed", {}),

  leadStats: () =>
    apiGet<{ total: number; comai: number; inowix: number; cyber: number; by_stage: Record<string, number> }>("/leads/stats"),

  companyUniverse: (limit = 100) =>
    apiGet<{
      items: Array<Record<string, unknown>>;
      total: number;
    }>(`/company-universe?limit=${limit}`),

  intelligenceAnalysis: () =>
    apiGet<{ analysis: Record<string, unknown>; recommendations: Array<Record<string, unknown>>; scoring: Record<string, unknown> }>("/intelligence-loop/analysis"),

  intelligenceRecommendations: () =>
    apiGet<{ recommendations: Array<Record<string, unknown>>; total: number }>("/intelligence-loop/recommendations"),

  improvementOverview: () =>
    apiGet<{ overview: Record<string, unknown> }>("/improvement/overview"),
  improvementCollectors: () =>
    apiGet<{ collectors: Array<Record<string, unknown>> }>("/improvement/collectors"),
  improvementRules: () =>
    apiGet<{ rules: Array<Record<string, unknown>> }>("/improvement/rules"),
  improvementOpportunities: () =>
    apiGet<{ opportunities: Array<Record<string, unknown>> }>("/improvement/opportunities"),
  improvementExperiments: () =>
    apiGet<{ experiments: Array<Record<string, unknown>> }>("/improvement/experiments"),
  improvementRecommendations: () =>
    apiGet<{ recommendations: Array<Record<string, unknown>> }>("/improvement/recommendations"),

  outcomesDashboard: () =>
    apiGet<{
      generated_at: string;
      funnel: Array<{ stage: string; count: number; conversion_from_previous: number }>;
      rates: {
        meeting_rate: number;
        reply_rate: number;
        proposal_rate: number;
        close_rate: number;
        contacted_count: number;
        replied_count: number;
        meeting_count: number;
        proposal_count: number;
        won_count: number;
        lost_count: number;
        total_opportunities: number;
      };
      revenue: {
        total_revenue: number;
        average_deal_size: number;
        average_sales_cycle_days: number;
        open_pipeline_value: number;
        won_deals: number;
      };
      revenue_by_collector: Array<{
        dimension: string;
        key: string;
        revenue: number;
        deals: number;
        average_deal_size: number;
        win_rate: number;
      }>;
      revenue_by_industry: Array<{
        dimension: string;
        key: string;
        revenue: number;
        deals: number;
        average_deal_size: number;
        win_rate: number;
      }>;
      revenue_by_service: Array<{
        dimension: string;
        key: string;
        revenue: number;
        deals: number;
        average_deal_size: number;
        win_rate: number;
      }>;
      revenue_by_persona: Array<{
        dimension: string;
        key: string;
        revenue: number;
        deals: number;
        average_deal_size: number;
        win_rate: number;
      }>;
      revenue_by_technology: Array<{
        dimension: string;
        key: string;
        revenue: number;
        deals: number;
        average_deal_size: number;
        win_rate: number;
      }>;
      prediction_accuracy: Array<{
        category: string;
        key: string;
        sample_size: number;
        accuracy_score: number;
        precision: number;
        recall: number;
        average_prediction_error: number;
      }>;
      service_accuracy: Array<{
        category: string;
        key: string;
        sample_size: number;
        accuracy_score: number;
        precision: number;
        recall: number;
        average_prediction_error: number;
      }>;
      collector_accuracy: Array<{
        category: string;
        key: string;
        sample_size: number;
        accuracy_score: number;
        precision: number;
        recall: number;
        average_prediction_error: number;
      }>;
      persona_accuracy: Array<{
        category: string;
        key: string;
        sample_size: number;
        accuracy_score: number;
        precision: number;
        recall: number;
        average_prediction_error: number;
      }>;
      industry_accuracy: Array<{
        category: string;
        key: string;
        sample_size: number;
        accuracy_score: number;
        precision: number;
        recall: number;
        average_prediction_error: number;
      }>;
      roi: Record<string, number>;
      learning_recommendations: Array<{
        area: string;
        target_key: string;
        recommendation: string;
        reason: string;
        expected_impact: number;
        confidence: number;
        requires_approval: boolean;
      }>;
    }>("/outcomes/dashboard"),
  outcomesAnalytics: () =>
    apiGet<{
      generated_at: string;
      rates: Record<string, number>;
      revenue: Record<string, number>;
      funnel: Array<{ stage: string; count: number; conversion_from_previous: number }>;
      accuracy_summary: Record<string, number>;
      top_services: Array<Record<string, unknown>>;
      top_collectors: Array<Record<string, unknown>>;
      top_industries: Array<Record<string, unknown>>;
      learning_recommendations: Array<Record<string, unknown>>;
    }>("/outcomes/analytics"),
  outcomesCompany: (companyId: string) =>
    apiGet<{
      company_id: string;
      company_name: string;
      outcomes: Array<Record<string, unknown>>;
      contact_attempts: Array<Record<string, unknown>>;
      meetings: Array<Record<string, unknown>>;
      proposals: Array<Record<string, unknown>>;
      deals: Array<Record<string, unknown>>;
      feedback: Array<Record<string, unknown>>;
      totals: Record<string, number>;
    }>(`/outcomes/company/${companyId}`),
  outcomesUpdate: (body: {
    opportunity_id: string;
    company_id?: string;
    lifecycle_stage: string;
    notes?: string | null;
    reason?: string | null;
    owner?: string | null;
    revenue?: number | null;
    deal_value?: number | null;
    actor?: string;
  }) => apiPost<Record<string, unknown>>("/outcomes/update", body),

  communicationMode: () =>
    apiGet<{
      mode: string;
      allow_production_send: boolean;
      sandbox: boolean;
      queues: Record<string, unknown>;
    }>("/communication/mode"),
  communicationQueues: () =>
    apiGet<{
      mode: string;
      allow_production_send: boolean;
      sandbox: boolean;
      depths: Record<string, number>;
      stopped_campaigns: number;
    }>("/communication/queues"),
  communicationSandboxSend: (body: {
    channel?: string;
    to_address?: string;
    subject?: string;
    body_text?: string;
    simulated_reply?: string;
    campaign_id?: string;
    company_id?: string;
    opportunity_id?: string;
  }) => apiPost<Record<string, unknown>>("/communication/sandbox/send", body),
  communicationFounderSend: (body: {
    channel?: string;
    to_address: string;
    subject?: string;
    body_text: string;
    body_html?: string;
    campaign_id?: string;
    campaign_step_id?: string;
    company_id?: string;
    opportunity_id?: string;
    simulate_reply?: boolean;
    force_sandbox?: boolean;
    actor?: string;
  }) => apiPost<Record<string, unknown>>("/communication/send", body),
  communicationExecuteCampaign: (
    campaignId: string,
    body: {
      to_address: string;
      subject?: string;
      body_text?: string;
      channel?: string;
      company_id?: string;
      opportunity_id?: string;
      simulate_reply?: boolean;
      force_sandbox?: boolean;
      actor?: string;
    },
  ) => apiPost<Record<string, unknown>>(`/communication/campaigns/${campaignId}/execute`, body),
  communicationOauthStatus: (provider = "gmail") =>
    apiGet<{
      connected: boolean;
      provider: string;
      account_email?: string | null;
      expires_at?: string | null;
      history_id?: string | null;
      status?: string;
    }>(`/communication/oauth/status?provider=${provider}`),
  communicationSyncGmailReplies: () => apiPost<Record<string, unknown>>("/communication/sync/gmail-replies", {}),
  communicationE2EApproveSendReply: (body?: Record<string, unknown>) =>
    apiPost<Record<string, unknown>>("/communication/e2e/approve-send-reply", body ?? {}),
  communicationSandboxMeeting: (body: {
    title?: string;
    description?: string;
    campaign_id?: string;
    company_id?: string;
    opportunity_id?: string;
    attendees?: string[];
  }) => apiPost<Record<string, unknown>>("/communication/sandbox/meeting", body),
  communicationStopCampaign: (campaignId: string, body?: { reason?: string; actor?: string }) =>
    apiPost<Record<string, unknown>>(`/communication/campaigns/${campaignId}/stop`, body ?? {}),
  inbox: (limit = 50) =>
    apiGet<
      Array<{
        id: string;
        company_id: string;
        subject: string;
        unread_count: number;
        pinned: boolean;
        channels: string[];
        ai_summary?: string | null;
        last_activity_at?: string | null;
      }>
    >(`/inbox?limit=${limit}`),
  inboxConversation: (conversationId: string) =>
    apiGet<
      Array<{
        id: string;
        channel: string;
        item_type: string;
        direction: string;
        subject?: string | null;
        body: string;
        from_address?: string | null;
        to_address?: string | null;
        unread: boolean;
        occurred_at: string;
      }>
    >(`/inbox/${conversationId}`),
  systemHealth: () =>
    apiGet<{
      overall_score: number;
      status: string;
      mode: string;
      components: Array<{
        name: string;
        status: string;
        score: number;
        latency_ms?: number | null;
        details?: Record<string, unknown>;
      }>;
      recommendations: string[];
    }>("/system-health"),
  qaHealth: () =>
    apiGet<{
      overall_score: number;
      status: string;
      mode: string;
      components: Array<Record<string, unknown>>;
      recommendations: string[];
    }>("/qa/health"),
  qaE2ESandbox: () =>
    apiPost<{
      scenario: string;
      passed: boolean;
      mode: string;
      steps: Array<{ name: string; passed: boolean; detail: string; duration_ms: number }>;
    }>("/qa/e2e/sandbox", {}),

  targets: (params?: { tier?: string; icp_key?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.tier) q.set("tier", params.tier);
    if (params?.icp_key) q.set("icp_key", params.icp_key);
    q.set("limit", String(params?.limit ?? 100));
    return apiGet<{ targets: TargetAccountRecord[]; total: number }>(`/targets?${q.toString()}`);
  },
  target: (id: string) => apiGet<TargetAccountRecord>(`/targets/${id}`),
  targetsDashboard: () =>
    apiGet<{
      total: number;
      tiers: Record<string, number>;
      industries: Record<string, number>;
      countries: Record<string, number>;
      avg_revenue_score: number;
      hunter_triggered: number;
      top_services: Record<string, number>;
      pipeline_ready: number;
      heat: Array<{
        company_id: string;
        company_name: string;
        score: number;
        tier: string;
        icp?: string | null;
      }>;
    }>("/targets/dashboard"),
  icps: () => apiGet<ICPProfileRecord[]>("/icp"),
  createIcp: (body: Record<string, unknown>) => apiPost<ICPProfileRecord>("/icp", body),
  updateIcp: (id: string, body: Record<string, unknown>) => apiPut<ICPProfileRecord>(`/icp/${id}`, body),
  deleteIcp: (id: string) => apiDelete<{ deleted: boolean }>(`/icp/${id}`),
  hunterStart: (companyId: string) => apiPost<Record<string, unknown>>("/hunter/start", { company_id: companyId }),
  hunterStatus: (companyId?: string) =>
    apiGet<{
      status: string;
      job_id?: string | null;
      company_id?: string | null;
      tasks: string[];
      completed_tasks: string[];
      result: Record<string, unknown>;
    }>(companyId ? `/hunter/status?company_id=${companyId}` : "/hunter/status"),

  leadEnginePresets: () =>
    apiGet<{ presets: Record<string, Record<string, unknown>> }>("/lead-engine/presets"),
  leadEngineStart: (body: { product: string; limit: number; icp: Record<string, unknown> }) =>
    apiPost<LeadEngineRun>("/lead-engine/runs", body),
  leadEngineRuns: (limit = 20) => apiGet<{ runs: LeadEngineRun[] }>(`/lead-engine/runs?limit=${limit}`),
  leadEngineRun: (runId: string) => apiGet<LeadEngineRun>(`/lead-engine/runs/${runId}`),
  leadEngineLeads: (runId: string, minScore = 0) =>
    apiGet<{ run_id: string; count: number; leads: LeadEngineLead[] }>(
      `/lead-engine/runs/${runId}/leads?min_score=${minScore}`,
    ),
  leadEngineEnrich: (runId: string, leadIds: string[]) =>
    apiPost<LeadEngineRun>(`/lead-engine/runs/${runId}/enrich`, { lead_ids: leadIds }),
  leadEngineDrafts: (runId: string, leadIds?: string[]) =>
    apiPost<{
      run_id: string;
      count: number;
      drafts: Array<{ lead_id: string; company?: string; email?: string; subject: string; body: string }>;
    }>(`/lead-engine/runs/${runId}/drafts`, { lead_ids: leadIds ?? null }),
  leadEngineSend: (runId: string, leadIds: string[], dryRun = false) =>
    apiPost<{
      run_id: string;
      sent: number;
      attempted: number;
      results: Array<{ lead_id: string; to_email?: string; subject?: string; success: boolean; error?: string }>;
      cc: string[];
    }>(`/lead-engine/runs/${runId}/send`, { lead_ids: leadIds, dry_run: dryRun }),
  leadEngineExportUrl: (runId: string) => `/api/v1/lead-engine/runs/${runId}/export`,
  leadEngineAutoStatus: () =>
    apiGet<{
      enabled: boolean;
      interval_sec: number;
      product: string;
      limit: number;
      last_run_id?: string | null;
      last_started_at?: number | null;
      last_error?: string | null;
      runs_completed: number;
      pool_count: number;
      pool_ready: number;
    }>("/lead-engine/auto"),
  leadEngineAutoStart: (body: {
    product: string;
    limit: number;
    interval_sec?: number;
    icp: Record<string, unknown>;
  }) => apiPost<Record<string, unknown>>("/lead-engine/auto/start", body),
  leadEngineAutoStop: () => apiPost<Record<string, unknown>>("/lead-engine/auto/stop", {}),
  leadEnginePool: (limit = 100) =>
    apiGet<{ count: number; leads: LeadEngineLead[] }>(`/lead-engine/pool?limit=${limit}`),
  leadEnginePoolLoad: (limit = 40) =>
    apiPost<LeadEngineRun>(`/lead-engine/pool/load?limit=${limit}`, {}),

  /** Unified Sales Workspace — Lead Engine backed Home/Leads/Pipeline/Outreach/Analytics */
  workspaceOverview: () => apiGet<Record<string, unknown>>("/workspace/overview"),
  workspaceLeads: (params?: { limit?: number; search?: string; status?: string }) => {
    const q = new URLSearchParams();
    q.set("limit", String(params?.limit ?? 300));
    if (params?.search) q.set("search", params.search);
    if (params?.status && params.status !== "all") q.set("status", params.status);
    return apiGet<{
      items: Array<Record<string, unknown>>;
      total: number;
      stage_counts: Record<string, number>;
      filter_counts?: Record<string, number>;
      source?: string;
    }>(`/workspace/leads?${q.toString()}`);
  },
  workspaceLead: (id: string) => apiGet<Record<string, unknown>>(`/workspace/leads/${id}`),
  workspaceSetStage: (id: string, stage: string) =>
    apiPost<{ ok: boolean; lead: Record<string, unknown> }>(`/workspace/leads/${id}/stage`, { stage }),
  workspaceDraftLead: (id: string) =>
    apiPost<{
      ok: boolean;
      lead_id: string;
      subject: string;
      body: string;
      hook_used?: string;
      lead: Record<string, unknown>;
    }>(`/workspace/leads/${id}/draft`, {}),
  workspaceSendLead: (
    id: string,
    body?: { dry_run?: boolean; subject?: string; body?: string },
  ) =>
    apiPost<{
      ok: boolean;
      dry_run?: boolean;
      to_email?: string;
      subject?: string;
      body?: string;
      lead?: Record<string, unknown>;
    }>(`/workspace/leads/${id}/send`, body || {}),
  workspaceSync: () => apiPost<Record<string, unknown>>("/workspace/sync", {}),
  workspaceOutreach: (limit = 100) =>
    apiGet<{
      campaigns: Array<Record<string, unknown>>;
      total: number;
      pending: number;
      sent: number;
      delivered: number;
      replied: number;
      bounced: number;
      dashboard: Record<string, unknown>;
    }>(`/workspace/outreach?limit=${limit}`),
  workspaceApproveOutreach: (id: string) =>
    apiPost<Record<string, unknown>>(`/workspace/outreach/${id}/approve`, {}),
  workspaceRejectOutreach: (id: string) =>
    apiPost<Record<string, unknown>>(`/workspace/outreach/${id}/reject`, {}),
  workspaceAnalytics: () => apiGet<Record<string, unknown>>("/workspace/analytics"),
  workspaceActivity: (limit = 30) =>
    apiGet<{ feed: Array<Record<string, unknown>>; count: number }>(`/workspace/activity?limit=${limit}`),

  revenueHunterTaxonomy: () =>
    apiGet<{
      countries: string[];
      company_sizes: string[];
      industries: string[];
      funding_stages: string[];
      revenue_bands: string[];
      services: string[];
    }>("/revenue-hunter/taxonomy"),
  revenueHunterDossiers: (params?: { grade?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.grade) q.set("grade", params.grade);
    q.set("limit", String(params?.limit ?? 100));
    return apiGet<{ dossiers: RevenueHunterDossierRecord[]; total: number }>(
      `/revenue-hunter/dossiers?${q.toString()}`,
    );
  },
  revenueHunterDossier: (id: string) => apiGet<RevenueHunterDossierRecord>(`/revenue-hunter/dossiers/${id}`),
  revenueHunterDashboard: () =>
    apiGet<{
      todays_targets: Array<Record<string, unknown>>;
      top_25_companies: Array<Record<string, unknown>>;
      expected_revenue: number;
      expected_pipeline: number;
      meetings_today: number;
      campaign_queue: number;
      reply_queue: number;
      follow_ups: number;
      hot_opportunities: number;
      generated_at?: string | null;
    }>("/revenue-hunter/dashboard"),
  revenueHunterWorkQueue: (params?: { status?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.status) q.set("status", params.status);
    q.set("limit", String(params?.limit ?? 50));
    return apiGet<{ items: RevenueHunterWorkQueueItem[]; total: number }>(
      `/revenue-hunter/work-queue?${q.toString()}`,
    );
  },
  revenueHunterWorkAction: (id: string, action: string, actor = "founder") =>
    apiPost<RevenueHunterWorkQueueItem>(`/revenue-hunter/work-queue/${id}/action`, { action, actor }),

  founderOsCommandCenter: () => apiGet<FounderOsPack>("/founder-os/command-center"),
  founderOsRefresh: () => apiPost<FounderOsPack>("/founder-os/refresh", {}),
  founderOsBrief: () => apiGet<Record<string, unknown>>("/founder-os/brief"),
  founderOsAssistant: () => apiGet<Record<string, unknown>>("/founder-os/assistant"),
  founderOsTasks: (status = "open") =>
    apiGet<{ tasks: Array<Record<string, unknown>>; total: number }>(`/founder-os/tasks?status=${status}`),
  founderOsCompleteTask: (id: string) => apiPost<Record<string, unknown>>(`/founder-os/tasks/${id}/complete`, {}),
  founderOsKpis: () => apiGet<Record<string, unknown>>("/founder-os/kpis"),
  founderOsRecommendations: () =>
    apiGet<{ recommendations: Array<Record<string, unknown>>; total: number }>("/founder-os/recommendations"),
  founderOsProposals: () =>
    apiGet<{ proposals: Array<Record<string, unknown>>; total: number }>("/founder-os/proposals"),
  founderOsMeetings: () =>
    apiGet<{ meetings: Array<Record<string, unknown>>; total: number }>("/founder-os/meetings"),
  founderOsTimeline: (companyId: string) =>
    apiGet<{ events: Array<Record<string, unknown>>; total: number }>(`/founder-os/timeline/${companyId}`),
  founderOsTrack: (body: {
    event_type: string;
    action: string;
    actor?: string;
    company_id?: string;
    entity_type?: string;
    entity_id?: string;
    payload?: Record<string, unknown>;
  }) => apiPost<{ id: string; tracked: string }>("/founder-os/analytics/track", body),

  salesIntelligenceCompany: (companyId: string) =>
    apiGet<SalesIntelligencePack>(`/sales-intelligence/company/${companyId}`),
  salesIntelligenceOpportunity: (opportunityId: string) =>
    apiGet<SalesIntelligencePack>(`/sales-intelligence/opportunity/${opportunityId}`),
  salesIntelligenceRefresh: (companyId: string) =>
    apiPost<{ refreshed: boolean; pack: SalesIntelligencePack }>(`/sales-intelligence/refresh/${companyId}`, {}),
  salesIntelligenceDashboard: () =>
    apiGet<{
      total_evaluated: number;
      hot_intent: number;
      high_close_probability: number;
      avg_intent: number;
      avg_deal_probability: number;
      top_accounts: Array<Record<string, unknown>>;
      scoring_version: string;
    }>("/sales-intelligence/dashboard"),

  liveRevenueCompany: (companyId: string) => apiGet<Record<string, unknown>>(`/live-revenue/company/${companyId}`),
  liveRevenueRefresh: (companyId: string) => apiPost<Record<string, unknown>>(`/live-revenue/refresh/${companyId}`, {}),
  liveRevenueApprovalCenter: () =>
    apiGet<{ cards: Array<Record<string, unknown>>; total: number; scoring_version: string }>(
      "/live-revenue/approval-center",
    ),
  liveRevenueProposals: () =>
    apiGet<{ proposals: Array<Record<string, unknown>>; total: number }>("/live-revenue/proposals"),
  liveRevenueDashboard: () =>
    apiGet<{
      total_runs: number;
      awaiting_approval: number;
      proposals: number;
      opens: number;
      clicks: number;
      recent_runs: Array<Record<string, unknown>>;
      scoring_version: string;
    }>("/live-revenue/dashboard"),
  liveRevenueCommandCenter: () => apiGet<Record<string, unknown>>("/live-revenue/command-center"),
  liveRevenueTrack: (body: {
    tracking_id: string;
    event_type: string;
    company_id?: string;
    campaign_id?: string;
    target_url?: string;
  }) => apiPost<{ id: string; tracked: string; event_type: string }>("/live-revenue/track", body),

  productionValidationReport: () => apiGet<Record<string, unknown>>("/production-validation/report"),
  productionValidationRefresh: () => apiPost<Record<string, unknown>>("/production-validation/refresh", {}),
  productionHealth: () =>
    apiGet<{
      overall_status?: string;
      overall_score?: number;
      components?: Array<Record<string, unknown>>;
      alerts?: Array<Record<string, unknown>>;
      scoring_version?: string;
    }>("/production-validation/health"),
  productionRevenue: () =>
    apiGet<{
      revenue?: Record<string, unknown>;
      founder_board?: Record<string, unknown>;
      campaign_funnels?: Array<Record<string, unknown>>;
      weekly_report?: Record<string, unknown>;
      scoring_version?: string;
    }>("/production-validation/revenue"),
  productionAlerts: () =>
    apiGet<{ alerts: Array<Record<string, unknown>>; total: number }>("/production-validation/alerts"),
  productionPlaybooks: () =>
    apiGet<{ playbooks: Array<Record<string, unknown>>; total: number }>("/production-validation/playbooks"),
  productionCampaignMonitoring: () =>
    apiGet<{ funnels: Array<Record<string, unknown>>; total: number }>("/production-validation/campaigns/monitoring"),
  productionLeadReadiness: (companyId: string) =>
    apiGet<Record<string, unknown>>(`/production-validation/lead-readiness/${companyId}`),

  phCompany: (companyId: string, persist = false) =>
    apiGet<Record<string, unknown>>(`/production-hardening/company/${companyId}?persist=${persist}`),
  phEvaluateCompany: (companyId: string) =>
    apiPost<Record<string, unknown>>(`/production-hardening/company/${companyId}/evaluate`, {}),
  phOpportunities: (limit = 100) =>
    apiGet<{
      opportunities: Array<Record<string, unknown>>;
      total: number;
      scoring_version: string;
    }>(`/production-hardening/opportunities?limit=${limit}`),
  phTrust: () => apiGet<Record<string, unknown>>("/production-hardening/trust"),
  phDuplicates: () =>
    apiGet<{ plans: Array<Record<string, unknown>>; total: number }>("/production-hardening/duplicates"),
  phHealthSignals: () =>
    apiGet<{ component_signals: Record<string, Record<string, number>>; scoring_version: string; hardcoded: boolean }>(
      "/production-hardening/health/signals",
    ),

  sreCompany: (companyId: string, refresh = false) =>
    apiGet<Record<string, unknown>>(`/sales-readiness/company/${companyId}?refresh=${refresh}`),
  sreEvaluate: (companyId: string) =>
    apiPost<Record<string, unknown>>(`/sales-readiness/company/${companyId}/evaluate`, {}),
  sreDashboard: () => apiGet<Record<string, unknown>>("/sales-readiness/dashboard"),
  sreSearch: (params?: { q?: string; status?: string; limit?: number }) => {
    const query = new URLSearchParams();
    if (params?.q) query.set("q", params.q);
    if (params?.status) query.set("status", params.status);
    query.set("limit", String(params?.limit ?? 50));
    return apiGet<{ results: Array<Record<string, unknown>>; total: number }>(`/sales-readiness/search?${query}`);
  },
  sreTrust: () => apiGet<Record<string, unknown>>("/sales-readiness/trust"),
  sreOutreachReady: (limit = 50) =>
    apiGet<{ results: Array<Record<string, unknown>>; total: number }>(`/sales-readiness/outreach-ready?limit=${limit}`),
  sreHighIntent: (limit = 50) =>
    apiGet<{ results: Array<Record<string, unknown>>; total: number }>(`/sales-readiness/high-intent?limit=${limit}`),
  sreEnterprise: (limit = 50) =>
    apiGet<{ results: Array<Record<string, unknown>>; total: number }>(`/sales-readiness/enterprise?limit=${limit}`),

  rdiCompany: (companyId: string, refresh = false) =>
    apiGet<Record<string, unknown>>(`/revenue-data-recovery/company/${companyId}?refresh=${refresh}`),
  rdiEvaluate: (companyId: string) =>
    apiPost<Record<string, unknown>>(`/revenue-data-recovery/company/${companyId}/evaluate`, {}),
  rdiDossier: (companyId: string) =>
    apiGet<Record<string, unknown>>(`/revenue-data-recovery/company/${companyId}/dossier`),
  rdiQueue: (params?: { stage?: string; limit?: number }) => {
    const query = new URLSearchParams();
    if (params?.stage) query.set("stage", params.stage);
    query.set("limit", String(params?.limit ?? 50));
    return apiGet<{ items: Array<Record<string, unknown>>; total: number }>(
      `/revenue-data-recovery/queue?${query}`,
    );
  },
  rdiFounderQueue: (limit = 60) =>
    apiGet<{ items: Array<Record<string, unknown>>; total: number }>(
      `/revenue-data-recovery/founder-queue?limit=${limit}`,
    ),
  rdiDashboard: () => apiGet<Record<string, unknown>>("/revenue-data-recovery/dashboard"),
  rdiQa: () => apiGet<Record<string, unknown>>("/revenue-data-recovery/qa"),

  rqpCompany: (companyId: string, refresh = false) =>
    apiGet<Record<string, unknown>>(`/revenue-quality/company/${companyId}?refresh=${refresh}`),
  rqpEvaluate: (companyId: string) =>
    apiPost<Record<string, unknown>>(`/revenue-quality/company/${companyId}/evaluate`, {}),
  rqpFounderQueue: (limit = 60) =>
    apiGet<{ items: Array<Record<string, unknown>>; total: number }>(
      `/revenue-quality/founder-queue?limit=${limit}`,
    ),
  rqpKpi: () => apiGet<Record<string, unknown>>("/revenue-quality/kpi"),
  rqpAcceptance: (params?: { manual_review_sample?: number; manual_review_accuracy?: number }) => {
    const query = new URLSearchParams();
    if (params?.manual_review_sample != null) query.set("manual_review_sample", String(params.manual_review_sample));
    if (params?.manual_review_accuracy != null)
      query.set("manual_review_accuracy", String(params.manual_review_accuracy));
    const qs = query.toString();
    return apiGet<Record<string, unknown>>(`/revenue-quality/acceptance${qs ? `?${qs}` : ""}`);
  },
  rqpDashboard: () => apiGet<Record<string, unknown>>("/revenue-quality/dashboard"),
  rqpSeedGold: () => apiPost<Record<string, unknown>>("/revenue-quality/golden-dataset/seed", {}),

  alphaCompany: (companyId: string, refresh = false) =>
    apiGet<Record<string, unknown>>(`/beacon-alpha/company/${companyId}?refresh=${refresh}`),
  alphaEvaluate: (companyId: string) =>
    apiPost<Record<string, unknown>>(`/beacon-alpha/company/${companyId}/evaluate`, {}),
  alphaFounderQueue: () =>
    apiGet<{ items: Array<Record<string, unknown>>; total: number }>("/beacon-alpha/founder-queue"),
  alphaQaPending: (limit = 40) =>
    apiGet<{ items: Array<Record<string, unknown>>; total: number }>(`/beacon-alpha/qa/pending?limit=${limit}`),
  alphaQaDecide: (companyId: string, body: { rating: string; notes?: string; reviewer?: string }) =>
    apiPost<Record<string, unknown>>(`/beacon-alpha/qa/${companyId}`, body),
  alphaQaAnalytics: () => apiGet<Record<string, unknown>>("/beacon-alpha/qa/analytics"),
  alphaAcceptance: () => apiGet<Record<string, unknown>>("/beacon-alpha/acceptance"),
  alphaDashboard: () => apiGet<Record<string, unknown>>("/beacon-alpha/dashboard"),

  gtCompany: (companyId: string, refresh = false) =>
    apiGet<Record<string, unknown>>(`/ground-truth/company/${companyId}?refresh=${refresh}`),
  gtEvaluate: (companyId: string) =>
    apiPost<Record<string, unknown>>(`/ground-truth/company/${companyId}/evaluate`, {}),
  gtFounderQueue: () =>
    apiGet<{ items: Array<Record<string, unknown>>; total: number }>("/ground-truth/founder-queue"),
  gtFunnel: () => apiGet<Record<string, unknown>>("/ground-truth/funnel"),
  gtDailyReport: () => apiGet<Record<string, unknown>>("/ground-truth/daily-report"),
  gtAcceptance: () => apiGet<Record<string, unknown>>("/ground-truth/acceptance"),
  gtDashboard: () => apiGet<Record<string, unknown>>("/ground-truth/dashboard"),

  erowdDashboard: () => apiGet<{ items: Array<Record<string, unknown>>; admitted: number; rejected: number; scoring_version?: string }>("/entity-resolution/dashboard"),
  erowdReport: () => apiGet<Record<string, unknown>>("/entity-resolution/report"),
  erowdSearch: (q: string) => apiGet<Record<string, unknown>>(`/entity-resolution/search?q=${encodeURIComponent(q)}`),
  erowdCompany: (companyId: string) => apiGet<Record<string, unknown>>(`/entity-resolution/company/${companyId}`),
  erowdEvaluate: (payload: Record<string, unknown>) => apiPost<Record<string, unknown>>("/entity-resolution/evaluate", payload),
  erowdRebuild: (limit = 1000, fetchOfficial = false) =>
    apiPost<Record<string, unknown>>(`/entity-resolution/rebuild?limit=${limit}&fetch_official=${fetchOfficial}`, {}),

  cirDashboard: () => apiGet<{ items: Array<Record<string, unknown>>; founder_queue: number; scoring_version?: string }>("/company-intelligence/dashboard"),
  cirSummary: () => apiGet<Record<string, unknown>>("/company-intelligence/summary"),
  cirSearch: (q: string) => apiGet<Record<string, unknown>>(`/company-intelligence/search?q=${encodeURIComponent(q)}`),
  cirCompany: (companyId: string) => apiGet<Record<string, unknown>>(`/company-intelligence/company/${companyId}`),
  cirOpportunities: () => apiGet<{ items: Array<Record<string, unknown>>; count: number }>("/company-intelligence/opportunities"),
  cirRebuild: (limit = 500, fetchWebsite = false) =>
    apiPost<Record<string, unknown>>(`/company-intelligence/rebuild?limit=${limit}&fetch_website=${fetchWebsite}`, {}),
  cirEvaluate: (payload: Record<string, unknown>) => apiPost<Record<string, unknown>>("/company-intelligence/evaluate", payload),

  revDashboard: () => apiGet<Record<string, unknown>>("/revenue-execution-validation/dashboard"),
  revFunnel: () => apiGet<Record<string, unknown>>("/revenue-execution-validation/funnel"),
  revRejections: () => apiGet<Record<string, unknown>>("/revenue-execution-validation/rejections"),
  revConnectors: () => apiGet<{ items: Array<Record<string, unknown>> }>("/revenue-execution-validation/connectors"),
  revFounderQueue: () => apiGet<{ items: Array<Record<string, unknown>>; count: number }>("/revenue-execution-validation/founder-queue"),
  revQaPending: () => apiGet<{ items: Array<Record<string, unknown>>; ratings: string[] }>("/revenue-execution-validation/qa/pending"),
  revQaSubmit: (payload: Record<string, unknown>) => apiPost<Record<string, unknown>>("/revenue-execution-validation/qa", payload),
  revQaAnalytics: () => apiGet<Record<string, unknown>>("/revenue-execution-validation/qa/analytics"),
  revDailyReport: () => apiGet<Record<string, unknown>>("/revenue-execution-validation/daily-report"),
  revAcceptance: () => apiGet<Record<string, unknown>>("/revenue-execution-validation/acceptance"),
  revRebuild: (limit = 500) => apiPost<Record<string, unknown>>(`/revenue-execution-validation/rebuild?limit=${limit}`, {}),
  revEvaluate: (payload: Record<string, unknown>) => apiPost<Record<string, unknown>>("/revenue-execution-validation/evaluate", payload),

  igfDashboard: () => apiGet<Record<string, unknown>>("/identity-graph/dashboard"),
  igfFunnel: () => apiGet<Record<string, unknown>>("/identity-graph/funnel"),
  igfReport: () => apiGet<Record<string, unknown>>("/identity-graph/report"),
  igfSearch: (q: string) => apiGet<{ items: Array<Record<string, unknown>>; count: number }>(`/identity-graph/search?q=${encodeURIComponent(q)}`),
  igfCompany: (companyId: string) => apiGet<Record<string, unknown>>(`/identity-graph/company/${companyId}`),
  igfEvaluate: (payload: Record<string, unknown>) => apiPost<Record<string, unknown>>("/identity-graph/evaluate", payload),
  igfRebuild: (limit = 1000, fetchOfficial = false) =>
    apiPost<Record<string, unknown>>(`/identity-graph/rebuild?limit=${limit}&fetch_official=${fetchOfficial}`, {}),

  iceDashboard: () => apiGet<Record<string, unknown>>("/identity-coverage/dashboard"),
  iceRecovery: (limit = 50) =>
    apiGet<{ items: Array<Record<string, unknown>>; count: number }>(`/identity-coverage/recovery?limit=${limit}`),
  iceCollectors: () => apiGet<{ collectors: Array<Record<string, unknown>> }>("/identity-coverage/collectors"),
  iceProviders: () => apiGet<Record<string, unknown>>("/identity-coverage/providers"),
  iceReports: () => apiGet<Record<string, unknown>>("/identity-coverage/reports"),
  iceCompany: (companyId: string) => apiGet<Record<string, unknown>>(`/identity-coverage/company/${companyId}`),
  iceRetry: (limit = 40) => apiPost<Record<string, unknown>>(`/identity-coverage/retry?limit=${limit}`, {}),
  iceExpand: (limit = 800) => apiPost<Record<string, unknown>>(`/identity-coverage/expand?limit=${limit}`, {}),

  rdapDashboard: () => apiGet<Record<string, unknown>>("/revenue-data-acquisition/dashboard"),
  rdapConnectors: () => apiGet<{ connectors: Array<Record<string, unknown>> }>("/revenue-data-acquisition/connectors"),
  rdapRecovery: (limit = 50) =>
    apiGet<{ items: Array<Record<string, unknown>>; count: number }>(`/revenue-data-acquisition/recovery?limit=${limit}`),
  rdapReports: () => apiGet<Record<string, unknown>>("/revenue-data-acquisition/reports"),
  rdapRevenueYield: () => apiGet<{ items: Array<Record<string, unknown>> }>("/revenue-data-acquisition/revenue-yield"),
  rdapCompany: (companyId: string) =>
    apiGet<Record<string, unknown>>(`/revenue-data-acquisition/company/${companyId}`),
  rdapExpand: (limit = 800) =>
    apiPost<Record<string, unknown>>(`/revenue-data-acquisition/expand?limit=${limit}`, {}),
  rdapRetry: (limit = 40) =>
    apiPost<Record<string, unknown>>(`/revenue-data-acquisition/recovery/retry?limit=${limit}`, {}),

  rrpDashboard: () => apiGet<Record<string, unknown>>("/revenue-ready/dashboard"),
  rrpFounderQueue: () =>
    apiGet<{ items: Array<Record<string, unknown>>; count: number }>("/revenue-ready/founder-queue"),
  rrpPerfect: () => apiPost<Record<string, unknown>>("/revenue-ready/perfect", {}),
  rrpReport: () => apiGet<Record<string, unknown>>("/revenue-ready/report"),
  rrpReview: (companyId: string, label: string) =>
    apiPost<Record<string, unknown>>(`/revenue-ready/company/${companyId}/review`, { label }),

  ofcSync: () => apiPost<Record<string, unknown>>("/first-customer/sync", {}),
  ofcWorkspace: () =>
    apiGet<{
      items: Array<Record<string, unknown>>;
      count: number;
      today_action: Record<string, unknown>;
    }>("/first-customer/workspace"),
  ofcRecord: (recordId: string) => apiGet<Record<string, unknown>>(`/first-customer/records/${recordId}`),
  ofcTransition: (recordId: string, status: string, note?: string) =>
    apiPost<Record<string, unknown>>(`/first-customer/records/${recordId}/transition`, { status, note }),
  ofcTimeline: (recordId: string, event_type: string, payload: Record<string, unknown> = {}) =>
    apiPost<Record<string, unknown>>(`/first-customer/records/${recordId}/timeline`, { event_type, payload }),
  ofcNote: (recordId: string, note: string) =>
    apiPost<Record<string, unknown>>(`/first-customer/records/${recordId}/notes`, { note }),
  ofcObjection: (recordId: string, label: string) =>
    apiPost<Record<string, unknown>>(`/first-customer/records/${recordId}/objections`, { label }),
  ofcRevenueDashboard: () => apiGet<Record<string, unknown>>("/first-customer/revenue-dashboard"),
  ofcLearning: () => apiGet<Record<string, unknown>>("/first-customer/learning"),
  ofcToday: () => apiGet<Record<string, unknown>>("/first-customer/today"),
  ofcReport: () => apiGet<Record<string, unknown>>("/first-customer/report"),

  clrDashboard: () => apiGet<Record<string, unknown>>("/revenue-validation/dashboard"),
  clrDailyBrief: () => apiGet<Record<string, unknown>>("/revenue-validation/daily-brief"),
  clrExecutive: () => apiGet<Record<string, unknown>>("/revenue-validation/executive"),
  clrOutcomes: () => apiGet<{ items: Array<Record<string, unknown>>; count: number }>("/revenue-validation/outcomes"),
  clrCompany: (companyId: string) => apiGet<Record<string, unknown>>(`/revenue-validation/company/${companyId}`),
  clrTransition: (companyId: string, outcome: string, notes?: string, revenue_amount?: number) =>
    apiPost<Record<string, unknown>>(`/revenue-validation/company/${companyId}/transition`, {
      outcome,
      notes,
      revenue_amount,
    }),
  clrNotes: (companyId: string, note: string) =>
    apiPost<Record<string, unknown>>(`/revenue-validation/company/${companyId}/notes`, { note }),
  clrPrediction: (companyId: string, body: Record<string, unknown>) =>
    apiPost<Record<string, unknown>>(`/revenue-validation/company/${companyId}/prediction`, body),
  clrWeeklyReview: () => apiGet<Record<string, unknown>>("/revenue-validation/weekly-review"),
  clrProductionReadiness: () => apiGet<Record<string, unknown>>("/revenue-validation/production-readiness"),
  clrReport: () => apiGet<Record<string, unknown>>("/revenue-validation/report"),
  clrSync: (seedContacted = false) =>
    apiPost<Record<string, unknown>>(`/revenue-validation/sync?seed_contacted=${seedContacted}`, {}),

  executionStatus: () => apiGet<Record<string, unknown>>("/execution/status"),
  executionReadiness: () => apiGet<Record<string, unknown>>("/execution/readiness"),
  executionValidate: () => apiPost<Record<string, unknown>>("/execution/validate", {}),
  executionDashboardCard: () => apiGet<Record<string, unknown>>("/execution/dashboard-card"),
  executionReportSection: () => apiGet<Record<string, unknown>>("/execution/report-section"),

  m1Report: () => apiGet<Record<string, unknown>>("/revenue-readiness/report"),
  m1Collection: () => apiGet<Record<string, unknown>>("/revenue-readiness/collection"),
  m1SalesAudit: () => apiGet<Record<string, unknown>>("/revenue-readiness/sales-readiness-audit"),
  m1SuccessMetrics: () => apiGet<Record<string, unknown>>("/revenue-readiness/success-metrics"),

  asaCompany: (companyId: string) => apiGet<Record<string, unknown>>(`/autonomous-sales-agent/company/${companyId}`),
  asaRefresh: (companyId: string) =>
    apiPost<Record<string, unknown>>(`/autonomous-sales-agent/refresh/${companyId}`, {}),
  asaWorkQueue: (refresh = false) =>
    apiGet<{
      items: Array<Record<string, unknown>>;
      total: number;
      scoring_version: string;
      founder_focus?: string[];
    }>(`/autonomous-sales-agent/work-queue?refresh=${refresh}`),
  asaMorningBrief: (refresh = false) =>
    apiGet<{
      priorities: string[];
      expected_meetings: Array<Record<string, unknown>>;
      expected_replies: Array<Record<string, unknown>>;
      high_risk_deals: Array<Record<string, unknown>>;
      companies_requiring_attention: Array<Record<string, unknown>>;
      revenue_forecast: number;
      follow_ups_due: Array<Record<string, unknown>>;
      scoring_version: string;
    }>(`/autonomous-sales-agent/morning-brief?refresh=${refresh}`),
  asaMorningBriefRefresh: () =>
    apiPost<{
      priorities: string[];
      expected_meetings: Array<Record<string, unknown>>;
      expected_replies: Array<Record<string, unknown>>;
      high_risk_deals: Array<Record<string, unknown>>;
      companies_requiring_attention: Array<Record<string, unknown>>;
      revenue_forecast: number;
      follow_ups_due: Array<Record<string, unknown>>;
      scoring_version: string;
    }>("/autonomous-sales-agent/morning-brief/refresh", {}),
  asaTimeline: (companyId: string) =>
    apiGet<{ events: Array<Record<string, unknown>>; total: number }>(
      `/autonomous-sales-agent/timeline/${companyId}`,
    ),
  asaDashboard: () => apiGet<Record<string, unknown>>("/autonomous-sales-agent/dashboard"),

  rocDashboard: (refresh = false) =>
    apiGet<{
      snapshot_id?: string;
      revenue_score?: number;
      pipeline_value?: number;
      expected_revenue?: number;
      control_tower?: Record<string, unknown>;
      command_center?: Record<string, unknown>;
      forecast?: Record<string, unknown>;
      founder_assistant?: Record<string, unknown>;
      operational_metrics?: Record<string, unknown>;
      alerts?: Array<Record<string, unknown>>;
      scoring_version?: string;
    }>(`/revenue-operations/dashboard?refresh=${refresh}`),
  rocRefresh: () => apiPost<Record<string, unknown>>("/revenue-operations/refresh", {}),
  rocForecast: () => apiGet<Record<string, unknown>>("/revenue-operations/forecast"),
  rocAlerts: (lifecycle?: string) =>
    apiGet<{ alerts: Array<Record<string, unknown>>; total: number }>(
      `/revenue-operations/alerts${lifecycle ? `?lifecycle=${lifecycle}` : ""}`,
    ),
  rocMemory: (q = "") =>
    apiGet<{ records: Array<Record<string, unknown>>; total: number }>(
      `/revenue-operations/memory?q=${encodeURIComponent(q)}`,
    ),
  rocReplay: (id: string) => apiGet<Record<string, unknown>>(`/revenue-operations/replay/${id}`),
  rocLearning: () =>
    apiGet<{ recommendations: Array<Record<string, unknown>>; total: number }>("/revenue-operations/learning"),
  rocMetrics: () => apiGet<Record<string, unknown>>("/revenue-operations/metrics"),

  goiCompany: (companyId: string) => apiGet<Record<string, unknown>>(`/account-journey/company/${companyId}`),
  goiRefresh: (limit = 30) => apiPost<{ refreshed: number; requested: number }>(`/account-journey/refresh?limit=${limit}`, {}),
  goiDashboard: () =>
    apiGet<{
      total_journeys: number;
      by_health: Record<string, number>;
      by_stage: Record<string, number>;
      accounts: Array<Record<string, unknown>>;
      scoring_version: string;
    }>("/account-journey/dashboard"),
  goiFollowups: () =>
    apiGet<{ plans: Array<Record<string, unknown>>; total: number; note?: string }>("/account-journey/followups"),
  goiAnalytics: () => apiGet<{ payload: Record<string, unknown>; scoring_version?: string }>("/account-journey/analytics"),
  goiReplies: () => apiGet<{ replies: Array<Record<string, unknown>>; total: number }>("/account-journey/replies"),
  goiHealth: () => apiGet<{ snapshots: Array<Record<string, unknown>>; total: number }>("/account-journey/health"),

  aepDashboard: () =>
    apiGet<{
      total_clients: number;
      by_stage: Record<string, number>;
      by_health: Record<string, number>;
      delivery: Record<string, unknown>;
      founder_view: Record<string, unknown>;
      clients: Array<Record<string, unknown>>;
      scoring_version: string;
    }>("/client-execution/dashboard"),
  aepClient: (companyId: string) => apiGet<Record<string, unknown>>(`/client-execution/client/${companyId}`),
  aepHealth: () => apiGet<{ snapshots: Array<Record<string, unknown>>; total: number }>("/client-execution/health"),
  aepHandoffs: () => apiGet<{ handoffs: Array<Record<string, unknown>>; total: number }>("/client-execution/handoff"),
  aepUpsells: () =>
    apiGet<{ recommendations: Array<Record<string, unknown>>; total: number; note?: string }>("/client-execution/upsells"),
  aepProjects: () => apiGet<{ projects: Array<Record<string, unknown>>; total: number }>("/client-execution/projects"),
  aepRefresh: (limit = 30) =>
    apiPost<{ refreshed: number; requested: number }>(`/client-execution/refresh?limit=${limit}`, {}),
  aepApproveUpsell: (recommendationId: string, approve = true) =>
    apiPost<Record<string, unknown>>(`/client-execution/upsells/${recommendationId}/approve`, {
      approve,
      actor: "founder",
    }),

  goapDashboard: () => apiGet<Record<string, unknown>>("/opportunity-acquisition/dashboard"),
  goapConnectors: () =>
    apiGet<{ connectors: Array<Record<string, unknown>>; total: number }>("/opportunity-acquisition/connectors"),
  goapConnector: (id: string) => apiGet<Record<string, unknown>>(`/opportunity-acquisition/connectors/${id}`),
  goapGraph: (companyId: string) => apiGet<Record<string, unknown>>(`/opportunity-acquisition/companies/${companyId}/graph`),
  goapWebsites: () => apiGet<{ profiles: Array<Record<string, unknown>>; total: number }>("/opportunity-acquisition/website"),
  goapTechnology: () =>
    apiGet<{ profiles: Array<Record<string, unknown>>; total: number }>("/opportunity-acquisition/technology"),
  goapFunding: () => apiGet<{ events: Array<Record<string, unknown>>; total: number }>("/opportunity-acquisition/funding"),
  goapHiring: () => apiGet<{ events: Array<Record<string, unknown>>; total: number }>("/opportunity-acquisition/hiring"),
  goapReviews: () => apiGet<{ signals: Array<Record<string, unknown>>; total: number }>("/opportunity-acquisition/reviews"),
  goapCommunity: () =>
    apiGet<{ signals: Array<Record<string, unknown>>; total: number }>("/opportunity-acquisition/community"),
  goapBenchmarks: () =>
    apiGet<{ benchmarks: Array<Record<string, unknown>>; total: number }>("/opportunity-acquisition/benchmarks"),
  goapFreshness: () => apiGet<Record<string, unknown>>("/opportunity-acquisition/freshness"),
  goapAnalytics: () => apiGet<Record<string, unknown>>("/opportunity-acquisition/analytics"),
  goapDailyReport: () => apiGet<Record<string, unknown>>("/opportunity-acquisition/daily-report"),
  goapRefresh: (limit = 40) =>
    apiPost<Record<string, unknown>>(`/opportunity-acquisition/refresh?limit=${limit}`, {}),

  aipDashboard: () => apiGet<Record<string, unknown>>("/account-intelligence/dashboard"),
  aipSearch: (params: Record<string, string> = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiGet<{ results: Array<Record<string, unknown>>; total: number }>(
      `/account-intelligence/search${qs ? `?${qs}` : ""}`,
    );
  },
  aipCompany: (companyId: string) => apiGet<Record<string, unknown>>(`/account-intelligence/company/${companyId}`),
  aipContacts: (companyId: string) => apiGet<Record<string, unknown>>(`/account-intelligence/company/${companyId}/contacts`),
  aipTechnology: (companyId: string) =>
    apiGet<Record<string, unknown>>(`/account-intelligence/company/${companyId}/technology`),
  aipWebsite: (companyId: string) => apiGet<Record<string, unknown>>(`/account-intelligence/company/${companyId}/website`),
  aipBusiness: (companyId: string) => apiGet<Record<string, unknown>>(`/account-intelligence/company/${companyId}/business`),
  aipReadiness: (companyId: string) =>
    apiGet<Record<string, unknown>>(`/account-intelligence/company/${companyId}/readiness`),
  aipRelationship: (companyId: string) =>
    apiGet<Record<string, unknown>>(`/account-intelligence/company/${companyId}/relationship`),
  aipTimeline: (companyId: string) => apiGet<Record<string, unknown>>(`/account-intelligence/company/${companyId}/timeline`),
  aipVerification: (companyId: string) =>
    apiGet<Record<string, unknown>>(`/account-intelligence/company/${companyId}/verification`),
  aipRefresh: (limit = 30) => apiPost<Record<string, unknown>>(`/account-intelligence/refresh?limit=${limit}`, {}),

  roipDashboard: () => apiGet<Record<string, unknown>>("/revenue-optimization/dashboard"),
  roipFounder: () => apiGet<Record<string, unknown>>("/revenue-optimization/founder"),
  roipIndustry: () => apiGet<{ industries: Array<Record<string, unknown>>; total: number }>("/revenue-optimization/industry"),
  roipOffers: () => apiGet<{ offers: Array<Record<string, unknown>>; total: number }>("/revenue-optimization/offers"),
  roipRecommendations: () =>
    apiGet<{ recommendations: Array<Record<string, unknown>>; total: number; note?: string }>(
      "/revenue-optimization/recommendations",
    ),
  roipBenchmarks: () =>
    apiGet<{ benchmarks: Array<Record<string, unknown>>; total: number }>("/revenue-optimization/benchmarks"),
  roipLearning: () => apiGet<Record<string, unknown>>("/revenue-optimization/learning"),
  roipReplies: () => apiGet<{ replies: Array<Record<string, unknown>>; total: number }>("/revenue-optimization/replies"),
  roipCompany: (companyId: string) => apiGet<Record<string, unknown>>(`/revenue-optimization/company/${companyId}`),
  roipCampaign: (campaignId: string) => apiGet<Record<string, unknown>>(`/revenue-optimization/campaign/${campaignId}`),
  roipSearch: (params: Record<string, string> = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiGet<Record<string, unknown>>(`/revenue-optimization/search${qs ? `?${qs}` : ""}`);
  },
  roipRefresh: (limit = 100) => apiPost<Record<string, unknown>>(`/revenue-optimization/refresh?limit=${limit}`, {}),

  // Buying Events API
  buyingEvents: (params?: {
    department?: string;
    classification?: string;
    status?: string;
    freshness?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.department) query.set("department", params.department);
    if (params?.classification) query.set("classification", params.classification);
    if (params?.status) query.set("status", params.status);
    if (params?.freshness) query.set("freshness", params.freshness);
    if (params?.search) query.set("search", params.search);
    query.set("limit", String(params?.limit ?? 100));
    query.set("offset", String(params?.offset ?? 0));
    return apiGet<{ items: Array<Record<string, unknown>>; total: number }>(`/buying-events?${query}`);
  },
  buyingEvent: (id: string) => apiGet<Record<string, unknown>>(`/buying-events/${id}`),
  buyingEventsStats: () => apiGet<Record<string, unknown>>("/buying-events/stats"),
  buyingEventsIntent: () => apiGet<Record<string, unknown>>("/buying-events/intent"),
  buyingEventsPipeline: () => apiGet<Record<string, unknown>>("/buying-events/pipeline"),
  buyingEventsSendEmail: (id: string, body: { to_email: string; subject: string; body: string }) =>
    apiPost<Record<string, unknown>>(`/buying-events/${id}/send-email`, body),
  buyingEventsSendBulk: (body: {
    event_ids?: string[];
    subject_template?: string;
    body_template?: string;
    custom_subject?: string;
    custom_body?: string;
  }) => apiPost<Record<string, unknown>>("/buying-events/send-bulk", body),
  buyingEventsUpdate: (id: string, body: { status?: string; classification?: string }) =>
    apiPost<Record<string, unknown>>(`/buying-events/${id}/update`, body),
  buyingEventsDelete: (id: string) =>
    apiPost<Record<string, unknown>>(`/buying-events/${id}/delete`, {}),
  buyingEventsEnrichAll: () =>
    apiPost<Record<string, unknown>>("/buying-events/enrich-all", {}),
  buyingEventsEnrich: (id: string) =>
    apiPost<Record<string, unknown>>(`/buying-events/${id}/enrich`, {}),
  buyingEventsEnrichmentStatus: (taskId: string) =>
    apiGet<Record<string, unknown>>(`/buying-events/enrichment-status/${taskId}`),
  buyingEventEnrichmentStatus: (id: string) =>
    apiGet<Record<string, unknown>>(`/buying-events/${id}/enrichment-status`),
};

export type SalesIntelligencePack = {
  snapshot_id?: string | null;
  company_id: string;
  company_name: string;
  opportunity_id?: string | null;
  buying_intent: Record<string, unknown>;
  psychology: Record<string, unknown>;
  objections: Array<Record<string, unknown>>;
  offer: Record<string, unknown>;
  trust: Record<string, unknown>;
  proposal: Record<string, unknown>;
  meeting_coach: Record<string, unknown>;
  reply_intelligence: Array<Record<string, unknown>>;
  memory: Record<string, unknown>;
  score: Record<string, unknown>;
  scoring_version?: string | null;
  evidence_chain?: string[];
  buying_intent_score?: number | null;
  buying_stage?: string | null;
  urgency?: string | null;
  primary_offer?: string | null;
  deal_probability?: number | null;
  close_probability?: number | null;
  created_at?: string | null;
};

export type FounderOsPack = {
  brief_id?: string | null;
  brief: Record<string, unknown>;
  command_center: Record<string, unknown>;
  assistant: Record<string, unknown> & { contacts?: Array<Record<string, unknown>>; greeting?: string; mission?: string };
  tasks: Array<Record<string, unknown>>;
  kpis: Record<string, unknown>;
  recommendations: Array<Record<string, unknown>>;
  proposals: Array<Record<string, unknown>>;
  meeting_packs: Array<Record<string, unknown>>;
  timeline_events?: Array<Record<string, unknown>>;
  scoring_version?: string | null;
};

export type RevenueHunterDossierRecord = {
  id: string;
  company_id: string;
  opportunity_id?: string | null;
  company_name: string;
  industry?: string | null;
  country?: string | null;
  company_size_band?: string | null;
  funding_stage?: string | null;
  revenue_band?: string | null;
  filter_passed: boolean;
  filter_match: Record<string, unknown>;
  recommended_service: string;
  service_confidence: number;
  service_matches: Array<Record<string, unknown>>;
  pain_points: Array<Record<string, unknown>>;
  website_intelligence: Record<string, unknown>;
  why_now: Record<string, unknown>;
  dossier: Record<string, unknown>;
  priority_grade: string;
  revenue_score: number;
  expected_budget: string;
  expected_timeline: string;
  probability: number;
  proceed_to_campaign: boolean;
  work_queue_eligible: boolean;
  score_breakdown: Array<Record<string, unknown>>;
  evidence_chain: string[];
  explanations: Record<string, unknown>;
  scoring_version: string;
  created_at?: string | null;
};

export type RevenueHunterWorkQueueItem = {
  id: string;
  dossier_id?: string | null;
  company_id: string;
  company_name: string;
  priority_grade: string;
  recommended_service: string;
  why_today: string;
  expected_budget: string;
  probability: number;
  primary_contact: Record<string, unknown>;
  status: string;
  allowed_actions: string[];
  rank: number;
  action_log: Array<Record<string, unknown>>;
  acted_at?: string | null;
  created_at?: string | null;
};

export type TargetAccountRecord = {
  id: string;
  company_id: string;
  opportunity_id?: string | null;
  company_name: string;
  industry?: string | null;
  country?: string | null;
  matched_icp_key?: string | null;
  matched_icp_name?: string | null;
  service_match?: string | null;
  fit_score: number;
  intent_score: number;
  budget_score: number;
  budget_band?: string | null;
  urgency_score: number;
  accessibility_score: number;
  competition_score: number;
  revenue_opportunity_score: number;
  tier: string;
  why_now: string;
  buying_signals: string[];
  negative_signals: string[];
  score_breakdown: Array<Record<string, unknown>>;
  evidence_chain: string[];
  hunter_triggered: boolean;
  hunter_tasks: string[];
  proceed_to_copilot: boolean;
  scoring_version: string;
  created_at?: string | null;
};

export type ICPProfileRecord = {
  id: string;
  key: string;
  name: string;
  service_match: string;
  priority: number;
  employee_count_min?: number | null;
  employee_count_max?: number | null;
  company_size_min?: number | null;
  company_size_max?: number | null;
  industries: string[];
  countries?: string[];
  technology_stack: string[];
  hiring_signals: string[];
  pain_points: string[];
  buying_signals: string[];
  negative_signals: string[];
  headquarters_cities?: string[];
  specialties?: string[];
  company_types?: string[];
  year_founded_min?: number | null;
  year_founded_max?: number | null;
  linkedin_url_required?: boolean;
  company_name_contains?: string[];
  domains?: string[];
  lists?: string[];
  is_active: boolean;
  metadata_json?: Record<string, unknown>;
};

export type LeadEngineRun = {
  run_id: string;
  product: string;
  status: string;
  stage: string;
  progress_pct?: number;
  stage_label?: string;
  enrich_status?: string;
  enrich_progress_pct?: number;
  enrich_label?: string;
  counts: Record<string, number>;
  rejects?: Record<string, number>;
  soft_flags?: Record<string, number>;
  error?: string | null;
  limit?: number;
  icp?: Record<string, unknown>;
  lead_count?: number;
  elapsed_seconds?: number | null;
  export_csv?: string | null;
};

export type LeadEngineLead = {
  id: string;
  company: string;
  founder_name?: string;
  founder_role?: string;
  email: string;
  phone?: string;
  website?: string;
  city?: string;
  category?: string;
  size?: string;
  platform?: string;
  intent_score?: number;
  grade?: string;
  why?: string;
  signal?: string;
  subject?: string;
  body?: string;
  evidence?: string[];
  outreach_status?: string;
  enriched?: boolean;
  already_contacted?: boolean;
};

// ── Partner Leads API ──────────────────────────────────────

export type PartnerLeadRecord = {
  id: string;
  agency_name: string;
  agency_url: string | null;
  country: string | null;
  city: string | null;
  agency_type: string | null;
  employees: string | null;
  founded: number | null;
  clients: string | null;
  client_count: number | null;
  revenue_generated: string | null;
  revenue_managed: string | null;
  notable_clients: string[];
  decision_maker: string | null;
  decision_maker_role: string | null;
  email: string | null;
  phone: string | null;
  linkedin: string | null;
  contactability: string | null;
  services: string[];
  certifications: string[];
  tier: string | null;
  client_access_score: number | null;
  comai_fit_score: number | null;
  final_score: number | null;
  why_this_agency: string | null;
  comai_fit: string | null;
  pitch_angle: string | null;
  status: string;
  outreach_sent: boolean;
  response_received: boolean;
  meeting_scheduled: boolean;
  partner_converted: boolean;
  source: string | null;
  created_at: string;
  updated_at: string;
};

export type PartnerLeadsStats = {
  total: number;
  tier_a: number;
  tier_b: number;
  tier_c: number;
  contacted: number;
  responded: number;
  meetings: number;
  converted: number;
  high_contactability: number;
  by_country: Record<string, number>;
  by_type: Record<string, number>;
  avg_final_score: number;
  avg_client_access_score: number;
  avg_comai_fit_score: number;
};

export async function getPartnerLeads(params?: {
  tier?: string;
  status?: string;
  country?: string;
  agency_type?: string;
  contactability?: string;
  search?: string;
  limit?: number;
  offset?: number;
}) {
  const query = new URLSearchParams();
  if (params?.tier) query.set("tier", params.tier);
  if (params?.status) query.set("status", params.status);
  if (params?.country) query.set("country", params.country);
  if (params?.agency_type) query.set("agency_type", params.agency_type);
  if (params?.contactability) query.set("contactability", params.contactability);
  if (params?.search) query.set("search", params.search);
  if (params?.limit) query.set("limit", String(params.limit));
  if (params?.offset) query.set("offset", String(params.offset));
  return apiGet<{ total: number; items: PartnerLeadRecord[] }>(
    `/partner-leads?${query}`
  );
}

export async function getPartnerLeadsStats() {
  return apiGet<PartnerLeadsStats>("/partner-leads/stats");
}

export async function getPartnerLead(id: string) {
  return apiGet<PartnerLeadRecord>(`/partner-leads/${id}`);
}

export async function updatePartnerLead(
  id: string,
  data: Partial<{
    status: string;
    tier: string;
    outreach_sent: boolean;
    response_received: boolean;
    meeting_scheduled: boolean;
    partner_converted: boolean;
    notes: string;
  }>
) {
  return apiPut<PartnerLeadRecord>(`/partner-leads/${id}`, data);
}

export async function exportPartnerLeads() {
  return apiGet<PartnerLeadRecord[]>("/partner-leads/export/all");
}
