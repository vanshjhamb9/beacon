"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  BarChart3,
  Building2,
  Mail,
  Phone,
  Target,
  TrendingUp,
  Users,
  Zap,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type Stats = {
  total: number;
  with_phone: number;
  with_email: number;
  with_both: number;
  hot: number;
  warm: number;
  low: number;
  with_founder: number;
  with_role: number;
  mega_extracted: number;
  avg_score: number;
  categories: Record<string, number>;
  roles: Record<string, number>;
  sources: Record<string, number>;
};

export function AnalyticsWorkspace() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/unified-leads/stats");
      if (res.ok) setStats(await res.json());
    } catch (e) {
      console.error("Failed to fetch stats", e);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, [fetchStats]);

  if (loading || !stats) {
    return (
      <div className="space-y-6">
        <h1 className="font-display text-2xl font-semibold">Analytics</h1>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 rounded-xl bg-muted/30 animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  const categoryEntries = Object.entries(stats.categories).sort(
    (a, b) => b[1] - a[1]
  );
  const roleEntries = Object.entries(stats.roles).sort(
    (a, b) => b[1] - a[1]
  );
  const sourceEntries = Object.entries(stats.sources).sort(
    (a, b) => b[1] - a[1]
  );

  const contactCoverage = stats.total
    ? Math.round((stats.with_both / stats.total) * 100)
    : 0;
  const phoneCoverage = stats.total
    ? Math.round((stats.with_phone / stats.total) * 100)
    : 0;
  const emailCoverage = stats.total
    ? Math.round((stats.with_email / stats.total) * 100)
    : 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold">Analytics</h1>
        <p className="text-sm text-muted-foreground">
          Lead pipeline metrics and decision maker coverage
        </p>
      </div>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          {
            label: "Total Leads",
            value: String(stats.total),
            icon: Users,
            color: "text-blue-500",
          },
          {
            label: "With Phone",
            value: `${stats.with_phone} (${phoneCoverage}%)`,
            icon: Phone,
            color: "text-emerald-500",
          },
          {
            label: "With Email",
            value: `${stats.with_email} (${emailCoverage}%)`,
            icon: Mail,
            color: "text-blue-400",
          },
          {
            label: "Both Phone+Email",
            value: `${stats.with_both} (${contactCoverage}%)`,
            icon: Target,
            color: "text-purple-500",
          },
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
                    <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
                      {kpi.label}
                    </p>
                    <p className="mt-1 font-display text-3xl font-semibold">
                      {kpi.value}
                    </p>
                  </div>
                  <kpi.icon className={cn("h-8 w-8 opacity-50", kpi.color)} />
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </section>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          {
            label: "Hot Leads",
            value: stats.hot,
            color: "bg-emerald-500",
            textColor: "text-emerald-400",
          },
          {
            label: "Warm Leads",
            value: stats.warm,
            color: "bg-amber-500",
            textColor: "text-amber-400",
          },
          {
            label: "Low Leads",
            value: stats.low,
            color: "bg-slate-500",
            textColor: "text-slate-400",
          },
          {
            label: "Avg Score",
            value: stats.avg_score,
            color: "bg-primary",
            textColor: "text-primary",
          },
        ].map((item, idx) => (
          <motion.div
            key={item.label}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + 0.05 * idx, duration: 0.3 }}
          >
            <Card className="border-border/60 bg-card/60">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className={cn("h-3 w-3 rounded-full", item.color)} />
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
                      {item.label}
                    </p>
                    <p className={cn("text-2xl font-bold", item.textColor)}>
                      {item.value}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">
              Decision Maker Roles
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {roleEntries.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No roles classified yet
              </p>
            ) : (
              roleEntries.map(([role, count]) => (
                <div key={role} className="flex items-center gap-3">
                  <div className="flex items-center gap-2 flex-1">
                    {role.includes("FOUNDER") || role.includes("CEO") ? (
                      <Zap className="h-3 w-3 text-emerald-400" />
                    ) : (
                      <Users className="h-3 w-3 text-muted-foreground" />
                    )}
                    <span className="text-sm text-muted-foreground">
                      {role}
                    </span>
                  </div>
                  <span className="font-medium">{count}</span>
                  <div className="w-20 h-2 rounded-full bg-muted/30 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-primary"
                      style={{
                        width: `${Math.min(100, (count / stats.total) * 100)}%`,
                      }}
                    />
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Categories</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {categoryEntries.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No categories yet
              </p>
            ) : (
              categoryEntries.map(([cat, count]) => (
                <div key={cat} className="flex items-center gap-3">
                  <div className="flex items-center gap-2 flex-1">
                    <Building2 className="h-3 w-3 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">{cat}</span>
                  </div>
                  <span className="font-medium">{count}</span>
                  <div className="w-20 h-2 rounded-full bg-muted/30 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-primary"
                      style={{
                        width: `${Math.min(100, (count / stats.total) * 100)}%`,
                      }}
                    />
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">
              Contact Coverage
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              {
                label: "Phone Coverage",
                value: phoneCoverage,
                count: stats.with_phone,
                color: "bg-emerald-500",
              },
              {
                label: "Email Coverage",
                value: emailCoverage,
                count: stats.with_email,
                color: "bg-blue-500",
              },
              {
                label: "Both Phone+Email",
                value: contactCoverage,
                count: stats.with_both,
                color: "bg-purple-500",
              },
            ].map((item) => (
              <div key={item.label} className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">{item.label}</span>
                  <span className="font-medium">
                    {item.count} ({item.value}%)
                  </span>
                </div>
                <div className="h-3 overflow-hidden rounded-full bg-muted/30">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${item.value}%` }}
                    transition={{ duration: 0.5 }}
                    className={cn("h-full rounded-full", item.color)}
                  />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Extraction Sources</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {sourceEntries.length === 0 ? (
              <p className="text-sm text-muted-foreground">No sources yet</p>
            ) : (
              sourceEntries.map(([source, count]) => (
                <div key={source} className="flex items-center gap-3">
                  <div className="flex items-center gap-2 flex-1">
                    <BarChart3 className="h-3 w-3 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">
                      {source.replace("_", " ")}
                    </span>
                  </div>
                  <Badge variant="outline">{count}</Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}
