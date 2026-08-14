"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { ArrowRight, Clock, FileText, Mail, RefreshCw, Target, Users, Zap } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { cn, formatScore } from "@/lib/utils";
import { IntelligenceCard } from "@/features/intelligence/intelligence-card";

function greetingForNow(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

export function HomeWorkspace() {
  const queryClient = useQueryClient();

  const overview = useQuery({
    queryKey: ["workspace-overview"],
    queryFn: () => beaconApi.workspaceOverview(),
    refetchInterval: 15_000,
  });

  const syncMutation = useMutation({
    mutationFn: () => beaconApi.workspaceSync(),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["workspace-overview"] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-leads"] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-outreach"] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-analytics"] });
    },
  });

  const discoveryMutation = useMutation({
    mutationFn: async () => {
      await beaconApi.workspaceSync();
      return beaconApi.leadEngineStart({
        product: "comai",
        limit: 25,
        icp: {
          specialties: ["fashion", "beauty", "jewellery", "lifestyle"],
          industries: ["fashion", "beauty", "jewellery", "lifestyle", "ecommerce", "d2c"],
          headquarters_cities: ["Delhi", "Mumbai", "Bangalore", "Bengaluru"],
          countries: ["India"],
          company_types: ["d2c_brand"],
          employee_count_min: 5,
          employee_count_max: 80,
          technology_stack: ["shopify", "woocommerce"],
        },
      });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["workspace-overview"] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-leads"] });
      void queryClient.invalidateQueries({ queryKey: ["lead-engine-runs"] });
    },
  });

  const isLoading = overview.isLoading;
  const data = (overview.data || {}) as Record<string, unknown>;
  const kpisRaw = (data.kpis || {}) as Record<string, number>;
  const stageCounts = (data.stage_counts || {}) as Record<string, number>;
  const topLeads = ((data.top_leads as Array<Record<string, unknown>>) || []) as Array<
    Record<string, unknown>
  >;
  const feed = ((data.feed as Array<Record<string, unknown>>) || []) as Array<Record<string, unknown>>;
  const total = Number(kpisRaw.total_leads || topLeads.length || 0);
  const newCount = Number(kpisRaw.new_today || stageCounts.new || 0);

  const kpis = [
    { label: "New Today", value: String(newCount), icon: Target, color: "text-blue-500" },
    { label: "In Pipeline", value: String(total), icon: Users, color: "text-purple-500" },
    {
      label: "Contacted",
      value: String(kpisRaw.contacted || stageCounts.contacted || 0),
      icon: Mail,
      color: "text-orange-500",
    },
    {
      label: "Replied",
      value: String(kpisRaw.replied || stageCounts.replied || 0),
      icon: FileText,
      color: "text-green-500",
    },
  ];

  if (isLoading) return <Skeleton className="h-96 w-full" />;

  const pipelineTotal =
    (stageCounts.new || 0) +
    (stageCounts.contacted || 0) +
    (stageCounts.replied || 0) +
    (stageCounts.meeting || 0) +
    (stageCounts.won || 0) || 1;

  return (
    <div className="mx-auto max-w-[1400px] space-y-6">
      <motion.section
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="rounded-2xl border border-border/60 bg-[radial-gradient(circle_at_top_left,_rgba(52,211,153,0.12),_transparent_55%),linear-gradient(180deg,_rgba(15,23,42,0.95),_rgba(15,23,42,0.72))] p-6"
      >
        <p className="text-sm text-muted-foreground">{greetingForNow()}, Vansh</p>
        <h1 className="mt-1 font-display text-3xl font-semibold tracking-tight sm:text-4xl">
          Your Sales Dashboard
        </h1>
        <p className="mt-2 max-w-xl text-base text-foreground/90">
          {total > 0
            ? `You have ${total} Lead Engine leads in your pipeline. ${newCount} new leads waiting for review.`
            : "Run discovery to find new mid-D2C leads from Lead Engine."}
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Button onClick={() => discoveryMutation.mutate()} disabled={discoveryMutation.isPending}>
            {discoveryMutation.isPending ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                Discovering...
              </>
            ) : (
              <>
                <Zap className="mr-2 h-4 w-4" />
                Run Discovery
              </>
            )}
          </Button>
          <Button variant="outline" onClick={() => syncMutation.mutate()} disabled={syncMutation.isPending}>
            {syncMutation.isPending ? "Syncing..." : "Sync Workspace"}
          </Button>
          <Button asChild>
            <Link href="/leads">
              View All Leads
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/pipeline">View Pipeline</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/lead-engine">Lead Engine</Link>
          </Button>
        </div>
      </motion.section>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {kpis.map((kpi, idx) => (
          <motion.div
            key={kpi.label}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 * idx, duration: 0.3 }}
          >
            <Card className="border-border/60 bg-card/60">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">{kpi.label}</p>
                    <p className="mt-1 font-display text-3xl font-semibold">{kpi.value}</p>
                  </div>
                  <kpi.icon className={cn("h-8 w-8 opacity-50", kpi.color)} />
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </section>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Pipeline Summary</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex h-3 overflow-hidden rounded-full bg-muted/30">
            {[
              { key: "new", color: "bg-blue-500" },
              { key: "contacted", color: "bg-orange-500" },
              { key: "replied", color: "bg-green-500" },
              { key: "meeting", color: "bg-purple-500" },
              { key: "won", color: "bg-sky-400" },
            ].map((s) => (
              <div
                key={s.key}
                className={cn("h-full", s.color)}
                style={{ width: `${((stageCounts[s.key] || 0) / pipelineTotal) * 100}%` }}
              />
            ))}
          </div>
          <div className="flex flex-wrap gap-4 text-sm">
            {[
              { label: "New", key: "new", color: "bg-blue-500" },
              { label: "Contacted", key: "contacted", color: "bg-orange-500" },
              { label: "Replied", key: "replied", color: "bg-green-500" },
              { label: "Meeting", key: "meeting", color: "bg-purple-500" },
              { label: "Won", key: "won", color: "bg-sky-400" },
            ].map((s) => (
              <div key={s.key} className="flex items-center gap-2">
                <span className={cn("h-2.5 w-2.5 rounded-full", s.color)} />
                <span className="text-muted-foreground">{s.label}:</span>
                <span className="font-medium">{stageCounts[s.key] || 0}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <IntelligenceCard />

      <div className="grid gap-6 lg:grid-cols-[1fr_350px]">
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-display text-lg font-semibold">Today&apos;s New Leads</h2>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/leads">
                View All
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>

          {topLeads.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <Target className="mx-auto h-12 w-12 text-muted-foreground/50" />
                <p className="mt-4 text-muted-foreground">
                  No leads yet. Run discovery or open Lead Engine to find new opportunities.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {topLeads.map((lead, idx) => (
                <motion.div
                  key={String(lead.id || idx)}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.03 * idx, duration: 0.2 }}
                >
                  <Link href={`/leads/${lead.id}`}>
                    <Card className="transition-colors hover:border-primary/50 hover:bg-muted/20">
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{String(lead.company_name || "Unknown")}</span>
                              {!!lead.intent_score && (
                                <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                                  {formatScore(Number(lead.intent_score), 0)}
                                </span>
                              )}
                            </div>
                            <p className="mt-1 line-clamp-1 text-sm text-muted-foreground">
                              {String(lead.why_now || lead.description || "No description")}
                            </p>
                            <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted-foreground">
                              {!!lead.department && (
                                <span className="rounded-md bg-muted/50 px-2 py-0.5">{String(lead.department)}</span>
                              )}
                              {!!lead.industry && (
                                <span className="rounded-md bg-muted/50 px-2 py-0.5">{String(lead.industry)}</span>
                              )}
                              {!!lead.email && (
                                <span className="rounded-md bg-muted/50 px-2 py-0.5">{String(lead.email)}</span>
                              )}
                            </div>
                          </div>
                          <ArrowRight className="h-4 w-4 shrink-0 text-muted-foreground" />
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                </motion.div>
              ))}
            </div>
          )}
        </section>

        <aside>
          <Card className="sticky top-20">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                <Clock className="h-4 w-4" />
                Live Activity
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {feed.length === 0 ? (
                <p className="text-sm text-muted-foreground">No recent activity.</p>
              ) : (
                feed.slice(0, 12).map((item, idx) => (
                  <div key={String(item.id || idx)} className="border-b border-border/40 pb-2 last:border-0">
                    <p className="text-sm font-medium">{String(item.detail || item.event || "Update")}</p>
                    <p className="text-xs text-muted-foreground">{String(item.at || "").replace("T", " ").slice(0, 19)}</p>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </aside>
      </div>
    </div>
  );
}
