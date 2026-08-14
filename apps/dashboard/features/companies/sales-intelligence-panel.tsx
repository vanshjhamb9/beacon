"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi, type SalesIntelligencePack } from "@/lib/api/beacon";
import { formatScore } from "@/lib/utils";

const TABS = [
  "Buying Intent",
  "Psychology",
  "Objections",
  "Offer",
  "Proposal",
  "Meeting",
  "Relationship",
  "Reply Intelligence",
  "Score",
] as const;

type Tab = (typeof TABS)[number];

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

function asList(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

export function SalesIntelligencePanel({ companyId }: { companyId: string }) {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<Tab>("Buying Intent");

  const pack = useQuery({
    queryKey: ["sales-intelligence", companyId],
    queryFn: () => beaconApi.salesIntelligenceCompany(companyId),
    retry: false,
  });

  const refresh = useMutation({
    mutationFn: () => beaconApi.salesIntelligenceRefresh(companyId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["sales-intelligence", companyId] });
    },
  });

  const data = pack.data;
  const intent = asRecord(data?.buying_intent);
  const psychology = asRecord(data?.psychology);
  const offer = asRecord(data?.offer);
  const proposal = asRecord(data?.proposal);
  const meeting = asRecord(data?.meeting_coach);
  const memory = asRecord(data?.memory);
  const score = asRecord(data?.score);
  const objections = asList(data?.objections);
  const replies = asList(data?.reply_intelligence);
  const trust = asRecord(data?.trust);

  const summary = useMemo(() => {
    if (!data) return null;
    return {
      intent: Number(intent.buying_intent_score ?? data.buying_intent_score ?? 0),
      urgency: String(intent.urgency ?? data.urgency ?? "—"),
      stage: String(intent.buying_stage ?? data.buying_stage ?? "—"),
      offer: String(offer.primary_offer ?? data.primary_offer ?? "—"),
      deal: Number(score.deal_probability ?? data.deal_probability ?? 0),
    };
  }, [data, intent, offer, score]);

  if (pack.isLoading) {
    return <Skeleton className="h-72 w-full" />;
  }

  if (pack.isError) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-3">
          <div>
            <SectionLabel>Sales Intelligence</SectionLabel>
            <CardTitle className="font-display text-xl">Not evaluated yet</CardTitle>
            <CardDescription>Run a refresh to compose intent, psychology, offer, and score.</CardDescription>
          </div>
          <Button disabled={refresh.isPending} onClick={() => refresh.mutate()}>
            {refresh.isPending ? "Refreshing…" : "Refresh"}
          </Button>
        </CardHeader>
        <CardContent>
          <ErrorState description="No sales intelligence snapshot for this company." onRetry={() => refresh.mutate()} />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="space-y-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <SectionLabel>Sales Intelligence</SectionLabel>
            <CardTitle className="font-display text-xl">Buyer conversion pack</CardTitle>
            <CardDescription>
              Deterministic composition from Revenue Hunter, Decision Discovery, Opportunity Engine, and Communication Gateway.
            </CardDescription>
          </div>
          <Button disabled={refresh.isPending} onClick={() => refresh.mutate()}>
            {refresh.isPending ? "Refreshing…" : "Refresh"}
          </Button>
        </div>
        {summary ? (
          <div className="flex flex-wrap gap-2">
            <Badge className="bg-muted text-muted-foreground ring-border">Intent {formatScore(summary.intent)}</Badge>
            <Badge className="bg-muted text-muted-foreground ring-border">Urgency {summary.urgency}</Badge>
            <Badge className="bg-muted text-muted-foreground ring-border">Stage {summary.stage}</Badge>
            <Badge className="bg-muted text-muted-foreground ring-border">Offer {summary.offer}</Badge>
            <Badge className="bg-muted text-muted-foreground ring-border">Deal {formatScore(summary.deal)}</Badge>
          </div>
        ) : null}
        <div className="flex flex-wrap gap-2">
          {TABS.map((item) => (
            <Button
              key={item}
              size="sm"
              variant={tab === item ? "default" : "outline"}
              onClick={() => setTab(item)}
            >
              {item}
            </Button>
          ))}
        </div>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        {tab === "Buying Intent" ? (
          <IntentTab intent={intent} />
        ) : null}
        {tab === "Psychology" ? <PsychologyTab psychology={psychology} /> : null}
        {tab === "Objections" ? <ObjectionsTab objections={objections} /> : null}
        {tab === "Offer" ? <OfferTab offer={offer} trust={trust} /> : null}
        {tab === "Proposal" ? <ProposalTab proposal={proposal} /> : null}
        {tab === "Meeting" ? <MeetingTab meeting={meeting} /> : null}
        {tab === "Relationship" ? <RelationshipTab memory={memory} /> : null}
        {tab === "Reply Intelligence" ? <ReplyTab replies={replies} /> : null}
        {tab === "Score" ? <ScoreTab score={score} /> : null}
      </CardContent>
    </Card>
  );
}

