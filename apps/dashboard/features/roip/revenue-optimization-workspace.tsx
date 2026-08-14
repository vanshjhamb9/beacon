"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

type Tab =
  | "overview"
  | "email"
  | "whatsapp"
  | "industry"
  | "founder"
  | "offers"
  | "replies"
  | "subjects"
  | "cta"
  | "benchmarks"
  | "learning"
  | "recommendations";

export function RevenueOptimizationWorkspace() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<Tab>("overview");
  const [q, setQ] = useState("");

  const dashboard = useQuery({ queryKey: ["roip-dashboard"], queryFn: () => beaconApi.roipDashboard() });
  const founder = useQuery({ queryKey: ["roip-founder"], queryFn: () => beaconApi.roipFounder() });
  const industry = useQuery({ queryKey: ["roip-industry"], queryFn: () => beaconApi.roipIndustry() });
  const offers = useQuery({ queryKey: ["roip-offers"], queryFn: () => beaconApi.roipOffers() });
  const recommendations = useQuery({
    queryKey: ["roip-recommendations"],
    queryFn: () => beaconApi.roipRecommendations(),
  });
  const benchmarks = useQuery({ queryKey: ["roip-benchmarks"], queryFn: () => beaconApi.roipBenchmarks() });
  const learning = useQuery({ queryKey: ["roip-learning"], queryFn: () => beaconApi.roipLearning() });
  const replies = useQuery({ queryKey: ["roip-replies"], queryFn: () => beaconApi.roipReplies() });
  const search = useQuery({
    queryKey: ["roip-search", q],
    queryFn: () => beaconApi.roipSearch(q ? { q } : {}),
  });

  const refresh = useMutation({
    mutationFn: () => beaconApi.roipRefresh(),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["roip-dashboard"] }),
        queryClient.invalidateQueries({ queryKey: ["roip-founder"] }),
        queryClient.invalidateQueries({ queryKey: ["roip-industry"] }),
        queryClient.invalidateQueries({ queryKey: ["roip-offers"] }),
        queryClient.invalidateQueries({ queryKey: ["roip-recommendations"] }),
        queryClient.invalidateQueries({ queryKey: ["roip-benchmarks"] }),
        queryClient.invalidateQueries({ queryKey: ["roip-learning"] }),
        queryClient.invalidateQueries({ queryKey: ["roip-replies"] }),
        queryClient.invalidateQueries({ queryKey: ["roip-search"] }),
      ]);
    },
  });

  const email = useMemo(() => (dashboard.data?.email as Record<string, unknown>) ?? {}, [dashboard.data]);
  const founderData = founder.data ?? (dashboard.data?.founder as Record<string, unknown>) ?? {};
  const industries = industry.data?.industries ?? (dashboard.data?.industries as Array<Record<string, unknown>>) ?? [];
  const offerRows = offers.data?.offers ?? (dashboard.data?.offers as Array<Record<string, unknown>>) ?? [];
  const recRows =
    recommendations.data?.recommendations ?? (dashboard.data?.recommendations as Array<Record<string, unknown>>) ?? [];
  const benchRows = benchmarks.data?.benchmarks ?? (dashboard.data?.benchmarks as Array<Record<string, unknown>>) ?? [];
  const replyRows = replies.data?.replies?.length
    ? replies.data.replies
    : ((dashboard.data?.replies as Array<Record<string, unknown>>) ?? []);
  const subjects = useMemo(() => {
    const fromSearch = (search.data?.subjects as Array<Record<string, unknown>>) ?? [];
    if (fromSearch.length) return fromSearch.slice(0, 20);
    return ((dashboard.data?.subjects as Array<Record<string, unknown>>) ?? []).slice(0, 20);
  }, [search.data, dashboard.data]);
  const ctas = useMemo(() => ((dashboard.data?.ctas as Array<Record<string, unknown>>) ?? []).slice(0, 20), [dashboard.data]);

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "overview", label: "Overview" },
    { id: "email", label: "Email Analytics" },
    { id: "whatsapp", label: "WhatsApp Analytics" },
    { id: "industry", label: "Industry Analytics" },
    { id: "founder", label: "Founder Analytics" },
    { id: "offers", label: "Offer Performance" },
    { id: "replies", label: "Reply Intelligence" },
    { id: "subjects", label: "Subject Intelligence" },
    { id: "cta", label: "CTA Intelligence" },
    { id: "benchmarks", label: "Benchmarks" },
    { id: "learning", label: "Learning" },
    { id: "recommendations", label: "Recommendations" },
  ];

  if (dashboard.isLoading) return <Skeleton className="h-72 w-full" />;
  if (dashboard.isError) {
    return <ErrorState description="Revenue Optimization unavailable." onRetry={() => void dashboard.refetch()} />;
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <SectionLabel>ROIP v1</SectionLabel>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Revenue Optimization</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
            Deterministic analytics and evidence-backed recommendations. Never auto-applies — founder approval required.
          </p>
        </div>
        <Button disabled={refresh.isPending} onClick={() => refresh.mutate()}>
          Refresh metrics
        </Button>
      </header>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Open Rate" value={`${String(email.open_rate ?? 0)}%`} />
        <Stat label="Reply Rate" value={`${String(email.reply_rate ?? 0)}%`} />
        <Stat label="Revenue" value={String(founderData.revenue ?? 0)} />
        <Stat label="Version" value={String(dashboard.data?.scoring_version ?? "roip-v1")} />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <input
          className="rounded-md border border-border bg-background px-3 py-2 text-sm"
          placeholder="Search industry, offer, subject, reply type…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <Badge variant="outline">Founder approval required</Badge>
      </div>

      <div className="flex flex-wrap gap-2">
        {tabs.map((t) => (
          <Button key={t.id} size="sm" variant={tab === t.id ? "default" : "outline"} onClick={() => setTab(t.id)}>
            {t.label}
          </Button>
        ))}
      </div>

      {tab === "overview" && (
        <div className="grid gap-4 lg:grid-cols-2">
          <ListCard title="Top industries" rows={industries.slice(0, 8)} primary="industry" secondary="close_rate" />
          <ListCard title="Top offers" rows={offerRows.slice(0, 8)} primary="offer" secondary="score" />
          <ListCard title="Recommendations" rows={recRows.slice(0, 8)} primary="title" secondary="confidence" />
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Learning summary</CardTitle>
              <CardDescription>Production is never mutated automatically.</CardDescription>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              {String(learning.data?.summary ?? dashboard.data?.learning_summary ?? "No learning yet.")}
            </CardContent>
          </Card>
        </div>
      )}

      {tab === "email" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Email Performance</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-2 sm:grid-cols-3 text-sm">
            {[
              ["Delivered", email.delivered],
              ["Opened", email.opened],
              ["Multiple opens", email.multiple_opens],
              ["Calendly clicks", email.calendly_clicks],
              ["Website visits", email.website_visits],
              ["Bounce", email.bounce],
              ["Spam", email.spam],
              ["Unsubscribe", email.unsubscribe],
              ["Confidence", email.confidence],
            ].map(([k, v]) => (
              <div key={String(k)}>
                <div className="text-muted-foreground">{k}</div>
                <div className="font-medium">{String(v ?? 0)}</div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {tab === "whatsapp" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">WhatsApp Analytics</CardTitle>
            <CardDescription>Derived from founder channel activity in outreach events.</CardDescription>
          </CardHeader>
          <CardContent className="text-sm">
            Messages: {String(founderData.whatsapp_messages ?? 0)}
          </CardContent>
        </Card>
      )}

      {tab === "industry" && <ListCard title="Industry conversion" rows={industries} primary="industry" secondary="revenue" />}
      {tab === "founder" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Founder Performance</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-2 sm:grid-cols-3 text-sm">
            {[
              ["Companies contacted", founderData.companies_contacted],
              ["Emails sent", founderData.emails_sent],
              ["WhatsApp", founderData.whatsapp_messages],
              ["Meetings booked", founderData.meetings_booked],
              ["Meetings completed", founderData.meetings_completed],
              ["Proposals", founderData.proposals_sent],
              ["Deals closed", founderData.deals_closed],
              ["Revenue", founderData.revenue],
              ["Pipeline health", founderData.pipeline_health],
            ].map(([k, v]) => (
              <div key={String(k)}>
                <div className="text-muted-foreground">{k}</div>
                <div className="font-medium">{String(v ?? 0)}</div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
      {tab === "offers" && <ListCard title="Offer performance" rows={offerRows} primary="offer" secondary="revenue" />}
      {tab === "replies" && <ListCard title="Reply intelligence" rows={replyRows} primary="category" secondary="urgency" />}
      {tab === "subjects" && <ListCard title="Subject intelligence" rows={subjects} primary="subject" secondary="open_rate" />}
      {tab === "cta" && <ListCard title="CTA Intelligence" rows={ctas} primary="cta" secondary="score" />}
      {tab === "benchmarks" && <ListCard title="Benchmarks" rows={benchRows} primary="period" secondary="growth" />}
      {tab === "learning" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Revenue Learning</CardTitle>
            <CardDescription>modifies_production = false</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>{String(learning.data?.summary ?? "—")}</p>
            <p className="text-muted-foreground">Why won: {JSON.stringify(learning.data?.why_won ?? [])}</p>
            <p className="text-muted-foreground">Why lost: {JSON.stringify(learning.data?.why_lost ?? [])}</p>
          </CardContent>
        </Card>
      )}
      {tab === "recommendations" && (
        <ListCard title="Optimization recommendations" rows={recRows} primary="title" secondary="confidence" />
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-2xl">{value}</CardTitle>
      </CardHeader>
    </Card>
  );
}

function ListCard({
  title,
  rows,
  primary,
  secondary,
}: {
  title: string;
  rows: Array<Record<string, unknown>>;
  primary: string;
  secondary: string;
}) {
  if (!rows.length) return <EmptyState title={title} description="No rows yet — refresh metrics." />;
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {rows.slice(0, 25).map((row, idx) => (
          <div key={`${String(row[primary])}-${idx}`} className="flex items-center justify-between gap-3 text-sm">
            <span className="truncate">{String(row[primary] ?? "—")}</span>
            <Badge variant="secondary">{String(row[secondary] ?? "—")}</Badge>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
