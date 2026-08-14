"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { BarChart3, TrendingUp, Users, Zap } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { cn } from "@/lib/utils";

export function AnalyticsWorkspace() {
  const { data, isLoading } = useQuery({
    queryKey: ["workspace-analytics"],
    queryFn: () => beaconApi.workspaceAnalytics(),
    refetchInterval: 20_000,
  });

  if (isLoading) return <Skeleton className="h-96 w-full" />;

  const kpis = (data?.kpis || {}) as Record<string, number>;
  const stageCounts = (data?.stage_counts || data?.pipeline_distribution || {}) as Record<string, number>;
  const funnel = ((data?.funnel as Array<Record<string, unknown>>) || []) as Array<{
    label: string;
    value: number;
    percentage: number;
  }>;
  const revenue = (data?.revenue || {}) as Record<string, number>;

  const totalLeads = Number(kpis.total_leads || 0);
  const conversionRate = Number(kpis.conversion_rate || 0);
  const contactRate = Number(kpis.contact_rate || 0);
  const won = Number(kpis.won || stageCounts.won || 0);

  return (
    <div className="mx-auto max-w-[1400px] space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold">Analytics</h1>
        <p className="text-sm text-muted-foreground">Live metrics from Lead Engine workspace</p>
      </div>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Total Leads", value: String(totalLeads), icon: Users, color: "text-blue-500" },
          { label: "Conversion Rate", value: `${conversionRate}%`, icon: TrendingUp, color: "text-green-500" },
          { label: "Contact Rate", value: `${contactRate}%`, icon: BarChart3, color: "text-purple-500" },
          { label: "Won Deals", value: String(won), icon: Zap, color: "text-emerald-500" },
        ].map((kpi, idx) => (
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
          <CardTitle className="text-base">Conversion Funnel</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {(funnel.length
            ? funnel
            : [
                { label: "Discovered", value: totalLeads, percentage: 100 },
                { label: "Contacted", value: 0, percentage: 0 },
                { label: "Replied", value: 0, percentage: 0 },
                { label: "Meeting", value: 0, percentage: 0 },
                { label: "Won", value: 0, percentage: 0 },
              ]
          ).map((step, idx) => (
            <div key={step.label} className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">{step.label}</span>
                <span className="font-medium">{step.value}</span>
              </div>
              <div className="h-3 overflow-hidden rounded-full bg-muted/30">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.max(0, Math.min(100, Number(step.percentage) || 0))}%` }}
                  transition={{ delay: 0.1 * idx, duration: 0.5 }}
                  className="h-full rounded-full bg-primary"
                />
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Pipeline Distribution</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              { label: "New", value: stageCounts.new || 0, color: "bg-blue-500" },
              { label: "Contacted", value: stageCounts.contacted || 0, color: "bg-orange-500" },
              { label: "Replied", value: stageCounts.replied || 0, color: "bg-green-500" },
              { label: "Meeting", value: stageCounts.meeting || 0, color: "bg-purple-500" },
              { label: "Won", value: stageCounts.won || 0, color: "bg-emerald-500" },
              { label: "Lost", value: stageCounts.lost || 0, color: "bg-red-500" },
            ].map((stage) => (
              <div key={stage.label} className="flex items-center gap-3">
                <div className={cn("h-3 w-3 rounded-full", stage.color)} />
                <span className="flex-1 text-sm text-muted-foreground">{stage.label}</span>
                <span className="font-medium">{stage.value}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Revenue Metrics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              { label: "Pipeline Value", value: `$${Number(revenue.pipeline_value || 0).toLocaleString()}` },
              { label: "Won Revenue", value: `$${Number(revenue.won_revenue || 0).toLocaleString()}` },
              { label: "Average Deal Size", value: `$${Number(revenue.avg_deal_size || 0).toLocaleString()}` },
              { label: "Win Rate", value: `${Number(revenue.win_rate || 0).toFixed(1)}%` },
            ].map((metric) => (
              <div key={metric.label} className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">{metric.label}</span>
                <span className="font-medium">{metric.value}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
