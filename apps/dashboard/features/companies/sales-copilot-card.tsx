"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi, type SalesCopilotPackage } from "@/lib/api/beacon";
import { formatDateTime, formatLabel, formatScore, scoreTone } from "@/lib/utils";

const TABS = [
  "Research",
  "Strategy",
  "Email",
  "LinkedIn",
  "WhatsApp",
  "Video Script",
  "Meeting Prep",
  "Versions",
  "Quality Score",
  "Prompt Version",
  "Evidence",
  "Review Status",
] as const;

type Tab = (typeof TABS)[number];

const RESEARCH_KEYS = [
  "executive_summary",
  "company_overview",
  "business_model",
  "current_situation",
  "pain_points",
  "growth_signals",
  "buying_signals",
  "technology_stack",
  "recent_hiring",
  "decision_makers",
];

const STRATEGY_KEYS = [
  "recommended_service",
  "value_proposition",
  "conversation_strategy",
  "opening_angle",
  "things_to_mention",
  "things_to_avoid",
  "possible_objections",
  "suggested_responses",
  "meeting_objectives",
];

export function SalesCopilotCard({ companyId }: { companyId: string }) {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<Tab>("Research");
  const [style, setStyle] = useState("professional");

  const copilot = useQuery({
    queryKey: ["company-copilot", companyId],
    queryFn: () => beaconApi.copilotCompany(companyId),
    retry: false,
  });
  const history = useQuery({
    queryKey: ["company-copilot-history", companyId],
    queryFn: () => beaconApi.copilotHistory(companyId),
    retry: false,
  });

  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ["company-copilot", companyId] });
    await queryClient.invalidateQueries({ queryKey: ["company-copilot-history", companyId] });
  };

  const generate = useMutation({
    mutationFn: () => beaconApi.copilotGenerate(companyId),
    onSuccess: invalidate,
  });
  const regenerate = useMutation({
    mutationFn: () => beaconApi.copilotRegenerate(copilot.data?.id ?? companyId),
    onSuccess: invalidate,
  });
  const review = useMutation({
    mutationFn: (action: string) =>
      beaconApi.copilotReview(copilot.data!.id, { action, reviewer: "operator" }),
    onSuccess: invalidate,
  });

  const styles = useMemo(() => {
    const fromVariants = (copilot.data?.style_variants ?? []).map((item) => item.style);
    if (fromVariants.length) return fromVariants;
    return Array.from(new Set((copilot.data?.drafts ?? []).map((item) => item.style)));
  }, [copilot.data]);

  const draftsForStyle = useMemo(() => {
    const variant = (copilot.data?.style_variants ?? []).find((item) => item.style === style);
    if (variant?.drafts?.length) return variant.drafts;
    return (copilot.data?.drafts ?? []).filter((item) => item.style === style);
  }, [copilot.data, style]);

  const sectionMap = useMemo(() => {
    const map = new Map<string, { title: string; content: string; attribution: Record<string, unknown> }>();
    for (const section of copilot.data?.sections ?? []) {
      map.set(section.key, section);
    }
    return map;
  }, [copilot.data]);

  return (
    <Card>
      <CardHeader className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <CardTitle>AI Sales Copilot</CardTitle>
          <CardDescription>
            Evidence-grounded sales intelligence package for human review — drafts are never sent
          </CardDescription>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            disabled={generate.isPending}
            onClick={() => generate.mutate()}
          >
            {generate.isPending ? "Generating…" : "Generate package"}
          </Button>
          <Button
            variant="outline"
            disabled={!copilot.data || regenerate.isPending}
            onClick={() => regenerate.mutate()}
          >
            {regenerate.isPending ? "Regenerating…" : "Regenerate"}
          </Button>
          <Button
            variant="outline"
            disabled={!copilot.data || review.isPending}
            onClick={() => review.mutate("approve")}
          >
            Approve
          </Button>
          <Button
            variant="outline"
            disabled={!copilot.data || review.isPending}
            onClick={() => review.mutate("reject")}
          >
            Reject
          </Button>
          <Button
            variant="outline"
            disabled={!copilot.data || review.isPending}
            onClick={() => review.mutate("mark_favorite")}
          >
            Favorite
          </Button>
          <Button
            variant="outline"
            disabled={!copilot.data || review.isPending}
            onClick={() => review.mutate("archive")}
          >
            Archive
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {copilot.isError ? (
          <EmptyState
            title="No sales package yet"
            description="Generate a Sales Intelligence Package from verified Beacon engines. Nothing is sent automatically."
            className="py-10"
            action={
              <Button disabled={generate.isPending} onClick={() => generate.mutate()}>
                {generate.isPending ? "Generating…" : "Generate package"}
              </Button>
            }
          />
        ) : copilot.isLoading ? (
          <Skeleton className="h-64 w-full" />
        ) : copilot.data ? (
          <div className="space-y-5">
            <HeaderMeta data={copilot.data} />
            <div className="flex flex-wrap gap-2">
              {TABS.map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => setTab(item)}
                  className={`rounded-md px-3 py-1.5 text-xs transition ${
                    tab === item
                      ? "bg-foreground text-background"
                      : "bg-muted text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {item}
                </button>
              ))}
            </div>

            {(tab === "Email" ||
              tab === "LinkedIn" ||
              tab === "WhatsApp" ||
              tab === "Video Script" ||
              tab === "Meeting Prep") &&
            styles.length ? (
              <div className="flex flex-wrap gap-2">
                {styles.map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => setStyle(item)}
                    className={`rounded-md px-3 py-1.5 text-xs transition ${
                      style === item
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {formatLabel(item)}
                  </button>
                ))}
              </div>
            ) : null}

            {tab === "Research" ? <SectionList keys={RESEARCH_KEYS} sectionMap={sectionMap} /> : null}
            {tab === "Strategy" ? <SectionList keys={STRATEGY_KEYS} sectionMap={sectionMap} /> : null}
            {tab === "Email" ? (
              <DraftBlock
                drafts={draftsForStyle.filter((item) => item.kind === "email" || item.kind === "subject_line")}
              />
            ) : null}
            {tab === "LinkedIn" ? (
              <DraftBlock drafts={draftsForStyle.filter((item) => item.kind === "linkedin")} />
            ) : null}
            {tab === "WhatsApp" ? (
              <DraftBlock drafts={draftsForStyle.filter((item) => item.kind === "whatsapp")} />
            ) : null}
            {tab === "Video Script" ? (
              <DraftBlock drafts={draftsForStyle.filter((item) => item.kind === "video_script")} />
            ) : null}
            {tab === "Meeting Prep" ? (
              <DraftBlock
                drafts={draftsForStyle.filter(
                  (item) =>
                    item.kind === "meeting_agenda" ||
                    item.kind === "discovery_question" ||
                    item.kind.startsWith("follow_up"),
                )}
              />
            ) : null}
            {tab === "Versions" ? (
              history.isError ? (
                <ErrorState description="Unable to load version history." />
              ) : (
                <div className="space-y-2">
                  {(history.data?.results ?? []).map((item) => (
                    <div
                      key={item.id}
                      className="flex flex-wrap items-center justify-between gap-2 border-b border-border/50 py-2 text-sm"
                    >
                      <span>
                        v{item.version} · {formatLabel(item.review_status)}
                        {item.is_favorite ? " · favorite" : ""}
                      </span>
                      <span className="text-muted-foreground">
                        {formatScore(item.quality_overall, 0)} · {formatDateTime(item.created_at)}
                      </span>
                    </div>
                  ))}
                </div>
              )
            ) : null}
            {tab === "Quality Score" ? (
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                {Object.entries(copilot.data.quality).map(([key, value]) => (
                  <div key={key} className="rounded-lg border border-border/60 p-3">
                    <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
                      {formatLabel(key)}
                    </p>
                    <p className={`font-display text-2xl font-semibold ${scoreTone(value)}`}>
                      {formatScore(value, 0)}
                    </p>
                  </div>
                ))}
              </div>
            ) : null}
            {tab === "Prompt Version" ? (
              <div className="space-y-2 text-sm">
                <p>
                  <span className="text-muted-foreground">Prompt:</span>{" "}
                  {copilot.data.generation.prompt_version}
                </p>
                <p>
                  <span className="text-muted-foreground">Provider:</span>{" "}
                  {copilot.data.generation.llm_provider}
                </p>
                <p>
                  <span className="text-muted-foreground">Model:</span> {copilot.data.generation.llm_model}
                </p>
                <p>
                  <span className="text-muted-foreground">Temperature:</span>{" "}
                  {copilot.data.generation.temperature}
                </p>
                <p>
                  <span className="text-muted-foreground">Tokens:</span>{" "}
                  {copilot.data.generation.total_tokens}
                </p>
                <p>
                  <span className="text-muted-foreground">Latency:</span>{" "}
                  {formatScore(copilot.data.generation.latency_ms, 0)} ms
                </p>
                <p>
                  <span className="text-muted-foreground">Cost estimate:</span> $
                  {copilot.data.generation.cost_estimate_usd.toFixed(4)}
                </p>
              </div>
            ) : null}
            {tab === "Evidence" ? (
              <div className="space-y-2">
                {(copilot.data.evidence_chain ?? []).map((item, index) => (
                  <div key={`${item.reference_id || item.summary}-${index}`} className="text-sm">
                    <span className="text-muted-foreground">{formatLabel(String(item.category || "evidence"))}:</span>{" "}
                    {String(item.summary || "Evidence")}
                  </div>
                ))}
              </div>
            ) : null}
            {tab === "Review Status" ? (
              <div className="space-y-2 text-sm">
                <p>
                  Status: <Badge className="bg-muted text-muted-foreground ring-border">{formatLabel(copilot.data.review_status)}</Badge>
                </p>
                <p>Favorite: {copilot.data.is_favorite ? "Yes" : "No"}</p>
                <p>Version: v{copilot.data.version}</p>
                <p className="text-muted-foreground">Created {formatDateTime(copilot.data.created_at)}</p>
              </div>
            ) : null}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function HeaderMeta({ data }: { data: SalesCopilotPackage }) {
  return (
    <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
      <div className="space-y-2">
        <p className="font-display text-xl font-semibold">{data.recommended_service || "Service pending"}</p>
        <p className="text-sm text-muted-foreground">{data.business_pain || "No verified pain captured."}</p>
        <div className="flex flex-wrap gap-2">
          <Badge className="bg-muted text-muted-foreground ring-border">v{data.version}</Badge>
          <Badge className="bg-muted text-muted-foreground ring-border">
            {formatLabel(data.review_status)}
          </Badge>
          <Badge className="bg-muted text-muted-foreground ring-border">
            Quality {formatScore(data.quality.overall, 0)}
          </Badge>
          <Badge className="bg-muted text-muted-foreground ring-border">
            {data.generation.prompt_version}
          </Badge>
        </div>
      </div>
      <p className={`font-display text-3xl font-semibold ${scoreTone(data.opportunity_score)}`}>
        {formatScore(data.opportunity_score, 0)}
      </p>
    </div>
  );
}