function IntentTab({ intent }: { intent: Record<string, unknown> }) {
  const evidence = asList(intent.evidence_chain);
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <Metric label="Intent Score" value={String(intent.buying_intent_score ?? "—")} />
      <Metric label="Buying Stage" value={String(intent.buying_stage ?? "—")} />
      <Metric label="Urgency" value={String(intent.urgency ?? "—")} />
      <Metric label="Budget" value={String(intent.budget_probability ?? "—")} />
      <Metric label="Decision Window" value={`${intent.decision_window_days ?? "—"} Days`} />
      <Metric label="Complexity" value={String(intent.decision_complexity ?? "—")} />
      <Metric label="Buying Confidence" value={String(intent.buying_confidence ?? "—")} />
      <div className="md:col-span-2">
        <p className="mb-2 text-xs uppercase tracking-wide text-muted-foreground">Evidence chain</p>
        {evidence.length ? (
          <ul className="space-y-1 text-muted-foreground">
            {evidence.slice(0, 12).map((item) => (
              <li key={String(item)}>• {String(item)}</li>
            ))}
          </ul>
        ) : (
          <EmptyState title="No evidence" description="Refresh to rebuild the evidence chain." />
        )}
      </div>
    </div>
  );
}

function PsychologyTab({ psychology }: { psychology: Record<string, unknown> }) {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <Metric label="Motivation" value={String(psychology.buyer_motivation ?? "—")} />
      <Metric label="Risk Tolerance" value={String(psychology.risk_tolerance ?? "—")} />
      <Metric label="Innovation" value={String(psychology.innovation_level ?? "—")} />
      <Metric label="Growth Focus" value={String(psychology.growth_focus ?? "—")} />
      <Metric label="Cost Sensitivity" value={String(psychology.cost_sensitivity ?? "—")} />
      <Metric label="Automation Readiness" value={String(psychology.automation_readiness ?? "—")} />
      <Metric label="Pain Intensity" value={String(psychology.pain_intensity ?? "—")} />
      <Metric label="Communication Style" value={String(psychology.preferred_communication_style ?? "—")} />
    </div>
  );
}

function ObjectionsTab({ objections }: { objections: unknown[] }) {
  if (!objections.length) {
    return <EmptyState title="No objections predicted" description="Add replies or pains to improve prediction." />;
  }
  return (
    <div className="space-y-3">
      {objections.map((raw) => {
        const item = asRecord(raw);
        return (
          <div key={String(item.objection)} className="rounded-xl border border-border/60 p-3">
            <div className="flex flex-wrap items-center gap-2">
              <p className="font-medium">{String(item.objection)}</p>
              <Badge className="bg-muted text-muted-foreground ring-border">
                Likelihood {String(item.likelihood)}
              </Badge>
              <Badge className="bg-muted text-muted-foreground ring-border">
                Confidence {String(item.confidence)}
              </Badge>
            </div>
            <p className="mt-2 text-muted-foreground">{String(item.suggested_response)}</p>
          </div>
        );
      })}
    </div>
  );
}

function OfferTab({ offer, trust }: { offer: Record<string, unknown>; trust: Record<string, unknown> }) {
  const cross = asList(offer.cross_sell);
  const cases = asList(trust.case_studies);
  return (
    <div className="space-y-4">
      <div className="grid gap-3 md:grid-cols-2">
        <Metric label="Primary Offer" value={String(offer.primary_offer ?? "—")} />
        <Metric label="Secondary Offer" value={String(offer.secondary_offer ?? "—")} />
        <Metric label="Expected Value" value={String(offer.expected_value ?? "—")} />
        <Metric label="Cross-sell" value={cross.map(String).join(", ") || "—"} />
      </div>
      <div>
        <p className="mb-2 text-xs uppercase tracking-wide text-muted-foreground">Trust assets</p>
        <ul className="space-y-1 text-muted-foreground">
          {cases.slice(0, 6).map((item) => {
            const asset = asRecord(item);
            return <li key={String(asset.title)}>• {String(asset.title)}</li>;
          })}
        </ul>
      </div>
    </div>
  );
}

