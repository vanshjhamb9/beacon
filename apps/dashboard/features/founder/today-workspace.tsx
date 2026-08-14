"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useMemo, useState } from "react";

import { CompanyDrawer } from "@/components/company/company-drawer";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge, statusFromLabel } from "@/components/ui/status";
import { beaconApi } from "@/lib/api/beacon";
import { gmailConnectUrl } from "@/lib/founder";
import { indexByCompanyId, mergeLead } from "@/lib/lead";
import { formatScore } from "@/lib/utils";

export function TodayWorkspace() {
  const [drawer, setDrawer] = useState<{
    companyId?: string;
    companyName?: string;
    recordId?: string;
    seed?: Record<string, unknown>;
  } | null>(null);

  const brief = useQuery({
    queryKey: ["clr-daily-brief"],
    queryFn: () => beaconApi.clrDailyBrief(),
    refetchInterval: 60_000,
  });
  const ofc = useQuery({
    queryKey: ["ofc-workspace"],
    queryFn: () => beaconApi.ofcWorkspace(),
  });
  const founderQueue = useQuery({
    queryKey: ["rrp-founder-queue-v4"],
    queryFn: () => beaconApi.rrpFounderQueue(),
  });
  const oauth = useQuery({
    queryKey: ["gmail-oauth-status"],
    queryFn: () => beaconApi.communicationOauthStatus("gmail"),
  });

  const ofcItems = ((ofc.data?.items as Array<Record<string, unknown>>) || []) as Array<Record<string, unknown>>;
  const queueItems = ((founderQueue.data?.items as Array<Record<string, unknown>>) || []) as Array<
    Record<string, unknown>
  >;
  const ofcByCompany = indexByCompanyId(ofcItems);
  const queueByCompany = indexByCompanyId(queueItems);

  const data = brief.data || {};
  const first = (data.contact_first as Record<string, unknown>) || {};
  const targetRaw = ((data.todays_target as Record<string, unknown>) || first) as Record<string, unknown>;
  const priorities = ((data.todays_priority as Array<Record<string, unknown>>) || []).slice(0, 5);
  const followups = ((data.follow_ups_due as Array<Record<string, unknown>>) || []).slice(0, 5);
  const connected = Boolean(oauth.data?.connected);

  const targetLead = useMemo(() => {
    const companyId = String(targetRaw.company_id || first.company_id || priorities[0]?.company_id || "");
    return mergeLead(
      priorities[0],
      first,
      targetRaw,
      companyId ? queueByCompany.get(companyId) : null,
      companyId ? ofcByCompany.get(companyId) : null,
      ofcItems[0],
      queueItems[0],
    );
  }, [targetRaw, first, priorities, queueByCompany, ofcByCompany, ofcItems, queueItems]);

  const queueLeads = useMemo(() => {
    const source = priorities.length
      ? priorities
      : queueItems.slice(0, 5).length
        ? queueItems.slice(0, 5)
        : ofcItems.slice(0, 5);
    return source.map((row) => {
      const id = String(row.company_id || "");
      return mergeLead(row, queueByCompany.get(id), ofcByCompany.get(id));
    });
  }, [priorities, queueItems, ofcItems, queueByCompany, ofcByCompany]);

  if (brief.isLoading && ofc.isLoading) return <Skeleton className="h-80 w-full" />;

  return (
    <div className="mx-auto max-w-5xl space-y-6" id="activity">
      <header className="space-y-2">
        <p className="text-sm text-muted-foreground">What should I do today?</p>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Today</h1>
      </header>

      <Card className="border-status-ready/30 bg-status-ready/5">
        <CardHeader className="border-b-0">
          <p className="text-[11px] uppercase tracking-[0.14em] text-status-ready">Today&apos;s Target</p>
          <CardTitle className="text-2xl">{targetLead.company}</CardTitle>
          <div className="mt-2 flex flex-wrap gap-2">
            <StatusBadge tone={statusFromLabel(targetLead.status)}>{targetLead.status}</StatusBadge>
            {targetLead.confidence > 0 ? (
              <span className="text-xs text-muted-foreground">Score {formatScore(targetLead.confidence, 0)}</span>
            ) : null}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <Fact label="Why now" value={targetLead.whyNow} />
            <Fact label="Decision maker" value={targetLead.decisionMaker} />
            <Fact label="Email" value={targetLead.email || "—"} />
            <Fact label="Service" value={targetLead.service} />
          </div>
          <p className="text-sm text-muted-foreground">Next · {targetLead.nextAction}</p>
          <div className="flex flex-wrap gap-2">
            {!connected ? (
              <Button asChild>
                <a href={gmailConnectUrl()}>Connect Gmail</a>
              </Button>
            ) : (
              <Button asChild>
                <Link href="/outreach">Start Outreach</Link>
              </Button>
            )}
            <Button
              variant="outline"
              onClick={() =>
                setDrawer({
                  companyId: targetLead.companyId,
                  companyName: targetLead.company,
                  recordId: targetLead.recordId,
                  seed: targetLead.raw,
                })
              }
            >
              Open Company
            </Button>
          </div>
        </CardContent>
      </Card>

      <section className="space-y-3">
        <h2 className="font-display text-lg font-semibold">Daily Queue</h2>
        <div className="space-y-2">
          {queueLeads.map((lead, idx) => (
            <div
              key={`${lead.companyId}-${idx}`}
              className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border/60 bg-card/50 px-4 py-3"
            >
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium">
                  #{idx + 1} {lead.company}
                </p>
                <p className="text-xs text-muted-foreground">
                  {lead.decisionMaker} · {lead.email || "No email"}
                </p>
                <p className="mt-1 text-xs text-muted-foreground line-clamp-2">{lead.whyNow}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">{formatScore(lead.confidence, 0)}</span>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() =>
                    setDrawer({
                      companyId: lead.companyId,
                      companyName: lead.company,
                      recordId: lead.recordId,
                      seed: lead.raw,
                    })
                  }
                >
                  Review
                </Button>
              </div>
            </div>
          ))}
          {queueLeads.length === 0 ? (
            <p className="text-sm text-muted-foreground">No companies in today&apos;s queue yet.</p>
          ) : null}
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Follow-ups</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {followups.length === 0 ? (
              <p className="text-muted-foreground">None due.</p>
            ) : (
              followups.map((row, idx) => (
                <p key={idx}>
                  {String(row.company)} · {String(row.days_since_contact)}d
                </p>
              ))
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">All ready leads</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {(queueItems.length ? queueItems : ofcItems).slice(0, 6).map((row, idx) => {
              const lead = mergeLead(row);
              return (
                <button
                  key={`${lead.companyId}-${idx}`}
                  type="button"
                  className="flex w-full items-center justify-between rounded-lg border border-border/50 px-3 py-2 text-left hover:bg-muted/30"
                  onClick={() =>
                    setDrawer({
                      companyId: lead.companyId,
                      companyName: lead.company,
                      recordId: lead.recordId,
                      seed: lead.raw,
                    })
                  }
                >
                  <span>{lead.company}</span>
                  <span className="text-xs text-muted-foreground">{formatScore(lead.confidence, 0)}</span>
                </button>
              );
            })}
          </CardContent>
        </Card>
      </div>

      <CompanyDrawer
        open={Boolean(drawer)}
        onClose={() => setDrawer(null)}
        companyId={drawer?.companyId}
        companyName={drawer?.companyName}
        recordId={drawer?.recordId}
        seed={drawer?.seed}
      />
    </div>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm leading-relaxed">{value}</p>
    </div>
  );
}