function SectionList({
  keys,
  sectionMap,
}: {
  keys: string[];
  sectionMap: Map<string, { title: string; content: string; attribution: Record<string, unknown> }>;
}) {
  return (
    <div className="space-y-4">
      {keys.map((key) => {
        const section = sectionMap.get(key);
        if (!section) return null;
        const summaries = (section.attribution.evidence_summaries as string[] | undefined) ?? [];
        return (
          <div key={key} className="space-y-1 border-b border-border/50 pb-3">
            <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">{section.title}</p>
            <p className="whitespace-pre-wrap text-sm">{section.content}</p>
            {summaries.length ? (
              <p className="text-xs text-muted-foreground">Evidence: {summaries.slice(0, 3).join(" · ")}</p>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

function DraftBlock({
  drafts,
}: {
  drafts: Array<{ title: string; body: string; subject_lines?: string[]; kind: string }>;
}) {
  if (!drafts.length) {
    return <p className="text-sm text-muted-foreground">No draft available for this style.</p>;
  }
  return (
    <div className="space-y-4">
      {drafts.map((draft) => (
        <div key={`${draft.kind}-${draft.title}`} className="space-y-2 rounded-lg border border-border/60 p-4">
          <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">{draft.title}</p>
          {(draft.subject_lines ?? []).length ? (
            <div className="space-y-1 text-sm">
              <p className="text-muted-foreground">Subject lines</p>
              {draft.subject_lines!.map((line) => (
                <p key={line}>{line}</p>
              ))}
            </div>
          ) : null}
          <p className="whitespace-pre-wrap text-sm">{draft.body}</p>
        </div>
      ))}
    </div>
  );
}
