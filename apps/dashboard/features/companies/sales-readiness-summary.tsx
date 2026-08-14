"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { formatLabel, formatPercent, formatScore, scoreTone } from "@/lib/utils";

function stars(n: number) {
  return "★".repeat(Math.max(0, Math.min(5, n))) + "☆".repeat(Math.max(0, 5 - Math.max(0, Math.min(5, n))));
}

function Attr({
  label,
  value,
  source,
  collected,
  confidence,
  evidence,
}: {
  label: string;
  value?: unknown;
  source?: unknown;
  collected?: unknown;
  confidence?: unknown;
  evidence?: unknown;
}) {
  const display = value == null || value === "" || value === "UNKNOWN" ? "UNKNOWN" : String(value);
  return (
    <div className="rounded-lg border border-border/60 p-3">
      <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">{label}</p>
      <p className="mt-1 font-medium">{display}</p>
      <div className="mt-2 flex flex-wrap gap-1 text-[11px] text-muted-foreground">
        <span>Source {String(source ?? "UNKNOWN")}</span>
        <span>·</span>
        <span>Collected {String(collected ?? "UNKNOWN").slice(0, 16)}</span>
        <span>·</span>
        <span>
          Confidence{" "}
          {confidence == null || confidence === "UNKNOWN" ? "UNKNOWN" : formatPercent(Number(confidence) > 1 ? Number(confidence) / 100 : Number(confidence))}
        </span>
      </div>
      {Array.isArray(evidence) && evidence.length > 0 ? (
        <p className="mt-1 text-[11px] text-muted-foreground">Evidence: {evidence.slice(0, 3).map(String).join(" · ")}</p>
      ) : null}
    </div>
  );
}

