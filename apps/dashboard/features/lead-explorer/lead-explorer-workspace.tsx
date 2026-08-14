"use client";

import { useQuery } from "@tanstack/react-query";
import {
  ArrowDown,
  CheckCircle2,
  Clock3,
  ExternalLink,
  Play,
  Radar,
  RefreshCw,
  Search,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { cn } from "@/lib/utils";

function fmtDuration(seconds: number | null | undefined): string {
  if (seconds == null || Number.isNaN(seconds)) return "—";
  if (seconds < 60) return `${Math.round(seconds)} sec`;
  if (seconds < 3600) return `${Math.round(seconds / 60)} min`;
  return `${(seconds / 3600).toFixed(1)} hr`;
}

export function LeadExplorerWorkspace() {
  const router = useRouter();
  const params = useSearchParams();
  const initialId = params.get("company_id") || params.get("id") || "";
  const [query, setQuery] = useState(params.get("q") || "");
  const [selectedId, setSelectedId] = useState(initialId);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [replayIndex, setReplayIndex] = useState(0);
  const [replaying, setReplaying] = useState(false);

  const search = useQuery({
    queryKey: ["lix-search", query],
    queryFn: () => beaconApi.explorerSearch(query, 25),
    placeholderData: (previous) => previous,
  });

  const company = useQuery({
    queryKey: ["lix-company", selectedId],
    queryFn: () => beaconApi.explorerCompany(selectedId),
    enabled: Boolean(selectedId),
  });

  const contribution = useQuery({
    queryKey: ["lix-contribution"],
    queryFn: beaconApi.explorerContribution,
  });

  useEffect(() => {
    if (!selectedId && search.data?.items?.length) {
      const first = search.data.items[0]?.company_id;
      if (first) setSelectedId(String(first));
    }
  }, [search.data, selectedId]);

  useEffect(() => {
    if (!replaying || !company.data?.replay?.length) return;
    if (replayIndex >= company.data.replay.length - 1) {
      setReplaying(false);
      return;
    }
    const timer = window.setTimeout(() => setReplayIndex((i) => i + 1), 700);
    return () => window.clearTimeout(timer);
  }, [replaying, replayIndex, company.data?.replay]);

  const summary = company.data?.summary;
  const timeline = company.data?.timeline || [];
  const providers = company.data?.providers || [];
  const evidence = company.data?.evidence || [];
  const score = company.data?.score;
  const fields = company.data?.fields || [];
  const stages = company.data?.stages || [];
  const durations = company.data?.stage_durations || [];
  const failure = company.data?.failure;
  const promotion = company.data?.promotion;
  const replay = company.data?.replay || [];
  const selectedEvent = useMemo(
    () => timeline.find((e) => e.id === selectedEventId) || timeline[replayIndex] || timeline[0],
    [timeline, selectedEventId, replayIndex],
  );

  function selectCompany(id: string) {
    setSelectedId(id);
    setReplayIndex(0);
    setReplaying(false);
    setSelectedEventId(null);
    router.replace(`/lead-explorer?company_id=${id}${query ? `&q=${encodeURIComponent(query)}` : ""}`);
  }

  return (
    <div className="mx-auto flex max-w-[1600px] flex-col gap-6 pb-10">
      <header className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div className="space-y-2">
          <SectionLabel>LIX v1</SectionLabel>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Lead Intelligence Explorer</h1>
          <p className="max-w-3xl text-sm text-muted-foreground">
            Replay any lead from first signal to Revenue Ready. No GPT. No new scoring — pure observability.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              void search.refetch();
              void company.refetch();
              void contribution.refetch();
            }}
          >
            <RefreshCw className="mr-2 h-4 w-4" /> Refresh
          </Button>
          <Button
            size="sm"
            disabled={!selectedId || !replay.length}
            onClick={() => {
              setReplayIndex(0);
              setReplaying(true);
            }}
          >
            <Play className="mr-2 h-4 w-4" /> Replay
          </Button>
        </div>
      </header>

      <Card className="border-border/60 bg-card/40">
        <CardContent className="flex flex-col gap-3 pt-6 md:flex-row md:items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="pl-9"
              placeholder="Search by company, domain, email, founder, lead ID, revenue ready ID"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <p className="text-xs text-muted-foreground">Instant lookup · {search.data?.count ?? 0} matches</p>
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[320px_1fr]">
        <Card className="border-border/60 bg-card/40">
          <CardHeader>
            <CardTitle className="text-base">Results</CardTitle>
            <CardDescription>Click a company to open its full lifecycle</CardDescription>
          </CardHeader>
          <CardContent className="max-h-[720px] space-y-2 overflow-y-auto">
            {search.isLoading && <Skeleton className="h-24 w-full" />}
            {search.isError && (
              <ErrorState title="Search failed" description="GET /explorer/search unavailable" />
            )}
            {(search.data?.items || []).map((item) => (
              <button
                key={String(item.company_id)}
                type="button"
                onClick={() => selectCompany(String(item.company_id))}
                className={cn(
                  "w-full rounded-xl border px-3 py-3 text-left transition",
                  selectedId === item.company_id
                    ? "border-primary/50 bg-primary/10"
                    : "border-border/50 hover:border-primary/30",
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="truncate font-medium">{String(item.company || "—")}</p>
                  {item.revenue_ready ? (
                    <Badge className="bg-emerald-600 text-white">RR</Badge>
                  ) : (
                    <Badge variant="outline">{String(item.current_stage || "—")}</Badge>
                  )}
                </div>
                <p className="truncate text-xs text-muted-foreground">{String(item.domain || "—")}</p>
                <p className="truncate text-xs text-muted-foreground">
                  {String(item.founder || "—")} · {String(item.email || "—")}
                </p>
              </button>
            ))}
          </CardContent>
        </Card>

        <div className="space-y-6">
          {!selectedId ? (
            <Card className="border-border/60 bg-card/40">
              <CardContent className="py-16 text-center text-muted-foreground">
                Select a company to inspect its explainable lifecycle.
              </CardContent>
            </Card>
          ) : company.isLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : company.isError ? (
            <ErrorState
              title="Lead Explorer unavailable"
              description="Confirm migration 20260727_0049 and API /explorer/company."
              onRetry={() => void company.refetch()}
            />
          ) : (
            <>
              <Card className="border-border/60 bg-card/40">
                <CardHeader>
                  <CardTitle className="flex flex-wrap items-center gap-3">
                    <span>{String(summary?.company || "Company")}</span>
                    {summary?.revenue_ready ? (
                      <Badge className="bg-emerald-600 text-white">Revenue Ready</Badge>
                    ) : (
                      <Badge variant="secondary">{String(summary?.current_stage || "—")}</Badge>
                    )}
                  </CardTitle>
                  <CardDescription>
                    {String(summary?.domain || "—")} · Source {String(summary?.source || "—")}
                  </CardDescription>
                </CardHeader>
                <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  <Metric label="Current Stage" value={String(summary?.current_stage || "—")} />
                  <Metric label="Current Score" value={String(summary?.current_score ?? "—")} />
                  <Metric label="Confidence" value={String(summary?.confidence ?? "—")} />
                  <Metric label="Trust" value={String(summary?.trust ?? "—")} />
                  <Metric label="Pipeline Value" value={String(summary?.pipeline_value ?? 0)} />
                  <Metric label="Created" value={formatTime(summary?.created_at)} />
                  <Metric label="Last Updated" value={formatTime(summary?.last_updated)} />
                  <Metric label="Lead ID" value={String(summary?.lead_id || selectedId).slice(0, 8)} />
                </CardContent>
              </Card>

              {failure && (
                <Card className="border-rose-500/40 bg-rose-500/5">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base text-rose-200">
                      <XCircle className="h-4 w-4" /> Rejected
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-1 text-sm">
                    <p>Stage: {String(failure.rejected_stage || "unknown")}</p>
                    {(failure.reasons || []).map((reason) => (
                      <p key={reason} className="text-muted-foreground">
                        · {reason}
                      </p>
                    ))}
                  </CardContent>
                </Card>
              )}

              {promotion && (
                <Card className="border-border/60 bg-card/40">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <ShieldCheck className="h-4 w-4" /> Stage Decision / Promotion
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="text-sm">
                    <p className="font-medium">{String(promotion.reason || "—")}</p>
                    <p className="mt-2 text-muted-foreground">
                      Passed: {(promotion.passed || []).join(", ") || "—"}
                    </p>
                    <p className="text-muted-foreground">
                      Missing: {(promotion.missing || []).join(", ") || "none"}
                    </p>
                  </CardContent>
                </Card>
              )}

              <div className="grid gap-6 xl:grid-cols-2">
                <Card className="border-border/60 bg-card/40">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Radar className="h-4 w-4" /> Complete Timeline
                    </CardTitle>
                    <CardDescription>Git-history style · every event clickable</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-0">
                    {timeline.length === 0 && (
                      <p className="text-sm text-muted-foreground">No timeline events yet. Run sync.</p>
                    )}
                    {timeline.map((event, index) => {
                      const active =
                        (replaying && replay[replayIndex]?.focus?.id === event.id) ||
                        selectedEventId === event.id;
                      return (
                        <button
                          key={event.id || `${event.event_type}-${index}`}
                          type="button"
                          onClick={() => setSelectedEventId(event.id)}
                          className={cn(
                            "flex w-full gap-3 border-l-2 px-3 py-3 text-left transition",
                            active ? "border-primary bg-primary/5" : "border-border/60 hover:bg-muted/20",
                          )}
                        >
                          <div className="w-16 shrink-0 text-xs tabular-nums text-muted-foreground">
                            {formatClock(event.occurred_at)}
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="text-sm font-medium">{event.label || event.headline || event.event_type}</p>
                            <p className="truncate text-xs text-muted-foreground">
                              {event.connector || event.provider || "—"} · {event.stage || "—"}
                            </p>
                          </div>
                        </button>
                      );
                    })}
                    {selectedEvent && (
                      <div className="mt-4 rounded-xl border border-border/60 p-3 text-sm">
                        <p className="font-medium">{selectedEvent.label}</p>
                        <p className="text-muted-foreground">{selectedEvent.detail || "No detail"}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card className="border-border/60 bg-card/40">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Clock3 className="h-4 w-4" /> Live Stage Duration
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {durations.map((d, index) => (
                      <div key={d.stage} className="flex items-center gap-2 text-sm">
                        <div className="min-w-0 flex-1 rounded-lg border border-border/50 px-3 py-2">
                          <div className="flex justify-between gap-2">
                            <span>{d.label}</span>
                            <span className="tabular-nums text-muted-foreground">
                              {fmtDuration(d.duration_seconds as number | null)}
                            </span>
                          </div>
                        </div>
                        {index < durations.length - 1 && <ArrowDown className="h-3 w-3 text-muted-foreground" />}
                      </div>
                    ))}
                    {durations.length === 0 && (
                      <p className="text-sm text-muted-foreground">Durations appear after stage history sync.</p>
                    )}
                  </CardContent>
                </Card>
              </div>

              <div className="grid gap-6 xl:grid-cols-2">
                <Card className="border-border/60 bg-card/40">
                  <CardHeader>
                    <CardTitle className="text-base">Score Breakdown</CardTitle>
                    <CardDescription>Explains the existing score — does not rescore</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    {(score?.components || []).map((c) => (
                      <div key={c.key} className="flex items-center justify-between border-b border-border/40 py-2">
                        <span className={cn(!c.present && "text-muted-foreground")}>{c.label}</span>
                        <span className="tabular-nums font-medium">
                          {c.present ? `+${c.points}` : "+0"}
                        </span>
                      </div>
                    ))}
                    <div className="flex justify-between pt-2 text-base font-semibold">
                      <span>Total</span>
                      <span className="tabular-nums">{score?.total ?? "—"}</span>
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-border/60 bg-card/40">
                  <CardHeader>
                    <CardTitle className="text-base">Evidence Chain</CardTitle>
                    <CardDescription>Why Beacon trusts this company</CardDescription>
                  </CardHeader>
                  <CardContent className="grid gap-2 sm:grid-cols-2">
                    {evidence.map((item) => (
                      <a
                        key={item.id || item.label}
                        href={item.url || undefined}
                        target={item.url ? "_blank" : undefined}
                        rel="noreferrer"
                        className="rounded-lg border border-border/50 px-3 py-2 text-sm hover:border-primary/40"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-medium">{item.label}</span>
                          {item.url ? <ExternalLink className="h-3 w-3" /> : null}
                        </div>
                        <p className="text-xs text-muted-foreground">{item.provider}</p>
                      </a>
                    ))}
                    {evidence.length === 0 && (
                      <p className="text-sm text-muted-foreground">No evidence recorded yet.</p>
                    )}
                  </CardContent>
                </Card>
              </div>

              <Card className="border-border/60 bg-card/40">
                <CardHeader>
                  <CardTitle className="text-base">Provider History</CardTitle>
                  <CardDescription>Reserved slots for Hunter, Apollo, LinkedIn, PDL, and more</CardDescription>
                </CardHeader>
                <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                  {providers.map((p) => (
                    <div key={p.provider} className="rounded-xl border border-border/50 p-3 text-sm">
                      <div className="flex items-center justify-between gap-2">
                        <p className="font-medium">{p.label}</p>
                        <Badge variant="outline">{String(p.status)}</Badge>
                      </div>
                      <p className="mt-2 text-muted-foreground">Latency: {p.latency_ms ?? "—"} ms</p>
                      <p className="text-muted-foreground">
                        Fields: {(p.fields_added || []).join(", ") || "—"}
                      </p>
                      <p className="text-muted-foreground">Credits: {p.credits_used ?? "—"}</p>
                      <p className="text-muted-foreground">
                        Success: {p.success == null ? "—" : p.success ? "Yes" : "No"} · Confidence:{" "}
                        {p.confidence ?? "—"}
                      </p>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <div className="grid gap-6 xl:grid-cols-2">
                <Card className="border-border/60 bg-card/40">
                  <CardHeader>
                    <CardTitle className="text-base">Field History</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 text-sm">
                    {fields.map((f) => (
                      <div key={f.id || `${f.field_name}-${f.occurred_at}`} className="border-b border-border/40 pb-3">
                        <p className="font-medium capitalize">{f.field_name}</p>
                        <p>{String(f.field_value || "—")}</p>
                        <p className="text-xs text-muted-foreground">
                          Added by {f.provider} · {formatTime(f.occurred_at)} · Confidence {f.confidence}
                        </p>
                      </div>
                    ))}
                    {fields.length === 0 && (
                      <p className="text-muted-foreground">No field provenance yet.</p>
                    )}
                  </CardContent>
                </Card>

                <Card className="border-border/60 bg-card/40">
                  <CardHeader>
                    <CardTitle className="text-base">Stage Decisions</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    {stages.map((s) => (
                      <div key={s.stage} className="flex items-start justify-between gap-3 rounded-lg border border-border/50 px-3 py-2">
                        <div>
                          <p className="font-medium">{s.label}</p>
                          <p className="text-muted-foreground">{s.reason || "—"}</p>
                        </div>
                        {s.status === "passed" ? (
                          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                        ) : s.status === "rejected" || s.status === "failed" ? (
                          <XCircle className="h-4 w-4 text-rose-400" />
                        ) : (
                          <Badge variant="outline">{s.status}</Badge>
                        )}
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </div>

              {replaying && replay[replayIndex] && (
                <Card className="border-primary/40 bg-primary/5">
                  <CardHeader>
                    <CardTitle className="text-base">Lead Replay</CardTitle>
                    <CardDescription>
                      Frame {replayIndex + 1} / {replay.length}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="text-sm">
                    <p className="font-medium">{replay[replayIndex]?.focus?.label}</p>
                    <p className="text-muted-foreground">{replay[replayIndex]?.focus?.detail}</p>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>
      </div>

      <Card className="border-border/60 bg-card/40">
        <CardHeader>
          <CardTitle className="text-base">Connector Contribution</CardTitle>
          <CardDescription>Which provider created the most Revenue Ready companies</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {(contribution.data?.items || []).map((row) => (
            <div key={row.provider} className="rounded-xl border border-border/50 p-3 text-sm">
              <p className="font-medium">{row.label}</p>
              <p className="text-muted-foreground">Companies {row.companies_affected}</p>
              <p className="text-muted-foreground">Emails {row.emails_added}</p>
              <p className="text-muted-foreground">DM {row.dm_added}</p>
              <p className="text-muted-foreground">Revenue Ready {row.revenue_ready_created}</p>
              <p className="text-muted-foreground">Success {row.success_pct}%</p>
            </div>
          ))}
          {(contribution.data?.providers || [])
            .filter((p) => ["apollo", "linkedin", "people_data_labs"].includes(String(p.provider)))
            .map((p) => (
              <div key={`reserved-${p.provider}`} className="rounded-xl border border-dashed border-border/50 p-3 text-sm">
                <p className="font-medium">{p.label}</p>
                <p className="text-muted-foreground">{String(p.status).replaceAll("_", " ")}</p>
              </div>
            ))}
          {!contribution.data?.items?.length && (
            <p className="text-sm text-muted-foreground">
              Contribution fills after{" "}
              <button
                type="button"
                className="underline"
                onClick={() => void beaconApi.explorerSync().then(() => contribution.refetch())}
              >
                sync
              </button>
              .
            </p>
          )}
        </CardContent>
      </Card>

      <p className="text-xs text-muted-foreground">
        Deep links: Operations / Revenue Ready / Analytics companies open here via{" "}
        <Link className="underline" href="/lead-explorer">
          /lead-explorer?company_id=…
        </Link>
      </p>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border/50 p-3">
      <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">{label}</p>
      <p className="mt-1 truncate text-lg font-semibold tabular-nums">{value}</p>
    </div>
  );
}

function formatTime(value: unknown): string {
  if (!value) return "—";
  const d = new Date(String(value));
  if (Number.isNaN(d.getTime())) return String(value);
  return d.toLocaleString();
}

function formatClock(value: unknown): string {
  if (!value) return "--:--";
  const d = new Date(String(value));
  if (Number.isNaN(d.getTime())) return "--:--";
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
