"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

const OUTCOMES = [
  "CONTACTED",
  "EMAIL_SENT",
  "REPLIED",
  "POSITIVE_REPLY",
  "MEETING_BOOKED",
  "PROPOSAL_SENT",
  "NEGOTIATION",
  "WON",
  "LOST",
  "FOLLOW_UP_SENT",
  "NO_RESPONSE",
] as const;

export function RevenueValidationWorkspace() {
  const qc = useQueryClient();
  const [selected, setSelected] = useState<string | null>(null);

  const dash = useQuery({
    queryKey: ["clr-dashboard"],
    queryFn: () => beaconApi.clrDashboard(),
    refetchInterval: 60_000,
  });
  const outcomes = useQuery({
    queryKey: ["clr-outcomes"],
    queryFn: () => beaconApi.clrOutcomes(),
    refetchInterval: 60_000,
  });
  const detail = useQuery({
    queryKey: ["clr-company", selected],
    queryFn: () => beaconApi.clrCompany(selected!),
    enabled: Boolean(selected),
  });

  const sync = useMutation({
    mutationFn: () => beaconApi.clrSync(false),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["clr-dashboard"] });
      void qc.invalidateQueries({ queryKey: ["clr-outcomes"] });
    },
  });

  const transition = useMutation({
    mutationFn: ({ companyId, outcome }: { companyId: string; outcome: string }) =>
      beaconApi.clrTransition(companyId, outcome),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["clr-outcomes"] });
      void qc.invalidateQueries({ queryKey: ["clr-company", selected] });
      void qc.invalidateQueries({ queryKey: ["clr-dashboard"] });
    },
  });

  if (dash.isError) {
    return <ErrorState title="Revenue Validation unavailable" description="API /revenue-validation/dashboard failed." />;
  }

  const today = (dash.data?.today || {}) as Record<string, unknown>;
  const timeline = ((detail.data?.timeline as Array<Record<string, unknown>>) || []) as Array<Record<string, unknown>>;
  const companies = Array.from(
    new Map(
      (((outcomes.data?.items as Array<Record<string, unknown>>) || []) as Array<Record<string, unknown>>).map((o) => [
        String(o.company_id),
        o,
      ]),
    ).values(),
  );

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <SectionLabel>CLR v1 · Closed Loop</SectionLabel>
          <h1 className="text-2xl font-semibold tracking-tight">Revenue Validation</h1>
          <p className="text-sm text-muted-foreground">
            Outcomes, attribution, prediction validation. Append-only. No scoring changes.
          </p>
        </div>
        <Button onClick={() => sync.mutate()} disabled={sync.isPending}>
          {sync.isPending ? "Syncing…" : "Sync from OFC"}
        </Button>
      </div>

      <Card className="border-emerald-700/40 bg-emerald-950/20">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">CTO morning question</CardTitle>
        </CardHeader>
        <CardContent className="text-sm space-y-1">
          <p>{String(dash.data?.question || "")}</p>
          <p className="font-medium">
            Contact {String(today.company || "—")} — {String(today.why || "")}
          </p>
          <p className="text-muted-foreground">{String(dash.data?.learned_yesterday || "")}</p>
        </CardContent>
      </Card>

      {outcomes.isLoading && <Skeleton className="h-32 w-full" />}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Companies with outcomes</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {companies.map((c) => (
              <button
                key={String(c.company_id)}
                type="button"
                className="flex w-full items-center justify-between rounded-md border px-3 py-2 text-left text-sm hover:bg-muted/40"
                onClick={() => setSelected(String(c.company_id))}
              >
                <span>{String(c.company_id).slice(0, 8)}…</span>
                <Badge variant="outline">{String(c.outcome)}</Badge>
              </button>
            ))}
            {companies.length === 0 && <p className="text-sm text-muted-foreground">No outcomes yet — sync.</p>}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Activity Timeline</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {!selected && <p className="text-sm text-muted-foreground">Select a company.</p>}
            {selected && (
              <>
                <div className="flex flex-wrap gap-2">
                  {OUTCOMES.map((outcome) => (
                    <Button
                      key={outcome}
                      size="sm"
                      variant="outline"
                      disabled={transition.isPending}
                      onClick={() => transition.mutate({ companyId: selected, outcome })}
                    >
                      {outcome}
                    </Button>
                  ))}
                </div>
                <div className="space-y-2 text-sm">
                  {timeline.map((t) => (
                    <div key={String(t.id)} className="border-l-2 border-muted pl-3">
                      <p className="font-medium">{String(t.outcome)}</p>
                      <p className="text-xs text-muted-foreground">
                        {String(t.timestamp)} · {String(t.actor)} · {String(t.source)}
                      </p>
                      {t.notes ? <p className="text-xs">{String(t.notes)}</p> : null}
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
