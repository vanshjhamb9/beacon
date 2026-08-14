"use client";

import { useQuery } from "@tanstack/react-query";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { CommunicationReadinessCard, CampaignExecutionBanner } from "@/features/execution-readiness/communication-readiness-card";
import { beaconApi } from "@/lib/api/beacon";

export function DailyBriefWorkspace() {
  const brief = useQuery({
    queryKey: ["clr-daily-brief"],
    queryFn: () => beaconApi.clrDailyBrief(),
    refetchInterval: 60_000,
  });

  if (brief.isError) {
    return <ErrorState title="Daily Brief unavailable" description="API /revenue-validation/daily-brief failed." />;
  }
  if (brief.isLoading) return <Skeleton className="h-48 w-full" />;

  const data = brief.data || {};
  const priorities = (data.todays_priority as Array<Record<string, unknown>>) || [];
  const followups = (data.follow_ups_due as Array<Record<string, unknown>>) || [];
  const yesterday = (data.yesterday_summary as Record<string, unknown>) || {};
  const first = (data.contact_first as Record<string, unknown>) || {};

  const target = (data.todays_target as Record<string, unknown>) || first;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <SectionLabel>CLR v1 · er-v1</SectionLabel>
        <h1 className="text-2xl font-semibold tracking-tight">Daily Brief</h1>
        <p className="text-sm text-muted-foreground">{String(data.question || "")}</p>
      </div>

      <CampaignExecutionBanner />
      <CommunicationReadinessCard />

      <Card className="border-emerald-700/40 bg-emerald-950/20">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Today&apos;s Target</CardTitle>
        </CardHeader>
        <CardContent className="space-y-1 text-sm">
          <p className="text-base font-medium">{String(target.company || first.company || "—")}</p>
          <p>
            <span className="text-muted-foreground">Status · </span>
            {String(target.status || first.status || "READY TO SEND")}
          </p>
          <p className="text-muted-foreground">{String(target.reason || first.reason || first.why || "")}</p>
          <p>Email · {String(first.email || "—")}</p>
          <p>Next Action · {String(target.next_action || first.next_action || first.next_step || "—")}</p>
          <p>Tracking · {String(target.tracking || first.tracking || "Disabled until first successful delivery.")}</p>
          <p className="pt-2 text-muted-foreground">{String(data.learned_yesterday || "")}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Today&apos;s Priority — Top 5</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {priorities.map((p, i) => (
            <div key={`${p.company_id}-${i}`} className="border-b border-border/60 pb-2 text-sm last:border-0">
              <p className="font-medium">
                #{i + 1} {String(p.company)}
              </p>
              <p className="text-muted-foreground">{String(p.decision_maker)} · {String(p.email || "—")}</p>
              <p>Why · {String(p.why_today)}</p>
              <p>Next · {String(p.suggested_next_step)}</p>
            </div>
          ))}
          {priorities.length === 0 && <p className="text-sm text-muted-foreground">Sync CLR after OFC.</p>}
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        <ListCard title="Follow-ups Due" rows={followups.map((f) => `${f.company} · ${f.days_since_contact}d · ${f.priority}`)} />
        <ListCard
          title="Meetings Today"
          rows={((data.meetings_today as Array<Record<string, unknown>>) || []).map((m) => String(m.company))}
        />
        <ListCard
          title="Replies Waiting"
          rows={((data.replies_waiting as Array<Record<string, unknown>>) || []).map((m) => String(m.company))}
        />
        <ListCard
          title="Proposals Pending"
          rows={((data.proposals_pending as Array<Record<string, unknown>>) || []).map((m) => String(m.company))}
        />
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Yesterday Summary</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-3 gap-2 text-sm sm:grid-cols-6">
          {["replies", "meetings", "wins", "losses", "pipeline_added", "revenue_added"].map((k) => (
            <div key={k}>
              <p className="text-xs text-muted-foreground">{k.replace("_", " ")}</p>
              <p className="font-semibold">{String(yesterday[k] ?? 0)}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function ListCard({ title, rows }: { title: string; rows: string[] }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-1 text-sm">
        {rows.length === 0 && <p className="text-muted-foreground">None</p>}
        {rows.map((r) => (
          <p key={r}>{r}</p>
        ))}
      </CardContent>
    </Card>
  );
}