export function SalesReadinessExecutiveSummary({ companyId }: { companyId: string }) {
  const queryClient = useQueryClient();
  const sre = useQuery({
    queryKey: ["sre-company", companyId],
    queryFn: () => beaconApi.sreCompany(companyId),
    retry: false,
  });
  const evaluate = useMutation({
    mutationFn: () => beaconApi.sreEvaluate(companyId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["sre-company", companyId] });
    },
  });

  if (sre.isLoading) return <Skeleton className="h-64 w-full" />;
  if (sre.isError || !sre.data) {
    return (
      <EmptyState
        title="Sales readiness unavailable"
        description="Evaluate this company through the Sales Readiness Engine."
        action={
          <Button disabled={evaluate.isPending} onClick={() => evaluate.mutate()}>
            {evaluate.isPending ? "Evaluating…" : "Evaluate sales readiness"}
          </Button>
        }
      />
    );
  }

  const d = sre.data as Record<string, any>;
  const identityFields = (d.identity?.fields ?? {}) as Record<string, any>;
  const services = (d.services ?? []) as Array<Record<string, any>>;
  const roles = (d.contacts?.roles ?? []) as Array<Record<string, any>>;
  const signals = (d.recent_signals ?? []) as Array<Record<string, any>>;
  const timeline = (d.evidence_timeline ?? []) as Array<Record<string, any>>;

  return (
    <Card className="border-border/70 shadow-soft">
      <CardHeader className="gap-3">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-2">
            <SectionLabel>Sales Readiness</SectionLabel>
            <h2 className="font-display text-3xl font-semibold tracking-tight">{String(d.company_name)}</h2>
            <div className="flex flex-wrap gap-2">
              <Badge>{String(d.status)}</Badge>
              <Badge variant="outline" className={scoreTone(Number(d.trust_score ?? 0))}>
                Trust {formatScore(Number(d.trust_score ?? 0), 0)}%
              </Badge>
              <Badge variant="outline">{stars(Number(d.stars ?? 0))}</Badge>
              {d.visible_in_founder_queue ? <Badge>Founder Queue</Badge> : <Badge variant="outline">Hidden from Founder Queue</Badge>}
              {d.eligible_for_revenue_hunter ? <Badge>Revenue Hunter</Badge> : <Badge variant="outline">Not RH eligible</Badge>}
            </div>
          </div>
          <Button variant="outline" disabled={evaluate.isPending} onClick={() => evaluate.mutate()}>
            {evaluate.isPending ? "Evaluating…" : "Re-evaluate"}
          </Button>
        </div>
        <CardDescription>
          Next action: {String(d.next_action ?? "UNKNOWN")} · Outreach: {String(d.outreach?.status ?? "UNKNOWN")}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <Attr label="Identity" value={d.identity?.identity_complete ? "Complete" : "Incomplete"} source="sales_readiness.identity" evidence={d.identity?.missing_fields} />
          <Attr
            label="Website"
            value={identityFields.website?.value ?? d.website?.grade}
            source={identityFields.website?.source}
            collected={identityFields.website?.collected_at}
            confidence={identityFields.website?.confidence}
            evidence={d.website?.evidence}
          />
          <Attr
            label="Industry"
            value={identityFields.industry?.value}
            source={identityFields.industry?.source}
            collected={identityFields.industry?.collected_at}
            confidence={identityFields.industry?.confidence}
          />
          <Attr
            label="Country"
            value={identityFields.country?.value}
            source={identityFields.country?.source}
            collected={identityFields.country?.collected_at}
            confidence={identityFields.country?.confidence}
          />
        </div>

        <div className="grid gap-3 lg:grid-cols-2">
          <div>
            <p className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Buying Intent</p>
            <div className="rounded-lg border border-border/60 p-3">
              <p className="font-medium">{String(d.intent?.level ?? "UNKNOWN")}</p>
              <p className="text-sm text-muted-foreground">Score {formatScore(Number(d.intent?.score ?? 0), 0)}</p>
              <div className="mt-2 flex flex-wrap gap-1">
                {signals.slice(0, 6).map((s, i) => (
                  <Badge key={i} variant="outline">
                    {String(s.value)}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
          <div>
            <p className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Revenue Potential</p>
            <div className="rounded-lg border border-border/60 p-3 text-sm text-muted-foreground">
              <div className="flex justify-between"><span>Deal size</span><span className="text-foreground">{String(d.revenue?.deal_size ?? "UNKNOWN")}</span></div>
              <div className="flex justify-between"><span>Probability</span><span className="text-foreground">{formatScore(Number(d.revenue?.probability ?? 0), 0)}%</span></div>
              <div className="flex justify-between"><span>Sales cycle</span><span className="text-foreground">{String(d.revenue?.sales_cycle ?? "UNKNOWN")}</span></div>
              <div className="flex justify-between"><span>Founder time</span><span className="text-foreground">{String(d.revenue?.recommended_founder_time ?? "UNKNOWN")}</span></div>
            </div>
          </div>
        </div>

        <div>
          <p className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Recommended Services</p>
          {services.length === 0 ? (
            <p className="text-sm text-muted-foreground">UNKNOWN — no evidence-backed service match yet.</p>
          ) : (
            <div className="grid gap-2 md:grid-cols-2">
              {services.map((svc) => (
                <div key={String(svc.recommended_service)} className="rounded-lg border border-border/60 p-3">
                  <p className="font-medium">{String(svc.recommended_service)}</p>
                  <p className="text-sm text-muted-foreground">{String(svc.estimated_value ?? "UNKNOWN")}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{(svc.reason ?? []).slice(0, 3).map(String).join(" · ")}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          <p className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
            Decision Makers · Coverage {formatScore(Number(d.contacts?.coverage_percent ?? 0), 0)}%
          </p>
          <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
            {roles
              .filter((r) => r.name && r.name !== "UNKNOWN")
              .slice(0, 6)
              .map((r) => (
                <div key={String(r.role)} className="rounded-lg border border-border/60 p-3 text-sm">
                  <p className="font-medium">
                    {String(r.role)} · {String(r.name)}
                  </p>
                  <p className="text-muted-foreground">Email {String(r.verified_email?.value ?? "UNKNOWN")}</p>
                  <p className="text-muted-foreground">Phone {String(r.verified_phone?.value ?? "UNKNOWN")}</p>
                  <p className="text-muted-foreground">LinkedIn {String(r.linkedin?.value ?? "UNKNOWN")}</p>
                </div>
              ))}
            {roles.filter((r) => r.name && r.name !== "UNKNOWN").length === 0 ? (
              <p className="text-sm text-muted-foreground">UNKNOWN — no verified decision makers observed.</p>
            ) : null}
          </div>
        </div>

        <div className="grid gap-3 lg:grid-cols-2">
          <div>
            <p className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Evidence Timeline</p>
            <div className="space-y-2">
              {timeline.slice(0, 5).map((ev, i) => (
                <div key={i} className="rounded-lg border border-border/60 p-2 text-xs text-muted-foreground">
                  <Badge variant="outline">{String(ev.source ?? "UNKNOWN")}</Badge> {String(ev.value ?? "")}
                </div>
              ))}
              {timeline.length === 0 ? <p className="text-sm text-muted-foreground">UNKNOWN</p> : null}
            </div>
          </div>
          <div>
            <p className="mb-2 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Suggested First Message</p>
            <p className="rounded-lg border border-border/60 p-3 text-sm text-muted-foreground">
              {String(d.suggested_first_message ?? "UNKNOWN")}
            </p>
            <p className="mt-3 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Technology maturity</p>
            <p className="text-sm">{formatScore(Number(d.technology?.maturity_score ?? 0), 0)} · Website grade {String(d.website?.grade ?? "F")}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
