"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useMemo } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { SalesCopilotCard } from "@/features/companies/sales-copilot-card";
import { SalesIntelligencePanel } from "@/features/companies/sales-intelligence-panel";
import { CirExecutiveSummary } from "@/features/companies/cir-executive-summary";
import { OfcCompanyCard } from "@/features/companies/ofc-company-card";
import { CompanyJourneyPanel } from "@/features/intelligence-center/company-journey-panel";
import { SalesReadinessExecutiveSummary } from "@/features/companies/sales-readiness-summary";
import { ReviewActions } from "@/features/opportunities/review-actions";
import { beaconApi } from "@/lib/api/beacon";
import {
  formatDateTime,
  formatLabel,
  formatPercent,
  formatRelativeTime,
  formatScore,
  priorityTone,
  scoreTone,
} from "@/lib/utils";

export function CompanyWorkspace({ companyId }: { companyId: string }) {
  const queryClient = useQueryClient();

  const company = useQuery({
    queryKey: ["company", companyId],
    queryFn: () => beaconApi.company(companyId),
  });
  const dna = useQuery({
    queryKey: ["company-dna", companyId],
    queryFn: () => beaconApi.contextDna(companyId),
    retry: false,
  });
  const contexts = useQuery({
    queryKey: ["company-context", companyId],
    queryFn: () => beaconApi.contextCompany(companyId),
  });
  const pains = useQuery({
    queryKey: ["company-pains", companyId],
    queryFn: () => beaconApi.contextPains(companyId),
  });
  const goals = useQuery({
    queryKey: ["company-goals", companyId],
    queryFn: () => beaconApi.contextGoals(companyId),
  });
  const evidence = useQuery({
    queryKey: ["company-evidence", companyId],
    queryFn: () => beaconApi.contextEvidence(companyId),
  });
  const timeline = useQuery({
    queryKey: ["company-timeline", companyId],
    queryFn: () => beaconApi.companyTimeline(companyId),
  });
  const revenue = useQuery({
    queryKey: ["company-revenue", companyId],
    queryFn: () => beaconApi.revenueCompany(companyId),
    retry: false,
  });
  const playbook = useQuery({
    queryKey: ["company-playbook", companyId],
    queryFn: () => beaconApi.revenuePlaybook(companyId),
    retry: false,
  });
  const enrichment = useQuery({
    queryKey: ["company-enrichment", companyId],
    queryFn: () => beaconApi.enrichmentCompany(companyId),
    retry: false,
  });
  const verification = useQuery({
    queryKey: ["company-verification", companyId],
    queryFn: () => beaconApi.verificationCompany(companyId),
    retry: false,
  });
  const erowd = useQuery({
    queryKey: ["company-erowd", companyId],
    queryFn: () => beaconApi.erowdCompany(companyId),
    retry: false,
  });
  const decision = useQuery({
    queryKey: ["company-decision", companyId],
    queryFn: () => beaconApi.decisionCompany(companyId),
    retry: false,
  });
  const opportunities = useQuery({
    queryKey: ["opportunities"],
    queryFn: () => beaconApi.opportunities({ limit: 200 }),
  });
  const phCard = useQuery({
    queryKey: ["ph-company", companyId],
    queryFn: () => beaconApi.phCompany(companyId),
    retry: false,
  });
  const evaluatePh = useMutation({
    mutationFn: () => beaconApi.phEvaluateCompany(companyId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["ph-company", companyId] });
    },
  });

  const companyOpportunity = useMemo(
    () => (opportunities.data?.opportunities ?? []).find((item) => item.company_id === companyId),
    [opportunities.data, companyId],
  );

  const opportunityId = companyOpportunity?.id;
  const opportunityEvidence = useQuery({
    queryKey: ["opportunity-evidence", opportunityId],
    queryFn: () => beaconApi.opportunityEvidence(opportunityId!),
    enabled: Boolean(opportunityId),
  });
  const opportunityHistory = useQuery({
    queryKey: ["opportunity-history", opportunityId],
    queryFn: () => beaconApi.opportunityHistory(opportunityId!),
    enabled: Boolean(opportunityId),
  });
  const opportunityRecommendation = useQuery({
    queryKey: ["opportunity-recommendation", opportunityId],
    queryFn: () => beaconApi.opportunityRecommendation(opportunityId!),
    enabled: Boolean(opportunityId),
  });

  const qualityReports = useQuery({
    queryKey: ["quality-events"],
    queryFn: () => beaconApi.qualityEvents({ limit: 50 }),
  });

  const feedback = useMutation({
    mutationFn: beaconApi.opportunityFeedback,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["opportunities"] });
    },
  });

  const refreshEnrichment = useMutation({
    mutationFn: () => beaconApi.enrichmentRefresh(companyId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["company-enrichment", companyId] });
      await queryClient.invalidateQueries({ queryKey: ["company-verification", companyId] });
    },
  });

  const refreshVerification = useMutation({
    mutationFn: () => beaconApi.verificationRefresh(companyId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["company-verification", companyId] });
      await queryClient.invalidateQueries({ queryKey: ["company-decision", companyId] });
    },
  });

  const refreshDecision = useMutation({
    mutationFn: () => beaconApi.decisionRefresh(companyId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["company-decision", companyId] });
    },
  });

  if (company.isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-28 w-full" />
        <div className="grid gap-4 lg:grid-cols-3">
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
        </div>
      </div>
    );
  }

  if (company.isError || !company.data) {
    return (
      <ErrorState
        description="Company not found or API unavailable."
        onRetry={() => void company.refetch()}
      />
    );
  }

  const latestContext = contexts.data?.contexts[0];
  const linkedReports = (qualityReports.data?.events ?? []).filter((report) =>
    (contexts.data?.contexts ?? []).some((ctx) => ctx.quality_report_id === report.id),
  );

  const ph = phCard.data;
  const emptyLead = (ph?.empty_states as Record<string, Record<string, unknown>> | undefined)?.lead_enrichment;
  const emptyDecision = (ph?.empty_states as Record<string, Record<string, unknown>> | undefined)?.decision_discovery;

  return (
    <div className="mx-auto flex max-w-[900px] flex-col gap-6">
      <OfcCompanyCard companyId={companyId} />
      <CompanyJourneyPanel companyId={companyId} />

      <details className="rounded-xl border border-border/60 p-4">
        <summary className="cursor-pointer text-sm font-medium text-muted-foreground">Advanced intelligence (legacy tabs)</summary>
        <div className="mt-4 space-y-6">
      <Card className="border-border/70 bg-card/80 shadow-soft">
        <CardHeader className="pb-3">
          <SectionLabel>Identity foundation</SectionLabel>
          <CardTitle className="text-xl">Official Website & Entity Resolution</CardTitle>
          <CardDescription>
            A company without a verified official website is not a company — it remains a signal.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {erowd.isLoading ? (
            <Skeleton className="h-16 w-full" />
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <div>
                <p className="text-xs text-muted-foreground">Official Website</p>
                <p className="font-medium">
                  {erowd.data?.official_website ? (
                    <a
                      className="text-primary underline-offset-2 hover:underline"
                      href={String(erowd.data.official_website)}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {String(erowd.data.official_website)}
                    </a>
                  ) : (
                    String(ph?.website ?? company.data?.primary_domain ?? "Not discovered")
                  )}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Verified</p>
                <Badge variant={erowd.data?.verified ? "default" : "secondary"}>
                  {erowd.data?.verified ? "Yes" : "No"}
                </Badge>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Confidence</p>
                <p className="font-medium">{formatScore(Number(erowd.data?.confidence ?? 0), 0)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Collector</p>
                <p className="font-medium">{String(erowd.data?.collector ?? ph?.source ?? "—")}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Discovery Source</p>
                <p className="font-medium">{String(erowd.data?.discovery_source ?? "—")}</p>
              </div>
              <div className="sm:col-span-2 lg:col-span-1">
                <p className="text-xs text-muted-foreground">Evidence</p>
                <p className="text-sm text-muted-foreground">
                  {Array.isArray(erowd.data?.evidence) && erowd.data.evidence.length
                    ? (erowd.data.evidence as string[]).slice(0, 4).join(" · ")
                    : "No EROWD evidence stored"}
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <CirExecutiveSummary companyId={companyId} />
      <SalesReadinessExecutiveSummary companyId={companyId} />

      <header className="flex flex-col gap-4 rounded-2xl border border-border/70 bg-card/60 p-6 shadow-soft">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-2">
            <SectionLabel>Founder Workspace</SectionLabel>
            <h1 className="font-display text-3xl font-semibold tracking-tight">
              {String(ph?.company ?? company.data.name)}
            </h1>
            <div className="flex flex-wrap gap-2 pt-1">
              <Badge className="bg-muted text-muted-foreground ring-border">
                {String(ph?.industry ?? company.data.industry ?? "Industry unknown")}
              </Badge>
              <Badge className="bg-muted text-muted-foreground ring-border">
                {String(ph?.location ?? "Location unknown")}
              </Badge>
              <Badge className="bg-muted text-muted-foreground ring-border">
                {String(ph?.employees ?? "Employees unknown")}
              </Badge>
              <Badge className="bg-muted text-muted-foreground ring-border">
                {String(erowd.data?.official_website ?? ph?.website ?? company.data.primary_domain ?? "No website")}
              </Badge>
              <Badge className="bg-muted text-muted-foreground ring-border">
                Source {String(ph?.source ?? "unknown")}
              </Badge>
              <Badge className="bg-muted text-muted-foreground ring-border">
                Intent {String(ph?.intent ?? "—")}
              </Badge>
              <Badge className={`ring-border ${scoreTone(Number(ph?.score ?? 0))}`}>
                Score {formatScore(Number(ph?.score ?? 0), 0)}
              </Badge>
              <Badge className="bg-muted text-muted-foreground ring-border">
                Readiness {formatLabel(String(ph?.contact_readiness ?? "not_ready"))}
              </Badge>
              <Badge className="bg-muted text-muted-foreground ring-border">
                Identity {formatScore(Number(erowd.data?.confidence ?? ph?.confidence ?? 0), 0)}
              </Badge>
              {ph?.visible_in_founder_queue ? (
                <Badge>Founder Queue</Badge>
              ) : (
                <Badge variant="outline">Hidden from Founder Queue</Badge>
              )}
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" disabled={evaluatePh.isPending} onClick={() => evaluatePh.mutate()}>
              {evaluatePh.isPending ? "Evaluating…" : "Re-evaluate readiness"}
            </Button>
            {companyOpportunity ? (
              <Button asChild variant="outline">
                <Link href={`/opportunities/${companyOpportunity.id}`}>Opportunity detail</Link>
              </Button>
            ) : null}
            <Button
              variant="outline"
              disabled={refreshEnrichment.isPending}
              onClick={() => refreshEnrichment.mutate()}
            >
              {refreshEnrichment.isPending ? "Refreshing lead…" : "Refresh lead profile"}
            </Button>
            {companyOpportunity ? (
              <ReviewActions
                disabled={feedback.isPending}
                onReview={(outcome) =>
                  feedback.mutate({
                    opportunity_id: companyOpportunity.id,
                    reviewer: "operator",
                    review_outcome: outcome,
                  })
                }
              />
            ) : null}
          </div>
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <Stat label="Decision maker" value={String(ph?.decision_maker ?? "—")} />
          <Stat label="Verified email" value={String(ph?.verified_email ?? "—")} />
          <Stat label="Verified phone" value={String(ph?.verified_phone ?? "—")} />
          <Stat
            label="Service / deal"
            value={`${String(ph?.recommended_service ?? "—")} · ${String(ph?.estimated_deal ?? "—")}`}
          />
        </div>
        {Array.isArray(ph?.collected_from) && ph.collected_from.length > 0 ? (
          <div>
            <p className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Collected from</p>
            <div className="flex flex-wrap gap-2">
              {(ph.collected_from as Array<Record<string, unknown>>).slice(0, 8).map((row, idx) => (
                <Badge key={`${row.source}-${idx}`} variant="outline">
                  {String(row.source)} · {String(row.at ?? "").slice(0, 16)}
                </Badge>
              ))}
            </div>
          </div>
        ) : null}
        {Array.isArray(ph?.evidence_cards) && ph.evidence_cards.length > 0 ? (
          <div>
            <p className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Evidence</p>
            <div className="grid gap-2 md:grid-cols-2">
              {(ph.evidence_cards as Array<Record<string, unknown>>).slice(0, 4).map((ev, idx) => (
                <div key={idx} className="rounded-lg border border-border/60 p-3 text-sm text-muted-foreground">
                  <div className="mb-1 flex flex-wrap gap-2">
                    <Badge variant="outline">{String(ev.source)}</Badge>
                    {ev.confidence != null ? (
                      <Badge variant="outline">{formatPercent(Number(ev.confidence))}</Badge>
                    ) : null}
                  </div>
                  <p>{String(ev.snippet ?? "")}</p>
                </div>
              ))}
            </div>
          </div>
        ) : null}
        {ph?.admission && (ph.admission as Record<string, unknown>).verdict === "reject" ? (
          <EmptyState
            title="Admission rejected"
            description={((ph.admission as Record<string, unknown>).reasons as string[] | undefined)?.join(" · ") || "Failed Opportunity Admission Gate"}
            className="py-6"
          />
        ) : null}
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Sales-Ready Lead Profile</CardTitle>
          <CardDescription>
            Enriched company, contacts, decision makers, and outreach context — review here before manual outreach
          </CardDescription>
        </CardHeader>
        <CardContent>
          {enrichment.isError ? (
            <EmptyState
              title={String(emptyLead?.why ?? "No verified contacts yet")}
              description={`Engine: ${String(emptyLead?.engine ?? "lead_enrichment")}. Next: ${String(emptyLead?.next_scheduled ?? "enrichment queue")}. Expected: ${String(emptyLead?.expected_completion ?? "after worker runs")}.`}
              className="py-10"
              action={
                <Button variant="outline" disabled={refreshEnrichment.isPending} onClick={() => refreshEnrichment.mutate()}>
                  Manual refresh
                </Button>
              }
            />
          ) : enrichment.isLoading ? (
            <Skeleton className="h-56 w-full" />
          ) : enrichment.data ? (
            <div className="space-y-5">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div className="space-y-2">
                  <p className="font-display text-xl font-semibold">{enrichment.data.recommended_service}</p>
                  <p className="text-sm text-muted-foreground">{enrichment.data.why_now}</p>
                  <div className="flex flex-wrap gap-2">
                    {enrichment.data.priority ? (
                      <Badge className={priorityTone(enrichment.data.priority)}>
                        {formatLabel(enrichment.data.priority)}
                      </Badge>
                    ) : null}
                    <Badge className="bg-muted text-muted-foreground ring-border">
                      {enrichment.data.buyer_persona}
                    </Badge>
                    {enrichment.data.estimated_budget ? (
                      <Badge className="bg-muted text-muted-foreground ring-border">
                        Budget {formatLabel(enrichment.data.estimated_budget)}
                      </Badge>
                    ) : null}
                    <Badge className="bg-muted text-muted-foreground ring-border">
                      Enrichment {formatScore(enrichment.data.enrichment_confidence.overall_enrichment_confidence, 0)}
                    </Badge>
                  </div>
                </div>
                <p className={`font-display text-3xl font-semibold ${scoreTone(enrichment.data.opportunity_score)}`}>
                  {formatScore(enrichment.data.opportunity_score, 0)}
                </p>
              </div>

              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <Stat label="Website" value={enrichment.data.company_profile.website || "—"} />
                <Stat
                  label="Size"
                  value={
                    enrichment.data.company_profile.company_size_range ||
                    (enrichment.data.company_profile.employee_count_estimate
                      ? `${enrichment.data.company_profile.employee_count_estimate} employees`
                      : "—")
                  }
                />
                <Stat
                  label="Location"
                  value={
                    [enrichment.data.company_profile.location, enrichment.data.company_profile.country]
                      .filter(Boolean)
                      .join(", ") || "—"
                  }
                />
                <Stat label="Business pain" value={enrichment.data.business_pain || "—"} />
              </div>

              <div className="grid gap-4 lg:grid-cols-3">
                <div>
                  <p className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
                    Public contacts
                  </p>
                  <ListItems
                    items={(enrichment.data.public_contact_information ?? []).map(
                      (item) => `${formatLabel(item.kind)}: ${item.value}`,
                    )}
                  />
                </div>
                <div>
                  <p className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
                    Decision makers
                  </p>
                  <ListItems
                    items={(enrichment.data.decision_makers ?? []).map((person) =>
                      person.linkedin_url
                        ? `${person.name} · ${person.role}`
                        : `${person.name} · ${person.role}`,
                    )}
                  />
                </div>
                <div>
                  <p className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
                    Best outreach angle
                  </p>
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    {enrichment.data.best_outreach_angle}
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {(enrichment.data.social_profiles ?? []).slice(0, 4).map((profile) => (
                      <a
                        key={`${profile.platform}-${profile.url}`}
                        href={profile.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-primary underline-offset-2 hover:underline"
                      >
                        {formatLabel(profile.platform)}
                      </a>
                    ))}
                  </div>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <p className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
                    Technology stack
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {(enrichment.data.technology_stack.length
                      ? enrichment.data.technology_stack
                      : [{ name: "Not detected", category: "", confidence: 0, source: "" }]
                    ).map((tech) => (
                      <Badge key={`${tech.name}-${tech.source}`} className="bg-muted text-muted-foreground ring-border">
                        {tech.name}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
                    Team & hiring
                  </p>
                  <Stat
                    label="Open positions"
                    value={
                      enrichment.data.team_insights.open_positions.length
                        ? enrichment.data.team_insights.open_positions.slice(0, 4).join(", ")
                        : enrichment.data.team_insights.hiring_trends || "No open roles detected"
                    }
                  />
                </div>
              </div>

              <div className="grid gap-3 border-t border-border/60 pt-4 sm:grid-cols-4">
                <Stat
                  label="Profile completeness"
                  value={formatScore(enrichment.data.enrichment_confidence.profile_completeness, 0)}
                />
                <Stat
                  label="Contact availability"
                  value={formatScore(enrichment.data.enrichment_confidence.contact_availability, 0)}
                />
                <Stat
                  label="Technology confidence"
                  value={formatScore(enrichment.data.enrichment_confidence.technology_confidence, 0)}
                />
                <Stat
                  label="Decision-maker confidence"
                  value={formatScore(enrichment.data.enrichment_confidence.decision_maker_confidence, 0)}
                />
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-4">
          <div>
            <CardTitle>Decision Maker Discovery</CardTitle>
            <CardDescription>
              Publicly attributed decision makers, official business channels, and ranked outreach paths
            </CardDescription>
          </div>
          <Button
            variant="outline"
            disabled={refreshDecision.isPending}
            onClick={() => refreshDecision.mutate()}
          >
            {refreshDecision.isPending ? "Discovering…" : "Refresh discovery"}
          </Button>
        </CardHeader>
        <CardContent>
          {decision.isError ? (
            <EmptyState
              title={String(emptyDecision?.why ?? "No decision makers discovered yet")}
              description={`Engine: ${String(emptyDecision?.engine ?? "decision_discovery")}. Next: ${String(emptyDecision?.next_scheduled ?? "decision queue")}. Expected: ${String(emptyDecision?.expected_completion ?? "after verification")}.`}
              className="py-10"
              action={
                <Button variant="outline" disabled={refreshDecision.isPending} onClick={() => refreshDecision.mutate()}>
                  Manual refresh
                </Button>
              }
            />
          ) : decision.isLoading ? (
            <Skeleton className="h-48 w-full" />
          ) : decision.data ? (
            <div className="space-y-5">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div className="space-y-2">
                  <p className="font-display text-xl font-semibold">{decision.data.recommended_service}</p>
                  <p className="text-sm text-muted-foreground">{decision.data.reason}</p>
                  <div className="flex flex-wrap gap-2">
                    <Badge className="bg-muted text-muted-foreground ring-border">
                      Discovery {formatScore(decision.data.confidence.overall_discovery_score, 0)}
                    </Badge>
                    <Badge className="bg-muted text-muted-foreground ring-border">
                      Buyer match {formatScore(decision.data.buyer_match_confidence, 0)}
                    </Badge>
                  </div>
                </div>
                <p className={`font-display text-3xl font-semibold ${scoreTone(decision.data.opportunity_score)}`}>
                  {formatScore(decision.data.opportunity_score, 0)}
                </p>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <Stat
                  label="Primary decision maker"
                  value={
                    decision.data.primary_decision_maker
                      ? `${decision.data.primary_decision_maker.name} · ${decision.data.primary_decision_maker.role}`
                      : "Not publicly identified"
                  }
                />
                <Stat
                  label="Secondary decision maker"
                  value={
                    decision.data.secondary_decision_maker
                      ? `${decision.data.secondary_decision_maker.name} · ${decision.data.secondary_decision_maker.role}`
                      : "Not publicly identified"
                  }
                />
              </div>

              <div className="grid gap-4 lg:grid-cols-3">
                <div>
                  <p className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Departments</p>
                  <ListItems
                    items={(decision.data.departments ?? []).map(
                      (item) => `${item.name} · ${formatScore(item.signal_strength, 0)}`,
                    )}
                  />
                </div>
                <div>
                  <p className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
                    Official business contacts
                  </p>
                  {(decision.data.public_emails.length ||
                    decision.data.public_phones.length ||
                    decision.data.contact_channels.length) ? (
                    <ListItems
                      items={[
                        ...decision.data.public_emails.map((email) => `Email: ${email}`),
                        ...decision.data.public_phones.map((phone) => `Phone: ${phone}`),
                        ...decision.data.contact_channels
                          .filter((item) => !item.value.includes("@") && item.kind !== "business_phone")
                          .slice(0, 4)
                          .map((item) => `${formatLabel(item.kind)}: ${item.value}`),
                      ]}
                    />
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      {decision.data.no_public_contact_message ||
                        "No verified public business contact available."}
                    </p>
                  )}
                </div>
                <div>
                  <p className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
                    Official company profiles
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {(decision.data.public_profiles ?? []).length ? (
                      decision.data.public_profiles.map((profile) => (
                        <a
                          key={`${profile.platform}-${profile.url}`}
                          href={profile.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-xs text-primary underline-offset-2 hover:underline"
                        >
                          {formatLabel(profile.platform)}
                        </a>
                      ))
                    ) : (
                      <p className="text-sm text-muted-foreground">No official public profiles detected.</p>
                    )}
                  </div>
                </div>
              </div>

              <div>
                <p className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
                  Recommended outreach order
                </p>
                <ListItems
                  items={(decision.data.best_outreach_sequence ?? []).slice(0, 8).map((step) => {
                    const rank = String(step.rank ?? "");
                    const kind = formatLabel(String(step.channel_kind ?? step.kind ?? "channel"));
                    const value = String(step.value ?? "");
                    return `${rank}. ${kind} — ${value}`;
                  })}
                />
              </div>

              <div className="grid gap-3 border-t border-border/60 pt-4 sm:grid-cols-4">
                <Stat
                  label="Leadership confidence"
                  value={formatScore(decision.data.confidence.leadership_confidence, 0)}
                />
                <Stat
                  label="Department confidence"
                  value={formatScore(decision.data.confidence.department_confidence, 0)}
                />
                <Stat
                  label="Contact confidence"
                  value={formatScore(decision.data.confidence.contact_confidence, 0)}
                />
                <Stat
                  label="Buyer match confidence"
                  value={formatScore(decision.data.confidence.buyer_match_confidence, 0)}
                />
              </div>

              <div>
                <p className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Evidence</p>
                <ListItems
                  items={(decision.data.evidence_chain ?? []).slice(0, 6).map((item) =>
                    String(item.summary || item.category || "Evidence"),
                  )}
                />
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <SalesIntelligencePanel companyId={companyId} />

      <SalesCopilotCard companyId={companyId} />

      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-4">
          <div>
            <CardTitle>Lead Readiness</CardTitle>
            <CardDescription>
              Data verification coverage, freshness, and trust for this enriched profile
            </CardDescription>
          </div>
          <Button
            variant="outline"
            disabled={refreshVerification.isPending}
            onClick={() => refreshVerification.mutate()}
          >
            {refreshVerification.isPending ? "Verifying…" : "Re-verify"}
          </Button>
        </CardHeader>
        <CardContent>
          {verification.isError ? (
            <EmptyState
              title="Verification pending"
              description="Data Verification runs after Lead Enrichment. Refresh once an enrichment report exists."
              className="py-10"
            />
          ) : verification.isLoading ? (
            <Skeleton className="h-48 w-full" />
          ) : verification.data ? (
            <div className="space-y-5">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
                    Overall Readiness
                  </p>
                  <p className={`font-display text-4xl font-semibold ${scoreTone(verification.data.overall_readiness)}`}>
                    {formatScore(verification.data.overall_readiness, 0)}%
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Decision: {formatLabel(verification.data.decision)}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge className="bg-muted text-muted-foreground ring-border">
                    Freshness {formatScore(verification.data.freshness_score, 0)}%
                  </Badge>
                  <Badge className="bg-muted text-muted-foreground ring-border">
                    Trust {formatScore(verification.data.trust_score, 0)}%
                  </Badge>
                  <Badge className="bg-muted text-muted-foreground ring-border">
                    Completeness {formatScore(verification.data.completeness.overall_completeness, 0)}%
                  </Badge>
                </div>
              </div>

              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                {(
                  [
                    ["Company Profile", verification.data.readiness_checklist.company_profile],
                    ["Technology", verification.data.readiness_checklist.technology],
                    ["Leadership", verification.data.readiness_checklist.leadership],
                    ["Public Business Email", verification.data.readiness_checklist.public_business_email],
                    ["Public Phone", verification.data.readiness_checklist.public_phone],
                    ["Hiring", verification.data.readiness_checklist.hiring],
                    ["Funding", verification.data.readiness_checklist.funding],
                    ["Timeline", verification.data.readiness_checklist.timeline],
                  ] as const
                ).map(([label, ok]) => (
                  <div
                    key={label}
                    className="flex items-center justify-between rounded-lg border border-border/60 bg-background/40 px-3 py-2 text-sm"
                  >
                    <span>{label}</span>
                    <span className={ok ? "text-emerald-600" : "text-muted-foreground"}>{ok ? "✓" : "✗"}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <CardHeader>
            <CardTitle>Company DNA</CardTitle>
            <CardDescription>Context Engine profile snapshot</CardDescription>
          </CardHeader>
          <CardContent>
            {dna.isError ? (
              <p className="text-sm text-muted-foreground">DNA not available yet.</p>
            ) : dna.isLoading ? (
              <Skeleton className="h-40 w-full" />
            ) : dna.data ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <Stat label="Industry" value={dna.data.industry || "—"} />
                <Stat label="Growth stage" value={formatLabel(dna.data.company_stage)} />
                <Stat label="Business model" value={formatLabel(dna.data.business_model)} />
                <Stat label="Completeness" value={formatScore(dna.data.completeness_score, 0)} />
                <Stat label="AI adoption" value={formatScore(dna.data.ai_adoption, 0)} />
                <Stat label="Automation adoption" value={formatScore(dna.data.automation_adoption, 0)} />
                <div className="sm:col-span-2">
                  <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Technology stack</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {(dna.data.technology_stack.length ? dna.data.technology_stack : ["Not detected"]).map((tech) => (
                      <Badge key={tech} className="bg-muted text-muted-foreground ring-border">
                        {tech}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            ) : null}
            {latestContext ? (
              <div className="mt-5 grid gap-3 border-t border-border/60 pt-4 sm:grid-cols-3">
                <Stat label="AI readiness" value={formatScore(latestContext.ai_readiness, 0)} />
                <Stat label="Automation readiness" value={formatScore(latestContext.automation_readiness, 0)} />
                <Stat label="Budget probability" value={formatScore(latestContext.budget_probability, 0)} />
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Revenue Recommendation</CardTitle>
            <CardDescription>Deterministic service match and deal range</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {revenue.isError ? (
              <EmptyState
                title="No revenue recommendation"
                description="Revenue Engine has not scored this company yet."
                className="py-10"
              />
            ) : revenue.isLoading ? (
              <Skeleton className="h-48 w-full" />
            ) : revenue.data ? (
              <>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-display text-xl font-semibold">{revenue.data.recommended_service}</p>
                    <p className="text-sm text-muted-foreground">{revenue.data.reason}</p>
                  </div>
                  <p className={`font-display text-3xl font-semibold ${scoreTone(revenue.data.opportunity_score)}`}>
                    {formatScore(revenue.data.opportunity_score, 0)}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge className={priorityTone(revenue.data.priority)}>{formatLabel(revenue.data.priority)}</Badge>
                  <Badge className="bg-muted text-muted-foreground ring-border">
                    {formatLabel(revenue.data.estimated_budget_range)}
                  </Badge>
                  <Badge className="bg-muted text-muted-foreground ring-border">
                    {revenue.data.buyer_persona?.persona || "Persona pending"}
                  </Badge>
                </div>
                <Stat label="Business pain" value={revenue.data.business_pain || "—"} />
                <Stat
                  label="Confidence"
                  value={`${formatScore(revenue.data.confidence, 0)} · ${formatLabel(revenue.data.project_size)} · ${formatLabel(revenue.data.implementation_complexity)} complexity`}
                />
              </>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>Playbook</CardTitle>
            <CardDescription>Structured conversation guidance — no outreach generation</CardDescription>
          </CardHeader>
          <CardContent>
            {playbook.isError ? (
              <p className="text-sm text-muted-foreground">Playbook not available.</p>
            ) : playbook.data ? (
              <div className="grid gap-4 md:grid-cols-2">
                <Stat label="Why" value={playbook.data.why} />
                <Stat label="Conversation angle" value={playbook.data.conversation_angle} />
                <Stat label="Decision maker" value={playbook.data.decision_maker} />
                <Stat label="Expected outcome" value={playbook.data.expected_outcome} />
                <Stat label="Risk" value={playbook.data.risk} />
                <Stat label="Business pain" value={playbook.data.business_pain} />
              </div>
            ) : (
              <Skeleton className="h-32 w-full" />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Pains & Goals</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Pains</p>
              <ListItems items={(pains.data?.items ?? []).map((item) => `${item.category}: ${item.value}`)} />
            </div>
            <div>
              <p className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Goals</p>
              <ListItems items={(goals.data?.items ?? []).map((item) => `${item.category}: ${item.value}`)} />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Signals Timeline</CardTitle>
            <CardDescription>Chronological company activity</CardDescription>
          </CardHeader>
          <CardContent>
            <Timeline
              items={(timeline.data?.timeline ?? []).map((item) => ({
                title: formatLabel(item.signal_type),
                body: item.summary,
                stamp: item.timestamp,
                meta: `Confidence ${formatScore(item.confidence, 0)} · ${item.source || "source unknown"}`,
              }))}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Evidence Chain & Source Attribution</CardTitle>
            <CardDescription>Context evidence plus opportunity evidence</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {(evidence.data?.evidence ?? []).slice(0, 6).map((item) => (
              <div key={item.id} className="rounded-lg border border-border/60 bg-background/40 px-3 py-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium">{formatLabel(item.evidence_type)}</p>
                  <span className="text-xs text-muted-foreground">{formatScore(item.confidence, 0)}</span>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  {item.reference_key || item.reference_id || "Reference unavailable"} · {formatRelativeTime(item.created_at)}
                </p>
              </div>
            ))}
            {(opportunityEvidence.data?.evidence ?? []).slice(0, 6).map((item) => (
              <div key={item.id} className="rounded-lg border border-border/60 bg-background/40 px-3 py-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium">{formatLabel(item.source_type)} · {item.category}</p>
                  <Badge className="bg-muted text-muted-foreground ring-border">{item.polarity}</Badge>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">{item.summary}</p>
                <p className="mt-1 text-[11px] text-muted-foreground">
                  Confidence {formatScore(item.confidence, 0)} · Weight {formatScore(item.weight, 2)} · Trust/freshness in details
                </p>
              </div>
            ))}
            {(evidence.data?.evidence.length ?? 0) === 0 && (opportunityEvidence.data?.evidence.length ?? 0) === 0 ? (
              <p className="text-sm text-muted-foreground">No evidence linked yet.</p>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Opportunity Analysis</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {companyOpportunity ? (
              <>
                <Stat label="Status" value={formatLabel(companyOpportunity.status)} />
                <Stat label="Recommendation" value={formatLabel(companyOpportunity.recommendation)} />
                <Stat label="Narrative" value={companyOpportunity.narrative} />
                <Stat
                  label="Scores"
                  value={`Opp ${formatScore(companyOpportunity.opportunity_score, 0)} · Conf ${formatScore(companyOpportunity.confidence_score, 0)} · Urgency ${formatScore(companyOpportunity.urgency_score, 0)}`}
                />
                {opportunityRecommendation.data ? (
                  <Stat
                    label="Next step"
                    value={`${opportunityRecommendation.data.action}: ${opportunityRecommendation.data.next_step}`}
                  />
                ) : null}
              </>
            ) : (
              <p className="text-sm text-muted-foreground">No opportunity scored yet.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Changes</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(opportunityHistory.data?.history ?? []).slice(0, 6).map((item) => (
              <div key={item.id} className="rounded-lg border border-border/50 px-3 py-2">
                <p className="text-sm font-medium">{formatLabel(item.action)}</p>
                <p className="text-xs text-muted-foreground">
                  {item.actor} · {formatDateTime(item.created_at)}
                </p>
              </div>
            ))}
            {(opportunityHistory.data?.history.length ?? 0) === 0 ? (
              <p className="text-sm text-muted-foreground">No history yet.</p>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quality Reports</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {linkedReports.slice(0, 5).map((report) => (
              <div key={report.id} className="rounded-lg border border-border/50 px-3 py-2">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium">{report.source}</p>
                  <Badge className="bg-muted text-muted-foreground ring-border">{report.decision}</Badge>
                </div>
                <p className="text-xs text-muted-foreground">
                  Quality {formatScore(report.overall_quality_score, 0)} · Trust {formatScore(report.trust_score, 0)} · Freshness{" "}
                  {formatScore(report.freshness_score, 0)}
                </p>
              </div>
            ))}
            {linkedReports.length === 0 ? (
              <p className="text-sm text-muted-foreground">No linked quality reports found in recent events.</p>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Knowledge Graph Summary</CardTitle>
          <CardDescription>Derived from revenue evidence and context references</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Knowledge node refs:{" "}
            {Array.isArray(revenue.data?.evidence.knowledge_node_ids)
              ? (revenue.data?.evidence.knowledge_node_ids as string[]).join(", ") || "None"
              : "None linked on latest recommendation"}
          </p>
          <p className="mt-2 text-sm text-muted-foreground">
            Context coverage confidence avg:{" "}
            {contexts.data?.contexts.length
              ? formatPercent(
                  contexts.data.contexts.reduce((sum, item) => sum + item.confidence, 0) /
                    contexts.data.contexts.length,
                )
              : "—"}
          </p>
        </CardContent>
      </Card>
        </div>
      </details>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm leading-relaxed">{value}</p>
    </div>
  );
}

function ListItems({ items }: { items: string[] }) {
  if (!items.length) return <p className="text-sm text-muted-foreground">None detected.</p>;
  return (
    <ul className="space-y-2">
      {items.slice(0, 6).map((item) => (
        <li key={item} className="rounded-lg border border-border/50 bg-background/30 px-3 py-2 text-sm">
          {item}
        </li>
      ))}
    </ul>
  );
}

function Timeline({
  items,
}: {
  items: Array<{ title: string; body: string; stamp: string; meta: string }>;
}) {
  if (!items.length) return <p className="text-sm text-muted-foreground">No timeline events yet.</p>;
  return (
    <ol className="space-y-0">
      {items.slice(0, 12).map((item, index) => (
        <li key={`${item.stamp}-${index}`} className="relative flex gap-4 pb-6 last:pb-0">
          <div className="flex flex-col items-center">
            <span className="mt-1 h-2.5 w-2.5 rounded-full bg-primary shadow-soft" />
            {index < items.length - 1 ? <span className="mt-1 w-px flex-1 bg-border" /> : null}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-medium">{item.title}</p>
              <p className="text-xs text-muted-foreground">{formatDateTime(item.stamp)}</p>
            </div>
            <p className="mt-1 text-sm text-muted-foreground">{item.body}</p>
            <p className="mt-1 text-[11px] text-muted-foreground">{item.meta}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}