function ProposalTab({ proposal }: { proposal: Record<string, unknown> }) {
  return (
    <div className="space-y-3">
      <Metric label="Timeline" value={String(proposal.timeline ?? "—")} />
      <Metric label="Budget Range" value={String(proposal.budget_range ?? "—")} />
      <Metric label="ROI Estimate" value={String(proposal.roi_estimate ?? "—")} />
      <ListBlock title="Outline" items={asList(proposal.proposal_outline)} />
      <ListBlock title="Scope" items={asList(proposal.scope)} />
      <ListBlock title="Deliverables" items={asList(proposal.deliverables)} />
      <ListBlock title="Implementation" items={asList(proposal.implementation_plan)} />
    </div>
  );
}

function MeetingTab({ meeting }: { meeting: Record<string, unknown> }) {
  return (
    <div className="space-y-3">
      <p>{String(meeting.company_summary ?? "—")}</p>
      <ListBlock title="Business Pain" items={asList(meeting.business_pain)} />
      <ListBlock title="Buying Signals" items={asList(meeting.buying_signals)} />
      <ListBlock title="Discovery Questions" items={asList(meeting.discovery_questions)} />
      <ListBlock title="Likely Objections" items={asList(meeting.likely_objections)} />
      <Metric label="Closing Strategy" value={String(meeting.closing_strategy ?? "—")} />
      <ListBlock title="Meeting Goals" items={asList(meeting.meeting_goals)} />
      <ListBlock title="Follow-up Plan" items={asList(meeting.follow_up_plan)} />
    </div>
  );
}

function RelationshipTab({ memory }: { memory: Record<string, unknown> }) {
  const timeline = asList(memory.relationship_timeline);
  const journey = asList(memory.buying_journey);
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div>
        <p className="mb-2 text-xs uppercase tracking-wide text-muted-foreground">Relationship timeline</p>
        {timeline.length ? (
          <ul className="space-y-2 text-muted-foreground">
            {timeline.slice(0, 12).map((item, idx) => {
              const row = asRecord(item);
              return (
                <li key={`${row.title}-${idx}`}>
                  <span className="font-medium text-foreground">{String(row.type)}</span> — {String(row.title)}
                </li>
              );
            })}
          </ul>
        ) : (
          <EmptyState title="No timeline yet" description="Emails, replies, and meetings will appear here." />
        )}
      </div>
      <div>
        <p className="mb-2 text-xs uppercase tracking-wide text-muted-foreground">Buying journey</p>
        <ul className="space-y-2">
          {journey.map((item) => {
            const row = asRecord(item);
            return (
              <li key={String(row.stage)} className="flex items-center justify-between rounded-lg border border-border/50 px-3 py-2">
                <span>{String(row.stage)}</span>
                <Badge className="bg-muted text-muted-foreground ring-border">{row.done ? "done" : "open"}</Badge>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

function ReplyTab({ replies }: { replies: unknown[] }) {
  if (!replies.length) {
    return <EmptyState title="No replies classified" description="Inbound replies update this automatically." />;
  }
  return (
    <div className="space-y-3">
      {replies.map((raw, idx) => {
        const item = asRecord(raw);
        return (
          <div key={`${item.classification}-${idx}`} className="rounded-xl border border-border/60 p-3">
            <div className="flex flex-wrap gap-2">
              <Badge className="bg-muted text-muted-foreground ring-border">{String(item.classification)}</Badge>
              <Badge className="bg-muted text-muted-foreground ring-border">
                Confidence {String(item.confidence)}
              </Badge>
            </div>
            <p className="mt-2">{String(item.best_response)}</p>
            <p className="mt-1 text-muted-foreground">{String(item.reason)}</p>
          </div>
        );
      })}
    </div>
  );
}

function ScoreTab({ score }: { score: Record<string, unknown> }) {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <Metric label="Deal Probability" value={String(score.deal_probability ?? "—")} />
      <Metric label="Revenue Probability" value={String(score.revenue_probability ?? "—")} />
      <Metric label="Expected Deal Size" value={String(score.expected_deal_size ?? "—")} />
      <Metric label="Sales Health" value={String(score.sales_health ?? "—")} />
      <Metric label="Relationship Health" value={String(score.relationship_health ?? "—")} />
      <Metric label="Competition Risk" value={String(score.competition_risk ?? "—")} />
      <Metric label="Close Probability" value={String(score.close_probability ?? "—")} />
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border/50 bg-background/40 px-3 py-2">
      <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 font-medium">{value}</p>
    </div>
  );
}

function ListBlock({ title, items }: { title: string; items: unknown[] }) {
  if (!items.length) return null;
  return (
    <div>
      <p className="mb-2 text-xs uppercase tracking-wide text-muted-foreground">{title}</p>
      <ul className="space-y-1 text-muted-foreground">
        {items.slice(0, 10).map((item) => (
          <li key={String(item)}>• {String(item)}</li>
        ))}
      </ul>
    </div>
  );
}

export type { SalesIntelligencePack };
