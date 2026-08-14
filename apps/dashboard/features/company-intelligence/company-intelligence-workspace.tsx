"use client";

import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { formatScore } from "@/lib/utils";

type Row = {
  company?: string;
  website?: string;
  industry?: string;
  revenue_readiness?: string;
  readiness_score?: number;
  technology?: string;
  buying_signals?: string;
  decision_makers?: string;
  business_email?: string;
  best_service?: string;
  next_action?: string;
  evidence?: number;
  founder_queue_eligible?: boolean;
};

export function CompanyIntelligenceWorkspace() {
  const dashboard = useQuery({
    queryKey: ["cir-dashboard"],
    queryFn: () => beaconApi.cirDashboard(),
    refetchInterval: 60_000,
  });
  const summary = useQuery({
    queryKey: ["cir-summary"],
    queryFn: () => beaconApi.cirSummary(),
    refetchInterval: 120_000,
  });

  if (dashboard.isError) {
    return <ErrorState title="Company Intelligence unavailable" description="API /company-intelligence/dashboard failed." />;
  }

  const items = ((dashboard.data?.items as Row[]) || []) as Row[];

  return (
    <div className="space-y-6">
      <div>
        <SectionLabel>Revenue intelligence</SectionLabel>
        <h1 className="text-2xl font-semibold tracking-tight">Company Intelligence</h1>
        <p className="text-sm text-muted-foreground">
          What a BDM would learn in 20 minutes on the official website — evidence only, no fabrication.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Profiles</CardDescription>
            <CardTitle>{dashboard.isLoading ? <Skeleton className="h-7 w-16" /> : items.length}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Founder Queue eligible</CardDescription>
            <CardTitle>
              {dashboard.isLoading ? <Skeleton className="h-7 w-16" /> : Number(dashboard.data?.founder_queue || 0)}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Business profile %</CardDescription>
            <CardTitle>
              {summary.isLoading ? <Skeleton className="h-7 w-16" /> : `${Number(summary.data?.business_profile_pct || 0)}%`}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Contact %</CardDescription>
            <CardTitle>
              {summary.isLoading ? <Skeleton className="h-7 w-16" /> : `${Number(summary.data?.contact_pct || 0)}%`}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Intelligence workspace</CardTitle>
          <CardDescription>
            Company · Website · Industry · Revenue Readiness · Technology · Buying Signals · Decision Makers · Email ·
            Best Service · Next Action · Evidence
          </CardDescription>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full min-w-[1100px] text-left text-sm">
            <thead className="border-b text-muted-foreground">
              <tr>
                <th className="py-2 pr-3 font-medium">Company</th>
                <th className="py-2 pr-3 font-medium">Website</th>
                <th className="py-2 pr-3 font-medium">Industry</th>
                <th className="py-2 pr-3 font-medium">Revenue Readiness</th>
                <th className="py-2 pr-3 font-medium">Technology</th>
                <th className="py-2 pr-3 font-medium">Buying Signals</th>
                <th className="py-2 pr-3 font-medium">Decision Makers</th>
                <th className="py-2 pr-3 font-medium">Business Email</th>
                <th className="py-2 pr-3 font-medium">Best Service</th>
                <th className="py-2 pr-3 font-medium">Next Action</th>
                <th className="py-2 font-medium">Evidence</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.isLoading &&
                Array.from({ length: 6 }).map((_, i) => (
                  <tr key={i} className="border-b">
                    <td className="py-3" colSpan={11}>
                      <Skeleton className="h-5 w-full" />
                    </td>
                  </tr>
                ))}
              {!dashboard.isLoading && items.length === 0 && (
                <tr>
                  <td className="py-6 text-muted-foreground" colSpan={11}>
                    No CIR profiles yet. Worker runs every 120s on EROWD-admitted companies only.
                  </td>
                </tr>
              )}
              {items.map((row, idx) => (
                <tr key={`${row.company}-${idx}`} className="border-b align-top">
                  <td className="py-3 pr-3 font-medium">{row.company || "—"}</td>
                  <td className="py-3 pr-3">
                    {row.website ? (
                      <a className="text-primary underline-offset-2 hover:underline" href={row.website} target="_blank" rel="noreferrer">
                        {row.website}
                      </a>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="py-3 pr-3">{row.industry || "UNKNOWN"}</td>
                  <td className="py-3 pr-3">
                    <Badge variant={row.founder_queue_eligible ? "default" : "secondary"}>
                      {row.revenue_readiness || "UNKNOWN"} {row.readiness_score != null ? `(${formatScore(Number(row.readiness_score), 0)})` : ""}
                    </Badge>
                  </td>
                  <td className="py-3 pr-3">{row.technology || "UNKNOWN"}</td>
                  <td className="py-3 pr-3">{row.buying_signals || "—"}</td>
                  <td className="py-3 pr-3">{row.decision_makers || "—"}</td>
                  <td className="py-3 pr-3">{row.business_email || "UNKNOWN"}</td>
                  <td className="py-3 pr-3">{row.best_service || "UNKNOWN"}</td>
                  <td className="py-3 pr-3">{row.next_action || "—"}</td>
                  <td className="py-3">{row.evidence ?? 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
