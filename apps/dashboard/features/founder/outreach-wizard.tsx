"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check } from "lucide-react";
import { useMemo, useState } from "react";

import { CompanyDrawer } from "@/components/company/company-drawer";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge, statusFromLabel } from "@/components/ui/status";
import { beaconApi } from "@/lib/api/beacon";
import { gmailConnectUrl, OUTREACH_STEPS, outreachStep } from "@/lib/founder";
import { mergeLead } from "@/lib/lead";
import { cn, formatScore } from "@/lib/utils";

export function OutreachWizard() {
  const qc = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [wizardStep, setWizardStep] = useState(0);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const workspace = useQuery({
    queryKey: ["ofc-workspace"],
    queryFn: () => beaconApi.ofcWorkspace(),
    refetchInterval: 60_000,
  });
  const oauth = useQuery({
    queryKey: ["gmail-oauth-status"],
    queryFn: () => beaconApi.communicationOauthStatus("gmail"),
  });
  const detail = useQuery({
    queryKey: ["ofc-record", selectedId],
    queryFn: () => beaconApi.ofcRecord(selectedId!),
    enabled: Boolean(selectedId),
  });

  const sync = useMutation({
    mutationFn: () => beaconApi.ofcSync(),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["ofc-workspace"] }),
  });

  const transition = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => beaconApi.ofcTransition(id, status),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["ofc-workspace"] });
      void qc.invalidateQueries({ queryKey: ["ofc-record", selectedId] });
    },
  });

  const items = useMemo(
    () => ((workspace.data?.items as Array<Record<string, unknown>>) || []) as Array<Record<string, unknown>>,
    [workspace.data],
  );
  const selected = items.find((item) => String(item.id) === selectedId) || items[0] || null;
  const activeId = selected ? String(selected.id) : null;
  const detailRecord = (detail.data as { record?: Record<string, unknown> } | undefined)?.record;
  const lead = mergeLead(selected, detailRecord);
  const connected = Boolean(oauth.data?.connected);
  const currentStep = selected ? Math.max(wizardStep, outreachStep(String(selected.status))) : wizardStep;
  const today = (workspace.data?.today_action || {}) as Record<string, unknown>;

  if (workspace.isError) {
    return <ErrorState title="Outreach unavailable" description="Could not load outreach workspace." />;
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-sm text-muted-foreground">Prospect → Review → Approve → Send → Track → Won</p>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Outreach</h1>
          {today.action ? (
            <p className="mt-1 text-sm text-muted-foreground">{String(today.action)}</p>
          ) : null}
        </div>
        <Button variant="outline" onClick={() => sync.mutate()} disabled={sync.isPending}>
          {sync.isPending ? "Syncing…" : "Refresh prospects"}
        </Button>
      </header>

      <ol className="flex gap-2 overflow-x-auto pb-1 scrollbar-thin">
        {OUTREACH_STEPS.map((step, idx) => {
          const done = idx < currentStep;
          const active = idx === currentStep;
          return (
            <li key={step}>
              <button
                type="button"
                onClick={() => setWizardStep(idx)}
                className={cn(
                  "flex min-w-[110px] items-center gap-2 rounded-xl border px-3 py-2 text-left text-sm transition",
                  active
                    ? "border-primary/40 bg-primary/10 text-foreground"
                    : done
                      ? "border-status-ready/30 bg-status-ready/10 text-status-ready"
                      : "border-border/60 text-muted-foreground",
                )}
              >
                <span
                  className={cn(
                    "flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-semibold",
                    active || done ? "bg-primary text-primary-foreground" : "bg-muted",
                  )}
                >
                  {done ? <Check className="h-3 w-3" /> : idx + 1}
                </span>
                {step}
              </button>
            </li>
          );
        })}
      </ol>

      {workspace.isLoading ? <Skeleton className="h-48 w-full" /> : null}

      <div className="grid gap-4 lg:grid-cols-[300px_1fr]">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Prospects ({items.length})</CardTitle>
          </CardHeader>
          <CardContent className="max-h-[640px] space-y-2 overflow-y-auto scrollbar-thin">
            {items.map((item) => {
              const id = String(item.id);
              const row = mergeLead(item);
              const active = id === (selectedId || activeId);
              return (
                <button
                  key={id}
                  type="button"
                  onClick={() => {
                    setSelectedId(id);
                    setWizardStep(outreachStep(String(item.status)));
                  }}
                  className={cn(
                    "w-full rounded-lg border px-3 py-2.5 text-left transition",
                    active ? "border-primary/40 bg-primary/10" : "border-border/60 hover:bg-muted/30",
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <p className="truncate text-sm font-medium">{row.company}</p>
                    <span className="text-[11px] text-muted-foreground">{formatScore(row.confidence, 0)}</span>
                  </div>
                  <p className="mt-1 truncate text-xs text-muted-foreground">{row.decisionMaker}</p>
                  <div className="mt-1">
                    <StatusBadge tone={statusFromLabel(row.status)}>{row.status}</StatusBadge>
                  </div>
                </button>
              );
            })}
            {items.length === 0 ? (
              <p className="text-sm text-muted-foreground">No prospects yet. Refresh to sync ready companies.</p>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="border-b-0 pb-2">
            <CardTitle className="text-xl">{lead.company}</CardTitle>
            <p className="text-sm text-muted-foreground">
              Step {currentStep + 1}: {OUTREACH_STEPS[currentStep]} · {lead.service}
            </p>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            {!selected ? (
              <p className="text-muted-foreground">Choose a company from the left to begin.</p>
            ) : (
              <>
                <div className="grid gap-3 sm:grid-cols-2">
                  <Field label="Why now" value={lead.whyNow} />
                  <Field label="Pain" value={lead.pain} />
                  <Field label="Decision maker" value={lead.decisionMaker} />
                  <Field label="Email" value={lead.email || "—"} />
                  <Field label="Website" value={lead.website || "—"} />
                  <Field label="CTA" value={lead.cta} />
                </div>
                <Field label="Email draft" value={lead.emailDraft} />
                <Field label="WhatsApp draft" value={lead.whatsappDraft} />
                {lead.evidence.length ? (
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Evidence</p>
                    <ul className="mt-1 list-disc space-y-1 pl-5 text-muted-foreground">
                      {lead.evidence.slice(0, 5).map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                <div className="flex flex-wrap gap-2 pt-2">
                  <Button variant="outline" onClick={() => setDrawerOpen(true)}>
                    Open Company
                  </Button>
                  {!connected ? (
                    <Button asChild>
                      <a href={gmailConnectUrl()}>Connect Gmail</a>
                    </Button>
                  ) : null}
                  {currentStep < 2 ? (
                    <Button onClick={() => setWizardStep(Math.min(5, currentStep + 1))}>Continue</Button>
                  ) : null}
                  {currentStep === 2 && connected ? (
                    <Button
                      disabled={transition.isPending || !activeId}
                      onClick={() => {
                        if (!activeId) return;
                        transition.mutate({ id: activeId, status: "CONTACTED" });
                        setWizardStep(3);
                      }}
                    >
                      Approve & Mark Sent
                    </Button>
                  ) : null}
                  {currentStep >= 3 && currentStep < 5 ? (
                    <Button variant="outline" onClick={() => setWizardStep(Math.min(5, currentStep + 1))}>
                      Next
                    </Button>
                  ) : null}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <CompanyDrawer
        open={drawerOpen && Boolean(selected)}
        onClose={() => setDrawerOpen(false)}
        companyId={lead.companyId}
        companyName={lead.company}
        recordId={activeId}
        seed={lead.raw}
      />
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">{label}</p>
      <p className="mt-1 whitespace-pre-wrap leading-relaxed">{value}</p>
    </div>
  );
}
